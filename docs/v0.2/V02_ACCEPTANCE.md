# DevRelay v0.2-A acceptance criteria

Stage A is accepted only when **all** of the following hold. Evidence column
names the test/artifact that proves it.

## Functional

| # | Criterion | Evidence |
| --- | --- | --- |
| A1 | Automatic happy path: implement -> tests PASS -> reviewer PASS -> `FINAL_GATE_REQUIRED` | `test_v02a_engine_auto_review.py::test_automatic_happy_path` |
| A2 | Blocking review: implement -> reviewer P2 -> `FIX_REQUIRED` -> FIX -> tests -> reviewer PASS -> `FINAL_GATE_REQUIRED` | `test_v02a_e2e_fake.py` |
| A3 | Reviewer `decision=PASS` with a P1 finding is overridden by policy -> `FIX_REQUIRED` | `test_v02a_engine_auto_review.py::test_policy_overrides_pass_decision` |
| A4 | Reviewer `decision=REQUEST_CHANGES` with only P3 passes per default policy | `test_v02a_engine_auto_review.py::test_p3_only_passes_by_policy` |
| A5 | Format retry consumes a second external reviewer call (counted exactly) | `test_v02a_reviewer_calls.py::test_format_retry_counts_two_calls` |
| A6 | Exhausted format retries -> `BLOCKED review_format` with exact call count | `test_v02a_reviewer_calls.py::test_format_retry_exhausted_blocks` |
| A7 | HTTP 500 -> no uncontrolled retry -> `BLOCKED review_provider`, sanitized body | `test_v02a_reviewer_calls.py::test_http_error_blocks_and_sanitizes` |
| A8 | HTTP timeout -> `BLOCKED`, budget accounting correct | `test_v02a_reviewer_calls.py::test_transport_timeout_blocks` |
| A9 | Reviewer budget exhausted before the request -> provider not called -> `BLOCKED provider_budget_exhausted` | `test_v02a_budget.py::test_reviewer_budget_preflight_blocks` |
| A10 | Implementer budget exhausted before a fix -> Codex not called -> `BLOCKED` | `test_v02a_budget.py::test_implementer_budget_preflight_blocks` |
| A11 | Total budget exhausted -> no provider invocation at all | `test_v02a_budget.py::test_total_budget_preflight_blocks` |
| A12 | Crash before/inside a reviewer call -> persisted in-flight marker -> restart does not repeat the call | `test_v02a_engine_auto_review.py::test_reviewer_in_flight_marker_fails_closed` |
| A13 | Manual reviewer consumes zero external reviewer calls | `test_v02a_engine_auto_review.py::test_manual_review_consumes_no_external_calls` |
| A14 | Automatic FIX prompt contains structured findings (id/severity/title/description/files/evidence/recommendation) | `test_v02a_fix_handoff.py::test_fix_prompt_contains_structured_findings` |
| A15 | Second reviewer request contains the previous findings | `test_v02a_fix_handoff.py::test_second_review_sees_previous_findings` |
| A16 | Finding fingerprint is deterministic and excludes the finding id | `test_v02a_fix_handoff.py::test_finding_fingerprint_is_deterministic` |
| A17 | Secret echoed by the reviewer output/error is sanitized before persistence | `test_v02a_engine_auto_review.py::test_secret_in_reviewer_result_is_redacted` |
| A18 | Oversized reviewer response fails closed instead of being truncated/guessed | `test_v02a_reviewer_calls.py::test_oversized_response_fails_closed` |
| A19 | `review_stalled` stops repeated identical blockers (`pipeline.max_same_finding_cycles`) | `test_v02a_engine_auto_review.py::test_repeated_finding_blocks_as_stalled` |
| A20 | Final gate remains manual: automatic review PASS never reaches `DONE` | `test_v02a_engine_auto_review.py::test_final_gate_stays_manual` |
| A21 | Review round started but never finalized (crash after the response) fails closed; `unblock` acknowledges it without losing evidence and the next round gets a unique identity | `test_v02a_engine_auto_review.py::test_unfinished_review_round_fails_closed_and_unblock_acknowledges` |

## Compatibility / state

| # | Criterion | Evidence |
| --- | --- | --- |
| S1 | All v0.1 tests keep passing (no weakened assertions) | full `python -m pytest` |
| S2 | v0.1 task `state.json` fixture loads and `status` works | `test_v02a_state_migration.py::test_v01_state_fixture_loads_and_status_works` |
| S3 | Task policy is the snapshot taken at task start; editing workspace config does not change it | `test_v02a_state_migration.py::test_task_policy_is_snapshotted` |
| S4 | An explicit, audited policy refresh is the only way to change it | `test_v02a_state_migration.py::test_unblock_refresh_policy_is_audited_and_effective` |
| S5 | `devrelay status` shows provider budget and last review evidence | `test_v02a_cli.py::test_status_shows_budget_and_review` |
| S6 | `devrelay usage` is read-only and reports exact counts | `test_v02a_cli.py::test_usage_command` |
| S7 | `devrelay doctor` reports reviewer env presence only (set/missing), sends no request | `test_v02a_cli.py::test_doctor_reviewer_check_is_offline` |
| S8 | Raw `baseline/tracked.patch` stays byte-exact (never redacted) | `test_baseline_service.py` + `test_audit_remediation.py` |

## Process

| # | Criterion | Evidence |
| --- | --- | --- |
| P1 | No real Codex invocation, no real reviewer API call in this stage | all tests use fakes / `httpx.MockTransport` |
| P2 | No version bump, no release, no tag, no push, no PyPI action | branch `v0.2-a-auto-review`, local commit only |
| P3 | Docs updated (README section, CHANGELOG `Unreleased`, v0.2 docs) | `README.md`, `CHANGELOG.md`, `docs/v0.2/*` |

## Additional coverage beyond the matrix

| Test | What it pins down |
| --- | --- |
| `test_v02a_budget.py::test_usage_counts_only_external_calls` | manual/unavailable events count 0; only real invocations count |
| `test_v02a_budget.py::test_budget_check_raises_with_limits_in_message` | refusal message names used/max for all three limits |
| `test_v02a_budget.py::test_budget_describe_lines` | `status`/`usage` budget line format |
| `test_v02a_reviewer_calls.py::test_transport_retry_default_is_zero` | transport retries are opt-in |
| `test_v02a_reviewer_calls.py::test_transport_retry_opt_in_costs_two_calls` | an opt-in transport retry is counted |
| `test_v02a_reviewer_calls.py::test_reviewer_calls_preflight_before_each_request` | budget is checked before *every* request, not once per review |
| `test_v02a_engine_auto_review.py::test_format_retry_evidence_is_preserved` | both the failed and the successful call/attempt are persisted |
| `test_v02a_engine_auto_review.py::test_keyboard_interrupt_during_review_blocks_and_does_not_rerun` | interrupt persists evidence, clears the marker, blocks, re-raises |
| `test_v02a_engine_auto_review.py::test_stagnation_guard_disabled_by_default` | default `max_same_finding_cycles: 0` keeps v0.1 loop semantics |
| `test_v02a_fix_handoff.py::test_fingerprints_and_seen_counts_are_recorded` | fingerprints are recorded even when the guard is disabled |
| `test_v02a_state_migration.py::test_policy_snapshot_file_is_written_at_start` | the snapshot artifact exists and is readable |

## Audit remediation (v0.2-A.1)

Required regression matrix from the independent audit. Every row is proven by a
test in `tests/test_v02a_audit_remediation.py`.

| # | Criterion | Evidence |
| --- | --- | --- |
| A | Persisted valid result + crash before application -> restart replays it with **0** reviewer calls | `test_A_persisted_result_replayed_with_zero_reviewer_calls` |
| A2 | Recovered blocking result enters `FIX_REQUIRED` and only the *new* round costs a call | `test_A2_recovered_blocking_result_enters_fix_without_extra_call` |
| B | Half-applied legacy state (`fe4b044`) finishes without duplicate history | `test_B_legacy_half_apply_finishes_without_duplicate_history` |
| C | `finding_seen_counts` counted exactly once across repeated continues | `test_C_repeated_continue_keeps_single_application` |
| D | Applied marker + missing terminal transition completes locally, no reviewer call | `test_D_applied_marker_without_transition_completes_locally` |
| E | Fully applied + repeated `continue` -> no-op, no extra calls, no audit growth | `test_E_fully_applied_repeated_continue_is_a_noop` |
| F | Uncertain external call still fails closed and invents no result | `test_F_uncertain_call_fails_closed_and_invents_no_result` |
| D* | Reviewer call ids unique across restart + unblock + retry | `test_reviewer_call_ids_unique_across_unblock_retry` |
| E* | Reviewer call evidence immutable across retry (byte-identical) | `test_reviewer_call_ids_unique_across_unblock_retry` |
| F* | Implementer retry gets a new attempt id (`A0002`) | `test_implementer_retry_gets_new_identity_and_keeps_evidence` |
| G* | Implementer evidence (attempt/call/run/log) survives the retry | `test_implementer_retry_gets_new_identity_and_keeps_evidence` |
| H* | All provider call ids globally unique and linked to attempts | `test_call_ids_are_unique_and_usage_matches_actual_calls` |
| I* | Budget usage agrees with the actual fake call count | `test_call_ids_are_unique_and_usage_matches_actual_calls` |
| J | Policy refresh preserves before/after YAML + record + SHA-256 | `test_policy_refresh_preserves_before_after_and_usage` |
| K | Refresh never resets usage/call ids; §12 limit semantics hold | `test_policy_refresh_preserves_before_after_and_usage` |
| L | Response cap wording is accurate and behaviour stays fail-closed | `test_response_cap_wording_and_behaviour` |
| M | Mixed retry sequence: phase + error type match the real cause | `test_mixed_retry_sequence_labels_each_cause` |
| M2 | Engine-level format retries: 3 calls, unique ids, exact usage | `test_engine_level_format_retries_are_counted_and_unique` |
| N | Fingerprint normalizes separators/order, never case | `test_fingerprint_normalizes_separators_not_case` |
| O | New tasks persist `policy_source: snapshot` + schema 4 + sequences | `test_new_task_persists_policy_source` |
| P | Legacy task `status`/`usage` are read-only (state bytes unchanged) | `test_legacy_status_and_usage_are_read_only` |
| P3-06 | Review-history prompt growth is linear and non-nested | `test_review_history_prompt_growth_is_linear_and_non_nested` |
| Budget 1 | Recovery after a crash keeps reviewer usage at 1 (not 2) | `test_A_persisted_result_replayed_with_zero_reviewer_calls` |
| Budget 2 | Failed implementer = 1 call, retry success = 2 | `test_implementer_retry_gets_new_identity_and_keeps_evidence` |
| Budget 3 | Format retries: every HTTP call is counted (3) | `test_engine_level_format_retries_are_counted_and_unique` |
| Budget 4 | Manual review consumes 0 external calls | `test_budget_manual_review_costs_zero_external_calls` |
| Budget 5 | Budget-refused call spends nothing | `test_budget_refused_call_spends_nothing` |

## Smoke-blocker remediation (baseline capture, v0.2-A)

| # | Criterion | Evidence |
| --- | --- | --- |
| B1 | `.devrelay/` gitignored -> `devrelay init` + `devrelay start` succeed, state `PLAN_REQUIRED`, no `BaselineError` | `test_baseline_ignored_self.py::test_start_succeeds_when_devrelay_is_ignored` |
| B2 | Raw capture in the same repo excludes `.devrelay` from the tree | `test_raw_capture_survives_ignored_self_dir` |
| B3 | `.devrelay` not ignored -> self state still excluded (baseline + current tree) | `test_self_state_excluded_when_not_ignored` |
| B4 | Repository that *tracks* `.devrelay/**` -> excluded from tree and patch | `test_tracked_devrelay_state_is_excluded` |
| B5 | Other ignored files stay excluded; untracked + staged-new + tracked modification included; tracked deletion represented | `test_ignored_files_excluded_and_new_files_included` |
| B6 | Real `.git/index` bytes unchanged; temp index cleaned up | `test_real_index_bytes_unchanged_and_temp_index_cleaned` |
| B7 | Task-relative delta excludes DevRelay state | `test_task_delta_excludes_devrelay_state` |
| B8 | The failing argv (`:(exclude).devrelay` on an ignored path) is not used and still demonstrably fails | `test_exclude_pathspec_on_ignored_path_is_not_used` |

## Verification run (recorded)

| Item | Value |
| --- | --- |
| Date | 2026-09-10 |
| Command | `python -m pytest -q --junitxml=...` (offline, no network) |
| Result | **227 tests, 0 failures, 0 errors, 0 skipped** |
| v0.2-A subset | 60 tests (files `tests/test_v02a_*.py`, incl. 22 audit-remediation tests) |
| Baseline smoke-blocker subset | 8 tests (`tests/test_baseline_ignored_self.py`) |
| Branch / base | `v0.2-a-auto-review` (`fe4b044` + remediation commit) |
| Environment | Python 3.14.6, git 2.55.0.windows.3, Windows/Git Bash |
| Provider usage | zero real Codex calls, zero real reviewer HTTP calls |

Reproduce with `python -m pytest -q`. The junit XML is a build artifact and is
not committed.
