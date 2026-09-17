"""The v0.3-D transition policy: which next state is legal, and why.

Pure policy - no I/O, no model, no provider knowledge.  The rules are:

* a model-bearing phase is legal only from its own ``READY_*`` state;
* a completed implementer turn opens ``READY_REVIEWER``;
* a completed reviewer turn opens ``AWAITING_DECISION`` (and closes a cycle);
* a role turn that is uncertain, pending or failed fails the run **closed**
  (``BLOCKED``) - never a retry, never the other role;
* only an explicit external decision leaves ``AWAITING_DECISION``:
  ``complete`` -> ``COMPLETED``, ``stop`` -> ``STOPPED`` and
  ``request_changes`` -> ``READY_IMPLEMENTER`` **only** while cycle budget
  remains, otherwise ``LIMIT_REACHED``;
* terminal runs accept nothing.
"""

from __future__ import annotations

from dataclasses import dataclass

from devrelay.errors import OrchestrationInvalidTransitionError
from devrelay.orchestration.models import (
    OrchestrationRun,
    RunState,
    TransitionRecord,
    Decision,
    OrchestrationAction,
)


@dataclass(frozen=True)
class TurnOutcome:
    """The truthful result of one accepted role turn."""

    ok: bool
    blocked_reason: str = ""
    detail: str = ""


@dataclass(frozen=True)
class Transition:
    """The next state plus the bookkeeping that must change with it."""

    state: RunState
    current_cycle: int
    completed_cycles: int
    blocked_reason: str = ""

    def apply(self, run: OrchestrationRun, transition: TransitionRecord) -> OrchestrationRun:
        run.state = self.state
        run.current_cycle = self.current_cycle
        run.completed_cycles = self.completed_cycles
        run.blocked_reason = self.blocked_reason
        run.last_transition = transition
        return run


def require_not_terminal(run: OrchestrationRun) -> None:
    if run.terminal:
        raise OrchestrationInvalidTransitionError(
            f"run {run.run_id} is terminal ({run.state.value}); no model-bearing "
            "orchestration action may run again (a terminal run is never reopened)"
        )


def require_no_in_flight_turn(run: OrchestrationRun) -> None:
    if run.in_flight_turn is not None:
        raise OrchestrationInvalidTransitionError(
            f"run {run.run_id} has an unfinished model turn "
            f"(role={run.in_flight_turn.role}); it is failed closed and never replayed "
            "(recovery is out of scope for v0.3-D)"
        )


def require_state(run: OrchestrationRun, expected: RunState, action: str) -> None:
    if run.state is not expected:
        raise OrchestrationInvalidTransitionError(
            f"{action} is not legal from {run.state.value} "
            f"(run {run.run_id} expects {expected.value})"
        )


def require_cycle_budget(run: OrchestrationRun) -> None:
    from devrelay.errors import OrchestrationCycleLimitError

    if run.model_turns_used >= run.model_turn_budget:
        raise OrchestrationCycleLimitError(
            f"run {run.run_id} has spent its model-turn budget "
            f"({run.model_turns_used}/{run.model_turn_budget} = 2 x max_cycles); "
            "no further model turn is allowed in this run"
        )


def start_transition() -> Transition:
    return Transition(
        state=RunState.READY_IMPLEMENTER,
        current_cycle=1,
        completed_cycles=0,
    )


def after_role_turn(run: OrchestrationRun, role: str, outcome: TurnOutcome) -> Transition:
    """The next state after one implementer/reviewer turn."""
    if role not in ("implementer", "reviewer"):
        raise OrchestrationInvalidTransitionError(f"unknown orchestration role {role!r}")
    if not outcome.ok:
        # Fail closed: never retry, never advance to the other role.
        return Transition(
            state=RunState.BLOCKED,
            current_cycle=run.current_cycle,
            completed_cycles=run.completed_cycles,
            blocked_reason=outcome.blocked_reason or "role_turn_failed",
        )
    if role == "implementer":
        return Transition(
            state=RunState.READY_REVIEWER,
            current_cycle=run.current_cycle,
            completed_cycles=run.completed_cycles,
        )
    # A completed reviewer turn closes the cycle and stops for the Planner.
    return Transition(
        state=RunState.AWAITING_DECISION,
        current_cycle=run.current_cycle,
        completed_cycles=run.completed_cycles + 1,
    )


def after_decision(run: OrchestrationRun, decision: Decision) -> Transition:
    """The next state after an explicit external decision."""
    if decision is Decision.COMPLETE:
        return Transition(
            state=RunState.COMPLETED,
            current_cycle=run.current_cycle,
            completed_cycles=run.completed_cycles,
        )
    if decision is Decision.STOP:
        return Transition(
            state=RunState.STOPPED,
            current_cycle=run.current_cycle,
            completed_cycles=run.completed_cycles,
        )
    if decision is Decision.REQUEST_CHANGES:
        if run.completed_cycles >= run.max_cycles:
            return Transition(
                state=RunState.LIMIT_REACHED,
                current_cycle=run.current_cycle,
                completed_cycles=run.completed_cycles,
                blocked_reason="cycle_limit",
            )
        return Transition(
            state=RunState.READY_IMPLEMENTER,
            current_cycle=run.current_cycle + 1,
            completed_cycles=run.completed_cycles,
        )
    raise OrchestrationInvalidTransitionError(
        f"unknown decision {decision!r}; v0.3-D supports exactly "
        "complete, request_changes and stop"
    )


def transition_record(
    *,
    action: OrchestrationAction,
    source: str,
    run: OrchestrationRun,
    next_state: RunState,
    role: str = "",
    note: str = "",
) -> TransitionRecord:
    return TransitionRecord(
        action=action.value,
        source=source,
        previous_state=run.state.value,
        next_state=next_state.value,
        cycle=run.current_cycle,
        role=role,
        note=note,
    )


__all__ = [
    "Transition",
    "TurnOutcome",
    "after_decision",
    "after_role_turn",
    "require_cycle_budget",
    "require_no_in_flight_turn",
    "require_not_terminal",
    "require_state",
    "start_transition",
    "transition_record",
]
