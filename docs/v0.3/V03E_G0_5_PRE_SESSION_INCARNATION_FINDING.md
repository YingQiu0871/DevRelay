# DevRelay v0.3-E — G0.5-PRE / SIC session-incarnation capability finding (definition candidate)

**Status: DEFINITION CANDIDATE — SIC = `NOT RUN / DEFINITION CANDIDATE`.**  This document is
**not** accepted, **not** frozen, and it **executes nothing**.  It becomes the accepted
definition only after a separate independent definition review.  No oracle exists and no
inspection has been performed.

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
* **F. SEMANTICALLY ESTABLISHED** — its meaning is supported by actual
  API/schema/documentation/observable contract evidence, **not** by its name, a binary string
  occurrence, or a single sample.
* **G. NOT DEPENDENT ON UNPROVED P2/P3/P8/P9 SEMANTICS** — unless this finding explicitly
  concludes that such a dependency exists, in which case the anchor is **NOT AVAILABLE NOW**.

## 4. Non-qualifying evidence (frozen as insufficient by itself)

`session_id`; workspace; `workspace_match`; `run.workspace`; `parent_id` without proven
semantics; `updated_at`; any created-like timestamp without proven semantics; `title`;
`agent`; `model`; `state`; `route_snapshot`; `route_source`; `run_id`; `call_id`; ledger
presence; prompt digest; message timestamps; `health.version`; a purely local nonce; and any
hash/fingerprint over these fields.  These may be reopened **only** if genuinely new platform
semantics are established — never by re-labelling them.

## 5. Semantic outcomes (exactly four)

* **`SIC_PRESENT_AND_SEMANTICS_ESTABLISHED`** — a concrete read-only field/tuple is exposed
  **and** evidence establishes the required session-incarnation semantics strongly enough to
  support a future Case-C product design.
* **`SIC_METADATA_PRESENT_BUT_SEMANTICS_UNPROVEN`** — candidate metadata exists/is exposed,
  but its immutability/scope/incarnation semantics are not sufficiently established.
* **`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`** — the exact authorized inspection surfaces
  expose no candidate metadata that could satisfy the criteria.
* **`SIC_EVIDENCE_INSUFFICIENT`** — the authorized method cannot reach enough authoritative
  evidence to answer the question.

**"Not found" and "not proven" must never be collapsed.**  A field that exists without
established semantics is the second outcome, never the first.

## 6. Harness-invalid boundary

`HARNESS_INVALID` is **not** a semantic result: it applies only when the future inspection
fails **before reaching its precommitted evidence surfaces** for a harness/environment
reason (for example, the inspection runner cannot execute, or a declared static artifact
cannot be read for an environment reason).  No semantic outcome may be retried to obtain a
better result, and harness-invalid attempts must be recorded separately and excluded from the
semantic count.

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
* **E.** read-only response examples **as supporting evidence only**, never as semantic proof
  by themselves.

Broad web research is **not** authorized as semantic proof unless separately justified.  The
future pre-run oracle must freeze the exact subset it will use.  Nothing is executed in this
definition round.

## 14. Static binary/string limitation

Binary/string/token occurrences may be used **only to locate possible surfaces**.  They may
**not** establish field existence in a public contract, immutability, scope, uniqueness,
incarnation semantics or reuse behaviour.  String counts alone can **never** yield
`SIC_PRESENT_AND_SEMANTICS_ESTABLISHED`.

## 15. Live-endpoint requirement analysis (definition level)

Class A/B/D evidence can establish *whether a field is declared* and *what bundled
documentation says*, but for the installed build it generally **cannot** establish runtime
exposure, per-session scope, stability across the recovery interval or incarnation
sensitivity — precisely the properties B, C and F of §3.  Therefore answering SIC **may
ultimately require a live local read-only endpoint inspection** (class C).  No endpoint was
started, contacted or assumed in this round.

If a live path is used, static evidence alone was insufficient **because** the decisive
properties are runtime/contract properties of the running target, not declarations in
shipped artifacts.  Any live use requires a **separate execution authorization** and a frozen
target-binding method (§17); the old G0.4 authorization must **not** be reused, and the
historical missing `base_url` must **not** be treated as a repairable precondition under
prior authority.

## 16. `base_url` consequence

The previous G0.4 execution found `opencode.base_url = ""`; that failure remains historical
and closed.  For SIC, this fact is **not** automatically `SIC_NOT_EXPOSED` and **not**
automatically `SIC_EVIDENCE_INSUFFICIENT`.  The future execution definition must declare one
of two modes:

* **Mode A — entirely offline/static**: authorized class A/B/D (and E as supporting only),
  zero HTTP, zero OpenCode activity; or
* **Mode B — live local read-only inspection**: requires a **new** separately authorized
  exact-target local endpoint setup/target-binding precondition, a frozen endpoint, a
  precommitted request count and the §17 binding standard.

The mode is a property of the future oracle, not of this definition; nothing is configured
now, and Mode B must not be assumed to be granted.

## 17. Target-binding standard (if a live mode is ever authorized)

Before any request, the future execution must bind and record: exact OpenCode version;
declared executable identity; binary hash; concrete loopback endpoint; listener/process
binding (PID, canonical executable path, executable hash, creation identity); a **pre-request
identity snapshot**; and — after the last request — a **post-request continuity snapshot**
with equality required on the same fields (any difference = continuity failure, evidence
invalid).  This reuses the G0.4 lessons without reopening G0.4.  No port/endpoint is frozen
here because none is known before execution.

## 18. No probe shopping

The future inspection is bounded.  It is forbidden to try one endpoint, then another, then
another schema, then another metadata guess until a positive result appears.  The future
oracle must precommit: the evidence surfaces; the request count (if any); the endpoint (if
any); the candidate-field evaluation rule; the stop conditions; and the semantic outcome
mapping.

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
hash; oracle identity; authorized evidence surfaces; target-binding evidence (if live);
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
