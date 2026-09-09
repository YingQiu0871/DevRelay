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
        results={"codex exec --sandbox workspace-write": cmd_result(stdout="CHANGED_FILES\nok")}
    )
    provider = CodexCLIProvider(
        CodexConfig(timeout_seconds=123.0), runner=runner, workspace_root="/fake/ws"
    )
    result = provider.run(_context())
    assert result.success
    assert result.exit_code == 0
    assert result.report == "CHANGED_FILES\nok"
    exec_call = next(
        c for c in runner.calls if "exec" in c["argv"] and "--help" not in c["argv"]
    )
    assert exec_call["cwd"] == "/fake/ws"
    assert exec_call["timeout"] == 123.0
    assert exec_call["argv"] == ["codex", "exec", "--sandbox", "workspace-write"]
    assert exec_call["input"] is not None  # stdin mode
    assert "You are the implementation agent." in exec_call["input"]


def test_codex_subprocess_failure_is_result_not_crash():
    runner = FakeCommandRunner(
        results={
            "codex exec --sandbox workspace-write": cmd_result(
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
            "codex exec --sandbox workspace-write": cmd_result(
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
    exec_call = next(
        c for c in runner.calls if "exec" in c["argv"] and "--help" not in c["argv"]
    )
    assert exec_call["argv"][:2] == ["codex", "exec"]
    assert "You are the implementation agent." in exec_call["argv"][-1]
    assert exec_call["input"] is None


# ---------------------------------------------------------------------------
# RC hardening: stdin is the canonical transport (scenarios 28-32)
# ---------------------------------------------------------------------------
def test_stdin_is_the_default_transport():
    config = CodexConfig()
    assert config.prompt_mode == "stdin"  # canonical; argv is fallback only


def test_long_prompt_travels_verbatim_via_stdin():
    runner = FakeCommandRunner(results={})
    provider = CodexCLIProvider(CodexConfig(), runner=runner, workspace_root="/fake/ws")
    long_objective = "fix " + "x" * 80_000
    context = ImplementerContext(
        task_id="DR-0001",
        packet=make_packet(objective=long_objective),
        attempt=1,
        workspace_root="/fake/ws",
    )
    result = provider.run(context)
    assert result.success
    exec_call = next(
        c for c in runner.calls if "exec" in c["argv"] and "--help" not in c["argv"]
    )
    assert exec_call["input"] is not None
    assert len(exec_call["input"]) >= 80_000
    # argv carries NO prompt payload (keeps Windows arg-length limits away)
    assert "xxxxx" not in " ".join(exec_call["argv"])


def test_unicode_and_shell_metacharacters_remain_literal_on_stdin():
    runner = FakeCommandRunner(results={})
    provider = CodexCLIProvider(CodexConfig(), runner=runner, workspace_root="/fake/ws")
    tricky = (
        "你好 🚀\n"
        "$(touch /tmp/pwned-devrelay)\n"
        '; rm -rf /tmp/x "quoted" `backtick` & disallowed'
    )
    context = ImplementerContext(
        task_id="DR-0001",
        packet=make_packet(objective=tricky),
        attempt=1,
        workspace_root="/fake/ws",
    )
    provider.run(context)
    exec_call = next(
        c for c in runner.calls if "exec" in c["argv"] and "--help" not in c["argv"]
    )
    # passed through stdin byte-for-byte, never interpreted by a shell
    assert tricky in exec_call["input"]
    argv_text = " ".join(exec_call["argv"])
    assert "$(touch" not in argv_text
    assert "backtick" not in argv_text


def test_unknown_configured_flags_rejected_before_start():
    help_text = (
        "Usage: codex exec [OPTIONS] [PROMPT]\n"
        "  --sandbox <SANDBOX_MODE>\n"
        "  --approve-for-me\n"
        "  -C, --cd <DIR>\n"
    )
    runner = FakeCommandRunner(
        results={"codex exec --help": cmd_result(stdout=help_text)}
    )
    provider = CodexCLIProvider(
        CodexConfig(args=["exec", "--full-auto", "--sandbox", "workspace-write"]),
        runner=runner,
        workspace_root="/fake/ws",
    )
    warnings = provider.unknown_arg_warnings()
    assert any("--full-auto" in w for w in warnings)
    result = provider.run(_context())
    assert not result.success
    assert "--full-auto" in (result.error or "")
