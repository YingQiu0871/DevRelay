# Oracle-PathE — new ETB execution oracle design candidate (PATH_E)

**Status: DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE.
Revision: REMEDIATED per third-party design-review findings (see §21).**

**Revision note.** The first Oracle-PathE design candidate commit
`3b085dae4ff89512bcf23f80043b78ddc82a490f` received a third-party independent
design-review verdict of `REQUEST_CHANGES` (P0 = 0, P1 = 1, P2 = 1, P3 = 3). The
accepted findings are remediated in this revision and recorded in §21. The
remediated artifact remains a **design candidate**: not accepted, not frozen,
not effective; it authorizes no execution and consumes no budget.

This document specifies the normative Oracle-PathE executable
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.ps1`. It is a design
candidate only: it authorizes no execution, consumes no budget, reserves no
runtime output, and creates no ETB observation.

---

## 1. Owner decision and lineage identity

| Item | Value |
|---|---|
| OWNER DECISION | OPEN A NEW ETB LINEAGE |
| Lineage | `PATH E — NEW ETB ATTEMPT` |
| Human oracle name | `Oracle-PathE` |
| Canonical lineage token | `PATH_E` |
| Canonical oracle token | `ORACLE_PATH_E` |
| Spec artifact | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.md` |
| Executable artifact | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.ps1` |

This is a **new** lineage. It is **not** a retry of Path D, not `Recovery-R3`,
not `Oracle-R3`, not `Oracle-D`, not `Oracle-PD`, not `Oracle-PathD2`, not a
reuse of Path-D authorization, not a reset of Path-D budgets, and not a
repair-and-rerun of Oracle-PathD. The historical naming exclusions remain
historical and preserved; none of those identifiers is used as an active oracle
identity anywhere in this artifact or in its executable.

---

## 2. Historical predecessor and reviewed defect (design motivation)

**Historical predecessor:** `Oracle-PathD`
(`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1`), now
`EXHAUSTED / CLOSED / IMMUTABLE` and **not** modified by this design.

**Historical reviewed defect (independently confirmed, accepted, NOT
REPAIRED):** `Get-FileHash` was **used** unprotected at the predecessor's
lines 117 and 118 for oracle self-identity, while command availability was only
**checked** later at its line 189, inside an infrastructure gate whose own list
**includes** `Get-FileHash`. That gate was therefore unreachable in exactly the
scenario it exists to handle.

**Historical consequence:** the Path-D one-shot attempt was exhausted with
`ORACLE-PATHD INVOCATIONS = 1 OF 1 / MAXIMUM REACHED` and produced **no ETB
semantic result**: the intended `HARNESS_INVALID` branch was never reached,
evidence/manifest/result publication was never reached, the listener query was
never reached, target binding was never reached, S0/S1 continuity was never
reached, and the process terminated with exit code 1, outside the predecessor's
intended `0`/`3` completion model.

**Explicit statement:** Oracle-PathE **DOES NOT REOPEN PATH-D**. It is a new
oracle design in a new owner-governed lineage. Path-D's exhausted budgets,
claims, records and artifacts are historical facts and are neither reused nor
reset.

**Normative rule introduced to eliminate the defect:**

> **NO REQUIRED FACILITY MAY BE USED BEFORE ITS REQUIRED-AVAILABILITY CONDITION
> HAS BEEN SAFELY ESTABLISHED.**

and, specifically:

> **`Get-FileHash` MUST NOT be invoked before Oracle-PathE has safely
> established whether `Get-FileHash` is available.**

Oracle-PathE satisfies both by never calling `Get-FileHash` at all (see §5) and
by running an explicit bootstrap safety phase before every other stage (see §4).

---

## 3. Scope of this design candidate

Authorized by this round: **design and construction of the Oracle-PathE design
candidate only.**

Not authorized by this round: Path-E ETB execution; Path-E authorization-use
consumption; Path-E attempt consumption; any listener query; any target probe;
any endpoint probe; any provider call; OpenCode start/restart; result
generation; any modification of Path-D artifacts.

Expected life cycle after this round (no stage may be skipped):

```
Oracle-PathE design candidate
→ third-party independent Oracle-PathE design review
→ Oracle-PathE acceptance bookkeeping
→ independent bookkeeping confirmation
→ Path-E execution-authorization design
→ its independent review / acceptance lifecycle
→ only then a future one-shot operational round
```

---

## 4. Bootstrap safety phase (normative)

Oracle-PathE executes a **BOOTSTRAP SAFETY PHASE** before every other stage.
Its purpose is to guarantee that the oracle can reach its own classification
machinery without first depending on an unchecked facility.

### 4.1 Assumed bootstrap primitives

Available because the script is executing under Windows PowerShell / .NET at
all, and therefore **not** gated:

- PowerShell language constructs: statements, functions, operators, arrays,
  ordered hashtables, `if`/`elseif`/`else`, `foreach`, `try`/`catch`/`finally`,
  `throw`, `trap`.
- Type literals for `System.*` types and static .NET members of runtime
  libraries already loaded: `System.IO.Path`, `System.IO.File`,
  `System.IO.Directory`, `System.IO.FileStream`, `System.Text.StringBuilder`,
  `System.Text.UTF8Encoding`, `System.Text.Encoding`,
  `System.Security.Cryptography.SHA256`, `System.DateTimeOffset`,
  `System.Console`, `System.Globalization.CultureInfo`, `System.Environment`.

None of the above is a cmdlet. In particular Oracle-PathE uses
`[System.IO.Path]::GetDirectoryName` instead of `Split-Path`,
`[System.IO.Directory]::SetCurrentDirectory` instead of `Set-Location`,
`[System.IO.File]::ReadAllText`/`ReadAllBytes` instead of `Get-Content`, and
`[System.IO.File]::Exists`/`[System.IO.Directory]::Exists` instead of
`Test-Path`, so that bootstrap and the target stages do not depend on those
cmdlets.

`System.Console` is the frozen **reporting primitive**. Every line Oracle-PathE
prints — bootstrap, semantic, publication-failure, publication-OK and guard
lines alike — is written with `[System.Console]::Out.WriteLine`, which:

- belongs to the same .NET runtime layer that is already required to execute the
  script at all, so its availability follows from the script executing;
- is **not** a PowerShell cmdlet, so no reporting surface depends on a module
  that the bootstrap phase may have just found unavailable;
- returns nothing and writes nothing into the PowerShell pipeline, so reporting
  cannot be confused with oracle output objects;
- throws an ordinary .NET exception if the channel is unavailable or closed;
  that failure is handled by §4.5, never by an unchecked path.

Two cmdlets that the predecessor did use are **eliminated entirely**, not
gated: all reporting that used `Write-Output` now goes through
`[System.Console]::Out.WriteLine`, and all iteration that used `ForEach-Object`
now uses the `foreach` language statement. Oracle-PathE therefore contains
**zero** `Write-Output` invocations, **zero** `ForEach-Object` invocations and
**zero** `Get-FileHash` invocations.

### 4.2 Gated facilities and the complete command taxonomy

Everything else that is a cmdlet or an external executable is a **GATED
FACILITY** and is availability-checked in the bootstrap phase, before its first
operational use anywhere in the file:

`python`, `Add-Type`, `Get-NetTCPConnection`, `Get-CimInstance`,
`ConvertTo-Json`, `ConvertFrom-Json`.

The gate list is **not** the completeness argument by itself. Completeness is
established by the following taxonomy invariant, which is normative here and is
a mandatory requirement on every review and on the regression test of §18:

> **Every command invocation (`CommandAst`) in the executable must belong to
> exactly one of four declared classes: (A) a script-local function defined
> before its first use; (B) an explicitly declared bootstrap primitive of §4.1;
> (C) an explicitly declared gated facility of §4.2 whose availability handling
> precedes its first operational use; (D) an explicitly declared external
> executable whose gate precedes its first invocation. A command invocation not
> covered by this taxonomy is a design-review failure.**

There must be **no undeclared operational command**. In the remediated revision
the enumeration is: 6 script-local functions (`Test-BootstrapFacility`,
`Get-Utf8FileSha256`, `Get-LowerHex`, `Get-CanonicalPath`, `New-Snapshot`,
`Take-Snapshot`), the 6 gated facilities listed above, and the 1 external
executable `python` — 28 `CommandAst` nodes in total, with no dynamic command
name, no alias, no `Invoke-*` mechanism and no invocation of an undeclared
cmdlet. `Write-Output`, `ForEach-Object` and `Get-FileHash` appear as **0**
command invocations and are therefore not gated at all: they are never used.

### 4.3 The checker cannot terminate the script

`Test-BootstrapFacility` is itself wrapped in `try`/`catch`, so the failure of
`Get-Command` itself is reported as an *unavailable facility* rather than
escaping as an uncaught terminating error. This is the structural difference
from the predecessor, whose unchecked first use escaped before any
classification.

### 4.4 Behaviour when a required facility is unavailable

The bootstrap phase sets a terminal `HARNESS_INVALID` outcome with
`TerminalStage = 'infrastructure_command_unavailable:<first missing facility>'`.
If `Get-NetTCPConnection` is among the missing facilities,
`listener_probe_outcome` becomes `COMMAND_UNAVAILABLE`; otherwise it remains
`NOT_REACHED`. No later stage runs. If the serialization facilities are
available, the oracle **publishes** the `HARNESS_INVALID / NO ETB SEMANTIC
RESULT` result; if they are not, the oracle exits with the documented
infrastructure exit code (see §9) and publishes nothing.

### 4.5 Reporting-channel failure model

Reporting through `[System.Console]::Out.WriteLine` can itself fail if the
stdout channel is unavailable or closed. The model is fail-closed and is
identical at both layers:

- at step 6 (terminal reporting) a reporting failure is an unexpected host
  failure: it reaches the top-level guard of §8, which exits `4` without
  deleting, retrying, repairing or rewriting anything. If publication had
  already succeeded, the published artifact **remains on disk**; its presence
  must be inspected on disk and must never be inferred from the exit code;
- inside the guard itself, the emergency reporting is wrapped so that a
  reporting failure cannot prevent the frozen `exit 4`.

No reporting failure can corrupt, delete or rewrite a published artifact, and
no reporting failure is ever converted into an ETB semantic verdict.

---

## 5. Oracle self-identity hashing

Oracle-PathE freezes **one** mechanism for establishing its own script/spec
identity:

> **Mechanism B — the .NET SHA-256 primitive.**

`Get-Utf8FileSha256` reads the file with
`[System.IO.File]::ReadAllBytes` and hashes it with
`[System.Security.Cryptography.SHA256]::Create()`. Availability of this
primitive follows from the PowerShell/.NET runtime already required to execute
the script; it is deterministic, reviewable, fail-closed and fully specified,
and it runs before any target probing.

Consequently `Get-FileHash` is **never** used by Oracle-PathE, and the
predecessor's ordering defect is eliminated by construction rather than merely
re-ordered. This also applies to the executable-hash stage of the target
binding sequence (§12), which uses the same primitive.

---

## 6. Command-availability ordering table (normative)

For every facility, the availability-check stage must strictly precede its
first-use stage.

| Facility | Availability check | First operational use | Ordering |
|---|---|---|---|
| `python` | bootstrap phase (`step 0`) | `step 2` config-reader subprocess | check < use |
| `Add-Type` | bootstrap phase (`step 0`) | `step 3` native type load | check < use |
| `Get-NetTCPConnection` | bootstrap phase (`step 0`) | `step 4` listener query inside `Take-Snapshot` | check < use |
| `Get-CimInstance` | bootstrap phase (`step 0`) | `step 4` process query inside `Take-Snapshot` | check < use |
| `ConvertFrom-Json` | bootstrap phase (`step 0`) | `step 4` package manifest parse | check < use |
| `ConvertTo-Json` | bootstrap phase (`step 0`) | `step 5` evidence serialization | check < use |
| `ConvertFrom-Json` | bootstrap phase (`step 0`) | `step 5` evidence readback validation | check < use |
| `Get-FileHash` | **not gated — not used at all** | **none** | vacuous |
| `Write-Output` | **not gated — not used at all** | **none** | vacuous |
| `ForEach-Object` | **not gated — not used at all** | **none** | vacuous |
| `Get-Command` | the bootstrap mechanism itself (§4.3) | only inside `Test-BootstrapFacility`, wrapped in `try`/`catch` | self-checked |
| `[System.Console]::Out.WriteLine` | **declared bootstrap primitive** (§4.1) | reporting only; never a semantic operation | not a cmdlet |
| `Get-LowerHex` | script-local function | defined L247, first used L649 | definition < use |

Measured on the **remediated** revision
(`V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.ps1`, 41 610 bytes, 772 lines,
SHA-256 `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb`):
the last bootstrap-availability call is at line 267; the earliest
gated-facility call is at line 277 (`python`); therefore the invariant holds
with a margin, and `Get-NetTCPConnection` is not reached before line 411, inside
`Take-Snapshot` (lines 403–531). These line numbers are recorded for this
candidate revision and must be re-measured by review; the stage ordering above
is the normative statement.

---

## 7. Infrastructure-failure model (expected, oracle-classifiable)

The following are **expected infrastructure failures** and are classified by
the oracle itself; they never escape:

| Condition | Outcome | `terminal_stage` family |
|---|---|---|
| a gated facility is unavailable at bootstrap | `HARNESS_INVALID` | `infrastructure_command_unavailable:*` |
| `python` cannot be resolved or launched for the config reader | `HARNESS_INVALID` | `config_reader_failure` |
| native type load (`Add-Type`) fails | `HARNESS_INVALID` | `native_type_load_failure` |
| P/Invoke invocation / marshaling / handle-close failure | `HARNESS_INVALID` | `*_path` stages |
| listener query raises or is unavailable | `ETB_UNSATISFIED` / `COMMAND_UNAVAILABLE` | `s0_listener` / `s1_listener` |
| process query raises | `ETB_UNSATISFIED` | `s0_process` / `s1_process` |
| the reporting channel fails at step 6 | unexpected host failure → guard → exit `4` | no stage: reporting failure is never a semantic stage |

Infrastructure problems and ETB semantic outcomes remain distinct: an
infrastructure problem is never silently converted into an ETB semantic
verdict, and an ETB semantic failure is never misclassified as
`HARNESS_INVALID`. Broad catching that would blur this boundary is prohibited.

---

## 8. Unexpected internal / host failure model

Oracle-PathE installs a **top-level `trap`** before anything else runs. It
exists solely for an unexpected internal or host failure for which no designed
branch applies. It converts such a failure into the documented fail-closed
terminal state, with the emergency reporting itself guarded:

```
try {
  ORACLE_PATH_E_UNEXPECTED_HOST_FAILURE
  ORACLE_PATH_E_FINAL_CLASSIFICATION=HARNESS_INVALID
  ORACLE_PATH_E_SEMANTIC_RESULT=NONE
} catch {
  # emergency-report failure is swallowed; nothing about it is printed
}
exit 4
```

The implementation is normative in three respects:

- the guard invokes **no cmdlet**: its reporting is
  `[System.Console]::Out.WriteLine` over frozen string constants only, so the
  guard cannot fail because a module it needs is unavailable — precisely the
  failure class it exists to convert;
- the three reporting writes are wrapped in a local `try`/`catch` whose `catch`
  body is empty, and `exit 4` is deliberately **outside** that `try`/`catch`.
  The normative invariant is:
  **an exception inside the emergency reporting path cannot prevent `exit 4`**;
- the guard is narrow. It does not absorb the classified branches: the
  publication region keeps its own local `try`/`catch` (`exit 3`), the
  expected-infrastructure branch keeps its own `exit 2`, and a normal
  publication keeps its own `exit 0`. Only an unexpected failure reaches the
  guard.

Consistent with the inherited frozen discipline, no exception message, stack,
provider text or environment data is captured, persisted or printed. There is
therefore **no unexplained "any arbitrary terminating error" bucket** and **no
reachable undocumented `exit 1` path**: every termination of Oracle-PathE maps
to a classified branch or to this documented guard.

Because the guard can also catch a failure raised *after* a successful
publication (§4.5, §14 item 12), later governance interprets `exit 4` as
*fail-closed; artifact presence must be inspected on disk and is never inferred
from the exit code*.

---

## 9. Exit-code contract

| Exit code | Meaning |
|---|---|
| `0` | the oracle completed and **published** one of the three result classes |
| `2` | an **expected infrastructure failure** was classified, but the result could not be published because a publication facility was itself unavailable. This branch is reached **before any output path is created**, so no output artifact exists (fail-closed) |
| `3` | the publication/control stage failed **after** the semantic outcome was decided. This code **does not mean that no output artifact exists**: a control failure can occur after one or more FINAL moves have already happened |
| `4` | an **unexpected internal or host failure** reached the top-level guard (fail-closed). The guard emits its frozen classification when its reporting channel is usable, and a failure of that channel does not change the exit code. The guard can also catch a failure raised after a successful publication |

**Artifact-presence rule (normative).** Exit codes `3` and `4` are *not*
artifact-absence assertions. For both, artifact presence must be established by
inspecting the fail-closed publication state on disk, and must never be inferred
from the exit code. Only exit `2` asserts that no output artifact was created,
because that branch is reached before any output path is touched. In every case
there is no cleanup, no retry, no overwrite and no automatic repair.

The predecessor's undeclared `exit 1` accidental path no longer exists as an
undocumented outcome: any value other than the four above is a defect of the
artifact, not a contract outcome.

---

## 10. Target semantic question (unchanged)

Oracle-PathE answers the **same** ETB semantic question as Oracle-PathD. The
requirement is not weakened or reinterpreted because Path-D terminated before
reaching it.

| Item | Value |
|---|---|
| endpoint | `http://127.0.0.1:4096` |
| endpoint family | IPv4, host `127.0.0.1`, port `4096`, scheme `http` |
| listener predicate | `LocalAddress = 127.0.0.1`, `LocalPort = 4096`, `State = Listen` |
| expected target executable SHA-256 | `578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35` |
| accepted target path (raw) | `C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe` |
| package | `opencode-ai` |
| expected version | `1.18.11` |
| declared bin | `opencode` |

Mode P (pre-existing target) is preserved: no endpoint discovery, no fallback,
no alternate port, no `localhost` alias, no IPv6 alternate, no Mode L, no
OpenCode start/restart, no HTTP, no `/doc`, no `/session`, no provider/model
call. None of these values was probed in this design round.

---

## 11. Listener ownership

The exact listener query belongs **only** to Oracle-PathE, and it is executed
only inside the snapshot stage after the bootstrap phase has established that
`Get-NetTCPConnection` exists.

There is **no** external authorization-layer target or listener pre-probe. This
design round itself performed **0 listener queries, 0 `Get-NetTCPConnection`
executions, 0 port-4096 probes and 0 endpoint probes**. The historical Path-D
and out-of-band observations are **not** reused as Path-E evidence and never
will be: only Oracle-PathE's own frozen query inside a consumed Path-E attempt
may contribute to a Path-E execution observation.

---

## 12. Target-binding sequence (preserved)

```
listener uniqueness
→ OwningProcess
→ PID
→ Win32_Process
→ ExecutablePath
→ CreationDate
→ PID + CreationDate.Ticks process-instance identity
→ CreateFileW / GetFinalPathNameByHandleW canonicalization
→ exact canonical path equality
→ binary SHA-256 (observed and accepted)
→ package identity (name / version / declared bin, bin canonicalized and compared)
→ S0
→ S1
→ S0/S1 continuity over the frozen field set
```

No step was removed, reordered or weakened. The only implementation change is
that binary SHA-256 now uses the .NET primitive (§5), which is not a semantic
change to the binding sequence.

---

## 13. Result-class model

Exactly three Oracle semantic classes exist and are the only values ever
assigned to the semantic outcome:

```
ETB_SATISFIED
ETB_UNSATISFIED
HARNESS_INVALID / NO ETB SEMANTIC RESULT
```

No fourth class is introduced. The historical Path-D governance phrase
`UNCLASSIFIED CONTROL FAILURE` is **not** a class of this oracle; it describes a
Path-D governance outcome record and appears in Oracle-PathE only inside a
non-normative comment explaining what this oracle must not resurrect. No
`PASS`, `FAIL`, `PARTIAL`, `UNKNOWN`, `PROBABLE` or `RETRY` is a result class;
`PASS`/`FAIL` appear only as `$Checks` status values, exactly as in the
predecessor. No result is preselected: the initial semantic value is
`HARNESS_INVALID` only as the fail-closed default before any evaluation.

---

## 14. Publication model (fail-closed, no overwrite)

The Path-E output namespace is unique and initially absent. Publication
preserves the inherited discipline:

1. six-path occupancy precondition — any occupied evidence/manifest/result path
   in either its TEMP or FINAL form fails closed with a constant marker;
2. output directory created with `[System.IO.Directory]::CreateDirectory`;
3. TEMP creation with `[System.IO.FileMode]::CreateNew` and
   `[System.IO.FileShare]::None` (exclusive, no overwrite);
4. write, then `Flush($true)`;
5. full byte read-back comparison;
6. terminal-LF, no-double-LF and no-BOM assertions;
7. JSON validation through `ConvertFrom-Json` including
   `schema_version`/`outcome`/`listener_probe_outcome` agreement;
8. SHA-256 of the evidence bytes and manifest line construction
   (`<digest>␠␠<path>`), with the same write/read-back/validation discipline;
9. the result artifact, including the runtime-constructed U+2014 em dash from
   an ASCII-only source;
10. publication order **evidence → manifest → result last**, each with
    post-move byte verification and, for evidence and manifest, post-move
    semantic re-validation;
11. any failure in this region raises, is caught by a narrow local
    `try`/`catch`, and yields the frozen `HARNESS_INVALID` evidence-machinery
    outcome with a constant publication-failure surface — no exception text is
    persisted;
12. that narrow `try`/`catch` covers publication only. Terminal reporting
    happens after it, through the reporting primitive of §4.1. If reporting
    fails after a successful publication, the failure reaches the guard of §8:
    nothing is deleted, retried, repaired or rewritten, the three published
    artifacts stay on disk exactly as verified by step 10, and their presence
    must be inspected on disk rather than inferred from the exit code.

No Path-D output path is referenced anywhere in Oracle-PathE.

---

## 15. Namespace reservations (design only; nothing created)

Reserved for the future Path-E lineage and **not created** in this round:

- runtime namespace: `docs/v0.3/evidence/etb-execution-path-e/`
- evidence: `…/ETB_EVIDENCE.json`, `…/ETB_EVIDENCE.json.tmp`
- manifest: `…/MANIFEST.sha256`, `…/MANIFEST.sha256.tmp`
- result: `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_E.md{,.tmp}`
- claims: `docs/v0.3/evidence/ETB_PATH_E_AUTHORIZATION_USE.claim{,.tmp}` and
  `docs/v0.3/evidence/ETB_PATH_E_ATTEMPT_USE.claim{,.tmp}`

The derived reserved namespace is **11 paths** in total: 1 runtime directory,
2 evidence files (TEMP + FINAL), 2 manifest files, 2 result files, 2
authorization-claim files and 2 attempt-claim files. The six output paths
asserted by the §14 occupancy precondition are the evidence/manifest/result
subset of that namespace. Current occupancy is **0 / 11** — nothing in the
namespace exists.

The future Path-E execution-authorization design governs those claims. No
Path-E budget is consumed, or even operationally active, in this round.

Evidence schema identity for the future lineage: `devrelay-etb-v1-path-e`.
Path-E specific provenance fields (`oracle_path_e_commit`,
`oracle_path_e_spec_sha256`, `oracle_path_e_script_sha256`) are recorded as
`UNKNOWN` until a future independent approval record populates them; they are
never inferred, defaulted or fabricated.

---

## 16. Budget model (design only)

No consumable Path-E budget exists in this round. The future Path-E
authorization-design stage may propose a fresh
`AUTHORIZATION_USE_BUDGET = 1 OF 1` and `ETB_ATTEMPT_BUDGET = 1 OF 1`, but those
budgets must not become executable merely because an Oracle-PathE design
exists. Oracle acceptance and Path-E authorization acceptance remain separate
gates.

---

## 17. Effectivity and status

```
ORACLE-PATHE = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE
PATH-E EXECUTION AUTHORIZATION = NOT DESIGNED / NOT ACCEPTED
PATH-E AUTHORIZATION USE = NOT AVAILABLE FOR CONSUMPTION
PATH-E ETB ATTEMPT = NOT AVAILABLE FOR CONSUMPTION
PATH-E ETB EXECUTION = NOT AUTHORIZED
PATH-E RUNTIME OCCUPANCY = 0 / 11
AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED
PATH-D = EXHAUSTED / CLOSED / IMMUTABLE
```

This candidate grants no execution effectivity and collapses no acceptance
stage. It creates no ETB observation and changes no authoritative result.

---

## 18. Static verification and regression test

Performed on the remediated candidate revision, **statically only** — the
executable was parsed, never executed:

| Test | Result |
|---|---|
| PowerShell parser errors | `0` |
| ASCII-only source, no BOM, CR = 0, exactly one terminal LF | pass (`MAXBYTE = 125`, 772 LF) |
| `CommandAst` nodes enumerated and classified | `28`, taxonomy violations `0` |
| Dynamic command name / alias / `Invoke-*` / `Invoke-Expression` | `0` |
| `Write-Output` command invocations | `0` |
| `ForEach-Object` command invocations | `0` |
| `Get-FileHash` command invocations | `0` |
| `Split-Path` / `Set-Location` / `Get-Content` / `Test-Path` invocations | `0` each |
| Guard body `CommandAst` count | `0` (frozen `[System.Console]::Out` constants only) |
| Bootstrap check precedes first gated-facility call | pass (check ≤ L267 < use L277) |
| `Get-NetTCPConnection` only inside the snapshot stage | pass (L411 within L403–531) |
| `[System.Console]::Out.WriteLine` sites | `20` (3 of them inside the guard) |
| `Get-Command` only inside the wrapped checker | pass (L194 within L192–199) |
| No Path-D output namespace reference | `0` |
| No Path-D claim path used as Path-E control state | `0` |
| No excluded oracle identity used as an active name | `0` each |
| Result class set exactly three | pass (the only writers of the semantic outcome are the three classes) |
| No retry / fallback / sleep logic | pass (`Start-Sleep = 0`, `while = 0`; only bounded byte-compare and dash-scan `for` loops) |
| Exit-code surface exactly `0 / 2 / 3 / 4` | pass (L772 / L582 / L760 / L112) |

**Regression test for the Path-D failure (static, non-target-reaching):**

- *Property A* — Oracle-PathE performs **zero** `Get-FileHash` command calls
  (proved by AST command inventory), so the predecessor's
  use-before-availability sequence **cannot** recur.
- *Property B* — every bootstrap availability check is issued strictly before
  the first call of every gated facility, so no gated facility can be used
  before its availability has been established.
- *Property C* — an unavailable required facility sets the terminal
  `HARNESS_INVALID` outcome with
  `terminal_stage = infrastructure_command_unavailable:<facility>` and reaches
  the oracle's own publication/exit path instead of terminating at an unchecked
  first use.
- *Property D (enumeration completeness)* — the regression is **not** allowed to
  rest on a hand-maintained list of expected names. Under the §4.2 taxonomy
  invariant the enumeration must cover **every** `CommandAst` in the executable
  and prove class membership for each one, so a newly introduced facility that
  the author forgot to add to the table fails the property instead of passing
  silently. Equivalently: the test fails whenever the enumerated command count
  exceeds the declared taxonomy entries.
- *Property E (guard fail-closed)* — the guard's reporting writes sit inside a
  local `try`/`catch` with `exit 4` outside it, and the guard body contains
  **no** `CommandAst`; therefore neither an unavailable cmdlet nor a failing
  reporting channel can prevent `exit 4`. This is proved by AST inspection of
  the guard body plus the isolated language-semantics probe recorded in §21,
  which executes no DevRelay artifact and touches no DevRelay path.

Therefore the property "if `Get-FileHash` is unavailable at the relevant
boundary, Oracle-PathE reaches the intended infrastructure-failure handling path
instead of terminating at an unchecked first use" holds **vacuously and
structurally**: the oracle never reaches such a boundary because it never uses
that facility, and every command it does use is enumerated and classified under
the taxonomy invariant above. The test used no production runtime namespace,
performed no listener query and consumed no budget.

---

## 19. Non-claims

Oracle-PathE is

- NOT a SIC result;
- NOT a P6 result;
- NOT a G0.5 result;
- NOT a Mode-B result;
- NOT a Case-C authorization;
- NOT an adoption authorization;
- NOT an ETB semantic result of any kind while it remains a design candidate.

---

## 20. Next stage

```
NEXT STAGE = THIRD-PARTY INDEPENDENT REVIEW OF ORACLE-PATHE DESIGN CANDIDATE
```

That review must explicitly attempt to reproduce or detect the historical
Oracle-PathD `Get-FileHash`-before-availability-gate defect, and must
independently re-measure the ordering invariant of §6. It must additionally
verify, on the remediated revision:

- `Write-Output` actual `CommandAst` count = `0`;
- `ForEach-Object` actual `CommandAst` count = `0`;
- the guard body has no cmdlet dependency;
- an emergency-reporting failure still terminates at `exit 4`;
- complete `CommandAst` taxonomy coverage under §4.2;
- no reachable undocumented `exit 1`;
- the historical `Get-FileHash` defect remains absent;
- Path-E runtime occupancy is correctly represented as `0 / 11`.

Acceptance bookkeeping is **not** performed in this round.

---

## 21. Remediation record (third-party design-review findings)

The first Oracle-PathE design candidate
(`3b085dae4ff89512bcf23f80043b78ddc82a490f`) was reviewed independently and
returned `REQUEST_CHANGES` with P0 = 0, P1 = 1, P2 = 1, P3 = 3. This revision
remediates exactly those accepted findings and adds no other change.

| Finding | Severity | Accepted defect | Remediation in this revision |
|---|---|---|---|
| P1-1 | P1 | the guard and every reporting surface used the ungated cmdlet `Write-Output`, so an environment in which that cmdlet's module is unavailable made the guard abort before `exit 4` and terminate with an undocumented exit `1` | all 20 reporting sites now use the declared bootstrap primitive `[System.Console]::Out.WriteLine`; the guard's reporting is wrapped with `exit 4` outside it; `Write-Output` command invocations = `0` |
| P2-1 | P2 | `Write-Output` and `ForEach-Object` were operational cmdlets outside the declared facility model | both are eliminated rather than gated: `Write-Output` → reporting primitive, `ForEach-Object` → `foreach` language statement (`ForEach-Object` invocations = `0`); §4.2 now imposes the taxonomy invariant on every command invocation |
| P3-1 | P3 | the regression completeness claim overstated what had been enumerated | §18 Property D adds the enumeration-completeness obligation and the "enumerated command count > declared taxonomy entries ⇒ fail" rule |
| P3-2 | P3 | the exit-`3` wording could be read as "no output artifact exists" | §9 forbids inferring artifact presence from exit `3` or `4`; §14 item 12 records the post-publication reporting behaviour |
| P3-3 | P3 | Path-E runtime occupancy was reported as `0 / 6` | §15 derives the reserved namespace as `11` paths and reports occupancy `0 / 11`; `0 / 6` survives only as the six-output-path subset asserted by the §14 occupancy precondition |

The remediated artifact remains a design candidate:
`NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE`. This remediation round performed no
execution of Oracle-PathE or Oracle-PathD, no ETB execution, no listener query,
no endpoint probe, no claim creation, no budget creation or consumption and no
Path-D modification. Every check listed in §18 is static/parser/AST analysis,
plus one isolated language-semantics probe (nested `pwsh -NoProfile`, containing
no DevRelay artifact and touching no DevRelay path) which confirms the two guard
properties directly: a simulated host failure with a working emergency channel
terminates at `exit 4`, and the same failure with a throwing emergency channel
**still** terminates at `exit 4` because the inner `catch` suppresses only the
reporting failure.
