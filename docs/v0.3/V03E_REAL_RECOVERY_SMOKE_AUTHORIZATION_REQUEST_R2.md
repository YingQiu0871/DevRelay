# DevRelay v0.3-E — real-smoke authorization request, revision 2

Status: **REQUEST — NOT ISSUED BY THIS DOCUMENT**

Requesting session: the implementing agent session, branch
`v0.3-e-recovery-reconciliation` at `312dd74`.

## 1. What is requested

**Exactly one** real crash-and-recovery smoke of the v0.3-E mandatory fail-closed
core, executed under the corrective precommitted oracle
`docs/v0.3/V03E_REAL_RECOVERY_SMOKE_ORACLE_R2.md`, after the revision-1 smoke was
recorded as FAIL (see `docs/v0.3/V03E_REAL_RECOVERY_SMOKE_RESULT.md`,
`docs/v0.3/V03E_IMPLEMENTATION_AUTHORIZATION.md` §3).

## 2. Why a revision-2 smoke is well-founded

| Item | State |
| --- | --- |
| Revision-1 oracle + driver | precommitted at `f8f52a2`; executed once; authorization spent |
| Revision-1 result | **FAIL** under the oracle as written; every product-facing phase S0–S8 was observed conformant |
| Defect 1 (oracle) | §3 counted *all* `send_prompt` records, including the bridge's non-submitting ownership-probe GET (same operation label, no prompt digest) — the count could never equal the model-bearing POST count |
| Defect 2 (harness) | the revision-1 driver recorded `agree: false` but never *asserted* the equality rule, so it printed PASS while the written rule says FAIL; a driver↔oracle fidelity defect |
| Correction in R2 | the submission count is normative: `method == "POST"` records for the implementer session must equal the instance log's `message=process` lines; the expected probe GETs are recorded separately; **every** oracle rule must map to a named, asserted driver criterion, evidenced in `oracle-conformance.json` |
| Product code | unchanged by this round (no source edit is requested or authorized) |

The revision-1 run is not reinterpreted: it stays FAIL and spent. Revision 2 is a
new, corrective instrument and needs its own one-shot authorization.

## 3. Binding constraints proposed

1. **Scope**: the mandatory fail-closed core only (`reconcile` + `mark_unrecoverable`);
   `adopt_completed_turn` stays disabled, `ADOPTION_CAPABILITY_ENABLED = False`.
2. **One smoke**, one run, `max_cycles = 1`, at most **one** real model-bearing
   submission (the crashed implementer turn). No retry, resume, replay, second run.
3. **Disposable everything**: dedicated loopback instance, `%TEMP%` workspace and
   sessions, removed afterwards; the operator's own OpenCode instance is untouched.
4. **No acceptance, no release**: no `V03E_ACCEPTANCE.md` row may be marked COVERED,
   no tag/release/push/merge, version unchanged.
5. **Immutability**: oracle R2 and driver R2 are frozen at the authorization commit
   and executed without edit; a material defect is a FAIL, recorded, not patched.
6. **Evidence outside the repository**, cited by path and SHA-256 from the result
   document.
7. **Repository neutrality**: the tracked tree is byte-identical before and after;
   only this round's governance artifacts are new.

## 4. Explicit non-goals

- No enablement of adoption, no remote-correlation read.
- No acceptance review and no claim of independent approval: a PASS here is
  evidence, and the separately authorized independent review still decides.

## 5. Decision requested

Either:

- **APPROVE** — issue `docs/v0.3/V03E_REAL_RECOVERY_SMOKE_AUTHORIZATION_R2.md`
  citing the oracle R2 and driver R2 hashes; or
- **REJECT / REQUEST CHANGES** — state which condition is unacceptable.

The decision is the workspace owner's; the implementing session cannot and does not
issue it to itself.
