# DEVRELAY v0.3-E — PRE-ETB EXECUTION ORACLE: PATH F DESIGN CANDIDATE

- **Artifact identity:** `Oracle-PathF`
- **Canonical lineage token:** `PATH_F`
- **Canonical oracle token:** `ORACLE_PATH_F`
- **Companion executable:** `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.ps1`
- **Status:** `DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE`
- **Design round:** Path-F successor ETB lineage, design and governance only
- **Predecessor lineage:** `PATH E` — `EXHAUSTED / CLOSED`
- **Execution authority created by this artifact:** `NONE`

This artifact is a design candidate. It executes nothing, creates no claim, creates
and consumes no budget, occupies no runtime namespace path, and modifies no
predecessor artifact. Every operational statement below is a specification of a
future, separately authorized round, not a description of anything that happened.

---

## 1. Owner decision and lineage identity

```
OWNER DECISION = OPEN A NEW ETB LINEAGE
PREDECESSOR LINEAGE = PATH E
NEW LINEAGE = PATH F — NEW ETB ATTEMPT
NEW EXECUTION ORACLE = Oracle-PathF
OWNER NAMING DECISION = PATH-F / Oracle-PathF
```

This is an explicit Owner naming decision. The Owner did **not** authorize: a
Path-E retry; Path-E claim reuse; a Path-E budget reset; a Path-E Oracle
re-invocation; a Path-E repair-and-rerun; promotion of the raw Path-E result; ACL
restoration; a Path-D reopen; or any ETB execution in this round.

**This is a NEW lineage and explicitly NOT** a Path-E retry, a Path-E
continuation, a Path-E budget reset, a Path-E claim reuse, a Path-E repair, a
Path-D retry, `Recovery-R3` (unless separately and explicitly defined),
`Oracle-PathE` v2, or an Oracle-PathD reuse. It is a new lineage with a new
one-shot authority lifecycle that must be designed, reviewed, accepted and
authorized independently.

### 1.1 Carried-forward predecessor terminal facts (preserved, not reinterpreted)

```
RAW PATH-E ORACLE OBSERVATION = ETB_UNSATISFIED
RAW PATH-E RESULT PROMOTION ELIGIBILITY = REJECTED / BLOCKED
PATH-E ETB SEMANTIC RESULT = NONE
PATH-E AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
PATH-E ETB ATTEMPT = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE
ORACLE-PATHE INVOCATIONS = 1 OF 1 / MAXIMUM REACHED
PATH-E RETRY AUTHORITY = NONE
PATH-E namespace occupancy = 6 / 11
AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED
PATH-D = EXHAUSTED / CLOSED / IMMUTABLE
```

### 1.2 Path-E lineage closure declared by this round

Per the recovered `PATH_D_TO_PATH_E_SUCCESSOR_PRECEDENT` (commit `3b085dae`,
`docs(v03e): define Path-E execution oracle candidate`), a successor-lineage
design round declares the predecessor terminal in the exact predecessor-era
vocabulary. This round therefore records:

```
PATH-E LINEAGE = EXHAUSTED / CLOSED
```

Path E is not reopened, not repaired and not rerun. Closure is a governance
statement about the lineage, **not** an ETB semantic result: it does not promote
the raw Path-E observation, does not convert `PATH-E ETB SEMANTIC RESULT = NONE`
into anything, and does not create retry authority. The three-term canonical form
`EXHAUSTED / CLOSED / IMMUTABLE` is not used here because the predecessor
precedent at this stage uses the two-term form; the third term enters the
repository vocabulary only through a later, separate round.

---

## 2. Historical predecessors and reviewed defects

Neither predecessor artifact is modified, wrapped, sourced, patched, repaired or
reused by this design. Both remain frozen exactly as committed.

### 2.1 Oracle-PathD — reviewed implementation defect

`Get-FileHash` was used for oracle self-identity at predecessor lines 117/118
while its availability was only checked at line 189: an ungated facility was used
before its own availability gate. The Path-D operational round terminated as an
unclassified control failure with `PATH-D ETB SEMANTIC RESULT = NONE`. The defect
is recorded as `YES / ACCEPTED / NOT REPAIRED`.

### 2.2 Oracle-PathE — operational lessons

| # | Lesson | Classification |
|---|--------|----------------|
| L1 | A pre-consumption claim-create failure was followed by a RE-ATTEMPT under a mutated permission state instead of a fail-closed stop | unauthorized re-attempt |
| L2 | An access-control list was mutated during the operational round | unauthorized environment mutation; semantic effect `NON-SEMANTIC`; ACL state `NOT NORMALIZED`; restoration `NOT AUTHORIZED BY THAT ROUND`; rollback scripts are `NOT AUTHORITY` |
| L3 | The authorization artifact and the accepted Oracle specification used incompatible provenance wording (frozen values vs. `UNKNOWN`) | cross-document wording tension; reporting/governance, non-semantic |
| L4 | Runtime namespace occupancy was reported as 2/11 while the actual occupancy was 6/11 | reporting variance; reporting-only, non-semantic |
| L5 | The operational round required an escalated file-access mode | process variance; nonblocking; grants nothing |

Path-F closes L1, L2, L3 and L5 structurally in this design (§7, §8, §9, §19) and
closes L4 by defining exact namespace accounting in §18.

---

## 3. Scope of this design candidate

In scope: this specification; the companion executable; the governance-surface
bookkeeping for the round. Out of scope: execution authorization; ETB execution;
claim creation; budget consumption; runtime namespace occupation; any
modification of Path-E or Path-D artifacts; ACL restoration or normalization;
result promotion; push, tag or release.

At design time the Path-F runtime namespace occupancy is `0 / 11` (§18). No
Path-F path exists on disk.

---

## 4. Bootstrap safety phase (normative)

The bootstrap phase runs before every other stage.

### 4.1 Assumed bootstrap primitives

Assumed available because the script is executing under Windows PowerShell / .NET
at all:

- PowerShell language constructs: statements, functions, operators, arrays,
  ordered hashtables, `if`/`elseif`/`else`, `foreach`, `try`/`catch`/`finally`,
  `throw`, `trap`.
- Type literals for `System.*` types and static .NET members of the runtime
  libraries already loaded: `System.IO.Path`, `System.IO.File`,
  `System.IO.Directory`, `System.IO.FileStream`, `System.IO.FileMode`,
  `System.IO.FileAccess`, `System.IO.FileShare`, `System.Text.StringBuilder`,
  `System.Text.UTF8Encoding`, `System.Text.Encoding`, `System.Guid`,
  `System.IntPtr`, `System.Security.Cryptography.SHA256`,
  `System.DateTimeOffset`, `System.Console`, `System.Globalization.CultureInfo`,
  `System.Environment`.

None of these is a cmdlet. The executable therefore uses
`[System.IO.Path]::GetDirectoryName` instead of `Split-Path`,
`[System.IO.Directory]::SetCurrentDirectory` instead of `Set-Location`,
`[System.IO.File]::ReadAllText` / `ReadAllBytes` instead of `Get-Content`, and
`[System.IO.File]::Exists` / `[System.IO.Directory]::Exists` instead of
`Test-Path`.

`System.Console` is the frozen reporting primitive: a .NET static type of the same
runtime layer required to execute the script at all, not a PowerShell cmdlet, and
the only output channel the executable uses (`[System.Console]::Out.WriteLine`,
deterministic single-line stdout). A write through it returns nothing and adds
nothing to the pipeline. If the channel is unavailable the write throws like any
other .NET call: at step 6 the top-level guard converts it into the frozen exit 4,
and inside the guard an emergency-report failure is swallowed so the
process-control exit code is unaffected.

### 4.2 Gated facilities and the complete command taxonomy

Gated facilities: `python`, `Add-Type`, `Get-NetTCPConnection`, `Get-CimInstance`,
`ConvertTo-Json`, `ConvertFrom-Json`. Each is availability-checked in the
bootstrap phase before its first operational use anywhere in the file.

Every command invocation in the executable belongs to exactly one of four
declared classes:

| Class | Meaning | Path-F count |
|-------|---------|--------------|
| A | script-local function, defined before use | 19 |
| B | declared bootstrap primitive (not a cmdlet) | 0 command nodes |
| C | declared gated facility, availability-handled before first use | 8 |
| D | declared external executable, gated before first invocation | 0 |

Total `CommandAst` nodes: **28** = 19 class A + 8 class C + 1 `Get-Command`
invocation inside the wrapped availability checker. There is no dynamic command
name, no alias and no `Invoke-*`. Class B contributes no command nodes because the
assumed primitives are language constructs and .NET members, not commands; class D
contributes none because no external executable other than the gated `python`
config reader is invoked.

### 4.3 The checker cannot terminate the script

`Test-BootstrapFacility` is itself wrapped in `try`/`catch` so that the failure of
the checker (`Get-Command` unavailable) is reported as an unavailable facility
instead of terminating the script.

### 4.4 Behaviour when a required facility is unavailable

Terminal `HARNESS_INVALID` with `TerminalStage = 'infrastructure_command_unavailable:<first missing>'`;
`listener_probe_outcome = 'COMMAND_UNAVAILABLE'` if the missing facility is
`Get-NetTCPConnection`, otherwise `NOT_REACHED`. This is a governance/control
failure, never a fourth ETB semantic class (§16).

### 4.5 Reporting-channel failure model

Reporting is deterministic single-line stdout through the §4.1 primitive. A
reporting failure before publication terminates through the top-level guard
(exit 4). A reporting failure **after** a successful publication does not delete,
retry, repair or rewrite anything: the artifact presence must be inspected on
disk, never inferred from the exit code.

---

## 5. Oracle self-identity hashing

Mechanism B is preserved unchanged: self-identity is computed with .NET SHA-256
(`[System.Security.Cryptography.SHA256]::Create()` over
`[System.IO.File]::ReadAllBytes(...)`, exposed as `Get-Utf8FileSha256`).
`Get-FileHash` is **never** used (`CommandAst` count 0), which closes the reviewed
Path-D defect structurally.

The executable reports, as runtime observations:

```
ORACLE_PATH_F_SCRIPT_SHA256 = <observed>
ORACLE_PATH_F_SPEC_SHA256   = <observed>
```

These are **observations**, not provenance. They are recorded in the evidence
artifact under distinct field names (`oracle_self_identity_sha256`,
`oracle_self_identity_spec_sha256`) and are explicitly not the provenance fields
of §19.

---

## 6. Command-availability ordering table (normative)

Rule: **check stage < first-use stage**, measured on the Path-F revision.

| Gated facility | Availability check | First operational use | Ordering |
|----------------|--------------------|-----------------------|----------|
| `python` | bootstrap loop L262-264 (call L263) + re-check L376 | L386 | satisfied |
| `Add-Type` | bootstrap loop L262-264 (call L263) | L463 | satisfied |
| `Get-NetTCPConnection` | bootstrap loop L262-264 (call L263) | L520 (inside `Take-Snapshot` L512-640) | satisfied |
| `Get-CimInstance` | bootstrap loop L262-264 (call L263) | L555 | satisfied |
| `ConvertTo-Json` | bootstrap loop L262-264 (call L263) + dedicated check L266 | L749 | satisfied |
| `ConvertFrom-Json` | bootstrap loop L262-264 (call L263) + dedicated check L267 | L618 | satisfied |

Last bootstrap-availability call: **L376**. Earliest gated-facility use: **L386**.
`Get-NetTCPConnection` is not reached before L520. No reachable undocumented
`exit 1` exists (§12).

---

## 7. Pre-publication write-viability gate (normative; new in Path-F)

Path-F adds step 1.5, a deterministic **pre-publication write-viability gate**,
placed after the bootstrap phase and the self-identity stage and before the config
read, before every target probe and before any publication step (region
L305-365, marker reported at L360).

Purpose: prove, **without consuming one-shot authority and without creating any
governed path**, that this process can create, write, read back and delete a
non-reserved probe file in each directory it will later publish into, using the
file-access mode that is **already established**. This closes Path-E lessons L1,
L2 and L5: a permission failure must be discovered before any irreversible step,
and it must never be answered by mutating an access-control list or by
re-attempting after such a mutation.

Normative rules:

1. The gate uses .NET only. It invokes no cmdlet and no external executable, and
   it is therefore not a gated facility.
2. Probe paths are **not** part of the reserved namespace: they are
   `.path-f-write-viability-probe-<guid>.tmp` files created with
   `[System.IO.FileMode]::CreateNew` and `[System.IO.FileShare]::None`, written,
   flushed with `Flush($true)`, read back byte-for-byte, and **deleted** again. No
   claim, evidence, manifest or result path is touched; no Path-E or Path-D path
   is touched.
3. The gate creates **no** governed TEMP claim and consumes **no** budget. It
   observes capability only.
4. The gate runs before every publication step and before any governed path
   creation.
5. If any probe step fails, the gate **fails closed**: terminal outcome
   `HARNESS_INVALID`, `TerminalStage = 'write_viability:<directory>'`,
   `listener_probe_outcome = 'NOT_REACHED'`, process exit 2, no governed path
   created, no retry, no ACL change.
6. If a probe file cannot be deleted, the gate fails closed and records the
   residue path; the marker line reports it for on-disk inspection. It never
   retries and never repairs.
7. The gate mutates no access-control list and invokes no ACL command
   (`acl_mutation_attempted = false`, `acl_commands_used = 0`).

Marker line:

```
ORACLE_PATH_F_WRITE_VIABILITY ok=<true|false> stage=<stage> residue=<paths>
```

The gate result is recorded in the evidence artifact under `write_viability`
(`gate`, `directories`, `ok`, `stage`, `residue`, `acl_mutation_attempted`,
`acl_commands_used`).

---

## 8. Access-control-list and environment mutation policy (normative)

1. No access-control list is ever read, enumerated, modified, restored,
   normalized or repaired by the Oracle-PathF executable. Command counts for
   `icacls`, `Set-Acl` and `Get-Acl` are all 0.
2. If the established permission mode cannot support publication, the run fails
   closed at the write-viability gate with `HARNESS_INVALID` and no ETB semantic
   result. It never improvises a permission change.
3. No elevation, no package installation, no `PATH` mutation and no system-scope
   environment change is performed. The only environment interaction is the
   process-scoped `PYTHONPATH` value required by the config reader: it is set with
   `[System.Environment]::SetEnvironmentVariable(..., 'Process')` immediately
   before that subprocess and restored to its prior value (or removed) in a
   `finally` block. This is a process-local, restored change, it occurs before any
   irreversible step, and it grants no authority.
4. ACL restoration or normalization is **out of scope** for this round and for
   the oracle itself. Any future ACL repair requires separate Owner
   authorization. Rollback scripts are **not authority**.
5. A permission failure is never a reason to mutate the environment: it is a
   fail-closed outcome (§7, §10).

---

## 9. Sandbox and file-access execution mode policy (normative)

1. The required file-access mode must be **established before** the
   write-viability gate runs. The gate observes the established mode; it never
   escalates it.
2. A future Path-F execution authorization record must state the required mode
   explicitly and must not create escalation authority.
3. If the established mode is insufficient, the run fails closed at the gate with
   `HARNESS_INVALID`. No escalation may occur after the irreversible sequence
   begins, and no escalation may be attempted in response to a failure.
4. The escalated file-access mode observed during the Path-E operational round is
   classified as nonblocking process variance (lesson L5). It grants nothing to
   Path-F and is not inherited as authority.

---

## 10. Infrastructure-failure model (expected, oracle-classifiable)

| Terminal stage | Meaning | Outcome |
|----------------|---------|---------|
| `write_viability:<directory>` | pre-publication write capability not provable (new in Path-F) | `HARNESS_INVALID`, no semantic result, exit 2 |
| `infrastructure_command_unavailable:<first missing>` | a gated facility is unavailable | `HARNESS_INVALID`, no semantic result |
| `config_reader_failure` | the config reader subprocess failed or returned an unusable value | `HARNESS_INVALID`, no semantic result |
| `native_type_load_failure` | the P/Invoke canonicalization type could not be loaded | `HARNESS_INVALID`, no semantic result |
| `s0_listener` / `s1_listener` | listener snapshot not uniquely resolvable | `HARNESS_INVALID`, no semantic result |
| `s0_process` / `s1_process` | process snapshot not uniquely resolvable | `HARNESS_INVALID`, no semantic result |

None of these is a fourth ETB semantic class; all are governance/control failures.

---

## 11. Unexpected internal / host failure model

A top-level `trap` guard (L144-152) covers every failure the staged model does not
classify:

```
ORACLE_PATH_F_UNEXPECTED_HOST_FAILURE
_FINAL_CLASSIFICATION = HARNESS_INVALID
_SEMANTIC_RESULT = NONE
exit 4
```

The guard body contains **0** command invocations, so it cannot itself depend on
an ungated facility. `exit 4` sits outside the inner empty `catch`, so an
exception raised while emergency-reporting cannot prevent the exit.

---

## 12. Exit-code contract

| Exit | Meaning | Artifact assertion |
|------|---------|--------------------|
| 0 | a semantic result was classified and published | result artifact present and validated |
| 2 | no result artifact exists; reached before any output path is touched (bootstrap failure, serialization/validation unavailable, or pre-publication write-viability failure) | **no** artifact; this is the only exit that asserts absence |
| 3 | `HARNESS_INVALID` evidence-machinery outcome published | presence must be inspected on disk |
| 4 | unexpected internal / host failure | presence must be inspected on disk |

Exactly four exit codes exist: 0, 2, 3, 4. Path-F introduces **no new exit code**:
the write-viability failure reuses exit 2, because it is precisely the
"no artifact was created and no output path was touched" case. Exits 3 and 4 are
not artifact-absence assertions.

---

## 13. Target semantic question (unchanged)

The ETB question, target identity and acceptance values are inherited unchanged:

- endpoint `http://127.0.0.1:4096`, IPv4;
- listener predicate: `LocalAddress` / `LocalPort` / `State = Listen`;
- expected target path
  `C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe`;
- expected target SHA-256
  `578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35`;
- package `opencode-ai`, version `1.18.11`, declared bin `opencode`.

Path-F changes none of these values. It changes how the oracle proves it may
publish, how it binds provenance, and how it refuses to retry.

---

## 14. Listener ownership

Listener query ownership belongs exclusively to the Oracle-PathF executable. The
authorization layer must not restate, amend, weaken or extend the listener
predicate, the listener uniqueness rule or the target-binding sequence. A listener
probe result is a control observation, not an ETB semantic result.

---

## 15. Target-binding sequence (preserved)

Target-binding **ownership** belongs exclusively to the Oracle-PathF executable: the
sequence, its order, its uniqueness rules and its fail-closed outcomes are owned
by this specification and are not restated, amended, weakened or extended by any
authorization artifact. The authorization layer may require that the sequence
exists; it may not re-specify it.

Unchanged from the accepted Oracle-PathE design: canonical path resolution through
`GetFinalPathNameByHandleW` (P/Invoke, loaded with the single gated `Add-Type`
call), PID resolution through `Win32_Process`, snapshot acquisition at two
stages (S0/S1), continuity evaluation, expected-hash comparison against the
canonicalized target, package name/version/bin verification, and the exit-2 path
when the target cannot be bound.

---

## 16. Result-class model

Exactly three ETB semantic classes exist:

```
ETB_SATISFIED
ETB_UNSATISFIED
HARNESS_INVALID / NO ETB SEMANTIC RESULT
```

There is no fourth ETB semantic class. `PASS`, `FAIL`, `PARTIAL`, `UNKNOWN`,
`PROBABLE` and `RETRY` are not classes. Governance/control-failure descriptors
(§10, §11) remain distinct from ETB semantic classes; `UNCLASSIFIED CONTROL
FAILURE` is a Path-D governance phrase, not a class.

A raw Path-F result **must not** become authoritative in the operational session.
It must pass its own independent review, bookkeeping and confirmation lifecycle
before any promotion question is even asked:

```
raw result published by the oracle
  -> FRESH QUALIFYING THIRD-PARTY INDEPENDENT RESULT REVIEW
  -> acceptance bookkeeping commit
  -> independent confirmation of that bookkeeping
  -> only then may promotion eligibility be evaluated
```

Until that lifecycle completes, the raw result stands as
`RAW RESULT PROMOTION ELIGIBILITY = REJECTED / BLOCKED` and the authoritative ETB
semantic result is unchanged. No step of that lifecycle may be skipped,
collapsed, or performed by the session that produced the raw result.

---

## 17. Publication model

Preserved from the accepted Oracle-PathE design, with the write-viability gate
(§7) as a mandatory precondition:

1. six-path occupancy precondition; fail closed with a constant marker if any
   reserved path is already occupied;
2. `[System.IO.Directory]::CreateDirectory` for the evidence directory;
3. TEMP evidence written with `[System.IO.FileMode]::CreateNew` +
   `[System.IO.FileShare]::None` (no overwrite, ever);
4. write, then `Flush($true)`;
5. full byte read-back comparison;
6. terminal-LF / no-double-LF / no-BOM assertions;
7. `ConvertFrom-Json` validation including `schema_version`, `outcome` and
   `listener_probe_outcome` agreement;
8. SHA-256 of the evidence bytes; manifest line `<digest>` + two ASCII spaces +
   `<path>`;
9. result artifact constructed last, including a runtime-built U+2014 em dash
   from ASCII-only source;
10. publication order **evidence → manifest → result last**, with post-move byte
    verification and semantic re-validation;
11. failures raise into a narrow local `try`/`catch` that publishes a frozen
    `HARNESS_INVALID` evidence-machinery outcome with a constant
    publication-failure surface and no persisted exception text;
12. terminal reporting happens after that `try`/`catch`, through the §4.1
    reporting primitive.

No overwrite, repair, retry or delete exists anywhere in the publication path.
TEMP paths are reserved namespace members (§18).

---

## 18. Namespace reservations (design only; nothing created)

The Path-F runtime namespace is exactly 11 paths:

| # | Path |
|---|------|
| 1 | `docs/v0.3/evidence/ETB_PATH_F_AUTHORIZATION_USE.claim` |
| 2 | `docs/v0.3/evidence/ETB_PATH_F_AUTHORIZATION_USE.claim.tmp` |
| 3 | `docs/v0.3/evidence/ETB_PATH_F_ATTEMPT_USE.claim` |
| 4 | `docs/v0.3/evidence/ETB_PATH_F_ATTEMPT_USE.claim.tmp` |
| 5 | `docs/v0.3/evidence/etb-execution-path-f/` (directory) |
| 6 | `docs/v0.3/evidence/etb-execution-path-f/ETB_EVIDENCE.json` |
| 7 | `docs/v0.3/evidence/etb-execution-path-f/ETB_EVIDENCE.json.tmp` |
| 8 | `docs/v0.3/evidence/etb-execution-path-f/MANIFEST.sha256` |
| 9 | `docs/v0.3/evidence/etb-execution-path-f/MANIFEST.sha256.tmp` |
| 10 | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_F.md` |
| 11 | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_F.md.tmp` |

Occupancy accounting is by path, exactly as defined here: the Path-E namespace
reported 6/11 because five artifacts **and the evidence directory** counted, and
the Path-F design defines the same rule explicitly so that lesson L4 cannot
recur. Current Path-F occupancy: **0 / 11**.

Path-E and Path-D namespaces are untouched by this design and by any future
Path-F execution.

---

## 19. Provenance model (normative — one rule, stated once)

Path-F chooses **MODEL 2: external lineage binding**, and defines it exactly once
here. This is a deliberate design decision, not a copy of Path-E wording.

```
provenance_model = MODEL_2_EXTERNAL_LINEAGE_BINDING
provenance_owner_content = ORACLE_PATH_F_SPEC
provenance_owner_lineage_binding = PATH_F_EXECUTION_AUTHORIZATION_RECORD_AND_CLAIMS
```

Rules:

1. **Content provenance is owned by this specification.** The Oracle-PathF
   evidence artifact carries the three Path-F provenance fields with the literal
   value `UNKNOWN`:
   - `oracle_path_f_commit`
   - `oracle_path_f_spec_sha256`
   - `oracle_path_f_script_sha256`

   They are **never** inferred, defaulted or fabricated by the executable.
2. **Lineage binding is owned externally.** The future Path-F execution
   authorization record and the Path-F claim artifacts carry the frozen Path-F
   values (`Oracle-PathF` commit, spec SHA-256, script SHA-256), verifiable
   directly from the repository. The binding is therefore repository-verifiable
   without asking the evidence artifact to assert something the specification
   reserves.
3. **The two ownerships must never contradict each other.** A future Path-F
   authorization artifact must be written compatibly with this section: it may
   require that Path-F claims and governance surfaces record the frozen Path-F
   values, but it must **not** require the Oracle evidence artifact to record
   values that this specification reserves as `UNKNOWN`. This is the design-time
   elimination of the Path-E lesson L3 tension — Path-F does not create a new
   contradiction between its authorization and its Oracle specification.
4. **No post-hoc evidence rewriting.** Once published, the evidence artifact is
   never rewritten, normalized or repaired. If lineage binding is ever needed
   after the fact, it is supplied by a governance record, not by editing evidence.
5. **Self-identity is not provenance.** `oracle_self_identity_sha256` and
   `oracle_self_identity_spec_sha256` are runtime observations (§5) recorded under
   distinct field names.
6. **Historical identity is not a Path-F identity.** The historical original ETB
   oracle identity (`1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc` /
   `01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921`) is
   recorded for continuity only. It is **not** a Path-F identity, is never used as
   an active oracle identity, and is never substituted for Path-F provenance. No
   Path-D, Oracle-R2, Recovery-R1, Recovery-R2 or D1 identity is substituted
   either.
7. **The executable asserts no lineage it cannot observe.** At design time the
   constants `$OraclePathFCommit`, `$OraclePathFSpecSha` and `$OraclePathFScriptSha`
   are `'UNKNOWN'`; the executable never writes a guessed value into them.

---

## 20. Budget model (design only)

Three budgets are defined; **none exists** and none is available for consumption.

### 20.1 PATH-F AUTHORIZATION-USE BUDGET

| Property | Value |
|----------|-------|
| Initial state | `NOT CREATED / NOT AVAILABLE FOR CONSUMPTION` |
| Availability condition | a separate, accepted Path-F execution authorization round |
| Exact irreversible consumption event | successful `[System.IO.FileMode]::CreateNew` of `docs/v0.3/evidence/ETB_PATH_F_AUTHORIZATION_USE.claim.tmp` |
| Post-consumption state | `1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE` |
| Claim identity | `ETB_PATH_F_AUTHORIZATION_USE.claim` |
| TEMP/FINAL | TEMP is the consumption record; FINAL is promoted only by a later governance round |
| Retry | `NONE` |

### 20.2 PATH-F ETB-ATTEMPT BUDGET

| Property | Value |
|----------|-------|
| Initial state | `NOT CREATED / NOT AVAILABLE FOR CONSUMPTION` |
| Availability condition | the authorization-use budget already consumed, in the same authorized round |
| Exact irreversible consumption event | successful `[System.IO.FileMode]::CreateNew` of `docs/v0.3/evidence/ETB_PATH_F_ATTEMPT_USE.claim.tmp` |
| Post-consumption state | `1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE` |
| Claim identity | `ETB_PATH_F_ATTEMPT_USE.claim` |
| Retry | `NONE` |

### 20.3 ORACLE-PATHF INVOCATION BUDGET

| Property | Value |
|----------|-------|
| Initial state | `NOT AUTHORIZED` |
| Availability condition | both claim budgets consumed in the same authorized round |
| Maximum | `1 OF 1 / MAXIMUM REACHED` after the single authorized invocation |
| Retry | `NONE` |

### 20.4 Frozen failure rule (closes Path-E lesson L1)

A `CreateNew` that fails **before** the file is created does **not** consume the
budget — no irreversible event occurred. It nevertheless **terminates the
round**: the failure is fail-closed, no retry is attempted, no permission change
is attempted, and any further attempt requires a **new Owner decision**. There is
no pre-consumption re-attempt authority of any kind. This rule is frozen at design
time rather than left ambiguous, as it was under Path-E.

No Path-D or Path-E budget may be reused, reset, extended or reinterpreted. A
failed Path-F round never returns to a predecessor lineage.

---

## 21. Effectivity and status

```
ORACLE-PATHF = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE
PATH-F EXECUTION AUTHORIZATION = NOT CREATED / NOT EFFECTIVE
PATH-F EXECUTION AUTHORITY = NONE
PATH-F CLAIM BUDGETS = NOT OPERATIONALLY AVAILABLE
PATH-F ETB ATTEMPT = NOT AVAILABLE
ORACLE-PATHF INVOCATION = NOT AUTHORIZED
PATH-E LINEAGE = EXHAUSTED / CLOSED
PATH-E RAW RESULT = BLOCKED / NON-PROMOTABLE
PATH-E RETRY AUTHORITY = NONE
PATH-F RUNTIME NAMESPACE OCCUPANCY = 0 / 11
AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED
ACL STATE = NOT NORMALIZED (unchanged by this round)
ACL RESTORATION = OUT OF SCOPE
```

This design creates no ETB observation and no execution authority.

---

## 22. Static verification and regression test

Measured on the Path-F revision of
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.ps1`:

```
bytes = 49704        lines = 894        LF = 894        CR = 0
non-ASCII bytes = 0  max byte = 125     BOM = absent
parser errors = 0
SHA-256 = 4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0
```

Function extents: `Test-BootstrapFacility` L240-247, `Get-Utf8FileSha256`
L280-291, `Get-LowerHex` L295-299, `Get-CanonicalPath` L474-495, `New-Snapshot`
L497-509, `Take-Snapshot` L512-640. Guard `trap`: L144-152, command invocations
inside: 0. Exit sites: `exit 4` L151, `exit 2` L691, `exit 3` L882, `exit 0`
L894.

`CommandAst` inventory (28): class A — `Test-BootstrapFacility` L263, L266, L267,
L376; `Get-Utf8FileSha256` L301, L302, L598, L599; `Get-LowerHex` L765, L776,
L859; `Get-CanonicalPath` L581, L585, L632; `New-Snapshot` L513, L675, L676;
`Take-Snapshot` L655, L661. Class C — `python` L386; `Add-Type` L463;
`Get-NetTCPConnection` L520; `Get-CimInstance` L555; `ConvertTo-Json` L749;
`ConvertFrom-Json` L618, L759, L856. Plus `Get-Command` L242 inside the wrapped
availability checker. Class B and class D counts: 0 command nodes.

Regression properties that a third-party design review must re-measure:

| # | Property | Required result |
|---|----------|-----------------|
| A | no command outside the declared taxonomy | 28 nodes, all classified |
| B | guard body is command-free | 0 |
| C | check stage < first-use stage for every gated facility | holds (L376 < L386) |
| D | `Get-FileHash` usage | 0 |
| E | Path-F occupancy representation | `0 / 11`, by the §18 path rule |
| F | ACL command usage (`icacls`, `Set-Acl`, `Get-Acl`) | 0 |
| G | write-viability gate precedes every publication step and every governed path creation | holds |
| H | reachable undocumented `exit 1` | none |
| I | `while`, `Start-Sleep`, `Write-Output`, `ForEach-Object`, `Split-Path`, `Set-Location`, `Get-Content`, `Test-Path`, `Invoke-Expression` usage | 0 each |
| J | `try` statements / `[System.Console]::Out.WriteLine` sites | 20 / 22 |

Reproducible verification: parse the file with
`[System.Management.Automation.Language.Parser]::ParseFile` and enumerate
`CommandAst`, `FunctionDefinitionAst`, `TrapStatementAst`, `WhileStatementAst` and
`TryStatementAst` nodes; compute SHA-256 with .NET
(`[System.Security.Cryptography.SHA256]::Create()` over
`[System.IO.File]::ReadAllBytes`); count byte classes with
`[System.IO.File]::ReadAllBytes` (never `Select-String`, whose zero-match output is
not evidence).

### 22.1 Frozen artifact identity mechanism

- The executable is covered by an **exact-path** `.gitattributes` rule
  (`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.ps1 text eol=lf`); no
  wildcard rule is added and no existing rule is modified.
- This specification is covered by the existing repository-wide `*.md text eol=lf`
  rule.
- Both files are LF-only, BOM-free and byte-stable; their identity is established
  by SHA-256 over the raw bytes (§5), never by a reformatting tool, never by
  `Get-FileHash` inside the oracle, and never by line-ending normalization after
  the fact.

---

## 23. Non-claims

This design candidate is not a SIC result, not a P6 result, not a G0.5 result, not
a Mode-B result, not a Case-C authorization and not an adoption authorization. It
classifies no ETB semantics, promotes nothing, and creates no authority.

---

## 24. Next stage

```
NEXT STAGE = FRESH QUALIFYING THIRD-PARTY INDEPENDENT REVIEW
             OF THE ORACLE-PATHF DESIGN CANDIDATE
```

That review must, at minimum: attempt to reproduce or detect the historical
`Get-FileHash`-before-availability-gate defect; independently re-measure the
ordering invariant of §6; verify that the write-viability gate of §7 cannot
consume one-shot authority and cannot create a governed path; verify the ACL
command count is 0; verify that §19 is internally coherent and that no future
authorization wording is required to contradict it; and verify the namespace
accounting rule of §18.

Acceptance bookkeeping, freeze and confirmation are **not** performed in this
round, and no independent confirmation is required at the design-candidate stage.
The design is a candidate only: it is not accepted, not frozen and not effective
until a later, separately authorized round says so.
