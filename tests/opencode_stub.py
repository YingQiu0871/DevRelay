"""Deterministic offline OpenCode server stub (v0.3-A tests).

A tiny in-memory implementation of the **verified** OpenCode 1.18.11 server
shape (see ``docs/v0.3/V03A_SPEC.md`` and the A33 evidence): the synchronous
submission route is ``POST /session/{id}/message`` returning ``{info, parts}``,
runtime state comes from ``GET /session/status``, and any *unmatched* path
answers with the real SPA fallback (``200 text/html``) - including the
nonexistent ``/prompt`` route, so an accidental regression to it is visible.

Wired through ``httpx.MockTransport`` so every v0.3-A test runs offline and
deterministically.  Failure modes are configured explicitly (never inferred).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from devrelay.opencode.bridge import OpenCodeBridge
from devrelay.opencode.transport import OpenCodeTransport

# Absolute on every platform: provider-reported workspaces are only trusted when
# absolute (P2/PART III - no implicit resolution against DevRelay's cwd).
DEFAULT_WORKSPACE = str(Path(tempfile.gettempdir()) / "opencode-stub-ws")

FAKE_SECRET = "sk-live-OPENCODESECRET1234567890ab"

#: The real server answers unmatched routes with its SPA shell (200 text/html).
#: A33 observed exactly this for the nonexistent `/session/{id}/prompt` route.
SPA_FALLBACK_HTML = (
    "<!doctype html>" + chr(10)
    + '<html lang="en"><head><title>OpenCode</title></head>'
    + '<body><div id="root"></div></body></html>' + chr(10)
)

#: Transport failures the stub can raise per route (third-review P1 tests).
STUB_EXCEPTIONS = {
    "read_timeout": httpx.ReadTimeout,
    "write_timeout": httpx.WriteTimeout,
    "connect_timeout": httpx.ConnectTimeout,
    "pool_timeout": httpx.PoolTimeout,
    "connect_error": httpx.ConnectError,
    "read_error": httpx.ReadError,
    "remote_protocol_error": httpx.RemoteProtocolError,
}


def _session(
    session_id: str,
    *,
    workspace: str = DEFAULT_WORKSPACE,
    state: str = "idle",
    title: str = "",
    include_workspace: bool = True,
    include_state: bool = False,
) -> dict[str, Any]:
    """A session object.

    By default (``include_state=False``) this models the real OpenCode 1.18.11
    session, which has no ``state``/``status`` field at all (A33 evidence):
    runtime state must come from ``GET /session/status``.  ``include_state=True``
    keeps a state-reporting provider available for the bridge's state mapping.
    """
    payload: dict[str, Any] = {
        "id": session_id,
        "title": title or f"session {session_id}",
    }
    if include_state:
        payload["state"] = state
    if include_workspace:
        payload["directory"] = workspace
    return payload


def _message(
    message_id: str, role: str, text: str, *, created_at: str = ""
) -> dict[str, Any]:
    return {
        "info": {
            "id": message_id,
            "role": role,
            "created_at": created_at or f"2026-01-01T00:00:{message_id[-2:]}Z",
        },
        "parts": [{"type": "text", "text": text}],
    }


class StubOpenCodeServer:
    """Configurable in-memory OpenCode server for offline bridge tests."""

    def __init__(
        self,
        *,
        workspace: str = DEFAULT_WORKSPACE,
        sessions: list[dict[str, Any]] | None = None,
        messages: list[dict[str, Any]] | None = None,
        state_sequence: list[str] | None = None,
        capabilities: list[str] | None = None,
        version: str = "stub-9.9.9",
        abort_supported: bool = True,
        unreachable: bool = False,
        timeout: bool = False,
        http_status: int | None = None,
        error_body: str | None = None,
        malformed: str = "",
        oversize: bool = False,
        prompt_reply: dict[str, Any] | None = None,
        prompt_ack_only: bool = False,
        prompt_raw_reply: Any = None,
        prompt_http_status: int | None = None,
        prompt_append: dict[str, Any] | None = None,
        prompt_exception: str | None = None,
        session_exception_after_prompt: str | None = None,
        prompt_error_body: str | None = None,
        vanish_after_prompt: bool = False,
        session_http_status_after_prompt: int | None = None,
        session_error_body_after_prompt: str | None = None,
        session_id_override: str | None = None,
        messages_http_status: int | None = None,
        messages_error_body: str | None = None,
        malformed_after_prompt: str = "",
        abort_status: int | None = None,
        abort_body: str | None = None,
        abort_removes_session: bool = False,
        health_healthy: bool = True,
        status_map: dict[str, Any] | None = None,
        status_sequence: list[Any] | None = None,
        prompt_content_type: str = "application/json",
        prompt_html_fallback: bool = False,
    ) -> None:
        self.workspace = workspace
        self.sessions = (
            list(sessions)
            if sessions is not None
            else [_session("ses_match", workspace=workspace)]
        )
        self.messages = (
            list(messages)
            if messages is not None
            else [
                _message("msg_01", "user", "hello"),
                _message("msg_02", "assistant", "hi there"),
            ]
        )
        self.state_sequence = list(state_sequence or [])
        self.capabilities = list(capabilities or ["list_sessions", "messages", "interrupt"])
        self.version = version
        self.abort_supported = abort_supported
        self.unreachable = unreachable
        self.timeout = timeout
        self.http_status = http_status
        self.error_body = error_body
        self.malformed = malformed
        self.oversize = oversize
        self.prompt_reply = prompt_reply
        self.prompt_ack_only = prompt_ack_only
        # P1-3 scenarios: a raw (non-message) POST payload, a session that
        # vanishes right after acceptance, and a failing follow-up read.
        self.prompt_raw_reply = prompt_raw_reply
        self.prompt_http_status = prompt_http_status
        # A message appended when the prompt is received even though the response
        # body itself is unusable (P1-B: accepted + reply correlated later).
        self.prompt_append = prompt_append
        self.prompt_exception = prompt_exception
        self.session_exception_after_prompt = session_exception_after_prompt
        self.prompt_error_body = prompt_error_body
        self.vanish_after_prompt = vanish_after_prompt
        self.session_http_status_after_prompt = session_http_status_after_prompt
        self.session_error_body_after_prompt = session_error_body_after_prompt
        self.session_id_override = session_id_override
        self.messages_http_status = messages_http_status
        self.messages_error_body = messages_error_body
        self.malformed_after_prompt = malformed_after_prompt
        self.abort_status = abort_status
        self.abort_body = abort_body
        self.abort_removes_session = abort_removes_session
        self.health_healthy = health_healthy
        #: Real `/session/status` map (session id -> SessionStatus).  A session
        #: that is not running is *absent* from the map, exactly like 1.18.11.
        # Kept verbatim (a malformed payload must be testable as-is).
        self.status_map = status_map if status_map is not None else {}
        #: Successive answers for `/session/status` (the last one repeats).
        self.status_sequence = list(status_sequence or [])
        self.next_status_index = 0
        self.prompt_content_type = prompt_content_type
        self.prompt_html_fallback = prompt_html_fallback

        # observations
        self.requests: list[tuple[str, str]] = []
        self.prompts: list[dict[str, Any]] = []
        self.next_state_index = 0
        self._message_counter = len(self.messages) + 1

    # ------------------------------------------------------------------
    def handler(self, request: httpx.Request) -> httpx.Response:
        path = urlparse(str(request.url)).path
        self.requests.append((request.method.upper(), path))
        if self.unreachable:
            raise httpx.ConnectError("connection refused")
        if self.timeout:
            raise httpx.ReadTimeout("stub timeout")
        if self.http_status and self.http_status >= 400:
            body = self.error_body if self.error_body is not None else '{"error":"boom"}'
            return httpx.Response(self.http_status, text=body)
        if self.oversize:
            return httpx.Response(200, text=json.dumps({"blob": "x" * 20000}))

        if self.malformed == "invalid_json":
            return httpx.Response(200, text="{not json")
        if self.malformed == "empty":
            return httpx.Response(200, text="")
        if self.malformed == "deep_json":
            # P1-E parser bomb: extreme nesting raises RecursionError in json.
            return httpx.Response(200, text="[" * 200_000 + "]" * 200_000)
        if self.malformed == "huge_int":
            # P1-E parser bomb: a 5000-digit integer exceeds CPython's limit.
            return httpx.Response(200, text="9" * 5_000)
        if self.malformed == "not_object":
            return self._json(["not", "an", "object"])

        parts = [p for p in path.split("/") if p]
        if path == "/session/status":
            # Real runtime-status map: only active/retrying sessions appear.
            if self.status_sequence:
                index = min(self.next_status_index, len(self.status_sequence) - 1)
                self.next_status_index += 1
                return self._json(self.status_sequence[index])
            return self._json(self.status_map)
        if path == "/global/health":
            return self._json(
                {
                    "healthy": self.health_healthy,
                    "version": self.version,
                    "capabilities": self.capabilities,
                }
            )
        if parts[:1] == ["session"] and len(parts) == 1:
            if self.malformed == "not_array":
                return self._json({"sessions": {"unexpected": True}})
            return self._json({"sessions": self.sessions})
        if parts[:1] == ["session"] and len(parts) == 2:
            if self.prompts and self.session_http_status_after_prompt:
                return httpx.Response(
                    self.session_http_status_after_prompt,
                    text=self.session_error_body_after_prompt or '{"error":"boom"}',
                )
            session = self._find(parts[1])
            if session is None:
                return httpx.Response(404, text="not found")
            if self.prompts and self.session_exception_after_prompt:
                raise STUB_EXCEPTIONS[self.session_exception_after_prompt](
                    "stub follow-up failure"
                )
            if self.prompts and self.malformed_after_prompt:
                if self.malformed_after_prompt == "not_object":
                    return self._json(["not", "an", "object"])
                return httpx.Response(200, text="{not json")
            if self.session_id_override:
                session = {**session, "id": self.session_id_override}
            if self.state_sequence:
                index = min(self.next_state_index, len(self.state_sequence) - 1)
                self.next_state_index += 1
                session = {**session, "state": self.state_sequence[index]}
            return self._json(session)
        if parts[:1] == ["session"] and parts[2:] == ["prompt"]:
            # Not a route on OpenCode 1.18.11: the real server answers unknown
            # paths with its SPA shell.  Kept so a regression to the old path is
            # both recorded and semantically visible (200 text/html).
            return httpx.Response(
                200, text=SPA_FALLBACK_HTML, headers={"content-type": "text/html"}
            )
        if parts[:1] == ["session"] and parts[2:] == ["message"]:
            session = self._find(parts[1])
            if session is None:
                return httpx.Response(404, text="not found")
            if request.method.upper() == "POST":
                return self._handle_message_post(session, request)
            if self.messages_http_status is not None:
                return httpx.Response(
                    self.messages_http_status,
                    text=self.messages_error_body
                    if self.messages_error_body is not None
                    else '{"error":"boom"}',
                )
            if self.malformed == "messages_not_array":
                return self._json({"messages": "nope"})
            return self._json({"messages": self.messages})
        if parts[:1] == ["session"] and parts[2:] == ["abort"]:
            if self._find(parts[1]) is None:
                return httpx.Response(404, text="not found")
            if self.abort_removes_session:
                self.sessions = [s for s in self.sessions if s.get("id") != parts[1]]
            if self.abort_status is not None:
                if self.abort_status == 204:
                    return httpx.Response(204)
                return httpx.Response(
                    self.abort_status,
                    text=self.abort_body
                    if self.abort_body is not None
                    else '{"error":"boom"}',
                )
            if not self.abort_supported:
                return httpx.Response(405, text="abort unsupported")
            self._find(parts[1])["state"] = "idle"
            return self._json({"ok": True})
        # Unmatched routes: the real server answers with its SPA shell (200
        # text/html) - the behaviour A33 observed for `/session/{id}/prompt`.
        return httpx.Response(
            200, text=SPA_FALLBACK_HTML, headers={"content-type": "text/html"}
        )

    # ------------------------------------------------------------------
    def _handle_message_post(self, session: dict[str, Any], request: httpx.Request):
        """Real ``POST /session/{id}/message`` behaviour for one submission."""
        body = json.loads(request.content.decode("utf-8") or "{}")
        if self.prompt_exception:
            # The server received the message: record it (and any reply it
            # produced) and then fail the way the transport would.
            self.prompts.append(body)
            if self.prompt_append is not None:
                self._message_counter += 1
                self.messages.append(self.prompt_append)
            session["state"] = "busy"
            raise STUB_EXCEPTIONS[self.prompt_exception]("stub prompt failure")
        if self.prompt_html_fallback:
            self.prompts.append(body)
            session["state"] = "busy"
            return httpx.Response(
                200, text=SPA_FALLBACK_HTML, headers={"content-type": "text/html"}
            )
        if self.prompt_http_status is not None:
            self.prompts.append(body)
            if self.prompt_append is not None:
                self._message_counter += 1
                self.messages.append(self.prompt_append)
            session["state"] = "busy"
            return httpx.Response(
                self.prompt_http_status,
                text=self.prompt_error_body
                if self.prompt_error_body is not None
                else '{"error":"boom"}',
                headers={"content-type": self.prompt_content_type},
            )
        if self.prompt_raw_reply is not None:
            self.prompts.append(body)
            self._message_counter += 1
            session["state"] = "busy"
            if self.vanish_after_prompt:
                self.sessions = [s for s in self.sessions if s is not session]
            return self._json(self.prompt_raw_reply)
        self.prompts.append(body)
        text = ""
        for part in body.get("parts", []):
            if isinstance(part, dict) and part.get("type") == "text":
                text = str(part.get("text", ""))
        reply = self.prompt_reply or _message(
            "msg_%02d" % self._message_counter, "assistant", "echo: " + text
        )
        self._message_counter += 1
        self.messages.append(reply)
        session["state"] = "busy"
        if self.vanish_after_prompt:
            self.sessions = [s for s in self.sessions if s is not session]
        if self.prompt_ack_only:
            return self._json({"ok": True})
        # Real documented response: {info: AssistantMessage, parts: Part[]}
        return self._json(reply)

    # ------------------------------------------------------------------
    def _find(self, session_id: str) -> dict[str, Any] | None:
        for session in self.sessions:
            if session.get("id") == session_id:
                return session
        return None

    @staticmethod
    def _json(payload: Any, status: int = 200) -> httpx.Response:
        return httpx.Response(status, content=json.dumps(payload).encode("utf-8"))

    def client(self) -> httpx.Client:
        return httpx.Client(
            transport=httpx.MockTransport(self.handler),
            base_url="http://opencode.invalid",
        )

    def transport(self, **overrides: Any) -> OpenCodeTransport:
        payload = {
            "base_url": "http://opencode.invalid",
            "timeout_seconds": 5.0,
            "max_response_bytes": overrides.pop("max_response_bytes", 1_048_576),
            "client": self.client(),
        }
        payload.update(overrides)
        return OpenCodeTransport(**payload)

    def bridge(self, *, workspace_root: str = DEFAULT_WORKSPACE, **kwargs: Any) -> OpenCodeBridge:
        """Bridge wired to this stub (never touches the network)."""
        payload: dict[str, Any] = {
            "base_url": "http://opencode.invalid",
            "workspace_root": workspace_root,
            "poll_interval_seconds": 0.01,
            "sleep": lambda _seconds: None,
        }
        payload.update(kwargs)
        payload["transport"] = self.transport(
            max_response_bytes=payload.get("max_response_bytes", 1_048_576)
        )
        return OpenCodeBridge(**payload)
