"""Semantic invariants for a persisted v0.3-D run document.

The store parses the JSON, but parsing is not trust: a run document can be
tampered with on disk, copied between workspaces, truncated or hand-edited.  This
module re-derives every invariant the production state machine *guarantees* and
refuses anything else as ``orchestration_state_corrupt``.

Design rules used here:

* every rule below is satisfied by **every** honestly generated run, including
  the legitimate crash boundary (a ``READY_*`` state carrying an ``in_flight``
  intent) - verified against the honest-state corpus in
  ``tests/test_v03d_invariants.py``;
* a rule is only added when the state machine or the tests prove it, never
  invented;
* corruption is never repaired: no normalisation, no re-resolution, no silent
  migration, no reset.
"""

from __future__ import annotations

from typing import Any, NoReturn

from devrelay.errors import OrchestrationStateCorruptError, RoleRoutingError
from devrelay.orchestration.models import (
    HARD_MAX_CYCLES,
    MIN_MAX_CYCLES,
    ORCHESTRATION_SCHEMA_VERSION,
    TERMINAL_STATES,
    SUPPORTED_RUN_ROLES,
    Decision,
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
    {RunState.READY_IMPLEMENTER, RunState.READY_REVIEWER, RunState.BLOCKED}
)

_EXPECTED_IN_FLIGHT_STATE = {
    "implementer": RunState.READY_IMPLEMENTER,
    "reviewer": RunState.READY_REVIEWER,
}


def validate_run_semantics(run: Any) -> None:
    """Raise ``OrchestrationStateCorruptError`` unless *run* is an honest run."""

    def bad(reason: str) -> NoReturn:
        raise OrchestrationStateCorruptError(
            f"orchestration run {getattr(run, 'run_id', '?')!r} is semantically "
            f"corrupt: {reason}; refusing to treat it as authoritative"
        )

    # -- §3 fixed schema version --------------------------------------
    if run.schema_version != ORCHESTRATION_SCHEMA_VERSION:
        bad(
            f"schema_version {run.schema_version!r} is not the supported "
            f"v{ORCHESTRATION_SCHEMA_VERSION} (no migration is attempted)"
        )

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
    # Each reserved turn is either recorded in its role history (finished) or
    # still held by the in-flight intent (crash boundary).
    recorded = len(run.implementer_turns) + len(run.reviewer_turns)
    expected_recorded = run.model_turns_used - (1 if run.in_flight_turn is not None else 0)
    if recorded != expected_recorded:
        bad(
            f"{recorded} turn record(s) do not account for "
            f"{run.model_turns_used} reserved turn(s)"
            + (" with an in-flight intent" if run.in_flight_turn is not None else "")
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

    # -- §10 role histories: one phase per cycle, implementer first -----
    for role, turns in (("implementer", run.implementer_turns), ("reviewer", run.reviewer_turns)):
        seen: dict[int, int] = {}
        for turn in turns:
            if turn.role != role:
                bad(f"{role} history contains a {turn.role!r} turn record")
            if not (1 <= turn.cycle <= run.max_cycles):
                bad(f"{role} turn cycle {turn.cycle} is outside 1..{run.max_cycles}")
            seen[turn.cycle] = seen.get(turn.cycle, 0) + 1
            if seen[turn.cycle] > 1:
                bad(f"{role} has more than one turn in cycle {turn.cycle}")
            if turn.outcome not in {item.value for item in TurnOutcomeState}:
                bad(f"{role} turn outcome {turn.outcome!r} is not a known outcome")
            if turn.outcome == TurnOutcomeState.IN_FLIGHT.value:
                bad(f"{role} history contains an unfinished in-flight turn")
            if turn.prompt_chars < 0 or len(turn.prompt_sha256) not in (0, 64):
                bad(f"{role} turn has malformed prompt evidence")
            if turn.resolved_model != snapshot[role].model:
                bad(
                    f"{role} turn was recorded against model {turn.resolved_model!r} "
                    f"but the snapshot says {snapshot[role].model!r}"
                )
    for cycle in range(1, run.current_cycle + 1):
        impl_count = sum(1 for turn in run.implementer_turns if turn.cycle == cycle)
        rev_count = sum(1 for turn in run.reviewer_turns if turn.cycle == cycle)
        if rev_count > impl_count:
            bad(f"cycle {cycle} has a reviewer turn before any implementer turn")

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
    state = run.state
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
        if in_flight.resolved_model != snapshot[in_flight.role].model:
            bad("in-flight intent model does not match the route snapshot")
        if in_flight.prompt_chars < 0 or len(in_flight.prompt_sha256) not in (0, 64):
            bad("in-flight intent has malformed prompt evidence")

    # -- decision history ---------------------------------------------
    allowed_decisions = {item.value for item in Decision}
    for record in run.decision_history:
        if record.decision not in allowed_decisions:
            bad(f"decision history contains unknown decision {record.decision!r}")
        if record.source != "external_planner":
            bad(
                f"decision history decision {record.decision!r} has source "
                f"{record.source!r} (only external decisions may advance a run)"
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
    elif state in (RunState.COMPLETED, RunState.STOPPED, RunState.LIMIT_REACHED) or (
        run.current_cycle > 1
    ):
        # A closed terminal state and any cycle beyond the first can only have
        # been reached by an explicit external decision; an empty history there
        # means the document was not produced by the state machine.
        bad(
            f"state {state.value} / cycle {run.current_cycle} was reached without "
            "any decision history"
        )

    # -- start provenance ---------------------------------------------
    # ``last_transition is None`` is legal for an in-memory run under
    # construction; requiring provenance for *persisted* documents is enforced by
    # the store on load and on save (OrchestrationStore._require_provenance).
    if run.last_transition is not None:
        if run.last_transition.action == "start":
            if run.last_transition.previous_state:
                bad("the start transition must not claim a previous state")
        elif not run.last_transition.previous_state:
            bad("a non-start transition must record its previous state")


def _require_mappable_model(model: str, role: str, bad: Any) -> None:
    from devrelay.roles.models import model_identity

    try:
        model_identity(model, role=role)
    except RoleRoutingError as exc:
        bad(f"route_snapshot[{role!r}] model {model!r} cannot be mapped ({exc.code})")


__all__ = ["validate_run_semantics"]
