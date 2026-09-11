"""v0.2-B stage 3: frozen snapshot classification, integrity and recovery."""

from __future__ import annotations

import pytest

from devrelay.artifacts.store import sha256_file
from devrelay.config import (
    PolicyDocument,
    dump_config_yaml,
    dump_policy_yaml,
    load_config,
)
from devrelay.errors import (
    PolicySnapshotIntegrityError,
    PolicySnapshotMissingError,
)
from devrelay.pipeline.engine import PolicyRecoveryGrant
from devrelay.snapshot import SnapshotState, check_snapshot, snapshot_path

from helpers import (
    ScriptedAutoReviewer,
    build_engine,
    default_config,
    make_packet,
    make_review,
)

STATE = "DR-0001"


def _started(tmp_path, *, config=None, reviewer=None):
    reviewer = reviewer or ScriptedAutoReviewer([make_review("PASS")])
    _root, store, engine = build_engine(
        tmp_path, config=config or default_config(), reviewer=reviewer
    )
    engine.create_task("t")
    engine.import_plan(STATE, make_packet(task_id=STATE))
    return store, engine


# ---------------------------------------------------------------------------
# R3-8: the recorded digest is the digest of the bytes on disk (LF, no CRLF)
# ---------------------------------------------------------------------------
def test_recorded_digest_matches_on_disk_bytes(tmp_path):
    store, _engine = _started(tmp_path)
    task = store.read_task(STATE)
    path = snapshot_path(store, STATE)
    assert task.policy_source == "snapshot"
    assert task.policy_snapshot_path == f".devrelay/tasks/{STATE}/config.snapshot.yaml"
    assert task.policy_config_sha256 == sha256_file(path)
    assert task.policy_provenance is not None
    assert task.policy_provenance.generation == 1
    assert task.policy_provenance.snapshot_sha256 == task.policy_config_sha256
    assert b"\r" not in path.read_bytes()


# ---------------------------------------------------------------------------
# R3-1 / R3-2: damaged snapshots fail closed before any provider work
# ---------------------------------------------------------------------------
def test_corrupt_snapshot_fails_closed(tmp_path):
    store, engine = _started(tmp_path)
    path = snapshot_path(store, STATE)
    before_state = store.state_path(STATE).read_bytes()
    path.write_bytes(b"pipeline: [unclosed\n")

    with pytest.raises(PolicySnapshotIntegrityError) as excinfo:
        engine.continue_task(STATE)
    message = str(excinfo.value)
    assert "policy_snapshot_integrity_error" in message
    assert "refresh-policy" in message
    # No implicit downgrade, no implicit repair, no state mutation.
    assert store.state_path(STATE).read_bytes() == before_state
    assert store.read_task(STATE).provider_calls == []


def test_snapshot_replaced_by_another_valid_policy_fails_closed(tmp_path):
    store, engine = _started(tmp_path)
    path = snapshot_path(store, STATE)
    other = PolicyDocument.from_workspace_config(default_config())
    other.budget.max_reviewer_calls = 1
    path.write_text(dump_policy_yaml(other), encoding="utf-8")

    with pytest.raises(PolicySnapshotIntegrityError):
        engine.continue_task(STATE)


# ---------------------------------------------------------------------------
# R3-4: a modern task whose snapshot was deleted is MISSING, never legacy
# ---------------------------------------------------------------------------
def test_modern_snapshot_deleted_is_missing_not_legacy(tmp_path):
    store, engine = _started(tmp_path)
    snapshot_path(store, STATE).unlink()
    task = store.read_task(STATE)
    state = check_snapshot(store, task).state
    assert state is SnapshotState.MISSING
    with pytest.raises(PolicySnapshotMissingError):
        engine.continue_task(STATE)


# ---------------------------------------------------------------------------
# Legacy tasks keep working through explicit live policy resolution
# ---------------------------------------------------------------------------
def _make_legacy_v02a_task(store, engine, task_id=STATE):
    """Rewrite a task into a v0.2-A-shaped one: schema 4, CRLF full-config dump."""
    task = store.read_task(task_id)
    task.state_schema_version = 4
    task.policy_snapshot_path = ""
    task.policy_config_sha256 = ""
    task.policy_provenance = None
    store.write_task(task)
    text = dump_config_yaml(load_config(None)).replace("\n", "\r\n")
    snapshot_path(store, task_id).write_bytes(text.encode("utf-8"))
    return store.read_task(task_id)


def test_v02a_snapshot_task_keeps_its_frozen_policy(tmp_path):
    store, engine = _started(tmp_path)
    _make_legacy_v02a_task(store, engine)
    task = store.read_task(STATE)
    state = check_snapshot(store, task).state
    assert state is SnapshotState.VALID  # digest-less legacy tolerance

    # A live policy edit must not reach the frozen task.
    engine.config.budget.max_reviewer_calls = 0
    engine.config.review.blocking_severities = []
    document = engine._task_config(store.read_task(STATE))
    assert document.budget.max_reviewer_calls == 4
    assert {s.value for s in document.review.blocking_severities} == {"P0", "P1", "P2"}


def test_genuine_legacy_task_is_legacy_live(tmp_path):
    store, engine = _started(tmp_path)
    task = store.read_task(STATE)
    task.state_schema_version = 2
    task.policy_source = ""
    task.policy_snapshot_path = ""
    task.policy_config_sha256 = ""
    store.write_task(task)
    snapshot_path(store, STATE).unlink()

    current = store.read_task(STATE)
    state = check_snapshot(store, current).state
    assert state is SnapshotState.LEGACY_LIVE
    # ...and it still executes from the explicit live policy.
    events = engine.continue_task(STATE)
    assert events and store.read_task(STATE).state.value in (
        "REVIEWING",
        "FINAL_GATE_REQUIRED",
        "BLOCKED",
    )
