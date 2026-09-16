"""Strict, read-only view over the durable OpenCode call ledger (v0.3-B).

The accepted v0.3-A ledger API (`FilesystemOpenCodeLedger.read_records`) skips
entries it cannot parse, which is the right behaviour for the *bridge* (a broken
record must never break a live call) but the wrong behaviour for an observability
tool: an MCP caller asking "what calls happened?" must never be told "none" when
the ledger is in fact unreadable.

This module therefore adds a deliberately strict, bounded, read-only view:

* it only ever looks inside ``<workspace>/.devrelay/opencode`` - no paths from the
  client;
* a corrupt ``sequence.json`` or a corrupt/unreadable ``OC-*.json`` record raises
  :class:`OpenCodeLedgerError` instead of being hidden;
* at most ``limit`` (bounded) records are read, newest allocation first;
* the ledger format itself is untouched.

The v0.3-A runtime keeps using its own tolerant reader; nothing here is imported
by :mod:`devrelay.opencode`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from devrelay.errors import OpenCodeLedgerError
from devrelay.redact import sanitize

#: Fields surfaced to MCP callers: identity, state, timing and non-secret
#: metadata only.  The raw record never contains prompt text or credentials, and
#: this projection keeps it that way even if that ever changed.
_RECORD_FIELDS = (
    "call_id",
    "operation",
    "state",
    "method",
    "path",
    "session_id",
    "issued",
    "external_request_count",
    "http_status",
    "error_type",
    "error",
    "started_at",
    "completed_at",
    "duration_ms",
    "response_bytes",
    "response_truncated",
    "response_media_type",
    "submission_uncertain",
    "prompt_sha256",
    "prompt_chars",
    "agent",
    "model",
)


def ledger_root(devrelay_dir: Path) -> Path:
    return Path(devrelay_dir) / "opencode"


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise OpenCodeLedgerError(
            f"OpenCode ledger entry {path.name} is unreadable "
            f"({type(exc).__name__}); refusing to report the ledger as empty"
        ) from exc


def sequence_state(devrelay_dir: Path) -> dict[str, Any]:
    """Presence/validity of ``sequence.json`` (never its raw contents)."""
    path = ledger_root(devrelay_dir) / "sequence.json"
    if not path.is_file():
        return {"present": False, "next_call_sequence": None}
    payload = _read_json(path)
    value = payload.get("next_call_sequence") if isinstance(payload, dict) else None
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise OpenCodeLedgerError(
            "OpenCode call sequence is malformed (expected "
            "{'next_call_sequence': <int >= 1>}); refusing to report the ledger "
            "as healthy"
        )
    return {"present": True, "next_call_sequence": value}


def read_records_strict(devrelay_dir: Path, *, limit: int) -> list[dict[str, Any]]:
    """Newest ``limit`` call records, strictly parsed and sanitized.

    Raises :class:`OpenCodeLedgerError` for a corrupt sequence file or any
    unreadable record in the returned window - corruption is reported, never
    hidden behind an empty list.
    """
    root = ledger_root(devrelay_dir)
    calls_dir = root / "calls"
    if not calls_dir.is_dir():
        return []
    paths = sorted(calls_dir.glob("OC-*.json"))
    if not paths:
        return []
    selected = paths[-max(1, limit) :]
    out: list[dict[str, Any]] = []
    for path in selected:
        payload = _read_json(path)
        if not isinstance(payload, dict):
            raise OpenCodeLedgerError(
                f"OpenCode ledger entry {path.name} is not an object; refusing to "
                "report the ledger as healthy"
            )
        projected: dict[str, Any] = {}
        for field in _RECORD_FIELDS:
            if field not in payload:
                continue
            value = payload[field]
            if field in ("error", "path", "session_id", "agent", "model"):
                value = sanitize(value if isinstance(value, str) else str(value))[:500]
            projected[field] = value
        out.append(projected)
    return out


__all__ = ["ledger_root", "read_records_strict", "sequence_state"]
