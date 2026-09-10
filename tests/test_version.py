"""Version single-source-of-truth tests (release preparation).

The authoritative version lives in ``pyproject.toml``; the installed
distribution metadata is derived from it.  These tests fail if the runtime
version, the packaged metadata and pyproject ever drift apart, and keep
``devrelay version`` tied to the same source.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from typer.testing import CliRunner

import devrelay
from devrelay.cli import app

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _pyproject_version() -> str:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return data["project"]["version"]


def test_runtime_version_matches_pyproject():
    assert devrelay.__version__ == _pyproject_version()


def test_installed_metadata_matches_pyproject():
    from importlib.metadata import PackageNotFoundError, version

    try:
        installed = version("devrelay")
    except PackageNotFoundError:  # not installed: pyproject remains the source
        return
    assert installed == _pyproject_version()
    assert installed == devrelay.__version__


def test_release_version_is_0_1_0():
    assert _pyproject_version() == "0.1.0"


def test_cli_version_command_reports_the_same_version():
    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert devrelay.__version__ in result.output
