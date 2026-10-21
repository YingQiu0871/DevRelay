"""Local bearer tokens, header-borne sessions, Host and Origin checks."""

from __future__ import annotations

import hmac
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlsplit

from devrelay.web.errors import WebApiError

TOKEN_ENV = "DEVRELAY_WEB_TOKEN"
SESSION_HEADER = "x-devrelay-session"
SESSION_TTL_SECONDS = 8 * 60 * 60
IDLE_TTL_SECONDS = 30 * 60
MAX_SESSIONS = 8

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def generate_token() -> str:
    """A 256-bit URL-safe local bearer token."""
    return secrets.token_urlsafe(32)


def _safe_compare(expected: str, supplied: str) -> bool:
    """Constant-time compare that also treats non-ASCII input as a mismatch."""
    try:
        return hmac.compare_digest(expected, supplied)
    except (TypeError, ValueError):
        return False


def _token_matches(expected: str, supplied: str) -> bool:
    return bool(supplied) and _safe_compare(expected, supplied)


def validate_token(value: str) -> str:
    """Validate the token shape without persisting or echoing it."""
    text = (value or "").strip()
    if len(text) < 32:
        raise WebApiError(
            "invalid_token",
            "web token must be at least 32 characters",
            status_code=503,
        )
    try:
        text.encode("ascii")
    except UnicodeEncodeError as exc:
        raise WebApiError(
            "invalid_token",
            "web token must be ASCII",
            status_code=503,
        ) from exc
    return text


def _host_port(value: str, *, field: str) -> tuple[str, int]:
    raw = (value or "").strip()
    if not raw or "\r" in raw or "\n" in raw:
        raise WebApiError("invalid_host", f"invalid {field} header")
    try:
        parsed = urlsplit("//" + raw)
    except ValueError as exc:
        raise WebApiError("invalid_host", f"invalid {field} header") from exc
    if parsed.username is not None or parsed.password is not None:
        raise WebApiError("invalid_host", f"{field} must not contain credentials")
    if parsed.path or parsed.query or parsed.fragment:
        raise WebApiError("invalid_host", f"invalid {field} header")
    hostname = parsed.hostname
    if hostname not in _LOOPBACK_HOSTS:
        raise WebApiError("invalid_host", f"{field} is not a loopback origin")
    try:
        port = parsed.port
    except ValueError as exc:
        raise WebApiError("invalid_host", f"invalid {field} port") from exc
    # HTTP/1.1 omits the port for the default :80.  Any non-default port must be
    # explicit; the comparison below still rejects :80 on a non-80 listener.
    return hostname, int(port if port is not None else 80)


def validate_host(host_header: str, port: int) -> None:
    """Reject DNS-rebinding hosts; only the actual loopback origin is allowed."""
    _hostname, actual = _host_port(host_header, field="Host")
    if actual != int(port):
        raise WebApiError("invalid_host", "Host port does not match the bound port")


def validate_origin(origin: str | None, port: int) -> None:
    """Reject cross-origin browser requests; absent Origin is allowed for CLI."""
    if origin is None:
        return
    raw = origin.strip()
    if not raw or "\r" in raw or "\n" in raw:
        raise WebApiError("origin_rejected", "invalid Origin header", status_code=403)
    try:
        parsed = urlsplit(raw)
    except ValueError as exc:
        raise WebApiError("origin_rejected", "invalid Origin header", status_code=403) from exc
    if parsed.scheme != "http" or parsed.username is not None or parsed.password is not None:
        raise WebApiError("origin_rejected", "Origin is not the local API", status_code=403)
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise WebApiError("origin_rejected", "Origin is not the local API", status_code=403)
    if parsed.hostname not in _LOOPBACK_HOSTS:
        raise WebApiError("origin_rejected", "Origin is not the local API", status_code=403)
    try:
        actual = parsed.port
    except ValueError as exc:
        raise WebApiError("origin_rejected", "invalid Origin port", status_code=403) from exc
    if (actual if actual is not None else 80) != int(port):
        raise WebApiError("origin_rejected", "Origin is not the local API", status_code=403)


@dataclass
class WebSession:
    session_id: str
    created: float
    last_seen: float


class AuthManager:
    """In-memory token/session state for one process.

    Sessions are intentionally not persisted: a restart invalidates every
    browser session.  The bearer token is per-process unless supplied through
    ``DEVRELAY_WEB_TOKEN``.
    """

    def __init__(
        self,
        token: str,
        *,
        port: int,
        session_ttl: float = SESSION_TTL_SECONDS,
        idle_ttl: float = IDLE_TTL_SECONDS,
        max_sessions: int = MAX_SESSIONS,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        value = validate_token(token)
        self._token = value
        self.port = int(port)
        self.session_ttl = float(session_ttl)
        self.idle_ttl = float(idle_ttl)
        self.max_sessions = max(1, int(max_sessions))
        self._monotonic = monotonic
        self._sessions: dict[str, WebSession] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # bearer token
    # ------------------------------------------------------------------
    def matches_token(self, supplied: str) -> bool:
        return _token_matches(self._token, supplied)

    def bearer_identity(self, authorization: str | None) -> bool:
        if not authorization:
            return False
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() != "bearer" or not value.strip():
            return False
        return self.matches_token(value.strip())

    # ------------------------------------------------------------------
    # browser sessions
    # ------------------------------------------------------------------
    def _purge(self, now: float) -> None:
        expired = [
            sid
            for sid, session in self._sessions.items()
            if now - session.created > self.session_ttl
            or now - session.last_seen > self.idle_ttl
        ]
        for sid in expired:
            self._sessions.pop(sid, None)

    def create_session(self) -> WebSession:
        with self._lock:
            now = self._monotonic()
            self._purge(now)
            while len(self._sessions) >= self.max_sessions:
                oldest = min(
                    self._sessions.items(),
                    key=lambda item: item[1].last_seen,
                )[0]
                self._sessions.pop(oldest, None)
            session = WebSession(
                session_id=secrets.token_urlsafe(32),
                created=now,
                last_seen=now,
            )
            self._sessions[session.session_id] = session
            return session

    def resolve_session(self, session_id: str | None) -> WebSession | None:
        if not session_id:
            return None
        with self._lock:
            now = self._monotonic()
            self._purge(now)
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if now - session.created > self.session_ttl:
                self._sessions.pop(session_id, None)
                return None
            if now - session.last_seen > self.idle_ttl:
                self._sessions.pop(session_id, None)
                return None
            session.last_seen = now
            return session

    def delete_session(self, session_id: str | None) -> None:
        if not session_id:
            return
        with self._lock:
            self._sessions.pop(session_id, None)

    def session_count(self) -> int:
        with self._lock:
            self._purge(self._monotonic())
            return len(self._sessions)
