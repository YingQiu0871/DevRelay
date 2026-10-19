# DevRelay v0.3-E — independent adversarial review record (unauthorized draft)

Status: **REVIEW PERFORMED / FINDINGS RAISED / REMEDIATED / NOT ACCEPTANCE**.

> This record documents an **adversarial review of the unauthorized draft
> implementation** described in `docs/v0.3/V03E_IMPLEMENTATION.md`. It is not an
> acceptance record and it does not create the implementation authorization the
> governance chain still requires (`V03E_SPEC.md` §1, `V03_PLAN.md`,
> `V03E_ACCEPTANCE.md`). No acceptance row is marked COVERED, no stage status is
> advanced, and adoption remains disabled.

## 1. Scope and method

| Item | Value |
| --- | --- |
| Reviewed tree | branch `v0.3-e-recovery-reconciliation`, commits `b10fcea` (implementation), `d035d03` (environment notes), plus the disclosure commit `54ec97f`; the remediation is commit `a7fe160` |
| Review artifacts | `docs/v0.3/V03E_SPEC.md`, `docs/v0.3/V03E_ACCEPTANCE.md`, `docs/v0.3/V03E_IMPLEMENTATION.md` |
| Reviewer | an independent subagent given the code, the spec and the acceptance matrix, with a **review-only** brief (no edits to the repository) |
| Method | adversarial reading plus executable reproductions from `D:\DevRelay`: crash-window harnesses from `tests/v03d_helpers.py`, byte-level diffs of `.devrelay`, ledger tampering, digest tampering, error-code and annotation inspection |
| Review question | does the mandatory fail-closed core (a) never reopen an interrupted run, (b) never replay/submit/retry/resume, (c) attribute evidence honestly with no inference from absence, (d) survive restart, and (e) keep `adopt_completed_turn` unreachable? |
| Verdict | **REQUEST CHANGES** — P0: 1, P1: 3, P2: 4 |

The reviewer also confirmed the governance gap independently: no v0.3-E
implementation-authorization record exists in `docs/v0.3`, so the reviewed code is
an unauthorized draft (already disclosed in `V03E_IMPLEMENTATION.md`).

## 2. Findings and dispositions

Every finding below was reproduced before it was fixed; every fix is covered by a
new or extended test, and the full suite was re-run afterwards (§4).

| id | sev | location (before the fix) | defect | disposition |
| --- | --- | --- | --- | --- |
| F1 | **P0** | `src/devrelay/orchestration/service.py` (`reconcile_run` → `_collect_recovery_evidence` → `bridge.read_messages`), `src/devrelay/mcp/server.py` annotations | `devrelay_reconcile_run` was annotated `read_only_hint=True` and §21 requires "no durable mutation", but on a live intent it issued two HTTP GETs; the bridge accounts **every** HTTP call, so reconcile appended `OC-0008.json`/`OC-0009.json` and rewrote `opencode/sequence.json` while reporting on that very surface (the ceiling it reported was read before its own writes). The same GET path ran inside `resolve_recovery`. | **Fixed.** The mandatory core is now strictly local: `_local_evidence` scans the durable ledger only, `reconcile_run`/`_enter_and_resolve` perform no provider call, and the report states the remote gap explicitly (`recovery.REMOTE_NOT_READ_REASON`). `test_v03e_recovery.py` now snapshots **every** file under `.devrelay` (SHA-256) and requires the tree to be byte-identical across reconcile; a second assertion requires the accounting subtree to be unchanged across resolve. |
| F2 | **P1** | `src/devrelay/orchestration/ledger_reader.py` (completeness and newer-than-sequence checks nested in `if calls_dir.is_dir()`) | An absent calls directory with a surviving `sequence.json` proved an interval it could not prove (`no_record_in_proven_interval`, `interval_proven=True`). | **Fixed.** Completeness over `1..ceiling` now runs regardless of the directory's presence; an absent directory therefore degrades to `evidence_gap` ("has no accounting record"). |
| F3 | **P1** | `ledger_reader.py` (no `floor <= ceiling` check) | A floor newer than the ceiling (inverted interval) silently skipped every candidate and reported a proven absence. | **Fixed.** An inverted interval is `evidence_gap` ("the interval is inverted, so nothing inside it is proven"). |
| F4 | **P1** | `ledger_reader.py` (`present[number] = path`) | Two files whose names parse to one id (`OC-0002.json` + `OC-00002.json`) collapsed into one, so two matching submissions could be reported as `exactly_one_match`. | **Fixed.** Two files claiming one id are `evidence_gap` ("two ledger files claim call OC-…; the submission identity is ambiguous"). |
| F5 | **P2** | `src/devrelay/orchestration/models.py` (`coverage` outside the digest), `src/devrelay/orchestration/invariants.py` | `coverage` was never validated and `attempt.blocked_reason` was never tied to `recovery_reason`; a hand edit (`coverage="PWNED"`, `blocked_reason="cycle_limit"`) was accepted by `store.load`/`get_run`. | **Fixed.** Invariants require `coverage ∈ {proven_interval, evidence_gap}` and `blocked_reason == recovery_reason` for a failed frozen attempt (a completed one must carry none). `frozen_attempt` no longer silently normalizes an unknown reason. Covered by two new invariant tests. |
| F6 | **P2** | `ledger_reader.py` (no `record.call_id` check against its file name/ceiling) | A record stored as `OC-0002.json` but declaring `call_id: OC-0009` was accepted as the attribution for `OC-0002`. | **Fixed.** A record must declare exactly its file-name identity, otherwise `evidence_gap` ("declares call_id …; it cannot be attributed to …"). New ledger test. |
| F7 | **P2** | `src/devrelay/orchestration/recovery.py` (`reconcile_report`), `service.py` | The report lacked §21's per-item `checklist` (pass/fail/unknown) and `blockers`, and terminal runs received a full report although §21 says reconcile "refuses locally for terminal states". | **Fixed.** The report now carries `checklist` + `blockers` (document, attempt identity, ledger attribution, ledger settlement, remote correlation, route stability, resolution state, adoption capability, platform proofs). A terminal run is refused locally with `orchestration_recovery_unsupported` and no write. The §10 vs §21 wording conflict about **v1** documents is resolved in favour of §10's explicit dispatch ("report only"): a v1 document still gets the frozen `v1_frozen` report, which now says so in its checklist and blockers. Pinned by `test_terminal_runs_are_never_reopened` and the existing frozen-v1 test. |
| F8 | **P2** | `tests/test_v03e_recovery.py` "read-only" tests | They compared only `prompt_posts()`, so F1 stayed green. | **Fixed** together with F1: byte-level tree snapshots, plus accounting-subtree assertions for resolve. |

Two further defects were found by the author while preparing the review inputs and
are included here for completeness:

| id | sev | defect | disposition |
| --- | --- | --- | --- |
| A1 | P1 | `previous_floor` called `ledger_reader.newest_call_id(call_ids)` (a list) against a `*call_ids` signature, so it always raised; the broad `except` in the collector turned every v2 reconcile report into a silent blank gap (`gap_reason=""`). | **Fixed** (`newest_call_id(*call_ids)`; reasoned gap on failure; non-empty gap reason when there is no attempt to attribute). Regression tests in `tests/test_v03e_attribution.py`. |
| A2 | P2 | `frozen_attempt` silently substituted `turn_interrupted` for an unknown reason, which could disagree with the record's `recovery_reason`. | **Fixed**: it now raises; invariants also cross-check the two. |

## 3. Attacked and held

The reviewer exercised these attacks and the implementation held; they are part of
the evidence value of this round and are kept in the suite:

- a live v2 intent refuses `devrelay_run_implementer`, `devrelay_run_reviewer` and
  `devrelay_decide_run` with `orchestration_recovery_required`, byte-identically,
  with zero submissions;
- resolution is write-once (`orchestration_recovery_already_resolved`, zero
  bytes changed on the repeat);
- `adopt_completed_turn` is refused before any write
  (`orchestration_adoption_disabled`), and flipping
  `ADOPTION_CAPABILITY_ENABLED` in-process still cannot produce an adopted state
  (the record validator refuses it; the run stays unchanged);
- a frozen v1 document refuses resolution and keeps the v0.3-D fail-closed
  materialization;
- one atomic run write (temp file + `os.replace`), so a crash leaves either the
  pre-recovery or the post-recovery document, never a mixture;
- the strict reader rejects extra fields, wrong schema versions, foreign
  evidence, digest mismatches and tampered adoption;
- `mark_unrecoverable` survives a missing/unreadable evidence surface (gap is
  reported, never required);
- restart: a live intent, a persisted `RECOVERY_REQUIRED` document and a settled
  `BLOCKED` run are all read back exactly, with no automatic work;
- no retry/resume/resubmission/polling path exists in the new code;
- the MCP per-surface execution lock serializes reconcile/resolve on one surface;
  multi-surface coordination is explicitly unsupported (documented, not a claim).

## 4. Post-remediation verification

```
python -m pytest -q            # isolated TEMP outside the repository
```

- v0.3-E suites: `tests/test_v03e_recovery.py` (15),
  `tests/test_v03e_attribution.py` (8), `tests/test_v03e_ledger.py` (17),
  `tests/test_v03e_models.py` (13), `tests/test_v03e_invariants.py` (17) — 70
  passed.
- Full suite: **1236 collected, 0 failed, pytest exit 0**.

Numbers are recorded by the implementing session, not independently re-measured
by the reviewer (the reviewer ran the 56-test v0.3-E snapshot that existed at
review time and confirmed it green — which is exactly why F1–F8 survived it).

## 5. Residual risks and open items

1. **Remote correlation is not wired.** The mandatory core never reads session
   history; `recovery.match_remote_turn` exists as the §12.3 rule set for the
   gated adoption path. Any future adoption work must wire it *and* solve the
   accounting problem F1 exposed (a read that appends ledger records), under a
   new authorization and on top of the platform proofs.
2. **Adoption code is dead-in-this-build.** `_apply_resolution`'s adopt branch and
   `state_machine.after_adoption` are unreachable while
   `ADOPTION_CAPABILITY_ENABLED` is `False` and are not exercised by tests; the
   flag-flip probe shows the record validator refuses the state rather than an
   explicit check. That is acceptable only while adoption is disabled; enabling
   the capability requires a dedicated review of that path.
   > Later status (2026-10-20): `_apply_resolution` now refuses adoption with an
   > explicit guard before any mutation; the flag-flip test covers it
   > (`test_adoption_flag_flip_is_refused_before_any_write`).
3. **Whole-ledger completeness is deliberately stricter than interval proof.**
   The reader requires every allocated call id from `OC-0001` to the durable
   ceiling to have a record. A deletion below the floor therefore degrades
   attribution to a permanent `evidence_gap` — conservative, and intentionally
   kept (an unprovable interval must never become a proof).
4. **No service-level lock.** `OrchestrationService` called directly has no
   per-surface lock; only the MCP surface does. Multi-surface use remains
   unsupported by design.
5. **No real recovery execution.** All of the above is offline and deterministic;
   the real smoke of §26 is still not authorized.

## 6. Governance outcome

- No acceptance row is marked COVERED by this design-freeze review; the status
  line it examined read "DESIGN FROZEN / NOT ACCEPTED / UNRELEASED" and the proof
  gate for adoption was then unchanged.  **Later status:** the implementation was
  subsequently authorized, the mandatory fail-closed core was independently
  accepted (2026-10-17; P0 = 0, P1 = 0, P2 = 2 — `V03E_ACCEPTANCE.md`), adoption
  remains **DISABLED**, the platform gates are open and the package is
  **unreleased**.
- The findings were remediated in the unauthorized draft so the recorded draft is
  internally coherent; that is the entire status change.
- An implementation authorization, the independent acceptance review and the real
  smoke remain prerequisites before any of this can be treated as the authorized
  v0.3-E implementation.
