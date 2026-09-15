"""OpenCode HTTP transport (v0.3-A).

One configured endpoint, one attempt per request, bounded responses, sanitized
errors.  No port scanning, no process discovery, no shell, no retries.

The wire paths are *defaults* for the documented OpenCode server shape; every
path is configurable (``OpenCodeConfig.paths``) and the normalization layer is
tolerant, because the exact server contract can only be confirmed by a real
smoke (see ``docs/v0.3/V03A_SPEC.md``).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Mapping

import httpx

from devrelay.opencode.models import OpenCodeCallState
from devrelay.redact import sanitize

# Response bodies are never echoed in full: bounded read + sanitized snippet.
MAX_ERROR_SNIPPET_CHARS = 500


@dataclass
class OpenCodePaths:
    """Configurable wire paths (defaults follow the OpenCode server shape)."""

    health: str = "/global/health"
    sessions: str = "/session"
    session: str = "/session/{session_id}"
    messages: str = "/session/{session_id}/message"
    prompt: str = "/session/{session_id}/prompt"
    abort: str = "/session/{session_id}/abort"

    def session_path(self, session_id: str) -> str:
        return self.session.format(session_id=session_id)

    def messages_path(self, session_id: str) -> str:
        return self.messages.format(session_id=session_id)

    def prompt_path(self, session_id: str) -> str:
        return self.prompt.format(session_id=session_id)

    def abort_path(self, session_id: str) -> str:
        return self.abort.format(session_id=session_id)


@dataclass
class TransportResponse:
    """Outcome of exactly one HTTP attempt (never raises for provider errors)."""

    state: OpenCodeCallState
    status: int | None = None
    data: Any = None
    error_type: str = ""
    error: str = ""
    duration_ms: int = 0
    response_bytes: int = 0
    response_truncated: bool = False
    headers: Mapping[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.state is OpenCodeCallState.COMPLETED


class OpenCodeTransport:
    """Thin, explicit HTTP client for one configured OpenCode server."""

    def __init__(
        self,
        base_url: str,
        *,
        paths: OpenCodePaths | None = None,
        token: str = "",
        timeout_seconds: float = 30.0,
        max_response_bytes: int = 1_048_576,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.paths = paths or OpenCodePaths()
        self.timeout_seconds = float(timeout_seconds)
        self.max_response_bytes = max(1_024, int(max_response_bytes))
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if client is not None:
            # Injected client (tests): still enforce auth/identity headers.
            if headers:
                client.headers.update(headers)
            self._client = client
            self._owns_client = False
        else:
            self._client = httpx.Client(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout_seconds,
            )
            self._owns_client = True

    # ------------------------------------------------------------------
    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        params: Mapping[str, Any] | None = None,
        expect_json: bool = True,
    ) -> TransportResponse:
        """Issue exactly one request; ``state`` always describes the outcome."""
        started = time.monotonic()
        try:
            with self._client.stream(
                method, path, json=json_body, params=params
            ) as response:
                body = self._read_bounded(response)
                status = response.status_code
                headers = {k.lower(): v for k, v in response.headers.items()}
        except httpx.TimeoutException as exc:
            return TransportResponse(
                state=OpenCodeCallState.TIMED_OUT,
                error_type="timeout",
                error=sanitize(f"{type(exc).__name__}: {exc}")[:MAX_ERROR_SNIPPET_CHARS],
                duration_ms=self._ms(started),
            )
        except httpx.HTTPError as exc:
            return TransportResponse(
                state=OpenCodeCallState.PROVIDER_UNAVAILABLE,
                error_type="transport",
                error=sanitize(f"{type(exc).__name__}: {exc}")[:MAX_ERROR_SNIPPET_CHARS],
                duration_ms=self._ms(started),
            )
        except OSError as exc:  # pragma: no cover - defensive
            return TransportResponse(
                state=OpenCodeCallState.PROVIDER_UNAVAILABLE,
                error_type="transport",
                error=sanitize(f"{type(exc).__name__}: {exc}")[:MAX_ERROR_SNIPPET_CHARS],
                duration_ms=self._ms(started),
            )

        truncated = len(body) > self.max_response_bytes
        payload_bytes = body[: self.max_response_bytes]
        duration = self._ms(started)
        if truncated:
            return TransportResponse(
                state=OpenCodeCallState.MALFORMED_RESPONSE,
                status=status,
                error_type="response_too_large",
                error=(
                    "response exceeded the configured "
                    f"{self.max_response_bytes}-byte cap; refusing to parse it"
                ),
                duration_ms=duration,
                response_bytes=len(body),
                response_truncated=True,
                headers=headers,
            )
        if not 200 <= status < 300:
            return TransportResponse(
                state=OpenCodeCallState.PROVIDER_UNAVAILABLE,
                status=status,
                error_type="http_status",
                error=f"HTTP {status}: {self._snippet(payload_bytes)}",
                duration_ms=duration,
                response_bytes=len(body),
                headers=headers,
            )
        if not expect_json:
            return TransportResponse(
                state=OpenCodeCallState.COMPLETED,
                status=status,
                data=None,
                duration_ms=duration,
                response_bytes=len(body),
                headers=headers,
            )
        text = payload_bytes.decode("utf-8", errors="replace").strip()
        if not text:
            return TransportResponse(
                state=OpenCodeCallState.MALFORMED_RESPONSE,
                status=status,
                error_type="empty_response",
                error="server returned an empty body where JSON was expected",
                duration_ms=duration,
                response_bytes=len(body),
                headers=headers,
            )
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            return TransportResponse(
                state=OpenCodeCallState.MALFORMED_RESPONSE,
                status=status,
                error_type="invalid_json",
                error=f"invalid JSON response: {exc}",
                duration_ms=duration,
                response_bytes=len(body),
                headers=headers,
            )
        return TransportResponse(
            state=OpenCodeCallState.COMPLETED,
            status=status,
            data=data,
            duration_ms=duration,
            response_bytes=len(body),
            headers=headers,
        )

    # ------------------------------------------------------------------
    def _read_bounded(self, response: httpx.Response) -> bytes:
        """Stream the body, stopping at cap+1 bytes (never unbounded)."""
        chunks: list[bytes] = []
        total = 0
        limit = self.max_response_bytes + 1
        for chunk in response.iter_bytes():
            if not chunk:
                continue
            chunks.append(chunk)
            total += len(chunk)
            if total >= limit:
                break
        return b"".join(chunks)

    @staticmethod
    def _snippet(data: bytes) -> str:
        text = data.decode("utf-8", errors="replace").strip()
        return sanitize(text)[:MAX_ERROR_SNIPPET_CHARS]

    @staticmethod
    def _ms(started: float) -> int:
        return max(0, int(round((time.monotonic() - started) * 1000)))

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
