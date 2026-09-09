"""State machine unit tests: valid paths, invalid transitions, caps."""

import pytest

from devrelay.errors import InvalidTransitionError
from devrelay.pipeline.states import (
    PipelineState,
    allowed_transitions,
    can_transition,
    is_terminal,
    transition,
)

S = PipelineState

HAPPY_PATH = [
    S.NEW,
    S.PLAN_REQUIRED,
    S.PLAN_READY,
    S.IMPLEMENTING,
    S.TESTING,
    S.REVIEWING,
    S.FINAL_GATE_REQUIRED,
    S.DONE,
]

FIX_PATH = [
    S.NEW,
    S.PLAN_REQUIRED,
    S.PLAN_READY,
    S.IMPLEMENTING,
    S.TESTING,
    S.REVIEWING,
    S.FIX_REQUIRED,
    S.FIXING,
    S.TESTING,
    S.REVIEWING,
    S.FINAL_GATE_REQUIRED,
    S.DONE,
]


@pytest.mark.parametrize("path", [HAPPY_PATH, FIX_PATH])
def test_valid_state_paths(path):
    for current, following in zip(path, path[1:]):
        assert transition(current, following) == following


def test_every_state_has_documented_transitions():
    for state in S:
        assert allowed_transitions(state) is not None


def test_illegal_transition_is_rejected():
    for from_state, to_state in [
        (S.NEW, S.PLAN_READY),          # skips PLAN_REQUIRED
        (S.REVIEWING, S.IMPLEMENTING),  # backwards
        (S.DONE, S.PLAN_REQUIRED),      # terminal
        (S.DONE, S.NEW),
        (S.BLOCKED, S.DONE),            # blocked only via unblock targets
        (S.PLAN_REQUIRED, S.REVIEWING),
    ]:
        with pytest.raises(InvalidTransitionError):
            transition(from_state, to_state)
        assert not can_transition(from_state, to_state)


def test_unblock_targets_from_blocked_are_explicit():
    expected = {S.PLAN_READY, S.IMPLEMENTING, S.REVIEWING, S.FIX_REQUIRED}
    assert allowed_transitions(S.BLOCKED) == frozenset(expected)


def test_terminal_states_are_terminal():
    for state in (S.BLOCKED, S.DONE, S.FAILED):
        assert is_terminal(state)
        assert not allowed_transitions(S.DONE) if state is S.DONE else True


def test_working_states_not_terminal():
    for state in (S.PLAN_READY, S.IMPLEMENTING, S.REVIEWING, S.FIXING):
        assert not is_terminal(state)
