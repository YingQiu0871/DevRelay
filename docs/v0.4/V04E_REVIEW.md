# DevRelay v0.4-E1 — independent review record

Status: **E1 reviewed: two REQUEST CHANGES reports (no P0); P1s remediated;
accepted by the owner on 2026-10-22.**  No v0.4 tag or release is implied.
See [V04E_ACCEPTANCE.md](V04E_ACCEPTANCE.md).

## Findings and disposition

| ID | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| E1-R1 | P1 | Zip entry names used Windows backslashes, which can flatten the tree for strict unzip tools. | Arcnames now use `.as_posix()`; the builder reopens the zip and asserts `devrelay.exe`, README, LICENSE and `_internal/` entries. |
| E1-R2 | P1 | Frozen app had no dist metadata, so a future release could report the stale literal version; smoke output was unchecked. | Added `--copy-metadata devrelay`, checked installed metadata against `--version`, captured and compared `devrelay.exe version` to `devrelay {version}`, and asserted bundled profile/static files.  Web modules are collected explicitly. |
| E1-R3 | P2 | Portable and wheel jobs checked out the tag independently; a moved tag could mix commits. | Windows job records `COMMIT_SHA.txt`; publish downloads it and refuses to continue if it differs from the wheel checkout. |
| E1-R4 | P2 | Final gate checked asset names only; checksum membership/digests were not re-verified. | `SHA256SUMS` now includes the portable zip and is generated from local artifacts; the final gate requires the fourth asset.  A rerun still cannot re-download assets by design, so digest re-verification remains a documented residual. |
| E1-R5 | P2 | No tests covered the Windows job, dependency, checkout ref, artifact path or builder checks. | Added static tests for the Windows job, `needs:`, artifact name/path, publish provenance check, zip path/metadata/payload checks, and action SHA pinning. |
| E1-R6 | P2 | Reproducibility/SBOM: `.[web]` ranges resolve at release time; no lock/SBOM. | Accepted residual; the portable build is version/metadata checked but not byte-reproducible. |
| E1-R7 | P3 | Docs said `SHA256SUMS.txt` and still advertised the installer as immediate. | README/roadmap/project status updated: portable zip is unsigned; `.exe` installer/signing deferred. |
| E1-R8 | P3 | `windows-assets/` was not ignored; a stale test variable and input interpolation existed. | Added to `.gitignore`; removed stale loop variable; version reaches PowerShell through `env:` only. |

## Verified good

- The portable is built only from the release tag, on a Windows runner, with the
  release workflow gated by draft/PyPI/tag checks.
- `publish` depends on `windows-portable`; the artifact is downloaded before
  checksum/attach and the draft is published only after the four-asset check.
- The installer `.exe` is not faked; it is explicitly deferred.
- PyPI/OIDC, `--clobber` upload and draft-before-publish ordering remain intact.

## Remaining gate

E1 is implemented and reviewed; owner acceptance is pending.  The portable build
is unsigned and not byte-reproducible; no installer, code signing, winget/scoop
manifests or auto-update ship.
