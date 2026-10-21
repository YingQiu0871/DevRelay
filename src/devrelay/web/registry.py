"""Explicit, bounded project registry for the local control API."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devrelay.models import utcnow_iso
from devrelay.web.errors import WebApiError

REGISTRY_SCHEMA_VERSION = 1
MAX_PROJECTS = 32
MAX_LABEL_CHARS = 80


@dataclass(frozen=True)
class Project:
    project_id: str
    root: str
    label: str
    created_at: str

    def public(self, *, active: bool = False) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "root": self.root,
            "label": self.label,
            "created_at": self.created_at,
            "active": bool(active),
        }


def _project_id(root: Path) -> str:
    identity = os.path.normcase(str(root))
    return "prj_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]


class ProjectRegistry:
    """A tiny JSON registry; paths enter only through explicit CLI validation."""

    def __init__(self, devrelay_dir: str | Path) -> None:
        self.devrelay_dir = Path(devrelay_dir)
        self.directory = self.devrelay_dir / "web"
        self.path = self.directory / "projects.json"
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # persistence
    # ------------------------------------------------------------------
    def _read(self) -> list[Project]:
        with self._lock:
            if not self.path.exists():
                return []
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise WebApiError(
                    "registry_invalid",
                    "the project registry is unreadable",
                    status_code=500,
                ) from exc
            if not isinstance(raw, dict) or raw.get("schema_version") != REGISTRY_SCHEMA_VERSION:
                raise WebApiError(
                    "registry_invalid",
                    "the project registry has an unsupported schema",
                    status_code=500,
                )
            items = raw.get("projects")
            if not isinstance(items, list) or len(items) > MAX_PROJECTS:
                raise WebApiError(
                    "registry_invalid",
                    "the project registry is malformed",
                    status_code=500,
                )
            projects: list[Project] = []
            for item in items:
                if not isinstance(item, dict):
                    raise WebApiError("registry_invalid", "invalid project entry", status_code=500)
                try:
                    project = Project(
                        project_id=str(item["project_id"]),
                        root=str(item["root"]),
                        label=str(item.get("label", ""))[:MAX_LABEL_CHARS],
                        created_at=str(item.get("created_at", "")),
                    )
                except KeyError as exc:
                    raise WebApiError(
                        "registry_invalid", "invalid project entry", status_code=500
                    ) from exc
                if not project.project_id.startswith("prj_") or not project.root:
                    raise WebApiError("registry_invalid", "invalid project entry", status_code=500)
                projects.append(project)
            return projects

    def _write(self, projects: list[Project]) -> None:
        with self._lock:
            self.directory.mkdir(parents=True, exist_ok=True)
            payload = {
                "schema_version": REGISTRY_SCHEMA_VERSION,
                "projects": [
                    {
                        "project_id": p.project_id,
                        "root": p.root,
                        "label": p.label,
                        "created_at": p.created_at,
                    }
                    for p in projects
                ],
            }
            fd, tmp_name = tempfile.mkstemp(prefix=".projects-", dir=self.directory)
            tmp = Path(tmp_name)
            try:
                with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                    json.dump(payload, handle, indent=2, sort_keys=False)
                    handle.write("\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(tmp, self.path)
            except BaseException:
                try:
                    tmp.unlink(missing_ok=True)
                except OSError:  # pragma: no cover - defensive
                    pass
                raise
            try:
                os.chmod(self.path, 0o600)
            except OSError:  # pragma: no cover - Windows ACL is the effective owner
                pass

    # ------------------------------------------------------------------
    # public operations
    # ------------------------------------------------------------------
    def list(self) -> list[Project]:
        return self._read()

    def get(self, project_id: str) -> Project:
        for project in self._read():
            if project.project_id == project_id:
                return project
        raise WebApiError("project_not_found", "project is not registered", status_code=404)

    def add(self, root: str | Path, *, label: str = "") -> Project:
        candidate = Path(root)
        if not candidate.is_absolute():
            raise WebApiError(
                "invalid_project_path",
                "project path must be absolute",
            )
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as exc:
            raise WebApiError(
                "invalid_project_path",
                "project path cannot be resolved",
            ) from exc
        if not resolved.is_dir():
            raise WebApiError("invalid_project_path", "project path is not a directory")
        if not (resolved / ".devrelay").is_dir():
            raise WebApiError(
                "invalid_project_path",
                "project is not an initialized DevRelay workspace",
            )
        clean_label = " ".join((label or "").split())[:MAX_LABEL_CHARS]
        with self._lock:
            projects = self._read()
            canonical = os.path.normcase(str(resolved))
            for project in projects:
                if os.path.normcase(str(Path(project.root))) == canonical:
                    return project
            if len(projects) >= MAX_PROJECTS:
                raise WebApiError(
                    "project_limit_reached",
                    f"at most {MAX_PROJECTS} projects may be registered",
                )
            project = Project(
                project_id=_project_id(resolved),
                root=str(resolved),
                label=clean_label or resolved.name,
                created_at=utcnow_iso(),
            )
            if any(p.project_id == project.project_id for p in projects):
                raise WebApiError(
                    "project_id_collision",
                    "project identity collision; registry unchanged",
                    status_code=500,
                )
            projects.append(project)
            self._write(projects)
            return project

    def remove(self, project_id: str) -> None:
        with self._lock:
            projects = self._read()
            kept = [p for p in projects if p.project_id != project_id]
            if len(kept) == len(projects):
                raise WebApiError("project_not_found", "project is not registered", status_code=404)
            self._write(kept)
