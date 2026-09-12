"""Filesystem-backed artifact store.

Every task lives under ``.devrelay/tasks/<DR-XXXX>/`` and is fully
human-readable; machine state is JSON (``state.json``).  No SQLite, no hidden
state.  Writes are atomic (temp file + ``os.replace``).
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Optional

from devrelay.errors import (
    DevRelayError,
    StateSchemaTooNewError,
    TaskNotFoundError,
)
from devrelay.models import MAX_SUPPORTED_STATE_SCHEMA, TaskRun, utcnow_iso


def encode_lf(text: str) -> bytes:
    """Deterministic UTF-8/LF bytes for every textual artifact DevRelay writes.

    v0.2-B byte discipline: Python's ``Path.write_text`` translates LF to
    ``os.linesep`` on Windows, so hashing the in-memory text and writing the
    same text produced two different byte streams (and therefore two different
    SHA-256 digests).  All textual artifacts are now written through this
    helper, and every recorded digest is the digest of the bytes it returns.
    """
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def sha256_hex(data: bytes) -> str:
    """Lowercase hex SHA-256 of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    """SHA-256 of the exact bytes on disk (never of decoded/normalized text)."""
    return sha256_hex(Path(path).read_bytes())


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def _atomic_write_text(path: Path, text: str) -> None:
    _atomic_write_bytes(path, encode_lf(text))


class ArtifactStore:
    """All DevRelay persistence for one workspace root."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.devrelay_dir = self.root / ".devrelay"
        self._index_path = self.devrelay_dir / "state.json"

    # -- initialization ---------------------------------------------------
    def is_initialized(self) -> bool:
        return self.devrelay_dir.is_dir()

    def ensure_initialized(self) -> Path:
        self.devrelay_dir.mkdir(parents=True, exist_ok=True)
        if not self._index_path.exists():
            self._write_index({})
        return self.devrelay_dir

    # -- index ------------------------------------------------------------
    def _write_index(self, index: dict[str, Any]) -> None:
        _atomic_write_text(
            self._index_path,
            json.dumps(index, indent=2, ensure_ascii=False, sort_keys=True),
        )

    def _read_index(self) -> dict[str, Any]:
        if not self._index_path.exists():
            return {"current_task": None, "tasks": {}, "next_seq": 1}
        try:
            data = json.loads(self._index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise DevRelayError(f"corrupt .devrelay/state.json: {exc}") from exc
        if not isinstance(data, dict):
            raise DevRelayError("corrupt .devrelay/state.json: not a mapping")
        data.setdefault("current_task", None)
        data.setdefault("tasks", {})
        data.setdefault("next_seq", 1)
        return data

    def allocate_task_id(self) -> str:
        index = self._read_index()
        seq = int(index.get("next_seq", 1))
        task_id = f"DR-{seq:04d}"
        index["next_seq"] = seq + 1
        self._write_index(index)
        return task_id

    def set_current_task(self, task_id: str) -> None:
        index = self._read_index()
        index["current_task"] = task_id
        self._write_index(index)

    def current_task_id(self) -> str | None:
        return self._read_index().get("current_task")

    def list_task_ids(self) -> list[str]:
        return sorted(self._read_index().get("tasks", {}).keys())

    def task_exists(self, task_id: str) -> bool:
        return (self.task_dir(task_id) / "state.json").is_file()

    # -- paths ------------------------------------------------------------
    def task_dir(self, task_id: str) -> Path:
        return self.devrelay_dir / "tasks" / task_id

    def state_path(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "state.json"

    def _sub(self, task_id: str, name: str) -> Path:
        path = self.task_dir(task_id) / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def implementation_dir(self, task_id: str) -> Path:
        return self._sub(task_id, "implementation")

    def reviews_dir(self, task_id: str) -> Path:
        return self._sub(task_id, "reviews")

    def logs_dir(self, task_id: str) -> Path:
        return self._sub(task_id, "logs")

    def final_dir(self, task_id: str) -> Path:
        return self._sub(task_id, "final")

    def baseline_dir(self, task_id: str) -> Path:
        return self._sub(task_id, "baseline")

    def policy_dir(self, task_id: str) -> Path:
        return self._sub(task_id, "policy")

    # -- v0.2-C runtime / control-plane paths -----------------------------
    def tmp_dir(self) -> Path:
        """Transient workspace (`.devrelay/tmp`): never evidence, never durable.

        Lives inside the workspace so a ``workspace-write`` sandboxed child can
        write its staging file, but inside ``.devrelay`` so it can never appear
        in a baseline, task delta or reviewer diff.
        """
        path = self.devrelay_dir / "tmp"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def attempt_staging_dir(self, task_id: str, attempt_id: str) -> Path:
        """Child-writable staging directory for exactly one attempt."""
        return self.tmp_dir() / "runtime" / attempt_id

    def task_runtime_dir(self, task_id: str, attempt_id: str) -> Path:
        """Parent-written immutable runtime evidence for one attempt."""
        return self._sub(task_id, "runtime") / attempt_id

    def control_state_dir(self, task_id: str) -> Path:
        return self._sub(task_id, "policy") / "control-state"

    def control_plane_hold_path(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "CONTROL_PLANE_HOLD.json"

    def read_control_plane_hold(self, task_id: str) -> dict[str, Any] | None:
        """Read the hold record if present (never raises on corrupt JSON)."""
        path = self.control_plane_hold_path(task_id)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"corrupt": True, "path": str(path)}
        return data if isinstance(data, dict) else {"corrupt": True, "path": str(path)}

    def write_control_plane_hold(self, task_id: str, record: dict[str, Any]) -> Path:
        """Create the hold immutably (refuse to replace an existing hold)."""
        return self.write_json_new(self.control_plane_hold_path(task_id), record)

    def clear_control_plane_hold(self, task_id: str, *, reason: str) -> Path:
        """Move the hold into the audit trail; never delete it."""
        path = self.control_plane_hold_path(task_id)
        if not path.is_file():
            raise DevRelayError(f"no control-plane hold exists for {task_id}")
        stamp = utcnow_iso().replace(":", "-")
        target = self.control_state_dir(task_id) / f"hold-cleared-{stamp}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.replace(target)
        except OSError as exc:  # pragma: no cover - defensive
            raise DevRelayError(f"cannot archive control-plane hold: {exc}") from exc
        return target

    def write_json_new(self, path: str | Path, data: Any) -> Path:
        return self.write_text_new(
            path,
            json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True),
        )

    # -- bounded I/O helpers (v0.2-C) -------------------------------------
    @staticmethod
    def read_bytes_bounded(path: str | Path, max_bytes: int) -> tuple[bytes, int, bool]:
        """Read at most ``max_bytes`` (+1 to detect overflow) — never more.

        Returns ``(data, size, truncated)``; ``truncated`` is true when the file
        is larger than the cap, in which case ``data`` holds only ``max_bytes``.
        A stat race cannot cause an unbounded allocation because the read itself
        is bounded.
        """
        full = Path(path)
        cap = max(0, int(max_bytes))
        try:
            size = full.stat().st_size
        except OSError:
            raise
        with open(full, "rb") as handle:
            data = handle.read(cap + 1)
        truncated = size > cap or len(data) > cap
        if len(data) > cap:
            data = data[:cap]
        return data, size, truncated

    # -- task persistence -------------------------------------------------
    def write_task(self, task: TaskRun) -> None:
        path = self.state_path(task.task_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        for sub in (
            "implementation",
            "reviews",
            "logs",
            "final",
            "baseline",
            "policy",
        ):
            (path.parent / sub).mkdir(parents=True, exist_ok=True)
        # Schema migration happens here and only here: read-only commands never
        # call write_task, so they never migrate a task or create a backup.
        upgraded = self._prepare_state_write(path, task)
        _atomic_write_text(
            path,
            json.dumps(upgraded.model_dump(mode="json"), indent=2, ensure_ascii=False),
        )
        self._update_index(task)
        return None

    def write_task_with_digest(self, task: TaskRun) -> str:
        """Like :meth:`write_task` but returns the SHA-256 of the written bytes.

        The digest is computed from the exact byte string handed to the
        filesystem, so it is the identity of the persisted document *without*
        reading it back (no race, no second write).  Used by the v0.2-C
        COMPLETION_READY milestone so a replay can prove that nothing edited
        ``state.json`` afterwards.
        """
        path = self.state_path(task.task_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        for sub in (
            "implementation",
            "reviews",
            "logs",
            "final",
            "baseline",
            "policy",
        ):
            (path.parent / sub).mkdir(parents=True, exist_ok=True)
        upgraded = self._prepare_state_write(path, task)
        data = json.dumps(
            upgraded.model_dump(mode="json"), indent=2, ensure_ascii=False
        ).encode("utf-8")
        _atomic_write_bytes(path, data)
        self._update_index(task)
        return hashlib.sha256(data).hexdigest()

    def _update_index(self, task: TaskRun) -> None:
        index = self._read_index()
        index.setdefault("tasks", {})[task.task_id] = {
            "title": task.title,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }
        if not index.get("current_task"):
            index["current_task"] = task.task_id
        self._write_index(index)

    def _prepare_state_write(self, path: Path, task: TaskRun) -> TaskRun:
        """Return the task to serialize, migrating an older persisted schema.

        Contract for the first mutating write of a task whose *persisted*
        ``state_schema_version`` is older than the current schema:

        1. the exact current ``state.json`` bytes are retained;
        2. ``state.v<old>.json.bak`` is created **once** with those exact bytes
           and is never overwritten afterwards;
        3. a backup failure aborts the write with ``state.json`` untouched;
        4. only then is the upgraded (schema-current) document serialized;
        5. the caller's in-memory task is never mutated - a ``model_copy`` is
           returned, so a failed write stays unambiguous and retryable.

        A task saved *only* by this version already carries the current schema,
        so no backup is created for it.
        """
        if not path.is_file():
            return task
        try:
            raw = path.read_bytes()
            previous = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return task  # unknown/corrupt previous version: nothing to migrate
        old_version = (
            previous.get("state_schema_version") if isinstance(previous, dict) else None
        )
        if not isinstance(old_version, int) or old_version >= MAX_SUPPORTED_STATE_SCHEMA:
            return task
        backup = path.with_name(f"state.v{old_version}.json.bak")
        if not backup.exists():
            # Raises on failure: the main state write below is then never reached.
            _atomic_write_bytes(backup, raw)
        if int(getattr(task, "state_schema_version", 0) or 0) >= MAX_SUPPORTED_STATE_SCHEMA:
            return task
        return task.model_copy(
            update={"state_schema_version": MAX_SUPPORTED_STATE_SCHEMA}
        )

    def read_task(self, task_id: str) -> TaskRun:
        path = self.state_path(task_id)
        if not path.is_file():
            raise TaskNotFoundError(
                f"task {task_id} does not exist (looked in {path.parent})"
            )
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise DevRelayError(f"corrupt task state {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise DevRelayError(f"invalid task state {path}: not a mapping")
        # Diagnostics before validation: TaskRun forbids extra fields, so a
        # future schema would otherwise surface as an opaque ValidationError.
        version = data.get("state_schema_version", 0)
        if isinstance(version, int) and version > MAX_SUPPORTED_STATE_SCHEMA:
            raise StateSchemaTooNewError(
                f"state for {task_id} was written by a newer DevRelay "
                f"(state_schema_version {version} > "
                f"{MAX_SUPPORTED_STATE_SCHEMA}); upgrade DevRelay"
            )
        try:
            return TaskRun.model_validate(data)
        except Exception as exc:
            raise DevRelayError(f"invalid task state {path}: {exc}") from exc

    def rel_path(self, path: str | Path) -> str:
        """Store-friendly relative path under the workspace root."""
        full = Path(path)
        try:
            return str(full.resolve().relative_to(self.root.resolve()))
        except ValueError:
            return str(full)

    # -- generic atomic file helpers -------------------------------------
    def write_text(self, path: str | Path, text: str) -> Path:
        full = Path(path)
        _atomic_write_text(full, text)
        return full

    def write_text_with_digest(self, path: str | Path, text: str) -> tuple[Path, str]:
        """Write LF-normalized text and return (path, sha256 of written bytes).

        The digest is computed from the exact byte string handed to the
        filesystem, so it always matches ``sha256_file(path)`` afterwards.
        """
        data = encode_lf(text)
        full = self.write_bytes(path, data)
        return full, sha256_hex(data)

    def write_bytes(self, path: str | Path, data: bytes) -> Path:
        full = Path(path)
        full.parent.mkdir(parents=True, exist_ok=True)
        tmp = full.with_name(f".{full.name}.tmp")
        tmp.write_bytes(data)
        os.replace(tmp, full)
        return full

    def write_bytes_new(self, path: str | Path, data: bytes) -> Path:
        """Create an immutable evidence file; refuse to replace an existing one.

        Used for refresh/recovery evidence: an attempt's artifacts are immutable
        history, so a later attempt must never overwrite them (fail closed).
        """
        full = Path(path)
        full.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(full, "xb") as handle:
                handle.write(data)
        except FileExistsError as exc:
            raise DevRelayError(
                f"refusing to overwrite existing evidence file {full}; "
                "evidence artifacts are immutable"
            ) from exc
        return full

    def write_text_new(self, path: str | Path, text: str) -> Path:
        """LF-normalized :meth:`write_bytes_new` for immutable text evidence."""
        return self.write_bytes_new(path, encode_lf(text))

    def read_bytes(self, path: str | Path) -> bytes:
        return Path(path).read_bytes()

    def write_json(self, path: str | Path, data: Any) -> Path:
        full = Path(path)
        _atomic_write_text(
            full,
            json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True),
        )
        return full

    def read_text(self, path: str | Path) -> str:
        full = Path(path)
        return full.read_text(encoding="utf-8")

    def list_dir(self, path: str | Path) -> list[str]:
        full = Path(path)
        if not full.is_dir():
            return []
        return sorted(p.name for p in full.iterdir() if p.is_file())
