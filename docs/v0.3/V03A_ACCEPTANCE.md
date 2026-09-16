# DevRelay v0.3-A acceptance matrix

All evidence is **offline**: the deterministic in-memory OpenCode stub
(`tests/opencode_stub.py`) via `httpx.MockTransport`. No real OpenCode instance,
no network, no model call is required (or used) by any test below.

Legend: **COVERED** = automated test asserts it · **PARTIAL** = covered
indirectly · **DEFERRED** = documented, not automated in this stage.

| # | Criterion | Status | Evidence (`tests/test_v03a_opencode.py`, plus `tests/test_v03a_remediation.py` for the R-rows) |
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
| A22 | Empty prompt refused locally with a hard error (`ACCEPTED_LOCALLY` is reserved and never emitted) | COVERED | `test_send_prompt_requires_non_empty_prompt` |
| A23 | Bounded idle wait completes on idle with every poll accounted | COVERED | `test_wait_idle_completes_when_session_becomes_idle` |
| A24 | Idle wait timeout is explicit and final (no retry) | COVERED | `test_wait_idle_times_out_without_retrying` |
| A25 | Terminal session error is surfaced, not swallowed | COVERED | `test_wait_idle_returns_terminal_error_state` |
| A26 | Interrupt supported → `INTERRUPTED` | COVERED | `test_interrupt_is_reported_when_supported` |
| A27 | Interrupt unsupported → fail closed (`interrupt_unsupported`) | COVERED | `test_interrupt_fails_closed_when_unsupported` |
| A28 | Durable, unique, monotonic call ids; one record per issued request; no prompt text persisted | COVERED | `test_call_accounting_is_explicit_and_durable` |
| A29 | No hidden retries: a failed operation issues exactly one request | COVERED | `test_no_hidden_retries_on_failure` |
| A30 | CLI surface is thin: `health`, `sessions`, `calls` work through the bridge | COVERED | `test_cli_opencode_health_and_sessions` |
| A31 | OpenCode section is wiring only (never task policy); legacy snapshots tolerate it | COVERED | `test_opencode_section_is_projected_out_of_the_policy` (real `resolve_policy_config` + `workspace_policy_overrides`), `test_legacy_full_config_snapshot_tolerates_opencode_only_when_lenient` (`opencode`/`codex`/`profiles`/`review.provider` dropped only in lenient mode; strict mode still fails) |
| A32 | No v0.3-B functionality (role routing / orchestration / approval / MCP) | COVERED (negative) | self-audit + absence of any pipeline import in `devrelay/opencode/**`; documented non-goals |
| A33 | Real OpenCode smoke | DEFERRED | proposed separately after independent review of this offline implementation |

## Independent-review remediation (R-rows)

All R-rows live in `tests/test_v03a_remediation.py` (offline stub + fake clock +
spy transport).  58 of its 66 tests fail against the pre-remediation source of
`71feaff`, so each one is a regression test for a specific finding rather than a
restatement of existing coverage; the 8 that already passed are marked *(guard)*.

| # | Finding | Status | Evidence |
| --- | --- | --- | --- |
| R1 | P1-1 whole-operation idle budget: deadline set before the ownership probe, every request clamped to the remaining budget, no request after expiry, honest duration evidence | COVERED | `test_wait_idle_keeps_probe_and_polls_inside_the_declared_budget`, `test_wait_idle_explicit_timeout_wins_over_the_configured_default`, `test_wait_idle_probe_alone_cannot_outlive_a_tiny_budget`, `test_wait_idle_with_an_exhausted_budget_issues_no_request_at_all`, `test_wait_idle_records_every_poll_as_its_own_ledger_call` *(guard)* |
| R2 | P1-2 message window keeps the newest messages; truncation and cursor honesty; config bound | COVERED | `test_message_window_keeps_the_newest_and_reports_truncation`, `test_message_window_cursor_near_the_tail_is_not_reported_as_nothing_new`, `test_message_window_cursor_outside_the_window_is_flagged_not_dropped`, `test_message_window_configuration_above_the_hard_max_fails_closed` |
| R3 | P1-3 reply correlation: no stale reply, no id-bearing envelope, ack + later reply, follow-up 404/500 honest, accounting == ledger, no resubmission | COVERED | `test_send_prompt_never_substitutes_a_stale_assistant_reply`, `test_send_prompt_never_accepts_an_id_bearing_envelope_as_a_reply`, `test_send_prompt_ack_then_reply_correlates_only_the_new_message`, `test_send_prompt_follow_up_404_is_an_honest_post_acceptance_result`, `test_send_prompt_follow_up_failure_is_surfaced_not_swallowed` |
| R4 | P1-4 the OpenCode bearer token is denylisted for Codex children (real child process) and reported by `doctor` without its value | COVERED | `test_opencode_token_is_in_the_codex_child_denylist`, `test_codex_child_never_receives_the_opencode_token`, `test_doctor_reports_the_scrubbed_opencode_token` |
| R5 | P2-A ambient proxy/CA environment cannot reroute the control channel | COVERED | `test_transport_ignores_ambient_proxy_configuration` |
| R6 | P2-B session-id grammar + returned-id mismatch, zero requests for invalid ids | COVERED | `test_invalid_session_ids_issue_zero_requests`, `test_returned_session_id_must_match_the_requested_one`, `test_returned_id_mismatch_blocks_acting_operations`, `test_valid_opaque_session_id_is_accepted` *(guard)* |
| R7 | P2-C interrupt semantics: 204/JSON success, 404, 405/501, provider error, oversized body | COVERED | `test_interrupt_accepts_an_empty_204_without_claiming_verification`, `test_interrupt_accepts_a_json_success_body`, `test_interrupt_of_a_vanished_session_is_not_reported_as_unsupported`, `test_interrupt_unsupported_statuses_fail_closed`, `test_interrupt_provider_error_is_not_mislabelled_as_unsupported`, `test_interrupt_oversized_response_is_malformed_not_unsupported` |
| R8 | P2-D prompt/token echoes never reach the ledger or the console; snippets bounded; digest honestly documented as a fingerprint | COVERED | `test_prompt_and_token_echo_never_reach_the_ledger`, `test_follow_up_echo_is_scrubbed_and_bounded`, `test_prompt_digest_is_an_identifier_not_a_secrecy_mechanism` *(guard)* |
| R9 | P2-E ledger fails closed: corrupt/malformed sequence, deleted sequence recovery, crash gap, identity collision | COVERED | `test_corrupt_sequence_with_records_fails_closed`, `test_malformed_sequence_payload_fails_closed`, `test_deleted_sequence_recovers_from_the_existing_ledger`, `test_allocation_after_a_crash_gap_never_reuses_an_identity`, `test_existing_call_identity_is_never_overwritten` |
| R10 | P2-F `--json` keeps a failing exit status; exit codes reflect the operation, not the renderer | COVERED | `test_cli_json_mode_keeps_a_failing_exit_status`, `test_cli_json_mode_succeeds_only_when_the_operation_does`, `test_cli_reports_a_pending_reply_as_a_non_zero_but_honest_result` |
| R11 | PART III config coverage: defaults, bounds, `extra="forbid"`, `opencode: null`, base-URL scheme/userinfo/path, policy projection, legacy snapshot, `allow_unknown_workspace` | COVERED | `test_opencode_config_defaults_and_bounds`, `test_opencode_base_url_must_be_unambiguous`, `test_opencode_base_url_normalizes_trailing_slash`, `test_null_opencode_section_means_not_configured`, `test_invalid_opencode_wiring_in_the_workspace_file_fails_closed`, `test_opencode_section_is_projected_out_of_the_policy` *(guard)*, `test_legacy_full_config_snapshot_tolerates_opencode_only_when_lenient` *(guard)*, `test_allow_unknown_workspace_controls_the_ownership_verdict` |

## Second independent-review remediation (S-rows)

All S-rows live in `tests/test_v03a_second_remediation.py` (offline OpenCode stub,
offline Codex stub spawned as a real child process, no network).  **36 of its 49
tests fail against `f5d487d`** for the actual failure mechanism (verified by
temporarily reverting the seven remediated source files and restoring them
byte-identically); the 13 that already passed are guards.

| # | Finding | Status | Evidence |
| --- | --- | --- | --- |
| S1 | P1-A every Codex child process (legacy text runtime, `--version`, `exec --help`, capability detection, doctor) is spawned through a centralized credential scrub; the parent keeps its credentials | COVERED | `test_every_codex_child_path_is_scrubbed` (real child env captured per invocation), `test_provider_probes_pass_the_denylist_to_the_runner`, `test_doctor_codex_probes_are_scrubbed` |
| S2 | P1-B a 2xx submission with an unusable body (`204`, empty `200`, invalid JSON, oversized) is post-acceptance: one POST, no resubmission, follow-up attempted, `reply_pending`, POST evidence preserved, accounting == ledger | COVERED | `test_2xx_with_an_unusable_body_is_post_acceptance` (4 cases), `test_2xx_with_an_unusable_body_still_correlates_a_later_reply`, `test_4xx_submission_is_still_a_failed_operation` |
| S3 | P1-C the anti-DoS pre-cap keeps the true newest tail (>2000 entries), with honest counts/cursor/replay and working reply correlation on large sessions | COVERED | `test_large_payloads_keep_the_true_newest_messages` (2100, 2300), `test_large_payload_cursor_and_replay_semantics_are_honest`, `test_send_prompt_sees_a_reply_appended_to_a_large_session` |
| S4 | P1-D JSON/backslash/percent-escaped provider echoes of the prompt or token never reach the result, CLI output or any durable record (POST, follow-up and poll paths) | COVERED | `test_post_failure_echo_is_scrubbed_in_every_encoding`, `test_follow_up_and_poll_echoes_are_scrubbed_in_every_encoding`, `test_cli_output_never_renders_a_recoverable_echo` |
| S5 | P1-E parser bombs (extreme nesting, over-long integer, invalid JSON) normalize into `MALFORMED_RESPONSE`, settle the ledger record, and never traceback in the CLI; programming errors still propagate | COVERED | `test_parser_bombs_are_malformed_and_settled` (6 cases), `test_parser_bomb_does_not_traceback_in_the_cli`, `test_programming_errors_still_propagate` |
| S6 | PART II-A a failing ownership/boundary probe keeps the calls it already issued | COVERED | `test_boundary_failure_keeps_the_probe_accounting`, `test_probe_failure_keeps_its_own_call` |
| S7 | PART II-B a malformed follow-up keeps the `send_prompt` identity with embedded follow-up status | COVERED | `test_malformed_follow_up_keeps_the_send_identity` |
| S8 | PART II-C dot-segment session ids are refused before URL construction | COVERED | `test_dot_segment_session_ids_issue_zero_requests`, `test_dotted_ids_that_are_not_dot_segments_still_work` |
| S9 | PART II-D the full returned session id is compared (no truncation-equal collision) | COVERED | `test_returned_id_suffix_cannot_hide_behind_truncation`, `test_returned_id_mismatch_is_still_detected` |
| S10 | PART II-E malformed authorities/ports/control characters/percent-encoded authorities are configuration errors before httpx, and config errors never echo an embedded password | COVERED | `test_malformed_urls_are_configuration_errors`, `test_malformed_authority_never_reaches_httpx`, `test_config_errors_never_echo_an_embedded_password`, `test_accepted_urls_construct_a_transport` |
| S11 | PART II-F a refused create-new leaves no phantom in-memory ledger record | COVERED | `test_refused_create_new_leaves_no_phantom_record` |

## Third independent-review blocker remediation (T-rows)

All T-rows live in `tests/test_v03a_third_remediation.py` (offline OpenCode stub
with per-route transport failures; no network, no model).  **22 of its 23 tests
fail against `6e0eb61`** for the actual mechanism (verified by temporarily
reverting the four remediated source files and restoring them byte-identically);
the one that already passed is the guard that a *correlated* reply is still
returned.

| # | Finding | Status | Evidence |
| --- | --- | --- | --- |
| T1 | P1 POST `ReadTimeout`/`WriteTimeout` are submission-uncertain: one POST, no retry, `submission_uncertain`, `reply_pending`, explicit "may already have been accepted / do not resubmit" evidence, one bounded follow-up, accounting == ledger, nothing left `ISSUED` | COVERED | `test_post_timeout_is_submission_uncertain` (read + write), `test_later_reply_after_a_post_timeout_stays_flagged_uncertain` |
| T2 | P1 POST `ConnectTimeout`/`ConnectError` are a definite "not submitted" outcome (no follow-up implying acceptance, no retry) | COVERED | `test_post_connect_failure_is_definitely_not_submitted` (connect timeout + connect error) |
| T3 | P1 the classification itself (which failures prove nothing was submitted, exact error types and call states) | COVERED | `test_transport_failure_classes_are_classified`, `test_non_post_read_timeout_is_not_a_submission_uncertainty` |
| T4 | SMOKE BLOCKER a post-acceptance result never exposes the pre-submission message window/page (`messages == []`, `page is None`, old assistant text absent) for follow-up 500, follow-up timeout, provider unavailable, vanished session, malformed follow-up, still-pending and POST read timeout | COVERED | `test_no_pre_submission_reply_is_exposed` (7 modes), `test_a_correlated_reply_is_still_returned` (guard) |
| T5 | Human CLI states the submission truth and the pending reply, never prints an old reply, and agrees with `--json` | COVERED | `test_human_output_states_the_submission_truth` (5 modes), `test_pending_human_output_says_do_not_resubmit` |
| T6 | Adjacent: a genuine HTTP rejection keeps its status as submission evidence (`submission_status`, `submission_body == ""`) | COVERED | `test_rejected_submission_keeps_the_http_status` (401, 500) |

## A33 real-protocol remediation (V-rows)

All V-rows live in `tests/test_v03a_real_protocol.py` (offline stub modelling the
**verified** OpenCode 1.18.11 wire contract; fixtures derived from the installed
server's `/doc`).  **28 of its 30 tests fail against `780c2fd`** for the actual
mechanism (verified by temporarily reverting the four remediated source files and
restoring them byte-identically); the two that already passed are the
stale-reply guard for the HTML case and a stub-self-check.

| # | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| V1 | submission uses the real route `POST /session/{id}/message`, exactly one POST, and the nonexistent `/prompt` route is never attempted (no fallback) | COVERED | `test_submission_uses_the_real_message_route_exactly_once`, `test_unknown_route_in_the_stub_matches_the_real_spa_behaviour` |
| V2 | minimum request body is `parts` only; optional members omitted unless requested | COVERED | `test_minimum_request_body_is_parts_only` |
| V3 | `agent` forwarded as a string; `model` encoded as the real `{providerID, modelID}` identity; unmappable override fails locally before any request | COVERED | `test_agent_is_forwarded_and_model_is_a_structured_identity`, `test_unmappable_model_override_fails_locally_before_any_request` |
| V4 | real `{info, parts}` response normalizes to exactly one new assistant reply; raw wire objects do not escape; unknown parts stay limited | COVERED | `test_real_sync_response_normalizes_to_one_new_assistant_reply`, `test_real_sync_response_with_unknown_parts_stays_limited` |
| V5 | assistant-role requirement: a non-assistant/incomplete body is never the reply (fail closed, no stale reply, accounting intact) | COVERED | `test_non_assistant_or_incomplete_response_is_not_a_reply`, `test_ack_only_json_body_stays_accepted_but_pending` |
| V6 | 2xx evidence: a JSON body with an unusable body is accepted (not "definitely failed"); a 2xx whose media type is not credible (SPA `text/html`) is submission-uncertain, one POST, no resubmit, ledger settled with the media type | COVERED | `test_json_endpoint_with_a_broken_body_is_accepted_not_uncertain`, `test_html_200_fallback_is_submission_uncertain`, `test_html_200_fallback_never_substitutes_a_stale_reply` |
| V7 | `wait_idle` uses the real `/session/status` contract (idle, busy→idle, retry→idle with evidence, bounded busy timeout, missing entry = idle, target absent while another session is busy, malformed payloads fail closed) and no longer polls the session detail for a nonexistent state field | COVERED | `test_wait_idle_status_idle_completes`, `test_wait_idle_busy_then_idle`, `test_wait_idle_retry_keeps_evidence_and_continues`, `test_wait_idle_bounded_busy_timeout`, `test_wait_idle_missing_entry_means_idle`, `test_wait_idle_target_absent_while_another_session_is_busy`, `test_wait_idle_malformed_status_fails_closed`, `test_wait_idle_does_not_poll_the_session_detail_for_state` |
| V8 | human and `--json` output tell the same truth for the unexpected-contract case | COVERED | `test_human_output_reports_the_unexpected_contract` |

## Call accounting totals recorded by the suite

Every test above asserts exact counts where a count is meaningful
(`request_count`, `call_ids`, one record per issued request). The suite is
deterministic; there is no retry, no background work and no network.

Accounting totals asserted by the real-protocol suite: a synchronous `/message`
submission with an inline reply is `4` requests (probe + boundary session +
boundary message list + POST); `wait_idle` is the ownership probe plus one status
poll per observation (`2` for the first answer, `4` for busy→busy→idle), and a
bounded busy timeout accounts every poll; every case asserts
`request_count == len(ledger.read_records())`, `call_ids` matching the ledger and
no record left `ISSUED`.

Accounting totals asserted by the third-remediation suite: a POST read/write
timeout is `6` requests (probe + boundary session + boundary messages + POST +
the single bounded follow-up session/message read); a POST connect failure is `4`
(no follow-up is issued, because nothing was submitted); a rejected POST (401/500)
is `4`.  In every case `request_count == len(ledger.read_records())`, `call_ids`
matches the ledger exactly and no record is left `ISSUED`.

Accounting totals asserted by the remediation suites: an ack-only `send_prompt`
with a follow-up read is `6` requests (probe + boundary session + boundary
messages + POST + follow-up session + follow-up messages); the same operation
with a failing follow-up is still `5 == len(ledger.read_records())`; an unusable
2xx submission body is also `6`; a failing boundary read is `3` (probe + boundary
session + failing message read); and no record is ever left `ISSUED`.
