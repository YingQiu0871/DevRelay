# DevRelay v0.3-E — G0.5-PRE / SIC session-incarnation capability finding (definition candidate)

**Status: DEFINITION CANDIDATE — SIC = `NOT RUN / DEFINITION CANDIDATE / AWAITING INDEPENDENT RE-REVIEW`.**  This document is **not** accepted and **not** frozen, and it **executes nothing**.  The first independent definition review returned **`REQUEST_CHANGES — V0.3-E G0.5-PRE / SIC DEFINITION`** (P0 = 0, P1 = 1, P2 = 3); the framing, status model, outcome model, §25.1 preservation, G0.4 separation, G1/G2 separation and zero-budget rules were **accepted**, and this revision remediates **only** the blocking findings — **P1** positive semantic authority, **P2-A** `NOT_EXPOSED` coverage, **P2-B** mode precommit and **P2-C** actual destination/responder binding (with the associated no-alternate-endpoint and continuity rules).  The non-blocking P3 items are deliberately **not** addressed.  No oracle exists and no inspection has been performed.

**What SIC is.**  A **new prerequisite information finding** outside the existing P1–P9
ladder, introduced because the independently approved Case-C design block
(*APPROVE V0.3-E CASE-C PREREQUISITE DESIGN BLOCK*) confirmed the stronger thesis
**`BLOCKED — NO SOUND ORIGINAL-SESSION PROVENANCE ANCHOR AVAILABLE`**: no currently accepted
evidence source can soundly support **ORIGINAL OWNERSHIP PROVEN** for adoption.

**What SIC is not.**  SIC is **not** G0.5, **not** G1, **not** G2, **not** G0.4, **not** a new
P-number, **not** a proof of P6, **not** an adoption-enabling proof, and **not** an
implementation authorization.  It is an information prerequisite only.

## 1. Identity and baseline

| Item | Value |
| --- | --- |
| Definition baseline HEAD | `b44004325093bb148f052261ab10d7760acc4ef4` |
| Branch | `v0.3-e-recovery-reconciliation` |
| Accepted §25.1 block SHA-256 (immutable input) | `d3244ee0d24f5d740b34dac358378870d4d8238b0755787cffb7313d01044ee0` |
| G0.5 / P6 status (unchanged by SIC) | `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP`; P6 = `UNPROVEN / UNSATISFIED` |
| G0.4 / P4 status (closed; unrelated) | `AUTHORITATIVE FAIL / P4 UNPROVEN / CLOSED` |
| G1 / G2 | `NOT RUN` (no work authorized or performed) |
| Implementation | `NOT AUTHORIZED` |

## 2. Exact question the future finding must answer

> Does OpenCode 1.18.11 expose, through a read-only session representation available to
> DevRelay, a **per-session-incarnation identity/property** (or well-defined tuple) with
> semantics sufficient to distinguish **the original remote session incarnation** from a
> **recreated/replaced/reused session** that may present the same `session_id` and the same
> apparent workspace?

The candidate anchor must provide authority **beyond**: `session_id` equality; workspace
equality; route/model/agent equality; ledger presence; local timestamps; a purely local
nonce; local metadata fingerprints.

## 3. Required semantic properties of a qualifying anchor

A field or tuple may qualify only if the future evidence can establish **all** of:

* **A. SESSION-SCOPED** — the value identifies/binds a specific session record/incarnation,
  not merely the server, workspace, project, route or process.
* **B. INCARNATION-SENSITIVE** — a recreated/replaced/new session incarnation must not be
  legitimately indistinguishable under the anchor merely because it reuses the same
  `session_id`/workspace.
* **C. STABLE FOR THE SAME INCARNATION** — the value remains suitable for comparison across
  the recovery interval for the same session incarnation.
* **D. READ-ONLY OBSERVABLE** — DevRelay can obtain it without mutating the session.
* **E. LOCALLY PERSISTABLE** — DevRelay can store the anchor at binding time and compare it
  at recovery time.
* **F. SEMANTICALLY ESTABLISHED** — its meaning is supported by **observable contract
  evidence** as defined in §3.1 (an explicitly declared/documented contract semantic from an
  authoritative surface associated with the exact installed target, whose declared behaviour
  may be checked for runtime consistency against that target) — **not** by its name, a binary
  string occurrence, a single sample, repeated samples, or any purely empirical observation.
* **G. NOT DEPENDENT ON UNPROVED P2/P3/P8/P9 SEMANTICS** — unless this finding explicitly
  concludes that such a dependency exists, in which case the anchor is **NOT AVAILABLE NOW**.

### 3.1 Observable contract evidence, and the limits of runtime observation (P1)

**OBSERVABLE CONTRACT EVIDENCE** means an **explicitly declared or documented contract
semantic** from an **authoritative surface associated with the exact installed target**, whose
declared behaviour **may be checked for runtime consistency** against that target.  It must
**not** mean empirical observation alone.

**Runtime observations / response examples may support only:** field existence at runtime;
runtime exposure; target/version consistency; response shape/type consistency; and consistency
with an already-declared contract.

**Runtime observations alone may never establish:** immutability; incarnation sensitivity;
session-incarnation scope; non-reuse; uniqueness; stability guarantees; provenance guarantees;
or any other platform semantic required for `SIC_PRESENT_AND_SEMANTICS_ESTABLISHED`.

**Sufficiency rules (frozen):** one sample is insufficient; **multiple samples are also
insufficient**; **repeated stable observations are insufficient**; and **different values
across multiple sessions are insufficient** — unless an **authoritative declared semantic
independently establishes what those observations mean**.

## 4. Non-qualifying evidence (frozen as insufficient by itself)

`session_id`; workspace; `workspace_match`; `run.workspace`; `parent_id` without proven
semantics; `updated_at`; any created-like timestamp without proven semantics; `title`;
`agent`; `model`; `state`; `route_snapshot`; `route_source`; `run_id`; `call_id`; ledger
presence; prompt digest; message timestamps; `health.version`; a purely local nonce; and any
hash/fingerprint over these fields.  These may be reopened **only** if genuinely new platform
semantics are established — never by re-labelling them.

## 5. Semantic outcomes (exactly four)

* **`SIC_PRESENT_AND_SEMANTICS_ESTABLISHED`** — requires **both**:
  **A.** the candidate field/tuple is **actually exposed** through the authorized
  target/contract surface; **and**
  **B.** **authoritative declared semantics** establish **all** required qualifying-anchor
  properties (§3).
  Runtime observations may verify **consistency with B**, but they **cannot supply B**.  If a
  field exists but the required declared semantics are absent, the result **must** be
  `SIC_METADATA_PRESENT_BUT_SEMANTICS_UNPROVEN`; **no empirical promotion to a positive result
  is permitted**.
* **`SIC_METADATA_PRESENT_BUT_SEMANTICS_UNPROVEN`** — candidate metadata exists/is exposed
  (including when runtime exposure is demonstrated), but its immutability/scope/incarnation
  semantics are not sufficiently established by authoritative declared semantics.
* **`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`** — the exact **successfully inspected,
  precommitted** authorized contract surface exposes no candidate metadata satisfying the
  discovery rule; **complete coverage is required and no global generalization is permitted
  (§5.1)**.
* **`SIC_EVIDENCE_INSUFFICIENT`** — the authorized method cannot reach enough authoritative
  evidence to answer the question, **including** any inspection whose authorized surface is
  partial, unreachable, truncated, ambiguous or incompletely parsed (§5.1, §6).

**"Not found" and "not proven" must never be collapsed.**  A field that exists without
established semantics is the second outcome, never the first.

### 5.1 Coverage rules for `SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT` (P2-A)

* **RULE 1 — COMPLETE COVERAGE REQUIRED.**  This outcome is legal **only** if the precommitted
  authorized inspection surface was **completely and successfully inspected** according to the
  frozen oracle, with **no unresolved ambiguity about coverage**.  If the required surface is
  partial, unreachable, truncated, ambiguous, incompletely parsed, or otherwise **not
  authoritatively covered**, the result **must** be `SIC_EVIDENCE_INSUFFICIENT` — **not**
  `SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`.
* **RULE 2 — GLOBAL NEGATIVE NON-CLAIM.**  `SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT` means
  **only** that the exact successfully inspected, precommitted contract surface exposes no
  candidate metadata satisfying the discovery rule.  It **must not** mean that OpenCode
  globally has no session-incarnation metadata, and it **must not** be generalized beyond the
  inspected surface and version.

## 6. Harness-invalid boundary

`HARNESS_INVALID` is **not** a semantic result: it applies only when the future inspection
fails **before reaching its precommitted evidence surfaces** for a harness/environment
reason (for example, the inspection runner cannot execute, or a declared static artifact
cannot be read for an environment reason).  No semantic outcome may be retried to obtain a
better result, and harness-invalid attempts must be recorded separately and excluded from the
semantic count.  **Once the semantic inspection has begun**, incomplete or ambiguous
authoritative coverage that prevents a sound global result maps to
`SIC_EVIDENCE_INSUFFICIENT` (§5.1), unless the attempt qualifies under the already-frozen
harness-invalid boundary **before** the semantic assertion point.  `HARNESS_INVALID` must
**never** be used to hide an incomplete semantic inspection.

## 7. Positive-result consequence (no shortcut)

`SIC_PRESENT_AND_SEMANTICS_ESTABLISHED` does **not** prove P6, does not by itself make the
G0.5 oracle freezable, and does not enable adoption.  It establishes only that a sound
Case-C product design **may now be possible**.  The remaining chain is unchanged and
sequential:

minimal Case-C enforcement-slice design → independent design review → separate
implementation authorization → implementation → independent implementation review →
G0.5 pre-run oracle freeze → G0.5 execution/review.

## 8. Non-positive-result consequence

If the outcome is `SIC_METADATA_PRESENT_BUT_SEMANTICS_UNPROVEN`,
`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT` or `SIC_EVIDENCE_INSUFFICIENT`, then **no Case-C
implementation may be designed by inventing provenance**; G0.5 remains blocked.  The owner
must later choose among separately reviewed options such as: another justified platform
capability route; a DevRelay-controlled session-creation capability/design change; or an
explicit product-scope change for capability C.  **This finding must not select those
automatically.**

## 9. Separation from G0.4

G0.4/P4 asked whether a **durable per-operation pending handle** exists; G0.5-PRE / SIC asks
whether a **read-only per-session-incarnation provenance property** exists with sufficient
semantics.  They are different questions with different evidence surfaces.  G0.4 remains
`AUTHORITATIVE FAIL / P4 UNPROVEN / CLOSED`; its oracle and proof are not modified by SIC and
are not reopened.

## 10. Separation from G1 / G2

G1/P1 owns restart/history durability; G2 owns P2 text fidelity, P3 prompt/completion
uniqueness, P8 session exclusivity and P9 timestamp/order fidelity.  SIC does **not** replace
them and must not count future proof assumptions as present evidence.  If a candidate
anchor's semantics would require one of those future proofs, the anchor is classified as
**not currently established** and the dependency is recorded explicitly.

## 11. Read-only method only

The future SIC finding is **read only**.  Forbidden: prompt submission; writing marker
messages; any session mutation; session creation/deletion; interrupt; provider inference;
fake provider; mutating a live OpenCode database for test purposes.  A marker/write-back
design is **outside** this finding.

## 12. Platform target

Target: the installed OpenCode package/product **1.18.11**.  Execution must **re-verify**
identity at run time and must record package identity, binary/path identity, version and
artifact hash as applicable; inspecting a different OpenCode version is not authorized and
must stop the run rather than silently retarget.

## 13. Authorized evidence classes (designed here; none executed)

* **A.** installed package static artifacts / bundled schemas / generated clients;
* **B.** official or bundled OpenAPI/schema/documentation reachable from the exact installed
  target;
* **C.** the exact read-only session representation/schema from the installed target (this is
  the class that may require a live local endpoint — see §15);
* **D.** official field semantics available from local/bundled documentation;
* **E.** read-only response examples **as supporting evidence only** — limited exactly as
  §3.1 freezes (existence/exposure/consistency, never semantics by themselves).

Broad web research is **not** authorized as semantic proof unless separately justified.  The
future pre-run oracle must freeze the exact subset it will use.  Nothing is executed in this
definition round.

## 14. Static binary/string limitation

Binary/string/token occurrences may be used **only to locate possible surfaces**.  They may
**not** establish field existence in a public contract, immutability, scope, uniqueness,
incarnation semantics or reuse behaviour.  String counts alone can **never** yield
`SIC_PRESENT_AND_SEMANTICS_ESTABLISHED`.

## 15. Static vs live evidence (corrected — P1)

Authoritative **static/bundled contract evidence MAY be sufficient for SIC** if it establishes
**all** required semantic criteria (§3) **and** the applicability of that contract to the exact
installed target.

A **live local read-only inspection MAY be needed only** to establish or verify: runtime
exposure; installed-target applicability; response/schema consistency; and target
identity/continuity.

**A live inspection MUST NOT manufacture semantic authority that is absent from the declared
contract.**  Therefore, if metadata is exposed live but **no authoritative semantic contract
establishes the required incarnation properties**, the result is
**`SIC_METADATA_PRESENT_BUT_SEMANTICS_UNPROVEN`** — never a positive result, because runtime
observation is limited exactly as frozen in §3.1 (one sample, multiple samples, repeated
stable observations and cross-session differences are **all** insufficient without an
authoritative declared semantic).

It must **not** be stated or implied that "runtime properties are decisive, therefore live
observation can prove incarnation semantics".  No endpoint was started, contacted or assumed
in this round.  Any live use requires a **separate execution authorization** and the
target-binding contract of §17; the old G0.4 authorization must **not** be reused, and the
historical missing `base_url` must **not** be treated as a repairable precondition under prior
authority.

## 16. `base_url` consequence

The previous G0.4 execution found `opencode.base_url = ""`; that failure remains historical
and closed.  For SIC, this fact is **not** automatically `SIC_NOT_EXPOSED` and **not**
automatically `SIC_EVIDENCE_INSUFFICIENT`.  The future oracle must precommit **exactly one**
inspection mode (§18):

* **Mode A — offline / static only**: authorized class A/B/D (and E as supporting only), zero
  HTTP and zero OpenCode activity.  This mode **may** suffice on its own if the declared
  contract evidence establishes all §3 criteria **and** applicability to the exact installed
  target; and
* **Mode B — live local read-only**: requires a **new** separately authorized exact-target
  endpoint setup, a frozen endpoint, a precommitted request set/count and the §17
  target-binding contract.  It may **only** establish or verify runtime exposure,
  installed-target applicability, response/schema consistency and target identity/continuity —
  never semantics absent from the declared contract.

Nothing is configured now, and Mode B must not be assumed to be granted.

## 17. Target-binding contract (P2-C; only if a live mode is authorized)

### 17.1 Actual destination and responder binding

The future execution must establish that **the actual HTTP client destination is the exact
frozen concrete endpoint bound to the exact pre-verified listener/process**.  It must freeze
and record at least: concrete **numeric loopback address**; **exact port**; **exact address
family**; **exact scheme**; **exact client destination URI/base**; **one deterministic
listener** bound to that endpoint; **listener PID**; **canonical executable path**;
**executable hash**; **process creation identity** where available; **exact OpenCode version**;
a **pre-request identity snapshot**; and a **post-request continuity snapshot** (§17.3).

The required evidence chain must be exactly one unambiguous chain:

`client destination → frozen endpoint → deterministic listener → verified target process`

A pre/post unchanged process **elsewhere on the host** is insufficient.  If that chain cannot
be established, the evidence is **invalid**.

### 17.2 Listener / address ambiguity — fail closed

If any ambiguity exists in IPv4-vs-IPv6 resolution, `localhost` expansion, wildcard listeners,
multiple listeners, port sharing, multiple candidate PIDs, proxy/forwarder indirection,
responder identity or endpoint resolution, the result is **TARGET BINDING INVALID** and the
future execution must **STOP before any semantic inspection**.  It must not guess which process
answered and must not select one opportunistically.

### 17.3 Post-request continuity

After the final live request, continuity of the **same bound target** must be verified by
comparing at least: endpoint; listener PID; canonical executable path; executable hash;
process creation identity; and version — against the pre-request snapshot.  Any mismatch is a
**target continuity failure → evidence invalid**.  A continuity failure must **not** be
converted into a semantic SIC result.

### 17.4 No alternate endpoint

Exactly the precommitted endpoint may be used.  If it fails, it is forbidden to try another
port, another `localhost` resolution, another address family, another OpenCode instance, the
desktop build, another listener or another `base_url`.  **No endpoint shopping.**  A different
endpoint requires a **new separately authorized execution/oracle**, not continuation of the
current run.

### 17.5 G0.4 lessons reused (without reopening G0.4)

This binding contract explicitly reuses the accepted G0.4 revision-3 lessons: exact endpoint
only; no alternate endpoint; deterministic one-listener binding; address-family/listener
ambiguity fails closed; executable identity chain (canonical path **and** hash); and
pre/post-request continuity.  This does **not** reopen G0.4: `G0.4/P4 = AUTHORITATIVE FAIL /
P4 UNPROVEN / CLOSED` and both G0.4 artifacts remain untouched.  No port/endpoint is frozen
here because none is known before execution.

## 18. No probe shopping and mode precommit (P2-B)

The future inspection is bounded and its **mode is fixed before execution**.  The oracle must
precommit **exactly one** of:

* **MODE A — OFFLINE / STATIC ONLY**;
* **MODE B — LIVE LOCAL READ-ONLY**; or
* **MODE C — PRECOMMITTED BOUNDED STATIC→LIVE TWO-STAGE METHOD**, legal only if deliberately
  designed before execution as follows: exact static surfaces; exact static completion
  criteria; an exact **transition condition defined before execution** (never "static did not
  give the answer we wanted"); exact live endpoint; exact live request set/count; the §17
  target-binding contract; no alternative path after either phase; and the semantic outcome
  mapping.

**MID-RUN MODE SWITCHING IS FORBIDDEN.**  For example, starting Mode A, observing insufficient
evidence and *then* deciding to start OpenCode is invalid; and starting one live strategy,
failing, and then switching to another live strategy is invalid.  Such switching invalidates
the attempt unless the exact staged transition was already frozen in the oracle.

The oracle's mandatory precommit set is: **inspection mode**; authorized evidence surfaces;
candidate-discovery/extraction rule; endpoint (if live); exact request count/set (if live);
transition rule (if staged); candidate evaluation criteria (against the fixed §3 criteria);
target-binding requirements (§17); stop conditions; and semantic outcome mapping.  No
opportunistic switching of mode, endpoint, schema or candidates is permitted.

## 19. Field discovery vs semantic validation

Two separated phases:

* **PHASE A — DISCOVERY**: does the inspected contract expose any candidate per-session
  field/tuple?
* **PHASE B — SEMANTIC VALIDATION**: for each precommitted candidate, is there authoritative
  evidence for the required incarnation properties (§3)?

A candidate discovered without sufficient semantics yields
`SIC_METADATA_PRESENT_BUT_SEMANTICS_UNPROVEN` — **not** a positive result.

## 20. Multiple candidates

The oracle must precommit **all** candidate fields discoverable from the authorized contract
surface **before** semantic verdicting, then evaluate each against the same fixed criteria.  A
global positive result requires **at least one** candidate satisfying **all** required
properties.  New candidates must not be added after observing failures.

## 21. Required future evidence fields

Repository HEAD; branch/worktree; OpenCode version; package/binary identity; binary/artifact
hash; oracle identity; **inspection mode (A / B / C as precommitted)**; authorized evidence surfaces; target-binding evidence (if live);
request count (if any); candidate field/tuple names; where each field is exposed; field type;
session-scope evidence; stability evidence; incarnation-sensitivity evidence; read-only
observability evidence; local-persistability assessment; semantic-authority source;
dependencies on unproved P1/P2/P3/P8/P9; per-candidate verdict; global SIC verdict; activity
counters; privacy/non-claims; harness-invalid vs semantic classification.

## 22. Privacy

The future finding must not persist credentials, tokens, raw prompts, model responses or
reasoning.  If a live read-only session representation is ever required, prefer synthetic or
non-sensitive pre-provisioned session data, and do not inspect user content unless strictly
necessary.

## 23. Zero provider / model budget (frozen)

real provider calls **0**; fake provider calls **0**; model inference **0**; model turns
**0**; prompt submissions **0**; session mutations **0**.  Any future live activity must be
read-only API/schema inspection only.

## 24. Status model

`SIC = NOT RUN / DEFINITION CANDIDATE` → independent definition review → `DEFINITION
ACCEPTED` → separate pre-run oracle candidate → independent oracle review → separately
authorized execution → `CANDIDATE SIC RESULT` → independent result review → authoritative SIC
finding.  The executor never self-approves.

## 25. Relation to G0.5 status

Throughout SIC definition, oracle construction and execution, **G0.5 remains**
`NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP` until a sound
Case-C path actually exists **and is independently reviewed**.  A positive SIC finding alone
does **not** make the G0.5 oracle freezable.

## 26. Relation to implementation authorization

Even if SIC later returns `SIC_PRESENT_AND_SEMANTICS_ESTABLISHED`, implementation remains
**NOT AUTHORIZED**: a new minimal Case-C slice design must first consume the accepted SIC
fact and itself pass independent design review.

## 27. Non-claims of this definition round

This document defines a future finding; it performs none of it.  It starts no OpenCode
instance, issues no HTTP request, reads no `/doc` or `/session` surface, inspects no live
endpoint, configures nothing, implements no Case-C logic, proves nothing about P6, and
changes no status other than recording that SIC exists as a definition candidate.  G0.5, G1
and G2 are unchanged; adoption remains **DISABLED**; implementation remains **NOT
AUTHORIZED**; the accepted §25.1 definition and the G0.4 artifacts are untouched.
