# DevRelay v0.3-E — real-smoke authorization, revision 2 (issued)

Status: **ISSUED — EXACTLY ONE CORRECTIVE REAL CRASH-AND-RECOVERY SMOKE /
NOT ACCEPTANCE / NOT RELEASE / ONE-SHOT**

| Item | Value |
| --- | --- |
| Issued by | the workspace owner (the human operator of this repository) by explicit instruction in this session (`m02306`: *"准备修正版 oracle + 新授权请求 + 重跑，之后独立验收评审"*) |
| Recorded by | the implementing agent session (bookkeeping only; not self-approval of a review) |
| Issued at | 2026-10-17, Europe/Paris, branch `v0.3-e-recovery-reconciliation` |
| Baseline commit | `312dd74` (revision-1 smoke result recorded) |
| Frozen oracle | `docs/v0.3/V03E_REAL_RECOVERY_SMOKE_ORACLE_R2.md`, SHA-256 `60e0613a2810b70dc58d7235723044fbc99e2ca2001650c17a6e7097b7cd7289` |
| Driver | `docs/v0.3/V03E_REAL_RECOVERY_SMOKE_DRIVER_R2.py`, SHA-256 `3ce16c502788f83e5a0a9264b7c527ed4fe401a9c054cc416df379d307ba6bf0` (committed with this record; plumbing-checked with no model-bearing call before the run) |
| Covers code | the mandatory fail-closed recovery core as already authorized at `f8f52a2` / remediated in `a7fe160`; **no source change** is authorized by this record |
| Use | **one-shot** — one corrective smoke; **spent** (executed 2026-10-17, see §4) |
| Decision | **APPROVED** |
| Spent on | run `DR-ea1c53353d82430e97e3ce9365922b49`; recorded `PASS — V0.3-E REAL CRASH-AND-RECOVERY SMOKE (R2)` in `docs/v0.3/V03E_REAL_RECOVERY_SMOKE_RESULT_R2.md`; not acceptance |

## 1. Scope authorized

**Exactly one** real crash-and-recovery smoke of the v0.3-E mandatory fail-closed
core, under oracle R2 and driver R2 above, with `max_cycles = 1` and at most one
real model-bearing submission (the implementer turn that is crashed).

Nothing else. This record does **not** authorize a source edit, a second run, a
retry, a resume, a re-submission, a replay, enabling `adopt_completed_turn`, any
remote-correlation read, a release, a tag, a push, a merge, or marking any
`V03E_ACCEPTANCE.md` row COVERED.

## 2. Why revision 2 (recorded, not an excuse)

The revision-1 smoke is FAIL and stays FAIL
(`docs/v0.3/V03E_REAL_RECOVERY_SMOKE_RESULT.md`). Its failure was a harness
failure with two parts:

1. oracle R1 §3 counted every ledger record labelled `send_prompt`, including the
   bridge's non-submitting ownership-probe GET (same operation label, no prompt
   digest), so the count could not equal the model-bearing POST count;
2. the R1 driver recorded that comparison but never asserted it, so it printed PASS
   while the rule said FAIL.

Oracle R2 defines the submission count as `method == "POST"` records for the
implementer session, keeps the `message=process` line as the independent witness,
records the expected probe GETs separately, and requires every normative rule to
be mapped to a named, asserted driver criterion (`oracle-conformance.json`). The
revision-1 run is not reinterpreted or reused.

## 3. Conditions (binding)

1. Oracle R2 and driver R2 are executed **without edit**; a material defect found
   during execution is a FAIL recorded in the result document, never patched into
   the oracle, and no rerun happens under this authorization.
2. The chain, environment, procedure and pass criteria are exactly those of oracle
   R2 §2–§5; the harness is driver R2 as committed.
3. Disposable instance, workspace and sessions only; the operator's own OpenCode
   instance, sessions and repository tree are untouched.
4. Evidence lives outside the repository and is cited by path and SHA-256 from the
   result document; `oracle-conformance.json` is part of the evidence.
5. `ADOPTION_CAPABILITY_ENABLED` stays `False`; the smoke must not flip it.
6. The verdict is **evidence**, not acceptance. Acceptance still requires the
   separately authorized independent review; this round ends with that review
   request, not with an acceptance decision.

## 4. Spent-on-execution semantics

Once the smoke executes, this authorization is **spent**:

```
AUTHORIZATION SPENT ON EXECUTION — NOT REUSABLE
```

No second run under it, no re-dating, no silent extension. The result document
records the run id, the evidence path and hashes, and the verdict.

## 5. Completion criteria for this round

1. the smoke executed under oracle R2, with a result document recording either
   `PASS — V0.3-E REAL CRASH-AND-RECOVERY SMOKE (R2)` or `FAIL` plus the first
   failing criterion, and the oracle→driver conformance table;
2. `V03E_IMPLEMENTATION.md`, `V03E_ACCEPTANCE.md`, `V03_PLAN.md`, `README.md`,
   `BACKLOG.md` updated without marking anything accepted;
3. any revision-1 bookkeeping found inaccurate is corrected in the same round;
4. committed cleanly, and the independent acceptance review requested (not
   performed) next.

All four criteria were met by the smoke round itself (result commit `9cf8f14`); no
acceptance was marked at that point. Criterion 2 governed the smoke round only —
the acceptance decision is the *separate* independent review requested in `m02306`,
which was performed afterwards and is recorded in `docs/v0.3/V03E_ACCEPTANCE.md` §0
(verdict *APPROVE V0.3-E MANDATORY FAIL-CLOSED CORE ACCEPTANCE*, P0 = 0, P1 = 0,
P2 = 2; scope: local read-only reconciliation + one-shot `mark_unrecoverable`;
`adopt_completed_turn` remains DISABLED; no platform gate claimed). That review, not
this authorization, owns the COVERED markings.

