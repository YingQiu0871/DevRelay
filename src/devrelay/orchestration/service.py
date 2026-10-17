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
    RoleRoutingError,
    OrchestrationAdoptionDisabledError,
    OrchestrationCycleLimitError,
    OrchestrationInvalidTransitionError,
    OrchestrationRecoveryAlreadyResolvedError,
    OrchestrationRecoveryRequiredError,
    OrchestrationRecoveryUnsupportedError,
    OrchestrationRouteChangedError,
    OrchestrationSessionConflictError,
)
from devrelay.models import utcnow_iso
from devrelay.opencode.models import prompt_digest
from devrelay.orchestration import ledger_reader, recovery
from devrelay.orchestration import state_machine as policy
from devrelay.orchestration.models import (
    DECISION_SOURCE,
    DEFAULT_MAX_CYCLES,
    HARD_MAX_CYCLES,
    MIN_MAX_CYCLES,
    ORCHESTRATION_SCHEMA_VERSION,
    Decision,
    DecisionRecord,
    OrchestrationAction,
    OrchestrationRun,
    RecoveryRecord,
    RecoveryResolution,
    RoleRouteSnapshot,
    RunState,
    TurnOutcomeState,
    TurnRecord,
)
from devrelay.orchestration.store import OrchestrationStore

#: Audit-source labels.
SOURCE_EXTERNAL = DECISION_SOURCE
SOURCE_MODEL = "model_bearing"
SOURCE_INTERNAL = "internal"


def _unconfirmed_turn_message(role: str, attempt: TurnRecord) -> str:
    """Describe a non-confirmed turn from the accepted bridge evidence only.

    Never claims uncertainty or a pending reply unless the structured flags say
    so: ``connect_error``/``connect_timeout``/HTTP 500 are *definite* failures, and
    saying "uncertain submission" about them would be false.
    """
    if attempt.submission_uncertain and attempt.reply_pending:
        state = "the submission may have reached OpenCode and its reply is still pending"
    elif attempt.submission_uncertain:
        state = "the submission may have reached OpenCode (uncertain submission)"
    elif attempt.reply_pending:
        state = "the submission was accepted and its reply is still pending"
    elif attempt.submission_attempted:
        status = (
            f"HTTP {attempt.submission_status}"
            if attempt.submission_status is not None
            else "no status"
        )
        state = f"the submission was attempted and did not complete ({status})"
    else:
        state = "no submission was attempted (the request failed before the model call)"
    return (
        f"the {role} turn did not reach a confirmed completion: {state}; the run is "
        "blocked and is never retried automatically"
    )


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
        try:
            resolved = self._router.resolve(role)
        except RoleRoutingError as exc:
            # The role captured by this run can no longer be resolved (the
            # workspace configuration became unconfigured or invalid).  That is
            # route invalidation for an existing run - fail it closed, keep the
            # snapshot, and never fall back to another route or model.
            self._block(
                run,
                reason="route_changed",
                role=role,
                note=f"role route unresolvable: {getattr(exc, 'code', type(exc).__name__)}",
            )
            raise OrchestrationRouteChangedError(
                f"the configured route for role {role} can no longer be resolved "
                f"({getattr(exc, 'code', type(exc).__name__)}); run {run.run_id} is failed "
                "closed (no route replacement, no default model, no fallback)"
            ) from exc
        current = RoleRouteSnapshot.from_route(resolved)
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
        """Finalize a persisted in-flight turn into the role history, then block.

        The interrupted attempt is *never* replayed, but its sanitized evidence
        must survive: the record is completed as ``blocked``/``turn_interrupted``
        and appended to the correct role history (so ``model_turns_used`` keeps a
        matching turn record), the transition keeps the phase action and role as
        provenance, and only then is the run failed closed.
        """
        attempt = run.in_flight_turn
        if attempt is None:
            return
        attempt.outcome = TurnOutcomeState.BLOCKED.value
        attempt.blocked_reason = "turn_interrupted"
        attempt.completed_at = utcnow_iso()
        if attempt.role == "implementer":
            run.implementer_turns.append(attempt)
        else:
            run.reviewer_turns.append(attempt)
        run.in_flight_turn = None
        transition = policy.Transition(
            state=RunState.BLOCKED,
            current_cycle=run.current_cycle,
            completed_cycles=run.completed_cycles,
            blocked_reason="turn_interrupted",
        )
        record = policy.transition_record(
            action=(
                OrchestrationAction.RUN_IMPLEMENTER
                if attempt.role == "implementer"
                else OrchestrationAction.RUN_REVIEWER
            ),
            source=SOURCE_MODEL,
            run=run,
            next_state=RunState.BLOCKED,
            role=attempt.role,
            note="interrupted before the accepted result was recorded; never replayed",
        )
        transition.apply(run, record)
        run.updated_at = utcnow_iso()
        self.store.save(run)

    def _load_for_action(self, run_id: object) -> OrchestrationRun:
        run = self.store.load(run_id)
        if run.schema_version < 2:
            # The frozen v0.3-D contract (V03E_SPEC §10): a v1 document keeps
            # exactly its old behaviour, is never migrated, and the next mutating
            # action materializes the interrupted turn as blocked/turn_interrupted.
            self._materialize_interrupted_turn(run)
            return run
        if run.state is RunState.RECOVERY_REQUIRED:
            raise OrchestrationRecoveryRequiredError(
                f"run {run.run_id} is in RECOVERY_REQUIRED "
                f"(recovery_reason={run.recovery_reason}); the only legal write is "
                "devrelay_resolve_recovery(mark_unrecoverable) - no model turn, "
                "decision, retry or resume may run"
            )
        if run.in_flight_turn is not None:
            raise OrchestrationRecoveryRequiredError(
                f"run {run.run_id} has an interrupted model turn "
                f"(role={run.in_flight_turn.role}); it is never replayed - call "
                "devrelay_reconcile_run and then "
                "devrelay_resolve_recovery(mark_unrecoverable)"
            )
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
        try:
            routes = self._current_routes()
        except RoleRoutingError as exc:
            # Nothing durable exists yet, so there is no run to fail closed; the
            # planner still gets the route-change code rather than a
            # provider-shaped or generic error, and no model is ever called.
            raise OrchestrationRouteChangedError(
                "the configured role routes could not be resolved "
                f"({getattr(exc, 'code', type(exc).__name__)}); no orchestration run "
                "was created and no default model or fallback route is substituted"
            ) from exc
        # Ownership is verified before any run exists.
        self._verify_session(implementer_session_id)
        self._verify_session(reviewer_session_id)

        run_id = self.store.new_run_id()
        transition = policy.start_transition()
        run = OrchestrationRun(
            schema_version=ORCHESTRATION_SCHEMA_VERSION,
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
        # A brand-new run has no previous state; do not claim otherwise.
        run.last_transition.previous_state = ""
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
            # Keep the accepted bridge/role taxonomy when it is available, and
            # describe the failure with the *structured evidence* the accepted
            # bridge reported - never with a generic claim about uncertainty.
            error_type = str(getattr(result, "error_type", "") or "") or "submission_not_confirmed"
            error_message = _unconfirmed_turn_message(role, attempt)
        elif not achieved and not error_message:
            error_message = _unconfirmed_turn_message(role, attempt)

        attempt.outcome = (
            TurnOutcomeState.COMPLETED.value if achieved else TurnOutcomeState.BLOCKED.value
        )
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

    # ------------------------------------------------------------------
    # v0.3-E: fail-closed recovery (read-only reconcile, single resolution)
    # ------------------------------------------------------------------
    def _local_evidence(
        self, run: OrchestrationRun, attempt: TurnRecord
    ) -> ledger_reader.LedgerScan:
        """Read-only local accounting evidence.

        Nothing here touches the network: on this bridge every HTTP call is
        ledger-accounted, so a session-history read would itself append call
        records and ``sequence.json`` to the surface a "read-only" reconciliation
        claims not to mutate.  The mandatory core is therefore strictly local; the
        remote half exists only for the gated adoption capability.
        """
        try:
            identity = recovery.attempt_identity(run, attempt)
            return ledger_reader.scan_ledger(
                self.store.devrelay_dir, identity, floor=recovery.previous_floor(run)
            )
        except Exception as exc:  # noqa: BLE001 - evidence collection never decides a resolution
            # Never paper the failure over with an empty ledger section: an
            # unscannable accounting surface is an evidence gap with a reason.
            return ledger_reader.LedgerScan(
                outcome=ledger_reader.OUTCOME_GAP,
                gap_reason=(
                    "the local accounting ledger could not be scanned "
                    f"({type(exc).__name__})"
                ),
            )

    def _route_drift(self, run: OrchestrationRun) -> str:
        """Report-only drift check (never blocks, never rewrites the snapshot)."""
        for role in ("implementer", "reviewer"):
            snapshot = run.route_snapshot.get(role)
            try:
                current = RoleRouteSnapshot.from_route(self._router.resolve(role))
            except RoleRoutingError as exc:
                return (
                    f"{role} route no longer resolves "
                    f"({getattr(exc, 'code', type(exc).__name__)})"
                )
            if snapshot is None or snapshot.model_dump() != current.model_dump():
                return f"{role} route differs from the captured snapshot"
        return ""

    def reconcile_run(self, run_id: object) -> dict[str, object]:
        """Read-only recovery evidence.  Never writes, submits, retries or resumes.

        Legal for any non-terminal v2 document (a v1 document gets the frozen
        v0.3-D report of ``V03E_SPEC.md`` §10); a terminal run is refused locally,
        because there is nothing left to recover and a report could only invite a
        retry the fail-closed contract forbids.  The action is strictly local: it
        performs no provider call, so the durable surface stays byte-identical.
        """
        run = self.store.load(run_id)
        if run.schema_version < 2:
            return recovery.reconcile_report(run, v1_frozen=True)
        if run.terminal:
            raise OrchestrationRecoveryUnsupportedError(
                f"run {run.run_id} is terminal ({run.state.value}): reconcile is "
                "legal only for non-terminal v2 documents; a terminal run is never "
                "reopened or recovered"
            )
        attempt = run.in_flight_turn or (
            run.recovery.attempt if run.recovery is not None else None
        )
        scan: ledger_reader.LedgerScan | None = None
        if attempt is not None:
            scan = self._local_evidence(run, attempt)
        return recovery.reconcile_report(
            run, ledger_scan=scan, route_drift=self._route_drift(run)
        )

    def resolve_recovery(self, run_id: object, resolution: object) -> OrchestrationOutcome:
        """Apply exactly one resolution to the materialized interrupted attempt.

        Only ``mark_unrecoverable`` is available in this build: exactly one blocked
        turn is recorded and the run ends BLOCKED.  Nothing is submitted, retried,
        resumed or adopted, and a resolution is write-once.
        """
        names = ", ".join(recovery.resolution_names())
        if not isinstance(resolution, str):
            raise OrchestrationInvalidTransitionError(
                f"resolution must be one of {names} (got {type(resolution).__name__})"
            )
        try:
            value = RecoveryResolution(resolution)
        except ValueError as exc:
            raise OrchestrationInvalidTransitionError(
                f"unknown recovery resolution {resolution!r}; this build supports {names}"
            ) from exc
        run = self.store.load(run_id)
        if run.schema_version < 2:
            raise OrchestrationRecoveryUnsupportedError(
                f"run {run.run_id} is a frozen v0.3-D (v1) document: it has no "
                "recovery protocol, so no resolution is applied; the next mutating "
                "action fails it closed as BLOCKED/turn_interrupted (never migrated)"
            )
        existing = run.recovery
        if existing is not None and existing.resolution:
            raise OrchestrationRecoveryAlreadyResolvedError(
                existing.resolution, existing.resolved_at
            )
        if (
            value is RecoveryResolution.ADOPT_COMPLETED_TURN
            and not recovery.ADOPTION_CAPABILITY_ENABLED
        ):
            raise OrchestrationAdoptionDisabledError(recovery.ADOPTION_DISABLED_REASON)
        if run.terminal:
            raise OrchestrationInvalidTransitionError(
                f"run {run.run_id} is terminal ({run.state.value}); a terminal run is "
                "never reopened or recovered"
            )
        if run.state is RunState.RECOVERY_REQUIRED:
            return self._apply_resolution(run, value)
        if run.in_flight_turn is not None:
            return self._enter_and_resolve(run, value)
        raise OrchestrationInvalidTransitionError(
            f"run {run.run_id} has no interrupted turn to recover (state "
            f"{run.state.value}, nothing in flight); resolve_recovery applies only to "
            "a v2 live-intent document or a RECOVERY_REQUIRED one"
        )

    def _enter_and_resolve(
        self, run: OrchestrationRun, value: RecoveryResolution
    ) -> OrchestrationOutcome:
        """Materialize the interrupted intent, enter RECOVERY_REQUIRED, resolve."""
        attempt = run.in_flight_turn
        if attempt is None:  # pragma: no cover - caller guarantees a live intent
            raise OrchestrationInvalidTransitionError("no interrupted turn to materialize")
        entry_state = run.state
        reason = recovery.infer_recovery_reason(attempt)
        scan = self._local_evidence(run, attempt)
        evidence, frozen = recovery.build_record(
            run,
            attempt,
            entry_state=entry_state,
            reason=reason,
            ledger_scan=scan,
            remote=recovery.RemoteMatch(
                recovery.REMOTE_GAP,
                gap_reason=recovery.REMOTE_NOT_READ_REASON,
            ),
        )
        run.in_flight_turn = None
        run.recovery = RecoveryRecord(
            attempt=frozen, recovery_reason=reason, evidence=evidence
        )
        run.recovery_reason = reason
        transition = policy.after_enter_recovery(run)
        record = policy.transition_record(
            action=OrchestrationAction.RECOVER,
            source=SOURCE_EXTERNAL,
            run=run,
            next_state=transition.state,
            role=attempt.role,
            note=(
                "materialized interrupted turn (never replayed, never refunded); "
                f"captured reason={reason}"
            ),
        )
        transition.apply(run, record)
        return self._apply_resolution(run, value)

    def _apply_resolution(
        self, run: OrchestrationRun, value: RecoveryResolution
    ) -> OrchestrationOutcome:
        """Resolve the (materialized) record exactly once and persist atomically."""
        record = run.recovery
        if record is None:  # pragma: no cover - invariants guarantee a record
            raise OrchestrationInvalidTransitionError(
                "RECOVERY_REQUIRED requires a materialized recovery record"
            )
        attempt = record.attempt
        if value is RecoveryResolution.MARK_UNRECOVERABLE:
            if attempt.role == "implementer":
                run.implementer_turns.append(attempt)
            else:
                run.reviewer_turns.append(attempt)
            run.recovery = record.model_copy(
                update={
                    "resolution": value.value,
                    "resolved_at": utcnow_iso(),
                }
            )
            transition = policy.after_mark_unrecoverable(run, record.recovery_reason)
            note = (
                "materialized interrupted turn marked unrecoverable: exactly one "
                "blocked turn, no retry, no resume, no adoption"
            )
        else:  # ADOPT_COMPLETED_TURN is disabled in this build
            run.recovery = record.model_copy(
                update={"resolution": value.value, "resolved_at": utcnow_iso()}
            )
            transition = policy.after_adoption(run, attempt.role)
            note = "adopted a completed interrupted turn (proof-gated)"
        record_out = policy.transition_record(
            action=OrchestrationAction.RECOVER,
            source=SOURCE_EXTERNAL,
            run=run,
            next_state=transition.state,
            role=attempt.role,
            note=note,
        )
        transition.apply(run, record_out)
        run.updated_at = utcnow_iso()
        self.store.save(run)
        return OrchestrationOutcome(run=run, ok=True)


__all__ = [
    "OrchestrationOutcome",
    "OrchestrationService",
    "SOURCE_EXTERNAL",
    "SOURCE_INTERNAL",
    "SOURCE_MODEL",
]
