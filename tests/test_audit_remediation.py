"""Release-audit remediation regression tests (AUD-01 … AUD-05).

Everything here uses real temporary git repositories and the real production
paths: no mocked reconstruction, no mocked policy guard, no mocked redaction
boundary.  Only the remote reviewer transport is mocked (httpx.MockTransport).

AUD-01: byte-exact patch transport -> durable recovery works for tracked changes
AUD-02: provider exception cannot bypass the post-run guard or auto-rerun
AUD-03: reviewer payload / artifact redaction boundary
AUD-04: conflicted or unverifiable index fails closed
AUD-05: tracked.patch is byte-for-byte faithful (incl. CRLF repos)
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import httpx
import pytest

from devrelay.artifacts.store import ArtifactStore
from devrelay.baseline.service import BaselineService
from devrelay.config import DevRelayConfig, load_config
from devrelay.models import (
    AttemptStatus,
    Finding,
    IndexSnapshotStatus,
    PolicyViolationType,
    ProviderExecutionResult,
    ReviewResult,
    TaskPacket,
    TaskRun,
)
from devrelay.pipeline.engine import DevRelayEngine
from devrelay.pipeline.states import PipelineState as S
from devrelay.providers.base import ImplementerProvider
from devrelay.providers.manual import ManualReviewer
from devrelay.providers.openai_compatible import (
    OpenAICompatibleReviewer,
    ReviewerEndpoint,
)
from devrelay.workspace.git import GitWorkspace
from devrelay.workspace.runner import CommandRunner

from helpers import default_config

NL = chr(10)
CR = chr(13)
IDENT = {
    "GIT_AUTHOR_NAME": "A",
    "GIT_AUTHOR_EMAIL": "a@x",
    "GIT_COMMITTER_NAME": "A",
    "GIT_COMMITTER_EMAIL": "a@x",
}
SECRET = "sk-live-AUDIT1234567890abcdef"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def git(root: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        env={**os.environ, **IDENT},
        capture_output=True,
        text=True,
        timeout=60,
        check=check,
    )


def git_bytes(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        env={**os.environ, **IDENT},
        capture_output=True,
        timeout=60,
    ).stdout


def make_repo(files: dict[str, bytes], *, autocrlf: str | None = None) -> Path:
    root = Path(subprocess.run(
        ["python", "-c", "import tempfile;print(tempfile.mkdtemp(prefix='auditrem-'))"],
        capture_output=True, text=True, check=True,
    ).stdout.strip())
    git(root, "init", "-q", "-b", "main")
    if autocrlf is not None:
        git(root, "config", "core.autocrlf", autocrlf)
    for name, data in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    git(root, "add", "-A")
    git(root, "commit", "-qm", "init")
    return root


def service_for(root: Path) -> tuple[ArtifactStore, CommandRunner, BaselineService, DevRelayConfig]:
    store = ArtifactStore(root)
    store.ensure_initialized()
    runner = CommandRunner()
    config = default_config()
    return store, runner, BaselineService(root, runner, store, config), config


def capture(svc: BaselineService, store: ArtifactStore, tid: str = "DR-0001") -> TaskRun:
    baseline = svc.capture(tid)
    task = TaskRun(task_id=tid, title="t", baseline=baseline)
    store.write_task(task)
    return task


def raw_patch_bytes(root: Path) -> bytes:
    """Independent re-derivation of the durable patch (production pathspec)."""
    return git_bytes(
        root,
        "diff", "HEAD", "--binary", "--find-renames", "--", ".",
        ":(exclude).devrelay",
    )


def prune_tree(root: Path, runner: CommandRunner, tree: str) -> None:
    runner.run(["git", "-C", str(root), "reflog", "expire", "--expire=now", "--all"])
    runner.run(["git", "-C", str(root), "gc", "--prune=now"])
    probe = runner.run(["git", "-C", str(root), "cat-file", "-e", tree])
    assert probe.exit_code != 0, "baseline tree object was not pruned"


class ActionImplementer(ImplementerProvider):
    """Fake provider performing a real action (optionally raising)."""

    name = "action"

    def __init__(self, action, *, raises: BaseException | None = None,
                 result: ProviderExecutionResult | None = None) -> None:
        self.action = action
        self.raises = raises
        self.calls = 0
        self.result = result or ProviderExecutionResult(
            exit_code=0, stdout="done", report="done"
        )

    def availability(self) -> tuple[bool, str]:
        return (True, "ok")

    def run(self, context):
        self.calls += 1
        if self.action:
            self.action(Path(context.workspace_root))
        if self.raises is not None:
            raise self.raises
        return self.result


def build_engine(root: Path, implementer, *, reviewer=None, config=None):
    store, runner, svc, cfg = service_for(root)
    config = config or cfg
    engine = DevRelayEngine(
        config,
        store,
        GitWorkspace(root, runner),
        implementer=implementer,
        reviewer=reviewer or ManualReviewer(),
        runner=runner,
        baselines=svc,
    )
    return store, engine


def start_task(engine, tid: str = "DR-0001") -> None:
    engine.create_task("t")
    engine.import_plan(tid, TaskPacket(task_id=tid, title="t", objective="o",
                                       acceptance_criteria=["x"]))


def append(path: Path, text: str) -> None:
    path.write_bytes(path.read_bytes() + text.encode())


# ---------------------------------------------------------------------------
# AUD-05: tracked.patch must be byte-for-byte faithful
# ---------------------------------------------------------------------------

def test_patch_bytes_faithful_lf_repo():
    root = make_repo({"a.txt": b"base" + NL.encode()})
    (root / "a.txt").write_bytes(b"base" + NL.encode() + b"USER" + NL.encode())
    store, _runner, svc, _cfg = service_for(root)
    capture(svc, store)
    stored = (store.baseline_dir("DR-0001") / "tracked.patch").read_bytes()
    assert stored == raw_patch_bytes(root)
    assert b"+USER" in stored


def test_patch_bytes_faithful_crlf_repo_with_autocrlf_false():
    crlf = (b"line1" + CR.encode() + NL.encode() + b"line2" + CR.encode() + NL.encode())
    root = make_repo({"f.txt": crlf}, autocrlf="false")
    assert git_bytes(root, "cat-file", "-p", "HEAD:f.txt") == crlf  # CRLF in repo form
    (root / "f.txt").write_bytes(crlf + b"user-crlf" + CR.encode() + NL.encode())
    store, _runner, svc, _cfg = service_for(root)
    capture(svc, store)
    stored = (store.baseline_dir("DR-0001") / "tracked.patch").read_bytes()
    raw = raw_patch_bytes(root)
    assert b"\r" in raw, "fixture should exercise CR bytes"
    assert stored == raw, "tracked.patch is not byte-faithful for CRLF content"


def test_patch_bytes_faithful_binary_file():
    root = make_repo({"bin.dat": b"\x00BIN\xff\xfe" + NL.encode()})
    (root / "bin.dat").write_bytes(b"\x00BIN\xff\xfeUSER\x00\x01")
    store, _runner, svc, _cfg = service_for(root)
    capture(svc, store)
    stored = (store.baseline_dir("DR-0001") / "tracked.patch").read_bytes()
    assert stored == raw_patch_bytes(root)
    assert b"GIT binary patch" in stored


# ---------------------------------------------------------------------------
# AUD-01: durable recovery matrix after pruning the baseline tree
# ---------------------------------------------------------------------------

def _scenario_modify(root: Path) -> None:
    (root / "a.txt").write_bytes(b"base" + NL.encode() + b"USER" + NL.encode())


def _scenario_delete(root: Path) -> None:
    (root / "del.txt").unlink()


def _scenario_rename(root: Path) -> None:
    (root / "ren.txt").rename(root / "ren2.txt")


def _scenario_binary(root: Path) -> None:
    (root / "bin.dat").write_bytes(b"\x00USER\xff\xfe")


def _scenario_staged_new(root: Path) -> None:
    (root / "new.txt").write_bytes(b"new" + NL.encode())
    git(root, "add", "new.txt")


def _scenario_staged_unstaged(root: Path) -> None:
    (root / "m.txt").write_bytes(b"m2" + NL.encode())
    git(root, "add", "m.txt")
    (root / "m.txt").write_bytes(b"m2" + NL.encode() + b"m3" + NL.encode())


def _scenario_crlf(root: Path) -> None:
    (root / "c.txt").write_bytes(b"c1" + CR.encode() + NL.encode() + b"USER" + CR.encode() + NL.encode())


RECOVERY_SCENARIOS = [
    ("tracked-modify", _scenario_modify, lambda r: append(r / "a.txt", "AGENT_EDIT\n")),
    ("tracked-delete", _scenario_delete, lambda r: append(r / "a.txt", "AGENT_EDIT\n")),
    ("tracked-rename", _scenario_rename, lambda r: append(r / "a.txt", "AGENT_EDIT\n")),
    ("binary-modify", _scenario_binary, lambda r: (r / "bin.dat").write_bytes(b"\x00USER\xff\xfeAGENT")),
    ("staged-new-file", _scenario_staged_new, lambda r: append(r / "a.txt", "AGENT_EDIT\n")),
    ("staged+unstaged", _scenario_staged_unstaged, lambda r: append(r / "m.txt", "AGENT_EDIT\n")),
    ("crlf-tracked", _scenario_crlf, lambda r: append(r / "c.txt", "AGENT_EDIT" + CR + NL)),
]


@pytest.mark.parametrize("name,prepare,agent", RECOVERY_SCENARIOS, ids=[s[0] for s in RECOVERY_SCENARIOS])
def test_gc_recovery_matrix_for_tracked_changes(name, prepare, agent):
    crlf_repo = name == "crlf-tracked"
    files = {
        "a.txt": b"base" + NL.encode(),
        "del.txt": b"delete me" + NL.encode(),
        "ren.txt": b"rename me" + NL.encode(),
        "bin.dat": b"\x00BIN\xff\xfe",
        "m.txt": b"m1" + NL.encode(),
    }
    if crlf_repo:
        files["c.txt"] = b"c1" + CR.encode() + NL.encode()
    root = make_repo(files, autocrlf="false" if crlf_repo else None)
    prepare(root)

    store, runner, svc, _cfg = service_for(root)
    task = capture(svc, store)
    assert task.baseline is not None
    recorded_tree = task.baseline.baseline_worktree_tree_sha

    agent(root)
    expected = svc.task_delta(task)          # fast path (tree object present)
    assert expected.has_changes

    prune_tree(root, runner, recorded_tree)
    recovered = svc.task_delta(task)         # must reconstruct from artifacts

    assert recovered.method == "reconstructed", recovered.method
    assert recovered.from_tree == recorded_tree
    assert recovered.changed_files == expected.changed_files
    assert recovered.text_diff == expected.text_diff


def test_gc_recovery_preserves_same_file_attribution():
    root = make_repo({"a.txt": b"base" + NL.encode()})
    (root / "a.txt").write_bytes(b"base" + NL.encode() + b"USER_CHANGE" + NL.encode())
    store, runner, svc, _cfg = service_for(root)
    task = capture(svc, store)
    tree = task.baseline.baseline_worktree_tree_sha

    (root / "a.txt").write_bytes(
        b"base" + NL.encode() + b"USER_CHANGE" + NL.encode() + b"AGENT_CHANGE" + NL.encode()
    )
    prune_tree(root, runner, tree)
    delta = svc.task_delta(task)
    assert delta.method == "reconstructed"
    added = [l for l in delta.text_diff.splitlines() if l.startswith("+")]
    assert any("AGENT_CHANGE" in l for l in added)
    assert not any("USER_CHANGE" in l for l in added), added


# ---------------------------------------------------------------------------
# AUD-02: provider exception / interruption lifecycle
# ---------------------------------------------------------------------------

def _engine_with_raising_provider(root: Path, action, exc: BaseException, **kw):
    impl = ActionImplementer(action, raises=exc)
    store, engine = build_engine(root, impl, **kw)
    start_task(engine)
    return store, engine, impl


def _rebuilt_engine(root: Path, impl):
    """Fresh engine for an EXISTING task (process-restart simulation)."""
    return build_engine(root, impl)


def test_provider_exception_persists_evidence_and_blocks_restart_rerun():
    root = make_repo({"a.txt": b"base" + NL.encode()})

    def action(r: Path) -> None:
        append(r / "a.txt", "HALF_WORK\n")

    store, engine, impl = _engine_with_raising_provider(
        root, action, RuntimeError("provider exploded")
    )
    with pytest.raises(RuntimeError):
        engine.continue_task("DR-0001")

    task = store.read_task("DR-0001")
    assert task.state == S.BLOCKED
    assert task.blocked_code == "interrupted_attempt"
    assert task.attempt_in_flight is False            # finalised, not left in flight
    assert task.implementation_passes == 0
    attempt = task.attempts[-1]
    assert attempt.status == AttemptStatus.INTERRUPTED
    assert attempt.provider_exception and "RuntimeError" in attempt.provider_exception
    assert attempt.post_snapshot is not None          # POST was still captured
    policy_dir = store.policy_dir("DR-0001")
    assert (policy_dir / "attempt-01.json").is_file()
    assert (policy_dir / "post-run-01.json").is_file()
    assert b"HALF_WORK" in (root / "a.txt").read_bytes()

    # restart: a fresh engine must NOT auto-rerun the provider
    store2, engine2 = _rebuilt_engine(root, ActionImplementer(None))
    impl2 = engine2.implementer
    events = engine2.continue_task("DR-0001")
    assert impl2.calls == 0
    assert store2.read_task("DR-0001").state == S.BLOCKED
    joined = " ".join(events).lower()
    assert "manual acknowledgement" in joined and "unblock" in joined

    # explicit human acknowledgement re-enables a run
    engine2.unblock("DR-0001", reason="reviewed the half-applied change")
    engine2.continue_task("DR-0001")
    assert impl2.calls == 1


def test_provider_exception_after_commit_prioritises_policy_violation():
    root = make_repo({"a.txt": b"base" + NL.encode()})
    head_before = git(root, "rev-parse", "HEAD").stdout.strip()

    def action(r: Path) -> None:
        append(r / "a.txt", "AGENT\n")
        git(r, "commit", "-qam", "sneaky")

    store, engine, _impl = _engine_with_raising_provider(
        root, action, RuntimeError("boom after commit")
    )
    # Policy outcome has priority: the attempt is blocked on the violation and
    # the provider exception is stored as attempt evidence (no re-raise).
    engine.continue_task("DR-0001")

    task = store.read_task("DR-0001")
    assert task.state == S.BLOCKED
    assert task.blocked_code == "policy_violation"     # policy beats provider error
    assert task.policy_violations[0].type == PolicyViolationType.UNEXPECTED_HEAD_CHANGE
    attempt = task.attempts[-1]
    assert attempt.status == AttemptStatus.POLICY_VIOLATION
    assert attempt.provider_exception and "RuntimeError" in attempt.provider_exception
    assert attempt.post_snapshot is not None
    # no auto-repair: the sneaky commit is still there
    assert git(root, "rev-parse", "HEAD").stdout.strip() != head_before


def test_provider_exception_with_index_mutation_is_detected():
    root = make_repo({"a.txt": b"base" + NL.encode()})

    def action(r: Path) -> None:
        (r / "staged.txt").write_bytes(b"s" + NL.encode())
        git(r, "add", "staged.txt")

    store, engine, _impl = _engine_with_raising_provider(
        root, action, RuntimeError("boom after staging")
    )
    # Index violation wins over the provider exception (evidence kept).
    engine.continue_task("DR-0001")

    task = store.read_task("DR-0001")
    assert task.state == S.BLOCKED
    assert any(
        v.type == PolicyViolationType.UNEXPECTED_INDEX_MUTATION
        for v in task.policy_violations
    )
    # staging preserved (no auto-unstage)
    assert "staged.txt" in git(root, "status", "--porcelain").stdout


def test_keyboard_interrupt_after_worktree_mutation_fails_closed():
    root = make_repo({"a.txt": b"base" + NL.encode()})

    def action(r: Path) -> None:
        append(r / "a.txt", "HALF_WORK\n")

    store, engine, _impl = _engine_with_raising_provider(
        root, action, KeyboardInterrupt()
    )
    with pytest.raises(KeyboardInterrupt):
        engine.continue_task("DR-0001")

    task = store.read_task("DR-0001")
    assert task.state == S.BLOCKED
    assert task.blocked_code == "interrupted_attempt"
    assert task.attempts[-1].status == AttemptStatus.INTERRUPTED
    assert task.attempts[-1].post_snapshot is not None

    store2, engine2 = _rebuilt_engine(root, ActionImplementer(None))
    impl2 = engine2.implementer
    engine2.continue_task("DR-0001")
    assert impl2.calls == 0                            # fail closed across restart


def test_fix_pass_provider_exception_is_guarded(tmp_path):
    root = make_repo({"a.txt": b"base" + NL.encode()})
    impl = ActionImplementer(lambda r: append(r / "a.txt", "FIRST\n"))
    store, engine = build_engine(root, impl)
    start_task(engine)
    engine.continue_task("DR-0001")
    assert store.read_task("DR-0001").state == S.REVIEWING

    engine.import_manual_review(
        "DR-0001",
        ReviewResult(decision="REQUEST_CHANGES", summary="fix", findings=[
            Finding(severity="P1", title="bug")
        ]),
    )
    impl.raises = RuntimeError("fix provider exploded")
    impl.action = lambda r: append(r / "a.txt", "HALF_FIX\n")
    with pytest.raises(RuntimeError):
        engine.continue_task("DR-0001")

    task = store.read_task("DR-0001")
    assert task.state == S.BLOCKED
    assert task.blocked_code == "interrupted_attempt"
    attempt = task.attempts[-1]
    assert attempt.phase == "FIX"
    assert attempt.status == AttemptStatus.INTERRUPTED
    assert attempt.post_snapshot is not None
    assert (store.policy_dir("DR-0001") / "attempt-02.json").is_file()


def test_in_flight_marker_blocks_provider_run_after_hard_kill_simulation():
    """A kill -9 leaves attempt_in_flight=True: restart must not auto-rerun."""
    root = make_repo({"a.txt": b"base" + NL.encode()})
    impl = ActionImplementer(lambda r: append(r / "a.txt", "AGENT\n"))
    store, engine = build_engine(root, impl)
    start_task(engine)

    task = store.read_task("DR-0001")
    task.attempt_in_flight = True
    store.write_task(task)

    events = engine.continue_task("DR-0001")
    assert impl.calls == 0
    blocked = store.read_task("DR-0001")
    assert blocked.state == S.BLOCKED
    assert blocked.blocked_code == "interrupted_attempt"
    assert any("in-flight" in e or "manual acknowledgement" in e for e in events)


# ---------------------------------------------------------------------------
# AUD-04: conflicted / unverifiable index fails closed
# ---------------------------------------------------------------------------

def _make_conflict(root: Path) -> None:
    git(root, "checkout", "-q", "-b", "side")
    (root / "a.txt").write_bytes(b"side" + NL.encode())
    git(root, "commit", "-qam", "side")
    git(root, "checkout", "-q", "main")
    (root / "a.txt").write_bytes(b"main2" + NL.encode())
    git(root, "commit", "-qam", "main")
    git(root, "merge", "side")


def test_conflicted_index_blocks_before_provider_run():
    root = make_repo({"a.txt": b"main" + NL.encode()})
    _make_conflict(root)
    assert "UU a.txt" in git(root, "status", "--porcelain").stdout

    impl = ActionImplementer(lambda r: append(r / "a.txt", "AGENT\n"))
    store, engine = build_engine(root, impl)
    start_task(engine)
    events = engine.continue_task("DR-0001")

    assert impl.calls == 0                              # refused BEFORE spending quota
    task = store.read_task("DR-0001")
    assert task.state == S.BLOCKED
    assert task.blocked_code == "policy_check_incomplete"
    attempt = task.attempts[-1]
    assert attempt.status == AttemptStatus.POLICY_CHECK_INCOMPLETE
    assert attempt.pre_snapshot is not None
    assert attempt.pre_snapshot.index_snapshot_status is IndexSnapshotStatus.CONFLICTED
    assert attempt.pre_snapshot.index_unmerged_entries
    policy_dir = store.policy_dir("DR-0001")
    assert (policy_dir / "pre-run-01.json").is_file()
    assert (policy_dir / "attempt-01.json").is_file()
    saved = json.loads((policy_dir / "pre-run-01.json").read_text(encoding="utf-8"))
    assert saved["index_snapshot_status"] == "CONFLICTED"
    assert any("fail closed" in e for e in events)


def test_post_run_conflicted_index_blocks():
    """Index becomes unverifiable DURING the run: must block, not report clean."""
    root = make_repo({"a.txt": b"main" + NL.encode()})
    git(root, "checkout", "-q", "-b", "side")
    (root / "a.txt").write_bytes(b"side" + NL.encode())
    git(root, "commit", "-qam", "side")
    git(root, "checkout", "-q", "main")
    (root / "a.txt").write_bytes(b"main2" + NL.encode())
    git(root, "commit", "-qam", "main")

    def action(r: Path) -> None:
        git(r, "merge", "--no-commit", "side")   # conflict, HEAD unchanged

    impl = ActionImplementer(action)
    store, engine = build_engine(root, impl)
    start_task(engine)
    engine.continue_task("DR-0001")

    task = store.read_task("DR-0001")
    assert task.state == S.BLOCKED
    assert task.blocked_code == "policy_check_incomplete"
    assert any(
        v.type == PolicyViolationType.POLICY_CHECK_INCOMPLETE
        for v in task.policy_violations
    )
    assert task.attempts[-1].status == AttemptStatus.POLICY_CHECK_INCOMPLETE
    assert (store.policy_dir("DR-0001") / "violations-01.json").is_file()


def test_normal_repo_index_mutation_still_blocks():
    """Regression guard: the normal (verifiable) path still detects mutations."""
    root = make_repo({"a.txt": b"base" + NL.encode()})

    def action(r: Path) -> None:
        (r / "staged.txt").write_bytes(b"s" + NL.encode())
        git(r, "add", "staged.txt")

    impl = ActionImplementer(action)
    store, engine = build_engine(root, impl)
    start_task(engine)
    engine.continue_task("DR-0001")
    task = store.read_task("DR-0001")
    assert task.state == S.BLOCKED
    assert task.blocked_code == "policy_violation"
    assert any(
        v.type == PolicyViolationType.UNEXPECTED_INDEX_MUTATION
        for v in task.policy_violations
    )


# ---------------------------------------------------------------------------
# AUD-03: reviewer redaction boundary
# ---------------------------------------------------------------------------

def _secret_repo() -> Path:
    return make_repo({
        "cfg.py": (
            'API_KEY = "' + SECRET + '"' + NL + "PRESENT = 1" + NL
        ).encode(),
        "a.txt": b"user content" + NL.encode(),
    })


def _write_boundary_impl() -> ActionImplementer:
    def action(r: Path) -> None:
        append(r / "cfg.py", "NEW_SETTING = 2\n")
    return ActionImplementer(action)


def test_remote_reviewer_payload_is_redacted_and_still_task_relative():
    root = _secret_repo()
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.content.decode("utf-8", "replace")
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(
            {"decision": "PASS", "summary": "ok", "findings": []}
        )}}]})

    store, runner, svc, cfg = service_for(root)
    cfg.review.provider = "openai_compatible"
    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="https://review.example/v1"
    )
    reviewer = OpenAICompatibleReviewer(
        ReviewerEndpoint(base_url="https://review.example/v1", api_key="k", model="m"),
        client=client,
    )
    engine = DevRelayEngine(
        cfg, store, GitWorkspace(root, runner), implementer=_write_boundary_impl(),
        reviewer=reviewer, runner=runner, baselines=svc,
    )
    start_task(engine)
    engine.continue_task("DR-0001")

    body = captured.get("body", "")
    assert body, "reviewer payload was not captured"
    assert SECRET not in body
    assert "[REDACTED]" in body
    assert "+NEW_SETTING = 2" in body          # task-relative semantics preserved
    assert store.read_task("DR-0001").state == S.FINAL_GATE_REQUIRED


def test_manual_review_request_artifact_is_redacted():
    root = _secret_repo()
    store, engine = build_engine(root, _write_boundary_impl())
    start_task(engine)
    engine.continue_task("DR-0001")

    request = (store.reviews_dir("DR-0001") / "review-01-request.md").read_text(
        encoding="utf-8"
    )
    assert SECRET not in request
    assert "[REDACTED]" in request
    assert "+NEW_SETTING = 2" in request
    assert "task baseline -> current workspace" in request


def test_previous_findings_evidence_is_redacted_in_next_request():
    root = _secret_repo()
    store, engine = build_engine(root, _write_boundary_impl())
    start_task(engine)
    engine.continue_task("DR-0001")            # -> REVIEWING (manual request 1)
    engine.import_manual_review(
        "DR-0001",
        ReviewResult(
            decision="REQUEST_CHANGES",
            summary="context mentions " + SECRET,
            findings=[Finding(severity="P1", title="bug", evidence="log: " + SECRET)],
        ),
    )
    engine.continue_task("DR-0001")            # fix pass -> REVIEWING (request 2)

    request2 = (store.reviews_dir("DR-0001") / "review-02-request.md").read_text(
        encoding="utf-8"
    )
    assert SECRET not in request2
    assert "[REDACTED]" in request2
