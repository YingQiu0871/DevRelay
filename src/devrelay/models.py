"""Core data models for DevRelay.

Everything that crosses a module boundary or is persisted as JSON is a
Pydantic model here so that machine-readable state is always validated.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from devrelay.pipeline.states import PipelineState


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RiskLevel(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    RELEASE = "RELEASE"


class Severity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


SEVERITY_ORDER: list[Severity] = [
    Severity.P0,
    Severity.P1,
    Severity.P2,
    Severity.P3,
]


class ReviewDecision(str, Enum):
    PASS = "PASS"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    BLOCKED = "BLOCKED"


def _coerce_lines(value: Any) -> list[str]:
    """Accept a single string, a multi-line string or a list -> clean strings."""
    if value is None:
        return []
    if isinstance(value, str):
        lines = [ln.strip() for ln in value.splitlines() if ln.strip()]
        return lines
    if isinstance(value, (list, tuple)):
        out: list[str] = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                out.append(text)
        return out
    raise ValueError(
        f"expected a string or a list of strings, got {type(value).__name__}"
    )


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


class TaskPacket(BaseModel):
    """The standard task specification produced by the (manual) planner."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    title: str = ""
    objective: str = ""
    scope: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    tests_required: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.NORMAL
    notes: str = ""

    @field_validator(
        "scope",
        "out_of_scope",
        "acceptance_criteria",
        "constraints",
        "tests_required",
        mode="before",
    )
    @classmethod
    def _lists(cls, value: Any) -> Any:
        return _coerce_lines(value)

    @field_validator("title", "objective", "notes", mode="before")
    @classmethod
    def _texts(cls, value: Any) -> str:
        return _coerce_text(value)


class Finding(BaseModel):
    """A structured reviewer finding. Severity P0-P3."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    severity: Severity
    title: str
    description: str = ""
    files: list[str] = Field(default_factory=list)
    evidence: str = ""
    recommendation: str = ""

    @field_validator("files", mode="before")
    @classmethod
    def _files(cls, value: Any) -> Any:
        return _coerce_lines(value)

    @field_validator("title", "description", "evidence", "recommendation", mode="before")
    @classmethod
    def _texts(cls, value: Any) -> str:
        return _coerce_text(value)

    @field_validator("title")
    @classmethod
    def _title_required(cls, value: str) -> str:
        if not value:
            raise ValueError("Finding 'title' must not be empty")
        return value


class ReviewResult(BaseModel):
    """A complete review: findings + summary + machine decision."""

    model_config = ConfigDict(extra="forbid")

    findings: list[Finding] = Field(default_factory=list)
    summary: str = ""
    decision: ReviewDecision
    reviewer: str = ""

    @field_validator("summary", mode="before")
    @classmethod
    def _summary(cls, value: Any) -> str:
        return _coerce_text(value)


class CommandResult(BaseModel):
    """Result of one subprocess invocation (always shell=False)."""

    model_config = ConfigDict(extra="forbid")

    command: list[str]
    cwd: str | None = None
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    timed_out: bool = False
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None and not self.timed_out and self.exit_code == 0


class ProviderExecutionResult(BaseModel):
    """Result of running an implementer provider (e.g. Codex CLI)."""

    model_config = ConfigDict(extra="forbid")

    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    timed_out: bool = False
    error: str | None = None
    report: str = ""

    @property
    def success(self) -> bool:
        return self.error is None and not self.timed_out and self.exit_code == 0


class TestRunResult(BaseModel):
    """Result of one test command."""

    model_config = ConfigDict(extra="forbid")

    name: str
    command: list[str]
    ok: bool = False
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    timed_out: bool = False
    error: str | None = None


class WorkspaceSnapshot(BaseModel):
    """Immutable snapshot of the workspace taken at task start."""

    model_config = ConfigDict(extra="forbid")

    repo_root: str | None = None
    head_sha: str | None = None
    branch: str | None = None
    dirty_files: list[str] = Field(default_factory=list)
    has_git: bool = True
    captured_at: str = Field(default_factory=utcnow_iso)

    @property
    def is_dirty(self) -> bool:
        return bool(self.dirty_files)


class TransitionEvent(BaseModel):
    """One audited pipeline transition."""

    model_config = ConfigDict(extra="forbid")

    from_state: str
    to_state: str
    at: str = Field(default_factory=utcnow_iso)
    note: str = ""
    by: str = "system"


class FinalGateRecord(BaseModel):
    """Manual final-gate approval."""

    model_config = ConfigDict(extra="forbid")

    approved_by: str = "manual"
    approved_at: str = Field(default_factory=utcnow_iso)
    note: str = ""


class TaskRun(BaseModel):
    """Persisted per-task runtime state (tasks/<id>/state.json)."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    title: str
    packet: TaskPacket | None = None
    state: PipelineState = PipelineState.NEW
    plan_ready: bool = False
    created_at: str = Field(default_factory=utcnow_iso)
    updated_at: str = Field(default_factory=utcnow_iso)

    # Counters (machine truth, not display strings).
    implementation_passes: int = 0
    fix_iterations_used: int = 0

    initial_snapshot: WorkspaceSnapshot | None = None
    blocked_reason: str | None = None
    blocked_code: str | None = None
    manual_override: bool = False

    current_findings: list[Finding] = Field(default_factory=list)
    open_p3: list[Finding] = Field(default_factory=list)
    last_review: ReviewResult | None = None
    review_history: list[ReviewResult] = Field(default_factory=list)

    last_tests_passed: bool | None = None
    test_evidence: list[str] = Field(default_factory=list)
    implementation_report_paths: list[str] = Field(default_factory=list)

    final_gate: FinalGateRecord | None = None
    audit: list[TransitionEvent] = Field(default_factory=list)

    @property
    def next_attempt(self) -> int:
        """1-based attempt number for the next implementation pass."""
        return max(1, self.implementation_passes + 1)

    @property
    def open_blocking_findings(self) -> list[Finding]:
        return list(self.current_findings)
