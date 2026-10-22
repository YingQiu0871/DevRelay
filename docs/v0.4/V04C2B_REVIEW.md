# DevRelay v0.4-C2b — independent review record

Status: **C2b reviewed: APPROVE WITH FINDINGS (P0/P1 = 0); P2 findings
remediated; pending owner acceptance.**  No v0.4 tag or release is implied.

## Findings and disposition

| ID | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| C2b-R1 | P2 | The `expected_updated_at` check is a compare-then-act hint; `updated_at` has second precision and the state machine reloads the run. | Documented explicitly as optimistic, not a store CAS.  The state machine remains authoritative; same-second ambiguity is a known residual. |
| C2b-R2 | P2 | State-machine rejections were mapped to 503, misclassifying client errors as provider unavailability. | Decision conflicts (`invalid_transition`, recovery/route/session/cycle conflicts, corrupt state) are now mapped to 409. |
| C2b-R3 | P2 | Interrupt was session-scoped only and could target an unrelated/reused session; spec overstated "run-owned". | Interrupt now requires a non-terminal run with an in-flight turn, and the selected role must match that in-flight turn.  The spec documents that the session is recorded on the run but is not a cryptographic ownership proof (bridge verifies workspace membership only). |
| C2b-R4 | P2 | Tests covered only happy paths; no invalid-ID, non-AWAITING, missing-confirm, extra-session-id, reviewer-role or error-path cases. | Added invalid-ID, non-AWAITING 409, missing body confirm, extra `session_id` 422, no-in-flight 409, role mapping and UI bounded-control tests.  The bridge success path still uses a monkeypatched `opencode_interrupt`; real transport validation is covered by the accepted bridge suite. |
| C2b-R5 | P3 | Controls were offered in states where the action would fail; copy said read-only/no run control. | UI disables decision unless `AWAITING_DECISION` and no in-flight turn; interrupt only with an in-flight turn.  Copy now says bounded run control. |
| C2b-R6 | P3 | `run-action-result` survived run switches; a `409 run_changed` did not reload the revision. | Detail loads clear the result; `run_changed` reloads and asks for a retry. |
| C2b-R7 | P3 | A post-logout detail load could race the login screen. | The existing request-generation counter/clearSession path remains the guard; no new request is accepted after the counter bump. |

## Verified good

- Only two new controls: decision and role-scoped interrupt; no pause, manual
  prompt, stream, start, phase execution or recovery endpoint.
- Both require session/bearer auth, `X-DevRelay-Confirm: apply` and body
  `confirm: "apply"`.
- Decision enums and run-id grammar are enforced; decision history is written
  by the accepted state machine with no model call.
- Interrupt uses the run's own role session, requires a matching in-flight turn,
  sends one abort request, and reports `interrupt_verified: false` honestly.
- UI confirms both actions, disables in-flight buttons, handles 401 and
  `run_changed`, and exposes no raw stream/prompt control.

## Remaining gate

C2b is implemented and reviewed with findings; owner acceptance is pending.
Pause, manual prompt and streaming remain C2c.  The interrupt session is not
exclusive-ownership proof; that residual is documented, not claimed solved.
