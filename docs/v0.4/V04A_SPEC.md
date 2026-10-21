# DevRelay v0.4-A — Local HTTP Control API

Status: **A1 + A2 ACCEPTED / CLOSED by the owner on 2026-10-22.**  This is a
stage acceptance, not a v0.4 release.  The acceptance record is
[V04A_ACCEPTANCE.md](V04A_ACCEPTANCE.md).
The A1 review and its dispositions are recorded in
[V04A_REVIEW.md](V04A_REVIEW.md); the A1 localhost cookie limitation was
resolved by moving sessions to a header, which is the prerequisite A2 needed.
The A2 review, re-review and remediation are recorded in
[V04A_A2_REVIEW.md](V04A_A2_REVIEW.md); A2 was accepted with the residual P3
notes carried forward.

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
- in-memory bearer token, header-borne browser session exchange;
- Host/Origin/body/content-type validation;
- project registry (`devrelay web project ...`);
- read endpoints: health, status, projects, runs, run detail, roles, redacted
  config view;
- `POST /api/config/validate` (validation only, no write);
- no mutation endpoint.

### v0.4-A2 — backend-owned configuration write (implemented; pending review)

- `PUT /api/config` with optimistic concurrency and an explicit confirmation
  header;
- full-file validation of the merged document through the existing config model;
- atomic replacement, previous-file backup, comments not preserved (documented);
- no secrets in the submitted document;
- still no run-control endpoint.

A1 was reviewed before A2 was implemented.  The roadmap's "backend-owned config
mutation" is satisfied by A2, which is implemented here and pending independent
review; A1 established the transport boundary first.

### A1 implementation in this tree

- `src/devrelay/web/app.py` — ASGI routes, security middleware, bounded JSON
  parsing and the stable error envelope;
- `src/devrelay/web/auth.py` — token/header-session, Host and Origin checks;
- `src/devrelay/web/registry.py` — explicit project registry;
- `src/devrelay/web/config.py` — A2 validation, backup and atomic replacement;
- `src/devrelay/web/service.py` — bounded read adapter and config-write facade;
- `src/devrelay/web/workspace.py` — fail-closed workspace resolution;
- `src/devrelay/cli_web.py` — `devrelay web serve` and
  `devrelay web project add/list/remove`;
- `tests/test_v04a_web.py` — 33 offline tests covering the route matrix,
  header-session/Host/Origin/body limits, registry, redaction, CLI wiring,
  config validation, the editable allowlist and the atomic A2 write.

The live smoke on 2026-10-21 bound `127.0.0.1:0`, served `/healthz` with HTTP
200, and returned HTTP 401 for `/api/status` without a session.  The full
offline suite now collects **1,305** tests (1,303 pass + 2 environment skips on
this Windows host: one POSIX-only test and one symlink-privilege test).

## Architecture and dependency direction

```text
browser / API client
        │  HTTP on 127.0.0.1
        ▼
devrelay.web.app        ASGI routes, request validation, error envelope
        │
        ├── devrelay.web.auth       token/header-session/Host/Origin
        ├── devrelay.web.registry   explicit project registry
        ├── devrelay.web.config     A2 validate/backup/atomic replace
        └── devrelay.web.service    read adapter + config-write facade
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
- On success it returns a **header-borne session token**:
  `{"ok": true, "data": {"session_token": "...", "transport":
  "X-DevRelay-Session", "expires_in": 28800}}`.  No cookie is set.
- The client sends `X-DevRelay-Session: <session_token>` on subsequent requests.
  A header is never attached automatically by a browser, so a cross-origin page
  cannot make the browser replay it and **no CSRF token is needed**.
- Sessions are held in memory (maximum 8); 8-hour absolute TTL and 30-minute
  idle TTL.  A restart invalidates all sessions.
- `GET /api/session` returns the authenticated mode; `DELETE /api/session`
  invalidates the server-side session.
- `Authorization: Bearer <token>` is accepted for non-browser clients; the
  per-process root token can be used directly.

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
  "error": {"code": "unauthorized", "message": "authentication required"},
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

## API endpoints (A1 reads + A2 config write)

All `/api/*` routes except `/healthz` require authentication.  `GET /healthz`
returns a liveness envelope (`ok`, `schema_version`, `request_id`) and no
workspace, configuration or provider details.

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/healthz` | unauthenticated liveness, no data |
| POST | `/api/session` | exchange token for a header session |
| GET | `/api/session` | current authenticated mode |
| DELETE | `/api/session` | clear session |
| GET | `/api/health` | authenticated version/workspace id |
| GET | `/api/status` | bounded `devrelay_status` read |
| GET | `/api/projects` | registered projects |
| GET | `/api/runs?limit=20` | bounded run summaries |
| GET | `/api/runs/{run_id}` | one run's summary/attempts |
| GET | `/api/roles` | role/model routes, no secrets |
| GET | `/api/config` | redacted effective config + `config_sha256` |
| PUT | `/api/config` | A2 curated patch write (see below) |
| POST | `/api/config/validate` | validate a proposed patch, no write |

`run_id` must match the existing `DR-<32 hex>` grammar; project ids must match
`prj_<12 hex>`.  Invalid run ids are `400 invalid_run_id` before any store
access.
Responses reuse the existing accepted read surfaces; no raw provider body,
prompt text, token, absolute path outside the registered root, or unbounded
stdout is returned.  List limits are bounded (maximum 100) and truncation is
reported explicitly.

## Configuration write (A2, implemented; pending review)

- `GET /api/config` includes `config_sha256` (the digest of the current
  `.devrelay/config.yaml`) and `restart_required` (the file no longer matches
  the wiring loaded at process start).
- `PUT /api/config` body:
  `{"expected_sha256": "<current file digest>", "config": { ...curated patch... },
    "confirm": "apply"}`.
- A header-borne session or bearer token **and** `X-DevRelay-Confirm: apply` are
  required; no CSRF token exists.
- The merged document is parsed with `WorkspaceFile`/`DevRelayConfig`; unknown
  keys, secret-looking keys (`token`, `password`, `api_key`, `secret`,
  `credential`) and execution/wiring fields (`codex.executable`,
  `codex.args`, `codex.launcher_args`, `opencode.base_url`,
  `opencode.workspace`, `profiles`, `tests.targeted`, `tests.full`) are
  rejected.
- `expected_sha256` must match the current file; otherwise `409 config_changed`.
- Write is atomic (`temp` + fsync + `os.replace`), after saving the previous file
  as `.devrelay/config.yaml.bak-<timestamp>`; comments are not preserved and the
  response says so.  A `.devrelay/web/config.lock` advisory lock serializes
  writers across processes; a busy lock is `409 config_busy`.
- The write never changes a running task's frozen policy snapshot.  The live
  process keeps its loaded wiring until restart; the file is the source for the
  next start.
- No file path is accepted in the body; the target is always the registered
  workspace's `.devrelay/config.yaml`.
- Response: `old_sha256`, `new_sha256`, `backup_created`, `backup_name`,
  `comments_preserved: false`, `restart_required`, and the write scope.

### Editable allowlist (A2)

A2 is a **curated patch**, not an unrestricted full document.  The submitted
object is merged over the current file; omitted fields are preserved.  Editable
fields are:

- `pipeline`, `budget`, `review`, `scope`, `baseline` and `git` (the hard-false
  git validator still applies);
- `roles.implementer` / `roles.reviewer` identifiers;
- `tests.full_regression` and `tests.timeout_seconds`;
- `codex.prompt_mode`, `timeout_seconds`, `runtime_mode`, `max_result_bytes` and
  `max_capture_bytes`;
- `opencode.default_session`, `agent`, `model`, timeouts, response/message caps.

Explicitly **not editable** through the API: `profiles`, `codex.executable`,
`codex.args`, `codex.launcher_args`, `opencode.base_url`, `opencode.workspace`,
`opencode.allow_unknown_workspace`, and `tests.targeted` / `tests.full` (their
values are shell commands).  These are preserved from the current file and a
request naming them is `422 config_field_not_editable`.  Policy fields that are
editable affect **future** tasks only; a running task's frozen snapshot is never
rewritten.  An empty patch is a no-op, and a symlinked config is rejected.

## Dependencies

- Prefer the already available ASGI stack: `starlette` and `uvicorn` are
  transitive dependencies of the optional `mcp` extra.  The implementation adds
  `web = ["starlette>=0.37,<2", "uvicorn>=0.30,<1"]` and includes both in `dev`
  so the test suite is deterministic.
- `devrelay web serve` fails with `web_dependency_missing` and an install hint
  when the extra is absent; the core CLI remains installable without it.
- No new frontend build chain is introduced in v0.4-A.

## Test plan (offline)

- Unit: constant-time token compare, session expiry/idle expiry, header session,
  Host, Origin, content type, 64 KiB body boundary, unknown fields, id grammars.
- 33 ASGI tests via Starlette `TestClient`; no real socket for the route matrix.
- A2: stale digest, confirmation header, secret-key rejection, atomic replace,
  backup content, and file/response digest equality.
- Registry tests: absolute/relative paths, missing `.devrelay`, duplicate root,
  atomic write, path traversal attempts, no directory walking.
- Redaction tests: token, provider secret and workspace path never appear in
  unauthenticated responses; config view exposes no filesystem paths or argv.
- Live binding: exercised manually on `127.0.0.1:0`; the non-loopback CLI refusal
  is automated.  A socket-level test is intentionally not in the offline suite
  to avoid a thread/port race on the Windows CI runner.
- Existing 1,305 offline tests (1,303 pass + 2 environment skips on this
  Windows host) remain green.

## Acceptance IDs

| ID | Criterion |
| --- | --- |
| A1 | Default bind is loopback; non-loopback host is refused |
| A2 | Unauthenticated `/api/*` is `401`; `/healthz` leaks no workspace data |
| A3 | Token exchange returns a header-borne session token and sets no cookie |
| A4 | `X-DevRelay-Session` authenticates; a missing/invalid header is `401` |
| A5 | Bearer clients work without a session and never receive CORS permission |
| A6 | Wrong `Host` and wrong `Origin` are refused |
| A7 | Non-JSON, unknown-field and oversized bodies fail closed |
| A8 | Projects are exposed by registry id; no API accepts a filesystem path or browses directories |
| A9 | Read responses are bounded and contain no token/prompt/secret |
| A10 | `POST /api/config/validate` never writes; A2 writes atomically with digest guard and backup |
| A11 | Restart invalidates sessions; token is never logged or written |
| A12 | Missing `web` extra produces an actionable CLI error |
| A13 | Live loopback smoke and the full existing suite pass (manual smoke recorded above) |

## Resolved limitation: localhost cookie scope

The original A1 design used a host-scoped session cookie.  Because cookies are
not port-scoped, another local web service on `127.0.0.1` could receive it if
the user visited that service.  A2's prerequisite removed cookies entirely:
`POST /api/session` now returns a token consumed through
`X-DevRelay-Session`, a header that a browser never attaches automatically.
The remaining limitation is recorded as resolved in
[BACKLOG.md](../BACKLOG.md) §12.

A1/A2 still summarize up to 500 run documents before applying the requested
list limit; the cap fails closed, but incremental pagination belongs to v0.4-C.

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
2. **A1 was read-only; A2 adds written configuration behind a separate review
   gate** — A1 shipped without a write endpoint; A2 is now implemented and
   awaiting review.
3. **One-time fragment login URL, no persisted token file** — accepted; the
   token is per-process or supplied by `DEVRELAY_WEB_TOKEN`.

## Review focus for A1 + A2

- Does the middleware reject every request before route handling when `Host`,
  `Origin`, bearer token or session header is invalid?
- Can any read endpoint accept a path, browse a directory, or return a
  token/secret?
- Is the bounded-body path free of an unbounded buffering window?
- Is the CLI's loopback validation performed before any socket bind?
- Does `PUT /api/config` reject every execution/wiring field outside the
  allowlist, and do validate/apply share the same merge and validation path?
- Can an A2 write repoint `codex.executable`, `codex.args`, `opencode.base_url`,
  `opencode.workspace`, `profiles`, or `tests.targeted`/`tests.full`?
- Does the digest check plus in-process writer lock plus backup prevent a
  silent lost update, and is a symlinked config rejected?
- Does A2 ever rewrite a running task's frozen policy snapshot?
