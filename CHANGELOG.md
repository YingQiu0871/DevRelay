# Changelog

All notable changes to DevRelay are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased - v0.2-A candidate (independent review pending)

Automatic review loop with an enforced execution budget. **Not released**: the
package version stays `0.1.0`, nothing is pushed or published, and the
behaviour below was validated with fake providers only (no real Codex
invocation and no real reviewer endpoint were used).

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
  opt-in; every retry is a counted call) and a `max_response_chars` hard cap -
  oversized answers are refused with an explicit error, never silently cut.
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

- 197 tests, fully offline (fake providers, `httpx.MockTransport`, real tiny
  git repositories). 38 of them are new v0.2-A tests covering budget
  pre-flight, exact call accounting, format/transport separation, crash
  recovery, policy authority, fingerprints, snapshot/refresh-policy, CLI
  visibility and a fake-provider engine-level end-to-end loop.

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
