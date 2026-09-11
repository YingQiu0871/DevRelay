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
from dataclasses import dataclass
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
from devrelay.artifacts.store import ArtifactStore, sha256_hex
from devrelay.config import (
    ConfigError,
    DevRelayConfig,
    FrozenBudget,
    PolicyDocument,
    ResolvedPolicy,
    WiringConfig,
    dump_policy_yaml,
    load_policy_snapshot,
)
from devrelay.errors import (
    BaselineError,
    BaselineUnavailableError,
    DevRelayError,
    PolicyLiveResolutionFailedError,
    PolicyLiveResolutionRequiredError,
    PolicyRefreshNotAllowedError,
    ProviderError,
    ReviewFormatError,
    StateConflictError,
    WorkspaceError,
)
from devrelay.models import (
    AppliedReviewRecord,
    ProfileRef,
    AttemptStatus,
    CallErrorType,
    Finding,
    FinalGateRecord,
    IndexSnapshotStatus,
    PolicyProvenance,
    PolicyRefreshRecord,
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
from devrelay.snapshot import (
    SnapshotCheck,
    SnapshotState,
    build_provenance,
    check_snapshot,
    classify_snapshot_state,
    freeze_policy,
    read_snapshot_document,
    snapshot_error,
    snapshot_path as snapshot_path_in_store,
)
from devrelay.pipeline.policy import PipelinePolicy
from devrelay.pipeline.review_lifecycle import (
    APPLICATION_APPLIED,
    APPLICATION_FINISH_ONLY,
    APPLICATION_NOT_APPLIED,
    ReviewSession,
    acknowledge_unfinished_attempts,
    mark_findings,
    pending_result_attempt,
    review_application_state,
    review_result_hash,
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


def _rel_posix(path: str) -> str:
    """Persist workspace-relative paths with forward slashes (portable state)."""
    return str(path).replace("\\", "/")


@dataclass(frozen=True)
class PolicyRecoveryGrant:
    """Human authorization for the explicit policy-recovery path.

    Only ``devrelay unblock --refresh-policy`` constructs one; the engine never
    fabricates a grant, so a damaged snapshot can never be repaired implicitly.
    """

    reason: str = "policy integrity recovery"
    by: str = "human"


@dataclass(frozen=True)
class PolicyReadout:
    """State-only view of a task's policy for ``status``/``usage``.

    Reading these commands never touches a live profile file: the document comes
    from the task's own snapshot (integrity-checked) or from recorded
    provenance, and a missing/corrupt snapshot degrades to a labelled
    ``None`` document rather than an error.
    """

    source: str
    document: PolicyDocument | None
    integrity: str = ""
    detail: str = ""
    profiles: tuple[ProfileRef, ...] = ()

    @property
    def display(self) -> str:
        if self.integrity == "verified":
            return "snapshot (verified)"
        if self.integrity == "unverified_legacy_no_digest":
            return "snapshot (legacy: digest not recorded)"
        if self.integrity == "not_frozen":
            return "live-fallback (not frozen)"
        if self.source == "snapshot":
            return f"snapshot (UNVERIFIED: {self.integrity})"
        return f"{self.source} ({self.integrity or 'unrecorded'})"


@dataclass(frozen=True)
class _ReviewOutcome:
    """Terminal outcome of applying one review result (pure decision result)."""

    state: str                                  # resulting task state name
    decision: str = ""                          # policy-effective decision
    target: PipelineState | None = None         # state to move to (if any)
    blocked_code: str | None = None
    reason: str = ""
    again: bool | None = None                   # True = keep advancing (fix)

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
        config: DevRelayConfig | None,
        store: ArtifactStore,
        workspace,
        implementer: ImplementerProvider,
        reviewer: ReviewerProvider,
        runner=None,
        baselines=None,
        *,
        runtime_config: WiringConfig | None = None,
        fallback_policy_config: ResolvedPolicy | None = None,
        policy_recovery=None,
        policy_view_provider=None,
    ) -> None:
        if config is None and runtime_config is None:
            raise DevRelayError(
                "engine needs either a workspace config or a runtime wiring config"
            )
        self.config = config
        self.runtime_config = runtime_config or WiringConfig.from_workspace_config(
            config  # type: ignore[arg-type]
        )
        self._fallback_policy_config = fallback_policy_config
        self.policy_recovery = policy_recovery
        # Lazily supplies the live workspace policy for *display* of legacy
        # tasks only; read-only commands never resolve profiles for a task that
        # owns a frozen snapshot.
        self._policy_view_provider = policy_view_provider
        self.store = store
        self.workspace = workspace
        self.implementer = implementer
        self.reviewer = reviewer
        self.runner = runner
        self.baselines = baselines

    def _fallback_policy(self) -> ResolvedPolicy:
        """Explicit live policy, used only where the design allows it.

        Either the caller supplied a resolved policy (CLI: profiles included) or
        it is derived from the live workspace document.  It is never consulted
        for a task whose frozen snapshot exists but cannot be used.
        """
        if self._fallback_policy_config is not None:
            return self._fallback_policy_config
        if self.config is None:
            raise PolicyLiveResolutionRequiredError(
                "no live policy is available in this command context and the task "
                "has no usable frozen policy"
            )
        return ResolvedPolicy.from_workspace_config(self.config)

    def _baseline_service(self):
        if self.baselines is None:
            raise DevRelayError(
                "engine was constructed without a baseline service; "
                "task baselines are mandatory in v0.1-RC"
            )
        return self.baselines

    # ------------------------------------------------------------------ #
    # task-scoped policy (v0.2-B: frozen snapshot or explicit live policy)
    # ------------------------------------------------------------------ #
    def snapshot_path(self, task_id: str) -> Path:
        return snapshot_path_in_store(self.store, task_id)

    def snapshot_check(self, task: TaskRun) -> SnapshotCheck:
        """Read-only classification of the task's frozen policy snapshot."""
        return check_snapshot(self.store, task)

    def _resolve_task_policy(self, task: TaskRun) -> ResolvedPolicy:
        """The task's effective policy - the single policy entry point.

        * ``valid``       -> the frozen snapshot (the only policy authority)
        * ``legacy_live`` -> the explicit live policy supplied by the caller
        * anything else   -> fail closed; runtime wiring/workspace defaults are
          never substituted for a snapshot that once governed the task.
        """
        check = self.snapshot_check(task)
        if check.state is SnapshotState.VALID:
            document, dropped, digest = read_snapshot_document(self.store, task)
            provenance = (
                task.policy_provenance
                or build_provenance(
                    generation=1, integrity="unverified_legacy_tolerant"
                )
            ).model_copy(
                update={"snapshot_sha256": digest, "dropped_legacy_keys": dropped}
            )
            return ResolvedPolicy(
                document=document, provenance=provenance, source="snapshot"
            )
        if check.state is SnapshotState.LEGACY_LIVE:
            return self._fallback_policy()
        if self.policy_recovery is not None:
            return self._recover_task_policy(task, check)
        raise snapshot_error(check)

    def read_recorded_policy(self, task: TaskRun) -> PolicyReadout:
        """Policy view for ``status``/``usage`` that never touches profiles."""
        check = self.snapshot_check(task)
        source = self.policy_source_for(task)
        recorded = task.policy_provenance
        profiles = tuple(recorded.profiles) if recorded is not None else ()
        if check.state is SnapshotState.VALID:
            try:
                document, _dropped, _digest = read_snapshot_document(self.store, task)
            except DevRelayError as exc:  # pragma: no cover - racing writer
                return PolicyReadout(
                    source=source,
                    document=None,
                    integrity="invalid",
                    detail=str(exc),
                    profiles=profiles,
                )
            integrity = (
                "verified"
                if getattr(task, "policy_config_sha256", "")
                else "unverified_legacy_no_digest"
            )
            return PolicyReadout(
                source=source,
                document=document,
                integrity=integrity,
                profiles=profiles,
            )
        if check.state is SnapshotState.LEGACY_LIVE:
            return PolicyReadout(
                source=source,
                document=self._legacy_display_policy(),
                integrity="not_frozen",
                detail=check.detail,
                profiles=profiles,
            )
        return PolicyReadout(
            source=source,
            document=None,
            integrity=check.state.value,
            detail=check.detail,
            profiles=profiles,
        )

    def _legacy_display_policy(self) -> PolicyDocument | None:
        """Live workspace policy for *display* of a legacy task, best effort.

        Legacy tasks have no frozen policy, so showing the live budget is the
        v0.2-A contract.  This never runs for a task with a usable snapshot and
        never fails a read-only command.
        """
        if self.config is not None:
            return PolicyDocument.from_workspace_config(self.config)
        if self._policy_view_provider is None:
            return None
        try:
            return self._policy_view_provider()
        except Exception:  # pragma: no cover - display only
            return None

    def policy_source_for(self, task: TaskRun) -> str:
        """Recorded policy source for display (never writes to the task)."""
        if task.policy_source in ("snapshot", "live-fallback"):
            return task.policy_source
        state, _detail = classify_snapshot_state(task, self.store)
        return "snapshot" if state is SnapshotState.VALID else "live-fallback"

    def _task_config(self, task: TaskRun) -> PolicyDocument:
        """Deprecated v0.2-A name; now returns the task's **PolicyDocument**.

        Kept because v0.2-A tests read ``engine._task_config(task).budget``.  It
        no longer mutates task state and no longer returns a workspace config.
        """
        return self._resolve_task_policy(task).document

    def task_policy_snapshot_text(self, task_id: str) -> str | None:
        snapshot = self.snapshot_path(task_id)
        return snapshot.read_text(encoding="utf-8") if snapshot.is_file() else None

    def refresh_task_policy(
        self,
        task_id: str,
        reason: str,
        *,
        by: str = "human",
        force: bool = False,
        recovery: bool = False,
    ) -> TaskRun:
        """Explicitly re-freeze the live policy as this task's policy.

        The only supported way to change a running task's policy, and the only
        recovery for a missing/invalid/hash-mismatched snapshot.  Live policy is
        resolved *before* anything is mutated; previous snapshot bytes are
        preserved only when they are actually readable (never invented), and
        usage counters, call identities, attempts and review history are never
        touched.
        """
        task = self._load(task_id)
        check = self.snapshot_check(task)
        # Repairing a snapshot that is not valid IS an integrity recovery, no
        # matter which entry point (unblock --refresh-policy or the execution
        # grant) asked for it: the record must say so.
        recovery = recovery or check.state is not SnapshotState.VALID
        # 1) Resolve the live policy first: a resolution failure mutates nothing.
        try:
            live = self._fallback_policy()
        except DevRelayError as exc:
            raise PolicyLiveResolutionFailedError(
                f"cannot refresh the policy of {task_id}: live policy resolution "
                f"failed: {exc}"
            ) from exc
        document = live.document
        after_text = dump_policy_yaml(document)

        policy_dir = self.store.policy_dir(task_id)
        index = len(task.policy_refreshes) + 1
        refresh_id = f"{task_id}-P{index:04d}"
        before_path = policy_dir / f"policy-refresh-{index:02d}-before.yaml"
        after_path = policy_dir / f"policy-refresh-{index:02d}-after.yaml"
        record_path = policy_dir / f"policy-refresh-{index:02d}.json"

        # 2) Preserve the previous snapshot only if its bytes are readable.
        before_bytes: bytes | None = None
        if check.path is not None and check.path.is_file():
            try:
                before_bytes = check.path.read_bytes()
            except OSError:
                before_bytes = None
        before_available = before_bytes is not None
        before_sha = sha256_hex(before_bytes) if before_bytes is not None else ""
        if before_available:
            self.store.write_bytes(before_path, before_bytes)
        self.store.write_text(after_path, after_text)
        after_sha = sha256_hex(after_text.encode("utf-8"))

        # 3) New frozen-policy generation (evidence generation, not a change
        #    counter: an explicit refresh always increments it).
        previous_generation = int(
            getattr(task.policy_provenance, "generation", 0) or 0
        )
        generation = previous_generation + 1
        provenance = build_provenance(
            generation=generation,
            selector_raw=list(live.provenance.selector_raw),
            profiles=list(live.provenance.profiles),
            workspace_config_sha256=live.provenance.workspace_config_sha256,
            integrity="sha256_verified",
        )
        digest, provenance = freeze_policy(
            self.store, task_id, document, provenance
        )

        record = PolicyRefreshRecord(
            refresh_id=refresh_id,
            by=by,
            reason=reason,
            before_source="snapshot" if before_available else "",
            after_source="snapshot",
            before_config_sha256=before_sha,
            after_config_sha256=after_sha,
            before_path=(
                self.store.rel_path(before_path) if before_available else ""
            ),
            after_path=self.store.rel_path(after_path),
            record_path=self.store.rel_path(record_path),
            generation=generation,
            after_generation=generation,
            trigger="integrity_recovery" if recovery else "explicit_refresh",
            before_state=check.state.value,
            before_snapshot_available=before_available,
            before_sha256=before_sha,
            after_sha256=after_sha,
            usage_unchanged=True,
        )
        self.store.write_text(record_path, _json_pretty(record))

        task.policy_refreshes.append(record)
        task.policy_source = "snapshot"
        task.policy_snapshot_path = _rel_posix(
            self.store.rel_path(self.snapshot_path(task_id))
        )
        task.policy_config_sha256 = digest
        task.policy_provenance = provenance
        task.audit.append(
            TransitionEvent(
                from_state=task.state.value,
                to_state=task.state.value,
                note=(
                    f"policy snapshot refreshed from workspace config: {reason} "
                    f"({refresh_id}; forced={str(bool(force)).lower()}; "
                    f"generation {generation}; trigger "
                    f"{record.trigger}; previous state "
                    f"{record.before_state}; before_snapshot_available="
                    f"{str(before_available).lower()}; before/after evidence under "
                    f"{self.store.rel_path(after_path)} and "
                    f"{self.store.rel_path(record_path)})"
                ),
                by=by,
            )
        )
        self._persist(task)
        return task

    def _recover_task_policy(self, task: TaskRun, check: SnapshotCheck) -> ResolvedPolicy:
        """Explicit recovery of a missing/invalid/mismatched snapshot."""
        grant = self.policy_recovery
        refreshed = self.refresh_task_policy(
            task.task_id,
            getattr(grant, "reason", "policy integrity recovery"),
            by=getattr(grant, "by", "human"),
            force=True,
            recovery=True,
        )
        return ResolvedPolicy(
            document=self._task_config(refreshed),
            provenance=refreshed.policy_provenance,
            source="snapshot",
        )

    def _policy_for(self, task: TaskRun) -> PipelinePolicy:
        return PipelinePolicy(self._resolve_task_policy(task).document)

    def _budget_for(self, task: TaskRun) -> ProviderBudget:
        limits = self._resolve_task_policy(task).document.budget
        if not isinstance(limits, FrozenBudget):  # pragma: no cover - guard
            raise DevRelayError(
                "internal: task budget did not come from a policy resolution"
            )
        return ProviderBudget(limits)

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

    def _set_blocked(self, task: TaskRun, code: str, reason: str) -> None:
        """Mutate a task into BLOCKED (caller decides when to persist).

        Kept separate from :meth:`_block` so a caller that must land several
        semantic changes in one atomic state write can do so.
        """
        task.blocked_code = code
        task.blocked_reason = sanitize(truncate(reason, 2000))
        if task.state != PipelineState.BLOCKED:
            self._move(task, PipelineState.BLOCKED, note=f"blocked: {code}")

    def _block(self, task: TaskRun, code: str, reason: str) -> None:
        self._set_blocked(task, code, reason)
        self._persist(task)

    def _record_provider_call(self, task_id: str, record: ProviderCallRecord) -> None:
        """Upsert an external-call record in task state + evidence artifact.

        The record is created (as intent) *before* the invocation with a durable
        ``call_id``; settling it rewrites only that same call's evidence file,
        never another call's.
        """
        task = self._load(task_id)
        for index, existing in enumerate(task.provider_calls):
            if existing.call_id == record.call_id:
                task.provider_calls[index] = record
                break
        else:
            task.provider_calls.append(record)
        self._persist(task)
        self.store.write_text(
            self.store.policy_dir(task_id) / "calls" / f"{record.call_id}.json",
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
        *,
        attempt_id: str | None = None,
    ) -> None:
        policy_dir = self.store.policy_dir(task_id)
        runs_dir = policy_dir / "runs"
        self.store.write_text(
            policy_dir / f"pre-run-{attempt:02d}.json", _json_pretty(pre)
        )
        self.store.write_text(
            policy_dir / f"post-run-{attempt:02d}.json", _json_pretty(post)
        )
        if attempt_id:
            # Immutable per-attempt evidence: a retry of the same logical pass
            # can rewrite the convenience files above but never these.
            self.store.write_text(
                runs_dir / f"{attempt_id}-pre.json", _json_pretty(pre)
            )
            self.store.write_text(
                runs_dir / f"{attempt_id}-post.json", _json_pretty(post)
            )
        if violations:
            payload = json.dumps(
                [v.model_dump(mode="json") for v in violations],
                indent=2,
                ensure_ascii=False,
            )
            self.store.write_text(
                policy_dir / f"violations-{attempt:02d}.json", payload
            )
            if attempt_id:
                self.store.write_text(
                    runs_dir / f"{attempt_id}-violations.json", payload
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
        """Upsert the attempt in task state + evidence artifacts.

        ``policy/attempt-NN.json`` stays the *latest* view of logical pass NN
        (v0.1 compatibility).  The immutable per-attempt copy is keyed by the
        durable attempt id, so a failed attempt's evidence survives the retry
        that reuses the same logical pass number.
        """
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
        self.store.write_text(
            policy_dir / "attempts" / f"{record.attempt_id}.json",
            _json_pretty(record),
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
        freeze = self._fallback_policy()
        try:
            digest, provenance = freeze_policy(
                self.store, task_id, freeze.document, freeze.provenance
            )
        except OSError:
            import shutil

            shutil.rmtree(task_dir, ignore_errors=True)
            raise
        # The snapshot *is* this task's policy from now on: persisted eagerly,
        # with the digest of its exact bytes and the provenance behind it.
        task.policy_snapshot_path = _rel_posix(
            self.store.rel_path(self.snapshot_path(task_id))
        )
        task.policy_config_sha256 = digest
        task.policy_provenance = provenance
        task.policy_source = "snapshot"
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
        # Durable attempt identity (never derived from success counters): a
        # failed attempt that is retried after an unblock gets a NEW identity,
        # so its evidence is never overwritten.
        attempt_id = task.allocate_attempt_id()
        record = ProviderAttempt(
            attempt_id=attempt_id,
            iteration=attempt,
            phase="FIX" if is_fix else "IMPLEMENT",
        )
        policy_doc = self._task_config(task)
        context = ImplementerContext(
            task_id=task.task_id,
            packet=packet,
            attempt=attempt,
            workspace_root=str(self.workspace.root),
            is_fix=is_fix,
            findings=list(task.current_findings),
            reuse_approved_scope=policy_doc.scope.reuse_approved_scope,
            current_delta_first=policy_doc.scope.current_delta_first,
        )

        # ---- budget gate: never invoke the implementer when it would exceed --
        budget = ProviderBudget(policy_doc.budget)
        try:
            budget.check(task, ProviderKind.IMPLEMENTER)
        except BudgetExhaustedError as exc:
            current = self._load(task.task_id)
            self._block(current, "provider_budget_exhausted", str(exc))
            events.append(f"[{task.task_id}] BLOCKED: {exc}")
            return False

        # ---- persist in-flight marker + call intent BEFORE the provider -----
        # The call identity is allocated and its intent recorded here, in one
        # atomic state write, so budget/evidence stay exact even if the process
        # dies between the allocation and the invocation.
        call_id = task.allocate_call_id()
        call_record = ProviderCallRecord(
            call_id=call_id,
            provider_kind=ProviderKind.IMPLEMENTER,
            provider_name=self.implementer.name,
            phase=(
                ProviderCallPhase.FIX if is_fix else ProviderCallPhase.IMPLEMENT
            ),
            attempt_number=attempt,
            task_iteration=attempt,
            started_at=utcnow_iso(),
            # Conservatively counted as attempted until the run proves the CLI
            # never started (unavailable CLI -> settled to 0).
            external_call_count=1,
            parent_attempt_id=attempt_id,
        )
        record.call_ids.append(call_id)
        task.attempt_in_flight = True
        self._write_attempt(task, record)
        self._record_provider_call(task.task_id, call_record)
        events.append(
            f"[{task.task_id}] implementing (attempt {attempt}, "
            f"{'fix' if is_fix else 'initial'} pass, {attempt_id}, {call_id})"
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
        call_record = call_record.model_copy(
            update={
                "completed_at": utcnow_iso(),
                "success": exception is None
                and not provider_unavailable
                and bool(result is not None and result.success),
                "duration_seconds": record_duration(record),
                # No external call happened when the CLI was unavailable.
                "external_call_count": 0 if provider_unavailable else 1,
                "error_type": call_error,
                "error": sanitize(call_error_text) if call_error_text else None,
            }
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
                task.task_id,
                attempt,
                pre_snapshot,
                post_snapshot,
                violations,
                attempt_id=attempt_id,
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
        stdout_payload = sanitize(truncate(stdout_text or "", _MAX_LOG_CHARS))
        stderr_payload = sanitize(truncate(stderr_text or "", _MAX_LOG_CHARS))
        # Immutable per-attempt logs (durable attempt id in the name).
        self.store.write_text(
            log_dir / f"{attempt_id}.stdout.log", stdout_payload
        )
        self.store.write_text(
            log_dir / f"{attempt_id}.stderr.log", stderr_payload
        )
        # Convenience aliases for the logical pass (latest attempt of pass NN).
        stdout_file = self.store.write_text(
            log_dir / f"codex-{attempt:02d}.stdout.log", stdout_payload
        )
        stderr_file = self.store.write_text(
            log_dir / f"codex-{attempt:02d}.stderr.log", stderr_payload
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
        policy_doc = self._task_config(task)
        policy = PipelinePolicy(policy_doc)
        command_lines = list(policy_doc.tests.targeted)
        if (
            task.packet
            and policy.run_full_regression(task.packet.risk_level)
            and policy_doc.tests.full
        ):
            command_lines += [f"[full] {cmd}" for cmd in policy_doc.tests.full]
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
                timeout_seconds=policy_doc.tests.timeout_seconds,
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
            if policy_doc.pipeline.auto_fix_tests and policy.can_fix_again(task):
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
        # Pure resolution: building a bundle must not rewrite task state.
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
        pipeline should keep moving automatically (auto reviewer, fix needed).

        Crash-window discipline (v0.2-A audit remediation):

        * KNOWN COMPLETED RESULT (schema-valid, sanitized, persisted) ->
          replay :meth:`_apply_review` locally, **zero** external calls.
        * UNCERTAIN EXTERNAL CALL (in-flight marker, or an attempt that never
          finalized) -> fail closed; never invent a result.
        """
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

        # ---- RESULT PERSISTED but not APPLIED: replay, never re-request -----
        recovery = self.recover_pending_review(task, events)
        if recovery is not None:
            return recovery

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

        policy_doc = self._task_config(task)
        budget = ProviderBudget(policy_doc.budget)
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
            format_retries=policy_doc.review.retries,
            transport_retries=policy_doc.review.transport_retries,
            max_response_chars=policy_doc.review.max_response_chars,
            timeout_seconds=policy_doc.review.timeout_seconds,
            sink=session,
        )
        try:
            # Normalize *before* the result is persisted on the attempt: the
            # stored identity must be exactly the identity that gets applied,
            # otherwise a restart replay could not recognise its own result.
            review = sanitize_review_result(
                self._normalize_review(
                    task.task_id, self.reviewer.review(bundle, call_policy=call_policy)
                )
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
        return self._apply_review(
            current, review, events, attempt_id=session.attempt.attempt_id
        )

    # ------------------------------------------------------------------ #
    # review result recovery (P1-01)
    # ------------------------------------------------------------------ #
    def recover_pending_review(
        self, task: TaskRun, events: list[str]
    ) -> bool | None:
        """Replay a persisted-but-unapplied review result, or return ``None``.

        ``None`` means "nothing to recover - continue with the normal flow".
        A non-``None`` return is the pipeline decision (True = keep advancing),
        produced with **zero** additional external calls.
        """
        pending = pending_result_attempt(task)
        if pending is not None and pending.result is not None:
            review = pending.result
            identity = review_result_hash(review)
            events.append(
                f"[{task.task_id}] recovering persisted review result from attempt "
                f"{pending.attempt_id} ({identity[:12]}): replaying locally with "
                "0 external calls"
            )
            return self._apply_review(
                task,
                review,
                events,
                attempt_id=pending.attempt_id,
                recovered=True,
            )
        # Applied result whose terminal transition never landed (crash between
        # the marker write and the state move): complete it locally - but only
        # when the task provably has not moved on since, otherwise a new review
        # round must proceed normally.
        for attempt in reversed(task.review_attempts):
            if attempt.result is None or not attempt.result_applied:
                continue
            marker = self._marker_for(task, attempt.result)
            if marker is None or not self._needs_application_completion(task, marker):
                break
            events.append(
                f"[{task.task_id}] review result of attempt {attempt.attempt_id} "
                "is already applied; completing the pending transition locally "
                "(0 external calls)"
            )
            return self._complete_pending_application(task, marker, events)
        return None

    def _confirm_applied(
        self,
        task: TaskRun,
        review: ReviewResult,
        attempt_id: str | None,
        events: list[str],
    ) -> bool:
        """No-op confirmation for a review whose application is already durable.

        Never touches history, seen counters or transitions: the recorded
        outcome is authoritative for the caller's control flow.
        """
        recorded_state = ""
        for marker in task.applied_reviews:
            if marker.identity == review_result_hash(review):
                recorded_state = marker.state
                break
        touched = False
        if attempt_id:
            for index, attempt in enumerate(task.review_attempts):
                if attempt.attempt_id == attempt_id and not attempt.result_applied:
                    task.review_attempts[index] = attempt.model_copy(
                        update={
                            "result_applied": True,
                            "applied_at": utcnow_iso(),
                            "applied_state": recorded_state or attempt.applied_state,
                        }
                    )
                    touched = True
                    break
        if not recorded_state and attempt_id:
            for attempt in task.review_attempts:
                if attempt.attempt_id == attempt_id and attempt.applied_state:
                    recorded_state = attempt.applied_state
                    break
        # A durable marker can survive a crash that happened before the state
        # transition was persisted: finish it locally - but only when the task
        # demonstrably has not moved on since (see _needs_application_completion).
        marker = self._marker_for(task, review)
        if marker is not None and self._needs_application_completion(task, marker):
            self._complete_pending_application(task, marker, events)
            touched = False  # the completion helper persisted already
        if touched:
            self._persist(task)
        events.append(
            f"[{task.task_id}] review application already durable "
            f"({recorded_state or 'unknown state'}); nothing reapplied"
        )
        return recorded_state == PipelineState.FIX_REQUIRED.value

    def _finish_applied_review(
        self,
        task: TaskRun,
        review: ReviewResult,
        events: list[str],
        *,
        attempt_id: str | None = None,
    ) -> bool:
        """Complete the bookkeeping of a review recorded before the marker era.

        Only reached for ``finish_only`` state (the unreleased ``fe4b044``
        candidate persisted history and the terminal state in two separate
        writes), so it never re-appends history and never re-bumps
        ``finding_seen_counts``.  The terminal state is re-derived from policy -
        deterministic at this point, therefore identical to what the original
        application computed.
        """
        policy = self._policy_for(task)
        review_number = self._review_number_of(task, review)
        decision, _ = policy.effective_decision(review)
        terminal = self._terminal_outcome(task, review, policy, decision)
        self._record_applied(
            task,
            review,
            terminal,
            review_number,
            attempt_id,
            events,
            review_file=str(
                self.store.rel_path(
                    self.store.reviews_dir(task.task_id)
                    / f"review-{review_number:02d}-result.json"
                )
            ),
        )
        self._apply_terminal(task, terminal)
        self._persist(task)
        events.append(
            f"[{task.task_id}] completed previously interrupted review "
            f"application (#{review_number}) -> {terminal.state}"
        )
        return terminal.again or False

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

    # ------------------------------------------------------------------ #
    # review application (idempotent, one atomic state write)
    # ------------------------------------------------------------------ #
    def _review_number_of(self, task: TaskRun, review: ReviewResult) -> int:
        """Round number of *review*: existing history entry, else the next one."""
        identity = review_result_hash(review)
        for index, stored in enumerate(task.review_history, start=1):
            if review_result_hash(stored) == identity:
                return index
        return len(task.review_history) + 1

    def _terminal_outcome(
        self,
        task: TaskRun,
        review: ReviewResult,
        policy: PipelinePolicy,
        decision: ReviewDecision,
    ) -> "_ReviewOutcome":
        """Pure decision -> terminal state mapping (no mutation, no I/O).

        Policy authority lives here: the reviewer's ``decision`` string is never
        the final authority, ``blocking_severities`` is.
        """
        if decision == ReviewDecision.BLOCKED:
            return _ReviewOutcome(
                state=PipelineState.BLOCKED.value,
                decision=decision.value,
                blocked_code="reviewer_blocked",
                reason=review.summary or "reviewer returned decision=BLOCKED",
                again=False,
            )
        if decision == ReviewDecision.REQUEST_CHANGES:
            stalled = stalled_findings(
                review, task, self._task_config(task).pipeline.max_same_finding_cycles
            )
            if stalled:
                first = stalled[0]
                return _ReviewOutcome(
                    state=PipelineState.BLOCKED.value,
                    decision=decision.value,
                    blocked_code="review_stalled",
                    reason=(
                        "the same blocking finding keeps returning "
                        f"(fingerprint {first.fingerprint}, seen "
                        f"{task.finding_seen_counts.get(first.fingerprint, 0)}x): "
                        f"[{first.severity.value}] {first.title}. DevRelay stopped "
                        "the loop instead of re-running the same fix until the "
                        "budget is gone; use 'devrelay unblock --reason \"...\"' if "
                        "another cycle is genuinely intended."
                    ),
                    again=False,
                )
            if not policy.can_fix_again(task):
                return _ReviewOutcome(
                    state=PipelineState.BLOCKED.value,
                    decision=decision.value,
                    blocked_code="max_iterations",
                    reason=(
                        "blocking findings remain after "
                        f"{policy.max_fix_iterations} fix iteration(s); "
                        "use 'devrelay unblock --to fix' for an explicit override"
                    ),
                    again=False,
                )
            return _ReviewOutcome(
                state=PipelineState.FIX_REQUIRED.value,
                decision=decision.value,
                target=PipelineState.FIX_REQUIRED,
                again=True,
            )
        return _ReviewOutcome(
            state=PipelineState.FINAL_GATE_REQUIRED.value,
            decision=decision.value,
            target=PipelineState.FINAL_GATE_REQUIRED,
            again=False,
        )

    def _apply_terminal(self, task: TaskRun, outcome: "_ReviewOutcome") -> None:
        """Mutate the task to its terminal outcome (caller persists exactly once)."""
        if outcome.target is not None:
            self._move(task, outcome.target, note="review applied")
            return
        self._set_blocked(task, outcome.blocked_code or "internal", outcome.reason)

    def _record_applied(
        self,
        task: TaskRun,
        review: ReviewResult,
        outcome: "_ReviewOutcome",
        review_number: int,
        attempt_id: str | None,
        events: list[str],
        *,
        review_file: str = "",
    ) -> None:
        """Add the durable application marker + attempt marker (in memory)."""
        identity = review_result_hash(review)
        if task.applied_review_identity(identity) is None:
            task.applied_reviews.append(
                AppliedReviewRecord(
                    identity=identity,
                    review_number=review_number,
                    attempt_id=attempt_id,
                    review_file=review_file,
                    decision=outcome.decision,
                    state=outcome.state,
                    findings=len(review.findings),
                    fix_iterations=task.fix_iterations_used,
                    implementation_passes=task.implementation_passes,
                )
            )
        if attempt_id:
            for index, attempt in enumerate(task.review_attempts):
                if attempt.attempt_id != attempt_id:
                    continue
                task.review_attempts[index] = attempt.model_copy(
                    update={
                        "result_applied": True,
                        "applied_at": utcnow_iso(),
                        "applied_state": outcome.state,
                    }
                )
                break

    def _marker_for(
        self, task: TaskRun, review: ReviewResult
    ) -> AppliedReviewRecord | None:
        identity = review_result_hash(review)
        for marker in task.applied_reviews:
            if marker.identity == identity:
                return marker
        return None

    @staticmethod
    def _needs_application_completion(
        task: TaskRun, marker: AppliedReviewRecord
    ) -> bool:
        """True when an applied review's terminal transition never landed.

        Requires *proof that nothing happened since*: the task is still in
        ``REVIEWING`` for the same round and at the same fix/implementation pass
        counters as when the review was applied.  A task that ran a fix pass and
        came back to ``REVIEWING`` therefore starts a normal new round instead of
        replaying the previous one.
        """
        if task.state != PipelineState.REVIEWING:
            return False
        if marker.state not in (
            PipelineState.FIX_REQUIRED.value,
            PipelineState.FINAL_GATE_REQUIRED.value,
            PipelineState.BLOCKED.value,
        ):
            return False
        return (
            task.fix_iterations_used == marker.fix_iterations
            and task.implementation_passes == marker.implementation_passes
            and len(task.review_history) == marker.review_number
        )

    def _complete_pending_application(
        self,
        task: TaskRun,
        marker: AppliedReviewRecord,
        events: list[str],
    ) -> bool:
        """Finish a terminal transition whose state write never happened."""
        if marker.state == PipelineState.FIX_REQUIRED.value:
            self._move(task, PipelineState.FIX_REQUIRED, note="resume: review applied")
            again = True
        elif marker.state == PipelineState.FINAL_GATE_REQUIRED.value:
            self._move(
                task, PipelineState.FINAL_GATE_REQUIRED, note="resume: review applied"
            )
            again = False
        else:
            self._set_blocked(
                task, "reviewer_blocked", "resumed from an applied review result"
            )
            again = False
        if marker.attempt_id:
            for index, attempt in enumerate(task.review_attempts):
                if attempt.attempt_id == marker.attempt_id:
                    task.review_attempts[index] = attempt.model_copy(
                        update={
                            "result_applied": True,
                            "applied_at": attempt.applied_at or utcnow_iso(),
                            "applied_state": marker.state,
                        }
                    )
                    break
        self._persist(task)
        events.append(
            f"[{task.task_id}] completed the pending review application "
            f"(#{marker.review_number}) -> {marker.state} with 0 external calls"
        )
        return again

    def _apply_review(
        self,
        task: TaskRun,
        review: ReviewResult,
        events: list[str],
        *,
        attempt_id: str | None = None,
        recovered: bool = False,
    ) -> bool:
        """Persists the review and applies the policy decision - exactly once.

        Idempotency contract (v0.2-A audit remediation): the whole semantic
        application (history append, seen counters, findings, applied marker,
        terminal state) lands in **one** atomic ``state.json`` write, so a crash
        either happens before it (nothing applied -> the persisted result is
        replayed from ``ReviewAttempt.result``) or after it (identity match ->
        no-op). Replays never duplicate history, counters, transitions or audit
        events, and never cost an external call.

        The reviewer's ``decision`` string is never the final authority: the
        task policy (``blocking_severities``) decides FIX vs PASS.
        """
        policy = self._policy_for(task)
        # A reviewer may echo secrets from the diff; persist only sanitized text.
        # Normalization is idempotent and happens BEFORE the result is stored on
        # the attempt, so the persisted identity is the applied identity.
        review = sanitize_review_result(self._normalize_review(task.task_id, review))
        identity = review_result_hash(review)
        state = review_application_state(task, review, attempt_id)

        if state != APPLICATION_NOT_APPLIED:
            events.append(
                f"[{task.task_id}] review result {identity[:12]} was already "
                f"applied ({state}); no duplicate history/counters "
                "(0 external calls)"
            )
            if state == APPLICATION_APPLIED:
                return self._confirm_applied(task, review, attempt_id, events)
            return self._finish_applied_review(
                task, review, events, attempt_id=attempt_id
            )

        review = mark_findings(review, task)  # fingerprints + seen counters
        review_number = len(task.review_history) + 1
        reviews_dir = self.store.reviews_dir(task.task_id)
        result_file = self.store.write_text(
            reviews_dir / f"review-{review_number:02d}-result.json",
            _json_pretty(review),
        )
        rel_file = self.store.rel_path(result_file)

        decision, _ = policy.effective_decision(review)
        outcome = self._terminal_outcome(task, review, policy, decision)

        # ---- single semantic mutation batch ---------------------------------
        task.review_history.append(review)
        task.last_review = review
        task.current_findings = policy.blocking_findings(review)
        task.open_p3 = policy.non_blocking_findings(review)
        self._record_applied(
            task,
            review,
            outcome,
            review_number,
            attempt_id,
            events,
            review_file=rel_file,
        )
        self._apply_terminal(task, outcome)
        self._persist(task)  # atomic: history + counters + marker + state
        # ---------------------------------------------------------------------

        events.append(
            f"[{task.task_id}] review #{review_number} stored: {rel_file}"
            + (" (recovered from persisted result)" if recovered else "")
        )
        if outcome.blocked_code == "reviewer_blocked":
            events.append(f"[{task.task_id}] BLOCKED: reviewer decision=BLOCKED")
        elif outcome.blocked_code == "review_stalled":
            first = policy.blocking_findings(review)[0]
            events.append(
                f"[{task.task_id}] BLOCKED: review stalled on a repeated "
                f"finding ({first.severity.value}: {first.title})"
            )
        elif outcome.blocked_code == "max_iterations":
            events.append(f"[{task.task_id}] BLOCKED: max fix iterations reached")
        elif outcome.target is PipelineState.FIX_REQUIRED:
            events.append(
                f"[{task.task_id}] review found "
                f"{len(task.current_findings)} blocking finding(s) -> FIX_REQUIRED"
            )
        else:
            events.append(f"[{task.task_id}] review passed -> FINAL_GATE_REQUIRED")
        return outcome.again

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
        # Normalize/sanitize first so the persisted attempt result carries the
        # same identity that will be applied (replayable, idempotent).
        review = sanitize_review_result(self._normalize_review(task.task_id, review))
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
        self._apply_review(
            task, review, events, attempt_id=session.attempt.attempt_id
        )
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
        force: bool = False,
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
            self.refresh_task_policy(task_id, reason.strip(), force=force)
            task = self._load(task_id)
        to_state = _UNBLOCK_TARGETS[target]
        self._move(task, to_state, note=f"manual unblock: {reason.strip()}")
        if to_state == PipelineState.FIX_REQUIRED:
            task.manual_override = True
        # A human explicitly acknowledged the interrupted attempt: clear the
        # crash markers so a new provider run is allowed.  Everything else -
        # state/audit, provider calls, review attempts, policy refreshes - is
        # kept; unblock never deletes evidence.
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
        # AUD-09 stays open as a structural backlog item (blocked_reason is still
        # cleared), but the cleared block is preserved here verbatim so the
        # information survives in the audit trail.
        cleared = task.blocked_code
        if cleared or task.blocked_reason:
            task.audit.append(
                TransitionEvent(
                    from_state=task.state.value,
                    to_state=task.state.value,
                    note=(
                        "cleared block record: code="
                        f"{cleared or '-'} reason={(task.blocked_reason or '-')[:500]} "
                        f"(acknowledged: {reason.strip()})"
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
        # Read-only: resolve the effective policy/source without rewriting the
        # task just to display where the policy came from.
        readout = self.read_recorded_policy(task)
        policy_source = readout.source
        usage = ProviderBudget.usage(task)
        if readout.document is not None:
            limits = readout.document.budget
            budget_one_line = (
                f"implementer {usage.implementer_calls}/{limits.max_implementer_calls}"
                f", reviewer {usage.reviewer_calls}/{limits.max_reviewer_calls}"
                f", total {usage.total_calls}/{limits.max_total_provider_calls}"
            )
        else:
            budget_one_line = (
                f"implementer {usage.implementer_calls}/-, reviewer "
                f"{usage.reviewer_calls}/-, total {usage.total_calls}/- "
                f"({readout.display})"
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
                + (
                    ", result persisted, not applied"
                    if last_attempt.result_persisted
                    and not last_attempt.result_applied
                    else ""
                )
                + (" (IN FLIGHT)" if task.review_call_in_flight else "")
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
            "policy_source": policy_source,
            "policy_display": readout.display,
            "policy_integrity": readout.integrity,
            "policy_detail": readout.detail,
            "policy_profiles": [
                {"name": ref.name, "sha256": ref.sha256} for ref in readout.profiles
            ],
            "blocked": task.blocked_code or "",
        }

    def usage_block(self, task_id: str) -> dict[str, object]:
        """Read-only provider usage/audit summary for `devrelay usage`."""
        task = self._load(task_id)
        readout = self.read_recorded_policy(task)
        policy_source = readout.source
        limits = readout.document.budget if readout.document is not None else None
        usage = ProviderBudget.usage(task)
        last_attempt = task.review_attempts[-1] if task.review_attempts else None
        pending = pending_result_attempt(task)
        return {
            "task_id": task.task_id,
            "state": task.state.value,
            "implementer_calls": usage.implementer_calls,
            "reviewer_calls": usage.reviewer_calls,
            "total_calls": usage.total_calls,
            "max_implementer_calls": (
                limits.max_implementer_calls if limits is not None else None
            ),
            "max_reviewer_calls": (
                limits.max_reviewer_calls if limits is not None else None
            ),
            "max_total_provider_calls": (
                limits.max_total_provider_calls if limits is not None else None
            ),
            "policy_display": readout.display,
            "policy_integrity": readout.integrity,
            "policy_detail": readout.detail,
            "policy_profiles": [
                {"name": ref.name, "sha256": ref.sha256} for ref in readout.profiles
            ],
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
                    "attempt_id": attempt.attempt_id,
                    "provider": attempt.provider_name,
                    "status": attempt.status.value,
                    "transport_attempts": attempt.transport_attempts,
                    "format_attempts": attempt.format_attempts,
                    "external_calls": attempt.external_calls_consumed,
                    "call_ids": list(attempt.call_ids),
                    "model": attempt.model,
                    "endpoint_host": attempt.endpoint_host,
                    "error_type": attempt.error_type.value if attempt.error_type else None,
                    "result": attempt.result.decision.value if attempt.result else None,
                    "result_persisted": attempt.result_persisted,
                    "result_applied": attempt.result_applied,
                    "applied_state": attempt.applied_state,
                }
                for attempt in task.review_attempts
            ],
            "last_review_attempt": (
                last_attempt.status.value if last_attempt is not None else "-"
            ),
            "pending_review_result": (
                {
                    "attempt_id": pending.attempt_id,
                    "review_number": pending.review_number,
                    "result_hash": pending.result_hash,
                }
                if pending is not None
                else None
            ),
            "applied_reviews": [
                {
                    "identity": record.identity,
                    "review_number": record.review_number,
                    "attempt_id": record.attempt_id,
                    "state": record.state,
                    "decision": record.decision,
                    "applied_at": record.applied_at,
                }
                for record in task.applied_reviews
            ],
            "policy_source": policy_source,
            "policy_refreshes": [
                {
                    "refresh_id": record.refresh_id,
                    "at": record.at,
                    "reason": record.reason,
                    "before_source": record.before_source,
                    "after_source": record.after_source,
                    "before_config_sha256": record.before_config_sha256,
                    "after_config_sha256": record.after_config_sha256,
                }
                for record in task.policy_refreshes
            ],
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
