"""v0.3-E fail-closed recovery: the mandatory core, end to end.

Every crash boundary here is produced by a real ``SystemExit`` inside a
production call path (stub transport, ledger settlement, or ``store.save``),
never by hand-writing a "busy" document, so the interrupted intent being
recovered is exactly the one the service durably committed.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from devrelay.orchestration import recovery
from devrelay.orchestration.models import (
    LEGACY_SCHEMA_VERSION,
    ORCHESTRATION_SCHEMA_VERSION,
    OrchestrationAction,
    RecoveryRecord,
    RunState,
    TransitionRecord,
)
from devrelay.orchestration.state_machine import after_enter_recovery, transition_record
from v03d_helpers import (
    RUN_ID,
    build,
    call,
    decide,
    dying_stub,
    fixed_run_ids,
    freeze_v03d,
    get_run,
    phase,
    prompt_posts,
    raw_payload,
    restart_surface,
    run_id_of,
    state_path,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def crashed_run(tmp_path: Path, *, on_post: int = 1, max_cycles: int = 1):
    """A real crash at the *on_post*-th submission leaves a live v2 intent."""
    stub = dying_stub(tmp_path / "ws", on_post=on_post)
    harness = build(tmp_path, stub=stub, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=max_cycles)
    if on_post == 2:
        assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is True
        tool = "devrelay_run_reviewer"
    else:
        tool = "devrelay_run_implementer"
    with pytest.raises(SystemExit):
        phase(harness.server, tool, run_id, "crashed prompt")
    return harness, run_id


def document_bytes(ws: Path, run_id: str) -> bytes:
    return state_path(ws, run_id).read_bytes()


def tree_snapshot(ws: Path) -> dict[str, str]:
    """Every durable file under ``.devrelay`` with its SHA-256.

    A "read-only" tool must leave this *exactly* equal - including the accounting
    ledger and its call sequence, which a session-history read would otherwise
    append to.
    """
    base = ws / ".devrelay"
    snapshot: dict[str, str] = {}
    for path in sorted(base.rglob("*")):
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            snapshot[str(path.relative_to(base))] = digest
    return snapshot


def resolve(server, run_id: str, resolution: str):
    return call(
        server,
        "devrelay_resolve_recovery",
        {"run_id": run_id, "resolution": resolution},
    )


def reconcile(server, run_id: str):
    return call(server, "devrelay_reconcile_run", {"run_id": run_id})


def refusal(envelope, code: str) -> None:
    assert envelope["ok"] is False, envelope
    assert envelope["error"]["type"] == code, envelope["error"]


# ---------------------------------------------------------------------------
# entry: a v2 live intent freezes every mutating phase action
# ---------------------------------------------------------------------------
def test_a_live_v2_intent_refuses_every_mutating_phase_action(tmp_path: Path) -> None:
    harness, run_id = crashed_run(tmp_path)
    before = document_bytes(harness.ws, run_id)

    for tool, prompt in (
        ("devrelay_run_implementer", "i"),
        ("devrelay_run_reviewer", "r"),
    ):
        envelope = phase(harness.server, tool, run_id, prompt)
        refusal(envelope, "orchestration_recovery_required")
        assert envelope["data"]["state"] == "READY_IMPLEMENTER"
        assert envelope["data"]["in_flight"] is True
        assert document_bytes(harness.ws, run_id) == before, "a refusal must not write"

    refusal(decide(harness.server, run_id, "complete"), "orchestration_recovery_required")
    assert document_bytes(harness.ws, run_id) == before
    assert prompt_posts(harness.stub) == [], (
        "the refusal must not submit anything (the dying POST is never recorded)"
    )


def test_get_run_reports_the_frozen_v2_intent(tmp_path: Path) -> None:
    harness, run_id = crashed_run(tmp_path)
    envelope = get_run(harness.server, run_id)
    assert envelope["ok"] is True
    data = envelope["data"]
    assert data["schema_version"] == ORCHESTRATION_SCHEMA_VERSION == 2
    assert data["in_flight"] is True
    assert data["state"] == "READY_IMPLEMENTER"
    assert data["legal_next_actions"] == ["devrelay_resolve_recovery"]


# ---------------------------------------------------------------------------
# reconcile: read-only, honest, and explicit about what it cannot prove
# ---------------------------------------------------------------------------
def test_reconcile_is_read_only_and_reports_the_honest_evidence(
    tmp_path: Path,
) -> None:
    harness, run_id = crashed_run(tmp_path)
    before = document_bytes(harness.ws, run_id)
    posts = prompt_posts(harness.stub)
    durable_before = tree_snapshot(harness.ws)

    envelope = reconcile(harness.server, run_id)
    assert envelope["ok"] is True, envelope
    data = envelope["data"]
    assert data["run_id"] == run_id
    assert data["state"] == "READY_IMPLEMENTER"
    assert data["terminal"] is False
    assert data["recoverable"] is True
    assert data["v1_frozen"] is False
    # W3: the request may already have left the machine - the durable ledger
    # record is still ISSUED, so the submission is uncertain, not interrupted.
    assert data["recovery_reason"] == "submission_uncertain"
    assert data["ledger"]["outcome"] == "exactly_one_match"
    assert data["ledger"]["state"] == "ISSUED"
    assert data["recovery"] is None, "nothing is materialized by a read"
    assert data["attempt"]["role"] == "implementer"
    assert data["adoption"]["available"] is False
    assert data["adoption"]["reason"] == recovery.ADOPTION_DISABLED_REASON
    assert data["adoption"]["candidate"] is None
    assert data["ledger"]["outcome"] in {
        "exactly_one_match",
        "no_record_in_proven_interval",
        "evidence_gap",
        "multiple_matches",
    }
    # The mandatory core is local-only: no session history is read, because an
    # OpenCode read is ledger-accounted and would mutate the surface below.
    assert data["remote"]["outcome"] == "evidence_gap"
    assert data["remote"]["gap_reason"] == recovery.REMOTE_NOT_READ_REASON
    assert data["budget"]["turn_attempts"] == 1
    assert data["budget"]["model_turns_used"] == 1
    assert data["submission"]["submitted_by_recovery"] is False
    assert data["legal_next_actions"] == ["devrelay_resolve_recovery"]
    assert "never" in data["note"] or "read-only" in data["note"]
    checklist = data["checklist"]
    assert checklist, "the report carries the per-item adoption checklist"
    assert {(entry["item"], entry["status"]) for entry in checklist} >= {
        ("ledger attribution", "pass"),
        ("adoption capability", "fail"),
        ("remote correlation", "unknown"),
    }
    assert all(entry["status"] in {"pass", "fail", "unknown"} for entry in checklist)
    assert data["blockers"], "a disabled capability must be reported as a blocker"
    assert any("adoption is disabled" in line for line in data["blockers"])

    assert document_bytes(harness.ws, run_id) == before, "reconcile never writes"
    assert tree_snapshot(harness.ws) == durable_before, (
        "reconcile is byte-identical: no ledger append, no sequence rewrite, no record"
    )
    assert prompt_posts(harness.stub) == posts, "reconcile never submits"

    # what the durable document says is what the report says
    persisted = raw_payload(harness.ws, run_id)
    assert persisted["schema_version"] == 2
    assert persisted["in_flight_turn"]["role"] == "implementer"
    assert persisted["in_flight_turn"]["prompt_sha256"] == data["attempt"]["prompt_sha256"]


def test_reconcile_on_a_quiet_run_reports_nothing_to_recover(tmp_path: Path) -> None:
    harness = build(tmp_path)
    run_id = run_id_of(harness.server, max_cycles=1)
    envelope = reconcile(harness.server, run_id)
    assert envelope["ok"] is True, envelope
    data = envelope["data"]
    assert data["state"] == "READY_IMPLEMENTER"
    assert data["budget"]["in_flight"] is False
    assert data["recoverable"] is False
    assert data["attempt"] is None
    assert data["recovery"] is None
    assert data["ledger"]["interval_proven"] is False
    assert data["legal_next_actions"] == ["devrelay_run_implementer"]
    assert prompt_posts(harness.stub) == []


# ---------------------------------------------------------------------------
# resolve: exactly one blocked turn, exactly one write
# ---------------------------------------------------------------------------
def test_mark_unrecoverable_materializes_exactly_one_blocked_turn(tmp_path: Path) -> None:
    harness, run_id = crashed_run(tmp_path)
    posts = prompt_posts(harness.stub)
    before = raw_payload(harness.ws, run_id)
    accounting_before = {
        key: value
        for key, value in tree_snapshot(harness.ws).items()
        if key.startswith("opencode/")
    }

    envelope = resolve(harness.server, run_id, "mark_unrecoverable")
    assert envelope["ok"] is True, envelope
    data = envelope["data"]
    assert data["state"] == "BLOCKED"
    assert data["terminal"] is True
    assert data["in_flight"] is False
    assert data["blocked_reason"] == "submission_uncertain"
    assert data["recovery_reason"] == "submission_uncertain"
    assert data["legal_next_actions"] == []
    assert data["model_turns_used"] == before["model_turns_used"] == 1
    assert data["turn_attempts"] == before["turn_attempts"] == 1
    assert len(data["implementer_turns"]) == 1
    turn = data["implementer_turns"][0]
    assert turn["role"] == "implementer"
    assert turn["outcome"] == "blocked"
    assert turn["blocked_reason"] == "submission_uncertain"
    assert turn["completed_at"]
    assert turn["prompt_sha256"] == before["in_flight_turn"]["prompt_sha256"]
    assert data["reviewer_turns"] == []

    record = data["recovery"]
    assert record["resolution"] == "mark_unrecoverable"
    assert record["resolved_at"]
    assert record["recovery_reason"] == "submission_uncertain"
    assert record["attempt"]["outcome"] == "blocked"
    assert record["evidence"]["evidence_sha256"] == record["evidence"]["evidence_sha256"]
    assert record["evidence"]["attempt_call_ids"] == ",".join(
        before["in_flight_turn"]["call_ids"]
    )

    transition = data["last_transition"]
    assert transition["action"] == "recover"
    assert transition["source"] == "external_planner"
    assert transition["previous_state"] == "RECOVERY_REQUIRED"
    assert transition["next_state"] == "BLOCKED"
    assert transition["role"] == "implementer"

    assert prompt_posts(harness.stub) == posts, "recovery never submits a model turn"
    accounting_after = {
        key: value
        for key, value in tree_snapshot(harness.ws).items()
        if key.startswith("opencode/")
    }
    assert accounting_after == accounting_before, (
        "resolve never reads session history: a provider call would append ledger "
        "records and rewrite the call sequence"
    )

    persisted = raw_payload(harness.ws, run_id)
    assert persisted["state"] == "BLOCKED"
    assert persisted["in_flight_turn"] is None
    assert persisted["recovery"]["resolution"] == "mark_unrecoverable"


def test_recovery_is_write_once(tmp_path: Path) -> None:
    harness, run_id = crashed_run(tmp_path)
    first = resolve(harness.server, run_id, "mark_unrecoverable")
    assert first["ok"] is True, first
    after = document_bytes(harness.ws, run_id)

    second = resolve(harness.server, run_id, "mark_unrecoverable")
    refusal(second, "orchestration_recovery_already_resolved")
    assert "mark_unrecoverable" in second["error"]["message"]
    assert second["data"]["state"] == "BLOCKED"
    assert document_bytes(harness.ws, run_id) == after, "no second resolution is applied"

    third = resolve(harness.server, run_id, "adopt_completed_turn")
    refusal(third, "orchestration_recovery_already_resolved")
    assert document_bytes(harness.ws, run_id) == after


def test_adoption_is_refused_before_any_write(tmp_path: Path) -> None:
    harness, run_id = crashed_run(tmp_path)
    before = document_bytes(harness.ws, run_id)

    envelope = resolve(harness.server, run_id, "adopt_completed_turn")
    refusal(envelope, "orchestration_adoption_disabled")
    assert envelope["data"]["in_flight"] is True
    assert document_bytes(harness.ws, run_id) == before, "a disabled adoption writes nothing"
    assert prompt_posts(harness.stub) == [], "the dying POST is never recorded as served"

    # the mandatory core still has its one legal exit after the refusal
    assert resolve(harness.server, run_id, "mark_unrecoverable")["ok"] is True


def test_adoption_flag_flip_is_refused_before_any_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A flipped capability flag still refuses adoption before any write.

    The flag is a build-time constant, so this exercises the defence in depth
    inside the resolution path: even with adoption enabled, a materialized
    attempt that is not ``completed`` is refused as an invalid transition, and
    neither the run document nor the provider ledger is touched.
    """
    harness, run_id = crashed_run(tmp_path)
    before = document_bytes(harness.ws, run_id)
    posts = prompt_posts(harness.stub)
    monkeypatch.setattr(recovery, "ADOPTION_CAPABILITY_ENABLED", True)
    envelope = resolve(harness.server, run_id, "adopt_completed_turn")
    refusal(envelope, "orchestration_invalid_transition")
    assert "completed" in envelope["error"]["message"]
    assert document_bytes(harness.ws, run_id) == before
    assert prompt_posts(harness.stub) == posts


def test_unknown_resolutions_are_argument_errors(tmp_path: Path) -> None:
    harness, run_id = crashed_run(tmp_path)
    before = document_bytes(harness.ws, run_id)
    for value in ("adopt", "", "MARK_UNRECOVERABLE", None):
        envelope = call(
            harness.server,
            "devrelay_resolve_recovery",
            {"run_id": run_id, "resolution": value},
        )
        refusal(envelope, "mcp_invalid_argument")
        assert document_bytes(harness.ws, run_id) == before


def test_terminal_runs_are_never_reopened(tmp_path: Path) -> None:
    harness = build(tmp_path)
    run_id = run_id_of(harness.server, max_cycles=1)
    assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is True
    assert phase(harness.server, "devrelay_run_reviewer", run_id, "r")["ok"] is True
    assert decide(harness.server, run_id, "complete")["ok"] is True
    before = document_bytes(harness.ws, run_id)

    envelope = resolve(harness.server, run_id, "mark_unrecoverable")
    refusal(envelope, "orchestration_invalid_transition")
    assert document_bytes(harness.ws, run_id) == before

    # A terminal run has nothing left to reconcile: reconcile refuses locally
    # instead of presenting a "recoverable" report (V03E_SPEC.md §21), and the
    # refusal itself is byte-neutral.
    refusal(reconcile(harness.server, run_id), "orchestration_recovery_unsupported")
    assert document_bytes(harness.ws, run_id) == before

    # A terminal run is never reopened, not even through the disabled adoption
    # capability: the terminal check comes first, so the refusal is an invalid
    # transition rather than the adoption-disabled refusal.
    refusal(
        resolve(harness.server, run_id, "adopt_completed_turn"),
        "orchestration_invalid_transition",
    )
    assert document_bytes(harness.ws, run_id) == before


# ---------------------------------------------------------------------------
# frozen v1 documents keep the exact v0.3-D contract
# ---------------------------------------------------------------------------
def test_a_frozen_v1_document_refuses_recovery_and_fails_closed(tmp_path: Path) -> None:
    harness, run_id = crashed_run(tmp_path)
    freeze_v03d(harness.ws, run_id)
    before = document_bytes(harness.ws, run_id)

    report = reconcile(harness.server, run_id)
    assert report["ok"] is True, report
    assert report["data"]["schema_version"] == LEGACY_SCHEMA_VERSION == 1
    assert report["data"]["v1_frozen"] is True
    assert report["data"]["recoverable"] is False
    assert "v1" in report["data"]["note"]
    refusal(resolve(harness.server, run_id, "mark_unrecoverable"), "orchestration_recovery_unsupported")
    assert document_bytes(harness.ws, run_id) == before, "v1 is never migrated"

    # ... and the frozen v0.3-D materialization still happens exactly once
    envelope = phase(harness.server, "devrelay_run_implementer", run_id, "i")
    assert envelope["ok"] is False
    assert envelope["data"]["state"] == "BLOCKED"
    assert envelope["data"]["blocked_reason"] == "turn_interrupted"
    refusal(
        resolve(harness.server, run_id, "mark_unrecoverable"),
        "orchestration_recovery_unsupported",
    )


# ---------------------------------------------------------------------------
# entry from a READY_REVIEWER live intent
# ---------------------------------------------------------------------------
def test_a_crashed_reviewer_turn_resolves_as_a_blocked_reviewer_turn(
    tmp_path: Path,
) -> None:
    harness, run_id = crashed_run(tmp_path, on_post=2)
    report = reconcile(harness.server, run_id)
    assert report["ok"] is True, report
    assert report["data"]["state"] == "READY_REVIEWER"
    assert report["data"]["attempt"]["role"] == "reviewer"
    assert report["data"]["recovery_reason"] == "submission_uncertain"

    envelope = resolve(harness.server, run_id, "mark_unrecoverable")
    assert envelope["ok"] is True, envelope
    data = envelope["data"]
    assert data["state"] == "BLOCKED"
    assert data["blocked_reason"] == "submission_uncertain"
    assert [turn["outcome"] for turn in data["implementer_turns"]] == ["completed"]
    assert [turn["outcome"] for turn in data["reviewer_turns"]] == ["blocked"]
    assert data["recovery"]["attempt"]["role"] == "reviewer"
    assert data["last_transition"]["role"] == "reviewer"
    assert prompt_posts(harness.stub) == ["/session/ses_impl/message"], (
        "only the completed implementer submission was served; the reviewer POST died"
    )


# ---------------------------------------------------------------------------
# restart matrix: the durable document is the only truth
# ---------------------------------------------------------------------------
def test_a_restart_reads_the_same_live_intent_and_resolves_it(tmp_path: Path) -> None:
    harness, run_id = crashed_run(tmp_path)
    restarted = restart_surface(harness)

    read = get_run(restarted.server, run_id)
    assert read["ok"] is True
    assert read["data"]["in_flight"] is True
    assert read["data"]["state"] == "READY_IMPLEMENTER"
    assert read["data"]["legal_next_actions"] == ["devrelay_resolve_recovery"]
    assert prompt_posts(restarted.stub) == [], "a restart never replays the intent"

    envelope = resolve(restarted.server, run_id, "mark_unrecoverable")
    assert envelope["ok"] is True, envelope
    assert envelope["data"]["state"] == "BLOCKED"
    assert prompt_posts(restarted.stub) == []
    assert raw_payload(restarted.ws, run_id)["recovery"]["resolution"] == "mark_unrecoverable"


def test_a_restart_after_resolution_sees_a_settled_blocked_run(tmp_path: Path) -> None:
    harness, run_id = crashed_run(tmp_path)
    assert resolve(harness.server, run_id, "mark_unrecoverable")["ok"] is True
    restarted = restart_surface(harness)

    read = get_run(restarted.server, run_id)
    assert read["ok"] is True
    assert read["data"]["state"] == "BLOCKED"
    assert read["data"]["in_flight"] is False
    assert read["data"]["recovery"]["resolution"] == "mark_unrecoverable"
    assert read["data"]["legal_next_actions"] == []
    refusal(
        resolve(restarted.server, run_id, "mark_unrecoverable"),
        "orchestration_recovery_already_resolved",
    )


# ---------------------------------------------------------------------------
# the RECOVERY_REQUIRED document shape (a persisted, unresolved record)
# ---------------------------------------------------------------------------
def _persist_recovery_required(harness, run_id: str) -> None:
    """Materialize the crash intent into a persisted, unresolved record."""
    store = harness.service.store
    run = store.load(run_id)
    attempt = run.in_flight_turn
    assert attempt is not None
    scan = harness.service._local_evidence(run, attempt)
    reason = recovery.infer_recovery_reason(attempt, scan)
    evidence, frozen = recovery.build_record(
        run,
        attempt,
        entry_state=run.state,
        reason=reason,
        ledger_scan=scan,
        remote=recovery.RemoteMatch(recovery.REMOTE_GAP),
    )
    run.in_flight_turn = None
    run.recovery = RecoveryRecord(attempt=frozen, recovery_reason=reason, evidence=evidence)
    run.recovery_reason = reason
    transition = after_enter_recovery(run)
    record = transition_record(
        action=OrchestrationAction.RECOVER,
        source="external_planner",
        run=run,
        next_state=transition.state,
        role=attempt.role,
    )
    transition.apply(run, record)
    store.save(run)


def test_a_persisted_recovery_required_document_resolves_in_place(tmp_path: Path) -> None:
    harness, run_id = crashed_run(tmp_path)
    _persist_recovery_required(harness, run_id)

    persisted = raw_payload(harness.ws, run_id)
    assert persisted["state"] == "RECOVERY_REQUIRED"
    assert persisted["in_flight_turn"] is None
    assert persisted["recovery"]["resolution"] == ""

    before = document_bytes(harness.ws, run_id)
    report = reconcile(harness.server, run_id)
    assert report["ok"] is True, report
    assert report["data"]["state"] == "RECOVERY_REQUIRED"
    assert report["data"]["recoverable"] is True
    assert report["data"]["recovery_reason"] == "submission_uncertain"
    assert report["data"]["legal_next_actions"] == [
        "devrelay_reconcile_run",
        "devrelay_resolve_recovery(mark_unrecoverable)",
    ]
    assert document_bytes(harness.ws, run_id) == before

    refusal(decide(harness.server, run_id, "complete"), "orchestration_recovery_required")
    refusal(
        phase(harness.server, "devrelay_run_implementer", run_id, "i"),
        "orchestration_recovery_required",
    )
    assert document_bytes(harness.ws, run_id) == before

    envelope = resolve(harness.server, run_id, "mark_unrecoverable")
    assert envelope["ok"] is True, envelope
    assert envelope["data"]["state"] == "BLOCKED"
    assert envelope["data"]["blocked_reason"] == "submission_uncertain"
    assert len(envelope["data"]["implementer_turns"]) == 1


def test_a_persisted_recovery_required_document_survives_a_restart(tmp_path: Path) -> None:
    harness, run_id = crashed_run(tmp_path)
    _persist_recovery_required(harness, run_id)
    restarted = restart_surface(harness)

    read = get_run(restarted.server, run_id)
    assert read["ok"] is True, read
    assert read["data"]["state"] == "RECOVERY_REQUIRED"
    assert read["data"]["in_flight"] is False
    assert read["data"]["legal_next_actions"] == [
        "devrelay_reconcile_run",
        "devrelay_resolve_recovery(mark_unrecoverable)",
    ]

    envelope = resolve(restarted.server, run_id, "mark_unrecoverable")
    assert envelope["ok"] is True, envelope
    assert envelope["data"]["state"] == "BLOCKED"


# ---------------------------------------------------------------------------
# §16 crash-window matrix: the reason follows the durable ledger, not the crash
# ---------------------------------------------------------------------------
def test_w1_a_crash_before_the_request_left_the_machine_is_just_interrupted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """W1: no HTTP call happened, so nothing may claim a submission."""
    from devrelay.roles.service import RoleRouter

    def exploding_send(*args: object, **kwargs: object) -> None:
        raise SystemExit("simulated process death before the request left the machine")

    monkeypatch.setattr(RoleRouter, "send_role_prompt", exploding_send)
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)

    with pytest.raises(SystemExit):
        phase(harness.server, "devrelay_run_implementer", run_id, "w1 prompt")

    report = reconcile(harness.server, run_id)
    assert report["ok"] is True, report
    data = report["data"]
    assert data["recoverable"] is True
    assert data["recovery_reason"] == "turn_interrupted"
    # nothing was submitted, so no ledger record can attribute a submission
    assert data["ledger"]["state"] == ""
    assert data["ledger"]["outcome"] in {"evidence_gap", "no_record_in_proven_interval"}
    assert prompt_posts(harness.stub) == []


def test_w4_a_settle_that_never_became_durable_is_still_an_uncertain_submission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """W4: the response arrived, but the settle never became durable."""
    from devrelay.opencode.accounting import FilesystemOpenCodeLedger
    from devrelay.opencode.models import OpenCodeCallState
    from devrelay.orchestration.ledger_reader import SUBMISSION_OPERATION

    original_finish = FilesystemOpenCodeLedger.finish

    def exploding_finish(self, record):
        if (
            record.operation == SUBMISSION_OPERATION
            and record.method == "POST"
            and record.state is OpenCodeCallState.COMPLETED
        ):
            raise SystemExit("simulated process death before the settle became durable")
        return original_finish(self, record)

    monkeypatch.setattr(FilesystemOpenCodeLedger, "finish", exploding_finish)
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)

    with pytest.raises(SystemExit):
        phase(harness.server, "devrelay_run_implementer", run_id, "w4 prompt")

    report = reconcile(harness.server, run_id)
    assert report["ok"] is True, report
    data = report["data"]
    assert data["recovery_reason"] == "submission_uncertain"
    assert data["ledger"]["outcome"] == "exactly_one_match"
    assert data["ledger"]["state"] == "ISSUED", (
        "the durable record never settled: the submission may have been delivered"
    )
    assert prompt_posts(harness.stub) == ["/session/ses_impl/message"]


def test_w5_an_accepted_call_whose_turn_was_never_persisted_is_reply_pending(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """W5/W6: the provider accepted the call, the local result did not survive."""
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)

    original_save = harness.service.store.save

    def exploding_save(run):
        if run.in_flight_turn is None and run.turn_attempts >= 1:
            raise SystemExit("simulated process death before the finished turn was persisted")
        return original_save(run)

    monkeypatch.setattr(harness.service.store, "save", exploding_save)

    with pytest.raises(SystemExit):
        phase(harness.server, "devrelay_run_implementer", run_id, "w5 prompt")

    # the crash window is over: the recovery write itself must succeed
    monkeypatch.setattr(harness.service.store, "save", original_save)

    # the document still shows the interrupted intent, the ledger shows acceptance
    persisted = raw_payload(harness.ws, run_id)
    assert persisted["in_flight_turn"] is not None
    assert persisted["implementer_turns"] == []

    report = reconcile(harness.server, run_id)
    assert report["ok"] is True, report
    data = report["data"]
    assert data["recovery_reason"] == "reply_pending"
    assert data["ledger"]["outcome"] == "exactly_one_match"
    assert data["ledger"]["state"] == "COMPLETED"
    assert 200 <= data["ledger"]["http_status"] < 300

    envelope = resolve(harness.server, run_id, "mark_unrecoverable")
    assert envelope["ok"] is True, envelope
    assert envelope["data"]["state"] == "BLOCKED"
    assert envelope["data"]["blocked_reason"] == "reply_pending"


def test_w1_proven_absence_is_reported_as_an_unconfirmed_attribution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """W1 with a floor: a proven interval only bounds the search.

    The implementer turn completes first, so the crashed reviewer attempt gets a
    proven floor and ceiling, and the process then dies before the request leaves
    the machine.  Per SPEC §9 / E44 that absence is *not* proof of non-delivery:
    the checklist must report an unconfirmed attribution (not "unknown because no
    interval is proven", and not a pass).
    """
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)
    assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is True

    def die_before_submission(*args: object, **kwargs: object) -> None:
        raise SystemExit("crash before submission")

    monkeypatch.setattr(harness.service._router, "send_role_prompt", die_before_submission)
    with pytest.raises(SystemExit):
        phase(harness.server, "devrelay_run_reviewer", run_id, "r")

    report = reconcile(harness.server, run_id)
    assert report["ok"] is True, report
    data = report["data"]
    assert data["recovery_reason"] == "turn_interrupted"
    assert data["ledger"]["outcome"] == "no_record_in_proven_interval"
    assert data["ledger"]["interval_proven"] is True
    assert data["ledger"]["gap_reason"] == ""
    attribution = next(
        item for item in data["checklist"] if item["item"] == "ledger attribution"
    )
    assert attribution["status"] == "unknown"
    assert "no DevRelay ledger record" in attribution["detail"]
    assert "proven interval" in attribution["detail"]
    assert "not submitted" not in attribution["detail"]
    assert "never submitted" not in attribution["detail"]
    assert "no proven interval" not in attribution["detail"]
