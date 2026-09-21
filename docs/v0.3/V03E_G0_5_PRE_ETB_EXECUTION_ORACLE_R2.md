# DevRelay v0.3-E — G0.5-PRE / SIC — ETB execution oracle R2 (execution-fidelity / output-namespace closure)

> **ETB EXECUTION ORACLE-R2**
> **DESIGN CANDIDATE**
> **NOT ACCEPTED**
> **NOT FROZEN**
> **NOT EXECUTED**
> **DOES NOT EXECUTE ETB**
> **DOES NOT CREATE R2 OUTPUTS**
> **DOES NOT AUTHORIZE ANY ATTEMPT**

Status: **ETB EXECUTION ORACLE-R2 = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EXECUTED**

Baseline: `4a84b12aac0ee3c09e5de67cbec3a61eba446bdc` (branch `v0.3-e-recovery-reconciliation`).

This round is **design / documentation / tracked-executable freeze only**.  Oracle-R2 is not executed here, no
R2 output path or directory is created, no new authorization and no new claim namespace is designed, and
nothing in this artifact authorizes an ETB attempt.

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

## 7. Identity model

After independent acceptance of this candidate, all three values below are **immutable**, and a later
bookkeeping commit, Recovery-R2 authorization commit, operational HEAD or result-review commit must replace
none of them:

| Value | Definition |
| --- | --- |
| `oracle_r2_commit` | the immutable future independently accepted commit containing **both** Oracle-R2 files |
| `oracle_r2_script_sha256` | **committed-blob** SHA-256 of `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1` (the LF byte sequence stored in `oracle_r2_commit`, i.e. `git show <oracle_r2_commit>:docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1`), never a checkout-normalized byte sequence |
| `oracle_r2_spec_sha256` | **committed-blob** SHA-256 of `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.md` |

**7.1 Worktree-identity requirement (fail closed).**  Because the repository uses `* text=auto` with
`core.autocrlf=true` and this round is not authorized to modify `.gitattributes`, a future checkout could
materialize the script with CRLF line endings.  Therefore the future Recovery-R2 authorization **and** the
future executor MUST, before attempt consumption: (i) require the tracked blob hash at `oracle_r2_commit` to
equal `oracle_r2_script_sha256`; (ii) require the worktree file bytes to be **byte-identical** to those
committed blob bytes; and (iii) if they differ for any reason (including checkout line-ending
normalization), **STOP before consuming anything** — the accepted executable bytes are the LF blob bytes, and
a non-identical file must never be executed as Oracle-R2.  This is the only permitted handling; no
normalization, rewrite, re-encoding or "equivalent bytes" substitution is authorized, and no `.gitattributes`
change is made or implied by this round.

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
semantic OpenCode request in between → S0 == S1 on the accepted §15.2 field set.  Native parameter values
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
executor.  The script prints `ORACLE_R2_SCRIPT_SHA256`, `ORACLE_R2_SPEC_SHA256`, `ORACLE_R2_SEMANTIC`,
`ORACLE_R2_CHECKS`, then `ORACLE_R2_PUBLICATION_OK`, `ORACLE_R2_EVIDENCE_SHA256`,
`ORACLE_R2_MANIFEST_SHA256`, `ORACLE_R2_FINAL_CLASSIFICATION` and `ORACLE_R2_SEMANTIC_RESULT`; exit code `0`
means the oracle completed and published, `3` means the publication stage failed (frozen
`HARNESS_INVALID / NO ETB SEMANTIC RESULT`), and any other termination means the attempt produced no trusted
output.

## 18. Static validation performed in this design round

Parser-only syntax validation and static byte/source audits were performed on the tracked `.ps1`; the
operational main path was **not** executed, no listener/process command was run, and the endpoint was not
contacted.

## 19. Current status and sequence

```
ETB EXECUTION ORACLE-R2                   = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EXECUTED
RECOVERY-R1 AUTHORIZATION                 = SPENT / NOT REUSABLE
RECOVERY-R1 ETB ATTEMPT                   = SPENT / NOT REUSABLE
RECOVERY-R1 PUBLISHED ETB RESULT          = REJECTED
AUTHORITATIVE ETB SEMANTIC RESULT         = NONE
NEW_ETB_AUTHORIZATION_REQUIRED            = YES
```

**19.1** No Recovery-R2 authorization exists, no Recovery-R2 claim namespace is designed here, and Oracle-R2
is not usable until independently accepted.

**19.2 Authoritative sequence:** Recovery-R1 attempt consumed → Recovery-R1 candidate result published →
independent result review → Recovery-R1 published result **REJECTED** → authoritative ETB semantic result
NONE → **Oracle-R2 execution-fidelity/output-namespace design (this round)** → independent Oracle-R2 review →
if approved, Oracle-R2 acceptance bookkeeping → independent Oracle-R2 bookkeeping confirmation → Recovery-R2
authorization design → independent Recovery-R2 authorization review → Recovery-R2 acceptance bookkeeping →
independent bookkeeping confirmation → exactly one Recovery-R2 operational ETB attempt → independent
ETB-result review → only an independently accepted `ETB_SATISFIED` may allow Mode-B construction.  **No stage
may be skipped.**

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

**End of ETB execution oracle-R2 design candidate.**
