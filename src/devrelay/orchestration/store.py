"""Durable, single-writer orchestration store (v0.3-D).

Layout::

    <workspace>/.devrelay/orchestration/runs/<run_id>.json

* run ids are **generated** (``DR-<32 hex>``) and validated against a strict
  pattern before they ever touch the filesystem, so a caller-supplied id can
  never become a traversal primitive;
* writes are atomic (unique temp file + ``os.replace``) against a crash of this
  process; durability against power loss is **not** claimed (no ``fsync``);
* a missing run is ``orchestration_run_not_found``; an unreadable/corrupt run is
  ``orchestration_state_corrupt`` - the store never silently recreates or resets
  a run.

Single-writer scope: the shipped stdio MCP server builds exactly one tool
surface, and that surface serializes every tool body with one execution lock, so
one server process is the only writer here.  Running several surfaces or several
processes against one workspace is explicitly **unsupported** for v0.3-D (no
cross-process locking, no lease, no recovery); every document is additionally
bound to the workspace it was created in, so a copied-in run is refused.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from devrelay.errors import OrchestrationRunNotFoundError, OrchestrationStateCorruptError
from devrelay.orchestration.invariants import validate_run_semantics
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
    """Strict full match: no prefix/suffix, no trailing newline or CR."""
    return isinstance(run_id, str) and bool(_RUN_ID_RE.fullmatch(run_id))


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
        except OrchestrationStateCorruptError:
            # semantic invariants already explained the problem precisely
            raise
        except Exception as exc:  # noqa: BLE001 - pydantic validation surface
            raise OrchestrationStateCorruptError(
                f"orchestration run {run_id} is malformed ({type(exc).__name__}); "
                "refusing to reset or recreate it"
            ) from exc
        if run.run_id != run_id:
            raise OrchestrationStateCorruptError(
                f"orchestration run {run_id} contains a different run id; refusing to use it"
            )
        self._require_provenance(run)
        self._require_bound_workspace(run)
        return run

    def _require_provenance(self, run: OrchestrationRun) -> None:
        """A persisted run must record the transition that produced its state."""
        if run.last_transition is None:
            raise OrchestrationStateCorruptError(
                f"orchestration run {run.run_id} carries no transition provenance; "
                "refusing to treat it as authoritative"
            )

    def _require_bound_workspace(self, run: OrchestrationRun) -> None:
        """A run copied in from another workspace is corrupt here, never adopted."""
        bound = str(self.devrelay_dir.parent.resolve())
        stored = str(Path(run.workspace).resolve()) if run.workspace else ""
        if not stored or stored != bound:
            raise OrchestrationStateCorruptError(
                f"orchestration run {run.run_id} is bound to workspace "
                f"{run.workspace!r}, which is not this store's workspace "
                f"({bound}); refusing to adopt or rewrite it"
            )

    def save(self, run: OrchestrationRun) -> None:
        """Atomically persist *run* (unique temp file + replace).

        The semantic invariants are re-checked here as well as on load, so an
        internally inconsistent run can never reach the disk in the first place.
        """
        validate_run_semantics(run)
        self._require_provenance(run)
        self._require_bound_workspace(run)
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
