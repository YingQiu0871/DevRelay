# DevRelay v0.3-E — G0.5-PRE / SIC — ETB QUERY_EXCEPTION DIAGNOSTIC D1 (corrective design R1 candidate)

> **ETB QUERY_EXCEPTION DIAGNOSTIC D1 — CORRECTIVE DESIGN R1**
> **DESIGN CANDIDATE**
> **NOT ACCEPTED**
> **NOT AUTHORIZED**
> **NOT EXECUTED**
> **EXECUTES NOTHING**
> **CREATES NO CLAIM NOW**
> **CREATES NO EVIDENCE NOW**
> **DOES NOT TOUCH THE AUTHORITATIVE RECOVERY-R2 RESULT**
> **DIAGNOSTIC OBSERVATIONS CAN NEVER BECOME ETB SEMANTIC RESULTS**
> **SUPERSEDES THE REJECTED INITIAL CANDIDATE `78266c954087b33baf5a12dfab1cbdef845a0bbb` (REQUEST_CHANGES — P0 = 0, P1 = 0, P2 = 1, P3 = 2)**

Status: **ETB QUERY_EXCEPTION DIAGNOSTIC D1 = CORRECTIVE DESIGN R1 = DESIGN CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED / NOT EXECUTED**

## 0. Owner decision (PATH B — new diagnostic-design stage)

The human owner elected **PATH B — NEW DIAGNOSTIC-DESIGN STAGE**: G0.5-PRE work continues **only** by
designing a new, separately authorized, read-only diagnostic stage whose sole purpose is to capture the
missing listener-query failure information behind the already authoritative Recovery-R2 result. This owner
decision does **not** authorize execution, another ETB attempt, another Recovery-R2 attempt, Mode-B, G0.5, P6,
SIC, G1/G2 or v0.3-E implementation.

## 1. Authoritative starting state (immutable; D1 binds to it)

Starting bookkeeping HEAD: `93e44fe61c59ec5070e2823062a607347bb9163a` (branch
`v0.3-e-recovery-reconciliation`), the authoritative result-bookkeeping commit of the Recovery-R2 attempt.

| Item | Value |
| --- | --- |
| `AUTHORITATIVE ETB SEMANTIC RESULT` | `ETB_UNSATISFIED` |
| `RECOVERY-R2 AUTHORIZATION` | `ACCEPTED / FROZEN / FULLY CONSUMED` |
| `RECOVERY-R2 AUTHORIZATION USE` | `SPENT / NOT REUSABLE` |
| `RECOVERY-R2 ETB ATTEMPT` | `SPENT / NOT REUSABLE` |
| Oracle-R2 invocation count | `1 / MAXIMUM REACHED` |
| Mode-B | `BLOCKED / NOT RUN` |
| `P6` | `UNPROVEN / UNSATISFIED` |
| G0.5 | `NOT CLOSED` |
| `NEW RECOVERY AUTHORIZATION` | `NONE` |
| Case-C | `NOT AUTHORIZED` |
| v0.3-E implementation | `NOT AUTHORIZED` |
| `G1`/`G2` | `NOT RUN` |
| `adopt_completed_turn` | `DISABLED` |

## 2. This round is design only

No listener query was executed in this round; no `Get-NetTCPConnection` invocation occurred; no Oracle-R2 or
old-oracle execution occurred; no diagnostic claim, evidence, result or output directory was created; no live
listener/process state was inspected; no live `Get-CimInstance`, operational P/Invoke, target-executable
hash, `OpenCode --version`, HTTP, `/doc`, `/session` or provider/model call occurred; config,
`CONFIG_ESTABLISHMENT`, Recovery-R2 artifacts, R1 artifacts, the accepted Recovery-R2 authorization, the
Oracle-R2 spec/script and `.gitattributes` were not modified; SIC, Mode-B and G0.5/G1/G2 were not run; no
runtime/test/dependency/version change occurred; no push, merge, tag or release. **No `.ps1` executable is
created in this round.**

## 3. Source finding that D1 addresses

**ROOT_CAUSE_IDENTIFIABILITY = PARTIALLY_CONSTRAINED**
**STATIC_ORACLE_R2_LISTENER_DEFECT = NOT_PROVEN**

Known (independently reconciled from the authoritative published state):

- the frozen R2 listener branch produced `QUERY_EXCEPTION`;
- `COMMAND_UNAVAILABLE` was ruled out (`listener_probe_outcome = QUERY_EXCEPTION`, and the availability
  branch is a distinct frozen class);
- config reader failure was ruled out (`config_exact = PASS` in the published evidence);
- native type-load failure was ruled out (`terminal_stage = s0_listener`, not a native-stage failure);
- `ZERO_ROWS`, `MULTIPLE_ROWS` and `FIELD_OR_PID_INVALID` were not the published branch;
- the R2 classification `QUERY_EXCEPTION → ETB_UNSATISFIED` is authoritative.

Unknown (the diagnostic unknowns D1 exists to resolve):

- whether `QUERY_EXCEPTION` came from the **terminating catch path** or the **error-record path**;
- exception type;
- `FullyQualifiedErrorId`;
- `CategoryInfo` (activity/reason/target name/target type);
- exception message;
- inner exception;
- HResult / native / provider / CIM details;
- PowerShell environment identity;
- `Get-NetTCPConnection` command/module identity (NetTCPIP module version);
- whether the failure was access/permissions related;
- whether the failure was transient;
- what the same exact query actually returns in a later diagnostic observation.

## 4. D1 non-goals (frozen)

D1 is **NOT** an ETB semantic attempt. D1 cannot produce `ETB_SATISFIED`, `ETB_UNSATISFIED` or
`HARNESS_INVALID` as a replacement or successor ETB semantic result. D1 cannot: change the authoritative
Recovery-R2 `ETB_UNSATISFIED` result; reopen Recovery-R2 budgets; satisfy P6; fail P6; close G0.5; authorize
Mode-B; perform process binding; perform executable identity binding; perform package/version target
binding; perform S0/S1 ETB continuity; or perform HTTP/provider/model operations. **Even if the diagnostic
observation later sees a listener row, that observation MUST NOT be promoted to `ETB_SATISFIED`.**

## 5. Diagnostic target (frozen)

The future diagnostic implementation uses the **same listener-query shape** as accepted Oracle-R2 so its
failure details are directly comparable with Recovery-R2:

- cmdlet: `Get-NetTCPConnection`
- arguments: `-LocalAddress '127.0.0.1'`, `-LocalPort 4096`, `-State Listen`

No alternate address, no `localhost` substitution, no IPv6, no alternate port, no port discovery, no
first-free port.

## 6. Future query execution limit (frozen)

Diagnostic listener-query invocation maximum = **1**. No retry, no repeat, no delayed second sample, no
polling, no "confirmatory" second invocation, no alternate command, no equivalent CIM reconstruction, no
fallback query. This budget is **diagnostic-only** and wholly distinct from Recovery-R2 (which remains
permanently `SPENT / NOT REUSABLE`).

## 7. New D1 namespace (reserved; nothing created this round)

| Kind | Path |
| --- | --- |
| authorization claim TEMP | `docs/v0.3/evidence/ETB_QUERY_DIAGNOSTIC_D1_AUTHORIZATION_USE.claim.tmp` |
| authorization claim FINAL | `docs/v0.3/evidence/ETB_QUERY_DIAGNOSTIC_D1_AUTHORIZATION_USE.claim` |
| attempt claim TEMP | `docs/v0.3/evidence/ETB_QUERY_DIAGNOSTIC_D1_ATTEMPT_USE.claim.tmp` |
| attempt claim FINAL | `docs/v0.3/evidence/ETB_QUERY_DIAGNOSTIC_D1_ATTEMPT_USE.claim` |
| evidence directory | `docs/v0.3/evidence/etb-query-diagnostic-d1/` |
| evidence FINAL | `docs/v0.3/evidence/etb-query-diagnostic-d1/QUERY_DIAGNOSTIC_EVIDENCE.json` |
| evidence TEMP | `docs/v0.3/evidence/etb-query-diagnostic-d1/QUERY_DIAGNOSTIC_EVIDENCE.json.tmp` |
| manifest FINAL | `docs/v0.3/evidence/etb-query-diagnostic-d1/MANIFEST.sha256` |
| manifest TEMP | `docs/v0.3/evidence/etb-query-diagnostic-d1/MANIFEST.sha256.tmp` |
| result FINAL | `docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_DIAGNOSTIC_RESULT_D1.md` |
| result TEMP | `docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_DIAGNOSTIC_RESULT_D1.md.tmp` |

These paths are permanently distinct from the original/R1/R2 claim namespaces and from **all** oracle output
namespaces. **None of these paths may be created in this design round.**

## 8. Future D1 budgets (wholly independent from Recovery-R2)

| Budget | Value |
| --- | --- |
| D1 AUTHORIZATION USE | **1 OF 1** |
| D1 DIAGNOSTIC ATTEMPT | **1 OF 1** |
| D1 LISTENER QUERY INVOCATION | **MAXIMUM 1** |

Recovery-R2 remains permanently `SPENT / NOT REUSABLE`. Defining these budgets **does not grant their use**:
after this round D1 remains `DESIGN CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED / NOT EXECUTED`,
D1 AUTHORIZATION USE = `UNAVAILABLE / NOT YET GRANTED`, D1 DIAGNOSTIC ATTEMPT =
`UNAVAILABLE / NOT YET GRANTED`, and the D1 claim namespace/evidence schema are only DEFINED BY DESIGN
CANDIDATE.

## 9. Future D1 authorization identity model (no self-reference)

Future provenance, populated **only** by the later independent acceptance record (never by the executor):

- `diagnostic_d1_design_commit` = the independently accepted **D1 design** commit;
- `diagnostic_d1_spec_sha256` = SHA-256 of
  `docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_EXCEPTION_DIAGNOSTIC_D1_SPEC.md` at that accepted design commit.

A future implementation/execution authorization may additionally bind its own accepted executable SHA-256.
This spec does **not** embed its own candidate commit hash or its own blob SHA (no self-reference).

## 10. Source-result binding (permanent, immutable)

D1 permanently binds itself to the immutable source state it diagnoses:

| Item | Value |
| --- | --- |
| authoritative result-bookkeeping HEAD | `93e44fe61c59ec5070e2823062a607347bb9163a` |
| Recovery-R2 evidence SHA-256 | `6f903f05e859a05a99dc0cde253e878ae7235c1554e212ab2f6b27945b2da0c8` |
| Recovery-R2 manifest SHA-256 | `b4701c900132ffee9d9f31ac7c7137c906da80de97a08678544c7d7d7eb522c1` |
| Recovery-R2 result SHA-256 | `84f51bb5d7765112cb65376ea164e10780bb777f1beb6e962d6baa4508fe9efa` |
| Recovery-R2 authorization claim SHA-256 | `fd7336e4694f8d491ddd3067880851f96974a29a1117d48f7dd47eb2d629ccf7` |
| Recovery-R2 attempt claim SHA-256 | `69eb6ef0352375311f72c211d04c8ed39e59d8f7b00b6d7738577044916167f9` |
| accepted Recovery-R2 authorization identity | `02bef765f74d7349c592138b35280b8b51995a5d` / `91917bb55cc5b59a811c6a5f7bcbc3bf48ffa4f5688c379914912fe6f092d4ab` |
| accepted Oracle-R2 identity | `dfb78f34d919e8c9863a8398fb4f63ee301167bc` / `5e9221e3950af6ec3e0612c4d962562c33e761899dfd6af42d10f5a9895f9f2f` / `22c5fbd61da609e6cc39e973be6030d4c360019ed1f56e69ca45f92fa1689c17` |
| authoritative published branch | `listener_probe_outcome = QUERY_EXCEPTION`, `outcome = ETB_UNSATISFIED`, `terminal_stage = s0_listener` |

D1 observations MUST NOT rewrite or supersede any of these identities.

## 11. Future allowed environment metadata (closed categories)

The future diagnostic implementation may read **only** the environment metadata needed to explain the
listener query:

| Category | Allowed fields |
| --- | --- |
| PowerShell | `PSEdition`, `PSVersion`, `Platform`, `OS` |
| command metadata | `Name`, `CommandType`, `Source`, `Version`, `ModuleName` |
| module metadata | read-only module metadata specifically associated with the command, if required to establish the NetTCPIP module version |

**Not permitted:** broad environment inventory; enumerating unrelated modules; installed-software lists;
user/account information.

## 12. Exact future listener query semantics (design requirement; not executed this round)

```powershell
$qerr = @()

try {
    $rows = @(
        Get-NetTCPConnection `
            -LocalAddress '127.0.0.1' `
            -LocalPort 4096 `
            -State Listen `
            -ErrorAction SilentlyContinue `
            -ErrorVariable qerr
    )
}
catch {
    <capture terminating ErrorRecord>
}
```

The future implementation must ensure: `$qerr` is initialized immediately before the query; the query occurs
exactly once; the `catch` captures the actual `$_` `ErrorRecord`; all `qerr` entries are preserved for
evidence; rows are not silently discarded; **no second query is used to clarify the first**.

## 13. Future diagnostic observation vocabulary (non-ETB semantics)

| Class | Mechanical definition |
| --- | --- |
| `COMMAND_UNAVAILABLE` | the command metadata/availability gate cannot resolve `Get-NetTCPConnection` |
| `TERMINATING_EXCEPTION` | the exact single listener query reaches `catch` and produces a terminating `ErrorRecord` |
| `ERROR_RECORDS_ZERO_ROWS` | the query returns zero rows and `qerr` contains one or more `ErrorRecord`s |
| `ERROR_RECORDS_WITH_ROWS` | the query returns one or more rows and `qerr` contains one or more `ErrorRecord`s |
| `ZERO_ROWS` | zero rows and no `qerr` records |
| `ONE_ROW` | exactly one row and no `qerr` records |
| `MULTIPLE_ROWS` | more than one row and no `qerr` records |
| `DIAGNOSTIC_HARNESS_INVALID` | the diagnostic harness itself cannot truthfully produce/publish the required closed evidence for reasons outside the listener-query observation |

These are **diagnostic observation classes only** and MUST NOT map directly to `ETB_SATISFIED`,
`ETB_UNSATISFIED`, P6 PASS/FAIL or G0.5 PASS/FAIL. `TERMINATING_EXCEPTION` and `ERROR_RECORDS_*` are **never
collapsed** — that distinction is one of D1's primary purposes (it resolves whether the authoritative
`QUERY_EXCEPTION` came from the terminating catch path or the error-record path).

## 14. Row evidence contract

If the future one-shot query produces rows, D1 records **only** the listener fields already relevant to the
frozen query: `LocalAddress`, `LocalPort`, `State`, `OwningProcess`, and the total row count. **No process
lookup, no PID-to-executable resolution, no `Win32_Process`, no process `CreationDate`, no executable path,
no executable hash, no package version, no target binding.** A row is an observation only.

## 15. Error-record evidence contract (ACCEPTANCE CRITICAL)

For **each** terminating or `qerr` `ErrorRecord`, the future evidence freezes exactly these fields:

| # | Field |
| --- | --- |
| 1 | `source` (`TERMINATING_EXCEPTION` or `ERROR_VARIABLE`) |
| 2 | `fully_qualified_error_id` |
| 3 | `category` |
| 4 | `category_activity` |
| 5 | `category_reason` |
| 6 | `category_target_name` |
| 7 | `category_target_type` |
| 8 | `exception_type` |
| 9 | `exception_message` |
| 10 | `exception_hresult` |
| 11 | `inner_exception_type` |
| 12 | `inner_exception_message` |
| 13 | `error_details_message` |
| 14 | `invocation_position_message` |
| 15 | `script_stack_trace` |

If a field is unavailable, it is serialized with an **empty string** under one exact frozen rule (field is
always present; unavailable → `""`). No conditional omission, no serialization of arbitrary PowerShell
objects — a closed bounded schema only.

## 16. Command-availability evidence

Unlike Recovery-R2 evidence, D1 evidence explicitly persists the command-availability observation:
`availability = AVAILABLE / UNAVAILABLE` plus the permitted command metadata of §11. The evidence must not
rely on later inference from the diagnostic outcome.

## 17. Query-shape evidence

The future evidence explicitly encodes the frozen query shape:

| Field | Value |
| --- | --- |
| `local_address` | `127.0.0.1` |
| `local_port` | `4096` |
| `state` | `Listen` |
| `error_action` | `SilentlyContinue` |
| `error_variable` | `qerr` |
| `query_invocation_count` | `1` |

This closes the current evidence gap where query parameters were not persisted.

## 18. Future D1 evidence schema (new, closed)

`schema_version = devrelay-etb-query-diagnostic-d1-v1`. Exact top-level order:

1. `schema_version`
2. `source_authoritative_bookkeeping_commit`
3. `source_r2_evidence_sha256`
4. `source_r2_result_sha256`
5. `execution_started_at`
6. `execution_finished_at`
7. `diagnostic_mode`
8. `endpoint`
9. `configured_base_url`
10. `powershell_environment`
11. `command_metadata`
12. `query`
13. `query_outcome`
14. `row_count`
15. `rows`
16. `terminating_error`
17. `error_records`
18. `non_claims`
19. `activity_counters`

No missing fields, no extra fields.

**Exact closed subfield order:**

- `powershell_environment`: `PSEdition`, `PSVersion`, `Platform`, `OS`
- `command_metadata`: `Name`, `CommandType`, `Source`, `Version`, `ModuleName`, `availability`
- `query`: `local_address`, `local_port`, `state`, `error_action`, `error_variable`, `query_invocation_count`
- row entry: `LocalAddress`, `LocalPort`, `State`, `OwningProcess`
- `terminating_error`: exactly `null` **or** the exact 15 fields of §15 in the §15 order with
  `source = "TERMINATING_EXCEPTION"` (a closed single object, never an array, never omitted,
  never `{}`, never `[]`) — see §31
- error-record entry: the exact 15 fields of §15
- `activity_counters`: see §21
- `non_claims`: the exact ordered list of §20

**Complete closed sub-schema inventory:** see §40 (**`D1_SUBSCHEMAS = ALL_CLOSED`**).
Per-field representation / absence rules for the whole D1 schema: see §33.

## 19. Config binding

The future diagnostic stage binds to the currently accepted config state: `.devrelay/config.yaml`
SHA-256 = `b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf`, size = 1897, configured
`base_url = http://127.0.0.1:4096`. Future config parsing uses the **same accepted frozen reader shape**
already used by Recovery-R2 (`PYTHONPATH=<repo>/src python -c "<frozen reader>" "<repo>"`). No second YAML
parser. No config modification.

## 20. Non-claims (frozen)

Future D1 evidence/result must state that the diagnostic observation does **not** by itself establish:
`ETB_SATISFIED`; a replacement `ETB_UNSATISFIED`; P6 PASS; P6 FAIL; G0.5 PASS; G0.5 FAIL; Mode-B
authorization; OpenCode general compatibility/incompatibility; permanent endpoint state; permanent listener
state; process binding; target executable identity; or the correctness/incorrectness of Oracle-R2 generally.

## 21. Future activity counters (closed)

| Counter | Frozen semantics |
| --- | --- |
| `listener_query_invocations` | exact listener-query invocations; accepted execution requires **<= 1** |
| `process_queries` | prohibited; must be `0` |
| `target_executable_hashes` | prohibited; must be `0` |
| `opencode_starts` | prohibited; must be `0` |
| `http_requests` | prohibited; must be `0` |
| `provider_model_calls` | prohibited; must be `0` |
| `retries` | prohibited; must be `0` |
| `fallbacks` | prohibited; must be `0` |

## 22. Future publication model (design only)

Future publication conceptually: evidence FINAL → manifest FINAL → result FINAL, using TEMP → no-overwrite
publication with byte read-back (the established pattern), manifest binding **only**
`QUERY_DIAGNOSTIC_EVIDENCE.json` (one line: 64-lowercase-hex + two spaces + exact repository-relative
evidence path + LF), result last. The writer is **not implemented in this round**. New D1 paths only; no
reuse of Recovery-R2 output paths.

## 23. Future claim model (design only)

Distinct reserved schemas:

- `devrelay-etb-query-diagnostic-d1-authorization-use-v1`
- `devrelay-etb-query-diagnostic-d1-attempt-use-v1`

Both must bind, at minimum: the future accepted D1 authorization/design provenance; the future accepted D1
executable provenance; `source_authoritative_bookkeeping_commit = 93e44fe61c59ec5070e2823062a607347bb9163a`;
`source_r2_evidence_sha256 = 6f903f05…`; `source_r2_result_sha256 = 84f51bb5…`; `state = CONSUMED`. No
self-referential value is finalized. **No claim is created in this round.** The later
implementation/authorization round must freeze exact serialization and atomic consumption mechanics (the
established TEMP/CreateNew consumption-point model) before any execution.

## 24. Diagnostic-result authority

A future D1 result is **diagnostic evidence only**. Even after independent review it may become
`AUTHORITATIVE DIAGNOSTIC RESULT` but MUST NOT become `AUTHORITATIVE ETB SEMANTIC RESULT` and MUST NOT
replace `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED`. Any later decision to create a new ETB
authorization remains a separate owner decision.

## 25. Future control sequence (no stage skipped)

current reconciliation / owner decision → **D1 design candidate [THIS ROUND]** → independent D1 design
review → if approved: D1 design acceptance bookkeeping → independent bookkeeping confirmation → separate D1
implementation / execution-authorization candidate → independent implementation/authorization review → if
approved: D1 execution-authorization bookkeeping → independent bookkeeping confirmation → exactly one D1
diagnostic authorization consumption → exactly one D1 diagnostic-attempt consumption → exactly one
listener-query invocation → publication of D1 diagnostic evidence/result → independent D1 result review →
result bookkeeping / confirmation as separately authorized → owner reconciliation. **This design round does
not skip directly to live execution.**

## 26. Relation to Path C / Path D

**PATH C — STATIC ORACLE CORRECTION:** currently lacks a static basis because
`STATIC_ORACLE_R2_LISTENER_DEFECT = NOT_PROVEN`. D1 does **not** authorize Oracle-R2 modification.

**PATH D — NEW ETB ATTEMPT:** remains **NOT AUTHORIZED**. D1 does not grant a new ETB attempt; a later owner
may choose Path D only after a separate decision/design.

## 27. Current gate states (preserved)

`AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED`; Mode-B = `BLOCKED / NOT RUN`; `P6 = UNPROVEN /
UNSATISFIED`; G0.5 = `NOT CLOSED`; G0.5 execution = `NOT AUTHORIZED`; Case-C = `NOT AUTHORIZED`; v0.3-E
implementation = `NOT AUTHORIZED`; `G1`/`G2` = `NOT RUN`; `adopt_completed_turn` = `DISABLED`.

## 28. Design self-sufficiency

A future implementation designer needs no chat memory to know: why D1 exists (§3); what source result it
binds (§10); what exact query must eventually be executed (§5, §12); what environment metadata is allowed
(§11); what error details must be captured (§15); the diagnostic vocabulary (§13); the evidence schema (§18);
the non-claims (§20); the one-shot nature (§8, §21); the namespace (§7); the publication paths (§7, §22);
the forbidden operations (§4, §14, §19, §21); and the future review sequence (§25).

## 29. Design-round counters and non-claims of this round

This design round performed: listener-query executions `0`; claim creation `0`; diagnostic outputs `0`;
Oracle executions `0`; target/listener/process live probes `0`; OpenCode starts/restarts `0`; HTTP `0`;
provider/model calls `0`; SIC `0`; Mode-B `0`; G0.5/G1/G2 `0`; config mutation `0`; Recovery-R2 artifact
mutation `0`; R1 mutation `0`; runtime/test/dependency/version changes `0`. This candidate does not claim:
D1 accepted; D1 authorized; D1 executed; a new ETB authorization exists; Recovery-R2 reusable;
`ETB_SATISFIED`; P6 PASS/FAIL; G0.5 PASS/FAIL; Mode-B authorized; Oracle-R2 defective; root cause
determined.

**End of ETB query diagnostic D1 design candidate.**

---

# Part II — corrective design R1 (schema-gap closure)

## 30. Corrective round R1 — review findings addressed

The initial D1 design candidate `78266c954087b33baf5a12dfab1cbdef845a0bbb` (parent
`93e44fe61c59ec5070e2823062a607347bb9163a`; spec SHA-256
`73af7be76de48cffb6c90a499064194e259f2613cd3906c3fa539c1c44b68b55`) received
**REQUEST_CHANGES — V0.3-E ETB QUERY_EXCEPTION DIAGNOSTIC D1 DESIGN** with
**P0 = 0, P1 = 0, P2 = 1, P3 = 2**.

That initial candidate is **REJECTED / SUPERSEDED / NEVER ACCEPTED / NOT AUTHORIZED /
NOT EXECUTED**. It is preserved permanently as historical provenance (§1) and is never
relabelled as accepted.

| # | Severity | Finding | Status after R1 |
| --- | --- | --- | --- |
| 1 | **P2 (blocking)** | `terminating_error` has no explicit closed schema | **CLOSED** (§31) |
| 2 | **P2 (blocking)** | null / absent / empty representations are not frozen | **CLOSED** (§33, §34, §35, §37) |
| A | P3 (non-blocking) | source-provenance mechanical preservation inferable but not explicitly documented | **CLOSED** (§38) |
| B | P3 (non-blocking) | error strings have no maximum representation rule | **REMAINS OPEN / NON-BLOCKING** (§39) |

This corrective round is **design-only**. It closes findings 1, 2 and A. It deliberately
does **not** close B (§39). It executes nothing, creates no claim, grants no
authorization, and changes none of the design elements preserved by §3 of this round's
instruction: the PATH B owner decision, the D1 purpose, the non-ETB semantic boundary,
the diagnostic target, the `Get-NetTCPConnection` query shape, the `127.0.0.1` / `4096` /
`Listen` binding, the one-query maximum, the no-retry rule, the D1 claim and output
namespaces, the D1 budgets, the provenance model, the allowed environment-metadata
categories, the diagnostic observation vocabulary, the observation partition, the row
evidence field set, the 15-field ErrorRecord field set, the 19-field top-level schema and
its order, the config binding, the non-claims, the activity counters, the publication
sequence, the claim-model design-only boundary, the diagnostic-result authority model,
the future control sequence, the Path C / Path D status, and the current Mode-B / P6 /
G0.5 state.

The corrective delta is **sub-schema and representation ambiguity only**.

## 31. `terminating_error` closed sub-schema (P2 finding 1, blocking)

`terminating_error` is explicitly added to the **CLOSED** sub-schema contract. It is
exactly one of:

- **A.** JSON `null`; or
- **B.** exactly one closed `ErrorRecord` object using **exactly the same 15 ordered
  fields** already defined by the §15 ErrorRecord schema.

When the object form is present:

- `source = "TERMINATING_EXCEPTION"`;
- the remaining 14 fields use the same field names, ordering and scalar serialization
  rules as the existing §15 ErrorRecord schema (§34).

`terminating_error` is a **SINGLE object, never an array**. It MUST contain only the
ErrorRecord captured from the actual `catch { $_ }` path of §12.

If no terminating exception occurred:

- `terminating_error = null`.

Do **not** omit the field. Do **not** serialize `{}`. Do **not** serialize `[]`. Do
**not** place `qerr`-only records in `terminating_error`.

## 32. `error_records` array relation (P2 finding 1, blocking)

`error_records` contains **ONLY** ErrorRecords captured through `-ErrorVariable qerr`, in
their observed order.

Every `error_records[]` entry uses the same exact 15-field closed ErrorRecord schema of
§15. For every entry:

- `source = "ERROR_VARIABLE"`.

A terminating `catch` record MUST NOT be duplicated into `error_records` merely because it
also caused query termination.

If `qerr` contains zero records:

- `error_records = []`.

This creates an explicit **mechanical** distinction between `terminating_error` and
`error_records`: they are populated from disjoint capture paths, and neither is derivable
from the other.

## 33. Complete null / empty representation table (P2 finding 2, blocking) — ACCEPTANCE CRITICAL

This table is normative for the **complete** D1 evidence schema. After it there is no
implementation choice left over between `null`, `""`, `[]` and an omitted key.

### 33.1 Required fields

Every field defined by the closed top-level schema and every field defined by a closed
object schema is **ALWAYS emitted**. There is **no conditional key omission** anywhere in
the D1 evidence schema.

### 33.2 Strings

An unavailable / not-observed value for a field whose schema type is a string is
serialized as:

- `""`

It is **never** `null`.

### 33.3 Arrays

Every array field is always emitted as a JSON array. Zero elements is:

- `[]`

It is **never** `null`.

This applies explicitly to `rows`, `error_records`, `non_claims`, and any other closed
array in the D1 schema.

### 33.4 Optional object

The only absence representation for the single optional object field `terminating_error`
is:

- `null`

When present it is the exact closed 15-field ErrorRecord object of §31.

### 33.5 Integer-valued required counters

These fields are always JSON integers and are **never** `null`:

- `row_count`
- `query.query_invocation_count`
- all activity counters (§21)
- `query.local_port`

Their non-observation semantics are explicit:

| Field | Value | Rule |
| --- | --- | --- |
| `row_count` | `0` | no rows returned, or the query did not reach a completed row result |
| `query.query_invocation_count` | `0` | the listener query was **not** invoked, including `COMMAND_UNAVAILABLE` |
| `query.query_invocation_count` | `1` | the single allowed listener query **has** been invoked |

**No negative sentinel values** are permitted anywhere in the D1 schema.

### 33.6 Row integer fields

For row-entry integer properties whose value cannot truthfully be obtained — `LocalPort`,
`OwningProcess` — serialize:

- `null`

Otherwise serialize the observed JSON integer. **The row key itself remains present.**

Row string properties `LocalAddress` and `State` use:

- `""`

when unavailable.

### 33.7 Command metadata

The `command_metadata` object is **ALWAYS present**, and its exact field order remains
frozen (§18).

When:

- `availability = "UNAVAILABLE"`

**all** string metadata fields are emitted and set to `""`, including the existing `Name`,
`CommandType`, `Source`, `Version` and `ModuleName` fields. **No command metadata key may
be omitted.**

When `AVAILABLE`, serialize the observed allowed metadata values (§11).

### 33.8 PowerShell environment

The `powershell_environment` object is **ALWAYS present**. Every frozen string field
remains present. If an allowed property is unavailable, serialize `""`. Environment
collection is **not** broadened (§11).

### 33.9 Fixed query object

The `query` object is **ALWAYS present**. Its frozen query-shape values remain:

| Field | Frozen value |
| --- | --- |
| `local_address` | `"127.0.0.1"` |
| `local_port` | `4096` |
| `state` | `"Listen"` |
| `error_action` | `"SilentlyContinue"` |
| `error_variable` | `"qerr"` |

Only `query_invocation_count` varies between `0` and `1`, under the frozen rules of §33.5.

### 33.10 Endpoint / config fields

`endpoint` remains the frozen diagnostic endpoint representation. `configured_base_url`
must come from the accepted frozen config-reader contract of §19.

No placeholder is invented for config-reader failure. A future inability to establish
mandatory config identity belongs to the **future diagnostic harness / precondition
failure path**; it is **not** represented by silently replacing the required configured
value with `null` or empty text.

## 34. Error-record scalar serialization (closed)

The exact 15-field ErrorRecord order of §15 is preserved verbatim:

| # | Field | Frozen JSON type |
| --- | --- | --- |
| 1 | `source` | string |
| 2 | `fully_qualified_error_id` | string |
| 3 | `category` | string |
| 4 | `category_activity` | string |
| 5 | `category_reason` | string |
| 6 | `category_target_name` | string |
| 7 | `category_target_type` | string |
| 8 | `exception_type` | string |
| 9 | `exception_message` | string |
| 10 | `exception_hresult` | string |
| 11 | `inner_exception_type` | string |
| 12 | `inner_exception_message` | string |
| 13 | `error_details_message` | string |
| 14 | `invocation_position_message` | string |
| 15 | `script_stack_trace` | string |

Every one of these fields is frozen as a **JSON STRING**. An unavailable value is `""`.

For `exception_hresult`, when available, serialize its invariant signed decimal
**textual** representation as a JSON string. Example shape only: `"-2146233087"`. It is
**not** emitted as a JSON number.

This keeps exactly one scalar / absence rule for the full ErrorRecord schema.

## 35. Representation by observation class (frozen, exhaustive)

These per-class representations are frozen and cover the §13 vocabulary completely.

### 35.1 `TERMINATING_EXCEPTION`

- `query_invocation_count = 1`
- `terminating_error` = the actual `catch` ErrorRecord object (§31)
- `rows = []`
- `row_count = 0`

Any `qerr` entries actually captured before termination remain independently represented
in `error_records` using `source = "ERROR_VARIABLE"`. **No second query is executed to
clarify row state** (§6).

### 35.2 `COMMAND_UNAVAILABLE`

- `command_metadata.availability = "UNAVAILABLE"`
- all command metadata strings = `""` (§33.7)
- `query_invocation_count = 0`
- `rows = []`
- `row_count = 0`
- `terminating_error = null`
- `error_records = []`

**No listener query occurs.**

### 35.3 `ZERO_ROWS`

- `query_invocation_count = 1`
- `rows = []`
- `row_count = 0`
- `terminating_error = null`
- `error_records = []`

### 35.4 `ONE_ROW`

- `query_invocation_count = 1`
- `rows` = exactly one closed row object
- `row_count = 1`
- `terminating_error = null`
- `error_records = []`

### 35.5 `MULTIPLE_ROWS`

- `query_invocation_count = 1`
- `rows` = all returned closed row objects in observed query order
- `row_count = rows.length`
- `terminating_error = null`
- `error_records = []`

### 35.6 `ERROR_RECORDS_ZERO_ROWS`

- `query_invocation_count = 1`
- `rows = []`
- `row_count = 0`
- `terminating_error = null`
- `error_records` = one or more `qerr` ErrorRecord objects

### 35.7 `ERROR_RECORDS_WITH_ROWS`

- `query_invocation_count = 1`
- `rows` = one or more returned row objects
- `row_count = rows.length`
- `terminating_error = null`
- `error_records` = one or more `qerr` ErrorRecord objects

This class covers **both** one row + `qerr` and multiple rows + `qerr` **without**
introducing a new observation class.

## 36. `DIAGNOSTIC_HARNESS_INVALID` serialization point

The existing D1 semantic rule is **unchanged**: `DIAGNOSTIC_HARNESS_INVALID` is a
**diagnostic control outcome**, not an ETB semantic result (§4, §13).

This corrective design clarifies **only** the serialization point: if the harness can
still truthfully construct the frozen closed evidence schema, it **MUST** use the same
null / empty rules of §33.

If the harness **cannot** truthfully construct the mandatory closed evidence record at
all, publication / control behavior is handled by the **later
implementation/authorization design**. That later mechanism is **not invented** in this
round.

## 37. Null / empty completeness test (design-level walk)

The design walks every required case and fixes its exact JSON representation class:

| # | Case | `query_invocation_count` | `rows` | `row_count` | `terminating_error` | `error_records` |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | command unavailable | `0` | `[]` | `0` | `null` | `[]` |
| 2 | terminating exception | `1` | `[]` | `0` | ErrorRecord object | qerr entries, or `[]` |
| 3 | zero rows / no qerr | `1` | `[]` | `0` | `null` | `[]` |
| 4 | one row / no qerr | `1` | 1 object | `1` | `null` | `[]` |
| 5 | multiple rows / no qerr | `1` | n objects | `n` | `null` | `[]` |
| 6 | zero rows / qerr | `1` | `[]` | `0` | `null` | one or more objects |
| 7 | one row / qerr | `1` | 1 object | `1` | `null` | one or more objects |
| 8 | multiple rows / qerr | `1` | n objects | `n` | `null` | one or more objects |
| 9 | no terminating exception | `1` (or `0` under COMMAND_UNAVAILABLE) | — | — | `null` | — |
| 10 | unavailable command metadata | `0` | `[]` | `0` | `null` | `[]`; all metadata strings `""` |
| 11 | unavailable row scalar | `1` | 1 object with `LocalPort` / `OwningProcess` = `null` and `LocalAddress` / `State` = `""` | `1` | `null` | `[]` |
| 12 | empty `rows` array | any | `[]` | `0` | as per class | as per class |
| 13 | empty `error_records` array | as per class | as per class | `rows.length` | as per class | `[]` |

**`D1_NULL_EMPTY_RULES = COMPLETE.`**

## 38. Source-provenance clarification (P3 finding A, closed)

This closes the first non-blocking P3 observation **without** changing the 19-field
top-level schema (§18).

- **A.** `source_authoritative_bookkeeping_commit = 93e44fe61c59ec5070e2823062a607347bb9163a`
  anchors the tracked historical source state.
- **B.** The accepted Recovery-R2 authorization and the accepted Oracle-R2 tracked
  artifacts are **mechanically recoverable** from that immutable Git ancestry/tree
  together with their already frozen accepted hashes (§10). No chat memory, transcript or
  executor recollection is required to re-derive any of them.
- **C.** The Recovery-R2 manifest relationship remains **externally frozen** by the
  accepted R2 manifest format and the D1-bound R2 evidence hash
  (`source_r2_evidence_sha256`). D1 does not restate or re-derive that manifest.
- **D.** The two untracked Recovery-R2 claim hashes MUST be rebound as **mandatory future
  execution/authorization preconditions**:

| Precondition | SHA-256 |
| --- | --- |
| Recovery-R2 authorization claim | `fd7336e4694f8d491ddd3067880851f96974a29a1117d48f7dd47eb2d629ccf7` |
| Recovery-R2 attempt claim | `69eb6ef0352375311f72c211d04c8ed39e59d8f7b00b6d7738577044916167f9` |

These two hashes are **not** added as new top-level evidence fields, and the 19-field
schema is **not** altered. This is explicit **external / precondition** provenance
binding only, because those two claim artifacts are untracked operational control state
and are not part of the Git tree.

## 39. Error-string boundedness (P3 finding B — remains open, non-blocking)

This corrective round does **not** introduce arbitrary truncation.

The existing closed scalar field set and the prohibition against arbitrary
PowerShell-object serialization (§15, §34) are preserved unchanged.

Recorded honestly:

**ERROR STRING MAXIMUM REPRESENTATION RULE = NOT YET FROZEN / NON-BLOCKING DESIGN
OBSERVATION**

No accepted deterministic boundedness rule exists in the current design for
`exception_message`, `inner_exception_message`, `error_details_message`,
`invocation_position_message` or `script_stack_trace`. A lossy truncation policy is
**not** invented merely to force this P3 to zero, because truncation would silently
destroy diagnostic evidence D1 exists to capture. This P3 may remain if the independent
reviewer continues to classify it as non-blocking.

## 40. Closed sub-schema inventory — ALL_CLOSED

The closed sub-schema inventory of §18 is hereby completed. Every object in the D1
evidence schema is **closed**; no open object schema remains:

| Sub-schema | Status | Definition |
| --- | --- | --- |
| `powershell_environment` | CLOSED | §18 (exact order), §33.8 (absence rule) |
| `command_metadata` | CLOSED | §18 (exact order), §33.7 (absence rule) |
| `query` | CLOSED | §18 (exact order), §33.9 (frozen values) |
| row entry | CLOSED | §14, §18, §33.6 |
| `terminating_error` | CLOSED | **§31** — exactly `null` or the exact 15-field ErrorRecord object; cross-references the §15 / §34 ErrorRecord schema and the null-when-absent rule |
| error-record entry | CLOSED | §15, §34 |
| `activity_counters` | CLOSED | §21 |
| `non_claims` | CLOSED | §20 |

**`D1_SUBSCHEMAS = ALL_CLOSED.`**

## 41. Corrective-round status

Active status after this corrective round:

**ETB QUERY_EXCEPTION DIAGNOSTIC D1 — CORRECTIVE DESIGN R1 = DESIGN CANDIDATE / NOT
ACCEPTED / NOT AUTHORIZED / NOT EXECUTED.**

This corrective candidate is **not** APPROVED, **not** ACCEPTED, **not** FROZEN, **not**
AUTHORIZED, **not** EXECUTABLE and **not** READY FOR LIVE DIAGNOSTIC EXECUTION. It
requires a fresh independent D1 design re-review before any further step of the §25
sequence.

This corrective round performed: listener-query executions `0`; claim creation `0`;
diagnostic outputs `0`; Oracle executions `0`; target/listener/process live probes `0`;
OpenCode starts/restarts `0`; HTTP `0`; provider/model calls `0`; SIC `0`; Mode-B `0`;
G0.5/G1/G2 `0`; config mutation `0`; Recovery-R2 artifact mutation `0`; R1 mutation `0`;
runtime/test/dependency/version changes `0`. **No D1 operational path of §7 was created.
No `.ps1` file was created.** The corrective tracked delta is exactly three files:
`docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_EXCEPTION_DIAGNOSTIC_D1_SPEC.md`, `CHANGELOG.md` and
`docs/v0.3/V03E_ACCEPTANCE.md`.

All current gate states are preserved unchanged (§27): `AUTHORITATIVE ETB SEMANTIC RESULT
= ETB_UNSATISFIED`; Recovery-R2 authorization use = `SPENT / NOT REUSABLE`; Recovery-R2
attempt = `SPENT / NOT REUSABLE`; Mode-B = `BLOCKED / NOT RUN`; `P6 = UNPROVEN /
UNSATISFIED`; G0.5 = `NOT CLOSED`; G0.5 execution = `NOT AUTHORIZED`; Case-C = `NOT
AUTHORIZED`; v0.3-E implementation = `NOT AUTHORIZED`; `G1`/`G2` = `NOT RUN`;
`adopt_completed_turn` = `DISABLED`.

**End of ETB query diagnostic D1 corrective design R1.**

---

# Part III — implementation design gap clarification C1

## 42. Clarification round C1 — scope and attribution

An implementation / execution-authorization round was attempted against the accepted design
`6ad917b950c12e7a93579c519cc63f89925c2ab0` (spec SHA-256
`e9c521ff9d9333999d1ccc2156f3f78400a5b0e5b19b42a7cf2280c8f0def466`) and **stopped before any
mutation** with the finding **`D1 IMPLEMENTATION DESIGN GAP`**: two required members of the
accepted 19-field top-level evidence schema had no frozen JSON type or value. That attempt
created **0 files, 0 commits, 0 claims, 0 queries and consumed 0 budgets**, and it reported:

| Gap | Description |
| --- | --- |
| **P1-1** | `diagnostic_mode` exists in the accepted 19-field top-level schema but has no frozen JSON type or value |
| **P1-2** | `endpoint` exists in the accepted 19-field top-level schema but has no frozen JSON type, shape or value |
| **P3** | `non_claims` is specified semantically but its exact serialized string-array elements are not frozen |

This clarification round is **design-only**. It closes P1-1 (§43), P1-2 (§44) and P3 (§47)
and adds the normative closure audit required to prevent a recurrence (§49, §50). It does
**not** create an executable, an execution-authorization document, a claim, evidence, a
manifest, a result or an output directory; it executes nothing.

The **only** clarifications in C1 are: `diagnostic_mode` (§43), `endpoint` (§44), the exact
serialized `non_claims` array (§47) and the comprehensive top-level field closure table
(§49). Every other accepted design element is preserved verbatim, explicitly including the
query semantics, query target, query invocation budget, ErrorRecord schema,
`terminating_error`, `error_records`, the null/empty rules, the observation vocabulary, the
row schema, the PowerShell environment schema, the command metadata schema, the activity
counters, the claim namespace, the future budgets, the publication namespace, the source
provenance, the config contract and the Path C / Path D state.

## 43. `diagnostic_mode` — frozen (P1-1, CLOSED)

| Property | Frozen value |
| --- | --- |
| JSON type | **string** |
| Cardinality | required scalar (always emitted; §33.1) |
| Value | **constant** `"QUERY_EXCEPTION_DIAGNOSTIC_D1"` |

This value is a **constant**. It **does not vary by runtime observation**. It does **not**
encode the query outcome, an ETB result, the P6 state or the G0.5 state. It identifies
**only** the diagnostic procedure that produced the evidence.

Unavailable / `null` / empty representations are **NOT permitted**. The field must always be
exactly:

`"diagnostic_mode":"QUERY_EXCEPTION_DIAGNOSTIC_D1"`

subject only to normal JSON property framing and the frozen top-level order.

## 44. `endpoint` — frozen (P1-2, CLOSED)

| Property | Frozen value |
| --- | --- |
| JSON type | **string** (a scalar — **not** an object) |
| Cardinality | required scalar (always emitted; §33.1) |
| Value | **constant** `"http://127.0.0.1:4096"` |

This is the **fixed diagnostic target** selected for D1. It is **NOT an object**. It does
**not** inherit the Oracle-R2 endpoint object schema, and it does **not** contain `scheme`,
`address_family`, `host`, `port`, `base_uri` or `fallback` as nested fields.

The exact D1 representation is a scalar JSON string:

`"endpoint":"http://127.0.0.1:4096"`

No `null`. No empty string. No alternate host. No IPv6. No `localhost` alias. No alternate
port.

## 45. `endpoint` versus `configured_base_url`

The distinction between the two top-level fields is explicitly frozen:

| Field | Meaning |
| --- | --- |
| `endpoint` | the **constant** D1 diagnostic target `"http://127.0.0.1:4096"` (§44) |
| `configured_base_url` | the value **read from** `.devrelay/config.yaml` using the already accepted frozen Recovery-R2 config-reader contract (§19) |

Future execution requires:

`configured_base_url == endpoint == "http://127.0.0.1:4096"`

**before any claim consumption.**

The two fields are intentionally redundant for provenance: `endpoint` records the
**diagnostic target contract**, while `configured_base_url` records the configuration value
**actually established** by the frozen config reader. Do **not** merge the fields. Do **not**
infer one in place of collecting and checking the other.

## 46. No Oracle-R2 endpoint-schema inheritance

D1 `endpoint` is explicitly **NOT** the `devrelay-etb-v1-r2` endpoint object. **No R2 nested
endpoint fields are inherited.** Oracle-R2 may be cited **only** as historical context. The
D1 scalar `endpoint` definition in this clarification is authoritative for D1 **after this
clarification itself is independently accepted**.

## 47. Exact `non_claims` array — frozen (P3, CLOSED)

`non_claims` is a **JSON array of strings** with **EXACTLY 13 elements in this exact order**:

| # | Exact element |
| --- | --- |
| 1 | `"does not establish ETB_SATISFIED"` |
| 2 | `"does not establish a replacement ETB_UNSATISFIED"` |
| 3 | `"does not establish P6 PASS"` |
| 4 | `"does not establish P6 FAIL"` |
| 5 | `"does not establish G0.5 PASS"` |
| 6 | `"does not establish G0.5 FAIL"` |
| 7 | `"does not authorize Mode-B"` |
| 8 | `"does not establish OpenCode general compatibility or incompatibility"` |
| 9 | `"does not establish permanent endpoint state"` |
| 10 | `"does not establish permanent listener state"` |
| 11 | `"does not establish process binding"` |
| 12 | `"does not establish target executable identity"` |
| 13 | `"does not establish Oracle-R2 general correctness or incorrectness"` |

**No additional element. No omitted element. No alternative punctuation. No reordering. No
splitting one sentence into multiple elements. No joining multiple elements.** The array is
always emitted exactly with these 13 strings.

## 48. §20 → serialized array one-to-one mapping

The frozen 13-string array is a **serialization formalization** of the already accepted §20
semantic non-claims. It adds **no** new substantive non-claim and deletes **no** existing
semantic non-claim:

| §20 semantic item | Serialized array element |
| --- | --- |
| `ETB_SATISFIED` | 1 |
| a replacement `ETB_UNSATISFIED` | 2 |
| P6 PASS | 3 |
| P6 FAIL | 4 |
| G0.5 PASS | 5 |
| G0.5 FAIL | 6 |
| Mode-B authorization | 7 |
| OpenCode general compatibility/incompatibility | 8 |
| permanent endpoint state | 9 |
| permanent listener state | 10 |
| process binding | 11 |
| target executable identity | 12 |
| the correctness/incorrectness of Oracle-R2 generally | 13 |

The mapping is **13 → 13**, bijective, with no remainder on either side.

## 49. Complete top-level 19-field closure table — ACCEPTANCE CRITICAL

This table is normative for **every** top-level evidence field of
`devrelay-etb-query-diagnostic-d1-v1`:

| # | Field | JSON type | Cardinality | Value / source contract | Runtime-variable | Detailed rule |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `schema_version` | string | required scalar | constant `"devrelay-etb-query-diagnostic-d1-v1"` | no | §18 |
| 2 | `source_authoritative_bookkeeping_commit` | string | required scalar | constant `"93e44fe61c59ec5070e2823062a607347bb9163a"` | no | §10, §18 |
| 3 | `source_r2_evidence_sha256` | string | required scalar | constant `"6f903f05e859a05a99dc0cde253e878ae7235c1554e212ab2f6b27945b2da0c8"` | no | §10, §18 |
| 4 | `source_r2_result_sha256` | string | required scalar | constant `"84f51bb5d7765112cb65376ea164e10780bb777f1beb6e962d6baa4508fe9efa"` | no | §10, §18 |
| 5 | `execution_started_at` | string | required scalar | runtime UTC timestamp | **yes** | §51 |
| 6 | `execution_finished_at` | string | required scalar | runtime UTC timestamp | **yes** | §51 |
| 7 | `diagnostic_mode` | string | required scalar | constant `"QUERY_EXCEPTION_DIAGNOSTIC_D1"` | no | **§43** |
| 8 | `endpoint` | string | required scalar | constant `"http://127.0.0.1:4096"` | no | **§44**, §45 |
| 9 | `configured_base_url` | string | required scalar | runtime-established through the accepted frozen config reader; must equal `"http://127.0.0.1:4096"` | **yes** | §19, §33.10, §45 |
| 10 | `powershell_environment` | object | required object | closed sub-schema already frozen | yes | §11, §18, §33.8 |
| 11 | `command_metadata` | object | required object | closed sub-schema already frozen | yes | §11, §16, §18, §33.7 |
| 12 | `query` | object | required object | closed sub-schema already frozen | partly (`query_invocation_count` only) | §17, §18, §33.9 |
| 13 | `query_outcome` | string | required scalar | exactly one value from the accepted eight-value vocabulary | yes | §13, §25-§26 |
| 14 | `row_count` | integer | required scalar | existing accepted integer rules apply | yes | §18, §33.5 |
| 15 | `rows` | array | required array | zero or more closed row objects; existing accepted order/empty rules apply | yes | §14, §18, §33.3, §33.6 |
| 16 | `terminating_error` | object **OR** `null` | required key | exact previously accepted optional-object semantics | yes | §31, §33.4 |
| 17 | `error_records` | array | required array | zero or more closed ErrorRecord objects; qerr-only semantics preserved | yes | §32, §33.3 |
| 18 | `non_claims` | array | required array | exactly 13 JSON strings, exact values/order frozen by this clarification | no (constant array) | **§47**, §48 |
| 19 | `activity_counters` | object | required object | existing accepted closed counter schema | yes | §21, §29 |

## 50. Top-level closure audit rule

A top-level field is considered **CLOSED** only if the design specifies either:

- **A.** a complete scalar type and value/source rule; or
- **B.** a closed object/array sub-schema by explicit cross-reference; or
- **C.** an explicitly authorized later implementation-stage formatting choice whose semantic
  type, source and cardinality are **already frozen**.

Every one of the 19 top-level fields satisfies exactly one of those routes (§49). The design
therefore states:

**`D1_TOPLEVEL_FIELD_CLOSURE = 19 / 19 CLOSED.`**

Future D1 design reviews MUST include this **19/19 top-level field closure audit** as a
mandatory check (§54).

## 51. Timestamp delegation (authorized, not a gap)

For `execution_started_at` and `execution_finished_at`, this clarification freezes **now**
only:

| Property | Frozen value |
| --- | --- |
| JSON type | **string** |
| Cardinality | required scalar (always emitted) |
| Source | UTC runtime timestamp |

The prior authorized implementation-stage freedom to freeze **one** exact invariant textual
timestamp format **later** is preserved:

**TIMESTAMP STRING FORMAT = INTENTIONALLY DEFERRED TO IMPLEMENTATION / EXECUTION-AUTHORIZATION
DESIGN**

This is an **AUTHORIZED IMPLEMENTATION-LEVEL FORMAT CHOICE / NOT A MATERIAL D1 SEMANTIC
GAP**. Type, source and cardinality are **not** left unspecified.

## 52. Previous accepted design status during candidacy

Until this clarification is independently approved and accepted, the previously accepted D1
design remains:

`6ad917b950c12e7a93579c519cc63f89925c2ab0` / `e9c521ff9d9333999d1ccc2156f3f78400a5b0e5b19b42a7cf2280c8f0def466`

**ACCEPTED / FROZEN / HISTORICAL AUTHORITATIVE PREDECESSOR / IMPLEMENTATION BLOCKED BY
SUBSEQUENTLY DISCOVERED DESIGN GAP.**

Its acceptance bookkeeping at `8738651ab805b9ccf07a4687627ef0a1d7bb7916` also remains
**historically valid**. The previously accepted revision is **NOT** relabelled REJECTED or
NEVER ACCEPTED; the newly discovered gap means only that the accepted revision is
insufficiently complete to authorize construction of the implementation candidate.

The new clarification is only:

**D1 IMPLEMENTATION DESIGN GAP CLARIFICATION C1 = DESIGN CANDIDATE / NOT ACCEPTED / NOT
FROZEN / NOT AUTHORIZED / NOT EXECUTED.**

`diagnostic_d1_design_commit` is **NOT** prematurely replaced in active accepted provenance.

## 53. Future successor provenance

If and **only if** this clarification later receives independent approval and acceptance
bookkeeping:

- the clarification candidate commit becomes the **new** `diagnostic_d1_design_commit`;
- the SHA-256 of the clarified D1 spec at that commit becomes the **new**
  `diagnostic_d1_spec_sha256`;

for all future D1 implementation / execution-authorization work. At that future point,
`6ad917b950c12e7a93579c519cc63f89925c2ab0` must remain recorded as **PREVIOUSLY ACCEPTED /
HISTORICAL PREDECESSOR / SUPERSEDED BY ACCEPTED CLARIFICATION** — **not** as REJECTED.

**This provenance transition is NOT performed in the current candidate round.**

## 54. Prior review-coverage omission (REVIEW-COVERAGE CORRECTION)

Recorded as a **review-coverage correction**, and explicitly **not** as evidence of malicious
or invalid prior review:

The prior Corrective Design R1 review verified the **eight listed closed sub-schemas** but did
**not** cross-check every top-level member of the 19-field schema for an explicit scalar
type/value/source rule or a sub-schema binding. That omission allowed `diagnostic_mode` and
`endpoint` to remain materially underdefined, which the attempted implementation round then
surfaced as **`D1 IMPLEMENTATION DESIGN GAP`**.

**Future D1 design reviews MUST include a 19/19 TOP-LEVEL FIELD CLOSURE AUDIT** (§50).

## 55. C1 status and preserved state

Active status after this clarification candidate:

**D1 IMPLEMENTATION DESIGN GAP CLARIFICATION C1 = DESIGN CANDIDATE / NOT ACCEPTED / NOT
FROZEN / NOT AUTHORIZED / NOT EXECUTED.**

The stopped implementation attempt is recorded accurately: **D1 IMPLEMENTATION /
EXECUTION-AUTHORIZATION ATTEMPT = STOPPED BEFORE MUTATION / NO CANDIDATE CREATED / ZERO SIDE
EFFECTS**; files created `0`; commits created `0`; claims `0`; queries `0`; budgets consumed
`0`.

Preserved unchanged by C1: the query contract (`Get-NetTCPConnection -LocalAddress '127.0.0.1'
-LocalPort 4096 -State Listen -ErrorAction SilentlyContinue -ErrorVariable qerr`), the
one-query maximum, the no-retry rule, the eight-value observation vocabulary, the 15-field
ErrorRecord schema, `terminating_error` semantics, `error_records` semantics, the row schema,
the null/empty rules and the activity counters (§19 of this round's instruction).

Preserved source binding: `source_authoritative_bookkeeping_commit = 93e44fe6…`; R2 evidence
`6f903f05…`; R2 manifest `b4701c90…`; R2 result `84f51bb5…`; R2 authorization claim
`fd7336e4…`; R2 attempt claim `69eb6ef0…`.

All D1 operational artifacts remain **absent**; budgets remain **D1 AUTHORIZATION USE =
`UNAVAILABLE / NOT YET GRANTED`**, **D1 DIAGNOSTIC ATTEMPT = `UNAVAILABLE / NOT YET
GRANTED`**, **D1 LISTENER QUERY EXECUTION = `NOT AUTHORIZED`**. No implementation candidate
exists and no execution authorization exists.

Preserved downstream state: `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED`;
Recovery-R2 authorization use = `SPENT / NOT REUSABLE`; Recovery-R2 attempt = `SPENT / NOT
REUSABLE`; Mode-B = `BLOCKED / NOT RUN`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 = `NOT CLOSED`;
G0.5 execution = `NOT AUTHORIZED`; Case-C = `NOT AUTHORIZED`; v0.3-E implementation = `NOT
AUTHORIZED`; `G1`/`G2` = `NOT RUN`; `adopt_completed_turn` = `DISABLED`; PATH C = `NO STATIC
BASIS / NOT AUTHORIZED`; PATH D = `NOT AUTHORIZED`.

Standing P3 preserved unchanged: **ERROR STRING MAXIMUM REPRESENTATION RULE = NOT YET FROZEN /
NON-BLOCKING DESIGN OBSERVATION** (no truncation invented; status not modified by C1).

**End of ETB query diagnostic D1 implementation design gap clarification C1.**
