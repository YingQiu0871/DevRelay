"""v0.2-A acceptance: CLI visibility (status budget/review, usage, offline doctor)."""

from __future__ import annotations

from pathlib import Path

import yaml
from typer.testing import CliRunner

from devrelay.cli import app

from helpers import make_git_repo

FAKE_KEY = "sk-live-DOCTORMUSTNOTPRINT123456"


def _prepared_repo(tmp_path: Path, monkeypatch) -> Path:
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    monkeypatch.chdir(repo)
    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    assert runner.invoke(app, ["start", "v0.2 cli smoke"]).exit_code == 0
    return repo


def _stub_codex(monkeypatch) -> None:
    """Keep doctor hermetic: no codex subprocess, no model call."""
    from devrelay.providers.codex_cli import CodexCLIProvider

    monkeypatch.setattr(CodexCLIProvider, "availability", lambda self: (True, "stub codex"))
    monkeypatch.setattr(CodexCLIProvider, "unknown_arg_warnings", lambda self: [])


# ---------------------------------------------------------------------------
# S5: status shows budget + review evidence
# ---------------------------------------------------------------------------
def test_status_shows_budget_and_review(tmp_path, monkeypatch):
    _prepared_repo(tmp_path, monkeypatch)
    result = CliRunner().invoke(app, ["status"])
    assert result.exit_code == 0, result.output
    assert "Budget" in result.output
    assert "implementer 0/4, reviewer 0/4, total 0/8" in result.output
    assert "Review" in result.output
    assert "Policy" in result.output


# ---------------------------------------------------------------------------
# S6: usage is read-only and reports exact counts
# ---------------------------------------------------------------------------
def test_usage_command(tmp_path, monkeypatch):
    _prepared_repo(tmp_path, monkeypatch)
    result = CliRunner().invoke(app, ["usage"])
    assert result.exit_code == 0, result.output
    assert "Provider budget:" in result.output
    assert "Implementer  0 / 4" in result.output
    assert "Reviewer     0 / 4" in result.output
    assert "Total        0 / 8" in result.output
    assert "Review attempts:" in result.output
    assert "(none)" in result.output

    # There is deliberately no command that resets/forges usage.
    help_result = CliRunner().invoke(app, ["--help"])
    assert "reset" not in help_result.output.lower()


# ---------------------------------------------------------------------------
# S7: doctor reports presence only and never sends a request
# ---------------------------------------------------------------------------
def test_doctor_reviewer_check_is_offline(tmp_path, monkeypatch):
    repo = _prepared_repo(tmp_path, monkeypatch)
    _stub_codex(monkeypatch)

    config_path = repo / ".devrelay" / "config.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    data["review"]["provider"] = "openai_compatible"
    config_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    monkeypatch.setenv("DEVRELAY_REVIEWER_API_KEY", FAKE_KEY)
    monkeypatch.setenv("DEVRELAY_REVIEWER_MODEL", "fake-model")

    # Any attempt to build an HTTP client during doctor fails the test.
    import httpx

    def _forbidden_client(*args, **kwargs):  # pragma: no cover - must not run
        raise AssertionError("doctor must not create an HTTP client")

    monkeypatch.setattr(httpx, "Client", _forbidden_client)

    result = CliRunner().invoke(app, ["doctor"])
    assert result.exit_code == 0, result.output
    assert "Reviewer provider: openai_compatible" in result.output
    assert "DEVRELAY_REVIEWER_API_KEY: set" in result.output
    assert "DEVRELAY_REVIEWER_MODEL: set" in result.output
    assert FAKE_KEY not in result.output          # presence only, never the value
    assert "no request is sent by doctor" in result.output
    assert "Provider budget: implementer 4, reviewer 4, total 8" in result.output
