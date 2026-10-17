"""v0.3-E ledger reconciliation: the read-only proof of what a turn submitted."""

from __future__ import annotations

import json
from pathlib import Path

from devrelay.opencode.accounting import FilesystemOpenCodeLedger
from devrelay.opencode.models import OpenCodeCallRecord, OpenCodeCallState
from devrelay.orchestration import ledger_reader
from devrelay.orchestration.ledger_reader import LedgerIdentity, newest_call_id, scan_ledger

SESSION = "ses_impl"
DIGEST = "a" * 64


def identity(*, digest: str = DIGEST, chars: int = 11, model: str = "model-a") -> LedgerIdentity:
    return LedgerIdentity(
        session_id=SESSION,
        prompt_sha256=digest,
        prompt_chars=chars,
        resolved_model=model,
        resolved_agent="agent-a",
    )


def ledger_for(tmp_path: Path) -> FilesystemOpenCodeLedger:
    return FilesystemOpenCodeLedger(tmp_path / ".devrelay")


def write(
    ledger: FilesystemOpenCodeLedger,
    *,
    session: str = SESSION,
    digest: str = DIGEST,
    chars: int = 11,
    model: str = "model-a",
    agent: str = "agent-a",
    operation: str = "send_prompt",
    state: OpenCodeCallState | None = OpenCodeCallState.COMPLETED,
    call_id: str | None = None,
) -> str:
    call_id = call_id or ledger.allocate_call_id()
    record = OpenCodeCallRecord(
        call_id=call_id,
        operation=operation,
        state=state if state is not None else OpenCodeCallState.ISSUED,
        session_id=session,
        prompt_sha256=digest,
        prompt_chars=chars,
        model=model,
        agent=agent,
        http_status=200,
        response_media_type="application/json",
        completed_at="2026-10-17T10:00:00+00:00",
        submission_uncertain=False,
    )
    ledger.begin(record)
    ledger.finish(record)
    return call_id


def test_exactly_one_record_in_the_proven_interval_is_the_only_success(tmp_path: Path) -> None:
    ledger = ledger_for(tmp_path)
    call_id = write(ledger)
    scan = scan_ledger(tmp_path / ".devrelay", identity())
    assert scan.outcome == "exactly_one_match"
    assert scan.record is not None
    assert scan.record.call_id == call_id
    assert scan.floor == ""
    assert scan.ceiling == "OC-0001"
    # the *match* is certain; the empty interval itself is not "proven", so a
    # later absence in this run can never be trusted as proof
    assert scan.interval_proven is False
    assert scan.candidate_count == 1
    assert scan.gap_reason == ""
    assert scan.route_disagreement is False
    assert scan.evidence == {}  # the caller builds the frozen evidence from `record`


def test_the_floor_is_the_largest_finalized_call_id(tmp_path: Path) -> None:
    ledger = ledger_for(tmp_path)
    first = write(ledger)
    second = write(ledger)
    scan = scan_ledger(tmp_path / ".devrelay", identity(digest="b" * 64), floor=second)
    assert scan.floor == second
    assert scan.ceiling == second
    assert scan.outcome == "no_record_in_proven_interval"
    assert scan.candidate_count == 0
    assert scan.interval_proven is True
    # a digest that only matches the older call is below the floor: still absent
    assert first < second


def test_a_missing_match_without_a_proven_floor_is_an_evidence_gap(tmp_path: Path) -> None:
    ledger = ledger_for(tmp_path)
    write(ledger)
    scan = scan_ledger(tmp_path / ".devrelay", identity(digest="c" * 64))
    assert scan.outcome == "evidence_gap"
    assert scan.record is None
    assert scan.interval_proven is False
    assert scan.candidate_count == 0
    assert scan.gap_reason


def test_two_records_with_the_same_identity_are_never_guessed_apart(tmp_path: Path) -> None:
    ledger = ledger_for(tmp_path)
    write(ledger)
    write(ledger)
    scan = scan_ledger(tmp_path / ".devrelay", identity())
    assert scan.outcome == "multiple_matches"
    assert scan.record is None
    assert scan.candidate_count == 2


def test_an_allocated_call_id_without_a_record_is_a_gap(tmp_path: Path) -> None:
    ledger = ledger_for(tmp_path)
    missing = ledger.allocate_call_id()  # identity burned, no record written
    write(ledger)
    scan = scan_ledger(tmp_path / ".devrelay", identity())
    assert scan.outcome == "evidence_gap"
    assert missing in scan.gap_reason
    assert "no accounting record" in scan.gap_reason


def test_a_missing_sequence_file_leaves_the_ceiling_unproven(tmp_path: Path) -> None:
    ledger = ledger_for(tmp_path)
    write(ledger)
    ledger.sequence_path.unlink()
    scan = scan_ledger(tmp_path / ".devrelay", identity())
    assert scan.outcome == "evidence_gap"
    assert scan.ceiling == ""
    assert scan.interval_proven is False


def test_a_corrupt_sequence_file_is_a_gap(tmp_path: Path) -> None:
    ledger = ledger_for(tmp_path)
    write(ledger)
    ledger.sequence_path.write_text("{not json", encoding="utf-8")
    scan = scan_ledger(tmp_path / ".devrelay", identity())
    assert scan.outcome == "evidence_gap"
    assert "sequence" in scan.gap_reason


def test_a_record_newer_than_the_sequence_is_a_crash_window_gap(tmp_path: Path) -> None:
    ledger = ledger_for(tmp_path)
    write(ledger)
    write(ledger, call_id="OC-0009")  # never allocated by the sequence
    scan = scan_ledger(tmp_path / ".devrelay", identity())
    assert scan.outcome == "evidence_gap"
    assert "OC-0009" in scan.gap_reason


def test_a_torn_record_is_a_gap(tmp_path: Path) -> None:
    ledger = ledger_for(tmp_path)
    call_id = write(ledger)
    (ledger.calls_dir / f"{call_id}.json").write_text("{\"call_id\": ", encoding="utf-8")
    scan = scan_ledger(tmp_path / ".devrelay", identity())
    assert scan.outcome == "evidence_gap"
    assert call_id in scan.gap_reason


def test_route_disagreement_is_reported_not_hidden(tmp_path: Path) -> None:
    ledger = ledger_for(tmp_path)
    write(ledger, model="other-model")
    scan = scan_ledger(tmp_path / ".devrelay", identity())
    assert scan.outcome == "evidence_gap"
    assert scan.route_disagreement is True
    assert "route" in scan.gap_reason


def test_only_send_prompt_calls_count_as_candidates(tmp_path: Path) -> None:
    ledger = ledger_for(tmp_path)
    write(ledger, operation="get_messages", state=None)
    scan = scan_ledger(tmp_path / ".devrelay", identity())
    assert scan.outcome == "evidence_gap"
    assert scan.candidate_count == 0


def test_every_stored_record_round_trips_as_json(tmp_path: Path) -> None:
    ledger = ledger_for(tmp_path)
    call_id = write(ledger)
    payload = json.loads((ledger.calls_dir / f"{call_id}.json").read_text(encoding="utf-8"))
    assert payload["operation"] == "send_prompt"
    assert payload["prompt_sha256"] == DIGEST
    assert payload["submission_uncertain"] is False


def test_newest_call_id_ignores_empty_and_unparseable_identities() -> None:
    assert newest_call_id() == ""
    assert newest_call_id("", "OC-0002", "OC-0011") == "OC-0011"
    assert newest_call_id("nonsense", "OC-0003") == "OC-0003"
