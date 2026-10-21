"""v0.2-A acceptance: reviewer call accounting, retry semantics, size caps.

Covers A5 (format retry = 2 calls), A6 (retry exhaustion), A7 (HTTP error, no
uncontrolled retry, sanitized body), A8 (timeout), A18 (oversized response)
plus the transport-retry opt-in and "no credentials in evidence".
"""

from __future__ import annotations

import json

import httpx
import pytest

from devrelay.errors import ProviderError, ReviewFormatError
from devrelay.models import CallErrorType, ProviderCallPhase, ProviderKind
from devrelay.providers.evidence import ReviewCallPolicy
from devrelay.providers.openai_compatible import (
    OpenAICompatibleReviewer,
    ReviewerEndpoint,
)
from devrelay.workspace.runner import CommandRunner

from helpers import make_packet

SECRET = "sk-live-REVIEWERCALL1234567890abcd"
VALID = json.dumps(
    {
        "decision": "REQUEST_CHANGES",
        "summary": "one real bug",
        "findings": [{"severity": "P2", "title": "wrong value", "description": "d"}],
    }
)


class MemorySink:
    """CallSink double that records exactly what the provider reports.

    Mirrors the real contract: ``start`` owns identity and returns the record
    the provider must keep using (see ``ReviewSession.start``).
    """

    def __init__(self) -> None:
        self.preflights: list[tuple[ProviderKind, ProviderCallPhase]] = []
        self.started: list = []
        self.finished: list = []
        self._sequence = 0

    def preflight(self, kind, phase) -> None:
        self.preflights.append((kind, phase))

    def start(self, record):
        self._sequence += 1
        record = record.model_copy(
            update={"call_id": record.call_id or f"mem-C{self._sequence:04d}"}
        )
        self.started.append(record)
        return record

    def finish(self, record) -> None:
        self.finished.append(record)


def _bundle():
    from devrelay.artifacts.renderer import ReviewBundle

    return ReviewBundle(
        task_id="DR-0001",
        packet=make_packet(),
        workspace_root="/fake/ws",
        diff="diff --git a/x b/x\n+change\n",
        changed_files=["x.py"],
    )


def _transport(contents, status_codes=None, *, handler=None):
    calls = {"n": 0}

    def default_handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        index = min(calls["n"] - 1, len(contents) - 1)
        body = contents[index]
        status = (status_codes or [200] * len(contents))[index]
        if isinstance(body, httpx.Response):
            return body
        return httpx.Response(status, json={"choices": [{"message": {"content": body}}]})

    return httpx.MockTransport(handler or default_handler)


def _reviewer(sink, transport, *, retries=1, transport_retries=0, max_response_chars=200_000):
    client = httpx.Client(transport=transport, base_url="https://review.example/v1")
    return OpenAICompatibleReviewer(
        ReviewerEndpoint(base_url="https://review.example/v1", api_key="k", model="m"),
        retries=retries,
        transport_retries=transport_retries,
        max_response_chars=max_response_chars,
        client=client,
        call_sink=sink,
    )


def _policy(sink, *, format_retries=1, transport_retries=0, max_response_chars=200_000):
    return ReviewCallPolicy(
        format_retries=format_retries,
        transport_retries=transport_retries,
        max_response_chars=max_response_chars,
        sink=sink,
    )


# ---------------------------------------------------------------------------
# A5: one format retry = two external reviewer calls
# ---------------------------------------------------------------------------
def test_format_retry_counts_two_calls():
    sink = MemorySink()
    reviewer = _reviewer(sink, _transport(["not json at all", VALID]))
    result = reviewer.review(_bundle(), call_policy=_policy(sink))

    assert result.decision.value == "REQUEST_CHANGES"
    assert len(sink.started) == 2
    assert [r.phase for r in sink.started] == [
        ProviderCallPhase.REVIEW,
        ProviderCallPhase.REVIEW_FORMAT_RETRY,
    ]
    assert [r.external_call_count for r in sink.started] == [1, 1]
    assert sum(r.external_call_count for r in sink.finished) == 2
    assert sink.finished[0].error_type is CallErrorType.FORMAT
    assert sink.finished[1].success is True
    # evidence carries identity, never credentials
    assert sink.started[0].model == "m"
    assert sink.started[0].endpoint_host == "review.example"
    assert "k" != sink.started[0].model


# ---------------------------------------------------------------------------
# A6: format retries exhausted -> error, exact call count
# ---------------------------------------------------------------------------
def test_format_retry_exhausted_blocks():
    sink = MemorySink()
    reviewer = _reviewer(sink, _transport(["garbage", "{also broken"]))
    with pytest.raises(ReviewFormatError):
        reviewer.review(_bundle(), call_policy=_policy(sink))
    assert len(sink.started) == 2
    assert all(r.success is False for r in sink.finished)
    assert all(r.error_type is CallErrorType.FORMAT for r in sink.finished)


# ---------------------------------------------------------------------------
# A7: HTTP error -> no uncontrolled retry, sanitized body
# ---------------------------------------------------------------------------
def test_http_error_blocks_and_sanitizes():
    body = json.dumps({"error": f"bad key {SECRET}"})
    sink = MemorySink()
    reviewer = _reviewer(sink, _transport([httpx.Response(500, text=body)]))
    with pytest.raises(ProviderError) as excinfo:
        reviewer.review(_bundle(), call_policy=_policy(sink))

    assert len(sink.started) == 1                     # no retry on HTTP errors
    assert sink.finished[0].error_type is CallErrorType.HTTP_STATUS
    assert SECRET not in str(excinfo.value)           # sanitized message
    assert SECRET not in json.dumps(sink.finished[0].model_dump(mode="json"))
    assert "500" in str(excinfo.value)


# ---------------------------------------------------------------------------
# A8: timeout -> error, one attempted call recorded
# ---------------------------------------------------------------------------
def test_transport_timeout_blocks():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    sink = MemorySink()
    reviewer = _reviewer(sink, httpx.MockTransport(handler))
    with pytest.raises(ProviderError) as excinfo:
        reviewer.review(_bundle(), call_policy=_policy(sink))

    assert len(sink.started) == 1
    assert sink.finished[0].error_type is CallErrorType.TIMEOUT
    assert sink.finished[0].external_call_count == 1   # conservative accounting
    assert "timed out" in str(excinfo.value).lower()


def test_transport_retry_opt_in_costs_two_calls():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("boom", request=request)
        return httpx.Response(200, json={"choices": [{"message": {"content": VALID}}]})

    sink = MemorySink()
    reviewer = _reviewer(sink, httpx.MockTransport(handler))
    result = reviewer.review(
        _bundle(), call_policy=_policy(sink, transport_retries=1)
    )
    assert result.decision.value == "REQUEST_CHANGES"
    assert len(sink.started) == 2
    assert sink.started[1].phase is ProviderCallPhase.REVIEW_TRANSPORT_RETRY
    assert sink.finished[0].error_type is CallErrorType.TRANSPORT


def test_transport_retry_default_is_zero():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    sink = MemorySink()
    reviewer = _reviewer(sink, httpx.MockTransport(handler))
    with pytest.raises(ProviderError):
        reviewer.review(_bundle(), call_policy=_policy(sink))
    assert len(sink.started) == 1


# ---------------------------------------------------------------------------
# A18: oversized response fails closed (never truncated + guessed)
# ---------------------------------------------------------------------------
def test_oversized_response_fails_closed():
    huge = "x" * 5_000
    sink = MemorySink()
    reviewer = _reviewer(sink, _transport([huge]), max_response_chars=1_000)
    with pytest.raises(ReviewFormatError) as excinfo:
        reviewer.review(_bundle(), call_policy=_policy(sink, max_response_chars=1_000))

    assert "exceeded the configured parsing/persistence limit" in str(excinfo.value)
    assert "refuses to parse, truncate and guess" in str(excinfo.value)
    assert len(sink.started) == 1                      # no retry on oversized body
    assert sink.finished[0].error_type is CallErrorType.RESPONSE_TOO_LARGE


def test_reviewer_calls_preflight_before_each_request():
    sink = MemorySink()
    reviewer = _reviewer(sink, _transport(["bad", VALID]))
    reviewer.review(_bundle(), call_policy=_policy(sink))
    assert [kind for kind, _phase in sink.preflights] == [
        ProviderKind.REVIEWER,
        ProviderKind.REVIEWER,
    ]
