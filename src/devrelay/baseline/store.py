"""Durable persistence of task baseline artifacts.

Artifact layout per task::

    .devrelay/tasks/<DR-XXXX>/baseline/
        baseline.json   # validated WorkspaceBaseline (machine truth)
        manifest.json   # human-readable companion (entries + dirty lists)
        tracked.patch   # HEAD -> task-start-worktree diff (--binary, renames)
        files/<sha1>.blob   # raw copies of pre-existing untracked files

Everything is read back through validation - a missing or corrupted artifact
raises :class:`BaselineCorruptError` (never a silent guess).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from devrelay.artifacts.store import ArtifactStore
from devrelay.errors import BaselineCorruptError
from devrelay.models import BaselineUntrackedEntry, WorkspaceBaseline

MANIFEST_VERSION = 1


class BaselineStore:
    """Reads/writes the baseline artifacts of one task."""

    def __init__(self, store: ArtifactStore) -> None:
        self._store = store
        self.root = store.root

    def baseline_dir(self, task_id: str) -> Path:
        return self._store.baseline_dir(task_id)

    def baseline_json_path(self, task_id: str) -> Path:
        return self.baseline_dir(task_id) / "baseline.json"

    def manifest_path(self, task_id: str) -> Path:
        return self.baseline_dir(task_id) / "manifest.json"

    def patch_path(self, task_id: str) -> Path:
        return self.baseline_dir(task_id) / "tracked.patch"

    def files_dir(self, task_id: str) -> Path:
        return self.baseline_dir(task_id) / "files"

    # ------------------------------------------------------------------
    def write(
        self,
        task_id: str,
        baseline: WorkspaceBaseline,
        patch_bytes: bytes,
        untracked_files: list[tuple[str, bytes]],
    ) -> Path:
        """Persist one captured baseline (all-or-nothing on validation)."""
        directory = self.baseline_dir(task_id)
        directory.mkdir(parents=True, exist_ok=True)
        files_dir = directory / "files"
        files_dir.mkdir(parents=True, exist_ok=True)
        self._store.write_text(
            self.baseline_json_path(task_id),
            json.dumps(baseline.model_dump(mode="json"), indent=2, ensure_ascii=False),
        )
        self._store.write_bytes(self.patch_path(task_id), patch_bytes)
        for storage_name, data in untracked_files:
            self._store.write_bytes(files_dir / storage_name, data)
        manifest = {
            "manifest_version": MANIFEST_VERSION,
            "baseline_schema_version": baseline.baseline_schema_version,
            "task_id": task_id,
            "preexisting_dirty_files": baseline.preexisting_dirty_files,
            "preexisting_untracked_files": baseline.preexisting_untracked_files,
            "untracked_entries": [
                entry.model_dump(mode="json")
                for entry in baseline.untracked_entries
            ],
        }
        self._store.write_text(
            self.manifest_path(task_id),
            json.dumps(manifest, indent=2, ensure_ascii=False),
        )
        return directory

    # ------------------------------------------------------------------
    def load(self, task_id: str) -> tuple[WorkspaceBaseline, bytes]:
        """Load and validate the baseline artifacts of a task."""
        try:
            baseline_data = json.loads(
                self.baseline_json_path(task_id).read_text(encoding="utf-8")
            )
            baseline = WorkspaceBaseline.model_validate(baseline_data)
            manifest = json.loads(
                self.manifest_path(task_id).read_text(encoding="utf-8")
            )
            patch_bytes = self.patch_path(task_id).read_bytes()
            if not isinstance(manifest, dict) or manifest.get("manifest_version") != MANIFEST_VERSION:
                raise ValueError("manifest_version mismatch")
            expected = {
                entry.rel_path: entry for entry in baseline.untracked_entries
            }
            manifest_entries = manifest.get("untracked_entries") or []
            if len(manifest_entries) != len(expected):
                raise ValueError("manifest/baseline untracked entry count mismatch")
            for entry_data in manifest_entries:
                entry = BaselineUntrackedEntry.model_validate(entry_data)
                if entry.rel_path not in expected:
                    raise ValueError(f"manifest entry {entry.rel_path!r} not in baseline")
                stored = self.files_dir(task_id) / entry.storage_name
                if not stored.is_file():
                    raise ValueError(f"stored blob missing: {entry.storage_name}")
                if stored.stat().st_size != entry.size:
                    raise ValueError(
                        f"stored blob size mismatch for {entry.rel_path!r}"
                    )
        except BaselineCorruptError:
            raise
        except Exception as exc:  # JSON/parse/missing file/OSError...
            raise BaselineCorruptError(
                f"baseline artifacts for task {task_id} are corrupt or missing: "
                f"{exc}. DevRelay does not guess - recreate the task so a fresh "
                "baseline is captured."
            ) from exc
        return baseline, patch_bytes

    def read_untracked_file(self, task_id: str, entry: BaselineUntrackedEntry) -> bytes:
        path = self.files_dir(task_id) / entry.storage_name
        try:
            return path.read_bytes()
        except OSError as exc:
            raise BaselineCorruptError(
                f"cannot read stored baseline file {entry.storage_name!r}: {exc}"
            ) from exc

    def validate(self, task_id: str) -> WorkspaceBaseline:
        baseline, _ = self.load(task_id)
        return baseline
