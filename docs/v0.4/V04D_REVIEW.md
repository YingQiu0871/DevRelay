# DevRelay v0.4-D1 — independent review record

Status: **D1 reviewed: REQUEST CHANGES remediated to APPROVE WITH FINDINGS
(P0/P1 = 0); accepted by the owner on 2026-10-22.**  No v0.4 tag or release is
implied.  See [V04D_ACCEPTANCE.md](V04D_ACCEPTANCE.md).

## Findings and disposition

| ID | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| D1-R1 | P1 | `activate_project` awaited `run_in_threadpool` while holding a `threading.RLock`; a second concurrent activation could block the single event loop forever. | Fixed: the new service is built outside the lock; only the attribute swap is inside a no-await critical section.  Concurrent activations are last-write-wins and both complete.  A two-worker TestClient concurrency test covers it. |
| D1-R2 | P2 | UI had no workspace epoch: an auto-refresh from the old service could repaint old runs after a switch or reopen an old run. | Fixed: `workspaceEpoch` invalidates `loadAll`/`refreshRuns` results; auto-refresh is stopped during the switch; successful switch reloads explicitly and a reload failure is reported as post-switch. |
| D1-R3 | P2 | Tests missed activation failure/rollback, concurrency, post-switch isolation, health project id and body confirmation. | Added: deleted-registry-root 503 with old service retained; concurrent activation; `/api/runs|tasks|sessions` empty after switch; `/api/health` project id; missing body confirm 422. |
| D1-R4 | P3 | Body `confirm` was parsed but unused. | Now checked explicitly. |
| D1-R5 | P3 | `app.state.project_id` was dead/drift-prone. | Removed; handlers use the API's active project id. |
| D1-R6 | P3 | Registered root was not checked for absolute path at activation. | Activation rejects non-absolute roots with 409.  A replaced directory at the same path remains a same-user registry-trust residual. |
| D1-R7 | P3 | `loadAll` failure after a successful switch could look like activation failure. | UI reports "Project switched, but reload failed" instead. |
| D1-R8 | P3 | Session `run_ids` silently capped; latest tie left first run; project roots exposed in `/api/projects`. | Added `run_ids_truncated`; ties prefer the later run; project roots remain part of the authenticated registry view (accepted D1 scope). |

## Verified good

- Activation accepts only a registered `prj_<12 hex>` id; no path is accepted.
- Auth, Host/Origin, header confirmation and body confirmation gate activation.
- Service swap is in-memory/process-local; no persistence and no filesystem
  create/remove/move.
- Sessions are derived from persisted runs only; no arbitrary session lookup,
  provider body or session switch endpoint.
- UI uses registry ids/labels; activation resets detail, stops auto-refresh and
  reloads the new workspace.
- Existing A/B/C tests remain green.

## Remaining gate

D1 is implemented and reviewed with findings; owner acceptance is pending.
Persistent active selection, OpenCode session switching/ownership transfer,
HTTP project add/remove and archived-run mutation remain deferred.
