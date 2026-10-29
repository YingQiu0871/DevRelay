"""Durable OpenCode session leases (pending-switch primitive; no endpoint)."""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = 1
SWITCH_ID_RE = re.compile(r"^SW-[0-9a-f]{32}$")


def generate_switch_id() -> str:
    return f"SW-{uuid4().hex}"


def valid_switch_id(switch_id: object) -> bool:
    return isinstance(switch_id, str) and bool(SWITCH_ID_RE.fullmatch(switch_id))


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
            if existing is not None and existing.get("state") in (
                "active",
                "pending_switch",
                "uncertain",
            ):
                if (
                    existing.get("state") == "active"
                    and existing.get("workspace") == workspace
                    and existing.get("run_id") == run_id
                    and existing.get("role") == role
                ):
                    return existing
                raise SessionLeaseConflict("session is already leased or pending")
            for other_id, entry in data["leases"].items():
                if (
                    other_id != session_id
                    and entry.get("state") in ("active", "pending_switch")
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

    def acquire_pending_switch(
        self,
        session_id: str,
        *,
        workspace: str,
        run_id: str,
        role: str,
        source_session_id: str,
        switch_id: str | None = None,
    ) -> dict[str, Any]:
        """Hold a target lease beside the active source lease for one switch.

        The target is not active and cannot be used for model I/O until
        ``commit_switch``.  The source remains active; only an explicit commit
        releases it.
        """
        workspace = _canonical_workspace(workspace)
        switch_id = switch_id or generate_switch_id()
        if not valid_switch_id(switch_id):
            raise SessionLeaseConflict("switch id is invalid")
        if session_id == source_session_id:
            raise SessionLeaseConflict("target and source sessions must differ")
        with self._lock:
            data = self._read()
            source = data["leases"].get(source_session_id)
            if (
                source is None
                or source.get("state") != "active"
                or source.get("workspace") != workspace
                or source.get("run_id") != run_id
                or source.get("role") != role
            ):
                raise SessionLeaseConflict("source session has no matching active lease")
            existing = data["leases"].get(session_id)
            if existing is not None and existing.get("state") in (
                "active",
                "pending_switch",
                "uncertain",
            ):
                raise SessionLeaseConflict("target session is already leased or pending")
            for entry in data["leases"].values():
                if (
                    entry.get("state") == "pending_switch"
                    and entry.get("run_id") == run_id
                    and entry.get("role") == role
                ):
                    raise SessionLeaseConflict("run/role already has a pending switch")
            record = {
                "session_id": session_id,
                "workspace": workspace,
                "run_id": run_id,
                "role": role,
                "state": "pending_switch",
                "switch_id": switch_id,
                "source_session_id": source_session_id,
                "acquired_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "released_at": "",
                "evidence": "local",
            }
            data["leases"][session_id] = record
            self._write(data)
            return record

    def pending_for_run(self, run_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return [
                entry
                for entry in self._read()["leases"].values()
                if entry.get("run_id") == run_id
                and entry.get("state") == "pending_switch"
            ]

    def blocking_for_run(self, run_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return [
                entry
                for entry in self._read()["leases"].values()
                if entry.get("run_id") == run_id
                and entry.get("state") in ("pending_switch", "uncertain")
            ]

    def pending_switch(self, switch_id: str) -> dict[str, Any] | None:
        if not valid_switch_id(switch_id):
            return None
        with self._lock:
            for entry in self._read()["leases"].values():
                if (
                    entry.get("state") == "pending_switch"
                    and entry.get("switch_id") == switch_id
                ):
                    return entry
        return None

    def _pending_entry(self, data: dict[str, Any], switch_id: str) -> dict[str, Any]:
        for entry in data["leases"].values():
            if (
                entry.get("state") == "pending_switch"
                and entry.get("switch_id") == switch_id
            ):
                return entry
        raise SessionLeaseConflict("no pending switch with this id")

    def abort_switch(self, switch_id: str) -> dict[str, Any]:
        with self._lock:
            data = self._read()
            target = self._pending_entry(data, switch_id)
            target["state"] = "released"
            target["released_at"] = datetime.now(timezone.utc).isoformat(
                timespec="seconds"
            )
            target["switch_result"] = "aborted"
            self._write(data)
            return target

    def mark_switch_uncertain(self, switch_id: str) -> dict[str, Any]:
        with self._lock:
            data = self._read()
            target = self._pending_entry(data, switch_id)
            target["state"] = "uncertain"
            target["switch_result"] = "uncertain"
            self._write(data)
            return target

    def commit_switch(self, switch_id: str) -> dict[str, Any]:
        """Atomically activate target and release source in one write."""
        with self._lock:
            data = self._read()
            target = self._pending_entry(data, switch_id)
            source = data["leases"].get(str(target.get("source_session_id", "")))
            if source is None or source.get("state") != "active":
                raise SessionLeaseConflict("source lease is no longer active")
            if (
                source.get("run_id") != target.get("run_id")
                or source.get("role") != target.get("role")
                or source.get("workspace") != target.get("workspace")
            ):
                raise SessionLeaseConflict("source lease does not match the pending switch")
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            target["state"] = "active"
            target["released_at"] = ""
            target["switch_result"] = "committed"
            target["switched_from"] = target.get("source_session_id", "")
            source["state"] = "released"
            source["released_at"] = now
            source["switched_to"] = target.get("session_id", "")
            self._write(data)
            return {"source": source, "target": target}

    def switch_for_run(self, run_id: str) -> dict[str, Any] | None:
        """The one pending/uncertain switch target held for ``run_id``, if any."""
        blocking = [
            entry
            for entry in self.blocking_for_run(run_id)
            if valid_switch_id(entry.get("switch_id"))
        ]
        if len(blocking) > 1:
            raise SessionLeaseConflict("more than one unresolved switch exists for this run")
        return blocking[0] if blocking else None

    def resolve_switch(self, switch_id: str, *, run_committed: bool) -> dict[str, Any]:
        """Explicitly finish a pending/uncertain switch after a crash or failed commit.

        The caller decides ``run_committed`` from the durable run document, which
        is authoritative: a committed run gets target active + source released
        (the commit that failed); an uncommitted run gets the target released (the
        abort that never ran).  No provider I/O and no run write happen here.
        """
        if not valid_switch_id(switch_id):
            raise SessionLeaseConflict("switch id is invalid")
        with self._lock:
            data = self._read()
            target = next(
                (
                    entry
                    for entry in data["leases"].values()
                    if entry.get("switch_id") == switch_id
                    and entry.get("state") in ("pending_switch", "uncertain")
                ),
                None,
            )
            if target is None:
                raise SessionLeaseConflict("no pending or uncertain switch with this id")
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            previous_state = target.get("state", "")
            if not run_committed:
                target["state"] = "released"
                target["released_at"] = now
                target["switch_result"] = "aborted_by_recovery"
                target["recovered_at"] = now
                target["recovery"] = "explicit"
                self._write(data)
                return {"result": "aborted", "previous_state": previous_state, "target": target}
            source = data["leases"].get(str(target.get("source_session_id", "")))
            if source is not None and source.get("state") == "active":
                if (
                    source.get("run_id") != target.get("run_id")
                    or source.get("role") != target.get("role")
                    or source.get("workspace") != target.get("workspace")
                ):
                    raise SessionLeaseConflict("source lease does not match the switch")
                source["state"] = "released"
                source["released_at"] = now
                source["switched_to"] = target.get("session_id", "")
            elif source is not None and source.get("state") != "released":
                raise SessionLeaseConflict(
                    f"source lease state is {source.get('state')!r}; refusing to resolve"
                )
            target["state"] = "active"
            target["released_at"] = ""
            target["switch_result"] = "committed_by_recovery"
            target["switched_from"] = target.get("source_session_id", "")
            target["recovered_at"] = now
            target["recovery"] = "explicit"
            self._write(data)
            return {
                "result": "committed",
                "previous_state": previous_state,
                "source": source,
                "target": target,
            }

    def reattach(
        self,
        session_id: str,
        *,
        workspace: str,
        run_id: str,
        role: str,
    ) -> dict[str, Any]:
        """Re-attach an active lease to the session a run currently records.

        The caller passes the run document's current role session.  Any other
        active lease held for the same workspace/run/role is therefore orphaned
        and is released in the same write.  No provider I/O and no run write.
        """
        workspace = _canonical_workspace(workspace)
        with self._lock:
            data = self._read()
            for entry in data["leases"].values():
                if entry.get("run_id") == run_id and entry.get("state") in (
                    "pending_switch",
                    "uncertain",
                ):
                    raise SessionLeaseConflict(
                        "the run has an unresolved switch or uncertain lease; resolve it first"
                    )
            existing = data["leases"].get(session_id)
            if existing is not None and existing.get("state") == "active":
                if (
                    existing.get("workspace") == workspace
                    and existing.get("run_id") == run_id
                    and existing.get("role") == role
                ):
                    raise SessionLeaseConflict("the session already holds this run's lease")
                raise SessionLeaseConflict("session is leased by another run or role")
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            orphans: list[str] = []
            for other_id, entry in data["leases"].items():
                if (
                    other_id != session_id
                    and entry.get("state") == "active"
                    and entry.get("workspace") == workspace
                    and entry.get("run_id") == run_id
                    and entry.get("role") == role
                ):
                    entry["state"] = "released"
                    entry["released_at"] = now
                    entry["released_by"] = "reattach"
                    entry["superseded_by"] = session_id
                    orphans.append(other_id)
            record = {
                "session_id": session_id,
                "workspace": workspace,
                "run_id": run_id,
                "role": role,
                "state": "active",
                "acquired_at": now,
                "released_at": "",
                "evidence": "local",
                "recovery": "reattach",
            }
            data["leases"][session_id] = record
            self._write(data)
            return {"lease": record, "released_orphans": orphans}

    def release_run(self, run_id: str) -> int:
        with self._lock:
            data = self._read()
            released = 0
            for entry in data["leases"].values():
                if entry.get("run_id") == run_id and entry.get("state") in (
                    "active",
                    "pending_switch",
                ):
                    entry["state"] = "released"
                    entry["released_at"] = datetime.now(timezone.utc).isoformat(
                        timespec="seconds"
                    )
                    released += 1
            if released:
                self._write(data)
            return released

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

    def recover(
        self, session_id: str, *, expected_state: str | None = None
    ) -> dict[str, Any] | None:
        """Explicitly release a stale active/pending/uncertain lease.

        This is a local recovery action: it does not contact the provider, does
        not abort a turn and does not switch any run.  The caller must have
        verified the session out of band.
        """
        with self._lock:
            data = self._read()
            entry = data["leases"].get(session_id)
            if entry is None:
                return None
            state = entry.get("state")
            if state not in ("active", "pending_switch", "uncertain"):
                return None
            if expected_state is not None and state != expected_state:
                raise SessionLeaseConflict(
                    f"lease state is {state!r}, expected {expected_state!r}"
                )
            entry["previous_state"] = state
            entry["state"] = "released"
            entry["released_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            entry["recovered_at"] = entry["released_at"]
            entry["recovery"] = "explicit"
            self._write(data)
            return entry

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
            if value.get("state") not in (
                "active",
                "pending_switch",
                "released",
                "uncertain",
            ):
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
