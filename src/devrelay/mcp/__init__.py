"""DevRelay MCP tool surface (v0.3-B).

A narrow adapter that exposes the accepted v0.3-A OpenCode bridge capabilities
over the Model Context Protocol (local stdio transport) so an MCP client - for
example a ChatGPT planner - can invoke DevRelay programmatically.

Boundary (v0.3-B):

* the MCP layer is an **adapter**, never an engine: no orchestration, no role
  routing, no review/fix loops, no approval or acceptance authority, no retries
  or model fallbacks of its own;
* it reuses :class:`devrelay.opencode.bridge.OpenCodeBridge` exactly as accepted
  in v0.3-A (one submission POST, submission-uncertainty semantics, stale-reply
  suppression, durable accounting, credential/prompt containment);
* one MCP server process is bound to exactly one workspace, resolved once at
  startup; no tool accepts a workspace path;
* the optional ``mcp`` dependency is imported only when a server is actually
  built, so importing :mod:`devrelay` never requires it.

The OpenCode package must not import this package (dependency direction:
``devrelay.mcp`` -> ``devrelay.opencode``).
"""

from __future__ import annotations

from devrelay.mcp.models import (
    MCP_SCHEMA_VERSION,
    MCP_SERVER_NAME,
    McpEnvelope,
    McpEnvelopeError,
)

__all__ = [
    "MCP_SCHEMA_VERSION",
    "MCP_SERVER_NAME",
    "McpEnvelope",
    "McpEnvelopeError",
]
