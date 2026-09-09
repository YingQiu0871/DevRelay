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
