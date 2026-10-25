"""The v0.3-D run model: bounded state, sanitized audit records, route snapshots.

Nothing here performs I/O and nothing here can call a model.  The persisted
record deliberately contains **no** raw prompt, **no** provider response body,
**no** model reasoning and **no** credential material: only identifiers, hashes,
lengths and accepted bridge evidence.

v0.3-E adds the fail-closed recovery *shape*: the ``RECOVERY_REQUIRED`` state,
exactly one ``recovery`` record holding the materialized interrupted attempt and
its metadata-only ``evidence`` digest, and the two legal recovery actions.  It
adds no submission, retry, resume or adoption capability.
"""

from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from devrelay.models import utcnow_iso

#: Persisted run-document schema version written for **new** runs (v0.5).
ORCHESTRATION_SCHEMA_VERSION = 3

#: The frozen v0.3-D document version.  v1 documents are read with exactly the
#: v0.3-D rules, are never rewritten and never enter ``RECOVERY_REQUIRED``.
LEGACY_SCHEMA_VERSION = 1

#: Every document version this build can read.  A document claiming any other
#: version is corrupt, never migrated.
#: v2 (v0.3-E/v0.4) remains readable but cannot carry switch evidence; v3 is
#: required before the pending-switch path may commit.
SUPPORTED_SCHEMA_VERSIONS: tuple[int, ...] = (
    LEGACY_SCHEMA_VERSION,
    2,
    ORCHESTRATION_SCHEMA_VERSION,
)

#: The only reasons a v2 run may be in ``RECOVERY_REQUIRED``.
RECOVERY_REASONS: tuple[str, ...] = (
    "turn_interrupted",
    "submission_uncertain",
    "reply_pending",
)

#: The audited action label of every recovery edge.
RECOVERY_ACTION = "recover"

#: Domain separator of the metadata-only recovery evidence digest.
EVIDENCE_DIGEST_DOMAIN = "devrelay-evidence-v1"

#: Absolute code-level bound: no configuration or caller value may exceed it.
HARD_MAX_CYCLES = 3
MIN_MAX_CYCLES = 1
DEFAULT_MAX_CYCLES = 2

#: Every decision recorded by v0.3-D comes from outside DevRelay.
DECISION_SOURCE = "external_planner"

#: The semantic roles a run may reference (matches the v0.3-C vocabulary).
SUPPORTED_RUN_ROLES: tuple[str, ...] = ("implementer", "reviewer")


class RunState(str, Enum):
    """The explicit v0.3-D run states (no fuzzy string states)."""

    READY_IMPLEMENTER = "READY_IMPLEMENTER"
    READY_REVIEWER = "READY_REVIEWER"
    AWAITING_DECISION = "AWAITING_DECISION"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"
    BLOCKED = "BLOCKED"
    LIMIT_REACHED = "LIMIT_REACHED"
    #: v0.3-E: non-terminal, execution-frozen.  Reached only by an explicit
    #: recovery edge, never as a side effect of an invalid action.
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


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
    #: v0.3-E: the explicit recovery edge (materialize + one resolution).
    RECOVER = "recover"


class RecoveryResolution(str, Enum):
    """The only two resolution values the v0.3-E contract defines.

    ``mark_unrecoverable`` is the mandatory fail-closed exit and is always
    available.  ``adopt_completed_turn`` is **disabled** in this build (its
    platform proofs never passed) and is refused before any mutation.
    """

    MARK_UNRECOVERABLE = "mark_unrecoverable"
    ADOPT_COMPLETED_TURN = "adopt_completed_turn"


class TurnOutcomeState(str, Enum):
    """The exact outcome vocabulary of a recorded orchestration turn."""

    IN_FLIGHT = "in_flight"
    COMPLETED = "completed"
    BLOCKED = "blocked"


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
    cycle: StrictInt
    started_at: str = Field(default_factory=utcnow_iso)
    completed_at: str = ""
    #: Only the digest and the length of the Planner-supplied prompt are kept.
    prompt_sha256: str = ""
    prompt_chars: StrictInt = 0
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
    #: ``in_flight`` until the accepted role result is recorded, then
    #: ``completed`` or ``blocked`` (constrained vocabulary).
    outcome: str = TurnOutcomeState.IN_FLIGHT.value
    blocked_reason: str = ""

    @model_validator(mode="after")
    def _known_outcome(self) -> "TurnRecord":
        allowed = {item.value for item in TurnOutcomeState}
        if self.outcome not in allowed:
            raise ValueError(
                f"turn outcome {self.outcome!r} is not one of {sorted(allowed)}"
            )
        return self

    def public(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        return data


def _canonical_scalar(value: object) -> str:
    """One digest field as text: no JSON quoting, explicit absence."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, (list, tuple)):
        return ",".join(str(item) for item in value)
    return str(value)


def _evidence_values(
    *,
    run_id: str,
    schema_version: int,
    state: str,
    current_cycle: int,
    completed_cycles: int,
    model_turns_used: int,
    turn_attempts: int,
    attempt_role: str,
    attempt_cycle: int,
    attempt_prompt_sha256: str,
    attempt_prompt_chars: int,
    attempt_resolved_model: str,
    attempt_resolved_agent: str,
    attempt_route_source: str,
    attempt_started_at: str,
    attempt_call_ids: object,
    ledger_call_id: str | None,
    ledger_state: str | None,
    ledger_http_status: int | None,
    ledger_submission_uncertain: bool,
    ledger_response_media_type: str | None,
    ledger_completed_at: str | None,
    remote_message_id: str | None,
    remote_role: str | None,
    remote_created_at: str | None,
    remote_matched_digest: str | None,
) -> list[str]:
    """The exact, ordered v0.3-E evidence field set (``V03E_SPEC.md`` §13)."""
    return [
        EVIDENCE_DIGEST_DOMAIN,
        _canonical_scalar(run_id),
        _canonical_scalar(schema_version),
        _canonical_scalar(state),
        _canonical_scalar(current_cycle),
        _canonical_scalar(completed_cycles),
        _canonical_scalar(model_turns_used),
        _canonical_scalar(turn_attempts),
        _canonical_scalar(attempt_role),
        _canonical_scalar(attempt_cycle),
        _canonical_scalar(attempt_prompt_sha256),
        _canonical_scalar(attempt_prompt_chars),
        _canonical_scalar(attempt_resolved_model),
        _canonical_scalar(attempt_resolved_agent),
        _canonical_scalar(attempt_route_source),
        _canonical_scalar(attempt_started_at),
        _canonical_scalar(list(attempt_call_ids or [])),
        _canonical_scalar(ledger_call_id),
        _canonical_scalar(ledger_state),
        _canonical_scalar(ledger_http_status),
        _canonical_scalar(ledger_submission_uncertain),
        _canonical_scalar(ledger_response_media_type),
        _canonical_scalar(ledger_completed_at),
        _canonical_scalar(remote_message_id),
        _canonical_scalar(remote_role),
        _canonical_scalar(remote_created_at),
        _canonical_scalar(remote_matched_digest),
    ]


class RecoveryEvidence(BaseModel):
    """The frozen, metadata-only evidence set one recovery resolution used.

    It is a *snapshot*: the entry mutation writes it once and never rewrites it.
    ``evidence_sha256`` is recomputed and verified on every load, so a persisted
    record cannot silently claim a different evidence set than the one it
    digest-committed to.  No prompt, response, reasoning or credential material
    is ever part of it (``V03E_SPEC.md`` §13).
    """

    model_config = ConfigDict(extra="forbid")

    evidence_sha256: str
    run_id: str
    schema_version: StrictInt
    state: str
    current_cycle: StrictInt
    completed_cycles: StrictInt
    model_turns_used: StrictInt
    turn_attempts: StrictInt
    attempt_role: str
    attempt_cycle: StrictInt
    attempt_prompt_sha256: str
    attempt_prompt_chars: StrictInt
    attempt_resolved_model: str
    attempt_resolved_agent: str
    attempt_route_source: str
    attempt_started_at: str
    attempt_call_ids: str
    ledger_call_id: str = ""
    ledger_state: str = ""
    ledger_http_status: int | None = None
    ledger_submission_uncertain: bool = False
    ledger_response_media_type: str = ""
    ledger_completed_at: str = ""
    remote_message_id: str = ""
    remote_role: str = ""
    remote_created_at: str = ""
    remote_matched_digest: str = ""
    #: ``proven_interval`` when the strict reader could prove its window,
    #: ``evidence_gap`` when it could not.  Not part of the digest.
    coverage: str = ""

    def values(self) -> list[str]:
        return _evidence_values(
            run_id=self.run_id,
            schema_version=self.schema_version,
            state=self.state,
            current_cycle=self.current_cycle,
            completed_cycles=self.completed_cycles,
            model_turns_used=self.model_turns_used,
            turn_attempts=self.turn_attempts,
            attempt_role=self.attempt_role,
            attempt_cycle=self.attempt_cycle,
            attempt_prompt_sha256=self.attempt_prompt_sha256,
            attempt_prompt_chars=self.attempt_prompt_chars,
            attempt_resolved_model=self.attempt_resolved_model,
            attempt_resolved_agent=self.attempt_resolved_agent,
            attempt_route_source=self.attempt_route_source,
            attempt_started_at=self.attempt_started_at,
            attempt_call_ids=self.attempt_call_ids.split(",") if self.attempt_call_ids else [],
            ledger_call_id=self.ledger_call_id or None,
            ledger_state=self.ledger_state or None,
            ledger_http_status=self.ledger_http_status,
            ledger_submission_uncertain=self.ledger_submission_uncertain,
            ledger_response_media_type=self.ledger_response_media_type or None,
            ledger_completed_at=self.ledger_completed_at or None,
            remote_message_id=self.remote_message_id or None,
            remote_role=self.remote_role or None,
            remote_created_at=self.remote_created_at or None,
            remote_matched_digest=self.remote_matched_digest or None,
        )

    def compute_digest(self) -> str:
        joined = "\n".join(self.values())
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    @model_validator(mode="after")
    def _digest_matches(self) -> "RecoveryEvidence":
        expected = self.compute_digest()
        if self.evidence_sha256 != expected:
            raise ValueError(
                "recovery evidence_sha256 does not match its own canonical field "
                f"set (recorded {self.evidence_sha256!r}, computed {expected!r})"
            )
        return self


class RecoveryRecord(BaseModel):
    """Exactly one materialized interrupted attempt plus its resolution.

    A run has at most one of these.  While unresolved, its attempt is the only
    accounting holder of the consumed slot (it is **not** also in a role
    history); a resolution converts it once, atomically, into that role history.
    """

    model_config = ConfigDict(extra="forbid")

    attempt: TurnRecord
    recovery_reason: str
    resolution: str = ""
    resolved_at: str = ""
    evidence: RecoveryEvidence

    @model_validator(mode="after")
    def _shape(self) -> "RecoveryRecord":
        if self.recovery_reason not in RECOVERY_REASONS:
            raise ValueError(
                f"recovery_reason {self.recovery_reason!r} is not one of "
                f"{list(RECOVERY_REASONS)}"
            )
        allowed = {item.value for item in RecoveryResolution}
        if self.resolution not in allowed | {""}:
            raise ValueError(
                f"recovery resolution {self.resolution!r} is not one of {sorted(allowed)}"
            )
        if (self.resolution == "") != (self.resolved_at == ""):
            raise ValueError(
                "a recovery record records either both its resolution and "
                "resolved_at, or neither"
            )
        # The frozen attempt is a *finished, failed* record.  Only an adopted
        # (proof-gated, disabled) attempt may be recorded as completed.
        expected_outcome = (
            TurnOutcomeState.COMPLETED.value
            if self.resolution == RecoveryResolution.ADOPT_COMPLETED_TURN.value
            else TurnOutcomeState.BLOCKED.value
        )
        if self.attempt.outcome != expected_outcome:
            raise ValueError(
                f"recovery attempt outcome {self.attempt.outcome!r} is not "
                f"{expected_outcome!r} for resolution {self.resolution!r}"
            )
        if self.attempt.completed_at == "":
            raise ValueError("the materialized recovery attempt must be finished")
        if self.attempt.role not in SUPPORTED_RUN_ROLES:
            raise ValueError(
                f"recovery attempt role {self.attempt.role!r} is not a supported role"
            )
        return self

    def public(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


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
    cycle: StrictInt = 0
    role: str = ""
    note: str = ""


_SWITCH_ID_RE = re.compile(r"^SW-[0-9a-f]{32}$")


class SessionSwitchRecord(BaseModel):
    """Append-only evidence for one explicit session switch (v3)."""

    model_config = ConfigDict(extra="forbid")

    switch_id: str
    role: Literal["implementer", "reviewer"]
    source_session_id: str
    target_session_id: str
    switched_at: str
    source_revision: str
    target_lease_acquired_at: str
    operator: Literal["local-http"] = "local-http"
    result: Literal["committed"] = "committed"

    @model_validator(mode="after")
    def _switch_invariants(self) -> "SessionSwitchRecord":
        if not _SWITCH_ID_RE.fullmatch(self.switch_id):
            raise ValueError("switch_id must be SW-<32 lowercase hex>")
        if not self.source_session_id.strip() or not self.target_session_id.strip():
            raise ValueError("source/target session ids must not be blank")
        if self.source_session_id == self.target_session_id:
            raise ValueError("source and target session ids must differ")
        if not self.switched_at or not self.source_revision:
            raise ValueError("switch timestamp/revision evidence is required")
        if not self.target_lease_acquired_at:
            raise ValueError("target lease evidence is required")
        return self


class OrchestrationRun(BaseModel):
    """The durable, validated orchestration run."""

    model_config = ConfigDict(extra="forbid")

    #: Strict, required integers: a persisted document must state them explicitly
    #: and pydantic may never coerce ``"2"``/``2.0``/``true``/``null`` into a
    #: number.  A missing ``schema_version`` is a malformed document, not a
    #: document to migrate, so it has no default.
    schema_version: StrictInt
    run_id: str
    workspace: str
    state: RunState = RunState.READY_IMPLEMENTER

    implementer_session_id: str
    reviewer_session_id: str

    max_cycles: StrictInt = DEFAULT_MAX_CYCLES
    current_cycle: StrictInt = 1
    completed_cycles: StrictInt = 0

    #: One per reserved model-bearing turn slot (equal to ``model_turns_used``).
    turn_attempts: StrictInt = 0
    #: Required: ``model_turn_budget`` is always ``2 x max_cycles`` and a default
    #: of 0 could only ever describe an impossible run.
    model_turn_budget: StrictInt
    #: **Consumed orchestration model-turn budget slots** - NOT a count of
    #: confirmed provider/HTTP submissions.  A slot is consumed when the durable
    #: in-flight intent is committed, before the role/model call is entered, so
    #: ``model_turns_used = 1`` with zero actual POSTs (for example a connect
    #: failure after the slot was reserved) is valid and intentional.  The truth
    #: about an actual submission lives in the ledger and in the per-turn
    #: ``submission_attempted``/``submission_status``/``submission_uncertain``/
    #: ``call_ids`` evidence.
    model_turns_used: StrictInt = 0

    created_at: str = Field(default_factory=utcnow_iso)
    updated_at: str = Field(default_factory=utcnow_iso)

    route_snapshot: dict[str, RoleRouteSnapshot] = Field(default_factory=dict)

    last_transition: TransitionRecord | None = None
    implementer_turns: list[TurnRecord] = Field(default_factory=list)
    reviewer_turns: list[TurnRecord] = Field(default_factory=list)
    decision_history: list[DecisionRecord] = Field(default_factory=list)
    #: v3: append-only switch evidence; empty on v1/v2 documents.
    session_switch_history: list[SessionSwitchRecord] = Field(default_factory=list)

    #: Set while a model-bearing phase is in flight.  A persisted in-flight turn
    #: is never replayed: the next mutating operation fails the run closed.
    in_flight_turn: TurnRecord | None = None
    blocked_reason: str = ""

    #: v0.3-E: the single materialized recovery record (at most one, ever).
    recovery: RecoveryRecord | None = None
    #: v0.3-E: why this run needed recovery - required in RECOVERY_REQUIRED,
    #: empty everywhere else, and repeated verbatim by ``blocked_reason`` once
    #: ``mark_unrecoverable`` resolves it.
    recovery_reason: str = ""

    @model_validator(mode="after")
    def _semantic_invariants(self) -> "OrchestrationRun":
        """Every constructed/loaded run must be semantically honest.

        The validator is imported lazily so this module stays import-cycle free;
        it is the same rule set the store applies on load and on save.
        """
        from devrelay.orchestration.invariants import validate_run_semantics

        validate_run_semantics(self)
        return self

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
            "schema_version": self.schema_version,
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
            "recovery_reason": self.recovery_reason,
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
            "session_switch_history": [
                record.model_dump(mode="json")
                for record in self.session_switch_history
            ],
            "recovery": self.recovery.public() if self.recovery is not None else None,
            # While a model-bearing turn is in flight no model-bearing action is
            # legal: on a v2 document the only legal act is the explicit
            # recovery resolution (on a frozen v1 document nothing is
            # advertised, exactly as in v0.3-D).
            "legal_next_actions": (
                (["devrelay_resolve_recovery"] if self.schema_version >= 2 else [])
                if self.in_flight_turn is not None
                else legal_next_actions(self.state)
            ),
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
    if state is RunState.RECOVERY_REQUIRED:
        # The mandatory fail-closed core: adoption is disabled, so exactly one
        # resolution is legal (``+ adopt_completed_turn`` only once the platform
        # proofs enable it).
        return [
            "devrelay_reconcile_run",
            "devrelay_resolve_recovery(mark_unrecoverable)",
        ]
    return []


__all__ = [
    "DECISION_SOURCE",
    "SUPPORTED_RUN_ROLES",
    "DEFAULT_MAX_CYCLES",
    "EVIDENCE_DIGEST_DOMAIN",
    "HARD_MAX_CYCLES",
    "LEGACY_SCHEMA_VERSION",
    "MIN_MAX_CYCLES",
    "ORCHESTRATION_SCHEMA_VERSION",
    "RECOVERY_ACTION",
    "RECOVERY_REASONS",
    "SUPPORTED_SCHEMA_VERSIONS",
    "TERMINAL_STATES",
    "Decision",
    "DecisionRecord",
    "OrchestrationAction",
    "OrchestrationRun",
    "RecoveryEvidence",
    "RecoveryRecord",
    "RecoveryResolution",
    "RoleRouteSnapshot",
    "RunState",
    "SessionSwitchRecord",
    "TransitionRecord",
    "TurnOutcomeState",
    "TurnRecord",
    "legal_next_actions",
]
