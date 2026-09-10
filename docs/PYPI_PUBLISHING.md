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

## Triggering the publication (after the pending publisher exists)

From the repository's *Actions* tab, run the `release` workflow manually, or:

```bash
gh workflow run release.yml -f tag=v0.1.0 -f confirm=PUBLISH
gh run watch
```

The workflow:

- runs **only** on manual dispatch with `confirm=PUBLISH` - never on `push` or
  `pull_request`;
- refuses any tag other than `v0.1.0` (v0.1 bootstrap safety guard);
- refuses draft or prerelease GitHub Releases;
- downloads the wheel and sdist from the existing GitHub Release instead of
  rebuilding them, so PyPI receives the exact artifacts that were verified;
- verifies that there is exactly one wheel and one sdist, checks their
  filenames/version, and compares their sha256 against the pinned v0.1.0
  bootstrap digests;
- runs `twine check` before uploading;
- uploads with `pypa/gh-action-pypi-publish` using OIDC (`id-token: write`),
  with `attestations: false` and `packages-dir: dist/`.

No secrets are configured in the `pypi` environment or in repository secrets:
Trusted Publishing needs none.

## After publication

- The project page becomes <https://pypi.org/project/devrelay/>.
- Later releases should generalize the bootstrap guard (tag validation instead
  of the `v0.1.0` pin) and, ideally, replace the pinned digests with a general
  provenance check.
