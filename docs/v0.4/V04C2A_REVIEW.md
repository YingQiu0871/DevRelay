# DevRelay v0.4-C2a — independent review record

Status: **C2a reviewed: APPROVE WITH FINDINGS (P0/P1 = 0); P2 findings
remediated; pending owner acceptance.**  No v0.4 tag or release is implied.

## Findings and disposition

| ID | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| C2a-R1 | P2 | Diff failure reason embedded raw exception text, which can include absolute paths or a failed diff fragment. | Fixed: failure reason is the fixed string `task diff unavailable`; no exception text or diff output is returned. |
| C2a-R2 | P2 | `BaselineService.task_delta` reconstructs a baseline tree and can write loose git objects (`hash-object -w`/`write-tree`), so the GET endpoint was not side-effect-free. | Changed to a read-only `git diff --stat <stored baseline tree>` with `--no-ext-diff --no-textconv`, a 15-second timeout and bounded capture.  No object reconstruction, no index/worktree mutation and no `task_delta` call.  Git may still read attributes; no repository write is performed by this path. |
| C2a-R3 | P2 | Task detail mapped every `DevRelayError` (including corrupt/schema-too-new state) to 404; list skipped unreadable tasks silently and could raise `AttributeError` for a malformed index. | Fixed: missing task is 404, corrupt/unreadable state is `503 task_store_unreadable`; malformed index is 503; list reports a `skipped` count; task IDs are ASCII `DR-[0-9]{4}` full matches. |
| C2a-R4 | P2 | Tests were thin around corruption, invalid IDs, diff absence, auth and task request races. | Added corrupt-index 503, trailing-newline invalid ID, no-full-diff assertion, unauthenticated access, UI markers and `taskDetailRequest` checks. |
| C2a-R5 | P3 | `MAX_TASK_SCAN` was unused; `\d`/`$` grammar was lax; diff cap was characters not KiB. | Scan cap is applied; regex uses ASCII digits + `fullmatch`; spec now states the 16k-character bound. |
| C2a-R6 | P3 | Spec example used `APPROVE` while the review enum is `PASS`; UI omitted review attempts/counts/open P3. | Spec example corrected to `PASS`; UI shows provider counts, token/cost-unavailable copy, review attempts and open P3 findings. |

## Verified good

- `/api/tasks` and `/api/tasks/{task_id}` are authenticated GETs; no path
  parameter, no task/run action.
- Task IDs are path-confined; missing/invalid/corrupt states are distinguished.
- Successful detail responses contain a stat, not a full diff.
- Test evidence/review text/final gate/blocked reasons pass `redact_text` and
  documented bounds; no token/cost values are fabricated.
- UI uses `textContent`, has no task/run control, guards task-detail requests and
  clears task/run detail on logout.

## Remaining gate

C2a is implemented and reviewed with findings; owner acceptance is pending.
C2b (pause/interrupt/manual prompt, streaming) remains a separate endpoint and
threat-model review.  A baseline-present diff-stat test remains a follow-up
because constructing a complete git baseline is environment-heavy; the failure
path is covered.
