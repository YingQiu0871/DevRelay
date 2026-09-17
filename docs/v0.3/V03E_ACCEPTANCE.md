# DevRelay v0.3-E acceptance matrix — recovery & reconciliation (design phase)

Status: **DESIGN / NOT IMPLEMENTED / NOT ACCEPTED / UNRELEASED**

This matrix is the acceptance target for v0.3-E.  In this round **only the design
exists**: `docs/v0.3/V03E_SPEC.md`.  No recovery code, no new tool, no schema
change and no test was written; no real provider/model call was made; the accepted
v0.3-D runtime candidate `8b70610a5cdda600ef57cf8378c4f69cd33d5be4` is untouched.

Legend:

* **FROZEN (design)** — the contract is decided by the reviewed design and may be
  implemented as written.
* **PROOF REQUIRED** — the contract cannot be implemented or accepted until the
  platform proof listed in `V03E_SPEC.md` §15 is supplied.
* **NOT IMPLEMENTED** — no code exists yet (every row, this round).
* **FUTURE EVIDENCE** — the test/smoke evidence that implementation must produce.

## A. Design contract (frozen by review of this document)

| # | Criterion | Design status | Reference |
| --- | --- | --- | --- |
| E1 | The recovery problem is split into the distinct cases A–H and never collapsed into one "retryable" bucket | FROZEN (design) | SPEC §4 |
| E2 | RECONCILE / MATERIALIZE / RESUME / RETRY are defined separately, and reconcile/resume may never be implemented as retry | FROZEN (design) | SPEC §5 |
| E3 | Recovery authority is deterministic evidence **plus** an explicit external planner action; provider/reviewer prose has zero recovery authority | FROZEN (design) | SPEC §6 |
| E4 | No implicit retry, no fallback model/route, no automatic role sequencing, no automatic resume, no budget refund | FROZEN (design) | SPEC §3, §13, §20, §25 |
| E5 | Every preserved v0.3-D invariant is listed and binding, including terminal-never-reopen and reviewer-prose authority | FROZEN (design) | SPEC §3 |
| E6 | Terminal states never enter recovery; recovery tools against them are local, mutation-free and model-call-free | FROZEN (design) | SPEC §18 |
| E7 | `devrelay_get_run` stays read-only; reconciliation/materialization requires an explicit recovery action | FROZEN (design) | SPEC §17 |
| E8 | Recovery privacy: digests/ids/metadata only; no prompt/response/reasoning/credential persistence | FROZEN (design) | SPEC §22 |
| E9 | Concurrency: recovery shares the accepted per-surface execution lock; no process-wide or multi-process claim | FROZEN (design) | SPEC §21 |
| E10 | Crash-window matrix W0–W6 with durable evidence, allowed/forbidden action and final safe state per window | FROZEN (design) | SPEC §11 |
| E11 | Restart behaviour per state and per in-flight condition, with no implicit model call after a restart | FROZEN (design) | SPEC §11, §14, §16 |
| E12 | Budget/accounting table for every recovery case, with the accepted `model_turns_used` meaning preserved | FROZEN (design) | SPEC §20 |
| E13 | Route snapshot stays authoritative; current configuration is drift detection only | FROZEN (design) | SPEC §12.1 |
| E14 | Workspace/session ownership and role/session distinctness re-verified before any adoption; a copied run is not recoverable | FROZEN (design) | SPEC §19 |
| E15 | Tool surface is the minimum two-tool split (read-only reconcile + mutating resolve), with no hidden phase turn | FROZEN (design) | SPEC §17 |
| E16 | Schema/versioning policy: `schema_version` 2 for new documents, no migration, no silent defaults for safety-critical fields | FROZEN (design) | SPEC §23 |
| E17 | Backward compatibility table for every existing v0.3-D document shape, with no reinterpretation of accepted history | FROZEN (design) | SPEC §24 |
| E18 | Exactly one new run state (`RECOVERY_REQUIRED`), non-terminal and execution-frozen, with enumerated entry conditions and legal exits | FROZEN (design) | SPEC §7, §16 |
| E19 | Non-goals explicitly exclude automatic retry, daemons, WebUI/HTTP recovery, distributed locking and release work | FROZEN (design) | SPEC §25 |
| E20 | Test strategy defined before implementation (crash windows, restart, no-duplicate-submission, budget, identity, ambiguity, terminal immunity, authority, mutations, honest corpus, zero real calls) | FROZEN (design) | SPEC §26 |

## B. Proof-gated contract (cannot be implemented or accepted yet)

| # | Criterion | Design status | Reference |
| --- | --- | --- | --- |
| E21 | Reconciled **completion adoption** (materialize an already-completed turn with zero provider calls) | **PROOF REQUIRED** (P1/P2/P3) | SPEC §12, §15 |
| E22 | **Pending reply** resolution by bounded read-only reconciliation, with no waiting/polling loop | **PROOF REQUIRED** (P4) | SPEC §14, §15 |
| E23 | **Non-delivery** treated as a proof rather than a classification | **PROOF REQUIRED** (P5) | SPEC §13, §15 |
| E24 | Session identity strength against a deleted/recreated/copied session | **PROOF REQUIRED** (P6) | SPEC §19, §15 |
| E25 | Ledger settle-record integrity under a hard kill during settlement | **PROOF REQUIRED** (P7) | SPEC §15 |
| E26 | Real v0.3-E smoke scenario (remote success + controlled local persistence interruption + reconcile + adopt + zero duplicate provider call) | **PROOF REQUIRED** (P1–P4) and **NOT AUTHORIZED** | SPEC §27 |

Until E21–E25 are resolved, the only implementable, acceptable v0.3-E behaviour is
"reconcile and report, never adopt, always fail closed".

## C. Implementation acceptance (future round — no code exists)

| # | Criterion | Status | Future evidence |
| --- | --- | --- | --- |
| E27 | Read-only `devrelay_reconcile_run` produces the structured proof report (attempt identity, ledger evidence, remote candidates, checklist, blockers) with zero mutations and zero model calls | NOT IMPLEMENTED | tool tests (read-only assertions, no POST, byte-identical document) |
| E28 | `devrelay_resolve_recovery` re-derives every §12 checklist item at call time and refuses on any unproven item | NOT IMPLEMENTED | per-item refusal tests + mutation tests |
| E29 | Adoption appends the already-completed turn exactly once and moves the run only through the single legal exit; repeated resolve calls are idempotent | NOT IMPLEMENTED | idempotence tests, `evidence_sha256` tests |
| E30 | Across every recovery scenario the prompt-POST count never increases (no duplicate submission) | NOT IMPLEMENTED | ledger/`external_request_count` assertions across A–H |
| E31 | `model_turns_used` is never refunded, reset or recomputed by any recovery path or restart | NOT IMPLEMENTED | accounting assertions + mutation test |
| E32 | Route drift, foreign/missing session, copied workspace document and mismatched route/model all fail closed | NOT IMPLEMENTED | identity-matrix tests |
| E33 | Ambiguous evidence (two candidates, conflicting digests, unreadable ledger) always fails closed with the run frozen | NOT IMPLEMENTED | ambiguity tests |
| E34 | Terminal immunity: every recovery action against every terminal state is local, mutation-free and model-call-free | NOT IMPLEMENTED | terminal matrix tests |
| E35 | Reviewer prose still has zero authority in the recovery path (no prose parsing anywhere) | NOT IMPLEMENTED | prose-variant tests + AST/source assertions |
| E36 | Restart at any point never performs work implicitly and never creates budget | NOT IMPLEMENTED | restart matrix tests |
| E37 | v0.3-D documents keep their semantics (v1 never migrated/reinterpreted; `BLOCKED` stays terminal) | NOT IMPLEMENTED | compatibility corpus tests |
| E38 | Recovery-critical invariants are mutation-verified (no second submission, no refund, no adoption without proof, no terminal reopening, read-only reconcile) | NOT IMPLEMENTED | mutation back-check with recorded failure counts |
| E39 | A production-generated honest recovery corpus (cases A–H plus fake remote evidence variants) is accepted by the extended validators, and corrupted variants rejected | NOT IMPLEMENTED | corpus + differential battery |
| E40 | 0 real provider/model calls during unit/integration testing; the single bounded real smoke is separately authorized | NOT IMPLEMENTED | run records |

## D. Deferred / carried from v0.3-D acceptance

| # | Item | Why deferred |
| --- | --- | --- |
| F1 | Multi-surface / multi-process same-workspace coordination | remains unsupported; v0.3-E does not expand the locking scope (SPEC §21) |
| F2 | The carried v0.3-D P3 list (MCP SDK argument normalization and JSON-shaped prompts, non-cryptographic validation bound, inert temp files, read-only `get_run`, no fsync/power-loss durability) | unchanged by v0.3-E; kept in `docs/BACKLOG.md` §5 |
| F3 | Automatic resume / retry protocols | explicit non-goals (SPEC §25) |
| F4 | A cryptographic or append-only integrity anchor for run documents | not required by v0.3-E; would be its own hardening stage |
