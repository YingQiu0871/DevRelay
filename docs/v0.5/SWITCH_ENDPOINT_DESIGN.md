# DevRelay v0.5 — session switch endpoint design

Status: **DESIGN ONLY — NOT IMPLEMENTED.**  No switch route, request field or
mutation exists.  Lease acquisition and explicit uncertain-lease recovery are
implemented; those are preconditions, not a switch.

## Why this is not a small endpoint

A run's implementer/reviewer session ids are part of its durable evidence.  A
switch would change who executes the next turn while preserving the audit trail;
it is not a rename of a prompt.  The current run schema has no switch event, and
there is no proof that an arbitrary target session is safe to adopt.

## Preconditions (all required)

1. Durable leases are acquired for new runs and terminal release works.
2. Explicit recovery exists for stale `active`/`uncertain` leases.
3. The target session is verified by the accepted OpenCode bridge to belong to
   this canonical workspace; a client-supplied string is never trusted.
4. The target is not actively leased by another run.
5. The run has no in-flight turn and no pending manual reply.
6. A schema/evidence design for `session_switch_history` is accepted and
   migration/replay behavior is defined.
7. The switch is an explicit operator action with confirmation, expected run
   revision and expected source lease evidence.

## Proposed API (future, not implemented)

`POST /api/runs/{run_id}/session/switch`

```json
{
  "role": "implementer|reviewer",
  "target_session_id": "verified provider session id",
  "expected_updated_at": "run revision",
  "expected_source_session_id": "current run session id",
  "confirm": "apply"
}
```

- Header `X-DevRelay-Confirm: apply` plus body `confirm`.
- Loopback/auth/Host/Origin/body-cap rules unchanged.
- No arbitrary workspace/path/model/agent; no automatic fallback.

## Transaction sequence

1. Validate run/role/revision and no in-flight/pending reply.
2. Resolve target via bridge workspace proof; reject if not owned.
3. Acquire target lease; reject if active elsewhere.
4. Recheck run revision/source session.
5. Atomically append switch evidence and update the run's role session.
6. Release the source lease only after step 5 commits.
7. On any failure before commit, release target and leave run unchanged.
8. On a crash between target acquisition and commit, reconciliation marks the
   target lease uncertain; no automatic retry or reassignment.

## Required run evidence

A switch event must record:

- source/target session ids and role;
- operator confirmation source (local HTTP), timestamp;
- previous/new run revision;
- lease acquisition evidence;
- failure/rollback result.

No prompt/reply text or tokens.

## Rejections

| Condition | Result |
| --- | --- |
| run changed | `409 run_changed` |
| role not in run | `400 invalid_role` |
| target active elsewhere | `409 session_leased` |
| target not workspace-owned | `409 session_target_invalid` |
| in-flight turn | `409 run_in_flight` |
| pending manual reply | `409 manual_prompt_pending` |
| lease store corrupt | `503 session_lease_unavailable` |
| missing confirmation | `403` |

## What remains before implementation

- Lease acquisition tests are in place; recovery endpoint is implemented.
- Need a run schema version/evidence design and migration decision.
- Need a provider target-resolution path that cannot be confused with a
  client-chosen session.
- Need crash/fault tests for target-acquired-but-not-committed.
- Need independent review; no switch route is authorized by this document.

## Acceptance criteria (future)

| ID | Criterion |
| --- | --- |
| X1 | No switch without verified workspace/lease/revision gates |
| X2 | Atomic evidence + session update; no partial switch |
| X3 | Source lease released only after commit |
| X4 | Crash/uncertain target never auto-reassigned |
| X5 | No arbitrary session id/path/model/agent accepted |
| X6 | Existing prompt/interrupt/read behavior remains unchanged |
