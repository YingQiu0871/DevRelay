# DevRelay portable reproducibility & lock plan

Status: **PLAN — NOT PROVEN.**  The portable build is not byte-reproducible and
no lock file is shipped today.  The CycloneDX SBOM records resolved versions but
does not make a build deterministic.

## Current gaps

1. `pip install ".[web]"` resolves open ranges at release time.
2. PyInstaller embeds build-path/timestamp metadata and collects an environment-
   dependent module set.
3. Zip entries use filesystem mtimes and platform separators (separators are now
   normalized, mtimes are not).
4. SBOM metadata timestamp and dependency set depend on the build environment.
5. No second-build digest comparison or lock hash chain in the release gate.

## Proposed lock

- Generate a **Windows/py3.13-specific** constraints file from a clean venv:
  exact versions of devrelay runtime + `web` extra + PyInstaller/build tools.
- Pin by version and hash (`--require-hashes` where practical).
- Build with `pip install --no-deps -c constraints.txt` after installing the
  locked wheelhouse; never let `.[web]` resolve at release time.
- Record the lock file in `SHA256SUMS` and the release notes.
- The lock is platform/Python-specific; do not present it as universal.

## Proposed deterministic build

- Use a fixed `SOURCE_DATE_EPOCH` and a fixed build root.
- Normalize zip entry order, timestamps and permissions (currently only POSIX
  separators are normalized).
- Disable PyInstaller timestamp/version resources or pin them.
- Generate the SBOM with the fixed epoch and a deterministic serial.
- Build twice from the same tag + lock in the same image; compare SHA-256 of
  every artifact and the normalized SBOM.
- Store the two-run evidence in the release record; if hashes differ, publish
  no reproducibility claim and list the differing bytes.

## Release gate (future)

A release may claim reproducibility only when:

1. lock file is present and marked platform-specific;
2. both builds use the same lock and `SOURCE_DATE_EPOCH`;
3. wheel, sdist, portable zip and SBOM hashes match across two builds;
4. the comparison log is attached to the release evidence;
5. the claim explicitly excludes code signing/notarization and provider runtime.

Until then, docs say **SBOM, not reproducible**.

## Proof helper

`scripts/compare_builds.py` compares two artifact directories by exact SHA-256
and fails on missing/extra/changed files.  It is only the comparison harness;
it is not evidence until two clean, locked builds are produced and the result is
recorded.

## Commands (illustrative; not yet wired)

```powershell
python -m venv .build-venv
. .build-venv/Scripts/Activate.ps1
python -m pip install --require-hashes -r requirements/portable-win-py313.lock
$env:SOURCE_DATE_EPOCH = "1792713600"
python scripts/build_portable.py --version 0.4.0 --dist dist --output build-a
# repeat in a clean directory/image -> build-b
Get-FileHash build-a/DevRelay-Portable-Windows-x64.zip
Get-FileHash build-b/DevRelay-Portable-Windows-x64.zip
python scripts/compare_builds.py build-a build-b
```

## Acceptance criteria

| ID | Criterion |
| --- | --- |
| R1 | Lock has exact versions and hashes, platform/Python labelled |
| R2 | Build uses the lock and no unconstrained resolve |
| R3 | Zip order/timestamps/permissions normalized |
| R4 | SBOM is deterministic under fixed epoch |
| R5 | Two clean builds produce identical artifact hashes |
| R6 | Evidence attached; otherwise the "reproducible" claim is withheld |

No lock file or reproducibility claim is included in v0.4.0.
