"""Shared fakes/helpers for the DevRelay test-suite (no real Codex/network)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

from devrelay.artifacts.store import ArtifactStore
from devrelay.config import DevRelayConfig, load_config
from devrelay.models import (
    CommandResult,
    Finding,
    NameStatusEntry,
    ProviderExecutionResult,
    RepoSnapshot,
    ReviewResult,
    Severity,
    TaskDelta,
    TaskPacket,
    TaskRun,
    WorkspaceBaseline,
    WorkspaceSnapshot,
)
from devrelay.pipeline.engine import DevRelayEngine
from devrelay.providers.base import ImplementerProvider, ReviewerProvider
from devrelay.workspace.git import GitWorkspace
from devrelay.workspace.runner import CommandRunner


# ---------------------------------------------------------------------------
# git helper
# ---------------------------------------------------------------------------

def make_git_repo(path: Path, *, initial_files: dict[str, str] | None = None) -> Path:
    """Create a git repository with one initial commit."""
    path.mkdir(parents=True, exist_ok=True)
    for name, content in (initial_files or {}).items():
        target = path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    git_env = {**os.environ.copy(), "GIT_AUTHOR_NAME": "DevRelay Test",
               "GIT_AUTHOR_EMAIL": "t@devrelay.test",
               "GIT_COMMITTER_NAME": "DevRelay Test",
               "GIT_COMMITTER_EMAIL": "t@devrelay.test"}
    def _git(args, cwd=None):
        proc = subprocess.run(
            ["git", *args] if cwd is None else ["git", "-C", str(cwd), *args],
            env=git_env, capture_output=True, text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"git {' '.join(args)} failed rc={proc.returncode}: "
                f"{proc.stderr[-800:] or proc.stdout[-800:]}"
            )

    _git(["init", "-q", "-b", "main", str(path)])
    _git(["add", "-A"], cwd=path)
    proc = subprocess.run(
        ["git", "-C", str(path), "commit", "-q", "-m", "initial"],
        env=git_env, capture_output=True, text=True,
    )
    combined = f"{proc.stderr or ''}{proc.stdout or ''}"
    if proc.returncode != 0 and "nothing to commit" not in combined:
        raise RuntimeError(
            f"git commit failed rc={proc.returncode}: {combined[-800:]}"
        )
    return path


def dirty_file(path: Path, name: str, content: str = "dirty content\n") -> Path:
    """Create/modify a file so the workspace reports it as dirty."""
    target = path / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# fakes
# ---------------------------------------------------------------------------

class FakeCommandRunner:
    """Records calls; scripted results keyed by joined argv."""

    def __init__(self, results: dict[str, CommandResult] | None = None) -> None:
        self.results = results or {}
        self.calls: list[dict] = []
        self.which_map: dict[str, str | None] = {}

    def run(self, argv, cwd=None, timeout_seconds=900.0, input_text=None, env=None):
        self.calls.append(
            {
                "argv": list(argv),
                "cwd": str(cwd) if cwd is not None else None,
                "input": input_text,
                "timeout": timeout_seconds,
            }
        )
        result = self.results.get(" ".join(argv))
        if result is None:
            return CommandResult(
                command=list(argv),
                cwd=str(cwd) if cwd is not None else None,
                exit_code=0,
            )
        return result

    def which(self, executable: str) -> str | None:
        return self.which_map.get(executable, f"/fake/{executable}")


def fake_success(stdout: str = "ok\n", code: int = 0) -> CommandResult:
    return CommandResult(command=[], exit_code=code, stdout=stdout)


def cmd_result(
    *,
    exit_code: int = 0,
    stdout: str = "",
    stderr: str = "",
    timed_out: bool = False,
    error: str | None = None,
) -> CommandResult:
    return CommandResult(
        command=[], exit_code=exit_code, stdout=stdout, stderr=stderr,
        timed_out=timed_out, error=error,
    )


class FakeWorkspace:
    def __init__(
        self,
        root: Path,
        *,
        dirty_files: Optional[list[str]] = None,
        diff_text: str = "diff --git a/src/x.py b/src/x.py\n+change\n",
        changed: Optional[list[str]] = None,
        head: str = "abc123def456",
    ) -> None:
        self.root = Path(root)
        self._dirty = dirty_files or []
        self._diff = diff_text
        self._changed = changed if changed is not None else list(self._dirty)
        self._head = head

    def snapshot(self) -> WorkspaceSnapshot:
        return WorkspaceSnapshot(
            repo_root=str(self.root),
            head_sha=self._head,
            branch="main",
            dirty_files=list(self._dirty),
            has_git=True,
        )

    def detect_repo(self) -> bool:
        return True

    def diff(self, stat: bool = False) -> str:
        return "stat" if stat else self._diff

    def changed_name_only(self) -> list[str]:
        return list(self._changed)

    def head_sha(self) -> str | None:
        return self._head

    def status(self) -> str:
        return "\n".join(self._dirty)

    def is_dirty(self) -> bool:
        return bool(self._dirty)


class FakeImplementer(ImplementerProvider):
    name = "fake-implementer"

    def __init__(
        self,
        *,
        report: str = "FAKE IMPLEMENTATION\nIMPLEMENTATION_SUMMARY\nok\n",
        exit_code: int = 0,
        stderr: str = "",
        error: str | None = None,
        unavailable: bool = False,
        stdout: str | None = None,
    ) -> None:
        self._report = report
        self._exit_code = exit_code
        self._stderr = stderr
        self._error = error
        self._unavailable = unavailable
        self._stdout = stdout if stdout is not None else report
        self.calls: list = []

    def availability(self) -> tuple[bool, str]:
        return (not self._unavailable, "fake provider")

    def run(self, context) -> ProviderExecutionResult:
        self.calls.append(context)
        if self._unavailable:
            return ProviderExecutionResult(
                exit_code=None,
                error="Codex CLI is not installed or not available on PATH.",
                stderr="Codex CLI is not installed or not available on PATH.",
            )
        if self._error:
            return ProviderExecutionResult(exit_code=None, error=self._error)
        return ProviderExecutionResult(
            exit_code=self._exit_code,
            stdout=self._stdout,
            stderr=self._stderr,
            report=self._report,
        )


class QueueImplementer(FakeImplementer):
    """Fake implementer returning a queued result per call (then repeats last)."""

    def __init__(self, results: list[ProviderExecutionResult]) -> None:
        super().__init__()
        self.queue = list(results)

    def run(self, context) -> ProviderExecutionResult:
        self.calls.append(context)
        if self.queue:
            return self.queue.pop(0)
        return ProviderExecutionResult(exit_code=0, stdout="ok", report="ok")


class QueueReviewer(ReviewerProvider):
    """Automatic reviewer with a queue of ReviewResults."""

    name = "queue-reviewer"

    def __init__(self, results: list[ReviewResult]) -> None:
        self.queue = list(results)
        self.bundles: list = []

    @property
    def automatic(self) -> bool:
        return True

    def prepare_request(self, bundle, review_number=None):
        return None

    def review(self, bundle) -> ReviewResult:
        self.bundles.append(bundle)
        if self.queue:
            return self.queue.pop(0)
        return ReviewResult(decision="PASS", summary="default pass")


# ---------------------------------------------------------------------------
# model builders
# ---------------------------------------------------------------------------

def make_packet(
    task_id: str = "DR-0001",
    *,
    title: str = "Sample task",
    objective: str = "Do the thing",
    risk: str = "NORMAL",
    acceptance: Optional[list[str]] = None,
) -> TaskPacket:
    return TaskPacket(
        task_id=task_id,
        title=title,
        objective=objective,
        scope=["src/a.py"],
        out_of_scope=["docs/", "other/"],
        acceptance_criteria=acceptance or ["tests pass"],
        constraints=["no unrelated refactors"],
        tests_required=["pytest -q"],
        risk_level=risk,
    )


def make_finding(severity: Severity | str, title: str = "finding") -> Finding:
    return Finding(severity=severity, title=title, description="detail")


def make_review(
    decision: str,
    findings: Optional[list[Finding]] = None,
    summary: str = "review summary",
) -> ReviewResult:
    return ReviewResult(
        findings=findings or [],
        summary=summary,
        decision=decision,
        reviewer="test",
    )


def default_config() -> DevRelayConfig:
    return load_config(None)


class FakeBaselineService:
    """In-memory baseline/guard double for engine tests (no real git)."""

    def __init__(
        self,
        *,
        delta_text: str = "diff --git a/src/x.py b/src/x.py\n+agent line\n",
        violation_queues: Optional[list[list]] = None,
        fail_delta: bool = False,
    ) -> None:
        self._delta_text = delta_text
        self._violation_queues = list(violation_queues or [])
        self.fail_delta = fail_delta
        self.captures: list[str] = []
        self.pre_snapshots = 0
        self.post_snapshots = 0

    def capture(self, task_id: str) -> WorkspaceBaseline:
        self.captures.append(task_id)
        return WorkspaceBaseline(
            task_id=task_id,
            head_sha="abc123",
            branch="main",
            baseline_worktree_tree_sha="b" * 40,
            baseline_complete=True,
            baseline_storage_path=f"tasks/{task_id}/baseline",
        )

    def pre_snapshot(self) -> RepoSnapshot:
        self.pre_snapshots += 1
        return RepoSnapshot(head_sha="abc123", branch="main", index_tree_sha="i" * 40)

    def post_snapshot(self) -> RepoSnapshot:
        self.post_snapshots += 1
        return RepoSnapshot(head_sha="abc123", branch="main", index_tree_sha="i" * 40)

    def check_policy(self, before, after) -> list:
        if self._violation_queues:
            return self._violation_queues.pop(0)
        return []

    def task_delta(self, task: TaskRun) -> TaskDelta:
        if self.fail_delta:
            from devrelay.errors import BaselineUnavailableError

            raise BaselineUnavailableError(
                f"task {task.task_id} has no task baseline (legacy task)"
            )
        return TaskDelta(
            text_diff=self._delta_text,
            stat_text=" 1 file changed, 1 insertion(+)",
            changed_files=["src/x.py"],
            name_status=[NameStatusEntry(status="M", new_path="src/x.py")],
            method="fake",
        )

    def binary_task_diff(self, task: TaskRun) -> str:
        return "GIT binary patch (fake)"


def build_engine(
    tmp_path: Path,
    *,
    config: DevRelayConfig | None = None,
    implementer: ImplementerProvider | None = None,
    reviewer: ReviewerProvider | None = None,
    workspace=None,
    runner=None,
    use_real_git: bool = False,
    baseline_service=None,
):
    """Return (root, store, engine). Root contains a .devrelay store."""
    root = tmp_path / "ws"
    root.mkdir(parents=True, exist_ok=True)
    if use_real_git:
        make_git_repo(root, initial_files={"README.md": "hi\n"})
    store = ArtifactStore(root)
    store.ensure_initialized()
    cfg = config or default_config()
    if workspace is None:
        ws: object = GitWorkspace(root) if use_real_git else FakeWorkspace(root)
    else:
        ws = workspace
    if baseline_service is None:
        if use_real_git:
            from devrelay.baseline.service import BaselineService
            from devrelay.workspace.runner import CommandRunner as CR

            baseline_service = BaselineService(
                root, CR(), store, cfg
            )
        else:
            baseline_service = FakeBaselineService()
    eng = DevRelayEngine(
        cfg,
        store,
        ws,
        implementer=implementer or FakeImplementer(),
        reviewer=reviewer or ManualReviewerProxy(),
        runner=runner or FakeCommandRunner(),
        baselines=baseline_service,
    )
    return root, store, eng


from devrelay.providers.manual import ManualReviewer as ManualReviewerProxy  # noqa: E402
