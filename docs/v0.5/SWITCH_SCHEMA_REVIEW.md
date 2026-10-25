# Switch schema design review — 2026-10-25

Status: **APPROVED WITH CONDITIONS — SCHEMA ONLY, ENDPOINT NOT IMPLEMENTED.**

Scope: the proposed run-schema/evidence change needed before a session switch
endpoint.  This review does not authorize an endpoint, migration of existing
runs, or live session switching.

## Reviewed design

See [SWITCH_ENDPOINT_DESIGN.md](SWITCH_ENDPOINT_DESIGN.md).  The reviewed change
is a new append-only switch evidence record on `OrchestrationRun` and a schema
version boundary; the current version is 2 and v1/v2 are read-only.

## Approved schema (conditional)

Proposed v3 additions:

```text
SessionSwitchRecord:
  switch_id:           "SW-<32 lowercase hex>" (schema-validated)
  role:                "implementer" | "reviewer"
  source_session_id:   non-empty bounded string
  target_session_id:   non-empty bounded string, != source
  switched_at:         UTC ISO-8601 string
  source_revision:     the run.updated_at observed before the change
  lease_evidence:      target lease id/role/acquired_at (no token)
  operator:            "local-http"
  result:              "committed"
```

`OrchestrationRun` gains append-only `session_switch_history` (default empty).
The role's current `*_session_id` must equal the last record's target for that
role.  Records contain no prompt/reply text, tokens or provider bodies.

Schema boundary:

- new writes are v3; v1/v2 remain readable but **not switchable**;
- no automatic migration; an explicit operator migration is separate work;
- a v3 run without valid history/current-session consistency is corrupt;
- summary output bounds/redacts session/evidence fields;
- no switch is legal while `in_flight_turn` is set or a manual reply is pending.

## Conditions of approval

1. Implement crash/fault tests first (target acquired but run not updated;
   run updated but source not released; corrupt store; in-flight/pending).
   The runnable tests currently show a blocker: the lease store can hold only
   one active lease per run/role, so a pending target lease primitive (or an
   atomic swap operation) must be designed before the endpoint.
   Endpoint fault tests are committed as skipped scenarios, not as proof.
2. No endpoint until schema v3 read/write/migration tests pass and an
   independent review accepts the implementation.
3. Target session must be verified by the accepted bridge workspace check; a
   client string alone is never sufficient.
4. Lease acquisition/release is part of the transaction and rollback is tested.
5. Source lease is released only after a durable v3 commit.
6. A crash leaves uncertain leases, never silent reassignment or auto-retry.
7. Existing v1/v2 documents are never rewritten by this feature.

## Decision

**APPROVE the schema/evidence direction with the conditions above.**  This is
not approval of a switch endpoint implementation, and no code/API is added by
this review.

## Open items before implementation

- **Pending-switch lease primitive**: allow source active + target pending for
  the same run/role without weakening the one-active-lease invariant; commit
  atomically, abort cleanly, recover uncertain targets.  The current store
  rejects this (covered by `tests/test_v05_switch_faults.py`).
- Exact schema migration/read-only behavior for v2 runs.
- Summary/audit redaction bounds for session ids.
- Fault-injection hook design (no production behavior toggle).
- Independent implementation review after tests-first.
