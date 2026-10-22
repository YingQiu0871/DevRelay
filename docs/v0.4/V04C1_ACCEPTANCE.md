# DevRelay v0.4-C1 — owner acceptance record

Status: **ACCEPTED / CLOSED by the owner on 2026-10-22.**  This is a C1 stage
acceptance, not a v0.4 release; no tag or publication was created.

## Accepted scope

C1 is the read-only run dashboard on the accepted A1/B1 API:

- click-through run detail from `GET /api/runs` and `GET /api/runs/{run_id}`;
- state, cycle, completed cycles, model-turn budget, turn attempts, in-flight
  flag, update time;
- implementer/reviewer route snapshot;
- turn evidence (cycle, outcome, model, HTTP status,
  `submission_uncertain`/`reply_pending`/`retry_safe`, call IDs);
- decision history, blocked/recovery reasons;
- manual refresh and optional 5-second auto-refresh;
- no pause/interrupt/prompt/decide, raw provider stream, diff/test/review
  artifact view or cost accounting.

## Evidence

| Item | Value |
| --- | --- |
| Implementation commit | `3497c58` |
| CI | [run 39701949086](https://github.com/YingQiu0871/DevRelay/actions/runs/39701949086) — 8/8 jobs |
| Local suite | 1,326 collected — 1,324 passed + 2 environment skips |
| Review | independent read-only review: APPROVE WITH FINDINGS, P0/P1 = 0 |
| Review record | [V04C_REVIEW.md](V04C_REVIEW.md) |
| Tests | seeded run detail through the existing API; auto-refresh/control-boundary checks; request-guard/timer checks |

## Limitations carried forward

- No run-control actions; C2 requires a separate endpoint and threat-model
  review.
- No raw/normalized provider streaming, git diff/test/review artifact view or
  token/cost accounting.
- Auto-refresh is a 5-second read-only poll; it stops on session clear.
- List rebuilds may disturb keyboard focus/scroll (polish item).
- Remaining P3 notes are recorded in [V04C_REVIEW.md](V04C_REVIEW.md).

## Immutability

`v0.3.0` remains the published release.  C1 is unreleased `main` work.
