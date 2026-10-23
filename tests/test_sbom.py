"""CycloneDX SBOM generation tests for the portable runtime closure."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_sbom import build  # noqa: E402


def test_sbom_is_cyclonedx_and_contains_runtime_components():
    data = build("0.4.0")
    assert data["bomFormat"] == "CycloneDX"
    assert data["specVersion"] == "1.5"
    assert data["metadata"]["component"]["name"] == "devrelay"
    assert data["metadata"]["component"]["version"] == "0.4.0"
    names = {component["name"] for component in data["components"]}
    assert {"typer", "pydantic", "starlette", "uvicorn"} <= names
    assert not {"pytest", "pyinstaller", "mcp"} & names


def test_sbom_components_are_purls_and_root_dependencies_are_complete():
    data = build("0.4.0")
    refs = {component["bom-ref"] for component in data["components"]}
    for component in data["components"]:
        assert component["purl"] == component["bom-ref"]
        assert component["bom-ref"].startswith("pkg:pypi/")
    assert len(data["dependencies"]) == 1
    assert data["dependencies"][0]["ref"] == "pkg:pypi/devrelay"
    assert set(data["dependencies"][0]["dependsOn"]) == refs


def test_sbom_serial_is_deterministic_for_a_version():
    first = build("0.4.0")["serialNumber"]
    second = build("0.4.0")["serialNumber"]
    assert first == second
    assert first.startswith("urn:uuid:")
