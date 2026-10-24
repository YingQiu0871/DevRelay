# DevRelay v0.5 — session lease acquisition design

Status: **IMPLEMENTED (MCP START + TERMINAL RELEASE), 2026-10-25.**  The lease
store is acquired inside `devrelay_start_run` before run creation, released on
terminal outcomes, and remains read-only in `GET /api/sessions`.  There is still
no switch endpoint.  A crash between acquisition and run creation can leave an
active lease; it fails closed and can be explicitly released through
`POST /api/sessions/{session_id}/lease/recover` after out-of-band verification.

## Goal

Bind a run/role to its OpenCode session exactly once, fail closed on reuse, and
release only at a safe boundary.  The lease is a local ownership claim, not proof
that the provider session is exclusive or alive.

## Acquisition point

Preferred: inside the MCP `_execute` critical section at `devrelay_start_run`,
because that lock serializes all tool bodies in the one supported surface.

Implemented sequence:

1. Validate both session ids and the run budget; reject identical sessions before
   acquiring.
2. Generate the run id once and acquire both leases (all-or-nothing rollback).
3. Start the orchestration run with that run id under the same `_execute` lock.
4. If start fails, release the acquired leases and report the original error; no
   successful run is returned.
5. If acquisition fails, report `session_leased` / `session_lease_unavailable`;
   no run is created.
6. On any action whose resulting summary is terminal, release both leases.
7. On `interrupt`, do not release automatically (abort may not be verified).
8. Legacy run documents without leases remain readable; acquisition is only for
   new runs.  A crash between acquisition and run creation can leave an active
   lease that blocks reuse until explicit recovery.

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
