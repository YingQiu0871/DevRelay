"""Pipeline policy — the single place that turns config into decisions."""

from __future__ import annotations

from devrelay.config import DevRelayConfig
from devrelay.models import (
    Finding,
    ReviewDecision,
    ReviewResult,
    RiskLevel,
    Severity,
    TaskRun,
)


class PipelinePolicy:
    """Pure decision helpers backed by the validated configuration.

    Nothing here writes state or talks to the outside world, which keeps the
    decision logic unit-testable.
    """

    def __init__(self, config: DevRelayConfig) -> None:
        self.config = config

    @property
    def max_fix_iterations(self) -> int:
        return self.config.pipeline.max_fix_iterations

    @property
    def blocking_severities(self) -> set[Severity]:
        return set(self.config.review.blocking_severities)

    def is_blocking(self, finding: Finding) -> bool:
        return finding.severity in self.blocking_severities

    def blocking_findings(self, review: ReviewResult) -> list[Finding]:
        return [f for f in review.findings if self.is_blocking(f)]

    def non_blocking_findings(self, review: ReviewResult) -> list[Finding]:
        return [f for f in review.findings if not self.is_blocking(f)]

    def effective_decision(
        self, review: ReviewResult
    ) -> tuple[ReviewDecision, list[Finding]]:
        """Map a raw review onto a pipeline decision.

        * ``BLOCKED`` decision from the reviewer -> BLOCKED.
        * Any finding whose severity is in ``blocking_severities`` ->
          REQUEST_CHANGES (severity beats a sloppy PASS).
        * Otherwise PASS (P3-only reviews pass unless P3 is configured as
          blocking).  A REQUEST_CHANGES decision without blocking findings
          therefore still passes — decisions come from policy, not wording.
        """
        blocking = self.blocking_findings(review)
        if review.decision == ReviewDecision.BLOCKED:
            return ReviewDecision.BLOCKED, blocking
        if blocking:
            return ReviewDecision.REQUEST_CHANGES, blocking
        return ReviewDecision.PASS, []

    def can_fix_again(self, task: TaskRun) -> bool:
        """Fix loop cap: max_fix_iterations, unless a human unblocked it."""
        if task.manual_override:
            return True
        return task.fix_iterations_used < self.max_fix_iterations

    def run_full_regression(self, risk_level: RiskLevel) -> bool:
        mode = self.config.tests.full_regression
        if mode == "always":
            return True
        if mode == "never":
            return False
        return risk_level == RiskLevel.RELEASE  # release_only
