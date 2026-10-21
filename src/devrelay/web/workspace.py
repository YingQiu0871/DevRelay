"""Fail-closed workspace resolution for the local web process."""

from __future__ import annotations

from pathlib import Path

from devrelay.config import ConfigError, load_wiring_config
from devrelay.web.errors import WebApiError


def resolve_workspace(workspace: str | Path) -> tuple[Path, object, Path]:
    """Return (root, wiring, .devrelay) or fail before the socket is opened."""
    if workspace is None or str(workspace).strip() == "":
        raise WebApiError(
            "workspace_required",
            "--workspace <absolute path> is required",
            status_code=503,
        )
    root = Path(workspace)
    try:
        root = root.resolve(strict=True)
    except OSError as exc:
        raise WebApiError(
            "workspace_invalid",
            f"workspace {workspace!r} cannot be resolved",
            status_code=503,
        ) from exc
    if not root.is_dir():
        raise WebApiError("workspace_invalid", "workspace is not a directory", status_code=503)
    devrelay_dir = root / ".devrelay"
    if not devrelay_dir.is_dir():
        raise WebApiError(
            "workspace_invalid",
            "workspace is not initialized (no .devrelay directory; run devrelay init)",
            status_code=503,
        )
    try:
        wiring = load_wiring_config(root)
    except ConfigError as exc:
        raise WebApiError(
            "workspace_invalid",
            "workspace configuration is invalid",
            status_code=503,
        ) from exc
    return root, wiring, devrelay_dir
