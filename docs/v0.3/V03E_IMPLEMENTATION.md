# DevRelay v0.3-E — implementation report (mandatory fail-closed core)

Status: **IMPLEMENTED / OFFLINE TESTS PASS / ADVERSARIALLY REVIEWED (findings
remediated) / NOT ACCEPTED / NOT SMOKED**.

> **Authorization status — read this first.** The governance chain contains **no
> implementation authorization** for the mandatory core: `V03E_SPEC.md` §1,
> `V03_PLAN.md`, `V03E_ACCEPTANCE.md` and `V03E_G0_1_P7_PROOF.md` all state that
> implementation remains **NOT AUTHORIZED until a separately issued
> implementation authorization**, and no such record exists in
> `docs/v0.3/`. The work recorded below was therefore performed **without that
> authorization**: it is an **unauthorized draft implementation kept for review**,
> not the authorized v0.3-E implementation. It changes nothing in the acceptance
> chain — no acceptance row is marked COVERED, no stage status is advanced, and
> an implementation authorization (plus the independent review and real smoke it
> would unlock) is still required before any of this work can be treated as the
> authorized implementation, let alone accepted.

This report records what the v0.3-E implementation actually is, on branch
`v0.3-e-recovery-reconciliation`, against the design freeze in
`docs/v0.3/V03E_SPEC.md` and the design matrix `docs/v0.3/V03E_ACCEPTANCE.md`.

An **independent adversarial review** of this draft was performed after the first
pass and found one P0, three P1 and four P2 defects (all reproduced, all fixed);
the review record and its dispositions are in `docs/v0.3/V03E_REVIEW.md`. That
review is a review of the *unauthorized draft*, not an acceptance review.

It is **not** an acceptance record. Acceptance of v0.3-E requires the
independent review and the real-execution evidence that this round did not
produce (see §7). Nothing here may be read as a claim that v0.3-E is accepted,
released or independently reviewed.

The design freeze is unchanged: this round implements the **mandatory
fail-closed core** and keeps the optional `adopt_completed_turn` capability
disabled behind its unsatisfied platform proofs.

## 1. Scope delivered

| Item | State |
| --- | --- |
| Schema version 2 with a strict, no-migration reader and the frozen v1 (v0.3-D) contract | implemented |
| `RECOVERY_REQUIRED` run state and the `recover` action | implemented |
| `RecoveryEvidence` (27-field canonical digest) and `RecoveryRecord` models | implemented |
| Read-only ledger reconciliation (interval proof, exactly-one attribution) | implemented |
| Remote-turn correlation | **not wired** — the mandatory core is local-only (a session-history read is ledger-accounted, so it is not read-only here); it belongs to the gated adoption capability |
| `devrelay_reconcile_run` MCP tool (read-only, byte-identical, local evidence only) | implemented |
| `devrelay_resolve_recovery` MCP tool (one-shot write, `mark_unrecoverable` only) | implemented |
| `adopt_completed_turn` capability | **disabled** — `ADOPTION_CAPABILITY_ENABLED = False`, refused before any write |
| Retry / resume / resubmission / session adoption / replay of an interrupted turn | **absent by design** |
| Independent adversarial review of this draft (findings remediated) | done — `docs/v0.3/V03E_REVIEW.md`; not acceptance |
| Acceptance review, real recovery smoke, acceptance bookkeeping | **not done** |

## 2. Source changes

New modules:

- `src/devrelay/orchestration/ledger_reader.py` — `LedgerIdentity`, `LedgerScan`,
  `scan_ledger(devrelay_dir, identity, *, floor="")`, `newest_call_id`. Outcomes
  are exactly `exactly_one_match`, `multiple_matches`,
  `no_record_in_proven_interval` and `evidence_gap`. The floor is exclusive and
  must come from durable evidence; a missing sequence file, an allocated call id
  without a record (checked independently of the calls directory's presence), a
  record newer than the sequence, a torn record, a record whose `call_id`
  disagrees with its file name, two files claiming one call id, an inverted
  interval (floor newer than ceiling), an unparseable floor or a captured-route
  disagreement all degrade to `evidence_gap` instead of being guessed.
- `src/devrelay/orchestration/recovery.py` — `infer_recovery_reason`,
  `frozen_attempt`, `previous_floor`, `attempt_identity`, `match_remote_turn`
  (the §12.3 rules, kept for the gated adoption path and **not** called by the
  mandatory core), `coverage`, `build_evidence`, `build_record`,
  `reconcile_report` (with `checklist` and `blockers`), `resolution_names`, plus
  the disabled-capability constants `ADOPTION_CAPABILITY_ENABLED` /
  `ADOPTION_DISABLED_REASON` and the local-only marker
  `REMOTE_NOT_READ_REASON`.

Modified:

- `src/devrelay/orchestration/models.py` — `ORCHESTRATION_SCHEMA_VERSION = 2`,
  `LEGACY_SCHEMA_VERSION = 1`, `RunState.RECOVERY_REQUIRED`,
  `OrchestrationAction.RECOVER`, `RecoveryEvidence`, `RecoveryRecord`, the
  `recovery` / `recovery_reason` run fields, `summary()` recovery identifiers and
  `legal_next_actions()`.
- `src/devrelay/orchestration/invariants.py` — v2 schema gate, the frozen-v1
  recovery vetoes, the `RECOVERY_REQUIRED` shape rules, evidence ownership and
  digest verification, the coverage class, the attempt/recovery reason agreement,
  the single-recovery-attempt slot accounting and the `recover` edge map (`v1` has
  no recovery edges at all).
- `src/devrelay/orchestration/state_machine.py` — `after_enter_recovery`,
  `after_mark_unrecoverable`, `after_adoption`; interrupting prompts now name the
  v0.3-E recovery action.
- `src/devrelay/orchestration/service.py` — `reconcile_run(run_id)` and
  `resolve_recovery(run_id, resolution)`, `_local_evidence` (strict ledger scan
  only; no provider call), `_enter_and_resolve` (one atomic save that materializes
  the interrupted attempt and its resolution together), `_apply_resolution`. A v1
  run keeps its frozen behavior: the next model-bearing action materializes the
  legacy `BLOCKED` / `turn_interrupted` outcome exactly as v0.3-D did.
- `src/devrelay/errors.py` — `OrchestrationRecoveryRequiredError`,
  `OrchestrationRecoveryUnsupportedError`,
  `OrchestrationRecoveryAlreadyResolvedError`,
  `OrchestrationAdoptionDisabledError`.
- `src/devrelay/mcp/tools.py` — the two new tools, `_require_resolution`, the
  `devrelay_status` recovery capability block.
- `src/devrelay/mcp/server.py` — `MCP_SERVER_VERSION = "0.3.0-e"`, the recovery
  tool descriptions, the server instructions paragraph, tool registration.

## 3. The scheme as implemented

### 3.1 Schema version 2, no migration

`ORCHESTRATION_SCHEMA_VERSION` is now `2`; every run created by
`OrchestrationService.start_run` is written as v2. There is **no migration**: a
v1 document is read under the frozen v0.3-D contract and is never rewritten into
v2. A v1 document may not carry a recovery record, a recovery reason or the
`RECOVERY_REQUIRED` state, and the `recover` action does not exist for it. The
v0.3-D corpus (`tests/v03d_corpus.py`, `freeze_v03d`) keeps that contract under
test.

### 3.2 The interrupted-turn refusal

`_load_for_action` materializes a legacy v1 intent (unchanged v0.3-D behavior).
For a v2 run it mutates nothing: `RECOVERY_REQUIRED`, or a live
`in_flight_turn`, refuses every model-bearing phase action
(`devrelay_run_implementer`, `devrelay_run_reviewer`, `devrelay_decide_run`) with
`orchestration_recovery_required`. The refusal is byte-identical on disk and
submits nothing.

### 3.3 Evidence

`RecoveryEvidence` freezes 27 canonical JSON scalars (domain
`devrelay-evidence-v1`, then run identity, attempt identity, prompt digest and
length, the captured route, the ledger fields and the remote-match fields).
`values()` joins them with `"\n"`; `compute_digest()` is the SHA-256 of that
join. The digest is recomputed and verified on every read. `coverage` is
deliberately outside the digest. No prompt text, reply text, reasoning, token or
credential is ever stored.

### 3.4 Reconciliation (read-only)

`devrelay_reconcile_run` reports, without writing and **without any provider
call**: the run state and terminal flag, `recoverable`, `v1_frozen`, the recovery
reason, the stored recovery record (if any), the frozen attempt, the ledger
interval
(`outcome`/`floor`/`ceiling`/`interval_proven`/`candidate_count`/`gap_reason`),
the remote section (always a reasoned gap: the core is local-only), the adoption
capability (`available: false`, candidate, reason), the per-item **checklist**
(`pass`/`fail`/`unknown`, no partial credit) and the **blockers**, route drift,
budget counters, `legal_next_actions`, and
`submission.submitted_by_recovery: false`. It is byte-identical on disk: no
ledger record is appended and `opencode/sequence.json` is not rewritten. A
terminal run is refused locally (`orchestration_recovery_unsupported`) because
there is nothing left to recover; a frozen v1 document gets the report-only form
of `V03E_SPEC.md` §10.

### 3.5 Resolution (one-shot write)

`devrelay_resolve_recovery` accepts exactly `mark_unrecoverable`; any other
string is `mcp_invalid_argument`. `adopt_completed_turn` is refused with
`orchestration_adoption_disabled` **before any write**. The action performs no
provider call either: the evidence it freezes is the local ledger scan, and the
remote fields are frozen as an explicit gap (`REMOTE_NOT_READ_REASON`) — which is
exactly why `mark_unrecoverable` can never depend on the remote surface. On a
live v2 intent the service materializes the frozen attempt, the recovery reason,
the evidence and the resolution in **one** atomic save, with two transition
records written in that same save: `entry state -> RECOVERY_REQUIRED` and
`RECOVERY_REQUIRED -> BLOCKED` (`last_transition` is therefore the second one,
with `action: recover`, `source: external_planner` and the role of the frozen
attempt). The result is `BLOCKED` with `blocked_reason` equal to the recovery
reason
(`submission_uncertain`, `reply_pending` or `turn_interrupted`), the attempt
booked once in its role history, and no further action legal. A second resolution
is `orchestration_recovery_already_resolved`. A v1 run is
`orchestration_recovery_unsupported`.

### 3.6 Tool surface

19 MCP tools total. `devrelay_reconcile_run` is annotated `read_only`;
`devrelay_resolve_recovery` is `side_effecting`. `devrelay_status` reports
`recovery: {available: true, resolutions: [...], adoption_enabled: false,
adoption_reason: ..., submits_model_requests: false, retries: false,
resumes: false, max_recovery_attempts: 1}`.

### 3.7 Local integrity

The spec's per-surface execution lock (`V03E_SPEC.md` §12.6) is provided by the
MCP surface, not by the service: `McpTools` owns `self._execution_lock`
(`threading.RLock`, `src/devrelay/mcp/tools.py`) and every tool body runs inside
it, so a reconcile and a resolve on one surface cannot interleave, and the
recovery action holds the lock for its whole duration. A caller that uses
`OrchestrationService` directly gets no such lock; multi-process or
multi-surface coordination is explicitly unsupported (as the spec states).

## 4. Why adoption stays disabled

`adopt_completed_turn` requires the platform proofs that have not passed:
G0.5/P6 (identity and ownership veto bound) together with the remote enabling
proofs P1/P2/P3/P8. G0.1/P7, G0.2 and G0.3 passed; G0.4 remains an authoritative
FAIL with P4 UNPROVEN. The implementation therefore ships the option **off**:
the model, the record shape and the transition edges exist and are tested, but
`ADOPTION_CAPABILITY_ENABLED` is `False`, the MCP surface refuses the resolution
before writing, and no code path can adopt a completed turn. This is the
fail-closed outcome the design freeze mandates; enabling it requires new proofs
and a new authorization, not a code flip.

## 5. Tests

New offline suites (no real model call, deterministic OpenCode stub):

| File | Tests | Covers |
| --- | --- | --- |
| `tests/test_v03e_recovery.py` | 15 | end-to-end crash → refusal → reconcile → resolve → restart matrix, write-once, adoption refusal, frozen v1 behavior, reviewer-role crash; **byte-identical `.devrelay` tree** around read-only reconcile and the accounting subtree around resolve; terminal-run local refusal |
| `tests/test_v03e_attribution.py` | 8 | honest-report rules (gap ⇒ reasoned `gap_reason`, `interval_proven` ⇒ floor and ceiling, `call_id` ⇒ `exactly_one_match`), first-turn unproven floor, reviewer-crash proven interval, unreadable ledger surface, quiet run |
| `tests/test_v03e_models.py` | 13 | 27-field canonical set, digest construction and sensitivity, coverage exclusion, record shape rules, legal actions |
| `tests/test_v03e_ledger.py` | 17 | exactly-one attribution, floor/ceiling proofs, missing sequence, allocated-but-absent record (also with the calls directory absent), newer-than-sequence record, torn record, route disagreement, multiple matches, duplicate numeric claim, record/file call-id disagreement, inverted floor |
| `tests/test_v03e_invariants.py` | 17 | v1 vetoes, unknown schema version, `RECOVERY_REQUIRED` shape, unresolved record outside recovery, blocked-reason agreement, slot accounting, evidence ownership and digest tamper, coverage class, attempt/recovery reason agreement |

The v0.3-D suites were migrated to the v2 contract without changing their
subject: the tool inventory is 19 everywhere, the version mutation anchors read
`0.3.0-e`, and the v0.3-D corpus writes exactly the v0.3-D document via
`freeze_v03d` so the frozen-v1 read path stays under test.

Verification command and result:

```
python -m pytest -q
```

Result: **all tests pass** — 1236 collected, 0 failed (pytest exit 0).

Two environment notes for reproducing that result (neither is a v0.3-E
regression; both were observed on this machine):

- Run the suite with a fresh `TEMP`/`TMP`/`TMPDIR` outside the repository.
  `tests/test_baseline_ignored_self.py::test_real_index_bytes_unchanged_and_temp_index_cleaned`
  asserts that no `devrelay-index-*` directory is left in `%TEMP%`, so a shared
  temp root that another concurrent run is using at that instant can fail it
  (`docs/BACKLOG.md` §9, pre-existing hygiene item). A temp root *inside*
  `D:\DevRelay` additionally breaks
  `tests/test_git_workspace.py::test_non_repo_directory_errors`, because a
  "non-repo directory" then sits inside a git work tree.
- With an isolated temp root outside the repository the suite is green
  (measured: 66 files / 1236 tests, pytest exit 0).

## 6. Recorded verification

- `python -m pytest -q tests/test_v03e_*.py` — 70 passed (recovery 15,
  attribution 8, models 13, ledger 17, invariants 17).
- `python -m pytest -q` (full suite) — 1236 tests, 0 failed, exit code 0.
- Full suite re-run on the committed tree with an isolated `TEMP`/`TMP`/`TMPDIR`
  outside the repository — 66 files / 1236 tests, exit code 0.

## 7. What this report does not claim

- No implementation authorization (see the blockquote at the top of this file:
  this is an unauthorized draft, and the authorization is still a prerequisite).
- No independent *acceptance* review. An adversarial review of the draft was
  performed and its findings were remediated (`docs/v0.3/V03E_REVIEW.md`), but it
  was performed by a review-only subagent on the same tree — it is not the
  separately authorized review that acceptance would require, and it marks no
  acceptance row.
- No real crash-and-recover execution against a real OpenCode server; all
  evidence above is offline and deterministic.
- No acceptance row of `docs/v0.3/V03E_ACCEPTANCE.md` is marked COVERED by this
  report; that matrix remains the acceptance authority's document.
- No tag, release, push or merge; package version stays `0.1.0` and the
  supported public release stays `v0.1.0`.

