"""Session lease store tests (no switch endpoint is exposed)."""

from __future__ import annotations

from pathlib import Path

import pytest

from devrelay.web.session_leases import (
    SessionLeaseConflict,
    SessionLeaseError,
    SessionLeaseStore,
)


def test_acquire_release_and_active_lookup(tmp_path: Path):
    store = SessionLeaseStore(tmp_path / ".devrelay")
    lease = store.acquire(
        "sess-1",
        workspace=str(tmp_path / "workspace"),
        run_id="DR-" + "a" * 32,
        role="implementer",
    )
    assert lease["state"] == "active"
    assert store.get("sess-1") == lease
    assert store.active_for("DR-" + "a" * 32, "implementer") == [lease]
    assert store.release("sess-1") is True
    assert store.get("sess-1")["state"] == "released"
    assert store.release("sess-1") is False
    reacquired = store.acquire(
        "sess-1",
        workspace=str(tmp_path / "workspace"),
        run_id="DR-" + "b" * 32,
        role="reviewer",
    )
    assert reacquired["state"] == "active"
    assert reacquired["run_id"] == "DR-" + "b" * 32


def test_lease_conflicts_are_fail_closed(tmp_path: Path):
    store = SessionLeaseStore(tmp_path / ".devrelay")
    workspace = str(tmp_path / "workspace")
    store.acquire(
        "sess-1",
        workspace=workspace,
        run_id="DR-" + "a" * 32,
        role="implementer",
    )
    with pytest.raises(SessionLeaseConflict):
        store.acquire(
            "sess-1",
            workspace=workspace,
            run_id="DR-" + "b" * 32,
            role="implementer",
        )
    store.acquire(
        "sess-1",
        workspace=workspace,
        run_id="DR-" + "a" * 32,
        role="implementer",
    )
    store.mark_uncertain("sess-1")
    assert store.get("sess-1")["state"] == "uncertain"
    with pytest.raises(SessionLeaseConflict):
        store.acquire(
            "sess-1",
            workspace=workspace,
            run_id="DR-" + "c" * 32,
            role="reviewer",
        )


def test_explicit_recovery_releases_uncertain_or_active_lease(tmp_path: Path):
    store = SessionLeaseStore(tmp_path / ".devrelay")
    workspace = str(tmp_path / "workspace")
    store.acquire(
        "sess-1",
        workspace=workspace,
        run_id="DR-" + "a" * 32,
        role="implementer",
    )
    assert store.mark_uncertain("sess-1") is True
    recovered = store.recover("sess-1", expected_state="uncertain")
    assert recovered is not None
    assert recovered["state"] == "released"
    assert recovered["previous_state"] == "uncertain"
    assert store.recover("sess-1") is None
    store.acquire(
        "sess-2",
        workspace=workspace,
        run_id="DR-" + "b" * 32,
        role="reviewer",
    )
    with pytest.raises(SessionLeaseConflict):
        store.recover("sess-2", expected_state="uncertain")
    assert store.recover("sess-2")["previous_state"] == "active"


def test_corrupt_lease_store_fails_closed(tmp_path: Path):
    path = tmp_path / ".devrelay" / "web" / "session_leases.json"
    path.parent.mkdir(parents=True)
    path.write_text("not-json", encoding="utf-8")
    store = SessionLeaseStore(tmp_path / ".devrelay")
    with pytest.raises(SessionLeaseError):
        store.get("sess-1")
    with pytest.raises(SessionLeaseError):
        store.acquire(
            "sess-1",
            workspace=str(tmp_path / "workspace"),
            run_id="DR-" + "a" * 32,
            role="implementer",
        )
