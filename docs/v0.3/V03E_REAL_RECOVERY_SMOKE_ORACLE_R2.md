# DevRelay v0.3-E — real crash-and-recovery smoke oracle, revision 2 (precommitted)

Status: **PRECOMMITTED / IMMUTABLE ONCE COMMITTED / SINGLE USE / NOT ACCEPTANCE**

This document is the precommitted acceptance oracle for **one** real
crash-and-recovery smoke of the v0.3-E mandatory fail-closed core. It supersedes
`docs/v0.3/V03E_REAL_RECOVERY_SMOKE_ORACLE.md` (revision 1). It is frozen at the
commit that issues `docs/v0.3/V03E_REAL_RECOVERY_SMOKE_AUTHORIZATION_R2.md`; its
SHA-256 is recorded there. After that commit the oracle must not be edited — a
defect discovered during execution is recorded in the result document, never
patched into the oracle, and the smoke is a FAIL if the defect is material.

The smoke runs **once**. A rerun requires a new oracle and a new authorization.

## 0. Why revision 2 exists

Revision 1 (`V03E_REAL_RECOVERY_SMOKE_ORACLE.md`, SHA-256 `ac9e0318…df6c`) was
executed once and recorded as FAIL in
`docs/v0.3/V03E_REAL_RECOVERY_SMOKE_RESULT.md` (commit `312dd74`). The failure was
in the harness, not in the product:

1. revision 1 §3 defined the submission count as *the number of `send_prompt`
   ledger records*. DevRelay's `send_prompt` operation starts with a
   non-submitting ownership probe (`_probe_ownership("send_prompt", …)` →
   `_fetch_session` → `_request("send_prompt", "GET", …)`), which is durably
   accounted **with the same operation label** and no prompt digest. The count
   therefore included a GET probe and could never equal the number of
   model-bearing POSTs;
2. the revision-1 driver recorded that comparison (`submission-count.json`,
   `agree: false`) but **never asserted it**, so its printed verdict was PASS while
   the written oracle rule says FAIL. That discrepancy is the harness
   nonconformance this revision corrects: the count rule is now normative and the
   driver must assert it (see §4).

Revision 2 changes **only** the count definition, the conformance obligation and
the evidence layout. Every product-facing criterion of revision 1 is retained
verbatim in substance. Revision 1 and its single-use authorization remain spent;
this revision is exercised under its own one-shot authorization.

## 1. What the smoke must prove (and what it must not)

Prove, against real OpenCode `1.18.11` and real provider inference:

1. a **genuinely interrupted** turn — the DevRelay child is killed while the
   model-bearing submission is in flight, so the outcome is unknown and the remote
   may or may not have produced a reply — leaves a durable **v2 live intent**
   (`RECOVERY_REQUIRED`-capable state) and a ledger record;
2. a fresh surface **never replays** it: the three mutating orchestration tools
   refuse with `orchestration_recovery_required`, the run document is
   byte-identical and no new `/message` POST is issued;
3. `devrelay_reconcile_run` is **read-only and local-only**: no byte under
   `<ws>/.devrelay` changes, no HTTP request is issued, and the report attributes
   the attempt honestly from the ledger alone;
4. `devrelay_resolve_recovery(mark_unrecoverable)` writes **exactly one**
   resolution, ends the run **BLOCKED** with `blocked_reason == recovery_reason`,
   books the frozen attempt exactly once and freezes digest-consistent evidence;
5. the run is **terminal** afterwards (no second resolve, no replay, no reconcile);
6. the real remote reply is **not adopted** and its text is **not persisted**.

Must not: enable `adopt_completed_turn`, perform retries/resume/re-submission, mark
any acceptance row COVERED, tag/release/push/merge, or touch the repository's
tracked tree.

## 2. Environment and chain (fixed)

| Item | Value |
| --- | --- |
| Repository | `D:\DevRelay`, branch `v0.3-e-recovery-reconciliation` |
| OpenCode | `serve` 1.18.11, dedicated instance, free loopback port, no token |
| Provider routes | implementer `opencode/deepseek-v4.1-flash-free`, reviewer `opencode/glm-5.3-flash-free` (the `opencode-go` provider answers 403 "subscription required" on this machine, so the free `opencode` provider is used; both ids were listed by `GET /config/providers`, and the implementer id produced real text in a throwaway preflight before revision 1 was frozen) |
| Disposable workspace | `%TEMP%\devrelay-recovery-smoke-<UTC>` (created by the driver) |
| Disposable sessions | two prompt-free `POST /session` ids, distinct, never reused across roles |
| Chain | official MCP Python SDK stdio client → `python -m devrelay mcp serve --workspace <ws>` → v0.3-E service → bridge → OpenCode → provider |
| Prompt | fixed once, contains the sentinel `DEVRELAY-SMOKE-SENTINEL-<hex>`; sha256 reported |
| Evidence | everything under `<%TEMP%>\devrelay-recovery-smoke-<UTC>\evidence\` (outside the repo) |

## 3. Procedure and pass criteria (S0–S9)

Every phase is PASS/FAIL by the criteria below; no partial credit, no "likely".

**Submission count (normative).** A model-bearing submission is a ledger record
that has `method == "POST"`, `operation == "send_prompt"`, the implementer
`session_id` and a non-empty `prompt_sha256` (the bridge writes it before the
request is sent; a POST cannot happen without that allocation, which advances
`<ws>/.devrelay/opencode/sequence.json`).

The count is taken twice per phase:

- `ledger_submission_posts` — the number of such records for the implementer
  session;
- `log_message_process` — the number of `message=process session.id=<impl>` lines
  in the dedicated instance's log.

`ledger_submission_posts` must equal `log_message_process` and must be exactly
`0` in S0/S1 and exactly `1` from S2 through S8; disagreement or a different value
is a **FAIL**, recorded as measured.

The non-submitting ownership probe is **expected** and is recorded separately as
`ledger_probe_gets` (records with `operation == "send_prompt"`, `method == "GET"`,
no prompt digest). Exactly one probe is expected per `send_prompt` call; probe GETs
are never counted as submissions. `ledger_send_prompt_records` (every record
labelled `send_prompt`) is also recorded for audit; it is expected to equal
`ledger_submission_posts + ledger_probe_gets`.

**S0 — preflight (no model call).** Dedicated instance answers `GET /session` with
200; two prompt-free sessions are created; the disposable workspace gets a
`config.yaml` with `opencode.base_url`, the two role routes and the two sessions;
the repository HEAD, branch and porcelain are recorded. PASS iff all of that holds
and the submission count is 0 (`ledger_submission_posts == 0`,
`log_message_process == 0`).

**S1 — baseline.** `devrelay_start_run(max_cycles=1)` → `READY_IMPLEMENTER`,
`schema_version == 2`, `model_turns_used == 0`, `turn_attempts == 0`, no
`in_flight_turn`, no `recovery`, submission count 0. PASS iff exact.

**S2 — real crash (the only model-bearing step).** A child process calls
`devrelay_run_implementer(run_id, prompt)`. The driver watches
`<ws>/.devrelay/opencode/calls/` and, `0.6 s` after a `send_prompt` **POST**
record for the oracle prompt appears (deadline 300 s), kills the **whole child
process tree** with `taskkill /F /T`; the kill therefore lands while the
synchronous `POST /session/<id>/message` is in flight. PASS iff: the child is
dead; the run document is `schema_version 2` with a live `in_flight_turn` (role
`implementer`, cycle 1) whose `prompt_sha256`/`prompt_chars` equal the oracle
prompt; the ledger holds exactly one `send_prompt` POST record for that identity
(state `ISSUED` or with an unknown outcome) and exactly one probe GET; the
dedicated instance's log shows the implementer session processed a message
(`message=process session.id=<impl>`) and the submission count rule of §3 holds
(posts == lines == 1); the run document does **not** contain the prompt text.
Whether the remote session also holds an assistant message at kill time is
recorded as measured but is **not** part of the verdict.

**S3 — refusal (fresh surface).** A new MCP process (same workspace): `get_run`
shows the live intent; `run_implementer`, `run_reviewer` and `decide_run` each
return `isError` with `error.type == "orchestration_recovery_required"`; the run
document SHA-256 is unchanged; the submission count is unchanged (the full count
record, including posts and lines, equals the S2 record). PASS iff all exact.

**S4 — reconcile (read-only).** A SHA-256 manifest of every file under
`<ws>/.devrelay` is taken, then `devrelay_reconcile_run(run_id)` is called, then the
manifest is retaken. PASS iff: manifest identical; submission count unchanged and
still posts == lines == 1; envelope ok; `recoverable == true`; `v1_frozen ==
false`; `state == "READY_IMPLEMENTER"`; `attempt` role/cycle as in S2 and
`attempt.prompt_sha256` equal to the oracle prompt digest; `ledger.outcome ∈
{exactly_one_match, evidence_gap}` and honest (`exactly_one_match` ⇒ `call_id`
non-empty; `evidence_gap` ⇒ non-empty `gap_reason`; `interval_proven` ⇒ `floor`
and `ceiling` non-empty); `remote.outcome == "evidence_gap"` with a `gap_reason`
stating that the local surface reads no session history; `adoption.available ==
false`; `submission.submitted_by_recovery == false`; `checklist` has exactly the
nine items `document`, `attempt identity`, `ledger attribution`, `ledger
settlement`, `remote correlation`, `route stability`, `resolution state`,
`adoption capability`, `platform proofs`, each status ∈ {`pass`, `fail`,
`unknown`}; `blockers` non-empty and mentions adoption being disabled.

**S5 — resolve (`mark_unrecoverable`).** `devrelay_resolve_recovery` returns ok.
PASS iff: state `BLOCKED`, `terminal == true`, `legal_next_actions == []`;
`blocked_reason == recovery_reason` and the reason ∈ {`submission_uncertain`,
`reply_pending`, `turn_interrupted`}; `recovery.resolution == "mark_unrecoverable"`
with non-empty `resolved_at`; the evidence digest recomputes exactly from its 27
canonical fields (driver recomputes with the package's own canonicalization); the
frozen attempt is `blocked` and booked exactly once in the implementer history;
`last_transition` is `action == "recover"`, `previous_state ==
"RECOVERY_REQUIRED"`, `next_state == "BLOCKED"`; the run file changed relative to
S3 and no `*.tmp` file or lock residue remains; the ledger manifest (call ids and
states) is unchanged and the submission count is unchanged.

**S6 — terminality (no replay, no second resolution).** `run_implementer`,
`run_reviewer`, `decide_run` each fail with `orchestration_invalid_transition`;
a second `resolve_recovery` fails with `orchestration_recovery_already_resolved`;
`reconcile_run` fails with `orchestration_recovery_unsupported` (terminal refusal).
PASS iff all exact, the run document is byte-identical to S5 and the submission
count is unchanged.

**S7 — no adoption, no persistence.** The assistant reply text (and the sentinel)
must not appear anywhere under `<ws>/.devrelay` (case-insensitive plaintext scan of
every file); no `Authorization`/`Bearer`/token/api-key material may appear; the run
document must contain no prompt or reply text. PASS iff all hold.

**S8 — containment and cleanup.** Both disposable sessions are deleted (`DELETE`
200, then absent from `GET /session` or 404); the dedicated instance is stopped and
its port is free; the disposable workspace is removed; every MCP child process is
gone; the repository HEAD/branch/porcelain equal the S0 record (the only allowed
difference is this smoke's own new governance files, listed explicitly). PASS iff
all hold.

**S9 — verdict.** `PASS — V0.3-E REAL CRASH-AND-RECOVERY SMOKE (R2)` iff **every**
phase S0–S8 passed **and** the oracle→driver conformance table of §4 is complete
with no missing rule; otherwise `FAIL` with the first failing criterion and the
measured value recorded verbatim.

## 4. Conformance obligation (new in revision 2)

Every normative rule of this oracle must be implemented by a **named** driver
criterion, and the result document must reproduce the mapping. The driver writes
`<evidence>/oracle-conformance.json` with one entry per rule:

| rule id | requirement | driver criterion (label prefix) |
| --- | --- | --- |
| R-S0 | preflight, two sessions, count 0 | `S0 preflight` |
| R-S0-count | posts == lines == 0 | `submission count is 0 (posts)` |
| R-S1 | baseline document | `S1 baseline` |
| R-S1-count | posts == lines == 0 | `submission count is 0 (posts, S1)` |
| R-S2-crash | kill mid-flight, live intent, identity | `S2 real crash` |
| R-S2-post | exactly one POST for the identity | `exactly one submitted POST for the identity` |
| R-S2-probe | exactly one probe GET recorded | `exactly one ownership-probe GET recorded` |
| R-S2-count | posts == lines == 1 | `submission count agrees (posts == message=process)` |
| R-S3 | refusals, byte-identical doc, count unchanged | `S3 refusal on a fresh surface` |
| R-S4 | read-only reconcile, no durable write | `S4 reconcile is read-only` |
| R-S5 | one resolution, BLOCKED, digest, single booking | `S5 mark_unrecoverable` |
| R-S6 | terminality | `S6 terminality` |
| R-S7 | no adoption, no persistence | `S7 no adoption, no persistence` |
| R-S8 | cleanup, repo unchanged | `S8 cleanup` |

The driver must assert each label; a missing label, a failed label, or a label
whose phase was skipped makes the verdict FAIL. The conformance file is part of
the evidence and its SHA-256 is recorded in the result document.

## 5. Honesty rules

- Ambiguous or unexpected observations are recorded **as measured**; they are never
  normalized into the expected shape.
- Any durable write during S4 (any file added, removed or changed under
  `<ws>/.devrelay`, including the ledger) is a **FAIL**, even if the report looks
  right.
- If the remote reply text cannot be fetched in S7 (provider/privacy behaviour), the
  driver records `unavailable` and the phase fails unless the same text is provably
  absent from the run document; no inference from absence beyond that.
- The submission count is `ledger_submission_posts` (method `POST`) cross-checked
  against the instance log's `message=process` lines; disagreement is a FAIL. Probe
  GETs are recorded and excluded by definition, never by reinterpretation after the
  fact.
- The kill time in S2 is part of the oracle (`0.6 s` after the ledger record
  appears); an earlier or later kill is a procedure deviation and must be recorded
  as such, not silently adjusted.
- Wall-clock limits (S2 deadline 300 s) are part of the oracle; a timeout is a FAIL
  and not retried.

## 6. Abort and cleanup on failure

On the first FAIL: stop polling, record the measured state, delete the two
disposable sessions, stop the dedicated instance, remove the disposable workspace
unless evidence needs it, leave the evidence directory outside the repository and
write `FAIL` in the result document. **No rerun under this authorization.**

## 7. Evidence layout

```
<evidence>/smoke.json               machine verdict + per-phase measured values
<evidence>/oracle-conformance.json  rule id → driver label → pass/fail mapping (required)
<evidence>/phase-S0.json            preflight + repo state
<evidence>/phase-S1.json            start_run envelope
<evidence>/phase-S2.json            crash observations (ledger records, run doc, remote messages at kill)
<evidence>/phase-S3.json            refusal envelopes + hashes
<evidence>/phase-S4.json            manifest before/after + reconcile report
<evidence>/phase-S5.json            resolve envelope + recomputed digest + run document
<evidence>/phase-S6.json            terminality envelopes + hashes
<evidence>/phase-S7.json            scan results
<evidence>/phase-S8.json            cleanup observations
<evidence>/server.log               dedicated OpenCode instance log
<evidence>/submission-count.json    count records per phase (posts, probe GETs, lines)
<evidence>/repo-state.json          git state before/after
<evidence>/driver.log               driver stdout/stderr
```

## 8. What this oracle is not

Not an acceptance review, not an independent approval, not authorization to enable
`adopt_completed_turn`, not a release gate. A PASS here is **evidence**, and it
still needs the separately authorized independent review before any acceptance row
may be marked COVERED.
