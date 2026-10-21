# DevRelay v0.3-E — G0.2 clean re-run proof (precommitted oracle)

Status: **G0.2 = PASS — AUTHORITATIVE PASS / INDEPENDENTLY APPROVED**.  The
independent clean-rerun review issued **APPROVE V0.3-E G0.2 FALSE-CORRELATION PROOF**
with **P0 = 0, P1 = 0, P2 = 0**.  This PASS comes from that independent review of the
clean re-run, **never** from executor self-approval.

* Platform proof gate: **PARTIALLY EXECUTED / NOT COMPLETE** — `G0.1 / P7 = PASS` and
  `G0.2 = PASS` (both authoritative and independently approved); `G0.3`, `G0.4`,
  `G0.5`, `G1`, `G2` are **NOT RUN**; there is no "proof gate passed" and no
  "proof gate complete" status.
* Implementation: **NOT AUTHORIZED** — G0.1/P7 satisfied the frozen mandatory-core
  hard prerequisite and G0.2 has now independently passed its offline false-correlation
  proof; neither fact, alone or together, constitutes implementation authorization.
* `adopt_completed_turn`: **DISABLED** (G0.2 does not prove P8, P9, remote session
  ownership, provider completion, delivery truth or adoption eligibility; G1/G2 unrun).

This document is the evidence record of the **separately authorized clean G0.2
re-run**.  The oracle was frozen in the repository **before any case was executed**
(`V03E_G0_2_RERUN_ORACLE.md`, pre-run commit `12ea1b7`), and all ten fixed cases A–J
were executed **once each** under it.  The earlier G0.2 record
(`V03E_G0_2_FALSE_CORRELATION_PROOF.md`) is **substantively unchanged** as history:
its historical evidence and results are preserved, and only its citation references
were corrected and a narrow historical pointer added.  This re-run neither rewrites it
nor pretends to be it.

## 0. Authoritative status, independent approval and chronology

**Independent approval (recorded by the later bookkeeping round, from the
already-issued review):** `APPROVE V0.3-E G0.2 FALSE-CORRELATION PROOF`, final
severities **P0 = 0, P1 = 0, P2 = 0**.

The independent clean-rerun review confirmed:

* the pre-run oracle commit genuinely preceded execution;
* the oracle SHA-256 was independently recomputed;
* the oracle was immutable between the pre-run commit and the evidence commit;
* the oracle was normatively faithful to the frozen design;
* the identity-absent treatment was accepted;
* A-J were each executed once;
* all observed results were inside the precommitted allowed sets;
* no semantic rule changed after execution began;
* the manifest-binding warning was only a mechanical casing mismatch;
* **P2-1 closed** and **P2-2 closed**;
* the clean re-run stands on its own and does **not** rely on the original `8a37166`
  execution for PASS.

**Chronology (not flattened):** original G0.2 execution (commit `8a37166`) → original
candidate result → first independent `REQUEST_CHANGES` → P2-1 / P2-2 identified →
separately authorized clean re-run → `12ea1b7` pre-run oracle → clean A-J execution →
`7908ace` clean candidate pass → independent clean-rerun review **APPROVE** →
**authoritative `G0.2 = PASS`** → the bookkeeping commit that records it.

**Claim boundary (unchanged by the approval):** the authoritative G0.2 claim is only
that, given the durable local fields actually available and the frozen correlation
rules, offline correlation fails closed — one bounded `MATCH` only on the complete
durable identity tuple; ambiguous, duplicate or foreign evidence never yields a
guessed winner; identity-insufficient evidence never causes false attribution; corrupt
relevant evidence fails closed; timestamp/order never resolves ambiguity.  G0.2 does
**not** prove remote session ownership, P8, P9, provider completion, delivery truth,
adoption eligibility, future recovery correctness, or any G0.3-G2 step.

## 1. Identity of this proof

| Item | Value |
| --- | --- |
| Original starting HEAD for this round | `8a37166ebdab55fb644de08f0be8a11c7cb6e942` |
| Pre-run oracle commit | `12ea1b74066ee7412b6ee1f3633fe05fecf088a3` (`docs(v03e): freeze G0.2 clean-rerun oracle`), parent `8a37166ebdab55fb644de08f0be8a11c7cb6e942` |
| Pre-run oracle file SHA-256 | `e900f7a3b7d81b12561cf0280424b0454bb87b8dda2e2ee48cba220211295ded` (`docs/v0.3/V03E_G0_2_RERUN_ORACLE.md`, verified unchanged at execution time and after the binding re-check) |
| Branch | `v0.3-e-recovery-reconciliation` |
| Frozen semantic design candidate | `9f4a01804b9affe8938a272553df345b5a60aeed` |
| HEAD at execution start (verified by the harness) | `12ea1b74066ee7412b6ee1f3633fe05fecf088a3`, worktree clean |
| Proof start (UTC) | `2026-09-17T23:35:41Z` |
| Proof completion (UTC) | `2026-09-17T23:35:43Z` (total ≈ 2 s; per-case artifacts are ≈ 0.15 s apart, recorded by file times) |
| v0.3-E status | DESIGN FROZEN / NOT IMPLEMENTED / NOT ACCEPTED / UNRELEASED |
| G0.1 / P7 | **PASS** (authoritative, independently approved) |
| G0.3–G0.5 / G1 / G2 | **NOT RUN** |
| Real provider/model inference calls | **0** |
| Real network requests | **0** (accepted deterministic stub over `httpx.MockTransport`, `base_url = http://opencode.invalid`) |
| OpenCode processes started/restarted | **0** |
| Runtime / test / dependency / version change | **none** (`git diff 4448f92 -- src/devrelay tests pyproject.toml` is empty before and after) |

## 2. Precommitted oracle (frozen before execution)

The normative pre-run manifest is `docs/v0.3/V03E_G0_2_RERUN_ORACLE.md` (commit
`12ea1b7`, SHA-256 above).  Its rules, in summary:

* **Citations are the SPEC's real structures**: §8.4, **§9 items 1–6**, **§11 items
  1, 2, 6, 7, 8**, §12.2, §12.4, §12.6, §13, §16 (the SPEC has no §9.x/§11.x
  subsections; those were mis-cited in the earlier record and are corrected in this
  round's P3 cleanup, see §12).
* **Candidate domain**: corruption-strict enumeration of the workspace ledger; the
  candidate scope is records with `operation == "send_prompt"` **and**
  `session_id ==` the role session bound in the run document (implementer/reviewer),
  so `role` comes only from that binding.  `method`/`path` are recorded descriptively
  and are **not** identity dimensions.
* **Identity tuple** (exactly §9 item 1):
  `(operation, session_id, prompt_sha256, prompt_chars, model, agent)`.  No `run_id`,
  no cycle, no `call_id`, no `method`/`path`, no workspace, no timestamp was added.
* **Verdict precedence**: `CORRUPTION` → `EVIDENCE_GAP` (attempt-side identity
  insufficient, or unproven interval/completeness) → build the complete candidate set →
  one candidate `MATCH`; more than one `MULTIPLE_MATCHES` (`evidence_conflict`);
  zero `NO_MATCH` (report-only `no_record_in_proven_interval`).
* **Identity-absent rule**: a complete, schema-valid in-scope record that carries no
  prompt identity is `IDENTITY_ABSENT / NON-CANDIDATE` — reported, never matched,
  never an absence proof, and **not** a per-record global `EVIDENCE_GAP`.
  `EVIDENCE_GAP` stays reserved for unreadable/unparsable/torn/schema-invalid
  evidence, an unproven interval/completeness, or attempt-side identity insufficiency.
  Rationale (§9 item 2 names only unreadable/unparsable/torn/schema-invalid evidence;
  §11 item 2 requires that exactly one matching record may coexist with non-matching
  records): the accepted bridge labels its session-ownership probe with the
  originating operation name and writes no prompt identity, so the stricter reading
  would turn every real `send_prompt` correlation into an evidence gap — a reporting
  restriction, not a safety rule.
* **Corruption** outranks every other outcome, including a clean unique candidate.
* **Duplicates** → `MULTIPLE_MATCHES`; all candidates surfaced, no winner.
* **Timestamps/order**: descriptive only; never a selector, ranker or tie-break
  (§12.2; P9 unrun).
* **No-probe-shopping rule** and the **0** provider/model/network budget.

Mechanical binding of the executed rules to the committed manifest (harness
`manifest_binding_check()`): the manifest SHA-256 matched the expected value, HEAD at
execution was the pre-run commit with the expected parent, the worktree was clean at
start, and all required rule phrases were present.  The in-run phrase check compared
**case-sensitively** and reported one "missing" phrase (`No semantic rule changes
after case A begins` written with a capital N); the read-only re-check with a
case-insensitive comparison is clean.  This is recorded as mechanical observation 1 in
§11 — it is a harness wording defect in the *check*, not an oracle rule and not a case
assertion, and it changed no verdict.

## 3. Accepted source inventory

Unchanged from the earlier G0.2 round (no runtime file was modified): the persisted
run document and `TurnRecord` model (`src/devrelay/orchestration/models.py`), the
`_run_role` write ordering (`orchestration/service.py`: durable in-flight intent
before the call, bridge evidence after it, settlement write last), the durable store
(`orchestration/store.py`), the accepted ledger record model and digest helper
(`opencode/models.py`), the bridge `_request` ordering and `send_prompt` /
`_probe_ownership` paths (`opencode/bridge.py`), and the accepted ledger persistence
(`opencode/accounting.py`).  This round additionally verified the **actual structure**
of the frozen SPEC so that every citation is exact: subsections exist as §8.1–§8.4 and
§12.1–§12.6, while §9 and §11 are numbered list items.

## 4. Disposable corpus

Same construction discipline as the earlier round, in a **new** disposable OS temp
root (`…/dsh-g02-rerun/`), one workspace per case, nothing from the repository or any
real DevRelay workspace:

* **Production-generated** recovery input and base ledger: real orchestration service
  + real store + real v0.3-C role router + accepted v0.3-A bridge + real
  `FilesystemOpenCodeLedger`, with the accepted deterministic stub over
  `httpx.MockTransport`; the crash boundary is a real `SystemExit` inside the stub
  transport at the N-th prompt submission.  Per case: 17 published records
  (5 `get_session` probes, 3 prompt-free `send_prompt`-labelled ownership probes,
  6 reads, 2 settled submissions, 1 **ISSUED** submission) and a cycle-2
  `READY_IMPLEMENTER` document whose live implementer intent has `call_ids == []`.
* **Constructed** look-alikes that production cannot produce (a foreign call inside
  the target's session, an identity-less record) are written through the real ledger
  class/serializer from real payloads and re-validated against the accepted schema.
* Synthetic identifiers/digests only: no real prompt, response, reasoning or
  credential content anywhere.

## 5. Strict scanner

Complete recursive enumeration of the ledger directory, asserted per case
(`entries == files on disk`), dotfiles and `*.tmp` residues included, malformed
artifacts surfaced (never skipped), no pagination/window, the complete artifact set
handed to the oracle.  **Limitation kept explicit**: enumeration-at-scan-time is *not*
a stronger sequence-arithmetic floor/ceiling proof; the production reader must prove
the interval from durable sequence evidence.

## 6. Cases A–J: expected vs observed (one execution each)

`Semantic PASS` means the observed verdict lies in the precommitted allowed set **and**
every case-level assertion held.  The **Precommitted allowed** column reproduces the
**immutable pre-run manifest** (`V03E_G0_2_RERUN_ORACLE.md` §11), which is
authoritative; §12 records the P3-A/P3-B clarification about the post-run reproduction
and the manifest's global precedence.

| Case | Precommitted allowed | Observed | Candidates surfaced | Semantic result |
| --- | --- | --- | --- | --- |
| A — unique exact control | `MATCH` | `MATCH` | `OC-0017` | **PASS** |
| B — same session, distinct attempt | `MATCH` (look-alike excluded) | `MATCH` | `OC-0017`; `OC-0007` rejected on prompt identity | **PASS** |
| C — same full tuple on multiple calls | `MULTIPLE_MATCHES` (→ `evidence_conflict`) | `MULTIPLE_MATCHES` | `OC-0007`, `OC-0017` | **PASS** |
| D — same agent/model/session, insufficient identity | `MATCH` | `MATCH` | `OC-0017`; `OC-0901`/`OC-0902` out of scope; probes `IDENTITY_ABSENT` | **PASS** |
| E — stale-looking full-tuple duplicate | `MULTIPLE_MATCHES` (→ `evidence_conflict`); never a freshness-based winner | `MULTIPLE_MATCHES` | `OC-0017`, `OC-0903`; `OC-0007` rejected | **PASS** |
| F — wrong role / wrong operation | `MATCH` (look-alikes `NO_MATCH`) | `MATCH` | `OC-0017`; `OC-0904` out of scope (session), `OC-0905` out of scope (operation) | **PASS** |
| G — foreign run / same workspace | foreign different-session records excluded; the colliding full-tuple record → `MULTIPLE_MATCHES` (→ `evidence_conflict`) | `MULTIPLE_MATCHES` | `OC-0017`, `OC-0906`; foreign `OC-0021`/`OC-0024` out of scope | **PASS** |
| H — duplicate full matches | `MULTIPLE_MATCHES` | `MULTIPLE_MATCHES` | `OC-0017`, `OC-0907` | **PASS** |
| I — prompt identity removed from the only candidate | `NO_MATCH` / `EVIDENCE_GAP` | `NO_MATCH` | none; `OC-0017` reported `IDENTITY_ABSENT` | **PASS** |
| J — corrupt relevant look-alike | `CORRUPTION` / `EVIDENCE_GAP` | `CORRUPTION` | `OC-0017` (clean, not used) | **PASS** |

Case-level evidence detail (recorded values from the single clean run):

* **A** — run document `dceba5ff64bf416a5d7af31ab38a963a96e9547e9a917a2f4e8cfdba3ead09ca`;
  attempt digest `bdf56b51b85ae866962d1e451c66b75498d079812a9809210b73cbcf29bde557`
  (`prompt_chars = 18`); matched ISSUED record `calls/OC-0017.json`, 636 B, sha256
  `f9c816aec2efff87f7a46afd626c623bbfe1b0acebb4ef19a6ee32af3fb77ad4`; the two
  prompt-free ownership probes `OC-0004`/`OC-0014` are `IDENTITY_ABSENT`; §11 item 2
  ledger half not met (`settled_completed = false`, ISSUED).
* **B** — the rejected look-alike is the settled cycle-1 implementer submission
  `OC-0007` (same session/operation/route, different digest).
* **C** — identical prompt in cycles 1 and 2
  (`ff1c547022333d0eeee376dbb8ace7adbfde3dc8ecb006b3c58e092b5885e091`, 16 chars):
  `OC-0007` and `OC-0017` are indistinguishable on every durable field → conflict.
* **D** — constructed `OC-0901` (`read_messages`) and `OC-0902` (`wait_idle`) share
  session + model + agent with the attempt and are out of scope by operation; the
  authentic probes are `IDENTITY_ABSENT`; the target remains the single candidate.
* **E** — the authentic earlier-cycle call is rejected; constructed `OC-0903` (full
  tuple, later timestamps) cannot be excluded (no cycle field) → conflict; no
  freshness rule exists (static audit clean).
* **F** — wrong-role record `OC-0904` out of scope by session; wrong-operation record
  `OC-0905` out of scope by operation; neither is attributed.
* **G** — a second run `DR-bbbb…` (`READY_REVIEWER`, sessions `ses_impl_b`/`ses_rev_b`)
  wrote `OC-0021`/`OC-0024` into the **same** ledger; both are out of scope by session;
  a byte scan of every ledger artifact found neither run id; the constructed
  in-session full-tuple record `OC-0906` forces `evidence_conflict`.
* **H** — `OC-0017` (ISSUED) and constructed `OC-0907` (ISSUED) satisfy every durable
  field; both surfaced; no selection field exists in the result.
* **I** — mechanical precondition asserted before removing the field: exactly one
  record carried the complete tuple (`OC-0017`, the ISSUED submission).  After the
  required prompt identity was removed, no candidate remained → `NO_MATCH`, and the
  record is reported as `IDENTITY_ABSENT`.  (The intact-corpus `MATCH` behaviour is
  case A; no sensitivity variant was executed — see §13.)
* **J** — torn `calls/OC-0909.json` (569 B, sha256
  `3fd845f551eaa19c2243f5ee84f095ba21267e12ca5e28b16d37a49e6528d75b`, reader-invalid
  JSON) whose readable prefix carries the target session and digest, plus the inert
  temp residue `calls/.OC-0004.json.tmp` → `CORRUPTION` although one clean unique
  candidate existed.  **Recorded contrast** (not a proof case, not part of the
  oracle): the accepted tolerant `read_records()` on the same corpus returned 17
  records and would have reported a unique `MATCH` — the concrete reason the frozen
  design requires the corruption-strict reader (§9 item 2).

## 7. Aggregate result

* Cases executed: **10 / 10**, once each, in order A–J, under the unchanged oracle.
* Semantic verdicts inside their precommitted allowed sets: **10 / 10**.
* Case-level assertions failed: **0**.
* False positive attributions: **0**.  Ambiguous winners selected: **0**.
  Timestamp/order tie-breaks: **0**.  Prompt-hash-only attributions: **0**.
  Session-only attributions: **0**.
* Corruption of relevant evidence always failed closed (case J; and any malformed
  artifact in any corpus would have forced `CORRUPTION` by precedence).
* Oracle module SHA-256 at start and at end of execution: identical
  (`4b1edebeb70a7ed2076d777ebdce778b51b610355daaac46e469ec6135f69507`), i.e. no
  semantic rule changed while the cases ran.
* Mechanical static audit of the decision source for forbidden rules (scoring, fuzzy/
  similarity, ordering, timestamps, first/last/newest/oldest, call-id ranking): **0**
  hits.

## 8. `call_id` finding (unchanged and re-confirmed)

A live in-flight attempt does **not** durably contain the ledger `call_id` before/at
the crash boundary.  Accepted source ordering: the durable intent is saved before the
bridge is entered (`call_ids` empty) → `bridge._request` allocates the id and records
ISSUED/settled → the id is assigned to the attempt only after the call returns → it
reaches disk only in the settlement write that also clears `in_flight_turn` and
appends the role turn.  Measured in every case of this clean run: the persisted
attempt has `call_ids == []`.  `call_id` was **not** used as an oracle input (it is
reported as evidence of the records found).

## 9. `run_id` finding (unchanged and re-confirmed)

`run_id` is **absent from the ledger** (no such field in the accepted record model;
byte scan of every ledger artifact in case G found neither run id).  There is no direct
run↔ledger identity; the real relation is the run's role→session binding plus the
§9 item 1 tuple, so positive correlation stays bounded to "exactly one matching record
in the role session".

## 10. `session_id` finding (unchanged and re-confirmed)

`session_id` is an OpenCode session identifier, not a run or attempt id: one session
per role per run, reused across cycles, distinct across roles.  It is necessary but
never sufficient (no cycle identity, no identical-prompt disambiguation, no ownership
proof against a foreign writer).  Session ownership (`workspace_match`) needs a remote
read and is **not** proven offline; P8 remains unproven.

## 11. Identity-absent interpretation, timestamps, mechanical observations

* **Identity-absent** is the accepted interpretation of the frozen rules: complete,
  schema-valid in-scope records with no prompt identity are reported as
  `IDENTITY_ABSENT / NON-CANDIDATE` and never poison a valid unique tuple match; the
  frozen identity tuple is unchanged.  (Cases A, D, I evidence.)
* **Timestamps/order**: recorded descriptively only; no decision used them (cases E/H
  produced conflicts instead of freshness winners; static audit clean).
* **Mechanical observation 1** (non-semantic): the harness binding check compared the
  manifest phrases case-sensitively and reported one "missing" phrase; a read-only,
  case-insensitive re-check is clean and the manifest file is unchanged (SHA-256 still
  `e900f7a3…`).  It is not a case-level harness defect: no case aborted, no case was
  re-run, and no verdict was affected.
* **Invalid harness attempts: none.**  Every case reached its precommitted assertion
  point on its single execution.

## 12. P3 documentation cleanup performed in this round

* Incorrect subsection references in the earlier record
  (`V03E_G0_2_FALSE_CORRELATION_PROOF.md`: `§9.1`, `§9.2`, `§11.2`, `§11.3-§11.5`,
  `§11.7`) were replaced by the **actual** frozen structures (`§9 item 1`,
  `§9 item 2`, `§11 item 2`, `§11 items 3-5`, `§11 item 7`), with a note that the SPEC
  uses numbered list items for §9/§11.
* The P2-1 status contradiction was fixed by anchoring the G0.1 proof document's
  status block as **round-scoped** ("status at completion/approval of the G0.1
  round") with a pointer to the current gate state in `V03E_SPEC.md` §25 and the
  later proof records; the G0.1 evidence, criteria and conclusion are unchanged.
* Case result presentation in this document is split per case (expected / observed /
  candidates / semantic result) for readability.
* **P3-A (corrected here):** the post-run reproduction of the per-case allowed sets
  listed `MULTIPLE_MATCHES / EVIDENCE_GAP / CORRUPTION` for cases C, E and G, which is
  **broader** than the immutable pre-run manifest (those three cases allow only
  `MULTIPLE_MATCHES` → `evidence_conflict`).  The §6 table now reproduces the manifest
  exactly; the observed verdicts (`MULTIPLE_MATCHES`) are unchanged and lie inside both
  readings, so no executed result depended on the difference.
* **P3-B (clarified here):** the immutable manifest is preserved verbatim and is
  authoritative; its **global fail-closed precedence** (`CORRUPTION` first, then
  `EVIDENCE_GAP`) governs malformed or insufficient evidence, while each case-specific
  allowed set describes the semantic case **once its declared preconditions hold**.  No
  executed A-J result depended on resolving this tension.
* **P3-C (worded correctly here):** the original G0.2 record is **substantively
  unchanged** — its historical evidence and results are preserved; only its citation
  references were corrected and a narrow historical pointer was added.  It is not
  claimed to be byte-for-byte unchanged.
* **P3-D (retained limitations, non-blocking):** (i) the executed harness/oracle and the
  raw per-case evidence were not committed; (ii) the case-I sensitivity belongs in
  future implementation tests (P8/P6 territory; no P8 claim); (iii) the §11 item 6
  interaction with the bridge's own probe/read operations needs future interpretation
  before optional adoption implementation; (iv) the `model`/`agent` sanitize/clip
  asymmetry may remove candidates; (v) the scanner interval remains
  enumeration-at-scan-time, not a stronger sequence-arithmetic interval proof;
  (vi) the manifest-binding case-sensitive phrase check was a mechanical check defect
  (casing only; no verdict affected).
* **`P3` is not claimed to be zero**: the earlier P3 observations, the P3-A-P3-D items
  above and the carried-forward notes in §13 remain recorded.

## 13. Carried forward (recorded, not proven here)

1. **Implementation-test sensitivity (not a proof case, not executed in this
   re-run).**  If a future foreign/future writer can create a prompt-free
   "submission" inside the same target session, tuple correlation alone cannot prove
   ownership.  This is P8/P6 territory: it must be carried into the future
   implementation tests and must **not** be used to claim P8.
2. **§11 item 6 clarity (future implementation clarification, not a design change).**
   The rule "no other DevRelay ledger operation touches that session inside the
   window" must be interpreted and reviewed against the bridge's **own** probe/read
   records (the accepted bridge writes ownership probes and reads in the same
   session, and labels the probe with the originating operation) before any optional
   adoption implementation.  This is explicitly **outside** G0.2's positive claim and
   was not attempted here.
3. **Interval strength**: the scanner proves complete enumeration at scan time, not a
   sequence-arithmetic interval; the production reader must prove the interval from
   durable sequence evidence.
4. **Sanitize/clip asymmetry** for `model`/`agent` between the run snapshot and the
   ledger record (a mismatch can only remove a candidate).

## 14. Limitations and non-claims

This clean candidate result does **not** establish: that v0.3-E recovery exists or is
correct (nothing was implemented; the harness is disposable proof code); future
strict-reader correctness; P1/P2/P3/P8/P9; session ownership/P6; that a `MATCH` means
provider completion (the crash-boundary match is an ISSUED record and the §11 item 2
ledger half is not met); that adoption or implementation is authorized; delivery
truth; `fsync`/power-loss durability; or any G0.3–G2 step.  The harness, oracle
modules and per-case evidence live only in the OS temp area
(`…/dsh-g02-rerun/{oracle.py,corpus.py,run_cases.py,evidence/*.json}`) and are **not**
committed; the committed record is this document plus the precommitted manifest.

## 15. Budget

0 real provider/model inference calls; 0 real network requests; 0 OpenCode processes
started or restarted; no runtime/test/dependency/version change.

## 16. Result: clean candidate pass -> authoritative PASS

**Candidate stage (as recorded in `7908ace`):** `G0.2 = CLEAN CANDIDATE PASS /
AWAITING INDEPENDENT REVIEW` — all ten fixed cases A-J executed once each under the
oracle precommitted in commit `12ea1b7` (manifest SHA-256 `e900f7a3…`, unchanged),
every semantic verdict inside its precommitted allowed set, no weak metadata producing
a positive attribution, no ambiguous winner or timestamp tie-break, and corrupt
relevant evidence failing closed even when a clean unique candidate was present.

**Authoritative stage (recorded by the later bookkeeping round):** the independent
clean-rerun review issued **APPROVE V0.3-E G0.2 FALSE-CORRELATION PROOF** with
**P0 = 0, P1 = 0, P2 = 0**, so **`G0.2 = PASS` — authoritative and independently
approved**.  The executing agent did not self-approve it, and the candidate stage above
stays recorded as the pre-approval history.

Unchanged alongside it: `G0.1 / P7 = PASS` (authoritative, independently approved) —
G0.1/P7 and G0.2 are authoritative PASS and mandatory-core implementation remains
**NOT AUTHORIZED** pending a separate authorization; `G0.3`, `G0.4`, `G0.5`, `G1`,
`G2` = **NOT RUN**; overall platform proof gate = **PARTIALLY EXECUTED / NOT COMPLETE**
(not passed, not complete); `adopt_completed_turn` = **DISABLED**.

History is preserved: `V03E_G0_2_FALSE_CORRELATION_PROOF.md` remains the original
proof record (including its first complete-pass oracle bug, its invalid attempts, the
first independent `REQUEST_CHANGES` and P2-1/P2-2) and
`V03E_G0_2_RERUN_ORACLE.md` remains the immutable pre-run oracle artifact.
