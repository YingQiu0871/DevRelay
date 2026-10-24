"""Durable OpenCode session leases (foundation; no switch endpoint)."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


def _canonical_workspace(workspace: str) -> str:
    return os.path.normcase(os.path.realpath(workspace))


class SessionLeaseError(RuntimeError):
    """The lease store cannot be used safely."""


class SessionLeaseConflict(SessionLeaseError):
    """The session is already actively leased by a different run/role."""


class SessionLeaseStore:
    """One active lease per session and per run/role.

    This is a local ownership claim, not proof that the provider session is
    exclusive or alive.  There is deliberately no HTTP switch endpoint yet; the
    store is a prerequisite for one.
    """

    def __init__(self, devrelay_dir: str | Path) -> None:
        self.path = Path(devrelay_dir) / "web" / "session_leases.json"
        self._lock = threading.RLock()

    def get(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._read()["leases"].get(session_id)

    def all(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return dict(self._read()["leases"])

    def active_for(self, run_id: str, role: str) -> list[dict[str, Any]]:
        with self._lock:
            return [
                entry
                for entry in self._read()["leases"].values()
                if entry.get("run_id") == run_id
                and entry.get("role") == role
                and entry.get("state") == "active"
            ]

    def acquire(
        self,
        session_id: str,
        *,
        workspace: str,
        run_id: str,
        role: str,
    ) -> dict[str, Any]:
        workspace = _canonical_workspace(workspace)
        with self._lock:
            data = self._read()
            existing = data["leases"].get(session_id)
            if existing is not None and existing.get("state") == "uncertain":
                raise SessionLeaseConflict("session lease is uncertain; recovery required")
            if existing is not None and existing.get("state") == "active":
                if (
                    existing.get("workspace") == workspace
                    and existing.get("run_id") == run_id
                    and existing.get("role") == role
                ):
                    return existing
                raise SessionLeaseConflict("session is already leased")
            for other_id, entry in data["leases"].items():
                if (
                    other_id != session_id
                    and entry.get("state") == "active"
                    and entry.get("workspace") == workspace
                    and entry.get("run_id") == run_id
                    and entry.get("role") == role
                ):
                    raise SessionLeaseConflict("run/role already holds another lease")
            record = {
                "session_id": session_id,
                "workspace": workspace,
                "run_id": run_id,
                "role": role,
                "state": "active",
                "acquired_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "released_at": "",
                "evidence": "local",
            }
            data["leases"][session_id] = record
            self._write(data)
            return record

    def release(self, session_id: str) -> bool:
        with self._lock:
            data = self._read()
            entry = data["leases"].get(session_id)
            if entry is None or entry.get("state") != "active":
                return False
            entry["state"] = "released"
            entry["released_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            self._write(data)
            return True

    def mark_uncertain(self, session_id: str) -> bool:
        with self._lock:
            data = self._read()
            entry = data["leases"].get(session_id)
            if entry is None or entry.get("state") != "active":
                return False
            entry["state"] = "uncertain"
            self._write(data)
            return True

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": SCHEMA_VERSION, "leases": {}}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SessionLeaseError("session lease store is unreadable") from exc
        if (
            not isinstance(raw, dict)
            or raw.get("schema_version") != SCHEMA_VERSION
            or not isinstance(raw.get("leases"), dict)
        ):
            raise SessionLeaseError("session lease store has an invalid schema")
        for key, value in raw["leases"].items():
            if not isinstance(key, str) or not isinstance(value, dict):
                raise SessionLeaseError("session lease store has invalid entries")
            if value.get("state") not in ("active", "released", "uncertain"):
                raise SessionLeaseError("session lease store has invalid state")
        return raw

    def _write(self, data: dict[str, Any]) -> None:
        temp_path: Path | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            handle = tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=".session_leases.",
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
            raise SessionLeaseError("session lease store cannot be written") from exc
