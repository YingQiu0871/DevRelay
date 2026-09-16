"""v0.3-B focused tests: the MCP tool surface (in-process, offline).

Every tool is exercised through the real MCP SDK dispatch
(``MCPServer.call_tool`` -> argument schema -> tool body -> DevRelay envelope)
with the **real accepted v0.3-A bridge** wired to the deterministic OpenCode
stub over ``httpx.MockTransport``.  No process, no HTTP socket, no model, no
network call.

The stdio process/transport boundary has its own suite
(``tests/test_v03b_mcp_stdio.py``).
"""

from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path
from typing import Any

import pytest
import yaml

from devrelay.errors import OpenCodeSessionNotFoundError
from devrelay.mcp.models import MCP_MAX_CALL_LIMIT, MCP_PROMPT_MAX_CHARS
from devrelay.mcp.server import (
    MCP_SERVER_VERSION,
    McpStartupError,
    build_surface,
    create_server,
    resolve_workspace,
)
from devrelay.opencode.accounting import FilesystemOpenCodeLedger

from opencode_stub import DEFAULT_WORKSPACE, StubOpenCodeServer, _message, _session

WS = DEFAULT_WORKSPACE
TOKEN_SENTINEL = "oc-token-MCP-SENTINEL-4711"

FORBIDDEN_TOOL_WORDS = (
    "shell",
    "exec",
    "subprocess",
    "http_request",
    "read_file",
    "write_file",
    "git_",
    "config_edit",
    "delete_session",
    "token",
    "env",
)


# ---------------------------------------------------------------------------
# fixtures / helpers
# ---------------------------------------------------------------------------
def make_workspace(tmp_path: Path, **opencode: Any) -> Path:
    """A minimal initialized DevRelay workspace (configuration only)."""
    ws = tmp_path / "ws"
    (ws / ".devrelay" / "profiles").mkdir(parents=True, exist_ok=True)
    section: dict[str, Any] = {
        "base_url": "http://opencode.invalid",
        "workspace": "",
        "timeout_seconds": 30,
        "idle_timeout_seconds": 10,
        "poll_interval_seconds": 0.01,
        "max_messages": 50,
        "allow_unknown_workspace": False,
    }
    section.update(opencode)
    (ws / ".devrelay" / "config.yaml").write_text(
        yaml.safe_dump({"opencode": section}, sort_keys=False), encoding="utf-8"
    )
    return ws


def envelope_of(result: Any) -> dict[str, Any]:
    assert result.structured_content is not None, (
        "a DevRelay tool result must always carry the structured envelope"
    )
    return result.structured_content


def call(server: Any, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    result = asyncio.run(server.call_tool(name, arguments or {}))
    return envelope_of(result)


def call_result(server: Any, name: str, arguments: dict[str, Any] | None = None) -> Any:
    return asyncio.run(server.call_tool(name, arguments or {}))


def build(
    tmp_path: Path,
    stub: StubOpenCodeServer | None = None,
    *,
    opencode: dict[str, Any] | None = None,
    bridge_factory: Any = None,
    diagnostics: Any = None,
    bind_stub: bool = True,
) -> tuple[Any, StubOpenCodeServer, Path]:
    ws = make_workspace(tmp_path, **(opencode or {}))
    stub = stub or StubOpenCodeServer(workspace=str(ws))
    if bind_stub:
        # Ownership is authoritative: the stub must report the bound workspace
        # (the foreign-workspace test opts out on purpose).
        stub.workspace = str(ws)
        for session in stub.sessions:
            session["directory"] = str(ws)
    if bridge_factory is None:
        ledger = FilesystemOpenCodeLedger(ws / ".devrelay")

        def bridge_factory() -> Any:  # noqa: F811 - injected factory
            return stub.bridge(workspace_root=str(ws), ledger=ledger)

    surface = build_surface(ws, bridge_factory=bridge_factory, diagnostics=diagnostics)
    return create_server(surface, diagnostics=diagnostics), stub, ws


def posts(stub: StubOpenCodeServer) -> list[str]:
    return [path for method, path in stub.requests if method == "POST"]


# ---------------------------------------------------------------------------
# discovery / lifecycle / tool inventory
# ---------------------------------------------------------------------------
def test_tool_inventory_annotations_and_descriptions(tmp_path):
    server, _stub, _ws = build(tmp_path)
    tools = asyncio.run(server.list_tools())
    names = [tool.name for tool in tools]
    assert names == [
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
    by_name = {tool.name: tool for tool in tools}
    for name in (
        "devrelay_status",
        "opencode_health",
        "opencode_list_sessions",
        "opencode_get_session",
        "opencode_read_messages",
        "opencode_calls",
        "opencode_wait_idle",
    ):
        assert by_name[name].annotations.read_only_hint is True, name
    send = by_name["opencode_send_prompt"].annotations
    assert send.read_only_hint is False
    assert send.idempotent_hint is False, "send_prompt must never claim idempotency"
    interrupt = by_name["opencode_interrupt"].annotations
    assert interrupt.read_only_hint is False
    assert interrupt.destructive_hint is True

    description = by_name["opencode_send_prompt"].description or ""
    for phrase in (
        "exactly ONE",
        "never retries",
        "submission_uncertain",
        "reply_pending",
        "do NOT resubmit",
        "retry_safe",
    ):
        assert phrase in description, phrase
    wait_description = by_name["opencode_wait_idle"].description or ""
    assert "never sends a prompt" in wait_description
    interrupt_description = by_name["opencode_interrupt"].description or ""
    assert "NOT" in interrupt_description and "interrupt_verified" in interrupt_description


def test_no_dangerous_low_level_tools(tmp_path):
    server, _stub, _ws = build(tmp_path)
    names = [tool.name.lower() for tool in asyncio.run(server.list_tools())]
    for name in names:
        for word in FORBIDDEN_TOOL_WORDS:
            assert word not in name, (name, word)


def test_no_tool_accepts_a_workspace_path(tmp_path):
    server, _stub, _ws = build(tmp_path)
    for tool in asyncio.run(server.list_tools()):
        properties = set((tool.input_schema.get("properties") or {}))
        for forbidden in ("workspace", "cwd", "directory", "path", "root"):
            assert forbidden not in properties, (tool.name, forbidden)


def test_no_acceptance_authority_surface(tmp_path):
    server, _stub, _ws = build(tmp_path)
    status = call(server, "devrelay_status")
    assert status["data"]["acceptance_authority"] is False
    text = json.dumps(status).lower()
    for word in ("approved", "review passed", "ready to merge", "accepted_implementation"):
        assert word not in text
    for tool in asyncio.run(server.list_tools()):
        assert "approve" not in tool.name and "accept" not in tool.name


def test_server_identity_and_schema_version(tmp_path):
    server, _stub, _ws = build(tmp_path)
    status = call(server, "devrelay_status")
    assert status["schema_version"] == 1
    assert status["tool"] == "devrelay_status"
    assert status["error"] is None
    assert status["data"]["mcp"]["server_version"] == MCP_SERVER_VERSION
    assert status["data"]["mcp"]["transport"] == "stdio"
    assert status["data"]["mcp"]["side_effects_serialized"] is True


# ---------------------------------------------------------------------------
# bound workspace
# ---------------------------------------------------------------------------
def test_workspace_is_resolved_and_bound(tmp_path):
    ws = make_workspace(tmp_path)
    root, wiring, devrelay_dir = resolve_workspace(ws)
    assert root == ws.resolve()
    assert devrelay_dir == ws.resolve() / ".devrelay"
    assert wiring.opencode.base_url == "http://opencode.invalid"


def test_invalid_workspace_refuses_startup(tmp_path):
    with pytest.raises(McpStartupError):
        resolve_workspace("")
    with pytest.raises(McpStartupError):
        resolve_workspace(tmp_path / "does-not-exist")
    plain = tmp_path / "plain"
    plain.mkdir()
    with pytest.raises(McpStartupError):
        resolve_workspace(plain)

    broken = tmp_path / "broken"
    (broken / ".devrelay").mkdir(parents=True)
    (broken / ".devrelay" / "config.yaml").write_text(
        "opencode:\n  base_url: http://user:secret@host:1\n", encoding="utf-8"
    )
    with pytest.raises(McpStartupError) as excinfo:
        resolve_workspace(broken)
    assert "secret" not in str(excinfo.value)


def test_foreign_session_is_hidden_and_fails_closed(tmp_path):
    foreign = StubOpenCodeServer(
        workspace="C:/elsewhere",
        sessions=[_session("ses_foreign", workspace="C:/elsewhere")],
    )
    server, stub, _ws = build(tmp_path, foreign, bind_stub=False)
    listed = call(server, "opencode_list_sessions")
    assert listed["ok"] is True
    assert listed["data"]["sessions"] == []

    with_others = call(server, "opencode_list_sessions", {"include_other_workspaces": True})
    assert [s["session_id"] for s in with_others["data"]["sessions"]] == ["ses_foreign"]

    shown = call(server, "opencode_get_session", {"session_id": "ses_foreign"})
    assert shown["ok"] is False
    assert shown["error"]["type"] == "opencode_session_workspace_mismatch"
    assert shown["error"]["message"]
    assert stub.requests  # the probe was made; the verdict is honest


# ---------------------------------------------------------------------------
# read-only tools
# ---------------------------------------------------------------------------
def test_status_sanitizes_endpoint_and_never_returns_tokens(tmp_path, monkeypatch):
    from devrelay.mcp.tools import _endpoint_authority

    monkeypatch.setenv("DEVRELAY_OPENCODE_TOKEN", TOKEN_SENTINEL)
    server, _stub, _ws = build(
        tmp_path, opencode={"base_url": "http://127.0.0.1:4096"}
    )
    status = call(server, "devrelay_status")
    assert status["ok"] is True
    data = status["data"]
    assert data["workspace"]
    assert data["opencode"]["endpoint_authority"] == "http://127.0.0.1:4096"
    assert data["opencode"]["configured"] is True
    assert data["opencode"]["token_source"].startswith("DEVRELAY_OPENCODE_TOKEN")
    assert TOKEN_SENTINEL not in json.dumps(status)
    # the authority projection itself strips credentials/path/query
    assert (
        _endpoint_authority("http://user:secret@host.example:8443/api?x=1#frag")
        == "http://host.example:8443"
    )
    assert _endpoint_authority("") == ""


def test_health_ok_and_provider_failure(tmp_path):
    server, _stub, _ws = build(tmp_path)
    good = call(server, "opencode_health")
    assert good["ok"] is True
    assert good["data"]["health"]["healthy"] is True
    assert good["data"]["call_ids"]

    unreachable = StubOpenCodeServer(unreachable=True)
    bad_server, _stub2, _ws2 = build(tmp_path / "unreachable", unreachable)
    bad = call(bad_server, "opencode_health")
    assert bad["ok"] is False
    assert bad["error"]["type"] == "connect_error"
    assert bad["data"]["state"] == "PROVIDER_UNAVAILABLE"


def test_get_session_returns_normalized_session(tmp_path):
    server, stub, _ws = build(tmp_path)
    result = call(server, "opencode_get_session", {"session_id": "ses_match"})
    assert result["ok"] is True
    session = result["data"]["session"]
    assert session["session_id"] == "ses_match"
    assert session["workspace_match"] is True
    assert "directory" not in session and "parts" not in session


def test_read_messages_exposes_page_semantics(tmp_path):
    messages = [_message(f"msg_{i:02d}", "user" if i % 2 else "assistant", f"t{i}") for i in range(1, 61)]
    server, _stub, _ws = build(tmp_path, StubOpenCodeServer(messages=messages))
    result = call(server, "opencode_read_messages", {"session_id": "ses_match"})
    assert result["ok"] is True
    page = result["data"]["page"]
    assert set(page) >= {
        "next_cursor",
        "provider_message_count",
        "window_truncated",
        "cursor_unknown",
        "replayed",
        "hard_max_messages",
    }
    assert page["provider_message_count"] == 60
    assert page["window_truncated"] is True
    assert len(result["data"]["messages"]) == 50
    message = result["data"]["messages"][0]
    assert set(message) == {"message_id", "role", "created_at", "parts"}
    assert "info" not in json.dumps(result["data"])

    tail = call(
        server,
        "opencode_read_messages",
        {"session_id": "ses_match", "cursor": result["data"]["messages"][-1]["message_id"]},
    )
    assert tail["ok"] is True
    assert tail["data"]["messages"] == []
    assert tail["data"]["page"]["replayed"] is True


def test_calls_ledger_is_readable_and_reports_corruption(tmp_path):
    server, _stub, ws = build(tmp_path)
    call(server, "opencode_health")
    result = call(server, "opencode_calls", {"limit": 10})
    assert result["ok"] is True
    assert result["data"]["count"] == 1
    record = result["data"]["records"][0]
    assert record["operation"] == "health"
    assert record["state"] == "COMPLETED"
    assert record["completed_at"]
    assert result["data"]["sequence"]["present"] is True

    calls_dir = ws / ".devrelay" / "opencode" / "calls"
    (calls_dir / "OC-0009.json").write_text("{not json", encoding="utf-8")
    corrupted = call(server, "opencode_calls", {"limit": 10})
    assert corrupted["ok"] is False
    assert corrupted["error"]["type"] == "opencode_ledger_error"
    assert "unreadable" in corrupted["error"]["message"] or "refusing" in corrupted["error"]["message"]


def test_calls_reports_a_corrupt_sequence(tmp_path):
    server, _stub, ws = build(tmp_path)
    call(server, "opencode_health")
    (ws / ".devrelay" / "opencode" / "sequence.json").write_text("[]", encoding="utf-8")
    result = call(server, "opencode_calls")
    assert result["ok"] is False
    assert result["error"]["type"] == "opencode_ledger_error"


# ---------------------------------------------------------------------------
# opencode_send_prompt: v0.3-A semantics preserved through MCP
# ---------------------------------------------------------------------------
def real_reply(message_id: str = "msg_assistant_new", text: str = "DEVRELAY_A33_OK") -> dict[str, Any]:
    return {
        "info": {
            "id": message_id,
            "sessionID": "ses_match",
            "role": "assistant",
            "time": {"created": 1_789_554_011_423},
        },
        "parts": [
            {
                "id": "prt_1",
                "sessionID": "ses_match",
                "messageID": message_id,
                "type": "text",
                "text": text,
            }
        ],
    }


def test_send_prompt_success_preserves_full_evidence(tmp_path):
    server, stub, _ws = build(tmp_path, StubOpenCodeServer(prompt_reply=real_reply()))
    result = call(
        server,
        "opencode_send_prompt",
        {"session_id": "ses_match", "prompt": "hello"},
    )
    assert result["ok"] is True
    assert posts(stub) == ["/session/ses_match/message"]
    data = result["data"]
    for field in (
        "operation",
        "state",
        "call_ids",
        "request_count",
        "submission_attempted",
        "submission_status",
        "submission_uncertain",
        "reply_pending",
        "reply_boundary",
        "messages",
        "error_type",
        "error",
        "retry_safe",
    ):
        assert field in data, field
    assert data["operation"] == "send_prompt"
    assert data["state"] == "COMPLETED"
    assert data["reply_pending"] is False
    assert data["submission_uncertain"] is False
    assert data["submission_status"] == 200
    assert data["request_count"] == 4
    assert data["retry_safe"] is False
    assert [m["message_id"] for m in data["messages"]] == ["msg_assistant_new"]
    assert data["messages"][0]["parts"][-1]["text"] == "DEVRELAY_A33_OK"


@pytest.mark.parametrize("failure", ["read_timeout", "write_timeout"])
def test_send_prompt_timeout_is_uncertain_and_never_retryable(tmp_path, failure):
    server, stub, _ws = build(tmp_path, StubOpenCodeServer(prompt_exception=failure))
    result = call(
        server, "opencode_send_prompt", {"session_id": "ses_match", "prompt": "hello"}
    )
    assert result["ok"] is False
    assert result["error"]["type"] == failure
    data = result["data"]
    assert data["submission_uncertain"] is True
    assert data["reply_pending"] is True
    assert data["retry_safe"] is False
    assert data["messages"] == []
    assert posts(stub) == ["/session/ses_match/message"], "exactly one attempt, no retry"
    assert "hi there" not in json.dumps(result)


def test_send_prompt_connect_failure_is_definitely_not_submitted(tmp_path):
    server, stub, _ws = build(tmp_path, StubOpenCodeServer(prompt_exception="connect_error"))
    result = call(
        server, "opencode_send_prompt", {"session_id": "ses_match", "prompt": "hello"}
    )
    assert result["ok"] is False
    assert result["error"]["type"] == "connect_error"
    data = result["data"]
    assert data["submission_attempted"] is True
    assert data["submission_uncertain"] is False
    assert data["reply_pending"] is False
    assert data["retry_safe"] is True, "nothing was submitted, so a retry cannot duplicate"
    assert posts(stub) == ["/session/ses_match/message"]


def test_send_prompt_html_fallback_is_uncertain(tmp_path):
    server, stub, _ws = build(tmp_path, StubOpenCodeServer(prompt_html_fallback=True))
    result = call(
        server, "opencode_send_prompt", {"session_id": "ses_match", "prompt": "hello"}
    )
    assert result["ok"] is False
    data = result["data"]
    assert data["submission_uncertain"] is True
    assert data["submission_contract"] == "unexpected_media_type:text/html"
    assert data["reply_pending"] is True
    assert data["retry_safe"] is False
    assert len(posts(stub)) == 1


def test_send_prompt_rejected_status_is_not_retry_safe(tmp_path):
    server, stub, _ws = build(
        tmp_path,
        StubOpenCodeServer(prompt_http_status=500, prompt_error_body='{"error":"boom"}'),
    )
    result = call(
        server, "opencode_send_prompt", {"session_id": "ses_match", "prompt": "hello"}
    )
    assert result["ok"] is False
    data = result["data"]
    assert data["submission_status"] == 500
    assert data["submission_uncertain"] is False
    assert data["reply_pending"] is False
    assert data["retry_safe"] is False, "the server saw the POST: a retry could duplicate"
    assert len(posts(stub)) == 1


def test_send_prompt_pending_never_substitutes_a_stale_reply(tmp_path):
    server, stub, _ws = build(
        tmp_path, StubOpenCodeServer(prompt_raw_reply={"ok": True})
    )
    result = call(
        server, "opencode_send_prompt", {"session_id": "ses_match", "prompt": "hello"}
    )
    assert result["ok"] is False
    assert result["data"]["reply_pending"] is True
    assert result["data"]["messages"] == []
    assert result["data"]["retry_safe"] is False
    assert "hi there" not in json.dumps(result)
    assert len(posts(stub)) == 1


def test_send_prompt_model_override_uses_the_accepted_grammar(tmp_path):
    server, stub, _ws = build(tmp_path, StubOpenCodeServer(prompt_reply=real_reply()))
    result = call(
        server,
        "opencode_send_prompt",
        {
            "session_id": "ses_match",
            "prompt": "hello",
            "agent": "build",
            "model": "opencode-go/deepseek-v4.1-flash",
        },
    )
    assert result["ok"] is True
    assert stub.prompts[0]["model"] == {
        "providerID": "opencode-go",
        "modelID": "deepseek-v4.1-flash",
    }
    assert stub.prompts[0]["agent"] == "build"

    bad_server, bad_stub, _ws2 = build(tmp_path / "bad-model")
    bad = call(
        bad_server,
        "opencode_send_prompt",
        {"session_id": "ses_match", "prompt": "hello", "model": "glm-4.6"},
    )
    assert bad["ok"] is False
    assert bad["error"]["type"] == "mcp_invalid_argument"
    assert bad_stub.requests == [], "an unmappable model must fail before any request"


def test_send_prompt_prompt_never_reaches_durable_artifacts(tmp_path):
    server, _stub, ws = build(tmp_path, StubOpenCodeServer(prompt_http_status=500))
    prompt = "MCP-SECRET-PROMPT-do-not-persist-4711"
    result = call(
        server, "opencode_send_prompt", {"session_id": "ses_match", "prompt": prompt}
    )
    assert prompt not in json.dumps(result), "the send result must not echo the prompt"
    for path in (ws / ".devrelay").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            assert prompt not in text, path
    records = call(server, "opencode_calls")["data"]["records"]
    post = [r for r in records if r["method"] == "POST"]
    assert len(post) == 1
    assert post[0]["prompt_chars"] == len(prompt)
    assert post[0]["prompt_sha256"]


# ---------------------------------------------------------------------------
# wait / interrupt
# ---------------------------------------------------------------------------
def test_wait_idle_states_through_mcp(tmp_path):
    from opencode_stub import StubOpenCodeServer as Stub

    idle_server, _s1, _w1 = build(
        tmp_path / "idle", Stub(status_map={"ses_match": {"type": "idle"}})
    )
    idle = call(idle_server, "opencode_wait_idle", {"session_id": "ses_match"})
    assert idle["ok"] is True
    assert idle["data"]["state"] == "COMPLETED"

    busy_server, _s2, _w2 = build(
        tmp_path / "busy",
        Stub(
            status_sequence=[
                {"ses_match": {"type": "busy"}},
                {"ses_match": {"type": "retry", "attempt": 2, "message": "slow", "next": 100}},
                {},
            ]
        ),
    )
    busy = call(busy_server, "opencode_wait_idle", {"session_id": "ses_match"})
    assert busy["ok"] is True
    assert "retry attempt 2" in busy["data"]["status_detail"]

    timeout_server, _s3, _w3 = build(
        tmp_path / "timeout",
        Stub(status_map={"ses_match": {"type": "busy"}}),
        opencode={"idle_timeout_seconds": 1},
    )
    timed = call(
        timeout_server,
        "opencode_wait_idle",
        {"session_id": "ses_match", "timeout_seconds": 0.5},
    )
    assert timed["ok"] is False
    assert timed["error"]["type"] == "idle_timeout"
    assert timed["data"]["state"] == "TIMED_OUT"


def test_wait_idle_timeout_bounds_are_enforced(tmp_path):
    server, _stub, _ws = build(tmp_path, opencode={"idle_timeout_seconds": 5})
    # Note (verified SDK behaviour, mcp 2.2.0): a JSON boolean arriving for the
    # numeric `timeout_seconds` field is coerced to 1.0/0.0 by the advertised
    # schema before DevRelay sees it; that is a finite in-bounds wait, so the
    # safety property (never unlimited, always finite) still holds.
    for bad in (0, -1, 5.5, 10_000, float("inf"), "10"):
        result = call(
            server,
            "opencode_wait_idle",
            {"session_id": "ses_match", "timeout_seconds": bad},
        )
        assert result["ok"] is False, bad
        assert result["error"]["type"] == "mcp_invalid_argument", bad


def test_interrupt_variants_through_mcp(tmp_path):
    ok_server, _s1, _w1 = build(
        tmp_path / "i1", StubOpenCodeServer(abort_status=204)
    )
    accepted = call(ok_server, "opencode_interrupt", {"session_id": "ses_match"})
    assert accepted["ok"] is True
    assert accepted["data"]["state"] == "INTERRUPTED"
    assert accepted["data"]["interrupt_verified"] is False
    assert "not a verified terminal state" in accepted["data"]["interrupt_semantics"]

    unsupported_server, _s2, _w2 = build(
        tmp_path / "i2", StubOpenCodeServer(abort_status=405)
    )
    unsupported = call(unsupported_server, "opencode_interrupt", {"session_id": "ses_match"})
    assert unsupported["ok"] is False
    assert unsupported["error"]["type"] == "interrupt_unsupported"
    assert unsupported["data"]["interrupt_verified"] is False

    vanished_server, _s3, _w3 = build(
        tmp_path / "i3",
        StubOpenCodeServer(abort_status=404, abort_removes_session=True),
    )
    vanished = call(vanished_server, "opencode_interrupt", {"session_id": "ses_match"})
    assert vanished["ok"] is False
    assert vanished["error"]["type"] == "interrupt_session_not_found"

    down_server, _s4, _w4 = build(
        tmp_path / "i4", StubOpenCodeServer(abort_status=500, abort_body='{"error":"x"}')
    )
    down = call(down_server, "opencode_interrupt", {"session_id": "ses_match"})
    assert down["ok"] is False
    assert down["error"]["type"] == "http_status"


# ---------------------------------------------------------------------------
# argument validation (all of it DevRelay-side, before any bridge call)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "name,arguments",
    [
        ("opencode_get_session", {}),
        ("opencode_get_session", {"session_id": "bad id!"}),
        ("opencode_get_session", {"session_id": "."}),
        ("opencode_read_messages", {"cursor": "x"}),
        ("opencode_send_prompt", {"session_id": "ses_match", "prompt": "   "}),
        ("opencode_send_prompt", {"session_id": "ses_match", "prompt": "x" * (MCP_PROMPT_MAX_CHARS + 1)}),
        ("opencode_send_prompt", {"session_id": "ses_match", "prompt": "hi", "model": "nope"}),
        ("opencode_send_prompt", {"session_id": "ses_match", "prompt": "hi", "agent": "a" * 200}),
        ("opencode_calls", {"limit": MCP_MAX_CALL_LIMIT + 1}),
        ("opencode_calls", {"limit": 0}),
        ("opencode_wait_idle", {"session_id": "ses_match", "timeout_seconds": 10_000}),
    ],
)
def test_argument_validation_produces_envelopes_and_zero_requests(
    tmp_path, name, arguments
):
    server, stub, _ws = build(tmp_path)
    result = call(server, name, arguments)
    assert result["ok"] is False, (name, arguments)
    assert result["error"]["type"] == "mcp_invalid_argument"
    assert result["error"]["message"]
    assert result["schema_version"] == 1
    assert stub.requests == [], "validation must happen before any bridge request"


def test_cursor_is_bounded(tmp_path):
    server, stub, _ws = build(tmp_path)
    result = call(
        server, "opencode_read_messages", {"session_id": "ses_match", "cursor": "c" * 300}
    )
    assert result["ok"] is False
    assert result["error"]["type"] == "mcp_invalid_argument"
    assert stub.requests == []


# ---------------------------------------------------------------------------
# error boundary
# ---------------------------------------------------------------------------
class _RaisingBridge:
    """Fake bridge that always raises - for the error-boundary tests."""

    def __init__(self, exc: BaseException) -> None:
        self.exc = exc
        self.calls = 0

    def _raise(self, *args: Any, **kwargs: Any) -> Any:
        self.calls += 1
        raise self.exc

    def health(self, *args: Any, **kwargs: Any) -> Any:
        return self._raise()

    def list_sessions(self, *args: Any, **kwargs: Any) -> Any:
        return self._raise()

    def get_session(self, *args: Any, **kwargs: Any) -> Any:
        return self._raise()

    def read_messages(self, *args: Any, **kwargs: Any) -> Any:
        return self._raise()

    def send_prompt(self, *args: Any, **kwargs: Any) -> Any:
        return self._raise()

    def wait_idle(self, *args: Any, **kwargs: Any) -> Any:
        return self._raise()

    def interrupt(self, *args: Any, **kwargs: Any) -> Any:
        return self._raise()


def test_devrelay_errors_keep_their_stable_code(tmp_path):
    bridge = _RaisingBridge(OpenCodeSessionNotFoundError("session ses_x does not exist"))
    server, _stub, _ws = build(tmp_path, bridge_factory=lambda: bridge)
    result = call(server, "opencode_get_session", {"session_id": "ses_x"})
    assert result["ok"] is False
    assert result["error"]["type"] == "opencode_session_not_found"
    assert "ses_x" in result["error"]["message"]


def test_unexpected_exception_is_generic_and_diagnosed(tmp_path):
    diagnostics: list[str] = []
    bridge = _RaisingBridge(RuntimeError("boom at C:\\Users\\secret\\path with sk-abc123"))
    server, _stub, _ws = build(
        tmp_path, bridge_factory=lambda: bridge, diagnostics=diagnostics.append
    )
    result = call(server, "opencode_health")
    assert result["ok"] is False
    assert result["error"]["type"] == "internal_error"
    assert "Traceback" not in json.dumps(result)
    assert "sk-abc123" not in json.dumps(result)
    assert "C:\\Users" not in json.dumps(result)
    assert diagnostics, "an unexpected internal error must be diagnosed on stderr"
    assert any("RuntimeError" in line for line in diagnostics)
    assert "sk-abc123" not in "".join(diagnostics)


def test_sdk_schema_boundary_is_bounded_and_leakless(tmp_path):
    """A JSON type the SDK's own schema rejects must not leak a traceback.

    Verified SDK fact (mcp 2.2.0): ``MCPServer`` validates the advertised input
    schema before the tool body runs and converts the failure into an
    ``isError`` result.  DevRelay cannot shape that message, so the contract is:
    bounded validation text, no traceback, no secrets, no envelope confusion -
    while every *semantic* problem a schema cannot express is validated by
    DevRelay itself and returns the envelope (previous test).
    """
    server, stub, _ws = build(tmp_path)
    with pytest.raises(Exception) as excinfo:
        asyncio.run(
            server.call_tool(
                "opencode_send_prompt", {"session_id": "ses_match", "prompt": 12345}
            )
        )
    message = str(excinfo.value)
    assert "Traceback" not in message
    assert "sk-" not in message
    assert "C:\\" not in message
    assert stub.requests == []


# ---------------------------------------------------------------------------
# concurrency + cancellation boundaries
# ---------------------------------------------------------------------------
class _ConcurrencyProbeBridge:
    """Fake bridge that records overlap between side-effecting submissions."""

    def __init__(self) -> None:
        self.active = 0
        self.max_active = 0
        self.submissions = 0
        self.started = threading.Event()
        self.release = threading.Event()
        self.gate = threading.Event()

    def send_prompt(self, session_id: str, prompt: str, *, agent: str = "", model: str = "") -> Any:
        from devrelay.opencode.models import OpenCodeOperationResult, OpenCodeOperationState

        self.submissions += 1
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        self.started.set()
        if self.submissions == 1:
            self.gate.wait(timeout=5)
        self.active -= 1
        return OpenCodeOperationResult(
            operation="send_prompt",
            state=OpenCodeOperationState.COMPLETED,
            session_id=session_id,
            call_ids=[f"FAKE-{self.submissions}"],
            request_count=1,
            submission_attempted=True,
            submission_status=200,
        )

    def interrupt(self, session_id: str) -> Any:
        return self.send_prompt(session_id, "")


def test_side_effecting_tools_serialize_per_process(tmp_path):
    bridge = _ConcurrencyProbeBridge()
    server, _stub, _ws = build(tmp_path, bridge_factory=lambda: bridge)

    async def run_two() -> list[Any]:
        first = asyncio.create_task(
            server.call_tool(
                "opencode_send_prompt", {"session_id": "ses_match", "prompt": "one"}
            )
        )
        while not bridge.started.is_set():
            await asyncio.sleep(0.01)
        second = asyncio.create_task(
            server.call_tool(
                "opencode_send_prompt", {"session_id": "ses_match", "prompt": "two"}
            )
        )
        await asyncio.sleep(0.1)
        overlap_while_first_held = bridge.max_active
        bridge.gate.set()
        return [await first, await second], overlap_while_first_held

    results, overlap = asyncio.run(run_two())
    assert overlap == 1, "a second submission must not overlap the first"
    assert bridge.max_active == 1
    assert bridge.submissions == 2
    assert all(envelope_of(r)["ok"] is True for r in results)


def test_cancellation_preserves_evidence_and_never_claims_safe_retry(tmp_path):
    """A cancelled MCP call must not look like "the prompt was never submitted"."""
    bridge = _ConcurrencyProbeBridge()
    issued: list[str] = []
    original = bridge.send_prompt

    def recording_send(session_id: str, prompt: str, **kwargs: Any) -> Any:
        issued.append(session_id)
        return original(session_id, prompt, **kwargs)

    bridge.send_prompt = recording_send  # type: ignore[method-assign]
    server, _stub, _ws = build(tmp_path, bridge_factory=lambda: bridge)

    async def run_and_cancel() -> str:
        task = asyncio.create_task(
            server.call_tool(
                "opencode_send_prompt", {"session_id": "ses_match", "prompt": "one"}
            )
        )
        while not bridge.started.is_set():
            await asyncio.sleep(0.01)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            return "cancelled"
        return "completed"

    outcome = asyncio.run(run_and_cancel())
    assert outcome == "cancelled"
    assert issued == ["ses_match"], "the submission had already been issued"
    bridge.gate.set()
    # No envelope was delivered for the cancelled call, so the ONLY truthful
    # statement available to a client is "the submission was already issued" -
    # never "not submitted", and never "safe to retry".
    for envelope in (call(server, "devrelay_status"),):
        assert envelope["ok"] is True


# ---------------------------------------------------------------------------
# secret containment across the boundary
# ---------------------------------------------------------------------------
def test_no_credential_leakage_in_any_tool_envelope(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVRELAY_OPENCODE_TOKEN", TOKEN_SENTINEL)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-should-never-appear")
    diagnostics: list[str] = []
    server, _stub, _ws = build(
        tmp_path,
        StubOpenCodeServer(prompt_http_status=500, prompt_error_body='{"error":"Bearer leaked"}'),
        diagnostics=diagnostics.append,
    )
    payloads = [
        json.dumps(call(server, "devrelay_status")),
        json.dumps(call(server, "opencode_health")),
        json.dumps(call(server, "opencode_calls")),
        json.dumps(
            call(server, "opencode_send_prompt", {"session_id": "ses_match", "prompt": "hi"})
        ),
    ]
    joined = "\n".join(payloads) + "\n".join(diagnostics)
    assert TOKEN_SENTINEL not in joined
    assert "sk-should-never-appear" not in joined
    assert "Authorization" not in joined
