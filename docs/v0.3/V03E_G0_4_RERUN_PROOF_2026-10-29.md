# DevRelay v0.3-E — G0.4 / P4 rerun proof (2026-10-29)

**Status: CANDIDATE RESULT, recorded by the executing (implementing) agent — NOT
self-approved.  Candidate verdict: `EVIDENCE_INSUFFICIENT` →
CANDIDATE FAIL / P4 UNPROVEN** (reason `CANDIDATE_IDENTIFIER_SEMANTICS_UNRESOLVED`).
The independent reviewer decides.  `adopt_completed_turn` stays disabled; no capability
changed.  The prior round (`V03E_G0_4_API_INSPECTION_PROOF.md`) stays final and is not
superseded.

## 1. Identity and authorization

| Item | Value |
| --- | --- |
| Definition | revision-3 oracle + provisioning addendum + harness, independent decision **ACCEPT — V0.3-E G0.4 REVISION 4 COMPOSITE (FROZEN AT 36ba030)** |
| Oracle blob / SHA-256 | `34b0f5e8…` / `b0c34fa19c3e639b5637d74d49e1c9c357b7db914ee1becf70229f3e5ed4bfa4` |
| Addendum blob / SHA-256 | `bc07a675…` / `15efd88c61b8ed1b17f965c57e45287125ed46ac9cc321f8e1b253c04cc58e1b` |
| Harness blob / SHA-256 | `5502dc1e…` / `9b995808b7ba78e74f98d93a92ae1001062fe9c705aeb214a96953b35ba1cfb7` |
| Repository at execution | `36ba030f2abefacb57c1d95df554f148aa410ebe`, clean (recorded in `preflight.json`) |
| Authorization | owner-issued in the Claude Code session (answer "签发，执行" to the authorization question); `AuthorizedAtUtc 2026-10-29T01:16:02Z`.  `authorization.md` (SHA-256 `357380c1cab0b0a23d6e99016e355c83bca9e54b303c2994a90b46e3692d4fc4`, outside git) was written by the implementing agent from the owner-approved `authorization-draft.md`; the session transcript is the primary record |
| Host | Windows 11 Pro 10.0.26300; PowerShell 7.6.9; Python 3.14.6 |
| Evidence path | `D:\DevRelay-gate\G0.4-2026-10-29\evidence` (outside git) |

## 2. Counters

| Counter | Value |
| --- | --- |
| provisioning OpenCode starts | 1 |
| proof OpenCode starts/restarts | 0 |
| loopback `GET /doc` | 1 |
| other HTTP | 0 |
| provider/model calls | 0 |
| harness external connections | 0 |
| observed external connections (sampled, process tree) | 0 |
| retries | 0 |

## 3. Cases A and B (binding and capture)

* **A — `TARGET_BOUND`.**  Package `opencode-ai` 1.18.11, declared bin
  `./bin/opencode.exe`; target and listener executable identical: canonical path
  `…\npm\node_modules\opencode-ai\bin\opencode.exe`, SHA-256 `578d7eb3…cc35`, 174,182,280
  bytes, `LastWriteTimeUtc 2026-08-02T15:22:01Z` ≤ creation, NTFS file id
  `0x…010000001e64be`.  Exactly one LISTEN on `127.0.0.1:47231` (PID 58772, parent = harness
  PID 60208, created `2026-10-29T01:16:14.327Z` ≥ authorization).  Endpoint
  `http://127.0.0.1:47231` from `load_wiring_config`.
* **B — B1 and B2 pass.**  `GET /doc` connected `127.0.0.1:58739 → 127.0.0.1:47231`;
  `HTTP/1.1 200 OK`, `application/json`, `Content-Length` 478,747 = body bytes; body SHA-256
  `c3a9f94af0c3324d97b482b14c692e810ce7ccac3136319ba46334de972b4cf1`; OpenAPI 3.1.0,
  162 paths, 188 operations, 472 component schemas.  Post-snapshot
  (`2026-10-29T01:16:24.72Z`) equals pre-snapshot (`01:16:20.40Z`) in PID, creation time,
  path, hash, size, last-write time, file id and listener uniqueness →
  `SAME_BOUND_TARGET`.
* Teardown stopped PID 58772; one descendant (56816) was recorded in `teardown.json` and
  not signalled; port free after.  Isolated home received 5 files; the server log shows
  config loaded only from `opencode-home`.  *Post-run observation, outside the evidence
  set:* a process query a few minutes later found no PID 56816.
* External connections were **sampled** at the pre/post instants only (none seen); this
  is not a packet capture.
* `/doc` `info.version` = `1.0.0` carries no build identity, so the oracle §8.10
  corroboration is **absent**, not confirming; identity rests on the local chain.
* Residual (pre-accepted): pre→post interval 4.3 s, including the GET and the byte-wise body
  hash.

## 4. Cases C–H (offline, on the captured schema only)

* **C — session status.**  `GET /session/status` returns a map of `SessionStatus`
  (`idle` | `busy` | `retry{attempt,message,next}`); v2 `GET /api/session/active` returns
  `{ses…: {type: running}}`.  Both are **SESSION_LEVEL_ONLY**.
* **D — synchronous message route.**  `POST /session/{sessionID}/message` accepts an
  optional client-supplied `messageID` (`^msg`) and returns `{info: AssistantMessage,
  parts}`.  `AssistantMessage` carries `id`, `parentID` (`^msg`, no description),
  `time{created, completed?}`, `finish` (free string).  No operation/request/job field.
* **E — `prompt_async`.**  `POST /session/{sessionID}/prompt_async` takes the same body
  (optional client `messageID`) and returns **204 with no body**: no server-issued
  identifier.  v2 `POST /api/session/{sessionID}/prompt` ("Durably admit one session
  input …") returns `SessionInputAdmitted{id ^msg_, admittedSeq, promotedSeq?, delivery,
  timeCreated}`.
* **F — event surfaces.**  `/event`, `/global/event`, `/api/event` are SSE.  v2 durable
  history `GET /api/session/{sessionID}/history?after=` and `/api/session/{id}/event?after=`
  carry `SessionNextPromptAdmitted` / `SessionNextPrompted` (`messageID`) and
  `SessionNextStepStarted/Ended/Failed` (`assistantMessageID`).  **No step event carries the
  admitted input `messageID`**, so input → step linkage is only by event `seq` order.
  `requestID` / `callID` appear only for permission/question/tool sub-events, not for a
  prompt operation.
* **G — identifier traceability.**

  | Candidate | Operation-specific | OpenCode-owned | Post-call observable | Read-only resolvable to its state/result | No order/timestamp heuristic |
  | --- | --- | --- | --- | --- | --- |
  | v1 client `messageID` + `AssistantMessage.parentID` (also used by `POST /session/{id}/command` and `/shell`) | plausible (client-chosen per submission) | client-supplied, OpenCode-persisted | yes (`GET /session/{id}/message/{messageID}`) | **unresolved**: no lookup by operation; only list + filter on `parentID`; `parentID` semantics undocumented; several assistant messages may share one parent and no operation-level completion field exists | yes for the link itself |
  | v2 `SessionInputAdmitted.id` / `admittedSeq` | plausible | yes | yes (`GET /api/session/{id}/message/{messageID}` returns the user input) | **no** operation state on the input; result linkage only via ordered history | **no** — needs `seq` order |
  | session id, `SessionStatus`, `SessionActive` | no | yes | yes | session-level only | — |
  | `requestID` (permission/question), `callID` (tool) | sub-operation, not a prompt operation | yes | partly | not a prompt-operation handle | — |
  | `IntegrationAttempt` `attemptID` | integration connect flow, not a model operation | yes | yes | out of question scope | — |
* **H — completeness sweep.**  All 188 operations and 472 schemas were inventoried
  mechanically (`schema-inventory.json`, 40 identifier-like field names) and the
  routes/schemas above were read in full.  Additional routes and their disposition:

  | Route | Disposition |
  | --- | --- |
  | `POST /api/session/{id}/wait` | waits for the session agent loop to become idle — session-level only (see `wait_idle` control) |
  | `POST /sync/history` | seq-ordered sync event history (`evt_`, `aggregate_id`, `seq`) — order-based, same class as v2 history |
  | `POST /session/{id}/command`, `POST /session/{id}/shell` | same client-`messageID` / `AssistantMessage` mechanism as D — folded into the v1 candidate row |
  | `GET /tui/control/next` | TUI control request queue — not an operation handle |
  | `POST /experimental/session/{id}/background` | returns a boolean — no identifier |

  No other operation/request/task/job/run/prompt handle with a lookup route was found.

* **`wait_idle` control (oracle §16).**  The platform's wait/status surfaces —
  `POST /api/session/{id}/wait` ("Wait for a session agent loop to become idle"),
  `GET /session/status` and `GET /api/session/active` — are **session-level only**.  An
  idle session does not prove that a specific submission completed.
* **DevRelay-local-id control (oracle §16).**  DevRelay `call_ids`, `reply_boundary` and
  `in_flight_turn` are DevRelay-local; `assistant_message_ids` are remote message ids.
  None appears in, or is resolvable through, the captured OpenCode schema as an operation
  handle; none is a qualifying remote per-operation pending handle.

## 5. Candidate conclusion

* Not **PASS-B**: no candidate establishes every qualifying dimension (oracle §12); the v1
  `messageID`/`parentID` chain leaves read-only resolvability of the operation's
  pending/result state unresolved, and v2 linkage depends on event order.
* Not **PASS-A**: absence cannot be concluded (oracle §13) because the v1 chain is a
  candidate whose disqualification rests on undocumented semantics, not on the schema.
* Therefore **`EVIDENCE_INSUFFICIENT`**, reason `CANDIDATE_IDENTIFIER_SEMANTICS_UNRESOLVED`
  → **CANDIDATE FAIL / P4 UNPROVEN**.  Consequence (oracle §14–§15): E31 stays FROZEN /
  report-only; `reply_pending` stays report-only; no capability changes.

Notable for a future, separately reviewed design: the 1.18.11 API now contains a v2
"durable admission" surface (`/api/session/{id}/prompt`, `admittedSeq`, durable history).
This proof does not evaluate it as a capability.

## 6. Evidence file hashes (outside git)

`config.json 8216fc6a…93cf`, `doc.json c3a9f94a…4cf1`, `get.json 5f9503f3…9e99`,
`post.json fe3eb946…45e5`, `pre.json 87eef298…8a86`, `preflight.json c8753b1b…4f77`,
`provisioning.json cf11ea73…1391`, `result.json 254b8e0a…3122`,
`schema-inventory.json 9e80cf76…871d`, `statics.json 8363a837…7f77`,
`teardown.json 0d25e8f4…25e3`, `server-stdout.log 23868454…be` (two lines: unsecured
warning, listening line), `server-stderr.log` empty.
