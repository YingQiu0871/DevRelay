# DevRelay v0.4.0 — release notes

Status: **PUBLISHED 2026-10-22.**  Tag `v0.4.0` peels to
`c3a54162547cb810e454c498ee05f8eac33c99ae`; PyPI and the GitHub Release are
public.  Evidence is recorded in [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md).

## Highlights

v0.4 adds a local, auditable Web control plane on top of the accepted v0.3
orchestration core:

- **A — Local HTTP API / config write**: loopback-only Starlette/uvicorn,
  bearer + `X-DevRelay-Session` auth, Host/Origin validation, bounded bodies,
  digest/confirmation/backup/atomic config writes, and wiring edits limited to
  a loopback OpenCode base URL.
- **B — WebUI**: no-build static UI with fragment-token login, configuration
  form, read-only wiring/MCP/credential-name display, status and recent runs.
- **C — Run/task control plane**:
  - read-only run/task artifact dashboards (C1/C2a);
  - `decide` and role-scoped `interrupt` (C2b);
  - one bounded manual prompt and normalized message polling (C2c).
- **D1 — Project/session management**: registered-project activation and a
  run-recorded session inventory.
- **E1 — Packaging**: unsigned PyInstaller portable Windows x64 zip built from
  the release tag, checksummed, attached to the draft and required before
  publication.  The `.exe` installer is explicitly deferred.

Pause is **not** implemented: the accepted state machine has no pause state;
interrupt is an abort, not a pause.

## Install / upgrade

Published artifacts:

- PyPI: `python -m pip install devrelay==0.4.0`
- GitHub Release: wheel, sdist, `SHA256SUMS`,
  `DevRelay-Portable-Windows-x64.zip`

The portable zip is unsigned.  Extract it as a whole and verify `SHA256SUMS`
before running `devrelay.exe`; it does not install a service or modify PATH.

## Security notes

- WebUI binds loopback only; sessions ride `X-DevRelay-Session`, not cookies.
- Config/wiring writes require `X-DevRelay-Confirm: apply`, a current digest
  where applicable, secret scanning, a cross-process lock and atomic replace.
- Run decision/interrupt/prompt require explicit confirmation; roles/session
  ids come from the run, never from the client.
- Task text, review evidence and provider messages are bounded/redacted; no
  token/cost values or raw provider bodies are exposed.
- The portable build is unsigned; code signing remains deferred.

## Verification

- Full offline suite: **1,345 collected — 1,343 passed + 2 environment skips**
  on Windows; CI `test.yml` 8/8 on commit `c3a5416`.
- Release workflow tests: tag/PyPI/draft gates, portable job, four-asset gate,
  provenance and SHA pins.
- Release workflow
  [39858586636](https://github.com/YingQiu0871/DevRelay/actions/runs/39858586636):
  both jobs succeeded; the Windows runner built the portable zip and the publish
  job verified its commit provenance.
- Downloaded-asset verification: `SHA256SUMS` matched all three artifacts;
  extracted `devrelay.exe version` reported `devrelay 0.4.0`; a fresh venv
  installed the published wheel and reported `0.4.0`.
- The Windows runner/portable job has now run against the real v0.4 tag.

## Known limitations

- No pause; no WebSocket/SSE live stream (normalized polling only).
- No OpenCode session switching/ownership transfer.
- Active project selection is in-memory and lost on restart.
- Manual-prompt pending marker is process-local; the CLI can still start turns.
- Portable build is not byte-reproducible; no SBOM/lock is bundled.
- No `.exe` installer, code signing, winget/scoop manifest or auto-update.
- Actions still emit Node.js 20 deprecation warnings; bumping the pinned action
  SHAs is a post-release hardening item.
- The release workflow/portable job succeeded on the first real v0.4 tag; a
  future failure must still leave the Release as a draft and be fixed/re-run.

## Publication evidence

See `docs/RELEASE_CHECKLIST.md` § v0.4.0.  The owner created the annotated tag,
draft Release and dispatched `release.yml` with `tag=v0.4.0` and
`confirm=PUBLISH`; the AI recorded and verified the evidence.
