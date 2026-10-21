# DevRelay v0.3-D acceptance matrix — bounded orchestration

> Later status (2026-10-21): released as part of DevRelay 0.3.0.

Status: **ACCEPTED / CLOSED / UNRELEASED** (subject to one final independent
closeout review of this bookkeeping change) - real bounded orchestration smoke
**`PASS — V0.3-D REAL BOUNDED ORCHESTRATION SMOKE`** at candidate
`8b70610a5cdda600ef57cf8378c4f69cd33d5be4` (see §L).  Package version stays
`0.1.0`; the supported public release remains `v0.1.0`; no `v0.3-D` tag exists and
**v0.3-E has not started**.  Branch `v0.3-d-bounded-orchestration`; implementation
commit `78d4e5d…` (never amended), then the first and second remediation commits,
then this acceptance closeout.

Development trail (preserved, not rewritten): initial candidate `78d4e5d` ->
independent `REQUEST_CHANGES` (P1: persisted state trusted) -> first remediation
`98dd422` -> independent `REQUEST_CHANGES` (three reachability P1s) -> second
remediation `8b70610` -> independent final reachability re-review (**P0 = 0,
P1 = 0, P2 = 0**) and its decision *APPROVE V0.3-D FOR ONE BOUNDED REAL
ORCHESTRATION SMOKE WITH RECORDED P3* -> real smoke **PASS** -> acceptance
bookkeeping commit `be4dce7` -> closeout review `REQUEST_CHANGES` (P0 = 0,
P1 = 0, **P2 = 1**: a documentation/status contradiction, no runtime finding) ->
this docs-only follow-up.  The accepted **runtime** candidate remains
`8b70610a5cdda600ef57cf8378c4f69cd33d5be4`; `be4dce7` and this follow-up are
documentation-only commits.

Sections A-I (D-rows), J and K are **offline** evidence: the real MCP SDK
dispatch over the real orchestration service, the real v0.3-C role router and the
accepted v0.3-A bridge wired to the deterministic OpenCode stub
(`httpx.MockTransport`), plus a real stdio MCP subprocess against a deterministic
loopback fake OpenCode server - **no real model call**.  The **real-provider**
evidence is the single authorized bounded smoke recorded in **§L**; no second
smoke was performed.
**Real orchestration model calls in this offline validation/re-review round: 0**
(that statement is scoped to the offline sections of this matrix; the single real
provider smoke is recorded in §L).

Legend: **COVERED** = automated test asserts it · **PARTIAL** = covered
indirectly · **DEFERRED** = documented, not automated in this stage.

## A. Run model, bounds and durable store
| # | Criterion | Status | Evidence (`tests/test_v03d_models.py`, `tests/test_v03d_store.py`) |
| --- | --- | --- | --- |
| D1 | Hard bounds are exactly as specified (`HARD_MAX_CYCLES = 3`, `1 <= max_cycles <= 3`, default 2, budget `2 x max_cycles`, absolute ceiling 6 turns) | COVERED | `test_bounds_match_the_specification`, `test_start_run_accepts_the_hard_bound_but_not_beyond` |
| D2 | Explicit state enum and exactly four terminal states | COVERED | `test_state_enum_is_explicit_and_complete`, `test_terminal_states_are_exactly_the_four_documented_ones` |
| D3 | The run document is strict, content-free and exposes a Planner-complete summary | COVERED | `test_run_model_is_strict_and_carries_no_content_fields`, `test_summary_exposes_everything_a_planner_needs`, `test_route_snapshot_is_sanitized_identifiers_only` |
| D4 | Run ids are generated and collision-resistant; a caller-supplied id can never be a path | COVERED | `test_generated_ids_are_collision_resistant_and_pattern_valid`, `test_caller_supplied_ids_can_never_be_paths[12 cases]`, `test_contained_path_stays_under_the_runs_directory` |
| D5 | Writes are atomic (unique temp + replace) with no temp residue; **no** power-loss durability is claimed (no `fsync`) | COVERED | `test_writes_are_atomic_and_leave_no_temp_files`, `test_round_trip_preserves_the_run_document`; wording: `V03D_SPEC.md` section 6, `store.py` module docstring |
| D6 | Missing runs are not-found; corrupt/malformed/unknown-field/wrong-id runs are reported and never reset; **persisted state is treated as untrusted input** (semantic invariants on load *and* save, provenance, workspace binding) | COVERED | `test_missing_run_is_reported_as_not_found`, `test_corrupt_json_is_reported_and_never_reset`, `test_malformed_document_is_reported_as_corrupt`, `test_unknown_fields_are_rejected_as_corrupt`, `test_document_with_a_different_run_id_is_corrupt`, plus the whole R-section below |

> **Later status (2026-10-20):** D5's "no fsync" describes the v0.3-D store. The
> v0.3-E orchestration store fsyncs the temp document before replacement and the
> parent directory on POSIX; Windows directory fsync is unavailable, so rename
> durability across power loss is not claimed. Atomic replacement and inert-temp
> behavior are unchanged.

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
| D14 | `max_cycles` outside 1..3 is refused locally with zero POST; a boolean is refused by the tool body and the SDK's lax normalization is measured and recorded (R20) | COVERED | `test_start_run_rejects_out_of_bound_cycles[0\|4\|-1\|10]`, `test_start_run_accepts_the_hard_bound_but_not_beyond`, `test_boolean_max_cycles_is_rejected_by_the_tool_body`, `test_mcp_sdk_normalizes_max_cycles_before_the_tool_body`, `test_the_service_also_refuses_a_boolean_max_cycles` |
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
| D24 | Exact model-turn accounting (budget, used, remaining, attempts) and per-turn sanitized evidence (route, call ids, status, flags, assistant ids); `model_turns_used` counts **consumed slots** and is never refunded (R13) | COVERED | `test_model_turn_accounting_is_exact`, `test_turn_evidence_carries_routes_and_call_ids`, `tests/test_v03d_intent_order.py` accounting matrix |
| D25 | Only external decisions appear in the decision history, marked `external_planner` | COVERED | `test_decision_history_records_only_external_decisions` |

## E. Invalid transitions and duplicate protection
| # | Criterion | Status | Evidence (`tests/test_v03d_orchestration.py`, `tests/test_v03d_mcp_tools.py`) |
| --- | --- | --- | --- |
| D26 | Reviewer before implementer, decision before reviewer, implementer/reviewer twice, phases while awaiting a decision, `complete` twice, `request_changes` after `complete`, any phase after `STOPPED`/`BLOCKED` | COVERED | `test_reviewer_before_implementer_is_refused`, `test_decision_before_reviewer_is_refused`, `test_implementer_twice_is_refused_without_a_second_post`, `test_reviewer_twice_is_refused_without_a_second_post`, `test_implementer_and_reviewer_while_awaiting_decision_are_refused`, `test_complete_twice_and_request_changes_after_complete_are_refused`, `test_model_bearing_actions_after_stop_or_block_are_refused` |
| D27 | Unknown run ids and corrupt run documents fail closed with the run untouched | COVERED | `test_unknown_run_id_and_corrupt_run_fail_closed`, `tests/test_v03d_mcp_tools.py::test_unknown_run_id_is_a_bounded_local_error` |
| D28 | Unsupported decisions and malformed run ids are refused with state visible and no POST | COVERED | `test_unsupported_decisions_are_refused[6 values]`, `test_a_non_string_decision_is_rejected_at_the_sdk_boundary`, `tests/test_v03d_mcp_tools.py::test_malformed_run_ids_are_local_errors_and_never_paths[5 values]`, `…::test_a_non_string_run_id_is_rejected_at_the_sdk_boundary` |
| D29 | Route drift, an **unresolvable** route and ownership loss fail the run closed with zero POST and an immutable snapshot (R9) | COVERED | `test_a_changed_role_route_fails_the_run_closed`, `test_a_session_that_stops_being_owned_blocks_the_run`, `tests/test_v03d_invariants.py` route-invalidation tests |

## F. Persistence, restart and containment
| # | Criterion | Status | Evidence (`tests/test_v03d_orchestration.py`, `tests/test_v03d_mcp_tools.py`) |
| --- | --- | --- | --- |
| D30 | `get_run` is local read-only (no OpenCode request, no mutation) | COVERED | `test_get_run_reads_durable_state_without_network_or_mutation`, `tests/test_v03d_mcp_tools.py::test_get_run_is_local_and_read_only`, `tests/test_v03d_stdio.py::test_stdio_get_run_is_local_and_terminal_runs_refuse_phases` |
| D31 | A new service/process reads the same durable state and continues legally | COVERED | `test_a_new_service_reads_the_same_run_after_a_restart` |
| D32 | The durable intent is written **before** submission; a persisted in-flight turn is never replayed, is materialized into the role history with its sanitized audit fields, and fails the run closed (R10, R11, R12) | COVERED | `test_a_persisted_in_flight_turn_is_never_replayed`, `tests/test_v03d_intent_order.py`, `tests/test_v03d_invariants.py::test_the_interrupted_corpus_entry_keeps_its_audit_trail` |
| D33 | No prompt, reply, reasoning or credential material is persisted | COVERED | `test_persisted_runs_hold_no_prompts_replies_or_credentials`, `tests/test_v03d_mcp_tools.py::test_durable_state_never_persists_prompt_or_reply_text`, `…::test_no_credential_leaks_through_any_orchestration_envelope` |

## G. MCP surface and concurrency
| # | Criterion | Status | Evidence (`tests/test_v03d_mcp_tools.py`, `tests/test_v03d_concurrency.py`) |
| --- | --- | --- | --- |
| D34 | Exactly 17 tools: the accepted twelve unchanged, the role tools at 9..11, the five orchestration tools appended; no sixth orchestration tool, no resources/prompts | COVERED | `test_inventory_is_sixteen_plus_exactly_five_seventeen`, `test_orchestration_annotations_are_honest`, `tests/test_v03d_stdio.py::test_stdio_advertises_seventeen_tools` |
| D35 | Input schemas expose only the documented arguments (no model/agent/endpoint/workspace/retry/task prompt) | COVERED | `test_input_schemas_accept_only_the_documented_arguments` |
| D36 | Descriptions are a Planner safety surface (no model call for start/get/decide, one explicit phase turn, never interprets reviewer text, stops at `AWAITING_DECISION`, `external_planner` source) | COVERED | `test_descriptions_are_a_planner_safety_surface` |
| D37 | All orchestration tools share the accepted execution boundary (`max_concurrent_execution == 1`), whose honest scope is **per tool surface** (R19) | COVERED | `test_orchestration_tools_share_the_one_execution_boundary[4 pairs]`, `test_decide_run_waits_for_the_boundary_too`, `tests/test_v03b_mcp_concurrency.py::test_status_reports_the_global_serialization_boundary` |
| D38 | Two concurrent same-phase attempts submit exactly once; the loser fails locally with the transitioned state visible | COVERED | `test_two_concurrent_implementer_attempts_submit_exactly_once`, `test_two_concurrent_reviewer_attempts_submit_exactly_once` |
| D39 | `devrelay_status` exposes the sanitized orchestration capability block and never inlines runs | COVERED | `test_status_exposes_the_orchestration_capability_block`, `test_status_never_lists_raw_runs` |

## H. Regression and back-check
| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| D40 | Accepted v0.3-C suite unchanged and green | COVERED | `tests/test_v03c_*.py` (140 tests); disclosed expectation updates: tool positions 9..11 of 17 and inventory size |
| D41 | Accepted v0.3-B suite unchanged and green | COVERED | `tests/test_v03b_*.py` (111 tests); disclosed expectation updates: tool inventory 12 → 17 and server version `0.3.0-c` → `0.3.0-d` |
| D42 | Accepted v0.3-A suite unchanged and green | COVERED | `tests/test_v03a_*.py` (200 tests), no changes |
| D43 | Full offline suite green with isolated `TEMP`/`TMP`/`TMPDIR` | COVERED | full-suite runs recorded in the remediation reports (first remediation **1064** = 963 + 101, second remediation **1166** = 1064 + 102); v0.3-D 154 → **255** → **357**, v0.3-C 140, v0.3-B 111, v0.3-A 200, complete result tuple **0 failed / 0 errors / 0 skipped / 0 xfail / 0 xpass** |
| D44 | Mutation back-check: reviewer auto-completes; cycle cap removed; duplicate phase allowed; reviewer text auto-sequences; route drift ignored; **in-flight intent not saved before the call** | COVERED | disposable `git archive HEAD` copies, each running the whole v0.3-D suite (control: **255 pass**); **68 / 4 / 6 / 67 / 2 / 4** tests fail respectively.  Mutation F is detected by exactly the four new intent-order tests (`test_the_durable_in_flight_intent_precedes_the_submission`, `test_both_roles_commit_their_intent_before_their_submission`, `test_a_crash_at_submission_leaves_a_loadable_in_flight_intent`, `test_a_crash_during_the_reviewer_turn_blocks_without_closing_a_cycle`); it was undetected before this remediation |
| D45 | Real model/OpenCode/network calls during implementation **and remediation** | COVERED | **0** (offline stub or loopback fake only) |

## I. Deferred (non-blocking, recorded)
| # | Item | Why deferred |
| --- | --- | --- |
| E1 | Bounded real orchestration smoke (two cycles maximum, 4 model turns) | **DONE - `PASS`** at candidate `8b70610…` (one authorized run, 4 real model turns / 4 POSTs, 0 retries/fallbacks); full evidence in **§L** |
| E2 | v0.3-E recovery: reconciliation after a crash during submission, uncertain-call recovery, orphan-process recovery, automatic resume | explicitly out of scope for v0.3-D; a persisted in-flight turn currently fails the run closed |
| E3 | Multi-process orchestration locking | explicitly **unsupported**: the execution lock is per tool surface, the shipped stdio server builds exactly one surface, and the store is single-writer; several surfaces/processes against one workspace are out of scope (R19) |
| E4 | Run listing / run history API, retention policy for run documents | not needed for the bounded workflow yet |

## J. Remediation after the independent gate (v0.3-D)

The independent gate returned `REQUEST_CHANGES — V0.3-D BOUNDED ORCHESTRATION`
(P0 = 0, one blocking P1: persisted state was trusted, plus P2/P3 findings).  This
section maps every required remedy to its evidence.  Nothing here accepts v0.3-D:
the stage was then still **candidate, not accepted** and needed an independent
re-review (historical: v0.3-D was accepted later - see §L).

| # | Required remedy | Status | Evidence |
| --- | --- | --- | --- |
| R1 | Persisted orchestration state is untrusted input, enforced at the **model/store load boundary** (not by adding checks to `start_run`) | DONE | `src/devrelay/orchestration/invariants.py` (`validate_run_semantics`, called by the `OrchestrationRun` model validator, by `OrchestrationStore.load` through `model_validate`, and by `OrchestrationStore.save` before writing); `tests/test_v03d_invariants.py` |
| R2 | Gate repro **A**: `max_cycles = 99` / `model_turn_budget = 198` must not execute more than the six-turn ceiling | DONE | `test_repro_A_inflated_persisted_ceiling_cannot_execute_extra_turns` (7 attempts, 0 POSTs, 0 turn records, file byte-identical) |
| R3 | Gate repro **B**: identical implementer/reviewer session ids in a persisted run | DONE | `test_repro_B_identical_sessions_are_never_accepted`, `T11_identical_role_sessions`, `T12_blank_role_session` |
| R4 | Gate repro **C**: `max_cycles = 1000` must not open ≥ 5 cycles / 10 POSTs | DONE | `test_repro_C_max_cycles_1000_cannot_open_five_cycles` (5 decisions refused, 0 POSTs, no cycle opened) |
| R5 | Gate repro **D**: `AWAITING_DECISION` + `completed_cycles = 0` + empty reviewer history must not open a cycle | DONE | `test_repro_D_awaiting_decision_without_a_cycle_cannot_open_one`, `T16_awaiting_decision_without_any_cycle` |
| R6 | 20-case corruption/tamper matrix | DONE | `test_the_20_case_tamper_matrix_is_refused_at_the_load_boundary` (T01–T20) **plus** `test_additional_tampered_documents_are_refused_too` (X01–X22) - 42 parametrized tamper cases - plus `test_store_level_corruption_is_refused_as_well` (missing provenance, foreign workspace, mismatched run id) and `test_truncated_documents_are_refused_and_kept` |
| R7 | Corrupt state is refused everywhere, never repaired, never able to reach a model call | DONE | every matrix case asserts `store.load` raises `orchestration_state_corrupt` with a precise message, `devrelay_get_run`/`devrelay_run_implementer`/`devrelay_decide_run` fail with the same code, the POST count does not move and the file is **byte-identical** afterwards |
| R8 | Save-time validation, transition provenance, workspace binding | DONE | `OrchestrationStore.save` validates before writing; `_require_provenance`; `_require_bound_workspace` (a run copied in from another workspace is refused, never adopted) |
| R9 | An unresolvable role route fails closed like a changed route | DONE | `test_a_route_that_stops_resolving_blocks_the_run_and_keeps_the_snapshot` (durable `BLOCKED`/`route_changed`, immutable snapshot, 0 POST), `test_a_blocked_route_run_stays_terminal`, `test_start_with_unconfigured_roles_creates_nothing`, `test_start_with_an_invalid_role_route_creates_nothing` |
| R10 | An interrupted turn is materialized into the role history with its sanitized fields before the run fails closed | DONE | `test_the_interrupted_corpus_entry_keeps_its_audit_trail`, `test_a_crash_at_submission_leaves_a_loadable_in_flight_intent`, `test_a_crash_during_the_reviewer_turn_blocks_without_closing_a_cycle` (cycle not closed, no decision, no replay, audit preserved) |
| R11 | Durable in-flight intent exists **before** the role call reaches submission (gate/callback, no sleeps) | DONE | `test_the_durable_in_flight_intent_precedes_the_submission`, `test_both_roles_commit_their_intent_before_their_submission` - a transport-level callback snapshots the on-disk document at the exact moment the prompt POST is sent (`posts_recorded_so_far == 0`) |
| R12 | Mutation **F** (bypass the pre-call intent save) must fail the new regression | DONE | 4 tests fail under Mutation F (the two ordering tests and the two crash tests); it was undetected before (D44) |
| R13 | Model-turn accounting matrix (`model_turns_used` = consumed slots, never refunded, always matched by a turn record) | DONE | `test_a_failed_turn_consumes_exactly_one_slot_and_never_refunds_it[10 failure kinds]`, `test_a_successful_turn_consumes_exactly_one_slot_and_records_one_turn`, `test_the_budget_is_never_exceeded_over_a_full_run` (max_cycles = 3 → exactly 6 slots/POSTs, then refused) |
| R14 | Honest-state corpus accepted and stable | DONE | `test_the_honest_corpus_is_accepted_and_stable[11 states]` - every state produced by the real service loads, passes the invariant pass, reports an honest summary and survives a re-save (fixed point) |
| R15 | Reviewer prose can never become a decision | DONE | `test_reviewer_prose_never_advances_the_run[APPROVE, Approved: true, approved: true, score: 10/10, JSON decision object, LGTM, REQUEST_CHANGES text, reviewer_outcome=COMPLETED]` - all end at `AWAITING_DECISION`, empty decision history, exactly two POSTs |
| R16 | `legal_next_actions` is empty while a turn is in flight | DONE | `test_legal_next_actions_is_empty_while_a_turn_is_in_flight`, corpus row `10_ready_implementer_with_in_flight_intent`, `test_a_persisted_in_flight_turn_is_never_replayed` |
| R17 | Run ids are matched strictly (no trailing newline/CR/space, no prefix/suffix) | DONE | `store.valid_run_id` uses `fullmatch`; `test_run_ids_are_matched_strictly_end_to_end[8 vectors]` next to the existing 12-case local-error matrix |
| R18 | Constrained turn-outcome vocabulary | DONE | `TurnOutcomeState` (`in_flight`/`completed`/`blocked`), `TurnRecord` validator, `test_turn_outcome_vocabulary_is_constrained`, tamper case `X01_unknown_turn_outcome` |
| R19 | No power-loss durability overclaim; lock scope stated as per-surface | DONE | spec sections 6 and 7 and `store.py`/`tools.py` docstrings; `devrelay_status` now reports `lock_scope`, `surfaces`, `multiple_surfaces_or_processes`; `tests/test_v03b_mcp_concurrency.py::test_status_reports_the_global_serialization_boundary` still passes |
| R20 | Boolean `max_cycles` probe | DONE (recorded, not fixed at the adapter) | `test_boolean_max_cycles_is_rejected_by_the_tool_body` (the tool body refuses a real `bool`), `test_the_service_also_refuses_a_boolean_max_cycles`, and `test_mcp_sdk_normalizes_max_cycles_before_the_tool_body` which measures the SDK's lax normalization (`true`→1, `"2"`→2, `2.0`→2, `1.5` refused by the SDK, `false`→0 refused by DevRelay).  The normalization happens above the DevRelay boundary and can never raise the 1..3 ceiling, so it is recorded as a P3 boundary finding in the spec §10 and `docs/BACKLOG.md` §5 |

## K. Second remediation — persisted-state reachability (independent gate, P1 = 3)

The second independent gate returned `REQUEST_CHANGES` with three blocking P1s:
a persisted run only had to have *plausible fields*, not a state provable from its
history.  Every honest document used as evidence below is generated by the real
service (`tests/v03d_corpus.py`), including crash boundaries produced by a real
`SystemExit` at submission.  At the time of that round v0.3-D was still **NOT
ACCEPTED** (historical: it was accepted later - see §L).

| # | Required remedy | Status | Evidence |
| --- | --- | --- | --- |
| S1 | **P1-A**: `READY_REVIEWER` (and a live reviewer in-flight intent) requires exactly one **completed** implementer turn in the current cycle | DONE | `tests/test_v03d_reachability.py::test_p1a_a1_valid_ready_reviewer_without_implementer_turns` / `..._a2_state_switched_to_ready_reviewer_without_evidence` / `..._a3_live_reviewer_intent_without_implementer_evidence` (each: `orchestration_state_corrupt`, 0 OpenCode requests, 0 POST, byte-identical file) and `..._controls_are_accepted` |
| S2 | **P1-B**: a historical `blocked` turn forbids every active/completed state, and reviewer completion requires implementer completion in the same cycle | DONE | `..._b1_blocked_historical_turn_inside_an_active_run`, `..._b2_completed_reviewer_without_any_implementer_evidence`, `..._b3_completed_reviewer_whose_implementer_turn_failed`; the five honest `BLOCKED` variants (implementer failure, reviewer failure, route change, interrupted implementer, interrupted reviewer) stay valid (`test_p1b_controls_every_honest_blocked_variant_stays_valid`) |
| S3 | **P1-C**: an exhausted `max_cycles=3` run rolled back toward cycle 1 cannot spend again | DONE | `..._p1c_the_raw_exploit_from_the_gate_is_refused` plus ten stronger variants (`..._p1c_stronger_rollback_variants_are_all_refused[...]`): counters/history/decisions reset in every combination, stale or rewritten transition, missing `request_changes`, fabricated cycle 3, future-cycle turn, terminal-to-active rollback, reviewer evidence without implementer evidence, blocked turn injected into a completed history |
| S4 | `last_transition.next_state == run.state`, with a real edge (action/previous/role/cycle) per state | DONE | `_require_last_transition` in `invariants.py`; rollback variants `everything_reset_but_the_transition_kept`, `transition_rewritten_to_a_non_edge`, `transition_next_state_flipped`, `terminal_run_rolled_back_to_an_active_state` |
| S5 | decision-history / completed-cycle relation | DONE | `len(decision_history) == completed_cycles - (1 if AWAITING_DECISION else 0)`; variants `one_request_changes_decision_removed`, `counters_and_turns_reset_but_decisions_kept`; the open-cycle arithmetic (`opened == current_cycle - 1`) is enforced too and is provably implied by the other rules |
| S6 | future-cycle turn evidence is forbidden; at most one turn per role per cycle; implementer before reviewer | DONE | `future_cycle_turn_injected`, the cycle loop in `invariants.py`, tamper-matrix rows `T13`/`T14` in `tests/test_v03d_invariants.py` |
| S7 | strict persisted types (`schema_version` required, six numeric fields strict) | DONE | `StrictInt` fields plus no default for `schema_version`/`model_turn_budget`; `..._persisted_numeric_fields_are_strict[35 cases]`, `..._missing_persisted_fields_are_rejected`, `..._model_turn_budget_has_no_impossible_default` |
| S8 | turn audit-field consistency (timestamps, digest, prompt length, outcome vs reason, agent/route source) | DONE | `..._turn_audit_fields_are_consistent[9 cases]`; `_require_prompt_evidence`, `_require_finished_audit`, `_require_route_agreement` |
| S9 | honest corpus generated by production transitions, crash boundaries by a real `SystemExit`; `READY_REVIEWER + live reviewer in-flight` included | DONE | `tests/v03d_corpus.py` (19 members) plus `..._every_honest_member_survives_save_restart_load_and_resave[19 cases]`; the hand-written in-flight fixtures in `tests/test_v03d_invariants.py` and `tests/test_v03d_orchestration.py` were replaced by the crash path |
| S10 | differential corpus: honest accepted, one semantic mutation at a time rejected | DONE | `..._every_honest_member_rejects_every_semantic_mutation` (15-mutation battery across the 19 members, **232** applied checks) |
| S11 | save-side invariants (defense in depth) | DONE | `..._save_refuses_an_impossible_in_memory_run[4 cases]` - the prior on-disk document stays byte-identical; mutation **K** (save-time validation removed) fails tests |
| S12 | failure-message truthfulness | DONE | `..._failure_messages_follow_the_structured_evidence` (five failure modes: the message must match the recorded `submission_attempted`/`submission_uncertain`/`reply_pending`/`submission_status` evidence) |
| S13 | tool-description truthfulness about duplicate attempts | DONE | `_RUN_IMPLEMENTER_DESCRIPTION` now states that an ordinary duplicate fails locally while a persisted interrupted phase is first materialized into `BLOCKED`; `_GET_RUN_DESCRIPTION` states that an unreachable document is refused as corrupt |
| S14 | lock-scope wording and exact status keys | DONE | `lock_scope`, `surfaces`, `multiple_surfaces_or_processes` in `devrelay_status`; `..._status_advertises_the_exact_lock_scope`; stale "process-scoped/process-wide" wording removed from the source comment, README and `V03_PLAN` (historical accepted v0.3-B records keep their stage wording) |
| S15 | model-turn wording (slots, not confirmed requests) | DONE | spec §4, README, `V03_PLAN` and the tool descriptions now say "reserved/consumed model-turn budget slots (at most six model POST attempts)" |
| S16 | atomic temp-file wording | DONE | `store.py`/spec §6: atomic replacement of the final document; a hard kill may leave an **inert** `.tmp` file that is never listed or honoured; no `fsync`/power-loss claim; `..._an_inert_temp_file_is_never_listed_or_honoured` |
| S17 | SDK JSON-shaped string limitation | DONE (recorded P3) | `..._json_shaped_prompts_are_refused_at_the_sdk_boundary` plus spec §10/BACKLOG §5: the prompt is refused at the SDK boundary with **no submission**; a `str`-only annotation would break the documented `mcp_invalid_argument` envelope, so it is not changed here |
| S18 | honest bound of non-cryptographic validation | DONE (documented) | `..._p1c_a_perfectly_rewritten_history_is_the_documented_bound` plus spec §6: a fully rewritten, internally consistent history is not detectable without an external integrity anchor; no journal or chain is added |
| S19 | mutations A-J (and K) with failure counts | DONE | recorded in the second remediation report (disposable `git archive HEAD` copies, whole v0.3-D suite, control **357 pass**): A 105, B 19, C 6, D 104, E 6, F 18, G 3, H 2, I 4, J 4, K 4 - mutation G/H/I/J exercise the new reachability rules and K exercises save-side validation |
| S20 | route-unresolvable, crash/in-flight, interrupted-audit, accounting, authority, one-submission and concurrency regressions preserved | DONE | `tests/test_v03d_invariants.py`, `tests/test_v03d_intent_order.py`, `tests/test_v03d_orchestration.py` (255 tests) all still green; the corpus adds the five honest `BLOCKED` variants and both in-flight roles in cycles 1 and 2 |

> **Later status (2026-10-20):** S16's "no fsync" wording is historical for the
> same reason (see the note after the A table); the inert-temp guarantee and the
> "never listed or honoured" rule are unchanged.

## L. Final acceptance — one bounded real orchestration smoke (`PASS`)

**This section is the only real-provider evidence for v0.3-D.**  Everything in
sections A-I (offline validation, D-rows), J (first remediation) and K (second
reachability remediation) is **offline** evidence: real MCP SDK dispatch, real
orchestration service, real v0.3-C router and the accepted v0.3-A bridge wired to
the deterministic OpenCode stub, plus a real stdio MCP subprocess against a
deterministic loopback fake.  No real model call happens in those sections.  The
evidence below is a **single authorized real run** against real OpenCode and real
provider inference; no second smoke was performed.

### L.1 Run identity

| Item | Value |
| --- | --- |
| Candidate under acceptance | `8b70610a5cdda600ef57cf8378c4f69cd33d5be4` (branch `v0.3-d-bounded-orchestration`) |
| Smoke date | **2026-09-17** (local; evidence recorded 18:09) |
| `run_id` | `DR-dfb23a14e4654a5d9b75b296a27b1245`, `max_cycles = 2` |
| Workspace | one-off disposable workspace under the OS temp directory (removed after the run) |
| Disposable sessions | implementer `ses_f4fe32251ffeNafiFnHZ6uv0BY`, reviewer `ses_f4fe3221fffe8bHcYS6ihnK5d6` (both prompt-free `POST /session`, cost 0, owned by that workspace, never created by DevRelay, never reused across roles) |
| Chain | official MCP SDK client → real `devrelay mcp serve --workspace <ws>` (server `0.3.0-d`, 17 tools) → v0.3-D orchestration → v0.3-C role routing → accepted v0.3-A bridge → real OpenCode `1.18.11` (dedicated instance, no auth) → real provider inference |
| Versions | OpenCode **1.18.11**, MCP Python SDK **2.2.0**, DevRelay package `0.1.0`, MCP server version `0.3.0-d` |
| Result | **PASS — V0.3-D REAL BOUNDED ORCHESTRATION SMOKE** |

### L.2 Cycle-by-cycle transitions and the two real authority probes

| Step | Action | Real provider text | Durable state after the step | Model calls added |
| --- | --- | --- | --- | --- |
| 1 | `devrelay_start_run(max_cycles=2)` | — | `READY_IMPLEMENTER`, cycle 1, used 0/4 | 0 |
| 2 | explicit `devrelay_run_implementer` (cycle 1) | implementer reply | `READY_REVIEWER`, used 1/4 | 1 |
| 3 | explicit `devrelay_run_reviewer` (cycle 1) | **`REQUEST_CHANGES`** | **`AWAITING_DECISION`**, `decision_history` **empty**, cycle still 1, `legal_next_actions` only *decide* | 1 |
| 4 | explicit `devrelay_decide_run(request_changes)` | — | `READY_IMPLEMENTER`, cycle **2** | **0** |
| 5 | explicit `devrelay_run_implementer` (cycle 2) | implementer reply | `READY_REVIEWER`, used 3/4 | 1 |
| 6 | explicit `devrelay_run_reviewer` (cycle 2) | **`APPROVE`** | **`AWAITING_DECISION`**, `terminal = false`, no completion, no new cycle, no call to the other role | 1 |
| 7 | explicit `devrelay_decide_run(complete)` | — | **`COMPLETED`**, `terminal = true`, cycle 2, `completed_cycles = 2`, `decision_history` exactly two `external_planner` records | **0** |

Acceptance conclusion: **provider/reviewer prose has zero orchestration decision
authority** - neither `REQUEST_CHANGES` nor `APPROVE` moved the run; only the two
explicit external planner decisions did, and each decision cost 0 model calls.

### L.3 Exact accounting

* real model-bearing turns **4** (`max_cycles = 2`): implementer c1, reviewer c1,
  implementer c2, reviewer c2;
* `POST /session/{id}/message` submissions **exactly 4** (ledger call ids
  `OC-0015`, `OC-0020`, `OC-0025`, `OC-0030`; one POST inside each turn's
  `call_ids`, all HTTP 200, `external_request_count = 1` per turn);
* `model_turns_used = 4`, `model_turn_budget = 4`, `turn_attempts = 4`;
* retries **0**, fallbacks **0**, automatic role calls **0**, interrupts/aborts
  **0**, fifth model turn **0**;
* every turn recorded `submission_uncertain = false` and `reply_pending = false`;
* ledger final state: **30 records, all `COMPLETED`, 0 `ISSUED`** (no orphaned or
  uncertain call identity).

### L.4 Real route agreement

| Turn | Configured route | `devrelay_get_role` | Turn `resolved_model` | Provider runtime log |
| --- | --- | --- | --- | --- |
| implementer c1 | `opencode-go/deepseek-v4.1-flash` | same | same | same (`providerID`/`modelID`/session id) |
| reviewer c1 | `opencode-go/glm-5.3-flash` | same | same | same |
| implementer c2 | `opencode-go/deepseek-v4.1-flash` | same | same | same |
| reviewer c2 | `opencode-go/glm-5.3-flash` | same | same | same |

Four-way agreement held for all four turns (workspace configuration =
`devrelay_get_role` = the durable turn's `resolved_model` = the provider debug log
and the raw assistant metadata, with non-zero cost/tokens).  No model/agent
override was accepted from the caller and no fallback route was used.

### L.5 Durability and privacy checks (45/45 passed)

* four completed durable turn records - two implementer (cycles 1 and 2) and two
  reviewer (cycles 1 and 2) - each with the correct role and cycle;
* no `in_flight_turn` at completion;
* route snapshot unchanged from run creation;
* per-turn `prompt_sha256` + `prompt_chars` present and, when recomputed
  independently from the exact real prompts, matching record by record
  (150 / 150 / 177 / 169 characters);
* raw prompts **not** persisted; provider answer text **not** persisted; provider
  reasoning **not** persisted; no credential material (`Authorization`, `Bearer`,
  token, `api_key`, `secret`) anywhere under `.devrelay` (plaintext prompt and
  sentinel-token scans: zero hits);
* the run document stores only `assistant_message_ids`, never message text;
* `decision_history` contains exactly two `external_planner` decisions;
* final transition ends at `COMPLETED`;
* the workspace `README` sha256 and the tracked tree were unchanged, and the
  repository HEAD/branch/tag/porcelain were unchanged before and after the smoke.

### L.6 Terminal guard (proved twice without spending a fifth turn)

1. **Runtime:** calling the non-model-bearing `devrelay_decide_run` again on the
   terminal run returned `isError` with `error.type =
   orchestration_invalid_transition` and the message that the run *is terminal
   (COMPLETED) ... never reopened*; the state stayed visible and unchanged, the run
   file stayed byte-identical and **0 new POSTs** were issued.
2. **Offline local:** the same persisted document was re-checked with the local
   policy guards and a stub bridge that raises on any touch - the bridge was never
   touched and `require_not_terminal`, both phase state guards and the decision
   state guard all refused.

### L.7 Containment and cleanup

Both disposable sessions were deleted (`DELETE` 200, then `GET` 404; session table
empty), the dedicated OpenCode instance was stopped (its port free again), the
user's own OpenCode processes were untouched, no MCP child process remained, and
the evidence (report plus per-phase JSON/log/raw-message captures) was kept outside
the repository.  The repository working tree was clean before and after.

### L.8 Acceptance decision

Independent final reachability re-review: **P0 = 0, P1 = 0, P2 = 0**, decision
*APPROVE V0.3-D FOR ONE BOUNDED REAL ORCHESTRATION SMOKE WITH RECORDED P3*, with the
carried P3 list kept in `docs/BACKLOG.md` §5.  One
authorized bounded real orchestration smoke: **PASS** as recorded above; no second
smoke was performed.  v0.3-D is therefore **ACCEPTED / CLOSED / UNRELEASED**,
subject to one final independent closeout review of this bookkeeping change.
Package version stays `0.1.0`, the public release remains `v0.1.0`, no `v0.3-D`
tag was created, and **v0.3-E has not started** (recovery remains explicitly out
of scope for v0.3-D).
