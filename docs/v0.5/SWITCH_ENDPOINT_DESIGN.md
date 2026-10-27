# DevRelay v0.5 — session switch endpoint design

Status: **IMPLEMENTED (2026-10-25).**  `POST /api/runs/{run_id}/session/switch`
is live with v3 evidence, target workspace verification, pending lease and
atomic lease commit.  A lease-commit failure after the run write returns
`503 switch_lease_uncertain` and requires explicit recovery.  See
[SWITCH_SCHEMA_REVIEW.md](SWITCH_SCHEMA_REVIEW.md).

## Why this is not a small endpoint

A run's implementer/reviewer session ids are part of its durable evidence.  A
switch changes who executes the next turn while preserving the audit trail; it
is not a rename of a prompt.  The v3 run schema now carries validated switch
evidence, and the endpoint verifies the target through the accepted bridge.

## Implemented endpoint

`POST /api/runs/{run_id}/session/switch`

Body: `role`, `target_session_id`, `expected_updated_at`,
`expected_source_session_id`, `confirm: "apply"`; header
`X-DevRelay-Confirm: apply`.

Happy path:

1. validate auth/confirmation/revision/role/source session;
2. reject terminal, in-flight, pending manual prompt or existing pending switch;
3. verify target workspace ownership through the bridge;
4. acquire target `pending_switch` lease;
5. append v3 evidence and update the run role session;
6. atomically commit the lease (target active, source released).

Failure after the run write but before lease commit returns
`503 switch_lease_uncertain`; the target lease is marked uncertain and manual
prompts are blocked by `switch_pending` until explicit recovery.  No UI control
is added.

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
- Schema/evidence direction approved with conditions in
  [SWITCH_SCHEMA_REVIEW.md](SWITCH_SCHEMA_REVIEW.md); implementation pending.
- Need a migration decision for v1/v2 runs and tests-first fault coverage.
- Pending-switch lease primitive is implemented and tested (source active +
  target `pending_switch`, atomic commit/abort/uncertain, explicit recovery).
  The HTTP endpoint and v3 run-schema implementation remain blocked on this
  review's remaining conditions; one endpoint fault scenario is still skipped.
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
