# DevRelay v0.3-E — G0.5-PRE / SIC — ETB execution oracle PathD (Path-D output-namespace successor)

> **ETB EXECUTION ORACLE-PATHD — DESIGN CANDIDATE**
> **DESIGN CANDIDATE**
> **NOT ACCEPTED**
> **NOT FROZEN**
> **NOT EXECUTED**
> **DOES NOT EXECUTE ETB**
> **DOES NOT CREATE PATH-D OUTPUTS**
> **DOES NOT AUTHORIZE ANY ATTEMPT**
> **DOES NOT AUTHORIZE A LISTENER QUERY**

Status: **ETB EXECUTION ORACLE-PATHD = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EXECUTED**

## 0. Owner decisions (immutable)

```
OWNER DECISION              = D-EXEC-1 — AUTHORIZE NEW PATH-D EXECUTION ORACLE DESIGN
OWNER NAMING DECISION       = N-C — Oracle-PathD
CANONICAL ID TOKEN          = PATH_D
PURPOSE                     = CREATE A NEW EXECUTABLE ORACLE VARIANT WITH A DISTINCT OUTPUT NAMESPACE
PATH-D AUTHORIZATION DESIGN = BLOCKED UNTIL ORACLE-PATHD IS ACCEPTED / FROZEN
PATH-D ETB EXECUTION        = NOT AUTHORIZED
```

**0.1** `D-EXEC-1` authorizes **design only**. It does not authorize oracle execution, ETB execution, listener
query execution, claim consumption or attempt consumption.

**0.2** `N-C` is an explicit Owner naming decision. `Oracle-PathD` is **not** derived from a non-existent
`Recovery-R3` cycle. The canonical `Oracle-R3`, `Oracle-D` and `Oracle-PD` identifiers are **not** used.

## 1. Why Oracle-PathD exists (historical namespace blockers)

Path D (`NEW ETB ATTEMPT`) requires an executable, frozen ETB oracle. All existing oracles are unavailable:

* **BLOCKER 1 — Oracle-R2's output namespace is occupied.** All six Oracle-R2 output paths must be ABSENT
  before its publication work begins (Oracle-R2 spec §11.2). Three of the six finals are **present**
  (`evidence/etb-execution-r2/ETB_EVIDENCE.json`, `evidence/etb-execution-r2/MANIFEST.sha256`,
  `V03E_G0_5_PRE_ETB_EXECUTION_RESULT_R2.md`). Reuse would therefore violate Oracle-R2's own precondition or
  mutate historical artifacts.
* **BLOCKER 2 — the original oracle has no preserved executable.** `V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.ps1`
  does not exist, and its three output finals are also present.
* **BLOCKER 3 — script modification is forbidden.** Oracle-R2 §17.1 forbids extracting, regenerating,
  translating, wrapping or modifying its executable, and §17.4 freezes its invocation with **no parameters**;
  its six output paths are hard-coded. The output namespace therefore cannot be re-pointed by any permitted
  means.

Oracle-PathD resolves all three by being a **new, distinct, immutable object** with a **new output
namespace**. No historical artifact is moved, archived, deleted or overwritten to make room.

## 2. Predecessor identity (Oracle-R2, immutable)

| Item | Value |
| --- | --- |
| `predecessor_oracle_name` | `Oracle-R2` |
| `oracle_r2_commit` | `dfb78f34d919e8c9863a8398fb4f63ee301167bc` |
| `oracle_r2_spec_sha256` | `5e9221e3950af6ec3e0612c4d962562c33e761899dfd6af42d10f5a9895f9f2f` |
| `oracle_r2_script_sha256` | `22c5fbd61da609e6cc39e973be6030d4c360019ed1f56e69ca45f92fa1689c17` |
| Oracle-R2 spec path | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.md` |
| Oracle-R2 script path | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1` |

**2.1** Oracle-R2 and its outputs are **not** modified, renamed, normalized, moved or deleted by this round or
by any future Oracle-PathD execution.

**2.2** Oracle-PathD is the **minimum semantic successor** of the accepted Oracle-R2 executable. Its only
permitted differences are `NEW_ORACLE_IDENTITY`, `NEW_OUTPUT_NAMESPACE`, and the
`MECHANICAL_REFERENCE_FOR_NEW_IDENTITY_OR_NAMESPACE` changes those two require. It is a controlled clone with a
new immutable namespace, **not** a rewrite.

## 3. Frozen artifacts of this round

| Artifact | Role |
| --- | --- |
| `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1` | **normative executable Oracle-PathD implementation** |
| `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.md` | this specification |
| `.gitattributes` | exactly one added narrow LF rule for the new executable (§17) — no wildcard, no other text policy changed, `core.autocrlf` unaltered |

**3.1** No runtime output, claim, evidence, manifest or result is created by this design round.

## 4. Output namespace (new; six exact paths)

| Purpose | Final path | Temp path |
| --- | --- | --- |
| evidence | `docs/v0.3/evidence/etb-execution-path-d/ETB_EVIDENCE.json` | `docs/v0.3/evidence/etb-execution-path-d/ETB_EVIDENCE.json.tmp` |
| manifest | `docs/v0.3/evidence/etb-execution-path-d/MANIFEST.sha256` | `docs/v0.3/evidence/etb-execution-path-d/MANIFEST.sha256.tmp` |
| result | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_D.md` | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_D.md.tmp` |

**4.1** These paths are permanently distinct from the original oracle namespace
(`docs/v0.3/evidence/etb-execution/…`, `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT.md`), from the Oracle-R2
namespace (§2), and from the D1 namespace (`docs/v0.3/evidence/etb-query-diagnostic-d1/…`). **No historical
output path is reused, inspected, deleted, cleaned up or overwritten.**

**4.2 Output precondition.** All six new Path-D paths must be **ABSENT** before publication work begins;
**file OR directory** occupancy at any exact path fails closed. The evidence directory
`docs/v0.3/evidence/etb-execution-path-d` is created by the oracle only if absent; if that exact path exists as
a file, or cannot be created as a directory, the attempt fails closed (`HARNESS_INVALID`).

**4.3 Design-stage occupancy.** At this design-candidate stage all six paths, the namespace directory, and all
four Path-D claim paths of §19 are **ABSENT** (§24.2 records the verified table).

## 5. Identity model

After independent acceptance of this candidate, all three values below are **immutable**, and a later
bookkeeping commit, authorization commit, operational HEAD or result-review commit must replace none of them:

| Value | Definition |
| --- | --- |
| `oracle_path_d_commit` | the immutable future independently accepted commit containing **both** Oracle-PathD files |
| `oracle_path_d_script_sha256` | **committed-blob** SHA-256 of `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1` (the LF byte sequence stored in `oracle_path_d_commit`, i.e. `git show <oracle_path_d_commit>:docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1`), never a checkout-normalized byte sequence |
| `oracle_path_d_spec_sha256` | **committed-blob** SHA-256 of `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.md` |

**5.1** `oracle_path_d_commit` and `oracle_path_d_spec_sha256` are **UNKNOWN** until this design candidate is
committed and independently approved. They are populated **only** by the later independent approval record;
they are **not** executor choices.

**5.2** The future Path-D authorization claim and attempt claim MUST bind to `oracle_path_d_commit`,
`oracle_path_d_spec_sha256` and `oracle_path_d_script_sha256`.

**5.3** A later bookkeeping HEAD, authorization commit, operational HEAD or result-review HEAD must **not**
replace any of those provenance values. `oracle_path_d_commit` is the independently accepted
**oracle-design** commit — never the later bookkeeping commit and never any operational HEAD.

**5.4 Candidate-stage executable identity (recorded now; frozen at acceptance).**

| Item | Value |
| --- | --- |
| executable path | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1` |
| candidate byte length | `31328` |
| candidate worktree SHA-256 | `8bdeb434794c43fe4a199e7338790ba0dbd319728b6766d54299c894a16ac738` |
| encoding | ASCII-only; every byte `<= 0x7F`; **no BOM** |
| line endings | LF only; CR count `0`; exactly one terminal LF |
| parser-only validation | `[System.Management.Automation.Language.Parser]::ParseFile` → **0 parse errors** |
| design-construction baseline | `0bd97206584d0726cf86317de8f385ec2720d423` |
| predecessor oracle | `Oracle-R2` (§2) |
| Owner decisions | `D-EXEC-1`; naming `N-C` |

**5.5** The value under `oracle_path_d_script_sha256` is authoritative **only** after acceptance; the
candidate value above is this round's recorded construction identity.

## 6. Worktree-identity requirement (fail closed)

**6.1** The repository uses `* text=auto` with `core.autocrlf=true`, which would otherwise materialize this
normative executable with CRLF line endings. This round therefore adds exactly **one** narrow tracked
attribute rule (§17), so a **normal canonical checkout** materializes the script as LF bytes independently of
any local `core.autocrlf` value.

**6.2** The future Path-D authorization **and** the future executor MUST, before attempt consumption:
(i) require the tracked blob hash at `oracle_path_d_commit` to equal `oracle_path_d_script_sha256`; (ii) require
the worktree file bytes to be **byte-identical** to those committed blob bytes; and (iii) if they differ for any
reason, **STOP before consuming anything**.

**6.3** The accepted executable bytes are the LF blob bytes. No normalization, rewrite, re-encoding, alternate
checkout, "equivalent bytes" substitution or executor-selected equivalent representation is authorized.

## 7. Listener taxonomy (acceptance critical; preserved verbatim from Oracle-R2 §8)

| Case | Condition | Classification |
| --- | --- | --- |
| **A** | `Get-NetTCPConnection` command/module genuinely unavailable | `HARNESS_INVALID / NO ETB SEMANTIC RESULT` |
| **B** | cmdlet exists, but the exact frozen listener query raises an access / provider / query / execution exception | `ETB_UNSATISFIED` |
| **C** | exact query successfully returns zero matching rows | `ETB_UNSATISFIED` |
| **D** | exact query returns more than one matching row | `ETB_UNSATISFIED` |
| **E** | exactly one row, but required listener field/PID validation fails | `ETB_UNSATISFIED` |
| **F** | exactly one valid matching row | continue the target-binding procedure |

**7.1** **No blanket `catch { HARNESS_INVALID }` is permitted around the listener/snapshot procedure.**

## 8. Command availability and query error handling (preserved)

**8.1** The script performs an explicit, deterministic availability branch **before** the exact listener
query, using one mechanism only: `Get-Command -Name <name> -ErrorAction SilentlyContinue`; a `$null` result
means unavailable. Availability is **never** inferred from the shape of a listener-query exception.

**8.2** The exact listener query is `@(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 4096 -State
Listen -ErrorAction SilentlyContinue -ErrorVariable qerr)` inside its own **narrow** `try`/`catch` boundary.

**8.3** Deterministic listener-probe decision order (frozen):

1. a terminating exception from that call → `QUERY_EXCEPTION` → `ETB_UNSATISFIED`;
2. a collected non-terminating error whose `FullyQualifiedErrorId` matches `*CmdletizationQuery_NotFound*`
   **and** zero rows → `ZERO_ROWS` → `ETB_UNSATISFIED`;
3. any other collected non-terminating error → `QUERY_EXCEPTION` → `ETB_UNSATISFIED`;
4. no error and zero rows → `ZERO_ROWS` → `ETB_UNSATISFIED`;
5. no error and more than one row → `MULTIPLE_ROWS` → `ETB_UNSATISFIED`;
6. no error and exactly one row → field/PID validation → `FIELD_OR_PID_INVALID` → `ETB_UNSATISFIED`, or
   `ONE_VALID_ROW` → continue.

**8.4** A no-match condition surfaced by PowerShell 5.1 / `ErrorAction` semantics as a terminating exception
is therefore classified `ETB_UNSATISFIED` (case B), never `HARNESS_INVALID`. **The PowerShell exception form
alone can never produce `HARNESS_INVALID` from the listener stage.**

## 9. No global classification catch (preserved)

**9.1** The script contains **no** outer/general catch that maps arbitrary snapshot or listener exceptions to
`HARNESS_INVALID`. Its `catch` blocks are narrow and typed:

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

## 10. Target-binding chain (preserved)

endpoint tuple → exact listener query and uniqueness → `OwningProcess` → PID-scoped `Win32_Process` query
(`ProcessId`, `ExecutablePath`, `CreationDate`) → process-instance identity (PID **and** `CreationDate.Ticks`)
→ `CreateFileW`/`GetFinalPathNameByHandleW` canonicalization of **both** the process-reported `ExecutablePath`
and the accepted target literal (AS-IS `\\?\` text, `-ceq` comparison) → dual `Get-FileHash -Algorithm SHA256`
equal to `578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35` → exact `package.json` identity
(`opencode-ai`, `1.18.11`, `bin.opencode` resolving under the accepted package root to the accepted
executable, canonicalized and compared `-ceq`) → S0 → S1 with no HTTP and no semantic OpenCode request in
between → S0 == S1 on the continuity comparison field set frozen by the **ORIGINAL FROZEN ORACLE** artifact
(`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md`), section **§15.2 of that artifact** — expressly **not** any section of this specification.

**10.1** Preserved exactly, unchanged: Mode P (pre-existing target); owner endpoint
`http://127.0.0.1:4096`; no endpoint discovery; no fallback; no IPv6; no `localhost` alias; no alternate port;
no Mode L; no OpenCode start/restart; no HTTP; no `/doc`; no `/session`; no provider/model call; listener
uniqueness requirement. Native parameter values (`GENERIC_READ 0x80000000`, share `0x00000007`,
`OPEN_EXISTING 3`, `FILE_ATTRIBUTE_NORMAL 0x80`, flags `0`, `StringBuilder(32768)`) and the
`DevRelayEtbNativeV1` declarations are the accepted ones. **No accepted target-binding condition is weakened.**

## 11. Evidence schema and the single audit field

**11.1** The top-level evidence contract is the accepted closed **16-field** contract in the accepted order,
carrying the distinct schema identity **`devrelay-etb-v1-path-d`**; the script writes that exact string and
asserts it on read-back:

```
schema_version, oracle_commit, oracle_sha256, execution_started_at, execution_finished_at,
mode, endpoint, configured_base_url, target, snapshot_s0, snapshot_s1, checks,
listener_probe_outcome, outcome, non_claims, activity_counters
```

**11.2 Schema identity separation (frozen).** `devrelay-etb-v1` denotes only the **historical original closed
schema** of the original frozen oracle. `devrelay-etb-v1-r2` denotes only the **Oracle-R2** schema. Neither is
used, reused or reinterpreted by Oracle-PathD. The three identities are distinct and none reinterprets another.
**No semantic field meaning is altered.**

**11.3 `listener_probe_outcome`** — type: JSON string; exact allowed values (enum), unchanged from Oracle-R2:

| Value | Meaning | Bound classification |
| --- | --- | --- |
| `COMMAND_UNAVAILABLE` | `Get-NetTCPConnection` unavailable | `HARNESS_INVALID` |
| `QUERY_EXCEPTION` | exact query raised an exception/error | `ETB_UNSATISFIED` |
| `ZERO_ROWS` | exact query returned zero rows | `ETB_UNSATISFIED` |
| `MULTIPLE_ROWS` | exact query returned more than one row | `ETB_UNSATISFIED` |
| `ONE_VALID_ROW` | exactly one row and all field/PID validations passed | continue |
| `FIELD_OR_PID_INVALID` | one row but field/PID validation failed | `ETB_UNSATISFIED` |
| `NOT_REACHED` | only valid before the listener stage, or when an earlier frozen terminal condition already ended the attempt | (no listener classification) |

**11.4 S0/S1 semantics of the single published field (frozen, not executor-selectable).** The single published
`listener_probe_outcome` field always means **THE LISTENER PROBE OUTCOME ASSOCIATED WITH THE LAST ACTUALLY
EXECUTED SNAPSHOT PROBE THAT DETERMINES OR CONTRIBUTES TO THE PUBLISHED TERMINAL RESULT**, resolved
mechanically as: `NOT_REACHED` when failure occurs before any listener probe; the S0 listener outcome when S0
terminates the attempt; the S1 listener outcome when S0 succeeds with `ONE_VALID_ROW` and S1 terminates the
attempt; `ONE_VALID_ROW` when both probes succeed. The script implements this as a **total** assignment.
**"S0 or S1?" is therefore never executor-selectable.**

**11.5** The published semantic `outcome` **must agree** with this field. The script derives the outcome from
the same decision that produces the field, and the frozen read-back verification additionally requires the
serialized `listener_probe_outcome` and `outcome` to equal the in-memory values; a mismatch therefore surfaces
as the frozen evidence-machinery `HARNESS_INVALID` — it is **not** executor-selectable. No raw exception
message, stack trace, prompt, response or reasoning is persisted.

**11.6** `checks` keeps the accepted 18 keys and the accepted `PASS` / `FAIL` / `NOT_REACHED` vocabulary.
`activity_counters` keeps the accepted 14 keys, all `0` for a compliant attempt. `non_claims` keeps the
accepted six ordered strings. `endpoint` and `target` keep the accepted ordered sub-objects. Snapshots keep the
accepted 25-field order. Unobserved fields use only the accepted truthful placeholders.

## 12. Result taxonomy (unchanged; three classes only)

`ETB_SATISFIED`; `ETB_UNSATISFIED`; `HARNESS_INVALID / NO ETB SEMANTIC RESULT`. No new class; no `PASS`,
`FAIL`, `PARTIAL`, `UNKNOWN`, `PROBABLE` or `RETRY`. **No result is selected in this design round.**

## 13. Result artifact, encoding and publication order

**13.1 Publication order (frozen).** `ETB_EVIDENCE.json` → `MANIFEST.sha256` → `RESULT_PATH_D` **last**, using
the two-argument `System.IO.File.Move` (no overwrite), each followed by read-back byte verification, and then
the frozen post-publication verification. The manifest covers **only** `ETB_EVIDENCE.json`: one line,
`<64-lowercase-sha256>` + two ASCII spaces + `docs/v0.3/evidence/etb-execution-path-d/ETB_EVIDENCE.json` + LF.
No rewrite after publication.

**13.2 Result artifact template.** The accepted template is preserved exactly, written as UTF-8, **no BOM**,
LF only, exactly one final LF, and read back and byte-verified before success. The final `RESULT_PATH_D` bytes
are required to be **byte-identical** to the already validated result temp bytes; **no second semantic parser**
of the published result is added, and no post-result probe of any kind follows.

**13.3 UTF-8 / U+2014 mechanism (frozen).** The source is **ASCII-only** (every byte `<= 0x7F`; verified
mechanically in this round). The em dash is constructed at runtime exactly as `$EmDash = [char]0x2014` and
serialized through `[System.Text.UTF8Encoding]::new($false)`, so the published result artifact contains the
exact UTF-8 bytes `E2 80 94` for U+2014 in its first line. The script verifies the presence of those three
bytes in the result temp before publication.

**13.4 Publication-failure stdout (frozen constant).** If any failure occurs anywhere inside the delimited
evidence/publication region, the executable emits exactly the single constant stdout line
**`ORACLE_PATH_D_PUBLICATION_FAILURE`** and nothing else on that line — no exception message, stack trace,
provider text, file path, environment data or partially written output is captured, persisted or printed —
followed by `ORACLE_PATH_D_FINAL_CLASSIFICATION=HARNESS_INVALID`, `ORACLE_PATH_D_SEMANTIC_RESULT=NONE` and exit
code `3`. No other publication-failure stdout exists.

**13.5 Complete stdout contract (frozen).** `ORACLE_PATH_D_SCRIPT_SHA256`, `ORACLE_PATH_D_SPEC_SHA256`,
`ORACLE_PATH_D_SEMANTIC`, `ORACLE_PATH_D_CHECKS`, and then exactly one of the two terminal surfaces — the
success surface `ORACLE_PATH_D_PUBLICATION_OK`, `ORACLE_PATH_D_EVIDENCE_SHA256`,
`ORACLE_PATH_D_MANIFEST_SHA256`, `ORACLE_PATH_D_FINAL_CLASSIFICATION`, `ORACLE_PATH_D_SEMANTIC_RESULT`, or the
publication-failure surface of §13.4. **No other stdout line exists.** Exit code `0` means the oracle completed
and published, `3` means the publication stage failed (frozen `HARNESS_INVALID / NO ETB SEMANTIC RESULT`), and
any other termination means the attempt produced no trusted output.

## 14. Mandatory stop

**14.1** The normative executable terminates immediately after final result publication and the frozen
verifications. After result publication it performs **no** `Get-Command`, `Get-NetTCPConnection`,
`Get-CimInstance`, endpoint inspection, listener/process inspection, availability probe, diagnostic, repair,
reclassification or additional evidence collection. No "helpful" post-result check and no report-time probe.

## 15. Tracked executable requirement (self-containment)

**15.1** The `.ps1` file **is** the future executable. A future executor **must not** extract the script from
this Markdown, generate a temporary script, copy/paste function bodies into another script, translate to
Python, wrap it in another classification layer, inject assertions, or modify it before execution.

**15.2** Complete operational behavior is determinable from the tracked `.ps1` bytes plus this specification.
No behavior depends on chat instructions, executor memory, temporary generated code, untracked helper scripts
or interactive judgment. All helper functions are contained in the tracked `.ps1`; the only external
primitives are the exact named standard PowerShell/.NET commands and APIs frozen here.

**15.3 Exact future execution invocation** (frozen shape; run from the repository root):

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1"
```

No parameters, no wrapper, no redirection that alters stdout semantics, and no post-execution probing by the
executor.

**15.4** The repository root is derived deterministically from the tracked script location (`$PSScriptRoot` is
`<repo>/docs/v0.3`, so its grandparent is `<repo>`); no absolute repository path is hard-coded.

**15.5 Config-reader invocation fidelity (preserved).** The normative executable MUST deterministically
establish `<repo>/src` as `PYTHONPATH` for the config-reader subprocess:

```
PYTHONPATH=<repo>/src
python -c "<frozen config reader>" "<repo>"
```

The process-level `PYTHONPATH` is captured first and restored on every exit path through a deterministic
`finally` block — the prior value when one existed, **absence** when none existed. `PYTHONPATH` for this
invocation resolves to `<repo>/src` **only**: never merged, prepended or appended. Stderr is suppressed and
never participates in classification. **The executor has no choice in this mechanism.**

## 16. Preconditions for the future Path-D authorization (PRE-* contract)

The future Path-D authorization MUST require, at minimum, all of the following. Every check is **read-only**.

| ID | Required condition |
| --- | --- |
| **PRE-1** | current branch is `v0.3-e-recovery-reconciliation` |
| **PRE-2** | the tracked blob hash at `oracle_path_d_commit` for the executable equals `oracle_path_d_script_sha256` |
| **PRE-3** | the tracked blob hash at `oracle_path_d_commit` for the specification equals `oracle_path_d_spec_sha256` |
| **PRE-4** | the **current worktree** executable bytes are **byte-identical** to that committed blob (no normalized-equivalent acceptance) |
| **PRE-5** | a read-only git attribute check resolves the normative executable to `text: set` and `eol: lf` |
| **PRE-6** | the tracked worktree contains **no** tracked modification and **no** staged path |
| **PRE-7** | `.devrelay/config.yaml` is present with `SHA-256 = b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf`, `size = 1897`, and production-resolved `opencode.base_url = http://127.0.0.1:4096`, read **only** through the frozen reader shape of §15.5 |
| **PRE-8** | `CONFIG_ESTABLISHMENT` is present exactly at `docs/v0.3/evidence/etb-execution/CONFIG_ESTABLISHMENT.json` with `SHA-256 = ea9fc2bc564cfd6d613e3145703f28d80bb87eb89dcdecaf7ad43b52d7bd9300` (accepted semantic status remains `VALID / PRESENT`) |
| **PRE-9** | all historical claim markers still exist with their accepted SHA-256 values, and **no** historical claim, evidence, manifest or result has been modified, deleted, renamed or archived |
| **PRE-10** | **all four** Path-D claim paths of §19 are **ABSENT** under the §19.2 occupancy predicate |
| **PRE-11** | **all six** Path-D output paths of §4 are **ABSENT** under the same file-or-directory occupancy predicate |
| **PRE-12** | **no** Path-D authorization claim and **no** Path-D attempt claim has yet been consumed |
| **PRE-13** | no historical authorization or attempt budget is reset, reopened or reused |

**16.1** PRE-12 is physically entailed by the PRE-10 ABSENT result (a consumption point is the successful
`CreateNew` of the corresponding TEMP path); no separate probe beyond the occupancy predicate is permitted.

**16.2** Failure of **any** PRE-* condition → **STOP BEFORE CONSUMING ANYTHING**. No repair. No retry. No
fallback. No claim is created, no config is touched, no oracle is entered.

**16.3** Historical occupied paths are **irrelevant** to these preconditions because they are not reused; they
must remain untouched.

## 17. Tracked attributes (LF contract)

`.gitattributes` gains exactly **one** narrow rule:

```
docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1 text eol=lf
```

**17.1** No repository-wide `*.ps1` rule is added, no other text policy is changed, and `core.autocrlf` is not
altered. `git check-attr text eol -- docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1` resolves to
`text: set` and `eol: lf`.

## 18. Claim lineage (new; permanently distinct)

```
LINEAGE = PATH_D
```

| Marker | Temp path | Final path |
| --- | --- | --- |
| Path-D authorization claim | `docs/v0.3/evidence/ETB_PATH_D_AUTHORIZATION_USE.claim.tmp` | `docs/v0.3/evidence/ETB_PATH_D_AUTHORIZATION_USE.claim` |
| Path-D ETB attempt claim | `docs/v0.3/evidence/ETB_PATH_D_ATTEMPT_USE.claim.tmp` | `docs/v0.3/evidence/ETB_PATH_D_ATTEMPT_USE.claim` |

**18.1** These are **new** identities. They do **not** reset, reopen or reuse `ETB_RECOVERY_R2_*`,
`ETB_QUERY_DIAGNOSTIC_D1_*`, `ETB_RECOVERY_R1_*` or the original `ETB_*` claims. All historical claim paths
remain reserved forever. No historical claim path may be reused.

**18.2** No other claim path may be created under this oracle.

**18.3 Occupancy predicate (frozen).**

```
CLAIM_PATH_OCCUPIED(path) := [System.IO.File]::Exists(path) -or [System.IO.Directory]::Exists(path)
ABSENT                    := File.Exists(path) == false AND Directory.Exists(path) == false
```

A file, a **directory**, a partial file, a malformed file or a zero-length file at one of these exact paths
counts as **OCCUPIED** and fails closed. No deletion. No cleanup. No overwrite. No rename.

## 19. Consumption boundary

**19.1** This oracle design round creates **no** execution budget and consumes **nothing**. The oracle carries
no claim writer and no authorization logic; the future Path-D authorization owns claim creation.

**19.2** **ORACLE DESIGN ACCEPTANCE MUST NOT BE CONFLATED WITH PATH-D EXECUTION AUTHORIZATION.** After this
oracle is accepted and frozen, Path D **returns to** its previously blocked `NEW ETB EXECUTION AUTHORIZATION
DESIGN` stage, which must then bind `oracle_path_d_commit`, `oracle_path_d_spec_sha256` and
`oracle_path_d_script_sha256`.

## 20. Fail-closed semantics (preserved)

Any failed precondition → **STOP BEFORE EXECUTION CONSUMPTION**. Any script-integrity mismatch → `HARNESS
INVALID / STOP`. No automatic repair. No cleanup. No output overwrite. No retry. No fallback. No endpoint
discovery. No alternate port. No `localhost` alias. No IPv6 alternate. No OpenCode start/restart. No HTTP. No
`/doc`. No provider call.

## 21. Semantic diff vs Oracle-R2

**21.1** An exhaustive line-level diff of the accepted Oracle-R2 executable against this candidate yields
**43 added / 39 removed** lines across **19 hunks**. Every hunk maps to exactly one permitted category:

| Category | Hunks |
| --- | --- |
| `NEW_ORACLE_IDENTITY` | header title and identity banner; `$OraclePathDSpecPath` / `$OraclePathDScriptPath` constants and their uses; `ORACLE_PATH_D_SCRIPT_SHA256` / `ORACLE_PATH_D_SPEC_SHA256` / `ORACLE_PATH_D_SEMANTIC` / `ORACLE_PATH_D_CHECKS` / `ORACLE_PATH_D_PUBLICATION_OK` / `ORACLE_PATH_D_PUBLICATION_FAILURE` / `ORACLE_PATH_D_EVIDENCE_SHA256` / `ORACLE_PATH_D_MANIFEST_SHA256` / `ORACLE_PATH_D_FINAL_CLASSIFICATION` / `ORACLE_PATH_D_SEMANTIC_RESULT`; `ORACLE_PATH_D_OUTPUT_*` failure constants; schema identity `devrelay-etb-v1-path-d` (write and read-back assert) |
| `NEW_OUTPUT_NAMESPACE` | the six output paths (final and temp) and `$PathDDir` |
| `MECHANICAL_REFERENCE_FOR_NEW_IDENTITY_OR_NAMESPACE` | comments that named the predecessor identity (`corrective R2` → current identity), with no semantic content |

```
ORACLE_SEMANTIC_DRIFT = NONE
```

**21.2** The following are **absent from the diff** and therefore provably unchanged: the listener predicate
and its decision order; the endpoint tuple and `configured_base_url`; the accepted target literal and
`$ExpectedSha` / `$ExpectedVersion` / `$PackageRoot` / `$PackageManifest`; `$OriginalOracleCommit` /
`$OriginalOracleSha`; the `$Checks` key set; the `New-Snapshot` field set; the S0/S1 continuity comparison
field set; `Get-CanonicalPath`; the native declarations and parameter values; the config-reader mechanism; the
publication order and all read-back verifications; the result template; the `$EmDash` mechanism; the `non_claims`
list; the `activity_counters` key set; the three result classes.

## 22. Historical preservation

**22.1** This round does **not** modify, move, archive, normalize or delete: the Oracle-R2 spec, executable or
outputs; the Recovery-R1 artifacts; the Recovery-R2 authorization, claims, evidence, manifest or result; the
D1 authorization, claims, evidence, manifest or result; the original spent claims; the original oracle
evidence, manifest or result; `CONFIG_ESTABLISHMENT.json`; or any historical status surface other than the two
permitted candidate-state entries of §23.

**22.2** Config remains the exact post-image (§16 PRE-7); Oracle-PathD does not mutate config and does not
republish `CONFIG_ESTABLISHMENT`.

**22.3** Preserved downstream state: `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED`; Recovery-R2
authorization / attempt = `SPENT / NOT REUSABLE`; `D1 AUTHORIZATION / ATTEMPT = SPENT / NOT REUSABLE`;
`D1 LISTENER QUERY = EXECUTED ONCE`; Mode-B = `BLOCKED / NOT RUN`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 =
`NOT CLOSED`; G0.5 execution / Case-C / v0.3-E implementation **NOT AUTHORIZED**; `G1`/`G2` **NOT RUN**;
`adopt_completed_turn` **DISABLED**; **PATH C = NO STATIC BASIS / NOT AUTHORIZED**.

**22.4 MODEL A (preserved).** Future execution-generated operational artifacts remain **untracked and
byte-immutable** where the accepted contract requires; tracked governance state advances only through the
established status surfaces (`CHANGELOG.md`, `docs/v0.3/V03E_ACCEPTANCE.md`). No generated execution evidence
is committed in this design round.

## 23. Current status and sequence

```
ETB EXECUTION ORACLE-PATHD (this candidate) = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EXECUTED
OWNER DECISION                              = D-EXEC-1
OWNER NAMING DECISION                       = N-C — Oracle-PathD
CANONICAL ID TOKEN                          = PATH_D
PATH-D AUTHORIZATION DESIGN                 = BLOCKED PENDING ORACLE ACCEPTANCE
PATH-D ETB EXECUTION                        = NOT AUTHORIZED
ORACLE EXECUTION                            = NOT AUTHORIZED
LISTENER QUERY                              = NOT EXECUTED
PATH C                                      = NO STATIC BASIS / NOT AUTHORIZED
```

**23.1 Authoritative sequence:** D-EXEC-1 owner decision → Oracle-PathD design candidate `[THIS ROUND]` →
independent Oracle-PathD design review → only if approved: Oracle-PathD acceptance bookkeeping → independent
bookkeeping confirmation → **resume** Path-D `NEW ETB EXECUTION AUTHORIZATION DESIGN` → independent
authorization review → authorization acceptance bookkeeping → independent bookkeeping confirmation → exactly
one Path-D authorization consumption → exactly one Path-D ETB attempt consumption → exactly one ETB execution →
independent ETB-result review → only an independently accepted `ETB_SATISFIED` may allow Mode-B construction.
**No stage may be skipped.**

**23.2 Status surfaces.** This candidate round updates only `CHANGELOG.md` and `docs/v0.3/V03E_ACCEPTANCE.md`,
recording: `OWNER = D-EXEC-1`; `OWNER NAMING DECISION = N-C / Oracle-PathD`; `ORACLE-PATHD = DESIGN CANDIDATE /
REQUIRES INDEPENDENT REVIEW`; `PATH-D AUTHORIZATION DESIGN = BLOCKED PENDING ORACLE ACCEPTANCE`;
`PATH-D ETB EXECUTION = NOT AUTHORIZED`. **No acceptance or freeze is recorded.**

## 24. Design-round activity counters and non-claims

**24.1** This design round performed: oracle executions `0`; ETB executions `0`; listener queries `0`;
`Get-NetTCPConnection` calls `0`; claim creations `0`; evidence/manifest/result creations `0`; budget
consumptions `0`; config mutations `0`; HTTP `0`; provider/model calls `0`; SIC `0`; Mode-B `0`; G0.5/G1/G2 `0`;
runtime/test/dependency/version changes `0`; historical-artifact mutations `0`; historical namespace reuses `0`.

**24.2 Namespace occupancy at design time (verified; all ABSENT).** All six §4 paths, the
`docs/v0.3/evidence/etb-execution-path-d` directory, and all four §18 claim paths were verified **ABSENT** under
the file-or-directory occupancy predicate.

**24.3** This candidate does **not** claim: Oracle-PathD accepted; Oracle-PathD frozen; Oracle-PathD executed;
Path-D authorized; Path D executable today; a claim exists; a prior oracle defective; `ETB_SATISFIED`;
`ETB_UNSATISFIED` proven or disproven by anything here; P6 PASS/FAIL; G0.5 PASS/FAIL; Mode-B authorized; root
cause determined.

**24.4** The 43/39-line diff of §21.1 is a **GOVERNANCE-TEXT AND IDENTITY DELTA**, not an execution-semantic
delta; §21.2 enumerates the execution semantics proven unchanged by their absence from that diff.

**End of ETB execution oracle PathD design candidate.**
