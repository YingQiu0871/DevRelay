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
from devrelay.models import MAX_SUPPORTED_STATE_SCHEMA, TaskRun


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
        self._backup_before_schema_upgrade(path, task)
        _atomic_write_text(
            path, json.dumps(task.model_dump(mode="json"), indent=2, ensure_ascii=False)
        )
        index = self._read_index()
        index.setdefault("tasks", {})[task.task_id] = {
            "title": task.title,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }
        if not index.get("current_task"):
            index["current_task"] = task.task_id
        self._write_index(index)

    def _backup_before_schema_upgrade(self, path: Path, task: TaskRun) -> Path | None:
        """Keep one ``state.v<old>.json.bak`` before upgrading a task state.

        The schema migration is one-way (a v0.2-A binary cannot read schema 5),
        so the pre-upgrade bytes are preserved exactly once.
        """
        if not path.is_file():
            return None
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        old_version = previous.get("state_schema_version")
        if not isinstance(old_version, int):
            return None
        new_version = int(getattr(task, "state_schema_version", 0) or 0)
        if old_version >= new_version or old_version >= MAX_SUPPORTED_STATE_SCHEMA:
            return None
        backup = path.with_name(f"state.v{old_version}.json.bak")
        if backup.exists():
            return backup
        _atomic_write_bytes(backup, path.read_bytes())
        return backup

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
