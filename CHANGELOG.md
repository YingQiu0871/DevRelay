# Changelog

All notable changes to DevRelay are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased - v0.3-E design FROZEN (recovery & reconciliation)

**Design frozen.  Not implemented, not accepted, unreleased.**  The independent
design-freeze review approved candidate
`9f4a01804b9affe8938a272553df345b5a60aeed` with **P0 = 0, P1 = 0, P2 = 0** and
F1-F12 **CLOSED**, decision *APPROVE V0.3-E FAIL-CLOSED CORE DESIGN; PLATFORM PROOF
GATE REQUIRED BEFORE IMPLEMENTATION*.  Implementation is **not authorized**, the
platform proof gate is **not complete** (**G0.1 / P7 = PASS** — authoritative,
independently approved by *APPROVE V0.3-E G0.1 / P7 PLATFORM PROOF* with
P0 = 0, P1 = 0, P2 = 0; G0.3 failed its original oracle, was independently reviewed as a TYPE-1 proof-plan failure and then independently approved after the corrected clean rerun - **G0.3 / P5 = PASS** - (see below); G0.4-G0.5, G1, G2 not run at freeze time (G0.4 has since been executed once and is an authoritative `FAIL / P4 UNPROVEN` - see below); G0.2 ran and, after one `REQUEST_CHANGES` review, was cleanly re-run under a precommitted oracle and then independently approved - `G0.2 = PASS` - see below), `adopt_completed_turn`
remains **disabled**, and
the recorded P3 observations (P3-1, P3-2, P3-4/P3-5) stay non-blocking.

**G0.1 / P7 (local ledger persistence under hard kill) was executed once** after the
freeze and produced a candidate result: six planned case executions (before the
durable ISSUED write, during that write, after ISSUED but before settlement, during
settlement publication, after settlement publication, and a corrupted-record
control) all met their predefined criteria against the real accepted ledger
persistence path, with the corruption-strict scanner never treating malformed
evidence as absence while the tolerant accounting reader demonstrably did.  That
candidate result was *CANDIDATE PASS / REQUIRES INDEPENDENT REVIEW*; the first
independent proof review returned `REQUEST_CHANGES` for **bookkeeping/status wording
only** (P0 = 0, P1 = 0, P2 = 1 - the evidence itself was found sufficient; fixed in
`8997071`), and the final independent proof review then issued
**APPROVE V0.3-E G0.1 / P7 PLATFORM PROOF** (P0 = 0, P1 = 0, P2 = 0), so
**G0.1 / P7 = PASS** (authoritative, independently approved) and it no longer blocks
mandatory-core implementation *eligibility*; implementation nonetheless remains
**not authorized** until a separately issued implementation authorization.  The
remaining gate steps (G0.3-G0.5, G1, G2) had **not** run at that point, so the platform
proof gate was recorded as **partially executed / not complete** (not passed, not
complete); `adopt_completed_turn` remains disabled, and 0 real provider/model calls were
made.  Evidence: `docs/v0.3/V03E_G0_1_P7_PROOF.md` (later rounds are recorded below).

**G0.2 (offline run<->call false-correlation proof) was executed once** at `4448f92`
with no runtime change and returned a **candidate pass**: all ten planned cases (A-J)
behaved fail-closed against real production-generated corpora (a live in-flight intent
from a real crash boundary plus the accepted ledger written by the real bridge/ledger
classes, offline).  A unique exact correlation is possible only when the complete
frozen identity tuple matches exactly one record in the run's role session; the
same-session/different-attempt, identical-prompt, weak-field-only, stale-cycle,
wrong-role/operation, foreign-run, duplicate, missing-identity and corrupt-look-alike
cases all end in `NO_MATCH` / `evidence_conflict` / `evidence_gap` / `corruption`
with no false attribution and no timestamp tie-break, and the corruption-strict scan
wins over a clean unique candidate (the tolerant accounting reader would silently skip
the torn artifact and claim uniqueness).  Two central findings: the ledger carries
**no run identity and no cycle/attempt identity**, and a live in-flight attempt never
durably contains the ledger `call_id`.  That round's result was a candidate pass; the
first independent review returned `REQUEST_CHANGES` (P0 = 0, P1 = 0, P2 = 2), and a
separately authorized **clean G0.2 re-run** was then executed under an oracle
precommitted in commit `12ea1b7` (`docs/v0.3/V03E_G0_2_RERUN_ORACLE.md`): the ten fixed
cases A-J ran once each, every verdict stayed inside its precommitted allowed set, the
oracle was unchanged during execution and no weak metadata produced an attribution.
That clean re-run was then independently reviewed and approved (**APPROVE V0.3-E G0.2
FALSE-CORRELATION PROOF**, P0 = 0, P1 = 0, P2 = 0), so **G0.2 = PASS** (authoritative,
independently approved).

**G0.3 (transport / non-delivery classification, P5) was executed once** offline at
`efa2ca3` under the oracle precommitted in `b9c4704`
(`docs/v0.3/V03E_G0_3_TRANSPORT_ORACLE.md`) and returned a **candidate FAIL**: all six
accepted non-delivery classes (`connect_timeout`, `pool_timeout`, `connect_error`,
`proxy_error`, `unsupported_protocol`, `local_protocol_error`) were independently shown
pre-send on the installed stack (no request header or body byte reached the network
stream), and every uncertain class stayed uncertain with `retry_safe` false; but
precommitted case G0.3-J (`write_error`) surfaced as `remote_protocol_error` instead of
its precommitted class because the installed httpcore suppresses a request-send
`WriteError` and continues to the read phase.  No non-delivery safety property was
violated and no capability depends on P5 (informational only), but per the precommitted
standard the candidate result is **FAIL** and the affected case/class is named.  0 real
provider/model calls, 0 real network requests.  Evidence:
`docs/v0.3/V03E_G0_3_TRANSPORT_PROOF.md`.  That failure was then independently reviewed
as **FAIL - V0.3-E G0.3 / P5 PROOF - TYPE 1 PROOF-PLAN FAILURE** (P0 = 0, P1 = 0, P2 = 0):
the candidate correctly failed its immutable oracle, case J's exact classification
expectation was wrong for the installed HTTP/1.1 request-send path, **no accepted
safe/non-delivery classifier bucket was shown to be unsafe**, and **no runtime
remediation is required**; a corrected clean rerun was separately authorized under a new
precommitted oracle (`docs/v0.3/V03E_G0_3_RERUN_ORACLE.md`).

**Corrected clean G0.3 / P5 rerun (executed once, one semantic execution per case):**
The corrected clean rerun was then independently reviewed and approved (**APPROVE
V0.3-E G0.3 / P5 TRANSPORT PROOF**, P0 = 0, P1 = 0, P2 = 0), so **G0.3 / P5 = PASS**
(authoritative, independently approved).  Under the corrected oracle
(`e328ec5`, manifest SHA-256 `9e4c7de6…`) the accepted safe buckets are class-wide
pre-send on the installed stack — `connect_timeout`, `pool_timeout`, `connect_error`,
`unsupported_protocol`, and the pre-send-only `local_protocol_error` mapping boundary (the
h11 request-construction mapping) — with no request header or body byte on the wire;
`proxy_error` is recorded as **UNREACHABLE_CURRENT_CONFIGURATION** (no proxy in the
accepted configuration, `trust_env=False`); every uncertain class (`read_timeout`,
`write_timeout`, `read_error`, `remote_protocol_error`, `close_error`) stayed
`submission_uncertain=True` with `retry_safe=False`; the corrected case J surfaced
`remote_protocol_error` with uncertainty exactly as precommitted (httpcore suppresses the
request-send `WriteError`), while `write_error` stays a defensive, unexercised mapping;
HTTP rejection (500) and the success control were never treated as non-delivery; and the
unmapped mid-send h11 escape path is recorded as a fail-closed observability limitation
(no runtime change).  0 provider/model calls, 0 network requests, 0 OpenCode processes.
Evidence: `docs/v0.3/V03E_G0_3_CLEAN_RERUN_PROOF.md`.  G0.1/P7 and G0.2 are authoritative PASS and mandatory-core
implementation remains **not authorized** pending a separate authorization; the
platform proof gate stays **partially executed / not complete** (G0.3/P5 = PASS,
authoritative; G0.4/G0.5/G1/G2 not run at that point; G0.4 has since been executed once and is an
authoritative **FAIL / P4 UNPROVEN** - the accepted workspace had no OpenCode base endpoint, so no
target instance could be bound and 0 `GET /doc` were issued: `docs/v0.3/V03E_G0_4_API_INSPECTION_PROOF.md`)
and
`adopt_completed_turn` stays **disabled**.  Clean-rerun evidence:
`docs/v0.3/V03E_G0_2_CLEAN_RERUN_PROOF.md`; original record (preserved):
`docs/v0.3/V03E_G0_2_FALSE_CORRELATION_PROOF.md`.

**G0.4 (installed-API inspection for a per-operation pending handle, P4) was executed
once** under its approved immutable revision-3 oracle
(`docs/v0.3/V03E_G0_4_API_INSPECTION_ORACLE.md`, committed-blob SHA-256 `b0c34fa1…`).
Case A could not establish `TARGET_BOUND`: the accepted workspace configuration
(`.devrelay/config.yaml`) resolves no OpenCode endpoint (`opencode.base_url` is empty;
`OpenCodeConfig.configured` is false), and DevRelay never discovers servers by scanning
ports or processes - so no target instance, listener or responder could be bound and the
binding reason is `TARGET_IDENTITY_UNRESOLVED`.  The precommitted failure path applied:
**0 loopback HTTP requests, 0 `GET /doc`**, cases B-H not executed, no substitute or
historical evidence, no rerun.  Final semantic outcome for the round:
`EVIDENCE_INSUFFICIENT` -> executor-stage **CANDIDATE FAIL / P4 UNPROVEN**.

The independent failed-proof review then issued **APPROVE V0.3-E G0.4 FAILED PROOF** with
**P0 = 0, P1 = 0, P2 = 0** and failure classification **TYPE 3 - SEMANTIC ENVIRONMENT /
CONFIGURATION RESULT** (the accepted workspace supplied no OpenCode base endpoint), which
makes the result authoritative: **G0.4 / P4 = FAIL / P4 UNPROVEN**.  No API/schema property
was established, so nothing follows about whether a durable per-operation handle exists;
P4 remains formally unproven, a rerun of this execution is **not authorized**, and repairing
the configuration would be a **new** execution requiring new external authorization under the
same immutable oracle.  The installed target's static identity was recorded
(`opencode-ai` 1.18.11, declared bin `./bin/opencode.exe`, executable SHA-256
`578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35`).  0 provider/model
calls, 0 network requests, 0 OpenCode starts/restarts.  Evidence:
`docs/v0.3/V03E_G0_4_API_INSPECTION_PROOF.md`.

**G0.5 / P6 definition was remediated** (documentation/definition only; no oracle, no
proof, no execution).  A prior read-only inventory returned *NOT READY — G0.5 DEFINITION
AMBIGUITY* (no frozen PASS/FAIL semantics, no method, no identity-dimension set, identity vs
ownership undefined, and an adoption-role contradiction between §19, §25, §27, §28 and E33).
The remediation freezes **P6 as a local identity/ownership VETO BOUND on adoption — not an
adoption-enabling proof**: G0.5 PASS clears only the local veto prerequisite and enables
nothing by itself, while G0.5 FAIL leaves the veto active and adoption DISABLED.  The
remote/platform *enabling* proofs remain **P1+P2+P3+P8 (+P9 if applicable)** through G1/G2,
and **both classes must be satisfied before adoption may ever be authorized**.  The frozen
definition (`V03E_SPEC.md` §25.1) fixes the exact question, the identity/ownership
definitions, the fail-closed original-owned-session rule, exactly **four case classes A–D**
(missing; foreign; recreated/originality-unprovable; copied — with **`session_id` equality
alone insufficient**), a **bounding PASS**, FAIL and insufficient-evidence semantics, a
**local/offline method** (0 HTTP, 0 `/doc`, 0 OpenCode start/restart, 0 session mutations, 0
provider/fake-provider calls; the missing G0.4 `base_url` is therefore **not** a G0.5
prerequisite), the identity-dimension matrix, the adoption dependency equation, evidence
fields, privacy rules, the status model and the no-probe-shopping discipline.  At that point
G0.5 remained **NOT RUN / DEFINITION REMEDIATED / AWAITING INDEPENDENT DEFINITION REVIEW**
(superseded by the accepted status recorded below); no G0.5 oracle existed and G1/G2 remained
unrun.

**G0.5/P6 oracle construction was attempted and stopped by a LOCAL REACHABILITY GAP.**  The
definition baseline was accepted by independent review (*APPROVE V0.3-E G0.5
ADOPTION-DEPENDENCY CLEANUP*, P0 = 0, P1 = 0, P2 = 0; commit `ad86a79`; the substantive §25.1
block was preserved byte-for-byte, SHA-256 `d3244ee0…`).  A pre-run oracle construction round
then performed a purely static, per-case source-reachability check against existing local
enforcement: **Case A (missing)** binds to the blank/missing session-reference validation,
**Case B (foreign)** to the pure session↔workspace ownership primitive, and **Case D (copied)**
to the run↔workspace binding check — but **Case C (recreated / originality-unprovable) has no
existing local original-session/provenance enforcement path**, so a complete four-case oracle
cannot be frozen; constructing one would require proof-only policy code or a new runtime
primitive, both prohibited.  The independent review approved that outcome (*APPROVE V0.3-E
G0.5 ORACLE FREEZABILITY FAILURE*, P0 = 0, P1 = 0, P2 = 0), classifying it as **C —
NOT-YET-IMPLEMENTED V0.3-E ENFORCEMENT PREREQUISITE** (not a definition defect, not a proof
failure, not a harness failure, not an installed-platform limitation).  **No G0.5 oracle was
created, no semantic case was executed, and therefore there is no G0.5 PASS and no G0.5
FAIL**: `G0.5/P6 = NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY
GAP`, with **P6 = UNPROVEN / UNSATISFIED**.  Adoption stays DISABLED, the mandatory core is
unaffected (G0.1/P7 remains the only hard gate and stays PASS/CLOSED), and G1/G2 remain unrun;
the attempt caused 0 runtime/test/config changes and 0 provider/HTTP/OpenCode activity.

**A new prerequisite information finding — G0.5-PRE / SIC (session-incarnation capability
finding) — was defined** (definition candidate only; nothing executed).  The independently
approved Case-C prerequisite design block (*APPROVE V0.3-E CASE-C PREREQUISITE DESIGN BLOCK*)
confirmed the stronger thesis **`BLOCKED — NO SOUND ORIGINAL-SESSION PROVENANCE ANCHOR
AVAILABLE`**: no currently accepted evidence source can soundly support ORIGINAL OWNERSHIP
PROVEN, purely local nonce/fingerprint approaches are not provenance, a fail-always guard
would permanently remove capability C and is therefore a product-scope change, G1/P1 does not
prove session incarnation, G2/P2/P3/P8/P9 do not themselves prove it, and G0.4/P4 is
unrelated and stays CLOSED.  SIC asks whether OpenCode 1.18.11 exposes, through a read-only
session representation, a per-session-incarnation property (or tuple) whose semantics are
strong enough to serve as a provenance anchor, with four precommitted outcomes
(`SIC_PRESENT_AND_SEMANTICS_ESTABLISHED`, `SIC_METADATA_PRESENT_BUT_SEMANTICS_UNPROVEN`,
`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`, `SIC_EVIDENCE_INSUFFICIENT`), a strictly read-only
method, a zero provider/model budget, static-string limits and no-probe-shopping discipline —
definition: `docs/v0.3/V03E_G0_5_PRE_SESSION_INCARNATION_FINDING.md`, status **SIC = NOT RUN /
DEFINITION CANDIDATE**, awaiting independent definition review.  No OpenCode instance was
started, no HTTP or `/doc`/`/session` access occurred and no provider/model call was made;
G0.5 stays `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP`,
G1/G2 stay NOT RUN, adoption stays DISABLED and implementation remains NOT AUTHORIZED.

**The SIC definition received `REQUEST_CHANGES` (`REQUEST_CHANGES — V0.3-E G0.5-PRE / SIC
DEFINITION`; P0 = 0, P1 = 1, P2 = 3) and only its blocking findings were remediated**
(`docs/v0.3/V03E_G0_5_PRE_SESSION_INCARNATION_FINDING.md`; status **SIC = NOT RUN /
DEFINITION CANDIDATE / AWAITING INDEPENDENT RE-REVIEW**).  **P1 — positive semantic
authority:** "observable contract evidence" is now defined normatively as an explicitly
declared/documented contract semantic from an authoritative surface associated with the exact
installed target, whose declared behaviour may be checked for runtime consistency; runtime
observations/response examples may support only field existence, runtime exposure,
target/version consistency, response shape/type consistency and consistency with an
already-declared contract, and may **never** establish immutability, incarnation sensitivity,
session-incarnation scope, non-reuse, uniqueness, stability or provenance — one sample,
multiple samples, repeated stable observations and cross-session differences are **all**
insufficient without an authoritative declared semantic.  `SIC_PRESENT_AND_SEMANTICS_ESTABLISHED`
now requires **both** actual exposure through the authorized surface **and** authoritative
declared semantics for **all** qualifying properties; declaration-free metadata exposure yields
`SIC_METADATA_PRESENT_BUT_SEMANTICS_UNPROVEN` with no empirical promotion.  **P2-A —
`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`** is legal only on complete, successful coverage of the
precommitted surface (partial/unreachable/truncated/ambiguous/incompletely-parsed coverage →
`SIC_EVIDENCE_INSUFFICIENT`), and it is a surface-and-version-scoped non-claim that must never
generalize to "OpenCode has no session-incarnation metadata"; incomplete inspection may not be
hidden behind `HARNESS_INVALID`.  **P2-B — mode precommit:** the oracle must freeze exactly one
of Mode A (offline/static), Mode B (live local read-only) or Mode C (precommitted bounded
static→live two-stage, with the transition condition defined before execution); mid-run mode
switching and endpoint shopping invalidate the attempt, and the mandatory precommit set now
covers mode, surfaces, discovery/extraction rule, endpoint, request set/count, transition rule,
evaluation criteria, target binding, stop conditions and outcome mapping.  **P2-C — actual
destination/responder binding:** the actual HTTP client destination must be the exact frozen
concrete endpoint (numeric loopback address, port, address family, scheme, client destination
URI/base) bound to one deterministic listener (PID, canonical executable path, executable hash,
creation identity, exact version) with pre/post-request identity snapshots; any address-family,
listener, port-sharing, PID, proxy or responder ambiguity is **TARGET BINDING INVALID** and
stops before semantic inspection; a pre/post unchanged process elsewhere on the host is
insufficient; continuity mismatch makes the evidence invalid and may not be reported as a SIC
result; this reuses the accepted G0.4 revision-3 binding lessons without reopening G0.4.  The
non-blocking P3 items were deliberately not addressed, no status other than the SIC definition
candidate changed, and 0 runtime/test/config, provider/model, HTTP, `/doc`/`/session` or
OpenCode activity occurred.

**The first (Mode-A) SIC oracle-construction attempt was independently approved as a
freezability failure, and a narrow outcome-mapping amendment was applied.**  The independent
review issued *APPROVE V0.3-E SIC ORACLE FREEZABILITY FAILURE* (**P0 = 0, P1 = 0, P2 = 0**)
with classification **NARROW SIC DEFINITION VOCABULARY / OUTCOME-MAPPING DEFECT**: the accepted
four-outcome vocabulary could not truthfully map the state "candidate metadata present with
authoritative declared semantics that affirmatively establish non-qualification", because
outcome #2 was worded as semantics being *not sufficiently established* while the remaining
outcomes require zero candidates (NOT_EXPOSED) or insufficient coverage (EVIDENCE_INSUFFICIENT);
folding the two together or inventing a fifth outcome was forbidden.  **No SIC semantic attempt
occurred and no SIC oracle exists.**  The amendment (Option A) keeps exactly the four tokens and
clarifies `SIC_METADATA_PRESENT_BUT_SEMANTICS_UNPROVEN` normatively as *"candidate metadata
exists/is exposed, but no discovered candidate establishes the required qualifying SIC
semantics"*, covering exactly two sub-classes — **A. qualifying semantics unestablished**
(absent/insufficient/incomplete/ambiguous/unproven) and **B. authoritatively non-qualifying**
(established semantics affirmatively failing at least one required criterion) — with an explicit
token-interpretation note that the token does not require all candidate semantics to be unknown,
that the outcome stays strictly non-positive, that a positive result still requires one candidate
satisfying all of criteria A–G, that `NOT_EXPOSED` remains available only for complete coverage
plus zero candidates (discovery is never retroactively erased), that sufficient negative evidence
is never `EVIDENCE_INSUFFICIENT`, that `HARNESS_INVALID` stays outside the semantics, and that
per-candidate verdicts (`QUALIFIES` / `SEMANTICS_UNPROVEN` / `NON_QUALIFYING_METADATA`) are never
global tokens.  A frozen global mapping and an 11-row compatibility matrix now cover every
reachable state.  Mode A/B/C rules, the mode-precommit/no-mode-shopping rules, the
static-vs-live semantic-authority boundary, target binding, actual-responder, no-alternate-endpoint
and pre/post-continuity rules are all preserved unchanged, as is the positive-evidence threshold
(runtime observations still cannot establish semantics).  Status: `SIC = NOT RUN / DEFINITION
ACCEPTED / DEFINITION AMENDMENT CANDIDATE / ORACLE NOT YET CREATED / ORACLE NOT FREEZABLE —
OUTCOME MAPPING GAP`; the amendment requires independent review before any oracle is frozen.
The recorded scoped static-surface fact is only that the inspected installed static package
surface (OpenCode 1.18.11 npm distribution) contains no readable session schema, OpenAPI
artifact, generated client, bundled session documentation or declared session-metadata
semantics — it is **not** a SIC result and must never be read as "OpenCode has no incarnation
metadata".  G0.5/P6, G1/G2, adoption and implementation statuses are unchanged; 0
runtime/test/config, provider/model, HTTP, `/doc`/`/session` or OpenCode activity occurred, and
no oracle or result artifact was created.

**The SIC outcome-mapping amendment was independently approved, and a Mode-A pre-run oracle
candidate was constructed.**  The independent review issued *APPROVE V0.3-E SIC
OUTCOME-MAPPING DEFINITION AMENDMENT*, which makes commit `829d3c0` (SIC definition artifact
blob `5463ac19…`) the accepted SIC definition baseline and **resolves the prior `ORACLE NOT
FREEZABLE — OUTCOME MAPPING GAP` at definition level** — that blocker was a pre-oracle
definition defect (the four-outcome vocabulary could not truthfully map authoritatively
non-qualifying metadata), never an SIC semantic result.  With the amended definition in force, a
**MODE-A (offline/static only) pre-run oracle candidate** was written to
`docs/v0.3/V03E_G0_5_PRE_SIC_ORACLE.md`: **PRE-RUN ORACLE CANDIDATE — NOT ACCEPTED, NOT FROZEN,
NOT EXECUTED**, `SIC = NOT RUN / DEFINITION ACCEPTED / ORACLE CANDIDATE`.  The oracle freezes the
exact Mode-A authorized surface — the whole installed `opencode-ai` 1.18.11 package tree,
re-enumerated at construction: **8 files / 6 directories** in lexicographic order with sizes and
SHA-256 (`LICENSE`; `bin/opencode.exe` `578d7eb3…`; the two `node_modules/opencode-windows-x64*`
platform trees — `opencode-windows-x64/bin/opencode.exe` byte-identical to the declared bin, and
`opencode-windows-x64-baseline/bin/opencode.exe` `0e80c444…` — plus their `package.json`
manifests; and `postinstall.mjs`) — each artifact classified exactly once
(`PACKAGE_METADATA` / `INSTALLER_LOGIC` / `LICENSE_TEXT` / `OPAQUE_COMPILED_BINARY`, with compiled
binaries hashed and recorded but never supplying candidate fields or semantic authority).  It
also freezes: the complete-coverage rule (any missing, extra, drifted, unreadable, unparseable,
unclassified or ambiguous artifact prevents `NOT_EXPOSED` and maps to `EVIDENCE_INSUFFICIENT`
unless strictly inside the pre-assertion `HARNESS_INVALID` boundary); a deterministic,
enumerable candidate-extraction rule with a session-anchored discovery grammar, frozen alias
normalization and explicit forbidden sources (no arbitrary binary strings, no UUID-shaped bytes,
no frequencies, no name guesses detached from a session contract); discovery-before-validation
with a frozen candidate set (a `NON_QUALIFYING_METADATA` candidate is never retroactively
erased); the accepted per-candidate vocabulary (`QUALIFIES` / `SEMANTICS_UNPROVEN` /
`NON_QUALIFYING_METADATA`) with a complete per-candidate record schema; criteria A–G with the
strict incarnation-sensitivity, stability and session-scope thresholds; the Mode-A
semantic-authority rules; the amended four-outcome mapping; the mandatory surface-scoped
`NOT_EXPOSED` non-claim; **no live fallback** (the mode is fixed before execution and
`EVIDENCE_INSUFFICIENT` ends the run); exactly one semantic attempt with no rerun, no alternate
package, no second static surface and no manifest update after results; the artifact-drift stop
rule; and the future result-artifact schema with zero-activity budgets and privacy prohibitions.
A surface-scoped construction fact is recorded for transparency — the frozen manifest contains
zero `DECLARATIVE_CONTRACT_CANDIDATE` artifacts — explicitly **not** a SIC result and never to be
read as "OpenCode has no incarnation metadata".  No SIC semantic attempt occurred, no result
artifact exists and no execution is authorized; G0.5/P6 remains `NOT RUN / DEFINITION ACCEPTED /
ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP` with P6 `UNPROVEN / UNSATISFIED`, G1/G2 remain
`NOT RUN`, adoption stays **DISABLED** and implementation remains **NOT AUTHORIZED**; 0
runtime/test/config, provider/model, HTTP, `/doc`/`/session` or OpenCode activity occurred.

That approval followed three earlier review rounds: the first independent design
review returned `REQUEST_CHANGES` (P0 = 1, P1 = 6, P2 = 5) and the
recovery/reconciliation contract was repaired in `f67bf9e`; two narrow re-reviews
then returned `REQUEST_CHANGES` for a stale status/gating pointer (fixed in
`5b7c65a`) and for a G0.1/P7 hard-gate contradiction (fixed in `9f4a018`).  The
remediated design
splits a **mandatory fail-closed core** (reconcile/report + an explicit
`mark_unrecoverable` exit; no provider submission, no retry, no auto-resume, no
adoption) from an **optional gated** `adopt_completed_turn` capability and a
**report-only** pending capability, so that no optional capability can block the
core:

* recovery entry is an explicit legal planner action
  (`devrelay_resolve_recovery` on a valid v2 document with a live in-flight intent,
  or on `RECOVERY_REQUIRED`), fixing the review's P0 deadlock; v2 phase/decide calls
  refuse without mutating, so no transition is a side effect of an invalid action;
* the interrupted attempt is represented by exactly one `recovery.attempt` record
  and is converted once (into one blocked or one completed role turn) at
  resolution, with the complete `RECOVERY_REQUIRED` document shape and pinned
  accounting equations published (a consumed slot is never refunded and is counted
  exactly once);
* corruption is explicitly never recovery (violations outside the enumerated deltas
  become `orchestration_state_corrupt`: no entry, no override, no repair);
* a strict recovery evidence reader replaces "no ledger record, therefore never
  issued" (identity-scoped, no silent skipping, no truncation-as-proof, an interval
  proof, otherwise `evidence_gap`);
* adoption claims are downgraded: reconcile may report a candidate, but
  `resolve_recovery` must refuse `adopt_completed_turn` until the operation
  attribution proofs P1, P2, P3 and P8 (plus P9 if timestamps are used) pass;
* schema handling is version-dispatched (v1 validated by the frozen v0.3-D rules and
  never migrated or reinterpreted; v2 uses the v0.3-E rules; anything else is
  corrupt), `evidence_sha256` has a canonical metadata-only definition with a
  stable already-resolved error, the crash-window matrix gains the window where the
  response exists but the ledger settle is not durable, and pending results are
  report-only.

The full contract (case taxonomy, `RECOVERY_REQUIRED` state, crash-window and
restart matrices, minimum two-tool surface, capability dependency table, platform
proof gate) is in `docs/v0.3/V03E_SPEC.md` with the design-phase matrix in
`docs/v0.3/V03E_ACCEPTANCE.md`.  It contains no retry protocol, keeps
`model_turns_used` as consumed slots that are never refunded, keeps terminal runs
closed and keeps `devrelay_get_run` read-only.  Implementation is gated in two
separate stages, and both of its prerequisites are now satisfied (design frozen;
**G0.1/P7 = PASS**, authoritative and independently approved): the **mandatory
fail-closed core**
(reconcile/report + `mark_unrecoverable`; no retry, no model submission, no
auto-resume) requires the design freeze **and** the local strict-reader /
ledger-integrity proof **G0.1/P7 to PASS first** (design frozen -> G0.1/P7 PASS ->
implementation may be authorized; there is no degraded-implementation path) - both of
those steps have happened, so implementation awaits only a separately issued
authorization - while
the **optional** `adopt_completed_turn` capability stays disabled and requires **both**
the independently satisfied local **P6/G0.5 identity/ownership veto bound** (SPEC §25.1)
**and** the independently satisfied remote/platform *enabling* proofs
P1 + P2 + P3 + P8 (plus P9 if timestamp/order correlation is used) through G1/G2,
together with the remaining platform proof gate.  Pending-result handling stays report-only and
non-delivery classification stays informational.  No runtime source, test, schema, dependency,
version or tag changed; no real provider/model call was made and no OpenCode
instance was started.  Design branch: `v0.3-e-recovery-reconciliation` (parent
`56e7842`).

The first design revision of this section read: `docs/v0.3/V03E_SPEC.md` (case taxonomy A-H, preserved v0.3-D
invariants, one new non-terminal execution-frozen `RECOVERY_REQUIRED` state,
exact call-identity model, reconciliation evidence sources, crash-window matrix
W0-W6, restart matrix, reconciled completion / non-delivery / pending-reply
policies, budget and privacy rules, minimum two-tool MCP surface, design-decisions
table) and `docs/v0.3/V03E_ACCEPTANCE.md` (design-phase matrix).  The design
forbids implicit retry, model fallback, automatic sequencing and automatic resume,
keeps `model_turns_used` as consumed slots that are never refunded, keeps terminal
runs closed, and keeps `devrelay_get_run` read-only.  Two tools are proposed and
**not** implemented: `devrelay_reconcile_run` (read-only) and
`devrelay_resolve_recovery` (mutating, evidence-gated).  Implementation is gated on
an independent design review and the open platform proofs in SPEC section 15
(P1-P7).  No runtime source, test, schema, dependency, version or tag changed; no
real provider/model call was made.  Design branch:
`v0.3-e-recovery-reconciliation` (parent `56e7842`).

## Unreleased - v0.3-D accepted (bounded orchestration)

Durable, **bounded** orchestration state over the accepted v0.3-C role path: a
Planner creates a run, explicitly runs each phase, and records its own decision -
DevRelay remembers where the run is, enforces a hard cycle bound and fails closed
on uncertainty.  **Accepted internally, closed and unreleased** at candidate
`8b70610a5cdda600ef57cf8378c4f69cd33d5be4` after two independent remediations and
one authorized bounded real orchestration smoke (`PASS — V0.3-D REAL BOUNDED
ORCHESTRATION SMOKE`): the package version stays `0.1.0`, the supported public
release remains `v0.1.0`, there is no `v0.3-D` tag, nothing is pushed, merged,
tagged or published, and v0.3-E has not started.

### Added

- **`src/devrelay/orchestration/`** (`models.py`, `store.py`, `state_machine.py`,
  `service.py`): the explicit run states (`READY_IMPLEMENTER`, `READY_REVIEWER`,
  `AWAITING_DECISION`, `COMPLETED`, `STOPPED`, `BLOCKED`, `LIMIT_REACHED`), hard
  bounds (`max_cycles` 1..3 with `HARD_MAX_CYCLES = 3`, default 2, model-turn
  budget `2 x max_cycles`, absolute ceiling six turns), a strict durable run
  document with a Planner-complete summary, a single-writer atomic store under
  `.devrelay/orchestration/runs/<run_id>.json`, a pure transition policy and the
  service that binds them to the accepted role router and bridge.
- **Five MCP tools** (the accepted twelve unchanged, total **17**):
  `devrelay_start_run` (two existing role sessions + `max_cycles`; no model call),
  `devrelay_get_run` (read-only, local), `devrelay_run_implementer` and
  `devrelay_run_reviewer` (one explicit phase turn each) and
  `devrelay_decide_run` (`complete` | `request_changes` | `stop`; no model call).
  All five share the accepted execution boundary, so one MCP surface still
  serializes all seventeen tools.
- **Durable audit**: previous/next state, timestamp, action, external vs
  model-bearing source, cycle, role, prompt digest and length, resolved
  model/agent, call ids, submission status/flags, uncertainty/pending and
  assistant message ids - never a raw prompt, provider reply, model reasoning or
  credential.
- **Fail-closed bounds**: an uncertain, pending or failed phase blocks the run
  (no retry, no fallback, no role switch, no automatic interrupt); a changed **or
  unresolvable** role route or an ownership loss fails the run closed with zero
  model POST; a persisted in-flight turn is never replayed; a corrupt run document
  is reported as `orchestration_state_corrupt` and never reset.
- **255 offline tests** (154 at the candidate, 101 added by the remediation)
  plus the v0.3-D spec and acceptance matrix.

### Notes

- **The external Planner stays authoritative.**  DevRelay never parses reviewer
  prose (`APPROVE`/`REQUEST_CHANGES`/anything else) to choose a state: a
  successful reviewer turn always stops at `AWAITING_DECISION`, and only an
  explicit decision (recorded with `source = external_planner`) advances the run.
- **Still no automatic sequencing**: no automatic implementer -> reviewer call, no
  repair loop, no scheduler, no background runner, no semantic judgement of review
  content, no automatic acceptance or merge, no session creation.
- **Backward compatibility**: the accepted v0.3-A/B/C behaviour is unchanged; the
  raw `opencode_send_prompt` and role `devrelay_send_role_prompt` paths are
  untouched, and the only test-expectation updates are the intended tool
  inventory (12 -> 17) and the advertised server version (`0.3.0-c` -> `0.3.0-d`).
### Remediation (independent gate: `REQUEST_CHANGES`, P0 = 0, one blocking P1)

The first v0.3-D candidate trusted persisted run state as input.  Fixed at the
model/store load boundary rather than by adding checks to `start_run`:

- **Persisted state is untrusted input** (`src/devrelay/orchestration/invariants.py`):
  every load *and* every save re-derives the invariants the state machine
  guarantees - fixed schema version, `1 <= max_cycles <= 3`, budget `2 x
  max_cycles`, counters consistent with the recorded turns, `turn_attempts ==
  model_turns_used`, every reserved slot accounted for by a finished turn or the
  live in-flight intent, two distinct non-blank sessions, a complete and mappable
  two-role snapshot, one turn per role per cycle with the implementer first,
  `completed_cycles` equal to the completed reviewer turns, the state/cycle
  relation, `LIMIT_REACHED` only at the cap with `blocked_reason=cycle_limit`,
  `BLOCKED` only with a reason, the in-flight shape (matching `READY_*` state,
  current cycle, `outcome=in_flight`, snapshot model, well-formed prompt
  evidence), an external-only decision history consistent with the current state,
  and start provenance that claims no previous state.  Anything else is
  `orchestration_state_corrupt`: refused, never repaired, never migrated, never
  rewritten, never able to reach a model call.  The store additionally requires
  transition provenance for a persisted document and binds it to its workspace.
- **The gate's four reproductions are refused**: `max_cycles=99`/budget 198 cannot
  run a single extra turn, identical role sessions are rejected, `max_cycles=1000`
  cannot open five cycles, and `AWAITING_DECISION` with `completed_cycles=0` and
  no reviewer turn cannot open one.  A 20-case tamper matrix plus 22 additional
  corruption cases assert this, including that the file is byte-identical after
  every refused attempt.
- **An unresolvable role route** (role removed, or its configured route invalid)
  now fails an existing run closed with `orchestration_route_changed`, durable
  `BLOCKED`/`blocked_reason=route_changed`, an immutable snapshot and zero model
  POST; at `start_run` there is nothing durable to block, so the same failure is
  reported as `orchestration_route_changed` with no run created.
- **An interrupted turn keeps its audit trail**: the sanitized attempt is
  finalized as `blocked`/`turn_interrupted` and appended to the role history (so
  the reserved slot keeps a matching record and the transition keeps the phase
  action and role) before the run fails closed; `legal_next_actions` is empty while
  an intent is live.
- **The durable in-flight intent provably precedes submission**: a transport-level
  callback observes the on-disk document at the exact moment the prompt POST is
  sent (no sleeps, no polling), and a real process death (`SystemExit`) at
  submission leaves a loadable in-flight document that a fresh surface
  materializes into an auditable `BLOCKED` run.  The previously undetected
  Mutation F (bypassing the pre-call save) now fails four tests.
- **Accounting, vocabulary and identity wording**: `model_turns_used` is
  documented and tested as *consumed slots* that are never refunded (a ten-kind
  failure matrix asserts one slot, one turn record, no retry); turn `outcome` is
  constrained to `in_flight`/`completed`/`blocked`; run ids are matched with a
  strict full match; and the docs/status no longer overclaim (atomic against a
  crash of this process, **no** power-loss `fsync` claim; the execution lock is
  per tool surface, the shipped stdio server builds exactly one surface, and
  multiple surfaces or processes are unsupported).
- **Recorded, not fixed (P3)**: the MCP SDK's lax argument model normalizes JSON
  `true`/`"2"`/`2.0` to integers before the tool body (and refuses `1.5`), so a
  boolean `max_cycles` reaches the body as `1`.  DevRelay still rejects a real
  `bool` at its own boundary and the 1..3 ceiling can never be raised (`false`
  normalizes to 0 and is refused).

### Second remediation (independent gate: P0 = 0, three blocking P1s)

The second gate proved that a persisted run only had to have *plausible fields*.
Three exploits are closed by making the current state **provable from the
persisted history** (turn history, decision history, counters, transition
provenance, cycle structure and in-flight intent), still with **0 real model
calls** and still **NOT ACCEPTED at that point** (historical: v0.3-D was
accepted later in this same Unreleased section, after the smoke in the next
subsection):

- **P1-A**: `READY_REVIEWER` - and a live reviewer in-flight intent - now requires
  exactly one **completed** implementer turn in the current cycle.  A forged
  reviewer phase used to reach `POST /session/<reviewer>/message` before the
  post-call save noticed; it is now `orchestration_state_corrupt` at the load
  boundary with zero requests and a byte-identical file.
- **P1-B**: a historical `blocked` turn implies `BLOCKED` (a failed phase fails the
  run closed and nothing reopens it), so a blocked turn can no longer sit inside an
  active or completed run; a completed reviewer turn also requires exactly one
  completed implementer turn in the same cycle.  All five honest `BLOCKED` variants
  (implementer failure, reviewer failure, route change, interrupted implementer,
  interrupted reviewer) stay valid.
- **P1-C**: an exhausted `max_cycles=3` run rolled back toward cycle 1 can no
  longer spend again.  The validator now requires the last transition to be a real
  state-machine edge **ending at the current state** (with the action, previous
  state, role and cycle that edge implies), the decision history to equal
  `completed_cycles - (1 if AWAITING_DECISION else 0)`, every decision to be a legal
  `AWAITING_DECISION` edge whose terminal decision is last, the opened cycles to
  equal `current_cycle - 1`, no turn from a future cycle, and the persisted spend
  to be possible for the cycle structure (`model_turns_used <= 2 x current_cycle`).
  Ten rollback variants (counters/history/decisions reset in every combination,
  stale or rewritten transition, missing `request_changes`, fabricated cycle 3,
  future-cycle turn, terminal-to-active rollback, reviewer evidence without
  implementer evidence, blocked turn injected into a completed history) are all
  refused before any submission.
- **Strict persisted types**: `schema_version` and `model_turn_budget` are required
  (no default) and `schema_version`, `max_cycles`, `current_cycle`,
  `completed_cycles`, `turn_attempts`, `model_turn_budget`, `model_turns_used` (plus
  per-turn `cycle`/`prompt_chars` and the transition cycle) are strict integers, so
  a persisted `"2"`, `2.0`, `true`, `false`, `null` or a missing `schema_version`
  is a malformed document - never a coerced number, never a migration.
- **Turn audit consistency**: finished turns need a valid `completed_at`, a
  lowercase sha256 prompt digest, a positive prompt length, no `blocked_reason`
  when completed and a non-empty one when blocked; an in-flight intent claims
  neither completion nor a blocked reason; `resolved_model`, `resolved_agent` and
  `route_source` must all agree with the captured snapshot.
- **Honest corpus and differential proof**: a new production-generated corpus
  (`tests/v03d_corpus.py`, 19 states including both in-flight roles in cycles 1-2
  and all five `BLOCKED` shapes, with crash boundaries produced by a real
  `SystemExit`) must load, re-save, restart and reload unchanged, and each member
  must reject a 15-mutation battery one mutation at a time.  The hand-written
  in-flight fixtures were replaced by the real crash path.
- **Save-side invariants** are covered directly (state/history relation, identical
  sessions, budget, decision history): an impossible in-memory run cannot be
  written, and the previous document stays byte-identical.
- **Truthfulness fixes**: failure messages are shaped from the recorded
  `submission_attempted`/`submission_uncertain`/`reply_pending`/`submission_status`
  evidence (a connect error is no longer described as uncertain); the
  `devrelay_run_implementer` description explains that a persisted interrupted
  phase is first materialized into `BLOCKED`; `devrelay_get_run` says an
  unreachable document is refused as corrupt; the lock scope is stated per tool
  surface with `lock_scope`/`surfaces`/`multiple_surfaces_or_processes` status keys;
  the model-turn ceiling is described as six reserved/consumed **slots** (at most
  six POST attempts); atomic file replacement no longer implies hard-kill cleanup
  (an inert `.tmp` file is never listed or honoured, and no `fsync`/power-loss
  durability is claimed).
- **Recorded P3s**: the MCP SDK pre-parses JSON-looking *string* prompts
  (`{"task": ...}`) into dict/list and refuses them at its own boundary with **no
  submission** (a `str`-only annotation would break the documented
  `mcp_invalid_argument` envelope, so it is recorded rather than changed); and the
  honest bound of self-contained validation - a fully rewritten but internally
  consistent history cannot be distinguished from an honest one without an external
  integrity anchor (no journal or chain is added).
- **Tests**: the v0.3-D suite grows from 255 to **357** (the new reachability suite
  plus the corpus), the full offline suite from 1064 to **1166**, with mutations
  A-K all detected (A 105, B 19, C 6, D 104, E 6, F 18, G 3, H 2, I 4, J 4, K 4;
  control 357 v0.3-D tests green).

### Accepted — one bounded real orchestration smoke (`PASS`)

The single authorized real run was executed against real OpenCode and real provider
inference and passed: **`PASS — V0.3-D REAL BOUNDED ORCHESTRATION SMOKE`**
(candidate `8b70610a5cdda600ef57cf8378c4f69cd33d5be4`, run id
`DR-dfb23a14e4654a5d9b75b296a27b1245`, 2026-09-17).

* **Exactly four real model-bearing turns** and **exactly four**
  `POST /session/{id}/message` submissions for `max_cycles = 2`: implementer c1
  (`opencode-go/deepseek-v4.1-flash`), reviewer c1 (`opencode-go/glm-5.3-flash`),
  implementer c2, reviewer c2 - four-way route agreement (configuration =
  `devrelay_get_role` = durable `resolved_model` = provider runtime log);
* **0 retries, 0 fallbacks, 0 automatic role calls, 0 interrupts/aborts, and no
  fifth model turn**; `model_turns_used = 4` of `model_turn_budget = 4`; ledger
  final state 30 records, all `COMPLETED`, 0 `ISSUED`;
* **reviewer authority proved against real prose:** the cycle-1 provider answer
  `REQUEST_CHANGES` left the run at `AWAITING_DECISION` with an empty decision
  history (only an explicit `devrelay_decide_run(request_changes)` opened cycle 2),
  and the cycle-2 provider answer `APPROVE` did **not** complete the run (only an
  explicit `devrelay_decide_run(complete)` produced `COMPLETED`).  Both decisions
  cost 0 model calls;
* **terminal guard proved without spending a fifth turn:** a repeated
  `devrelay_decide_run` on the terminal run returned
  `orchestration_invalid_transition` ("never reopened") with the state visible,
  unchanged, a byte-identical run file and 0 new POSTs, and the same document was
  re-checked offline with a throw-on-touch stub bridge that was never touched;
* **durability/privacy audit 45/45:** four completed durable turn records (two
  implementer, two reviewer, correct cycles), no in-flight intent at completion,
  unchanged route snapshot, prompt digests/lengths independently recomputed and
  matching (150/150/177/169), and no prompt, provider answer, reasoning or
  credential material anywhere under `.devrelay`;
* containment: both disposable sessions deleted, the dedicated OpenCode instance
  stopped, the user's own processes untouched, no MCP child process left, and the
  repository HEAD/branch/tag/working tree unchanged.

Carried findings stay recorded (they do not block acceptance): the accepted v0.3-A
reasoning-part normalization limitation, the information-only
`legal_next_actions` display shape, the derived (not persisted) `terminal` field,
the MCP SDK argument-normalization and JSON-shaped-string prompt boundaries, the
non-cryptographic bound of persisted-state validation, inert temp files after a
hard kill, read-only `get_run`, no `fsync`/power-loss durability, and no
multi-surface/multi-process coordination.  v0.3-E recovery remains explicitly out
of scope and not started.

- `MCP_SERVER_VERSION` is `0.3.0-d`.  v0.3-D is accepted/closed and unreleased; no
  further real orchestration smoke is authorized, and v0.3-E recovery is explicitly
  out of scope and not started.

## Unreleased - v0.3-C accepted (agent role routing)

Explicit, deterministic **role -> route resolution** on top of the accepted
v0.3-B MCP surface: an MCP caller selects a semantic role and DevRelay supplies
the exact workspace-configured model (and optional OpenCode agent).  **Accepted
internally / unreleased**: the accepted functional candidate is
`eabb667d1bd9e379d3b7105d72b6a2751bc2a32b`, the package version stays `0.1.0`, the
supported public release remains `v0.1.0`, nothing is pushed, merged, tagged or
published, and no public v0.3 release exists.

### Accepted (real role-routing smoke)

- Semantic roles are exactly `implementer` and `reviewer`, resolved from an
  immutable workspace `roles:` wiring section (`model` + optional `agent`;
  identifiers only - no prompts, credentials, endpoints, retries, fallbacks or
  candidate lists).
- The caller cannot influence the configured route: the role tool accepts only
  `role`, `session_id` and `prompt`; extra protocol members are ignored, and the
  effective route always comes from configuration (no default route, no fallback,
  no role switching).
- Three role-aware MCP tools (`devrelay_list_roles`, `devrelay_get_role`,
  `devrelay_send_role_prompt`) - total MCP inventory **12** - all routed through
  the one accepted global execution-serialization boundary.
- The raw `opencode_send_prompt` path is preserved unchanged, including its
  caller-supplied model/agent semantics.
- Real routing verified by two bounded runs: implementer →
  `opencode-go/deepseek-v4.1-flash` and reviewer → `opencode-go/glm-5.3-flash`,
  each with exactly one `devrelay_send_role_prompt`, exactly one real inference
  (OpenCode `1.18.11` provider log) and exactly one
  `POST /session/{id}/message`; three-way route agreement
  (`devrelay_get_role` = response `resolved_model_identity` = provider log);
  `ok=true`, `isError=false`, `submission_uncertain=false`,
  `reply_pending=false`, `retry_safe=false`; no retry, no fallback, no alternate
  model.
- No automatic acceptance, no review loops and no orchestration: an implementer
  completion did not invoke the reviewer, and the reviewer completion triggered
  nothing - each role ran only because it was explicitly invoked.
- Complete containment and cleanup in both runs: disposable workspace unchanged,
  disposable sessions deleted, dedicated OpenCode stopped, MCP process exited,
  evidence kept outside the repository.

### Added

- **`src/devrelay/roles/`** (`models.py`, `resolver.py`, `service.py`): the role
  vocabulary (`implementer`, `reviewer` - no generic taxonomy yet, no vendor or
  model identifier in code), a frozen `RoleRoute` value object (role, model,
  agent, source) with sanitized read-only/audit views, deterministic exact
  resolution, and `RoleRouter.send_role_prompt(bridge, role, session_id, prompt)`
  which resolves first and then delegates to the accepted
  `OpenCodeBridge.send_prompt`.
- **Local error taxonomy**: `role_unknown`, `role_unconfigured` and
  `role_invalid_route` (`CodedError` subclasses) - local routing failures raised
  before any request that could submit a model turn, never mislabeled as provider
  failures.
- **`roles:` workspace wiring section**: `roles.implementer` / `roles.reviewer`
  with `model` (`<providerID>/<modelID>`, the accepted grammar) and an optional
  `agent`.  Identifiers only: prompt templates, shell commands, environment
  variables, endpoint/workspace overrides, retry policies, fallback models,
  candidate lists and credentials are rejected by the schema.  Runtime wiring,
  never task policy (excluded from policy overrides; tolerated-and-dropped in
  legacy full-config dumps).  The section is optional - an existing v0.3-B
  workspace stays valid and `devrelay mcp serve` never refuses to start because
  role routing is absent.
- **Three MCP tools** (the accepted nine are unchanged, total 12):
  `devrelay_list_roles` (read-only), `devrelay_get_role` (read-only) and
  `devrelay_send_role_prompt` (`role`, `session_id`, `prompt` only).  Their
  descriptions state the routing contract: the caller selects the role, DevRelay
  resolves the exact configured model/agent, the route cannot be overridden,
  exactly one model turn is sent, nothing is retried, and a reviewer reply is
  provider text rather than an acceptance decision.
- **Role-routing evidence in the send envelope**: `role`, `resolved_model`,
  `resolved_model_identity`, `resolved_agent`, `route_source` alongside every
  accepted v0.3-A send field, so a planner can audit which role and route were
  used; an accepted bridge failure keeps its exact code and additionally reports
  the attempted route.
- **140 offline tests** (`tests/test_v03c_role_config.py`,
  `tests/test_v03c_roles.py`, `tests/test_v03c_role_tools.py`,
  `tests/test_v03c_role_concurrency.py`, `tests/test_v03c_stdio_roles.py`,
  `tests/v03c_helpers.py`) plus the v0.3-C spec/acceptance documents.

### Notes

- **No orchestration**: no automatic implementer -> reviewer sequencing, no
  repair loops, no retry loops, no automatic acceptance or rejection, no merge
  decisions, no Planner role inside DevRelay, no session creation or lifecycle
  management, no model ranking/fallback, no WebUI/HTTP control API.  The external
  planner still decides which role to call, when and what to do next.
- **Backward compatibility**: the raw `opencode_send_prompt` tool is byte-for-byte
  unchanged (caller-supplied model/agent still reach the wire, no role key in its
  envelope) and both paths can be used in the same session.  Role routing is
  never inferred from prompt text, session title or model availability.
- **The v0.3-B execution boundary still applies**: all twelve tool bodies run
  under the same one per-surface execution lock (no role lock, no scheduler), so
  the accepted single-writer filesystem ledger never sees concurrent access.
- `MCP_SERVER_VERSION` is `0.3.0-c` (the advertised surface changed from nine to
  twelve tools).  The real role-routed model smoke is **done** (see "Accepted
  (real role-routing smoke)" above); a first two-role harness run failed only
  because it required the whole normalized assistant text to equal a sentinel -
  real providers also return a reasoning part that the accepted v0.3-A
  normalization currently presents as `kind="text"` (recorded as a non-blocking
  P3 in `docs/BACKLOG.md`).  That history is preserved, not rewritten.

## Unreleased - v0.2-B project profiles (candidate under independent review)

Reusable project policy profiles on top of a frozen, integrity-verified task
policy. **Not released**: the package version stays `0.1.0`, nothing is pushed,
merged, tagged or published, and all v0.2-B behaviour was validated offline with
fake providers (no real Codex invocation, no real reviewer endpoint).

### Added

- **Project profiles** - `.devrelay/profiles/<name>.yaml` plus an ordered
  `profiles: [base, python]` selector in `.devrelay/config.yaml`. Precedence:
  packaged policy defaults < profiles in selector order < workspace overrides.
  Profile files are *policy only*: `review.provider`, `codex.*`, `git.*` and the
  selector itself are rejected (the model is the allowlist). Limits: <= 8
  profiles, <= 1 MiB per file, `yaml.safe_load`, no `extends`, no user/global
  profile directory, no CLI override, one name grammar, strict path containment.
- **Raw profile diagnostics** - `devrelay profile list|show|validate`, which work
  even when the selector is broken, and `profile validate` reports *all*
  problems (invalid filenames, per-file errors, selector syntax, duplicates,
  missing references) instead of stopping at the first one.
- **`devrelay config show` / `--resolved`** - the first prints live runtime
  wiring plus the raw, unresolved selector and explicitly says it is not the
  effective task policy; the second is the authoritative, fail-closed resolver.
- **`devrelay doctor`** now reports raw profile inspection and the full policy
  chain separately, flags pre-schema-5 tasks and profile drift, and has
  `--strict` for CI use (exit non-zero when anything is not OK).
- **Snapshot integrity** - `tasks/<id>/config.snapshot.yaml` is verified by
  SHA-256 over its exact on-disk bytes *before* it is parsed, and
  `devrelay unblock --reason "..." --refresh-policy` recovers a missing,
  invalid or hash-mismatched snapshot (recording `before_snapshot_available`
  instead of inventing a before-snapshot).

### Changed

- **Runtime wiring and task policy are separate types.** `WiringConfig`
  (`review.provider`, `codex.*`) is live and never frozen; `PolicyDocument`
  (`pipeline`, `budget`, `review` policy knobs, `tests`, `scope`, `baseline`,
  `git`) is resolved once and frozen into the task. `PipelinePolicy` accepts only
  a `PolicyDocument`; a workspace config can no longer be used as task policy.
- **`state_schema_version` 4 -> 5**: tasks persist `policy_snapshot_path`,
  `policy_config_sha256` and `policy_provenance` (selector, per-profile raw-byte
  hashes, workspace-config hash, generation, integrity). Before the first write
  that upgrades an older task, its state is copied once to
  `state.v<old>.json.bak`. State written by a *newer* DevRelay now produces a
  dedicated `state_schema_too_new` diagnostic instead of a model error.
- **All textual artifacts are written as UTF-8 with LF endings**, and every
  recorded digest is the digest of the bytes actually written (on Windows,
  `Path.write_text` used to turn LF into CRLF while hashes were computed over
  LF text, so recorded hashes could never match the disk).
- **`status`, `usage`, `diff` and `logs` are state-only**: they never validate
  live policy, never resolve the profile chain and never read a profile file, so
  deleting or editing profiles cannot break them. Live drift belongs to
  `doctor` and `config show --resolved`.
- **Execution commands classify the snapshot before any provider object is
  constructed**, so a damaged snapshot fails closed without building a Codex or
  reviewer client.
- `devrelay init` installs a workspace template (wiring + selector + commented
  policy overrides) instead of a copy of the policy defaults, and creates
  `.devrelay/profiles/`. The packaged `src/devrelay/profiles/default.yaml` is now
  the single editable default authority: the in-code `DEFAULT_PROFILE_YAML`
  literal and the repository-root `profiles/default.yaml` copy are gone.

### Removed

- The v0.2-A silent policy downgrade: a task whose snapshot is missing, invalid
  or hash-mismatched no longer continues under live wiring/workspace defaults.
  Only genuine pre-snapshot ("legacy") tasks resolve live policy, and the
  execution path never writes `policy_source`.

### Fixed (independent-review P2 remediation)

- **P2-1 - real state-schema migration.** The first *mutating* write of a task
  whose persisted `state_schema_version` is older than the current schema now
  keeps the exact previous `state.json` bytes in a one-time
  `state.v<old>.json.bak` and only then writes the upgraded (schema-current)
  document. The backup is created once, is never overwritten, and a backup
  failure aborts the write with `state.json` untouched; the upgraded document is
  a serialized copy, so the caller's in-memory task is never mutated and a
  failed write stays retryable. v5-only fields can no longer land in a file that
  still claims schema 4, and `doctor` stops reporting a permanently pending
  migration. Read-only commands still never migrate and never create a backup.
  A *migrated* v0.2-A task still uses its digest-less legacy snapshot: the
  integrity-metadata requirement now keys off the recorded snapshot path rather
  than the bare schema number.
- **P2-2 - refresh evidence is append-only.** Refresh evidence identity no
  longer comes from `len(task.policy_refreshes) + 1`. Every attempt that starts
  writing evidence consumes a unique, never-reused *evidence attempt* number
  allocated from both persisted records and on-disk `policy-refresh-NN-*`
  artifacts (gaps tolerated, `max(seen) + 1`), and the evidence files are
  written with create-new writers that refuse to replace an existing path. A
  failed attempt's artifacts therefore survive a retry untouched: attempt 01
  stays on disk as orphan evidence while the successful retry is attempt 02 and
  may still advance generation 1 -> 2. An on-disk artifact is evidence of an
  *attempt*; a refresh counts as applied only when the persisted task references
  that record and its generation/digest/provenance describe the applied
  generation. Orphan evidence is never deleted, never overwritten and never
  treated as applied.

## Unreleased - v0.3-B accepted (MCP tool surface)

A narrow local **Model Context Protocol adapter** over the accepted v0.3-A
OpenCode bridge, so an MCP-capable client (for example a ChatGPT planner) can
invoke DevRelay programmatically.  **Accepted internally / unreleased**: the
final real MCP smoke passed at accepted candidate
`d058d62341a173414bdba88fe357b08c236c8bb4`, the package version stays `0.1.0`,
the supported public release remains v0.1.0, nothing is pushed, merged, tagged or
published, and no public v0.3 release exists.  The automated suite still makes no
real network/model call; the real chain was one separately authorized one-shot
smoke.

### Accepted (final real MCP smoke)

- Official MCP Python SDK **2.2** (`mcp>=2.2,<3`), stdio-only MCP server, exactly
  nine bounded tools, one-workspace binding per server process.
- Truthful structured envelopes (`schema_version 1`) with `structuredContent` plus
  a JSON text fallback, and `isError` mechanically `not ok`.
- Exact-one-submission semantics inherited unchanged from v0.3-A (never retries,
  never falls back, never resubmits; `submission_uncertain`/`reply_pending` are
  reported as evidence).
- **Global serialized MCP execution** over the accepted filesystem ledger: one
  process-wide re-entrant lock covers all nine tool bodies, because the accepted
  ledger allocates call identities with a non-atomic read-modify-write.
- Final real smoke `PASS — V0.3-B LOCAL REAL MCP SMOKE`: real `mcp 2.2.0` client
  -> stdio -> `devrelay mcp serve --workspace <ws>` -> accepted v0.3-A bridge ->
  real OpenCode `1.18.11` -> explicit `opencode-go/deepseek-v4.1-flash`.  Exactly
  one MCP `opencode_send_prompt`, exactly one `POST /session/{id}/message`
  (HTTP 200, no `/prompt`, no `prompt_async`, no retry, no fallback), provider
  inference confirmed, `isError=false`, `ok=true`, `submission_uncertain=false`,
  `reply_pending=false`, `retry_safe=false`, assistant reply exactly
  `DEVRELAY_V03B_MCP_OK`, final history `user -> assistant`, 13 settled ledger
  records with zero `ISSUED` and no raw prompt in durable evidence.
- Complete containment and cleanup: disposable workspace unchanged (README hash,
  clean `git status`, no model-created files), disposable session deleted
  (`GET` -> 404), dedicated OpenCode stopped, MCP process exited, evidence kept
  outside the repository.

### Added

- `devrelay mcp serve --workspace <absolute-path>`: a local **stdio** MCP server
  bound to exactly one DevRelay workspace.  stdout carries MCP protocol frames
  only, diagnostics go to stderr, there is no HTTP listener and no LAN exposure;
  an invalid workspace fails closed (exit 2) before any tool is served.
- Nine high-level tools over the accepted v0.3-A bridge: `devrelay_status`,
  `opencode_health`, `opencode_list_sessions`, `opencode_get_session`,
  `opencode_read_messages`, `opencode_calls`, `opencode_send_prompt`,
  `opencode_wait_idle`, `opencode_interrupt`.  No dangerous low-level tool
  (HTTP/shell/file/git/config/env/delete/token) is exposed.
- One stable result envelope (`schema_version 1`, `ok`/`tool`/`data`/`error`) with
  `structuredContent` plus a JSON text fallback; a failed call also sets the
  protocol `isError` flag while keeping the full envelope.
- Honest MCP tool annotations: read-only hints for read tools, side-effecting for
  `send_prompt`/`interrupt`, no false idempotency claim, and planner-oriented
  descriptions that say "exactly one prompt, never retries, do not resubmit when
  `submission_uncertain`/`reply_pending`".
- Strict `<providerID>/<modelID>` model grammar, bounded prompt/timeout/limit
  validation, and a strict read-only ledger view that reports corruption instead
  of returning an empty list.
- Offline acceptance harness: an in-process tool matrix (real bridge over the
  deterministic stub) and a real stdio subprocess suite driven by the official
  MCP client and a raw JSON-RPC probe against a loopback fake OpenCode server.

### Fixed (independent-review gate remediation)

- **Envelope truthfulness (P1)**: `opencode_get_session` reported `ok: true` /
  `isError: false` for HTTP 500, malformed provider responses and unreachable
  endpoints.  Every bridge-backed tool now derives its envelope from one shared
  rule in the tool layer (`McpToolSurface._bridge_envelope`): `ok` is true only
  when the accepted operation reached that tool's success state, and the protocol
  flag is mechanical (`isError == not ok`, no per-tool special case in the
  server).  Sanitized operation evidence is always preserved in `data`.
- **stdio harness candidate pinning**: every child MCP process is launched with
  `PYTHONPATH` pinned to the checkout under test and a stripped environment, so
  the suite can no longer silently exercise an ambient editable installation; a
  mutation-propagation test proves the executed tree is the one the harness
  points at.
- **Malformed MCP input**: the documented behaviour now matches the observed SDK
  behaviour - unparseable / non-JSON-RPC / method-less frames are silently
  dropped (no reply, process alive), unknown methods answer `-32601`, invalid
  params answer `-32602`; DevRelay never claims a protocol error it does not emit.
- **Ledger ordering**: `opencode_calls` orders records by numeric call sequence
  (`OC-9999` before `OC-10000`) and reports a non-`OC-<number>` file instead of
  ranking it.
- **Cancellation evidence**: strengthened tests prove no submission is recorded
  before the gate, an already-issued POST leaves an inspectable settled record
  with no `retry_safe` claim, no automatic resubmit/interrupt happens, and the
  execution lock is released for later calls.
- **Global execution serialization (P2, post-re-gate)**: parallel MCP tool
  executions raced the accepted v0.3-A filesystem ledger, which allocates durable
  `OC-*` identities with a non-atomic read-modify-write and refuses identity
  reuse.  With 8 concurrent `opencode_read_messages` on one server, 7 of 8 calls
  failed (`internal_error` from a `PermissionError` on the shared
  `.sequence.json.tmp` rename, and `opencode_ledger_error` from a colliding
  `OC-0001`) and the durable ledger was truncated to 2 of 8 records.  All nine
  tool bodies - reads included - now run under exactly **one** process-scoped,
  re-entrant execution lock (`McpToolSurface._execution_lock`); the redundant
  `_side_effect_lock` and the separate bridge-construction lock are gone, so
  there is no lock order to get wrong and no scheduler to reason about.  The same
  8-call batch now returns 8/8 success with 16 unique, settled, contiguously
  numbered call identities and a measured maximum of one concurrent ledger entry.
  `devrelay_status` reports `execution_serialized: true`.  Consequences: a long
  `opencode_wait_idle` body delays other calls in the same process, cancelling a
  request does not let another body overtake an already-running one, and two
  `devrelay mcp serve` processes over one workspace are still not serialized
  against each other (single-writer ledger hardening remains deferred).

### Notes

- v0.3-A sources, semantics and tests are unchanged; every v0.3-A guarantee
  (exactly one submission POST, no retry/fallback, submission-uncertainty
  distinction, stale-reply suppression, durable accounting, credential/prompt
  containment) holds through the MCP layer.
- **All** tool execution (reads included) is serialized per MCP server process by
  one re-entrant execution lock, because the accepted v0.3-A filesystem ledger is
  a single-writer store; cancelling a local MCP request never implies "not
  submitted" and never triggers an automatic abort.
- The real MCP-client smoke is **done** (see "Accepted (final real MCP smoke)"
  above).  Still deferred: Streamable HTTP/SSE transport, multi-process /
  multi-workspace serving, and any role routing or orchestration (v0.3-C, not
  started).

## Unreleased - v0.3-A accepted (OpenCode session bridge)

A narrow, provider-contained bridge to one explicitly configured, already running
OpenCode server. **Accepted internally and still unreleased**: the package
version stays `0.1.0`, nothing is pushed, merged, tagged or published, and the
supported public release remains v0.1.0.

### Accepted

- **Final decision:** `ACCEPT — V0.3-A OPENCODE SESSION BRIDGE`, functional
  candidate `bcf9627e92ef839abb756810e3c615e6d01b6576`; v0.3-A functional
  development is closed and the runtime implementation is frozen at that commit.
- **Real compatibility verified** against a dedicated **OpenCode 1.18.11** server:
  health, prompt-free session creation, explicit disposable session, workspace
  ownership, empty baseline read, exactly **one** real
  `POST /session/{id}/message` with the explicit model
  `opencode-go/deepseek-v4.1-flash` (wire `{providerID, modelID}`), provider
  inference confirmed, synchronous `{info, parts}` response (HTTP `200`,
  `application/json`) normalized to one correlated assistant reply whose text is
  exactly `DEVRELAY_A33_OK`, runtime status via `GET /session/status` (idle
  represented by the session's absence from the map), real provider message
  ordering **oldest → newest**, stable window (`cursor_unknown=false`,
  `replayed=false`, no truncation), workspace unchanged, 15 settled ledger
  records with no `ISSUED`, no raw prompt and no credentials persisted, and the
  disposable session/server cleaned up afterwards.
- **Historical A33 attempts are preserved as evidence, not rewritten:** the first
  attempt was `BLOCKED` (no provisioned endpoint/session), the first real
  protocol attempt was `FAIL` (the obsolete `/session/{id}/prompt` route does not
  exist on 1.18.11), a second real attempt was `FAIL` (the *user's* global default
  model referenced a provider disabled by the same configuration), and a
  zero-model diagnostic proved that failure was an OpenCode/environment
  configuration issue with **no DevRelay defect** before the final explicit-model
  smoke passed.
- Non-blocking follow-ups (F1 follow-up-only hardening, Basic-vs-Bearer auth
  compatibility, multi-process ledger locking, cross-host/container path mapping,
  server-side pagination, corrupt-ledger UX, Windows Codex `pwsh.exe`, remaining
  v0.2-C real E2E evidence) stay recorded in `docs/BACKLOG.md`.

### Added

- `devrelay/opencode/`: normalized DevRelay-owned models (`OpenCodeSession`,
  `OpenCodeMessage`/`OpenCodeMessagePart`, `OpenCodeMessagePage`,
  `OpenCodeHealth`, `OpenCodeOperationResult`, `OpenCodeCallRecord`), an explicit
  operation/call state vocabulary, an HTTP transport with one configured endpoint
  (never port scanning) and bounded response reads, a durable per-request call
  ledger (`.devrelay/opencode/calls/<call-id>.json`, monotonic `OC-NNNN` ids) and
  the `OpenCodeBridge` capability surface: `health`, `list_sessions`,
  `get_session`, `read_messages`, `send_prompt`, `wait_idle`, `interrupt`.
- Workspace/session ownership enforcement: the configured workspace must match the
  session's reported workspace; unknown sessions and cross-workspace reuse are
  hard failures, and a session that reports no workspace fails closed unless the
  unsafe opt-in is set explicitly.
- Bounded `wait_idle` (idle/terminal or `TIMED_OUT`, no retry) and interrupt that
  reports `interrupt_unsupported` instead of pretending a cancellation happened.
- `opencode:` runtime wiring in the workspace config (explicit `base_url`,
  workspace, optional session/agent/model, timeouts, response/message caps) plus
  `DEVRELAY_OPENCODE_TOKEN` read from the environment only. The section is never
  task policy: it is excluded from the frozen policy projection and tolerated as
  a known wiring key in legacy full-config snapshots.
- `devrelay opencode health|sessions|show|read|send|wait|interrupt|calls` — thin
  CLI wrappers that print normalized results (no OpenCode logic in the CLI).
- `tests/opencode_stub.py` + `tests/test_v03a_opencode.py`: deterministic offline
  coverage of discovery, selection, reading, one prompt, idle completion, provider
  failure, malformed response, timeout, interrupt, unknown session,
  workspace/session mismatch, cursor replay and accounting.

### Fixed (independent-review remediation)

Remediation of the `REQUEST_CHANGES - V0.3-A` findings, still entirely offline
(58 of the 66 new tests in `tests/test_v03a_remediation.py` fail against the
pre-remediation source):

- **P1** `wait_idle` now establishes the whole-operation deadline *before* the
  ownership probe and clamps every request (probe included) and the inter-poll
  sleep to the remaining budget, so the declared/idle timeout is genuinely
  enforced and nothing runs after the return.
- **P1** `read_messages` keeps the **newest** messages (`messages[-max:]`) and
  reports `provider_message_count`/`window_truncated` instead of head-truncating
  a large payload and calling it a complete replay; `max_messages` is bounded to
  the 200-message wire maximum in config validation.
- **P1** `send_prompt` correlates a reply only as a *new assistant* message
  (inline candidate or one explicit follow-up read): no stale reply, no
  id-bearing envelope treated as a reply, `reply_pending` when nothing new is
  visible, a follow-up `404`/`500` reported as a post-acceptance condition
  (never "your prompt was not submitted"), merged accounting on every path, and
  no automatic resubmission.
- **P1** `DEVRELAY_OPENCODE_TOKEN` joined `CODEX_CHILD_ENV_DENYLIST`: a Codex
  child process never inherits the OpenCode bearer credential.
- **P2** `trust_env=False` on the control-channel client (ambient proxy/CA
  variables cannot reroute it); strict session-id grammar plus a returned-id
  mismatch check (invalid ids issue zero requests); explicit interrupt semantics
  (`204`/JSON accepted → `INTERRUPTED` with `interrupt_verified: false`, `404` →
  `interrupt_session_not_found`, `405`/`501` → `interrupt_unsupported`, otherwise
  the real provider error or `MALFORMED_RESPONSE`); provider echoes of the prompt
  or token are scrubbed from error snippets in the submission *and* in
  post-submission reads/polls (literal-value scrubbing, documented as such, with
  the unsalted prompt SHA-256 documented as an identifier and not as secrecy);
  ledger allocation fails closed (corrupt sequence, identity collision) and
  recovers from existing records otherwise; `--json` keeps a non-zero exit status
  for a failed operation in both output modes.
- Config hardening: base-URL validation (scheme/host/embedded credentials/path
  prefix/query/fragment), fail-closed numeric bounds, `extra="forbid"` preserved,
  and an empty (`null`) section body now means "not configured" instead of a
  validation error.

### Documentation

- `docs/v0.3/V03A_SPEC.md`, `docs/v0.3/V03A_ACCEPTANCE.md`,
  `docs/v0.3/V03_PLAN.md`, and `docs/BACKLOG.md` (which carries the pending
  v0.2-C real Codex smoke and a separate Windows Codex shell P2 investigation).

### Fixed (A33 real-protocol remediation)

Real-protocol compatibility with the installed OpenCode 1.18.11 server, after the
authorized A33 smoke returned `FAIL` on a genuine product/protocol mismatch
(28 of the 30 new tests in `tests/test_v03a_real_protocol.py` fail against
`780c2fd`; no real model call was made during this remediation):

- **Submission route**: the default prompt path is now the documented
  `POST /session/{id}/message` (the old `/session/{id}/prompt` route does not
  exist on 1.18.11 - the server answers unmatched paths with a `200 text/html`
  SPA shell).  There is deliberately **no** compatibility fallback and no switch
  to `prompt_async`: exactly one POST, on the real route.
- **Request contract**: the minimum body is
  `{"parts":[{"type":"text","text":...}]}` with every optional member omitted;
  `agent` is forwarded as the documented string and `model` is encoded as the real
  structured identity `{providerID, modelID}` via the explicit
  `<providerID>/<modelID>` grammar - an unmappable override fails locally before
  any request is issued.
- **Response normalization**: the real synchronous `{info, parts}` body
  normalizes to exactly one assistant message (role must be `assistant`, text
  parts normalize, unknown parts stay limited, raw wire objects never escape); an
  incomplete/non-assistant body remains an honest pending/fail-closed result.
- **Runtime status**: `wait_idle` polls the real `GET /session/status` map
  (`idle` completes, `busy`/`retry` keep polling with retry evidence preserved in
  `status_detail`, a **missing entry means idle** - verified: 1.18.11 omits
  non-running sessions, and the session object has no state field), instead of
  polling a session state field that does not exist. All deadline/ownership/
  clamping/accounting guarantees are unchanged.
- **2xx evidence**: a 2xx is credible acceptance only when its media/body contract
  matches the endpoint. A JSON body with an unusable body stays "accepted,
  unusable body"; a 2xx whose media type cannot carry the documented contract
  (the SPA `text/html` fallback) is **submission-uncertain** with the media type
  preserved on the result (`submission_contract`) and on the durable record
  (`response_media_type`), never presented as accepted and never retried.

### Fixed (third independent-review blocker remediation)

Third remediation pass on `6e0eb61` (22 of the 23 new tests in
`tests/test_v03a_third_remediation.py` fail against it), still entirely offline:

- **Blocker P1** transport failures around the submission POST are now classified
  instead of treated alike: `connect_timeout`/`pool_timeout`/`connect_error` and
  local refusals prove nothing was submitted, while `read_timeout`,
  `write_timeout`, read/write errors, remote protocol errors and anything
  unclassified are *submission-uncertain*.  An uncertain POST reports
  `submission_uncertain: true`, `reply_pending: true` (unless a new assistant
  reply is correlated), explains that the prompt may already have been accepted
  and that DevRelay will not resubmit automatically, performs exactly one bounded
  follow-up read and never retries the POST.
- **Blocker P2** a post-acceptance result can no longer expose the
  pre-submission message window: `messages` is empty and `page` is `null`
  whenever no new assistant reply was positively correlated (follow-up 500,
  timeout, provider unavailable, vanished session, malformed follow-up, still
  pending, or an uncertain submission), so `messages[-1]` can never be mistaken
  for the answer to the prompt just sent.  The boundary cursor stays available as
  `reply_boundary`.
- **Adjacent** the human CLI now states the submission verdict and the reply
  state explicitly ("submission accepted (HTTP nnn …)", "submission uncertain …
  do not resubmit automatically", "submission rejected (HTTP nnn)", "submission
  not accepted", "reply pending: no new assistant message was confirmed"), never
  prints an old reply, and agrees with `--json`; a genuine HTTP rejection keeps
  its status as submission evidence (`submission_status`) and is not described as
  an unusable body; a malformed follow-up clears the page as well as the
  messages; and `submission_uncertain` results are never a clean exit.

### Fixed (second independent-review remediation)

Second remediation pass on `f5d487d` (36 of the 49 new tests in
`tests/test_v03a_second_remediation.py` fail against it), still entirely offline:

- **P1** every Codex child process - legacy text runtime, `--version`,
  `exec --help`, capability detection, doctor probes - now spawns through one
  centralized credential-scrubbing adapter, so the OpenCode token and the other
  denylisted provider credentials can no longer reach any Codex child (the parent
  process keeps its credentials).
- **P1** a 2xx prompt submission with an unusable body (`204`, empty `200`,
  invalid JSON, oversized) is a *post-acceptance* result, not a failed
  submission: `submission_body`/`submission_status` record the evidence, the
  bounded follow-up read still runs, `reply_pending` stays honest and nothing is
  resubmitted.
- **P1** the anti-DoS pre-cap on provider message lists keeps the true newest
  tail (previously `raw[:2000]` could hide the newest messages of a large session
  and break reply correlation).
- **P1** provider echoes of the prompt/token are now scrubbed in their JSON-,
  backslash- and percent-escaped forms (two escaping levels) on the POST, the
  follow-up read and every wait/poll request, before anything reaches the ledger,
  the result or the console.
- **P1** parser bombs (extreme JSON nesting, over-long integer literals) and
  invalid JSON normalize into `MALFORMED_RESPONSE` with a specific error type,
  and the durable call record is always settled - a provider body can no longer
  strand a record at `ISSUED` or traceback the CLI. Programming errors still
  propagate.
- **Adjacent** operation accounting survives a failing ownership/boundary probe;
  a malformed follow-up keeps the `send_prompt` identity; dot-segment session ids
  are refused; the full (untruncated) returned session id is compared; malformed
  URL authorities are configuration errors before httpx and config errors no
  longer echo an embedded password; a refused create-new leaves no phantom
  in-memory ledger record.

## Unreleased - v0.2-C candidate (structured Codex runtime)

Structured, isolated, tamper-evident and replayable Codex runtime. **Not
released**: version stays `0.1.0`, nothing is pushed/merged/tagged/published, and
everything below is validated offline with a stub Codex CLI (no model call, no
network).

### Added

- Structured implementer contract: `--output-schema` + `--output-last-message`
  with a validated `ImplementationResult` (`schema_version = 1`); `--json` events
  are observational only and never required for a run to count.
- Transient raw result staging under `.devrelay/tmp/runtime/<attempt-id>/`:
  bounded read, `raw_result_sha256`, sanitized immutable `result.json` (create-new
  writers), best-effort removal, stale-staging cleanup-or-refuse policy.
- DevRelay-owned Codex argv: `exec`, `--sandbox workspace-write` (exactly once),
  `--ignore-user-config`, `--ignore-rules`, `--json`, schema/result flags, cwd and
  stdin prompt. `-p/--profile`, user `--sandbox`, `--add-dir`, `--cd`,
  `--skip-git-repo-check`, `--approve-for-me`, bypass flags, output-path flags and
  unsafe `-c` namespaces are rejected; a repository Codex config fails structured
  mode closed (`codex.runtime_mode: text` is the explicit opt-out).
- Codex child environment scrub (reviewer + enumerated LLM provider credentials),
  honestly documented as an explicit denylist, not general secret isolation.
- Control-plane guard: in-memory PRE manifest, POST verification before any state
  re-read, `codex_control_plane_violation` fail-closed path, metadata-only
  violation evidence (no raw tampered content), durable hold with
  verification-gated recovery (`--acknowledge-control-plane-violation`,
  `--restore-state-from-pre`).
- Durable implementer milestones (`PROCESS_EXITED` … `COMPLETION_READY` …
  `COMPLETION_APPLIED`) with idempotent application; `attempt_in_flight` is only
  cleared once a replay-safe verdict exists.
- Completion replay: a `COMPLETION_READY` attempt with matching identities is
  applied locally with **0 external calls**; drift blocks as
  `implementer_replay_workspace_changed` / `replay_control_state_changed`;
  `devrelay unblock --replay-completion` applies it explicitly after a human
  restored the workspace.
- Two-stage reconciliation (`implementation-reconciliation.json`,
  `test-reconciliation-NN.json`) surfacing claimed-vs-observed files, rejected
  traversal claims, unknown result field names and test-claim disagreements.
- Baseline root hardening: `baseline.json`/`manifest.json`/`tracked.patch` are
  content-hashed by the guard and untracked blobs are verified against their
  declared SHA-256 before use.
- Bounded, deadlock-free process capture (always-drain reader threads, head+tail
  retention) with truncation evidence, `env_remove` support and terminate→kill
  fallback.
- `doctor` reports the effective runtime mode, structured capability and the
  scrubbed credential names; `status`/`usage` show runtime milestones and results.

### Changed

- `state_schema_version` 5 → 6 (durable milestones, workspace/control-plane
  identity, runtime evidence), reusing the existing migration/backup/too-new
  machinery; v0.2-B tasks keep loading and read-only commands still never migrate.
- Bumped `MAX_SUPPORTED_STATE_SCHEMA` accordingly; a v0.2-B binary refuses v6 with
  `state_schema_too_new` instead of guessing.

### Fixed (independent-review P1 remediation)

- **P1-A — structured mode was silently downgraded on every frozen-task CLI
  path.** The effective runtime mode was read from the *task policy* source, but
  the CLI builds engines with `config=None` for tasks that own a frozen snapshot,
  so `devrelay continue` fell back to `text`: no `--output-schema`, no bounded
  result read, no child environment scrub, no control-plane PRE/POST guard and no
  containment — a silent loss of the whole v0.2-C contract. The mode now comes
  from the live `WiringConfig` only (`self.runtime_config.codex.runtime_mode`),
  the frozen document stays authoritative for policy only (it carries no `codex`
  section at all), and a mis-wired engine fails pre-flight instead of
  downgrading. `status` prints the effective mode as `Runtime:` and `doctor`
  reports mode, capability and containment. Regression coverage drives the *real
  CLI* end-to-end (`test_cli_continue_runs_the_structured_runtime`,
  `test_cli_runtime_mode_text_is_explicit_and_stays_text`), not just an internal
  helper.
- **P1-B — a detached descendant could mutate the control plane after POST.**
  Nothing contained the Codex process tree: the child could spawn a detached
  grandchild that outlived it, wait for the POST manifest comparison to pass and
  then rewrite `.devrelay/tasks/<id>/state.json` (and drop arbitrary files) with
  no violation and no trace. New module `devrelay/workspace/containment.py`
  provides the abstraction (`spawn_contained` / `wait_contained` /
  `terminate_contained` / `kill_contained` / `all_contained_processes_dead`) and a
  race-free Windows Job Object backend (`KILL_ON_JOB_CLOSE`, no breakaway, broker
  hand-off *before* Codex runs). The runner ends a contained window by closing the
  job and verifying `all_contained_processes_dead()` **before** the engine
  computes POST, so a surviving descendant can no longer land after the guard. The
  refusal is honest: on POSIX (where a process group cannot contain a
  `setsid`/double-fork descendant) structured mode fails pre-flight with
  `codex_process_containment_unsupported` and **0 provider calls** instead of
  claiming weak containment, and `doctor` flags the missing capability.
  Containment facts (`containment`, `containment_all_dead`) are persisted in the
  attempt runtime evidence, in the violation report and in the hold. If the tree
  cannot be confirmed dead within the containment deadline, the run fails closed
  as `codex_containment_unverified`: the POST comparison is skipped entirely, no
  state is overwritten, a post-mortem hold is written for manual recovery, and
  the invocation stays charged (the process really ran).
- **P1-D — a consumed call disappeared from `provider_calls`/budget on the
  control-plane-violation path.** The pre-run attempt write persisted a stale
  in-memory `TaskRun` and erased the accounting intent recorded moments earlier,
  so a *real* Codex invocation that was voided by the guard left
  `provider_calls == []`, budget usage `0` and an orphan `policy/calls/*.json`
  entry. The pre-run write now merges the persisted accounting facts (call list
  plus the monotonic sequencing counters, `max()` of both sides) into the record
  it writes while the caller's in-memory transition is preserved. A voided run is
  now fully charged: call id `DR-0001-C0001`, usage `implementer_calls == 1`,
  ledger entry present, hold referencing the same call id, and the trusted
  parent-held `*-state.pre.json` copy contains it.
- **C7 / C16 acceptance closure.** `C7`: a non-zero exit with a *valid* model
  result is still a failure (`implementer_failed`, no `COMPLETION_READY`, no
  durable `result.json`) and is still charged once. `C16`: unicode workspace
  roots, staging paths and claimed file names survive the whole structured
  runtime (manifest, reconciliation, evidence).

### Fixed (real-smoke structured schema remediation)

- **The transport schema was rejected by the real Structured Outputs endpoint.**
  The one approved real Codex smoke (call `DR-0001-C0001` against `301e891`)
  authenticated via ChatGPT, ran the real structured argv, passed containment and
  a clean control-plane check, and was then refused with HTTP 400
  `invalid_json_schema`: *"'additionalProperties' is required to be supplied and
  to be false"*. `result_json_schema()` emitted a tolerant schema
  (`additionalProperties: true`, only three required root fields), which the
  offline stub accepted, so no test could see it. The transport schema is now
  strict: every object node (root and `tests_run` items) sets
  `additionalProperties: false`, `required` lists exactly the declared
  properties, `schema_version` is `{"type": "integer", "enum": [1]}`, and
  optionality is expressed only by deterministic empty values (`[]` / `""`).
  The local post-parse model is unchanged and stays defensive (caps,
  `schema_version`/status enforcement, claim-path rejection, unknown-field
  recording) - a strict transport contract is not a weaker trust model.
- **The offline Codex stub is now as strict as the real endpoint.** Before
  writing a structured result it lints the supplied `--output-schema`
  recursively (closed objects, fully required objects, declared required keys,
  `schema_version` pinned to 1) and refuses (`invalid_json_schema`, exit 3)
  otherwise, so the pre-fix schema now fails offline too. Regression coverage:
  `tests/test_v02c_schema_strictness.py` (recursive strictness lint, nested item
  contract, no risky constructs, pre-fix schema rejected end-to-end with exactly
  one charged call, strict-schema happy path, parser caps/security intact).

## Unreleased - v0.2-A candidate (audit remediation, closure audit pending)

Automatic review loop with an enforced execution budget, plus the remediation of
the independent audit of commit `fe4b044` (one P1, three P2, six P3 findings).
**Not released**: the package version stays `0.1.0`, nothing is pushed, merged,
tagged or published, and the behaviour below was validated with fake providers
only (no real Codex invocation and no real reviewer endpoint were used).

### Fixed

- Baseline capture no longer fails with `git add -A -- . :(exclude).devrelay
  failed: The following paths are ignored ...: .devrelay` in repositories whose
  `.gitignore` lists `.devrelay/` (the normal, documented setup). The worktree
  tree is now built from an explicit list of eligible paths (tracked changes +
  non-ignored new files, `.devrelay` filtered in DevRelay code) against the
  temporary index, never from an explicitly named ignored pathspec, and never
  with `git add -f` (which would include unrelated ignored files). A repository
  that *tracks* `.devrelay/**` is excluded symmetrically. Regression coverage:
  `tests/test_baseline_ignored_self.py`.

### Fixed (audit remediation)

- **P1-01** - the crash window between persisting a reviewer result and applying
  it can no longer cost a second paid reviewer call. A persisted, schema-valid,
  sanitized result is now an authoritative, replayable result: the next
  `continue` replays it locally with **0 external calls** and enters the
  policy-defined state (`FIX_REQUIRED` / `FINAL_GATE_REQUIRED` / `BLOCKED`).
  An *uncertain* call still fails closed - DevRelay never invents a result.
- **P1-01 (idempotency)** - the whole semantic application (history, seen
  counters, findings, applied marker, transition, audit) lands in **one atomic
  state write**, guarded by a stable result identity plus an
  `AppliedReviewRecord`. Restart replays therefore never duplicate history,
  counters, transitions or audit events; content equality alone is not treated
  as proof (two legitimately identical rounds still apply separately), and a
  missing terminal transition is completed locally only with proof that nothing
  happened since.
- **P2-01 / P2-02** - one durable, task-scoped identity system replaces
  process-local counters and success-derived numbering: call ids
  (`DR-0001-C0007`), implementer attempts (`DR-0001-A0002`) and review attempts
  (`DR-0001-R0002`) are allocated from persisted monotonic sequences before the
  invocation, never reused after a failure, and never reset by `unblock` or a
  policy refresh. Calls link to attempts (`parent_attempt_id`, `call_ids`).
- **P2-01 / P2-02 (evidence)** - immutable evidence is keyed by those identities
  (`policy/calls/<call-id>.json`, `policy/attempts/<attempt-id>.json`,
  `policy/runs/<attempt-id>-*.json`, `logs/<attempt-id>.*`,
  `reviews/review-NN-<attempt-id>-meta.json`); a retry can no longer overwrite a
  failed attempt's or another call's evidence. The legacy `NN`-named artifacts
  remain as documented "latest view" convenience copies.
- **P2-03** - `unblock --refresh-policy` preserves the previous policy:
  `PolicyRefreshRecord` plus `policy/policy-refresh-NN-{before,after}.yaml` and
  `-NN.json` (before/after SHA-256, actor, reason). Usage is never reset,
  deleted or renumbered, and existing calls count against the new limits.
- **P3-01** - `max_response_chars` is documented (config, README, error message)
  as a parsing/persistence cap; the HTTP client may buffer the body first, so it
  is not a network-level memory limit.
- **P3-02** - retry phase labels follow the failure cause; a mixed
  format/transport/format sequence no longer mislabels a transport retry as
  `REVIEW_FORMAT_RETRY`.
- **P3-03** - finding fingerprints normalize path separators and file order but
  never case-fold paths (POSIX repositories may contain both `A.py` and `a.py`).
- **P3-04** - `policy_source` is persisted as `snapshot` at task creation;
  `status`/`usage` resolve it read-only and never rewrite task state (legacy
  tasks keep reporting `live-fallback` unmodified).
- **P3-05** - AUD-09 stays open as a backlog item; `unblock` still clears the
  block record but now preserves it verbatim in the audit trail and deletes no
  evidence (calls, attempts, review attempts, policy refreshes).
- **P3-06** - review-history growth was analysed and proven linear/non-nested
  (one summary line per previous round, bounded by `max_reviewer_calls`); prompt
  compaction stays deferred.
- State schema bumped to **4** with public v0.1 state compatibility and a
  `finish_only` recovery path for private `fe4b044` state.

### Added

- Automatic review loop: the engine drives the reviewer itself and feeds
  blocking findings back into the fix prompt. The state machine is unchanged
  and the final gate stays manual - never an automatic `DONE`.
- Execution budget (`budget.max_implementer_calls` 4, `max_reviewer_calls` 4,
  `max_total_provider_calls` 8) checked **before** every external call;
  exceeding a limit BLOCKS the task with code `provider_budget_exhausted` and
  reports used/max for all three limits. The budget is never reset
  automatically.
- Persisted `ProviderCallRecord` for every attempted external invocation
  (kind, phase, success, error type, duration, model, endpoint host - never
  credentials or full URLs) plus `reviews/review-NN-call-MM-meta.json`.
- Reviewer attempt lifecycle (`ReviewAttempt`) with `review-NN-meta.json`:
  status, transport/format attempt counts and external calls consumed.
- Crash-safe in-flight marker (`review_call_in_flight`) persisted before the
  request: a hard kill leaves evidence, and the next `continue` fails closed
  with `interrupted_reviewer_attempt` until a human `unblock --reason ...`.
  A review round that was started but never finalized (crash after the provider
  answered, before the result was persisted) is detected from the persisted
  attempt and fails closed the same way; acknowledging it closes the round as
  `INTERRUPTED` without deleting its call evidence, and the retried round gets
  a unique attempt identity.
- Transport vs format failure separation (`transport_retries` default 0 is
  opt-in; every retry is a counted call) and a `max_response_chars`
  parsing/persistence cap - oversized answers are refused with an explicit
  error, never silently cut or guessed.
- Sanitized HTTP error bodies and model output (same redaction boundary as
  reviewer input) before persistence.
- Finding fingerprints
  (`sha256(severity | normalized title | files | description)`) with per-task
  seen counts, and the opt-in `pipeline.max_same_finding_cycles` stall guard
  (`0` = disabled; fingerprints are recorded either way).
- Task policy snapshot (`tasks/<id>/config.snapshot.yaml`) applied for the
  whole task, `policy_source` visibility, and the audited
  `devrelay unblock --refresh-policy --reason "..."` as the only supported way
  to change a running task's budget/blocking policy.
- `devrelay usage` (read-only provider usage/audit view); `status` now shows
  budget used/max, last review attempt and policy source; `doctor` reports
  reviewer env var **presence** only (`set`/`MISSING`) without sending a
  request, and prints the configured budget.
- State schema version 3 (`provider_calls`, `review_attempts`,
  `finding_seen_counts`, ...) with v0.1 fixture compatibility.

### Changed

- Policy authority over the reviewer: a `PASS` decision that still carries a
  blocking finding does not pass - the configured `blocking_severities` decides.
- The Codex FIX prompt carries structured findings (`- [P2] id=... title=...`
  with `description:` / `files:` / `evidence:` / `recommendation:` lines).
- Manual reviewing is unchanged and still makes zero external calls (a
  `ReviewAttempt` with `external_calls = 0` is recorded for audit).

### Security

- Reviewer credentials stay in environment variables; they never appear in
  `config.yaml`, task state, provider call records, artifacts or logs, and
  `doctor` prints presence rather than values.
- Budget/attempt evidence is append-only: no command resets or forges usage.

### Tests

- 227 tests, fully offline (fake providers, `httpx.MockTransport`, real tiny
  git repositories): 38 v0.2-A tests covering budget pre-flight, exact call
  accounting, format/transport separation, crash recovery, policy authority,
  fingerprints, snapshot/refresh-policy, CLI visibility and a fake-provider
  engine-level end-to-end loop, plus 22 audit-remediation tests covering the
  required crash/identity/policy matrix (persisted-result replay with zero
  calls, single application, immutable evidence, durable ids, policy-refresh
  evidence, retry labelling, fingerprint normalization, read-only legacy
  status/usage, budget regressions), plus 8 baseline-capture tests for the
  ignored-`.devrelay` smoke blocker.

## 0.1.0 - 2026-09-10

First public release: local AI coding orchestration with a task baseline, a
bounded review/fix loop and repository policy guards.

### Added

- Local AI coding orchestration pipeline (PLAN -> IMPLEMENT -> TEST -> REVIEW
  -> FIX loop -> FINAL_GATE -> DONE)
- Persistent task state machine with audited transitions and resume after
  process restart
- Official Codex CLI implementer (prompt streamed on stdin, no OpenAI API key
  required)
- Codex execution path that works with a ChatGPT-subscription-authenticated
  Codex CLI login
- Manual planner workflow (Task Packet `plan show` / `plan import`)
- Manual reviewer workflow (`review export` / `review import`)
- OpenAI-compatible reviewer provider for HTTP review endpoints
- Dirty-workspace task baselines: pre-existing tracked/untracked changes,
  staged and unstaged mixes, deletions, renames and binary files are captured
  without touching the user's real Git index
- Task-relative diffs: reviewers and reports see the baseline -> current
  workspace delta, never HEAD-relative attribution of pre-existing user work
- Durable baseline recovery: byte-faithful `tracked.patch` plus untracked
  blobs, reconstructed and SHA-verified after `git gc` prunes the baseline tree
- Git repository policy guards: HEAD, branch, tag, other local refs and real
  index staging are snapshotted before/after every provider run; violations
  BLOCK the task and are never auto-repaired
- Interrupted provider attempt recovery: persisted attempt lifecycle, post-run
  evidence for exceptions/timeouts/KeyboardInterrupt, fail-closed restart
  requiring explicit human acknowledgement
- Reviewer secret redaction (best-effort pattern based) applied at a single
  boundary shared by the remote and manual reviewer paths
- CLI commands: `init`, `doctor`, `start`, `status`, `plan`, `continue`,
  `diff`, `logs`, `review`, `final`, `unblock`, `version`
- Artifact/evidence generation per task (baseline, implementation reports,
  review requests/results, logs, policy snapshots, final report)
- Release/final gate with a human-readable `final/report.md` answering "why is
  this task considered complete?"

### Security

- No ChatGPT credential scraping, no browser/session automation, no
  undocumented authentication paths
- No OpenAI API key requirement for the Codex CLI execution path
- `shell=False` subprocess execution with argv lists and timeouts
- Git HEAD/branch/ref/index mutation guards with structured violations
- Fail-closed handling of conflicted or otherwise unverifiable Git index state
  (blocked before a provider run can start)
- Best-effort reviewer secret redaction (not a data-loss-prevention system)
- Push prevention remains **provider-limited / best-effort**: the local
  postcondition check cannot mathematically prove that no `git push` happened

### Known limitations

- One active task at a time (no concurrency)
- One implementer: the official Codex CLI
- No MCP server, ChatGPT plugin, web UI or VS Code extension yet
- No mathematical push prevention (see Security)
- Reviewer redaction is pattern-based best effort, not DLP
- Structured Codex event stream (`codex exec --json`) is not parsed yet
- Remaining P3 backlog tracked for a later release:
  - dead HEAD-relative helpers in `GitWorkspace` (unused since task-relative
    deltas landed)
  - `unblock` clears the raw `blocked_reason` field (the audit trail, policy
    snapshots and attempt evidence are retained)
  - files marked `assume-unchanged` / `skip-worktree` do not appear in
    `preexisting_dirty_files` metadata (the task delta itself stays correct)
  - `final/report.md` header line is rendered at the moment of approval
