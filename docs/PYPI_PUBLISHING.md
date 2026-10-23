# Publishing DevRelay to PyPI

DevRelay uses **PyPI Trusted Publishing** through GitHub Actions OIDC.
No long-lived PyPI API token is stored in GitHub (and none is required).

Publisher identity is matched by PyPI on three values:

| Field | Value |
| --- | --- |
| PyPI project name | `devrelay` |
| GitHub owner | `YingQiu0871` |
| Repository name | `DevRelay` |
| Workflow name | `release.yml` |
| Environment name | `pypi` |

`release.yml` is the workflow **file name only** (not a path); PyPI does not
accept `Release.yml`, `.github/workflows/release.yml`, or the workflow's
`name:` value here.

## First publication (one-time account setup, done by the maintainer)

1. Log in to <https://pypi.org>.
2. Open *Account settings → Publishing* (pending trusted publishers) and choose
   **Add a new pending publisher**.
3. Project name: `devrelay`
4. Owner: `YingQiu0871`
5. Repository name: `DevRelay`
6. Workflow name: `release.yml`
7. Environment name: `pypi`
8. Add the pending publisher.

A **pending publisher does not reserve the project name** on PyPI. Create it
and trigger the publication promptly.

This setup was made before the first release and is kept here as the record of
how the trusted publisher is registered; it does not have to be repeated for
later releases.

## Triggering a publication

Publishing is **manual**: the `release` workflow runs only on `workflow_dispatch`
(there is no `push` or `pull_request` trigger), and its job is skipped unless the
`confirm` input is exactly `PUBLISH`.

### Before dispatching: the draft Release

The workflow **finishes** a GitHub Release that already exists as a **draft** and
is not marked prerelease; an already published Release or a prerelease is
refused. Create the draft first (its tag must be reachable from `origin/main`; the
workflow checks that with `git merge-base --is-ancestor`):

```bash
gh release create v0.4.0 --draft --title "devrelay v0.4.0" --notes-file <notes>
```

The draft is what makes the ordering checkable: the wheel, the sdist, the
portable Windows zip, the CycloneDX SBOM and `SHA256SUMS` are attached to it
before PyPI sees the upload, and it is flipped to a published Release only once
all five assets are present.  A separate Windows runner builds the portable zip
and SBOM from the tag; the publication job cannot start until that job succeeds.
(v0.4.0 predates the SBOM and has four assets; the next release requires five.)

### Dispatch it by hand

From the repository's *Actions* tab, select the `release` workflow, choose
**Run workflow**, and fill in the tag (for example `v0.4.0`) and `confirm` set to
`PUBLISH`. Or from a checkout:

```bash
gh workflow run release.yml -f tag=v0.4.0 -f confirm=PUBLISH
gh run watch
```

Without `confirm=PUBLISH` nothing is executed.

### What the workflow does, in order

1. **Tag shape** - the tag must match `^v[0-9]+\.[0-9]+\.[0-9]+$`; branch names
   or tags such as `v0.3` or `0.3.0` fail the run immediately.
2. **Checkout** - the release tag itself is checked out, with full history.
3. **Tag vs packaged version** - `pyproject.toml` is read at that tag and the tag
   must be exactly `v<version>` (so `v0.4.0` for the current tree).
4. **Ancestry** - `git merge-base --is-ancestor` must show the tag commit is
   reachable from `origin/main`; an unmerged tag is refused.
5. **Release state** - `gh release view` must report `isDraft=true` and
   `isPrerelease=false`.
6. **PyPI probe** - the workflow asks PyPI whether this version already has its
   files; see *Idempotent reruns* below.
7. **Build from source** - `python -m build --outdir dist` at the tag, into a
   clean `dist/`, with `build==1.6.1` and `twine==7.0.0` installed in CI. The
   build tools are CI-only: they are not project dependencies. The distributions
   are built from the tag's own source, not taken from an existing Release.
8. **Windows portable + SBOM** - a Windows runner builds the wheel at the tag,
   runs PyInstaller 6.15.0 (onedir), executes `devrelay.exe version`, generates
   the CycloneDX runtime SBOM, and uploads
   `DevRelay-Portable-Windows-x64.zip` + `DevRelay-SBOM.cdx.json` as the
   `windows-portable` artifact.
9. **Artifact set and checksums** - exactly one wheel and one sdist, both
   containing `devrelay/profiles/default.yaml`, plus the portable zip and SBOM;
   `release-assets/SHA256SUMS` covers all four files.
10. **`twine check dist/*.whl dist/*.tar.gz`** - metadata validation of exactly
    those two files.
11. **Attach to the draft** - `gh release upload ... --clobber` for the wheel, the
    sdist, `release-assets/SHA256SUMS`, the portable zip and the SBOM.
12. **Upload to PyPI** - `pypa/gh-action-pypi-publish` with `packages-dir: dist/`
    and `attestations: true`, authenticating with OIDC (`id-token: write`) in the
    `pypi` environment; no stored credentials are involved.
13. **Finish the Release** - the last step re-reads the draft's assets and
    requires `devrelay-<version>-py3-none-any.whl`, `devrelay-<version>.tar.gz`,
    `SHA256SUMS`, `DevRelay-Portable-Windows-x64.zip` and
    `DevRelay-SBOM.cdx.json`; only then does it run
    `gh release edit "$TAG" --draft=false`. A missing asset fails the run and
    leaves the Release a draft.

Two dispatches for the same tag are serialized by a job-level concurrency group
(`release-<tag>`, cancellation disabled), so a second run observes the first
one's result instead of racing it.

### Idempotent reruns

Before anything is built, step 6 asks PyPI for
`https://pypi.org/pypi/devrelay/<version>/json` and decides from
`urls[].filename` - not from the HTTP status alone:

- **404** - the version is not on PyPI: build, attach and upload normally.
- **200, one wheel and one sdist** - the version is already published: the
  Windows build, checksum, attach and PyPI steps are skipped by design and only
  the final asset gate runs.  The Windows job checks PyPI first, so a rerun no
  longer spends 45 minutes rebuilding an artifact that will be discarded; the
  publish job tolerates the missing artifact and still requires the portable zip
  already attached to the draft.
- **200, partial upload** (wheel without sdist, sdist without wheel, or
  duplicates) - the run **fails** and reports which file names are missing, to be
  uploaded by hand. PyPI files are immutable: the workflow never rebuilds and
  re-uploads them.
- **Any other status, or a 200 whose file list is empty** - the run fails closed.

No secrets are configured in the `pypi` environment or in repository secrets:
Trusted Publishing needs none.

## After publication

- The project page becomes <https://pypi.org/project/devrelay/>.
- Every later release goes through the same workflow: the tag shape, the packaged
  version and the `main` ancestry are validated per release, so nothing is pinned
  to a particular version any more.
- Release actions are pinned to full commit SHAs and target Node.js 24 action
  releases.  The PyPI upload already carries attestations (`attestations:
  true`); the GitHub Release assets do not have separate attestations.

## History

`v0.1.0` and `v0.3.0` were previously published; the `v0.3.0` and `v0.4.0`
publication records are kept in `docs/RELEASE_CHECKLIST.md`.  `v0.4.0` was the
first release with the Windows portable asset. The first version of this guide
and of the workflow belonged to a bootstrap: the workflow accepted **only** the
`v0.1.0` tag, fetched the wheel and the sdist from an existing GitHub Release
instead of building them, and compared them against hard-coded sha256 digests.
That guard no longer exists - the current workflow validates the tag and the
packaged version and builds from source - and this section is the only part of
this document that describes the old behaviour.
