"""Baseline capture: build trees from the real worktree with a TEMPORARY index.

Hard rules:

* never run ``git add/reset/checkout/stash/commit`` against the real index;
* every index manipulation runs with ``GIT_INDEX_FILE=<temp>``;
* ignored files are excluded by git itself (plus an explicit
  ``:(exclude).devrelay`` pathspec so DevRelay state never pollutes deltas);
* the temp index is created under a temporary directory and always removed.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import stat as stat_module
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from devrelay.baseline.store import BaselineStore
from devrelay.errors import BaselineError, BaselineSizeError, BaselineUnavailableError
from devrelay.models import (
    BaselineUntrackedEntry,
    WorkspaceBaseline,
    utcnow_iso,
)
from devrelay.workspace.runner import CommandRunner

SELF_PATHPEC = ":(exclude).devrelay"
_GIT_TIMEOUT = 300.0


def _is_self(name: str) -> bool:
    return name == ".devrelay" or name.startswith(".devrelay/")


class TempGitIndex:
    """Context manager: temporary GIT_INDEX_FILE used for tree building."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self._tmp = tempfile.TemporaryDirectory(prefix="devrelay-index-")
        self.index_path = Path(self._tmp.name) / "index"
        self.env = {"GIT_INDEX_FILE": str(self.index_path)}

    def __enter__(self) -> "TempGitIndex":
        return self

    def __exit__(self, *exc) -> None:
        self._tmp.cleanup()


@dataclass
class CapturedBaseline:
    """Everything captured for one task start (persist via BaselineStore)."""

    baseline: WorkspaceBaseline
    patch_bytes: bytes = b""
    untracked_files: list[tuple[str, bytes]] = field(default_factory=list)


def run_git(
    root: Path,
    runner: CommandRunner,
    args: list[str],
    *,
    no_optional_locks: bool = False,
    **kwargs,
) -> str:
    """Run one git command inside the workspace; raise BaselineError on failure."""
    argv = ["git"]
    if no_optional_locks:
        # status can opportunistically refresh (and rewrite) the real index;
        # baseline capture must never touch it, so lock refresh off.
        argv.append("--no-optional-locks")
    result = runner.run(
        [*argv, "-C", str(root), *args],
        cwd=root,
        timeout_seconds=kwargs.pop("timeout", _GIT_TIMEOUT),
        env=kwargs.pop("env", None),
        input_text=kwargs.pop("input_text", None),
        **kwargs,
    )
    if result.error is not None or result.exit_code != 0:
        detail = (result.stderr or result.stdout or "").strip()[:2000]
        raise BaselineError(f"git {' '.join(args[:6])} failed: {detail}")
    return result.stdout


def worktree_tree_sha(root: Path, runner: CommandRunner) -> str:
    """Snapshot the current worktree as a tree using a temporary index.

    Content == HEAD + tracked modifications/deletions + non-ignored untracked
    files (with ``.devrelay`` excluded).  Never touches the real index.
    """
    with TempGitIndex(root) as tmp:
        run_git(root, runner, ["read-tree", "HEAD"], env=tmp.env)
        run_git(
            root,
            runner,
            ["add", "-A", "--", ".", SELF_PATHPEC],
            env=tmp.env,
        )
        tree = run_git(root, runner, ["write-tree"], env=tmp.env).strip()
        if not tree:
            raise BaselineError("git write-tree returned an empty tree sha")
        return tree


def _tracked_changed_names(
    root: Path, runner: CommandRunner, env: dict[str, str] | None = None
) -> list[str]:
    """Tracked changes vs HEAD (staged + unstaged, incl. deletions)."""
    names = []
    raw = runner.run(
        ["git", "-C", str(root), "diff", "--name-only", "-z", "HEAD"],
        cwd=root,
        env=env,
        timeout_seconds=_GIT_TIMEOUT,
    )
    if raw.exit_code != 0:
        raise BaselineError(
            f"git diff --name-only failed: {(raw.stderr or '').strip()[:2000]}"
        )
    for name in raw.stdout.split("\0"):
        if name and not _is_self(name):
            names.append(name)
    return sorted(set(names))


def _untracked_names(root: Path, runner: CommandRunner) -> list[str]:
    raw = runner.run(
        ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=root,
        timeout_seconds=_GIT_TIMEOUT,
    )
    if raw.exit_code != 0:
        raise BaselineError(
            f"git ls-files --others failed: {(raw.stderr or '').strip()[:2000]}"
        )
    names = []
    for name in raw.stdout.split("\0"):
        if name and not _is_self(name):
            names.append(name)
    return sorted(set(names))


def _storage_name(rel_path: str) -> str:
    return hashlib.sha1(rel_path.encode("utf-8")).hexdigest() + ".blob"


def _capture_untracked_files(
    root: Path, names: list[str], max_bytes: int
) -> tuple[list[BaselineUntrackedEntry], list[tuple[str, bytes]]]:
    entries: list[BaselineUntrackedEntry] = []
    blobs: list[tuple[str, bytes]] = []
    for rel_path in names:
        full = (root / rel_path)
        try:
            info = os.lstat(str(full))
        except OSError as exc:
            raise BaselineError(
                f"cannot stat pre-existing untracked file {rel_path!r}: {exc}"
            ) from exc
        if stat_module.S_ISDIR(info.st_mode):
            continue  # git tracks files, not directories
        if info.st_size > max_bytes:
            raise BaselineSizeError(rel_path, info.st_size, max_bytes)
        is_symlink = stat_module.S_ISLNK(info.st_mode)
        if is_symlink:
            try:
                data = os.readlink(str(full)).encode("utf-8")
            except OSError as exc:
                raise BaselineError(
                    f"cannot read symlink target {rel_path!r}: {exc}"
                ) from exc
            mode = "120000"
        else:
            try:
                with open(str(full), "rb") as handle:
                    data = handle.read()
            except OSError as exc:
                raise BaselineError(
                    f"cannot read pre-existing untracked file {rel_path!r}: {exc}"
                ) from exc
            executable = bool(info.st_mode & 0o111)
            mode = "100755" if executable else "100644"
        storage_name = _storage_name(rel_path)
        entries.append(
            BaselineUntrackedEntry(
                rel_path=rel_path,
                storage_name=storage_name,
                size=len(data),
                mode=mode,
                is_symlink=is_symlink,
                sha256=hashlib.sha256(data).hexdigest(),
            )
        )
        blobs.append((storage_name, data))
    return entries, blobs


class BaselineBuilder:
    """Captures the real task-start workspace state (read-only for the user)."""

    def __init__(
        self,
        root: Path,
        runner: CommandRunner,
        max_untracked_file_bytes: int,
    ) -> None:
        self.root = Path(root)
        self.runner = runner
        self.max_untracked_file_bytes = max_untracked_file_bytes

    def capture(self, task_id: str, storage_rel: str) -> CapturedBaseline:
        head = run_git(
            self.root, self.runner, ["rev-parse", "HEAD"]
        ).strip()
        if not head:
            raise BaselineUnavailableError(
                "repository has no commits (unborn HEAD). DevRelay baselines "
                "need at least one commit; commit the initial state first."
            )
        try:
            branch = run_git(
                self.root, self.runner, ["rev-parse", "--abbrev-ref", "HEAD"]
            ).strip()
        except BaselineError:
            branch = None
        # All index-reading git commands run against a CLONE of the real index
        # under a temporary GIT_INDEX_FILE.  Stat refreshes (which `git diff`
        # and friends perform) then write to the clone, never to .git/index.
        with TempGitIndex(self.root) as clone:
            real_index = self.root / ".git" / "index"
            if real_index.is_file():
                shutil.copyfile(str(real_index), str(clone.index_path))
            porcelain_v2 = run_git(
                self.root,
                self.runner,
                ["status", "--porcelain=v2"],
                env=clone.env,
                no_optional_locks=True,
            )
            dirty = _tracked_changed_names(self.root, self.runner, env=clone.env)
            # HEAD -> task-start worktree for tracked files (binary-capable).
            # Byte-exact transport: the patch is binary-sensitive durable data
            # and must never pass through text-mode stdin/stdout translation.
            patch_result = self.runner.run_bytes(
                [
                    "git",
                    "-C",
                    str(self.root),
                    "diff",
                    "HEAD",
                    "--binary",
                    "--find-renames",
                    "--",
                    ".",
                    SELF_PATHPEC,
                ],
                cwd=self.root,
                env=clone.env,
                timeout_seconds=_GIT_TIMEOUT,
            )
            if patch_result.exit_code != 0:
                raise BaselineError(
                    "git diff --binary failed: "
                    f"{patch_result.stderr.decode('utf-8', errors='replace').strip()[:2000]}"
                )
            patch_bytes = patch_result.stdout
            # Real index tree, read through the clone (read-only semantics).
            try:
                index_tree = run_git(
                    self.root,
                    self.runner,
                    ["write-tree"],
                    env=clone.env,
                ).strip() or None
            except BaselineError:
                index_tree = None
        untracked = _untracked_names(self.root, self.runner)
        entries, blobs = _capture_untracked_files(
            self.root, untracked, self.max_untracked_file_bytes
        )

        # Worktree tree via temporary index (HEAD + worktree, no real index).
        tree = worktree_tree_sha(self.root, self.runner)

        baseline = WorkspaceBaseline(
            task_id=task_id,
            head_sha=head,
            branch=branch,
            status_porcelain_v2=porcelain_v2,
            preexisting_dirty_files=dirty,
            preexisting_untracked_files=untracked,
            index_tree_sha=index_tree,
            baseline_worktree_tree_sha=tree,
            baseline_manifest_version=1,
            baseline_storage_path=storage_rel,
            baseline_complete=True,
            untracked_entries=entries,
            notes=(
                "captured via temporary GIT_INDEX_FILE; real git index was "
                "not modified; .devrelay excluded"
            ),
        )
        return CapturedBaseline(
            baseline=baseline,
            patch_bytes=patch_bytes,
            untracked_files=blobs,
        )
