"""OpenAI-compatible HTTP reviewer provider (DeepSeek and friends).

Configuration comes exclusively from environment variables — never from
artifacts, YAML or the command line:

* ``DEVRELAY_REVIEWER_BASE_URL`` (default ``https://api.deepseek.com/v1``)
* ``DEVRELAY_REVIEWER_API_KEY``   (required)
* ``DEVRELAY_REVIEWER_MODEL``     (default ``deepseek-chat``)

The provider talks the OpenAI ``chat/completions`` protocol.  The model is
asked to return ONE JSON object; output is schema-validated with Pydantic.
Invalid JSON is retried once (configurable) and never guessed; after the
retries are exhausted the task goes BLOCKED for human handling.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Optional

import httpx
from pydantic import ValidationError

from devrelay.artifacts.renderer import (
    REVIEWER_SYSTEM_PROMPT,
    ReviewBundle,
    render_review_user_prompt,
)
from devrelay.errors import (
    ProviderError,
    ProviderUnavailableError,
    ReviewFormatError,
)
from devrelay.models import Finding, ReviewResult, Severity
from devrelay.providers.base import ReviewerProvider

ENV_BASE_URL = "DEVRELAY_REVIEWER_BASE_URL"
ENV_API_KEY = "DEVRELAY_REVIEWER_API_KEY"
ENV_MODEL = "DEVRELAY_REVIEWER_MODEL"

DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


@dataclass
class ReviewerEndpoint:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float = 120.0
    response_format_json: bool = True


def endpoint_from_env(
    timeout_seconds: float = 120.0,
    response_format_json: bool = True,
) -> ReviewerEndpoint:
    api_key = os.environ.get(ENV_API_KEY, "")
    if not api_key:
        raise ProviderUnavailableError(
            f"{ENV_API_KEY} is not set. DevRelay never stores reviewer keys; "
            "export the environment variable before running "
            "'devrelay continue' (e.g. export DEVRELAY_REVIEWER_API_KEY=...)."
        )
    return ReviewerEndpoint(
        base_url=os.environ.get(ENV_BASE_URL, DEFAULT_BASE_URL).rstrip("/"),
        api_key=api_key,
        model=os.environ.get(ENV_MODEL, DEFAULT_MODEL),
        timeout_seconds=timeout_seconds,
        response_format_json=response_format_json,
    )


def _strip_fences(text: str) -> str:
    return _FENCE_RE.sub("", text.strip()).strip()


def _parse_review_json(text: str) -> ReviewResult:
    """Parse and validate reviewer JSON. Raises ReviewFormatError."""
    try:
        cleaned = _strip_fences(text)
        data = json.loads(cleaned)
        review = ReviewResult.model_validate(data)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise ReviewFormatError(f"invalid reviewer JSON: {exc}") from exc
    # Assign stable ids when the model did not provide them.
    findings: list[Finding] = []
    for index, finding in enumerate(review.findings, start=1):
        if not finding.id:
            finding = finding.model_copy(
                update={"id": f"{finding.severity.value}-{index:02d}"}
            )
        findings.append(finding)
    return review.model_copy(update={"findings": findings})


class OpenAICompatibleReviewer(ReviewerProvider):
    name = "openai_compatible"

    def __init__(
        self,
        endpoint: ReviewerEndpoint,
        *,
        retries: int = 1,
        client: httpx.Client | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.retries = max(0, retries)
        headers = (
            {"Authorization": f"Bearer {endpoint.api_key}"} if endpoint.api_key else {}
        )
        if client is None:
            self._client = httpx.Client(
                base_url=endpoint.base_url,
                headers=headers,
                timeout=endpoint.timeout_seconds,
            )
            self._owns_client = True
        else:
            # Injected client (tests): still enforce the auth header.
            if endpoint.api_key:
                client.headers["Authorization"] = f"Bearer {endpoint.api_key}"
            self._client = client
            self._owns_client = False

    @property
    def automatic(self) -> bool:
        return True

    def prepare_request(self, bundle: ReviewBundle, review_number: int | None = None) -> None:
        return None

    def review(self, bundle: ReviewBundle) -> ReviewResult:
        payload = {
            "model": self.endpoint.model,
            "temperature": 0.0,
            "stream": False,
            "messages": [
                {"role": "system", "content": REVIEWER_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": render_review_user_prompt(bundle)
                    + "\n\nOutput ONLY the JSON review object.",
                },
            ],
        }
        if self.endpoint.response_format_json:
            payload["response_format"] = {"type": "json_object"}
        url = "/chat/completions"

        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = self._client.post(url, json=payload)
            except httpx.HTTPError as exc:
                raise ProviderError(
                    f"reviewer HTTP request failed ({self.endpoint.model}): {exc}"
                ) from exc
            if response.status_code != 200:
                # Never persist response bodies verbatim; keep a redacted hint.
                detail = response.text[:500]
                raise ProviderError(
                    f"reviewer endpoint returned HTTP {response.status_code} "
                    f"({self.endpoint.model}). Body: {detail}"
                )
            try:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return _parse_review_json(content)
            except ReviewFormatError as exc:
                last_error = exc
            except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
                last_error = exc
            # fall through to retry
        raise ReviewFormatError(
            "reviewer returned invalid/non-JSON output after "
            f"{self.retries + 1} attempt(s). DevRelay does not guess: the task "
            "is BLOCKED for manual review (import a review with "
            "'devrelay review import'). Last error: {last_error}"
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
