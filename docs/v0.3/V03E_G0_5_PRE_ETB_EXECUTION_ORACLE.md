# DevRelay v0.3-E — G0.5-PRE / SIC — ETB execution oracle (Mode P, Class-A fixed endpoint)

> **ETB EXECUTION ORACLE**
> **MODE P**
> **CLASS A OWNER-SUPPLIED FIXED ENDPOINT**
> **ORACLE CANDIDATE**
> **NOT ACCEPTED**
> **NOT FROZEN**
> **NOT EXECUTED**
> **DOES NOT MODIFY CONFIGURATION**
> **DOES NOT START OPENCODE**
> **DOES NOT PERFORM HTTP**
> **DOES NOT AUTHORIZE ETB EXECUTION**

Status: **ORACLE CANDIDATE — NOT ACCEPTED / NOT FROZEN / NOT EXECUTED / NOT AUTHORIZED**
Revision: **round-2 remediation candidate** (supersedes the rejected candidate `b117daf`, which received
*REQUEST_CHANGES — V0.3-E ETB MODE-P EXECUTION ORACLE*, P0 = 0, P1 = 3, P2 = 2; that candidate is **not**
accepted and **not** frozen).

Baseline: `b117dafd08fe545f64499de6f64dffe08cb8dcad` (branch `v0.3-e-recovery-reconciliation`).

This artifact is a **design**.  It freezes every semantic rule **and every piece of execution machinery**
a later authorized ETB attempt must apply, so that the executor chooses nothing at runtime.  It
establishes no endpoint, modifies no configuration, compiles nothing, starts nothing, issues no HTTP,
publishes no evidence, and executes no ETB.  It is self-contained: a future executor does not need the
rejected review report.

Anchors (committed Git blobs):

| Anchor | Identity |
| --- | --- |
| accepted ETB definition | `docs/v0.3/V03E_G0_5_PRE_MODE_B_ENDPOINT_BINDING.md`, blob `99cc6dcee4ab1a3f0589c3e7d11308d089601ba07d16cc2d37a9fc32c777b3a0` |
| accepted owner-decision record | `docs/v0.3/V03E_G0_5_PRE_ETB_OWNER_ORACLE_PARAMETERS.md`, blob `152311341b8bc8cfb93964f3709a6922a62d914c8a297dea1e3634940bb34cbe` |
| accepted Round-2 U2/U3 artifact | `docs/v0.3/V03E_G0_5_PRE_ETB_U2_U3_AUTHORITY_RESOLUTION.md`, blob `49b22a88a593ce9ce59e7da6ae5221d8300d4963cca5b9fdc2dc8c2b47a91453` |
| accepted prior U1/U2/U3 capability artifact | `docs/v0.3/V03E_G0_5_PRE_ETB_CAPABILITY_RESOLUTION.md`, blob `59e8ef575fa3ab854f65fee5e25621c51f74c8b76615d7d4d9fb1e071b4049ac` |

**Remediation scope (round 2).**  The independent review accepted the previous candidate's owner-tuple
preservation, ETB-definition conformance, production config-reader semantics
(**CONFIG_EXACTNESS_SOUND**), listener query and cardinality, PID/process query, `CreationDate` identity
semantics, `CreateFileW` parameter values, `GetFinalPathNameByHandleW` flags/buffer size, canonical-path
AS-IS/`-ceq` policy, package/version/bin binding, dual SHA-256 rule, 25-field snapshot schema, S0/S1
plan, later Mode-B PRE/POST contract, `HARNESS_INVALID` as pre-semantic/no-ETB-result, no-shopping,
configuration timing and status preservation.  Those parts are **preserved unchanged**.  This revision
tightens **only** the blocked machinery: P1-A P/Invoke implementation machinery (§17), P1-B atomic
evidence publication (§21, §23, §24), P1-C manifest construction/verification (§22), P2-A per-class
failure classification (§18), P2-B timestamp serialization and JSON writer/nested deterministic schema
(§19, §20).

## 1. Authoritative inputs (immutable external inputs)

| Input | Frozen value |
| --- | --- |
| owner-selected mode | **MODE P — PRE-EXISTING TARGET** |
| owner-selected endpoint policy | **CLASS A — OWNER-SUPPLIED FIXED ENDPOINT** |
| scheme | `http` |
| address family | **IPv4** |
| host | `127.0.0.1` |
| port | `4096` |
| base URI | `http://127.0.0.1:4096` |
| fallback | **NONE** |

**1.1** These values **MUST NOT** be chosen, derived, normalized into substitutes, replaced, retried or
renegotiated by the executor or by the oracle.

**1.2** Mode P means the target must be **pre-existing**: the oracle does not start, restart or create an
OpenCode server and does not assert that a listener currently exists.  It verifies **only** the frozen
endpoint — never a discovered one.

## 2. Authoritative target identity

| Item | Frozen value |
| --- | --- |
| package | `opencode-ai` |
| version | `1.18.11` |
| expected executable | `C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe` |
| expected package root | `C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai` |
| expected package manifest | `C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\package.json` |
| expected SHA-256 | `578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35` |

**2.1** No alternate binary, no alternate installation, no PATH lookup, no npm query, no retargeting.

## 3. Accepted ETB semantics implemented

The oracle implements the accepted binding chain — authoritative endpoint tuple → exact listener →
unique owning PID → canonical executable path → executable SHA-256 → exact OpenCode version → process
creation identity — and defines the target-continuity contract a later Mode-B SIC oracle must consume
(§16).  The oracle performs **NO HTTP**, defines **no HTTP request set**, adds **no liveness HTTP probe**
and reads neither `/doc` nor `/session`.  The S0/S1 check demonstrates stable observable binding only; it
does not claim HTTP-request continuity.

## 4. Accepted capability state (preserved; not reopened)

`U1 = U1_NOT_ESTABLISHED`; `U2 = U2_ESTABLISHED`; `U3 = U3_ESTABLISHED`;
`MODE L = MODE_L_MECHANISM_NOT_YET_FREEZABLE`; `MODE P = MODE_P_MECHANISM_FREEZABLE`;
`MODE P = SELECTED BY HUMAN OWNER`.

## 5. Configuration verification (CONFIG_EXACTNESS_SOUND — preserved)

**5.1 Frozen read path (production loader; identified by static inspection; not executed in this design
round):** source file `src/devrelay/config.py`; symbol module-level function
`load_wiring_config(root_or_path: str | Path) -> WiringConfig`; returned field `WiringConfig.opencode` →
`OpenCodeConfig.base_url` (normalized by a `field_validator` with `rstrip("/")`); auxiliary predicate
`OpenCodeConfig.configured`; production call sites `src/devrelay/cli.py` (`load_wiring_config(root /
".devrelay" / "config.yaml")`), `src/devrelay/cli.py`, `src/devrelay/mcp/server.py`
(`load_wiring_config(root)`).  *(Line numbers previously cited are informational only; see §29.)*

**5.2 Qualifying properties (verified statically):** read-only (the load path performs no write, create,
unlink or directory operation); deterministic (UTF-8 decode + `yaml.safe_load`; no environment variable
participates in `base_url` resolution); reusable without configuration mutation.

**5.3 Frozen invocation shape** (repository root `<repo>`):

```
PYTHONPATH=<repo>/src python -c "import sys; from devrelay.config import load_wiring_config; sys.stdout.write(load_wiring_config(sys.argv[1]).opencode.base_url)" "<repo>"
```

**5.4 Frozen semantics:** if the argument is a directory the loader reads `<dir>/.devrelay/config.yaml`;
if that path is not a file it returns defaults (so the read value is `""`); otherwise it parses the file
and returns the validator-normalized `base_url`.  The oracle compares the **returned field**, never raw
file bytes.  **No raw-YAML parser is added to ETB.**

**5.5 Required configured value:** the returned `base_url` must satisfy `-ceq 'http://127.0.0.1:4096'`
(exact, case-sensitive).  Any other value — including `""`, a surviving trailing-slash variant,
`localhost`, `::1`, another port or another scheme — is a config mismatch.

**5.6 Configuration-establishment fidelity requirement (recorded for the future, separately authorized
stage):** that stage MUST write the **exact owner literal** `http://127.0.0.1:4096` **with no trailing
slash**, so that the production-resolved value equals the frozen tuple.  This design round writes
nothing.

**5.7 Python invocation failure mapping:** `python` command not resolvable/launchable; non-zero
interpreter failure before the loader returns; `devrelay.config` import failure; dependency/import/runtime
failure → **`HARNESS_INVALID`**.  A successfully returned production loader value continues under §5.5.
**No alternate interpreter retry, no `py` launcher fallback, no PATH search** beyond the single
precommitted `python` invocation.

## 6. Exact listener query and cardinality rule

```powershell
$listenerRows = @(
    Get-NetTCPConnection `
        -LocalAddress '127.0.0.1' `
        -LocalPort 4096 `
        -State Listen
)
```

**6.1** No wildcard, no `localhost`, no `0.0.0.0`, no `::1`, no listener enumeration outside this query.

**6.2** `$listenerRows.Count -eq 1` is required; the sole row must satisfy `LocalAddress -ceq
'127.0.0.1'`, `LocalPort -eq 4096`, `State -eq 'Listen'`, and `OwningProcess` must exist and be a
positive integer compatible with a UInt32 PID.

**6.3** Any command failure, 0 or >1 rows, field mismatch, missing or ambiguous PID →
`ETB_UNSATISFIED`; no scan for another listener.

## 7. Exact PID-scoped process query

```powershell
$processRows = @(
    Get-CimInstance `
        -Namespace root/cimv2 `
        -ClassName Win32_Process `
        -Filter ("ProcessId = {0}" -f $owningPid)
)
```

**7.1** `$processRows.Count -eq 1` is required; the sole row must expose `ProcessId`, `ExecutablePath`
and `CreationDate`, with `ProcessId -eq $owningPid`, `ExecutablePath` non-null/non-empty/whitespace, and
`CreationDate` readable.

**7.2** Zero or multiple rows, a missing required property, or any failed assertion → `ETB_UNSATISFIED`.
No process enumeration.

## 8. Process-creation identity rule

**8.1** Identity = **PID + `CreationDate`**.

**8.2** Evidence capture: `creation_date_iso = CreationDate.ToString("o", InvariantCulture)`;
`creation_date_ticks = CreationDate.Ticks`.

**8.3** Equality = **PID exact equality AND `CreationDate.Ticks` exact equality**.  The `.Ticks` /
round-trip-format pair is a serialization/equality mechanism for the CIM `datetime` value, not a new
platform-capability claim.

**8.4** Accepted residual (recorded, not hidden): a **sub-resolution `CreationDate` collision is not
mathematically excluded**; no mathematical global uniqueness is claimed.  The semantic claim is only
that exact equality means no replacement was **observed** through the accepted discriminator.

**8.5** Missing, unreadable, non-`DateTime` or ambiguous `CreationDate` (including unavailable `Ticks`)
→ `ETB_UNSATISFIED`.

## 9. `CreateFileW` parameter values (preserved)

| Parameter | Frozen value |
| --- | --- |
| `dwDesiredAccess` | `GENERIC_READ` = `0x80000000` |
| `dwShareMode` | `FILE_SHARE_READ \| FILE_SHARE_WRITE \| FILE_SHARE_DELETE` = `0x00000007` |
| `lpSecurityAttributes` | `NULL` |
| `dwCreationDisposition` | `OPEN_EXISTING` = `3` |
| `dwFlagsAndAttributes` | `FILE_ATTRIBUTE_NORMAL` = `0x00000080` |
| `hTemplateFile` | `NULL` |

**9.1** The **same** helper procedure is applied to (A) the process-reported `ExecutablePath` and (B) the
accepted target executable literal of §2.  **No alternate path routine.**

## 10. `GetFinalPathNameByHandleW` flags and buffer (preserved)

**10.1** Flags: `FILE_NAME_NORMALIZED` + `VOLUME_NAME_DOS`, numeric `dwFlags` = **`0`**; fixed buffer size
= **32768 characters**; return value `0` **or** `>= 32768` → `ETB_UNSATISFIED` (no larger-buffer retry);
`CloseHandle` always called on a successfully opened handle on a `finally`-equivalent path.

## 11. Canonical path text rules and comparison (preserved)

**11.1** The path returned by `GetFinalPathNameByHandleW` is used **AS-IS**: `\\?\` retained (not
stripped); no slash-direction conversion; no drive-letter case change; no case folding; no normalization
beyond the API.

**11.2** Comparison = PowerShell case-sensitive exact string equality **`-ceq`** between the observed
process canonical final path and the accepted target canonical final path.  Inequality →
`ETB_UNSATISFIED` (safe false-negative preferred over permissive equivalence).

## 12. Executable hash rule (preserved)

**12.1** `Get-FileHash -Algorithm SHA256 -LiteralPath <path>` is applied to **both** the
process-reported `ExecutablePath` and the accepted target literal; **each must independently equal**
`578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35`.  Hexadecimal letter case is the
only permitted normalization (`-ieq` on the 64-hex digests).  No alternate algorithm or file.

## 13. Exact version verification (preserved)

**13.1** No binary invocation.  Version is verified **only** through the exact frozen `package.json`
(§2), parsed as JSON deterministically, requiring `name -ceq 'opencode-ai'`, `version -ceq '1.18.11'`,
and a `bin.opencode` that resolves under the accepted package root to the accepted executable, where the
resolved path is canonicalized by the **same** §9–§11 procedure and compared with `-ceq` against the
accepted target's canonical final path.  No alternate manifest, package search, PATH lookup or npm query.

## 14. Snapshot schema (25 fields, exact order — preserved)

```
mode
endpoint_scheme
endpoint_address_family
endpoint_host
endpoint_port
endpoint_base_uri
configured_base_url
listener_local_address
listener_local_port
listener_state
listener_owning_pid
process_pid
process_creation_date_iso
process_creation_date_ticks
process_executable_path_raw
process_executable_path_canonical
accepted_target_path_raw
accepted_target_path_canonical
observed_executable_sha256
accepted_target_sha256
package_name
package_version
package_bin_opencode
expected_sha256
expected_version
```

**14.1** A snapshot is **valid** only if every §5–§13 rule passed for it.  No user, session, prompt,
message, provider or model content is captured.

## 15. ETB execution plan — S0 / S1 (preserved)

**15.1** S0 = one full validated snapshot; S1 = a second full validated snapshot immediately afterward
with **no HTTP and no semantic OpenCode request** between them; both must independently satisfy every
frozen identity rule.

**15.2** **S0 == S1** is required on: endpoint tuple; `configured_base_url`; listener address; listener
port; listener state; owning PID; process PID; `CreationDate.Ticks`; raw `ExecutablePath`; canonical
process path; canonical accepted-target path; observed hash; accepted-target hash; package name; package
version; package bin mapping.  Any mismatch → `ETB_UNSATISFIED`.

## 16. Later Mode-B PRE/POST continuity contract (preserved; contract only)

Before **each** future Mode-B HTTP request a PRE snapshot is taken, and after it a POST snapshot, both by
the identical §14 procedure; each must independently satisfy the ETB identity requirements and be fully
equal on every §15.2 field.  Any mismatch, or any unavailable required identity evidence, means the HTTP
evidence **must NOT be interpreted semantically**.  This artifact assigns no SIC outcome, designs no
Mode-B request set and executes no HTTP.

## 17. Native P/Invoke machinery (P1-A — frozen)

**17.1 Exact type name:** `DevRelayEtbNativeV1`.

**17.2 Exact C# source text** — the complete ready-to-use `Add-Type` source, frozen verbatim:

```csharp
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class DevRelayEtbNativeV1
{
    [DllImport(
        "kernel32.dll",
        EntryPoint = "CreateFileW",
        CharSet = CharSet.Unicode,
        ExactSpelling = true,
        SetLastError = true)]
    public static extern IntPtr CreateFileW(
        [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
        UInt32 dwDesiredAccess,
        UInt32 dwShareMode,
        IntPtr lpSecurityAttributes,
        UInt32 dwCreationDisposition,
        UInt32 dwFlagsAndAttributes,
        IntPtr hTemplateFile);

    [DllImport(
        "kernel32.dll",
        EntryPoint = "GetFinalPathNameByHandleW",
        CharSet = CharSet.Unicode,
        ExactSpelling = true,
        SetLastError = true)]
    public static extern UInt32 GetFinalPathNameByHandleW(
        IntPtr hFile,
        [Out] StringBuilder lpszFilePath,
        UInt32 cchFilePath,
        UInt32 dwFlags);

    [DllImport(
        "kernel32.dll",
        EntryPoint = "CloseHandle",
        ExactSpelling = true,
        SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool CloseHandle(
        IntPtr hObject);
}
```

**17.3 Exact invocation shape** (equivalent to):

```powershell
Add-Type `
  -TypeDefinition $nativeSource `
  -Language CSharp `
  -ErrorAction Stop
```

**17.4** No future executor may write, alter, extend or choose a different P/Invoke declaration, type
name, entry point, marshaling attribute or parameter list.

**17.5 Handle policy:** handle representation = `System.IntPtr`; `INVALID_HANDLE_VALUE =
[System.IntPtr](-1)`.  `CreateFileW` returning `INVALID_HANDLE_VALUE` → **`ETB_UNSATISFIED`**.  A
managed/P-Invoke invocation exception caused by type load, entry-point resolution, marshaling or
signature mismatch → **`HARNESS_INVALID` / NO ETB SEMANTIC RESULT**.  `CloseHandle` is always called on
every successfully opened handle in a `finally`-equivalent block; a `CloseHandle` return of `false`
after an otherwise successful native call → **`HARNESS_INVALID`** (cleanup cannot be trusted).  **No
retry.**

**17.6 Buffer and read-out:** buffer type = `System.Text.StringBuilder`; capacity = 32768 characters;
exact construction `$buffer = [System.Text.StringBuilder]::new(32768)`; call
`[DevRelayEtbNativeV1]::GetFinalPathNameByHandleW($handle, $buffer, [uint32]32768, [uint32]0)`; let the
UInt32 return be `$length`.  If `$length -eq 0` or `$length -ge 32768` → `ETB_UNSATISFIED`.  Otherwise
extract **exactly** `$resolved = $buffer.ToString(0, [int]$length)`.  **No** NUL-terminated unbounded
read, **no** buffer resize, **no** retry.  The already-frozen AS-IS canonical-path rule (§11) then
applies.

**17.7 Frozen helper procedure** (applied identically to both paths of §9.1): open with the §9 parameters
→ on `INVALID_HANDLE_VALUE` fail as §17.5 → `GetFinalPathNameByHandleW` per §10/§17.6 → capture
`$buffer.ToString(0, [int]$length)` → `CloseHandle` in a `finally`-equivalent block (failure →
`HARNESS_INVALID`).

## 18. Failure taxonomy (P2-A — frozen)

**18.1 General rule.**  `ETB_UNSATISFIED` = a target / environment / required-target-evidence condition
failed.  `HARNESS_INVALID` = the oracle implementation or evidence machinery itself cannot be trusted.
An unexpected exception **not** explicitly classified below is `HARNESS_INVALID` with **NO ETB SEMANTIC
RESULT**, **NO RETRY**, **STOP**.  **No executor judgment is permitted.**

**18.2 Deterministic failure-mapping table (exact):**

| Class | Condition | Classification |
| --- | --- | --- |
| CONFIG READER | `python` cannot be resolved/launched | `HARNESS_INVALID` |
| CONFIG READER | repository `devrelay.config` import failure | `HARNESS_INVALID` |
| CONFIG READER | dependency/import/runtime failure before the production loader executes | `HARNESS_INVALID` |
| CONFIG READER | loader returns normally but config is absent/default-empty | `ETB_UNSATISFIED` |
| CONFIG READER | production `ConfigError` / invalid configured endpoint | `ETB_UNSATISFIED` |
| CONFIG READER | resolved `base_url` ≠ frozen owner URI | `ETB_UNSATISFIED` |
| POWERSHELL | `Get-NetTCPConnection` command/module unavailable | `HARNESS_INVALID` |
| POWERSHELL | `Get-CimInstance` command unavailable | `HARNESS_INVALID` |
| POWERSHELL | `Get-FileHash` command unavailable | `HARNESS_INVALID` |
| POWERSHELL | `Add-Type` command unavailable | `HARNESS_INVALID` |
| POWERSHELL | `ConvertTo-Json` command unavailable | `HARNESS_INVALID` |
| POWERSHELL | `ConvertFrom-Json` unavailable when required for read-back verification | `HARNESS_INVALID` |
| LISTENER | cmdlet exists but the exact query raises an access/provider/query exception | `ETB_UNSATISFIED` |
| LISTENER | 0 rows | `ETB_UNSATISFIED` |
| LISTENER | >1 rows | `ETB_UNSATISFIED` |
| LISTENER | field/PID validation failure | `ETB_UNSATISFIED` |
| PROCESS | cmdlet exists but the exact PID-scoped query raises an access/provider/query exception | `ETB_UNSATISFIED` |
| PROCESS | 0 rows | `ETB_UNSATISFIED` |
| PROCESS | >1 rows | `ETB_UNSATISFIED` |
| PROCESS | required `ProcessId`/`ExecutablePath`/`CreationDate` unavailable | `ETB_UNSATISFIED` |
| ADD-TYPE | source compilation / type-load failure | `HARNESS_INVALID` |
| ADD-TYPE | native entry-point/marshaling/signature invocation exception | `HARNESS_INVALID` |
| ADD-TYPE | `CreateFileW` returns `INVALID_HANDLE_VALUE` | `ETB_UNSATISFIED` |
| ADD-TYPE | `GetFinalPathNameByHandleW` returns `0` or `>= 32768` | `ETB_UNSATISFIED` |
| ADD-TYPE | `CloseHandle` returns `false` | `HARNESS_INVALID` |
| HASHING | `Get-FileHash` exists but the target file cannot be read | `ETB_UNSATISFIED` |
| HASHING | hash mismatch | `ETB_UNSATISFIED` |
| PACKAGE | fixed `package.json` missing/unreadable | `ETB_UNSATISFIED` |
| PACKAGE | malformed JSON | `ETB_UNSATISFIED` |
| PACKAGE | name/version/bin mismatch | `ETB_UNSATISFIED` |
| EVIDENCE | evidence directory cannot be created/accessed for output | `HARNESS_INVALID` |
| EVIDENCE | temporary evidence file cannot be created/written/flushed/read back | `HARNESS_INVALID` |
| EVIDENCE | JSON serialization failure | `HARNESS_INVALID` |
| EVIDENCE | JSON parse-back failure | `HARNESS_INVALID` |
| EVIDENCE | temporary manifest creation/write/read-back failure | `HARNESS_INVALID` |
| EVIDENCE | manifest mismatch | `HARNESS_INVALID` |
| EVIDENCE | temporary result creation/write/read-back failure | `HARNESS_INVALID` |
| EVIDENCE | final same-directory publication move failure | `HARNESS_INVALID` |
| EVIDENCE | post-publication byte/hash verification failure | `HARNESS_INVALID` |

**18.3** No retry or fallback for any entry.

## 19. Execution timestamps (P2-B — frozen)

**19.1** Source: `[System.DateTimeOffset]::UtcNow`.

**19.2** String representation: `yyyy-MM-dd'T'HH:mm:ss.fffffff'Z'` with
`System.Globalization.CultureInfo.InvariantCulture`.  Both `execution_started_at` and
`execution_finished_at` MUST use exactly this format and UTC.  **No local-time timestamps.**  (Any
example values elsewhere are descriptive only; the runtime value varies.)

## 20. JSON writer and nested deterministic schema (P2-B — frozen)

**20.1 Writer:** PowerShell ordered objects plus `ConvertTo-Json` with EXACT options `-Depth 12
-Compress`:

```powershell
$json = $evidence | ConvertTo-Json -Depth 12 -Compress
$jsonText = $json + "`n"
```

**20.2 Encoding:** UTF-8 **NO BOM** via `New-Object System.Text.UTF8Encoding($false)`.  Because
`-Compress` yields a single-line representation, internal JSON newlines = **NONE**; the final file is
**one JSON line + exactly one LF**.  **No CRLF conversion.**

**20.3 Every object is `[ordered]`.**  Top-level order is exactly: `schema_version`, `oracle_commit`,
`oracle_sha256`, `execution_started_at`, `execution_finished_at`, `mode`, `endpoint`,
`configured_base_url`, `target`, `snapshot_s0`, `snapshot_s1`, `checks`, `outcome`, `non_claims`,
`activity_counters`.

**20.4 `endpoint` order:** `scheme`, `address_family`, `host`, `port`, `base_uri`, `fallback`.

**20.5 `target` order:** `package_name`, `expected_version`, `expected_executable`, `expected_sha256`,
`package_root`, `package_manifest`.

**20.6 Snapshot order:** exactly the 25-field order of §14.

**20.7 `checks` order (18 keys):** `config_exact`, `listener_unique`, `listener_fields`,
`process_unique`, `process_fields`, `creation_identity`, `process_path_canonicalized`,
`target_path_canonicalized`, `canonical_path_equal`, `observed_hash_equal`, `target_hash_equal`,
`package_name_equal`, `package_version_equal`, `package_bin_equal`, `s0_valid`, `s1_valid`,
`s0_s1_equal`, `no_shopping`.  Each value MUST be exactly one of `PASS`, `FAIL`, `NOT_REACHED`; no
free-text replacement.

**20.8 `non_claims` ordered string array:** `not_sic_result`, `not_p6_result`, `not_g0_5_result`,
`not_mode_b_result`, `not_case_c_authorization`, `not_adoption_authorization`.

**20.9 `activity_counters` order (14 keys):** `web_network`, `endpoint_discovery`, `port_scan`,
`listener_scan`, `process_scan`, `opencode_start`, `http`, `doc`, `session`, `provider_model`,
`sic_attempts`, `mode_b_oracle_work`, `g0_5`, `g1_g2`.  All values are non-negative integers; for a
compliant attempt all are **`0`** (and `no_shopping` may be `PASS` only when they are all `0`).

**20.10 Frozen value vocabulary (removes remaining executor choice):** `schema_version` =
`"devrelay-etb-v1"`; `mode` = `"MODE_P"` (top-level and inside each snapshot); `endpoint.scheme` =
`"http"`; `endpoint.address_family` = `"IPv4"`; `endpoint.host` = `"127.0.0.1"`; `endpoint.port` =
`4096` (integer); `endpoint.base_uri` = `"http://127.0.0.1:4096"`; `endpoint.fallback` = `"NONE"`;
`listener_state` = `"Listen"`; `listener_local_address` = `"127.0.0.1"`; `listener_local_port` = `4096`;
`package_name` = `"opencode-ai"`; `package_version` = `"1.18.11"`; `package_bin_opencode` =
`"./bin/opencode.exe"` (the declared value as read); `expected_version` = `"1.18.11"`;
`expected_sha256` = the §2 digest; all SHA-256 values in evidence are **64 lowercase hex characters**;
`process_creation_date_ticks` and all PIDs/ports are integers; all path values are strings.

**20.11 `outcome` field** is one of `ETB_SATISFIED`, `ETB_UNSATISFIED`, `HARNESS_INVALID`.  If
`HARNESS_INVALID`, the semantic interpretation is always **NO ETB SEMANTIC RESULT EXISTS**.

## 21. Evidence output paths, preexistence rule and temp write primitive (P1-B — frozen)

**21.1 Frozen directory:** `docs/v0.3/evidence/etb-execution`.  A future execution MAY create it as
evidence output; directory-creation failure → `HARNESS_INVALID`.  **This design round does not create
it.**

**21.2 Frozen final paths:**

| Purpose | Final path |
| --- | --- |
| evidence | `docs/v0.3/evidence/etb-execution/ETB_EVIDENCE.json` |
| manifest | `docs/v0.3/evidence/etb-execution/MANIFEST.sha256` |
| result | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT.md` |

**21.3 Frozen temp paths (exactly):**

```
docs/v0.3/evidence/etb-execution/ETB_EVIDENCE.json.tmp
docs/v0.3/evidence/etb-execution/MANIFEST.sha256.tmp
docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT.md.tmp
```

Each temp is in the **same directory** as its corresponding final.

**21.4 Preexistence rule:** before any evidence publication attempt, **all six** paths (3 final + 3 temp)
MUST NOT EXIST.  If **any** exists → `HARNESS_INVALID`, **NO DELETE, NO OVERWRITE, NO CLEANUP, NO
RETRY, STOP**.  This is one authorized attempt only.

**21.5 Temp write primitive (frozen for every temp file):** encode the complete intended content to bytes
first using `UTF8Encoding(false)`; open a `System.IO.FileStream` with `FileMode.CreateNew`,
`FileAccess.Write`, `FileShare.None`; write all bytes; call `Flush(true)`; dispose/close; then
`ReadAllBytes(temp)` and require **byte-for-byte equality** with the intended byte array.  Any failure →
`HARNESS_INVALID`.  **Do not publish directly to a final path with `WriteAllText`.**

**21.6 Evidence temp verification:** after writing `ETB_EVIDENCE.json.tmp`, verify (i) read-back bytes
equal intended bytes; (ii) the file ends in exactly one LF; (iii) the byte before that final LF is
neither LF nor CR; (iv) no BOM; (v) `ConvertFrom-Json` parses the UTF-8 text; (vi) parsed
`schema_version -ceq 'devrelay-etb-v1'`; (vii) parsed `outcome` equals the in-memory outcome.  Any failure
→ `HARNESS_INVALID`.

## 22. Manifest construction and verification (P1-C — frozen)

**22.1 Coverage (exactly one file):** `docs/v0.3/evidence/etb-execution/ETB_EVIDENCE.json`.  The manifest
does **not** include itself and does **not** include the Markdown result artifact.  The result artifact
separately records `evidence_sha256` and `manifest_sha256`.

**22.2 Format:** SHA-256; digest = **64 lowercase hexadecimal characters**; **exactly 1 line**; line
format EXACTLY:

```
<64-lowercase-sha256><two ASCII spaces>docs/v0.3/evidence/etb-execution/ETB_EVIDENCE.json<LF>
```

No header, no comments, UTF-8, **NO BOM**, LF only, **exactly one final LF**.

**22.3 Hash construction:** compute SHA-256 over the **exact bytes intended for**
`ETB_EVIDENCE.json` **before** final publication; the resulting lowercase digest is used in the one
manifest line.  After writing `MANIFEST.sha256.tmp`: read back bytes, require exact byte equality with
the intended manifest bytes, parse the single line, and require the digest exact, the two spaces exact,
and the repository-relative path exact.  Any failure → `HARNESS_INVALID`.

**22.4 In-memory hashing mechanism (frozen):** `System.Security.Cryptography.SHA256.Create()` →
`ComputeHash(byte[])` → lowercase hexadecimal.  This is **evidence-machinery hashing only**; it does not
change the accepted target-executable hash rule, which remains `Get-FileHash` (§12).  If
`SHA256.Create`/`ComputeHash` fails → `HARNESS_INVALID`.

## 23. Result artifact, result temp and construction order (P1-B — frozen)

**23.1 Result template** — UTF-8/no-BOM/LF with one final LF, containing at minimum these exact labeled
fields in this order:

```
DEVRELAY v0.3-E ETB EXECUTION RESULT — CANDIDATE

Status:
CANDIDATE ETB RESULT / AWAITING INDEPENDENT RESULT REVIEW

Outcome:
<ETB_SATISFIED | ETB_UNSATISFIED | HARNESS_INVALID / NO ETB SEMANTIC RESULT>

Oracle commit:
<oracle_commit>

Oracle SHA-256:
<oracle_sha256>

Evidence SHA-256:
<evidence_sha256>

Manifest SHA-256:
<manifest_sha256>

Execution started UTC:
<execution_started_at>

Execution finished UTC:
<execution_finished_at>

Non-claims:
NOT SIC
NOT P6
NOT G0.5
NOT MODE-B RESULT
NOT CASE-C AUTHORIZATION
NOT ADOPTION AUTHORIZATION

No result artifact is authoritative before independent review.
```

**23.2 Result temp:** construct the complete Markdown result bytes in memory and write **only** to
`V03E_G0_5_PRE_ETB_EXECUTION_RESULT.md.tmp` using the identical §21.5 procedure
(`CreateNew`/write/`Flush(true)`/close/`ReadAllBytes`/exact-byte-equality).  Any failure →
`HARNESS_INVALID`.

**23.3 Manifest SHA:** after successful read-back verification, compute SHA-256 of the **exact bytes** of
`MANIFEST.sha256.tmp`; that lowercase digest becomes `manifest_sha256` inside the result artifact.

**23.4 Construction order (no circular hash dependency):** evidence bytes → evidence temp → evidence
verification → manifest bytes → manifest temp → manifest verification → manifest SHA → result bytes →
result temp → result verification.

## 24. Publication, post-publication verification and partial output (P1-B — frozen)

**24.1 Publication primitive:** `System.IO.File.Move(temp, final)` with **no overwrite**.  Publication
occurs **only after all three temp files are successfully written and verified**.  Final publication
order EXACTLY: (1) `ETB_EVIDENCE.json.tmp` → `ETB_EVIDENCE.json`; (2) `MANIFEST.sha256.tmp` →
`MANIFEST.sha256`; (3) `V03E_G0_5_PRE_ETB_EXECUTION_RESULT.md.tmp` →
`V03E_G0_5_PRE_ETB_EXECUTION_RESULT.md` — **the result artifact is published LAST**.  No
`File.Replace`, no overwrite, no alternate filename, no cleanup, no retry.  Any `Move` failure →
`HARNESS_INVALID`.

**24.2 Post-publication verification:** after **each** successful `Move`, `ReadAllBytes(final)` and
verify SHA-256 / byte identity against the already verified temp content.  After all three `Move`s,
verify again: `ETB_EVIDENCE.json` parses; its `outcome` matches the in-memory attempt state; the manifest
line digest matches the **final** evidence bytes; the manifest path matches the exact repository-relative
evidence path; and the result artifact's oracle SHA, evidence SHA, manifest SHA, outcome and timestamps
match the final evidence set.  Any failure → `HARNESS_INVALID / NO ETB SEMANTIC RESULT`.  **No retry.**

**24.3 Partial-publication rule:** if publication fails at any step → `HARNESS_INVALID` / NO ETB SEMANTIC
RESULT.  Do **not** delete temps or already-published finals; leave them for forensic review.  Any
partial output set is explicitly **NON-AUTHORITATIVE** and **INVALID AS AN ETB RESULT**, and MUST NOT be
used by Mode-B construction.  The existence of `ETB_EVIDENCE.json` or `MANIFEST.sha256` without the
successfully verified complete final set **never** means an ETB result exists.  The Markdown result is
published last specifically to reduce accidental interpretation of a partial set; even if the Markdown
result exists but final post-publication verification fails → `HARNESS_INVALID / NO ETB SEMANTIC RESULT`.

**24.4 Serializer/publication failure before output:** if the oracle cannot serialize trustworthy
evidence bytes at all (`ConvertTo-Json` unavailable/failure, UTF-8 encoding failure, in-memory evidence
construction failure) → `HARNESS_INVALID / NO ETB SEMANTIC RESULT`, and **no output file is required or
trusted**.  An executor run report may state `HARNESS_INVALID`, but that report is **not** an ETB
semantic result.

**24.5 Outcome vs publication failure:** a target/environment evaluation may first determine
`ETB_SATISFIED` or `ETB_UNSATISFIED`; but if subsequent mandatory evidence/publication machinery fails,
the **final** attempt classification becomes `HARNESS_INVALID / NO ETB SEMANTIC RESULT`.  **A provisional
semantic state MUST NOT survive an evidence-integrity failure.**

## 25. Outcome taxonomy (preserved)

**25.1 `ETB_SATISFIED`** requires: authoritative config exactly equal to the owner tuple; S0 fully valid;
S1 fully valid; S0 == S1 under §15.2; all path/hash/version/process-identity requirements satisfied; no
endpoint shopping, no mode switching, no fallback; **and** the complete evidence/publication machinery of
§21–§24 succeeded and verified.

**25.2 `ETB_UNSATISFIED`** covers the target/environment/required-evidence failures enumerated in §18.2
(config mismatch or missing; endpoint malformed; listener missing / count ≠ 1 / field mismatch;
`OwningProcess` missing or invalid; process count ≠ 1; `ExecutablePath` unavailable; `CreationDate`
unavailable; `CreateFileW` failure; `GetFinalPathNameByHandleW` failure; canonical-path mismatch; hash
failure/mismatch; package manifest missing/malformed/mismatch; version mismatch; S0/S1 identity mismatch;
any accepted fail-closed ETB condition).  It is **ONLY** a prerequisite/control result — **NOT** SIC
FAIL, **NOT** P6 FAIL, **NOT** G0.5 FAIL, **NOT** "OpenCode cannot support Mode B".

**25.3 `HARNESS_INVALID`** is reserved only for inability to trust the oracle machinery itself, per
§18.2; it means **NO ETB SEMANTIC RESULT EXISTS**, must not be reinterpreted as `ETB_UNSATISFIED`, and
carries **no retry or repair** within the same authorized attempt — stop and require separate
review/re-authorization.

## 26. `ETB_SATISFIED` non-claims (preserved)

Even `ETB_SATISFIED` means **only** that the exact configured endpoint is deterministically bound to the
accepted OpenCode target under this frozen oracle, and that the later Mode-B oracle may resume
**construction** after independent ETB result acceptance.  It does **not** establish SIC semantics, P6,
G0.5, session incarnation, turn provenance, message provenance, pending-handle semantics, Mode-B PASS,
Case-C authorization or `adopt_completed_turn`.

## 27. No-endpoint-shopping / no-fallback rules (preserved)

One endpoint, one mode, one authorized attempt.  Forbidden: alternate port; alternate host; `localhost`;
`::1`; `0.0.0.0`; alternate address family; alternate OpenCode installation; alternate executable; PATH
search; port scan; listener scan; process scan; log-derived endpoint; retry after failure; Mode P → Mode
L switch.

## 28. Deterministic execution order (frozen; no runtime choice)

1. verify oracle artifact identity (`oracle_commit`, `oracle_sha256`) against the accepted oracle — mismatch → `HARNESS_INVALID`;
2. read the authoritative config through §5 and require exact equality with the frozen tuple (§5.5) — otherwise classify per §18.2;
3. take **S0** (§14) by running §6 → §7 → §8 → §9+§17 → §10/§17.6 → §11 → §12 → §13 in order, failing closed on the first violation with the §18.2 classification;
4. take **S1** by repeating step 3 with no HTTP or semantic OpenCode request in between;
5. require S0 == S1 under §15.2 — otherwise `ETB_UNSATISFIED`;
6. determine the provisional semantic state (`ETB_SATISFIED` / `ETB_UNSATISFIED`) — **no other value**;
7. serialize evidence per §19–§20; write the evidence temp and verify it per §21.5/§21.6; write the manifest temp and verify it per §22; compute the manifest SHA (§23.3); write the result temp and verify it per §23.2;
8. publish the three files in the exact order of §24.1 and run the §24.2 post-publication verification — any failure converts the final classification to `HARNESS_INVALID / NO ETB SEMANTIC RESULT` per §24.5;
9. stop.  No retry, no repair, no cleanup, no alternate endpoint, no mode switch.

## 29. Static anchor hygiene

Previously cited line numbers (`config.py:576`, `cli.py:182`, `cli.py:388`, `mcp/server.py:117`) are
**informational only**.  The frozen authority is the **module path, symbol/function/class names and the
semantic call path** — never static line numbers.  Line numbers must not be execution predicates.

## 30. Activity counters for this design round and non-claims

**30.1** This remediation round performed: web/network `0`; live endpoint queries `0`;
`Get-NetTCPConnection` executions `0`; live `Get-CimInstance` `0`; listener/process/port enumeration `0`;
config mutation `0`; OpenCode starts `0`; HTTP `0`; `/doc` `0`; `/session` `0`; `Add-Type` execution `0`;
P/Invoke execution `0`; evidence publication `0`; ETB execution `0`; SIC `0`; Mode-B oracle work `0`;
provider/model `0`; G0.5 `0`; G1/G2 `0`; runtime/test/dependency/version changes `0`.  Static repository
inspection does not count as ETB execution.

**30.2 Non-claims.**  This candidate oracle does not establish an endpoint, does not assert that
`127.0.0.1:4096` is listening, does not assert that OpenCode is running or owns any listener, does not
modify configuration, does not start OpenCode, does not perform HTTP, does not compile a native type,
does not publish evidence, does not authorize ETB execution, and produces no `ETB_SATISFIED` /
`ETB_UNSATISFIED` / `HARNESS_INVALID` result.  Preserved unchanged: `ETB = DEFINITION ACCEPTED / NOT
EXECUTED`; `ETB EXECUTION / ORACLE = CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED / NOT EXECUTED`; Mode-B =
`NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE
CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`; `G0.5 / P6 = NOT RUN / DEFINITION ACCEPTED / ORACLE
NOT FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED` and G0.5 **NOT CLOSED**;
`G1`/`G2` `NOT RUN`; Case-C and v0.3-E implementation `NOT AUTHORIZED`; `adopt_completed_turn`
**DISABLED**.

**End of ETB execution-oracle candidate, round-2 remediation revision (Mode P, Class-A fixed endpoint).**
