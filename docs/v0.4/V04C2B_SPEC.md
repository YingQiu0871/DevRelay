# DevRelay v0.4-C2b — Bounded Run Control

Status: **IMPLEMENTED + INDEPENDENTLY REVIEWED — APPROVE WITH FINDINGS; P2
findings remediated; pending owner acceptance.**  The review is recorded in
[V04C2B_REVIEW.md](V04C2B_REVIEW.md).  C2b adds exactly two explicit run
controls.  It does **not** add pause, manual prompt, free-form provider output or
a live stream.

## Scope

### Decision

`POST /api/runs/{run_id}/decide`

```json
{
  "expected_updated_at": "<run.updated_at from GET>",
  "decision": "complete|request_changes|stop",
  "confirm": "apply"
}
```

- Requires `X-DevRelay-Confirm: apply`.
- Verifies the current `updated_at` before recording; a stale value is
  `409 run_changed`.  This is an optimistic hint, not a store-level CAS: the
  accepted state machine remains the final authority, and `updated_at` has
  second precision, so a same-second AWAITING_DECISION revision can still
  collide.  The state-machine rejection is mapped to `409`.
- Delegates to the accepted `devrelay_decide_run` state machine: only
  `AWAITING_DECISION`, no in-flight turn, one of the three decisions.  No model
  call is made.
- The decision is persisted in the run's `decision_history`.

### Interrupt

`POST /api/runs/{run_id}/interrupt`

```json
{"role": "implementer|reviewer", "confirm": "apply"}
```

- Requires `X-DevRelay-Confirm: apply`.
- Resolves the session ID from the run itself; no client-supplied session ID or
  arbitrary remote target is accepted.
- Requires the run to be non-terminal with an in-flight turn, and requires the
  selected role to match that in-flight turn.
- Calls the accepted `opencode_interrupt` bridge operation for that role
  session.  The session is recorded on the run, but this is **not** a proof of
  exclusive session ownership: `start_run` accepts caller-supplied sessions and
  the bridge verifies workspace membership, not cross-run uniqueness.  A
  recorded session reused by manual CLI work in the same workspace could still
  be interrupted; this residual is explicit.
- An accepted abort is **not** a verified terminal state:
  `interrupt_verified` remains false in the response, exactly as the accepted
  MCP surface documents.
- Unavailable bridge/transport errors are returned as bounded 503 envelopes;
  no retry or fallback is attempted.

## Explicit non-goals

- No pause: the accepted orchestration state machine has no pause state, and
  C2b does not invent one.
- No manual prompt: `opencode_send_prompt` remains out of scope; arbitrary
  prompt injection needs its own ownership/redaction review.
- No raw provider output, WebSocket/SSE or log stream.
- No run start, implementer/reviewer phase execution, recovery resolution,
  task approval or project switch.
- No C2b write can bypass C2a/C1 read bounds or the A2/B2 config boundaries.

## Security boundary

- Same loopback Host/Origin, body cap, header/bearer session authentication.
- `run_id` is validated by the accepted `DR-<32 hex>` grammar.
- `decision` and `role` are literal enums; unknown values are pydantic 422.
- Explicit confirmation header + body `confirm: "apply"` are both required.
- Decision has an optimistic `expected_updated_at` check.
- Interrupt can only address the implementer/reviewer session already stored on
  the run.
- The UI confirms before either action and never exposes pause/prompt/stream.

## Tests

- Decision: confirmation, stale revision, valid decision history, invalid enum.
- Interrupt: confirmation, role-scoped session ID, unverified abort flag,
  invalid role.
- UI: bounded control markers; no pause/prompt controls.
- Full suite: **1,332 collected** (1,330 pass + 2 environment skips on this
  Windows host).

## Acceptance IDs

| ID | Criterion |
| --- | --- |
| C2b-1 | Decide requires confirmation and a current `expected_updated_at` |
| C2b-2 | Decide accepts only complete/request_changes/stop and records history |
| C2b-3 | Interrupt is scoped to the run's own role session and reports unverified abort |
| C2b-4 | No pause/manual prompt/stream/start/phase-execution endpoint exists |
| C2b-5 | Auth/Host/Origin/body limits and read boundaries are unchanged |
| C2b-6 | Existing C1/C2a/A/B tests remain green |
