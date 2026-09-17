"""Durable, single-writer orchestration store (v0.3-D).

Layout::

    <workspace>/.devrelay/orchestration/runs/<run_id>.json

* run ids are **generated** (``DR-<32 hex>``) and validated against a strict
  pattern before they ever touch the filesystem, so a caller-supplied id can
  never become a traversal primitive;
* writes are atomic (unique temp file + ``os.replace``), so a partially written
  document never appears as a valid run;
* a missing run is ``orchestration_run_not_found``; an unreadable/corrupt run is
  ``orchestration_state_corrupt`` - the store never silently recreates or resets
  a run.

Only one MCP server process writes here (the accepted v0.3-B execution boundary
serializes all tool bodies); multi-process orchestration locking is explicitly
out of scope for v0.3-D.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from devrelay.errors import OrchestrationRunNotFoundError, OrchestrationStateCorruptError
from devrelay.orchestration.models import OrchestrationRun

#: Generated run identity: prefix + 32 lowercase hex characters.
RUN_ID_PATTERN = r"^DR-[0-9a-f]{32}$"
_RUN_ID_RE = re.compile(RUN_ID_PATTERN)

#: Directory (relative to ``.devrelay``) holding run documents.
RUNS_SUBDIR = ("orchestration", "runs")


def generate_run_id() -> str:
    """Collision-resistant run identity (never a read-max-write counter)."""
    return f"DR-{uuid4().hex}"


def valid_run_id(run_id: object) -> bool:
    return isinstance(run_id, str) and bool(_RUN_ID_RE.match(run_id))


class OrchestrationStore:
    """Single-writer durable storage for orchestration runs."""

    def __init__(
        self,
        devrelay_dir: str | Path,
        *,
        run_id_factory: Callable[[], str] = generate_run_id,
        clock: Callable[[], str] | None = None,
    ) -> None:
        self.devrelay_dir = Path(devrelay_dir)
        self._run_id_factory = run_id_factory
        self._clock = clock

    # ------------------------------------------------------------------
    @property
    def root(self) -> Path:
        return self.devrelay_dir.joinpath(*RUNS_SUBDIR)

    def new_run_id(self) -> str:
        run_id = self._run_id_factory()
        if not valid_run_id(run_id):
            raise OrchestrationStateCorruptError(
                "the configured run-id factory produced an invalid orchestration id"
            )
        return run_id

    def path_for(self, run_id: object) -> Path:
        """The contained path for *run_id* (never a traversal primitive)."""
        if not valid_run_id(run_id):
            # A malformed id is "not found", never a filesystem lookup.
            raise OrchestrationRunNotFoundError(
                f"no orchestration run {run_id!r} in this workspace "
                "(run ids are generated as 'DR-<32 hex characters>')"
            )
        return self.root / f"{run_id}.json"

    # ------------------------------------------------------------------
    def exists(self, run_id: object) -> bool:
        try:
            return self.path_for(run_id).is_file()
        except OrchestrationRunNotFoundError:
            return False

    def load(self, run_id: object) -> OrchestrationRun:
        path = self.path_for(run_id)
        if not path.is_file():
            raise OrchestrationRunNotFoundError(
                f"no orchestration run {run_id} in this workspace"
            )
        try:
            payload: Any = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise OrchestrationStateCorruptError(
                f"orchestration run {run_id} is unreadable ({type(exc).__name__}); "
                "refusing to reset or recreate it"
            ) from exc
        try:
            run = OrchestrationRun.model_validate(payload)
        except Exception as exc:  # noqa: BLE001 - pydantic validation surface
            raise OrchestrationStateCorruptError(
                f"orchestration run {run_id} is malformed ({type(exc).__name__}); "
                "refusing to reset or recreate it"
            ) from exc
        if run.run_id != run_id:
            raise OrchestrationStateCorruptError(
                f"orchestration run {run_id} contains a different run id; refusing to use it"
            )
        return run

    def save(self, run: OrchestrationRun) -> None:
        """Atomically persist *run* (unique temp file + replace)."""
        path = self.path_for(run.run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(run.model_dump(mode="json"), indent=2, sort_keys=False)
        tmp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            tmp.write_text(payload + "\n", encoding="utf-8")
            os.replace(tmp, path)
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:  # pragma: no cover - best effort cleanup
                    pass

    def create(self, run: OrchestrationRun) -> OrchestrationRun:
        self.save(run)
        return run

    def touch(self, run: OrchestrationRun) -> OrchestrationRun:
        """Update ``updated_at`` and persist."""
        if self._clock is not None:
            run.updated_at = self._clock()
        self.save(run)
        return run


__all__ = ["RUNS_SUBDIR", "RUN_ID_PATTERN", "OrchestrationStore", "generate_run_id", "valid_run_id"]
