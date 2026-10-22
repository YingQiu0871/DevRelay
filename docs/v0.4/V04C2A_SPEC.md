# DevRelay v0.4-C2a — Read-Only Task Artifact Dashboard

Status: **IMPLEMENTED + INDEPENDENTLY REVIEWED — APPROVE WITH FINDINGS; P2
findings remediated; pending owner acceptance.**  The review is recorded in
[V04C2A_REVIEW.md](V04C2A_REVIEW.md).  C2a enriches the C1 dashboard with
task-relative evidence.  It adds no run/task control and no streaming transport.

## Objective

Expose the already-persisted pipeline task evidence to the local owner without
accepting a filesystem path or adding a write surface:

- task list and current-task marker;
- test status and bounded, redacted test evidence;
- last/current review findings and bounded review history;
- task-relative git **diff stat** (never the full diff);
- provider-call/review-attempt accounting (call counts, no token/cost data);
- blocked reason and final gate.

## API

`GET /api/tasks?limit=20` (authenticated, 1..100):

```json
{
  "tasks": [
    {"task_id": "DR-0001", "title": "...", "state": "DONE",
     "current": true, "updated_at": "...", "baseline_available": true}
  ],
  "returned": 1, "total": 1, "limit": 20, "truncated": false,
  "current_task": "DR-0001"
}
```

`GET /api/tasks/{task_id}` (authenticated; `DR-<4 digits>` grammar):

```json
{
  "task_id": "DR-0001",
  "title": "...",
  "state": "DONE",
  "current": true,
  "plan_ready": true,
  "implementation_passes": 1,
  "fix_iterations_used": 0,
  "baseline_available": true,
  "tests": {"passed": true, "evidence": ["..."]},
  "review": {"last": {"decision": "PASS", "summary": "...", "findings": []},
             "history": [], "current_findings": [], "open_p3": []},
  "git": {"available": true, "stat": "src/a.py | 2 +-", "truncated": false},
  "usage": {"implementer_calls": 1, "reviewer_calls": 1, "total_calls": 2,
            "provider_calls": [], "review_attempts": [],
            "token_usage_available": false, "cost_available": false},
  "final_gate": {"approved_by": "manual", "approved_at": "...", "note": ""},
  "blocked": {"code": null, "reason": ""}
}
```

Invalid/missing task IDs are `400 invalid_task_id` / `404 task_not_found`.
The task store is read through `ArtifactStore`; no path parameter is accepted.

## Bounds and redaction

- Task IDs must match `DR-\d{4}`; task scan cap 200, list cap 100.
- Test evidence: 30 lines, 1,000 chars each.
- Review summary 2,000 chars, description/evidence/recommendation 1,000,
  findings cap 50, history cap 10.
- Diff **stat only**, 16 KiB cap; full diff is never returned.
- Provider-call records cap 100; review attempts cap 20.
- All text passes `redact_text`; errors are bounded and type-prefixed.
- A missing/corrupt baseline or git failure returns `git.available: false`
  with a bounded reason, not a 500 and not a guessed diff.

## Non-goals

- No task/run action (start, continue, approve, review import, unblock,
  pause, interrupt, prompt, decide).
- No full diff, provider prompt/response, raw stdout/stderr or artifact file
  browser.
- No token/cost accounting where the provider record does not contain it;
  `token_usage_available`/`cost_available` are explicit false.
- No WebSocket/SSE.
- No arbitrary task directory or path access.

## Tests

- Seeded `TaskRun` through `ArtifactStore`, list/detail shape, missing/invalid
  IDs and unauthenticated access.
- Static Tasks-tab markers and `/api/tasks` reference.
- Full suite: **1,329 collected** (1,327 pass + 2 environment skips on this
  Windows host).

## Acceptance IDs

| ID | Criterion |
| --- | --- |
| C2a-1 | Task list/detail are authenticated GETs with task-id grammar |
| C2a-2 | Test status/evidence and review findings are bounded and redacted |
| C2a-3 | Git diff is stat-only, bounded and fails closed |
| C2a-4 | Provider call/review attempt accounting is present; token/cost explicitly unavailable |
| C2a-5 | No task/run control, full diff, raw output or arbitrary path is exposed |
| C2a-6 | Existing C1/A/B tests remain green |
