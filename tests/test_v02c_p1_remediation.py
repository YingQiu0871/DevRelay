"""v0.2-C P1 remediation: runtime wiring, process containment, call accounting.

Blocking findings from the independent v0.2-C review, each closed here by a
focused test:

* **P1-A** engines running a *frozen* task read the Codex runtime mode from the
  wrong config source, so the production CLI silently ran the legacy text path
  (no structured contract, no staging, no control-plane guard, no env scrub).
* **P1-B** a detached descendant could outlive the main Codex process, wait for
  the POST control-plane check to pass and then mutate authoritative state.
* **P1-D** the pre-run attempt write used a stale in-memory ``TaskRun`` and
  erased the recorded call intent, so a real invocation disappeared from
  ``provider_calls``/budget usage on the control-plane-violation path.

Everything runs against the offline ``codex`` stub: no model, no network.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import yaml
from typer.testing import CliRunner

from devrelay.artifacts.store import ArtifactStore
from devrelay.cli import app
from devrelay.pipeline.budget import ProviderBudget
from devrelay.providers.codex_cli import CodexCLIProvider
from devrelay.workspace.runner import CommandRunner

from helpers import (
    ScriptedAutoReviewer,
    build_engine,
    default_config,
    make_git_repo,
    make_packet,
    make_review,
    structured_codex_config,
    write_codex_stub,
)

STATE = "DR-0001"
CONTAINMENT = "windows-job-object"

# A deferred, detached grandchild: it sleeps past the end of the Codex process
# and then tampers with the authoritative control plane. If (and only if) the
# run is uncontained this write lands after the POST check has already passed.
TAMPER_CHILD = '''"""Detached descendant used to probe post-guard tampering."""
import json
import sys
import time
from pathlib import Path

workspace = Path(sys.argv[1])
marker = Path(sys.argv[2])
delay = float(sys.argv[3])
marker.parent.mkdir(parents=True, exist_ok=True)
marker.write_text("child-started", encoding="utf-8")
time.sleep(delay)
devrelay = workspace / ".devrelay"
devrelay.mkdir(parents=True, exist_ok=True)
(devrelay / "evil.txt").write_text("descendant was here\\n", encoding="utf-8")
state_path = devrelay / "tasks" / "DR-0001" / "state.json"
if state_path.is_file():
    data = json.loads(state_path.read_text(encoding="utf-8"))
    data["title"] = "TAMPERED-BY-DESCENDANT"
    state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
marker.with_name(marker.name + ".done").write_text("tampered", encoding="utf-8")
'''


def _engine_with_stub(tmp_path: Path, stub: Path, *, config=None, **engine_kwargs):
    """Engine whose implementer is the real CodexCLIProvider + offline stub."""
    base = config or _structured_config(stub)
    if config is None:
        base.codex = structured_codex_config(stub)
    provider = CodexCLIProvider(
        base.codex, CommandRunner(), workspace_root=str(tmp_path / "ws")
    )
    root, store, engine = build_engine(
        tmp_path,
        config=base,
        implementer=provider,
        reviewer=ScriptedAutoReviewer([make_review("PASS")]),
        use_real_git=True,
        **engine_kwargs,
    )
    engine.create_task("v0.2-C P1 remediation")
    engine.import_plan(STATE, make_packet(task_id=STATE))
    return root, store, engine


def _structured_config(stub: Path, **overrides):
    config = default_config()
    config.tests.targeted = []
    config.budget.max_implementer_calls = 1
    config.budget.max_total_provider_calls = 2
    config.codex = structured_codex_config(stub, **overrides)
    return config


def _reconfigure(stub: Path, **config) -> None:
    """Rewrite the stub behaviour sidecar (same stub file, new behaviour)."""
    stub.with_name("stub-config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )


def _tamper_child(tmp_path: Path) -> Path:
    child = tmp_path / "tamper_child.py"
    child.write_text(TAMPER_CHILD, encoding="utf-8")
    return child


def _prove_tamper_payload_works(tmp_path: Path, child: Path, delay: float) -> None:
    """Control run: the same payload *without* containment really does tamper.

    Without this check the negative assertions below could pass vacuously (a
    typo in the child script would look exactly like successful containment).
    """
    workspace = tmp_path / "control-ws"
    task_dir = workspace / ".devrelay" / "tasks" / STATE
    task_dir.mkdir(parents=True)
    (task_dir / "state.json").write_text(
        json.dumps({"title": "control"}), encoding="utf-8"
    )
    marker = tmp_path / "control.marker"
    subprocess.Popen(
        [sys.executable, str(child), str(workspace), str(marker), str(delay)],
        close_fds=True,
    )
    done = marker.with_name(marker.name + ".done")
    deadline = time.monotonic() + delay + 30
    while time.monotonic() < deadline and not done.exists():
        time.sleep(0.2)
    assert done.exists(), "tamper payload never ran: negative checks are vacuous"
    assert (workspace / ".devrelay" / "evil.txt").is_file()
    tampered = json.loads((task_dir / "state.json").read_text(encoding="utf-8"))
    assert tampered["title"] == "TAMPERED-BY-DESCENDANT"


def _assert_no_post_guard_tamper(root: Path, marker: Path, store: ArtifactStore) -> None:
    """No descendant write landed, and the child never completed its tamper."""
    assert not (root / ".devrelay" / "evil.txt").exists()
    assert not marker.with_name(marker.name + ".done").exists()
    state = json.loads(store.state_path(STATE).read_text(encoding="utf-8"))
    assert state["title"] != "TAMPERED-BY-DESCENDANT"


# ===========================================================================
# P1-A: the production CLI path must use the wiring's runtime mode
# ===========================================================================
def _prepared_cli_repo(tmp_path: Path, monkeypatch, stub: Path, **codex) -> tuple[Path, CliRunner]:
    """A real git workspace driven only through the production CLI."""
    repo = make_git_repo(tmp_path / "repo", initial_files={"app.py": "print(1)\n"})
    monkeypatch.chdir(repo)
    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0

    config_path = repo / ".devrelay" / "config.yaml"
    workspace_config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    workspace_config["review"] = {"provider": "manual"}
    workspace_config["tests"] = {"targeted": []}
    workspace_config["codex"] = {
        **(workspace_config.get("codex") or {}),
        "executable": sys.executable,
        "launcher_args": [str(stub)],
        "runtime_mode": "structured",
        **codex,
    }
    config_path.write_text(
        yaml.safe_dump(workspace_config, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    assert runner.invoke(app, ["start", "cli structured"]).exit_code == 0
    task_md = repo / ".devrelay" / "tasks" / STATE / "task.md"
    task_md.write_text(
        "# Task DR-0001\n\n"
        "## Title\n\ncli structured\n\n"
        "## Objective\n\nrun the structured runtime\n",
        encoding="utf-8",
    )
    assert runner.invoke(app, ["plan", "import", str(task_md)]).exit_code == 0
    return repo, runner


def test_cli_continue_runs_the_structured_runtime(tmp_path, monkeypatch):
    """The exact P1-A escape: a frozen task through the real CLI is structured."""
    argv_capture = tmp_path / "argv.json"
    argv_full_capture = tmp_path / "argv-full.json"
    prompt_capture = tmp_path / "prompt.txt"
    stub = write_codex_stub(
        tmp_path / "tools",
        argv_capture=str(argv_capture),
        argv_full_capture=str(argv_full_capture),
        prompt_capture=str(prompt_capture),
    )
    repo, runner = _prepared_cli_repo(tmp_path, monkeypatch, stub)

    result = runner.invoke(app, ["continue"])
    assert result.exit_code == 0, result.output

    argv = json.loads(argv_capture.read_text(encoding="utf-8"))
    assert argv.count("exec") == 1, argv
    assert argv.count("--sandbox") == 1, argv
    assert "workspace-write" in argv
    for owned in (
        "--ignore-user-config",
        "--ignore-rules",
        "--json",
        "--output-schema",
        "--output-last-message",
    ):
        assert argv.count(owned) == 1, (owned, argv)
    # the launcher prefix made the stub the process entry point: the structured
    # argv (exec + DevRelay-owned flags) is what the launcher handed to Codex
    full_argv = json.loads(argv_full_capture.read_text(encoding="utf-8"))
    assert full_argv[0] == str(stub), full_argv
    assert full_argv[1] == "exec", full_argv
    # the prompt reached Codex through stdin, not through the argv
    assert prompt_capture.read_text(encoding="utf-8").strip()

    store = ArtifactStore(repo)
    task = store.read_task(STATE)
    attempt = task.attempts[-1]
    assert task.state.value in ("TESTING", "REVIEWING", "FINAL_GATE_REQUIRED")
    runtime = attempt.runtime
    assert runtime is not None
    assert runtime.runtime_mode == "structured"
    assert runtime.control_plane_changes == 0
    assert runtime.result_claimed is True
    assert runtime.containment == CONTAINMENT
    assert runtime.containment_all_dead is True
    runtime_dir = store.task_runtime_dir(STATE, attempt.attempt_id)
    for name in ("runtime.json", "schema.json", "result.json", "completion.json"):
        assert (runtime_dir / name).is_file(), name

    # the frozen policy snapshot is still the authority for *policy* only: it
    # carries no codex runtime mode, so the structured run cannot have come from
    # task policy (the P1-A downgrade happened when it was read from there).
    snapshot = yaml.safe_load(
        (store.task_dir(STATE) / "config.snapshot.yaml").read_text(encoding="utf-8")
    )
    assert "codex" not in snapshot
    assert "runtime_mode" not in json.dumps(snapshot)

    # doctor / status report the effective (wiring) mode
    status = runner.invoke(app, ["status"])
    assert status.exit_code == 0, status.output
    runtime_lines = [ln for ln in status.output.splitlines() if "Runtime" in ln]
    assert runtime_lines and "structured" in runtime_lines[0], status.output
    doctor = runner.invoke(app, ["doctor"])
    assert doctor.exit_code == 0, doctor.output
    assert "structured" in doctor.output


def test_cli_runtime_mode_text_is_explicit_and_stays_text(tmp_path, monkeypatch):
    """An explicitly text-wired workspace keeps the legacy path (no upgrade)."""
    argv_capture = tmp_path / "argv.json"
    argv_full_capture = tmp_path / "argv-full.json"
    stub = write_codex_stub(
        tmp_path / "tools",
        argv_capture=str(argv_capture),
        argv_full_capture=str(argv_full_capture),
    )
    # the text runtime runs ``executable + args`` (no launcher prefix, no exec)
    repo, runner = _prepared_cli_repo(
        tmp_path, monkeypatch, stub, runtime_mode="text", args=[str(stub)]
    )

    result = runner.invoke(app, ["continue"])
    assert result.exit_code == 0, result.output
    argv = json.loads(argv_capture.read_text(encoding="utf-8"))
    for structured_only in ("--output-schema", "--output-last-message", "--ignore-rules"):
        assert structured_only not in argv, argv
    # no launcher prefix and no DevRelay-owned ``exec``: the legacy text path
    assert json.loads(argv_full_capture.read_text(encoding="utf-8")) == [str(stub)]
    assert argv == []

    store = ArtifactStore(repo)
    task = store.read_task(STATE)
    runtime = task.attempts[-1].runtime
    assert (runtime.runtime_mode if runtime else "text") == "text"
    status = runner.invoke(app, ["status"])
    runtime_lines = [ln for ln in status.output.splitlines() if "Runtime" in ln]
    assert runtime_lines and "text" in runtime_lines[0], status.output


# ===========================================================================
# P1-D: a consumed call must survive the control-plane-violation path
# ===========================================================================
def test_violation_keeps_the_consumed_call_charged(tmp_path):
    """A real invocation is charged even when the run is voided by the guard."""
    stub = write_codex_stub(tmp_path / "tools")
    root, store, engine = _engine_with_stub(tmp_path, stub)
    evil = root / ".devrelay" / "evil.txt"
    # the Codex child itself writes an unexpected control-plane file
    _reconfigure(stub, tamper=[["write", str(evil), "child wrote this"]])

    events = engine.continue_task(STATE)
    assert any("codex_control_plane_violation" in e for e in events)

    task = store.read_task(STATE)
    assert [(r.call_id, r.external_call_count) for r in task.provider_calls] == [
        (f"{STATE}-C0001", 1)
    ]
    usage = ProviderBudget.usage(task)
    assert usage.implementer_calls == 1
    assert usage.total_calls == 1
    # the durable call ledger keeps the same, uniquely identified invocation
    call_file = store.policy_dir(STATE) / "calls" / f"{STATE}-C0001.json"
    assert call_file.is_file()
    call = json.loads(call_file.read_text(encoding="utf-8"))
    assert call["call_id"] == f"{STATE}-C0001"
    hold = json.loads(
        (store.task_dir(STATE) / "CONTROL_PLANE_HOLD.json").read_text(encoding="utf-8")
    )
    assert hold["call_id"] == f"{STATE}-C0001"
    assert hold["code"] == "codex_control_plane_violation"
    # the violation report records containment metadata (never file contents)
    report_file = next(iter(store.control_state_dir(STATE).glob("*-violation.json")))
    report = json.loads(report_file.read_text(encoding="utf-8"))
    assert report["containment"]["containment"] == CONTAINMENT
    assert report["containment"]["containment_all_dead"] is True
    assert "child wrote this" not in report_file.read_text(encoding="utf-8")


def test_state_tamper_keeps_the_consumed_call_in_the_trusted_pre(tmp_path):
    """A tampered state.json is never overwritten; the parent's copy is trusted."""
    stub = write_codex_stub(tmp_path / "tools")
    _, store, engine = _engine_with_stub(tmp_path, stub)
    state_path = store.state_path(STATE)
    _reconfigure(stub, tamper=[["write", str(state_path), "TAMPERED"]])

    events = engine.continue_task(STATE)
    assert any("codex_control_plane_violation" in e for e in events)
    # fail closed: the child's bytes are left exactly as written
    assert state_path.read_text(encoding="utf-8") == "TAMPERED"

    control_state = store.control_state_dir(STATE)
    pre_file = next(iter(control_state.glob("*-state.pre.json")))
    pre = json.loads(pre_file.read_text(encoding="utf-8"))
    assert [(r["call_id"], r["external_call_count"]) for r in pre["provider_calls"]] == [
        (f"{STATE}-C0001", 1)
    ]
    hold = json.loads(
        (store.task_dir(STATE) / "CONTROL_PLANE_HOLD.json").read_text(encoding="utf-8")
    )
    assert hold["call_id"] == f"{STATE}-C0001"
    diverging = list(hold.get("diverging_paths") or []) + [
        str(difference.get("rel_path", ""))
        for difference in (hold.get("differences") or [])
        if isinstance(difference, dict)
    ]
    assert any(path.endswith("state.json") for path in diverging), hold


# ===========================================================================
# P1-B: the contained process tree must be dead before POST may trust anything
# ===========================================================================
def test_detached_descendant_cannot_tamper_after_post(tmp_path):
    """The auditor's exact bypass: a deferred detached write vs. the POST check."""
    child = _tamper_child(tmp_path)
    _prove_tamper_payload_works(tmp_path, child, delay=2.0)

    stub = write_codex_stub(tmp_path / "tools")
    root, store, engine = _engine_with_stub(tmp_path, stub)
    marker = tmp_path / "child.marker"
    _reconfigure(
        stub,
        descendant=str(child),
        descendant_args=[str(root), str(marker), "2.0"],
        descendant_close_fds=True,
    )

    events = engine.continue_task(STATE)
    assert not any("control_plane_violation" in e for e in events), events
    task = store.read_task(STATE)
    assert task.state.value in ("TESTING", "REVIEWING", "FINAL_GATE_REQUIRED")
    attempt = task.attempts[-1]
    assert attempt.runtime is not None
    assert attempt.runtime.containment == CONTAINMENT
    assert attempt.runtime.containment_all_dead is True
    assert attempt.runtime.containment_error == ""

    # the descendant is already dead: nothing can land in the 2s it was told to
    # wait (well before POST + completion) and nothing lands afterwards either
    time.sleep(4.0)
    _assert_no_post_guard_tamper(root, marker, store)


def test_descendant_inheriting_pipes_is_contained_without_hanging(tmp_path):
    """Inherited stdout/stderr handles must not make the reader threads hang."""
    child = _tamper_child(tmp_path)
    stub = write_codex_stub(tmp_path / "tools")
    root, store, engine = _engine_with_stub(tmp_path, stub)
    marker = tmp_path / "child.marker"
    _reconfigure(
        stub,
        descendant=str(child),
        descendant_args=[str(root), str(marker), "2.0"],
        descendant_close_fds=False,  # the descendant holds the inherited pipes
    )

    started = time.monotonic()
    engine.continue_task(STATE)
    elapsed = time.monotonic() - started
    assert elapsed < 60, elapsed  # bounded: no reader thread outlives the tree

    task = store.read_task(STATE)
    assert task.attempts[-1].runtime.containment_all_dead is True
    time.sleep(4.0)
    _assert_no_post_guard_tamper(root, marker, store)


def test_structured_timeout_kills_the_contained_tree_and_still_checks_post(tmp_path):
    """A timed-out run kills the whole tree and is still charged and guarded."""
    child = _tamper_child(tmp_path)
    _prove_tamper_payload_works(tmp_path, child, delay=2.0)
    stub = write_codex_stub(tmp_path / "tools")
    config = _structured_config(stub)
    config.codex = config.codex.model_copy(update={"timeout_seconds": 2.0})
    root, store, engine = _engine_with_stub(tmp_path, stub, config=config)
    marker = tmp_path / "child.marker"
    _reconfigure(
        stub,
        sleep=60,
        # the descendant's write is scheduled well after the 2s timeout: only a
        # tree that was really killed can explain the absence of the write
        descendant=str(child),
        descendant_args=[str(root), str(marker), "6.0"],
        descendant_close_fds=True,
    )

    started = time.monotonic()
    events = engine.continue_task(STATE)
    elapsed = time.monotonic() - started
    assert elapsed < 20, elapsed  # the 60s child was killed, not waited for

    task = store.read_task(STATE)
    assert task.state.value == "FAILED"
    assert task.blocked_code == "implementer_failed"
    assert ProviderBudget.usage(task).implementer_calls == 1
    assert any("timed_out=True" in e for e in events), events
    # the timeout never reached COMPLETION_READY and left no completion artifact
    assert task.attempts[-1].completion_ready is False
    assert not (
        store.task_runtime_dir(STATE, task.attempts[-1].attempt_id) / "completion.json"
    ).exists()
    # POST still ran (the guard is not skipped on a provider failure) and the
    # descendant never got the chance to write after it
    assert task.attempts[-1].runtime is not None
    assert task.attempts[-1].runtime.control_plane_changes == 0
    time.sleep(8.0)
    _assert_no_post_guard_tamper(root, marker, store)


def test_unverified_containment_skips_post_and_holds(tmp_path, monkeypatch):
    """If the tree cannot be confirmed dead, POST must not run at all."""
    from devrelay.workspace import containment as containment_module

    stub = write_codex_stub(tmp_path / "tools")
    root, store, engine = _engine_with_stub(tmp_path, stub)

    class _NeverDead:
        """Containment that never confirms the tree is dead."""

        name = CONTAINMENT

        def __init__(self, inner):
            self._inner = inner

        def __getattr__(self, item):
            return getattr(self._inner, item)

        def all_contained_processes_dead(self, timeout: float = 0.0) -> bool:
            self._inner.all_contained_processes_dead(timeout)
            return False

    real_create = containment_module.create_containment

    def _create():
        return _NeverDead(real_create())

    import devrelay.providers.codex_cli as codex_cli

    monkeypatch.setattr(containment_module, "create_containment", _create)
    monkeypatch.setattr(codex_cli, "create_containment", _create)

    events = engine.continue_task(STATE)
    assert any("codex_containment_unverified" in e for e in events), events

    # the guard did NOT run: no POST identity was ever computed, and the state
    # on disk is exactly the parent-written pre-run state (no verdict persisted)
    hold = json.loads(
        (store.task_dir(STATE) / "CONTROL_PLANE_HOLD.json").read_text(encoding="utf-8")
    )
    assert hold["code"] == "codex_containment_unverified"
    assert hold["call_id"] == f"{STATE}-C0001"
    assert hold["containment"]["containment_all_dead"] is False
    report = json.loads(
        next(iter(store.control_state_dir(STATE).glob("*-violation.json"))).read_text(
            encoding="utf-8"
        )
    )
    assert report["code"] == "codex_containment_unverified"
    assert report["post_manifest_sha256"] == ""
    task = store.read_task(STATE)
    assert task.state.value == "IMPLEMENTING"
    assert all(not attempt.completion_ready for attempt in task.attempts)
    assert all(
        attempt.milestone.value not in ("COMPLETION_READY", "COMPLETION_APPLIED")
        for attempt in task.attempts
    )
    # the consumed call is still charged (the process really ran)
    assert [(r.call_id, r.external_call_count) for r in task.provider_calls] == [
        (f"{STATE}-C0001", 1)
    ]


def test_containment_is_required_for_structured_mode(tmp_path, monkeypatch):
    """No strong containment -> structured mode refuses to start (0 calls)."""
    import devrelay.providers.codex_cli as codex_cli

    stub = write_codex_stub(tmp_path / "tools")
    _, store, engine = _engine_with_stub(tmp_path, stub)
    monkeypatch.setattr(
        codex_cli,
        "containment_support",
        lambda: (False, "no strong containment on this platform"),
    )

    events = engine.continue_task(STATE)
    task = store.read_task(STATE)
    assert task.blocked_code == "codex_process_containment_unsupported"
    assert ProviderBudget.usage(task).total_calls == 0
    assert ProviderBudget.usage(task).implementer_calls == 0
    assert any("containment" in e for e in events), events
    # nothing ran: the stub was never invoked and the settled ledger entry for
    # the refused attempt records zero external calls
    assert not (tmp_path / "argv.json").exists()
    settled = json.loads(
        (store.policy_dir(STATE) / "calls" / f"{STATE}-C0001.json").read_text(
            encoding="utf-8"
        )
    )
    assert settled["external_call_count"] == 0
    assert not (store.task_runtime_dir(STATE, task.attempts[-1].attempt_id) / "result.json").exists()


# ===========================================================================
# C7 / C16 closure
# ===========================================================================
def test_c7_nonzero_exit_with_a_valid_result_is_still_a_failure(tmp_path):
    """A model result never upgrades a failed process to a success."""
    stub = write_codex_stub(tmp_path / "tools")
    root, store, engine = _engine_with_stub(tmp_path, stub)
    _reconfigure(stub, exit_code=3, result="valid")

    engine.continue_task(STATE)
    task = store.read_task(STATE)
    assert task.state.value == "FAILED"
    assert task.blocked_code == "implementer_failed"
    assert ProviderBudget.usage(task).implementer_calls == 1
    attempt = task.attempts[-1]
    assert attempt.completion_ready is False
    assert attempt.milestone.value != "COMPLETION_READY"
    runtime_dir = store.task_runtime_dir(STATE, attempt.attempt_id)
    # the structured result is not promoted to durable evidence on failure
    assert not (runtime_dir / "result.json").exists()
    assert not (runtime_dir / "completion.json").exists()
    logs = store.logs_dir(STATE) / f"{attempt.attempt_id}.stderr.log"
    assert logs.is_file()


def test_c16_unicode_paths_end_to_end(tmp_path):
    """A unicode workspace root + unicode claims survive the whole runtime."""
    unicode_root = tmp_path / "\u4e2d\u6587-\u00fc"
    unicode_rel = "src/\u00fcnicode/\u4e2d\u6587 file.py"
    stub = write_codex_stub(tmp_path / "tools", changed_files=[unicode_rel])
    root, store, engine = _engine_with_stub(unicode_root, stub)
    assert "\u4e2d\u6587" in str(root)

    events = engine.continue_task(STATE)
    task = store.read_task(STATE)
    assert task.state.value in ("TESTING", "REVIEWING", "FINAL_GATE_REQUIRED"), events
    attempt = task.attempts[-1]
    assert attempt.runtime is not None
    assert attempt.runtime.result_claimed is True
    assert attempt.runtime.staging_removed is True
    assert attempt.runtime.control_plane_changes == 0
    runtime_dir = store.task_runtime_dir(STATE, attempt.attempt_id)
    assert (runtime_dir / "result.json").is_file()
    assert (runtime_dir / "schema.json").is_file()
    reconciliation = json.loads(
        (runtime_dir / "implementation-reconciliation.json").read_text(encoding="utf-8")
    )
    assert reconciliation["claimed_files"] == [unicode_rel]
    assert reconciliation["path_rejected"] == []
    assert reconciliation["unclaimed_change"] == []
