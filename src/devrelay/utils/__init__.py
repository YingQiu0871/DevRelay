"""Small shared helpers."""

from __future__ import annotations


def truncate(text: str, limit: int, *, suffix: str = "\n...[truncated by DevRelay]") -> str:
    """Truncate *text* to *limit* characters, appending an explicit suffix."""
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    head = text[: max(0, limit - len(suffix))]
    return head + suffix
