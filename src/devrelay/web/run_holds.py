"""Durable advisory run holds (web control-plane only)."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


class RunHoldError(RuntimeError):
    """The advisory hold store cannot be read or written safely."""


class RunHoldStore:
    """A small atomic JSON store under ``.devrelay/web``.

    A hold is advisory: it never changes run state and never calls a provider.
    The current implementation is consulted by the web run controls only; the
    CLI does not yet consult this store.
    """

    def __init__(self, devrelay_dir: str | Path) -> None:
        self.path = Path(devrelay_dir) / "web" / "run_holds.json"
        self._lock = threading.RLock()

    def get(self, run_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._read()["holds"].get(run_id)

    def hold(self, run_id: str, *, reason: str) -> dict[str, Any]:
        with self._lock:
            data = self._read()
            entry = {
                "run_id": run_id,
                "reason": reason,
                "actor": "local-operator",
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            data["holds"][run_id] = entry
            self._write(data)
            return entry

    def release(self, run_id: str) -> bool:
        with self._lock:
            data = self._read()
            existed = run_id in data["holds"]
            data["holds"].pop(run_id, None)
            self._write(data)
            return existed

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": SCHEMA_VERSION, "holds": {}}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RunHoldError("advisory hold store is unreadable") from exc
        if (
            not isinstance(raw, dict)
            or raw.get("schema_version") != SCHEMA_VERSION
            or not isinstance(raw.get("holds"), dict)
        ):
            raise RunHoldError("advisory hold store has an invalid schema")
        for key, value in raw["holds"].items():
            if not isinstance(key, str) or not isinstance(value, dict):
                raise RunHoldError("advisory hold store has invalid entries")
        return raw

    def _write(self, data: dict[str, Any]) -> None:
        temp_path: Path | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            handle = tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=".run_holds.",
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
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise RunHoldError("advisory hold store cannot be written") from exc
