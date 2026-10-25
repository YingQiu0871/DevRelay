"""Tests-first fault scenarios for the future switch transaction.

The endpoint and the pending-switch lease primitive are intentionally not
implemented.  Runnable tests here cover the current lease-store constraint and
corruption fail-closed; endpoint fault scenarios are skipped with an explicit
reason so they cannot be mistaken for implemented behavior.
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


def test_current_store_cannot_hold_source_and_target_for_one_run_role(tmp_path: Path):
    """Documents the missing pending-switch primitive.

    A switch needs both the source (active) and target (pending) lease while the
    run/role is unchanged.  The current all-or-nothing lease store rejects the
    second acquisition; this is a design blocker, not an endpoint test.
    """
    store = SessionLeaseStore(tmp_path / ".devrelay")
    workspace = str(tmp_path / "ws")
    store.acquire(
        SOURCE,
        workspace=workspace,
        run_id=RUN_ID,
        role="implementer",
    )
    with pytest.raises(SessionLeaseConflict):
        store.acquire(
            TARGET,
            workspace=workspace,
            run_id=RUN_ID,
            role="implementer",
        )


def test_corrupt_switch_lease_store_fails_closed(tmp_path: Path):
    path = tmp_path / ".devrelay" / "web" / "session_leases.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not-json", encoding="utf-8")
    store = SessionLeaseStore(tmp_path / ".devrelay")
    with pytest.raises(SessionLeaseError):
        store.acquire(
            TARGET,
            workspace=str(tmp_path / "ws"),
            run_id=RUN_ID,
            role="implementer",
        )


@pytest.mark.skip(
    reason="switch endpoint and pending-switch lease primitive not implemented; "
    "schema approved with conditions"
)
def test_crash_after_target_acquisition_leaves_source_active_and_target_recoverable(
    tmp_path: Path,
) -> None:
    # Contract for the future implementation:
    # - source remains active
    # - target is pending/uncertain, never auto-activated
    # - run session fields are unchanged
    # - explicit lease recovery can clear target
    assert False


@pytest.mark.skip(
    reason="switch endpoint and pending-switch lease primitive not implemented; "
    "schema approved with conditions"
)
def test_crash_after_run_commit_before_source_release_needs_explicit_recovery(
    tmp_path: Path,
) -> None:
    # Contract for the future implementation:
    # - v3 run evidence contains the committed switch
    # - source lease remains active until explicitly recovered
    # - no automatic retry/reassignment
    assert False


@pytest.mark.skip(
    reason="switch endpoint not implemented; schema approved with conditions"
)
def test_in_flight_or_pending_reply_blocks_switch(tmp_path: Path) -> None:
    # Contract: both conditions reject before acquiring any target lease.
    assert False
