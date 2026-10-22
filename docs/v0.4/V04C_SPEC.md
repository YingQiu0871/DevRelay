# DevRelay v0.4-C — Dashboard & Live Runs

Status: **C1 ACCEPTED / CLOSED by the owner on 2026-10-22.**  The review is
recorded in [V04C_REVIEW.md](V04C_REVIEW.md) and the acceptance record in
[V04C1_ACCEPTANCE.md](V04C1_ACCEPTANCE.md).  C1 is a read-only dashboard over the
accepted runs API; run-control actions are deliberately deferred to a separately
reviewed C2.

## Scope

C1 adds to the B1 Status tab:

- run list with click-to-open detail;
- run state, cycle, completed cycles, model-turn budget, turn attempts,
  in-flight flag and update time;
- implementer/reviewer route snapshot;
- implementer/reviewer turn evidence (cycle, outcome, model, HTTP status,
  `submission_uncertain`/`reply_pending`/`retry_safe` flags, call IDs);
- decision history, blocked/recovery reasons;
- explicit **Refresh** and optional **Auto-refresh 5s**;
- a clear read-only/control boundary in the UI.

It uses only the existing authenticated A1 routes:

- `GET /api/runs?limit=8`
- `GET /api/runs/{run_id}`

No new write endpoint, no pause/interrupt/prompt action and no WebSocket
transport is added.

## Explicitly deferred to C2

- pause / interrupt / manual prompt / decide actions;
- raw or normalized provider output streaming;
- live WebSocket/SSE transport.

C2a (test evidence, review findings, diff stat, provider-call accounting) is
implemented separately in [V04C2A_SPEC.md](V04C2A_SPEC.md); it is still
read-only and does not add controls.

## Security boundary

- Same loopback bind, Host/Origin, body/session/bearer auth as A1/B1.
- Run IDs are validated by the existing accepted route grammar; no filesystem
  path or arbitrary task lookup is accepted.
- The dashboard renders all values with `textContent`; no `innerHTML`.
- Auto-refresh performs only authenticated GETs every 5 seconds; it stops when
  the tab is unloaded and can be switched off.
- No run action, no shell, no provider credential, no arbitrary output stream.

## UI evidence

The run detail panel shows turn evidence rather than raw provider prose:
`outcome`, `submission_status`, `submission_uncertain`, `call_ids`,
`resolved_model`, cycle and decision history.  This is the accepted normalized
run evidence, not a new data source.

## Tests

- 2 new C1 tests: seeded run detail through the existing API, and static
  auto-refresh/no-run-control checks.
- Existing 19 UI tests remain.
- Full suite: **1,326 collected** (1,324 pass + 2 environment skips on this
  Windows host).

## Acceptance IDs

| ID | Criterion |
| --- | --- |
| C1-1 | Run list is clickable and detail loads from `/api/runs/{run_id}` |
| C1-2 | Detail shows state/cycle/budget/turn evidence/decisions/reasons |
| C1-3 | Refresh and optional 5s auto-refresh are read-only GETs |
| C1-4 | No pause/interrupt/prompt/decide action is exposed |
| C1-5 | No raw provider prose, path, credential or HTML injection is introduced |
| C1-6 | Existing A1/A2/B1/B2 tests remain green |
