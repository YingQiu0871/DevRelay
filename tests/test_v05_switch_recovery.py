"""Explicit run-level resolution of a pending/uncertain session switch.

The durable run document decides the outcome: a run that records the switch
gets the lease commit completed; a run that does not gets the target released.
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
SOURCE = "ses_source"
TARGET = "ses_target"
TOKEN = "d" * 32


def _pending(tmp_path: Path) -> tuple[SessionLeaseStore, dict]:
    store = SessionLeaseStore(tmp_path / ".devrelay")
    workspace = str(tmp_path / "ws")
    store.acquire(SOURCE, workspace=workspace, run_id=RUN_ID, role="implementer")
    target = store.acquire_pending_switch(
        TARGET,
        workspace=workspace,
        run_id=RUN_ID,
        role="implementer",
        source_session_id=SOURCE,
    )
    return store, target


def test_resolve_committed_activates_target_and_releases_source(tmp_path: Path):
    store, target = _pending(tmp_path)
    store.mark_switch_uncertain(target["switch_id"])
    assert store.switch_for_run(RUN_ID)["session_id"] == TARGET
    result = store.resolve_switch(target["switch_id"], run_committed=True)
    assert result["result"] == "committed"
    assert result["previous_state"] == "uncertain"
    assert store.get(TARGET)["state"] == "active"
    assert store.get(TARGET)["recovery"] == "explicit"
    assert store.get(SOURCE)["state"] == "released"
    assert store.get(SOURCE)["switched_to"] == TARGET
    assert store.switch_for_run(RUN_ID) is None
    assert store.blocking_for_run(RUN_ID) == []


def test_resolve_uncommitted_releases_target_and_keeps_source(tmp_path: Path):
    store, target = _pending(tmp_path)
    result = store.resolve_switch(target["switch_id"], run_committed=False)
    assert result["result"] == "aborted"
    assert result["previous_state"] == "pending_switch"
    assert store.get(TARGET)["state"] == "released"
    assert store.get(SOURCE)["state"] == "active"
    assert store.blocking_for_run(RUN_ID) == []


def test_resolve_committed_tolerates_already_released_source(tmp_path: Path):
    store, target = _pending(tmp_path)
    store.mark_switch_uncertain(target["switch_id"])
    store.recover(SOURCE, expected_state="active")
    result = store.resolve_switch(target["switch_id"], run_committed=True)
    assert result["result"] == "committed"
    assert store.get(TARGET)["state"] == "active"


def test_resolve_is_fail_closed(tmp_path: Path):
    store, target = _pending(tmp_path)
    with pytest.raises(SessionLeaseConflict):
        store.resolve_switch("SW-" + "0" * 32, run_committed=True)
    with pytest.raises(SessionLeaseConflict):
        store.resolve_switch("not-a-switch", run_committed=True)
    # A source lease reassigned to another run must not be released.
    data = store._read()
    data["leases"][SOURCE]["run_id"] = "DR-" + "b" * 32
    store._write(data)
    with pytest.raises(SessionLeaseConflict):
        store.resolve_switch(target["switch_id"], run_committed=True)
    assert store.get(TARGET)["state"] == "pending_switch"
    store.resolve_switch(target["switch_id"], run_committed=False)
    with pytest.raises(SessionLeaseConflict):
        store.resolve_switch(target["switch_id"], run_committed=False)


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


def _run_with_lease(workspace: Path, monkeypatch, client: TestClient):
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
    monkeypatch.setattr(
        api.service.surface.orchestration, "verify_session", lambda sid: None
    )
    return run, leases, api


def _switch(client: TestClient, run, headers, target: str):
    detail = client.get(f"/api/runs/{run.run_id}", headers=headers).json()["data"]
    return client.post(
        f"/api/runs/{run.run_id}/session/switch",
        json={
            "role": "implementer",
            "target_session_id": target,
            "expected_updated_at": detail["updated_at"],
            "expected_source_session_id": detail["implementer_session_id"],
            "confirm": "apply",
        },
        headers=headers,
    )


def test_uncertain_switch_resolves_to_committed_and_run_can_switch_again(
    client: TestClient, workspace: Path, monkeypatch
):
    run, leases, api = _run_with_lease(workspace, monkeypatch, client)
    headers = _headers(client)
    real_commit = api.service._session_leases.commit_switch
    monkeypatch.setattr(
        api.service._session_leases,
        "commit_switch",
        lambda switch_id: (_ for _ in ()).throw(SessionLeaseError("boom")),
    )
    failed = _switch(client, run, headers, TARGET)
    assert failed.status_code == 503
    assert failed.json()["error"]["code"] == "switch_lease_uncertain"
    monkeypatch.setattr(api.service._session_leases, "commit_switch", real_commit)

    detail = client.get(f"/api/runs/{run.run_id}", headers=headers).json()["data"]
    pending = detail["pending_switch"]
    assert pending["state"] == "uncertain"
    assert pending["source_session_id"] == run.implementer_session_id
    assert pending["target_session_id"] == TARGET

    no_confirm = client.post(
        f"/api/runs/{run.run_id}/session/switch/recover",
        json={"switch_id": pending["switch_id"], "confirm": "apply"},
        headers={SESSION_HEADER: headers[SESSION_HEADER]},
    )
    assert no_confirm.status_code == 403
    wrong_id = client.post(
        f"/api/runs/{run.run_id}/session/switch/recover",
        json={"switch_id": "SW-" + "0" * 32, "confirm": "apply"},
        headers=headers,
    )
    assert wrong_id.status_code == 409
    assert wrong_id.json()["error"]["code"] == "switch_not_pending"

    resolved = client.post(
        f"/api/runs/{run.run_id}/session/switch/recover",
        json={"switch_id": pending["switch_id"], "confirm": "apply"},
        headers=headers,
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["data"]["result"] == "committed"
    assert leases.get(TARGET)["state"] == "active"
    assert leases.get(run.implementer_session_id)["state"] == "released"
    after = client.get(f"/api/runs/{run.run_id}", headers=headers).json()["data"]
    assert after["pending_switch"] is None

    again = _switch(client, run, headers, "ses_third")
    assert again.status_code == 200, again.text
    assert again.json()["data"]["implementer_session_id"] == "ses_third"
    assert leases.get(TARGET)["state"] == "released"
    assert leases.get("ses_third")["state"] == "active"


def test_switch_interrupted_before_run_write_resolves_to_aborted(
    client: TestClient, workspace: Path, monkeypatch
):
    run, leases, _api = _run_with_lease(workspace, monkeypatch, client)
    headers = _headers(client)
    # Simulates a crash after the target lease and before the run write.
    pending = leases.acquire_pending_switch(
        TARGET,
        workspace=str(workspace.resolve()),
        run_id=run.run_id,
        role="implementer",
        source_session_id=run.implementer_session_id,
    )
    blocked = _switch(client, run, headers, "ses_other")
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "switch_pending"

    resolved = client.post(
        f"/api/runs/{run.run_id}/session/switch/recover",
        json={"switch_id": pending["switch_id"], "confirm": "apply"},
        headers=headers,
    )
    assert resolved.status_code == 200, resolved.text
    data = resolved.json()["data"]
    assert data["result"] == "aborted"
    assert data["session_id"] == run.implementer_session_id
    assert leases.get(TARGET)["state"] == "released"
    assert leases.get(run.implementer_session_id)["state"] == "active"
    detail = client.get(f"/api/runs/{run.run_id}", headers=headers).json()["data"]
    assert detail["implementer_session_id"] == run.implementer_session_id
    assert detail["session_switch_history"] == []


def test_resolve_refuses_when_run_and_lease_disagree(
    client: TestClient, workspace: Path, monkeypatch
):
    run, leases, _api = _run_with_lease(workspace, monkeypatch, client)
    headers = _headers(client)
    pending = leases.acquire_pending_switch(
        TARGET,
        workspace=str(workspace.resolve()),
        run_id=run.run_id,
        role="implementer",
        source_session_id=run.implementer_session_id,
    )
    # The lease claims a different source than the run records.
    data = leases._read()
    data["leases"][TARGET]["source_session_id"] = "ses_elsewhere"
    leases._write(data)
    response = client.post(
        f"/api/runs/{run.run_id}/session/switch/recover",
        json={"switch_id": pending["switch_id"], "confirm": "apply"},
        headers=headers,
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "switch_state_inconsistent"
    assert leases.get(TARGET)["state"] == "pending_switch"
