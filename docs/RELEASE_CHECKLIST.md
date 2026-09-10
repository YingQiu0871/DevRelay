# DevRelay v0.1.0 release checklist

Completed for the v0.1.0 candidate (commit and local tag recorded at the
bottom). Nothing in this file claims that a remote release exists.

## Completed in this repository

- [x] Unit / integration tests (`python -m pytest` - 149 passed)
- [x] Independent release audit (findings AUD-01 … AUD-11 recorded and graded)
- [x] Audit remediation (AUD-01 … AUD-05 fixed with regression tests)
- [x] Closure audit (AUD-01 … AUD-05 re-verified CLOSED, no new P0/P1/P2)
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

## Remaining steps for the publisher (not done here)

- [ ] Create the remote GitHub repository
- [ ] `git push` the release commit to `main`
- [ ] `git push` the local annotated tag `v0.1.0`
- [ ] Create the GitHub Release from the `v0.1.0` tag (paste CHANGELOG section)
- [ ] Optional: publish to PyPI (`python -m build` then upload `dist/*`)

## Release evidence (fill in when publishing)

- DevRelay commit: `c4053af` (RC) + release-preparation commit (see `git log`)
- Local tag: `v0.1.0` (annotated, local only - **not pushed**)
- Real Codex smoke: 1 invocation, exit 0, sandbox `workspace-write`,
  policy violations: 0
- Build artifacts: `dist/devrelay-0.1.0-py3-none-any.whl`,
  `dist/devrelay-0.1.0.tar.gz`
