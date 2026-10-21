"""v0.3-D MCP tool surface: inventory, schemas, descriptions, envelopes, secrets."""

from __future__ import annotations

import asyncio
import json

import pytest

from devrelay.mcp.tools import READ_ONLY_TOOLS, SIDE_EFFECTING_TOOLS, TOOL_NAMES
from devrelay.orchestration.recovery import ADOPTION_DISABLED_REASON

from v03d_helpers import (
    IMPLEMENTER_SESSION,
    REVIEWER_SESSION,
    RUN_ID,
    build,
    call,
    call_result,
    decide,
    fixed_run_ids,
    get_run,
    phase,
    run_id_of,
    start,
)

ORCHESTRATION_TOOLS = [
    "devrelay_start_run",
    "devrelay_get_run",
    "devrelay_run_implementer",
    "devrelay_run_reviewer",
    "devrelay_decide_run",
]
#: v0.3-E appends exactly two fail-closed recovery tools.
RECOVERY_TOOLS = ["devrelay_reconcile_run", "devrelay_resolve_recovery"]


def tools_of(server) -> dict:
    return {tool.name: tool for tool in asyncio.run(server.list_tools())}


# ---------------------------------------------------------------------------
# inventory and schemas
# ---------------------------------------------------------------------------
def test_inventory_is_sixteen_plus_exactly_five_seventeen(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    names = [tool.name for tool in asyncio.run(harness.server.list_tools())]
    assert names == list(TOOL_NAMES)
    assert len(names) == 19
    assert names[12:17] == ORCHESTRATION_TOOLS
    assert names[17:] == RECOVERY_TOOLS
    assert names[:12] == [
        "devrelay_status",
        "opencode_health",
        "opencode_list_sessions",
        "opencode_get_session",
        "opencode_read_messages",
        "opencode_calls",
        "opencode_send_prompt",
        "opencode_wait_idle",
        "opencode_interrupt",
        "devrelay_list_roles",
        "devrelay_get_role",
        "devrelay_send_role_prompt",
    ]
    assert set(READ_ONLY_TOOLS) | set(SIDE_EFFECTING_TOOLS) == set(TOOL_NAMES)


def test_orchestration_annotations_are_honest(tmp_path):
    tools = tools_of(build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID)).server)
    assert tools["devrelay_get_run"].annotations.read_only_hint is True
    for name in ("devrelay_start_run", "devrelay_run_implementer", "devrelay_run_reviewer", "devrelay_decide_run"):
        annotations = tools[name].annotations
        assert annotations.read_only_hint is False, name
        assert annotations.idempotent_hint is False, name


def test_input_schemas_accept_only_the_documented_arguments(tmp_path):
    tools = tools_of(build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID)).server)
    assert set(tools["devrelay_start_run"].input_schema["properties"]) == {
        "implementer_session_id",
        "reviewer_session_id",
        "max_cycles",
    }
    assert set(tools["devrelay_get_run"].input_schema["properties"]) == {"run_id"}
    for name in ("devrelay_run_implementer", "devrelay_run_reviewer"):
        assert set(tools[name].input_schema["properties"]) == {"run_id", "prompt"}
    assert set(tools["devrelay_decide_run"].input_schema["properties"]) == {"run_id", "decision"}
    for name in ORCHESTRATION_TOOLS:
        for forbidden in ("model", "agent", "endpoint", "workspace", "cwd", "retry", "task_prompt"):
            assert forbidden not in (tools[name].input_schema.get("properties") or {}), (name, forbidden)


def test_descriptions_are_a_planner_safety_surface(tmp_path):
    tools = tools_of(build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID)).server)
    start = tools["devrelay_start_run"].description or ""
    assert "NO model call" in start
    assert "two existing, different OpenCode sessions" in start
    assert "never creates" in start

    implementer = tools["devrelay_run_implementer"].description or ""
    assert "exactly ONE implementer role turn" in implementer
    assert "READY_IMPLEMENTER" in implementer
    assert "never retried" in implementer
    assert "BLOCKED" in implementer

    reviewer = tools["devrelay_run_reviewer"].description or ""
    assert "exactly ONE reviewer role turn" in reviewer
    assert "never interprets the reviewer" in reviewer
    assert "AWAITING_DECISION" in reviewer

    decide = tools["devrelay_decide_run"].description or ""
    assert "EXPLICIT external decision" in decide
    assert "complete" in decide and "request_changes" in decide and "stop" in decide
    assert "never starts the cycle for you" in decide
    assert "external_planner" in decide
    assert "no model call" in decide.lower()


# ---------------------------------------------------------------------------
# start / get behaviour through MCP
# ---------------------------------------------------------------------------
def test_start_run_is_zero_model_and_only_read_only_validation(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    envelope = start(harness.server, max_cycles=2)
    assert envelope["ok"] is True
    assert [p for m, p in harness.stub.requests if m == "POST"] == []
    assert all(method == "GET" for method, _path in harness.stub.requests), (
        "start_run may only perform bounded read-only ownership checks"
    )


def test_get_run_is_local_and_read_only(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)
    before_requests = list(harness.stub.requests)
    path = harness.ws / ".devrelay" / "orchestration" / "runs" / f"{run_id}.json"
    before_bytes = path.read_bytes()
    envelope = get_run(harness.server, run_id)
    assert envelope["ok"] is True
    assert list(harness.stub.requests) == before_requests
    assert path.read_bytes() == before_bytes


@pytest.mark.parametrize(
    "bad_run_id",
    ["../../etc/passwd", "DR-nothex", "", None, "DR-" + "a" * 200],
)
def test_malformed_run_ids_are_local_errors_and_never_paths(tmp_path, bad_run_id):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    envelope = call(harness.server, "devrelay_get_run", {"run_id": bad_run_id})
    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "mcp_invalid_argument"
    assert [p for m, p in harness.stub.requests if m == "POST"] == []
    assert not (harness.ws.parent / "etc").exists()


def test_a_non_string_run_id_is_rejected_at_the_sdk_boundary(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    with pytest.raises(Exception) as excinfo:
        asyncio.run(harness.server.call_tool("devrelay_get_run", {"run_id": 12}))
    assert "run_id" in str(excinfo.value)
    assert [p for m, p in harness.stub.requests if m == "POST"] == []


def test_unknown_run_id_is_a_bounded_local_error(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    envelope = get_run(harness.server, "DR-" + "9" * 32)
    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "orchestration_run_not_found"
    assert envelope["data"]["run_id"] == "DR-" + "9" * 32


# ---------------------------------------------------------------------------
# the P1 authority invariant through MCP
# ---------------------------------------------------------------------------
def test_reviewer_approve_never_completes_the_run_by_itself(tmp_path):
    from test_v03b_mcp_tools import real_reply

    from v03d_helpers import two_session_stub

    stub = two_session_stub(tmp_path / "ws", prompt_reply=real_reply(message_id="msg_i", text="done"))
    harness = build(tmp_path, stub=stub, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)
    assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is True
    stub.prompt_reply = real_reply(message_id="msg_r", text="APPROVE")
    reviewed = phase(harness.server, "devrelay_run_reviewer", run_id, "r")

    assert reviewed["ok"] is True
    assert reviewed["data"]["state"] == "AWAITING_DECISION"
    assert reviewed["data"]["terminal"] is False
    assert len([p for m, p in stub.requests if m == "POST"]) == 2
    state = get_run(harness.server, run_id)["data"]
    assert state["state"] == "AWAITING_DECISION"
    assert state["completed_cycles"] == 1

    completed = decide(harness.server, run_id, "complete")
    assert completed["data"]["state"] == "COMPLETED"
    assert len([p for m, p in stub.requests if m == "POST"]) == 2


def test_terminal_state_is_reported_in_the_error_envelope(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)
    phase(harness.server, "devrelay_run_implementer", run_id, "i")
    phase(harness.server, "devrelay_run_reviewer", run_id, "r")
    decide(harness.server, run_id, "stop")
    envelope = phase(harness.server, "devrelay_run_implementer", run_id, "again")
    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "orchestration_invalid_transition"
    assert envelope["data"]["state"] == "STOPPED"
    assert envelope["data"]["terminal"] is True
    assert envelope["data"]["legal_next_actions"] == []


def test_state_makes_the_legal_next_action_obvious(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)
    assert get_run(harness.server, run_id)["data"]["legal_next_actions"] == [
        "devrelay_run_implementer"
    ]
    phase(harness.server, "devrelay_run_implementer", run_id, "i")
    assert get_run(harness.server, run_id)["data"]["legal_next_actions"] == [
        "devrelay_run_reviewer"
    ]
    phase(harness.server, "devrelay_run_reviewer", run_id, "r")
    assert get_run(harness.server, run_id)["data"]["legal_next_actions"] == [
        "devrelay_decide_run(complete|request_changes|stop)"
    ]


# ---------------------------------------------------------------------------
# status surface, secrets and persistence scans
# ---------------------------------------------------------------------------
def test_status_exposes_the_orchestration_capability_block(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    data = call(harness.server, "devrelay_status")["data"]
    block = data["orchestration"]
    assert block == {
        "enabled": True,
        "hard_max_cycles": 3,
        "default_max_cycles": 2,
        "automatic_role_sequencing": False,
        "automatic_decisions": False,
        "durable_state": True,
        "state_location": "orchestration/runs",
        "recovery": {
            "available": True,
            "resolutions": ["mark_unrecoverable", "adopt_completed_turn"],
            "adoption_enabled": False,
            "adoption_reason": ADOPTION_DISABLED_REASON,
            "submits_model_requests": False,
            "retries": False,
            "resumes": False,
            "max_recovery_attempts": 1,
        },
    }
    assert "run_id" not in block and "state" not in block, "status never inlines a run"


def test_status_never_lists_raw_runs(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)
    blob = json.dumps(call(harness.server, "devrelay_status"))
    assert run_id not in blob


def test_no_credential_leaks_through_any_orchestration_envelope(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVRELAY_OPENCODE_TOKEN", "oc-token-V03D-MCP-SENTINEL-4711")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-v03d-mcp-sentinel-4711")
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    prompt = "PROMPT-MCP-SENTINEL-V03D"
    run_id = run_id_of(harness.server, max_cycles=1)
    payloads = [
        json.dumps(start(harness.server, max_cycles=1)),
        json.dumps(get_run(harness.server, run_id)),
        json.dumps(phase(harness.server, "devrelay_run_implementer", run_id, prompt)),
        json.dumps(phase(harness.server, "devrelay_run_reviewer", run_id, prompt)),
        json.dumps(decide(harness.server, run_id, "complete")),
        json.dumps(call(harness.server, "devrelay_status")),
    ]
    joined = "\n".join(payloads)
    assert "oc-token-V03D-MCP-SENTINEL-4711" not in joined
    assert "sk-v03d-mcp-sentinel-4711" not in joined
    assert prompt not in joined, "the orchestration path never echoes the prompt"


def test_durable_state_never_persists_prompt_or_reply_text(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    prompt = "PROMPT-FILE-SENTINEL-V03D"
    run_id = run_id_of(harness.server, max_cycles=1)
    phase(harness.server, "devrelay_run_implementer", run_id, prompt)
    phase(harness.server, "devrelay_run_reviewer", run_id, prompt)
    blob = (harness.ws / ".devrelay" / "orchestration" / "runs" / f"{run_id}.json").read_text(
        encoding="utf-8"
    )
    assert prompt not in blob
    assert "echo: " not in blob, "provider reply text is never persisted"
    assert "prompt_sha256" in blob and "prompt_chars" in blob
