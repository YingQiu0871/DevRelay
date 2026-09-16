"""v0.3-B stdio integration harness: real MCP client <-> real server process.

This suite launches the actual ``devrelay mcp serve`` process and speaks the MCP
protocol to it over stdin/stdout (official ``mcp`` SDK client), with the bridge
talking to a deterministic **loopback fake** OpenCode HTTP server that reuses the
accepted v0.3-A stub routing.  It therefore verifies what an in-process test
cannot:

* stdout carries MCP protocol traffic only (no banners, no logs);
* diagnostics go to stderr;
* tool registration / argument schema / result serialization over the wire;
* lifecycle: multiple sequential calls, clean exit on EOF;
* startup refusal for an invalid workspace, before any tool is served.

No external network and no model call: the fake server binds an ephemeral
loopback port inside the test process.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator

import httpx
import pytest
import yaml

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from opencode_stub import StubOpenCodeServer

EXACT_TOOLS = [
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
TOKEN_SENTINEL = "oc-token-STDIO-SENTINEL-4711"
PROMPT = "Reply with exactly DEVRELAY_A33_OK."


# ---------------------------------------------------------------------------
# deterministic loopback fake OpenCode server
# ---------------------------------------------------------------------------
class _FakeOpenCodeServer:
    """Threaded loopback HTTP server reusing the accepted v0.3-A stub routing."""

    def __init__(self, stub: StubOpenCodeServer) -> None:
        self.stub = stub
        handler = self._make_handler()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def _make_handler(self) -> type[BaseHTTPRequestHandler]:
        stub = self.stub

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def _dispatch(self) -> None:  # noqa: N802 - http.server API
                length = int(self.headers.get("content-length") or 0)
                body = self.rfile.read(length) if length else b""
                request = httpx.Request(
                    self.command,
                    "http://127.0.0.1" + self.path,
                    headers={k: v for k, v in self.headers.items()},
                    content=body,
                )
                try:
                    response = stub.handler(request)
                    status, payload = response.status_code, response.content
                    extra = {
                        k: v
                        for k, v in response.headers.items()
                        if k.lower() not in ("content-length", "transfer-encoding")
                    }
                except Exception as exc:  # stub failure modes -> honest HTTP 500
                    status = 500
                    payload = json.dumps({"error": type(exc).__name__}).encode()
                    extra = {"content-type": "application/json"}
                self.send_response(status)
                for key, value in extra.items():
                    self.send_header(key, value)
                self.send_header("content-length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = _dispatch
            do_POST = _dispatch
            do_DELETE = _dispatch

            def log_message(self, *args: Any) -> None:  # keep test output clean
                return

        return Handler

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)


@pytest.fixture()
def fake_opencode() -> Iterator[_FakeOpenCodeServer]:
    stub = StubOpenCodeServer(prompt_reply=None)
    server = _FakeOpenCodeServer(stub)
    try:
        yield server
    finally:
        server.close()


def make_workspace(tmp_path: Path, base_url: str) -> Path:
    ws = tmp_path / "ws"
    (ws / ".devrelay" / "profiles").mkdir(parents=True, exist_ok=True)
    (ws / ".devrelay" / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "opencode": {
                    "base_url": base_url,
                    "workspace": "",
                    "timeout_seconds": 30,
                    "idle_timeout_seconds": 10,
                    "poll_interval_seconds": 0.01,
                    "max_messages": 50,
                    "allow_unknown_workspace": False,
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return ws


def server_params(ws: Path, *, env: dict[str, str] | None = None) -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "devrelay", "mcp", "serve", "--workspace", str(ws)],
        cwd=str(ws),
        env=env,
    )


def envelope_of(result: Any) -> dict[str, Any]:
    assert result.structured_content is not None
    return result.structured_content


# ---------------------------------------------------------------------------
# discovery / protocol cleanliness / lifecycle
# ---------------------------------------------------------------------------
def test_stdio_initialize_discovery_and_sequential_calls(tmp_path, fake_opencode):
    ws = make_workspace(tmp_path, fake_opencode.base_url)
    fake_opencode.stub.workspace = str(ws)
    for session in fake_opencode.stub.sessions:
        session["directory"] = str(ws)

    async def run() -> tuple[Any, list[str], dict[str, Any], dict[str, Any], dict[str, Any]]:
        async with stdio_client(server_params(ws)) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                tools = await session.list_tools()
                status = envelope_of(await session.call_tool("devrelay_status", {}))
                health = envelope_of(await session.call_tool("opencode_health", {}))
                calls = envelope_of(await session.call_tool("opencode_calls", {}))
                return init, [t.name for t in tools.tools], status, health, calls

    init, names, status, health, calls = asyncio.run(run())
    assert init.server_info.name == "devrelay"
    assert names == EXACT_TOOLS
    assert status["ok"] is True
    assert status["data"]["workspace"] == str(ws.resolve())
    assert status["data"]["opencode"]["endpoint_authority"] == fake_opencode.base_url
    assert health["ok"] is True
    assert health["data"]["health"]["healthy"] is True
    assert calls["ok"] is True
    assert calls["data"]["count"] == 1  # the health call, accounted durably


def test_stdio_stdout_is_protocol_only(tmp_path):
    """No banner/log may reach stdout: with stdin closed the child emits none."""
    ws = make_workspace(tmp_path, "http://127.0.0.1:9")
    proc = subprocess.run(
        [sys.executable, "-m", "devrelay", "mcp", "serve", "--workspace", str(ws)],
        cwd=str(ws),
        input=b"",
        capture_output=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    assert proc.stdout == b"", "stdout must stay clean for the MCP transport"
    assert b"serving MCP over stdio" in proc.stderr


def test_stdio_reports_errors_as_envelopes_without_tracebacks(tmp_path, fake_opencode):
    ws = make_workspace(tmp_path, fake_opencode.base_url)
    fake_opencode.stub.workspace = str(ws)
    for session in fake_opencode.stub.sessions:
        session["directory"] = str(ws)

    async def run() -> tuple[Any, Any, Any]:
        async with stdio_client(server_params(ws)) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                semantic = await session.call_tool(
                    "opencode_get_session", {"session_id": "bad id!"}
                )
                schema = None
                try:
                    schema = await session.call_tool(
                        "opencode_send_prompt", {"session_id": "ses_match", "prompt": 5}
                    )
                except Exception as exc:  # SDK-level schema rejection
                    schema = exc
                unknown = None
                try:
                    unknown = await session.call_tool("opencode_nope", {})
                except Exception as exc:
                    unknown = exc
                return semantic, schema, unknown

    semantic, schema, unknown = asyncio.run(run())
    envelope = envelope_of(semantic)
    assert semantic.is_error is True
    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "mcp_invalid_argument"
    assert "Traceback" not in json.dumps(envelope)
    for other in (schema, unknown):
        text = json.dumps(other.structured_content) if getattr(other, "structured_content", None) else str(other)
        assert "Traceback" not in text
        assert "File \"" not in text


def test_stdio_send_prompt_end_to_end_against_the_loopback_fake(tmp_path, fake_opencode):
    ws = make_workspace(tmp_path, fake_opencode.base_url)
    stub = fake_opencode.stub
    stub.workspace = str(ws)
    for session in stub.sessions:
        session["directory"] = str(ws)
    env = {
        **{k: v for k, v in os.environ.items() if not k.startswith("DEVRELAY_")},
        "DEVRELAY_OPENCODE_TOKEN": TOKEN_SENTINEL,
    }
    env.pop("PYTHONPATH", None)

    async def run() -> dict[str, Any]:
        async with stdio_client(server_params(ws, env=env)) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "opencode_send_prompt",
                    {"session_id": "ses_match", "prompt": PROMPT, "model": "opencode-go/deepseek-v4.1-flash"},
                )
                return envelope_of(result)

    envelope = asyncio.run(run())
    assert envelope["ok"] is True, json.dumps(envelope)[:400]
    data = envelope["data"]
    assert data["state"] == "COMPLETED"
    assert data["submission_status"] == 200
    assert data["submission_uncertain"] is False
    assert data["reply_pending"] is False
    assert data["retry_safe"] is False
    assert data["messages"][0]["role"] == "assistant"
    assert data["messages"][0]["parts"][-1]["text"] == "echo: " + PROMPT
    assert stub.prompts[0]["model"] == {
        "providerID": "opencode-go",
        "modelID": "deepseek-v4.1-flash",
    }
    posts = [p for m, p in stub.requests if m == "POST"]
    assert posts == ["/session/ses_match/message"], "exactly one submission over the wire"
    assert TOKEN_SENTINEL not in json.dumps(envelope)
    # the prompt is never persisted, and the ledger holds exactly one POST record
    for path in (ws / ".devrelay").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            assert PROMPT not in text, path
            assert TOKEN_SENTINEL not in text, path


def test_stdio_raw_protocol_lines_and_clean_eof_exit(tmp_path, fake_opencode):
    """Raw JSON-RPC over the pipes: newline-delimited frames, clean EOF exit."""
    ws = make_workspace(tmp_path, fake_opencode.base_url)
    fake_opencode.stub.workspace = str(ws)
    for session in fake_opencode.stub.sessions:
        session["directory"] = str(ws)

    proc = subprocess.Popen(
        [sys.executable, "-m", "devrelay", "mcp", "serve", "--workspace", str(ws)],
        cwd=str(ws),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    assert proc.stdin and proc.stdout

    def send(payload: dict[str, Any]) -> None:
        proc.stdin.write(json.dumps(payload) + chr(10))
        proc.stdin.flush()

    def receive() -> dict[str, Any]:
        line = proc.stdout.readline()
        assert line.strip(), "the server closed stdout unexpectedly"
        return json.loads(line)  # every stdout line must be a protocol frame

    try:
        send(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "devrelay-raw-probe", "version": "0"},
                },
            }
        )
        init = receive()
        assert init["result"]["serverInfo"]["name"] == "devrelay"
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        listed = receive()
        assert [tool["name"] for tool in listed["result"]["tools"]] == EXACT_TOOLS
        send(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "devrelay_status", "arguments": {}},
            }
        )
        called = receive()
        result = called["result"]
        assert result["structuredContent"]["ok"] is True
        assert result["structuredContent"]["tool"] == "devrelay_status"
        assert result.get("isError") in (None, False)
        # EOF on stdin: the server must exit cleanly and promptly
        proc.stdin.close()
        assert proc.wait(timeout=30) == 0
        assert proc.stdout.read() == "", "no stray stdout after the last frame"
        stderr = proc.stderr.read() if proc.stderr else ""
        assert "serving MCP over stdio" in stderr
    finally:
        if proc.poll() is None:  # pragma: no cover - defensive
            proc.kill()


def test_stdio_invalid_workspace_refuses_before_serving(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    completed = subprocess.run(
        [sys.executable, "-m", "devrelay", "mcp", "serve", "--workspace", str(plain)],
        cwd=str(plain),
        input=b"",
        capture_output=True,
        timeout=60,
    )
    assert completed.returncode == 2
    assert completed.stdout == b""
    assert b"not an initialized DevRelay workspace" in completed.stderr

    missing = subprocess.run(
        [sys.executable, "-m", "devrelay", "mcp", "serve"],
        capture_output=True,
        timeout=60,
    )
    assert missing.returncode == 2
    assert missing.stdout == b""
    assert b"--workspace" in missing.stderr
