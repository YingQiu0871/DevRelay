# DevRelay v0.5 — OpenCode session ownership & switching design

Status: **LEASE ACQUISITION + PENDING-SWITCH PRIMITIVE + v3 SWITCH EVIDENCE +
SWITCH ENDPOINT (2026-10-25).**  `src/devrelay/web/session_leases.py` implements the durable
store, including source-active + target-pending switch leases with atomic
commit/abort/uncertain; `devrelay_start_run` acquires both role leases before run
creation and terminal outcomes release them; `GET /api/sessions` reports lease
metadata.  There is still no session-switch endpoint or `session_id` request
field.

## Current facts

- A run stores `implementer_session_id` and `reviewer_session_id`.
- `start_run` accepts caller-supplied sessions and the bridge verifies workspace
  membership, not cross-run exclusivity.
- Web prompt/read/interrupt use the run's recorded session; no arbitrary session
  is accepted.
- Project activation is not session switching.

## Why a lease is needed

A string on a run is evidence of association, not ownership.  Reuse by another
run or manual CLI work can make an interrupt/prompt target unrelated activity.
A switch would amplify that risk, so the first requirement is a durable local
ownership record, not a new endpoint.

## Proposed lease record

Store under `.devrelay/web/session_leases.json` (or orchestration state if a
schema migration is approved):

```json
{
  "schema_version": 1,
  "leases": {
    "session-id": {
      "workspace": "canonical absolute path",
      "run_id": "DR-...",
      "role": "implementer|reviewer",
      "state": "active|released|uncertain",
      "acquired_at": "...",
      "released_at": "",
      "evidence": "local"
    }
  }
}
```

Invariants:

1. One active lease per session and per run/role.
2. Workspace is canonicalized (realpath + normcase on Windows) before comparison.
3. Lease acquisition requires a run and a session already verified by the
   accepted bridge/workspace check.
4. Lease release is explicit or tied to terminal run transition; never silent
   timeout while a reply is pending.
5. A corrupt/uncertain lease store fails closed: no prompt, interrupt or switch.
6. The lease is a **local claim**, not proof that the provider session is
   exclusive or alive.

## Future switch design (not authorized)

A safe switch would need:

1. Source run/role and target session id, both resolved via a durable binding
   operation — never a free-form session parameter.
2. Target lease acquisition (`409 session_leased` if active elsewhere).
3. Workspace membership proof from the accepted bridge.
4. Turn-boundary check; no switch while a turn or manual reply is pending.
5. Source lease release only after target acquisition and a durable record.
6. Explicit recovery if acquisition succeeds but provider binding fails.
7. Confirmation header/body, audit evidence, and no automatic retry.

A future API shape is detailed in
[SWITCH_ENDPOINT_DESIGN.md](SWITCH_ENDPOINT_DESIGN.md); **no endpoint is
implemented and none may be added without the lease/schema/review conditions
listed there.**

## Threat model

| Threat | Control |
| --- | --- |
| Client chooses arbitrary session | No session-id field; leases/bindings only |
| Session reused by another run | Unique active lease; `409 session_leased` |
| Cross-workspace target | Canonical workspace check; bridge ownership probe |
| Stale lease after crash | `uncertain` state; explicit recovery; fail closed |
| Switch during in-flight turn | Turn-boundary guard; reject |
| Lease file corruption | Fail closed; no provider call |
| Provider session gone | Bridge error; no fallback/default session |

## Acceptance criteria (future)

| ID | Criterion |
| --- | --- |
| S1 | No endpoint accepts an arbitrary session id |
| S2 | One active lease per session/run-role, enforced atomically |
| S3 | Cross-workspace and reused-session targets are rejected |
| S4 | Switch is rejected with in-flight/pending manual reply |
| S5 | Corrupt/uncertain lease state fails closed with no provider I/O |
| S6 | Crash recovery never silently releases or reassigns a lease |
| S7 | Audit records contain ids/roles/timestamps, never prompts or tokens |

No implementation is authorized by this document.
