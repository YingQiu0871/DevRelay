"""Provider abstractions for DevRelay."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from devrelay.models import Finding, ProviderExecutionResult, ReviewResult, TaskPacket

from devrelay.artifacts.renderer import ReviewBundle

if TYPE_CHECKING:  # pragma: no cover - typing only
    from devrelay.providers.evidence import ReviewCallPolicy


@dataclass
class RuntimePlan:
    """Engine-owned Codex runtime plan for one attempt (v0.2-C).

    The engine builds it *before* the control-plane PRE manifest is captured, so
    every artifact it references already exists when the guard starts watching.
    """

    runtime_mode: str
    argv: list[str]
    env_remove: list[str]
    staging_path: str
    schema_path: str
    workdir: str
    prompt: str
    attempt_id: str = ""
    call_id: str = ""
    capabilities: str = ""


@dataclass
class ImplementerContext:
    """Everything the implementer provider needs for one pass."""

    task_id: str
    packet: TaskPacket
    attempt: int
    workspace_root: str
    is_fix: bool = False
    findings: list[Finding] = field(default_factory=list)
    reuse_approved_scope: bool = True
    current_delta_first: bool = True
    # v0.2-C: prompt text (built by the engine so the exact bytes are hashed
    # before the run) and the runtime plan for structured Codex execution.
    prompt: str = ""
    plan: "RuntimePlan | None" = None


class ImplementerProvider(ABC):
    """Runs an implementation pass inside the workspace."""

    name: str = "implementer"

    @abstractmethod
    def availability(self) -> tuple[bool, str]:
        """Return (available, human-readable diagnostic). Never raises."""

    @abstractmethod
    def run(self, context: ImplementerContext) -> ProviderExecutionResult:
        """Execute one implementation pass. Never raises provider errors."""


class ReviewerProvider(ABC):
    """Reviews a task delta. Manual reviewers stop at REVIEWING; automatic
    (API-based) reviewers run inside ``devrelay continue``."""

    name: str = "reviewer"

    @property
    def automatic(self) -> bool:
        return False

    @property
    def model(self) -> str | None:
        """Model identity for evidence purposes (never a token)."""
        return None

    @property
    def endpoint_host(self) -> str | None:
        """Endpoint host for evidence purposes (never credentials/query)."""
        return None

    @abstractmethod
    def prepare_request(
        self, bundle: ReviewBundle, review_number: int | None = None
    ) -> str | None:
        """Return request text for a manual reviewer (None for automatic)."""

    def review(
        self,
        bundle: ReviewBundle,
        *,
        call_policy: "ReviewCallPolicy | None" = None,
    ) -> ReviewResult:
        """Run an automatic review (only valid when ``automatic`` is True).

        ``call_policy`` carries the task-scoped retry/size policy; providers
        with no external calls (manual reviewers) simply ignore it.
        """
        from devrelay.errors import ProviderUnavailableError

        raise ProviderUnavailableError(
            f"reviewer provider '{self.name}' is manual; it cannot run "
            "automatically. Use 'devrelay review export' / 'review import'."
        )
