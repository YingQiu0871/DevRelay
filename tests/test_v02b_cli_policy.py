"""v0.2-B stage 3: CLI-level policy guards (provider spies, schema, force)."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from devrelay.cli import app

from helpers import make_git_repo


def _prepared_repo(tmp_path: Path, monkeypatch) -> Path:
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    monkeypatch.chdir(repo)
    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    assert runner.invoke(app, ["start", "v0.2-B policy smoke"]).exit_code == 0
    return repo


def _output(result) -> str:
    text = result.output or ""
    stderr = getattr(result, "stderr", "") or ""
    return text + stderr


def _snapshot(repo: Path) -> Path:
    return repo / ".devrelay" / "tasks" / "DR-0001" / "config.snapshot.yaml"


def _spy_on_providers(monkeypatch) -> None:
    """Any provider construction during a damaged-snapshot command fails."""
    from devrelay.providers.codex_cli import CodexCLIProvider
    from devrelay.providers.manual import ManualReviewer
    from devrelay.providers.openai_compatible import OpenAICompatibleReviewer

    def _boom(*args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError("provider was constructed for a damaged snapshot")

    monkeypatch.setattr(CodexCLIProvider, "__init__", _boom)
    monkeypatch.setattr(ManualReviewer, "__init__", _boom)
    monkeypatch.setattr(OpenAICompatibleReviewer, "__init__", _boom)


# ---------------------------------------------------------------------------
# B-PROVIDER-CONSTRUCT-1: fail closed before any provider object exists
# ---------------------------------------------------------------------------
def test_corrupt_snapshot_never_constructs_a_provider(tmp_path, monkeypatch):
    repo = _prepared_repo(tmp_path, monkeypatch)
    _snapshot(repo).write_bytes(b"pipeline: [unclosed\n")
    _spy_on_providers(monkeypatch)

    result = CliRunner().invoke(app, ["continue"])
    assert result.exit_code != 0
    assert "policy_snapshot_integrity_error" in _output(result)
    assert not isinstance(result.exception, AssertionError)


def test_deleted_snapshot_never_constructs_a_provider(tmp_path, monkeypatch):
    repo = _prepared_repo(tmp_path, monkeypatch)
    _snapshot(repo).unlink()
    _spy_on_providers(monkeypatch)

    result = CliRunner().invoke(app, ["continue"])
    assert result.exit_code != 0
    assert "policy_snapshot_missing" in _output(result)
    assert not isinstance(result.exception, AssertionError)


# ---------------------------------------------------------------------------
# R3-9: state written by a newer DevRelay gets a dedicated diagnostic
# ---------------------------------------------------------------------------
def test_state_schema_too_new_has_a_dedicated_error(tmp_path, monkeypatch):
    repo = _prepared_repo(tmp_path, monkeypatch)
    state_path = repo / ".devrelay" / "tasks" / "DR-0001" / "state.json"
    data = json.loads(state_path.read_text(encoding="utf-8"))
    data["state_schema_version"] = 99
    state_path.write_text(json.dumps(data), encoding="utf-8")
    before = state_path.read_bytes()

    for command in (["status"], ["usage"], ["continue"]):
        result = CliRunner().invoke(app, command)
        assert result.exit_code != 0, command
        assert "state_schema_too_new" in _output(result), command
        assert "upgrade DevRelay" in _output(result), command
    # Read-only commands never rewrite the newer state.
    assert state_path.read_bytes() == before


# ---------------------------------------------------------------------------
# R3-11: replacing an intact policy needs --force
# ---------------------------------------------------------------------------
def test_integrity_recovery_does_not_require_a_blocked_task(tmp_path, monkeypatch):
    """The classifier state authorizes recovery; the task need not be blocked."""
    repo = _prepared_repo(tmp_path, monkeypatch)
    _snapshot(repo).unlink()
    state_path = repo / ".devrelay" / "tasks" / "DR-0001" / "state.json"
    before = json.loads(state_path.read_text(encoding="utf-8"))
    assert before["state"] == "PLAN_REQUIRED"

    result = CliRunner().invoke(
        app, ["unblock", "--reason", "recover lost snapshot", "--refresh-policy"]
    )
    assert result.exit_code == 0, _output(result)
    assert _snapshot(repo).is_file()
    after = json.loads(state_path.read_text(encoding="utf-8"))
    assert after["state"] == "PLAN_REQUIRED"  # nothing was unblocked
    assert after["policy_source"] == "snapshot"
    record = after["policy_refreshes"][-1]
    assert record["trigger"] == "integrity_recovery"
    assert record["before_snapshot_available"] is False


def test_refresh_of_intact_policy_requires_force(tmp_path, monkeypatch):
    repo = _prepared_repo(tmp_path, monkeypatch)
    result = CliRunner().invoke(
        app, ["unblock", "--reason", "no real reason", "--refresh-policy"]
    )
    assert result.exit_code != 0
    assert "policy_refresh_not_allowed" in _output(result)
    assert "--force" in _output(result)
    # ...and the frozen policy is untouched.
    assert _snapshot(repo).is_file()


def _block_task(repo: Path) -> None:
    """Model a task that stopped on a provider budget (a real v0.2-A case)."""
    state_path = repo / ".devrelay" / "tasks" / "DR-0001" / "state.json"
    data = json.loads(state_path.read_text(encoding="utf-8"))
    data["state"] = "BLOCKED"
    data["blocked_code"] = "provider_budget_exhausted"
    data["blocked_reason"] = "test fixture"
    state_path.write_text(json.dumps(data), encoding="utf-8")


def test_refresh_of_damaged_snapshot_needs_no_force(tmp_path, monkeypatch):
    repo = _prepared_repo(tmp_path, monkeypatch)
    _block_task(repo)
    _snapshot(repo).unlink()
    result = CliRunner().invoke(
        app, ["unblock", "--reason", "recover lost snapshot", "--refresh-policy"]
    )
    assert result.exit_code == 0, _output(result)
    assert _snapshot(repo).is_file()

    state_path = repo / ".devrelay" / "tasks" / "DR-0001" / "state.json"
    record = json.loads(state_path.read_text(encoding="utf-8"))["policy_refreshes"][-1]
    assert record["trigger"] == "integrity_recovery"
    assert record["before_state"] == "missing"
    assert record["before_snapshot_available"] is False
    assert record["before_sha256"] == ""


# ---------------------------------------------------------------------------
# status reports integrity without touching live profiles
# ---------------------------------------------------------------------------
def test_status_reports_unverified_snapshot(tmp_path, monkeypatch):
    repo = _prepared_repo(tmp_path, monkeypatch)
    _snapshot(repo).write_bytes(b"policy: [broken\n")
    result = CliRunner().invoke(app, ["status"])
    assert result.exit_code == 0, _output(result)
    assert "UNVERIFIED: hash_mismatch" in _output(result)
    assert "refresh-policy" in _output(result)
