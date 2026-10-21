# DevRelay v0.3-E — implementation authorization request

Status: **REQUEST — NOT ISSUED BY THIS DOCUMENT**

Requesting session: the implementing agent session, branch
`v0.3-e-recovery-reconciliation` at `36fe9c5cc367a024b2365611f4cb00c7f2b9e249`.

## 1. What is requested

Two things, and nothing else:

1. **Ratification of the already-written draft.**  The mandatory fail-closed
   recovery core exists on this branch as a **draft without an implementation
   authorization record** (disclosed in
   `docs/v0.3/V03E_IMPLEMENTATION.md`, commit `54ec97f`).  Requested: an
   implementation authorization that covers that code as it stands after the
   review remediation (commit `a7fe160`), so the work is an authorized
   implementation of the frozen design instead of an unauthorized draft.
2. **Exactly one real crash-and-recovery smoke**, executed under the
   precommitted oracle `docs/v0.3/V03E_REAL_RECOVERY_SMOKE_ORACLE.md`
   (SHA-256 `ac9e0318b9257691067ccc6cfb669516dbb6d64d5ee56b9d5eaad46f5ac9df6c`).

The authorization must be **one-shot**: after the smoke executes, it is spent.  A
rerun requires a new oracle and a new authorization.

## 2. Why the request is well-founded

| Item | State |
| --- | --- |
| Design freeze | `docs/v0.3/V03E_SPEC.md` frozen; candidate `9f4a01804…` reviewed **P0 = 0, P1 = 0, P2 = 0** |
| Mandatory-core local gate | **G0.1 / P7 = PASS** — authoritative, independently approved (`V03E_G0_1_P7_PROOF.md`); the only gate the mandatory core needed before implementation |
| Adoption gate | **untouched and unsatisfied** — G0.4 authoritative FAIL / P4 UNPROVEN; G0.5/P6, G1, G2 not run; `ADOPTION_CAPABILITY_ENABLED = False` |
| Implementation | drafted and reviewed adversarially; one P0, three P1, four P2 found, all remediated (`V03E_REVIEW.md`, commit `a7fe160`) |
| Offline evidence | 70 v0.3-E tests, 1236 full-suite tests, all green; the report is `V03E_IMPLEMENTATION.md` |
| Missing pieces this request covers | the implementation-authorization record, and one real crash-and-recovery execution |

## 3. Binding constraints proposed for the authorization

1. **Scope**: only the mandatory fail-closed core (`reconcile` + `mark_unrecoverable`);
   `adopt_completed_turn` stays disabled and out of scope.
2. **One smoke**, one run, `max_cycles = 1`, at most **one** real model-bearing
   submission (the crashed implementer turn).  Reviewer turns, retries, resumes and
   second runs are not authorized.
3. **Disposable everything**: dedicated loopback OpenCode instance, disposable
   workspace and sessions under `%TEMP%`, deleted afterwards; the user's own
   OpenCode instance and sessions are never touched.
4. **No acceptance, no release**: no row of `V03E_ACCEPTANCE.md` may be marked
   COVERED, no tag/release/push/merge, package version and public release unchanged.
5. **Oracle immutability**: the oracle is frozen at the authorization commit and
   executed without edit; a material defect is a FAIL, recorded, not patched.
6. **Evidence outside the repository**; the result document in the repository cites
   its path and hashes.
7. **Repository neutrality**: the tracked tree is byte-identical before and after;
   the only new files are the governance artifacts of this request/round.

## 4. Explicit non-goals

- No enablement of adoption, no remote-correlation wiring (the mandatory core is
  local-only by design: every OpenCode HTTP call is ledger-accounted, so a
  session-history GET would be a durable mutation under a read-only annotation).
- No acceptance review and no claim of independent approval.
- No real-provider proof for any v0.3-E adoption precondition.

## 5. Decision requested

Either:

- **APPROVE** — issue `docs/v0.3/V03E_IMPLEMENTATION_AUTHORIZATION.md` with the
  scope in §1, the constraints in §3 and the oracle hash above; or
- **REJECT / REQUEST CHANGES** — state which condition is unacceptable.

The decision is the workspace owner's; the implementing session cannot and does not
issue it to itself.


