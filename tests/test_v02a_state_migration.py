"""v0.2-A acceptance: state compatibility and task-scoped policy semantics."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from devrelay.artifacts.store import ArtifactStore
from devrelay.cli import app
from devrelay.models import Severity
from devrelay.pipeline.states import PipelineState as S

from helpers import (
    ScriptedAutoReviewer,
    build_engine,
    default_config,
    make_finding,
    make_git_repo,
    make_packet,
    make_review,
)

# A v0.1.0-shaped state.json: no provider_calls / review_attempts /
# finding_seen_counts / policy_source / attempt_in_flight fields at all.
V01_STATE = {
    "task_id": "DR-0001",
    "title": "v0.1 legacy task",
    "state_schema_version": 2,
    "packet": {
        "task_id": "DR-0001",
        "title": "v0.1 legacy task",
        "objective": "keep loading old state",
        "risk_level": "NORMAL",
    },
    "state": "REVIEWING",
    "plan_ready": True,
    "created_at": "2026-09-01T00:00:00+00:00",
    "updated_at": "2026-09-01T00:00:00+00:00",
    "implementation_passes": 1,
    "fix_iterations_used": 0,
    "initial_snapshot": {
        "repo_root": "/legacy/repo",
        "head_sha": "abc",
        "branch": "main",
        "dirty_files": [],
        "has_git": True,
        "captured_at": "2026-09-01T00:00:00+00:00",
    },
    "current_findings": [],
    "open_p3": [],
    "review_history": [],
    "last_tests_passed": True,
    "test_evidence": [],
    "implementation_report_paths": [],
    "audit": [],
    "policy_violations": [],
    "attempts": [],
}


def _write_legacy_task(root: Path) -> ArtifactStore:
    store = ArtifactStore(root)
    store.ensure_initialized()
    task_dir = store.task_dir("DR-0001")
    task_dir.mkdir(parents=True, exist_ok=True)
    store.write_text(task_dir / "state.json", json.dumps(V01_STATE, indent=2))
    store.set_current_task("DR-0001")
    return store


# ---------------------------------------------------------------------------
# S2: v0.1 state loads and the task stays usable
# ---------------------------------------------------------------------------
def test_v01_state_fixture_loads_and_status_works(tmp_path, monkeypatch):
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    store = _write_legacy_task(repo)

    task = store.read_task("DR-0001")
    assert task.state == S.REVIEWING
    assert task.provider_calls == []
    assert task.review_attempts == []
    assert task.finding_seen_counts == {}
    assert task.review_call_in_flight is False

    monkeypatch.chdir(repo)
    result = CliRunner().invoke(app, ["status"])
    assert result.exit_code == 0, result.output
    assert "REVIEWING" in result.output
    assert "Budget" in result.output

    usage = CliRunner().invoke(app, ["usage"])
    assert usage.exit_code == 0, usage.output
    assert "Provider budget:" in usage.output
    assert "Implementer  0 / 4" in usage.output


# ---------------------------------------------------------------------------
# S3: the task policy is the snapshot taken at task start
# ---------------------------------------------------------------------------
def test_task_policy_is_snapshotted(tmp_path):
    config = default_config()
    config.budget.max_reviewer_calls = 4
    reviewer = ScriptedAutoReviewer(
        [make_review("REQUEST_CHANGES", [make_finding("P2", title="blocker")]), make_review("PASS")]
    )
    _root, store, engine = build_engine(tmp_path, config=config, reviewer=reviewer)
    engine.create_task("t")
    engine.import_plan("DR-0001", make_packet(task_id="DR-0001"))

    # The user edits the workspace config mid-task: budgets to zero and no
    # blocking severities. The running task must NOT silently change policy.
    engine.config.budget.max_reviewer_calls = 0
    engine.config.review.blocking_severities = []

    engine.continue_task("DR-0001")
    task = store.read_task("DR-0001")
    assert task.policy_source == "snapshot"
    assert task.state == S.FINAL_GATE_REQUIRED          # reviewer ran, P2 still blocked
    assert task.fix_iterations_used == 1                # P2 was still blocking
    assert len(reviewer.bundles) == 2
    assert task.review_history[0].findings[0].severity is Severity.P2


def test_policy_snapshot_file_is_written_at_start(tmp_path):
    _root, store, engine = build_engine(tmp_path)
    engine.create_task("t")
    snapshot = store.task_dir("DR-0001") / "config.snapshot.yaml"
    assert snapshot.is_file()
    assert "max_same_finding_cycles" in snapshot.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# S4: the only way to change a running task's policy is an audited refresh
# ---------------------------------------------------------------------------
def test_unblock_refresh_policy_is_audited_and_effective(tmp_path):
    config = default_config()
    config.budget.max_reviewer_calls = 0                 # blocks the first review
    _root, store, engine = build_engine(
        tmp_path, config=config, reviewer=ScriptedAutoReviewer([make_review("PASS")])
    )
    engine.create_task("t")
    engine.import_plan("DR-0001", make_packet(task_id="DR-0001"))
    engine.continue_task("DR-0001")
    blocked = store.read_task("DR-0001")
    assert blocked.blocked_code == "provider_budget_exhausted"

    # Raising the limit in the live config alone is not enough ...
    engine.config.budget.max_reviewer_calls = 4
    engine.continue_task("DR-0001")
    assert store.read_task("DR-0001").blocked_code == "provider_budget_exhausted"

    # ... the human must explicitly refresh the task policy.
    engine.unblock(
        "DR-0001",
        reason="raising reviewer budget for one more round",
        refresh_policy=True,
    )
    task = store.read_task("DR-0001")
    assert task.policy_source == "snapshot"
    assert any(
        "policy snapshot refreshed" in event.note and event.by == "human"
        for event in task.audit
    )
    engine.continue_task("DR-0001")
    assert store.read_task("DR-0001").state == S.FINAL_GATE_REQUIRED
