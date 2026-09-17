"""v0.3-D bounded orchestration over the REAL stdio MCP boundary (offline).

Chain: official MCP client -> real ``devrelay mcp serve`` child -> orchestration
service -> role router -> accepted bridge -> deterministic loopback fake
OpenCode.  No external model, no OpenCode process, no network.
"""

from __future__ import annotations

import asyncio
import json
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

IMPLEMENTER_SESSION = "ses_impl"
REVIEWER_SESSION = "ses_rev"
ORCHESTRATION_TOOLS = [
    "devrelay_start_run",
    "devrelay_get_run",
    "devrelay_run_implementer",
    "devrelay_run_reviewer",
    "devrelay_decide_run",
]


def make_orchestration_workspace(tmp_path, base_url: str):
    ws = make_workspace(tmp_path, base_url)
    path = ws / ".devrelay" / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    data["roles"] = {
        "implementer": {"model": "provider-a/model-a"},
        "reviewer": {"model": "provider-b/model-b"},
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return ws


def two_sessions(fake, ws):
    stub = fake.stub
    base = dict(stub.sessions[0])
    stub.sessions = [
        dict(base, id=IMPLEMENTER_SESSION, directory=str(ws)),
        dict(base, id=REVIEWER_SESSION, directory=str(ws)),
    ]
    stub.workspace = str(ws)
    for session in stub.sessions:
        session["directory"] = str(ws)
    return stub


def reply(message_id: str, text: str) -> dict[str, Any]:
    return {
        "info": {"id": message_id, "sessionID": "x", "role": "assistant", "time": {"created": 1}},
        "parts": [{"type": "text", "text": text}],
    }


def posts(stub) -> list[str]:
    return [p for method, p in stub.requests if method == "POST"]


def run_over_stdio(ws, script):
    async def runner():
        async with stdio_client(server_params(ws)) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                return await script(session, init)

    return asyncio.run(runner())


def start_args(max_cycles: int = 1) -> dict[str, Any]:
    return {
        "implementer_session_id": IMPLEMENTER_SESSION,
        "reviewer_session_id": REVIEWER_SESSION,
        "max_cycles": max_cycles,
    }


def test_stdio_advertises_seventeen_tools(fake_opencode, tmp_path):
    ws = make_orchestration_workspace(tmp_path, fake_opencode.base_url)
    two_sessions(fake_opencode, ws)

    async def script(session, _init):
        return [tool.name for tool in (await session.list_tools()).tools]

    names = run_over_stdio(ws, script)
    assert len(EXACT_TOOLS) == 17
    assert names == EXACT_TOOLS
    assert names[12:] == ORCHESTRATION_TOOLS


def test_stdio_one_cycle_keeps_awaiting_decision_until_the_planner_decides(
    fake_opencode, tmp_path
):
    ws = make_orchestration_workspace(tmp_path, fake_opencode.base_url)
    stub = two_sessions(fake_opencode, ws)

    async def script(session, _init):
        out: dict[str, Any] = {}
        stub.prompt_reply = reply("msg_impl", "implemented")
        start = envelope_of(await session.call_tool("devrelay_start_run", start_args(1)))
        run_id = start["data"]["run_id"]
        out["start"] = start["data"]
        out["posts_after_start"] = len(posts(stub))

        implemented = await session.call_tool(
            "devrelay_run_implementer", {"run_id": run_id, "prompt": "implement it"}
        )
        out["implemented"] = envelope_of(implemented)

        # the reviewer answers APPROVE - DevRelay must not interpret it
        stub.prompt_reply = reply("msg_review", "APPROVE")
        reviewed = await session.call_tool(
            "devrelay_run_reviewer", {"run_id": run_id, "prompt": "review it"}
        )
        out["reviewed"] = envelope_of(reviewed)
        out["posts_after_cycle"] = len(posts(stub))
        out["after_reviewer_get"] = envelope_of(
            await session.call_tool("devrelay_get_run", {"run_id": run_id})
        )

        decided = await session.call_tool(
            "devrelay_decide_run", {"run_id": run_id, "decision": "complete"}
        )
        out["decided"] = envelope_of(decided)
        out["posts_final"] = len(posts(stub))
        return out

    observed = run_over_stdio(ws, script)
    assert observed["start"]["state"] == "READY_IMPLEMENTER"
    assert observed["posts_after_start"] == 0, "start_run performs no model call"
    assert observed["implemented"]["ok"] is True
    assert observed["implemented"]["data"]["state"] == "READY_REVIEWER"
    assert observed["reviewed"]["ok"] is True
    assert observed["reviewed"]["data"]["state"] == "AWAITING_DECISION"
    assert observed["posts_after_cycle"] == 2, "one POST per explicit role call"
    assert observed["after_reviewer_get"]["data"]["state"] == "AWAITING_DECISION"
    assert observed["after_reviewer_get"]["data"]["completed_cycles"] == 1
    assert observed["decided"]["data"]["state"] == "COMPLETED"
    assert observed["decided"]["data"]["terminal"] is True
    assert observed["posts_final"] == 2, "the decision spends no model turn"
    assert [item["source"] for item in observed["decided"]["data"]["decision_history"]] == [
        "external_planner"
    ]


def test_stdio_two_cycle_request_changes_flow(fake_opencode, tmp_path):
    ws = make_orchestration_workspace(tmp_path, fake_opencode.base_url)
    stub = two_sessions(fake_opencode, ws)

    async def script(session, _init):
        stub.prompt_reply = reply("msg_i1", "implemented 1")
        start = envelope_of(await session.call_tool("devrelay_start_run", start_args(2)))
        run_id = start["data"]["run_id"]
        states = []
        for cycle in (1, 2):
            stub.prompt_reply = reply(f"msg_i{cycle}", f"implemented {cycle}")
            implemented = envelope_of(
                await session.call_tool(
                    "devrelay_run_implementer", {"run_id": run_id, "prompt": f"impl {cycle}"}
                )
            )
            states.append(implemented["data"]["state"])
            stub.prompt_reply = reply(f"msg_r{cycle}", f"REVIEW {cycle}")
            reviewed = envelope_of(
                await session.call_tool(
                    "devrelay_run_reviewer", {"run_id": run_id, "prompt": f"rev {cycle}"}
                )
            )
            states.append(reviewed["data"]["state"])
            decision = "request_changes" if cycle == 1 else "complete"
            decided = envelope_of(
                await session.call_tool(
                    "devrelay_decide_run", {"run_id": run_id, "decision": decision}
                )
            )
            states.append(decided["data"]["state"])
        final = envelope_of(await session.call_tool("devrelay_get_run", {"run_id": run_id}))
        return {"states": states, "final": final["data"], "posts": len(posts(stub))}

    observed = run_over_stdio(ws, script)
    assert observed["states"] == [
        "READY_REVIEWER",
        "AWAITING_DECISION",
        "READY_IMPLEMENTER",
        "READY_REVIEWER",
        "AWAITING_DECISION",
        "COMPLETED",
    ]
    assert observed["final"]["completed_cycles"] == 2
    assert observed["final"]["max_cycles"] == 2
    assert observed["posts"] == 4, "2 cycles x (1 implementer + 1 reviewer)"


def test_stdio_get_run_is_local_and_terminal_runs_refuse_phases(fake_opencode, tmp_path):
    ws = make_orchestration_workspace(tmp_path, fake_opencode.base_url)
    stub = two_sessions(fake_opencode, ws)

    async def script(session, _init):
        stub.prompt_reply = reply("msg_i", "implemented")
        start = envelope_of(await session.call_tool("devrelay_start_run", start_args(1)))
        run_id = start["data"]["run_id"]
        await session.call_tool(
            "devrelay_run_implementer", {"run_id": run_id, "prompt": "implement it"}
        )
        stub.prompt_reply = reply("msg_r", "no verdict here")
        await session.call_tool(
            "devrelay_run_reviewer", {"run_id": run_id, "prompt": "review it"}
        )
        stopped = envelope_of(
            await session.call_tool("devrelay_decide_run", {"run_id": run_id, "decision": "stop"})
        )
        requests_before = len(stub.requests)
        read = envelope_of(await session.call_tool("devrelay_get_run", {"run_id": run_id}))
        requests_after_read = len(stub.requests)
        refused = await session.call_tool(
            "devrelay_run_implementer", {"run_id": run_id, "prompt": "again"}
        )
        bad_decision = await session.call_tool(
            "devrelay_decide_run", {"run_id": run_id, "decision": "approve"}
        )
        return {
            "stopped": stopped["data"],
            "read": read["data"],
            "requests_before_read": requests_before,
            "requests_after_read": requests_after_read,
            "refused": refused.structured_content,
            "refused_is_error": refused.is_error,
            "bad_decision": bad_decision.structured_content,
            "posts": len(posts(stub)),
        }

    observed = run_over_stdio(ws, script)
    assert observed["stopped"]["state"] == "STOPPED"
    assert observed["read"]["terminal"] is True
    assert observed["requests_after_read"] == observed["requests_before_read"], (
        "get_run performs no OpenCode request"
    )
    assert observed["refused_is_error"] is True
    assert observed["refused"]["error"]["type"] == "orchestration_invalid_transition"
    assert observed["refused"]["data"]["state"] == "STOPPED"
    assert observed["bad_decision"]["error"]["type"] in (
        "mcp_invalid_argument",
        "orchestration_invalid_transition",
    )
    assert observed["posts"] == 2, "refused actions spend no model turn"


def test_stdio_start_run_validates_sessions_and_bounds(fake_opencode, tmp_path):
    ws = make_orchestration_workspace(tmp_path, fake_opencode.base_url)
    stub = two_sessions(fake_opencode, ws)

    async def script(session, _init):
        same = await session.call_tool(
            "devrelay_start_run",
            {
                "implementer_session_id": IMPLEMENTER_SESSION,
                "reviewer_session_id": IMPLEMENTER_SESSION,
                "max_cycles": 1,
            },
        )
        too_many = await session.call_tool("devrelay_start_run", start_args(4))
        missing = await session.call_tool(
            "devrelay_start_run",
            {
                "implementer_session_id": IMPLEMENTER_SESSION,
                "reviewer_session_id": "ses_missing",
                "max_cycles": 1,
            },
        )
        return {
            "same": same.structured_content,
            "too_many": too_many.structured_content,
            "missing": missing.structured_content,
            "posts": len(posts(stub)),
        }

    observed = run_over_stdio(ws, script)
    assert observed["same"]["error"]["type"] == "orchestration_session_conflict"
    assert observed["too_many"]["error"]["type"] == "mcp_invalid_argument"
    assert observed["missing"]["error"]["type"] == "orchestration_session_conflict"
    assert observed["posts"] == 0, "a refused start never performs a model call"
    assert json.dumps(observed["missing"]).find("ses_missing") >= 0


def test_stdio_extra_members_do_not_break_the_phase_contract(fake_opencode, tmp_path):
    ws = make_orchestration_workspace(tmp_path, fake_opencode.base_url)
    stub = two_sessions(fake_opencode, ws)

    async def script(session, _init):
        stub.prompt_reply = reply("msg_i", "implemented")
        start = envelope_of(await session.call_tool("devrelay_start_run", start_args(1)))
        run_id = start["data"]["run_id"]
        result = await session.call_tool(
            "devrelay_run_implementer",
            {
                "run_id": run_id,
                "prompt": "implement it",
                "model": "attacker/model",
                "agent": "attacker-agent",
                "session_id": REVIEWER_SESSION,
            },
        )
        return {
            "envelope": envelope_of(result),
            "wire": stub.prompts[-1] if stub.prompts else None,
            "posts": len(posts(stub)),
        }

    observed = run_over_stdio(ws, script)
    assert observed["envelope"]["ok"] is True
    assert observed["envelope"]["data"]["state"] == "READY_REVIEWER"
    assert observed["wire"]["model"] == {"providerID": "provider-a", "modelID": "model-a"}, (
        "the run's session and configured route always win"
    )
    assert observed["posts"] == 1
