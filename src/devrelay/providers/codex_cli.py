"""Official Codex CLI implementer provider.

Security contract (enforced here):

* never requires or reads OPENAI_API_KEY;
* never reads, copies or parses ChatGPT/Codex credential files;
* never touches browser sessions or undocumented auth endpoints;
* the user is responsible for installing and authenticating the official
  Codex CLI (`codex login` / `codex --version`);
* Codex is executed via argv (shell=False) inside the workspace with a
  configurable timeout; stdout/stderr/exit code/duration are returned as a
  structured :class:`ProviderExecutionResult` (never an uncaught crash).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from devrelay.config import CodexConfig
from devrelay.errors import ProviderUnavailableError
from devrelay.models import ProviderExecutionResult, TaskPacket
from devrelay.providers.base import ImplementerContext, ImplementerProvider
from devrelay.workspace.runner import CommandRunner


def build_implementation_prompt(context: ImplementerContext) -> str:
    """The exact prompt DevRelay sends to Codex (pure function, unit-tested)."""
    packet = context.packet
    lines = [
        "You are the implementation agent.",
        "",
        f"Task: {context.task_id} — {packet.title or '(untitled)'}",
        f"Workspace (work only inside it): {context.workspace_root}",
        f"Implementation attempt: {context.attempt}",
        "",
        "## Objective",
        "",
        packet.objective or "(no objective written)",
        "",
    ]

    def section(heading: str, items: list[str]) -> None:
        if not items:
            return
        lines.append(f"## {heading}")
        lines.append("")
        lines.extend(f"- {item}" for item in items)
        lines.append("")

    section("Scope (implement ONLY this)", packet.scope)
    section("Out of Scope (do NOT touch)", packet.out_of_scope)
    section("Acceptance Criteria", packet.acceptance_criteria)
    section("Constraints", packet.constraints)
    section("Tests Required", packet.tests_required)

    if packet.notes:
        lines += ["## Notes", "", packet.notes, ""]

    if context.is_fix and context.findings:
        lines.append("## Reviewer findings to fix in THIS iteration")
        lines.append("")
        for finding in context.findings:
            lines.append(
                f"- [{finding.severity.value}] {finding.title}: "
                f"{finding.description} (evidence: {finding.evidence})"
            )
            if finding.recommendation:
                lines.append(f"  Recommended: {finding.recommendation}")
        lines.append("")

    lines += [
        "## Working rules",
        "",
        "- Work only inside the provided workspace.",
        "- Implement only the current Task Packet.",
        "- Do not re-review previously approved scope unless the current delta can affect it.",
        "- Current delta first.",
        "- Do not perform unrelated refactors.",
        "- Do not push, merge, tag, reset --hard or delete branches. Do not commit.",
        "- Preserve unrelated user changes.",
        "- Run targeted tests first.",
        "- Do not run full regression unless the task policy explicitly requires it.",
        "",
        "## Required completion report (end your response with these sections)",
        "",
        "CHANGED_FILES",
        "IMPLEMENTATION_SUMMARY",
        "TESTS_RUN",
        "TEST_RESULTS",
        "KNOWN_RISKS",
        "UNRESOLVED_ITEMS",
    ]
    return "\n".join(lines)


class CodexCLIProvider(ImplementerProvider):
    """Runs the official ``codex`` CLI via subprocess (shell=False)."""

    name = "codex"

    def __init__(
        self,
        config: CodexConfig,
        runner: CommandRunner | None = None,
        workspace_root: str | Path | None = None,
    ) -> None:
        self.config = config
        self.runner = runner or CommandRunner()
        self.workspace_root = str(Path(workspace_root).resolve()) if workspace_root else None
        self._availability: tuple[bool, str] | None = None

    def availability(self) -> tuple[bool, str]:
        if self._availability is not None:
            return self._availability
        if not self.runner.which(self.config.executable):
            self._availability = (
                False,
                "Codex CLI is not installed or not available on PATH.",
            )
            return self._availability
        probe = self.runner.run(
            [self.config.executable, "--version"], timeout_seconds=30
        )
        if probe.success:
            self._availability = (True, f"Codex CLI found: {probe.stdout.strip()}")
        else:
            self._availability = (
                False,
                "Codex CLI is installed but the version probe failed "
                f"(exit {probe.exit_code}): {probe.stderr.strip() or probe.error}",
            )
        return self._availability

    def run(self, context: ImplementerContext) -> ProviderExecutionResult:
        available, diagnostic = self.availability()
        if not available:
            return ProviderExecutionResult(
                exit_code=None,
                stderr=diagnostic,
                error=diagnostic,
            )
        prompt = build_implementation_prompt(context)
        argv = [self.config.executable, *self.config.args]
        stdin: str | None = None
        if self.config.prompt_mode == "argv":
            argv.append(prompt)
        else:
            stdin = prompt

        result = self.runner.run(
            argv,
            cwd=context.workspace_root or self.workspace_root,
            timeout_seconds=self.config.timeout_seconds,
            input_text=stdin,
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        # Prefer the structured report inside stdout; keep raw stdout for logs.
        report = stdout.strip()
        return ProviderExecutionResult(
            exit_code=result.exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=result.duration_seconds,
            timed_out=result.timed_out,
            error=result.error,
            report=report,
        )
