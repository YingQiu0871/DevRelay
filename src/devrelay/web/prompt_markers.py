"""Durable, non-secret markers for manual prompts whose reply is unresolved."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


class PromptMarkerError(RuntimeError):
    """The marker file exists but cannot be read or written safely."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class PromptMarkerStore:
    """A small JSON store under ``.devrelay/web``.

    The store deliberately holds no prompt text: only the run id, role session,
    provider evidence code and timestamps.  Reads/writes are process-local
    serialized; multiple web writer processes are unsupported, matching the
    accepted single-writer bridge boundary.
    """

    def __init__(self, devrelay_dir: str | Path) -> None:
        self.path = Path(devrelay_dir) / "web" / "manual_prompts.json"
        self._lock = threading.RLock()

    def pending(self, run_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._read()["pending"].get(run_id)

    def mark(
        self,
        run_id: str,
        *,
        session_id: str,
        code: str,
        reply_pending: bool,
        submission_uncertain: bool,
    ) -> None:
        with self._lock:
            data = self._read()
            data["pending"][run_id] = {
                "session_id": session_id,
                "code": code,
                "reply_pending": bool(reply_pending),
                "submission_uncertain": bool(submission_uncertain),
                "created_at": _now(),
            }
            self._write(data)

    def clear(self, run_id: str) -> bool:
        with self._lock:
            data = self._read()
            existed = run_id in data["pending"]
            data["pending"].pop(run_id, None)
            self._write(data)
            return existed

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": SCHEMA_VERSION, "pending": {}}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PromptMarkerError("manual prompt marker is unreadable") from exc
        if (
            not isinstance(raw, dict)
            or raw.get("schema_version") != SCHEMA_VERSION
            or not isinstance(raw.get("pending"), dict)
        ):
            raise PromptMarkerError("manual prompt marker has an invalid schema")
        pending = raw["pending"]
        for key, value in pending.items():
            if not isinstance(key, str) or not isinstance(value, dict):
                raise PromptMarkerError("manual prompt marker has invalid entries")
        return raw

    def _write(self, data: dict[str, Any]) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            handle = tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=".manual_prompts.",
                suffix=".tmp",
                delete=False,
            )
            temp_path = Path(handle.name)
            try:
                json.dump(data, handle, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            finally:
                handle.close()
            os.replace(temp_path, self.path)
        except OSError as exc:
            try:
                temp_path.unlink(missing_ok=True)
            except (OSError, UnboundLocalError):
                pass
            raise PromptMarkerError("manual prompt marker cannot be written") from exc
