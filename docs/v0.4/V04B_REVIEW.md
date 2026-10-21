# DevRelay v0.4-B1 — independent review record

Status: **B1 reviewed: APPROVE WITH FINDINGS (P0/P1 = 0); P2 findings
remediated; accepted by the owner on 2026-10-22.**  No v0.4 tag or release is
implied.  See [V04B_ACCEPTANCE.md](V04B_ACCEPTANCE.md).

Two independent read-only reviews were performed against the static UI and the
`editable_document` projection.  Neither found a P0/P1.  The findings below are
recorded with their dispositions.

## Findings and disposition

| ID | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| B-R1 | P2 | The form filled every control with hardcoded defaults and submitted every field, so an apparently untouched Apply could write schema defaults over profile policy. | Fixed: `renderConfig` records a baseline from the actual form values, and `pruneUnchanged` submits only changed leaves.  An untouched form is an explicit no-op. |
| B-R2 | P2 | `editable_document` copied allowlisted lists wholesale and did not screen secret-named nested keys, so a hand-edited policy section could leak through the read projection. | Fixed: lists are recursed, secret-named keys are skipped, secret-shaped strings are omitted, and `roles` is restricted to the four identifier fields instead of a whole-section prefix. |
| B-R3 | P2 | The token was retained in the hidden login input; the form had no `method`, so a JS failure could GET `/?token=...`. | Fixed: the input has no `name`, the form uses `method="post"`, `form-action 'none'` is enforced, and the token is cleared on success/logout/expiry. |
| B-R4 | P2 | The UI/docs called the token "one-time", but the per-process token remains valid until restart. | Copy corrected to **per-process token**; single-use is not claimed.  This is a documentation/semantic correction, not a consumption feature. |
| B-R5 | P2 | B7 tests were partly vacuous: the fixture had no `tests` section, and codex exclusions were not asserted. | Fixed: tests append a `tests` section and assert `tests.targeted`/`full`, `codex.executable`/`args`/`launcher_args`, `review.provider`, profile and OpenCode paths are absent. |
| B-R6 | P3 | `decodeURIComponent(location.hash)` could throw before `history.replaceState`, leaving a fragment. | Fixed: decode errors are caught and the fragment is removed in `finally`. |
| B-R7 | P3 | Validation and submission built the patch twice; an edit during the round-trip could apply a different object. | Fixed: validation receives the exact patch, and a post-validation rebuild must match or the apply is refused. |
| B-R8 | P3 | Missing/symlinked/invalid config projected as `{}` while `write_supported` remained true. | Fixed: `ConfigWriter.available()` (regular existing file) drives `write_supported`; the UI disables the write controls and labels the state `write unavailable`; a missing-config test covers it. |
| B-R9 | P3 | Later 401s could leave the screen in a stale state; a failed post-apply reload could overwrite the success message. | Fixed: 401s route to the login view; post-apply reload failures preserve the success message and report the reload failure. |
| B-R10 | P3 | Test gaps around `/ui`, wrong Origin, session no-cookie, wheel package data and unsafe DOM APIs. | `/ui`, wrong Origin, no-`Set-Cookie`, source package data and DOM API checks were added.  The wheel build was verified manually; an in-suite wheel build is intentionally not added (it would require a build tool/network in the offline matrix). |

## Verified good

- Login token is read from the fragment and removed before exchange; no
  cookie, `localStorage`, console logging or token-bearing request URL.
- Header session only (`X-DevRelay-Session`); UI routes are public only for
  `/`, `/ui`, `/assets/*` and `/healthz`; all API routes keep auth.
- CSP has no `unsafe-inline`/`unsafe-eval`; assets are a fixed allowlist with
  explicit MIME and `nosniff`.
- Dynamic values use `textContent`/DOM text APIs; no `innerHTML`,
  `outerHTML`, `insertAdjacentHTML`, `document.write` or `eval`.
- The UI form's fields are a subset of the A2 allowlist; server-side
  `expected_sha256`, confirmation header and full validation remain the
  authority.
- `editable_document` excludes `review.provider`, `opencode.base_url`/
  `workspace`, `profiles`, `codex.executable`/argv and test shell commands.

## Remaining gate

B1 is implemented and reviewed with findings.  Owner acceptance is pending.
Open items are the richer unavailable-config state and the manual-only wheel
package-data verification.  The UI does not edit endpoint/credential wiring;
that requires a separate reviewed wiring API.
