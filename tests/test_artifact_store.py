"""Artifact store tests: persistence, resume, task layout."""

import pytest

from devrelay.artifacts.store import ArtifactStore
from devrelay.errors import DevRelayError, TaskNotFoundError
from devrelay.models import Finding, ReviewResult, Severity, TaskPacket, TaskRun
from devrelay.pipeline.states import PipelineState


def test_task_ids_are_sequential(tmp_path):
    store = ArtifactStore(tmp_path)
    store.ensure_initialized()
    assert store.allocate_task_id() == "DR-0001"
    assert store.allocate_task_id() == "DR-0002"
    assert store.allocate_task_id() == "DR-0003"


def test_write_read_roundtrip(tmp_path):
    store = ArtifactStore(tmp_path)
    store.ensure_initialized()
    task = TaskRun(
        task_id="DR-0001",
        title="Wear Tile",
        packet=TaskPacket(task_id="DR-0001", title="Wear Tile", objective="render"),
        state=PipelineState.PLAN_READY,
        plan_ready=True,
        review_history=[
            ReviewResult(
                findings=[Finding(severity=Severity.P3, title="nit")],
                summary="ok",
                decision="PASS",
            )
        ],
    )
    store.write_task(task)
    loaded = store.read_task("DR-0001")
    assert loaded == task
    assert loaded.state == PipelineState.PLAN_READY
    assert loaded.packet is not None
    assert loaded.packet.objective == "render"
    assert loaded.review_history[0].findings[0].severity == Severity.P3
    # index updated
    assert store.current_task_id() == "DR-0001"


def test_resume_across_store_instances(tmp_path):
    """State must survive process restart: new store object sees the task."""
    store1 = ArtifactStore(tmp_path)
    store1.ensure_initialized()
    task = TaskRun(
        task_id="DR-0001",
        title="t",
        state=PipelineState.REVIEWING,
        current_findings=[Finding(severity=Severity.P2, title="real bug")],
    )
    store1.write_task(task)

    store2 = ArtifactStore(tmp_path)  # fresh instance == process restart
    reloaded = store2.read_task("DR-0001")
    assert reloaded.state == PipelineState.REVIEWING
    assert reloaded.current_findings[0].severity == Severity.P2
    assert store2.current_task_id() == "DR-0001"


def test_artifact_layout_created(tmp_path):
    store = ArtifactStore(tmp_path)
    store.ensure_initialized()
    task = TaskRun(task_id="DR-0001", title="t")
    store.write_task(task)
    task_dir = store.task_dir("DR-0001")
    assert task_dir.is_dir()
    for sub in ("implementation", "reviews", "logs", "final"):
        assert (task_dir / sub).is_dir()


def test_task_not_found_raises(tmp_path):
    store = ArtifactStore(tmp_path)
    store.ensure_initialized()
    with pytest.raises(TaskNotFoundError):
        store.read_task("DR-9999")


def test_corrupt_state_json_raises_clean_error(tmp_path):
    store = ArtifactStore(tmp_path)
    store.ensure_initialized()
    state = store.state_path("DR-0001")
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text("{not json", encoding="utf-8")
    with pytest.raises(DevRelayError):
        store.read_task("DR-0001")


def test_no_tmp_files_left_behind(tmp_path):
    store = ArtifactStore(tmp_path)
    store.ensure_initialized()
    store.write_json(tmp_path / ".devrelay" / "probe.json", {"a": 1})
    leftovers = [p.name for p in (tmp_path / ".devrelay").iterdir() if ".tmp" in p.name]
    assert leftovers == []
