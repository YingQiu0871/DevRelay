"""Frozen task policy snapshots: classification, integrity, freeze (v0.2-B).

The snapshot (``tasks/<id>/config.snapshot.yaml``) is the *sole* policy
authority for a task that has one.  This module owns:

* the five-state classifier (:class:`SnapshotState`) derived from persisted
  provenance - never from "the file happens not to exist";
* byte-true integrity verification (SHA-256 of the exact bytes on disk, checked
  *before* the YAML is parsed);
* writing a snapshot once, LF-only, with provenance.

Nothing here consults a live profile file: classification is state-only plus the
task's own snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from devrelay.artifacts.store import ArtifactStore, sha256_file
from devrelay.config import (
    ConfigError,
    PolicyDocument,
    dump_policy_yaml,
    load_policy_snapshot,
)
from devrelay.errors import (
    PolicySnapshotIntegrityError,
    PolicySnapshotInvalidError,
    PolicySnapshotMissingError,
    PolicySnapshotStateError,
)
from devrelay.models import (
    SNAPSHOT_ERA_SCHEMA,
    PolicyProvenance,
    ProfileRef,
    TaskRun,
)

SNAPSHOT_FILENAME = "config.snapshot.yaml"
MAX_SNAPSHOT_BYTES = 1024 * 1024
RESOLVER_VERSION = "0.2-B/1"


class SnapshotState(str, Enum):
    """The complete, disjoint taxonomy of a task's snapshot state."""

    VALID = "valid"
    LEGACY_LIVE = "legacy_live"
    MISSING = "missing"
    INVALID = "invalid"
    HASH_MISMATCH = "hash_mismatch"


@dataclass(frozen=True)
class SnapshotCheck:
    """Classification result plus the diagnostic detail behind it."""

    state: SnapshotState
    detail: str = ""
    path: Path | None = None
    expected_sha256: str = ""
    actual_sha256: str = ""


def snapshot_path(store: ArtifactStore, task_id: str) -> Path:
    return store.task_dir(task_id) / SNAPSHOT_FILENAME


def snapshot_expected(task: TaskRun) -> bool:
    """Does persisted provenance say a snapshot governs this task?

    The discriminator is provenance, never ``snapshot.exists()``: deleting the
    snapshot of a modern task must move it to MISSING, never to LEGACY_LIVE.
    """
    if task.policy_source == "snapshot":
        return True
    version = int(getattr(task, "state_schema_version", 0) or 0)
    return version >= SNAPSHOT_ERA_SCHEMA and bool(
        getattr(task, "policy_snapshot_path", "")
    )


def recorded_snapshot_path(task: TaskRun) -> str:
    """Persisted snapshot path, with the v0.2-A default for older tasks."""
    recorded = getattr(task, "policy_snapshot_path", "") or ""
    if recorded:
        return recorded
    return f".devrelay/tasks/{task.task_id}/{SNAPSHOT_FILENAME}"


def _contained(path: Path, task_dir: Path) -> bool:
    try:
        path.resolve().relative_to(task_dir.resolve())
    except ValueError:
        return False
    return True


def check_snapshot(store: ArtifactStore, task: TaskRun) -> SnapshotCheck:
    """Classify a task's snapshot without reading any live profile."""
    task_dir = store.task_dir(task.task_id)
    path = snapshot_path(store, task.task_id)

    if not snapshot_expected(task):
        # Genuine pre-snapshot task, including the historical 'live-fallback'
        # mark v0.2-A persisted when it silently downgraded a task whose
        # snapshot had gone missing.
        return SnapshotCheck(SnapshotState.LEGACY_LIVE, detail="no snapshot provenance")

    recorded = recorded_snapshot_path(task)
    if not recorded:
        return SnapshotCheck(
            SnapshotState.MISSING,
            detail="provenance says snapshot, but no snapshot path is recorded",
            path=path,
        )
    if not _contained(path, task_dir):
        return SnapshotCheck(
            SnapshotState.INVALID,
            detail="snapshot path escapes the task directory",
            path=path,
        )
    if not path.is_file():
        return SnapshotCheck(
            SnapshotState.MISSING, detail="snapshot file is absent", path=path
        )
    try:
        size = path.stat().st_size
        actual = sha256_file(path)
    except OSError as exc:
        return SnapshotCheck(
            SnapshotState.INVALID, detail=f"unreadable: {exc}", path=path
        )
    if size > MAX_SNAPSHOT_BYTES:
        return SnapshotCheck(
            SnapshotState.INVALID,
            detail=f"snapshot is {size} bytes (limit {MAX_SNAPSHOT_BYTES})",
            path=path,
        )

    recorded_digest = getattr(task, "policy_config_sha256", "") or ""
    if recorded_digest:
        if actual != recorded_digest:
            return SnapshotCheck(
                SnapshotState.HASH_MISMATCH,
                detail="snapshot bytes differ from the recorded digest",
                path=path,
                expected_sha256=recorded_digest,
                actual_sha256=actual,
            )
        strict = True
    else:
        version = int(getattr(task, "state_schema_version", 0) or 0)
        if version >= SNAPSHOT_ERA_SCHEMA:
            return SnapshotCheck(
                SnapshotState.INVALID,
                detail=(
                    "integrity_metadata_absent: a schema-5 snapshot task must "
                    "record policy_config_sha256"
                ),
                path=path,
                actual_sha256=actual,
            )
        # Approved legacy tolerance: digest-less v0.2-A snapshots were a full
        # workspace-config dump; known wiring keys are dropped, everything else
        # must still validate.
        strict = False

    try:
        load_policy_snapshot(path, strict=strict, source=str(path))
    except ConfigError as exc:
        return SnapshotCheck(
            SnapshotState.INVALID, detail=str(exc), path=path, actual_sha256=actual
        )
    return SnapshotCheck(SnapshotState.VALID, detail="", path=path, actual_sha256=actual)


def classify_snapshot_state(
    task: TaskRun, store: ArtifactStore
) -> tuple[SnapshotState, str]:
    """(state, detail) for *task*, computed read-only."""
    check = check_snapshot(store, task)
    return check.state, check.detail


def read_snapshot_document(
    store: ArtifactStore, task: TaskRun
) -> tuple[PolicyDocument, list[str], str]:
    """Parse the snapshot of a VALID task: (document, dropped keys, digest)."""
    check = check_snapshot(store, task)
    if check.state is not SnapshotState.VALID:
        raise snapshot_error(check)
    assert check.path is not None
    strict = bool(getattr(task, "policy_config_sha256", "") or "")
    document, dropped = load_policy_snapshot(
        check.path, strict=strict, source=str(check.path)
    )
    return document, dropped, check.actual_sha256


def snapshot_error(check: SnapshotCheck):
    """The typed, fail-closed error for a non-valid snapshot state."""
    if check.state is SnapshotState.MISSING:
        return PolicySnapshotMissingError(check.detail, path=check.path)
    if check.state is SnapshotState.HASH_MISMATCH:
        return PolicySnapshotIntegrityError(
            check.detail,
            path=check.path,
            expected_sha256=check.expected_sha256,
            actual_sha256=check.actual_sha256,
        )
    if check.state is SnapshotState.INVALID:
        return PolicySnapshotInvalidError(check.detail, path=check.path)
    return PolicySnapshotStateError(
        f"task has no usable frozen policy ({check.state.value}): {check.detail}"
    )


def freeze_policy(
    store: ArtifactStore,
    task_id: str,
    document: PolicyDocument,
    provenance: PolicyProvenance,
) -> tuple[str, PolicyProvenance]:
    """Write the task's policy snapshot; return (digest of written bytes, provenance)."""
    path = snapshot_path(store, task_id)
    _written, digest = store.write_text_with_digest(path, dump_policy_yaml(document))
    updated = provenance.model_copy(
        update={"snapshot_sha256": digest, "resolver_version": RESOLVER_VERSION}
    )
    return digest, updated


def build_provenance(
    *,
    generation: int,
    selector_raw: list[str] | None = None,
    profiles: list[ProfileRef] | None = None,
    workspace_config_sha256: str = "",
    integrity: str = "sha256_verified",
    dropped_legacy_keys: list[str] | None = None,
) -> PolicyProvenance:
    """Provenance for one frozen-policy generation."""
    return PolicyProvenance(
        generation=generation,
        selector_raw=list(selector_raw or []),
        profiles=list(profiles or []),
        workspace_config_sha256=workspace_config_sha256,
        resolver_version=RESOLVER_VERSION,
        integrity=integrity,
        dropped_legacy_keys=list(dropped_legacy_keys or []),
    )
