# DevRelay v0.4-C2a — owner acceptance record

Status: **ACCEPTED / CLOSED by the owner on 2026-10-22.**  This is a C2a stage
acceptance, not a v0.4 release; no tag or publication was created.

## Accepted scope

C2a is the read-only task artifact dashboard:

- authenticated `GET /api/tasks` and `GET /api/tasks/{task_id}`;
- task list/current marker, state, tests/evidence, review findings/history,
  open P3, final gate and blocked state;
- task-relative **git diff stat only** (no full diff);
- provider-call and review-attempt accounting;
- explicit `token_usage_available: false` / `cost_available: false`;
- Tasks tab in the local UI;
- no task/run action, no arbitrary path, no raw provider output.

## Evidence

| Item | Value |
| --- | --- |
| Implementation commit | `9640425` |
| CI | [run 39775641367](https://github.com/YingQiu0871/DevRelay/actions/runs/39775641367) — 8/8 jobs |
| Local suite | 1,329 collected — 1,327 passed + 2 environment skips |
| Review | independent read-only review: APPROVE WITH FINDINGS, P0/P1 = 0 |
| Review record | [V04C2A_REVIEW.md](V04C2A_REVIEW.md) |
| Tests | seeded task list/detail, corrupt index 503, invalid/missing IDs, auth, no full diff, UI markers/request guard |

## Limitations carried forward

- A baseline-present diff-stat test remains a follow-up; the missing-baseline
  failure path is covered.
- Git diff stat can still read repository attributes; no object reconstruction
  or index/worktree mutation is performed by the C2a path.
- Token/cost data is not available from provider records and is reported as
  unavailable, never fabricated.
- List rebuilds may disturb keyboard focus/scroll (polish).
- C2b (pause/interrupt/manual prompt/decide, streaming) is a separate gate.

## Immutability

`v0.3.0` remains the published release.  C2a is unreleased `main` work.
