"""v0.2-A engine-level acceptance: automatic review loop behaviour."""

from __future__ import annotations

import json

import httpx
import pytest

from devrelay.models import (
    CallErrorType,
    ProviderCallPhase,
    ProviderCallRecord,
    ProviderKind,
    ReviewAttempt,
    ReviewAttemptStatus,
    Severity,
)
from devrelay.pipeline.states import PipelineState as S
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

SECRET = "sk-live-ENGINEREVIEW1234567890abcd"
VALID = json.dumps(
    {
        "decision": "PASS",
        "summary": "looks good",
        "findings": [],
    }
)


def _start(tmp_path, *, config=None, implementer=None, reviewer=None):
    root, store, engine = build_engine(
        tmp_path,
        config=config,
        implementer=implementer or FakeImplementer(),
        reviewer=reviewer,
    )
    engine.create_task("t")
    engine.import_plan("DR-0001", make_packet(task_id="DR-0001"))
    return store, engine


# ---------------------------------------------------------------------------
# A1: automatic happy path
# ---------------------------------------------------------------------------
def test_automatic_happy_path(tmp_path):
    reviewer = ScriptedAutoReviewer([make_review("PASS", summary="ok")])
    impl = FakeImplementer()
    store, engine = _start(tmp_path, implementer=impl, reviewer=reviewer)
    events = engine.continue_task("DR-0001")

    task = store.read_task("DR-0001")
    assert task.state == S.FINAL_GATE_REQUIRED
    assert len(impl.calls) == 1
    assert len(reviewer.bundles) == 1
    assert task.provider_calls[0].external_call_count == 1
    assert task.provider_calls[1].external_call_count == 1
    assert task.review_attempts[-1].status is ReviewAttemptStatus.COMPLETED
    reviews = store.reviews_dir("DR-0001")
    assert (reviews / "review-01-meta.json").is_file()
    assert (reviews / "review-01-call-01-meta.json").is_file()
    assert (reviews / "review-01-result.json").is_file()
    assert "review passed" in " ".join(events)


# ---------------------------------------------------------------------------
# A3: policy overrides a PASS decision that carries a P1 finding
# ---------------------------------------------------------------------------
def test_policy_overrides_pass_decision(tmp_path):
    reviewer = ScriptedAutoReviewer(
        [make_review("PASS", [make_finding("P1", title="core break")])]
    )
    store, engine = _start(tmp_path, reviewer=reviewer)
    engine.continue_task("DR-0001")

    task = store.read_task("DR-0001")
    # policy decides FIX (P1 is blocking), then the loop runs the fix pass and
    # the second (default) review passes.
    assert task.review_history[0].decision.value == "PASS"
    assert task.review_history[0].findings[0].severity is Severity.P1
    assert task.state == S.FINAL_GATE_REQUIRED
    assert task.fix_iterations_used == 1
    assert len(task.review_history) == 2


# ---------------------------------------------------------------------------
# A4: REQUEST_CHANGES with only P3 passes per default policy
# ---------------------------------------------------------------------------
def test_p3_only_passes_by_policy(tmp_path):
    reviewer = ScriptedAutoReviewer(
        [make_review("REQUEST_CHANGES", [make_finding("P3", title="nit")])]
    )
    store, engine = _start(tmp_path, reviewer=reviewer)
    engine.continue_task("DR-0001")

    task = store.read_task("DR-0001")
    assert task.state == S.FINAL_GATE_REQUIRED
    assert task.fix_iterations_used == 0
    assert [f.severity for f in task.open_p3] == [Severity.P3]


# ---------------------------------------------------------------------------
# A12: interrupted reviewer attempt fails closed
# ---------------------------------------------------------------------------
def test_reviewer_in_flight_marker_fails_closed(tmp_path):
    reviewer = ScriptedAutoReviewer([make_review("PASS")])
    store, engine = _start(tmp_path, reviewer=reviewer)

    task = store.read_task("DR-0001")
    task.review_call_in_flight = True          # simulates a hard kill mid-request
    store.write_task(task)

    engine.continue_task("DR-0001")
    blocked = store.read_task("DR-0001")
    assert blocked.state == S.BLOCKED
    assert blocked.blocked_code == "interrupted_reviewer_attempt"
    assert reviewer.bundles == []              # the reviewer was NOT called again

    # Explicit acknowledgement is the only way forward.
    engine.unblock("DR-0001", reason="reviewed the interrupted call")
    assert store.read_task("DR-0001").review_call_in_flight is False
    engine.continue_task("DR-0001")
    assert len(reviewer.bundles) == 1


def test_unfinished_review_round_fails_closed_and_unblock_acknowledges(tmp_path):
    """Crash window *after* the response arrived (marker already cleared)."""
    reviewer = ScriptedAutoReviewer([make_review("PASS")])
    store, engine = _start(tmp_path, reviewer=reviewer)

    # Simulate: the round started, the provider answered, the process died
    # before the result was finalized -> attempt stuck IN_FLIGHT, marker clear.
    task = store.read_task("DR-0001")
    task.review_attempts.append(
        ReviewAttempt(
            review_number=1,
            attempt_id="DR-0001-R01",
            provider_name="scripted-auto",
            status=ReviewAttemptStatus.IN_FLIGHT,
            call_ids=["scripted-call-001"],
            external_calls_consumed=1,
        )
    )
    task.provider_calls.append(
        ProviderCallRecord(
            call_id="scripted-call-001",
            provider_kind=ProviderKind.REVIEWER,
            provider_name="scripted-auto",
            phase=ProviderCallPhase.REVIEW,
            external_call_count=1,
            success=True,
        )
    )
    task.review_call_in_flight = False
    store.write_task(task)

    engine.continue_task("DR-0001")
    blocked = store.read_task("DR-0001")
    assert blocked.state == S.BLOCKED
    assert blocked.blocked_code == "interrupted_reviewer_attempt"
    assert "never finalized" in (blocked.blocked_reason or "")
    assert reviewer.bundles == []              # no silent repeat of a billed call

    # Unblocking acknowledges (and closes) the stale round, keeping evidence.
    engine.unblock("DR-0001", reason="checked the persisted call evidence")
    acked = store.read_task("DR-0001")
    assert acked.state == S.REVIEWING
    assert acked.review_attempts[-1].status is ReviewAttemptStatus.INTERRUPTED
    assert acked.review_attempts[-1].call_ids == ["scripted-call-001"]
    assert any(
        "unfinished review round(s) #1" in event.note for event in acked.audit
    )

    engine.continue_task("DR-0001")
    resumed = store.read_task("DR-0001")
    assert len(reviewer.bundles) == 1
    assert resumed.state == S.FINAL_GATE_REQUIRED
    assert [a.status for a in resumed.review_attempts] == [
        ReviewAttemptStatus.INTERRUPTED,
        ReviewAttemptStatus.COMPLETED,
    ]


def test_keyboard_interrupt_during_review_blocks_and_does_not_rerun(tmp_path):
    reviewer = ScriptedAutoReviewer([KeyboardInterrupt()])
    store, engine = _start(tmp_path, reviewer=reviewer)
    with pytest.raises(KeyboardInterrupt):
        engine.continue_task("DR-0001")

    task = store.read_task("DR-0001")
    assert task.state == S.BLOCKED
    assert task.blocked_code == "interrupted_reviewer_attempt"
    assert task.review_call_in_flight is False
    attempt = task.review_attempts[-1]
    assert attempt.status is ReviewAttemptStatus.INTERRUPTED
    assert attempt.error_type is CallErrorType.EXCEPTION

    # Restart: a fresh engine must not call the reviewer again.
    reviewer2 = ScriptedAutoReviewer([make_review("PASS")])
    _root2, store2, engine2 = build_engine(tmp_path, reviewer=reviewer2)
    engine2.continue_task("DR-0001")
    assert reviewer2.bundles == []
    assert store2.read_task("DR-0001").state == S.BLOCKED


# ---------------------------------------------------------------------------
# A13: manual review consumes zero external calls
# ---------------------------------------------------------------------------
def test_manual_review_consumes_no_external_calls(tmp_path):
    store, engine = _start(tmp_path, reviewer=ManualReviewer())
    engine.continue_task("DR-0001")
    assert store.read_task("DR-0001").state == S.REVIEWING
    assert (store.reviews_dir("DR-0001") / "review-01-request.md").is_file()

    engine.import_manual_review("DR-0001", make_review("PASS", summary="manual ok"))
    task = store.read_task("DR-0001")
    assert task.state == S.FINAL_GATE_REQUIRED
    attempt = task.review_attempts[-1]
    assert attempt.provider_name == "manual"
    assert attempt.external_calls_consumed == 0
    assert all(r.external_call_count == 0 for r in task.provider_calls if r.provider_name == "manual")
    assert [r.provider_name for r in task.provider_calls] == ["fake-implementer"]


# ---------------------------------------------------------------------------
# A17: reviewer output secrets are sanitized before persistence
# ---------------------------------------------------------------------------
def test_secret_in_reviewer_result_is_redacted(tmp_path):
    review = make_review(
        "REQUEST_CHANGES",
        [
            make_finding("P2", title="leaky").model_copy(
                update={"evidence": f"log line with {SECRET}"}
            )
        ],
        summary=f"context mentions {SECRET}",
    )
    reviewer = ScriptedAutoReviewer([review, make_review("PASS")])
    store, engine = _start(tmp_path, reviewer=reviewer)
    engine.continue_task("DR-0001")

    task = store.read_task("DR-0001")
    assert SECRET not in json.dumps(task.model_dump(mode="json"))
    stored = (store.reviews_dir("DR-0001") / "review-01-result.json").read_text(encoding="utf-8")
    meta = (store.reviews_dir("DR-0001") / "review-01-meta.json").read_text(encoding="utf-8")
    assert SECRET not in stored and SECRET not in meta
    assert "[REDACTED]" in stored
    # structure survives redaction
    assert task.review_history[0].findings[0].severity is Severity.P2
    assert task.review_history[0].findings[0].title == "leaky"


# ---------------------------------------------------------------------------
# A19: opt-in stagnation guard
# ---------------------------------------------------------------------------
def test_repeated_finding_blocks_as_stalled(tmp_path):
    config = default_config()
    config.pipeline.max_same_finding_cycles = 2
    same = [
        make_review("REQUEST_CHANGES", [make_finding("P2", title="same blocker")]),
        make_review("REQUEST_CHANGES", [make_finding("P2", title="same blocker")]),
    ]
    store, engine = _start(tmp_path, config=config, reviewer=ScriptedAutoReviewer(same))
    engine.continue_task("DR-0001")

    task = store.read_task("DR-0001")
    assert task.state == S.BLOCKED
    assert task.blocked_code == "review_stalled"
    assert "same blocker" in (task.blocked_reason or "")
    counts = list(task.finding_seen_counts.values())
    assert counts == [2]


def test_stagnation_guard_disabled_by_default(tmp_path):
    config = default_config()
    assert config.pipeline.max_same_finding_cycles == 0
    same = [
        make_review("REQUEST_CHANGES", [make_finding("P2", title="same blocker")]),
        make_review("REQUEST_CHANGES", [make_finding("P2", title="same blocker")]),
        make_review("PASS"),
    ]
    store, engine = _start(tmp_path, config=config, reviewer=ScriptedAutoReviewer(same))
    engine.continue_task("DR-0001")
    # With the guard disabled the loop keeps fixing until the reviewer passes.
    assert store.read_task("DR-0001").state == S.FINAL_GATE_REQUIRED


# ---------------------------------------------------------------------------
# A20: final gate stays manual
# ---------------------------------------------------------------------------
def test_final_gate_stays_manual(tmp_path):
    reviewer = ScriptedAutoReviewer([make_review("PASS")])
    store, engine = _start(tmp_path, reviewer=reviewer)
    engine.continue_task("DR-0001")

    task = store.read_task("DR-0001")
    assert task.state == S.FINAL_GATE_REQUIRED
    assert task.final_gate is None
    engine.continue_task("DR-0001")            # never auto-approves
    assert store.read_task("DR-0001").state == S.FINAL_GATE_REQUIRED
    engine.approve_final("DR-0001", note="human gate")
    assert store.read_task("DR-0001").state == S.DONE


# ---------------------------------------------------------------------------
# Review evidence: format retry keeps both call artifacts (engine + real provider)
# ---------------------------------------------------------------------------
def test_format_retry_evidence_is_preserved(tmp_path):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        content = "not json" if calls["n"] == 1 else VALID
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://review.example/v1")
    reviewer = OpenAICompatibleReviewer(
        ReviewerEndpoint(base_url="https://review.example/v1", api_key="k", model="m"),
        retries=1,
        client=client,
    )
    store, engine = _start(tmp_path, reviewer=reviewer)
    engine.continue_task("DR-0001")

    task = store.read_task("DR-0001")
    assert task.state == S.FINAL_GATE_REQUIRED
    assert len(task.provider_calls) == 3       # 1 implementer + 2 reviewer calls
    phases = [r.phase for r in task.provider_calls if r.provider_kind.value == "REVIEWER"]
    assert phases == [ProviderCallPhase.REVIEW, ProviderCallPhase.REVIEW_FORMAT_RETRY]
    assert sum(r.external_call_count for r in task.provider_calls) == 3  # 1 impl + 2 reviewer
    assert task.review_attempts[-1].external_calls_consumed == 2

    reviews = store.reviews_dir("DR-0001")
    call1 = json.loads((reviews / "review-01-call-01-meta.json").read_text(encoding="utf-8"))
    call2 = json.loads((reviews / "review-01-call-02-meta.json").read_text(encoding="utf-8"))
    assert call1["phase"] == "REVIEW" and call1["error_type"] == "FORMAT"
    assert call2["phase"] == "REVIEW_FORMAT_RETRY" and call2["success"] is True
