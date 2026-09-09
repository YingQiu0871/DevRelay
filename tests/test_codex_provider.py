"""Codex CLI provider tests: prompt policy, availability, success/failure."""

from devrelay.config import CodexConfig
from devrelay.models import Finding, ProviderExecutionResult, Severity
from devrelay.providers.base import ImplementerContext
from devrelay.providers.codex_cli import (
    CodexCLIProvider,
    build_implementation_prompt,
)

from helpers import FakeCommandRunner, cmd_result, make_packet


def _context(*, is_fix=False, findings=None, attempt=1):
    return ImplementerContext(
        task_id="DR-0001",
        packet=make_packet(),
        attempt=attempt,
        workspace_root="/fake/ws",
        is_fix=is_fix,
        findings=findings or [],
    )


def test_prompt_contains_policy_and_report_sections():
    prompt = build_implementation_prompt(_context())
    for required in (
        "You are the implementation agent.",
        "Work only inside the provided workspace",
        "Do not re-review previously approved scope",
        "Current delta first.",
        "Do not perform unrelated refactors.",
        "Do not push, merge, tag, reset --hard or delete branches. Do not commit.",
        "Run targeted tests first.",
        "CHANGED_FILES",
        "IMPLEMENTATION_SUMMARY",
        "KNOWN_RISKS",
        "UNRESOLVED_ITEMS",
        "Acceptance Criteria",
        "Out of Scope",
    ):
        assert required in prompt


def test_fix_prompt_embeds_findings():
    finding = Finding(
        severity=Severity.P1,
        title="Null slot fallback missing",
        description="occurs on empty slot",
        evidence="trace",
        recommendation="add fallback",
    )
    prompt = build_implementation_prompt(_context(is_fix=True, findings=[finding]))
    assert "[P1]" in prompt
    assert "Null slot fallback missing" in prompt
    assert "add fallback" in prompt


def test_codex_missing_on_path_reports_clean_error():
    runner = FakeCommandRunner()
    runner.which_map["codex"] = None
    provider = CodexCLIProvider(CodexConfig(), runner=runner, workspace_root="/fake/ws")
    ok, diagnostic = provider.availability()
    assert ok is False
    assert "Codex CLI is not installed" in diagnostic
    result = provider.run(_context())
    assert isinstance(result, ProviderExecutionResult)
    assert result.error is not None
    assert "Codex CLI is not installed" in result.error
    assert result.exit_code is None
    assert not result.success
    # No credential probing happened: only one command family is allowed
    assert all(call["argv"][0] == "codex" for call in runner.calls) or runner.calls == []


def test_codex_subprocess_success_streams_prompt_on_stdin():
    runner = FakeCommandRunner(
        results={"codex exec --full-auto": cmd_result(stdout="CHANGED_FILES\nok")}
    )
    provider = CodexCLIProvider(
        CodexConfig(timeout_seconds=123.0), runner=runner, workspace_root="/fake/ws"
    )
    result = provider.run(_context())
    assert result.success
    assert result.exit_code == 0
    assert result.report == "CHANGED_FILES\nok"
    exec_call = next(c for c in runner.calls if "exec" in c["argv"])
    assert exec_call["cwd"] == "/fake/ws"
    assert exec_call["timeout"] == 123.0
    assert exec_call["argv"] == ["codex", "exec", "--full-auto"]
    assert exec_call["input"] is not None  # stdin mode
    assert "You are the implementation agent." in exec_call["input"]


def test_codex_subprocess_failure_is_result_not_crash():
    runner = FakeCommandRunner(
        results={
            "codex exec --full-auto": cmd_result(
                exit_code=3, stderr="session failed", stdout="partial"
            )
        }
    )
    provider = CodexCLIProvider(CodexConfig(), runner=runner, workspace_root="/fake/ws")
    result = provider.run(_context())
    assert result.exit_code == 3
    assert not result.success
    assert "session failed" in result.stderr


def test_codex_timeout_is_reported():
    runner = FakeCommandRunner(
        results={
            "codex exec --full-auto": cmd_result(
                exit_code=None, timed_out=True, error="timed out"
            )
        }
    )
    provider = CodexCLIProvider(CodexConfig(), runner=runner, workspace_root="/fake/ws")
    result = provider.run(_context())
    assert result.timed_out
    assert not result.success


def test_argv_prompt_mode_appends_prompt_argument():
    runner = FakeCommandRunner(results={})
    config = CodexConfig(prompt_mode="argv", args=["exec"])
    provider = CodexCLIProvider(config, runner=runner, workspace_root="/fake/ws")
    provider.run(_context())
    exec_call = next(c for c in runner.calls if "exec" in c["argv"])
    assert exec_call["argv"][:2] == ["codex", "exec"]
    assert "You are the implementation agent." in exec_call["argv"][-1]
    assert exec_call["input"] is None
