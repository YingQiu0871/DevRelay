"""Facade used by the pipeline engine and CLI (real git implementation)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from devrelay.artifacts.store import ArtifactStore
from devrelay.baseline.capture import BaselineBuilder, worktree_tree_sha
from devrelay.baseline.comparator import BaselineComparator
from devrelay.baseline.guard import RepoGuard
from devrelay.baseline.store import BaselineStore
from devrelay.config import DevRelayConfig
from devrelay.errors import BaselineCorruptError, BaselineUnavailableError
from devrelay.models import (
    PolicyViolation,
    RepoSnapshot,
    TaskDelta,
    TaskRun,
    WorkspaceBaseline,
)
from devrelay.workspace.runner import CommandRunner


class BaselineService:
    """Real-git baseline service: capture, delta, reconstruction, guard."""

    def __init__(
        self,
        root: str | Path,
        runner: CommandRunner | None,
        store: ArtifactStore,
        config: DevRelayConfig,
    ) -> None:
        self.root = Path(root).resolve()
        self.runner = runner or CommandRunner()
        self.store = store
        self.config = config
        self._bstore = BaselineStore(store)
        self._builder = BaselineBuilder(
            self.root,
            self.runner,
            config.baseline.max_untracked_file_bytes,
        )
        self._comparator = BaselineComparator(self.root, self.runner)
        self._guard = RepoGuard(self.root, self.runner)

    # -- baseline lifecycle ---------------------------------------------
    def capture(self, task_id: str) -> WorkspaceBaseline:
        storage_rel = self.store.rel_path(self._bstore.baseline_dir(task_id))
        captured = self._builder.capture(task_id, storage_rel)
        self._bstore.write(
            task_id,
            captured.baseline,
            captured.patch_bytes,
            captured.untracked_files,
        )
        return captured.baseline

    def validate_baseline(self, task_id: str) -> WorkspaceBaseline:
        return self._bstore.validate(task_id)

    def _load_baseline(self, task: TaskRun) -> tuple[WorkspaceBaseline, bytes]:
        if task.baseline is None or not task.baseline.baseline_complete:
            raise BaselineUnavailableError(
                f"task {task.task_id} has no complete task baseline "
                "(it predates v0.1-RC baselines). Precise task-relative deltas "
                "are unavailable for legacy tasks; create a new task to get a "
                "baseline. DevRelay will not guess a diff."
            )
        return self._bstore.load(task.task_id)

    # -- task-relative delta --------------------------------------------
    def task_delta(self, task: TaskRun) -> TaskDelta:
        baseline, _patch = self._load_baseline(task)
        tree, method = self._comparator.ensure_baseline_tree(
            self._bstore, task.task_id, baseline
        )
        current = worktree_tree_sha(self.root, self.runner)
        return self._comparator.diff_trees(tree, current, method=method)

    def binary_task_diff(self, task: TaskRun) -> str:
        baseline, _patch = self._load_baseline(task)
        tree, _method = self._comparator.ensure_baseline_tree(
            self._bstore, task.task_id, baseline
        )
        current = worktree_tree_sha(self.root, self.runner)
        return self._comparator.binary_patch(tree, current)

    # -- policy guard ----------------------------------------------------
    def pre_snapshot(self) -> RepoSnapshot:
        return self._guard.snapshot(note="pre provider run")

    def post_snapshot(self) -> RepoSnapshot:
        return self._guard.snapshot(note="post provider run")

    def check_policy(
        self,
        before: RepoSnapshot,
        after: RepoSnapshot,
    ) -> list[PolicyViolation]:
        return self._guard.check_policy(before, after, self.config.git)
