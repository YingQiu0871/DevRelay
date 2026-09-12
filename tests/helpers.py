"""Shared fakes/helpers for the DevRelay test-suite (no real Codex/network)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from devrelay.artifacts.store import ArtifactStore
from devrelay.config import DevRelayConfig, load_config
from devrelay.models import (
    CommandResult,
    Finding,
    NameStatusEntry,
    ProviderExecutionResult,
    RepoSnapshot,
    ReviewResult,
    Severity,
    TaskDelta,
    TaskPacket,
    TaskRun,
    WorkspaceBaseline,
    WorkspaceSnapshot,
)
from devrelay.errors import ProviderError, ReviewFormatError
from devrelay.models import (
    CallErrorType,
    ProviderCallPhase,
    ProviderCallRecord,
    ProviderKind,
    utcnow_iso,
)
from devrelay.pipeline.engine import DevRelayEngine
from devrelay.providers.base import ImplementerProvider, ReviewerProvider
from devrelay.providers.evidence import NullCallSink
from devrelay.workspace.git import GitWorkspace
from devrelay.workspace.runner import CommandRunner


# ---------------------------------------------------------------------------
# git helper
# ---------------------------------------------------------------------------

def make_git_repo(path: Path, *, initial_files: dict[str, str] | None = None) -> Path:
    """Create a git repository with one initial commit."""
    path.mkdir(parents=True, exist_ok=True)
    for name, content in (initial_files or {}).items():
        target = path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    git_env = {**os.environ.copy(), "GIT_AUTHOR_NAME": "DevRelay Test",
               "GIT_AUTHOR_EMAIL": "t@devrelay.test",
               "GIT_COMMITTER_NAME": "DevRelay Test",
               "GIT_COMMITTER_EMAIL": "t@devrelay.test"}
    def _git(args, cwd=None):
        proc = subprocess.run(
            ["git", *args] if cwd is None else ["git", "-C", str(cwd), *args],
            env=git_env, capture_output=True, text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"git {' '.join(args)} failed rc={proc.returncode}: "
                f"{proc.stderr[-800:] or proc.stdout[-800:]}"
            )

    _git(["init", "-q", "-b", "main", str(path)])
    _git(["add", "-A"], cwd=path)
    proc = subprocess.run(
        ["git", "-C", str(path), "commit", "-q", "-m", "initial"],
        env=git_env, capture_output=True, text=True,
    )
    combined = f"{proc.stderr or ''}{proc.stdout or ''}"
    if proc.returncode != 0 and "nothing to commit" not in combined:
        raise RuntimeError(
            f"git commit failed rc={proc.returncode}: {combined[-800:]}"
        )
    return path


def dirty_file(path: Path, name: str, content: str = "dirty content\n") -> Path:
    """Create/modify a file so the workspace reports it as dirty."""
    target = path / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# fakes
# ---------------------------------------------------------------------------

class FakeCommandRunner:
    """Records calls; scripted results keyed by joined argv."""

    def __init__(self, results: dict[str, CommandResult] | None = None) -> None:
        self.results = results or {}
        self.calls: list[dict] = []
        self.which_map: dict[str, str | None] = {}

    def run(self, argv, cwd=None, timeout_seconds=900.0, input_text=None, env=None):
        self.calls.append(
            {
                "argv": list(argv),
                "cwd": str(cwd) if cwd is not None else None,
                "input": input_text,
                "timeout": timeout_seconds,
            }
        )
        result = self.results.get(" ".join(argv))
        if result is None:
            return CommandResult(
                command=list(argv),
                cwd=str(cwd) if cwd is not None else None,
                exit_code=0,
            )
        return result

    def which(self, executable: str) -> str | None:
        return self.which_map.get(executable, f"/fake/{executable}")


def fake_success(stdout: str = "ok\n", code: int = 0) -> CommandResult:
    return CommandResult(command=[], exit_code=code, stdout=stdout)


def cmd_result(
    *,
    exit_code: int = 0,
    stdout: str = "",
    stderr: str = "",
    timed_out: bool = False,
    error: str | None = None,
) -> CommandResult:
    return CommandResult(
        command=[], exit_code=exit_code, stdout=stdout, stderr=stderr,
        timed_out=timed_out, error=error,
    )


class FakeWorkspace:
    def __init__(
        self,
        root: Path,
        *,
        dirty_files: Optional[list[str]] = None,
        diff_text: str = "diff --git a/src/x.py b/src/x.py\n+change\n",
        changed: Optional[list[str]] = None,
        head: str = "abc123def456",
    ) -> None:
        self.root = Path(root)
        self._dirty = dirty_files or []
        self._diff = diff_text
        self._changed = changed if changed is not None else list(self._dirty)
        self._head = head

    def snapshot(self) -> WorkspaceSnapshot:
        return WorkspaceSnapshot(
            repo_root=str(self.root),
            head_sha=self._head,
            branch="main",
            dirty_files=list(self._dirty),
            has_git=True,
        )

    def detect_repo(self) -> bool:
        return True

    def diff(self, stat: bool = False) -> str:
        return "stat" if stat else self._diff

    def changed_name_only(self) -> list[str]:
        return list(self._changed)

    def head_sha(self) -> str | None:
        return self._head

    def status(self) -> str:
        return "\n".join(self._dirty)

    def is_dirty(self) -> bool:
        return bool(self._dirty)


class FakeImplementer(ImplementerProvider):
    name = "fake-implementer"

    def __init__(
        self,
        *,
        report: str = "FAKE IMPLEMENTATION\nIMPLEMENTATION_SUMMARY\nok\n",
        exit_code: int = 0,
        stderr: str = "",
        error: str | None = None,
        unavailable: bool = False,
        stdout: str | None = None,
    ) -> None:
        self._report = report
        self._exit_code = exit_code
        self._stderr = stderr
        self._error = error
        self._unavailable = unavailable
        self._stdout = stdout if stdout is not None else report
        self.calls: list = []

    def availability(self) -> tuple[bool, str]:
        return (not self._unavailable, "fake provider")

    def run(self, context) -> ProviderExecutionResult:
        self.calls.append(context)
        if self._unavailable:
            return ProviderExecutionResult(
                exit_code=None,
                error="Codex CLI is not installed or not available on PATH.",
                stderr="Codex CLI is not installed or not available on PATH.",
            )
        if self._error:
            return ProviderExecutionResult(exit_code=None, error=self._error)
        return ProviderExecutionResult(
            exit_code=self._exit_code,
            stdout=self._stdout,
            stderr=self._stderr,
            report=self._report,
        )


class QueueImplementer(FakeImplementer):
    """Fake implementer returning a queued result per call (then repeats last)."""

    def __init__(self, results: list[ProviderExecutionResult]) -> None:
        super().__init__()
        self.queue = list(results)

    def run(self, context) -> ProviderExecutionResult:
        self.calls.append(context)
        if self.queue:
            return self.queue.pop(0)
        return ProviderExecutionResult(exit_code=0, stdout="ok", report="ok")


class ScriptedAutoReviewer(ReviewerProvider):
    """Automatic reviewer fake that accounts calls exactly like the real one.

    Each scripted outcome consumes exactly one external reviewer call through
    the sink the engine injects (``call_policy.sink``), so engine-level tests
    exercise the real budget/accounting path instead of mocking it away.
    """

    name = "scripted-auto"

    def __init__(self, outcomes: list, *, model: str = "fake-model") -> None:
        self.outcomes = list(outcomes)
        self.bundles: list = []
        self._model = model
        self._sequence = 0

    @property
    def automatic(self) -> bool:
        return True

    @property
    def model(self) -> str:
        return self._model

    @property
    def endpoint_host(self) -> str:
        return "fake.endpoint.invalid"

    def prepare_request(self, bundle, review_number=None):
        return None

    def review(self, bundle, *, call_policy=None):
        self.bundles.append(bundle)
        outcome = self.outcomes.pop(0) if self.outcomes else ReviewResult(
            decision="PASS", summary="default pass"
        )
        sink = getattr(call_policy, "sink", None) or NullCallSink()
        self._sequence += 1
        # Identity comes from the sink (durable, task-scoped) - exactly like the
        # real provider, so engine-level tests exercise real accounting.
        record = ProviderCallRecord(
            call_id="",
            provider_kind=ProviderKind.REVIEWER,
            provider_name=self.name,
            phase=ProviderCallPhase.REVIEW,
            attempt_number=self._sequence,
            external_call_count=1,
            model=self._model,
            endpoint_host=self.endpoint_host,
        )
        sink.preflight(ProviderKind.REVIEWER, ProviderCallPhase.REVIEW)
        record = sink.start(record)

        def settle(*, success: bool, error_type=None, error=None) -> ProviderCallRecord:
            settled = record.model_copy(
                update={
                    "success": success,
                    "completed_at": utcnow_iso(),
                    "error_type": error_type,
                    "error": error,
                }
            )
            sink.finish(settled)
            return settled

        if isinstance(outcome, ReviewResult):
            settle(success=True)
            return outcome
        if isinstance(outcome, tuple) and outcome and outcome[0] == "format":
            settle(success=False, error_type=CallErrorType.FORMAT, error=outcome[1])
            raise ReviewFormatError(outcome[1])
        if isinstance(outcome, tuple) and outcome and outcome[0] == "transport":
            settle(success=False, error_type=CallErrorType.TRANSPORT, error=outcome[1])
            raise ProviderError(outcome[1])
        if isinstance(outcome, BaseException):
            settle(success=False, error_type=CallErrorType.EXCEPTION, error=str(outcome))
            raise outcome
        raise AssertionError(f"unsupported scripted outcome: {outcome!r}")


class QueueReviewer(ReviewerProvider):
    """Automatic reviewer with a queue of ReviewResults."""

    name = "queue-reviewer"

    def __init__(self, results: list[ReviewResult]) -> None:
        self.queue = list(results)
        self.bundles: list = []

    @property
    def automatic(self) -> bool:
        return True

    def prepare_request(self, bundle, review_number=None):
        return None

    def review(self, bundle, *, call_policy=None) -> ReviewResult:
        self.bundles.append(bundle)
        if self.queue:
            return self.queue.pop(0)
        return ReviewResult(decision="PASS", summary="default pass")


# ---------------------------------------------------------------------------
# model builders
# ---------------------------------------------------------------------------

def make_packet(
    task_id: str = "DR-0001",
    *,
    title: str = "Sample task",
    objective: str = "Do the thing",
    risk: str = "NORMAL",
    acceptance: Optional[list[str]] = None,
) -> TaskPacket:
    return TaskPacket(
        task_id=task_id,
        title=title,
        objective=objective,
        scope=["src/a.py"],
        out_of_scope=["docs/", "other/"],
        acceptance_criteria=acceptance or ["tests pass"],
        constraints=["no unrelated refactors"],
        tests_required=["pytest -q"],
        risk_level=risk,
    )


def make_finding(severity: Severity | str, title: str = "finding") -> Finding:
    return Finding(severity=severity, title=title, description="detail")


def make_review(
    decision: str,
    findings: Optional[list[Finding]] = None,
    summary: str = "review summary",
) -> ReviewResult:
    return ReviewResult(
        findings=findings or [],
        summary=summary,
        decision=decision,
        reviewer="test",
    )


def default_config() -> DevRelayConfig:
    return load_config(None)


class FakeBaselineService:
    """In-memory baseline/guard double for engine tests (no real git)."""

    def __init__(
        self,
        *,
        delta_text: str = "diff --git a/src/x.py b/src/x.py\n+agent line\n",
        violation_queues: Optional[list[list]] = None,
        fail_delta: bool = False,
    ) -> None:
        self._delta_text = delta_text
        self._violation_queues = list(violation_queues or [])
        self.fail_delta = fail_delta
        self.captures: list[str] = []
        self.pre_snapshots = 0
        self.post_snapshots = 0

    def capture(self, task_id: str) -> WorkspaceBaseline:
        self.captures.append(task_id)
        return WorkspaceBaseline(
            task_id=task_id,
            head_sha="abc123",
            branch="main",
            baseline_worktree_tree_sha="b" * 40,
            baseline_complete=True,
            baseline_storage_path=f"tasks/{task_id}/baseline",
        )

    def pre_snapshot(self) -> RepoSnapshot:
        self.pre_snapshots += 1
        return RepoSnapshot(head_sha="abc123", branch="main", index_tree_sha="i" * 40)

    def post_snapshot(self) -> RepoSnapshot:
        self.post_snapshots += 1
        return RepoSnapshot(head_sha="abc123", branch="main", index_tree_sha="i" * 40)

    def validate_baseline(self, task_id: str) -> WorkspaceBaseline:
        """In-memory double: nothing to validate, always succeeds."""
        return self.capture(task_id)

    def task_delta(self, task) -> TaskDelta:
        return TaskDelta(
            text_diff=self._delta_text,
            changed_files=["src/x.py"],
            from_tree="a" * 40,
            to_tree="b" * 40,
            method="trees",
        )

    def check_policy(self, before, after) -> list:
        if self._violation_queues:
            return self._violation_queues.pop(0)
        return []

    def task_delta(self, task: TaskRun) -> TaskDelta:
        if self.fail_delta:
            from devrelay.errors import BaselineUnavailableError

            raise BaselineUnavailableError(
                f"task {task.task_id} has no task baseline (legacy task)"
            )
        return TaskDelta(
            text_diff=self._delta_text,
            stat_text=" 1 file changed, 1 insertion(+)",
            changed_files=["src/x.py"],
            name_status=[NameStatusEntry(status="M", new_path="src/x.py")],
            method="fake",
        )

    def binary_task_diff(self, task: TaskRun) -> str:
        return "GIT binary patch (fake)"


def build_engine(
    tmp_path: Path,
    *,
    config: DevRelayConfig | None = None,
    implementer: ImplementerProvider | None = None,
    reviewer: ReviewerProvider | None = None,
    workspace=None,
    runner=None,
    use_real_git: bool = False,
    baseline_service=None,
    fallback_policy_config=None,
    runtime_config=None,
):
    """Return (root, store, engine). Root contains a .devrelay store."""
    root = tmp_path / "ws"
    root.mkdir(parents=True, exist_ok=True)
    if use_real_git:
        make_git_repo(root, initial_files={"README.md": "hi\n"})
    store = ArtifactStore(root)
    store.ensure_initialized()
    cfg = config or default_config()
    if workspace is None:
        ws: object = GitWorkspace(root) if use_real_git else FakeWorkspace(root)
    else:
        ws = workspace
    if baseline_service is None:
        if use_real_git:
            from devrelay.baseline.service import BaselineService
            from devrelay.workspace.runner import CommandRunner as CR

            baseline_service = BaselineService(
                root, CR(), store, cfg
            )
        else:
            baseline_service = FakeBaselineService()
    eng = DevRelayEngine(
        cfg,
        store,
        ws,
        implementer=implementer or FakeImplementer(),
        reviewer=reviewer or ManualReviewerProxy(),
        runner=runner or FakeCommandRunner(),
        baselines=baseline_service,
        runtime_config=runtime_config,
        fallback_policy_config=fallback_policy_config,
    )
    return root, store, eng


from devrelay.providers.manual import ManualReviewer as ManualReviewerProxy  # noqa: E402


# ---------------------------------------------------------------------------
# v0.2-C: fake Codex CLI (offline structured-runtime harness)
# ---------------------------------------------------------------------------
CODEX_STUB_HELP = """Run Codex non-interactively

Usage: codex exec [OPTIONS] [PROMPT]

Options:
  -s, --sandbox <SANDBOX_MODE>      [possible values: read-only, workspace-write, danger-full-access]
      --ignore-user-config          Do not load $CODEX_HOME/config.toml; auth still uses CODEX_HOME
      --ignore-rules                Do not load user or project execpolicy `.rules` files
      --output-schema <FILE>        Path to a JSON Schema file describing the model's final response shape
  -o, --output-last-message <FILE>  Specifies file where the last message from the agent should be written
      --json                        Print events to stdout as JSONL
      --color <COLOR>               [possible values: always, never, auto]
  -h, --help                        Print help
"""

CODEX_STUB_SOURCE = '''"""Offline `codex` stub for DevRelay v0.2-C tests (never calls a model)."""
import json
import os
import sys
import time
from pathlib import Path

HELP = """%s"""


def main() -> int:
    args = sys.argv[1:]
    config_path = Path(__file__).with_name("stub-config.json")
    cfg = json.loads(config_path.read_text(encoding="utf-8")) if config_path.is_file() else {}
    if "--version" in args:
        print("codex-cli 9.9.9-stub")
        return 0
    if "exec" in args and ("--help" in args or "-h" in args):
        print(HELP)
        return 0
    prompt = ""
    if not sys.stdin.isatty():
        try:
            prompt = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        except Exception:
            prompt = ""
    if cfg.get("prompt_capture"):
        Path(cfg["prompt_capture"]).write_text(prompt, encoding="utf-8", errors="replace")
    if cfg.get("env_capture"):
        record = {name: bool(os.environ.get(name)) for name in cfg.get("env_names", [])}
        Path(cfg["env_capture"]).write_text(json.dumps(record), encoding="utf-8")
    if cfg.get("argv_capture"):
        Path(cfg["argv_capture"]).write_text(json.dumps(args), encoding="utf-8")
    for op, target, *rest in cfg.get("tamper", []) or []:
        path = Path(target)
        if op == "write":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rest[0] if rest else "", encoding="utf-8")
        elif op == "delete" and path.exists():
            path.unlink()
    if cfg.get("sleep"):
        time.sleep(float(cfg["sleep"]))
    exit_code = int(cfg.get("exit_code", 0) or 0)
    out = None
    for index, token in enumerate(args):
        if token in ("-o", "--output-last-message") and index + 1 < len(args):
            out = args[index + 1]
        elif token.startswith("--output-last-message="):
            out = token.split("=", 1)[1]
    if cfg.get("extra_staging") and out:
        Path(out).parent.joinpath(cfg["extra_staging"]).write_text("x", encoding="utf-8")
    if out and cfg.get("result", "valid") != "missing":
        payload = cfg.get("result_payload")
        if payload is None:
            payload = {
                "schema_version": 1,
                "status": cfg.get("status", "COMPLETE"),
                "summary": cfg.get("summary", "stub implementation"),
                "changed_files": cfg.get("changed_files", ["app.py"]),
                "tests_run": cfg.get("tests_run", [{"command": "python -m pytest -q", "result": "PASS"}]),
                "unresolved_items": cfg.get("unresolved_items", []),
                "known_risks": cfg.get("known_risks", []),
            }
        raw = payload if isinstance(payload, str) else json.dumps(payload)
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(raw, encoding="utf-8")
    for line in cfg.get("events", ['{"type":"thread.started","thread_id":"stub-session-1"}', '{"type":"turn.completed","model":"stub-model"}']):
        print(line)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
''' % CODEX_STUB_HELP


def write_codex_stub(directory: Path, **config) -> Path:
    """Write an offline Codex stub plus its behaviour sidecar.

    Returns the stub path; use it as ``CodexConfig(executable=sys.executable,
    launcher_args=[str(stub)], runtime_mode="structured")``.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    stub = directory / "codex_stub.py"
    stub.write_text(CODEX_STUB_SOURCE, encoding="utf-8")
    (directory / "stub-config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )
    return stub


def structured_codex_config(stub: Path, **overrides):
    """CodexConfig wired to the offline stub in structured mode."""
    from devrelay.config import CodexConfig

    payload = {
        "executable": sys.executable,
        "launcher_args": [str(stub)],
        "args": ["exec", "--sandbox", "workspace-write"],
        "runtime_mode": "structured",
    }
    payload.update(overrides)
    return CodexConfig(**payload)
