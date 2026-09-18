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
`V03E_G0_3_CLEAN_RERUN_PROOF.md`; **G0.4 was executed once and returned `CANDIDATE FAIL / P4 UNPROVEN`** — the accepted configuration resolved no OpenCode endpoint, so no target instance could be bound and **0 `GET /doc`** were issued (`V03E_G0_4_API_INSPECTION_PROOF.md`); steps G0.5, G1, G2 not run),
`adopt_completed_turn` remains **DISABLED**,
and the mandatory-core gate **G0.1/P7 PASS first** is now **satisfied** (the proof
passed and was independently approved), with no degraded-implementation path.

Only a design exists: **no recovery code, no new tool, no schema change and no test
was written**.  Of the proof-gate rows below, **G0.1/P7 (E34)**, **G0.2 (E35)** and
**G0.3/P5 (E36)** are authoritative PASS (independently approved); **G0.4** was **executed once** under its approved immutable revision-3 oracle (`docs/v0.3/V03E_G0_4_API_INSPECTION_ORACLE.md`, committed-blob SHA-256 `b0c34fa1…`) and returned **CANDIDATE FAIL / P4 UNPROVEN** — Case A did not establish `TARGET_BOUND` (`TARGET_IDENTITY_UNRESOLVED`: no OpenCode endpoint is configured in `.devrelay/config.yaml`), so 0 loopback HTTP requests / 0 `GET /doc` were issued and cases B–H were not executed (`docs/v0.3/V03E_G0_4_API_INSPECTION_PROOF.md`); **G0.5**, **G1** and **G2** have **NOT run**.  No OpenCode instance was started and no
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
remains **DISABLED** until P1 + P2 + P3 + P8 (plus P9 only if timestamp/order
correlation is used), gated by G1/G2.  **G0.1 / P7 was executed once and returned
**PASS** (authoritative, independently approved — `V03E_G0_1_P7_PROOF.md`), so
G0.1/P7 no longer blocks mandatory-core implementation *eligibility*; the other gate
steps have **NOT run** (G0.4 was executed once and returned **CANDIDATE FAIL / P4 UNPROVEN** — no configured endpoint, no target binding, 0 `GET /doc`; G0.5, G1, G2 unrun) — G0.2 = PASS (authoritative, independently approved), while G0.3 failed its original oracle, was independently reviewed as a TYPE-1 proof-plan failure, corrected and then independently approved — G0.3/P5 = PASS (authoritative) — the platform proof gate is **partially
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
| E27 | When enabled, adoption requires all §11 items: single matching settled ledger record; the matched user message is the last relevant one; the assistant message is directly associated and final; no unexpected session message; no other ledger operation on that session in the window; identity match; P1+P2+P3+P8 (+P9 if timestamps) | PROOF REQUIRED (P1/P2/P3/P8/P9) | SPEC §11 |
| E28 | Adoption performs no provider call, uses one atomic write, converts the attempt into exactly one completed role turn, and lands in `READY_REVIEWER` / `AWAITING_DECISION` | PROOF REQUIRED | SPEC §8.1, §11 |
| E29 | **P8 — session exclusivity**: no other writer (another surface/process, human or client chat, direct OpenCode API use, unrelated tooling) submitted into the session during the evidence window.  Required for adoption; **not** required for report/`mark_unrecoverable` | PROOF REQUIRED (G2 + local cross-checks) | SPEC §11 (condition 6), §19 |
| E30 | **P9 — `created_at`/ordering fidelity**: if any correlation uses timestamps or relative order, their determinism, semantics and restart survival must be proven; otherwise timestamps are not identity primitives | PROOF REQUIRED only if timestamps are used | SPEC §12.2, §28 |

## C. Report-only capabilities

| # | Criterion | Design status | Reference |
| --- | --- | --- | --- |
| E31 | **P4 pending**: OpenCode 1.18.11 exposes session-level status only (no durable per-operation handle) → `reply_pending` is report-only: no adoption, no polling loop, no automatic wait, no pending-driven state advance; a future handle needs a new reviewed capability extension.  *The session-level-only statement is **historical review knowledge** and the report-only policy applies regardless; the **formal G0.4 proof status** is row E37 (executed once: `CANDIDATE FAIL / P4 UNPROVEN`)* | FROZEN (report-only) | SPEC §14 |
| E32 | **P5 non-delivery**: the accepted transport classification is reported as evidence only — no orchestration authority, no retry licence, no refund; `mark_unrecoverable` remains the only mandatory-core resolution | FROZEN (informational) | SPEC §15 |
| E33 | **P6 identity bound**: missing/foreign/recreated/copied session ⇒ adoption unavailable; report/`mark_unrecoverable` still work without claiming remote completion | FROZEN (bound) | SPEC §12.4 |

## D. Local platform proofs (no real provider needed)

| # | Criterion | Status | Reference |
| --- | --- | --- | --- |
| E34 | **P7 / G0.1** — hard-kill DevRelay around `ISSUED`/settle writes and verify the strict reader returns a complete valid record or `evidence_gap`/corruption, never silently skipping | **PASS** (authoritative / independently approved; executed once at `5bdc21d`–`fe304ab`, candidate result then approved by the final proof review — *APPROVE V0.3-E G0.1 / P7 PLATFORM PROOF*, P0 = 0, P1 = 0, P2 = 0; cases A1, A2, B, C, D, E all met their predefined criteria; evidence: `docs/v0.3/V03E_G0_1_P7_PROOF.md`) | SPEC §9, §25 |
| E35 | **G0.2** — offline run↔call false-correlation cases (two runs, reused prompts, reused sessions, neighbouring call ids) | **PASS** (authoritative / independently approved through *APPROVE V0.3-E G0.2 FALSE-CORRELATION PROOF*, P0 = 0, P1 = 0, P2 = 0; clean re-run under the oracle precommitted in commit `12ea1b7`; ten fixed cases A-J executed once each and fail-closed — a unique `MATCH` only on the complete identity tuple, otherwise `NO_MATCH`/`evidence_conflict`/`evidence_gap`/`corruption`, no timestamp tie-break, oracle module hash unchanged during execution, 0 provider/model calls; evidence: `docs/v0.3/V03E_G0_2_CLEAN_RERUN_PROOF.md`; original round preserved: `docs/v0.3/V03E_G0_2_FALSE_CORRELATION_PROOF.md`) | SPEC §25 |
| E36 | **G0.3** — transport/non-delivery classification checks against the accepted taxonomy (P5) | **PASS** (authoritative / independently approved through *APPROVE V0.3-E G0.3 / P5 TRANSPORT PROOF*, P0 = 0, P1 = 0, P2 = 0; corrected clean rerun executed once under the oracle precommitted in `e328ec5`, one semantic execution per case: `connect_timeout`/`pool_timeout`/`connect_error`/`unsupported_protocol` and the pre-send-only `local_protocol_error` mapping boundary are class-wide pre-send with no request header or body byte on the wire, `proxy_error` is `UNREACHABLE_CURRENT_CONFIGURATION`, every uncertain class stayed `submission_uncertain == true` with `retry_safe == false`, corrected case G0.3-J surfaced `remote_protocol_error` exactly as precommitted, and HTTP rejection/success were never non-delivery; P5 remains informational only; evidence: `docs/v0.3/V03E_G0_3_CLEAN_RERUN_PROOF.md`; the original round's candidate FAIL and its independent TYPE-1 review outcome remain historical in `docs/v0.3/V03E_G0_3_TRANSPORT_PROOF.md`) | SPEC §25 |
| E37 | **G0.4** — OpenCode installed-API inspection for a per-operation pending handle (P4) | **EXECUTED ONCE — `CANDIDATE FAIL / P4 UNPROVEN`** under the approved immutable revision-3 oracle `docs/v0.3/V03E_G0_4_API_INSPECTION_ORACLE.md` (committed-blob SHA-256 `b0c34fa1…`): Case A did not establish `TARGET_BOUND` (`TARGET_IDENTITY_UNRESOLVED` — no OpenCode endpoint is configured in `.devrelay/config.yaml`), so **0 loopback HTTP requests / 0 `GET /doc`** were issued and cases B–H were not executed; P4 remains formally unproven (evidence: `docs/v0.3/V03E_G0_4_API_INSPECTION_PROOF.md`; 0 provider/model calls, 0 OpenCode starts) | SPEC §25 |
| E38 | **G0.5** — session identity/bound checks (P6: missing, foreign, recreated, copied) | PROOF REQUIRED (local) | SPEC §25 |

## E. Remote platform proofs (gated capabilities only)

| # | Criterion | Status | Reference |
| --- | --- | --- | --- |
| E39 | **G1 / P1** — real local OpenCode `1.18.11` session-history restart proof: ids and text survive a server restart | PROOF REQUIRED (0 provider calls) | SPEC §25, §28 |
| E40 | **G2 / P2, P3, P8, P9** — real local OpenCode + **local fake** OpenAI-compatible provider: submitted-text fidelity, duplicate-identical-prompt uniqueness, session-exclusivity assumptions as far as observable, timestamp/order fidelity if used | PROOF REQUIRED (0 real provider calls) | SPEC §25, §28 |

Proof-gate rules: **no probe shopping** — one planned probe per case; a failed
proof removes the gated capability rather than triggering another probe; the gate
has **not** run and must not be run in this design round.

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
