"""v0.3-D transition policy (pure state machine, offline)."""

from __future__ import annotations

import pytest

from devrelay.errors import OrchestrationCycleLimitError, OrchestrationInvalidTransitionError
from devrelay.orchestration import state_machine as policy
from devrelay.orchestration.models import (
    TERMINAL_STATES,
    Decision,
    OrchestrationAction,
    RunState,
    TransitionRecord,
    TurnRecord,
)
from v03d_helpers import make_run


def apply_transition(run, transition):
    record = policy.transition_record(
        action=OrchestrationAction.DECIDE,
        source="external_planner",
        run=run,
        next_state=transition.state,
    )
    return transition.apply(run, record)


# ---------------------------------------------------------------------------
# role turns
# ---------------------------------------------------------------------------
def test_a_completed_implementer_turn_opens_the_reviewer_phase():
    run = make_run(state=RunState.READY_IMPLEMENTER)
    transition = policy.after_role_turn(run, "implementer", policy.TurnOutcome(ok=True))
    assert transition.state is RunState.READY_REVIEWER
    assert transition.completed_cycles == 0
    assert transition.current_cycle == run.current_cycle


def test_a_completed_reviewer_turn_stops_at_awaiting_decision_and_closes_the_cycle():
    run = make_run(state=RunState.READY_REVIEWER)
    transition = policy.after_role_turn(run, "reviewer", policy.TurnOutcome(ok=True))
    assert transition.state is RunState.AWAITING_DECISION
    assert transition.completed_cycles == 1
    assert transition.blocked_reason == ""


@pytest.mark.parametrize("role", ["implementer", "reviewer"])
def test_any_unsuccessful_turn_blocks_the_run(role):
    run = make_run(
        state=RunState.READY_IMPLEMENTER if role == "implementer" else RunState.READY_REVIEWER
    )
    transition = policy.after_role_turn(
        run, role, policy.TurnOutcome(ok=False, blocked_reason="read_timeout")
    )
    assert transition.state is RunState.BLOCKED
    assert transition.blocked_reason == "read_timeout"


def test_an_unsuccessful_turn_without_a_reason_still_blocks():
    run = make_run(state=RunState.READY_IMPLEMENTER)
    transition = policy.after_role_turn(run, "implementer", policy.TurnOutcome(ok=False))
    assert transition.state is RunState.BLOCKED
    assert transition.blocked_reason == "role_turn_failed"


def test_unknown_role_is_rejected_by_policy():
    run = make_run(state=RunState.READY_IMPLEMENTER)
    with pytest.raises(OrchestrationInvalidTransitionError):
        policy.after_role_turn(run, "planner", policy.TurnOutcome(ok=True))


# ---------------------------------------------------------------------------
# external decisions
# ---------------------------------------------------------------------------
def test_complete_and_stop_are_terminal():
    run = make_run(state=RunState.AWAITING_DECISION)
    assert policy.after_decision(run, Decision.COMPLETE).state is RunState.COMPLETED
    assert policy.after_decision(run, Decision.STOP).state is RunState.STOPPED


def test_request_changes_opens_the_next_cycle_while_budget_remains():
    run = make_run(state=RunState.AWAITING_DECISION, completed_cycles=1, max_cycles=2)
    transition = policy.after_decision(run, Decision.REQUEST_CHANGES)
    assert transition.state is RunState.READY_IMPLEMENTER
    assert transition.current_cycle == 2
    assert transition.completed_cycles == 1


def test_request_changes_at_the_cycle_cap_reaches_the_limit():
    run = make_run(state=RunState.AWAITING_DECISION, completed_cycles=2, max_cycles=2)
    transition = policy.after_decision(run, Decision.REQUEST_CHANGES)
    assert transition.state is RunState.LIMIT_REACHED
    assert transition.blocked_reason == "cycle_limit"


@pytest.mark.parametrize("decision", ["approve", "reject", "merge", "retry", "", None, 7])
def test_unknown_decisions_are_rejected_by_policy(decision):
    run = make_run(state=RunState.AWAITING_DECISION)
    with pytest.raises(OrchestrationInvalidTransitionError):
        policy.after_decision(run, decision)  # type: ignore[arg-type]


def test_applying_a_transition_records_previous_and_next_state():
    run = make_run(state=RunState.AWAITING_DECISION, completed_cycles=1, max_cycles=2)
    transition = policy.after_decision(run, Decision.REQUEST_CHANGES)
    applied = apply_transition(run, transition)
    assert applied.state is RunState.READY_IMPLEMENTER
    assert applied.current_cycle == 2
    assert applied.last_transition is not None
    assert applied.last_transition.previous_state == "AWAITING_DECISION"
    assert applied.last_transition.next_state == "READY_IMPLEMENTER"
    assert applied.previous_state == "AWAITING_DECISION"


# ---------------------------------------------------------------------------
# guards
# ---------------------------------------------------------------------------
def test_terminal_runs_refuse_further_actions():
    for terminal in sorted(TERMINAL_STATES, key=lambda state: state.value):
        with pytest.raises(OrchestrationInvalidTransitionError):
            policy.require_not_terminal(make_run(state=terminal))


def test_state_guard_names_the_expected_state():
    run = make_run(state=RunState.READY_IMPLEMENTER)
    policy.require_state(run, RunState.READY_IMPLEMENTER, "run_implementer")
    with pytest.raises(OrchestrationInvalidTransitionError) as excinfo:
        policy.require_state(run, RunState.READY_REVIEWER, "run_reviewer")
    assert "READY_REVIEWER" in str(excinfo.value)


def test_in_flight_guard_refuses_to_continue():
    run = make_run(state=RunState.READY_IMPLEMENTER)
    run.in_flight_turn = TurnRecord(role="implementer", cycle=1)
    with pytest.raises(OrchestrationInvalidTransitionError) as excinfo:
        policy.require_no_in_flight_turn(run)
    assert "never replayed" in str(excinfo.value)


def test_cycle_budget_guard_uses_the_model_turn_budget():
    run = make_run(model_turn_budget=2, model_turns_used=2)
    with pytest.raises(OrchestrationCycleLimitError):
        policy.require_cycle_budget(run)
    run.model_turns_used = 1
    policy.require_cycle_budget(run)


def test_transition_record_is_audit_ready():
    run = make_run(state=RunState.READY_IMPLEMENTER)
    record = policy.transition_record(
        action=OrchestrationAction.RUN_IMPLEMENTER,
        source="model_bearing",
        run=run,
        next_state=RunState.READY_REVIEWER,
        role="implementer",
        note="confirmed completion",
    )
    assert isinstance(record, TransitionRecord)
    assert record.action == "run_implementer"
    assert record.source == "model_bearing"
    assert record.role == "implementer"
    assert record.previous_state == "READY_IMPLEMENTER"
    assert record.next_state == "READY_REVIEWER"
    assert record.cycle == 1
    assert record.note == "confirmed completion"
