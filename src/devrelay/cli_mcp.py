"""``devrelay mcp ...`` - thin registration of the v0.3-B MCP tool surface.

The CLI only parses arguments and hands the bound workspace to
:func:`devrelay.mcp.server.serve`; every MCP concern (envelope, tool schemas,
validation, error boundary, stdio transport) lives in :mod:`devrelay.mcp`.

Deliberately **one** command: the MCP tools are MCP capabilities, not a second
CLI surface, so they are not duplicated here.

Stdout discipline: on stdio the MCP protocol owns stdout, so this module prints
nothing to stdout; failures go to stderr and exit non-zero *before* serving.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer

from devrelay.errors import DevRelayError

mcp_app = typer.Typer(
    help="MCP tool surface (local stdio adapter over the accepted v0.3-A bridge).",
    no_args_is_help=True,
)


@mcp_app.command("serve")
def mcp_serve(
    workspace: Optional[str] = typer.Option(
        None,
        "--workspace",
        help="absolute path of the ONE DevRelay workspace this server is bound to",
    ),
) -> None:
    """Serve the DevRelay MCP tools over stdio (stdout carries MCP only)."""
    from devrelay.mcp.server import McpStartupError, serve

    if not workspace:
        typer.echo(
            "Error: --workspace <absolute path> is required: one MCP server "
            "process is bound to exactly one DevRelay workspace.",
            err=True,
        )
        raise typer.Exit(2)
    try:
        serve(Path(workspace))
    except McpStartupError as exc:
        # Startup failures must be visible on stderr before the MCP handshake;
        # stdout stays clean because no protocol session has started.
        print(f"[devrelay-mcp] {exc}", file=sys.stderr, flush=True)
        raise typer.Exit(2) from exc
    except DevRelayError as exc:  # pragma: no cover - defensive
        print(f"[devrelay-mcp] {exc}", file=sys.stderr, flush=True)
        raise typer.Exit(2) from exc


__all__ = ["mcp_app"]
