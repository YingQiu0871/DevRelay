# DevRelay v0.4-C2b — owner acceptance record

Status: **ACCEPTED / CLOSED by the owner on 2026-10-22.**  This is a C2b stage
acceptance, not a v0.4 release; no tag or publication was created.

## Accepted scope

C2b adds two explicit, bounded run controls:

- `POST /api/runs/{run_id}/decide` — complete / request_changes / stop, with
  `X-DevRelay-Confirm: apply`, body `confirm`, current `expected_updated_at`,
  state-machine validation and `decision_history`; no model call.
- `POST /api/runs/{run_id}/interrupt` — implementer/reviewer role only, requires
  a non-terminal run with a matching in-flight turn, uses only the run's
  recorded session, sends one abort request and reports
  `interrupt_verified: false` honestly.
- UI Decision/Interrupt controls with confirmation and state gating.

Explicit non-goals: pause, manual prompt, raw/normalized stream, start, phase
execution and recovery resolution.  C2c remains a separate gate.

## Evidence

| Item | Value |
| --- | --- |
| Implementation commit | `92e3d9a` |
| CI | [run 39787724867](https://github.com/YingQiu0871/DevRelay/actions/runs/39787724867) — 8/8 jobs |
| Local suite | 1,332 collected — 1,330 passed + 2 environment skips |
| Review | independent read-only review: APPROVE WITH FINDINGS, P0/P1 = 0 |
| Review record | [V04C2B_REVIEW.md](V04C2B_REVIEW.md) |
| Tests | stale revision, non-AWAITING 409, invalid enums/IDs, extra session id, in-flight role gating, interrupt session mapping, UI control markers |

## Limitations carried forward

- `expected_updated_at` is an optimistic hint, not a store-level CAS; the state
  machine is authoritative and second-precision timestamps leave a narrow
  same-second window.
- A run-recorded session is not an exclusive-ownership proof; manual CLI work
  reusing the same session in the workspace could still be interrupted.
- An accepted interrupt is not a verified terminal state.
- Pause, manual prompt and streaming remain C2c.

## Immutability

`v0.3.0` remains the published release.  C2b is unreleased `main` work.
