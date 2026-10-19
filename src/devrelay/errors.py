"""DevRelay exception hierarchy.

Every user-facing failure should surface as a :class:`DevRelayError` subclass
so the CLI can print a clean diagnostic instead of a traceback.
"""

from __future__ import annotations


class DevRelayError(Exception):
    """Base class for all DevRelay errors."""


class ConfigError(DevRelayError):
    """Configuration could not be parsed or validated."""


class TaskNotFoundError(DevRelayError):
    """No such task exists in the workspace store."""


class InvalidTransitionError(DevRelayError):
    """The requested state transition is not allowed."""

    def __init__(self, from_state: str, to_state: str) -> None:
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Invalid state transition: {from_state} -> {to_state} "
            f"(not allowed by the pipeline state machine)."
        )


class WorkspaceError(DevRelayError):
    """Workspace or git interaction failed."""


class ProviderError(DevRelayError):
    """A provider (implementer/reviewer) failed in a recoverable way."""


class ProviderUnavailableError(ProviderError):
    """The provider cannot run at all (e.g. Codex CLI is not installed)."""


class ReviewFormatError(ProviderError):
    """Reviewer output could not be parsed/validated."""


class StateConflictError(DevRelayError):
    """An operation is not allowed in the current task state."""


class BaselineError(DevRelayError):
    """Task workspace baseline could not be captured, stored or used."""


class BaselineUnavailableError(BaselineError):
    """The task has no usable baseline (legacy task or missing capture)."""


class BaselineCorruptError(BaselineError):
    """Persisted baseline artifacts are missing/inconsistent - no guessing."""


class BaselineSizeError(BaselineError):
    """A pre-existing file exceeds the configured baseline snapshot limit."""

    def __init__(self, path: str, size: int, limit: int) -> None:
        self.path = path
        self.size = size
        self.limit = limit
        super().__init__(
            f"cannot snapshot pre-existing file {path!r}: size {size} bytes "
            f"exceeds baseline.max_untracked_file_bytes ({limit}). "
            "No task was created; adjust the limit in .devrelay/config.yaml "
            "if you really want to snapshot this file."
        )


# ---------------------------------------------------------------------------
# v0.2-B: frozen task policy, project profiles, state schema
# ---------------------------------------------------------------------------

class PolicySnapshotError(DevRelayError):
    """A task's frozen policy snapshot exists but cannot be used (fail closed).

    DevRelay never substitutes live wiring or workspace defaults for a snapshot
    that once governed a task; recovery is explicit:
    ``devrelay unblock --refresh-policy --reason "..."``.
    """

    code = "policy_snapshot_error"

    def __init__(
        self,
        detail: str,
        *,
        path: object | None = None,
        expected_sha256: str = "",
        actual_sha256: str = "",
    ) -> None:
        self.detail = detail
        self.path = path
        self.expected_sha256 = expected_sha256
        self.actual_sha256 = actual_sha256
        super().__init__(self._describe())

    def _describe(self) -> str:
        parts = [f"{self.code}: {self.detail}"]
        if self.path is not None:
            parts.append(f"snapshot: {self.path}")
        if self.expected_sha256:
            parts.append(f"recorded sha256: {self.expected_sha256}")
        if self.actual_sha256:
            parts.append(f"actual sha256: {self.actual_sha256}")
        parts.append(
            'recovery: devrelay unblock --refresh-policy --reason "<why>"'
        )
        return "; ".join(parts)


class PolicySnapshotMissingError(PolicySnapshotError):
    """The frozen snapshot a task's provenance expects is not there."""

    code = "policy_snapshot_missing"


class PolicySnapshotInvalidError(PolicySnapshotError):
    """The snapshot bytes are there but unusable (YAML/schema/size/path)."""

    code = "policy_snapshot_invalid"


class PolicySnapshotIntegrityError(PolicySnapshotError):
    """The snapshot bytes no longer match the recorded digest."""

    code = "policy_snapshot_integrity_error"


class PolicySnapshotStateError(PolicySnapshotError):
    """Persisted provenance is internally inconsistent (fail closed)."""

    code = "policy_snapshot_state_inconsistent"


class CodedError(DevRelayError):
    """A DevRelay error whose message always starts with its stable code.

    Scripts and tests key off the code; humans still get the full sentence.
    """

    code = "error"

    def __init__(self, message: str = "") -> None:
        text = message or (self.__doc__ or "").strip() or self.code
        if self.code and not text.startswith(f"{self.code}:"):
            text = f"{self.code}: {text}"
        super().__init__(text)


class PolicyLiveResolutionRequiredError(CodedError):
    """A legacy task needs an explicit live-policy resolution and got none."""

    code = "policy_live_resolution_required"


class PolicyLiveResolutionFailedError(CodedError):
    """Explicit live-policy resolution failed (profiles/config invalid)."""

    code = "policy_live_resolution_failed"


class PolicyRefreshNotAllowedError(CodedError):
    """Refusing to refresh a healthy snapshot without an explicit force."""

    code = "policy_refresh_not_allowed"


class StateSchemaTooNewError(CodedError):
    """Task state was written by a newer DevRelay (schema > supported)."""

    code = "state_schema_too_new"


class ProfileError(CodedError):
    """A project profile or the profile selector is invalid."""

    code = "profile_error"


class ProfileNameInvalidError(ProfileError):
    code = "profile_name_invalid"


class ProfileNotFoundError(ProfileError):
    code = "profile_not_found"


class ProfilePathEscapeError(ProfileError):
    code = "profile_path_escape"


class ProfileTooLargeError(ProfileError):
    code = "profile_too_large"


class ProfileDuplicateError(ProfileError):
    code = "profile_duplicate"


class ProfileCountExceededError(ProfileError):
    code = "profile_count_exceeded"


class ProfileKeyForbiddenError(ProfileError):
    code = "profile_key_forbidden"


class ProfileSelectorError(ProfileError):
    code = "profile_selector_unresolved"


# ---------------------------------------------------------------------------
# v0.3-A OpenCode session bridge
# ---------------------------------------------------------------------------
class OpenCodeError(CodedError):
    """OpenCode bridge failure (v0.3-A)."""

    code = "opencode_error"


class OpenCodeConfigError(OpenCodeError):
    """The OpenCode bridge is not configured consistently."""

    code = "opencode_config_invalid"


class OpenCodeUnavailableError(OpenCodeError):
    """The configured OpenCode server could not be reached or answered."""

    code = "opencode_unavailable"


class OpenCodeProtocolError(OpenCodeError):
    """The OpenCode server answered with an unexpected/malformed shape."""

    code = "opencode_protocol_error"


class OpenCodeSessionNotFoundError(OpenCodeError):
    """The explicitly selected session does not exist on this server."""

    code = "opencode_session_not_found"


class OpenCodeSessionWorkspaceMismatchError(OpenCodeError):
    """The selected session does not belong to the configured workspace."""

    code = "opencode_session_workspace_mismatch"


class OpenCodeUnsupportedError(OpenCodeError):
    """The configured server does not support a requested capability."""

    code = "opencode_unsupported"


class OpenCodeLedgerError(OpenCodeError):
    """OpenCode call-identity accounting could not proceed safely.

    Raised when the durable call sequence is unreadable/torn or when a call
    identity would have to be reused: v0.3-A fails closed instead of restarting
    numbering or overwriting an existing record.
    """

    code = "opencode_ledger_error"


# ---------------------------------------------------------------------------
# v0.3-C: semantic role routing (semantic role -> exact configured route)
#
# These are *local* routing failures: they are raised before any request that
# could submit a model turn, and they are never mislabeled as provider failures.
# ---------------------------------------------------------------------------


class RoleRoutingError(CodedError):
    """Base class for v0.3-C role-routing failures (never a provider state)."""

    code = "role_routing_error"


class RoleUnknownError(RoleRoutingError):
    """The requested role is not one of the supported semantic roles.

    Also raised when the role is omitted or blank: v0.3-C never infers a role
    from prompt text, session title, ordering or model availability.
    """

    code = "role_unknown"


class RoleUnconfiguredError(RoleRoutingError):
    """The role is supported, but this workspace configures no route for it."""

    code = "role_unconfigured"


class RoleInvalidRouteError(RoleRoutingError):
    """The configured route for this role is malformed (model/agent grammar)."""

    code = "role_invalid_route"


# ---------------------------------------------------------------------------
# v0.3-D: bounded orchestration (durable run state over the accepted role path)
#
# These are *local* orchestration failures: they are raised before any request
# that could submit a model turn and are never mislabeled as provider/role
# failures (bridge and role errors keep their accepted taxonomy).
# ---------------------------------------------------------------------------


class OrchestrationError(CodedError):
    """Base class for v0.3-D bounded-orchestration failures."""

    code = "orchestration_error"


class OrchestrationRunNotFoundError(OrchestrationError):
    """No orchestration run with that id exists in this workspace."""

    code = "orchestration_run_not_found"


class OrchestrationInvalidTransitionError(OrchestrationError):
    """The requested orchestration action is not legal from the run's state."""

    code = "orchestration_invalid_transition"


class OrchestrationCycleLimitError(OrchestrationError):
    """The cycle/model-turn bound of this run (or the hard bound) was exceeded."""

    code = "orchestration_cycle_limit"


class OrchestrationSessionConflictError(OrchestrationError):
    """The run's sessions are missing, identical or otherwise unusable."""

    code = "orchestration_session_conflict"


class OrchestrationRouteChangedError(OrchestrationError):
    """A configured role route changed during the run; the run fails closed."""

    code = "orchestration_route_changed"


class OrchestrationStateCorruptError(OrchestrationError):
    """The persisted run document is unreadable or malformed (never reset)."""

    code = "orchestration_state_corrupt"


class OrchestrationPersistenceError(OrchestrationError):
    """The run document could not be durably written."""

    code = "orchestration_persistence_error"


# ---------------------------------------------------------------------------
# v0.3-E: fail-closed recovery of interrupted turns
#
# Recovery never reports a provider/role outcome: the only accepted resolution
# recorded by this build is ``mark_unrecoverable`` (fail closed), and adoption
# stays disabled until its platform proofs pass.
# ---------------------------------------------------------------------------


class OrchestrationRecoveryRequiredError(OrchestrationError):
    """A live role turn is interrupted; only recovery may touch this run."""

    code = "orchestration_recovery_required"


class OrchestrationRecoveryUnsupportedError(OrchestrationError):
    """A frozen v0.3-D (v1) run has no recovery protocol; it fails closed."""

    code = "orchestration_recovery_unsupported"


class OrchestrationRecoveryAlreadyResolvedError(OrchestrationError):
    """A recovery resolution is write-once; the recorded one is reported back."""

    code = "orchestration_recovery_already_resolved"

    def __init__(self, resolution: str, resolved_at: str) -> None:
        self.resolution = resolution
        self.resolved_at = resolved_at
        super().__init__(
            f"recovery already resolved as {resolution!r} at {resolved_at!r}; a "
            "resolution is write-once and no second resolution is applied"
        )


class OrchestrationAdoptionDisabledError(OrchestrationError):
    """adopt_completed_turn is disabled until its platform proofs pass."""

    code = "orchestration_adoption_disabled"
