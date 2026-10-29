# DevRelay release checklist

The publication flow is the tag-driven workflow in
`.github/workflows/release.yml`, described step by step in
`docs/PYPI_PUBLISHING.md`.  The publisher owns every remote action.  For v0.3.0
the publisher completed the steps below on 2026-10-21; the evidence is recorded
here and the release is public.

## v0.5.1 (prepared, not published)

### Verified in this tree

- [x] Version single-sourced at **0.5.1** in `pyproject.toml`, the
  `src/devrelay/__init__.py` fallback and `tests/test_version.py`; the
  `release.yml` dispatch default is `v0.5.1`.
- [x] Full offline suite: **1,387 collected — 1,385 pass + 2 environment skips**
  on this Windows host (Python 3.14.6).
- [x] `python -m build` produced `devrelay-0.5.1-py3-none-any.whl` (331,838
  bytes) and `devrelay-0.5.1.tar.gz` (1,428,785 bytes); `twine check` passed both.
- [x] Release notes: [v0.5/RELEASE_NOTES_v0.5.1.md](v0.5/RELEASE_NOTES_v0.5.1.md).

### Publisher steps (owner authorization required)

1. [ ] Release-preparation commit on `main`; `test.yml` green.
2. [ ] Annotated tag `v0.5.1`, pushed.
3. [ ] **Draft** GitHub Release for `v0.5.1`.
4. [ ] `release.yml` dispatched with `tag=v0.5.1`, `confirm=PUBLISH`.
5. [ ] Five assets attached, Release no longer a draft, PyPI serves 0.5.1, a
   fresh venv installs it.
6. [ ] Evidence recorded here; README/project-status flipped to published.

## v0.5.0 (published 2026-10-29)

### Verified in this tree

- [x] Version single-sourced at **0.5.0** in `pyproject.toml`, the
  `src/devrelay/__init__.py` fallback and `tests/test_version.py`; the
  `release.yml` dispatch default is `v0.5.0`; editable reinstall reports 0.5.0.
- [x] Full offline suite: **1,381 collected — 1,379 pass + 2 environment skips**
  on this Windows host (Python 3.14.6).
- [x] `python -m build` produced `devrelay-0.5.0-py3-none-any.whl` (330,392
  bytes) and `devrelay-0.5.0.tar.gz` (1,415,512 bytes); `twine check` passed
  both; the wheel contains `devrelay/profiles/default.yaml` and the WebUI assets.
- [x] Release notes: [v0.5/RELEASE_NOTES_v0.5.0.md](v0.5/RELEASE_NOTES_v0.5.0.md).

### Publisher steps (completed 2026-10-29, owner-authorized in session)

1. [x] Release-preparation commit `36af6af` on `main`; `test.yml` green.
2. [x] Annotated tag `v0.5.0` on `36af6af`, pushed.
3. [x] **Draft** GitHub Release for `v0.5.0`.
4. [x] `release.yml` dispatched with `tag=v0.5.0`, `confirm=PUBLISH`.
5. [x] Five assets attached, Release no longer a draft, PyPI serves 0.5.0, a
   fresh venv installs it.
6. [x] Evidence recorded here; README/project-status flipped to published.

### Release evidence

- Release commit: `36af6afdb1fb48d1376873aa5605d2f925bb2384`
- Tag: `v0.5.0` (annotated tag object `c3c306d599cf2fcbc8c47fd6b3a994ecec9f590f`,
  peeled commit `36af6af`)
- `test.yml` run: https://github.com/YingQiu0871/DevRelay/actions/runs/40798227385 (8/8)
- `release.yml` run: https://github.com/YingQiu0871/DevRelay/actions/runs/40799180664
  (Build Windows portable: success; Publish to PyPI (OIDC): success)
- PyPI page: https://pypi.org/project/devrelay/0.5.0/
- GitHub Release: https://github.com/YingQiu0871/DevRelay/releases/tag/v0.5.0
- Published at: `2026-10-29T01:16:18Z`; `isDraft=false`, `isPrerelease=false`
- Assets:
  - `devrelay-0.5.0-py3-none-any.whl` (330,684 bytes)
    `sha256:8880df1a858737e092ef2d56e7d3d1cf38c2060006dfe2805143f613d2048491`
  - `devrelay-0.5.0.tar.gz` (1,414,995 bytes)
    `sha256:dfe0b668ef017396f1a320a86403706b058d73d1282e5241815abb667818168a`
  - `DevRelay-Portable-Windows-x64.zip` (19,715,605 bytes)
    `sha256:204c30fd34c80997203e09a7955a48be340680885a0cd0c83ae58d5da122febc`
  - `DevRelay-SBOM.cdx.json` (8,501 bytes)
    `sha256:b689ffd0bd27cb8e867e80520aa12d23d0d9129a079cdbd749dd5f01739b805c`
  - `SHA256SUMS` (375 bytes)
    `sha256:baa60a5be314b8af1c3df9155b692a7dfefa6ba5703e3513db24603084904da7`
- PyPI wheel and sdist digests equal the Release assets.
- Downloaded-asset verification: `SHA256SUMS` matched all four files; extracted
  `devrelay.exe version` reported `devrelay 0.5.0`; a fresh venv installed
  `devrelay==0.5.0` from PyPI and reported `0.5.0`; the SBOM is CycloneDX 1.5 for
  `devrelay 0.5.0` with 23 components.

### Disclosed caveats

- The portable zip is unsigned; no `.exe` installer.
- `adopt_completed_turn` remains disabled; v0.3-E platform gates are not closed.

## v0.4.0 (published 2026-10-22)

### Verified in this tree

- [x] Version single-sourced at **0.4.0** in `pyproject.toml`, the
  `src/devrelay/__init__.py` fallback and `tests/test_version.py`; editable
  reinstall reports `devrelay 0.4.0`.
- [x] Full offline suite: **1,345 collected — 1,343 pass + 2 environment skips**
  on this Windows host.
- [x] `python -m build` produced `devrelay-0.4.0-py3-none-any.whl` and
  `devrelay-0.4.0.tar.gz`; `twine check` passed both.
- [x] Portable local build produced `DevRelay-Portable-Windows-x64.zip`;
  extracted `devrelay.exe version` reported `devrelay 0.4.0`; profile/static
  assertions passed.
- [x] A/B/C/D1/E1 acceptance records are present under `docs/v0.4/`.
- [x] E1 release workflow includes the Windows portable job, four-asset gate,
  provenance check and SHA-pinned actions; release tests pass.
- [x] Release notes: [v0.4/RELEASE_NOTES_v0.4.0.md](v0.4/RELEASE_NOTES_v0.4.0.md).

### Publisher steps (completed 2026-10-22)

1. [x] Reviewed the release-preparation commit and waited for `test.yml` green.
2. [x] Created annotated tag `v0.4.0` on `c3a5416` and pushed it.
3. [x] Created a **draft** GitHub Release for `v0.4.0`.
4. [x] Dispatched `release.yml` with `tag=v0.4.0`, `confirm=PUBLISH`.
5. [x] Verified the Windows portable artifact, wheel, sdist and `SHA256SUMS`
   are attached, the Release is no longer a draft, PyPI serves 0.4.0, and a
   fresh venv installs it.
6. [x] Recorded the release commit, CI run, release run and PyPI digests here;
   flipped README/project-status to published.

### Release evidence

- Release commit: `c3a54162547cb810e454c498ee05f8eac33c99ae`
- Tag: `v0.4.0` (annotated tag object `007528204baa5d232893897fe9d4f1b8717ae009`,
  peeled commit `c3a5416`)
- `test.yml` run: https://github.com/YingQiu0871/DevRelay/actions/runs/39857350094
- `release.yml` run: https://github.com/YingQiu0871/DevRelay/actions/runs/39858586636
- PyPI page: https://pypi.org/project/devrelay/0.4.0/
- GitHub Release: https://github.com/YingQiu0871/DevRelay/releases/tag/v0.4.0
- Published at: `2026-10-22T21:38:24Z`; `isDraft=false`, `isPrerelease=false`
- Assets:
  - `devrelay-0.4.0-py3-none-any.whl` (316,610 bytes)
    `sha256:17e7710ed1614f3c845d85068c675c820f3bf4d4c543dd645ba87155afea16aa`
  - `devrelay-0.4.0.tar.gz` (1,364,176 bytes)
    `sha256:da4fa52ee77b2017a70cc3f58cbd6ecb3696d68bca1f8db2129a9c19931492c2`
  - `DevRelay-Portable-Windows-x64.zip` (19,740,716 bytes)
    `sha256:6c5eb6c47f1b194e84334fba3b0566c2c4725c93c0a5200ccde8e042a759a2dc`
  - `SHA256SUMS` (286 bytes)
    `sha256:4129ca1944a11108da0b5a2fcfe373c0197dea45918939e32cc60b80e2ed9027`
- Downloaded-asset verification: `SHA256SUMS` matched all three files;
  extracted `devrelay.exe version` reported `devrelay 0.4.0`; a fresh venv
  installed the published wheel and reported `0.4.0`.

### Disclosed caveats

- The portable zip is unsigned and not byte-reproducible; no SBOM.
- Pause, session switching, persistent active-project selection and the `.exe`
  installer remain deferred.
- Post-release: actions were bumped to Node.js 24 releases after v0.4.0; the
  next CI run verifies the new pins.
- Post-release: a CycloneDX SBOM generator and a five-asset release gate were
  added for the next release.  v0.4.0 itself has no SBOM asset.
- Post-release: pending manual-prompt markers are now durable under
  `.devrelay/web/manual_prompts.json` with a confirmed recovery endpoint; v0.4.0
  still has the earlier process-local behavior.

## v0.3.0 (2026-10-21)

### Verified in this tree

- [x] Version single-sourced: `pyproject.toml` and the
  `src/devrelay/__init__.py` fallback constant both read `0.3.0`, and
  `devrelay version` reports `0.3.0`.  The MCP server banner keeps its own
  `0.3.0-e` identifier; that identifier is not the release version and is
  unchanged by this release.
- [x] Offline test suite: `python -m pytest -q` collects **1,272** tests.  On
  Windows the structured Codex runtime runs: **1,271 pass + 1 POSIX-only skip**
  (the 8.3 regression test runs where the volume provides short names and
  self-skips where 8.3 is disabled).  On Linux the 35 structured-runtime
  end-to-end tests and the Windows-only 8.3 test are skipped: **1,236 pass +
  36 skips** (the CI result is recorded under the publisher steps).
- [x] `python -m build` produces `dist/devrelay-0.3.0-py3-none-any.whl` and
  `dist/devrelay-0.3.0.tar.gz`, and `python -m twine check dist/*.whl
  dist/*.tar.gz` passes.
- [x] The sdist ships the packaged policy profiles (`profiles/*.yaml`).
- [x] A fresh virtualenv installed from the built wheel reports `0.3.0` for
  `devrelay version`.
- [x] The release-document freeze commit is docs-only: no change to `src/`,
  `tests/`, `pyproject.toml` or `.github/`.  A separate CI-portability fix
  (below) is the only post-freeze source/test change before the tag.

### CI portability fix (2026-10-21)

- [x] OpenCode workspace ownership compares canonical paths
  (`os.path.realpath` + `os.path.normcase`), so a provider's Windows 8.3
  spelling (`RUNNER~1`) matches DevRelay's resolved long path.  The regression
  test uses `GetShortPathNameW` and self-skips where the volume has no short
  names.
- [x] Structured Codex end-to-end tests are marked
  `requires_windows_containment` and skipped on POSIX.  The runtime is
  unchanged: POSIX still fails closed with
  `codex_process_containment_unsupported` and zero provider calls, exactly as
  `docs/v0.2/V02C_SPEC.md` requires.
- [x] The failed `test.yml` run on `9e7192b` produced no tag.  The fixed
  `main` commit `f78d46e` passed `test.yml` before the tag (evidence below).

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

### Publisher steps (completed 2026-10-21)

1. [x] Fast-forwarded `main` to the reviewed release commit and pushed it.
2. [x] Waited for `test.yml` to be green on that commit.
3. [x] Created the annotated tag `v0.3.0` on `main` and pushed it.
4. [x] Created a **draft** GitHub Release for the `v0.3.0` tag.
5. [x] Dispatched the `release` workflow with `tag = v0.3.0` and
   `confirm = PUBLISH`.
6. [x] Verified PyPI serves `devrelay 0.3.0` (wheel and sdist), the GitHub
   Release is no longer a draft and carries the three assets, and a fresh venv
   installs the published wheel.

### Release evidence

- Release commit: `f78d46edc4802870c3af9a98bf91464890971a74`
- Tag: `v0.3.0` (annotated; peeled commit `f78d46e`)
- `test.yml` run: https://github.com/YingQiu0871/DevRelay/actions/runs/39658557766
- `release.yml` run: https://github.com/YingQiu0871/DevRelay/actions/runs/39659859484
- PyPI files:
  - `devrelay-0.3.0-py3-none-any.whl`
    (`sha256:258aef99cb923c303843c54fa26301b4c2e99089028e51e5c4061d1cd680b941`)
  - `devrelay-0.3.0.tar.gz`
    (`sha256:6cd6d75383ab49bfd02444490954fa7d3cee1316ffa30ea249ef94965add52d7`)
- PyPI page: https://pypi.org/project/devrelay/0.3.0/
- Install verification: fresh venv from PyPI reports `devrelay 0.3.0`.
- GitHub Release (draft=false):
  https://github.com/YingQiu0871/DevRelay/releases/tag/v0.3.0
  with the wheel, sdist, and `SHA256SUMS`.

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
