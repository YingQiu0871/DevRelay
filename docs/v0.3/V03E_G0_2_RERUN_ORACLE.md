# DevRelay v0.3-E — G0.2 clean re-run: precommitted proof oracle (immutable pre-run manifest)

This file is the **immutable pre-run proof manifest** for the separately authorized
**clean G0.2 re-run**.  It was committed **before any G0.2 semantic case was
executed**, it is not modified after that commit, and its commit SHA and file SHA-256
are recorded in `V03E_G0_2_CLEAN_RERUN_PROOF.md`.  Its purpose is to make the oracle
provably pre-existing, so the clean run cannot be an oracle tuned to its own outcome.

## 1. Identity of this manifest

| Item | Value |
| --- | --- |
| Repository HEAD at precommit | `8a37166ebdab55fb644de08f0be8a11c7cb6e942` |
| Branch | `v0.3-e-recovery-reconciliation` |
| Package version / public tags | `0.1.0` / `v0.1.0` only; no upstream |
| Frozen semantic design candidate | `9f4a01804b9affe8938a272553df345b5a60aeed` |
| Prior authoritative state | `G0.1 / P7 = PASS`; `G0.2 = CANDIDATE PASS / NOT APPROVED` (latest independent review: `REQUEST_CHANGES — V0.3-E G0.2 PROOF`, P0 = 0, P1 = 0, P2 = 2; the evidence itself passed substantive audit and the final oracle was determined normatively correct) |
| v0.3-E status | DESIGN FROZEN / NOT IMPLEMENTED / NOT ACCEPTED / UNRELEASED |
| Other gate steps | G0.3, G0.4, G0.5, G1, G2 = NOT RUN |
| Provider / model / network budget for this re-run | **0** inference calls, **0** network requests, **0** OpenCode processes started |

## 2. Purpose

The previous G0.2 round had already completed one pass under an oracle that was later
corrected (from an implementation bug against a determinate frozen criterion, not a
post-outcome criterion change), and the disposable harness was uncommitted.  That
created a material proof-record ambiguity.  This authorized re-run therefore executes
**A–J exactly once each**, from the start, under the oracle precommitted in this
manifest, with the harness uncommitted but the **oracle fixed in the repository
history before execution**.

The re-run validates the already-determined final oracle.  It does **not** change the
frozen design, does not add identity fields, and does not re-open any G0.1 result.

## 3. Exact frozen-design sources governing the oracle

Citations below are the **actual** structures of `docs/v0.3/V03E_SPEC.md`: §8 and §12
have numbered subsections (§8.1–§8.4, §12.1–§12.6); **§9 and §11 have numbered list
items**, so they are cited as "§9 item N" / "§11 item N".

| Source | What it fixes |
| --- | --- |
| §8.4 | the only legal `recover` edges into and out of `RECOVERY_REQUIRED` (role/cycle of the attempt) |
| §9 item 1 | the identity-scoped scan: records matching the attempt identity on **operation, `session_id`, `prompt_sha256`, `prompt_chars`, `model`, `agent`** within the proven interval |
| §9 item 2 | **no silent skipping**: an unreadable, unparsable, torn or schema-invalid record is never skipped and yields `evidence_gap` |
| §9 item 3 | no truncation as proof (newest-N / max-N windows may never be used to conclude "no record") |
| §9 item 4 | interval proof: the full relevant sequence interval must be proven, or `evidence_gap` |
| §9 item 5 | outcomes: `exactly_one_match` · `multiple_matches` (→ `evidence_conflict`) · `no_record_in_proven_interval` (report-only) · `evidence_gap` |
| §9 item 6 | no inference from absence: a missing record is never proof of non-delivery |
| §11 item 1 | adoption additionally requires every §12.6 local-integrity condition |
| §11 item 2 | adoption requires **exactly one** ledger record matching the attempt identity, settled `COMPLETED`, 2xx, JSON media type, `submission_uncertain == false` |
| §11 item 6 | adoption requires that **no other DevRelay ledger operation touches that session** inside the window (see §11 below) |
| §11 item 7 | captured workspace/session/role/model identity must match |
| §11 item 8 | P1/P2/P3/P8 (+P9 if timestamps/order are used) must have passed |
| §12.2 | `prompt_sha256` is the digest of the exact prompt string; missing/invalid timestamps are never identity evidence unless P9 passes |
| §12.4 | workspace binding and session ownership are re-verified before adoption (remote; P6/G0.5) |
| §13 | `evidence_sha256` field list names `attempt.call_ids…` and `ledger.call_id` (recorded evidence, not a correlation input here) |
| §16 | crash-window matrix (a crash during submission is the scenario this proof models) |

## 4. Candidate domain (precommitted)

1. Ledger artifacts are enumerated **corruption-strictly** from the workspace ledger
   directory: complete recursive enumeration, dotfiles and `*.tmp` residues included,
   every file surfaced, no pagination/window/limit (see §9 item 3).
2. The **candidate scope** is the set of parseable records whose
   `operation == "send_prompt"` (the accepted role-prompt submission operation of the
   accepted bridge) **and** whose `session_id` equals the role session bound in the run
   document — `implementer_session_id` for an implementer attempt,
   `reviewer_session_id` for a reviewer attempt (§8.4 role/cycle, §12.4 session
   binding).  `role` is therefore supplied **only** by that binding.
3. `method` and `path` are **not** part of the candidate domain as identity
   dimensions.  They may be recorded descriptively in the evidence, but they must
   never select, filter or rank a target attempt.

## 5. Exact identity tuple (precommitted)

`(operation, session_id, prompt_sha256, prompt_chars, model, agent)` — exactly the
six values of §9 item 1, taken from the durable persisted attempt
(`attempt.role`, `attempt.cycle`, `attempt.prompt_sha256`, `attempt.prompt_chars`,
`attempt.resolved_model`, `attempt.resolved_agent` in the run document, with the
session from the role binding).

No field is added: **no** `run_id`, **no** cycle, **no** `call_id`, **no**
`method`/`path`, **no** workspace, **no** timestamp, **no** ordering index.

## 6. Verdict precedence (precommitted, first match wins)

| Order | Condition | Verdict |
| --- | --- | --- |
| 1 | any scanned artifact is unreadable/unparsable/torn/schema-invalid, or the sequence file cannot be read/validated | `CORRUPTION` (fail closed) |
| 2 | the target attempt itself lacks required durable identity (no role session binding, empty `prompt_sha256`, `prompt_chars <= 0`, or no live in-flight intent) — or the required interval/corpus completeness is unproven | `EVIDENCE_GAP` (fail closed) |
| 3 | build the complete candidate set using the six-value tuple of §5 | — |
| 4 | exactly one candidate | `MATCH` (`exactly_one_match`, §9 item 5) |
| 5 | more than one candidate | `MULTIPLE_MATCHES` → `evidence_conflict` (§9 item 5) |
| 6 | zero candidates | `NO_MATCH` (report-only `no_record_in_proven_interval`, §9 items 5/6) |

Forbidden everywhere in the decision path: scoring, fuzzy/partial matching, prompt
similarity, timestamp freshness, newest/oldest, first/last, call-id ranking,
session-only attribution, agent/model-only attribution, prompt-hash-only attribution.
A mechanical audit of the decision source for these rule tokens is part of the
evidence.

## 7. Treatment of identity-absent schema-valid records (precommitted)

A record inside the candidate scope that is **complete and schema-valid but carries no
prompt identity** (`prompt_sha256 == ""`) is classified:

**IDENTITY_ABSENT / NON-CANDIDATE** — reported in the evidence, never matched, never
treated as an absence proof, and **not** a per-record global evidence gap.

This is normative, not outcome-driven:

* §9 item 2 reserves the no-silent-skip/`evidence_gap` rule for evidence that is
  *unreadable, unparsable, torn or schema-invalid*; a complete, schema-valid record is
  none of those, it is simply a different call;
* §11 item 2 requires the **possibility** of exactly one ledger record matching the
  attempt identity, which presupposes that other (non-matching) records may coexist;
* the accepted bridge labels its session-ownership probe with the originating
  operation name (`send_prompt`) while writing no prompt identity at all, so a rule
  that turned every such record into a global gap would make every real
  `send_prompt` correlation an `evidence_gap` — that is a reporting restriction, not a
  safety rule, and the safety direction (never a positive match on weak metadata) is
  preserved without it.

`EVIDENCE_GAP` therefore remains reserved for: unreadable evidence, unparsable
evidence, torn evidence, schema-invalid evidence, an unproven evidence interval /
corpus completeness (where applicable), and the attempt-side identity itself being
insufficient.

## 8. Treatment of corruption (precommitted)

Any relevant unreadable/unparsable/torn/schema-invalid artifact in the scanned ledger
— including a residue whose readable prefix looks like the target identity — forces
`CORRUPTION` and outranks every other outcome, **even when a clean unique candidate
exists**.  The proof also records the contrast with the accepted tolerant
`read_records()`, which silently skips such artifacts (§9 item 2 is the reason the
frozen design requires a dedicated strict reader).

## 9. Treatment of duplicate matches (precommitted)

Two or more records satisfying the full tuple produce `MULTIPLE_MATCHES`
(`evidence_conflict`).  **All** candidates are surfaced and no winner is chosen: no
first/last, no newest/oldest, no lowest/lexicographically smallest `call_id`, no
scoring — none of the frozen sources authorizes such a rule.

## 10. Treatment of timestamps and order (precommitted)

`attempt.started_at` and the ledger `started_at`/`completed_at` values may be recorded
descriptively only.  They never select, rank, filter or break a tie, and no freshness
inference is permitted (§12.2; P9 remains a separate, unrun gate in G2).

## 11. Case definitions and precommitted allowed outcome sets

Cases are the fixed matrix; each is executed **once** under this manifest.

| Case | Definition | Precommitted allowed outcome set |
| --- | --- | --- |
| **A** | unique exact control: one live in-flight attempt and exactly one ledger record satisfying the complete tuple, plus unrelated records differing on required identity | `MATCH` on that record; no unrelated record may match |
| **B** | same session, distinct attempt: two calls in the same role session, only one carrying the target tuple; the other differs in at least one required identity dimension | target `MATCH`; look-alike excluded (`NO_MATCH` for the look-alike) |
| **C** | same full durable tuple on multiple calls (identical prompt digest in two cycles) | `MULTIPLE_MATCHES` / `evidence_conflict` |
| **D** | same `agent` + `model` + `session_id` but insufficient attempt identity (distinct operations) | weak-field records do not match (reported out of scope / `IDENTITY_ABSENT`); the unique real full-tuple target may still `MATCH` |
| **E** | stale-looking full-tuple duplicate from an earlier cycle (no cycle field exists) | `MULTIPLE_MATCHES` / `evidence_conflict`; never a freshness-based winner |
| **F** | wrong role and wrong operation look-alikes | look-alikes `NO_MATCH`; the target may `MATCH` if uniquely identified |
| **G** | foreign run in the same workspace: foreign different-session records excluded; a foreign call inside the target session with the full tuple | foreign different-session records excluded; the colliding full-tuple record causes `MULTIPLE_MATCHES` / `evidence_conflict` (no ownership inference) |
| **H** | duplicate full matches | `MULTIPLE_MATCHES` |
| **I** | the required prompt identity is removed from the only record that would otherwise match | `NO_MATCH` (record reported as `IDENTITY_ABSENT`); `EVIDENCE_GAP` also acceptable under this manifest; a positive `MATCH` is **not** acceptable |
| **J** | corrupt relevant look-alike (torn artifact whose readable prefix carries the target identity) alongside a clean unique candidate | `CORRUPTION` (fail closed), even though a clean unique candidate exists; `EVIDENCE_GAP` also acceptable |

Case-level semantics that are not part of the oracle but are asserted per case:
the matched candidate is reported with its `call_id`, artifact path, state, HTTP
status, `submission_uncertain` and media type; the §11 item 2 ledger half of the
adoption gate is evaluated and reported for a `MATCH`; and no case may be promoted,
added or removed during execution.

## 12. Fixed no-probe-shopping rule (precommitted)

* A–J are the fixed planned cases; **one execution each**, in order.
* No semantic rule changes after case A begins; no expected outcome set changes; no
  identity field is added; no case is added or removed; the sensitivity variant
  discussed for case I is **not** promoted into a proof case and is not executed as
  proof evidence.
* A case may be re-run **only** if a mechanical harness defect prevents it from
  reaching the precommitted assertion point (for example a serialization crash before
  oracle evaluation, fixture construction failing before the target condition exists,
  a barrier never reached, or a malformed test setup that does not instantiate the
  predeclared case).  Such attempts are recorded separately and excluded.
* If a case reaches the precommitted assertion point and produces a semantic verdict,
  **that verdict counts**: the oracle is not changed and the case is not retried to
  obtain a different semantic result.
* A semantic verdict outside the precommitted allowed set means the clean re-run
  **fails**.

## 13. Budget and side-effect constraints

0 real provider/model inference calls; 0 real network requests (the accepted
deterministic stub over `httpx.MockTransport` is used, offline); 0 OpenCode processes
started or restarted; no repository state other than this manifest and the documented
docs/evidence files; no runtime, test, dependency or version change.

## 14. Immutability

After the pre-run commit that introduces this file, it is **not modified**.  Any
correction would require a new authorization and a new manifest with its own pre-run
commit; the evidence document records this file's commit SHA and SHA-256 so a
reviewer can verify that the oracle existed before the execution.
