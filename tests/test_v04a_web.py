"""v0.4-A1 local HTTP control API: auth, registry and read-only routes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient
from typer.testing import CliRunner

from devrelay.cli import app as cli_app
from devrelay.config import install_default_config
from devrelay.web.app import create_app
from devrelay.web.auth import AuthManager, SESSION_HEADER
from devrelay.web.errors import WebApiError
from devrelay.web.registry import ProjectRegistry

TOKEN = "t" * 32
BASE_URL = "http://127.0.0.1:8765"


class _Clock:
    def __init__(self) -> None:
        self.now = 1_000.0

    def monotonic(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    (root / ".devrelay").mkdir(parents=True)
    install_default_config(root / ".devrelay" / "config.yaml")
    return root


@pytest.fixture
def app(workspace: Path):
    return create_app(str(workspace), port=8765, token=TOKEN)


@pytest.fixture
def client(app):
    with TestClient(app, base_url=BASE_URL, raise_server_exceptions=False) as test_client:
        yield test_client


def _session_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/session", json={"token": TOKEN})
    assert response.status_code == 200, response.text
    return {SESSION_HEADER: response.json()["data"]["session_token"]}


def test_healthz_is_unauthenticated_and_leaks_no_workspace(client: TestClient, workspace: Path):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert str(workspace) not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_api_requires_authentication(client: TestClient):
    response = client.get("/api/status")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
    assert response.headers["www-authenticate"] == "Bearer"


def test_wrong_bearer_is_rejected(client: TestClient):
    response = client.get("/api/status", headers={"Authorization": "Bearer " + "x" * 32})
    assert response.status_code == 401


def test_non_ascii_token_is_a_clean_401(client: TestClient):
    response = client.post("/api/session", json={"token": "é" * 32})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_cors_preflight_is_not_offered(client: TestClient):
    response = client.options(
        "/api/status",
        headers={
            "Origin": BASE_URL,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 405
    assert "access-control-allow-origin" not in response.headers


def test_unknown_route_and_method_return_json_envelopes(client: TestClient):
    not_found = client.get("/api/nope", headers={"Authorization": f"Bearer {TOKEN}"})
    assert not_found.status_code == 404
    assert not_found.json()["error"]["code"] == "not_found"
    bad_method = client.put("/api/status", headers={"Authorization": f"Bearer {TOKEN}"})
    assert bad_method.status_code == 405
    assert bad_method.json()["error"]["code"] == "method_not_allowed"


def test_bearer_authenticates(client: TestClient):
    response = client.post(
        "/api/config/validate",
        json={"config": {}},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["valid"] is True


def test_session_exchange_returns_header_token_without_cookie(client: TestClient):
    response = client.post("/api/session", json={"token": TOKEN})
    assert response.status_code == 200
    assert "set-cookie" not in response.headers
    data = response.json()["data"]
    assert data["session_token"]
    assert data["transport"].lower() == SESSION_HEADER
    assert data["expires_in"] == 28800


def test_header_session_authenticates_and_delete_invalidates(client: TestClient):
    headers = _session_headers(client)
    assert client.get("/api/status", headers=headers).status_code == 200
    assert (
        client.get(
            "/api/status",
            headers={**headers, "Authorization": "Bearer not-a-valid-token"},
        ).status_code
        == 200
    )
    deleted = client.delete("/api/session", headers=headers)
    assert deleted.status_code == 200
    assert "set-cookie" not in deleted.headers
    assert client.get("/api/status", headers=headers).status_code == 401


def test_session_header_is_required(client: TestClient):
    assert client.get("/api/status").status_code == 401
    assert (
        client.get("/api/status", headers={SESSION_HEADER: "x" * 43}).status_code
        == 401
    )


def test_bad_host_is_rejected(client: TestClient):
    response = client.get("/healthz", headers={"Host": "evil.example:8765"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_host"
    malformed = client.get("/healthz", headers={"Host": "[::1"})
    assert malformed.status_code == 400
    assert malformed.json()["error"]["code"] == "invalid_host"


def test_bad_origin_is_rejected(client: TestClient):
    response = client.post(
        "/api/session",
        json={"token": TOKEN},
        headers={"Origin": "http://evil.example:8765"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "origin_rejected"
    malformed = client.post(
        "/api/session",
        json={"token": TOKEN},
        headers={"Origin": "http://[::1"},
    )
    assert malformed.status_code == 403
    assert malformed.json()["error"]["code"] == "origin_rejected"


def test_content_type_json_validation_and_unknown_fields(client: TestClient):
    auth = _session_headers(client)
    wrong_type = client.post(
        "/api/config/validate",
        content=b"{}",
        headers={**auth, "Content-Type": "text/plain"},
    )
    assert wrong_type.status_code == 415
    invalid_json = client.post(
        "/api/config/validate",
        content=b"{not json",
        headers={**auth, "Content-Type": "application/json"},
    )
    assert invalid_json.status_code == 400
    unknown = client.post(
        "/api/config/validate",
        json={"config": {}, "extra": True},
        headers=auth,
    )
    assert unknown.status_code == 422
    assert unknown.json()["error"]["code"] == "invalid_request"


def test_body_limit_is_enforced(client: TestClient):
    payload = b'{"token":"' + TOKEN.encode() + b'","pad":"' + b"x" * (70 * 1024) + b'"}'
    response = client.post("/api/session", content=payload, headers={"Content-Type": "application/json"})
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "body_too_large"


def test_projects_include_the_active_workspace(client: TestClient, workspace: Path):
    auth = _session_headers(client)
    response = client.get("/api/projects", headers=auth)
    assert response.status_code == 200
    projects = response.json()["data"]["projects"]
    assert len(projects) == 1
    assert projects[0]["active"] is True
    assert projects[0]["root"] == str(workspace.resolve())
    assert projects[0]["project_id"].startswith("prj_")


def test_read_routes_are_bounded_and_secret_free(client: TestClient, workspace: Path):
    auth = _session_headers(client)
    assert client.get("/api/status", headers=auth).status_code == 200
    roles = client.get("/api/roles", headers=auth)
    assert roles.status_code == 200
    assert roles.json()["data"]["read_only"] is True
    config = client.get("/api/config", headers=auth)
    assert config.status_code == 200
    assert TOKEN not in config.text
    assert str(workspace) not in config.text
    assert "token_source" in config.text
    assert "workspace_override" in config.json()["data"]["opencode"]
    assert "workspace" not in config.json()["data"]["opencode"]
    assert "launcher_args" not in config.json()["data"]["codex"]
    assert "args" not in config.json()["data"]["codex"]
    assert config.json()["data"]["codex"]["executable"] == "codex"
    assert config.json()["data"]["write_supported"] is True
    assert config.json()["data"]["read_only"] is False
    assert len(config.json()["data"]["config_sha256"]) == 64
    assert client.get("/api/runs", headers=auth).json()["data"]["runs"] == []


def test_run_id_grammar_and_missing_run(client: TestClient):
    auth = _session_headers(client)
    invalid = client.get("/api/runs/DR-" + "z" * 32, headers=auth)
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "invalid_run_id"
    missing = client.get("/api/runs/DR-" + "0" * 32, headers=auth)
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "orchestration_run_not_found"


def test_config_validate_is_read_only(client: TestClient, workspace: Path):
    auth = _session_headers(client)
    before = (workspace / ".devrelay" / "config.yaml").read_text(encoding="utf-8")
    valid = client.post("/api/config/validate", json={"config": {}}, headers=auth)
    assert valid.status_code == 200 and valid.json()["data"]["valid"] is True
    invalid = client.post(
        "/api/config/validate",
        json={"config": {"unknown_key": True}},
        headers=auth,
    )
    assert invalid.status_code == 200
    assert invalid.json()["data"]["valid"] is False
    assert invalid.json()["data"]["errors"][0]["loc"] == ["unknown_key"]
    after = (workspace / ".devrelay" / "config.yaml").read_text(encoding="utf-8")
    assert before == after


def _config_digest(client: TestClient, auth: dict[str, str]) -> str:
    response = client.get("/api/config", headers=auth)
    assert response.status_code == 200, response.text
    return response.json()["data"]["config_sha256"]


def test_config_write_requires_confirmation_and_current_digest(client: TestClient):
    auth = _session_headers(client)
    digest = _config_digest(client, auth)
    body = {"expected_sha256": digest, "config": {"pipeline": {"max_fix_iterations": 2}}, "confirm": "apply"}
    no_header = client.put("/api/config", json=body, headers=auth)
    assert no_header.status_code == 403
    assert no_header.json()["error"]["code"] == "confirmation_required"
    stale = client.put(
        "/api/config",
        json={**body, "expected_sha256": "0" * 64},
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "config_changed"


def test_config_write_is_atomic_with_backup_and_new_digest(client: TestClient, workspace: Path):
    auth = _session_headers(client)
    digest = _config_digest(client, auth)
    config_path = workspace / ".devrelay" / "config.yaml"
    old_text = config_path.read_text(encoding="utf-8")
    new_config = {"pipeline": {"max_fix_iterations": 2}}
    response = client.put(
        "/api/config",
        json={"expected_sha256": digest, "config": new_config, "confirm": "apply"},
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["applied"] is True
    assert data["comments_preserved"] is False
    assert data["backup_created"] is True
    assert data["backup_name"].startswith("config.yaml.bak-")
    assert str(workspace) not in response.text
    new_text = config_path.read_text(encoding="utf-8")
    assert "max_fix_iterations: 2" in new_text
    assert "opencode:" in new_text
    assert "profiles:" in new_text
    assert data["new_sha256"] == hashlib.sha256(new_text.encode("utf-8")).hexdigest()
    assert data["restart_required"] is True
    backups = list((workspace / ".devrelay").glob("config.yaml.bak-*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == old_text


def test_config_write_rejects_secret_keys_and_codex_argv(client: TestClient, workspace: Path):
    auth = _session_headers(client)
    digest = _config_digest(client, auth)
    before = (workspace / ".devrelay" / "config.yaml").read_bytes()
    for config in (
        {"opencode": {"token": "secret"}},
        {"codex": {"args": ["exec", "--sandbox", "read-only"]}},
        {"roles": {"reviewer": {"agent": "Bearer abcdefghijklmnop"}}},
    ):
        response = client.put(
            "/api/config",
            json={"expected_sha256": digest, "config": config, "confirm": "apply"},
            headers={**auth, "X-DevRelay-Confirm": "apply"},
        )
        assert response.status_code == 422, response.text
    assert (workspace / ".devrelay" / "config.yaml").read_bytes() == before


def test_config_write_empty_patch_is_a_noop(client: TestClient, workspace: Path):
    auth = _session_headers(client)
    digest = _config_digest(client, auth)
    before = (workspace / ".devrelay" / "config.yaml").read_bytes()
    response = client.put(
        "/api/config",
        json={"expected_sha256": digest, "config": {}, "confirm": "apply"},
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["applied"] is False
    assert data["no_change"] is True
    assert data["backup_created"] is False
    assert (workspace / ".devrelay" / "config.yaml").read_bytes() == before


def test_config_write_rejects_symlinked_config(client: TestClient, workspace: Path):
    auth = _session_headers(client)
    digest = _config_digest(client, auth)
    config_path = workspace / ".devrelay" / "config.yaml"
    target = workspace / ".devrelay" / "config-real.yaml"
    config_path.rename(target)
    try:
        config_path.symlink_to(target)
    except OSError as exc:  # pragma: no cover - Windows privilege-dependent
        pytest.skip(f"symlink unavailable: {exc}")
    response = client.put(
        "/api/config",
        json={"expected_sha256": digest, "config": {}, "confirm": "apply"},
        headers={**auth, "X-DevRelay-Confirm": "apply"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "config_symlink_rejected"


def test_config_write_requires_auth(client: TestClient):
    response = client.put(
        "/api/config",
        json={"expected_sha256": "0" * 64, "config": {}, "confirm": "apply"},
        headers={"X-DevRelay-Confirm": "apply"},
    )
    assert response.status_code == 401


def test_config_validate_rejects_secret_values(client: TestClient):
    auth = _session_headers(client)
    for value in (
        "Bearer abcdefghijklmnop",
        "sk-ant-api03-abcdefghijklmnop",
        "Authorization: Basic YWxhZGRpbjpvcGVuc2VzYW1l",
    ):
        response = client.post(
            "/api/config/validate",
            json={"config": {"roles": {"reviewer": {"agent": value}}}},
            headers=auth,
        )
        assert response.status_code == 200
        assert response.json()["data"]["valid"] is False
        assert response.json()["data"]["errors"][0]["type"] == "secret_value_rejected"


def test_config_write_rejects_wiring_and_execution_fields(client: TestClient):
    auth = _session_headers(client)
    digest = _config_digest(client, auth)
    for config in (
        {"codex": {"executable": "C:\\tmp\\evil.exe"}},
        {"opencode": {"base_url": "https://remote.example:4096"}},
        {"opencode": {"workspace": "C:\\outside"}},
        {"profiles": ["untrusted"]},
        {"tests": {"targeted": ["cmd.exe /c whoami"]}},
    ):
        response = client.put(
            "/api/config",
            json={"expected_sha256": digest, "config": config, "confirm": "apply"},
            headers={**auth, "X-DevRelay-Confirm": "apply"},
        )
        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "config_field_not_editable"


def test_registry_accepts_only_initialized_absolute_workspaces(tmp_path: Path):
    registry = ProjectRegistry(tmp_path / "registry-workspace" / ".devrelay")
    registry.devrelay_dir.mkdir(parents=True)
    with pytest.raises(WebApiError) as relative_error:
        registry.add("relative/path")
    assert relative_error.value.code == "invalid_project_path"

    plain = tmp_path / "plain"
    plain.mkdir()
    with pytest.raises(WebApiError) as plain_error:
        registry.add(plain)
    assert plain_error.value.code == "invalid_project_path"

    initialized = tmp_path / "initialized"
    (initialized / ".devrelay").mkdir(parents=True)
    project = registry.add(initialized)
    assert project.project_id.startswith("prj_")
    assert registry.add(initialized).project_id == project.project_id
    assert registry.list()[0].root == str(initialized.resolve())
    registry.remove(project.project_id)
    assert registry.list() == []


def test_auth_session_expiry_is_deterministic():
    clock = _Clock()
    auth = AuthManager(TOKEN, port=8765, monotonic=clock.monotonic)
    session = auth.create_session()
    assert auth.resolve_session(session.session_id) is not None
    clock.advance(31 * 60)
    assert auth.resolve_session(session.session_id) is None

    clock2 = _Clock()
    auth2 = AuthManager(TOKEN, port=8765, session_ttl=10, monotonic=clock2.monotonic)
    session2 = auth2.create_session()
    clock2.advance(11)
    assert auth2.resolve_session(session2.session_id) is None


def test_cli_project_registry(tmp_path: Path, workspace: Path, monkeypatch):
    monkeypatch.chdir(workspace)
    runner = CliRunner()
    added = runner.invoke(cli_app, ["web", "project", "add", str(workspace)])
    assert added.exit_code == 0, added.output
    project = json.loads(added.output)
    assert project["project_id"].startswith("prj_")
    listed = runner.invoke(cli_app, ["web", "project", "list"])
    assert listed.exit_code == 0, listed.output
    assert project["project_id"] in listed.output
    removed = runner.invoke(cli_app, ["web", "project", "remove", project["project_id"]])
    assert removed.exit_code == 0, removed.output
    assert project["project_id"] not in runner.invoke(cli_app, ["web", "project", "list"]).output


def test_cli_refuses_non_loopback_bind(workspace: Path, monkeypatch):
    monkeypatch.chdir(workspace)
    result = CliRunner().invoke(cli_app, ["web", "serve", "--host", "0.0.0.0"])
    assert result.exit_code == 1
    assert "127.0.0.1" in result.output


def test_cli_web_help_is_registered():
    result = CliRunner().invoke(cli_app, ["web", "--help"])
    assert result.exit_code == 0
    assert "serve" in result.output
    assert "project" in result.output


def test_create_app_rejects_missing_workspace(tmp_path: Path):
    with pytest.raises(WebApiError) as exc:
        create_app(str(tmp_path / "missing"), port=8765, token=TOKEN)
    assert exc.value.code == "workspace_invalid"


def test_invalid_startup_token_does_not_write_the_registry(workspace: Path):
    registry_path = workspace / ".devrelay" / "web" / "projects.json"
    with pytest.raises(WebApiError) as exc:
        create_app(str(workspace), port=8765, token="short")
    assert exc.value.code == "invalid_token"
    assert not registry_path.exists()
