"""v0.2-A acceptance: provider budget enforcement and usage accounting.

Covers A9 (reviewer budget), A10 (implementer budget), A11 (total budget) and
the rule that usage always comes from persisted call records.
"""

from __future__ import annotations

from devrelay.models import (
    ProviderCallPhase,
    ProviderCallRecord,
    ProviderKind,
    TaskRun,
    utcnow_iso,
)
from devrelay.pipeline.budget import BudgetExhaustedError, ProviderBudget
from devrelay.pipeline.states import PipelineState as S

from helpers import (
    FakeImplementer,
    ScriptedAutoReviewer,
    build_engine,
    default_config,
    make_finding,
    make_packet,
    make_review,
)


def _setup(tmp_path, *, max_impl=4, max_rev=4, max_total=8, outcomes=None, implementer=None):
    config = default_config()
    config.budget.max_implementer_calls = max_impl
    config.budget.max_reviewer_calls = max_rev
    config.budget.max_total_provider_calls = max_total
    reviewer = ScriptedAutoReviewer(outcomes or [])
    impl = implementer or FakeImplementer()
    root, store, engine = build_engine(
        tmp_path, config=config, implementer=impl, reviewer=reviewer
    )
    engine.create_task("t")
    engine.import_plan("DR-0001", make_packet(task_id="DR-0001"))
    return store, engine, reviewer, impl


# ---------------------------------------------------------------------------
# A9: reviewer budget exhausted -> reviewer never called
# ---------------------------------------------------------------------------
def test_reviewer_budget_preflight_blocks(tmp_path):
    store, engine, reviewer, impl = _setup(tmp_path, max_rev=0)
    engine.continue_task("DR-0001")
    task = store.read_task("DR-0001")

    assert task.state == S.BLOCKED
    assert task.blocked_code == "provider_budget_exhausted"
    assert "reviewer 0/0" in (task.blocked_reason or "")
    assert reviewer.bundles == []          # never invoked
    assert len(impl.calls) == 1            # the implementer did run once
    assert ProviderBudget.usage(task).reviewer_calls == 0


# ---------------------------------------------------------------------------
# A10: implementer budget exhausted before a fix
# ---------------------------------------------------------------------------
def test_implementer_budget_preflight_blocks(tmp_path):
    """The automatic loop wants a fix pass, but the budget forbids the call.

    ``continue_task`` loops from review straight into the fix attempt, so the
    budget gate fires inside the same call: the implementer must not run twice.
    """
    outcomes = [make_review("REQUEST_CHANGES", [make_finding("P2", title="bug")])]
    store, engine, reviewer, impl = _setup(tmp_path, max_impl=1, outcomes=outcomes)
    engine.continue_task("DR-0001")

    task = store.read_task("DR-0001")
    assert task.state == S.BLOCKED
    assert task.blocked_code == "provider_budget_exhausted"
    assert "implementer 1/1" in (task.blocked_reason or "")
    assert len(impl.calls) == 1            # no second implementer call
    assert len(reviewer.bundles) == 1      # reviewer ran exactly once

    # A further continue must not spend anything either.
    engine.continue_task("DR-0001")
    assert len(impl.calls) == 1


# ---------------------------------------------------------------------------
# A11: total budget exhausted -> no provider invocation at all
# ---------------------------------------------------------------------------
def test_total_budget_preflight_blocks(tmp_path):
    store, engine, reviewer, impl = _setup(
        tmp_path, max_impl=4, max_rev=4, max_total=1
    )
    engine.continue_task("DR-0001")
    task = store.read_task("DR-0001")

    assert task.state == S.BLOCKED
    assert task.blocked_code == "provider_budget_exhausted"
    assert "total 1/1" in (task.blocked_reason or "")
    assert len(impl.calls) == 1
    assert reviewer.bundles == []


# ---------------------------------------------------------------------------
# Usage comes from persisted records, never from iteration counters
# ---------------------------------------------------------------------------
def _record(kind: ProviderKind, external: int, phase: ProviderCallPhase) -> ProviderCallRecord:
    return ProviderCallRecord(
        call_id=f"{kind.value}-{phase.value}-{external}",
        provider_kind=kind,
        provider_name="test",
        phase=phase,
        external_call_count=external,
        completed_at=utcnow_iso(),
    )


def test_usage_counts_only_external_calls():
    task = TaskRun(task_id="DR-0001", title="t")
    task.fix_iterations_used = 99          # must not influence usage
    task.provider_calls = [
        _record(ProviderKind.IMPLEMENTER, 1, ProviderCallPhase.IMPLEMENT),
        _record(ProviderKind.IMPLEMENTER, 1, ProviderCallPhase.FIX),
        _record(ProviderKind.IMPLEMENTER, 0, ProviderCallPhase.IMPLEMENT),  # unavailable
        _record(ProviderKind.REVIEWER, 1, ProviderCallPhase.REVIEW),
        _record(ProviderKind.REVIEWER, 1, ProviderCallPhase.REVIEW_FORMAT_RETRY),
        _record(ProviderKind.REVIEWER, 0, ProviderCallPhase.MANUAL_REVIEW),
    ]
    usage = ProviderBudget.usage(task)
    assert usage.implementer_calls == 2
    assert usage.reviewer_calls == 2
    assert usage.total_calls == 4


def test_budget_check_raises_with_limits_in_message():
    config = default_config().budget
    config.max_implementer_calls = 1
    config.max_reviewer_calls = 1
    config.max_total_provider_calls = 2
    budget = ProviderBudget(config)
    task = TaskRun(task_id="DR-0001", title="t")
    task.provider_calls = [_record(ProviderKind.IMPLEMENTER, 1, ProviderCallPhase.IMPLEMENT)]

    with pytest_raises() as excinfo:
        budget.check(task, ProviderKind.IMPLEMENTER)   # 1 used + 1 > total 1
    message = str(excinfo.value)
    assert "provider budget exhausted" in message
    assert "implementer 1/1" in message
    assert "never resets" in message


class pytest_raises:
    """Tiny local raiser to keep the assertion readable without extra imports."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        assert exc_type is BudgetExhaustedError, f"unexpected: {exc_type}"
        self.value = exc
        return True


def test_budget_describe_lines(tmp_path):
    store, engine, _reviewer, _impl = _setup(tmp_path)
    task = store.read_task("DR-0001")
    lines = ProviderBudget(default_config().budget).describe(task)
    assert lines[0].startswith("Implementer  0 / 4")
    assert lines[1].startswith("Reviewer     0 / 4")
    assert lines[2].startswith("Total        0 / 8")
