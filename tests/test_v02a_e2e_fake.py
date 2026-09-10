"""v0.2-A independent engine-level E2E with fake providers (no real models).

Flow: FakeCodex #1 writes a buggy implementation -> FakeReviewer #1 returns a
P2 finding -> automatic FIX -> FakeCodex #2 fixes it -> FakeReviewer #2 PASS ->
FINAL_GATE_REQUIRED (never DONE).
"""

from __future__ import annotations

from pathlib import Path

from devrelay.models import ProviderExecutionResult, Severity
from devrelay.pipeline.states import PipelineState as S
from devrelay.providers.base import ImplementerProvider
from devrelay.providers.codex_cli import build_implementation_prompt

from helpers import (
    ScriptedAutoReviewer,
    build_engine,
    default_config,
    make_finding,
    make_packet,
    make_review,
)


class ScriptedFileImplementer(ImplementerProvider):
    """Fake Codex: first pass writes the buggy version, fix pass corrects it."""

    name = "fake-codex"

    def __init__(self) -> None:
        self.calls: list = []

    def availability(self) -> tuple[bool, str]:
        return (True, "fake codex")

    def run(self, context) -> ProviderExecutionResult:
        self.calls.append(context)
        root = Path(context.workspace_root)
        if len(self.calls) == 1:
            (root / "app.py").write_text('def greet():\n    return "hello"\n', encoding="utf-8")
            (root / "test_app.py").write_text(
                'from app import greet\n\n\ndef test_greet():\n    assert greet() == "hello world"\n',
                encoding="utf-8",
            )
            report = "attempt 1: wrote buggy implementation"
        else:
            (root / "app.py").write_text(
                'def greet():\n    return "hello world"\n', encoding="utf-8"
            )
            report = "attempt 2: fixed greet() to return 'hello world'"
        return ProviderExecutionResult(
            exit_code=0, stdout=report, report=report
        )


def _blocking_review():
    return make_review(
        "REQUEST_CHANGES",
        [
            make_finding("P2", title="greet returns wrong value").model_copy(
                update={
                    "id": "P2-01",
                    "description": "returns 'hello' instead of 'hello world'",
                    "files": ["app.py"],
                    "evidence": "test_app.py expects 'hello world'",
                    "recommendation": "return exactly 'hello world'",
                }
            )
        ],
        summary="one blocking P2",
    )


def test_fake_provider_end_to_end_loop(tmp_path):
    config = default_config()
    implementer = ScriptedFileImplementer()
    reviewer = ScriptedAutoReviewer([_blocking_review(), make_review("PASS", summary="fixed")])

    _root, store, engine = build_engine(
        tmp_path,
        config=config,
        implementer=implementer,
        reviewer=reviewer,
        use_real_git=True,
    )
    engine.create_task("Change greet output to hello world")
    engine.import_plan("DR-0001", make_packet(task_id="DR-0001"))
    events = engine.continue_task("DR-0001")

    task = store.read_task("DR-0001")

    # ---- state machine path -------------------------------------------------
    assert task.state == S.FINAL_GATE_REQUIRED
    assert task.state is not S.DONE            # final gate stays manual
    visited = [event.to_state for event in task.audit]
    for expected in (
        "PLAN_READY",
        "IMPLEMENTING",
        "TESTING",
        "REVIEWING",
        "FIX_REQUIRED",
        "FIXING",
        "FINAL_GATE_REQUIRED",
    ):
        assert expected in visited, f"{expected} missing from {visited}"

    # ---- exact external call accounting ------------------------------------
    assert len(implementer.calls) == 2
    assert len(reviewer.bundles) == 2
    assert [r.provider_kind.value for r in task.provider_calls] == [
        "IMPLEMENTER",
        "REVIEWER",
        "IMPLEMENTER",
        "REVIEWER",
    ]
    assert sum(r.external_call_count for r in task.provider_calls) == 4
    usage = engine.usage_block("DR-0001")
    assert (usage["implementer_calls"], usage["reviewer_calls"], usage["total_calls"]) == (2, 2, 4)
    assert usage["max_implementer_calls"] == 4
    assert usage["max_total_provider_calls"] == 8

    # ---- findings persisted, handed to the fix, visible to review #2 --------
    assert task.review_history[0].findings[0].severity is Severity.P2
    assert task.review_history[0].findings[0].fingerprint
    fix_context = implementer.calls[1]
    assert fix_context.is_fix is True
    assert fix_context.findings[0].id == "P2-01"
    fix_prompt = build_implementation_prompt(fix_context)
    assert "[P2]" in fix_prompt and "greet returns wrong value" in fix_prompt
    assert "files: app.py" in fix_prompt
    assert reviewer.bundles[1].previous_reviews

    # ---- attempts / review attempts persisted ------------------------------
    assert [a.phase for a in task.attempts] == ["IMPLEMENT", "FIX"]
    assert all(a.status.value == "COMPLETED" for a in task.attempts)
    assert [a.status.value for a in task.review_attempts] == ["COMPLETED", "COMPLETED"]
    assert task.review_call_in_flight is False
    assert task.attempt_in_flight is False

    # ---- review artifacts ---------------------------------------------------
    reviews = store.reviews_dir("DR-0001")
    for name in (
        "review-01-result.json",
        "review-01-meta.json",
        "review-01-call-01-meta.json",
        "review-02-result.json",
        "review-02-meta.json",
        "review-02-call-01-meta.json",
    ):
        assert (reviews / name).is_file(), f"{name} missing"

    # ---- implementation artifacts ------------------------------------------
    assert (store.implementation_dir("DR-0001") / "iteration-01.md").is_file()
    assert (store.implementation_dir("DR-0001") / "iteration-02.md").is_file()

    # ---- the fix was actually applied to the workspace ---------------------
    assert "hello world" in (Path(engine.workspace.root) / "app.py").read_text(encoding="utf-8")
    assert any("review passed" in line for line in events)
