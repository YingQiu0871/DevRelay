"""DevRelay - local AI coding orchestrator.

Plan with one model, build with Codex, review with another - without
copy-pasting between agents.

The installed distribution metadata (generated from ``pyproject.toml``) is the
single source of truth for the version; the literal below is only a fallback
for running directly from a source checkout that was never installed.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _distribution_version

try:
    __version__ = _distribution_version("devrelay")
except PackageNotFoundError:  # pragma: no cover - source checkout only
    __version__ = "0.1.0"
