"""Task-relative delta computation and baseline tree reconstruction.

The reviewer never sees ``git diff HEAD`` any more.  The task delta is always

    task-start baseline tree  ->  current worktree tree

and the baseline tree object is only a fast path: if it has been garbage
collected, the tree is reconstructed from the durable artifacts (original HEAD
tree + ``tracked.patch`` + saved untracked blobs) in another temporary index.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Optional

from devrelay.baseline.capture import (
    TempGitIndex,
    run_git,
    worktree_tree_sha,
)
from devrelay.baseline.store import BaselineStore
from devrelay.errors import BaselineCorruptError, BaselineError
from devrelay.models import (
    NameStatusEntry,
    TaskDelta,
    WorkspaceBaseline,
)
from devrelay.workspace.runner import CommandRunner

_GIT_TIMEOUT = 300.0
_BINARY_DIFF_RE = re.compile(
    r"^Binary files (?:a/)?(.*?) and (?:b/)?(.*?) differ$"
)
_STATUS_TOKEN_RE = re.compile(r"^[ACDMRTUXB][0-9]*$")


def _parse_name_status_z(raw: str) -> list[NameStatusEntry]:
    """Parse ``git diff --name-status -z`` output (rename aware)."""
    tokens = [t for t in raw.split("\0")]
    entries: list[NameStatusEntry] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if not token:
            i += 1
            continue
        if _STATUS_TOKEN_RE.match(token):
            status = token
            if len(status) > 1 and status[1:].isdigit():
                status = status[0] + status[1:]  # keep e.g. R100
            if status[0] in ("R", "C") and i + 2 < len(tokens):
                old_path = tokens[i + 1]
                new_path = tokens[i + 2]
                entries.append(
                    NameStatusEntry(status=status, old_path=old_path, new_path=new_path)
                )
                i += 3
            elif i + 1 < len(tokens):
                new_path = tokens[i + 1]
                entries.append(NameStatusEntry(status=status, new_path=new_path))
                i += 2
            else:
                i += 1
        else:
            # Safety: never guess on malformed records.
            raise BaselineCorruptError(
                "malformed git name-status output; refusing to guess: "
                f"token={token!r}"
            )
    return entries


class BaselineRecovery:
    """Reconstructs a baseline tree from durable artifacts (temp index)."""

    def __init__(self, root: Path, runner: CommandRunner) -> None:
        self.root = Path(root)
        self.runner = runner

    def tree_exists(self, tree_sha: str) -> bool:
        result = self.runner.run(
            ["git", "-C", str(self.root), "cat-file", "-e", tree_sha],
            cwd=self.root,
            timeout_seconds=_GIT_TIMEOUT,
        )
        return result.exit_code == 0

    def reconstruct(
        self,
        baseline: WorkspaceBaseline,
        patch_bytes: bytes,
        read_untracked: Callable[[str], bytes],
    ) -> str:
        """Build the baseline tree in a temp index and verify its SHA."""
        if not baseline.head_sha:
            raise BaselineCorruptError(
                "baseline has no head_sha; cannot reconstruct baseline tree"
            )
        with TempGitIndex(self.root) as tmp:
            run_git(self.root, self.runner, ["read-tree", baseline.head_sha], env=tmp.env)
            if patch_bytes:
                result = self.runner.run(
                    [
                        "git",
                        "-C",
                        str(self.root),
                        "apply",
                        "--cached",
                        "--binary",
                        "-",
                    ],
                    cwd=self.root,
                    env=tmp.env,
                    input_text=patch_bytes.decode("utf-8", errors="replace"),
                    timeout_seconds=_GIT_TIMEOUT,
                )
                if result.exit_code != 0:
                    raise BaselineCorruptError(
                        "cannot apply tracked.patch to the baseline tree: "
                        f"{(result.stderr or '').strip()[:2000]}"
                    )
            for entry in baseline.untracked_entries:
                data = read_untracked(entry.storage_name)
                import tempfile

                with tempfile.TemporaryDirectory(prefix="devrelay-blob-") as td:
                    blob_path = Path(td) / entry.storage_name
                    blob_path.write_bytes(data)
                    blob = run_git(
                        self.root,
                        self.runner,
                        ["hash-object", "-w", str(blob_path)],
                        env=tmp.env,
                    ).strip()
                    run_git(
                        self.root,
                        self.runner,
                        [
                            "update-index",
                            "--add",
                            "--cacheinfo",
                            f"{entry.mode},{blob},{entry.rel_path}",
                        ],
                        env=tmp.env,
                    )
            tree = run_git(self.root, self.runner, ["write-tree"], env=tmp.env).strip()
        if (
            baseline.baseline_worktree_tree_sha
            and tree != baseline.baseline_worktree_tree_sha
        ):
            raise BaselineCorruptError(
                "reconstructed baseline tree does not match the recorded tree "
                f"({tree} != {baseline.baseline_worktree_tree_sha}); refusing "
                "to compute a diff on unverified data"
            )
        return tree


class BaselineComparator:
    """Computes the task-relative delta between two trees."""

    def __init__(self, root: Path, runner: CommandRunner) -> None:
        self.root = Path(root)
        self.runner = runner
        self.recovery = BaselineRecovery(root, runner)

    def ensure_baseline_tree(
        self,
        store: BaselineStore,
        task_id: str,
        baseline: WorkspaceBaseline,
    ) -> tuple[str, str]:
        """Return (usable tree sha, method used)."""
        recorded = baseline.baseline_worktree_tree_sha
        if recorded and self.recovery.tree_exists(recorded):
            return recorded, "trees"
        _, patch_bytes = store.load(task_id)
        reconstructed = self.recovery.reconstruct(
            baseline,
            patch_bytes,
            lambda name: store.read_untracked_file(
                task_id, next(e for e in baseline.untracked_entries if e.storage_name == name)
            ),
        )
        return reconstructed, "reconstructed"

    def diff_trees(
        self,
        base_tree: str,
        current_tree: str,
        method: str = "trees",
    ) -> TaskDelta:
        if base_tree == current_tree:
            return TaskDelta(
                from_tree=base_tree,
                to_tree=current_tree,
                method=method,
            )
        text_diff = run_git(
            self.root,
            self.runner,
            ["diff", "--find-renames", base_tree, current_tree],
        )
        stat_text = run_git(
            self.root,
            self.runner,
            ["diff", "--stat", base_tree, current_tree],
        )
        name_only_raw = run_git(
            self.root,
            self.runner,
            ["diff", "--name-only", "-z", base_tree, current_tree],
        )
        changed = [n for n in name_only_raw.split("\0") if n]
        name_status_raw = run_git(
            self.root,
            self.runner,
            [
                "diff",
                "--name-status",
                "--find-renames",
                "-z",
                base_tree,
                current_tree,
            ],
        )
        name_status = _parse_name_status_z(name_status_raw)
        binary_files: list[str] = []
        for line in text_diff.splitlines():
            match = _BINARY_DIFF_RE.match(line)
            if match:
                for path in (match.group(1), match.group(2)):
                    if path and path not in binary_files:
                        binary_files.append(path)
        return TaskDelta(
            text_diff=text_diff,
            stat_text=stat_text,
            changed_files=changed,
            name_status=name_status,
            binary_files=binary_files,
            from_tree=base_tree,
            to_tree=current_tree,
            method=method,
        )

    def binary_patch(self, base_tree: str, current_tree: str) -> str:
        return run_git(
            self.root,
            self.runner,
            ["diff", "--binary", "--find-renames", base_tree, current_tree],
        )
