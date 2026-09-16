# DevRelay v0.3-B acceptance matrix — MCP tool surface

Status: **candidate implementation complete — ready for independent review**
(unreleased; package version stays `0.1.0`; public release remains `v0.1.0`).

Baseline: accepted v0.3-A at `bcf9627…` (documentation closeout `f4c92f3…`),
branch `v0.3-b-mcp-tool-surface`.  All evidence below is **offline**: the
deterministic v0.3-A stub over `httpx.MockTransport`, a real stdio MCP
subprocess, and a deterministic loopback fake OpenCode HTTP server created
inside the test process.  No external network, no model, no real OpenCode
server.

Legend: **COVERED** = automated test asserts it · **PARTIAL** = covered
indirectly · **DEFERRED** = documented, not automated in this stage.

## A. Discovery, inventory and lifecycle

| # | Criterion | Status | Evidence (`tests/test_v03b_mcp_tools.py` unless noted) |
| --- | --- | --- | --- |
| B1 | MCP server initializes and advertises the exact nine tools | COVERED | `test_tool_inventory_annotations_and_descriptions`, `tests/test_v03b_mcp_stdio.py::test_stdio_initialize_discovery_and_sequential_calls`, `…::test_stdio_raw_protocol_lines_and_clean_eof_exit` |
| B2 | Tool descriptions are a safety surface (exactly one prompt, never retries, inspect `submission_uncertain`/`reply_pending`, do not resubmit) | COVERED | `test_tool_inventory_annotations_and_descriptions` |
| B3 | Read tools marked read-only; `send_prompt`/`interrupt` not read-only; no false idempotency claim | COVERED | `test_tool_inventory_annotations_and_descriptions` |
| B4 | No dangerous low-level tool (HTTP/shell/subprocess/file/git/config/env/delete/token) | COVERED | `test_no_dangerous_low_level_tools` |
| B5 | No tool accepts a workspace path/cwd/directory | COVERED | `test_no_tool_accepts_a_workspace_path` |
| B6 | Multiple sequential calls in one session use the same bound workspace; clean exit on EOF; no stdout contamination | COVERED | `tests/test_v03b_mcp_stdio.py::test_stdio_initialize_discovery_and_sequential_calls`, `…::test_stdio_stdout_is_protocol_only`, `…::test_stdio_raw_protocol_lines_and_clean_eof_exit` |
| B7 | Malformed MCP input never crashes the process | COVERED | `tests/test_v03b_mcp_stdio.py::test_stdio_reports_errors_as_envelopes_without_tracebacks` |

## B. Bound workspace

| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| B8 | Valid workspace resolves/canonicalizes once and binds the surface | COVERED | `test_workspace_is_resolved_and_bound` |
| B9 | Invalid workspace (missing, uninitialized, invalid wiring) refuses startup before serving | COVERED | `test_invalid_workspace_refuses_startup`, `tests/test_v03b_mcp_stdio.py::test_stdio_invalid_workspace_refuses_before_serving` |
| B10 | Foreign sessions stay hidden by default and fail closed when addressed; `include_other_workspaces` remains explicit | COVERED | `test_foreign_session_is_hidden_and_fails_closed` |
| B11 | No cross-workspace switching, no discovery/scanning, no client-controlled cwd | COVERED | `test_no_tool_accepts_a_workspace_path`, `test_workspace_is_resolved_and_bound` |

## C. Read-only tools

| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| B12 | `devrelay_status`: schema/package versions, bound workspace, sanitized endpoint authority, configured flag, bridge operations, tool inventory, `acceptance_authority: false` | COVERED | `test_status_sanitizes_endpoint_and_never_returns_tokens`, `test_server_identity_and_schema_version`, `test_no_acceptance_authority_surface` |
| B13 | `opencode_health` returns the normalized health view; provider failure returns an error envelope | COVERED | `test_health_ok_and_provider_failure` |
| B14 | `opencode_get_session` returns the normalized session only | COVERED | `test_get_session_returns_normalized_session` |
| B15 | `opencode_read_messages` returns the accepted page semantics (`next_cursor`, `provider_message_count`, `window_truncated`, `cursor_unknown`, `replayed`) and no raw provider JSON | COVERED | `test_read_messages_exposes_page_semantics` |
| B16 | `opencode_calls` exposes sanitized durable records and reports corruption explicitly (never `[] / success`) | COVERED | `test_calls_ledger_is_readable_and_reports_corruption`, `test_calls_reports_a_corrupt_sequence` |
| B17 | No read tool returns tokens/credentials/config secrets | COVERED | `test_status_sanitizes_endpoint_and_never_returns_tokens`, `test_no_credential_leakage_in_any_tool_envelope` |

## D. `opencode_send_prompt` (v0.3-A semantics preserved)

| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| B18 | Synchronous success through the real `/message` contract: exactly one POST, full evidence fields, correlated reply | COVERED | `test_send_prompt_success_preserves_full_evidence`, `tests/test_v03b_mcp_stdio.py::test_stdio_send_prompt_end_to_end_against_the_loopback_fake` |
| B19 | `ReadTimeout`/`WriteTimeout` → `submission_uncertain`, `reply_pending`, `retry_safe: false`, one POST, no retry | COVERED | `test_send_prompt_timeout_is_uncertain_and_never_retryable` (read + write) |
| B20 | Connect failure → definitely not submitted (`submission_uncertain: false`, `retry_safe: true`), no follow-up implying acceptance | COVERED | `test_send_prompt_connect_failure_is_definitely_not_submitted` |
| B21 | 2xx with a non-credible media contract (SPA `text/html`) → submission uncertain, no resubmit | COVERED | `test_send_prompt_html_fallback_is_uncertain` |
| B22 | Rejected HTTP status → not accepted, not retry-safe | COVERED | `test_send_prompt_rejected_status_is_not_retry_safe` |
| B23 | Pending reply never substitutes a stale/pre-submit assistant message | COVERED | `test_send_prompt_pending_never_substitutes_a_stale_reply` |
| B24 | Model override uses the accepted `<providerID>/<modelID>` grammar and the real wire object; unmappable value fails before any request | COVERED | `test_send_prompt_model_override_uses_the_accepted_grammar`, `tests/test_v03b_mcp_stdio.py::test_stdio_send_prompt_end_to_end_against_the_loopback_fake` |
| B25 | The prompt never reaches durable artifacts; only `prompt_sha256`/`prompt_chars` are recorded | COVERED | `test_send_prompt_prompt_never_reaches_durable_artifacts`, `tests/test_v03b_mcp_stdio.py::test_stdio_send_prompt_end_to_end_against_the_loopback_fake` |
| B26 | The envelope never collapses ambiguity into "failed"/"safe to retry" (`ok`, `submission_uncertain`, `reply_pending`, `retry_safe` all preserved) | COVERED | `test_send_prompt_timeout_is_uncertain_and_never_retryable`, `…` (all D-rows) |

## E. Wait and interrupt

| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| B27 | `opencode_wait_idle`: idle completes; busy→idle and retry→idle keep polling with retry evidence; bounded busy wait times out honestly | COVERED | `test_wait_idle_states_through_mcp` |
| B28 | Wait bounds enforced (finite, positive, ≤ configured/MCP bound; unlimited not available) | COVERED | `test_wait_idle_timeout_bounds_are_enforced` |
| B29 | `opencode_interrupt`: 204 accepted (`interrupt_verified: false`), unsupported, vanished session, provider failure - none overstated as verified termination | COVERED | `test_interrupt_variants_through_mcp` |
| B30 | Waiting/interrupting never sends a model prompt | COVERED | `test_wait_idle_states_through_mcp`, `test_interrupt_variants_through_mcp` (POST counts asserted) |

## F. Validation and error boundary

| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| B31 | Invalid session id, blank/oversized prompt, bad model grammar, bad timeout, bad limit → envelope `mcp_invalid_argument` **before any bridge request** | COVERED | `test_argument_validation_produces_envelopes_and_zero_requests`, `test_cursor_is_bounded` |
| B32 | DevRelay errors keep their stable codes in the envelope | COVERED | `test_devrelay_errors_keep_their_stable_code` |
| B33 | Unexpected internal exceptions become a generic `internal_error` envelope plus a bounded, redacted stderr diagnostic - never a traceback, never a fake provider failure | COVERED | `test_unexpected_exception_is_generic_and_diagnosed` |
| B34 | SDK-level schema rejections stay bounded and leakless (documented SDK boundary) | COVERED | `test_sdk_schema_boundary_is_bounded_and_leakless`, `tests/test_v03b_mcp_stdio.py::test_stdio_reports_errors_as_envelopes_without_tracebacks` |
| B35 | A failed envelope is delivered with `isError: true` and keeps `structuredContent` | COVERED | `tests/test_v03b_mcp_stdio.py::test_stdio_reports_errors_as_envelopes_without_tracebacks` |

## G. Concurrency, cancellation, secrets, logging

| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| B36 | Side-effecting tool calls serialize per process; no overlapping submissions | COVERED | `test_side_effecting_tools_serialize_per_process` |
| B37 | Cancellation preserves already-issued evidence and never implies "safe to retry", with no automatic remote abort | COVERED | `test_cancellation_preserves_evidence_and_never_claims_safe_retry` |
| B38 | No credential/prompt leakage through results, ledger or diagnostics | COVERED | `test_no_credential_leakage_in_any_tool_envelope`, `test_send_prompt_prompt_never_reaches_durable_artifacts` |
| B39 | stdout carries protocol frames only; diagnostics on stderr | COVERED | `tests/test_v03b_mcp_stdio.py::test_stdio_stdout_is_protocol_only`, `…::test_stdio_raw_protocol_lines_and_clean_eof_exit` |
| B40 | No acceptance authority anywhere in the surface | COVERED | `test_no_acceptance_authority_surface` |

## H. Regression gate (v0.3-A unchanged)

| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| B41 | All v0.3-A suites unchanged and green (200 tests) | COVERED | `tests/test_v03a_opencode.py`, `tests/test_v03a_remediation.py`, `tests/test_v03a_second_remediation.py`, `tests/test_v03a_third_remediation.py`, `tests/test_v03a_real_protocol.py` |
| B42 | Full offline suite green with isolated `TEMP`/`TMP`/`TMPDIR`, count increased by the v0.3-B tests | COVERED | full-suite run recorded in the implementation report |
| B43 | No external model/OpenCode/network call required for acceptance | COVERED | every suite runs against `httpx.MockTransport`, a loopback fake or no HTTP at all |

## I. Deferred (non-blocking, recorded)

| # | Item | Why deferred |
| --- | --- | --- |
| B44 | Real MCP client smoke (ChatGPT/other host) against a disposable OpenCode session | explicitly **after** independent review; this round makes 0 real model calls |
| B45 | Streamable HTTP/SSE MCP transport | out of scope for v0.3-B |
| B46 | Multi-process concurrency / multi-workspace serving | v0.3-B is one process, one workspace, serialized side effects |
| B47 | Tool-level progress notifications, resources, prompts | not needed for the adapter surface |
