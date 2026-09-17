"""v0.3-D bounded orchestration: durable run state, bounds and legal transitions.

Dependency direction (enforced by tests):

    MCP adapter -> orchestration -> role router (v0.3-C) -> OpenCode bridge (v0.3-A)

The orchestration layer owns *where a run is*, which next action is legal, the
hard cycle bound and the durable audit trail.  It never judges review content:
reviewer prose is evidence, never authority, and an external Planner decision is
the only way out of ``AWAITING_DECISION``.
"""

from __future__ import annotations

from devrelay.orchestration.invariants import validate_run_semantics
from devrelay.orchestration.models import (
    DECISION_SOURCE,
    DEFAULT_MAX_CYCLES,
    HARD_MAX_CYCLES,
    MIN_MAX_CYCLES,
    SUPPORTED_RUN_ROLES,
    ORCHESTRATION_SCHEMA_VERSION,
    TERMINAL_STATES,
    Decision,
    DecisionRecord,
    OrchestrationAction,
    OrchestrationRun,
    RoleRouteSnapshot,
    RunState,
    TransitionRecord,
    TurnOutcomeState,
    TurnRecord,
)
from devrelay.orchestration.service import OrchestrationOutcome, OrchestrationService
from devrelay.orchestration.state_machine import TurnOutcome, after_decision, after_role_turn
from devrelay.orchestration.store import (
    RUN_ID_PATTERN,
    OrchestrationStore,
    generate_run_id,
    valid_run_id,
)

__all__ = [
    "DECISION_SOURCE",
    "DEFAULT_MAX_CYCLES",
    "HARD_MAX_CYCLES",
    "MIN_MAX_CYCLES",
    "ORCHESTRATION_SCHEMA_VERSION",
    "RUN_ID_PATTERN",
    "TERMINAL_STATES",
    "Decision",
    "DecisionRecord",
    "OrchestrationAction",
    "OrchestrationOutcome",
    "OrchestrationRun",
    "OrchestrationService",
    "OrchestrationStore",
    "RoleRouteSnapshot",
    "RunState",
    "TransitionRecord",
    "TurnOutcome",
    "TurnOutcomeState",
    "TurnRecord",
    "after_decision",
    "after_role_turn",
    "generate_run_id",
    "validate_run_semantics",
    "valid_run_id",
]
