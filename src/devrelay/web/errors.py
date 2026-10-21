"""Bounded HTTP-facing errors for the local control API."""

from __future__ import annotations

from devrelay.redact import redact_text


class WebApiError(Exception):
    """One bounded, client-safe HTTP failure.

    The message is deliberately short and redacted at construction time; no
    traceback or upstream payload is ever attached.
    """

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.code = code
        self.message = redact_text(message or code)[:300]
        self.status_code = int(status_code)
        self.headers = dict(headers or {})
        super().__init__(self.message)


class WebDependencyError(WebApiError):
    """The optional web extra is not installed."""

    def __init__(self, message: str) -> None:
        super().__init__("web_dependency_missing", message, status_code=503)
