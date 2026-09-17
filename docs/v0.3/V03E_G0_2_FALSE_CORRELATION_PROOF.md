# DevRelay v0.3-E — G0.2 offline run↔call false-correlation proof

Status: **G0.2 CANDIDATE PASS — REQUIRES INDEPENDENT REVIEW** (self-approval is
forbidden; the mandatory-core implementation stays **NOT AUTHORIZED** until a
separately issued implementation authorization).

* Platform proof gate: **PARTIALLY EXECUTED / NOT COMPLETE** — **G0.1 / P7 = PASS**
  (authoritative, independently approved); **G0.2 = CANDIDATE PASS / AWAITING
  INDEPENDENT REVIEW**; **G0.3, G0.4, G0.5, G1 and G2 = NOT RUN**.
* This document is evidence about the **accepted durable evidence itself** (what the
  v0.3-D run documents and the accepted v0.3-A ledger can prove about which ledger
  call belongs to which run/role/cycle/attempt).  It is **not** a proof of any future
  v0.3-E implementation: no recovery code exists.
* Real provider/model inference calls during this proof: **0**.  No OpenCode process
  was started or restarted; no network activity took place.

## 1. Identity

| Item | Value |
| --- | --- |
| Starting HEAD | `4448f92d9dc13ef9880301d2252a78c59221ac26` (branch `v0.3-e-recovery-reconciliation`) |
| Frozen semantic design candidate | `9f4a01804b9affe8938a272553df345b5a60aeed` |
| v0.3-E status during the proof | DESIGN FROZEN / NOT IMPLEMENTED / NOT ACCEPTED / UNRELEASED |
| G0.1 / P7 | **PASS** (authoritative, independently approved — `V03E_G0_1_P7_PROOF.md`) |
| G0.2 before this execution | NOT RUN |
| Package version / public tags | `0.1.0` / `v0.1.0` only (unchanged) |
| Runtime/test/version changes by this proof | **none** (`git diff 4448f92 -- src/devrelay tests pyproject.toml` is empty) |
| Real provider/model inference calls | **0** |

## 2. Accepted source inventory (read-only)

Inspected before any corpus was built (no field was assumed to exist):

| Source | What it provides |
| --- | --- |
| `src/devrelay/orchestration/models.py` | `OrchestrationRun` (schema v1: `schema_version`, `run_id`, `workspace`, `state`, `implementer_session_id`, `reviewer_session_id`, `max_cycles`, `current_cycle`, `completed_cycles`, `turn_attempts`, `model_turn_budget`, `model_turns_used`, `route_snapshot`, `last_transition`, `implementer_turns`, `reviewer_turns`, `decision_history`, `in_flight_turn`, `blocked_reason`), `TurnRecord` (`role`, `cycle`, `started_at`, `completed_at`, `prompt_sha256`, `prompt_chars`, `resolved_model`, `resolved_agent`, `route_source`, `operation_state`, `submission_attempted`, `submission_status`, `submission_uncertain`, `reply_pending`, `retry_safe`, `call_ids`, `assistant_message_ids`, `outcome`, `blocked_reason`), `RoleRouteSnapshot`, `legal_next_actions` |
| `src/devrelay/orchestration/service.py` | `_run_role` ordering: the durable in-flight intent is written **before** the call (attempt construction + counters + `store.save`, lines ~359-372), bridge evidence (`operation_state`, `submission_*`, `call_ids`, `assistant_message_ids`) is attached **after** the call returns (lines ~390-401), and the settlement write that clears `in_flight_turn` and appends the role turn happens last (lines ~418-446) |
| `src/devrelay/orchestration/store.py` | run documents at `<workspace>/.devrelay/orchestration/runs/DR-<32hex>.json`; strict validation on load and save; workspace binding; atomic replace |
| `src/devrelay/opencode/models.py` | `OpenCodeCallRecord` (`call_id`, `operation`, `state`, `method`, `path`, `session_id`, `issued`, `external_request_count`, `http_status`, `error_type`, `error`, `started_at`, `completed_at`, `duration_ms`, `response_bytes`, `response_truncated`, `submission_uncertain`, `response_media_type`, `prompt_sha256`, `prompt_chars`, `agent`, `model`); `prompt_digest()` |
| `src/devrelay/opencode/bridge.py` | `_request` ordering: `allocate_call_id()` → `ledger.begin(ISSUED)` → transport → `ledger.finish(settled)` (lines ~1212-1280); `send_prompt` (line 430): ownership probe → boundary read → single `POST .../message` carrying the prompt (the only call site that passes `prompt=`, line ~484); `_probe_ownership("send_prompt", session_id)` (line ~1386) issues a `GET /session/{id}` under the **same operation label** with **no** prompt |
| `src/devrelay/opencode/accounting.py` | `FilesystemOpenCodeLedger`: `calls/OC-NNNN.json`, create-new `begin()`, temp+replace `finish()`/`_write()`, `sequence.json`, and the **tolerant** `read_records()` that silently skips unreadable records |
| `docs/v0.3/V03E_SPEC.md` | §9 strict reader (identity-scoped scan over `operation, session_id, prompt_sha256, prompt_chars, model, agent`; no silent skipping; no truncation-as-proof; `exactly_one_match` / `multiple_matches` / `no_record_in_proven_interval` / `evidence_gap`), §11 adoption gate, §12 sources/identity, §13 `evidence_sha256` field order, §16 crash-window matrix |

## 3. Field-authority table

`Y` = present, `–` = absent, `n/a` = not applicable to that side.
"Identity strength" describes what the field can prove on its own.
All G0.2 decisions derive only from the frozen §9/§11/§12 rules; no stronger scheme
was invented.

| Field | In run state? | In ledger? | Frozen design authority | Identity strength | May positively correlate? | May only disqualify? | Not authoritative? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `run_id` | Y (`DR-<32hex>`) | **–** | §13 lists it in the evidence set; the ledger schema has no such field | none across the two sides (no join key) | **no** | n/a | **Y** (ledger-side run identity does not exist) |
| `workspace` | Y | – (only `session_id`) | §12.4 workspace binding | binding assertion only | no | n/a | Y (needs the remote session read; G0.5) |
| `role` | Y (`attempt.role`) | **–** | §8.4/§11.7 | derived only through the role→session binding | only via `session_id` | Y (wrong role session) | Y on its own |
| `cycle` | Y (`attempt.cycle`) | **–** | §8.2/§8.4 | none on the ledger side | **no** | no (cannot be checked) | **Y** (never inferred from timestamps — P9 unrun) |
| `session_id` | Y (implementer/reviewer session) | Y | §9.1 identity field, §11.7 | strong inside one run; **shared by all cycles of a role**, not unique across runs | yes, but only as one element of the full tuple | Y (different session) | Y alone (session equality is not attribution) |
| `operation` | **–** (only `operation_state` after the call) | Y | §9.1 identity field | label only — the accepted ownership probe carries the **same** label (`send_prompt`) with no prompt | yes, as part of the tuple **together with identity carriage** | Y (different operation) | **Y alone** (it is not a submission marker) |
| `method` / `path` | – | Y | not in §9.1 | corroborating evidence only | **no** (not authorized as a filter) | no | Y |
| `prompt_sha256` | Y | Y | §9.1, §12.2 | pinpoint equality of the exact prompt string (unsalted identifier, not secrecy) | yes (required) | Y (different digest) | Y alone (P2/G2 unrun; remote text fidelity unproven) |
| `prompt_chars` | Y | Y | §9.1 | corroborating equality | yes (required) | Y | Y alone |
| `model` | Y (`resolved_model` snapshot) | Y (sanitized, clipped to 128) | §9.1, §11.7 | equality with a sanitize/clip asymmetry | yes (required) | Y (mismatch → no match) | Y alone |
| `agent` | Y (`resolved_agent` snapshot) | Y (sanitized, clipped to 64) | §9.1, §11.7 | as `model` (empty on both sides is equal) | yes (required) | Y | Y alone |
| `call_id` | **Y only on a settled turn** (`TurnRecord.call_ids`); **– in a live in-flight attempt** | Y (identity + filename) | §13 (`attempt.call_ids…`, `ledger.call_id`) | exact — when it is durable, which it is **not** for the recovery input | **no for the recovery input** (see §8); if ever present, only as a lookup key with the invariants re-checked | n/a | Y for the crash boundary |
| `assistant_message_ids` | Y on settled turns | – | §11.3-§11.5 (session-history side) | session-history correlation, not ledger correlation | no (not a ledger field) | n/a | Y here |
| `state` (`ISSUED`/`COMPLETED`/…) | Y only after the call (`operation_state`) | Y | §11.2 | outcome class, not identity | no | Y for adoption (§11.2 requires settled `COMPLETED`) | Y |
| `http_status`, `response_media_type`, `submission_uncertain` | Y only after the call (`submission_*`) | Y | §11.2 | classification, not identity | no | Y for adoption | Y |
| `issued`, `external_request_count` | – | Y | accounting only | accounting | no | no | Y |
| `started_at` / `completed_at` | Y (`attempt.started_at`) | Y | §12.2 last bullet; **P9 unrun** | timestamps are **not** identity authority | **no** | no | **Y** (recorded descriptively only) |
| `route_source` | Y | – | §12.3 drift detection | route provenance, not identity | no | n/a | Y |
| counters (`turn_attempts`, `model_turns_used`) | Y | – | §8.3 accounting | accounting | no | no | Y |
| session ownership (`workspace_match`) | – | – | §12.4 / P6 | requires a remote read; G0.5 unrun | **no** (not available offline) | n/a | **Y** |

**Consequence of the table:** the only durable join that can exist between a live
in-flight attempt and the accepted ledger is the tuple
`(operation, session_id, prompt_sha256, prompt_chars, model, agent)` — exactly
§9.1 — with `role` supplied by the run document's role→session binding and with
"identity carriage" (a non-empty `prompt_sha256`) distinguishing a real submission
from the ownership probe that shares the operation label.

## 4. The proof oracle

The oracle is a **disposable proof harness** (`oracle.py` in the OS temp area; not
production code, not committed).  It was frozen before the cases ran and derives
only from §9/§11/§12.

**Scope filter** (a record is *in scope* when both hold):

1. `record.operation == "send_prompt"` (the accepted role-submission operation), and
2. `record.session_id == <role session from the run document>`
   (`implementer_session_id` for an implementer attempt, `reviewer_session_id` for a
   reviewer attempt).

**Within scope:**

* a record that carries **no prompt identity** (`prompt_sha256 == ""`) is reported as
  `identity_absent`, never matched and never treated as an absence proof;
* a record whose `prompt_sha256`/`prompt_chars` (or, after that, `model`/`agent`)
  **differ** from the attempt is a durably different call → rejected look-alike;
* a record whose `prompt_sha256`, `prompt_chars`, `model` and `agent` **all equal**
  the persisted attempt values is a **candidate**.

**Verdict precedence** (first match wins):

| Order | Condition | Verdict |
| --- | --- | --- |
| 1 | any artifact is unreadable/unparsable/schema-invalid | `CORRUPTION` |
| 2 | the attempt side lacks identity (no role session, empty digest, `prompt_chars <= 0`, or no live intent) | `EVIDENCE_GAP` |
| 3 | exactly one candidate | `MATCH` (`exactly_one_match`) |
| 4 | no candidate | `NO_MATCH` (report-only "no record in the proven interval", **never** "not submitted") |
| 5 | two or more candidates | `MULTIPLE_MATCHES` (→ `evidence_conflict`) |

For a `MATCH`, the oracle additionally evaluates the **§11.2 ledger half** of the
adoption gate (settled `COMPLETED`, 2xx, JSON media type, `submission_uncertain ==
false`) and labels it as the adoption gate only — the mandatory core never adopts.

**Forbidden rules (mechanically audited).**  `forbidden_rule_audit()` inspects the
decision source and searches for
`sorted(`, `sort(`, `max(`, `min(`, `[-1]`, `[0]`, `started_at`, `completed_at`,
`timestamp`, `elapsed`, `difflib`, `SequenceMatcher`, `fuzzy`, `similar`, `score`,
`weight`, `newest`, `oldest`, `first`, `latest`, `prefer`.
Result: **0 hits**.  The scanner sorts its artifact list by path only for
deterministic enumeration; that ordering never participates in the decision
function.  No scoring, no fuzzy matching, no nearest-timestamp, no newest/first
selection, no "same session therefore same attempt", no "same prompt hash therefore
same attempt", no "same agent/model therefore same attempt" exists anywhere in the
decision path.

## 5. Disposable corpus construction

* Root: a disposable OS temp directory (`…/dsh-g02-proof/run/<case>/`), one workspace
  per case.  Nothing under the repository, the user's real `.devrelay` state, or any
  production workspace was read or written; no user run or ledger was used.
* **Production-generated artifacts** (the recovery input and the base ledger):
  the real `OrchestrationService` + real `OrchestrationStore` + real v0.3-C role
  router + real accepted v0.3-A bridge + real `FilesystemOpenCodeLedger`, with the
  accepted deterministic OpenCode stub over `httpx.MockTransport`
  (`base_url = http://opencode.invalid`).  The **crash boundary is a real
  `SystemExit`** raised inside the stub transport at the N-th prompt submission
  (the accepted v0.3-D reachability technique): the durable in-flight intent and the
  ISSUED ledger record are production artifacts, not hand-written documents.
* Corpus baseline (per case): `start_run(max_cycles=2)` → implementer cycle 1 →
  reviewer cycle 1 → explicit `decide(request_changes)` → implementer cycle 2 dies at
  submission.  Result (measured per case): 17 published ledger records — 5 `get_session`
  probes, 3 prompt-free `send_prompt`-labelled ownership probes, 6 `read_messages`
  reads, 2 settled submissions and 1 ISSUED submission — and a run document
  in `READY_IMPLEMENTER` cycle 2 with a live implementer intent whose `call_ids` is
  **empty**.
* Look-alikes that production cannot produce (a foreign call inside the target's
  session; an identity-less record) are **constructed** through the real ledger class
  and serializer from real record payloads, re-validated against the accepted schema,
  and are labelled as constructed in each case.
* Synthetic identifiers only: no real prompt, response, reasoning or credential
  content exists anywhere in the corpus (prompts are short harness strings; the
  ledger stores only their digest and length).

## 6. Strict corpus scanner (G0.1 discipline)

* `full recursive enumeration of <ledger dir> (N file(s)); no pagination/window/limit
  applied; every file surfaced` — asserted per case: the number of scanned entries
  equals the number of files on disk (`scan["files_seen"] == scan["entries"] ==
  files on disk`), including dotfiles and `*.tmp` residues.
* Every file yields exactly one entry: a parseable call record, the sequence file, or
  `MALFORMED` with its parse error.  Nothing is skipped silently; a `MALFORMED`
  artifact forces `CORRUPTION` for the whole scan.
* Temp residues that parse as records are surfaced as records with
  `artifact_kind = temp_residue` (they can only add conflicts, never remove one).
* Interval honesty: the "proven interval" in this proof is the **full enumeration
  statement** above, not a sequence-arithmetic floor/ceiling proof.  A production
  reader must additionally prove the interval from durable sequence evidence
  (implementation-time work; recorded as a limitation, not claimed here).
* Tolerant-vs-strict contrast (as in G0.1): the accepted `read_records()` was run on
  the same corpus in case J.  It silently drops the torn artifact.

## 7. Cases A–J

Each case ran **once** in the final harness over its own complete corpus.  All ten
met the fail-closed standard (a `EVIDENCE_GAP` / `EVIDENCE_CONFLICT` /
`MULTIPLE_MATCHES` / `CORRUPTION` outcome is a *success* wherever identity is
insufficient).  `PASS` below means "the observed verdict is in the case's allowed set
and every case-level assertion held".

| Case | Expected | Observed | Candidates | Verdict | Result |
| --- | --- | --- | --- | --- | --- |
| G0.2-A | exactly one MATCH; no unrelated record matches | exactly one record: the production ISSUED submission of this attempt; the other 16 records (13 out of scope, 2 prompt-free ownership probes, 1 different-prompt look-alike) are not matched | `OC-0017` | `MATCH` | **PASS** |
| G0.2-B | target MATCH; same-session other attempt NO_MATCH | the cycle-1 implementer submission (same session/operation/route, different prompt digest) is rejected | `OC-0017` | `MATCH` | **PASS** |
| G0.2-C | same digest must not collapse two calls | two distinct calls share digest/chars/session/operation/route (cycle 1 settled + cycle 2 ISSUED) → both surfaced, no winner picked | `OC-0007`, `OC-0017` | `MULTIPLE_MATCHES` (evidence_conflict) | **PASS** |
| G0.2-D | weak equality alone must not correlate | two constructed calls sharing session + agent + model but a different operation are **not** candidates; authentic no-prompt probes are reported as `identity_absent`, never matched | `OC-0017` | `MATCH` | **PASS** |
| G0.2-E | stale call must not match; no freshness inference | the authentic earlier-cycle submission (different prompt) is rejected; a stale-looking record carrying the full tuple cannot be excluded → fail closed | `OC-0017`, `OC-0903` | `MULTIPLE_MATCHES` | **PASS** |
| G0.2-F | NO_MATCH for wrong role / wrong operation | the wrong-role record (other role session, identical digest/route) and the wrong-operation record (same session and digest) are both out of scope | `OC-0017` | `MATCH` | **PASS** |
| G0.2-G | foreign run must not be attributed to the target | the second run in the same workspace (own sessions, same ledger) is never a candidate; a foreign call inside the target session cannot be excluded → fail closed | `OC-0017`, `OC-0906` | `MULTIPLE_MATCHES` | **PASS** |
| G0.2-H | duplicates → conflict, never a pick | two records satisfy every durable correlation field; both are surfaced | `OC-0017`, `OC-0907` | `MULTIPLE_MATCHES` | **PASS** |
| G0.2-I | missing identity field → GAP/NO_MATCH, not MATCH | with the identity-critical field removed from the only matching record, the verdict degrades from MATCH (control) to no candidate at all | none | `NO_MATCH` | **PASS** |
| G0.2-J | CORRUPTION / GAP; never "skip the corrupt file and claim uniqueness" | a torn artifact whose readable prefix carries the target session and digest forces corruption although one clean unique candidate exists | `OC-0017` (not used) | `CORRUPTION` | **PASS** |

### 7.1 Case evidence detail

* **G0.2-A** — run document `265d837575315c9f8272425e35e9da30cc16968c02161dc16f56f9a873aeb9a6`
  (636-byte ISSUED record `calls/OC-0017.json`, sha256
  `38f542e8714a47fd77e1e4a8d4f5b8fcb984bf47812f795f80ad9cec085316a3`); attempt digest
  `bdf56b51b85ae866962d1e451c66b75498d079812a9809210b73cbcf29bde557`, `prompt_chars = 18`,
  `attempt.call_ids = []`.  The matched record is **ISSUED**, so the §11.2 ledger half
  is *not* met (a crash during submission is not adoptable evidence of completion).
* **G0.2-B** — same corpus shape; the rejected look-alike is the settled cycle-1
  implementer submission (`OC-0007`, digest `ff1c547022333d0e…`, 16 chars).
* **G0.2-C** — identical prompt across cycles 1 and 2
  (`ff1c547022333d0eeee376dbb8ace7adbfde3dc8ecb006b3c58e092b5885e091`, 16 chars);
  `OC-0007` and `OC-0017` are indistinguishable by every durable field, so the
  design's `multiple_matches → evidence_conflict` is the only safe outcome.  This is
  exactly what **P3** (deterministic uniqueness for identical prompts) gates for the
  optional adoption capability.
* **G0.2-D** — constructed `OC-0901` (`read_messages`) and `OC-0902` (`wait_idle`)
  carry the attempt's session/model/agent; both are out of scope by operation.  The
  authentic ownership probes (`OC-0004`, `OC-0014`, `method = GET`, no prompt
  identity) are reported as `identity_absent`.
* **G0.2-E** — `OC-0007` (cycle 1, different prompt) rejected; constructed `OC-0903`
  (full tuple, earlier timestamps) is a candidate → conflict.  No timestamp is
  consulted: the static audit is clean and the verdict contains both candidates.
* **G0.2-F** — constructed `OC-0904` (reviewer session, target digest and route) is
  out of scope by session; constructed `OC-0905` (`read_messages` with the target
  digest) is out of scope by operation.  *Limitation:* `method`/`path` are not part of
  the §9.1 tuple, so a same-operation record with a different endpoint path is not
  distinguishable; no path rule was invented.
* **G0.2-G** — a second production run (`DR-bbbb…`, sessions `ses_impl_b`/`ses_rev_b`)
  wrote into the **same** ledger (records `OC-0018`–`OC-0024`); none is a candidate.
  Run identity appears in **no** ledger artifact (asserted by byte-scanning every
  scanned artifact for both run ids).  The constructed `OC-0906` (foreign call inside
  the target's session) forces a conflict.
* **G0.2-H** — `OC-0017` (ISSUED) and constructed `OC-0907` (ISSUED) are identical on
  every durable field; the result contains both and no choice field of any kind.
* **G0.2-I** — control (intact corpus): `MATCH` on `OC-0017`.  After removing
  `prompt_sha256`/`prompt_chars` from that record: no candidate, verdict `NO_MATCH`,
  the record reported as `identity_absent`.  *Recorded sensitivity observation (not a
  second case):* adding an **additional** intact full-identity record (`OC-0910`)
  yields `MATCH` on `OC-0910` while the identity-less record stays reported under
  `identity_absent` — see §12 for the interpretation decision this exposes.
* **G0.2-J** — torn `calls/OC-0909.json` (569 bytes; sha256
  `2da9516f5ca19300b54e1c94b134905651dc00eecf7d578bfc8fe137cbf8091c`;
  `JSONDecodeError: Unterminated string`) plus an inert temp residue
  `calls/.OC-0004.json.tmp`.  Strict scan: 20 files / 18 parseable records / 1 residue
  / 1 malformed → `CORRUPTION`.  Tolerant `read_records()` on the *same* corpus
  returned 17 records and would have reported a unique `MATCH` on `OC-0017`: the
  contrast is the concrete reason the frozen design requires a dedicated
  corruption-strict reader (§9.2).

## 8. Special case — `call_id`

**Finding: a live in-flight attempt never durably contains the ledger `call_id`
before/at the crash boundary.**

Proof from the accepted source ordering:

1. `service.py::_run_role` builds the `TurnRecord` with role/cycle/prompt digest/route
   only, sets `run.in_flight_turn = attempt`, increments the counters and calls
   `store.save(run)` **before** the bridge is entered (`call_ids` is still `[]`).
2. `bridge.py::_request` allocates the call id (`allocate_call_id()`), writes the
   ISSUED record (`ledger.begin`), performs the transport request and settles the
   record (`ledger.finish`), and returns the id to the caller.
3. Back in `_run_role`, `attempt.call_ids` is assigned only **after** the bridge call
   returns, and the mutated attempt reaches the disk only in the **settlement write**
   that also clears `in_flight_turn` and appends the turn to role history.
4. Therefore a process death anywhere between the durable intent and that settlement
   write leaves exactly the state proven in every case below: a live in-flight intent
   with `call_ids == []`, `operation_state == ""`, `submission_attempted == false`,
   plus the ISSUED ledger record (if the POST had been entered).

Consequences recorded: the association "attempt ↔ `call_id`" becomes durable **only
together with the settlement** (i.e. when the run is no longer in an in-flight state),
so `call_id` cannot be used as a lookup key by the recovery reader for the recovery
input; and there is no accepted ordering in which the id is persisted earlier.  If it
were ever available (settled turn), it would still be a lookup key only — every §9.1
identity value plus the document invariants would have to agree; a bare `call_id`
match is never sufficient on its own.  **No `call_id` was retrofitted into the
oracle**: the oracle consumes no `call_id` input (it only reports the ids of the
records it found).

## 9. Special case — `run_id`

**Finding: `run_id` is absent from the OpenCode call ledger.**  `OpenCodeCallRecord`
has no run/workspace field (`extra="forbid"`), and a byte scan of every artifact in
case G found neither run id anywhere in the ledger.  There is therefore **no direct
run↔ledger identity**, and the proof does not claim one.

The weaker relation that actually exists is: `run document → role session id` (one
of exactly two ids bound to the run) `+` the §9.1 identity tuple carried by a
submission record.  Consequences: (a) a call from another run in the same workspace
can only be excluded by the session binding, never by run identity; (b) if a foreign
call shares the target's session *and* the full tuple, the durable evidence cannot
separate them (case G) → fail closed; (c) positive correlation stays bounded to
"exactly one record matching the attempt identity in the role session", which is
precisely §9.1 and §11.2.

## 10. Session identity

* `session_id` is an OpenCode session identifier, **not** a run id and **not** an
  attempt id.  In the accepted runtime the run document binds exactly one session per
  role (`implementer_session_id`, `reviewer_session_id`, both required, distinct —
  `start_run` refuses an equal pair), and the same role session is reused across all
  cycles of that run.
* Measured in the corpus: the implementer session carries the cycle-1 and cycle-2
  submissions, the probes and the reads (case A: `ses_impl` on `OC-0001`…`OC-0017`);
  the foreign run's calls live in the same ledger under different session ids.
* Therefore session equality is **necessary but not sufficient**: it never identifies
  a cycle (case E), never separates identical prompts (case C), and never proves run
  ownership when a foreign writer uses the same session (case G).
* Session **ownership** (`workspace_match`) requires a remote read and is **not**
  proven offline; the mandatory core never depends on it, and adoption remains gated
  by G0.5/P6.  This proof does **not** establish P8 session exclusivity.

## 11. Timestamps / order

Timestamps (`attempt.started_at`, `ledger.started_at`/`completed_at`) were recorded
descriptively only and were **never** used to select, rank or break a tie:

* the decision source contains no timestamp/ordering token (static audit, 0 hits);
* case E's stale-looking record with the full tuple produced `MULTIPLE_MATCHES`
  instead of "the newer one wins";
* case H surfaces both duplicates instead of the earliest/latest call id;
* §12.2 forbids timestamp identity evidence unless **P9** passes, and P9 remains a
  separate, unrun gate (G2).

## 12. Ambiguity findings and interpretation decisions requiring review

1. **Ownership probe labelled as a submission.**  The accepted bridge issues the
   session-ownership probe as `operation = "send_prompt"`, `method = GET`,
   `path = /session/{id}`, with no prompt identity (measured: `OC-0004`, `OC-0014`,
   `OC-0021`).  A reader that keyed on the operation label alone would see a
   same-operation, same-session record for every turn.  The oracle therefore requires
   **identity carriage** (non-empty `prompt_sha256`) before a record can match, and
   reports probe-like records under `identity_absent`.
2. **Interpretation decision (flagged for the independent review).**  A complete,
   schema-valid, in-scope record that carries **no** prompt identity is treated as a
   non-match (reported, never matched) rather than as a per-record evidence gap.
   Rationale: §9.2's no-silent-skip rule names *unreadable, unparsable, torn or
   schema-invalid* records — this record is none of those; it is a different,
   complete call, and the accepted code path can only produce prompt-free
   `send_prompt` records (the submission path requires a non-empty prompt and always
   writes the digest).  The stricter reading (any identity-less in-scope record ⇒
   `evidence_gap`) would make **every** real `send_prompt` correlation an evidence gap,
   because every submission is preceded by such a probe.  Both readings are reported:
   case I's sensitivity observation shows the stricter corpus variant, and the
   difference is confined to *reporting* versus *failing closed* — neither reading can
   attribute a call to a run on weak metadata, and no reading that was tested produced
   a false positive.  The reviewer may require the stricter rule; that would be a
   design-level tightening, not a G0.2 defect.
3. **Cycle/attempt ambiguity is real and unremovable offline** (cases C, E): the ledger
   has no cycle, attempt, role or run field.  Ambiguity resolves as
   `evidence_conflict`, which the frozen core handles by never adopting
   (`mark_unrecoverable` remains available).
4. **`model`/`agent` are compared as literals across a sanitize/clip asymmetry**
   (the ledger stores `sanitize(...)` clipped to 128/64; the run stores the raw
   snapshot).  A mismatch can only remove a candidate (fail closed); it can never
   create one.  A pathological (very long or sanitized) model string could therefore
   turn a true correlation into `NO_MATCH` — recorded as a limitation, not a safety
   defect.
5. **`method`/`path` are not part of the §9.1 tuple** (case F): the accepted ledger
   does distinguish the probe from the submission by method/path, but the frozen
   identity list does not include them, so no path rule was invented and no claim is
   made about same-operation/other-path records.
6. **Interval provenance** is the enumeration statement of §6, not a sequence-floor/
   ceiling proof (same class of disclosure as G0.1's P3-4).

## 13. Invalid attempts and no-probe-shopping record

`A`–`J` are the fixed planned cases; each ran once in the final harness and no case
was re-run to search for a passing configuration.  Harness-invalid attempts are
recorded here in full and **excluded from the evidence of record**:

1. **Aborted (no verdicts)** — case J's evidence serialization crashed because the
   inventory helper parsed every `OC-*.json` file, including the deliberately torn
   artifact.  Fixed by making the helper record unreadable artifacts instead of
   raising.  No case verdict from this attempt is used.
2. **Case J precondition not met** — the torn artifact was first produced by cutting
   the record at a fixed 55 % offset, which landed *before* the `prompt_sha256` line,
   so the artifact's readable prefix did not carry the target identity and the case's
   own precondition ("a malformed artifact whose filename or surrounding metadata
   makes it look relevant") was not satisfied.  The cut was moved to immediately after
   the digest line.  Case J's verdict from that attempt is excluded.
3. **Full run excluded (harness rule not derived from the frozen text)** — the first
   complete pass applied an invented rule ("any in-scope record without a prompt
   identity ⇒ per-record evidence gap"); because the accepted ownership probe is such
   a record, all cases except I returned `EVIDENCE_GAP`.  The rule was corrected to the
   §9.1/§9.2 reading documented in §4/§12.  **This correction increases `MATCH`
   outcomes and is therefore explicitly flagged for independent scrutiny**; the
   reasoning from the frozen text is recorded in §12.2, both readings are reported,
   and no verdict from that pass is used.
4. **Case-level harness selection bug** — cases B and E initially selected the
   prompt-free probe record as their "earlier-cycle look-alike", so the intended
   rejection was not exercised; the selection now requires a prompt-carrying record
   with a different digest.  The cases' expected properties were unchanged.

No extra look-alike case was added after observing any failure, and no case's
expected outcome was relaxed: the only outcome-set adjustment is case I's, where the
case text itself allows `EVIDENCE_GAP / NO_MATCH` and the corpus now removes the
identity field from the record that would otherwise match (the earlier corpus, which
additionally kept an intact record, is reported as the sensitivity observation
instead).

## 14. Limitations and non-claims

The G0.2 candidate result does **not** establish any of the following:

* that v0.3-E recovery exists, is implemented, or is correct — nothing was
  implemented; the oracle is disposable proof code, not production code;
* that the future production strict reader will behave identically — the design
  requires it to, and it must be implemented and tested separately (G0.1/P7 proves the
  local persistence assumptions only);
* **P1** (session-history durability), **P2** (submitted-text fidelity), **P3**
  (identical-prompt uniqueness), **P8** (session exclusivity) or **P9**
  (timestamp/order fidelity) — all remain unproven and are G1/G2 work;
* session ownership / workspace binding (`workspace_match`) or P6 — not provable
  offline;
* that a `MATCH` means the provider completed anything: the crash-boundary match is an
  **ISSUED** record; adoption requires the §11.2 settled/2xx/JSON/uncertain-false
  evidence plus the session-history conditions, and remains **DISABLED**;
* that `adopt_completed_turn` is enabled or authorized, or that mandatory-core
  implementation is authorized;
* delivery truth, remote submission identity, `fsync`/power-loss durability, or any
  G0.3–G2 step (none has run);
* that the interval was proven by sequence arithmetic (see §6/§12.6).

Additional disclosures: the harness, oracle and per-case evidence live in a
disposable OS temp directory (`…/dsh-g02-proof/{oracle.py,corpus.py,run_cases.py,
evidence/*.json}`) and are **not** committed into `src/` or `tests/`; they are not
reconstructed or re-run after the fact (same auditability limitation as G0.1's P3-3).
Case-level numbers quoted above are the values recorded by the single evidence run.

## 15. Provider / model calls

**0** real provider/model inference calls; **0** OpenCode processes started or
restarted; **0** network requests (all HTTP is the accepted offline stub transport
against `http://opencode.invalid`); the ledger and run documents are workspace-local.

## 16. Candidate conclusion

**G0.2 CANDIDATE PASS — REQUIRES INDEPENDENT REVIEW.**  All ten planned cases A–J
behaved fail-closed:

* a unique exact correlation **is** possible when, and only when, exactly one ledger
  record matches the §9.1 identity tuple in the run's role session (case A: `MATCH`);
* every ambiguity resolved to a fail-closed outcome — same session/different attempt
  → `NO_MATCH` (case B); identical prompt digests → `MULTIPLE_MATCHES` (case C); weak
  field equality → no candidate (case D); stale/unprovable cycle → conflict (case E);
  wrong role/operation → `NO_MATCH` (case F); foreign run → conflict, never attributed
  (case G); duplicates → conflict with no winner (case H); missing identity field →
  `NO_MATCH` (case I); corrupt look-alike → `CORRUPTION` even though a clean unique
  candidate exists (case J);
* no weak metadata (session, agent, model, prompt digest, proximity, freshness) ever
  produced a positive attribution on its own, and no timestamp took part in any
  decision.

Two findings are central and must be carried into the implementation and its review:
**the ledger carries no run identity and no cycle/attempt identity**, and **the
`call_id` is not durable in a live in-flight attempt** — so positive correlation is
bounded to "exactly one matching record in the role session", and everything else must
stay `evidence_gap` / `evidence_conflict` with `mark_unrecoverable` as the always
available exit.

Independent approval of this candidate is required before **G0.2 = PASS** may be
recorded; until then **G0.2 = CANDIDATE PASS / AWAITING INDEPENDENT REVIEW**,
**G0.1 / P7 = PASS**, **G0.3–G0.5/G1/G2 = NOT RUN**, the platform proof gate stays
**PARTIALLY EXECUTED / NOT COMPLETE**, mandatory-core implementation stays **NOT
AUTHORIZED**, and `adopt_completed_turn` stays **DISABLED**.
