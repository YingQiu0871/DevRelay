# DevRelay v0.3-E — G0.5-PRE / SIC — Path-E one-shot ETB execution authorization

> **PATH-E AUTHORIZATION = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / NOT EXECUTED.**
> **THIS AUTHORIZATION DESIGN GRANTS NO EXECUTION AUTHORITY TODAY.**
> **IT CREATES NO CLAIM NOW AND CONSUMES NO BUDGET.**
> **IT DOES NOT ENTER ORACLE-PATHE AND DOES NOT QUERY ANY LISTENER.**
> **IT IS AUTHORIZED FOR DESIGN ONLY AT THIS STAGE.**
> **THIS IS NOT A RETRY OF PATH-D OR OF ANY EARLIER LINEAGE.**
> **ONE AUTHORIZATION USE + ONE ETB ATTEMPT ONLY IF LATER INDEPENDENTLY ACCEPTED.**

**Status:** **PATH-E AUTHORIZATION = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / NOT EXECUTED**

**Date:** 2026-09-30
**Repository:** `D:\DevRelay`
**Branch:** `v0.3-e-recovery-reconciliation`
**Parent governance commit (build base):** `367aca3f61e6387940deb976d0302ebc7d8b07c4`

---

## 0. Owner decisions (immutable)

The Owner has recorded, and this artifact may not weaken, reinterpret, relabel or extend:

1. `PATH-E LINEAGE = OPENED FOR DESIGN ONLY` — the Owner **DECISION = OPEN A NEW ETB LINEAGE**; `NEW LINEAGE = PATH E — NEW ETB ATTEMPT`; `NEW EXECUTION ORACLE = Oracle-PathE`; canonical lineage token `PATH_E`; canonical oracle token `ORACLE_PATH_E`.
2. This new lineage is **explicitly NOT** a retry of Path D, **NOT** `Recovery-R3`, **NOT** `Oracle-R3`, **NOT** `Oracle-D`, **NOT** `Oracle-PD`, **NOT** `Oracle-PathD2`, **NOT** a reuse of the Path-D authorization, **NOT** a reset of the Path-D budgets, and **NOT** a repair-and-rerun of Oracle-PathD.
3. `PATH-D LINEAGE = EXHAUSTED / CLOSED / IMMUTABLE`; `PATH-D RETRY AUTHORITY = NONE`; Path D is not reopened, repaired or rerun by this round.
4. The reviewed predecessor defect is carried forward as accepted history and is **NOT** repaired in the frozen predecessor artifact: Oracle-PathD used `Get-FileHash` unprotected at predecessor lines 117/118 while its availability was only checked at line 189 (whose gate list itself contains `Get-FileHash`, making that gate unreachable in exactly the scenario it exists to handle).
5. The normative correction frozen for this lineage is: **NO REQUIRED COMMAND MAY BE USED BEFORE ITS REQUIRED-AVAILABILITY CONDITION HAS BEEN SAFELY ESTABLISHED**, and Oracle-PathE satisfies it by **never calling `Get-FileHash` at all**.
6. `ORACLE-PATHE = ACCEPTED / FROZEN / EFFECTIVE` (accepted design identity `f7cafd83a95225e1ce9565a9336ded8575b65335`), and it must not be modified, re-accepted, re-reviewed-in-place or extended by this authorization.
7. The ETB result-class model is closed at exactly three classes and no fourth ETB class may be created by this lineage.
8. The last authoritative ETB semantic result is `ETB_UNSATISFIED` and must remain **PRESERVED** until a future authorized Path-E execution produces a new raw observation **and** that observation completes independent result review, result bookkeeping and independent bookkeeping confirmation.
9. Any stage that this document requires to be an independent third-party review or confirmation must satisfy `OWNER DETERMINATION = THIRD-PARTY INDEPENDENCE REQUIRES DIFFERENT AGENT/SESSION`; a methodological same-session review is adversarial self-review and is **NOT SUFFICIENT** for third-party independence.
10. `A5E592BD BOOKKEEPING = HISTORICAL / NOT CONFIRMED / NOT EFFECTIVE FOR ACCEPTANCE / SUPERSEDED FOR REVIEW-AUTHORITY PURPOSES` — the historical commit `a5e592bd9265fe4f20a97ed10d7ed39b4531be98` is not reopened, re-confirmed, rewritten or reused as review authority.

These Owner decisions are recorded in the active tracked status surfaces of this repository and are not re-derivable from this artifact alone.

---

## 1. Purpose and scope

### 1.1 Purpose

This artifact defines the **one-shot ETB execution-authorization model for the PATH E — NEW ETB ATTEMPT lineage**.

Its purpose is to make the following **mechanically checkable, deterministic, fail-closed and auditable**:

1. what an executor must verify **before** any authorization budget is consumed;
2. where, how and with exactly which bytes the two claim budgets are consumed;
3. what irreversible point of no return consumption represents;
4. what the authorization layer may **not** do (target binding, listener query, result classification);
5. how the single Oracle-PathE invocation is bounded, targeted and terminated;
6. how the resulting raw observation relates to the authoritative ETB semantic result;
7. how this authorization itself becomes effective — and only then usable.

### 1.2 Non-purpose

This artifact is **not**: an acceptance of itself; an execution; a retry; a listener probe; a target probe; a readiness check; a Path-D artifact; a modification of any accepted Oracle-PathE artifact; a new ETB result class; a promotion of any observation to the authoritative ETB semantic result; an authorization for more than one authorization use and more than one ETB attempt; or a reusable, resettable or renewable budget.

### 1.3 Scope boundary

This artifact governs **only** the consumption of the two Path-E claim budgets for **one** attempt of **one** invocation of the **accepted** Oracle-PathE executable against the **pre-existing** target, under all preconditions of §13.

It does **not** govern: the Oracle's internal behavior (owned by the accepted Oracle-PathE spec); the target application's behavior; any other lineage; any other endpoint; any other port; any other executable; any second attempt.

---

## 2. Accepted Oracle-PathE provenance

The authorization binds the following **accepted, frozen and effective** identity and may not redefine, extend, re-derive or modify it:

| Item | Frozen value |
| --- | --- |
| `oracle_path_e_commit` | `f7cafd83a95225e1ce9565a9336ded8575b65335` |
| `oracle_path_e_parent` | `3b085dae4ff89512bcf23f80043b78ddc82a490f` |
| `oracle_path_e_tree` | `0101461d95bdbc72d809dcf259b0fae1bf5be7ca` |
| `oracle_path_e_subject` | `fix(v03e): remediate Oracle-PathE design review findings` |
| `oracle_path_e_spec` | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.md` |
| `oracle_path_e_spec_sha256` | `78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b` |
| `oracle_path_e_spec_bytes` | `33881` |
| `oracle_path_e_spec_lines` | `676` |
| `oracle_path_e_script` | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.ps1` |
| `oracle_path_e_script_sha256` | `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb` |
| `oracle_path_e_script_bytes` | `41610` |
| `oracle_path_e_script_lines` | `772` |
| `oracle_path_e_design_acceptance_bookkeeping` | `302dd74aa9f22640eaacb34bfbbc96de93dbaa9b` |
| `oracle_path_e_design_acceptance_bookkeeping_tree` | `fe2963fea5d2e8e9c20db52902c71bee3a883fa3` |
| `oracle_path_e_design_acceptance_confirmation_record` | `367aca3f61e6387940deb976d0302ebc7d8b07c4` |
| `Oracle-PathE status` | `ACCEPTED / FROZEN / EFFECTIVE` |
| `Oracle-PathE execution` | `NOT AUTHORIZED` (the accepted design is effective; **executing it is not**) |

`oracle_path_e_commit` is the **independently reviewed DESIGN commit**. It is **never** substituted by an acceptance-bookkeeping commit, by a confirmation-record commit, by the current branch HEAD, or by any later commit; the acceptance and confirmation commits are recorded above as separate provenance facts only.

---

## 3. Provenance distinction — generic ETB vs Path-E

The accepted Oracle-PathE specification intentionally describes a **generic** ETB execution oracle: its contract, its class set, its publication model and its target semantics are lineage-independent. In the accepted Oracle-PathE spec, `oracle_path_e_commit`, `oracle_path_e_spec_sha256` and `oracle_path_e_script_sha256` were recorded as `UNKNOWN`, because that lineage's design could not truthfully know its own identity.

This artifact does **not** edit that accepted specification. Instead, the missing lineage binding is centralized **here**:

| Generic (accepted Oracle-PathE spec) | Path-E binding (this authorization) |
| --- | --- |
| `oracle_path_e_commit = UNKNOWN` | `f7cafd83a95225e1ce9565a9336ded8575b65335` |
| `oracle_path_e_spec_sha256 = UNKNOWN` | `78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b` |
| `oracle_path_e_script_sha256 = UNKNOWN` | `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb` |
| `oracle_commit` (generic parameter) | `oracle_path_e_commit` (frozen, above) |

Consequences that must not be blurred:

1. the accepted Oracle-PathE spec's `UNKNOWN` values are **not** defects and are **not** corrected by editing it;
2. every Path-E claim and every Path-E evidence artifact records the **frozen Path-E values** of §2, never `UNKNOWN`;
3. no Path-D, Oracle-R2, Recovery-R1, Recovery-R2 or D1 identity may be substituted for a Path-E identity anywhere in this lineage.

---

## 4. Predecessor Oracle-PathD provenance (historical, NOT reusable)

The Path-D lineage reached a terminal state and is preserved as immutable history. Its identities are recorded here **only** so that the prohibition is mechanically checkable and so that no executor can confuse the two lineages.

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

**Permanent Path-D state (must remain unchanged and must not be consumed, reused, reset, deleted, moved or reinterpreted):**

```
PATH-D                              = EXHAUSTED / CLOSED / IMMUTABLE
PATH-D AUTHORIZATION USE            = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
PATH-D ETB ATTEMPT                  = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
ORACLE-PATHD INVOCATIONS            = 1 OF 1 / MAXIMUM REACHED
PATH-D BOOKKEEPED OPERATIONAL OUTCOME = UNCLASSIFIED CONTROL FAILURE / NO ETB SEMANTIC RESULT / ACCEPTED / FROZEN AS GOVERNANCE HISTORY
PATH-D ETB SEMANTIC RESULT          = NONE
PATH-D EXECUTION OUTPUTS            = NONE
PATH-D RETRY AUTHORITY              = NONE
PATH-D ORACLE IMPLEMENTATION DEFECT = YES / ACCEPTED / NOT REPAIRED
```

The Path-D authorization artifact, the Path-D spec, the Path-D executable and both Path-D claims are **byte-frozen history**. This lineage may read them for provenance and must **never** execute, consume, delete, rewrite, move or reference them as its own budget or namespace.

**Reviewed predecessor defect carried forward (not repaired in the frozen predecessor artifact):** Oracle-PathD used `Get-FileHash` unprotected at lines 117/118 while its availability was only checked at line 189, so the intended `HARNESS_INVALID` path was unreachable, no evidence/manifest/result was published, no listener query and no target binding were reached, the attempt ended before any ETB semantics and the process terminated with an undeclared exit code `1`. Oracle-PathE corrects the class of defect by never using that command at all; this authorization adds no further repair and must not modify either lineage's frozen artifacts.

---

## 5. Authorization identity model

### 5.1 Identity fields

| Field | Value at design-candidate stage | Populated by |
| --- | --- | --- |
| `path_e_authorization_commit` | `<future independently accepted authorization-design commit>` | the later independent acceptance record — **never** an executor |
| `path_e_authorization_sha256` | `<committed-blob SHA-256 of docs/v0.3/V03E_G0_5_PRE_ETB_PATH_E_AUTHORIZATION.md>` | the later independent acceptance record — **never** an executor |
| `oracle_path_e_commit` | `f7cafd83a95225e1ce9565a9336ded8575b65335` | §2 (frozen) |
| `oracle_path_e_spec_sha256` | `78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b` | §2 (frozen) |
| `oracle_path_e_script_sha256` | `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb` | §2 (frozen) |

**Rule:** an executor may **never** choose, compute-at-runtime, infer from HEAD, or guess `path_e_authorization_commit` or `path_e_authorization_sha256`. Both values must already exist as frozen text in the accepted control surfaces of §13.5, written there by the independent acceptance and confirmation stages. If either value is still a placeholder, the authorization is **not accepted** and no consumption may occur.

### 5.2 State model

```
DESIGN-CANDIDATE STATE (now)
  PATH-E AUTHORIZATION = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / NOT EXECUTED
  PATH-E AUTHORIZATION USE = NOT AVAILABLE FOR CONSUMPTION
  PATH-E ETB ATTEMPT       = NOT AVAILABLE FOR CONSUMPTION
  ORACLE-PATHE INVOCATIONS = NOT AUTHORIZED

POST-CONFIRMATION STATE (only after §26 completes in order)
  PATH-E AUTHORIZATION = ACCEPTED / FROZEN / EFFECTIVE
  EXECUTION AUTHORITY  = GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY
  PATH-E AUTHORIZATION USE = 1 OF 1 / AVAILABLE FOR CONSUMPTION
  PATH-E ETB ATTEMPT       = 1 OF 1 / AVAILABLE FOR CONSUMPTION
  ORACLE-PATHE INVOCATIONS = 1 OF 1 / AVAILABLE ONLY AFTER BOTH CLAIMS EXIST

CONSUMED STATE (irreversible)
  PATH-E AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
  PATH-E ETB ATTEMPT       = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
  ORACLE-PATHE INVOCATIONS = 1 OF 1 / MAXIMUM REACHED
```

**Read this block as a projection, not as a current claim.** The two blocks above are **not simultaneous**. `DESIGN-CANDIDATE STATE (now)` is the live tracked state until every stage of §5.3 has completed. `POST-CONFIRMATION STATE` is the projected state at the **future** operational consumption point — after authorization acceptance, after independent confirmation and after materialization of that confirmation as a repository-verifiable record commit — and it must **not** be asserted, claimed or evaluated as true before then. PRE-3 is the gate that reads that future state, and it separates the Oracle-PathE design effectivity layer from the Path-E execution-authorization effectivity layer from the consumable-claim layer; the requirement that the authorization be `non-effective` is a **design-candidate-stage** fact and a precondition must not require it at the operational moment.

### 5.3 Effectivity rule

This document is a **design candidate**. It becomes effective **only** through the ordered lifecycle of §26: (1) qualifying third-party independent review in a different agent/session; (2) authorization acceptance bookkeeping in exactly one single-parent commit whose sole tracked delta is `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md`; (3) a fresh independent confirmation of that bookkeeping in a different agent/session; (4) materialization of that confirmation as a repository-verifiable record commit of the same two-file shape. **No stage may be skipped, merged, collapsed, self-performed or performed by the same session twice.** Until every stage completes, **no** consumption, claim creation, listener query or Oracle invocation is permitted under this authorization.

---

## 6. Historical authorization state (permanent non-reusable markers)

The following identities and budgets are **spent, closed and non-renewable** and must never be consumed, reset, deleted, moved, re-derived or reinterpreted by this lineage:

| Historical budget | State |
| --- | --- |
| `ETB AUTHORIZATION USE` (original lineage) | `SPENT / NOT REUSABLE` |
| `ETB AUTHORIZATION USE` (Recovery-R1) | `SPENT / NOT REUSABLE` |
| `ETB ATTEMPT USE` (Recovery-R1) | `SPENT / NOT REUSABLE` |
| `ETB AUTHORIZATION USE` (Recovery-R2) | `SPENT / NOT REUSABLE` |
| `ETB ATTEMPT USE` (Recovery-R2) | `SPENT / NOT REUSABLE` |
| `ETB AUTHORIZATION USE` (D1) | `SPENT / NOT REUSABLE` |
| `ETB ATTEMPT USE` (D1) | `SPENT / NOT REUSABLE` |
| `PATH-D AUTHORIZATION USE` | `1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE` |
| `PATH-D ETB ATTEMPT` | `1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE` |
| `ORACLE-PATHD INVOCATIONS` | `1 OF 1 / MAXIMUM REACHED` |
| `ORACLE-R2 INVOCATIONS` | `MAXIMUM REACHED / NOT REUSABLE` |

**Rule:** no historical claim, authorization, budget, namespace, evidence file, manifest or result may be reused, counted, renamed, deleted or repurposed as a Path-E budget or Path-E artifact. Historical artifacts remain byte-immutable and outside this lineage's write scope.

---

## 7. New claim namespace (Path-E)

This lineage introduces exactly **two** budget claims and no others:

| Item | Path |
| --- | --- |
| authorization-use TEMP | `docs/v0.3/evidence/ETB_PATH_E_AUTHORIZATION_USE.claim.tmp` |
| authorization-use FINAL | `docs/v0.3/evidence/ETB_PATH_E_AUTHORIZATION_USE.claim` |
| attempt-use TEMP | `docs/v0.3/evidence/ETB_PATH_E_ATTEMPT_USE.claim.tmp` |
| attempt-use FINAL | `docs/v0.3/evidence/ETB_PATH_E_ATTEMPT_USE.claim` |

Both files live directly in `docs/v0.3/evidence/` — **not** inside the Path-E runtime output directory of §23, because a claim is a control object and must remain inspectable even if no output directory is ever created.

**At design-candidate stage all four paths are ABSENT** and must remain absent until an executor legitimately consumes the corresponding budget. Creating any of them by any other means (manually, by an earlier design or review round, or by copying a Path-D claim) is a control failure, not a consumption.

---

## 8. Claim-path occupancy predicate

The occupancy predicate is identity-based and deterministic; it never depends on file size, content, timestamps or directory enumeration order:

```powershell
function Test-DevRelayPathEOccupied {
    param([Parameter(Mandatory)][string]$Path)
    return ([System.IO.File]::Exists($Path) -or [System.IO.Directory]::Exists($Path))
}
```

An executor must evaluate this predicate for **all eleven** reserved Path-E paths of §23 and for both claim TEMP/FINAL pairs before consuming anything. The required design-time and pre-consumption state is:

```
PATH-E RUNTIME OCCUPANCY = 0 / 11
```

If any reserved path exists, the authorization is **not** consumable and the executor must fail closed without consuming a budget.

---

## 9. Authorization claim schema

**Schema identity:** `devrelay-etb-path-e-authorization-use-v1`

The claim is an ordered, closed, single-line JSON object serialized as UTF-8 **without BOM**, with **exactly one** terminating LF, no indentation and no extra field:

| # | Field | Required value |
| --- | --- | --- |
| 1 | `schema_version` | `devrelay-etb-path-e-authorization-use-v1` |
| 2 | `authorization_commit` | `path_e_authorization_commit` (§5.1, frozen text — never computed at runtime) |
| 3 | `authorization_sha256` | `path_e_authorization_sha256` (§5.1, frozen text — never computed at runtime) |
| 4 | `oracle_path_e_commit` | `f7cafd83a95225e1ce9565a9336ded8575b65335` |
| 5 | `oracle_path_e_spec_sha256` | `78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b` |
| 6 | `oracle_path_e_script_sha256` | `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb` |
| 7 | `state` | `CONSUMED` |

Field order is part of the contract. No field may be added, removed, reordered, truncated, padded, uppercased or reformatted. Hex digests are lowercase. The claim is **not** self-referential: it identifies this authorization and the accepted Oracle-PathE design, never itself.

---

## 10. Attempt claim schema

**Schema identity:** `devrelay-etb-path-e-attempt-use-v1`

| # | Field | Required value |
| --- | --- | --- |
| 1 | `schema_version` | `devrelay-etb-path-e-attempt-use-v1` |
| 2 | `authorization_commit` | `path_e_authorization_commit` (§5.1, frozen text — never computed at runtime) |
| 3 | `authorization_sha256` | `path_e_authorization_sha256` (§5.1, frozen text — never computed at runtime) |
| 4 | `oracle_path_e_commit` | `f7cafd83a95225e1ce9565a9336ded8575b65335` |
| 5 | `oracle_path_e_spec_sha256` | `78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b` |
| 6 | `oracle_path_e_script_sha256` | `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb` |
| 7 | `state` | `CONSUMED` |

Both schemas differ **only** in field 1. This is deliberate: an attempt may not be consumable unless its authorization was consumed first under the same frozen identities.

---

## 11. Exact frozen claim writer source

The following function is the **frozen, verbatim** consumption primitive. An executor must not re-implement it, wrap it, parameterize it differently, "improve" it, add retry logic to it, or use any other publication method. It is the only permitted way either claim may be created.

```powershell
function Write-DevRelayPathEOneShotClaim {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$TempPath,
        [Parameter(Mandatory)][string]$FinalPath,
        [Parameter(Mandatory)][string]$SchemaVersion,
        [Parameter(Mandatory)][string]$AuthorizationCommit,
        [Parameter(Mandatory)][string]$AuthorizationSha256,
        [Parameter(Mandatory)][string]$OraclePathECommit,
        [Parameter(Mandatory)][string]$OraclePathESpecSha256,
        [Parameter(Mandatory)][string]$OraclePathEScriptSha256
    )

    $ErrorActionPreference = 'Stop'

    if ([System.IO.File]::Exists($TempPath) -or [System.IO.Directory]::Exists($TempPath)) {
        throw 'DEVRELAY_CLAIM_ALREADY_PRESENT_TEMP'
    }
    if ([System.IO.File]::Exists($FinalPath) -or [System.IO.Directory]::Exists($FinalPath)) {
        throw 'DEVRELAY_CLAIM_ALREADY_PRESENT_FINAL'
    }

    $payload = [ordered]@{
        schema_version           = $SchemaVersion
        authorization_commit     = $AuthorizationCommit
        authorization_sha256     = $AuthorizationSha256
        oracle_path_e_commit     = $OraclePathECommit
        oracle_path_e_spec_sha256   = $OraclePathESpecSha256
        oracle_path_e_script_sha256 = $OraclePathEScriptSha256
        state                    = 'CONSUMED'
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

---

## 12. Consumption points and budgets

| Budget | Value | Consumed at |
| --- | --- | --- |
| `PATH_E_AUTHORIZATION_USE_BUDGET` | `1 of 1` | successful `CreateNew` of `ETB_PATH_E_AUTHORIZATION_USE.claim.tmp` |
| `PATH_E_ETB_ATTEMPT_BUDGET` | `1 of 1` | successful `CreateNew` of `ETB_PATH_E_ATTEMPT_USE.claim.tmp` |
| `ORACLE-PATHE INVOCATIONS` | `1 of 1` | the single permitted invocation of the accepted Oracle-PathE executable |

**Irreversibility rule:** the consumption point is the **successful creation of the TEMP claim**, not its publication to FINAL. Once the TEMP file exists, the budget is **spent permanently**, even if every later step fails, even if publication fails, even if the Oracle is never entered, and even if the process is killed. There is **no** mechanism to restore, refund, reset, re-open or re-issue a spent budget: no deletion of a claim, no `git reset`, no `git checkout`, no branch reset, no filesystem cleanup, no re-run of the writer, and no "second attempt" under the same authorization. Any future attempt requires an entirely new Owner-authorized lineage.

**Ordering rule:** the authorization claim is always consumed **before** the attempt claim, and the attempt claim **before** the Oracle is entered. The three budgets are strictly sequential; no step may be reordered, merged or skipped, and no step may be performed speculatively, in advance, "to save time", or as part of a dry run.

---

## 13. Pre-consumption preconditions (PRE-1 … PRE-15)

All fifteen preconditions are **mandatory, ordered and fail-closed**. An executor evaluates them in order; the **first** failure stops the round. Preconditions are evaluated **before** any claim file is created and **before** any Oracle invocation. A precondition failure consumes **no** budget and creates **no** artifact: `PATH-E AUTHORIZATION USE = 0 OF 1 / NOT CONSUMED`, `PATH-E ETB ATTEMPT = 0 OF 1 / NOT STARTED`, `ORACLE-PATHE INVOCATIONS = 0`.

| ID | Precondition | Required evidence |
| --- | --- | --- |
| **PRE-1** | Repository, branch and governance base are the expected ones | repository root `D:\DevRelay`; branch `v0.3-e-recovery-reconciliation`; the accepted Oracle-PathE design acceptance bookkeeping commit `302dd74aa9f22640eaacb34bfbbc96de93dbaa9b` is an ancestor of `HEAD`; `HEAD` is on the accepted governance line and is **not** a detached or unrelated state |
| **PRE-2** | Authorization artifact self-identity is frozen and matches the committed blob | `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_E_AUTHORIZATION.md` exists; its committed-blob SHA-256 equals the accepted `path_e_authorization_sha256`; `path_e_authorization_commit` is a committed ancestor of `HEAD` whose sole tracked delta against its parent is `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md` and the new artifact path — the accepted control surfaces already contain populated, frozen values for both `path_e_authorization_commit` and `path_e_authorization_sha256`, populated **only** through the authorization acceptance / confirmation lifecycle of §5.3, with **no unresolved angle-bracket placeholder remaining in those accepted surfaces** — and the executor did **not** choose, guess, infer from `HEAD` or rewrite either value. The **design-candidate** revision of this document is **not** required to contain its own future accepted values: a design candidate necessarily carries the two explicit placeholders of §5.1, and neither the design candidate nor the executor may rewrite this artifact to substitute them. The corrected revision of the artifact — **not** the design-candidate revision — is the artifact bound by the frozen values above |
| **PRE-3** | Oracle-PathE design effectivity, Path-E execution-authorization effectivity and consumable state are each satisfied at the future operational consumption point | this gate is evaluated at the **future** operational consumption point — immediately before the **first** irreversible authorization-use claim create — and is deliberately **not** evaluated at the design-candidate stage of this document. Three distinct states must simultaneously hold, each in its own layer: **(A) Oracle-PathE design effectivity:** the tracked status surfaces state `ORACLE-PATHE = ACCEPTED / FROZEN / EFFECTIVE`, `QUALIFYING THIRD-PARTY DESIGN REVIEW = APPROVED`, and `CORRECTIVE / SUPERSEDING ORACLE-PATHE DESIGN ACCEPTANCE BOOKKEEPING = CONFIRMED`; **(B) Path-E execution-authorization effectivity:** the accepted control surfaces state `PATH-E AUTHORIZATION = ACCEPTED / FROZEN / EFFECTIVE` with `EXECUTION AUTHORITY = GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY`; **(C) consumable state:** `PATH-E AUTHORIZATION USE = 1 OF 1 / AVAILABLE FOR CONSUMPTION` and `PATH-E ETB ATTEMPT = 1 OF 1 / AVAILABLE FOR CONSUMPTION` per §5.2, both **available but not yet consumed** — zero Path-E claims yet created — while `PATH-E RUNTIME OCCUPANCY = 0 / 11`. The requirement that the authorization be `non-effective` applies to the **design-candidate** stage only — it is the current state, recorded in §5.2 and §27 — and must **not** be required at this gate. `ORACLE-PATHE INVOCATIONS = 1 OF 1` becomes available only after both claims exist, and its revocation of availability is not required here |
| **PRE-4** | Oracle-PathE executable blob identity is exact | the blob of `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.ps1` at the accepted design commit `f7cafd83a95225e1ce9565a9336ded8575b65335`, at `HEAD`, in the index and in the worktree is the **same** blob, whose SHA-256 is `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb` |
| **PRE-5** | Oracle-PathE specification blob identity is exact | the blob of `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.md` at the accepted design commit, at `HEAD`, in the index and in the worktree is the **same** blob, whose SHA-256 is `78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b` |
| **PRE-6** | Working tree is byte-identical to `HEAD` for the governed artifacts | `git status --porcelain` reports no modification, deletion, rename or staged change for the two accepted Oracle-PathE artifacts, the authorization artifact itself, or any governed control surface; no unmerged path exists |
| **PRE-7** | Line-ending attributes resolve as frozen | `git check-attr text eol -- docs/v0.3/V03E_G0_5_PRE_ETB_PATH_E_AUTHORIZATION.md docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.ps1 docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.md` reports `text: set` and `eol: lf` for each path (no wildcard rule may be relied on) |
| **PRE-8** | No reviewed, accepted or frozen artifact has been modified | every identity in §2 and §4, `.gitattributes`, the accepted Oracle-PathE spec and executable, the Path-D spec/executable/authorization and both Path-D claims, and all historical governance commits are byte-unchanged |
| **PRE-9** | Configuration file identity is exact | `.devrelay/config.yaml` has SHA-256 `B5E4ABABF9B49F4E2BCDBA1C1DD20FC320A0EC4AEDBC98931F8595FF4416A8CF` and `1897` bytes |
| **PRE-10** | Configuration-establishment evidence identity is exact | `docs/v0.3/evidence/etb-execution/CONFIG_ESTABLISHMENT.json` has SHA-256 `EA9FC2BC564CFD6D613E3145703F28D80BB87EB89DCDECAF7AD43B52D7BD9300` and `1031` bytes |
| **PRE-11** | Historical markers are intact and unclaimed | every historical budget in §6 is still recorded as spent/closed; no historical claim, evidence, manifest or result file has been modified, deleted or added; the two Path-D claims remain byte-identical with SHA-256 `5e33a8f3da06ba36582b357fb114011e51bae30cafae1449a9c90de59f3ef017` and `64f86fcc7f3d63501b32dba5a5bf0905173002ee55d6ec008bed527472653db0` |
| **PRE-12** | All four Path-E claim paths are absent | `ETB_PATH_E_AUTHORIZATION_USE.claim{,.tmp}` and `ETB_PATH_E_ATTEMPT_USE.claim{,.tmp}` are all absent per the §8 predicate |
| **PRE-13** | The reserved Path-E runtime/output and control namespace is empty | all six output paths of §23 plus the runtime directory plus both claim FINAL paths plus both claim TEMP paths are absent: `PATH-E RUNTIME OCCUPANCY = 0 / 11` |
| **PRE-14** | No prior Path-E authorization or attempt consumption has occurred | neither Path-E claim exists in any form; no Path-E evidence, manifest or result exists; no Path-E budget is recorded as consumed anywhere in the tracked surfaces |
| **PRE-15** | No execution has occurred in this round before the preconditions passed | the executor has performed **zero** Oracle invocations, **zero** ETB attempts, **zero** listener queries, **zero** target probes, **zero** endpoint probes and **zero** OpenCode starts before PRE-1 … PRE-14 have all passed |

### 13.3 Ownership boundary frozen by the preconditions

The following belong **exclusively** to the accepted Oracle-PathE executable and are **forbidden** to the authorization layer, to the executor's orchestration, and to any helper, wrapper, diagnostic or "readiness" step:

listener query; config comparison against the live endpoint; `OwningProcess` resolution; PID resolution; `Win32_Process` lookup; `ExecutablePath` retrieval; `CreationDate` retrieval; target executable hashing; package identity validation; `package.json` validation; `CreateFileW` / `GetFinalPathNameByHandleW` canonicalization; S0 and S1 snapshot acquisition; S0/S1 continuity evaluation; and **all** ETB result classification.

The authorization layer may verify **only** static artifact identity (PRE-2, PRE-4, PRE-5, PRE-6, PRE-7, PRE-9, PRE-10) and governance/precondition state (PRE-1, PRE-3, PRE-8, PRE-11 … PRE-15). Hashing of the **accepted Oracle-PathE artifacts themselves** is permitted and required; hashing, opening, probing or enumerating the **target** is not.

---

## 14. No target pre-probe

**Prohibited by this authorization, absolutely and without exception, before the Oracle is entered and outside the Oracle:**

`Get-NetTCPConnection`; `netstat`; any TCP connection enumeration; any port-4096 probe or scan; any `localhost` probe; any `127.0.0.1` probe; any IPv6-loopback probe; any endpoint reachability check; any HTTP or HTTPS request; any `/doc`, `/session`, `/openapi.json` or equivalent endpoint call; `Test-NetConnection`; `Invoke-WebRequest`; `Invoke-RestMethod`; `curl`; `wget`; `Get-CimInstance` or `Get-WmiObject` target binding; `Get-Process` discovery of the target; `OpenCode --version` or any OpenCode start, restart or CLI query; `Get-FileHash` on the target binary; `CreateFileW` / `GetFinalPathNameByHandleW` on the target; reading the target's `package.json`; and any other read-only or read-write interaction with the target, its process, its port or its files.

**Rationale (accepted history, not re-litigated here):** in this repository's history an out-of-band listener probe during a governance round produced a real, disclosed incident and required a dedicated reconciliation; a pre-Oracle probe would additionally create an **unbudgeted ETB observation**, which the result-authority model of §21 forbids. The Oracle alone owns the single permitted listener query, executed inside its snapshot stage after all bootstrap checks.

**Consequence:** if an executor believes a target probe is necessary in order to proceed, the correct action is to **stop and fail closed** — not to probe. There is no "readiness", "diagnostic", "convenience" or "one-time" exception, and no historical observation may be reused as Path-E evidence.

---

## 15. Authorization-consumption step

After PRE-1 … PRE-15 pass, the executor performs **exactly** the following and nothing else:

```powershell
Write-DevRelayPathEOneShotClaim `
    -TempPath  'docs/v0.3/evidence/ETB_PATH_E_AUTHORIZATION_USE.claim.tmp' `
    -FinalPath 'docs/v0.3/evidence/ETB_PATH_E_AUTHORIZATION_USE.claim' `
    -SchemaVersion 'devrelay-etb-path-e-authorization-use-v1' `
    -AuthorizationCommit '<path_e_authorization_commit>' `
    -AuthorizationSha256 '<path_e_authorization_sha256>' `
    -OraclePathECommit 'f7cafd83a95225e1ce9565a9336ded8575b65335' `
    -OraclePathESpecSha256 '78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b' `
    -OraclePathEScriptSha256 'c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb'
```

The angle-bracket values are **frozen text** copied from the accepted control surfaces; they are never computed at runtime, never inferred from `HEAD` and never left as placeholders.

On success:

```
PATH-E AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
```

On any thrown error: **stop immediately**, do not retry, do not delete the TEMP file if it exists, do not proceed to §16 or §18, and report the thrown marker verbatim. The round ends as a control failure under §17.

---

## 16. Post-authorization control boundary

After §15 succeeds, the **only** permitted next action is the attempt consumption of §18. In particular, the executor may **not**: query the listener; probe the endpoint; start or restart OpenCode; read the target's files; run any diagnostic; re-evaluate the preconditions in a way that touches the target; publish anything; or invoke the Oracle before the attempt claim exists.

If the attempt claim cannot be created for any reason, the round ends as a control failure under §19. The authorization budget stays spent.

---

## 17. Authorization-control failure

If PRE-1 … PRE-15 pass but the authorization claim cannot be created, published or verified, the round fails as:

```
PATH-E AUTHORIZATION CONTROL FAILURE
```

This outcome is **not** `ETB_UNSATISFIED`, **not** `HARNESS_INVALID`, **not** an ETB semantic result and **not** `ETB_SATISFIED`. It is a control-layer failure of this authorization. Consequences:

1. no Oracle invocation occurs;
2. no ETB attempt is made and the attempt budget is **not** consumed;
3. the authorization budget remains **spent** if the TEMP claim was created, and **unspent** only if it was never created;
4. `AUTHORITATIVE ETB SEMANTIC RESULT` is **unchanged** (`ETB_UNSATISFIED / PRESERVED`);
5. no retry is permitted under this authorization.

---

## 18. ETB attempt consumption

Only after §15 succeeded, the executor performs **exactly**:

```powershell
Write-DevRelayPathEOneShotClaim `
    -TempPath  'docs/v0.3/evidence/ETB_PATH_E_ATTEMPT_USE.claim.tmp' `
    -FinalPath 'docs/v0.3/evidence/ETB_PATH_E_ATTEMPT_USE.claim' `
    -SchemaVersion 'devrelay-etb-path-e-attempt-use-v1' `
    -AuthorizationCommit '<path_e_authorization_commit>' `
    -AuthorizationSha256 '<path_e_authorization_sha256>' `
    -OraclePathECommit 'f7cafd83a95225e1ce9565a9336ded8575b65335' `
    -OraclePathESpecSha256 '78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b' `
    -OraclePathEScriptSha256 'c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb'
```

On success:

```
PATH-E ETB ATTEMPT = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
```

Only now may the Oracle be entered. If the attempt claim cannot be created, the round ends under §19; the authorization budget remains spent and the attempt budget is either spent (TEMP created) or unspent (TEMP never created) — never restored.

---

## 19. Post-attempt-claim failure

If the attempt claim was created but any step between its creation and the Oracle entry fails, the round fails closed:

```
PATH-E ETB ATTEMPT CLAIM = PRESENT / 1 OF 1 / SPENT / IRREVERSIBLE
ORACLE-PATHE = NOT ENTERED
AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED
```

The executor must **stop**, must not delete either claim, must not retry, must not enter the Oracle "anyway", and must not attempt to republish or repair the claim. Both budgets remain spent and the round is a control failure.

---

## 20. Oracle entry boundary and exact invocation

Only after §18 succeeded may the Oracle be entered, and then only with this **exact** command line, from the repository root, with **no** parameters, **no** wrapper script, **no** alternate implementation, **no** substituted executable and **no** modified copy:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.ps1"
```

Frozen target semantics carried unchanged from the accepted lineage (the Oracle owns all of them; this authorization merely records what must not be weakened):

| Item | Frozen value / rule |
| --- | --- |
| `configured_base_url` | `http://127.0.0.1:4096` |
| listener predicate | `LocalAddress = 127.0.0.1` / `LocalPort = 4096` / `State = Listen` |
| mode | `MODE = P / PRE-EXISTING TARGET` |
| target executable path | `C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe` |
| target binary SHA-256 | `578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35` |
| target package | `opencode-ai` |
| target version | `1.18.11` |
| target bin identity | `opencode` |
| forbidden | endpoint discovery; fallback endpoint; alternate port; `localhost` alias; IPv6 alternate; OpenCode start or restart; HTTP requests; `/doc`; `/session`; provider or model calls |

The Oracle's own identity binding, listener ownership, target-binding sequence, S0/S1 continuity evaluation, publication order (evidence → manifest → result last), fail-closed publication model and exit-code contract (`0` / `2` / `3` / `4`) are owned by the **accepted** Oracle-PathE specification and are **not** restated, amended, weakened or extended here.

---

## 21. Result authority — observation vs authoritative semantic result

A Path-E Oracle invocation produces a **raw observation** published into the reserved output namespace of §23. That observation is **not** immediately the authoritative ETB semantic result.

**Promotion pipeline (all stages mandatory, in order, each in a different agent/session where independence is required):**

1. Path-E execution publishes a raw, self-describing observation artifact (evidence, manifest, result) with exactly one of the three closed classes of §22;
2. **independent result review** of that raw observation by a qualifying third party;
3. **result bookkeeping** in exactly one single-parent commit whose sole tracked delta is `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md`;
4. **independent confirmation** of that bookkeeping, materialized as a repository-verifiable record commit of the same two-file shape.

Only after all four stages does a new ETB semantic result become authoritative. Until then:

```
AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED
```

This authorization, its acceptance, its claims, its consumption and the Oracle invocation itself **never** replace the authoritative ETB semantic result. A raw observation that has not completed the pipeline is **never** cited as the authoritative result, and no stage of this lineage may silently promote it.

---

## 22. Result classes (closed)

Exactly three ETB semantic classes exist, and this authorization may not add, rename, split, merge or reorder them:

| Class | Meaning |
| --- | --- |
| `ETB_SATISFIED` | the target semantics were established and satisfied |
| `ETB_UNSATISFIED` | the target semantics were evaluated and not satisfied |
| `HARNESS_INVALID / NO ETB SEMANTIC RESULT` | the harness could not evaluate the semantics; no ETB semantic result exists |

**Forbidden:** `PASS`, `FAIL`, `PARTIAL`, `UNKNOWN`, `PROBABLE`, `RETRY`, `ERROR`, `BLOCKED` or any other class name as an ETB **result** class. The historical Path-D phrase `UNCLASSIFIED CONTROL FAILURE` is **not** a class of this lineage and must not be resurrected as one; it remains Path-D governance history describing a control-layer outcome that produced `PATH-D ETB SEMANTIC RESULT = NONE`.

Any class preselection, inference from a prior lineage, or classification by anyone other than the accepted Oracle-PathE executable is void.

---

## 23. Artifact model, MODEL A and operational inventory

### 23.1 MODEL A (preserved)

Runtime artifacts produced by a future authorized execution are **generated operational files**: they live in the reserved namespace below, they remain **untracked**, and they are **byte-immutable** once published. Tracked governance advances **only** through the two established active status surfaces:

```
CHANGELOG.md
docs/v0.3/V03E_ACCEPTANCE.md
```

No runtime or generated artifact may become tracked; no governance fact may be recorded by creating a runtime file.

### 23.2 Reserved Path-E runtime / output namespace (design only — nothing is created)

| # | Reserved path | State now |
| --- | --- | --- |
| 1 | `docs/v0.3/evidence/etb-execution-path-e/` (runtime directory) | ABSENT |
| 2 | `docs/v0.3/evidence/etb-execution-path-e/ETB_EVIDENCE.json.tmp` | ABSENT |
| 3 | `docs/v0.3/evidence/etb-execution-path-e/ETB_EVIDENCE.json` | ABSENT |
| 4 | `docs/v0.3/evidence/etb-execution-path-e/MANIFEST.sha256.tmp` | ABSENT |
| 5 | `docs/v0.3/evidence/etb-execution-path-e/MANIFEST.sha256` | ABSENT |
| 6 | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_E.md.tmp` | ABSENT |
| 7 | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_E.md` | ABSENT |
| 8 | `docs/v0.3/evidence/ETB_PATH_E_AUTHORIZATION_USE.claim.tmp` | ABSENT |
| 9 | `docs/v0.3/evidence/ETB_PATH_E_AUTHORIZATION_USE.claim` | ABSENT |
| 10 | `docs/v0.3/evidence/ETB_PATH_E_ATTEMPT_USE.claim.tmp` | ABSENT |
| 11 | `docs/v0.3/evidence/ETB_PATH_E_ATTEMPT_USE.claim` | ABSENT |

```
PATH-E RUNTIME NAMESPACE = 11 PATHS
PATH-E RUNTIME OCCUPANCY = 0 / 11
```

**No Path-D output path may be referenced, reused or written anywhere in this lineage.** The future evidence schema identity is `devrelay-etb-v1-path-e`.

---

## 24. Historical immutability

This authorization round creates **no** execution authority, consumes **no** budget, creates **no** claim and modifies **no** frozen artifact. Frozen and unchangeable, before and after this round:

`f7cafd83a95225e1ce9565a9336ded8575b65335`; `302dd74aa9f22640eaacb34bfbbc96de93dbaa9b`; `fe2963fea5d2e8e9c20db52902c71bee3a883fa3`; `eb54fde563524f51d4e729655639a7c0386cb43a`; `a5e592bd9265fe4f20a97ed10d7ed39b4531be98`; both accepted Oracle-PathE artifacts; `.gitattributes`; the Path-D spec, executable, authorization artifact and both claims; the Recovery-R1, Recovery-R2, D1, Oracle-R2 and original-oracle artifacts; all configuration and construction-time banners; and the four recorded non-blocking Oracle-PathE design-review observations (`P3-1 / O-1` publication-region SHA-256 object not disposed; `P3-2 / O-2` spec §6 `ConvertFrom-Json` listed twice against three executable sites; `P3-3 / O-3` spec §17 base `DESIGN CANDIDATE` terminology retained; `P3-4` spec §4.2 narrative enumeration precision), which remain `NONBLOCKING / NOT REPAIRED / NO EXECUTABLE SEMANTIC IMPACT` and must **not** be "fixed" by editing a reviewed or accepted byte.

**`a5e592bd9265fe4f20a97ed10d7ed39b4531be98` remains** `HISTORICAL / NOT CONFIRMED / NOT EFFECTIVE FOR ACCEPTANCE / SUPERSEDED FOR REVIEW-AUTHORITY PURPOSES` — it is not reopened, re-confirmed, rewritten or reused as review authority.

---

## 25. Self-sufficiency

To consume this authorization and invoke the Oracle, an executor needs **only**:

1. this authorization artifact (`docs/v0.3/V03E_G0_5_PRE_ETB_PATH_E_AUTHORIZATION.md`), with its frozen `path_e_authorization_commit` and `path_e_authorization_sha256`;
2. the accepted Oracle-PathE specification and executable, at the frozen hashes of §2;
3. the accepted control-state markers in the two active status surfaces;
4. the frozen claim writer of §11;
5. the repository working copy.

No chat history, conversation transcript, agent memory, external testimony, clipboard content, environment variable, out-of-band note or undocumented convention may be required, consulted or trusted. If any required value is missing, the executor fails closed.

---

## 26. Authoritative sequence and effectivity model

The following order is frozen. **No stage may be skipped, merged, collapsed, reordered, self-performed or repeated by the same session.**

```
1. Path-E authorization design candidate (this document, committed)
2. QUALIFYING THIRD-PARTY INDEPENDENT REVIEW of this candidate (different agent/session)
3. Path-E authorization acceptance bookkeeping
      = exactly ONE single-parent commit whose sole tracked delta is
        M CHANGELOG.md + M docs/v0.3/V03E_ACCEPTANCE.md
4. FRESH INDEPENDENT CONFIRMATION of that acceptance bookkeeping (different agent/session)
5. materialization of that confirmation as a repository-verifiable record commit
      = exactly ONE single-parent commit of the same two-file shape
6. only now: PATH-E AUTHORIZATION = ACCEPTED / FROZEN / EFFECTIVE
      EXECUTION AUTHORITY = GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY
7. fresh operational execution session performs §13 → §20 in order
```

Independence declarations required at stage 2 (recorded **before** any technical conclusion):

```
THIRD-PARTY REVIEWER SESSION SEPARATION = SATISFIED
REVIEWER WAS NOT THE AUTHORIZATION-CANDIDATE-AUTHOR SESSION = YES
REVIEWER DID NOT PREVIOUSLY REVIEW THIS EXACT AUTHORIZATION OBJECT = YES
```

and at stage 4, additionally: `REVIEWER WAS NOT THE AUTHORIZATION-ACCEPTANCE-BOOKKEEPING-AUTHOR SESSION = YES`.

**Stage 6 is the only point at which this authorization becomes usable, and it is unusable until then.** Committing this document, reviewing it, accepting it or confirming it does **not**, by itself, consume, grant or release any budget.

---

## 27. Current status

```
ORACLE-PATHE                          = ACCEPTED / FROZEN / EFFECTIVE
Accepted design identity              = f7cafd83a95225e1ce9565a9336ded8575b65335
Accepted spec SHA-256                 = 78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b
Accepted script SHA-256               = c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb
AUTHORIZATION DESIGN CANDIDATE       = 26b183083fbbe323441283f99f3cf2c931acd6ff
QUALIFYING THIRD-PARTY AUTHORIZATION DESIGN REVIEW OF 26B1830 = REQUEST_CHANGES
Authorization design review severity = P0 = 0 / P1 = 0 / P2 = 2 / P3 = 3
Authorization design review blocking findings = P2-1 PRE-2 UNSATISFIABLE SELF-IDENTITY GATE; P2-2 PRE-3 CONTRADICTORY EFFECTIVITY GATE
AUTHORIZATION DESIGN CANDIDATE 26B1830 = HISTORICAL REJECTED CANDIDATE / SUPERSEDED BY A CORRECTED SUCCESSOR
CORRECTED AUTHORIZATION DESIGN CANDIDATE = COMMITTED / REVIEW REQUIRED
ORACLE-PATHE REVIEW AUTHORITY         = the tokens `QUALIFYING THIRD-PARTY DESIGN REVIEW = APPROVED`, `CORRECTIVE / SUPERSEDING ORACLE-PATHE DESIGN ACCEPTANCE BOOKKEEPING = CONFIRMED`, `ORACLE-PATHE = ACCEPTED / FROZEN / EFFECTIVE` record the **Oracle-PathE design** effectivity only; they are **not** a verdict on the Path-E execution-authorization design candidate, which stands separately as 26B1830 / REQUEST_CHANGES / superseded by a corrected successor
PATH-E AUTHORIZATION                  = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / NOT EXECUTED
PATH-E AUTHORIZATION USE              = NOT AVAILABLE FOR CONSUMPTION
PATH-E ETB ATTEMPT                    = NOT AVAILABLE FOR CONSUMPTION
PATH-E ETB EXECUTION                  = NOT AUTHORIZED
ORACLE-PATHE EXECUTION                = NOT AUTHORIZED
ORACLE-PATHD EXECUTION                = NOT AUTHORIZED
PATH-E RUNTIME OCCUPANCY              = 0 / 11
PATH-E CLAIM PATHS                    = ABSENT (4 / 4)
LISTENER QUERY                        = NOT EXECUTED
TARGET PROBE                          = NOT EXECUTED
AUTHORITATIVE ETB SEMANTIC RESULT     = ETB_UNSATISFIED / PRESERVED
PATH-D                                = EXHAUSTED / CLOSED / IMMUTABLE
PATH-D AUTHORIZATION USE              = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
PATH-D ETB ATTEMPT                    = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
ORACLE-PATHD INVOCATIONS              = 1 OF 1 / MAXIMUM REACHED
PATH-D ETB SEMANTIC RESULT            = NONE
PATH-D RETRY AUTHORITY                = NONE
A5E592BD BOOKKEEPING                  = HISTORICAL / NOT CONFIRMED / NOT EFFECTIVE FOR ACCEPTANCE / SUPERSEDED FOR REVIEW-AUTHORITY PURPOSES
MODEL A                               = PRESERVED
NEXT STAGE                            = FRESH QUALIFYING THIRD-PARTY INDEPENDENT REVIEW OF THE CORRECTED PATH-E EXECUTION-AUTHORIZATION DESIGN CANDIDATE
```

---

## 28. Fail-closed / no-retry contract

1. Every precondition failure stops the round **before** consumption.
2. Every post-consumption failure stops the round **after** consumption, permanently.
3. No retry, no rerun, no second attempt, no automatic re-invocation, no backoff loop, no `Start-Sleep`-and-retry and no "try the other port" path exists anywhere in this authorization.
4. No claim is ever deleted, truncated, moved, overwritten, renamed or reset — not to clean up, not to "unstick" a run, not to recover a budget.
5. A spent budget is spent forever, regardless of the outcome, and regardless of who observes it afterwards.
6. `git reset`, `git checkout`, branch switching, stashing, cleaning, rebasing, amending or force-updating **never** restores a budget and never un-consumes a claim.
7. An unavailable facility, an unexpected host failure, a publication failure and a control failure are all **fail-closed**: they never produce `ETB_SATISFIED`, never produce a semantic result and never silently promote an observation.
8. If any required value, artifact, attribute or precondition cannot be verified, the correct action is to **stop and report**, not to proceed, improvise, approximate or ask a later stage to fix it.

---

## 29. Activity counters

```
PATH-E AUTHORIZATION DESIGN ROUND
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
  reviewed-artifact mutations            = 0
  historical-lineage reopenings          = 0
  Path-D modifications                   = 0
  runtime / test / dependency / version changes = 0
  repository modifications beyond the authorization candidate and the status surfaces = 0
  tags / releases / pushes               = 0
```

### 29.1 Preserved non-claims

This authorization is **NOT** `SIC`; **NOT** `P6`; **NOT** `G0.5` completion; **NOT** a `MODE-B RESULT`; **NOT** a `CASE-C AUTHORIZATION`; **NOT** an adoption authorization; **NOT** a retry authorization for any lineage; **NOT** a general license to query a listener; and **NOT** an ETB result of any class. It claims no accepted status for itself.

---

**End of Path-E one-shot ETB execution authorization, design candidate.**




