"""Explicit lease re-attachment for a run's current role session.

The run document names the session; any other active lease left for the same
run/role is orphaned and released in the same write.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from starlette.testclient import TestClient

from devrelay.config import install_default_config
from devrelay.web.app import create_app
from devrelay.web.auth import SESSION_HEADER
from devrelay.web.session_leases import (
    SessionLeaseConflict,
    SessionLeaseError,
    SessionLeaseStore,
)

RUN_ID = "DR-" + "a" * 32
TOKEN = "e" * 32


def test_reattach_releases_orphan_and_activates_current(tmp_path: Path):
    store = SessionLeaseStore(tmp_path / ".devrelay")
    workspace = str(tmp_path / "ws")
    store.acquire("ses_old", workspace=workspace, run_id=RUN_ID, role="implementer")
    result = store.reattach("ses_new", workspace=workspace, run_id=RUN_ID, role="implementer")
    assert result["released_orphans"] == ["ses_old"]
    assert store.get("ses_old")["state"] == "released"
    assert store.get("ses_old")["superseded_by"] == "ses_new"
    assert store.get("ses_new")["state"] == "active"
    assert store.get("ses_new")["recovery"] == "reattach"
    assert [e["session_id"] for e in store.active_for(RUN_ID, "implementer")] == ["ses_new"]


def test_reattach_reuses_a_released_lease_without_touching_other_roles(tmp_path: Path):
    store = SessionLeaseStore(tmp_path / ".devrelay")
    workspace = str(tmp_path / "ws")
    store.acquire("ses_impl", workspace=workspace, run_id=RUN_ID, role="implementer")
    store.acquire("ses_rev", workspace=workspace, run_id=RUN_ID, role="reviewer")
    store.release("ses_impl")
    result = store.reattach("ses_impl", workspace=workspace, run_id=RUN_ID, role="implementer")
    assert result["released_orphans"] == []
    assert store.get("ses_impl")["state"] == "active"
    assert store.get("ses_rev")["state"] == "active"


def test_reattach_is_fail_closed(tmp_path: Path):
    store = SessionLeaseStore(tmp_path / ".devrelay")
    workspace = str(tmp_path / "ws")
    store.acquire("ses_a", workspace=workspace, run_id=RUN_ID, role="implementer")
    with pytest.raises(SessionLeaseConflict):  # already holds this run's lease
        store.reattach("ses_a", workspace=workspace, run_id=RUN_ID, role="implementer")
    store.acquire("ses_b", workspace=workspace, run_id="DR-" + "b" * 32, role="implementer")
    with pytest.raises(SessionLeaseConflict):  # leased by another run
        store.reattach("ses_b", workspace=workspace, run_id=RUN_ID, role="implementer")
    store.acquire_pending_switch(
        "ses_c", workspace=workspace, run_id=RUN_ID, role="implementer", source_session_id="ses_a"
    )
    with pytest.raises(SessionLeaseConflict):  # unresolved switch on the run
        store.reattach("ses_d", workspace=workspace, run_id=RUN_ID, role="reviewer")
    assert store.get("ses_a")["state"] == "active"
    assert store.get("ses_d") is None


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    (root / ".devrelay").mkdir(parents=True)
    install_default_config(root / ".devrelay" / "config.yaml")
    return root


@pytest.fixture
def client(workspace: Path):
    app = create_app(str(workspace), port=8765, token=TOKEN)
    with TestClient(
        app, base_url="http://127.0.0.1:8765", raise_server_exceptions=False
    ) as test_client:
        yield test_client


def _headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/session", json={"token": TOKEN})
    assert response.status_code == 200
    return {
        SESSION_HEADER: response.json()["data"]["session_token"],
        "X-DevRelay-Confirm": "apply",
    }


def _detail(client: TestClient, run_id: str, headers) -> dict:
    return client.get(f"/api/runs/{run_id}", headers=headers).json()["data"]


def _reattach(client: TestClient, run_id: str, headers, role="implementer", updated_at=None):
    if updated_at is None:
        updated_at = _detail(client, run_id, headers)["updated_at"]
    return client.post(
        f"/api/runs/{run_id}/session/lease/reattach",
        json={"role": role, "expected_updated_at": updated_at, "confirm": "apply"},
        headers=headers,
    )


def test_reattach_unsticks_a_run_after_generic_target_recovery(
    client: TestClient, workspace: Path, monkeypatch
):
    """The pre-0.5.0 residual: uncertain switch, then generic /lease/recover of the target."""
    from devrelay.orchestration.store import OrchestrationStore
    from v03d_helpers import honest_run

    run = honest_run(workspace=str(workspace.resolve()))
    OrchestrationStore(workspace / ".devrelay").create(run)
    leases = SessionLeaseStore(workspace / ".devrelay")
    leases.acquire(
        run.implementer_session_id,
        workspace=str(workspace.resolve()),
        run_id=run.run_id,
        role="implementer",
    )
    api = client.app.app.state.api
    monkeypatch.setattr(api.service.surface.orchestration, "verify_session", lambda sid: None)
    real_commit = api.service._session_leases.commit_switch
    monkeypatch.setattr(
        api.service._session_leases,
        "commit_switch",
        lambda switch_id: (_ for _ in ()).throw(SessionLeaseError("boom")),
    )
    headers = _headers(client)
    detail = _detail(client, run.run_id, headers)
    failed = client.post(
        f"/api/runs/{run.run_id}/session/switch",
        json={
            "role": "implementer",
            "target_session_id": "ses_target",
            "expected_updated_at": detail["updated_at"],
            "expected_source_session_id": run.implementer_session_id,
            "confirm": "apply",
        },
        headers=headers,
    )
    assert failed.json()["error"]["code"] == "switch_lease_uncertain"
    monkeypatch.setattr(api.service._session_leases, "commit_switch", real_commit)
    # The old generic path: release the uncertain target directly.
    assert client.post(
        "/api/sessions/ses_target/lease/recover",
        json={"confirm": "apply", "expected_state": "uncertain"},
        headers=headers,
    ).status_code == 200
    stuck = _detail(client, run.run_id, headers)
    assert stuck["pending_switch"] is None
    assert stuck["role_leases"]["implementer"] == "released"

    response = _reattach(client, run.run_id, headers)
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["session_id"] == "ses_target"
    assert data["released_orphans"] == [run.implementer_session_id]
    assert leases.get("ses_target")["state"] == "active"
    assert leases.get(run.implementer_session_id)["state"] == "released"
    assert _detail(client, run.run_id, headers)["role_leases"]["implementer"] == "active"

    again = client.post(
        f"/api/runs/{run.run_id}/session/switch",
        json={
            "role": "implementer",
            "target_session_id": "ses_next",
            "expected_updated_at": _detail(client, run.run_id, headers)["updated_at"],
            "expected_source_session_id": "ses_target",
            "confirm": "apply",
        },
        headers=headers,
    )
    assert again.status_code == 200, again.text
    assert leases.get("ses_next")["state"] == "active"


def test_reattach_endpoint_refusals(client: TestClient, workspace: Path):
    from devrelay.orchestration.models import RunState
    from devrelay.orchestration.store import OrchestrationStore
    from v03d_helpers import honest_run

    store = OrchestrationStore(workspace / ".devrelay")
    run = honest_run(workspace=str(workspace.resolve()))
    store.create(run)
    leases = SessionLeaseStore(workspace / ".devrelay")
    leases.acquire(
        run.implementer_session_id,
        workspace=str(workspace.resolve()),
        run_id=run.run_id,
        role="implementer",
    )
    headers = _headers(client)

    no_confirm = client.post(
        f"/api/runs/{run.run_id}/session/lease/reattach",
        json={"role": "implementer", "expected_updated_at": "x", "confirm": "apply"},
        headers={SESSION_HEADER: headers[SESSION_HEADER]},
    )
    assert no_confirm.status_code == 403
    stale = _reattach(client, run.run_id, headers, updated_at="stale")
    assert stale.status_code == 409 and stale.json()["error"]["code"] == "run_changed"
    active = _reattach(client, run.run_id, headers)
    assert active.status_code == 409 and active.json()["error"]["code"] == "lease_already_active"

    # The reviewer session is held by another run: refuse, change nothing.
    leases.acquire(
        run.reviewer_session_id,
        workspace=str(workspace.resolve()),
        run_id="DR-" + "c" * 32,
        role="reviewer",
    )
    assert _detail(client, run.run_id, headers)["role_leases"]["reviewer"] == "held_elsewhere"
    held = _reattach(client, run.run_id, headers, role="reviewer")
    assert held.status_code == 409 and held.json()["error"]["code"] == "session_leased"

    leases.acquire_pending_switch(
        "ses_pending",
        workspace=str(workspace.resolve()),
        run_id=run.run_id,
        role="implementer",
        source_session_id=run.implementer_session_id,
    )
    pending = _reattach(client, run.run_id, headers, role="reviewer")
    assert pending.status_code == 409 and pending.json()["error"]["code"] == "switch_pending"

    terminal = honest_run(
        RunState.COMPLETED, workspace=str(workspace.resolve()), run_id="DR-" + "1" * 32
    )
    store.create(terminal)
    done = _reattach(client, terminal.run_id, headers)
    assert done.status_code == 409 and done.json()["error"]["code"] == "run_terminal"


def test_ui_exposes_explicit_reattach(client: TestClient):
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    assert 'id="run-lease-reattach"' in html
    assert 'id="run-lease-role"' in html
    assert "reattachLease" in script
    assert "/session/lease/reattach" in script
    assert "expected_updated_at: detail.updated_at" in script
