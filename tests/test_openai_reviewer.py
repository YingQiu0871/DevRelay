"""OpenAI-compatible reviewer tests with a mocked HTTP transport."""

import json

import httpx
import pytest

from devrelay.errors import ProviderError, ProviderUnavailableError, ReviewFormatError
from devrelay.models import ReviewDecision
from devrelay.providers.openai_compatible import (
    ENV_API_KEY,
    OpenAICompatibleReviewer,
    ReviewerEndpoint,
    _parse_review_json,
    endpoint_from_env,
)

from helpers import FakeWorkspace, make_packet


def _bundle():
    return None  # reviewers only use the bundle text via render; mock tests
    # build a real one lazily below


def _real_bundle():
    from devrelay.artifacts.renderer import ReviewBundle

    return ReviewBundle(
        task_id="DR-0001",
        packet=make_packet(),
        workspace_root="/fake/ws",
        diff="diff --git a/x b/x\n+change\n",
        changed_files=["x.py"],
    )


_VALID_JSON = json.dumps(
    {
        "decision": "REQUEST_CHANGES",
        "summary": "one real bug",
        "findings": [
            {
                "severity": "P1",
                "title": "race on refresh",
                "description": "two writers",
                "files": ["src/sync.py"],
            }
        ],
    }
)


def _transport(contents, *, status_codes=None, headers_seen=None):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if headers_seen is not None:
            headers_seen["authorization"] = request.headers.get("authorization")
        calls["n"] += 1
        idx = calls["n"] - 1
        status = (status_codes or [200] * len(contents))[min(idx, len(contents) - 1)]
        body = contents[min(idx, len(contents) - 1)]
        if isinstance(body, str):
            return httpx.Response(status, json={"choices": [{"message": {"content": body}}]})
        return httpx.Response(status, json=body)

    return httpx.MockTransport(handler)


def test_parse_review_json_strips_fences_and_assigns_ids():
    review = _parse_review_json(f"```json\n{_VALID_JSON}\n```")
    assert review.decision == ReviewDecision.REQUEST_CHANGES
    assert review.findings[0].id == "P1-01"
    assert review.findings[0].severity.value == "P1"


def test_reviewer_returns_valid_review_and_auth_header():
    seen: dict = {}
    client = httpx.Client(
        transport=_transport([f"```json\n{_VALID_JSON}\n```"], headers_seen=seen),
        base_url="https://review.example/v1",
    )
    reviewer = OpenAICompatibleReviewer(
        ReviewerEndpoint(base_url="https://review.example/v1", api_key="sk-test-abcdefgh123456", model="m"),
        client=client,
    )
    result = reviewer.review(_real_bundle())
    assert result.decision == ReviewDecision.REQUEST_CHANGES
    assert result.findings[0].title == "race on refresh"
    assert seen.get("authorization") == "Bearer sk-test-abcdefgh123456"
    assert reviewer.automatic is True


def test_invalid_json_retried_once_then_blocked(tmp_path):
    client = httpx.Client(
        transport=_transport(["not json at all", "{also broken"]),
        base_url="https://review.example/v1",
    )
    reviewer = OpenAICompatibleReviewer(
        ReviewerEndpoint(base_url="https://review.example/v1", api_key="k", model="m"),
        retries=1,
        client=client,
    )
    with pytest.raises(ReviewFormatError):
        reviewer.review(_real_bundle())


def test_invalid_then_valid_json_succeeds():
    client = httpx.Client(
        transport=_transport(["garbage", f"```json\n{_VALID_JSON}\n```"]),
        base_url="https://review.example/v1",
    )
    reviewer = OpenAICompatibleReviewer(
        ReviewerEndpoint(base_url="https://review.example/v1", api_key="k", model="m"),
        retries=1,
        client=client,
    )
    result = reviewer.review(_real_bundle())
    assert result.decision == ReviewDecision.REQUEST_CHANGES


def test_http_error_is_provider_error():
    client = httpx.Client(
        transport=_transport([{"error": "boom"}], status_codes=[500]),
        base_url="https://review.example/v1",
    )
    reviewer = OpenAICompatibleReviewer(
        ReviewerEndpoint(base_url="https://review.example/v1", api_key="k", model="m"),
        client=client,
    )
    with pytest.raises(ProviderError, match="500"):
        reviewer.review(_real_bundle())


def test_endpoint_from_env_requires_key(monkeypatch):
    monkeypatch.delenv(ENV_API_KEY, raising=False)
    with pytest.raises(ProviderUnavailableError):
        endpoint_from_env()


def test_endpoint_from_env_reads_env(monkeypatch):
    monkeypatch.setenv(ENV_API_KEY, "sk-secret-abcdefgh1234567890")
    monkeypatch.setenv("DEVRELAY_REVIEWER_BASE_URL", "https://deep.example/v1")
    monkeypatch.setenv("DEVRELAY_REVIEWER_MODEL", "deepseek-chat")
    endpoint = endpoint_from_env()
    assert endpoint.base_url == "https://deep.example/v1"
    assert endpoint.model == "deepseek-chat"
    assert endpoint.api_key == "sk-secret-abcdefgh1234567890"
