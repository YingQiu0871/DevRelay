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

Baseline: `b3be79d4f6bbe9975385aff30e091abe89b032c2` (branch `v0.3-e-recovery-reconciliation`).

This artifact is a **design**.  It freezes every semantic rule a later authorized ETB attempt must
apply, so that the executor chooses **no** semantic rule at runtime.  It establishes no endpoint,
modifies no configuration, starts nothing, issues no HTTP, and executes no ETB.

Anchors (committed Git blobs):

| Anchor | Identity |
| --- | --- |
| accepted ETB definition | `docs/v0.3/V03E_G0_5_PRE_MODE_B_ENDPOINT_BINDING.md`, blob `99cc6dcee4ab1a3f0589c3e7d11308d089601ba07d16cc2d37a9fc32c777b3a0` |
| accepted owner-decision record | `docs/v0.3/V03E_G0_5_PRE_ETB_OWNER_ORACLE_PARAMETERS.md`, blob `152311341b8bc8cfb93964f3709a6922a62d914c8a297dea1e3634940bb34cbe` |
| accepted Round-2 U2/U3 artifact | `docs/v0.3/V03E_G0_5_PRE_ETB_U2_U3_AUTHORITY_RESOLUTION.md`, blob `49b22a88a593ce9ce59e7da6ae5221d8300d4963cca5b9fdc2dc8c2b47a91453` |
| accepted prior U1/U2/U3 capability artifact | `docs/v0.3/V03E_G0_5_PRE_ETB_CAPABILITY_RESOLUTION.md`, blob `59e8ef575fa3ab854f65fee5e25621c51f74c8b76615d7d4d9fb1e071b4049ac` |

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

**1.1** These values **MUST NOT** be chosen, derived, normalized into substitutes, replaced, retried
or renegotiated by the executor or by the oracle.  They are consumed verbatim.

**1.2** Mode P means the target must be **pre-existing**: the oracle does **not** start, restart or
create an OpenCode server, and it does **not** assert that a listener currently exists.  It verifies
**only** the frozen endpoint — never a discovered one.

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

## 3. Accepted ETB semantics implemented by this oracle

**3.1** The oracle implements the accepted binding chain:

```
authoritative endpoint tuple
→ exact listener
→ unique owning PID
→ canonical executable path
→ executable SHA-256
→ exact OpenCode version
→ process creation identity
```

**3.2** The oracle performs **NO HTTP**.  It defines **no HTTP request set**, adds **no liveness HTTP
probe**, and reads neither `/doc` nor `/session`.  The two-snapshot check (§15) demonstrates stable
observable binding only; it does **not** claim HTTP-request continuity.

**3.3** The oracle defines the target-continuity contract that a later Mode-B SIC oracle must consume
(§16) and nothing else about Mode-B.

## 4. Accepted capability state (preserved; not reopened)

`U1 = U1_NOT_ESTABLISHED`; `U2 = U2_ESTABLISHED`; `U3 = U3_ESTABLISHED`;
`MODE L = MODE_L_MECHANISM_NOT_YET_FREEZABLE`; `MODE P = MODE_P_MECHANISM_FREEZABLE`;
`MODE P = SELECTED BY HUMAN OWNER`.  This design round reopens none of these findings.

## 5. Configuration verification mechanism (frozen; static finding only)

**5.1 Static finding — the existing production read path (identified by static inspection only; not
executed in this round):**

| Item | Value |
| --- | --- |
| source file | `src/devrelay/config.py` |
| symbol | module-level function `load_wiring_config(root_or_path: str \| Path) -> WiringConfig` (definition at line 576) |
| returned field | `WiringConfig.opencode` → `OpenCodeConfig.base_url` (`OpenCodeConfig` declares `base_url: str = ""`; a `field_validator` normalizes it with `rstrip("/")`) |
| auxiliary predicate | `OpenCodeConfig.configured` = `bool(self.base_url.strip())` |
| production call sites | `src/devrelay/cli.py:182` (`load_wiring_config(root / ".devrelay" / "config.yaml")`), `src/devrelay/cli.py:388`, `src/devrelay/mcp/server.py:117` (`load_wiring_config(root)`) |

**5.2 Properties that qualify it (verified statically):** *read-only* — the load path
(`load_wiring_config` → `_parse_yaml_bytes` → `_parse_yaml`) performs no write, create, unlink or
directory operation; *deterministic* — the file is decoded as UTF-8 and parsed with
`yaml.safe_load`, and no environment variable participates in `opencode.base_url` resolution;
*reusable without configuration mutation* — it takes a root/path argument and returns a validated
object.

**5.3 Frozen invocation shape** (repository root `<repo>`, workspace root `<repo>`):

```
PYTHONPATH=<repo>/src python -c "import sys; from devrelay.config import load_wiring_config; sys.stdout.write(load_wiring_config(sys.argv[1]).opencode.base_url)" "<repo>"
```

**5.4 Frozen semantics of that call:** if the argument is a directory, the loader reads
`<dir>/.devrelay/config.yaml`; if that path is not a file it returns defaults (so the read value is
`""`); otherwise it parses the file and returns the validator-normalized `base_url` (any trailing
`/` stripped).  The oracle compares the **returned field**, never the raw file bytes.

**5.5 Required configured value at execution time:** the returned `base_url` must satisfy
`-ceq 'http://127.0.0.1:4096'` (exact, case-sensitive).  Any other value — including `""`, a
trailing-slash variant that survives normalization, `localhost`, `::1`, a different port, or a
different scheme — is a config mismatch.

**5.6 Failure mapping (precommitted):**

* production loader **module cannot be imported** (e.g. `PYTHONPATH` misconfigured) → **`HARNESS_INVALID`** (machinery/setup defect, §18);
* loader raises `ConfigError` (unparseable YAML, non-UTF-8, invalid wiring) → **`ETB_UNSATISFIED`** (config condition);
* config file absent → loader returns defaults → returned value `""` → **`ETB_UNSATISFIED`** (config missing/mismatch);
* returned value ≠ frozen tuple → **`ETB_UNSATISFIED`**.

**5.7** The oracle never writes `opencode.base_url`.  Configuration establishment is a separate,
separately authorized stage (§22).

## 6. Exact listener query and cardinality rule

**6.1 Frozen query (verbatim):**

```powershell
$listenerRows = @(
    Get-NetTCPConnection `
        -LocalAddress '127.0.0.1' `
        -LocalPort 4096 `
        -State Listen
)
```

**6.2** No wildcard, no `localhost`, no `0.0.0.0`, no `::1`, and **no listener enumeration outside
this exact query**.

**6.3 Frozen cardinality rule:** `$listenerRows.Count -eq 1` is **required**.

**6.4 Frozen sole-row field verification** (all must hold):

* `LocalAddress -ceq '127.0.0.1'`;
* `LocalPort -eq 4096`;
* `State -eq 'Listen'`;
* `OwningProcess` **exists** and is a positive integer compatible with a UInt32 PID.

**6.5 Failure mapping:** any command failure, zero results, more than one result, any field mismatch,
a missing `OwningProcess`, or an ambiguous/invalid PID → **`ETB_UNSATISFIED`**.  The oracle must
**not** scan for another listener.

## 7. Exact PID-scoped process query

**7.1 Frozen query (verbatim, `$owningPid` from §6):**

```powershell
$processRows = @(
    Get-CimInstance `
        -Namespace root/cimv2 `
        -ClassName Win32_Process `
        -Filter ("ProcessId = {0}" -f $owningPid)
)
```

**7.2 Frozen cardinality rule:** `$processRows.Count -eq 1` is **required**.

**7.3 Frozen required properties of the sole row:** `ProcessId`, `ExecutablePath`, `CreationDate`.

**7.4 Frozen assertions:**

* `ProcessId -eq $owningPid` (exact equality with the listener's `OwningProcess`);
* `ExecutablePath` is neither `$null` nor empty/whitespace;
* `CreationDate` is neither `$null` nor unreadable.

**7.5 Failure mapping:** zero or multiple rows, a missing required property, or any failed assertion →
**`ETB_UNSATISFIED`**.  No process enumeration is permitted.

## 8. Process-creation identity rule

**8.1 Frozen identity:** **PID + `CreationDate`**.

**8.2 Frozen capture for evidence:**

```
creation_date_iso   = CreationDate.ToString("o", InvariantCulture)
creation_date_ticks = CreationDate.Ticks
```

**8.3 Frozen equality rule:** **PID exact equality AND `CreationDate.Ticks` exact equality.**  The
`.Ticks`/round-trip-format pair is a serialization/equality mechanism for the CIM `datetime` value,
not a new platform-capability claim.

**8.4 Accepted residual (recorded, not hidden):** a **sub-resolution `CreationDate` collision is not
mathematically excluded**; no mathematical global uniqueness is claimed.  The semantic claim is only:
exact equality means **no replacement was OBSERVED through the accepted platform discriminator**.

**8.5 Failure mapping:** missing, unreadable, non-`DateTime` or ambiguous `CreationDate` (including an
unavailable `Ticks`) → **`ETB_UNSATISFIED`**.

## 9. Executable-path canonicalization — `CreateFileW` parameters (frozen)

**9.1 One canonicalization procedure is applied identically to (A) `Win32_Process.ExecutablePath`
and (B) the accepted target executable literal of §2.**

**9.2 Frozen P/Invoke target:** `kernel32.dll`, `CreateFileW`, `SetLastError = true`,
`CharSet = CharSet.Unicode`, return type `IntPtr`.

**9.3 Frozen parameters:**

| Parameter | Frozen value |
| --- | --- |
| `dwDesiredAccess` | `GENERIC_READ` = `0x80000000` |
| `dwShareMode` | `FILE_SHARE_READ \| FILE_SHARE_WRITE \| FILE_SHARE_DELETE` = `0x00000007` |
| `lpSecurityAttributes` | `NULL` |
| `dwCreationDisposition` | `OPEN_EXISTING` = `3` |
| `dwFlagsAndAttributes` | `FILE_ATTRIBUTE_NORMAL` = `0x00000080` |
| `hTemplateFile` | `NULL` |

**9.4 Failure mapping:** any open failure (including an invalid handle value such as `-1` /
`INVALID_HANDLE_VALUE`) → **`ETB_UNSATISFIED`**.  The oracle must not attempt another open mode.

## 10. `GetFinalPathNameByHandleW` rule (frozen)

**10.1 Frozen call:** `GetFinalPathNameByHandleW(hFile, buffer, 32768, 0)` with

* `FILE_NAME_NORMALIZED` = `0x0`;
* `VOLUME_NAME_DOS` = `0x0`;
* numeric `dwFlags` = **`0`**;
* fixed `WCHAR` buffer size = **32768 characters**.

**10.2 Frozen return-value rule:** if the return value is `0` **or** `>= 32768` →
**`ETB_UNSATISFIED`** (the API's "buffer too small" case is treated as failure, never as a retry with a
larger buffer).

**10.3** `CloseHandle` is **always** called on a successfully opened handle, on a
`finally`-equivalent path, in every outcome.

**10.4** Any API failure → **`ETB_UNSATISFIED`**.

## 11. Canonical path text rules and comparison

**11.1** The canonical path returned by `GetFinalPathNameByHandleW` is used **AS-IS**:

* retain the `\\?\` prefix — do **not** strip it;
* do **not** convert slash direction;
* do **not** uppercase or lowercase the drive letter;
* do **not** case-fold;
* do **not** perform any textual normalization beyond what
  `GetFinalPathNameByHandleW(FILE_NAME_NORMALIZED, VOLUME_NAME_DOS)` already returns.

**11.2 Frozen comparison rule:** PowerShell **case-sensitive exact string equality `-ceq`** between
the observed process canonical final path and the accepted target canonical final path.

**11.3 Failure mapping:** any inequality → **`ETB_UNSATISFIED`**.  This intentionally prefers a safe
false-negative failure over permissive path equivalence.

## 12. Executable hash rule

**12.1 Frozen hashing call:** `Get-FileHash -Algorithm SHA256 -LiteralPath <path>`.

**12.2** The oracle hashes **BOTH** (A) the process-reported `ExecutablePath` and (B) the accepted
target executable literal of §2.  **Each must independently equal**
`578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35`.

**12.3 Frozen comparison:** hexadecimal letter case is the **only** permitted normalization; the
comparison is `-ieq` on the 64-hex-character digests.  No alternate algorithm, no alternate file.

**12.4 Failure mapping:** any hashing failure or mismatch → **`ETB_UNSATISFIED`**.

## 13. Exact version verification

**13.1** The oracle **does NOT** launch `opencode.exe --version` or any equivalent binary invocation.

**13.2 Frozen mechanism:** read **only** the exact manifest
`C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\package.json` and parse it as JSON
deterministically.

**13.3 Frozen assertions:**

* `name -ceq 'opencode-ai'`;
* `version -ceq '1.18.11'`;
* `bin.opencode` exists and resolves under the accepted package root (§2) to the accepted executable
  of §2, where the resolved path is canonicalized through the **same** §9–§11 procedure and compared
  with `-ceq` against the accepted target's canonical final path.

**13.4** No alternate `package.json`, no package search, no PATH lookup, no npm query.

**13.5 Failure mapping:** missing, malformed or mismatching manifest, or a bin mapping that does not
resolve to the accepted executable → **`ETB_UNSATISFIED`**.

## 14. Snapshot definition (exact fields)

**14.1** One functionally complete identity snapshot contains **exactly** these fields, in this order:

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

**14.2** A snapshot is **valid** only if every §5–§13 rule passed for it.  **No** user, session,
prompt, message, provider or model content is captured.

## 15. ETB execution plan — S0 / S1

**15.1** A future authorized ETB execution takes:

* **S0** = one full validated snapshot (§14);
* **S1** = a second full validated snapshot immediately afterward, with **no HTTP and no semantic
  OpenCode request** between them.

**15.2** Both snapshots must **independently** satisfy every frozen ETB identity rule.

**15.3 Frozen equality requirement S0 == S1** on: endpoint tuple; `configured_base_url`; listener
address; listener port; listener state; owning PID; process PID; `CreationDate.Ticks`; raw
`ExecutablePath`; canonical process path; canonical accepted-target path; observed hash;
accepted-target hash; package name; package version; package bin mapping.

**15.4 Failure mapping:** any mismatch → **`ETB_UNSATISFIED`**.

**15.5** This two-snapshot check demonstrates stable observable binding and freezes the snapshot
mechanism that later Mode-B execution must reuse.  It does **not** claim that ETB verifies HTTP-request
continuity.

## 16. Later Mode-B PRE/POST continuity contract (contract only)

**16.1** Before **each** future Mode-B HTTP request, the Mode-B oracle takes a **PRE** snapshot using
the identical frozen procedure (§14); after that request completes or fails, it takes a **POST**
snapshot using the identical procedure.

**16.2** PRE and POST must each independently satisfy the ETB identity requirements **and** be fully
equal on every identity field listed in §15.3.

**16.3** Any PRE/POST mismatch, or any unavailable required identity evidence, means the HTTP evidence
**must NOT be interpreted semantically**.

**16.4** This artifact assigns **no** SIC outcome, designs **no** Mode-B request set, and executes
**no** HTTP.

## 17. Outcome taxonomy (exactly three execution-control outcomes)

**17.1 `ETB_SATISFIED`** requires **all** of:

* authoritative config exactly equals the owner tuple (§5);
* S0 fully valid; S1 fully valid; S0 == S1 under §15.3;
* all path, hash, version and process-identity requirements satisfied;
* no endpoint shopping, no mode switching, no fallback.

**17.2 `ETB_UNSATISFIED`** covers TARGET / ENVIRONMENT / REQUIRED-EVIDENCE failures, including: config
mismatch; config missing; endpoint malformed; listener missing; listener count ≠ 1; listener field
mismatch; `OwningProcess` missing/invalid; process count ≠ 1; `ExecutablePath` unavailable;
`CreationDate` unavailable; `CreateFileW` failure; `GetFinalPathNameByHandleW` failure; canonical-path
mismatch; hash failure/mismatch; package manifest missing/malformed/mismatch; version mismatch; S0/S1
identity mismatch; and any other accepted fail-closed ETB condition.

**17.3 `ETB_UNSATISFIED` is ONLY a prerequisite/control result.**  It is **NOT** SIC FAIL, **NOT** P6
FAIL, **NOT** G0.5 FAIL, and **NOT** "OpenCode cannot support Mode B".

## 18. `HARNESS_INVALID` boundary

**18.1** `HARNESS_INVALID` is reserved **only** for inability to trust the oracle machinery itself —
never for target/environment failure.  Examples: oracle artifact/hash mismatch before execution;
oracle script/command transcription differing from this frozen oracle; an internal assertion
impossible under the frozen schema; an unexpected unclassified exception caused by an oracle
implementation defect; evidence serialization failure; an evidence file that cannot be written
atomically; post-write evidence that cannot be parsed back; an evidence manifest that cannot verify
against the bytes just written.

**18.2** `HARNESS_INVALID` means **NO ETB semantic result exists**.  It must **not** be reinterpreted
as `ETB_UNSATISFIED`, and there is **no retry or repair** within the same authorized attempt — the
attempt stops and requires separate review / re-authorization.

## 19. Evidence serialization (frozen paths and format)

**19.1 Frozen paths:**

| Purpose | Path |
| --- | --- |
| raw evidence | `docs/v0.3/evidence/etb-execution/ETB_EVIDENCE.json` |
| manifest | `docs/v0.3/evidence/etb-execution/MANIFEST.sha256` |
| result artifact | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT.md` |

**19.2** `ETB_EVIDENCE.json` carries `schema_version` = **`devrelay-etb-v1`** and the following
**ordered** top-level fields:

```
schema_version
oracle_commit
oracle_sha256
execution_started_at
execution_finished_at
mode
endpoint
configured_base_url
target
snapshot_s0
snapshot_s1
checks
outcome
non_claims
activity_counters
```

**19.3** Deterministic ordered objects only.  JSON requirements: **UTF-8, NO BOM, LF only, exactly one
final LF, no comments**, and **no** prompt/session/message/provider/model content.

**19.4** Frozen no-BOM write mechanism (PowerShell):

```powershell
[System.IO.File]::WriteAllText(
    $path,
    $json + "`n",
    (New-Object System.Text.UTF8Encoding($false))
)
```

and the serialized JSON must contain LF only.

## 20. Result-artifact semantics

**20.1** The future result artifact must be marked **CANDIDATE ETB RESULT / AWAITING INDEPENDENT
RESULT REVIEW** and must state **exactly one** of: `ETB_SATISFIED`, `ETB_UNSATISFIED`, or
`HARNESS_INVALID / NO ETB SEMANTIC RESULT`.

**20.2** No result is authoritative before independent review.

## 21. `ETB_SATISFIED` non-claims

**21.1** Even `ETB_SATISFIED` means **only** that the exact configured endpoint is deterministically
bound to the accepted OpenCode target under this frozen oracle, and that the later Mode-B oracle may
resume **construction** after independent ETB result acceptance.

**21.2** It does **not** establish SIC semantics, P6, G0.5, session incarnation, turn provenance,
message provenance, pending-handle semantics, Mode-B PASS, Case-C authorization, or
`adopt_completed_turn`.

## 22. Configuration timing

**22.1** This design round does **not** modify configuration; `opencode.base_url` remains `""`.

**22.2** The accepted sequence is unchanged and no stage may be skipped:

```
ETB ORACLE DESIGN
→ independent oracle review
→ separate execution/configuration authorization
→ set authoritative opencode.base_url to the already frozen tuple
→ ETB execution
→ independent ETB result review
→ only if ETB_SATISFIED is accepted: Mode-B SIC oracle construction may resume
```

**22.3** No configuration mutation before separate authorization.

## 23. No-endpoint-shopping / no-fallback rules

**23.1** One endpoint, one mode, one authorized attempt.

**23.2** Forbidden during execution: alternate port; alternate host; `localhost`; `::1`; `0.0.0.0`;
alternate address family; alternate OpenCode installation; alternate executable; PATH search; port
scan; listener scan; process scan; log-derived endpoint; retry after failure; Mode P → Mode L switch.

## 24. Deterministic execution order (frozen)

The future authorized attempt performs exactly these steps in this order:

1. verify the oracle artifact identity (`oracle_commit`, `oracle_sha256`) against the accepted oracle — mismatch → `HARNESS_INVALID`;
2. read the authoritative config through §5 and require exact equality with the frozen tuple — otherwise `ETB_UNSATISFIED`;
3. take **S0** (§14) by running §6 → §7 → §8 → §9 → §10 → §11 → §12 → §13 in order, failing closed on the first violation with the §17.2 classification;
4. take **S1** by repeating step 3 with no HTTP or semantic OpenCode request in between;
5. require S0 == S1 under §15.3 — otherwise `ETB_UNSATISFIED`;
6. serialize evidence per §19, write the manifest, verify the manifest against the bytes just written — serialization/manifest failure → `HARNESS_INVALID`;
7. write the result artifact per §20 with exactly one outcome token;
8. stop.  No retry, no repair, no alternate endpoint, no mode switch.

## 25. Activity counters for this design round and non-claims

**25.1** This design round performed: web/network `0`; `Get-NetTCPConnection` executions `0`; live
`Get-CimInstance` process queries `0`; listener/process/port enumeration `0`; endpoint probes `0`;
config mutations `0`; OpenCode starts `0`; HTTP `0`; `/doc` `0`; `/session` `0`; ETB executions `0`;
SIC attempts `0`; Mode-B oracle work `0`; provider/model calls `0`; G0.5 `0`; G1/G2 `0`; runtime, test,
dependency and version changes `0`.  Static repository inspection does not count as ETB execution.

**25.2 Non-claims.**  This candidate oracle does **not** establish an endpoint, does **not** assert that
`127.0.0.1:4096` is listening, does **not** assert that OpenCode is running or owns any listener, does
**not** modify configuration, does **not** start OpenCode, does **not** perform HTTP, does **not**
authorize ETB execution, and produces no `ETB_SATISFIED` / `ETB_UNSATISFIED` / `HARNESS_INVALID`
result.  Preserved unchanged: `ETB = DEFINITION ACCEPTED / NOT EXECUTED`; `ETB EXECUTION / ORACLE =
CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED / NOT EXECUTED`; Mode-B = `NOT RUN / NO ORACLE / ORACLE NOT
FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE
BLOCKER`; `G0.5 / P6 = NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP`
with `P6 = UNPROVEN / UNSATISFIED` and G0.5 **NOT CLOSED**; `G1`/`G2` `NOT RUN`; Case-C and v0.3-E
implementation `NOT AUTHORIZED`; `adopt_completed_turn` **DISABLED**.

**End of ETB execution-oracle candidate (Mode P, Class-A fixed endpoint).**
