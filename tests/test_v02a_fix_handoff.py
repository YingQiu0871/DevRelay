"""v0.2-A acceptance: auto-fix handoff, previous-findings handoff, fingerprints."""

from __future__ import annotations

from dataclasses import replace

from devrelay.models import Finding, Severity
from devrelay.pipeline.review_lifecycle import (
    finding_fingerprint,
    mark_findings,
    stalled_findings,
)
from devrelay.pipeline.states import PipelineState as S
from devrelay.providers.base import ImplementerContext
from devrelay.providers.codex_cli import build_implementation_prompt

from helpers import (
    FakeImplementer,
    ScriptedAutoReviewer,
    build_engine,
    make_finding,
    make_packet,
    make_review,
)


def _finding(**overrides) -> Finding:
    base = Finding(
        id="P2-01",
        severity=Severity.P2,
        title="greet returns wrong value",
        description="returns 'hello' instead of 'hello world'",
        files=["app.py"],
        evidence="python -m pytest -q fails on test_app.py::test_greet",
        recommendation="return exactly 'hello world'",
    )
    return base.model_copy(update=overrides)


# ---------------------------------------------------------------------------
# A14: the FIX prompt carries fully structured findings
# ---------------------------------------------------------------------------
def test_fix_prompt_contains_structured_findings():
    context = ImplementerContext(
        task_id="DR-0001",
        packet=make_packet(task_id="DR-0001"),
        attempt=2,
        workspace_root="/fake/ws",
        is_fix=True,
        findings=[_finding()],
    )
    prompt = build_implementation_prompt(context)

    assert "[P2]" in prompt
    assert "id=P2-01" in prompt
    assert "title=greet returns wrong value" in prompt
    assert "description: returns 'hello' instead of 'hello world'" in prompt
    assert "files: app.py" in prompt
    assert "evidence: python -m pytest -q fails on test_app.py::test_greet" in prompt
    assert "recommendation: return exactly 'hello world'" in prompt
    # the packet and iteration context stay present
    assert "Implementation attempt: 2" in prompt
    assert "## Objective" in prompt
    assert "## Scope (implement ONLY this)" in prompt


# ---------------------------------------------------------------------------
# A15: findings flow automatically into the fix pass and the next review
# ---------------------------------------------------------------------------
def test_second_review_sees_previous_findings(tmp_path):
    blocker = make_review("REQUEST_CHANGES", [_finding()], summary="one P2 blocker")
    reviewer = ScriptedAutoReviewer([blocker, make_review("PASS")])
    impl = FakeImplementer()
    _root, store, engine = build_engine(tmp_path, implementer=impl, reviewer=reviewer)
    engine.create_task("t")
    engine.import_plan("DR-0001", make_packet(task_id="DR-0001"))
    engine.continue_task("DR-0001")

    task = store.read_task("DR-0001")
    assert task.state == S.FINAL_GATE_REQUIRED
    assert len(impl.calls) == 2

    # the fix pass received the structured finding
    fix_context = impl.calls[1]
    assert fix_context.is_fix is True
    assert [f.id for f in fix_context.findings] == ["P2-01"]
    assert fix_context.findings[0].files == ["app.py"]

    # the second review request carried the previous findings
    second_bundle = reviewer.bundles[1]
    assert second_bundle.previous_reviews, "review #2 must see review #1"
    assert second_bundle.previous_reviews[0].findings[0].title == "greet returns wrong value"
    from devrelay.artifacts.renderer import render_review_user_prompt

    prompt = render_review_user_prompt(second_bundle)
    assert "Reviewer findings history".lower() in prompt.lower() or "review #1" in prompt
    assert "greet returns wrong value" in prompt


# ---------------------------------------------------------------------------
# A16: deterministic fingerprints
# ---------------------------------------------------------------------------
def test_finding_fingerprint_is_deterministic():
    first = _finding()
    second = _finding(id="renumbered-by-the-model", severity=Severity.P2)
    assert finding_fingerprint(first) == finding_fingerprint(second)

    # whitespace/case normalisation
    assert finding_fingerprint(_finding(title="  GREET   returns wrong value ")) == (
        finding_fingerprint(_finding(title="greet returns wrong value"))
    )

    # semantic changes produce a different fingerprint
    assert finding_fingerprint(first) != finding_fingerprint(
        _finding(severity=Severity.P1)
    )
    assert finding_fingerprint(first) != finding_fingerprint(
        _finding(files=["other.py"])
    )
    assert finding_fingerprint(first) != finding_fingerprint(
        _finding(description="a different root cause entirely")
    )


def test_fingerprints_and_seen_counts_are_recorded(tmp_path):
    review = make_review("REQUEST_CHANGES", [_finding()])
    task = make_packet(task_id="DR-0001")
    from devrelay.models import TaskRun

    run = TaskRun(task_id="DR-0001", title="t")
    marked = mark_findings(review, run)
    assert marked.findings[0].fingerprint
    fingerprint = marked.findings[0].fingerprint
    assert run.finding_seen_counts == {fingerprint: 1}

    # second round with the same blocker (different id) bumps the counter
    marked2 = mark_findings(make_review("REQUEST_CHANGES", [_finding(id="P2-99")]), run)
    assert marked2.findings[0].fingerprint == fingerprint
    assert run.finding_seen_counts[fingerprint] == 2

    # the stall helper only reports findings that reached the configured count
    assert stalled_findings(marked2, run, 0) == []
    assert stalled_findings(marked2, run, 2) == list(marked2.findings)
    assert stalled_findings(marked2, run, 3) == []
