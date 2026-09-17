"""v0.3-D orchestration service: durable runs over the accepted v0.3-C role path.

Every model-bearing method performs **at most one** accepted role turn:

    load -> bounds/state checks -> route snapshot check -> session ownership
         -> persist intent (in-flight) -> one role call -> record evidence
         -> transition -> atomic save

Nothing in this module parses provider text, counts reviewer verdicts or decides
whether the work is good: the external Planner decides, and a successful reviewer
turn always stops at ``AWAITING_DECISION``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from devrelay.errors import (
    DevRelayError,
    OrchestrationCycleLimitError,
    OrchestrationInvalidTransitionError,
    OrchestrationRouteChangedError,
    OrchestrationSessionConflictError,
)
from devrelay.models import utcnow_iso
from devrelay.opencode.models import prompt_digest
from devrelay.orchestration import state_machine as policy
from devrelay.orchestration.models import (
    DECISION_SOURCE,
    DEFAULT_MAX_CYCLES,
    HARD_MAX_CYCLES,
    MIN_MAX_CYCLES,
    Decision,
    DecisionRecord,
    OrchestrationAction,
    OrchestrationRun,
    RoleRouteSnapshot,
    RunState,
    TurnRecord,
)
from devrelay.orchestration.store import OrchestrationStore

#: Audit-source labels.
SOURCE_EXTERNAL = DECISION_SOURCE
SOURCE_MODEL = "model_bearing"
SOURCE_INTERNAL = "internal"


@dataclass(frozen=True)
class OrchestrationOutcome:
    """The truthful result of one orchestration action."""

    run: OrchestrationRun
    ok: bool = True
    error_type: str = ""
    error_message: str = ""

    @property
    def summary(self) -> dict[str, Any]:
        return self.run.summary()


class OrchestrationService:
    """Durable bounded orchestration bound to one workspace."""

    def __init__(
        self,
        *,
        router: Any,
        bridge_provider: Callable[[], Any],
        devrelay_dir: str | Path,
        workspace_root: str | Path,
        store: OrchestrationStore | None = None,
    ) -> None:
        self._router = router
        self._bridge_provider = bridge_provider
        self.workspace_root = Path(workspace_root)
        self.store = store or OrchestrationStore(devrelay_dir)

    # ------------------------------------------------------------------
    # shared helpers
    # ------------------------------------------------------------------
    def _bridge(self) -> Any:
        return self._bridge_provider()

    def _verify_session(self, session_id: str) -> None:
        """Both sessions must belong to the bound workspace (fail before start)."""
        try:
            result = self._bridge().get_session(session_id)
        except DevRelayError as exc:
            raise OrchestrationSessionConflictError(
                f"session {session_id} could not be verified in this workspace "
                f"({getattr(exc, 'code', type(exc).__name__)}); an orchestration run "
                "requires two existing, owned sessions (nothing is created or "
                "substituted)"
            ) from exc
        session = getattr(result, "session", None)
        if not getattr(result, "ok", False) or session is None:
            raise OrchestrationSessionConflictError(
                f"session {session_id} could not be verified in this workspace "
                f"({getattr(result, 'error_type', '') or 'no session record'}); an "
                "orchestration run requires two existing, owned sessions"
            )
        if not getattr(session, "workspace_match", False):
            raise OrchestrationSessionConflictError(
                f"session {session_id} does not belong to the bound workspace; an "
                "orchestration run requires two existing, owned sessions "
                "(no session is created, reused or substituted)"
            )

    def _current_routes(self) -> dict[str, RoleRouteSnapshot]:
        return {
            role: RoleRouteSnapshot.from_route(self._router.resolve(role))
            for role in ("implementer", "reviewer")
        }

    def _require_route_unchanged(self, run: OrchestrationRun, role: str) -> RoleRouteSnapshot:
        current = RoleRouteSnapshot.from_route(self._router.resolve(role))
        snapshot = run.route_snapshot.get(role)
        if snapshot is None or snapshot.model_dump() != current.model_dump():
            self._block(run, reason="route_changed", role=role, note="role route changed")
            raise OrchestrationRouteChangedError(
                f"the configured route for role {role} changed during run {run.run_id}; "
                "the run is failed closed instead of silently continuing under a new route"
            )
        return snapshot

    def _block(
        self, run: OrchestrationRun, *, reason: str, role: str = "", note: str = ""
    ) -> OrchestrationRun:
        transition = policy.Transition(
            state=RunState.BLOCKED,
            current_cycle=run.current_cycle,
            completed_cycles=run.completed_cycles,
            blocked_reason=reason,
        )
        record = policy.transition_record(
            action=OrchestrationAction.BLOCK,
            source=SOURCE_INTERNAL,
            run=run,
            next_state=RunState.BLOCKED,
            role=role,
            note=note or reason,
        )
        transition.apply(run, record)
        run.updated_at = utcnow_iso()
        self.store.save(run)
        return run

    def _materialize_interrupted_turn(self, run: OrchestrationRun) -> None:
        """A persisted in-flight turn is never replayed: fail the run closed."""
        if run.in_flight_turn is None:
            return
        run.in_flight_turn.outcome = "blocked"
        run.in_flight_turn.blocked_reason = "turn_interrupted"
        run.in_flight_turn.completed_at = utcnow_iso()
        run.in_flight_turn = None
        self._block(
            run,
            reason="turn_interrupted",
            role="",
            note="a model turn was in flight when the process stopped; no replay",
        )

    def _load_for_action(self, run_id: object) -> OrchestrationRun:
        run = self.store.load(run_id)
        self._materialize_interrupted_turn(run)
        return run

    # ------------------------------------------------------------------
    # read-only
    # ------------------------------------------------------------------
    def get_run(self, run_id: object) -> OrchestrationRun:
        """Read durable state only (no OpenCode request, no mutation)."""
        return self.store.load(run_id)

    def list_run_ids(self) -> list[str]:
        if not self.store.root.is_dir():
            return []
        return sorted(path.stem for path in self.store.root.glob("DR-*.json"))

    # ------------------------------------------------------------------
    # start
    # ------------------------------------------------------------------
    def start_run(
        self,
        *,
        implementer_session_id: str,
        reviewer_session_id: str,
        max_cycles: int = DEFAULT_MAX_CYCLES,
    ) -> OrchestrationRun:
        """Create bounded orchestration state.  Never performs a model call."""
        if not isinstance(max_cycles, int) or isinstance(max_cycles, bool):
            raise OrchestrationCycleLimitError("max_cycles must be an integer 1..3")
        if max_cycles < MIN_MAX_CYCLES or max_cycles > HARD_MAX_CYCLES:
            raise OrchestrationCycleLimitError(
                f"max_cycles must be between {MIN_MAX_CYCLES} and {HARD_MAX_CYCLES} "
                f"(the v0.3-D hard bound); got {max_cycles}"
            )
        if not implementer_session_id or not reviewer_session_id:
            raise OrchestrationSessionConflictError(
                "an orchestration run requires an explicit implementer session and "
                "reviewer session (v0.3-D never creates or infers a session)"
            )
        if implementer_session_id == reviewer_session_id:
            raise OrchestrationSessionConflictError(
                "the implementer and reviewer sessions must be different: one session "
                "for both roles would destroy reviewer independence"
            )
        routes = self._current_routes()
        # Ownership is verified before any run exists.
        self._verify_session(implementer_session_id)
        self._verify_session(reviewer_session_id)

        run_id = self.store.new_run_id()
        transition = policy.start_transition()
        run = OrchestrationRun(
            run_id=run_id,
            workspace=str(self.workspace_root),
            implementer_session_id=implementer_session_id,
            reviewer_session_id=reviewer_session_id,
            max_cycles=max_cycles,
            model_turn_budget=2 * max_cycles,
            route_snapshot=routes,
        )
        run.last_transition = policy.transition_record(
            action=OrchestrationAction.START,
            source=SOURCE_EXTERNAL,
            run=run,
            next_state=transition.state,
            note=f"external start with max_cycles={max_cycles}",
        )
        transition.apply(run, run.last_transition)
        return self.store.create(run)

    # ------------------------------------------------------------------
    # model-bearing phases
    # ------------------------------------------------------------------
    def run_implementer(self, run_id: object, prompt: str) -> OrchestrationOutcome:
        return self._run_role(run_id, "implementer", prompt)

    def run_reviewer(self, run_id: object, prompt: str) -> OrchestrationOutcome:
        return self._run_role(run_id, "reviewer", prompt)

    def _run_role(self, run_id: object, role: str, prompt: str) -> OrchestrationOutcome:
        run = self._load_for_action(run_id)
        policy.require_not_terminal(run)
        policy.require_no_in_flight_turn(run)
        expected = (
            RunState.READY_IMPLEMENTER if role == "implementer" else RunState.READY_REVIEWER
        )
        policy.require_state(run, expected, f"run_{role}")
        policy.require_cycle_budget(run)
        snapshot = self._require_route_unchanged(run, role)
        session_id = (
            run.implementer_session_id if role == "implementer" else run.reviewer_session_id
        )
        try:
            self._verify_session(session_id)
        except DevRelayError as exc:
            self._block(
                run, reason="session_not_owned", role=role, note=f"session check failed: {exc.code if hasattr(exc, 'code') else type(exc).__name__}"
            )
            raise

        # Persist the intent *before* the call: a crash mid-call leaves a durable
        # in-flight marker that can never be replayed.
        attempt = TurnRecord(
            role=role,
            cycle=run.current_cycle,
            prompt_sha256=prompt_digest(prompt),
            prompt_chars=len(prompt),
            resolved_model=snapshot.model,
            resolved_agent=snapshot.agent,
            route_source=snapshot.route_source,
        )
        run.in_flight_turn = attempt
        run.turn_attempts += 1
        run.model_turns_used += 1
        run.updated_at = utcnow_iso()
        self.store.save(run)

        error_type = ""
        error_message = ""
        try:
            outcome = self._router.send_role_prompt(
                self._bridge(), role=role, session_id=session_id, prompt=prompt
            )
            result = outcome.result
        except DevRelayError as exc:
            error_type = getattr(exc, "code", "") or type(exc).__name__
            error_message = str(exc)
            result = None
        except Exception as exc:  # noqa: BLE001 - defensive boundary
            error_type = "internal_error"
            error_message = f"{type(exc).__name__} while running the {role} turn"
            result = None

        if result is not None:
            raw_state = getattr(result, "state", "")
            attempt.operation_state = str(getattr(raw_state, "value", "") or raw_state or "")
            attempt.submission_attempted = bool(getattr(result, "submission_attempted", False))
            attempt.submission_status = getattr(result, "submission_status", None)
            attempt.submission_uncertain = bool(getattr(result, "submission_uncertain", False))
            attempt.reply_pending = bool(getattr(result, "reply_pending", False))
            attempt.retry_safe = bool(getattr(result, "retry_safe", False))
            attempt.call_ids = [str(call_id) for call_id in (result.call_ids or [])]
            attempt.assistant_message_ids = [
                str(message.message_id) for message in (result.messages or [])
            ]

        achieved = bool(
            result is not None
            and getattr(result, "ok", False)
            and not attempt.submission_uncertain
            and not attempt.reply_pending
        )
        if not achieved and not error_type:
            # keep the accepted bridge/role taxonomy when it is available
            error_type = str(getattr(result, "error_type", "") or "") or "submission_not_confirmed"
            error_message = (
                "the role turn did not reach a confirmed completion "
                "(uncertain submission or pending reply); the run is blocked and is "
                "never retried automatically"
            )

        attempt.outcome = "completed" if achieved else "blocked"
        attempt.blocked_reason = "" if achieved else error_type
        attempt.completed_at = utcnow_iso()
        run.in_flight_turn = None

        transition = policy.after_role_turn(
            run, role, policy.TurnOutcome(ok=achieved, blocked_reason=error_type)
        )
        record = policy.transition_record(
            action=(
                OrchestrationAction.RUN_IMPLEMENTER
                if role == "implementer"
                else OrchestrationAction.RUN_REVIEWER
            ),
            source=SOURCE_MODEL,
            run=run,
            next_state=transition.state,
            role=role,
            note="confirmed completion" if achieved else f"blocked: {error_type}",
        )
        transition.apply(run, record)
        if role == "implementer":
            run.implementer_turns.append(attempt)
        else:
            run.reviewer_turns.append(attempt)
        run.updated_at = utcnow_iso()
        self.store.save(run)

        return OrchestrationOutcome(
            run=run,
            ok=achieved,
            error_type="" if achieved else error_type,
            error_message="" if achieved else error_message,
        )

    # ------------------------------------------------------------------
    # explicit external decision
    # ------------------------------------------------------------------
    def decide_run(self, run_id: object, decision: object) -> OrchestrationOutcome:
        """Record an explicit external decision.  No model call, ever."""
        run = self._load_for_action(run_id)
        policy.require_not_terminal(run)
        policy.require_no_in_flight_turn(run)
        policy.require_state(run, RunState.AWAITING_DECISION, "decide_run")
        if isinstance(decision, str):
            try:
                decision_value = Decision(decision)
            except ValueError as exc:
                raise OrchestrationInvalidTransitionError(
                    f"unknown decision {decision!r}; v0.3-D supports exactly "
                    "complete, request_changes and stop"
                ) from exc
        elif isinstance(decision, Decision):
            decision_value = decision
        else:
            raise OrchestrationInvalidTransitionError(
                f"decision must be one of complete, request_changes, stop (got "
                f"{type(decision).__name__})"
            )

        transition = policy.after_decision(run, decision_value)
        record = policy.transition_record(
            action=OrchestrationAction.DECIDE,
            source=SOURCE_EXTERNAL,
            run=run,
            next_state=transition.state,
            note=f"external decision={decision_value.value}",
        )
        transition.apply(run, record)
        run.decision_history.append(
            DecisionRecord(
                decision=decision_value.value,
                previous_state=record.previous_state,
                next_state=record.next_state,
            )
        )
        run.updated_at = utcnow_iso()
        self.store.save(run)
        return OrchestrationOutcome(run=run, ok=True)


__all__ = ["OrchestrationOutcome", "OrchestrationService", "SOURCE_EXTERNAL", "SOURCE_INTERNAL", "SOURCE_MODEL"]
