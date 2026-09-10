"""Review attempt lifecycle, call evidence and finding fingerprints (v0.2-A).

One automatic review round is a persisted :class:`ReviewAttempt`.  The
in-flight crash marker (``TaskRun.review_call_in_flight``) is written *before*
any reviewer HTTP request: if the process dies during that request, a restart
must fail closed instead of re-requesting a reviewer whose previous call may
already have been billed.

Artifacts written by this module::

    reviews/review-01-meta.json            # ReviewAttempt (transport metadata)
    reviews/review-01-call-01-meta.json    # one file per external call attempt
    reviews/review-01-result.json          # ReviewResult (written by the engine)
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
    renumbers the same blocker still produces the same fingerprint.
    """
    files = "|".join(sorted(path.strip().lower() for path in finding.files))
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


class ReviewSession:
    """Owns one review round: crash marker, call records and meta artifacts."""

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
            attempt_id=f"{task_id}-R{review_number:02d}",
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
        return self._reviews_dir() / f"review-{self.review_number:02d}-meta.json"

    def call_meta_path(self, index: int) -> Path:
        return (
            self._reviews_dir()
            / f"review-{self.review_number:02d}-call-{index:02d}-meta.json"
        )

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------
    def _unique_attempt_id(self, task: TaskRun) -> str:
        """Round identity that never collides with an already-recorded round.

        ``review_number`` counts *completed* rounds, so a round that was
        interrupted and later re-entered reuses the same number. The attempt id
        must stay unique anyway - otherwise finalizing the new round would
        overwrite the acknowledged evidence of the interrupted one.
        """
        base = f"{self.task_id}-R{self.review_number:02d}"
        existing = {attempt.attempt_id for attempt in task.review_attempts}
        if base not in existing:
            return base
        suffix = 2
        while f"{base}-{suffix}" in existing:
            suffix += 1
        return f"{base}-{suffix}"

    def begin(self) -> None:
        """Persist the in-flight attempt + crash marker before any request."""
        task = self._load_task()
        self.attempt.attempt_id = self._unique_attempt_id(task)
        task.review_call_in_flight = True
        self.attempt.status = ReviewAttemptStatus.IN_FLIGHT
        task.review_attempts.append(self.attempt)
        self._persist_task(task)
        self._write_meta(task)
        self._events.append(
            f"[{self.task_id}] review #{self.review_number}: calling provider "
            f"'{self.attempt.provider_name}'"
            + (f" (model {self.attempt.model})" if self.attempt.model else "")
        )

    def preflight(self, kind: ProviderKind, phase: ProviderCallPhase) -> None:
        """Budget gate - called by the provider immediately before each request."""
        self._budget.check(self._load_task(), kind)

    # ------------------------------------------------------------------
    # CallSink protocol
    # ------------------------------------------------------------------
    def start(self, record: ProviderCallRecord) -> None:
        self._call_index += 1
        record = record.model_copy(update={"attempt_number": self._call_index})
        self._call_records.append(record)
        task = self._load_task()
        task.provider_calls.append(record)
        task.review_call_in_flight = True
        self.attempt.format_attempts = sum(
            1 for r in self._call_records if r.phase is not ProviderCallPhase.REVIEW_TRANSPORT_RETRY
        )
        self.attempt.transport_attempts = len(self._call_records)
        self.attempt.call_ids.append(record.call_id)
        self.attempt.external_calls_consumed += max(0, record.external_call_count)
        self._persist_task(task)
        self._write_meta(task)
        self._write_call_meta(record)

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
        self._write_call_meta(record)
        self._write_meta(task)

    def finalize(
        self,
        status: ReviewAttemptStatus,
        *,
        result: ReviewResult | None = None,
        error_type: CallErrorType | None = None,
        error: str | None = None,
    ) -> TaskRun:
        task = self._load_task()
        self.attempt.status = status
        self.attempt.completed_at = utcnow_iso()
        self.attempt.result = result
        self.attempt.error_type = error_type
        self.attempt.error = sanitize(error) if error else None
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
            attempt_id=self._unique_attempt_id(task),
            provider_name="manual",
            status=ReviewAttemptStatus.COMPLETED,
            completed_at=utcnow_iso(),
            result=result,
            external_calls_consumed=0,
            format_attempts=0,
            transport_attempts=0,
        )
        task.review_call_in_flight = False
        for index, existing in enumerate(task.review_attempts):
            if existing.attempt_id == attempt.attempt_id:
                task.review_attempts[index] = attempt
                break
        else:
            task.review_attempts.append(attempt)
        self._persist_task(task)
        self.attempt = attempt
        self._write_meta(task)
        return task

    # ------------------------------------------------------------------
    # artifacts
    # ------------------------------------------------------------------
    def _write_meta(self, task: TaskRun) -> None:
        self._store.write_text(
            self.meta_path(),
            json.dumps(self.attempt.model_dump(mode="json"), indent=2, ensure_ascii=False),
        )

    def _write_call_meta(self, record: ProviderCallRecord) -> None:
        index = next(
            (
                i
                for i, existing in enumerate(self._call_records, start=1)
                if existing.call_id == record.call_id
            ),
            1,
        )
        self._store.write_text(
            self.call_meta_path(index),
            json.dumps(
                record.model_dump(mode="json"), indent=2, ensure_ascii=False
            ),
        )


def unfinished_attempt(task: TaskRun) -> ReviewAttempt | None:
    """The last review round that was started but never finalized.

    The in-flight marker covers the window *during* a request; this covers the
    wider window of a started round (crash after the HTTP response was received
    but before the result was persisted). Both must fail closed, because the
    request may already have been billed.
    """
    for attempt in reversed(task.review_attempts):
        if attempt.status is ReviewAttemptStatus.IN_FLIGHT:
            return attempt
    return None


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
    "AttemptStatus",
    "ReviewSession",
    "acknowledge_unfinished_attempts",
    "finding_fingerprint",
    "mark_findings",
    "stalled_findings",
    "unfinished_attempt",
]
