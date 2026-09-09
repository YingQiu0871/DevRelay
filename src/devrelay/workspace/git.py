"""Git-backed workspace abstraction.

DevRelay records the workspace state when a task starts (HEAD SHA, branch,
preexisting dirty files) so later reports can distinguish what the agent
changed from what was already there.  DevRelay itself never commits, pushes,
tags, resets or deletes branches.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from devrelay.errors import WorkspaceError
from devrelay.models import WorkspaceSnapshot
from devrelay.workspace.runner import CommandRunner


class GitWorkspace:
    """Read-only git access used for snapshots, diffs and status."""

    def __init__(self, root: str | Path, runner: CommandRunner | None = None) -> None:
        self.root = Path(root).resolve()
        self.runner = runner or CommandRunner()
        if not self.root.is_dir():
            raise WorkspaceError(f"workspace does not exist: {self.root}")

    # -- detection --------------------------------------------------------
    def detect_repo(self) -> bool:
        result = self.runner.run(
            ["git", "-C", str(self.root), "rev-parse", "--is-inside-work-tree"],
            cwd=self.root,
            timeout_seconds=30,
        )
        return result.success and result.stdout.strip().lower() == "true"

    def require_repo(self) -> None:
        if not self.detect_repo():
            raise WorkspaceError(
                f"{self.root} is not a git repository. "
                "DevRelay tasks operate inside git workspaces; run "
                "'git init' first if this is a new project."
            )

    # -- git queries ------------------------------------------------------
    def _git(self, *args: str) -> str:
        self.require_repo()
        result = self.runner.run(
            ["git", "-C", str(self.root), *args],
            cwd=self.root,
            timeout_seconds=120,
        )
        if result.error is not None:
            raise WorkspaceError(f"git failed: {result.error}")
        if result.exit_code != 0:
            raise WorkspaceError(
                f"git {' '.join(args)} failed (exit {result.exit_code}): "
                f"{result.stderr.strip()[:2000]}"
            )
        return result.stdout

    def head_sha(self) -> str | None:
        try:
            return self._git("rev-parse", "HEAD").strip() or None
        except WorkspaceError:
            return None

    def current_branch(self) -> str | None:
        try:
            return self._git("rev-parse", "--abbrev-ref", "HEAD").strip() or None
        except WorkspaceError:
            return None

    def status(self) -> str:
        return self._git("--no-optional-locks", "status", "--porcelain=v1")

    def is_dirty(self) -> bool:
        return bool(self.status().strip())

    def changed_name_only(self) -> list[str]:
        """Names of tracked modifications plus untracked (non-ignored) files."""
        tracked = self._git("diff", "--name-only", "HEAD").splitlines()
        untracked = self._git("ls-files", "--others", "--exclude-standard").splitlines()
        names: list[str] = []
        for name in [*tracked, *untracked]:
            cleaned = name.strip()
            if cleaned and cleaned not in names:
                names.append(cleaned)
        return names

    def diff(self, stat: bool = False) -> str:
        args = ["diff", "--stat", "HEAD"] if stat else ["diff", "HEAD"]
        body = self._git(*args)
        untracked = self._git("ls-files", "--others", "--exclude-standard").splitlines()
        if untracked:
            untracked_note = (
                "\n# Untracked files (not part of git diff):\n"
                + "\n".join(f"#   {name}" for name in untracked)
            )
            body = f"{body}{untracked_note}" if body else untracked_note
        return body

    # -- snapshot ---------------------------------------------------------
    def snapshot(self) -> WorkspaceSnapshot:
        if not self.detect_repo():
            return WorkspaceSnapshot(
                repo_root=str(self.root),
                head_sha=None,
                branch=None,
                dirty_files=[],
                has_git=False,
            )
        return WorkspaceSnapshot(
            repo_root=str(self.root),
            head_sha=self.head_sha(),
            branch=self.current_branch(),
            dirty_files=self.changed_name_only(),
            has_git=True,
        )
