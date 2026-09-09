"""Repository policy postcondition guard.

Every Codex implement/fix pass is wrapped in pre/post repository snapshots.
DevRelay then compares control state - HEAD, branch, tags, other local refs
and the REAL git index - and produces structured :class:`PolicyViolation`
records instead of string-only logs.

DevRelay never repairs repository state automatically: violations route the
task to BLOCKED and the human decides (``devrelay unblock --reason ...``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from devrelay.baseline.capture import run_git
from devrelay.config import GitPolicyConfig
from devrelay.errors import BaselineError
from devrelay.models import (
    PolicyViolation,
    PolicyViolationType,
    RepoSnapshot,
    Severity,
    utcnow_iso,
)
from devrelay.workspace.runner import CommandRunner

_GIT_TIMEOUT = 300.0


def _run(root: Path, runner: CommandRunner, args: list[str]) -> str:
    result = runner.run(
        ["git", "-C", str(root), *args],
        cwd=root,
        timeout_seconds=_GIT_TIMEOUT,
    )
    if result.error is not None or result.exit_code != 0:
        raise BaselineError(
            f"git {' '.join(args[:4])} failed: "
            f"{(result.stderr or result.stdout or '').strip()[:1000]}"
        )
    return result.stdout


class RepoGuard:
    """Read-only repository state snapshots + policy comparison."""

    def __init__(self, root: Path, runner: CommandRunner) -> None:
        self.root = Path(root)
        self.runner = runner

    # ------------------------------------------------------------------
    def snapshot(self, note: str = "") -> RepoSnapshot:
        head = None
        branch = None
        try:
            head = _run(self.root, self.runner, ["rev-parse", "HEAD"]).strip() or None
        except BaselineError:
            head = None
        try:
            branch = (
                _run(self.root, self.runner, ["rev-parse", "--abbrev-ref", "HEAD"])
                .strip()
                or None
            )
        except BaselineError:
            branch = None
        index_tree = None
        try:
            index_tree = _run(self.root, self.runner, ["write-tree"]).strip() or None
        except BaselineError:
            index_tree = None  # unmerged index etc. -> skipped, never guessed
        refs = sorted(
            line
            for line in _run(
                self.root, self.runner, ["for-each-ref", "--format=%(refname) %(objectname)"]
            ).splitlines()
            if line.strip()
        )
        tags = sorted(
            line for line in refs if line.startswith("refs/tags/")
        )
        return RepoSnapshot(
            head_sha=head,
            branch=branch,
            index_tree_sha=index_tree,
            local_refs=refs,
            tags=tags,
            note=note,
        )

    # ------------------------------------------------------------------
    def check_policy(
        self,
        before: RepoSnapshot,
        after: RepoSnapshot,
        git: GitPolicyConfig,
    ) -> list[PolicyViolation]:
        violations: list[PolicyViolation] = []

        if before.head_sha != after.head_sha:
            violations.append(
                PolicyViolation(
                    id="",
                    type=PolicyViolationType.UNEXPECTED_HEAD_CHANGE,
                    severity=Severity.P0,
                    before={"head": before.head_sha},
                    after={"head": after.head_sha},
                    description=(
                        "HEAD changed during the provider run "
                        f"({before.head_sha or '-'} -> {after.head_sha or '-'}). "
                        "DevRelay does not auto-reset; unblock after deciding."
                    ),
                    blocking=not git.allow_commit,
                )
            )
        if before.branch != after.branch:
            violations.append(
                PolicyViolation(
                    id="",
                    type=PolicyViolationType.UNEXPECTED_BRANCH_CHANGE,
                    severity=Severity.P0,
                    before={"branch": before.branch},
                    after={"branch": after.branch},
                    description=(
                        f"branch switched during the provider run "
                        f"({before.branch or '-'} -> {after.branch or '-'})."
                    ),
                    blocking=True,
                )
            )
        if before.tags != after.tags:
            violations.append(
                PolicyViolation(
                    id="",
                    type=PolicyViolationType.UNEXPECTED_TAG_CHANGE,
                    severity=Severity.P0,
                    before={"tags": "\n".join(before.tags)},
                    after={"tags": "\n".join(after.tags)},
                    description="tags created/deleted/moved during the provider run.",
                    blocking=not git.allow_tag,
                )
            )

        # Other local refs (heads beyond the current branch, remotes, notes).
        current_head_ref = f"refs/heads/{after.branch}" if after.branch else None

        def other_refs(snapshot: RepoSnapshot) -> list[str]:
            kept = []
            for line in snapshot.local_refs:
                if line.startswith("refs/tags/"):
                    continue
                refname = line.split(" ", 1)[0]
                if refname == current_head_ref:
                    continue
                kept.append(line)
            return kept

        if other_refs(before) != other_refs(after):
            violations.append(
                PolicyViolation(
                    id="",
                    type=PolicyViolationType.UNEXPECTED_REF_CHANGE,
                    severity=Severity.P1,
                    before={"refs": "\n".join(other_refs(before))},
                    after={"refs": "\n".join(other_refs(after))},
                    description="unexpected local ref mutation during the provider run.",
                    blocking=True,
                )
            )
        if (
            before.index_tree_sha is not None
            and after.index_tree_sha is not None
            and before.index_tree_sha != after.index_tree_sha
        ):
            violations.append(
                PolicyViolation(
                    id="",
                    type=PolicyViolationType.UNEXPECTED_INDEX_MUTATION,
                    severity=Severity.P1,
                    before={"index_tree": before.index_tree_sha},
                    after={"index_tree": after.index_tree_sha},
                    description=(
                        "the real git index staging state changed during the "
                        "provider run. Worktree edits never need staging; "
                        "DevRelay will not auto-unstage."
                    ),
                    blocking=not git.allow_index_mutation,
                )
            )
        return violations
