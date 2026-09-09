"""GitWorkspace tests against real (tiny) git repositories."""

import pytest

from devrelay.errors import WorkspaceError
from devrelay.workspace.git import GitWorkspace
from devrelay.workspace.runner import CommandRunner

from helpers import dirty_file, make_git_repo


def test_snapshot_of_clean_repo(tmp_path):
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    ws = GitWorkspace(repo)
    assert ws.detect_repo()
    snapshot = ws.snapshot()
    assert snapshot.has_git
    assert snapshot.head_sha
    assert snapshot.branch in ("main", "master")
    assert snapshot.dirty_files == []
    assert not snapshot.is_dirty


def test_snapshot_records_preexisting_dirty_files(tmp_path):
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n", "b.txt": "b\n"})
    dirty_file(repo, "a.txt", content="changed\n")
    dirty_file(repo, "new.txt", content="untracked\n")
    ws = GitWorkspace(repo)
    assert ws.is_dirty()
    snapshot = ws.snapshot()
    assert "a.txt" in snapshot.dirty_files
    assert "new.txt" in snapshot.dirty_files


def test_changed_name_only_and_diff(tmp_path):
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    dirty_file(repo, "a.txt", content="a\nchanged\n")
    dirty_file(repo, "untracked.txt", content="u\n")
    ws = GitWorkspace(repo)
    names = ws.changed_name_only()
    assert "a.txt" in names
    assert "untracked.txt" in names
    diff = ws.diff()
    assert "+changed" in diff
    assert "untracked.txt" in diff  # flagged in the untracked note


def test_non_repo_directory_errors(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    ws = GitWorkspace(plain)
    assert not ws.detect_repo()
    with pytest.raises(WorkspaceError):
        ws.diff()
    snapshot = ws.snapshot()
    assert snapshot.has_git is False
