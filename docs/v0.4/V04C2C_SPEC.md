# DevRelay v0.4-C2c — Manual Prompt & Normalized Message Polling

Status: **C2c ACCEPTED / CLOSED by the owner on 2026-10-22.**  The review is
recorded in [V04C2C_REVIEW.md](V04C2C_REVIEW.md) and the acceptance record in
[V04C2C_ACCEPTANCE.md](V04C2C_ACCEPTANCE.md).  C2c adds a manual prompt to an
existing run session and a bounded, normalized message-polling surface.

**Pause is not implemented in C2c.**  The accepted orchestration state machine
has no durable pause state; `interrupt` is an abort request, not a pause.  C2c
does not fake a pause by blocking a request or mutating a run into a new state.

## Scope

### Manual prompt

`POST /api/runs/{run_id}/prompt`

```json
{
  "role": "implementer|reviewer",
  "prompt": "bounded text",
  "confirm": "apply"
}
```

- Requires `X-DevRelay-Confirm: apply`.
- Run must be non-terminal and have no in-flight turn.
- Session ID comes only from the run's recorded implementer/reviewer session;
  no client-supplied session or arbitrary target is accepted.
- Prompt is 1..16,000 characters.
- Delegates to the accepted `opencode_send_prompt`; one submission, no retry or
  fallback.  An accepted-but-unconfirmed/pending submission is reported with
  `completed: false` and its evidence fields, not hidden.
- Returns bounded normalized message text plus call/status evidence; no raw
  provider body, tool arguments, prompt echo or credential.
- A pending/uncertain prompt records a durable marker under
  `.devrelay/web/manual_prompts.json` containing only run id, role session,
  evidence code and timestamps — never prompt/reply text.  Further web prompts
  for that run return `409 manual_prompt_pending` across process restarts.
- `POST /api/runs/{run_id}/prompt/recover` (header+body confirmation) clears
  the marker without sending, aborting or resubmitting anything.  Operators must
  verify the session first; the UI exposes the same explicit action.

### Message polling

`GET /api/runs/{run_id}/messages?role=implementer|reviewer&cursor=...`

- Session comes from the run's role session.
- Delegates to the accepted `opencode_read_messages` cursor window.
- Returns at most 50 messages; each text is redacted and bounded to 4,000
  characters with a 16,384-character total text budget; cursor is bounded to
  512 characters.
- `cursor_unknown`, `replayed`, `window_truncated` and
  `provider_message_count` are passed through.
- This is polling, not WebSocket/SSE; no server push listener is added.

### UI

Run detail gains:

- a role selector, bounded prompt textarea and Send prompt button, with an
  explicit confirmation;
- a Live normalized messages panel with role selector, manual Load, optional
  5-second polling and bounded message rendering;
- no pause button, no free-form stream, no auto-retry.

## Security boundary

- Same loopback Host/Origin, body limit and header/bearer session auth.
- Prompt and message routes require auth; prompt additionally requires the
  confirmation header and body `confirm`.
- `run_id` is the accepted grammar; `role` is a literal enum; cursor is bounded
  and passed only to the accepted message reader.
- No client-supplied session ID, provider URL, tool argument, filesystem path
  or raw output is accepted/returned.
- The durable marker is metadata-only and assumes one web writer process (the
  accepted bridge boundary); recovery requires explicit confirmation.
- Prompt text is not logged; it is sent once to the selected run session.
- Message text is sanitized by the accepted bridge and redacted again by the
  web adapter; output is bounded.
- Pause remains unsupported; C2c does not claim it.

## Non-goals

- No pause state or pause endpoint.
- No WebSocket/SSE live stream.
- No start, phase execution, recovery resolution, task action or project switch.
- No raw provider body/tool arguments, arbitrary session or external endpoint.
- No automatic retry/resubmission after an uncertain prompt submission.

## Tests

- Prompt: confirmation, role/session mapping, no in-flight, prompt bound,
  normalized reply, unauthenticated access.
- Messages: role scoping, cursor pass-through, bounded normalized message,
  invalid role and auth.
- UI: prompt/polling markers, no pause control.
- Marker: file persistence across a new service instance, no prompt text,
  corruption fail-closed, confirmed recovery.
- Full suite after marker hardening: **1,349 collected** (1,347 pass + 2
  environment skips on this Windows host).

## Acceptance IDs

| ID | Criterion |
| --- | --- |
| C2c-1 | Prompt requires auth, confirmation, role and no in-flight turn |
| C2c-2 | Prompt targets only the run's role session and never retries |
| C2c-3 | Message polling is role/cursor scoped and bounded/redacted |
| C2c-4 | No pause, stream, arbitrary session, path or raw output is exposed |
| C2c-5 | UI confirms prompt, polls only on request/opt-in, and has no pause control |
| C2c-7 | Pending marker survives a process restart without storing prompt text |
| C2c-8 | Confirmed recovery clears the marker without provider side effects |
| C2c-6 | Existing C1/C2a/C2b/A/B tests remain green |
