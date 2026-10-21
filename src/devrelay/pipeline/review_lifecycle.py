"""Review attempt lifecycle, call evidence and finding fingerprints (v0.2-A).

One automatic review round is a persisted :class:`ReviewAttempt`.  Identities
come from durable, task-scoped, monotonic sequences (``DR-0001-R0002``,
``DR-0001-C0007``) that are allocated and persisted *before* anything leaves the
machine - never from a process-local counter, so restarts, unblocks and retries
can never reuse an identity or overwrite another call's evidence.

Result lifecycle (v0.2-A audit remediation)::

    CALL COMPLETED     status == COMPLETED          (a call finished)
    RESULT PERSISTED   result_persisted + result_hash
                       -> authoritative, sanitized, schema-valid result that a
                          restart replays locally with ZERO external calls
    RESULT APPLIED     result_applied + applied_at/applied_state
                       -> reached review_history exactly once (idempotent)

An *uncertain* external call (in-flight marker set, or a round that never
finalized) fails closed instead: DevRelay never pretends a result exists.

Artifacts written by this module (``<NN>`` = semantic review round)::

    reviews/review-NN-result.json              # ReviewResult (written by engine)
    reviews/review-NN-<attempt-id>-meta.json   # immutable per-attempt metadata
    reviews/review-NN-meta.json                # latest attempt of that round
    reviews/review-NN-call-MM-meta.json        # latest call view of that round
    policy/calls/<call-id>.json                # immutable per-call evidence
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Callable

from devrelay.artifacts.store import ArtifactStore
from devrelay.models import (
    AttemptStatus,
    CallErrorType,
    Finding,
    ProviderCallPhase,
    ProviderCallRecord,
    ProviderKind,
    ReviewAttempt,
    ReviewAttemptStatus,
    ReviewResult,
    TaskRun,
    utcnow_iso,
)
from devrelay.pipeline.budget import ProviderBudget
from devrelay.redact import sanitize


def finding_fingerprint(finding: Finding) -> str:
    """Deterministic identity of a finding across review rounds.

    Deliberately excludes the per-round finding id; a reviewer that renames or
    renumbers the same blocker still produces the same fingerprint.  File paths
    are separator-normalized (``src\\a.py`` == ``src/a.py``) and sorted, but
    never case-folded: a POSIX repository may legitimately contain both
    ``A.py`` and ``a.py``, so distinct paths must stay distinct.
    """
    files = "|".join(
        sorted(path.strip().replace("\\", "/") for path in finding.files)
    )
    title = re.sub(r"\s+", " ", (finding.title or "").strip().lower())
    description = re.sub(r"\s+", " ", (finding.description or "").strip().lower())
    payload = "\n".join(
        [
            finding.severity.value,
            title,
            files,
            description[:2000],
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def review_result_hash(review: ReviewResult) -> str:
    """Stable identity of one semantic review result.

    Fingerprints are stripped first: they are *derived* during application, so
    the identity must not change when a result is replayed.  Two structurally
    equal results therefore always hash equal, which is what makes a restart
    replay provably idempotent instead of a guess.
    """
    canonical = review.model_copy(
        update={
            "findings": [
                finding.model_copy(update={"fingerprint": ""})
                for finding in review.findings
            ]
        }
    )
    payload = json.dumps(
        canonical.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ReviewSession:
    """Owns one review attempt: crash marker, call records and meta artifacts."""

    def __init__(
        self,
        *,
        store: ArtifactStore,
        task_id: str,
        review_number: int,
        provider_name: str,
        model: str | None,
        endpoint_host: str | None,
        budget: ProviderBudget,
        load_task: Callable[[], TaskRun],
        persist: Callable[[TaskRun], None],
        events: list[str],
        attempt_id: str | None = None,
    ) -> None:
        self._store = store
        self.task_id = task_id
        self.review_number = review_number
        self._budget = budget
        self._load_task = load_task
        self._persist_task = persist
        self._events = events
        self._call_index = 0
        self.attempt = ReviewAttempt(
            review_number=review_number,
            attempt_id=attempt_id or "",
            provider_name=provider_name,
            model=model,
            endpoint_host=endpoint_host,
        )
        self._call_records: list[ProviderCallRecord] = []

    # ------------------------------------------------------------------
    # paths
    # ------------------------------------------------------------------
    def _reviews_dir(self) -> Path:
        return self._store.reviews_dir(self.task_id)

    def meta_path(self) -> Path:
        """Latest view of the current round (convenience, may be rewritten)."""
        return self._reviews_dir() / f"review-{self.review_number:02d}-meta.json"

    def attempt_meta_path(self, attempt_id: str | None = None) -> Path:
        """Immutable per-attempt metadata (unique attempt identity in the name)."""
        return self._reviews_dir() / (
            f"review-{self.review_number:02d}-"
            f"{attempt_id or self.attempt.attempt_id or 'unknown'}-meta.json"
        )

    def call_meta_path(self, index: int) -> Path:
        """Latest per-round call view (index within this attempt)."""
        return (
            self._reviews_dir()
            / f"review-{self.review_number:02d}-call-{index:02d}-meta.json"
        )

    def call_evidence_path(self, call_id: str) -> Path:
        """Immutable per-call evidence, keyed by the durable call identity."""
        return self._store.policy_dir(self.task_id) / "calls" / f"{call_id}.json"

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------
    def begin(self) -> None:
        """Persist identity + in-flight attempt and crash marker before any call."""
        task = self._load_task()
        if not self.attempt.attempt_id:
            self.attempt.attempt_id = task.allocate_review_attempt_id()
        task.review_call_in_flight = True
        self.attempt.status = ReviewAttemptStatus.IN_FLIGHT
        task.review_attempts.append(self.attempt)
        self._persist_task(task)
        self._write_meta(task)
        self._events.append(
            f"[{self.task_id}] review #{self.review_number} "
            f"({self.attempt.attempt_id}): calling provider "
            f"'{self.attempt.provider_name}'"
            + (f" (model {self.attempt.model})" if self.attempt.model else "")
        )

    def preflight(self, kind: ProviderKind, phase: ProviderCallPhase) -> None:
        """Budget gate - called by the provider immediately before each request."""
        self._budget.check(self._load_task(), kind)

    # ------------------------------------------------------------------
    # CallSink protocol
    # ------------------------------------------------------------------
    def start(self, record: ProviderCallRecord) -> ProviderCallRecord:
        """Allocate the durable call identity and persist the intent."""
        self._call_index += 1
        task = self._load_task()
        record = record.model_copy(
            update={
                "call_id": task.allocate_call_id(),
                "attempt_number": self._call_index,
                "task_iteration": task.fix_iterations_used + 1,
                "parent_attempt_id": self.attempt.attempt_id,
                "review_number": self.review_number,
            }
        )
        self._call_records.append(record)
        task.provider_calls.append(record)
        task.review_call_in_flight = True
        self.attempt.format_attempts = sum(
            1
            for r in self._call_records
            if r.phase is not ProviderCallPhase.REVIEW_TRANSPORT_RETRY
        )
        self.attempt.transport_attempts = len(self._call_records)
        self.attempt.call_ids.append(record.call_id)
        self.attempt.external_calls_consumed += max(0, record.external_call_count)
        self._persist_task(task)
        self._write_meta(task)
        self._write_call_meta(task, record)
        return record

    def finish(self, record: ProviderCallRecord) -> None:
        for index, existing in enumerate(self._call_records):
            if existing.call_id == record.call_id:
                self._call_records[index] = record
                break
        task = self._load_task()
        for index, existing in enumerate(task.provider_calls):
            if existing.call_id == record.call_id:
                task.provider_calls[index] = record
                break
        else:  # pragma: no cover - defensive: start() should have appended it
            task.provider_calls.append(record)
        task.review_call_in_flight = False
        self._persist_task(task)
        self._write_call_meta(task, record)
        self._write_meta(task)

    def finalize(
        self,
        status: ReviewAttemptStatus,
        *,
        result: ReviewResult | None = None,
        error_type: CallErrorType | None = None,
        error: str | None = None,
    ) -> TaskRun:
        """Close the attempt and persist a usable result as authoritative."""
        task = self._load_task()
        self.attempt.status = status
        self.attempt.completed_at = utcnow_iso()
        self.attempt.result = result
        self.attempt.error_type = error_type
        self.attempt.error = sanitize(error) if error else None
        if result is not None:
            # Sanitized/schema-valid result -> replayable authoritative state.
            self.attempt.result_persisted = True
            self.attempt.result_hash = review_result_hash(result)
        task.review_call_in_flight = False
        for index, existing in enumerate(task.review_attempts):
            if existing.attempt_id == self.attempt.attempt_id:
                task.review_attempts[index] = self.attempt
                break
        else:  # pragma: no cover - defensive
            task.review_attempts.append(self.attempt)
        self._persist_task(task)
        self._write_meta(task)
        return task

    def record_manual_review(self, result: ReviewResult) -> TaskRun:
        """Manual review event: auditable, but consumes zero external calls."""
        task = self._load_task()
        attempt = ReviewAttempt(
            review_number=self.review_number,
            attempt_id=task.allocate_review_attempt_id(),
            provider_name="manual",
            status=ReviewAttemptStatus.COMPLETED,
            completed_at=utcnow_iso(),
            result=result,
            result_persisted=True,
            result_hash=review_result_hash(result),
            external_calls_consumed=0,
            format_attempts=0,
            transport_attempts=0,
        )
        task.review_call_in_flight = False
        task.review_attempts.append(attempt)
        self._persist_task(task)
        self.attempt = attempt
        self._write_meta(task)
        return task

    def mark_applied(self, task: TaskRun, state: str) -> ReviewAttempt:
        """Record the RESULT APPLIED milestone on this attempt (in memory)."""
        self.attempt.result_applied = True
        self.attempt.applied_at = utcnow_iso()
        self.attempt.applied_state = state
        for index, existing in enumerate(task.review_attempts):
            if existing.attempt_id == self.attempt.attempt_id:
                task.review_attempts[index] = self.attempt
                break
        return self.attempt

    # ------------------------------------------------------------------
    # artifacts
    # ------------------------------------------------------------------
    def _write_meta(self, task: TaskRun) -> None:
        payload = json.dumps(
            self.attempt.model_dump(mode="json"), indent=2, ensure_ascii=False
        )
        # Immutable per-attempt evidence (unique attempt id in the file name)
        # plus a convenience "latest attempt of this round" view.
        if self.attempt.attempt_id:
            self._store.write_text(self.attempt_meta_path(), payload)
        self._store.write_text(self.meta_path(), payload)

    def _write_call_meta(self, task: TaskRun, record: ProviderCallRecord) -> None:
        index = next(
            (
                i
                for i, existing in enumerate(self._call_records, start=1)
                if existing.call_id == record.call_id
            ),
            1,
        )
        payload = json.dumps(
            record.model_dump(mode="json"), indent=2, ensure_ascii=False
        )
        # Immutable per-call evidence: the durable call identity is the file
        # name, so a later retry can never overwrite this call's record.
        self._store.write_text(self.call_evidence_path(record.call_id), payload)
        self._store.write_text(self.call_meta_path(index), payload)


# ----------------------------------------------------------------------
# crash-window helpers (fail closed vs. replay locally)
# ----------------------------------------------------------------------
def unfinished_attempt(task: TaskRun) -> ReviewAttempt | None:
    """The last review attempt that was started but never finalized.

    The in-flight marker covers the window *during* a request; this covers the
    wider window of a started attempt (crash after the HTTP response was
    received but before the attempt was finalized). Both must fail closed,
    because the request may already have been billed.
    """
    for attempt in reversed(task.review_attempts):
        if attempt.status is ReviewAttemptStatus.IN_FLIGHT:
            return attempt
    return None


def pending_result_attempt(task: TaskRun) -> ReviewAttempt | None:
    """The last attempt whose authoritative result was never applied.

    This is the *recoverable* window: a schema-valid, sanitized ReviewResult is
    already persisted, so a restart can replay it locally with zero external
    calls instead of paying for another reviewer invocation.  ``result_persisted``
    is the explicit marker for results written by this version; an attempt that
    merely carries a result (state written before the marker existed) still
    qualifies, because abandoning a completed paid-for call would be worse.
    """
    for attempt in reversed(task.review_attempts):
        if (
            attempt.status is ReviewAttemptStatus.COMPLETED
            and attempt.result is not None
            and not attempt.result_applied
        ):
            return attempt
    return None


# Application state of one incoming review result (see review_application_state).
APPLICATION_APPLIED = "applied"
APPLICATION_FINISH_ONLY = "finish_only"
APPLICATION_NOT_APPLIED = "not_applied"


def review_application_state(
    task: TaskRun, review: ReviewResult, attempt_id: str | None = None
) -> str:
    """Decide whether *review* still has to be applied semantically.

    The authoritative test is **attempt-scoped**: an attempt that already
    carries ``result_applied`` (or a marker recorded for that attempt id) was
    applied, so replaying it must not touch history, counters or transitions.

    Content equality alone is deliberately *not* an application proof: two
    distinct rounds may legitimately produce byte-identical reviews (that is
    exactly the repeated-blocker case the stagnation guard watches), so a new
    attempt with the same content must still be applied.

    ``finish_only`` covers state written by the unreleased ``fe4b044``
    candidate, which appended the review to history in one write and applied the
    terminal state in another: with no application markers anywhere, a
    history-tail identity match means "finish the interrupted application"
    rather than "apply it again".
    """
    identity = review_result_hash(review)
    if attempt_id:
        for attempt in task.review_attempts:
            if attempt.attempt_id == attempt_id and attempt.result_applied:
                return APPLICATION_APPLIED
        if any(
            marker.identity == identity and marker.attempt_id == attempt_id
            for marker in task.applied_reviews
        ):
            return APPLICATION_APPLIED
    elif any(marker.identity == identity for marker in task.applied_reviews):
        return APPLICATION_APPLIED
    if (
        not task.applied_reviews
        and task.review_history
        and review_result_hash(task.review_history[-1]) == identity
    ):
        return APPLICATION_FINISH_ONLY
    return APPLICATION_NOT_APPLIED


def acknowledge_unfinished_attempts(
    task: TaskRun, *, note: str
) -> list[ReviewAttempt]:
    """Close stale IN_FLIGHT attempts after an explicit human acknowledgement.

    Returns the attempts that were closed (empty when there were none). The
    attempt and its call records are kept - only the status is finalized, so the
    evidence survives while the task becomes runnable again.
    """
    closed: list[ReviewAttempt] = []
    for index, attempt in enumerate(task.review_attempts):
        if attempt.status is not ReviewAttemptStatus.IN_FLIGHT:
            continue
        attempt.status = ReviewAttemptStatus.INTERRUPTED
        attempt.completed_at = utcnow_iso()
        attempt.error_type = CallErrorType.EXCEPTION
        attempt.error = sanitize(
            "INTERRUPTED_REVIEWER_ATTEMPT: review round #{number} never "
            "finalized ({note})".format(number=attempt.review_number, note=note)
        )
        task.review_attempts[index] = attempt
        closed.append(attempt)
    return closed


def mark_findings(review: ReviewResult, task: TaskRun) -> ReviewResult:
    """Attach fingerprints to findings and bump the task's seen counters."""
    findings: list[Finding] = []
    for finding in review.findings:
        fingerprint = finding.fingerprint or finding_fingerprint(finding)
        findings.append(finding.model_copy(update={"fingerprint": fingerprint}))
        task.finding_seen_counts[fingerprint] = (
            task.finding_seen_counts.get(fingerprint, 0) + 1
        )
    return review.model_copy(update={"findings": findings})


def stalled_findings(
    review: ReviewResult, task: TaskRun, max_same_finding_cycles: int
) -> list[Finding]:
    """Blocking findings whose fingerprint has now been seen too many times."""
    if max_same_finding_cycles <= 0:
        return []
    stalled: list[Finding] = []
    for finding in review.findings:
        if not finding.fingerprint:
            continue
        if task.finding_seen_counts.get(finding.fingerprint, 0) >= max_same_finding_cycles:
            stalled.append(finding)
    return stalled


# Re-exported for callers that only need the attempt-status enum.
__all__ = [
    "APPLICATION_APPLIED",
    "APPLICATION_FINISH_ONLY",
    "APPLICATION_NOT_APPLIED",
    "AttemptStatus",
    "ReviewSession",
    "acknowledge_unfinished_attempts",
    "finding_fingerprint",
    "mark_findings",
    "pending_result_attempt",
    "review_application_state",
    "review_result_hash",
    "stalled_findings",
    "unfinished_attempt",
]
