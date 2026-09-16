"""DevRelay command-line interface.

Everything user-facing goes through here.  Raw subprocesses are never started
in this module — providers and the workspace abstraction own execution.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import yaml
from typing import Optional

import typer
from pydantic import ValidationError

from devrelay import __version__
from devrelay.artifacts.store import ArtifactStore
from devrelay.baseline.service import BaselineService
from devrelay.config import (
    DevRelayConfig,
    PolicyDocument,
    ResolvedPolicy,
    WiringConfig,
    dump_policy_yaml,
    install_default_config,
    load_config,
    load_wiring_config,
    workspace_policy_overrides,
)
from devrelay.profiles import (
    PROFILE_NAME_PATTERN,
    load_profile,
    PROFILE_SUFFIX,
    discover_profiles,
    inspect_profile,
    profiles_dir,
    resolve_policy_config,
    validate_profiles,
)
from devrelay.errors import (
    BaselineError,
    ConfigError,
    DevRelayError,
    PolicyLiveResolutionFailedError,
    PolicyRefreshNotAllowedError,
    ProviderUnavailableError,
    TaskNotFoundError,
)
from devrelay.snapshot import SnapshotState, check_snapshot, snapshot_error
from devrelay.models import SNAPSHOT_ERA_SCHEMA
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

def _echo_control_plane_holds(holds: list) -> None:
    """Print control-plane hold records (metadata only, never file contents)."""
    typer.echo("CONTROL-PLANE HOLD — DevRelay authoritative state was modified")
    typer.echo("")
    for hold in holds:
        typer.echo(f"Task: {hold.get('task_id')}")
        typer.echo(f"  code:      {hold.get('code')}")
        typer.echo(f"  attempt:   {hold.get('attempt_id')}")
        typer.echo(f"  detected:  {hold.get('created_at')}")
        paths = hold.get("diverging_paths") or []
        if paths:
            typer.echo("  changed:   " + ", ".join(str(p) for p in paths[:10]))
        if hold.get("violation_report"):
            typer.echo(f"  report:    {hold['violation_report']}")
        if hold.get("corrupt"):
            typer.echo("  (the hold record itself is unreadable)")
    typer.echo("")
    typer.echo(
        "Protected state must match the trusted PRE identity again before "
        "anything may run:"
    )
    typer.echo(
        "  devrelay unblock --reason \"...\" --acknowledge-control-plane-violation"
    )
    typer.echo(
        "  (optionally --restore-state-from-pre when a parent-held copy exists)"
    )
    typer.echo("")


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


def _read_task(store: ArtifactStore, task_id: str):
    """Read task state, turning any state problem into a clean CLI failure.

    Covers the dedicated ``state_schema_too_new`` diagnostic: state written by a
    newer DevRelay is reported, never traced back as a pydantic error.
    """
    try:
        return store.read_task(task_id)
    except DevRelayError as exc:
        _fail(str(exc))


def _task_id(store: ArtifactStore, explicit: str | None) -> str:
    if explicit:
        return explicit
    current = store.current_task_id()
    if not current:
        _fail("no task exists yet; run 'devrelay start \"<title>\"' first")
    return current


def _store(root: Path) -> ArtifactStore:
    """Initialized artifact store for *root* (no configuration is read)."""
    store = ArtifactStore(root)
    if not store.is_initialized():
        _fail(f"DevRelay is not initialized in {root}; run 'devrelay init' first")
    return store


def _raw_config_mapping(path: Path) -> dict:
    """Raw top-level keys of the workspace config (no validation, no profiles)."""
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _load_wiring(root: Path) -> WiringConfig:
    """Live runtime wiring only - never validates live policy sections."""
    try:
        return load_wiring_config(root / ".devrelay" / "config.yaml")
    except ConfigError as exc:
        _fail(str(exc))


def _display_policy_provider(root: Path):
    """Lazy *display* policy for legacy tasks (never touches profile files).

    Read-only commands pass this to the engine; it is only called for a task
    that has no frozen snapshot at all, and a malformed live policy override
    degrades to "no limits shown" instead of failing the command.
    """

    def _provide() -> PolicyDocument | None:
        try:
            return PolicyDocument.from_workspace_config(
                load_config(root / ".devrelay" / "config.yaml")
            )
        except (ConfigError, OSError):
            return None

    return _provide


def _engine(
    root: Path,
    store: ArtifactStore,
    config: DevRelayConfig | None,
    *,
    reviewer_required: bool = False,
    policy: ResolvedPolicy | None = None,
    wiring: WiringConfig | None = None,
    display_policy: bool = False,
) -> DevRelayEngine:
    runner = CommandRunner()
    workspace = GitWorkspace(root, runner)
    if wiring is None:
        wiring = WiringConfig.from_workspace_config(config) if config is not None else WiringConfig()
    # Reviewer construction-time defaults come from the resolved task policy when
    # one is available.  The engine always passes the frozen per-call
    # ReviewCallPolicy, so these values are fallbacks for direct provider use
    # only - never the policy the pipeline runs under.
    if policy is not None:
        policy_view = policy.document
    elif config is not None:
        policy_view = PolicyDocument.from_workspace_config(config)
    else:
        # Wiring-only commands (status/usage/diff/logs) never execute a policy:
        # the baseline service is constructed with defaults because it only
        # *reads* an already-captured baseline here, and every valid policy
        # hard-disables the git guard flags it consults.
        policy_view = PolicyDocument()
    implementer = CodexCLIProvider(wiring.codex, runner, workspace_root=root)
    reviewer: ReviewerProvider
    if wiring.review_provider == "openai_compatible":
        try:
            reviewer = OpenAICompatibleReviewer(
                endpoint_from_env(timeout_seconds=policy_view.review.timeout_seconds),
                retries=policy_view.review.retries,
            )
        except ProviderUnavailableError:
            if reviewer_required:
                raise
            reviewer = ManualReviewer()
    else:
        reviewer = ManualReviewer()
    baseline_service = BaselineService(root, runner, store, policy_view)
    return DevRelayEngine(
        config,
        store,
        workspace,
        implementer=implementer,
        reviewer=reviewer,
        runner=runner,
        baselines=baseline_service,
        runtime_config=wiring,
        fallback_policy_config=policy,
        policy_view_provider=_display_policy_provider(root) if display_policy else None,
    )


def _task_engine(
    root: Path,
    store: ArtifactStore,
    task_id: str,
    *,
    fail_closed: bool = True,
) -> DevRelayEngine:
    """Engine for a command that acts on an existing task.

    Guardrail: the task's snapshot is classified *before* any provider object is
    constructed, so a missing/invalid/mismatched snapshot fails closed without a
    Codex or reviewer client ever being built.  A task with a valid frozen
    snapshot never has its live policy validated and never reads a profile; a
    legacy task resolves its live policy explicitly.
    """
    check = check_snapshot(store, _read_task(store, task_id))
    damaged = check.state in (
        SnapshotState.MISSING,
        SnapshotState.INVALID,
        SnapshotState.HASH_MISMATCH,
    )
    wiring = _load_wiring(root)
    if damaged:
        if fail_closed:
            _fail(str(snapshot_error(check)))
        return _engine(
            root, store, None, wiring=wiring, display_policy=True
        )
    if check.state is not SnapshotState.LEGACY_LIVE:
        return _engine(root, store, None, wiring=wiring)
    try:
        policy = resolve_policy_config(root)
    except DevRelayError as exc:
        _fail(str(PolicyLiveResolutionFailedError(str(exc))))
    return _engine(root, store, None, policy=policy, wiring=wiring)


def _require_reviewing_task(store: ArtifactStore, explicit: str | None) -> str:
    task_id = _task_id(store, explicit)
    task = _read_task(store, task_id)
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
    profile_dir = profiles_dir(repo_root)
    profile_dir.mkdir(parents=True, exist_ok=True)
    typer.echo(f"Initialized DevRelay v{__version__} at {repo_root}")
    typer.echo(f"Config: {config_path}")
    typer.echo(f"Profiles: {profile_dir}")
    typer.echo("")
    typer.echo("Project profiles are committed; task state is not. Recipe:")
    typer.echo("  .devrelay/*")
    typer.echo("  !.devrelay/profiles/")
    typer.echo("Recommended: '*.yaml text eol=lf' in .gitattributes (stable hashes).")
    typer.echo("Next: devrelay start \"<task title>\"")


@app.command()
def doctor(
    strict: bool = typer.Option(
        False, "--strict", help="Exit non-zero when any diagnostic is not OK"
    ),
) -> None:
    """Diagnose the environment: wiring, profiles, policy chain, tasks.

    Raw profile inspection and the authoritative full-chain resolution are
    reported separately, so a broken selector never hides the per-file
    diagnostics (and vice versa).  Zero cost: no network request is ever sent.
    """
    try:
        root = require_root(Path.cwd())
    except DevRelayError as exc:
        _fail(str(exc))
    store = _store(root)
    config_file = root / ".devrelay" / "config.yaml"
    problems: list[str] = []
    typer.echo(f"Workspace: {root}")
    typer.echo(f"Config: {config_file}")
    ws = GitWorkspace(root)
    typer.echo(f"Git repo: {ws.detect_repo()}")

    # -- runtime wiring (live, never validates policy) --------------------
    wiring: WiringConfig
    try:
        wiring = load_wiring_config(config_file)
        typer.echo("Runtime wiring: OK")
    except ConfigError as exc:
        wiring = WiringConfig()
        problems.append(str(exc))
        typer.echo(f"Runtime wiring: BROKEN — {exc}")
    codex = CodexCLIProvider(wiring.codex, CommandRunner(), workspace_root=root)
    ok, diagnostic = codex.availability()
    typer.echo(f"Codex CLI: {'OK' if ok else 'MISSING'} — {diagnostic}")
    typer.echo(
        f"  Args: {' '.join(wiring.codex.args)} "
        f"(prompt transport: {wiring.codex.prompt_mode})"
    )
    for warning in codex.unknown_arg_warnings():
        typer.echo(f"  Warning: {warning}")
    # v0.2-C structured runtime diagnostics (help probes only - never a model).
    from devrelay.providers.codex_runtime import (
        CODEX_CHILD_ENV_DENYLIST,
        detect_capabilities,
        detect_repo_codex_config,
    )

    typer.echo(f"  Runtime mode: {wiring.codex.runtime_mode}")
    if ok:
        capabilities = detect_capabilities(
            codex.runner,
            wiring.codex.executable,
            getattr(wiring.codex, "launcher_args", ()) or (),
        )
        typer.echo(f"  {capabilities.describe()}")
        if wiring.codex.runtime_mode == "structured" and not capabilities.structured_supported:
            problems.append("structured runtime unsupported by the installed CLI")
        repo_config = detect_repo_codex_config(Path(root))
        if repo_config:
            typer.echo(
                "  Repository Codex config: " + ", ".join(repo_config)
                + (" (blocked in structured mode)" if wiring.codex.runtime_mode == "structured" else "")
            )
        if wiring.codex.runtime_mode == "structured" and repo_config:
            problems.append("repository Codex config is not supported in structured mode")
    # v0.2-C: strong containment is a hard precondition of the structured
    # runtime (the POST control-plane check is only meaningful when nothing the
    # Codex child spawned can still be alive), so it is reported explicitly.
    from devrelay.workspace.containment import containment_support

    containment_ok, containment_diagnostic = containment_support()
    if wiring.codex.runtime_mode == "structured":
        typer.echo(
            "  Process containment: "
            + ("OK" if containment_ok else "UNAVAILABLE")
            + f" — {containment_diagnostic}"
        )
        if not containment_ok:
            problems.append(
                "structured runtime requires strong process containment "
                "(set codex.runtime_mode: text explicitly to use the uncontained "
                "legacy runtime)"
            )
    else:
        typer.echo(
            "  Process containment: not used by the legacy text runtime "
            "(no structured contract, no control-plane guard)"
        )
    scrubbed = sorted(
        name for name in CODEX_CHILD_ENV_DENYLIST if os.environ.get(name)
    )
    typer.echo(
        "  Codex child env scrub: "
        + (", ".join(scrubbed) if scrubbed else "(no known credentials present)")
    )
    typer.echo(
        "  Note: ambient non-listed secrets stay visible to the Codex child "
        "(not a general secret sandbox)."
    )
    typer.echo(f"Reviewer provider: {wiring.review_provider}")
    if wiring.review_provider == "openai_compatible":
        from devrelay.providers.openai_compatible import (
            ENV_API_KEY,
            ENV_BASE_URL,
            ENV_MODEL,
        )

        # Presence only - never the value, and never a network request
        # (doctor must stay zero-cost).
        typer.echo(f"  {ENV_BASE_URL}: {'set' if os.environ.get(ENV_BASE_URL) else 'unset (default)'}")
        typer.echo(f"  {ENV_MODEL}: {'set' if os.environ.get(ENV_MODEL) else 'unset (default)'}")
        typer.echo(f"  {ENV_API_KEY}: {'set' if os.environ.get(ENV_API_KEY) else 'MISSING'}")
        typer.echo("  (no request is sent by doctor; reviewer calls are counted per task)")

    # -- raw profile inspection (independent of the selector) -------------
    names, invalid = discover_profiles(root)
    typer.echo("Project profiles (raw inspection):")
    typer.echo(f"  discovered: {', '.join(names) if names else '(none)'}")
    for filename in invalid:
        problems.append(f"{filename} is not a valid profile filename")
        typer.echo(f"  warning: {filename} is not a valid profile file and is ignored")
    report = validate_profiles(root)
    typer.echo(f"  selector (raw): {report.selector_raw}")
    invalid_entries = [entry for entry in report.entries if not entry.ok]
    typer.echo(
        "  per-file validation: "
        + (
            f"OK ({len(report.entries)} profile(s))"
            if not invalid_entries
            else f"{len(invalid_entries)} invalid of {len(report.entries)}"
        )
    )
    for error in report.errors:
        problems.append(error)
        typer.echo(f"  problem: {error}")

    # -- authoritative full-chain resolution ------------------------------
    budget = None
    try:
        policy = resolve_policy_config(root)
        budget = policy.document.budget
        typer.echo(
            "Effective policy chain: OK "
            f"(profiles applied: {[ref.name for ref in policy.provenance.profiles]})"
        )
    except DevRelayError as exc:
        problems.append(f"policy chain: {exc}")
        typer.echo(f"Effective policy chain: FAILED — {exc}")
        try:
            budget = PolicyDocument.from_workspace_config(
                load_config(config_file)
            ).budget
            typer.echo("  (showing workspace-only values below; this is NOT the chain)")
        except DevRelayError:
            budget = None
    if budget is not None:
        typer.echo(
            "Provider budget: "
            f"implementer {budget.max_implementer_calls}, "
            f"reviewer {budget.max_reviewer_calls}, "
            f"total {budget.max_total_provider_calls}"
        )

    # -- task state --------------------------------------------------------
    task_ids = store.list_task_ids()
    typer.echo(f"Tasks: {len(task_ids)}")
    for task_id in task_ids:
        try:
            task = store.read_task(task_id)
        except DevRelayError as exc:
            problems.append(str(exc))
            typer.echo(f"  {task_id}: UNREADABLE — {exc}")
            continue
        state = check_snapshot(store, task).state
        notes: list[str] = [f"policy {state.value}"]
        if task.state_schema_version < SNAPSHOT_ERA_SCHEMA:
            notes.append(
                f"state schema {task.state_schema_version} (migration to 5 pending)"
            )
            problems.append(
                f"{task_id} is on state schema {task.state_schema_version}; the "
                "next write migrates it to 5 (one-way, backup kept)"
            )
        if state is not SnapshotState.VALID:
            problems.append(f"{task_id} has no usable frozen policy ({state.value})")
        recorded = task.policy_provenance
        if recorded is not None and recorded.profiles:
            drift = []
            for ref in recorded.profiles:
                try:
                    _document, digest = load_profile(root, ref.name)
                except DevRelayError:
                    drift.append(f"{ref.name}: missing")
                    continue
                if digest != ref.sha256:
                    drift.append(f"{ref.name}: changed since freeze")
            if drift:
                notes.append("profile drift — " + "; ".join(drift))
        typer.echo(f"  {task_id}: {', '.join(notes)}")

    if strict and problems:
        typer.echo("")
        typer.echo(f"doctor --strict: {len(problems)} problem(s) found")
        raise typer.Exit(1)



@app.command()
def start(title: str = typer.Argument(..., help="Short task title")) -> None:
    """Create a new task (state PLAN_REQUIRED)."""
    root = _resolve_root()
    store = _store(root)
    ws = GitWorkspace(root)
    if not ws.detect_repo():
        _fail(
            f"{root} is not a git repository — DevRelay tasks require git "
            "(run 'git init' first)."
        )
    try:
        policy = resolve_policy_config(root)
    except DevRelayError as exc:
        _fail(str(exc))
    engine = _engine(
        root, store, None, policy=policy, wiring=_load_wiring(root)
    )
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
    store = _store(root)
    # v0.2-C: control-plane holds are discovered by scanning task directories,
    # never by trusting .devrelay/state.json (which a Codex child could write).
    holds = store.list_control_plane_holds()
    try:
        task_id = _task_id(store, task)
    except Exception:
        if holds:
            _echo_control_plane_holds(holds)
            raise typer.Exit(1)
        raise
    hold = next((h for h in holds if h.get("task_id") == task_id), None)
    if hold is not None:
        _echo_control_plane_holds([hold])
    run = _read_task(store, task_id)
    # State-only: status never resolves live profiles and never rewrites state.
    engine = _engine(
        root, store, None, wiring=_load_wiring(root), display_policy=True
    )
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
        ("Runtime", "runtime_mode"),
        ("Budget", "budget"),
        ("Review", "review"),
        ("Runtime", "runtime"),
        ("Policy", "policy_source"),
    ):
        if key == "policy_source":
            typer.echo(f"{label:<12} {block['policy_display']}")
            continue
        typer.echo(f"{label:<12} {block[key]}")
    recorded = block.get("policy_profiles") or []
    if recorded:
        typer.echo("")
        typer.echo("Profiles recorded (frozen with the task, not re-read):")
        for ref in recorded:
            typer.echo(f"  {ref['name']:<16} {ref['sha256']}")
    if block.get("policy_integrity") not in (
        "",
        "verified",
        "not_frozen",
        "unverified_legacy_no_digest",
        "workspace_overrides",
    ):
        typer.echo("")
        typer.echo(
            f"Policy problem ({block['policy_integrity']}): "
            f"{block.get('policy_detail') or 'snapshot unusable'}"
        )
        typer.echo(
            "Recovery: 'devrelay unblock --reason \"...\" --refresh-policy'"
        )
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
    store = _store(root)
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
    store = _store(root)
    task_id = _task_id(store, task)
    if not file.is_file():
        _fail(f"file not found: {file}")
    engine = _task_engine(root, store, task_id)
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
    store = _store(root)
    task_id = _task_id(store, task)
    # Guardrail: classify + verify the frozen policy before any provider exists.
    engine = _task_engine(root, store, task_id)
    try:
        events = engine.continue_task(task_id)
    except DevRelayError as exc:
        _fail(str(exc))
    for line in events:
        typer.echo(line)
    state = _read_task(store, task_id).state.value
    typer.echo(f"[{task_id}] state: {state}")
    if any(line.endswith("-> FIX_REQUIRED") for line in events):
        typer.echo(f"[{task_id}] next: 'devrelay continue' to run the fix pass")
    if any(line.startswith(f"[{task_id}] ERROR") for line in events):
        raise typer.Exit(1)
    if state in ("BLOCKED", "FAILED"):
        raise typer.Exit(1)


@app.command()
def usage(
    task: Optional[str] = typer.Option(None, "--task", help="Task id (default: current)"),
) -> None:
    """Show provider invocation counts, budget and review attempt history.

    Read-only: there is deliberately no command that resets or forges usage.
    """
    root = _resolve_root()
    store = _store(root)
    task_id = _task_id(store, task)
    engine = _engine(
        root, store, None, wiring=_load_wiring(root), display_policy=True
    )
    try:
        data = engine.usage_block(task_id)
    except DevRelayError as exc:
        _fail(str(exc))

    def _limit(value: object) -> str:
        return "-" if value is None else str(value)

    typer.echo(f"Task: {data['task_id']}  (state {data['state']})")
    typer.echo("")
    typer.echo("Provider budget:")
    typer.echo(
        f"  Implementer  {data['implementer_calls']} / {_limit(data['max_implementer_calls'])}"
    )
    typer.echo(f"  Reviewer     {data['reviewer_calls']} / {_limit(data['max_reviewer_calls'])}")
    typer.echo(f"  Total        {data['total_calls']} / {_limit(data['max_total_provider_calls'])}")
    typer.echo("")
    typer.echo("Reviewer:")
    typer.echo(f"  provider     {data['reviewer_provider']}")
    typer.echo(f"  model        {data['reviewer_model']}")
    typer.echo(f"  endpoint     {data['reviewer_endpoint_host']}")
    typer.echo(f"  policy from  {data['policy_source']} ({data['policy_display']})")
    for ref in data.get("policy_profiles") or []:
        typer.echo(f"  profile      {ref['name']} {ref['sha256']}")
    typer.echo("")
    typer.echo("Review attempts:")
    attempts = data["review_attempts"]
    if attempts:
        for attempt in attempts:
            typer.echo(
                f"  Review #{attempt['review_number']}"
                f"  Attempt {attempt['attempt_id']} {attempt['status']} via "
                f"{attempt['provider']} - calls {attempt['external_calls']}, "
                f"http {attempt['transport_attempts']}, format "
                f"{attempt['format_attempts']}"
                + (f", result {attempt['result']}" if attempt["result"] else "")
                + (f", error {attempt['error_type']}" if attempt["error_type"] else "")
            )
            for call_id in attempt["call_ids"]:
                typer.echo(f"    Call {call_id}")
            if attempt["result_persisted"]:
                typer.echo(
                    "    result persisted"
                    + (
                        f", applied -> {attempt['applied_state']}"
                        if attempt["result_applied"]
                        else ", NOT applied yet (replayed locally on continue)"
                    )
                )
    else:
        typer.echo("  (none)")
    if data["pending_review_result"]:
        pending = data["pending_review_result"]
        typer.echo("")
        typer.echo(
            "Pending review result: "
            f"attempt {pending['attempt_id']} (round #{pending['review_number']}) - "
            "will be replayed with 0 external calls"
        )
    typer.echo("")
    typer.echo("Provider calls:")
    calls = data["provider_calls"]
    if calls:
        for call in calls:
            typer.echo(
                f"  {call['call_id']} {call['kind']} {call['phase']} "
                f"external={call['external_calls']} "
                f"{'ok' if call['success'] else 'failed'}"
                + (f" ({call['error_type']})" if call["error_type"] else "")
                + (f" model={call['model']}" if call["model"] else "")
                + f" {call['duration_seconds']}s"
            )
    else:
        typer.echo("  (none)")
    if data["policy_refreshes"]:
        typer.echo("")
        typer.echo("Policy refreshes (before/after preserved):")
        for refresh in data["policy_refreshes"]:
            typer.echo(
                f"  {refresh['refresh_id']} {refresh['at']} "
                f"{refresh['before_source']} -> {refresh['after_source']}: "
                f"{refresh['reason']}"
            )
    if data["blocked_code"]:
        typer.echo("")
        typer.echo(f"Blocked: {data['blocked_code']}")


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
    store = _store(root)
    task_id = _task_id(store, task)
    engine = _engine(root, store, None, wiring=_load_wiring(root))
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
    store = _store(root)
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
    store = _store(root)
    task_id = _require_reviewing_task(store, task)
    engine = _task_engine(root, store, task_id)
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
    store = _store(root)
    task_id = _require_reviewing_task(store, task)
    if not file.is_file():
        _fail(f"file not found: {file}")
    try:
        raw = json.loads(file.read_text(encoding="utf-8"))
        review = ReviewResult.model_validate(raw)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        _fail(f"invalid review file: {exc}")
    engine = _task_engine(root, store, task_id)
    try:
        events = engine.import_manual_review(task_id, review)
    except DevRelayError as exc:
        _fail(str(exc))
    for line in events:
        typer.echo(line)
    state = _read_task(store, task_id).state.value
    typer.echo(f"[{task_id}] state: {state}")


final_app = typer.Typer(help="Final gate commands.", no_args_is_help=True)
app.add_typer(final_app, name="final")


@final_app.command("export")
def final_export(
    task: Optional[str] = typer.Option(None, "--task"),
) -> None:
    """Generate the final human review package."""
    root = _resolve_root()
    store = _store(root)
    task_id = _task_id(store, task)
    engine = _task_engine(root, store, task_id)
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
    store = _store(root)
    task_id = _task_id(store, task)
    engine = _task_engine(root, store, task_id)
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
    refresh_policy: bool = typer.Option(
        False,
        "--refresh-policy",
        help=(
            "Re-freeze the workspace policy as this task's policy (the only "
            "supported way to raise a running task's budget, and the recovery "
            "for a missing/invalid/damaged snapshot). Audited."
        ),
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help=(
            "Required to replace the frozen policy of a task that is neither "
            "blocked nor failed and whose snapshot is intact."
        ),
    ),
    acknowledge_control_plane: bool = typer.Option(
        False,
        "--acknowledge-control-plane-violation",
        help=(
            "Acknowledge a v0.2-C control-plane hold. The hold is cleared only "
            "when protected state matches the trusted PRE identity again."
        ),
    ),
    restore_control_plane_state: bool = typer.Option(
        False,
        "--restore-state-from-pre",
        help=(
            "With --acknowledge-control-plane-violation: restore the parent-held "
            "pre-run state.json (hash-validated) before verification."
        ),
    ),
    replay_completion: bool = typer.Option(
        False,
        "--replay-completion",
        help=(
            "Apply a COMPLETION_READY attempt locally (0 provider calls) when "
            "all recorded identities still match."
        ),
    ),
    task: Optional[str] = typer.Option(None, "--task"),
) -> None:
    """Manually recover a BLOCKED/FAILED task (never skips findings silently)."""
    root = _resolve_root()
    store = _store(root)
    task_id = _task_id(store, task)
    if refresh_policy and not force:
        current = _read_task(store, task_id)
        snapshot_state = check_snapshot(store, current).state
        healthy = snapshot_state is SnapshotState.VALID
        blocked = bool(current.blocked_code) or current.state.value == "FAILED"
        if healthy and not blocked:
            _fail(
                str(
                    PolicyRefreshNotAllowedError(
                        f"task {task_id} has a valid frozen policy "
                        f"(sha256 {current.policy_config_sha256}) and is not "
                        "blocked; pass --force to replace an intact task policy"
                    )
                )
            )
    if refresh_policy:
        # Full live-policy validation is required here: this command is the
        # explicit recovery/change mechanism and must resolve the chain first.
        try:
            policy = resolve_policy_config(root)
        except DevRelayError as exc:
            _fail(str(PolicyLiveResolutionFailedError(str(exc))))
        engine = _engine(
            root, store, None, policy=policy, wiring=_load_wiring(root)
        )
    else:
        engine = _task_engine(root, store, task_id, fail_closed=False)
    try:
        run = engine.unblock(
            task_id,
            reason=reason,
            to=to,
            refresh_policy=refresh_policy,
            force=force,
            acknowledge_control_plane=acknowledge_control_plane,
            restore_control_plane_state=restore_control_plane_state,
            replay_completion=replay_completion,
        )
    except DevRelayError as exc:
        _fail(str(exc))
    typer.echo(f"{task_id} unblocked -> {run.state.value} (reason: {reason})")
    if refresh_policy:
        typer.echo(
            "Policy snapshot refreshed from the workspace config "
            f"(policy_source={run.policy_source}); recorded in the audit trail."
        )
    if run.state.value in ("FIX_REQUIRED", "IMPLEMENTING", "REVIEWING"):
        typer.echo("Next: 'devrelay continue' (manual override recorded in audit)")


profile_app = typer.Typer(
    help="Project profile inspection (raw, works with a broken selector).",
    no_args_is_help=True,
)
from devrelay.cli_opencode import opencode_app  # noqa: E402  (v0.3-A bridge)
from devrelay.cli_mcp import mcp_app  # noqa: E402  (v0.3-B MCP tool surface)

app.add_typer(opencode_app, name="opencode")
app.add_typer(mcp_app, name="mcp")
app.add_typer(profile_app, name="profile")

config_app = typer.Typer(
    help="Show runtime wiring (unresolved) or the resolved policy chain.",
    no_args_is_help=True,
)
app.add_typer(config_app, name="config")


@profile_app.command("list")
def profile_list() -> None:
    """List project profile files without resolving the selector."""
    root = _resolve_root()
    _store(root)
    names, invalid = discover_profiles(root)
    if not names and not invalid:
        typer.echo(f"no project profiles in {profiles_dir(root)}")
        return
    for name in names:
        entry = inspect_profile(root, name)
        status = "ok" if entry.ok else "INVALID"
        typer.echo(f"{name:<24} {status:<8} {entry.sha256[:16]}")
    for filename in invalid:
        typer.echo(
            f"{filename:<24} {'IGNORED':<8} not a valid profile file "
            f"(expected <name>{PROFILE_SUFFIX} with name {PROFILE_NAME_PATTERN})"
        )


@profile_app.command("show")
def profile_show(
    name: str = typer.Argument(..., help="Profile name (without .yaml)"),
) -> None:
    """Print one profile file; only that file is read."""
    root = _resolve_root()
    _store(root)
    entry = inspect_profile(root, name)
    if not entry.ok:
        _fail(entry.error)
    typer.echo(f"Profile: {name}")
    typer.echo(f"Path: {entry.path}")
    typer.echo(f"SHA-256: {entry.sha256}")
    typer.echo("")
    typer.echo(entry.path.read_text(encoding="utf-8"), nl=False)


@profile_app.command("validate")
def profile_validate(
    name: Optional[str] = typer.Argument(None, help="Profile name (default: all)"),
) -> None:
    """Validate one profile, or every profile plus the raw selector."""
    root = _resolve_root()
    _store(root)
    if name:
        entry = inspect_profile(root, name)
        if entry.ok:
            typer.echo(f"{name}: OK ({entry.sha256})")
            return
        _fail(entry.error)
    report = validate_profiles(root)
    typer.echo(f"Selector (raw): {report.selector_raw}")
    for entry in report.entries:
        typer.echo(
            f"  {entry.name:<24} {'OK' if entry.ok else 'INVALID'}"
            + ("" if entry.ok else f" — {entry.error}")
        )
    for filename in report.invalid_filenames:
        typer.echo(f"  {filename:<24} IGNORED — not a valid profile filename")
    if report.ok:
        typer.echo(f"All {len(report.entries)} profile(s) valid; chain composes.")
        return
    typer.echo("")
    for error in report.errors:
        typer.echo(f"error: {error}")
    raise typer.Exit(1)


@config_app.command("show")
def config_show(
    resolved: bool = typer.Option(
        False, "--resolved", help="Resolve the full profile chain (authoritative)"
    ),
) -> None:
    """Show live runtime wiring + the raw selector, or the resolved policy."""
    root = _resolve_root()
    _store(root)
    path = root / ".devrelay" / "config.yaml"
    if resolved:
        try:
            policy = resolve_policy_config(root)
        except DevRelayError as exc:
            _fail(f"policy chain could not be resolved: {exc}")
        typer.echo("# Effective task policy (authoritative full resolution)")
        typer.echo(f"# selector: {policy.provenance.selector_raw}")
        for ref in policy.provenance.profiles:
            typer.echo(f"# profile {ref.name}: {ref.sha256}")
        typer.echo(
            f"# workspace config sha256: {policy.provenance.workspace_config_sha256}"
        )
        typer.echo(dump_policy_yaml(policy.document), nl=False)
        return

    wiring = _load_wiring(root)
    raw = _raw_config_mapping(path)
    selector = raw.get("profiles") or []
    typer.echo("Runtime wiring / workspace overrides:")
    typer.echo(f"  review.provider        {wiring.review_provider}")
    typer.echo(f"  codex.executable       {wiring.codex.executable}")
    typer.echo(f"  codex.args             {' '.join(wiring.codex.args)}")
    typer.echo(f"  codex.prompt_mode      {wiring.codex.prompt_mode}")
    typer.echo(f"  codex.timeout_seconds  {wiring.codex.timeout_seconds:g}")
    typer.echo("")
    typer.echo(f"Selected profiles (unresolved): {selector}")
    overrides = sorted(workspace_policy_overrides(path))
    typer.echo(f"Policy overrides present in config.yaml: {overrides or '[]'}")
    typer.echo("")
    typer.echo("Note: this is live runtime wiring, not the effective task policy.")
    typer.echo("      For the resolved chain:  devrelay config show --resolved")
    typer.echo("      For a task's frozen policy: devrelay status --task <id>")


def main() -> None:
    try:
        app()
    except typer.Exit:
        raise
    except Exception as exc:  # last-resort guard (never prints secrets raw)
        _unexpected(exc)


if __name__ == "__main__":
    main()
