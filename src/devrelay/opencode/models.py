"""Normalized OpenCode models owned by DevRelay (v0.3-A).

Nothing outside :mod:`devrelay.opencode` ever sees a raw OpenCode wire object:
the transport parses server payloads and the bridge maps them into these models.
Every textual field is sanitized and capped before it can reach an artifact or
the console (the raw transcript is never persisted).

State vocabulary for one bridge operation (explicit by design):

    ACCEPTED_LOCALLY      the request was validated locally and never issued
    ISSUED                an external request has actually been sent
    IN_FLIGHT             the operation is still running on the server
    COMPLETED             the server reached a terminal/idle outcome
    TIMED_OUT             the bounded wait expired (no retry is attempted)
    INTERRUPTED           an in-flight operation was aborted on request
    PROVIDER_UNAVAILABLE  transport failure / capability unavailable / bad status
    MALFORMED_RESPONSE    the server answered with an unexpected shape
"""

from __future__ import annotations

import hashlib
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from devrelay.models import utcnow_iso

# Caps for everything the server can influence.
MAX_TEXT_CHARS = 8_000
MAX_PARTS = 200
MAX_MESSAGES = 200
MAX_SESSIONS = 500
MAX_TITLE_CHARS = 300
MAX_ID_CHARS = 200
MAX_WORKSPACE_CHARS = 1_024


class OpenCodeSessionState(str, Enum):
    """Normalized session state (unknown server states map to UNKNOWN)."""

    IDLE = "IDLE"
    BUSY = "BUSY"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

    @property
    def terminal(self) -> bool:
        return self in (OpenCodeSessionState.IDLE, OpenCodeSessionState.ERROR)


class OpenCodeOperationState(str, Enum):
    """Explicit lifecycle state of one bridge operation."""

    ACCEPTED_LOCALLY = "ACCEPTED_LOCALLY"
    ISSUED = "ISSUED"
    IN_FLIGHT = "IN_FLIGHT"
    COMPLETED = "COMPLETED"
    TIMED_OUT = "TIMED_OUT"
    INTERRUPTED = "INTERRUPTED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    MALFORMED_RESPONSE = "MALFORMED_RESPONSE"


class OpenCodeCallState(str, Enum):
    """Per-request accounting state (one HTTP request = one call record)."""

    ISSUED = "ISSUED"
    COMPLETED = "COMPLETED"
    TIMED_OUT = "TIMED_OUT"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    MALFORMED_RESPONSE = "MALFORMED_RESPONSE"


def _clean(value: object, limit: int) -> str:
    from devrelay.redact import sanitize

    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return sanitize(value.strip())[:limit]


class OpenCodeHealth(BaseModel):
    """Result of the health probe (capability view, no session data)."""

    model_config = ConfigDict(extra="forbid")

    healthy: bool = False
    version: str = ""
    capabilities: list[str] = Field(default_factory=list)
    detail: str = ""

    def supports(self, capability: str) -> bool:
        return capability in self.capabilities


class OpenCodeSession(BaseModel):
    """One session as DevRelay understands it."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    workspace: str = ""
    workspace_known: bool = False
    workspace_match: bool = False
    title: str = ""
    state: OpenCodeSessionState = OpenCodeSessionState.UNKNOWN
    agent: str = ""
    model: str = ""
    updated_at: str = ""
    parent_id: str = ""

    def selectable(self) -> bool:
        return bool(self.session_id) and self.workspace_match


class OpenCodeMessagePart(BaseModel):
    """One normalized message part (text is sanitized and capped)."""

    model_config = ConfigDict(extra="forbid")

    kind: str = "text"          # text | tool | other
    text: str = ""
    name: str = ""              # tool name only, never tool arguments


class OpenCodeMessage(BaseModel):
    """One normalized message (message identity is the server's id)."""

    model_config = ConfigDict(extra="forbid")

    message_id: str
    role: str = "unknown"       # assistant | user | system | unknown
    created_at: str = ""
    parts: list[OpenCodeMessagePart] = Field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(part.text for part in self.parts if part.text)


class OpenCodeMessagePage(BaseModel):
    """A read window plus its cursor semantics."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = ""
    messages: list[OpenCodeMessage] = Field(default_factory=list)
    next_cursor: str = ""
    cursor_unknown: bool = False   # the requested cursor is no longer available
    replayed: bool = False         # nothing new since the requested cursor


class OpenCodeOperationResult(BaseModel):
    """Uniform outcome of one bridge operation.

    Provider conditions are *returned* here (never raised) so callers cannot
    mistake a timeout or an unavailable server for success.  Configuration bugs
    and ownership violations raise instead (they are programming/user errors,
    not provider states).
    """

    model_config = ConfigDict(extra="forbid")

    operation: str
    state: OpenCodeOperationState
    session_id: str = ""
    call_ids: list[str] = Field(default_factory=list)
    request_count: int = 0
    started_at: str = Field(default_factory=utcnow_iso)
    completed_at: str = ""
    duration_ms: int = 0
    http_status: int | None = None
    error_type: str = ""
    error: str = ""
    health: OpenCodeHealth | None = None
    session: OpenCodeSession | None = None
    sessions: list[OpenCodeSession] = Field(default_factory=list)
    page: OpenCodeMessagePage | None = None
    messages: list[OpenCodeMessage] = Field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.state is OpenCodeOperationState.COMPLETED

    @property
    def terminal(self) -> bool:
        return self.state in (
            OpenCodeOperationState.COMPLETED,
            OpenCodeOperationState.TIMED_OUT,
            OpenCodeOperationState.INTERRUPTED,
            OpenCodeOperationState.PROVIDER_UNAVAILABLE,
            OpenCodeOperationState.MALFORMED_RESPONSE,
            OpenCodeOperationState.ACCEPTED_LOCALLY,
        )


class OpenCodeCallRecord(BaseModel):
    """Accounting for exactly one issued external request.

    The record never contains the prompt text, transcripts, environment values
    or credentials: only identity, state, counts, timing and a prompt hash.
    """

    model_config = ConfigDict(extra="forbid")

    call_id: str
    operation: str
    state: OpenCodeCallState = OpenCodeCallState.ISSUED
    method: str = ""
    path: str = ""
    session_id: str = ""
    issued: bool = True
    external_request_count: int = 1
    http_status: int | None = None
    error_type: str = ""
    error: str = ""
    started_at: str = Field(default_factory=utcnow_iso)
    completed_at: str = ""
    duration_ms: int = 0
    response_bytes: int = 0
    response_truncated: bool = False
    prompt_sha256: str = ""
    prompt_chars: int = 0
    agent: str = ""
    model: str = ""

    @property
    def summary(self) -> str:
        return (
            f"{self.call_id} {self.operation} {self.method} {self.path} "
            f"[{self.state.value}]"
            + (f" http={self.http_status}" if self.http_status is not None else "")
            + (f" {self.error_type}" if self.error_type else "")
        )


def prompt_digest(prompt: str) -> str:
    """Hash of the exact prompt text (the text itself is never persisted)."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()
