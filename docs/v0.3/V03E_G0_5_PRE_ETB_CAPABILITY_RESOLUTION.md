# DevRelay v0.3-E — G0.5-PRE / SIC — ETB execution-oracle design support: U1 / U2 / U3 capability resolution

> **ETB EXECUTION-ORACLE DESIGN SUPPORT**
> **U1 / U2 / U3 CAPABILITY RESOLUTION**
> **CANDIDATE FINDING**
> **NOT ACCEPTED**
> **NOT AN ETB EXECUTION ORACLE**
> **NOT ETB EXECUTION**
> **DOES NOT ESTABLISH AN ENDPOINT**
> **DOES NOT SELECT A MODE**
> **DOES NOT AUTHORIZE CONFIGURATION CHANGE**
> **DOES NOT AUTHORIZE OPENCODE SERVER START**

Status: **CANDIDATE FINDING — NOT ACCEPTED** (design-support evidence only)

Baseline: `bb7f7899cf198f8b81089e81c07faf377edd8583` (branch `v0.3-e-recovery-reconciliation`).

This artifact records a bounded, read-only capability resolution for the three unresolved platform
facts carried by the accepted ETB definition (U1, U2, U3).  It is **design support for a future ETB
execution oracle**; it is **not** an ETB execution oracle, it does **not** execute ETB, and it is
**not** a new proof-ladder gate.

Anchors (committed Git blobs):

| Anchor | Identity |
| --- | --- |
| accepted ETB definition | `docs/v0.3/V03E_G0_5_PRE_MODE_B_ENDPOINT_BINDING.md`, commit `f3f625f`, blob `99cc6dcee4ab1a3f0589c3e7d11308d089601ba07d16cc2d37a9fc32c777b3a0` |
| accepted SIC definition | `docs/v0.3/V03E_G0_5_PRE_SESSION_INCARNATION_FINDING.md`, blob `5463ac19ddc532f2a5f4f73c1076284f4c5f75b94338a5720a189b955e23ad11` |
| Mode-A oracle | `docs/v0.3/V03E_G0_5_PRE_SIC_ORACLE.md`, blob `31d7ac5020ba6a7e3a4eb700df0feedc8f480d67a89f7124091e87df9ff7dc78` |
| Mode-A result | `docs/v0.3/V03E_G0_5_PRE_SIC_RESULT.md`, blob `ce6c503d3bd62fa09c34d52bbd570e1a98dab403d1164b2e740fe6c476ecadc6` |
| §25.1 protected block | `docs/v0.3/V03E_SPEC.md` §25.1, blob `d3244ee0d24f5d740b34dac358378870d4d8238b0755787cffb7313d01044ee0` |
| G0.4 oracle | `docs/v0.3/V03E_G0_4_API_INSPECTION_ORACLE.md`, blob `b0c34fa19c3e639b5637d74d49e1c9c357b7db914ee1becf70229f3e5ed4bfa4` |

## 1. Purpose and output role

**1.1 Purpose.**  Resolve, as far as soundly possible from bounded **local read-only** evidence, the
concrete platform capabilities behind **U1** (exact OpenCode launch syntax / explicit bind
capability), **U2** (exact Windows frozen-endpoint → owning-PID verification primitive and
semantics) and **U3** (process-instance / creation-identity primitive and semantics).

**1.2 Output role.**  Design-support evidence only.  It may establish that a concrete mechanism is
available for later ETB oracle construction; it does **not** mean ETB oracle accepted, ETB
execution authorized, `ETB SATISFIED`, endpoint established, mode selected, SIC proved, P6 proved or
G0.5 proved.

**1.3 Out of scope.**  U4 (concrete deterministic port policy) and U5 (actual ETB mode selection)
are **not** resolved here.  No endpoint, port, address family, Mode L or Mode P was selected, and
`opencode.base_url` was not touched.

## 2. Method and closed probe set

**2.1 Closed set.**  Exactly the authorized probes were run — **O1, O2, W1–W9** — with no addition,
no substitution and no variant after observing output.  Presentation capture used
`Out-String -Width 400` uniformly for the W probes (a capture-width choice applied identically to
every probe, not a per-probe adaptation).

**2.2 Execution environment note (disclosed).**  The harness's Windows-run helper was unavailable
in this session (`spawn ... node.exe ENOENT`), so the authorized W probes were executed through the
platform's own `powershell.exe` with `-NoProfile -NonInteractive` from the local shell instead.  The
commands, the closed set and the metadata-only restriction were unchanged.

**2.3 Help-only OpenCode boundary.**  O1/O2 were invoked as help/metadata only, with a bounded
30-second timeout and stdin closed.  Both exited immediately (exit code `0`) printing help text;
neither started a server, opened a listener, submitted a prompt, accessed a session, invoked a
provider, or performed external network traffic.  No `serve` invocation without `--help` was made,
no binding was tested, and no port was selected.

**2.4 U2 discovery guard.**  `Get-NetTCPConnection` itself was **never executed**: only
`Get-Command` and `Get-Help` metadata were inspected (W1/W2).  No listener, port or endpoint was
listed or derived.

**2.5 U3 process-query boundary.**  No process was enumerated and no current PID was queried.  Only
cmdlet capability metadata/help (W3/W4/W6/W7/W8/W9) and `Win32_Process` **class/schema** metadata
(W5, `Get-CimClass`) were inspected.

**2.6 No help-file installation / no online help.**  `Update-Help` and `-Online` were **not** used
(closed set).  This materially limits the captured help (see §11).

## 3. Probe execution record

Target executable (verified **before** O1 and re-verified **after** all probes):
`C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe`, SHA-256
`578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35` (identical both times), size
174 182 280 bytes.  Package metadata read from the same installation root: `name = opencode-ai`,
`version = 1.18.11`, declared bin `./bin/opencode.exe`.

| Probe | Exact command | Ran | Exit / state | stdout bytes | stderr bytes | stdout SHA-256 | stderr SHA-256 | Supports |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O1 | `<target exe> --help` | yes | `0` | 0 | 4291 | `e3b0c442…b7852b855` (empty) | `250e987d…8ed9974e` | U1 A–F |
| O2 | `<target exe> serve --help` | yes | `0` | 0 | 1234 | `e3b0c442…b7852b855` (empty) | `6855794f…f839684e` | U1 A–F |
| W1 | `Get-Command Get-NetTCPConnection` | yes | `0` | 1214 | 0 | `bb8b706c…216798e9` | empty | U2 availability |
| W2 | `Get-Help Get-NetTCPConnection -Full` | yes | `0` | 5230 | 0 | `d083198d…7b8ed99` | empty | U2 semantics |
| W3 | `Get-Command Get-CimInstance` | yes | `0` | 1214 | 0 | `efce47eb…d524e86` | empty | U3 availability |
| W4 | `Get-Help Get-CimInstance -Full` | yes | `0` | 7883 | 0 | `6e995575…bcd4a` | empty | U3 PID-scoped query shape |
| W5 | `Get-CimClass -ClassName Win32_Process` | yes | `0` | 1244 | 0 | `09638f96…b512e3` | empty | U3 class metadata |
| W6 | `Get-Command Get-Process` | yes | `0` | 1214 | 0 | `0d7eb3bc…ec3b66` | empty | U3 availability |
| W7 | `Get-Help Get-Process -Full` | yes | `0` | 4053 | 0 | `b3e85643…877063` | empty | U3 PID-scoped query shape |
| W8 | `Get-Command Get-FileHash` | yes | `0` | 1214 | 0 | `1818ac53…c6d31a` | empty | U3 hash capability |
| W9 | `Get-Help Get-FileHash -Full` | yes | `0` | 2614 | 0 | `5909738f…cddf09` | empty | U3 hash capability |

All W probes are PowerShell cmdlet probes, so their "exit code" is the process exit code of the
non-interactive shell invocation (`0` = the command completed without a terminating error); none
produced stderr bytes.  Raw captures (unhashed padding included) are retained **outside the
repository** at `C:\Users\1\AppData\Local\Temp\etb-cap.PC89OZ`; only the hashes above and the
excerpts in this artifact are recorded.  No secrets were captured or persisted.

**3.1 Availability facts (from W1/W3/W6/W8).**

| Cmdlet | CommandType | Module / source | Version |
| --- | --- | --- | --- |
| `Get-NetTCPConnection` | Function | `NetTCPIP` | 1.0.0.0 |
| `Get-CimInstance` | Cmdlet | `CimCmdlets` | 1.0.0.0 |
| `Get-Process` | Cmdlet | `Microsoft.PowerShell.Management` | 3.1.0.0 |
| `Get-FileHash` | Function | `Microsoft.PowerShell.Utility` | 3.1.0.0 |

## 4. U1 — OpenCode launch syntax / explicit bind capability

**4.1 Evidence (O1, exact target binary).**  The command list includes
`opencode serve    starts a headless opencode server`; the global options include:

```
      --port          port to listen on                                        [number] [default: 0]
      --hostname      hostname to listen on                          [string] [default: "127.0.0.1"]
      --mdns          enable mDNS service discovery (defaults hostname to 0.0.0.0)
                                                                          [boolean] [default: false]
      --mdns-domain   custom domain name for mDNS service (default: opencode.local)
```

**4.2 Evidence (O2, exact target binary).**  `opencode serve` has its own help page with the same
serve-relevant options: `--port` (`[number] [default: 0]`), `--hostname`
(`[string] [default: "127.0.0.1"]`), `--mdns` (defaults hostname to `0.0.0.0`), `--mdns-domain`,
`--cors`, `--pure`, `--print-logs`, `--log-level`.  It documents no output/URL/PID reporting.

**4.3 U1 per-fact matrix.**

| Fact | Required finding | Classification |
| --- | --- | --- |
| A | the server subcommand exists | **ESTABLISHED** — `opencode serve` is documented as "starts a headless opencode server" |
| B | the exact command form is established | **ESTABLISHED** — `opencode serve` plus its documented options |
| C | explicit numeric-address/hostname binding option | **ESTABLISHED** — `--hostname <string>` documented as "hostname to listen on", default the numeric loopback literal `"127.0.0.1"` |
| D | explicit port-binding option | **ESTABLISHED** — `--port <number>` documented as "port to listen on", default `0` |
| E | semantics permit binding the preauthorized exact endpoint rather than selecting another endpoint implicitly | **SEMANTICS_UNPROVEN** — the options' purpose is documented, but the help does not document exact-bind behaviour, the meaning of `--port 0`, bind-failure behaviour, or the absence of implicit substitution; `--mdns` is documented as *changing* the effective hostname to `0.0.0.0`, so hostname selection is demonstrably alterable by another flag |
| F | the launch invocation gives the launcher a deterministic child/process identity sufficient for later binding design | **SEMANTICS_UNPROVEN** — the help documents no process-identity, URL or port reporting for `serve`; §9 forbids launching the server to observe behaviour, so this cannot be resolved from help evidence alone |

**4.4 U1 overall: `U1_NOT_ESTABLISHED`.**

Exact reason: facts **A–D are established** from the exact target binary's own help (subcommand,
command form, and explicit `--hostname`/`--port` options with documented purpose and defaults), but
facts **E and F are `SEMANTICS_UNPROVEN`**.  Under §8, `U1_ESTABLISHED` requires that **all**
launch/bind semantics needed for Mode L can later be frozen **without invention**; exact-bind and
bind-failure semantics (E) and deterministic launcher-visible process identity (F) cannot yet be
frozen from the authorized evidence, so U1 is **not** established.

Remaining information need: an authoritative, reviewed determination of (i) `--hostname`/`--port`
exact-bind and bind-failure semantics (including the meaning of the documented `--port 0` default),
and (ii) how a future Mode-L launch obtains a deterministic process identity for the launched
server.  Both require evidence beyond `--help` (e.g. an authorized launch-capability determination),
and neither may be closed by guessing flags or by launching a server in a capability round.

**4.5 No mode selection.**  Nothing here selects Mode L, and no `serve` invocation without `--help`
was made (§9).

## 5. U2 — frozen-endpoint → owning-PID verification primitive

**5.1 Evidence (W1).**  `Get-NetTCPConnection` is available (Function, `NetTCPIP` 1.0.0.0).

**5.2 Evidence (W2, syntax and parameter metadata).**

```
Get-NetTCPConnection [[-LocalAddress] <string[]>] [[-LocalPort] <uint16[]>]
    [-RemoteAddress <string[]>] [-RemotePort <uint16[]>]
    [-State {Closed | Listen | SynSent | SynReceived | Established | FinWait1 | FinWait2 |
             CloseWait | Closing | LastAck | TimeWait | DeleteTCB | Bound}]
    [-AppliedSetting {...}] [-OwningProcess <uint32[]>] [-CreationTime <datetime[]>]
    [-OffloadState {...}] [-CimSession <CimSession[]>] [-ThrottleLimit <int>] [-AsJob]
```

* `-LocalAddress <string[]>` — position `0`, alias `IPAddress`, accepts pipeline input by property
  name;
* `-LocalPort <uint16[]>` — position `1`;
* `-State` — the allowed values explicitly include `Listen`;
* `-OwningProcess <uint32[]>` — present as a parameter;
* `OUTPUTS`: `Microsoft.Management.Infrastructure.CimInstance#ROOT/StandardCimv2/MSFT_NetTCPConnection`
  — the help does **not** enumerate that class's properties;
* `REMARKS`: **"Get-Help cannot find the Help files for this cmdlet on this computer.  It is
  displaying only partial help."** — no parameter descriptions are present in the captured help.

**5.3 U2 per-fact matrix.**

| Fact | Classification |
| --- | --- |
| filter-by-exact-local-address | **SEMANTICS_UNPROVEN** — the `-LocalAddress` parameter is exposed (position 0, alias `IPAddress`), but no description text documents exact-match filtering semantics (or wildcard/range behaviour) |
| filter-by-exact-local-port | **SEMANTICS_UNPROVEN** — `-LocalPort <uint16[]>` is exposed, but its filtering semantics are not documented |
| listener-state restriction | **SEMANTICS_UNPROVEN** — `-State` admits the documented value `Listen`, but that it restricts results to listening endpoints is not documented |
| owning-PID exposure | **EVIDENCE_INSUFFICIENT** — `-OwningProcess` exists as an *input* parameter, but the output class's property enumeration is absent from the (partial) help, so an owning-PID *output* property is not documented either way |
| multiple-result detectability | **SEMANTICS_UNPROVEN** — the documented output type is a CIM instance collection, but result-count semantics are not documented |

**5.4 U2 overall: `U2_NOT_ESTABLISHED`.**

Exact reason: the interface **shape** is documented (address, port and state parameters exist), but
the captured help is explicitly **partial** because the module's help files are not installed on
this machine, so the **semantics** required to precommit a deterministic endpoint-scoped predicate
(exact-match behaviour, result-set semantics, owning-PID output property) are not established.  Per
§12, the help contract therefore cannot establish a sufficiently exact endpoint-scoped predicate.

Remaining information need: documented parameter semantics for `-LocalAddress`/`-LocalPort`/`-State`
and the `MSFT_NetTCPConnection` output property enumeration (in particular an owning-PID property).
Obtainable only through evidence outside the authorized closed set (e.g. installed help files or
authoritative documentation) or through a future, separately reviewed ETB oracle.

**5.5 No live lookup claimed.**  No endpoint→PID lookup was performed, no listener or port was
listed, and no endpoint was derived.  Capability evidence is **not** endpoint authority.

## 6. U3 — process-instance / creation-identity primitive

**6.1 Evidence (W3/W4).**  `Get-CimInstance` is available (Cmdlet, `CimCmdlets` 1.0.0.0).  Its
documented syntax includes `[-ClassName] <string>` (required, position 0), `-Filter <string>`,
`-Query <string>`, `-QueryDialect <string>`, `-Property <string[]>`, `-KeyOnly`; `OUTPUTS`:
`Microsoft.Management.Infrastructure.CimInstance`.  The help is **partial** (same REMARKS) and is
rendered in the machine's localized help language; no parameter descriptions are present.

**6.2 Evidence (W5).**  `Get-CimClass -ClassName Win32_Process` resolves in namespace `ROOT/CIMV2`:
class `Win32_Process`, methods shown as `{Create, Terminat…}`, properties shown as
`{Caption, Description, InstallDate, Name…}`.  The authorized rendering **truncated the property
list**; the full property enumeration was **not** captured, and no property semantics are described.

**6.3 Evidence (W6/W7).**  `Get-Process` is available (Cmdlet, `Microsoft.PowerShell.Management`
3.1.0.0).  Its documented syntax contains an explicit PID-scoped parameter set:

```
Get-Process -Id <int[]> [-ComputerName <string[]>] [-Module] [-FileVersionInfo]
Get-Process -Id <int[]> -IncludeUserName
```

with `-Id <int[]>` required in those sets, alias `PID`.  `OUTPUTS`:
`System.Diagnostics.ProcessModule`, `System.Diagnostics.FileVersionInfo`,
`System.Diagnostics.Process` — the help does **not** enumerate the properties of
`System.Diagnostics.Process` (partial help).

**6.4 Evidence (W8/W9).**  `Get-FileHash` is available (Function, `Microsoft.PowerShell.Utility`
3.1.0.0).  Its documented syntax is:

```
Get-FileHash [-Path] <string[]> [-Algorithm {SHA1 | SHA256 | SHA384 | SHA512 | MACTripleDES | MD5 | RIPEMD160}]
Get-FileHash -LiteralPath <string[]> [-Algorithm {...}]
Get-FileHash -InputStream <Stream> [-Algorithm {...}]
```

with `-Path` required and positional 0, `-LiteralPath` (alias `PSPath`) required in its set, and
`SHA256` explicitly among the documented algorithm choices.  Help is partial (same REMARKS).

**6.5 U3 per-fact matrix.**

| Fact | Classification |
| --- | --- |
| PID-scoped process query | **ESTABLISHED** — the syntax explicitly documents a parameter set whose only identifying input is `-Id <int[]>` (alias `PID`), so a query scoped to an already-known PID can be precommitted without enumerating processes; `Get-CimInstance -ClassName/-Filter/-Query` additionally exposes a class-scoped filtered-query shape |
| executable-path exposure | **EVIDENCE_INSUFFICIENT** — neither `System.Diagnostics.Process` nor `Win32_Process` property enumeration was captured (partial help; truncated W5 rendering), so no executable-path property is documented |
| canonical-path semantics | **EVIDENCE_INSUFFICIENT** — nothing in the captured evidence documents path canonicalization (symlink/junction/reparse resolution, separator or case normalization) for any exposed path value |
| process-instance discriminator | **EVIDENCE_INSUFFICIENT** — no creation/start property is documented for either surface, and no semantics are described; a field name alone would in any case be insufficient (§18 of the design brief) |
| SHA-256 exact-path hashing | **ESTABLISHED** — `Get-FileHash` documents a required path parameter (`-Path`, positional 0; `-LiteralPath` for literal paths) together with an algorithm choice that explicitly includes `SHA256` |

**6.6 U3 overall: `U3_NOT_ESTABLISHED`.**

Exact missing semantics: (i) a **documented executable-path property** for a PID-scoped process
query, together with its **canonicalization semantics** sufficient to compare against the declared
target path
`C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe`; and (ii) a
**documented process-instance/creation-identity property** whose semantics denote the creation/start
of that specific process instance strongly enough to act as the accepted PID-reuse discriminator.
Both are absent from the authorized evidence surface (partial help; truncated class rendering), so a
later fail-closed ETB oracle cannot yet freeze a sufficiently strong process-instance chain without
invention.

Recorded sub-note (not a classification): `Get-FileHash`'s `-Path` parameter accepts a string array
and the cmdlet also exposes a separate `-LiteralPath` parameter; the captured help does not document
which one is semantically appropriate for a literal path, so a future oracle must precommit one and
justify it rather than assume.

## 7. Mechanism-freezability results

**7.1 Mode L.**  Requires `U1_ESTABLISHED` **and** `U2_ESTABLISHED` **and** `U3_ESTABLISHED`, with no
contradiction with the accepted ETB definition.  U1, U2 and U3 are all **NOT_ESTABLISHED** →
**`MODE_L_MECHANISM_NOT_YET_FREEZABLE`**.

**7.2 Mode P.**  Requires `U2_ESTABLISHED` **and** `U3_ESTABLISHED`, with no contradiction with the
accepted ETB definition (no endpoint needs to exist yet in a capability round).  Both are
**NOT_ESTABLISHED** → **`MODE_P_MECHANISM_NOT_YET_FREEZABLE`**.

**7.3 Neither result is a mode selection.**  No mode was selected, no mode was excluded, and the
accepted two-mode model (mutually exclusive, precommit-before-action, no fallback) is unchanged.

## 8. U4 / U5 — unresolved by design

**U4** (concrete deterministic port allocation policy if class B is used) =
**UNRESOLVED BY DESIGN / OWNER-ORACLE DECISION REMAINS**.  No class-B policy was invented and no
class-A port was chosen.

**U5** (actual ETB mode selection) =
**UNRESOLVED BY DESIGN / OWNER-ORACLE DECISION REMAINS**.

## 9. Evidence-surface limitations (recorded, not compensated)

**9.1** Every W help surface on this machine is **partial**: the relevant help files are not
installed, and `Update-Help`/`-Online` were outside the authorized closed set.  The captured help
therefore documents **interface shape** (syntax, parameter metadata, input/output *types*, aliases)
but **not parameter or property semantics**.

**9.2** The `Microsoft.PowerShell.*` help captured here is rendered in the machine's localized help
language; the `NetTCPIP` help is English.  Both show the same partial-help REMARKS.

**9.3** The authorized `Get-CimClass` rendering truncated the `Win32_Process` property list.  Per the
closed-set rule ("if an allowed command is missing or insufficient: record the gap; do NOT
substitute another command"), the gap is **recorded**, not worked around.

**9.4** No live platform query was performed for U2/U3 (no listener listing, no port listing, no
process enumeration, no PID query), so no runtime behaviour was observed for any candidate
primitive.

## 10. Side-effect record

**10.1 Observed side effect (disclosed exactly).**  Invoking the exact target binary for O1/O2
appended to the OpenCode log: `C:\Users\1\.local\share\opencode\log\opencode.log` grew from
**15 650 374** bytes (mtime `2026-09-20 00:47:53`) to **15 650 620** bytes (mtime `2026-09-20
00:48:12`) — **+246 bytes** within the probe window.  The log's contents were **not** read (it is
the user's own OpenCode activity log; privacy).

**10.2 Attribution caveat.**  The OpenCode state directory is shared with the user's own active
OpenCode usage — `opencode.db` (599 617 536 bytes) and `opencode.db-wal` (5 384 872 bytes) mtimes
also advanced inside the same window.  The log growth is therefore consistent with, but not
exclusively attributable to, this round's help invocations.

**10.3 No other side effects observed.**  No `.devrelay` modification (`config.yaml` and `state.json`
byte-identical, mtimes unchanged at `2026-09-16 01:47:06`; `opencode.base_url` still `""`); no
repository runtime/test/config modification (`git status` clean throughout); no intentionally created
OpenCode listener (both help invocations exited immediately with exit code `0` and printed only help
text; no `serve` without `--help` was run); no HTTP; no `/doc` or `/session` access; no port scan or
listener enumeration; no provider/model call; no external network access; no ETB execution.

**10.4** `PROJECT_MEMORY.md` is ignored/untracked agent-memory bookkeeping and is **not** repository
evidence.

## 11. Non-claims

This candidate finding does **not** establish or imply: an endpoint (no endpoint exists,
`opencode.base_url` remains `""`); a port, address or address family; a selected mode; an ETB
execution oracle; ETB execution authorization; `ETB SATISFIED`; `ETB UNSATISFIED`; SIC PASS or FAIL;
P6 PASS or FAIL; G0.5 PASS or FAIL; adoption enablement; or any implementation authorization.  The
`U1_NOT_ESTABLISHED` / `U2_NOT_ESTABLISHED` / `U3_NOT_ESTABLISHED` results are **evidence-surface
limitations**, not findings that the platform lacks these capabilities, and they are **not** ETB
outcomes.

## 12. Preserved state

Mode-A remains **completed and authoritative** (`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`, strictly
scoped to its accepted frozen static surface).  Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT
FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING
PREREQUISITE BLOCKER` and its oracle construction has **not** resumed.  ETB remains
`DEFINITION ACCEPTED / NOT EXECUTED` with `ETB EXECUTION / ORACLE = NOT YET DEFINED / NOT
AUTHORIZED` (unchanged by this round).  `G0.5 / P6` remains `NOT RUN / DEFINITION ACCEPTED / ORACLE
NOT FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED` and **NOT CLOSED**;
`G1`/`G2` remain `NOT RUN`; Case-C and v0.3-E implementation remain **NOT AUTHORIZED**;
`adopt_completed_turn` remains **DISABLED**.

## 13. Activity counters

Endpoint establishments 0; endpoint selections 0; port selections 0; configuration changes 0;
OpenCode server starts/restarts 0; listeners created 0; ETB executions 0; ETB execution oracles
created 0; Mode-B SIC oracles created 0; SIC attempts 0; HTTP requests 0; `/doc` 0; `/session` 0;
port scans 0; listener enumerations 0; process enumerations 0; provider/model calls 0; fake provider
0; external network requests 0; G0.5 0; G1/G2 0; runtime/test/dependency/version changes 0.
Authorized probes executed: **11 of 11** (O1, O2, W1–W9), no additions, no substitutions.

**End of capability-resolution candidate.**
