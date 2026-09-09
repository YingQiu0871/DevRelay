"""Secret redaction helpers.

DevRelay never stores secrets in artifacts or logs.  All text that reaches an
artifact or a log line should be passed through :func:`redact_text` first.

The redactor removes:

* values of well-known secret environment variables (plus any env var whose
  name contains TOKEN/KEY/SECRET/PASSWORD),
* `sk-...` style API keys,
* `Authorization: ...` / `Bearer ...` header values,
* `key = value` assignments whose key looks secret.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Iterable

REDACTED = "[REDACTED]"

_SECRET_NAME_HINTS = ("token", "key", "secret", "password", "credential")
_KNOWN_SECRET_ENV = (
    "DEVRELAY_REVIEWER_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "DEEPSEEK_API_KEY",
    "CODEX_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "GITHUB_TOKEN",
    "GITLAB_TOKEN",
    "HUGGINGFACE_TOKEN",
)

_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"(?i)\bbasic\s+[A-Za-z0-9+/=]{16,}"),
    re.compile(r"(?i)\bsk-[A-Za-z0-9_-]{8,}"),
    re.compile(
        r"(?i)([a-z0-9_.-]*(?:api[_-]?key|token|password|secret|credential)"
        r"[a-z0-9_.-]*)\s*[:=]\s*[\"']?([^\s\"',;}{]+)"
    ),
    re.compile(r"(?i)\b(?:authorization|x-[a-z0-9-]+)\s*:\s*\S+"),
)


def _is_secret_env_name(name: str) -> bool:
    lowered = name.lower()
    return lowered in _KNOWN_SECRET_ENV or any(h in lowered for h in _SECRET_NAME_HINTS)


def secret_env_values() -> set[str]:
    """Collect current secret env-var values (used for literal replacement)."""
    values: set[str] = set()
    for name, value in os.environ.items():
        if value and _is_secret_env_name(name) and len(value) >= 4:
            values.add(value)
    return values


def redact_text(text: str, extra_values: Iterable[str] = ()) -> str:
    """Return *text* with secret-looking values replaced by ``[REDACTED]``."""
    if not text:
        return text
    result = text
    for value in (*secret_env_values(), *extra_values):
        if value and len(value) >= 4:
            result = result.replace(value, REDACTED)
    for pattern in _PATTERNS:
        result = pattern.sub(REDACTED, result)
    return result


def sanitize(text: str | None) -> str:
    """Alias of :func:`redact_text` used before persisting provider output."""
    return redact_text(text or "")


class RedactingFilter(logging.Filter):
    """Logging filter that redacts secret-looking content from every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.msg = redact_text(record.getMessage())
            record.args = ()
        except Exception:  # pragma: no cover - never break logging
            pass
        return True
