"""v0.4-B static WebUI and editable config projection."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from devrelay.config import install_default_config
from devrelay.web.app import create_app
from devrelay.web.auth import SESSION_HEADER

TOKEN = "b" * 32
BASE_URL = "http://127.0.0.1:8765"


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    (root / ".devrelay").mkdir(parents=True)
    install_default_config(root / ".devrelay" / "config.yaml")
    return root


@pytest.fixture
def client(workspace: Path):
    app = create_app(str(workspace), port=8765, token=TOKEN)
    with TestClient(app, base_url=BASE_URL, raise_server_exceptions=False) as test_client:
        yield test_client


def _auth(client: TestClient) -> dict[str, str]:
    response = client.post("/api/session", json={"token": TOKEN})
    assert response.status_code == 200
    assert "set-cookie" not in response.headers
    return {SESSION_HEADER: response.json()["data"]["session_token"]}


def test_ui_index_is_public_and_locked_down(client: TestClient, workspace: Path):
    response = client.get("/")
    assert response.status_code == 200
    assert "DevRelay" in response.text
    assert str(workspace) not in response.text
    csp = response.headers["content-security-policy"]
    assert "script-src 'self'" in csp
    assert "connect-src 'self'" in csp
    assert "form-action 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "set-cookie" not in response.headers


def test_ui_assets_are_fixed_and_have_security_headers(client: TestClient):
    script = client.get("/assets/app.js")
    assert script.status_code == 200
    assert script.headers["content-type"].startswith("text/javascript")
    assert "X-DevRelay-Session" in script.text
    assert "document.cookie" not in script.text
    for unsafe in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write"):
        assert unsafe not in script.text
    assert "history.replaceState" in script.text
    assert "sessionStorage" in script.text
    assert "pruneUnchanged" in script.text
    assert "configBaseline" in script.text
    assert "readFormPatch" in script.text
    assert "connect-src 'self'" in script.headers["content-security-policy"]

    styles = client.get("/assets/styles.css")
    assert styles.status_code == 200
    assert styles.headers["content-type"].startswith("text/css")


def test_ui_asset_allowlist_rejects_unknown_and_traversal_paths(client: TestClient):
    assert client.get("/assets/nope.js").status_code == 404
    assert client.get("/assets/..%2F..%2Fconfig.yaml").status_code in (404, 405)


def test_ui_assets_are_packaged():
    package = files("devrelay.web")
    assert package.joinpath("static/index.html").is_file()
    assert package.joinpath("static/app.js").is_file()
    assert package.joinpath("static/styles.css").is_file()


def test_ui_still_rejects_wrong_host(client: TestClient):
    assert client.get("/", headers={"Host": "evil.example:8765"}).status_code == 400


def test_ui_alias_and_wrong_origin(client: TestClient):
    assert client.get("/ui").status_code == 200
    rejected = client.get("/", headers={"Origin": "http://evil.example:8765"})
    assert rejected.status_code == 403


def test_config_view_has_only_editable_projection(client: TestClient):
    auth = _auth(client)
    before = client.get("/api/config", headers=auth)
    digest = before.json()["data"]["config_sha256"]
    applied = client.put(
        "/api/config",
        json={
            "expected_sha256": digest,
            "config": {"pipeline": {"max_fix_iterations": 2}},
            "confirm": "apply",
        },
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert applied.status_code == 200, applied.text
    config = client.get("/api/config", headers=auth)
    data = config.json()["data"]
    editable = data["editable_config"]
    assert editable["pipeline"]["max_fix_iterations"] == 2
    assert "opencode" in editable
    assert "base_url" not in editable["opencode"]
    assert "workspace" not in editable["opencode"]
    assert "profiles" not in editable
    assert "provider" not in editable.get("review", {})
    assert "targeted" not in editable.get("tests", {})
    assert "full" not in editable.get("tests", {})
    assert data["restart_required"] is True


def test_ui_form_has_no_excluded_wiring_inputs(client: TestClient):
    html = client.get("/").text
    assert 'name="pipeline.max_fix_iterations"' in html
    for forbidden in (
        'name="codex.executable"',
        'name="codex.args"',
        'name="opencode.base_url"',
        'name="opencode.workspace"',
        'name="profiles"',
        'name="tests.targeted"',
        'name="review.provider"',
    ):
        assert forbidden not in html


def test_config_view_excludes_wiring_and_shell_commands(client: TestClient, workspace: Path):
    auth = _auth(client)
    config_path = workspace / ".devrelay" / "config.yaml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8")
        + "\ntests:\n  targeted: [\"echo hi\"]\n  timeout_seconds: 900\n",
        encoding="utf-8",
    )
    editable = client.get("/api/config", headers=auth).json()["data"]["editable_config"]
    assert editable["tests"]["timeout_seconds"] == 900
    assert "targeted" not in editable["tests"]
    assert "full" not in editable["tests"]
    assert "executable" not in editable.get("codex", {})
    assert "args" not in editable.get("codex", {})
    assert "launcher_args" not in editable.get("codex", {})


def test_editable_projection_drops_secret_named_policy_keys(client: TestClient, workspace: Path):
    auth = _auth(client)
    config_path = workspace / ".devrelay" / "config.yaml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8")
        + "\npipeline:\n  token: \"not-for-the-ui\"\n",
        encoding="utf-8",
    )
    editable = client.get("/api/config", headers=auth).json()["data"]["editable_config"]
    assert "token" not in editable.get("pipeline", {})


def test_config_view_marks_missing_config_unwritable(client: TestClient, workspace: Path):
    auth = _auth(client)
    (workspace / ".devrelay" / "config.yaml").unlink()
    data = client.get("/api/config", headers=auth).json()["data"]
    assert data["write_supported"] is False
    assert data["editable_config"] == {}


def test_wiring_view_is_separate_and_reference_only(client: TestClient, workspace: Path):
    auth = _auth(client)
    response = client.get("/api/wiring", headers=auth)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["config_sha256"]) == 64
    assert data["write_supported"] is True
    assert data["opencode"]["base_url"] == ""
    assert data["opencode"]["allow_unknown_workspace"] is False
    assert data["credentials"]["opencode_token"]["env"] == "DEVRELAY_OPENCODE_TOKEN"
    assert "value" not in data["credentials"]["opencode_token"]
    assert data["mcp"]["transport"] == "stdio"
    assert str(workspace) not in response.text
    assert TOKEN not in response.text


def test_wiring_write_updates_endpoint_with_backup(client: TestClient, workspace: Path):
    auth = _auth(client)
    before = client.get("/api/wiring", headers=auth).json()["data"]
    config_path = workspace / ".devrelay" / "config.yaml"
    old_text = config_path.read_text(encoding="utf-8")
    response = client.put(
        "/api/wiring",
        json={
            "expected_sha256": before["config_sha256"],
            "wiring": {"opencode": {"base_url": "http://127.0.0.1:4096"}},
            "confirm": "apply",
        },
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["applied"] is True
    assert data["restart_required"] is True
    assert data["write_scope"] == "OpenCode endpoint wiring only"
    assert data["backup_created"] is True
    updated_text = config_path.read_text(encoding="utf-8")
    assert "127.0.0.1:4096" in updated_text
    assert "review:" in updated_text
    assert "opencode:" in updated_text
    backups = list((workspace / ".devrelay").glob("config.yaml.bak-*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == old_text
    refreshed = client.get("/api/wiring", headers=auth).json()["data"]
    assert refreshed["opencode"]["base_url"] == "http://127.0.0.1:4096"
    assert refreshed["config_sha256"] != before["config_sha256"]


def test_wiring_write_rejects_non_endpoint_fields(client: TestClient):
    auth = _auth(client)
    digest = client.get("/api/wiring", headers=auth).json()["data"]["config_sha256"]
    for wiring in (
        {"opencode": {"workspace": "C:\\outside"}},
        {"opencode": {"allow_unknown_workspace": True}},
        {"codex": {"executable": "evil.exe"}},
    ):
        response = client.put(
            "/api/wiring",
            json={"expected_sha256": digest, "wiring": wiring, "confirm": "apply"},
            headers={**auth, "X-DevRelay-Confirm": "apply"},
        )
        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "config_field_not_editable"


def test_wiring_write_rejects_remote_endpoint(client: TestClient, workspace: Path):
    auth = _auth(client)
    digest = client.get("/api/wiring", headers=auth).json()["data"]["config_sha256"]
    before = (workspace / ".devrelay" / "config.yaml").read_bytes()
    response = client.put(
        "/api/wiring",
        json={
            "expected_sha256": digest,
            "wiring": {"opencode": {"base_url": "https://remote.example:4096"}},
            "confirm": "apply",
        },
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "endpoint_not_local"
    assert (workspace / ".devrelay" / "config.yaml").read_bytes() == before


def test_wiring_view_does_not_expose_workspace_or_token_value(
    client: TestClient, workspace: Path, monkeypatch
):
    monkeypatch.setenv("DEVRELAY_OPENCODE_TOKEN", "opencode-super-secret-value")
    auth = _auth(client)
    config_path = workspace / ".devrelay" / "config.yaml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            'workspace: ""', 'workspace: "C:\\\\outside"'
        ),
        encoding="utf-8",
    )
    response = client.get("/api/wiring", headers=auth)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["opencode"]["workspace_override"] is True
    assert "opencode-super-secret-value" not in response.text
    assert "C:\\\\outside" not in response.text
    assert data["credentials"]["opencode_token"]["configured"] is True


def test_wiring_write_requires_confirmation_and_current_digest(client: TestClient):
    auth = _auth(client)
    digest = client.get("/api/wiring", headers=auth).json()["data"]["config_sha256"]
    body = {
        "expected_sha256": digest,
        "wiring": {"opencode": {"base_url": ""}},
        "confirm": "apply",
    }
    assert client.put("/api/wiring", json=body, headers=auth).status_code == 403
    stale = client.put(
        "/api/wiring",
        json={**body, "expected_sha256": "0" * 64},
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "config_changed"
    assert client.get("/api/wiring").status_code == 401


def test_connections_ui_has_no_credential_or_workspace_input(client: TestClient):
    html = client.get("/").text
    assert 'id="opencode-base-url"' in html
    assert 'name="opencode.base_url"' not in html
    assert 'name="opencode.workspace"' not in html
    assert 'name="DEVRELAY_OPENCODE_TOKEN"' not in html
    assert "Connections" in html


def test_dashboard_run_detail_uses_existing_read_api(client: TestClient, workspace: Path):
    from devrelay.orchestration.store import OrchestrationStore
    from v03d_helpers import honest_run

    auth = _auth(client)
    store = OrchestrationStore(workspace / ".devrelay")
    run = honest_run(workspace=str(workspace.resolve()))
    store.create(run)
    listed = client.get("/api/runs", headers=auth)
    assert listed.status_code == 200
    assert any(item["run_id"] == run.run_id for item in listed.json()["data"]["runs"])
    detail = client.get(f"/api/runs/{run.run_id}", headers=auth)
    assert detail.status_code == 200, detail.text
    data = detail.json()["data"]
    assert data["run_id"] == run.run_id
    assert "state" in data
    assert "implementer_turns" in data


def test_dashboard_has_auto_refresh_and_no_run_controls(client: TestClient):
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    for marker in ("run-detail", "auto-refresh", "refresh-runs", "Decision history"):
        assert marker in html
    assert "loadRunDetail" in script
    assert "/api/runs/" in script
    assert "runDetailRequest" in script
    assert "refreshInFlight" in script
    assert "submission_uncertain" in script
    assert "setInterval(refreshRuns, 5000)" in script
    assert "clearInterval(state.autoTimer)" in script
    assert 'id="run-decide"' in html
    assert 'id="run-interrupt"' in html
    for control in ("pause", "sendPrompt", "manual-prompt", "stream"):
        assert f'id="{control}"' not in html


def test_task_dashboard_uses_read_only_task_api(client: TestClient, workspace: Path):
    from devrelay.artifacts.store import ArtifactStore
    from devrelay.models import TaskRun

    auth = _auth(client)
    store = ArtifactStore(workspace)
    store.ensure_initialized()
    task_id = store.allocate_task_id()
    store.write_task(TaskRun(task_id=task_id, title="Seeded dashboard task"))
    listed = client.get("/api/tasks?limit=20", headers=auth)
    assert listed.status_code == 200
    data = listed.json()["data"]
    assert data["total"] == 1
    assert data["tasks"][0]["task_id"] == task_id
    detail = client.get(f"/api/tasks/{task_id}", headers=auth)
    assert detail.status_code == 200, detail.text
    payload = detail.json()["data"]
    assert payload["task_id"] == task_id
    assert payload["title"] == "Seeded dashboard task"
    assert payload["git"]["available"] is False
    assert "diff" not in payload["git"]
    assert payload["tests"]["passed"] is None
    assert payload["usage"]["total_calls"] == 0
    assert "provider_calls" in payload["usage"]
    assert client.get("/api/tasks/not-a-task", headers=auth).status_code == 400
    assert client.get("/api/tasks/DR-0001%0A", headers=auth).status_code == 400
    assert client.get("/api/tasks/DR-9999", headers=auth).status_code == 404
    assert client.get("/api/tasks").status_code == 401


def test_task_store_corruption_is_503(client: TestClient, workspace: Path):
    auth = _auth(client)
    (workspace / ".devrelay" / "state.json").write_text("{not-json", encoding="utf-8")
    response = client.get("/api/tasks", headers=auth)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "task_store_unreadable"


def test_ui_has_task_dashboard_markers(client: TestClient):
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    for marker in ("task-detail", "tasks-view", "Tests &amp; evidence", "Review findings"):
        assert marker in html
    assert "/api/tasks" in script
    assert "loadTaskDetail" in script
    assert "taskDetailRequest" in script
    assert "review_attempts" in script
    assert "token_usage_available" not in script  # UI states unavailable copy, not a token value


def test_run_decide_requires_confirmation_and_current_revision(
    client: TestClient, workspace: Path
):
    from devrelay.orchestration.models import RunState
    from devrelay.orchestration.store import OrchestrationStore
    from v03d_helpers import honest_run

    auth = _auth(client)
    store = OrchestrationStore(workspace / ".devrelay")
    run = honest_run(RunState.AWAITING_DECISION, workspace=str(workspace.resolve()))
    store.create(run)
    ready = honest_run(workspace=str(workspace.resolve()), run_id="DR-" + "c" * 32)
    store.create(ready)
    not_ready = client.post(
        f"/api/runs/{ready.run_id}/decide",
        json={"expected_updated_at": "x", "decision": "complete", "confirm": "apply"},
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert not_ready.status_code == 409
    ready_detail = client.get(f"/api/runs/{ready.run_id}", headers=auth).json()["data"]
    invalid_state = client.post(
        f"/api/runs/{ready.run_id}/decide",
        json={
            "expected_updated_at": ready_detail["updated_at"],
            "decision": "complete",
            "confirm": "apply",
        },
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert invalid_state.status_code == 409
    assert invalid_state.json()["error"]["code"] == "orchestration_invalid_transition"
    detail = client.get(f"/api/runs/{run.run_id}", headers=auth).json()["data"]
    body = {
        "expected_updated_at": detail["updated_at"],
        "decision": "complete",
        "confirm": "apply",
    }
    assert (
        client.post(f"/api/runs/{run.run_id}/decide", json=body, headers=auth).status_code
        == 403
    )
    stale = client.post(
        f"/api/runs/{run.run_id}/decide",
        json={**body, "expected_updated_at": "not-current"},
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "run_changed"
    applied = client.post(
        f"/api/runs/{run.run_id}/decide",
        json=body,
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert applied.status_code == 200, applied.text
    after = client.get(f"/api/runs/{run.run_id}", headers=auth).json()["data"]
    assert after["decision_history"][-1]["decision"] == "complete"
    invalid = client.post(
        f"/api/runs/{run.run_id}/decide",
        json={**body, "decision": "explode"},
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert invalid.status_code == 422
    missing_body_confirm = client.post(
        f"/api/runs/{run.run_id}/decide",
        json={"expected_updated_at": detail["updated_at"], "decision": "stop"},
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert missing_body_confirm.status_code == 422
    assert (
        client.post(
            "/api/runs/not-a-run/decide",
            json=body,
            headers={**auth, "X-DevRelay-Confirm": "apply"},
        ).status_code
        == 400
    )


def test_run_interrupt_is_role_scoped_and_confirmed(
    client: TestClient, workspace: Path, monkeypatch
):
    from devrelay.mcp.models import ok_envelope
    from devrelay.mcp.tools import McpToolSurface
    from devrelay.orchestration.store import OrchestrationStore
    from v03d_helpers import honest_run, with_in_flight

    seen = {}

    def fake_interrupt(self, session_id=None):
        seen["session_id"] = session_id
        return ok_envelope(
            "opencode_interrupt",
            {"session_id": session_id, "interrupt_verified": False},
        )

    monkeypatch.setattr(McpToolSurface, "opencode_interrupt", fake_interrupt)
    auth = _auth(client)
    store = OrchestrationStore(workspace / ".devrelay")
    not_in_flight = honest_run(workspace=str(workspace.resolve()), run_id="DR-" + "d" * 32)
    store.create(not_in_flight)
    blocked = client.post(
        f"/api/runs/{not_in_flight.run_id}/interrupt",
        json={"role": "implementer", "confirm": "apply"},
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert blocked.status_code == 409
    run = with_in_flight(honest_run(workspace=str(workspace.resolve())), "implementer")
    store.create(run)
    body = {"role": "implementer", "confirm": "apply"}
    assert (
        client.post(f"/api/runs/{run.run_id}/interrupt", json=body, headers=auth).status_code
        == 403
    )
    response = client.post(
        f"/api/runs/{run.run_id}/interrupt",
        json=body,
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"]["interrupt_verified"] is False
    assert seen["session_id"] == run.implementer_session_id
    invalid = client.post(
        f"/api/runs/{run.run_id}/interrupt",
        json={"role": "other", "confirm": "apply"},
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert invalid.status_code == 422
    extra = client.post(
        f"/api/runs/{run.run_id}/interrupt",
        json={"role": "implementer", "session_id": "other", "confirm": "apply"},
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert extra.status_code == 422
    assert (
        client.post(
            "/api/runs/not-a-run/interrupt",
            json=body,
            headers={**auth, "X-DevRelay-Confirm": "apply"},
        ).status_code
        == 400
    )


def test_manual_prompt_is_confirmed_and_session_scoped(
    client: TestClient, workspace: Path, monkeypatch
):
    from devrelay.mcp.models import ok_envelope
    from devrelay.mcp.tools import McpToolSurface
    from devrelay.orchestration.store import OrchestrationStore
    from v03d_helpers import honest_run

    seen = {}

    def fake_prompt(self, session_id=None, prompt=None, agent=None, model=None):
        seen.update(session_id=session_id, prompt=prompt, agent=agent, model=model)
        return ok_envelope(
            "opencode_send_prompt",
            {
                "session_id": session_id,
                "state": "COMPLETED",
                "call_ids": ["OC-0001"],
                "messages": [
                    {
                        "message_id": "msg_1",
                        "role": "assistant",
                        "created_at": "2026-10-22T00:00:00+00:00",
                        "parts": [{"kind": "text", "text": "done"}],
                    }
                ],
                "reply_pending": False,
                "submission_uncertain": False,
            },
        )

    monkeypatch.setattr(McpToolSurface, "opencode_send_prompt", fake_prompt)
    auth = _auth(client)
    store = OrchestrationStore(workspace / ".devrelay")
    run = honest_run(workspace=str(workspace.resolve()))
    store.create(run)
    body = {"role": "implementer", "prompt": "manual check", "confirm": "apply"}
    assert (
        client.post(f"/api/runs/{run.run_id}/prompt", json=body, headers=auth).status_code
        == 403
    )
    response = client.post(
        f"/api/runs/{run.run_id}/prompt",
        json=body,
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["completed"] is True
    assert data["messages"][0]["text"] == "done"
    assert seen["session_id"] == run.implementer_session_id
    assert seen["agent"] is None and seen["model"] is None
    too_long = client.post(
        f"/api/runs/{run.run_id}/prompt",
        json={"role": "implementer", "prompt": "x" * 16_001, "confirm": "apply"},
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert too_long.status_code == 422


def test_run_messages_are_role_scoped_and_bounded(
    client: TestClient, workspace: Path, monkeypatch
):
    from devrelay.mcp.models import ok_envelope
    from devrelay.mcp.tools import McpToolSurface
    from devrelay.orchestration.store import OrchestrationStore
    from v03d_helpers import honest_run

    seen = {}

    def fake_read(self, session_id=None, cursor=None):
        seen.update(session_id=session_id, cursor=cursor)
        messages = [
            {
                "message_id": f"msg_{index}",
                "role": "assistant",
                "parts": [{"text": "Authorization: Bearer secret-token " + "x" * 5_000}],
            }
            for index in range(60)
        ]
        return ok_envelope(
            "opencode_read_messages",
            {
                "session_id": session_id,
                "next_cursor": "next",
                "messages": messages,
            },
        )

    monkeypatch.setattr(McpToolSurface, "opencode_read_messages", fake_read)
    auth = _auth(client)
    store = OrchestrationStore(workspace / ".devrelay")
    run = honest_run(workspace=str(workspace.resolve()))
    store.create(run)
    response = client.get(
        f"/api/runs/{run.run_id}/messages?role=implementer&cursor=old",
        headers=auth,
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert len(data["messages"]) <= 50
    assert all(len(item["text"]) <= 4_000 for item in data["messages"])
    assert sum(len(item["text"]) for item in data["messages"]) <= 16_384
    assert "secret-token" not in response.text
    assert data["next_cursor"] == "next"
    assert "session_id" not in data
    assert seen["session_id"] == run.implementer_session_id
    assert seen["cursor"] == "old"
    assert (
        client.get(f"/api/runs/{run.run_id}/messages?role=other", headers=auth).status_code
        == 400
    )
    too_long = client.get(
        f"/api/runs/{run.run_id}/messages?role=implementer&cursor={'x' * 513}",
        headers=auth,
    )
    assert too_long.status_code == 400
    assert too_long.json()["error"]["code"] == "invalid_cursor"
    assert client.get(f"/api/runs/{run.run_id}/messages?role=implementer").status_code == 401


def test_manual_prompt_rejects_in_flight_terminal_and_blank(
    client: TestClient, workspace: Path
):
    from devrelay.orchestration.models import RunState
    from devrelay.orchestration.store import OrchestrationStore
    from v03d_helpers import honest_run, with_in_flight

    auth = _auth(client)
    store = OrchestrationStore(workspace / ".devrelay")
    in_flight = with_in_flight(
        honest_run(workspace=str(workspace.resolve())), "implementer"
    )
    store.create(in_flight)
    terminal = honest_run(
        RunState.COMPLETED,
        workspace=str(workspace.resolve()),
        run_id="DR-" + "e" * 32,
    )
    store.create(terminal)
    headers = {**auth, "X-DevRelay-Confirm": "apply"}
    for run in (in_flight, terminal):
        response = client.post(
            f"/api/runs/{run.run_id}/prompt",
            json={"role": "implementer", "prompt": "x", "confirm": "apply"},
            headers=headers,
        )
        assert response.status_code == 409
    blank = client.post(
        f"/api/runs/{in_flight.run_id}/prompt",
        json={"role": "implementer", "prompt": "   ", "confirm": "apply"},
        headers=headers,
    )
    assert blank.status_code == 422


def test_manual_prompt_pending_and_redaction(client: TestClient, workspace: Path, monkeypatch):
    from devrelay.mcp.models import error_envelope
    from devrelay.mcp.tools import McpToolSurface
    from devrelay.orchestration.store import OrchestrationStore
    from v03d_helpers import honest_run

    def fake_prompt(self, session_id=None, prompt=None, agent=None, model=None):
        return error_envelope(
            "opencode_send_prompt",
            "submission_not_confirmed",
            "pending",
            {
                "session_id": session_id,
                "reply_pending": True,
                "submission_uncertain": True,
                "messages": [
                    {
                        "message_id": "m1",
                        "role": "assistant",
                        "parts": [{"text": "Authorization: Bearer secret-token"}],
                    }
                ],
            },
        )

    monkeypatch.setattr(McpToolSurface, "opencode_send_prompt", fake_prompt)
    auth = _auth(client)
    store = OrchestrationStore(workspace / ".devrelay")
    run = honest_run(workspace=str(workspace.resolve()))
    store.create(run)
    headers = {**auth, "X-DevRelay-Confirm": "apply"}
    first = client.post(
        f"/api/runs/{run.run_id}/prompt",
        json={"role": "implementer", "prompt": "manual-check-unique", "confirm": "apply"},
        headers=headers,
    )
    assert first.status_code == 200
    data = first.json()["data"]
    assert data["completed"] is False
    assert data["reply_pending"] is True
    assert "secret-token" not in first.text
    second = client.post(
        f"/api/runs/{run.run_id}/prompt",
        json={"role": "implementer", "prompt": "y", "confirm": "apply"},
        headers=headers,
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "manual_prompt_pending"

    marker = workspace / ".devrelay" / "web" / "manual_prompts.json"
    assert marker.is_file()
    marker_text = marker.read_text(encoding="utf-8")
    assert "manual-check-unique" not in marker_text
    assert "secret-token" not in marker_text

    from devrelay.web.errors import WebApiError
    from devrelay.web.service import WebReadService

    api = client.app.app.state.api
    fresh = WebReadService(
        workspace_root=api.service.workspace_root,
        wiring=api.service.wiring,
        devrelay_dir=api.service.devrelay_dir,
    )
    with pytest.raises(WebApiError) as exc:
        fresh.prompt_run(run.run_id, "implementer", "after restart")
    assert exc.value.code == "manual_prompt_pending"

    recovered = client.post(
        f"/api/runs/{run.run_id}/prompt/recover",
        json={"confirm": "apply"},
        headers=headers,
    )
    assert recovered.status_code == 200, recovered.text
    assert recovered.json()["data"]["cleared"] is True
    assert run.run_id not in marker.read_text(encoding="utf-8")
    after = client.post(
        f"/api/runs/{run.run_id}/prompt",
        json={"role": "implementer", "prompt": "after recovery", "confirm": "apply"},
        headers=headers,
    )
    assert after.status_code == 200


def test_manual_prompt_marker_corruption_fails_closed(
    client: TestClient, workspace: Path, monkeypatch
):
    from devrelay.mcp.tools import McpToolSurface
    from devrelay.orchestration.store import OrchestrationStore
    from v03d_helpers import honest_run

    marker = workspace / ".devrelay" / "web" / "manual_prompts.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("not-json", encoding="utf-8")
    called = {"value": False}

    def fake_prompt(self, session_id=None, prompt=None, agent=None, model=None):
        called["value"] = True
        raise AssertionError("provider must not be called when the marker is corrupt")

    monkeypatch.setattr(McpToolSurface, "opencode_send_prompt", fake_prompt)
    auth = _auth(client)
    store = OrchestrationStore(workspace / ".devrelay")
    run = honest_run(workspace=str(workspace.resolve()))
    store.create(run)
    response = client.post(
        f"/api/runs/{run.run_id}/prompt",
        json={"role": "implementer", "prompt": "x", "confirm": "apply"},
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "manual_prompt_marker_unavailable"
    assert called["value"] is False


def test_advisory_hold_is_durable_and_blocks_manual_prompt(
    client: TestClient, workspace: Path, monkeypatch
):
    from devrelay.mcp.models import ok_envelope
    from devrelay.mcp.tools import McpToolSurface
    from devrelay.orchestration.store import OrchestrationStore
    from v03d_helpers import honest_run
    from devrelay.web.service import WebReadService

    called = {"value": False}

    def fake_prompt(self, session_id=None, prompt=None, agent=None, model=None):
        called["value"] = True
        return ok_envelope(
            "opencode_send_prompt",
            {
                "session_id": session_id,
                "state": "COMPLETED",
                "messages": [],
                "reply_pending": False,
                "submission_uncertain": False,
            },
        )

    monkeypatch.setattr(McpToolSurface, "opencode_send_prompt", fake_prompt)
    auth = _auth(client)
    store = OrchestrationStore(workspace / ".devrelay")
    run = honest_run(workspace=str(workspace.resolve()))
    store.create(run)
    detail = client.get(f"/api/runs/{run.run_id}", headers=auth).json()["data"]
    headers = {**auth, "X-DevRelay-Confirm": "apply"}
    body = {
        "expected_updated_at": detail["updated_at"],
        "reason": "operator review",
        "confirm": "apply",
    }
    assert client.post(f"/api/runs/{run.run_id}/hold", json=body, headers=auth).status_code == 403
    held = client.post(f"/api/runs/{run.run_id}/hold", json=body, headers=headers)
    assert held.status_code == 200, held.text
    assert held.json()["data"]["held"] is True
    assert held.json()["data"]["hold"]["reason"] == "operator review"
    detail = client.get(f"/api/runs/{run.run_id}", headers=auth).json()["data"]
    assert detail["hold"]["reason"] == "operator review"
    assert detail["state"] == run.state.value

    api = client.app.app.state.api
    fresh = WebReadService(
        workspace_root=api.service.workspace_root,
        wiring=api.service.wiring,
        devrelay_dir=api.service.devrelay_dir,
    )
    assert fresh.run(run.run_id)["hold"]["reason"] == "operator review"

    blocked = client.post(
        f"/api/runs/{run.run_id}/prompt",
        json={"role": "implementer", "prompt": "blocked", "confirm": "apply"},
        headers=headers,
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "run_held"
    assert called["value"] is False

    released = client.post(
        f"/api/runs/{run.run_id}/hold/release",
        json={"confirm": "apply"},
        headers=headers,
    )
    assert released.status_code == 200
    assert released.json()["data"]["cleared"] is True
    allowed = client.post(
        f"/api/runs/{run.run_id}/prompt",
        json={"role": "implementer", "prompt": "allowed", "confirm": "apply"},
        headers=headers,
    )
    assert allowed.status_code == 200


def test_advisory_hold_store_corruption_fails_closed(
    client: TestClient, workspace: Path, monkeypatch
):
    from devrelay.mcp.tools import McpToolSurface
    from devrelay.orchestration.store import OrchestrationStore
    from v03d_helpers import honest_run

    hold_path = workspace / ".devrelay" / "web" / "run_holds.json"
    hold_path.parent.mkdir(parents=True, exist_ok=True)
    hold_path.write_text("not-json", encoding="utf-8")
    called = {"value": False}

    def fake_prompt(self, session_id=None, prompt=None, agent=None, model=None):
        called["value"] = True
        raise AssertionError("provider must not be called")

    monkeypatch.setattr(McpToolSurface, "opencode_send_prompt", fake_prompt)
    auth = _auth(client)
    store = OrchestrationStore(workspace / ".devrelay")
    run = honest_run(workspace=str(workspace.resolve()))
    store.create(run)
    response = client.post(
        f"/api/runs/{run.run_id}/prompt",
        json={"role": "implementer", "prompt": "x", "confirm": "apply"},
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "run_hold_unavailable"
    assert called["value"] is False


def test_c2c_ui_has_manual_prompt_and_polling(client: TestClient):
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    for marker in (
        "run-prompt",
        "run-prompt-recover",
        "messages-view",
        "Live normalized messages",
    ):
        assert marker in html
    assert "sendManualPrompt" in script
    assert "recoverPromptMarker" in script
    assert "holdRun" in script
    assert "releaseHold" in script
    assert 'id="run-hold"' in html
    assert 'id="run-hold-release"' in html
    assert "loadMessages" in script
    assert "/api/runs/" in script
    assert 'id="run-pause"' not in html
    assert "setInterval" in script
    assert "loadMessages(false)" in script


def test_c2b_ui_has_only_bounded_controls(client: TestClient):
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    assert 'id="run-decide"' in html
    assert 'id="run-interrupt"' in html
    assert "decideRun" in script
    assert "interruptRun" in script
    assert "X-DevRelay-Confirm" in script
    assert 'detail.state !== "AWAITING_DECISION"' in script
    assert "detail.in_flight" in script
    assert 'id="run-pause"' not in html
    assert 'id="run-prompt-send"' in html
    for endpoint in ("/pause", "/phase", "/stream"):
        assert endpoint not in script


def test_project_activation_switches_active_workspace(
    client: TestClient, workspace: Path, tmp_path: Path
):
    from devrelay.config import install_default_config
    from devrelay.web.registry import ProjectRegistry

    other = tmp_path / "other-workspace"
    (other / ".devrelay").mkdir(parents=True)
    install_default_config(other / ".devrelay" / "config.yaml")
    registry = ProjectRegistry(workspace / ".devrelay")
    project = registry.add(other)
    auth = _auth(client)
    body = {"confirm": "apply"}
    assert (
        client.post(
            f"/api/projects/{project.project_id}/activate",
            json=body,
            headers=auth,
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/projects/{project.project_id}/activate",
            json={},
            headers={**auth, "X-DevRelay-Confirm": "apply"},
        ).status_code
        == 422
    )
    response = client.post(
        f"/api/projects/{project.project_id}/activate",
        json=body,
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"]["active"] is True
    projects = client.get("/api/projects", headers=auth).json()["data"]["projects"]
    assert [item["project_id"] for item in projects if item["active"]] == [
        project.project_id
    ]
    status = client.get("/api/status", headers=auth).json()["data"]
    assert status["workspace"] == str(other.resolve())
    health = client.get("/api/health", headers=auth).json()["data"]
    assert health["project_id"] == project.project_id
    assert client.get("/api/runs", headers=auth).json()["data"]["total"] == 0
    assert client.get("/api/tasks", headers=auth).json()["data"]["total"] == 0
    assert client.get("/api/sessions", headers=auth).json()["data"]["total"] == 0
    assert (
        client.post(
            "/api/projects/not-a-project/activate",
            json=body,
            headers={**auth, "X-DevRelay-Confirm": "apply"},
        ).status_code
        == 404
    )


def test_project_activation_failure_keeps_old_service(
    client: TestClient, workspace: Path, tmp_path: Path
):
    from devrelay.config import install_default_config
    from devrelay.web.registry import ProjectRegistry
    import shutil

    other = tmp_path / "broken-workspace"
    (other / ".devrelay").mkdir(parents=True)
    install_default_config(other / ".devrelay" / "config.yaml")
    registry = ProjectRegistry(workspace / ".devrelay")
    project = registry.add(other)
    shutil.rmtree(other)
    auth = _auth(client)
    response = client.post(
        f"/api/projects/{project.project_id}/activate",
        json={"confirm": "apply"},
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert response.status_code == 503
    status = client.get("/api/status", headers=auth).json()["data"]
    assert status["workspace"] == str(workspace.resolve())


def test_concurrent_project_activation_does_not_deadlock(
    client: TestClient, workspace: Path, tmp_path: Path
):
    from concurrent.futures import ThreadPoolExecutor
    from devrelay.config import install_default_config
    from devrelay.web.registry import ProjectRegistry

    registry = ProjectRegistry(workspace / ".devrelay")
    projects = []
    for index in range(2):
        other = tmp_path / f"concurrent-{index}"
        (other / ".devrelay").mkdir(parents=True)
        install_default_config(other / ".devrelay" / "config.yaml")
        projects.append(registry.add(other))
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-DevRelay-Confirm": "apply",
    }

    def activate(project_id: str) -> int:
        with TestClient(client.app, base_url=BASE_URL) as worker:
            return worker.post(
                f"/api/projects/{project_id}/activate",
                json={"confirm": "apply"},
                headers=headers,
            ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(activate, [item.project_id for item in projects]))
    assert results == [200, 200]


def test_sessions_inventory_is_run_recorded(client: TestClient, workspace: Path):
    from devrelay.orchestration.store import OrchestrationStore
    from v03d_helpers import honest_run

    auth = _auth(client)
    store = OrchestrationStore(workspace / ".devrelay")
    run = honest_run(workspace=str(workspace.resolve()))
    store.create(run)
    from devrelay.web.session_leases import SessionLeaseStore

    SessionLeaseStore(workspace / ".devrelay").acquire(
        run.implementer_session_id,
        workspace=str(workspace.resolve()),
        run_id=run.run_id,
        role="implementer",
    )
    response = client.get("/api/sessions", headers=auth)
    assert response.status_code == 200
    data = response.json()["data"]
    ids = {item["session_id"] for item in data["sessions"]}
    assert run.implementer_session_id in ids
    assert run.reviewer_session_id in ids
    leased = next(
        item for item in data["sessions"] if item["session_id"] == run.implementer_session_id
    )
    assert leased["lease"]["run_id"] == run.run_id
    assert leased["lease"]["state"] == "active"
    assert data["lease_error"] == ""
    for item in data["sessions"]:
        assert "parts" not in item
        assert "prompt" not in item
    SessionLeaseStore(workspace / ".devrelay").mark_uncertain(
        run.implementer_session_id
    )
    headers = {**auth, "X-DevRelay-Confirm": "apply"}
    assert (
        client.post(
            f"/api/sessions/{run.implementer_session_id}/lease/recover",
            json={"confirm": "apply", "expected_state": "uncertain"},
            headers=auth,
        ).status_code
        == 403
    )
    recovered = client.post(
        f"/api/sessions/{run.implementer_session_id}/lease/recover",
        json={"confirm": "apply", "expected_state": "uncertain"},
        headers=headers,
    )
    assert recovered.status_code == 200, recovered.text
    assert recovered.json()["data"]["previous_state"] == "uncertain"
    assert recovered.json()["data"]["state"] == "released"
    assert client.get("/api/sessions").status_code == 401
    assert (
        client.get(f"/api/sessions/{run.implementer_session_id}", headers=auth).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/runs/{run.run_id}/session/switch",
            json={"role": "implementer", "target_session_id": "other", "confirm": "apply"},
            headers={**auth, "X-DevRelay-Confirm": "apply"},
        ).status_code
        == 404
    )


def test_d_ui_has_project_and_session_controls(client: TestClient):
    html = client.get("/").text
    script = client.get("/assets/app.js").text
    for marker in ("project-select", "project-activate", "sessions-view"):
        assert marker in html
    assert "activateProject" in script
    assert "/api/sessions" in script
    assert "workspaceEpoch" in script
    assert "switchingProject" in script


def test_ui_does_not_expose_token_in_html(client: TestClient):
    response = client.get("/")
    assert TOKEN not in response.text
    assert "DEVRELAY_WEB_TOKEN" not in response.text
