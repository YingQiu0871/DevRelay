"""Pipeline engine: drives tasks through the DevRelay state machine.

The engine persists *every* transition and every artifact before moving on, so
``state.json`` is the single source of truth and a task can be resumed after a
process restart or crash.  Provider calls are isolated behind the
implementer/reviewer abstractions and all subprocess execution happens through
the :mod:`devrelay.workspace.runner` module (shell=False everywhere).
"""

from __future__ import annotations

import json
import shlex
from pathlib import Path
from typing import Optional

from devrelay.artifacts.renderer import (
    ReviewBundle,
    render_final_report,
    render_review_request_md,
    render_task_markdown,
    sanitize_review_bundle,
    sanitize_review_result,
    starter_task_markdown,
)
from devrelay.artifacts.store import ArtifactStore
from devrelay.config import (
    ConfigError,
    DevRelayConfig,
    dump_config_yaml,
    load_config,
)
from devrelay.errors import (
    BaselineError,
    BaselineUnavailableError,
    DevRelayError,
    ProviderError,
    ReviewFormatError,
    StateConflictError,
    WorkspaceError,
)
from devrelay.models import (
    AttemptStatus,
    CallErrorType,
    Finding,
    FinalGateRecord,
    IndexSnapshotStatus,
    PolicyViolation,
    PolicyViolationType,
    ProviderAttempt,
    ProviderCallPhase,
    ProviderCallRecord,
    ProviderExecutionResult,
    ProviderKind,
    RepoSnapshot,
    ReviewAttemptStatus,
    ReviewDecision,
    ReviewResult,
    TaskDelta,
    TaskPacket,
    TaskRun,
    TransitionEvent,
    WorkspaceSnapshot,
    utcnow_iso,
)
from devrelay.pipeline.budget import BudgetExhaustedError, ProviderBudget
from devrelay.pipeline.policy import PipelinePolicy
from devrelay.pipeline.review_lifecycle import (
    ReviewSession,
    acknowledge_unfinished_attempts,
    mark_findings,
    stalled_findings,
    unfinished_attempt,
)
from devrelay.pipeline.states import PipelineState, transition
from devrelay.providers.base import (
    ImplementerContext,
    ImplementerProvider,
    ReviewerProvider,
)
from devrelay.providers.evidence import ReviewCallPolicy
from devrelay.redact import sanitize
from devrelay.utils import truncate

# Sanity cap on persisted provider output (kept out of config on purpose).
_MAX_LOG_CHARS = 1_000_000

_UNBLOCK_DEFAULT_TARGET = {
    "max_iterations": "fix",
    "tests_failed": "fix",
    "review_format": "review",
    "reviewer_blocked": "review",
    "review_provider": "review",
    "implementer_failed": "plan",
    "policy_violation": "plan",
    "policy_guard_error": "plan",
    "policy_check_incomplete": "implement",
    "interrupted_attempt": "implement",
    "interrupted_reviewer_attempt": "review",
    "provider_budget_exhausted": "implement",
    "review_stalled": "fix",
    "baseline_error": "plan",
    "internal": "plan",
}

# Appended to budget refusals raised during the review stage so the recovery
# command is unambiguous (`provider_budget_exhausted` defaults to the implement
# stage, but a reviewer-budget refusal must not force another implementer pass).
_REVIEW_BUDGET_HINT = (
    " Blocked during the review stage; to continue reviewing after raising the "
    "limits explicitly: devrelay unblock --to review --refresh-policy "
    "--reason \"...\""
)

_UNBLOCK_TARGETS = {
    "plan": PipelineState.PLAN_READY,
    "implement": PipelineState.IMPLEMENTING,
    "fix": PipelineState.FIX_REQUIRED,
    "review": PipelineState.REVIEWING,
}


class DevRelayEngine:
    def __init__(
        self,
        config: DevRelayConfig,
        store: ArtifactStore,
        workspace,
        implementer: ImplementerProvider,
        reviewer: ReviewerProvider,
        runner=None,
        baselines=None,
    ) -> None:
        self.config = config
        self.policy = PipelinePolicy(config)
        self.store = store
        self.workspace = workspace
        self.implementer = implementer
        self.reviewer = reviewer
        self.runner = runner
        self.baselines = baselines

    def _baseline_service(self):
        if self.baselines is None:
            raise DevRelayError(
                "engine was constructed without a baseline service; "
                "task baselines are mandatory in v0.1-RC"
            )
        return self.baselines

    # ------------------------------------------------------------------ #
    # task-scoped policy (v0.2-A)
    # ------------------------------------------------------------------ #
    def _task_config(self, task: TaskRun) -> DevRelayConfig:
        """Execution policy for *task*: the snapshot taken at task start.

        Editing the workspace ``.devrelay/config.yaml`` mid-task must not
        silently change budget, blocking severities, retries or test policy.
        A missing/unreadable snapshot falls back to the live config and is
        marked auditable via ``task.policy_source == 'live-fallback'``.
        """
        snapshot = self.store.task_dir(task.task_id) / "config.snapshot.yaml"
        if snapshot.is_file():
            try:
                config = load_config(snapshot)
                task.policy_source = "snapshot"
                return config
            except ConfigError:
                task.policy_source = "live-fallback"
                return self.config
        task.policy_source = "live-fallback"
        return self.config

    def refresh_task_policy(self, task_id: str, reason: str) -> TaskRun:
        """Explicitly re-snapshot the live config as this task's policy.

        This is the only supported way to change a running task's budget or
        blocking policy; it is audited and requires a human reason.
        """
        task = self._load(task_id)
        snapshot = self.store.task_dir(task_id) / "config.snapshot.yaml"
        self.store.write_text(snapshot, dump_config_yaml(self.config))
        task.policy_source = "snapshot"
        task.audit.append(
            TransitionEvent(
                from_state=task.state.value,
                to_state=task.state.value,
                note=f"policy snapshot refreshed from workspace config: {reason}",
                by="human",
            )
        )
        self._persist(task)
        return task

    def _policy_for(self, task: TaskRun) -> PipelinePolicy:
        return PipelinePolicy(self._task_config(task))

    def _budget_for(self, task: TaskRun) -> ProviderBudget:
        return ProviderBudget(self._task_config(task).budget)

    # ------------------------------------------------------------------ #
    # persistence helpers
    # ------------------------------------------------------------------ #
    def _load(self, task_id: str) -> TaskRun:
        return self.store.read_task(task_id)

    def _persist(self, task: TaskRun) -> None:
        task.updated_at = utcnow_iso()
        self.store.write_task(task)

    def _move(self, task: TaskRun, to_state: PipelineState, note: str = "") -> None:
        transition(task.state, to_state)
        task.audit.append(
            TransitionEvent(
                from_state=task.state.value,
                to_state=to_state.value,
                note=note,
                by="engine",
            )
        )
        task.state = to_state
    def _hard_fail(self, task: TaskRun, code: str, reason: str) -> None:
        """Provider/execution hard failure -> FAILED (safe, audited)."""
        task.blocked_code = code
        task.blocked_reason = sanitize(truncate(reason, 2000))
        if task.state != PipelineState.FAILED:
            self._move(task, PipelineState.FAILED, note=f"failed: {code}")
        self._persist(task)

    def _block(self, task: TaskRun, code: str, reason: str) -> None:
        task.blocked_code = code
        task.blocked_reason = sanitize(truncate(reason, 2000))
        if task.state != PipelineState.BLOCKED:
            self._move(task, PipelineState.BLOCKED, note=f"blocked: {code}")
        self._persist(task)

    def _record_provider_call(self, task_id: str, record: ProviderCallRecord) -> None:
        """Append an external-call record to the task and persist evidence."""
        task = self._load(task_id)
        task.provider_calls.append(record)
        self._persist(task)
        self.store.write_text(
            self.store.policy_dir(task_id) / f"call-{record.call_id}.json",
            _json_pretty(record),
        )

    # ------------------------------------------------------------------ #
    # policy guard helpers
    # ------------------------------------------------------------------ #
    def _persist_policy_run(
        self,
        task_id: str,
        attempt: int,
        pre: RepoSnapshot,
        post: RepoSnapshot,
        violations: list[PolicyViolation],
    ) -> None:
        policy_dir = self.store.policy_dir(task_id)
        self.store.write_text(
            policy_dir / f"pre-run-{attempt:02d}.json", _json_pretty(pre)
        )
        self.store.write_text(
            policy_dir / f"post-run-{attempt:02d}.json", _json_pretty(post)
        )
        if violations:
            self.store.write_text(
                policy_dir / f"violations-{attempt:02d}.json",
                json.dumps(
                    [v.model_dump(mode="json") for v in violations],
                    indent=2,
                    ensure_ascii=False,
                ),
            )

    def _record_policy_violations(
        self,
        task: TaskRun,
        violations: list[PolicyViolation],
        attempt: int,
    ) -> None:
        seq = len(task.policy_violations)
        for index, violation in enumerate(violations, start=1):
            seq += 1
            violation = violation.model_copy(
                update={"id": f"PV-{attempt:02d}-{index:02d}"}
            )
            task.policy_violations.append(violation)

    # ------------------------------------------------------------------ #
    # provider attempt lifecycle (AUD-02)
    # ------------------------------------------------------------------ #
    def _write_attempt(self, task: TaskRun, record: ProviderAttempt) -> None:
        """Upsert the attempt in task state + policy/attempt-NN.json."""
        for index, existing in enumerate(task.attempts):
            if existing.attempt_id == record.attempt_id:
                task.attempts[index] = record
                break
        else:
            task.attempts.append(record)
        self._persist(task)
        policy_dir = self.store.policy_dir(task.task_id)
        self.store.write_text(
            policy_dir / f"attempt-{record.iteration:02d}.json", _json_pretty(record)
        )

    def _finalize_attempt(
        self, task: TaskRun, record: ProviderAttempt, status: AttemptStatus
    ) -> TaskRun:
        """Close the attempt (crash marker cleared) and persist everything."""
        record.status = status
        record.completed_at = utcnow_iso()
        current = self._load(task.task_id)
        current.attempt_in_flight = False
        self._write_attempt(current, record)
        return current

    def _preflight_index_check(
        self, task: TaskRun, record: ProviderAttempt, pre: RepoSnapshot, events: list[str]
    ) -> bool:
        """Fail closed BEFORE the provider starts when index state is unusable.

        Running the provider first would spend quota and could mutate the
        workspace that DevRelay cannot verify.
        """
        if pre.index_snapshot_status is IndexSnapshotStatus.OK:
            return True
        current = self._finalize_attempt(
            task, record, AttemptStatus.POLICY_CHECK_INCOMPLETE
        )
        self.store.write_text(
            self.store.policy_dir(task.task_id)
            / f"pre-run-{record.iteration:02d}.json",
            _json_pretty(pre),
        )
        self._block(
            current,
            "policy_check_incomplete",
            "index-mutation verification is impossible in this repository "
            f"state (index snapshot: {pre.index_snapshot_status.value}"
            + (f" - {pre.index_snapshot_error}" if pre.index_snapshot_error else "")
            + "). Provider execution was refused before it started; resolve "
            "unresolved merge conflicts / index problems, then "
            "'devrelay unblock --reason \"...\"'.",
        )
        events.append(
            f"[{task.task_id}] BLOCKED before provider run: index snapshot "
            f"{pre.index_snapshot_status.value} (fail closed)"
        )
        return False

    # ------------------------------------------------------------------ #
    # lifecycle
    # ------------------------------------------------------------------ #
    def create_task(self, title: str) -> TaskRun:
        # Read-only repo check first (never refreshes the real index).
        if not getattr(self.workspace, "detect_repo", lambda: False)():
            raise WorkspaceError(
                "DevRelay tasks require a git repository workspace "
                f"({self.workspace.root}). Run 'git init' first."
            )
        task_id = self.store.allocate_task_id()
        task = TaskRun(  # starts in NEW; _move below goes NEW -> PLAN_REQUIRED
            task_id=task_id,
            title=title.strip() or "(untitled)",
            packet=TaskPacket(task_id=task_id, title=title.strip() or "(untitled)"),
        )
        task_dir = self.store.task_dir(task_id)
        task_dir.mkdir(parents=True, exist_ok=True)
        for sub in (
            "implementation",
            "reviews",
            "logs",
            "final",
            "baseline",
            "policy",
        ):
            (task_dir / sub).mkdir(parents=True, exist_ok=True)
        # Capture the durable task-start workspace baseline BEFORE any
        # provider work.  Uses a temporary GIT_INDEX_FILE; the user's real
        # index is never modified.
        try:
            baseline = self._baseline_service().capture(task_id)
        except BaselineError as exc:
            import shutil

            shutil.rmtree(task_dir, ignore_errors=True)
            raise
        task.baseline = baseline
        task.initial_snapshot = WorkspaceSnapshot(
            repo_root=str(self.workspace.root),
            head_sha=baseline.head_sha,
            branch=baseline.branch,
            dirty_files=(
                list(baseline.preexisting_dirty_files)
                + list(baseline.preexisting_untracked_files)
            ),
            has_git=True,
        )
        self.store.write_text(
            task_dir / "task.json",
            _json_pretty(task.packet),
        )
        self.store.write_text(
            task_dir / "task.md",
            starter_task_markdown(task_id, task.title),
        )
        self.store.write_text(
            task_dir / "config.snapshot.yaml",
            dump_config_yaml(self.config),
        )
        self._move(task, PipelineState.PLAN_REQUIRED, note="task created")
        self._persist(task)
        self.store.set_current_task(task_id)
        return task

    def import_plan(self, task_id: str, packet: TaskPacket) -> TaskRun:
        task = self._load(task_id)
        if task.state not in (PipelineState.PLAN_REQUIRED,):
            raise StateConflictError(
                f"task {task_id} is in state {task.state.value}; a plan can "
                "only be imported while PLAN_REQUIRED"
            )
        if packet.task_id and packet.task_id != task_id:
            raise StateConflictError(
                f"packet.task_id '{packet.task_id}' does not match task '{task_id}'"
            )
        packet = packet.model_copy(update={"task_id": task_id})
        task.packet = packet
        task.title = packet.title or task.title
        task.plan_ready = True
        task_dir = self.store.task_dir(task_id)
        self.store.write_text(task_dir / "task.json", _json_pretty(packet))
        self.store.write_text(task_dir / "task.md", render_task_markdown(packet))
        self._move(task, PipelineState.PLAN_READY, note="plan imported")
        self._persist(task)
        return task

    # ------------------------------------------------------------------ #
    # continue: one automatic push as far as policy allows
    # ------------------------------------------------------------------ #
    def continue_task(self, task_id: str) -> list[str]:
        events: list[str] = []
        max_steps = 10 + self._policy_for(self._load(task_id)).max_fix_iterations * 4
        steps = 0
        while steps < max_steps:
            steps += 1
            task = self._load(task_id)
            state = task.state
            if state not in {
                PipelineState.PLAN_READY,
                PipelineState.IMPLEMENTING,
                PipelineState.TESTING,
                PipelineState.REVIEWING,
                PipelineState.FIX_REQUIRED,
                PipelineState.FIXING,
            }:
                break
            again = self._advance_once(task, events)
            current = self._load(task_id).state
            if not again:
                break
            if current == PipelineState.FIX_REQUIRED and not self.reviewer.automatic:
                break
        if steps >= max_steps:  # pragma: no cover - hard guard
            events.append("[engine] safety stop: too many automatic steps")
        if not events:
            final = self._load(task_id)
            if final.state in (PipelineState.BLOCKED, PipelineState.FAILED):
                events.append(
                    f"[{task_id}] task is {final.state.value}"
                    + (f" ({final.blocked_code})" if final.blocked_code else "")
                    + (f": {final.blocked_reason}" if final.blocked_reason else "")
                    + " - use 'devrelay unblock --reason \"...\"' to resume manually"
                )
        return events

    def _advance_once(self, task: TaskRun, events: list[str]) -> bool:
        state = task.state
        ran_impl = False
        if state in (PipelineState.PLAN_READY, PipelineState.IMPLEMENTING):
            if not self._do_implementation(task, events):
                return False
            ran_impl = True
        elif state in (PipelineState.FIX_REQUIRED, PipelineState.FIXING):
            if not self._do_implementation(task, events):
                return False
            ran_impl = True
        elif state == PipelineState.TESTING:
            ran_impl = True  # resume after crash: tests pending

        task = self._load(task.task_id)
        if task.state == PipelineState.TESTING:
            if not self._do_tests(task, events):
                return False
        task = self._load(task.task_id)
        if task.state == PipelineState.REVIEWING:
            return self._do_review(task, events)
        return False

    # ------------------------------------------------------------------ #
    # implementation stage
    # ------------------------------------------------------------------ #
    def _do_implementation(self, task: TaskRun, events: list[str]) -> bool:
        """Runs the implementer once. True = success and now TESTING.

        Every run is a persisted :class:`ProviderAttempt`: the PRE snapshot and
        the crash marker are written BEFORE the provider is invoked, and the
        POST snapshot + policy guard run for success, non-zero exit,
        timeouts and Python exceptions alike (AUD-02).
        """
        packet = task.packet
        if packet is None:
            raise StateConflictError(
                f"task {task.task_id} has no Task Packet; import a plan first"
            )
        # Fail closed: a previous attempt may have modified the workspace and
        # never completed its post-run verification (hard kill, crash).
        if task.attempt_in_flight:
            self._block(
                task,
                "interrupted_attempt",
                "Previous provider attempt may have modified the workspace and "
                "its post-run verification did not complete. Manual "
                "acknowledgement is required before another provider run: "
                "'devrelay unblock --reason \"...\"'.",
            )
            events.append(
                f"[{task.task_id}] BLOCKED: previous provider attempt is "
                "still marked in-flight (manual acknowledgement required)"
            )
            return False
        policy = self._policy_for(task)
        if task.state == PipelineState.PLAN_READY:
            self._move(task, PipelineState.IMPLEMENTING, note="implementation start")
        elif task.state == PipelineState.FIX_REQUIRED:
            if not policy.can_fix_again(task):
                self._block(
                    task,
                    "max_iterations",
                    "blocking findings remain and max_fix_iterations "
                    f"({policy.max_fix_iterations}) is exhausted; "
                    "unblock explicitly to allow another fix round",
                )
                events.append(
                    f"[{task.task_id}] BLOCKED: max fix iterations reached"
                )
                return False
            task.fix_iterations_used += 1
            self._move(task, PipelineState.FIXING, note="fix iteration start")
        elif task.state not in (PipelineState.IMPLEMENTING, PipelineState.FIXING):
            raise StateConflictError(
                f"cannot implement from state {task.state.value}"
            )

        attempt = task.next_attempt
        is_fix = task.state == PipelineState.FIXING
        record = ProviderAttempt(
            attempt_id=f"{task.task_id}-A{attempt:02d}",
            iteration=attempt,
            phase="FIX" if is_fix else "IMPLEMENT",
        )
        policy_config = self._task_config(task)
        context = ImplementerContext(
            task_id=task.task_id,
            packet=packet,
            attempt=attempt,
            workspace_root=str(self.workspace.root),
            is_fix=is_fix,
            findings=list(task.current_findings),
            reuse_approved_scope=policy_config.scope.reuse_approved_scope,
            current_delta_first=policy_config.scope.current_delta_first,
        )

        # ---- budget gate: never invoke the implementer when it would exceed --
        budget = ProviderBudget(policy_config.budget)
        try:
            budget.check(task, ProviderKind.IMPLEMENTER)
        except BudgetExhaustedError as exc:
            current = self._load(task.task_id)
            self._block(current, "provider_budget_exhausted", str(exc))
            events.append(f"[{task.task_id}] BLOCKED: {exc}")
            return False

        # ---- persist in-flight marker BEFORE the provider starts ----------
        task.attempt_in_flight = True
        self._write_attempt(task, record)
        events.append(
            f"[{task.task_id}] implementing (attempt {attempt}, "
            f"{'fix' if is_fix else 'initial'} pass)"
        )
        service = self._baseline_service()
        try:
            pre_snapshot = service.pre_snapshot()
        except BaselineError as exc:
            current = self._finalize_attempt(
                task, record, AttemptStatus.PROVIDER_ERROR
            )
            self._block(
                current,
                "policy_guard_error",
                f"pre-run repository verification failed: {exc}",
            )
            events.append(
                f"[{task.task_id}] BLOCKED: policy guard could not verify "
                "repository state before the provider run"
            )
            return False
        record.pre_snapshot = pre_snapshot
        self._write_attempt(task, record)  # PRE persisted before the provider run
        if not self._preflight_index_check(task, record, pre_snapshot, events):
            return False

        # ---- provider execution (exceptions are captured, never guessed) ---
        result: ProviderExecutionResult | None = None
        exception: BaseException | None = None
        try:
            result = self.implementer.run(context)
            record.provider_started = True
            record.provider_finished = True
        except (Exception, KeyboardInterrupt) as exc:  # noqa: BLE001 - audited path
            exception = exc
            record.provider_started = True
            record.provider_exception = f"{type(exc).__name__}: {exc}"
        if result is not None:
            record.provider_exit_code = result.exit_code
            record.provider_timed_out = result.timed_out
            record.provider_error = result.error
        self._write_attempt(self._load(task.task_id), record)

        # ---- v0.2-A: persisted external-call accounting --------------------
        provider_unavailable = bool(
            result is not None and result.error and result.exit_code is None
        )
        call_error: CallErrorType | None = None
        call_error_text: str | None = None
        if exception is not None:
            call_error = CallErrorType.EXCEPTION
            call_error_text = f"{type(exception).__name__}: {exception}"
        elif provider_unavailable:
            call_error = CallErrorType.PROVIDER_UNAVAILABLE
            call_error_text = (result.error or "") if result else None
        elif result is not None and not result.success:
            call_error = (
                CallErrorType.TIMEOUT if result.timed_out else CallErrorType.PROVIDER_ERROR
            )
            call_error_text = result.stderr.strip()[:1000] or result.error
        call_record = ProviderCallRecord(
            call_id=f"{record.attempt_id}-impl",
            provider_kind=ProviderKind.IMPLEMENTER,
            provider_name=self.implementer.name,
            phase=(
                ProviderCallPhase.FIX if is_fix else ProviderCallPhase.IMPLEMENT
            ),
            started_at=record.started_at,
            completed_at=utcnow_iso(),
            success=exception is None
            and not provider_unavailable
            and bool(result is not None and result.success),
            attempt_number=attempt,
            task_iteration=attempt,
            duration_seconds=record_duration(record),
            # No external call happened when the CLI was unavailable.
            external_call_count=0 if provider_unavailable else 1,
            error_type=call_error,
            error=sanitize(call_error_text) if call_error_text else None,
            model=None,
            endpoint_host=None,
        )
        self._record_provider_call(task.task_id, call_record)
        events.append(
            f"[{task.task_id}] implementer call recorded "
            f"({call_record.external_call_count} external call, "
            f"{call_record.duration_seconds}s)"
        )

        # ---- POST snapshot + policy guard: always attempted ---------------
        post_snapshot: RepoSnapshot | None = None
        violations: list[PolicyViolation] = []
        guard_error: str | None = None
        try:
            post_snapshot = service.post_snapshot()
            violations = service.check_policy(pre_snapshot, post_snapshot)
            record.policy_checked = True
        except BaselineError as exc:
            guard_error = str(exc)
            record.policy_check_error = guard_error
        record.post_snapshot = post_snapshot
        record.violations = violations
        if post_snapshot is not None:
            self._persist_policy_run(
                task.task_id, attempt, pre_snapshot, post_snapshot, violations
            )

        # ---- logs (evidence for every outcome, incl. exceptions) ----------
        log_dir = self.store.logs_dir(task.task_id)
        stdout_text = result.stdout if result is not None else ""
        stderr_text = result.stderr if result is not None else ""
        if exception is not None:
            stderr_text = (
                f"{stderr_text}\n[DevRelay] provider raised "
                f"{type(exception).__name__}: {exception}\n"
            )
        stdout_file = self.store.write_text(
            log_dir / f"codex-{attempt:02d}.stdout.log",
            sanitize(truncate(stdout_text or "", _MAX_LOG_CHARS)),
        )
        stderr_file = self.store.write_text(
            log_dir / f"codex-{attempt:02d}.stderr.log",
            sanitize(truncate(stderr_text or "", _MAX_LOG_CHARS)),
        )
        events.append(
            f"[{task.task_id}] implementer logs: "
            f"{self.store.rel_path(stdout_file)}, {self.store.rel_path(stderr_file)}"
        )

        # ---- decide, with policy violations taking priority --------------
        if violations:
            incomplete = any(
                v.type == PolicyViolationType.POLICY_CHECK_INCOMPLETE
                for v in violations
            )
            current = self._finalize_attempt(
                task,
                record,
                AttemptStatus.POLICY_CHECK_INCOMPLETE
                if incomplete
                else AttemptStatus.POLICY_VIOLATION,
            )
            self._record_policy_violations(current, violations, attempt)
            first = violations[0]
            code = "policy_check_incomplete" if incomplete else "policy_violation"
            self._block(
                current,
                code,
                f"[{first.type.value}] {first.description} "
                "(policy/violations-*.json has full details)",
            )
            events.append(
                f"[{task.task_id}] BLOCKED: policy check incomplete "
                f"({first.type.value})"
                if incomplete
                else f"[{task.task_id}] BLOCKED: policy violation "
                f"{first.type.value} ({len(violations)} violation(s))"
            )
            if exception is not None:
                events.append(
                    f"[{task.task_id}] provider exception also recorded: "
                    f"{record.provider_exception}"
                )
                return False
            return False
        if guard_error is not None:
            current = self._finalize_attempt(
                task, record, AttemptStatus.POLICY_CHECK_INCOMPLETE
            )
            self._block(
                current,
                "policy_guard_error",
                f"post-run repository verification failed: {guard_error}",
            )
            events.append(
                f"[{task.task_id}] BLOCKED: policy guard could not verify "
                "repository state after the provider run"
            )
            return False
        if exception is not None:
            current = self._finalize_attempt(
                task, record, AttemptStatus.INTERRUPTED
            )
            self._block(
                current,
                "interrupted_attempt",
                "INTERRUPTED_PROVIDER_ATTEMPT: the provider raised "
                f"{record.provider_exception}. The workspace may have been "
                "modified; post-run repository state was captured and "
                "verified. Manual acknowledgement is required before another "
                "provider run: 'devrelay unblock --reason \"...\"'.",
            )
            events.append(
                f"[{task.task_id}] BLOCKED: provider raised "
                f"{type(exception).__name__}; evidence persisted"
            )
            raise exception

        assert result is not None  # no exception != None result
        if result.error and result.exit_code is None:
            # Provider unavailable (e.g. Codex CLI missing): nothing ran, so the
            # task stays IMPLEMENTING/FIXING for a retry after installation.
            current = self._finalize_attempt(
                task, record, AttemptStatus.PROVIDER_UNAVAILABLE
            )
            events.append(f"[{task.task_id}] ERROR: {result.error}")
            return False
        if not result.success:
            reason = (
                f"implementer exit={result.exit_code}"
                + (f" timed_out={result.timed_out}" if result.timed_out else "")
                + f" stderr={result.stderr.strip()[:1000]}"
            )
            current = self._finalize_attempt(task, record, AttemptStatus.PROVIDER_ERROR)
            self._hard_fail(current, "implementer_failed", reason)
            events.append(f"[{task.task_id}] FAILED: {reason}")
            return False

        current = self._finalize_attempt(task, record, AttemptStatus.COMPLETED)
        current.implementation_passes += 1
        summary_body = sanitize(result.report or result.stdout or "")
        summary = (
            f"# Implementation report — attempt {attempt}\n\n"
            f"Generated at {utcnow_iso()} by provider '{self.implementer.name}'.\n\n"
            f"{truncate(summary_body, 200_000)}\n"
        )
        impl_dir = self.store.implementation_dir(current.task_id)
        impl_file = self.store.write_text(
            impl_dir / f"iteration-{attempt:02d}.md", summary
        )
        rel = self.store.rel_path(impl_file)
        if rel not in current.implementation_report_paths:
            current.implementation_report_paths.append(rel)
        self._move(
            current,
            PipelineState.TESTING,
            note=f"implementation attempt {attempt} succeeded",
        )
        self._persist(current)
        events.append(f"[{task.task_id}] implementation done -> TESTING")
        return True

    # ------------------------------------------------------------------ #
    # test stage
    # ------------------------------------------------------------------ #
    def _do_tests(self, task: TaskRun, events: list[str]) -> bool:
        """Runs configured targeted tests (+ full regression for release risk).
        True = tests passed and state moved to REVIEWING."""
        if task.state != PipelineState.TESTING:
            self._move(task, PipelineState.TESTING, note="tests resumed")
        attempt = max(1, task.implementation_passes)
        policy_config = self._task_config(task)
        policy = PipelinePolicy(policy_config)
        command_lines = list(policy_config.tests.targeted)
        if (
            task.packet
            and policy.run_full_regression(task.packet.risk_level)
            and policy_config.tests.full
        ):
            command_lines += [f"[full] {cmd}" for cmd in policy_config.tests.full]
        events.append(
            f"[{task.task_id}] tests: {len(command_lines)} command(s) configured"
        )
        evidence: list[str] = []
        all_ok = True

        for index, raw in enumerate(command_lines, start=1):
            is_full = raw.startswith("[full] ")
            raw_command = raw[len("[full] ") :] if is_full else raw
            try:
                argv = shlex.split(raw_command)
            except ValueError as exc:
                all_ok = False
                evidence.append(f"INVALID command '{raw_command}': {exc}")
                break
            if not argv:
                continue
            result = self.runner.run(
                argv,
                cwd=str(self.workspace.root),
                timeout_seconds=policy_config.tests.timeout_seconds,
            )
            log_dir = self.store.logs_dir(task.task_id)
            self.store.write_text(
                log_dir / f"test-{attempt:02d}-{index:02d}.log",
                sanitize(
                    truncate(
                        f"$ {' '.join(argv)}\n\n{result.stdout}\n\n{result.stderr}",
                        _MAX_LOG_CHARS,
                    )
                ),
            )
            passed = result.success
            line = (
                f"{'PASS' if passed else 'FAIL'} {'[full] ' if is_full else ''}"
                f"{' '.join(argv)} (exit={result.exit_code}, "
                f"{result.duration_seconds:.1f}s)"
            )
            evidence.append(line)
            events.append(f"[{task.task_id}] tests: {line}")
            if not passed:
                all_ok = False
                if result.timed_out:
                    evidence.append("reason: timed out")
                break

        task.test_evidence.extend(evidence)
        task.last_tests_passed = all_ok
        if not all_ok:
            self._persist(task)
            if policy_config.pipeline.auto_fix_tests and policy.can_fix_again(task):
                self._move(task, PipelineState.FIX_REQUIRED, note="tests failed")
                self._persist(task)
                events.append(f"[{task.task_id}] tests failed -> FIX_REQUIRED")
            else:
                self._block(
                    task,
                    "tests_failed",
                    "test command failed: " + (evidence[-1] if evidence else "unknown"),
                )
                events.append(
                    f"[{task.task_id}] BLOCKED: tests failed "
                    "(set pipeline.auto_fix_tests=true to auto-route to fixes)"
                )
            return False

        if not evidence:
            evidence.append("no test commands configured in profile")
            task.test_evidence.extend(evidence)
        self._move(task, PipelineState.REVIEWING, note="tests passed")
        self._persist(task)
        events.append(f"[{task.task_id}] tests passed -> REVIEWING")
        return True

    # ------------------------------------------------------------------ #
    # review stage
    # ------------------------------------------------------------------ #
    def _require_task_delta(self, task: TaskRun) -> TaskDelta:
        """Task-relative delta (baseline -> current). Raises BaselineError."""
        if task.baseline is None:
            raise BaselineUnavailableError(
                f"task {task.task_id} has no task baseline (legacy task); "
                "precise task-relative deltas require a v0.1-RC task with a "
                "captured baseline. Create a new task instead of guessing."
            )
        return self._baseline_service().task_delta(task)

    def _build_review_bundle(self, task: TaskRun) -> ReviewBundle:
        return sanitize_review_bundle(self._build_raw_review_bundle(task))

    def _build_raw_review_bundle(self, task: TaskRun) -> ReviewBundle:
        delta = self._require_task_delta(task)
        diff = delta.text_diff
        diff_limit = self._task_config(task).review.max_diff_bytes
        diff_truncated = len(diff) > diff_limit
        if diff_truncated:
            diff = truncate(diff, diff_limit)
        changed = delta.changed_files
        last_report = ""
        if task.implementation_report_paths:
            try:
                last_report = self.store.read_text(
                    self.store.devrelay_dir / task.implementation_report_paths[-1]
                )
            except OSError:
                last_report = ""
        preexisting: list[str] = []
        if task.baseline is not None:
            preexisting = (
                list(task.baseline.preexisting_dirty_files)
                + list(task.baseline.preexisting_untracked_files)
            )
        elif task.initial_snapshot is not None:
            preexisting = list(task.initial_snapshot.dirty_files)
        return ReviewBundle(
            task_id=task.task_id,
            packet=task.packet or TaskPacket(task_id=task.task_id, title=task.title),
            workspace_root=str(self.workspace.root),
            initial_snapshot=task.initial_snapshot,
            diff=diff,
            changed_files=changed,
            diff_truncated=diff_truncated,
            implementation_summary=last_report,
            implementation_report_paths=list(task.implementation_report_paths),
            test_evidence=list(task.test_evidence),
            previous_reviews=list(task.review_history),
            current_findings=list(task.current_findings),
            preexisting_dirty_files=preexisting,
            attempt=max(1, task.implementation_passes),
            is_fix=task.fix_iterations_used > 0,
        )

    def _do_review(self, task: TaskRun, events: list[str]) -> bool:
        """Starts the review for the current state. Returns True when the
        pipeline should keep moving automatically (auto reviewer, fix needed)."""
        if task.state != PipelineState.REVIEWING:
            raise StateConflictError(f"cannot review from state {task.state.value}")
        # Fail closed: a previous reviewer call may already have been billed.
        if task.review_call_in_flight:
            self._block(
                task,
                "interrupted_reviewer_attempt",
                "A previous reviewer call was still marked in-flight when this "
                "process started (crash or hard kill). That request may already "
                "have consumed provider quota, so DevRelay will not repeat it "
                "automatically. Manual acknowledgement is required: "
                "'devrelay unblock --reason \"...\"'.",
            )
            events.append(
                f"[{task.task_id}] BLOCKED: reviewer call in-flight marker from a "
                "previous run (manual acknowledgement required)"
            )
            return False
        # Fail closed for the wider window: a review round that was started but
        # never finalized (crash after the response arrived) may also have been
        # billed even though the marker was already cleared.
        stale = unfinished_attempt(task)
        if stale is not None:
            self._block(
                task,
                "interrupted_reviewer_attempt",
                f"Review round #{stale.review_number} was started but never "
                "finalized (crash after the provider answered). The request may "
                "already have consumed provider quota, so DevRelay will not "
                "repeat it automatically. Review the persisted call evidence "
                f"({len(stale.call_ids)} call(s) recorded) and acknowledge with "
                "'devrelay unblock --reason \"...\"'.",
            )
            events.append(
                f"[{task.task_id}] BLOCKED: unfinished review round #"
                f"{stale.review_number} (manual acknowledgement required)"
            )
            return False
        try:
            bundle = self._build_review_bundle(task)
        except BaselineError as exc:
            current = self._load(task.task_id)
            self._block(current, "baseline_error", str(exc))
            events.append(
                f"[{task.task_id}] BLOCKED: baseline error - {str(exc)[:300]}"
            )
            return False
        if not self.reviewer.automatic:
            return self._export_manual_request(task, bundle, events)

        policy_config = self._task_config(task)
        budget = ProviderBudget(policy_config.budget)
        review_number = len(task.review_history) + 1
        session = ReviewSession(
            store=self.store,
            task_id=task.task_id,
            review_number=review_number,
            provider_name=self.reviewer.name,
            model=self.reviewer.model,
            endpoint_host=self.reviewer.endpoint_host,
            budget=budget,
            load_task=lambda: self._load(task.task_id),
            persist=self._persist,
            events=events,
        )
        # Budget gate before anything is sent (fail fast, spend nothing).
        try:
            budget.check(task, ProviderKind.REVIEWER)
        except BudgetExhaustedError as exc:
            current = self._load(task.task_id)
            self._block(
                current, "provider_budget_exhausted", str(exc) + _REVIEW_BUDGET_HINT
            )
            events.append(
                f"[{task.task_id}] BLOCKED: {exc}"
            )
            return False

        session.begin()
        call_policy = ReviewCallPolicy(
            format_retries=policy_config.review.retries,
            transport_retries=policy_config.review.transport_retries,
            max_response_chars=policy_config.review.max_response_chars,
            timeout_seconds=policy_config.review.timeout_seconds,
            sink=session,
        )
        try:
            review = sanitize_review_result(
                self.reviewer.review(bundle, call_policy=call_policy)
            )
        except BudgetExhaustedError as exc:
            current = session.finalize(
                ReviewAttemptStatus.BUDGET_BLOCKED, error=str(exc)
            )
            self._block(
                current, "provider_budget_exhausted", str(exc) + _REVIEW_BUDGET_HINT
            )
            events.append(f"[{task.task_id}] BLOCKED: {exc}")
            return False
        except ReviewFormatError as exc:
            current = session.finalize(
                ReviewAttemptStatus.FORMAT_FAILED,
                error_type=CallErrorType.FORMAT,
                error=str(exc),
            )
            self._block(
                current,
                "review_format",
                f"reviewer output could not be validated: {exc}",
            )
            events.append(
                f"[{task.task_id}] BLOCKED: invalid reviewer JSON "
                f"({session.attempt.external_calls_consumed} reviewer call(s) consumed)"
            )
            return False
        except ProviderError as exc:
            current = session.finalize(
                ReviewAttemptStatus.TRANSPORT_FAILED,
                error_type=CallErrorType.TRANSPORT,
                error=str(exc),
            )
            self._block(current, "review_provider", str(exc))
            events.append(
                f"[{task.task_id}] BLOCKED: review provider error "
                f"({session.attempt.external_calls_consumed} reviewer call(s) consumed)"
            )
            return False
        except (Exception, KeyboardInterrupt) as exc:  # noqa: BLE001 - audited path
            session.finalize(
                ReviewAttemptStatus.INTERRUPTED,
                error_type=CallErrorType.EXCEPTION,
                error=f"{type(exc).__name__}: {exc}",
            )
            current = self._load(task.task_id)
            self._block(
                current,
                "interrupted_reviewer_attempt",
                "INTERRUPTED_REVIEWER_ATTEMPT: the reviewer raised "
                f"{type(exc).__name__}: {exc}. Call evidence was persisted; "
                "manual acknowledgement is required before another reviewer "
                "call: 'devrelay unblock --reason \"...\"'.",
            )
            events.append(
                f"[{task.task_id}] BLOCKED: reviewer raised "
                f"{type(exc).__name__}; evidence persisted"
            )
            raise exc

        current = session.finalize(ReviewAttemptStatus.COMPLETED, result=review)
        events.append(
            f"[{task.task_id}] review #{review_number} via "
            f"{self.reviewer.name}"
            + (f" ({self.reviewer.model})" if self.reviewer.model else "")
            + f": {session.attempt.external_calls_consumed} call(s), "
            f"{session.attempt.transport_attempts} HTTP attempt(s)"
        )
        return self._apply_review(current, review, events)

    def _export_manual_request(
        self, task: TaskRun, bundle: ReviewBundle, events: list[str]
    ) -> bool:
        review_number = len(task.review_history) + 1
        content = self.reviewer.prepare_request(bundle, review_number) or ""
        reviews_dir = self.store.reviews_dir(task.task_id)
        path = self.store.write_text(
            reviews_dir / f"review-{review_number:02d}-request.md", content
        )
        events.append(
            f"[{task.task_id}] manual review request written: "
            f"{self.store.rel_path(path)}"
        )
        events.append(
            f"[{task.task_id}] awaiting manual review import "
            "(devrelay review import <file.json>)"
        )
        self._persist(task)
        return False

    def _apply_review(
        self, task: TaskRun, review: ReviewResult, events: list[str]
    ) -> bool:
        """Persists the review and applies the policy decision.

        The reviewer's ``decision`` string is never the final authority: the
        task policy (``blocking_severities``) decides FIX vs PASS.
        """
        policy = self._policy_for(task)
        # A reviewer may echo secrets from the diff; persist only sanitized text.
        review = sanitize_review_result(self._normalize_review(task.task_id, review))
        review = mark_findings(review, task)  # fingerprints + seen counters
        review_number = len(task.review_history) + 1
        reviews_dir = self.store.reviews_dir(task.task_id)
        result_file = self.store.write_text(
            reviews_dir / f"review-{review_number:02d}-result.json",
            _json_pretty(review),
        )
        task.review_history.append(review)
        task.last_review = review
        blocking = policy.blocking_findings(review)
        task.current_findings = blocking
        task.open_p3 = policy.non_blocking_findings(review)
        self._persist(task)
        events.append(
            f"[{task.task_id}] review #{review_number} stored: "
            f"{self.store.rel_path(result_file)}"
        )

        decision, _ = policy.effective_decision(review)
        if decision == ReviewDecision.BLOCKED:
            self._block(
                task,
                "reviewer_blocked",
                review.summary or "reviewer returned decision=BLOCKED",
            )
            events.append(f"[{task.task_id}] BLOCKED: reviewer decision=BLOCKED")
            return False
        if decision == ReviewDecision.REQUEST_CHANGES:
            stalled = stalled_findings(
                review, task, self._task_config(task).pipeline.max_same_finding_cycles
            )
            if stalled:
                first = stalled[0]
                self._block(
                    task,
                    "review_stalled",
                    "the same blocking finding keeps returning "
                    f"(fingerprint {first.fingerprint}, seen "
                    f"{task.finding_seen_counts.get(first.fingerprint, 0)}x): "
                    f"[{first.severity.value}] {first.title}. DevRelay stopped the "
                    "loop instead of re-running the same fix until the budget is "
                    "gone; use 'devrelay unblock --reason \"...\"' if another "
                    "cycle is genuinely intended.",
                )
                events.append(
                    f"[{task.task_id}] BLOCKED: review stalled on a repeated "
                    f"finding ({first.severity.value}: {first.title})"
                )
                return False
            if not policy.can_fix_again(task):
                self._block(
                    task,
                    "max_iterations",
                    f"blocking findings remain after "
                    f"{policy.max_fix_iterations} fix iteration(s); "
                    "use 'devrelay unblock --to fix' for an explicit override",
                )
                events.append(f"[{task.task_id}] BLOCKED: max fix iterations reached")
                return False
            self._move(task, PipelineState.FIX_REQUIRED, note="review requested changes")
            self._persist(task)
            events.append(
                f"[{task.task_id}] review found {len(blocking)} blocking "
                "finding(s) -> FIX_REQUIRED"
            )
            return True
        self._move(
            task, PipelineState.FINAL_GATE_REQUIRED, note="review passed"
        )
        self._persist(task)
        events.append(f"[{task.task_id}] review passed -> FINAL_GATE_REQUIRED")
        return False

    @staticmethod
    def _normalize_review(task_id: str, review: ReviewResult) -> ReviewResult:
        findings: list[Finding] = []
        for index, finding in enumerate(review.findings, start=1):
            if not finding.id:
                finding = finding.model_copy(
                    update={"id": f"{finding.severity.value}-{index:02d}"}
                )
            findings.append(finding)
        reviewer = review.reviewer or "manual/imported"
        return review.model_copy(update={"findings": findings, "reviewer": reviewer})

    # ------------------------------------------------------------------ #
    # manual review import / final gate / unblock
    # ------------------------------------------------------------------ #
    def export_review_request(self, task_id: str) -> Path:
        task = self._load(task_id)
        if task.state != PipelineState.REVIEWING:
            raise StateConflictError(
                f"task is in state {task.state.value}; review export requires "
                "REVIEWING"
            )
        if self.reviewer.automatic:
            raise StateConflictError(
                "the configured reviewer is automatic; manual review export "
                "is not applicable"
            )
        try:
            bundle = self._build_review_bundle(task)
        except BaselineError as exc:
            current = self._load(task_id)
            self._block(current, "baseline_error", str(exc))
            raise
        review_number = len(task.review_history) + 1
        content = self.reviewer.prepare_request(bundle, review_number) or ""
        reviews_dir = self.store.reviews_dir(task.task_id)
        path = self.store.write_text(
            reviews_dir / f"review-{review_number:02d}-request.md", content
        )
        return path

    def import_manual_review(self, task_id: str, review: ReviewResult) -> list[str]:
        task = self._load(task_id)
        if task.state != PipelineState.REVIEWING:
            raise StateConflictError(
                f"task is in state {task.state.value}; review import requires "
                "REVIEWING"
            )
        if self.reviewer.automatic:
            raise StateConflictError(
                "the configured reviewer is automatic; importing a manual "
                "review is not applicable"
            )
        events: list[str] = []
        # v0.2-A: manual review is auditable but consumes zero external calls.
        review_number = len(task.review_history) + 1
        session = ReviewSession(
            store=self.store,
            task_id=task.task_id,
            review_number=review_number,
            provider_name="manual",
            model=None,
            endpoint_host=None,
            budget=self._budget_for(task),
            load_task=lambda: self._load(task.task_id),
            persist=self._persist,
            events=events,
        )
        session.record_manual_review(review)
        task = self._load(task_id)
        self._apply_review(task, review, events)
        return events

    def export_final(self, task_id: str) -> Path:
        task = self._load(task_id)
        if task.state != PipelineState.FINAL_GATE_REQUIRED:
            raise StateConflictError(
                f"task is in state {task.state.value}; final export requires "
                "FINAL_GATE_REQUIRED (review must pass first)"
            )
        try:
            bundle = self._build_review_bundle(task)
        except BaselineError as exc:
            current = self._load(task_id)
            self._block(current, "baseline_error", str(exc))
            raise
        content = (
            "# Final gate review request\n\n"
            "Manual final gate: verify the acceptance criteria below against "
            "the final TASK-RELATIVE delta. Approve with `devrelay final "
            "approve` or request changes via a normal review import.\n\n"
            f"**Task:** {task.task_id} — {task.title}\n"
            f"**Initial HEAD:** "
            f"{task.baseline.head_sha if task.baseline else (task.initial_snapshot.head_sha if task.initial_snapshot else '-')}\n"
            "**Diff scope:** task baseline -> current workspace "
            "(pre-existing user changes excluded)\n\n"
            "---\n\n" + render_review_request_md(bundle, review_number=0)
        )
        final_dir = self.store.final_dir(task.task_id)
        path = self.store.write_text(
            final_dir / "final-review-request.md", content
        )
        return path

    def approve_final(self, task_id: str, note: str = "") -> TaskRun:
        task = self._load(task_id)
        if task.state != PipelineState.FINAL_GATE_REQUIRED:
            raise StateConflictError(
                f"task is in state {task.state.value}; final approval requires "
                "FINAL_GATE_REQUIRED"
            )
        try:
            delta = self._require_task_delta(task)
        except BaselineError as exc:
            current = self._load(task_id)
            self._block(current, "baseline_error", str(exc))
            raise
        task.final_gate = FinalGateRecord(note=note.strip())
        preexisting: list[str] = []
        if task.baseline is not None:
            preexisting = (
                list(task.baseline.preexisting_dirty_files)
                + list(task.baseline.preexisting_untracked_files)
            )
        elif task.initial_snapshot is not None:
            preexisting = list(task.initial_snapshot.dirty_files)
        policy_notes = [
            f"[{v.id}] {v.type.value}: {v.description}"
            for v in task.policy_violations
        ]
        head_now = self.workspace.head_sha()
        # Transition FIRST so the persisted report reflects the task's real
        # final state (DONE) instead of the pre-approval state.
        self._move(task, PipelineState.DONE, note="final gate approved")
        self._persist(task)
        report = render_final_report(
            task,
            preexisting_changes=preexisting,
            task_changed_files=delta.changed_files,
            task_diff_stat_text=sanitize(delta.stat_text),
            head_now=head_now,
            note=note,
            policy_notes=policy_notes,
        )
        final_dir = self.store.final_dir(task.task_id)
        self.store.write_text(final_dir / "report.md", report)
        return task

    def unblock(
        self,
        task_id: str,
        reason: str,
        to: str | None = None,
        *,
        refresh_policy: bool = False,
    ) -> TaskRun:
        if not reason or not reason.strip():
            raise DevRelayError("unblock requires a non-empty --reason")
        task = self._load(task_id)
        if task.state not in (PipelineState.BLOCKED, PipelineState.FAILED):
            raise StateConflictError(
                f"task is in state {task.state.value}; unblock only applies "
                "to BLOCKED/FAILED tasks"
            )
        target = to
        if target is None:
            target = _UNBLOCK_DEFAULT_TARGET.get(task.blocked_code or "", "plan")
        if target not in _UNBLOCK_TARGETS:
            raise DevRelayError(
                f"unknown unblock target '{target}' (use one of "
                f"{sorted(_UNBLOCK_TARGETS)})"
            )
        # Explicit, audited policy refresh: the only supported way to change a
        # running task's budget/blocking policy (never implicit, never silent).
        if refresh_policy:
            self.refresh_task_policy(task_id, reason.strip())
            task = self._load(task_id)
        to_state = _UNBLOCK_TARGETS[target]
        self._move(task, to_state, note=f"manual unblock: {reason.strip()}")
        if to_state == PipelineState.FIX_REQUIRED:
            task.manual_override = True
        # A human explicitly acknowledged the interrupted attempt: clear the
        # crash markers so a new provider run is allowed (state/audit/evidence
        # for the old attempt are kept).
        marker_notes: list[str] = []
        if task.attempt_in_flight:
            task.attempt_in_flight = False
            marker_notes.append("interrupted provider attempt")
        if task.review_call_in_flight:
            task.review_call_in_flight = False
            marker_notes.append("interrupted reviewer attempt")
        closed = acknowledge_unfinished_attempts(task, note=reason.strip())
        if closed:
            marker_notes.append(
                "unfinished review round(s) "
                + ", ".join(f"#{attempt.review_number}" for attempt in closed)
            )
        if marker_notes:
            task.audit.append(
                TransitionEvent(
                    from_state=task.state.value,
                    to_state=task.state.value,
                    note=(
                        f"manual acknowledgement of {' and '.join(marker_notes)}: "
                        f"{reason.strip()}"
                    ),
                    by="human",
                )
            )
        task.blocked_code = None
        task.blocked_reason = None
        self._persist(task)
        return task

    # ------------------------------------------------------------------ #
    # CLI-facing task-relative diff helpers
    # ------------------------------------------------------------------ #
    def task_diff_text(self, task_id: str, *, stat: bool = False) -> str:
        task = self._load(task_id)
        delta = self._require_task_delta(task)
        return delta.stat_text if stat else delta.text_diff

    def task_binary_diff(self, task_id: str) -> str:
        task = self._load(task_id)
        if task.baseline is None:
            raise BaselineUnavailableError(
                f"task {task_id} has no task baseline (legacy task); "
                "binary task diffs are unavailable"
            )
        return self._baseline_service().binary_task_diff(task)

    # ------------------------------------------------------------------ #
    # status / diagnostics
    # ------------------------------------------------------------------ #
    def status_block(self, task_id: str) -> dict[str, str]:
        task = self._load(task_id)
        state = task.state
        state_name = state.value
        planner = "DONE" if task.plan_ready else "WAITING"
        implementer = (
            "RUNNING"
            if state in (PipelineState.IMPLEMENTING, PipelineState.FIXING)
            else ("DONE" if task.implementation_passes > 0 else "WAITING")
        )
        tests = (
            "RUNNING"
            if state == PipelineState.TESTING
            else (
                "PASS"
                if task.last_tests_passed is True
                else "FAIL" if task.last_tests_passed is False else "WAITING"
            )
        )
        reviewer = (
            "RUNNING"
            if state == PipelineState.REVIEWING and self.reviewer.automatic
            else (
                "WAITING"
                if state == PipelineState.REVIEWING
                else "DONE" if task.review_history else "PENDING"
            )
        )
        gate = (
            "APPROVED"
            if task.final_gate is not None
            else "DONE"
            if state == PipelineState.DONE
            else "PENDING"
        )
        policy_config = self._task_config(task)
        budget = ProviderBudget(policy_config.budget)
        usage = budget.usage(task)
        budget_one_line = (
            f"implementer {usage.implementer_calls}/{policy_config.budget.max_implementer_calls}"
            f", reviewer {usage.reviewer_calls}/{policy_config.budget.max_reviewer_calls}"
            f", total {usage.total_calls}/{policy_config.budget.max_total_provider_calls}"
        )
        if last_attempt := (task.review_attempts[-1] if task.review_attempts else None):
            review_one_line = (
                f"#{last_attempt.review_number} {last_attempt.status.value}"
                f" via {last_attempt.provider_name}"
                + (f" ({last_attempt.model})" if last_attempt.model else "")
                + f", calls {last_attempt.external_calls_consumed}"
                + (
                    f", decision {last_attempt.result.decision.value}"
                    if last_attempt.result
                    else ""
                )
            )
        else:
            review_one_line = "-"
        return {
            "task_id": task.task_id,
            "title": task.title,
            "state": state_name,
            "iteration": str(max(1, task.fix_iterations_used + 1)),
            "planner": planner,
            "implementer": implementer,
            "tests": tests,
            "reviewer": reviewer,
            "final_gate": gate,
            "baseline": (
                "OK"
                if task.baseline and task.baseline.baseline_complete
                else "NONE (legacy task)"
            ),
            "attempt": (
                task.attempts[-1].status.value if task.attempts else "-"
            )
            + (" (IN FLIGHT)" if task.attempt_in_flight else ""),
            "budget": budget_one_line,
            "review": review_one_line,
            "policy_source": task.policy_source or "snapshot",
            "blocked": task.blocked_code or "",
        }

    def usage_block(self, task_id: str) -> dict[str, object]:
        """Read-only provider usage/audit summary for `devrelay usage`."""
        task = self._load(task_id)
        policy_config = self._task_config(task)
        budget = ProviderBudget(policy_config.budget)
        usage = budget.usage(task)
        last_attempt = task.review_attempts[-1] if task.review_attempts else None
        return {
            "task_id": task.task_id,
            "state": task.state.value,
            "implementer_calls": usage.implementer_calls,
            "reviewer_calls": usage.reviewer_calls,
            "total_calls": usage.total_calls,
            "max_implementer_calls": policy_config.budget.max_implementer_calls,
            "max_reviewer_calls": policy_config.budget.max_reviewer_calls,
            "max_total_provider_calls": policy_config.budget.max_total_provider_calls,
            "reviewer_provider": self.reviewer.name,
            "reviewer_model": self.reviewer.model or "-",
            "reviewer_endpoint_host": self.reviewer.endpoint_host or "-",
            "provider_calls": [
                {
                    "call_id": record.call_id,
                    "kind": record.provider_kind.value,
                    "phase": record.phase.value,
                    "success": record.success,
                    "external_calls": record.external_call_count,
                    "error_type": record.error_type.value if record.error_type else None,
                    "model": record.model,
                    "endpoint_host": record.endpoint_host,
                    "duration_seconds": record.duration_seconds,
                }
                for record in task.provider_calls
            ],
            "review_attempts": [
                {
                    "review_number": attempt.review_number,
                    "provider": attempt.provider_name,
                    "status": attempt.status.value,
                    "transport_attempts": attempt.transport_attempts,
                    "format_attempts": attempt.format_attempts,
                    "external_calls": attempt.external_calls_consumed,
                    "model": attempt.model,
                    "endpoint_host": attempt.endpoint_host,
                    "error_type": attempt.error_type.value if attempt.error_type else None,
                    "result": attempt.result.decision.value if attempt.result else None,
                }
                for attempt in task.review_attempts
            ],
            "last_review_attempt": (
                last_attempt.status.value if last_attempt is not None else "-"
            ),
            "policy_source": task.policy_source or "snapshot",
            "blocked_code": task.blocked_code,
            "attempt_in_flight": task.attempt_in_flight,
            "review_call_in_flight": task.review_call_in_flight,
        }


def _json_pretty(obj) -> str:
    import json

    return json.dumps(obj.model_dump(mode="json"), indent=2, ensure_ascii=False)


def record_duration(record: ProviderAttempt) -> float:
    """Seconds between attempt start and now (best-effort, never negative)."""
    from datetime import datetime, timezone

    try:
        started = datetime.fromisoformat(record.started_at)
    except ValueError:  # pragma: no cover - defensive
        return 0.0
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    return max(0.0, round((datetime.now(timezone.utc) - started).total_seconds(), 3))
