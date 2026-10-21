"""Provider call evidence collection (v0.2-A).

Reviewers and implementers report every *external* invocation through a
:class:`CallSink`.  The engine supplies a sink that persists each call into the
task state and writes per-call evidence artifacts; tests use
:class:`NullCallSink`.
"""

from __future__ import annotations

from typing import Protocol

from devrelay.models import ProviderCallPhase, ProviderCallRecord, ProviderKind


class CallSink(Protocol):
    """Persistence boundary for provider call records.

    Implementations own *identity*: :meth:`start` allocates the durable,
    task-scoped call id (persisted before the request) and returns the record
    the provider must use for every later update.  Providers never invent call
    ids themselves, so identities cannot collide across restarts or retries.
    """

    def preflight(self, kind: ProviderKind, phase: ProviderCallPhase) -> None:
        """Raise if the next call would exceed the task budget (no side effects)."""

    def start(self, record: ProviderCallRecord) -> ProviderCallRecord:
        """Persist call intent before the request and return the stored record."""

    def finish(self, record: ProviderCallRecord) -> None:
        """Persist the final outcome of a call."""


class NullCallSink:
    """No-op sink used when accounting is not wired (unit tests, tooling)."""

    def __init__(self) -> None:
        self.records: list[ProviderCallRecord] = []
        self._sequence = 0

    def preflight(self, kind: ProviderKind, phase: ProviderCallPhase) -> None:
        return None

    def start(self, record: ProviderCallRecord) -> ProviderCallRecord:
        # No task state to allocate from: hand out a locally unique label so
        # tooling still sees a stable, non-empty identity.
        self._sequence += 1
        record = record.model_copy(
            update={"call_id": record.call_id or f"local-C{self._sequence:04d}"}
        )
        self.records.append(record)
        return record

    def finish(self, record: ProviderCallRecord) -> None:
        for index, existing in enumerate(self.records):
            if existing.call_id == record.call_id:
                self.records[index] = record
                break


class ReviewCallPolicy:
    """Effective call-shaping policy for one review round (from the task snapshot).

    Carries the task-scoped retry/size limits *and* the sink the provider must
    use to persist call evidence, so the engine can wire accounting without
    mutating the provider instance.
    """

    def __init__(
        self,
        *,
        format_retries: int = 1,
        transport_retries: int = 0,
        max_response_chars: int = 200_000,
        timeout_seconds: float = 120.0,
        sink: "CallSink | None" = None,
    ) -> None:
        self.format_retries = max(0, int(format_retries))
        self.transport_retries = max(0, int(transport_retries))
        self.max_response_chars = max(1_000, int(max_response_chars))
        self.timeout_seconds = float(timeout_seconds)
        self.sink = sink
