# DevRelay v0.4-C1 — independent review record

Status: **C1 reviewed: APPROVE WITH FINDINGS (P0/P1 = 0); P2 findings
remediated; accepted by the owner on 2026-10-22.**  No v0.4 tag or release is
implied.  See [V04C1_ACCEPTANCE.md](V04C1_ACCEPTANCE.md).

## Findings and disposition

| ID | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| C1-R1 | P2 | `loadRunDetail` had no request-generation guard: clicking run A then B could render A last; closing during an in-flight load could reopen the panel; overlapping auto-refreshes were possible. | Fixed: a monotonic `runDetailRequest` is checked after every await; the close button and session clear invalidate it; `refreshInFlight` prevents overlapping refresh ticks; failed detail loads clear the selection and hide the panel. |
| C1-R2 | P2 | The spec promised `submission_uncertain`, but the turn row did not render it. | Fixed: turn rows now show `submission uncertain`, `reply pending` and `retry-safe` flags. |
| C1-R3 | P3 | Control test only grepped four IDs. | Extended to `decide`, prompt-related IDs, plus assertions for the request guard, 5s interval, timer cleanup and `submission_uncertain`. |
| C1-R4 | P3 | Stale error/selection state and logout could leave a rendered detail. | Fixed: successful refreshes clear the alert; failed detail loads clear selection; `clearSession` stops the timer, clears selection and hides the detail. |
| C1-R5 | P3 | Every auto-refresh rebuilt the run list and could disturb focus/scroll. | Recorded as a polish item; no correctness issue. |
| C1-R6 | P3 | Suite-count claims cannot be verified by a read-only reviewer. | The owner run executes the suite; C1's local full-suite count is recorded in the acceptance evidence when run. |

## Verified good

- C1 adds only Refresh/Close buttons, a checkbox and click-to-open rows; all
  C1 fetches are GETs and no pause/interrupt/prompt/decide action exists.
- All run values use `textContent`/DOM text APIs; no `innerHTML`, `outerHTML`,
  `insertAdjacentHTML` or `document.write`.
- Run IDs are URI-encoded and server-validated; no arbitrary path.
- Header session/token handling is unchanged; no cookie.
- Detail shows normalized TurnRecord/DecisionRecord evidence only, no raw
  provider prose.
- C2 (control, live stream, diff/tests/findings, cost) is explicitly deferred.

## Remaining gate

C1 is implemented and reviewed with findings.  Owner acceptance is pending.
C2 builds on this detail surface but requires a new endpoint/threat-model review;
C1 exposes no control capability.
