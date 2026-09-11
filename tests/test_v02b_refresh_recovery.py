"""v0.2-B stage 3: explicit refresh / integrity recovery semantics."""

from __future__ import annotations

import pytest

from devrelay.artifacts.store import sha256_file
from devrelay.errors import (
    PolicySnapshotIntegrityError,
    PolicySnapshotMissingError,
    PolicySnapshotInvalidError,
)
from devrelay.pipeline.engine import PolicyRecoveryGrant
from devrelay.snapshot import SnapshotState, check_snapshot, snapshot_path

from helpers import (
    ScriptedAutoReviewer,
    build_engine,
    default_config,
    make_finding,
    make_packet,
    make_review,
)

STATE = "DR-0001"


def _started(tmp_path, *, reviewer=None):
    reviewer = reviewer or ScriptedAutoReviewer(
        [make_review("REQUEST_CHANGES", [make_finding("P2", title="b")]), make_review("PASS")]
    )
    _root, store, engine = build_engine(
        tmp_path, config=default_config(), reviewer=reviewer
    )
    engine.create_task("t")
    engine.import_plan(STATE, make_packet(task_id=STATE))
    return store, engine


def test_recovery_of_missing_snapshot_records_no_invented_before(tmp_path):
    store, engine = _started(tmp_path)
    snapshot_path(store, STATE).unlink()
    with pytest.raises(PolicySnapshotMissingError):
        engine.continue_task(STATE)

    engine.policy_recovery = PolicyRecoveryGrant(reason="snapshot lost")
    engine.continue_task(STATE)

    refreshed = store.read_task(STATE)
    record = refreshed.policy_refreshes[-1]
    assert refreshed.policy_source == "snapshot"
    assert refreshed.policy_provenance.generation == 2
    assert refreshed.policy_config_sha256 == sha256_file(snapshot_path(store, STATE))
    assert record.trigger == "integrity_recovery"
    assert record.before_state == "missing"
    assert record.before_snapshot_available is False
    assert record.before_sha256 == ""
    assert record.before_config_sha256 == ""
    assert record.before_path == ""
    assert record.usage_unchanged is True
    assert check_snapshot(store, refreshed).state is SnapshotState.VALID


def test_recovery_of_hash_mismatch_keeps_the_damaged_bytes_as_evidence(tmp_path):
    store, engine = _started(tmp_path)
    path = snapshot_path(store, STATE)
    path.write_bytes(b"not: a policy\n")
    damaged = path.read_bytes()

    engine.policy_recovery = PolicyRecoveryGrant(reason="snapshot edited")
    engine.continue_task(STATE)

    refreshed = store.read_task(STATE)
    record = refreshed.policy_refreshes[-1]
    assert record.before_state == "hash_mismatch"
    assert record.before_snapshot_available is True
    assert record.before_sha256 != ""
    evidence = store.root / record.before_path
    assert evidence.read_bytes() == damaged  # preserved, never re-serialized
    assert refreshed.policy_config_sha256 == sha256_file(path)


def test_recovery_of_invalid_yaml_fails_closed_first(tmp_path):
    store, engine = _started(tmp_path)
    snapshot_path(store, STATE).write_bytes(b"pipeline: [unclosed\n")
    with pytest.raises(PolicySnapshotIntegrityError):
        engine.continue_task(STATE)  # digest is checked before parsing
    engine.policy_recovery = PolicyRecoveryGrant(reason="repair")
    engine.continue_task(STATE)
    assert check_snapshot(store, store.read_task(STATE)).state is SnapshotState.VALID


def test_generation_counts_evidence_not_semantic_change(tmp_path):
    store, engine = _started(tmp_path)
    first_bytes = snapshot_path(store, STATE).read_bytes()

    engine.refresh_task_policy(STATE, "same policy, new generation")
    second = store.read_task(STATE)
    assert second.policy_provenance.generation == 2
    assert snapshot_path(store, STATE).read_bytes() == first_bytes  # identical bytes
    assert second.policy_config_sha256 == sha256_file(snapshot_path(store, STATE))
    assert second.policy_refreshes[-1].generation == 2

    engine.refresh_task_policy(STATE, "again")
    third = store.read_task(STATE)
    assert third.policy_provenance.generation == 3
    assert [r.generation for r in third.policy_refreshes] == [2, 3]


def test_refresh_preserves_usage_calls_and_history(tmp_path):
    store, engine = _started(tmp_path)
    engine.continue_task(STATE)
    before = store.read_task(STATE)
    call_ids = [record.call_id for record in before.provider_calls]
    sequences = (
        before.next_provider_call_sequence,
        before.next_provider_attempt_sequence,
        before.next_review_attempt_sequence,
    )
    history = len(before.review_history)
    assert call_ids  # the run really did spend calls

    engine.refresh_task_policy(STATE, "raise the budget")
    after = store.read_task(STATE)
    assert [record.call_id for record in after.provider_calls] == call_ids
    assert (
        after.next_provider_call_sequence,
        after.next_provider_attempt_sequence,
        after.next_review_attempt_sequence,
    ) == sequences
    assert len(after.review_history) == history
    assert after.policy_refreshes[-1].usage_unchanged is True


def test_engine_refresh_api_stays_usable_without_force(tmp_path):
    """v0.2-A contract: the audited engine call replaces a valid snapshot."""
    store, engine = _started(tmp_path)
    engine.config.budget.max_reviewer_calls = 2
    engine.refresh_task_policy(STATE, "tighten reviewer budget")
    document = engine._task_config(store.read_task(STATE))
    assert document.budget.max_reviewer_calls == 2
