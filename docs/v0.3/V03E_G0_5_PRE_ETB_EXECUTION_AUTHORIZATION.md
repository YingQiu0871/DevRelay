# DevRelay v0.3-E — G0.5-PRE / SIC — ETB execution / configuration authorization

> **ETB EXECUTION / CONFIGURATION AUTHORIZATION**
> **CANDIDATE RECORD**
> **NOT ACCEPTED**
> **NOT EFFECTIVE**
> **DOES NOT MODIFY CONFIGURATION**
> **DOES NOT EXECUTE ETB**
> **DOES NOT START OPENCODE**
> **DOES NOT AUTHORIZE HTTP**
> **ONE ETB ATTEMPT ONLY IF LATER INDEPENDENTLY ACCEPTED**

Status: **ETB EXECUTION / CONFIGURATION AUTHORIZATION = ROUND-5 CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT EXECUTED**

Revision: **round-5 claim-path type semantic closure candidate** (supersedes the Round-4 candidate
`008115d`, which received *REQUEST_CHANGES — V0.3-E ETB EXECUTION / CONFIGURATION AUTHORIZATION ROUND-4*,
P0 = 0, P1 = 0, P2 = 1, P3 = 2; the Round-3 candidate `c106b2d`, which received *REQUEST_CHANGES — V0.3-E
ETB EXECUTION / CONFIGURATION AUTHORIZATION ROUND-3*, P0 = 0, P1 = 1, P2 = 1, P3 = 2; the Round-2
candidate `390eda1`, which received *REQUEST_CHANGES — V0.3-E ETB EXECUTION / CONFIGURATION AUTHORIZATION
ROUND-2*, P0 = 0, P1 = 1, P2 = 0, P3 = 2; and the earlier `f52cb2b`, which received *REQUEST_CHANGES —
V0.3-E ETB EXECUTION / CONFIGURATION AUTHORIZATION*, P0 = 0, P1 = 2, P2 = 2).  **All four remain
rejected.**

Baseline: `008115d6988c76d3c4ce185f73d047d44f5d8579` (branch `v0.3-e-recovery-reconciliation`).

This artifact is a **candidate authorization record only**.  It authorizes nothing today: it creates no
claim marker, creates no evidence directory, modifies no configuration, executes no ETB attempt, starts
no OpenCode, issues no HTTP and publishes no evidence.  It becomes effective **only** if a separate
independent authorization review accepts it.

Accepted frozen oracle provenance (immutable; bound permanently):

| Item | Value |
| --- | --- |
| `oracle_commit` | `1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc` |
| `oracle_artifact` | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md` |
| `oracle_sha256` | `01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921` |

Current authoritative status: `ETB = DEFINITION ACCEPTED / NOT EXECUTED`; `ETB EXECUTION / ORACLE =
ACCEPTED / FROZEN / NOT EXECUTED / EXECUTION NOT AUTHORIZED`.

**Remediation scope.**  Round 5 closes exactly the Round-4 finding and redesigns nothing else:
**CLAIM_PATH_TYPE_SEMANTICS** — one exact path-occupancy predicate is now frozen (`File.Exists(path)` **or**
`Directory.Exists(path)`), the frozen claim writer's three path checks are widened to that predicate, the
directory-at-claim-path corners are classified fail-closed, and the recovery table now speaks only in
terms of that predicate (§11, §14, §25).  Everything already closed is preserved semantically unchanged
(Round-3 claim-writer closure, PowerShell/.NET-only writer, `ConvertTo-Json -Depth 4 -Compress`,
`UTF8Encoding(false)`, real PowerShell LF, `FileMode.CreateNew`/`FileAccess.Write`/`FileShare.None`, the
single `Write()`, `Flush(true)`, `Dispose()`, `ReadAllBytes()`, byte-by-byte verification, two-argument
`File.Move`, the process-crash-only recovery model, tracking/commit policy, future claim namespace, claim
non-deletion, the directory create/verify rule, byte-exact config mutation, the `CONFIG_ESTABLISHMENT`
path/schema/serialization, both 1-of-1 budgets, output-precondition timing, the owner tuple, oracle
provenance and Mode-B/G0.5 preservation).

## 1. Purpose and scope

**1.1** This candidate authorization, **only after independent authorization review and acceptance**, may
authorize exactly two things, in this order:

* **A. one exact configuration establishment** — write `http://127.0.0.1:4096` to
  `<root>/.devrelay/config.yaml` → `opencode.base_url`; and then
* **B. exactly ONE ETB execution attempt** under the already accepted frozen ETB oracle.

**1.2** This round performs **neither A nor B**, and does not authorize them.

## 2. Authorized configuration mutation (exact; preserved)

| Item | Value |
| --- | --- |
| file | `<root>/.devrelay/config.yaml` |
| field | `opencode.base_url` |
| before | `""` (current value) |
| after | **`http://127.0.0.1:4096`** |

No trailing slash; no alternate URI; **no other configuration field change**; no other `.devrelay` field;
no source file; no test; no dependency; no version; no runtime implementation.

## 3. Owner inputs (preserved, not reinterpreted)

**MODE P — PRE-EXISTING TARGET**; **CLASS A — OWNER-SUPPLIED FIXED ENDPOINT**; scheme `http`; address
family IPv4; host `127.0.0.1`; port `4096`; base URI `http://127.0.0.1:4096`; fallback **NONE**.  No
substitution, no alternate endpoint, no Mode P → Mode L, no OpenCode start, no retry.

## 4. Static config audit (read-only; preserved)

| Fact | Value |
| --- | --- |
| `PRE_CONFIG_SHA256` | `daaf72578cb4a91b5adeb481530baf47577174325167caddf7249964da7923a8` |
| `PRE_CONFIG_SIZE` | `1876` bytes |
| BOM | **none** |
| line ending | **LF only** (0 CRLF), final LF present |
| encoding | valid UTF-8 |
| duplicate-key audit | **clean** at every mapping level; exactly one effective `opencode` key and exactly one effective `base_url` key; no anchors, aliases or merge keys |
| production-resolved pre-value | `opencode.base_url == ""` (`configured == False`) |

## 5. Byte-exact mutation anchor (preserved)

Unique span at offset **1065**, length 24, **occurrence count exactly 1**:

```
OLD_CONFIG_SPAN_HEX = 6f70656e636f64653a0a2020626173655f75726c3a202222
NEW_CONFIG_SPAN_HEX = 6f70656e636f64653a0a2020626173655f75726c3a2022687474703a2f2f3132372e302e302e313a3430393622
```

Statically constructed post-image: `POST_CONFIG_SIZE = 1897` bytes; `POST_CONFIG_SHA256 =
b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf`.  Byte-diff witness: 1065 unchanged
prefix bytes and 787 unchanged suffix bytes; only the frozen span changes.  No `yaml.safe_dump`, regex
edit, generic string replacement or manual-editor mutation is authorized.

## 6. Config mutation algorithm (preserved)

Read raw bytes → require SHA-256/size equal to the pre-image facts → require the OLD span occurs exactly
once → replace that one span with the NEW span → require the constructed bytes (before writing) to
hash/size to the post-image facts.  Any failure → `AUTHORIZATION_CONTROL_FAILURE` / ETB NOT STARTED.

## 7. Config temp / final paths (preserved)

`CONFIG FINAL = <root>/.devrelay/config.yaml`; `CONFIG TEMP = <root>/.devrelay/config.yaml.etb-auth.tmp`;
**`CONFIG BACKUP = NONE`**; the temp must not exist before mutation (else
`AUTHORIZATION_CONTROL_FAILURE`), with no delete, reuse, overwrite or retry.

## 8. Config write / durability procedure (preserved; the CONFIG writer remains Python)

Single `python` invocation: read/verify pre-image → construct exact post-image bytes → exclusive create
(`xb`) the temp → write the complete post-image → stream flush → `os.fsync(temp_file.fileno())` → close →
read-back byte/hash verification → publish by exactly `os.replace(CONFIG_TEMP, CONFIG_FINAL)` in the same
directory → post-replace read-back verification → one production-reader invocation requiring the resolved
value `http://127.0.0.1:4096`.  No alternate rename primitive, no backup, no copy-delete sequence, no
direct in-place write, no retry.  Any failure → `AUTHORIZATION_CONTROL_FAILURE` / ETB NOT STARTED /
AUTHORIZATION SPENT.  **This is the CONFIG writer only; the CLAIM writers are PowerShell/.NET only
(§13).**

## 9. Config semantic-preservation rule (preserved)

The post-image must be byte-identical to the pre-image outside the frozen span replacement, and the
executor must produce an exact byte-diff witness proving that only that span changed.  No unrelated
semantic or formatting change is authorized.

## 10. Control-marker parent and exact claim paths (preserved)

The two one-shot **claim markers** use the **already existing** repository directory `docs/v0.3/evidence`
as their parent, and are deliberately **not** placed inside the non-existent `etb-execution` directory:

| Marker | Final path | Temp path |
| --- | --- | --- |
| authorization claim | `docs/v0.3/evidence/ETB_AUTHORIZATION_USE.claim` | `docs/v0.3/evidence/ETB_AUTHORIZATION_USE.claim.tmp` |
| ETB attempt claim | `docs/v0.3/evidence/ETB_ATTEMPT_USE.claim` | `docs/v0.3/evidence/ETB_ATTEMPT_USE.claim.tmp` |

These files are **control-state markers**: not ETB semantic evidence, not included in the ETB
`MANIFEST.sha256`, and not Mode-B evidence.

**10.1 Root binding (wording-only strengthening of the already accepted binding).**  Future operational
execution **MUST** run with the repository root as its working directory before any relative frozen
claim/config/evidence path is evaluated.  All relative paths in this authorization are
**repository-root-relative**.  No other root-resolution mechanism is introduced.

## 11. Claim presence is authoritative (occupancy predicate §11.4)

**11.1** If the authorization claim temp **and** its final are both **ABSENT** (per the predicate of
§11.4) → authorization state = **UNUSED**.

**11.2** If the authorization claim temp **or** its final is **OCCUPIED** (per the predicate of §11.4) →
authorization state = **CONSUMED**.  This remains true even if the claim content is incomplete, a process
crashed during claim writing, or the final rename never occurred, and it holds whether the occupant is a
**file** or a **directory**.  **Occupancy of either path is deliberately fail-closed evidence that the
authorization was claimed.  No parser success is required.**

**11.3** If the ETB attempt claim temp **and** its final are both **ABSENT** → ETB attempt state =
**NOT STARTED** (subject to the authorization state).  If either is **OCCUPIED** → ETB attempt state =
**CONSUMED**.  Again: temp **or** final occupancy is enough, and no parser success is required.

**11.4 Frozen path-occupancy predicate (Round-5 closure).**  For claim TEMP/FINAL path state the **only**
permitted meaning of "present", "exists" or "occupied" is:

```
CLAIM_PATH_OCCUPIED(path)  :=  [System.IO.File]::Exists(path) -or [System.IO.Directory]::Exists(path)

CLAIM PATH ABSENT   :=  File.Exists(path) == false AND Directory.Exists(path) == false
CLAIM PATH OCCUPIED :=  File.Exists(path) == true  OR  Directory.Exists(path) == true
```

**11.5** This predicate applies **identically** to the authorization claim TEMP, the authorization claim
FINAL, the ETB-attempt claim TEMP and the ETB-attempt claim FINAL.  No other notion of presence is
permitted for claim-path state.

**11.6 Directory at a claim path.**  If an actual **directory** occupies **any** claim TEMP or FINAL path,
that path is **OCCUPIED**:

* authorization claim paths — OCCUPIED temp or final → **AUTHORIZATION CONSUMED** → STOP → the writer MUST
  NOT proceed to `CreateNew` → no cleanup, no deletion, no rename, no retry → independent review required
  before any future action;
* ETB-attempt claim paths — OCCUPIED temp or final → **ETB ATTEMPT CONSUMED** → STOP → no rerun → the
  writer MUST NOT proceed to `CreateNew` → no cleanup, no deletion, no rename.

**11.7** Do **not** attempt to determine whether such a directory is legitimate claim content.
**Occupancy alone is fail-closed.**

**11.8** A partial claim **file**, a zero-length claim **file**, a malformed claim **file** and a claim
**directory** all count as **OCCUPIED** whenever `File.Exists(path)` **or** `Directory.Exists(path)` is
true.  No parsing is required to classify the claim state, and no repair is authorized.

## 12. Claim content (schemas; preserved)

Authorization claim — `schema_version = devrelay-etb-authorization-use-v1`; ordered fields exactly
`schema_version`, `authorization_commit`, `authorization_sha256`, `oracle_commit`, `oracle_sha256`,
`state`; `state = CONSUMED`.

ETB attempt claim — `schema_version = devrelay-etb-attempt-use-v1`; the same ordered fields;
`state = CONSUMED`.

Both: deterministic UTF-8, **no BOM**, exactly one final LF; no timestamp; no
user/session/message/provider/model content.

## 13. Single claim-writer language (P1 closure)

**13.1** BOTH claim writers are frozen to **Windows PowerShell / .NET ONLY**.

**13.2** No Python claim writer.  No `os.fsync` alternative.  No alternate implementation language.  No
executor-authored replacement code.

**13.3** The exact frozen writer source in §14 MUST be embedded and used **verbatim** by a future
executor.

## 14. Exact frozen claim writer source (P1 closure)

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

**14.1 Frozen mechanisms (no alternatives):** `ConvertTo-Json -Depth 4 -Compress`;
`[System.Text.UTF8Encoding]::new($false)`; `$json + "`n"`; `[System.IO.FileStream]::new(...)` with
`[System.IO.FileMode]::CreateNew`, `[System.IO.FileAccess]::Write`, `[System.IO.FileShare]::None`;
`$stream.Write($bytes, 0, $bytes.Length)`; `$stream.Flush($true)`; `$stream.Dispose()`;
`[System.IO.File]::ReadAllBytes(...)`; explicit byte-by-byte equality; `[System.IO.File]::Move(source,
destination)` using the **two-argument overload**; and the three path checks expressed through the frozen
occupancy predicate of §11.4 (`[System.IO.File]::Exists(path) -or [System.IO.Directory]::Exists(path)`) for
the initial TEMP pre-check, the initial FINAL pre-check and the pre-`Move` FINAL re-check.

**14.2 Forbidden:** any overwrite `File.Move` overload; `File.Replace`; `Move-Item`; `Rename-Item`; any
Python rename; `os.rename`; `os.replace`; and any other alternate primitive.

## 15. Exclusive-create consumption semantics (P1 closure)

**15.1** The semantic consumption boundary remains the **successful return** from

```powershell
[System.IO.FileStream]::new(
    $TempPath,
    [System.IO.FileMode]::CreateNew,
    [System.IO.FileAccess]::Write,
    [System.IO.FileShare]::None
)
```

**15.2** At that exact point the temp has been exclusively created and, as applicable, `AUTHORIZATION_USE`
or `ETB_ATTEMPT` is **CONSUMED**.

**15.3** `FileMode.CreateNew` **MUST fail if `TempPath` already exists**.  No truncation.  No reuse.  No
overwrite.

## 16. Move / no-overwrite semantics (P1 closure)

**16.1** Publication is exactly `[System.IO.File]::Move($TempPath, $FinalPath)` using the **two-argument
overload**.

**16.2** The destination **MUST NOT** exist.  The two-argument .NET `File.Move` used here is the **sole**
publication primitive and is required to **fail rather than overwrite** an existing destination.

**16.3** The explicit FINAL occupancy check before the move — `[System.IO.File]::Exists($FinalPath) -or
[System.IO.Directory]::Exists($FinalPath)`, per the frozen predicate of §11.4 — is an **additional
fail-closed check**; it does **not** authorize another move primitive.

**16.4** If a **directory** appears at `FinalPath` after the TEMP `CreateNew` but before publication, that
second frozen FINAL occupancy check detects it → the claim **remains CONSUMED** → the writer throws
`DEVRELAY_CLAIM_FINAL_APPEARED` → STOP → no cleanup, no retry, and **no `File.Move` attempt is made after
that check detects occupancy**.

**16.5** If a **directory** occupies `FinalPath` **before** writer invocation, FINAL is **OCCUPIED** → the
claim is already **CONSUMED** → STOP before `CreateNew`.

## 17. Write-all rule (P1 closure)

**17.1** The entire byte array is written by the single `$stream.Write($bytes, 0, $bytes.Length)`
operation.

**17.2** After `Flush(true)` and close, `ReadAllBytes(temp)` must equal the intended byte array exactly;
after `File.Move`, `ReadAllBytes(final)` must equal the intended byte array exactly.

**17.3** No serializer or encoding alternatives.

## 18. Exact authorization claim invocation

Future invocation must be exactly equivalent to:

```powershell
Write-DevRelayOneShotClaim `
    -TempPath 'docs/v0.3/evidence/ETB_AUTHORIZATION_USE.claim.tmp' `
    -FinalPath 'docs/v0.3/evidence/ETB_AUTHORIZATION_USE.claim' `
    -SchemaVersion 'devrelay-etb-authorization-use-v1' `
    -AuthorizationCommit '<INDEPENDENTLY_ACCEPTED_AUTHORIZATION_COMMIT>' `
    -AuthorizationSha256 '<INDEPENDENTLY_ACCEPTED_AUTHORIZATION_SHA256>' `
    -OracleCommit '1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc' `
    -OracleSha256 '01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921'
```

**18.1** The two authorization placeholders are **NOT executor choices**: they are populated **only** from
the independent approval record for the immutable authorization artifact.  If **this** Round-4 candidate
is approved, they become `authorization_commit` = the Round-4 candidate commit and
`authorization_sha256` = the committed SHA-256 of this revised authorization artifact.

## 19. Exact ETB attempt claim invocation

Future invocation must be exactly equivalent to:

```powershell
Write-DevRelayOneShotClaim `
    -TempPath 'docs/v0.3/evidence/ETB_ATTEMPT_USE.claim.tmp' `
    -FinalPath 'docs/v0.3/evidence/ETB_ATTEMPT_USE.claim' `
    -SchemaVersion 'devrelay-etb-attempt-use-v1' `
    -AuthorizationCommit '<INDEPENDENTLY_ACCEPTED_AUTHORIZATION_COMMIT>' `
    -AuthorizationSha256 '<INDEPENDENTLY_ACCEPTED_AUTHORIZATION_SHA256>' `
    -OracleCommit '1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc' `
    -OracleSha256 '01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921'
```

**19.1** No other schema, version or path is allowed.

## 20. Claim writer failure semantics

**20.1 Authorization claim.**  If `TempPath` or `FinalPath` is **OCCUPIED** (frozen predicate of §11.4:
`File.Exists` **or** `Directory.Exists`) **before** writer invocation, the authorization is already
**CONSUMED** → STOP; do **not** invoke the writer.  If `FileMode.CreateNew` succeeds, the authorization is
**CONSUMED immediately**.  Any later writer exception leaves the authorization **CONSUMED** →
`AUTHORIZATION_CONTROL_FAILURE`, ETB **NOT STARTED**, STOP.  No cleanup.  No retry.  No alternate writer.

**20.2 ETB attempt claim.**  If `TempPath` or `FinalPath` is **OCCUPIED** (same frozen predicate), the ETB
attempt is already **CONSUMED** → STOP; no rerun.  If `FileMode.CreateNew` succeeds,
`ETB_ATTEMPT = 1/1 CONSUMED` immediately.  Any later writer exception leaves the ETB attempt **CONSUMED** →
**NO ETB SEMANTIC RESULT EXISTS** if the oracle has not yet been entered, STOP.  No cleanup.  No retry.  No
second ETB attempt.

**20.3** If `CLAIM_PATH_OCCUPIED(TempPath)` is true before invocation, the claim is already classified
**CONSUMED** by fail-closed occupancy semantics and the writer **MUST NOT** attempt `CreateNew`.  The
directory-at-TEMP corner is therefore **never** interpreted as UNUSED.

## 21. Crash model — process-crash recovery only (P2 closure)

**21.1** The supported guarantee for the claim markers is **PROCESS-CRASH RECOVERY**: if the
PowerShell/executor process terminates after successful OS-visible exclusive creation of a claim temp
file, the next executor is required to interpret an **OCCUPIED** TEMP or FINAL claim path (§11.4) as
**CONSUMED** and fail closed.

**21.2 Explicit non-claim:**

> **THIS AUTHORIZATION DOES NOT CLAIM POWER-LOSS DURABILITY OR MACHINE-CRASH DURABILITY FOR CLAIM
> DIRECTORY METADATA.**

**21.3** `Flush(true)` is used for **file-content** flushing before normal publication.  **No
parent-directory fsync guarantee is claimed**, and no guarantee is made for sudden power loss between
filesystem metadata operations.

**21.4** This limitation does **not** weaken the required process-crash one-shot semantics.

## 22. Terminology replacement (P2 closure)

Where semantically applicable, phrases such as "durable consumption boundary", "durably consumed" and
"durable one-shot witness" are replaced by precise phrases such as **"process-crash recovery consumption
boundary"**, **"process-crash-persistent one-shot marker"** and **"filesystem-presence one-shot
witness"** — or equivalent wording that does **not** imply power-loss durability.  The logical state
machine is unchanged.

## 23. Execution-evidence directory rule (preserved)

**23.1** Exact directory: `docs/v0.3/evidence/etb-execution`; **design-time state: it does NOT exist.**

**23.2** Creation occurs **only after** the authorization claim is consumed and **before** configuration
mutation; if absent, create **exactly** `docs/v0.3/evidence/etb-execution` using
`[System.IO.Directory]::CreateDirectory("docs/v0.3/evidence/etb-execution")` (repository-root-resolved
exact equivalent permitted), with **no alternate path, no parent search, no timestamped directory, no
suffix and no fallback**.

**23.3** After the call, require that the exact path exists and **is a directory**.  Creation failure or a
non-directory → `AUTHORIZATION_CONTROL_FAILURE`, authorization consumed, ETB attempt not started, STOP;
no cleanup, no retry, no alternate directory.

**23.4** An already existing **actual directory** is permitted (never deleted or recreated); a path that
exists but is not a directory → `AUTHORIZATION_CONTROL_FAILURE`.

## 24. Config-establishment outputs (preserved)

`docs/v0.3/evidence/etb-execution/CONFIG_ESTABLISHMENT.json` (final) and `…json.tmp` (temp); both must not
exist before config mutation; any existence → `AUTHORIZATION_CONTROL_FAILURE` with authorization consumed,
ETB not started, no deletion, no overwrite, no retry.

**24.1** The `devrelay-etb-config-establishment-v1` schema, its exact 17-field ordered top-level schema
(`schema_version`, `authorization_commit`, `authorization_sha256`, `oracle_commit`, `oracle_sha256`,
`config_path`, `pre_config_sha256`, `expected_pre_config_sha256`, `pre_resolved_base_url`,
`authorized_base_url`, `post_config_sha256`, `expected_post_config_sha256`, `post_resolved_base_url`,
`mutation_scope`, `authorization_use`, `etb_attempt`, `control_status`), its frozen constants
(`config_path = .devrelay/config.yaml`; `authorized_base_url = http://127.0.0.1:4096`; `mutation_scope =
opencode.base_url_only`; `authorization_use = 1/1_CONSUMED`; `etb_attempt = 0/1_NOT_STARTED`;
`control_status = CONFIG_ESTABLISHED`) and its deterministic serialization (`ConvertTo-Json -Depth 12
-Compress`, UTF-8 no-BOM, one JSON line plus exactly one LF, `UTF8Encoding(false)`, temp exclusive create →
write → durable flush → close → read-back verification → same-directory
`System.IO.File.Move(temp, final)` without overwrite) remain **exactly** the independently reviewed
Round-2 design.  This file remains authorization/configuration control evidence only.

## 25. Durable state machine (preserved; occupancy wording per §11.4)

| Authorization claim | ETB claim | Interpretation |
| --- | --- | --- |
| both TEMP and FINAL **ABSENT** | both TEMP and FINAL **ABSENT** | **AUTHORIZATION UNUSED** |
| TEMP or FINAL **OCCUPIED** | both TEMP and FINAL **ABSENT** | **AUTHORIZATION CONSUMED / ETB NOT STARTED** |
| TEMP or FINAL **OCCUPIED** | TEMP or FINAL **OCCUPIED** | **AUTHORIZATION CONSUMED / ETB ATTEMPT CONSUMED** |
| both TEMP and FINAL **ABSENT** | TEMP or FINAL **OCCUPIED** | **CONTROL-STATE INCONSISTENCY / FAIL CLOSED / NO EXECUTION / INDEPENDENT REVIEW REQUIRED** |

**25.0** "**OCCUPIED**" means exactly the frozen predicate of §11.4 —
`[System.IO.File]::Exists(path) -or [System.IO.Directory]::Exists(path)` — applied to the corresponding
claim TEMP/FINAL path.  "**ABSENT**" means both `File.Exists(path) == false` **and**
`Directory.Exists(path) == false`.  No undefined generic notion of "presence" is used anywhere in this
authorization, and **no parser success is required** for any row; no chat history and no executor memory is
needed.

**25.1** Claim markers are **never deleted** after success, `AUTHORIZATION_CONTROL_FAILURE`,
`ETB_UNSATISFIED`, `HARNESS_INVALID` or crash recovery: they are **process-crash-persistent one-shot
markers / filesystem-presence one-shot witnesses**.

**25.2 Budgets (preserved).**  `AUTHORIZATION_USE_BUDGET = 1 of 1` and `ETB_ATTEMPT_BUDGET = 1 of 1` are
separate boundaries, witnessed by claim-path **occupancy** (§11.4).

## 26. ETB attempt boundary (preserved)

`ETB_ATTEMPT = 1/1 CONSUMED` occurs on successful exclusive creation of the ETB claim temp, performed
**after** successful configuration establishment and `CONFIG_ESTABLISHMENT.json` publication and **before**
entering the accepted frozen oracle.  Any failure afterwards leaves the attempt consumed; there is no
second attempt.

## 27. Claim tracking policy (P3-1 closure)

**27.1** `ETB_AUTHORIZATION_USE.claim`, `ETB_AUTHORIZATION_USE.claim.tmp`, `ETB_ATTEMPT_USE.claim` and
`ETB_ATTEMPT_USE.claim.tmp` are intended **UNTRACKED OPERATIONAL CONTROL-STATE ARTIFACTS**.

**27.2** They are **NOT** part of the tracked-worktree-clean predicate, and their occupancy (§11.4) is **expected**
after operational authorization use.

**27.3** They **MUST NOT** be `git add`ed, staged, committed, deleted, renamed, archived or normalized
**before independent ETB-result review**.

**27.4** Any bookkeeping commit before independent ETB-result review **MUST use an exact allowlist of
intended tracked documentation files** and **MUST exclude** these claim markers.

**27.5** `.gitignore` must **not** be modified by this remediation.

## 28. Git status semantics (P3-1 closure)

**28.1** Frozen future reporting terminology: **"tracked worktree clean"** means **no tracked-file
modification outside the explicitly authorized operational changes**.  It does **NOT** mean
`git status --porcelain` is globally empty once untracked control/evidence markers exist.

**28.2** Future execution/result reports must **list expected untracked operational artifacts
separately**, and must **not** classify the expected claim markers themselves as accidental worktree
drift.

## 29. Claim markers must never be committed (P3-1 closure)

**29.1** Before independent ETB-result review completes, claim markers remain **untracked**.

**29.2** If a claim marker is found **staged**: **STOP**; do **not** unstage or delete it automatically;
report a control-state inconsistency for independent review.

**29.3** If a claim marker is found **committed unexpectedly**: **STOP**; do **not** rewrite history;
independent review is required.

**29.4** The claim-path occupancy semantics (§11.4) remain **fail closed regardless of Git tracking state**.

## 30. Future namespace rule (preserved)

**30.1** The current claim paths are **permanently reserved for THIS authorization identity**.  A future
additional authorization must independently freeze a **distinct claim namespace/path**.  Never delete the
current claims to reuse their names.

**30.2 Authorization identity model.**  If this Round-4 candidate is independently approved:
`authorization_commit` = the approved Round-4 candidate commit; `authorization_sha256` = the approved
revised authorization artifact SHA.  A later bookkeeping commit or the execution-time HEAD must **not**
replace it, and the claim-marker content must use that exact accepted pair.

## 31. Restored explicit output-precheck invariant (P3-2 closure)

> **The authorization layer MUST NOT pre-check, pre-interpret, delete, repair or otherwise act on the
> accepted oracle's six frozen temp/final ETB output paths.**

**31.1** Only after configuration establishment succeeds, `CONFIG_ESTABLISHMENT.json` succeeds and the ETB
claim is consumed/finalized does execution enter the accepted frozen oracle **from its FIRST STEP**.

**31.2** The accepted oracle **alone** performs its own six-path output-preexistence validation **inside
the already-consumed ETB attempt**.  No authorization-layer reinterpretation.

## 32. Operational order (preserved; claim steps now invoke the frozen writer)

1. static verification of the independently accepted authorization identity and oracle provenance;
2. require the authorization claim temp/final **absent**;
3. invoke `Write-DevRelayOneShotClaim` for the authorization claim — **`AUTHORIZATION_USE` becomes 1/1 CONSUMED** on successful `FileMode.CreateNew`;
4. complete/publish the authorization claim (temp → final via the two-argument `File.Move`);
5. create-or-verify exactly `docs/v0.3/evidence/etb-execution` under §23;
6. require `CONFIG_ESTABLISHMENT` final/temp absent;
7. verify the exact config pre-image SHA/size;
8. verify the production-resolved pre-value `""`;
9. construct the exact byte post-image;
10. write/fsync/read-back the config temp (Python config writer, §8);
11. `os.replace` config temp → config final;
12. verify the final `POST_CONFIG_SHA256`;
13. verify the production-resolved `base_url == http://127.0.0.1:4096`;
14. publish `CONFIG_ESTABLISHMENT.json`;
15. require the ETB attempt claim temp/final **absent**;
16. invoke `Write-DevRelayOneShotClaim` for the ETB attempt claim — **`ETB_ATTEMPT` becomes 1/1 CONSUMED** on successful `FileMode.CreateNew`;
17. complete/publish the ETB attempt claim (temp → final via the two-argument `File.Move`);
18. invoke the accepted frozen ETB oracle **from its first step**;
19. permit only the frozen oracle control/result state;
20. publish only oracle-defined ETB evidence/result;
21. **STOP**;
22. independent ETB-result review.

No Mode-B work.  No other sequencing change.

## 33. Failure semantics by window (preserved)

**33.1 Pre-authorization-claim failure** (before successful exclusive creation of the authorization claim
temp): authorization remains **UNUSED**; no config mutation may have occurred; no ETB attempt may have
begun; no alternate operational action is permitted — the **only** window in which the same accepted
authorization remains unused.

**33.2 Post-authorization-claim failure** (after successful exclusive creation, before ETB claim
creation): authorization **CONSUMED**, ETB **not started**, `AUTHORIZATION_CONTROL_FAILURE`, STOP, new
authorization required, no reuse.

**33.3 Post-ETB-claim failure** (after successful exclusive creation of the ETB claim temp): authorization
consumed, **ETB attempt consumed**, no second attempt; if the oracle was not yet entered there is **no ETB
semantic result**, STOP, independent review required; if the oracle was entered, only the accepted
oracle's taxonomy applies.

**33.4 Pre-ETB control token (preserved).**  `AUTHORIZATION_CONTROL_FAILURE` means: authorization
consumed; ETB execution did NOT start; `ETB_ATTEMPT` remains 0 of 1; **no** ETB semantic/control result
exists; it is **not** `ETB_UNSATISFIED`, **not** `ETB_SATISFIED`, **not** `HARNESS_INVALID` from an ETB
attempt, **not** SIC/P6/G0.5 failure.

## 34. Other preserved boundaries

**34.1 Pre-existing target.**  Mode P verifies a pre-existing target; no starting, restarting or launching
OpenCode, no listener creation, no rebinding, no Mode P → Mode L.  If the exact pre-existing target is
absent or cannot satisfy the frozen oracle, the attempt fails according to the oracle — no recovery by
target creation.

**34.2 No-fallback.**  Fallback stays **NONE**: no IPv4 → IPv6, no `localhost`, no `::1`, no other /
first-free / ephemeral port, no alternate executable or installation, no PATH-selected target, no
log/listener/process-derived endpoint, no retry against another endpoint.

**34.3 HTTP and OpenCode boundaries.**  The ETB execution performs **no HTTP**, no `/doc`, no `/session`
and no provider/model request; no Mode-B HTTP activity is authorized; `opencode serve`, OpenCode
launch/restart, process replacement and listener creation are **not** authorized.

**34.4 Result non-claims.**  The one-shot execution may produce only `ETB_SATISFIED`, `ETB_UNSATISFIED`, or
`HARNESS_INVALID / NO ETB SEMANTIC RESULT`; none is authoritative before separate independent ETB-result
review.  `ETB_SATISFIED` does **not** itself establish SIC semantics, P6, G0.5, session incarnation, turn
provenance, message provenance, pending-handle semantics, Mode-B PASS, Case-C authorization or
`adopt_completed_turn`; it only allows independent ETB result review and, only once `ETB_SATISFIED` is
independently accepted, resumption of Mode-B SIC oracle construction.  `ETB_UNSATISFIED` is only a
prerequisite/control result.  `HARNESS_INVALID` means **NO ETB SEMANTIC RESULT EXISTS**, with no retry and
no repair-and-continue inside the same authorization.

**34.5 Execution outputs.**  Only the evidence/result paths already frozen by the accepted oracle may be
used: no new alternative evidence path, no alternative result path, no alternate manifest, no
executor-selected filenames.

**34.6 No-rollback.**  Do **not** restore `base_url` automatically; do **not** delete claim markers; do
**not** delete config-evidence artifacts automatically.  No executor discretion.

**34.7 Mode-B / G0.5 / P6 / implementation.**  Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE /
CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER` (this
authorization candidate does not unblock it); `G0.5 / P6 = NOT RUN / DEFINITION ACCEPTED / ORACLE NOT
FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED` and G0.5 **NOT CLOSED**; Case-C and
v0.3-E implementation `NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`; `adopt_completed_turn` **DISABLED**.

## 35. Rejected authorization history

**35.1** `f52cb2b4c0ece73097511c816b448d9ede649fb5` — *REQUEST_CHANGES — V0.3-E ETB EXECUTION /
CONFIGURATION AUTHORIZATION*, P0 = 0, P1 = 2, P2 = 2 — remains rejected.
**35.2** `390eda1aeacb33032611030d47727e0a69650459` — *REQUEST_CHANGES — V0.3-E ETB EXECUTION /
CONFIGURATION AUTHORIZATION ROUND-2*, P0 = 0, P1 = 1, P2 = 0, P3 = 2 — remains rejected.
**35.3** `c106b2d93b272fb337795e8712f58e0c273088fa` (artifact SHA-256
`29019f683c4c217654034fc1408d2942b0b384832125fe80b7a6303927d015b0`) — *REQUEST_CHANGES — V0.3-E ETB
EXECUTION / CONFIGURATION AUTHORIZATION ROUND-3*, P0 = 0, P1 = 1, P2 = 1, P3 = 2 — remains rejected.
**35.4** `008115d6988c76d3c4ce185f73d047d44f5d8579` (artifact SHA-256
`dfe673e6ff961a7bdb324912ea541008d2ade98a5789b9bfc1581efe7f54bc10`) — *REQUEST_CHANGES — V0.3-E ETB
EXECUTION / CONFIGURATION AUTHORIZATION ROUND-4*, P0 = 0, P1 = 0, P2 = 1, P3 = 2 (the only blocking
finding was `CLAIM_PATH_TYPE_SEMANTICS = OPEN`: the state machine classified TEMP/FINAL "presence" while
the writer checked only `File.Exists`, so a directory at a claim path was classified differently) —
remains rejected.
**35.5** None of these is rewritten or amended; the candidate in force is **this round-5 revision**.

## 36. Current round status and activity counters

```
ETB EXECUTION / CONFIGURATION AUTHORIZATION = ROUND-5 CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT EXECUTED
ETB EXECUTION / ORACLE                        = ACCEPTED / FROZEN / NOT EXECUTED
ETB                                           = DEFINITION ACCEPTED / NOT EXECUTED
```

**36.1** No operational authorization is granted; no claim is created now; no directory is created now;
no config is changed now; no ETB is executed now.

**36.2** This remediation round performed: web/network `0`; endpoint query `0`; `Get-NetTCPConnection` `0`;
live `Get-CimInstance` `0`; port/listener/process enumeration `0`; config mutation `0`; OpenCode start `0`;
HTTP `0`; `/doc` `0`; `/session` `0`; `Add-Type` `0`; P/Invoke `0`; execution-evidence publication `0`; ETB
execution `0`; SIC `0`; Mode-B work `0`; provider/model `0`; G0.5 `0`; G1/G2 `0`;
runtime/test/dependency/version changes `0`.  Static document/config inspection is not operational ETB
activity.

**End of ETB execution / configuration authorization candidate record (round-4 claim-writer mechanical closure).**
