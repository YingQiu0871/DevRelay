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
import re
import time
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import quote, quote_plus

import httpx

from devrelay.errors import OpenCodeConfigError
from devrelay.opencode.models import OpenCodeCallState
from devrelay.redact import redact_text, sanitize

# Response bodies are never echoed in full: bounded read + sanitized snippet.
MAX_ERROR_SNIPPET_CHARS = 500


@dataclass
class OpenCodePaths:
    """Wire paths, verified against the installed OpenCode 1.18.11 ``/doc``.

    ``prompt`` and ``messages`` are the *same* route with different methods: the
    documented synchronous submission is ``POST /session/{id}/message`` ("Send
    message ... streaming the AI response"), while ``GET /session/{id}/message``
    lists the session's messages.  There is deliberately **no** ``/session/{id}/prompt``
    route on OpenCode 1.18.11 (the A33 smoke proved the server answers unmatched
    paths with a ``200 text/html`` SPA fallback) and no compatibility fallback:
    a fallback would issue a second submission POST.
    """

    health: str = "/global/health"
    sessions: str = "/session"
    session: str = "/session/{session_id}"
    messages: str = "/session/{session_id}/message"
    prompt: str = "/session/{session_id}/message"
    abort: str = "/session/{session_id}/abort"
    #: Runtime status map for every session (``SessionStatus``), used by wait_idle
    #: because OpenCode 1.18.11 session objects expose no state/status field.
    status: str = "/session/status"

    def session_path(self, session_id: str) -> str:
        return self.session.format(session_id=session_id)

    def messages_path(self, session_id: str) -> str:
        return self.messages.format(session_id=session_id)

    def prompt_path(self, session_id: str) -> str:
        return self.prompt.format(session_id=session_id)

    def abort_path(self, session_id: str) -> str:
        return self.abort.format(session_id=session_id)

    @property
    def status_path(self) -> str:
        return self.status


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
    #: True when this failure cannot prove the request was never submitted (a
    #: read/write timeout, a read/write error or a remote protocol error): the
    #: bytes may already have reached the server, so a caller must not treat the
    #: attempt as safely retryable (third-review blocker P1).
    submission_uncertain: bool = False
    #: Response media type (lower-cased, parameters stripped).  A 2xx whose media
    #: type is clearly not JSON (e.g. the SPA ``text/html`` fallback the real
    #: server returns for an unmatched route) is *not* credible acceptance
    #: evidence (A33 real-protocol finding).
    content_type: str = ""

    @property
    def ok(self) -> bool:
        return self.state is OpenCodeCallState.COMPLETED


def _redaction_variants(values: Iterable[str], *, depth: int = 2) -> tuple[str, ...]:
    """Literal and realistically encoded forms of every sensitive literal.

    A provider that echoes a prompt or a credential inside JSON, a URL-encoded
    field or a Python-style escape does not echo the literal bytes, so literal
    replacement alone is not enough (P1-D).  Each value is expanded into its
    JSON-escaped form (escaped quotes, backslashes, newline/tab escapes and
    non-ASCII code-point escapes), its backslash-escaped form, its percent-encoded
    forms (``quote`` and ``quote_plus``) and, up to ``depth`` levels, the escaped
    forms of those - then all of them are handed to the shared redactor.

    This is deliberately bounded and does not change the redaction subsystem
    itself: it only widens the list of literals that must never survive into a
    persisted or rendered error snippet.
    """
    out: list[str] = []
    seen: set[str] = set()

    def add(candidate: str) -> None:
        if len(candidate) >= 4 and candidate not in seen:
            seen.add(candidate)
            out.append(candidate)

    for value in values:
        if not value:
            continue
        add(value)
        current = [value]
        for _ in range(max(1, depth)):
            expanded: list[str] = []
            for item in current:
                expanded.extend(
                    (
                        json.dumps(item)[1:-1],                    # JSON escaping
                        item.encode("unicode_escape").decode("ascii"),
                        quote(item, safe=""),
                        quote_plus(item, safe=""),
                    )
                )
            for item in expanded:
                add(item)
            current = expanded
    return tuple(out)


def _error_name(exc: BaseException) -> str:
    """Snake-case exception name, used as a precise transport error type."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", type(exc).__name__).lower()


def transport_failure(
    exc: httpx.TransportError, *, error: str, duration_ms: int
) -> TransportResponse:
    """Classify a transport failure: submitted-uncertain or not-submitted.

    The distinction is safety-critical for a submission: ``ConnectTimeout``,
    ``PoolTimeout``, ``ConnectError``, ``ProxyError``, ``UnsupportedProtocol`` and
    ``LocalProtocolError`` prove that no connection was established or that the
    request was refused locally, so the prompt was *not* submitted and the
    failure is not ``submission_uncertain``.  A read/write timeout or a
    read/write/remote-protocol error may happen after the request bytes were sent
    - the server may already have accepted the prompt - so those (and anything
    unclassified) are marked ``submission_uncertain=True``.  The default is
    uncertainty: a caller must never be told "safe to retry" on a guess.
    """
    if isinstance(exc, httpx.ConnectTimeout):
        error_type, uncertain = "connect_timeout", False
    elif isinstance(exc, httpx.PoolTimeout):
        error_type, uncertain = "pool_timeout", False
    elif isinstance(exc, httpx.ConnectError):
        error_type, uncertain = "connect_error", False
    elif isinstance(exc, httpx.ReadTimeout):
        error_type, uncertain = "read_timeout", True
    elif isinstance(exc, httpx.WriteTimeout):
        error_type, uncertain = "write_timeout", True
    elif isinstance(
        exc, (httpx.ProxyError, httpx.UnsupportedProtocol, httpx.LocalProtocolError)
    ):
        error_type, uncertain = _error_name(exc), False
    else:
        # ReadError/WriteError/RemoteProtocolError/CloseError and any future
        # transport failure whose stage is unknown.
        error_type, uncertain = _error_name(exc), True
    return TransportResponse(
        state=(
            OpenCodeCallState.TIMED_OUT
            if isinstance(exc, httpx.TimeoutException)
            else OpenCodeCallState.PROVIDER_UNAVAILABLE
        ),
        error_type=error_type,
        error=error,
        duration_ms=duration_ms,
        submission_uncertain=uncertain,
    )


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
        # The bearer token must never appear in a persisted error snippet.
        self._token_redactions = (token,) if token else ()
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
            try:
                self._client = httpx.Client(
                    base_url=self.base_url,
                    headers=headers,
                    timeout=self.timeout_seconds,
                # P2-A: the OpenCode control channel is bearer-authenticated and
                # usually loopback.  Ambient HTTP_PROXY/HTTPS_PROXY/ALL_PROXY/
                # SSL_CERT_FILE must never silently reroute or intercept it.
                    # DevRelay has no reviewed proxy configuration mechanism, so
                    # ambient environment routing is disabled outright.
                    trust_env=False,
                )
            except httpx.InvalidURL as exc:
                # A malformed authority must be a configuration error (the
                # config layer already refuses these); never an httpx exception
                # escaping the provider boundary - and never a URL with an
                # embedded password in the message.
                raise OpenCodeConfigError(
                    "opencode.base_url is not a usable URL: "
                    + redact_text(str(exc))
                ) from None
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
        timeout_seconds: float | None = None,
        redact_values: Sequence[str] = (),
    ) -> TransportResponse:
        """Issue exactly one request; ``state`` always describes the outcome.

        ``timeout_seconds`` overrides the client timeout for this single request
        (used to clamp a bounded operation to its remaining budget).
        ``redact_values`` are extra literals (prompt text, bearer token) that must
        never appear in a persisted error snippet.
        """
        started = time.monotonic()
        extra = _redaction_variants((*self._token_redactions, *redact_values))
        request_timeout = (
            self.timeout_seconds if timeout_seconds is None else max(0.001, timeout_seconds)
        )
        try:
            with self._client.stream(
                method,
                path,
                json=json_body,
                params=params,
                timeout=request_timeout,
            ) as response:
                body = self._read_bounded(response)
                status = response.status_code
                headers = {k.lower(): v for k, v in response.headers.items()}
                media_type = headers.get("content-type", "").split(";")[0].strip().lower()
        except httpx.TransportError as exc:
            return transport_failure(
                exc,
                error=self._clip(f"{type(exc).__name__}: {exc}", extra),
                duration_ms=self._ms(started),
            )
        except httpx.HTTPError as exc:
            # Non-transport httpx failures (e.g. a decoding error) happen after a
            # response arrived, so they are never "not submitted".
            return TransportResponse(
                state=OpenCodeCallState.PROVIDER_UNAVAILABLE,
                error_type=_error_name(exc),
                error=self._clip(f"{type(exc).__name__}: {exc}", extra),
                duration_ms=self._ms(started),
                submission_uncertain=True,
            )
        except OSError as exc:  # pragma: no cover - defensive
            # A socket-level OSError can happen mid-transfer: fail closed.
            return TransportResponse(
                state=OpenCodeCallState.PROVIDER_UNAVAILABLE,
                error_type=_error_name(exc),
                error=self._clip(f"{type(exc).__name__}: {exc}", extra),
                duration_ms=self._ms(started),
                submission_uncertain=True,
            )

        truncated = len(body) > self.max_response_bytes
        payload_bytes = body[: self.max_response_bytes]
        duration = self._ms(started)
        if truncated:
            return TransportResponse(
                state=OpenCodeCallState.MALFORMED_RESPONSE,
                status=status,
                content_type=media_type,
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
                content_type=media_type,
                error_type="http_status",
                error=f"HTTP {status}: {self._snippet(payload_bytes, extra)}",
                duration_ms=duration,
                response_bytes=len(body),
                headers=headers,
            )
        if not expect_json:
            return TransportResponse(
                state=OpenCodeCallState.COMPLETED,
                status=status,
                content_type=media_type,
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
                content_type=media_type,
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
                content_type=media_type,
                error_type="invalid_json",
                error=f"invalid JSON response: {exc}",
                duration_ms=duration,
                response_bytes=len(body),
                headers=headers,
            )
        except RecursionError:
            # P1-E: extreme nesting is an untrusted-content condition, not a
            # crash: it must normalize like every other malformed body.
            return TransportResponse(
                state=OpenCodeCallState.MALFORMED_RESPONSE,
                status=status,
                content_type=media_type,
                error_type="json_too_deep",
                error=(
                    "provider JSON response is nested too deeply to parse; "
                    "refusing to interpret it"
                ),
                duration_ms=duration,
                response_bytes=len(body),
                headers=headers,
            )
        except ValueError as exc:
            # e.g. an integer literal beyond CPython's digit limit.
            return TransportResponse(
                state=OpenCodeCallState.MALFORMED_RESPONSE,
                status=status,
                content_type=media_type,
                error_type="json_unparsable",
                error=f"provider JSON response could not be parsed ({exc})",
                duration_ms=duration,
                response_bytes=len(body),
                headers=headers,
            )
        return TransportResponse(
            state=OpenCodeCallState.COMPLETED,
            status=status,
            content_type=media_type,
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
    def _clip(text: str, extra: Sequence[str]) -> str:
        """Bounded, sanitized snippet: never persists a raw provider body."""
        return redact_text(text, extra_values=extra)[:MAX_ERROR_SNIPPET_CHARS]

    @classmethod
    def _snippet(cls, data: bytes, extra: Sequence[str] = ()) -> str:
        text = data.decode("utf-8", errors="replace").strip()
        return cls._clip(text, extra)

    @staticmethod
    def _ms(started: float) -> int:
        return max(0, int(round((time.monotonic() - started) * 1000)))

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
