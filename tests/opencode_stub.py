"""Deterministic offline OpenCode server stub (v0.3-A tests).

A tiny in-memory implementation of the documented OpenCode server shape, wired
through ``httpx.MockTransport`` so every v0.3-A test runs offline and
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


def _session(
    session_id: str,
    *,
    workspace: str = DEFAULT_WORKSPACE,
    state: str = "idle",
    title: str = "",
    include_workspace: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": session_id,
        "state": state,
        "title": title or f"session {session_id}",
    }
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
        if parts[:1] == ["session"] and parts[2:] == ["message"]:
            if self._find(parts[1]) is None:
                return httpx.Response(404, text="not found")
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
        if parts[:1] == ["session"] and parts[2:] == ["prompt"]:
            session = self._find(parts[1])
            if session is None:
                return httpx.Response(404, text="not found")
            body = json.loads(request.content.decode("utf-8") or "{}")
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
                )
            self.prompts.append(body)
            text = ""
            for part in body.get("parts", []):
                if isinstance(part, dict) and part.get("type") == "text":
                    text = str(part.get("text", ""))
            reply = self.prompt_reply or _message(
                f"msg_{self._message_counter:02d}", "assistant", f"echo: {text}"
            )
            if self.prompt_raw_reply is not None:
                self._message_counter += 1
                session["state"] = "busy"
                if self.vanish_after_prompt:
                    self.sessions = [s for s in self.sessions if s is not session]
                return self._json(self.prompt_raw_reply)
            self._message_counter += 1
            self.messages.append(reply)
            session["state"] = "busy"
            if self.vanish_after_prompt:
                self.sessions = [s for s in self.sessions if s is not session]
            if self.prompt_ack_only:
                return self._json({"ok": True})
            return self._json({"message": reply})
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
        return httpx.Response(404, text="unknown route")

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
