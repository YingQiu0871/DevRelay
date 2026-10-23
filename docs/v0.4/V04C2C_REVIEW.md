# DevRelay v0.4-C2c — independent review record

Status: **C2c reviewed: APPROVE WITH FINDINGS (P0/P1 = 0); P2 findings
remediated; accepted by the owner on 2026-10-22.**  No v0.4 tag or release is
implied.  See [V04C2C_ACCEPTANCE.md](V04C2C_ACCEPTANCE.md).

## Findings and disposition

| ID | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| C2c-R1 | P2 | Prompt/message provider I/O ran synchronously on the uvicorn event loop; a slow bridge could stall health and polling. | All four run-control routes now run their service call through `run_in_threadpool`; the event loop remains responsive and a slow fake can be exercised without freezing the server. |
| C2c-R2 | P2 | Manual prompt bypassed the orchestration turn lifecycle; two queued prompts could pass the `in_flight` check, and a pending manual reply could be attributed to the next turn. | Added a prompt lock and a `manual_prompt_pending` marker: concurrent prompts are serialized, and a reply-pending/uncertain result blocks further web prompts with `409`.  Post-acceptance (2026-10-23) the marker is durable under `.devrelay/web/manual_prompts.json` (metadata only, no prompt text), survives restart, and has a confirmed recovery endpoint.  The CLI can still start a turn; that residual remains. |
| C2c-R3 | P2 | Tests did not cover in-flight/terminal/blank prompts, pending `completed:false`, cursor bounds, message truncation, raw-secret redaction or the new UI. | Added terminal/in-flight/blank 409/422 tests, a pending/redaction test, cursor >512, 50/4,000/16,384 truncation and prompt/polling UI markers. |
| C2c-R4 | P3 | `session_id` was echoed despite the "no arbitrary session exposed" criterion. | Removed from C2c responses; the run's session IDs remain part of the accepted run summary, not a new C2c field. |
| C2c-R5 | P3 | `_data` re-raised upstream error text unredacted/unbounded; whitespace-only prompts reached the tool and returned 503. | `_data` redacts/bounds messages; the prompt model rejects blank/whitespace-only prompts with 422. |
| C2c-R6 | P3 | UI races: `call_ids.length` unguarded, polling suppressed a requested reload, role change could append stale messages. | Added array guard, queued reload after in-flight poll, run-id/role/request-generation checks and timer cleanup. |
| C2c-R7 | P3 | Pause is not implemented. | Explicitly documented: the accepted state machine has no pause state; C2c does not fake one.  Pause remains a separate future gate. |

## Verified good

- Prompt requires auth, confirmation header + body confirm, role enum, prompt
  bound and no in-flight/terminal run; session comes only from the run.
- Prompt sends one request, no retry/fallback; unconfirmed/pending results are
  reported as `completed:false` with evidence.
- Message polling is role/cursor scoped, caps messages at 50, 4,000 chars each
  and 16,384 total, redacts text, and passes cursor/window metadata.
- No pause, raw stream, arbitrary session/path or provider body is exposed.
- UI uses `textContent`, confirms prompts, polls only on opt-in, and clears
  timers on close/logout.

## Remaining gate

C2c is implemented, reviewed and accepted; it shipped in v0.4.0.  The durable
manual-prompt marker and recovery endpoint are post-release hardening (next
artifact).  The CLI can still start orchestration turns; pause remains
unsupported.
