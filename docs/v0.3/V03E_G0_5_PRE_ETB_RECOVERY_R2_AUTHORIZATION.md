# DevRelay v0.3-E — G0.5-PRE / SIC — Recovery-R2 one-shot ETB execution authorization

> **RECOVERY-R2 ONE-SHOT ETB EXECUTION AUTHORIZATION**
> **DESIGN CANDIDATE**
> **NOT ACCEPTED**
> **NOT EFFECTIVE**
> **NOT EXECUTED**
> **GRANTS NO EXECUTION AUTHORITY TODAY**
> **CREATES NO CLAIM NOW**
> **DOES NOT ENTER ORACLE-R2**
> **ONE AUTHORIZATION USE + ONE ETB ATTEMPT ONLY IF LATER INDEPENDENTLY ACCEPTED**

Status: **RECOVERY-R2 AUTHORIZATION = DESIGN CANDIDATE / NOT ACCEPTED / NOT GRANTED / NOT EXECUTED**

Baseline: `9b17912a8b4bd6c87aa45eefc97a73eb3d22db34` (branch `v0.3-e-recovery-reconciliation`), the
independently confirmed Oracle-R2 acceptance-bookkeeping baseline.

This is a **new authorization artifact**.  It is **not** a revision of
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_AUTHORIZATION.md` (original Round-5 authorization) or of
`docs/v0.3/V03E_G0_5_PRE_ETB_RECOVERY_AUTHORIZATION.md` (Recovery-R1 authorization); both are immutable and
must not be modified.  It authorizes nothing today: it creates no claim, mutates no configuration, publishes
no evidence, performs no endpoint/listener/process probe and does not enter Oracle-R2.  It becomes effective
**only** if a separate independent Recovery-R2 authorization review accepts it.

## 1. Purpose and scope

**1.1** This artifact defines an **independently reviewable one-shot Recovery-R2 authorization** for exactly
**one** future ETB attempt executed by the **already accepted, frozen** tracked Oracle-R2 executable.

**1.2** It binds permanently to the accepted Oracle-R2 identity triple, uses a **completely new** Recovery-R2
claim namespace, provides exactly **one** authorization-use budget and exactly **one** ETB-attempt budget,
verifies the accepted executable bytes **before** authorization consumption, performs **no** config mutation,
performs **no** target/listener/process probe before the oracle, executes the tracked Oracle-R2 script
**directly** in the future operational round, and permits **no** retry, **no** fallback and **no**
executor-authored assertion or wrapper.

**1.3** Design scope only.  This round performs no execution, creates no claim, creates no R2 output, and does
not create `docs/v0.3/evidence/etb-execution-r2/`.

## 2. Accepted Oracle-R2 provenance (permanent, immutable)

| Item | Value |
| --- | --- |
| `oracle_r2_commit` | `dfb78f34d919e8c9863a8398fb4f63ee301167bc` |
| `oracle_r2_spec_sha256` | `5e9221e3950af6ec3e0612c4d962562c33e761899dfd6af42d10f5a9895f9f2f` |
| `oracle_r2_script_sha256` | `22c5fbd61da609e6cc39e973be6030d4c360019ed1f56e69ca45f92fa1689c17` |
| Oracle-R2 spec path | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.md` |
| Oracle-R2 script path | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1` |
| Oracle-R2 status | `ACCEPTED / FROZEN / NOT EXECUTED` |

**2.1** The triple above is the **permanently accepted Oracle-R2 identity**.  A later acceptance-bookkeeping
HEAD, an operational HEAD or a result-review HEAD must **not** replace any of these values.

**2.2** `EXECUTION AUTHORITY = NOT GRANTED` until this Recovery-R2 authorization is independently accepted
**and** its use budget is consumed exactly as frozen below.

## 3. Recovery-R2 authorization identity model

**3.1** If this candidate is later independently accepted:

```
recovery_r2_authorization_commit = <future independently accepted authorization-design commit>
recovery_r2_authorization_sha256 = <committed-blob SHA-256 of
                                    docs/v0.3/V03E_G0_5_PRE_ETB_RECOVERY_R2_AUTHORIZATION.md>
```

**3.2** Both values are **UNKNOWN** until this design candidate is committed and independently approved.
They are populated **only** by the later independent approval record; they are **not** executor choices.

**3.3** The future Recovery-R2 authorization claim and attempt claim MUST bind to **both**
`recovery_r2_authorization_commit` and `recovery_r2_authorization_sha256` **and** to the permanent accepted
Oracle-R2 triple of §2.

**3.4** A later acceptance-bookkeeping HEAD, operational HEAD or result-review HEAD must **not** replace any
of those provenance values.

## 4. Historical authorization state (permanent record; not reusable)

**4.1** Original Round-5 authorization:

| Item | Value |
| --- | --- |
| original `authorization_commit` | `64044fc45082cd63b0ae445c146d85720dfa1435` |
| original `authorization_sha256` | `511ab1e2eb2e4f1194d2c55951e5b9616dc515d1180c6399dd658207d443d0d8` |
| original authorization claim FINAL | `docs/v0.3/evidence/ETB_AUTHORIZATION_USE.claim` — **OCCUPIED** |
| original claim SHA-256 | `d84b428586f07a55a99f5b1391481d77763ec4ea697a40d1cec8aa0779613d4e` |
| original ETB attempt claim TEMP | `docs/v0.3/evidence/ETB_ATTEMPT_USE.claim.tmp` — **ABSENT** |
| original ETB attempt claim FINAL | `docs/v0.3/evidence/ETB_ATTEMPT_USE.claim` — **ABSENT** |

```
ORIGINAL AUTHORIZATION = SPENT / NOT REUSABLE
ORIGINAL ETB ATTEMPT   = 0/1 HISTORICAL ATTEMPT NEVER STARTED  (NOT REUSABLE: parent authorization is spent)
```

**4.2** Recovery-R1 authorization:

| Item | Value |
| --- | --- |
| Recovery-R1 authorization claim | `docs/v0.3/evidence/ETB_RECOVERY_R1_AUTHORIZATION_USE.claim` — **OCCUPIED** |
| Recovery-R1 authorization claim SHA-256 | `8876bcc603ebf0f858902e7cce7e98096bdaa1f71768c9346a7b3acc6e4620b9` |
| Recovery-R1 ETB attempt claim | `docs/v0.3/evidence/ETB_RECOVERY_R1_ATTEMPT_USE.claim` — **OCCUPIED** |
| Recovery-R1 ETB attempt claim SHA-256 | `5f1e9721ed89355940f76d2cb868efec768a85ea957b9f92ba395b72fd4f97d2` |

```
RECOVERY-R1 AUTHORIZATION = SPENT / NOT REUSABLE
RECOVERY-R1 ETB ATTEMPT   = SPENT / NOT REUSABLE
```

**4.3** None of these historical markers may be modified, deleted, renamed, archived, committed, normalized,
reused by path, or treated as UNUSED.  They are permanent control-state witnesses.

## 5. New Recovery-R2 claim namespace (permanently distinct)

Freeze **exactly** these four paths:

| Marker | Temp path | Final path |
| --- | --- | --- |
| Recovery-R2 authorization claim | `docs/v0.3/evidence/ETB_RECOVERY_R2_AUTHORIZATION_USE.claim.tmp` | `docs/v0.3/evidence/ETB_RECOVERY_R2_AUTHORIZATION_USE.claim` |
| Recovery-R2 ETB attempt claim | `docs/v0.3/evidence/ETB_RECOVERY_R2_ATTEMPT_USE.claim.tmp` | `docs/v0.3/evidence/ETB_RECOVERY_R2_ATTEMPT_USE.claim` |

**5.1** These paths are permanently distinct from the original Round-5 claim namespace
(`ETB_AUTHORIZATION_USE.claim`, `ETB_ATTEMPT_USE.claim`), from the Recovery-R1 claim namespace
(`ETB_RECOVERY_R1_AUTHORIZATION_USE.claim`, `ETB_RECOVERY_R1_ATTEMPT_USE.claim`) and from **all** oracle
output namespaces.  **No historical claim path may be reused.**

**5.2** No other claim path may be created under this authorization.

## 6. Claim-path occupancy predicate (frozen)

```
CLAIM_PATH_OCCUPIED(path) := [System.IO.File]::Exists(path) -or [System.IO.Directory]::Exists(path)
ABSENT                    := File.Exists(path) == false AND Directory.Exists(path) == false
```

**6.1** A file, a **directory**, a partial file, a malformed file or a zero-length file at one of these exact
paths counts as **OCCUPIED** and fails closed.

**6.2** No deletion.  No cleanup.  No overwrite.  No rename of historical claim markers.

## 7. Authorization claim schema (new, exact, closed)

```
schema_version = devrelay-etb-recovery-r2-authorization-use-v1
```

Exact ordered fields (7):

| # | Field |
| --- | --- |
| 1 | `schema_version` |
| 2 | `authorization_commit` |
| 3 | `authorization_sha256` |
| 4 | `oracle_r2_commit` |
| 5 | `oracle_r2_spec_sha256` |
| 6 | `oracle_r2_script_sha256` |
| 7 | `state` |

Exact value: `state = CONSUMED`.  No timestamp, no hostname, no PID, no operator, no comment, **no extra
field**.  Encoding: UTF-8, **no BOM**, exactly one final LF.

## 8. Attempt claim schema (new, exact, closed)

```
schema_version = devrelay-etb-recovery-r2-attempt-use-v1
```

Exact ordered fields (7): identical field list and order to §7, with the attempt `schema_version` value.
Exact value: `state = CONSUMED`.  **No extra field.**  Encoding: UTF-8, **no BOM**, exactly one final LF.

## 9. Exact frozen claim writer source

**9.1** The future executor MUST use the following function **verbatim**.  It must **not** be rewritten,
translated, replaced by an equivalent writer, or supplemented.  No Python, no `Set-Content`, no `Out-File`,
no alternate serializer.

**9.2** Frozen serialization depth: `ConvertTo-Json -Depth 4 -Compress` (sufficient for the flat 7-field
object; this exact value is frozen).

**9.3** If `TEMP` `CreateNew` succeeds, the corresponding one-shot budget is **consumed** even if a later
write, flush, read-back or move step fails.  **No deletion on failure** — the consumed marker remains as
evidence.

```powershell
function Write-DevRelayRecoveryR2OneShotClaim {
    param(
        [Parameter(Mandatory = $true)]
        [string] $TempPath,

        [Parameter(Mandatory = $true)]
        [string] $FinalPath,

        [Parameter(Mandatory = $true)]
        [string] $SchemaVersion,

        [Parameter(Mandatory = $true)]
        [string] $AuthorizationCommit,

        [Parameter(Mandatory = $true)]
        [string] $AuthorizationSha256,

        [Parameter(Mandatory = $true)]
        [string] $OracleR2Commit,

        [Parameter(Mandatory = $true)]
        [string] $OracleR2SpecSha256,

        [Parameter(Mandatory = $true)]
        [string] $OracleR2ScriptSha256
    )

    $ErrorActionPreference = 'Stop'

    if (
        [System.IO.File]::Exists($TempPath) -or
        [System.IO.Directory]::Exists($TempPath)
    ) {
        throw "DEVRELAY_CLAIM_ALREADY_PRESENT_TEMP"
    }

    if (
        [System.IO.File]::Exists($FinalPath) -or
        [System.IO.Directory]::Exists($FinalPath)
    ) {
        throw "DEVRELAY_CLAIM_ALREADY_PRESENT_FINAL"
    }

    $claim = [ordered]@{
        schema_version        = $SchemaVersion
        authorization_commit  = $AuthorizationCommit
        authorization_sha256  = $AuthorizationSha256
        oracle_r2_commit      = $OracleR2Commit
        oracle_r2_spec_sha256 = $OracleR2SpecSha256
        oracle_r2_script_sha256 = $OracleR2ScriptSha256
        state                 = 'CONSUMED'
    }

    $json = $claim | ConvertTo-Json -Depth 4 -Compress

    $text = $json + "`n"

    $encoding = [System.Text.UTF8Encoding]::new($false)

    $bytes = $encoding.GetBytes($text)

    $stream = $null

    try {
        $stream = [System.IO.FileStream]::new(
            $TempPath,
            [System.IO.FileMode]::CreateNew,
            [System.IO.FileAccess]::Write,
            [System.IO.FileShare]::None
        )

        $stream.Write($bytes, 0, $bytes.Length)

        $stream.Flush($true)
    }
    finally {
        if ($null -ne $stream) {
            $stream.Dispose()
        }
    }

    $tempBytes = [System.IO.File]::ReadAllBytes($TempPath)

    if ($tempBytes.Length -ne $bytes.Length) {
        throw "DEVRELAY_CLAIM_TEMP_LENGTH_MISMATCH"
    }

    for ($i = 0; $i -lt $bytes.Length; $i++) {
        if ($tempBytes[$i] -ne $bytes[$i]) {
            throw "DEVRELAY_CLAIM_TEMP_BYTE_MISMATCH"
        }
    }

    if (
        [System.IO.File]::Exists($FinalPath) -or
        [System.IO.Directory]::Exists($FinalPath)
    ) {
        throw "DEVRELAY_CLAIM_FINAL_APPEARED"
    }

    [System.IO.File]::Move(
        $TempPath,
        $FinalPath
    )

    $finalBytes = [System.IO.File]::ReadAllBytes($FinalPath)

    if ($finalBytes.Length -ne $bytes.Length) {
        throw "DEVRELAY_CLAIM_FINAL_LENGTH_MISMATCH"
    }

    for ($i = 0; $i -lt $bytes.Length; $i++) {
        if ($finalBytes[$i] -ne $bytes[$i]) {
            throw "DEVRELAY_CLAIM_FINAL_BYTE_MISMATCH"
        }
    }

    if (
        [System.IO.File]::Exists($TempPath) -or
        [System.IO.Directory]::Exists($TempPath)
    ) {
        throw "DEVRELAY_CLAIM_TEMP_STILL_PRESENT_AFTER_PUBLICATION"
    }

    if (-not [System.IO.File]::Exists($FinalPath)) {
        throw "DEVRELAY_CLAIM_FINAL_NOT_OCCUPIED_AS_FILE_AFTER_PUBLICATION"
    }
}
```

**9.4 Writer semantics mapping (normative, complete):** A temp occupancy evaluation with the §6 predicate;
B final occupancy evaluation with the §6 predicate; C either occupied → fail closed **before** creation;
D construct one `[ordered]` object using the relevant exact 7-field schema of §7/§8; E `ConvertTo-Json` at
the frozen depth of §9.2; F compressed JSON; G append exactly one LF; H encode with
`[System.Text.UTF8Encoding]::new($false)`; I create TEMP with `FileMode.CreateNew`, `FileAccess.Write`,
`FileShare.None`; J the successful `CreateNew` return is the **exact consumption point**; K write all bytes;
L `Flush($true)`; M `Dispose`; N `ReadAllBytes(TEMP)`; O verify byte-for-byte equality; P publish with the
exact two-argument `[System.IO.File]::Move($TempPath, $FinalPath)` (**no overwrite**); Q `ReadAllBytes(FINAL)`;
R verify byte-for-byte equality; S require TEMP **ABSENT** after successful publication; T require FINAL
**OCCUPIED AS FILE** after publication.

## 10. Consumption points and budgets

| State variable | Budget |
| --- | --- |
| `RECOVERY_R2_AUTHORIZATION_USE_BUDGET` | **1 of 1** |
| `RECOVERY_R2_ETB_ATTEMPT_BUDGET` | **1 of 1** |

**10.1** The **authorization** budget is consumed at the successful `CreateNew` of
`docs/v0.3/evidence/ETB_RECOVERY_R2_AUTHORIZATION_USE.claim.tmp`.

**10.2** The **ETB attempt** budget is consumed at the successful `CreateNew` of
`docs/v0.3/evidence/ETB_RECOVERY_R2_ATTEMPT_USE.claim.tmp`.

**10.3** Consumed means **permanently consumed**.  No independent review may reopen a consumed marker.

## 11. Pre-consumption preconditions (ALL before Recovery-R2 authorization consumption)

No additional precondition may be invented operationally.  Every check is **read-only**.

| ID | Required condition |
| --- | --- |
| **PRE-1** | current bookkeeping baseline `HEAD` equals the independently confirmed baseline `9b17912a8b4bd6c87aa45eefc97a73eb3d22db34` |
| **PRE-2** | current branch is `v0.3-e-recovery-reconciliation` |
| **PRE-3** | the accepted Oracle-R2 spec committed blob at `dfb78f34d919e8c9863a8398fb4f63ee301167bc` hashes exactly `5e9221e3950af6ec3e0612c4d962562c33e761899dfd6af42d10f5a9895f9f2f` |
| **PRE-4** | the accepted Oracle-R2 script committed blob at that same accepted commit hashes exactly `22c5fbd61da609e6cc39e973be6030d4c360019ed1f56e69ca45f92fa1689c17` |
| **PRE-5** | the **current worktree** Oracle-R2 script bytes are **byte-identical** to that accepted committed blob (no normalized-equivalent acceptance) |
| **PRE-6** | read-only git attribute check resolves the normative script to `text: set` and `eol: lf` |
| **PRE-7** | the tracked worktree contains **no** tracked modification and **no** staged path; the seven historical R1 operational artifacts may remain untracked exactly as accepted |
| **PRE-8** | `.devrelay/config.yaml` is present with `SHA-256 = b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf`, `size = 1897`, and production-resolved `opencode.base_url = http://127.0.0.1:4096` |
| **PRE-9** | `CONFIG_ESTABLISHMENT` is present exactly at `docs/v0.3/evidence/etb-execution/CONFIG_ESTABLISHMENT.json` with `SHA-256 = ea9fc2bc564cfd6d613e3145703f28d80bb87eb89dcdecaf7ad43b52d7bd9300` (accepted semantic status remains `VALID / PRESENT`) |
| **PRE-10** | the original spent authorization claim exists with expected SHA-256 `d84b428586f07a55a99f5b1391481d77763ec4ea697a40d1cec8aa0779613d4e` |
| **PRE-11** | the Recovery-R1 authorization claim exists with expected SHA-256 `8876bcc603ebf0f858902e7cce7e98096bdaa1f71768c9346a7b3acc6e4620b9` |
| **PRE-12** | the Recovery-R1 ETB attempt claim exists with expected SHA-256 `5f1e9721ed89355940f76d2cb868efec768a85ea957b9f92ba395b72fd4f97d2` |
| **PRE-13** | **all four** Recovery-R2 claim paths of §5 are **ABSENT** under the §6 occupancy predicate |
| **PRE-14** | this Recovery-R2 authorization artifact itself matches its independently accepted future `recovery_r2_authorization_commit` and `recovery_r2_authorization_sha256` |
| **PRE-15** | **no** Recovery-R2 authorization claim has yet been consumed |
| **PRE-16** | **no** Recovery-R2 ETB attempt claim has yet been consumed |

**11.1** PRE-15 and PRE-16 are the consumed-state confirmations: because a consumption point is the
successful `CreateNew` of the corresponding TEMP path, either TEMP or FINAL occupancy at those exact paths
means the budget is already consumed.  They are therefore physically entailed by the PRE-13 ABSENT result;
no separate probe beyond the §6 predicate is permitted.

**11.2** PRE-8 production resolution uses **only** the reader invocation shape already frozen for Oracle-R2
(`PYTHONPATH=<repo>/src python -c "<frozen reader source>" "<repo>"`), with the frozen repository root as the
single repository argument.  No alternative parser, no raw-YAML parser and no regex extraction is permitted.

**11.3** Failure of **any** PRE-* condition → **STOP BEFORE CONSUMING ANYTHING**.  No repair.  No retry.  No
fallback.  No claim is created, no config is touched, no oracle is entered.

## 12. Critical oracle-output precheck rule

**12.1** The authorization layer MUST NOT inspect the six Oracle-R2 output paths.  Specifically, before the
ETB attempt claim and Oracle-R2 entry, it must **not** inspect, stat, open, test, create or repair:

```
docs/v0.3/evidence/etb-execution-r2/ETB_EVIDENCE.json
docs/v0.3/evidence/etb-execution-r2/ETB_EVIDENCE.json.tmp
docs/v0.3/evidence/etb-execution-r2/MANIFEST.sha256
docs/v0.3/evidence/etb-execution-r2/MANIFEST.sha256.tmp
docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_R2.md
docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_R2.md.tmp
```

**12.2** The Oracle-R2 executable **owns** its own six-path precondition.  The authorization layer must not
duplicate it.  This preserves the accepted oracle-entry boundary and prevents the executor from adding
non-frozen oracle prechecks.

## 13. No target pre-probe

**13.1** Before Oracle-R2 entry, the authorization layer MUST NOT run: `Get-NetTCPConnection`;
`Get-CimInstance` for target binding; `CreateFileW`; `GetFinalPathNameByHandleW`; `Get-FileHash` on the
OpenCode target; `OpenCode --version`; package-target verification; listener/process enumeration; port scan;
HTTP; `/doc`; `/session`.

**13.2** Target binding belongs **only** to Oracle-R2.  Static hashing of the accepted Oracle-R2 artifact
itself is permitted and required (PRE-3, PRE-4, PRE-5).

## 14. Authorization-consumption step

**14.1** After **ALL** PRE-* conditions pass, invoke **exactly once**:

```powershell
Write-DevRelayRecoveryR2OneShotClaim `
  -TempPath            'docs/v0.3/evidence/ETB_RECOVERY_R2_AUTHORIZATION_USE.claim.tmp' `
  -FinalPath           'docs/v0.3/evidence/ETB_RECOVERY_R2_AUTHORIZATION_USE.claim' `
  -SchemaVersion       'devrelay-etb-recovery-r2-authorization-use-v1' `
  -AuthorizationCommit '<recovery_r2_authorization_commit>' `
  -AuthorizationSha256 '<recovery_r2_authorization_sha256>' `
  -OracleR2Commit      'dfb78f34d919e8c9863a8398fb4f63ee301167bc' `
  -OracleR2SpecSha256  '5e9221e3950af6ec3e0612c4d962562c33e761899dfd6af42d10f5a9895f9f2f' `
  -OracleR2ScriptSha256 '22c5fbd61da609e6cc39e973be6030d4c360019ed1f56e69ca45f92fa1689c17'
```

**14.2** The successful TEMP `CreateNew` return is exactly:

```
RECOVERY-R2 AUTHORIZATION USE = 1/1 CONSUMED
```

**14.3** No operation before this point consumes Recovery-R2 authority.

## 15. Post-authorization control boundary

**15.1** After Recovery-R2 authorization is consumed: do **not** mutate config; do **not** republish
`CONFIG_ESTABLISHMENT`; do **not** rerun the PRE-* checklist; do **not** introduce new assertions; do **not**
inspect target state; do **not** inspect Oracle-R2 output paths; do **not** create helper output.

**15.2** The next permitted control action is **only** the Recovery-R2 ETB-attempt claim consumption of §17.

## 16. Authorization-control failure

**16.1** If the authorization TEMP `CreateNew` succeeds but **any** later authorization claim publication
step fails before the ETB-attempt claim consumption point:

```
RECOVERY_R2_AUTHORIZATION_CONTROL_FAILURE
RECOVERY-R2 AUTHORIZATION USE = 1/1 CONSUMED
RECOVERY-R2 ETB ATTEMPT       = 0/1 NOT STARTED
AUTHORITATIVE ETB SEMANTIC RESULT = NONE
STOP
```

**16.2** No retry.  No repair.  No second claim attempt.  A **new independently accepted future
authorization** would be required before another ETB attempt.

**16.3** This control failure is **NOT** `ETB_UNSATISFIED`, **NOT** `HARNESS_INVALID` and **NOT**
`ETB_SATISFIED`.

## 17. ETB attempt consumption

**17.1** **Only after** the Recovery-R2 authorization FINAL claim is successfully published and verified may
the executor invoke **exactly once**:

```powershell
Write-DevRelayRecoveryR2OneShotClaim `
  -TempPath            'docs/v0.3/evidence/ETB_RECOVERY_R2_ATTEMPT_USE.claim.tmp' `
  -FinalPath           'docs/v0.3/evidence/ETB_RECOVERY_R2_ATTEMPT_USE.claim' `
  -SchemaVersion       'devrelay-etb-recovery-r2-attempt-use-v1' `
  -AuthorizationCommit '<recovery_r2_authorization_commit>' `
  -AuthorizationSha256 '<recovery_r2_authorization_sha256>' `
  -OracleR2Commit      'dfb78f34d919e8c9863a8398fb4f63ee301167bc' `
  -OracleR2SpecSha256  '5e9221e3950af6ec3e0612c4d962562c33e761899dfd6af42d10f5a9895f9f2f' `
  -OracleR2ScriptSha256 '22c5fbd61da609e6cc39e973be6030d4c360019ed1f56e69ca45f92fa1689c17'
```

**17.2** The successful TEMP `CreateNew` return is exactly:

```
RECOVERY-R2 ETB ATTEMPT = 1/1 CONSUMED
```

**17.3** This is the **ONE** permitted ETB attempt.

## 18. Post-attempt-claim failure

**18.1** If the attempt TEMP `CreateNew` succeeds but attempt-claim publication later fails:

```
RECOVERY-R2 AUTHORIZATION        = 1/1 CONSUMED
RECOVERY-R2 ETB ATTEMPT          = 1/1 CONSUMED
AUTHORITATIVE ETB SEMANTIC RESULT = NONE
ORACLE-R2                        = NOT ENTERED
STOP
```

**18.2** No retry.  No repair.  No second attempt.

## 19. Oracle entry boundary and exact invocation

**19.1** Oracle-R2 may be entered **ONLY** after **both** the Recovery-R2 authorization FINAL claim **and**
the Recovery-R2 ETB-attempt FINAL claim are successfully published and verified.

**19.2** After attempt-claim completion, invoke **EXACTLY**:

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1"
```

**19.3** With: no parameters; no wrapper; no generated script; no extracted script; no alternate PowerShell
implementation; no environment mutation beyond what the tracked Oracle-R2 itself performs; no
executor-authored assertion; no pre-oracle helper; no post-oracle helper.

**19.4** The tracked accepted script itself **is** the oracle.

## 20. Oracle identity at entry (frozen decision)

**20.1 Decision: the accepted worktree/blob byte-identity check is NOT repeated after authorization
consumption.**

**20.2 Reason:** exact byte identity was already a frozen **PRE-*** condition (PRE-3, PRE-4, PRE-5) evaluated
**before** authority consumption, and no permitted step between the PRE-* checklist and oracle invocation may
modify the script — §15 forbids mutation, assertion injection and helper creation, and §16/§18 provide the
only reachable failure classifications for intervening control steps.

**20.3** This avoids inventing another post-consumption failure surface.  The check is **not** operationally
selectable: it happens exactly once, before consumption.

## 21. Oracle result ownership

**21.1** Once Oracle-R2 is entered, Oracle-R2 **exclusively** owns: the six-path output precondition;
target/listener/process observation; target binding; the listener taxonomy; S0/S1 continuity; the evidence
schema; semantic classification; publication; the result artifact; and the mandatory stop.

**21.2** The authorization layer MUST NOT reinterpret its candidate result.  The allowed Oracle-R2 candidate
result vocabulary remains exactly: `ETB_SATISFIED`; `ETB_UNSATISFIED`; `HARNESS_INVALID / NO ETB SEMANTIC
RESULT`.

**21.3** The operational report may describe the candidate result but MUST NOT promote it to authoritative
status.

## 22. Oracle exit / stop rule

**22.1** After the tracked Oracle-R2 process returns, do **NOT**: rerun Oracle-R2; inspect listener/process
state; run `Get-Command` availability probes; run diagnostics; repair outputs; rewrite evidence/result;
reclassify the result; retry publication; perform HTTP; execute SIC; construct Mode-B; run G0.5/G1/G2.

**22.2** The **only** permitted post-oracle work is: read already-published Oracle-R2 artifacts; hash them;
read claim markers; read git/config static state as explicitly frozen for the operational report; and produce
the execution report.  **No new target observation.**

## 23. Attempt result authority

**23.1** Any Oracle-R2 result from the future operational round is **CANDIDATE ONLY** until independent
ETB-result review.

**23.2** Therefore after operational execution preserve: Mode-B = `BLOCKED / NOT RUN`; `P6 = UNPROVEN /
UNSATISFIED`; G0.5 = **NOT CLOSED**; Case-C = **NOT AUTHORIZED**; v0.3-E implementation = **NOT AUTHORIZED**;
`G1`/`G2` = `NOT RUN`; `adopt_completed_turn` = **DISABLED**.

**23.3** Only an independently accepted `ETB_SATISFIED` may permit Mode-B oracle construction.

## 24. No second attempt

Under this Recovery-R2 authorization: authorization writer invocation max = **1**; attempt writer invocation
max = **1**; Oracle-R2 invocation max = **1**.  No retry.  No "same attempt restart".  No repair-and-rerun.
No alternate target.  No alternate port.  No alternate executable.  No old-Oracle invocation.  No
`Mode P → Mode L` transition.  No fallback.

## 25. Config state

**25.1** Config is **already established**.  Recovery-R2 does **NOT**: mutate config; restore config;
republish `CONFIG_ESTABLISHMENT`; replay the original configuration mutation.  Historical transition
provenance remains original.

| Item | Value |
| --- | --- |
| `CONFIG_SHA256` | `b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf` |
| `CONFIG_SIZE` | `1897` bytes |
| resolved `opencode.base_url` | `http://127.0.0.1:4096` |

## 26. CONFIG_ESTABLISHMENT state

| Item | Value |
| --- | --- |
| path | `docs/v0.3/evidence/etb-execution/CONFIG_ESTABLISHMENT.json` |
| SHA-256 | `ea9fc2bc564cfd6d613e3145703f28d80bb87eb89dcdecaf7ad43b52d7bd9300` |
| status | `VALID / PRESENT` |

**26.1** Do not copy it into the R2 namespace.  Do not rewrite it.  Do not create `CONFIG_ESTABLISHMENT_R2`.

## 27. R1 output preservation

Historical R1 rejected artifacts remain immutable:

| Artifact | SHA-256 |
| --- | --- |
| R1 result `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT.md` | `0a46aa284af30eebad30c689a494a6d73169db1094e07d34b9599913cfe9110e` |
| R1 evidence `docs/v0.3/evidence/etb-execution/ETB_EVIDENCE.json` | `e2c603d73946b01f4e2ca33f7de70441dcc6aacad33b7421b0a066e160bf8b06` |
| R1 manifest `docs/v0.3/evidence/etb-execution/MANIFEST.sha256` | `ebe5214be473fab7afb83b858fb7857be5481424772e98c92770a2b3a817dfc5` |

**27.1** Recovery-R2 must not alter, delete, archive or move them.

## 28. Accepted Oracle-R2 executable preservation

| Item | Value |
| --- | --- |
| Oracle-R2 script path | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1` |
| accepted commit | `dfb78f34d919e8c9863a8398fb4f63ee301167bc` |
| accepted script SHA-256 | `22c5fbd61da609e6cc39e973be6030d4c360019ed1f56e69ca45f92fa1689c17` |
| accepted spec SHA-256 | `5e9221e3950af6ec3e0612c4d962562c33e761899dfd6af42d10f5a9895f9f2f` |

**28.1** The future authorization executes **exactly the tracked worktree path** after the pre-consumption
blob/worktree equality gate (PRE-5) passes.  The accepted Oracle-R2 bytes are frozen and must not be
modified, normalized or substituted.

## 29. Claim tracking policy

**29.1** The four Recovery-R2 claim paths are **untracked operational control-state artifacts**.  They must
not be `git add`ed, staged, committed, deleted, renamed, archived or normalized before independent result
review, and they are **not** part of the tracked-worktree-clean predicate of PRE-7.  The same fail-closed
Git-state policy as the accepted original and Recovery-R1 authorizations applies.

## 30. Authorization artifact self-sufficiency

**30.1** A future executor must be able to perform the Recovery-R2 operational round using **only**: this
accepted authorization artifact; the accepted Oracle-R2 spec/script; the repository state; and the existing
operational artifacts.  **No chat-memory-only step may be required.**

**30.2** Frozen inside this artifact: the claim paths (§5); the claim schemas (§7, §8); the claim writer
(§9); the consumption points and budgets (§10); the preconditions (§11); the oracle-output precheck
prohibition (§12); the target pre-probe prohibition (§13); the failure classifications (§16, §18); the oracle
invocation and entry boundary (§19); the stop rules (§15, §16, §18, §22); the provenance values (§2, §3); and
the budget semantics (§10).

## 31. Mode-B / G0.5 / implementation preservation

Mode-B = `BLOCKED / NOT RUN`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 = **NOT CLOSED**; Case-C = **NOT
AUTHORIZED**; v0.3-E implementation = **NOT AUTHORIZED**; `G1`/`G2` = `NOT RUN`; `adopt_completed_turn` =
**DISABLED**.  **Oracle-R2 acceptance alone does NOT establish target binding, and this authorization does
not run anything.**

## 32. Authoritative sequence

Recovery-R1 rejected → Oracle-R2 accepted/frozen → Oracle-R2 acceptance bookkeeping independently confirmed
→ **Recovery-R2 authorization design (this round)** → independent Recovery-R2 authorization review → if
approved: Recovery-R2 acceptance bookkeeping → independent bookkeeping confirmation → exactly one Recovery-R2
operational ETB attempt → independent ETB-result review → only an independently accepted `ETB_SATISFIED` may
permit Mode-B oracle construction.  **No stage may be skipped.**

## 33. Current status

```
ETB EXECUTION ORACLE-R2            = ACCEPTED / FROZEN / NOT EXECUTED
EXECUTION AUTHORITY                = NOT GRANTED
RECOVERY-R2 AUTHORIZATION          = DESIGN CANDIDATE / NOT ACCEPTED / NOT GRANTED / NOT EXECUTED
RECOVERY-R2 AUTHORIZATION USE      = UNUSED / 0 OF 1
RECOVERY-R2 ETB ATTEMPT            = NOT STARTED / 0 OF 1
RECOVERY-R2 CLAIM NAMESPACE        = DEFINED BY CANDIDATE / NO CLAIM CREATED
AUTHORITATIVE ETB SEMANTIC RESULT  = NONE
```

**33.1** No Recovery-R2 authority is granted today; no claim is created; no config is modified; no probe is
performed; Oracle-R2 is not entered.

## 34. Activity counters (this design round)

web/network `0`; endpoint inspection `0`; `Get-NetTCPConnection` `0`; live `Get-CimInstance` `0`;
listener/process/port enumeration `0`; operational P/Invoke `0`; config mutation `0`; claim creation `0`;
claim deletion `0`; R2 output creation `0`; R2 directory creation `0`; OpenCode start/restart `0`; HTTP `0`;
`/doc` `0`; `/session` `0`; provider/model call `0`; Oracle-R2 execution `0`; old-oracle execution `0`; ETB
execution `0`; SIC `0`; Mode-B work `0`; G0.5 `0`; G1/G2 `0`; R1 artifact mutation `0`;
runtime/test/dependency/version change `0`.

## 35. Executor-choice self-check (frozen, no material choice)

Frozen for a future Recovery-R2 executor: the authorization identity binding; the Oracle-R2 identity binding;
the four claim paths; both claim schemas and their exact field order; the claim serialization (frozen depth,
compressed JSON, one final LF, UTF-8 no BOM); the claim writer source; both consumption points; the `1 of 1`
authorization budget and the `1 of 1` attempt budget; the complete PRE-* checklist; the prohibition on
Oracle-output prechecks; the prohibition on target pre-probes; the post-authorization control boundary; the
attempt consumption step; the post-attempt-claim failure classification; the oracle invocation command and
script path; the no-wrapper rule; the no-repeat identity check after consumption; the oracle result ownership
and candidate-only authority; the post-oracle stop rule; the no-second-attempt rule; and the
authorization-control-failure classification.

**End of Recovery-R2 one-shot ETB execution authorization, design candidate.**
