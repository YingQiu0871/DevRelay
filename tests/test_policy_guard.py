"""Repository policy guard + engine reporting tests (RC scenarios 22-35)."""

import subprocess
from pathlib import Path
from typing import Callable, Optional

import pytest

from devrelay.artifacts.store import ArtifactStore
from devrelay.baseline.service import BaselineService
from devrelay.models import PolicyViolationType, TaskRun
from devrelay.pipeline.engine import DevRelayEngine
from devrelay.pipeline.states import PipelineState
from devrelay.providers.base import ImplementerProvider
from devrelay.providers.manual import ManualReviewer
from devrelay.workspace.git import GitWorkspace
from devrelay.workspace.runner import CommandRunner

from helpers import (
    FakeBaselineService,
    FakeCommandRunner,
    FakeImplementer,
    default_config,
    make_finding,
    make_git_repo,
    make_packet,
    make_review,
)

S = PipelineState


def _git(repo: Path, *args: str):
    env = {
        "GIT_AUTHOR_NAME": "T",
        "GIT_AUTHOR_EMAIL": "t@x",
        "GIT_COMMITTER_NAME": "T",
        "GIT_COMMITTER_EMAIL": "t@x",
    }
    subprocess.run(["git", "-C", str(repo), *args], check=True, env=env)


class ActionImplementer(FakeImplementer):
    """Fake implementer that performs a real filesystem/git action."""

    def __init__(self, action: Callable[[Path], None]):
        super().__init__(stdout="done")
        self.action = action

    def run(self, context):
        self.calls.append(context)
        root = Path(context.workspace_root)
        if self.action:
            self.action(root)
        return super().run(context)


def _real_engine(tmp_path: Path, implementer=None, *, dirty: dict[str, str] | None = None):
    """Real git repo + real baseline service + manual reviewer engine."""
    initial = {"a.txt": "base\n", "b.txt": "b\n"}
    repo = make_git_repo(tmp_path / "repo", initial_files=initial)
    if dirty:
        for name, content in dirty.items():
            target = repo / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    store = ArtifactStore(repo)
    store.ensure_initialized()
    config = default_config()
    runner = CommandRunner()
    ws = GitWorkspace(repo, runner)
    engine = DevRelayEngine(
        config,
        store,
        ws,
        implementer=implementer or FakeImplementer(),
        reviewer=ManualReviewer(),
        runner=runner,
        baselines=BaselineService(repo, runner, store, config),
    )
    return repo, store, engine


def _start_and_review(engine, store) -> str:
    task_id = "DR-0001"
    engine.create_task("t")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    engine.continue_task(task_id)
    assert store.read_task(task_id).state == S.REVIEWING
    return task_id


# ---------------------------------------------------------------------------
# 22. worktree-only change is allowed by the guard
# ---------------------------------------------------------------------------
def test_worktree_only_change_passes_guard(tmp_path):
    def edit(root: Path) -> None:
        (root / "a.txt").write_text("base\n+agent\n", encoding="utf-8")
        (root / "new_c.py").write_text("x=1\n", encoding="utf-8")

    repo, store, engine = _real_engine(tmp_path, implementer=ActionImplementer(edit))
    task_id = _start_and_review(engine, store)
    task = store.read_task(task_id)
    assert task.state == S.REVIEWING
    assert task.policy_violations == []
    policy_dir = store.policy_dir(task_id)
    assert not list(policy_dir.glob("violations-*.json"))
    assert task.implementation_passes == 1


# ---------------------------------------------------------------------------
# 23. HEAD change -> POLICY_VIOLATION + BLOCKED, no auto repair
# ---------------------------------------------------------------------------
def test_head_change_is_blocked_and_not_reverted(tmp_path):
    def commit(root: Path) -> None:
        _git(root, "commit", "--allow-empty", "-m", "sneaky")

    repo, store, engine = _real_engine(tmp_path, implementer=ActionImplementer(commit))
    task_id = "DR-0001"
    head_before = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    engine.create_task("t")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    events = engine.continue_task(task_id)
    task = store.read_task(task_id)
    assert task.state == S.BLOCKED
    assert task.blocked_code == "policy_violation"
    assert task.policy_violations
    assert task.policy_violations[0].type == PolicyViolationType.UNEXPECTED_HEAD_CHANGE
    assert task.implementation_passes == 0  # violating run never counted
    assert any("policy violation" in e for e in events)
    # artifacts persisted under policy/
    policy_dir = store.policy_dir(task_id)
    assert list(policy_dir.glob("pre-run-01.json"))
    assert list(policy_dir.glob("post-run-01.json"))
    violations_file = list(policy_dir.glob("violations-01.json"))
    assert violations_file
    # DevRelay never repairs state: sneaky commit is still there
    head_after = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    assert head_after != head_before


def test_violations_survive_process_restart(tmp_path):
    def commit(root: Path) -> None:
        _git(root, "commit", "--allow-empty", "-m", "sneaky")

    repo, store, engine = _real_engine(tmp_path, implementer=ActionImplementer(commit))
    task_id = "DR-0001"
    engine.create_task("t")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    engine.continue_task(task_id)
    assert store.read_task(task_id).state == S.BLOCKED

    # fresh store instance == restart
    store2 = ArtifactStore(repo)
    task2 = store2.read_task(task_id)
    assert task2.state == S.BLOCKED
    assert task2.policy_violations
    assert task2.policy_violations[0].type == PolicyViolationType.UNEXPECTED_HEAD_CHANGE


# ---------------------------------------------------------------------------
# 24. branch switch -> BLOCKED
# ---------------------------------------------------------------------------
def test_branch_change_is_blocked(tmp_path):
    def switch(root: Path) -> None:
        _git(root, "checkout", "-q", "-b", "sneaky-branch")

    repo, store, engine = _real_engine(tmp_path, implementer=ActionImplementer(switch))
    task_id = "DR-0001"
    engine.create_task("t")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    engine.continue_task(task_id)
    task = store.read_task(task_id)
    assert task.state == S.BLOCKED
    assert any(
        v.type == PolicyViolationType.UNEXPECTED_BRANCH_CHANGE
        for v in task.policy_violations
    )


# ---------------------------------------------------------------------------
# 25. tag mutation -> BLOCKED
# ---------------------------------------------------------------------------
def test_tag_creation_is_blocked(tmp_path):
    def tag(root: Path) -> None:
        _git(root, "tag", "sneaky-tag")

    repo, store, engine = _real_engine(tmp_path, implementer=ActionImplementer(tag))
    task_id = "DR-0001"
    engine.create_task("t")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    engine.continue_task(task_id)
    task = store.read_task(task_id)
    assert task.state == S.BLOCKED
    assert any(
        v.type == PolicyViolationType.UNEXPECTED_TAG_CHANGE
        for v in task.policy_violations
    )


# ---------------------------------------------------------------------------
# 26. real index staging mutation -> BLOCKED (default)
# ---------------------------------------------------------------------------
def test_index_mutation_is_blocked(tmp_path):
    def stage(root: Path) -> None:
        (root / "staged_by_agent.txt").write_text("x\n", encoding="utf-8")
        _git(root, "add", "staged_by_agent.txt")

    repo, store, engine = _real_engine(tmp_path, implementer=ActionImplementer(stage))
    task_id = "DR-0001"
    engine.create_task("t")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    engine.continue_task(task_id)
    task = store.read_task(task_id)
    assert task.state == S.BLOCKED
    assert any(
        v.type == PolicyViolationType.UNEXPECTED_INDEX_MUTATION
        for v in task.policy_violations
    )
    # DevRelay does not auto-unstage
    status = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True, text=True,
    ).stdout
    assert "staged_by_agent.txt" in status


# ---------------------------------------------------------------------------
# 33/34. review request + final report are task-relative
# ---------------------------------------------------------------------------
def test_review_request_contains_task_relative_diff_not_head_diff(tmp_path):
    def edit(root: Path) -> None:
        (root / "a.txt").write_text(
            "base\nUSER_ONLY_LINE\nAGENT_LINE\n", encoding="utf-8"
        )
        (root / "new_b.py").write_text("x=1\n", encoding="utf-8")

    repo, store, engine = _real_engine(
        tmp_path,
        implementer=ActionImplementer(edit),
        dirty={"a.txt": "base\nUSER_ONLY_LINE\n"},
    )
    task_id = _start_and_review(engine, store)
    request = (
        store.reviews_dir(task_id) / "review-01-request.md"
    ).read_text(encoding="utf-8")
    assert "task baseline -> current workspace" in request
    assert "+AGENT_LINE" in request
    added_leaks = [
        ln for ln in request.splitlines()
        if ln.startswith("+") and "USER_ONLY_LINE" in ln
    ]
    assert not added_leaks  # pre-existing content never leaks as agent additions
    assert "TASK-RELATIVE" in request


def test_final_report_separates_preexisting_and_task_changes(tmp_path):
    def edit(root: Path) -> None:
        (root / "a.txt").write_text(
            "base\nUSER_ONLY_LINE\nAGENT_LINE\n", encoding="utf-8"
        )
        (root / "new_b.py").write_text("x=1\n", encoding="utf-8")

    repo, store, engine = _real_engine(
        tmp_path,
        implementer=ActionImplementer(edit),
        dirty={"a.txt": "base\nUSER_ONLY_LINE\n"},
    )
    task_id = _start_and_review(engine, store)
    engine.import_manual_review(task_id, make_review("PASS"))
    assert store.read_task(task_id).state == S.FINAL_GATE_REQUIRED
    engine.approve_final(task_id, note="gate passed")
    task = store.read_task(task_id)
    assert task.state == S.DONE
    report = (store.final_dir(task_id) / "report.md").read_text(encoding="utf-8")
    assert "## Pre-existing Workspace Changes (excluded from the task delta)" in report
    assert "- a.txt" in report
    assert "## Task Changed Files (task baseline -> current workspace)" in report
    assert "- a.txt" in report and "- new_b.py" in report
    assert "## Repository Policy Checks" in report
    assert "USER_ONLY_LINE" not in report
    assert "Baseline status: COMPLETE" in report


# ---------------------------------------------------------------------------
# legacy tasks: explicit error, never a guessed diff
# ---------------------------------------------------------------------------
def test_legacy_task_without_baseline_blocks_with_explicit_error(tmp_path):
    root, store, engine = build_fake_engine(tmp_path)
    task_id = "DR-0001"
    engine.create_task("t")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    # simulate a pre-RC task: baseline never captured
    legacy = store.read_task(task_id).model_copy(update={"baseline": None})
    store.write_task(legacy)
    engine.continue_task(task_id)
    task = store.read_task(task_id)
    assert task.state == S.BLOCKED
    assert task.blocked_code == "baseline_error"
    assert "baseline" in (task.blocked_reason or "").lower()


def build_fake_engine(tmp_path):
    from devrelay.artifacts.store import ArtifactStore as S2

    root = tmp_path / "ws"
    root.mkdir(parents=True, exist_ok=True)
    store = S2(root)
    store.ensure_initialized()
    from devrelay.config import load_config
    from devrelay.workspace.git import GitWorkspace

    runner = CommandRunner()
    config = load_config(None)
    ws = GitWorkspace(root, runner)  # no git repo -> create_task refuses... use fake ws
    from helpers import FakeWorkspace

    ws = FakeWorkspace(root)
    engine = DevRelayEngine(
        config,
        store,
        ws,
        implementer=FakeImplementer(),
        reviewer=ManualReviewer(),
        runner=FakeCommandRunner(),
        baselines=FakeBaselineService(),
    )
    return root, store, engine
