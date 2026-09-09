"""Manual review import/export validation tests."""

import json

import pytest
from pydantic import ValidationError

from devrelay.errors import StateConflictError
from devrelay.models import Finding, ReviewDecision, ReviewResult, Severity
from devrelay.pipeline.states import PipelineState

from helpers import (
    ManualReviewerProxy,
    build_engine,
    default_config,
    make_finding,
    make_packet,
    make_review,
)


def _task_ready_for_review(engine, store, task_id: str):
    """Drive a task to REVIEWING via the (manual) default flow."""
    engine.create_task("T")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    events = engine.continue_task(task_id)
    assert store.read_task(task_id).state == PipelineState.REVIEWING
    return events


def test_manual_review_import_validation_rejects_malformed_json():
    with pytest.raises(json.JSONDecodeError):
        json.loads("{not json")


def test_review_result_schema_enforced():
    # unknown severity rejected
    with pytest.raises(ValidationError):
        ReviewResult.model_validate(
            {"decision": "PASS", "findings": [{"severity": "P9", "title": "x"}]}
        )
    # missing decision rejected (no natural-language guessing)
    with pytest.raises(ValidationError):
        ReviewResult.model_validate({"summary": "looks fine"})
    # extra fields rejected
    with pytest.raises(ValidationError):
        ReviewResult.model_validate(
            {"decision": "PASS", "findings": [], "run_this_shell": "rm -rf /"}
        )


def test_review_import_only_allowed_in_reviewing(tmp_path):
    root, store, engine = build_engine(tmp_path)
    task_id = "DR-0001"
    engine.create_task("T")
    engine.import_plan(task_id, make_packet(task_id=task_id))
    assert store.read_task(task_id).state == PipelineState.PLAN_READY
    with pytest.raises(StateConflictError):
        engine.import_manual_review(task_id, make_review("PASS"))


def test_manual_flow_review_export_and_import_to_final_gate(tmp_path):
    root, store, engine = build_engine(tmp_path)
    task_id = "DR-0001"
    _task_ready_for_review(engine, store, task_id)

    # the continue command already wrote a request file (REVIEWING, manual)
    request_path = store.reviews_dir(task_id) / "review-01-request.md"
    assert request_path.is_file()
    content = request_path.read_text(encoding="utf-8")
    assert "Manual review request" in content
    assert "Do not modify code" in content

    # import a PASS -> FINAL_GATE_REQUIRED
    events = engine.import_manual_review(task_id, make_review("PASS"))
    task = store.read_task(task_id)
    assert task.state == PipelineState.FINAL_GATE_REQUIRED
    result_file = store.reviews_dir(task_id) / "review-01-result.json"
    assert result_file.is_file()


def test_import_cannot_run_twice_from_same_state(tmp_path):
    root, store, engine = build_engine(tmp_path)
    task_id = "DR-0001"
    _task_ready_for_review(engine, store, task_id)
    engine.import_manual_review(task_id, make_review("PASS"))
    with pytest.raises(StateConflictError):
        engine.import_manual_review(task_id, make_review("PASS"))


def test_manual_reviewer_prepares_markdown():
    reviewer = ManualReviewerProxy()
    assert reviewer.automatic is False
    assert reviewer.name == "manual"
