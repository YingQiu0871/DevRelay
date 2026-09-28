# DevRelay v0.3-E — G0.5-PRE / SIC — Path-D one-shot ETB execution authorization

> **PATH-D ONE-SHOT ETB EXECUTION AUTHORIZATION**
> **DESIGN CANDIDATE**
> **NOT ACCEPTED**
> **NOT FROZEN**
> **NOT EFFECTIVE**
> **NOT EXECUTED**
> **GRANTS NO EXECUTION AUTHORITY TODAY**
> **CREATES NO CLAIM NOW**
> **DOES NOT ENTER ORACLE-PATHD**
> **AUTHORIZED FOR DESIGN ONLY AT THIS STAGE**
> **THIS IS NOT A RETRY**
> **ONE AUTHORIZATION USE + ONE ETB ATTEMPT ONLY IF LATER INDEPENDENTLY ACCEPTED**

Status: **PATH-D AUTHORIZATION = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / NOT EXECUTED**

## 0. Owner decisions (immutable)

```
OWNER DECISION               = PATH D — NEW ETB ATTEMPT
OWNER EXECUTION-SHAPE DECISION = D-EXEC-1 — AUTHORIZE NEW PATH-D EXECUTION ORACLE DESIGN
OWNER NAMING DECISION        = N-C — Oracle-PathD
CANONICAL ID TOKEN           = PATH_D
NEW ETB ATTEMPT              = AUTHORIZED FOR DESIGN ONLY AT THIS STAGE
ETB EXECUTION                = NOT YET AUTHORIZED
THIS IS NOT A RETRY
```

**0.1** The owner selected **PATH D — NEW ETB ATTEMPT** as a **new authorization lineage**. It is **not** a
retry of Recovery-R2, does **not** reuse Recovery-R2 or D1 authorization, is **not** a second D1 execution, and
resets **no** spent budget.

**0.2** `D-EXEC-1` authorized the construction of a new executable oracle variant; that oracle (**Oracle-PathD**)
was independently reviewed, accepted by acceptance bookkeeping, and independently confirmed. `N-C` froze its
identifier.

**0.3** This artifact authorizes **nothing** today: it creates no claim, mutates no configuration, publishes no
evidence, performs no endpoint/listener/process probe, and does not enter Oracle-PathD. It becomes effective
**only** if a separate independent Path-D authorization review accepts it **and** that acceptance bookkeeping is
independently confirmed (§26).

## 1. Purpose and scope

**1.1** This artifact defines an **independently reviewable one-shot Path-D authorization** for exactly **one**
future ETB attempt executed by the **already accepted, frozen and effective** tracked Oracle-PathD executable.

**1.2** It binds permanently to the accepted Oracle-PathD identity triple, uses a **completely new** `PATH_D`
claim namespace, provides exactly **one** authorization-use budget and exactly **one** ETB-attempt budget,
verifies the accepted executable bytes **before** authorization consumption, performs **no** config mutation,
performs **no** target/listener/process probe before the oracle, executes the tracked Oracle-PathD script
**directly** in the future operational round, and permits **no** retry, **no** fallback and **no**
executor-authored assertion or wrapper.

**1.3** Design scope only. This round performs no execution, creates no claim, creates no Path-D output, and
does not create `docs/v0.3/evidence/etb-execution-path-d/`.

## 2. Accepted Oracle-PathD provenance (permanent, immutable)

| Item | Value |
| --- | --- |
| `oracle_path_d_commit` | `3276ef0bb0808ac10b2b82fca68ff282759856fe` |
| `oracle_path_d_spec_sha256` | `15e39452f5efae1f87f03e38fd72ca3336fe3b591affbd93c9104e785fa9884b` |
| `oracle_path_d_script_sha256` | `8bdeb434794c43fe4a199e7338790ba0dbd319728b6766d54299c894a16ac738` |
| Oracle-PathD spec path | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.md` |
| Oracle-PathD script path | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1` |
| Oracle-PathD script byte length | `31328` |
| Oracle-PathD acceptance bookkeeping | `806ade0c51c1a3e2751abe2f0167c1267b2000b0` |
| Oracle-PathD status | `ACCEPTED / FROZEN / EFFECTIVE` |
| Oracle-PathD execution | `NOT AUTHORIZED` |

**2.1** The triple above is the **permanently accepted Oracle-PathD identity**. A later Path-D
acceptance-bookkeeping HEAD, authorization-design HEAD, operational HEAD or result-review HEAD must **not**
replace any of these values.

**2.2** `oracle_path_d_commit` is the independently reviewed **design** commit. The acceptance-bookkeeping commit
of §2 (`806ade0…`) and every later HEAD are **provenance records only** and never substitute for it.

**2.3** `EXECUTION AUTHORITY = NOT GRANTED` until this Path-D authorization is independently accepted **and** its
acceptance bookkeeping is independently confirmed **and** its use budget is consumed exactly as frozen below.

## 3. Provenance distinction — generic historical vs Path-D-specific (frozen)

**3.1** This authorization distinguishes **two different** provenance families that must never be conflated:

| Family | Field names | Meaning | Scope |
| --- | --- | --- | --- |
| **Generic historical ETB evidence fields** | `oracle_commit`, `oracle_sha256` | the **original** frozen oracle identity (`1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc` / `01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921`), preserved byte-identically inside the inherited closed ETB evidence schema | inherited ETB evidence semantics only; **not** a Path-D oracle binding |
| **Path-D authorization provenance fields** | `oracle_path_d_commit`, `oracle_path_d_spec_sha256`, `oracle_path_d_script_sha256` | the accepted **Oracle-PathD** identity triple of §2 | the Path-D authorization and claim layer |

**3.2** The generic fields are part of **inherited ETB evidence semantics** and are **not** modified, renamed or
reinterpreted by this authorization. They do not identify the oracle that produced a Path-D attempt.

**3.3** The Path-D provenance fields bind the **new** Oracle-PathD identity. The future Path-D authorization
claim and attempt claim MUST bind to `oracle_path_d_commit`, `oracle_path_d_spec_sha256` **and**
`oracle_path_d_script_sha256`, and **not** to `oracle_r2_*` or to the generic `oracle_commit` / `oracle_sha256`
pair.

**3.4** This section exists specifically so that the previously recorded non-blocking observation — that the
generic-versus-Path-D provenance distinction was not centralized in one explanatory location — does **not**
propagate into the Path-D lineage. The already accepted Oracle-PathD specification is **not** edited to add this
clarification; the clarification lives here, in the Path-D authorization artifact.

## 4. Predecessor Oracle-R2 provenance (historical only)

| Item | Value |
| --- | --- |
| `oracle_r2_commit` | `dfb78f34d919e8c9863a8398fb4f63ee301167bc` |
| `oracle_r2_spec_sha256` | `5e9221e3950af6ec3e0612c4d962562c33e761899dfd6af42d10f5a9895f9f2f` |
| `oracle_r2_script_sha256` | `22c5fbd61da609e6cc39e973be6030d4c360019ed1f56e69ca45f92fa1689c17` |

**4.1** Oracle-R2 remains **historical predecessor authority only**. This Path-D authorization binds to
**Oracle-PathD**, not directly to Oracle-R2, and never re-invokes Oracle-R2.

**4.2** Oracle-R2 and its outputs are **not** modified, renamed, normalized, moved or deleted by this round or by
any future Path-D execution.

## 5. Path-D authorization identity model

**5.1** If this candidate is later independently accepted and its acceptance bookkeeping independently
confirmed:

```
path_d_authorization_commit = <future independently accepted authorization-design commit>
path_d_authorization_sha256 = <committed-blob SHA-256 of
                               docs/v0.3/V03E_G0_5_PRE_ETB_PATH_D_AUTHORIZATION.md>
```

**5.2** Both values are **UNKNOWN** until this design candidate is committed and independently approved. They are
populated **only** by the later independent approval record; they are **not** executor choices.

**5.3** `path_d_authorization_commit` is the independently accepted **authorization-design** commit — **not** the
later acceptance-bookkeeping commit and **not** any operational HEAD. The bookkeeping HEAD never substitutes for
authorization provenance.

**5.4 Authorization lifecycle state model (frozen).** During this design candidate:

```
PATH-D AUTHORIZATION  = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / NOT EXECUTED
EXECUTION AUTHORITY   = NOT GRANTED
PATH-D AUTHORIZATION USE = 0 OF 1 / NOT CONSUMED
PATH-D ETB ATTEMPT       = 0 OF 1 / NOT STARTED
```

After a future independently approved acceptance-bookkeeping round **and** its independent confirmation:

```
PATH-D AUTHORIZATION  = ACCEPTED / FROZEN / EFFECTIVE
EXECUTION AUTHORITY   = GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY
PATH-D AUTHORIZATION USE = UNUSED / 0 OF 1
PATH-D ETB ATTEMPT       = NOT STARTED / 0 OF 1
```

Authorization use remains `UNUSED / 0 OF 1` until the authorization TEMP `CreateNew` succeeds, and the ETB
attempt remains `NOT STARTED / 0 OF 1` until the attempt TEMP `CreateNew` succeeds. **Independent bookkeeping
confirmation is required before any operational consumption**, and authority is **not** marked granted in this
design round.

## 6. Historical authorization state (permanent record; not reusable)

**6.1** Original Round-5 authorization: `ORIGINAL AUTHORIZATION = SPENT / NOT REUSABLE`;
`ORIGINAL ETB ATTEMPT = 0/1 HISTORICAL ATTEMPT NEVER STARTED (NOT REUSABLE: parent authorization is spent)`.

**6.2** Recovery-R1: `RECOVERY-R1 AUTHORIZATION = SPENT / NOT REUSABLE`;
`RECOVERY-R1 ETB ATTEMPT = SPENT / NOT REUSABLE`.

**6.3** Recovery-R2: `RECOVERY-R2 AUTHORIZATION = SPENT / NOT REUSABLE`;
`RECOVERY-R2 ETB ATTEMPT = SPENT / NOT REUSABLE`.

**6.4** D1 diagnostic lineage: `D1 AUTHORIZATION = SPENT / 1 OF 1 / IRREVERSIBLE / NOT REUSABLE`;
`D1 DIAGNOSTIC ATTEMPT = SPENT / 1 OF 1 / IRREVERSIBLE / NOT REUSABLE`;
`D1 LISTENER QUERY = EXECUTED ONCE / NO RETRY`.

**6.5** **None** of these historical markers may be modified, deleted, renamed, archived, committed,
normalized, reused by path, or treated as UNUSED. They are permanent control-state witnesses. This Path-D
authorization resets **no** historical budget and reopens **no** historical claim.

## 7. New Path-D claim namespace (permanently distinct)

Freeze **exactly** these four paths:

| Marker | Temp path | Final path |
| --- | --- | --- |
| Path-D authorization claim | `docs/v0.3/evidence/ETB_PATH_D_AUTHORIZATION_USE.claim.tmp` | `docs/v0.3/evidence/ETB_PATH_D_AUTHORIZATION_USE.claim` |
| Path-D ETB attempt claim | `docs/v0.3/evidence/ETB_PATH_D_ATTEMPT_USE.claim.tmp` | `docs/v0.3/evidence/ETB_PATH_D_ATTEMPT_USE.claim` |

**7.1** These paths are permanently distinct from the original Round-5 claim namespace
(`ETB_AUTHORIZATION_USE.claim`, `ETB_ATTEMPT_USE.claim`), from the Recovery-R1 namespace
(`ETB_RECOVERY_R1_*`), from the Recovery-R2 namespace (`ETB_RECOVERY_R2_*`), from the D1 namespace
(`ETB_QUERY_DIAGNOSTIC_D1_*`) and from **all** oracle output namespaces. **No historical claim path may be
reused.**

**7.2** The parent directory is the accepted claim-control location `docs/v0.3/evidence/`, recovered from the
existing claim precedent. No other claim path may be created under this authorization.

## 8. Claim-path occupancy predicate (frozen)

```
CLAIM_PATH_OCCUPIED(path) := [System.IO.File]::Exists(path) -or [System.IO.Directory]::Exists(path)
ABSENT                    := File.Exists(path) == false AND Directory.Exists(path) == false
```

**8.1** A file, a **directory**, a partial file, a malformed file or a zero-length file at one of these exact
paths counts as **OCCUPIED** and fails closed.

**8.2** No deletion. No cleanup. No overwrite. No rename of historical claim markers.

**8.3 Design-stage occupancy (verified).** All four Path-D claim paths, the six Oracle-PathD runtime output
paths and the `docs/v0.3/evidence/etb-execution-path-d` directory are **ABSENT** at design time:

```
PATH-D RUNTIME OCCUPANCY = 0 / 11
```

## 9. Authorization claim schema (new, exact, closed)

```
schema_version = devrelay-etb-path-d-authorization-use-v1
```

Exact ordered fields (7):

| # | Field |
| --- | --- |
| 1 | `schema_version` |
| 2 | `authorization_commit` |
| 3 | `authorization_sha256` |
| 4 | `oracle_path_d_commit` |
| 5 | `oracle_path_d_spec_sha256` |
| 6 | `oracle_path_d_script_sha256` |
| 7 | `state` |

Exact value: `state = CONSUMED`. No timestamp, no hostname, no PID, no operator, no comment, **no extra field**.
Encoding: UTF-8, **no BOM**, exactly one final LF.

## 10. Attempt claim schema (new, exact, closed)

```
schema_version = devrelay-etb-path-d-attempt-use-v1
```

Exact ordered fields are **the same seven** as §9, with `state = CONSUMED`. No extra field. Encoding: UTF-8,
**no BOM**, exactly one final LF.

**10.1** The authorization-use claim and the attempt-use claim are **distinct markers with distinct schema
versions** and must never be merged, aliased or substituted for one another.

## 11. Exact frozen claim writer source

**11.1** The future executor MUST use the following function **verbatim**. It must **not** be rewritten,
translated, replaced by an equivalent writer, or supplemented. No Python, no `Set-Content`, no `Out-File`, no
alternate serializer.

**11.2** Frozen serialization depth: `ConvertTo-Json -Depth 4 -Compress` (sufficient for the flat 7-field
object; this exact value is frozen).

**11.3** If `TEMP` `CreateNew` succeeds, the corresponding one-shot budget is **consumed** even if a later write,
flush, read-back or move step fails. **No deletion on failure** — the consumed marker remains as evidence.

**11.4** The writer performs exclusive creation, byte-identical read-back verification, UTF-8/no-BOM/LF framing
with exactly one terminal LF, and a two-argument `System.IO.File.Move` publication (no overwrite), after which
the final marker is immutable.

```powershell
function Write-DevRelayPathDOneShotClaim {
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
        [string] $OraclePathDCommit,

        [Parameter(Mandatory = $true)]
        [string] $OraclePathDSpecSha256,

        [Parameter(Mandatory = $true)]
        [string] $OraclePathDScriptSha256
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
        schema_version          = $SchemaVersion
        authorization_commit    = $AuthorizationCommit
        authorization_sha256    = $AuthorizationSha256
        oracle_path_d_commit    = $OraclePathDCommit
        oracle_path_d_spec_sha256   = $OraclePathDSpecSha256
        oracle_path_d_script_sha256 = $OraclePathDScriptSha256
        state                   = 'CONSUMED'
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

    if ($tempBytes[$tempBytes.Length - 1] -ne 10) {
        throw "DEVRELAY_CLAIM_TEMP_NO_FINAL_LF"
    }

    if (($tempBytes[0] -eq 0xEF) -and ($tempBytes[1] -eq 0xBB) -and ($tempBytes[2] -eq 0xBF)) {
        throw "DEVRELAY_CLAIM_TEMP_BOM"
    }

    [System.IO.File]::Move($TempPath, $FinalPath)

    $finalBytes = [System.IO.File]::ReadAllBytes($FinalPath)

    if ($finalBytes.Length -ne $bytes.Length) {
        throw "DEVRELAY_CLAIM_FINAL_LENGTH_MISMATCH"
    }

    for ($i = 0; $i -lt $bytes.Length; $i++) {
        if ($finalBytes[$i] -ne $bytes[$i]) {
            throw "DEVRELAY_CLAIM_FINAL_BYTE_MISMATCH"
        }
    }
}
```

## 12. Consumption points and budgets

| State variable | Budget |
| --- | --- |
| `PATH_D_AUTHORIZATION_USE_BUDGET` | **1 of 1** |
| `PATH_D_ETB_ATTEMPT_BUDGET` | **1 of 1** |

**12.1** The **authorization** budget is consumed at the successful `CreateNew` of
`docs/v0.3/evidence/ETB_PATH_D_AUTHORIZATION_USE.claim.tmp`.

**12.2** The **ETB attempt** budget is consumed at the successful `CreateNew` of
`docs/v0.3/evidence/ETB_PATH_D_ATTEMPT_USE.claim.tmp`.

**12.3** Consumed means **permanently consumed**. No independent review may reopen a consumed marker. A later
publication failure MUST NOT reopen a consumed budget.

**12.4** These budgets apply **only** to the new Path-D lineage. They do **not** reset, reopen or reinterpret
any historical budget (§6).

## 13. Pre-consumption preconditions (ALL before Path-D authorization consumption)

No additional precondition may be invented operationally. Every check is **read-only**.

| ID | Required condition |
| --- | --- |
| **PRE-1** | current branch is `v0.3-e-recovery-reconciliation` |
| **PRE-2** | this Path-D authorization artifact matches its independently accepted future `path_d_authorization_commit` and `path_d_authorization_sha256` |
| **PRE-3** | Oracle-PathD is `ACCEPTED / FROZEN / EFFECTIVE`, i.e. its acceptance bookkeeping `806ade0c51c1a3e2751abe2f0167c1267b2000b0` has been independently confirmed |
| **PRE-4** | the tracked blob at `oracle_path_d_commit` for `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1` hashes exactly `oracle_path_d_script_sha256` |
| **PRE-5** | the tracked blob at `oracle_path_d_commit` for `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.md` hashes exactly `oracle_path_d_spec_sha256` |
| **PRE-6** | the **current worktree** Oracle-PathD script bytes are **byte-identical** to that committed blob (no normalized-equivalent acceptance) |
| **PRE-7** | a read-only git attribute check resolves the normative Oracle-PathD executable to `text: set` and `eol: lf` |
| **PRE-8** | the tracked worktree contains **no** tracked modification and **no** staged path |
| **PRE-9** | `.devrelay/config.yaml` is present with `SHA-256 = b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf`, `size = 1897`, and production-resolved `opencode.base_url = http://127.0.0.1:4096`, read **only** through the frozen Oracle-PathD config-reader invocation shape |
| **PRE-10** | `CONFIG_ESTABLISHMENT` is present exactly at `docs/v0.3/evidence/etb-execution/CONFIG_ESTABLISHMENT.json` with `SHA-256 = ea9fc2bc564cfd6d613e3145703f28d80bb87eb89dcdecaf7ad43b52d7bd9300` (accepted semantic status remains `VALID / PRESENT`) |
| **PRE-11** | all historical claim markers, evidence, manifests and results still exist with their accepted SHA-256 values, and none has been modified, deleted, renamed or archived |
| **PRE-12** | **all four** Path-D claim paths of §7 are **ABSENT** under the §8 occupancy predicate |
| **PRE-13** | **all six** Oracle-PathD output paths and the `docs/v0.3/evidence/etb-execution-path-d` directory are **ABSENT**, i.e. `PATH-D RUNTIME OCCUPANCY = 0 / 11` |
| **PRE-14** | **no** Path-D authorization claim has yet been consumed |
| **PRE-15** | **no** Path-D ETB attempt claim has yet been consumed |

**13.1** PRE-14 and PRE-15 are the consumed-state confirmations: because a consumption point is the successful
`CreateNew` of the corresponding TEMP path, either TEMP or FINAL occupancy at those exact paths means the budget
is already consumed. They are therefore physically entailed by the PRE-12 ABSENT result; no separate probe
beyond the §8 predicate is permitted.

**13.2** Failure of **any** PRE-* condition → **STOP BEFORE CONSUMING ANYTHING**. No repair. No retry. No
fallback. No claim is created, no config is touched, no oracle is entered.

**13.3 Pre-consumption prerequisites versus runtime semantic checks (frozen distinction).** The PRE-* set above
covers only authorization-layer, file-system, provenance and static-availability conditions. The **runtime
semantic checks** — listener query and its classification order, config value comparison, `OwningProcess`/PID
resolution, `Win32_Process` lookup, `ExecutablePath`/`CreationDate` process-instance identity, binary SHA-256
validation, `package.json` identity validation, S0/S1 continuity and every result classification — belong
**exclusively** to the accepted Oracle-PathD executable and are **not** duplicated into this authorization
layer.

## 14. No target pre-probe

**14.1** Before Oracle-PathD entry, the authorization layer MUST NOT run: `Get-NetTCPConnection`; `Get-CimInstance`
for target binding; `CreateFileW`; `GetFinalPathNameByHandleW`; `Get-FileHash` on the OpenCode target;
`OpenCode --version`; package-target verification; listener/process enumeration; port scan; HTTP; `/doc`;
`/session`.

**14.2** Target binding belongs **only** to Oracle-PathD. Static hashing of the accepted Oracle-PathD artifact
itself is permitted and required (PRE-4, PRE-5, PRE-6).

## 15. Authorization-consumption step

**15.1** After **ALL** PRE-* conditions pass, invoke **exactly once**:

```powershell
Write-DevRelayPathDOneShotClaim `
  -TempPath             'docs/v0.3/evidence/ETB_PATH_D_AUTHORIZATION_USE.claim.tmp' `
  -FinalPath            'docs/v0.3/evidence/ETB_PATH_D_AUTHORIZATION_USE.claim' `
  -SchemaVersion        'devrelay-etb-path-d-authorization-use-v1' `
  -AuthorizationCommit  '<path_d_authorization_commit>' `
  -AuthorizationSha256  '<path_d_authorization_sha256>' `
  -OraclePathDCommit    '3276ef0bb0808ac10b2b82fca68ff282759856fe' `
  -OraclePathDSpecSha256   '15e39452f5efae1f87f03e38fd72ca3336fe3b591affbd93c9104e785fa9884b' `
  -OraclePathDScriptSha256 '8bdeb434794c43fe4a199e7338790ba0dbd319728b6766d54299c894a16ac738'
```

**15.2** The successful TEMP `CreateNew` return is exactly:

```
PATH-D AUTHORIZATION USE = 1/1 CONSUMED
```

**15.3** No operation before this point consumes Path-D authority.

## 16. Post-authorization control boundary

**16.1** After Path-D authorization is consumed: do **not** mutate config; do **not** republish
`CONFIG_ESTABLISHMENT`; do **not** rerun the PRE-* checklist; do **not** introduce new assertions; do **not**
inspect target state; do **not** inspect Oracle-PathD output paths; do **not** create helper output.

**16.2** The next permitted control action is **only** the Path-D ETB-attempt claim consumption of §18.

## 17. Authorization-control failure

**17.1** If the authorization TEMP `CreateNew` succeeds but **any** later authorization claim publication step
fails before the ETB-attempt claim consumption point:

```
PATH_D_AUTHORIZATION_CONTROL_FAILURE
PATH-D AUTHORIZATION USE = 1/1 CONSUMED
PATH-D ETB ATTEMPT       = 0/1 NOT STARTED
AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED
STOP
```

**17.2** No retry. No repair. No second claim attempt. A **new independently accepted future authorization**
would be required before another ETB attempt.

**17.3** This control failure is **NOT** `ETB_UNSATISFIED`, **NOT** `HARNESS_INVALID` and **NOT**
`ETB_SATISFIED`, and it does **not** alter the authoritative ETB semantic result.

## 18. ETB attempt consumption

**18.1** **Only after** the Path-D authorization FINAL claim is successfully published and verified may the
executor invoke **exactly once**:

```powershell
Write-DevRelayPathDOneShotClaim `
  -TempPath             'docs/v0.3/evidence/ETB_PATH_D_ATTEMPT_USE.claim.tmp' `
  -FinalPath            'docs/v0.3/evidence/ETB_PATH_D_ATTEMPT_USE.claim' `
  -SchemaVersion        'devrelay-etb-path-d-attempt-use-v1' `
  -AuthorizationCommit  '<path_d_authorization_commit>' `
  -AuthorizationSha256  '<path_d_authorization_sha256>' `
  -OraclePathDCommit    '3276ef0bb0808ac10b2b82fca68ff282759856fe' `
  -OraclePathDSpecSha256   '15e39452f5efae1f87f03e38fd72ca3336fe3b591affbd93c9104e785fa9884b' `
  -OraclePathDScriptSha256 '8bdeb434794c43fe4a199e7338790ba0dbd319728b6766d54299c894a16ac738'
```

**18.2** The successful TEMP `CreateNew` return is exactly:

```
PATH-D ETB ATTEMPT = 1/1 CONSUMED
```

**18.3** This is the **ONE** permitted ETB attempt.

## 19. Post-attempt-claim failure

**19.1** If the attempt TEMP `CreateNew` succeeds but attempt-claim publication later fails:

```
PATH-D AUTHORIZATION           = 1/1 CONSUMED
PATH-D ETB ATTEMPT             = 1/1 CONSUMED
AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED
ORACLE-PATHD                   = NOT ENTERED
STOP
```

**19.2** No retry. No repair. No second attempt.

## 20. Oracle entry boundary and exact invocation

**20.1** Oracle-PathD may be entered **ONLY** after **both** the Path-D authorization FINAL claim **and** the
Path-D ETB-attempt FINAL claim are successfully published and verified.

**20.2** After attempt-claim completion, invoke **EXACTLY** (run from the repository root):

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1"
```

**20.3** With: no parameters; no wrapper; no generated script; no extracted script; no patched script; no
alternate PowerShell implementation; no environment mutation beyond what the tracked Oracle-PathD itself
performs; no executor-authored assertion; no pre-oracle helper; no post-oracle helper.

**20.4** The tracked accepted script itself **is** the oracle.

**20.5 Execution shape (bound; not redesigned by this authorization).** The authorization binds **exactly** to
accepted Oracle-PathD and freezes:

* `MODE = P / PRE-EXISTING TARGET`;
* `configured_base_url = http://127.0.0.1:4096`;
* listener predicate `LocalAddress = 127.0.0.1`, `LocalPort = 4096`, `State = Listen`;
* **no** endpoint discovery, **no** fallback, **no** alternate port, **no** `localhost` alias, **no** IPv6
  alternate, **no** OpenCode start/restart, **no** HTTP, **no** `/doc`, **no** provider/model invocation.

**20.6 Target identity (bound; preserved).** `C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe`;
binary SHA-256 `578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35`; package `opencode-ai`; version
`1.18.11`; bin identity `bin.opencode`; `OwningProcess` → PID → `Win32_Process` → `ExecutablePath` →
`CreationDate` with process-instance identity by PID **and** `CreationDate.Ticks`; `CreateFileW` /
`GetFinalPathNameByHandleW` canonicalization; dual hash validation; `package.json` validation; S0/S1 continuity.

## 21. Result authority (observation versus authoritative semantic result)

**21.1** Execution observation and authoritative semantic result are **distinct**. A future Oracle-PathD
execution may publish one of the accepted Oracle result classes into its own output namespace; that publication
is an **execution observation**, not a new authoritative ETB semantic result.

**21.2** The published observation becomes the new authoritative ETB semantic result **only** after the
established sequence:

```
independent result review
→
result bookkeeping
→
bookkeeping confirmation
```

**21.3** Until that sequence completes:

```
AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED
```

**21.4** A raw generated result file MUST NOT silently replace the authoritative ETB semantic result. No
executor, no authorization layer and no bookkeeping round may promote a raw output file to authoritative status.

## 22. Result classes (exactly the accepted Oracle-PathD model)

`ETB_SATISFIED`; `ETB_UNSATISFIED`; `HARNESS_INVALID / NO ETB SEMANTIC RESULT`.

**22.1** No additional semantic class is introduced. No `PASS`, `FAIL`, `PARTIAL`, `UNKNOWN`, `PROBABLE` or
`RETRY`. **No result is preselected** by this authorization.

## 23. Artifact model, MODEL A and operational inventory terminology

**23.1** MODEL A is preserved. Future generated Path-D runtime artifacts remain **operational / untracked** and
**byte-immutable** according to accepted DevRelay precedent. Tracked governance state advances **only** through
the established status surfaces (`CHANGELOG.md`, `docs/v0.3/V03E_ACCEPTANCE.md`).

**23.2** Future output namespace: `docs/v0.3/evidence/etb-execution-path-d/` with the six exact paths
`ETB_EVIDENCE.json{,.tmp}`, `MANIFEST.sha256{,.tmp}` and
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_D.md{,.tmp}`. Future claims:
`docs/v0.3/evidence/ETB_PATH_D_AUTHORIZATION_USE.claim` and
`docs/v0.3/evidence/ETB_PATH_D_ATTEMPT_USE.claim` (with `.tmp` forms).

**23.3** **None** of these is generated in this round.

**23.4 Operational inventory terminology (precise; frozen for future use).** When describing the current
MODEL A operational material, both counting models MUST be stated explicitly and the inaccurate phrase
"thirteen historical artifacts" MUST NOT be used:

```
git status --porcelain collapsed entries = 13
expanded untracked files                 = 17
expanded composition                     = 12 historical operational files
                                         +  5 accepted D1 operational files
```

The two models count the same material under different directory-folding conventions; neither is a substitute
for the other, and the composition split is the authoritative description of what those entries are.

## 24. Historical immutability

**24.1** This round does **not** modify, move, archive, normalize or delete: the Oracle-PathD spec or executable;
Oracle-R2 artifacts; Recovery-R1 artifacts; Recovery-R2 artifacts; D1 artifacts; original ETB artifacts;
historical claims; historical evidence; historical manifests; historical results; or any construction-time
banner.

**24.2** This authorization references those materials **only** by frozen provenance.

**24.3** Config remains the exact accepted post-image (§13 PRE-9); this authorization does not mutate config and
does not republish `CONFIG_ESTABLISHMENT`.

**24.4** Preserved downstream state: `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED`; Recovery-R2
authorization / attempt = `SPENT / NOT REUSABLE`; `D1 = ACCEPTED / FROZEN / AUTHORITATIVE DIAGNOSTIC RESULT`;
`D1 AUTHORIZATION / ATTEMPT = SPENT / NOT REUSABLE`; `D1 LISTENER QUERY = EXECUTED ONCE`; Mode-B =
`BLOCKED / NOT RUN`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 = `NOT CLOSED`; G0.5 execution / Case-C / v0.3-E
implementation **NOT AUTHORIZED**; `G1`/`G2` **NOT RUN**; `adopt_completed_turn` **DISABLED**; **PATH C = NO
STATIC BASIS / NOT AUTHORIZED**.

## 25. Self-sufficiency

**25.1** A future executor must be able to perform the Path-D operational round using **only**: this
authorization artifact, the accepted Oracle-PathD specification and executable, and the accepted historical
control-state markers. No behavior depends on chat instructions, executor memory, temporary generated code or
untracked helper scripts.

**25.2** The complete operational sequence is: static verification → PRE-* gate sequence → authorization
consumption → post-authorization boundary → attempt consumption → Oracle-PathD entry → oracle-owned control and
result state → STOP → independent result review. **No stage may be skipped.**

## 26. Authoritative sequence and effectivity model

**26.1** The frozen lifecycle is:

```
Owner Path-D decision
→ Oracle-PathD design → third-party independent design review → acceptance bookkeeping → independent bookkeeping confirmation
→ Oracle-PathD ACCEPTED / FROZEN / EFFECTIVE
→ Path-D authorization design candidate [THIS ROUND]
→ independent authorization design review
→ authorization acceptance bookkeeping
→ independent bookkeeping confirmation
→ Path-D authorization ACCEPTED / FROZEN / EFFECTIVE
→ ONE authorization-use consumption
→ ONE attempt consumption
→ ONE Oracle-PathD execution
→ independent result review
→ result bookkeeping / confirmation
→ owner reconciliation (which may then establish a new authoritative ETB semantic result)
```

**26.2** No stage may be skipped. **This candidate does not grant execution effectivity**, and it does not
collapse authorization-design acceptance with acceptance-bookkeeping confirmation.

**26.3** The already completed Oracle-PathD stages are recorded exactly: design candidate `3276ef0…`; third-party
independent design review APPROVED with `P0 = 0, P1 = 0, P2 = 0, P3 = 3`; acceptance bookkeeping `806ade0…`;
independent bookkeeping confirmation issued; therefore **`ORACLE-PATHD = ACCEPTED / FROZEN / EFFECTIVE`**.

## 27. Current status

```
ORACLE-PATHD                    = ACCEPTED / FROZEN / EFFECTIVE
ORACLE-PATHD EXECUTION          = NOT AUTHORIZED
PATH-D AUTHORIZATION            = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE
PATH-D AUTHORIZATION USE        = 0 OF 1 / NOT CONSUMED
PATH-D ETB ATTEMPT              = 0 OF 1 / NOT STARTED
PATH-D ETB EXECUTION            = NOT AUTHORIZED
PATH-D CLAIMS                   = NOT CREATED
PATH-D RUNTIME OUTPUTS          = NOT CREATED
PATH-D RUNTIME OCCUPANCY        = 0 / 11
AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED
```

## 28. Fail-closed / no-retry contract

**28.1** The future Path-D attempt remains **one-shot**. Frozen permanently:

```
NO RETRY
NO FALLBACK
NO AUTOMATIC CLEANUP
NO CLAIM DELETION
NO CLAIM REUSE
NO OUTPUT OVERWRITE
NO HISTORICAL ARTIFACT MUTATION
NO BUDGET RESET
```

**28.2** If execution proceeds far enough to consume the attempt and later fails, the attempt remains **SPENT**
according to accepted precedent. No review may reopen a consumed claim.

## 29. Activity counters (this design round)

**29.1** This design round performed: oracle executions `0`; ETB executions `0`; listener queries `0`;
`Get-NetTCPConnection` calls `0`; claim creations `0`; evidence/manifest/result creations `0`; output-directory
creations `0`; budget consumptions `0`; config mutations `0`; endpoint-state modifications `0`; OpenCode
starts/restarts `0`; HTTP `0`; `/doc` `0`; provider/model calls `0`; SIC `0`; Mode-B `0`; G0.5/G1/G2 `0`;
runtime/test/dependency/version changes `0`; historical-artifact mutations `0`; historical-claim reuses `0`.

**29.2** This candidate does **not** claim: Path-D authorization accepted; Path-D authorization effective;
Path-D executed; any claim created; any budget consumed; any result selected; `ETB_SATISFIED`; a replacement
`ETB_UNSATISFIED`; P6 PASS/FAIL; G0.5 PASS/FAIL; Mode-B authorized; Oracle-R2 defective; Oracle-PathD executed.

**29.3 Non-claims preserved:** `NOT SIC`; `NOT P6`; `NOT G0.5`; `NOT MODE-B RESULT`; `NOT CASE-C AUTHORIZATION`;
`NOT ADOPTION AUTHORIZATION`.

**End of Path-D one-shot ETB execution authorization, design candidate.**
