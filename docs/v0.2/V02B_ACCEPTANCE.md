# DevRelay v0.2-B acceptance criteria

Project profiles, runtime-wiring/policy separation and frozen-policy snapshot
integrity. **Candidate under independent review**: not released, package version
stays `0.1.0`, everything below was validated offline with fake providers (no
real Codex invocation, no real reviewer endpoint).

Evidence column names the test that pins the behaviour down. Every test is
offline; no network, no subprocess provider.

## Wiring / policy separation

| # | Criterion | Evidence |
| --- | --- | --- |
| B1 | `WiringConfig` shares no field with `PolicyDocument`; a workspace config can never be used as task policy | `test_v02b_config_split.py::test_wiring_config_shares_no_field_with_policy`, `::test_pipeline_policy_rejects_a_config_object` |
| B2 | `self.runtime_config` exposes no policy attribute (structural, not conventional) | `test_v02b_config_split.py::test_engine_runtime_config_carries_no_policy` |
| B3 | The task's frozen policy is a `PolicyDocument` with no selector and no wiring | `test_v02b_config_split.py::test_task_snapshot_is_a_policy_document` |
| B4 | Profiles may set policy only (`git`/`codex`/`review.provider`/unknown keys rejected) | `test_v02b_profiles.py::test_profiles_may_only_set_policy` |
| B5 | Broken live policy overrides do not become an execution prerequisite for a frozen task | `test_v02b_profile_cli.py::test_frozen_task_continues_despite_broken_live_policy`, `test_v02b_profiles.py::test_frozen_task_records_profile_provenance_and_ignores_later_edits` |
| B6 | A new task still fails closed when the live policy is malformed | `test_v02b_profile_cli.py::test_start_fails_closed_on_broken_live_policy`, `test_v02b_profiles.py::test_new_task_fails_closed_on_a_broken_live_policy` |

## Byte writer and snapshot integrity

| # | Criterion | Evidence |
| --- | --- | --- |
| B7 | Every textual artifact is written as deterministic LF bytes | `test_v02b_byte_writer.py` (all) |
| B8 | The recorded digest is the digest of the bytes on disk | `test_v02b_snapshot_integrity.py::test_recorded_digest_matches_on_disk_bytes` |
| B9 | Corrupt snapshot: fail closed, no provider call, no state mutation | `test_v02b_snapshot_integrity.py::test_corrupt_snapshot_fails_closed` |
| B10 | Snapshot replaced by another *valid* policy: digest mismatch before parsing | `test_v02b_snapshot_integrity.py::test_snapshot_replaced_by_another_valid_policy_fails_closed` |
| B11 | Modern task with a deleted snapshot is `missing`, never legacy | `test_v02b_snapshot_integrity.py::test_modern_snapshot_deleted_is_missing_not_legacy` |
| B12 | A v0.2-A (schema 4, digest-less, CRLF) snapshot still governs its task | `test_v02b_snapshot_integrity.py::test_v02a_snapshot_task_keeps_its_frozen_policy` |
| B13 | A genuine pre-snapshot task keeps the explicit live-policy path | `test_v02b_snapshot_integrity.py::test_genuine_legacy_task_is_legacy_live` |
| B14 | Classification/verification happens before any provider object exists | `test_v02b_cli_policy.py::test_corrupt_snapshot_never_constructs_a_provider`, `::test_deleted_snapshot_never_constructs_a_provider` |

## Profiles

| # | Criterion | Evidence |
| --- | --- | --- |
| B15 | Precedence packaged defaults < profiles (order) < workspace overrides | `test_v02b_profiles.py::test_precedence_defaults_profiles_overrides` |
| B16 | Lists replace wholesale | `test_v02b_profiles.py::test_lists_replace_wholesale` |
| B17 | One name grammar everywhere; limits (8 profiles, 1 MiB, duplicates, missing) | `test_v02b_profiles.py::test_profile_name_grammar_is_single_sourced`, `::test_selector_limits_and_duplicates`, `::test_missing_profile_and_oversized_file_fail_closed` |
| B18 | Raw inspection works with a broken selector and reports everything | `test_v02b_profiles.py::test_raw_inspection_survives_a_broken_selector`, `test_v02b_profile_cli.py::test_profile_list_works_with_a_broken_selector`, `::test_profile_show_and_validate_are_per_file` |
| B19 | Provenance records selector, per-profile raw hashes and the config hash | `test_v02b_profiles.py::test_precedence_defaults_profiles_overrides` |

## CLI diagnostics and recovery

| # | Criterion | Evidence |
| --- | --- | --- |
| B20 | `config show` never opens a profile and never implies policy authority | `test_v02b_profile_cli.py::test_config_show_unresolved_is_useful_with_a_broken_chain` |
| B21 | `config show --resolved` is authoritative and fails closed | `test_v02b_profile_cli.py::test_config_show_resolved_is_authoritative` |
| B22 | `doctor` reports raw diagnostics and the chain separately; `--strict` exits non-zero | `test_v02b_profile_cli.py::test_doctor_reports_raw_and_chain_separately` |
| B23 | `status`/`usage` never read a live profile and never rewrite state | `test_v02b_profile_cli.py::test_status_and_usage_ignore_live_profiles` |
| B24 | Recovery of a missing snapshot invents no before-state | `test_v02b_refresh_recovery.py::test_recovery_of_missing_snapshot_records_no_invented_before` |
| B25 | Recovery of a damaged snapshot preserves its bytes as evidence | `test_v02b_refresh_recovery.py::test_recovery_of_hash_mismatch_keeps_the_damaged_bytes_as_evidence` |
| B26 | Generation counts successful freezes, not semantic changes | `test_v02b_refresh_recovery.py::test_generation_counts_evidence_not_semantic_change` |
| B27 | Refresh never touches usage, call identities, attempts or history | `test_v02b_refresh_recovery.py::test_refresh_preserves_usage_calls_and_history` |
| B28 | Replacing an intact policy needs `--force`; damaged snapshots do not | `test_v02b_cli_policy.py::test_refresh_of_intact_policy_requires_force`, `::test_refresh_of_damaged_snapshot_needs_no_force` |
| B29 | Status reports an unverifiable snapshot without failing or repairing | `test_v02b_cli_policy.py::test_status_reports_unverified_snapshot` |

## State schema

| # | Criterion | Evidence |
| --- | --- | --- |
| B30 | v0.2-B writes schema 5 and records provenance | `test_v02a_audit_remediation.py::test_new_task_persists_policy_source` (approved literal update), `test_v02b_snapshot_integrity.py::test_recorded_digest_matches_on_disk_bytes` |
| B31 | State from a newer DevRelay gets a dedicated diagnostic; read-only commands do not rewrite it | `test_v02b_cli_policy.py::test_state_schema_too_new_has_a_dedicated_error` |
| B32 | v0.1/v0.2-A states still load and keep working | `test_v02a_state_migration.py` (unchanged) |

## Process

| # | Criterion | Evidence |
| --- | --- | --- |
| P1 | Offline: no real Codex run, no reviewer request, no network in any test | full `python -m pytest`; provider spies in `test_v02b_cli_policy.py` |
| P2 | No version bump, no tag, no push, no release, no PyPI action | package version stays `0.1.0`; local commits only |
| P3 | v0.2-A behavioural coverage preserved | full suite, only two approved assertions updated (schema literal, default-policy source) |
