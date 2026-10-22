# DevRelay v0.4-D — Project & Session Management

Status: **D1 ACCEPTED / CLOSED by the owner on 2026-10-22.**  The review is
recorded in [V04D_REVIEW.md](V04D_REVIEW.md) and the acceptance record in
[V04D_ACCEPTANCE.md](V04D_ACCEPTANCE.md).  D1 adds explicit in-memory project
activation and a run-recorded session inventory.

## Scope

### Project activation

`POST /api/projects/{project_id}/activate`

```json
{"confirm": "apply"}
```

- Requires `X-DevRelay-Confirm: apply`.
- Accepts only a registered `prj_<12 hex>` id; no client filesystem path.
- Resolves the registered root with the accepted workspace rules, constructs a
  fresh read/write service for that workspace, and atomically swaps the active
  service under a lock.
- The token/session remains valid; the new active project is reflected by
  `/api/projects`, `/api/health`, and all subsequent reads/writes.
- The active project is **in-memory only**.  Restarting `devrelay web serve`
  returns to the workspace given on the command line; this is explicit, not
  persisted.
- No project is created, deleted, moved or deleted on disk.

### Session inventory

`GET /api/sessions`

- Derived only from persisted orchestration runs; no OpenCode network call.
- Each entry exposes `session_id`, roles, bounded `run_ids`, latest run/state
  and timestamp.
- Same 500-run scan cap as `/api/runs`; at most 100 sessions returned.
- This is an inventory, not a session switch: the API does not accept an
  arbitrary session id or rebind a run to another session.

### UI

- Project card gains a registry-backed selector + Activate button with
  confirmation.
- Status tab gains a Sessions list.
- Activation resets selected run/task/message detail and reloads the new
  workspace.

## Explicit non-goals

- No persistent active-project selection across restarts.
- No OpenCode session switching/ownership transfer; only the run-recorded
  session inventory.
- No project add/remove through HTTP (CLI registry remains the write path).
- No archived-run mutation; completed/terminal runs are already visible.
- No arbitrary path, session id or cross-workspace lookup.

## Security boundary

- Same loopback Host/Origin, body cap and header/bearer session auth.
- Project activation requires confirmation and resolves only registry entries.
- The registry id grammar is validated by lookup; no path is accepted.
- Session inventory contains only run-recorded ids/metadata, no provider body
  or arbitrary session lookup.
- Switching does not rotate the token; existing auth remains required.
- A switch is process-local and atomic under a lock; in-flight requests may
  finish against the previous service.

## Tests

- Project activation: confirmation, registry-only id, active marker/status
  switch, invalid id 404, auth.
- Session inventory: run-recorded role ids, auth.
- UI project/session markers.
- Existing C1/C2a/C2b/C2c/A/B tests remain green.
- Full suite: **1,342 collected** (1,340 pass + 2 environment skips on this
  Windows host).

## Acceptance IDs

| ID | Criterion |
| --- | --- |
| D1-1 | Only registered project ids can be activated; no path accepted |
| D1-2 | Activation requires confirmation and swaps the service under a lock |
| D1-3 | `/api/projects`, `/api/health` and subsequent reads reflect the active project |
| D1-4 | Sessions are run-recorded metadata only; no arbitrary session lookup |
| D1-5 | Active selection is in-memory and documented as non-persistent |
| D1-6 | UI exposes project activation and session inventory without new paths |
| D1-7 | Existing A/B/C tests remain green |
