# DevRelay v0.3-E — implementation report (mandatory fail-closed core)

Status: **IMPLEMENTED / OFFLINE TESTS PASS / NOT ACCEPTED / NOT SMOKED**.

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
| Read-only remote-turn matching (no request is ever submitted) | implemented |
| `devrelay_reconcile_run` MCP tool (read-only, zero mutation) | implemented |
| `devrelay_resolve_recovery` MCP tool (one-shot write, `mark_unrecoverable` only) | implemented |
| `adopt_completed_turn` capability | **disabled** — `ADOPTION_CAPABILITY_ENABLED = False`, refused before any write |
| Retry / resume / resubmission / session adoption / replay of an interrupted turn | **absent by design** |
| Independent review, real recovery smoke, acceptance bookkeeping | **not done** |

## 2. Source changes

New modules:

- `src/devrelay/orchestration/ledger_reader.py` — `LedgerIdentity`, `LedgerScan`,
  `scan_ledger(devrelay_dir, identity, *, floor="")`, `newest_call_id`. Outcomes
  are exactly `exactly_one_match`, `multiple_matches`,
  `no_record_in_proven_interval` and `evidence_gap`. The floor is exclusive and
  must come from durable evidence; a missing sequence file, an allocated call id
  without a record, a record newer than the sequence, a torn record, an
  unparseable floor or a captured-route disagreement all degrade to
  `evidence_gap` instead of being guessed.
- `src/devrelay/orchestration/recovery.py` — `infer_recovery_reason`,
  `frozen_attempt`, `previous_floor`, `attempt_identity`, `match_remote_turn`,
  `coverage`, `build_evidence`, `build_record`, `reconcile_report`,
  `resolution_names`, plus the disabled-capability constants
  `ADOPTION_CAPABILITY_ENABLED` / `ADOPTION_DISABLED_REASON`.

Modified:

- `src/devrelay/orchestration/models.py` — `ORCHESTRATION_SCHEMA_VERSION = 2`,
  `LEGACY_SCHEMA_VERSION = 1`, `RunState.RECOVERY_REQUIRED`,
  `OrchestrationAction.RECOVER`, `RecoveryEvidence`, `RecoveryRecord`, the
  `recovery` / `recovery_reason` run fields, `summary()` recovery identifiers and
  `legal_next_actions()`.
- `src/devrelay/orchestration/invariants.py` — v2 schema gate, the frozen-v1
  recovery vetoes, the `RECOVERY_REQUIRED` shape rules, evidence ownership and
  digest verification, the single-recovery-attempt slot accounting and the
  `recover` edge map (`v1` has no recovery edges at all).
- `src/devrelay/orchestration/state_machine.py` — `after_enter_recovery`,
  `after_mark_unrecoverable`, `after_adoption`; interrupting prompts now name the
  v0.3-E recovery action.
- `src/devrelay/orchestration/service.py` — `reconcile_run(run_id)` and
  `resolve_recovery(run_id, resolution)`, `_collect_recovery_evidence`,
  `_enter_and_resolve` (one atomic save that materializes the interrupted attempt
  and its resolution together), `_apply_resolution`. A v1 run keeps its frozen
  behavior: the next model-bearing action materializes the legacy
  `BLOCKED` / `turn_interrupted` outcome exactly as v0.3-D did.
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

`devrelay_reconcile_run` reports, without writing: the run state and terminal
flag, `recoverable`, `v1_frozen`, the recovery reason, the stored recovery record
(if any), the frozen attempt, the ledger interval
(`outcome`/`floor`/`ceiling`/`interval_proven`/`candidate_count`/`gap_reason`),
the remote match, the adoption capability (`available: false`, candidate,
reason), route drift, budget counters, `legal_next_actions`, and
`submission.submitted_by_recovery: false`. It performs no POST and changes no
byte on disk.

### 3.5 Resolution (one-shot write)

`devrelay_resolve_recovery` accepts exactly `mark_unrecoverable`; any other
string is `mcp_invalid_argument`. `adopt_completed_turn` is refused with
`orchestration_adoption_disabled` **before any write**. On a live v2 intent the
service materializes the frozen attempt, the recovery reason, the evidence and
the resolution in **one** atomic save, with a `recover` transition record
(`previous_state` = the entry state, `next_state` = `BLOCKED`). The result is
`BLOCKED` with `blocked_reason` equal to the recovery reason
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
| `tests/test_v03e_recovery.py` | 15 | end-to-end crash → refusal → reconcile → resolve → restart matrix, write-once, adoption refusal, frozen v1 behavior, reviewer-role crash |
| `tests/test_v03e_models.py` | 13 | 27-field canonical set, digest construction and sensitivity, coverage exclusion, record shape rules, legal actions |
| `tests/test_v03e_ledger.py` | 13 | exactly-one attribution, floor/ceiling proofs, missing sequence, allocated-but-absent record, newer-than-sequence record, torn record, route disagreement, multiple matches |
| `tests/test_v03e_invariants.py` | 15 | v1 vetoes, unknown schema version, `RECOVERY_REQUIRED` shape, unresolved record outside recovery, blocked-reason agreement, slot accounting, evidence ownership and digest tamper |

The v0.3-D suites were migrated to the v2 contract without changing their
subject: the tool inventory is 19 everywhere, the version mutation anchors read
`0.3.0-e`, and the v0.3-D corpus writes exactly the v0.3-D document via
`freeze_v03d` so the frozen-v1 read path stays under test.

Verification command and result:

```
python -m pytest -q
```

Result: **all tests pass** — 1222 collected, 0 failed (pytest exit 0).

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
  (measured: 66 files / 1222 tests, pytest exit 0).

## 6. Recorded verification

- `python -m pytest -q tests/test_v03e_*.py` — 56 passed.
- `python -m pytest -q` (full suite) — 1222 tests, 0 failed, exit code 0.
- Full suite re-run on the committed tree with an isolated `TEMP`/`TMP`/`TMPDIR`
  outside the repository — 66 files / 1222 tests, exit code 0 (467 s).

## 7. What this report does not claim

- No implementation authorization (see the blockquote at the top of this file:
  this is an unauthorized draft, and the authorization is still a prerequisite).
- No independent review of this implementation.
- No real crash-and-recover execution against a real OpenCode server; all
  evidence above is offline and deterministic.
- No acceptance row of `docs/v0.3/V03E_ACCEPTANCE.md` is marked COVERED by this
  report; that matrix remains the acceptance authority's document.
- No tag, release, push or merge; package version stays `0.1.0` and the
  supported public release stays `v0.1.0`.

