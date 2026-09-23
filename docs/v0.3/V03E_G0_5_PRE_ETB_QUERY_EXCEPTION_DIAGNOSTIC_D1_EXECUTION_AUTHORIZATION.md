# DevRelay v0.3-E — G0.5-PRE / SIC
# ETB QUERY_EXCEPTION DIAGNOSTIC D1 — EXECUTION AUTHORIZATION (candidate)

> **ETB QUERY_EXCEPTION DIAGNOSTIC D1 — EXECUTION AUTHORIZATION**
> **CANDIDATE**
> **NOT ACCEPTED**
> **NOT EFFECTIVE**
> **GRANTS NO EXECUTION**
> **CREATES NO CLAIM NOW**
> **CREATES NO EVIDENCE NOW**
> **CREATES NO RESULT NOW**
> **NOT AN ETB SEMANTIC ATTEMPT**
> **DIAGNOSTIC OBSERVATIONS CAN NEVER BECOME ETB SEMANTIC RESULTS**

Status: **D1 EXECUTION AUTHORIZATION = CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE**
Script status: **D1 IMPLEMENTATION = CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED**

---

## 1. Purpose

This document is the execution-authorization contract for the
`ETB QUERY_EXCEPTION DIAGNOSTIC D1` diagnostic stage. Its only purpose is to let a future,
**separately authorized** one-shot run capture the missing listener-query failure detail behind
the already authoritative Recovery-R2 outcome, using the accepted frozen query shape.

D1 is **not** an ETB semantic attempt. Nothing it observes may produce or replace
`ETB_SATISFIED`, `ETB_UNSATISFIED` or `HARNESS_INVALID` as an ETB semantic result, and even a
future observed listener row MUST NOT be promoted to `ETB_SATISFIED`.

**This document grants nothing in this round.** It is a candidate contract only.

## 2. Accepted design provenance (authoritative)

| Item | Value |
| --- | --- |
| `diagnostic_d1_design_commit` | `b8f8a67beac154894e496aaa601fa0a4cd4e9905` |
| `diagnostic_d1_spec_sha256` | `29f0f9cc1632f2f344f5cb4e01d25a832ba9acc78caedbdd43861b7d68ac4154` |
| spec path | `docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_EXCEPTION_DIAGNOSTIC_D1_SPEC.md` |
| `D1_TOPLEVEL_FIELD_CLOSURE` | `19 / 19 CLOSED` |

The C1-clarified revision is the **current** accepted authority. The superseded revision
`6ad917b950c12e7a93579c519cc63f89925c2ab0` / `e9c521ff…` is recorded as
**PREVIOUSLY ACCEPTED / HISTORICAL AUTHORITATIVE PREDECESSOR / SUPERSEDED BY ACCEPTED C1
CLARIFICATION** — it is **not** rejected. The design acceptance bookkeeping commit
`80e937880b3484cac0ff471ffc22ebeb06ff5297` is a bookkeeping commit, **not** a design commit, and
does not replace the design authority above.

## 3. Candidate script provenance model

| Item | Candidate value |
| --- | --- |
| script path | `docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_EXCEPTION_DIAGNOSTIC_D1_EXECUTION.ps1` |
| `diagnostic_d1_script_sha256` | computed **after** the candidate commit; reported externally, never embedded |
| `diagnostic_d1_authorization_commit` | the candidate HEAD of this round (established after commit) |
| `diagnostic_d1_authorization_sha256` | SHA-256 of this document (established after commit) |

These three values are **CANDIDATE** until independent review and later acceptance
bookkeeping. The script deliberately does **not** embed its own commit id or its own expected
SHA-256 (no self-reference); both arrive as mandatory runtime parameters.

## 4. Future authorization provenance

A future execution uses the values frozen by the acceptance bookkeeping of this candidate:

`diagnostic_d1_authorization_commit` / `diagnostic_d1_authorization_sha256` /
`diagnostic_d1_script_sha256`.

None of them may be replaced by a later operational HEAD, a result-review commit, or any
execution-time state.

## 5. Mandatory future parameters

The script requires three mandatory parameters and has no usable default for any of them:

| Parameter | Meaning |
| --- | --- |
| `-AcceptedAuthorizationCommit` | the accepted authorization/implementation candidate commit |
| `-ExpectedAuthorizationSha256` | the accepted SHA-256 of this authorization document |
| `-ExpectedScriptSha256` | the accepted SHA-256 of the script |

## 6. Fixed non-self-referential constants (hard-coded in the script)

| Constant | Value |
| --- | --- |
| `diagnostic_d1_design_commit` | `b8f8a67beac154894e496aaa601fa0a4cd4e9905` |
| `diagnostic_d1_spec_sha256` | `29f0f9cc1632f2f344f5cb4e01d25a832ba9acc78caedbdd43861b7d68ac4154` |
| `source_authoritative_bookkeeping_commit` | `93e44fe61c59ec5070e2823062a607347bb9163a` |
| `source_r2_evidence_sha256` | `6f903f05e859a05a99dc0cde253e878ae7235c1554e212ab2f6b27945b2da0c8` |
| `source_r2_manifest_sha256` | `b4701c900132ffee9d9f31ac7c7137c906da80de97a08678544c7d7d7eb522c1` |
| `source_r2_result_sha256` | `84f51bb5d7765112cb65376ea164e10780bb777f1beb6e962d6baa4508fe9efa` |
| `source_r2_authorization_claim_sha256` | `fd7336e4694f8d491ddd3067880851f96974a29a1117d48f7dd47eb2d629ccf7` |
| `source_r2_attempt_claim_sha256` | `69eb6ef0352375311f72c211d04c8ed39e59d8f7b00b6d7738577044916167f9` |
| `config_sha256` | `b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf` |
| `config_size` | `1897` |
| diagnostic endpoint | `http://127.0.0.1:4096` |

## 7. C1-closed top-level constants

| Field | Frozen value | Type |
| --- | --- | --- |
| `schema_version` | `devrelay-etb-query-diagnostic-d1-v1` | required JSON string |
| `diagnostic_mode` | `QUERY_EXCEPTION_DIAGNOSTIC_D1` | required JSON string, constant, never runtime-variable |
| `endpoint` | `http://127.0.0.1:4096` | required JSON string **scalar** |

`endpoint` is **not** an object and does **not** inherit the `devrelay-etb-v1-r2` endpoint
object schema (no `scheme` / `address_family` / `host` / `port` / `base_uri` / `fallback`).
No `null`, no empty string, no alternate host, no IPv6, no `localhost` alias, no alternate port.

## 8. `configured_base_url` versus `endpoint`

`configured_base_url` is **distinct** from `endpoint` and must be obtained with the accepted
frozen Recovery-R2 config reader. It is **never** derived by copying the `endpoint` constant.
A future precondition requires both:

- `configured_base_url == "http://127.0.0.1:4096"`, and
- `configured_base_url == endpoint`.

The two fields are intentionally redundant for provenance and are never merged.

## 9. Exact `non_claims` array

Exactly 13 JSON strings, in exactly this order, with no split, join, rewording or reorder:

1. `does not establish ETB_SATISFIED`
2. `does not establish a replacement ETB_UNSATISFIED`
3. `does not establish P6 PASS`
4. `does not establish P6 FAIL`
5. `does not establish G0.5 PASS`
6. `does not establish G0.5 FAIL`
7. `does not authorize Mode-B`
8. `does not establish OpenCode general compatibility or incompatibility`
9. `does not establish permanent endpoint state`
10. `does not establish permanent listener state`
11. `does not establish process binding`
12. `does not establish target executable identity`
13. `does not establish Oracle-R2 general correctness or incorrectness`

## 10. Authorization claim schema

`schema_version = devrelay-etb-query-diagnostic-d1-authorization-use-v1`

Exact ordered fields (final field `state=CONSUMED`, no extra, no missing):

1. `schema_version`
2. `diagnostic_d1_design_commit`
3. `diagnostic_d1_spec_sha256`
4. `diagnostic_d1_authorization_commit`
5. `diagnostic_d1_authorization_sha256`
6. `diagnostic_d1_script_sha256`
7. `source_authoritative_bookkeeping_commit`
8. `source_r2_evidence_sha256`
9. `source_r2_result_sha256`
10. `source_r2_authorization_claim_sha256`
11. `source_r2_attempt_claim_sha256`
12. `state` = `CONSUMED`

## 11. Attempt claim schema

`schema_version = devrelay-etb-query-diagnostic-d1-attempt-use-v1`

Same remaining eleven ordered fields, same final `state=CONSUMED`. Only `schema_version`
differs.

## 12. Claim serialization

UTF-8, no BOM, LF-only, exactly one terminal LF, no CR, no blank leading line, no blank
trailing line, one field per line, exact format `<field_name>=<value>\n` in the frozen field
order, no quoting, no spaces around `=`.

## 13. Claim paths

| Kind | Path |
| --- | --- |
| AUTH TEMP | `docs/v0.3/evidence/ETB_QUERY_DIAGNOSTIC_D1_AUTHORIZATION_USE.claim.tmp` |
| AUTH FINAL | `docs/v0.3/evidence/ETB_QUERY_DIAGNOSTIC_D1_AUTHORIZATION_USE.claim` |
| ATTEMPT TEMP | `docs/v0.3/evidence/ETB_QUERY_DIAGNOSTIC_D1_ATTEMPT_USE.claim.tmp` |
| ATTEMPT FINAL | `docs/v0.3/evidence/ETB_QUERY_DIAGNOSTIC_D1_ATTEMPT_USE.claim` |

**Occupancy** for every TEMP/FINAL path means `File.Exists(path)` **or**
`Directory.Exists(path)`. Any occupied claim path before future execution: **FAIL CLOSED** —
no deletion, no overwrite, no reuse.

## 14. Atomic claim consumption

For each claim: (1) construct exact bytes; (2) require TEMP and FINAL unoccupied; (3) open TEMP
with `FileMode.CreateNew`; (4) `FileAccess.Write`; (5) `FileShare.None`; (6) write all bytes;
(7) `Flush(true)`; (8) close; (9) read TEMP back; (10) require exact byte equality; (11)
two-argument `Move` TEMP → FINAL; (12) read FINAL back; (13) require exact byte equality; (14)
compute SHA-256 of FINAL for reporting. **No overwrite, no delete, no replace, no retry, no
alternate filename.**

## 15. Consumption boundaries

A successful TEMP `CreateNew` is the **irreversible consumption boundary**:

- if AUTH TEMP `CreateNew` succeeds → `AUTHORIZATION USE = SPENT` permanently, even if later
  steps fail;
- if ATTEMPT TEMP `CreateNew` succeeds → `DIAGNOSTIC ATTEMPT = SPENT` permanently, even if
  later steps fail.

## 16. Future execution order (frozen)

`PRECONDITIONS → AUTH claim consumption → ATTEMPT claim consumption → D1 evidence-directory
creation → command-availability inspection → zero-or-one listener query → evidence publication
→ manifest publication → result publication → STOP.`

Never query before both claims are consumed. AUTHORIZATION failure ⇒ no ATTEMPT, no query.
ATTEMPT failure ⇒ no query. No retry in the same or a later run once either budget is consumed.

## 17. Preconsumption preconditions

Before AUTH TEMP `CreateNew`, **all** of the following must hold:

| # | Precondition |
| --- | --- |
| A | accepted D1 design commit = `b8f8a67beac154894e496aaa601fa0a4cd4e9905` |
| B | accepted D1 spec SHA-256 = `29f0f9cc1632f2f344f5cb4e01d25a832ba9acc78caedbdd43861b7d68ac4154`, verified both at the design commit and in the worktree |
| C | `AcceptedAuthorizationCommit` resolves to an exact Git commit |
| D | authorization artifact at that commit hashes to `ExpectedAuthorizationSha256` |
| E | script at that commit hashes to `ExpectedScriptSha256` |
| F | worktree authorization artifact hashes to `ExpectedAuthorizationSha256` |
| G | worktree script hashes to `ExpectedScriptSha256` |
| H | config SHA/size = `b5e4abab…` / `1897` |
| I | frozen config reader returns `http://127.0.0.1:4096` |
| J | `configured_base_url == endpoint` |
| K | R2 evidence / manifest / result hashes match |
| L | R2 authorization / attempt claim hashes match |
| M | all four D1 claim TEMP/FINAL paths absent |
| N | all six D1 output TEMP/FINAL paths absent |
| O | D1 evidence directory absent |
| P | D1 result absent |

Any failure ⇒ **STOP BEFORE CLAIM CONSUMPTION**; no claim, no query, no output.

## 18. Frozen config reader

The script reuses the **exact** accepted Recovery-R2 reader contract
(`PYTHONPATH=<repo>/src` + `python -c "import sys; from devrelay.config import
load_wiring_config; sys.stdout.write(load_wiring_config(sys.argv[1]).opencode.base_url)"
<repo>`), including its `PYTHONPATH` save/restore behaviour in a `finally` block that restores
**absence** rather than an invented empty value when no prior `PYTHONPATH` existed. No second
YAML parser. `PYTHONPATH` is never left changed. Config establishment is a precondition only;
D1 never mutates config.

## 19. Future invocation shape

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "<script>" `
  -AcceptedAuthorizationCommit "<accepted authorization commit>" `
  -ExpectedAuthorizationSha256 "<accepted authorization SHA-256>" `
  -ExpectedScriptSha256 "<accepted script SHA-256>"
```

**This is frozen conceptually and MUST NOT be run in this round.**

## 20. Script self-integrity

At future runtime, before any claim consumption, the script computes the SHA-256 of the running
script path and the SHA-256 of the script blob at `AcceptedAuthorizationCommit`, and requires
both to equal `ExpectedScriptSha256`. It performs the corresponding worktree/blob verification
for the authorization artifact. Any mismatch ⇒ precondition failure, no claim, no query.

## 21. Command availability

The script uses narrowly `Get-Command -Name 'Get-NetTCPConnection'` to establish `AVAILABLE` or
`UNAVAILABLE` and to populate the accepted command metadata. **This is not the listener query**
and is not counted as one. No unrelated command or module inventory is performed.

If unavailable: `query_outcome = COMMAND_UNAVAILABLE`, `listener_query_invocations = 0`, and the
accepted `COMMAND_UNAVAILABLE` representation is used.

## 22. Exact listener query and query count

The script contains **exactly one** executable listener-query site (verified statically):

```
Get-NetTCPConnection `
  -LocalAddress '127.0.0.1' `
  -LocalPort 4096 `
  -State Listen `
  -ErrorAction SilentlyContinue `
  -ErrorVariable qerr
```

structured as `$qerr = @()` immediately before, `try { $rows = @( <query> ) } catch { <capture
actual $_ ErrorRecord> }`. **Query invocation maximum = 1.** No second query, no retry, no
repeat, no polling, no alternate command, no equivalent reconstruction, no fallback.

## 23. Observation vocabulary and classifier

Only: `COMMAND_UNAVAILABLE`, `TERMINATING_EXCEPTION`, `ERROR_RECORDS_ZERO_ROWS`,
`ERROR_RECORDS_WITH_ROWS`, `ZERO_ROWS`, `ONE_ROW`, `MULTIPLE_ROWS`,
`DIAGNOSTIC_HARNESS_INVALID`. No ETB semantic result may be generated.

Classification after availability handling: terminating catch ⇒ `TERMINATING_EXCEPTION`; else
`qerr > 0 and row_count == 0` ⇒ `ERROR_RECORDS_ZERO_ROWS`; else `qerr > 0 and row_count > 0` ⇒
`ERROR_RECORDS_WITH_ROWS`; else `qerr == 0 and row_count == 0` ⇒ `ZERO_ROWS`; else `qerr == 0
and row_count == 1` ⇒ `ONE_ROW`; else `qerr == 0 and row_count > 1` ⇒ `MULTIPLE_ROWS`. No
overlap.

## 24. ErrorRecord normalization and channel separation

Exactly 15 ordered JSON strings: `source`, `fully_qualified_error_id`, `category`,
`category_activity`, `category_reason`, `category_target_name`, `category_target_type`,
`exception_type`, `exception_message`, `exception_hresult`, `inner_exception_type`,
`inner_exception_message`, `error_details_message`, `invocation_position_message`,
`script_stack_trace`. Unavailable ⇒ `""`. `exception_hresult`, when present, is the invariant
signed decimal **text** as a JSON string. No arbitrary object serialization.

`terminating_error` is `null` or one normalized record with `source = TERMINATING_EXCEPTION`.
`error_records` holds `qerr`-only normalized records with `source = ERROR_VARIABLE`.

**Deterministic no-duplication:** if and only if the **final** `qerr` entry has the same
normalized 14 payload fields as the terminating record (excluding `source`), exactly that one
final `qerr` entry is suppressed. All earlier entries are retained even if payload-identical.
Never more than one entry is removed.

## 25. Error-string P3

Standing P3 unchanged: **ERROR STRING MAXIMUM REPRESENTATION RULE = NOT YET FROZEN /
NON-BLOCKING DESIGN OBSERVATION**. This candidate serializes the full observed accepted string
values: no truncation, no hashing in place of content, no arbitrary object expansion. **This P3
is not claimed closed.**

## 26. Row evidence

Each row carries only the accepted fields in frozen order (`LocalAddress`, `LocalPort`, `State`,
`OwningProcess`). No process lookup, no executable resolution, no `CreationDate`, no executable
hash, no package/version, no target binding. Query-return order is preserved.

## 27. Top-level evidence order

Exactly, in order: `schema_version`, `source_authoritative_bookkeeping_commit`,
`source_r2_evidence_sha256`, `source_r2_result_sha256`, `execution_started_at`,
`execution_finished_at`, `diagnostic_mode`, `endpoint`, `configured_base_url`,
`powershell_environment`, `command_metadata`, `query`, `query_outcome`, `row_count`, `rows`,
`terminating_error`, `error_records`, `non_claims`, `activity_counters`. No missing field, no
extra field.

## 28. Null / empty contract

Required keys are always emitted. Unavailable strings ⇒ `""`. Empty arrays ⇒ `[]`.
`terminating_error` absent ⇒ `null`. Required integer fields ⇒ JSON integers. Row
`LocalPort` / `OwningProcess` ⇒ observed integer or `null`. Row `LocalAddress` / `State` ⇒
observed string or `""`. No conditional key omission.

## 29. Timestamp format

C1 delegates the exact textual format to this stage. Frozen as one exact UTC invariant format:

`[System.DateTimeOffset]::UtcNow.ToString("yyyy-MM-dd'T'HH:mm:ss.fffffff'Z'", [System.Globalization.CultureInfo]::InvariantCulture)`

Used for both `execution_started_at` and `execution_finished_at`. No local timestamps.

## 30. JSON serialization

Ordered structures throughout. `ConvertTo-Json -Depth 12 -Compress` (the same depth as the
accepted Oracle-R2 precedent; static schema analysis finds depth 12 sufficient: the deepest
object is a row or ErrorRecord at depth 3). File framing: UTF-8, no BOM, LF-only, exactly one
terminal LF.

## 31. Activity counters

`listener_query_invocations` = `0` or `1` truthfully; `process_queries` = `0`;
`target_executable_hashes` = `0`; `opencode_starts` = `0`; `http_requests` = `0`;
`provider_model_calls` = `0`; `retries` = `0`; `fallbacks` = `0`. No hidden retry.

## 32. Output paths

| Kind | Path |
| --- | --- |
| Evidence FINAL | `docs/v0.3/evidence/etb-query-diagnostic-d1/QUERY_DIAGNOSTIC_EVIDENCE.json` |
| Manifest FINAL | `docs/v0.3/evidence/etb-query-diagnostic-d1/MANIFEST.sha256` |
| Result FINAL | `docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_DIAGNOSTIC_RESULT_D1.md` |

Only their already reserved TEMP counterparts are used. No alternate path. No R2 path reuse.

## 33. Directory-creation timing

The D1 evidence directory MUST be absent during precondition validation and is **not** created
then. It is created exactly once, **after both claims are consumed**, before evidence TEMP
publication. If creation fails: the attempt remains spent, no retry, and no query if the query
has not yet occurred. This operational failure is distinct from any diagnostic query outcome.

## 34. Atomic output publication

For evidence, manifest and result: TEMP `CreateNew` → `FileAccess.Write` → `FileShare.None` →
write exact bytes → `Flush(true)` → close → readback exact bytes → two-argument `Move`
TEMP→FINAL → read FINAL → require byte equality. No overwrite, no delete, no replace, no retry.
Publication order: **evidence → manifest → result**.

## 35. Manifest format

Binds the evidence file only. Exact one line:
`<lowercase-evidence-sha256><two ASCII spaces><repository-relative evidence path><LF>`. No BOM,
no CR, no extra line. The manifest never self-lists.

## 36. Result format

Deterministic narrow text containing at minimum: result/schema version;
`diagnostic_d1_design_commit`; `diagnostic_d1_spec_sha256`;
`diagnostic_d1_authorization_commit`; `diagnostic_d1_authorization_sha256`;
`diagnostic_d1_script_sha256`; `source_authoritative_bookkeeping_commit`; evidence SHA-256;
manifest SHA-256; `query_outcome`; `listener_query_invocations`; authorization claim state
`CONSUMED`; attempt claim state `CONSUMED`; diagnostic authority state `CANDIDATE / REQUIRES
INDEPENDENT RESULT REVIEW`; `authoritative ETB semantic result remains = ETB_UNSATISFIED`; and
the explicit `non_claims` for P6 / G0.5 / Mode-B. The result does **not** duplicate full
ErrorRecord strings — those remain in evidence only.

## 37. `DIAGNOSTIC_HARNESS_INVALID` behaviour

For a post-consumption harness/control failure where the closed evidence schema can still be
constructed truthfully, the script publishes evidence with `query_outcome =
DIAGNOSTIC_HARNESS_INVALID` and truthful counters under the frozen null/empty rules. If the
mandatory evidence record cannot be truthfully constructed, **nothing is fabricated**: the
control state becomes **D1 OPERATIONAL HARNESS/PUBLICATION FAILURE**, which is **not** a
`query_outcome` value. No retry.

## 38. Publication-failure behaviour

If evidence / manifest / result publication fails after consumption: **NO RETRY**, no cleanup
designed to enable a retry, no second query. Already-created artifacts are preserved exactly as
forensic state. The control state is reported as **D1 PUBLICATION INCOMPLETE** — an
execution-control state only, **not** `COMMAND_UNAVAILABLE`, **not** `TERMINATING_EXCEPTION`,
**not** `DIAGNOSTIC_HARNESS_INVALID`, **not** `ETB_UNSATISFIED` and **not** any ETB semantic
result.

## 39. Exit-code contract (closed)

| Code | Meaning |
| --- | --- |
| `0` | complete evidence + manifest + result publication success |
| `10` | precondition failure before claim consumption |
| `20` | authorization claim consumption failure |
| `30` | attempt claim consumption failure |
| `40` | post-consumption harness failure |
| `50` | publication incomplete |

No other success code. Unexpected internal failures map deterministically to the appropriate
non-zero class without retry. The identical mapping is implemented in the script.

## 40. Protected-source requirements

Future execution must not modify: the accepted D1 design spec, Recovery-R2 authorization
artifact, Recovery-R2 claims, R2 evidence / manifest / result, Oracle-R2 spec and script, the
original frozen oracle, Recovery-R1 artifacts, the original authorization, `V03E_SPEC.md`,
`.devrelay/config.yaml`, `CONFIG_ESTABLISHMENT.json`, `src/devrelay`, `tests`,
`pyproject.toml`, `.gitattributes`.

## 41. Downstream non-claims

Future D1 evidence/result must state that the diagnostic observation does not by itself
establish: `ETB_SATISFIED`; a replacement `ETB_UNSATISFIED`; P6 PASS; P6 FAIL; G0.5 PASS;
G0.5 FAIL; Mode-B authorization; OpenCode general compatibility or incompatibility; permanent
endpoint state; permanent listener state; process binding; target executable identity; or the
correctness/incorrectness of Oracle-R2 generally. Any later decision to create a new ETB
authorization remains a separate owner decision.

## 42. Candidate status of this round

**D1 EXECUTION AUTHORIZATION = CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE.**
**D1 IMPLEMENTATION = CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED.**

This round created no claim, no evidence, no manifest, no result and no output directory, ran no
listener query, and consumed no budget. Budgets remain **D1 AUTHORIZATION USE = UNAVAILABLE /
NOT YET GRANTED**, **D1 DIAGNOSTIC ATTEMPT = UNAVAILABLE / NOT YET GRANTED** and **D1 LISTENER
QUERY EXECUTION = NOT AUTHORIZED**. Both D1 claim paths and all six output paths remain ABSENT.

**End of D1 execution authorization candidate.**
