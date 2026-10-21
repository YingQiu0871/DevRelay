"""v0.3-C role configuration: schema, validation, policy separation, compat.

Offline only.  These tests pin the narrow ``roles:`` wiring section and, above
all, the backward-compatibility rule: an existing v0.3-B workspace without a
``roles:`` section keeps working, and only role-aware tools report the missing
route.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from devrelay.config import (
    PolicyDocument,
    WiringConfig,
    WorkspaceFile,
    install_default_config,
    load_policy_snapshot,
    load_wiring_config,
    load_workspace_file,
    workspace_policy_overrides,
)
from devrelay.errors import ConfigError, RoleInvalidRouteError, RoleUnconfiguredError
from devrelay.roles.models import RolesConfig

from v03c_helpers import (
    AGENT_ROLES,
    DISTINCT_ROLES,
    build_roles_server,
    call,
    send_role,
    write_roles,
)


def wiring_for(tmp_path: Path, roles: object) -> WiringConfig:
    ws = tmp_path / "ws"
    (ws / ".devrelay").mkdir(parents=True, exist_ok=True)
    data: dict[str, object] = {"opencode": {"base_url": "http://127.0.0.1:4096"}}
    if roles is not Ellipsis:
        data["roles"] = roles
    (ws / ".devrelay" / "config.yaml").write_text(
        yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
    )
    return load_wiring_config(ws)


# ---------------------------------------------------------------------------
# valid configuration
# ---------------------------------------------------------------------------
def test_both_roles_load_exactly(tmp_path):
    wiring = wiring_for(tmp_path, AGENT_ROLES)
    assert wiring.roles.implementer.model == "provider-a/model-a"
    assert wiring.roles.implementer.agent == "build"
    assert wiring.roles.reviewer.model == "provider-b/model-b"
    assert wiring.roles.reviewer.agent == "review"


def test_role_routes_are_wiring_never_policy(tmp_path):
    wiring = wiring_for(tmp_path, DISTINCT_ROLES)
    assert "roles" in WiringConfig.model_fields
    assert "roles" not in PolicyDocument.model_fields
    assert set(WiringConfig.model_fields) & set(PolicyDocument.model_fields) == set()

    ws = tmp_path / "ws"
    (ws / ".devrelay" / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "opencode": {"base_url": "http://127.0.0.1:4096"},
                "roles": DISTINCT_ROLES,
                "tests": {"targeted": ["pytest -q"]},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    overrides = workspace_policy_overrides(ws)
    assert "roles" not in overrides and "opencode" not in overrides
    assert overrides["tests"] == {"targeted": ["pytest -q"]}
    # ... and the live wiring is still validated and readable
    assert load_wiring_config(ws).roles.reviewer.model == "provider-b/model-b"


def test_legacy_full_config_snapshot_tolerates_the_roles_section(tmp_path):
    """A full-config dump that contains wiring must stay loadable (v0.2-A tolerance)."""
    dump = yaml.safe_dump(
        {
            "tests": {"targeted": ["pytest -q"]},
            "codex": {"executable": "codex"},
            "opencode": {"base_url": "http://127.0.0.1:4096"},
            "roles": DISTINCT_ROLES,
            "profiles": ["python"],
        },
        sort_keys=False,
    ).encode("utf-8")
    document, dropped = load_policy_snapshot(dump, strict=False)
    assert "roles" in dropped and "opencode" in dropped and "codex" in dropped
    assert "roles" not in document.model_dump(mode="json")


def test_default_template_documents_roles_and_installs_unconfigured(tmp_path):
    destination = tmp_path / ".devrelay" / "config.yaml"
    install_default_config(destination)
    text = destination.read_text(encoding="utf-8")
    assert "roles:" in text and "implementer:" in text and "reviewer:" in text
    workspace = load_workspace_file(destination)
    assert workspace.roles.implementer.model == ""
    assert workspace.roles.reviewer.agent == ""
    # An installed-but-unconfigured workspace is valid v0.3-B/C configuration.
    assert load_wiring_config(tmp_path).roles.reviewer.model == ""


# ---------------------------------------------------------------------------
# absent / partial configuration (backward compatibility)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("roles", [Ellipsis, None, {}], ids=["absent", "null", "empty"])
def test_missing_roles_section_is_valid_and_unconfigured(tmp_path, roles):
    wiring = wiring_for(tmp_path, roles)
    assert wiring.roles.implementer.model == ""
    assert wiring.roles.reviewer.model == ""


def test_only_one_role_configured_leaves_the_other_unconfigured(tmp_path):
    wiring = wiring_for(tmp_path, {"implementer": {"model": "provider-a/model-a"}})
    assert wiring.roles.implementer.model == "provider-a/model-a"
    assert wiring.roles.reviewer.model == ""


def test_blank_model_is_unconfigured_not_invalid(tmp_path):
    wiring = wiring_for(tmp_path, {"implementer": {"model": "   "}})
    assert wiring.roles.implementer.model == "   "


def test_malformed_agent_type_is_rejected_at_load(tmp_path):
    with pytest.raises(ConfigError):
        wiring_for(tmp_path, {"reviewer": {"model": "provider-b/model-b", "agent": 5}})


@pytest.mark.parametrize(
    "roles",
    [
        {"planner": {"model": "provider-a/model-a"}},
        {"implementer": {"model": "provider-a/model-a", "prompt": "you are the implementer"}},
        {"implementer": {"model": "provider-a/model-a", "retries": 3}},
        {"reviewer": {"models": ["provider-b/model-b"]}},
        {"reviewer": {"model": "provider-b/model-b", "base_url": "http://elsewhere"}},
    ],
    ids=["unsupported-role", "prompt-template", "retry-policy", "candidate-list", "endpoint"],
)
def test_unsupported_role_configuration_is_rejected(tmp_path, roles):
    """No role-level prompts, retries, candidate lists or endpoint overrides."""
    with pytest.raises(ConfigError):
        wiring_for(tmp_path, roles)


# ---------------------------------------------------------------------------
# absence must not break the accepted v0.3-B surface
# ---------------------------------------------------------------------------
def test_roles_absent_keeps_every_raw_v03b_tool_working(tmp_path):
    harness = build_roles_server(tmp_path, None)
    status = call(harness.server, "devrelay_status")
    assert status["ok"] is True
    assert status["data"]["roles"]["configured"] is False
    assert status["data"]["roles"]["supported_roles"] == ["implementer", "reviewer"]

    assert call(harness.server, "opencode_health")["ok"] is True
    raw = call(
        harness.server,
        "opencode_send_prompt",
        {"session_id": "ses_match", "prompt": "raw", "model": "caller/own-model"},
    )
    assert raw["ok"] is True
    assert harness.stub.prompts[-1]["model"] == {"providerID": "caller", "modelID": "own-model"}


def test_roles_absent_fails_only_role_aware_tools_locally(tmp_path):
    harness = build_roles_server(tmp_path, None)
    listed = call(harness.server, "devrelay_list_roles")
    assert listed["ok"] is True
    assert [entry["state"] for entry in listed["data"]["roles"]] == [
        "unconfigured",
        "unconfigured",
    ]

    got = call(harness.server, "devrelay_get_role", {"role": "reviewer"})
    assert got["ok"] is False and got["error"]["type"] == "role_unconfigured"

    sent = send_role(harness.server, "reviewer")
    assert sent["ok"] is False and sent["error"]["type"] == "role_unconfigured"
    assert harness.stub.requests == [], "an unconfigured role must not reach OpenCode"


def test_roles_present_do_not_change_non_role_envelopes(tmp_path):
    harness = build_roles_server(tmp_path, DISTINCT_ROLES)
    status = call(harness.server, "devrelay_status")
    assert status["data"]["roles"]["configured"] is True
    assert status["data"]["roles"]["roles"][0]["model"] == "provider-a/model-a"
    # every other pre-existing status key is untouched
    assert status["data"]["mcp"]["execution_serialized"] is True
    assert status["data"]["mcp"]["side_effects_serialized"] is True
    assert status["data"]["acceptance_authority"] is False


def test_empty_model_is_unconfigured_and_invalid_grammar_is_invalid(tmp_path):
    harness = build_roles_server(
        tmp_path, {"implementer": {"model": ""}, "reviewer": {"model": "not-a-route"}}
    )
    entries = {
        entry["role"]: entry for entry in call(harness.server, "devrelay_list_roles")["data"]["roles"]
    }
    assert entries["implementer"]["state"] == "unconfigured"
    assert entries["implementer"]["error"] == "role_unconfigured"
    assert entries["reviewer"]["state"] == "invalid"
    assert entries["reviewer"]["error"] == "role_invalid_route"
    assert entries["reviewer"]["model"] == "not-a-route"

    got = call(harness.server, "devrelay_get_role", {"role": "reviewer"})
    assert got["error"]["type"] == "role_invalid_route"
    assert harness.stub.requests == []


def test_roles_config_is_frozen(tmp_path):
    from pydantic import ValidationError

    wiring = wiring_for(tmp_path, DISTINCT_ROLES)
    with pytest.raises(ValidationError):
        wiring.roles.reviewer.model = "changed"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        RolesConfig().implementer = RolesConfig().reviewer  # type: ignore[misc]


def test_workspace_file_and_wiring_agree_on_roles(tmp_path):
    ws = tmp_path / "ws"
    (ws / ".devrelay").mkdir(parents=True, exist_ok=True)
    (ws / ".devrelay" / "config.yaml").write_text(
        yaml.safe_dump({"roles": DISTINCT_ROLES}, sort_keys=False), encoding="utf-8"
    )
    assert isinstance(load_workspace_file(ws / ".devrelay" / "config.yaml").roles, RolesConfig)
    assert load_wiring_config(ws).roles.implementer.model == "provider-a/model-a"
