"""Generate a minimal CycloneDX SBOM for the portable runtime dependency closure."""

from __future__ import annotations

import argparse
import json
import os
import re
import uuid
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from typing import Any

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

PROJECT_URL = "https://github.com/YingQiu0871/DevRelay"
ROOT_REF = "pkg:pypi/devrelay"


def _license(name: str) -> str:
    meta = distribution(name).metadata
    value = meta.get("License-Expression") or meta.get("License") or ""
    value = re.sub(r"\s+", " ", value).strip()
    return value[:200]


def _resolve(name: str, extras: set[str], seen: dict[str, str], order: list[str]) -> None:
    canonical = canonicalize_name(name)
    if canonical in seen:
        return
    try:
        dist = distribution(canonical)
    except PackageNotFoundError as exc:
        raise SystemExit(f"runtime dependency {canonical!r} is not installed") from exc
    seen[canonical] = dist.version
    order.append(canonical)
    for raw in dist.requires or ():
        requirement = Requirement(raw)
        if requirement.marker is not None:
            values = extras or {""}
            if not any(
                requirement.marker.evaluate({**default_environment(), "extra": extra})
                for extra in values
            ):
                continue
        _resolve(requirement.name, set(), seen, order)


def build(version: str, *, root_extras: set[str] | None = None) -> dict[str, Any]:
    extras = root_extras or {"web"}
    seen: dict[str, str] = {}
    order: list[str] = []
    for raw in distribution("devrelay").requires or ():
        requirement = Requirement(raw)
        if requirement.marker is not None:
            if not any(
                requirement.marker.evaluate({**default_environment(), "extra": extra})
                for extra in extras
            ):
                continue
        _resolve(requirement.name, set(), seen, order)

    components: list[dict[str, Any]] = []
    refs: list[str] = []
    for name in sorted(seen):
        ref = f"pkg:pypi/{name}@{seen[name]}"
        refs.append(ref)
        component: dict[str, Any] = {
            "type": "library",
            "bom-ref": ref,
            "name": name,
            "version": seen[name],
            "purl": ref,
        }
        license_text = _license(name)
        if license_text:
            component["licenses"] = [{"license": {"name": license_text}}]
        components.append(component)

    timestamp = os.environ.get("SOURCE_DATE_EPOCH")
    if timestamp:
        generated = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
    else:
        generated = datetime.now(timezone.utc)
    serial = uuid.uuid5(uuid.NAMESPACE_URL, f"{PROJECT_URL}/releases/tag/v{version}")
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{serial}",
        "version": 1,
        "metadata": {
            "timestamp": generated.isoformat().replace("+00:00", "Z"),
            "tools": {
                "components": [
                    {
                        "type": "application",
                        "name": "DevRelay SBOM generator",
                        "version": "1",
                    }
                ]
            },
            "component": {
                "type": "application",
                "bom-ref": ROOT_REF,
                "name": "devrelay",
                "version": version,
                "purl": f"{ROOT_REF}@{version}",
                "licenses": [{"license": {"name": "MIT"}}],
                "externalReferences": [{"type": "vcs", "url": PROJECT_URL}],
            },
        },
        "components": components,
        "dependencies": [{"ref": ROOT_REF, "dependsOn": refs}],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = build(args.version)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(args.output)


if __name__ == "__main__":
    main()
