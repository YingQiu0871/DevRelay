# Changelog

All notable changes to DevRelay are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased - v0.2-B project profiles (candidate under independent review)

Reusable project policy profiles on top of a frozen, integrity-verified task
policy. **Not released**: the package version stays `0.1.0`, nothing is pushed,
merged, tagged or published, and all v0.2-B behaviour was validated offline with
fake providers (no real Codex invocation, no real reviewer endpoint).

### Added

- **Project profiles** - `.devrelay/profiles/<name>.yaml` plus an ordered
  `profiles: [base, python]` selector in `.devrelay/config.yaml`. Precedence:
  packaged policy defaults < profiles in selector order < workspace overrides.
  Profile files are *policy only*: `review.provider`, `codex.*`, `git.*` and the
  selector itself are rejected (the model is the allowlist). Limits: <= 8
  profiles, <= 1 MiB per file, `yaml.safe_load`, no `extends`, no user/global
  profile directory, no CLI override, one name grammar, strict path containment.
- **Raw profile diagnostics** - `devrelay profile list|show|validate`, which work
  even when the selector is broken, and `profile validate` reports *all*
  problems (invalid filenames, per-file errors, selector syntax, duplicates,
  missing references) instead of stopping at the first one.
- **`devrelay config show` / `--resolved`** - the first prints live runtime
  wiring plus the raw, unresolved selector and explicitly says it is not the
  effective task policy; the second is the authoritative, fail-closed resolver.
- **`devrelay doctor`** now reports raw profile inspection and the full policy
  chain separately, flags pre-schema-5 tasks and profile drift, and has
  `--strict` for CI use (exit non-zero when anything is not OK).
- **Snapshot integrity** - `tasks/<id>/config.snapshot.yaml` is verified by
  SHA-256 over its exact on-disk bytes *before* it is parsed, and
  `devrelay unblock --reason "..." --refresh-policy` recovers a missing,
  invalid or hash-mismatched snapshot (recording `before_snapshot_available`
  instead of inventing a before-snapshot).

### Changed

- **Runtime wiring and task policy are separate types.** `WiringConfig`
  (`review.provider`, `codex.*`) is live and never frozen; `PolicyDocument`
  (`pipeline`, `budget`, `review` policy knobs, `tests`, `scope`, `baseline`,
  `git`) is resolved once and frozen into the task. `PipelinePolicy` accepts only
  a `PolicyDocument`; a workspace config can no longer be used as task policy.
- **`state_schema_version` 4 -> 5**: tasks persist `policy_snapshot_path`,
  `policy_config_sha256` and `policy_provenance` (selector, per-profile raw-byte
  hashes, workspace-config hash, generation, integrity). Before the first write
  that upgrades an older task, its state is copied once to
  `state.v<old>.json.bak`. State written by a *newer* DevRelay now produces a
  dedicated `state_schema_too_new` diagnostic instead of a model error.
- **All textual artifacts are written as UTF-8 with LF endings**, and every
  recorded digest is the digest of the bytes actually written (on Windows,
  `Path.write_text` used to turn LF into CRLF while hashes were computed over
  LF text, so recorded hashes could never match the disk).
- **`status`, `usage`, `diff` and `logs` are state-only**: they never validate
  live policy, never resolve the profile chain and never read a profile file, so
  deleting or editing profiles cannot break them. Live drift belongs to
  `doctor` and `config show --resolved`.
- **Execution commands classify the snapshot before any provider object is
  constructed**, so a damaged snapshot fails closed without building a Codex or
  reviewer client.
- `devrelay init` installs a workspace template (wiring + selector + commented
  policy overrides) instead of a copy of the policy defaults, and creates
  `.devrelay/profiles/`. The packaged `src/devrelay/profiles/default.yaml` is now
  the single editable default authority: the in-code `DEFAULT_PROFILE_YAML`
  literal and the repository-root `profiles/default.yaml` copy are gone.

### Removed

- The v0.2-A silent policy downgrade: a task whose snapshot is missing, invalid
  or hash-mismatched no longer continues under live wiring/workspace defaults.
  Only genuine pre-snapshot ("legacy") tasks resolve live policy, and the
  execution path never writes `policy_source`.

### Fixed (independent-review P2 remediation)

- **P2-1 - real state-schema migration.** The first *mutating* write of a task
  whose persisted `state_schema_version` is older than the current schema now
  keeps the exact previous `state.json` bytes in a one-time
  `state.v<old>.json.bak` and only then writes the upgraded (schema-current)
  document. The backup is created once, is never overwritten, and a backup
  failure aborts the write with `state.json` untouched; the upgraded document is
  a serialized copy, so the caller's in-memory task is never mutated and a
  failed write stays retryable. v5-only fields can no longer land in a file that
  still claims schema 4, and `doctor` stops reporting a permanently pending
  migration. Read-only commands still never migrate and never create a backup.
  A *migrated* v0.2-A task still uses its digest-less legacy snapshot: the
  integrity-metadata requirement now keys off the recorded snapshot path rather
  than the bare schema number.
- **P2-2 - refresh evidence is append-only.** Refresh evidence identity no
  longer comes from `len(task.policy_refreshes) + 1`. Every attempt that starts
  writing evidence consumes a unique, never-reused *evidence attempt* number
  allocated from both persisted records and on-disk `policy-refresh-NN-*`
  artifacts (gaps tolerated, `max(seen) + 1`), and the evidence files are
  written with create-new writers that refuse to replace an existing path. A
  failed attempt's artifacts therefore survive a retry untouched: attempt 01
  stays on disk as orphan evidence while the successful retry is attempt 02 and
  may still advance generation 1 -> 2. An on-disk artifact is evidence of an
  *attempt*; a refresh counts as applied only when the persisted task references
  that record and its generation/digest/provenance describe the applied
  generation. Orphan evidence is never deleted, never overwritten and never
  treated as applied.

## Unreleased - v0.2-C candidate (structured Codex runtime)

Structured, isolated, tamper-evident and replayable Codex runtime. **Not
released**: version stays `0.1.0`, nothing is pushed/merged/tagged/published, and
everything below is validated offline with a stub Codex CLI (no model call, no
network).

### Added

- Structured implementer contract: `--output-schema` + `--output-last-message`
  with a validated `ImplementationResult` (`schema_version = 1`); `--json` events
  are observational only and never required for a run to count.
- Transient raw result staging under `.devrelay/tmp/runtime/<attempt-id>/`:
  bounded read, `raw_result_sha256`, sanitized immutable `result.json` (create-new
  writers), best-effort removal, stale-staging cleanup-or-refuse policy.
- DevRelay-owned Codex argv: `exec`, `--sandbox workspace-write` (exactly once),
  `--ignore-user-config`, `--ignore-rules`, `--json`, schema/result flags, cwd and
  stdin prompt. `-p/--profile`, user `--sandbox`, `--add-dir`, `--cd`,
  `--skip-git-repo-check`, `--approve-for-me`, bypass flags, output-path flags and
  unsafe `-c` namespaces are rejected; a repository Codex config fails structured
  mode closed (`codex.runtime_mode: text` is the explicit opt-out).
- Codex child environment scrub (reviewer + enumerated LLM provider credentials),
  honestly documented as an explicit denylist, not general secret isolation.
- Control-plane guard: in-memory PRE manifest, POST verification before any state
  re-read, `codex_control_plane_violation` fail-closed path, metadata-only
  violation evidence (no raw tampered content), durable hold with
  verification-gated recovery (`--acknowledge-control-plane-violation`,
  `--restore-state-from-pre`).
- Durable implementer milestones (`PROCESS_EXITED` … `COMPLETION_READY` …
  `COMPLETION_APPLIED`) with idempotent application; `attempt_in_flight` is only
  cleared once a replay-safe verdict exists.
- Completion replay: a `COMPLETION_READY` attempt with matching identities is
  applied locally with **0 external calls**; drift blocks as
  `implementer_replay_workspace_changed` / `replay_control_state_changed`;
  `devrelay unblock --replay-completion` applies it explicitly after a human
  restored the workspace.
- Two-stage reconciliation (`implementation-reconciliation.json`,
  `test-reconciliation-NN.json`) surfacing claimed-vs-observed files, rejected
  traversal claims, unknown result field names and test-claim disagreements.
- Baseline root hardening: `baseline.json`/`manifest.json`/`tracked.patch` are
  content-hashed by the guard and untracked blobs are verified against their
  declared SHA-256 before use.
- Bounded, deadlock-free process capture (always-drain reader threads, head+tail
  retention) with truncation evidence, `env_remove` support and terminate→kill
  fallback.
- `doctor` reports the effective runtime mode, structured capability and the
  scrubbed credential names; `status`/`usage` show runtime milestones and results.

### Changed

- `state_schema_version` 5 → 6 (durable milestones, workspace/control-plane
  identity, runtime evidence), reusing the existing migration/backup/too-new
  machinery; v0.2-B tasks keep loading and read-only commands still never migrate.
- Bumped `MAX_SUPPORTED_STATE_SCHEMA` accordingly; a v0.2-B binary refuses v6 with
  `state_schema_too_new` instead of guessing.

### Fixed (independent-review P1 remediation)

- **P1-A — structured mode was silently downgraded on every frozen-task CLI
  path.** The effective runtime mode was read from the *task policy* source, but
  the CLI builds engines with `config=None` for tasks that own a frozen snapshot,
  so `devrelay continue` fell back to `text`: no `--output-schema`, no bounded
  result read, no child environment scrub, no control-plane PRE/POST guard and no
  containment — a silent loss of the whole v0.2-C contract. The mode now comes
  from the live `WiringConfig` only (`self.runtime_config.codex.runtime_mode`),
  the frozen document stays authoritative for policy only (it carries no `codex`
  section at all), and a mis-wired engine fails pre-flight instead of
  downgrading. `status` prints the effective mode as `Runtime:` and `doctor`
  reports mode, capability and containment. Regression coverage drives the *real
  CLI* end-to-end (`test_cli_continue_runs_the_structured_runtime`,
  `test_cli_runtime_mode_text_is_explicit_and_stays_text`), not just an internal
  helper.
- **P1-B — a detached descendant could mutate the control plane after POST.**
  Nothing contained the Codex process tree: the child could spawn a detached
  grandchild that outlived it, wait for the POST manifest comparison to pass and
  then rewrite `.devrelay/tasks/<id>/state.json` (and drop arbitrary files) with
  no violation and no trace. New module `devrelay/workspace/containment.py`
  provides the abstraction (`spawn_contained` / `wait_contained` /
  `terminate_contained` / `kill_contained` / `all_contained_processes_dead`) and a
  race-free Windows Job Object backend (`KILL_ON_JOB_CLOSE`, no breakaway, broker
  hand-off *before* Codex runs). The runner ends a contained window by closing the
  job and verifying `all_contained_processes_dead()` **before** the engine
  computes POST, so a surviving descendant can no longer land after the guard. The
  refusal is honest: on POSIX (where a process group cannot contain a
  `setsid`/double-fork descendant) structured mode fails pre-flight with
  `codex_process_containment_unsupported` and **0 provider calls** instead of
  claiming weak containment, and `doctor` flags the missing capability.
  Containment facts (`containment`, `containment_all_dead`) are persisted in the
  attempt runtime evidence and in the violation report.
- **P1-D — a consumed call disappeared from `provider_calls`/budget on the
  control-plane-violation path.** The pre-run attempt write persisted a stale
  in-memory `TaskRun` and erased the accounting intent recorded moments earlier,
  so a *real* Codex invocation that was voided by the guard left
  `provider_calls == []`, budget usage `0` and an orphan `policy/calls/*.json`
  entry. The pre-run write now merges the persisted accounting facts (call list
  plus the monotonic sequencing counters, `max()` of both sides) into the record
  it writes while the caller's in-memory transition is preserved. A voided run is
  now fully charged: call id `DR-0001-C0001`, usage `implementer_calls == 1`,
  ledger entry present, hold referencing the same call id, and the trusted
  parent-held `*-state.pre.json` copy contains it.
- **C7 / C16 acceptance closure.** `C7`: a non-zero exit with a *valid* model
  result is still a failure (`implementer_failed`, no `COMPLETION_READY`, no
  durable `result.json`) and is still charged once. `C16`: unicode workspace
  roots, staging paths and claimed file names survive the whole structured
  runtime (manifest, reconciliation, evidence).

## Unreleased - v0.2-A candidate (audit remediation, closure audit pending)

Automatic review loop with an enforced execution budget, plus the remediation of
the independent audit of commit `fe4b044` (one P1, three P2, six P3 findings).
**Not released**: the package version stays `0.1.0`, nothing is pushed, merged,
tagged or published, and the behaviour below was validated with fake providers
only (no real Codex invocation and no real reviewer endpoint were used).

### Fixed

- Baseline capture no longer fails with `git add -A -- . :(exclude).devrelay
  failed: The following paths are ignored ...: .devrelay` in repositories whose
  `.gitignore` lists `.devrelay/` (the normal, documented setup). The worktree
  tree is now built from an explicit list of eligible paths (tracked changes +
  non-ignored new files, `.devrelay` filtered in DevRelay code) against the
  temporary index, never from an explicitly named ignored pathspec, and never
  with `git add -f` (which would include unrelated ignored files). A repository
  that *tracks* `.devrelay/**` is excluded symmetrically. Regression coverage:
  `tests/test_baseline_ignored_self.py`.

### Fixed (audit remediation)

- **P1-01** - the crash window between persisting a reviewer result and applying
  it can no longer cost a second paid reviewer call. A persisted, schema-valid,
  sanitized result is now an authoritative, replayable result: the next
  `continue` replays it locally with **0 external calls** and enters the
  policy-defined state (`FIX_REQUIRED` / `FINAL_GATE_REQUIRED` / `BLOCKED`).
  An *uncertain* call still fails closed - DevRelay never invents a result.
- **P1-01 (idempotency)** - the whole semantic application (history, seen
  counters, findings, applied marker, transition, audit) lands in **one atomic
  state write**, guarded by a stable result identity plus an
  `AppliedReviewRecord`. Restart replays therefore never duplicate history,
  counters, transitions or audit events; content equality alone is not treated
  as proof (two legitimately identical rounds still apply separately), and a
  missing terminal transition is completed locally only with proof that nothing
  happened since.
- **P2-01 / P2-02** - one durable, task-scoped identity system replaces
  process-local counters and success-derived numbering: call ids
  (`DR-0001-C0007`), implementer attempts (`DR-0001-A0002`) and review attempts
  (`DR-0001-R0002`) are allocated from persisted monotonic sequences before the
  invocation, never reused after a failure, and never reset by `unblock` or a
  policy refresh. Calls link to attempts (`parent_attempt_id`, `call_ids`).
- **P2-01 / P2-02 (evidence)** - immutable evidence is keyed by those identities
  (`policy/calls/<call-id>.json`, `policy/attempts/<attempt-id>.json`,
  `policy/runs/<attempt-id>-*.json`, `logs/<attempt-id>.*`,
  `reviews/review-NN-<attempt-id>-meta.json`); a retry can no longer overwrite a
  failed attempt's or another call's evidence. The legacy `NN`-named artifacts
  remain as documented "latest view" convenience copies.
- **P2-03** - `unblock --refresh-policy` preserves the previous policy:
  `PolicyRefreshRecord` plus `policy/policy-refresh-NN-{before,after}.yaml` and
  `-NN.json` (before/after SHA-256, actor, reason). Usage is never reset,
  deleted or renumbered, and existing calls count against the new limits.
- **P3-01** - `max_response_chars` is documented (config, README, error message)
  as a parsing/persistence cap; the HTTP client may buffer the body first, so it
  is not a network-level memory limit.
- **P3-02** - retry phase labels follow the failure cause; a mixed
  format/transport/format sequence no longer mislabels a transport retry as
  `REVIEW_FORMAT_RETRY`.
- **P3-03** - finding fingerprints normalize path separators and file order but
  never case-fold paths (POSIX repositories may contain both `A.py` and `a.py`).
- **P3-04** - `policy_source` is persisted as `snapshot` at task creation;
  `status`/`usage` resolve it read-only and never rewrite task state (legacy
  tasks keep reporting `live-fallback` unmodified).
- **P3-05** - AUD-09 stays open as a backlog item; `unblock` still clears the
  block record but now preserves it verbatim in the audit trail and deletes no
  evidence (calls, attempts, review attempts, policy refreshes).
- **P3-06** - review-history growth was analysed and proven linear/non-nested
  (one summary line per previous round, bounded by `max_reviewer_calls`); prompt
  compaction stays deferred.
- State schema bumped to **4** with public v0.1 state compatibility and a
  `finish_only` recovery path for private `fe4b044` state.

### Added

- Automatic review loop: the engine drives the reviewer itself and feeds
  blocking findings back into the fix prompt. The state machine is unchanged
  and the final gate stays manual - never an automatic `DONE`.
- Execution budget (`budget.max_implementer_calls` 4, `max_reviewer_calls` 4,
  `max_total_provider_calls` 8) checked **before** every external call;
  exceeding a limit BLOCKS the task with code `provider_budget_exhausted` and
  reports used/max for all three limits. The budget is never reset
  automatically.
- Persisted `ProviderCallRecord` for every attempted external invocation
  (kind, phase, success, error type, duration, model, endpoint host - never
  credentials or full URLs) plus `reviews/review-NN-call-MM-meta.json`.
- Reviewer attempt lifecycle (`ReviewAttempt`) with `review-NN-meta.json`:
  status, transport/format attempt counts and external calls consumed.
- Crash-safe in-flight marker (`review_call_in_flight`) persisted before the
  request: a hard kill leaves evidence, and the next `continue` fails closed
  with `interrupted_reviewer_attempt` until a human `unblock --reason ...`.
  A review round that was started but never finalized (crash after the provider
  answered, before the result was persisted) is detected from the persisted
  attempt and fails closed the same way; acknowledging it closes the round as
  `INTERRUPTED` without deleting its call evidence, and the retried round gets
  a unique attempt identity.
- Transport vs format failure separation (`transport_retries` default 0 is
  opt-in; every retry is a counted call) and a `max_response_chars`
  parsing/persistence cap - oversized answers are refused with an explicit
  error, never silently cut or guessed.
- Sanitized HTTP error bodies and model output (same redaction boundary as
  reviewer input) before persistence.
- Finding fingerprints
  (`sha256(severity | normalized title | files | description)`) with per-task
  seen counts, and the opt-in `pipeline.max_same_finding_cycles` stall guard
  (`0` = disabled; fingerprints are recorded either way).
- Task policy snapshot (`tasks/<id>/config.snapshot.yaml`) applied for the
  whole task, `policy_source` visibility, and the audited
  `devrelay unblock --refresh-policy --reason "..."` as the only supported way
  to change a running task's budget/blocking policy.
- `devrelay usage` (read-only provider usage/audit view); `status` now shows
  budget used/max, last review attempt and policy source; `doctor` reports
  reviewer env var **presence** only (`set`/`MISSING`) without sending a
  request, and prints the configured budget.
- State schema version 3 (`provider_calls`, `review_attempts`,
  `finding_seen_counts`, ...) with v0.1 fixture compatibility.

### Changed

- Policy authority over the reviewer: a `PASS` decision that still carries a
  blocking finding does not pass - the configured `blocking_severities` decides.
- The Codex FIX prompt carries structured findings (`- [P2] id=... title=...`
  with `description:` / `files:` / `evidence:` / `recommendation:` lines).
- Manual reviewing is unchanged and still makes zero external calls (a
  `ReviewAttempt` with `external_calls = 0` is recorded for audit).

### Security

- Reviewer credentials stay in environment variables; they never appear in
  `config.yaml`, task state, provider call records, artifacts or logs, and
  `doctor` prints presence rather than values.
- Budget/attempt evidence is append-only: no command resets or forges usage.

### Tests

- 227 tests, fully offline (fake providers, `httpx.MockTransport`, real tiny
  git repositories): 38 v0.2-A tests covering budget pre-flight, exact call
  accounting, format/transport separation, crash recovery, policy authority,
  fingerprints, snapshot/refresh-policy, CLI visibility and a fake-provider
  engine-level end-to-end loop, plus 22 audit-remediation tests covering the
  required crash/identity/policy matrix (persisted-result replay with zero
  calls, single application, immutable evidence, durable ids, policy-refresh
  evidence, retry labelling, fingerprint normalization, read-only legacy
  status/usage, budget regressions), plus 8 baseline-capture tests for the
  ignored-`.devrelay` smoke blocker.

## 0.1.0 - 2026-09-10

First public release: local AI coding orchestration with a task baseline, a
bounded review/fix loop and repository policy guards.

### Added

- Local AI coding orchestration pipeline (PLAN -> IMPLEMENT -> TEST -> REVIEW
  -> FIX loop -> FINAL_GATE -> DONE)
- Persistent task state machine with audited transitions and resume after
  process restart
- Official Codex CLI implementer (prompt streamed on stdin, no OpenAI API key
  required)
- Codex execution path that works with a ChatGPT-subscription-authenticated
  Codex CLI login
- Manual planner workflow (Task Packet `plan show` / `plan import`)
- Manual reviewer workflow (`review export` / `review import`)
- OpenAI-compatible reviewer provider for HTTP review endpoints
- Dirty-workspace task baselines: pre-existing tracked/untracked changes,
  staged and unstaged mixes, deletions, renames and binary files are captured
  without touching the user's real Git index
- Task-relative diffs: reviewers and reports see the baseline -> current
  workspace delta, never HEAD-relative attribution of pre-existing user work
- Durable baseline recovery: byte-faithful `tracked.patch` plus untracked
  blobs, reconstructed and SHA-verified after `git gc` prunes the baseline tree
- Git repository policy guards: HEAD, branch, tag, other local refs and real
  index staging are snapshotted before/after every provider run; violations
  BLOCK the task and are never auto-repaired
- Interrupted provider attempt recovery: persisted attempt lifecycle, post-run
  evidence for exceptions/timeouts/KeyboardInterrupt, fail-closed restart
  requiring explicit human acknowledgement
- Reviewer secret redaction (best-effort pattern based) applied at a single
  boundary shared by the remote and manual reviewer paths
- CLI commands: `init`, `doctor`, `start`, `status`, `plan`, `continue`,
  `diff`, `logs`, `review`, `final`, `unblock`, `version`
- Artifact/evidence generation per task (baseline, implementation reports,
  review requests/results, logs, policy snapshots, final report)
- Release/final gate with a human-readable `final/report.md` answering "why is
  this task considered complete?"

### Security

- No ChatGPT credential scraping, no browser/session automation, no
  undocumented authentication paths
- No OpenAI API key requirement for the Codex CLI execution path
- `shell=False` subprocess execution with argv lists and timeouts
- Git HEAD/branch/ref/index mutation guards with structured violations
- Fail-closed handling of conflicted or otherwise unverifiable Git index state
  (blocked before a provider run can start)
- Best-effort reviewer secret redaction (not a data-loss-prevention system)
- Push prevention remains **provider-limited / best-effort**: the local
  postcondition check cannot mathematically prove that no `git push` happened

### Known limitations

- One active task at a time (no concurrency)
- One implementer: the official Codex CLI
- No MCP server, ChatGPT plugin, web UI or VS Code extension yet
- No mathematical push prevention (see Security)
- Reviewer redaction is pattern-based best effort, not DLP
- Structured Codex event stream (`codex exec --json`) is not parsed yet
- Remaining P3 backlog tracked for a later release:
  - dead HEAD-relative helpers in `GitWorkspace` (unused since task-relative
    deltas landed)
  - `unblock` clears the raw `blocked_reason` field (the audit trail, policy
    snapshots and attempt evidence are retained)
  - files marked `assume-unchanged` / `skip-worktree` do not appear in
    `preexisting_dirty_files` metadata (the task delta itself stays correct)
  - `final/report.md` header line is rendered at the moment of approval
