# DevRelay v0.4-B — Local WebUI Configuration

Status: **B1 + B2 ACCEPTED / CLOSED by the owner on 2026-10-22** — B2 is
recorded in [V04B2_SPEC.md](V04B2_SPEC.md) and
[V04B2_ACCEPTANCE.md](V04B2_ACCEPTANCE.md).  The B1 review is
recorded in [V04B_REVIEW.md](V04B_REVIEW.md) and the acceptance record in
[V04B_ACCEPTANCE.md](V04B_ACCEPTANCE.md).  This is a local, static single-page
UI served by `devrelay web serve`; it is not a hosted service and adds no
frontend build chain.  No v0.4 tag or release is implied.  B2 (separate wiring
API) is the next slice.

## Objective

Give the loopback A1/A2 API a usable browser surface for the **allowlisted**
configuration patch and the accepted read endpoints, without widening the A2
security boundary.

The UI must let a local owner:

1. open the CLI-printed URL and exchange the per-process fragment token for an
   in-memory header session;
2. see the active project, package version, config digest and restart state;
3. edit workflow/budget/review-policy fields, role model/agent identifiers and
   bounded runtime limits;
4. validate the patch, then explicitly confirm and apply it with the current
   `expected_sha256`;
5. see the resulting digest and whether `devrelay web serve` must restart;
6. read runtime status and recent runs.

## Security boundary

- Same loopback bind, Host/Origin validation and body limits as A1.
- Login token is read from the URL **fragment**, then removed with
  `history.replaceState`; it is never placed in a request URL or log.
- `POST /api/session` returns `session_token`; the browser sends
  `X-DevRelay-Session`.  No cookie and no CSRF token exist.
- Session token is kept in tab-scoped `sessionStorage` (memory fallback); it is
  not written to `localStorage`, a cookie, or the DOM.
- HTML uses a CSP with `default-src 'none'`, `script-src 'self'`,
  `style-src 'self'`, `connect-src 'self'`, `form-action 'none'` and
  `frame-ancestors 'none'`.
- Static assets are served from a fixed three-name allowlist.  The
  `/assets/{name}` route accepts one segment but serves only `index.html`,
  `app.js` or `styles.css`; no directory browsing or arbitrary path is
  accepted.
- All dynamic values use `textContent`; the UI does not use `innerHTML`.
- No arbitrary filesystem path, shell command, provider credential, run-control
  action or project switch is exposed.

## Editable vs read-only

Editable through `PUT /api/config` (A2 allowlist):

- `pipeline`, `budget`, non-provider `review` policy, `roles` identifiers,
  `tests.full_regression`/`timeout_seconds`, `codex` limits, `opencode` limits.

Displayed read-only, with an explanation:

- `review.provider`;
- `codex.executable` (basename only);
- `opencode.base_url` / workspace override;
- profiles, arbitrary argv and `tests.targeted`/`tests.full` shell commands.

Editing those wiring fields needs a **separate backend-owned wiring endpoint**
with its own review; it is deliberately not smuggled through A2.

## UI shape

- `GET /` and `/ui`: public static shell (no workspace data).
- `GET /assets/app.js`, `/assets/styles.css`: public fixed assets.
- Login view; summary cards; Configuration and Status & runs tabs.
- Configuration form covers workflow, provider budget, review policy,
  implementer/reviewer role identifiers, and bounded runtime limits.
- Apply flow: `/api/config/validate` → explicit browser confirmation →
  `PUT /api/config` with `X-DevRelay-Confirm: apply`.
- Read-only surfaces use the accepted `/api/status`, `/api/projects`,
  `/api/config` and `/api/runs?limit=8` routes.

## Non-goals

- No project switching or multi-project editor (v0.4-D).
- No OpenCode endpoint/MCP credential editor (needs a separate wiring API).
- No live log stream, pause/interrupt, manual prompt or run-control button
  (v0.4-C).
- No hosted UI, external fonts, telemetry or CDN assets.
- No change to the v0.3.0 pipeline, MCP surface or release workflow.

## Test plan

- 12 offline tests in `tests/test_v04b_ui.py`.
- Public HTML/assets, fixed asset allowlist, CSP and no-cookie headers.
- Wrong Host rejected on UI routes; API auth unchanged.
- `editable_config` contains only allowlisted values and no provider/paths/
  profile/shell-command fields.
- Static assets are package data and survive a wheel build.
- JS syntax checked locally; no browser automation is added to the offline
  suite.
- Full suite after B1: **1,317 collected** (1,315 pass + 2 environment skips on
  this Windows host).

## Acceptance IDs

| ID | Criterion |
| --- | --- |
| B1 | `/` and `/ui` serve the UI without authentication and without workspace data |
| B2 | UI assets are fixed, same-origin, CSP-compatible and package data |
| B3 | Token fragment is removed before exchange; no cookie is set |
| B4 | Session uses `X-DevRelay-Session`; API auth is unchanged |
| B5 | Config form only builds an A2-allowlisted patch |
| B6 | Apply requires validation, confirmation and the current digest |
| B7 | Read-only wiring is displayed without editing or credential exposure |
| B8 | Existing A1/A2 and full-suite tests remain green |
