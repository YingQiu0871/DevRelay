# DevRelay v0.2 specification

v0.2 hardens the local orchestration core into a long-running, budget-aware
pipeline. **Only stage A is implemented in this branch.**

| Stage | Scope | Status |
| --- | --- | --- |
| **A** | Automatic review loop (budget, review lifecycle, reviewer evidence, CLI visibility) | **CURRENT — candidate, not reviewed-closed** |
| **A.1** | Audit remediation of the `fe4b044` candidate (P1-01, P2-01..03, P3-01..06) | **CURRENT — awaiting closure audit** |
| B | Project profiles | **CURRENT - candidate, not reviewed-closed (v0.2-B)** |
| C | Structured Codex runtime (`codex exec --json` parsing, structured events) | NOT STARTED |
| D | General release pipeline (generalized tag validation, provenance, release automation) | NOT STARTED |
| E | RC / release process for v0.2 | NOT STARTED |

Nothing below stage B/E may be claimed as implemented until it lands on `main`
with its own tests.

## A. Automatic review loop (v0.2-A)

Goal: the pipeline can run

```
Codex -> TEST -> automatic reviewer -> blocking finding -> Codex FIX
      -> TEST -> reviewer -> PASS -> FINAL_GATE_REQUIRED
```

without the user copy-pasting review findings between agents, while every real
external model call is counted, bounded and auditable.

Requirements:

1. **No parallel state machine.** The existing `PipelineState` machine,
   `DevRelayEngine`, `PipelinePolicy`, `ReviewResult`/`Finding` models remain
   the single source of truth. No `AutoReviewEngine`, no second loop.
2. **Execution budget.** New `budget:` config with `max_implementer_calls`,
   `max_reviewer_calls`, `max_total_provider_calls` (defaults 4 / 4 / 8).
   Limits are enforced *before* any provider invocation; exceeding them is
   `BLOCKED` with `blocked_code: provider_budget_exhausted`.
3. **Every external call is a persisted record.** `ProviderCallRecord` captures
   provider kind/name, phase, attempt/iteration numbers, timing, success,
   error type, external call count, model and endpoint host — never a token,
   API key, credential or full URL.
4. **Call accounting is conservative.** A reviewer format retry is a second
   external call and consumes budget twice. A request that may have been sent
   is counted as attempted. Budget is never silently reset.
5. **Review attempt lifecycle.** Each automatic review is a persisted
   `ReviewAttempt` (review number, format attempts, transport attempts, status,
   result, error, calls consumed). An in-flight marker is written before the
   HTTP request; after a hard crash, `continue` must fail closed
   (`BLOCKED`, `interrupted_reviewer_attempt`) instead of re-requesting a
   reviewer whose previous call may already have been billed. The same applies
   to a round that was started but never finalized (crash after the response
   arrived): it is detected from the persisted attempt, `unblock` acknowledges
   it by closing it as `INTERRUPTED` (evidence preserved), and a re-entered
   round receives a unique attempt identity.
6. **Failure separation.** Transport failure (HTTP/network) and format failure
   (HTTP 200 without schema-valid JSON) are distinct. Format retries use
   `review.retries`; transport retries use a separate `review.transport_retries`
   (default 0) so a network problem never silently spends reviewer calls.
7. **Reviewer evidence.** Each review writes semantic result and execution
   metadata separately (`review-NN-result.json`, `review-NN-meta.json`, plus
   per-call metadata when a format retry happened).
8. **Policy authority.** `blocking_severities` (policy), not the reviewer's
   `decision` string, decides FIX vs PASS.
9. **Auto-fix handoff.** The FIX prompt contains the blocking findings with id,
   severity, title, description, files, evidence and recommendation, plus the
   Task Packet and scope constraints — no repository dump.
10. **Finding fingerprints.** Deterministic fingerprints (severity + normalized
    title/files/description, excluding the per-round finding id) with a
    persisted seen-count; repeated identical blockers can be stopped as
    `review_stalled` via `pipeline.max_same_finding_cycles`.
11. **Task-scoped policy.** The execution policy for a task (budget, blocking
    severities, retries, test policy, git policy) is the one snapshotted at task
    start. Editing the workspace config during a task does not silently change
    it; an explicit, audited refresh is required.
12. **Manual review stays first-class.** `review export` / `review import` /
    `final export` / `final approve` keep working, need no reviewer API
    configuration, and consume **zero** external reviewer calls.
13. **Final gate stays manual.** Even with tests PASS, review PASS and budget
    remaining, the pipeline stops at `FINAL_GATE_REQUIRED`.
14. **Secrets.** Reviewer-facing material is sanitized at one boundary; HTTP
    error bodies, model output and exceptions are sanitized before they reach
    state, artifacts or logs. Durable baseline artifacts remain byte-exact and
    are never redacted.

## A.1 Audit remediation (v0.2-A candidate, unresolved until closure audit)

An independent audit of the `fe4b044` candidate returned `REQUEST_CHANGES` with
one P1, three P2 and six P3 findings. This section specifies the remediation. It
does **not** promote stage A to DONE: A remains CURRENT / CANDIDATE.

### A.1.1 Review result lifecycle (P1-01)

Three distinct, durable milestones replace the implicit "finalize then hope":

| Milestone | Evidence | Meaning |
| --- | --- | --- |
| CALL COMPLETED | `ReviewAttempt.status == COMPLETED` | a call finished |
| RESULT PERSISTED | `result_persisted`, `result_hash` | sanitized, schema-valid, **authoritative** result |
| RESULT APPLIED | `result_applied`, `applied_at`, `applied_state` | reached `review_history` exactly once |

Restart rules, in this order:

1. **Uncertain external call** (`review_call_in_flight`, or an attempt that never
   finalized, or an attempt with no persisted result) -> fail closed
   (`interrupted_reviewer_attempt`). DevRelay never invents a result.
2. **Known completed result** (attempt `COMPLETED` + persisted result, not yet
   applied) -> replay `_apply_review` **locally with zero external calls**, and
   enter the state the policy dictates (blocking -> `FIX_REQUIRED`, policy PASS
   -> `FINAL_GATE_REQUIRED`, `BLOCKED` -> policy-defined BLOCKED).
3. **Applied but the terminal transition never landed** -> complete the
   transition locally, but only with proof that nothing happened since
   (same round, same fix/implementation counters). A task that ran a fix and
   came back to `REVIEWING` starts a normal new round.

### A.1.2 Idempotent application (P1-01, §3)

The whole semantic application of one result - history append, seen counters,
findings, applied marker, terminal state, audit note - lands in **one atomic
`state.json` write**, so a crash lands either before it (result is replayed) or
after it (identity match -> no-op). Replays never duplicate history, counters,
transitions or audit events and never cost an external call. Whether a result is
already applied is decided by durable identity:
`sha256` of the canonical, fingerprint-stripped result, recorded as an
`AppliedReviewRecord` **plus** the attempt's own `result_applied` marker - never
by a bare `if review_history:` check. Content equality alone is explicitly *not*
proof of application, because two rounds may legitimately return identical
reviews (that is the repeated-blocker case the stagnation guard exists for).

### A.1.3 Durable identity (P2-01, P2-02)

Identities come from persisted, task-scoped, monotonic sequences - never from
process-local counters or success counters:

| Object | Identity | Allocated |
| --- | --- | --- |
| Provider call | `DR-0001-C0007` | persisted *before* the invocation |
| Implementer attempt | `DR-0001-A0002` | persisted before the invocation |
| Review attempt | `DR-0001-R0002` | persisted before the first call |

`TaskRun.next_provider_call_sequence`, `next_provider_attempt_sequence` and
`next_review_attempt_sequence` are never decremented, never reused after a
failure, and never reset by `unblock` or a policy refresh. `review_number`
(the semantic round) stays distinct from the review *attempt* identity: one
round may have several attempts. Calls link back through
`ProviderCallRecord.parent_attempt_id` and `ReviewAttempt.call_ids` /
`ProviderAttempt.call_ids`.

### A.1.4 Immutable evidence (P2-01, P2-02)

| Artifact | Kind |
| --- | --- |
| `policy/calls/<call-id>.json` | immutable per-call evidence |
| `policy/attempts/<attempt-id>.json` | immutable per-attempt evidence |
| `policy/runs/<attempt-id>-{pre,post,violations}.json` | immutable per-run snapshots |
| `logs/<attempt-id>.{stdout,stderr}.log` | immutable per-attempt logs |
| `reviews/review-NN-<attempt-id>-meta.json` | immutable per-review-attempt meta |
| `policy/attempt-NN.json`, `pre-run-NN.json`, `post-run-NN.json`, `violations-NN.json`, `logs/codex-NN.*`, `reviews/review-NN-meta.json`, `reviews/review-NN-call-MM-meta.json` | mutable "latest view" convenience copies (documented as such) |

A retry may rewrite a convenience copy; it can never overwrite another call's or
another attempt's keyed evidence.

### A.1.5 Policy refresh evidence (P2-03)

`unblock --refresh-policy --reason ...` preserves the previous policy durably:
`policy/policy-refresh-NN-before.yaml`, `-after.yaml` and `-NN.json`
(`PolicyRefreshRecord`: refresh id, timestamp, actor, reason, before/after
source, before/after SHA-256, evidence attempt), appended to
`TaskRun.policy_refreshes`. Refresh semantics are unchanged: usage is never
reset, deleted or renumbered; a new (max) budget applies to already-spent calls
exactly as it did before, and each refresh is audited.

**Evidence attempt vs. generation.** The `NN` in `policy-refresh-NN-*` is an
*evidence attempt* number, deliberately distinct from the policy generation:
every attempt that starts writing evidence consumes a unique, never-reused
number allocated from both the persisted records and the on-disk artifacts
(`max(seen) + 1`, gaps tolerated), and evidence files are created with a
create-new writer that refuses to replace an existing path. A failed attempt
therefore keeps its artifacts - attempt 01 may remain on disk unreferenced by
state while the successful retry is attempt 02 and still advances generation
1 -> 2. An on-disk artifact is evidence of an *attempt* only; a refresh counts
as authoritatively applied when the persisted task references that record and
its `policy_provenance.generation`, `policy_config_sha256` and provenance
describe the applied generation. Orphan evidence is never deleted, never
overwritten and never interpreted as applied.

### A.1.6 P3 fixes

* **P3-01** - `max_response_chars` is documented (config, README, error message)
  as a *parsing/persistence* cap: the HTTP client may buffer the body first, so
  it is not a network-level memory limit. Behaviour is unchanged: oversized
  content is never parsed, never truncated-and-guessed, never persisted.
* **P3-02** - retry phases follow the *cause* of the retry: a mixed
  format -> transport -> format sequence is labelled `REVIEW`,
  `REVIEW_FORMAT_RETRY`, `REVIEW_TRANSPORT_RETRY`, `REVIEW_FORMAT_RETRY`.
* **P3-03** - finding fingerprints normalize path separators (`\` -> `/`) and
  sort files, but never case-fold paths (POSIX repositories may hold both
  `A.py` and `a.py`).
* **P3-04** - `policy_source` is persisted as `snapshot` when the task is
  created; `status` and `usage` resolve it read-only and never rewrite state
  (legacy tasks keep showing `live-fallback` without being modified).
* **P3-05** - AUD-09 remains open as a backlog item. `unblock` still clears
  `blocked_code`/`blocked_reason`, but now records the cleared block verbatim in
  the audit trail and deletes no evidence (calls, attempts, review attempts,
  policy refreshes all survive).
* **P3-06** - review-history growth is linear and non-nested: the reviewer
  prompt renders one summary line per previous round and never re-renders
  previous findings. Under the default policy a task has at most
  `budget.max_reviewer_calls` (4) applied rounds, so the prompt is bounded by
  roughly `4 x (summary + one line)`; exceeding that requires an explicit human
  `unblock --refresh-policy`. Prompt compaction is therefore recorded as a
  deferred P3 enhancement, not a defect.

### A.1.7 State schema

`state_schema_version` is bumped to **4** (durable sequences, review-result
lifecycle, applied markers, policy refreshes). Public v0.1 task state
(`state_schema_version: 2`) keeps loading and working: new fields default
safely, and `status`/`usage` never rewrite it. States written by the unreleased
`fe4b044` candidate are handled through the identity-based `finish_only` path.

## B. Project profiles (v0.2-B)

Implemented in this branch; see `docs/v0.2/V02B_ACCEPTANCE.md` for the acceptance
criteria and evidence.

1. **Three-layer policy chain.** packaged defaults
   (`src/devrelay/profiles/default.yaml`) < `.devrelay/profiles/<name>.yaml`
   (selector order, later wins) < policy overrides in `.devrelay/config.yaml`.
2. **Wiring and policy are separate types.** `WiringConfig`
   (`review.provider`, `codex.*`) is live and never frozen; `PolicyDocument`
   (`pipeline`, `budget`, `review` policy knobs, `tests`, `scope`, `baseline`,
   `git`) is resolved once and frozen per task. `PipelinePolicy` accepts only a
   `PolicyDocument`.
3. **Profile documents are policy only.** `review.provider`, `codex.*`,
   `git.*`, `profiles` and unknown keys are rejected. Limits: <= 8 profiles,
   <= 1 MiB per file, `safe_load`, no `extends`, no user/global directory, no CLI
   override, one name grammar, strict containment.
4. **Frozen policy integrity.** The snapshot is hashed over its exact on-disk
   bytes and verified before parsing; missing/invalid/hash-mismatched snapshots
   fail closed with `policy_snapshot_*` codes instead of falling back to live
   wiring or workspace defaults. Genuine pre-snapshot tasks keep the historical
   explicit live-policy path.
5. **Explicit recovery.** `devrelay unblock --reason "..." --refresh-policy`
   resolves the live chain first, preserves previous bytes only when readable,
   records provenance and a new generation, and never touches usage or history.
   Replacing an intact policy requires `--force`.
6. **Read-only commands stay independent.** `status`/`usage`/`diff`/`logs` never
   validate live policy, never resolve profiles and never rewrite state; raw
   profile diagnostics (`profile list/show/validate`) work with a broken
   selector, and `config show --resolved` is the only authoritative resolver.
7. **State schema 5** persists snapshot path, digest and provenance; older states
   (2-4) still load, `> 5` produces a dedicated `state_schema_too_new`
   diagnostic, and the first *mutating* write of an older task keeps its exact
   previous `state.json` bytes in a one-time `state.v<old>.json.bak` before
   writing the upgraded document (the backup is never overwritten, a backup
   failure aborts the write, and read-only commands never migrate).

## C–E (not started)

* **C — Structured Codex runtime:** parse `codex exec --json` events, capture
  structured tool/command events and per-run metadata instead of raw stdout.
* **D — General release pipeline:** generalize the v0.1 bootstrap guards
  (tag validation beyond `v0.1.0`), artifact provenance verification, release
  workflow automation for arbitrary versions.
* **E — RC / release:** v0.2 release-candidate audit cycle and publication.
