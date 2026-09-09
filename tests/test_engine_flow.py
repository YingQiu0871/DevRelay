"""End-to-end pipeline engine tests with fakes (no real Codex/network)."""

import pytest

from devrelay.config import load_config
from devrelay.errors import StateConflictError
from devrelay.models import ProviderExecutionResult, Severity
from devrelay.pipeline.states import PipelineState
from devrelay.providers.base import ReviewerProvider

from helpers import (
    FakeCommandRunner,
    FakeImplementer,
    FakeWorkspace,
    QueueImplementer,
    QueueReviewer,
    build_engine,
    cmd_result,
    dirty_file,
    make_finding,
    make_git_repo,
    make_packet,
    make_review,
)
from devrelay.artifacts.store import ArtifactStore
from devrelay.workspace.git import GitWorkspace
from devrelay.workspace.runner import CommandRunner

S = PipelineState


def _to_reviewing(engine, store, task_id):
    engine.continue_task(task_id)
    assert store.read_task(task_id).state == S.REVIEWING


# ---------------------------------------------------------------------------

def test_full_manual_cycle_to_done(tmp_path):
    root, store, engine = build_engine(tmp_path)
    task_id = "DR-0001"
    engine.create_task("Wear tile fix")
    task = store.read_task(task_id)
    assert task.state == S.PLAN_REQUIRED
    assert store.current_task_id() == task_id
    assert (store.task_dir(task_id) / "task.md").is_file()

    engine.import_plan(task_id, make_packet(task_id=task_id))
    task = store.read_task(task_id)
    assert task.state == S.PLAN_READY
    assert task.plan_ready is True
    # config snapshot per task exists
    assert (store.task_dir(task_id) / "config.snapshot.yaml").is_file()

    _to_reviewing(engine, store, task_id)
    task = store.read_task(task_id)
    assert task.implementation_passes == 1
    assert (store.implementation_dir(task_id) / "iteration-01.md").is_file()
    assert (store.logs_dir(task_id) / "codex-01.stdout.log").is_file()
    assert (store.reviews_dir(task_id) / "review-01-request.md").is_file()
    assert task.last_tests_passed is True  # no commands configured -> pass

    engine.import_manual_review(task_id, make_review("PASS"))
    task = store.read_task(task_id)
    assert task.state == S.FINAL_GATE_REQUIRED
    assert task.review_history
    assert (store.reviews_dir(task_id) / "review-01-result.json").is_file()

    final_path = engine.export_final(task_id)
    assert final_path.is_file()
    assert "Final gate" in final_path.read_text(encoding="utf-8")

    engine.approve_final(task_id, note="looks good on device")
    task = store.read_task(task_id)
    assert task.state == S.DONE
    assert task.final_gate is not None
    report = (store.final_dir(task_id) / "report.md").read_text(encoding="utf-8")
    assert "Why is this task considered complete?" in report
    assert "DR-0001" in report
    # audit trail persisted
    assert task.audit[-1].to_state == S.DONE.value


def test_state_survives_engine_recreation(tmp_path):
    """Resume across 'process restarts' (fresh engine + fresh store object)."""
    root, store1, engine1 = build_engine(tmp_path)
    engine1.create_task("Resume me")
    engine1.import_plan("DR-0001", make_packet(task_id="DR-0001"))
    assert store1.read_task("DR-0001").state == S.PLAN_READY

    store2 = ArtifactStore(root)
    engine2 = FakeWorkspace(root)
    ws = FakeWorkspace(root)
    eng2 = build_engine(tmp_path)
    # build a *new* engine bound to a fresh store instance
    from devrelay.pipeline.engine import DevRelayEngine
    from devrelay.config import load_config as lc

    from devrelay.providers.manual import ManualReviewer

    engine2 = DevRelayEngine(
        lc(None),
        ArtifactStore(root),
        ws,
        implementer=FakeImplementer(),
        reviewer=ManualReviewer(),
        runner=FakeCommandRunner(),
    )
    _to_reviewing(engine2, store2, "DR-0001")
    assert store2.read_task("DR-0001").state == S.REVIEWING
    # artifacts written by the "first process" are still visible
    assert (store2.reviews_dir("DR-0001") / "review-01-request.md").is_file()


@pytest.mark.parametrize("severity", ["P0", "P1", "P2"])
def test_blocking_severities_route_to_fix(tmp_path, severity):
    root, store, engine = build_engine(tmp_path)
    task_id = "DR-0001"
    engine.create_task("t")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    _to_reviewing(engine, store, task_id)
    engine.import_manual_review(
        task_id,
        make_review("REQUEST_CHANGES", [make_finding(severity)]),
    )
    task = store.read_task(task_id)
    assert task.state == S.FIX_REQUIRED
    assert task.current_findings[0].severity.value == severity


def test_p3_only_review_passes_by_default_policy(tmp_path):
    root, store, engine = build_engine(tmp_path)
    task_id = "DR-0001"
    engine.create_task("t")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    _to_reviewing(engine, store, task_id)
    # reviewer literally says REQUEST_CHANGES but only reports a P3 ->
    # policy (blocking_severities=[P0,P1,P2]) says PASS.
    engine.import_manual_review(
        task_id,
        make_review("REQUEST_CHANGES", [make_finding("P3", title="nitpick")]),
    )
    task = store.read_task(task_id)
    assert task.state == S.FINAL_GATE_REQUIRED
    assert [f.severity for f in task.open_p3] == [Severity.P3]


def test_max_fix_iterations_blocks_then_unblock_allows_override(tmp_path):
    root, store, engine = build_engine(tmp_path)
    task_id = "DR-0001"
    engine.create_task("t")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    _to_reviewing(engine, store, task_id)

    blocking = lambda: make_review("REQUEST_CHANGES", [make_finding("P1")])  # noqa: E731
    for _ in range(3):
        engine.import_manual_review(task_id, blocking())
        assert store.read_task(task_id).state == S.FIX_REQUIRED
        engine.continue_task(task_id)
        assert store.read_task(task_id).state == S.REVIEWING

    # 4th blocking review -> cap exhausted
    engine.import_manual_review(task_id, blocking())
    task = store.read_task(task_id)
    assert task.state == S.BLOCKED
    assert task.blocked_code == "max_iterations"
    assert task.fix_iterations_used == 3

    # no silent skip: unblock requires a reason; findings still open
    engine.unblock(task_id, reason="human reviewed findings; one more round")
    task = store.read_task(task_id)
    assert task.state == S.FIX_REQUIRED
    assert task.manual_override is True

    engine.continue_task(task_id)
    assert store.read_task(task_id).state == S.REVIEWING
    engine.import_manual_review(task_id, make_review("PASS"))
    task = store.read_task(task_id)
    assert task.state == S.FINAL_GATE_REQUIRED
    engine.approve_final(task_id)
    assert store.read_task(task_id).state == S.DONE


def test_failing_tests_block_by_default(tmp_path):
    config = load_config(None)
    config.tests.targeted = ["pytest -q"]
    runner = FakeCommandRunner(results={"pytest -q": cmd_result(exit_code=1, stderr="F")})
    root, store, engine = build_engine(tmp_path, config=config, runner=runner)
    task_id = "DR-0001"
    engine.create_task("t")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    events = engine.continue_task(task_id)
    task = store.read_task(task_id)
    assert task.state == S.BLOCKED
    assert task.blocked_code == "tests_failed"
    assert any("tests failed" in e for e in events)
    # failure evidence recorded, no review ran
    assert not task.review_history
    assert task.last_tests_passed is False


def test_failing_tests_can_auto_route_to_fix(tmp_path):
    config = load_config(None)
    config.tests.targeted = ["pytest -q"]
    config.pipeline.auto_fix_tests = True
    runner = FakeCommandRunner(
        results={"pytest -q": cmd_result(exit_code=1, stderr="F")}
    )
    root, store, engine = build_engine(tmp_path, config=config, runner=runner)
    task_id = "DR-0001"
    engine.create_task("t")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    engine.continue_task(task_id)
    task = store.read_task(task_id)
    assert task.state == S.FIX_REQUIRED

    # second round: tests now pass -> review request written (manual);
    # fix_iterations_used increments when the fix pass actually runs
    runner.results["pytest -q"] = cmd_result(exit_code=0, stdout="ok")
    engine.continue_task(task_id)
    task = store.read_task(task_id)
    assert task.state == S.REVIEWING
    assert task.implementation_passes == 2
    assert task.fix_iterations_used == 1


def test_provider_unavailable_leaves_state_for_retry(tmp_path):
    root, store, engine = build_engine(tmp_path, implementer=FakeImplementer(unavailable=True))
    task_id = "DR-0001"
    engine.create_task("t")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    events = engine.continue_task(task_id)
    task = store.read_task(task_id)
    assert task.state == S.IMPLEMENTING
    assert any("Codex CLI is not installed" in e for e in events)

    # user installs codex; same task continues from IMPLEMENTING
    engine2 = build_engine(tmp_path)[2]
    _to_reviewing(engine2, store, task_id)
    assert store.read_task(task_id).implementation_passes == 1


def test_implementer_nonzero_exit_marks_failed(tmp_path):
    root, store, engine = build_engine(
        tmp_path, implementer=FakeImplementer(exit_code=2, stderr="boom")
    )
    task_id = "DR-0001"
    engine.create_task("t")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    engine.continue_task(task_id)
    task = store.read_task(task_id)
    assert task.state == S.FAILED
    assert task.blocked_code == "implementer_failed"

    engine.unblock(task_id, reason="retry after fixing environment")
    assert store.read_task(task_id).state == S.PLAN_READY


def test_auto_reviewer_full_fix_loop_is_bounded(tmp_path):
    results = [
        make_review("REQUEST_CHANGES", [make_finding("P1")]),
        make_review("REQUEST_CHANGES", [make_finding("P1")]),
        make_review("REQUEST_CHANGES", [make_finding("P1")]),
        make_review("PASS"),
    ]
    implementer = FakeImplementer()
    reviewer = QueueReviewer(results)
    root, store, engine = build_engine(
        tmp_path, implementer=implementer, reviewer=reviewer
    )
    task_id = "DR-0001"
    engine.create_task("t")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    events = engine.continue_task(task_id)
    task = store.read_task(task_id)
    assert task.state == S.FINAL_GATE_REQUIRED
    assert task.implementation_passes == 4  # 1 impl + 3 fixes
    assert task.fix_iterations_used == 3
    assert len(task.review_history) == 4
    assert len(implementer.calls) == 4
    assert all(bundle.changed_files is not None for bundle in reviewer.bundles)
    assert any("FIX_REQUIRED" in e for e in events)


class _RaisingFormatReviewer(ReviewerProvider):
    name = "raising"

    @property
    def automatic(self):
        return True

    def prepare_request(self, bundle, review_number=None):
        return None

    def review(self, bundle):
        from devrelay.errors import ReviewFormatError

        raise ReviewFormatError("not json after retries")


def test_malformed_auto_review_json_blocks_not_guesses(tmp_path):
    root, store, engine = build_engine(
        tmp_path, reviewer=_RaisingFormatReviewer()
    )
    task_id = "DR-0001"
    engine.create_task("t")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    engine.continue_task(task_id)
    task = store.read_task(task_id)
    assert task.state == S.BLOCKED
    assert task.blocked_code == "review_format"


def test_secret_values_never_reach_artifacts(tmp_path, monkeypatch):
    secret = "sk-artifact-leak-check-1234567890"
    monkeypatch.setenv("DEVRELAY_FAKE_TOKEN", secret)
    implementer = FakeImplementer(
        stdout=f"report contains key {secret} and nothing else"
    )
    root, store, engine = build_engine(tmp_path, implementer=implementer)
    task_id = "DR-0001"
    engine.create_task("t")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    engine.continue_task(task_id)
    log_path = store.logs_dir(task_id) / "codex-01.stdout.log"
    content = log_path.read_text(encoding="utf-8")
    assert secret not in content
    assert "[REDACTED]" in content


def test_dirty_workspace_is_captured_not_blamed(tmp_path):
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "v1\n"})
    dirty_file(repo, "a.txt", content="v2-preexisting\n")
    store = ArtifactStore(repo)
    store.ensure_initialized()
    ws = GitWorkspace(repo, CommandRunner())
    from devrelay.pipeline.engine import DevRelayEngine

    from devrelay.providers.manual import ManualReviewer

    engine = DevRelayEngine(
        load_config(None),
        store,
        ws,
        implementer=FakeImplementer(),
        reviewer=ManualReviewer(),
        runner=CommandRunner(),
    )
    engine.create_task("t")
    task = store.read_task("DR-0001")
    assert task.initial_snapshot is not None
    assert "a.txt" in task.initial_snapshot.dirty_files
    assert task.initial_snapshot.is_dirty


def test_review_history_and_p3_survive(tmp_path):
    root, store, engine = build_engine(tmp_path)
    task_id = "DR-0001"
    engine.create_task("t")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    _to_reviewing(engine, store, task_id)
    engine.import_manual_review(
        task_id,
        make_review(
            "REQUEST_CHANGES",
            [make_finding("P3", title="style nit"), make_finding("P2", title="real bug")],
        ),
    )
    engine.continue_task(task_id)
    engine.import_manual_review(task_id, make_review("PASS"))
    task = store.read_task(task_id)
    assert len(task.review_history) == 2
    assert task.review_history[0].findings[0].severity == Severity.P3
    assert task.state == S.FINAL_GATE_REQUIRED
