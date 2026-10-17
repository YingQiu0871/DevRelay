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
import queue
import shutil
import subprocess
import sys
import threading
import time
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
    # v0.3-C appends exactly three role-aware tools; the accepted nine above are
    # unchanged, in order.
    "devrelay_list_roles",
    "devrelay_get_role",
    "devrelay_send_role_prompt",
    # v0.3-D appends exactly five bounded-orchestration tools.
    "devrelay_start_run",
    "devrelay_get_run",
    "devrelay_run_implementer",
    "devrelay_run_reviewer",
    "devrelay_decide_run",
    # v0.3-E appends exactly two fail-closed recovery tools.
    "devrelay_reconcile_run",
    "devrelay_resolve_recovery",
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


#: The child must import the checkout under test, never an ambient editable
#: installation.  The repository's normal test strategy is ``pythonpath = ["src"]``
#: (see pyproject.toml), so the harness pins exactly that for every child.
CANDIDATE_SRC = Path(__file__).resolve().parents[1] / "src"
_PINNED_DROP = ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP")


def child_env(**extra: str) -> dict[str, str]:
    """Environment for a child MCP server process: pinned candidate + extras."""
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("DEVRELAY_") and key not in _PINNED_DROP
    }
    env["PYTHONPATH"] = str(CANDIDATE_SRC)
    env.update({key: value for key, value in extra.items() if value is not None})
    return env


def server_params(ws: Path, *, env: dict[str, str] | None = None) -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "devrelay", "mcp", "serve", "--workspace", str(ws)],
        cwd=str(ws),
        env=child_env(**(env or {})),
    )


def run_child(args: list[str], *, cwd: Path, env: dict[str, str] | None = None,
              input_bytes: bytes = b"", timeout: int = 60) -> subprocess.CompletedProcess:
    """Run one child MCP process with the candidate checkout pinned."""
    return subprocess.run(
        [sys.executable, "-m", "devrelay", "mcp", *args],
        cwd=str(cwd),
        env=child_env(**(env or {})),
        input=input_bytes,
        capture_output=True,
        timeout=timeout,
    )


def spawn_child(args: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-m", "devrelay", "mcp", *args],
        cwd=str(cwd),
        env=child_env(**(env or {})),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
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
    proc = run_child(["serve", "--workspace", str(ws)], cwd=ws)
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    assert proc.stdout == b"", "stdout must stay clean for the MCP transport"
    assert b"serving MCP over stdio" in proc.stderr


def test_stdio_reports_errors_as_envelopes_without_tracebacks(tmp_path, fake_opencode):
    ws = make_workspace(tmp_path, fake_opencode.base_url)
    fake_opencode.stub.workspace = str(ws)
    for session in fake_opencode.stub.sessions:
        session["directory"] = str(ws)

    async def run() -> tuple[Any, Any, Any]:
        async with stdio_client(
            server_params(ws, env={"DEVRELAY_OPENCODE_TOKEN": TOKEN_SENTINEL})
        ) as (read, write):
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

    # concrete invariants, not "some error occurred"
    envelope = envelope_of(semantic)
    assert semantic.is_error is True
    assert envelope["schema_version"] == 1
    assert envelope["tool"] == "opencode_get_session"
    assert envelope["ok"] is False
    assert envelope["error"] is not None and envelope["error"]["type"] == "mcp_invalid_argument"
    assert envelope["error"]["message"]
    assert semantic.is_error is (not envelope["ok"])
    assert json.loads(semantic.content[0].text) == envelope, (
        "the text fallback must represent the same semantic outcome"
    )
    rendered = json.dumps(envelope)
    assert "Traceback" not in rendered and 'File "' not in rendered
    assert TOKEN_SENTINEL not in rendered
    assert "SK-" not in rendered.upper()

    # the SDK-level schema rejection (a JSON number where a string is required)
    # stays a bounded SDK error: no traceback, no secret, documented boundary
    for other in (schema, unknown):
        rendered = (
            json.dumps(getattr(other, "structured_content", None))
            if getattr(other, "structured_content", None)
            else str(other)
        )
        assert "Traceback" not in rendered
        assert 'File "' not in rendered
        assert TOKEN_SENTINEL not in rendered


def test_stdio_send_prompt_end_to_end_against_the_loopback_fake(tmp_path, fake_opencode):
    ws = make_workspace(tmp_path, fake_opencode.base_url)
    stub = fake_opencode.stub
    stub.workspace = str(ws)
    for session in stub.sessions:
        session["directory"] = str(ws)
    env = {"DEVRELAY_OPENCODE_TOKEN": TOKEN_SENTINEL}

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

    proc = spawn_child(["serve", "--workspace", str(ws)], cwd=ws)
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
    completed = run_child(["serve", "--workspace", str(plain)], cwd=plain)
    assert completed.returncode == 2
    assert completed.stdout == b""
    assert b"not an initialized DevRelay workspace" in completed.stderr

    missing = run_child(["serve"], cwd=plain)
    assert missing.returncode == 2
    assert missing.stdout == b""
    assert b"--workspace" in missing.stderr

# ---------------------------------------------------------------------------
# candidate identity: the child must execute the tree under test
# ---------------------------------------------------------------------------
def _copy_mutated_candidate(target_src: Path, marker: str) -> Path:
    """Copy the candidate package and mutate two independent surfaces.

    The marker is visible both in the advertised server version and in the
    `devrelay_status` tool payload, so it proves the *tool code path* executed by
    the child comes from the copied tree - not merely its metadata.
    """
    shutil.copytree(
        CANDIDATE_SRC / "devrelay",
        target_src / "devrelay",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    server_py = target_src / "devrelay" / "mcp" / "server.py"
    server_text = server_py.read_text(encoding="utf-8")
    assert 'MCP_SERVER_VERSION = "0.3.0-e"' in server_text
    server_py.write_text(
        server_text.replace(
            'MCP_SERVER_VERSION = "0.3.0-e"', f'MCP_SERVER_VERSION = "{marker}"'
        ),
        encoding="utf-8",
    )
    tools_py = target_src / "devrelay" / "mcp" / "tools.py"
    tools_text = tools_py.read_text(encoding="utf-8")
    anchor = '"bridge_operations": list(BRIDGE_OPERATIONS),'
    assert anchor in tools_text
    tools_py.write_text(
        tools_text.replace(
            anchor, anchor + f'\n                "candidate_marker": "{marker}",', 1
        ),
        encoding="utf-8",
    )
    return target_src


def test_stdio_child_executes_the_candidate_checkout(tmp_path):
    """Mutation propagation: a copied tree changes what the child actually runs."""
    marker = "0.3.0-b-MUTANT-CHECK"
    mutated_src = _copy_mutated_candidate(tmp_path / "tree" / "src", marker)
    ws = make_workspace(tmp_path, "http://127.0.0.1:9")

    async def probe(env: dict[str, str] | None) -> tuple[str, Any]:
        async with stdio_client(server_params(ws, env=env)) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                status = envelope_of(await session.call_tool("devrelay_status", {}))
                return init.server_info.version, status["data"].get("candidate_marker")

    mutant_version, mutant_marker = asyncio.run(probe({"PYTHONPATH": str(mutated_src)}))
    pristine_version, pristine_marker = asyncio.run(probe(None))

    assert mutant_version == marker
    assert mutant_marker == marker, "the tool code path must come from the copied tree"
    assert pristine_version == "0.3.0-e"
    assert pristine_marker is None
    assert (mutant_version, mutant_marker) != (pristine_version, pristine_marker)


def test_stdio_every_child_launch_pins_the_candidate_src():
    """The harness must never rely on the ambient editable installation."""
    assert CANDIDATE_SRC.is_dir()
    env = child_env()
    assert env["PYTHONPATH"] == str(CANDIDATE_SRC)
    assert not any(key.startswith("DEVRELAY_") for key in env)
    params = server_params(CANDIDATE_SRC)
    assert params.env is not None and params.env["PYTHONPATH"] == str(CANDIDATE_SRC)


# ---------------------------------------------------------------------------
# malformed MCP input: record the ACTUAL SDK behaviour
# ---------------------------------------------------------------------------
def _raw_line_reader(proc: subprocess.Popen) -> "queue.Queue[str]":
    lines: "queue.Queue[str]" = queue.Queue()

    def reader() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            lines.put(line)

    threading.Thread(target=reader, daemon=True).start()
    return lines


def _drain(lines: "queue.Queue[str]", timeout: float) -> list[str]:
    out: list[str] = []
    end = time.monotonic() + timeout
    while True:
        remaining = end - time.monotonic()
        if remaining <= 0:
            break
        try:
            out.append(lines.get(timeout=remaining))
        except queue.Empty:
            break
    return out


@pytest.mark.parametrize("invalid", [False, True])
def test_stdio_malformed_frames_actual_behaviour(tmp_path, invalid):
    """Unparseable/invalid-shape frames are dropped; protocol errors are typed.

    Verified SDK behaviour (mcp 2.2.0, observed through the real stdio server):
    frames that are not parseable JSON, not JSON-RPC shaped, or missing a method
    receive **no reply at all** (they are dropped, the process stays alive and
    keeps serving); an unknown method answers a JSON-RPC error -32601 and a
    request with invalid params answers -32602.  DevRelay must therefore not
    claim a generic protocol-error response for unparseable input.
    """
    ws = make_workspace(tmp_path, "http://127.0.0.1:9")
    proc = spawn_child(["serve", "--workspace", str(ws)], cwd=ws)
    lines = _raw_line_reader(proc)

    def send(raw: str) -> None:
        assert proc.stdin is not None
        proc.stdin.write(raw + chr(10))
        proc.stdin.flush()

    try:
        send(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-11-25",
                        "capabilities": {},
                        "clientInfo": {"name": "malformed-probe", "version": "0"},
                    },
                }
            )
        )
        assert _drain(lines, 5), "initialize must be answered"
        send(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}))

        if invalid:
            dropped = [
                "this is not json at all",
                json.dumps({"hello": "world"}),
                json.dumps({"jsonrpc": "2.0", "id": 7}),
            ]
            for raw in dropped:
                send(raw)
            assert _drain(lines, 1.0) == [], "unparseable frames are silently dropped"
        else:
            send(json.dumps({"jsonrpc": "2.0", "id": 8, "method": "nope/method"}))
            unknown = _drain(lines, 2.0)
            assert len(unknown) == 1
            payload = json.loads(unknown[0])
            assert payload["error"]["code"] == -32601
            assert payload["id"] == 8

            send(json.dumps({"jsonrpc": "2.0", "id": 9, "method": "tools/call"}))
            bad_params = _drain(lines, 2.0)
            assert len(bad_params) == 1
            payload = json.loads(bad_params[0])
            assert payload["error"]["code"] == -32602

        # the session survives malformed input and still serves real calls
        send(json.dumps({"jsonrpc": "2.0", "id": 10, "method": "tools/list"}))
        recovered = _drain(lines, 5)
        assert len(recovered) == 1
        assert [t["name"] for t in json.loads(recovered[0])["result"]["tools"]] == EXACT_TOOLS

        assert proc.stdin is not None
        proc.stdin.close()
        assert proc.wait(timeout=30) == 0
    finally:
        if proc.poll() is None:  # pragma: no cover - defensive
            proc.kill()
