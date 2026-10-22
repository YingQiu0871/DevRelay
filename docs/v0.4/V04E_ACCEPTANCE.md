# DevRelay v0.4-E1 — owner acceptance record

Status: **ACCEPTED / CLOSED by the owner on 2026-10-22.**  This is an E1 stage
acceptance, not a v0.4 release; no tag or publication was created.

## Accepted scope

E1 adds:

- `DevRelay-Portable-Windows-x64.zip` built on Windows from the release tag with
  PyInstaller onedir;
- metadata/version assertion, bundled profile/static payload checks, POSIX zip
  entry names and reopened-zip layout validation;
- a `windows-portable` release job with commit-SHA provenance, artifact upload,
  publish-side provenance verification, checksum inclusion and draft attachment;
- a final four-asset gate (wheel, sdist, SHA256SUMS, portable zip);
- full-SHA action pins and the v0.4 hardening record.

**The signed `.exe` installer, code signing, winget/scoop manifests and
auto-update are explicitly deferred; no fake installer is shipped.**

## Evidence

| Item | Value |
| --- | --- |
| Implementation commit | `149b282` |
| CI | [run 39850444246](https://github.com/YingQiu0871/DevRelay/actions/runs/39850444246) — 8/8 jobs |
| Local suite | 1,345 collected — 1,343 passed + 2 environment skips |
| Local portable smoke | built zip; `devrelay.exe version` matched 0.3.0; profile/static present |
| Review | two independent read-only reports: REQUEST CHANGES (no P0); P1/P2 items remediated |
| Review record | [V04E_REVIEW.md](V04E_REVIEW.md) |
| Hardening record | [HARDENING_v0.4.md](../HARDENING_v0.4.md) |

## Limitations carried forward

- The release workflow has **not** been dispatched against a real v0.4 tag; the
  Windows runner job is statically validated, not exercised in CI.
- The portable build is unsigned and not byte-reproducible; `.[web]` is resolved
  at release time and no SBOM/lock is bundled.
- The final gate checks asset names and checksum membership, but a skip-rebuild
  rerun cannot re-download assets by design; missing/wrong assets require manual
  restoration.
- The `.exe` installer, signing and package-manager manifests remain deferred.
- Portable `devrelay.exe` requires Windows 10/11 x64; it is not a service and
  does not modify PATH.

## Immutability

`v0.3.0` remains the published release.  E1 is unreleased `main` work.
