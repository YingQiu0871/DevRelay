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
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

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
from devrelay.models import (
    CallErrorType,
    Finding,
    ProviderCallPhase,
    ProviderCallRecord,
    ProviderKind,
    ReviewResult,
    Severity,
    utcnow_iso,
)
from devrelay.providers.base import ReviewerProvider
from devrelay.providers.evidence import CallSink, NullCallSink, ReviewCallPolicy
from devrelay.redact import sanitize

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
        transport_retries: int = 0,
        max_response_chars: int = 200_000,
        client: httpx.Client | None = None,
        call_sink: CallSink | None = None,
    ) -> None:
        self.endpoint = endpoint
        # Format retries (HTTP 200 without schema-valid JSON).
        self.retries = max(0, retries)
        # Transport retries (network/HTTP failures) - separate on purpose.
        self.transport_retries = max(0, transport_retries)
        self.max_response_chars = max(1_000, int(max_response_chars))
        self._sink: CallSink = call_sink or NullCallSink()
        self._call_sequence = 0
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

    # -- identity evidence (never a token) ------------------------------
    @property
    def model(self) -> str:
        return self.endpoint.model

    @property
    def endpoint_host(self) -> str | None:
        return urlparse(self.endpoint.base_url).hostname

    @property
    def automatic(self) -> bool:
        return True

    def prepare_request(self, bundle: ReviewBundle, review_number: int | None = None) -> None:
        return None

    # ------------------------------------------------------------------
    def _new_record(self, phase: ProviderCallPhase) -> ProviderCallRecord:
        self._call_sequence += 1
        return ProviderCallRecord(
            call_id=f"{self.name}-call-{self._call_sequence:03d}",
            provider_kind=ProviderKind.REVIEWER,
            provider_name=self.name,
            phase=phase,
            attempt_number=self._call_sequence,
            external_call_count=1,  # a real external call is being attempted
            model=self.endpoint.model,
            endpoint_host=self.endpoint_host,
        )

    def _settle(
        self,
        record: ProviderCallRecord,
        started: float,
        *,
        success: bool,
        error_type: CallErrorType | None = None,
        error: str | None = None,
    ) -> ProviderCallRecord:
        record = record.model_copy(
            update={
                "completed_at": utcnow_iso(),
                "success": success,
                "duration_seconds": round(time.monotonic() - started, 3),
                "error_type": error_type,
                "error": sanitize(error)[:1000] if error else None,
            }
        )
        self._sink.finish(record)
        return record

    def review(
        self,
        bundle: ReviewBundle,
        *,
        call_policy: ReviewCallPolicy | None = None,
    ) -> ReviewResult:
        policy = call_policy or ReviewCallPolicy(
            format_retries=self.retries,
            transport_retries=self.transport_retries,
            max_response_chars=self.max_response_chars,
            timeout_seconds=self.endpoint.timeout_seconds,
        )
        sink: CallSink = policy.sink or self._sink
        self._sink = sink  # account through the policy-provided sink
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

        format_attempts = 0
        transport_retries_used = 0
        while True:
            if transport_retries_used and format_attempts == 0:
                phase = ProviderCallPhase.REVIEW_TRANSPORT_RETRY
            elif format_attempts == 0:
                phase = ProviderCallPhase.REVIEW
            else:
                phase = ProviderCallPhase.REVIEW_FORMAT_RETRY
            record = self._new_record(phase)
            # Budget gate BEFORE anything leaves the machine.
            self._sink.preflight(ProviderKind.REVIEWER, phase)
            self._sink.start(record)
            started = time.monotonic()

            try:
                response = self._client.post(
                    url, json=payload, timeout=policy.timeout_seconds
                )
            except httpx.TimeoutException as exc:
                detail = sanitize(f"{type(exc).__name__}: {exc}")[:500]
                self._settle(record, started, success=False, error_type=CallErrorType.TIMEOUT, error=detail)
                if transport_retries_used < policy.transport_retries:
                    transport_retries_used += 1
                    continue
                raise ProviderError(
                    "reviewer request timed out after "
                    f"{policy.timeout_seconds:g}s ({self.endpoint_host or '-'}): {detail}"
                ) from exc
            except httpx.HTTPError as exc:
                detail = sanitize(f"{type(exc).__name__}: {exc}")[:500]
                self._settle(record, started, success=False, error_type=CallErrorType.TRANSPORT, error=detail)
                if transport_retries_used < policy.transport_retries:
                    transport_retries_used += 1
                    continue
                raise ProviderError(
                    "reviewer HTTP request failed "
                    f"({self.endpoint.model} @ {self.endpoint_host or '-'}): {detail}"
                ) from exc

            body_text = response.text or ""
            if len(body_text) > policy.max_response_chars:
                message = (
                    "reviewer response exceeded the configured limit "
                    f"({len(body_text)} > {policy.max_response_chars} chars); "
                    "DevRelay refuses to truncate and guess - the task is BLOCKED."
                )
                self._settle(
                    record,
                    started,
                    success=False,
                    error_type=CallErrorType.RESPONSE_TOO_LARGE,
                    error=message,
                )
                raise ReviewFormatError(message)

            if response.status_code != 200:
                # Never persist response bodies verbatim; redact before use.
                detail = sanitize(body_text[:500])
                self._settle(
                    record,
                    started,
                    success=False,
                    error_type=CallErrorType.HTTP_STATUS,
                    error=f"HTTP {response.status_code}: {detail}",
                )
                raise ProviderError(
                    f"reviewer endpoint returned HTTP {response.status_code} "
                    f"({self.endpoint.model} @ {self.endpoint_host or '-'}). "
                    f"Body: {detail}"
                )

            try:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                review = _parse_review_json(content)
            except ReviewFormatError as exc:
                self._settle(
                    record,
                    started,
                    success=False,
                    error_type=CallErrorType.FORMAT,
                    error=str(exc),
                )
                format_attempts += 1
                if format_attempts > policy.format_retries:
                    raise ReviewFormatError(
                        "reviewer returned invalid/non-JSON output after "
                        f"{format_attempts} attempt(s). DevRelay does not guess: "
                        "the task is BLOCKED for manual review (import a review "
                        f"with 'devrelay review import'). Last error: "
                        f"{sanitize(str(exc))[:300]}"
                    ) from exc
                continue
            except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
                self._settle(
                    record,
                    started,
                    success=False,
                    error_type=CallErrorType.FORMAT,
                    error=f"{type(exc).__name__}: {exc}",
                )
                format_attempts += 1
                if format_attempts > policy.format_retries:
                    raise ReviewFormatError(
                        "reviewer response did not contain a usable chat "
                        f"completion after {format_attempts} attempt(s). Last "
                        f"error: {sanitize(f'{type(exc).__name__}: {exc}')[:300]}"
                    ) from exc
                continue

            self._settle(record, started, success=True)
            return review

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
