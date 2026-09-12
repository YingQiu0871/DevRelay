"""v0.2-A AUDIT REMEDIATION regression matrix.

Maps to the independent audit findings and the required matrix (A-P):

P1-01  A  persisted result is replayed after a crash -> 0 external calls
       B  legacy half-applied state finishes without duplicate history
       C  finding_seen_counts counted exactly once
       D  applied marker + missing transition completes locally
       E  fully applied + repeated continue -> no-op
       F  uncertain external call still fails closed (no invented result)
P2-01  D* reviewer call ids unique across restart/unblock/retry
       E* reviewer call evidence immutable across retry
P2-02  F* implementer retry gets a new attempt id
       G* implementer evidence survives the retry
P2-03  J  policy refresh preserves before/after artifacts
       K  refresh never resets usage
P3-01  L  parsing/persistence cap wording + fail-closed behaviour
P3-02  M  mixed retry sequence: phase/error_type match the real cause
P3-03  N  fingerprint normalizes separators, not case
P3-04  O  new tasks persist policy_source=snapshot
       P  legacy status/usage are read-only
Budget 1-5 per audit section 20.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from devrelay.artifacts.store import ArtifactStore
from devrelay.config import bundled_default_path
from devrelay.errors import ProviderError, ReviewFormatError
from devrelay.models import (
    STATE_SCHEMA_VERSION,
    AppliedReviewRecord,
    CallErrorType,
    ProviderCallPhase,
    ProviderExecutionResult,
    ProviderKind,
    ReviewAttempt,
    ReviewAttemptStatus,
    ReviewResult,
)
from devrelay.pipeline.review_lifecycle import (
    finding_fingerprint,
    mark_findings,
    pending_result_attempt,
    review_result_hash,
)
from devrelay.pipeline.states import PipelineState as S
from devrelay.providers.base import ImplementerProvider, ReviewerProvider
from devrelay.providers.evidence import ReviewCallPolicy
from devrelay.providers.manual import ManualReviewer
from devrelay.providers.openai_compatible import (
    OpenAICompatibleReviewer,
    ReviewerEndpoint,
)

from helpers import (
    FakeImplementer,
    ScriptedAutoReviewer,
    build_engine,
    default_config,
    make_finding,
    make_packet,
    make_review,
)

STATE = "DR-0001"
VALID = json.dumps(
    {"decision": "PASS", "summary": "looks good", "findings": []}
)


class CrashAfterFinalize(BaseException):
    """Simulated hard kill inside the result-persisted -> applied window."""


class FlakyImplementer(ImplementerProvider):
    """Raises on the first invocation, succeeds afterwards."""

    name = "flaky"

    def __init__(self) -> None:
        self.calls: list = []

    def availability(self) -> tuple[bool, str]:
        return (True, "flaky fake")

    def run(self, context) -> ProviderExecutionResult:
        self.calls.append(context)
        if len(self.calls) == 1:
            raise RuntimeError("provider died after start")
        return ProviderExecutionResult(exit_code=0, stdout="ok", report="ok")


def _started(tmp_path, *, config=None, implementer=None, reviewer=None):
    root, store, engine = build_engine(
        tmp_path,
        config=config,
        implementer=implementer or FakeImplementer(),
        reviewer=reviewer,
    )
    engine.create_task("t")
    engine.import_plan(STATE, make_packet(task_id=STATE))
    return store, engine


def _reviewer_calls(task) -> list:
    return [
        record
        for record in task.provider_calls
        if record.provider_kind is ProviderKind.REVIEWER
    ]


def _evidence(store: ArtifactStore, name: str) -> Path:
    return store.policy_dir(STATE) / "calls" / name


# ===========================================================================
# P1-01 / matrix A: persisted result is replayed, never re-requested
# ===========================================================================
def test_A_persisted_result_replayed_with_zero_reviewer_calls(tmp_path):
    reviewer = ScriptedAutoReviewer([make_review("PASS", summary="recovered ok")])
    store, engine = _started(tmp_path, reviewer=reviewer)

    def crash(*args, **kwargs):
        raise CrashAfterFinalize()

    engine._apply_review = crash  # simulate the crash window
    with pytest.raises(CrashAfterFinalize):
        engine.continue_task(STATE)

    crashed = store.read_task(STATE)
    assert crashed.state == S.REVIEWING
    attempt = crashed.review_attempts[-1]
    assert attempt.status is ReviewAttemptStatus.COMPLETED
    assert attempt.result is not None and attempt.result_persisted is True
    assert attempt.result_applied is False
    assert crashed.review_history == []            # semantic apply never ran

    # ---- restart (new engine, new reviewer that must stay unused) ---------
    reviewer2 = ScriptedAutoReviewer(
        [make_review("REQUEST_CHANGES", [make_finding("P1")])]
    )
    _root2, store2, engine2 = build_engine(
        tmp_path, implementer=FakeImplementer(), reviewer=reviewer2
    )
    events = engine2.continue_task(STATE)

    assert reviewer2.bundles == []                 # 0 external reviewer calls
    task = store2.read_task(STATE)
    assert task.state == S.FINAL_GATE_REQUIRED     # persisted PASS was applied
    assert len(task.review_history) == 1
    assert any("replaying locally with 0 external calls" in e for e in events)
    # budget test 1: recovery must not double-count the paid call
    usage = engine2.usage_block(STATE)
    assert usage["reviewer_calls"] == 1
    assert len(_reviewer_calls(task)) == 1
    applied = [a for a in task.review_attempts if a.result_applied]
    assert len(applied) == 1 and applied[0].applied_state == S.FINAL_GATE_REQUIRED.value


def test_A2_recovered_blocking_result_enters_fix_without_extra_call(tmp_path):
    reviewer = ScriptedAutoReviewer(
        [make_review("REQUEST_CHANGES", [make_finding("P2", title="real bug")])]
    )
    store, engine = _started(tmp_path, reviewer=reviewer)
    engine._apply_review = lambda *a, **k: (_ for _ in ()).throw(CrashAfterFinalize())
    with pytest.raises(CrashAfterFinalize):
        engine.continue_task(STATE)

    impl = FakeImplementer()
    reviewer2 = ScriptedAutoReviewer([make_review("PASS")])
    _root2, store2, engine2 = build_engine(tmp_path, implementer=impl, reviewer=reviewer2)
    engine2.continue_task(STATE)

    task = store2.read_task(STATE)
    # The recovered REQUEST_CHANGES drove a real fix pass, and only the *new*
    # round cost a reviewer call (1 recovered + 1 new = 2 external calls).
    assert len(impl.calls) == 1
    assert task.state == S.FINAL_GATE_REQUIRED
    assert len(reviewer2.bundles) == 1
    assert engine2.usage_block(STATE)["reviewer_calls"] == 2
    assert len(task.review_history) == 2


# ===========================================================================
# matrix B / C: legacy half-applied state
# ===========================================================================
def _legacy_half_applied(tmp_path, review: ReviewResult):
    """State written by fe4b044: history + counters persisted, state not applied."""
    store, engine = _started(tmp_path, reviewer=ManualReviewer())
    task = store.read_task(STATE)
    task.state = S.REVIEWING
    normalized = engine._normalize_review(STATE, review)
    marked = mark_findings(normalized, task)
    task.review_history.append(marked)
    task.last_review = marked
    task.current_findings = [f for f in marked.findings if f.severity.value in {"P0", "P1", "P2"}]
    task.review_attempts.append(
        ReviewAttempt(
            review_number=1,
            attempt_id=f"{STATE}-R0001",
            provider_name="openai_compatible",
            status=ReviewAttemptStatus.COMPLETED,
            result=normalized,
        )
    )
    store.write_task(task)
    return store, engine


def test_B_legacy_half_apply_finishes_without_duplicate_history(tmp_path):
    review = make_review("REQUEST_CHANGES", [make_finding("P2", title="legacy blocker")])
    store, engine = _legacy_half_applied(tmp_path, review)

    engine.continue_task(STATE)
    task = store.read_task(STATE)

    assert len(task.review_history) == 1                       # no duplicate
    assert list(task.finding_seen_counts.values()) == [1]      # counted once
    assert any(e.to_state == S.FIX_REQUIRED.value for e in task.audit)
    identity = review_result_hash(task.review_history[0])
    assert [m.identity for m in task.applied_reviews] == [identity]
    assert len([e for e in task.audit if e.to_state == S.FIX_REQUIRED.value]) == 1


def test_C_repeated_continue_keeps_single_application(tmp_path):
    review = make_review("REQUEST_CHANGES", [make_finding("P1", title="once only")])
    store, engine = _legacy_half_applied(tmp_path, review)
    engine.continue_task(STATE)
    first = store.read_task(STATE)

    engine.continue_task(STATE)
    second = store.read_task(STATE)

    assert len(second.review_history) == len(first.review_history) == 1
    assert second.finding_seen_counts == first.finding_seen_counts == (
        {finding_fingerprint(first.current_findings[0]): 1}
    )
    assert len(second.applied_reviews) == 1


# ===========================================================================
# matrix D / E: applied marker without a transition, repeated continue
# ===========================================================================
def test_D_applied_marker_without_transition_completes_locally(tmp_path):
    reviewer = ScriptedAutoReviewer([make_review("PASS")])
    store, engine = _started(tmp_path, reviewer=reviewer)
    task = store.read_task(STATE)
    review = engine._normalize_review(STATE, make_review("PASS", summary="done"))
    task.state = S.REVIEWING
    task.review_history.append(review)
    task.last_review = review
    task.applied_reviews.append(
        AppliedReviewRecord(
            identity=review_result_hash(review),
            review_number=1,
            attempt_id=f"{STATE}-R0001",
            state=S.FINAL_GATE_REQUIRED.value,
        )
    )
    task.review_attempts.append(
        ReviewAttempt(
            review_number=1,
            attempt_id=f"{STATE}-R0001",
            provider_name="openai_compatible",
            status=ReviewAttemptStatus.COMPLETED,
            result=review,
            result_persisted=True,
            result_hash=review_result_hash(review),
            result_applied=True,
            applied_state=S.FINAL_GATE_REQUIRED.value,
        )
    )
    store.write_task(task)

    engine.continue_task(STATE)
    after = store.read_task(STATE)

    assert reviewer.bundles == []                  # no reviewer call
    assert after.state == S.FINAL_GATE_REQUIRED
    assert len(after.review_history) == 1
    assert len(after.applied_reviews) == 1


def test_E_fully_applied_repeated_continue_is_a_noop(tmp_path):
    reviewer = ScriptedAutoReviewer([make_review("PASS")])
    store, engine = _started(tmp_path, reviewer=reviewer)
    engine.continue_task(STATE)
    first = store.read_task(STATE)
    assert first.state == S.FINAL_GATE_REQUIRED

    for _ in range(3):
        engine.continue_task(STATE)

    second = store.read_task(STATE)
    assert len(reviewer.bundles) == 1              # never re-reviewed
    assert len(second.review_history) == 1
    assert len(second.audit) == len(first.audit)
    assert engine.usage_block(STATE)["reviewer_calls"] == 1


# ===========================================================================
# matrix F: uncertain external call still fails closed
# ===========================================================================
def test_F_uncertain_call_fails_closed_and_invents_no_result(tmp_path):
    reviewer = ScriptedAutoReviewer([make_review("PASS")])
    store, engine = _started(tmp_path, reviewer=reviewer)
    task = store.read_task(STATE)
    task.state = S.REVIEWING
    task.review_call_in_flight = True
    task.review_attempts.append(
        ReviewAttempt(
            review_number=1,
            attempt_id=f"{STATE}-R0001",
            provider_name="openai_compatible",
            status=ReviewAttemptStatus.IN_FLIGHT,
            call_ids=[f"{STATE}-C0002"],
        )
    )
    store.write_task(task)

    engine.continue_task(STATE)
    after = store.read_task(STATE)

    assert after.state == S.BLOCKED
    assert after.blocked_code == "interrupted_reviewer_attempt"
    assert reviewer.bundles == []
    assert pending_result_attempt(after) is None   # nothing is invented
    assert after.review_history == []


# ===========================================================================
# P2-01: reviewer call identity + immutable evidence
# ===========================================================================
def test_reviewer_call_ids_unique_across_unblock_retry(tmp_path):
    reviewer = ScriptedAutoReviewer(
        [("transport", "network down"), make_review("PASS")]
    )
    store, engine = _started(tmp_path, reviewer=reviewer)
    engine.continue_task(STATE)

    blocked = store.read_task(STATE)
    assert blocked.state == S.BLOCKED and blocked.blocked_code == "review_provider"
    first_ids = [r.call_id for r in _reviewer_calls(blocked)]
    assert len(first_ids) == 1
    first_evidence = _evidence(store, f"{first_ids[0]}.json")
    assert first_evidence.is_file()
    frozen = first_evidence.read_bytes()

    engine.unblock(STATE, reason="retry the failed reviewer call")
    engine.continue_task(STATE)

    task = store.read_task(STATE)
    ids = [r.call_id for r in _reviewer_calls(task)]
    assert len(ids) == 2
    assert len(set(ids)) == len(ids)               # unique across retry
    assert all(call_id.startswith(f"{STATE}-C") for call_id in ids)
    assert task.state == S.FINAL_GATE_REQUIRED
    # matrix E: the first call's evidence was NOT overwritten by the retry
    assert first_evidence.read_bytes() == frozen
    assert _evidence(store, f"{ids[1]}.json").is_file()
    # every call is traceable to its attempt and round
    assert all(r.parent_attempt_id for r in _reviewer_calls(task))
    assert all(r.review_number == 1 for r in _reviewer_calls(task))


# ===========================================================================
# P2-02: implementer attempt identity + evidence survival
# ===========================================================================
def test_implementer_retry_gets_new_identity_and_keeps_evidence(tmp_path):
    impl = FlakyImplementer()
    store, engine = _started(tmp_path, implementer=impl, reviewer=ManualReviewer())

    with pytest.raises(RuntimeError):
        engine.continue_task(STATE)

    failed = store.read_task(STATE)
    assert failed.state == S.BLOCKED and failed.blocked_code == "interrupted_attempt"
    assert [a.attempt_id for a in failed.attempts] == [f"{STATE}-A0001"]
    failed_call_ids = [r.call_id for r in failed.provider_calls]
    assert failed_call_ids == [f"{STATE}-C0001"]
    assert failed.attempts[0].call_ids == failed_call_ids

    attempt_evidence = store.policy_dir(STATE) / "attempts" / f"{STATE}-A0001.json"
    call_evidence = _evidence(store, f"{STATE}-C0001.json")
    run_evidence = store.policy_dir(STATE) / "runs" / f"{STATE}-A0001-post.json"
    log_evidence = store.logs_dir(STATE) / f"{STATE}-A0001.stdout.log"
    frozen = {
        "attempt": attempt_evidence.read_bytes(),
        "call": call_evidence.read_bytes(),
        "log": log_evidence.read_bytes(),
    }

    engine.unblock(STATE, reason="provider died; retrying once")
    engine.continue_task(STATE)

    task = store.read_task(STATE)
    assert [a.attempt_id for a in task.attempts] == [
        f"{STATE}-A0001",
        f"{STATE}-A0002",
    ]
    call_ids = [r.call_id for r in task.provider_calls]
    assert call_ids == [f"{STATE}-C0001", f"{STATE}-C0002"]
    assert len(set(call_ids)) == len(call_ids)
    assert task.attempts[1].call_ids == [f"{STATE}-C0002"]
    # old evidence survived the retry verbatim
    assert attempt_evidence.read_bytes() == frozen["attempt"]
    assert call_evidence.read_bytes() == frozen["call"]
    assert log_evidence.read_bytes() == frozen["log"]
    assert run_evidence.is_file()
    assert (store.policy_dir(STATE) / "attempts" / f"{STATE}-A0002.json").is_file()
    # budget test 2: one paid attempt before the retry, two in total
    assert engine.usage_block(STATE)["implementer_calls"] == 2


# ===========================================================================
# matrix H / I: global uniqueness + accounting agreement
# ===========================================================================
def test_call_ids_are_unique_and_usage_matches_actual_calls(tmp_path):
    impl = FakeImplementer()
    reviewer = ScriptedAutoReviewer(
        [
            make_review("REQUEST_CHANGES", [make_finding("P2", title="blocker")]),
            make_review("PASS"),
        ]
    )
    store, engine = _started(tmp_path, implementer=impl, reviewer=reviewer)
    engine.continue_task(STATE)

    task = store.read_task(STATE)
    ids = [r.call_id for r in task.provider_calls]
    assert len(ids) == 4
    assert len(set(ids)) == len(ids)
    assert ids == [
        f"{STATE}-C0001",
        f"{STATE}-C0002",
        f"{STATE}-C0003",
        f"{STATE}-C0004",
    ]
    usage = engine.usage_block(STATE)
    assert usage["implementer_calls"] == len(impl.calls) == 2
    assert usage["reviewer_calls"] == len(reviewer.bundles) == 2
    assert usage["total_calls"] == 4
    # relations: every attempt's calls resolve, every call names its attempt
    known = set(ids)
    for attempt in task.attempts:
        assert set(attempt.call_ids) <= known
    for call in task.provider_calls:
        assert call.parent_attempt_id
    for attempt in task.review_attempts:
        assert set(attempt.call_ids) <= known
    assert len({a.attempt_id for a in task.review_attempts}) == 2
    assert all(a.result_applied for a in task.review_attempts)


# ===========================================================================
# P2-03: policy refresh evidence + no usage reset
# ===========================================================================
def test_policy_refresh_preserves_before_after_and_usage(tmp_path):
    reviewer = ScriptedAutoReviewer(
        [make_review("REQUEST_CHANGES", [make_finding("P2", title="b")]), make_review("PASS")]
    )
    store, engine = _started(tmp_path, reviewer=reviewer)
    engine.continue_task(STATE)
    before_usage = engine.usage_block(STATE)
    assert before_usage["total_calls"] == 4          # 2 implementer + 2 reviewer
    assert before_usage["reviewer_calls"] == 2

    # A *different* live config (tighter reviewer budget) must not affect the
    # running task until an explicit, audited refresh happens.
    live = default_config()
    live.budget.max_reviewer_calls = 1
    _root2, store2, engine2 = build_engine(
        tmp_path, config=live, implementer=FakeImplementer(), reviewer=reviewer
    )
    task = store2.read_task(STATE)
    assert engine2.usage_block(STATE)["max_reviewer_calls"] == 4  # still the snapshot

    engine2.refresh_task_policy(STATE, "tighten reviewer budget to 1")
    refreshed = store2.read_task(STATE)
    policy_dir = store2.policy_dir(STATE)
    before_file = policy_dir / "policy-refresh-01-before.yaml"
    after_file = policy_dir / "policy-refresh-01-after.yaml"
    record_file = policy_dir / "policy-refresh-01.json"

    assert before_file.is_file() and after_file.is_file() and record_file.is_file()
    record = refreshed.policy_refreshes[-1]
    assert record.refresh_id == f"{STATE}-P0001"
    assert record.before_config_sha256 != record.after_config_sha256
    assert record.before_source == "snapshot" and record.after_source == "snapshot"
    assert "max_reviewer_calls: 4" in before_file.read_text(encoding="utf-8")
    assert "max_reviewer_calls: 1" in after_file.read_text(encoding="utf-8")
    # no credentials are ever serialized
    assert "sk-" not in before_file.read_text(encoding="utf-8") + after_file.read_text(
        encoding="utf-8"
    )
    assert not (policy_dir / "policy-refresh-01.json").read_text(
        encoding="utf-8"
    ).lower().count("api_key")

    after_usage = engine2.usage_block(STATE)
    assert after_usage["reviewer_calls"] == before_usage["reviewer_calls"] == 2
    assert after_usage["total_calls"] == before_usage["total_calls"] == 4
    assert after_usage["max_reviewer_calls"] == 1
    assert len(refreshed.provider_calls) == 4          # nothing deleted/renumbered
    assert [r.call_id for r in refreshed.provider_calls] == [
        f"{STATE}-C0001",
        f"{STATE}-C0002",
        f"{STATE}-C0003",
        f"{STATE}-C0004",
    ]

    # §12 semantics: used=1 > new max=1 -> the next reviewer call is refused
    from devrelay.pipeline.budget import BudgetExhaustedError, ProviderBudget

    with pytest.raises(BudgetExhaustedError):
        ProviderBudget(engine2._task_config(refreshed).budget).check(
            refreshed, ProviderKind.REVIEWER
        )

    # ...and raising the limit again makes exactly the remaining budget usable.
    live2 = default_config()
    live2.budget.max_reviewer_calls = 5
    _root3, store3, engine3 = build_engine(
        tmp_path, config=live2, implementer=FakeImplementer(), reviewer=reviewer
    )
    engine3.refresh_task_policy(STATE, "allow the remaining reviews")
    current = store3.read_task(STATE)
    ProviderBudget(engine3._task_config(current).budget).check(
        current, ProviderKind.REVIEWER
    )  # used=2 < max=5 -> must not raise
    assert engine3.usage_block(STATE)["total_calls"] == 4
    assert len(current.policy_refreshes) == 2
    assert len(current.provider_calls) == 4


# ===========================================================================
# P3-01: cap wording + behaviour
# ===========================================================================
def test_response_cap_wording_and_behaviour(tmp_path):
    # v0.2-B: the canonical default policy is the packaged file (the in-code
    # DEFAULT_PROFILE_YAML literal was deleted - one editable authority).
    default_policy = bundled_default_path().read_text(encoding="utf-8")
    assert "parsing/persistence" in default_policy
    assert "network-level" in default_policy

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "x" * 5_000}}]}
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="https://review.example/v1"
    )
    reviewer = OpenAICompatibleReviewer(
        ReviewerEndpoint(base_url="https://review.example/v1", api_key="k", model="m"),
        client=client,
    )
    with pytest.raises(ReviewFormatError) as excinfo:
        reviewer.review(_bundle(), call_policy=ReviewCallPolicy(max_response_chars=1_000))
    message = str(excinfo.value)
    assert "parsing/persistence limit" in message
    assert "refuses to parse, truncate and guess" in message
    assert "x" * 100 not in message                    # no content persisted/echoed


# ===========================================================================
# P3-02 / matrix M: mixed retry sequence keeps phases truthful
# ===========================================================================
class _RecordingSink:
    def __init__(self) -> None:
        self.started: list = []
        self.finished: list = []
        self._n = 0

    def preflight(self, kind, phase) -> None:
        return None

    def start(self, record):
        self._n += 1
        record = record.model_copy(update={"call_id": f"mix-C{self._n:04d}"})
        self.started.append(record)
        return record

    def finish(self, record) -> None:
        self.finished.append(record)


def test_mixed_retry_sequence_labels_each_cause(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        seq = len(handler.seen)
        handler.seen.append(seq)
        if seq == 0:
            return httpx.Response(200, json={"choices": [{"message": {"content": "junk"}}]})
        if seq == 1:
            raise httpx.ConnectError("connection refused")
        if seq == 2:
            return httpx.Response(200, json={"choices": [{"message": {"content": "junk"}}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": VALID}}]})

    handler.seen = []  # type: ignore[attr-defined]
    sink = _RecordingSink()
    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="https://review.example/v1"
    )
    reviewer = OpenAICompatibleReviewer(
        ReviewerEndpoint(base_url="https://review.example/v1", api_key="k", model="m"),
        client=client,
    )
    result = reviewer.review(
        _bundle(),
        call_policy=ReviewCallPolicy(
            format_retries=2, transport_retries=1, sink=sink
        ),
    )

    assert result.decision.value == "PASS"
    assert [r.phase for r in sink.started] == [
        ProviderCallPhase.REVIEW,
        ProviderCallPhase.REVIEW_FORMAT_RETRY,
        ProviderCallPhase.REVIEW_TRANSPORT_RETRY,
        ProviderCallPhase.REVIEW_FORMAT_RETRY,
    ]
    assert [r.error_type for r in sink.finished] == [
        CallErrorType.FORMAT,
        CallErrorType.TRANSPORT,
        CallErrorType.FORMAT,
        None,
    ]
    assert [r.external_call_count for r in sink.started] == [1, 1, 1, 1]
    assert [r.call_id for r in sink.started] == [
        "mix-C0001",
        "mix-C0002",
        "mix-C0003",
        "mix-C0004",
    ]


def test_engine_level_format_retries_are_counted_and_unique(tmp_path):
    config = default_config()
    config.review.retries = 2

    def handler(request: httpx.Request) -> httpx.Response:
        seq = len(handler.seen)
        handler.seen.append(seq)
        if seq < 2:
            return httpx.Response(200, json={"choices": [{"message": {"content": "junk"}}]})
        return httpx.Response(200, json={"choices": [{"message": {"content": VALID}}]})

    handler.seen = []  # type: ignore[attr-defined]
    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="https://review.example/v1"
    )
    reviewer = OpenAICompatibleReviewer(
        ReviewerEndpoint(base_url="https://review.example/v1", api_key="k", model="m"),
        client=client,
    )
    store, engine = _started(tmp_path, config=config, reviewer=reviewer)
    engine.continue_task(STATE)

    task = store.read_task(STATE)
    assert task.state == S.FINAL_GATE_REQUIRED
    reviewer_calls = _reviewer_calls(task)
    assert [r.phase.value for r in reviewer_calls] == [
        "REVIEW",
        "REVIEW_FORMAT_RETRY",
        "REVIEW_FORMAT_RETRY",
    ]
    ids = [r.call_id for r in task.provider_calls]
    assert len(set(ids)) == len(ids) == 4               # 1 implementer + 3 reviewer
    attempt = task.review_attempts[-1]
    assert attempt.format_attempts == 3
    assert attempt.transport_attempts == 3
    assert attempt.external_calls_consumed == 3
    # budget test 3: usage reflects every HTTP call that actually happened
    usage = engine.usage_block(STATE)
    assert usage["reviewer_calls"] == 3
    assert usage["total_calls"] == 4


# ===========================================================================
# P3-03 / matrix N: fingerprint normalization
# ===========================================================================
def test_fingerprint_normalizes_separators_not_case():
    base = make_finding("P2", title="Same  Blocker")

    windows = base.model_copy(
        update={"id": "P2-01", "files": ["src\\a.py", "src/b.py"]}
    )
    posix = base.model_copy(
        update={"id": "P2-99", "files": ["src/b.py", "src/a.py"]}
    )
    assert finding_fingerprint(windows) == finding_fingerprint(posix)

    upper = base.model_copy(update={"id": "P2-01", "files": ["src/A.py"]})
    lower = base.model_copy(update={"id": "P2-01", "files": ["src/a.py"]})
    assert finding_fingerprint(upper) != finding_fingerprint(lower)

    spaced = base.model_copy(update={"id": "P2-01", "files": ["  src/a.py  "]})
    assert finding_fingerprint(spaced) == finding_fingerprint(lower)

    other = base.model_copy(update={"id": "P2-01", "files": ["src/other.py"]})
    assert finding_fingerprint(other) != finding_fingerprint(lower)


# ===========================================================================
# P3-04 / matrix O / P: policy_source persistence and read-only legacy
# ===========================================================================
def test_new_task_persists_policy_source(tmp_path):
    store, _engine = _started(tmp_path, reviewer=ManualReviewer())
    task = store.read_task(STATE)
    assert task.policy_source == "snapshot"
    raw = json.loads(store.state_path(STATE).read_text(encoding="utf-8"))
    assert raw["policy_source"] == "snapshot"
    # Current schema (v0.2-B introduced 5, v0.2-C adds the runtime milestones).
    assert raw["state_schema_version"] == STATE_SCHEMA_VERSION
    assert raw["next_provider_call_sequence"] >= 1


LEGACY_STATE = {
    "task_id": STATE,
    "title": "legacy v0.1 task",
    "state_schema_version": 2,
    "state": "REVIEWING",
    "plan_ready": True,
    "implementation_passes": 1,
    "fix_iterations_used": 0,
    "packet": {"task_id": STATE, "title": "legacy", "objective": "o"},
    "current_findings": [],
    "open_p3": [],
    "review_history": [],
    "test_evidence": [],
    "implementation_report_paths": [],
    "audit": [],
    "policy_violations": [],
    "attempts": [],
}


def test_legacy_status_and_usage_are_read_only(tmp_path):
    store = ArtifactStore(tmp_path / "ws")
    store.ensure_initialized()
    store.task_dir(STATE).mkdir(parents=True, exist_ok=True)
    store.state_path(STATE).write_text(
        json.dumps(LEGACY_STATE), encoding="utf-8"
    )

    _root, _store, engine = build_engine(
        tmp_path, reviewer=ManualReviewer(), workspace=None
    )
    before = store.state_path(STATE).read_bytes()
    status = engine.status_block(STATE)
    usage = engine.usage_block(STATE)

    assert status["policy_source"] == "live-fallback"
    assert usage["policy_source"] == "live-fallback"
    assert store.state_path(STATE).read_bytes() == before   # never rewritten
    # the legacy document is untouched - not even a policy_source key was added
    assert "policy_source" not in json.loads(before.decode("utf-8"))

    # ...and a legacy task can still be continued safely afterwards.
    events = engine.continue_task(STATE)
    after = store.read_task(STATE)
    assert after.state in (S.REVIEWING, S.FINAL_GATE_REQUIRED, S.BLOCKED)
    assert any(STATE in event for event in events)
    assert store.state_path(STATE).read_bytes() != before   # execution may write


# ===========================================================================
# budget matrix (audit section 20)
# ===========================================================================
def test_budget_manual_review_costs_zero_external_calls(tmp_path):
    store, engine = _started(tmp_path, reviewer=ManualReviewer())
    engine.continue_task(STATE)
    engine.import_manual_review(STATE, make_review("PASS", summary="manual"))
    task = store.read_task(STATE)
    assert task.state == S.FINAL_GATE_REQUIRED
    assert engine.usage_block(STATE)["reviewer_calls"] == 0
    assert task.review_attempts[-1].external_calls_consumed == 0
    assert all(
        r.external_call_count == 0 or r.provider_kind is ProviderKind.IMPLEMENTER
        for r in task.provider_calls
    )
    assert not _reviewer_calls(task)


def test_budget_refused_call_spends_nothing(tmp_path):
    config = default_config()
    config.budget.max_reviewer_calls = 0
    reviewer = ScriptedAutoReviewer([make_review("PASS")])
    store, engine = _started(tmp_path, config=config, reviewer=reviewer)
    engine.continue_task(STATE)

    task = store.read_task(STATE)
    assert task.state == S.BLOCKED
    assert task.blocked_code == "provider_budget_exhausted"
    assert "unblock --to review --refresh-policy" in (task.blocked_reason or "")
    assert reviewer.bundles == []                     # no call was attempted
    assert not _reviewer_calls(task)
    assert engine.usage_block(STATE)["reviewer_calls"] == 0


# ===========================================================================
# P3-06: bounded review-history growth (no nesting, linear only)
# ===========================================================================
def test_review_history_prompt_growth_is_linear_and_non_nested():
    from devrelay.artifacts.renderer import ReviewBundle, render_review_user_prompt

    def bundle_with(history_len: int) -> ReviewBundle:
        history = [
            make_review(
                "REQUEST_CHANGES",
                [make_finding("P2", title=f"blocker {index}")],
                summary="x" * 200,
            )
            for index in range(history_len)
        ]
        return ReviewBundle(
            task_id=STATE,
            packet=make_packet(task_id=STATE),
            workspace_root="/fake/ws",
            diff="diff --git a/x b/x\n+change\n",
            changed_files=["x.py"],
            previous_reviews=history,
        )

    small = render_review_user_prompt(bundle_with(2))
    medium = render_review_user_prompt(bundle_with(4))
    large = render_review_user_prompt(bundle_with(6))

    # One summary line per previous round: strictly linear growth (the section
    # header is only paid once, from zero to one previous review)...
    assert len(large) - len(medium) == len(medium) - len(small)
    # ...and previous findings text is never re-rendered (no nesting).
    assert large.count("- review #") == 6
    assert "blocker 0" not in large
    assert "blocker 5" not in large


# ===========================================================================
# Audit §6/§10: usage exposes the attempt -> call relation
# ===========================================================================
def test_usage_block_exposes_attempt_call_relation(tmp_path):
    reviewer = ScriptedAutoReviewer(
        [("transport", "boom"), make_review("PASS")]
    )
    store, engine = _started(tmp_path, reviewer=reviewer)
    engine.continue_task(STATE)
    engine.unblock(STATE, reason="retry")
    engine.continue_task(STATE)

    usage = engine.usage_block(STATE)
    attempts = usage["review_attempts"]
    assert [a["attempt_id"] for a in attempts] == [f"{STATE}-R0001", f"{STATE}-R0002"]
    assert [a["status"] for a in attempts] == ["TRANSPORT_FAILED", "COMPLETED"]
    assert attempts[0]["call_ids"] == [f"{STATE}-C0002"]
    assert attempts[1]["call_ids"] == [f"{STATE}-C0003"]
    assert attempts[1]["result_persisted"] and attempts[1]["result_applied"]
    assert attempts[1]["applied_state"] == S.FINAL_GATE_REQUIRED.value
    assert usage["pending_review_result"] is None
    assert [r["identity"] for r in usage["applied_reviews"]] == [
        a.result_hash for a in store.read_task(STATE).review_attempts if a.result_hash
    ]
    assert usage["policy_refreshes"] == []
    # Interrupted attempt (no result) is visible as such, not as a result.
    assert attempts[0]["result"] is None and attempts[0]["result_persisted"] is False


# ===========================================================================
# Audit §19: replay uses the already-sanitized persisted result
# ===========================================================================
def test_replay_uses_sanitized_persisted_result(tmp_path):
    secret = "sk-live-REPLAYSECRET1234567890abcd"
    reviewer = ScriptedAutoReviewer(
        [
            make_review(
                "REQUEST_CHANGES",
                [make_finding("P2", title=f"leaked {secret}")],
                summary=f"reviewer echoed {secret}",
            )
        ]
    )
    store, engine = _started(tmp_path, reviewer=reviewer)
    engine._apply_review = lambda *a, **k: (_ for _ in ()).throw(CrashAfterFinalize())
    with pytest.raises(CrashAfterFinalize):
        engine.continue_task(STATE)

    crashed = store.read_task(STATE)
    persisted = crashed.review_attempts[-1].result
    assert persisted is not None
    assert secret not in persisted.model_dump_json()      # sanitized at rest
    attempt_meta = (
        store.reviews_dir(STATE) / f"review-01-{STATE}-R0001-meta.json"
    ).read_text(encoding="utf-8")
    assert secret not in attempt_meta

    reviewer2 = ScriptedAutoReviewer([make_review("PASS")])
    _root2, store2, engine2 = build_engine(
        tmp_path, implementer=FakeImplementer(), reviewer=reviewer2
    )
    engine2.continue_task(STATE)

    task = store2.read_task(STATE)
    # The recovered round cost nothing: exactly one call, for the new round.
    assert len(reviewer2.bundles) == 1
    assert engine2.usage_block(STATE)["reviewer_calls"] == 2
    assert secret not in task.model_dump_json()
    assert secret not in json.dumps(task.review_history[0].model_dump(mode="json"))
    assert len(task.review_history) == 2
    assert task.state == S.FINAL_GATE_REQUIRED


# ---------------------------------------------------------------------------
# helpers used above
# ---------------------------------------------------------------------------
def _bundle():
    from devrelay.artifacts.renderer import ReviewBundle

    return ReviewBundle(
        task_id=STATE,
        packet=make_packet(task_id=STATE),
        workspace_root="/fake/ws",
        diff="diff --git a/x b/x\n+change\n",
        changed_files=["x.py"],
    )
