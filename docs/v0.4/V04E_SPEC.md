# DevRelay v0.4-E — Packaging & GitHub Release Automation

Status: **E1 ACCEPTED / CLOSED by the owner on 2026-10-22.**  The review is
recorded in [V04E_REVIEW.md](V04E_REVIEW.md) and the acceptance record in
[V04E_ACCEPTANCE.md](V04E_ACCEPTANCE.md).  E1 adds a portable Windows x64 build
to the tag-driven release workflow.

## Scope (E1)

### Portable Windows x64

`DevRelay-Portable-Windows-x64.zip` is built on a Windows runner from the tag's
own source with PyInstaller 6.15.0 (onedir):

- bundles the Python runtime and runtime dependencies, including the `web`
  extra;
- includes `devrelay.exe`, `_internal/`, `README-PORTABLE.txt` and `LICENSE`;
- contains no installer, PATH change, Start Menu entry, service or auto-update;
- is unsigned; users must verify `SHA256SUMS`;
- the build script asserts `devrelay.exe version` equals the requested version
  and that the bundled profile/static payload exists before zipping; the zip
  uses POSIX path separators and is reopened to check required entries.

### Release workflow

The existing tag-driven `release.yml` flow now:

1. builds the portable zip in a separate `windows-portable` job from the tag;
2. makes `publish` depend on that job;
3. downloads the zip into the release job;
4. includes the portable zip in `SHA256SUMS`;
5. attaches wheel, sdist, `SHA256SUMS` and the portable zip to the draft;
6. refuses to publish unless all four assets are present.

The PyPI upload remains the same Trusted Publishing/OIDC flow.  A rerun after
PyPI already has the version still skips rebuilds by design; the final asset
check reports how to restore missing draft assets.

### Not in E1

- `DevRelay-Setup-Windows-x64.exe` installer.  No Inno Setup/NSIS toolchain or
  code-signing certificate is validated in this repository yet; shipping an
  unsigned, untested self-extracting wrapper would be worse than deferring it.
- Code signing/notarization, winget/scoop manifests, auto-update.
- Portable macOS/Linux bundles.

## Security boundary

- The portable build is produced from the checked-out release tag only.
- The release workflow still validates the tag shape, tag↔pyproject version,
  `origin/main` reachability, draft-only Release state and PyPI state.
- No PyPI token or signing secret is added; PyPI uses OIDC.
- The portable zip is attached before the draft is published; asset presence is
  rechecked immediately before publication.
- No shell interpolation of workflow inputs; tag/version reach shells via env.

## Tests

- Release workflow tests assert the portable asset is built, checksummed,
  attached and required by the final gate.
- `scripts/build_portable.py` is a Windows-only build helper; verification runs
  `devrelay.exe version` before zipping.
- Full suite: **1,345 collected** (1,343 pass + 2 environment skips; E1 adds
  static release-window/provenance and portable-builder tests).

## Acceptance IDs

| ID | Criterion |
| --- | --- |
| E1-1 | A Windows portable zip is built from the release tag |
| E1-2 | The zip is included in SHA256SUMS and attached to the draft |
| E1-3 | Publication is refused unless wheel, sdist, SHA256SUMS and portable zip are present |
| E1-4 | Existing tag/PyPI/draft safety gates remain intact |
| E1-5 | Installer `.exe` is explicitly deferred, not faked |
