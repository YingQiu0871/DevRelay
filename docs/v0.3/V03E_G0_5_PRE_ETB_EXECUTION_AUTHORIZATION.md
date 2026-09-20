# DevRelay v0.3-E — G0.5-PRE / SIC — ETB execution / configuration authorization

> **ETB EXECUTION / CONFIGURATION AUTHORIZATION**
> **CANDIDATE RECORD**
> **NOT ACCEPTED**
> **NOT EFFECTIVE**
> **DOES NOT MODIFY CONFIGURATION**
> **DOES NOT EXECUTE ETB**
> **DOES NOT START OPENCODE**
> **DOES NOT AUTHORIZE HTTP**
> **ONE ETB ATTEMPT ONLY IF LATER INDEPENDENTLY ACCEPTED**

Status: **ETB EXECUTION / CONFIGURATION AUTHORIZATION = ROUND-3 CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT EXECUTED**

Revision: **round-3 durable-claim remediation candidate** (supersedes the Round-2 candidate `390eda1`,
which received *REQUEST_CHANGES — V0.3-E ETB EXECUTION / CONFIGURATION AUTHORIZATION ROUND-2*,
P0 = 0, P1 = 1, P2 = 0, P3 = 2; and the earlier `f52cb2b`, which received *REQUEST_CHANGES — V0.3-E ETB
EXECUTION / CONFIGURATION AUTHORIZATION*, P0 = 0, P1 = 2, P2 = 2).  Both remain **rejected**.

Baseline: `390eda1aeacb33032611030d47727e0a69650459` (branch `v0.3-e-recovery-reconciliation`).

This artifact is a **candidate authorization record only**.  It authorizes nothing today: it modifies no
configuration, creates no claim marker, creates no evidence directory, executes no ETB attempt, starts no
OpenCode, issues no HTTP and publishes no evidence.  It becomes effective **only** if a separate
independent authorization review accepts it.  It is self-contained for a future executor and reviewer.

Accepted frozen oracle provenance (immutable; bound permanently):

| Item | Value |
| --- | --- |
| `oracle_commit` | `1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc` |
| `oracle_artifact` | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md` |
| `oracle_sha256` | `01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921` |

Current authoritative status: `ETB = DEFINITION ACCEPTED / NOT EXECUTED`; `ETB EXECUTION / ORACLE =
ACCEPTED / FROZEN / NOT EXECUTED / EXECUTION NOT AUTHORIZED`.

**Remediation scope.**  The Round-2 independent review **closed** `P1_A_CONFIG_MUTATION`,
`P1_B_AUTHORIZATION_REUSE`, `P2_A_OUTPUT_TIMING` and `P2_B_CONFIG_EVIDENCE`; all Round-2 frozen semantics
are **preserved unchanged** (§4–§9, §17–§18, §28–§31).  Round 3 closes the one remaining blocking finding —
the execution-evidence directory does not exist and parent-directory creation behaviour was unfrozen
(§15–§16) — and tightens the crash/replay nuance so that repository state alone durably distinguishes
**AUTHORIZATION UNUSED** / **AUTHORIZATION CONSUMED, ETB NOT STARTED** / **ETB ATTEMPT CONSUMED** without
relying on chat history, executor memory or an ephemeral process (§10–§14, §19–§25).

## 1. Purpose and scope

**1.1** This candidate authorization, **only after independent authorization review and acceptance**, may
authorize exactly two things, in this order:

* **A. one exact configuration establishment** — write `http://127.0.0.1:4096` to
  `<root>/.devrelay/config.yaml` → `opencode.base_url`; and then
* **B. exactly ONE ETB execution attempt** under the already accepted frozen ETB oracle.

**1.2** This round performs **neither A nor B**, and does not authorize them.

## 2. Authorized configuration mutation (exact; preserved)

| Item | Value |
| --- | --- |
| file | `<root>/.devrelay/config.yaml` |
| field | `opencode.base_url` |
| before | `""` (current value) |
| after | **`http://127.0.0.1:4096`** |

No trailing slash; no alternate URI; **no other configuration field change**; no other `.devrelay` field;
no source file; no test; no dependency; no version; no runtime implementation.

## 3. Owner inputs (preserved, not reinterpreted)

**MODE P — PRE-EXISTING TARGET**; **CLASS A — OWNER-SUPPLIED FIXED ENDPOINT**; scheme `http`; address
family IPv4; host `127.0.0.1`; port `4096`; base URI `http://127.0.0.1:4096`; fallback **NONE**.  No
substitution, no alternate endpoint, no Mode P → Mode L, no OpenCode start, no retry.

## 4. Static config audit (read-only; preserved)

| Fact | Value |
| --- | --- |
| `PRE_CONFIG_SHA256` | `daaf72578cb4a91b5adeb481530baf47577174325167caddf7249964da7923a8` |
| `PRE_CONFIG_SIZE` | `1876` bytes |
| BOM | **none** |
| line ending | **LF only** (0 CRLF), final LF present |
| encoding | valid UTF-8 |
| duplicate-key audit | **clean** at every mapping level; exactly one effective `opencode` key and exactly one effective `base_url` key; no anchors, aliases or merge keys |
| production-resolved pre-value | `opencode.base_url == ""` (`configured == False`) |

Because execution requires byte identity with this audited pre-image, the structural audit remains
applicable at execution time.

## 5. Byte-exact mutation anchor (preserved)

Unique span at offset **1065**, length 24, **occurrence count exactly 1**:

```
OLD_CONFIG_SPAN_HEX = 6f70656e636f64653a0a2020626173655f75726c3a202222
NEW_CONFIG_SPAN_HEX = 6f70656e636f64653a0a2020626173655f75726c3a2022687474703a2f2f3132372e302e302e313a3430393622
```

Statically constructed post-image: `POST_CONFIG_SIZE = 1897` bytes; `POST_CONFIG_SHA256 =
b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf`.  Byte-diff witness: 1065 unchanged
prefix bytes and 787 unchanged suffix bytes; only the frozen span changes.  No `yaml.safe_dump`, regex
edit, generic string replacement or manual-editor mutation is authorized.

## 6. Config mutation algorithm (preserved)

Read raw bytes → require SHA-256/size equal to the pre-image facts → require the OLD span occurs exactly
once → replace that one span with the NEW span → require the constructed bytes (before writing) to
hash/size to the post-image facts.  Any failure → `AUTHORIZATION_CONTROL_FAILURE` / ETB NOT STARTED.

## 7. Config temp / final paths (preserved)

`CONFIG FINAL = <root>/.devrelay/config.yaml`; `CONFIG TEMP = <root>/.devrelay/config.yaml.etb-auth.tmp`;
**`CONFIG BACKUP = NONE`**; the temp must not exist before mutation (else
`AUTHORIZATION_CONTROL_FAILURE`), with no delete, reuse, overwrite or retry.

## 8. Config write / durability procedure (preserved)

Single `python` invocation: read/verify pre-image → construct exact post-image bytes → exclusive create
(`xb`) the temp → write the complete post-image → stream flush → `os.fsync(temp_file.fileno())` → close →
read-back byte/hash verification → publish by exactly `os.replace(CONFIG_TEMP, CONFIG_FINAL)` in the same
directory → post-replace read-back verification → one production-reader invocation requiring the resolved
value `http://127.0.0.1:4096`.  No alternate rename primitive, no backup, no copy-delete sequence, no
direct in-place write, no retry.  Any failure → `AUTHORIZATION_CONTROL_FAILURE` / ETB NOT STARTED /
AUTHORIZATION SPENT.

## 9. Config semantic-preservation rule (preserved)

The post-image must be byte-identical to the pre-image outside the frozen span replacement, and the
executor must produce an exact byte-diff witness proving that only that span changed.  No unrelated
semantic or formatting change is authorized.

## 10. Control-marker parent and exact claim paths

**10.1** The two durable one-shot **claim markers** use the **already existing** repository directory
`docs/v0.3/evidence` as their parent.  They are **not** placed inside the currently non-existent
`etb-execution` directory.

| Marker | Final path | Temp path |
| --- | --- | --- |
| authorization claim | `docs/v0.3/evidence/ETB_AUTHORIZATION_USE.claim` | `docs/v0.3/evidence/ETB_AUTHORIZATION_USE.claim.tmp` |
| ETB attempt claim | `docs/v0.3/evidence/ETB_ATTEMPT_USE.claim` | `docs/v0.3/evidence/ETB_ATTEMPT_USE.claim.tmp` |

**10.2** These files are **control-state markers**: **not** ETB semantic evidence, **not** included in the
ETB `MANIFEST.sha256`, and **not** Mode-B evidence.

## 11. Claim presence is authoritative

**11.1** If **neither** the authorization claim temp **nor** its final exists → authorization state =
**UNUSED**.

**11.2** If **either** the authorization claim temp **or** its final exists → authorization state =
**CONSUMED**.  This remains true even if the claim content is incomplete, a process crashed during claim
writing, or the final rename never occurred.  **Presence of either file is deliberately fail-closed
evidence that the authorization was claimed.  No parser success is required.**

**11.3** If **neither** the ETB attempt claim temp **nor** its final exists → ETB attempt state =
**NOT STARTED** (subject to the authorization state).  If **either** exists → ETB attempt state =
**CONSUMED**.  Again: temp **or** final existence is enough, and no parser success is required.

## 12. Authorization claim content (schema)

Deterministic UTF-8 / **no BOM** / one-LF JSON; `schema_version = devrelay-etb-authorization-use-v1`;
`[ordered]` fields exactly:

```
schema_version
authorization_commit
authorization_sha256
oracle_commit
oracle_sha256
state
```

with `state = CONSUMED`.  No timestamp is required and no user/session/message/provider/model content is
included.

## 13. Authorization claim write procedure and durable consumption boundary

**13.1** At future operational execution, **before** config mutation, before creation of the
`etb-execution` directory, before `CONFIG_ESTABLISHMENT` evidence, before ETB-attempt claiming and before
ETB execution, the executor performs the **authorization claim**.

**13.2 Precondition:** the authorization claim **temp** and **final** must both be absent.  If either
exists, the authorization is **ALREADY CONSUMED** → STOP; do not reuse it, do not overwrite, delete or
repair it.

**13.3 Claim steps:** (1) construct the exact JSON bytes in memory; (2) open the authorization claim
**temp** with **exclusive-create** semantics; (3) **the moment exclusive creation of the temp succeeds,
`AUTHORIZATION_USE = 1/1 CONSUMED` — this is the durable consumption boundary**; (4) write all bytes;
(5) durably flush using the same frozen durable-write discipline used elsewhere (`Flush(true)` /
`os.fsync`); (6) close; (7) read back and verify the intended bytes; (8) move temp → final using a
same-directory **no-overwrite** move.

**13.4** If **any** failure occurs after step 3, the authorization **remains CONSUMED**, because temp
and/or final presence is the authoritative marker.  **No cleanup.  No retry.  No reuse.**  A new
authorization plus independent review is required.

## 14. Authorization crash recovery

**14.1** Crash **before** successful exclusive creation of the authorization claim temp → authorization =
**UNUSED**; a later operational invocation may still claim it.

**14.2** Crash **after** successful exclusive creation of the authorization claim temp → authorization =
**CONSUMED**; a later invocation sees temp or final and **MUST STOP**.

**14.3** There is therefore **no ambiguous pre-mutation crash window**.  **`PRE_CONFIG_SHA256` is no
longer used as the sole authorization-consumption marker** — the config pre-image/post-image remains a
**corroborating invariant only**.

## 15. Execution-evidence directory rule

**15.1** Exact execution-evidence directory: `docs/v0.3/evidence/etb-execution`.  **Design-time state: the
directory does NOT exist.**

**15.2** Future creation occurs **only after the authorization claim has been durably consumed and before
configuration mutation**.

**15.3** Frozen rule: if the directory does not exist, create **exactly**
`docs/v0.3/evidence/etb-execution` using
`[System.IO.Directory]::CreateDirectory("docs/v0.3/evidence/etb-execution")` (or the repository-root-resolved
exact equivalent).  **No alternate directory, no parent search, no timestamped directory, no suffix, no
fallback path.**

**15.4** After the call, require that **that exact path exists and is a directory**.  If creation fails or
the path resolves to anything else → `AUTHORIZATION_CONTROL_FAILURE`; `AUTHORIZATION_USE = 1/1 CONSUMED`;
`ETB_ATTEMPT = 0/1 NOT STARTED`; STOP.  No retry, no cleanup, no alternate directory.

## 16. Directory preexistence policy

**16.1** If `docs/v0.3/evidence/etb-execution` already exists at operational entry, it is permitted
**only** if it is an actual directory: do **not** delete it, do **not** recreate it, do **not** choose
another directory; all individually frozen output-preexistence rules still apply.

**16.2** If the path exists but is **not** a directory → `AUTHORIZATION_CONTROL_FAILURE` / authorization
consumed / ETB not started / STOP.  This makes `Directory.CreateDirectory` idempotency explicit and
removes executor choice.

## 17. Config-establishment paths (preserved)

`docs/v0.3/evidence/etb-execution/CONFIG_ESTABLISHMENT.json` (final) and
`docs/v0.3/evidence/etb-execution/CONFIG_ESTABLISHMENT.json.tmp` (temp).  After the exact directory rule of
§15–§16, **both must not exist before config mutation**; any existence → `AUTHORIZATION_CONTROL_FAILURE`
with authorization consumed, ETB not started, no deletion, no overwrite, no retry.

## 18. Config-establishment evidence schema (preserved)

`schema_version = devrelay-etb-config-establishment-v1`; `[ordered]` objects; the exact frozen 17-field
top-level order (`schema_version`, `authorization_commit`, `authorization_sha256`, `oracle_commit`,
`oracle_sha256`, `config_path`, `pre_config_sha256`, `expected_pre_config_sha256`, `pre_resolved_base_url`,
`authorized_base_url`, `post_config_sha256`, `expected_post_config_sha256`, `post_resolved_base_url`,
`mutation_scope`, `authorization_use`, `etb_attempt`, `control_status`) and constants (`config_path =
.devrelay/config.yaml`; `authorized_base_url = http://127.0.0.1:4096`; `mutation_scope =
opencode.base_url_only`; `authorization_use = 1/1_CONSUMED`; `etb_attempt = 0/1_NOT_STARTED`;
`control_status = CONFIG_ESTABLISHED`).  Serialization follows the accepted oracle conventions
(`ConvertTo-Json -Depth 12 -Compress`, UTF-8 no-BOM, one JSON line plus exactly one LF,
`UTF8Encoding(false)`, temp exclusive create → write → durable flush → close → read-back verification →
same-directory `System.IO.File.Move(temp, final)` without overwrite).  This file remains
authorization/configuration control evidence only — not ETB semantic evidence, not covered by the oracle
manifest, not an ETB result.

## 19. ETB attempt claim content (schema)

`schema_version = devrelay-etb-attempt-use-v1`; `[ordered]` fields exactly:

```
schema_version
authorization_commit
authorization_sha256
oracle_commit
oracle_sha256
state
```

with `state = CONSUMED`; UTF-8, no BOM, one LF.

## 20. ETB attempt claim procedure and durable consumption boundary

**20.1** Immediately **after** successful configuration establishment **and** successful
`CONFIG_ESTABLISHMENT.json` publication, but **before** entering the accepted frozen oracle, the executor
creates the ETB attempt claim.

**20.2 Precondition:** the ETB attempt claim **temp** and **final** must both be absent.  If either
exists, the ETB attempt has **already been consumed** → STOP; no rerun, no overwrite, no delete, no
repair.

**20.3 Steps:** exclusive-create `ETB_ATTEMPT_USE.claim.tmp` — **the moment exclusive creation succeeds,
`ETB_ATTEMPT = 1/1 CONSUMED`**; then write, durably flush, close, read back, and same-directory move
temp → final.

**20.4** Any failure after exclusive creation leaves the ETB attempt **CONSUMED**.  **No retry.  No second
ETB attempt.**

## 21. ETB crash recovery

**21.1** Neither ETB claim temp nor final present **and** the authorization claim present ⇒ authorization
consumed, **ETB attempt not started**.

**21.2** Either ETB claim temp or final present ⇒ **ETB attempt consumed**.

**21.3** Therefore a crash immediately after ETB-attempt consumption but before the oracle publishes
evidence can **never** permit rerunning ETB.

## 22. Entering the frozen oracle

**22.1** Only after successful ETB attempt claim creation/publication does the executor invoke the
accepted frozen oracle **from its first step**.  The accepted oracle remains **unchanged**, and its own
output-preexistence checks remain **inside** the already-consumed ETB attempt.

**22.2** If the oracle returns `ETB_SATISFIED`, `ETB_UNSATISFIED` or `HARNESS_INVALID / NO ETB SEMANTIC
RESULT`, the ETB attempt **remains consumed**.  No second attempt.

## 23. Durable state recovery table

| Authorization claim | ETB claim | Interpretation |
| --- | --- | --- |
| absent | absent | **AUTHORIZATION UNUSED** |
| present | absent | **AUTHORIZATION CONSUMED / ETB NOT STARTED** |
| present | present | **AUTHORIZATION CONSUMED / ETB ATTEMPT CONSUMED** |
| absent | present | **CONTROL-STATE INCONSISTENCY / FAIL CLOSED / NO EXECUTION / INDEPENDENT REVIEW REQUIRED** |

"present" means **temp OR final exists**.  No chat history is needed; no executor memory is needed.

## 24. Claim files after completion

**24.1** Neither claim marker may be deleted after success, `ETB_UNSATISFIED`, `HARNESS_INVALID`,
`AUTHORIZATION_CONTROL_FAILURE` or crash recovery: they are **durable one-shot witnesses**.

**24.2** Any later attempt requires a **new independently accepted authorization** with a **different
authorization identity** and separately frozen claim paths, or a separately reviewed archival/namespace
policy.  Do **not** silently reuse the old claim paths for a new authorization.

## 25. Future new-authorization namespace rule

**25.1** Because these claim paths permanently mark **this** authorization's use, a future independently
accepted additional ETB authorization **MUST define its own new claim-marker namespace/path before
execution**.  This Round-3 candidate authorizes only the current one-shot authorization, and **no future
executor may delete these markers to reuse the same paths**.

**25.2 Authorization identity model (preserved).**  If this Round-3 candidate is later independently
approved: `authorization_commit` = the approved Round-3 candidate commit; `authorization_sha256` = the
approved revised authorization artifact SHA.  A later bookkeeping commit or the execution-time HEAD must
**not** replace it, and the claim-marker content must use that exact accepted pair.

## 26. Revised operational order (frozen)

1. static verification of the independently accepted authorization identity and oracle provenance;
2. require the authorization claim temp/final **absent**;
3. **exclusive-create the authorization claim temp — `AUTHORIZATION_USE` becomes 1/1 CONSUMED here**;
4. complete/publish the authorization claim;
5. create-or-verify exactly `docs/v0.3/evidence/etb-execution` under §15–§16;
6. require `CONFIG_ESTABLISHMENT` final/temp absent;
7. verify the exact config pre-image SHA/size;
8. verify the production-resolved pre-value `""`;
9. construct the exact byte post-image;
10. write/fsync/read-back the config temp;
11. `os.replace` config temp → config final;
12. verify the final `POST_CONFIG_SHA256`;
13. verify the production-resolved `base_url == http://127.0.0.1:4096`;
14. publish `CONFIG_ESTABLISHMENT.json`;
15. require the ETB attempt claim temp/final **absent**;
16. **exclusive-create the ETB attempt claim temp — `ETB_ATTEMPT` becomes 1/1 CONSUMED here**;
17. complete/publish the ETB attempt claim;
18. invoke the accepted frozen ETB oracle **from its first step**;
19. permit only the frozen oracle control/result state;
20. publish only oracle-defined ETB evidence/result;
21. **STOP**;
22. independent ETB-result review.

No Mode-B work.

## 27. Failure semantics by window

**27.1 Pre-authorization-claim failure** (before successful exclusive creation of the authorization claim
temp): authorization remains **UNUSED**; no config mutation may have occurred; no ETB attempt may have
begun; no alternate operational action is permitted.  **This is the ONLY window in which the same accepted
authorization remains unused.**

**27.2 Post-authorization-claim failure** (after successful exclusive creation of the authorization claim
temp but before ETB claim creation): authorization **CONSUMED**, ETB **not started**,
`AUTHORIZATION_CONTROL_FAILURE`, STOP, new authorization required, no reuse.

**27.3 Post-ETB-claim failure** (after successful exclusive creation of the ETB claim temp): authorization
consumed, **ETB attempt consumed**, no second attempt.  If the frozen oracle itself was entered, use only
its result/control taxonomy.  If the failure occurs during claim finalization **before** the oracle is
entered: the ETB attempt is **still CONSUMED**, **no ETB semantic result exists**, STOP, independent
review required, no rerun.

**27.4 Pre-ETB control token (preserved).**  `AUTHORIZATION_CONTROL_FAILURE` means: authorization
consumed; ETB execution did NOT start; `ETB_ATTEMPT` remains 0 of 1; **no** ETB semantic/control result
exists; it is **not** `ETB_UNSATISFIED`, **not** `ETB_SATISFIED`, **not** `HARNESS_INVALID` from an ETB
attempt, **not** SIC/P6/G0.5 failure.

## 28. No-rollback (preserved)

Do **not** restore `base_url` automatically; do **not** delete durable claim markers; do **not** delete
config-evidence artifacts automatically.  After any failure following configuration replacement, the file
remains at the exact post-image unless a future separately authorized action changes it.  No executor
discretion.

## 29. Budgets (preserved; now durably witnessed)

| State variable | Budget | Durable witness |
| --- | --- | --- |
| `AUTHORIZATION_USE_BUDGET` | **1 of 1** | authorization claim temp/final presence |
| `ETB_ATTEMPT_BUDGET` | **1 of 1** | ETB attempt claim temp/final presence |

They are **not** the same boundary.

## 30. Other preserved boundaries

**30.1 Pre-existing target.**  Mode P verifies a pre-existing target; no starting, restarting or launching
OpenCode, no listener creation, no rebinding, no Mode P → Mode L.  If the exact pre-existing target is
absent or cannot satisfy the frozen oracle, the attempt fails according to the oracle — **no recovery by
target creation**.

**30.2 No-fallback.**  Fallback stays **NONE**: no IPv4 → IPv6, no `localhost`, no `::1`, no other /
first-free / ephemeral port, no alternate executable or installation, no PATH-selected target, no
log/listener/process-derived endpoint, no retry against another endpoint.

**30.3 HTTP and OpenCode boundaries.**  The ETB execution performs **no HTTP**, no `/doc`, no `/session`
and no provider/model request; no Mode-B HTTP activity is authorized; `opencode serve`, OpenCode
launch/restart, process replacement and listener creation are **not** authorized.

**30.4 Result non-claims.**  The one-shot execution may produce only `ETB_SATISFIED`,
`ETB_UNSATISFIED`, or `HARNESS_INVALID / NO ETB SEMANTIC RESULT`; none is authoritative before separate
independent ETB-result review.  `ETB_SATISFIED` does **not** itself establish SIC semantics, P6, G0.5,
session incarnation, turn provenance, message provenance, pending-handle semantics, Mode-B PASS, Case-C
authorization or `adopt_completed_turn`; it only allows independent ETB result review and, only once
`ETB_SATISFIED` is independently accepted, resumption of Mode-B SIC oracle construction.
`ETB_UNSATISFIED` is only a prerequisite/control result (**not** SIC/P6/G0.5 failure and **not** a claim
that OpenCode cannot support Mode B).  `HARNESS_INVALID` means **NO ETB SEMANTIC RESULT EXISTS**, with no
retry and no repair-and-continue inside the same authorization.

**30.5 Execution outputs.**  Only the evidence/result paths already frozen by the accepted oracle may be
used: no new alternative evidence path, no alternative result path, no alternate manifest, no
executor-selected filenames.  The oracle's output-preexistence rule applies inside the oracle (§22).

**30.6 Mode-B / G0.5 / P6 / implementation.**  Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE /
CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER` (this
authorization candidate does not unblock it); `G0.5 / P6 = NOT RUN / DEFINITION ACCEPTED / ORACLE NOT
FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED` and G0.5 **NOT CLOSED**; Case-C and
v0.3-E implementation `NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`; `adopt_completed_turn` **DISABLED**.

## 31. Rejected authorization history

**31.1** `f52cb2b4c0ece73097511c816b448d9ede649fb5` received *REQUEST_CHANGES — V0.3-E ETB EXECUTION /
CONFIGURATION AUTHORIZATION* (P0 = 0, P1 = 2, P2 = 2) and remains rejected.
**31.2** `390eda1aeacb33032611030d47727e0a69650459` received *REQUEST_CHANGES — V0.3-E ETB EXECUTION /
CONFIGURATION AUTHORIZATION ROUND-2* (P0 = 0, P1 = 1, P2 = 0, P3 = 2) and remains rejected.
**31.3** Neither is rewritten or amended; the candidate in force is **this round-3 revision**.

## 32. Current round status and activity counters

```
ETB EXECUTION / CONFIGURATION AUTHORIZATION = ROUND-3 CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT EXECUTED
ETB EXECUTION / ORACLE                        = ACCEPTED / FROZEN / NOT EXECUTED
ETB                                           = DEFINITION ACCEPTED / NOT EXECUTED
```

**32.1** No authorization is currently granted; **no claim marker currently exists**; no evidence
directory is created now; no config mutation occurs now.

**32.2** This remediation-design round performed: web/network `0`; endpoint query `0`;
`Get-NetTCPConnection` `0`; live `Get-CimInstance` `0`; port/listener/process enumeration `0`; config
mutation `0`; OpenCode start `0`; HTTP `0`; `/doc` `0`; `/session` `0`; `Add-Type` `0`; P/Invoke `0`;
execution-evidence publication `0`; ETB execution `0`; SIC `0`; Mode-B work `0`; provider/model `0`;
G0.5 `0`; G1/G2 `0`; runtime/test/dependency/version changes `0`.  Static repository/document/config
inspection is not operational ETB activity.

**End of ETB execution / configuration authorization candidate record (round-3 durable-claim remediation).**
