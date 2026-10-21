"""`devrelay web` commands: local control API and project registry."""

from __future__ import annotations

import json
import os
import socket
from pathlib import Path
from typing import Optional

import typer

from devrelay.web.auth import TOKEN_ENV, generate_token, validate_token
from devrelay.web.errors import WebApiError
from devrelay.web.registry import Project, ProjectRegistry
from devrelay.web.workspace import resolve_workspace

web_app = typer.Typer(
    name="web",
    help="Local HTTP control API (loopback only).",
    no_args_is_help=True,
)
project_app = typer.Typer(
    name="project",
    help="Explicit project registry for the local API.",
    no_args_is_help=True,
)
web_app.add_typer(project_app, name="project")

_LOOPBACK_BIND = {
    "127.0.0.1": "127.0.0.1",
    "localhost": "127.0.0.1",
    "::1": "::1",
}


def _fail(message: str) -> None:
    typer.echo(f"error: {message}", err=True)
    raise typer.Exit(1)


def _registry(workspace: Optional[Path]) -> ProjectRegistry:
    root, _wiring, devrelay_dir = resolve_workspace(workspace or Path.cwd())
    return ProjectRegistry(devrelay_dir)


def _print_project(project: Project) -> None:
    typer.echo(json.dumps(project.public(), ensure_ascii=False, indent=2))


@project_app.command("add")
def project_add(
    path: Path = typer.Argument(..., help="Absolute path to an initialized workspace"),
    label: str = typer.Option("", "--label", help="Optional display label"),
    workspace: Optional[Path] = typer.Option(
        None, "--workspace", help="Workspace whose registry is edited (default: cwd)"
    ),
) -> None:
    try:
        project = _registry(workspace).add(path, label=label)
    except WebApiError as exc:
        _fail(f"{exc.code}: {exc.message}")
    _print_project(project)


@project_app.command("list")
def project_list(
    workspace: Optional[Path] = typer.Option(
        None, "--workspace", help="Workspace whose registry is read (default: cwd)"
    ),
) -> None:
    try:
        projects = _registry(workspace).list()
    except WebApiError as exc:
        _fail(f"{exc.code}: {exc.message}")
    typer.echo(json.dumps([p.public() for p in projects], ensure_ascii=False, indent=2))


@project_app.command("remove")
def project_remove(
    project_id: str = typer.Argument(..., help="prj_<12 hex> project id"),
    workspace: Optional[Path] = typer.Option(
        None, "--workspace", help="Workspace whose registry is edited (default: cwd)"
    ),
) -> None:
    try:
        _registry(workspace).remove(project_id)
    except WebApiError as exc:
        _fail(f"{exc.code}: {exc.message}")
    typer.echo(f"removed {project_id}")


@web_app.command("serve")
def serve(
    workspace: Optional[Path] = typer.Option(
        None, "--workspace", help="Initialized workspace to serve (default: cwd)"
    ),
    host: str = typer.Option("127.0.0.1", "--host", help="Loopback host"),
    port: int = typer.Option(8765, "--port", min=0, max=65535, help="Port (0 = OS-assigned)"),
) -> None:
    """Serve the read-only local HTTP API until interrupted."""
    bind_host = _LOOPBACK_BIND.get(host.strip().lower())
    if bind_host is None:
        _fail("host must be 127.0.0.1, localhost or ::1")
    workspace_path = workspace or Path.cwd()
    token_from_env = bool(os.environ.get(TOKEN_ENV))
    try:
        token = validate_token(os.environ.get(TOKEN_ENV) or generate_token())
        resolve_workspace(workspace_path)
    except WebApiError as exc:
        _fail(f"{exc.code}: {exc.message}")

    try:
        from devrelay.web.app import create_app
        import uvicorn
    except ImportError:  # pragma: no cover - depends on environment
        _fail(
            "the web extra is not installed; install it with: "
            "python -m pip install 'devrelay[web]'"
        )

    sock = socket.socket(
        socket.AF_INET6 if ":" in bind_host else socket.AF_INET,
        socket.SOCK_STREAM,
    )
    try:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind_host, port))
        sock.listen(2048)
        actual_port = int(sock.getsockname()[1])
    except OSError as exc:
        sock.close()
        _fail(f"could not bind {bind_host}:{port} ({exc.strerror or exc.__class__.__name__})")

    try:
        app = create_app(str(workspace_path), port=actual_port, token=token)
    except WebApiError as exc:
        sock.close()
        _fail(f"{exc.code}: {exc.message}")
    except BaseException:
        sock.close()
        raise

    display_host = "[::1]" if ":" in bind_host else bind_host
    if token_from_env:
        typer.echo(f"DevRelay web: http://{display_host}:{actual_port}/ (DEVRELAY_WEB_TOKEN)")
    else:
        typer.echo(f"DevRelay web: http://{display_host}:{actual_port}/#token={token}")

    config = uvicorn.Config(
        app,
        host=bind_host,
        port=actual_port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    try:
        server.run(sockets=[sock])
    except KeyboardInterrupt:  # pragma: no cover - interactive shutdown
        server.should_exit = True
    finally:
        sock.close()
