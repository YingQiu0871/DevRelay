# DevRelay v0.2-C acceptance matrix

> Later status (2026-10-20): included in DevRelay 0.3.0; independent acceptance is not complete; evidence remains offline/fake-provider only.

Evidence column names the test that proves the criterion. All tests are offline
(stub Codex CLI, fake providers, real tiny git repositories); no model call and no
network request is involved.

Legend: **COVERED** = automated test asserts it · **PARTIAL** = covered
indirectly or by existing (v0.1–v0.2-B) suites · **DEFERRED** = documented, not
automated in this stage.

| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| C1 | Structured happy path: result parsed, sanitized, persisted, `TESTING` | COVERED | `test_v02c_structured.py::test_structured_happy_path_persists_sanitized_evidence` |
| C2 | Claimed files vs observed delta recorded | COVERED | `implementation-reconciliation.json` asserted in the happy-path test + `reconcile_observed_files` unit |
| C3 | Omitted changed file flagged (`unclaimed_change`) | COVERED | happy-path warnings |
| C4 | Falsely claimed file flagged (`claimed_not_changed`) | COVERED | happy-path warnings |
| C5 | Malformed result → `codex_result_malformed`, no retry | COVERED | `test_structured_failures_block_without_retry` |
| C6 | Missing result (exit 0) → `codex_result_missing` | COVERED | same |
| C7 | Non-zero exit with partial result → hard failure, evidence kept | COVERED | `test_v02c_p1_remediation.py::test_c7_nonzero_exit_with_a_valid_result_is_still_a_failure` (a *valid* result still cannot upgrade a failed process; charged once, no `result.json`/`completion.json`) |
| C8 | Timeout: child killed, bounded capture, failure | COVERED | `test_v02c_p1_remediation.py::test_structured_timeout_kills_the_contained_tree_and_still_checks_post` (contained tree killed, POST still runs, run still charged) + `test_runner.py` |
| C9 | Unknown completion / crash → fail closed | COVERED | `test_v02c_replay.py::test_hard_crash_uncertainty_fails_closed_without_rerun` |
| C10 | Replay without reinvocation (0 calls) | COVERED | `test_completion_replay_workspace_match` |
| C11 | Unique attempt/call identities | COVERED | v0.2-A identity suites + happy-path call count |
| C12 | Provider budget accounting unchanged | COVERED | v0.2-A budget suite + `usage_block` assertions |
| C13 | Git guard violation wins over claims | COVERED | `test_policy_guard.py` (unchanged) |
| C14 | Binary/untracked/CRLF delta handling | COVERED | `test_baseline_service.py`, `test_audit_remediation.py` (unchanged) |
| C15 | Secret containment in runtime artifacts | COVERED | `test_structured_happy_path…` + `test_secret_in_tampered_file_never_reaches_evidence` |
| C16 | Unicode/quoted paths | COVERED | `test_v02c_p1_remediation.py::test_c16_unicode_paths_end_to_end` (unicode workspace root + unicode claim, end-to-end) |
| C17 | Old CLI without structured flags → `codex_runtime_unsupported`, 0 cost | PARTIAL | capability detection + engine pre-flight block path (unit-tested helpers) |
| C18 | v0.2-B (schema 5) state loads and migrates | COVERED | `test_v02c_units.py::test_schema5_state_loads_and_migrates` |
| C19 | No commit/push/tag/reset; index untouched | COVERED | guard + baseline suites (unchanged) |
| C20 | Full offline suite green | COVERED | `python -m pytest` — 349 passed (was 338 before the P1 remediation; 11 new tests, none weakened, no skip/xfail added) |
| C21 | COMPLETION_READY + matching identities → local replay, `TESTING` once | COVERED | `test_completion_replay_workspace_match` |
| C22 | Workspace drift → `implementer_replay_workspace_changed`, 0 calls, no rollback | COVERED | `test_completion_replay_workspace_drift_blocks` |
| C23 | Raw `-o` staged transiently, sanitized durable result, raw hash recorded | COVERED | happy-path test (+ `staging_removed`, `raw_result_sha256`) |
| C24 | Stale raw staging is never evidence; cleaned or refused | COVERED | `test_v02c_units.py::test_stale_staging_cleanup_and_refusal` |
| C25 | `codex.args` conflict with DevRelay-owned flags rejected before invocation | COVERED | `test_v02c_structured.py::test_argument_ownership_rejects_indirect_bypasses` |
| C26 | Two-stage reconciliation (implementation now, tests after) | COVERED | happy-path test asserts both artifacts |
| C27 | Missing/unknown `ImplementationResult.schema_version` → malformed | COVERED | `test_structured_failures_block_without_retry` |
| C28 | Oversized `-o` → bounded read, `codex_result_too_large`, no retry | COVERED | same |
| C29 | Codex child env denylist; OS/toolchain env preserved | COVERED | happy-path env capture assertion |
| C30 | Model status is advisory (exit 0 + `BLOCKED` still proceeds) | COVERED | `test_model_status_is_advisory` |
| C31 | Child edits task `state.json` → violation, hold, no `TESTING`, tamper preserved | COVERED | `test_control_plane_violation_on_state_tamper` |
| C32 | Child edits the call ledger → violation | COVERED | `test_control_plane_violation_on_ledger_tamper` |
| C33 | Child edits another task's state → violation | PARTIAL | same manifest mechanism (other-task dirs are protected); no dedicated test |
| C34 | Only the declared staging file may be written | COVERED | happy path (no violation) |
| C35 | Unexpected staging entry → violation | COVERED | `test_control_plane_violation_on_unexpected_staging_file` |
| C36 | Stale staging: remove safely or refuse before a new attempt | COVERED | `test_stale_staging_cleanup_and_refusal` |
| C37 | Pre-existing durable runtime path → fail closed, no overwrite | COVERED | `test_durable_runtime_artifact_collision_fails_closed` |
| C38 | Indirect config bypass (`-p`, unsafe `-c`, repo config) cannot weaken controls | COVERED | ownership test + repo-config gate in `prepare_runtime` |
| C39 | External control-state edit after READY → `replay_control_state_changed`, 0 calls | COVERED | `test_replay_blocked_by_state_json_drift`, `test_replay_blocked_by_protected_manifest_drift` |
| C40 | Normal run produces no control-plane violation | COVERED | happy path (`control_plane_changes == 0`) |
| C41 | PRE trust is parent-memory only during execution | COVERED | `test_no_child_writable_pre_artifact_is_written` (no PRE artifact exists; in-memory comparison drives the POST check) |
| C42 | No raw tamper content in durable evidence | COVERED | `test_control_plane_violation_on_state_tamper`, `test_secret_in_tampered_file_never_reaches_evidence` |
| C43 | Allowed staging creation does not false-positive | COVERED | `test_v02c_units.py::test_staging_metadata_exempt_but_unexpected_entries_detected` |
| C44 | Baseline integrity root tamper → violation | COVERED | `test_baseline_root_files_are_content_hashed` |
| C45 | Baseline blob tamper → integrity verification fails before use | COVERED | `test_baseline_blob_tamper_is_detected_before_use` |
| C46 | Hold cannot be cleared while protected state differs | COVERED | `test_hold_ack_refused_while_divergent_then_cleared_after_restore`, `test_tampered_pre_copy_is_refused` |
| C47 | Hard-crash uncertainty: no automatic restore from disk evidence | COVERED | `test_no_child_writable_pre_artifact_is_written` (missing completion evidence blocks), `test_hard_crash_uncertainty_fails_closed_without_rerun` |
| C48 | Junction/reparse handling (probe SKIPPED, never PASS, when privileged) | COVERED | `test_v02c_units.py::test_reparse_detection_uses_platform_attributes` |
| C49 | Hold discovery precedes workspace-index trust | COVERED | `test_hold_discovery_survives_corrupt_workspace_index` |
| C50 | Old-child uncertainty prevents an automatic new Codex attempt | COVERED | `test_hard_crash_uncertainty_fails_closed_without_rerun` |

## Independent-review P1 remediation closure

| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| R1 (P1-A) | A frozen task driven through the **production CLI** really runs the structured runtime | COVERED | `test_cli_continue_runs_the_structured_runtime` — real `devrelay init/start/plan import/continue`; stub argv has exactly one `exec`/`--sandbox` plus every DevRelay-owned flag, the launcher prefix made the stub the entry point, `runtime.json`/`schema.json`/`result.json`/`completion.json` exist, `status` shows `Runtime: structured`, `doctor` agrees, and the frozen snapshot carries no `codex`/`runtime_mode` key (proof the mode cannot come from task policy) |
| R2 (P1-A) | An explicitly text-wired workspace keeps the legacy path (no silent upgrade/downgrade) | COVERED | `test_cli_runtime_mode_text_is_explicit_and_stays_text` — argv has no `--output-schema`/`--output-last-message`/`--ignore-rules`, no `exec`, no launcher prefix; `status` shows `Runtime: text` |
| R3 (P1-B) | A detached descendant cannot mutate the control plane after POST | COVERED | `test_detached_descendant_cannot_tamper_after_post` — the delegated grandchild's write is scheduled after the Codex process exits; `evil.txt` never appears, `state.json` title is untouched, and the tamper payload's liveness is proven by an uncontained control run in the same test |
| R4 (P1-B) | Inherited pipes cannot hang the parent, and a timed-out tree is really dead | COVERED | `test_descendant_inheriting_pipes_is_contained_without_hanging` (bounded run, `containment_all_dead == True`), `test_structured_timeout_kills_the_contained_tree_and_still_checks_post` (60 s child killed at a 2 s timeout; its 6 s descendant write never lands) |
| R5 (P1-B / capability gate) | Structured mode refuses to start without strong containment (0 provider calls) | COVERED | `test_containment_is_required_for_structured_mode` — `codex_process_containment_unsupported`, `implementer_calls == 0`, ledger entry settled at `external_call_count == 0`, no argv ever captured; `doctor` reports the missing capability |
| R6 (P1-D) | A consumed call is never erased by the failure paths | COVERED | `test_violation_keeps_the_consumed_call_charged` (`provider_calls == [DR-0001-C0001]`, usage 1, ledger file, hold on the same call id, containment recorded in the violation report), `test_state_tamper_keeps_the_consumed_call_in_the_trusted_pre` (tampered `state.json` left exactly as written; the parent's `*-state.pre.json` copy contains the charged call) |
| R7 (P1-B, fail closed) | POST is skipped entirely when the contained tree cannot be confirmed dead | COVERED | `test_unverified_containment_skips_post_and_holds` — forced containment-deadline failure: `codex_containment_unverified`, `post_manifest_sha256 == ""` (POST never ran), no `COMPLETION_READY`/verdict persisted, hold written, call still charged |
