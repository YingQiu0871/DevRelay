"""`devrelay opencode ...` — thin CLI wrappers over the v0.3-A bridge.

The CLI only parses arguments and prints the bridge's normalized results; all
OpenCode knowledge (endpoint, wire shapes, ownership validation, accounting,
timeouts) lives in :mod:`devrelay.opencode`.  Nothing here retries, orchestrates
or decides anything.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer

from devrelay.config import OpenCodeConfig
from devrelay.errors import DevRelayError, OpenCodeConfigError
from devrelay.opencode import OpenCodeBridge
from devrelay.opencode.models import OpenCodeOperationResult

opencode_app = typer.Typer(
    help="OpenCode session bridge (explicit endpoint, explicit session).",
    no_args_is_help=True,
)

ENV_TOKEN = "DEVRELAY_OPENCODE_TOKEN"


def _bridge(root: Path, wiring) -> OpenCodeBridge:
    """Build the bridge from live wiring; the token comes from the environment."""
    config: OpenCodeConfig = wiring.opencode
    if not config.configured:
        raise OpenCodeConfigError(
            "opencode.base_url is not configured in .devrelay/config.yaml; "
            "DevRelay never discovers servers by scanning ports or processes"
        )
    import os

    return OpenCodeBridge(
        base_url=config.base_url,
        workspace_root=config.workspace or root,
        token=os.environ.get(ENV_TOKEN, ""),
        timeout_seconds=config.timeout_seconds,
        idle_timeout_seconds=config.idle_timeout_seconds,
        poll_interval_seconds=config.poll_interval_seconds,
        max_response_bytes=config.max_response_bytes,
        max_messages=config.max_messages,
        allow_unknown_workspace=config.allow_unknown_workspace,
        devrelay_dir=root / ".devrelay",
    )


def _emit(result: OpenCodeOperationResult, *, json_output: bool) -> None:
    if json_output:
        typer.echo(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))
        return
    typer.echo(f"{result.operation}: {result.state.value}")
    if result.session_id:
        typer.echo(f"  session    {result.session_id}")
    if result.call_ids:
        typer.echo(f"  calls      {', '.join(result.call_ids)}")
        typer.echo(f"  requests   {result.request_count}")
    if result.error_type:
        typer.echo(f"  error      {result.error_type}: {result.error}")
    if result.health is not None:
        typer.echo(
            f"  health     {'ok' if result.health.healthy else 'degraded'}"
            + (f" (version {result.health.version})" if result.health.version else "")
        )
        if result.health.capabilities:
            typer.echo(f"  caps       {', '.join(result.health.capabilities)}")
    if result.sessions:
        typer.echo(f"  sessions   {len(result.sessions)}")
        for session in result.sessions:
            flag = "ok" if session.workspace_match else "other-workspace"
            typer.echo(
                f"    - {session.session_id} [{session.state.value}] {flag}"
                + (f" {session.title}" if session.title else "")
            )
    if result.session is not None:
        session = result.session
        typer.echo(f"  state      {session.state.value}")
        typer.echo(f"  workspace  {session.workspace or '(not reported)'}")
        if session.title:
            typer.echo(f"  title      {session.title}")
    if result.page is not None:
        page = result.page
        typer.echo(
            f"  messages   {len(page.messages)}"
            + (" (cursor unknown: full window returned)" if page.cursor_unknown else "")
            + (" (no new messages)" if page.replayed else "")
        )
        typer.echo(f"  cursor     {page.next_cursor or '-'}")
    for message in result.messages:
        text = message.text
        typer.echo(f"  [{message.role}] {message.message_id}")
        for line in (text or "").splitlines():
            typer.echo(f"    {line}")
    if not result.ok:
        raise typer.Exit(2)


@opencode_app.command("health")
def opencode_health(
    json_output: bool = typer.Option(False, "--json", help="raw normalized JSON"),
) -> None:
    """Probe the configured OpenCode server (no session data)."""
    from devrelay.cli import _load_wiring, _resolve_root

    root = _resolve_root()
    try:
        result = _bridge(root, _load_wiring(root)).health()
    except DevRelayError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
    _emit(result, json_output=json_output)


@opencode_app.command("sessions")
def opencode_sessions(
    all_workspaces: bool = typer.Option(
        False, "--all-workspaces", help="also list sessions from other workspaces"
    ),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """List OpenCode sessions with their ownership verdict."""
    from devrelay.cli import _load_wiring, _resolve_root

    root = _resolve_root()
    try:
        result = _bridge(root, _load_wiring(root)).list_sessions(
            include_other_workspaces=all_workspaces
        )
    except DevRelayError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
    _emit(result, json_output=json_output)


@opencode_app.command("show")
def opencode_show(
    session: Optional[str] = typer.Option(None, "--session", help="session id"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Read one explicitly selected session (ownership validated)."""
    from devrelay.cli import _load_wiring, _resolve_root

    root = _resolve_root()
    wiring = _load_wiring(root)
    session_id = session or wiring.opencode.default_session
    try:
        result = _bridge(root, wiring).get_session(session_id or "")
    except DevRelayError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
    _emit(result, json_output=json_output)


@opencode_app.command("read")
def opencode_read(
    session: Optional[str] = typer.Option(None, "--session"),
    cursor: Optional[str] = typer.Option(None, "--cursor", help="last message id"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Read the normalized message window (cursor semantics are explicit)."""
    from devrelay.cli import _load_wiring, _resolve_root

    root = _resolve_root()
    wiring = _load_wiring(root)
    session_id = session or wiring.opencode.default_session
    try:
        result = _bridge(root, wiring).read_messages(session_id or "", cursor)
    except DevRelayError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
    _emit(result, json_output=json_output)


@opencode_app.command("send")
def opencode_send(
    prompt: str = typer.Option(..., "--prompt", help="prompt text, or '-' for stdin"),
    session: Optional[str] = typer.Option(None, "--session"),
    agent: str = typer.Option("", "--agent"),
    model: str = typer.Option("", "--model"),
    wait: bool = typer.Option(
        False, "--wait", help="wait for idle/terminal after sending (bounded)"
    ),
    timeout: Optional[float] = typer.Option(None, "--timeout", help="idle wait seconds"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Send exactly one prompt to one explicitly selected session."""
    from devrelay.cli import _load_wiring, _resolve_root

    root = _resolve_root()
    wiring = _load_wiring(root)
    session_id = session or wiring.opencode.default_session
    text = sys.stdin.read() if prompt == "-" else prompt
    bridge = _bridge(root, wiring)
    try:
        result = bridge.send_prompt(
            session_id or "",
            text,
            agent=agent or wiring.opencode.agent,
            model=model or wiring.opencode.model,
        )
    except DevRelayError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
    _emit(result, json_output=json_output)
    if wait and result.ok:
        waited = bridge.wait_idle(session_id or "", timeout)
        _emit(waited, json_output=json_output)
        if waited.ok:
            fresh = bridge.read_messages(session_id or "", result.messages[-1].message_id if result.messages else None)
            _emit(fresh, json_output=json_output)


@opencode_app.command("wait")
def opencode_wait(
    session: Optional[str] = typer.Option(None, "--session"),
    timeout: Optional[float] = typer.Option(None, "--timeout", help="bounded seconds"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Wait (bounded) for the session to become idle or terminal."""
    from devrelay.cli import _load_wiring, _resolve_root

    root = _resolve_root()
    wiring = _load_wiring(root)
    session_id = session or wiring.opencode.default_session
    try:
        result = _bridge(root, wiring).wait_idle(session_id or "", timeout)
    except DevRelayError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
    _emit(result, json_output=json_output)


@opencode_app.command("interrupt")
def opencode_interrupt(
    session: Optional[str] = typer.Option(None, "--session"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Interrupt an in-flight operation (only when the server supports it)."""
    from devrelay.cli import _load_wiring, _resolve_root

    root = _resolve_root()
    wiring = _load_wiring(root)
    session_id = session or wiring.opencode.default_session
    try:
        result = _bridge(root, wiring).interrupt(session_id or "")
    except DevRelayError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
    _emit(result, json_output=json_output)


@opencode_app.command("calls")
def opencode_calls(
    limit: int = typer.Option(20, "--limit", help="most recent records"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Show the durable OpenCode call ledger (accounting evidence)."""
    from devrelay.artifacts.store import ArtifactStore
    from devrelay.cli import _resolve_root
    from devrelay.opencode.accounting import FilesystemOpenCodeLedger

    root = _resolve_root()
    store = ArtifactStore(root)
    ledger = FilesystemOpenCodeLedger(store.devrelay_dir)
    records = ledger.read_records()[-max(1, limit) :]
    if json_output:
        typer.echo(
            json.dumps([r.model_dump(mode="json") for r in records], indent=2, ensure_ascii=False)
        )
        return
    if not records:
        typer.echo("(no OpenCode calls recorded)")
        return
    for record in records:
        typer.echo(record.summary)
        if record.error:
            typer.echo(f"    {record.error[:300]}")
