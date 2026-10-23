"""Build the Windows x64 portable folder/zip from the checked-out source."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from importlib.metadata import PackageNotFoundError, version as installed_version
from pathlib import Path

from build_sbom import build as build_sbom

README = """DevRelay portable {version} (Windows x64)

Requirements: Windows 10/11 x64.  No Python installation is required by the
end user; the executable bundles the Python runtime.

Run:
  devrelay.exe version
  devrelay.exe --help
  devrelay.exe web serve --workspace <initialized workspace>

This portable build does not install a service, add itself to PATH, or create
Start Menu shortcuts.  Extract the whole archive and keep devrelay.exe next to
the _internal directory.

The build is unsigned.  Verify SHA256SUMS before running it.

SBOM.cdx.json describes the bundled runtime dependency versions in CycloneDX
1.5 JSON.
"""


def _wheel(dist: Path, version: str) -> Path:
    matches = sorted(dist.glob(f"devrelay-{version}-py3-none-any.whl"))
    if len(matches) != 1:
        raise SystemExit(
            f"expected exactly one devrelay-{version} wheel in {dist}, got {matches}"
        )
    return matches[0]


def build(dist: Path, output: Path, version: str) -> Path:
    if sys.platform != "win32":
        raise SystemExit("the portable build must run on Windows")
    root = Path(__file__).resolve().parents[1]
    wheel = _wheel(dist, version)
    try:
        installed = installed_version("devrelay")
    except PackageNotFoundError as exc:
        raise SystemExit("devrelay must be installed before building the portable") from exc
    if installed != version:
        raise SystemExit(
            f"installed devrelay metadata is {installed}, expected {version}"
        )
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="devrelay-portable-", dir=output) as tmp:
        tmp_path = Path(tmp)
        stage = tmp_path / "stage"
        build_dir = tmp_path / "build"
        spec_dir = tmp_path / "spec"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--noconfirm",
                "--clean",
                "--onedir",
                "--name",
                "devrelay",
                "--distpath",
                str(stage),
                "--workpath",
                str(build_dir),
                "--specpath",
                str(spec_dir),
                "--paths",
                str(root / "src"),
                "--add-data",
                f"{root / 'src' / 'devrelay' / 'profiles'};devrelay/profiles",
                "--add-data",
                f"{root / 'src' / 'devrelay' / 'web' / 'static'};devrelay/web/static",
                "--copy-metadata",
                "devrelay",
                "--collect-submodules",
                "uvicorn",
                "--collect-submodules",
                "starlette",
                str(root / "src" / "devrelay" / "__main__.py"),
            ],
            cwd=root,
            check=True,
        )
        portable = stage / "devrelay"
        exe = portable / "devrelay.exe"
        if not exe.is_file():
            raise SystemExit(f"PyInstaller did not produce {exe}")
        (portable / "README-PORTABLE.txt").write_text(
            README.replace("{version}", version), encoding="utf-8"
        )
        license_path = root / "LICENSE"
        if not license_path.is_file():
            raise SystemExit(f"LICENSE is missing: {license_path}")
        shutil.copy2(license_path, portable / "LICENSE")
        smoke = subprocess.run(
            [str(exe), "version"],
            cwd=portable,
            check=True,
            capture_output=True,
            text=True,
        )
        expected = f"devrelay {version}"
        if expected not in smoke.stdout.strip():
            raise SystemExit(
                f"portable version mismatch: expected {expected!r}, got {smoke.stdout.strip()!r}"
            )
        for relative in (
            "_internal/devrelay/profiles/default.yaml",
            "_internal/devrelay/web/static/index.html",
        ):
            if not (portable / relative).is_file():
                raise SystemExit(f"portable payload is missing {relative}")
        sbom = build_sbom(version)
        (portable / "SBOM.cdx.json").write_text(
            json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (output / "DevRelay-SBOM.cdx.json").write_text(
            json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        archive = output / "DevRelay-Portable-Windows-x64.zip"
        expected_entries = {
            "DevRelay/devrelay.exe",
            "DevRelay/README-PORTABLE.txt",
            "DevRelay/LICENSE",
            "DevRelay/SBOM.cdx.json",
        }
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as handle:
            for item in sorted(portable.rglob("*")):
                if item.is_file():
                    arcname = f"DevRelay/{item.relative_to(portable).as_posix()}"
                    handle.write(item, arcname)
        with zipfile.ZipFile(archive) as handle:
            names = set(handle.namelist())
            missing = expected_entries - names
            if missing:
                raise SystemExit(f"portable zip is missing {sorted(missing)}")
            if not any(name.startswith("DevRelay/_internal/") for name in names):
                raise SystemExit("portable zip has no _internal payload")
        print(archive)
        print(wheel)
        return archive


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.dist, args.output, args.version)


if __name__ == "__main__":
    main()
