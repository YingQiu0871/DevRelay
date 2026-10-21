"""v0.2-C completion replay, control-state identity and hold recovery.

All offline: a fake implementer that raises if it is ever invoked proves that
replay/hold paths cost **zero** provider calls.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from devrelay.errors import DevRelayError, StateConflictError
from devrelay.models import ProviderExecutionResult
from devrelay.pipeline.states import PipelineState as S
from devrelay.providers.base import ImplementerProvider
from devrelay.workspace.runner import CommandRunner

from helpers import (
    ScriptedAutoReviewer,
    build_engine,
    default_config,
    make_packet,
    make_review,
    requires_windows_containment,
    structured_codex_config,
    write_codex_stub,
)

pytestmark = requires_windows_containment

STATE = "DR-0001"


class CrashAfterReady(BaseException):
    """Simulated process death between COMPLETION_READY and COMPLETION_APPLIED."""


class ExplodingImplementer(ImplementerProvider):
    """Fails the test if the engine ever tries to invoke a provider again."""

    name = "exploding"

    def __init__(self) -> None:
        self.calls = 0

    def availability(self) -> tuple[bool, str]:
        return (True, "never invoked")

    def run(self, context) -> ProviderExecutionResult:
        self.calls += 1
        raise AssertionError("provider must not be invoked (replay/hold path)")


def _config():
    config = default_config()
    config.tests.targeted = []
    config.budget.max_implementer_calls = 1
    config.budget.max_total_provider_calls = 2
    return config


def _structured_engine(tmp_path: Path, stub, *, use_real_git: bool = True):
    from devrelay.providers.codex_cli import CodexCLIProvider

    config = _config()
    codex_config = structured_codex_config(stub)
    config.codex = codex_config
    provider = CodexCLIProvider(
        codex_config, CommandRunner(), workspace_root=str(tmp_path / "ws")
    )
    root, store, engine = build_engine(
        tmp_path,
        config=config,
        implementer=provider,
        reviewer=ScriptedAutoReviewer([make_review("PASS")]),
        use_real_git=use_real_git,
    )
    engine.create_task("replay fixture")
    engine.import_plan(STATE, make_packet(task_id=STATE))
    return root, store, engine


def _crash_after_ready(tmp_path: Path, stub):
    """Run one attempt, then die in the READY -> APPLIED window."""
    root, store, engine = _structured_engine(tmp_path, stub)
    original = type(engine)._apply_completion

    def boom(self, *args, **kwargs):
        raise CrashAfterReady()

    type(engine)._apply_completion = boom
    try:
        with pytest.raises(CrashAfterReady):
            engine.continue_task(STATE)
    finally:
        type(engine)._apply_completion = original
    task = store.read_task(STATE)
    assert task.attempts[-1].completion_ready is True
    assert task.attempts[-1].completion_applied is False
    assert task.attempt_in_flight is False
    return root, store, task


def _replay_engine(tmp_path: Path):
    """Fresh engine (no git re-init!) whose implementer must never be called.

    The workspace and baseline service are constructed directly: calling
    ``build_engine(use_real_git=True)`` again would re-run ``git init/add/commit``
    and change HEAD/branch/index, which is itself a guard-identity change.
    """
    from devrelay.artifacts.store import ArtifactStore
    from devrelay.baseline.service import BaselineService
    from devrelay.workspace.git import GitWorkspace

    implementer = ExplodingImplementer()
    config = _config()
    root_dir = tmp_path / "ws"
    store = ArtifactStore(root_dir)
    workspace = GitWorkspace(root_dir)
    baselines = BaselineService(root_dir, CommandRunner(), store, config)
    _root, store, engine = build_engine(
        tmp_path,
        config=config,
        implementer=implementer,
        reviewer=ScriptedAutoReviewer([make_review("PASS")]),
        workspace=workspace,
        baseline_service=baselines,
    )
    return store, engine, implementer


# ---------------------------------------------------------------------------
# C21: identities match -> local replay, zero provider calls
# ---------------------------------------------------------------------------
def test_completion_replay_workspace_match(tmp_path):
    root, store, task = _crash_after_ready(
        tmp_path, write_codex_stub(tmp_path / "tools")
    )
    store2, engine2, implementer = _replay_engine(tmp_path)
    events = engine2.continue_task(STATE)

    assert implementer.calls == 0
    replayed = store2.read_task(STATE)
    assert replayed.attempts[-1].completion_applied is True
    assert replayed.attempts[-1].applied_state == S.TESTING.value
    assert any("replaying completion" in event for event in events)
    assert engine2.usage_block(STATE)["implementer_calls"] == 1  # unchanged


# ---------------------------------------------------------------------------
# C22: workspace drift -> blocked, no rollback, no new Codex call
# ---------------------------------------------------------------------------
def test_completion_replay_workspace_drift_blocks(tmp_path):
    root, store, task = _crash_after_ready(
        tmp_path, write_codex_stub(tmp_path / "tools")
    )
    # a human edits the workspace after the completed run
    (tmp_path / "ws" / "human_edit.py").write_text("print('hi')\n", encoding="utf-8")

    store2, engine2, implementer = _replay_engine(tmp_path)
    engine2.continue_task(STATE)

    assert implementer.calls == 0
    blocked = store2.read_task(STATE)
    assert blocked.state == S.BLOCKED
    assert blocked.blocked_code == "implementer_replay_workspace_changed"
    # the completed attempt is preserved as evidence, nothing rolled back
    assert blocked.attempts[-1].completion_ready is True
    assert blocked.attempts[-1].completion_applied is False
    assert (tmp_path / "ws" / "human_edit.py").is_file()


# ---------------------------------------------------------------------------
# C39: control-state drift -> blocked (state.json and protected manifest)
# ---------------------------------------------------------------------------
def test_replay_blocked_by_state_json_drift(tmp_path):
    root, store, task = _crash_after_ready(
        tmp_path, write_codex_stub(tmp_path / "tools")
    )
    state_path = store.state_path(STATE)
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["manual_override"] = True  # external edit of authoritative state
    state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    store2, engine2, implementer = _replay_engine(tmp_path)
    engine2.continue_task(STATE)

    assert implementer.calls == 0
    blocked = store2.read_task(STATE)
    assert blocked.state == S.BLOCKED
    assert blocked.blocked_code == "replay_control_state_changed"


def test_replay_blocked_by_protected_manifest_drift(tmp_path):
    root, store, task = _crash_after_ready(
        tmp_path, write_codex_stub(tmp_path / "tools")
    )
    attempt_id = task.attempts[-1].attempt_id
    ledger = store.policy_dir(STATE) / "attempts" / f"{attempt_id}.json"
    ledger.write_text('{"tampered": true}', encoding="utf-8")

    store2, engine2, implementer = _replay_engine(tmp_path)
    engine2.continue_task(STATE)

    assert implementer.calls == 0
    blocked = store2.read_task(STATE)
    assert blocked.state == S.BLOCKED
    assert blocked.blocked_code == "replay_control_state_changed"


# ---------------------------------------------------------------------------
# C47/C50: hard-crash uncertainty never auto-restores or auto-reruns
# ---------------------------------------------------------------------------
def test_hard_crash_uncertainty_fails_closed_without_rerun(tmp_path):
    root, store, engine = _structured_engine(
        tmp_path, write_codex_stub(tmp_path / "tools")
    )
    task = store.read_task(STATE)
    task.attempt_in_flight = True  # hard kill mid-run
    store.write_task(task)

    store2, engine2, implementer = _replay_engine(tmp_path)
    engine2.continue_task(STATE)

    assert implementer.calls == 0
    blocked = store2.read_task(STATE)
    assert blocked.state == S.BLOCKED
    assert blocked.blocked_code == "interrupted_attempt"


def test_no_child_writable_pre_artifact_is_written(tmp_path):
    """Interpretation 1: the PRE anchor is parent memory, never a disk artifact."""
    root, store, task = _crash_after_ready(
        tmp_path, write_codex_stub(tmp_path / "tools")
    )
    control_dir = store.control_state_dir(STATE)
    if control_dir.is_dir():
        assert not list(control_dir.glob("*-pre.json"))
    # and a READY attempt without its durable completion evidence blocks
    attempt_id = task.attempts[-1].attempt_id
    (store.task_runtime_dir(STATE, attempt_id) / "completion.json").unlink()
    store2, engine2, implementer = _replay_engine(tmp_path)
    engine2.continue_task(STATE)
    assert implementer.calls == 0
    blocked = store2.read_task(STATE)
    assert blocked.blocked_code == "implementer_completion_evidence_missing"


# ---------------------------------------------------------------------------
# C46: hold cannot be cleared while protected state differs
# ---------------------------------------------------------------------------
def test_hold_ack_refused_while_divergent_then_cleared_after_restore(tmp_path):
    root, store, engine = _structured_engine(
        tmp_path, write_codex_stub(tmp_path / "tools")
    )
    state_path = store.state_path(STATE)
    (tmp_path / "tools" / "stub-config.json").write_text(
        json.dumps({"tamper": [["write", str(state_path), '{"broken": 1}']]}),
        encoding="utf-8",
    )
    engine.continue_task(STATE)
    hold = store.read_control_plane_hold(STATE)
    assert hold is not None and hold["code"] == "codex_control_plane_violation"

    # acknowledgement alone is refused while state.json still differs
    with pytest.raises(StateConflictError) as excinfo:
        engine.unblock(
            STATE, reason="ack", acknowledge_control_plane=True
        )
    assert "trusted PRE identity" in str(excinfo.value)
    assert store.read_control_plane_hold(STATE) is not None

    # explicit restore from the parent-held copy (hash-validated) clears it
    engine.unblock(
        STATE,
        reason="restore then acknowledge",
        acknowledge_control_plane=True,
        restore_control_plane_state=True,
    )
    assert store.read_control_plane_hold(STATE) is None
    restored = json.loads(state_path.read_text(encoding="utf-8"))
    assert restored.get("broken") is None
    assert restored["task_id"] == STATE


def test_tampered_pre_copy_is_refused(tmp_path):
    root, store, engine = _structured_engine(
        tmp_path, write_codex_stub(tmp_path / "tools")
    )
    state_path = store.state_path(STATE)
    (tmp_path / "tools" / "stub-config.json").write_text(
        json.dumps({"tamper": [["write", str(state_path), '{"broken": 1}']]}),
        encoding="utf-8",
    )
    engine.continue_task(STATE)
    hold = store.read_control_plane_hold(STATE)
    attempt_id = hold["attempt_id"]
    pre_copy = store.control_state_dir(STATE) / f"{attempt_id}-state.pre.json"
    assert pre_copy.is_file()
    pre_copy.write_text('{"also": "tampered"}', encoding="utf-8")
    with pytest.raises(StateConflictError):
        engine.unblock(
            STATE,
            reason="restore",
            acknowledge_control_plane=True,
            restore_control_plane_state=True,
        )


# ---------------------------------------------------------------------------
# C49: hold discovery does not trust the workspace index
# ---------------------------------------------------------------------------
def test_hold_discovery_survives_corrupt_workspace_index(tmp_path):
    root, store, engine = _structured_engine(
        tmp_path, write_codex_stub(tmp_path / "tools")
    )
    state_path = store.state_path(STATE)
    (tmp_path / "tools" / "stub-config.json").write_text(
        json.dumps({"tamper": [["write", str(state_path), '{"broken": 1}']]}),
        encoding="utf-8",
    )
    engine.continue_task(STATE)
    # corrupt the workspace index itself
    (store.devrelay_dir / "state.json").write_text("{not json", encoding="utf-8")
    holds = store.list_control_plane_holds()
    assert holds and holds[0]["task_id"] == STATE
