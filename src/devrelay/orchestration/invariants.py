"""Semantic invariants and reachability proof for a persisted v0.3-D run.

The store parses the JSON, but parsing is not trust: a run document can be
tampered with on disk, copied between workspaces, truncated, hand-edited or rolled
back to an earlier (cheaper) state.  This module re-derives every invariant the
production state machine *guarantees* and refuses anything else as
``orchestration_state_corrupt``.

The contract is stronger than "every field looks plausible": the **current state
must be provably reachable** from the persisted turn history, decision history,
counters, transition provenance, cycle structure and in-flight intent.  A
document whose history cannot have produced its state, counters or provenance is
not a run DevRelay will act on.

Design rules used here:

* every rule below is satisfied by **every** honestly generated run - verified
  against a corpus produced by the real service (including the legitimate crash
  boundary: a ``READY_*`` state carrying an ``in_flight`` intent);
* a rule is only added when the state machine, the corpus or the service proves
  it, never invented;
* corruption is never repaired: no normalisation, no re-resolution, no silent
  migration, no reset.

Honest bound of this guarantee (v0.3-D): a run document is self-contained mutable
JSON with no external integrity anchor, so DevRelay can guarantee that **every
structural and semantic reachability invariant holds** and that malformed,
inconsistent or partially rolled-back documents fail closed before any model
call.  It does **not** claim cryptographic or append-only tamper evidence: an
attacker who rewrites the whole document into a different but internally
consistent history is out of scope for v0.3-D (that would need a signed journal or
an append-only store, which v0.3-D deliberately does not add).
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, NoReturn

from devrelay.errors import OrchestrationStateCorruptError, RoleRoutingError
from devrelay.orchestration.models import (
    HARD_MAX_CYCLES,
    MIN_MAX_CYCLES,
    RECOVERY_ACTION,
    RECOVERY_REASONS,
    SUPPORTED_RUN_ROLES,
    SUPPORTED_SCHEMA_VERSIONS,
    TERMINAL_STATES,
    Decision,
    RecoveryResolution,
    RunState,
    TurnOutcomeState,
)

#: States that can only be reached *after* a cycle was closed by a completed
#: reviewer turn.
_CYCLE_CLOSED_STATES = frozenset(
    {
        RunState.AWAITING_DECISION,
        RunState.COMPLETED,
        RunState.STOPPED,
        RunState.LIMIT_REACHED,
    }
)

#: States in which a model-bearing phase of the *current* cycle has not yet
#: completed (so ``current_cycle == completed_cycles + 1``).
_CYCLE_OPEN_STATES = frozenset(
    {
        RunState.READY_IMPLEMENTER,
        RunState.READY_REVIEWER,
        RunState.BLOCKED,
        RunState.RECOVERY_REQUIRED,
    }
)

_EXPECTED_IN_FLIGHT_STATE = {
    "implementer": RunState.READY_IMPLEMENTER,
    "reviewer": RunState.READY_REVIEWER,
}

#: A persisted prompt digest is always a lowercase sha256 hex digest.
_PROMPT_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

#: The state machine edges a *last* transition may describe, per current state:
#: ``(action, previous_state, role)``.  ``None`` for the role means "any role the
#: action legitimately carries".  Cycle relations are checked next to the table.
_LAST_EDGE_RULES: dict[RunState, frozenset[tuple[str, str, str | None]]] = {
    RunState.READY_IMPLEMENTER: frozenset({("decide", "AWAITING_DECISION", "")}),
    RunState.READY_REVIEWER: frozenset(
        {
            ("run_implementer", "READY_IMPLEMENTER", "implementer"),
            # v0.3-E (adoption only): a resolved interrupted implementer turn.
            (RECOVERY_ACTION, RunState.RECOVERY_REQUIRED.value, "implementer"),
        }
    ),
    RunState.AWAITING_DECISION: frozenset(
        {
            ("run_reviewer", "READY_REVIEWER", "reviewer"),
            (RECOVERY_ACTION, RunState.RECOVERY_REQUIRED.value, "reviewer"),
        }
    ),
    RunState.COMPLETED: frozenset({("decide", "AWAITING_DECISION", "")}),
    RunState.STOPPED: frozenset({("decide", "AWAITING_DECISION", "")}),
    RunState.LIMIT_REACHED: frozenset({("decide", "AWAITING_DECISION", "")}),
    RunState.BLOCKED: frozenset(
        {
            # fail-closed via the phase itself (failed role turn / interruption)
            ("run_implementer", "READY_IMPLEMENTER", "implementer"),
            ("run_reviewer", "READY_REVIEWER", "reviewer"),
            # fail-closed administratively (route invalidation, ownership loss)
            ("block", "READY_IMPLEMENTER", None),
            ("block", "READY_REVIEWER", None),
            # v0.3-E fail-closed recovery exit: the materialized interrupted
            # attempt is (possibly in the same atomic write) marked
            # unrecoverable, and that single resolution is the last edge.
            (RECOVERY_ACTION, "READY_IMPLEMENTER", "implementer"),
            (RECOVERY_ACTION, "READY_REVIEWER", "reviewer"),
            (RECOVERY_ACTION, RunState.RECOVERY_REQUIRED.value, None),
        }
    ),
    RunState.RECOVERY_REQUIRED: frozenset(
        {
            # the entry edge only: an interrupted live intent of the current cycle
            (RECOVERY_ACTION, "READY_IMPLEMENTER", "implementer"),
            (RECOVERY_ACTION, "READY_REVIEWER", "reviewer"),
        }
    ),
}

#: Decisions that end a run: they may only ever be the last recorded decision.
_TERMINAL_DECISION_STATES = frozenset(
    {RunState.COMPLETED.value, RunState.STOPPED.value, RunState.LIMIT_REACHED.value}
)


def validate_run_semantics(run: Any) -> None:
    """Raise ``OrchestrationStateCorruptError`` unless *run* is an honest run."""

    def bad(reason: str) -> NoReturn:
        raise OrchestrationStateCorruptError(
            f"orchestration run {getattr(run, 'run_id', '?')!r} is semantically "
            f"corrupt: {reason}; refusing to treat it as authoritative"
        )

    # -- §3 fixed schema version --------------------------------------
    if run.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        bad(
            f"schema_version {run.schema_version!r} is not one of the supported "
            f"versions {list(SUPPORTED_SCHEMA_VERSIONS)} (no migration is attempted)"
        )
    # A frozen v0.3-D document keeps the exact v0.3-D contract: it has no
    # recovery record, no recovery reason and never enters RECOVERY_REQUIRED.
    if run.schema_version == 1:
        if run.recovery is not None:
            bad("a v1 (frozen v0.3-D) document must not carry a recovery record")
        if run.recovery_reason:
            bad(
                f"a v1 (frozen v0.3-D) document must not carry recovery_reason "
                f"{run.recovery_reason!r}"
            )
        if run.state is RunState.RECOVERY_REQUIRED:
            bad("a v1 (frozen v0.3-D) document can never be in RECOVERY_REQUIRED")

    # -- §4/§5 hard cycle bound and budget ----------------------------
    if not isinstance(run.max_cycles, int) or isinstance(run.max_cycles, bool):
        bad("max_cycles must be an integer")
    if not (MIN_MAX_CYCLES <= run.max_cycles <= HARD_MAX_CYCLES):
        bad(
            f"max_cycles {run.max_cycles} is outside the hard bound "
            f"{MIN_MAX_CYCLES}..{HARD_MAX_CYCLES}"
        )
    if run.model_turn_budget != 2 * run.max_cycles:
        bad(
            f"model_turn_budget {run.model_turn_budget} does not equal "
            f"2 x max_cycles ({2 * run.max_cycles})"
        )

    # -- §6 counters ---------------------------------------------------
    if not (1 <= run.current_cycle <= run.max_cycles):
        bad(f"current_cycle {run.current_cycle} is outside 1..{run.max_cycles}")
    if not (0 <= run.completed_cycles <= run.max_cycles):
        bad(f"completed_cycles {run.completed_cycles} is outside 0..{run.max_cycles}")
    if run.turn_attempts < 0:
        bad(f"turn_attempts {run.turn_attempts} is negative")
    if run.model_turns_used < 0:
        bad(f"model_turns_used {run.model_turns_used} is negative")
    if run.model_turns_used > run.model_turn_budget:
        bad(
            f"model_turns_used {run.model_turns_used} exceeds the model-turn "
            f"budget {run.model_turn_budget}"
        )
    # Every committed in-flight intent increments both counters together and
    # nothing ever decrements them, so they are equal in every honest state.
    if run.turn_attempts != run.model_turns_used:
        bad(
            f"turn_attempts {run.turn_attempts} disagrees with model_turns_used "
            f"{run.model_turns_used} (both are incremented once per reserved turn)"
        )
    # Each reserved turn is either recorded in its role history (finished),
    # still held by the in-flight intent (crash boundary), or - in v0.3-E
    # RECOVERY_REQUIRED - held by the single recovery record.
    in_recovery = (
        run.schema_version >= 2
        and run.state is RunState.RECOVERY_REQUIRED
        and run.recovery is not None
    )
    recorded = len(run.implementer_turns) + len(run.reviewer_turns)
    expected_recorded = (
        run.model_turns_used
        - (1 if run.in_flight_turn is not None else 0)
        - (1 if in_recovery else 0)
    )
    if recorded != expected_recorded:
        bad(
            f"{recorded} turn record(s) do not account for "
            f"{run.model_turns_used} reserved turn(s)"
            + (" with an in-flight intent" if run.in_flight_turn is not None else "")
            + (" with a materialized recovery attempt" if in_recovery else "")
        )
    # The budget is spend-only: the turns a run claims to have spent can never
    # exceed what its cycle structure could ever have allowed.
    if run.model_turns_used > 2 * run.current_cycle:
        bad(
            f"model_turns_used {run.model_turns_used} cannot have been spent by "
            f"cycle {run.current_cycle} (at most {2 * run.current_cycle} slots exist)"
        )

    # -- §7 session separation ----------------------------------------
    impl_session = run.implementer_session_id
    rev_session = run.reviewer_session_id
    for label, value in (
        ("implementer_session_id", impl_session),
        ("reviewer_session_id", rev_session),
    ):
        if not isinstance(value, str) or not value.strip():
            bad(f"{label} is missing or blank")
    if impl_session == rev_session:
        bad(
            "implementer_session_id and reviewer_session_id are identical: one "
            "session for both roles destroys reviewer independence"
        )

    # -- §8 workspace binding is checked by the store (needs the bound root) --

    # -- §9 route snapshot structure -----------------------------------
    snapshot = run.route_snapshot
    if set(snapshot) != set(SUPPORTED_RUN_ROLES):
        bad(
            f"route_snapshot keys {sorted(snapshot)} are not exactly "
            f"{sorted(SUPPORTED_RUN_ROLES)}"
        )
    for role in SUPPORTED_RUN_ROLES:
        entry = snapshot[role]
        if entry.role != role:
            bad(f"route_snapshot[{role!r}] declares role {entry.role!r}")
        if not isinstance(entry.model, str) or not entry.model.strip():
            bad(f"route_snapshot[{role!r}] has a blank model")
        if entry.route_source != "workspace_config":
            bad(
                f"route_snapshot[{role!r}] has unsupported route_source "
                f"{entry.route_source!r}"
            )
        _require_mappable_model(entry.model, role, bad)

    # -- §10 role histories: per-cycle evidence, real audit fields -----
    blocked_turns: list[str] = []
    for role, turns in (
        ("implementer", run.implementer_turns),
        ("reviewer", run.reviewer_turns),
    ):
        seen: dict[int, int] = {}
        for turn in turns:
            if turn.role != role:
                bad(f"{role} history contains a {turn.role!r} turn record")
            if not (1 <= turn.cycle <= run.max_cycles):
                bad(f"{role} turn cycle {turn.cycle} is outside 1..{run.max_cycles}")
            if turn.cycle > run.current_cycle:
                bad(
                    f"{role} turn cycle {turn.cycle} is from the future (the run is "
                    f"in cycle {run.current_cycle})"
                )
            seen[turn.cycle] = seen.get(turn.cycle, 0) + 1
            if seen[turn.cycle] > 1:
                bad(f"{role} has more than one turn in cycle {turn.cycle}")
            if turn.outcome not in {item.value for item in TurnOutcomeState}:
                bad(f"{role} turn outcome {turn.outcome!r} is not a known outcome")
            if turn.outcome == TurnOutcomeState.IN_FLIGHT.value:
                bad(f"{role} history contains an unfinished in-flight turn")
            _require_prompt_evidence(turn, f"{role} turn (cycle {turn.cycle})", bad)
            _require_route_agreement(
                turn, role, snapshot, bad, label=f"{role} turn (cycle {turn.cycle})"
            )
            _require_finished_audit(turn, f"{role} turn (cycle {turn.cycle})", bad)
            if turn.outcome == TurnOutcomeState.BLOCKED.value:
                blocked_turns.append(f"{role} cycle {turn.cycle}")
    state = run.state
    if blocked_turns and state is not RunState.BLOCKED:
        # A failed phase always fails the run closed and nothing reopens it, so a
        # blocked turn can never live inside an active or completed run.
        bad(
            f"blocked turn(s) ({', '.join(blocked_turns)}) exist but the run state "
            f"is {state.value} (a failed phase fails the run closed and never resumes)"
        )

    def completed_turns(role: str, cycle: int) -> list[Any]:
        turns = run.implementer_turns if role == "implementer" else run.reviewer_turns
        return [
            turn
            for turn in turns
            if turn.cycle == cycle and turn.outcome == TurnOutcomeState.COMPLETED.value
        ]

    for cycle in range(1, run.current_cycle + 1):
        impl_count = sum(1 for turn in run.implementer_turns if turn.cycle == cycle)
        rev_count = sum(1 for turn in run.reviewer_turns if turn.cycle == cycle)
        if rev_count > impl_count:
            bad(f"cycle {cycle} has a reviewer turn before any implementer turn")
        if len(completed_turns("reviewer", cycle)) and len(completed_turns("implementer", cycle)) != 1:
            # Reviewer completion is only reachable after that cycle's implementer
            # phase completed: the service cannot advance otherwise.
            bad(
                f"cycle {cycle} contains a completed reviewer turn without exactly "
                "one completed implementer turn in the same cycle"
            )

    completed_reviewer_turns = [
        turn
        for turn in run.reviewer_turns
        if turn.outcome == TurnOutcomeState.COMPLETED.value
    ]
    if run.completed_cycles != len(completed_reviewer_turns):
        bad(
            f"completed_cycles {run.completed_cycles} does not match the "
            f"{len(completed_reviewer_turns)} completed reviewer turn(s)"
        )
    for cycle in range(1, run.completed_cycles + 1):
        if not any(
            turn.cycle == cycle and turn.outcome == TurnOutcomeState.COMPLETED.value
            for turn in run.reviewer_turns
        ):
            bad(f"cycle {cycle} counts as completed but has no completed reviewer turn")

    # -- §10/§11 state <-> cycle <-> evidence --------------------------
    if state in _CYCLE_CLOSED_STATES:
        if run.current_cycle != run.completed_cycles:
            bad(
                f"state {state.value} requires current_cycle == completed_cycles "
                f"({run.current_cycle} != {run.completed_cycles})"
            )
        if run.completed_cycles < 1:
            bad(f"state {state.value} requires at least one completed cycle")
        last_reviewer = run.reviewer_turns[-1] if run.reviewer_turns else None
        if (
            last_reviewer is None
            or last_reviewer.cycle != run.current_cycle
            or last_reviewer.outcome != TurnOutcomeState.COMPLETED.value
        ):
            bad(
                f"state {state.value} requires a completed reviewer turn for "
                f"cycle {run.current_cycle}"
            )
    elif state in _CYCLE_OPEN_STATES:
        if run.current_cycle != run.completed_cycles + 1:
            bad(
                f"state {state.value} requires current_cycle == "
                f"completed_cycles + 1 ({run.current_cycle} != "
                f"{run.completed_cycles + 1})"
            )
    if state is RunState.LIMIT_REACHED and run.completed_cycles != run.max_cycles:
        bad(
            f"state LIMIT_REACHED requires completed_cycles == max_cycles "
            f"({run.completed_cycles} != {run.max_cycles})"
        )

    # A reviewer phase is only reachable after this cycle's implementer phase
    # completed - with or without a live in-flight reviewer intent, and with or
    # without a materialized interrupted reviewer attempt.
    reviewer_phase_is_current = (
        state is RunState.READY_REVIEWER
        or (run.in_flight_turn is not None and run.in_flight_turn.role == "reviewer")
        or (
            state is RunState.RECOVERY_REQUIRED
            and run.recovery is not None
            and run.recovery.attempt.role == "reviewer"
        )
    )
    if reviewer_phase_is_current and len(completed_turns("implementer", run.current_cycle)) != 1:
        bad(
            f"cycle {run.current_cycle} claims the reviewer phase without exactly one "
            "completed implementer turn in that cycle"
        )

    # -- blocked reason truthfulness -----------------------------------
    if state is RunState.BLOCKED:
        if not run.blocked_reason:
            bad("state BLOCKED requires a blocked_reason")
    elif state is RunState.LIMIT_REACHED:
        if run.blocked_reason != "cycle_limit":
            bad(f"state LIMIT_REACHED requires blocked_reason 'cycle_limit'")
    elif run.blocked_reason:
        bad(f"state {state.value} must not carry blocked_reason {run.blocked_reason!r}")

    # -- §11 in-flight intent shape ------------------------------------
    in_flight = run.in_flight_turn
    if in_flight is not None:
        if state in TERMINAL_STATES:
            bad(f"terminal state {state.value} carries a live in-flight intent")
        if state not in (RunState.READY_IMPLEMENTER, RunState.READY_REVIEWER):
            bad(f"state {state.value} cannot carry a live in-flight intent")
        if in_flight.role not in SUPPORTED_RUN_ROLES:
            bad(f"in-flight intent has unknown role {in_flight.role!r}")
        if _EXPECTED_IN_FLIGHT_STATE[in_flight.role] is not state:
            bad(
                f"in-flight {in_flight.role} intent requires state "
                f"{_EXPECTED_IN_FLIGHT_STATE[in_flight.role].value}, not {state.value}"
            )
        if in_flight.cycle != run.current_cycle:
            bad(
                f"in-flight intent cycle {in_flight.cycle} is not the current "
                f"cycle {run.current_cycle}"
            )
        if in_flight.outcome != TurnOutcomeState.IN_FLIGHT.value:
            bad(f"in-flight intent outcome must be 'in_flight', not {in_flight.outcome!r}")
        _require_prompt_evidence(in_flight, "in-flight intent", bad)
        _require_route_agreement(
            in_flight, in_flight.role, snapshot, bad, label="in-flight intent"
        )
        if in_flight.completed_at:
            bad("a live in-flight intent must not claim a completion timestamp")
        if in_flight.blocked_reason:
            bad("a live in-flight intent must not carry a blocked_reason")

    # -- decision history: a legal graph, not a free-form list ---------
    # Every recorded decision starts from AWAITING_DECISION and lands on an edge
    # the state machine actually has; each completed cycle (except the one still
    # awaiting its decision) has exactly one external decision; every cycle after
    # the first was opened by exactly one request_changes decision.
    allowed_decisions = {item.value for item in Decision}
    opened_cycles = 0
    for index, record in enumerate(run.decision_history):
        if record.decision not in allowed_decisions:
            bad(f"decision history contains unknown decision {record.decision!r}")
        if record.source != "external_planner":
            bad(
                f"decision history decision {record.decision!r} has source "
                f"{record.source!r} (only external decisions may advance a run)"
            )
        if not record.decided_at or not _is_iso(record.decided_at):
            bad(f"decision {record.decision!r} has no valid decided_at timestamp")
        if record.previous_state != RunState.AWAITING_DECISION.value:
            bad(
                f"decision {record.decision!r} was recorded from "
                f"{record.previous_state!r}; only AWAITING_DECISION may be left by a "
                "decision"
            )
        allowed_next = {
            Decision.COMPLETE.value: {RunState.COMPLETED.value},
            Decision.STOP.value: {RunState.STOPPED.value},
            Decision.REQUEST_CHANGES.value: {
                RunState.READY_IMPLEMENTER.value,
                RunState.LIMIT_REACHED.value,
            },
        }[record.decision]
        if record.next_state not in allowed_next:
            bad(
                f"decision {record.decision!r} cannot lead to {record.next_state!r} "
                f"(allowed: {sorted(allowed_next)})"
            )
        if record.next_state == RunState.READY_IMPLEMENTER.value:
            opened_cycles += 1
        if record.next_state in _TERMINAL_DECISION_STATES and index != len(
            run.decision_history
        ) - 1:
            bad(
                f"decision {record.decision!r} ended the run at {record.next_state!r} "
                "but later decisions are recorded"
            )

    expected_decisions = run.completed_cycles - (
        1 if state is RunState.AWAITING_DECISION else 0
    )
    if len(run.decision_history) != expected_decisions:
        bad(
            f"{len(run.decision_history)} decision(s) are recorded but "
            f"completed_cycles {run.completed_cycles} in state {state.value} requires "
            f"exactly {expected_decisions} external decision(s)"
        )
    if opened_cycles != run.current_cycle - 1:
        bad(
            f"cycle {run.current_cycle} requires exactly {run.current_cycle - 1} "
            f"request_changes decision(s) that opened a new cycle, found {opened_cycles}"
        )

    if run.decision_history:
        last = run.decision_history[-1]
        expected_decision = {
            RunState.COMPLETED: Decision.COMPLETE.value,
            RunState.STOPPED: Decision.STOP.value,
        }.get(state, Decision.REQUEST_CHANGES.value)
        if last.decision != expected_decision:
            bad(
                f"state {state.value} requires the last decision to be "
                f"{expected_decision!r}, not {last.decision!r}"
            )
        expected_next_state = (
            state.value
            if state in (RunState.COMPLETED, RunState.STOPPED, RunState.LIMIT_REACHED)
            else RunState.READY_IMPLEMENTER.value
        )
        if last.next_state != expected_next_state:
            bad(
                f"the last decision recorded next_state {last.next_state!r}, which "
                f"is not {expected_next_state!r} for state {state.value}"
            )

    # -- v0.3-E recovery shape (v2 only) -------------------------------
    _require_recovery_shape(run, state, snapshot, bad)

    # -- transition provenance: the last edge must end at this state --
    # ``last_transition is None`` is legal for an in-memory run under
    # construction; requiring provenance for *persisted* documents is enforced by
    # the store on load and on save (OrchestrationStore._require_provenance).
    _require_last_transition(run, state, bad)


def _is_iso(value: str) -> bool:
    try:
        datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return True


def _require_prompt_evidence(turn: Any, label: str, bad: Any) -> None:
    """Only a digest and a length of the prompt are persisted, always both."""
    if not isinstance(turn.prompt_sha256, str) or not _PROMPT_DIGEST_RE.match(
        turn.prompt_sha256
    ):
        bad(f"{label} has no valid prompt digest (expected a lowercase sha256)")
    if not isinstance(turn.prompt_chars, int) or turn.prompt_chars < 1:
        bad(f"{label} has an invalid prompt length {turn.prompt_chars!r}")
    if not turn.started_at or not _is_iso(turn.started_at):
        bad(f"{label} has no valid started_at timestamp")


def _require_route_agreement(
    turn: Any, role: str, snapshot: Any, bad: Any, *, label: str = ""
) -> None:
    """A turn (or live intent) must have been taken on the captured route."""
    entry = snapshot[role]
    where = label or f"{role} turn"
    if turn.resolved_model != entry.model:
        bad(
            f"{where} was recorded against model {turn.resolved_model!r} but the "
            f"snapshot says {entry.model!r}"
        )
    if turn.resolved_agent != entry.agent:
        bad(
            f"{where} was recorded against agent {turn.resolved_agent!r} but the "
            f"snapshot says {entry.agent!r}"
        )
    if turn.route_source != entry.route_source:
        bad(
            f"{where} was recorded with route_source {turn.route_source!r} but "
            f"the snapshot says {entry.route_source!r}"
        )


def _require_finished_audit(turn: Any, label: str, bad: Any) -> None:
    """A finished turn always records how it ended."""
    if not turn.completed_at or not _is_iso(turn.completed_at):
        bad(f"{label} has no valid completed_at timestamp")
    if turn.outcome == TurnOutcomeState.COMPLETED.value and turn.blocked_reason:
        bad(f"{label} completed but carries blocked_reason {turn.blocked_reason!r}")
    if turn.outcome == TurnOutcomeState.BLOCKED.value and not turn.blocked_reason:
        bad(f"{label} is blocked but carries no blocked_reason")


def _require_recovery_shape(run: Any, state: RunState, snapshot: Any, bad: Any) -> None:
    """The v0.3-E recovery shape: exactly one record, one resolution, no refunds.

    ``RECOVERY_REQUIRED`` holds the *unresolved* record (accounted instead of a
    history turn); every other state may only carry a *resolved* one, and
    ``mark_unrecoverable`` must have converted the same attempt into exactly one
    blocked history turn whose reason is the recovery reason.
    """
    recovery = run.recovery
    if run.schema_version < 2:
        return

    if state is RunState.RECOVERY_REQUIRED:
        if recovery is None:
            bad("state RECOVERY_REQUIRED requires exactly one materialized recovery record")
        if run.in_flight_turn is not None:
            bad(
                "state RECOVERY_REQUIRED must not carry a live in-flight intent "
                "(the interrupted attempt is materialized into the recovery record)"
            )
        if not run.recovery_reason:
            bad("state RECOVERY_REQUIRED requires a recovery_reason")
        if run.blocked_reason:
            bad(
                f"state RECOVERY_REQUIRED must not carry blocked_reason "
                f"{run.blocked_reason!r} (the run is not blocked before resolution)"
            )
        if recovery.resolution:
            bad(
                f"state RECOVERY_REQUIRED requires an unresolved recovery record, "
                f"found resolution {recovery.resolution!r}"
            )
        if run.recovery_reason != recovery.recovery_reason:
            bad(
                f"recovery_reason {run.recovery_reason!r} disagrees with the recovery "
                f"record's {recovery.recovery_reason!r}"
            )
        _require_recovery_record(run, recovery, snapshot, bad)
        attempt = recovery.attempt
        if attempt.cycle != run.current_cycle:
            bad(
                f"the recovery attempt cycle {attempt.cycle} is not the current "
                f"cycle {run.current_cycle}"
            )
        if any(turn.model_dump() == attempt.model_dump() for turn in run.turns):
            bad(
                "the materialized recovery attempt must not also appear in a role "
                "history before it is resolved (no double count, no refund)"
            )
        return

    if recovery is None:
        if run.recovery_reason:
            bad(
                f"state {state.value} must not carry recovery_reason "
                f"{run.recovery_reason!r}"
            )
        return

    # A resolved recovery record: only recovery states may carry one, and only
    # with a resolution recorded.
    if not recovery.resolution:
        bad(
            f"state {state.value} carries an unresolved recovery record "
            "(only RECOVERY_REQUIRED may)"
        )
    if not recovery.resolved_at or not _is_iso(recovery.resolved_at):
        bad("a resolved recovery record requires a valid resolved_at timestamp")
    if run.recovery_reason != recovery.recovery_reason:
        bad(
            f"recovery_reason {run.recovery_reason!r} disagrees with the recovery "
            f"record's {recovery.recovery_reason!r}"
        )
    _require_recovery_record(run, recovery, snapshot, bad)
    attempt = recovery.attempt
    history = (
        run.implementer_turns if attempt.role == "implementer" else run.reviewer_turns
    )
    if not any(turn.model_dump() == attempt.model_dump() for turn in history):
        bad(
            "the resolved recovery attempt is not recorded in its role history "
            "(a resolution converts the same attempt exactly once)"
        )
    if recovery.resolution == RecoveryResolution.MARK_UNRECOVERABLE.value:
        if state is not RunState.BLOCKED:
            bad(
                f"resolution mark_unrecoverable requires state BLOCKED, not "
                f"{state.value}"
            )
        if run.blocked_reason != recovery.recovery_reason:
            bad(
                f"a failed-closed recovery requires blocked_reason == recovery_reason "
                f"({recovery.recovery_reason!r}), found {run.blocked_reason!r}"
            )
        return
    if recovery.resolution == RecoveryResolution.ADOPT_COMPLETED_TURN.value:
        # Adoption is disabled in this build; a document carrying it can only
        # come from a build where the platform proofs enabled it.  It is still
        # validated structurally so such state is never misread.
        if attempt.outcome != TurnOutcomeState.COMPLETED.value:
            bad("an adopted recovery attempt must be recorded as completed")
        if state is RunState.READY_REVIEWER:
            if attempt.role != "implementer" or attempt.cycle != run.current_cycle:
                bad(
                    "an adopted implementer attempt must be this cycle's implementer "
                    "turn in READY_REVIEWER"
                )
        elif state is RunState.AWAITING_DECISION:
            if attempt.role != "reviewer" or attempt.cycle != run.completed_cycles:
                bad(
                    "an adopted reviewer attempt must be the completed reviewer turn "
                    f"of cycle {run.completed_cycles}"
                )
        else:
            bad(f"an adopted turn cannot land in state {state.value}")
        return
    bad(f"unknown recovery resolution {recovery.resolution!r}")


def _require_recovery_record(run: Any, recovery: Any, snapshot: Any, bad: Any) -> None:
    """The frozen attempt and its evidence digest must describe this run."""
    attempt = recovery.attempt
    evidence = recovery.evidence
    if evidence.run_id != run.run_id:
        bad(f"recovery evidence belongs to run {evidence.run_id!r}, not {run.run_id!r}")
    if evidence.schema_version != run.schema_version:
        bad("recovery evidence schema_version disagrees with the document")
    if evidence.state not in (
        RunState.READY_IMPLEMENTER.value,
        RunState.READY_REVIEWER.value,
    ):
        bad(
            f"recovery evidence state {evidence.state!r} is not an interruptible "
            "live-intent state"
        )
    last = run.last_transition
    if last is not None and last.previous_state != RunState.RECOVERY_REQUIRED.value:
        if evidence.state != last.previous_state:
            bad(
                f"recovery evidence state {evidence.state!r} disagrees with the "
                f"recorded entry state {last.previous_state!r}"
            )
    if evidence.current_cycle != run.current_cycle:
        bad("recovery evidence current_cycle disagrees with the document")
    if evidence.completed_cycles != run.completed_cycles:
        bad("recovery evidence completed_cycles disagrees with the document")
    if evidence.model_turns_used != run.model_turns_used:
        bad("recovery evidence model_turns_used disagrees with the document")
    if evidence.turn_attempts != run.turn_attempts:
        bad("recovery evidence turn_attempts disagrees with the document")
    if evidence.attempt_role != attempt.role or evidence.attempt_cycle != attempt.cycle:
        bad("recovery evidence attempt identity disagrees with the frozen attempt")
    if evidence.attempt_prompt_sha256 != attempt.prompt_sha256:
        bad("recovery evidence prompt digest disagrees with the frozen attempt")
    if evidence.attempt_prompt_chars != attempt.prompt_chars:
        bad("recovery evidence prompt length disagrees with the frozen attempt")
    if (
        evidence.attempt_resolved_model != attempt.resolved_model
        or evidence.attempt_resolved_agent != attempt.resolved_agent
        or evidence.attempt_route_source != attempt.route_source
        or evidence.attempt_started_at != attempt.started_at
    ):
        bad("recovery evidence route/start evidence disagrees with the frozen attempt")
    recorded_calls = [item for item in evidence.attempt_call_ids.split(",") if item]
    if recorded_calls != list(attempt.call_ids):
        bad("recovery evidence call ids disagree with the frozen attempt")
    if recovery.recovery_reason not in RECOVERY_REASONS:
        bad(f"recovery reason {recovery.recovery_reason!r} is not a known reason")
    if evidence.coverage not in ("proven_interval", "evidence_gap"):
        bad(
            f"recovery evidence coverage {evidence.coverage!r} is not a legal "
            "coverage class"
        )
    if attempt.outcome == TurnOutcomeState.BLOCKED.value:
        if attempt.blocked_reason != recovery.recovery_reason:
            bad(
                f"the frozen recovery attempt is blocked for "
                f"{attempt.blocked_reason!r}, not the recorded recovery reason "
                f"{recovery.recovery_reason!r}"
            )
    elif attempt.outcome == TurnOutcomeState.COMPLETED.value and attempt.blocked_reason:
        bad("a completed frozen recovery attempt must not carry a blocked_reason")
    _require_prompt_evidence(attempt, "recovery attempt", bad)
    _require_route_agreement(attempt, attempt.role, snapshot, bad, label="recovery attempt")


def _require_last_transition(run: Any, state: RunState, bad: Any) -> None:
    """The recorded transition must be a real edge that ends at *state*."""
    record = run.last_transition
    if record is None:
        return
    if record.next_state != state.value:
        bad(
            f"the last transition ends at {record.next_state!r} but the run state is "
            f"{state.value!r}"
        )
    if record.action == "start":
        if (
            record.previous_state
            or record.next_state != RunState.READY_IMPLEMENTER.value
            or record.cycle != 1
            or run.current_cycle != 1
        ):
            bad(
                "the start transition must describe a fresh cycle-1 "
                "READY_IMPLEMENTER run (no previous state)"
            )
        return
    if run.schema_version < 2 and record.action == RECOVERY_ACTION:
        bad(
            f"action {RECOVERY_ACTION!r} does not exist for schema_version "
            f"{run.schema_version} (the recovery edges are a v2 addition)"
        )
    if not record.previous_state:
        bad("a non-start transition must record its previous state")
    allowed = _LAST_EDGE_RULES.get(state, frozenset())
    matching = [
        edge
        for edge in allowed
        if edge[0] == record.action
        and edge[1] == record.previous_state
        and (edge[2] is None or edge[2] == record.role)
    ]
    if not matching:
        bad(
            f"the last transition ({record.action} from {record.previous_state!r} to "
            f"{record.next_state!r}, role {record.role!r}) is not a legal edge into "
            f"{state.value}"
        )
    if state is RunState.READY_IMPLEMENTER:
        expected_cycle = run.current_cycle - 1
    else:
        expected_cycle = run.current_cycle
    if record.cycle != expected_cycle:
        bad(
            f"the last transition was recorded in cycle {record.cycle} but state "
            f"{state.value} in cycle {run.current_cycle} requires cycle {expected_cycle}"
        )
    if not record.at or not _is_iso(record.at):
        bad("the last transition has no valid timestamp")


def _require_mappable_model(model: str, role: str, bad: Any) -> None:
    from devrelay.roles.models import model_identity

    try:
        model_identity(model, role=role)
    except RoleRoutingError as exc:
        bad(f"route_snapshot[{role!r}] model {model!r} cannot be mapped ({exc.code})")


__all__ = ["validate_run_semantics"]
