# DevRelay v0.3-E — G0.5-PRE / SIC — ETB execution oracle R2 (execution-fidelity / output-namespace closure)

> **ETB EXECUTION ORACLE-R2 — CORRECTIVE DESIGN R2 CANDIDATE**
> **DESIGN CANDIDATE**
> **NOT ACCEPTED**
> **NOT FROZEN**
> **NOT EXECUTED**
> **DOES NOT EXECUTE ETB**
> **DOES NOT CREATE R2 OUTPUTS**
> **DOES NOT AUTHORIZE ANY ATTEMPT**

Status: **ETB EXECUTION ORACLE-R2 = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EXECUTED**

Previous candidate `6d252a9466d768bb6345aad6c0c7a04562b8845c` (spec
`3373159918c76d0403ac5e98cbce9706e9659f7a9ad2e63b9124876e764194f2`, script
`3e2cc721a0be047e92f807a64693b53107b669650931a10408a37f361a897079`) =
**REQUEST_CHANGES — V0.3-E ETB EXECUTION ORACLE-R2 / SUPERSEDED AS A CANDIDATE** (independent review
severity P0 = 0, P1 = 1, P2 = 2, P3 = 5).  It remains historical, is **not** accepted, and is **not**
relabelled as any semantic ETB result.

Baseline: `6d252a9466d768bb6345aad6c0c7a04562b8845c` (branch `v0.3-e-recovery-reconciliation`) is the
parent of this corrective candidate; the original design baseline remains
`4a84b12aac0ee3c09e5de67cbec3a61eba446bdc`.

This round is **corrective design / documentation / tracked-executable correction only**.  Oracle-R2 is not
executed here, no R2 output path or directory is created, no new authorization and no new claim namespace is
designed, and nothing in this artifact authorizes an ETB attempt.

## 1. Provenance (immutable; Oracle-R2 rewrites none of these)

| Domain | Commit | SHA-256 |
| --- | --- | --- |
| original configuration-transition authorization | `64044fc45082cd63b0ae445c146d85720dfa1435` | `511ab1e2eb2e4f1194d2c55951e5b9616dc515d1180c6399dd658207d443d0d8` |
| Recovery-R1 authorization | `3541c011cf92d9d66253989c5f576c2ad845ca33` | `7fb1f28d427cc8c567491afc3137890f79b2bdb8bce88b4be2f63005824f3ab7` |
| original frozen ETB oracle | `1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc` | `01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921` |

## 2. Rejected Recovery-R1 result state (recorded accurately)

| Item | State |
| --- | --- |
| Recovery-R1 published candidate result | **REJECTED** |
| authoritative ETB semantic result | **NONE** |
| Recovery-R1 authorization | `1/1 CONSUMED / NOT REUSABLE` |
| Recovery-R1 ETB attempt | `1/1 CONSUMED / NOT REUSABLE` |

The independent result review returned **REJECT RECOVERY-R1 PUBLISHED ETB RESULT — NO AUTHORITATIVE ETB
SEMANTIC RESULT** (P0 = 0, P1 = 1, P2 = 1, P3 = 2) with `RECOVERY_CONTROL_STATE = VALID`,
`CONFIG_ESTABLISHMENT_RECOVERY = VALID`, `ORACLE_IMPLEMENTATION_FIDELITY = NONCONFORMANT / INDETERMINATE`,
`BLANKET_CATCH_CLASSIFICATION = NONCONFORMANT`, `MANDATORY_STOP_FIDELITY = NONCONFORMANT`,
`RESULT_ENCODING_FIDELITY = NONCONFORMANT`, `RESULT_ARTIFACT_VALIDITY = VALID_WITH_NONBLOCKING_TEXT_DEFECT`,
`PUBLISHED_RESULT_CLASSIFICATION = UNRESOLVABLE`, `FROZEN_TAXONOMY_RESULT = INDETERMINATE DUE TO EXECUTION
NONCONFORMANCE`, `INDEPENDENT_RECLASSIFICATION_PERMITTED = NO`, `NEW_ETB_AUTHORIZATION_REQUIRED = YES`.

**2.1** The rejected candidate must **not** be relabelled as `ETB_UNSATISFIED`, as an authoritative
`HARNESS_INVALID`, or as `ETB_SATISFIED`.  No independent reclassification is permitted.

## 3. Why the original oracle cannot simply be re-run

**BLOCKER A — output namespace occupied.**  The immutable Recovery-R1 finals
`docs/v0.3/evidence/etb-execution/ETB_EVIDENCE.json`,
`docs/v0.3/evidence/etb-execution/MANIFEST.sha256` and
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT.md` are **present**.  The original frozen oracle requires all
six of its final/temp output paths to be absent before a consumed attempt proceeds; therefore its exact
output namespace cannot be reused without violating its own precondition or mutating historical artifacts.
Oracle-R2 uses a **distinct output namespace** (§7).

**BLOCKER B — executable implementation not frozen.**  The Recovery-R1 execution script was not preserved,
so the independent review could not compare actual executable bytes against the accepted oracle, and a
blanket catch materially changed result classification.  Oracle-R2 therefore freezes **the executable script
itself** as a tracked immutable artifact (§6, §10).

## 4. Semantic inheritance

Oracle-R2 preserves the original frozen oracle's substantive ETB semantics except where this artifact
explicitly freezes a fidelity/namespace correction.  Preserved exactly: Mode P (pre-existing target); owner
endpoint `http://127.0.0.1:4096`; no endpoint discovery; no fallback; no IPv6; no `localhost` alias; no
alternate port; no Mode L; no OpenCode start/restart; no HTTP; no `/doc`; no `/session`; no provider/model
call; listener uniqueness requirement; `OwningProcess`; PID; `Win32_Process`; `ExecutablePath`;
canonicalization; target canonicalization; exact executable-path equality; executable SHA-256; exact OpenCode
version; `CreationDate`/process-instance identity; S0/S1 continuity; fail-closed semantics; terminal-result
semantics; no retry.  **No accepted target-binding condition is weakened.**

## 5. Result taxonomy (unchanged; three classes only)

`ETB_SATISFIED`; `ETB_UNSATISFIED`; `HARNESS_INVALID / NO ETB SEMANTIC RESULT`.  No new class; no `PASS`,
`FAIL`, `PARTIAL`, `UNKNOWN`, `PROBABLE` or `RETRY`.  Oracle-R2 exists to implement the existing taxonomy
correctly, not to redefine it.

## 6. Frozen artifacts of this round

| Artifact | Role |
| --- | --- |
| `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1` | **normative executable Oracle-R2 implementation** |
| `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.md` | this specification |
| `.gitattributes` | corrective R2 tracked **LF worktree contract** for the normative executable (§21.3) — exactly one added narrow rule, no other text policy changed, `core.autocrlf` unaltered |

## 7. Identity model

After independent acceptance of this candidate, all three values below are **immutable**, and a later
bookkeeping commit, Recovery-R2 authorization commit, operational HEAD or result-review commit must replace
none of them:

| Value | Definition |
| --- | --- |
| `oracle_r2_commit` | the immutable future independently accepted commit containing **both** Oracle-R2 files |
| `oracle_r2_script_sha256` | **committed-blob** SHA-256 of `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1` (the LF byte sequence stored in `oracle_r2_commit`, i.e. `git show <oracle_r2_commit>:docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1`), never a checkout-normalized byte sequence |
| `oracle_r2_spec_sha256` | **committed-blob** SHA-256 of `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.md` |

**7.1 Worktree-identity requirement (fail closed; corrective R2 removes the materialization deadlock).**  The
repository uses `* text=auto` with `core.autocrlf=true`, which would otherwise materialize this normative
executable with CRLF line endings.  This corrective round therefore adds exactly **one** narrow tracked
attribute rule — `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1 text eol=lf` (§21.3) — so that a
**normal canonical checkout** materializes the script as LF bytes independently of any local
`core.autocrlf` value.  No future ad-hoc repair stage is frozen or required: the corrective candidate itself
closes the repository-state problem.  The future Recovery-R2 authorization **and** the future executor MUST,
before attempt consumption: (i) require the tracked blob hash at `oracle_r2_commit` to equal
`oracle_r2_script_sha256`; (ii) require the worktree file bytes to be **byte-identical** to those committed
blob bytes; and (iii) if they differ for any reason, **STOP before consuming anything** — the accepted
executable bytes are the LF blob bytes, and a non-identical file must never be executed as Oracle-R2.  This is
the only permitted handling: no normalization, rewrite, re-encoding, alternate checkout, "equivalent bytes"
substitution or executor-selected equivalent representation is authorized.

The future Recovery-R2 authorization **MUST** bind to all three values.

## 8. Listener taxonomy (acceptance critical; implemented in the script)

| Case | Condition | Classification |
| --- | --- | --- |
| **A** | `Get-NetTCPConnection` command/module genuinely unavailable | `HARNESS_INVALID / NO ETB SEMANTIC RESULT` |
| **B** | cmdlet exists, but the exact frozen listener query raises an access / provider / query / execution exception | `ETB_UNSATISFIED` |
| **C** | exact query successfully returns zero matching rows | `ETB_UNSATISFIED` |
| **D** | exact query returns more than one matching row | `ETB_UNSATISFIED` |
| **E** | exactly one row, but required listener field/PID validation fails | `ETB_UNSATISFIED` |
| **F** | exactly one valid matching row | continue the target-binding procedure |

**8.1** **No blanket `catch { HARNESS_INVALID }` is permitted around the listener/snapshot procedure.**

## 9. Command-availability branch and query error handling

**9.1** The script performs an explicit, deterministic availability branch **before** the exact listener
query, using one mechanism only: `Get-Command -Name <name> -ErrorAction SilentlyContinue`; a `$null` result
means unavailable.  Availability is therefore **never** inferred from the shape of a listener-query
exception.

**9.2** The exact listener query is `@(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 4096 -State
Listen -ErrorAction SilentlyContinue -ErrorVariable qerr)` inside its own **narrow** `try`/`catch` boundary.

**9.3** Deterministic listener-probe decision order (frozen):

1. a terminating exception from that call → `QUERY_EXCEPTION` → `ETB_UNSATISFIED`;
2. a collected non-terminating error whose `FullyQualifiedErrorId` matches `*CmdletizationQuery_NotFound*`
   **and** zero rows → `ZERO_ROWS` → `ETB_UNSATISFIED`;
3. any other collected non-terminating error → `QUERY_EXCEPTION` → `ETB_UNSATISFIED`;
4. no error and zero rows → `ZERO_ROWS` → `ETB_UNSATISFIED`;
5. no error and more than one row → `MULTIPLE_ROWS` → `ETB_UNSATISFIED`;
6. no error and exactly one row → field/PID validation → `FIELD_OR_PID_INVALID` → `ETB_UNSATISFIED`, or
   `ONE_VALID_ROW` → continue.

**9.4** A no-match condition surfaced by PowerShell 5.1 / `ErrorAction` semantics as a terminating exception
is therefore classified `ETB_UNSATISFIED` (case B), never `HARNESS_INVALID`.  **The PowerShell exception form
alone can never produce `HARNESS_INVALID` from the listener stage.**

## 10. No global classification catch

**10.1** The script contains **no** outer/general catch that maps arbitrary snapshot or listener exceptions
to `HARNESS_INVALID`.  Its `catch` blocks are narrow and typed:

| Region | Exception → classification |
| --- | --- |
| native P/Invoke invocation (type load / entry point / marshaling / signature) | `HARNESS_INVALID` (frozen original row) |
| native `CloseHandle` returning false | `HARNESS_INVALID` (frozen original row) |
| native type load (`Add-Type`) | `HARNESS_INVALID` (frozen original row) |
| exact listener query | `QUERY_EXCEPTION` → `ETB_UNSATISFIED` |
| exact PID-scoped process query | `ETB_UNSATISFIED` |
| config reader launch/import/runtime failure | `HARNESS_INVALID` (frozen original row) |
| package manifest read/parse | `ETB_UNSATISFIED` |
| hash read | `ETB_UNSATISFIED` |
| **evidence/publication stage** (delimited region containing **no** listener, process, canonicalization, hash or package logic) | `HARNESS_INVALID` (frozen original row) |

**10.2** The reviewer must mechanically search every `catch`, `throw`, `HARNESS_INVALID` and
`ETB_UNSATISFIED` occurrence and verify branch correctness against §8–§10.

## 11. Output namespace (new; six exact paths)

| Purpose | Final path | Temp path |
| --- | --- | --- |
| evidence | `docs/v0.3/evidence/etb-execution-r2/ETB_EVIDENCE.json` | `docs/v0.3/evidence/etb-execution-r2/ETB_EVIDENCE.json.tmp` |
| manifest | `docs/v0.3/evidence/etb-execution-r2/MANIFEST.sha256` | `docs/v0.3/evidence/etb-execution-r2/MANIFEST.sha256.tmp` |
| result | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_R2.md` | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_R2.md.tmp` |

**11.1** The Recovery-R1 paths (`docs/v0.3/evidence/etb-execution/ETB_EVIDENCE.json`,
`…/MANIFEST.sha256`, `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT.md`) must **not** be reused and remain
immutable historical rejected artifacts.

**11.2 Output precondition.**  All six **new** R2 paths must be ABSENT before publication work begins;
**file OR directory** occupancy at any exact path fails closed.  No deletion, no cleanup, no overwrite, and
the old Recovery-R1 output paths are neither inspected nor altered as part of this precondition.  The R2
evidence directory `docs/v0.3/evidence/etb-execution-r2` is created by the oracle only if absent; if that
exact path exists as a file, or cannot be created as a directory, the attempt fails closed
(`HARNESS_INVALID`).

## 12. Evidence semantics and the single added audit field

**12.1** No existing target-binding evidence field or check is removed.  Top-level order is the accepted
order with exactly **one** inserted field:

```
schema_version, oracle_commit, oracle_sha256, execution_started_at, execution_finished_at,
mode, endpoint, configured_base_url, target, snapshot_s0, snapshot_s1, checks,
listener_probe_outcome, outcome, non_claims, activity_counters
```

**12.1.1 Evidence schema identity (corrective R2, frozen).**  The Oracle-R2 top-level evidence contract is a
**closed 16-field contract** and carries the distinct schema identity **`devrelay-etb-v1-r2`**; the script
writes that exact string and asserts it on read-back.  **`devrelay-etb-v1`** denotes only the **historical
original closed schema** of the original frozen oracle (the Recovery-R1 evidence artifact) and is never used,
reused or reinterpreted by Oracle-R2; adding the `listener_probe_outcome` audit field while retaining the old
identifier was the P2-A defect this correction removes.  The two identities are distinct and neither
reinterprets the other.

**12.2** `listener_probe_outcome` — type: JSON string; exact allowed values (enum):

| Value | Meaning | Bound classification |
| --- | --- | --- |
| `COMMAND_UNAVAILABLE` | `Get-NetTCPConnection` unavailable | `HARNESS_INVALID` |
| `QUERY_EXCEPTION` | exact query raised an exception/error | `ETB_UNSATISFIED` |
| `ZERO_ROWS` | exact query returned zero rows | `ETB_UNSATISFIED` |
| `MULTIPLE_ROWS` | exact query returned more than one row | `ETB_UNSATISFIED` |
| `ONE_VALID_ROW` | exactly one row and all field/PID validations passed | continue |
| `FIELD_OR_PID_INVALID` | one row but field/PID validation failed | `ETB_UNSATISFIED` |
| `NOT_REACHED` | only valid before the listener stage, or when an earlier frozen terminal condition already ended the attempt | (no listener classification) |

**12.2.1 S0/S1 semantics of the single published field (corrective R2; frozen, not executor-selectable).**
There are potentially **two** listener probes, S0 and S1.  The single published `listener_probe_outcome`
field always means **THE LISTENER PROBE OUTCOME ASSOCIATED WITH THE LAST ACTUALLY EXECUTED SNAPSHOT PROBE
THAT DETERMINES OR CONTRIBUTES TO THE PUBLISHED TERMINAL RESULT**, resolved mechanically as:

| Situation | Published `listener_probe_outcome` |
| --- | --- |
| failure occurs before any listener probe is executed | `NOT_REACHED` |
| the S0 listener probe terminates the attempt | the S0 listener probe outcome |
| S0 succeeds with `ONE_VALID_ROW` and the S1 listener probe terminates the attempt | the S1 listener probe outcome |
| S0 succeeds with `ONE_VALID_ROW` and the S1 listener probe succeeds | `ONE_VALID_ROW` |
| both listener probes succeed and a later continuity/identity check fails | `ONE_VALID_ROW`, unchanged |

The script implements this as a **total** assignment: the field is initialised to `NOT_REACHED` before any
probe can execute, re-assigned to the S0 listener outcome immediately after S0 is taken, and re-assigned to
the S1 listener outcome immediately after S1 is taken.  The `COMMAND_UNAVAILABLE` availability row assigns the
field before any probe is taken.  **"S0 or S1?" is therefore never executor-selectable**, and no path leaves
the field ambiguous.

**12.3** The published semantic `outcome` **must agree** with this field under the mapping above.  The script
derives the outcome from the same decision that produces the field (no second, independent assignment), and
the frozen read-back verification additionally requires the serialized `listener_probe_outcome` and
`outcome` to equal the in-memory values; a mismatch therefore surfaces as the frozen evidence-machinery
`HARNESS_INVALID` — it is **not** executor-selectable.  No raw exception message, stack trace, prompt,
response or reasoning is persisted.

**12.4** `checks` keeps the accepted 18 keys and the accepted `PASS` / `FAIL` / `NOT_REACHED` vocabulary.
`activity_counters` keeps the accepted 14 keys, all `0` for a compliant attempt.  `non_claims` keeps the
accepted six ordered strings.  `endpoint` and `target` keep the accepted ordered sub-objects.  Snapshots keep
the accepted 25-field order.

## 13. Snapshot placeholders

**13.1** Unobserved fields are represented **only** as truthful placeholders: empty string (`""`) for string
fields and `0` for integer fields, exactly as in the prior accepted evidence model.  They must **not** imply
that a listener, PID, path, hash, version or `CreationDate` was observed, nor that continuity was
established.  Frozen constants that are known a priori (`mode`, the endpoint tuple, `configured_base_url`,
`accepted_target_path_raw`, `accepted_target_sha256`, `package_name`, `expected_sha256`, `expected_version`)
are always populated with their frozen values; observed values are populated only when actually observed.

## 14. Target-binding chain (preserved)

endpoint tuple → exact listener query and uniqueness → `OwningProcess` → PID-scoped `Win32_Process` query
(`ProcessId`, `ExecutablePath`, `CreationDate`) → process-instance identity (PID **and** `CreationDate.Ticks`)
→ `CreateFileW`/`GetFinalPathNameByHandleW` canonicalization of **both** the process-reported
`ExecutablePath` and the accepted target literal (AS-IS `\\?\` text, `-ceq` comparison) → dual
`Get-FileHash -Algorithm SHA256` equal to `578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35`
→ exact `package.json` identity (`opencode-ai`, `1.18.11`, `bin.opencode` resolving under the accepted
package root to the accepted executable, canonicalized and compared `-ceq`) → S0 → S1 with no HTTP and no
semantic OpenCode request in between → S0 == S1 on the continuity comparison field set frozen by the
**ORIGINAL FROZEN ORACLE** artifact (`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md`), section **§15.2 of
that artifact** — expressly **not** this specification's own local §15.2, which is the UTF-8 / U+2014
mechanism.  Native parameter values
(`GENERIC_READ 0x80000000`, share `0x00000007`, `OPEN_EXISTING 3`, `FILE_ATTRIBUTE_NORMAL 0x80`, flags `0`,
`StringBuilder(32768)`) and the `DevRelayEtbNativeV1` declarations are the accepted ones.

## 15. Result artifact, encoding and publication order

**15.1** The result artifact keeps the accepted template with the R2 outcome vocabulary, written as UTF-8,
**no BOM**, LF only, exactly one final LF, and read back and byte-verified before success.

**15.2 UTF-8 / U+2014 mechanism (frozen).**  The source is **ASCII-only** (every byte ≤ `0x7F`; verified
mechanically in this round).  The em dash is constructed at runtime exactly as `$EmDash = [char]0x2014` and
serialized through `[System.Text.UTF8Encoding]::new($false)`, so the published result artifact contains the
exact UTF-8 bytes `E2 80 94` for U+2014 in its first line.  The script verifies the presence of those three
bytes in the result temp before publication.

**15.3 Publication order (frozen).**  `ETB_EVIDENCE.json` → `MANIFEST.sha256` → `RESULT_R2` **last**, using
the two-argument `System.IO.File.Move` (no overwrite), each followed by read-back byte verification, and then
the frozen post-publication verification.  The manifest covers **only** `ETB_EVIDENCE.json` (matching the
accepted design): one line, `<64-lowercase-sha256>` + two ASCII spaces +
`docs/v0.3/evidence/etb-execution-r2/ETB_EVIDENCE.json` + LF.  No rewrite after publication.

**15.4 Result final readback (corrective R2 clarification; frozen).**  The final `RESULT_R2` bytes are
required to be **byte-identical** to the already validated result temp bytes: after the two-argument
`File.Move`, the script re-reads the final file and performs a full length comparison plus a per-byte
comparison against exactly those validated temp bytes.  Byte identity therefore preserves **every** frozen
semantic field of the validated temp by construction, and **no second semantic parser of the published result
is added** after publication.  No post-result probe of any kind follows.

**15.5 Publication-failure stdout (corrective R2; frozen constant).**  If any failure occurs anywhere inside
the delimited evidence/publication region, the executable emits exactly the single constant stdout line
**`ORACLE_R2_PUBLICATION_FAILURE`** and nothing else on that line — no exception message, stack trace,
provider text, file path, environment data or partially written output is captured, persisted or printed —
followed by `ORACLE_R2_FINAL_CLASSIFICATION=HARNESS_INVALID`, `ORACLE_R2_SEMANTIC_RESULT=NONE` and exit code
`3`.  No other publication-failure stdout exists.

## 16. Mandatory stop

**16.1** The normative executable terminates immediately after final result publication and the frozen
verifications.  After result publication it performs **no** `Get-Command`, `Get-NetTCPConnection`,
`Get-CimInstance`, endpoint inspection, listener/process inspection, availability probe, diagnostic, repair,
reclassification or additional evidence collection.  No "helpful" post-result check and no report-time probe.

## 17. Tracked executable requirement (self-containment)

**17.1** The `.ps1` file **is** the future executable.  A future executor **must not** extract the script from
this Markdown, generate a temporary script, copy/paste function bodies into another script, translate to
Python, wrap it in another classification layer, inject assertions, or modify it before execution.

**17.2** The future Recovery-R2 authorization must require: verify the tracked blob hash at
`oracle_r2_commit` against the accepted `oracle_r2_script_sha256`; verify the worktree script bytes are
byte-identical to that blob (§7.1, else STOP); hash the script immediately before attempt consumption against
the accepted `oracle_r2_script_sha256`; execute **this exact tracked path**; and preserve its bytes for
independent review.

**17.3** Complete operational behavior is determinable from the tracked `.ps1` bytes plus this specification.
No behavior depends on chat instructions, executor memory, temporary generated code, untracked helper
scripts or interactive judgment.  All helper functions are contained in the tracked `.ps1`; the only
external primitives are the exact named standard PowerShell/.NET commands and APIs frozen here.

**17.4 Exact future execution invocation** (frozen shape; run from the repository root):

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1"
```

No parameters, no wrapper, no redirection that alters stdout semantics, and no post-execution probing by the
executor.  The **complete** frozen Oracle-R2 stdout contract is: `ORACLE_R2_SCRIPT_SHA256`,
`ORACLE_R2_SPEC_SHA256`, `ORACLE_R2_SEMANTIC`, `ORACLE_R2_CHECKS`, and then exactly one of the two terminal
surfaces — the success surface `ORACLE_R2_PUBLICATION_OK`, `ORACLE_R2_EVIDENCE_SHA256`,
`ORACLE_R2_MANIFEST_SHA256`, `ORACLE_R2_FINAL_CLASSIFICATION`, `ORACLE_R2_SEMANTIC_RESULT`, or the
publication-failure surface `ORACLE_R2_PUBLICATION_FAILURE` (§15.5, a constant line with no appended
exception text), `ORACLE_R2_FINAL_CLASSIFICATION=HARNESS_INVALID`, `ORACLE_R2_SEMANTIC_RESULT=NONE`.  **No
other stdout line exists and no undocumented failure stdout is permitted.**  Exit code `0` means the oracle
completed and published, `3` means the publication stage failed (frozen
`HARNESS_INVALID / NO ETB SEMANTIC RESULT`), and any other termination means the attempt produced no trusted
output.

## 18. Static validation performed in this design round

Parser-only syntax validation and static byte/source audits were performed on the tracked `.ps1`; the
operational main path was **not** executed, no listener/process command was run, and the endpoint was not
contacted.  For this corrective round the audits were: PowerShell **parser-only** validation
(`[System.Management.Automation.Language.Parser]::ParseFile`, **0 parse errors**), a full byte sweep
(**0 non-ASCII bytes**, **no BOM**, LF only, **CR count = 0**), `git check-attr text eol` on the normative
executable (resolving to the explicit LF contract frozen in §21.3), a static scan for residue of the corrected
defects (no hard-coded absolute repository path, no `$PublicationError`, exactly one evidence schema identity
`devrelay-etb-v1-r2`, a total `listener_probe_outcome` assignment), a static confirmation that the frozen
config-reader invocation shape of §21.1 is present, an `M`-only tracked-delta confirmation, and a
committed-blob-versus-worktree byte comparison (§7.1).

## 19. Current status and sequence

```
ETB EXECUTION ORACLE-R2 (this candidate)  = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EXECUTED
PREVIOUS ORACLE-R2 CANDIDATE 6d252a9      = REQUEST_CHANGES / SUPERSEDED AS A CANDIDATE
RECOVERY-R1 AUTHORIZATION                 = SPENT / NOT REUSABLE
RECOVERY-R1 ETB ATTEMPT                   = SPENT / NOT REUSABLE
RECOVERY-R1 PUBLISHED ETB RESULT          = REJECTED
AUTHORITATIVE ETB SEMANTIC RESULT         = NONE
NEW_ETB_AUTHORIZATION_REQUIRED            = YES
RECOVERY-R2 AUTHORIZATION                 = DOES NOT EXIST
```

**19.1** No Recovery-R2 authorization exists, no Recovery-R2 claim namespace is designed here, and this
corrective Oracle-R2 candidate is not usable until independently accepted.  The previous candidate
`6d252a9466d768bb6345aad6c0c7a04562b8845c` received *REQUEST_CHANGES — V0.3-E ETB EXECUTION ORACLE-R2*
(P0 = 0, P1 = 1, P2 = 2, P3 = 5) and is **SUPERSEDED AS A CANDIDATE**; it was never accepted, frozen or
executed, and it is **not** relabelled as `ETB_SATISFIED`, as an authoritative `ETB_UNSATISFIED` or as an
authoritative `HARNESS_INVALID`.

**19.2 Authoritative sequence:** Recovery-R1 attempt consumed → Recovery-R1 candidate result published →
independent result review → Recovery-R1 published result **REJECTED** → authoritative ETB semantic result
NONE → Oracle-R2 execution-fidelity/output-namespace design → Oracle-R2 candidate `6d252a9` → independent
Oracle-R2 review **REQUEST_CHANGES** (P0 = 0, P1 = 1, P2 = 2, P3 = 5) → **Oracle-R2 corrective design R2
(this round)** → independent corrective Oracle-R2 review → only if approved: Oracle-R2 acceptance bookkeeping
→ independent Oracle-R2 bookkeeping confirmation → Recovery-R2 authorization design → independent Recovery-R2
authorization review → Recovery-R2 acceptance bookkeeping → independent bookkeeping confirmation → exactly one
Recovery-R2 operational ETB attempt → independent ETB-result review → only an independently accepted
`ETB_SATISFIED` may allow Mode-B construction.  **No stage may be skipped.**

## 20. Preservation

**20.1** Config remains the exact post-image (`b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf`,
1897 bytes, `http://127.0.0.1:4096`); `CONFIG_ESTABLISHMENT = VALID / PRESENT`.  Oracle-R2 does not mutate
config and does not republish `CONFIG_ESTABLISHMENT`.

**20.2** The Recovery-R1 evidence/result artifacts, the original spent claim and the Recovery-R1 claims are
**not** modified, moved or deleted; they remain historical evidence of the rejected attempt.

**20.3** Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED /
PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 **NOT
CLOSED**; Case-C and v0.3-E implementation `NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`; `adopt_completed_turn`
**DISABLED**.

**20.4 Recovery-R1 operational artifact byte preservation.**  The seven R1 operational artifacts are **not**
part of the corrective tracked delta; their bytes are re-verified before and after this round:

| Artifact | SHA-256 |
| --- | --- |
| `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT.md` (R1 result) | `0a46aa284af30eebad30c689a494a6d73169db1094e07d34b9599913cfe9110e` |
| `docs/v0.3/evidence/ETB_AUTHORIZATION_USE.claim` (original authorization claim) | `d84b428586f07a55a99f5b1391481d77763ec4ea697a40d1cec8aa0779613d4e` |
| `docs/v0.3/evidence/ETB_RECOVERY_R1_AUTHORIZATION_USE.claim` | `8876bcc603ebf0f858902e7cce7e98096bdaa1f71768c9346a7b3acc6e4620b9` |
| `docs/v0.3/evidence/ETB_RECOVERY_R1_ATTEMPT_USE.claim` | `5f1e9721ed89355940f76d2cb868efec768a85ea957b9f92ba395b72fd4f97d2` |
| `docs/v0.3/evidence/etb-execution/CONFIG_ESTABLISHMENT.json` | `ea9fc2bc564cfd6d613e3145703f28d80bb87eb89dcdecaf7ad43b52d7bd9300` |
| `docs/v0.3/evidence/etb-execution/ETB_EVIDENCE.json` | `e2c603d73946b01f4e2ca33f7de70441dcc6aacad33b7421b0a066e160bf8b06` |
| `docs/v0.3/evidence/etb-execution/MANIFEST.sha256` | `ebe5214be473fab7afb83b858fb7857be5481424772e98c92770a2b3a817dfc5` |

## 21. Corrective R2 frozen corrections (review-finding closure)

This section records exactly what corrective R2 changed and freezes the mechanism for each blocking and
non-blocking finding.  Nothing here reopens an accepted semantic contract.

**21.1 Config-reader invocation fidelity (P1 closure; acceptance critical).**  The normative executable MUST
deterministically establish `<repo>/src` as `PYTHONPATH` for the config-reader subprocess, using the frozen
repository root, so that the src-layout production loader is importable without any installed package.  The
frozen subprocess semantics are exactly equivalent to the original frozen oracle's §5.3 shape:

```
PYTHONPATH=<repo>/src
python -c "<frozen config reader>" "<repo>"
```

The frozen PowerShell 5.1 mechanism is: capture whether a process-level `PYTHONPATH` existed and, if so, its
value; assign `$env:PYTHONPATH = (Join-Path $RepoRoot 'src')`; invoke the byte-identical frozen reader source
with `$RepoRoot` as its single repository argument; and restore the previous state in a deterministic `finally`
block — the prior value when one existed, **absence** (not an invented empty value) when none existed.
`PYTHONPATH` for this invocation resolves to `<repo>/src` **only**: it is never merged with, prepended to or
appended to any pre-existing content, and no second unrelated Python import path is hard-coded.  **The executor
has no choice in this mechanism.**  Any failure to establish or invoke the frozen reader remains
`config_reader_failure` → `HARNESS_INVALID` under the inherited infrastructure taxonomy.

**21.2 Repository-root binding (P3 closure).**  No absolute repository path is hard-coded anywhere in the
operational config-reader semantics.  The frozen root is derived deterministically from the tracked script
location (`$PSScriptRoot` is `<repo>/docs/v0.3`, so its grandparent is `<repo>`), and that single value is used
for the working location, for the config-reader repository argument and for `<repo>/src`.  The correction is
scoped to faithfully representing `<repo>` and `<repo>/src`; the script is not otherwise redesigned for
portability.

**21.3 LF worktree contract (P2-B closure; acceptance critical).**  `.gitattributes` gains exactly **one**
narrow rule:

```
docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1 text eol=lf
```

No repository-wide `*.ps1` rule is added, no other text policy is changed, and `core.autocrlf` is not altered.
`git check-attr text eol -- docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1` resolves to `text: set` and
`eol: lf`.  A normal canonical checkout therefore materializes the normative executable as LF bytes
independently of the local `core.autocrlf=true` setting, so the §7.1 byte-identity gate is satisfiable without
any ad-hoc repair stage.  The worktree script bytes are required to equal the committed blob bytes **byte for
byte**; no CRLF-vs-LF equivalence is acceptable.

**21.4 Evidence schema identity (P2-A closure).**  See §12.1.1: Oracle-R2 uses exactly `devrelay-etb-v1-r2`;
`devrelay-etb-v1` remains the historical original closed schema and is never used by Oracle-R2.

**21.5 `listener_probe_outcome` S0/S1 semantics (P3 closure).**  See §12.2.1: the published field is bound to
the last actually executed snapshot probe that determines or contributes to the published terminal result, by a
total assignment that leaves no executor choice.

**21.6 Listener taxonomy and catch structure (preserved; not weakened).**  The §8 mapping
(`COMMAND_UNAVAILABLE` → `HARNESS_INVALID`; `QUERY_EXCEPTION`, `ZERO_ROWS`, `MULTIPLE_ROWS` and
`FIELD_OR_PID_INVALID` → `ETB_UNSATISFIED`; `ONE_VALID_ROW` → continue; `NOT_REACHED` only before listener
execution or after an earlier frozen terminal state) and the §10 narrow typed catch structure are unchanged.  A
listener query exception after command availability remains `QUERY_EXCEPTION` → `ETB_UNSATISFIED`, and **no new
convenience `HARNESS_INVALID` path and no blanket classification catch were introduced**.

**21.7 Section-reference hygiene (P3 closure).**  Where this specification refers to the S0/S1 continuity
comparison field set, it names the **ORIGINAL FROZEN ORACLE** artifact
(`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md`) and that artifact's **§15.2** explicitly (§14), so the bare
section number can no longer be confused with this specification's own local §15.2 (the UTF-8 / U+2014
mechanism).

**21.8 Publication-failure stdout and result readback (P3 closure).**  See §15.5 (the single constant line
`ORACLE_R2_PUBLICATION_FAILURE`, with no exception message, stack, provider text or environment data) and §15.4
(final `RESULT_R2` bytes required to be byte-identical to the already validated result temp bytes, with no
second semantic parser and no post-result probe).

**21.9 Config-reader stderr / error semantics (P3 closure).**  The config-reader invocation suppresses stderr
and classifies **only** on the frozen subprocess exit code and the returned reader value.  Stderr suppression
never redefines subprocess success or failure, and the mere existence of stderr text never participates in the
classification; the local `ErrorActionPreference` used for the invocation is restored in the same `finally`
path.  This is scoped strictly to config-reader fidelity.

**End of ETB execution oracle-R2 corrective design R2 candidate.**
