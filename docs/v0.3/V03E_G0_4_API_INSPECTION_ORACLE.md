# DevRelay v0.3-E — G0.4 / P4 proof definition candidate: installed-API inspection oracle

**Status: PRE-RUN DEFINITION CANDIDATE (REVISION 3) — G0.4 remains NOT RUN and this file
contains NO G0.4 result.**

Revision 1 (`abd677a`) was rejected.  Revision 2 (`5cb03a8`) was **also rejected**: the
independent decision was **`REQUEST_CHANGES — V0.3-E G0.4 PROOF DEFINITION REVISION 2`**
with **P0 = 0, P1 = 2, P2 = 0**.  The two blocking findings were:

* **P1-1** — no mandatory post-`/doc` responder-continuity verification;
* **P1-2** — binding-chain ambiguity/incompleteness: ambiguous listener / `localhost`
  IPv4-IPv6 handling not fail-closed; the package's declared bin not required to resolve to
  the listener executable; executable SHA-256 equality not required.

The review **otherwise accepted** the target concretization as npm `opencode-ai` 1.18.11,
the characterization model, PASS-A / PASS-B, the durability definition, the A–H matrix, the
one-`/doc` budget, the no-probe-shopping rule and the frozen report-only policy.

**Revision 3 closes only P1-1 and P1-2 plus associated wording**: the mandatory
post-request responder-continuity snapshot (§8.8) and the completed binding chain — exact
configured endpoint only (§8.2), fail-closed address-family / listener-ambiguity rule
(§8.3), mandatory declared-bin binding (§8.4), mandatory executable SHA-256 equality (§8.5),
mandatory process creation/start identity (§8.6), pre-request snapshot and `TARGET_BOUND`
precondition (§8.7), fixed six-step order (§8.9), `/doc` metadata role (§8.10), explicit
case findings A1–A10 / B1–B2 (§9.1, §9.2), global PASS precondition (§11), the binding
failure list (§17.1) and the expanded mandatory evidence fields (§18).  Nothing already
accepted is reopened or weakened.

Revision 3 is **not** immutable and **not** accepted: it must be independently re-reviewed
before any execution.  Until then G0.4 is
`NOT RUN / REVISION-3 DEFINITION CANDIDATE / AWAITING INDEPENDENT RE-REVIEW`, P4 is **not**
proven, no G0.4 PASS exists, and no claim in this file may be read as a proof outcome.
Revision 3 is a definition-level change only: it alters no runtime semantics, grants no
capability and performs no inspection — it issues no HTTP, reads no `/doc`, resolves no
endpoint, queries no process and computes no hash.

## 1. Identity

| Item | Value |
| --- | --- |
| Repository HEAD at drafting | `5cb03a846aa192b2397f46909a4c92b09a481227` (revision-3 drafting base; revision 1 was drafted at `f41b7a1510a2c4f8b81c5e7a0d1fb439eb6dfdf8`) |
| Branch | `v0.3-e-recovery-reconciliation` |
| Package version / public tags | `0.1.0` / `v0.1.0` only; no upstream |
| Frozen semantic design candidate | `9f4a01804b9affe8938a272553df345b5a60aeed` |
| Authoritative proof state at drafting | `G0.1 / P7 = PASS / CLOSED`; `G0.2 = PASS / CLOSED`; `G0.3 / P5 = PASS / CLOSED`; `G0.4 = NOT RUN`; `G0.5 = NOT RUN`; `G1 = NOT RUN`; `G2 = NOT RUN` |
| Platform proof gate | `PARTIALLY EXECUTED / NOT COMPLETE` |
| mandatory-core implementation | **NOT AUTHORIZED** |
| `adopt_completed_turn` | **DISABLED** |
| v0.3-E | DESIGN FROZEN / NOT IMPLEMENTED / NOT ACCEPTED / UNRELEASED |
| Installed target (accepted) | **OpenCode 1.18.11 as shipped by the npm package `opencode-ai`** (`%APPDATA%\npm\node_modules\opencode-ai`, entry point `./bin/opencode.exe`) |
| Other installations on the host | a **desktop build** (`@opencode-aidesktop`) is also installed on this machine and is **not** the accepted target; a responder from any other installation is a different target and cannot be characterized by this definition |
| Definition revision | **revision 3** (remediation of revision 2 per the review's `REQUEST_CHANGES`, P1 = 2; see §25).  Revisions 1 and 2 were **both rejected** and neither is approved; revision 3 awaits independent re-review |
| Target instance to be bound | the listener answering the **exact configured DevRelay endpoint**, bound to the npm `opencode-ai` 1.18.11 installation by the mandatory chain of §8.1–§8.7 (canonical path **and** executable SHA-256 equality) |
| Authoritative document hash | SHA-256 of the **committed Git blob** (§26); the revision-3 blob hash is recorded in the revision-3 remediation report, not embedded in this file |
| Budget for the future G0.4 execution | 0 provider/model inference calls; 0 model turns; 0 external network requests; 0 OpenCode starts/restarts; **at most 1** local loopback read-only HTTP GET (`/doc`, the only permitted HTTP operation); local, read-only OS-metadata reads (socket listing, process query, package metadata, executable hashing) are permitted **only** as proof identity evidence |

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
* the mandatory target-binding chain of §8.1–§8.8 uses **local, read-only OS metadata reads
  and file hashing only** (socket listing, process query, package metadata, executable
  SHA-256) — it issues no HTTP, executes nothing, writes nothing, and is permitted **only**
  as proof identity evidence, never as runtime endpoint resolution;
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

### 8.1 Target-instance binding (MANDATORY; read-only; zero extra HTTP)

The semantic conclusion is only valid for the **bound** target instance, so the binding is
a required, fail-closed precondition of both PASS-A and PASS-B.  It uses **no HTTP of its
own** (the `GET /doc` of part B remains the only permitted HTTP operation) and is
precommitted as:

1. take the **configured loopback endpoint** from the accepted DevRelay configuration
   (explicit by design — DevRelay never scans ports or processes,
   `src/devrelay/config.py`);
2. resolve that endpoint to the **concrete loopback address and port the future HTTP client
   will actually use**, deterministically and without ambiguity (§8.2, §8.3), then — from
   **local, read-only OS metadata only** — map **that exact address/port** to its **single
   listening PID** and then to that process's **executable path** (e.g. a listening-socket
   listing plus a process query);
3. resolve that executable path to its **installation root and package metadata** and read
   its **name/version** (e.g. the `package.json` of the npm installation that owns the
   executable);
4. accept the installation only if its package metadata satisfies `name == opencode-ai` and
   `version == 1.18.11` **and** its declared bin `./bin/opencode.exe` resolves to a canonical
   executable path that **equals** the canonical listener executable path (§8.4) **and** the
   listener executable's SHA-256 **equals** the target declared-bin executable's SHA-256
   (§8.5).  Being merely inside the package root, or matching the process name alone, is
   **not** sufficient; no other installation (desktop build, another npm install, another
   version, another executable) may be substituted, and no dynamic retargeting is permitted;
5. require **process creation/start identity** for that listener (§8.6): PID, canonical
   executable path, executable SHA-256 and the OS process creation/start timestamp;
6. **freeze the pre-request snapshot** and establish `TARGET_BOUND` (§8.7) before any HTTP;
7. after the single `GET /doc`, **re-take the snapshot** and require full equality (§8.8).
   `/doc` version/build metadata is used only to **corroborate** — never to substitute for —
   this local chain (§8.10).

Rules:

* if the binding cannot be established within this authorized method — non-loopback or
  ambiguous destination (§8.2, §8.3), no listener, unresolvable PID or executable, missing
  executable path, unreadable or wrong package metadata, declared-bin mismatch, wrong or
  unresolvable executable, executable hash mismatch, missing process creation/start
  identity, or a failure of the post-request continuity check (§8.8) — the outcome is
  **`EVIDENCE_INSUFFICIENT`** and therefore **CANDIDATE FAIL / P4 UNPROVEN**.  It is
  **never** PASS-A or PASS-B, and **no `GET /doc` is issued** when the failure occurs before
  the GET (§8.7);
* a **non-matching** installation (desktop build, another npm install, another version,
  another executable) is reported as `TARGET_INSTANCE_MISMATCH` *within* that
  `EVIDENCE_INSUFFICIENT` outcome — the revision-2 label `TARGET_MISMATCH` is subsumed by
  it: the run is **INCONCLUSIVE for the accepted target**, no characterization of the
  accepted target is made, and characterizing the other installation would require a
  **separately authorized definition that names that target**;
* local port/process metadata is used as **proof evidence only**.  It is **not** a runtime
  endpoint-resolution mechanism, it does not change DevRelay's "never scans ports or
  processes" posture, and it must not be used to select, adopt or reconfigure an endpoint;
* the binding evidence — target statics, config resolution, the pre-GET snapshot, the
  post-GET snapshot and the binding verdicts (§18) — is **mandatory**, never "if
  available"; no required target-binding field may be omitted, and omitting one triggers the
  corresponding failure reason of §17.1.

**Why `/doc` is required:** the installed npm package ships a compiled binary and string
evidence but no readable route table / OpenAPI source sufficient to establish field
semantics or route linkage; the historical v0.3-A `/doc` observation is context, not
current G0.4 proof.  Therefore the future proof must inspect the **current installed
server's** read-only schema exactly once — **for the bound target instance** — and no
historical `/doc` result alone may establish G0.4 PASS.

### 8.2 Exact configured endpoint only (MANDATORY)

The future proof starts from the **exact endpoint resolved by accepted DevRelay
configuration** (`src/devrelay/config.py`; the endpoint is explicit by user configuration
and DevRelay never scans ports or processes).

* **No endpoint discovery.  No arbitrary port scan.  No search for a "working" OpenCode
  server.  No alternate endpoint after a failure.  No second server.**
* The endpoint must resolve **exclusively to a loopback target**.  If resolution involves a
  non-loopback address, or the future client's destination is not loopback, the outcome is
  `EVIDENCE_INSUFFICIENT` / **CANDIDATE FAIL / P4 UNPROVEN** **before any GET is issued**.
* The proof must resolve the endpoint to the **concrete loopback address and port the future
  HTTP client will use**, deterministically, and bind **that** exact address/port — not
  merely "the host", and not "whichever address answers first".

### 8.3 Address-family / listener ambiguity rule (MANDATORY, fail-closed)

`localhost` may resolve to IPv4 (`127.0.0.1`) and/or IPv6 (`::1`), and several processes may
share a wildcard listener.  The proof must tie the future HTTP destination to **one**
listener PID deterministically and must **fail closed** when:

* hostname resolution yields multiple possible address families **and** they map to
  **different** listener processes (or the client's address-family choice is not
  deterministic);
* wildcard/listener ownership is ambiguous, or a wildcard bind is shared by several
  processes;
* more than one incompatible listener could answer the resolved address/port;
* the future HTTP destination cannot be deterministically tied to exactly one listener PID
  (missing or unresolvable listening-socket ↔ PID mapping).

In any of those cases the verdict is **`TARGET_IDENTITY_AMBIGUOUS`** →
`EVIDENCE_INSUFFICIENT` → **CANDIDATE FAIL / P4 UNPROVEN**.  **No GET is issued**, no
candidate listener may be chosen arbitrarily, no address family may be "tried" to see which
one responds, and the attempt is **not** harness-invalid (§17.1).

### 8.4 Package declared-bin binding (MANDATORY)

The proof must, in this order:

* **A.** read the installed `opencode-ai` package metadata (the `package.json` at the
  installation root that owns the listener executable);
* **B.** verify `name == opencode-ai` **and** `version == 1.18.11` (exact strings);
* **C.** resolve its declared bin **`./bin/opencode.exe`** to a **canonical** target
  executable path (absolute; symlinks/junctions/reparse points resolved; separators and case
  normalized as the OS reports them);
* **D.** require **canonical listener `ExecutablePath` == canonical declared-bin executable
  path**, in addition to the executable hash equality of §8.5.

Being merely **inside** the package root is **not** sufficient.  A matching **process name
alone** is **not** sufficient.  Mismatch → **`TARGET_INSTANCE_MISMATCH`** →
`EVIDENCE_INSUFFICIENT` → **CANDIDATE FAIL**; **no GET**.

### 8.5 Executable SHA-256 binding (MANDATORY)

The proof must compute the SHA-256 of

* the **installed target declared-bin executable** (the canonical path resolved in §8.4 C),
  and
* the **executable image/path resolved for the listener process** (§8.6),

and require **`listener_executable_sha256 == target_declared_bin_sha256`**.  Canonical path
equality (§8.4 D) **and** executable hash equality are **both** required; either one alone is
insufficient.  Mismatch → **`TARGET_INSTANCE_MISMATCH`** → `EVIDENCE_INSUFFICIENT` →
**CANDIDATE FAIL**; **no GET**.  Hashing is a local read-only file operation: it executes
nothing, starts nothing and issues no HTTP.

### 8.6 Process creation/start identity (MANDATORY on the accepted Windows proof environment)

Local read-only process creation identity is available on the accepted Windows proof
environment, so it is **required**, and the proof must record at minimum:

* `PID`;
* `ExecutablePath` (canonical, §8.4);
* executable SHA-256 (§8.5);
* **process creation/start timestamp from OS process metadata**.

This timestamp is **not** operation-correlation evidence, is **not** the `reply_boundary`
cursor and is **not** a P9-style timestamp semantic; it is **only** local process-instance
identity evidence for the before/after continuity check (§8.8).  If creation/start identity
cannot be obtained → **`TARGET_IDENTITY_UNRESOLVED`** → `EVIDENCE_INSUFFICIENT` →
**CANDIDATE FAIL**.  The field may **not** be silently dropped, and "not available" is
**not** an accepted answer.

### 8.7 Pre-request responder snapshot and `TARGET_BOUND` precondition (MANDATORY)

**Before** the single `GET /doc`, the proof must freeze from local read-only metadata:

* configured endpoint; resolved concrete loopback address; port;
* listener PID; canonical listener `ExecutablePath`; listener executable SHA-256;
* listener process creation/start identity;
* target package evidence: package name; package version; package root; declared bin;
  canonical target executable path; target executable SHA-256;
* the pre-binding verdict.

**`TARGET_BOUND` requires all mandatory equality/identity checks of §8.1–§8.6 to pass.**  If
`TARGET_BOUND` is not established:

* **no `GET /doc` is issued** (0 loopback HTTP requests);
* the outcome is a **semantic G0.4 failure** — `EVIDENCE_INSUFFICIENT`, **CANDIDATE FAIL /
  P4 UNPROVEN** — **not** harness-invalid, **not** retryable, and **not** a reason to try
  another endpoint, address family or server.

### 8.8 Post-request responder continuity snapshot (MANDATORY)

**Immediately after** the single future `GET /doc` completes — in **any** outcome, including
a non-2xx response, an authorization rejection, or a malformed/absent schema — the proof must
take a **second** local OS-metadata snapshot of the **exact configured endpoint/listener**
and record again:

* resolved concrete endpoint; listener PID; canonical `ExecutablePath`; listener executable
  SHA-256; listener process creation/start identity.

Equality with the pre-request snapshot (§8.7) is **required**: same resolved endpoint, same
PID, same canonical executable, same executable SHA-256, same process creation/start
identity.  If **any** of them differs → **`TARGET_INSTANCE_CHANGED`** →
`EVIDENCE_INSUFFICIENT` → **CANDIDATE FAIL / P4 UNPROVEN**.  The already-issued GET
**counts** as the one permitted GET: **no second GET**, no re-binding to the new responder,
no retry, no "stable responder" search.

### 8.9 Fixed execution order (future proof)

1. **STEP 1** — derive installed target package/bin identity (§8.4, §8.5 statics).
2. **STEP 2** — resolve the configured DevRelay endpoint to the concrete loopback
   destination (§8.2, §8.3).
3. **STEP 3** — perform pre-request responder binding and freeze the snapshot (§8.6, §8.7).
4. **STEP 4** — **if and only if** `TARGET_BOUND`: perform **exactly one** `GET /doc`.
5. **STEP 5** — perform the mandatory post-request responder continuity snapshot (§8.8).
6. **STEP 6** — **if and only if** target continuity holds: perform the offline cases C–H
   against the single captured schema.

Consequences:

* if **STEP 3** fails: **0 GETs issued**; semantic FAIL (`EVIDENCE_INSUFFICIENT`).
* if **STEP 4** was issued and **STEP 5** fails: **1 GET counted**; **0 additional GETs**;
  semantic FAIL (`TARGET_INSTANCE_CHANGED`).

No alternate responder, no alternate endpoint, no second server, no rerun for a stable
responder.

### 8.10 `/doc` version/build metadata role (corroboration only)

* Version/build metadata exposed by the captured `/doc` document is **corroboration only** —
  never primary identity, never a substitute for the local chain of §8.4–§8.7.
* If it **contradicts** the local binding → **`SCHEMA_CONTRADICTION` /
  `TARGET_INSTANCE_MISMATCH` → FAIL**.
* If `/doc` exposes **no** identity metadata, that alone is **not** a failure: target
  identity is established through the mandatory local binding chain.

### 8.11 Runtime posture (proof-harness only; no runtime change)

Endpoint/listener/process inspection defined here is **PROOF-HARNESS ONLY**.  It does **not**
authorize DevRelay runtime to scan ports, scan processes, discover OpenCode, pick servers
dynamically, change endpoints, or use PID/executable metadata for orchestration.  Nothing in
this definition, and nothing in the future proof, changes any runtime behaviour; the
"explicit endpoint, no port/process scanning" posture stands.

## 9. Fixed future case matrix (exactly A–H; one live probe total)

| Case | Content | Precommitted expectation / outcome |
| --- | --- | --- |
| **G0.4-A — INSTALLED TARGET IDENTITY AND RUNNING-SERVER BINDING** | complete the mandatory read-only binding chain of §8.1–§8.7 against the exact configured endpoint and establish all ten required findings A1–A10 (§9.1): package identity, declared-bin resolution, canonical-path equality, executable SHA-256 equality and process creation/start identity | `TARGET_BOUND` / `IDENTITY_MATCH_AND_BOUND`; **any** unresolved, ambiguous or mismatched field → **CASE FAIL / `EVIDENCE_INSUFFICIENT`** (`TARGET_INSTANCE_MISMATCH`, `TARGET_IDENTITY_AMBIGUOUS` or `TARGET_IDENTITY_UNRESOLVED` recorded as the reason) with **no `GET /doc` issued** |
| **G0.4-B — CURRENT `/doc` CAPTURE FROM BOUND TARGET** | precondition case A == `TARGET_BOUND`; then the single authorized read-only loopback `GET /doc`, followed by the mandatory post-request responder-continuity snapshot (§8.8).  Case B requires **both** B1 (the existing `SCHEMA_AVAILABLE` / schema-validity requirements) **and** B2 (`POST_REQUEST_TARGET_CONTINUITY == SAME_BOUND_TARGET`) | B1 fails → **FAIL**; B2 differs → **CASE FAIL / `EVIDENCE_INSUFFICIENT`** (`TARGET_INSTANCE_CHANGED`; the already-issued GET counts, **no second GET**); both pass → case B may pass; `/doc` identity metadata contradicting the local chain → **FAIL** (`SCHEMA_CONTRADICTION` / `TARGET_INSTANCE_MISMATCH`, §8.10) |
| **G0.4-C — SESSION STATUS CONTROL** | inspect `/session/status` and the `SessionStatus` schema | characterize `SESSION_LEVEL_ONLY` or an operation-specific resource; historical expectation `SESSION_LEVEL_ONLY`, but the conclusion must rest on current schema evidence |
| **G0.4-D — SYNCHRONOUS MESSAGE ROUTE** | inspect `POST /session/{id}/message` request/response schemas from `/doc` only (no POST executed) | determine whether the schema returns any candidate operation handle distinct from ordinary session/message ids |
| **G0.4-E — `PROMPT_ASYNC` ROUTE** | inspect `POST /session/{id}/prompt_async` schema from `/doc` only (never invoked) | characterize request schema, response schema, returned identifiers, whether any returned identifier is operation-specific, and whether a read-only durable lookup route exists for it; route existence alone is not a qualifying handle |
| **G0.4-F — EVENT SURFACES** | inspect `/event` and `/global/event` schemas only (never subscribed) | characterize `requestID`, `request_id`, event identifiers and resource references, and determine whether they are merely event payload metadata or whether a durable read-only operation lookup exists; ephemeral event correlation alone does not qualify |
| **G0.4-G — IDENTIFIER TRACEABILITY** | for every candidate identifier discovered in C–F: trace all current `/doc` routes/schemas for a read-only API resource that can later resolve that identifier to the same operation's pending/result state | classify each candidate against **all** qualifying-handle requirements |
| **G0.4-H — COMPLETENESS / NEGATIVE CONTROL** | search the **complete** current `/doc` path/schema set (not only expected route names) for any other operation/request/task/job/run/prompt handle capable of qualifying | the absence conclusion may be made **only** after this complete schema sweep |

### 9.1 Case G0.4-A — required findings (all ten mandatory)

| # | Required finding |
| --- | --- |
| **A1** | installed package name == `opencode-ai` |
| **A2** | installed package version == `1.18.11` (exact) |
| **A3** | declared bin `./bin/opencode.exe` resolves to a canonical target executable path |
| **A4** | the configured DevRelay endpoint resolves to a **loopback** destination only (else fail before any GET, §8.2) |
| **A5** | the exact concrete endpoint has an **unambiguous** single listener (§8.3; `localhost` IPv4/IPv6 ambiguity is fail-closed) |
| **A6** | that listener's **PID** is identified |
| **A7** | listener canonical executable path **==** target declared-bin canonical executable path (§8.4) |
| **A8** | listener executable SHA-256 **==** target executable SHA-256 (§8.5) |
| **A9** | listener **process creation/start identity** obtained from OS process metadata (§8.6) |
| **A10** | **pre-request responder snapshot frozen** (§8.7) and `TARGET_BOUND` established |

Expected result: **`TARGET_BOUND` / `IDENTITY_MATCH_AND_BOUND`**.  **Any** unresolved,
ambiguous or mismatched field is **CASE FAIL / `EVIDENCE_INSUFFICIENT`** — never "close
enough", never PASS-A/PASS-B, and never a harness-invalid attempt.

### 9.2 Case G0.4-B — required findings (both mandatory)

* **B1** — the schema-validity requirements already defined for this case
  (`SCHEMA_AVAILABLE`: a parseable OpenAPI/schema document, with the recorded schema hash,
  path count and schema/component count).
* **B2** — `POST_REQUEST_TARGET_CONTINUITY == SAME_BOUND_TARGET` (§8.8): the post-request
  responder snapshot equals the pre-request snapshot on resolved endpoint, PID, canonical
  executable path, executable SHA-256 and process creation/start identity.

If B1 fails → **FAIL**.  If B2 fails → **FAIL** (`TARGET_INSTANCE_CHANGED`).  Only if both
hold may case B pass.

## 10. Future outcome set (exactly one conclusion)

* `CHARACTERIZED_NO_DURABLE_PER_OPERATION_HANDLE`
* `CHARACTERIZED_HANDLE_PRESENT_BUT_OUT_OF_SCOPE_FOR_V03E`
* `EVIDENCE_INSUFFICIENT`
* `SCHEMA_CONTRADICTION`

No fuzzy partial-success verdict is permitted, and **no fifth verdict is invented** for the
binding: an unbound, ambiguous, unreachable, unresolved or changed responder maps to
`EVIDENCE_INSUFFICIENT`, i.e. **CANDIDATE FAIL / P4 UNPROVEN** — never PASS-A and never
PASS-B.  The binding reasons

* **`TARGET_INSTANCE_MISMATCH`** — wrong package, wrong version, declared-bin mismatch, wrong
  executable, or executable hash mismatch (subsumes the revision-2 label `TARGET_MISMATCH`);
* **`TARGET_IDENTITY_AMBIGUOUS`** — address-family / listener ambiguity (§8.3);
* **`TARGET_IDENTITY_UNRESOLVED`** — a mandatory identity field (e.g. process
  creation/start identity) could not be obtained;
* **`TARGET_INSTANCE_CHANGED`** — post-request responder-continuity failure (§8.8);

are **reasons/subclassifications recorded under `EVIDENCE_INSUFFICIENT`**.  They are **not**
new fifth/sixth/seventh final verdicts, and the final outcome set remains exactly the four
listed above.  The two characterization verdicts are reachable **only** for a target instance
that is **both** pre-request bound and post-request continuity-confirmed (§11).

## 11. PASS semantics (both conclusions are fully-evidenced characterizations)

**Global PASS precondition (applies to PASS-A and PASS-B alike):** neither PASS outcome may
be produced unless **both** of these hold:

* `PRE_REQUEST_TARGET_BOUND` — the mandatory binding chain of §8.1–§8.7 succeeded against
  the exact configured endpoint (case G0.4-A == `TARGET_BOUND`); **and**
* `POST_REQUEST_SAME_TARGET_CONFIRMED` — the post-request responder snapshot equals the
  pre-request snapshot (§8.8), so the schema analyzed in cases C–H demonstrably came from
  that same bound target instance.

A schema-only inspection that lacks either half is `EVIDENCE_INSUFFICIENT` — never PASS-A and
never PASS-B.  Without the pre-request half no GET is issued at all (§8.7); if the GET was
issued and the post-request half fails, the run is a semantic FAIL with exactly one GET
counted and **no** additional GET (§8.8, §8.9).

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

This rule applies only to a target instance that is **both** pre-request bound (§8.7) **and**
post-request continuity-confirmed (§8.8).  If a candidate handle is found, the proof must not
stop at its name.  To conclude
`CHARACTERIZED_HANDLE_PRESENT_BUT_OUT_OF_SCOPE_FOR_V03E` it must establish **all**
qualifying dimensions (operation-specific, OpenCode-owned, post-call observable,
read-only-queryable/durably resolvable, no timestamp/order heuristic required).  If any
durability/specificity/queryability dimension is unresolved, the result is
`EVIDENCE_INSUFFICIENT`, **not** `HANDLE_PRESENT`.

## 13. Handle-absent rule

This rule applies only to a target instance that is **both** pre-request bound (§8.7) **and**
post-request continuity-confirmed (§8.8).  To conclude
`CHARACTERIZED_NO_DURABLE_PER_OPERATION_HANDLE` the proof must: successfully
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

Binding-chain failures of §8.2–§8.8 (non-loopback, ambiguous, unresolved, mismatched or
changed responder) are semantic failures of this class, **not** harness defects; the
precommitted list is §17.1.

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
written because of a proof-harness bug before response validation.

The harness-invalid boundary remains **narrow**: binding mismatch or ambiguity is **not** a
harness defect, listener disappearance is **not** a harness defect, responder replacement is
**not** a harness defect, and no rerun may be performed "to obtain a stable responder" or
"to try the other address family".  The following are **not** harness-invalid and **count**
as semantic evidence outcomes: the server returns 404; authorization rejects the GET; the
schema is malformed; a route is missing; an expected field is absent; candidate identifier
semantics remain unresolved; and every item of §17.1.

### 17.1 Binding-related semantic failures (precommitted; these COUNT and may not be retried)

The following binding outcomes are **semantic evidence outcomes**, never harness-invalid,
and may **not** be retried, re-scoped or reported as harness defects:

* non-loopback endpoint; no listener at the resolved address/port;
* ambiguous listener; `localhost` IPv4/IPv6 listener ambiguity; wildcard/multi-process
  listener-ownership ambiguity; more than one incompatible listener able to answer;
* unresolvable PID; missing `ExecutablePath`;
* wrong package; wrong version; declared-bin mismatch; wrong executable;
  executable SHA-256 mismatch;
* missing process creation/start identity; unreadable or unparsable package metadata;
* desktop responder; unknown installation; pre-request `TARGET_BOUND` failure;
* post-request PID change; post-request executable change; post-request hash change;
  post-request process-start-identity change; `TARGET_INSTANCE_CHANGED`.

Each maps to `EVIDENCE_INSUFFICIENT` (**CANDIDATE FAIL / P4 UNPROVEN**) for the accepted
target, with the specific reason recorded as in §10.

## 18. Evidence requirements (future proof)

All groups below are **mandatory**; no required target-binding field is optional.

**Target statics:** installed package name; package version; package root; declared bin;
canonical target executable path; target executable SHA-256.

**Config resolution:** configured endpoint; resolved concrete loopback address; port; the
loopback-only verdict (§8.2); the listener-unambiguity verdict (§8.3).

**Pre-GET snapshot:** listener PID; listener canonical executable path; listener executable
SHA-256; listener process creation/start identity; pre-binding verdict (`TARGET_BOUND` or the
failure reason).

**GET:** `/doc` HTTP status; `/doc` media type; full schema hash; path count;
schema/component count.

**Post-GET snapshot:** listener PID; listener canonical executable path; listener executable
SHA-256; listener process creation/start identity; post-binding continuity verdict
(`SAME_BOUND_TARGET` or `TARGET_INSTANCE_CHANGED`).

**Global verdicts:** `TARGET_BOUND` verdict; `TARGET_CONTINUITY` verdict; final
characterization verdict; capability consequence; provider/model count; external-network
count; loopback GET count; OpenCode start/restart count; repository identity.

**API/schema evidence (as previously defined):** candidate route list; candidate identifier
list; per-identifier qualifying-dimension matrix; complete path/schema search method;
session-status finding; sync-message schema finding; `prompt_async` schema finding;
event/global-event schema finding; `wait_idle` control finding; DevRelay-local-id control
finding.

**Corroboration only:** any version/build metadata exposed by the captured `/doc` document
(§8.10).

A required field that cannot be obtained is reported as such **and** carries the
corresponding failure reason of §17.1 — it may never be silently dropped.

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

Both boundaries below apply **only to the instance bound in case G0.4-A** (the named
accepted target of §1).  They never extend to another installation on the host (for
example the desktop build), to an unbound responder, or to any instance characterized
without the §8.1 binding.

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

This file defines a proof; it proves nothing.  It contains **no** G0.4 observed result, it
does not execute the inspection, it issues no HTTP request and does not read `/doc`, it
starts no OpenCode server, and it changes no runtime behaviour.  Revision 3 defines a
complete binding chain but performs none of it in this round: it resolves no endpoint, takes
no listener or process snapshot, queries no process, reads no package metadata and computes
no executable hash.  It does not make P4 proven, does not make G0.4 pass, does not mark this
revision accepted, and does not authorize implementation, adoption, retry or any capability
change.  `G0.4` remains `NOT RUN` until a separately executed proof is independently
approved.

## 25. Revision history

* **Revision 1** — `abd677a` (`docs(v03e): define G0.4 API-inspection proof`, parent
  `f41b7a1`): the initial pre-run definition candidate; SHA-256
  `7895ab1fa3ef918cd67cd1be3a25fde8b5c8907a353a35d6496488ca29532319`.
  Independent review decision: **`REQUEST_CHANGES — V0.3-E G0.4 PROOF DEFINITION`** with
  **P0 = 0, P1 = 1, P2 = 0, P3 = 3**.  Five of the six readiness gaps were accepted as
  closed; the blocking P1 was the missing fail-closed binding between the `/doc` responder
  and the accepted OpenCode 1.18.11 target (the review verified with read-only local
  metadata that this host runs a *different* installation — the desktop build — while the
  named target is the npm `opencode-ai` 1.18.11 package).  P3 notes: name the binding step
  as its own case; state that local port/process metadata is proof evidence only; and
  state that a non-matching/unbound instance is INCONCLUSIVE/FAIL and that characterizing
  another instance needs its own authorized definition.
* **Revision 2** — `5cb03a8` (`docs(v03e): bind G0.4 /doc inspection to the accepted
  target (revision 2)`, parent `abd677a`): added the mandatory §8.1 binding, extended case
  G0.4-A to `INSTALLED IDENTITY AND RUNNING-SERVER BINDING`, mapped unbound/`TARGET_MISMATCH`
  to `EVIDENCE_INSUFFICIENT` (never PASS), made the binding evidence mandatory in §18, scoped
  the claim boundaries to the bound instance (§23), recorded the non-claims (§24) and folded
  in the three P3 notes of the revision-1 review.  No runtime semantics, budgets, probe
  discipline or frozen policy changed.  SHA-256 (committed blob)
  `f34408fe2ff314f0b0cfbcbf34d57197c18f151f507ce8dee2771ad00af464bc`.
  Independent review decision: **`REQUEST_CHANGES — V0.3-E G0.4 PROOF DEFINITION REVISION 2`**
  with **P0 = 0, P1 = 2, P2 = 0** — **P1-1** no mandatory post-`/doc` responder-continuity
  verification; **P1-2** binding-chain ambiguity/incompleteness (ambiguous listener /
  `localhost` IPv4-IPv6 not fail-closed; declared bin not required to resolve to the listener
  executable; executable SHA-256 equality not required).  Revision 2 was **rejected**; the
  review otherwise accepted the target concretization, characterization model,
  PASS-A/PASS-B, durability definition, A–H matrix, one-`/doc` budget, no-probe-shopping rule
  and the frozen report-only policy.
* **Revision 3** — this revision (drafted on `5cb03a8`): closes **only** P1-1 and P1-2 plus
  associated wording — mandatory post-request responder-continuity snapshot (§8.8), exact
  configured endpoint rule (§8.2), fail-closed address-family / listener-ambiguity rule
  (§8.3), mandatory declared-bin binding (§8.4), mandatory executable SHA-256 equality
  (§8.5), mandatory process creation/start identity (§8.6), pre-request snapshot and
  `TARGET_BOUND` precondition (§8.7), fixed six-step execution order (§8.9), `/doc` metadata
  role (§8.10), runtime posture restatement (§8.11), explicit case A findings A1–A10 and case
  B findings B1–B2 (§9.1, §9.2), global PASS precondition (§11), binding failure list
  (§17.1), expanded mandatory evidence fields (§18) and the committed-blob hash convention
  (§26).  Nothing accepted by the revision-2 review is reopened or weakened; revisions 1 and
  2 both remain **rejected** and neither is approved.  This revision must itself be
  independently re-reviewed before any execution, and execution still requires a separate
  authorization.  Its committed-blob SHA-256 is recorded in the revision-3 remediation
  report (a file cannot embed the hash of the blob that contains it).

## 26. Document hash convention (committed blob)

**Authoritative document SHA-256 = SHA-256 of the committed Git blob bytes**, not the
platform-normalized working-tree representation.  This repository sets `* text=auto` and
`*.md text eol=lf`, so on Windows a clean working-tree Markdown file may contain CRLF while
the committed blob contains LF; hashing the working-tree file can therefore produce a *false
mismatch* against a hash taken from the commit.  Convention for this oracle and for future
proof artifacts:

* record the **committed blob** hash as authoritative proof identity — e.g.
  `git show <commit>:<path> | sha256sum`;
* a working-tree/CRLF hash may be recorded **in addition** only when explicitly labelled as
  such, and it never substitutes for the blob hash;
* revision-1 blob hash:
  `7895ab1fa3ef918cd67cd1be3a25fde8b5c8907a353a35d6496488ca29532319`; revision-2 blob hash:
  `f34408fe2ff314f0b0cfbcbf34d57197c18f151f507ce8dee2771ad00af464bc`; the revision-3 blob
  hash is recorded in the revision-3 remediation report rather than embedded here.
