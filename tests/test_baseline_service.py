"""Real-git baseline service tests (scenarios 1-21 of the RC spec).

Every scenario runs against a real temporary git repository and the real
BaselineService.  No Codex / network is involved.
"""

import hashlib
import subprocess
from pathlib import Path

import pytest

from devrelay.artifacts.store import ArtifactStore
from devrelay.baseline.service import BaselineService
from devrelay.errors import BaselineCorruptError
from devrelay.models import TaskRun
from devrelay.workspace.runner import CommandRunner

from helpers import default_config, dirty_file, make_git_repo


def _env_git(repo: Path, *args: str):
    env = {
        "GIT_AUTHOR_NAME": "T",
        "GIT_AUTHOR_EMAIL": "t@x",
        "GIT_COMMITTER_NAME": "T",
        "GIT_COMMITTER_EMAIL": "t@x",
    }
    subprocess.run(["git", "-C", str(repo), *args], check=True, env=env)


def _setup(tmp_path: Path, initial: dict[str, str]):
    repo = make_git_repo(tmp_path / "repo", initial_files=initial)
    store = ArtifactStore(repo)
    store.ensure_initialized()
    runner = CommandRunner()
    config = default_config()
    service = BaselineService(repo, runner, store, config)
    return repo, store, service, runner


def _capture(service, store, task_id: str = "DR-0001") -> TaskRun:
    baseline = service.capture(task_id)
    task = TaskRun(task_id=task_id, title="t", baseline=baseline)
    store.write_task(task)
    return task


def _write(repo: Path, name: str, content: bytes | str) -> Path:
    target = repo / name
    target.parent.mkdir(parents=True, exist_ok=True)
    data = content.encode("utf-8") if isinstance(content, str) else content
    target.write_bytes(data)
    return target

def _no_added_line_with(text: str, marker: str) -> None:
    """User content may legitimately appear as *context* in a unified diff;
    it must never appear as an added (+) line."""
    added = [ln for ln in text.splitlines() if ln.startswith("+") and marker in ln]
    assert not added, f"user content leaked as added lines: {added[:3]}"




# ---------------------------------------------------------------------------
# 1. clean baseline + agent change
# ---------------------------------------------------------------------------
def test_clean_baseline_then_agent_modifies_tracked_file(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"a.txt": "line1\n"})
    task = _capture(service, store)
    _write(repo, "a.txt", "line1\n+agent\n")
    delta = service.task_delta(task)
    assert delta.changed_files == ["a.txt"]
    assert "+agent" in delta.text_diff
    assert "+agent" in delta.text_diff


# ---------------------------------------------------------------------------
# 2. KEY: pre-existing user edit + agent edit on the SAME file
# ---------------------------------------------------------------------------
def test_same_file_user_then_agent_edit_only_agent_delta(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"a.txt": "base\n"})
    # user works before the task starts (uncommitted, unstaged)
    _write(repo, "a.txt", "base\nUSER_ONLY_LINE\n")
    task = _capture(service, store)
    assert "a.txt" in task.baseline.preexisting_dirty_files

    # agent extends the same file
    _write(repo, "a.txt", "base\nUSER_ONLY_LINE\nAGENT_LINE\n")
    delta = service.task_delta(task)
    assert delta.changed_files == ["a.txt"]
    assert "+AGENT_LINE" in delta.text_diff
    _no_added_line_with(delta.text_diff, "USER_ONLY_LINE")  # core acceptance


# ---------------------------------------------------------------------------
# 3. pre-existing modified A; agent modifies B -> A absent from task diff
# ---------------------------------------------------------------------------
def test_agent_only_touches_b_so_user_file_a_is_not_in_delta(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"a.txt": "a\n", "b.txt": "b\n"})
    _write(repo, "a.txt", "a\nUSER_CHANGE\n")
    task = _capture(service, store)
    _write(repo, "b.txt", "b\nAGENT_B\n")
    delta = service.task_delta(task)
    assert delta.changed_files == ["b.txt"]
    assert "a.txt" not in delta.changed_files
    _no_added_line_with(delta.text_diff, "USER_CHANGE")


# ---------------------------------------------------------------------------
# 4/5. pre-existing untracked file: agent modifies it / leaves it alone
# ---------------------------------------------------------------------------
def test_preexisting_untracked_file_agent_modifies_it(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"a.txt": "a\n"})
    _write(repo, "notes.txt", "USER_NOTE_ORIGINAL\n")
    task = _capture(service, store)
    assert "notes.txt" in task.baseline.preexisting_untracked_files
    assert task.baseline.untracked_entries[0].rel_path == "notes.txt"
    _write(repo, "notes.txt", "USER_NOTE_ORIGINAL\nAGENT_NOTE\n")
    delta = service.task_delta(task)
    assert "notes.txt" in delta.changed_files
    assert "+AGENT_NOTE" in delta.text_diff
    _no_added_line_with(delta.text_diff, "USER_NOTE_ORIGINAL")


def test_preexisting_untracked_file_unchanged_not_in_delta(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"a.txt": "a\n"})
    _write(repo, "notes.txt", "untouched\n")
    task = _capture(service, store)
    delta = service.task_delta(task)
    assert delta.changed_files == []
    assert not delta.has_changes


# ---------------------------------------------------------------------------
# 6/7. staged / staged+unstaged states
# ---------------------------------------------------------------------------
def test_preexisting_staged_change_is_baselined(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"s.txt": "v1\n"})
    _write(repo, "s.txt", "v2-staged\n")
    _env_git(repo, "add", "s.txt")
    task = _capture(service, store)
    assert "s.txt" in task.baseline.preexisting_dirty_files
    # staged content is part of the baseline: no delta when untouched
    assert service.task_delta(task).changed_files == []
    _write(repo, "s.txt", "v2-staged\nAGENT\n")
    delta = service.task_delta(task)
    assert delta.changed_files == ["s.txt"]
    _no_added_line_with(delta.text_diff, "v2-staged")


def test_staged_plus_unstaged_same_file_baseline_is_worktree_final(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"m.txt": "one\n"})
    _write(repo, "m.txt", "two-staged\n")
    _env_git(repo, "add", "m.txt")
    _write(repo, "m.txt", "two-staged\nthree-unstaged\n")
    task = _capture(service, store)
    assert service.task_delta(task).changed_files == []
    # baseline tree represents the FINAL working-tree content (staged+unstaged)
    _write(repo, "m.txt", "two-staged\nthree-unstaged\nAGENT\n")
    delta = service.task_delta(task)
    assert "+AGENT" in delta.text_diff
    _no_added_line_with(delta.text_diff, "three-unstaged")


# ---------------------------------------------------------------------------
# 8/9. pre-existing deletion / rename
# ---------------------------------------------------------------------------
def test_preexisting_deletion_is_baselined(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"gone.txt": "x\n", "stay.txt": "y\n"})
    (repo / "gone.txt").unlink()
    task = _capture(service, store)
    assert "gone.txt" in task.baseline.preexisting_dirty_files
    assert service.task_delta(task).changed_files == []
    _write(repo, "stay.txt", "y\nAGENT\n")
    delta = service.task_delta(task)
    assert delta.changed_files == ["stay.txt"]


def test_preexisting_rename_is_baselined(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"old_name.txt": "content\n"})
    (repo / "old_name.txt").rename(repo / "new_name.txt")
    task = _capture(service, store)
    assert service.task_delta(task).changed_files == []
    _write(repo, "new_name.txt", "content\nAGENT\n")
    delta = service.task_delta(task)
    assert delta.changed_files == ["new_name.txt"]


# ---------------------------------------------------------------------------
# 10-12. binary / unicode / spaces
# ---------------------------------------------------------------------------
def test_binary_dirty_file_baseline_and_delta(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"a.txt": "a\n"})
    _write(repo, "logo.bin", b"\x00\x01USERBIN\xff")
    task = _capture(service, store)
    assert task.baseline.untracked_entries[0].size == 10
    _write(repo, "logo.bin", b"\x00\x01USERBIN\xff\x00AGENTBIN\xfe")
    delta = service.task_delta(task)
    assert "logo.bin" in delta.changed_files
    assert "logo.bin" in delta.binary_files


def test_unicode_filename_roundtrip(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"a.txt": "a\n"})
    _write(repo, "你好世界-文件.txt", "user-unicode\n")
    task = _capture(service, store)
    assert any("你好世界" in n for n in task.baseline.preexisting_untracked_files)
    _write(repo, "你好世界-文件.txt", "user-unicode\nAGENT-UNICODE\n")
    delta = service.task_delta(task)
    assert any("你好世界" in n for n in delta.changed_files)
    assert "+AGENT-UNICODE" in delta.text_diff


def test_filename_with_spaces_roundtrip(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"a.txt": "a\n"})
    _write(repo, "my file with spaces.txt", "user\n")
    task = _capture(service, store)
    _write(repo, "my file with spaces.txt", "user\nAGENT\n")
    delta = service.task_delta(task)
    assert any("my file with spaces.txt" in n for n in delta.changed_files)
    assert "+AGENT" in delta.text_diff


# ---------------------------------------------------------------------------
# 13-15. agent-side additions / deletions / renames
# ---------------------------------------------------------------------------
def test_agent_creates_new_file(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"a.txt": "a\n"})
    task = _capture(service, store)
    _write(repo, "new_b.py", "x = 1\n")
    delta = service.task_delta(task)
    assert "new_b.py" in delta.changed_files
    assert "+x = 1" in delta.text_diff


def test_agent_deletes_tracked_file(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"victim.txt": "content\n"})
    task = _capture(service, store)
    (repo / "victim.txt").unlink()
    delta = service.task_delta(task)
    assert any(e.status == "D" and e.new_path == "victim.txt" for e in delta.name_status)


def test_agent_rename_detected(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"rename_me.txt": "content-xyz\n"})
    task = _capture(service, store)
    (repo / "rename_me.txt").rename(repo / "renamed_target.txt")
    delta = service.task_delta(task)
    rename = [e for e in delta.name_status if e.status.startswith("R")]
    assert rename, delta.name_status
    assert rename[0].old_path == "rename_me.txt"
    assert rename[0].new_path == "renamed_target.txt"


# ---------------------------------------------------------------------------
# 16. ignored files stay out
# ---------------------------------------------------------------------------
def test_ignored_files_excluded_from_baseline_and_delta(tmp_path):
    repo, store, service, _ = _setup(
        tmp_path, {"a.txt": "a\n", ".gitignore": "*.tmp\n"}
    )
    _write(repo, "ignored.tmp", "junk\n")
    task = _capture(service, store)
    assert task.baseline.preexisting_untracked_files == []
    _write(repo, "ignored.tmp", "more junk\n")
    assert service.task_delta(task).changed_files == []


# ---------------------------------------------------------------------------
# 17-19. persistence / reconstruction / corruption
# ---------------------------------------------------------------------------
def test_process_restart_delta_identical(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"a.txt": "base\n"})
    _write(repo, "a.txt", "base\nUSER\n")
    task = _capture(service, store)
    _write(repo, "a.txt", "base\nUSER\nAGENT\n")
    delta1 = service.task_delta(task)

    # fresh service + fresh store instance == process restart
    runner2 = CommandRunner()
    store2 = ArtifactStore(repo)
    service2 = BaselineService(repo, runner2, store2, default_config())
    task2 = store2.read_task(task.task_id)
    delta2 = service2.task_delta(task2)
    assert delta2.changed_files == delta1.changed_files
    assert delta2.text_diff == delta1.text_diff


def test_reconstruction_when_baseline_tree_object_unavailable(tmp_path):
    repo, store, service, runner = _setup(tmp_path, {"a.txt": "base\n"})
    _write(repo, "notes.txt", "untracked-user\n")
    task = _capture(service, store)
    _write(repo, "a.txt", "base\nAGENT_A\n")
    expected = service.task_delta(task)

    # remove the unreferenced baseline tree object (worst case: git gc)
    tree = task.baseline.baseline_worktree_tree_sha
    runner.run(["git", "-C", str(repo), "reflog", "expire", "--expire=now", "--all"])
    runner.run(["git", "-C", str(repo), "gc", "--prune=now"])
    probe = runner.run(["git", "-C", str(repo), "cat-file", "-e", tree])
    assert probe.exit_code != 0  # tree object really is gone

    delta = service.task_delta(task)  # must reconstruct from durable artifacts
    assert delta.method == "reconstructed"
    assert delta.text_diff == expected.text_diff
    assert delta.changed_files == expected.changed_files
    assert "+AGENT_A" in delta.text_diff
    assert delta.from_tree == tree  # reconstructed tree matches recorded sha


def test_manifest_corruption_is_explicit_error_not_guess(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"a.txt": "a\n"})
    task = _capture(service, store)
    manifest = store.baseline_dir(task.task_id) / "manifest.json"
    manifest.write_text("{ this is not json", encoding="utf-8")
    with pytest.raises(BaselineCorruptError):
        service.task_delta(task)


def test_baseline_json_corruption_is_explicit_error(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"a.txt": "a\n"})
    task = _capture(service, store)
    baseline_file = store.baseline_dir(task.task_id) / "baseline.json"
    baseline_file.unlink()
    with pytest.raises(BaselineCorruptError):
        service.task_delta(task)


# ---------------------------------------------------------------------------
# 20-21. real index safety + temp cleanup
# ---------------------------------------------------------------------------
def _real_index_bytes(repo: Path) -> bytes:
    return (repo / ".git" / "index").read_bytes()


def test_capture_never_modifies_real_index(tmp_path):
    repo, store, service, runner = _setup(tmp_path, {"a.txt": "a\n"})
    _write(repo, "a.txt", "a\nUSER\n")
    _write(repo, "staged.txt", "s\n")
    _env_git(repo, "add", "staged.txt")
    before = _real_index_bytes(repo)
    task = _capture(service, store)
    _write(repo, "a.txt", "a\nUSER\nAGENT\n")
    service.task_delta(task)
    service.task_delta(task)
    after = _real_index_bytes(repo)
    assert hashlib.sha256(before).hexdigest() == hashlib.sha256(after).hexdigest()
    # and staging state survived: staged.txt is still staged
    status = runner.run(["git", "-C", str(repo), "status", "--porcelain"]).stdout
    assert "A  staged.txt" in status or "M  staged.txt" in status


def test_temporary_index_files_are_cleaned_up(tmp_path):
    repo, store, service, _ = _setup(tmp_path, {"a.txt": "a\n"})
    _write(repo, "a.txt", "a\nUSER\n")
    task = _capture(service, store)
    service.task_delta(task)
    baseline_dir = store.baseline_dir(task.task_id)
    names = {p.name for p in baseline_dir.iterdir()}
    assert names == {"baseline.json", "manifest.json", "tracked.patch", "files"}
    assert not any("index" in n for n in names)
    assert not [p for p in baseline_dir.rglob("*.tmp")]
