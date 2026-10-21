# DevRelay v0.4-A1 — independent review record

Status: **A1 reviewed; verdict APPROVE WITH FINDINGS.  The one P2 localhost
cookie-scope item was resolved by moving sessions to `X-DevRelay-Session`; A2 is
implemented and awaits its own independent review.**

- Review target: the v0.4-A1 read-only local HTTP control API
  (`src/devrelay/web/`, `src/devrelay/cli_web.py`,
  `tests/test_v04a_web.py`, `docs/v0.4/V04A_SPEC.md`).
- Review scope: auth/session/CSRF, Host/Origin, body bounds, registry/path
  handling, error redaction, read-only guarantee.  No remote publication was
  involved.
- Verdict: no P0/P1 under the declared loopback/API-only threat model; A2
  configuration write was confirmed absent.

## Findings and disposition

| ID | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| R1 | P2 (was gating A2) | Session cookie is host-scoped, not port-scoped; another local web service could receive or overwrite it. | **Resolved:** cookies were removed; `POST /api/session` returns a token for `X-DevRelay-Session`, which no browser attaches automatically.  No CSRF token is needed.  The historical item is closed in `docs/BACKLOG.md` §12. |
| R2 | P2 | Config view returned `opencode.workspace` and `codex.executable` verbatim, potentially disclosing paths outside the registered root or credential-bearing wrapper paths. | Fixed: config view exposes only `workspace_override` and the executable basename; arbitrary `args`/`launcher_args` remain omitted. |
| R3 | P2 | Malformed Host/Origin (for example `[::1`) raised an uncaught `ValueError` and produced a 500 before auth. | Fixed: `urlsplit` failures are converted to `invalid_host` (400) or `origin_rejected` (403); regression tests added. |
| R4 | P2/P3 | The body cap checked after appending a chunk; a single oversized ASGI event was buffered. | Reduced: the chunk is checked before append.  Early 413/415 responses still rely on the server to drain the unread body; documented as a server-level boundary. |
| R5 | P3 | `/api/runs` loads and summarizes up to 500 runs before slicing to `limit`. | Recorded; v0.4-C pagination/caching can address it.  The 500-run hard cap fails closed. |
| R6 | P3 | Startup could write `projects.json` before the read service was constructed. | Fixed: token and service construction precede the registry's idempotent write. |
| R7 | P3 | CLI bound the socket before workspace/token/config validation; `SO_REUSEADDR` allowed port sharing on Windows. | Fixed: host, workspace and token shape are validated before bind; `SO_EXCLUSIVEADDRUSE` is used where available.  A later service/registry failure closes the socket before serving. |
| R8 | P3 | The 405 handler hardcoded an inaccurate `Allow` header. | Fixed: the generic 405 response no longer claims specific methods. |
| R9 | P3 | WebSocket scopes bypassed auth middleware (latent; no WS route existed). | Fixed: WebSocket scopes are closed with code 1008 before any future route can inherit an unauthenticated handshake. |
| R10 | P3 | Spec/test drift: counts, `invalid_run_id`, `/healthz` shape, and implied traversal/body coverage. | Fixed in `V04A_SPEC.md`; no API accepts a filesystem path, the registry rejects relative/uninitialized paths, and the body-limit test covers the 64 KiB boundary. |

## Remaining gate

`R1` is resolved by the header-session change.  A1's other findings remain as
recorded above (R2–R4 and R6–R10 fixed; R5 carried to v0.4-C).  A2 is implemented
and now needs its own independent review before acceptance; it is not covered by
this A1 review.
