# DevRelay v0.3-E — G0.4 / P4 rerun: provisioning addendum (revision 4 composite)

**Status: DEFINITION CANDIDATE — NOT REVIEWED, NOT FROZEN, NOT AUTHORIZED, NOT RUN.**
This file contains no G0.4 result.  `adopt_completed_turn` remains disabled.

## 0. Current status (supersedes the stale header of the revision-3 oracle)

| Item | Value |
| --- | --- |
| Revision-3 oracle | `docs/v0.3/V03E_G0_4_API_INSPECTION_ORACLE.md`, git blob `34b0f5e8a81c27805a082fe782137b2e23a05ce0`, committed-blob SHA-256 `b0c34fa19c3e639b5637d74d49e1c9c357b7db914ee1becf70229f3e5ed4bfa4`; approved (P0/P1/P2 = 0) and executed once |
| Prior G0.4 result | **AUTHORITATIVE FAIL / P4 UNPROVEN** (`V03E_G0_4_API_INSPECTION_PROOF.md`; no endpoint configured, 0 `GET /doc`).  It is final and is not rewritten or superseded |
| This round | a **new** G0.4 execution under revision 3 **plus this addendum** ("revision 4 composite"), triggered by the owner's 2026-10-29 decision to have the implementing agent start the npm `opencode-ai` 1.18.11 server |
| Re-review of revision 3 for this round | `REQUEST_CHANGES` (P0 = 0, P1 = 1, P2 = 4) at HEAD `9746a9e`; this addendum answers those five findings |
| Repository identity | re-pinned by the execution authorization (commit on `main`, package version) |

Revision 3 is **not edited**.  Its semantics (§3–§7, §9–§16, §19–§24) apply unchanged.
This addendum replaces revision-3 text **only** where a section below says so.

## 1. Changed budget (replaces revision 3 §1 "Budget" row and §8 part B "no start" bullets)

Two separate counters:

| Phase | Allowed |
| --- | --- |
| **Provisioning** (after STEP 2, before STEP 3) | exactly **1** OpenCode start, by the frozen harness, of the declared-bin executable; local OS-metadata polling for the listener; **0** HTTP by the harness |
| **Proof** (STEP 1 – STEP 5, excluding PROVISION) | **0** OpenCode starts/restarts; **at most 1** loopback `GET /doc`; **0** provider/model calls; **0** harness-issued external network connections |
| **Teardown** (after STEP 5) | stop exactly the provisioned PID; no other process is signalled |

Server-initiated background traffic is not a harness request.  It is minimized by §2 and
observed by §3; it is reported as `provisioning_observed_external_connections`, never
hidden, and it does not convert into a proof request.

## 2. Provisioning definition (new)

1. Performed by the frozen harness `V03E_G0_4_RERUN_HARNESS.ps1`, run once by the
   implementing agent after the owner's authorization is recorded.
2. Pre-check: **no listener** on port `P` in any address family; otherwise
   `PROVISION_PORT_BUSY` → stop with **0 starts, 0 GETs** (semantic FAIL; not retryable).
3. Command (no shell wrapper, no npm shim):
   `<declared-bin>\opencode.exe serve --hostname 127.0.0.1 --port <P>`, working directory
   = the authorized gate workspace root.
4. Isolation: `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME`, `XDG_STATE_HOME` point
   into `<evidence>\opencode-home\`; the child environment removes
   `OPENCODE_SERVER_PASSWORD`, `OPENCODE_SERVER_USERNAME`, `OPENCODE_CONFIG*`,
   `OPENCODE_API_KEY` and `OPENCODE_AUTH_CONTENT`, and sets `OPENCODE_DISABLE_AUTOUPDATE`,
   `OPENCODE_DISABLE_MODELS_FETCH`, `OPENCODE_DISABLE_DEFAULT_PLUGINS`,
   `OPENCODE_DISABLE_LSP_DOWNLOAD`, `OPENCODE_DISABLE_SHARE`,
   `OPENCODE_DISABLE_EXTERNAL_SKILLS`, `OPENCODE_DISABLE_CLAUDE_CODE` and
   `OPENCODE_DISABLE_PROJECT_CONFIG` to `1`.  These names were found by static string
   inspection of the pinned binary; their effect is **not** assumed — isolation is
   evidenced by files appearing under `opencode-home` and is otherwise a stated residual.
5. Authentication: no server password is set, so `GET /doc` sends **no** credential.  A
   401/403 is recorded as-is (case B1 fails); no credential is retried.
6. Readiness: poll local listening-socket metadata for `127.0.0.1:P` (≤ 60 s).  **No HTTP
   readiness probe.**  Timeout → `PROVISION_NO_LISTENER` → semantic FAIL, 0 GETs.
7. The provisioning record (started PID, harness PID, start command, start time
   UTC, environment variable **names** set/removed) is frozen before STEP 3.

## 3. Additional binding requirements (extend revision 3 §8.1–§8.8, §17.1, §18)

* **Provenance (P1):** listener PID == started PID; listener `ParentProcessId` == harness
  PID; listener `CreationDate` ≥ the authorization timestamp.  Any mismatch →
  `TARGET_IDENTITY_UNRESOLVED` → `EVIDENCE_INSUFFICIENT`, no GET.
* **Literal destination (P2-1):** the configured endpoint must be exactly
  `http://127.0.0.1:<P>` (literal IPv4, no hostname, no path).  The GET connects to the
  frozen `IPAddress 127.0.0.1` / port `P` with no name resolution; the client socket's
  actual local and remote endpoint are recorded and must equal `127.0.0.1:P`.
* **Listener recheck after GET (P2-2):** §8.8 additionally re-runs the §8.3 rule (exactly
  one LISTEN on port `P`, on `127.0.0.1`, none on `0.0.0.0`, `::`, `::1`).
* **File identity (P2-3):** both snapshots record executable size, `LastWriteTimeUtc` and
  the NTFS file id (`fsutil file queryfileid`); equality is required, and
  `LastWriteTimeUtc` ≤ listener `CreationDate`.  If the file id cannot be read, that field
  is recorded as unavailable and listed as a residual (it does not replace hash/path
  equality).  Residual stated: hashing the path cannot prove the mapped image equals the
  file on disk if the file were swapped and restored between snapshots.
* **Expected statics:** declared-bin SHA-256
  `578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35`, size 174,182,280
  bytes.  Any difference → `TARGET_INSTANCE_MISMATCH`, no substitution.
* **Desktop build:** the OpenCode desktop build / `opencode-cli` 2.1.1 is never the
  configured endpoint, is never signalled, and must hold no listener on port `P`.

## 4. Execution order (replaces revision 3 §8.9)

PREFLIGHT → STEP 1 statics → STEP 2 configured endpoint → PROVISION → STEP 3
pre-snapshot + `TARGET_BOUND` → STEP 4 one `GET /doc` iff bound → STEP 5 post-snapshot
(always, once the GET was attempted) → STEP 6 mechanical schema inventory (offline, no
HTTP) → TEARDOWN → STEP 6 C–H case analysis in the proof document.

* **PREFLIGHT** (not a proof action): evidence directory must not exist;
  `-AuthorizedAtUtc` must be ISO-8601 ending in `Z` (Kind = UTC); port ≠ 45278; repository
  tree clean; the oracle, this addendum and the harness are committed and their blob ids
  and committed-blob SHA-256 are recorded with HEAD and `$PSVersionTable`.  A preflight
  refusal performs no read of the target, no start and no HTTP, so it consumes nothing.
* **STEP 1** verifies package name/version, declared bin `./bin/opencode.exe`, size and
  SHA-256 **before** anything is executed; mismatch → 0 starts.
* **STEP 2** reads the endpoint with the accepted runtime loader
  `load_wiring_config(<workspace root>)`; the call must exit 0 and print exactly one
  line equal to `http://127.0.0.1:<P>`; otherwise 0 starts.
* **STEP 4** failures (connect refused, reset, timeout, no headers, `Content-Length`
  mismatch, malformed or truncated chunking, body > 64 MiB, non-200, non-JSON, no `paths`)
  are **semantic** case-B1 failures, never harness defects.  The read ends on
  `Content-Length` or the zero-size chunk terminator, not only on connection close.
* **TEARDOWN** guards every action separately; `result.json` is written in its own guarded
  block.  Descendant PIDs are recorded before the stop; only the provisioned PID is
  stopped (a descendant left running is reported, not signalled).
* **STEP 6** — the harness produces the mechanical schema inventory (path/route/schema
  counts, operation ids, candidate identifier field names).  The C–H classification is
  then written in the proof document under revision 3 §9–§13 and reviewed independently;
  `result.json` therefore carries `final_verdict = EVIDENCE_INSUFFICIENT` on a semantic
  failure, `awaiting = HARNESS_DEFECT_REVIEW` on a `HARNESS_DEFECT` (the independent
  reviewer decides), or `awaiting = STEP6_CASE_ANALYSIS_C_TO_H` otherwise.  STEP 4
  failures record the exception type, message and inner type; evidence writes after the
  GET are guarded so STEP 5 always runs.  The harness pins
  `$PSNativeCommandUseErrorActionPreference = $false`.

### 4.1 Reason mapping (all under `EVIDENCE_INSUFFICIENT`, revision 3 §10 / §17.1)

| Harness reason | Revision-3 reason |
| --- | --- |
| `TARGET_INSTANCE_MISMATCH` | wrong package/version/bin/executable/hash |
| `ENDPOINT_NOT_LITERAL_LOOPBACK` | non-loopback endpoint (§8.2) |
| `PROVISION_PORT_BUSY` | ambiguous listener (§8.3) |
| `PROVISION_NO_LISTENER` | no listener at the resolved address/port |
| `TARGET_IDENTITY_AMBIGUOUS` / `TARGET_IDENTITY_UNRESOLVED` | as §10 |
| `TARGET_INSTANCE_CHANGED` / `DESTINATION_MISMATCH` | post-request continuity (§8.8) |
| `SCHEMA_UNAVAILABLE: …` | case B1 failure |
| `HARNESS_DEFECT: …` | harness-invalid only within revision 3 §17's narrow boundary; the independent reviewer decides |

### 4.2 Residuals (stated, not hidden)

* External connections are **sampled** at the pre- and post-snapshot instants for the
  provisioned process and its descendants; this is not a full packet capture.
* `Canon` normalizes the final path and rejects a reparse-point executable, but does not
  resolve parent-directory reparse points or 8.3 short names.
* The NTFS file id comes from `fsutil file queryfileid`; if unavailable, the fsutil
  output is logged and "unavailable" on both sides is a recorded residual, not a proof of
  identity.

## 5. Evidence (extends revision 3 §18)

Outside git, under the authorized evidence path: `authorization.md`, `provisioning.json`,
`statics.json`, `pre.json`, `get.json` (status, media type, body SHA-256, byte count,
actual socket endpoints), `post.json`, `teardown.json`, `result.json` (all counters and
verdicts), `doc.json` (raw schema), `schema-inventory.json`, server stdout/stderr logs.
Committed to git: a redacted proof document with hashes, counters, verdicts and the C–H
analysis; no tokens, no raw provider bodies, no user content.

## 6. Unchanged

Question, definitions, PASS-A/PASS-B/FAIL semantics, case matrix A–H, no-probe-shopping,
report-only policy, claim boundaries.  A failed round stays failed; no second GET, no
second start, no alternate port or server.
