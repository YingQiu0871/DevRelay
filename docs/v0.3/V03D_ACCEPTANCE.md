# DevRelay v0.3-D acceptance matrix — bounded orchestration

Status: **candidate implementation complete — ready for independent review**
(unreleased; package version stays `0.1.0`; public release remains `v0.1.0`;
v0.3-E not started).  Branch `v0.3-d-bounded-orchestration`.

All evidence below is **offline**: the real MCP SDK dispatch over the real
orchestration service, the real v0.3-C role router and the accepted v0.3-A bridge
wired to the deterministic OpenCode stub (`httpx.MockTransport`), plus a real
stdio MCP subprocess against a deterministic loopback fake OpenCode server.
**Real orchestration model calls in this round: 0.**

Legend: **COVERED** = automated test asserts it · **PARTIAL** = covered
indirectly · **DEFERRED** = documented, not automated in this stage.

## A. Run model, bounds and durable store
| # | Criterion | Status | Evidence (`tests/test_v03d_models.py`, `tests/test_v03d_store.py`) |
| --- | --- | --- | --- |
| D1 | Hard bounds are exactly as specified (`HARD_MAX_CYCLES = 3`, `1 <= max_cycles <= 3`, default 2, budget `2 x max_cycles`, absolute ceiling 6 turns) | COVERED | `test_bounds_match_the_specification`, `test_start_run_accepts_the_hard_bound_but_not_beyond` |
| D2 | Explicit state enum and exactly four terminal states | COVERED | `test_state_enum_is_explicit_and_complete`, `test_terminal_states_are_exactly_the_four_documented_ones` |
| D3 | The run document is strict, content-free and exposes a Planner-complete summary | COVERED | `test_run_model_is_strict_and_carries_no_content_fields`, `test_summary_exposes_everything_a_planner_needs`, `test_route_snapshot_is_sanitized_identifiers_only` |
| D4 | Run ids are generated and collision-resistant; a caller-supplied id can never be a path | COVERED | `test_generated_ids_are_collision_resistant_and_pattern_valid`, `test_caller_supplied_ids_can_never_be_paths[12 cases]`, `test_contained_path_stays_under_the_runs_directory` |
| D5 | Writes are atomic (unique temp + replace) with no temp residue | COVERED | `test_writes_are_atomic_and_leave_no_temp_files`, `test_round_trip_preserves_the_run_document` |
| D6 | Missing runs are not-found; corrupt/malformed/unknown-field/wrong-id runs are reported and never reset | COVERED | `test_missing_run_is_reported_as_not_found`, `test_corrupt_json_is_reported_and_never_reset`, `test_malformed_document_is_reported_as_corrupt`, `test_unknown_fields_are_rejected_as_corrupt`, `test_document_with_a_different_run_id_is_corrupt` |

## B. Transition policy
| # | Criterion | Status | Evidence (`tests/test_v03d_state_machine.py`) |
| --- | --- | --- | --- |
| D7 | A completed implementer turn opens `READY_REVIEWER`; a completed reviewer turn opens `AWAITING_DECISION` and closes the cycle | COVERED | `test_a_completed_implementer_turn_opens_the_reviewer_phase`, `test_a_completed_reviewer_turn_stops_at_awaiting_decision_and_closes_the_cycle` |
| D8 | Any unsuccessful turn blocks the run (never a retry, never the other role) | COVERED | `test_any_unsuccessful_turn_blocks_the_run[implementer\|reviewer]`, `test_an_unsuccessful_turn_without_a_reason_still_blocks` |
| D9 | Decisions: `complete` → `COMPLETED`, `stop` → `STOPPED`, `request_changes` → next cycle only while budget remains, otherwise `LIMIT_REACHED` | COVERED | `test_complete_and_stop_are_terminal`, `test_request_changes_opens_the_next_cycle_while_budget_remains`, `test_request_changes_at_the_cycle_cap_reaches_the_limit` |
| D10 | Unknown roles/decisions are refused by policy | COVERED | `test_unknown_role_is_rejected_by_policy`, `test_unknown_decisions_are_rejected_by_policy[7 cases]` |
| D11 | Guards: terminal runs, in-flight turns, wrong state, exhausted budget | COVERED | `test_terminal_runs_refuse_further_actions`, `test_in_flight_guard_refuses_to_continue`, `test_state_guard_names_the_expected_state`, `test_cycle_budget_guard_uses_the_model_turn_budget` |

## C. start_run
| # | Criterion | Status | Evidence (`tests/test_v03d_orchestration.py`, `tests/test_v03d_mcp_tools.py`) |
| --- | --- | --- | --- |
| D12 | Creates bounded state (`READY_IMPLEMENTER`, cycle 1, budget, snapshots) with **zero** model POSTs | COVERED | `test_start_run_creates_bounded_state_with_zero_model_posts`, `test_start_run_is_zero_model_and_only_read_only_validation` |
| D13 | Accepts no task prompt and persists none | COVERED | `test_start_run_ignores_a_caller_prompt_because_it_accepts_none` |
| D14 | `max_cycles` outside 1..3 is refused locally with zero POST | COVERED | `test_start_run_rejects_out_of_bound_cycles[0\|4\|-1\|10]`, `test_start_run_accepts_the_hard_bound_but_not_beyond` |
| D15 | Identical sessions are refused; foreign/missing sessions fail before a run exists | COVERED | `test_identical_role_sessions_are_rejected`, `test_foreign_or_missing_sessions_fail_before_a_run_exists`, `test_unknown_session_fails_before_a_run_exists`, `tests/test_v03d_stdio.py::test_stdio_start_run_validates_sessions_and_bounds` |

## D. Model-bearing phases
| # | Criterion | Status | Evidence (`tests/test_v03d_orchestration.py`) |
| --- | --- | --- | --- |
| D16 | One-cycle happy path: exactly 2 model POSTs, `READY_REVIEWER` → `AWAITING_DECISION` → explicit `complete` → `COMPLETED` | COVERED | `test_one_cycle_happy_path_uses_exactly_two_model_posts` |
| D17 | Two-cycle `request_changes` flow: exactly 4 POSTs, `completed_cycles = 2`, final `COMPLETED` | COVERED | `test_two_cycle_request_changes_flow_uses_four_model_posts` |
| D18 | Hard cap: three cycles → 6 POSTs, then `request_changes` → `LIMIT_REACHED` with no seventh call and no fourth implementer turn | COVERED | `test_hard_cap_three_cycles_then_limit_reached_without_a_seventh_call` |
| D19 | `stop` is terminal and spends no model turn | COVERED | `test_stop_is_a_terminal_administrative_transition` |
| D20 | Reviewer prose never drives the state machine (`APPROVE`, `REQUEST_CHANGES`, `LGTM`, `PASS`, `FAIL`) and only an explicit external decision advances the run | COVERED | `test_reviewer_prose_never_drives_the_state_machine[5 replies]`, `test_request_changes_text_does_not_start_the_next_cycle`, `test_orchestration_never_claims_reviewer_approval`, `tests/test_v03d_mcp_tools.py::test_reviewer_approve_never_completes_the_run_by_itself`, `tests/test_v03d_stdio.py::test_stdio_one_cycle_keeps_awaiting_decision_until_the_planner_decides` |
| D21 | Implementer failure matrix (10 kinds) blocks the run, never invokes the reviewer, never retries | COVERED | `test_implementer_failure_blocks_the_run_without_a_reviewer_turn[10 cases]` |
| D22 | Reviewer failure matrix (10 kinds) blocks the run, allows no decision and no next cycle, never retries | COVERED | `test_reviewer_failure_blocks_the_run_without_another_cycle[10 cases]` |
| D23 | Uncertain/pending submissions block with durable evidence and never claim retry safety | COVERED | `test_uncertain_submission_blocks_and_records_durable_evidence` |
| D24 | Exact model-turn accounting (budget, used, remaining, attempts) and per-turn sanitized evidence (route, call ids, status, flags, assistant ids) | COVERED | `test_model_turn_accounting_is_exact`, `test_turn_evidence_carries_routes_and_call_ids` |
| D25 | Only external decisions appear in the decision history, marked `external_planner` | COVERED | `test_decision_history_records_only_external_decisions` |

## E. Invalid transitions and duplicate protection
| # | Criterion | Status | Evidence (`tests/test_v03d_orchestration.py`, `tests/test_v03d_mcp_tools.py`) |
| --- | --- | --- | --- |
| D26 | Reviewer before implementer, decision before reviewer, implementer/reviewer twice, phases while awaiting a decision, `complete` twice, `request_changes` after `complete`, any phase after `STOPPED`/`BLOCKED` | COVERED | `test_reviewer_before_implementer_is_refused`, `test_decision_before_reviewer_is_refused`, `test_implementer_twice_is_refused_without_a_second_post`, `test_reviewer_twice_is_refused_without_a_second_post`, `test_implementer_and_reviewer_while_awaiting_decision_are_refused`, `test_complete_twice_and_request_changes_after_complete_are_refused`, `test_model_bearing_actions_after_stop_or_block_are_refused` |
| D27 | Unknown run ids and corrupt run documents fail closed with the run untouched | COVERED | `test_unknown_run_id_and_corrupt_run_fail_closed`, `tests/test_v03d_mcp_tools.py::test_unknown_run_id_is_a_bounded_local_error` |
| D28 | Unsupported decisions and malformed run ids are refused with state visible and no POST | COVERED | `test_unsupported_decisions_are_refused[6 values]`, `test_a_non_string_decision_is_rejected_at_the_sdk_boundary`, `tests/test_v03d_mcp_tools.py::test_malformed_run_ids_are_local_errors_and_never_paths[5 values]`, `…::test_a_non_string_run_id_is_rejected_at_the_sdk_boundary` |
| D29 | Route drift and ownership loss fail the run closed with zero POST | COVERED | `test_a_changed_role_route_fails_the_run_closed`, `test_a_session_that_stops_being_owned_blocks_the_run` |

## F. Persistence, restart and containment
| # | Criterion | Status | Evidence (`tests/test_v03d_orchestration.py`, `tests/test_v03d_mcp_tools.py`) |
| --- | --- | --- | --- |
| D30 | `get_run` is local read-only (no OpenCode request, no mutation) | COVERED | `test_get_run_reads_durable_state_without_network_or_mutation`, `tests/test_v03d_mcp_tools.py::test_get_run_is_local_and_read_only`, `tests/test_v03d_stdio.py::test_stdio_get_run_is_local_and_terminal_runs_refuse_phases` |
| D31 | A new service/process reads the same durable state and continues legally | COVERED | `test_a_new_service_reads_the_same_run_after_a_restart` |
| D32 | A persisted in-flight turn is never replayed: the next mutating action fails the run closed | COVERED | `test_a_persisted_in_flight_turn_is_never_replayed` |
| D33 | No prompt, reply, reasoning or credential material is persisted | COVERED | `test_persisted_runs_hold_no_prompts_replies_or_credentials`, `tests/test_v03d_mcp_tools.py::test_durable_state_never_persists_prompt_or_reply_text`, `…::test_no_credential_leaks_through_any_orchestration_envelope` |

## G. MCP surface and concurrency
| # | Criterion | Status | Evidence (`tests/test_v03d_mcp_tools.py`, `tests/test_v03d_concurrency.py`) |
| --- | --- | --- | --- |
| D34 | Exactly 17 tools: the accepted twelve unchanged, the role tools at 9..11, the five orchestration tools appended; no sixth orchestration tool, no resources/prompts | COVERED | `test_inventory_is_sixteen_plus_exactly_five_seventeen`, `test_orchestration_annotations_are_honest`, `tests/test_v03d_stdio.py::test_stdio_advertises_seventeen_tools` |
| D35 | Input schemas expose only the documented arguments (no model/agent/endpoint/workspace/retry/task prompt) | COVERED | `test_input_schemas_accept_only_the_documented_arguments` |
| D36 | Descriptions are a Planner safety surface (no model call for start/get/decide, one explicit phase turn, never interprets reviewer text, stops at `AWAITING_DECISION`, `external_planner` source) | COVERED | `test_descriptions_are_a_planner_safety_surface` |
| D37 | All orchestration tools share the accepted execution boundary (`max_concurrent_execution == 1`) | COVERED | `test_orchestration_tools_share_the_one_execution_boundary[4 pairs]`, `test_decide_run_waits_for_the_boundary_too` |
| D38 | Two concurrent same-phase attempts submit exactly once; the loser fails locally with the transitioned state visible | COVERED | `test_two_concurrent_implementer_attempts_submit_exactly_once`, `test_two_concurrent_reviewer_attempts_submit_exactly_once` |
| D39 | `devrelay_status` exposes the sanitized orchestration capability block and never inlines runs | COVERED | `test_status_exposes_the_orchestration_capability_block`, `test_status_never_lists_raw_runs` |

## H. Regression and back-check
| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| D40 | Accepted v0.3-C suite unchanged and green | COVERED | `tests/test_v03c_*.py` (140 tests); disclosed expectation updates: tool positions 9..11 of 17 and inventory size |
| D41 | Accepted v0.3-B suite unchanged and green | COVERED | `tests/test_v03b_*.py` (111 tests); disclosed expectation updates: tool inventory 12 → 17 and server version `0.3.0-c` → `0.3.0-d` |
| D42 | Accepted v0.3-A suite unchanged and green | COVERED | `tests/test_v03a_*.py` (200 tests), no changes |
| D43 | Full offline suite green with isolated `TEMP`/`TMP`/`TMPDIR` | COVERED | full-suite run recorded in the implementation report (963 tests expected: 809 + 154) |
| D44 | Mutation back-check: reviewer auto-completes; cycle cap removed; duplicate implementer allowed; reviewer text auto-sequences; route drift ignored | COVERED | disposable `git archive` copies; 30 / 2 / 5 / 2 / 1 tests fail respectively (control: 154 pass) - recorded in the implementation report |
| D45 | Real model/OpenCode/network calls during implementation | COVERED | **0** (offline stub or loopback fake only) |

## I. Deferred (non-blocking, recorded)
| # | Item | Why deferred |
| --- | --- | --- |
| E1 | Bounded real orchestration smoke (two cycles maximum, 4 model turns) | requires independent review first (`P0 = 0`, `P1 = 0`, no smoke-blocking P2) and a separate authorization |
| E2 | v0.3-E recovery: reconciliation after a crash during submission, uncertain-call recovery, orphan-process recovery, automatic resume | explicitly out of scope for v0.3-D; a persisted in-flight turn currently fails the run closed |
| E3 | Multi-process orchestration locking | v0.3-D relies on the accepted single-process MCP serialization and a single-writer store |
| E4 | Run listing / run history API, retention policy for run documents | not needed for the bounded workflow yet |
