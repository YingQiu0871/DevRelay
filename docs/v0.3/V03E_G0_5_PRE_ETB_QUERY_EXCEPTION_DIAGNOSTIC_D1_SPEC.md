# DevRelay v0.3-E — G0.5-PRE / SIC — ETB QUERY_EXCEPTION DIAGNOSTIC D1 (design candidate)

> **ETB QUERY_EXCEPTION DIAGNOSTIC D1**
> **DESIGN CANDIDATE**
> **NOT ACCEPTED**
> **NOT AUTHORIZED**
> **NOT EXECUTED**
> **EXECUTES NOTHING**
> **CREATES NO CLAIM NOW**
> **CREATES NO EVIDENCE NOW**
> **DOES NOT TOUCH THE AUTHORITATIVE RECOVERY-R2 RESULT**
> **DIAGNOSTIC OBSERVATIONS CAN NEVER BECOME ETB SEMANTIC RESULTS**

Status: **ETB QUERY_EXCEPTION DIAGNOSTIC D1 = DESIGN CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED / NOT EXECUTED**

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
- error-record entry: the exact 15 fields of §15
- `activity_counters`: see §21
- `non_claims`: the exact ordered list of §20

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
