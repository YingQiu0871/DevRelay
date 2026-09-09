"""CLI surface tests (no Codex execution is ever triggered here)."""

import pytest
from typer.testing import CliRunner

from devrelay.cli import app
from devrelay.artifacts.store import ArtifactStore

from helpers import make_git_repo

runner = CliRunner()

PLAN_MD = """\
# Task DR-0001

## Title

Wear tile fix

## Objective

Fix the Wear tile rendering so it refreshes.

## Scope

- src/tile

## Out of Scope

- phone app behavior

## Acceptance Criteria

- targeted tests pass

## Constraints

- no refactors

## Tests Required

- gradle test

## Risk Level

NORMAL
"""


def test_help_exits_zero():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "start" in result.output
    assert "continue" in result.output


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_init_creates_config_without_clobber(tmp_path, monkeypatch):
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    monkeypatch.chdir(repo)
    first = runner.invoke(app, ["init"])
    assert first.exit_code == 0, first.output
    assert "Initialized" in first.output
    config = repo / ".devrelay" / "config.yaml"
    assert config.is_file()
    original = config.read_text(encoding="utf-8")

    second = runner.invoke(app, ["init"])
    assert second.exit_code != 0
    assert "already initialized" in second.output
    assert config.read_text(encoding="utf-8") == original  # untouched


def test_start_requires_initialized_workspace(tmp_path, monkeypatch):
    repo = make_git_repo(tmp_path / "repo")
    monkeypatch.chdir(repo)
    result = runner.invoke(app, ["start", "Fix tile"])
    assert result.exit_code != 0
    assert "devrelay init" in result.output


def test_start_and_status_in_git_workspace(tmp_path, monkeypatch):
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    monkeypatch.chdir(repo)
    assert runner.invoke(app, ["init"]).exit_code == 0

    result = runner.invoke(app, ["start", "Fix tile"])
    assert result.exit_code == 0, result.output
    assert "DR-0001" in result.output
    store = ArtifactStore(repo)
    assert store.current_task_id() == "DR-0001"

    status = runner.invoke(app, ["status"])
    assert status.exit_code == 0, status.output
    assert "DR-0001" in status.output
    assert "PLAN_REQUIRED" in status.output
    assert "Planner" in status.output


def test_plan_import_show_and_logs(tmp_path, monkeypatch):
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    monkeypatch.chdir(repo)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["start", "Wear tile"])

    plan_file = tmp_path / "plan.md"
    plan_file.write_text(PLAN_MD, encoding="utf-8")
    imported = runner.invoke(app, ["plan", "import", str(plan_file)])
    assert imported.exit_code == 0, imported.output
    assert "PLAN_READY" in imported.output

    shown = runner.invoke(app, ["plan", "show"])
    assert shown.exit_code == 0
    assert "Wear tile fix" in shown.output

    status = runner.invoke(app, ["status"])
    assert "PLAN_READY" in status.output

    logs = runner.invoke(app, ["logs"])
    assert logs.exit_code == 0
    assert "no logs yet" in logs.output


def test_status_requires_existing_task(tmp_path, monkeypatch):
    repo = make_git_repo(tmp_path / "repo")
    monkeypatch.chdir(repo)
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["status"])
    assert result.exit_code != 0
    assert "no task exists" in result.output
