"""Discovery of the DevRelay root and workspace from the filesystem."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from devrelay.errors import WorkspaceError


def find_root(start: str | Path | None = None) -> Path | None:
    """Nearest ancestor containing a ``.devrelay`` directory or a ``.git`` dir."""
    current = Path(start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    while True:
        if (current / ".devrelay").is_dir() or (current / ".git").is_dir():
            return current
        if current.parent == current:
            return None
        current = current.parent
    return None


def require_root(start: str | Path | None = None) -> Path:
    root = find_root(start)
    if root is None:
        raise WorkspaceError(
            "No DevRelay workspace found here (no .devrelay/ or .git/ marker in "
            "this directory or any parent). Run 'devrelay init' first."
        )
    return root
