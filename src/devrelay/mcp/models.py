"""DevRelay MCP tool surface (v0.3-B): models and documented bounds.

The MCP layer is an **adapter**: it exposes the already accepted v0.3-A
capabilities (`devrelay.opencode.OpenCodeBridge`) over the Model Context
Protocol so an MCP client (for example a ChatGPT planner) can invoke DevRelay
programmatically.  It never implements transport, retry, orchestration, review
or acceptance logic of its own.

This module owns:

* the stable MCP result envelope (``schema_version = 1``) and its error shape;
* the documented input bounds the adapter enforces before touching the bridge;
* small helpers that bound and sanitize everything that leaves the process.

Dependency direction (v0.3-B): ``devrelay.mcp`` -> ``devrelay.opencode`` and
never the other way round; ``devrelay.opencode`` must not import this package.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from devrelay.redact import redact_text

#: Version of the DevRelay MCP envelope contract (independent of the package
#: version and of the MCP protocol revision).
MCP_SCHEMA_VERSION = 1

#: MCP server identity advertised during initialization.
MCP_SERVER_NAME = "devrelay"
MCP_SERVER_TITLE = "DevRelay OpenCode bridge"

#: Hard, documented MCP-side input bounds (validated before any bridge call).
#: They exist to stop accidental control-plane abuse, not to constrain normal
#: coding prompts: 100k characters is far beyond a realistic prompt while still
#: bounded.
MCP_PROMPT_MAX_CHARS = 100_000
#: Durable call records returned by ``opencode_calls`` per request.
MCP_DEFAULT_CALL_LIMIT = 20
MCP_MAX_CALL_LIMIT = 200
#: Upper bound for a single ``opencode_wait_idle`` request, independent of the
#: workspace configuration (the configured idle timeout is the tighter bound
#: whenever it is smaller).
MCP_MAX_WAIT_SECONDS = 600.0
#: Everything rendered into an envelope message is bounded and redacted.
MCP_MESSAGE_MAX_CHARS = 800


class McpEnvelopeError(BaseModel):
    """Structured, sanitized error carried by a failed envelope."""

    model_config = ConfigDict(extra="forbid")

    type: str
    message: str


class McpEnvelope(BaseModel):
    """The one stable DevRelay MCP result envelope.

    ``ok`` describes *this tool call*, never a softened version of the bridge
    state: an ambiguous submission is ``ok = false`` while
    ``data.submission_uncertain`` / ``data.reply_pending`` keep the nuance the
    caller needs ("do not resubmit automatically").
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: int = MCP_SCHEMA_VERSION
    ok: bool
    tool: str
    data: dict[str, Any] = Field(default_factory=dict)
    error: McpEnvelopeError | None = None


def bounded(text: object, limit: int = MCP_MESSAGE_MAX_CHARS) -> str:
    """Redact secrets from *text* and bound its length for protocol output."""
    if text is None:
        return ""
    return redact_text(str(text))[:limit]


def ok_envelope(tool: str, data: dict[str, Any] | None = None) -> McpEnvelope:
    return McpEnvelope(ok=True, tool=tool, data=data or {}, error=None)


def error_envelope(
    tool: str, error_type: str, message: object, data: dict[str, Any] | None = None
) -> McpEnvelope:
    return McpEnvelope(
        ok=False,
        tool=tool,
        data=data or {},
        error=McpEnvelopeError(type=error_type or "error", message=bounded(message)),
    )


__all__ = [
    "MCP_DEFAULT_CALL_LIMIT",
    "MCP_MAX_CALL_LIMIT",
    "MCP_MAX_WAIT_SECONDS",
    "MCP_MESSAGE_MAX_CHARS",
    "MCP_PROMPT_MAX_CHARS",
    "MCP_SCHEMA_VERSION",
    "MCP_SERVER_NAME",
    "MCP_SERVER_TITLE",
    "McpEnvelope",
    "McpEnvelopeError",
    "bounded",
    "error_envelope",
    "ok_envelope",
]
