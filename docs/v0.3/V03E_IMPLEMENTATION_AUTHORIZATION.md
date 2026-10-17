# DevRelay v0.3-E — implementation authorization (issued)

Status: **ISSUED — ONE DRAFT RATIFICATION + ONE REAL CRASH-AND-RECOVERY SMOKE /
NOT ACCEPTANCE / NOT RELEASE**

| Item | Value |
| --- | --- |
| Issued by | the workspace owner (the human operator of this repository) by explicit instruction in this session (`m01693`: *"申请实现授权并补真实崩溃恢复 smoke"*) |
| Recorded by | the implementing agent session (bookkeeping only; this is **not** self-approval of a review) |
| Issued at | 2026-10-17, Europe/Paris, branch `v0.3-e-recovery-reconciliation` |
| Baseline commit | `36fe9c5cc367a024b2365611f4cb00c7f2b9e249` |
| Covers code | the mandatory fail-closed recovery core as remediated in `a7fe160` (`src/devrelay/orchestration/{recovery,ledger_reader,service,invariants,models,state_machine}.py`, `src/devrelay/mcp/{tools,server}.py`, `src/devrelay/errors.py`) |
| Frozen oracle | `docs/v0.3/V03E_REAL_RECOVERY_SMOKE_ORACLE.md`, SHA-256 `ac9e0318b9257691067ccc6cfb669516dbb6d64d5ee56b9d5eaad46f5ac9df6c` |
| Driver | `docs/v0.3/V03E_REAL_RECOVERY_SMOKE_DRIVER.py`, SHA-256 `da7d21357adfba5094504a944ce5f1e42310a5abea0508f1d483f80264152b37` (committed with this record; plumbing-checked with no model-bearing call before the run) |
| Use | **one-shot** — one real crash-and-recovery smoke; spent on execution |
| Decision | **APPROVED** |

## 1. Scope authorized

1. The v0.3-E mandatory fail-closed core already on this branch is an **authorized
   implementation** of the frozen design (`docs/v0.3/V03E_SPEC.md`) as reviewed and
   remediated in `V03E_REVIEW.md`.  Before this record it was an unauthorized draft.
2. **Exactly one** real crash-and-recovery smoke of that core, under the frozen
   oracle above, with `max_cycles = 1` and at most one real model-bearing submission
   (the implementer turn that is crashed).

Nothing else is authorized.  In particular this record does **not** authorize
enabling `adopt_completed_turn`, any remote-correlation read, retries, resume,
re-submission, replay, a second smoke or run, a release, a tag, a push, a merge, or
marking any `V03E_ACCEPTANCE.md` row COVERED.

## 2. Conditions (binding)

1. The oracle is executed **without edit**; a material defect found during
   execution is a FAIL recorded in the result document, never patched into the
   oracle, and no rerun happens under this authorization.
2. The smoke's chain, environment, procedure and pass criteria are exactly what the
   oracle fixes; the driver harness is the script committed with this record.
3. Disposable instance, workspace and sessions only; the operator's own OpenCode
   instance, sessions and repository tree are untouched and the tracked tree is
   byte-identical before and after.
4. Evidence lives outside the repository and is cited by path and hash from the
   result document.
5. `ADOPTION_CAPABILITY_ENABLED` stays `False`; the smoke must not flip it.
6. The smoke's verdict is **evidence**, not acceptance.  Any acceptance decision
   still requires the separately authorized independent review.

## 3. Spent-on-execution semantics

Once the smoke executes, this authorization is **spent**:

```
AUTHORIZATION SPENT ON EXECUTION — NOT REUSABLE
```

It stays in the tree as a permanent record.  It must not be reused, re-dated or
silently extended; a further real execution requires a new oracle and a new
authorization.

## 4. Completion criteria for this round

The round this record authorizes is complete when all of the following exist:

1. the smoke executed under the frozen oracle, with a result document recording
   either `PASS — V0.3-E REAL CRASH-AND-RECOVERY SMOKE` or `FAIL` plus the first
   failing criterion;
2. `V03E_IMPLEMENTATION.md` updated from "unauthorized draft" to "authorized by
   this record, not accepted";
3. `V03E_ACCEPTANCE.md`, `V03_PLAN.md`, `README.md` and `BACKLOG.md` updated to
   describe the new state without marking anything accepted;
4. the repository committed cleanly (only pre-existing untracked governance files
   remain untracked).

