"""v0.3-E local attribution: the reconcile report's ledger section.

These tests exist because review found a real defect behind this surface: the
report's ledger section was silently blank (``gap_reason == ""``) for *every*
v2 run, because the floor computation passed a list where a call id was
expected and the resulting ``TypeError`` was swallowed by the best-effort
evidence collector.  The suite that shipped with the implementation asserted
only that the outcome was "one of" the honest outcomes, so a permanently
blank section passed.

The contract pinned here: a report never shows an unexplained blank.  It either
attributes the interrupted submission to exactly one ledger record (with a
proven interval when a floor exists), or it reports a gap *with its reason*.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from devrelay.orchestration import recovery
from devrelay.orchestration.ledger_reader import (
    OUTCOME_EXACTLY_ONE,
    OUTCOME_GAP,
)
from devrelay.orchestration.models import RunState
from v03d_helpers import (
    RUN_ID,
    build,
    call,
    dying_stub,
    fixed_run_ids,
    honest_run,
    phase,
    raw_payload,
    run_id_of,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def crashed_run(tmp_path: Path, *, on_post: int = 1):
    """A real crash at the *on_post*-th submission leaves a live v2 intent."""
    stub = dying_stub(tmp_path / "ws", on_post=on_post)
    harness = build(tmp_path, stub=stub, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)
    if on_post == 2:
        assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is True
        tool = "devrelay_run_reviewer"
    else:
        tool = "devrelay_run_implementer"
    with pytest.raises(SystemExit):
        phase(harness.server, tool, run_id, "crashed prompt")
    return harness, run_id


def reconcile(server, run_id: str):
    return call(server, "devrelay_reconcile_run", {"run_id": run_id})


def assert_honest(ledger: dict) -> None:
    """No unexplained blank: a gap always carries a reason."""
    if ledger["outcome"] == OUTCOME_GAP:
        assert ledger["gap_reason"], ledger
    if ledger["interval_proven"]:
        assert ledger["floor"] and ledger["ceiling"], ledger
    if ledger["call_id"]:
        assert ledger["outcome"] == OUTCOME_EXACTLY_ONE, ledger


# ---------------------------------------------------------------------------
# attribution
# ---------------------------------------------------------------------------
def test_an_interrupted_reviewer_turn_is_attributed_over_a_proven_interval(
    tmp_path: Path,
) -> None:
    harness, run_id = crashed_run(tmp_path, on_post=2)
    persisted = raw_payload(harness.ws, run_id)
    implementer_call_id = persisted["implementer_turns"][0]["call_ids"][-1]

    envelope = reconcile(harness.server, run_id)
    assert envelope["ok"] is True, envelope
    ledger = envelope["data"]["ledger"]
    assert_honest(ledger)

    assert ledger["outcome"] == OUTCOME_EXACTLY_ONE
    assert ledger["call_id"] and ledger["call_id"] != implementer_call_id
    assert ledger["floor"] == implementer_call_id, "the floor is the newest finalized call"
    assert ledger["ceiling"] == ledger["call_id"], "every allocated id is at or below the ceiling"
    assert ledger["interval_proven"] is True
    assert ledger["candidate_count"] == 1
    assert ledger["gap_reason"] == ""
    # the crashed POST reached the transport but never produced a reply
    assert ledger["state"] in {"ISSUED", "COMPLETED"}
    assert ledger["http_status"] is None or ledger["http_status"] == 200


def test_a_first_turn_crash_reports_an_unproven_floor(tmp_path: Path) -> None:
    harness, run_id = crashed_run(tmp_path, on_post=1)
    envelope = reconcile(harness.server, run_id)
    assert envelope["ok"] is True, envelope
    ledger = envelope["data"]["ledger"]
    assert_honest(ledger)

    # there is no finalized turn before the interrupted attempt, so no durable
    # floor exists and the interval must not be claimed as proven
    assert ledger["floor"] == ""
    assert ledger["interval_proven"] is False
    assert ledger["outcome"] == OUTCOME_EXACTLY_ONE
    assert ledger["ceiling"] == ledger["call_id"]


def test_a_missing_match_without_a_floor_is_a_reasoned_gap(tmp_path: Path) -> None:
    harness, run_id = crashed_run(tmp_path, on_post=1)
    calls = sorted((harness.ws / ".devrelay" / "opencode" / "calls").glob("OC-*.json"))
    assert calls, "the crashed submission should have been recorded before transport"
    for path in calls:
        path.unlink()

    envelope = reconcile(harness.server, run_id)
    assert envelope["ok"] is True, envelope
    ledger = envelope["data"]["ledger"]
    assert_honest(ledger)
    assert ledger["outcome"] == OUTCOME_GAP
    assert ledger["call_id"] == ""
    # whichever boundary the reader hits first, the gap names it: the allocated
    # id whose record vanished, or the absent durable floor
    assert "accounting record" in ledger["gap_reason"] or "no durable floor" in ledger["gap_reason"]
    assert "cannot be proven" in ledger["gap_reason"] or "absence unproven" in ledger["gap_reason"]
    assert ledger["interval_proven"] is False


def test_a_broken_accounting_surface_becomes_a_reasoned_gap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    harness, run_id = crashed_run(tmp_path)
    before = (harness.ws / ".devrelay" / "orchestration" / "runs" / f"{run_id}.json").read_bytes()

    def broken(*args, **kwargs):
        raise RuntimeError("the durable surface is unreadable")

    monkeypatch.setattr("devrelay.orchestration.ledger_reader.scan_ledger", broken)

    envelope = reconcile(harness.server, run_id)
    assert envelope["ok"] is True, envelope
    ledger = envelope["data"]["ledger"]
    assert_honest(ledger)
    assert ledger["outcome"] == OUTCOME_GAP
    assert "could not be scanned" in ledger["gap_reason"]
    assert "RuntimeError" in ledger["gap_reason"]
    # a failed scan is evidence, not a write
    after = (harness.ws / ".devrelay" / "orchestration" / "runs" / f"{run_id}.json").read_bytes()
    assert after == before


def test_a_quiet_run_reports_no_turn_to_attribute(tmp_path: Path) -> None:
    harness = build(tmp_path)
    run_id = run_id_of(harness.server, max_cycles=1)
    envelope = reconcile(harness.server, run_id)
    assert envelope["ok"] is True, envelope
    data = envelope["data"]
    assert_honest(data["ledger"])
    assert data["attempt"] is None
    assert data["ledger"]["gap_reason"].startswith("no turn to attribute")
    assert data["remote"]["gap_reason"], "an unread session history is a named gap too"


def test_the_floor_uses_the_newest_call_id_across_finalized_turns() -> None:
    run = honest_run(RunState.BLOCKED, max_cycles=2)
    run.implementer_turns[0].call_ids = ["OC-0002", "OC-0009"]
    run.reviewer_turns = []
    assert recovery.previous_floor(run) == "OC-0009"

    run.implementer_turns[0].call_ids = []
    run.reviewer_turns = [run.implementer_turns[0].model_copy(update={"role": "reviewer"})]
    run.reviewer_turns[0].call_ids = ["OC-0011"]
    run.implementer_turns = [run.implementer_turns[0]]
    assert recovery.previous_floor(run) == "OC-0011"


def test_the_newest_call_id_accepts_ids_in_any_order() -> None:
    from devrelay.orchestration.ledger_reader import newest_call_id

    assert newest_call_id("OC-0009", "OC-0011", "OC-0002") == "OC-0011"
    assert newest_call_id() == ""
    assert newest_call_id("", "not-a-call", "OC-0004") == "OC-0004"


def test_evidence_records_the_attributed_call_id(tmp_path: Path) -> None:
    """mark_unrecoverable freezes the attributed ledger evidence, not a blank."""
    harness, run_id = crashed_run(tmp_path, on_post=2)
    envelope = call(
        harness.server,
        "devrelay_resolve_recovery",
        {"run_id": run_id, "resolution": "mark_unrecoverable"},
    )
    assert envelope["ok"] is True, envelope
    data = envelope["data"]
    assert data["state"] == "BLOCKED"
    # W3: the reviewer submission died with its durable ledger record still
    # ISSUED, so the honest reason is an uncertain submission.
    assert data["blocked_reason"] == "submission_uncertain"
    evidence = data["recovery"]["evidence"]
    assert evidence["ledger_call_id"].startswith("OC-")
    assert evidence["ledger_state"]
    assert evidence["coverage"]
    # the frozen digest still verifies over the evidence it carries
    persisted = json.loads(
        (harness.ws / ".devrelay" / "orchestration" / "runs" / f"{run_id}.json").read_text()
    )
    assert persisted["recovery"]["evidence"]["ledger_call_id"] == evidence["ledger_call_id"]
