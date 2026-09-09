"""Secrets redaction tests."""

import logging

from devrelay.redact import REDACTED, RedactingFilter, redact_text


def test_env_value_replaced(monkeypatch):
    monkeypatch.setenv("DEVRELAY_REVIEWER_API_KEY", "sk-live-abcdef1234567890")
    out = redact_text("call with sk-live-abcdef1234567890 now")
    assert "sk-live-abcdef1234567890" not in out
    assert REDACTED in out


def test_any_secretish_env_name_replaced(monkeypatch):
    monkeypatch.setenv("FAKE_TOKEN", "my-secret-token-value")
    out = redact_text("header my-secret-token-value tail")
    assert "my-secret-token-value" not in out


def test_sk_pattern_redacted_without_env(monkeypatch):
    for name in ("OPENAI_API_KEY", "DEVRELAY_REVIEWER_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    out = redact_text("key sk-abcdefghijklmnopqrstuvwxyz end")
    assert REDACTED in out
    assert "sk-abcdefghijklmnopqrstuvwxyz" not in out


def test_bearer_and_assignment_redacted():
    out = redact_text(
        "Authorization: Bearer abcdefghijklmnop1234567890 | api_key = \"deadbeefcafe1234\""
    )
    assert "Bearer abcdefghijklmnop1234567890" not in out
    assert "deadbeefcafe1234" not in out


def test_logging_filter_redacts():
    logger = logging.getLogger("redact-test")
    logger.handlers.clear()
    logger.propagate = False
    handler = logging.StreamHandler()
    handler.addFilter(RedactingFilter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.info("token=%s", "shhh-super-secret-value-999")
    # nothing visible to assert easily; ensure filter does not crash and
    # redacts the message
    record = logging.LogRecord(
        "x", logging.INFO, "file", 1, "msg with sk-abcdefghijklmnop12345678", (), None
    )
    assert RedactingFilter().filter(record)
    assert REDACTED in record.getMessage()
