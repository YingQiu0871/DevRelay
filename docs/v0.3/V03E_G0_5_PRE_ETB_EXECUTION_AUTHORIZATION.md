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

Status: **ETB EXECUTION / CONFIGURATION AUTHORIZATION = ROUND-2 CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT EXECUTED**
Revision: **round-2 remediation candidate** (supersedes the rejected candidate `f52cb2b4`, which received
*REQUEST_CHANGES — V0.3-E ETB EXECUTION / CONFIGURATION AUTHORIZATION*, P0 = 0, P1 = 2, P2 = 2; that
candidate remains **rejected**).

Baseline: `f52cb2b4c0ece73097511c816b448d9ede649fb5` (branch `v0.3-e-recovery-reconciliation`).

This artifact is a **candidate authorization record only**.  It authorizes nothing today: it modifies no
configuration, executes no ETB attempt, starts no OpenCode, issues no HTTP, publishes no evidence and
creates no result.  It becomes effective **only** if a separate independent authorization review accepts
it.  It is self-contained for a future executor and for a future independent reviewer.

Accepted frozen oracle provenance (immutable; bound permanently):

| Item | Value |
| --- | --- |
| `oracle_commit` | `1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc` |
| `oracle_artifact` | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md` |
| `oracle_sha256` | `01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921` |

Current authoritative status: `ETB = DEFINITION ACCEPTED / NOT EXECUTED`; `ETB EXECUTION / ORACLE =
ACCEPTED / FROZEN / NOT EXECUTED / EXECUTION NOT AUTHORIZED`.

**Remediation scope (round 2).**  The independent review accepted this authorization's scope, oracle
provenance, owner tuple, one-ETB-attempt ceiling, no-OpenCode-start rule, no-HTTP rule, fallback NONE,
configuration-after-attempt policy, ETB result/non-claim semantics and Mode-B/G0.5 preservation; those
are **preserved unchanged**.  This revision closes exactly four gaps: **P1-A** the config-mutation
mechanism (now frozen byte-exactly, §5–§9), **P1-B** authorization-use / pre-live-probe failure / reuse
semantics (§11–§13, §21–§22), **P2-A** the output-precondition timing conflict with the ETB attempt start
(§18–§19), and **P2-B** the configuration-establishment evidence path/format (§14–§17).

## 1. Purpose and scope

**1.1** This candidate authorization, **only after independent authorization review and acceptance**, may
authorize exactly two things, in this order:

* **A. one exact configuration establishment** — write `http://127.0.0.1:4096` to
  `<root>/.devrelay/config.yaml` → `opencode.base_url`; and then
* **B. exactly ONE ETB execution attempt** under the already accepted frozen ETB oracle.

**1.2** This round performs **neither A nor B**, and does not authorize them.

## 2. Authorized configuration mutation (exact)

| Item | Value |
| --- | --- |
| file | `<root>/.devrelay/config.yaml` |
| field | `opencode.base_url` |
| before | `""` (current value) |
| after | **`http://127.0.0.1:4096`** |

**2.1** No trailing slash; no alternate URI; **no other configuration field change**; no other `.devrelay`
field; no source file; no test; no dependency; no version; no runtime implementation.

## 3. Owner inputs (preserved, not reinterpreted)

| Input | Frozen value |
| --- | --- |
| mode | **MODE P — PRE-EXISTING TARGET** |
| endpoint policy | **CLASS A — OWNER-SUPPLIED FIXED ENDPOINT** |
| scheme | `http` |
| address family | **IPv4** |
| host | `127.0.0.1` |
| port | `4096` |
| base URI | `http://127.0.0.1:4096` |
| fallback | **NONE** |

No substitution, no alternate endpoint, no Mode P → Mode L, no OpenCode start, no retry.

## 4. Static config audit (this design round; read-only)

**4.1 Frozen pre-image facts** (obtained by read-only hashing/parsing of the current file in this round):

| Fact | Value |
| --- | --- |
| `PRE_CONFIG_SHA256` | `daaf72578cb4a91b5adeb481530baf47577174325167caddf7249964da7923a8` |
| `PRE_CONFIG_SIZE` | `1876` bytes |
| BOM | **none** (file does not start with `EF BB BF`) |
| line ending | **LF only** (0 CRLF, 54 LF), file ends with a final LF |
| encoding | valid UTF-8 |

**4.2 Duplicate-key / structural audit (read-only).**  A read-only parse with a duplicate-detecting
mapping constructor (production code unchanged) reported **no duplicate keys at any mapping level**.  The
root mapping keys are exactly `profiles`, `review`, `opencode`, `codex`; there is **exactly one effective
`opencode` key**; the `opencode` mapping is a dict whose keys are `base_url`, `workspace`,
`default_session`, `agent`, `model`, `timeout_seconds`, `idle_timeout_seconds`,
`poll_interval_seconds`, `max_response_bytes`, `max_messages`, `allow_unknown_workspace`, and it contains
**exactly one effective `base_url` key**; there are **no YAML anchors, aliases or merge keys** (`<<`)
anywhere in the file.

**4.3 Production-reader verification (read-only, static).**  Invoking the accepted production reader
read-only resolves `load_wiring_config(<root>).opencode.base_url == ''` and `configured == False`, i.e.
the current file is **valid under the production reader** and the pre-value is the empty string.

**4.4 Consequence.**  Because the future mutation requires byte identity with this exact pre-image (§6),
the structural audit of §4.2 remains applicable at execution time; no duplicate-key ambiguity can arise
from a file that must hash-match a uniquely-audited pre-image.

## 5. Byte-exact mutation anchor

**5.1** `yaml.safe_dump` and any general whole-document YAML rewriting are **not authorized**.  The
mutation is a **byte-exact patch** against the audited pre-image.

**5.2 Frozen unique span** (byte offset `1065`, length 24, **occurrence count exactly 1**):

```
OLD_CONFIG_SPAN_HEX = 6f70656e636f64653a0a2020626173655f75726c3a202222
```

which is exactly the bytes `opencode:` + LF + two spaces + `base_url: ` + `""`.

**5.3 Frozen replacement span** (length 45):

```
NEW_CONFIG_SPAN_HEX = 6f70656e636f64653a0a2020626173655f75726c3a2022687474703a2f2f3132372e302e302e313a3430393622
```

which is exactly the bytes `opencode:` + LF + two spaces + `base_url: ` + `"http://127.0.0.1:4096"`.

**5.4 All indentation, quoting convention, comments and line-ending bytes outside the scalar change
remain identical.**

**5.5 Statically constructed post-image** (recorded so the future executor verifies rather than derives):

| Fact | Value |
| --- | --- |
| `POST_CONFIG_SIZE` | `1897` bytes (pre-image `1876` + 21) |
| `POST_CONFIG_SHA256` | `b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf` |

**5.6 Byte-diff witness (verified statically in this round):** the pre-image prefix before the span
(1065 bytes) and the pre-image suffix after the span (787 bytes) are **identical** in the post-image;
**only** the frozen span changed.  The post-image re-parses with `opencode.base_url ==
'http://127.0.0.1:4096'` and an unchanged top-level key list.

## 6. Future config mutation algorithm (frozen)

The future execution must, exactly:

1. read `<root>/.devrelay/config.yaml` as **raw bytes**;
2. require `SHA-256 == PRE_CONFIG_SHA256` **and** byte length `== PRE_CONFIG_SIZE` — any mismatch →
   `AUTHORIZATION_CONTROL_FAILURE` / ETB NOT STARTED;
3. require `OLD_CONFIG_SPAN_HEX` occurs **exactly once** — otherwise `AUTHORIZATION_CONTROL_FAILURE` /
   ETB NOT STARTED;
4. replace that one exact byte span with `NEW_CONFIG_SPAN_HEX` — **no** YAML load/dump mutation, **no**
   regex edit, **no** generic string replacement, **no** manual editor, **no** alternate mechanism;
5. require the constructed bytes, before writing, to satisfy `SHA-256 == POST_CONFIG_SHA256` and size
   `== POST_CONFIG_SIZE` — otherwise `AUTHORIZATION_CONTROL_FAILURE` / ETB NOT STARTED.

## 7. Config temp / final paths

| Item | Value |
| --- | --- |
| CONFIG FINAL | `<root>/.devrelay/config.yaml` |
| CONFIG TEMP | `<root>/.devrelay/config.yaml.etb-auth.tmp` |
| CONFIG BACKUP | **NONE** |

**7.1** Before mutation, `CONFIG TEMP` **MUST NOT EXIST**; if it exists →
`AUTHORIZATION_CONTROL_FAILURE` / ETB NOT STARTED.  No delete, no reuse, no overwrite, no retry.

## 8. Config write / durability procedure (frozen; single `python` interpreter invocation)

The writer must, exactly:

1. read and verify the pre-image as §6 steps 1–2;
2. construct the exact post-image bytes per §5–§6;
3. open `CONFIG TEMP` with **exclusive-create** semantics equivalent to mode **`xb`**;
4. write the complete post-image bytes;
5. flush the Python stream, then call **`os.fsync(temp_file.fileno())`**, then close it;
6. read `CONFIG TEMP` back as bytes and require **byte-for-byte equality** with the intended post-image
   and `SHA-256 == POST_CONFIG_SHA256`;
7. publish using exactly **`os.replace(CONFIG_TEMP, CONFIG_FINAL)`** with both paths in the same
   directory — no alternate rename primitive, no backup, no copy-delete sequence, no direct in-place
   write, no retry;
8. after `os.replace`, read `CONFIG FINAL` back and require byte-for-byte equality with the intended
   post-image and `SHA-256 == POST_CONFIG_SHA256`;
9. invoke the accepted production reader **exactly once** and require
   `load_wiring_config(...).opencode.base_url == 'http://127.0.0.1:4096'`.

**8.1** Any failure anywhere in this configuration-establishment procedure →
`AUTHORIZATION_CONTROL_FAILURE` / ETB NOT STARTED / **AUTHORIZATION SPENT**.  No rollback, no alternate
writer, no second mutation attempt.

## 9. Config semantic-preservation rule

**9.1** Because execution requires byte identity with the exact statically audited pre-image
(`PRE_CONFIG_SHA256`), the §4.2 structural audit remains applicable at execution time.

**9.2** The post-image must be **byte-identical to the pre-image outside** the frozen
`OLD_CONFIG_SPAN` → `NEW_CONFIG_SPAN` replacement, and the executor must produce an **exact byte-diff
witness** proving that **only** the frozen span changed.  No unrelated semantic or formatting change is
authorized.

## 10. Authorization identity model

**10.1** `authorization_commit` = the independently accepted commit containing **this revised**
authorization artifact; `authorization_sha256` = the independently accepted blob SHA-256 of **this
revised** authorization artifact.

**10.2** A later acceptance-bookkeeping commit or the execution-time HEAD **MUST NOT** replace
`authorization_commit`.  The eventual independent approval record will bind the exact pair, and future
execution must use that independently accepted pair.

## 11. Two separate budgets

| State variable | Budget |
| --- | --- |
| `AUTHORIZATION_USE_BUDGET` | **1 of 1** |
| `ETB_ATTEMPT_BUDGET` | **1 of 1** |

**11.1** They are **not** the same boundary.

## 12. Authorization-use consumption

**12.1** The accepted authorization is consumed **exactly once**, at the **very beginning** of the future
operational execution round, **before** config mutation, config-evidence creation, oracle output checks
or ETB execution: set `AUTHORIZATION_USE = 1 of 1 CONSUMED`.

**12.2** Once consumed, the same authorization can **never** be reused.  Any failure after this point —
**even if ETB never starts** — means **STOP**; a new authorization plus independent review is required for
any future operational try.  **No preparation-retry loophole exists.**

## 13. Pre-ETB control-failure token

**13.1** Frozen pre-ETB control state: **`AUTHORIZATION_CONTROL_FAILURE`**, meaning: the accepted
authorization was consumed; **ETB execution did NOT start**; `ETB_ATTEMPT` remains **0 of 1**; **no** ETB
semantic/control result exists.

**13.2** It is **NOT** `ETB_UNSATISFIED`, **NOT** `ETB_SATISFIED`, **NOT** `HARNESS_INVALID` from an ETB
attempt, **NOT** SIC FAIL, **NOT** P6 FAIL, **NOT** G0.5 FAIL.

**13.3** After `AUTHORIZATION_CONTROL_FAILURE`: STOP; no retry; no repair-and-continue; new authorization
required.

## 14. Config-establishment evidence path

| Item | Value |
| --- | --- |
| FINAL | `docs/v0.3/evidence/etb-execution/CONFIG_ESTABLISHMENT.json` |
| TEMP | `docs/v0.3/evidence/etb-execution/CONFIG_ESTABLISHMENT.json.tmp` |

**14.1** This file is **authorization/configuration control evidence** — **NOT** ETB semantic evidence,
**NOT** covered by the ETB oracle `MANIFEST.sha256`, and **NOT** an ETB result.

**14.2** Before any config mutation, and after `AUTHORIZATION_USE` is consumed, **both** FINAL and TEMP
**MUST NOT EXIST**; if either exists → `AUTHORIZATION_CONTROL_FAILURE`.  No delete, no overwrite, no
retry.

## 15. Config-establishment JSON schema

**15.1** `schema_version = devrelay-etb-config-establishment-v1`; every object `[ordered]`; top-level
ordered fields exactly:

```
schema_version
authorization_commit
authorization_sha256
oracle_commit
oracle_sha256
config_path
pre_config_sha256
expected_pre_config_sha256
pre_resolved_base_url
authorized_base_url
post_config_sha256
expected_post_config_sha256
post_resolved_base_url
mutation_scope
authorization_use
etb_attempt
control_status
```

**15.2 Frozen values:** `config_path = .devrelay/config.yaml`; `authorized_base_url =
http://127.0.0.1:4096`; `mutation_scope = opencode.base_url_only`; `authorization_use = 1/1_CONSUMED`;
`etb_attempt = 0/1_NOT_STARTED`; `control_status = CONFIG_ESTABLISHED` (success case).

## 16. Config-evidence serialization

**16.1** Reuse the accepted oracle's deterministic JSON conventions: `ConvertTo-Json -Depth 12 -Compress`,
UTF-8, **no BOM**, one JSON line, **exactly one final LF**, no CRLF conversion; writer uses
`UTF8Encoding(false)`.

**16.2** The same discipline applies: temp exclusive create → write → durable flush (`Flush(true)`) →
close → read-back exact-byte verification → same-directory publication using exactly
**`System.IO.File.Move(temp, final)`** without overwrite, after the temp is fully written and verified.

**16.3** Any failure → `AUTHORIZATION_CONTROL_FAILURE`; **no ETB start**.

## 17. Config-evidence content

On successful config establishment, record: `authorization_commit`; `authorization_sha256`;
`oracle_commit = 1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc`; `oracle_sha256 =
01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921`; config path; pre-config **actual**
SHA; expected `PRE_CONFIG_SHA256`; pre-production-resolved `base_url`; authorized `base_url`;
post-config **actual** SHA; expected `POST_CONFIG_SHA256`; post-production-resolved `base_url`;
`mutation_scope`; authorization-use state; ETB-attempt state.  No prompt/session/message/provider/model
content.

## 18. ETB attempt start — revised boundary

**18.1** The former "immediately before the first live listener probe" boundary is **removed**.

**18.2** Frozen instead: `ETB_ATTEMPT = 1 of 1 CONSUMED` **immediately before entering the accepted frozen
ETB oracle at its FIRST oracle step**.

**18.3** Thus **all** frozen oracle machinery — oracle identity checks, oracle output-preexistence checks,
HARNESS validation and the later live listener/process queries — occurs **inside** the one consumed ETB
attempt.  This reconciles `HARNESS_INVALID` with the attempt budget.

## 19. Oracle output-precondition timing

**19.1** The authorization layer does **NOT** pre-check or reinterpret the accepted oracle's six
temp/final output paths.

**19.2** After configuration is established successfully **and** `CONFIG_ESTABLISHMENT.json` is
successfully published, the executor consumes `ETB_ATTEMPT = 1 of 1` and invokes the accepted frozen
oracle **from its first step**; the oracle itself performs its own frozen six-path preexistence
validation.

**19.3** If that oracle check fails, the ETB attempt is **already 1 of 1 consumed** and the accepted
oracle may return `HARNESS_INVALID / NO ETB SEMANTIC RESULT` exactly as frozen.  **No boundary
contradiction remains.**

## 20. Future operational order (frozen)

1. enter the independently accepted authorization;
2. **immediately** set `AUTHORIZATION_USE = 1 of 1 CONSUMED`;
3. verify accepted authorization identity;
4. verify accepted oracle provenance;
5. verify `CONFIG_ESTABLISHMENT.json` and its `.tmp` do not exist;
6. verify current config bytes against `PRE_CONFIG_SHA256` / `PRE_CONFIG_SIZE`;
7. verify the production-resolved pre-value `== ""`;
8. construct the deterministic byte-exact post-image;
9. write/flush/read-back `CONFIG TEMP` (§8 steps 3–6);
10. `os.replace(CONFIG TEMP → CONFIG FINAL)`;
11. read back final bytes and verify `POST_CONFIG_SHA256`;
12. verify production-resolved `base_url == http://127.0.0.1:4096`;
13. publish `CONFIG_ESTABLISHMENT.json` under §14–§17;
14. set `ETB_ATTEMPT = 1 of 1 CONSUMED`;
15. invoke the accepted frozen ETB oracle **from its first step**;
16. allow exactly the oracle-defined result/control state;
17. publish only the oracle-defined candidate evidence/result;
18. **STOP**;
19. independent ETB result review.

No Mode-B work in this operational round.

## 21. Failure before ETB start

**21.1** If **any** step 3–13 fails: `AUTHORIZATION_CONTROL_FAILURE`; `AUTHORIZATION_USE = 1/1 CONSUMED`;
`ETB_ATTEMPT = 0/1 NOT STARTED`; **STOP**.  No ETB result, no retry, no reuse of the authorization, no
alternate config method, no rollback.  A new authorization plus independent review is required before
another operational attempt.

## 22. Failure after ETB start

**22.1** Once step 14 occurs: `AUTHORIZATION_USE = 1/1 CONSUMED` and `ETB_ATTEMPT = 1/1 CONSUMED`.  All
subsequent result/control semantics come **only** from the accepted frozen oracle: `ETB_SATISFIED`,
`ETB_UNSATISFIED`, or `HARNESS_INVALID / NO ETB SEMANTIC RESULT`.  No second attempt under this
authorization.

## 23. Configuration after any failure

**23.1** No-rollback policy preserved.  If configuration replacement already occurred, then even if a
later step fails (config-establishment evidence publication, `ETB_UNSATISFIED`, `HARNESS_INVALID`, or any
other post-replacement failure), the executor must **NOT** automatically restore `""`.  The file remains
at the exact post-image unless a **future separately authorized** action changes it.  No executor
discretion.

## 24. Accepted oracle immutability

**24.1** `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md` must **not** be modified and no accepted oracle
execution semantics may be altered.  This authorization only fixes configuration establishment,
authorization consumption, pre-ETB control evidence, and the point at which the frozen oracle attempt
begins.

## 25. Other preserved boundaries

**25.1 Pre-existing target.**  Mode P verifies a pre-existing target; no starting, restarting or launching
OpenCode, no listener creation, no rebinding, no Mode P → Mode L.  If the exact pre-existing target is
absent or cannot satisfy the frozen oracle, the attempt fails according to the oracle — **no recovery by
target creation**.

**25.2 No-fallback.**  Fallback stays **NONE**: no IPv4 → IPv6, no `localhost`, no `::1`, no other /
first-free / ephemeral port, no alternate executable or installation, no PATH-selected target, no
log/listener/process-derived endpoint, no retry against another endpoint.

**25.3 HTTP and OpenCode boundaries.**  The ETB execution performs **no HTTP**, no `/doc`, no `/session`
and no provider/model request; no Mode-B HTTP activity is authorized; `opencode serve`, OpenCode
launch/restart, process replacement and listener creation are **not** authorized.

**25.4 Result non-claims.**  The one-shot execution may produce only `ETB_SATISFIED`,
`ETB_UNSATISFIED`, or `HARNESS_INVALID / NO ETB SEMANTIC RESULT`; none is authoritative before separate
independent ETB-result review.  `ETB_SATISFIED` does **not** itself establish SIC semantics, P6, G0.5,
session incarnation, turn provenance, message provenance, pending-handle semantics, Mode-B PASS, Case-C
authorization or `adopt_completed_turn`; it only allows independent ETB result review and, only once
`ETB_SATISFIED` is independently accepted, resumption of Mode-B SIC oracle construction.
`ETB_UNSATISFIED` is only a prerequisite/control result (**not** SIC/P6/G0.5 failure and **not** a claim
that OpenCode cannot support Mode B).  `HARNESS_INVALID` means **NO ETB SEMANTIC RESULT EXISTS** with no
retry and no repair-and-continue inside the same authorization.

**25.5 Execution outputs.**  Only the evidence/result paths already frozen by the accepted oracle may be
used: no new alternative evidence path, no alternative result path, no alternate manifest, no
executor-selected filenames.  The accepted oracle's output-preexistence rule applies inside the oracle
(§19).

**25.6 Mode-B / G0.5 / P6 / implementation.**  Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE /
CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER` (this
authorization candidate does not unblock it); `G0.5 / P6 = NOT RUN / DEFINITION ACCEPTED / ORACLE NOT
FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED` and G0.5 **NOT CLOSED**;
Case-C and v0.3-E implementation `NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`; `adopt_completed_turn`
**DISABLED**.

## 26. Rejected authorization history

**26.1** `f52cb2b4c0ece73097511c816b448d9ede649fb5` received *REQUEST_CHANGES — V0.3-E ETB EXECUTION /
CONFIGURATION AUTHORIZATION* (P0 = 0, P1 = 2, P2 = 2) and **remains rejected**; its history is **not**
rewritten or amended.  The candidate in force is **this round-2 remediation revision**.

## 27. Current round status and activity counters

```
ETB EXECUTION / CONFIGURATION AUTHORIZATION = ROUND-2 CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT EXECUTED
ETB EXECUTION / ORACLE                        = ACCEPTED / FROZEN / NOT EXECUTED
ETB                                           = DEFINITION ACCEPTED / NOT EXECUTED
```

**27.1** No authorization is granted now; no config changed now; no ETB executed now.

**27.2** This remediation-design round performed: web/network `0`; endpoint query `0`;
`Get-NetTCPConnection` `0`; live `Get-CimInstance` `0`; port/listener/process enumeration `0`; config
mutation `0`; OpenCode start `0`; HTTP `0`; `/doc` `0`; `/session` `0`; `Add-Type` `0`; P/Invoke `0`;
execution-evidence publication `0`; ETB execution `0`; SIC `0`; Mode-B oracle work `0`; provider/model
`0`; G0.5 `0`; G1/G2 `0`; runtime/test/dependency/version changes `0`.  Static config reads, hashes and
the duplicate-structure audit are recorded separately and are not operational ETB activity.

**End of ETB execution / configuration authorization candidate record (round-2 remediation).**
