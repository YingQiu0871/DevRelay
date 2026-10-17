# V03-E Real Crash-and-Recovery Smoke — Result

**Status:** EXECUTED ONCE / AUTHORIZATION SPENT / **VERDICT: FAIL** (per the
precommitted oracle) / PRODUCT CRITERIA OBSERVED PASS / NOT ACCEPTANCE

**Executed:** 2026-10-17, ~17:56:42–17:59 UTC, by the implementing agent, via
`docs/v0.3/V03E_REAL_RECOVERY_SMOKE_DRIVER.py` (precommitted, unmodified).
**Run id:** `DR-7248335182ec4207adb8d9d31b397287`
**Evidence:** `C:\Users\1\AppData\Local\Temp\devrelay-recovery-smoke-20261017T175642Z\evidence`
(outside the repo, per the oracle).

This document records what happened. It does not accept the stage, does not
change the oracle, and does not reinterpret the verdict.

---

## 1. Authorization that governed the run

- Work authorization: `docs/v0.3/V03E_IMPLEMENTATION_AUTHORIZATION.md`, issued
  for this agent by the human ("申请实现授权并补真实崩溃恢复 smoke").
- Baseline at authorization: `36fe9c5` (branch `v0.3-e-recovery-reconciliation`).
- Precommit that froze the artifacts (`f8f52a2`, blob-verified hashes):
  - oracle `docs/v0.3/V03E_REAL_RECOVERY_SMOKE_ORACLE.md`
    SHA-256 `ac9e0318b9257691067ccc6cfb669516dbb6d64d5ee56b9d5eaad46f5ac9df6c`;
  - driver `docs/v0.3/V03E_REAL_RECOVERY_SMOKE_DRIVER.py`
    SHA-256 `da7d21357adfba5094504a944ce5f1e42310a5abea0508f1d483f80264152b37`.
- The authorization is **single-use**. It was spent by the run recorded here;
  no second run was performed under it.

## 2. Environment

| item | value |
| --- | --- |
| OpenCode | 1.18.11, `C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe` |
| instance | `opencode serve --port <free> --hostname 127.0.0.1 --print-logs --log-level INFO` |
| implementer route | `opencode/deepseek-v4.1-flash-free` |
| reviewer route | `opencode/glm-5.3-flash-free` |
| workspace | disposable `%TEMP%\devrelay-recovery-smoke-<UTC>\ws`, removed at S8 |
| DevRelay surface | `python -m devrelay mcp serve --workspace <ws>` over MCP stdio |

`opencode-go/*` was rejected earlier with HTTP 403 ("An active OpenCode Go
subscription is required"), so the free `opencode` provider was used — the
oracle's substitute-route rule covers this choice.

## 3. Phases

| phase | result | measured (abridged) |
| --- | --- | --- |
| S0 preflight | PASS | instance 200, two sessions, config written, submission count 0 |
| S1 baseline | PASS | `READY_IMPLEMENTER`, `schema_version == 2`, 0 turns, no intent |
| S2 real crash | PASS | child killed (`taskkill /F /T` rc 0) 0.6 s after `OC-0007` appeared; run doc schema 2 `READY_IMPLEMENTER` with live `in_flight_turn` implementer cycle 1, prompt digest `ccdb5dba…6063`, 188 chars; exactly one identity-matching record `OC-0007`, state `ISSUED`; one `message=process` line; no prompt text in the doc |
| S3 refusals on a fresh surface | PASS | `get_run` shows the live intent; `run_implementer`, `run_reviewer`, `decide_run` → `orchestration_recovery_required`; run doc byte-identical (`53d31375…`); no new submission |
| S4 reconcile | PASS | `.devrelay` manifest byte-identical; `recoverable == true`, `v1_frozen == false`; `ledger.outcome == exactly_one_match`, call `OC-0007`; `remote.outcome == evidence_gap` with the "reads no session history" reason; adoption unavailable; checklist exactly the nine items (`ledger settlement` fail, `remote correlation` unknown, `adoption capability` fail, `platform proofs` unknown, rest pass); blockers non-empty incl. "adoption is disabled" |
| S5 resolve (`mark_unrecoverable`) | PASS | `BLOCKED`, `terminal == true`, `legal_next_actions == []`; recovery/blocked reason `turn_interrupted`; `resolved_at 2026-10-17T17:57:04+00:00`; evidence digest `189ef5a2…` recomputed equal; attempt booked once; `last_transition` recover `RECOVERY_REQUIRED → BLOCKED`; no temp residue |
| S6 terminality | PASS | `run_implementer`/`run_reviewer`/`decide_run` → `orchestration_invalid_transition`; second resolve → `orchestration_recovery_already_resolved`; `reconcile_run` → `orchestration_recovery_unsupported`; doc unchanged |
| S7 leakage | PASS | oracle sentinel, remote reply text and credential needles absent from every `<ws>/.devrelay` file |
| S8 cleanup | PASS | sessions deleted `(200, true)`, instance stopped, port free, repo head/branch/porcelain unchanged (`f8f52a2`), no MCP child survives, workspace removed |

**S2–S8 carry one FAIL:** the oracle's submission-count rule.

## 4. The failed criterion (and its diagnosis)

Oracle §3 freezes the count as follows (`V03E_REAL_RECOVERY_SMOKE_ORACLE.md:53`):

> The count is therefore taken twice per phase — the number of `send_prompt`
> records for the implementer session, and the number of
> `message=process session.id=<impl>` lines […] the two numbers must be
> **equal**; disagreement is a FAIL.

Measured at S2 and every later phase: ledger records labelled `send_prompt` = 2
(`OC-0004`, `OC-0007`), `message=process` lines = 1, `agree: false`.

Diagnosis — the oracle's count includes a **non-submitting ownership probe**:

1. `OrchestrationService._run_role` → `router.send_role_prompt` →
   `OpenCodeBridge.send_prompt` (`src/devrelay/opencode/bridge.py`).
2. `send_prompt` first calls `_probe_ownership("send_prompt", session_id)`
   → `_fetch_session` → `_request("send_prompt", "GET", …)`: the probe GET is
   durably accounted with `operation="send_prompt"`, method `GET`, and an empty
   prompt digest. That is `OC-0004`.
3. It then reads the pre-submission boundary (`read_messages`, `OC-0005` /
   `OC-0006`) and only then issues the one `POST /session/{id}/message`, which is
   `OC-0007` (digest `ccdb5dba…6063`, 188 chars).
4. There is exactly **one** POST record and exactly **one** `message=process`
   line, and the S1→S2 sequence advanced from `next_call_sequence: 3` to `8`
   (verify, probe, boundary, boundary read, submission). No second submission
   exists.

Reproduction without a model (deterministic, offline, stub-backed):
`build/_repro_send_prompt_records.py` (untracked, `build/` is git-ignored) runs
one `devrelay_run_implementer` and prints the ledger:

```
OC-0001 get_session   GET
OC-0002 get_session   GET
OC-0003 get_session   GET
OC-0004 send_prompt   GET
OC-0005 read_messages GET
OC-0006 read_messages GET
OC-0007 send_prompt   POST   6fa20a54dc10  12  COMPLETED
records labelled operation=send_prompt: 2
records with method=POST: 1
server processes started (stub): 1
```

The same allocation pattern as the smoke (`OC-0004` GET, `OC-0007` POST).

**Conclusion:** the count *as defined* counts the ownership probe, so the rule
cannot distinguish "one submission" from "one submission plus its accounting
probe". The product performed exactly one model-bearing submission. The defect
is in the oracle's measurement definition, not in DevRelay's behaviour.

**Verdict consequence:** the oracle states that "a defect discovered during
execution is recorded in the result document, never patched into the oracle, and
the smoke is a FAIL if the defect is material"
(`V03E_REAL_RECOVERY_SMOKE_ORACLE.md:6-10`). The defect is material to the
verdict rule, therefore this smoke is recorded as **FAIL**. No rerun was
performed, the oracle was not edited, and nothing here is converted into a PASS.

## 5. What the run nevertheless observed (evidence, not acceptance)

- A real model-bearing submission was interrupted mid-flight; the durable
  document kept a live v2 intent whose identity matches the single `send_prompt`
  POST record.
- Every model-bearing MCP tool refused while the intent was live, with a
  byte-identical document and no new submission (fail-closed).
- `reconcile` was read-only at byte level and attributed the submission to
  exactly one ledger record.
- `resolve(mark_unrecoverable)` performed no provider call, booked the attempt
  exactly once, and left a terminal `BLOCKED` document with an internally
  consistent evidence digest.
- Terminality held: no replay, no second resolution, no reopen.
- No prompt text, sentinel, reply text or credential needle reached the durable
  surface; cleanup removed sessions, instance and workspace, and the repo tree
  was unchanged.

These support the implementation's behaviour; they are **not** an acceptance
decision, and the formal smoke verdict remains FAIL.

## 6. Evidence inventory

Path: `C:\Users\1\AppData\Local\Temp\devrelay-recovery-smoke-20261017T175642Z\evidence`

| file | SHA-256 |
| --- | --- |
| `smoke.json` | `1bc53f69aab4c3750a9394a65ff798ffb4db87e7ac8f4a94c51ccae7d817811f` |
| `driver.log` | `962b1ca97f9d27ab52e46e8845ab25501202bea09a426a4f4b7d31706442253e` |
| `submission-count.json` | `2afd67465b2690422bf9d76d21d50e8858730c13d08872534129e650de4fc608` |
| `server.log` | `094cd03e8599e8e098f20f8ed72a35ecce5dd418edcbad927cf702cfcd42a7ce` |
| `crash_child.py` | `5614d03af392607d399639c1b9d6f7fc487efad3eb08a753075b14ffc5bae48f` |

Also present: `phase-S0.json` … `phase-S8.json`, `repo-state.json`,
`crash-child.out` / `.err`. The disposable workspace was deleted at S8, so the
ledger records themselves are gone; the driver logged `OC-0007`'s full record and
the submission-count derivation, and the offline reproduction above pins the
allocation pattern.

## 7. Next steps (require fresh human authorization)

1. A **corrective oracle** that defines the submission count as the number of
   ledger records with `method == "POST"` for the implementer session (equivalently
   records carrying a prompt digest), keeps the `message=process` line as the
   independent witness, and records separately that one ownership-probe GET is
   expected.
2. A fresh one-shot authorization for a rerun of the corrected oracle, on a new
   baseline commit.
3. Only then may the acceptance table be considered; this document marks no
   acceptance row COVERED.

The vendor `opencode` provider models are free-tier and were chosen because the
`opencode-go` routes require a subscription (403). That constraint should be
restated in the corrective oracle.
