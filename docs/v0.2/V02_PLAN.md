# DevRelay v0.2 plan

## Stage status

| Stage | Description | Status |
| --- | --- | --- |
| **A** | Automatic review loop (budget, review lifecycle, reviewer evidence, CLI visibility) | **CURRENT — candidate, not reviewed-closed** |
| **A.1** | Audit remediation of the `fe4b044` candidate (P1-01, P2-01..03, P3-01..06) | **CURRENT — awaiting closure audit** |
| B | Project profiles | **NOT STARTED** |
| C | Structured Codex runtime | **NOT STARTED** |
| D | General release pipeline | **NOT STARTED** |
| E | v0.2 RC / release | **NOT STARTED** |

This document does not claim any stage beyond A/A.1. Stage A is *not* DONE: the
independent audit returned `REQUEST_CHANGES`, and this branch only implements the
remediation that must be closure-audited before A can be closed.

## v0.2-A work breakdown (all completed in this branch)

1. `docs/v0.2/*` — spec, acceptance criteria, plan (this document).
2. **Models** — `ProviderCallRecord`, `ReviewAttempt`, usage summary, finding
   fingerprints, task-scoped policy source; `state_schema_version` bumped with
   backward-compatible defaults.
3. **Config** — `budget:` section, `review.transport_retries`,
   `review.max_response_chars`, `pipeline.max_same_finding_cycles`; bundled
   profile and repository profile updated.
4. **Budget policy** — `pipeline/budget.py`: usage computation from persisted
   call records (never inferred from iteration counters), pre-flight checks,
   `provider_budget_exhausted` blocking.
5. **Review lifecycle** — `pipeline/review_lifecycle.py`: review attempt
   begin/finalize, in-flight crash marker, per-call evidence artifacts.
6. **Reviewer provider** — `providers/openai_compatible.py`: per-attempt call
   records via a call sink, transport vs format failure separation,
   `transport_retries` (default 0), response size cap, sanitized HTTP error
   bodies, endpoint host/model evidence.
7. **Engine integration** — budget pre-flight before implementer and reviewer
   invocations, reviewer attempt persistence, fingerprint bookkeeping,
   `review_stalled` guard, task-scoped policy resolution.
8. **CLI** — `status` (budget + review), new read-only `usage`, `doctor`
   reviewer env presence check, `unblock` refresh-policy acknowledgement.
9. **Tests** — acceptance matrix A1–A20, S1–S8, plus a full engine-level fake
   E2E (two implementer calls, two reviewer calls, exact 4 total).
10. **Docs** — README “Automatic Review Loop”, CHANGELOG `Unreleased`.

## Audit remediation work breakdown (v0.2-A.1, all completed in this branch)

1. **P1-01 review result lifecycle** — `ReviewAttempt` gains
   `result_persisted`/`result_hash`/`result_applied`/`applied_at`/`applied_state`;
   `recover_pending_review()` replays a persisted result with zero external calls;
   `_needs_application_completion()` finishes a missing terminal transition only
   with proof that nothing happened since.
2. **Idempotent application** — `_apply_review` performs the whole semantic
   mutation in one atomic state write, guarded by a stable result identity plus
   an `AppliedReviewRecord` marker; content equality alone is not proof.
3. **P2-01/P2-02 durable identity** — `TaskRun.next_provider_call_sequence`,
   `next_provider_attempt_sequence`, `next_review_attempt_sequence`; call ids
   `DR-0001-C0007`, implementer attempts `DR-0001-A0002`, review attempts
   `DR-0001-R0002`; the reviewer no longer owns a process-local counter and the
   implementer attempt number is no longer derived from `implementation_passes`.
4. **Relations** — `ProviderCallRecord.parent_attempt_id`,
   `ProviderCallRecord.review_number`, `ProviderAttempt.call_ids`.
5. **Immutable evidence** — `policy/calls/<call-id>.json`,
   `policy/attempts/<attempt-id>.json`, `policy/runs/<attempt-id>-*.json`,
   `logs/<attempt-id>.*`, `reviews/review-NN-<attempt-id>-meta.json`; the old
   `NN` names stay as documented "latest view" convenience copies.
6. **P2-03 policy refresh evidence** — `PolicyRefreshRecord` +
   `policy/policy-refresh-NN-{before,after}.yaml` + `-NN.json`; usage is never
   reset, deleted or renumbered.
7. **P3-01..06** — cap wording, retry phase labelling, fingerprint path
   normalization, eager `policy_source`, AUD-09 audit note, linear-history proof.
8. **State schema 4** with v0.1 compatibility and a `finish_only` path for
   private `fe4b044` state.
9. **Tests** — 20 new tests in `tests/test_v02a_audit_remediation.py` covering the
   required A–P matrix and budget regressions 1–5.

## Deliberately deferred (recorded, not silently dropped)

* Automatic stagnation stop is implemented as an opt-in guard with default
  `max_same_finding_cycles: 0` (disabled); fingerprints and seen-counts are
  always persisted so v0.2-B/C can add smarter cross-task analysis. The
  disabled default is deliberate: it keeps v0.1 loop semantics (a repeated
  blocking finding still ends at `max_fix_iterations`) and avoids changing the
  meaning of existing tasks. Enabling the guard is a policy decision and, for a
  running task, requires `unblock --refresh-policy`.
* Transport retries default to 0; configurable, but deliberately not enabled by
  default so a flaky network cannot silently spend reviewer calls.
* Structured Codex event parsing (`codex exec --json`) stays in stage C.
* Generalizing the release workflow tag guard and adding general artifact
  provenance stays in stage D.
* Real Codex and real reviewer API smoke tests are **not** part of stage A;
  they follow the independent review of this candidate.
* **AUD-09** (an `unblock` clears `blocked_code`/`blocked_reason` instead of
  moving them into a durable block history) stays open as a backlog item. This
  remediation only records the cleared block verbatim in the audit trail; it does
  not restructure block bookkeeping.
* **P3-06 prompt compaction**: the review prompt is proven linear and bounded
  under policy (`max_reviewer_calls` x one summary line per round), so summary
  models / LLM compaction are explicitly deferred.
* **Streaming reviewer HTTP** (a true network-level response byte limit) stays a
  later-stage item; v0.2-A keeps the parsing/persistence cap and documents it
  honestly.

## Verification order used in this stage

1. `python -m pytest` (full suite, offline).
2. CLI smoke on temporary repositories with fake providers.
3. `git diff` review of the branch before committing.
4. One additional local commit on `v0.2-a-auto-review`
   (`Fix v0.2-A audit findings`); `fe4b044` is **not** squashed so the reviewer
   can see base -> remediation. **No push, no merge, no tag, no release.**
