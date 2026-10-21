# DevRelay v0.4-B1 — owner acceptance record

Status: **ACCEPTED / CLOSED by the owner on 2026-10-22.**  This is a B1 stage
acceptance, not a v0.4 release; no tag or publication was created.

## Accepted scope

B1 is the static, no-build local WebUI served at `/` and `/ui` by
`devrelay web serve`:

- fragment token → `X-DevRelay-Session` header session; no cookie;
- summary cards, project context, status and recent runs;
- allowlisted configuration form for workflow, budget, review policy, role
  identifiers and bounded runtime limits;
- validate → explicit confirmation → `PUT /api/config` with
  `expected_sha256`;
- endpoint, executable, profile, argv and test-shell-command wiring displayed
  read-only;
- self-only CSP, fixed asset allowlist, package-data assets.

## Evidence

| Item | Value |
| --- | --- |
| Implementation commit | `bab1349` |
| CI | [run 39692792680](https://github.com/YingQiu0871/DevRelay/actions/runs/39692792680) — 8/8 jobs |
| Local suite | 1,317 collected — 1,315 passed + 2 environment skips |
| Reviews | two independent read-only reviews: APPROVE WITH FINDINGS, P0/P1 = 0 |
| Review record | [V04B_REVIEW.md](V04B_REVIEW.md) |
| Live smoke | `/` 200, `/assets/app.js` 200, `/api/status` without session 401 |
| Wheel | static `index.html`, `app.js`, `styles.css` present |

## Limitations carried forward

- OpenCode endpoint, MCP connection credentials and other excluded wiring are
  read-only; B2 adds a separate reviewed wiring surface.
- No project switching (v0.4-D), live log stream or run control (v0.4-C).
- The token is per-process, not single-use.
- A wheel build is verified manually, not as an offline test.
- B1's remaining P3 polish is recorded in [V04B_REVIEW.md](V04B_REVIEW.md).

## Immutability

`v0.3.0` remains the published release.  B1 is unreleased `main` work.
