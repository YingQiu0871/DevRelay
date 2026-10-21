"""v0.2-B P2 remediation: state-schema migration and refresh evidence durability.

Two blockers from the independent v0.2-B review:

* **P2-1** - a loaded schema-2/3/4 task kept its old ``state_schema_version`` on
  write, so v5-only fields landed in a file still claiming schema 4,
  ``state.v<old>.json.bak`` was never created and ``doctor`` reported a pending
  migration forever.
* **P2-2** - refresh evidence identity came from
  ``len(task.policy_refreshes) + 1``, so a failed attempt (whose record never
  reached ``state.json``) had its ``policy-refresh-01-*`` artifacts overwritten
  by the retry.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

import devrelay.artifacts.store as store_module
from devrelay.artifacts.store import ArtifactStore, encode_lf, sha256_file
from devrelay.cli import app
from devrelay.config import load_config
from devrelay.errors import DevRelayError, PolicySnapshotError
from devrelay.models import STATE_SCHEMA_VERSION
from devrelay.pipeline.engine import next_refresh_attempt
from devrelay.snapshot import SnapshotState, check_snapshot, snapshot_path

from helpers import (
    ScriptedAutoReviewer,
    build_engine,
    make_git_repo,
    make_packet,
    make_review,
)

STATE = "DR-0001"
V5_ONLY_KEYS = ("policy_config_sha256", "policy_snapshot_path", "policy_provenance")


def _started(tmp_path):
    _root, store, engine = build_engine(tmp_path)
    engine.create_task("t")
    engine.import_plan(STATE, make_packet(task_id=STATE))
    return store, engine


def _downgrade(store, version, *, drop_v5=True, policy_source=None):
    """Rewrite ``state.json`` as an older-schema file; return its exact bytes."""
    path = store.state_path(STATE)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["state_schema_version"] = version
    if drop_v5:
        for key in V5_ONLY_KEYS:
            data.pop(key, None)
    if policy_source is not None:
        data["policy_source"] = policy_source
    path.write_bytes(encode_lf(json.dumps(data, indent=2)))
    return path.read_bytes()


def _raw_version(store) -> int:
    path = store.state_path(STATE)
    return json.loads(path.read_text(encoding="utf-8"))["state_schema_version"]


def _backups(store) -> list[Path]:
    return sorted(store.task_dir(STATE).glob("state.v*.json.bak"))


# ===========================================================================
# P2-1: real schema migration on the first mutating write
# ===========================================================================
@pytest.mark.parametrize("version", [2, 3, 4])
def test_first_mutating_write_migrates_and_backs_up_once(tmp_path, version):
    store, engine = _started(tmp_path)
    before_bytes = _downgrade(store, version)
    backup = store.task_dir(STATE) / f"state.v{version}.json.bak"
    assert not backup.exists()

    # B: a real mutating DevRelay operation writes the task
    engine.refresh_task_policy(STATE, "migrate")

    # C/D: upgraded schema and a one-time backup of the exact previous bytes
    assert _raw_version(store) == STATE_SCHEMA_VERSION
    assert store.read_task(STATE).state_schema_version == STATE_SCHEMA_VERSION
    assert backup.is_file()
    assert backup.read_bytes() == before_bytes  # E: byte-exact
    assert [p.name for p in _backups(store)] == [backup.name]

    # F/G: a second real write keeps the backup untouched and stays current
    engine.refresh_task_policy(STATE, "second write")
    assert _raw_version(store) == STATE_SCHEMA_VERSION
    assert backup.read_bytes() == before_bytes
    assert [p.name for p in _backups(store)] == [backup.name]


def test_migration_backup_failure_aborts_and_leaves_state_untouched(tmp_path, monkeypatch):
    _root, store, engine = build_engine(tmp_path)
    engine.create_task("t")
    before_bytes = _downgrade(store, 4)

    real = store_module._atomic_write_bytes

    def boom(path, data):
        if str(path).endswith(".bak"):
            raise OSError("injected: backup creation failed")
        return real(path, data)

    monkeypatch.setattr(store_module, "_atomic_write_bytes", boom)

    with pytest.raises(OSError):
        engine.import_plan(STATE, make_packet(task_id=STATE))

    assert store.state_path(STATE).read_bytes() == before_bytes
    assert _raw_version(store) == 4
    assert _backups(store) == []


def test_migration_state_write_failure_keeps_backup_and_allows_retry(tmp_path, monkeypatch):
    _root, store, engine = build_engine(tmp_path)
    engine.create_task("t")
    before_bytes = _downgrade(store, 4)
    backup = store.task_dir(STATE) / "state.v4.json.bak"

    real = store_module._atomic_write_text
    state_path = store.state_path(STATE)
    calls = {"n": 0}

    def boom(path, text):
        if Path(path) == state_path:
            calls["n"] += 1
            if calls["n"] == 1:
                raise OSError("injected: state write failed")
        return real(path, text)

    monkeypatch.setattr(store_module, "_atomic_write_text", boom)

    with pytest.raises(OSError):
        engine.import_plan(STATE, make_packet(task_id=STATE))

    # backup survived, main state is still the original old-schema bytes
    assert backup.is_file() and backup.read_bytes() == before_bytes
    assert state_path.read_bytes() == before_bytes
    assert _raw_version(store) == 4

    # retry succeeds, does not overwrite the backup
    engine.import_plan(STATE, make_packet(task_id=STATE))
    assert _raw_version(store) == STATE_SCHEMA_VERSION
    assert backup.read_bytes() == before_bytes
    assert [p.name for p in _backups(store)] == [backup.name]


def test_read_only_commands_never_migrate_state(tmp_path, monkeypatch):
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    monkeypatch.chdir(repo)
    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    assert runner.invoke(app, ["start", "read only"]).exit_code == 0
    store = ArtifactStore(repo)
    before_bytes = _downgrade(store, 4)

    for command in (
        ["status"],
        ["usage"],
        ["diff"],
        ["logs"],
        ["doctor"],
        ["config", "show"],
        ["profile", "list"],
    ):
        result = runner.invoke(app, command)
        assert result.exit_code == 0, (command, result.output)

    assert store.state_path(STATE).read_bytes() == before_bytes
    assert _raw_version(store) == 4
    assert _backups(store) == []

    # doctor sees the pending migration but must not perform it
    doctor = runner.invoke(app, ["doctor"])
    assert "migration to 5 pending" in doctor.output


def test_doctor_stops_reporting_pending_after_migration(tmp_path, monkeypatch):
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    monkeypatch.chdir(repo)
    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    assert runner.invoke(app, ["start", "doctor migration"]).exit_code == 0
    store = ArtifactStore(repo)
    before_bytes = _downgrade(store, 4)

    task_md = store.task_dir(STATE) / "task.md"
    task_md.write_text(
        "# Task DR-0001\n\n## Title\n\ndoctor migration\n\n## Objective\n\n"
        "exercise a real mutating write\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["plan", "import", str(task_md)])
    assert result.exit_code == 0, result.output

    assert _raw_version(store) == STATE_SCHEMA_VERSION
    assert (store.task_dir(STATE) / "state.v4.json.bak").read_bytes() == before_bytes
    doctor = runner.invoke(app, ["doctor"])
    assert doctor.exit_code == 0, doctor.output
    assert f"migration to {STATE_SCHEMA_VERSION} pending" not in doctor.output
    assert "DR-0001: policy valid" in doctor.output


def test_migrated_legacy_snapshot_task_keeps_its_frozen_policy(tmp_path):
    """Migrating a v0.2-A task must not brick its digest-less legacy snapshot."""
    _root, store, engine = build_engine(tmp_path)
    engine.create_task("t")
    snapshot_path(store, STATE).write_bytes(
        encode_lf(
            "pipeline:\n  max_fix_iterations: 3\n  auto_fix_tests: false\n"
            "  max_same_finding_cycles: 0\n"
            "budget:\n  max_implementer_calls: 4\n  max_reviewer_calls: 3\n"
            "  max_total_provider_calls: 7\n"
            "review:\n  provider: manual\n  blocking_severities: [P0, P1, P2]\n"
            "  retries: 1\n  transport_retries: 0\n  max_response_chars: 200000\n"
            "  max_diff_bytes: 300000\n  timeout_seconds: 120\n"
            "tests:\n  targeted: []\n  full: []\n  full_regression: release_only\n"
            "  timeout_seconds: 900\n"
            "scope:\n  reuse_approved_scope: true\n  current_delta_first: true\n"
            "baseline:\n  max_untracked_file_bytes: 52428800\n"
            "git:\n  allow_commit: false\n  allow_push: false\n  allow_tag: false\n"
            "  allow_reset_hard: false\n  allow_index_mutation: false\n"
            "codex:\n  executable: codex\n  args: ['exec']\n  prompt_mode: stdin\n"
            "  timeout_seconds: 1800\n"
            "profiles: []\n"
        )
    )
    before_bytes = _downgrade(store, 4, policy_source="snapshot")
    assert check_snapshot(store, store.read_task(STATE)).state is SnapshotState.VALID

    # real mutating write -> schema 5, digest still absent, no provenance path
    engine.import_plan(STATE, make_packet(task_id=STATE))
    migrated = store.read_task(STATE)
    assert migrated.state_schema_version == STATE_SCHEMA_VERSION
    assert migrated.policy_config_sha256 == ""
    assert migrated.policy_snapshot_path == ""

    # the legacy snapshot stays authoritative (and is still tolerated)
    assert check_snapshot(store, migrated).state is SnapshotState.VALID
    engine.config.budget.max_reviewer_calls = 99
    assert engine._task_config(migrated).budget.max_reviewer_calls == 3


def test_frozen_task_with_path_but_no_digest_still_fails_closed(tmp_path):
    _root, store, engine = build_engine(tmp_path)
    engine.create_task("t")
    task = store.read_task(STATE).model_copy(update={"policy_config_sha256": ""})
    store.write_task(task)  # path is still recorded -> metadata loss is real
    current = store.read_task(STATE)
    assert current.policy_snapshot_path
    assert check_snapshot(store, current).state is SnapshotState.INVALID


# ===========================================================================
# P2-2: refresh evidence attempts are unique, never reused, never overwritten
# ===========================================================================
def _policy_dir(store) -> Path:
    return store.policy_dir(STATE)


def _evidence_bytes(policy_dir: Path, attempt: int) -> dict[str, bytes]:
    return {
        p.name: p.read_bytes()
        for p in sorted(policy_dir.glob(f"policy-refresh-{attempt:02d}*"))
    }


def _changed_policy_setup(tmp_path, *, damage="hash_mismatch"):
    """A task whose frozen policy differs from the live one, snapshot damaged."""
    root, store, engine = build_engine(tmp_path)
    engine.create_task("t")
    engine.import_plan(STATE, make_packet(task_id=STATE))
    engine.config.budget.max_reviewer_calls = 7  # live policy now differs
    path = snapshot_path(store, STATE)
    if damage == "hash_mismatch":
        path.write_bytes(b"budget:\n  max_reviewer_calls: 1\n")
    elif damage == "missing":
        path.unlink()
    else:
        path.write_bytes(b"pipeline: [broken\n")
    return store, engine


def _inject_refresh_failure(store, boundary):
    """Patch the store instance so one refresh write boundary fails."""
    real = {
        "bytes": store.write_bytes,
        "text": store.write_text,
        "bytes_new": store.write_bytes_new,
        "text_new": store.write_text_new,
        "task": store.write_task,
    }

    def wb(path, data, *a, **k):
        if boundary == "snapshot" and str(path).endswith("config.snapshot.yaml"):
            raise OSError("injected: snapshot")
        return real["bytes"](path, data, *a, **k)

    def wbn(path, data, *a, **k):
        if boundary == "before" and str(path).endswith("-before.yaml"):
            raise OSError("injected: before evidence")
        return real["bytes_new"](path, data, *a, **k)

    def wtn(path, text, *a, **k):
        if boundary == "after" and str(path).endswith("-after.yaml"):
            raise OSError("injected: after evidence")
        if boundary == "record" and str(path).endswith(".json"):
            raise OSError("injected: refresh record")
        return real["text_new"](path, text, *a, **k)

    def wt(path, text, *a, **k):
        if boundary == "snapshot" and str(path).endswith("config.snapshot.yaml"):
            raise OSError("injected: snapshot")
        return real["text"](path, text, *a, **k)

    def wk(task, *a, **k):
        if boundary == "state":
            raise OSError("injected: state persist")
        return real["task"](task, *a, **k)

    store.write_bytes = wb
    store.write_text = wt
    store.write_bytes_new = wbn
    store.write_text_new = wtn
    store.write_task = wk

    def restore():
        store.write_bytes = real["bytes"]
        store.write_text = real["text"]
        store.write_bytes_new = real["bytes_new"]
        store.write_text_new = real["text_new"]
        store.write_task = real["task"]

    return restore


@pytest.mark.parametrize(
    "boundary", ["before", "after", "snapshot", "record", "state"]
)
def test_failed_refresh_evidence_is_never_overwritten_by_a_retry(tmp_path, boundary):
    store, engine = _changed_policy_setup(tmp_path)
    policy_dir = _policy_dir(store)
    restore = _inject_refresh_failure(store, boundary)
    try:
        with pytest.raises(OSError):
            engine.refresh_task_policy(STATE, f"failed {boundary}")
    finally:
        restore()

    # No provider was invoked, and the task fails closed (state unchanged or
    # hash mismatch) - an unrecorded generation can never execute.
    assert store.read_task(STATE).provider_calls == []
    damaged = store.read_task(STATE)
    assert check_snapshot(store, damaged).state is not SnapshotState.VALID
    with pytest.raises(PolicySnapshotError):
        engine._task_config(damaged)

    attempt_01 = _evidence_bytes(policy_dir, 1)
    # A failed attempt died on its very first evidence write (the "before"
    # boundary) leaves no durable evidence at all, so reusing attempt 01
    # overwrites nothing.  Otherwise the retry must take a NEW identity.
    expected_attempt = 2 if attempt_01 else 1

    engine.refresh_task_policy(STATE, "retry after failure")
    if attempt_01:
        assert _evidence_bytes(policy_dir, 1) == attempt_01
    retry_evidence = _evidence_bytes(policy_dir, expected_attempt)
    assert f"policy-refresh-{expected_attempt:02d}-after.yaml" in retry_evidence
    assert f"policy-refresh-{expected_attempt:02d}.json" in retry_evidence

    refreshed = store.read_task(STATE)
    record = refreshed.policy_refreshes[-1]
    assert record.evidence_attempt == expected_attempt
    assert record.refresh_id == f"{STATE}-P{expected_attempt:04d}"
    assert record.generation == 2
    assert refreshed.policy_provenance.generation == 2
    assert refreshed.policy_config_sha256 == sha256_file(snapshot_path(store, STATE))
    assert check_snapshot(store, refreshed).state is SnapshotState.VALID


def test_state_write_failure_after_snapshot_is_fail_closed_then_recovers(tmp_path):
    """Highest-risk sequence: snapshot replaced, state.json persist fails."""
    store, engine = _changed_policy_setup(tmp_path)
    policy_dir = _policy_dir(store)
    old_digest = store.read_task(STATE).policy_config_sha256
    restore = _inject_refresh_failure(store, "state")
    try:
        with pytest.raises(OSError):
            engine.refresh_task_policy(STATE, "state write fails")
    finally:
        restore()

    damaged = store.read_task(STATE)
    assert damaged.policy_config_sha256 == old_digest          # still generation 1
    assert damaged.policy_refreshes == []                      # nothing applied
    assert check_snapshot(store, damaged).state is SnapshotState.HASH_MISMATCH
    attempt_01 = _evidence_bytes(policy_dir, 1)
    assert "policy-refresh-01.json" in attempt_01              # orphan record kept

    engine.refresh_task_policy(STATE, "recovery retry")
    refreshed = store.read_task(STATE)
    assert _evidence_bytes(policy_dir, 1) == attempt_01        # untouched
    assert refreshed.policy_refreshes[-1].evidence_attempt == 2
    assert refreshed.policy_provenance.generation == 2
    assert check_snapshot(store, refreshed).state is SnapshotState.VALID


def test_orphan_evidence_and_gaps_allocate_the_next_attempt(tmp_path):
    store, engine = _started(tmp_path)
    policy_dir = _policy_dir(store)
    assert next_refresh_attempt(store.read_task(STATE), policy_dir) == 1

    # orphan attempt 01 on disk, never referenced by state
    (policy_dir / "policy-refresh-01-after.yaml").write_bytes(b"x")
    (policy_dir / "policy-refresh-01.json").write_bytes(b"{}")
    assert next_refresh_attempt(store.read_task(STATE), policy_dir) == 2

    # a persisted record with a higher attempt number (gap tolerated)
    record = store.read_task(STATE).policy_refreshes
    engine.refresh_task_policy(STATE, "first")
    task = store.read_task(STATE)
    task.policy_refreshes[-1] = task.policy_refreshes[-1].model_copy(
        update={"evidence_attempt": 5}
    )
    store.write_task(task)
    (policy_dir / "policy-refresh-07-before.yaml").write_bytes(b"y")
    assert next_refresh_attempt(store.read_task(STATE), policy_dir) == 8


def test_immutable_evidence_writer_refuses_to_overwrite(tmp_path):
    store, engine = _started(tmp_path)
    target = _policy_dir(store) / "policy-refresh-01-after.yaml"
    store.write_text_new(target, "first\n")
    with pytest.raises(DevRelayError):
        store.write_text_new(target, "second\n")
    assert target.read_bytes() == b"first\n"
    with pytest.raises(DevRelayError):
        store.write_bytes_new(target, b"second\n")
    assert target.read_bytes() == b"first\n"


def test_successful_refresh_still_uses_attempt_01_then_02(tmp_path):
    store, engine = _started(tmp_path)
    policy_dir = _policy_dir(store)
    # a task already written by this version needs no migration backup
    assert _backups(store) == []
    engine.refresh_task_policy(STATE, "first")
    first = store.read_task(STATE).policy_refreshes[-1]
    assert first.evidence_attempt == 1
    assert (policy_dir / "policy-refresh-01-before.yaml").is_file()
    assert (policy_dir / "policy-refresh-01-after.yaml").is_file()
    assert (policy_dir / "policy-refresh-01.json").is_file()

    engine.refresh_task_policy(STATE, "second")
    second = store.read_task(STATE).policy_refreshes[-1]
    assert second.evidence_attempt == 2
    assert (policy_dir / "policy-refresh-02.json").is_file()
    assert [r.generation for r in store.read_task(STATE).policy_refreshes] == [2, 3]
