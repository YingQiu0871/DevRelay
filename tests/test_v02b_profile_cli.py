"""v0.2-B stage 5: profile/config diagnostics and profile independence."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from devrelay.cli import app

from helpers import make_git_repo


def _output(result) -> str:
    return (result.output or "") + (getattr(result, "stderr", "") or "")


def _repo(tmp_path, monkeypatch, *, profiles=None, selector="", extra=""):
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    monkeypatch.chdir(repo)
    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    directory = repo / ".devrelay" / "profiles"
    directory.mkdir(parents=True, exist_ok=True)
    for name, body in (profiles or {}).items():
        (directory / name).write_text(body, encoding="utf-8")
    config = repo / ".devrelay" / "config.yaml"
    config.write_text(f"{selector}\n{extra}\n", encoding="utf-8")
    return repo


def _start(repo: Path) -> None:
    result = CliRunner().invoke(app, ["start", "profile task"])
    assert result.exit_code == 0, _output(result)


# ---------------------------------------------------------------------------
# R3-5: profile diagnostics survive a broken selector
# ---------------------------------------------------------------------------
def test_profile_list_works_with_a_broken_selector(tmp_path, monkeypatch):
    _repo(
        tmp_path,
        monkeypatch,
        profiles={
            "valid.yaml": "budget:\n  max_reviewer_calls: 2\n",
            "Base.yaml": "budget:\n  max_reviewer_calls: 1\n",
        },
        selector="profiles: [missing, valid]",
    )
    result = CliRunner().invoke(app, ["profile", "list"])
    assert result.exit_code == 0, _output(result)
    assert "valid" in result.output
    assert "Base.yaml" in result.output and "IGNORED" in result.output


def test_profile_show_and_validate_are_per_file(tmp_path, monkeypatch):
    _repo(
        tmp_path,
        monkeypatch,
        profiles={"valid.yaml": "budget:\n  max_reviewer_calls: 2\n"},
        selector="profiles: [missing, valid]",
    )
    runner = CliRunner()
    show = runner.invoke(app, ["profile", "show", "valid"])
    assert show.exit_code == 0, _output(show)
    assert "max_reviewer_calls: 2" in show.output
    assert "SHA-256:" in show.output

    ghost = runner.invoke(app, ["profile", "show", "ghost"])
    assert ghost.exit_code != 0
    assert "profile_not_found" in _output(ghost)

    one = runner.invoke(app, ["profile", "validate", "valid"])
    assert one.exit_code == 0, _output(one)

    all_profiles = runner.invoke(app, ["profile", "validate"])
    assert all_profiles.exit_code != 0
    # Collect-all: the missing reference AND the per-file verdicts are reported.
    assert "missing" in all_profiles.output
    assert "valid" in all_profiles.output


def test_config_show_unresolved_is_useful_with_a_broken_chain(tmp_path, monkeypatch):
    _repo(
        tmp_path,
        monkeypatch,
        profiles={"valid.yaml": "budget:\n  max_reviewer_calls: 2\n"},
        selector="profiles: [missing, valid]",
        extra="budget:\n  max_total_provider_calls: 6\n",
    )
    result = CliRunner().invoke(app, ["config", "show"])
    assert result.exit_code == 0, _output(result)
    assert "Selected profiles (unresolved): ['missing', 'valid']" in result.output
    assert "not the effective task policy" in result.output
    assert "'budget'" in result.output  # labelled policy overrides present


def test_config_show_resolved_is_authoritative(tmp_path, monkeypatch):
    repo = _repo(
        tmp_path,
        monkeypatch,
        profiles={"valid.yaml": "budget:\n  max_reviewer_calls: 2\n"},
        selector="profiles: [valid]",
    )
    runner = CliRunner()
    ok = runner.invoke(app, ["config", "show", "--resolved"])
    assert ok.exit_code == 0, _output(ok)
    assert "max_reviewer_calls: 2" in ok.output
    assert "profile valid:" in ok.output

    # Break the chain: the authoritative resolver must fail closed.
    (repo / ".devrelay" / "profiles" / "valid.yaml").unlink()
    broken = runner.invoke(app, ["config", "show", "--resolved"])
    assert broken.exit_code != 0
    assert "profile_not_found" in _output(broken)


def test_doctor_reports_raw_and_chain_separately(tmp_path, monkeypatch):
    _repo(
        tmp_path,
        monkeypatch,
        profiles={"valid.yaml": "budget:\n  max_reviewer_calls: 2\n"},
        selector="profiles: [missing, valid]",
    )
    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0, _output(result)
    assert "per-file validation: OK" in result.output
    assert "Effective policy chain: FAILED" in result.output

    strict = runner.invoke(app, ["doctor", "--strict"])
    assert strict.exit_code != 0


# ---------------------------------------------------------------------------
# R3-6: status/usage never touch live profiles (and never rewrite state)
# ---------------------------------------------------------------------------
def test_status_and_usage_ignore_live_profiles(tmp_path, monkeypatch):
    import devrelay.cli as cli_module
    import devrelay.profiles as profiles_module

    repo = _repo(
        tmp_path,
        monkeypatch,
        profiles={"valid.yaml": "budget:\n  max_reviewer_calls: 2\n"},
        selector="profiles: [valid]",
    )
    _start(repo)

    def _forbidden(*args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError("a live profile was read by a read-only command")

    monkeypatch.setattr(profiles_module, "resolve_policy_config", _forbidden)
    monkeypatch.setattr(profiles_module, "load_profile", _forbidden)
    monkeypatch.setattr(cli_module, "resolve_policy_config", _forbidden)
    for path in (repo / ".devrelay" / "profiles").glob("*.yaml"):
        path.unlink()

    state_path = repo / ".devrelay" / "tasks" / "DR-0001" / "state.json"
    before = state_path.read_bytes()
    runner = CliRunner()
    for command in (["status"], ["usage"]):
        result = runner.invoke(app, command)
        assert result.exit_code == 0, _output(result)
        assert "snapshot" in result.output
    assert state_path.read_bytes() == before  # read-only means read-only

    # Recorded provenance is displayed without re-reading the profile file.
    import json

    recorded = json.loads(before.decode("utf-8"))["policy_provenance"]["profiles"]
    assert recorded and recorded[0]["name"] == "valid"
    status_again = CliRunner().invoke(app, ["status"])
    assert recorded[0]["sha256"] in status_again.output


# ---------------------------------------------------------------------------
# B-WIRING-1: a frozen task survives a malformed live policy override
# ---------------------------------------------------------------------------
def test_start_fails_closed_on_broken_live_policy(tmp_path, monkeypatch):
    repo = _repo(
        tmp_path,
        monkeypatch,
        profiles={"valid.yaml": "budget:\n  max_reviewer_calls: 2\n"},
        selector="profiles: [valid]",
    )
    config = repo / ".devrelay" / "config.yaml"
    config.write_text(
        config.read_text(encoding="utf-8")
        + 'budget:\n  max_total_provider_calls: "THIS IS NOT AN INTEGER"\n',
        encoding="utf-8",
    )
    result = CliRunner().invoke(app, ["start", "cannot start"])
    assert result.exit_code != 0
    assert "invalid" in _output(result).lower()


def test_frozen_task_continues_despite_broken_live_policy(tmp_path, monkeypatch):
    repo = _repo(
        tmp_path,
        monkeypatch,
        profiles={"valid.yaml": "budget:\n  max_reviewer_calls: 2\n"},
        selector="profiles: [valid]",
    )
    _start(repo)
    config = repo / ".devrelay" / "config.yaml"
    config.write_text(
        'profiles: [valid]\nbudget:\n  max_total_provider_calls: "NOT AN INTEGER"\n',
        encoding="utf-8",
    )
    (repo / ".devrelay" / "profiles" / "valid.yaml").unlink()

    result = CliRunner().invoke(app, ["continue"])
    # No plan imported yet: the command may stop for a pipeline reason, but it
    # must NOT fail on live policy validation.
    assert "invalid policy overrides" not in _output(result)
    assert "max_total_provider_calls" not in _output(result)
