"""DevRelay control-plane guard (v0.2-C).

A Codex child runs with ``--sandbox workspace-write`` inside the workspace, so
it *can* write ``.devrelay/**``.  Nothing in Git observation covers that state:
it holds the task state machine, the frozen policy, the budget ledger, attempt
runs, review evidence, baselines and the workspace index.

This module builds a deterministic manifest of everything under ``.devrelay``
except the current attempt's declared staging allowlist, compares the manifest
captured **in memory before the spawn** against the one recomputed after the
child exits, and reports exact differences.

Trust rules (final design closure):

* the authoritative PRE identity exists only in parent memory while the child
  runs; nothing on disk is ever re-read as the comparison authority;
* a difference under the protected control plane is a violation, fails closed
  and is never auto-repaired;
* violation evidence contains paths, kinds, sizes and hashes - never the raw
  contents of a tampered file (it may contain model-injected secrets).
"""

from __future__ import annotations

import hashlib
import json
import os
import stat as stat_module
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from devrelay.errors import DevRelayError
from devrelay.models import utcnow_iso

# Attribute flag set on Windows for any reparse point (symlink, junction, mount
# point, app-exec link, cloud placeholder, ...).
FILE_ATTRIBUTE_REPARSE_POINT = 0x400

CONTROL_PLANE_MANIFEST_VERSION = 1

# Caps: a hostile child must not be able to exhaust parent memory or CPU by
# writing a huge file.  Files above these limits either fall back to the rooted
# baseline check (see ``hash_skipped_reason``) or fail closed.
MAX_MANIFEST_ENTRIES = 4000
MAX_HASHED_FILE_BYTES = 8 * 1024 * 1024
MAX_HASHED_TOTAL_BYTES = 64 * 1024 * 1024
MAX_PATH_CHARS = 4096

BASELINE_BLOB_MARKER = "baseline/files/"


class ControlPlaneError(DevRelayError):
    """Raised when the control plane cannot be inspected safely."""


class ControlPlaneTooLargeError(ControlPlaneError):
    """A protected file is too large to verify within the configured caps."""


def is_reparse_or_link(path: Path) -> bool:
    """Detect symlinks, junctions and any Windows reparse point.

    ``os.lstat`` alone is not enough on Windows, so the platform attribute flag
    is consulted in addition to ``islink``/``isjunction``.
    """
    try:
        info = os.lstat(str(path))
    except OSError:
        return False
    if stat_module.S_ISLNK(info.st_mode):
        return True
    checker = getattr(os.path, "isjunction", None)
    if checker is not None:
        try:
            if checker(str(path)):
                return True
        except (OSError, ValueError):  # pragma: no cover - platform defensive
            pass
    attributes = getattr(info, "st_file_attributes", 0)
    return bool(attributes & FILE_ATTRIBUTE_REPARSE_POINT)


def _entry_identity(info: os.stat_result) -> str:
    dev = getattr(info, "st_dev", None)
    ino = getattr(info, "st_ino", None)
    if dev is None or ino is None:
        return ""
    return f"{dev}:{ino}"


def _sha256_file_bounded(path: Path, max_bytes: int) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(min(65536, max_bytes - total + 1))
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ControlPlaneTooLargeError(
                    f"{path} grew beyond the {max_bytes}-byte hashing cap while "
                    "being read"
                )
            digest.update(chunk)
    return digest.hexdigest(), total


@dataclass(frozen=True)
class ManifestEntry:
    """One protected path in the control-plane manifest."""

    rel_path: str
    kind: str                      # file | dir | symlink | other
    size: int | None = None
    sha256: str | None = None
    identity: str = ""
    # Staging directory bookkeeping: metadata changes caused by the single
    # allowed child write must not look like a violation.
    metadata_exempt: bool = False
    allowed_staging_file: bool = False
    # Baseline blobs above the hashing cap are covered by the rooted baseline
    # verification instead of the control-plane manifest.
    rooted: bool = False
    hash_skipped: bool = False

    def to_json(self) -> dict:
        return {
            "rel_path": self.rel_path,
            "kind": self.kind,
            "size": self.size,
            "sha256": self.sha256,
            "identity": self.identity,
            "metadata_exempt": self.metadata_exempt,
            "allowed_staging_file": self.allowed_staging_file,
            "rooted": self.rooted,
            "hash_skipped": self.hash_skipped,
        }


@dataclass
class ControlPlaneManifest:
    """Deterministic snapshot of the protected control plane (in memory)."""

    entries: list[ManifestEntry] = field(default_factory=list)
    staging_dir: str = ""
    allowed_files: tuple[str, ...] = ()
    sha256: str = ""
    created_at: str = field(default_factory=utcnow_iso)
    hashed_bytes: int = 0
    hash_skipped_paths: list[str] = field(default_factory=list)
    version: int = CONTROL_PLANE_MANIFEST_VERSION

    def by_path(self) -> dict[str, ManifestEntry]:
        return {entry.rel_path: entry for entry in self.entries}

    def to_json(self) -> dict:
        return {
            "version": self.version,
            "staging_dir": self.staging_dir,
            "allowed_files": list(self.allowed_files),
            "created_at": self.created_at,
            "hashed_bytes": self.hashed_bytes,
            "hash_skipped_paths": list(self.hash_skipped_paths),
            "entries": [entry.to_json() for entry in self.entries],
        }

    @property
    def protected_sha256(self) -> str:
        """Identity over protected paths only (staging subtree excluded).

        Used for replay/recovery: the staging directory is transient by design
        and is cleaned after a run, so it must not participate in an identity
        that has to be recomputable later.
        """
        staging = self.staging_dir.replace("\\", "/").rstrip("/")
        prefix = staging + "/"
        entries = [
            entry.to_json()
            for entry in self.entries
            if entry.rel_path.replace("\\", "/") != staging
            and not entry.rel_path.replace("\\", "/").startswith(prefix)
        ]
        payload = json.dumps(
            {"version": self.version, "entries": entries},
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def compute_sha256(self) -> str:
        payload = json.dumps(
            {
                "version": self.version,
                "staging_dir": self.staging_dir,
                "allowed_files": list(self.allowed_files),
                "entries": [entry.to_json() for entry in self.entries],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ManifestDifference:
    """One detected control-plane change (metadata only, never content)."""

    rel_path: str
    change: str                     # created | deleted | modified | type_changed
    kind_before: str | None
    kind_after: str | None
    size_before: int | None
    size_after: int | None
    sha256_before: str | None
    sha256_after: str | None
    detail: str = ""

    def to_json(self) -> dict:
        return {
            "rel_path": self.rel_path,
            "change": self.change,
            "kind_before": self.kind_before,
            "kind_after": self.kind_after,
            "size_before": self.size_before,
            "size_after": self.size_after,
            "sha256_before": self.sha256_before,
            "sha256_after": self.sha256_after,
            "detail": self.detail,
        }


def _kind_of(path: Path, info: os.stat_result) -> str:
    if stat_module.S_ISLNK(info.st_mode):
        return "symlink"
    if is_reparse_or_link(path):
        return "symlink"
    if stat_module.S_ISDIR(info.st_mode):
        return "dir"
    if stat_module.S_ISREG(info.st_mode):
        return "file"
    return "other"


def build_manifest(
    devrelay_dir: Path,
    *,
    staging_dir: Path,
    allowed_files: Sequence[str],
    max_entries: int = MAX_MANIFEST_ENTRIES,
    max_file_bytes: int = MAX_HASHED_FILE_BYTES,
    max_total_bytes: int = MAX_HASHED_TOTAL_BYTES,
) -> ControlPlaneManifest:
    """Build the protected-plane manifest (content-hashed where allowed).

    The current attempt's staging directory is handled entry-scoped: its own
    ``size``/``mtime`` are exempt (the allowed child write legitimately changes
    them) while its identity and entry set are compared.
    """
    devrelay_dir = Path(devrelay_dir)
    staging_dir = Path(staging_dir)
    try:
        staging_rel = str(staging_dir.relative_to(devrelay_dir)).replace("\\", "/")
    except ValueError as exc:  # pragma: no cover - defensive
        raise ControlPlaneError(
            f"staging directory {staging_dir} is not inside {devrelay_dir}"
        ) from exc
    allowed = tuple(sorted(set(allowed_files)))

    manifest = ControlPlaneManifest(
        staging_dir=staging_rel, allowed_files=allowed
    )
    root_str = str(devrelay_dir)
    entries: list[ManifestEntry] = []
    total_hashed = 0

    def add(path: Path, *, inside_staging: bool) -> None:
        nonlocal total_hashed
        if len(entries) >= max_entries:
            raise ControlPlaneTooLargeError(
                f"control plane exceeds the {max_entries}-entry manifest cap"
            )
        rel = str(path.relative_to(devrelay_dir)).replace("\\", "/")
        if len(rel) > MAX_PATH_CHARS:
            raise ControlPlaneTooLargeError(
                f"control-plane path exceeds {MAX_PATH_CHARS} characters"
            )
        try:
            info = os.lstat(str(path))
        except OSError as exc:
            raise ControlPlaneError(f"cannot stat protected path {rel}: {exc}") from exc
        kind = _kind_of(path, info)
        if kind == "symlink":
            # A link/reparse point inside the control plane is itself a
            # violation: we refuse to follow it and record it explicitly.
            entries.append(
                ManifestEntry(
                    rel_path=rel,
                    kind="symlink",
                    size=None,
                    sha256=None,
                    identity=_entry_identity(info),
                )
            )
            return
        if kind == "dir":
            entries.append(
                ManifestEntry(
                    rel_path=rel,
                    kind="dir",
                    size=None,
                    sha256=None,
                    identity=_entry_identity(info),
                    metadata_exempt=inside_staging and rel == staging_rel,
                )
            )
            return
        if kind != "file":
            entries.append(
                ManifestEntry(
                    rel_path=rel,
                    kind=kind,
                    size=None,
                    sha256=None,
                    identity=_entry_identity(info),
                )
            )
            return
        size = int(info.st_size)
        is_allowed = inside_staging and Path(rel).name in allowed
        rooted = BASELINE_BLOB_MARKER in rel
        if size > max_file_bytes:
            if rooted and not is_allowed:
                # Large baseline blob: the declared hash is rooted in
                # baseline/baseline.json (content-hashed here) and verified by
                # the baseline store before use.
                manifest.hash_skipped_paths.append(rel)
                entries.append(
                    ManifestEntry(
                        rel_path=rel,
                        kind="file",
                        size=size,
                        sha256=None,
                        identity=_entry_identity(info),
                        rooted=True,
                        hash_skipped=True,
                    )
                )
                return
            raise ControlPlaneTooLargeError(
                f"protected file {rel} is {size} bytes, above the "
                f"{max_file_bytes}-byte control-plane hashing cap"
            )
        if total_hashed + size > max_total_bytes:
            raise ControlPlaneTooLargeError(
                "control plane exceeds the "
                f"{max_total_bytes}-byte total hashing cap at {rel}"
            )
        digest, read_size = _sha256_file_bounded(path, max_file_bytes)
        total_hashed += read_size
        entries.append(
            ManifestEntry(
                rel_path=rel,
                kind="file",
                size=size,
                sha256=digest,
                identity=_entry_identity(info),
                allowed_staging_file=is_allowed,
            )
        )

    for dirpath, dirnames, filenames in os.walk(root_str, followlinks=False):
        current = Path(dirpath)
        dirnames.sort()
        filenames.sort()
        inside_staging = current == staging_dir or staging_dir in current.parents
        if current != Path(root_str):
            add(current, inside_staging=inside_staging)
        for name in filenames:
            add(current / name, inside_staging=inside_staging)

    entries.sort(key=lambda entry: entry.rel_path)
    manifest.entries = entries
    manifest.hashed_bytes = total_hashed
    manifest.sha256 = manifest.compute_sha256()
    return manifest


def diff_manifests(
    before: ControlPlaneManifest, after: ControlPlaneManifest
) -> list[ManifestDifference]:
    """Differences between two manifests, allowing only the declared staging file."""
    pre = before.by_path()
    post = after.by_path()
    allowed = set(after.allowed_files or before.allowed_files)
    staging = after.staging_dir or before.staging_dir
    differences: list[ManifestDifference] = []

    for rel in sorted(set(pre) | set(post)):
        old = pre.get(rel)
        new = post.get(rel)
        if old is None and new is not None:
            if _is_allowed_staging_creation(rel, new, staging, allowed):
                continue
            differences.append(
                ManifestDifference(
                    rel_path=rel,
                    change="created",
                    kind_before=None,
                    kind_after=new.kind,
                    size_before=None,
                    size_after=new.size,
                    sha256_before=None,
                    sha256_after=new.sha256,
                )
            )
            continue
        if new is None and old is not None:
            differences.append(
                ManifestDifference(
                    rel_path=rel,
                    change="deleted",
                    kind_before=old.kind,
                    kind_after=None,
                    size_before=old.size,
                    size_after=None,
                    sha256_before=old.sha256,
                    sha256_after=None,
                )
            )
            continue
        assert old is not None and new is not None
        if old.kind != new.kind:
            differences.append(
                ManifestDifference(
                    rel_path=rel,
                    change="type_changed",
                    kind_before=old.kind,
                    kind_after=new.kind,
                    size_before=old.size,
                    size_after=new.size,
                    sha256_before=old.sha256,
                    sha256_after=new.sha256,
                    detail="file type or link/reparse state changed",
                )
            )
            continue
        if old.identity and new.identity and old.identity != new.identity:
            differences.append(
                ManifestDifference(
                    rel_path=rel,
                    change="type_changed",
                    kind_before=old.kind,
                    kind_after=new.kind,
                    size_before=old.size,
                    size_after=new.size,
                    sha256_before=old.sha256,
                    sha256_after=new.sha256,
                    detail="path identity changed (replaced in place)",
                )
            )
            continue
        metadata_exempt = old.metadata_exempt and new.metadata_exempt
        if old.size != new.size and not metadata_exempt:
            if _is_allowed_staging_file(rel, staging, allowed):
                # The allowed file's size change is the expected child write.
                continue
            differences.append(
                ManifestDifference(
                    rel_path=rel,
                    change="modified",
                    kind_before=old.kind,
                    kind_after=new.kind,
                    size_before=old.size,
                    size_after=new.size,
                    sha256_before=old.sha256,
                    sha256_after=new.sha256,
                    detail="size changed",
                )
            )
            continue
        if old.sha256 and new.sha256 and old.sha256 != new.sha256:
            differences.append(
                ManifestDifference(
                    rel_path=rel,
                    change="modified",
                    kind_before=old.kind,
                    kind_after=new.kind,
                    size_before=old.size,
                    size_after=new.size,
                    sha256_before=old.sha256,
                    sha256_after=new.sha256,
                    detail="content hash changed",
                )
            )
    return differences


def _is_allowed_staging_file(rel: str, staging: str, allowed: set[str]) -> bool:
    rel_norm = rel.replace("\\", "/")
    staging_norm = staging.replace("\\", "/").rstrip("/")
    prefix = staging_norm + "/"
    if not rel_norm.startswith(prefix):
        return False
    return rel_norm[len(prefix):] in allowed


def _is_allowed_staging_creation(
    rel: str, entry: ManifestEntry, staging: str, allowed: set[str]
) -> bool:
    return entry.kind == "file" and _is_allowed_staging_file(rel, staging, allowed)


def unexpected_manifest_paths(differences: Iterable[ManifestDifference]) -> list[str]:
    return sorted({difference.rel_path for difference in differences})


def build_staging_dir(staging_dir: Path) -> Path:
    """Create the parent-owned staging directory, refusing unsafe preconditions."""
    staging_dir = Path(staging_dir)
    parent = staging_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    for candidate in (parent, staging_dir):
        if candidate.exists() and is_reparse_or_link(candidate):
            raise ControlPlaneError(
                f"refusing to use staging path {candidate}: symlink/junction/"
                "reparse point detected"
            )
    if staging_dir.exists():
        if not staging_dir.is_dir():
            raise ControlPlaneError(
                f"refusing to use staging path {staging_dir}: not a directory"
            )
        leftovers = sorted(child.name for child in staging_dir.iterdir())
        if leftovers:
            raise ControlPlaneError(
                "stale runtime staging content for this attempt: "
                + ", ".join(leftovers[:5])
            )
    else:
        staging_dir.mkdir(parents=False)
    return staging_dir


def cleanup_staging(staging_dir: Path, *, allowed_files: Sequence[str]) -> list[str]:
    """Remove stale raw staging files (unlink then verify absence).

    Only the declared raw result file(s) are removed; any unexpected content
    makes the caller fail closed instead of silently deleting evidence.
    """
    staging_dir = Path(staging_dir)
    if not staging_dir.is_dir():
        return []
    unexpected = sorted(
        child.name
        for child in staging_dir.iterdir()
        if child.name not in set(allowed_files)
    )
    if unexpected:
        raise ControlPlaneError(
            "refusing to clean staging directory with unexpected content: "
            + ", ".join(unexpected[:5])
        )
    removed: list[str] = []
    for name in allowed_files:
        target = staging_dir / name
        if not target.exists():
            continue
        if is_reparse_or_link(target):
            raise ControlPlaneError(
                f"refusing to unlink staging path {target}: link/reparse point"
            )
        target.unlink()
        if target.exists():  # pragma: no cover - defensive
            raise ControlPlaneError(f"staging file {target} could not be removed")
        removed.append(name)
    return removed
