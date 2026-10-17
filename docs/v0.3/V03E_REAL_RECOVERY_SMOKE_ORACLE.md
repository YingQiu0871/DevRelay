# DevRelay v0.3-E — real crash-and-recovery smoke oracle (precommitted)

Status: **PRECOMMITTED / IMMUTABLE ONCE COMMITTED / SINGLE USE / NOT ACCEPTANCE**

This document is the precommitted acceptance oracle for **one** real
crash-and-recovery smoke of the v0.3-E mandatory fail-closed core.  It is frozen at
the commit that issues `docs/v0.3/V03E_IMPLEMENTATION_AUTHORIZATION.md`; its
SHA-256 is recorded there.  After that commit the oracle must not be edited — a
defect discovered during execution is recorded in the result document, never
patched into the oracle, and the smoke is a FAIL if the defect is material.

The smoke runs **once**.  A rerun requires a new oracle and a new authorization.

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
| Provider routes | implementer `opencode/deepseek-v4.1-flash-free`, reviewer `opencode/glm-5.3-flash-free` (the `opencode-go` provider answers 403 "subscription required" on this machine, so the free `opencode` provider is used; both ids were listed by `GET /config/providers`, and the implementer id produced real text in a throwaway preflight before this oracle was frozen) |
| Disposable workspace | `%TEMP%\devrelay-recovery-smoke-<UTC>` (created by the driver) |
| Disposable sessions | two prompt-free `POST /session` ids, distinct, never reused across roles |
| Chain | official MCP Python SDK stdio client → `python -m devrelay mcp serve --workspace <ws>` → v0.3-E service → bridge → OpenCode → provider |
| Prompt | fixed once, contains the sentinel `DEVRELAY-SMOKE-SENTINEL-<hex>`; sha256 reported |
| Evidence | everything under `<%TEMP%>\devrelay-recovery-smoke-<UTC>\evidence\` (outside the repo) |

## 3. Procedure and pass criteria (S0–S9)

Every phase is PASS/FAIL by the criteria below; no partial credit, no "likely".

**Submission count.** A `/message` POST cannot happen without a ledger allocation:
the bridge allocates one call id (advancing
`<ws>/.devrelay/opencode/sequence.json`) and writes the `send_prompt` record before
the request is constructed.  The count is therefore taken twice per phase — the
number of `send_prompt` records for the implementer session, and the number of
`message=process session.id=<impl>` lines in the dedicated instance's log — and the
two numbers must be **equal**; disagreement is a FAIL.

**S0 — preflight (no model call).** Dedicated instance answers `GET /session` with
200; two prompt-free sessions are created; the disposable workspace gets a
`config.yaml` with `opencode.base_url`, the two role routes and the two sessions;
the repository HEAD, branch and porcelain are recorded.  PASS iff all of that holds
and the submission count is 0 (no `send_prompt` record, no `message=process` line).

**S1 — baseline.** `devrelay_start_run(max_cycles=1)` → `READY_IMPLEMENTER`,
`schema_version == 2`, `model_turns_used == 0`, `turn_attempts == 0`, no
`in_flight_turn`, no `recovery`, submission count 0.  PASS iff exact.

**S2 — real crash (the only model-bearing step).** A child process calls
`devrelay_run_implementer(run_id, prompt)`.  The driver watches
`<ws>/.devrelay/opencode/calls/` and, `0.6 s` after a `send_prompt` record for the
implementer session appears (deadline 300 s), kills the **whole child process tree**
with `taskkill /F /T`; the kill therefore lands while the synchronous
`POST /session/<id>/message` is in flight.  PASS iff: the child is dead; the run
document is `schema_version 2` with a live `in_flight_turn` (role `implementer`,
cycle 1) whose `prompt_sha256`/`prompt_chars` equal the oracle prompt; the ledger
holds exactly one `send_prompt` record for that identity (state `ISSUED` or with an
unknown outcome); the dedicated instance's log shows the implementer session
processed a message (`message=process session.id=<impl>`); the run document does
**not** contain the prompt text.  Whether the remote session also holds an assistant
message at kill time is recorded as measured but is **not** part of the verdict.

**S3 — refusal (fresh surface).** A new MCP process (same workspace): `get_run`
shows the live intent; `run_implementer`, `run_reviewer` and `decide_run` each
return `isError` with `error.type == "orchestration_recovery_required"`; the run
document SHA-256 is unchanged; the submission count is unchanged (1, the crashed
submission).  PASS iff all exact.

**S4 — reconcile (read-only).** A SHA-256 manifest of every file under
`<ws>/.devrelay` is taken, then `devrelay_reconcile_run(run_id)` is called, then the
manifest is retaken.  PASS iff: manifest identical; submission count unchanged; envelope
ok; `recoverable == true`; `v1_frozen == false`; `state == "READY_IMPLEMENTER"`;
`attempt` role/cycle as in S2 and `attempt.prompt_sha256` equal to the oracle
prompt digest; `ledger.outcome ∈ {exactly_one_match, evidence_gap}` and honest
(`exactly_one_match` ⇒ `call_id` non-empty; `evidence_gap` ⇒ non-empty
`gap_reason`; `interval_proven` ⇒ `floor` and `ceiling` non-empty);
`remote.outcome == "evidence_gap"` with a `gap_reason` stating that the local
surface reads no session history; `adoption.available == false`;
`submission.submitted_by_recovery == false`; `checklist` has exactly the nine items
`document`, `attempt identity`, `ledger attribution`, `ledger settlement`, `remote
correlation`, `route stability`, `resolution state`, `adoption capability`,
`platform proofs`, each status ∈ {`pass`, `fail`, `unknown`}; `blockers` non-empty
and mentions adoption being disabled.

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
document must contain no prompt or reply text.  PASS iff all hold.

**S8 — containment and cleanup.** Both disposable sessions are deleted (`DELETE`
200, then absent from `GET /session` or 404); the dedicated instance is stopped and
its port is free; the disposable workspace is removed; every MCP child process is
gone; the repository HEAD/branch/porcelain equal the S0 record (the only allowed
difference is this smoke's own new governance files, listed explicitly).  PASS iff
all hold.

**S9 — verdict.** `PASS — V0.3-E REAL CRASH-AND-RECOVERY SMOKE` iff **every** phase
S0–S8 passed; otherwise `FAIL` with the first failing criterion and the measured
value recorded verbatim.

## 4. Honesty rules

- Ambiguous or unexpected observations are recorded **as measured**; they are never
  normalized into the expected shape.
- Any durable write during S4 (any file added, removed or changed under
  `<ws>/.devrelay`, including the ledger) is a **FAIL**, even if the report looks
  right.
- If the remote reply text cannot be fetched in S7 (provider/privacy behaviour), the
  driver records `unavailable` and the phase fails unless the same text is provably
  absent from the run document; no inference from absence beyond that.
- The submission count is taken from the ledger's `send_prompt` records and
  cross-checked against the instance log's `message=process` lines; disagreement is
  a FAIL.
- The kill time in S2 is part of the oracle (`0.6 s` after the ledger record
  appears); an earlier or later kill is a procedure deviation and must be recorded
  as such, not silently adjusted.
- Wall-clock limits (S2 deadline 300 s) are part of the oracle; a timeout is a FAIL
  and not retried.

## 5. Abort and cleanup on failure

On the first FAIL: stop polling, record the measured state, delete the two
disposable sessions, stop the dedicated instance, remove the disposable workspace
unless evidence needs it, leave the evidence directory outside the repository and
write `FAIL` in the result document.  **No rerun under this authorization.**

## 6. Evidence layout

```
<evidence>/smoke.json           machine verdict + per-phase measured values
<evidence>/phase-S1.json        start_run envelope
<evidence>/phase-S2.json        crash observations (ledger record, run doc, remote messages at kill)
<evidence>/phase-S3.json        refusal envelopes + hashes
<evidence>/phase-S4.json        manifest before/after + reconcile report
<evidence>/phase-S5.json        resolve envelope + recomputed digest + run document
<evidence>/phase-S6.json        terminality envelopes + hashes
<evidence>/phase-S7.json        scan results
<evidence>/phase-S8.json        cleanup observations
<evidence>/server.log           dedicated OpenCode instance log
<evidence>/submission-count.json ledger records and extracted message=process lines per phase
<evidence>/repo-state.json      git state before/after
<evidence>/driver.log           driver stdout/stderr
```

## 7. What this oracle is not

Not an acceptance review, not an independent approval, not authorization to enable
`adopt_completed_turn`, not a release gate.  A PASS here is **evidence**, and it
still needs the separately authorized independent review before any acceptance row
may be marked COVERED.
