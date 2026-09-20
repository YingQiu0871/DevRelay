# DevRelay v0.3-E — G0.5-PRE / SIC — ETB execution-oracle design support: U2 / U3 authoritative semantics resolution (round 2)

> **ETB EXECUTION-ORACLE DESIGN SUPPORT**
> **U2 / U3 AUTHORITATIVE SEMANTICS RESOLUTION**
> **ROUND-2 CANDIDATE FINDING**
> **NOT ACCEPTED**
> **NOT AN ETB EXECUTION ORACLE**
> **NOT ETB EXECUTION**
> **DOES NOT ESTABLISH AN ENDPOINT**
> **DOES NOT SELECT A PORT**
> **DOES NOT SELECT A MODE**
> **DOES NOT AUTHORIZE CONFIGURATION CHANGE**
> **DOES NOT AUTHORIZE OPENCODE START**

Status: **ROUND-2 CANDIDATE FINDING — NOT ACCEPTED** (design-support evidence only)

Baseline: `5615b300519dc141787f5bd759f3308c31ef616b` (branch `v0.3-e-recovery-reconciliation`).

This round resolves the remaining **U2** (frozen-endpoint → unique owning PID) and **U3** (known PID →
executable identity + process-instance identity + canonical executable path capability) semantic gaps
using a **closed authoritative source set** plus **local schema/metadata probes only**.  It is design
support for a future ETB execution oracle: **not** an ETB execution oracle, **not** ETB execution,
**not** Mode-B SIC oracle construction.  U1 was not worked on; its status is preserved (§8).

Anchors (committed Git blobs):

| Anchor | Identity |
| --- | --- |
| accepted ETB definition | `docs/v0.3/V03E_G0_5_PRE_MODE_B_ENDPOINT_BINDING.md`, blob `99cc6dcee4ab1a3f0589c3e7d11308d089601ba07d16cc2d37a9fc32c777b3a0` |
| accepted U1/U2/U3 capability artifact | `docs/v0.3/V03E_G0_5_PRE_ETB_CAPABILITY_RESOLUTION.md`, blob `59e8ef575fa3ab854f65fee5e25621c51f74c8b76615d7d4d9fb1e071b4049ac` |
| accepted SIC definition | `docs/v0.3/V03E_G0_5_PRE_SESSION_INCARNATION_FINDING.md`, blob `5463ac19ddc532f2a5f4f73c1076284f4c5f75b94338a5720a189b955e23ad11` |
| Mode-A oracle / result | `31d7ac5020ba6a7e3a4eb700df0feedc8f480d67a89f7124091e87df9ff7dc78` / `ce6c503d3bd62fa09c34d52bbd570e1a98dab403d1164b2e740fe6c476ecadc6` |
| §25.1 protected block | `d3244ee0d24f5d740b34dac358378870d4d8238b0755787cffb7313d01044ee0` |
| G0.4 oracle | `b0c34fa19c3e639b5637d74d49e1c9c357b7db914ee1becf70229f3e5ed4bfa4` |

## 1. Method

**1.1 Closed external source set (D1–D9).**  External network access was used **only** for the nine
approved Microsoft Learn pages, retrieved once each by a bounded direct HTTPS retrieval from the
local Windows PowerShell session (no search-engine result was used as semantic evidence; no
third-party source; no link followed from any approved page).  All nine returned HTTP 200 and their
bodies were hashed; **no page body is stored in this repository** (§5 of the round brief).

**1.2 Closed local probe set (S1–S4).**  Metadata/schema probes only: `Get-Command` metadata (S1,
S4) and `Get-CimClass` class metadata (S2, S3).  **No** TCP connection, listener, port or process
**instance** was queried or enumerated; `Get-NetTCPConnection` itself was never executed; no
`Get-CimInstance` call was made for either class.

**1.3 Evidence location.**  `docs/v0.3/evidence/etb-u2-u3-authoritative-semantics/` — 14 tracked
evidence files plus `MANIFEST.sha256` (all 14 hashes verified OK).  Each `D*` file carries the source
ID, title, canonical location, retrieval timestamp, retrieved-body SHA-256, paraphrased propositions
and only the minimal short excerpts needed to prove them.

## 2. Retrieval record (D1–D9)

| ID | Title | Retrieved final URL | Bytes | Retrieved-body SHA-256 | Retrieved |
| --- | --- | --- | --- | --- | --- |
| D1 | Get-NetTCPConnection (NetTCPIP) | `/en-us/powershell/module/nettcpip/get-nettcpconnection?view=windowsserver2025-ps` | 69290 | `e6d01fef2b73cda806d21b57399bcc7f470d1edf4b115f2f053265961f6d815c` | 2026-09-20T12:57:51 |
| D2 | MSFT_NetTCPConnection class | `/en-us/windows/win32/fwp/wmi/nettcpipprov/msft-nettcpconnection` | 109836 | `6a840d574f233838dc0cb0066b11d0c7ef954e6f589b6befc3b62f6695f025ba` | 2026-09-20T12:57:51 |
| D3 | Win32_Process class | `/en-us/windows/win32/cimwin32prov/win32-process` | 104616 | `22630ac5d64a70e8463582ff6678edb562837a6383ceb40b17fc14abfca357ad` | 2026-09-20T12:57:51 |
| D4 | Get-CimInstance (CimCmdlets), 5.1 view | `/en-us/powershell/module/cimcmdlets/get-ciminstance?view=powershell-5.1` | 120192 | `72aa6ae90a0412f4bf9cad4f9e51e9b8549de654078702ec386c1a45dd914218` | 2026-09-20T12:57:52 |
| D5 | about_WQL, 5.1 view | `/en-us/powershell/module/microsoft.powershell.core/about/about_wql?view=powershell-5.1` | 74466 | `e5965760204e20653677cd1096b72ea5ef43c9fa12ba5fb7e1be5ff4f720967c` | 2026-09-20T12:57:52 |
| D6 | about_Arrays, 5.1 view | `/en-us/powershell/module/microsoft.powershell.core/about/about_arrays?view=powershell-5.1` | 88056 | `0f5b158724f5b9135fd182f521fcaa4842e58db3f34cb23c45cd6960ee293ac1` | 2026-09-20T12:57:52 |
| D7 | GetFinalPathNameByHandleW (fileapi.h) | `/en-us/windows/win32/api/fileapi/nf-fileapi-getfinalpathnamebyhandlew` | 59967 | `79eece1aa66bb7305039bd583f7e157606270d432fd1c74cd3f03141151cdea9` | 2026-09-20T12:57:53 |
| D8 | CreateFileW (fileapi.h) | `/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew` | 115289 | `928be0bdc6cd702f41f4f09df6c8ddd2c46ddba45629eccb5e4b49e890081630` | 2026-09-20T12:57:53 |
| D9 | Add-Type (Microsoft.PowerShell.Utility), 5.1 view | `/en-us/powershell/module/microsoft.powershell.utility/add-type?view=powershell-5.1` | 115125 | `55f5f2a865f5869f1964ee6ff57511ba2421c29ea64264d212836eecdf1ff3d8` | 2026-09-20T12:57:53 |

**Retrieval count: exactly 9 (all HTTP 200).**  No other external source was contacted.

## 3. Local metadata probe record (S1–S4)

| ID | Exact command | Result |
| --- | --- | --- |
| S1 | `Get-Command Get-NetTCPConnection` | `Function`, module `NetTCPIP` 1.0.0.0; **OutputType has 2 entries**, the second being `Microsoft.Management.Infrastructure.CimInstance#ROOT/StandardCimv2/MSFT_NetTCPConnection` |
| S2 | `Get-CimClass -Namespace root/StandardCimv2 -ClassName MSFT_NetTCPConnection` | class present in `ROOT/StandardCimv2`; `LocalAddress` (String), `LocalPort` (UInt16), `State` (UInt8), `OwningProcess` (UInt32), `CreationTime` (DateTime) all present, **all `ReadOnly`** with `read=True` |
| S3 | `Get-CimClass -Namespace root/cimv2 -ClassName Win32_Process` | class present in `ROOT/CIMV2`; `ProcessId` (UInt32), `ExecutablePath` (String), `CreationDate` (DateTime) all present, all `ReadOnly`; `CreationDate` carries `Fixed=True`; `ExecutablePath` carries `Privileges=SeDebugPrivilege` |
| S4 | `Get-Command Add-Type` | `Cmdlet`, `Microsoft.PowerShell.Utility` 3.1.0.0 |

Machine-readable copies: `S1-get-nettcpconnection-command-metadata.json`,
`S2-msft-nettcpconnection-schema.json`, `S3-win32-process-schema.json`,
`S4-add-type-command-metadata.json` (hashes in `MANIFEST.sha256`).

## 4. U2 matrix — frozen-endpoint → unique owning PID

| Fact | Evidence | Classification |
| --- | --- | --- |
| exact-local-address filter | D1 P2: `-LocalAddress` "Specifies an array of local IP addresses. The cmdlet gets connections for the addresses that you specify." — `Supports wildcards: False`, alias `IPAddress`, position 0 | **ESTABLISHED** |
| exact-local-port filter | D1 P3: `-LocalPort` "Specifies an array of local ports. The cmdlet gets connections for the ports that you specify." — `Supports wildcards: False`, position 1 | **ESTABLISHED** |
| listener-state restriction | D1 P4: `-State` "Specifies an array of TCP states. The cmdlet gets connections that match the states that you specify", `Listen` an accepted value; D2 P4: `State` is a Read-only property with `Listen = 2` = "Waiting for a connection request from any remote TCP and port" | **ESTABLISHED** |
| output-class binding | S1: installed command metadata binds `OutputType` to `…CimInstance#ROOT/StandardCimv2/MSFT_NetTCPConnection`; D1 P5 documents the `CimInstance` wrapper whose path after `#` gives namespace and class; D2 P1 places the class in `Root\StandardCimv2`; S2 confirms the class locally | **ESTABLISHED** |
| owning-PID **output** semantics | D2 P5: `OwningProcess` — uint32, **Read-only** — "The PID of the owning process of the TCP connection."; S2 confirms `ReadOnly` locally.  Kept distinct from the `-OwningProcess` **input** filter | **ESTABLISHED** |
| result cardinality / uniqueness detectability | D6: `@( ... )` places the enclosed result in an array "Even if there is zero or one object"; documented `$a.Count → 1` (one object) and `$b.Count → 0` (empty); `Count` is the standard collection-count property | **ESTABLISHED** |

**4.1 U2 overall: `U2_ESTABLISHED`.**  Every required piece is authoritatively established (exact
address filter, exact port filter, Listen restriction, output contract, owning-PID output semantics,
unique-result detectability), and the local applicability of the class and command metadata is bound
through S1/S2.  No contradiction with the accepted ETB definition was found: the mechanism is
**endpoint-scoped** (it queries only the already-frozen exact address/port), it performs **no**
discovery, and it **fails closed** unless exactly one matching listener exists.

**4.2 Recorded fail-closed properties (design requirements, not gaps).**  A target bound to a
wildcard address rather than the frozen numeric loopback address yields **zero** matches and therefore
fails closed (correct per the accepted ETB definition); multiple matches (e.g. an address/port pair
shared by several listeners) fail closed; the future oracle must require `@(...).Count == 1` before
reading `OwningProcess` from the unique result.  No address or port was frozen or queried in this
round.

## 5. U3 matrix — known PID → executable identity, process-instance identity, canonical path

| Fact | Evidence | Classification |
| --- | --- | --- |
| exact PID-scoped query | D4 P1: `-Filter` "Specifies a where clause to use as a filter … WQL or the CQL query language. Do not include the WHERE keyword"; D5 P1/P2/P3: `WHERE <property> <operator> <value>`, `=` = **Equal**, `LIKE` = wildcard, property/value must be accurate; D5 P4 documents the same class in an example | **ESTABLISHED** (upgrades the prior evidence basis; no PID was queried) |
| local `ProcessId` presence | S3: `ProcessId` (UInt32, ReadOnly) present in `ROOT/CIMV2` | **ESTABLISHED** |
| local `ExecutablePath` presence | S3: `ExecutablePath` (String, ReadOnly, `Privileges=SeDebugPrivilege`) present | **ESTABLISHED** |
| documented `ExecutablePath` semantics | D3 P2: "Path to the executable file of the process." | **ESTABLISHED** |
| local `CreationDate` presence | S3: `CreationDate` (DateTime, ReadOnly, `Fixed=True`) present | **ESTABLISHED** |
| documented `CreationDate` semantics | D3 P3: "Date the process begins executing." (qualifier `Fixed`) | **ESTABLISHED** |
| process-instance discriminator strength | D3 P3 + S3 `Fixed=True`: the creation date is fixed for the process instance and denotes when that process began executing, so a later **reused PID** necessarily belongs to a newly started process with a different creation date — sufficient for snapshot-to-snapshot replacement detection (no mathematical global uniqueness required or claimed) | **ESTABLISHED** |
| final/canonical path API semantics | D7: "Retrieves the final path for the specified file"; `FILE_NAME_NORMALIZED` (0x0) "Return the normalized drive name. This is the default."; `VOLUME_NAME_DOS` (0x0) "Return the path with the drive letter. This is the default."; "A final path is the path that is returned when a path is fully resolved" (symlink example) | **ESTABLISHED** (with caveats, §5.2) |
| read-only handle acquisition | D8: `dwDesiredAccess` documents `GENERIC_READ`; `OPEN_EXISTING` (3) "Opens a file or device, only if it exists. If the specified file or device does not exist, the function fails and the last-error code is set to ERROR_FILE_NOT_FOUND (2)" — no creation, no truncation (`TRUNCATE_EXISTING` is a separate disposition) | **ESTABLISHED** |
| locally available route to invoke that capability | D9: "On Windows, you can use this feature to make Platform Invoke (P/Invoke) calls to unmanaged functions in PowerShell" (+ documented native-API example); S4: `Add-Type` present locally as a Cmdlet (`Microsoft.PowerShell.Utility` 3.1.0.0) | **ESTABLISHED** |
| SHA-256 exact-path hashing | previously accepted finding; **not reopened** (no contradictory evidence appeared) | **ESTABLISHED** (carried) |

**5.1 U3 overall: `U3_ESTABLISHED`.**  All items required by the round brief are sufficiently
established, including the locally available invocation route for the final-path capability.

**5.2 Recorded fail-closed caveats (design requirements, not gaps).**  (i) `ExecutablePath` carries
the documented `Privileges ("SeDebugPrivilege")` qualifier, so a future oracle must treat an
unreadable/absent value as **fail closed**, never as an empty or benign path.  (ii) Under
`FILE_NAME_NORMALIZED` the API splits the path into components and fails with `ERROR_ACCESS_DENIED`
if the caller lacks access to any component — a fail-closed outcome.  (iii) With `VOLUME_NAME_DOS`
the returned string uses the `\\?\` form, and the future oracle must apply the **identical**
canonicalization to both the process's `ExecutablePath` and the accepted target binary before
comparing.  (iv) `ExecutablePath` itself is documented only as "path to the executable file of the
process" and must **not** be treated as canonical without the D7/D8 route.  None of these were
exercised in this round: no handle was opened, no native call was compiled or executed, and the
target executable was not opened.

## 6. Mode-P mechanism freezability

Applying the accepted mapping — `MODE_P_MECHANISM_FREEZABLE` iff `U2_ESTABLISHED` **and**
`U3_ESTABLISHED` and no contradiction with the accepted ETB definition — the result is
**`MODE_P_MECHANISM_FREEZABLE`**.

The combined evidence supports precommitting, in a future separately reviewed ETB oracle, the
endpoint-scoped chain: query the already-frozen numeric address + port with the Listen restriction,
require exactly one result, read the read-only `OwningProcess`, resolve the executable identity
through a PID-scoped query (`ExecutablePath` + `CreationDate`), canonicalize via a read-only
`OPEN_EXISTING` handle and `GetFinalPathNameByHandleW` with `FILE_NAME_NORMALIZED`, compare with the
same canonicalization of the accepted target binary, hash with SHA-256, and enforce pre/post
snapshot continuity.

**6.1 This is NOT Mode-P selection.**  No mode was selected or excluded; the two-mode model
(mutually exclusive, precommit-before-action, no fallback) is unchanged.  `MODE_P_MECHANISM_FREEZABLE`
means only that the mechanism semantics are sufficiently established for later ETB oracle design.

## 7. U4 / U5

**U4** = **UNRESOLVED BY DESIGN / OWNER-ORACLE DECISION REMAINS** — no class-B policy invented, no
class-A port chosen, no port policy instantiated.

**U5** = **UNRESOLVED BY DESIGN / OWNER-ORACLE DECISION REMAINS** — **even though the Mode-P
mechanism is now freezable, U5 remains unresolved**; no mode was selected.

## 8. U1 / Mode-L preservation (unchanged)

**U1 = `U1_NOT_ESTABLISHED`** and **MODE L = `MODE_L_MECHANISM_NOT_YET_FREEZABLE`** are unchanged.  No
OpenCode probe was run, no server was launched, and the closed U2/U3 evidence exposes **no**
contradiction to the accepted U1 record.  (Mode-L freezability would additionally require
`U1_ESTABLISHED`; it remains not yet freezable.)

## 9. Remaining gaps

- **U1** (Mode-L launch/bind semantics and launcher-visible process identity): still the open
  capability item, unchanged by this round.
- **U4 / U5**: owner/oracle decisions, deliberately unresolved.
- **Implementation-level items for the future ETB oracle** (not capability gaps, but requirements to
  be frozen there): the exact canonicalization comparison rule and its `\\?\` handling; the
  `SeDebugPrivilege` fail-closed policy; the exact pre/post snapshot field set and comparison rule;
  and the exact cardinality enforcement expression.
- The prior round's U2 mechanism gap (no concrete endpoint-scoped primitive with established
  semantics) and U3 mechanism gaps (no documented executable-path property, no canonicalization
  route, no process-instance discriminator) are **closed** as capability questions by this round's
  candidate finding.

## 10. Non-claims

This candidate finding does **not** establish an endpoint (`opencode.base_url` remains `""`), does
**not** select a port, address or address family, does **not** select Mode L or Mode P, does **not**
authorize a configuration change or an OpenCode start, is **not** an ETB execution oracle, **not**
ETB execution, **not** ETB SATISFIED/UNSATISFIED, **not** a SIC result, **not** a P6 result and
**not** a G0.5 result.  No live TCP, listener, port or process-instance query was performed; no
provider/model call and no session interaction occurred.  `U2_ESTABLISHED`, `U3_ESTABLISHED` and
`MODE_P_MECHANISM_FREEZABLE` are capability/design-support results only.

## 11. Preserved state

ETB = `DEFINITION ACCEPTED / NOT EXECUTED`; ETB EXECUTION / ORACLE = `NOT YET DEFINED / NOT
AUTHORIZED`.  Mode A remains completed and authoritative (`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`,
strictly scoped to the accepted static surface).  Mode-B = `NOT RUN / NO ORACLE / ORACLE NOT
FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING
PREREQUISITE BLOCKER`; Mode-B oracle construction has not resumed.  `G0.5 / P6 = NOT RUN / DEFINITION
ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 NOT
CLOSED.  `G1`/`G2` `NOT RUN`; Case-C and v0.3-E implementation `NOT AUTHORIZED`;
`adopt_completed_turn` **DISABLED**.

## 12. Activity counters

Live TCP queries 0; live process-instance queries 0; port/listener/process enumeration 0; endpoint
establishments 0; port selections 0; mode selections 0; OpenCode server starts 0; OpenCode HTTP 0;
`/doc` 0; `/session` 0; provider/model calls 0; ETB executions 0; Mode-B SIC oracle work 0; SIC
attempts 0; G0.5 0; G1/G2 0; runtime/test/dependency/version changes 0.  External network: **exactly
9** approved Microsoft Learn retrievals (D1–D9), no other external request.  Local probes: **exactly
4** (S1–S4), metadata/schema only.

**End of round-2 candidate finding.**
