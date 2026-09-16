"""v0.3-C role routing over the REAL stdio MCP boundary (deterministic fake).

Chain exercised here:

    real MCP client (mcp 2.2.0) -> stdio -> real ``devrelay mcp serve`` child
        -> role resolver -> accepted v0.3-A bridge -> deterministic fake OpenCode

No external model, no OpenCode process, no network.  The harness (candidate
pinning, loopback fake, exact tool list) is the accepted v0.3-B one; this suite
extends it with the three v0.3-C tools.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from mcp import ClientSession
from mcp.client.stdio import stdio_client

from test_v03b_mcp_stdio import (  # noqa: F401 - fake_opencode is a fixture
    EXACT_TOOLS,
    envelope_of,
    fake_opencode,
    make_workspace,
    server_params,
)
from v03c_helpers import AGENT_ROLES, DISTINCT_ROLES, IMPLEMENTER_WIRE, REVIEWER_WIRE

ROLE_TOOLS = ["devrelay_list_roles", "devrelay_get_role", "devrelay_send_role_prompt"]


def make_roles_workspace(
    tmp_path: Path, base_url: str, roles: dict[str, Any] | None
) -> Path:
    ws = make_workspace(tmp_path, base_url)
    path = ws / ".devrelay" / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if roles is None:
        data.pop("roles", None)
    else:
        data["roles"] = roles
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return ws


async def call(session: ClientSession, name: str, arguments: dict[str, Any]) -> Any:
    return await session.call_tool(name, arguments)


def run_over_stdio(ws: Path, script: Any) -> Any:
    async def runner() -> Any:
        async with stdio_client(server_params(ws)) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await script(session)

    return asyncio.run(runner())


def test_stdio_advertises_twelve_tools_and_the_role_tools(fake_opencode, tmp_path):
    ws = make_roles_workspace(tmp_path, fake_opencode.base_url, DISTINCT_ROLES)

    async def script(session: ClientSession) -> list[str]:
        tools = await session.list_tools()
        return [tool.name for tool in tools.tools]

    names = run_over_stdio(ws, script)
    assert len(EXACT_TOOLS) == 12
    assert names == EXACT_TOOLS
    assert names[9:] == ROLE_TOOLS


def test_stdio_role_views_report_the_configured_routes(fake_opencode, tmp_path):
    ws = make_roles_workspace(tmp_path, fake_opencode.base_url, AGENT_ROLES)

    async def script(session: ClientSession) -> dict[str, Any]:
        listed = envelope_of(await call(session, "devrelay_list_roles", {}))
        implementer = envelope_of(await call(session, "devrelay_get_role", {"role": "implementer"}))
        reviewer = envelope_of(await call(session, "devrelay_get_role", {"role": "reviewer"}))
        unknown = await call(session, "devrelay_get_role", {"role": "planner"})
        return {
            "listed": listed,
            "implementer": implementer,
            "reviewer": reviewer,
            "unknown": envelope_of(unknown),
            "unknown_is_error": unknown.is_error,
        }

    observed = run_over_stdio(ws, script)
    assert observed["listed"]["ok"] is True
    assert observed["listed"]["data"]["role_routing_configured"] is True
    assert observed["implementer"]["data"]["model"] == "provider-a/model-a"
    assert observed["implementer"]["data"]["agent"] == "build"
    assert observed["reviewer"]["data"]["model"] == "provider-b/model-b"
    assert observed["reviewer"]["data"]["agent"] == "review"
    assert observed["unknown"]["ok"] is False
    assert observed["unknown"]["error"]["type"] == "role_unknown"
    assert observed["unknown_is_error"] is True


def test_stdio_role_sends_reach_the_configured_wire_models(fake_opencode, tmp_path):
    ws = make_roles_workspace(tmp_path, fake_opencode.base_url, AGENT_ROLES)
    fake_opencode.stub.workspace = str(ws)
    for session in fake_opencode.stub.sessions:
        session["directory"] = str(ws)

    async def script(session: ClientSession) -> dict[str, Any]:
        implementer = await call(
            session,
            "devrelay_send_role_prompt",
            {"role": "implementer", "session_id": "ses_match", "prompt": "implement it"},
        )
        reviewer = await call(
            session,
            "devrelay_send_role_prompt",
            {"role": "reviewer", "session_id": "ses_match", "prompt": "review it"},
        )
        return {
            "implementer": envelope_of(implementer),
            "reviewer": envelope_of(reviewer),
            "implementer_is_error": implementer.is_error,
            "reviewer_is_error": reviewer.is_error,
            "text_matches": json.loads(
                [c.text for c in reviewer.content if getattr(c, "type", "") == "text"][0]
            )
            == envelope_of(reviewer),
        }

    observed = run_over_stdio(ws, script)
    assert observed["implementer"]["ok"] is True
    assert observed["reviewer"]["ok"] is True
    assert observed["implementer_is_error"] is False
    assert observed["reviewer_is_error"] is False
    assert observed["text_matches"] is True
    assert observed["implementer"]["data"]["resolved_model_identity"] == IMPLEMENTER_WIRE
    assert observed["reviewer"]["data"]["resolved_model_identity"] == REVIEWER_WIRE
    assert observed["implementer"]["data"]["resolved_agent"] == "build"
    assert observed["reviewer"]["data"]["resolved_agent"] == "review"

    bodies = fake_opencode.stub.prompts
    assert len(bodies) == 2, "one submission per role send, no retry, no fallback"
    assert bodies[0]["model"] == IMPLEMENTER_WIRE and bodies[0]["agent"] == "build"
    assert bodies[1]["model"] == REVIEWER_WIRE and bodies[1]["agent"] == "review"
    assert [p for m, p in fake_opencode.stub.requests if m == "POST"] == [
        "/session/ses_match/message",
        "/session/ses_match/message",
    ]


def test_stdio_role_send_never_leaks_a_model_override(fake_opencode, tmp_path):
    ws = make_roles_workspace(tmp_path, fake_opencode.base_url, DISTINCT_ROLES)
    fake_opencode.stub.workspace = str(ws)
    for session in fake_opencode.stub.sessions:
        session["directory"] = str(ws)

    async def script(session: ClientSession) -> dict[str, Any]:
        result = await call(
            session,
            "devrelay_send_role_prompt",
            {
                "role": "reviewer",
                "session_id": "ses_match",
                "prompt": "review it",
                "model": "provider-a/model-a",
                "agent": "build",
            },
        )
        return {"envelope": envelope_of(result), "is_error": result.is_error}

    observed = run_over_stdio(ws, script)
    assert observed["is_error"] is False
    assert observed["envelope"]["data"]["resolved_model_identity"] == REVIEWER_WIRE
    body = fake_opencode.stub.prompts[-1]
    assert body["model"] == REVIEWER_WIRE and "agent" not in body


def test_stdio_unknown_and_unconfigured_roles_never_reach_opencode(fake_opencode, tmp_path):
    ws = make_roles_workspace(tmp_path, fake_opencode.base_url, {"implementer": {"model": "provider-a/model-a"}})
    fake_opencode.stub.workspace = str(ws)
    for session in fake_opencode.stub.sessions:
        session["directory"] = str(ws)

    async def script(session: ClientSession) -> dict[str, Any]:
        unknown = await call(
            session,
            "devrelay_send_role_prompt",
            {"role": "planner", "session_id": "ses_match", "prompt": "hi"},
        )
        unconfigured = await call(
            session,
            "devrelay_send_role_prompt",
            {"role": "reviewer", "session_id": "ses_match", "prompt": "hi"},
        )
        return {
            "unknown": envelope_of(unknown),
            "unconfigured": envelope_of(unconfigured),
        }

    observed = run_over_stdio(ws, script)
    assert observed["unknown"]["error"]["type"] == "role_unknown"
    assert observed["unconfigured"]["error"]["type"] == "role_unconfigured"
    assert fake_opencode.stub.prompts == [], "no model POST for a routing failure"
    assert [p for m, p in fake_opencode.stub.requests if m == "POST"] == []


def test_stdio_workspace_without_roles_still_serves_every_raw_tool(fake_opencode, tmp_path):
    ws = make_roles_workspace(tmp_path, fake_opencode.base_url, None)
    fake_opencode.stub.workspace = str(ws)
    for session in fake_opencode.stub.sessions:
        session["directory"] = str(ws)

    async def script(session: ClientSession) -> dict[str, Any]:
        tools = await session.list_tools()
        status = envelope_of(await call(session, "devrelay_status", {}))
        raw = envelope_of(
            await call(
                session,
                "opencode_send_prompt",
                {"session_id": "ses_match", "prompt": "raw", "model": "caller/own-model"},
            )
        )
        role = envelope_of(
            await call(
                session,
                "devrelay_send_role_prompt",
                {"role": "reviewer", "session_id": "ses_match", "prompt": "hi"},
            )
        )
        return {
            "tool_count": len(tools.tools),
            "status": status,
            "raw": raw,
            "role": role,
        }

    observed = run_over_stdio(ws, script)
    assert observed["tool_count"] == 12, "role routing absent must not shrink the surface"
    assert observed["status"]["data"]["roles"]["configured"] is False
    assert observed["raw"]["ok"] is True
    assert observed["role"]["ok"] is False and observed["role"]["error"]["type"] == "role_unconfigured"
    assert fake_opencode.stub.prompts[-1]["model"] == {
        "providerID": "caller",
        "modelID": "own-model",
    }
    assert len(fake_opencode.stub.prompts) == 1, "only the raw path submitted"


def test_stdio_reviewer_reply_is_text_not_a_decision(fake_opencode, tmp_path):
    ws = make_roles_workspace(tmp_path, fake_opencode.base_url, DISTINCT_ROLES)
    fake_opencode.stub.workspace = str(ws)
    for session in fake_opencode.stub.sessions:
        session["directory"] = str(ws)
    fake_opencode.stub.prompt_reply = {
        "info": {
            "id": "msg_review",
            "sessionID": "ses_match",
            "role": "assistant",
            "time": {"created": 1_789_554_011_423},
        },
        "parts": [{"type": "text", "text": "APPROVE"}],
    }

    async def script(session: ClientSession) -> dict[str, Any]:
        return envelope_of(
            await call(
                session,
                "devrelay_send_role_prompt",
                {"role": "reviewer", "session_id": "ses_match", "prompt": "review it"},
            )
        )

    envelope = run_over_stdio(ws, script)
    assert envelope["ok"] is True
    text = "".join(
        part["text"] for part in envelope["data"]["messages"][0]["parts"] if part["kind"] == "text"
    )
    assert text == "APPROVE"
    for key in ("decision", "verdict", "approved", "accepted", "next_action"):
        assert key not in envelope["data"], key
