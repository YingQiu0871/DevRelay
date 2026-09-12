# DevRelay v0.2-C acceptance matrix

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
| C7 | Non-zero exit with partial result → hard failure, evidence kept | PARTIAL | `test_nonzero_exit_is_a_hard_failure` (result not parsed on failure by design) |
| C8 | Timeout: child killed, bounded capture, failure | PARTIAL | `test_runner.py` (terminate→kill, bounded capture) + structured path inherits it |
| C9 | Unknown completion / crash → fail closed | COVERED | `test_v02c_replay.py::test_hard_crash_uncertainty_fails_closed_without_rerun` |
| C10 | Replay without reinvocation (0 calls) | COVERED | `test_completion_replay_workspace_match` |
| C11 | Unique attempt/call identities | COVERED | v0.2-A identity suites + happy-path call count |
| C12 | Provider budget accounting unchanged | COVERED | v0.2-A budget suite + `usage_block` assertions |
| C13 | Git guard violation wins over claims | COVERED | `test_policy_guard.py` (unchanged) |
| C14 | Binary/untracked/CRLF delta handling | COVERED | `test_baseline_service.py`, `test_audit_remediation.py` (unchanged) |
| C15 | Secret containment in runtime artifacts | COVERED | `test_structured_happy_path…` + `test_secret_in_tampered_file_never_reaches_evidence` |
| C16 | Unicode/quoted paths | PARTIAL | argv-list invocation (no shell) + claim normalization unit; no dedicated end-to-end Unicode path test |
| C17 | Old CLI without structured flags → `codex_runtime_unsupported`, 0 cost | PARTIAL | capability detection + engine pre-flight block path (unit-tested helpers) |
| C18 | v0.2-B (schema 5) state loads and migrates | COVERED | `test_v02c_units.py::test_schema5_state_loads_and_migrates` |
| C19 | No commit/push/tag/reset; index untouched | COVERED | guard + baseline suites (unchanged) |
| C20 | Full offline suite green | COVERED | `python -m pytest` — 338 passed |
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
