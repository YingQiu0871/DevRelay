# DevRelay release checklist

The publication flow is the tag-driven workflow in
`.github/workflows/release.yml`, described step by step in
`docs/PYPI_PUBLISHING.md`.  The publisher owns every remote action: nothing in
this file claims that a release, tag or push exists until the publisher performs
it.

## v0.3.0 (2026-10-21)

### Verified in this tree

- [x] Version single-sourced: `pyproject.toml` and the
  `src/devrelay/__init__.py` fallback constant both read `0.3.0`, and
  `devrelay version` reports `0.3.0`.  The MCP server banner keeps its own
  `0.3.0-e` identifier; that identifier is not the release version and is
  unchanged by this release.
- [x] Offline test suite: `python -m pytest -q` collects **1,271** tests --
  **1,270 pass + 1 POSIX-only skip on Windows**; on Linux the POSIX-only test
  is not skipped, so the Linux job runs all 1,271 (the CI result is recorded
  under the publisher steps).
- [x] `python -m build` produces `dist/devrelay-0.3.0-py3-none-any.whl` and
  `dist/devrelay-0.3.0.tar.gz`, and `python -m twine check dist/*.whl
  dist/*.tar.gz` passes.
- [x] The sdist ships the packaged policy profiles (`profiles/*.yaml`).
- [x] A fresh virtualenv installed from the built wheel reports `0.3.0` for
  `devrelay version`.
- [x] Release-document freeze is docs-only: no change to `src/`, `tests/`,
  `pyproject.toml` or `.github/`.

### Release scope (disclosed, not claimed)

- v0.2-A (automatic review loop), v0.2-B (project profiles / frozen-policy
  integrity) and v0.2-C (structured Codex runtime) **ship inside 0.3.0** but
  their **independent acceptance is not complete**; their evidence is
  offline / fake-provider only.  They are not separately released v0.2 stages.
- v0.3-A to v0.3-D are accepted internally and closed.
- v0.3-E is the **mandatory fail-closed core only**: `adopt_completed_turn`
  stays **DISABLED**, and the platform proof gate is **partially executed /
  not complete** (G0.1/P7 = PASS, G0.2 = PASS, G0.3/P5 = PASS, G0.4/P4 =
  authoritative FAIL / P4 UNPROVEN, G0.5/P6 = NOT RUN, G1/G2 not run).

### Publisher steps (owner only; not performed by the implementer)

1. Merge the reviewed `release/0.3.0-integrate` branch into `main` (fast-forward
   if `main` has not moved; otherwise a merge commit), and push `main`.  The
   integration docs commit inside that branch changes documentation only; the
   merge itself only brings the release branch's code and docs into `main`.
2. Wait for the CI workflow to be green on that commit.
3. Create the annotated tag `v0.3.0` on `main` and push it.
4. Create a **draft** GitHub Release for the `v0.3.0` tag, without assets.
5. Dispatch the `release` workflow by hand with `tag = v0.3.0` and
   `confirm = PUBLISH`.
6. Verify the outcome: PyPI serves `devrelay 0.3.0` (wheel and sdist) and the
   GitHub Release is no longer a draft and carries the three assets.  Record the
   `test.yml` run URL, the tag, the draft-Release state and the PyPI file list in
   *Release evidence* below.

### Release evidence (fill in when publishing)

- Release commit:
- Tag:
- `test.yml` run:
- `release.yml` run:
- PyPI files:
- Install verification (`devrelay version`):
- GitHub Release (draft=false):

## v0.1.0 (historical)

Completed for the v0.1.0 candidate (commit and local tag recorded at the
bottom). Nothing in this section claims that a remote release exists.

**Superseded:** v0.1.0 was published manually; the v0.3.0 flow above is
tag-driven, and the manual "create the GitHub Release" / "optional PyPI upload"
steps below are kept only as history.

### Completed in this repository

- [x] Unit / integration tests (`python -m pytest` - 149 passed)
- [x] Independent release audit (findings AUD-01 ... AUD-11 recorded and graded)
- [x] Audit remediation (AUD-01 ... AUD-05 fixed with regression tests)
- [x] Closure audit (AUD-01 ... AUD-05 re-verified CLOSED, no new P0/P1/P2)
- [x] Real Codex CLI smoke test (exactly one model invocation, PASS)
- [x] Dirty-workspace smoke (pre-existing modified tracked file + untracked file)
- [x] Task-relative delta verified against a real dirty workspace
- [x] Git policy guard verified (no commit / stage / branch / tag mutation)
- [x] `python -m build` (wheel + sdist generated)
- [x] Fresh virtualenv install from the built wheel
- [x] Credential / secret scan of the tracked tree and build artifacts
- [x] README reviewed for release accuracy
- [x] CHANGELOG.md written
- [x] Version single-sourced from `pyproject.toml` (`importlib.metadata`)

### Remaining steps for the publisher (historical, done for v0.1.0)

- [x] Create the remote GitHub repository
- [x] `git push` the release commit to `main`
- [x] `git push` the local annotated tag `v0.1.0`
- [x] Create the GitHub Release from the `v0.1.0` tag (paste CHANGELOG section)
- [x] Publish to PyPI (`python -m build` then upload `dist/*`)

### Release evidence

- DevRelay commit: `c4053af` (RC) + release-preparation commit (see `git log`)
- Local tag: `v0.1.0` (annotated)
- Real Codex smoke: 1 invocation, exit 0, sandbox `workspace-write`,
  policy violations: 0
- Build artifacts: `dist/devrelay-0.1.0-py3-none-any.whl`,
  `dist/devrelay-0.1.0.tar.gz`
