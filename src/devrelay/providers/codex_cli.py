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

import hashlib
import re
from pathlib import Path
from typing import Optional

from devrelay.artifacts.store import ArtifactStore
from devrelay.config import CodexConfig
from devrelay.errors import ProviderUnavailableError
from devrelay.models import ProviderExecutionResult, TaskPacket
from devrelay.providers.base import ImplementerContext, ImplementerProvider, RuntimePlan
from devrelay.providers.codex_runtime import (
    CodexChildRunner,
    CodexContainmentUnsupportedError,
    CodexResultError,
    CodexRuntimeUnsupportedError,
    build_invocation,
    detect_capabilities,
    detect_repo_codex_config,
    observe_events,
    parse_result_bytes,
    result_json_schema,
    write_json_new,
    write_text_new,
)
from devrelay.redact import sanitize
from devrelay.workspace.containment import (
    ContainmentError,
    ContainmentUnsupportedError,
    containment_support,
    create_containment,
)
from devrelay.workspace.runner import CommandRunner

_FLAG_RE = re.compile(r"^\s+--([a-z0-9-]+)", re.IGNORECASE)


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
                f"- [{finding.severity.value}] id={finding.id or 'n/a'} "
                f"title={finding.title}"
            )
            if finding.description:
                lines.append(f"  description: {finding.description}")
            if finding.files:
                lines.append(f"  files: {', '.join(finding.files)}")
            if finding.evidence:
                lines.append(f"  evidence: {finding.evidence}")
            if finding.recommendation:
                lines.append(f"  recommendation: {finding.recommendation}")
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
        "",
        "The structured result schema handed to you with --output-schema is",
        "strict: every field is required and unknown fields are rejected. Emit",
        "every field, using [] for empty lists (changed_files, tests_run,",
        "unresolved_items, known_risks), \"\" for an empty summary or note, and",
        "one of the allowed status values. --output-schema is the authority; do",
        "not invent fields.",
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
        # P1-A: every Codex child (probes included) is spawned through the
        # scrubbing adapter, so no call site can forget the credential denylist.
        self.runner = CodexChildRunner(runner or CommandRunner())
        self.workspace_root = str(Path(workspace_root).resolve()) if workspace_root else None
        self._availability: tuple[bool, str] | None = None
        self._help_flags: set[str] | None = None

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

    # -- CLI help verification (never invokes a model) -----------------
    def _exec_help_flags(self) -> set[str]:
        if self._help_flags is not None:
            return self._help_flags
        probe = self.runner.run(
            [self.config.executable, "exec", "--help"], timeout_seconds=60
        )
        flags: set[str] = set()
        if probe.success:
            for line in probe.stdout.splitlines():
                for match in re.finditer(
                    r"(?<![A-Za-z0-9])--([a-z0-9-]+)", line, re.IGNORECASE
                ):
                    flags.add("--" + match.group(1).lower())
        self._help_flags = flags
        return flags

    def unknown_arg_warnings(self) -> list[str]:
        """Flags configured in ``codex.args`` missing from ``codex exec --help``."""
        if not self.runner.which(self.config.executable):
            return []
        available = self._exec_help_flags()
        if not available:
            return []
        warnings: list[str] = []
        for token in self.config.args:
            if not token.startswith("--"):
                continue
            name = token.split("=", 1)[0].lower()
            if name not in available:
                warnings.append(
                    f"configured codex arg '{name}' is not present in the "
                    "installed CLI's `codex exec --help`; the run will be "
                    "rejected before starting."
                )
        return warnings

    # -- v0.2-C structured runtime preparation (never invokes a model) ----
    def prepare_runtime(
        self,
        context: ImplementerContext,
        *,
        attempt_id: str,
        call_id: str,
        runtime_dir: Path,
        staging_dir: Path,
        runtime_mode: str,
    ) -> RuntimePlan:
        """Detect capabilities, honour the repo-config gate and build argv.

        Writes the parent-owned request/schema/runtime artifacts *before* the
        control-plane PRE manifest is captured, so nothing DevRelay writes can
        later look like a child mutation.
        """
        capabilities = detect_capabilities(
            self.runner,
            self.config.executable,
            getattr(self.config, "launcher_args", ()) or (),
        )
        if not capabilities.present:
            raise CodexRuntimeUnsupportedError(
                f"Codex CLI unavailable: {capabilities.diagnostic}"
            )
        if runtime_mode == "structured":
            if not capabilities.structured_supported:
                raise CodexRuntimeUnsupportedError(
                    "structured runtime requested but the installed Codex CLI "
                    "does not support "
                    + ", ".join(capabilities.missing_structured_flags())
                    + "; set codex.runtime_mode: text explicitly to use the "
                    "legacy text runtime (DevRelay never downgrades silently)"
                )
            supported, diagnostic = containment_support()
            if not supported:
                raise CodexContainmentUnsupportedError(
                    "structured runtime requires strong descendant containment "
                    f"so that nothing the Codex child spawns can outlive the "
                    f"control-plane check, but {diagnostic}. Set "
                    "codex.runtime_mode: text explicitly to use the legacy text "
                    "runtime (DevRelay never downgrades silently)"
                )
            repo_config = detect_repo_codex_config(Path(context.workspace_root))
            if repo_config:
                raise CodexRuntimeUnsupportedError(
                    "repository Codex configuration is not supported in "
                    "structured mode (it can change sandbox/tool/runtime "
                    "controls indirectly): "
                    + ", ".join(repo_config)
                    + "; remove it or set codex.runtime_mode: text explicitly"
                )
        prompt = context.prompt or build_implementation_prompt(context)
        runtime_dir = Path(runtime_dir)
        runtime_dir.mkdir(parents=True, exist_ok=True)
        schema_path = runtime_dir / "schema.json"
        staging_path = Path(staging_dir) / "last-message.raw.json"
        if not schema_path.exists():
            write_json_new(schema_path, result_json_schema())
        invocation = build_invocation(
            config=self.config,
            capabilities=capabilities,
            workdir=Path(context.workspace_root),
            prompt=prompt,
            staging_path=staging_path,
            schema_path=schema_path,
            runtime_mode=runtime_mode,
        )
        runtime_json = runtime_dir / "runtime.json"
        if not runtime_json.exists():
            write_json_new(
                runtime_json,
                {
                    "attempt_id": attempt_id,
                    "call_id": call_id,
                    "runtime_mode": runtime_mode,
                    "capabilities": invocation.describe(),
                    "timeout_seconds": self.config.timeout_seconds,
                    "max_result_bytes": self.config.max_result_bytes,
                    "max_capture_bytes": self.config.max_capture_bytes,
                },
            )
        request_path = runtime_dir / "request.sanitized.txt"
        if not request_path.exists():
            write_text_new(request_path, sanitize(prompt))
        return RuntimePlan(
            runtime_mode=runtime_mode,
            argv=invocation.argv,
            env_remove=invocation.env_remove,
            staging_path=str(staging_path),
            schema_path=str(schema_path),
            workdir=str(Path(context.workspace_root)),
            prompt=prompt,
            attempt_id=attempt_id,
            call_id=call_id,
            capabilities=capabilities.describe(),
        )

    def _run_structured(
        self, context: ImplementerContext, plan: RuntimePlan
    ) -> ProviderExecutionResult:
        """Spawn Codex with the DevRelay-owned argv and collect the result."""
        try:
            containment = create_containment()
        except (ContainmentUnsupportedError, ContainmentError) as exc:
            # The pre-flight gate should have refused already; fail closed
            # rather than spawning without containment.
            return ProviderExecutionResult(
                exit_code=None,
                stderr=str(exc),
                error=(
                    "codex_process_containment_unsupported: strong descendant "
                    f"containment is unavailable ({exc}); refusing to spawn"
                ),
                runtime_mode=plan.runtime_mode,
            )
        try:
            result = self.runner.run(
                plan.argv,
                cwd=plan.workdir,
                timeout_seconds=self.config.timeout_seconds,
                input_text=plan.prompt,
                env_remove=plan.env_remove,
                max_capture_bytes=self.config.max_capture_bytes,
                containment=containment,
            )
        finally:
            try:
                containment.close()
            except Exception:  # pragma: no cover - defensive
                pass
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        observation = observe_events(stdout)
        warnings: list[str] = []
        if not observation.types:
            warnings.append("no JSONL events observed (observational only)")
        warnings.extend(observation.parse_warnings[:5])
        outcome = ProviderExecutionResult(
            exit_code=result.exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=result.duration_seconds,
            timed_out=result.timed_out,
            error=result.error,
            report=stdout.strip(),
            runtime_mode=plan.runtime_mode,
            staging_path=plan.staging_path,
            argv=list(plan.argv),
            env_removed=list(plan.env_remove),
            capabilities=plan.capabilities,
            session_id=observation.session_id,
            events_summary=observation.to_json(),
            runtime_warnings=warnings,
            stdout_bytes_total=result.stdout_bytes_total,
            stderr_bytes_total=result.stderr_bytes_total,
            stdout_truncated=result.stdout_truncated,
            stderr_truncated=result.stderr_truncated,
            containment=result.containment,
            containment_all_dead=result.containment_all_dead,
            containment_error=result.containment_error,
        )
        if result.timed_out or result.error or result.exit_code is None:
            return outcome
        # Read the model result with a hard cap *before* parsing anything.
        staging = Path(plan.staging_path)
        try:
            data, size, truncated = ArtifactStore.read_bytes_bounded(
                staging, self.config.max_result_bytes
            )
        except OSError:
            outcome.result_error_code = "codex_result_missing"
            outcome.result_error = (
                "Codex did not write the structured result file "
                f"({plan.staging_path}); the run cannot be treated as complete"
            )
            return outcome
        outcome.result_bytes_total = size
        outcome.raw_result_sha256 = hashlib.sha256(data).hexdigest()
        if truncated:
            outcome.result_error_code = "codex_result_too_large"
            outcome.result_error = (
                f"structured result is {size} bytes, above the configured "
                f"{self.config.max_result_bytes}-byte cap; DevRelay refuses to "
                "read or guess it"
            )
            return outcome
        try:
            parsed, rejected, unknown = parse_result_bytes(data)
        except CodexResultError as exc:
            outcome.result_error_code = getattr(exc, "code", "codex_result_malformed")
            outcome.result_error = str(exc)
            return outcome
        outcome.structured_result = parsed
        outcome.rejected_path_claims = rejected
        outcome.unknown_result_fields = unknown
        if rejected:
            outcome.runtime_warnings.append(
                f"{len(rejected)} rejected path claim(s) (traversal/absolute)"
            )
        if unknown:
            outcome.runtime_warnings.append(
                "unknown result field(s): " + ", ".join(unknown[:5])
            )
        return outcome

    def run(self, context: ImplementerContext) -> ProviderExecutionResult:
        available, diagnostic = self.availability()
        if not available:
            return ProviderExecutionResult(
                exit_code=None,
                stderr=diagnostic,
                error=diagnostic,
            )
        plan = context.plan
        if plan is not None and plan.runtime_mode == "structured":
            return self._run_structured(context, plan)
        unknown = self.unknown_arg_warnings()
        if unknown:
            message = (
                "Codex CLI invocation rejected before start: "
                + " ".join(unknown)
            )
            return ProviderExecutionResult(
                exit_code=None, stderr=message, error=message
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
