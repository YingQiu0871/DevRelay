# DevRelay v0.3-E — G0.5-PRE / SIC — ETB control-state recovery authorization (Recovery-R1)

> **ETB CONTROL-STATE RECOVERY AUTHORIZATION**
> **RECOVERY-R1 CANDIDATE**
> **NOT ACCEPTED**
> **NOT EFFECTIVE**
> **NOT EXECUTED**
> **DOES NOT PERFORM RECOVERY**
> **DOES NOT MUTATE CONFIGURATION**
> **DOES NOT CREATE CLAIMS NOW**
> **DOES NOT ENTER THE ORACLE NOW**
> **ONE RECOVERY USE + ONE ETB ATTEMPT ONLY IF LATER INDEPENDENTLY ACCEPTED**

Status: **ETB CONTROL-STATE RECOVERY AUTHORIZATION = RECOVERY-R1 CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT EXECUTED**

Baseline: `14c5343ef4e9d00de132f30eec8597f9071cd770` (branch `v0.3-e-recovery-reconciliation`).  The one-shot
operational round created **no commit**, so this HEAD remains the accepted authorization-bookkeeping
baseline while the operational filesystem state is intentionally **not** the original pre-operation state.

This artifact is a **new authorization artifact** — it is **not** a revision of
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_AUTHORIZATION.md`, which is immutable and must not be modified.  It
authorizes nothing today: it performs no recovery, mutates no configuration, creates no claim, publishes no
evidence and does not enter the oracle.  It becomes effective **only** if a separate independent
recovery-authorization review accepts it.

Accepted frozen oracle provenance (immutable; unchanged by recovery — **recovery does not create a new
oracle**):

| Item | Value |
| --- | --- |
| `oracle_commit` | `1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc` |
| `oracle_sha256` | `01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921` |
| `oracle_artifact` | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md` |

## 1. Spent original authorization (permanent record)

| Item | Value |
| --- | --- |
| original `authorization_commit` | `64044fc45082cd63b0ae445c146d85720dfa1435` |
| original `authorization_sha256` | `511ab1e2eb2e4f1194d2c55951e5b9616dc515d1180c6399dd658207d443d0d8` |
| original authorization claim | `docs/v0.3/evidence/ETB_AUTHORIZATION_USE.claim` |
| original claim SHA-256 (witness) | `d84b428586f07a55a99f5b1391481d77763ec4ea697a40d1cec8aa0779613d4e` |

```
ORIGINAL AUTHORIZATION = SPENT / NOT REUSABLE
```

**1.1** The original claim is the **permanent spent-authorization witness**.  It must **not** be deleted,
renamed, archived, committed, reused by path, treated as UNUSED, or invoked again; the original
authorization must never be used again.

## 2. Original ETB attempt

**2.1** The original operational round never created `docs/v0.3/evidence/ETB_ATTEMPT_USE.claim.tmp` or
`docs/v0.3/evidence/ETB_ATTEMPT_USE.claim`:

```
ORIGINAL ETB ATTEMPT = 0/1 NOT STARTED
```

**2.2** This does **not** permit continuation under the original authorization — that authorization is
spent.  The Recovery-R1 attempt authorized here is a **new** attempt under a **new** authorization.

## 3. Current config recovery baseline (exact)

| Item | Value |
| --- | --- |
| `CURRENT_CONFIG_SHA256` | `b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf` |
| `CURRENT_CONFIG_SIZE` | `1897` bytes |
| production-resolved `opencode.base_url` | `http://127.0.0.1:4096` |

**3.1** This is the **exact accepted frozen post-image**.  Historical pre-mutation constants remain
`PRE_CONFIG_SHA256 = daaf72578cb4a91b5adeb481530baf47577174325167caddf7249964da7923a8`,
`PRE_CONFIG_SIZE = 1876`, historical pre-resolved `base_url = ""` — **historical verified pre-mutation
values only; they are NOT the current config state.**

## 4. No config mutation in recovery

```
RECOVERY CONFIG MUTATION = FORBIDDEN
```

**4.1** Recovery must **not** restore `""`, must **not** apply `OLD_CONFIG_SPAN` or `NEW_CONFIG_SPAN`, must
**not** run the original Python config-mutation writer, must **not** create `config.yaml.etb-auth.tmp`,
must **not** run `os.replace` on the config, and must **not** perform any YAML, regex or other rewrite of
the config in any form.

**4.2** The only permitted config operations in recovery are **read-only verification** of the current
SHA-256, the current size and the production-resolved `base_url`, expecting exactly
`b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf` / `1897` /
`http://127.0.0.1:4096`.  **Mismatch → `RECOVERY_AUTHORIZATION_CONTROL_FAILURE` / STOP; no repair.**

## 5. Recovery authorization identity model

**5.1** If this Recovery-R1 candidate is later independently accepted:
`recovery_authorization_commit` = the immutable accepted commit containing **this** recovery authorization
artifact, and `recovery_authorization_sha256` = the committed SHA-256 of **this** artifact.

**5.2** A later bookkeeping commit, an operational execution commit, an evidence commit, a result-review
commit or the execution-time HEAD must **not** replace that pair.  The eventual independent approval record
binds the exact pair, which future recovery execution must use.

## 6. Frozen oracle remains unchanged

**6.1** `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md` must not be modified.  Recovery creates **no** new
ETB oracle.  If recovery later reaches ETB execution, it enters **this exact accepted oracle from its FIRST
STEP**.

## 7. New Recovery-R1 claim namespace (permanently distinct)

| Marker | Final path | Temp path |
| --- | --- | --- |
| recovery authorization claim | `docs/v0.3/evidence/ETB_RECOVERY_R1_AUTHORIZATION_USE.claim` | `docs/v0.3/evidence/ETB_RECOVERY_R1_AUTHORIZATION_USE.claim.tmp` |
| recovery ETB attempt claim | `docs/v0.3/evidence/ETB_RECOVERY_R1_ATTEMPT_USE.claim` | `docs/v0.3/evidence/ETB_RECOVERY_R1_ATTEMPT_USE.claim.tmp` |

**7.1** These paths are permanently distinct from `ETB_AUTHORIZATION_USE.claim` and
`ETB_ATTEMPT_USE.claim`; no original claim path may be reused.  A later Recovery-R2, if ever required, must
define another distinct namespace.

## 8. Claim-path occupancy predicate (frozen)

```
CLAIM_PATH_OCCUPIED(path) := [System.IO.File]::Exists(path) -or [System.IO.Directory]::Exists(path)
ABSENT                    := File.Exists(path) == false AND Directory.Exists(path) == false
```

**8.1** This predicate applies to all four **new** Recovery-R1 claim paths.  A file, a directory, a partial
file, a malformed file or a zero-length file at one of these exact paths counts as **OCCUPIED** and fails
closed.

## 9. Exact claim-writer reuse

**9.1** Recovery must use the **exact accepted** `Write-DevRelayOneShotClaim` PowerShell/.NET function from
the immutable original authorization artifact (`authorization_commit = 64044fc…`, artifact SHA-256 =
`511ab1e2eb2e4f1194d2c55951e5b9616dc515d1180c6399dd658207d443d0d8`).  It must **not** be rewritten,
translated, or replaced by an equivalent writer.

**9.2** For repository self-sufficiency the function is reproduced below as a **byte-for-byte verbatim
copy**, and it is **normatively identical** to the accepted original function.  **A future independent
reviewer must diff the two functions; no executable deviation is allowed.**

```powershell
function Write-DevRelayOneShotClaim {
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
        [string] $OracleCommit,

        [Parameter(Mandatory = $true)]
        [string] $OracleSha256
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
        schema_version     = $SchemaVersion
        authorization_commit = $AuthorizationCommit
        authorization_sha256 = $AuthorizationSha256
        oracle_commit      = $OracleCommit
        oracle_sha256      = $OracleSha256
        state              = 'CONSUMED'
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
}
```

## 10. Recovery claim schema

`schema_version = devrelay-etb-authorization-use-v1`; ordered fields exactly `schema_version`,
`authorization_commit`, `authorization_sha256`, `oracle_commit`, `oracle_sha256`, `state`; `state =
CONSUMED`.  UTF-8, no BOM, exactly one final LF.

**10.1** For the **new Recovery-R1 authorization claim**: `authorization_commit =
<INDEPENDENTLY_ACCEPTED_RECOVERY_AUTHORIZATION_COMMIT>`; `authorization_sha256 =
<INDEPENDENTLY_ACCEPTED_RECOVERY_AUTHORIZATION_SHA256>`; `oracle_commit =
1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc`; `oracle_sha256 =
01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921`.

**10.2** The placeholders are populated **only** by the later independent approval record; they are not
executor choices.

## 11. Recovery authorization budget

| State variable | Budget |
| --- | --- |
| `RECOVERY_AUTHORIZATION_USE_BUDGET` | **1 of 1** |
| `RECOVERY_ETB_ATTEMPT_BUDGET` | **1 of 1** |

**11.1** Consumption uses the same exact accepted writer boundary: the successful
`[System.IO.FileMode]::CreateNew` creation of `ETB_RECOVERY_R1_AUTHORIZATION_USE.claim.tmp` ⇒
`RECOVERY AUTHORIZATION USE = 1/1 CONSUMED`.  No retry, no reuse, no cleanup.

## 12. Pre-claim recovery preconditions (read-only)

Before consuming Recovery-R1 authorization, future execution must verify, read-only:

**A.** working directory = repository root;
**B.** HEAD corresponds to the independently accepted recovery-bookkeeping baseline that will later be
frozen;
**C.** the original authorization claim **FINAL** is OCCUPIED by the exact expected original claim
(SHA-256 `d84b428586f07a55a99f5b1391481d77763ec4ea697a40d1cec8aa0779613d4e`);
**D.** the original authorization claim **TEMP** is ABSENT;
**E.** the original ETB attempt claim **TEMP and FINAL** are ABSENT;
**F.** current config SHA-256 = `b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf`;
**G.** current config size = `1897`;
**H.** production-resolved `base_url` = `http://127.0.0.1:4096`;
**I.** `docs/v0.3/evidence/etb-execution` exists and is an actual directory;
**J.** `CONFIG_ESTABLISHMENT.json` is ABSENT;
**K.** `CONFIG_ESTABLISHMENT.json.tmp` is ABSENT;
**L.** all four **new** Recovery-R1 claim paths are ABSENT.

**12.1** Failure of any pre-claim condition → RECOVERY AUTHORIZATION remains **UNUSED**; STOP; no mutation,
no cleanup, no ETB.

## 13. Config-establishment evidence recovery purpose

**13.1** Recovery does **not** perform configuration establishment again.  It performs
**CONFIG_ESTABLISHMENT EVIDENCE RECOVERY / PUBLICATION** for the configuration transition that **already
successfully occurred** under the **original** accepted authorization.

**13.2** The recovered evidence must **truthfully describe that original transition** and must **not**
imply that Recovery-R1 mutated the config.

## 14. Original-vs-recovery provenance separation

**14.1** The recovered `docs/v0.3/evidence/etb-execution/CONFIG_ESTABLISHMENT.json` **must retain the
original configuration-transition authorization identity**:

| Field | Value (original identity — NOT the recovery identity) |
| --- | --- |
| `authorization_commit` | `64044fc45082cd63b0ae445c146d85720dfa1435` |
| `authorization_sha256` | `511ab1e2eb2e4f1194d2c55951e5b9616dc515d1180c6399dd658207d443d0d8` |

**14.2** Reason: this file records the config transition that actually occurred under the original
authorization.  Recovery-R1 authority is separately proven by `ETB_RECOVERY_R1_AUTHORIZATION_USE.claim`.
**The two provenance domains must not be conflated.**

## 15. Exact CONFIG_ESTABLISHMENT schema reproduction (17 ordered fields, explicit values)

`schema_version = devrelay-etb-config-establishment-v1`; `[ordered]` objects; serialization and publication
exactly per §19.  All 17 fields, with their exact values, so that a future executor chooses nothing:

| # | Field | Value |
| --- | --- | --- |
| 1 | `schema_version` | `devrelay-etb-config-establishment-v1` |
| 2 | `authorization_commit` | `64044fc45082cd63b0ae445c146d85720dfa1435` |
| 3 | `authorization_sha256` | `511ab1e2eb2e4f1194d2c55951e5b9616dc515d1180c6399dd658207d443d0d8` |
| 4 | `oracle_commit` | `1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc` |
| 5 | `oracle_sha256` | `01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921` |
| 6 | `config_path` | `.devrelay/config.yaml` |
| 7 | `pre_config_sha256` | `daaf72578cb4a91b5adeb481530baf47577174325167caddf7249964da7923a8` (historical) |
| 8 | `expected_pre_config_sha256` | `daaf72578cb4a91b5adeb481530baf47577174325167caddf7249964da7923a8` |
| 9 | `pre_resolved_base_url` | `""` (historical) |
| 10 | `authorized_base_url` | `http://127.0.0.1:4096` |
| 11 | `post_config_sha256` | `b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf` (current post-image) |
| 12 | `expected_post_config_sha256` | `b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf` |
| 13 | `post_resolved_base_url` | `http://127.0.0.1:4096` |
| 14 | `mutation_scope` | `opencode.base_url_only` |
| 15 | `authorization_use` | `1/1_CONSUMED` |
| 16 | `etb_attempt` | `0/1_NOT_STARTED` |
| 17 | `control_status` | `CONFIG_ESTABLISHED` |

**15.1** **No recovery-specific field is permitted**: no `recovery_authorization_commit`, no
`recovery_reason`, no timestamp, no comment, no additional field.  `schema_version` and the field order must
not change.  The evidence remains the evidence record of the **original** configuration establishment.

## 16. Historical preimage handling

**16.1** `pre_config_sha256` is populated from the **historically verified pre-mutation value**
`daaf72578cb4a91b5adeb481530baf47577174325167caddf7249964da7923a8`; `expected_pre_config_sha256` is
populated from the same frozen expected pre-mutation constant; `pre_resolved_base_url` is populated from the
historically verified pre-mutation resolved value `""`.

**16.2** These are **historical evidence values**.  They must **not** be validated by requiring the
**current** config to equal the preimage.

## 17. Current postimage handling

**17.1** Before recovered-evidence publication — and only after Recovery-R1 authorization has been consumed
— reverify **read-only**: current config SHA-256 =
`b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf`; current config size = `1897`;
production-resolved `base_url` = `http://127.0.0.1:4096`.

**17.2** `post_config_sha256`, `expected_post_config_sha256` and `post_resolved_base_url` are populated from
exactly those frozen/current post-image values, per the accepted original schema.

## 18. Absolute forbidden assertion

**18.1** After the original config mutation has occurred, **no recovery step may assert**
`current_config_sha256 == PRE_CONFIG_SHA256` or any semantically equivalent logic, and **no recovery step
may assert** `current_resolved_base_url == ""`.  The historical preimage values are **evidence inputs only**
— they are **not** current-state predicates.

**18.2** The previously executor-authored `PRE_SHA_NOT_PREIMAGE` assertion is **FORBIDDEN**, and no
equivalent assertion may be added.  In particular, no executor-authored pre-write assertion of any kind is
permitted in the evidence-publication step (§19.3).

## 19. Exact serialization and publication rule

**19.1** Reuse exactly the accepted deterministic machinery: `ConvertTo-Json -Depth 12 -Compress`;
`[System.Text.UTF8Encoding]::new($false)`; one JSON line plus exactly one final LF; no CRLF conversion.

**19.2** `TEMP = docs/v0.3/evidence/etb-execution/CONFIG_ESTABLISHMENT.json.tmp`; `FINAL =
docs/v0.3/evidence/etb-execution/CONFIG_ESTABLISHMENT.json`; exclusive TEMP creation
(`[System.IO.FileMode]::CreateNew`, `[System.IO.FileAccess]::Write`, `[System.IO.FileShare]::None`) →
complete write → frozen flush semantics (`Flush($true)`) → close → read-back byte equality → same-directory
**two-argument** `System.IO.File.Move(temp, final)` with **no overwrite**.

**19.3** **No Python alternative, no alternate JSON serializer, no executor-authored pre-write assertion,
no retry.**  Any failure → §20.

## 20. Recovery evidence failure semantics

**20.1** After Recovery-R1 claim consumption, **any** failure in postimage verification, production-reader
verification, `CONFIG_ESTABLISHMENT` construction, serialization, TEMP creation, write, flush, read-back,
`File.Move` or final verification →

```
RECOVERY_AUTHORIZATION_CONTROL_FAILURE
RECOVERY AUTHORIZATION USE = CONSUMED
RECOVERY ETB ATTEMPT        = NOT STARTED
STOP
```

**20.2** No retry, no cleanup, no config rollback, no original-claim deletion.  A later **Recovery-R2**
authorization would be required.

## 21. Recovery ETB claim

**21.1** Only after `CONFIG_ESTABLISHMENT.json` is **successfully published**: require both
`ETB_RECOVERY_R1_ATTEMPT_USE.claim.tmp` and `ETB_RECOVERY_R1_ATTEMPT_USE.claim` **ABSENT** under the
accepted occupancy predicate, then invoke the exact accepted claim writer with `TempPath =
docs/v0.3/evidence/ETB_RECOVERY_R1_ATTEMPT_USE.claim.tmp`, `FinalPath =
docs/v0.3/evidence/ETB_RECOVERY_R1_ATTEMPT_USE.claim`, `SchemaVersion = devrelay-etb-attempt-use-v1`,
`AuthorizationCommit = <INDEPENDENTLY_ACCEPTED_RECOVERY_AUTHORIZATION_COMMIT>`, `AuthorizationSha256 =
<INDEPENDENTLY_ACCEPTED_RECOVERY_AUTHORIZATION_SHA256>`, `OracleCommit = 1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc`,
`OracleSha256 = 01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921`.

**21.2** Successful TEMP `CreateNew` ⇒ `RECOVERY ETB ATTEMPT = 1/1 CONSUMED`.  **This is the FIRST actual
ETB attempt**; the original failed operational round consumed **no** ETB attempt.

## 22. Recovery ETB claim failure semantics

**22.1** If the recovery ETB claim TEMP or FINAL is already **OCCUPIED** → `RECOVERY ETB ATTEMPT =
CONSUMED` → STOP.  If claim creation succeeds but publication later fails → the attempt **remains
CONSUMED**, and **NO ETB SEMANTIC RESULT EXISTS** if the oracle was not entered.  No retry; no second
attempt.

## 23. Enter frozen oracle

**23.1** Only after (i) the Recovery-R1 authorization claim has been successfully finalized, (ii) the
existing post-image has been successfully reverified, (iii) `CONFIG_ESTABLISHMENT.json` has been
successfully recovered/published, and (iv) the Recovery-R1 ETB claim has been successfully finalized, may
execution enter `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md` **from its FIRST STEP**, using exactly
the accepted frozen oracle with no modification and **no pre-oracle endpoint/listener/process probe**.

**23.2** The authorization/recovery layer **MUST NOT** pre-check, pre-interpret, delete, repair or act on
the oracle's six frozen output paths; the oracle alone handles those paths inside the consumed ETB attempt.

## 24. Oracle boundaries (preserved)

No OpenCode start/restart; no HTTP; no `/doc`; no `/session`; no endpoint substitution; no endpoint
discovery; no IPv6; no `localhost` alias; no alternate port; no Mode L; no fallback; no retry; no second ETB
attempt.  Sole endpoint: `http://127.0.0.1:4096`; the target must already exist.

## 25. Oracle result

**25.1** Only the frozen oracle vocabulary: `ETB_SATISFIED`, `ETB_UNSATISFIED`, `HARNESS_INVALID / NO ETB
SEMANTIC RESULT`.  Whatever candidate result is produced remains **NON-AUTHORITATIVE** until independent
ETB-result review.  **No Mode-B work in the same round.**

## 26. Recovery authorization no-rollback

**26.1** Config remains `http://127.0.0.1:4096` throughout Recovery-R1.  No recovery action is authorized to
restore `""`.  If Recovery-R1 fails at any later step, the config is left at the exact post-image.

## 27. Original operational artifact preservation

**27.1** Never delete or rewrite `docs/v0.3/evidence/ETB_AUTHORIZATION_USE.claim` or the currently empty
`docs/v0.3/evidence/etb-execution` directory.  Once `CONFIG_ESTABLISHMENT.json` is successfully recovered it
becomes the control evidence for the original config establishment and must not be rewritten thereafter.

## 28. New recovery claim tracking policy

**28.1** The four new Recovery-R1 claim paths are **untracked operational control-state artifacts**.  They
must not be `git add`ed, staged, committed, deleted, renamed, archived or normalized before independent
result review, and they are **not** part of the tracked-worktree-clean predicate.  The same fail-closed
Git-state policy as the accepted original authorization applies.

## 29. Independent control-failure review record

**29.1** The independent review of the failed operational round returned:

```
CONFIRM AUTHORIZATION_CONTROL_FAILURE STATE — NEW AUTHORIZATION REQUIRED
P0 = 0, P1 = 1, P2 = 0, P3 = 1
```

and separately concluded:

```
STATE_MACHINE_FINAL_STATE          = VALID
EXECUTION_PROCEDURE_FIDELITY       = NONCONFORMANT
CONFIG_EVIDENCE_SCHEMA             = SOUND
FAILURE_CAUSE                      = EXECUTOR_NONCONFORMANCE
ORIGINAL_AUTHORIZATION_REUSABLE    = NO
CONFIG_MUTATION_REPLAY_ALLOWED     = NO
```

**29.2** The confirmed final state of that round was: original authorization **SPENT / NOT REUSABLE**;
`AUTHORIZATION USE = 1/1 CONSUMED`; original `ETB ATTEMPT = 0/1 NOT STARTED`; **no ETB semantic result**;
config = exact frozen post-image; `CONFIG_ESTABLISHMENT = MISSING`; oracle **never entered**.

## 30. Mode-B / G0.5 / implementation preservation

Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE
CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 **NOT CLOSED**;
Case-C `NOT AUTHORIZED`; v0.3-E implementation `NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`;
`adopt_completed_turn` **DISABLED**.  **The fact that the config now contains the endpoint does NOT
establish target binding.**

## 31. Authoritative sequence (extended)

Round-5 authorization independently accepted → acceptance bookkeeping independently accepted → one-shot
operational authorization consumed → exact config mutation completed → `CONFIG_ESTABLISHMENT` publication
failed due to executor nonconformance → `AUTHORIZATION_CONTROL_FAILURE` → independent control-state review
confirmed the state → original authorization permanently spent → **Recovery-R1 authorization design (this
artifact)** → independent Recovery-R1 authorization review → if accepted, Recovery-R1 acceptance
bookkeeping → independent bookkeeping confirmation → one Recovery-R1 operational use → verify existing
post-image → recover/publish the missing `CONFIG_ESTABLISHMENT` evidence → consume one Recovery-R1 ETB
attempt → enter the frozen oracle once → independent ETB-result review → only an independently accepted
`ETB_SATISFIED` may permit Mode-B construction.  **No stage is skipped.**

## 32. Current status

```
ETB CONTROL-STATE RECOVERY AUTHORIZATION = RECOVERY-R1 CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT EXECUTED
ORIGINAL ROUND-5 AUTHORIZATION           = SPENT / NOT REUSABLE / AUTHORIZATION_CONTROL_FAILURE
ORIGINAL ETB ATTEMPT                     = 0/1 NOT STARTED
ETB SEMANTIC RESULT                      = NONE
CONFIG                                   = EXACT POSTIMAGE
CONFIG_ESTABLISHMENT                     = MISSING
ORACLE                                   = NOT ENTERED
```

**32.1** No recovery authority is granted yet; no recovery is performed by this round; no claim is created;
no config is modified; the oracle is not entered.

## 33. Activity counters (this design round)

web/network `0`; endpoint queries `0`; `Get-NetTCPConnection` `0`; live `Get-CimInstance` `0`;
listener/process/port enumeration `0`; config mutation `0`; claim creation `0`; claim-path directory
creation `0`; `CONFIG_ESTABLISHMENT` publication `0`; OpenCode start/restart `0`; HTTP `0`; `/doc` `0`;
`/session` `0`; `Add-Type` `0`; P/Invoke `0`; ETB execution `0`; SIC `0`; Mode-B work `0`; provider/model
`0`; G0.5 `0`; G1/G2 `0`; runtime/test/dependency/version changes `0`.

## 34. Executor-choice self-check (frozen, no material choice)

Frozen for a future Recovery-R1 executor: the recovery baseline; the fact that config is **not** mutated;
the current post-image hash/size/resolved value; the historical preimage values (evidence inputs only); the
original-vs-recovery provenance split in `CONFIG_ESTABLISHMENT.json`; all 17 evidence fields with explicit
values; the serialization and publication primitive; the **forbidden** `PRE_SHA_NOT_PREIMAGE` assertion and
the ban on executor-authored pre-write assertions; the recovery claim paths; the recovery claim writer
(verbatim accepted function); the recovery authorization identity binding; the recovery ETB claim paths; the
ETB attempt boundary; the oracle identity; the oracle entry boundary; retry; cleanup; rollback; and the
Mode-B prohibition.

**End of ETB control-state recovery authorization, Recovery-R1 design candidate.**
