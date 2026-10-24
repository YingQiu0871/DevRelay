# DevRelay v0.5 — Pause design review (proposal)

Status: **ADVISORY HOLD IMPLEMENTED (WEB + MCP ACTION PATH), 2026-10-24.**  The
hold is a durable control-plane flag, not a pause state and not a provider pause.
The accepted MCP action path consults it; there is no standalone CLI orchestration
command in this tree.  True `PAUSED` state remains unimplemented; interrupt
remains an abort request.

## Problem

The accepted orchestration state machine has no pause state.  A pause is useful
only if it has explicit semantics for an already-running provider turn; silently
blocking the next request is not a pause and must not be described as one.

## Candidate A — advisory hold (implemented web-only)

A durable, run-scoped hold flag (outside the run state machine) checked before
starting the next model-bearing action.

Implemented endpoints:

- `POST /api/runs/{run_id}/hold`
- `POST /api/runs/{run_id}/hold/release`
- run detail exposes `hold` (and `hold_error` if the store is unreadable)
- the WebUI has Hold/Release controls and displays the reason

The store is `.devrelay/web/run_holds.json`; a held run's manual prompt is
rejected with `409 run_held`.  A corrupt hold store causes manual prompt/hold to
fail closed with `503 run_hold_unavailable`.  The accepted MCP action path
(`devrelay_run_implementer` / `devrelay_run_reviewer`) also checks the store and
returns `run_held` without provider I/O.  Any future standalone CLI orchestration
command must use the same store.

### Contract

- `POST /api/runs/{run_id}/hold` with `X-DevRelay-Confirm: apply`, body
  `{"confirm":"apply","expected_updated_at":"...","reason":"..."}`.
- `POST /api/runs/{run_id}/release` with the same confirmation discipline.
- A held run rejects **new** model-bearing actions with `409 run_held`; already
  in-flight provider work is allowed to finish or be interrupted explicitly.
- The hold is advisory, not a provider pause; the run remains in its current
  state and can still be read, decided or interrupted according to existing
  rules.
- Hold/release are audited as local evidence with actor/time/reason (no secret
  or prompt text).
- Durable store keyed by workspace + run, atomic write, fail-closed on corruption.
- No automatic resume after restart; a hold remains until explicitly released.

### Invariants

1. A hold never calls a provider and never changes run state.
2. A held run never starts a new turn until release.
3. An in-flight turn is not cancelled by hold.
4. Only one hold record per run; idempotent release.
5. CLI/orchestration must consult the same hold store, otherwise the guarantee
   is web-only and must say so.

### Rejections

- pending run change: `409 run_changed`
- terminal run: `409 run_terminal`
- missing confirmation: `403`
- corrupt hold store: `503`, no action
- missing/unknown run: `404`

## Candidate B — true `PAUSED` state (v0.5+)

Adds a `PAUSED` run state with transitions at turn boundaries.  Requires a
separate design review covering:

- whether pause is legal with an in-flight turn (likely no);
- decision/limit/recovery interactions;
- terminality and replay rules;
- resume target (which state/cycle);
- audit and migration of existing run documents;
- provider-side truth: a local state does not prove the provider stopped.

This is a state-machine change, not a UI feature; it must not be smuggled into
Candidate A.

## Candidate C — process supervisor stop

Rejected: it stops the whole web process, not one run, and gives no run-level
audit or recovery semantics.

## Security / failure model

- Hold/release are authenticated, loopback-only, confirmation-gated writes.
- No arbitrary prompt, session id, path or provider target.
- Atomic durable write; corruption fails closed.
- Concurrent hold/release serialized; last-writer evidence retained.
- A hold never claims provider quiescence.

## Acceptance criteria for Candidate A

| ID | Criterion |
| --- | --- |
| P1 | Hold/release require auth + header/body confirmation |
| P2 | Hold is durable across restart and does not change run state |
| P3 | New model-bearing actions on a held run are rejected before provider I/O |
| P4 | In-flight work can still finish or be interrupted |
| P5 | Corrupt/missing hold store fails closed, never silently allows |
| P6 | CLI and web both consult the hold store, or the feature is explicitly web-only |
| P7 | No pause/interrupt conflation in API/UI/docs |

## Open questions

1. Who may hold: web operator only, or CLI too?
2. Does a hold block decision actions (not model-bearing), or only turns?
3. Is release allowed while a turn is in flight?
4. How is a hold surfaced in run detail without implying provider pause?
5. Should hold records expire? (Recommendation: no silent expiry; explicit
   release only.)

No implementation is authorized by this document.
