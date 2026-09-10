"""DevRelay command-line interface.

Everything user-facing goes through here.  Raw subprocesses are never started
in this module — providers and the workspace abstraction own execution.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import typer
from pydantic import ValidationError

from devrelay import __version__
from devrelay.artifacts.store import ArtifactStore
from devrelay.baseline.service import BaselineService
from devrelay.config import (
    DevRelayConfig,
    install_default_config,
    load_config,
)
from devrelay.errors import (
    BaselineError,
    ConfigError,
    DevRelayError,
    ProviderUnavailableError,
    TaskNotFoundError,
)
from devrelay.models import ReviewResult, TaskPacket
from devrelay.pipeline.engine import DevRelayEngine
from devrelay.providers.base import ImplementerProvider, ReviewerProvider
from devrelay.providers.codex_cli import CodexCLIProvider
from devrelay.providers.manual import ManualReviewer
from devrelay.providers.openai_compatible import OpenAICompatibleReviewer, endpoint_from_env
from devrelay.workspace.discovery import require_root
from devrelay.workspace.git import GitWorkspace
from devrelay.workspace.runner import CommandRunner

app = typer.Typer(
    name="devrelay",
    help=(
        "DevRelay - Plan with one model, build with Codex, review with "
        "another - without copy-pasting between agents."
    ),
    add_completion=False,
    no_args_is_help=True,
)


def _fail(message: str) -> None:
    typer.echo(f"Error: {message}", err=True)
    raise typer.Exit(1)


def _unexpected(exc: Exception) -> None:
    if os.environ.get("DEVRELAY_DEBUG"):
        raise exc
    _fail(f"unexpected error: {exc}")


# ---------------------------------------------------------------------------
# shared context helpers
# ---------------------------------------------------------------------------

def _resolve_root() -> Path:
    try:
        return require_root(Path.cwd())
    except DevRelayError as exc:
        _fail(str(exc))


def _load_store_config(root: Path) -> tuple[ArtifactStore, DevRelayConfig]:
    store = ArtifactStore(root)
    if not store.is_initialized():
        _fail(f"DevRelay is not initialized in {root}; run 'devrelay init' first")
    config_path = root / ".devrelay" / "config.yaml"
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        _fail(str(exc))
    return store, config


def _task_id(store: ArtifactStore, explicit: str | None) -> str:
    if explicit:
        return explicit
    current = store.current_task_id()
    if not current:
        _fail("no task exists yet; run 'devrelay start \"<title>\"' first")
    return current


def _engine(
    root: Path,
    store: ArtifactStore,
    config: DevRelayConfig,
    *,
    reviewer_required: bool = False,
) -> DevRelayEngine:
    runner = CommandRunner()
    workspace = GitWorkspace(root, runner)
    implementer = CodexCLIProvider(config.codex, runner, workspace_root=root)
    reviewer: ReviewerProvider
    if config.review.provider == "openai_compatible":
        try:
            reviewer = OpenAICompatibleReviewer(
                endpoint_from_env(timeout_seconds=config.review.timeout_seconds),
                retries=config.review.retries,
            )
        except ProviderUnavailableError:
            if reviewer_required:
                raise
            reviewer = ManualReviewer()
    else:
        reviewer = ManualReviewer()
    baseline_service = BaselineService(root, runner, store, config)
    return DevRelayEngine(
        config,
        store,
        workspace,
        implementer=implementer,
        reviewer=reviewer,
        runner=runner,
        baselines=baseline_service,
    )


def _require_reviewing_task(store: ArtifactStore, explicit: str | None) -> str:
    task_id = _task_id(store, explicit)
    try:
        task = store.read_task(task_id)
    except TaskNotFoundError as exc:
        _fail(str(exc))
    if task.state.value != "REVIEWING":
        _fail(
            f"task {task_id} is in state {task.state.value}; expected REVIEWING"
        )
    return task_id


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

@app.command()
def version() -> None:
    """Show the DevRelay version."""
    typer.echo(f"devrelay {__version__}")


@app.command()
def init() -> None:
    """Initialize DevRelay in the current git repository."""
    cwd = Path.cwd().resolve()

    # Already inside an initialized workspace?
    from devrelay.workspace.discovery import find_root

    existing = find_root(cwd)
    if existing and (existing / ".devrelay").is_dir():
        _fail(f"DevRelay is already initialized at {existing}")

    runner = CommandRunner()
    repo_root = cwd
    probe = runner.run(
        ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"], timeout_seconds=30
    )
    if probe.success and probe.stdout.strip():
        repo_root = Path(probe.stdout.strip())
    else:
        typer.echo(
            "Warning: current directory is not inside a git repository; "
            "initializing here anyway (tasks require git to start).",
            err=True,
        )
    store = ArtifactStore(repo_root)
    store.ensure_initialized()
    config_path = install_default_config(repo_root / ".devrelay" / "config.yaml")
    typer.echo(f"Initialized DevRelay v{__version__} at {repo_root}")
    typer.echo(f"Config: {config_path}")
    typer.echo("Next: devrelay start \"<task title>\"")


@app.command()
def doctor() -> None:
    """Diagnose the environment (Codex CLI, git, reviewer env)."""
    try:
        root = require_root(Path.cwd())
    except DevRelayError as exc:
        _fail(str(exc))
    store, config = _load_store_config(root)
    typer.echo(f"Workspace: {root}")
    typer.echo(f"Config: {root / '.devrelay' / 'config.yaml'}")
    ws = GitWorkspace(root)
    typer.echo(f"Git repo: {ws.detect_repo()}")
    codex = CodexCLIProvider(config.codex, CommandRunner(), workspace_root=root)
    ok, diagnostic = codex.availability()
    typer.echo(f"Codex CLI: {'OK' if ok else 'MISSING'} — {diagnostic}")
    typer.echo(
        f"  Args: {' '.join(config.codex.args)} "
        f"(prompt transport: {config.codex.prompt_mode})"
    )
    for warning in codex.unknown_arg_warnings():
        typer.echo(f"  Warning: {warning}")
    typer.echo(f"Reviewer provider: {config.review.provider}")
    if config.review.provider == "openai_compatible":
        from devrelay.providers.openai_compatible import (
            ENV_API_KEY,
            ENV_BASE_URL,
            ENV_MODEL,
        )

        typer.echo(f"  {ENV_BASE_URL}: {'set' if os.environ.get(ENV_BASE_URL) else 'unset (default)'}")
        typer.echo(f"  {ENV_MODEL}: {'set' if os.environ.get(ENV_MODEL) else 'unset (default)'}")
        typer.echo(f"  {ENV_API_KEY}: {'set' if os.environ.get(ENV_API_KEY) else 'MISSING'}")
    typer.echo(f"Tasks: {len(store.list_task_ids())}")


@app.command()
def start(title: str = typer.Argument(..., help="Short task title")) -> None:
    """Create a new task (state PLAN_REQUIRED)."""
    root = _resolve_root()
    store, config = _load_store_config(root)
    ws = GitWorkspace(root)
    if not ws.detect_repo():
        _fail(
            f"{root} is not a git repository — DevRelay tasks require git "
            "(run 'git init' first)."
        )
    engine = _engine(root, store, config)
    try:
        task = engine.create_task(title)
    except BaselineError as exc:
        _fail(str(exc))
    typer.echo(f"Created task {task.task_id}: {task.title}")
    typer.echo(f"State: {task.state.value}")
    typer.echo(f"Task dir: {store.task_dir(task.task_id)}")
    typer.echo("Next: edit the task.md and run 'devrelay plan import task.md'")


@app.command()
def status(
    task: Optional[str] = typer.Option(None, "--task", help="Task id (default: current)"),
) -> None:
    """Show the current task and stage status."""
    root = _resolve_root()
    store, _config = _load_store_config(root)
    task_id = _task_id(store, task)
    try:
        run = store.read_task(task_id)
    except TaskNotFoundError as exc:
        _fail(str(exc))
    engine = _engine(root, store, _config)
    block = engine.status_block(task_id)
    typer.echo("DevRelay")
    typer.echo("")
    typer.echo(f"Task: {task_id}")
    typer.echo(f"Title: {run.title}")
    typer.echo("")
    typer.echo(f"State: {block['state']}")
    typer.echo(f"Iteration: {block['iteration']}")
    typer.echo("")
    for label, key in (
        ("Planner", "planner"),
        ("Implementer", "implementer"),
        ("Tests", "tests"),
        ("Reviewer", "reviewer"),
        ("Final Gate", "final_gate"),
        ("Baseline", "baseline"),
        ("Attempt", "attempt"),
    ):
        typer.echo(f"{label:<12} {block[key]}")
    if block["blocked"]:
        reason = run.blocked_reason or ""
        typer.echo("")
        typer.echo(f"Blocked ({block['blocked']}): {reason}")
        typer.echo("Recovery: 'devrelay unblock --reason \"...\"'")


plan_app = typer.Typer(help="Task Packet planning commands.", no_args_is_help=True)
app.add_typer(plan_app, name="plan")


@plan_app.command("show")
def plan_show(
    task: Optional[str] = typer.Option(None, "--task"),
) -> None:
    """Show the current task.md."""
    root = _resolve_root()
    store, _config = _load_store_config(root)
    task_id = _task_id(store, task)
    md_path = store.task_dir(task_id) / "task.md"
    if not md_path.is_file():
        _fail(f"no task.md for {task_id}")
    typer.echo(md_path.read_text(encoding="utf-8"))


@plan_app.command("import")
def plan_import(
    file: Path = typer.Argument(..., help="task.md or task.json to import"),
    task: Optional[str] = typer.Option(None, "--task"),
) -> None:
    """Import a Task Packet (state -> PLAN_READY)."""
    root = _resolve_root()
    store, config = _load_store_config(root)
    task_id = _task_id(store, task)
    if not file.is_file():
        _fail(f"file not found: {file}")
    engine = _engine(root, store, config)
    try:
        if file.suffix.lower() == ".json":
            raw = json.loads(file.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                _fail("plan JSON must be an object")
            raw.setdefault("task_id", task_id)
            packet = TaskPacket.model_validate(raw)
        else:
            packet = _parse_task_markdown_safe(file.read_text(encoding="utf-8"), task_id)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        _fail(f"invalid plan file: {exc}")
    try:
        run = engine.import_plan(task_id, packet)
    except DevRelayError as exc:
        _fail(str(exc))
    typer.echo(f"Plan imported for {run.task_id} — state {run.state.value}")
    typer.echo("Next: 'devrelay continue'")


def _parse_task_markdown_safe(text: str, task_id: str) -> TaskPacket:
    from devrelay.artifacts.renderer import parse_task_markdown

    return parse_task_markdown(text, task_id)


@app.command(name="continue")
def continue_task(
    task: Optional[str] = typer.Option(None, "--task"),
) -> None:
    """Run the next pipeline stage(s) for the current task."""
    root = _resolve_root()
    store, config = _load_store_config(root)
    task_id = _task_id(store, task)
    try:
        engine = _engine(root, store, config, reviewer_required=True)
        events = engine.continue_task(task_id)
    except DevRelayError as exc:
        _fail(str(exc))
    for line in events:
        typer.echo(line)
    state = store.read_task(task_id).state.value
    typer.echo(f"[{task_id}] state: {state}")
    if any(line.endswith("-> FIX_REQUIRED") for line in events):
        typer.echo(f"[{task_id}] next: 'devrelay continue' to run the fix pass")
    if any(line.startswith(f"[{task_id}] ERROR") for line in events):
        raise typer.Exit(1)
    if state in ("BLOCKED", "FAILED"):
        raise typer.Exit(1)


@app.command()
def diff(
    stat: bool = typer.Option(False, "--stat", help="show diffstat only"),
    binary: bool = typer.Option(
        False, "--binary", help="emit the binary-safe task patch instead"
    ),
    out: Optional[Path] = typer.Option(
        None, "--out", help="write the (binary) task patch to a file"
    ),
    task: Optional[str] = typer.Option(None, "--task"),
) -> None:
    """Show the TASK-RELATIVE diff (task baseline -> current workspace)."""
    root = _resolve_root()
    store, config = _load_store_config(root)
    task_id = _task_id(store, task)
    engine = _engine(root, store, config)
    try:
        if binary:
            content = engine.task_binary_diff(task_id)
            if out is not None:
                store.write_text(out, content)
                typer.echo(f"Binary task patch written: {out}")
                return
        elif out is not None:
            _fail("--out requires --binary")
        else:
            content = engine.task_diff_text(task_id, stat=stat)
    except BaselineError as exc:
        _fail(str(exc))
    typer.echo(content)


@app.command()
def logs(
    task: Optional[str] = typer.Option(None, "--task"),
) -> None:
    """List task log files (codex/test runs)."""
    root = _resolve_root()
    store, _config = _load_store_config(root)
    task_id = _task_id(store, task)
    log_dir = store.logs_dir(task_id)
    names = store.list_dir(log_dir)
    if not names:
        typer.echo(f"no logs yet for {task_id}")
        return
    for name in names:
        typer.echo(f"{task_id}/logs/{name}")


review_app = typer.Typer(help="Manual review handoff.", no_args_is_help=True)
app.add_typer(review_app, name="review")


@review_app.command("export")
def review_export(
    task: Optional[str] = typer.Option(None, "--task"),
) -> None:
    """Write the manual review request for the current REVIEWING task."""
    root = _resolve_root()
    store, config = _load_store_config(root)
    task_id = _require_reviewing_task(store, task)
    engine = _engine(root, store, config)
    try:
        path = engine.export_review_request(task_id)
    except DevRelayError as exc:
        _fail(str(exc))
    typer.echo(f"Review request: {path}")


@review_app.command("import")
def review_import(
    file: Path = typer.Argument(..., help="review result JSON"),
    task: Optional[str] = typer.Option(None, "--task"),
) -> None:
    """Import a manual review JSON result."""
    root = _resolve_root()
    store, config = _load_store_config(root)
    task_id = _require_reviewing_task(store, task)
    if not file.is_file():
        _fail(f"file not found: {file}")
    try:
        raw = json.loads(file.read_text(encoding="utf-8"))
        review = ReviewResult.model_validate(raw)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        _fail(f"invalid review file: {exc}")
    engine = _engine(root, store, config)
    try:
        events = engine.import_manual_review(task_id, review)
    except DevRelayError as exc:
        _fail(str(exc))
    for line in events:
        typer.echo(line)
    state = store.read_task(task_id).state.value
    typer.echo(f"[{task_id}] state: {state}")


final_app = typer.Typer(help="Final gate commands.", no_args_is_help=True)
app.add_typer(final_app, name="final")


@final_app.command("export")
def final_export(
    task: Optional[str] = typer.Option(None, "--task"),
) -> None:
    """Generate the final human review package."""
    root = _resolve_root()
    store, config = _load_store_config(root)
    task_id = _task_id(store, task)
    engine = _engine(root, store, config)
    try:
        path = engine.export_final(task_id)
    except DevRelayError as exc:
        _fail(str(exc))
    typer.echo(f"Final gate package: {path}")


@final_app.command("approve")
def final_approve(
    note: str = typer.Option("", "--note", help="Gate approval note"),
    task: Optional[str] = typer.Option(None, "--task"),
) -> None:
    """Approve the final gate (task -> DONE, report.md written)."""
    root = _resolve_root()
    store, config = _load_store_config(root)
    task_id = _task_id(store, task)
    engine = _engine(root, store, config)
    try:
        run = engine.approve_final(task_id, note=note)
    except DevRelayError as exc:
        _fail(str(exc))
    typer.echo(f"Final gate approved — {run.task_id} is DONE")
    typer.echo(f"Report: {store.final_dir(task_id) / 'report.md'}")


@app.command()
def unblock(
    reason: str = typer.Option(..., "--reason", prompt=True, help="Required human reason"),
    to: Optional[str] = typer.Option(
        None, "--to", help="plan | implement | fix | review (default: by block code)"
    ),
    task: Optional[str] = typer.Option(None, "--task"),
) -> None:
    """Manually recover a BLOCKED/FAILED task (never skips findings silently)."""
    root = _resolve_root()
    store, config = _load_store_config(root)
    task_id = _task_id(store, task)
    engine = _engine(root, store, config)
    try:
        run = engine.unblock(task_id, reason=reason, to=to)
    except DevRelayError as exc:
        _fail(str(exc))
    typer.echo(f"{task_id} unblocked -> {run.state.value} (reason: {reason})")
    if run.state.value in ("FIX_REQUIRED", "IMPLEMENTING"):
        typer.echo("Next: 'devrelay continue' (manual override recorded in audit)")


def main() -> None:
    try:
        app()
    except typer.Exit:
        raise
    except Exception as exc:  # last-resort guard (never prints secrets raw)
        _unexpected(exc)


if __name__ == "__main__":
    main()
