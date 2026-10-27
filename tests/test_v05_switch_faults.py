"""Lease-level switch fault tests.

The pending-switch lease primitive, v3 run schema and HTTP switch endpoint are
implemented; endpoint-level fault tests live beside the WebUI API tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from devrelay.web.session_leases import (
    SessionLeaseConflict,
    SessionLeaseError,
    SessionLeaseStore,
)

RUN_ID = "DR-" + "a" * 32
SOURCE = "ses_source"
TARGET = "ses_target"
WORKSPACE = "ws"


def _store(tmp_path: Path) -> SessionLeaseStore:
    return SessionLeaseStore(tmp_path / ".devrelay")


def test_pending_switch_holds_target_beside_active_source(tmp_path: Path):
    store = _store(tmp_path)
    workspace = str(tmp_path / WORKSPACE)
    store.acquire(SOURCE, workspace=workspace, run_id=RUN_ID, role="implementer")
    target = store.acquire_pending_switch(
        TARGET,
        workspace=workspace,
        run_id=RUN_ID,
        role="implementer",
        source_session_id=SOURCE,
    )
    assert target["state"] == "pending_switch"
    assert target["source_session_id"] == SOURCE
    assert store.get(SOURCE)["state"] == "active"
    assert store.get(TARGET)["state"] == "pending_switch"
    with pytest.raises(SessionLeaseConflict):
        store.acquire_pending_switch(
            "ses_other",
            workspace=workspace,
            run_id=RUN_ID,
            role="implementer",
            source_session_id=SOURCE,
        )


def test_commit_switch_atomically_activates_target_and_releases_source(tmp_path: Path):
    store = _store(tmp_path)
    workspace = str(tmp_path / WORKSPACE)
    store.acquire(SOURCE, workspace=workspace, run_id=RUN_ID, role="implementer")
    target = store.acquire_pending_switch(
        TARGET,
        workspace=workspace,
        run_id=RUN_ID,
        role="implementer",
        source_session_id=SOURCE,
    )
    result = store.commit_switch(target["switch_id"])
    assert result["target"]["state"] == "active"
    assert result["source"]["state"] == "released"
    assert store.pending_switch(target["switch_id"]) is None
    assert store.active_for(RUN_ID, "implementer")[0]["session_id"] == TARGET


def test_abort_or_uncertain_switch_never_releases_source(tmp_path: Path):
    store = _store(tmp_path)
    workspace = str(tmp_path / WORKSPACE)
    store.acquire(SOURCE, workspace=workspace, run_id=RUN_ID, role="implementer")

    aborted = store.acquire_pending_switch(
        TARGET,
        workspace=workspace,
        run_id=RUN_ID,
        role="implementer",
        source_session_id=SOURCE,
    )
    store.abort_switch(aborted["switch_id"])
    assert store.get(TARGET)["state"] == "released"
    assert store.get(SOURCE)["state"] == "active"

    uncertain = store.acquire_pending_switch(
        "ses_target_2",
        workspace=workspace,
        run_id=RUN_ID,
        role="implementer",
        source_session_id=SOURCE,
    )
    store.mark_switch_uncertain(uncertain["switch_id"])
    assert store.get("ses_target_2")["state"] == "uncertain"
    assert store.get(SOURCE)["state"] == "active"
    recovered = store.recover("ses_target_2")
    assert recovered["previous_state"] == "uncertain"
    assert store.get(SOURCE)["state"] == "active"


def test_crash_after_pending_target_leaves_source_active_and_target_recoverable(
    tmp_path: Path,
):
    store = _store(tmp_path)
    workspace = str(tmp_path / WORKSPACE)
    store.acquire(SOURCE, workspace=workspace, run_id=RUN_ID, role="implementer")
    target = store.acquire_pending_switch(
        TARGET,
        workspace=workspace,
        run_id=RUN_ID,
        role="implementer",
        source_session_id=SOURCE,
    )
    # Simulate a crash before commit: no automatic activation/reassignment.
    assert store.get(SOURCE)["state"] == "active"
    assert store.get(TARGET)["state"] == "pending_switch"
    assert store.active_for(RUN_ID, "implementer")[0]["session_id"] == SOURCE
    recovered = store.recover(TARGET, expected_state="pending_switch")
    assert recovered["state"] == "released"
    assert store.get(SOURCE)["state"] == "active"
    assert target["switch_id"]


def test_corrupt_switch_lease_store_fails_closed(tmp_path: Path):
    path = tmp_path / ".devrelay" / "web" / "session_leases.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not-json", encoding="utf-8")
    store = _store(tmp_path)
    with pytest.raises(SessionLeaseError):
        store.acquire_pending_switch(
            TARGET,
            workspace=str(tmp_path / WORKSPACE),
            run_id=RUN_ID,
            role="implementer",
            source_session_id=SOURCE,
        )
