# DevRelay v0.4-C2c — owner acceptance record

Status: **ACCEPTED / CLOSED by the owner on 2026-10-22.**  This is a C2c stage
acceptance, not a v0.4 release; no tag or publication was created.

## Accepted scope

C2c adds:

- `POST /api/runs/{run_id}/prompt` — one bounded manual prompt to the run's
  own implementer/reviewer session, confirmation header + body confirm, no
  in-flight/terminal run, no retry/fallback, pending/uncertain evidence.
- `GET /api/runs/{run_id}/messages` — role/cursor-scoped normalized message
  polling with 50-message, 4,000-char-per-message, 16,384-total bounds and
  redaction.
- UI manual-prompt controls and opt-in 5-second normalized message polling.
- Provider I/O offloaded through `run_in_threadpool`.

**Pause is explicitly not implemented**: the accepted orchestration state machine
has no pause state; interrupt is an abort, not a pause.

## Evidence

| Item | Value |
| --- | --- |
| Implementation commit | `3054bb5` |
| CI | [run 39822399627](https://github.com/YingQiu0871/DevRelay/actions/runs/39822399627) — 8/8 jobs |
| Local suite | 1,337 collected — 1,335 passed + 2 environment skips |
| Review | independent read-only review: APPROVE WITH FINDINGS, P0/P1 = 0 |
| Review record | [V04C2C_REVIEW.md](V04C2C_REVIEW.md) |
| Tests | prompt confirmation/role/in-flight/terminal/blank/pending, cursor bounds, message truncation/redaction, UI markers |

## Limitations carried forward

- **Post-acceptance (2026-10-23):** the pending marker is now durable under
  `.devrelay/web/manual_prompts.json` and survives a web process restart; a
  confirmed `POST /api/runs/{run_id}/prompt/recover` clears it without provider
  side effects.  The marker still does not store prompt/reply text.
- The CLI can still start an orchestration turn outside the web surface; the
  durable marker only blocks further web prompts for that run.
- A pending manual reply cannot be proven settled from the web surface; the
  operator must verify before clearing the marker.
- Pause remains unsupported; C2c does not fake it.
- Message polling is not a WebSocket/SSE stream.
- Provider I/O is offloaded, but a slow/hung provider can still hold one worker
  thread for the bridge timeout.

## Immutability

C2c shipped in v0.4.0 (released 2026-10-22); the durable marker/recovery work is
post-release `main` hardening, not part of the 0.4.0 artifact.
