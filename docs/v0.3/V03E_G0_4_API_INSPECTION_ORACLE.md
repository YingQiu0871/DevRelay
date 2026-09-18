# DevRelay v0.3-E — G0.4 / P4 proof definition candidate: installed-API inspection oracle

**Status: PRE-RUN DEFINITION CANDIDATE — G0.4 remains NOT RUN and this file contains NO
G0.4 result.**  If an independent reviewer approves it without modification, this file
becomes the immutable oracle for the future G0.4 execution.  Until then, G0.4 is
`NOT RUN / DEFINITION CANDIDATE AWAITING INDEPENDENT REVIEW`, P4 is **not** proven, and
no claim in this file may be read as a proof outcome.

## 1. Identity

| Item | Value |
| --- | --- |
| Repository HEAD at drafting | `f41b7a1510a2c4f8b81c5e7a0d1fb439eb6dfdf8` |
| Branch | `v0.3-e-recovery-reconciliation` |
| Package version / public tags | `0.1.0` / `v0.1.0` only; no upstream |
| Frozen semantic design candidate | `9f4a01804b9affe8938a272553df345b5a60aeed` |
| Authoritative proof state at drafting | `G0.1 / P7 = PASS / CLOSED`; `G0.2 = PASS / CLOSED`; `G0.3 / P5 = PASS / CLOSED`; `G0.4 = NOT RUN`; `G0.5 = NOT RUN`; `G1 = NOT RUN`; `G2 = NOT RUN` |
| Platform proof gate | `PARTIALLY EXECUTED / NOT COMPLETE` |
| mandatory-core implementation | **NOT AUTHORIZED** |
| `adopt_completed_turn` | **DISABLED** |
| v0.3-E | DESIGN FROZEN / NOT IMPLEMENTED / NOT ACCEPTED / UNRELEASED |
| Installed target | OpenCode **1.18.11** (`opencode-ai` npm package, `bin/opencode.exe`; a desktop build is also installed) |
| Budget for the future G0.4 execution | 0 provider/model inference calls; 0 model turns; 0 external network requests; 0 OpenCode starts/restarts; **at most 1** local loopback read-only HTTP GET (`/doc`) |

## 2. Frozen design references this definition must stay inside

* `V03E_SPEC.md` §14 — pending results (P4): report-only policy.
* `V03E_SPEC.md` §19 row **D** — pending-result handling: "would require an
  operation-specific handle proof"; **report-only in v0.3-E; no mutation capability**.
* `V03E_SPEC.md` §25 — proof gate step **G0.4** ("OpenCode installed-API inspection for a
  per-operation pending handle (P4)", scope `read-only inspection`, 0 real provider
  calls), the gate rules (no probe shopping; one planned probe per case; harness-invalid
  attempts recorded and excluded), and the statement that G0.4–G0.5 "remain relevant to
  the reporting language … and must not blur the G0.1 gate".
* `V03E_SPEC.md` §28 row **P4** — "does a durable per-operation pending handle exist?" →
  gates `pending capability (D)`.
* `V03E_ACCEPTANCE.md` row **E31** (FROZEN, report-only) and row **E37** (G0.4,
  `PROOF REQUIRED (read-only inspection)`).
* Preserved runtime policy (must not be altered by this definition or by the future
  proof): `reply_pending` is **report-only**; no pending-result adoption, no polling
  loop, no automatic wait, no pending-driven state advance, no retry, no resubmission,
  no budget refund, no automatic resume; a merely `busy` session never advances
  anything; future use of a stronger platform operation handle requires a **separately
  reviewed capability extension**; P4 is **not** part of the `adopt_completed_turn`
  gate; G0.4 must **not** become a new mandatory-core hard gate.

### 2.1 Historical P4 knowledge vs formal G0.4 proof status (explicit)

* **Historical knowledge:** the previous design review concluded that OpenCode 1.18.11
  exposes session-level status only and that there is no durable per-operation pending
  handle.  This is recorded in `V03E_SPEC.md` §14 as a *recorded independent-review
  conclusion*, in §27 as a design decision, and in §28 as an already-answered question.
* **Formal proof status:** **G0.4 has not yet formally established that result** under a
  precommitted platform-proof definition, so `E37` remains `PROOF REQUIRED` and G0.4
  remains `NOT RUN` until the separately executed proof is independently approved.
* The frozen **policy** consequence of the historical knowledge (`reply_pending` is
  report-only) is unaffected by the proof status: **E31 stays FROZEN / report-only**
  whether G0.4 passes, fails, or is never run.
* Nothing in this file may be used to write that P4 has already formally passed.

## 3. Exact question G0.4 characterizes

> Does the installed OpenCode 1.18.11 API expose a durable, operation-specific,
> read-only-observable handle for one submitted operation that is stronger than
> session-level busy/idle state?

G0.4 is a **characterization** proof, **not** "prove that a handle does not exist".  Both
a positive and a negative fully-evidenced answer are valid characterization results.

## 4. Definition: "per-operation"

A handle is **per-operation** only if it identifies one specific submission/operation
rather than any of: an entire session; the current session busy/idle state; an arbitrary
message without operation linkage; a DevRelay-local ledger call id; a cursor; a
timestamp; an event with no durable lookup identity.

It must let an API consumer distinguish **operation X** from **another operation in the
same session**.

## 5. Definition: "durable" for G0.4 (narrow, precommitted minimum)

A candidate handle is **DURABLE for G0.4** only if all four hold:

1. it is **OpenCode-owned / exposed by the OpenCode API**, not merely held in DevRelay
   transient memory;
2. it **survives beyond the lifetime of the initiating synchronous HTTP request / local
   function call**;
3. after the original submit call's transient local context is gone, a **read-only API
   surface can still use that identifier/resource** to inspect the state or result
   association of that same specific operation;
4. its identity **does not depend on timestamp/order heuristics**.

**Explicit exclusion (scope):** G0.4 does **not** require durability across an OpenCode
server restart.  That dimension is outside this proof's scope and overlaps later
restart/history questions such as G1/P1 or a future pending-capability extension.  This
G0.4 durability definition **cannot** by itself justify implementing any capability.

## 6. Qualifying-handle requirements

A qualifying handle requires **all** of:

* `OPERATION_SPECIFIC` (section 4);
* `OPEN_CODE_OWNED`;
* `POST_CALL_OBSERVABLE` (observable after the initiating call's transient context is
  gone);
* `READ_ONLY_QUERYABLE_OR_DURABLY_RESOLVABLE` (a read-only API surface can resolve the
  identifier to that operation's state/result association);
* `NO_TIMESTAMP_OR_ORDER_HEURISTIC_REQUIRED`.

If any single requirement is absent, the object is **not** a qualifying durable
per-operation pending handle.  A partially characterized candidate is
`EVIDENCE_INSUFFICIENT`, never a positive result.

## 7. Non-qualifying examples (precommitted)

Non-qualifying unless the future inspection proves additional durable semantics:
session id; session busy/idle status; DevRelay `call_id`; `reply_boundary`; assistant
message id alone; `requestID` / `request_id` string presence alone; ephemeral SSE event
id alone; `prompt_async` route name alone; a message id with no operation-state lookup;
a timestamp/order position.  **A string appearing in a compiled binary is never proof of
handle semantics by itself.**

## 8. Inspection method (for the future execution only)

The future G0.4 proof must combine **both**:

**A. Static installed-artifact inspection (read-only).**
* installed `opencode-ai` package metadata (name/version/entry points);
* the shipped compiled binary / artifacts, for string/route-name inventory only;
* accepted DevRelay source (to establish what DevRelay holds locally);
* the historical accepted v0.3-A API record **as context only** — never as current proof.
* Static string presence alone is **not** sufficient for a semantic conclusion.

**B. Exactly one bounded live local schema inspection.**
* **exactly ONE** read-only loopback HTTP `GET /doc`;
* against an **already running accepted local OpenCode 1.18.11** server;
* no other HTTP method or endpoint may be called; no `prompt`, no `prompt_async`, no
  message `POST`, no `interrupt`, no session mutation, no event subscription, no provider
  request, no model turn;
* **no OpenCode process may be started or restarted for the proof** (neither to obtain
  `/doc` nor to retry);
* if no already-running accepted 1.18.11 server can provide `/doc` under this authorized
  read-only method, the proof **must not silently fall back to starting a server**: the
  result is `EVIDENCE_INSUFFICIENT` / **FAIL**, unless an independently reviewed
  replacement evidence method is authorized **before** execution.

**Why `/doc` is required:** the installed npm package ships a compiled binary and string
evidence but no readable route table / OpenAPI source sufficient to establish field
semantics or route linkage; the historical v0.3-A `/doc` observation is context, not
current G0.4 proof.  Therefore the future proof must inspect the **current installed
server's** read-only schema exactly once, and no historical `/doc` result alone may
establish G0.4 PASS.

## 9. Fixed future case matrix (exactly A–H; one live probe total)

| Case | Content | Precommitted expectation / outcome |
| --- | --- | --- |
| **G0.4-A — INSTALLED IDENTITY** | verify the installed server/package target is OpenCode 1.18.11 | `IDENTITY_MATCH`; mismatch → **FAIL** |
| **G0.4-B — COMPLETE CURRENT `/doc` CAPTURE** | the single authorized read-only loopback `GET /doc`; verify a parseable OpenAPI/schema document for the running accepted 1.18.11 instance | `SCHEMA_AVAILABLE`; unavailable/malformed/version-inconsistent → **FAIL** |
| **G0.4-C — SESSION STATUS CONTROL** | inspect `/session/status` and the `SessionStatus` schema | characterize `SESSION_LEVEL_ONLY` or an operation-specific resource; historical expectation `SESSION_LEVEL_ONLY`, but the conclusion must rest on current schema evidence |
| **G0.4-D — SYNCHRONOUS MESSAGE ROUTE** | inspect `POST /session/{id}/message` request/response schemas from `/doc` only (no POST executed) | determine whether the schema returns any candidate operation handle distinct from ordinary session/message ids |
| **G0.4-E — `PROMPT_ASYNC` ROUTE** | inspect `POST /session/{id}/prompt_async` schema from `/doc` only (never invoked) | characterize request schema, response schema, returned identifiers, whether any returned identifier is operation-specific, and whether a read-only durable lookup route exists for it; route existence alone is not a qualifying handle |
| **G0.4-F — EVENT SURFACES** | inspect `/event` and `/global/event` schemas only (never subscribed) | characterize `requestID`, `request_id`, event identifiers and resource references, and determine whether they are merely event payload metadata or whether a durable read-only operation lookup exists; ephemeral event correlation alone does not qualify |
| **G0.4-G — IDENTIFIER TRACEABILITY** | for every candidate identifier discovered in C–F: trace all current `/doc` routes/schemas for a read-only API resource that can later resolve that identifier to the same operation's pending/result state | classify each candidate against **all** qualifying-handle requirements |
| **G0.4-H — COMPLETENESS / NEGATIVE CONTROL** | search the **complete** current `/doc` path/schema set (not only expected route names) for any other operation/request/task/job/run/prompt handle capable of qualifying | the absence conclusion may be made **only** after this complete schema sweep |

## 10. Future outcome set (exactly one conclusion)

* `CHARACTERIZED_NO_DURABLE_PER_OPERATION_HANDLE`
* `CHARACTERIZED_HANDLE_PRESENT_BUT_OUT_OF_SCOPE_FOR_V03E`
* `EVIDENCE_INSUFFICIENT`
* `SCHEMA_CONTRADICTION`

No fuzzy partial-success verdict is permitted.

## 11. PASS semantics (both conclusions are fully-evidenced characterizations)

* **PASS-A — `CHARACTERIZED_NO_DURABLE_PER_OPERATION_HANDLE`:** the complete authorized
  installed-API inspection finds no API object/field/resource satisfying the
  qualifying-handle definition (section 6), after the complete schema sweep of case H.
* **PASS-B — `CHARACTERIZED_HANDLE_PRESENT_BUT_OUT_OF_SCOPE_FOR_V03E`:** the installed
  API conclusively exposes a qualifying durable per-operation handle, with **every**
  qualifying dimension established (section 12).

**PASS-B does not enable that handle in v0.3-E.**  Current v0.3-E pending policy remains
report-only; using such a handle would require a new reviewed capability design **plus**
a new proof **plus** a new implementation authorization.  Therefore G0.4 PASS means
"the installed API was conclusively characterized" — it does **not** mean "pending
adoption capability enabled".

## 12. Handle-present rule

If a candidate handle is found, the proof must not stop at its name.  To conclude
`CHARACTERIZED_HANDLE_PRESENT_BUT_OUT_OF_SCOPE_FOR_V03E` it must establish **all**
qualifying dimensions (operation-specific, OpenCode-owned, post-call observable,
read-only-queryable/durably resolvable, no timestamp/order heuristic required).  If any
durability/specificity/queryability dimension is unresolved, the result is
`EVIDENCE_INSUFFICIENT`, **not** `HANDLE_PRESENT`.

## 13. Handle-absent rule

To conclude `CHARACTERIZED_NO_DURABLE_PER_OPERATION_HANDLE` the proof must: successfully
inspect the **current** `/doc`; cover the complete path/schema set; inspect the known
candidate routes; trace every candidate identifier; and establish that none satisfies
all qualifying dimensions.  Absence may **never** be inferred from missing expected
names, binary strings, a single route, `session/status` alone, or historical review
prose.

## 14. FAIL semantics

A future G0.4 candidate FAIL occurs if the authorized inspection cannot conclusively
characterize the installed API against the qualifying-handle definition, with
non-exhaustive example classes: `EVIDENCE_INSUFFICIENT`, `SCHEMA_UNAVAILABLE`,
`CANDIDATE_IDENTIFIER_SEMANTICS_UNRESOLVED`, `CONTRADICTORY_API_SURFACES`,
`INCOMPLETE_ROUTE_OR_SCHEMA_COVERAGE`,
`INSPECTION_METHOD_FAILURE_AFTER_REACHING_ASSERTION_POINT`.

A FAIL means **P4 remains formally unproven**.  It does **not** block the mandatory core,
does **not** block `mark_unrecoverable`, does **not** alter the adoption gate, does
**not** enable retry, and does **not** remove any currently enabled pending capability
(v0.3-E has none).  Pending remains report-only.

## 15. Failure consequence (precommitted, precise)

If G0.4 FAILS: `E31` remains FROZEN / report-only; `reply_pending` remains report-only;
no pending capability is enabled; no capability is automatically removed because none
exists; mandatory-core authorization rules do not change; the adoption gate does not
change; `mark_unrecoverable` remains available; G0.4 stays failed/unproven; and any
stronger future pending capability remains unavailable.  **No degraded implementation
mode is invented.**

## 16. Controls (precommitted)

* **`wait_idle` control:** `wait_idle` is **session-level only**.  A session being `idle`
  does **not** prove that the specific previous submission completed, and a missing
  session-status-map entry being treated as idle is likewise **not** an
  operation-completion proof.  G0.4 must not reinterpret `wait_idle` as a per-operation
  handle.
* **DevRelay identifier control:** DevRelay `call_ids` are local ledger identifiers;
  `assistant_message_ids` are remote **message** identifiers; `reply_boundary` is a
  session/message cursor; `in_flight_turn` is DevRelay-local persisted intent.  None is a
  qualifying remote per-operation pending handle merely by existing.  G0.4 concerns the
  **OpenCode platform API**, not DevRelay-local state.

## 17. No-probe-shopping rule (future execution)

The future G0.4 proof contains exactly cases **A–H**.  There is exactly **one** live HTTP
probe: case B / `GET /doc`.  Cases C–H are analyses of that same captured schema plus the
installed local artifacts.  No extra HTTP probe may be performed after seeing results,
and no second OpenCode server may be started to search for a better result.

A rerun of `/doc` is permitted **only** if a mechanical harness defect prevents the first
attempt from reaching the precommitted assertion point — e.g. the local proof script
cannot parse its own output because of a proof-script bug, or the capture file cannot be
written because of a proof-harness bug before response validation.  The following are
**not** harness-invalid and **count** as semantic evidence outcomes: the server returns
404; authorization rejects the GET; the schema is malformed; a route is missing; an
expected field is absent; candidate identifier semantics remain unresolved.

## 18. Evidence requirements (future proof)

Repository identity; installed package version/path; running-server version identity if
available from `/doc`/schema metadata; `/doc` HTTP status; `/doc` media type; full schema
hash; path count; schema/component count; candidate route list; candidate identifier
list; per-identifier qualifying-dimension matrix; complete path/schema search method;
session-status finding; sync-message schema finding; `prompt_async` schema finding;
event/global-event schema finding; `wait_idle` control finding; DevRelay-local-id control
finding; final characterization verdict; capability consequence; provider/model count;
external-network count; loopback GET count; OpenCode start/restart count.

**Must not persist:** credentials, raw prompts, responses containing user content,
reasoning, provider secrets.  The OpenAPI document may be hashed and summarized; no
sensitive server configuration may be committed.

## 19. Consequence of a positive finding

If the future G0.4 proof establishes a qualifying handle, G0.4 may PASS as
`CHARACTERIZED_HANDLE_PRESENT_BUT_OUT_OF_SCOPE_FOR_V03E` — but `reply_pending` remains
report-only in current v0.3-E, no current capability is enabled, no current tool may use
the handle, and a future pending-capability extension requires new design, new proof, new
implementation review and separate authorization.

## 20. Consequence of a negative finding

If the future proof establishes no qualifying handle, G0.4 may PASS as
`CHARACTERIZED_NO_DURABLE_PER_OPERATION_HANDLE`.  Current frozen policy remains exactly
as already designed: `reply_pending` = report-only; no pending adoption, no polling loop,
no automatic wait, no pending-driven advance.  This PASS formally closes P4 for the
installed 1.18.11 target.

## 21. Consequence of insufficient evidence

If the current `/doc` cannot be obtained under the authorized method, or candidate
identifier semantics cannot be conclusively resolved, then G0.4 =
`CANDIDATE FAIL / P4 UNPROVEN`.  Historical review knowledge must **not** be treated as
substitute proof, and current policy remains report-only.

## 22. Acceptance transition (future; not executed here)

* before execution: `E37 = PROOF REQUIRED / G0.4 NOT RUN`;
* after the executing agent obtains a conclusive characterization:
  `G0.4 = CANDIDATE PASS / AWAITING INDEPENDENT REVIEW` and
  `E37 = CANDIDATE PASS / AWAITING INDEPENDENT REVIEW`;
* after an inconclusive/failed characterization:
  `G0.4 = CANDIDATE FAIL / P4 UNPROVEN`.

Only an independent reviewer may produce `G0.4 / P4 = AUTHORITATIVE PASS`; the executing
agent may never self-approve.

## 23. Approved claim boundaries

**If a future PASS-A is approved, the maximum claim is:** for the inspected installed
OpenCode 1.18.11 API/schema, no exposed read-only API object satisfies the precommitted
definition of a durable per-operation pending handle.  It must **not** be claimed that no
internal/private handle exists inside OpenCode, that future versions have none, that
event internals have none beyond the exposed API, or that provider delivery is known.

**If a future PASS-B is approved, the maximum claim is:** for the inspected installed
OpenCode 1.18.11 API/schema, a specific exposed API object satisfies the precommitted
characterization definition.  It must **not** be claimed that it is safe for v0.3-E to
use, that it survives an OpenCode restart, that it proves provider delivery, that it
enables pending adoption, or that it changes current recovery semantics.

## 24. Non-claims of this definition round

This file defines a proof; it proves nothing.  It contains **no** G0.4 observed result,
it does not execute the inspection, it issues no HTTP request and does not read `/doc`,
it starts no OpenCode server, and it changes no runtime behaviour.  It does not make P4
proven, does not make G0.4 pass, and does not authorize implementation, adoption, retry
or any capability change.  `G0.4` remains `NOT RUN` until a separately executed proof is
independently approved.
