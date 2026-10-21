# DevRelay v0.4-A — owner acceptance record

Status: **ACCEPTED / CLOSED by the owner on 2026-10-22.**  This is a stage
acceptance, not a release: no v0.4 tag or PyPI/GitHub release was created, and
`v0.3.0` remains the latest published release.

## Accepted scope

- **A1** — loopback-only, authenticated HTTP transport, project registry,
  bounded read endpoints, and `POST /api/config/validate` (no writes).
- **R1** — header-borne browser sessions (`X-DevRelay-Session`) replace the
  original cookie/CSRF design, resolving the localhost cookie-scope finding.
- **A2** — allowlisted `PUT /api/config` patch with digest guard, explicit
  confirmation header, secret scanning, owner-only backup and atomic replace.

A2 is a curated patch, not an unrestricted full-document write.  Execution and
wiring fields (`codex.executable`, `codex.args`, `codex.launcher_args`,
`opencode.base_url`, `opencode.workspace`, `profiles`, `review.provider` and
shell-valued `tests.targeted`/`tests.full`) are not editable through the API.

## Commits

| Commit | Content |
| --- | --- |
| `75197ec` | A1 read-only local HTTP control API |
| `d42772c` | R1 header sessions + A2 allowlisted config write |
| `db77a4b` | A2 re-review hardening (provider exclusion, cross-process lock, `restart_required`, health redaction) |

## Review evidence

- A1 review: **APPROVE WITH FINDINGS**, P0/P1 = 0; R1 resolved.
- A2 first review: **REQUEST CHANGES** (P1 execution/wiring reachability, policy
  scope).
- A2 remediation re-review: **APPROVE WITH FINDINGS**, P0/P1 = 0.
- Remaining P3 notes are recorded in
  [V04A_A2_REVIEW.md](V04A_A2_REVIEW.md): backup accumulation/orphan on write
  failure, symlink check→read TOCTOU, best-effort directory fsync, and a
  best-effort cross-process lock.  None is claimed as solved beyond its
  documented mitigation.

## Verification

- Local full suite, Windows, isolated `TEMP/TMP`: **1,305 collected — 1,303
  passed + 2 environment skips** (POSIX-only test and symlink privilege).
- CI matrix (`test.yml`): **8/8 jobs passed**
  ([run 39686877308](https://github.com/YingQiu0871/DevRelay/actions/runs/39686877308)).
- Live loopback smoke: session exchange returned `X-DevRelay-Session` with no
  `Set-Cookie`; `PUT /api/config` returned `applied: true`,
  `restart_required: true`, and the config digest changed.

## Carry-forward

- v0.4-B: browser WebUI configuration on top of this API.
- v0.4-C: run-control endpoints and incremental run pagination (A1/A2 still
  summarize at most 500 run documents before applying `limit`).
- v0.4-D: multi-project switching.
- Remaining v0.3-E platform gates and v0.2-A/B/C independent acceptance remain
  open, as recorded in [../PROJECT_STATUS.md](../PROJECT_STATUS.md).

## Immutability

`v0.3.0` is unchanged (`tag object c40a2bec…`, commit `f78d46e`).  A1/A2 are
unreleased `main` work; publishing v0.4 requires its own release gate.
