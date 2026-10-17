"""Strict read-only reader of the v0.3-A OpenCode call ledger (v0.3-E).

Recovery must never claim more than durable evidence supports (V03E_SPEC §9):

* the scan is *identity scoped*: only ``send_prompt`` records of the interrupted
  session whose captured prompt identity (digest, length, route) matches the
  frozen attempt are considered;
* the scan runs inside a *proven interval*: the floor comes from the newest
  finalized turn's durable call ids, the ceiling from the durable call sequence.
  When either cannot be proven the outcome is ``evidence_gap`` - a bounded or
  newest-N window never proves absence;
* an unreadable, torn, missing or schema-invalid record inside the allocated
  range is a gap, never a skipped record;
* the reader never writes, never allocates a call id and opens no socket.

The outcomes are exactly: ``exactly_one_match``, ``multiple_matches``,
``no_record_in_proven_interval`` and ``evidence_gap``.  "No record in a proven
interval" is not the same claim as "was never submitted": the ledger only
accounts *issued* requests, so the absence of a record is evidence about the
local accounting surface, nothing more.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from devrelay.opencode.accounting import FilesystemOpenCodeLedger
from devrelay.opencode.models import OpenCodeCallRecord

_CALL_ID_RE = re.compile(r"^OC-(\d+)$")

SUBMISSION_OPERATION = "send_prompt"

OUTCOME_EXACTLY_ONE = "exactly_one_match"
OUTCOME_MULTIPLE = "multiple_matches"
OUTCOME_ABSENT = "no_record_in_proven_interval"
OUTCOME_GAP = "evidence_gap"


@dataclass(frozen=True)
class LedgerIdentity:
    """The durable identity of one model-bearing submission."""

    session_id: str
    prompt_sha256: str
    prompt_chars: int
    resolved_model: str = ""
    resolved_agent: str = ""


@dataclass(frozen=True)
class LedgerScan:
    """The honest outcome of one identity-scoped ledger scan."""

    outcome: str
    record: OpenCodeCallRecord | None = None
    floor: str = ""
    ceiling: str = ""
    interval_proven: bool = False
    candidate_count: int = 0
    gap_reason: str = ""
    route_disagreement: bool = False
    evidence: dict[str, str] = field(default_factory=dict)

    @property
    def proven_absent(self) -> bool:
        return self.outcome == OUTCOME_ABSENT and self.interval_proven


def _call_number(call_id: str) -> int | None:
    match = _CALL_ID_RE.match(call_id or "")
    return int(match.group(1)) if match else None


def _sequence_ceiling(devrelay_dir: Path) -> tuple[int | None, str]:
    """The durable ceiling: every allocated id is below ``next_call_sequence``."""
    ledger = FilesystemOpenCodeLedger(devrelay_dir)
    sequence_path = ledger.sequence_path
    if not sequence_path.is_file():
        return None, "the durable call sequence is absent (ceiling unproven)"
    try:
        payload = json.loads(sequence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"the durable call sequence is unreadable ({type(exc).__name__})"
    value = payload.get("next_call_sequence") if isinstance(payload, dict) else None
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        return None, "the durable call sequence is malformed (ceiling unproven)"
    return value - 1, ""


def _read_call(path: Path) -> tuple[OpenCodeCallRecord | None, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return OpenCodeCallRecord.model_validate(payload), ""
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return None, f"call record {path.name} is unreadable ({type(exc).__name__})"


def scan_ledger(
    devrelay_dir: Path,
    identity: LedgerIdentity,
    *,
    floor: str = "",
) -> LedgerScan:
    """Scan the durable ledger for *identity* inside ``floor..ceiling``.

    ``floor`` is exclusive and must be a proven call id from durable evidence
    (the newest finalized turn's last call).  An empty floor is unproven: a match
    is still usable evidence, an absence is then a gap.
    """
    ledger = FilesystemOpenCodeLedger(Path(devrelay_dir))
    calls_dir = ledger.calls_dir
    allocated, ceiling_gap = _sequence_ceiling(Path(devrelay_dir))
    if allocated is None:
        return LedgerScan(outcome=OUTCOME_GAP, floor=floor, gap_reason=ceiling_gap)
    ceiling = f"OC-{allocated:04d}"
    floor_number = _call_number(floor) if floor else None
    floor_proven = bool(floor) and floor_number is not None
    if floor and floor_number is None:
        return LedgerScan(
            outcome=OUTCOME_GAP,
            floor=floor,
            ceiling=ceiling,
            gap_reason=f"floor {floor!r} is not a call id",
        )

    records: list[OpenCodeCallRecord] = []
    if calls_dir.is_dir():
        present: dict[int, Path] = {}
        for path in calls_dir.glob("OC-*.json"):
            number = _call_number(path.stem)
            if number is not None:
                present[number] = path
        # Every allocated identity must have an accounting record: a missing one
        # is a torn/refused request in a crash window, never "not submitted".
        for number in range(1, allocated + 1):
            if number not in present:
                return LedgerScan(
                    outcome=OUTCOME_GAP,
                    floor=floor,
                    ceiling=ceiling,
                    gap_reason=(
                        f"allocated call OC-{number:04d} has no accounting record "
                        "(crash window or torn ledger; absence unproven)"
                    ),
                )
        for number in sorted(present):
            if number > allocated:
                return LedgerScan(
                    outcome=OUTCOME_GAP,
                    floor=floor,
                    ceiling=ceiling,
                    gap_reason=(
                        f"call record OC-{number:04d} is newer than the durable "
                        "sequence (ceiling unproven)"
                    ),
                )
            if floor_number is not None and number <= floor_number:
                continue
            record, reason = _read_call(present[number])
            if record is None:
                return LedgerScan(
                    outcome=OUTCOME_GAP,
                    floor=floor,
                    ceiling=ceiling,
                    gap_reason=reason,
                )
            records.append(record)

    candidates = [
        record
        for record in records
        if record.operation == SUBMISSION_OPERATION
        and record.session_id == identity.session_id
        and record.prompt_sha256
        and record.prompt_sha256 == identity.prompt_sha256
        and record.prompt_chars == identity.prompt_chars
    ]
    exact = [
        record
        for record in candidates
        if record.model == identity.resolved_model
        and record.agent == identity.resolved_agent
    ]
    route_disagreement = bool(candidates) and not exact
    interval_proven = floor_proven
    if len(exact) > 1:
        return LedgerScan(
            outcome=OUTCOME_MULTIPLE,
            floor=floor,
            ceiling=ceiling,
            interval_proven=interval_proven,
            candidate_count=len(exact),
            gap_reason=(
                f"{len(exact)} ledger records match the captured prompt identity "
                "(the interruption cannot be attributed to one submission)"
            ),
        )
    if route_disagreement:
        return LedgerScan(
            outcome=OUTCOME_GAP,
            floor=floor,
            ceiling=ceiling,
            interval_proven=interval_proven,
            candidate_count=len(candidates),
            route_disagreement=True,
            gap_reason=(
                "a ledger record matches the prompt identity but disagrees on the "
                "captured route; it cannot be attributed to this attempt"
            ),
        )
    if len(exact) == 1:
        return LedgerScan(
            outcome=OUTCOME_EXACTLY_ONE,
            record=exact[0],
            floor=floor,
            ceiling=ceiling,
            interval_proven=interval_proven,
            candidate_count=1,
        )
    if not floor_proven:
        return LedgerScan(
            outcome=OUTCOME_GAP,
            floor=floor,
            ceiling=ceiling,
            gap_reason=(
                "no durable floor (the newest finalized turn records no call ids); "
                "absence of a matching record cannot be proven"
            ),
        )
    return LedgerScan(
        outcome=OUTCOME_ABSENT,
        floor=floor,
        ceiling=ceiling,
        interval_proven=True,
        candidate_count=0,
    )


def newest_call_id(*call_ids: list[str]) -> str:
    """The highest durable call id of the given durable evidence, or ``""``."""
    numbers = [number for number in map(_call_number, call_ids) if number is not None]
    return f"OC-{max(numbers):04d}" if numbers else ""


__all__ = [
    "LedgerIdentity",
    "LedgerScan",
    "OUTCOME_ABSENT",
    "OUTCOME_EXACTLY_ONE",
    "OUTCOME_GAP",
    "OUTCOME_MULTIPLE",
    "SUBMISSION_OPERATION",
    "newest_call_id",
    "scan_ledger",
]
