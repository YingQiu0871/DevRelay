"""Release-preparation regression tests (P3-A final report status, P3-B unborn HEAD)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from devrelay.artifacts.store import ArtifactStore
from devrelay.baseline.service import BaselineService
from devrelay.cli import app
from devrelay.config import load_config
from devrelay.errors import BaselineUnavailableError
from devrelay.pipeline.engine import DevRelayEngine
from devrelay.pipeline.states import PipelineState as S
from devrelay.providers.manual import ManualReviewer
from devrelay.workspace.git import GitWorkspace
from devrelay.workspace.runner import CommandRunner

from helpers import build_engine, make_packet, make_review

IDENT = {
    "GIT_AUTHOR_NAME": "A",
    "GIT_AUTHOR_EMAIL": "a@x",
    "GIT_COMMITTER_NAME": "A",
    "GIT_COMMITTER_EMAIL": "a@x",
}


# ---------------------------------------------------------------------------
# P3-A: final/report.md must reflect the real final state (DONE)
# ---------------------------------------------------------------------------

def test_final_report_status_is_done_after_approval(tmp_path):
    root, store, engine = build_engine(tmp_path)
    engine.create_task("t")
    engine.import_plan("DR-0001", make_packet(task_id="DR-0001"))
    engine.continue_task("DR-0001")
    assert store.read_task("DR-0001").state == S.REVIEWING

    engine.import_manual_review("DR-0001", make_review("PASS"))
    assert store.read_task("DR-0001").state == S.FINAL_GATE_REQUIRED

    engine.approve_final("DR-0001", note="release prep check")
    task = store.read_task("DR-0001")
    assert task.state == S.DONE

    report = (store.final_dir("DR-0001") / "report.md").read_text(encoding="utf-8")
    assert "**Status:** DONE" in report
    assert "**Status:** FINAL_GATE_REQUIRED" not in report
    assert "Final gate approved" in report or "Approved by: manual" in report


# ---------------------------------------------------------------------------
# P3-B: unborn HEAD must produce a curated user error, not raw git output
# ---------------------------------------------------------------------------

def _unborn_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "unborn"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "-C", str(repo), "init", "-q", "-b", "main"],
        check=True,
        env={**os.environ, **IDENT},
    )
    return repo


def _engine_for(repo: Path) -> tuple[ArtifactStore, DevRelayEngine]:
    store = ArtifactStore(repo)
    store.ensure_initialized()
    runner = CommandRunner()
    config = load_config(None)
    engine = DevRelayEngine(
        config,
        store,
        GitWorkspace(repo, runner),
        implementer=None,  # not used: task creation must fail first
        reviewer=ManualReviewer(),
        runner=runner,
        baselines=BaselineService(repo, runner, store, config),
    )
    return store, engine


def test_unborn_head_raises_friendly_error_without_raw_git_output(tmp_path):
    repo = _unborn_repo(tmp_path)
    store, engine = _engine_for(repo)

    with pytest.raises(BaselineUnavailableError) as excinfo:
        engine.create_task("t")

    message = str(excinfo.value)
    assert "no commits yet" in message
    assert "initial commit" in message
    assert "fatal:" not in message
    assert "ambiguous argument" not in message
    # no half-created task/baseline artifacts
    assert not (store.task_dir("DR-0001")).exists()
    assert store.current_task_id() is None


def test_cli_start_in_unborn_repo_exits_nonzero_with_friendly_message(tmp_path, monkeypatch):
    repo = _unborn_repo(tmp_path)
    monkeypatch.chdir(repo)
    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0

    result = runner.invoke(app, ["start", "release package smoke"])

    assert result.exit_code != 0
    assert "no commits yet" in result.output
    assert "fatal:" not in result.output
    assert "ambiguous argument" not in result.output
    assert not (repo / ".devrelay" / "tasks" / "DR-0001").exists()
