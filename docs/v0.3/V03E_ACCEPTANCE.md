# DevRelay v0.3-E acceptance matrix — recovery & reconciliation (design phase)

Status: **DESIGN FROZEN / NOT IMPLEMENTED / NOT ACCEPTED / UNRELEASED**

Independent design-freeze review of candidate
`9f4a01804b9affe8938a272553df345b5a60aeed`: **P0 = 0, P1 = 0, P2 = 0**, F1–F12
**CLOSED**, decision **APPROVE V0.3-E FAIL-CLOSED CORE DESIGN; PLATFORM PROOF GATE
REQUIRED BEFORE IMPLEMENTATION**.  The design (`docs/v0.3/V03E_SPEC.md`) is frozen;
implementation is **NOT authorized**, the platform proof gate is **NOT complete**
(**G0.1 / P7 = PASS — authoritative, independently approved through
*APPROVE V0.3-E G0.1 / P7 PLATFORM PROOF*, P0 = 0, P1 = 0, P2 = 0 —
`V03E_G0_1_P7_PROOF.md`; **G0.2 = PASS — authoritative, independently approved**
through *APPROVE V0.3-E G0.2 FALSE-CORRELATION PROOF* (P0 = 0, P1 = 0, P2 = 0) via the
clean re-run under the oracle precommitted in commit `12ea1b7`: ten fixed cases A-J
fail-closed, oracle unchanged during execution, 0 provider/model calls —
`V03E_G0_2_CLEAN_RERUN_PROOF.md` (original round preserved:
`V03E_G0_2_FALSE_CORRELATION_PROOF.md`); the original G0.3 round failed as
**CANDIDATE FAIL** and was independently reviewed as a **TYPE-1 proof-plan failure**
(P0 = 0, P1 = 0, P2 = 0: no classifier-safety failure, no runtime remediation required —
`V03E_G0_3_TRANSPORT_PROOF.md`); the separately authorized **corrected clean rerun** under
the oracle precommitted in `e328ec5` (`V03E_G0_3_RERUN_ORACLE.md`) produced
**G0.3 / P5 = PASS** — authoritative, independently approved through *APPROVE V0.3-E G0.3 / P5 TRANSPORT PROOF* (P0 = 0, P1 = 0, P2 = 0); accepted safe buckets
class-wide pre-send, `proxy_error` `UNREACHABLE_CURRENT_CONFIGURATION`, every uncertain
class fail-closed, corrected case J surfaced `remote_protocol_error` as precommitted —
`V03E_G0_3_CLEAN_RERUN_PROOF.md`; **G0.4 was executed once and is an authoritative `FAIL / P4 UNPROVEN`** — the independent failed-proof review issued *APPROVE V0.3-E G0.4 FAILED PROOF* (P0 = 0, P1 = 0, P2 = 0; failure type **TYPE 3 — SEMANTIC ENVIRONMENT / CONFIGURATION RESULT**): the accepted configuration supplied no OpenCode base endpoint, so no target instance could be bound and **0 `GET /doc`** were issued (`V03E_G0_4_API_INSPECTION_PROOF.md`); steps G0.5, G1, G2 not run),
`adopt_completed_turn` remains **DISABLED**,
and the mandatory-core gate **G0.1/P7 PASS first** is now **satisfied** (the proof
passed and was independently approved), with no degraded-implementation path.

Only a design exists: **no recovery code, no new tool, no schema change and no test
was written**.  Of the proof-gate rows below, **G0.1/P7 (E34)**, **G0.2 (E35)** and
**G0.3/P5 (E36)** are authoritative PASS (independently approved); **G0.4/P4** was **executed once** under its approved immutable revision-3 oracle (`docs/v0.3/V03E_G0_4_API_INSPECTION_ORACLE.md`, committed-blob SHA-256 `b0c34fa1…`) and the independently issued failed-proof decision *APPROVE V0.3-E G0.4 FAILED PROOF* (P0 = 0, P1 = 0, P2 = 0; failure type **TYPE 3 — SEMANTIC ENVIRONMENT / CONFIGURATION RESULT**) makes it an **authoritative FAIL / P4 UNPROVEN** — Case A did not establish `TARGET_BOUND` (`TARGET_IDENTITY_UNRESOLVED`: the accepted workspace had no OpenCode base endpoint), so 0 loopback HTTP requests / 0 `GET /doc` were issued and cases B–H were not executed (`docs/v0.3/V03E_G0_4_API_INSPECTION_PROOF.md`); **G0.5/P6 = NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP** — the definition was accepted by independent review (*APPROVE V0.3-E G0.5 ADOPTION-DEPENDENCY CLEANUP*, P0 = 0, P1 = 0, P2 = 0; baseline `ad86a79`) and the subsequent pre-run oracle construction was independently approved as a **freezability failure** (*APPROVE V0.3-E G0.5 ORACLE FREEZABILITY FAILURE*, P0 = 0, P1 = 0, P2 = 0; classification **C — NOT-YET-IMPLEMENTED V0.3-E ENFORCEMENT PREREQUISITE**): under the accepted §25.1 definition, cases **A (missing)**, **B (foreign)** and **D (copied)** bind to existing local enforcement, but **case C (recreated / originality-unprovable) has no existing local original-session/provenance enforcement path**, so a complete four-case oracle cannot be frozen and **no oracle was created**.  P6 = **UNPROVEN / UNSATISFIED**; **no G0.5 semantic case was executed**, therefore there is **no G0.5 PASS and no G0.5 FAIL**; the independently approved Case-C prerequisite design block (*APPROVE V0.3-E CASE-C PREREQUISITE DESIGN BLOCK*) confirmed the stronger thesis **`BLOCKED — NO SOUND ORIGINAL-SESSION PROVENANCE ANCHOR AVAILABLE`**, and a new read-only prerequisite information finding — **G0.5-PRE / SIC (session-incarnation capability finding)** — is now a **definition candidate** (`docs/v0.3/V03E_G0_5_PRE_SESSION_INCARNATION_FINDING.md`, status **SIC MODE-A = EXECUTED ONCE / DEFINITION ACCEPTED / ORACLE ACCEPTED AND FROZEN / AUTHORITATIVE FINDING = `SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT` / ATTEMPT CONSUMED / NO RERUN AUTHORIZED**; the **broader session-incarnation capability = NOT ESTABLISHED BY MODE-A STATIC SURFACE**.  The independent result review approved the result (*APPROVE V0.3-E SIC MODE-A RESULT*, P0 = 0, P1 = 0, P2 = 0; classification **VALID SEMANTIC RESULT**) and it binds the reviewed result artifact `docs/v0.3/V03E_G0_5_PRE_SIC_RESULT.md` (blob `ce6c503d…`, kept immutable) to that decision.  The accepted/frozen Mode-A oracle (`docs/v0.3/V03E_G0_5_PRE_SIC_ORACLE.md`, baseline `e1fb6ac`, blob `31d7ac50…`) governed **exactly one** authorized offline/static attempt under a hard zero-live budget: the frozen manifest was re-enumerated and matched exactly (8 files / 6 directories, no missing/extra/drifted artifact), every artifact was classified, complete coverage held, the deterministic extraction produced **zero candidates**, and the frozen mapping yielded `SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`.  Strict scope and non-claims: the finding applies **only** to the exact successfully inspected OpenCode 1.18.11 installed static package surface and frozen target/package artifacts; it does **not** establish that OpenCode globally has no session-incarnation metadata, does **not** establish that a live/local API exposes no additional contract surface, does **not** establish P6 (neither PASS nor FAIL), is **not** `G0.5 PASS`/`G0.5 FAIL`, and does **not** enable `adopt_completed_turn`.  The attempt is consumed; **no rerun** and **no Mode B/C** is authorized, and G0.5/P6 is unchanged.  The earlier remediation had established: runtime observation may never supply semantic authority, `NOT_EXPOSED` requires complete precommitted coverage with no global generalization, the inspection mode must be precommitted with no mid-run switching, and live binding must tie the actual client destination to the verified responder process; not a P-number, not a proof of P6, not an adoption-enabling proof, not an implementation authorization; 0 provider/model/HTTP/OpenCode activity); **G1** and **G2** have **NOT run**.  No OpenCode instance was started and no
provider/model call was made.  The accepted v0.3-D runtime candidate
`8b70610a5cdda600ef57cf8378c4f69cd33d5be4` is untouched.  Every *implementation* row
below remains FUTURE / NOT RUN, and the recorded P3 observations (P3-1, P3-2,
P3-4/P3-5) stay non-blocking.

Legend:

* **FROZEN (design)** — decided and frozen by the independently approved v0.3-E
  design (candidate `9f4a01804b9affe8938a272553df345b5a60aeed`; design-freeze review
  **P0 = 0, P1 = 0, P2 = 0**).  This label records **design status only** and does
  **not** authorize implementation: mandatory-core implementation required
  **G0.1 / P7 PASS** under `V03E_SPEC.md` §25 - that gate has now **passed**
  (authoritative, independently approved), so implementation may be authorized by a
  separately issued authorization, and there is no degraded-implementation path.
* **PROOF REQUIRED** — cannot be implemented or accepted until the named platform
  proof passes (proof gate in `V03E_SPEC.md` §25).
* **DISABLED** — documented but refused at runtime until its gate passes.
* **FUTURE / NOT RUN** — evidence the implementation round must produce; nothing
  here is claimed as passed.

## A. Mandatory core (no remote platform proof required; G0.1/P7 gate satisfied)

Design freeze does **not** authorize implementation.  The mandatory-core ordering was
**design frozen → G0.1 / P7 PASS → implementation may be authorized**, and the second
step is now **satisfied** (the proof passed and was independently approved), so
implementation may be authorized by a separately issued authorization; had G0.1/P7
failed, mandatory-core implementation would have remained **blocked** (no
degraded-implementation path), and `evidence_gap` stays a future *runtime*
fail-closed outcome rather than a substitute for G0.1/P7 PASS.  Optional adoption
remains **DISABLED** unless **both**: the local **P6 identity/ownership veto bound** is
independently satisfied by G0.5 (§25.1), **and** the required remote/platform *enabling*
proofs P1 + P2 + P3 + P8 (plus P9 only if timestamp/order correlation is used) are
independently satisfied by G1/G2.  **No single proof enables adoption.**  **G0.1 / P7 was executed once and returned
**PASS** (authoritative, independently approved — `V03E_G0_1_P7_PROOF.md`), so
G0.1/P7 no longer blocks mandatory-core implementation *eligibility*; the other gate
steps have **NOT run** (G0.4 was executed once and is an authoritative **FAIL / P4 UNPROVEN** — approved failed proof, TYPE 3; no configured endpoint, no target binding, 0 `GET /doc`; G0.5, G1, G2 unrun) — G0.2 = PASS (authoritative, independently approved), while G0.3 failed its original oracle, was independently reviewed as a TYPE-1 proof-plan failure, corrected and then independently approved — G0.3/P5 = PASS (authoritative) — the platform proof gate is **partially
executed / not complete**, and mandatory-core implementation remains **NOT
AUTHORIZED** until a separately issued implementation authorization.

| # | Criterion | Design status | Reference |
| --- | --- | --- | --- |
| E1 | Scope split: mandatory core (report + `mark_unrecoverable`, no submission, no retry, no auto-resume, no adoption) vs optional gated adoption vs report-only pending vs informational non-delivery | FROZEN | SPEC §1, §19 |
| E2 | The recovery problem is split into distinct cases A–H **plus X (corrupt)** and never collapsed into one "retryable" bucket | FROZEN | SPEC §4 |
| E3 | RECONCILE / MATERIALIZE / RESUME / RETRY are defined separately; bridge `retry_safe` has no recovery authority; v0.3-E has no retry protocol | FROZEN | SPEC §5, §18 |
| E4 | Recovery authority = deterministic evidence **and** an explicit external planner action; provider/reviewer prose has zero recovery authority | FROZEN | SPEC §7 |
| E5 | **Entry is an explicit legal action**: `resolve_recovery` accepts (1) a valid v2 non-terminal document with a legal live intent and (2) a document already in `RECOVERY_REQUIRED`; v2 phase/decide calls refuse **without mutating** | FROZEN | SPEC §7 |
| E6 | **One legal attempt representation**: one `recovery.attempt` record while in `RECOVERY_REQUIRED`; resolution converts it once into exactly one role turn | FROZEN | SPEC §8.1 |
| E7 | **Exact `RECOVERY_REQUIRED` document shape** with pinned accounting equations (`turn_attempts == model_turns_used`; `impl + rev + ra == model_turns_used`; no refund; counted exactly once) and the new `recover` edges | FROZEN | SPEC §8.2, §8.3, §8.4 |
| E8 | **Corruption is never recovery**: violations outside the enumerated deltas → `orchestration_state_corrupt`, no entry, no override, no repair | FROZEN | SPEC §6 |
| E9 | **Strict recovery evidence reader**: identity-scoped, no silent skipping, no truncation-as-proof, interval proof, `evidence_gap` otherwise; absence is never proof of non-delivery | FROZEN (correctness proof = G0.1/P7) | SPEC §9 |
| E10 | `mark_unrecoverable` independence: requires only a legal recovery document/action, planner authority, local invariants and no corruption; **never** requires remote session history | FROZEN | SPEC §11 (intro), §19 |
| E11 | Terminal states never enter recovery and never reopen; recovery actions against them are local, mutation-free and model-call-free | FROZEN | SPEC §12.5 |
| E12 | `devrelay_get_run` stays read-only; reconciliation/materialization requires an explicit recovery action | FROZEN | SPEC §21 |
| E13 | Budget/accounting: the §8.3 equations, no refund, no reset, no recomputation, no restart budget | FROZEN | SPEC §8.3, §22 |
| E14 | Route snapshot authoritative; current configuration is drift detection only; no fallback, no snapshot rewrite | FROZEN | SPEC §12.3 |
| E15 | Workspace/session identity re-verified; copied/foreign/missing session bounds recovery (adoption unavailable; report/`mark_unrecoverable` still work) | FROZEN | SPEC §12.4 |
| E16 | Concurrency: recovery shares the accepted per-surface lock; multi-surface/multi-process remains unsupported; no process-wide claim | FROZEN | SPEC §22 |
| E17 | Privacy: digests/ids/metadata only; no prompt/response/reasoning/credential persistence | FROZEN | SPEC §22 |
| E18 | Crash-window matrix W0–W7 (**including W4: response received, ledger settle not durably written**) with no cell authorizing behaviour forbidden elsewhere | FROZEN | SPEC §16 |
| E19 | Restart matrix: no restart performs work, creates budget, refunds a slot or issues a request | FROZEN | SPEC §17 |
| E20 | **Schema v1/v2 dispatch**: v1 validated by the frozen v0.3-D validator, never written/migrated, no recovery entry, resolve refuses locally, v1 live-intent behaviour exactly v0.3-D; v2 uses v0.3-E rules; anything else is corrupt.  New runs are v2 | FROZEN | SPEC §10 |
| E21 | `evidence_sha256` canonical input (field list, order, encoding, null representation, version marker), no raw text hashed; repeat resolve → stable `orchestration_recovery_already_resolved` error with no write | FROZEN | SPEC §13 |
| E22 | Prompt-digest semantics pinned to the accepted joined-text representation (multiple parts joined with `\n`, no line-ending normalization, UTF-8, empty/missing → fail closed); canonical fidelity still depends on P2 | FROZEN (fidelity = P2) | SPEC §12.2 |
| E23 | Minimum tool surface: `devrelay_reconcile_run` (read-only) + `devrelay_resolve_recovery` (only write, gated adoption); no hidden phase turn, no wait, no polling, no retry | FROZEN | SPEC §21 |
| E24 | Non-goals explicit (retry, auto-decisions, sequencing, fallback, pending adoption, distributed locking, daemons, WebUI/HTTP, release work, heuristics) | FROZEN | SPEC §23 |
| E25 | Test strategy defined before implementation, including entry, accounting, strict-reader, corruption, gate-refusal, `mark_unrecoverable`-independence, no-submission, terminal, restart, dispatch, privacy and mutation tests | FROZEN | SPEC §24 |

## B. Optional gated capability — `adopt_completed_turn` (DISABLED until proven)

| # | Criterion | Design status | Reference |
| --- | --- | --- | --- |
| E26 | Adoption is **not** part of the mandatory scope; `resolve_recovery` MUST refuse it while the gate is unproven; reconcile may report a candidate only | DISABLED (design) | SPEC §1, §11 |
| E27 | When enabled, adoption requires all §11 items: single matching settled ledger record; the matched user message is the last relevant one; the assistant message is directly associated and final; no unexpected session message; no other ledger operation on that session in the window; identity match; the **local P6 identity/ownership veto bound** satisfied (§12.4, §25.1); and the remote/platform **enabling** proofs P1+P2+P3+P8 (+P9 if timestamps) — the local veto bound and the remote enabling proofs are **distinct classes** and **both** are required | PROOF REQUIRED (P1/P2/P3/P8/P9 **+ the P6 veto bound** / G0.5) | SPEC §11, §25.1 |
| E28 | Adoption performs no provider call, uses one atomic write, converts the attempt into exactly one completed role turn, and lands in `READY_REVIEWER` / `AWAITING_DECISION` | PROOF REQUIRED | SPEC §8.1, §11 |
| E29 | **P8 — session exclusivity**: no other writer (another surface/process, human or client chat, direct OpenCode API use, unrelated tooling) submitted into the session during the evidence window.  Required for adoption; **not** required for report/`mark_unrecoverable` | PROOF REQUIRED (G2 + local cross-checks) | SPEC §11 (condition 6), §19 |
| E30 | **P9 — `created_at`/ordering fidelity**: if any correlation uses timestamps or relative order, their determinism, semantics and restart survival must be proven; otherwise timestamps are not identity primitives | PROOF REQUIRED only if timestamps are used | SPEC §12.2, §28 |

## C. Report-only capabilities

| # | Criterion | Design status | Reference |
| --- | --- | --- | --- |
| E31 | **P4 pending**: OpenCode 1.18.11 exposes session-level status only (no durable per-operation handle) → `reply_pending` is report-only: no adoption, no polling loop, no automatic wait, no pending-driven state advance; a future handle needs a new reviewed capability extension.  *The session-level-only statement is **historical review knowledge** and the report-only policy applies regardless; the **formal G0.4 proof status** is row E37 (executed once: authoritative **FAIL / P4 UNPROVEN**)* | FROZEN (report-only) | SPEC §14 |
| E32 | **P5 non-delivery**: the accepted transport classification is reported as evidence only — no orchestration authority, no retry licence, no refund; `mark_unrecoverable` remains the only mandatory-core resolution | FROZEN (informational) | SPEC §15 |
| E33 | **P6 identity/ownership veto bound**: missing/foreign/recreated/copied or otherwise unprovable session ⇒ adoption unavailable; **`session_id` equality alone never clears the veto** and no single field proves ownership; report/`mark_unrecoverable` still work without claiming remote completion.  This is a **fail-closed veto bound, not an adoption-enabling proof** | FROZEN (bound) | SPEC §12.4, §25.1 |

## D. Local platform proofs (no real provider needed)

| # | Criterion | Status | Reference |
| --- | --- | --- | --- |
| E34 | **P7 / G0.1** — hard-kill DevRelay around `ISSUED`/settle writes and verify the strict reader returns a complete valid record or `evidence_gap`/corruption, never silently skipping | **PASS** (authoritative / independently approved; executed once at `5bdc21d`–`fe304ab`, candidate result then approved by the final proof review — *APPROVE V0.3-E G0.1 / P7 PLATFORM PROOF*, P0 = 0, P1 = 0, P2 = 0; cases A1, A2, B, C, D, E all met their predefined criteria; evidence: `docs/v0.3/V03E_G0_1_P7_PROOF.md`) | SPEC §9, §25 |
| E35 | **G0.2** — offline run↔call false-correlation cases (two runs, reused prompts, reused sessions, neighbouring call ids) | **PASS** (authoritative / independently approved through *APPROVE V0.3-E G0.2 FALSE-CORRELATION PROOF*, P0 = 0, P1 = 0, P2 = 0; clean re-run under the oracle precommitted in commit `12ea1b7`; ten fixed cases A-J executed once each and fail-closed — a unique `MATCH` only on the complete identity tuple, otherwise `NO_MATCH`/`evidence_conflict`/`evidence_gap`/`corruption`, no timestamp tie-break, oracle module hash unchanged during execution, 0 provider/model calls; evidence: `docs/v0.3/V03E_G0_2_CLEAN_RERUN_PROOF.md`; original round preserved: `docs/v0.3/V03E_G0_2_FALSE_CORRELATION_PROOF.md`) | SPEC §25 |
| E36 | **G0.3** — transport/non-delivery classification checks against the accepted taxonomy (P5) | **PASS** (authoritative / independently approved through *APPROVE V0.3-E G0.3 / P5 TRANSPORT PROOF*, P0 = 0, P1 = 0, P2 = 0; corrected clean rerun executed once under the oracle precommitted in `e328ec5`, one semantic execution per case: `connect_timeout`/`pool_timeout`/`connect_error`/`unsupported_protocol` and the pre-send-only `local_protocol_error` mapping boundary are class-wide pre-send with no request header or body byte on the wire, `proxy_error` is `UNREACHABLE_CURRENT_CONFIGURATION`, every uncertain class stayed `submission_uncertain == true` with `retry_safe == false`, corrected case G0.3-J surfaced `remote_protocol_error` exactly as precommitted, and HTTP rejection/success were never non-delivery; P5 remains informational only; evidence: `docs/v0.3/V03E_G0_3_CLEAN_RERUN_PROOF.md`; the original round's candidate FAIL and its independent TYPE-1 review outcome remain historical in `docs/v0.3/V03E_G0_3_TRANSPORT_PROOF.md`) | SPEC §25 |
| E37 | **G0.4** — OpenCode installed-API inspection for a per-operation pending handle (P4) | **AUTHORITATIVE FAIL / P4 UNPROVEN** — the single authorized execution (immutable revision-3 oracle `docs/v0.3/V03E_G0_4_API_INSPECTION_ORACLE.md`, committed-blob SHA-256 `b0c34fa1…`) was independently approved as a **FAILED PROOF**: *APPROVE V0.3-E G0.4 FAILED PROOF*, P0 = 0, P1 = 0, P2 = 0, failure type **TYPE 3 — SEMANTIC ENVIRONMENT / CONFIGURATION RESULT**.  Case A did not establish `TARGET_BOUND` (`TARGET_IDENTITY_UNRESOLVED` — the accepted workspace had no OpenCode base endpoint), so **0 loopback HTTP requests / 0 `GET /doc`** were issued and cases B–H were not executed; **no API/schema property was established and P4 remains formally unproven** (evidence: `docs/v0.3/V03E_G0_4_API_INSPECTION_PROOF.md`; 0 provider/model calls, 0 OpenCode starts; rerun of this execution not authorized) | SPEC §25 |
| E38 | **G0.5** — P6 local identity/ownership **veto-bound** proof: exactly four case classes A–D (missing; foreign; recreated/originality-unprovable; copied); PASS is a **bounding** pass that clears only the local veto prerequisite and never proves global session-id uniqueness or ownership by id; method is local/offline (0 HTTP, 0 OpenCode, 0 provider/fake-provider calls, no restart, no session mutation) | PROOF REQUIRED (local, offline) — definition **accepted** (SPEC §25.1, baseline `ad86a79`); **ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP**: cases A/B/D reachable through existing local enforcement, **case C has no existing local original-session/provenance enforcement path**, so no complete four-case oracle can be frozen; **0 semantic cases executed → no PASS, no FAIL**; P6 = **UNPROVEN / UNSATISFIED**; G0.5 = **NOT RUN** and no oracle exists; a read-only **session-incarnation capability finding — G0.5-PRE / SIC** (`V03E_G0_5_PRE_SESSION_INCARNATION_FINDING.md`, **SIC MODE-A = EXECUTED ONCE / ORACLE ACCEPTED AND FROZEN / AUTHORITATIVE FINDING `SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT` / ATTEMPT CONSUMED / NO RERUN AUTHORIZED**; broader session-incarnation capability **NOT ESTABLISHED BY MODE-A STATIC SURFACE**; approved result artifact `V03E_G0_5_PRE_SIC_RESULT.md`, frozen oracle `V03E_G0_5_PRE_SIC_ORACLE.md`; no Mode B/C authorized) is now defined as the prerequisite information finding for any future Case-C design | SPEC §25, §25.1, SIC definition |

## E. Remote platform proofs (gated capabilities only)

| # | Criterion | Status | Reference |
| --- | --- | --- | --- |
| E39 | **G1 / P1** — real local OpenCode `1.18.11` session-history restart proof: ids and text survive a server restart | PROOF REQUIRED (0 provider calls) | SPEC §25, §28 |
| E40 | **G2 / P2, P3, P8, P9** — real local OpenCode + **local fake** OpenAI-compatible provider: submitted-text fidelity, duplicate-identical-prompt uniqueness, session-exclusivity assumptions as far as observable, timestamp/order fidelity if used | PROOF REQUIRED (0 real provider calls) | SPEC §25, §28 |

Proof-gate rules: **no probe shopping** — one planned probe per case; a failed
proof removes the gated capability rather than triggering another probe; the gate
has **not** run and must not be run in this design round.  **G1/G2 are the
remote/platform adoption *enabling* proofs; the local P6 identity/ownership *veto bound* is
proved separately by G0.5 (SPEC §25.1).  Both classes must be satisfied before adoption may
ever be authorized, and neither enables adoption alone.**

## F. Implementation acceptance (future round — no code exists, nothing claimed)

| # | Criterion | Status | Future evidence |
| --- | --- | --- | --- |
| E41 | Explicit entry works for both input shapes, and v2 phase/decide calls refuse without mutating | FUTURE / NOT RUN | entry tests + byte-identical document assertions |
| E42 | `RECOVERY_REQUIRED` document shape and the §8.3 accounting equations hold before/at/after every resolution, with the attempt counted exactly once | FUTURE / NOT RUN | shape + accounting tests |
| E43 | Corruption outside the enumerated deltas never becomes recovery (no entry, no override, byte-identical file) | FUTURE / NOT RUN | corruption matrix |
| E44 | Strict reader: unreadable/torn records → `evidence_gap`; no truncation-as-proof; interval proof; `no_record_in_proven_interval` never read as "never submitted" | FUTURE / NOT RUN | reader tests |
| E45 | Adoption is refused item-by-item unless every §11 condition and its gate pass | FUTURE / NOT RUN | refusal matrix + capability flag tests |
| E46 | `mark_unrecoverable` works with no session history and with a missing/foreign session | FUTURE / NOT RUN | independence tests |
| E47 | Across every recovery scenario the prompt-POST count / `external_request_count` never increases | FUTURE / NOT RUN | ledger assertions |
| E48 | Terminal immunity, restart matrix, v1/v2 dispatch, privacy scans and the accepted v0.3-D invariants (authority, ≤1 submission, terminals, budget) hold | FUTURE / NOT RUN | matrix tests |
| E49 | Recovery-critical invariants are mutation-verified (no second submission, no refund, no ungated adoption, no terminal reopening, no side-effect entry, read-only reconcile, strict-reader honesty) with recorded failure counts | FUTURE / NOT RUN | mutation back-check |
| E50 | Production-generated honest recovery corpus (A–H + fake remote-evidence variants) accepted; corrupted variants rejected | FUTURE / NOT RUN | corpus + differential battery |
| E51 | 0 real provider/model calls during unit/integration testing; the single bounded adoption smoke (if the gate passes) uses exactly one real model turn and is separately authorized | FUTURE / NOT RUN | run records |

## G. Deferred / carried

| # | Item | Why deferred |
| --- | --- | --- |
| F1 | Multi-surface / multi-process same-workspace coordination | remains unsupported; v0.3-E does not expand the locking scope (SPEC §22) |
| F2 | The carried v0.3-D P3 list (MCP SDK argument normalization and JSON-shaped prompts, non-cryptographic validation bound, inert temp files, read-only `get_run`, no fsync/power-loss durability) | unchanged by v0.3-E; kept in `docs/BACKLOG.md` §5 |
| F3 | Automatic resume / retry protocols | explicit non-goals (SPEC §18, §23) |
| F4 | A future real acceptance smoke for `adopt_completed_turn` | only if the platform proof gate passes; if adoption stays disabled, **no real smoke is required** and the reduced core can be accepted fully locally (SPEC §26) |
