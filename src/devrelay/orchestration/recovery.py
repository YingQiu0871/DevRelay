"""v0.3-E fail-closed recovery: reconcile evidence and resolve exactly once.

The mandatory core is deliberately narrow (``docs/v0.3/V03E_SPEC.md``):

* recovery **never** submits a model turn, retries a request, resumes a run or
  adopts a remote reply in this build;
* the only resolution recorded here is ``mark_unrecoverable``: the interrupted
  reservation becomes exactly one ``blocked`` turn in its role history and the
  run ends ``BLOCKED`` with ``blocked_reason == recovery_reason``;
* ``adopt_completed_turn`` exists as a protocol value but stays **disabled**
  (:data:`ADOPTION_CAPABILITY_ENABLED`) until the platform proofs P1/P2/P3/P6/P8
  pass - the resolved ``G0.5``/P6 gate is unresolved, so the safe default is the
  only default;
* the evidence digest is frozen at resolution time, is metadata only (never a
  prompt, reply, reasoning trace or credential), and a persisted record that
  disagrees with its own digest is corrupt rather than "re-resolvable".

Everything here is a pure function over the durable run document plus optional
strict ledger / session-history reads; the service owns the atomic write.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from devrelay.models import utcnow_iso
from devrelay.opencode.models import (
    MAX_TEXT_CHARS,
    OpenCodeCallRecord,
    prompt_digest,
)
from devrelay.orchestration import ledger_reader
from devrelay.orchestration.ledger_reader import LedgerIdentity, LedgerScan
from devrelay.orchestration.models import (
    RECOVERY_REASONS,
    OrchestrationRun,
    RecoveryEvidence,
    RecoveryResolution,
    RunState,
    TurnOutcomeState,
    TurnRecord,
)

#: Adoption stays disabled: the G0.5/P6 gate is NOT SATISFIED, and P1/P2/P3/P8
#: have no independent proof either.  Enabling it requires those proofs first.
ADOPTION_CAPABILITY_ENABLED = False

ADOPTION_DISABLED_REASON = (
    "adopt_completed_turn is disabled: the platform proofs (G0.5/P6 plus "
    "P1/P2/P3/P8) have not passed, so this build cannot prove that a completed "
    "remote turn originated from the interrupted local submission"
)

#: Remote turn correlation outcomes (report-only; never a submission claim).
REMOTE_EXACTLY_ONE = "exactly_one_match"
REMOTE_NO_MATCH_IN_WINDOW = "no_match_in_window"
REMOTE_GAP = "evidence_gap"

#: The mandatory fail-closed core is **local-only**: it never reads session
#: history, because every OpenCode HTTP call on this bridge is ledger-accounted
#: and a "read-only" reconciliation must leave the eligible surface byte-identical.
#: Remote correlation belongs to the gated adoption capability (still disabled) and
#: requires its own authorization before it is wired in.
REMOTE_NOT_READ_REASON = (
    "the local recovery surface reads no session history (it performs no provider "
    "call and leaves the durable surface untouched); remote correlation belongs to "
    "the gated adoption capability, which is disabled"
)


@dataclass(frozen=True)
class RemoteMatch:
    """The result of looking for the captured prompt in the session history."""

    outcome: str
    message_id: str = ""
    role: str = ""
    created_at: str = ""
    matched_digest: str = ""
    gap_reason: str = ""


def infer_recovery_reason(
    attempt: TurnRecord, ledger_scan: LedgerScan | None = None
) -> str:
    """The most conservative true reason for the materialized attempt.

    The reason is derived from the durable local ledger, never from the shape
    of the crash alone (SPEC §16 W1-W7):

    * ``submission_uncertain`` - the submission may have reached the provider:
      the attempt itself is flagged uncertain, the settled record carries
      ``submission_uncertain``, the durable record is still ``ISSUED`` (W3: the
      request may have been delivered and the response header was never seen;
      W4: the response arrived but the settle never became durable - both
      leave the same ``ISSUED`` evidence behind), or the response was
      malformed (the provider did answer, so this is not a clean
      interruption).
    * ``reply_pending`` - the provider accepted the call (a settled
      ``COMPLETED`` record with a 2xx status) but the local result was never
      correlated: W5 (the assistant identity was not captured) and W6 (the
      result is known but the completed turn was not persisted).
    * ``turn_interrupted`` - nothing durable proves that the provider ever saw
      the request: W1 (the intent was persisted before the request left the
      machine and the proven interval holds no record) and W2 (the connection
      was established but the call never settled).  A settled record with a
      non-2xx status lands here too: the provider answered with an error, so
      no submission is claimed and no reply is pending.

    Without a scan - or with a scan that proves nothing - the reason stays
    ``turn_interrupted``: the absence of evidence is never evidence of a
    submission.
    """
    if attempt.submission_uncertain:
        return "submission_uncertain"
    if attempt.reply_pending:
        return "reply_pending"
    record: OpenCodeCallRecord | None = None
    if (
        ledger_scan is not None
        and ledger_scan.outcome == ledger_reader.OUTCOME_EXACTLY_ONE
    ):
        record = ledger_scan.record
    if record is None:
        return "turn_interrupted"
    if record.submission_uncertain:
        return "submission_uncertain"
    state = record.state.value if hasattr(record.state, "value") else str(record.state)
    if state == "ISSUED":
        return "submission_uncertain"
    if state == "COMPLETED":
        status = record.http_status
        if status is not None and 200 <= int(status) < 300:
            return "reply_pending"
        return "turn_interrupted"
    if state == "MALFORMED_RESPONSE":
        return "submission_uncertain"
    return "turn_interrupted"


def frozen_attempt(attempt: TurnRecord, reason: str) -> TurnRecord:
    """Freeze an interrupted intent as a finished, failed turn record."""
    if reason not in RECOVERY_REASONS:
        raise ValueError(f"unknown recovery reason {reason!r}")
    return attempt.model_copy(
        update={
            "outcome": TurnOutcomeState.BLOCKED.value,
            "blocked_reason": reason,
            "completed_at": utcnow_iso(),
        }
    )


def previous_floor(run: OrchestrationRun) -> str:
    """The newest durable call id of the finalized turns *before* the attempt.

    An empty value means no durable floor is proven; absence of a ledger record
    then becomes ``evidence_gap`` instead of a false "not submitted".
    """
    call_ids = [
        call_id for turn in run.turns for call_id in (turn.call_ids or [])
    ]
    return ledger_reader.newest_call_id(*call_ids)


def attempt_identity(run: OrchestrationRun, attempt: TurnRecord) -> LedgerIdentity:
    session_id = (
        run.implementer_session_id
        if attempt.role == "implementer"
        else run.reviewer_session_id
    )
    return LedgerIdentity(
        session_id=session_id,
        prompt_sha256=attempt.prompt_sha256,
        prompt_chars=attempt.prompt_chars,
        resolved_model=attempt.resolved_model,
        resolved_agent=attempt.resolved_agent,
    )


def match_remote_turn(result: object, attempt: TurnRecord) -> RemoteMatch:
    """Look for the captured prompt digest in one bounded session-history read.

    Absence in a bounded window is **not** proof of absence: only an exact match
    is evidence, and an unreadable/truncated/ambiguous window is a gap.
    """
    if result is None:
        return RemoteMatch(REMOTE_GAP, gap_reason="the session history was not read")
    if not getattr(result, "ok", False):
        reason = getattr(result, "error_type", "") or getattr(result, "state", "")
        text = getattr(reason, "value", reason) or "unknown"
        return RemoteMatch(
            REMOTE_GAP,
            gap_reason=f"the session history could not be read ({text})",
        )
    page = getattr(result, "page", None)
    messages = list(getattr(result, "messages", []) or ())
    if not messages and page is not None:
        messages = list(page.messages or ())
    if page is not None and (page.window_truncated or page.cursor_unknown):
        return RemoteMatch(
            REMOTE_GAP,
            gap_reason=(
                "the session history read was window-truncated or its cursor is "
                "unknown; uniqueness and absence cannot be proven"
            ),
        )
    if not attempt.prompt_sha256:
        return RemoteMatch(
            REMOTE_GAP, gap_reason="the interrupted attempt captured no prompt digest"
        )
    if attempt.prompt_chars > MAX_TEXT_CHARS:
        return RemoteMatch(
            REMOTE_GAP,
            gap_reason=(
                "the captured prompt is longer than the bounded per-message text "
                "cap; the remote digest cannot be compared"
            ),
        )
    matches = [
        message
        for message in messages
        if (text := getattr(message, "text", ""))
        and hashlib.sha256(text.encode("utf-8")).hexdigest() == attempt.prompt_sha256
    ]
    if len(matches) > 1:
        return RemoteMatch(
            REMOTE_GAP,
            matched_digest=attempt.prompt_sha256,
            gap_reason=(
                f"{len(matches)} remote messages match the captured prompt digest; "
                "the turn cannot be attributed to one message"
            ),
        )
    if len(matches) == 1:
        message = matches[0]
        return RemoteMatch(
            REMOTE_EXACTLY_ONE,
            message_id=str(getattr(message, "message_id", "") or ""),
            role=str(getattr(message, "role", "") or ""),
            created_at=str(getattr(message, "created_at", "") or ""),
            matched_digest=prompt_digest(message.text),
        )
    return RemoteMatch(REMOTE_NO_MATCH_IN_WINDOW)


def coverage(scan: LedgerScan | None) -> str:
    if scan is not None and scan.interval_proven and scan.outcome in (
        ledger_reader.OUTCOME_EXACTLY_ONE,
        ledger_reader.OUTCOME_ABSENT,
    ):
        return "proven_interval"
    return "evidence_gap"


def build_evidence(
    run: OrchestrationRun,
    attempt: TurnRecord,
    *,
    entry_state: RunState,
    ledger_scan: LedgerScan | None,
    remote: RemoteMatch | None,
) -> RecoveryEvidence:
    """Freeze the canonical, metadata-only evidence set (``V03E_SPEC.md`` §13)."""
    record = ledger_scan.record if ledger_scan is not None else None
    matched = remote if remote is not None else RemoteMatch(REMOTE_GAP)
    fields = {
        "evidence_sha256": "",
        "run_id": run.run_id,
        "schema_version": run.schema_version,
        "state": entry_state.value,
        "current_cycle": run.current_cycle,
        "completed_cycles": run.completed_cycles,
        "model_turns_used": run.model_turns_used,
        "turn_attempts": run.turn_attempts,
        "attempt_role": attempt.role,
        "attempt_cycle": attempt.cycle,
        "attempt_prompt_sha256": attempt.prompt_sha256,
        "attempt_prompt_chars": attempt.prompt_chars,
        "attempt_resolved_model": attempt.resolved_model,
        "attempt_resolved_agent": attempt.resolved_agent,
        "attempt_route_source": attempt.route_source,
        "attempt_started_at": attempt.started_at,
        "attempt_call_ids": ",".join(attempt.call_ids or []),
        "ledger_call_id": record.call_id if record is not None else "",
        "ledger_state": record.state.value if record is not None else "",
        "ledger_http_status": record.http_status if record is not None else None,
        "ledger_submission_uncertain": (
            bool(record.submission_uncertain) if record is not None else False
        ),
        "ledger_response_media_type": (
            record.response_media_type if record is not None else ""
        ),
        "ledger_completed_at": record.completed_at if record is not None else "",
        "remote_message_id": matched.message_id,
        "remote_role": matched.role,
        "remote_created_at": matched.created_at,
        "remote_matched_digest": matched.matched_digest,
        "coverage": coverage(ledger_scan),
    }
    plain = RecoveryEvidence.model_construct(**fields)
    digest = plain.compute_digest()
    return RecoveryEvidence.model_validate(
        {**plain.model_dump(mode="json"), "evidence_sha256": digest}
    )


def build_record(
    run: OrchestrationRun,
    attempt: TurnRecord,
    *,
    entry_state: RunState,
    reason: str,
    ledger_scan: LedgerScan | None,
    remote: RemoteMatch | None,
) -> tuple[RecoveryEvidence, TurnRecord]:
    """The evidence + frozen attempt pair for one recovery entry."""
    evidence = build_evidence(
        run,
        attempt,
        entry_state=entry_state,
        ledger_scan=ledger_scan,
        remote=remote,
    )
    return evidence, frozen_attempt(attempt, reason)


def _adoption_checklist(
    run: OrchestrationRun,
    attempt: TurnRecord | None,
    ledger_part: dict[str, object],
    route_drift: str,
    *,
    v1_frozen: bool,
    resolved: bool,
) -> tuple[list[dict[str, str]], list[str]]:
    """The per-item adoption checklist (``V03E_SPEC.md`` §11/§21) and blockers.

    Statuses are exactly ``pass`` / ``fail`` / ``unknown``: no partial credit and no
    "likely" verdict.  Nothing here enables adoption - ``ADOPTION_CAPABILITY_ENABLED``
    is ``False`` and the resolve action refuses it before any write - but the report
    must state *why*, item by item, instead of leaving the operator to guess.
    """
    checklist: list[dict[str, str]] = []

    def item(name: str, status: str, detail: str) -> None:
        checklist.append({"item": name, "status": status, "detail": detail})

    item(
        "document",
        "unknown" if v1_frozen else "pass",
        (
            "frozen v0.3-D (v1) document: the recovery protocol does not apply"
            if v1_frozen
            else f"v{run.schema_version} document passed the strict reader"
        ),
    )
    item(
        "attempt identity",
        "pass" if attempt is not None and attempt.prompt_sha256 else "unknown",
        (
            "the interrupted attempt captured a prompt digest and length"
            if attempt is not None and attempt.prompt_sha256
            else "no interrupted or materialized attempt to identify"
        ),
    )

    outcome = str(ledger_part["outcome"])
    if outcome == ledger_reader.OUTCOME_EXACTLY_ONE:
        attribution = ("pass", f"exactly one ledger record ({ledger_part['call_id']})")
    elif outcome == ledger_reader.OUTCOME_MULTIPLE:
        attribution = (
            "fail",
            f"{ledger_part['candidate_count']} ledger records match: the submission "
            "cannot be attributed to one",
        )
    elif outcome == ledger_reader.OUTCOME_ABSENT and bool(ledger_part["interval_proven"]):
        # A proven interval bounds the search; per SPEC §9 / E44 it is *not*
        # proof that the request was never submitted, and the adoption
        # checklist cannot pass on absence alone.
        attribution = (
            "unknown",
            "no DevRelay ledger record was found in the proven interval; "
            "adoption attribution cannot be confirmed",
        )
    else:
        reason = str(ledger_part["gap_reason"])
        if outcome == ledger_reader.OUTCOME_ABSENT:
            reason = reason or "no matching ledger record, but the interval is not proven"
        attribution = ("unknown", reason or "no proven interval for the attempt")
    item("ledger attribution", *attribution)

    settled = (
        str(ledger_part["state"]) == "COMPLETED"
        and ledger_part["http_status"] is not None
        and 200 <= int(ledger_part["http_status"]) < 300
        and str(ledger_part["response_media_type"]).startswith("application/json")
        and not bool(ledger_part["submission_uncertain"])
    )
    item(
        "ledger settlement",
        "pass" if settled else ("fail" if outcome == ledger_reader.OUTCOME_EXACTLY_ONE else "unknown"),
        (
            "the one matching record is settled COMPLETED with a 2xx JSON reply"
            if settled
            else "no settled COMPLETED/2xx/JSON record for this attempt"
        ),
    )
    item("remote correlation", "unknown", REMOTE_NOT_READ_REASON)
    item(
        "route stability",
        "fail" if route_drift else "pass",
        route_drift or "both role routes still match the captured snapshot",
    )
    item(
        "resolution state",
        "fail" if resolved else "pass",
        "the recovery record is already resolved"
        if resolved
        else "no resolution has been applied yet",
    )
    item(
        "adoption capability",
        "fail" if not ADOPTION_CAPABILITY_ENABLED else "pass",
        ADOPTION_DISABLED_REASON
        if not ADOPTION_CAPABILITY_ENABLED
        else "the capability is enabled in this build",
    )
    item(
        "platform proofs",
        "unknown",
        "the adoption-enabling platform proofs (G0.5/P6, G1/G2 with P1/P2/P3/P8) "
        "have not passed; G0.4 is an authoritative FAIL / P4 UNPROVEN",
    )

    blockers: list[str] = []
    if not ADOPTION_CAPABILITY_ENABLED:
        blockers.append(f"adoption is disabled: {ADOPTION_DISABLED_REASON}")
    for entry in checklist:
        if entry["status"] != "pass":
            blockers.append(f"{entry['item']}: {entry['detail']}")
    if v1_frozen:
        blockers.append(
            "this is a frozen v1 document: the only recovery action is the next "
            "mutating phase action failing it closed as BLOCKED/turn_interrupted"
        )
    return checklist, blockers


def reconcile_report(
    run: OrchestrationRun,
    *,
    ledger_scan: LedgerScan | None = None,
    remote: RemoteMatch | None = None,
    route_drift: str = "",
    v1_frozen: bool = False,
) -> dict[str, object]:
    """The read-only reconcile report (no mutation, no submission)."""
    intent = run.in_flight_turn
    recovery = run.recovery
    if run.state is RunState.RECOVERY_REQUIRED and recovery is not None:
        attempt = recovery.attempt
        reason = recovery.recovery_reason
        recoverable = True
    elif intent is not None:
        attempt = intent
        reason = infer_recovery_reason(intent, ledger_scan)
        recoverable = not v1_frozen
    else:
        attempt = None
        reason = run.recovery_reason
        recoverable = False
    ledger_part: dict[str, object] = {
        "outcome": ledger_reader.OUTCOME_GAP,
        "call_id": "",
        "state": "",
        "http_status": None,
        "submission_uncertain": False,
        "response_media_type": "",
        "completed_at": "",
        "floor": "",
        "ceiling": "",
        "interval_proven": False,
        "candidate_count": 0,
        "gap_reason": "",
    }
    if ledger_scan is not None:
        record = ledger_scan.record
        ledger_part.update(
            {
                "outcome": ledger_scan.outcome,
                "call_id": record.call_id if record is not None else "",
                "state": record.state.value if record is not None else "",
                "http_status": record.http_status if record is not None else None,
                "submission_uncertain": (
                    bool(record.submission_uncertain) if record is not None else False
                ),
                "response_media_type": (
                    record.response_media_type if record is not None else ""
                ),
                "completed_at": record.completed_at if record is not None else "",
                "floor": ledger_scan.floor,
                "ceiling": ledger_scan.ceiling,
                "interval_proven": ledger_scan.interval_proven,
                "candidate_count": ledger_scan.candidate_count,
                "gap_reason": ledger_scan.gap_reason,
            }
        )
    if v1_frozen:
        ledger_part["gap_reason"] = (
            "v1 (frozen v0.3-D) documents have no recovery protocol; no recovery "
            "evidence is collected or acted upon for them"
        )
    elif ledger_scan is None:
        ledger_part["gap_reason"] = (
            "no turn to attribute: the run has no interrupted or materialized "
            "attempt, so no ledger interval is claimed"
        )
    if remote is None:
        remote_part: dict[str, object] = {
            "outcome": REMOTE_GAP,
            "message_id": "",
            "role": "",
            "created_at": "",
            "gap_reason": REMOTE_NOT_READ_REASON,
        }
    else:
        remote_part = {
            "outcome": remote.outcome,
            "message_id": remote.message_id,
            "role": remote.role,
            "created_at": remote.created_at,
            "gap_reason": remote.gap_reason,
        }
    summary = run.summary()
    resolved = recovery is not None and bool(recovery.resolution)
    checklist, blockers = _adoption_checklist(
        run,
        attempt,
        ledger_part,
        route_drift,
        v1_frozen=v1_frozen,
        resolved=resolved,
    )
    return {
        "run_id": run.run_id,
        "schema_version": run.schema_version,
        "state": run.state.value,
        "terminal": run.terminal,
        "recoverable": recoverable,
        "v1_frozen": v1_frozen,
        "recovery_reason": reason,
        "recovery": recovery.public() if recovery is not None else None,
        "attempt": attempt.public() if attempt is not None else None,
        "ledger": ledger_part,
        "remote": remote_part,
        "adoption": {
            "available": ADOPTION_CAPABILITY_ENABLED,
            "candidate": (
                attempt.public()
                if attempt is not None
                and not v1_frozen
                and (remote is not None and remote.outcome == REMOTE_EXACTLY_ONE)
                else None
            ),
            "reason": ADOPTION_DISABLED_REASON,
        },
        "route": {"drift": route_drift or ""},
        "budget": {
            "model_turns_used": run.model_turns_used,
            "turn_attempts": run.turn_attempts,
            "model_turn_budget": run.model_turn_budget,
            "implementer_turns": len(run.implementer_turns),
            "reviewer_turns": len(run.reviewer_turns),
            "recovery_attempt": 1
            if (run.state is RunState.RECOVERY_REQUIRED and recovery is not None)
            else 0,
            "in_flight": intent is not None,
        },
        "legal_next_actions": summary.get("legal_next_actions", []),
        "submission": {"submitted_by_recovery": False},
        "checklist": checklist,
        "blockers": blockers,
        "note": (
            "v1 document: the frozen v0.3-D contract applies; the next mutating "
            "action fails the run closed as BLOCKED/turn_interrupted and the "
            "recovery tools do not apply"
            if v1_frozen
            else "reconcile is read-only: nothing was written, submitted, retried "
            "or resumed"
        ),
    }


def resolution_names() -> tuple[str, ...]:
    return tuple(item.value for item in RecoveryResolution)


__all__ = [
    "ADOPTION_CAPABILITY_ENABLED",
    "ADOPTION_DISABLED_REASON",
    "REMOTE_EXACTLY_ONE",
    "REMOTE_GAP",
    "REMOTE_NO_MATCH_IN_WINDOW",
    "RemoteMatch",
    "attempt_identity",
    "build_evidence",
    "build_record",
    "coverage",
    "frozen_attempt",
    "infer_recovery_reason",
    "match_remote_turn",
    "previous_floor",
    "reconcile_report",
    "resolution_names",
]
