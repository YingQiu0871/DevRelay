# DevRelay v0.2 specification

v0.2 hardens the local orchestration core into a long-running, budget-aware
pipeline. **Only stage A is implemented in this branch.**

| Stage | Scope | Status |
| --- | --- | --- |
| **A** | Automatic review loop (budget, review lifecycle, reviewer evidence, CLI visibility) | **CURRENT — this branch** |
| B | Project profiles | NOT STARTED |
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

## B–E (not started)

* **B — Project profiles:** reusable per-project policy profiles, profile
  inheritance, project-specific test/scope defaults.
* **C — Structured Codex runtime:** parse `codex exec --json` events, capture
  structured tool/command events and per-run metadata instead of raw stdout.
* **D — General release pipeline:** generalize the v0.1 bootstrap guards
  (tag validation beyond `v0.1.0`), artifact provenance verification, release
  workflow automation for arbitrary versions.
* **E — RC / release:** v0.2 release-candidate audit cycle and publication.
