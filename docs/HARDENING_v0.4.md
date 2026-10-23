# DevRelay v0.4 hardening pass

Date: 2026-10-22/23.  Scope: accepted A/B/C/D surface, release pipeline and the
E1 portable package.  This is not a new feature stage.

## Completed in this pass

- **Release actions pinned to full commit SHAs** in `test.yml` and
  `release.yml` (checkout, setup-python, upload/download-artifact, PyPA
  publish).  A static test rejects unpinned remote actions.
- **Node.js 24 action runtime** (2026-10-23): pinned actions upgraded to
  checkout v7.0.1, setup-python v7.1.0, upload-artifact v7.0.2 and
  download-artifact v8.0.2, removing the Node 20 warnings seen during the
  v0.4.0 release.
- **E1 portable packaging** added with a Windows-only PyInstaller onedir build;
  the release gate requires the portable zip and CycloneDX SBOM alongside wheel,
  sdist and `SHA256SUMS`.
- **CycloneDX SBOM** (2026-10-23): `scripts/build_sbom.py` resolves the portable
  runtime dependency closure (base + `web` extra, markers evaluated) and emits
  CycloneDX 1.5 JSON.  The portable zip contains `SBOM.cdx.json`; a standalone
  `DevRelay-SBOM.cdx.json` is attached to the next Release.  This is not a
  byte-reproducible build or a lock file.
- **Prior review P1/P2 fixes retained**:
  - D1 activation no longer awaits while holding a thread lock;
  - C2c provider I/O is offloaded from the event loop and pending manual
    prompts are serialized;
  - C2b state conflicts map to 409 and interrupt requires a matching in-flight
    role turn;
  - C2a task diff is a read-only `git diff --stat` with no raw path leak.
- **Release tests** cover the portable/SBOM assets, checksum membership,
  attachment order and final five-asset gate in addition to the existing
  tag/PyPI/draft safety checks.
- **Idempotent reruns no longer block on the Windows build**: the Windows job
  now checks PyPI before building, and the publish job tolerates the absent
  artifact while still requiring the already-attached portable asset.  A rerun
  after PyPI publication cannot spend 45 minutes rebuilding a discarded zip or
  fail merely because the Windows runner is unavailable.

## Residual risks (explicitly not solved)

| Risk | State | Mitigation |
| --- | --- | --- |
| Pause not implemented | Accepted | No fake pause; interrupt is an abort. |
| Manual-prompt pending marker is process-local | Accepted | Restart clears it; CLI can still start turns. |
| Run-recorded session is not exclusive ownership | Accepted | Role + matching in-flight turn required; bridge verifies workspace only. |
| Active project selection is in-memory | Accepted | Restart returns to the CLI workspace; documented. |
| Project root replaced at the same path | Accepted | Same-user registry trust; activation rejects non-absolute roots. |
| Provider call can occupy one worker for bridge timeout | Accepted | `run_in_threadpool` keeps the event loop responsive; bridge timeout bounds it. |
| Portable `.exe` installer / code signing not shipped | Deferred | E1 ships an unsigned portable zip; installer not faked. |
| Portable build is not byte-reproducible | Accepted | SBOM records resolved versions; no lock/SBOM reproducibility guarantee yet. |
| Shared `%TEMP%` residue can flake one baseline test | Operational | Run the suite with an isolated `TEMP/TMP/TMPDIR` (see below). |
| Release action SHA values need manual review | Accepted | Static test enforces pinning shape; SHAs are reviewed on bump. |
| Actions emit Node.js 20 deprecation warnings | Fixed | Bumped to Node.js 24 action releases; verify on the next CI run. |

## Verification

```powershell
$tempRoot = Join-Path $env:TEMP ('devrelay-temp-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
$env:TEMP = $tempRoot; $env:TMP = $tempRoot; $env:TMPDIR = $tempRoot
python -m pytest -q
python -m pytest -q tests/test_release_workflow.py
```

Expected: full suite **1,348 collected — 1,346 pass + 2 environment skips**;
release workflow and SBOM tests green.

SBOM generation:

```powershell
python scripts/build_sbom.py --version 0.4.0 --output DevRelay-SBOM.cdx.json
```

Portable build (Windows, with PyInstaller installed):

```powershell
python -m build --wheel --outdir dist
python scripts/build_portable.py --version <version> --dist dist --output windows-assets
```

The script runs `devrelay.exe version` before writing the zip.

## Not claimed

This pass does not add pause, session switching, persistent active projects,
installer/code signing, package-manager manifests or a WebSocket stream.
