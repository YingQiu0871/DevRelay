# Reproducibility proof — 2026-10-24 (same-environment)

Status: **SAME-ENVIRONMENT DOUBLE BUILD PASS.**  This is narrower than a release
reproducibility claim: the release job uses Windows/Python 3.13, while this proof
uses the locally available Windows/Python 3.14.6 environment and a proof-only
lock file.

## Environment

| Item | Value |
| --- | --- |
| OS | Microsoft Windows 11 Professional, 10.0.26300 |
| Python | 3.14.6 (MSC v.1944 64-bit) |
| PyInstaller | 6.15.0 |
| `SOURCE_DATE_EPOCH` | `1792713600` |
| Lock | `requirements/portable-win-py314.lock` |
| Lock SHA-256 | `84c93c4169258859b453bc9090a4044807bf5f163c4968bb2f4998a48daee5fa` |
| Source commit | `9b0d419e4ada9e127516909b0d0eb0df45eaf8a5` |

## Commands

```powershell
$env:SOURCE_DATE_EPOCH = "1792713600"
python scripts/build_portable.py --version 0.4.0 `
  --dist dist --output build-a --lock requirements/portable-win-py314.lock
python scripts/build_portable.py --version 0.4.0 `
  --dist dist --output build-b --lock requirements/portable-win-py314.lock
python scripts/compare_builds.py build-a build-b
```

## Result

`compare_builds.py` reported **REPRODUCIBILITY PASS: 2 artifacts match**.

| Artifact | SHA-256 (both builds) |
| --- | --- |
| `DevRelay-Portable-Windows-x64.zip` | `50ffcedbc484554c76972ac222cb910eb669c2df35b9205b1018b71efc5608b4` |
| `DevRelay-SBOM.cdx.json` | `0c4eee19cd63d7897e64d98612965a54b1710535eea8023924483a33bf3a4385` |

Normalization added for this proof:

- zip entries sorted, fixed 1980 timestamps/permissions;
- PyInstaller `base_library.zip` members reordered/deterministically rewritten;
- SBOM timestamp fixed by `SOURCE_DATE_EPOCH`;
- exact-version lock preflight (`--lock`) rejects installed-version drift.

## What this does not prove

- The Windows release job (Python 3.13) is not this environment; its lock is not
  yet wired into the release workflow.
- The lock has exact versions but no hashes/wheelhouse yet.
- A different machine/Python/PyInstaller version may produce different hashes.
- The released v0.4.0 portable was built before these normalizations and is not
  claimed reproducible.

Therefore the project still says **"SBOM, not reproducibly built"** for released
artifacts.  Turning this into a release claim requires a Python 3.13 build
environment, hash-pinned wheelhouse and a second clean build in CI/release.

A Windows/Python 3.13 release constraint file now exists
(`requirements/portable-win-py313.lock`) and is wired into the release job, but
it has not yet been used for a Python 3.13 double build.  It is a version lock,
not a hash lock.
