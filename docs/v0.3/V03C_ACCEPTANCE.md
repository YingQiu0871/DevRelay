# DevRelay v0.3-C acceptance matrix — agent role routing

> Later status (2026-10-21): released as part of DevRelay 0.3.0.

Status: **ACCEPT — DEVRELAY v0.3-C AGENT ROLE ROUTING** — functional development
**CLOSED** (accepted internally; **UNRELEASED**).

| Field | Value |
| --- | --- |
| Accepted functional candidate | `eabb667d1bd9e379d3b7105d72b6a2751bc2a32b` (branch `v0.3-c-agent-role-routing`) |
| Functional development | `CLOSED` |
| Release state | `UNRELEASED` (no public v0.3 release exists) |
| Package version | `0.1.0` (unchanged) |
| Public release | `v0.1.0` |
| Findings at acceptance | P0 = 0 · P1 = 0 · smoke-blocking P2 = 0 (non-blocking P2/P3 carried in `docs/BACKLOG.md`) |
| Next stage | `v0.3-D Bounded Orchestration — NEXT / NOT STARTED` |

Acceptance rests on the **combined** evidence of two bounded real runs (sections
I.1-I.3): implementer → `opencode-go/deepseek-v4.1-flash` and reviewer →
`opencode-go/glm-5.3-flash`, each with exactly one real model turn and exactly one
`POST /session/{id}/message`.  Branch `v0.3-c-agent-role-routing`, based on the
v0.3-B acceptance closeout `c883bab…` (accepted v0.3-B runtime `d058d62…`).

### History (preserved as evidence; never rewritten into one clean success story)

1. v0.3-C candidate `eabb667…`: roles package, three role-aware MCP tools (12
   total), 140 new offline tests;
2. independent static/offline review:
   `APPROVE V0.3-C FOR ONE REAL ROLE-ROUTING SMOKE WITH RECORDED P2/P3`, which
   independently proved exact implementer/reviewer route separation, caller
   override that cannot influence the route, no default/fallback, raw
   `opencode_send_prompt` preserved, exactly-one submission, workspace ownership,
   no acceptance authority, no orchestration, official stdio integration and the
   full isolated suite at `809 passed`;
3. first real two-role smoke: **`FAIL — V0.3-C REAL ROLE-ROUTING SMOKE`** — the
   implementer real route itself succeeded (`opencode-go/deepseek-v4.1-flash`,
   exactly one POST, real inference, truthful metadata, no retry/fallback/
   orchestration) and the reviewer turn was deliberately **not** invoked; the run
   failed only because its harness required the entire normalized assistant text
   to equal a sentinel;
4. investigation established that the apparent implementer "preamble" came from an
   **inherited normalization behavior**: OpenCode provider `reasoning` parts are
   currently normalized by accepted v0.3-A into `kind="text"`.  That harness
   condition therefore tested a property outside the v0.3-C routing contract;
5. reviewer-only completion smoke:
   **`PASS — V0.3-C REVIEWER ROUTING COMPLETION SMOKE`**
   (`opencode-go/glm-5.3-flash`, three-way route agreement);
6. combined real evidence establishes both semantic routes → this acceptance.

The original FAIL is kept on purpose: it is evidence that the smoke criterion
itself was too strict for the provider-part normalization model.  The first run is
**not** restated as PASS, and its routing half is used only for what it actually
proved.

Sections A-H below are **offline** evidence: the real MCP SDK dispatch over the
real accepted v0.3-A bridge wired to the deterministic OpenCode stub
(`httpx.MockTransport`), plus a real stdio MCP subprocess against a deterministic
loopback fake OpenCode server.  The real role-routed calls are the separate,
bounded smoke runs recorded in sections I.1-I.3.

Legend: **COVERED** = automated test asserts it · **PARTIAL** = covered
indirectly · **DEFERRED** = documented, not automated in this stage.

## A. Role configuration

| # | Criterion | Status | Evidence (`tests/test_v03c_role_config.py` unless noted) |
| --- | --- | --- | --- |
| C1 | Both roles load exactly (model + optional agent) | COVERED | `test_both_roles_load_exactly` |
| C2 | Role routes are runtime wiring, never task policy (excluded from policy overrides; `PolicyDocument` has no `roles`) | COVERED | `test_role_routes_are_wiring_never_policy` |
| C3 | A legacy full-config dump containing `roles` stays loadable and records the dropped key | COVERED | `test_legacy_full_config_snapshot_tolerates_the_roles_section`, `tests/test_v03a_remediation.py` (unchanged behavior, one enumerated key list extended) |
| C4 | Absent / null / empty `roles:` section is valid and simply unconfigured | COVERED | `test_missing_roles_section_is_valid_and_unconfigured[absent\|null\|empty]` |
| C5 | One role configured leaves the other unconfigured (implementer missing / reviewer missing) | COVERED | `test_only_one_role_configured_leaves_the_other_unconfigured`, `test_empty_model_is_unconfigured_and_invalid_grammar_is_invalid` |
| C6 | Blank model is `role_unconfigured`, malformed model is `role_invalid_route` (distinct, deterministic) | COVERED | `test_blank_model_is_unconfigured_not_invalid`, `test_empty_model_is_unconfigured_and_invalid_grammar_is_invalid` |
| C7 | Malformed agent type is rejected at load; blank agent is rejected locally | COVERED | `test_malformed_agent_type_is_rejected_at_load`, `tests/test_v03c_roles.py::test_malformed_agent_values_fail_locally` |
| C8 | Unsupported role names, role-level prompt templates, retry policies, candidate lists and endpoint overrides are rejected | COVERED | `test_unsupported_role_configuration_is_rejected[unsupported-role\|prompt-template\|retry-policy\|candidate-list\|endpoint]` |
| C9 | The installed template documents the section (commented) and yields unconfigured roles | COVERED | `test_default_template_documents_roles_and_installs_unconfigured` |
| C10 | The role configuration is frozen (immutable value object) | COVERED | `test_roles_config_is_frozen` |
| C11 | Workspace-file and live-wiring views agree | COVERED | `test_workspace_file_and_wiring_agree_on_roles` |

## B. Resolution, vocabulary and error taxonomy

| # | Criterion | Status | Evidence (`tests/test_v03c_roles.py` unless noted) |
| --- | --- | --- | --- |
| C12 | Exactly two supported roles (`implementer`, `reviewer`); no vendor/model identity in code | COVERED | `test_supported_roles_are_exactly_implementer_and_reviewer` |
| C13 | Resolution returns the exact configured route for each role, normalized spelling | COVERED | `test_resolution_returns_the_exact_configured_routes`, `test_resolution_normalizes_the_configured_model_spelling`, `test_multi_slash_model_keeps_the_provider_boundary` |
| C14 | Exact matching only: no case folding, alias, prefix/similarity match, no inference from prompt/session/availability | COVERED | `test_exact_role_names_are_accepted`, `test_unknown_roles_fail_locally[15 cases]`, `test_no_fuzzy_or_inferred_role_selection` |
| C15 | Typed local taxonomy: `role_unknown` / `role_unconfigured` / `role_invalid_route`, one shared base class | COVERED | `test_unknown_roles_fail_locally`, `test_unconfigured_role_is_typed_and_local`, `test_malformed_configured_model_is_an_invalid_route`, `test_routing_errors_share_one_base_class` |
| C16 | The model grammar is the accepted v0.3-A one (no second grammar); role config inherits it verbatim | COVERED | `test_role_config_inherits_the_accepted_grammar_verbatim`, `test_model_identity_reuses_the_accepted_bridge_grammar` |
| C17 | Route value object is frozen and carries only role/model/agent/source (no prompt, secret or policy) | COVERED | `test_role_route_is_frozen_and_carries_no_secret_or_policy` |
| C18 | Sanitized views: `public()` for the read-only tools, `route_evidence()` for sends (includes the wire identity) | COVERED | `test_public_and_evidence_views_are_sanitized` |
| C19 | Omitted agent is `None`/absent, never an empty string | COVERED | `test_omitted_agent_is_none_never_empty_string` |
| C20 | Read-only views describe every supported role, including `unconfigured`/`invalid` states | COVERED | `test_list_roles_reports_every_supported_role_with_state`, `test_roles_summary_is_compact_and_truthful` |
| C21 | Dependency direction: role package never imports MCP; accepted opencode package never imports roles (AST import analysis) | COVERED | `test_roles_package_never_imports_mcp`, `test_accepted_opencode_package_never_imports_roles` |
| C22 | No HTTP, shell or socket code inside the role package | COVERED | `test_roles_package_contains_no_http_or_shell_code` |

## C. Role-aware execution (P1 invariants)

| # | Criterion | Status | Evidence (`tests/test_v03c_roles.py` + `tests/test_v03c_role_tools.py`) |
| --- | --- | --- | --- |
| C23 | **The caller cannot override model/agent**: the operation has no such parameter and no such MCP input property | COVERED | `test_role_aware_send_accepts_no_model_or_agent_argument`, `test_role_send_input_schema_has_no_route_override`, `test_caller_supplied_model_and_agent_are_ignored` (configured route still reaches the wire) |
| C24 | Resolution happens before the bridge: a routing failure performs zero bridge calls | COVERED | `test_send_role_prompt_resolves_before_touching_the_bridge` |
| C25 | One delegation per invocation: only the resolved model/agent, never a retry or a fallback | COVERED | `test_send_role_prompt_delegates_once_with_the_resolved_route`, `test_send_role_prompt_does_not_retry_or_fall_back`, `test_no_fallback_model_is_ever_used` |
| C26 | Role definitions cannot carry credentials (schema has only model/agent) | COVERED | `test_role_configuration_cannot_carry_credentials` |

## D. Implementer/reviewer separation and agent routing

| # | Criterion | Status | Evidence (`tests/test_v03c_role_tools.py`) |
| --- | --- | --- | --- |
| C27 | Distinct fixtures stay distinct and reach their own wire models: implementer -> `{"providerID": "provider-a", "modelID": "model-a"}`, reviewer -> `{"providerID": "provider-b", "modelID": "model-b"}` | COVERED | `test_implementer_and_reviewer_reach_their_own_wire_models` |
| C28 | No cross-routing between the two roles | COVERED | `test_no_cross_routing_between_the_two_roles` |
| C29 | The durable ledger records the routed model per role | COVERED | `test_ledger_records_the_routed_model_for_each_role` |
| C30 | The route follows configuration only (changing config changes the wire model) | COVERED | `test_role_route_is_switched_only_by_configuration` |
| C31 | Configured agent reaches the wire for each role | COVERED | `test_configured_agent_reaches_the_wire[implementer\|reviewer]` |
| C32 | An unconfigured agent is omitted from the request entirely (no empty-string agent) | COVERED | `test_omitted_agent_is_left_out_of_the_request_entirely`, `test_only_one_role_needs_an_agent` |

## E. MCP surface, envelopes and auditability

| # | Criterion | Status | Evidence (`tests/test_v03c_role_tools.py` unless noted) |
| --- | --- | --- | --- |
| C33 | Exactly 12 tools: the accepted nine unchanged and in order, plus exactly three | COVERED | `test_inventory_is_the_accepted_nine_plus_exactly_three` |
| C34 | Honest annotations: the two role views are read-only, the role send is side-effecting and not idempotent | COVERED | `test_role_tool_annotations_are_honest` |
| C35 | Input schemas expose only `role` / `session_id` / `prompt` (no model, agent, workspace, endpoint, retry) | COVERED | `test_role_send_input_schema_has_no_route_override` |
| C36 | Descriptions are a safety surface (semantic role, no override, exactly one turn, no retry, inspect uncertainty, reviewer text is not a decision, no acceptance authority) | COVERED | `test_role_tool_descriptions_are_a_safety_surface`, `test_reviewer_output_is_text_not_a_decision` |
| C37 | `devrelay_status` reports the routing state truthfully (configured and unconfigured workspaces) | COVERED | `test_status_reports_role_routing_state`, `test_roles_present_do_not_change_non_role_envelopes` |
| C38 | Read-only role views never touch OpenCode | COVERED | `test_list_roles_is_read_only_and_sanitized`, `test_get_role_returns_the_exact_route[implementer\|reviewer]` |
| C39 | Every role send envelope carries routing + accepted send evidence, and never claims which model "should" be used | COVERED | `test_every_role_send_envelope_is_route_evidenced`, `test_a_planner_can_answer_every_routing_question` |
| C40 | Routing metadata never echoes the prompt | COVERED | `test_role_envelope_never_echoes_the_prompt_in_routing_metadata` |

## F. Failure semantics

| # | Criterion | Status | Evidence (`tests/test_v03c_role_tools.py`) |
| --- | --- | --- | --- |
| C41 | Unknown/omitted/blank/case-variant role: local failure, **zero** OpenCode requests | COVERED | `test_unknown_or_omitted_role_fails_locally[planner\|case-variant\|blank\|null\|omitted]` |
| C42 | Unconfigured role: local failure, zero OpenCode requests, truthful `supported_roles` | COVERED | `test_unconfigured_role_fails_locally` |
| C43 | Malformed configured route: local failure, never classified as a provider failure | COVERED | `test_invalid_configured_route_fails_locally_and_is_not_a_provider_error`, `test_routing_failures_are_never_reported_as_provider_failures` |
| C44 | Workspace/session mismatch keeps the accepted ownership failure and submits nothing (route evidence preserved) | COVERED | `test_foreign_session_still_fails_closed_with_no_submission` |
| C45 | Argument validation still precedes the network | COVERED | `test_argument_validation_still_precedes_the_network` |
| C46 | Accepted send semantics preserved through the role path: success, ConnectError, ReadTimeout, WriteTimeout, 2xx wrong media type, HTTP rejection, accepted/pending - with the same `submission_status`/`submission_uncertain`/`reply_pending`/`retry_safe` values and at most one POST | COVERED | `test_role_path_preserves_every_accepted_send_semantic[7 cases]` |
| C47 | Exactly one submission POST per role send; no retry | COVERED | `test_one_post_per_role_send_and_no_retry[implementer\|reviewer]` |

## G. Concurrency, cancellation and the accepted boundary

| # | Criterion | Status | Evidence (`tests/test_v03c_role_concurrency.py`) |
| --- | --- | --- | --- |
| C48 | The three role tools use the **same** execution lock: no overlap with reads, with the raw send, or between the two roles (`max_concurrent_execution == 1`) | COVERED | `test_role_tools_never_overlap_the_accepted_tools[role_send+read\|role_send+raw_send\|implementer+reviewer]` |
| C49 | The read-only role views also wait for that one boundary instead of running beside it | COVERED | `test_role_read_tools_wait_for_the_same_execution_boundary[list_roles\|get_role]` |
| C50 | Mixed parallel load (reads + both role sends) keeps the accepted ledger intact: unique/contiguous ids, nothing `ISSUED`, ledger overlap 1, exactly one POST per role send, each role on its own model | COVERED | `test_parallel_reads_and_both_role_sends_keep_the_ledger_intact` |
| C51 | v0.3-C adds no second lock, no role lock and no scheduler (one `RLock`, taken in exactly two places) | COVERED | `test_role_tools_share_the_one_execution_lock` |
| C52 | Cancellation stays honest: the boundary is held until the already-running body exits, exactly one submission, no retry, no automatic role switch, no automatic interrupt, durable evidence settled | COVERED | `test_cancelled_role_send_keeps_evidence_and_never_switches_role`, `test_role_send_envelope_never_claims_retry_safety_after_cancellation` |

## H. Integration, regression and boundaries

| # | Criterion | Status | Evidence (`tests/test_v03c_stdio_roles.py`) |
| --- | --- | --- | --- |
| C53 | Real stdio MCP boundary: `tools/list` = exactly 12 with the three role tools | COVERED | `test_stdio_advertises_twelve_tools_and_the_role_tools` |
| C54 | Over the wire: `list_roles`/`get_role` report the configured routes and both roles send their own model/agent; exactly one POST per role send | COVERED | `test_stdio_role_views_report_the_configured_routes`, `test_stdio_role_sends_reach_the_configured_wire_models` |
| C55 | Over the wire: a caller-supplied `model`/`agent` never changes the route | COVERED | `test_stdio_role_send_never_leaks_a_model_override` |
| C56 | Over the wire: routing failures produce envelopes with zero model POSTs | COVERED | `test_stdio_unknown_and_unconfigured_roles_never_reach_opencode` |
| C57 | A workspace without `roles:` still serves all 12 tools; only the role path fails locally | COVERED | `test_stdio_workspace_without_roles_still_serves_every_raw_tool` |
| C58 | Reviewer output (`APPROVE`) stays provider text: no decision field, no role switch | COVERED | `test_stdio_reviewer_reply_is_text_not_a_decision` |
| C59 | Raw `opencode_send_prompt` regression: caller model/agent still reach the wire, envelope carries no role key, works with and without role configuration, and coexists with the role path | COVERED | `tests/test_v03c_role_tools.py::test_raw_send_prompt_keeps_the_caller_model_when_roles_are_configured`, `…::test_raw_path_is_not_redirected_through_role_routing`, `…::test_raw_path_works_without_any_role_configuration`, `…::test_both_paths_can_be_used_in_one_session` |
| C60 | Secret boundary: no token/credential in any role envelope, diagnostic or durable ledger record | COVERED | `tests/test_v03c_role_tools.py::test_no_credential_leaks_through_any_role_envelope`, `…::test_durable_ledger_never_stores_the_role_prompt_or_a_credential` |
| C61 | Accepted v0.3-A suites unchanged and green (200 tests; runtime sources byte-identical) | COVERED | `tests/test_v03a_*.py` (only one enumerated wiring-key list extended, as when `opencode` was added) |
| C62 | Accepted v0.3-B suites green after the surface change (111 tests; only the tool-inventory/version expectations updated) | COVERED | `tests/test_v03b_mcp_tools.py`, `tests/test_v03b_mcp_stdio.py`, `tests/test_v03b_mcp_concurrency.py` |
| C63 | No orchestration surface exists: the three new tools are two read-only views plus one bounded send; no tool sequences roles, approves or rejects | COVERED | `test_no_role_tool_can_accept_reject_or_sequence_anything`, `test_reviewer_output_is_text_not_a_decision` |

## I.1 Real role-routing evidence — IMPLEMENTER run

Bounded real run at candidate `eabb667…` (chain: real official MCP client over
stdio → real DevRelay MCP server → role resolver → accepted v0.3-A bridge → real
OpenCode `1.18.11` → real provider).

| Criterion | Result |
| --- | --- |
| Configured / resolved / actual route | `opencode-go/deepseek-v4.1-flash` (three-way agreement: `devrelay_get_role`, response `resolved_model_identity`, OpenCode DEBUG provider log) |
| `devrelay_send_role_prompt` invocations | **1** (arguments only `role`, `session_id`, `prompt`; no model/agent override) |
| `/session/{id}/message` POSTs | **1** |
| Retry / fallback / alternate model | 0 / 0 / 0 |
| Automatic reviewer invocation | **0** (the reviewer turn was never triggered by DevRelay) |
| HTTP / envelope | `submission_status=200`, `ok=true`, `isError=false`, `submission_uncertain=false`, `reply_pending=false`, `retry_safe=false` |
| Correlated assistant response | contained `DEVRELAY_V03C_IMPLEMENTER_OK` (the normalized assistant text also carried the model's reasoning text, see P3-5) |
| Ledger / workspace / cleanup | all records settled, one model POST, workspace unchanged, cleanup complete |
| Harness result of that run | **`FAIL — V0.3-C REAL ROLE-ROUTING SMOKE`** (exact-whole-message harness condition only) |

## I.2 Real role-routing evidence — REVIEWER completion run

Bounded real run at candidate `eabb667…` (fresh disposable workspace, dedicated
OpenCode `1.18.11`, MCP SDK `2.2.0`, real stdio chain, exactly 12 tools).

| Criterion | Result |
| --- | --- |
| Configured / resolved / actual route | `opencode-go/glm-5.3-flash` (three-way agreement: `devrelay_get_role` before and after, response `resolved_model_identity` = `{providerID: opencode-go, modelID: glm-5.3-flash}`, OpenCode DEBUG provider log `message=stream providerID=opencode-go modelID=glm-5.3-flash session.id=…`) |
| `devrelay_send_role_prompt` invocations | **1**; implementer invocations in that run: **0** |
| `/session/{id}/message` POSTs | **1** (ledger `OC-0008`, model `opencode-go/glm-5.3-flash`) |
| Retry / fallback / alternate model / automatic follow-up | 0 / 0 / 0 / 0 |
| HTTP / envelope | `submission_status=200`, `ok=true`, `isError=false`, `submission_uncertain=false`, `reply_pending=false`, `retry_safe=false` |
| Assistant answer text part | exactly `DEVRELAY_V03C_REVIEWER_OK` (visible text also contained the token inside the reasoning part) |
| Final history | user → assistant; `cursor_unknown=false`, `replayed=false`, `window_truncated=false` |
| Ledger / workspace / cleanup | 13 records all `COMPLETED`, zero `ISSUED`, one model POST, workspace unchanged, cleanup complete |
| Harness result of that run | **`PASS — V0.3-C REVIEWER ROUTING COMPLETION SMOKE`** |

## I.3 Combined acceptance evidence

```text
implementer -> opencode-go/deepseek-v4.1-flash   (real inference, 1 POST)
reviewer    -> opencode-go/glm-5.3-flash          (real inference, 1 POST)
P0 = 0 · P1 = 0 · smoke-blocking P2 = 0
PASS — COMPLETE REAL V0.3-C ROLE-ROUTING EVIDENCE
```

Both routes: come from workspace configuration, cannot be altered through
call-time `model`/`agent` fields on the role tool, produce exactly one model
submission per explicit role call, never retry, never fall back, never switch
roles, never call the other role automatically, and preserve the accepted v0.3-A
ownership and accounting semantics.

## J. Deferred (non-blocking, recorded)

| # | Item | Why deferred |
| --- | --- | --- |
| D1 | Real role-routed model smoke against a real OpenCode server | **done before acceptance**: implementer run (`opencode-go/deepseek-v4.1-flash`) plus reviewer completion run (`opencode-go/glm-5.3-flash`), one bounded turn per role — see sections I.1-I.3; kept here so the original deferral stays visible |
| D2 | Generic/arbitrary role taxonomy and role registry | v0.3-C deliberately ships exactly `implementer`/`reviewer` to avoid a premature taxonomy; migration stays manageable |
| D3 | Session-per-role provisioning / session policy | out of scope: v0.3-C never creates, binds or infers sessions |
| D4 | Orchestration: implementer -> reviewer sequencing and repair loops | v0.3-D territory; v0.3-C routes only |
