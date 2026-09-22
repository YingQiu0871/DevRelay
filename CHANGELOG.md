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

**The Mode-A SIC oracle was independently accepted and frozen, and its single authorized
execution produced a candidate result.**  The independent decision *APPROVE V0.3-E SIC MODE-A
PRE-RUN ORACLE* froze `docs/v0.3/V03E_G0_5_PRE_SIC_ORACLE.md` (baseline `e1fb6ac`, blob
`31d7ac50…`), and the separate one-shot external authorization permitted **exactly one** offline
/static semantic attempt.  Executed evidence (`docs/v0.3/V03E_G0_5_PRE_SIC_RESULT.md`, a
**CANDIDATE SIC RESULT** pending independent review): target identity verified (`opencode-ai`
1.18.11, package root unchanged, declared bin `./bin/opencode.exe`, declared-bin SHA-256
`578d7eb3…`); the frozen manifest was re-enumerated and matched **exactly** — 8 files / 6
directories, no missing artifact, no extra artifact inside the package root, no size/hash drift;
all 8 artifacts were classified exactly once (`PACKAGE_METADATA` ×3, `INSTALLER_LOGIC` ×1,
`LICENSE_TEXT` ×1, `OPAQUE_COMPILED_BINARY` ×3, the binaries hashed and identified only — never
executed, never scanned for semantic strings); the deterministic Phase-A extraction enumerated 32
declared `package.json` key paths (22 + 5 + 5) and found **zero** session-anchor key paths, and the
`postinstall.mjs` declaration scan found no explicitly declared schema/type/field-table contract
structure and no session-anchor declaration; complete authoritative coverage therefore held and
the frozen candidate set was **empty (0 candidates)**, so Phase B was not applicable and the frozen
mapping row C yielded the candidate outcome **`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`**.  The
mandatory surface-scoped non-claim is recorded prominently: the result applies only to the exact
successfully inspected installed static package surface and frozen artifacts, does **not**
establish that OpenCode globally has no session-incarnation metadata, does **not** establish that a
live/local API exposes no additional contract surface, does **not** establish P6 and does **not**
enable `adopt_completed_turn`.  Zero-live budget held throughout (0 OpenCode starts, 0 HTTP, 0
`/doc`, 0 `/session`, 0 runtime response reads, 0 provider/model/fake-provider calls, 0 prompt
submissions, 0 session mutations, 0 network, 0 process discovery, 0 port scanning, 0 endpoint
configuration); only local static reads and hashing were performed.  The attempt is consumed (1 of
1), **no rerun is authorized**, no Mode B/C was created or executed, the accepted SIC definition
and the frozen oracle were not modified, and the candidate result must not be treated as
authoritative or as P6 proof.  `G0.5 / P6` remains `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT
FREEZABLE / LOCAL REACHABILITY GAP` with P6 `UNPROVEN / UNSATISFIED`; `G1`/`G2` remain `NOT RUN`;
Case-C and v0.3-E implementation remain **NOT AUTHORIZED**; `adopt_completed_turn` remains
**DISABLED**; 0 runtime/test/config changes occurred.

**The Mode-A SIC result was independently approved and is now the authoritative Mode-A finding.**
The independent result review issued *APPROVE V0.3-E SIC MODE-A RESULT* (**P0 = 0, P1 = 0, P2 = 0**;
classification **VALID SEMANTIC RESULT**), binding the reviewed, immutable result artifact
`docs/v0.3/V03E_G0_5_PRE_SIC_RESULT.md` (blob `ce6c503d3bd62fa09c34d52bbd570e1a98dab403d1164b2e740fe6c476ecadc6`)
to the decision: the **authoritative Mode-A SIC finding is `SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`**,
established by the single authorized offline/static attempt under the accepted/frozen oracle
(`docs/v0.3/V03E_G0_5_PRE_SIC_ORACLE.md`, blob `31d7ac50…`, baseline `e1fb6ac`) — attempt consumed,
no rerun, no Mode B/C and no live activity.  Active status is converged to `SIC MODE-A = EXECUTED
ONCE / DEFINITION ACCEPTED / ORACLE ACCEPTED AND FROZEN / AUTHORITATIVE FINDING =
SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT / ATTEMPT CONSUMED / NO RERUN AUTHORIZED`, and separately
**broader session-incarnation capability = NOT ESTABLISHED BY MODE-A STATIC SURFACE**.  The strict
scope and non-claims are preserved everywhere: the finding applies **only** to the exact
successfully inspected OpenCode 1.18.11 installed static package surface and frozen target/package
artifacts; it does **not** establish that OpenCode globally has no session-incarnation metadata, does
**not** establish that a live/local API exposes no additional contract surface, does **not**
establish P6 (neither `P6 PASS` nor `P6 FAIL`), is **not** `G0.5 PASS` or `G0.5 FAIL`, and does
**not** enable `adopt_completed_turn`.  Stale status wording in `docs/v0.3/V03E_SPEC.md`, `README.md`,
`docs/v0.3/V03_PLAN.md` and `docs/BACKLOG.md` (which still described SIC as `NOT RUN / DEFINITION
CANDIDATE`) was converged in the same round; the accepted SIC definition (`5463ac19…`), the frozen
oracle (`31d7ac50…`), the reviewed result artifact (`ce6c503d…`), the substantive §25.1 block
(`d3244ee0…`) and the G0.4 artifacts were **not** modified.  `G0.5 / P6` remains `NOT RUN /
DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN /
UNSATISFIED` and is **NOT CLOSED**; `G1`/`G2` remain `NOT RUN`; Case-C and v0.3-E implementation
remain **NOT AUTHORIZED**; `adopt_completed_turn` remains **DISABLED**; no Mode B/C oracle was
created and no sequencing decision about them was made; 0 new SIC attempts, 0 new HTTP/`/doc`/
`/session`, 0 OpenCode activity, 0 provider/model/fake-provider calls and 0 network activity
occurred, and 0 runtime/test/config changes were made.

**A Mode-B (live local read-only) SIC pre-run oracle construction round produced no oracle, and
that freezability failure was independently approved.**  The independent review issued *APPROVE
V0.3-E SIC MODE-B ORACLE FREEZABILITY FAILURE* (**P0 = 0, P1 = 0, P2 = 0**) for the scoped
pre-oracle finding **`SIC MODE-B ORACLE NOT FREEZABLE — CONCRETE ENDPOINT NOT ESTABLISHED`**
under **current** accepted configuration/state — an independent review decision, not executor
self-approval, and **not** `MODE-B FAIL`, `SIC FAIL`, `P6 FAIL` or `G0.5 FAIL`.  The accepted
cause is the endpoint-authority path itself: the only supported current runtime endpoint
authority for DevRelay's local OpenCode bridge is `<root>/.devrelay/config.yaml` →
`opencode.base_url`, with the `OpenCodeConfig` empty-string model default as the absent/empty
fallback, and the current value is `base_url: ""` — so no exact scheme, numeric loopback
address, address family, port or base URI is established.  Resolution precision (recorded as
independently reviewed): environment supplies no `opencode.base_url`; the CLI has no endpoint
override; profiles are policy-only and provide no runtime OpenCode wiring; state and task
snapshots are reproducibility/runtime records, not endpoint-resolution authority; no user-level
DevRelay endpoint config participates; OpenCode `provider.*.options.baseURL` values are upstream
model-provider endpoints, not the local OpenCode service endpoint; runtime
logs/database/storage are not accepted endpoint authority; and the documented
`127.0.0.1:4096` value is example text only.  Default/template precision: the packaged
`profiles/default.yaml` contains **no** `opencode` section, the runtime empty fallback derives
from the `OpenCodeConfig` model default, and `WORKSPACE_CONFIG_TEMPLATE` contains `base_url: ""`
as workspace-generation material — the workspace template is **not** the packaged runtime
default.  Current Mode-B status is therefore `SIC MODE-B = NOT RUN / NO ORACLE / ORACLE NOT
FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING
PREREQUISITE BLOCKER`, with **no semantic Mode-B attempt**; the `/doc`-completeness question,
the exact Mode-B request set, live schema parsing, reference traversal, live candidate
extraction and the Mode-B semantic outcome are all **NOT REACHED / UNDECIDED**, and no partial
Mode-B oracle, Mode-B result, Mode C or endpoint-prerequisite artifact exists.  Mode A is
untouched: it stays completed and authoritative with `SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`,
strictly scoped to its exact successfully inspected OpenCode 1.18.11 static package surface.
A future Mode-B design needs a deterministic, precommitted mechanism binding endpoint →
listener → PID → canonical executable → executable hash → process creation identity where
available; the independent review classified the executor's stronger "DevRelay itself must
launch OpenCode" claim as **TOO STRONG / MECHANISM NOT YET DETERMINED**, so a future design may
choose controlled launch **or** another sound deterministic read-only binding mechanism,
subject to later independent review — **no choice was made in this round**.  The next dependency
was recorded at that point only as **MODE-B ENDPOINT / TARGET-BINDING PREREQUISITE = NOT YET
DEFINED / NOT AUTHORIZED** (its future definition had to settle endpoint-selection ownership,
authoritative endpoint source, numeric loopback address, address family, deterministic port
policy, pre-existing-vs-explicitly-launched target policy, deterministic target-binding mechanism
and the no-endpoint-shopping rule; none of that was designed in that round — a **definition
candidate** for the prerequisite was subsequently created in the next round, recorded below).
Hygiene record (independent
finding, **P3 only**): the prior construction report's "NO FILES MODIFIED" wording was
overbroad, because a round record was appended to the git-ignored/untracked `PROJECT_MEMORY.md`;
that file is outside tracked repository content, is ignored/untracked, does not participate in
DevRelay runtime/config, altered no endpoint/config/oracle evidence, and left the tracked
worktree clean — the precise wording going forward is "**no tracked repository/config/oracle/
source/test/document artifact modified**", and `PROJECT_MEMORY.md` was **not** edited to address
the wording issue.  `G0.5 / P6` remains `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE /
LOCAL REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED` and **NOT CLOSED**; `G1`/`G2` remain
`NOT RUN`; Case-C and v0.3-E implementation remain **NOT AUTHORIZED**; `adopt_completed_turn`
remains **DISABLED**; no endpoint was established, no port was selected, `opencode.base_url` and
`.devrelay` configuration were **not** modified, no listener was created, no port was scanned
and no listener was probed; 0 new SIC semantic attempts, 0 Mode-B executions,
0 HTTP/`/doc`/`/session`, 0 OpenCode starts/restarts, 0 endpoint selection, 0
provider/model/fake-provider calls, 0 external network, 0 G0.5 and 0 G1/G2 activity occurred,
and 0 runtime/test/dependency/version/config changes were made.

**A definition candidate now exists for the Mode-B endpoint / target-binding prerequisite (ETB).**
`docs/v0.3/V03E_G0_5_PRE_MODE_B_ENDPOINT_BINDING.md` defines the narrow **pre-oracle**
prerequisite that must be satisfied before a Mode-B (live local read-only) SIC oracle can be
constructed, with status **`ETB = DEFINITION CANDIDATE / NOT ACCEPTED / NOT EXECUTED / NOT
AUTHORIZED`**.  It establishes **no endpoint**, authorizes **no configuration change** and
authorizes **no OpenCode launch**.  ETB sits **outside P1–P9** as a pre-oracle prerequisite only:
it proves nothing — not P6, not G0.5, not SIC semantics, not session incarnation, not turn or
message provenance, not pending-handle semantics — and success enables exactly one thing, the
resumption of Mode-B SIC oracle **construction** (never Mode-B execution, G0.5, Case-C
implementation or adoption).  It freezes the endpoint authority as exactly
`<root>/.devrelay/config.yaml` → `opencode.base_url` (current value still `""`), with environment,
profile, CLI, state-snapshot, log, database, port/listener/process scan, provider upstream
`baseURL`, documentation example, implicit `localhost` and implicit default port all **forbidden**
as endpoint authority; endpoint-selection ownership is **external / owner-authorized** and the
executor must not invent the tuple (`127.0.0.1:4096` is **not** automatically selected); the
required form is `http` + a numeric loopback address + an **explicit** address family + an
**explicit** integer port (no actual value selected in this round).  The deterministic port policy
is frozen as a requirement with two admissible classes — **A: owner-supplied fixed port**
(available today) and **B: an independently accepted deterministic allocation policy** (admissible
only once such a policy exists and is accepted; not invented here) — while trying `4096` then
another port, first-free-port, range scanning, random ports, OS-assigned ephemeral ports without a
precommitted durable freeze, failure-driven choice and port retries are **forbidden**; an
unbindable precommitted port ends the attempt.  Exactly **two mutually exclusive modes** are
allowed — **MODE L (controlled launch)** and **MODE P (pre-existing target)** — with **no
selection made in this round**, a mandatory mode precommit **before any operational action**, **no
`L → P` / `P → L` fallback**, no mode shopping, and a mode change requiring new external
authorization.  **MODE L** requires the frozen 1.18.11 identity, the accepted executable hash, an
already externally authorized address/port, launch arguments that explicitly bind that exact
address/port, a PID obtained from the launch act itself, no scanning to choose the target, and
attempt termination on bind failure — but its **launch capability is UNESTABLISHED**: accepted
evidence records only a dedicated loopback `opencode serve` (v0.3-A artifacts) and freezes no
flags, so **Mode L is conditional on a later separately reviewed launch-capability determination**
and no CLI flags are guessed.  **MODE P** requires the endpoint tuple to be already explicit in the
authoritative configuration and permits only **endpoint-scoped owner verification** (endpoint
**discovery** is forbidden); a read-only OS mechanism is admissible only if it queries only the
already-frozen exact endpoint and deterministically returns its owning PID, with ambiguity failing
closed — and **no concrete primitive is asserted as authoritative**, that remaining a future
ETB-oracle requirement.  The definition freezes the target-binding chain (endpoint tuple → exact
listener → unique owning PID → canonical executable path → executable SHA-256 → exact OpenCode
version → process creation identity where available, no single element sufficient), the
pre/post-request continuity requirements (ETB itself performs **no** Mode-B HTTP), the
process-creation-identity property (PID alone never proves continuity; unavailability must be
classified explicitly as fail-closed rather than silently dropped), the version binding to
OpenCode 1.18.11 / `578d7eb3…`, the configuration boundary (setting `base_url` only after the
tuple is externally authorized and the mode precommitted — and configuration **never** equals
binding), the no-endpoint-shopping prohibitions, the fail-closed conditions (**never** to be
reinterpreted as SIC results), `ETB SATISFIED` (an unambiguous evidence package; **not** SIC/P6/G0.5
PASS) and `ETB UNSATISFIED` (a prerequisite/control result only: Mode-B oracle construction stays
blocked; it does **not** mean SIC, P6 or G0.5 failed), the status model, and the frozen sequencing
(**definition accepted → separate ETB oracle design → separate authorization → execution →
independent result review → only if ETB SATISFIED may Mode-B SIC oracle construction resume**; no
direct jump to Mode-B execution).  The definition aligns with the accepted G0.4 oracle's existing
endpoint-scoped binding definition (§8.1–§8.8) and reuses its semantics, while recording explicitly
that that prior art was **never executed** (G0.4 Case A `TARGET_IDENTITY_UNRESOLVED`, no configured
endpoint, 0 HTTP), so it is a reviewed definition rather than validated capability evidence; three
platform facts are carried forward as future requirements (exact launch syntax/address-port binding
capability; the concrete endpoint→PID primitive and its semantics; availability and semantics of
process creation identity) and none is invented.  Mode A remains completed and authoritative
(`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`, strictly scoped to its frozen static surface); Mode-B
status is unchanged (`NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT
ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`) and the Mode-B SIC
oracle remains **not freezable**; `G0.5 / P6` remains `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT
FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED` and **NOT CLOSED**;
`G1`/`G2` remain `NOT RUN`; Case-C and v0.3-E implementation remain **NOT AUTHORIZED**;
`adopt_completed_turn` remains **DISABLED**; ETB is **not** accepted and **not** executed, and no
operational authorization exists.  This round established no endpoint, selected no port or
address, changed no configuration (`.devrelay/config.yaml` untouched, `opencode.base_url` still
`""`), started no OpenCode, created no listener, performed no port/listener/process scan, issued
**0** HTTP, touched neither `/doc` nor `/session`, created no ETB execution oracle and no Mode-B
oracle, executed no SIC attempt, ran no G0.5/G1/G2, and made 0 runtime/test/dependency/version
changes.

**The ETB definition candidate was independently approved, so the Mode-B endpoint / target-binding
prerequisite is now an accepted prerequisite (this supersedes the candidate status recorded in the
preceding entry).**  The independent definition review issued *APPROVE V0.3-E MODE-B ETB
PREREQUISITE DEFINITION* (**P0 = 0, P1 = 0, P2 = 0**; three non-blocking P3s), binding the
immutable definition artifact `docs/v0.3/V03E_G0_5_PRE_MODE_B_ENDPOINT_BINDING.md` (blob
`99cc6dcee4ab1a3f0589c3e7d11308d089601ba07d16cc2d37a9fc32c777b3a0`, commit `f3f625f`) to that
decision — an independent review decision, not executor self-approval.  The authoritative ETB
status is therefore **`ETB = DEFINITION ACCEPTED / NOT EXECUTED`**, recorded separately from
**`ETB EXECUTION / ORACLE = NOT YET DEFINED / NOT AUTHORIZED`**; the two are deliberately **not**
merged into a new semantic outcome, and no `ETB SATISFIED`, `ETB UNSATISFIED` or `ETB EXECUTED`
result exists or is claimed.  The accepted definition remains a **pre-oracle prerequisite outside
P1–P9**: it proves none of P6, G0.5, SIC semantics, session incarnation, turn provenance, message
provenance or pending-handle semantics, and definition acceptance authorizes **nothing
operational**.  The accepted endpoint-authority model is unchanged — the future authoritative
endpoint source is exactly `<root>/.devrelay/config.yaml` → `opencode.base_url`, with no
alternative authority, and the current value is still `base_url: ""` — so **no endpoint is
established**, and definition acceptance must not be confused with endpoint establishment.
Endpoint selection remains **EXTERNAL / OWNER-AUTHORIZED** (or derived under a separately
independently accepted deterministic allocation policy); no address, address family, port or base
URI has been selected and `127.0.0.1:4096` remains example text only; the accepted port-policy
classes remain **A (owner-supplied fixed port)** and **B (independently accepted deterministic
allocation policy)**, and class B currently has **no concrete accepted policy** (none invented).
The accepted mode model defines exactly **two mutually exclusive** future modes — **MODE L
(controlled launch)** and **MODE P (pre-existing target)** — with **no mode selected**, no
third/hybrid mode, no `L → P` / `P → L` fallback, and definition acceptance authorizing **neither**
mode operationally.  The **Mode-L gap** is recorded as **UNESTABLISHED** (exact OpenCode server
command, exact address-binding flag semantics, exact port-binding flag semantics — no flag is
inferred or invented), so Mode L remains conditional and cannot be operationally precommitted
until separately established.  The **Mode-P gap** is recorded as **UNESTABLISHED** (the
endpoint-scoped owner-verification mechanism), with the accepted semantic boundary unchanged:
endpoint **discovery is FORBIDDEN**, while endpoint-scoped verification against an already-frozen
endpoint is **POTENTIALLY ADMISSIBLE** only if a future reviewed ETB oracle freezes a
deterministic concrete mechanism — and **no Windows command/API has been accepted**.  The accepted
target-binding chain is unchanged (authoritative endpoint tuple → exact listener → unique owning
PID → canonical executable path → executable SHA-256 → exact OpenCode version → process creation
identity where available), with **no single element proving binding**, `base_url` alone
insufficient and listener existence alone insufficient; the accepted process-instance rule is also
unchanged — PID alone is insufficient, a platform-supported process-instance discriminator
protecting against PID reuse is required, inability to obtain the required process-instance
evidence on the currently accepted Windows proof environment **fails closed**, and the concrete
primitive/semantics remain unresolved for the ETB execution oracle.  Definition semantics are
recorded **without being executed**: a future ETB execution under a separately frozen execution
oracle may yield `ETB SATISFIED` — which will mean only that the endpoint/target-binding
prerequisite is established sufficiently for Mode-B SIC oracle construction to resume, **not**
`SIC PASS`, `P6 PASS` or `G0.5 PASS` — or `ETB UNSATISFIED`, which means only that Mode-B SIC
oracle construction **remains blocked**.  The accepted unresolved-fact register is carried
forward as future ETB-oracle work with **nothing marked resolved**: **U1** exact OpenCode launch
syntax / explicit bind capability; **U2** exact Windows frozen-endpoint → owning-PID verification
primitive and semantics; **U3** process-instance/creation-identity primitive and semantics; **U4**
concrete deterministic port allocation policy if class B is used; **U5** actual ETB mode
selection — the independent review determined that **none** of U1–U5 blocks definition
acceptance.  Review P3s are recorded accurately as **non-blocking**: **P3-1** the construction
instruction "No amend" was violated by amending a seconds-old, unreviewed, unpushed intermediate
local commit — classified as a **bounded process-hygiene deviation only** (no
accepted/reviewed/shared history rewritten; final ancestry deterministic), explicitly **not
normalized**, with future rounds required to honor **NO AMEND**; **P3-2** the ETB definition
freezes the future endpoint form as HTTP-only, narrower than config validation's http/https
acceptance, with an explicit future review escape clause — **not** broadened now; **P3-3** Mode-P
endpoint-scoped verification still leaves bounded mechanism discretion, which a future ETB oracle
must concretely precommit — **not** solved now.  The accepted sequencing is unchanged and no stage
may be skipped: ETB definition **ACCEPTED** → next, separately, ETB execution/oracle design →
independent oracle review → separate execution authorization → ETB execution → independent ETB
result review → **only if ETB SATISFIED** may Mode-B SIC oracle construction resume.  The accepted
definition artifact is **immutable** and was **not** modified: its own at-construction header may
remain `DEFINITION CANDIDATE / NOT ACCEPTED`, because acceptance is represented through the
independent approval record and the active authoritative status surfaces, following the existing
immutable-artifact + approval-record pattern.  Mode-B status is unchanged — `SIC MODE-B = NOT RUN /
NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION /
TARGET-BINDING PREREQUISITE BLOCKER` — and Mode-B oracle construction has **not** resumed,
precisely because ETB has **not** been executed and is **not** SATISFIED.  Mode A remains
completed and authoritative (`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`, strictly scoped to its
accepted frozen static surface); `G0.5 / P6` remains `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT
FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED` and **NOT CLOSED**;
`G1`/`G2` remain `NOT RUN`; Case-C and v0.3-E implementation remain **NOT AUTHORIZED**;
`adopt_completed_turn` remains **DISABLED**.  This bookkeeping round established no endpoint,
selected no endpoint or port, changed no configuration (`.devrelay/config.yaml` untouched,
`opencode.base_url` still `""`), started no OpenCode, created no listener, designed no ETB
execution oracle, executed no ETB, created no Mode-B oracle, issued **0** HTTP, touched neither
`/doc` nor `/session`, executed no SIC attempt, ran no G0.5/G1/G2, and made 0
runtime/test/dependency/version changes.

**A capability-resolution candidate for the ETB design-support questions U1 / U2 / U3 was produced
(design support only).**  `docs/v0.3/V03E_G0_5_PRE_ETB_CAPABILITY_RESOLUTION.md` records a bounded,
read-only resolution attempt for the three platform facts carried by the accepted ETB definition —
**U1** exact OpenCode launch syntax / explicit bind capability, **U2** exact Windows
frozen-endpoint → owning-PID verification primitive and semantics, and **U3** process-instance /
creation-identity primitive and semantics — under a **closed probe set** of exactly eleven
authorized probes (the exact target executable's `--help` and `serve --help`, plus `Get-Command` /
`Get-Help` / `Get-CimClass` metadata for `Get-NetTCPConnection`, `Get-CimInstance`, `Get-Process`
and `Get-FileHash`), with no addition, substitution or variant after observing output.  It is
**design support for a future ETB execution oracle** — **not** an ETB execution oracle, **not** ETB
execution, **not** a proof-ladder gate — and it establishes no endpoint, selects no mode and
authorizes nothing.  Results: **U1 = `U1_NOT_ESTABLISHED`** (facts A–D established from the exact
1.18.11 binary's own help — the `opencode serve` subcommand "starts a headless opencode server", and
explicit `--hostname <string>` "hostname to listen on" / `--port <number>` "port to listen on"
options with defaults `"127.0.0.1"` and `0` — while fact E, exact-bind/implicit-substitution and
bind-failure semantics, and fact F, deterministic launcher-visible process identity, are
`SEMANTICS_UNPROVEN`, so Mode-L launch/bind semantics cannot yet be frozen without invention);
**U2 = `U2_NOT_ESTABLISHED`** (the `Get-NetTCPConnection` interface shape is documented —
`-LocalAddress` position 0/alias `IPAddress`, `-LocalPort <uint16[]>`, `-State` admitting the
documented value `Listen`, `-OwningProcess` as an input parameter, output type
`MSFT_NetTCPConnection` — but the captured help is explicitly **partial** because the module's help
files are not installed, so exact-match filtering semantics, result-set semantics and an owning-PID
output property are not documented: `SEMANTICS_UNPROVEN` for the three filter facts and
`EVIDENCE_INSUFFICIENT` for owning-PID output exposure); **U3 = `U3_NOT_ESTABLISHED`** (a PID-scoped
process query is **ESTABLISHED** — `Get-Process -Id <int[]>` alias `PID` is a documented parameter
set — and SHA-256 exact-path hashing is **ESTABLISHED** from `Get-FileHash`'s documented
`-Path`/`-LiteralPath` plus the algorithm enum containing `SHA256`, but executable-path exposure,
canonical-path semantics and the process-instance/PID-reuse discriminator are all
`EVIDENCE_INSUFFICIENT` because no property enumeration or property semantics were captured and the
authorized `Get-CimClass` rendering truncated the `Win32_Process` property list, the gap being
recorded rather than worked around).  Consequences: **`MODE_L_MECHANISM_NOT_YET_FREEZABLE`** and
**`MODE_P_MECHANISM_NOT_YET_FREEZABLE`** (neither is a mode selection), while **U4** and **U5**
remain **UNRESOLVED BY DESIGN / OWNER-ORACLE DECISION REMAINS**.  These are **evidence-surface
limitations, not platform-absence findings** and **not** ETB outcomes: no `ETB PASS`/`ETB FAIL`/
`ETB SATISFIED`/`ETB UNSATISFIED`/SIC/P6 result is created.  Recorded side effect: invoking the
exact target binary for the two help probes appended **+246 bytes** to
`C:\Users\1\.local\share\opencode\log\opencode.log` (15 650 374 → 15 650 620 bytes) inside the probe
window, with the caveat that the OpenCode state directory is shared with the user's own active
OpenCode usage so the growth is consistent with, but not exclusively attributable to, this round;
the log contents were not read.  No other side effect occurred: `.devrelay` untouched
(`opencode.base_url` still `""`), no repository runtime/test/config modification, no OpenCode server
started, no listener created, no port scan or listener/process enumeration, **0** HTTP, neither
`/doc` nor `/session` touched, no provider/model call and no external network access.  The current
authoritative ETB status is **unchanged** by this design-support round — `ETB = DEFINITION ACCEPTED
/ NOT EXECUTED` and `ETB EXECUTION / ORACLE = NOT YET DEFINED / NOT AUTHORIZED` — and Mode-B oracle
construction has still **not** resumed.

**The ETB U1/U2/U3 capability-resolution candidate was independently approved, so its findings are
now authoritative design-support status (this supersedes the candidate status recorded in the
preceding entry).**  The independent review issued *APPROVE V0.3-E ETB U1/U2/U3 CAPABILITY
RESOLUTION* (**P0 = 0, P1 = 0, P2 = 0**; four non-blocking P3s), binding the immutable capability
artifact `docs/v0.3/V03E_G0_5_PRE_ETB_CAPABILITY_RESOLUTION.md` (blob
`59e8ef575fa3ab854f65fee5e25621c51f74c8b76615d7d4d9fb1e071b4049ac`, commit `3151f87`) to that
decision — an independent review decision, not executor self-approval.  The authoritative capability
findings are **`U1 = U1_NOT_ESTABLISHED`**, **`U2 = U2_NOT_ESTABLISHED`**, **`U3 =
U3_NOT_ESTABLISHED`**, **`MODE L = MODE_L_MECHANISM_NOT_YET_FREEZABLE`** and **`MODE P =
MODE_P_MECHANISM_NOT_YET_FREEZABLE`**, with **`U4 = UNRESOLVED BY DESIGN / OWNER-ORACLE DECISION
REMAINS`** and **`U5 = UNRESOLVED BY DESIGN / OWNER-ORACLE DECISION REMAINS`**.  These are
**capability / design-support findings only**: they are **evidence-surface limitations, not
platform-absence findings**, and they are **not** `ETB UNSATISFIED`, `ETB FAIL`, `SIC FAIL`,
`P6 FAIL` or `G0.5 FAIL`.  Accepted U1 detail: A (serve subcommand exists), B (exact command form),
C (explicit hostname/address option) and D (explicit port option) are `ESTABLISHED`, while E
(exact-bind / bind-failure / no-substitution semantics) and F (deterministic launcher-visible
process identity) are `SEMANTICS_UNPROVEN` — therefore `U1_NOT_ESTABLISHED`; this does **not** mean
Mode L is impossible and does **not** mean OpenCode cannot bind an exact endpoint, only that the
required semantics remain unestablished.  Accepted U2 detail: the `Get-NetTCPConnection` local help
is **PARTIAL**; exact-local-address filter semantics, exact-local-port filter semantics,
listener-state restriction semantics and multiple-result detectability are `SEMANTICS_UNPROVEN`, and
owning-PID **output** exposure is `EVIDENCE_INSUFFICIENT` — therefore `U2_NOT_ESTABLISHED`, with the
distinction preserved that the existence of `-OwningProcess` as an **input** filter does **not**
establish an owning-PID **output** property, and no `MSFT_NetTCPConnection` property is inferred from
general knowledge.  Accepted U3 detail: PID-scoped query and SHA-256 exact-path hashing are
`ESTABLISHED`, while executable-path exposure, canonical-path semantics and the process-instance
discriminator are `EVIDENCE_INSUFFICIENT` — therefore `U3_NOT_ESTABLISHED`, with no invented
`ExecutablePath`, canonicalization or `CreationDate`/`StartTime` semantics.  Reviewed
next-information ordering (recorded as **current design-support status, not authorization**):
**FIRST** — U2: authoritative parameter semantics for `-LocalAddress`, `-LocalPort` and `-State`,
plus authoritative `MSFT_NetTCPConnection` output-property semantics, especially an owning-PID
output property; **SECOND** — U3: a documented executable-path property with path-comparison /
canonicalization semantics, plus a documented process-instance / creation-identity property whose
semantics are strong enough to discriminate PID reuse; **THIRD** — U1: exact-bind, bind-failure and
no-substitution semantics for `--hostname`/`--port` (including the meaning of `--port 0`), plus a
deterministic launcher-visible process-identity mechanism.  **The repository does not yet contain
enough information to construct a sound final ETB execution oracle; additional bounded capability
evidence is required first** — and no follow-up capability round is designed or authorized here.
Review P3s are recorded accurately as **non-blocking standing observations, none presented as
resolved**: **P3-1** the intended PowerShell execution helper failed (`node.exe ENOENT`) and the same
frozen W1–W9 commands were executed through `powershell.exe -NoProfile -NonInteractive` — a
non-material process/harness deviation; **P3-2** the OpenCode help invocations produced the disclosed
**+246-byte** growth in `C:\Users\1\.local\share\opencode\log\opencode.log` during the probe window —
a non-blocking local metadata/hygiene side effect on which no semantic evidence depended; **P3-3**
the "no untracked leftovers" wording was technically overbroad because the ignored/untracked
`PROJECT_MEMORY.md` exists — no runtime/config/evidence impact; **P3-4** previously carried project
P3s were not re-promoted.  Raw-capture treatment: the review independently corroborated the raw
captures under `C:\Users\1\AppData\Local\Temp\etb-cap.PC89OZ` during review, but that **ephemeral
path is not an authoritative long-term repository source**; the accepted repository artifact carries
the durable summarized evidence and hash record, and future evidence rounds should preserve required
raw/surrogate evidence in a **durable tracked form** when authorized — user logs and private data
must never be copied into the repository.  ETB status is unchanged by this acceptance: `ETB =
DEFINITION ACCEPTED / NOT EXECUTED` and `ETB EXECUTION / ORACLE = NOT YET DEFINED / NOT AUTHORIZED`;
capability-finding acceptance creates **no** ETB execution oracle, **no** ETB execution
authorization, **no** `ETB SATISFIED` and **no** `ETB UNSATISFIED`.  Endpoint and mode state is
unchanged: `opencode.base_url` is still `""`, no endpoint is established, no address, address
family, port or base URI is selected, no port policy is instantiated, and neither Mode L nor Mode P
is selected.  Mode A remains completed and authoritative (`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`,
strictly scoped to the accepted static surface); Mode-B status is unchanged (`NOT RUN / NO ORACLE /
ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING
PREREQUISITE BLOCKER`) and Mode-B oracle construction has **not** resumed; `G0.5 / P6` remains
`NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN /
UNSATISFIED` and **NOT CLOSED**; `G1`/`G2` remain `NOT RUN`; Case-C and v0.3-E implementation remain
**NOT AUTHORIZED**; `adopt_completed_turn` remains **DISABLED**.  This bookkeeping round ran no
capability probe, no web lookup, no PowerShell help install and no OpenCode help invocation;
established no endpoint; selected no endpoint, port, address family or mode; changed no
configuration; started no OpenCode server; created no listener; performed no process/listener/port
query; did no ETB oracle work and no ETB execution; issued **0** HTTP; touched neither `/doc` nor
`/session`; executed no SIC attempt; ran no G0.5/G1/G2; and made 0 runtime/test/dependency/version
changes.

**A round-2 candidate capability finding resolved the ETB U2 and U3 semantic gaps (design support
only; not accepted).**  `docs/v0.3/V03E_G0_5_PRE_ETB_U2_U3_AUTHORITY_RESOLUTION.md` records a bounded
resolution of **U2** (frozen-endpoint → unique owning PID) and **U3** (known PID → executable
identity + process-instance identity + canonical executable path) using a **closed authoritative
source set** — exactly **nine** approved Microsoft Learn pages (D1–D9, all HTTP 200, bodies hashed,
no page body committed, no search-engine result or third-party source used as evidence) — plus
exactly **four** local metadata/schema probes (S1–S4) that retrieved **no** instance and performed
**no** live TCP, listener, port or process query.  Durable evidence is tracked under
`docs/v0.3/evidence/etb-u2-u3-authoritative-semantics/` (14 evidence files + `MANIFEST.sha256`, all
hashes verified).  Candidate results: **`U2 = U2_ESTABLISHED`** — the exact-local-address and
exact-local-port filter semantics are documented (both `Supports wildcards: False`), `-State`
restricts to the states specified with `Listen` among the accepted values (and `State` is a read-only
property whose `Listen` value means waiting for a connection request), the installed command metadata
binds `OutputType` to `…CimInstance#ROOT/StandardCimv2/MSFT_NetTCPConnection` (corroborated by the
class documentation's `Root\StandardCimv2` namespace and by local class metadata), `OwningProcess` is
documented as a **read-only** uint32 property holding "the PID of the owning process of the TCP
connection" (kept distinct from the `-OwningProcess` **input** filter), and `@(...)`+`.Count`
deterministically distinguishes 0/1/N results — so the endpoint-scoped verification
`-LocalAddress <frozen> -LocalPort <frozen> -State Listen` with `@(...).Count == 1` and a read of
`OwningProcess` is freezable, with wildcard-bound or multi-match cases failing closed; and
**`U3 = U3_ESTABLISHED`** — the WQL/CQL `-Filter` contract plus the documented `=` **Equal** operator
(with `LIKE` as the separate wildcard form) establish the exact PID-scoped predicate,
`ProcessId`/`ExecutablePath`/`CreationDate` are all present locally as read-only properties,
`ExecutablePath` is documented as "Path to the executable file of the process", `CreationDate` is
documented (qualifier `Fixed`) as "Date the process begins executing" so a reused PID necessarily
belongs to a newly started instance with a different creation date, and the canonical/final-path
capability is established by `GetFinalPathNameByHandleW` (`FILE_NAME_NORMALIZED` = "Return the
normalized drive name", "A final path is the path that is returned when a path is fully resolved")
with a read-only `GENERIC_READ` + `OPEN_EXISTING` handle (no creation, no truncation) invoked through
`Add-Type` P/Invoke (present locally), SHA-256 hashing being already accepted.  Consequently the
candidate **`MODE P = MODE_P_MECHANISM_FREEZABLE`** — mechanism semantics are now sufficient for later
ETB oracle design — while **U1 = `U1_NOT_ESTABLISHED`** and **MODE L =
`MODE_L_MECHANISM_NOT_YET_FREEZABLE`** are **unchanged** (no OpenCode probe, no server launch, no
contradicting evidence), and **U4/U5 remain `UNRESOLVED BY DESIGN / OWNER-ORACLE DECISION REMAINS`**
(Mode-P mechanism freezability is **not** mode selection).  Recorded fail-closed caveats (design
requirements, not gaps): the `SeDebugPrivilege` qualifier on `ExecutablePath`; `ERROR_ACCESS_DENIED`
on component-access failure under normalized resolution; the `\\?\` DOS-prefix form requiring the
**identical** canonicalization on both sides; and `ExecutablePath` never being treated as canonical
without that route.  No endpoint was established, no port or address selected, no mode selected, no
configuration changed (`opencode.base_url` still `""`), no OpenCode started, no listener created, no
HTTP issued, no `/doc` or `/session` access, no provider/model call, and no ETB execution, ETB oracle
or Mode-B oracle work occurred; this round is a **candidate only until independent review**, and the
current authoritative state remains `ETB = DEFINITION ACCEPTED / NOT EXECUTED` with `ETB EXECUTION /
ORACLE = NOT YET DEFINED / NOT AUTHORIZED`.

**The round-2 ETB U2/U3 authoritative-semantics candidate was independently approved, so its results
are now authoritative capability status (this supersedes the U2/U3 and Mode-P results recorded in the
preceding capability entries).**  The independent review issued *APPROVE V0.3-E ETB U2/U3
AUTHORITATIVE SEMANTICS ROUND-2* (**P0 = 0, P1 = 0, P2 = 0**; five non-blocking P3s), binding the
immutable Round-2 artifact `docs/v0.3/V03E_G0_5_PRE_ETB_U2_U3_AUTHORITY_RESOLUTION.md` (blob
`49b22a88a593ce9ce59e7da6ae5221d8300d4963cca5b9fdc2dc8c2b47a91453`, commit `dcf899d`) together with
its tracked evidence manifest `docs/v0.3/evidence/etb-u2-u3-authoritative-semantics/MANIFEST.sha256`
(blob `579e21e6596e552a1ee453a0a3c08489f4911ff51a1f922dae5bfa71c770a15a`; 14 evidence files,
manifest re-verified **14 OK / 0 mismatch** against the committed blobs) to that decision — an
independent review decision, not executor self-approval.  The authoritative capability state is
therefore **`U1 = U1_NOT_ESTABLISHED`** (unchanged), **`U2 = U2_ESTABLISHED`**, **`U3 =
U3_ESTABLISHED`**, **`MODE L = MODE_L_MECHANISM_NOT_YET_FREEZABLE`** (unchanged) and **`MODE P =
MODE_P_MECHANISM_FREEZABLE`**, with **`U4 = UNRESOLVED BY DESIGN / OWNER-ORACLE DECISION REMAINS`**
and **`U5 = UNRESOLVED BY DESIGN / OWNER-ORACLE DECISION REMAINS`**; this supersedes the previous
capability state **only** for U2/U3 and the Mode-P mechanism-freezability consequence, and U1/Mode-L
are **not** changed (Mode L is not claimed impossible).  Accepted U2 detail: exact `LocalAddress`
filtering, exact `LocalPort` filtering, `State`/`Listen` filtering, installed output-class binding to
`ROOT/StandardCimv2/MSFT_NetTCPConnection`, `OwningProcess` **output-property** semantics, and 0/1/N
cardinality normalization with the `Count == 1` uniqueness rule are all ESTABLISHED — with the
mechanism boundary preserved: the future query is **endpoint-scoped verification against one
already-frozen exact endpoint**, **not endpoint discovery**.  Accepted U3 detail: the PID-scoped
`Win32_Process` equality filter, the local `ProcessId` property, the local `ExecutablePath` property,
`ExecutablePath`'s documented meaning, the local `CreationDate` property, `CreationDate`'s
process-start semantics, the process-instance-discriminator use at the accepted ETB capability level,
the `GetFinalPathNameByHandleW` final-path capability, the `CreateFileW` existing-file handle
capability, the `Add-Type`/P-Invoke local invocation route and SHA-256 exact-path hashing are all
ESTABLISHED.  Accepted canonicalization chain (freezable semantics; **no implementation code
written** and the exact implementation rules **not** claimed frozen): raw `Win32_Process.ExecutablePath`
→ `CreateFileW` on the existing executable under a future fail-closed deterministic share/access rule
→ `GetFinalPathNameByHandleW` with `FILE_NAME_NORMALIZED` + `VOLUME_NAME_DOS` → the identical
final-path procedure applied to the accepted target executable → deterministic comparison → SHA-256
verification.  Mode-P consequence: `MODE_P_MECHANISM_FREEZABLE` holds because `U2_ESTABLISHED` **and**
`U3_ESTABLISHED` with no contradiction to the accepted ETB definition — and
**`MODE_P_MECHANISM_FREEZABLE` is NOT Mode-P selection**; it establishes no endpoint, port, address
family or base URI, no ETB oracle, no ETB execution authorization and no `ETB SATISFIED`.  Review P3s
are recorded accurately as **non-blocking standing observations, none presented as resolved or
blocking**: **P3-1** D1 was delivered in the `windowsserver2025-ps` view after the requested
PowerShell-5.1 fallback and was locally bound through S1/S2 — classified non-material; **P3-2**
`CreateFileW` `dwShareMode` is not yet precommitted — a deterministic future-oracle implementation
rule, not a capability semantic gap; **P3-3** `CreationDate` carries a residual precision/collision
caveat — no mathematical global uniqueness is claimed, and the future ETB oracle must explicitly
record the residual and use exact pre/post equality with fail-closed treatment of any mismatch or
ambiguity; **P3-4** the evidence `.txt`/`.json`/`.sha256` paths may materialize CRLF on a future
checkout — committed Git blobs are authoritative and manifest verification must be against committed
blobs; **P3-5** web search, where used, only located already-precommitted URLs and supplied no
semantic evidence; the standing `PROJECT_MEMORY` wording P3 is preserved.  Still **NOT FROZEN**
(future ETB execution-oracle design items; they do **not** invalidate U2/U3 capability establishment):
the exact canonicalization comparison rule, `\\?\` prefix handling, case normalization/comparison,
slash normalization, drive-letter normalization, `CreateFileW` `dwShareMode`,
`SeDebugPrivilege`/access-denied fail-closed behaviour, the pre/post target snapshot exact field set,
the pre/post equality/comparison rule, and the exact `Count == 1` expression and failure handling.
The narrow next stage is recorded as **OWNER / ORACLE-PARAMETER DECISION = NOT YET EXECUTED** (purpose:
U5 mode selection and, **only if Mode P is selected**, U4 endpoint parameter selection); recording it
does **not** authorize it, and no such decision was made in this round.  Preserved unchanged: `ETB =
DEFINITION ACCEPTED / NOT EXECUTED`; `ETB EXECUTION / ORACLE = NOT YET DEFINED / NOT AUTHORIZED` (the
ETB oracle does not yet exist and ETB execution is not authorized even though Mode-P mechanism
semantics are now freezable); `opencode.base_url` is still `""` with no endpoint established, no
address, address family, port or base URI selected and no configuration change; Mode A remains
completed and authoritative (`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`, strictly scoped to its accepted
static surface); Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT
ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER` with oracle construction
**not** resumed; `G0.5 / P6` remains `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL
REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED` and **NOT CLOSED**; `G1`/`G2` remain `NOT RUN`;
Case-C and v0.3-E implementation remain **NOT AUTHORIZED**; `adopt_completed_turn` remains
**DISABLED**.  This bookkeeping round performed **0** web retrievals, **0** schema probes, **0** live
TCP queries, **0** live process queries, **0** port/listener/process enumeration, **0** endpoint
establishments or selections, **0** port selections, **0** mode selections, **0** configuration
changes, **0** OpenCode starts, **0** listener work, **0** ETB oracle design, **0** ETB executions,
**0** OpenCode HTTP, **0** `/doc`, **0** `/session`, **0** SIC attempts, **0** Mode-B oracle work,
**0** provider/model calls, **0** network, **0** G0.5 and **0** G1/G2 activity, and **0**
runtime/test/dependency/version changes.  The accepted Round-2 artifact and every file under its
evidence directory were **not** modified (artifact blob `49b22a88…`, manifest blob `579e21e6…`,
manifest re-verified 14 OK / 0 mismatch); the artifact retains its `ROUND-2 CANDIDATE FINDING / NOT
ACCEPTED` header because acceptance is carried by the independent review record and the active
authoritative status surfaces.

**The human owner has explicitly decided the ETB mode and endpoint parameters; a candidate repository
record of that decision now exists (not yet independently accepted).**
`docs/v0.3/V03E_G0_5_PRE_ETB_OWNER_ORACLE_PARAMETERS.md` records the owner's decision as **frozen
external input** for a future ETB execution-oracle design: **U5 = MODE P — PRE-EXISTING TARGET
(selected by the owner; MODE L = NOT SELECTED)**, **U4 = CLASS A — OWNER-SUPPLIED FIXED ENDPOINT**, and
the indivisible endpoint tuple **scheme `http` / address family IPv4 / numeric loopback address
`127.0.0.1` / port `4096` / base URI `http://127.0.0.1:4096`**, with **fallback = NONE**.  The record is
marked **CANDIDATE RECORD / HUMAN OWNER DECISION / NOT YET INDEPENDENTLY ACCEPTED**, so the active status
is `OWNER / ORACLE-PARAMETER DECISION = CANDIDATE RECORD / OWNER INPUT FROZEN / INDEPENDENT FIDELITY
REVIEW PENDING`.  Acceptance-critical provenance: the **executor did not choose** Mode P, IPv4,
`127.0.0.1`, `4096` or the base URI — the human owner supplied them and the executor must not
reinterpret, replace or extend them; the historical documentation example `127.0.0.1:4096` is **not**
the source of authority.  The record freezes the no-fallback prohibitions (IPv4 → IPv6;
`127.0.0.1` → `localhost`; `127.0.0.1` → `::1`; `4096` → another port, first-free port or ephemeral
port; Mode P → Mode L; alternate OpenCode binary or installation; endpoints discovered from logs,
listener scans or process scans; and retry on another endpoint after failure), requires that a later
ETB execution verify **the exact frozen endpoint only with no endpoint discovery**, and states the
fail-closed consequence: no listener at `127.0.0.1:4096`, more than one matching listener, no owning
PID, ambiguous owner, wrong executable, wrong hash, wrong OpenCode version, process-instance mismatch,
or unavailable required identity evidence ⇒ **ETB must not be considered SATISFIED**, with **no**
fallback endpoint or mode attempted.  **Configuration is deliberately untouched:** the owner-authorized
endpoint is `http://127.0.0.1:4096` while `.devrelay/config.yaml` → `opencode.base_url` **remains `""`**
— the owner parameter decision exists, but the endpoint is **not** yet established in configuration; a
future separately authorized action may set `base_url` to the frozen tuple, and this round does **not**
authorize that mutation.  Preserved unchanged: `U1 = U1_NOT_ESTABLISHED` and `MODE L =
MODE_L_MECHANISM_NOT_YET_FREEZABLE` (Mode L is neither invalid nor impossible, and no automatic
Mode P → Mode L fallback exists); `U2 = U2_ESTABLISHED`, `U3 = U3_ESTABLISHED` and `MODE P =
MODE_P_MECHANISM_FREEZABLE` (not reopened, and the U2/U3 mechanism was **not** executed); the target
identity (OpenCode / `opencode-ai` 1.18.11,
`C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe`, SHA-256 `578d7eb3…`) with no
alternate binary, installation or retargeting; `ETB = DEFINITION ACCEPTED / NOT EXECUTED` and
`ETB EXECUTION / ORACLE = NOT YET DEFINED / NOT AUTHORIZED`, with no `ETB SATISFIED`,
`ETB UNSATISFIED` or `ETB EXECUTED` created; Mode-B `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE /
CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`
with oracle construction not resumed; `G0.5 / P6` unchanged with `P6 = UNPROVEN / UNSATISFIED` and G0.5
**NOT CLOSED**; Case-C and v0.3-E implementation `NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`;
`adopt_completed_turn` **DISABLED**.  The future-oracle rules left explicitly open (exact
`Get-NetTCPConnection` expression; exact `Count == 1` enforcement and failure handling; exact
`Win32_Process` PID query expression; pre/post target snapshot field sets and equality rules;
`CreationDate` precision-residual handling; `CreateFileW` `dwShareMode`; `ExecutablePath` access-failure
handling; `SeDebugPrivilege` failure handling; `GetFinalPathNameByHandleW` access-failure handling;
`\\?\` prefix handling; case comparison, slash normalization and drive-letter normalization rules;
target-executable canonicalization procedure details; exact evidence serialization; and any
`HARNESS_INVALID` vs `ETB UNSATISFIED` boundary) were **not** solved in this round.  Sequencing is
unchanged and no stage may be skipped: owner decision → independent review and acceptance → ETB
execution-oracle design → independent oracle review → separate execution/configuration authorization →
configuration establishment as authorized → ETB execution → independent ETB result review → only if
ETB SATISFIED may Mode-B SIC oracle construction resume.  This round performed **0** web retrievals,
**0** schema probes, **0** live TCP queries, **0** live process queries, **0** port/listener/process
enumeration, **0** endpoint establishment or probing, **0** configuration mutations, **0** OpenCode
starts/restarts, **0** listener work, **0** HTTP, **0** `/doc`, **0** `/session`, **0** ETB oracle
design, **0** ETB executions, **0** SIC attempts, **0** Mode-B oracle work, **0** provider/model calls,
**0** network, **0** G0.5 and **0** G1/G2 activity, and **0** runtime/test/dependency/version changes;
`opencode.base_url` remains `""`.

**The human owner's ETB mode / endpoint decision record was independently fidelity-reviewed and is
now authoritative accepted status.**  The independent fidelity review issued *APPROVE V0.3-E ETB
OWNER / ORACLE-PARAMETER DECISION RECORD* (**P0 = 0, P1 = 0, P2 = 0**; two non-blocking P3s), binding
the immutable decision record `docs/v0.3/V03E_G0_5_PRE_ETB_OWNER_ORACLE_PARAMETERS.md` (blob
`152311341b8bc8cfb93964f3709a6922a62d914c8a297dea1e3634940bb34cbe`, commit `bab4979`) to that
decision — an independent review decision, not executor self-approval — so the **HUMAN OWNER DECISION
IS ACCEPTED AS FAITHFULLY RECORDED**.  Authoritative owner-decision state: **U5 = MODE P — PRE-EXISTING
TARGET, SELECTED BY HUMAN OWNER** with **MODE L = NOT SELECTED** (Mode L is neither invalid nor
impossible, U1 is **not** resolved, and no automatic Mode P → Mode L fallback exists); **U4 = CLASS A —
OWNER-SUPPLIED FIXED ENDPOINT** with the indivisible tuple **`http` / IPv4 / `127.0.0.1` / `4096` /
`http://127.0.0.1:4096`** and **fallback = NONE**; the **executor selected none of these values**, and
the historical example `127.0.0.1:4096` is **not** the source of authority — the source of authority is
the human owner's explicit decision.  The authoritative no-fallback prohibitions remain frozen
(IPv4 → IPv6; `127.0.0.1` → `localhost`; `127.0.0.1` → `::1`; `4096` → any other port, first-free or
ephemeral; Mode P → Mode L; alternate OpenCode binary or installation; endpoint discovery from logs,
listeners or processes; retry against an alternate endpoint), and a later inability to satisfy the
frozen tuple must **fail closed**.  **Owner authority vs configuration (acceptance-critical):** the
**owner-authorized endpoint** is `http://127.0.0.1:4096`, but the **current configured endpoint is
NONE** — `.devrelay/config.yaml` → `opencode.base_url` **remains `""`** and is unchanged, so **owner
endpoint parameters are authoritative while the endpoint is NOT yet established in configuration**; no
configuration mutation is authorized by this bookkeeping round.  **Pre-existing target:** Mode P means
the target must be pre-existing for the later ETB attempt; this status does **not** assert that OpenCode
is running, that a listener exists, that `127.0.0.1:4096` is reachable, or that the endpoint currently
satisfies ETB, and the future ETB execution attempt must verify **exactly the frozen endpoint** with
**no discovery**.  **Frozen external inputs** for future ETB-oracle design (the oracle MUST consume them
and MUST NOT choose, derive, negotiate, normalize into substitutes or replace them): mode = MODE P;
endpoint policy = CLASS A OWNER-SUPPLIED FIXED ENDPOINT; scheme = `http`; address family = IPv4; host =
`127.0.0.1`; port = `4096`; base URI = `http://127.0.0.1:4096`; fallback = NONE.  **Target identity
preserved:** OpenCode / `opencode-ai` 1.18.11,
`C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe`, SHA-256 `578d7eb3…` — no
alternate binary, no alternate installation, no retargeting.  **Mode-P capability state preserved and
kept distinct:** `U2 = U2_ESTABLISHED`, `U3 = U3_ESTABLISHED` and `MODE P =
MODE_P_MECHANISM_FREEZABLE` remain accepted, and `MODE P = SELECTED BY HUMAN OWNER` is recorded
separately — mechanism freezability ≠ mode selection ≠ oracle implementation ≠ ETB execution.  **Still
NOT FROZEN** (ETB execution-oracle design items; not solved now): the exact `Get-NetTCPConnection`
expression; exact `Count == 1` enforcement/failure handling; exact `Win32_Process` PID query expression;
pre-request and post-request target snapshot exact field sets; pre/post equality and comparison rules;
`CreationDate` precision-residual handling; `CreateFileW` `dwShareMode`; `ExecutablePath` access-failure
handling; `SeDebugPrivilege` failure handling; `GetFinalPathNameByHandleW` access-failure handling;
`\\?\` prefix handling; case comparison, slash normalization and drive-letter normalization rules;
target-executable canonicalization details; exact evidence serialization; and the `HARNESS_INVALID` vs
`ETB UNSATISFIED` boundary if needed.  **Configuration authorization boundary:** a **future separately
authorized** stage may configure `opencode.base_url = http://127.0.0.1:4096` because the tuple is
owner-authorized and Mode P is owner-selected — this round **does not authorize and does not perform**
that mutation.  **Sequencing (no stage may be skipped):** OWNER / ORACLE-PARAMETER DECISION → fidelity
reviewed → acceptance bookkept and independently confirmed → **ETB EXECUTION-ORACLE DESIGN** →
independent oracle review → separate execution/configuration authorization → configuration
establishment as authorized → ETB execution → independent ETB-result review → **only if ETB SATISFIED**
may Mode-B SIC oracle construction resume.  **Preserved unchanged:** `ETB = DEFINITION ACCEPTED / NOT
EXECUTED` and `ETB EXECUTION / ORACLE = NOT YET DEFINED / NOT AUTHORIZED` (no `ETB SATISFIED`,
`ETB UNSATISFIED` or `ETB EXECUTED` created); `U1 = U1_NOT_ESTABLISHED` and `MODE L =
MODE_L_MECHANISM_NOT_YET_FREEZABLE`; Mode-B = `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE
ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER` with oracle
construction **not** resumed (the owner-authorized tuple does **not** mean the endpoint is configured or
established); `G0.5 / P6 = NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY
GAP` with `P6 = UNPROVEN / UNSATISFIED` and G0.5 **NOT CLOSED**; Case-C and v0.3-E implementation
`NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`; `adopt_completed_turn` **DISABLED**.  Review P3s recorded as
**non-blocking** (neither presented as blocking nor as resolved): **P3-1** the recurring phrase "no
untracked leftovers" is technically overbroad because `PROJECT_MEMORY.md` remains ignored/untracked —
preferred wording going forward, adopted in this entry, is "**tracked worktree clean; ignored/untracked
`PROJECT_MEMORY.md` persists**"; **P3-2** previously carried project P3s were not re-promoted.  This
bookkeeping round performed **0** web retrievals, **0** schema probes, **0** live TCP queries, **0** live
process queries, **0** port/listener/process enumeration, **0** endpoint establishment or probing,
**0** configuration mutations, **0** OpenCode starts/restarts, **0** listener work, **0** HTTP, **0**
`/doc`, **0** `/session`, **0** ETB oracle design, **0** ETB executions, **0** SIC attempts, **0**
Mode-B oracle work, **0** provider/model calls, **0** network, **0** G0.5 and **0** G1/G2 activity, and
**0** runtime/test/dependency/version changes; `opencode.base_url` remains `""`, the tracked worktree is
clean, and the ignored/untracked `PROJECT_MEMORY.md` persists.

**A candidate ETB execution oracle for Mode P / Class-A fixed endpoint now exists (design only; not
accepted, not frozen, not executed).**  `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md` freezes every
semantic rule a later authorized ETB attempt must apply — so that the executor chooses no semantic rule
at runtime — for the owner-selected **MODE P — PRE-EXISTING TARGET** with the **CLASS A
OWNER-SUPPLIED FIXED ENDPOINT** `http` / IPv4 / `127.0.0.1` / `4096` / `http://127.0.0.1:4096` and
**fallback = NONE**, against OpenCode / `opencode-ai` **1.18.11**
(`C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe`, SHA-256 `578d7eb3…`).
The artifact is marked **ETB EXECUTION ORACLE / MODE P / CLASS A OWNER-SUPPLIED FIXED ENDPOINT / ORACLE
CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EXECUTED / DOES NOT MODIFY CONFIGURATION / DOES NOT START
OPENCODE / DOES NOT PERFORM HTTP / DOES NOT AUTHORIZE ETB EXECUTION**, so the recorded status is
`ETB = DEFINITION ACCEPTED / NOT EXECUTED` with `ETB EXECUTION / ORACLE = CANDIDATE / NOT ACCEPTED / NOT
AUTHORIZED / NOT EXECUTED`.  Static design findings and frozen rules (no runtime choice remains): the
**production config-read mechanism is the existing `src/devrelay/config.py` function
`load_wiring_config(root_or_path) -> WiringConfig`**, consumed read-only and deterministically through
`WiringConfig.opencode.base_url` (the validator-normalized field, trailing `/` stripped) with the frozen
invocation `PYTHONPATH=<repo>/src python -c "…load_wiring_config(sys.argv[1]).opencode.base_url" "<repo>"`,
required to equal `http://127.0.0.1:4096` exactly (`-ceq`), with precommitted failure mapping (loader
module import failure → `HARNESS_INVALID`; `ConfigError`/absent file/`""`/mismatch → `ETB_UNSATISFIED`);
the **exact listener query** `@(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 4096 -State
Listen)` with `Count -eq 1` plus `LocalAddress -ceq '127.0.0.1'`, `LocalPort -eq 4096`, `State -eq
'Listen'` and a present positive `OwningProcess`; the **exact PID-scoped process query**
`@(Get-CimInstance -Namespace root/cimv2 -ClassName Win32_Process -Filter "ProcessId = <pid>")` with
`Count -eq 1` and required `ProcessId` / `ExecutablePath` / `CreationDate`; **process-instance identity =
PID + `CreationDate.Ticks`** (serialized as `ToString("o", InvariantCulture)` and `.Ticks`) with the
accepted **sub-resolution collision residual recorded** and no mathematical uniqueness claimed;
**canonicalization through `CreateFileW`** (`GENERIC_READ` `0x80000000`, share
`READ|WRITE|DELETE` `0x00000007`, `NULL` security attributes, `OPEN_EXISTING` `3`,
`FILE_ATTRIBUTE_NORMAL` `0x00000080`, `NULL` template) **plus
`GetFinalPathNameByHandleW(FILE_NAME_NORMALIZED + VOLUME_NAME_DOS, flags = 0, 32768-WCHAR buffer)`**
with return `0` or `>= 32768` failing closed and `CloseHandle` always on a `finally`-equivalent path;
**path text kept exactly as returned** (`\\?\` retained, no slash/case/drive-letter normalization) and
compared with **`-ceq`** (safe false-negative preferred over permissive equivalence); **SHA-256 via
`Get-FileHash -Algorithm SHA256 -LiteralPath`** on both the process-reported path and the accepted
target literal, each required to equal the accepted digest (hex letter case the only normalization,
`-ieq`); **version verification only through the exact frozen `package.json`** (no binary invocation, no
PATH/npm lookup) requiring `name = opencode-ai`, `version = 1.18.11` and a `bin.opencode` that resolves
under the accepted package root to the accepted executable canonicalized by the same procedure; a
**25-field identity snapshot**; the **S0/S1 two-snapshot plan** (no HTTP between them, full identity
equality required) that also freezes the **later Mode-B PRE/POST target-continuity contract** (contract
only — no Mode-B request set, no SIC outcome, no HTTP); the **three-outcome taxonomy**
`ETB_SATISFIED` / `ETB_UNSATISFIED` / `HARNESS_INVALID` with `ETB_UNSATISFIED` explicitly **not** SIC/P6/
G0.5 failure and `HARNESS_INVALID` reserved for untrustworthy oracle machinery only (no ETB semantic
result, no retry, stop and re-authorize); and **evidence serialization** at
`docs/v0.3/evidence/etb-execution/ETB_EVIDENCE.json` (`schema_version` `devrelay-etb-v1`, ordered
top-level fields, UTF-8 no-BOM, LF only, one final LF, no comments, no user/session/prompt/provider
content, frozen `UTF8Encoding($false)` writer) plus `MANIFEST.sha256` and a result artifact
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT.md` marked **CANDIDATE ETB RESULT / AWAITING INDEPENDENT
RESULT REVIEW**.  Even an accepted `ETB_SATISFIED` would mean only that the exact configured endpoint is
deterministically bound to the accepted target and that Mode-B SIC oracle **construction** may resume
after independent ETB result acceptance — it would not establish SIC semantics, P6, G0.5, session
incarnation, provenance, Mode-B PASS, Case-C authorization or `adopt_completed_turn`.  Preserved
unchanged: `opencode.base_url` is still `""` (no configuration mutation in this round and none before a
separate authorization); no endpoint is established; no listener existence or OpenCode liveness is
asserted; Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED /
PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`; `G0.5 / P6` remains `NOT RUN /
DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED`
and G0.5 **NOT CLOSED**; `G1`/`G2` remain `NOT RUN`; Case-C and v0.3-E implementation remain **NOT
AUTHORIZED**; `adopt_completed_turn` remains **DISABLED**; `U1 = U1_NOT_ESTABLISHED`,
`U2 = U2_ESTABLISHED`, `U3 = U3_ESTABLISHED`, `MODE L = MODE_L_MECHANISM_NOT_YET_FREEZABLE`,
`MODE P = MODE_P_MECHANISM_FREEZABLE` and the accepted owner decision are unchanged.  This design round
performed **0** web/network access, **0** `Get-NetTCPConnection` executions, **0** live `Get-CimInstance`
process queries, **0** listener/process/port enumeration, **0** endpoint probes, **0** config mutations,
**0** OpenCode starts, **0** HTTP, **0** `/doc`, **0** `/session`, **0** ETB executions, **0** SIC
attempts, **0** Mode-B oracle work, **0** provider/model calls, **0** G0.5 and **0** G1/G2 activity, and
**0** runtime/test/dependency/version changes; the tracked worktree is clean, and the ignored/untracked
`PROJECT_MEMORY.md` persists.

**The ETB Mode-P execution-oracle candidate was rejected by independent review, and a round-2
remediation revision now exists (still a candidate: not accepted, not frozen, not executed).**  The
independent review issued *REQUEST_CHANGES — V0.3-E ETB MODE-P EXECUTION ORACLE* (**P0 = 0, P1 = 3,
P2 = 2**) against candidate `b117daf` (blob `280e688b…`), so that candidate is **not** accepted and
**not** frozen and the last authoritative pre-oracle baseline remains `b3be79d`.
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md` was revised **in place** (no second oracle file) into a
self-contained round-2 remediation candidate.  The review's accepted portions are **preserved
unchanged** — owner tuple; ETB-definition conformance; production config-reader semantics
(**CONFIG_EXACTNESS_SOUND**); listener query and `Count == 1`; PID/process query; `CreationDate` identity
semantics; `CreateFileW` parameter values; `GetFinalPathNameByHandleW` flags/buffer size; AS-IS `\\?\`
with `-ceq`; package/version/bin binding; dual SHA-256 target rule; 25-field snapshot; S0/S1 plan; later
Mode-B PRE/POST contract; `HARNESS_INVALID` as pre-semantic/no-ETB-result; no-shopping; configuration
timing; status preservation — and **only the five blocking gaps were tightened**: **P1-A** native
machinery frozen verbatim (exact type `DevRelayEtbNativeV1`; the complete ready-to-use C# `Add-Type`
source with three `kernel32.dll` `DllImport` declarations using `EntryPoint`/`CharSet.Unicode`/
`ExactSpelling`/`SetLastError`, `LPWStr` marshaling, `StringBuilder [Out]` buffer and `bool`
`CloseHandle` return; the exact `Add-Type -TypeDefinition $nativeSource -Language CSharp -ErrorAction
Stop` invocation; `IntPtr` handles with `INVALID_HANDLE_VALUE = [IntPtr](-1)`; the
`[System.Text.StringBuilder]::new(32768)` buffer with the exact `$buffer.ToString(0, [int]$length)`
read-out; no NUL-terminated unbounded read, no resize, no retry; `CloseHandle` always on a
`finally`-equivalent path with a `false` return classified `HARNESS_INVALID`; the same helper applied to
both paths); **P1-B** atomic evidence publication frozen (directory `docs/v0.3/evidence/etb-execution`;
three finals plus three **same-directory** `.tmp` paths; the six-path preexistence rule where any existing
path yields `HARNESS_INVALID` with no delete/overwrite/cleanup/retry; the temp write primitive
`UTF8Encoding(false)` → `FileStream` `CreateNew`/`Write`/`FileShare.None` → `Flush(true)` → close →
`ReadAllBytes` byte-equality; evidence temp verification for byte equality, exactly one final LF, the
byte before it being neither LF nor CR, no BOM, `ConvertFrom-Json` parse, matching `schema_version` and
`outcome`; in-memory result construction written only to the result temp; and `System.IO.File.Move(temp,
final)` with no overwrite only after all three temps verify, in the exact order evidence → manifest →
result with the result published **last**, followed by per-move and post-set verification); **P1-C**
manifest construction/verification frozen (coverage of exactly the one evidence file, never itself and
never the Markdown result; exactly one line `<64-lowercase-sha256><two ASCII spaces>docs/v0.3/evidence/
etb-execution/ETB_EVIDENCE.json<LF>`; no header or comments; UTF-8 no-BOM/LF; digest computed over the
intended evidence bytes before publication; read-back byte equality plus digest/spaces/path exactness;
and the frozen in-memory hasher `SHA256.Create()` → `ComputeHash` → lowercase hex, which is
evidence-machinery hashing only and does not change the `Get-FileHash` target-executable rule); **P2-A**
failure taxonomy frozen per class via a deterministic table (config reader, PowerShell command
availability, listener, process, Add-Type/P-Invoke, hashing, package manifest, evidence machinery) with
any unclassified unexpected exception classified `HARNESS_INVALID`, no ETB semantic result, no retry,
stop; **P2-B** timestamps and JSON frozen (`[System.DateTimeOffset]::UtcNow` formatted
`yyyy-MM-dd'T'HH:mm:ss.fffffff'Z'` with `InvariantCulture` for both timestamps, no local time;
`ConvertTo-Json -Depth 12 -Compress` written with `UTF8Encoding($false)` as one JSON line plus exactly
one LF and no CRLF conversion; every object `[ordered]` with the frozen top-level, `endpoint`, `target`,
snapshot, `checks` (18 keys valued only `PASS`/`FAIL`/`NOT_REACHED`), `non_claims` (6 ordered entries)
and `activity_counters` (14 ordered keys) orders, plus a frozen value vocabulary — `MODE_P`, `http`,
`IPv4`, `127.0.0.1`, `4096`, `http://127.0.0.1:4096`, `NONE`, `Listen`, lowercase-hex digests, integer
PIDs/ports/ticks — so no executor choice remains).  Also newly frozen: partial-publication semantics (any
partial output set is non-authoritative and invalid as an ETB result, nothing is deleted, and the
existence of the evidence or manifest file — or even the Markdown result — without a fully verified final
set never means an ETB result exists) and the rule that a provisional `ETB_SATISFIED`/`ETB_UNSATISFIED`
**must not survive** an evidence-integrity failure, the final classification becoming `HARNESS_INVALID /
NO ETB SEMANTIC RESULT`; the configuration-establishment fidelity requirement that the future separately
authorized stage write the exact owner literal `http://127.0.0.1:4096` with no trailing slash; and
static-anchor hygiene (line numbers informational only — module path, symbol names and the semantic call
path are the frozen authority).  Recorded status is unchanged and unimplicated as accepted: `ETB =
DEFINITION ACCEPTED / NOT EXECUTED` and `ETB EXECUTION / ORACLE = CANDIDATE / NOT ACCEPTED / NOT
AUTHORIZED / NOT EXECUTED`.  The executor-choice self-check over the nineteen machinery items found **no
remaining runtime choice**, which is why the revision may be committed as a candidate.  `opencode.base_url`
remains `""`; no evidence directory or evidence file was created; no native type was compiled; no
PowerShell oracle code was executed; the tracked worktree is clean and the ignored/untracked
`PROJECT_MEMORY.md` persists.  This remediation round performed **0** web/network access, **0** live
endpoint queries, **0** `Get-NetTCPConnection` executions, **0** live `Get-CimInstance` queries, **0**
listener/process/port enumeration, **0** config mutations, **0** OpenCode starts, **0** HTTP, **0**
`/doc`, **0** `/session`, **0** `Add-Type` executions, **0** P/Invoke executions, **0** evidence
publications, **0** ETB executions, **0** SIC attempts, **0** Mode-B oracle work, **0** provider/model
calls, **0** G0.5 and **0** G1/G2 activity, and **0** runtime/test/dependency/version changes.  Preserved:
Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED /
PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`; `G0.5 / P6` remains `NOT RUN / DEFINITION
ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED` and G0.5
**NOT CLOSED**; `G1`/`G2` remain `NOT RUN`; Case-C and v0.3-E implementation remain **NOT AUTHORIZED**;
`adopt_completed_turn` remains **DISABLED**.

**The Round-2 ETB Mode-P execution oracle was independently approved and is now authoritative accepted
repository status: ACCEPTED / FROZEN / NOT EXECUTED / EXECUTION NOT AUTHORIZED.**  The independent review
issued *APPROVE V0.3-E ETB MODE-P ROUND-2 EXECUTION ORACLE* (**P0 = 0, P1 = 0, P2 = 0**; two
non-blocking P3s) — an independent review decision, not executor self-approval — binding exactly
`oracle_commit = 1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc` and `oracle_sha256 =
01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921`
(`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md`).  **Oracle provenance rule (permanent, authoritative):**
that `oracle_commit`/`oracle_sha256` pair is the accepted immutable oracle identity; a later
acceptance-bookkeeping commit, a later execution/configuration-authorization commit, and the current HEAD
at execution time **MUST NOT** replace `oracle_commit`, and the future ETB evidence fields
`oracle_commit`/`oracle_sha256` must reference exactly this independently accepted oracle.  The artifact
itself is **immutable** and was **not** modified: it keeps its construction-time `ORACLE CANDIDATE / NOT
ACCEPTED / NOT FROZEN` header under the established immutable-candidate-artifact + independent
approval-record + authoritative active-status pattern.  Authoritative status now reads `ETB = DEFINITION
ACCEPTED / NOT EXECUTED` together with `ETB EXECUTION / ORACLE = ACCEPTED / FROZEN / NOT EXECUTED /
EXECUTION NOT AUTHORIZED`; **no** `ETB_SATISFIED`, `ETB_UNSATISFIED`, `HARNESS_INVALID` result or
`ETB_EXECUTED` is created.  Accepted oracle scope (independently reviewed, semantics unchanged): the
production config-reader semantics; exact Mode-P endpoint verification; the unique-listener rule; the
unique owning-PID rule; the PID + `CreationDate` identity discriminator; the exact P/Invoke declarations;
the `CreateFileW` parameters; the `GetFinalPathNameByHandleW` procedure; the canonical-path AS-IS /
case-sensitive equality rule; the dual executable SHA-256 checks; package/version/bin binding; the
25-field identity snapshot; the S0/S1 ETB snapshot plan; the later Mode-B PRE/POST continuity contract;
the deterministic failure taxonomy; the UTC timestamp format; the ordered JSON schema; the exact JSON
writer settings; temp/final paths; the preexistence policy; `CreateNew` + `Flush(true)` + read-back
verification; manifest coverage/format/SHA-256 procedure; the result template; the same-directory
`File.Move` publication procedure; publication ordering; post-publication verification; partial-output
semantics; `HARNESS_INVALID` = NO ETB SEMANTIC RESULT; and no shopping / no fallback / no HTTP.  Owner
inputs remain frozen and unreinterpreted — **MODE P — PRE-EXISTING TARGET**; **CLASS A — OWNER-SUPPLIED
FIXED ENDPOINT**; `http` / IPv4 / `127.0.0.1` / `4096` / `http://127.0.0.1:4096`; fallback **NONE**.
Configuration state is unchanged: the owner-authorized endpoint is `http://127.0.0.1:4096` while the
currently configured endpoint is **NONE** and `.devrelay/config.yaml` → `opencode.base_url` remains
`""`; no configuration mutation is authorized or performed in this round, and the separately authorized
future configuration-establishment stage must write the exact owner literal `http://127.0.0.1:4096`
with **no trailing slash**.  **Rejected-candidate history preserved:** `b117daf` was rejected with
*REQUEST_CHANGES — V0.3-E ETB MODE-P EXECUTION ORACLE* (P0 = 0, P1 = 3, P2 = 2) and remains
unrewritten; the accepted oracle is the Round-2 remediation at `1c6c7cd`, **not** `b117daf`.  Review P3s
recorded as **non-blocking** (neither an unresolved oracle blocker): **P3-1** the executor's chat report
rendering lost the PowerShell backtick in the displayed `$json + "`n"` expression while the actual
tracked oracle text was verified correct; **P3-2** the standing `PROJECT_MEMORY` wording issue remains,
with the preferred wording "**tracked worktree clean; ignored/untracked `PROJECT_MEMORY.md` persists**"
used here.  **Next-stage classification:** `ETB EXECUTION / CONFIGURATION AUTHORIZATION = NOT YET GRANTED
/ NOT YET EXECUTED`; the next possible stage after this bookkeeping is independently confirmed is a
**separate ETB execution/configuration authorization**, which may authorize setting
`opencode.base_url = http://127.0.0.1:4096` and exactly one ETB execution under the accepted frozen
oracle — **this bookkeeping authorizes neither**.  **Sequencing (no stage may be skipped):** ETB
definition accepted → capability prerequisites accepted → owner mode/endpoint decision accepted → ETB
execution oracle designed → independent oracle approval → acceptance bookkeeping → independent
bookkeeping confirmation; **then only**: separate execution/configuration authorization → configuration
establishment → exactly one ETB execution attempt → independent ETB result review → only if
`ETB_SATISFIED` is independently accepted may Mode-B SIC oracle construction resume.  An accepted ETB
execution oracle does **not** itself mean the endpoint has been configured or ETB has been satisfied, so
Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED /
PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`; `G0.5 / P6` remains `NOT RUN /
DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED`
and G0.5 **NOT CLOSED**; `G1`/`G2` remain `NOT RUN`; Case-C and v0.3-E implementation remain **NOT
AUTHORIZED**; `adopt_completed_turn` remains **DISABLED**.  This bookkeeping round performed **0**
web/network access, **0** endpoint queries, **0** `Get-NetTCPConnection` executions, **0** live
`Get-CimInstance` queries, **0** listener/process/port enumeration, **0** config mutations, **0** OpenCode
starts, **0** HTTP, **0** `/doc`, **0** `/session`, **0** `Add-Type` executions, **0** P/Invoke
executions, **0** evidence publications, **0** ETB executions, **0** SIC attempts, **0** Mode-B oracle
work, **0** provider/model calls, **0** G0.5 and **0** G1/G2 activity, and **0**
runtime/test/dependency/version changes; no evidence file and no result artifact were created; the
tracked worktree is clean and the ignored/untracked `PROJECT_MEMORY.md` persists.

**A candidate authorization record for the one-shot ETB execution / configuration action now exists (not
accepted, not effective, not executed).**  `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_AUTHORIZATION.md` is
marked **ETB EXECUTION / CONFIGURATION AUTHORIZATION / CANDIDATE RECORD / NOT ACCEPTED / NOT EFFECTIVE /
DOES NOT MODIFY CONFIGURATION / DOES NOT EXECUTE ETB / DOES NOT START OPENCODE / DOES NOT AUTHORIZE HTTP /
ONE ETB ATTEMPT ONLY IF LATER INDEPENDENTLY ACCEPTED**, so the current active authorization status is
`ETB EXECUTION / CONFIGURATION AUTHORIZATION = CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT EXECUTED`.
Only if a separate independent authorization review accepts it may it authorize, in order, (A) exactly
one configuration establishment — writing `http://127.0.0.1:4096` (no trailing slash, no alternate URI,
no other field) to `<root>/.devrelay/config.yaml` → `opencode.base_url`, currently `""`, with the exact
before/after diff recorded — and then (B) **exactly ONE** ETB execution attempt under the accepted frozen
oracle, bound permanently to `oracle_commit = 1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc` and
`oracle_sha256 = 01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921` — the future
execution must **not** use `d058b38`, the authorization commit, the execution-time HEAD or any later
commit as `oracle_commit`, and no oracle modification is authorized.  Frozen boundaries: Mode P remains
**pre-existing target** (no OpenCode start/restart, no new instance, no listener creation, no rebinding,
no Mode P → Mode L switch, and no recovery by target creation); fallback stays **NONE** (no IPv4 → IPv6,
`localhost`, `::1`, other/first-free/ephemeral port, alternate executable or installation, PATH-selected
target, log/listener/process-derived endpoint, or retry against another endpoint); the authorized
**attempt budget is exactly one**, consumed immediately before the **first oracle operational probe after
configuration establishment** (pure configuration establishment and static preflight of oracle
provenance, authorization identity and pre-mutation config state do **not** consume it), with no rerun, no
"verification rerun" and no second attempt after `ETB_SATISFIED`, `ETB_UNSATISFIED` or `HARNESS_INVALID`
— any further attempt needs new authorization plus independent review; a non-deterministic configuration
mutation must **not** be improvised but returned as a control failure for review (no substitute endpoint,
no other field, no alternate config mechanism); outputs may use **only** the oracle-frozen evidence/result
paths; the result may only be `ETB_SATISFIED`, `ETB_UNSATISFIED` or `HARNESS_INVALID / NO ETB SEMANTIC
RESULT`, and none is authoritative before separate independent ETB-result review; `ETB_UNSATISFIED` is
**not** SIC/P6/G0.5 failure and not a claim that OpenCode cannot support Mode B; `HARNESS_INVALID` means
**no ETB semantic result exists**, with no retry or repair-and-continue inside the same authorization;
**no HTTP**, no `/doc`, no `/session` and no provider/model request are authorized, and no Mode-B HTTP
activity is authorized; **no OpenCode start/restart** is authorized; the frozen future execution order is
authorization identity → oracle provenance → config precondition → exact `base_url` write → production
reader verification → configuration-establishment evidence → exactly one ETB attempt → consume 1 of 1
before the first live probe → execute the frozen oracle → publish the oracle-defined candidate
evidence/result → **STOP** → independent ETB result review (no Mode-B construction in the same round);
**no automatic configuration rollback is authorized** — `opencode.base_url` remains
`http://127.0.0.1:4096` after the attempt unless a future separately authorized action changes it, with no
rollback-on-failure and no executor discretion; and the accepted oracle's output-preexistence rule is
preserved (no deletion and no overwrite of old outputs; a failed precondition follows the frozen
`HARNESS_INVALID`/no-result semantics).  Even a future accepted `ETB_SATISFIED` would establish none of
SIC semantics, P6, G0.5, session incarnation, turn provenance, message provenance, pending-handle
semantics, Mode-B PASS, Case-C authorization or `adopt_completed_turn`; it would only permit independent
ETB result review and, only once `ETB_SATISFIED` is independently accepted, the resumption of Mode-B SIC
oracle construction.  Preserved unchanged: `ETB = DEFINITION ACCEPTED / NOT EXECUTED`; `ETB EXECUTION /
ORACLE = ACCEPTED / FROZEN / NOT EXECUTED / EXECUTION NOT AUTHORIZED`; owner inputs (**MODE P**,
**CLASS A**, `http` / IPv4 / `127.0.0.1` / `4096` / `http://127.0.0.1:4096`, fallback **NONE**) with no
reinterpretation; `opencode.base_url` still `""` with no configuration mutation in this round; Mode-B
remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE
CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER` (this authorization candidate does **not** unblock
it); `G0.5 / P6` remains `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP`
with `P6 = UNPROVEN / UNSATISFIED` and G0.5 **NOT CLOSED**; `G1`/`G2` remain `NOT RUN`; Case-C and v0.3-E
implementation remain **NOT AUTHORIZED**; `adopt_completed_turn` remains **DISABLED**.  This
authorization-recording round performed **0** web/network access, **0** endpoint queries, **0**
`Get-NetTCPConnection` executions, **0** live `Get-CimInstance` queries, **0** port/listener/process
enumeration, **0** config mutations, **0** OpenCode starts/restarts, **0** HTTP, **0** `/doc`, **0**
`/session`, **0** `Add-Type` executions, **0** P/Invoke executions, **0** evidence publications, **0** ETB
executions, **0** SIC attempts, **0** Mode-B oracle work, **0** provider/model calls, **0** G0.5 and **0**
G1/G2 activity, and **0** runtime/test/dependency/version changes; no evidence file and no result
artifact were created; the tracked worktree is clean and the ignored/untracked `PROJECT_MEMORY.md`
persists.

**The ETB execution/configuration authorization candidate was rejected by independent review, and a
round-2 remediation revision now exists (still a candidate: not accepted, not effective, not executed).**
The independent review issued *REQUEST_CHANGES — V0.3-E ETB EXECUTION / CONFIGURATION AUTHORIZATION*
(**P0 = 0, P1 = 2, P2 = 2**) against `f52cb2b4c0ece73097511c816b448d9ede649fb5`, which **remains rejected**
and unamended; the last authoritative pre-authorization baseline remains `d058b38`.
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_AUTHORIZATION.md` was revised **in place** (no second authorization
artifact) into a self-contained round-2 remediation candidate that preserves the review's accepted
portions (authorization scope; oracle provenance; owner tuple; one-ETB-attempt ceiling; no OpenCode start;
no HTTP; fallback NONE; configuration-after-attempt policy; ETB result/non-claim semantics; Mode-B/G0.5
preservation) and closes exactly four gaps.  **P1-A config-mutation mechanism** is now frozen byte-exactly
from a read-only static audit of the current file: `PRE_CONFIG_SHA256 =
daaf72578cb4a91b5adeb481530baf47577174325167caddf7249964da7923a8`, `PRE_CONFIG_SIZE = 1876` bytes, **no
BOM**, **LF only** (0 CRLF, final LF), valid UTF-8, a **clean duplicate-key structural audit** (exactly one
effective `opencode` key and exactly one effective `base_url` key; no anchors, aliases or merge keys), and
production-resolved `opencode.base_url == ""`; the mutation is a **byte-exact patch** over the unique
24-byte span `OLD_CONFIG_SPAN_HEX = 6f70656e636f64653a0a2020626173655f75726c3a202222` (occurrence count
exactly 1) replaced by `NEW_CONFIG_SPAN_HEX =
6f70656e636f64653a0a2020626173655f75726c3a2022687474703a2f2f3132372e302e302e313a3430393622`,
yielding the statically constructed post-image `POST_CONFIG_SIZE = 1897` bytes / `POST_CONFIG_SHA256 =
b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf`, with a verified byte-diff witness
that only that span changes (1065 unchanged prefix bytes, 787 unchanged suffix bytes) and **no**
`yaml.safe_dump`, regex edit, generic string replacement or manual-editor mutation authorized; the writer
is frozen as a single `python` invocation using exclusive-create (`xb`), complete post-image write,
stream flush, `os.fsync`, close, read-back byte/hash verification, publication by exactly
`os.replace(CONFIG_TEMP, CONFIG_FINAL)` in the same directory, post-replace read-back verification and one
production-reader invocation requiring the resolved value `http://127.0.0.1:4096`, with
`CONFIG TEMP = <root>/.devrelay/config.yaml.etb-auth.tmp`, **CONFIG BACKUP = NONE** and a temp
non-existence precondition.  **P1-B authorization-use / pre-ETB failure / reuse semantics** are frozen:
two **separate** one-shot budgets — `AUTHORIZATION_USE_BUDGET = 1 of 1` and `ETB_ATTEMPT_BUDGET = 1 of 1`
— where the authorization is consumed **immediately at the start of the future operational round, before
config mutation, config-evidence creation, oracle output checks or ETB execution**, can never be reused,
and any later failure (even with ETB never started) stops the round with the frozen pre-ETB token
**`AUTHORIZATION_CONTROL_FAILURE`** (authorization consumed, ETB NOT started, `ETB_ATTEMPT = 0/1`, **no**
ETB semantic result — and explicitly not `ETB_UNSATISFIED`/`ETB_SATISFIED`/`HARNESS_INVALID`/SIC/P6/G0.5
failure), with no retry, no repair-and-continue and no preparation-retry loophole.  **P2-A
output-precondition timing** is reconciled: the authorization layer no longer pre-checks the oracle's six
output paths; instead `ETB_ATTEMPT = 1 of 1` is consumed **immediately before entering the accepted frozen
oracle at its first step**, so all oracle machinery (identity checks, output-preexistence checks, HARNESS
validation, live queries) runs **inside** the single consumed attempt and an oracle preexistence failure
correctly yields `HARNESS_INVALID / NO ETB SEMANTIC RESULT` with the attempt already consumed.  **P2-B
config-establishment evidence** is frozen at `docs/v0.3/evidence/etb-execution/CONFIG_ESTABLISHMENT.json`
(+ `.tmp`) as **authorization/configuration control evidence only** — not ETB semantic evidence, not
covered by the oracle `MANIFEST.sha256`, not an ETB result — with `schema_version =
devrelay-etb-config-establishment-v1`, an exact 17-field ordered top-level schema (`schema_version`,
`authorization_commit`, `authorization_sha256`, `oracle_commit`, `oracle_sha256`, `config_path`,
`pre_config_sha256`, `expected_pre_config_sha256`, `pre_resolved_base_url`, `authorized_base_url`,
`post_config_sha256`, `expected_post_config_sha256`, `post_resolved_base_url`, `mutation_scope`,
`authorization_use`, `etb_attempt`, `control_status`), frozen values (`config_path =
.devrelay/config.yaml`; `authorized_base_url = http://127.0.0.1:4096`; `mutation_scope =
opencode.base_url_only`; `authorization_use = 1/1_CONSUMED`; `etb_attempt = 0/1_NOT_STARTED`;
`control_status = CONFIG_ESTABLISHED`), and the accepted oracle's deterministic serialization discipline
(`ConvertTo-Json -Depth 12 -Compress`, UTF-8 no-BOM, one JSON line plus exactly one LF, `UTF8Encoding(false)`,
temp exclusive create → write → durable flush → close → read-back verification → same-directory
`System.IO.File.Move(temp, final)` without overwrite).  The authorization identity model is frozen too
(`authorization_commit`/`authorization_sha256` = the independently accepted commit and blob of **this**
revision, not replaceable by later bookkeeping or execution-time HEAD), and a 19-step future operational
order is frozen (enter authorization → consume authorization use → verify identities → verify config
pre-image and pre-value → construct post-image → write/flush/read-back temp → `os.replace` → read-back
verify → production-reader verify → publish config evidence → consume ETB attempt → invoke the frozen
oracle from its first step → allow only the oracle's control state → publish only oracle-defined outputs →
STOP → independent ETB result review), with **no automatic configuration rollback** after any failure and
the accepted oracle artifact left **immutable**.  Preserved unchanged: `ETB = DEFINITION ACCEPTED / NOT
EXECUTED`; `ETB EXECUTION / ORACLE = ACCEPTED / FROZEN / NOT EXECUTED / EXECUTION NOT AUTHORIZED`; owner
inputs (MODE P, CLASS A, `http` / IPv4 / `127.0.0.1` / `4096`, fallback NONE); `opencode.base_url` still
`""` with **no** configuration mutation in this round; Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT
FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE
BLOCKER`; `G0.5 / P6` remains `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY
GAP` with `P6 = UNPROVEN / UNSATISFIED` and G0.5 **NOT CLOSED**; `G1`/`G2` remain `NOT RUN`; Case-C and
v0.3-E implementation remain **NOT AUTHORIZED**; `adopt_completed_turn` remains **DISABLED**.  The current
authorization status is `ETB EXECUTION / CONFIGURATION AUTHORIZATION = ROUND-2 CANDIDATE / NOT ACCEPTED /
NOT EFFECTIVE / NOT EXECUTED` — no authorization is granted, no config changed and no ETB executed.  The
executor-choice self-check over the eighteen machinery items found **no remaining runtime choice**.  This
remediation-design round performed **0** web/network access, **0** endpoint queries, **0**
`Get-NetTCPConnection` executions, **0** live `Get-CimInstance` queries, **0** port/listener/process
enumeration, **0** config mutations, **0** OpenCode starts, **0** HTTP, **0** `/doc`, **0** `/session`,
**0** `Add-Type` executions, **0** P/Invoke executions, **0** execution-evidence publications, **0** ETB
executions, **0** SIC attempts, **0** Mode-B oracle work, **0** provider/model calls, **0** G0.5 and **0**
G1/G2 activity, and **0** runtime/test/dependency/version changes; static read-only config
reads/hashes/audit are recorded separately and are not operational ETB activity; the tracked worktree is
clean and the ignored/untracked `PROJECT_MEMORY.md` persists.

**The ETB execution/configuration authorization Round-2 candidate was rejected by independent review, and
a round-3 durable-claim remediation candidate now exists (still a candidate: not accepted, not effective,
not executed).**  The independent review issued *REQUEST_CHANGES — V0.3-E ETB EXECUTION / CONFIGURATION
AUTHORIZATION ROUND-2* (**P0 = 0, P1 = 1, P2 = 0, P3 = 2**) against `390eda1aeacb33032611030d47727e0a69650459`,
which **remains rejected** and unamended (as does the earlier `f52cb2b` rejection with P0 = 0, P1 = 2,
P2 = 2); the last authoritative pre-authorization baseline remains `d058b38`.  The review **closed**
`P1_A_CONFIG_MUTATION`, `P1_B_AUTHORIZATION_REUSE`, `P2_A_OUTPUT_TIMING` and `P2_B_CONFIG_EVIDENCE`, and all
Round-2 frozen semantics are preserved unchanged (byte-exact config mutation with `PRE_CONFIG_SHA256 =
daaf7257…` / 1876 bytes → `POST_CONFIG_SHA256 = b5e4abab…` / 1897 bytes through the unique 24-byte span;
`CONFIG TEMP`/`CONFIG FINAL` with `CONFIG BACKUP = NONE`; the `python` `xb`/`os.fsync`/`os.replace` writer
with read-back verification; the 17-field `devrelay-etb-config-establishment-v1` control-evidence schema and
its deterministic serialization; both 1-of-1 budgets; the `AUTHORIZATION_CONTROL_FAILURE` token;
no-rollback; no-retry; owner inputs; oracle provenance).  `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_AUTHORIZATION.md`
was revised **in place** (no second authorization artifact) as a self-contained round-3 remediation
candidate that closes the remaining blocking finding — the execution-evidence directory does not exist and
parent-directory creation behaviour was unfrozen — and tightens the crash/replay nuance so that repository
state alone durably distinguishes the three states without chat history, executor memory or an ephemeral
process.  **Durable one-shot claim markers** now live under the **already existing** parent
`docs/v0.3/evidence` (deliberately not inside the not-yet-existent `etb-execution` directory):
`docs/v0.3/evidence/ETB_AUTHORIZATION_USE.claim` (+ `.tmp`) with `schema_version =
devrelay-etb-authorization-use-v1` and the ordered fields `schema_version`, `authorization_commit`,
`authorization_sha256`, `oracle_commit`, `oracle_sha256`, `state = CONSUMED` (UTF-8, no BOM, one LF), and
`docs/v0.3/evidence/ETB_ATTEMPT_USE.claim` (+ `.tmp`) with `schema_version =
devrelay-etb-attempt-use-v1` and the same ordered fields; **temp-or-final presence is authoritative and
fail-closed** (no parser success required), so a crash during claim writing or a missing final rename still
means CONSUMED.  The **durable consumption boundaries** are frozen: `AUTHORIZATION_USE = 1/1 CONSUMED` the
moment exclusive creation of the authorization claim temp succeeds (performed before config mutation,
before creating the `etb-execution` directory, before config evidence, before ETB-attempt claiming and
before ETB execution), and `ETB_ATTEMPT = 1/1 CONSUMED` the moment exclusive creation of the ETB attempt
claim temp succeeds (after successful configuration establishment and `CONFIG_ESTABLISHMENT.json`
publication, before entering the frozen oracle).  **Crash recovery** is frozen: a crash before successful
exclusive creation of the authorization claim temp leaves the authorization **UNUSED** (the only window in
which it remains unused), while a crash after it leaves it **CONSUMED** with no ambiguous pre-mutation
window; `PRE_CONFIG_SHA256` is **demoted to a corroborating invariant only** and is no longer the sole
authorization-consumption marker; a crash after ETB-attempt consumption can never permit rerunning ETB.  A
**durable state recovery table** fixes the interpretation: authorization claim absent + ETB claim absent →
`AUTHORIZATION UNUSED`; authorization present + ETB absent → `AUTHORIZATION CONSUMED / ETB NOT STARTED`;
both present → `AUTHORIZATION CONSUMED / ETB ATTEMPT CONSUMED`; ETB present while authorization absent →
**control-state inconsistency / fail closed / no execution / independent review required**.  The
**execution-evidence directory rule** is frozen: `docs/v0.3/evidence/etb-execution` is created only after
the authorization claim is durably consumed and before configuration mutation, exactly via
`[System.IO.Directory]::CreateDirectory("docs/v0.3/evidence/etb-execution")` (repository-root-resolved
exact equivalent allowed), with no alternate directory, parent search, timestamped directory, suffix or
fallback path, followed by a requirement that the exact path exists and **is a directory**; failure or a
non-directory at that path → `AUTHORIZATION_CONTROL_FAILURE` with authorization consumed and ETB not
started; a pre-existing **actual directory** is permitted (idempotent, never deleted or recreated), which
removes executor choice.  Claim markers are **never deleted** after success, `ETB_UNSATISFIED`,
`HARNESS_INVALID`, `AUTHORIZATION_CONTROL_FAILURE` or crash recovery — they are durable one-shot witnesses
— and a **future new authorization must define its own claim-marker namespace/path** before execution (no
executor may delete the markers to reuse the paths).  A 22-step operational order is frozen (static
identity/oracle verification → require authorization claim absent → **exclusive-create it (AUTHORIZATION
CONSUMED)** → publish it → create-or-verify the evidence directory → config-evidence paths absent → config
pre-image verification → production pre-value `""` → post-image construction → write/fsync/read-back temp →
`os.replace` → final SHA verification → production post-value verification → publish config evidence →
require ETB claim absent → **exclusive-create it (ETB ATTEMPT CONSUMED)** → publish it → invoke the frozen
oracle from its first step → only frozen control/result state → only oracle-defined outputs → STOP →
independent ETB-result review), with failure semantics frozen per window (pre-authorization-claim: still
UNUSED and no alternate action; post-authorization-claim/pre-ETB: consumed, `AUTHORIZATION_CONTROL_FAILURE`,
new authorization required; post-ETB-claim: attempt consumed, no second attempt, no ETB semantic result if
the oracle was never entered) and no-rollback preserved.  Current status:
`ETB EXECUTION / CONFIGURATION AUTHORIZATION = ROUND-3 CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT
EXECUTED`; **no claim marker currently exists**, no evidence directory is created now, and no config
mutation occurs now.  Preserved unchanged: `ETB = DEFINITION ACCEPTED / NOT EXECUTED`; `ETB EXECUTION /
ORACLE = ACCEPTED / FROZEN / NOT EXECUTED / EXECUTION NOT AUTHORIZED`; owner inputs; `opencode.base_url`
still `""`; Mode-B blocked (`NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED
/ PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`); `G0.5 / P6` unchanged with `P6 =
UNPROVEN / UNSATISFIED` and G0.5 **NOT CLOSED**; Case-C and v0.3-E implementation **NOT AUTHORIZED**;
`G1`/`G2` `NOT RUN`; `adopt_completed_turn` **DISABLED**.  This remediation-design round created **no**
claim markers, **no** `etb-execution` directory, **no** config-establishment evidence, **no** ETB evidence
or result, **no** config temp and **no** config mutation, and performed **0** web/network access, **0**
endpoint queries, **0** `Get-NetTCPConnection` executions, **0** live `Get-CimInstance` queries, **0**
port/listener/process enumeration, **0** OpenCode starts, **0** HTTP, **0** `/doc`, **0** `/session`, **0**
`Add-Type` executions, **0** P/Invoke executions, **0** ETB executions, **0** SIC attempts, **0** Mode-B
work, **0** provider/model calls, **0** G0.5 and **0** G1/G2 activity, and **0**
runtime/test/dependency/version changes; the tracked worktree is clean and the ignored/untracked
`PROJECT_MEMORY.md` persists.

**The ETB execution/configuration authorization Round-3 candidate was rejected by independent review, and
a round-4 claim-writer mechanical-closure candidate now exists (still a candidate: not accepted, not
effective, not executed).**  The independent review issued *REQUEST_CHANGES — V0.3-E ETB EXECUTION /
CONFIGURATION AUTHORIZATION ROUND-3* (**P0 = 0, P1 = 1, P2 = 1, P3 = 2**) against
`c106b2d93b272fb337795e8712f58e0c273088fa` (artifact blob
`29019f683c4c217654034fc1408d2942b0b384832125fe80b7a6303927d015b0`), which **remains rejected** and
unamended (as do `390eda1` with P0 = 0, P1 = 1, P2 = 0, P3 = 2 and `f52cb2b` with P0 = 0, P1 = 2, P2 = 2);
the last authoritative pre-authorization baseline remains `d058b38`.  `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_AUTHORIZATION.md`
was revised **in place** (no second authorization artifact) as a self-contained round-4 remediation
candidate that closes exactly the four Round-3 findings and redesigns nothing else.  **P1 — claim-writer
exactness:** both claim writers are now frozen to **Windows PowerShell / .NET only** (no Python claim
writer, no `os.fsync` alternative, no alternate language, no executor-authored replacement code) with one
exact implementation, `Write-DevRelayOneShotClaim`, embedded **verbatim** in the artifact (104 lines,
byte-identical to the frozen source): `[ordered]` claim object; `ConvertTo-Json -Depth 4 -Compress`;
`$json + "`n"` (exactly one final LF); `[System.Text.UTF8Encoding]::new($false)` (no BOM);
`[System.IO.FileStream]::new($TempPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write,
[System.IO.FileShare]::None)`; a single `$stream.Write($bytes, 0, $bytes.Length)`; `$stream.Flush($true)`;
`$stream.Dispose()` on a `finally`-equivalent path; `[System.IO.File]::ReadAllBytes` with explicit
byte-by-byte equality for both the temp and the published final; and publication by the **two-argument**
`[System.IO.File]::Move($TempPath, $FinalPath)` as the **sole** publication primitive, which must fail
rather than overwrite an existing destination (the explicit `File.Exists` check before the move is only an
additional fail-closed check) — with every alternative forbidden: no overwrite `File.Move` overload, no
`File.Replace`, no `Move-Item`, no `Rename-Item`, no Python rename, no `os.rename`, no `os.replace`, no
other primitive.  The **consumption boundary** remains the successful return of `FileMode.CreateNew` (which
MUST fail if the temp exists; no truncation, reuse or overwrite), and the exact future invocations for both
claims are frozen (authorization claim: temp/final `docs/v0.3/evidence/ETB_AUTHORIZATION_USE.claim.tmp` /
`.claim` with `devrelay-etb-authorization-use-v1`; ETB attempt claim: temp/final
`docs/v0.3/evidence/ETB_ATTEMPT_USE.claim.tmp` / `.claim` with `devrelay-etb-attempt-use-v1`; both bound to
the independently accepted authorization commit/SHA and to oracle `1c6c7cd` / `01675fa7…`), with writer
failure semantics frozen per claim (pre-existing temp or final ⇒ already CONSUMED ⇒ STOP without invoking
the writer; any later writer exception ⇒ remains CONSUMED, `AUTHORIZATION_CONTROL_FAILURE` for the
authorization claim with ETB not started, and for the ETB claim no ETB semantic result if the oracle was not
entered; no cleanup, no retry, no alternate writer, no second attempt).  **P2 — durability narrowing:** the
supported guarantee is now explicitly **PROCESS-CRASH RECOVERY** only — "if the PowerShell/executor process
terminates after successful OS-visible exclusive creation of a claim temp file, the next executor is
required to interpret TEMP or FINAL presence as CONSUMED and fail closed" — with an explicit non-claim
("THIS AUTHORIZATION DOES NOT CLAIM POWER-LOSS DURABILITY OR MACHINE-CRASH DURABILITY FOR CLAIM DIRECTORY
METADATA"), `Flush(true)` described as **file-content** flushing only, no parent-directory fsync guarantee,
and no guarantee for sudden power loss between filesystem metadata operations; unbounded
"durable/durably/durability" wording for claim markers was replaced with process-crash-recovery terminology
("process-crash recovery consumption boundary", "process-crash-persistent one-shot marker",
"filesystem-presence one-shot witness") without changing the logical state machine.  **P3-1 — tracking
policy:** the four claim paths are declared intended **untracked operational control-state artifacts**,
**not** part of the tracked-worktree-clean predicate, whose presence is expected after operational
authorization use; they MUST NOT be `git add`ed, staged, committed, deleted, renamed, archived or
normalized before independent ETB-result review; bookkeeping commits before that review MUST use an exact
allowlist of intended tracked documentation files and MUST exclude the markers; `.gitignore` must not be
modified; "**tracked worktree clean**" is frozen to mean *no tracked-file modification outside the
explicitly authorized operational changes* (not a globally empty `git status --porcelain`), and future
reports must list expected untracked operational artifacts separately rather than classifying the expected
markers as worktree drift; if a marker is found staged → STOP without auto-unstaging/deleting, and if found
committed unexpectedly → STOP without rewriting history, both reported for independent review, with the
presence semantics remaining fail-closed regardless of Git tracking state.  **P3-2 — restored invariant:**
the explicit rule is restored verbatim — the authorization layer MUST NOT pre-check, pre-interpret, delete,
repair or otherwise act on the accepted oracle's six frozen temp/final ETB output paths; only after
configuration establishment succeeds, `CONFIG_ESTABLISHMENT.json` succeeds and the ETB claim is
consumed/finalized does execution enter the accepted frozen oracle from its FIRST STEP, and the oracle
alone performs its own six-path output-preexistence validation inside the already-consumed ETB attempt.
Preserved semantically unchanged: the byte-exact config mutation (`PRE_CONFIG_SHA256 = daaf7257…` / 1876 →
`POST_CONFIG_SHA256 = b5e4abab…` / 1897 through the unique 24-byte span), the Python `xb`/`fsync`/`os.replace`
config writer and read-back, config no-rollback, the `devrelay-etb-config-establishment-v1`
path/schema/serialization, the exact `Directory.CreateDirectory` directory create/verify rule (still
CLOSED), the four-row state machine and TEMP-or-FINAL-means-consumed rule with no parser success required,
claim non-deletion, the future claim-namespace rule, the ETB attempt boundary, oracle provenance and the
owner tuple, and Mode-B/G0.5/implementation preservation.  Current status:
`ETB EXECUTION / CONFIGURATION AUTHORIZATION = ROUND-4 CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT
EXECUTED`; no operational authorization is granted, no claim is created now, no directory is created now,
no config is changed now and no ETB is executed now.  This remediation round performed **0** web/network
access, **0** endpoint queries, **0** `Get-NetTCPConnection` executions, **0** live `Get-CimInstance`
queries, **0** port/listener/process enumeration, **0** config mutations, **0** OpenCode starts, **0** HTTP,
**0** `/doc`, **0** `/session`, **0** `Add-Type` executions, **0** P/Invoke executions, **0**
execution-evidence publications, **0** ETB executions, **0** SIC attempts, **0** Mode-B work, **0**
provider/model calls, **0** G0.5 and **0** G1/G2 activity, and **0** runtime/test/dependency/version
changes; the tracked worktree is clean and the ignored/untracked `PROJECT_MEMORY.md` persists.

**The ETB execution/configuration authorization Round-4 candidate was rejected by independent review, and
a round-5 claim-path type semantic closure candidate now exists (still a candidate: not accepted, not
effective, not executed).**  The independent review issued *REQUEST_CHANGES — V0.3-E ETB EXECUTION /
CONFIGURATION AUTHORIZATION ROUND-4* (**P0 = 0, P1 = 0, P2 = 1, P3 = 2**) against
`008115d6988c76d3c4ce185f73d047d44f5d8579` (artifact blob
`dfe673e6ff961a7bdb324912ea541008d2ade98a5789b9bfc1581efe7f54bc10`); its **only blocking finding** was
`CLAIM_PATH_TYPE_SEMANTICS = OPEN` — the recovery/state-machine text treated TEMP or FINAL "presence" as
consumed while the exact writer checked only `[System.IO.File]::Exists(path)`, and `File.Exists` returns
false when the exact path is occupied by a directory, so a directory at a claim path was classified
differently by the state machine and by the writer (no authorization-reuse or ETB hazard was demonstrated,
but the classification was not deterministic).  The candidate **remains rejected** and unamended, as do
`c106b2d` (P0 = 0, P1 = 1, P2 = 1, P3 = 2), `390eda1` (P0 = 0, P1 = 1, P2 = 0, P3 = 2) and `f52cb2b`
(P0 = 0, P1 = 2, P2 = 2); the last authoritative pre-authorization baseline remains `d058b38`.
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_AUTHORIZATION.md` was revised **in place** (no second authorization
artifact) as a self-contained round-5 remediation candidate that closes exactly that finding and redesigns
nothing else.  **One exact path-occupancy predicate is now frozen**: `CLAIM_PATH_OCCUPIED(path) :=
[System.IO.File]::Exists(path) -or [System.IO.Directory]::Exists(path)`, with `CLAIM PATH ABSENT :=
File.Exists(path) == false AND Directory.Exists(path) == false`, applied **identically** to the
authorization claim TEMP, the authorization claim FINAL, the ETB-attempt claim TEMP and the ETB-attempt
claim FINAL, and no other meaning of "present", "exists" or "occupied" is permitted for claim-path state.
A **directory at any claim TEMP/FINAL path is OCCUPIED**: for the authorization claim that means
AUTHORIZATION CONSUMED → STOP → the writer MUST NOT proceed to `CreateNew` → no cleanup, no deletion, no
rename, no retry → independent review required before any future action; for the ETB-attempt claim it means
ETB ATTEMPT CONSUMED → STOP → no rerun → the writer MUST NOT proceed to `CreateNew` → no cleanup, no
deletion, no rename.  The artifact explicitly forbids trying to determine whether such a directory is
legitimate claim content — **occupancy alone is fail-closed** — and states that a partial claim file, a
zero-length claim file, a malformed claim file and a claim directory all count as OCCUPIED whenever the
predicate is true, with no parsing required and no repair authorized.  The **frozen writer source was
modified in place** (not replaced or redesigned) at exactly its three path checks — the initial TEMP
pre-check, the initial FINAL pre-check and the pre-`Move` FINAL re-check — to the multi-line
`File.Exists(...) -or Directory.Exists(...)` form (the function is otherwise byte-identical: same
`[ordered]` claim object, `ConvertTo-Json -Depth 4 -Compress`, real PowerShell LF, `UTF8Encoding(false)`,
`FileStream`/`FileMode.CreateNew`/`FileAccess.Write`/`FileShare.None`, single `Write(bytes,0,len)`,
`Flush(true)`, `Dispose()`, `ReadAllBytes` byte-by-byte verification, and the two-argument
`System.IO.File.Move`; the three `throw` lines are unchanged, and a mechanical reconstruction from the
Round-4 source applying only those three authorized replacements reproduces the new source exactly).  The
`FileMode.CreateNew` **consumption boundary is preserved for a previously ABSENT path**, while an OCCUPIED
temp path is now classified CONSUMED by fail-closed occupancy semantics and the writer must not attempt
`CreateNew` — so the directory-at-TEMP corner is never interpreted as UNUSED; the directory-at-FINAL
corners are covered both before invocation (FINAL OCCUPIED → already CONSUMED → STOP before `CreateNew`)
and after TEMP creation but before publication (the second frozen FINAL occupancy check throws
`DEVRELAY_CLAIM_FINAL_APPEARED`, the claim remains CONSUMED, and **no `File.Move` attempt is made**).  The
**recovery table is restated in OCCUPIED/ABSENT terms only** (both ABSENT → AUTHORIZATION UNUSED; auth
TEMP/FINAL OCCUPIED + ETB both ABSENT → AUTHORIZATION CONSUMED / ETB NOT STARTED; both OCCUPIED →
AUTHORIZATION CONSUMED / ETB ATTEMPT CONSUMED; auth both ABSENT + ETB TEMP/FINAL OCCUPIED → CONTROL-STATE
INCONSISTENCY / FAIL CLOSED / NO EXECUTION / INDEPENDENT REVIEW REQUIRED), with no undefined generic notion
of presence and no parser success required.  A **wording-only root binding** was added: future operational
execution MUST run with the repository root as its working directory before any relative frozen
claim/config/evidence path is evaluated, and all relative paths in this authorization are
repository-root-relative — no other root-resolution mechanism is introduced (the already accepted
root-binding verdict is not reopened).  Preserved semantically unchanged: the Round-3 claim-writer closure
and its PowerShell/.NET-only language, the process-crash-only recovery model with its explicit non-claim of
power-loss/machine-crash durability for claim directory metadata, the claim tracking/commit policy and the
frozen "tracked worktree clean" semantics, the future claim-namespace rule, claim non-deletion, the exact
`Directory.CreateDirectory` directory create/verify rule, the byte-exact config mutation
(`PRE_CONFIG_SHA256 = daaf7257…` / 1876 → `POST_CONFIG_SHA256 = b5e4abab…` / 1897), the
`devrelay-etb-config-establishment-v1` path/schema/serialization, both 1-of-1 budgets, the restored
output-precheck invariant (the authorization layer MUST NOT pre-check, pre-interpret, delete, repair or
otherwise act on the accepted oracle's six frozen temp/final ETB output paths — only the frozen oracle
checks them inside the consumed ETB attempt), the owner tuple, oracle provenance and Mode-B/G0.5
preservation.  Current status: `ETB EXECUTION / CONFIGURATION AUTHORIZATION = ROUND-5 CANDIDATE / NOT
ACCEPTED / NOT EFFECTIVE / NOT EXECUTED`; no authorization is granted, no claim is created, no directory is
created, no config mutation occurs and no ETB is executed.  This remediation round performed **0**
web/network access, **0** endpoint queries, **0** `Get-NetTCPConnection` executions, **0** live
`Get-CimInstance` queries, **0** port/listener/process enumeration, **0** config mutations, **0** OpenCode
starts, **0** HTTP, **0** `/doc`, **0** `/session`, **0** `Add-Type` executions, **0** P/Invoke executions,
**0** execution-evidence publications, **0** ETB executions, **0** SIC attempts, **0** Mode-B work, **0**
provider/model calls, **0** G0.5 and **0** G1/G2 activity, and **0** runtime/test/dependency/version
changes; the tracked worktree is clean and the ignored/untracked `PROJECT_MEMORY.md` persists.

**(Historical round entry — superseded by the `AUTHORIZATION_CONTROL_FAILURE` entry below, which records that
this authorization was subsequently consumed and is now SPENT / NOT REUSABLE.)**  The ETB
execution/configuration authorization is now INDEPENDENTLY ACCEPTED / GRANTED (Round 5), while no
operational action has occurred yet: authorization use UNUSED, ETB attempt NOT STARTED, `opencode.base_url`
still `""`.  The independent review — not executor self-approval — returned **APPROVE V0.3-E ETB
EXECUTION / CONFIGURATION AUTHORIZATION ROUND-5** with **P0 = 0, P1 = 0, P2 = 0, P3 = 2**, explicitly
closing `P1_A_CONFIG_MUTATION`, `P1_B_AUTHORIZATION_REUSE`, `P2_A_OUTPUT_TIMING`, `P2_B_CONFIG_EVIDENCE`,
`ROUND2_P1_DIRECTORY_RULE`, `ROUND3_P1_CLAIM_WRITER`, `ROUND3_P2_DURABILITY`, `ROUND3_P3_TRACKING_POLICY`,
`ROUND3_P3_OUTPUT_PRECHECK_EXPLICITNESS`, `CLAIM_PATH_ROOT_BINDING` and `CLAIM_PATH_TYPE_SEMANTICS`; the
authorization design phase is complete.  The approval binds **exactly** `authorization_commit =
64044fc45082cd63b0ae445c146d85720dfa1435` and `authorization_sha256 =
511ab1e2eb2e4f1194d2c55951e5b9616dc515d1180c6399dd658207d443d0d8` for the immutable artifact
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_AUTHORIZATION.md`.  **Permanent authorization provenance rule:** this
pair is immutable and must not be replaced by this acceptance-bookkeeping commit, by any later operational,
evidence or result-review bookkeeping commit, or by the execution-time HEAD; future authorization-claim
content and all operational provenance referencing this authorization must reference exactly this pair, and
**the bookkeeping commit produced by this round is NOT `authorization_commit`**.  The accepted authorization
identity and the accepted oracle identity remain **distinct** immutable provenance pairs — `oracle_commit =
1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc` / `oracle_sha256 =
01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921` (`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md`) —
and neither may replace the other.  **Current authoritative authorization status:**
`ETB EXECUTION / CONFIGURATION AUTHORIZATION = ACCEPTED / GRANTED / NOT EXECUTED / AUTHORIZATION USE UNUSED /
ETB ATTEMPT NOT STARTED`.  The accepted artifact remains an **immutable accepted object** whose
construction-time header still reads ROUND-5 CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT EXECUTED — exactly
the established immutable-artifact + approval-record + active-status pattern used for the accepted frozen ETB
oracle candidate — so the artifact was **not** edited by this bookkeeping; current status is represented only
by this CHANGELOG and by `docs/v0.3/V03E_ACCEPTANCE.md`.  **Current claim state (authoritative, verified):**
`AUTHORIZATION CLAIM TEMP = ABSENT`, `AUTHORIZATION CLAIM FINAL = ABSENT`, `ETB ATTEMPT CLAIM TEMP = ABSENT`,
`ETB ATTEMPT CLAIM FINAL = ABSENT`, therefore `AUTHORIZATION USE = UNUSED` and `ETB ATTEMPT = NOT STARTED`;
no claim has been created and no authorization has yet been operationally consumed.  **Current configuration
state:** owner-authorized endpoint `http://127.0.0.1:4096`; currently configured endpoint **NONE**;
`.devrelay/config.yaml` → `opencode.base_url = ""` with `PRE_CONFIG_SHA256 =
daaf72578cb4a91b5adeb481530baf47577174325167caddf7249964da7923a8` and `PRE_CONFIG_SIZE = 1876`; no config
mutation has occurred and none is performed by this bookkeeping.  **Future authorized configuration
mutation (not performed now):** the accepted authorization permits, only in the later operational execution
round, the exact already-frozen transition `opencode.base_url` from `""` to `http://127.0.0.1:4096` under the
byte-exact configuration procedure frozen in the accepted artifact.  **One-shot scope (referencing the
immutable artifact rather than reproducing it):** mode **MODE P — PRE-EXISTING TARGET**; endpoint policy
**CLASS A — OWNER-SUPPLIED FIXED ENDPOINT**; endpoint `http://127.0.0.1:4096`; fallback **NONE**;
authorization-use budget **1 of 1**; ETB-attempt budget **1 of 1**; OpenCode start/restart **NOT AUTHORIZED**;
HTTP **NOT AUTHORIZED**; Mode-B work in the operational ETB round **NOT AUTHORIZED**.  The accepted claim
model is summarised at status level only and is **not** strengthened: process-crash-only claim model,
filesystem-node occupancy predicate, exact PowerShell/.NET claim writer, repository-root path binding,
untracked claim-marker policy and distinct future namespace requirement — **no power-loss durability is
claimed**.  **Historical rejections preserved (not rewritten):** `f52cb2b` REQUEST_CHANGES (P0 = 0, P1 = 2,
P2 = 2); `390eda1` REQUEST_CHANGES ROUND-2 (P0 = 0, P1 = 1, P2 = 0, P3 = 2); `c106b2d` REQUEST_CHANGES
ROUND-3 (P0 = 0, P1 = 1, P2 = 1, P3 = 2); `008115d` REQUEST_CHANGES ROUND-4 (P0 = 0, P1 = 0, P2 = 1,
P3 = 2); then `64044fc` **APPROVE ROUND-5** (P0 = 0, P1 = 0, P2 = 0, P3 = 2).  The two Round-5 P3 findings
are recorded as **non-blocking only**: P3-1, an executor chat/report rendering loss of the PowerShell
backtick while the actual committed artifact was independently verified correct; P3-2, a small
mechanical-strengthening note around the repository-root/CWD binding whose actual binding was independently
accepted as CLOSED — **neither is an unresolved authorization blocker**.  **Mode-B is not unblocked** by this
approval: it remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED /
PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`, because configuration establishment has not
occurred, ETB has not executed, and `ETB_SATISFIED` has not been independently reviewed or accepted.
`G0.5 / P6` remains `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP` with
`P6 = UNPROVEN / UNSATISFIED` and G0.5 **NOT CLOSED** — authorization approval is **not** P6 evidence.
Case-C implementation `NOT AUTHORIZED`; v0.3-E implementation `NOT AUTHORIZED`; `G1 = NOT RUN`; `G2 = NOT
RUN`; `adopt_completed_turn` **DISABLED**.  **Authoritative sequence:** ETB definition accepted → capability
prerequisites accepted → owner mode/endpoint decision accepted → frozen ETB execution oracle independently
accepted → oracle acceptance bookkeeping independently accepted → execution/configuration authorization
designed → authorization Round-1 rejected → Round-2 rejected → Round-3 rejected → Round-4 rejected → Round-5
independently approved → **authorization acceptance bookkeeping (this round)** → independent bookkeeping
confirmation → exactly one operational authorization use → exact configuration establishment → exactly one
ETB attempt → independent ETB-result review → only an independently accepted `ETB_SATISFIED` may permit
Mode-B SIC oracle construction to resume; no stage may be skipped.  **Next stage classification:** after this
acceptance bookkeeping is independently confirmed, the next stage may be the **ETB EXECUTION / CONFIGURATION
OPERATIONAL ROUND** under exactly `authorization_commit = 64044fc…` / `authorization_sha256 = 511ab1e2…`
plus `oracle_commit = 1c6c7cd…` / `oracle_sha256 = 01675fa7…` — but **this bookkeeping round does not begin
that operational round**.  This bookkeeping round performed **0** web/network access, **0** endpoint queries,
**0** `Get-NetTCPConnection` executions, **0** live `Get-CimInstance` queries, **0** port/listener/process
enumeration, **0** config mutations, **0** claim creations, **0** claim-path directory creations, **0**
`etb-execution` directory creations, **0** OpenCode starts/restarts, **0** HTTP, **0** `/doc`, **0**
`/session`, **0** `Add-Type` executions, **0** P/Invoke executions, **0** `CONFIG_ESTABLISHMENT`
publications, **0** ETB evidence publications, **0** ETB executions, **0** SIC attempts, **0** Mode-B work,
**0** provider/model calls, **0** G0.5 and **0** G1/G2 activity, and **0** runtime/test/dependency/version
changes; the tracked worktree is clean and the ignored/untracked `PROJECT_MEMORY.md` persists.

**(Historical round entry — superseded by the Recovery-R1 acceptance entry below, which records that this
candidate was subsequently independently APPROVED and is now ACCEPTED / GRANTED / USE UNUSED.)**  The one-shot
ETB operational round was executed, consumed the accepted authorization exactly once, and
ended in `AUTHORIZATION_CONTROL_FAILURE`; a separate Recovery-R1 control-state recovery authorization
candidate now exists (not accepted, not effective, not executed).  What actually happened: the
pre-authorization prerequisites all passed; the authorization claim was created with the artifact's exact
frozen `Write-DevRelayOneShotClaim` writer, so `AUTHORIZATION_USE` became **1/1 CONSUMED** at the successful
`FileMode.CreateNew` of `docs/v0.3/evidence/ETB_AUTHORIZATION_USE.claim.tmp` and the published claim
(`docs/v0.3/evidence/ETB_AUTHORIZATION_USE.claim`, 372 bytes, SHA-256
`d84b428586f07a55a99f5b1391481d77763ec4ea697a40d1cec8aa0779613d4e`) carries the exact ordered schema with
`state = CONSUMED`; `docs/v0.3/evidence/etb-execution` was created exactly via
`[System.IO.Directory]::CreateDirectory`; the **exact frozen byte-level configuration transition completed
and verified** (pre-image `daaf7257…` / 1876 → post-image `b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf` / 1897 via
the unique 24-byte span, `xb` exclusive-create + write + flush + `os.fsync` + close + read-back +
`os.replace` + read-back, with the production reader resolving `""` before and
`http://127.0.0.1:4096` after); then the `CONFIG_ESTABLISHMENT.json` publication invocation **aborted
before entering any frozen primitive** because of **executor nonconformance** — an executor-authored,
non-frozen pre-write assertion miscompared the *current* (post-mutation) config hash against the *preimage*
hash and threw `PRE_SHA_NOT_PREIMAGE`.  No serialization ran, no temp was created, no bytes were written and
no move was attempted, so there is **no partial output** and the evidence directory is empty; per the frozen
rules (config-evidence "any failure → `AUTHORIZATION_CONTROL_FAILURE` / ETB NOT STARTED" plus §33.2
"post-authorization-claim failure … STOP, new authorization required, no reuse" and §12.2 "no
preparation-retry loophole exists") the invocation was **not retried**.  Final state of that round:
`AUTHORIZATION_CONTROL_FAILURE`; original authorization **SPENT / NOT REUSABLE**; `AUTHORIZATION USE = 1/1
CONSUMED`; original `ETB ATTEMPT = 0/1 NOT STARTED` (no `ETB_ATTEMPT_USE.claim` / `.tmp` was ever created);
**no ETB semantic result exists**; config left at the exact frozen post-image (**no rollback**); original
`CONFIG_ESTABLISHMENT = MISSING`; frozen oracle **NEVER ENTERED** (no `Get-NetTCPConnection`,
`Get-CimInstance`, `Add-Type`, P/Invoke, HTTP, `/doc`, `/session`, OpenCode start or ETB execution); no
commit was created (HEAD remained `14c5343`).  The independent control-failure review returned *CONFIRM
AUTHORIZATION_CONTROL_FAILURE STATE — NEW AUTHORIZATION REQUIRED* (**P0 = 0, P1 = 1, P2 = 0, P3 = 1**) and
separately concluded `STATE_MACHINE_FINAL_STATE = VALID`, `EXECUTION_PROCEDURE_FIDELITY = NONCONFORMANT`,
`CONFIG_EVIDENCE_SCHEMA = SOUND`, `FAILURE_CAUSE = EXECUTOR_NONCONFORMANCE`,
`ORIGINAL_AUTHORIZATION_REUSABLE = NO`, `CONFIG_MUTATION_REPLAY_ALLOWED = NO`.  A **new** artifact
`docs/v0.3/V03E_G0_5_PRE_ETB_RECOVERY_AUTHORIZATION.md` (not a revision — the accepted original
authorization artifact remains immutable) now records
`ETB CONTROL-STATE RECOVERY AUTHORIZATION = RECOVERY-R1 CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT
EXECUTED`: it is a **new authorization** with `recovery_authorization_commit` /
`recovery_authorization_sha256` to be bound only by a later independent approval, a **new and permanently
distinct claim namespace** (`ETB_RECOVERY_R1_AUTHORIZATION_USE.claim`(+`.tmp`) and
`ETB_RECOVERY_R1_ATTEMPT_USE.claim`(+`.tmp`)), the same frozen occupancy predicate
(`File.Exists` **or** `Directory.Exists`), a **byte-for-byte verbatim copy** of the accepted
`Write-DevRelayOneShotClaim` function (verified identical; the reviewer must diff the two functions), and
two separate 1-of-1 budgets whose consumption boundary is the successful `CreateNew` of the recovery
authorization claim temp.  Recovery **does not re-establish configuration**: it performs only read-only
verification of the existing post-image (`b5e4abab…` / 1897 / `http://127.0.0.1:4096`) and then
**recovers/publishes the missing original `CONFIG_ESTABLISHMENT.json`** as control evidence of the
transition that already occurred — so that file must retain the **original** authorization identity
(`64044fc…` / `511ab1e2…`), never the recovery identity, and the two provenance domains must not be
conflated.  The artifact reproduces the accepted `devrelay-etb-config-establishment-v1` schema as the exact
17 ordered fields with explicit values (no recovery-specific field, no added timestamp or comment), treats
`pre_config_sha256`/`expected_pre_config_sha256`/`pre_resolved_base_url` as **historical evidence inputs**
(`daaf7257…` / `daaf7257…` / `""`) that must **not** be validated against the current file, and freezes the
**absolute prohibition** on the `PRE_SHA_NOT_PREIMAGE` assertion and on any executor-authored pre-write
assertion, together with the exact `ConvertTo-Json -Depth 12 -Compress` / `UTF8Encoding(false)` / one-LF /
`CreateNew`+`Flush(true)`+read-back / two-argument `File.Move` publication rule and the rule that the
authorization/recovery layer must not touch the oracle's six frozen output paths.  Failure semantics are
frozen (`RECOVERY_AUTHORIZATION_CONTROL_FAILURE`, recovery use CONSUMED, recovery ETB attempt NOT STARTED,
no retry, no cleanup, no rollback, no original-claim deletion, a later Recovery-R2 would be required), as is
the boundary at which the one Recovery-R1 ETB attempt is consumed (successful `CreateNew` of the recovery
ETB claim temp, after successful `CONFIG_ESTABLISHMENT.json` publication) — which would be the **first
actual ETB attempt** — followed by entering the unchanged frozen oracle from its FIRST STEP.  Preserved
unchanged: `oracle_commit = 1c6c7cd…` / `oracle_sha256 = 01675fa7…` (recovery creates no new oracle); the
original spent claim and the empty `etb-execution` directory are never deleted or rewritten; the four new
recovery claim paths are untracked operational control-state artifacts; config is never rolled back to `""`;
Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE
CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER` (**the config now containing the endpoint does not
establish target binding**); `P6 = UNPROVEN / UNSATISFIED`; G0.5 **NOT CLOSED**; Case-C and v0.3-E
implementation `NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`; `adopt_completed_turn` **DISABLED**.  The current
authorization status is `ETB EXECUTION / CONFIGURATION AUTHORIZATION = SPENT / NOT REUSABLE / AUTHORIZATION
USE 1/1 CONSUMED / ETB ATTEMPT 0/1 NOT STARTED / ETB SEMANTIC RESULT NONE /
AUTHORIZATION_CONTROL_FAILURE`.  This Recovery-R1 design round performed **0** web/network access, **0**
endpoint queries, **0** `Get-NetTCPConnection` executions, **0** live `Get-CimInstance` queries, **0**
listener/process/port enumeration, **0** config mutations, **0** claim creations, **0** claim-path
directory creations, **0** `CONFIG_ESTABLISHMENT` publications, **0** OpenCode starts/restarts, **0** HTTP,
**0** `/doc`, **0** `/session`, **0** `Add-Type` executions, **0** P/Invoke executions, **0** ETB
executions, **0** SIC attempts, **0** Mode-B work, **0** provider/model calls, **0** G0.5 and **0** G1/G2
activity, and **0** runtime/test/dependency/version changes; the spent-authorization claim remains untracked
and unstaged, the git-ignored config remains uncommitted, and the ignored/untracked `PROJECT_MEMORY.md`
persists.

**The Recovery-R1 control-state recovery authorization has been INDEPENDENTLY ACCEPTED / GRANTED, while no
recovery action has occurred yet: recovery use UNUSED, recovery ETB attempt NOT STARTED, no Recovery-R1
claim, no `CONFIG_ESTABLISHMENT`, no oracle entry.**  The independent review — not executor self-approval —
returned **APPROVE V0.3-E ETB CONTROL-STATE RECOVERY AUTHORIZATION RECOVERY-R1** against
`3541c011cf92d9d66253989c5f576c2ad845ca33` (artifact
`docs/v0.3/V03E_G0_5_PRE_ETB_RECOVERY_AUTHORIZATION.md`, blob
`7fb1f28d427cc8c567491afc3137890f79b2bdb8bce88b4be2f63005824f3ab7`), confirming
`RECOVERY_CLAIM_WRITER = BYTE_IDENTICAL`, `CONFIG_MUTATION_REPLAY = FORBIDDEN`,
`CONFIG_ESTABLISHMENT_ATTESTATION = TRANSITION_FACT`, `DELAYED_PUBLICATION_PROVENANCE = SUFFICIENT`,
`CONTEMPORANEITY_SEMANTICS = TRUTHFUL`, and finding the design internally consistent, deterministic,
repository-self-sufficient, non-reusing of the spent original authorization and non-replaying of the
original config mutation, **with no blocking design finding**.  **Permanent Recovery-R1 provenance:**
`recovery_authorization_commit = 3541c011cf92d9d66253989c5f576c2ad845ca33` and
`recovery_authorization_sha256 = 7fb1f28d427cc8c567491afc3137890f79b2bdb8bce88b4be2f63005824f3ab7`; this
pair is immutable and must not be replaced by this acceptance-bookkeeping commit, by the Recovery-R1
operational HEAD, by an evidence commit, by a result-review bookkeeping commit or by any later HEAD — **the
bookkeeping commit created by this round is NOT `recovery_authorization_commit`**.  **Three distinct
immutable provenance domains now exist and none may replace another:** (A) the original
configuration-transition authorization `64044fc…` / `511ab1e2…` — preserved as `ORIGINAL ROUND-5
AUTHORIZATION = SPENT / NOT REUSABLE / AUTHORIZATION_CONTROL_FAILURE`, with Recovery-R1 never replacing or
reinterpreting it; (B) the Recovery-R1 publication/execution authorization `3541c01…` / `7fb1f28d…`; and
(C) the frozen ETB oracle `1c6c7cd…` / `01675fa7…`.  **Authoritative recovery status:**
`ETB CONTROL-STATE RECOVERY AUTHORIZATION = ACCEPTED / GRANTED / NOT EXECUTED / RECOVERY AUTHORIZATION USE
UNUSED / RECOVERY ETB ATTEMPT NOT STARTED`.  The accepted Recovery-R1 artifact remains an **immutable
accepted candidate object** whose construction-time header still reads RECOVERY-R1 CANDIDATE / NOT ACCEPTED
/ NOT EFFECTIVE / NOT EXECUTED — the established immutable-artifact + approval-record + active-status
pattern — so it was **not** edited by this bookkeeping; current status is represented only by this CHANGELOG
and `docs/v0.3/V03E_ACCEPTANCE.md`.  **Current filesystem/control state (verified):** original authorization
claim FINAL **OCCUPIED**, original authorization claim TEMP **ABSENT**, original ETB attempt claim TEMP and
FINAL **ABSENT**, and all four Recovery-R1 claim paths (`ETB_RECOVERY_R1_AUTHORIZATION_USE.claim`(+`.tmp`),
`ETB_RECOVERY_R1_ATTEMPT_USE.claim`(+`.tmp`)) **ABSENT** ⇒ `ORIGINAL AUTHORIZATION = SPENT`, `ORIGINAL ETB
ATTEMPT = 0/1 NOT STARTED`, `RECOVERY-R1 AUTHORIZATION USE = UNUSED`, `RECOVERY-R1 ETB ATTEMPT = NOT
STARTED`; no budget has yet been consumed.  **Current config state:** `opencode.base_url =
http://127.0.0.1:4096`, SHA-256 `b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf`, size
1897 — the exact frozen post-image (historical preimage `daaf7257…` / 1876 / `""` remains historical only);
config is not mutated by this round.  **`CONFIG_ESTABLISHMENT` state:** `docs/v0.3/evidence/etb-execution`
exists as a directory but is empty — `CONFIG_ESTABLISHMENT.json` and `.tmp` are ABSENT, therefore
`CONFIG_ESTABLISHMENT = MISSING`; the empty directory itself is not evidence publication.  **Recovery-R1
scope (by reference to the immutable artifact):** one Recovery-R1 authorization use → read-only
verification of the existing exact post-image → publication of the missing `CONFIG_ESTABLISHMENT` evidence
for the **original** configuration transition → one Recovery-R1 ETB attempt → entry into the unchanged
frozen ETB oracle.  Recovery-R1 must **not** mutate config, restore `""`, reapply the original config patch,
reuse the original authorization or its claim paths, start/restart OpenCode, perform HTTP, perform Mode-B
work or run G0.5.  **Delayed-publication provenance (independently accepted semantics):**
`CONFIG_ESTABLISHMENT_ATTESTATION = TRANSITION_FACT` — the recovered record describes the **original**
transition, so its embedded authorization provenance remains `64044fc…` / `511ab1e2…`, while Recovery-R1
authority to publish the delayed record is separately established by `3541c01…` / `7fb1f28d…` plus its
future Recovery-R1 claim; hence `DELAYED_PUBLICATION_PROVENANCE = SUFFICIENT` and
`CONTEMPORANEITY_SEMANTICS = TRUTHFUL`; this does **not** imply that the original authorization itself later
re-executes publication.  **Recovery-R1 namespace/budgets:** the four new claim paths are permanently
distinct (the original namespace stays reserved), and `RECOVERY_AUTHORIZATION_USE_BUDGET = 1/1` /
`RECOVERY_ETB_ATTEMPT_BUDGET = 1/1` are both unconsumed.  **Config replay prohibition:**
`CONFIG_MUTATION_REPLAY = FORBIDDEN` — Recovery-R1 operational execution may only verify the current
post-image SHA, size and resolved `base_url`, and must never restore `""`, re-run OLD→NEW, re-run the
original Python config writer, reuse the original config temp or perform `os.replace` on config.  **Original
control-failure history preserved (not erased by this approval):** *CONFIRM AUTHORIZATION_CONTROL_FAILURE
STATE — NEW AUTHORIZATION REQUIRED* (P0 = 0, P1 = 1, P2 = 0, P3 = 1) with
`STATE_MACHINE_FINAL_STATE = VALID`, `EXECUTION_PROCEDURE_FIDELITY = NONCONFORMANT`,
`CONFIG_EVIDENCE_SCHEMA = SOUND`, `FAILURE_CAUSE = EXECUTOR_NONCONFORMANCE`,
`ORIGINAL_AUTHORIZATION_REUSABLE = NO`, `CONFIG_MUTATION_REPLAY_ALLOWED = NO`.  **Preserved unchanged:**
Mode-B `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE
CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 **NOT CLOSED**;
Case-C and v0.3-E implementation `NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`; `adopt_completed_turn` **DISABLED**;
**Recovery-R1 approval is not target-binding evidence**.  **Next stage:** only after independent
confirmation of this Recovery-R1 acceptance bookkeeping may the next stage be the **RECOVERY-R1 OPERATIONAL
ROUND**, binding to exactly `3541c01…` / `7fb1f28d…` plus the original pair `64044fc…` / `511ab1e2…` and the
oracle pair `1c6c7cd…` / `01675fa7…`; **this bookkeeping round does not begin recovery**.  Authoritative
sequence: Round-5 authorization accepted → Round-5 acceptance bookkeeping accepted → original authorization
consumed → exact config mutation completed → `CONFIG_ESTABLISHMENT` publication failed due to executor
nonconformance → `AUTHORIZATION_CONTROL_FAILURE` → independent control-state review confirmed → original
authorization SPENT → Recovery-R1 design → **Recovery-R1 independently approved** → **Recovery-R1
acceptance bookkeeping (this round)** → independent Recovery-R1 bookkeeping confirmation → one Recovery-R1
authorization use → verify the exact existing post-image → recover/publish the missing
`CONFIG_ESTABLISHMENT` → consume one Recovery-R1 ETB attempt → frozen oracle once → independent ETB-result
review → only an independently accepted `ETB_SATISFIED` may permit Mode-B construction; no stage is skipped.
This bookkeeping round performed **0** config mutations, **0** claim creations, **0** claim deletions, **0**
`CONFIG_ESTABLISHMENT` publications, **0** endpoint queries, **0** listener/process enumerations, **0**
OpenCode starts/restarts, **0** HTTP, **0** ETB, **0** SIC, **0** Mode-B work, **0** G0.5, **0** G1/G2
activity and **0** runtime/test/dependency/version changes; the spent-authorization claim remains untracked
and unstaged, the git-ignored config remains uncommitted, and the ignored/untracked `PROJECT_MEMORY.md`
persists.

**The Recovery-R1 published candidate ETB result was REJECTED by independent review, and a new ETB
execution oracle R2 (execution-fidelity / output-namespace closure) design candidate now exists — still a
candidate: not accepted, not frozen, not executed.**  The independent final decision was **REJECT
RECOVERY-R1 PUBLISHED ETB RESULT — NO AUTHORITATIVE ETB SEMANTIC RESULT** (**P0 = 0, P1 = 1, P2 = 1,
P3 = 2**) with `RECOVERY_CONTROL_STATE = VALID`, `CONFIG_ESTABLISHMENT_RECOVERY = VALID`,
`ORACLE_IMPLEMENTATION_FIDELITY = NONCONFORMANT / INDETERMINATE`, `BLANKET_CATCH_CLASSIFICATION =
NONCONFORMANT`, `MANDATORY_STOP_FIDELITY = NONCONFORMANT`, `RESULT_ENCODING_FIDELITY = NONCONFORMANT`,
`RESULT_ARTIFACT_VALIDITY = VALID_WITH_NONBLOCKING_TEXT_DEFECT`, `PUBLISHED_RESULT_CLASSIFICATION =
UNRESOLVABLE`, `FROZEN_TAXONOMY_RESULT = INDETERMINATE DUE TO EXECUTION NONCONFORMANCE`,
`INDEPENDENT_RECLASSIFICATION_PERMITTED = NO` and `NEW_ETB_AUTHORIZATION_REQUIRED = YES`.  Therefore
`RECOVERY-R1 AUTHORIZATION = SPENT / NOT REUSABLE`, `RECOVERY-R1 ETB ATTEMPT = SPENT / NOT REUSABLE`,
`RECOVERY-R1 PUBLISHED ETB RESULT = REJECTED`, `AUTHORITATIVE ETB SEMANTIC RESULT = NONE`; the rejected
candidate is **not** relabelled as `ETB_UNSATISFIED`, as an authoritative `HARNESS_INVALID` or as
`ETB_SATISFIED`, and no independent reclassification is permitted.  Two blockers are recorded for why the
original oracle cannot simply be re-run: **(A) output namespace occupied** — the immutable Recovery-R1 finals
`docs/v0.3/evidence/etb-execution/ETB_EVIDENCE.json`, `…/MANIFEST.sha256` and
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT.md` are present, and the original oracle requires all six of its
output paths absent before a consumed attempt proceeds; **(B) executable implementation not frozen** — the
Recovery-R1 execution script was not preserved, so its actual executable bytes could not be compared against
the accepted oracle and a blanket catch materially changed classification.  This round therefore freezes a
**new oracle as two tracked artifacts**: the specification
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.md` and the **normative tracked executable**
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1`.  The script is **ASCII-only** (every byte ≤ `0x7F`,
mechanically verified; no BOM, LF only) and constructs the result template's em dash at runtime as
`$EmDash = [char]0x2014`, serialized through `[System.Text.UTF8Encoding]::new($false)` so the result artifact
carries the exact UTF-8 bytes `E2 80 94`, with a pre-publication byte check for those three bytes — this
eliminates the PowerShell-5.1 source-decoding ambiguity that corrupted the previous result artifact's first
line.  The listener taxonomy is now explicit and mechanically distinct in both the spec and the script:
`COMMAND_UNAVAILABLE` (cmdlet/module genuinely unavailable, decided by an explicit
`Get-Command -ErrorAction SilentlyContinue` availability branch **before** the query) → `HARNESS_INVALID`;
`QUERY_EXCEPTION`, `ZERO_ROWS`, `MULTIPLE_ROWS` and `FIELD_OR_PID_INVALID` → `ETB_UNSATISFIED`;
`ONE_VALID_ROW` → continue the target-binding chain; `NOT_REACHED` only before the listener stage or after an
earlier frozen terminal condition.  The exact listener query
(`@(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 4096 -State Listen -ErrorAction SilentlyContinue
-ErrorVariable qerr)`) has its own **narrow** try/catch, and a no-match condition surfaced as a terminating
exception is classified `ETB_UNSATISFIED`, never `HARNESS_INVALID`; **no blanket or outer catch may map
snapshot/listener exceptions to `HARNESS_INVALID`** — the only remaining catches are the narrow, typed ones
frozen by the original taxonomy (native invocation / `CloseHandle` false / `Add-Type` load /
config-reader failure → `HARNESS_INVALID`; process query, package manifest, hash read → `ETB_UNSATISFIED`),
plus a delimited evidence-publication stage that contains **no** listener, process, canonicalization, hash or
package logic.  The evidence schema keeps every accepted field and adds exactly **one** audit field,
`listener_probe_outcome`, placed between `checks` and `outcome`, whose value is bound to the published
semantic outcome by the frozen mapping (and re-verified on read-back, so a mismatch surfaces as the frozen
evidence-machinery `HARNESS_INVALID` rather than being executor-selectable); unobserved snapshot fields
remain truthful placeholders (`""` / `0`).  The output namespace is **new and disjoint**: evidence
`docs/v0.3/evidence/etb-execution-r2/ETB_EVIDENCE.json` (+`.tmp`), manifest
`docs/v0.3/evidence/etb-execution-r2/MANIFEST.sha256` (+`.tmp`) and result
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_R2.md` (+`.tmp`), all six required absent before publication
work (file **or** directory occupancy fails closed), with the old Recovery-R1 paths neither reused nor
inspected; publication order stays evidence → manifest → result **last** with the two-argument
`File.Move` and read-back verification, and the manifest covers only the R2 evidence file.  The executable
terminates immediately after final publication and verification — **no post-result `Get-Command`,
`Get-NetTCPConnection`, `Get-CimInstance`, endpoint/listener/process probe, diagnostic, repair,
reclassification or extra evidence collection**.  Identity model: after independent acceptance,
`oracle_r2_commit` (the accepted commit containing both files), `oracle_r2_script_sha256` and
`oracle_r2_spec_sha256` are immutable and must be bound by the future Recovery-R2 authorization; the
executor must run the tracked `.ps1` directly (no extraction from Markdown, no temporary script, no
translation, no wrapper, no injected assertions) via the frozen invocation
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File "docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1"`.
Static validation performed in this design round: **parser-only** syntax validation of the tracked script
(PowerShell AST parser: **0 parse errors**, 4638 tokens), an ASCII-byte sweep (**0 non-ASCII bytes**), a
structural audit of every `catch`/`throw`/`HARNESS_INVALID`/`ETB_UNSATISFIED` branch, and hash computation —
**the operational main path was not executed, no listener/process command was run and the endpoint was not
contacted**.  Current statuses: `ETB EXECUTION ORACLE-R2 = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT
EXECUTED`; `RECOVERY-R1 AUTHORIZATION = SPENT / NOT REUSABLE`; `RECOVERY-R1 ETB ATTEMPT = SPENT / NOT
REUSABLE`; `RECOVERY-R1 PUBLISHED ETB RESULT = REJECTED`; `AUTHORITATIVE ETB SEMANTIC RESULT = NONE`;
`NEW_ETB_AUTHORIZATION_REQUIRED = YES`.  No Recovery-R2 authorization and no Recovery-R2 claim namespace
exist; config remains the exact post-image (`b5e4abab…` / 1897 / `http://127.0.0.1:4096`) and
`CONFIG_ESTABLISHMENT = VALID / PRESENT`; the Recovery-R1 evidence/result artifacts and all claims remain
untouched historical artifacts; Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE
ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`; `P6 = UNPROVEN /
UNSATISFIED`; G0.5 **NOT CLOSED**; Case-C and v0.3-E implementation `NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`;
`adopt_completed_turn` **DISABLED**.  This design round performed **0** config mutations, **0** claim
creations, **0** R2 directory or output creations, **0** Oracle-R2 executions, **0** old-oracle executions,
**0** endpoint queries, **0** `Get-NetTCPConnection` listener queries, **0** live `Get-CimInstance` queries,
**0** listener/process/port enumeration, **0** P/Invoke executions, **0** OpenCode starts/restarts, **0**
HTTP, **0** ETB executions, **0** SIC, **0** Mode-B work, **0** G0.5 and **0** G1/G2 activity, and **0**
runtime/test/dependency/version changes; the ignored/untracked `PROJECT_MEMORY.md` persists.

**The Oracle-R2 candidate `6d252a9` received `REQUEST_CHANGES` and was superseded by a narrow corrective
design round.**  The independent review issued *REQUEST_CHANGES — V0.3-E ETB EXECUTION ORACLE-R2* with
severity **P0 = 0, P1 = 1, P2 = 2, P3 = 5**, so that candidate was never accepted, never frozen and never
executed; it remains historical and is not relabelled as any semantic ETB result.  One blocking P1 was found —
**config-reader invocation fidelity**: the frozen oracle requires the config-reader subprocess to run with
`PYTHONPATH=<repo>/src`, and the rejected script invoked `python -c ... 'D:\DevRelay'` with no `PYTHONPATH`
established, which in a src-layout/non-installed environment could manufacture an artificial import failure
and turn a reachable result into `config_reader_failure` → `HARNESS_INVALID`, materially changing reachable
oracle behaviour.  Two blocking P2s were found: **evidence schema identity ambiguity** (the 16-field Oracle-R2
contract added `listener_probe_outcome` while retaining the closed original identifier `devrelay-etb-v1`) and
an **executable byte-identity design deadlock** (the accepted script blob is the 28024-byte LF sequence
`3e2cc721…`, while the canonical worktree under `* text=auto` with `core.autocrlf=true` materializes
28564-byte CRLF bytes `245e346c…`, and the rejected candidate froze no deterministic mechanism that lets a
canonical checkout contain the accepted executable bytes, so the accepted sequence would deterministically
deadlock before a Recovery-R2 authorization could be consumed).  Five P3s were closed as well.

**The corrective design round changed exactly five tracked paths** (`.gitattributes`, `CHANGELOG.md`,
`docs/v0.3/V03E_ACCEPTANCE.md`, `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.md`,
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1`) and no sixth tracked path.  **P1 remediation:** the
tracked script now deterministically establishes `PYTHONPATH = <repo>/src` for the config-reader subprocess —
capturing any prior process-level `PYTHONPATH` first, assigning exactly `<repo>/src` (never merged with,
prepended to or appended to pre-existing content), invoking the byte-identical frozen reader source with the
frozen repository root as its single repository argument, and restoring the prior state in a deterministic
`finally` block (restoring **absence**, not an invented empty value, when no prior `PYTHONPATH` existed) — so
the subprocess semantics are exactly equivalent to the original frozen oracle's
`PYTHONPATH=<repo>/src python -c "<frozen reader>" "<repo>"` shape.  The hard-coded `D:\DevRelay` is gone: the
frozen repository root is derived from the tracked script location, and config-reader stderr stays suppressed
and never participates in classification (classification depends only on the frozen subprocess exit code and
the returned reader value).  **P2-A remediation:** the Oracle-R2 evidence contract has the distinct identity
**`devrelay-etb-v1-r2`** (written and asserted on read-back), while `devrelay-etb-v1` remains only the
historical original closed schema of the Recovery-R1 evidence and is never reinterpreted.  **P2-B
remediation:** `.gitattributes` gains exactly **one** narrow rule —
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1 text eol=lf` (no repository-wide `*.ps1` rule, no other
text policy changed, `core.autocrlf` untouched), so a normal canonical checkout materializes the normative
executable as LF bytes independently of the local `core.autocrlf=true`, `git check-attr` resolves to
`text: set` / `eol: lf`, and the worktree bytes equal the committed blob bytes byte for byte — the accepted
fail-closed byte-identity gate is preserved unchanged and **no future ad-hoc repair stage is frozen**.  **P3
remediations:** `listener_probe_outcome` now has frozen total S0/S1 semantics (the published value is the
listener probe outcome of the last actually executed snapshot probe that determines or contributes to the
published terminal result, so "S0 or S1?" is not executor-selectable); the ambiguous section reference now
explicitly names the **original frozen oracle's §15.2** continuity comparison field set rather than this
specification's own local §15.2; publication failure emits exactly the constant stdout line
`ORACLE_R2_PUBLICATION_FAILURE` with no exception message, stack, provider text or environment data, and the
specification's frozen stdout contract now lists every possible Oracle-R2 stdout line; and `RESULT_R2` final
bytes are explicitly required to be byte-identical to the already validated result temp bytes, so all frozen
semantic fields are preserved by byte identity with no second semantic parser and no post-result probe.  The
listener taxonomy, the narrow typed catch structure, the output namespace, the six-path absence precondition,
the ASCII-only source with the runtime `[char]0x2014` construction through `UTF8Encoding(false)`, the
target-binding chain, canonicalization, hash/version checks, S0/S1 continuity, publication order, mandatory
stop, no HTTP, no OpenCode start/restart, no retry and no fallback are all **preserved without regression**.
Static validation for the corrective candidate: PowerShell **parser-only** validation with **0 parse errors**,
**0 non-ASCII bytes**, no BOM, LF only with **CR count = 0**, a `git check-attr` LF-contract confirmation,
residue scans for the corrected defects, and a committed-blob-versus-worktree byte comparison — **the
operational main path was not executed, no listener/process command was run and the endpoint was not
contacted**.  Current statuses: `ETB EXECUTION ORACLE-R2 (corrective candidate) = DESIGN CANDIDATE / NOT
ACCEPTED / NOT FROZEN / NOT EXECUTED`; `PREVIOUS ORACLE-R2 CANDIDATE 6d252a9 = REQUEST_CHANGES / SUPERSEDED AS
A CANDIDATE`; `RECOVERY-R1 AUTHORIZATION = SPENT / NOT REUSABLE`; `RECOVERY-R1 ETB ATTEMPT = SPENT / NOT
REUSABLE`; `RECOVERY-R1 PUBLISHED ETB RESULT = REJECTED`; `AUTHORITATIVE ETB SEMANTIC RESULT = NONE`;
`NEW_ETB_AUTHORIZATION_REQUIRED = YES`; and **no Recovery-R2 authorization and no Recovery-R2 claim namespace
exist**.  Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED /
PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 **NOT
CLOSED**; Case-C and v0.3-E implementation `NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`; `adopt_completed_turn`
**DISABLED**.  This corrective round performed **0** config mutations, **0** claim creations, **0** R2
directory or output creations, **0** Oracle-R2 executions, **0** old-oracle executions, **0** endpoint
queries, **0** `Get-NetTCPConnection` listener queries, **0** live `Get-CimInstance` queries, **0**
listener/process/port enumeration, **0** P/Invoke executions, **0** OpenCode starts/restarts, **0** HTTP,
**0** ETB executions, **0** SIC, **0** Mode-B work, **0** G0.5 and **0** G1/G2 activity, and **0**
runtime/test/dependency/version changes; the ignored/untracked `PROJECT_MEMORY.md` persists.

**The corrective Oracle-R2 candidate was independently approved, so Oracle-R2 is now `ACCEPTED / FROZEN /
NOT EXECUTED`.**  The independent review issued *APPROVE V0.3-E ETB EXECUTION ORACLE-R2 CORRECTIVE R2* with
severity **P0 = 0, P1 = 0, P2 = 0, P3 = 2**, which closes all three prior blockers — **P1 config-reader
invocation fidelity = RESOLVED**, **P2 evidence schema identity = RESOLVED** and **P2 executable byte-identity
deadlock = RESOLVED** — and leaves only two **non-blocking** P3 findings.  The permanently accepted Oracle-R2
identity is therefore `oracle_r2_commit = dfb78f34d919e8c9863a8398fb4f63ee301167bc`,
`oracle_r2_spec_sha256 = 5e9221e3950af6ec3e0612c4d962562c33e761899dfd6af42d10f5a9895f9f2f` and
`oracle_r2_script_sha256 = 22c5fbd61da609e6cc39e973be6030d4c360019ed1f56e69ca45f92fa1689c17`; these three
values together are the accepted Oracle-R2 identity, they are immutable, this acceptance-bookkeeping commit
does **not** replace `oracle_r2_commit`, and no future bookkeeping HEAD, Recovery-R2 authorization commit,
Recovery-R2 operational HEAD or ETB result-review commit may substitute for them.  Active Oracle-R2 status is
converged to **`ETB EXECUTION ORACLE-R2 = ACCEPTED / FROZEN / NOT EXECUTED`**, with `EXECUTABLE IDENTITY =
FROZEN`, `EXECUTION AUTHORITY = NOT GRANTED` and `RECOVERY-R2 AUTHORIZATION = DOES NOT EXIST`: **acceptance of
Oracle-R2 is design/oracle acceptance only and is NOT authorization to execute it.**  The accepted Oracle-R2
spec and script bytes are **frozen** and were **not** modified by this round; their own construction-time
headers may still read as design-candidate text, because acceptance is represented through the independent
approval record and the active authoritative status surfaces, following the established immutable-artifact +
approval-record pattern.  Historical provenance is preserved unchanged: candidate
`6d252a9466d768bb6345aad6c0c7a04562b8845c` = **REQUEST_CHANGES / SUPERSEDED AS A CANDIDATE / NEVER ACCEPTED
/ NEVER EXECUTED** — its `REQUEST_CHANGES` verdict is history only and is **not** the current Oracle-R2
verdict.  **No ETB semantic result follows from this acceptance:** `RECOVERY-R1 PUBLISHED ETB RESULT =
REJECTED`, `AUTHORITATIVE ETB SEMANTIC RESULT = NONE`, `RECOVERY-R1 AUTHORIZATION = SPENT / NOT REUSABLE`,
`RECOVERY-R1 ETB ATTEMPT = SPENT / NOT REUSABLE` and `NEW_ETB_AUTHORIZATION_REQUIRED = YES` are all preserved
exactly.  Recovery-R2 is explicitly **`NOT DESIGNED / NOT ACCEPTED / DOES NOT EXIST`**, its claim namespace is
**NOT CREATED** and its ETB attempt is **NOT STARTED**; no claim path was invented and no Recovery-R2
authorization was designed.  Mode-B remains `BLOCKED / NOT RUN`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 **NOT
CLOSED**; Case-C and v0.3-E implementation **NOT AUTHORIZED**; `G1`/`G2` `NOT RUN`;
`adopt_completed_turn` **DISABLED** — Oracle-R2 acceptance alone establishes neither target binding nor
`ETB_SATISFIED`.  **Non-blocking P3 recording (preserved, not promoted, not erased):** the review recorded
**P3 = 2 non-blocking**, and one explicitly noted residual edge case concerns Windows PowerShell
environment-variable semantics for a prior `PYTHONPATH` that is conceptually "present but empty"; the review
determined this has no result-classification effect and is non-blocking, and the accepted Oracle-R2 script was
**not** modified to address it in this round.  Authoritative sequence: Recovery-R1 rejected → Oracle-R2
initial candidate `6d252a9` → independent REQUEST_CHANGES → corrective Oracle-R2 candidate `dfb78f34` →
independent APPROVE → **Oracle-R2 acceptance bookkeeping (this round)** → independent acceptance-bookkeeping
confirmation → Recovery-R2 authorization design → independent Recovery-R2 authorization review → Recovery-R2
acceptance bookkeeping → independent bookkeeping confirmation → exactly one Recovery-R2 operational ETB
attempt → independent ETB-result review → only an independently accepted `ETB_SATISFIED` may permit Mode-B
oracle construction; **no stage may be skipped**.  This bookkeeping round performed **0** Oracle-R2
executions, **0** old-oracle executions, **0** claim creations, **0** claim deletions, **0** R2 output
creations, **0** R2 directory creations, **0** endpoint inspections, **0** listener queries, **0** process
queries, **0** operational P/Invoke, **0** OpenCode starts/restarts, **0** HTTP, **0** SIC, **0** Mode-B,
**0** G0.5, **0** G1/G2 activity, **0** config mutations, **0** R1 artifact mutations and **0**
runtime/test/dependency/version changes; the ignored/untracked `PROJECT_MEMORY.md` persists.

**A Recovery-R2 one-shot ETB execution authorization design candidate was created.**  The independent review
issued *APPROVE V0.3-E ETB EXECUTION ORACLE-R2 ACCEPTANCE BOOKKEEPING*, making
`9b17912a8b4bd6c87aa45eefc97a73eb3d22db34` the authoritative bookkeeping baseline (explicitly **not** the
Oracle-R2 provenance), and this round designs — as documentation only — the authorization under which exactly
**one** future ETB attempt may run the already accepted tracked Oracle-R2 executable.  The new artifact
`docs/v0.3/V03E_G0_5_PRE_ETB_RECOVERY_R2_AUTHORIZATION.md` is a **DESIGN CANDIDATE / NOT ACCEPTED / NOT
GRANTED / NOT EXECUTED**: it grants no execution authority today, creates no claim, mutates no configuration,
performs no endpoint/listener/process probe and does not enter Oracle-R2.  It binds permanently to the accepted
Oracle-R2 triple (`oracle_r2_commit = dfb78f34d919e8c9863a8398fb4f63ee301167bc`, `oracle_r2_spec_sha256 =
5e9221e3950af6ec3e0612c4d962562c33e761899dfd6af42d10f5a9895f9f2f`, `oracle_r2_script_sha256 =
22c5fbd61da609e6cc39e973be6030d4c360019ed1f56e69ca45f92fa1689c17`) plus the future independently accepted
`recovery_r2_authorization_commit` / `recovery_r2_authorization_sha256` pair.  It freezes a **new, permanently
distinct** claim namespace (four exact paths — `docs/v0.3/evidence/ETB_RECOVERY_R2_AUTHORIZATION_USE.claim`
(+`.tmp`) and `docs/v0.3/evidence/ETB_RECOVERY_R2_ATTEMPT_USE.claim` (+`.tmp`)), the accepted file-or-directory
occupancy predicate, two **new closed 7-field schemas** (`devrelay-etb-recovery-r2-authorization-use-v1` and
`devrelay-etb-recovery-r2-attempt-use-v1`, each ending in `state = CONSUMED` with no timestamp, hostname, PID,
operator, comment or extra field), the exact `Write-DevRelayRecoveryR2OneShotClaim` PowerShell/.NET writer
(exclusive `CreateNew` consumption point, exactly one LF, `UTF8Encoding(false)`, byte read-back, two-argument
no-overwrite `File.Move`, and TEMP-absent plus FINAL-occupied-as-file post-publication requirements), a **1/1**
authorization budget and a **1/1** ETB-attempt budget, and a complete 16-item read-only PRE-* checklist
(baseline HEAD, branch, accepted spec/script blob hashes, worktree byte identity, `text: set` / `eol: lf`, clean
tracked worktree, config hash/size/resolved value, `CONFIG_ESTABLISHMENT` hash, three historical claim
witnesses, all four new claim paths ABSENT, the accepted authorization artifact identity, and the
not-yet-consumed confirmations) with STOP-before-consumption on any failure.  It also freezes the boundary
rules that keep the oracle's own contract intact: **no authorization-layer precheck of the six Oracle-R2 output
paths**, **no target/listener/process pre-probe**, no config mutation and no `CONFIG_ESTABLISHMENT`
republication; the exact oracle entry invocation
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File "docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1"`
with no parameters, wrapper, generated or extracted script, alternate PowerShell implementation, environment
mutation, or pre/post-oracle helper; **no repeat of the byte-identity check after consumption** (it is a
pre-consumption PRE-* condition, and no permitted intervening step may modify the script); oracle-exclusive
ownership of target binding, the listener taxonomy, S0/S1 continuity, the evidence schema, classification,
publication and the mandatory stop, with any result **candidate-only** until independent ETB-result review; the
post-oracle stop rule (no rerun, no probe, no diagnostics, no repair, no reclassification, no retry of
publication, no HTTP, no SIC, no Mode-B, no G0.5/G1/G2); and the no-second-attempt rule (authorization writer
max **1**, attempt writer max **1**, Oracle-R2 invocation max **1**; no retry, no repair-and-rerun, no alternate
target/port/executable, no old-Oracle invocation, no `Mode P → Mode L` transition, no fallback).  Two explicit
control-failure classifications are frozen and are **not** ETB semantic results:
`RECOVERY_R2_AUTHORIZATION_CONTROL_FAILURE` (authorization 1/1 consumed, attempt 0/1 not started, result NONE)
and the post-attempt-claim failure state (authorization 1/1 consumed, attempt 1/1 consumed, result NONE,
Oracle-R2 not entered).  Static validation of the artifact: PowerShell **parser-only** validation of the
embedded writer with **0 parse errors** (605 tokens), byte-verified LF-only and BOM-free encoding, and
structural anchor plus PRE-* presence checks.  Historical state is preserved exactly: original Round-5
authorization `SPENT / NOT REUSABLE` with its claim FINAL OCCUPIED at `d84b4285…` and its ETB attempt `0/1
never started` (TEMP and FINAL ABSENT, still not reusable because the parent authorization is spent);
Recovery-R1 authorization `SPENT / NOT REUSABLE` (`8876bcc6…`); Recovery-R1 ETB attempt `SPENT / NOT REUSABLE`
(`5f1e9721…`); `AUTHORITATIVE ETB SEMANTIC RESULT = NONE`; config remains the exact post-image (`b5e4abab…` /
1897 / `http://127.0.0.1:4096`); `CONFIG_ESTABLISHMENT = VALID / PRESENT` (`ea9fc2bc…`).  Active statuses are
converged to `ETB EXECUTION ORACLE-R2 = ACCEPTED / FROZEN / NOT EXECUTED`, `EXECUTION AUTHORITY = NOT
GRANTED`, `RECOVERY-R2 AUTHORIZATION = DESIGN CANDIDATE / NOT ACCEPTED / NOT GRANTED / NOT EXECUTED`,
`RECOVERY-R2 AUTHORIZATION USE = UNUSED / 0 OF 1`, `RECOVERY-R2 ETB ATTEMPT = NOT STARTED / 0 OF 1` and
`RECOVERY-R2 CLAIM NAMESPACE = DEFINED BY CANDIDATE / NO CLAIM CREATED`.  Mode-B remains `BLOCKED / NOT RUN`;
`P6 = UNPROVEN / UNSATISFIED`; G0.5 **NOT CLOSED**; Case-C and v0.3-E implementation **NOT AUTHORIZED**;
`G1`/`G2` `NOT RUN`; `adopt_completed_turn` **DISABLED**.  This design round performed **0** Oracle-R2
executions, **0** old-oracle executions, **0** claim creations, **0** claim deletions, **0** R2 output
creations, **0** R2 directory creations, **0** endpoint inspections, **0** listener queries, **0** process
queries, **0** operational P/Invoke, **0** OpenCode starts/restarts, **0** HTTP, **0** `/doc` or `/session`,
**0** provider/model calls, **0** SIC, **0** Mode-B, **0** G0.5, **0** G1/G2 activity, **0** config mutations,
**0** R1 artifact mutations and **0** runtime/test/dependency/version changes; the ignored/untracked
`PROJECT_MEMORY.md` persists.

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
