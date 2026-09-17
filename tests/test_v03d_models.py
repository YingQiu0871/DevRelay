"""v0.3-D run model and transition policy (pure, offline)."""

from __future__ import annotations

import pytest

from devrelay.orchestration.models import (
    DECISION_SOURCE,
    DEFAULT_MAX_CYCLES,
    HARD_MAX_CYCLES,
    MIN_MAX_CYCLES,
    TERMINAL_STATES,
    Decision,
    OrchestrationRun,
    RoleRouteSnapshot,
    RunState,
    legal_next_actions,
)
from v03d_helpers import make_run


# ---------------------------------------------------------------------------
# bounds and states
# ---------------------------------------------------------------------------
def test_bounds_match_the_specification():
    assert HARD_MAX_CYCLES == 3
    assert MIN_MAX_CYCLES == 1
    assert DEFAULT_MAX_CYCLES == 2


def test_state_enum_is_explicit_and_complete():
    assert [state.value for state in RunState] == [
        "READY_IMPLEMENTER",
        "READY_REVIEWER",
        "AWAITING_DECISION",
        "COMPLETED",
        "STOPPED",
        "BLOCKED",
        "LIMIT_REACHED",
    ]


def test_terminal_states_are_exactly_the_four_documented_ones():
    assert TERMINAL_STATES == {
        RunState.COMPLETED,
        RunState.STOPPED,
        RunState.BLOCKED,
        RunState.LIMIT_REACHED,
    }
    assert RunState.READY_IMPLEMENTER not in TERMINAL_STATES
    assert RunState.READY_REVIEWER not in TERMINAL_STATES
    assert RunState.AWAITING_DECISION not in TERMINAL_STATES


def test_legal_next_actions_are_deterministic():
    assert legal_next_actions(RunState.READY_IMPLEMENTER) == ["devrelay_run_implementer"]
    assert legal_next_actions(RunState.READY_REVIEWER) == ["devrelay_run_reviewer"]
    assert legal_next_actions(RunState.AWAITING_DECISION) == [
        "devrelay_decide_run(complete|request_changes|stop)"
    ]
    for terminal in sorted(TERMINAL_STATES, key=lambda state: state.value):
        assert legal_next_actions(terminal) == []


# ---------------------------------------------------------------------------
# run document shape
# ---------------------------------------------------------------------------
def test_run_model_is_strict_and_carries_no_content_fields():
    run = make_run()
    assert run.model_config["extra"] == "forbid"
    keys = set(run.model_dump(mode="json"))
    for forbidden in ("prompt", "prompts", "reviewer_text", "reply", "response", "reasoning"):
        assert forbidden not in keys
    # prompt material is represented by digest + length only, on turn records
    assert "prompt_sha256" not in keys  # turns carry it, the run does not


def test_summary_exposes_everything_a_planner_needs():
    run = make_run(state=RunState.AWAITING_DECISION, completed_cycles=1)
    summary = run.summary()
    for field in (
        "run_id",
        "previous_state",
        "state",
        "cycle",
        "completed_cycles",
        "max_cycles",
        "model_turns_used",
        "model_turn_budget",
        "terminal",
        "blocked_reason",
        "route_snapshot",
        "legal_next_actions",
    ):
        assert field in summary, field
    assert summary["state"] == "AWAITING_DECISION"
    assert summary["terminal"] is False
    assert summary["acceptance_authority"] is False


def test_route_snapshot_is_sanitized_identifiers_only():
    snapshot = RoleRouteSnapshot.from_route(
        type("Route", (), {"role": "reviewer", "model": "provider-b/model-b", "agent": "", "source": "workspace_config"})()
    )
    assert snapshot.public() == {
        "role": "reviewer",
        "model": "provider-b/model-b",
        "agent": None,
        "route_source": "workspace_config",
    }


def test_decision_source_is_always_the_external_planner():
    assert DECISION_SOURCE == "external_planner"
    assert Decision.COMPLETE.value == "complete"
    assert Decision.REQUEST_CHANGES.value == "request_changes"
    assert Decision.STOP.value == "stop"
