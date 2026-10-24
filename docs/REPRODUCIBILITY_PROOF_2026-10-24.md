# Reproducibility proof — 2026-10-24

Status: **RELEASE-LOCK DOUBLE BUILD PASS (GitHub Windows / Python 3.13.16), plus a
local 3.14 same-environment check.**  The release lock is exact-version but not
hash-pinned and the proof is one runner image; this is not a cross-runner or
universal claim.

## GitHub Windows / Python 3.13 release lock

| Item | Value |
| --- | --- |
| Workflow | [reproducibility.yml](../.github/workflows/reproducibility.yml) |
| Run | [40134991611](https://github.com/YingQiu0871/DevRelay/actions/runs/40134991611) |
| Commit | `4c25e21250bc9d164b707f1a17f7ce5cfca7131d` |
| Runner | `windows-latest`, CPython 3.13.16 |
| Lock | `requirements/portable-win-py313.lock` |
| `SOURCE_DATE_EPOCH` | `1792713600` |
| Result | `REPRODUCIBILITY PASS: 2 artifacts match` |

| Artifact | SHA-256 (both builds) |
| --- | --- |
| `DevRelay-Portable-Windows-x64.zip` | `af8858fd2e909d077706b123a476b1d4b6902a4490ba022c629178aa3ab1d1ce` |
| `DevRelay-SBOM.cdx.json` | `0c4eee19cd63d7897e64d98612965a54b1710535eea8023924483a33bf3a4385` |

The downloaded Python 3.13 portable was extracted and `devrelay.exe version`
reported `devrelay 0.4.0`.

The release workflow uses the same lock and `--lock` preflight; this run proves
the lock is installable and deterministic on that GitHub runner image.  It does
not yet pin wheel hashes, and a changed runner image remains a residual.

## Local Windows / Python 3.14 same-environment check

The local proof uses a proof-only lock and the locally available Python 3.14.6;
its purpose is to exercise the normalization code outside CI.

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
