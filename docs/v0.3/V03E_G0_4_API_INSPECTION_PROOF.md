# DevRelay v0.3-E — G0.4 / P4 installed-API inspection proof

**Status at execution: CANDIDATE FAIL / P4 UNPROVEN — recorded by the executing agent, never
self-approved.  Current authoritative status: `G0.4 / P4 = AUTHORITATIVE FAIL / P4 UNPROVEN`**
(the independent failed-proof review issued *APPROVE V0.3-E G0.4 FAILED PROOF*, P0 = 0,
P1 = 0, P2 = 0, failure type **TYPE 3 — SEMANTIC ENVIRONMENT / CONFIGURATION RESULT** — see
the review-record block below).

> **Independent review outcome (recorded afterwards; this document's observed execution
> facts are unchanged):** the independent failed-proof review issued **APPROVE V0.3-E G0.4
> FAILED PROOF** with **P0 = 0, P1 = 0, P2 = 0** and failure classification **TYPE 3 —
> SEMANTIC ENVIRONMENT / CONFIGURATION RESULT**, which makes this round an authoritative
> **G0.4 / P4 = FAIL / P4 UNPROVEN**.  The execution-result artifact as first committed at
> `9a22528` had committed-blob SHA-256
> `62d033f98108d05c32d885af27e9ce6d90f454137c8caa71b7d03ec4b059060d`; only this
> review-record block and the status wording above were added afterwards, and none of the
> observed execution facts, counters or outcomes below was altered.
>
> A rerun of this execution is **NOT AUTHORIZED**: setting an endpoint and calling it the
> same proof run, repairing the configuration and rerunning under the old authorization,
> starting a server and continuing, or replacing the failed evidence are all prohibited.
> The failed run is final.  A future G0.4 execution after a deliberately changed
> configuration would be a **NEW execution** requiring **new external authorization** under
> the same immutable oracle (unless changed circumstances require a separately reviewed new
> oracle), and it must not rewrite or supersede this failed run.
>
> Non-blocking independent P3 limitations: (1) the zero-HTTP / zero-process-enumeration
> absence is not independently reconstructable from committed evidence beyond the coherent
> failure path and the absence of captured schema material; (2) the absolute
> environment-specific paths in this evidence are legitimate derived evidence and remain
> labelled environment-specific; (3) the residual TOCTOU note stays historical/non-operative
> here because no pre/post responder snapshot pair existed in this failed run.  None of these
> is a proof blocker.

This document is the execution evidence for the separately authorized G0.4 round.  It
records the single semantic execution of the fixed A–H plan against the immutable
revision-3 oracle.  **P4 is not proven, G0.4 did not pass, and no capability changed.**

## 1. Identity and authorization

| Item | Value |
| --- | --- |
| Repository HEAD at execution | `d4fb02b4213ace437a4eb4488f5818772c39cbf8` |
| Branch | `v0.3-e-recovery-reconciliation` |
| Package version / public tags | `0.1.0` / `v0.1.0` only; no upstream configured |
| Worktree at execution start | clean |
| Immutable oracle commit | `d4fb02b4213ace437a4eb4488f5818772c39cbf8` |
| Immutable oracle artifact | `docs/v0.3/V03E_G0_4_API_INSPECTION_ORACLE.md` |
| Oracle committed-blob SHA-256 (verified before execution) | `b0c34fa19c3e639b5637d74d49e1c9c357b7db914ee1becf70229f3e5ed4bfa4` |
| Definition decision | **APPROVE V0.3-E G0.4 PROOF DEFINITION REVISION 3** (P0 = 0, P1 = 0, P2 = 0) |
| Execution authorization | separately issued by the product owner after that approval |
| Authoritative proof state at execution | `G0.1 / P7 = PASS / CLOSED`; `G0.2 = PASS / CLOSED`; `G0.3 / P5 = PASS / CLOSED`; `G0.4 = NOT RUN / DEFINITION APPROVED / EXECUTION AUTHORIZED`; `G0.5 / G1 / G2 = NOT RUN` |
| Platform proof gate | `PARTIALLY EXECUTED / NOT COMPLETE` |
| mandatory-core implementation | **NOT AUTHORIZED** |
| `adopt_completed_turn` | **DISABLED** |

The oracle was treated as immutable: it was not edited, its criteria were not amended, and
no observed result was reinterpreted by changing PASS-A, PASS-B, FAIL semantics, the target
definition, the durability definition, the case matrix, the binding rules, the evidence
threshold or the no-probe-shopping rules.  Its committed-blob SHA-256 was re-verified after
execution and is unchanged (section 15).

## 2. Fixed execution order and the point at which it stopped

The accepted six-step order was executed without reordering:

| Step | Content | Result |
| --- | --- | --- |
| STEP 1 | derive installed target package/bin identity | **COMPLETED** (section 3) |
| STEP 2 | resolve the configured DevRelay endpoint to the concrete loopback destination | **FAILED — no endpoint is configured** (section 4) |
| STEP 3 | pre-request responder binding and frozen identity snapshot | **NOT ESTABLISHED** — `TARGET_NOT_BOUND` (section 6) |
| STEP 4 | exactly one local loopback `GET /doc` iff `TARGET_BOUND` | **NOT EXECUTED — 0 GETs issued** (section 7) |
| STEP 5 | mandatory post-request responder-continuity snapshot | **NOT APPLICABLE** — no request was issued (section 8) |
| STEP 6 | offline cases C–H against the single captured schema | **NOT EXECUTED** — no captured schema exists (sections 9–10) |

Case A did not establish `TARGET_BOUND`, so the precommitted failure path applied: **no
`GET /doc` was issued**, cases B–H were not executed, and no substitute or historical
evidence was used.

## 3. STEP 1 — installed target identity (local read-only metadata)

Package metadata was read from the installed npm package; no executable was started, and
nothing was written.

| Field | Value |
| --- | --- |
| Package name | `opencode-ai` |
| Package version | `1.18.11` |
| Declared bin | `./bin/opencode.exe` |
| Package root | `C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai` |
| Package metadata path | `…\opencode-ai\package.json` |
| Declared-bin path (resolved) | `…\opencode-ai\bin\opencode.exe` |
| Canonical target executable path | `C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe` |
| Target executable exists | yes |
| Target executable size | 174,182,280 bytes |
| Target executable filesystem mtime | 2026-08-02T15:22:01Z |
| **Target executable SHA-256** | `578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35` |

Derived rather than hard-coded: package root, package metadata path, declared-bin path,
canonical target executable path and the target executable hash.  The declared-bin path
resolved to the canonical path without any symlink/junction/reparse divergence.

This static identity is independent of the endpoint failure and stays valid as evidence for
any future authorized execution in this environment.

## 4. STEP 2 — configured endpoint: no endpoint is configured

The endpoint may only come from the accepted DevRelay configuration, and DevRelay never
discovers servers by scanning ports or processes (`src/devrelay/config.py`,
`OpenCodeConfig`: *"The endpoint is explicit by design: DevRelay never scans ports or
processes"*).

| Resolution check | Result |
| --- | --- |
| Configuration source | workspace `.devrelay/config.yaml` (gitignored runtime wiring) |
| `opencode.base_url` in that file | `""` (empty — *"disabled until base_url is set"*) |
| Accepted loader result (`devrelay.config.load_wiring_config('.')`) | `opencode.base_url = ''`, `opencode.configured = False` |
| Environment override for the endpoint | none exists — the only `DEVRELAY_OPENCODE_*` variable is `DEVRELAY_OPENCODE_TOKEN` (token only) |
| Profiles that could supply wiring | `.devrelay/profiles/` is empty; profile files may not set `opencode` wiring |
| Packaged default policy | `src/devrelay/profiles/default.yaml` contains no `opencode`/`base_url` wiring |
| Other state | `.devrelay/state.json` = `{}` |
| Accepted runtime behaviour when unset | `devrelay.opencode` raises *"opencode.base_url is not configured in .devrelay/config.yaml; DevRelay never discovers servers by scanning ports or processes"* |

**No endpoint was discovered, no port was scanned, no process was enumerated, no server was
selected merely because it was running, and no alternate endpoint was tried after the
failure.**  Because endpoint identity is missing, no concrete loopback destination, no
listener and no responder could be bound.

Concrete destination: **NOT ESTABLISHED**.  Loopback-only check: **NOT EVALUABLE**
(nothing to resolve).  Address family: **NOT ESTABLISHED** (nothing to pin, so no family was
chosen arbitrarily).

## 5. Failure reason (precommitted vocabulary)

The binding reason is **`TARGET_IDENTITY_UNRESOLVED`** — a mandatory identity field (here the
configured endpoint, the first element of the binding chain) could not be obtained, so no
downstream identity check could be evaluated.

Final semantic outcome: **`EVIDENCE_INSUFFICIENT`** (exactly one of the four precommitted
outcomes; no fifth verdict was invented, and `TARGET_IDENTITY_UNRESOLVED` is a
reason/subclassification under it, never a verdict of its own).

## 6. Case A — findings

| # | Required finding | Status |
| --- | --- | --- |
| **A1** | installed package name == `opencode-ai` | **PASS** (section 3) |
| **A2** | installed package version == `1.18.11` | **PASS** (section 3) |
| **A3** | declared bin `./bin/opencode.exe` resolves to a canonical target executable path | **PASS** (section 3) |
| **A4** | configured DevRelay endpoint resolves to a loopback destination only | **NOT EVALUABLE** — no configured endpoint |
| **A5** | exact concrete endpoint has an unambiguous single listener | **NOT EVALUABLE** — no concrete destination |
| **A6** | listener PID identified | **NOT EVALUABLE** — no concrete destination |
| **A7** | listener canonical executable == target declared-bin executable | **NOT EVALUABLE** — no listener |
| **A8** | listener executable SHA-256 == target executable SHA-256 | **NOT EVALUABLE** — no listener (target-side hash recorded) |
| **A9** | listener process creation/start identity obtained | **NOT EVALUABLE** — no listener |
| **A10** | pre-request responder snapshot frozen and `TARGET_BOUND` established | **FAILED** — `TARGET_NOT_BOUND` |

**Case A verdict: CASE FAIL / `EVIDENCE_INSUFFICIENT` (`TARGET_IDENTITY_UNRESOLVED`).**

Pre-request identity tuple (target statics recorded, responder fields not obtainable):

| Pre-request element | Value |
| --- | --- |
| package name / version | `opencode-ai` / `1.18.11` |
| package root | `C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai` |
| declared bin | `./bin/opencode.exe` |
| canonical target executable | `…\opencode-ai\bin\opencode.exe` |
| target executable SHA-256 | `578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35` |
| configured endpoint | **absent** (empty `opencode.base_url`) |
| resolved concrete loopback address / port / family | **NOT ESTABLISHED** |
| listener PID / canonical `ExecutablePath` / executable SHA-256 / creation identity | **NOT OBTAINED** (no listener lookup was performed, because no destination existed and discovery is prohibited) |
| pre-binding verdict | **`TARGET_NOT_BOUND`** |

No diagnostic or exploratory binding was attempted after the failure: no rerun of Case A, no
waiting for another server, no configuration change, no second address family.

## 7. Case B — the single `GET /doc`

| Item | Value |
| --- | --- |
| Precondition (Case A == `TARGET_BOUND`) | **NOT MET** |
| Loopback HTTP requests issued | **0** |
| `GET /doc` calls | **0** |
| HTTP status / media type / response-byte count / schema SHA-256 | **NOT OBTAINED** (no request was permitted) |
| Requests to `/session/status`, `/event`, `/global/event`, health/version/status, POSTs, `prompt_async`, message calls, interrupts | **0 — none issued** |
| Historical `/doc` substitution | **none** (prohibited, and not used) |
| Redirect handling | not applicable — no request was issued |

## 8. STEP 5 — post-request continuity snapshot

**NOT APPLICABLE.**  No request was issued, so there is no post-request snapshot to take and
no continuity comparison to make.  Continuity verdict: **NOT ESTABLISHED — not reached**
(never `SAME_BOUND_TARGET`, and no `TARGET_INSTANCE_CHANGED` was observed because no
before/after pair exists).  No rebinding, no retry, no waiting for a listener, and no second
GET occurred.

## 9. Case B schema condition and cases C–H

Case B was not executed (precondition unmet), so **B1** (`SCHEMA_AVAILABLE`) and **B2**
(`POST_REQUEST_TARGET_CONTINUITY == SAME_BOUND_TARGET`) are both **NOT EVALUATED**.

Cases C–H are offline analyses of the single captured schema; no schema was captured, so:

| Case | Status |
| --- | --- |
| G0.4-C — session status (`/session/status`, `SessionStatus`) | **NOT EXECUTED** — no captured schema |
| G0.4-D — synchronous message route (`POST /session/{id}/message`) | **NOT EXECUTED** — no captured schema |
| G0.4-E — `prompt_async` route | **NOT EXECUTED** — no captured schema |
| G0.4-F — event surfaces (`/event`, `/global/event`) | **NOT EXECUTED** — no captured schema |
| G0.4-G — identifier traceability | **NOT EXECUTED** — no candidate identifiers and no captured route/schema graph |
| G0.4-H — completeness / negative control | **NOT PERFORMED** — the absence conclusion requires the complete captured schema sweep, which does not exist |

Candidate-identifier matrix: **NOT PRODUCED** (no candidates observed).  Complete-schema
search result: **NOT PERFORMED**.  No absence claim is made, and none may be derived from
this round.

## 10. Final outcome and capability consequence

**Final semantic outcome: `EVIDENCE_INSUFFICIENT` — reason `TARGET_IDENTITY_UNRESOLVED`
(configured endpoint absent) → CANDIDATE FAIL / P4 UNPROVEN.**

Consequence (precommitted and unchanged):

* `E31` remains **FROZEN / report-only**; `reply_pending` remains **report-only**;
* no pending capability is enabled, and none is removed (v0.3-E has none);
* mandatory-core authorization rules do not change; the `adopt_completed_turn` gate does not
  change; `mark_unrecoverable` remains available;
* G0.4 stays failed/unproven; any stronger future pending capability remains unavailable;
* **no degraded implementation mode is invented.**

G0.4 status recorded by the executor: `CANDIDATE FAIL / P4 UNPROVEN` (row `E37` updated
accordingly).  No authoritative status is claimed.

## 11. What this round does and does not establish

* **Establishes:** in the accepted environment *as configured at execution time*, no OpenCode
  endpoint is configured for DevRelay, so no target instance could be bound by the
  precommitted read-only binding chain and the single permitted probe could not be issued
  without violating the no-discovery rule.  It also records the installed target's static
  identity and executable hash.
* **Does not establish:** that the installed OpenCode 1.18.11 API exposes no durable
  per-operation handle; nothing about the schema, routes or identifiers; nothing about which
  OpenCode processes or listeners may exist on this host (no enumeration was performed); and
  nothing that could substitute for a future authorized capture.
* The historical session-level-only knowledge remains **historical review knowledge** and is
  **not** promoted to a formal proof by this round.

## 12. Activity counters (exact)

| Counter | Count | Bound | Status |
| --- | --- | --- | --- |
| provider/model inference calls | 0 | = 0 | OK |
| model turns | 0 | = 0 | OK |
| external network requests | 0 | = 0 | OK |
| OpenCode starts | 0 | = 0 | OK |
| OpenCode restarts | 0 | = 0 | OK |
| loopback HTTP requests | 0 | ≤ 1 | OK |
| `GET /doc` calls | 0 | ≤ 1 | OK |
| other HTTP requests | 0 | = 0 | OK |

OpenCode processes were neither started, restarted, stopped nor signalled.  No prompt was
submitted, no `prompt_async` call was made, no message was posted, no event stream was
subscribed, no session was interrupted and no OpenCode state was mutated.

## 13. Privacy and persistence

No credentials, tokens, raw prompts, responses containing user content, reasoning or provider
secrets are recorded here — and none were obtained: the run produced no HTTP response body at
all.  The access token is environment-only (`DEVRELAY_OPENCODE_TOKEN`) and was never read or
needed.  The workspace configuration was consulted read-only; only the fact that its
`opencode.base_url` is empty is recorded, with no other configuration values reproduced.  No
raw `/doc` material exists to persist.

## 14. Execution discipline

* Exactly **one** semantic execution of the fixed A–H plan: no rerun, no probe shopping, no
  rerun to obtain a listener, a stable process, a matching installation, a different address
  family, a usable `/doc` or a desired schema result.
* The precommitted failure path was followed: no GET, no cases B–H, no substitute evidence,
  no historical `/doc` substitution.
* The immutable oracle was not modified, and no criterion was reinterpreted.
* No runtime source, test, dependency, version, configuration or OpenCode process was
  changed; no provider/model was invoked; no network request of any kind was made.
* Evidence provenance (read-only operations only): `git rev-parse`/`git show` for identity
  and oracle hashing; `sha256sum` for committed-blob hashing; the accepted configuration
  loader for endpoint resolution; Python `json`/`hashlib`/`pathlib` for the installed
  package metadata and target executable hash.

## 15. P3 execution notes and limitations

* **Oracle immutability verified after execution:** the oracle's committed-blob SHA-256 is
  still `b0c34fa19c3e639b5637d74d49e1c9c357b7db914ee1becf70229f3e5ed4bfa4`; the file was not
  touched by this round.
* **Residual TOCTOU assumption (not exercised):** the binding design assumes no transient
  foreign process can take over the exact bound address/port, serve the captured response and
  restore the original process undetected between the two local identity snapshots.  This
  round produced no snapshot pair, so the assumption was neither tested nor relied upon.
* **Concrete-destination rule applied:** the destination must be the one the actual proof HTTP
  client would use, established deterministically; since no destination could be established
  at all, the run failed closed — no probe was issued.
* **Hash convention:** authoritative document/oracle hashes use committed Git blob bytes, not
  platform-normalized working-tree bytes (revision-3 oracle convention).
* **Limitation:** the outcome is a configuration-state finding for this environment at this
  moment.  Configuring an endpoint later does not retroactively change this result, and a
  future G0.4 execution would require a new authorization and a fresh single execution under
  the same immutable oracle.
* **No self-approval:** this CANDIDATE FAIL is recorded by the executing agent; the
  authoritative G0.4/P4 status may only be produced by an independent reviewer.

## 16. Non-claims

This document records an execution result; it grants nothing.  It does not make P4 proven,
does not make G0.4 pass, does not enable pending adoption, does not change
`reply_pending` behaviour, does not authorize implementation, adoption, retry, resubmission
or any capability change, and does not authorize G0.5, G1 or G2.
