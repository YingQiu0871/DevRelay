"""Filesystem-backed artifact store.

Every task lives under ``.devrelay/tasks/<DR-XXXX>/`` and is fully
human-readable; machine state is JSON (``state.json``).  No SQLite, no hidden
state.  Writes are atomic (temp file + ``os.replace``).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from devrelay.errors import DevRelayError, TaskNotFoundError
from devrelay.models import TaskRun


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


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

    # -- task persistence -------------------------------------------------
    def write_task(self, task: TaskRun) -> None:
        path = self.state_path(task.task_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        for sub in ("implementation", "reviews", "logs", "final"):
            (path.parent / sub).mkdir(parents=True, exist_ok=True)
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

    def read_task(self, task_id: str) -> TaskRun:
        path = self.state_path(task_id)
        if not path.is_file():
            raise TaskNotFoundError(
                f"task {task_id} does not exist (looked in {path.parent})"
            )
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return TaskRun.model_validate(data)
        except (json.JSONDecodeError, OSError, Exception) as exc:
            if isinstance(exc, (json.JSONDecodeError, OSError)):
                raise DevRelayError(f"corrupt task state {path}: {exc}") from exc
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
