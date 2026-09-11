"""Baseline capture with an ignored DevRelay state directory (smoke blocker).

Regression for the real-smoke blocker: `devrelay start` failed with

    git add -A -- . :(exclude).devrelay failed:
    The following paths are ignored by one of your .gitignore files: .devrelay

in any repository whose `.gitignore` lists `.devrelay/` (the documented, normal
setup).  Git rejects an explicitly named ignored pathspec, so tree building must
never depend on `:(exclude).devrelay` - and `git add -f` is not an option
because it would pull unrelated ignored files into the tree.

Every scenario runs against a real temporary git repository with the real
BaselineService/engine.  No Codex, no reviewer, no network.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from devrelay.artifacts.store import ArtifactStore
from devrelay.baseline.capture import TempGitIndex, worktree_tree_sha
from devrelay.baseline.service import BaselineService
from devrelay.models import TaskRun
from devrelay.pipeline.states import PipelineState as S
from devrelay.workspace.runner import CommandRunner
from typer.testing import CliRunner

from devrelay.cli import app

from helpers import default_config, make_git_repo

IGNORE_CONTENT = ".devrelay/\n__pycache__/\n.pytest_cache/\n"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    env = {
        "GIT_AUTHOR_NAME": "T",
        "GIT_AUTHOR_EMAIL": "t@x",
        "GIT_COMMITTER_NAME": "T",
        "GIT_COMMITTER_EMAIL": "t@x",
    }
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, env=env
    )


def _service(repo: Path):
    store = ArtifactStore(repo)
    store.ensure_initialized()
    runner = CommandRunner()
    service = BaselineService(repo, runner, store, default_config())
    return store, runner, service


def _tree_files(repo: Path, runner: CommandRunner, tree: str) -> list[str]:
    result = runner.run(
        ["git", "-C", str(repo), "ls-tree", "-r", "--name-only", tree], cwd=repo
    )
    assert result.exit_code == 0, result.stderr
    return sorted(name for name in result.stdout.splitlines() if name)


def _index_bytes(repo: Path) -> str:
    index = repo / ".git" / "index"
    return hashlib.sha256(index.read_bytes()).hexdigest() if index.is_file() else ""


def _smoke_repo(
    tmp_path: Path, *, ignore_self: bool = True, with_devrelay: bool = True
) -> Path:
    """The exact smoke fixture: .gitignore lists .devrelay/, tracked app files."""
    files = {
        "app.py": 'def greet():\n    return "placeholder"\n',
        "test_app.py": (
            "from app import greet\n\n\n"
            "def test_greet_is_callable():\n    assert callable(greet)\n"
        ),
    }
    if ignore_self:
        files[".gitignore"] = IGNORE_CONTENT
    repo = make_git_repo(tmp_path / "repo", initial_files=files)
    if with_devrelay:
        # DevRelay runtime state directory (untracked; ignored or not).
        (repo / ".devrelay" / "tasks" / "DR-0001").mkdir(
            parents=True, exist_ok=True
        )
        (repo / ".devrelay" / "state.json").write_text(
            '{"current": null}\n', encoding="utf-8"
        )
        (repo / ".devrelay" / "config.yaml").write_text(
            "review:\n  provider: manual\n", encoding="utf-8"
        )
    return repo


# ---------------------------------------------------------------------------
# 1. THE SMOKE CASE: .devrelay/ ignored -> start must succeed
# ---------------------------------------------------------------------------
def test_start_succeeds_when_devrelay_is_ignored(tmp_path, monkeypatch):
    # Exactly the smoke reproduction: no .devrelay yet; `init` creates it and
    # `start` must then capture a baseline despite it being gitignored.
    repo = _smoke_repo(tmp_path, ignore_self=True, with_devrelay=False)
    monkeypatch.chdir(repo)

    init_result = CliRunner().invoke(app, ["init"])
    assert init_result.exit_code == 0, init_result.output

    result = CliRunner().invoke(app, ["start", "ignored self-dir regression"])
    assert result.exit_code == 0, result.output
    assert "Created task DR-0001" in result.output
    assert "BaselineError" not in result.output
    assert "paths are ignored" not in result.output

    store = ArtifactStore(repo)
    task = store.read_task("DR-0001")
    assert task.state == S.PLAN_REQUIRED
    assert task.policy_source == "snapshot"
    assert task.baseline is not None and task.baseline.baseline_complete
    # DevRelay state is excluded from the recorded worktree tree.
    files = _tree_files(
        repo, CommandRunner(), task.baseline.baseline_worktree_tree_sha
    )
    assert files == [".gitignore", "app.py", "test_app.py"]
    assert not any(name.startswith(".devrelay") for name in files)


def test_raw_capture_survives_ignored_self_dir(tmp_path):
    """The failing command itself: no BaselineError, tree excludes .devrelay."""
    repo = _smoke_repo(tmp_path, ignore_self=True)
    store, runner, service = _service(repo)
    baseline = service.capture("DR-0001")
    files = _tree_files(repo, runner, baseline.baseline_worktree_tree_sha)
    assert files == [".gitignore", "app.py", "test_app.py"]


# ---------------------------------------------------------------------------
# 2. .devrelay NOT ignored -> self state still excluded
# ---------------------------------------------------------------------------
def test_self_state_excluded_when_not_ignored(tmp_path):
    repo = _smoke_repo(tmp_path, ignore_self=False)
    store, runner, service = _service(repo)
    baseline = service.capture("DR-0001")
    files = _tree_files(repo, runner, baseline.baseline_worktree_tree_sha)
    assert ".gitignore" not in files            # not present in this repo
    assert files == ["app.py", "test_app.py"]
    # ...and the same exclusion holds for the current (delta) tree.
    current = worktree_tree_sha(repo, runner)
    assert _tree_files(repo, runner, current) == ["app.py", "test_app.py"]


def test_tracked_devrelay_state_is_excluded(tmp_path):
    """A repository that tracks .devrelay/** must not leak it into the tree."""
    repo = _smoke_repo(tmp_path, ignore_self=False)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "track tracked devrelay state")
    assert _git(repo, "ls-files", "--", ".devrelay").stdout.split() == [
        ".devrelay/config.yaml",
        ".devrelay/state.json",
    ]

    store, runner, service = _service(repo)
    baseline = service.capture("DR-0001")
    files = _tree_files(repo, runner, baseline.baseline_worktree_tree_sha)
    assert files == ["app.py", "test_app.py"]
    # The patch that reviewers see must exclude it as well.
    patch_text = (store.task_dir("DR-0001") / "baseline" / "tracked.patch").read_text(
        encoding="utf-8"
    )
    assert ".devrelay" not in patch_text


# ---------------------------------------------------------------------------
# 3. ignored / untracked / staged / tracked matrix
# ---------------------------------------------------------------------------
def test_ignored_files_excluded_and_new_files_included(tmp_path):
    repo = _smoke_repo(tmp_path, ignore_self=True)
    # unrelated ignored files
    (repo / "__pycache__").mkdir(exist_ok=True)
    (repo / "__pycache__" / "app.cpython-314.pyc").write_bytes(b"\x00junk")
    (repo / ".pytest_cache").mkdir(exist_ok=True)
    (repo / ".pytest_cache" / "CACHEDIR.TAG").write_text("junk\n", encoding="utf-8")
    # non-ignored untracked file
    (repo / "notes.txt").write_text("keep me\n", encoding="utf-8")
    # staged new file
    (repo / "staged.txt").write_text("staged\n", encoding="utf-8")
    _git(repo, "add", "staged.txt")
    # tracked modification + tracked deletion
    (repo / "app.py").write_text('def greet():\n    return "hello"\n', encoding="utf-8")
    _git(repo, "rm", "-q", "--cached", "test_app.py")
    (repo / "test_app.py").unlink()

    store, runner, service = _service(repo)
    index_before = _index_bytes(repo)
    baseline = service.capture("DR-0001")
    index_after = _index_bytes(repo)

    files = _tree_files(repo, runner, baseline.baseline_worktree_tree_sha)
    assert files == [".gitignore", "app.py", "notes.txt", "staged.txt"]
    assert "test_app.py" not in files                      # deletion represented
    assert "staged.txt" in files                           # staged addition kept
    assert "notes.txt" in files                            # untracked kept
    assert not any(n.startswith(".devrelay") for n in files)
    assert not any("__pycache__" in n or ".pytest_cache" in n for n in files)
    # real index untouched
    assert index_before == index_after


def test_real_index_bytes_unchanged_and_temp_index_cleaned(tmp_path):
    import tempfile

    repo = _smoke_repo(tmp_path, ignore_self=True)
    (repo / "app.py").write_text('def greet():\n    return "hello world"\n', encoding="utf-8")
    _git(repo, "add", "app.py")                    # staged modification
    (repo / "app.py").write_text('def greet():\n    return "hello"\n', encoding="utf-8")

    store, runner, service = _service(repo)
    before = _index_bytes(repo)
    service.capture("DR-0001")
    assert _index_bytes(repo) == before

    tmp_root = Path(tempfile.gettempdir())
    leftovers = sorted(p.name for p in tmp_root.glob("devrelay-index-*"))
    assert leftovers == [], leftovers   # TemporaryDirectory cleans up


def test_task_delta_excludes_devrelay_state(tmp_path):
    repo = _smoke_repo(tmp_path, ignore_self=True)
    store, runner, service = _service(repo)
    baseline = service.capture("DR-0001")
    task = TaskRun(task_id="DR-0001", title="t", baseline=baseline)
    store.write_task(task)

    # agent work + DevRelay's own churn (ignored)
    (repo / "app.py").write_text('def greet():\n    return "hello"\n', encoding="utf-8")
    (repo / ".devrelay" / "tasks" / "DR-0001" / "state.json").write_text(
        '{"big": "churn"}\n', encoding="utf-8"
    )
    (repo / ".devrelay" / "logs").mkdir(exist_ok=True)
    (repo / ".devrelay" / "logs" / "codex.log").write_text("noise\n", encoding="utf-8")

    delta = service.task_delta(task)
    assert delta.changed_files == ["app.py"]
    assert ".devrelay" not in delta.text_diff
    assert "churn" not in delta.text_diff
    assert "+    return \"hello\"" in delta.text_diff


# ---------------------------------------------------------------------------
# 4. the old failure mode is gone for good
# ---------------------------------------------------------------------------
def test_exclude_pathspec_on_ignored_path_is_not_used(tmp_path):
    """Guard the root cause: the exact failing argv must not come back.

    The probe runs against a *temporary* index, so the real index is never
    involved even while demonstrating the failure.
    """
    repo = _smoke_repo(tmp_path, ignore_self=True)
    store, runner, service = _service(repo)
    service.capture("DR-0001")
    assert (store.task_dir("DR-0001") / "baseline" / "baseline.json").is_file()
    index_before = _index_bytes(repo)

    with TempGitIndex(repo) as tmp:
        runner.run(
            ["git", "-C", str(repo), "read-tree", "HEAD"], cwd=repo, env=tmp.env
        )
        probe = runner.run(
            [
                "git",
                "-C",
                str(repo),
                "add",
                "-A",
                "--",
                ".",
                ":(exclude).devrelay",
            ],
            cwd=repo,
            env=tmp.env,
        )
    assert probe.exit_code == 1
    assert "ignored" in (probe.stderr or "").lower()
    assert _index_bytes(repo) == index_before        # real index untouched
