# DevRelay v0.3-A acceptance matrix

All evidence is **offline**: the deterministic in-memory OpenCode stub
(`tests/opencode_stub.py`) via `httpx.MockTransport`. No real OpenCode instance,
no network, no model call is required (or used) by any test below.

Legend: **COVERED** = automated test asserts it · **PARTIAL** = covered
indirectly · **DEFERRED** = documented, not automated in this stage.

| # | Criterion | Status | Evidence (`tests/test_v03a_opencode.py` unless noted) |
| --- | --- | --- | --- |
| A1 | Explicit endpoint required; unset `base_url` fails closed with a clear error | COVERED | `test_bridge_requires_an_explicit_endpoint`, `test_cli_opencode_requires_configuration` |
| A2 | Health probe returns normalized capability view | COVERED | `test_health_reports_capabilities` |
| A3 | Provider unavailable (connect error) → explicit `PROVIDER_UNAVAILABLE` | COVERED | `test_health_fails_closed_when_unreachable` |
| A4 | Request timeout → explicit `TIMED_OUT`, no retry | COVERED | `test_health_fails_closed_on_timeout` |
| A5 | Malformed/invalid-JSON payload → `MALFORMED_RESPONSE` | COVERED | `test_health_fails_closed_on_malformed_response` |
| A6 | Oversized response → bounded read, fail closed | COVERED | `test_oversized_response_fails_closed` |
| A7 | Session discovery, foreign workspaces hidden by default | COVERED | `test_list_sessions_filters_other_workspaces` |
| A8 | Session selection reports normalized state | COVERED | `test_get_session_reports_state` |
| A9 | Unknown session → hard failure | COVERED | `test_unknown_session_is_a_hard_failure` |
| A10 | Workspace/session mismatch → hard failure (no cross-workspace reuse) | COVERED | `test_workspace_mismatch_is_a_hard_failure` |
| A11 | Session without a reported workspace fails closed unless explicitly allowed | COVERED | `test_workspace_unknown_fails_closed_unless_explicitly_allowed` |
| A12 | Session id is always explicit; never guessed | COVERED | `test_session_id_is_required_and_never_guessed` |
| A13 | Message window normalization (roles, text, tool names only) | COVERED | `test_read_messages_window` |
| A14 | Cursor returns only new messages | COVERED | `test_read_messages_cursor_returns_only_new_messages` |
| A15 | Replayed cursor reported, not duplicated | COVERED | `test_read_messages_replayed_cursor_is_reported_not_duplicated` |
| A16 | Unknown/stale cursor flagged (`cursor_unknown`) | COVERED | `test_read_messages_unknown_cursor_is_flagged` |
| A17 | Malformed message payload fails closed | COVERED | `test_read_messages_malformed_payload_fails_closed` |
| A18 | One prompt submission returns the normalized assistant reply | COVERED | `test_send_prompt_success_returns_normalized_reply` |
| A19 | Agent/model selection forwarded when supported | COVERED | `test_send_prompt_agent_and_model_selection_are_forwarded` |
| A20 | Ack-only server: exactly one explicit follow-up read | COVERED | `test_send_prompt_ack_only_server_is_followed_by_one_read` |
| A21 | HTTP error body sanitized (no credential/secret leakage) | COVERED | `test_send_prompt_provider_error_is_sanitized` |
| A22 | Empty prompt refused locally (`ACCEPTED_LOCALLY` semantics) | COVERED | `test_send_prompt_requires_non_empty_prompt` |
| A23 | Bounded idle wait completes on idle with every poll accounted | COVERED | `test_wait_idle_completes_when_session_becomes_idle` |
| A24 | Idle wait timeout is explicit and final (no retry) | COVERED | `test_wait_idle_times_out_without_retrying` |
| A25 | Terminal session error is surfaced, not swallowed | COVERED | `test_wait_idle_returns_terminal_error_state` |
| A26 | Interrupt supported → `INTERRUPTED` | COVERED | `test_interrupt_is_reported_when_supported` |
| A27 | Interrupt unsupported → fail closed (`interrupt_unsupported`) | COVERED | `test_interrupt_fails_closed_when_unsupported` |
| A28 | Durable, unique, monotonic call ids; one record per issued request; no prompt text persisted | COVERED | `test_call_accounting_is_explicit_and_durable` |
| A29 | No hidden retries: a failed operation issues exactly one request | COVERED | `test_no_hidden_retries_on_failure` |
| A30 | CLI surface is thin: `health`, `sessions`, `calls` work through the bridge | COVERED | `test_cli_opencode_health_and_sessions` |
| A31 | OpenCode section is wiring only (never task policy); legacy snapshots tolerate it | COVERED | `tests/test_v02b_snapshot_integrity.py` (policy projection), `tests/test_config.py` (schema), plus the full suite |
| A32 | No v0.3-B functionality (role routing / orchestration / approval / MCP) | COVERED (negative) | self-audit + absence of any pipeline import in `devrelay/opencode/**`; documented non-goals |
| A33 | Real OpenCode smoke | DEFERRED | proposed separately after independent review of this offline implementation |

## Call accounting totals recorded by the suite

Every test above asserts exact counts where a count is meaningful
(`request_count`, `call_ids`, one record per issued request). The suite is
deterministic; there is no retry, no background work and no network.
