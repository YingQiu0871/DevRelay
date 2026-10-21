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


def test_ui_does_not_expose_token_in_html(client: TestClient):
    response = client.get("/")
    assert TOKEN not in response.text
    assert "DEVRELAY_WEB_TOKEN" not in response.text
