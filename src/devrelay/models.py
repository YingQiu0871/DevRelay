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
    # Deterministic identity of the finding across review rounds (v0.2-A);
    # excludes the per-round finding id on purpose.
    fingerprint: str = ""

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
    # Bounded-capture evidence (v0.2-C): totals and truncation flags make a
    # capped stream auditable instead of silently shortened.
    stdout_bytes_total: int = 0
    stderr_bytes_total: int = 0
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    # Strong process-containment evidence (structured runtime only).
    containment: str = ""
    containment_all_dead: bool = False
    containment_error: str = ""

    @property
    def success(self) -> bool:
        return self.error is None and not self.timed_out and self.exit_code == 0


class BinaryCommandResult(BaseModel):
    """Byte-exact subprocess result (no newline translation, no re-encoding).

    Used for git binary-sensitive transport (``git diff --binary`` output,
    ``git apply --cached --binary -`` input) where byte fidelity is required.
    """

    model_config = ConfigDict(extra="forbid")

    command: list[str]
    cwd: str | None = None
    exit_code: int | None = None
    stdout: bytes = b""
    stderr: bytes = b""
    duration_seconds: float = 0.0
    stdout_bytes_total: int = 0
    stderr_bytes_total: int = 0
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    containment: str = ""
    containment_all_dead: bool = False
    containment_error: str = ""
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

    # v0.2-C structured runtime evidence (advisory; the engine persists it).
    runtime_mode: str = "text"
    structured_result: ImplementationResult | None = None
    raw_result_sha256: str = ""
    result_bytes_total: int = 0
    staging_path: str = ""
    events_summary: dict | None = None
    runtime_warnings: list[str] = Field(default_factory=list)
    argv: list[str] = Field(default_factory=list)
    env_removed: list[str] = Field(default_factory=list)
    capabilities: str = ""
    result_error_code: str = ""
    result_error: str = ""
    rejected_path_claims: list[str] = Field(default_factory=list)
    unknown_result_fields: list[str] = Field(default_factory=list)
    session_id: str = ""
    stdout_bytes_total: int = 0
    stderr_bytes_total: int = 0
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    containment: str = ""
    containment_all_dead: bool = False
    containment_error: str = ""

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


# ---------------------------------------------------------------------------
# v0.1 RC hardening: baseline / policy guard / task-delta models
# ---------------------------------------------------------------------------

class PolicyViolationType(str, Enum):
    UNEXPECTED_HEAD_CHANGE = "UNEXPECTED_HEAD_CHANGE"
    UNEXPECTED_BRANCH_CHANGE = "UNEXPECTED_BRANCH_CHANGE"
    UNEXPECTED_TAG_CHANGE = "UNEXPECTED_TAG_CHANGE"
    UNEXPECTED_REF_CHANGE = "UNEXPECTED_REF_CHANGE"
    UNEXPECTED_INDEX_MUTATION = "UNEXPECTED_INDEX_MUTATION"
    POLICY_CHECK_INCOMPLETE = "POLICY_CHECK_INCOMPLETE"


class IndexSnapshotStatus(str, Enum):
    """Whether the real index could be captured reliably (fail closed)."""

    OK = "OK"
    UNAVAILABLE = "UNAVAILABLE"
    CONFLICTED = "CONFLICTED"
    ERROR = "ERROR"


class AttemptStatus(str, Enum):
    IN_FLIGHT = "IN_FLIGHT"
    COMPLETED = "COMPLETED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    INTERRUPTED = "INTERRUPTED"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    POLICY_CHECK_INCOMPLETE = "POLICY_CHECK_INCOMPLETE"


class ProviderKind(str, Enum):
    IMPLEMENTER = "IMPLEMENTER"
    REVIEWER = "REVIEWER"


class ProviderCallPhase(str, Enum):
    IMPLEMENT = "IMPLEMENT"
    FIX = "FIX"
    REVIEW = "REVIEW"
    REVIEW_FORMAT_RETRY = "REVIEW_FORMAT_RETRY"
    REVIEW_TRANSPORT_RETRY = "REVIEW_TRANSPORT_RETRY"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class CallErrorType(str, Enum):
    TRANSPORT = "TRANSPORT"
    TIMEOUT = "TIMEOUT"
    HTTP_STATUS = "HTTP_STATUS"
    FORMAT = "FORMAT"
    RESPONSE_TOO_LARGE = "RESPONSE_TOO_LARGE"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    EXCEPTION = "EXCEPTION"


class ReviewAttemptStatus(str, Enum):
    IN_FLIGHT = "IN_FLIGHT"
    COMPLETED = "COMPLETED"
    FORMAT_FAILED = "FORMAT_FAILED"
    TRANSPORT_FAILED = "TRANSPORT_FAILED"
    INTERRUPTED = "INTERRUPTED"
    BUDGET_BLOCKED = "BUDGET_BLOCKED"


class ProviderCallRecord(BaseModel):
    """One attempted external provider invocation (v0.2-A accounting unit).

    ``external_call_count`` is 1 when a real external model call was attempted
    (including attempts that failed after the request was started) and 0 for
    events that never left the machine (manual review, unavailable CLI). It is
    the single authority for budget accounting.

    ``call_id`` comes from a durable task-scoped sequence (``DR-0001-C0007``),
    allocated and persisted *before* the invocation, so identities never repeat
    across restarts, unblocks or retries.  Never persists credentials, API keys,
    authorization headers or full URLs.
    """

    model_config = ConfigDict(extra="forbid")

    call_id: str
    provider_kind: ProviderKind
    provider_name: str
    phase: ProviderCallPhase
    started_at: str = Field(default_factory=utcnow_iso)
    completed_at: str | None = None
    success: bool = False
    attempt_number: int = 1
    task_iteration: int = 1
    duration_seconds: float = 0.0
    external_call_count: int = 0
    error_type: CallErrorType | None = None
    error: str | None = None
    model: str | None = None
    endpoint_host: str | None = None
    # Traceability (v0.2-A remediation): which attempt/round caused this call.
    parent_attempt_id: str | None = None
    review_number: int | None = None


class AppliedReviewRecord(BaseModel):
    """Durable marker: one persisted ReviewResult was semantically applied.

    ``identity`` is the fingerprint-insensitive hash of the sanitized,
    normalized review, so a restart replay can prove whether a result already
    reached ``review_history`` instead of guessing from list lengths.
    """

    model_config = ConfigDict(extra="forbid")

    identity: str
    review_number: int
    attempt_id: str | None = None
    review_file: str = ""
    decision: str = ""
    state: str = ""
    findings: int = 0
    applied_at: str = Field(default_factory=utcnow_iso)
    # Progress snapshot at application time: lets a restart decide whether a
    # missing terminal transition must be completed (nothing happened since) or
    # whether the task legitimately moved on into a new review round.
    fix_iterations: int = 0
    implementation_passes: int = 0


class PolicyRefreshRecord(BaseModel):
    """Audited before/after evidence for one explicit policy refresh."""

    model_config = ConfigDict(extra="forbid")

    refresh_id: str
    at: str = Field(default_factory=utcnow_iso)
    by: str = "human"
    reason: str = ""
    before_source: str = ""
    after_source: str = ""
    before_config_sha256: str = ""
    after_config_sha256: str = ""
    before_path: str = ""
    after_path: str = ""
    record_path: str = ""
    # v0.2-B: generation-bound refresh/recovery provenance.
    generation: int = 0
    after_generation: int = 0
    trigger: str = "explicit_refresh"
    before_state: str = ""
    before_snapshot_available: bool = True
    before_sha256: str = ""
    after_sha256: str = ""
    usage_unchanged: bool = True
    # Refresh *evidence attempt* number, deliberately distinct from
    # ``generation``: every attempt that starts writing evidence consumes a
    # never-reused number, so a failed attempt's artifacts survive a retry
    # untouched.  A successful retry may therefore be attempt 02 while advancing
    # generation 1 -> 2.
    evidence_attempt: int = 0


class ReviewAttempt(BaseModel):
    """Lifecycle of one automatic (or imported manual) review round.

    ``review_number`` is the *semantic* round (which review of this task it is);
    ``attempt_id`` is the durable identity of this execution of that round.
    One semantic round can have several attempts (interrupted call, explicit
    acknowledgement, retry), so the two must never be conflated.
    """

    model_config = ConfigDict(extra="forbid")

    review_number: int
    attempt_id: str
    provider_name: str
    status: ReviewAttemptStatus = ReviewAttemptStatus.IN_FLIGHT
    started_at: str = Field(default_factory=utcnow_iso)
    completed_at: str | None = None
    model: str | None = None
    endpoint_host: str | None = None
    format_attempts: int = 0
    transport_attempts: int = 0
    external_calls_consumed: int = 0
    call_ids: list[str] = Field(default_factory=list)
    error_type: CallErrorType | None = None
    error: str | None = None
    result: ReviewResult | None = None
    # Result lifecycle (v0.2-A remediation). Three distinct milestones:
    #   CALL COMPLETED      -> status == COMPLETED (result may still be missing)
    #   RESULT PERSISTED    -> result_persisted + result_hash (authoritative,
    #                          sanitized, schema-valid; replayable after a crash)
    #   RESULT APPLIED      -> result_applied + applied_at/applied_state
    # A persisted-but-unapplied result is replayed locally on restart with
    # ZERO additional external calls; an uncertain call fails closed instead.
    result_persisted: bool = False
    result_hash: str = ""
    result_applied: bool = False
    applied_at: str | None = None
    applied_state: str | None = None


class ProviderUsage(BaseModel):
    """Counts derived from persisted call records (never from iteration math)."""

    model_config = ConfigDict(extra="forbid")

    implementer_calls: int = 0
    reviewer_calls: int = 0
    total_calls: int = 0


class PolicyViolation(BaseModel):
    """A structured repository-policy violation detected after a provider run."""

    model_config = ConfigDict(extra="forbid")

    id: str
    type: PolicyViolationType
    severity: Severity = Severity.P0
    detected_at: str = Field(default_factory=utcnow_iso)
    before: dict[str, str | None] = Field(default_factory=dict)
    after: dict[str, str | None] = Field(default_factory=dict)
    description: str = ""
    blocking: bool = True


class RepoSnapshot(BaseModel):
    """Point-in-time read-only snapshot of repository control state."""

    model_config = ConfigDict(extra="forbid")

    captured_at: str = Field(default_factory=utcnow_iso)
    head_sha: str | None = None
    branch: str | None = None
    index_tree_sha: str | None = None
    # Index capture reliability.  UNAVAILABLE/CONFLICTED/ERROR must never be
    # read as "no change": policy comparison fails closed for those.
    index_snapshot_status: IndexSnapshotStatus = IndexSnapshotStatus.OK
    index_snapshot_error: str | None = None
    index_status_porcelain: str = ""
    index_unmerged_entries: list[str] = Field(default_factory=list)
    # sorted "refname objectname" lines for local refs (tags excluded here)
    local_refs: list[str] = Field(default_factory=list)
    # sorted "tagname objectname" lines
    tags: list[str] = Field(default_factory=list)
    note: str = ""


# Structured implementer result contract version (v0.2-C), distinct from
# STATE_SCHEMA_VERSION below.
IMPLEMENTATION_RESULT_SCHEMA_VERSION = 1


class AttemptMilestone(str, Enum):
    """Durable implementer lifecycle (v0.2-C).

    "provider process finished" and "completion applied to pipeline state" are
    different facts; the milestone records which one is durable.
    """

    IN_FLIGHT = "IN_FLIGHT"
    PROCESS_EXITED = "PROCESS_EXITED"
    WORKSPACE_OBSERVED = "WORKSPACE_OBSERVED"
    GUARD_VERDICT_PERSISTED = "GUARD_VERDICT_PERSISTED"
    RESULT_PERSISTED = "RESULT_PERSISTED"
    COMPLETION_READY = "COMPLETION_READY"
    COMPLETION_APPLIED = "COMPLETION_APPLIED"


class WorkspaceIdentity(BaseModel):
    """Authoritative workspace/guard identity recorded for one attempt."""

    model_config = ConfigDict(extra="forbid")

    worktree_tree_sha: str = ""
    delta_identity: str = ""
    guard_identity: str = ""
    head_sha: str | None = None
    branch: str | None = None
    index_tree_sha: str | None = None
    changed_files: list[str] = Field(default_factory=list)
    observed_at: str = Field(default_factory=utcnow_iso)


class TestClaim(BaseModel):
    """One test run *claimed* by the model (always advisory)."""

    model_config = ConfigDict(extra="forbid")

    command: str = ""
    result: str = "NOT_RUN"          # PASS | FAIL | NOT_RUN
    notes: str = ""


class ImplementationResult(BaseModel):
    """Structured implementer result (advisory evidence, schema version 1)."""

    model_config = ConfigDict(extra="ignore")

    schema_version: int = IMPLEMENTATION_RESULT_SCHEMA_VERSION
    status: str = "COMPLETE"         # COMPLETE | PARTIAL | BLOCKED | FAILED
    summary: str = ""
    changed_files: list[str] = Field(default_factory=list)
    tests_run: list[TestClaim] = Field(default_factory=list)
    unresolved_items: list[str] = Field(default_factory=list)
    known_risks: list[str] = Field(default_factory=list)


class AttemptRuntimeEvidence(BaseModel):
    """Paths/hashes of the immutable runtime evidence for one attempt."""

    model_config = ConfigDict(extra="forbid")

    runtime_mode: str = "text"       # structured | text
    result_path: str = ""
    result_sha256: str = ""
    raw_result_sha256: str = ""
    result_status: str = ""
    result_schema_version: int | None = None
    events_path: str = ""
    events_sha256: str = ""
    session_id: str = ""
    model: str = ""
    staging_file: str = ""
    staging_removed: bool = False
    warnings: list[str] = Field(default_factory=list)
    implementation_reconciliation_path: str = ""
    test_reconciliation_paths: list[str] = Field(default_factory=list)
    control_plane_pre_sha256: str = ""
    control_plane_post_sha256: str = ""
    # SHA-256 of the exact state.json bytes written by the COMPLETION_READY
    # write; any later external edit changes it and blocks replay.
    state_sha256_at_ready: str = ""
    control_plane_changes: int = 0
    result_claimed: bool = False
    # Strong process containment: the mechanism that guarantees no descendant of
    # the Codex child can outlive it (and therefore can never mutate the control
    # plane after the POST check).
    containment: str = ""                 # e.g. windows-job-object | none
    containment_all_dead: bool = False    # parent-verified before POST
    containment_error: str = ""


class ControlPlaneDifference(BaseModel):
    """One control-plane change (metadata only; never raw content)."""

    model_config = ConfigDict(extra="forbid")

    rel_path: str
    change: str
    kind_before: str | None = None
    kind_after: str | None = None
    size_before: int | None = None
    size_after: int | None = None
    sha256_before: str | None = None
    sha256_after: str | None = None
    detail: str = ""


class ProviderAttempt(BaseModel):
    """One persisted implement/fix execution attempt (audit evidence).

    ``TaskRun.attempt_in_flight`` is the crash marker: it is written BEFORE
    the provider starts and only cleared once this process has finalised the
    attempt (post snapshot + policy guard).
    """

    model_config = ConfigDict(extra="forbid")

    attempt_id: str
    iteration: int
    phase: str = "IMPLEMENT"          # IMPLEMENT | FIX
    status: AttemptStatus = AttemptStatus.IN_FLIGHT
    started_at: str = Field(default_factory=utcnow_iso)
    completed_at: str | None = None
    provider_started: bool = False
    provider_finished: bool = False
    provider_exit_code: int | None = None
    provider_timed_out: bool = False
    provider_error: str | None = None
    provider_exception: str | None = None
    pre_snapshot: RepoSnapshot | None = None
    post_snapshot: RepoSnapshot | None = None
    policy_checked: bool = False
    policy_check_error: str | None = None
    violations: list[PolicyViolation] = Field(default_factory=list)
    # Durable call identities that belong to this attempt (v0.2-A remediation),
    # so attempt -> call -> phase -> budget is traceable without guessing.
    call_ids: list[str] = Field(default_factory=list)

    # v0.2-C: durable milestones, replay identity and runtime evidence.
    milestone: AttemptMilestone = AttemptMilestone.IN_FLIGHT
    workspace_identity: WorkspaceIdentity | None = None
    completion_ready: bool = False
    completion_applied: bool = False
    applied_at: str | None = None
    applied_state: str | None = None
    runtime: AttemptRuntimeEvidence | None = None
    control_plane_violation: bool = False


class BaselineUntrackedEntry(BaseModel):
    """One pre-existing untracked (non-ignored) file captured at task start."""

    model_config = ConfigDict(extra="forbid")

    rel_path: str
    storage_name: str
    size: int
    mode: str = "100644"          # git index mode (100644/100755/120000)
    is_symlink: bool = False
    sha256: str = ""


class WorkspaceBaseline(BaseModel):
    """Persisted task-start workspace baseline (baseline/baseline.json)."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    captured_at: str = Field(default_factory=utcnow_iso)
    baseline_schema_version: int = 1
    head_sha: str | None = None
    branch: str | None = None
    status_porcelain_v2: str = ""
    preexisting_dirty_files: list[str] = Field(default_factory=list)
    preexisting_untracked_files: list[str] = Field(default_factory=list)
    index_tree_sha: str | None = None       # real .git/index tree at capture
    baseline_worktree_tree_sha: str | None = None  # temporary-index tree
    baseline_manifest_version: int = 1
    baseline_storage_path: str = ""
    baseline_complete: bool = False
    untracked_entries: list[BaselineUntrackedEntry] = Field(default_factory=list)
    notes: str = ""

    @property
    def has_baseline_tree(self) -> bool:
        return bool(self.baseline_worktree_tree_sha)


class NameStatusEntry(BaseModel):
    """One parsed name-status record (rename-aware)."""

    model_config = ConfigDict(extra="forbid")

    status: str            # e.g. A/M/D/R/T/U + optional similarity e.g. "R100"
    old_path: str | None = None
    new_path: str = ""

    @property
    def display(self) -> str:
        if self.old_path and self.old_path != self.new_path:
            return f"{self.status} {self.old_path} -> {self.new_path}"
        return f"{self.status} {self.new_path}"


class TaskDelta(BaseModel):
    """True task-relative delta: task-start baseline -> current workspace."""

    model_config = ConfigDict(extra="forbid")

    text_diff: str = ""
    stat_text: str = ""
    changed_files: list[str] = Field(default_factory=list)
    name_status: list[NameStatusEntry] = Field(default_factory=list)
    binary_files: list[str] = Field(default_factory=list)
    from_tree: str | None = None
    to_tree: str | None = None
    method: str = "trees"       # trees | reconstructed | stored
    generated_at: str = Field(default_factory=utcnow_iso)

    @property
    def has_changes(self) -> bool:
        return bool(self.changed_files)


# State schema versions (v0.2-C).
STATE_SCHEMA_VERSION = 6
MAX_SUPPORTED_STATE_SCHEMA = 6

# Structured implementer result contract version (distinct from the state
# schema version above).
IMPLEMENTATION_RESULT_SCHEMA_VERSION = 1
SNAPSHOT_ERA_SCHEMA = 5


class ProfileRef(BaseModel):
    """One profile that contributed to a resolved policy document."""

    model_config = ConfigDict(extra="forbid")

    name: str
    sha256: str = ""


class PolicyProvenance(BaseModel):
    """Where a task's frozen policy came from (v0.2-B, state schema 5).

    Profile hashes are provenance, not trust anchors: normal execution never
    re-reads or re-hashes a profile file.
    """

    model_config = ConfigDict(extra="forbid")

    # Successful frozen-policy evidence generation (1 at task creation, +1 per
    # successful explicit refresh/recovery) - not a count of semantic changes.
    generation: int = 1
    resolved_at: str = Field(default_factory=utcnow_iso)
    selector_raw: list[str] = Field(default_factory=list)
    profiles: list[ProfileRef] = Field(default_factory=list)
    workspace_config_sha256: str = ""
    snapshot_sha256: str = ""
    resolver_version: str = "0.2-B/1"
    # sha256_verified | unverified_legacy_no_digest | unverified_legacy_tolerant
    integrity: str = ""
    dropped_legacy_keys: list[str] = Field(default_factory=list)


class TaskRun(BaseModel):
    """Persisted per-task runtime state (tasks/<id>/state.json)."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    title: str
    state_schema_version: int = STATE_SCHEMA_VERSION
    packet: TaskPacket | None = None
    state: PipelineState = PipelineState.NEW
    plan_ready: bool = False
    created_at: str = Field(default_factory=utcnow_iso)
    updated_at: str = Field(default_factory=utcnow_iso)

    # Task-start workspace baseline (v1.0-RC; None = legacy pre-baseline task).
    baseline: WorkspaceBaseline | None = None

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
    policy_violations: list[PolicyViolation] = Field(default_factory=list)
    # Persisted implement/fix attempt history + crash marker (see ProviderAttempt).
    attempts: list[ProviderAttempt] = Field(default_factory=list)
    attempt_in_flight: bool = False

    # v0.2-A: external provider accounting + review lifecycle.
    provider_calls: list[ProviderCallRecord] = Field(default_factory=list)
    review_attempts: list[ReviewAttempt] = Field(default_factory=list)
    review_call_in_flight: bool = False
    # Fingerprint -> number of review rounds in which this blocker was seen.
    finding_seen_counts: dict[str, int] = Field(default_factory=dict)
    # Which config governed this task's policy: "snapshot" | "live-fallback".
    # v0.2-B writes it only at task freeze and at an explicit refresh/recovery;
    # execution never rewrites it, and read-only commands only display it.
    policy_source: str = ""

    # v0.2-B (schema 5): frozen-policy identity, integrity and provenance.
    policy_snapshot_path: str = ""
    policy_config_sha256: str = ""
    policy_provenance: PolicyProvenance | None = None

    # Durable, task-scoped, monotonic identity sequences (v0.2-A remediation).
    # Allocated and persisted BEFORE the external invocation, never decremented,
    # never reused after a failure, never reset by unblock or policy refresh.
    next_provider_call_sequence: int = 1
    next_provider_attempt_sequence: int = 1
    next_review_attempt_sequence: int = 1
    # Audited history of explicit policy refreshes (before/after evidence).
    policy_refreshes: list[PolicyRefreshRecord] = Field(default_factory=list)
    # Semantic application markers: one entry per applied ReviewResult.
    applied_reviews: list[AppliedReviewRecord] = Field(default_factory=list)

    @property
    def next_attempt(self) -> int:
        """1-based logical pass number for the next implementation pass."""
        return max(1, self.implementation_passes + 1)

    # -- durable identity allocation (mutates only; the caller persists) -----
    def allocate_call_id(self) -> str:
        """Allocate the next external-call identity (``DR-0001-C0007``)."""
        sequence = max(1, int(self.next_provider_call_sequence))
        self.next_provider_call_sequence = sequence + 1
        return f"{self.task_id}-C{sequence:04d}"

    def allocate_attempt_id(self) -> str:
        """Allocate the next implementer-attempt identity (``DR-0001-A0002``)."""
        sequence = max(1, int(self.next_provider_attempt_sequence))
        self.next_provider_attempt_sequence = sequence + 1
        return f"{self.task_id}-A{sequence:04d}"

    def allocate_review_attempt_id(self) -> str:
        """Allocate the next review-attempt identity (``DR-0001-R0002``)."""
        sequence = max(1, int(self.next_review_attempt_sequence))
        self.next_review_attempt_sequence = sequence + 1
        return f"{self.task_id}-R{sequence:04d}"

    def call_by_id(self, call_id: str) -> "ProviderCallRecord | None":
        for record in self.provider_calls:
            if record.call_id == call_id:
                return record
        return None

    def applied_review_identity(self, identity: str) -> "AppliedReviewRecord | None":
        for record in self.applied_reviews:
            if record.identity == identity:
                return record
        return None

    @property
    def open_blocking_findings(self) -> list[Finding]:
        return list(self.current_findings)
