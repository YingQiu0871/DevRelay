# DevRelay v0.4-A — Local HTTP Control API

Status: **A1 IMPLEMENTED + INDEPENDENTLY REVIEWED — APPROVE WITH FINDINGS;
pending owner acceptance.  A2 is design only.**  The review and its dispositions
are recorded in [V04A_REVIEW.md](V04A_REVIEW.md).

This document proposes the transport and security foundation for the v0.4 local
WebUI.  It deliberately does not implement the WebUI, live run control, or a
browser-side configuration editor.  Those are v0.4-B/C.

## Objective (and its hard boundary)

Provide a **loopback-only, authenticated JSON API** over the already accepted
DevRelay read surface:

1. bind to loopback only (never `0.0.0.0` by default);
2. authenticate a local browser session or an explicit bearer client;
3. validate `Host`, `Origin`, `Content-Type`, body size and request shape;
4. serve bounded, redacted project/run/role/status reads;
5. expose a validated project registry instead of accepting filesystem paths
   from the browser;
6. support an optional, explicitly confirmed configuration write in a second
   slice, with backend validation and atomic replacement;
7. never expose arbitrary filesystem browsing, shell execution, provider
   credentials, or an implicit "run anything" action.

v0.4-A is an API, not a UI.  It does not add an autonomous orchestration loop,
does not change the pipeline, and does not make a WebUI decision on behalf of a
human.

## Phased scope

### v0.4-A1 — read-only transport foundation (first review target)

- `devrelay web serve` (loopback uvicorn) and the ASGI app;
- in-memory bearer token, browser session exchange, CSRF;
- Host/Origin/body/content-type validation;
- project registry (`devrelay web project ...`);
- read endpoints: health, status, projects, runs, run detail, roles, redacted
  config view;
- `POST /api/config/validate` (validation only, no write);
- no mutation endpoint.

### v0.4-A2 — backend-owned configuration write (second review target)

- `PUT /api/config` with optimistic concurrency and an explicit confirmation
  header;
- full-document validation through the existing config model;
- atomic replacement, previous-file backup, comments not preserved (documented);
- no secrets in the submitted document;
- still no run-control endpoint.

A1 must be reviewed and merged before A2 is implemented.  The roadmap's
"backend-owned config mutation" is satisfied by A2; A1 establishes the security
boundary first.

### A1 implementation in this tree

- `src/devrelay/web/app.py` — ASGI routes, security middleware, bounded JSON
  parsing and the stable error envelope;
- `src/devrelay/web/auth.py` — token/session/CSRF, Host and Origin checks;
- `src/devrelay/web/registry.py` — explicit project registry;
- `src/devrelay/web/service.py` — bounded read adapter over
  `McpToolSurface`/`OrchestrationService`;
- `src/devrelay/web/workspace.py` — fail-closed workspace resolution;
- `src/devrelay/cli_web.py` — `devrelay web serve` and
  `devrelay web project add/list/remove`;
- `tests/test_v04a_web.py` — 24 offline tests covering the route matrix,
  session/CSRF/Host/Origin/body limits, registry, redaction and CLI wiring.

The live smoke on 2026-10-21 bound `127.0.0.1:0`, served `/healthz` with HTTP
200, and returned HTTP 401 for `/api/status` without a session.  The full
offline suite now collects **1,296** tests (1,295 pass + 1 POSIX-only skip on
Windows).  A2 is not implemented; `/api/config/validate` is read-only.

## Architecture and dependency direction

```text
browser / API client
        │  HTTP on 127.0.0.1
        ▼
devrelay.web.app        ASGI routes, request validation, error envelope
        │
        ├── devrelay.web.auth       token/session/CSRF/Host/Origin
        ├── devrelay.web.registry   explicit project registry
        └── devrelay.web.service    read adapter (redaction + bounds)
                 │
                 ▼
        devrelay.mcp.tools.McpToolSurface  (accepted read/write surface)
        devrelay.orchestration             (run state reads)
        devrelay.artifacts.ArtifactStore   (read-only document access)
```

`devrelay.web` may import `devrelay.mcp`, `devrelay.orchestration` and
`devrelay.opencode`; none of those packages may import `devrelay.web`.  The web
package is an adapter, never a second orchestration engine.

## Process and binding

- Command: `devrelay web serve [--workspace PATH] [--port 8765]`.
- Default host is `127.0.0.1`; `--host` accepts only `127.0.0.1`, `::1` or
  `localhost`, resolved to a loopback address.  Any other value is refused before
  the socket is opened.
- Default port is `8765`; port `0` is allowed for tests and prints the actual
  bound port.
- The workspace must be an initialized DevRelay workspace (`.devrelay/`
  directory and valid wiring), using the same resolution rules as the MCP
  server.  It is registered automatically if absent.  Host, workspace and token
  shape are validated before bind; any later registry/service construction
  failure closes the bound socket before serving.
- Startup prints the login URL `http://127.0.0.1:<port>/#token=<one-time-token>`.
  The token is never written to logs, artifacts, config, or the registry.  A
  non-interactive caller may set `DEVRELAY_WEB_TOKEN`; the token is then not
  printed.
- `SIGINT`/`SIGTERM` shut down uvicorn gracefully; sessions are discarded.

## Authentication and browser session

### Token

- Per-process 256-bit token, URL-safe text, generated with `secrets.token_urlsafe`.
- `DEVRELAY_WEB_TOKEN`, when set, must be at least 32 characters; it replaces the
  generated token and is never echoed.
- Token comparison uses `hmac.compare_digest`.

### Session exchange

- `POST /api/session` body `{"token": "<token>"}`.
- On success: set `devrelay_web_session` cookie:
  `HttpOnly; SameSite=Strict; Path=/api; Max-Age=28800` (no `Secure` because the
  service is HTTP on loopback; `Secure` would break the local flow).
- Response: `{"ok": true, "data": {"csrf": "<token>", "expires_in": 28800}}`.
- Sessions are held in memory (maximum 8); 8-hour absolute TTL and 30-minute
  idle TTL.  A restart invalidates all sessions.
- `GET /api/session` returns the CSRF token for a valid cookie.
- `DELETE /api/session` clears the cookie and server-side session.
- `Authorization: Bearer <token>` is accepted for non-browser clients.  Bearer
  requests with no cookie do not need CSRF (a cross-origin page cannot set the
  header without a preflight, and no CORS is granted).

### CSRF

- Any state-changing request authenticated by the session cookie must carry
  `X-DevRelay-CSRF` matching the session's CSRF token.
- Bearer-authenticated requests may omit it.
- An invalid/missing CSRF token is `403 csrf_required`; it never reaches the
  service layer.

## Request validation

- `Host` must be `127.0.0.1:<port>`, `localhost:<port>` or `[::1]:<port>` with
  the actual bound port.  Anything else is `400 invalid_host` (DNS-rebinding
  defence).
- No CORS headers are emitted.  `OPTIONS` is `405 method_not_allowed`.
- If `Origin` is present, it must be one of the same three loopback origins with
  the bound port; otherwise `403 origin_rejected`.
- State-changing requests require `Content-Type: application/json` and valid
  UTF-8 JSON; `415 unsupported_media_type` otherwise.
- Body limit: 64 KiB.  `Content-Length` over the limit or a streamed body that
  exceeds it is `413 body_too_large`; never truncated-and-parsed.
- Unknown JSON fields are rejected by pydantic models (`extra="forbid"`).
- Every request gets an opaque `request_id`; responses and logs carry it.
- Request logs contain method, route template, status, duration and request id
  only — never headers, query strings, bodies, tokens or provider output.

## Error envelope

All errors use the same stable shape:

```json
{
  "schema_version": 1,
  "ok": false,
  "error": {"code": "csrf_required", "message": "CSRF token required"},
  "request_id": "req_..."
}
```

Messages are bounded and redacted; no traceback, filesystem path outside the
registered project, token or provider body appears.  Success responses use
`{"schema_version": 1, "ok": true, "data": ..., "request_id": "..."}`.

## Project registry

- File: `.devrelay/web/projects.json`, schema version 1, atomic replace.
- `devrelay web project add <absolute-path> [--label TEXT]`:
  resolves strictly, requires a directory with `.devrelay/`, derives a stable
  `prj_<12 hex>` id from the canonical root, and refuses duplicate roots.
- `devrelay web project list` / `remove <id>`: listing and unregistering only;
  removing never deletes project files.
- The API accepts only project ids.  It never accepts a path from the browser and
  never walks a directory tree.
- The serving workspace is registered idempotently at startup.
- Registry writes use a temp file plus `os.replace`; permissions are best-effort
  owner-only.

## Read API (A1)

All `/api/*` routes except `/healthz` require authentication.  `GET /healthz`
returns a liveness envelope (`ok`, `schema_version`, `request_id`) and no
workspace, configuration or provider details.

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/healthz` | unauthenticated liveness, no data |
| POST | `/api/session` | exchange token for session + CSRF |
| GET | `/api/session` | current session/CSRF |
| DELETE | `/api/session` | clear session |
| GET | `/api/health` | authenticated version/workspace id |
| GET | `/api/status` | bounded `devrelay_status` read |
| GET | `/api/projects` | registered projects |
| GET | `/api/runs?limit=20` | bounded run summaries |
| GET | `/api/runs/{run_id}` | one run's summary/attempts |
| GET | `/api/roles` | role/model routes, no secrets |
| GET | `/api/config` | redacted effective config |
| POST | `/api/config/validate` | validate a proposed document, no write |

`run_id` must match the existing `DR-<32 hex>` grammar; project ids must match
`prj_<12 hex>`.  Invalid run ids are `400 invalid_run_id` before any store
access.
Responses reuse the existing accepted read surfaces; no raw provider body,
prompt text, token, absolute path outside the registered root, or unbounded
stdout is returned.  List limits are bounded (maximum 100) and truncation is
reported explicitly.

## Configuration write (A2, proposed)

- `PUT /api/config` body:
  `{"expected_sha256": "<current file digest>", "config": { ...full document... },
    "confirm": "apply"}`.
- Authenticated session + CSRF (or bearer) and
  `X-DevRelay-Confirm: apply` are required.
- The document is parsed with `WorkspaceFile`/`DevRelayConfig`; unknown keys,
  secret-looking keys (`token`, `password`, `api_key`, `secret`) and
  provider-credential values are rejected.
- `expected_sha256` must match the current `.devrelay/config.yaml`; otherwise
  `409 config_changed`.
- Write is atomic (`temp` + `os.replace`), after saving the previous file as
  `.devrelay/config.yaml.bak-<timestamp>`; comments are not preserved and this is
  documented in the response.
- The write never changes a running task's frozen policy snapshot.
- No file path is accepted in the body; the target is always the registered
  workspace's `.devrelay/config.yaml`.

## Dependencies

- Prefer the already available ASGI stack: `starlette` and `uvicorn` are
  transitive dependencies of the optional `mcp` extra.  The implementation adds
  `web = ["starlette>=0.37,<2", "uvicorn>=0.30,<1"]` and includes both in `dev`
  so the test suite is deterministic.
- `devrelay web serve` fails with `web_dependency_missing` and an install hint
  when the extra is absent; the core CLI remains installable without it.
- No new frontend build chain is introduced in v0.4-A.

## Test plan (offline)

- Unit: constant-time token compare, session expiry/idle expiry, CSRF, Host,
  Origin, content type, 64 KiB body boundary, unknown fields, id grammars.
- 24 ASGI tests via Starlette `TestClient`; no real socket for the route matrix.
- Registry tests: absolute/relative paths, missing `.devrelay`, duplicate root,
  atomic write, path traversal attempts, no directory walking.
- Redaction tests: token, provider secret and workspace path never appear in
  unauthenticated responses; config view is explicitly read-only.
- Live binding: exercised manually on `127.0.0.1:0`; the non-loopback CLI refusal
  is automated.  A socket-level test is intentionally not in the offline suite
  to avoid a thread/port race on the Windows CI runner.
- Existing 1,296 offline tests (1,295 pass + 1 POSIX-only skip on Windows)
  remain green.

## Acceptance IDs

| ID | Criterion |
| --- | --- |
| A1 | Default bind is loopback; non-loopback host is refused |
| A2 | Unauthenticated `/api/*` is `401`; `/healthz` leaks no workspace data |
| A3 | Browser token exchange sets HttpOnly/SameSite=Strict session cookie |
| A4 | Session cookie mutations require the matching CSRF header |
| A5 | Bearer clients work without CSRF but never receive CORS permission |
| A6 | Wrong `Host` and wrong `Origin` are refused |
| A7 | Non-JSON, unknown-field and oversized bodies fail closed |
| A8 | Projects are exposed by registry id; no API accepts a filesystem path or browses directories |
| A9 | Read responses are bounded and contain no token/prompt/secret |
| A10 | `POST /api/config/validate` never writes; A2 writes atomically with digest guard |
| A11 | Restart invalidates sessions; token is never logged or written |
| A12 | Missing `web` extra produces an actionable CLI error |
| A13 | Live loopback smoke and the full existing suite pass (manual smoke recorded above; suite green) |

## Known A1 limitation (recorded before A2)

The browser session cookie is **host-scoped, not port-scoped**: a cookie set for
`127.0.0.1` or `localhost` is sent to every port on that host.  A malicious or
compromised local web service could therefore receive it (or overwrite it) if
the user visits that service.  A1 is an API-only slice with no frontend and the
cookie is restricted to `Path=/api`, but this is a real local-origin limitation.
Before the browser UI ships, A2 must choose a header-borne session or an
unguessable per-instance loopback host.  This is recorded in
[BACKLOG.md](../BACKLOG.md) and is **not** claimed as solved by A1.

A1 also summarizes up to 500 run documents before applying the requested list
limit; the cap fails closed, but incremental pagination belongs to v0.4-C.

## Explicit non-goals

- No HTML/JS frontend, no WebSocket/live log stream (v0.4-B/C).
- No run start/pause/interrupt/decide endpoint (v0.4-C).
- No multi-project switching UI (v0.4-D).
- No Windows installer (v0.4-E).
- No arbitrary shell, filesystem browser, provider proxy, or secret storage.
- No change to the v0.3.0 pipeline, MCP surface, or release workflow.

## Resolved design decisions

1. **Optional `web` extra (Starlette/uvicorn)** — accepted and implemented; the
   core CLI still runs without it.
2. **A1 read-only, A2 written configuration behind a separate review gate** —
   accepted; no write endpoint exists in A1.
3. **One-time fragment login URL, no persisted token file** — accepted; the
   token is per-process or supplied by `DEVRELAY_WEB_TOKEN`.

## Review focus for A1

- Does the middleware reject every request before route handling when `Host`,
  `Origin`, bearer token, session cookie or CSRF is invalid?
- Can any endpoint accept a path, browse a directory, or return a token/secret?
- Is the bounded-body path free of an unbounded buffering window?
- Is the CLI's loopback validation performed before any socket bind?
- A2 (`PUT /api/config`) is deliberately absent; validate that no code path
  writes `.devrelay/config.yaml`.
