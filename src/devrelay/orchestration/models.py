"""The v0.3-D run model: bounded state, sanitized audit records, route snapshots.

Nothing here performs I/O and nothing here can call a model.  The persisted
record deliberately contains **no** raw prompt, **no** provider response body,
**no** model reasoning and **no** credential material: only identifiers, hashes,
lengths and accepted bridge evidence.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from devrelay.models import utcnow_iso

#: Persisted run-document schema version (independent of the package version).
ORCHESTRATION_SCHEMA_VERSION = 1

#: Absolute code-level bound: no configuration or caller value may exceed it.
HARD_MAX_CYCLES = 3
MIN_MAX_CYCLES = 1
DEFAULT_MAX_CYCLES = 2

#: Every decision recorded by v0.3-D comes from outside DevRelay.
DECISION_SOURCE = "external_planner"


class RunState(str, Enum):
    """The explicit v0.3-D run states (no fuzzy string states)."""

    READY_IMPLEMENTER = "READY_IMPLEMENTER"
    READY_REVIEWER = "READY_REVIEWER"
    AWAITING_DECISION = "AWAITING_DECISION"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"
    BLOCKED = "BLOCKED"
    LIMIT_REACHED = "LIMIT_REACHED"


#: Once terminal, no model-bearing orchestration action may run again.
TERMINAL_STATES: frozenset[RunState] = frozenset(
    {
        RunState.COMPLETED,
        RunState.STOPPED,
        RunState.BLOCKED,
        RunState.LIMIT_REACHED,
    }
)

#: The only decisions an external Planner may record.
class Decision(str, Enum):
    COMPLETE = "complete"
    REQUEST_CHANGES = "request_changes"
    STOP = "stop"


#: Audit labels for state-changing operations.
class OrchestrationAction(str, Enum):
    START = "start"
    RUN_IMPLEMENTER = "run_implementer"
    RUN_REVIEWER = "run_reviewer"
    DECIDE = "decide"
    BLOCK = "block"


class RoleRouteSnapshot(BaseModel):
    """Sanitized route captured at run creation (identifiers only)."""

    model_config = ConfigDict(extra="forbid")

    role: str
    model: str
    agent: str = ""
    route_source: str = "workspace_config"

    @classmethod
    def from_route(cls, route: Any) -> "RoleRouteSnapshot":
        return cls(
            role=str(route.role),
            model=str(route.model),
            agent=str(getattr(route, "agent", "") or ""),
            route_source=str(getattr(route, "source", "workspace_config")),
        )

    def public(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "model": self.model,
            "agent": self.agent or None,
            "route_source": self.route_source,
        }


class TurnRecord(BaseModel):
    """One attempted model-bearing orchestration phase (sanitized evidence)."""

    model_config = ConfigDict(extra="forbid")

    role: str
    cycle: int
    started_at: str = Field(default_factory=utcnow_iso)
    completed_at: str = ""
    #: Only the digest and the length of the Planner-supplied prompt are kept.
    prompt_sha256: str = ""
    prompt_chars: int = 0
    resolved_model: str = ""
    resolved_agent: str = ""
    route_source: str = ""
    #: Accepted bridge evidence.
    operation_state: str = ""
    submission_attempted: bool = False
    submission_status: int | None = None
    submission_uncertain: bool = False
    reply_pending: bool = False
    retry_safe: bool = False
    call_ids: list[str] = Field(default_factory=list)
    assistant_message_ids: list[str] = Field(default_factory=list)
    #: "in_flight" until the accepted role result is recorded; then
    #: "completed" or "blocked".
    outcome: str = "in_flight"
    blocked_reason: str = ""

    def public(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        return data


class DecisionRecord(BaseModel):
    """An explicit external decision (never derived from reviewer prose)."""

    model_config = ConfigDict(extra="forbid")

    decision: str
    source: str = DECISION_SOURCE
    decided_at: str = Field(default_factory=utcnow_iso)
    previous_state: str
    next_state: str


class TransitionRecord(BaseModel):
    """One audited state transition."""

    model_config = ConfigDict(extra="forbid")

    action: str
    source: str
    at: str = Field(default_factory=utcnow_iso)
    previous_state: str
    next_state: str
    cycle: int = 0
    role: str = ""
    note: str = ""


class OrchestrationRun(BaseModel):
    """The durable, validated orchestration run."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = ORCHESTRATION_SCHEMA_VERSION
    run_id: str
    workspace: str
    state: RunState = RunState.READY_IMPLEMENTER

    implementer_session_id: str
    reviewer_session_id: str

    max_cycles: int = DEFAULT_MAX_CYCLES
    current_cycle: int = 1
    completed_cycles: int = 0

    turn_attempts: int = 0
    model_turn_budget: int = 0
    model_turns_used: int = 0

    created_at: str = Field(default_factory=utcnow_iso)
    updated_at: str = Field(default_factory=utcnow_iso)

    route_snapshot: dict[str, RoleRouteSnapshot] = Field(default_factory=dict)

    last_transition: TransitionRecord | None = None
    implementer_turns: list[TurnRecord] = Field(default_factory=list)
    reviewer_turns: list[TurnRecord] = Field(default_factory=list)
    decision_history: list[DecisionRecord] = Field(default_factory=list)

    #: Set while a model-bearing phase is in flight.  A persisted in-flight turn
    #: is never replayed: the next mutating operation fails the run closed.
    in_flight_turn: TurnRecord | None = None
    blocked_reason: str = ""

    # ------------------------------------------------------------------
    @property
    def terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    @property
    def previous_state(self) -> str:
        return self.last_transition.previous_state if self.last_transition else ""

    @property
    def turns(self) -> list[TurnRecord]:
        return [*self.implementer_turns, *self.reviewer_turns]

    def summary(self) -> dict[str, Any]:
        """The envelope-visible projection: enough for a Planner to act legally."""
        return {
            "run_id": self.run_id,
            "workspace": self.workspace,
            "state": self.state.value,
            "previous_state": self.previous_state,
            "terminal": self.terminal,
            "cycle": self.current_cycle,
            "completed_cycles": self.completed_cycles,
            "max_cycles": self.max_cycles,
            "turn_attempts": self.turn_attempts,
            "model_turns_used": self.model_turns_used,
            "model_turn_budget": self.model_turn_budget,
            "model_turns_remaining": max(self.model_turn_budget - self.model_turns_used, 0),
            "blocked_reason": self.blocked_reason,
            "in_flight": self.in_flight_turn is not None,
            "implementer_session_id": self.implementer_session_id,
            "reviewer_session_id": self.reviewer_session_id,
            "route_snapshot": {
                role: snapshot.public() for role, snapshot in sorted(self.route_snapshot.items())
            },
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_transition": (
                self.last_transition.model_dump(mode="json") if self.last_transition else None
            ),
            "implementer_turns": [turn.public() for turn in self.implementer_turns],
            "reviewer_turns": [turn.public() for turn in self.reviewer_turns],
            "decision_history": [
                record.model_dump(mode="json") for record in self.decision_history
            ],
            "legal_next_actions": legal_next_actions(self.state),
            "acceptance_authority": False,
        }


def legal_next_actions(state: RunState) -> list[str]:
    """The orchestration actions that are legal from *state* (Planner guidance)."""
    if state is RunState.READY_IMPLEMENTER:
        return ["devrelay_run_implementer"]
    if state is RunState.READY_REVIEWER:
        return ["devrelay_run_reviewer"]
    if state is RunState.AWAITING_DECISION:
        return ["devrelay_decide_run(complete|request_changes|stop)"]
    return []


__all__ = [
    "DECISION_SOURCE",
    "DEFAULT_MAX_CYCLES",
    "HARD_MAX_CYCLES",
    "MIN_MAX_CYCLES",
    "ORCHESTRATION_SCHEMA_VERSION",
    "TERMINAL_STATES",
    "Decision",
    "DecisionRecord",
    "OrchestrationAction",
    "OrchestrationRun",
    "RoleRouteSnapshot",
    "RunState",
    "TransitionRecord",
    "TurnRecord",
    "legal_next_actions",
]
