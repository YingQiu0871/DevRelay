"""The DevRelay pipeline state machine.

States are real enum members, never free-form strings.  The transition table
below is the single source of truth; the engine goes through
:func:`transition` for every state change so illegal transitions are rejected
before anything is persisted.
"""

from __future__ import annotations

from enum import Enum
from typing import FrozenSet

from devrelay.errors import InvalidTransitionError


class PipelineState(str, Enum):
    NEW = "NEW"
    PLAN_REQUIRED = "PLAN_REQUIRED"
    PLAN_READY = "PLAN_READY"
    IMPLEMENTING = "IMPLEMENTING"
    TESTING = "TESTING"
    REVIEWING = "REVIEWING"
    FIX_REQUIRED = "FIX_REQUIRED"
    FIXING = "FIXING"
    FINAL_GATE_REQUIRED = "FINAL_GATE_REQUIRED"
    BLOCKED = "BLOCKED"
    DONE = "DONE"
    FAILED = "FAILED"


_TERMINAL: FrozenSet[PipelineState] = frozenset(
    {PipelineState.BLOCKED, PipelineState.DONE, PipelineState.FAILED}
)

_TRANSITIONS: dict[PipelineState, FrozenSet[PipelineState]] = {
    PipelineState.NEW: frozenset({PipelineState.PLAN_REQUIRED, PipelineState.BLOCKED}),
    PipelineState.PLAN_REQUIRED: frozenset(
        {PipelineState.PLAN_READY, PipelineState.BLOCKED}
    ),
    PipelineState.PLAN_READY: frozenset(
        {PipelineState.IMPLEMENTING, PipelineState.BLOCKED, PipelineState.FAILED}
    ),
    PipelineState.IMPLEMENTING: frozenset(
        {PipelineState.TESTING, PipelineState.BLOCKED, PipelineState.FAILED}
    ),
    PipelineState.TESTING: frozenset(
        {
            PipelineState.REVIEWING,
            PipelineState.FIX_REQUIRED,
            PipelineState.BLOCKED,
            PipelineState.FAILED,
        }
    ),
    PipelineState.REVIEWING: frozenset(
        {
            PipelineState.FIX_REQUIRED,
            PipelineState.FINAL_GATE_REQUIRED,
            PipelineState.BLOCKED,
            PipelineState.FAILED,
        }
    ),
    PipelineState.FIX_REQUIRED: frozenset(
        {PipelineState.FIXING, PipelineState.BLOCKED, PipelineState.FAILED}
    ),
    PipelineState.FIXING: frozenset(
        {PipelineState.TESTING, PipelineState.BLOCKED, PipelineState.FAILED}
    ),
    PipelineState.FINAL_GATE_REQUIRED: frozenset(
        {PipelineState.DONE, PipelineState.BLOCKED, PipelineState.FAILED}
    ),
    # BLOCKED can only be left through the explicit, reason-mandatory
    # `devrelay unblock` mechanism.
    PipelineState.BLOCKED: frozenset(
        {
            PipelineState.PLAN_READY,
            PipelineState.IMPLEMENTING,
            PipelineState.REVIEWING,
            PipelineState.FIX_REQUIRED,
        }
    ),
    PipelineState.FAILED: frozenset(
        {PipelineState.PLAN_READY, PipelineState.IMPLEMENTING, PipelineState.BLOCKED}
    ),
    PipelineState.DONE: frozenset(),
}

# States in which the engine may make automatic progress during `continue`.
WORKING_STATES: FrozenSet[PipelineState] = frozenset(
    {
        PipelineState.PLAN_READY,
        PipelineState.IMPLEMENTING,
        PipelineState.TESTING,
        PipelineState.REVIEWING,
        PipelineState.FIX_REQUIRED,
        PipelineState.FIXING,
    }
)


def is_terminal(state: PipelineState) -> bool:
    return state in _TERMINAL


def allowed_transitions(state: PipelineState) -> FrozenSet[PipelineState]:
    return _TRANSITIONS[state]


def can_transition(from_state: PipelineState, to_state: PipelineState) -> bool:
    return to_state in _TRANSITIONS[from_state]


def transition(
    from_state: PipelineState, to_state: PipelineState
) -> PipelineState:
    """Validate and return *to_state*.

    Raises :class:`InvalidTransitionError` when the transition is not allowed.
    """
    if not can_transition(from_state, to_state):
        raise InvalidTransitionError(from_state.value, to_state.value)
    return to_state
