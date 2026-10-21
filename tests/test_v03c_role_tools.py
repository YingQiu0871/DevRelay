"""v0.3-C role-aware MCP tools, driven through the real MCP SDK dispatch.

Offline: the real surface over the real v0.3-A bridge wired to the accepted
OpenCode stub (``httpx.MockTransport``).  No process, no socket, no model.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from devrelay.mcp.tools import (
    READ_ONLY_TOOLS,
    SIDE_EFFECTING_TOOLS,
    TOOL_NAMES,
)
from devrelay.roles.models import RoleRouteConfig, RolesConfig, SUPPORTED_ROLES

from opencode_stub import StubOpenCodeServer, _session
from test_v03b_mcp_tools import real_reply
from v03c_helpers import (
    AGENT_ROLES,
    DISTINCT_ROLES,
    IMPLEMENTER_WIRE,
    REVIEWER_WIRE,
    ROLE_PROMPT,
    build_roles_server,
    call,
    call_result,
    last_wire_body,
    ledger_records,
    posts,
    prompt_texts,
    send_role,
    wire_bodies,
)

ROLE_TOOL = "devrelay_send_role_prompt"


# ---------------------------------------------------------------------------
# A. inventory, annotations and input schemas
# ---------------------------------------------------------------------------
def tools_of(server: Any) -> dict[str, Any]:
    return {tool.name: tool for tool in asyncio.run(server.list_tools())}


def test_inventory_is_the_accepted_nine_plus_exactly_three(tmp_path):
    harness = build_roles_server(tmp_path)
    names = [tool.name for tool in asyncio.run(harness.server.list_tools())]
    assert names == list(TOOL_NAMES)
    assert len(names) == 19
    assert names[:9] == [
        "devrelay_status",
        "opencode_health",
        "opencode_list_sessions",
        "opencode_get_session",
        "opencode_read_messages",
        "opencode_calls",
        "opencode_send_prompt",
        "opencode_wait_idle",
        "opencode_interrupt",
    ]
    assert names[9:12] == ["devrelay_list_roles", "devrelay_get_role", ROLE_TOOL]
    assert names[12:17] == [
        "devrelay_start_run",
        "devrelay_get_run",
        "devrelay_run_implementer",
        "devrelay_run_reviewer",
        "devrelay_decide_run",
    ]
    # v0.3-E appends exactly two fail-closed recovery tools.
    assert names[17:] == ["devrelay_reconcile_run", "devrelay_resolve_recovery"]
    assert set(READ_ONLY_TOOLS) | set(SIDE_EFFECTING_TOOLS) == set(TOOL_NAMES)


def test_role_tool_annotations_are_honest(tmp_path):
    tools = tools_of(build_roles_server(tmp_path).server)
    for name in ("devrelay_list_roles", "devrelay_get_role"):
        assert tools[name].annotations.read_only_hint is True, name
    send = tools[ROLE_TOOL].annotations
    assert send.read_only_hint is False
    assert send.idempotent_hint is False
    assert send.destructive_hint in (False, None)


def test_role_send_input_schema_has_no_route_override(tmp_path):
    tools = tools_of(build_roles_server(tmp_path).server)
    properties = set(tools[ROLE_TOOL].input_schema.get("properties") or {})
    assert properties == {"role", "session_id", "prompt"}
    for forbidden in ("model", "agent", "workspace", "cwd", "endpoint", "retry", "retry_safe"):
        assert forbidden not in properties, forbidden
    listed = set(tools["devrelay_list_roles"].input_schema.get("properties") or {})
    assert listed == set()
    assert set(tools["devrelay_get_role"].input_schema.get("properties") or {}) == {"role"}


def test_role_tool_descriptions_are_a_safety_surface(tmp_path):
    tools = tools_of(build_roles_server(tmp_path).server)
    send = tools[ROLE_TOOL].description or ""
    for phrase in (
        "SEMANTIC ROLE",
        "implementer or reviewer",
        "cannot pass a model or an agent",
        "cannot be overridden at call time",
        "exactly ONE",
        "never retries",
        "never switches roles automatically",
        "submission_uncertain",
        "reply_pending",
        "retry_safe",
        "NOT an acceptance decision",
        "no acceptance",
    ):
        assert phrase in send, phrase
    for name in ("devrelay_list_roles", "devrelay_get_role"):
        description = tools[name].description or ""
        assert description.startswith("Read-only"), name
        assert "Read-only" in description


def test_no_role_tool_is_dangerous(tmp_path):
    for name in TOOL_NAMES:
        for word in ("shell", "exec", "subprocess", "http_request", "git_", "delete", "token"):
            assert word not in name.lower(), (name, word)


# ---------------------------------------------------------------------------
# B. read-only role views
# ---------------------------------------------------------------------------
def test_status_reports_role_routing_state(tmp_path):
    configured = call(build_roles_server(tmp_path, DISTINCT_ROLES).server, "devrelay_status")
    roles = configured["data"]["roles"]
    assert roles["configured"] is True
    assert roles["supported_roles"] == list(SUPPORTED_ROLES)
    assert [entry["model"] for entry in roles["roles"]] == [
        "provider-a/model-a",
        "provider-b/model-b",
    ]

    unconfigured = call(build_roles_server(tmp_path, None).server, "devrelay_status")
    assert unconfigured["data"]["roles"]["configured"] is False
    assert all(entry["model"] is None for entry in unconfigured["data"]["roles"]["roles"])


def test_list_roles_is_read_only_and_sanitized(tmp_path):
    harness = build_roles_server(tmp_path, AGENT_ROLES)
    listed = call(harness.server, "devrelay_list_roles")
    assert listed["ok"] is True and listed["tool"] == "devrelay_list_roles"
    assert listed["data"]["read_only"] is True
    assert listed["data"]["acceptance_authority"] is False
    assert listed["data"]["role_routing_configured"] is True
    assert harness.stub.requests == [], "a read-only view must not touch OpenCode"


@pytest.mark.parametrize(
    "role,model,agent",
    [
        ("implementer", "provider-a/model-a", None),
        ("reviewer", "provider-b/model-b", None),
    ],
)
def test_get_role_returns_the_exact_route(tmp_path, role, model, agent):
    harness = build_roles_server(tmp_path, DISTINCT_ROLES)
    resolved = call(harness.server, "devrelay_get_role", {"role": role})
    assert resolved["ok"] is True
    assert resolved["data"]["role"] == role
    assert resolved["data"]["model"] == model
    assert resolved["data"]["agent"] is agent
    assert resolved["data"]["route_source"] == "workspace_config"
    assert harness.stub.requests == []


# ---------------------------------------------------------------------------
# C. implementer/reviewer separation on the wire
# ---------------------------------------------------------------------------
def test_implementer_and_reviewer_reach_their_own_wire_models(tmp_path):
    harness = build_roles_server(tmp_path, DISTINCT_ROLES)

    implementer = send_role(harness.server, "implementer")
    assert implementer["ok"] is True
    assert last_wire_body(harness.stub)["model"] == IMPLEMENTER_WIRE
    assert implementer["data"]["resolved_model_identity"] == IMPLEMENTER_WIRE

    reviewer = send_role(harness.server, "reviewer")
    assert reviewer["ok"] is True
    assert last_wire_body(harness.stub)["model"] == REVIEWER_WIRE
    assert reviewer["data"]["resolved_model_identity"] == REVIEWER_WIRE

    assert posts(harness.stub) == [
        "/session/ses_match/message",
        "/session/ses_match/message",
    ], "exactly one POST per role send, no retry, no duplicate"
    assert prompt_texts(harness.stub) == [ROLE_PROMPT, ROLE_PROMPT]


def test_no_cross_routing_between_the_two_roles(tmp_path):
    harness = build_roles_server(tmp_path, DISTINCT_ROLES)
    for role, expected in (("implementer", IMPLEMENTER_WIRE), ("reviewer", REVIEWER_WIRE)):
        send_role(harness.server, role)
        assert last_wire_body(harness.stub)["model"] == expected
    for body in wire_bodies(harness.stub):
        model = body["model"]
        assert model in (IMPLEMENTER_WIRE, REVIEWER_WIRE)
        assert not (model == IMPLEMENTER_WIRE and "provider-b" in json.dumps(body))


def test_ledger_records_the_routed_model_for_each_role(tmp_path):
    harness = build_roles_server(tmp_path, DISTINCT_ROLES)
    send_role(harness.server, "implementer")
    send_role(harness.server, "reviewer")
    records = ledger_records(harness.ws)
    submissions = [record for record in records if record["method"] == "POST"]
    assert [record["model"] for record in submissions] == [
        "provider-a/model-a",
        "provider-b/model-b",
    ]
    assert all(record["state"] == "COMPLETED" for record in records)
    assert len({record["call_id"] for record in records}) == len(records)


def test_role_route_is_switched_only_by_configuration(tmp_path):
    first = build_roles_server(tmp_path / "a", DISTINCT_ROLES)
    send_role(first.server, "reviewer")
    assert last_wire_body(first.stub)["model"] == REVIEWER_WIRE

    reassigned = build_roles_server(
        tmp_path / "b", {"implementer": {"model": "provider-a/model-a"}, "reviewer": {"model": "provider-c/model-c"}}
    )
    send_role(reassigned.server, "reviewer")
    assert last_wire_body(reassigned.stub)["model"] == {
        "providerID": "provider-c",
        "modelID": "model-c",
    }


# ---------------------------------------------------------------------------
# D. optional agent routing
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "role,agent", [("implementer", "build"), ("reviewer", "review")]
)
def test_configured_agent_reaches_the_wire(tmp_path, role, agent):
    harness = build_roles_server(tmp_path, AGENT_ROLES)
    envelope = send_role(harness.server, role)
    assert envelope["ok"] is True
    assert last_wire_body(harness.stub)["agent"] == agent
    assert envelope["data"]["resolved_agent"] == agent


def test_omitted_agent_is_left_out_of_the_request_entirely(tmp_path):
    harness = build_roles_server(tmp_path, DISTINCT_ROLES)
    envelope = send_role(harness.server, "reviewer")
    body = last_wire_body(harness.stub)
    assert "agent" not in body, "an unconfigured agent must be omitted, not empty"
    assert envelope["data"]["resolved_agent"] is None


def test_only_one_role_needs_an_agent(tmp_path):
    harness = build_roles_server(
        tmp_path,
        {"implementer": {"model": "provider-a/model-a", "agent": "build"}, "reviewer": {"model": "provider-b/model-b"}},
    )
    send_role(harness.server, "implementer")
    assert last_wire_body(harness.stub)["agent"] == "build"
    send_role(harness.server, "reviewer")
    assert "agent" not in last_wire_body(harness.stub)


# ---------------------------------------------------------------------------
# E. the caller cannot override the route (P1)
# ---------------------------------------------------------------------------
def test_caller_supplied_model_and_agent_are_ignored(tmp_path):
    harness = build_roles_server(tmp_path, DISTINCT_ROLES)
    envelope = call(
        harness.server,
        ROLE_TOOL,
        {
            "role": "reviewer",
            "session_id": "ses_match",
            "prompt": ROLE_PROMPT,
            "model": "provider-a/model-a",
            "agent": "build",
        },
    )
    assert envelope["ok"] is True
    body = last_wire_body(harness.stub)
    assert body["model"] == REVIEWER_WIRE, "the configured route wins"
    assert "agent" not in body, "the caller cannot inject an agent either"
    assert envelope["data"]["resolved_model_identity"] == REVIEWER_WIRE


def test_role_configuration_cannot_carry_credentials():
    assert set(RolesConfig.model_fields) == {"implementer", "reviewer"}
    assert set(RoleRouteConfig.model_fields) == {"model", "agent"}


def test_every_role_send_envelope_is_route_evidenced(tmp_path):
    harness = build_roles_server(tmp_path, AGENT_ROLES)
    for role in ("implementer", "reviewer"):
        envelope = send_role(harness.server, role)
        assert envelope["tool"] == ROLE_TOOL
        assert envelope["ok"] is True
        data = envelope["data"]
        assert data["role"] == role
        assert data["resolved_model"] in ("provider-a/model-a", "provider-b/model-b")
        assert data["route_source"] == "workspace_config"
        assert "role_routing" in data


# ---------------------------------------------------------------------------
# F. failure semantics and taxonomy
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "role,error_type",
    [
        ("planner", "role_unknown"),
        ("Implementer", "role_unknown"),
        ("", "role_unknown"),
        (None, "role_unknown"),
        (None, "role_unknown"),
    ],
    ids=["planner", "case-variant", "blank", "null", "omitted"],
)
def test_unknown_or_omitted_role_fails_locally(tmp_path, role, error_type):
    harness = build_roles_server(tmp_path, DISTINCT_ROLES)
    arguments = {"session_id": "ses_match", "prompt": ROLE_PROMPT}
    if role is not None:
        arguments["role"] = role
    result = call_result(harness.server, ROLE_TOOL, arguments)
    envelope = result.structured_content
    assert envelope["ok"] is False and envelope["error"]["type"] == error_type
    assert result.is_error is True
    assert harness.stub.requests == [], "an unknown role must not reach OpenCode"


def test_unconfigured_role_fails_locally(tmp_path):
    harness = build_roles_server(tmp_path, {"implementer": {"model": "provider-a/model-a"}})
    envelope = send_role(harness.server, "reviewer")
    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "role_unconfigured"
    assert envelope["data"]["role"] == "reviewer"
    assert envelope["data"]["supported_roles"] == list(SUPPORTED_ROLES)
    assert harness.stub.requests == []


def test_invalid_configured_route_fails_locally_and_is_not_a_provider_error(tmp_path):
    harness = build_roles_server(
        tmp_path, {"implementer": {"model": "provider-a/model-a"}, "reviewer": {"model": "broken"}}
    )
    envelope = send_role(harness.server, "reviewer")
    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "role_invalid_route"
    assert "provider_unavailable" not in envelope["error"]["type"]
    assert "opencode" not in envelope["error"]["type"]
    assert harness.stub.requests == []


def test_routing_failures_are_never_reported_as_provider_failures(tmp_path):
    harness = build_roles_server(tmp_path, DISTINCT_ROLES)
    for role, expected in (("planner", "role_unknown"), ("", "role_unknown")):
        envelope = send_role(harness.server, role)
        assert envelope["error"]["type"] == expected
        assert envelope["data"] == {
            "role": role or None,
            "supported_roles": list(SUPPORTED_ROLES),
            "route_source": "workspace_config",
            "role_routing_configured": True,
        }


def test_foreign_session_still_fails_closed_with_no_submission(tmp_path):
    foreign = StubOpenCodeServer(
        workspace="C:/elsewhere",
        sessions=[_session("ses_foreign", workspace="C:/elsewhere")],
    )
    harness = build_roles_server(
        tmp_path, DISTINCT_ROLES, stub=foreign, bind_stub=False
    )
    envelope = send_role(harness.server, "reviewer", session_id="ses_foreign")
    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "opencode_session_workspace_mismatch"
    assert posts(harness.stub) == [], "ownership is checked before any submission"
    assert envelope["data"]["resolved_model"] == "provider-b/model-b"


def test_argument_validation_still_precedes_the_network(tmp_path):
    harness = build_roles_server(tmp_path, DISTINCT_ROLES)
    bad_session = send_role(harness.server, "reviewer", session_id="../../etc/passwd")
    assert bad_session["ok"] is False and bad_session["error"]["type"] == "mcp_invalid_argument"
    bad_prompt = send_role(harness.server, "reviewer", prompt="   ")
    assert bad_prompt["ok"] is False and bad_prompt["error"]["type"] == "mcp_invalid_argument"
    assert harness.stub.requests == []


# ---------------------------------------------------------------------------
# G. exactly-one-submission semantics through the role path
# ---------------------------------------------------------------------------
ROLE_FAILURE_MATRIX: tuple[
    tuple[str, dict[str, Any], bool, int | None, bool, bool, bool, int], ...
] = (
    # label, stub kwargs, ok, submission_status, submission_uncertain,
    # reply_pending, retry_safe, expected submission POSTs
    ("inline_success", {"prompt_reply": real_reply()}, True, 200, False, False, False, 1),
    ("connect_error", {"prompt_exception": "connect_error"}, False, None, False, False, True, 1),
    ("read_timeout", {"prompt_exception": "read_timeout"}, False, None, True, True, False, 1),
    ("write_timeout", {"prompt_exception": "write_timeout"}, False, None, True, True, False, 1),
    ("html_2xx", {"prompt_html_fallback": True}, False, 200, True, True, False, 1),
    ("rejected_500", {"prompt_http_status": 500}, False, 500, False, False, False, 1),
    ("accepted_pending", {"prompt_raw_reply": {"ok": True}}, False, 200, False, True, False, 1),
)


@pytest.mark.parametrize(
    "label,stub_kwargs,expected_ok,status,uncertain,pending,retry_safe,expected_posts",
    ROLE_FAILURE_MATRIX,
    ids=[case[0] for case in ROLE_FAILURE_MATRIX],
)
def test_role_path_preserves_every_accepted_send_semantic(
    tmp_path,
    label,
    stub_kwargs,
    expected_ok,
    status,
    uncertain,
    pending,
    retry_safe,
    expected_posts,
):
    """The role path adds a route, never a new submission semantic."""
    stub = StubOpenCodeServer(**stub_kwargs)
    harness = build_roles_server(tmp_path, DISTINCT_ROLES, stub=stub)
    envelope = send_role(harness.server, "reviewer")

    assert envelope["ok"] is expected_ok, label
    data = envelope["data"]
    assert data["submission_attempted"] is True, label
    assert data["submission_status"] == status, label
    assert data["submission_uncertain"] is uncertain, label
    assert data["reply_pending"] is pending, label
    assert data["retry_safe"] is retry_safe, label
    assert data["role"] == "reviewer", label
    assert data["resolved_model"] == "provider-b/model-b", label
    assert data["resolved_model_identity"] == REVIEWER_WIRE, label
    if uncertain or pending:
        assert data["retry_safe"] is False, "an ambiguous submission is never retry_safe"
    if expected_ok:
        assert data["state"] == "COMPLETED", label
    submitted = posts(harness.stub)
    assert len(submitted) <= 1, f"{label}: never more than one submission POST"
    assert len(submitted) == expected_posts, label
    if expected_posts:
        assert submitted == ["/session/ses_match/message"], label
    assert "Traceback" not in json.dumps(envelope)

@pytest.mark.parametrize("role", ["implementer", "reviewer"])
def test_one_post_per_role_send_and_no_retry(tmp_path, role):
    harness = build_roles_server(tmp_path, DISTINCT_ROLES)
    envelope = send_role(harness.server, role)
    assert envelope["ok"] is True
    assert posts(harness.stub) == ["/session/ses_match/message"]
    assert len(harness.stub.prompts) == 1
    assert envelope["data"]["request_count"] >= 1
    assert envelope["data"]["state"] == "COMPLETED"


def test_no_fallback_model_is_ever_used(tmp_path):
    """A failing reviewer route must never silently become the implementer route."""
    stub = StubOpenCodeServer(prompt_http_status=500)
    harness = build_roles_server(tmp_path, DISTINCT_ROLES, stub=stub)
    envelope = send_role(harness.server, "reviewer")
    assert envelope["ok"] is False
    assert [body["model"] for body in wire_bodies(stub)] == [REVIEWER_WIRE]
    assert IMPLEMENTER_WIRE not in [body["model"] for body in wire_bodies(stub)]
    assert envelope["data"]["resolved_model_identity"] == REVIEWER_WIRE


# ---------------------------------------------------------------------------
# H. auditability
# ---------------------------------------------------------------------------
def test_a_planner_can_answer_every_routing_question(tmp_path):
    harness = build_roles_server(tmp_path, AGENT_ROLES)
    envelope = send_role(harness.server, "reviewer")
    data = envelope["data"]
    assert data["role"] == "reviewer"  # which semantic role was requested?
    assert data["resolved_model"] == "provider-b/model-b"  # which model was selected?
    assert data["resolved_agent"] == "review"  # which agent was selected?
    assert data["submission_attempted"] is True  # did the model POST occur?
    assert data["submission_uncertain"] is False  # was submission uncertain?
    assert data["call_ids"], "which OpenCode call ids belong to it?"
    assert data["route_source"] == "workspace_config"
    # ... and the claim is "configured routing", never "the model that should be used"
    assert "should" not in json.dumps(data)


def test_role_envelope_never_echoes_the_prompt_in_routing_metadata(tmp_path):
    harness = build_roles_server(tmp_path, DISTINCT_ROLES)
    secret_prompt = "PROMPT-SENTINEL-4711"
    envelope = send_role(harness.server, "reviewer", prompt=secret_prompt)
    routing = {
        key: value
        for key, value in envelope["data"].items()
        if key
        in (
            "role",
            "resolved_model",
            "resolved_model_identity",
            "resolved_agent",
            "route_source",
            "role_routing",
        )
    }
    assert secret_prompt not in json.dumps(routing)


# ---------------------------------------------------------------------------
# I. the raw path is unchanged (backward compatibility)
# ---------------------------------------------------------------------------
def test_raw_send_prompt_keeps_the_caller_model_when_roles_are_configured(tmp_path):
    harness = build_roles_server(tmp_path, DISTINCT_ROLES)
    envelope = call(
        harness.server,
        "opencode_send_prompt",
        {"session_id": "ses_match", "prompt": "raw prompt", "model": "caller/own-model"},
    )
    assert envelope["ok"] is True
    assert envelope["tool"] == "opencode_send_prompt"
    assert last_wire_body(harness.stub)["model"] == {
        "providerID": "caller",
        "modelID": "own-model",
    }
    for key in ("role", "resolved_model", "resolved_agent", "route_source", "role_routing"):
        assert key not in envelope["data"], key


def test_raw_path_is_not_redirected_through_role_routing(tmp_path):
    harness = build_roles_server(tmp_path, DISTINCT_ROLES)
    call(
        harness.server,
        "opencode_send_prompt",
        {"session_id": "ses_match", "prompt": "raw", "model": "provider-x/model-x", "agent": "rawagent"},
    )
    body = last_wire_body(harness.stub)
    assert body["model"] == {"providerID": "provider-x", "modelID": "model-x"}
    assert body["agent"] == "rawagent"
    assert body["model"] not in (IMPLEMENTER_WIRE, REVIEWER_WIRE)


def test_raw_path_works_without_any_role_configuration(tmp_path):
    harness = build_roles_server(tmp_path, None)
    envelope = call(
        harness.server, "opencode_send_prompt", {"session_id": "ses_match", "prompt": "hi"}
    )
    assert envelope["ok"] is True  # no model at all: the accepted v0.3-A behavior
    assert "model" not in last_wire_body(harness.stub)


def test_both_paths_can_be_used_in_one_session(tmp_path):
    harness = build_roles_server(tmp_path, DISTINCT_ROLES)
    raw = call(
        harness.server,
        "opencode_send_prompt",
        {"session_id": "ses_match", "prompt": "raw", "model": "caller/own-model"},
    )
    role = send_role(harness.server, "implementer")
    assert raw["ok"] is True and role["ok"] is True
    assert [body["model"] for body in wire_bodies(harness.stub)] == [
        {"providerID": "caller", "modelID": "own-model"},
        IMPLEMENTER_WIRE,
    ]


# ---------------------------------------------------------------------------
# J. secret and logging boundary
# ---------------------------------------------------------------------------
def test_no_credential_leaks_through_any_role_envelope(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVRELAY_OPENCODE_TOKEN", "oc-token-ROLE-SENTINEL-4711")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-role-sentinel-4711")
    diagnostics: list[str] = []
    harness = build_roles_server(tmp_path, AGENT_ROLES)
    payloads = [
        json.dumps(call(harness.server, "devrelay_status")),
        json.dumps(call(harness.server, "devrelay_list_roles")),
        json.dumps(call(harness.server, "devrelay_get_role", {"role": "reviewer"})),
        json.dumps(send_role(harness.server, "implementer")),
        json.dumps(send_role(harness.server, "planner")),
        "\n".join(diagnostics),
    ]
    joined = "\n".join(payloads)
    assert "oc-token-ROLE-SENTINEL-4711" not in joined
    assert "sk-role-sentinel-4711" not in joined


def test_durable_ledger_never_stores_the_role_prompt_or_a_credential(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVRELAY_OPENCODE_TOKEN", "oc-token-ROLE-SENTINEL-4711")
    harness = build_roles_server(tmp_path, DISTINCT_ROLES)
    prompt = "ROLE-PROMPT-SENTINEL-4711"
    send_role(harness.server, "reviewer", prompt=prompt)

    calls_dir = harness.ws / ".devrelay" / "opencode" / "calls"
    blob = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(calls_dir.glob("*.json"))
    )
    assert prompt not in blob
    assert "oc-token-ROLE-SENTINEL-4711" not in blob
    assert "prompt_sha256" in blob and "prompt_chars" in blob
    assert "provider-b/model-b" in blob  # the routed model is evidence, not a secret


# ---------------------------------------------------------------------------
# K. routing is not orchestration and carries no acceptance authority
# ---------------------------------------------------------------------------
def test_no_role_tool_can_accept_reject_or_sequence_anything(tmp_path):
    tools = tools_of(build_roles_server(tmp_path).server)
    for name, tool in tools.items():
        description = (tool.description or "").lower()
        for phrase in ("approve the implementation", "mark as accepted", "merge decision"):
            assert phrase not in description, name
    assert "no acceptance authority" in (tools[ROLE_TOOL].description or "")
    # The three new tools are exactly: two read-only views + one bounded send.
    assert {name for name in TOOL_NAMES[9:12]} == {
        "devrelay_list_roles",
        "devrelay_get_role",
        "devrelay_send_role_prompt",
    }


def test_reviewer_output_is_text_not_a_decision(tmp_path):
    """A reviewer reply that looks like APPROVE stays provider text."""
    stub = StubOpenCodeServer(
        prompt_reply=real_reply(text="REQUEST_CHANGES: please fix the parser")
    )
    harness = build_roles_server(tmp_path, DISTINCT_ROLES, stub=stub)
    envelope = send_role(harness.server, "reviewer")
    assert envelope["ok"] is True
    messages = envelope["data"]["messages"]
    assert [message["role"] for message in messages] == ["assistant"]
    text = "".join(
        part["text"] for part in messages[0]["parts"] if part["kind"] == "text"
    )
    assert text == "REQUEST_CHANGES: please fix the parser"
    # DevRelay reports the text and nothing else: no decision field exists.
    for key in ("decision", "verdict", "approved", "accepted", "next_action"):
        assert key not in envelope["data"], key
    # and the failing reviewer route never switches to the implementer's model
    assert [body["model"] for body in wire_bodies(stub)] == [REVIEWER_WIRE]
