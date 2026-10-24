# DevRelay v0.5 — session lease acquisition design

Status: **DESIGN ONLY — NO ACQUISITION WIRING.**  The lease store exists and is
read-only in `GET /api/sessions`; `start_run` does not acquire leases and there is
no switch endpoint.

## Goal

Bind a run/role to its OpenCode session exactly once, fail closed on reuse, and
release only at a safe boundary.  The lease is a local ownership claim, not proof
that the provider session is exclusive or alive.

## Acquisition point

Preferred: inside the MCP `_execute` critical section at `devrelay_start_run`,
because that lock serializes all tool bodies in the one supported surface.

Proposed sequence:

1. Validate both session ids and the run budget.
2. Preflight `SessionLeaseStore` conflicts for implementer/reviewer sessions.
3. Start the orchestration run (existing behavior).
4. Acquire both leases using the new run id under the same `_execute` lock.
5. If acquisition fails after the run exists, do **not** report success; mark the
   run/store `uncertain` for explicit recovery.  The store remains the source of
   truth; no automatic retry.
6. On any action whose resulting summary is terminal, release both leases.
7. On `interrupt`, do not release automatically (abort may not be verified).
8. On manual prompt, acquire-if-missing is **not** allowed; the run must already
   hold leases.  Legacy runs without leases fail closed for acquisition-required
   operations until explicitly migrated/recovered.

## Required store additions

- `preflight(session_id, workspace, run_id, role)` without mutation.
- `acquire_many(...)` all-or-nothing within the single process lock.
- `release_run(run_id)` for terminal cleanup.
- `migrate_legacy_run` explicit operator action (not automatic).
- Persisted `uncertain` entries require explicit recovery; no silent reuse.

## Failure / rollback matrix

| Failure | Behavior |
| --- | --- |
| Session already leased to another run | `session_leased`, no run created |
| Two roles share one session | reject before start (existing rule) |
| Lease write fails after run creation | run not reported successful; store/run marked uncertain; no provider call |
| Terminal action succeeds | release both leases; if release fails, record `lease_error`, do not hide |
| Process crash between run and lease write | startup reconciliation marks lease uncertain; no auto-acquire |
| Corrupt lease store | fail closed (`session_lease_unavailable`), no provider I/O |
| Cross-process peer | unsupported; documented, not silently assumed |

## API / compatibility

- No new HTTP switch endpoint.
- `devrelay_start_run` keeps its inputs; behavior becomes fail-closed on conflict.
- Existing run documents without leases remain readable; acquisition-required
  actions reject with `session_lease_missing` until explicit migration.
- Error envelopes use stable codes and include only ids/state, never prompt text.

## Tests required before implementation

- preflight conflict; all-or-nothing acquisition.
- terminal release; interrupt does not release.
- crash between run and lease write -> uncertain, no duplicate.
- legacy run -> `session_lease_missing`, no provider call.
- cross-workspace reuse rejected.
- corrupt store -> fail closed.
- concurrent start calls in one surface serialized.

## Acceptance criteria

| ID | Criterion |
| --- | --- |
| L1 | Start acquires both leases before any model-bearing action |
| L2 | Conflict yields `session_leased` and no run success/provider I/O |
| L3 | Terminal state releases leases; interrupt alone does not |
| L4 | Legacy/no-lease runs fail closed with an explicit migration path |
| L5 | Crash/uncertain leases never silently reassign |
| L6 | No switch endpoint or arbitrary session id is introduced |

Implementation requires this review to be accepted first; the current store and
read-only inventory remain the only shipped lease surface.
