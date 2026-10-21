# DevRelay v0.3-E — G0.5-PRE / SIC — Path-F one-shot ETB execution authorization

> **PATH-F AUTHORIZATION = CORRECTIVE SUCCESSOR DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / NOT EXECUTED.**
> **THIS AUTHORIZATION DESIGN GRANTS NO EXECUTION AUTHORITY TODAY.**
> **IT SUPERSEDES NOTHING BY ITSELF: THE PREVIOUSLY ACCEPTED PATH-F AUTHORIZATION REMAINS HISTORICALLY ACCEPTED / FROZEN / EFFECTIVE, AND ONLY ITS OPERATIONAL USE IS BLOCKED AFTER THE PRE-16 PRECONDITION STOP.**
> **REQUIRED PATH-F DSH OPERATIONAL EXECUTION / FILE-ACCESS MODE = `danger-full-access` — THE ONE NORMATIVE MODE TOKEN — ESTABLISHED BEFORE THE IRREVERSIBLE SEQUENCE AND OBSERVED THROUGH THE DSH SESSION RUNTIME-CONTEXT POLICY DECLARATION (§6.1, §6.4, PRE-16).**
> **`read-only` AND `workspace-write` ARE INSUFFICIENT FOR PATH-F OPERATIONAL EXECUTION.**
> **BOUNDED P2 REMEDIATION REVISION: THIS REVISION PROSPECTIVELY SUCCEEDS THE FIRST CORRECTIVE CANDIDATE `d895856d2efc9683b91b182c33647efe57b01fc3` / `c281f93e6ddfe09351c435e698c5d50c3a5cfcda2053f27159ba921e2eed72eb` (QUALIFYING REVIEW = `REQUEST_CHANGES` / P2 = 1 / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE), WHOSE BYTES REMAIN IMMUTABLE HISTORY AND ARE NOT AMENDED, REVOKED OR RELABELLED.**
> **IT CREATES NO CLAIM NOW AND CONSUMES NO BUDGET.**
> **IT DOES NOT ENTER ORACLE-PATHF AND DOES NOT QUERY ANY LISTENER.**
> **IT IS AUTHORIZED FOR DESIGN ONLY AT THIS STAGE.**
> **THIS IS NOT A RETRY OF PATH-E, PATH-D OR OF ANY EARLIER LINEAGE.**
> **ONE AUTHORIZATION USE + ONE ETB ATTEMPT ONLY IF LATER INDEPENDENTLY ACCEPTED.**

**Status:** **PATH-F AUTHORIZATION = CORRECTIVE SUCCESSOR DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / NOT EXECUTED**

**Date:** 2026-10-03
**Repository:** `D:\DevRelay`
**Branch:** `v0.3-e-recovery-reconciliation`
**Parent governance commit (build base):** `d895856d2efc9683b91b182c33647efe57b01fc3`
**Disposition commit bound (predecessor of the first corrective candidate; PRE-16 stop):** `5fae11eefdcaddc27b4abf28d3a2258ad654d84d`
**Corrective successor of (historically accepted; operationally blocked after the PRE-16 precondition stop):** `ed112f8c5f1e35d87092d0339698a792ce0b145a` / `c147af8714164dae8b81cafa4eb01945a3ceb8c74b36f0fc18fbd56db284c4de`
**Bounded P2 remediation successor of (qualifying review `REQUEST_CHANGES`, P2 = 1, not accepted / not frozen / not effective):** `d895856d2efc9683b91b182c33647efe57b01fc3` / `c281f93e6ddfe09351c435e698c5d50c3a5cfcda2053f27159ba921e2eed72eb`

---

## 0. Owner decisions (immutable)

The Owner has recorded, and this artifact may not weaken, reinterpret, relabel or extend:

1. `PATH-F LINEAGE = OPENED FOR DESIGN ONLY` — the Owner recorded `OWNER DECISION = OPEN A NEW ETB LINEAGE`; `PREDECESSOR LINEAGE = PATH E`; `NEW LINEAGE = PATH F — NEW ETB ATTEMPT`; `NEW EXECUTION ORACLE = Oracle-PathF`; `OWNER NAMING DECISION = PATH-F / Oracle-PathF`; canonical lineage token `PATH_F`; canonical oracle token `ORACLE_PATH_F`. Those decisions are recovered from the accepted `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.md` §1 and are **not** re-decided, re-derived or extended here.
2. This new lineage is **explicitly NOT** a Path-E retry, **NOT** a Path-E continuation, **NOT** a Path-E budget reset, **NOT** a Path-E claim reuse, **NOT** a Path-E repair-and-rerun, **NOT** a promotion of the raw Path-E observation, **NOT** `Recovery-R3`, **NOT** `Oracle-PathE` v2, **NOT** a Path-D reopen, **NOT** a reuse of any Path-D or Path-E authorization, and **NOT** an ACL restoration round.
3. `PATH-E LINEAGE = EXHAUSTED / CLOSED`; `PATH-E RETRY AUTHORITY = NONE`; Path E is not reopened, repaired or rerun by this round.
4. `PATH-D LINEAGE = EXHAUSTED / CLOSED / IMMUTABLE`; `PATH-D RETRY AUTHORITY = NONE`; Path D is not reopened, repaired or rerun by this round.
5. `ORACLE-PATHF = ACCEPTED / FROZEN / EFFECTIVE`, with accepted design identity `a5d598a05a0467eea98cd0bf16e4486cceb72c23`, and it must not be modified, re-accepted, re-reviewed-in-place, re-scoped or extended by this authorization.
6. `provenance_model = MODEL_2_EXTERNAL_LINEAGE_BINDING` (§19 of the accepted Oracle-PathF specification) is **frozen** and is not re-decided by this authorization. This authorization is required to be **compatible** with it; §3 and §19.4 record that compatibility explicitly.
7. The ETB result-class model is closed at exactly three classes and no fourth ETB class may be created by this lineage; governance/control descriptors are not ETB semantic classes.
8. The last authoritative ETB semantic result is `ETB_UNSATISFIED` and must remain **PRESERVED** until a future authorized Path-F execution produces a new raw observation **and** that observation completes independent result review, result bookkeeping and independent confirmation of that bookkeeping.
9. Any stage that this document requires to be an independent third-party review or confirmation must satisfy `OWNER DETERMINATION = THIRD-PARTY INDEPENDENCE REQUIRES DIFFERENT AGENT/SESSION`; a methodological same-session review is adversarial self-review and is **NOT SUFFICIENT** for third-party independence.
10. The `PATH-E` operational lessons `L1`–`L5` recorded in the accepted Oracle-PathF specification §2.2 are carried forward as accepted history and are **NOT** repaired by editing any frozen predecessor byte. `L3` (cross-document provenance wording tension) is closed for Path-F **by construction in this document** (§3, §19.4), not by editing the accepted Oracle-PathF specification.
11. The Owner authorized the creation of this design candidate only. Acceptance, freezing, effectivity and execution authority are **NOT** granted by this round.
12. `OWNER DECISION = AUTHOR ONE CORRECTIVE SUCCESSOR PATH-F ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE`, recorded in the Owner order governing this corrective round after the one-shot operational round terminated at its first failed precondition (`PRE-16`) with `PATH-F OPERATIONAL EXECUTION = NOT STARTED`, and governed by the disposition commit `5fae11eefdcaddc27b4abf28d3a2258ad654d84d` with `PATHF_PRE16_STRUCTURAL_GAP = CONFIRMED` and `REMEDIATION ROUTE = ROUTE A`. Route A requires exactly this corrective successor design lifecycle and **forbids** repairing the frozen accepted artifact in place. Acceptance, freezing, effectivity and execution authority are **NOT** granted to this corrective candidate either.
13. `REQUIRED PATH-F DSH OPERATIONAL EXECUTION / FILE-ACCESS MODE = danger-full-access`. This is the **one and only normative execution / file-access mode token of this authorization**, and it is the canonical unconfined mode token of the DSH harness in which the future operational round will run (§6.1, §6.4). `read-only = INSUFFICIENT FOR PATH-F OPERATIONAL EXECUTION` and `workspace-write = INSUFFICIENT FOR PATH-F OPERATIONAL EXECUTION`. This is a **PRE-EXISTING SESSION MODE requirement** supplied to the future operational execution environment. It is **NOT** reactive escalation authority, **NOT** ACL-repair authority, **NOT** permission-repair authority, **NOT** retry authority and **NOT** authority to switch modes after a failed gate or a failed claim operation. Stating the required mode prospectively is what the accepted Oracle-PathF specification §9.1/§9.2 requires of an execution-authorization record, and it is compatible with the frozen prohibition on reactive escalation (specification §9.3/§9.4; §6 and §7 of this artifact). This decision grants no ability to this authorization layer, the executor, the Oracle or any helper to elevate itself. **Superseded token (recorded once, so that the correction is auditable):** the first corrective candidate of this lineage stated this requirement as `full-file-access`. That token is **HISTORICAL / DESCRIPTIVE ONLY / NOT A DSH MODE TOKEN / NOT ACCEPTABLE AS PRE-16 EVIDENCE**; it is not a member of the closed DSH canonical mode vocabulary `read-only` | `workspace-write` | `danger-full-access`, and it appears nowhere in this artifact as a normative execution-mode value.
14. This corrective successor **revises this artifact only**. The previously accepted authorization artifact bytes at `c147af8714164dae8b81cafa4eb01945a3ceb8c74b36f0fc18fbd56db284c4de` remain immutable history, their acceptance remains historically valid, and neither identity is operationally usable until the corrective successor completes the lifecycle of §20. No historical status surface is rewritten by this round.
15. `OWNER DECISION = AUTHOR EXACTLY ONE BOUNDED CORRECTIVE SUCCESSOR REVISION TO REMEDIATE THE QUALIFYING-REVIEW P2 IN THE PATH-F CORRECTIVE AUTHORIZATION DESIGN`. The remediated finding is `FULL_FILE_ACCESS_MODE_IDENTITY = LABEL_PRESENT_BUT_NOT_OPERATIONALLY_VERIFIABLE` with `CORRECTED_PRE_16 = AMBIGUOUS`; the corrected prospective governance decision is paragraph 13 above. The scope of the remediation is **the sole blocking P2 plus the mechanical governance and cross-reference updates directly necessary to record it**; the four non-blocking observations of that review cause **no** broader redesign, and the design findings `P3-A` … `P3-G` already corrected by the preceding revision do **not** regress. Acceptance, freezing, effectivity and execution authority are **NOT** granted to this bounded remediation revision either.

These Owner decisions are recorded in the active tracked status surfaces of this repository and are not re-derivable from this artifact alone.

---

## 1. Purpose and scope

### 1.1 Purpose

This artifact defines the **one-shot ETB execution-authorization model for the PATH F — NEW ETB ATTEMPT lineage**.

Its purpose is to make the following **mechanically checkable, deterministic, fail-closed and auditable**:

1. what an executor must verify **before** any authorization budget is consumed;
2. where, how and with exactly which bytes the two claim budgets are consumed;
3. what irreversible point of no return consumption represents;
4. which prerequisites must already hold before the irreversible sequence begins — in particular execution/file-access mode viability and the absence of any ACL repair;
5. what the authorization layer may **not** do (target binding, listener query, result classification);
6. how the single Oracle-PathF invocation is bounded, targeted and terminated;
7. how the resulting raw observation relates to the authoritative ETB semantic result;
8. how this authorization itself becomes effective — and only then usable.

### 1.2 Non-purpose

This artifact is **not**: an acceptance of itself; an execution; a retry; a listener probe; a target probe; a readiness check; a Path-E or Path-D artifact; a modification of any accepted Oracle-PathF artifact; a new ETB result class; a promotion of any observation to the authoritative ETB semantic result; an authorization for more than one authorization use and more than one ETB attempt; or a reusable, resettable or renewable budget.

### 1.3 Scope boundary

This artifact governs **only** the consumption of the two Path-F claim budgets for **one** attempt of **one** invocation of the **accepted** Oracle-PathF executable against the **pre-existing** target, under all preconditions of §13.

It does **not** govern: the Oracle's internal behavior (owned by the accepted Oracle-PathF specification); the Oracle's write-viability gate internals (owned by the same specification); the target application's behavior; any other lineage; any other endpoint; any other port; any other executable; any second attempt.

### 1.4 Design inputs recovered from precedent

This candidate was designed from the following recovered repository precedent, and it invents no structure that precedent does not support:

| Precedent object | Commit | Role in this design |
| --- | --- | --- |
| Path-D ETB authorization design candidate | `29bf27fc2f76d415eb9c07d890f50b665aca6846` | earliest candidate shape: two-file governance delta + new artifact, PRE-1 … PRE-15 |
| Path-E ETB authorization design candidate | `26b183083fbbe323441283f99f3cf2c931acd6ff` | rejected candidate; source of the two blocking findings this design must not repeat |
| Path-E authorization remediation | `4900625114a38a86aa03a5fa4861c5bcd9436dc5` | corrected `PRE-2` (no self-identity paradox) and corrected `PRE-3` (no contradictory effectivity requirement) |
| Path-E authorization acceptance bookkeeping | `48e9b66dd5aeb147795dbc57e822e6b3d38e4565` | acceptance stage shape |
| Path-E authorization confirmation record | `c7ac36a8c596ae2ede8db7bce2e625f8c6ffa21c` | confirmation / materialization stage shape |
| Path-E authorization corrective successor commit | `4900625114a38a86aa03a5fa4861c5bcd9436dc5` | **the corrective-successor mutation shape reused, in substance, by this round**: exactly three modified paths (`CHANGELOG.md`, `docs/v0.3/V03E_ACCEPTANCE.md` and the authorization artifact), numstat `2 0` / `1 1` / `12 5`, subject family `fix(v03e): remediate <lineage> ETB authorization design review findings`, old candidate identity preserved and superseded prospectively only |
| Path-F PRE-16 disposition | `5fae11eefdcaddc27b4abf28d3a2258ad654d84d` | binds this corrective round: `PATH-F OPERATIONAL EXECUTION = NOT STARTED` at `PRE-16`, `PATHF_PRE16_STRUCTURAL_GAP = CONFIRMED`, `REMEDIATION ROUTE = ROUTE A`, and the Owner's prospective required execution-mode decision, whose canonical token is `danger-full-access` (§6.1) |

**Recovered authorization-design precedent classification:**

```
PATHF_EXECUTION_AUTHORIZATION_DESIGN_PRECEDENT = DETERMINATIVE
```

The classification is `DETERMINATIVE` because the candidate shape (exactly two modified governance surfaces plus exactly one new authorization artifact, and no `.gitattributes` change), the subject family (`docs(v03e): define <lineage> ETB authorization candidate`), the artifact naming family (`docs/v0.3/V03E_G0_5_PRE_ETB_PATH_<X>_AUTHORIZATION.md`), the claim-path family (`docs/v0.3/evidence/ETB_PATH_<X>_*_USE.claim{,.tmp}`), the claim schemas, the frozen claim-writer primitive, the PRE-gate family and the ordered five-stage authorization lifecycle are all fixed by direct repository precedent, and the two blocked design decisions (self-identity and effectivity-gate satisfiability) have a committed corrected precedent to inherit verbatim in substance. No acceptance-critical ambiguity remains.

**Corrective-successor precedent (added by this revision):**

```
PATHF_CORRECTIVE_AUTHORIZATION_DESIGN_PRECEDENT = DETERMINATIVE
```

The corrective-successor shape is likewise fixed by direct repository precedent, `4900625114a38a86aa03a5fa4861c5bcd9436dc5`: a frozen artifact with a recorded defect is corrected by a **new successor revision of the same artifact path** (never by amending the frozen revision), the old candidate identity is preserved and superseded **prospectively only**, the correction carries exactly the three-path governance delta, and the corrected successor is what the lineage's single authorization-use budget later binds. The one Path-F-specific novelty — this lineage's superseded identity had already reached `ACCEPTED / FROZEN / EFFECTIVE` while its budgets remained unconsumed — is resolved by the prospective-only supersession and the identity re-binding rules of §5.5, which create no second budget, no reset and no automatic reuse.

---

## 2. Accepted Oracle-PathF provenance

The authorization binds the following **accepted, frozen and effective** identity and may not redefine, extend, re-derive or modify it:

| Item | Frozen value |
| --- | --- |
| `oracle_path_f_commit` | `a5d598a05a0467eea98cd0bf16e4486cceb72c23` |
| `oracle_path_f_parent` | `c45fb94068d5384dd9662f822be4722951f4200b` |
| `oracle_path_f_tree` | `c4572c9e42e2ee0484e85536f3d1c7c32335f232` |
| `oracle_path_f_subject` | `docs(v03e): define Path-F execution oracle candidate` |
| `oracle_path_f_spec` | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.md` |
| `oracle_path_f_spec_sha256` | `b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5` |
| `oracle_path_f_spec_bytes` | `34308` |
| `oracle_path_f_spec_lines` | `733` |
| `oracle_path_f_script` | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.ps1` |
| `oracle_path_f_script_sha256` | `4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0` |
| `oracle_path_f_script_bytes` | `49704` |
| `oracle_path_f_script_lines` | `894` |
| `oracle_path_f_design_acceptance_bookkeeping` | `7ad12d1d0b9727548b271981116267f76c362f48` |
| `oracle_path_f_design_acceptance_bookkeeping_parent` | `a5d598a05a0467eea98cd0bf16e4486cceb72c23` |
| `oracle_path_f_design_acceptance_bookkeeping_tree` | `074b703dc6512b78ebd8381aa4147a3a96be2deb` |
| `oracle_path_f_design_acceptance_confirmation_record` | `1d06f2857840b9f4096bbedc156e3ac4c9eaddec` |
| `Oracle-PathF status` | `ACCEPTED / FROZEN / EFFECTIVE` |
| `Oracle-PathF execution` | `NOT AUTHORIZED` (the accepted design is effective; **executing it is not**) |
| `PATH-F EXECUTION AUTHORIZATION` | `ACCEPTED / FROZEN / EFFECTIVE` at `ed112f8c5f1e35d87092d0339698a792ce0b145a` / `c147af8714164dae8b81cafa4eb01945a3ceb8c74b36f0fc18fbd56db284c4de`, **OPERATIONALLY BLOCKED AFTER THE PRE-16 PRECONDITION STOP**; this corrective successor revision of the artifact is `DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE` (§5.5, §23) |
| `PATH-F EXECUTION AUTHORITY` | `NONE` (no operational round may run under either authorization identity until the corrective successor completes the lifecycle of §20) |
| `PATH-F OPERATIONAL EXECUTION` | `NOT STARTED` / `PRE-16 PRECONDITION STOP` / `NO CLAIM` / `NO BUDGET CONSUMPTION` / `NO ORACLE INVOCATION` |

`oracle_path_f_commit` is the **independently reviewed DESIGN commit**. It is **never** substituted by an acceptance-bookkeeping commit, by a confirmation-record commit, by this authorization's own future commit, by the current branch HEAD, or by any later commit; the acceptance and confirmation commits are recorded above as separate provenance facts only.

**Boundary of the design-candidate round that produced the accepted Oracle-F design:** the accepted design commit `a5d598a05a0467eea98cd0bf16e4486cceb72c23` is recorded as the accepted artifact identity because that value is directly repository-verifiable and is carried in the tracked status surfaces. This authorization records it as a **frozen binding**, not as a re-derivation; no claim is made here about any identity that the repository cannot attest.

---

## 3. Provenance model compatibility — MODEL 2 external lineage binding

The accepted Oracle-PathF specification §19 freezes:

```
provenance_model = MODEL_2_EXTERNAL_LINEAGE_BINDING
provenance_owner_content = ORACLE_PATH_F_SPEC
provenance_owner_lineage_binding = PATH_F_EXECUTION_AUTHORIZATION_RECORD_AND_CLAIMS
```

This authorization is written **compatibly** with that model and does not restate it as its own rule.

### 3.1 Content provenance is owned by the specification, not by this authorization

The Oracle-PathF evidence artifact carries the three Path-F provenance fields with the literal value `UNKNOWN`:

| Field in Oracle-generated evidence | Frozen value |
| --- | --- |
| `oracle_path_f_commit` | `UNKNOWN` |
| `oracle_path_f_spec_sha256` | `UNKNOWN` |
| `oracle_path_f_script_sha256` | `UNKNOWN` |

These are **not** defects and are **not** corrected by editing the accepted specification, the executable, or the evidence artifact.

### 3.2 Lineage binding is owned externally

The lineage binding is supplied **here**, and by the future Path-F claims and accepted control surfaces:

| Generic (accepted Oracle-PathF evidence) | Path-F binding (this authorization and the claims) |
| --- | --- |
| `oracle_path_f_commit = UNKNOWN` | `a5d598a05a0467eea98cd0bf16e4486cceb72c23` |
| `oracle_path_f_spec_sha256 = UNKNOWN` | `b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5` |
| `oracle_path_f_script_sha256 = UNKNOWN` | `4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0` |
| `oracle_self_identity_sha256` / `oracle_self_identity_spec_sha256` (runtime observations) | **not** lineage provenance; never substituted for the fields above |

### 3.3 The no-contradiction rule (closes Path-E lesson L3 for Path-F)

**This authorization MUST NOT contain, and does not contain, any requirement that every evidence artifact record the frozen Path-F identities, and it MUST NOT contain, and does not contain, any requirement that an Oracle-generated evidence field be something other than `UNKNOWN`.**

Consequences that must not be blurred:

1. every Path-F **claim** and every accepted **governance surface** records the **frozen Path-F values** of §2, never `UNKNOWN`;
2. the **Oracle-generated evidence artifact** records the literal `UNKNOWN` reserved by the accepted specification and is **never required** by this authorization to record anything else;
3. **no inference, defaulting or fabrication is permitted**: neither the executor, nor the authorization layer, nor the Oracle may invent a value for a reserved field or a placeholder;
4. **post-hoc evidence rewriting is forbidden**: once published, the evidence artifact is never rewritten, normalized or repaired. If lineage binding is ever needed after the fact, it is supplied by a governance record, never by editing evidence;
5. no Path-E, Path-D, Oracle-R2, Recovery-R1, Recovery-R2 or D1 identity may be substituted for a Path-F identity anywhere in this lineage.

```
PATHF_AUTHORIZATION_PROVENANCE_COMPATIBILITY = COHERENT
```

---

## 4. Predecessor terminal boundaries (historical, NOT reusable)

Both predecessor lineages reached terminal states and are preserved as immutable history. Their identities are recorded here **only** so that the prohibitions are mechanically checkable and so that no executor can confuse the lineages.

### 4.1 Path-E terminal boundary

| Item | Frozen value |
| --- | --- |
| `oracle_path_e_commit` | `f7cafd83a95225e1ce9565a9336ded8575b65335` |
| `oracle_path_e_spec` | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.md` |
| `oracle_path_e_spec_sha256` | `78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b` |
| `oracle_path_e_script` | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.ps1` |
| `oracle_path_e_script_sha256` | `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb` |
| `path_e_authorization_design_commit` | `4900625114a38a86aa03a5fa4861c5bcd9436dc5` |
| `path_e_authorization_artifact` | `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_E_AUTHORIZATION.md` |
| `path_e_authorization_sha256` | `01d8dc6806e622cb361f47abee178e5beeddb8f95199ff21362938312a299d06` |
| `path_e_authorization_acceptance` | `48e9b66dd5aeb147795dbc57e822e6b3d38e4565` |
| `path_e_authorization_confirmation_record` | `c7ac36a8c596ae2ede8db7bce2e625f8c6ffa21c` |

```
PATH-E LINEAGE                       = EXHAUSTED / CLOSED
PATH-E AUTHORIZATION USE             = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
PATH-E ETB ATTEMPT                   = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
ORACLE-PATHE INVOCATIONS             = 1 OF 1 / MAXIMUM REACHED
RAW PATH-E ORACLE OBSERVATION        = ETB_UNSATISFIED
PATH-E RAW RESULT PROMOTION ELIGIBILITY = REJECTED / BLOCKED
PATH-E ETB SEMANTIC RESULT           = NONE
PATH-E RETRY AUTHORITY               = NONE
PATH-E RUNTIME OCCUPANCY             = 6 / 11
```

**Rule:** the Path-E spec, the Path-E executable, the Path-E authorization artifact, both Path-E claims and every Path-E runtime artifact are **frozen history**. This lineage may read them for provenance and must **never** execute, consume, delete, rewrite, move, repair, clean up or reference them as its own budget or namespace. `PATH-E RUNTIME OCCUPANCY = 6 / 11` is recorded as a boundary fact; this round neither reduces nor increases it and performs **no cleanup**.

### 4.2 Path-D terminal boundary

| Item | Frozen historical value |
| --- | --- |
| `oracle_path_d_commit` | `3276ef0bb0808ac10b2b82fca68ff282759856fe` |
| `oracle_path_d_spec` | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.md` |
| `oracle_path_d_spec_sha256` | `15e39452f5efae1f87f03e38fd72ca3336fe3b591affbd93c9104e785fa9884b` |
| `oracle_path_d_script` | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1` |
| `oracle_path_d_script_sha256` | `8bdeb434794c43fe4a199e7338790ba0dbd319728b6766d54299c894a16ac738` |
| `path_d_authorization_commit` | `29bf27fc2f76d415eb9c07d890f50b665aca6846` |
| `path_d_authorization_artifact` | `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_D_AUTHORIZATION.md` |
| `path_d_authorization_sha256` | `49e7c29a4c2367764aba195931908c627b9c7226725c76e66b1ef60eecb6f9bf` |
| `path_d_authorization_acceptance` | `a7e3cccf5fa50a127ce92c2ed3529da1e926d5ed` |
| `path_d_authorization_use_claim_sha256` | `5e33a8f3da06ba36582b357fb114011e51bae30cafae1449a9c90de59f3ef017` |
| `path_d_attempt_use_claim_sha256` | `64f86fcc7f3d63501b32dba5a5bf0905173002ee55d6ec008bed527472653db0` |

```
PATH-D                               = EXHAUSTED / CLOSED / IMMUTABLE
PATH-D AUTHORIZATION USE             = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
PATH-D ETB ATTEMPT                   = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
ORACLE-PATHD INVOCATIONS             = 1 OF 1 / MAXIMUM REACHED
PATH-D BOOKKEEPED OPERATIONAL OUTCOME = UNCLASSIFIED CONTROL FAILURE / NO ETB SEMANTIC RESULT / ACCEPTED / FROZEN AS GOVERNANCE HISTORY
PATH-D ETB SEMANTIC RESULT           = NONE
PATH-D EXECUTION OUTPUTS             = NONE
PATH-D RETRY AUTHORITY               = NONE
PATH-D ORACLE IMPLEMENTATION DEFECT  = YES / ACCEPTED / NOT REPAIRED
```

`UNCLASSIFIED CONTROL FAILURE` is a **Path-D governance phrase describing a control-layer outcome**, not an ETB semantic class, and it must not be resurrected as one (§17).

### 4.3 Reviewed predecessor defect carried forward (not repaired anywhere)

Oracle-PathD used `Get-FileHash` unprotected at predecessor lines 117/118 while its availability was only checked at line 189, whose gate list itself contains `Get-FileHash`, making that gate unreachable in exactly the scenario it exists to handle. The intended `HARNESS_INVALID` path was never reached, no evidence/manifest/result was published, no listener query and no target binding were reached, the attempt ended before any ETB semantics, and the process terminated with an undeclared exit code `1`. Oracle-PathF corrects the class of defect by never calling `Get-FileHash` at all. This authorization adds no further repair and must not modify either lineage's frozen artifacts.

### 4.4 Carried Path-E operational lessons (L1–L5) and their Path-F closure

| # | Lesson (accepted history) | Closed for Path-F by |
| --- | --- | --- |
| L1 | a pre-consumption claim-create failure was answered by a re-attempt under a mutated permission state instead of a fail-closed stop | §8 (frozen non-consuming-failure rule) and §7 (ACL policy) |
| L2 | an access-control list was mutated during the operational round | §7 and §13 PRE-16 … PRE-18 |
| L3 | authorization wording and Oracle specification wording used incompatible provenance rules | §3 and §19.4 of this artifact |
| L4 | runtime namespace occupancy was mis-reported (2/11 reported against 6/11 actual) | §14 (exact path rule) and the §13 PRE-13/PRE-14 accounting |
| L5 | the operational round required an escalated file-access mode | §6 and the §13 PRE-16 … PRE-18 prerequisites |

No lesson is closed by editing a frozen predecessor byte.

---

## 5. Authorization identity model

### 5.1 Identity fields

| Field | Value at design-candidate stage | Populated by |
| --- | --- | --- |
| `path_f_authorization_commit` | `<future independently accepted authorization-design commit>` | the later independent acceptance record — **never** an executor |
| `path_f_authorization_sha256` | `<committed-blob SHA-256 of docs/v0.3/V03E_G0_5_PRE_ETB_PATH_F_AUTHORIZATION.md>` | the later independent acceptance record — **never** an executor |
| `oracle_path_f_commit` | `a5d598a05a0467eea98cd0bf16e4486cceb72c23` | §2 (frozen) |
| `oracle_path_f_spec_sha256` | `b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5` | §2 (frozen) |
| `oracle_path_f_script_sha256` | `4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0` | §2 (frozen) |

**Rule:** an executor may **never** choose, compute-at-runtime, infer from `HEAD`, infer from this document's own revision, or guess `path_f_authorization_commit` or `path_f_authorization_sha256`. Both values must already exist as frozen text in the accepted control surfaces that `PRE-2` (§13) evaluates, written there by the independent acceptance and confirmation stages of the lifecycle frozen in §20. If either value is still a placeholder, the authorization is **not accepted** and no consumption may occur.

### 5.2 State model

```
DESIGN-CANDIDATE STATE (now)
  PATH-F AUTHORIZATION = CORRECTIVE SUCCESSOR DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / NOT EXECUTED
  PATH-F AUTHORIZATION USE = NOT AVAILABLE FOR CONSUMPTION
  PATH-F ETB ATTEMPT       = NOT AVAILABLE FOR CONSUMPTION
  ORACLE-PATHF INVOCATIONS = NOT AUTHORIZED

POST-CONFIRMATION STATE (only after §20 completes in order)
  PATH-F AUTHORIZATION = ACCEPTED / FROZEN / EFFECTIVE
  EXECUTION AUTHORITY  = GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY
  PATH-F AUTHORIZATION USE = 1 OF 1 / AVAILABLE FOR CONSUMPTION
  PATH-F ETB ATTEMPT       = 1 OF 1 / AVAILABLE FOR CONSUMPTION
  ORACLE-PATHF INVOCATIONS = 1 OF 1 / AVAILABLE ONLY AFTER BOTH CLAIMS EXIST

CONSUMED STATE (irreversible)
  PATH-F AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
  PATH-F ETB ATTEMPT       = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
  ORACLE-PATHF INVOCATIONS = 1 OF 1 / MAXIMUM REACHED
```

**Read this block as a projection, not as a current claim.** The three blocks above are **not simultaneous**. `DESIGN-CANDIDATE STATE (now)` is the live tracked state until every stage of §5.3 has completed. `POST-CONFIRMATION STATE` is the projected state at the **future** operational consumption point — after authorization acceptance, after independent confirmation and after materialization of that confirmation as a repository-verifiable record commit — and it must **not** be asserted, claimed or evaluated as true before then. `PRE-3` is the gate that reads that future state, and it separates the Oracle-PathF design effectivity layer from the Path-F execution-authorization effectivity layer from the consumable-claim layer; the requirement that the authorization be `non-effective` is a **design-candidate-stage** fact and a precondition must not require it at the operational moment.

### 5.3 Effectivity rule

This document is a **corrective successor design candidate**. It becomes effective **only** through the ordered lifecycle of §20: (1) qualifying third-party independent review in a different agent/session; (2) authorization acceptance bookkeeping in exactly one single-parent commit whose sole tracked delta is `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md`; (3) a fresh independent confirmation of that bookkeeping in a different agent/session; (4) materialization of that confirmation as a repository-verifiable record commit of the same two-file shape.

**No stage may be skipped, merged, collapsed, self-performed or performed by the same session twice.** Until every stage completes, **no** consumption, claim creation, listener query or Oracle invocation is permitted under this authorization.

### 5.4 No self-identity paradox (design-time elimination of the Path-E P2-1 defect)

This authorization is **not** required to contain its own future accepted commit identity or its own future accepted SHA-256, and it **does not** contain them. It carries the two explicit `<…>` placeholders of §5.1. The accepted control surfaces produced by the later lifecycle populate those values; the executor reads them and never invents them. Consequently:

```
SELF-IDENTITY REQUIREMENT ON THE DESIGN CANDIDATE = NONE
SELF-IDENTITY PARADOX = ABSENT BY CONSTRUCTION
```

### 5.5 Corrective-successor supersession, budget carry-forward and PRE-16 stop binding

```
OLD PATH-F AUTHORIZATION IDENTITY = ed112f8c5f1e35d87092d0339698a792ce0b145a / c147af8714164dae8b81cafa4eb01945a3ceb8c74b36f0fc18fbd56db284c4de
OLD PATH-F AUTHORIZATION STATE    = ACCEPTED / FROZEN / EFFECTIVE (historical, never rewritten) / OPERATIONALLY BLOCKED AFTER THE PRE-16 PRECONDITION STOP
NEW CORRECTIVE AUTHORIZATION      = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / NOT OPERATIONALLY USABLE
SUPERSESSION EFFECT               = PROSPECTIVE ONLY
```

The precondition stop that motivates this revision is bound as follows and is **not** re-litigated, re-reviewed or re-materialized here:

```
PATH-F OPERATIONAL EXECUTION = NOT STARTED
FIRST FAILED GATE            = PRE-16
PRE-1 … PRE-15               = PASS
PRE-16                       = FAIL
PRE-17                       = FAIL (dependent on PRE-16)
PRE-18                       = NOT REACHED
BLOCKER                      = REQUIRED FILE-ACCESS MODE NOT ESTABLISHED BEFORE IRREVERSIBLE SEQUENCE
CLAIM CreateNew ATTEMPTS     = 0
CLAIMS CREATED               = NONE
BUDGETS CONSUMED             = NONE
ORACLE INVOCATIONS           = 0
RAW PATH-F ETB RESULT        = NONE
HARNESS_INVALID              = NONE
DISPOSITION COMMIT           = 5fae11eefdcaddc27b4abf28d3a2258ad654d84d
PATHF_PRE16_STRUCTURAL_GAP   = CONFIRMED
REMEDIATION ROUTE            = ROUTE A
SAME-ROUND RETRY             = FORBIDDEN
AUTOMATIC RETRY UNDER UNCHANGED GOVERNANCE = FORBIDDEN
```

Rules frozen by this supersession model:

1. the previously accepted authorization's bytes, commit identity and acceptance history are **immutable**: they are never amended, rewritten, deleted, relabelled `REJECTED` / `INVALID` / `SUPERSEDED-INVALID`, or invalidated retroactively. Its acceptance remains historically valid; what is blocked is its operational **usability**;
2. this corrective successor is bound by the two external placeholders of §5.1/§5.4 exactly as its predecessor was — it embeds no future commit SHA and no future artifact SHA — and later acceptance governance binds the new corrective identity;
3. **budget carry-forward.** The lineage holds exactly **one** authorization-use budget and exactly **one** ETB-attempt budget, and they are the claim pairs at the frozen §14 paths. There is **no** second budget, **no** successor-budget path and **no** twelfth namespace member, because the eleven-path namespace and the claim schemas are frozen by the accepted Oracle-PathF specification §18 and by §10/§12/§14 of this artifact. Neither budget was consumed (`0 OF 1 / NOT CONSUMED`, `0 OF 1 / NOT STARTED`), so both remain numerically intact and carry forward to the **new** accepted corrective authorization identity, which supplies the identity binding for the *same* two claim paths once the §20 lifecycle completes;
4. the carry-forward is **not** an automatic reuse authority: the old identity may not be consumed under, and **no** operational round may run under either identity until the corrective successor is `ACCEPTED / FROZEN / EFFECTIVE`;
5. the claim writer of §12.3 binds the **new** accepted values — every future Path-F claim carries the corrective successor's accepted `authorization_commit` and `authorization_sha256`, and **never** `ed112f8c…` / `c147af87…`;
6. this design round creates, resets, replaces, decrements or releases **no** budget, and establishes **no** execution authority.

```
PATHF_CORRECTIVE_BUDGET_CARRY_FORWARD_MODEL = SAME LINEAGE-LEVEL ONE-SHOT BUDGETS CARRIED FORWARD, IDENTITY RE-BOUND TO THE NEW ACCEPTED CORRECTIVE AUTHORIZATION (NO SECOND BUDGET, NO RESET, NO AUTOMATIC REUSE)
```

**Precedent support:** in the Path-E corrective cycle the lineage's single authorization-use budget was consumed exactly once and bound the **corrected successor** identity `4900625114a38a86aa03a5fa4861c5bcd9436dc5` / `01d8dc6806e622cb361f47abee178e5beeddb8f95199ff21362938312a299d06`, not the superseded candidate `26b183083fbbe323441283f99f3cf2c931acd6ff`, and no second budget was created for the successor. This artifact applies the same single-budget, successor-bound shape. The Path-F-specific addition — the superseded identity had already reached `ACCEPTED / FROZEN / EFFECTIVE` while its budgets remained unconsumed — is resolved by rule 1 (history preserved intact) together with rules 3 and 4 (identity re-bound, no reuse authority on either identity until the §20 lifecycle completes). It creates no new budget class, no new claim path and no fourth ETB result class.

**Corrective-stage supersession chain (recorded; no historical object is erased, revoked, amended or relabelled):**

```
CORRECTIVE STAGE 0 — HISTORICAL AUTHORIZATION
  identity          = ed112f8c5f1e35d87092d0339698a792ce0b145a / c147af8714164dae8b81cafa4eb01945a3ceb8c74b36f0fc18fbd56db284c4de
  state             = ACCEPTED / FROZEN / EFFECTIVE / OPERATIONALLY BLOCKED AFTER THE PRE-16 PRECONDITION STOP
CORRECTIVE STAGE 1 — FIRST CORRECTIVE CANDIDATE
  identity          = d895856d2efc9683b91b182c33647efe57b01fc3 / c281f93e6ddfe09351c435e698c5d50c3a5cfcda2053f27159ba921e2eed72eb
  qualifying review = REQUEST_CHANGES (P0 = 0 / P1 = 0 / P2 = 1 / P3 = 4)
  sole blocking P2  = FULL_FILE_ACCESS_MODE_IDENTITY = LABEL_PRESENT_BUT_NOT_OPERATIONALLY_VERIFIABLE
  corrected PRE-16  = AMBIGUOUS
  state             = NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / SUCCEEDED PROSPECTIVELY BY THIS REVISION
  its bytes         = immutable history; not amended, not revoked, not relabelled, not deleted
CORRECTIVE STAGE 2 — THIS BOUNDED P2-REMEDIATION SUCCESSOR
  identity          = the single-parent successor commit of d895856d2efc9683b91b182c33647efe57b01fc3 that introduces this revision (not embedded here by design)
  state             = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / NOT OPERATIONALLY USABLE
```

The bounded revision is deliberately narrow: it corrects the canonical DSH mode token (§0 decision 13, §6.1), adds the deterministic session-mode observation mechanism (§6.4), rewrites `PRE-16` so that it is objectively and deterministically evaluable, and performs only the mechanical governance and cross-reference updates directly necessary to record those three changes. It does **not** reopen the budget model, the eleven-path namespace, the claim model, the provenance model, the result boundary, the `PRE-17` control-state clarification, the `PRE-18` no-re-attempt closure, or any other already-corrected area. A future Path-F claim binds the **new** accepted corrective identity only; it binds neither `ed112f8c…` / `c147af87…` nor the rejected candidate `d895856…` / `c281f93e…`.

---

## 6. Pre-consumption write-viability and execution-mode ownership

The accepted Oracle-PathF specification §7 already defines the Oracle's internal pre-publication write-viability gate, and §8/§9 define the ACL and execution-mode policy. This authorization **does not restate, reinterpret, weaken or extend** those Oracle internals. It defines only what the **authorization/executor layer** must establish so that a future authorized round begins in the execution/file-access mode the frozen Oracle design requires — concretely, in the canonical DSH mode `danger-full-access` (§6.1, §6.4, `PRE-16`).

### 6.1 Authorization-layer obligations: the concrete required mode, and capacity

**DSH canonical execution / file-access mode vocabulary (closed; recovered from the installed harness):**

```
read-only | workspace-write | danger-full-access
```

**The normative declaration of this authorization:**

```
REQUIRED PATH-F DSH OPERATIONAL EXECUTION / FILE-ACCESS MODE = danger-full-access
read-only                                                   = INSUFFICIENT FOR PATH-F OPERATIONAL EXECUTION
workspace-write                                             = INSUFFICIENT FOR PATH-F OPERATIONAL EXECUTION
danger-full-access                                          = REQUIRED PRE-EXISTING DSH OPERATIONAL EXECUTION MODE
```

`danger-full-access` is the **one and only** normative mode token of this authorization, and it is the **only** mode under which a Path-F operational round may begin. There is **no second source of truth**: every other mode reference in this artifact resolves to this token.

**Recovered DSH evidence for the token (all of it independently reproducible on this machine):** the installed DeepSeek Harness declares its mode type as `SandboxMode = 'read-only' | 'workspace-write' | 'danger-full-access'`; its permission presets map `read-only` and `workspace-write` to a confining sandbox with approval `ask` and `danger-full-access` to an unconfined sandbox with approval `never`; and its sandbox-policy plugin resolves the mode from `DSH_PERMISSION_MODE` in the **launching** harness process, defaulting to `workspace-write`. `danger-full-access` is therefore the canonical **unconfined** token, and no string outside the three above is a DSH mode at all.

It is a **pre-existing session mode**: the future operational executor must **start** its session already provisioned in `danger-full-access`. The executor must **not**:

- start in `workspace-write` (or in `read-only`) and "try";
- probe a claim path, a governed path or any other file in order to discover whether permissions work;
- request or acquire `danger-full-access` **after** a failure;
- invoke any elevation mechanism **after** the irreversible sequence begins;
- use the harness's per-call sandbox-escalation facility (`sandbox_permissions`), which is a **reactive** elevation path and is therefore **NOT AUTHORIZED** for any round governed by this authorization;
- mutate an access-control list, restore one, normalize one or repair permissions;
- use `icacls` or `Set-Acl`;
- create any authorization-layer empirical governed-path write probe.

If the session-visible DSH policy declaration of §6.4 does **not** unambiguously report `danger-full-access` when the preconditions are evaluated:

```
PRE-16 = FAIL
ROUND  = FAIL CLOSED BEFORE CONSUMPTION
NO CLAIM / NO BUDGET CONSUMPTION / NO ORACLE INVOCATION / NO RETRY
```

Before any irreversible claim consumption, the authorization layer must establish **capacity** — nothing more:

1. the session-visible DSH policy declaration reports the canonical mode **exactly `danger-full-access`**, through the non-mutating observation mechanism of §6.4, before any claim path is created;
2. the required execution/file-access mode is **already established** for the round, before any claim path is created;
3. **no ACL repair is planned, pending or in progress**;
4. the required mode was **not** obtained by modifying an access-control list and will not be repaired by modifying one;
5. the failure mode is **fail closed**, not repair-and-retry;
6. the mode is a **pre-existing environmental fact supplied before execution**: it is not a capability that this authorization, the executor, the Oracle or any helper may confer on itself;
7. **no execution-time elevation mechanism is authorized**, and **no reactive elevation authority or path is available to this Path-F round**.

**Prospective requirement versus reactive escalation:**

```
PROSPECTIVE EXECUTION-MODE REQUIREMENT = PERMITTED / REQUIRED
REACTIVE ESCALATION AFTER FAILURE      = FORBIDDEN
```

Stating the required mode in advance is exactly what the accepted Oracle-PathF specification §9.1/§9.2 requires of an execution-authorization record; it creates, delegates and implies **no** escalation authority, **no** permission-repair authority and **no** retry authority. What the frozen model forbids is the **reactive** elevation invoked after a failed gate or after the irreversible sequence begins (specification §9.3/§9.4; §6.2/§7 and PRE-16 … PRE-18 of this artifact). `danger-full-access` is a prerequisite **supplied to** the future execution environment by the Owner-governed operational session; it does **not** grant the authorization layer or the Oracle any ability to elevate itself. The requirement is `NO REACTIVE ELEVATION AUTHORITY OR PATH IS AVAILABLE TO THIS PATH-F ROUND`; it is **never** a requirement to prove that the host operating system contains no possible elevation facility.

### 6.2 Explicit non-ownership

This authorization layer must **not**:

- perform the Oracle's write-viability probe itself (that gate is Oracle-owned and runs inside the Oracle, after the bootstrap phase, before the config read and before any publication step);
- create any probe file, TEMP artifact, evidence, manifest or result artifact in order to test write viability;
- run any ACL command, read or enumerate any access-control list, or invoke any elevation mechanism;
- probe, query or enumerate the target, the listener or the endpoint;
- create any governed path before the PRE-gates pass;
- change, request or escalate its own execution/file-access mode, in any circumstance, including after a failed gate or a failed claim operation;
- rely on any shell environment variable to establish the mode — the mode is observed **only** through the DSH session runtime-context policy declaration of §6.4;
- treat the concrete mode requirement of §6.1 as a mandate to inspect, enumerate or modify any access-control list.

The Oracle's probe residue model is frozen and is **not** reconsidered here: probe files are named `.path-f-write-viability-probe-<guid>.tmp`, are outside the reserved namespace of §14, are non-governed, are non-consuming, confer no cleanup or retry authority, and a failed gate terminates the round.

### 6.3 Failure behaviour

```
REQUIRED EXECUTION / FILE-ACCESS MODE NOT ESTABLISHED BEFORE THE IRREVERSIBLE SEQUENCE
  -> PRE-16 = FAIL
  -> ROUND = FAIL CLOSED BEFORE CONSUMPTION
  -> NO CLAIM CREATION
  -> NO CLAIM CONSUMPTION
  -> NO ORACLE INVOCATION
  -> NO SAME-ROUND ACL REPAIR
  -> NO SAME-ROUND MODE CHANGE
  -> NO REACTIVE ESCALATION
  -> NO SAME-ROUND RETRY
  -> a later attempt requires a NEW explicit Owner-governed authority lifecycle
```

### 6.4 Deterministic session-mode observation (the non-mutating channel bound by `PRE-16`)

The DSH harness publishes the **effective** file/sandbox policy of a session into that session's own runtime context. The sandbox-policy owner contributes exactly one capability-neutral context entry named `sandbox:policy` to the **current runtime-context snapshot** of **every** agent session, and the agent loop logs that snapshot in the session as a sourced `user/message`. The entry is rendered from the session's resolved canonical mode and is a closed, verbatim set of exactly three literals:

```
Current DSH file policy: read-only. Any available operation enforced by the DSH file sandbox cannot modify files in the standing mode. Do not refuse a required modification from this policy alone: try an available tool normally and follow any denial and escalation guidance it returns.
Current DSH file policy: workspace-write. Any available operation enforced by the DSH file sandbox may modify files under the session workspace: "<workspace root>". Some platform temporary areas may also be writable.
Current DSH file policy: danger-full-access. The DSH file sandbox does not restrict file modifications by available operations.
```

**The required session-mode observation mechanism is therefore:**

```
DSH SESSION-MODE OBSERVATION CHANNEL
  = the `sandbox:policy` runtime-context declaration present in the CURRENT session,
    delivered as a sourced user/message whose text begins with the literal
    `Current DSH file policy: `
REQUIRED OBSERVED VALUE
  = the canonical token following that literal is exactly `danger-full-access`
FAIL-CLOSED ON
  = the declaration is absent, unreadable, or reports any other value
```

A future executor satisfies `PRE-16` **only** by reading that declaration in its own session and comparing the token. It must **not**:

- look for a shell environment variable: the harness consumes `DSH_PERMISSION_MODE` in the **launching** process to configure the sandbox and approval policies, and that variable is **not** guaranteed to be exported into the child shell — in the authoring environment of this revision it was demonstrably absent while `DSH_HOME`, `DSH_PROFILE`, `DSH_PROFILE_DIR`, `DSH_SESSION_ID`, `DSH_SHELL` and `DSH_WEB_URL` were present. No environment-variable test may be used as primary evidence, and no environment variable may be invented as one;
- query a registry, a configuration file, an access-control list, a permission descriptor or any other out-of-band surface;
- probe, write, create, delete or read back any file — including any claim path, governed path, TEMP artifact, probe file or runtime-namespace path — in order to discover the mode;
- invoke any elevation, escalation or approval facility in order to make the declaration report `danger-full-access`.

**The mode check is non-mutating by construction and must require:**

```
filesystem writes        = 0
claim-path accesses      = 0
governed-path probes     = 0
ACL reads                = 0
ACL mutations            = 0
permission repairs       = 0
runtime escalation       = 0
trial CreateNew calls    = 0
```

**Approval-policy corroboration (secondary only, never primary evidence):** the same resolved mode drives the harness approval policy — `danger-full-access` resolves it to `never`, while `read-only` and `workspace-write` resolve it to `ask`. A round may note that corroboration, but the **primary and only admissible evidence** is the session-visible policy declaration above.

**Fail-closed rule:**

```
session-visible policy declaration absent, unreadable or not exactly `danger-full-access`
  -> PRE-16 = FAIL
  -> ROUND = FAIL CLOSED BEFORE CONSUMPTION
  -> NO CLAIM / NO BUDGET CONSUMPTION / NO ORACLE INVOCATION / NO RETRY
  -> NO MODE SWITCHING / NO REACTIVE ESCALATION / NO PERMISSION REPAIR / NO ACL REPAIR
  -> a later attempt requires a NEW explicit Owner-governed authority lifecycle
```

This mechanism establishes **no** execution authority, consumes **no** budget and creates **no** governed path. It replaces, for this authorization, the earlier design-candidate wording that described the mode as verifiable "from the session's own execution environment" without naming the channel; `PRE-17` may rely on it and therefore needs no probe of its own (§13 `PRE-17`).

---

## 7. ACL and access-mode policy (closes the Path-E failure mode explicitly)

The authorization design states deterministically, for any future authorized operational round governed by it:

| Rule | State |
| --- | --- |
| ACL mutation during the authorized operational round | **FORBIDDEN** |
| ACL restoration / normalization during the authorized operational round | **FORBIDDEN** |
| permission repair after any failed gate | **FORBIDDEN** |
| sandbox / file-access escalation after the irreversible sequence begins | **FORBIDDEN** |
| reactive escalation after a failed gate, a failed claim operation or any other failure | **FORBIDDEN** |
| switching the session's execution/file-access mode during an operational round | **FORBIDDEN** |
| starting a Path-F operational round in any mode other than `danger-full-access` | **FORBIDDEN** — `PRE-16` fails closed |
| relying on a shell environment variable to establish the required mode | **NOT AUTHORITY** — the mode is observed only through the DSH session runtime-context policy declaration of §6.4 |
| using the harness per-call sandbox-escalation facility (`sandbox_permissions`) | **NOT AUTHORIZED** — a reactive elevation path (§6.1, `PRE-16`) |
| improvisational retry after an access failure | **FORBIDDEN** |
| `icacls` as part of execution | **NOT AUTHORIZED** |
| `Set-Acl` as part of execution | **NOT AUTHORIZED** |
| ACL-repair or permission-normalization scripts as part of execution | **NOT AUTHORIZED** |
| rollback / "undo" script as authority | **NOT AUTHORITY** |

If the required write/file-access viability is not established before the irreversible sequence, the round fails closed: no claim consumption, no Oracle invocation, no same-round repair, no same-round retry. A later attempt requires a **new explicit Owner-governed authority lifecycle**; it may not be improvised inside the failed round, and it may not be derived from a rollback script.

### 7.1 Current residual ACL condition

```
CURRENT ACL STATE = OUTSIDE TRACKED GIT GOVERNANCE / NOT NORMALIZED / NO RESTORATION AUTHORIZED BY THIS ROUND
ACL RESTORATION = OUT OF SCOPE FOR THIS ROUND AND FOR ANY ROUND GOVERNED BY THIS AUTHORIZATION UNTIL SEPARATELY AUTHORIZED
```

This design round **documents** the residual condition and **mutates nothing**. It authorizes no normalization, no restoration and no repair. A future operational round must begin in a mode that is already viable — concretely, in `danger-full-access`, observed through the session-visible DSH policy declaration of §6.4 (§6.1, `PRE-16`) — and it may not create viability by mutating permissions, by escalating reactively or by switching modes after a failure.

---

## 8. No pre-consumption re-attempt (closes Path-E lesson L1)

The following semantics are frozen at design time rather than left to interpretation:

### 8.1 Authorization-claim failure

If the authorization claim TEMP `CreateNew` fails **before** the file is created:

```
BUDGET CONSUMPTION FOR THAT FAILED CLAIM = NO
ROUND OUTCOME = TERMINATED / FAIL CLOSED
SAME-ROUND RE-ATTEMPT = FORBIDDEN
RETRY AFTER A PERMISSION CHANGE = FORBIDDEN
```

### 8.2 Attempt-claim failure

If the attempt claim TEMP `CreateNew` fails **before** the file is created:

```
BUDGET CONSUMPTION FOR THAT FAILED CLAIM = NO
ROUND OUTCOME = TERMINATED / FAIL CLOSED
SAME-ROUND RE-ATTEMPT = FORBIDDEN
RETRY AFTER A PERMISSION CHANGE = FORBIDDEN
AUTHORIZATION BUDGET REMAINS SPENT IF ITS OWN TEMP CLAIM WAS CREATED
```

### 8.3 The governing semantic rule

```
NON-CONSUMING FAILURE DOES NOT MEAN RE-ATTEMPT AUTHORITY
```

An unconsumed budget is **not** an available budget after a failed round: the round is over, fail-closed, and any further attempt requires a new Owner-governed lifecycle. There is no "the claim was never created, so try again" path, no `Start-Sleep`-and-retry, no alternate port, no alternate path, no "fix the permission and re-run", and no interpretation gap of the kind Path-E exhibited.

---

## 9. Budget model (design only — nothing is created in this round)

Three separate one-shot authorities are designed. **None exists**, and none is available for consumption, as a result of this round.

### 9.1 A. PATH-F AUTHORIZATION-USE BUDGET

| Property | Value |
| --- | --- |
| Initial state | `NOT CREATED / NOT AVAILABLE FOR CONSUMPTION` |
| Future availability condition | this authorization design is independently reviewed, accepted, confirmed and materialized per §20, and every PRE-gate of §13 passes |
| Exact irreversible consumption event | successful `[System.IO.FileMode]::CreateNew` of `docs/v0.3/evidence/ETB_PATH_F_AUTHORIZATION_USE.claim.tmp` |
| Claim identity | `ETB_PATH_F_AUTHORIZATION_USE.claim` (+ `.tmp`) |
| TEMP / FINAL semantics | TEMP creation is the consumption record; FINAL is the published immutable marker; a failure after TEMP creation leaves TEMP in place as evidence |
| Post-consumption state | `1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE` |
| Failure behavior | §8.1 |
| No-reuse / no-reset / no-retry | `NO REUSE` / `NO RESET` / `NO RETRY` |

### 9.2 B. PATH-F ETB-ATTEMPT BUDGET

| Property | Value |
| --- | --- |
| Initial state | `NOT CREATED / NOT AVAILABLE FOR CONSUMPTION` |
| Future availability condition | the authorization-use budget was already consumed in the same authorized round |
| Exact irreversible consumption event | successful `[System.IO.FileMode]::CreateNew` of `docs/v0.3/evidence/ETB_PATH_F_ATTEMPT_USE.claim.tmp` |
| Claim identity | `ETB_PATH_F_ATTEMPT_USE.claim` (+ `.tmp`) |
| Post-consumption state | `1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE` |
| Failure behavior | §8.2 |
| No-reuse / no-reset / no-retry | `NO REUSE` / `NO RESET` / `NO RETRY` |

### 9.3 C. ORACLE-PATHF INVOCATION AUTHORITY

| Property | Value |
| --- | --- |
| Initial state | `NOT AUTHORIZED` |
| Future availability condition | both claim budgets were consumed in the same authorized round |
| Exact consumption event | the single permitted invocation of the accepted Oracle-PathF executable |
| Maximum | `1 OF 1 / MAXIMUM REACHED` |
| Failure behavior | a failed or aborted invocation still counts as the maximum |
| No-reuse / no-reset / no-retry | `NO REUSE` / `NO RESET` / `NO RETRY` |

### 9.4 Expected future successful consumption semantics

```
AUTHORIZATION USE       = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
ETB ATTEMPT             = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
ORACLE-PATHF INVOCATION = 1 OF 1 / MAXIMUM REACHED
```

### 9.5 This round creates nothing

```
PATH-F AUTHORIZATION-USE BUDGET = NOT CREATED / NOT AVAILABLE FOR CONSUMPTION
PATH-F ETB-ATTEMPT BUDGET       = NOT CREATED / NOT AVAILABLE FOR CONSUMPTION
ORACLE-PATHF INVOCATION         = NOT AUTHORIZED
PATH-F EXECUTION AUTHORITY      = NONE
```

No budget is created, allocated, reserved, decremented, consumed or made available by this design round. The three authorities above are **design descriptions of a future, separately authorized round**, not current capabilities.

**Carry-forward note (added by this corrective revision).** The lineage's two one-shot budgets already exist as the unconsumed claim pairs of the previously accepted authorization (`0 OF 1 / NOT CONSUMED`, `0 OF 1 / NOT STARTED`). Per §5.5 they remain numerically intact and are carried forward to the **new** accepted corrective authorization identity, with no second budget, no reset and no automatic reuse authority: they become available **only** once the corrective successor completes the §20 lifecycle and the `PRE-*` gates pass. Nothing in this note creates, restores or releases a budget today.

---

## 10. Claim identity and namespace (Path-F)

This lineage introduces exactly **two** budget claims and no others, at exactly these four paths:

| Item | Path |
| --- | --- |
| authorization-use TEMP | `docs/v0.3/evidence/ETB_PATH_F_AUTHORIZATION_USE.claim.tmp` |
| authorization-use FINAL | `docs/v0.3/evidence/ETB_PATH_F_AUTHORIZATION_USE.claim` |
| attempt-use TEMP | `docs/v0.3/evidence/ETB_PATH_F_ATTEMPT_USE.claim.tmp` |
| attempt-use FINAL | `docs/v0.3/evidence/ETB_PATH_F_ATTEMPT_USE.claim` |

Both files live directly in `docs/v0.3/evidence/` — **not** inside the Path-F runtime output directory of §14 — because a claim is a control object and must remain inspectable even if no output directory is ever created. These four paths are members of the frozen 11-path Path-F namespace of §14 and are counted in its occupancy arithmetic.

**At design-candidate stage all four paths are ABSENT**, verified by the §11 predicate, and they must remain absent until an executor legitimately consumes the corresponding budget. Creating any of them by any other means (manually, by an earlier design or review round, by copying a Path-D or Path-E claim, or by a "readiness" step) is a control failure, not a consumption, and it **blocks** the round rather than enabling it.

These paths are permanently distinct from the Path-D namespace (`ETB_PATH_D_*`), the Path-E namespace (`ETB_PATH_E_*`), the Recovery-R1, Recovery-R2 and D1 claim namespaces, and the original claim namespace. **No historical claim path may be reused, deleted, renamed, moved or counted as a Path-F budget.**

---

## 11. Claim-path occupancy predicate

The occupancy predicate is identity-based and deterministic; it never depends on file size, content, timestamps or directory-enumeration order:

```powershell
function Test-DevRelayPathFOccupied {
    param([Parameter(Mandatory)][string]$Path)
    return ([System.IO.File]::Exists($Path) -or [System.IO.Directory]::Exists($Path))
}
```

An executor must evaluate this predicate for **all eleven** reserved Path-F paths of §14 and for both claim TEMP/FINAL pairs before consuming anything. A file, a directory, a partial file, a malformed file or a zero-length file at one of those exact paths counts as **OCCUPIED** and fails closed.

The required design-time and pre-consumption state is:

```
PATH-F RUNTIME OCCUPANCY = 0 / 11
```

If any reserved path exists, the authorization is **not** consumable and the executor must fail closed without consuming a budget. No deletion, no cleanup, no overwrite and no rename exists as a remedy.

---

## 12. Claim schemas and the frozen claim writer

### 12.1 Authorization-use claim schema

**Schema identity:** `devrelay-etb-path-f-authorization-use-v1`

The claim is an ordered, closed, single-line JSON object serialized as UTF-8 **without BOM**, with **exactly one** terminating LF, no indentation and no extra field:

| # | Field | Required value |
| --- | --- | --- |
| 1 | `schema_version` | `devrelay-etb-path-f-authorization-use-v1` |
| 2 | `authorization_commit` | `path_f_authorization_commit` (§5.1, frozen text — never computed at runtime) |
| 3 | `authorization_sha256` | `path_f_authorization_sha256` (§5.1, frozen text — never computed at runtime) |
| 4 | `oracle_path_f_commit` | `a5d598a05a0467eea98cd0bf16e4486cceb72c23` |
| 5 | `oracle_path_f_spec_sha256` | `b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5` |
| 6 | `oracle_path_f_script_sha256` | `4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0` |
| 7 | `state` | `CONSUMED` |

### 12.2 Attempt-use claim schema

**Schema identity:** `devrelay-etb-path-f-attempt-use-v1`

| # | Field | Required value |
| --- | --- | --- |
| 1 | `schema_version` | `devrelay-etb-path-f-attempt-use-v1` |
| 2 | `authorization_commit` | `path_f_authorization_commit` (§5.1, frozen text — never computed at runtime) |
| 3 | `authorization_sha256` | `path_f_authorization_sha256` (§5.1, frozen text — never computed at runtime) |
| 4 | `oracle_path_f_commit` | `a5d598a05a0467eea98cd0bf16e4486cceb72c23` |
| 5 | `oracle_path_f_spec_sha256` | `b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5` |
| 6 | `oracle_path_f_script_sha256` | `4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0` |
| 7 | `state` | `CONSUMED` |

Both schemas differ **only** in field 1. This is deliberate: an attempt may not be consumable unless its authorization was consumed first under the same frozen identities. Field order is part of the contract. No field may be added, removed, reordered, truncated, padded, uppercased or reformatted. Hex digests are lowercase. Neither claim is self-referential: each identifies this authorization and the accepted Oracle-PathF design, never itself.

### 12.3 Exact frozen claim writer source

The following function is the **frozen, verbatim** consumption primitive. An executor must not re-implement it, wrap it, parameterize it differently, "improve" it, add retry logic to it, or use any other publication method. It is the only permitted way either claim may be created.

```powershell
function Write-DevRelayPathFOneShotClaim {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$TempPath,
        [Parameter(Mandatory)][string]$FinalPath,
        [Parameter(Mandatory)][string]$SchemaVersion,
        [Parameter(Mandatory)][string]$AuthorizationCommit,
        [Parameter(Mandatory)][string]$AuthorizationSha256,
        [Parameter(Mandatory)][string]$OraclePathFCommit,
        [Parameter(Mandatory)][string]$OraclePathFSpecSha256,
        [Parameter(Mandatory)][string]$OraclePathFScriptSha256
    )

    $ErrorActionPreference = 'Stop'

    if ([System.IO.File]::Exists($TempPath) -or [System.IO.Directory]::Exists($TempPath)) {
        throw 'DEVRELAY_CLAIM_ALREADY_PRESENT_TEMP'
    }
    if ([System.IO.File]::Exists($FinalPath) -or [System.IO.Directory]::Exists($FinalPath)) {
        throw 'DEVRELAY_CLAIM_ALREADY_PRESENT_FINAL'
    }

    $payload = [ordered]@{
        schema_version              = $SchemaVersion
        authorization_commit        = $AuthorizationCommit
        authorization_sha256        = $AuthorizationSha256
        oracle_path_f_commit        = $OraclePathFCommit
        oracle_path_f_spec_sha256   = $OraclePathFSpecSha256
        oracle_path_f_script_sha256 = $OraclePathFScriptSha256
        state                       = 'CONSUMED'
    }

    $json = $payload | ConvertTo-Json -Depth 4 -Compress
    $text = $json + "`n"
    $bytes = (New-Object System.Text.UTF8Encoding($false)).GetBytes($text)

    $stream = New-Object System.IO.FileStream($TempPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
    try {
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    }
    finally {
        $stream.Dispose()
    }

    $readBack = [System.IO.File]::ReadAllBytes($TempPath)
    if ($readBack.Length -ne $bytes.Length) { throw 'DEVRELAY_CLAIM_TEMP_LENGTH_MISMATCH' }
    for ($i = 0; $i -lt $bytes.Length; $i++) {
        if ($readBack[$i] -ne $bytes[$i]) { throw 'DEVRELAY_CLAIM_TEMP_BYTE_MISMATCH' }
    }
    if ($readBack[$readBack.Length - 1] -ne 10) { throw 'DEVRELAY_CLAIM_TEMP_NO_FINAL_LF' }
    if ($readBack.Length -ge 3 -and $readBack[0] -eq 239 -and $readBack[1] -eq 187 -and $readBack[2] -eq 191) { throw 'DEVRELAY_CLAIM_TEMP_BOM' }

    [System.IO.File]::Move($TempPath, $FinalPath)

    $finalBack = [System.IO.File]::ReadAllBytes($FinalPath)
    if ($finalBack.Length -ne $bytes.Length) { throw 'DEVRELAY_CLAIM_FINAL_LENGTH_MISMATCH' }
    for ($i = 0; $i -lt $bytes.Length; $i++) {
        if ($finalBack[$i] -ne $bytes[$i]) { throw 'DEVRELAY_CLAIM_FINAL_BYTE_MISMATCH' }
    }
}
```

**Frozen properties of this primitive (each is part of the contract):**

1. existence is checked for **both** TEMP and FINAL before any write, and either presence throws;
2. the temp file is created with `CreateNew` **and** `FileShare::None`, so no concurrent or repeated creation can succeed;
3. JSON is produced at frozen depth `4` in compressed form, followed by exactly one LF;
4. encoding is UTF-8 without BOM;
5. bytes are flushed to disk (`Flush($true)`) before read-back;
6. the temp file is verified byte-for-byte, for terminal LF and for absence of BOM **before** publication;
7. publication uses the two-argument `[System.IO.File]::Move` overload, which fails if the destination exists — there is no overwrite path;
8. the FINAL file is verified byte-for-byte after publication;
9. **no failure path deletes, truncates, moves or rewrites any file**, and a failure after TEMP creation leaves the TEMP claim in place as evidence of consumption;
10. the primitive performs **no** retry, **no** cleanup, **no** logging to the network and **no** interaction with the Oracle.

Throwing this primitive is never a `HARNESS_INVALID`, never `ETB_UNSATISFIED`, never `ETB_SATISFIED` and never a fourth ETB semantic class: it is an **authorization-layer control failure** (§16).

---

## 13. Pre-consumption preconditions (PRE-1 … PRE-18)

All eighteen preconditions are **mandatory, ordered and fail-closed**. An executor evaluates them in order; the **first** failure stops the round. Preconditions are evaluated **before** any claim file is created and **before** any Oracle invocation. A precondition failure consumes **no** budget and creates **no** artifact: `PATH-F AUTHORIZATION USE = 0 OF 1 / NOT CONSUMED`, `PATH-F ETB ATTEMPT = 0 OF 1 / NOT STARTED`, `ORACLE-PATHF INVOCATIONS = 0`.

**Why eighteen and not fifteen:** the recovered Path-D and Path-E candidates froze a fifteen-row family whose content this design preserves in substance. Path-F must additionally satisfy two requirements that no predecessor row covers — the explicit pre-consumption **write-viability / ACL / execution-mode** boundary (specification §7, §8, §9; lessons L2 and L5) and the explicit **non-consuming-failure / no-re-attempt** prerequisite. Rather than overload an existing row or invent an unnumbered rule, this design adds exactly three rows, `PRE-16`, `PRE-17` and `PRE-18`, and states the count explicitly. No predecessor semantic is dropped, renumbered or weakened.

| ID | Precondition | Required evidence |
| --- | --- | --- |
| **PRE-1** | Repository, branch and governance base are the expected ones | repository root `D:\DevRelay`; branch `v0.3-e-recovery-reconciliation`; the accepted Oracle-PathF design acceptance bookkeeping commit `7ad12d1d0b9727548b271981116267f76c362f48` and its confirmation-materialization successor `1d06f2857840b9f4096bbedc156e3ac4c9eaddec` are ancestors of `HEAD`; `HEAD` is on the accepted governance line and is **not** a detached or unrelated state |
| **PRE-2** | Authorization artifact self-identity is frozen and matches the committed blob | `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_F_AUTHORIZATION.md` exists; its committed-blob SHA-256 equals the accepted `path_f_authorization_sha256`; `path_f_authorization_commit` is a committed ancestor of `HEAD` whose sole tracked delta against its parent is `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md` and the new artifact path — the accepted control surfaces already contain populated, frozen values for both `path_f_authorization_commit` and `path_f_authorization_sha256`, populated **only** through the authorization acceptance / confirmation lifecycle of §5.3, with **no unresolved angle-bracket placeholder remaining in those accepted surfaces** — and the executor did **not** choose, guess, infer from `HEAD` or rewrite either value. The **design-candidate** revision of this document is **not** required to contain its own future accepted values: a design candidate necessarily carries the two explicit placeholders of §5.1, and neither the design candidate nor the executor may rewrite this artifact to substitute them. The corrected revision of the artifact — **not** the design-candidate revision — is the artifact bound by the frozen values above |
| **PRE-3** | Oracle-PathF design effectivity, Path-F execution-authorization effectivity and consumable state are each satisfied at the future operational consumption point | this gate is evaluated at the **future** operational consumption point — immediately before the **first** irreversible authorization-use claim create — and is deliberately **not** evaluated at the design-candidate stage of this document. Three distinct states must simultaneously hold, each in its own layer: **(A) Oracle-PathF design effectivity:** the tracked status surfaces state `ORACLE-PATHF DESIGN = ACCEPTED / FROZEN / EFFECTIVE`, `QUALIFYING THIRD-PARTY PATH-F DESIGN REVIEW = APPROVED`, and the Oracle-PathF design acceptance bookkeeping `7ad12d1…` is confirmed by its materialization record `1d06f28…`; **(B) Path-F execution-authorization effectivity:** the accepted control surfaces state `PATH-F AUTHORIZATION = ACCEPTED / FROZEN / EFFECTIVE` with `EXECUTION AUTHORITY = GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY`; **(C) consumable state:** `PATH-F AUTHORIZATION USE = 1 OF 1 / AVAILABLE FOR CONSUMPTION` and `PATH-F ETB ATTEMPT = 1 OF 1 / AVAILABLE FOR CONSUMPTION` per §5.2, both **available but not yet consumed** — zero Path-F claims yet created — while `PATH-F RUNTIME OCCUPANCY = 0 / 11`. The requirement that the authorization be `non-effective` applies to the **design-candidate** stage only — it is the current state, recorded in §5.2 and in the live-state surface §23 — and must **not** be required at this gate. `ORACLE-PATHF INVOCATIONS = 1 OF 1` becomes available only after both claims exist, and its revocation of availability is not required here |
| **PRE-4** | Oracle-PathF executable blob identity is exact | the blob of `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.ps1` at the accepted design commit `a5d598a05a0467eea98cd0bf16e4486cceb72c23`, at `HEAD`, in the index and in the worktree is the **same** blob, whose SHA-256 is `4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0` |
| **PRE-5** | Oracle-PathF specification blob identity is exact | the blob of `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.md` at the accepted design commit, at `HEAD`, in the index and in the worktree is the **same** blob, whose SHA-256 is `b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5` |
| **PRE-6** | Working tree is byte-identical to `HEAD` for the governed artifacts | `git status --porcelain` reports no modification, deletion, rename or staged change for the two accepted Oracle-PathF artifacts, the authorization artifact itself, or any governed control surface; no unmerged path exists |
| **PRE-7** | Line-ending attributes resolve as frozen | `git check-attr text eol -- docs/v0.3/V03E_G0_5_PRE_ETB_PATH_F_AUTHORIZATION.md docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.ps1 docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.md` reports `text: set` and `eol: lf` for each path (no wildcard rule may be relied on for the executable) |
| **PRE-8** | No reviewed, accepted or frozen artifact has been modified | every identity in §2 and §4, `.gitattributes`, the accepted Oracle-PathF spec and executable, the Path-E spec/executable/authorization and both Path-E claims, the Path-D spec/executable/authorization and both Path-D claims, and all historical governance commits are byte-unchanged |
| **PRE-9** | Configuration file identity is exact | `.devrelay/config.yaml` has SHA-256 `b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf` and `1897` bytes |
| **PRE-10** | Configuration-establishment evidence identity is exact | `docs/v0.3/evidence/etb-execution/CONFIG_ESTABLISHMENT.json` has SHA-256 `ea9fc2bc564cfd6d613e3145703f28d80bb87eb89dcdecaf7ad43b52d7bd9300` and `1031` bytes |
| **PRE-11** | Historical markers are intact and unclaimed | every historical budget in §4.1 and §4.2 is still recorded as spent/closed; no historical claim, evidence, manifest or result file has been modified, deleted or added; the two Path-D claims remain byte-identical with SHA-256 `5e33a8f3da06ba36582b357fb114011e51bae30cafae1449a9c90de59f3ef017` and `64f86fcc7f3d63501b32dba5a5bf0905173002ee55d6ec008bed527472653db0`; the Path-E namespace remains `6 / 11` with no Path-E artifact added, removed, repaired or cleaned |
| **PRE-12** | All four Path-F claim paths are absent | `ETB_PATH_F_AUTHORIZATION_USE.claim{,.tmp}` and `ETB_PATH_F_ATTEMPT_USE.claim{,.tmp}` are all absent per the §11 predicate |
| **PRE-13** | The reserved Path-F runtime/output and control namespace is empty | all eleven paths of §14 are absent under the §11 predicate: `PATH-F RUNTIME OCCUPANCY = 0 / 11` |
| **PRE-14** | No prior Path-F authorization or attempt consumption has occurred | neither Path-F claim exists in any form; no Path-F evidence, manifest or result exists; no Path-F budget is recorded as consumed anywhere in the tracked surfaces; the round that performs this evaluation is the **first** Path-F round to reach the consumption boundary |
| **PRE-15** | No execution has occurred in this round before the preconditions passed | the executor has performed **zero** Oracle invocations, **zero** ETB attempts, **zero** listener queries, **zero** target probes, **zero** endpoint probes and **zero** OpenCode starts before PRE-1 … PRE-14 have all passed |
| **PRE-16** | The session-visible DSH session-policy declaration reports the canonical mode exactly `danger-full-access`, provisioned before the irreversible sequence, with no ACL or permission repair pending and no reactive elevation path available | this row is **objectively and deterministically evaluable**: every clause is a comparison against a stated token or a stated absence, requiring no judgement, no interpretation and no empirical test. All eight clauses must hold, and each must be established **before** any claim path is created: **(1)** the DSH-provided, non-mutating session policy declaration of the **current** session — the `sandbox:policy` runtime-context entry of §6.4, whose text begins with the literal `Current DSH file policy: ` — reports the canonical mode **exactly `danger-full-access`**; **(2)** that mode was **provisioned before the Path-F operational round entered the irreversible sequence** — it is a pre-existing session mode, not something acquired at or after that point; **(3)** the mode was **not** obtained or requested as a response to any failed Path-F PRE gate, claim operation, Oracle action or runtime failure; **(4)** **no ACL repair** is planned, pending or active; **(5)** **no permission repair** is planned, pending or active; **(6)** **no reactive execution-time elevation path is authorized** for this round — `icacls`, `Set-Acl`, any ACL-repair or permission-normalization script, and the harness per-call sandbox-escalation facility (`sandbox_permissions`) are all excluded from it; **(7)** the mode check uses **only** the recovered non-mutating DSH session-policy observation mechanism of §6.4, and it requires **zero** filesystem writes, **zero** claim-path accesses, **zero** governed-path probes, **zero** ACL reads, **zero** ACL mutations, **zero** permission repairs, **zero** runtime escalation and **zero** trial `CreateNew` calls; **(8)** **inability to observe or establish the exact canonical token is `PRE-16 = FAIL`** — not a licence to test the mode, not a licence to switch modes and not a licence to escalate. The requirement is `NO REACTIVE ELEVATION AUTHORITY OR PATH IS AVAILABLE TO THIS PATH-F ROUND`; it is **never** a requirement to prove that the host operating system contains no possible elevation facility. A round that cannot satisfy this row fails closed — `ROUND = FAIL CLOSED BEFORE CONSUMPTION`, with no claim creation, no budget consumption, no Oracle invocation, no retry, no mode switching, no reactive escalation, no permission repair and no ACL repair |
| **PRE-17** | Write-viability control state is established without consuming authority, without creating a governed path and without any empirical write probe | this row is a **control-state / capacity** gate, and it is **satisfied by `PRE-16` having already confirmed `danger-full-access`** through the session-visible DSH policy declaration of §6.4, together with the frozen publication contract: with the session-visible policy reporting `danger-full-access`, the round's ability to create, write, flush and read back the claim files and the runtime outputs is a **control-state fact of the established mode**, and it must **never** be established by creating, writing, flushing or reading back any file. This row therefore requires **no file creation of any kind** by the authorization layer: **no** probe file, **no** TEMP artifact, **no** claim, **no** evidence, **no** manifest, **no** result, **no** runtime-namespace entry and **no** write to any governed path may be performed to satisfy it. It performs **no** probe on the Oracle's behalf, consumes **no** budget and creates **no** governed artifact. The Oracle's own pre-publication write-viability gate of the accepted specification §7 remains exclusively Oracle-owned, runs inside the Oracle after the bootstrap phase and before the config read, and is **not** re-specified, pre-empted, replaced or duplicated here. Probe residue, if the **Oracle** ever creates any, remains outside the §14 namespace, is non-governed and non-consuming, is **not** a claim, an attempt or a budget-consumption event, and is **not** subject to cleanup or retry authority. This row must remain satisfiable **after** `PRE-16` has confirmed `danger-full-access` through the session-visible policy channel, and it may never be read as requiring an empirical governed-path write test |
| **PRE-18** | Non-consuming failure confers no re-attempt authority | the executor has accepted, before entering the irreversible sequence, that a `CreateNew` failure that occurs **before** the TEMP file is created consumes **no** budget **and nevertheless terminates the round** (§8): consumption `NO`, outcome `TERMINATED / FAIL CLOSED`, same-round re-attempt `FORBIDDEN`, retry after a permission change `FORBIDDEN`, **changing the session's execution/file-access mode to answer the failure `FORBIDDEN`**, **reactive escalation in response to the failure `FORBIDDEN`**, and any further attempt requires a **new explicit Owner-governed authority lifecycle**. A round that has already suffered such a failure may not continue under this authorization |

### 13.1 Ownership boundary frozen by the preconditions

The following belong **exclusively** to the accepted Oracle-PathF executable and are **forbidden** to the authorization layer, to the executor's orchestration, and to any helper, wrapper, diagnostic, "readiness" or "pre-check" step:

listener query; config comparison against the live endpoint; `OwningProcess` resolution; PID resolution; `Win32_Process` lookup; `ExecutablePath` retrieval; `CreationDate` retrieval; target executable hashing; package identity validation; `package.json` validation; `CreateFileW` / `GetFinalPathNameByHandleW` canonicalization; S0 and S1 snapshot acquisition; S0/S1 continuity evaluation; the pre-publication write-viability gate itself; and **all** ETB result classification.

The authorization layer may verify **only** static artifact identity (PRE-2, PRE-4, PRE-5, PRE-6, PRE-7, PRE-9, PRE-10), governance/precondition state (PRE-1, PRE-3, PRE-8, PRE-11 … PRE-15, PRE-18) and the already-established execution-mode capacity (PRE-16, PRE-17) — where the mode itself is read from the DSH session runtime-context policy declaration of §6.4 and from nothing else. Hashing of the **accepted Oracle-PathF artifacts themselves** is permitted and required; hashing, opening, probing or enumerating the **target** is not.

### 13.2 Non-contradiction of PRE-2 and PRE-3

`PRE-2` requires frozen accepted values that **exist only after** the acceptance/confirmation lifecycle; it therefore cannot and does not require the design candidate to contain them. `PRE-3` requires the authorization to be `ACCEPTED / FROZEN / EFFECTIVE` **at the future operational moment**; it therefore cannot and does not require the design candidate to be non-effective at that same moment. Both rows are satisfiable in the state in which they are evaluated — the Path-E `P2-1` and `P2-2` findings are eliminated by construction, not by wording.

```
PRE_GATE_MODEL = CLOSED / COMPLETE
```

This statement describes the candidate's own structure — fifteen preserved rows plus three Path-F-specific rows, no gaps and no unreachable row — and is **not** a review verdict or an acceptance.

---

## 14. Path-F runtime namespace (exactly eleven paths)

The frozen namespace is quoted from the accepted Oracle-PathF specification §18 and binds exactly:

| # | Reserved path | State at design-candidate stage |
| --- | --- | --- |
| 1 | `docs/v0.3/evidence/ETB_PATH_F_AUTHORIZATION_USE.claim` | ABSENT |
| 2 | `docs/v0.3/evidence/ETB_PATH_F_AUTHORIZATION_USE.claim.tmp` | ABSENT |
| 3 | `docs/v0.3/evidence/ETB_PATH_F_ATTEMPT_USE.claim` | ABSENT |
| 4 | `docs/v0.3/evidence/ETB_PATH_F_ATTEMPT_USE.claim.tmp` | ABSENT |
| 5 | `docs/v0.3/evidence/etb-execution-path-f/` (directory) | ABSENT |
| 6 | `docs/v0.3/evidence/etb-execution-path-f/ETB_EVIDENCE.json` | ABSENT |
| 7 | `docs/v0.3/evidence/etb-execution-path-f/ETB_EVIDENCE.json.tmp` | ABSENT |
| 8 | `docs/v0.3/evidence/etb-execution-path-f/MANIFEST.sha256` | ABSENT |
| 9 | `docs/v0.3/evidence/etb-execution-path-f/MANIFEST.sha256.tmp` | ABSENT |
| 10 | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_F.md` | ABSENT |
| 11 | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_F.md.tmp` | ABSENT |

```
PATH-F RUNTIME NAMESPACE = 11 PATHS
PATH-F RUNTIME OCCUPANCY = 0 / 11
```

Occupancy accounting is **by path, exactly as listed**: a directory counts as one occupied path member, and a TEMP path is a distinct path member from its FINAL counterpart. This rule is stated so that the Path-E lesson L4 accounting variance cannot recur.

**No twelfth governed runtime path may be added.** No Path-E or Path-D output path may be referenced, reused, cleaned, repaired or written anywhere in this lineage. The future evidence schema identity is `devrelay-etb-v1-path-f`.

The authorization-design artifact of this round (`docs/v0.3/V03E_G0_5_PRE_ETB_PATH_F_AUTHORIZATION.md`) and the two accepted Oracle-PathF artifacts are **not** members of this runtime namespace: they are tracked governance and design artifacts, not runtime outputs.

---

## 15. No target pre-probe

**Prohibited by this authorization, absolutely and without exception, before the Oracle is entered and outside the Oracle:**

`Get-NetTCPConnection`; `netstat`; any TCP connection enumeration; any port-4096 probe or scan; any `localhost` probe; any `127.0.0.1` probe; any IPv6-loopback probe; any endpoint reachability check; any HTTP or HTTPS request; any `/doc`, `/session`, `/openapi.json` or equivalent endpoint call; `Test-NetConnection`; `Invoke-WebRequest`; `Invoke-RestMethod`; `curl`; `wget`; `Get-CimInstance` or `Get-WmiObject` target binding; `Get-Process` discovery of the target; `OpenCode --version` or any OpenCode start, restart or CLI query; `Get-FileHash` on the target binary; `CreateFileW` / `GetFinalPathNameByHandleW` on the target; reading the target's `package.json`; and any other read-only or read-write interaction with the target, its process, its port or its files.

**Rationale (accepted history, not re-litigated here):** in this repository's history an out-of-band listener probe during a governance round produced a real, disclosed incident and required a dedicated reconciliation; a pre-Oracle probe would additionally create an **unbudgeted ETB observation**, which the result-authority model of §17.4 forbids. The Oracle alone owns the single permitted listener query, executed inside its snapshot stage after all bootstrap checks.

**Consequence:** if an executor believes a target probe is necessary in order to proceed, the correct action is to **stop and fail closed** — not to probe. There is no "readiness", "diagnostic", "convenience" or "one-time" exception, and no historical observation may be reused as Path-F evidence.

---

## 16. Authorization-consumption step, control failure and attempt consumption

### 16.1 Authorization-consumption step

After PRE-1 … PRE-18 pass, the executor performs **exactly** the following and nothing else:

```powershell
Write-DevRelayPathFOneShotClaim `
    -TempPath  'docs/v0.3/evidence/ETB_PATH_F_AUTHORIZATION_USE.claim.tmp' `
    -FinalPath 'docs/v0.3/evidence/ETB_PATH_F_AUTHORIZATION_USE.claim' `
    -SchemaVersion 'devrelay-etb-path-f-authorization-use-v1' `
    -AuthorizationCommit '<path_f_authorization_commit>' `
    -AuthorizationSha256 '<path_f_authorization_sha256>' `
    -OraclePathFCommit 'a5d598a05a0467eea98cd0bf16e4486cceb72c23' `
    -OraclePathFSpecSha256 'b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5' `
    -OraclePathFScriptSha256 '4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0'
```

The angle-bracket values are **frozen text** copied from the accepted control surfaces; they are never computed at runtime, never inferred from `HEAD` and never left as placeholders.

On success:

```
PATH-F AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
```

On any thrown error: **stop immediately**, do not retry, do not delete the TEMP file if it exists, do not proceed to §16.3, and report the thrown marker verbatim. The round ends as a control failure under §16.2.

### 16.2 Authorization-control failure

If PRE-1 … PRE-18 pass but the authorization claim cannot be created, published or verified, the round fails as:

```
PATH-F AUTHORIZATION CONTROL FAILURE
```

This outcome is **not** `ETB_UNSATISFIED`, **not** `HARNESS_INVALID`, **not** an ETB semantic result, **not** `ETB_SATISFIED` and **not** a fourth ETB semantic class. It is a control-layer failure of this authorization. Consequences:

1. no Oracle invocation occurs;
2. no ETB attempt is made and the attempt budget is **not** consumed;
3. the authorization budget remains **spent** if the TEMP claim was created, and **unspent** only if it was never created — and in **both** cases the round is terminated with **no** re-attempt authority (§8);
4. `AUTHORITATIVE ETB SEMANTIC RESULT` is **unchanged** (`ETB_UNSATISFIED / PRESERVED`);
5. no retry is permitted under this authorization.

### 16.3 Post-authorization control boundary

After §16.1 succeeds, the **only** permitted next action is the attempt consumption of §16.4. In particular, the executor may **not**: query the listener; probe the endpoint; start or restart OpenCode; read the target's files; run any diagnostic; re-evaluate the preconditions in a way that touches the target; mutate an access-control list; publish anything; or invoke the Oracle before the attempt claim exists.

### 16.4 ETB attempt consumption

Only after §16.1 succeeded, the executor performs **exactly**:

```powershell
Write-DevRelayPathFOneShotClaim `
    -TempPath  'docs/v0.3/evidence/ETB_PATH_F_ATTEMPT_USE.claim.tmp' `
    -FinalPath 'docs/v0.3/evidence/ETB_PATH_F_ATTEMPT_USE.claim' `
    -SchemaVersion 'devrelay-etb-path-f-attempt-use-v1' `
    -AuthorizationCommit '<path_f_authorization_commit>' `
    -AuthorizationSha256 '<path_f_authorization_sha256>' `
    -OraclePathFCommit 'a5d598a05a0467eea98cd0bf16e4486cceb72c23' `
    -OraclePathFSpecSha256 'b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5' `
    -OraclePathFScriptSha256 '4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0'
```

On success:

```
PATH-F ETB ATTEMPT = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
```

Only now may the Oracle be entered. If the attempt claim cannot be created, the round ends under §8.2; the authorization budget remains spent and the attempt budget is either spent (TEMP created) or unspent (TEMP never created) — never restored, and never re-attemptable in the same round.

### 16.5 Post-attempt-claim failure

If the attempt claim was created but any step between its creation and the Oracle entry fails, the round fails closed:

```
PATH-F ETB ATTEMPT CLAIM = PRESENT / 1 OF 1 / SPENT / IRREVERSIBLE
ORACLE-PATHF = NOT ENTERED
AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED
```

The executor must **stop**, must not delete either claim, must not retry, must not enter the Oracle "anyway", and must not attempt to republish or repair the claim. Both budgets remain spent and the round is a control failure.

---

## 17. Oracle entry boundary, result classes and result authority

### 17.1 Exact invocation

Only after §16.4 succeeded may the Oracle be entered, and then only with this **exact** command line, from the repository root, with **no** parameters, **no** wrapper script, **no** alternate implementation, **no** substituted executable and **no** modified copy:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.ps1"
```

### 17.2 Oracle-owned internals (not restated here)

The Oracle's identity binding, listener ownership, target-binding sequence, S0/S1 continuity evaluation, pre-publication write-viability gate, publication order (evidence → manifest → result last), fail-closed publication model, kernel-level trap guard and exit-code contract (`0` / `2` / `3` / `4`, with **no** new exit code) are owned by the **accepted** Oracle-PathF specification and are **not** restated, amended, weakened or extended here. The authorization layer may require that those mechanisms exist; it may not re-specify them, pre-empt them or replace them.

### 17.3 Result classes (closed)

Exactly three ETB semantic classes exist, and this authorization may not add, rename, split, merge or reorder them:

| Class | Meaning |
| --- | --- |
| `ETB_SATISFIED` | the target semantics were established and satisfied |
| `ETB_UNSATISFIED` | the target semantics were evaluated and not satisfied |
| `HARNESS_INVALID / NO ETB SEMANTIC RESULT` | the harness could not evaluate the semantics; no ETB semantic result exists |

**Forbidden:** `PASS`, `FAIL`, `PARTIAL`, `UNKNOWN`, `PROBABLE`, `RETRY`, `ERROR`, `BLOCKED` or any other class name as an ETB **result** class. The historical Path-D phrase `UNCLASSIFIED CONTROL FAILURE` is **not** a class of this lineage and must not be resurrected as one; it remains Path-D governance history describing a control-layer outcome that produced `PATH-D ETB SEMANTIC RESULT = NONE`.

Authorization-layer and control-layer failures — `PATH-F AUTHORIZATION CONTROL FAILURE`, claim-writer throws, precondition failures, availability problems — are **governance/control descriptors only**. They are **not** a fourth ETB semantic class, they are not `HARNESS_INVALID` and they are not ETB observations. Any class preselection, inference from a prior lineage, or classification by anyone other than the accepted Oracle-PathF executable is void.

### 17.4 Result authority — observation versus authoritative semantic result

A Path-F Oracle invocation produces a **raw observation** published into the reserved output namespace of §14. That observation is **not** immediately the authoritative ETB semantic result.

**Promotion pipeline (all stages mandatory, in order, each in a different agent/session where independence is required):**

1. Path-F execution publishes a raw, self-describing observation artifact (evidence, manifest, result) with exactly one of the three closed classes of §17.3;
2. **independent result review** of that raw observation by a qualifying third party;
3. **result bookkeeping** in exactly one single-parent commit whose sole tracked delta is `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md`;
4. **independent confirmation** of that bookkeeping, materialized as a repository-verifiable record commit of the same two-file shape.

Only after all four stages does a new ETB semantic result become authoritative. Until then:

```
AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED
RAW RESULT PROMOTION ELIGIBILITY = REJECTED / BLOCKED
```

This authorization, its acceptance, its claims, its consumption and the Oracle invocation itself **never** replace the authoritative ETB semantic result. A raw observation that has not completed the pipeline is **never** cited as the authoritative result, and no stage of this lineage may silently promote it.

---

## 18. Fail-closed / no-retry contract

1. Every precondition failure stops the round **before** consumption.
2. Every post-consumption failure stops the round **after** consumption, permanently.
3. No retry, no rerun, no second attempt, no automatic re-invocation, no backoff loop, no `Start-Sleep`-and-retry and no "try the other port" path exists anywhere in this authorization.
4. No claim is ever deleted, truncated, moved, overwritten, renamed or reset — not to clean up, not to "unstick" a run, not to recover a budget.
5. A spent budget is spent forever, regardless of the outcome, and regardless of who observes it afterwards.
6. `git reset`, `git checkout`, branch switching, stashing, cleaning, rebasing, amending or force-updating **never** restores a budget and never un-consumes a claim.
7. An unavailable facility, an unexpected host failure, a publication failure and a control failure are all **fail-closed**: they never produce `ETB_SATISFIED`, never produce a semantic result and never silently promote an observation.
8. A **non-consuming** failure is still a terminated round: `NON-CONSUMING FAILURE DOES NOT MEAN RE-ATTEMPT AUTHORITY` (§8.3).
9. A permission, ACL or file-access problem is answered by failing closed — **never** by mutating permissions and retrying (§7).
10. If any required value, artifact, attribute or precondition cannot be verified, the correct action is to **stop and report**, not to proceed, improvise, approximate or ask a later stage to fix it.

---

## 19. Self-sufficiency, self-identity and historical immutability

### 19.1 Self-sufficiency

To consume this authorization and invoke the Oracle, an executor needs **only**:

1. this authorization artifact (`docs/v0.3/V03E_G0_5_PRE_ETB_PATH_F_AUTHORIZATION.md`), with its frozen `path_f_authorization_commit` and `path_f_authorization_sha256`;
2. the accepted Oracle-PathF specification and executable, at the frozen hashes of §2;
3. the accepted control-state markers in the two active status surfaces;
4. the frozen claim writer of §12.3;
5. the repository working copy and an already-established viable execution/file-access mode — concretely, a session whose DSH session policy declaration reports `danger-full-access` through the non-mutating channel of §6.4 (§6.1, `PRE-16`).

No chat history, conversation transcript, agent memory, external testimony, clipboard content, environment variable, out-of-band note or undocumented convention may be required, consulted or trusted. If any required value is missing, the executor fails closed.

### 19.2 Self-identity model (corrected Path-E precedent applied)

The authorization design artifact cannot contain its own future Git commit SHA or its own accepted artifact SHA before those identities exist. This candidate therefore:

- carries **explicit, frozen, angle-bracket placeholders** for `path_f_authorization_commit` and `path_f_authorization_sha256` (§5.1);
- **never** contains, embeds or hints at its own future commit identity or tree;
- **never** requires the executor to compute, guess, infer or fabricate either value;
- leaves binding of the two values to the later acceptance and confirmation stages, which record them as frozen text in the accepted control surfaces.

```
AUTHORIZATION DESIGN SELF-IDENTITY MODEL = PLACEHOLDER-BOUND EXTERNALLY / NO SELF-REFERENCE
```

### 19.3 Historical immutability

This authorization round creates **no** execution authority, consumes **no** budget, creates **no** claim and modifies **no** frozen artifact. Frozen and unchangeable, before and after this round:

`a5d598a05a0467eea98cd0bf16e4486cceb72c23`; `c45fb94068d5384dd9662f822be4722951f4200b`; `c4572c9e42e2ee0484e85536f3d1c7c32335f232`; `7ad12d1d0b9727548b271981116267f76c362f48`; `074b703dc6512b78ebd8381aa4147a3a96be2deb`; `1d06f2857840b9f4096bbedc156e3ac4c9eaddec`; `28118b135377277de5404f17c92779a928b71b32`; both accepted Oracle-PathF artifacts; `.gitattributes`; the Path-E spec, executable, authorization artifact and both Path-E claims; the Path-D spec, executable, authorization artifact and both Path-D claims; the Recovery-R1, Recovery-R2, D1, Oracle-R2 and original-oracle artifacts; all configuration and construction-time banners; and the recorded non-blocking Oracle-PathE design-review observations, which remain `NONBLOCKING / NOT REPAIRED / NO EXECUTABLE SEMANTIC IMPACT` and must **not** be "fixed" by editing a reviewed or accepted byte. The historical commit `a5e592bd9265fe4f20a97ed10d7ed39b4531be98` likewise remains `HISTORICAL / NOT CONFIRMED / NOT EFFECTIVE FOR ACCEPTANCE / SUPERSEDED FOR REVIEW-AUTHORITY PURPOSES` — it is not reopened, re-confirmed, rewritten or reused as review authority.

**MODEL A is preserved:** runtime artifacts produced by a future authorized execution are generated operational files; they remain **untracked** and byte-immutable once published. Tracked governance advances **only** through:

```
CHANGELOG.md
docs/v0.3/V03E_ACCEPTANCE.md
```

No runtime or generated artifact may become tracked; no governance fact may be recorded by creating a runtime file.

### 19.4 Provenance contradiction audit (recorded)

Because the accepted specification reserves its three content-provenance fields as `UNKNOWN` and this authorization binds the lineage externally, the candidate was audited for any sentence that would simultaneously require evidence to carry frozen Path-F identities and to reject `UNKNOWN`. The audit result is recorded in §3.3 and here (§19.4), and is:

```
PATHF_AUTHORIZATION_PROVENANCE_COMPATIBILITY = COHERENT
UNKNOWN CONTRADICTION = NONE
POST-HOC EVIDENCE REWRITING PERMITTED = NO
```

---

## 20. Authoritative sequence and effectivity model

The following order is frozen. **No stage may be skipped, merged, collapsed, reordered, self-performed or repeated by the same session.**

```
1. Path-F authorization design candidate (this document, committed)
2. QUALIFYING THIRD-PARTY INDEPENDENT REVIEW of this candidate (different agent/session)
3. Path-F authorization acceptance bookkeeping
      = exactly ONE single-parent commit whose sole tracked delta is
        M CHANGELOG.md + M docs/v0.3/V03E_ACCEPTANCE.md
4. FRESH INDEPENDENT CONFIRMATION of that acceptance bookkeeping (different agent/session)
5. materialization of that confirmation as a repository-verifiable record commit
      = exactly ONE single-parent commit of the same two-file shape
6. only now: PATH-F AUTHORIZATION = ACCEPTED / FROZEN / EFFECTIVE
      EXECUTION AUTHORITY = GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY
7. fresh operational execution session performs §13 -> §17 in order
```

Independence declarations required at stage 2 (recorded **before** any technical conclusion):

```
THIRD-PARTY REVIEWER SESSION SEPARATION = SATISFIED
REVIEWER WAS NOT THE AUTHORIZATION-CANDIDATE-AUTHOR SESSION = YES
REVIEWER DID NOT PREVIOUSLY REVIEW THIS EXACT AUTHORIZATION OBJECT = YES
```

and at stage 4, additionally: `REVIEWER WAS NOT THE AUTHORIZATION-ACCEPTANCE-BOOKKEEPING-AUTHOR SESSION = YES`.

**Stage 6 is the only point at which this authorization becomes usable, and it is unusable until then.** Committing this document, reviewing it, accepting it or confirming it does **not**, by itself, consume, grant or release any budget. Design effectivity of the Oracle-PathF design (already reached) is **not** execution authority and does **not** shorten this sequence by one stage.

---

## 21. Materialization self-audit (author self-audit only)

### 21.1 Audit scope

This is an **author self-audit of the design candidate**, performed before commit. It is **not** a review, **not** an acceptance, **not** an independent confirmation and **not** a verdict on the candidate. No review verdict is claimed anywhere in this document.

### 21.2 Audited properties and results

| # | Property | Result |
| --- | --- | --- |
| 1 | Oracle-PathF frozen identity exact (commit, spec SHA, script SHA, bytes, lines) | PASS — §2 |
| 2 | Provenance-model compatibility with `MODEL_2_EXTERNAL_LINEAGE_BINDING` | PASS — §3 |
| 3 | No sentence requires evidence to carry frozen identity, and no sentence rejects the reserved `UNKNOWN` | PASS — no `UNKNOWN` contradiction |
| 4 | No self-identity paradox; no embedded own commit or tree | PASS — §5.4, §19.2 |
| 5 | No execution authority created by this round | PASS — §9.5 |
| 6 | No budget created or made available | PASS — §9.5 |
| 7 | No claim created; all four claim paths absent | PASS — §10, §14 |
| 8 | No hidden retry or re-attempt path anywhere | PASS — §8, §18 |
| 9 | Failed-`CreateNew` semantics unambiguous (non-consuming ≠ retryable) | PASS — §8.3 |
| 10 | No ACL repair, restoration or normalization path | PASS — §7 |
| 11 | No escalation-after-failure path | PASS — §6.3, §7 |
| 12 | No listener/target ownership leak into the authorization layer | PASS — §13.1, §15 |
| 13 | No fourth ETB semantic class; control descriptors kept distinct | PASS — §17.3 |
| 14 | Namespace closed at exactly eleven paths; accounting rule explicit | PASS — §14 |
| 15 | Predecessor integrity preserved; no cleanup, reuse or repair | PASS — §4, §19.3 |
| 16 | No raw-result promotion; promotion pipeline intact | PASS — §17.4 |
| 17 | Deterministic future acceptance lifecycle; no skipped or self-performed stage | PASS — §20 |
| 18 | `PRE-2` and `PRE-3` satisfiable in the state in which they are evaluated | PASS — §13.2 |
| 19 | Written-artifact identity: this artifact carries no staged or worktree byte divergence | PASS at commit time |
| 20 | No runtime namespace path created; no probe performed; no listener query; no Oracle invocation | PASS |
| 21 | Concrete required execution/file-access mode stated with the canonical DSH token `danger-full-access`; `read-only` and `workspace-write` explicitly insufficient; no normative `full-file-access` occurrence anywhere | PASS — §0 decision 13, §6.1, `PRE-16` |
| 22 | `PRE-16` objectively and deterministically evaluable through eight explicit clauses; an unobservable or non-matching canonical token fails closed | PASS — §6.1, §6.4, §13 `PRE-16` |
| 23 | DSH session-mode observation channel explicit, non-mutating and actually supported by recovered DSH evidence; no environment variable required or assumed; `PRE-17` satisfiable after `PRE-16` has confirmed `danger-full-access` through it | PASS — §6.4, §13 `PRE-16`, §13 `PRE-17` |
| 24 | Corrective-successor supersession and single-budget carry-forward model coherent; no second budget, no reset, no automatic reuse | PASS — §5.5, §9.5 |
| 25 | Recorded design findings P3-A … P3-G corrected by this revision | PASS — §5.2, §5.3, §9.1, §13, §13.2, §15, §19.4 |
| 26 | No reactive-escalation, ACL-repair, permission-repair or retry authority created | PASS — §6.1, §6.2, §6.3, §7 |
| 27 | `PRE-18` semantics preserved and extended with the mode-change and reactive-escalation prohibitions | PASS — §13 `PRE-18` |
| 28 | `MODE_TOKEN_GLOBAL_NORMALIZATION = COMPLETE` — exactly one normative mode token, no second source of truth, no surviving generic mode phrase whose normative value cannot be traced to `danger-full-access` | PASS — §0 decision 13, §6.1, §6.4, §7, §13, §19.1, §23 |
| 29 | Bounded P2 remediation binding: the rejected first corrective candidate `d895856…` / `c281f93e…` is recorded as `REQUEST_CHANGES` / P2 = 1 without being amended, revoked or relabelled; scope limited to that P2 plus the directly necessary mechanical governance; `P3-A` … `P3-G` not regressed and no substantive area reopened | PASS — §0 decisions 13, 15, §5.5 |

### 21.3 Self-audit severity

```
DESIGN SELF-AUDIT SEVERITY (this round, author self-audit only)
  P0 = 0
  P1 = 0
  P2 = 0
  P3 = 1
```

| ID | Observation | Class |
| --- | --- | --- |
| **P3-1** | The accepted Oracle-PathF specification §22.1 records a frozen `SHA-256` for the executable and a byte-class table for it, while this authorization quotes only the SHA-256 values. The quoted values were re-measured and agree; the byte-class table is **not** duplicated here because it belongs to the specification and to the review stage. | `DOCUMENTATION COMPLETENESS / NONBLOCKING / NO EXECUTABLE SEMANTIC IMPACT / NOT REPAIRED` |

No P0, P1 or P2 condition was found in the candidate. This classification is an author self-audit result and does not bind any reviewer.

**Corrective-successor revision self-audit (this round, author self-audit only):**

```
CORRECTIVE-SUCCESSOR REVISION SELF-AUDIT SEVERITY
  P0 = 0
  P1 = 0
  P2 = 0
  P3 = 1
```

| ID | Observation | Class |
| --- | --- | --- |
| **P3-2** | The concrete required mode is stated **prospectively** for a future Owner-governed operational session. This design round neither establishes, verifies nor tests any execution/file-access mode, so `PRE-16` cannot be exercised here by construction. That is the intended boundary — the accepted Oracle-PathF specification §9.1/§9.2 permit exactly this prospective declaration and forbid reactive escalation — and it is recorded so that no reader mistakes the requirement for an established capability. | `PROCESS BOUNDARY / NONBLOCKING / NO AUTHORITY CREATED / NOT REPAIRED` |

No P0, P1 or P2 condition was found in this revision. This classification is an author self-audit result and does not bind any reviewer; the qualifying third-party review is a separate, later, differently-sessioned stage (§20, §24).

**Bounded P2 remediation revision self-audit (this round, author self-audit only):**

```
BOUNDED P2 REMEDIATION REVISION SELF-AUDIT SEVERITY
  P0 = 0
  P1 = 0
  P2 = 0
  P3 = 1
```

| ID | Observation | Class |
| --- | --- | --- |
| **P3-3** | The qualifying review of the preceding corrective candidate `d895856d2efc9683b91b182c33647efe57b01fc3` / `c281f93e6ddfe09351c435e698c5d50c3a5cfcda2053f27159ba921e2eed72eb` returned `REQUEST_CHANGES` with `P0 = 0`, `P1 = 0`, `P2 = 1`, `P3 = 4`. The sole blocking P2 was `FULL_FILE_ACCESS_MODE_IDENTITY = LABEL_PRESENT_BUT_NOT_OPERATIONALLY_VERIFIABLE` with `CORRECTED_PRE_16 = AMBIGUOUS`. This revision remediates exactly that one P2 — the canonical mode token becomes `danger-full-access` and the session-visible observation channel of §6.4 is bound — and performs only the mechanical governance/cross-reference updates directly necessary to record the remediation. The four additional P3 observations of that review caused no broader redesign; the `P3-A` … `P3-G` corrections of the preceding revision are preserved and no substantive area is reopened. | `REVIEW-FINDING REMEDIATION / BOUNDED / NONBLOCKING` |

The P2 recorded above was identified by an **independent review of the previous candidate**, not by this revision's own observation, and this revision's author self-audit finds no P0, P1 or P2 condition of its own. This classification is an author self-audit result and does not bind any reviewer; the qualifying third-party review of **this** bounded remediation revision is a separate, later, differently-sessioned stage (§20, §24).

### 21.4 Recorded design-time verification of this round

Performed by the design round itself, mechanically:

```
oracle_path_f_spec  = docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.md
  bytes = 34308  LF = 733  CR = 0  BOM = absent
  SHA-256 = b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5
oracle_path_f_script = docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.ps1
  bytes = 49704  LF = 894  CR = 0  non-ASCII bytes = 0  max byte = 125  BOM = absent
  SHA-256 = 4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0
git check-attr text eol
  -> text: set / eol: lf for the specification, the executable and this artifact
PATH-F RUNTIME OCCUPANCY = 0 / 11   (all eleven paths absent, by the §11 predicate)
PATH-F CLAIM PATHS       = ABSENT (4 / 4)
PATH-E RUNTIME OCCUPANCY = 6 / 11   (unchanged; no cleanup performed)
first corrective-successor round bounds (historical record of the preceding revision)
  parent governance commit             = 5fae11eefdcaddc27b4abf28d3a2258ad654d84d
  disposition commit bound             = 5fae11eefdcaddc27b4abf28d3a2258ad654d84d
  Oracle-PathF spec / script bytes+SHA = unchanged (34308 / b07a822b…, 49704 / 4c30a682…)
  PATH-F RUNTIME OCCUPANCY             = 0 / 11
  PATH-F CLAIM PATHS                   = ABSENT (4 / 4)
  PATH-E RUNTIME OCCUPANCY             = 6 / 11   (unchanged; no cleanup performed)
  execution-mode establishments/tests  = 0   (requirement stated only; nothing established, probed or switched)
  claims created = 0   budgets consumed = 0   Oracle invocations = 0
bounded P2 remediation revision round bounds (this revision)
  parent commit (first corrective candidate)  = d895856d2efc9683b91b182c33647efe57b01fc3
  rejected candidate artifact SHA-256         = c281f93e6ddfe09351c435e698c5d50c3a5cfcda2053f27159ba921e2eed72eb
  qualifying review verdict / severity        = REQUEST_CHANGES / P0 0 · P1 0 · P2 1 · P3 4
  sole blocking P2 remediated                 = FULL_FILE_ACCESS_MODE_IDENTITY = LABEL_PRESENT_BUT_NOT_OPERATIONALLY_VERIFIABLE
  canonical DSH mode token adopted            = danger-full-access
  normative full-file-access occurrences      = 0
  Oracle-PathF spec / script bytes+SHA        = unchanged (34308 / b07a822b…, 49704 / 4c30a682…)
  PATH-F RUNTIME OCCUPANCY                    = 0 / 11
  PATH-F CLAIM PATHS                          = ABSENT (4 / 4)
  PATH-E RUNTIME OCCUPANCY                    = 6 / 11   (unchanged; no cleanup performed)
  execution-mode establishments/tests         = 0   (requirement and observation channel stated only; nothing established, observed, probed or switched)
  claims created = 0   budgets consumed = 0   Oracle invocations = 0
```

---

## 22. Activity counters

```
PATH-F AUTHORIZATION DESIGN ROUND
  Oracle-PathF executions                = 0
  Oracle-PathE executions                = 0
  Oracle-PathD executions                = 0
  ETB executions                         = 0
  listener queries                       = 0
  Get-NetTCPConnection calls             = 0
  port-4096 probes                       = 0
  localhost / 127.0.0.1 probes           = 0
  endpoint probes                        = 0
  OpenCode starts / restarts             = 0
  HTTP / provider / model calls          = 0
  claims created                         = 0
  budgets created                        = 0
  budgets consumed                       = 0
  evidence / manifest / result creations = 0
  runtime namespace entries created      = 0
  ACL reads / mutations / restorations   = 0
  execution-mode establishments / tests  = 0   (the required canonical mode and its observation channel are stated only; nothing is established, observed, probed or switched)
  reviewed-artifact mutations            = 0
  predecessor cleanups                   = 0
  historical-lineage reopenings          = 0
  Path-E modifications                   = 0
  Path-D modifications                   = 0
  runtime / test / dependency / version changes = 0
  repository modifications beyond this authorization candidate and the two status surfaces = 0
  tags / releases / pushes               = 0
```

### 22.1 Preserved non-claims

This authorization is **NOT** `SIC`; **NOT** `P6`; **NOT** `G0.5` completion; **NOT** a `MODE-B RESULT`; **NOT** a `CASE-C AUTHORIZATION`; **NOT** an adoption authorization; **NOT** a retry authorization for any lineage; **NOT** a general license to query a listener; **NOT** an ACL-restoration authorization; and **NOT** an ETB result of any class. It claims no accepted status for itself.

---

## 23. Current status

```
ORACLE-PATHF DESIGN                    = ACCEPTED / FROZEN / EFFECTIVE
Accepted design identity               = a5d598a05a0467eea98cd0bf16e4486cceb72c23
Accepted spec SHA-256                  = b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5
Accepted script SHA-256                = 4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0
ORACLE-PATHF DESIGN ACCEPTANCE BOOKKEEPING = 7ad12d1d0b9727548b271981116267f76c362f48
ORACLE-PATHF DESIGN ACCEPTANCE CONFIRMATION MATERIALIZATION = 1d06f2857840b9f4096bbedc156e3ac4c9eaddec
ORACLE-PATHF DESIGN CONFIRMATION RECURSION = NONE
PATH-F AUTHORIZATION DESIGN            = BOUNDED P2 REMEDIATION REVISION OF THIS LINEAGE / CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE
PATH-F AUTHORIZATION DESIGN CANDIDATE  = the commit that introduces this bounded P2 remediation revision (single-parent successor of d895856d2efc9683b91b182c33647efe57b01fc3; not embedded here by design)
PATH-F AUTHORIZATION                   = BOUNDED P2 REMEDIATION DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / NOT EXECUTED
QUALIFYING THIRD-PARTY AUTHORIZATION DESIGN REVIEW OF THIS BOUNDED P2 REMEDIATION REVISION = NOT PERFORMED / REQUIRED NEXT
PREVIOUS CORRECTIVE CANDIDATE          = d895856d2efc9683b91b182c33647efe57b01fc3
Previous candidate artifact SHA-256    = c281f93e6ddfe09351c435e698c5d50c3a5cfcda2053f27159ba921e2eed72eb
PREVIOUS CORRECTIVE CANDIDATE STATE    = REQUEST_CHANGES (P0 0 / P1 0 / P2 1 / P3 4) / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / SUCCEEDED PROSPECTIVELY BY THIS REVISION
OLD PATH-F AUTHORIZATION (HISTORICAL)  = ed112f8c5f1e35d87092d0339698a792ce0b145a
Old authorization artifact SHA-256     = c147af8714164dae8b81cafa4eb01945a3ceb8c74b36f0fc18fbd56db284c4de
OLD PATH-F AUTHORIZATION EFFECTIVITY   = ACCEPTED / FROZEN / EFFECTIVE (historical; never rewritten, revoked or relabelled)
OLD PATH-F OPERATIONAL USABILITY       = BLOCKED AFTER THE PRE-16 PRECONDITION STOP / NOT AUTOMATICALLY RETRYABLE
SUPERSESSION EFFECT                    = PROSPECTIVE ONLY (§5.5)
PATH-F OPERATIONAL EXECUTION           = NOT STARTED (PRE-16 precondition stop; no claim, no budget consumption, no Oracle invocation)
PRE-16 STOP BINDING                    = PRE-1 … PRE-15 PASS / PRE-16 FAIL / PRE-17 FAIL (dependent on PRE-16) / PRE-18 NOT REACHED
PATHF_PRE16_STRUCTURAL_GAP             = CONFIRMED
REMEDIATION ROUTE                      = ROUTE A / CORRECTIVE SUCCESSOR AUTHORIZATION DESIGN LIFECYCLE REQUIRED
DISPOSITION COMMIT                     = 5fae11eefdcaddc27b4abf28d3a2258ad654d84d
REQUIRED PATH-F DSH OPERATIONAL EXECUTION / FILE-ACCESS MODE = danger-full-access
read-only                              = INSUFFICIENT FOR PATH-F OPERATIONAL EXECUTION
DSH CANONICAL MODE VOCABULARY          = read-only | workspace-write | danger-full-access (closed)
DSH SESSION-MODE OBSERVATION CHANNEL   = DSH `sandbox:policy` runtime-context declaration in the current session; required token exactly `danger-full-access` (§6.4)
MODE-TOKEN GLOBAL NORMALIZATION        = COMPLETE (exactly one normative mode token; no second source of truth)
workspace-write                        = INSUFFICIENT FOR PATH-F OPERATIONAL EXECUTION
PROSPECTIVE EXECUTION-MODE REQUIREMENT = PERMITTED / REQUIRED
REACTIVE ESCALATION AFTER FAILURE      = FORBIDDEN
CORRECTIVE SUCCESSOR OPERATIONAL USE   = NOT AVAILABLE UNTIL THE §20 LIFECYCLE COMPLETES FOR THE NEW IDENTITY
PATH-F EXECUTION AUTHORITY             = NONE
PATH-F AUTHORIZATION USE               = 1 OF 1 / UNCONSUMED (0 OF 1) — CARRIED FORWARD TO THE NEW ACCEPTED CORRECTIVE IDENTITY PER §5.5 / NOT USABLE UNDER EITHER IDENTITY TODAY
PATH-F ETB ATTEMPT                     = 1 OF 1 / UNSTARTED (0 OF 1) — SAME CARRY-FORWARD / NOT USABLE UNDER EITHER IDENTITY TODAY
PATH-F AUTHORIZATION-USE BUDGET        = NOT CREATED / NOT AVAILABLE FOR CONSUMPTION (no budget is created, reset or released by this round)
PATH-F ETB-ATTEMPT BUDGET              = NOT CREATED / NOT AVAILABLE FOR CONSUMPTION
ORACLE-PATHF INVOCATIONS               = 0 OF 1 / NOT AUTHORIZED
PATH-F CLAIMS                          = ABSENT (4 / 4)
PATH-F RUNTIME OCCUPANCY               = 0 / 11
PATH-F ETB EXECUTION                   = NOT AUTHORIZED
ORACLE-PATHF EXECUTION                 = NOT AUTHORIZED
ORACLE-PATHE EXECUTION                 = NOT AUTHORIZED
ORACLE-PATHD EXECUTION                 = NOT AUTHORIZED
LISTENER QUERY                         = NOT EXECUTED
TARGET PROBE                           = NOT EXECUTED
ACL MUTATION / RESTORATION             = NOT PERFORMED / NOT AUTHORIZED BY THIS ROUND
CURRENT ACL STATE                      = NOT NORMALIZED (unchanged by this round)
AUTHORITATIVE ETB SEMANTIC RESULT      = ETB_UNSATISFIED / PRESERVED
PATH-E LINEAGE                         = EXHAUSTED / CLOSED
PATH-E RAW RESULT                      = BLOCKED / NON-PROMOTABLE
PATH-E ETB SEMANTIC RESULT             = NONE
PATH-E RETRY AUTHORITY                 = NONE
PATH-E RUNTIME OCCUPANCY               = 6 / 11
PATH-D                                 = EXHAUSTED / CLOSED / IMMUTABLE
PATH-D AUTHORIZATION USE               = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
PATH-D ETB ATTEMPT                     = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
ORACLE-PATHD INVOCATIONS               = 1 OF 1 / MAXIMUM REACHED
PATH-D ETB SEMANTIC RESULT             = NONE
PATH-D RETRY AUTHORITY                 = NONE
A5E592BD BOOKKEEPING                   = HISTORICAL / NOT CONFIRMED / NOT EFFECTIVE FOR ACCEPTANCE / SUPERSEDED FOR REVIEW-AUTHORITY PURPOSES
MODEL A                                = PRESERVED
NEXT STAGE                             = FRESH QUALIFYING THIRD-PARTY INDEPENDENT REVIEW OF THE BOUNDED P2 REMEDIATION SUCCESSOR PATH-F ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE (DIFFERENT SESSION)
```

---

## 24. Next stage

```
NEXT STAGE = FRESH QUALIFYING THIRD-PARTY INDEPENDENT REVIEW
             OF THE BOUNDED P2 REMEDIATION SUCCESSOR PATH-F ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE
```

That review **MUST** occur in a **different agent/session** than the one that authored this bounded remediation revision, and it is **not** performed by this round. It must state its independence declarations before any technical conclusion. At minimum it must:

1. attempt to reproduce the two blocked Path-E findings (`P2-1` unsatisfiable self-identity gate, `P2-2` contradictory effectivity gate) and confirm they are absent here;
2. verify that §3 contains **no** requirement that Oracle-generated evidence carry frozen Path-F identities, and **no** requirement that contradicts the reserved `UNKNOWN`, and that the accepted specification's §19.3 compatibility requirement is met;
3. verify that the ACL/execution-mode policy of §6/§7 states the required mode concretely with the canonical DSH token **`danger-full-access`** (with `read-only` and `workspace-write` insufficient and **no normative `full-file-access` occurrence anywhere**), that §6.4's session-mode observation channel is the mechanism the installed DSH harness actually publishes to a session, and that no `icacls`, `Set-Acl`, ACL repair, permission normalization, mode switching, harness per-call sandbox escalation (`sandbox_permissions`) or escalation-after-failure is authorized — and that `PRE-16` … `PRE-18` close the Path-E `L1`/`L2`/`L5` failure modes, including the structural gap that stopped the first Path-F operational round;
4. verify that the non-consuming-failure rule of §8 has no interpretation gap and never yields re-attempt authority, and that `PRE-18` remains closed with the mode-change and reactive-escalation prohibitions added;
5. verify that the namespace accounting rule of §14 is exact and that the occupancy is `0 / 11`;
6. verify that the supersession and budget carry-forward model of §5.5 creates no second budget, no reset and no automatic reuse authority, and that a future claim binds the **new** accepted corrective identity and never `ed112f8c…` / `c147af87…`;
7. verify that no fourth ETB semantic class is introduced, that control descriptors remain distinct, and that the promotion pipeline of §17.4 is intact;
8. verify that this bounded remediation design round created no claim, no budget, no execution authority, no execution-mode establishment and no runtime namespace entry, and that `PATH-F OPERATIONAL EXECUTION` remains `NOT STARTED`;
9. verify that §6.4's channel is what the installed DSH harness actually publishes to a session (the `sandbox:policy` runtime-context declaration), that no shell environment variable and no ACL read is required or assumed anywhere in the artifact, and that `PRE-16` is fully evaluable through it with zero filesystem writes, zero claim-path accesses, zero governed-path probes, zero ACL operations, zero permission repairs and zero escalation;
10. verify `MODE_TOKEN_GLOBAL_NORMALIZATION = COMPLETE` — exactly one normative mode token, no surviving generic mode phrase whose normative value cannot be traced directly to `danger-full-access`, and the single retained historical mention of the superseded token explicitly qualified as `HISTORICAL / DESCRIPTIVE ONLY / NOT A DSH MODE TOKEN / NOT ACCEPTABLE AS PRE-16 EVIDENCE`;
11. verify that this bounded remediation revision did not regress `P3-A` … `P3-G` and did not reopen the budget model, the runtime namespace, the claim model, the provenance model or the result boundary.

**This round does NOT perform that review, does NOT bookkeep an acceptance, does NOT confirm the authorization, does NOT accept or freeze itself, and does NOT execute Path-F.**

---

## 25. Strict prohibitions carried by this authorization

No Oracle-PathF execution. No ETB attempt. No Path-F execution authorization. No claim creation. No budget creation. No budget consumption. No listener query. No endpoint probe. No runtime publication. No ACL mutation, restoration or normalization. No permission repair. No execution-mode establishment, verification, probing or switching. No elevation, and no reactive escalation after any failure. No Path-E cleanup. No Path-D mutation. No historical status-surface rewrite. No result promotion. No push. No tag. No release.

---

**End of Path-F one-shot ETB execution authorization, corrective successor design candidate.**
