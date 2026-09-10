"""Provider call budget (v0.2-A).

Usage is always derived from persisted :class:`ProviderCallRecord` entries -
never inferred from iteration counters - so the accounting stays exact even
across restarts, format retries and interrupted runs.

The budget is checked *before* any external provider invocation; when the next
call would exceed a limit the engine blocks with
``blocked_code: provider_budget_exhausted`` and never calls the provider.
Budgets are never reset automatically.
"""

from __future__ import annotations

from devrelay.config import BudgetConfig
from devrelay.errors import ProviderError
from devrelay.models import ProviderKind, ProviderUsage, TaskRun


class BudgetExhaustedError(ProviderError):
    """Raised before a provider call that would exceed the task budget."""

    def __init__(self, kind: ProviderKind, usage: ProviderUsage, limits: BudgetConfig) -> None:
        self.kind = kind
        self.usage = usage
        self.limits = limits
        super().__init__(
            "provider budget exhausted: refusing to invoke "
            f"{kind.value.lower()} (implementer {usage.implementer_calls}/"
            f"{limits.max_implementer_calls}, reviewer {usage.reviewer_calls}/"
            f"{limits.max_reviewer_calls}, total {usage.total_calls}/"
            f"{limits.max_total_provider_calls}). DevRelay never resets a budget "
            "automatically; raise the limits in the task policy explicitly "
            "(and acknowledge with 'devrelay unblock --refresh-policy') if more "
            "calls are intended."
        )


class ProviderBudget:
    """Pre-flight checks and usage reporting for one task bullet policy."""

    def __init__(self, limits: BudgetConfig) -> None:
        self.limits = limits

    @staticmethod
    def usage(task: TaskRun) -> ProviderUsage:
        implementer = 0
        reviewer = 0
        for record in task.provider_calls:
            count = max(0, int(record.external_call_count))
            if record.provider_kind is ProviderKind.IMPLEMENTER:
                implementer += count
            else:
                reviewer += count
        return ProviderUsage(
            implementer_calls=implementer,
            reviewer_calls=reviewer,
            total_calls=implementer + reviewer,
        )

    def check(self, task: TaskRun, kind: ProviderKind) -> None:
        """Raise :class:`BudgetExhaustedError` if one more call is not allowed."""
        usage = self.usage(task)
        limits = self.limits
        would_total = usage.total_calls + 1
        blocked = would_total > limits.max_total_provider_calls
        if kind is ProviderKind.IMPLEMENTER:
            blocked = blocked or (usage.implementer_calls + 1 > limits.max_implementer_calls)
        else:
            blocked = blocked or (usage.reviewer_calls + 1 > limits.max_reviewer_calls)
        if blocked:
            raise BudgetExhaustedError(kind, usage, limits)

    def describe(self, task: TaskRun) -> list[str]:
        usage = self.usage(task)
        return [
            f"Implementer  {usage.implementer_calls} / {self.limits.max_implementer_calls}",
            f"Reviewer     {usage.reviewer_calls} / {self.limits.max_reviewer_calls}",
            f"Total        {usage.total_calls} / {self.limits.max_total_provider_calls}",
        ]
