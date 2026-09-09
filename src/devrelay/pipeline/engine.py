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
    starter_task_markdown,
)
from devrelay.artifacts.store import ArtifactStore
from devrelay.config import DevRelayConfig, dump_config_yaml
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
    Finding,
    FinalGateRecord,
    PolicyViolation,
    ProviderExecutionResult,
    RepoSnapshot,
    ReviewDecision,
    ReviewResult,
    TaskDelta,
    TaskPacket,
    TaskRun,
    TransitionEvent,
    WorkspaceSnapshot,
    utcnow_iso,
)
from devrelay.pipeline.policy import PipelinePolicy
from devrelay.pipeline.states import PipelineState, transition
from devrelay.providers.base import (
    ImplementerContext,
    ImplementerProvider,
    ReviewerProvider,
)
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
    "baseline_error": "plan",
    "internal": "plan",
}

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

    def _policy_guard_after_run(
        self,
        task: TaskRun,
        attempt: int,
        pre: RepoSnapshot,
        events: list[str],
    ) -> bool:
        """Post-run repository policy verification. Returns True when the
        pipeline must stop (task already moved to BLOCKED)."""
        service = self._baseline_service()
        try:
            post = service.post_snapshot()
            violations = service.check_policy(pre, post)
        except BaselineError as exc:
            current = self._load(task.task_id)
            self._block(
                current,
                "policy_guard_error",
                f"post-run repository verification failed: {exc}",
            )
            events.append(
                f"[{task.task_id}] BLOCKED: policy guard could not verify "
                "repository state"
            )
            return True
        if not violations:
            return False
        self._persist_policy_run(task.task_id, attempt, pre, post, violations)
        current = self._load(task.task_id)
        self._record_policy_violations(current, violations, attempt)
        first = violations[0]
        self._block(
            current,
            "policy_violation",
            f"[{first.type.value}] {first.description} "
            "(policy/violations-*.json has full details)",
        )
        events.append(
            f"[{task.task_id}] BLOCKED: policy violation "
            f"{first.type.value} ({len(violations)} violation(s))"
        )
        return True

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
        max_steps = 10 + self.policy.max_fix_iterations * 4
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
        """Runs the implementer once. True = success and now TESTING."""
        packet = task.packet
        if packet is None:
            raise StateConflictError(
                f"task {task.task_id} has no Task Packet; import a plan first"
            )
        if task.state == PipelineState.PLAN_READY:
            self._move(task, PipelineState.IMPLEMENTING, note="implementation start")
        elif task.state == PipelineState.FIX_REQUIRED:
            if not self.policy.can_fix_again(task):
                self._block(
                    task,
                    "max_iterations",
                    "blocking findings remain and max_fix_iterations "
                    f"({self.policy.max_fix_iterations}) is exhausted; "
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
        is_fix = task.fix_iterations_used > 0 or bool(task.current_findings)
        context = ImplementerContext(
            task_id=task.task_id,
            packet=packet,
            attempt=attempt,
            workspace_root=str(self.workspace.root),
            is_fix=is_fix,
            findings=list(task.current_findings),
            reuse_approved_scope=self.config.scope.reuse_approved_scope,
            current_delta_first=self.config.scope.current_delta_first,
        )
        self._persist(task)
        events.append(
            f"[{task.task_id}] implementing (attempt {attempt}, "
            f"{'fix' if is_fix else 'initial'} pass)"
        )
        service = self._baseline_service()
        try:
            pre_snapshot = service.pre_snapshot()
        except BaselineError as exc:
            current = self._load(task.task_id)
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
        result: ProviderExecutionResult = self.implementer.run(context)

        log_dir = self.store.logs_dir(task.task_id)
        stdout_file = self.store.write_text(
            log_dir / f"codex-{attempt:02d}.stdout.log",
            sanitize(truncate(result.stdout or "", _MAX_LOG_CHARS)),
        )
        stderr_file = self.store.write_text(
            log_dir / f"codex-{attempt:02d}.stderr.log",
            sanitize(truncate(result.stderr or "", _MAX_LOG_CHARS)),
        )
        events.append(
            f"[{task.task_id}] implementer logs: "
            f"{self.store.rel_path(stdout_file)}, {self.store.rel_path(stderr_file)}"
        )

        provider_ran = not (result.error and result.exit_code is None)
        if provider_ran:
            if self._policy_guard_after_run(task, attempt, pre_snapshot, events):
                return False

        if result.error and result.exit_code is None:
            # Provider unavailable (e.g. Codex CLI missing): no state change,
            # clear diagnostic, task stays IMPLEMENTING/FIXING for retry.
            events.append(f"[{task.task_id}] ERROR: {result.error}")
            return False
        if not result.success:
            reason = (
                f"implementer exit={result.exit_code}"
                + (f" timed_out={result.timed_out}" if result.timed_out else "")
                + f" stderr={result.stderr.strip()[:1000]}"
            )
            task = self._load(task.task_id)
            self._hard_fail(task, "implementer_failed", reason)
            events.append(f"[{task.task_id}] FAILED: {reason}")
            return False

        task = self._load(task.task_id)
        task.implementation_passes += 1
        summary_body = sanitize(result.report or result.stdout or "")
        summary = (
            f"# Implementation report — attempt {attempt}\n\n"
            f"Generated at {utcnow_iso()} by provider '{self.implementer.name}'.\n\n"
            f"{truncate(summary_body, 200_000)}\n"
        )
        impl_dir = self.store.implementation_dir(task.task_id)
        impl_file = self.store.write_text(
            impl_dir / f"iteration-{attempt:02d}.md", summary
        )
        rel = self.store.rel_path(impl_file)
        if rel not in task.implementation_report_paths:
            task.implementation_report_paths.append(rel)
        self._move(
            task,
            PipelineState.TESTING,
            note=f"implementation attempt {attempt} succeeded",
        )
        self._persist(task)
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
        command_lines = list(self.config.tests.targeted)
        if (
            task.packet
            and self.policy.run_full_regression(task.packet.risk_level)
            and self.config.tests.full
        ):
            command_lines += [f"[full] {cmd}" for cmd in self.config.tests.full]
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
                timeout_seconds=self.config.tests.timeout_seconds,
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
            if self.config.pipeline.auto_fix_tests and self.policy.can_fix_again(task):
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
        delta = self._require_task_delta(task)
        diff = delta.text_diff
        diff_limit = self.config.review.max_diff_bytes
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
        try:
            review = self.reviewer.review(bundle)
        except ReviewFormatError as exc:
            self._block(
                task,
                "review_format",
                f"reviewer output could not be validated: {exc}",
            )
            events.append(
                f"[{task.task_id}] BLOCKED: invalid reviewer JSON "
                "(see state.json blocked_reason)"
            )
            return False
        except ProviderError as exc:
            self._block(task, "review_provider", str(exc))
            events.append(f"[{task.task_id}] BLOCKED: review provider error")
            return False
        return self._apply_review(task, review, events)

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
        """Persists the review and applies the policy decision."""
        review = self._normalize_review(task.task_id, review)
        review_number = len(task.review_history) + 1
        reviews_dir = self.store.reviews_dir(task.task_id)
        result_file = self.store.write_text(
            reviews_dir / f"review-{review_number:02d}-result.json",
            _json_pretty(review),
        )
        task.review_history.append(review)
        task.last_review = review
        blocking = self.policy.blocking_findings(review)
        task.current_findings = blocking
        task.open_p3 = self.policy.non_blocking_findings(review)
        self._persist(task)
        events.append(
            f"[{task.task_id}] review #{review_number} stored: "
            f"{self.store.rel_path(result_file)}"
        )

        decision, _ = self.policy.effective_decision(review)
        if decision == ReviewDecision.BLOCKED:
            self._block(
                task,
                "reviewer_blocked",
                review.summary or "reviewer returned decision=BLOCKED",
            )
            events.append(f"[{task.task_id}] BLOCKED: reviewer decision=BLOCKED")
            return False
        if decision == ReviewDecision.REQUEST_CHANGES:
            if not self.policy.can_fix_again(task):
                self._block(
                    task,
                    "max_iterations",
                    f"blocking findings remain after "
                    f"{self.policy.max_fix_iterations} fix iteration(s); "
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
        report = render_final_report(
            task,
            preexisting_changes=preexisting,
            task_changed_files=delta.changed_files,
            task_diff_stat_text=delta.stat_text,
            head_now=self.workspace.head_sha(),
            note=note,
            policy_notes=policy_notes,
        )
        final_dir = self.store.final_dir(task.task_id)
        self.store.write_text(final_dir / "report.md", report)
        self._move(task, PipelineState.DONE, note="final gate approved")
        self._persist(task)
        return task

    def unblock(
        self, task_id: str, reason: str, to: str | None = None
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
        to_state = _UNBLOCK_TARGETS[target]
        self._move(task, to_state, note=f"manual unblock: {reason.strip()}")
        if to_state == PipelineState.FIX_REQUIRED:
            task.manual_override = True
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
            "blocked": task.blocked_code or "",
        }


def _json_pretty(obj) -> str:
    import json

    return json.dumps(obj.model_dump(mode="json"), indent=2, ensure_ascii=False)
