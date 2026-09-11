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
