# DevRelay backlog and carried-forward status

Items recorded here are **not** part of any completed stage. Nothing in this file
authorizes code changes; each item names its own scope and owner stage.

## 1. v0.2-C real Codex smoke — PENDING (externally blocked)

| Field | Value |
| --- | --- |
| Status | **PENDING** — not passed, not waived |
| Candidate | `4790ca36edb1957ebc5e8df073a2be4ec2bb4459` (frozen v0.2-C baseline) |
| Consumed | **exactly one** real Codex call (no retry authorized) |
| Verified in that run | reviewed schema SHA-256 matched exactly; the real endpoint accepted the annotation-free schema; the earlier `invalid_json_schema` regression is **VERIFIED FIXED** |
| Still unverified | end-to-end structured delivery: `--output-last-message` result, schema-version validation, reconciliation, `COMPLETION_READY` → `COMPLETION_APPLIED`, budget/completion evidence from a real provider |
| Why it stopped | Codex hit the provider **usage limit** before producing the structured result |
| Constraint | Do **not** modify v0.2-C to work around the block; do **not** spend another real Codex call; do **not** treat the partial run as a pass |
| Smoke checklist (v0.3-A, accumulated) | when the real OpenCode smoke is next authorized it must verify: actual provider message ordering (baseline vs final, no local re-sorting), `cursor_unknown`/`replayed` on the follow-up read, message-window stability between consecutive reads (F1: an arbitrary unseen assistant id must not be accepted as correlation proof if the window is unstable), `read_timeout`/`write_timeout` behaviour against a real server, that a pending/uncertain submission is never presented as a delivered prompt, and the real synchronous `/message` request/response contract (the A33 attempt never reached a model) |
| Deferred (A33, recorded not designed) | OpenCode native server auth is HTTP Basic (`OPENCODE_SERVER_PASSWORD`) while DevRelay v0.3-A sends a bearer token (`DEVRELAY_OPENCODE_TOKEN`); equivalence is unverified and out of scope for this remediation |
| Evidence | left exactly as produced (historical smoke directory and artifacts untouched by v0.3-A) |
| Next step | a replacement single-call smoke once Codex provider availability returns; the offline suite already covers everything except real-provider delivery |

## 2. Windows Codex shell P2 — `exec_command` rejected around the WindowsApps `pwsh.exe` alias

| Field | Value |
| --- | --- |
| Status | **OPEN (separate investigation)** — discovered during the v0.2-C smoke |
| Symptom | Codex's shell `exec_command` was rejected by policy when resolving the WindowsApps `pwsh.exe` alias (App Execution Alias / reparse-point path) |
| Impact | On this Windows host a Codex run may fail to execute shell commands even though the CLI itself starts |
| Scope note | **Not** fixed in v0.3-A and not caused by v0.3-A. It belongs to a dedicated Codex-runtime investigation (resolving the real PowerShell path, alias/reparse handling, or documenting a supported shell configuration) |
| Proposed owner | next v0.2-C-adjacent runtime investigation (not v0.3-B) |

## 3. v0.3-A known limitations (by design)

* One configured endpoint, one workspace, one explicitly selected session: no
  discovery, no fan-out, no cross-workspace reuse.
* No automatic retry of any kind; a failed request stays failed and visible.
* `wait_idle` is polling-based (bounded, no streaming/SSE subscription yet).
* The wire paths in `OpenCodePaths` are code-level defaults (there is no
  `opencode.paths` configuration key); the exact server contract is only
  confirmable by a real smoke (separately proposed).
* Message ordering is taken from the provider as-is (newest last); no timestamp
  re-sorting.  Call ids are unique under the single-process model only.
* Provider-error scrubbing covers literal plus JSON/backslash/percent encodings up
  to two escaping levels; paraphrased or fragmented secrets are out of scope.
* The bridge is **not** wired into the pipeline: it neither implements nor routes
  any implementer/reviewer role.

## 4. Deferred follow-ups from the v0.3-B MCP tool surface (recorded; **non-blocking for v0.3-B acceptance**)

| Item | Note |
| --- | --- |
| Real MCP-client smoke (ChatGPT or another host) → disposable OpenCode session | **done before acceptance**: real official MCP Python SDK 2.2.0 client over stdio against real OpenCode `1.18.11` with one explicit model call (`PASS — V0.3-B LOCAL REAL MCP SMOKE`, reply `DEVRELAY_V03B_MCP_OK`); kept for history |
| Streamable HTTP/SSE MCP transport | out of scope for v0.3-B (local stdio only); needs its own design (auth, exposure, session lifetime) |
| Multi-process concurrency / multi-workspace serving | v0.3-B is one process bound to one workspace with **all** tool execution serialized by one re-entrant lock; two `devrelay mcp serve` processes over one workspace share one ledger and are NOT serialized against each other |
| Tool-level progress notifications, MCP resources/prompts | not needed for the adapter surface in v0.3-B |
| Single-writer ledger (`sequence.json` allocation is a non-atomic read-modify-write over one fixed-name temp file) | the v0.3-B execution lock makes concurrent access impossible *inside one MCP server process*; a lock file / atomic compare-and-swap identity allocation is required before multi-process serving or concurrent reads can be claimed |
| Read concurrency inside one process | deliberately serialized in v0.3-B because reads also allocate durable call identities; revisit only together with ledger hardening, not by weakening the boundary |
| Serialization latency | a long `opencode_wait_idle` (bounded by `idle_timeout_seconds`, MCP cap 600 s) delays every other tool call in the same process; a scheduler is explicitly out of scope for v0.3-B |
| Post-POST unexpected exception can collapse `data` to `{}` | recorded at the v0.3-B gate; the envelope still reports `ok: false`, but the operation evidence is thinner than on a `DevRelayError` path |
| `retry_safe` is absent (rather than `false`) for some pre-bridge failure envelopes | the truth table covers the bridge-backed path only; absence is not a safety claim and is documented as such |
| `devrelay_status` bound-root vs `config.workspace` nuance | status reports the bound root while the bridge may target the configured `workspace`; both are surfaced, the reporting nuance is recorded |
| `opencode_interrupt` queues behind an in-flight `send_prompt` | expected under the global serialization boundary (it is not an out-of-band abort) and documented; a second control channel would be a new design |
| Provider error routes may echo the prompt on non-prompt operations | the prompt is never stored durably and the submission routes are covered; non-prompt error bodies are sanitized but not prompt-scrubbed |
| Dead `_ENVELOPE_KEY` constant (and a `ServerMiddleware` import kept only as a protocol check) in `src/devrelay/mcp/server.py` | recorded at the v0.3-B gate; harmless leftovers from the abandoned middleware approach, deliberately not touched by the concurrency remediation (server.py envelope shaping is frozen) |

### Carried findings at v0.3-B acceptance (**non-blocking for v0.3-B acceptance**)

**P2 (recorded, non-blocking)**

1. **SDK argument-schema validation may reflect caller-supplied `input_value`.**
   When the MCP SDK's own JSON-schema check rejects an argument, the SDK emits its
   own bounded error text *before* DevRelay's validation runs, and that text can
   quote the offending caller value.  Therefore documentation must **not** claim
   universal secret redaction for malformed **SDK-level** arguments; the
   DevRelay-shaped paths (envelope, text fallback, diagnostics, durable evidence)
   remain bounded and redacted.
2. **Post-POST unexpected exception can collapse the convenient MCP response
   evidence to `data={}`.**  The envelope still reports `ok: false`, but the
   operation evidence is thinner than on a `DevRelayError` path; the durable
   ledger remains the recovery evidence.

**P3 / future hardening**

* the execution lock is per MCP surface / server instance; the shipped `serve()`
  constructs exactly one surface per process;
* the accepted filesystem ledger remains single-writer and does not support
  multi-process concurrency;
* read concurrency is deferred until ledger hardening;
* a long `opencode_wait_idle` serializes subsequent calls in the same process;
* `retry_safe` is absent rather than an explicit `false` on some pre-bridge
  failures;
* bound root vs `config.workspace` reporting nuance in `devrelay_status`;
* `opencode_interrupt` queues behind an in-flight `opencode_send_prompt`;
* prompt-echo possibilities on some non-prompt error routes;
* minor parser / test-id / dead-symbol items already recorded (dead
  `_ENVELOPE_KEY` and the `ServerMiddleware` protocol-check import, stale comment
  wording in an existing test, `%TEMP%` hygiene note);
* provider `created_at` is currently passed through as a text/object
  representation;
* a fresh idle session may appear as `state: UNKNOWN` in list/get while
  `wait_idle` resolves idle through the `/session/status` absence semantics.

## 5. Deferred follow-ups from v0.3-D bounded orchestration (recorded; **non-blocking for v0.3-D acceptance**)

| Item | Note |
| --- | --- |
| Bounded real orchestration smoke (two cycles maximum / four model turns) | **DONE - `PASS`** (candidate `8b70610…`, run id `DR-dfb23a14e4654a5d9b75b296a27b1245`, 4 real model turns / 4 POSTs, 0 retries, 0 fallbacks, terminal guard proved twice); evidence in `docs/v0.3/V03D_ACCEPTANCE.md` §L.  **No second smoke is authorized** |
| v0.3-E recovery: reconciliation after a crash during a model submission, uncertain-call recovery, orphan-process recovery, automatic resume | **moved to the v0.3-E design** (`docs/v0.3/V03E_SPEC.md`, design branch `v0.3-e-recovery-reconciliation`, parent `56e7842`): **DESIGN FROZEN / NOT IMPLEMENTED / NOT ACCEPTED / UNRELEASED** - the independent design-freeze review approved candidate `9f4a01804b9affe8938a272553df345b5a60aeed` (P0 = 0, P1 = 0, P2 = 0, F1-F12 CLOSED; decision *APPROVE V0.3-E FAIL-CLOSED CORE DESIGN; PLATFORM PROOF GATE REQUIRED BEFORE IMPLEMENTATION*), after the earlier `REQUEST_CHANGES` rounds (P0 = 1/P1 = 6/P2 = 5, then two narrow P2 pointer/gate fixes).  The mandatory core is reconcile/report + `mark_unrecoverable`; `adopt_completed_turn` is optional and gated.  v0.3-D behaviour is unchanged - a persisted in-flight turn fails the run closed (`blocked_reason=turn_interrupted`) and is never replayed.  **Implementation is gated in two separate stages.**  The **mandatory fail-closed core** (reconcile/report + `mark_unrecoverable` -> BLOCKED; no retry, no model submission, no auto-resume) required a successful independent design review/freeze **and** the **local** strict-reader / ledger-integrity proof (**G0.1** / **P7**) to **PASS first**: implementation ordering is design frozen -> G0.1/P7 PASS -> implementation may be authorized.  Both steps have since happened (the design is frozen and **G0.1/P7 = PASS**, authoritative and independently approved - see the row above), so that gate no longer blocks implementation *eligibility*; implementation itself still requires a separately issued authorization.  Had G0.1/P7 failed, core implementation would have stayed **blocked** - there is **no degraded-implementation path** (a degraded scope would need its own design change and review).  The **optional** `adopt_completed_turn` capability stays **disabled** and is separately gated on **P1 + P2 + P3 + P8** (plus **P9** only if timestamp/order correlation is used) and the corresponding platform proof gate (**G1/G2**, maximum real provider/model inference 0).  Pending-result handling remains **report-only** and non-delivery classification remains **informational only**.  Current pointers: `docs/v0.3/V03E_SPEC.md` §19 (capability dependency), §25 (proof gate), §28 (proof status) |
| Multi-process / multi-surface orchestration locking | the execution lock is **per tool surface** and the shipped stdio server builds exactly one surface, so several surfaces or several writer processes against one workspace are unsupported; the honest scope is now stated in `tools.py`, `store.py`, the spec §6/§7 and the `devrelay_status` block, and needs its own design if ever required |
| Run listing / run-history API and run-document retention | not needed for the bounded workflow; run documents accumulate under `.devrelay/orchestration/runs/` |
| `devrelay_get_run` does not materialize an interrupted turn (it reports `in_flight: true`) | deliberate: reads never mutate; the next mutating action fails the run closed |
| Repeated transition/read duplication (the service re-resolves routes before every phase) | cheap and deterministic; a future stage could cache per-run resolutions |

### Carried findings at v0.3-D acceptance (recorded; **non-blocking; P0 = P1 = P2 = 0**)

v0.3-D was accepted internally and closed (unreleased) at candidate
`8b70610a5cdda600ef57cf8378c4f69cd33d5be4` after the two remediations and the one
authorized real bounded smoke (`PASS — V0.3-D REAL BOUNDED ORCHESTRATION SMOKE`);
the items below were carried forward deliberately and none of them blocks
acceptance.

| Item | Note |
| --- | --- |
| MCP SDK argument normalization (P3, measured) | the SDK builds a lax pydantic argument model from the declared tool schema, so JSON `true` -> `1`, `"2"` -> `2`, `2.0` -> `2` reach the tool body (and `1.5` is refused by the SDK).  The DevRelay bound is applied to the normalized value and the tool body rejects a real `bool`, so the 1..3 ceiling can never be raised; no fix is attempted at the adapter layer because the normalization happens above it.  Evidence: `test_mcp_sdk_normalizes_max_cycles_before_the_tool_body`, `test_boolean_max_cycles_is_rejected_by_the_tool_body` |
| `devrelay_get_run` still reports `in_flight: true` instead of materializing an interrupted turn | deliberate: reads never mutate; `legal_next_actions` is empty while an intent is live and the next mutating action materializes the interruption (`blocked`/`turn_interrupted`) and fails the run closed |
| No power-loss durability (P3, wording) | writes are atomic against a crash of this process (no partial document, no temp residue) but no `fsync` is issued, so power-loss durability is not claimed anywhere in code or docs |
| MCP SDK pre-parses JSON-shaped *string* prompts (P3, measured) | `FuncMetadata.pre_parse_json` converts a string argument into dict/list whenever the declared annotation is not plain ``str``, so a prompt like ``{"task": ...}`` is refused by the SDK's own argument validation before DevRelay's envelope exists - **nothing is submitted**.  Non-JSON prompts (including malformed JSON text) work normally.  A plain ``str`` annotation would suppress the coercion but would also replace the documented ``mcp_invalid_argument`` envelope for a missing prompt with an SDK-level error, so the trade-off is recorded.  Evidence: `test_json_shaped_prompts_are_refused_at_the_sdk_boundary` |
| A fully rewritten, internally consistent run history is undetectable (documented bound) | a run document is self-contained mutable JSON with no external integrity anchor, so an attacker who rewrites *every* field into a different but consistent history (for example resetting an exhausted run to a fresh-looking cycle 1) cannot be distinguished from an honest run.  v0.3-D claims only: all structural/semantic reachability invariants hold, and every malformed, inconsistent or partially rolled-back document fails closed before any model call.  An append-only journal or signed chain would be later hardening.  Evidence: `test_p1c_a_perfectly_rewritten_history_is_the_documented_bound` |
| v0.3-E G0.1/P7 proof — **PASS (authoritative, independently approved)** | executed once at HEAD `5bdc21d` with the real accepted ledger persistence path and external hard kills: G0.1-A1 (before durable ISSUED), A2 (during the ISSUED create-new write), B (after ISSUED, before settle), C (during settlement publication), D (after settlement publication) and E (corrupted-record control).  Every case met its predefined criterion; the strict scanner never treated malformed evidence as absence, and the tolerant `read_records` demonstrably **did** (0 records for the corrupt cases) - which is why the frozen design requires a dedicated corruption-strict reader.  Chronology: execution → **CANDIDATE PASS / REQUIRES INDEPENDENT REVIEW** → first independent review `REQUEST_CHANGES` for bookkeeping/status wording only (fixed in `8997071`) → final independent proof review **APPROVE V0.3-E G0.1 / P7 PLATFORM PROOF** (P0 = 0, P1 = 0, P2 = 0) → **G0.1 / P7 = PASS**.  G0.1/P7 therefore no longer blocks mandatory-core implementation *eligibility*; implementation remains **NOT AUTHORIZED** pending a separately issued authorization, adoption stays **DISABLED**, G0.4-G0.5/G1/G2 remain unrun, G0.2 passed its false-correlation proof on independent review after a separately authorized clean re-run and G0.3 returned a candidate FAIL (all six non-delivery classes proven pre-send; case G0.3-J surfaced `remote_protocol_error` instead of the precommitted `write_error` class) - see the rows below; G0.1/P7 and G0.2 are authoritative PASS and implementation remains NOT AUTHORIZED; platform proof gate = partially executed / not complete.  Evidence: `docs/v0.3/V03E_G0_1_P7_PROOF.md` |
| v0.3-E G0.3 transport / non-delivery classification — **CANDIDATE FAIL (awaiting independent review)** | executed once offline at HEAD `efa2ca3` under the oracle precommitted in `b9c4704` (`docs/v0.3/V03E_G0_3_TRANSPORT_ORACLE.md`, SHA-256 `6ca090b5…`) against the installed stack (httpx 0.28.1, httpcore 1.0.9, h11 0.16.0): the six accepted non-delivery classes (`connect_timeout`, `pool_timeout`, `connect_error`, `proxy_error`, `unsupported_protocol`, `local_protocol_error`) were each driven through the real accepted transport with a scripted in-process `httpcore` network backend and shown **pre-send** (no request header or body byte reached the network stream; `submission_uncertain == false`), and the uncertain classes (`read_timeout`, `write_timeout`, `read_error`, `remote_protocol_error`, unclassified `close_error`) all stayed `submission_uncertain == true` with `retry_safe == false`; HTTP rejection (500) and the success control were never treated as non-delivery, and exactly one submission POST was issued per case with no hidden resubmission.  The candidate **FAIL** is triggered by case **G0.3-J**: the installed httpcore suppresses a request-send `WriteError` and proceeds to the read phase, so the precommitted `write_error` trigger surfaced as `remote_protocol_error` (still submission-uncertain) instead of its precommitted class.  No non-delivery safety property was violated; P5 evidence is informational only in the frozen design, so no capability is silently degraded.  0 real provider/model calls, 0 real network requests, 0 OpenCode processes.  An independent review of that failure issued **FAIL - V0.3-E G0.3 / P5 PROOF - TYPE 1 PROOF-PLAN FAILURE** (P0 = 0, P1 = 0, P2 = 0) - the candidate correctly failed its immutable oracle, case J's exact classification expectation was wrong for the installed HTTP/1.1 request-send path, no accepted safe/non-delivery bucket was shown to be unsafe, and no runtime remediation is required - so a corrected clean rerun was separately authorized under the new precommitted oracle `docs/v0.3/V03E_G0_3_RERUN_ORACLE.md`.  Evidence: `docs/v0.3/V03E_G0_3_TRANSPORT_PROOF.md` |
| v0.3-E G0.2 clean false-correlation re-run — **PASS (authoritative, independently approved)** | separately authorized clean re-run executed once under the oracle precommitted in commit `12ea1b7` (`docs/v0.3/V03E_G0_2_RERUN_ORACLE.md`, SHA-256 `e900f7a3…`): the ten fixed cases A-J ran once each in order and every verdict stayed inside its precommitted allowed set (A unique `MATCH`; B target `MATCH` with the same-session look-alike rejected on prompt identity; C identical full tuple -> `MULTIPLE_MATCHES`; D weak-field-only records out of scope; E stale full-tuple duplicate -> conflict, never a freshness winner; F wrong role/operation excluded; G foreign run excluded, in-session full tuple -> conflict; H duplicates -> conflict with no winner; I prompt identity removed -> `NO_MATCH`/`IDENTITY_ABSENT`; J torn relevant look-alike -> `CORRUPTION` even with a clean unique candidate).  The oracle module hash was identical before and after execution, the static forbidden-rule audit was clean, and the accepted tolerant reader was recorded as a contrast (it silently drops the torn artifact).  Result: the independent clean-rerun review issued **APPROVE V0.3-E G0.2 FALSE-CORRELATION PROOF** (P0 = 0, P1 = 0, P2 = 0), so **G0.2 = PASS** (authoritative, independently approved; not self-approved).  Evidence: `docs/v0.3/V03E_G0_2_CLEAN_RERUN_PROOF.md`; original round preserved: `docs/v0.3/V03E_G0_2_FALSE_CORRELATION_PROOF.md` |
| v0.3-E G0.2 false-correlation proof (original round) — **CANDIDATE PASS (historical)** | executed once at HEAD `4448f92` (offline; 0 provider/model calls) against production-generated corpora: a live in-flight implementer intent from a real crash boundary plus the accepted ledger written by the real bridge/ledger classes.  Result: all ten planned cases A-J fail-closed - a unique `MATCH` only when the complete frozen identity tuple (`operation`, `session_id`, `prompt_sha256`, `prompt_chars`, `model`, `agent`) matches exactly one record in the run's role session (case A), while same-session/different-attempt (B), identical-prompt digests (C), weak-field-only equality (D), stale/unprovable cycle (E), wrong role/operation (F), foreign run in the same workspace (G), duplicate plausible matches (H), a missing identity field (I) and a torn look-alike (J) all resolve to `NO_MATCH` / `evidence_conflict` / `evidence_gap` / `corruption` with no false attribution and no timestamp tie-break.  Central findings: the ledger has **no run identity and no cycle/attempt identity**, and a live in-flight attempt never durably contains the ledger `call_id` (the association becomes durable only with the settlement write that clears `in_flight_turn`).  Interpretations flagged for review: a complete, schema-valid in-scope record carrying no prompt identity (the accepted ownership probe is labelled `send_prompt` but carries no prompt) is reported as `identity_absent` and never matched, instead of forcing a per-record gap; the stricter reading is reported as a sensitivity observation.  Evidence: `docs/v0.3/V03E_G0_2_FALSE_CORRELATION_PROOF.md` |
| v0.3-E recorded P3 observations (non-blocking; do not block design freeze) | **P3-1** `evidence_sha256` includes timestamp-derived metadata, but digest equality has no identity authority and is not timestamp-fidelity proof (that needs P9); **P3-2** "directly associated assistant message" remains a proof-gated platform assumption (part of the optional adoption gate, not the mandatory core); **P3-4/P3-5** minor clarity observations around summary wording recorded by the reviewer.  `P3` is **not** zero. |
| v0.3-E platform proofs (recorded; gate the **optional** adoption capability) | **P1** session-history durability across an OpenCode server restart, **P2** verbatim preservation of the submitted user text (so a digest match is sound), **P3** deterministic uniqueness for identical prompts, **P8** session exclusivity (no other writer in the evidence window), **P9** `created_at`/ordering fidelity (only if timestamps are used) - these gate `adopt_completed_turn` only.  **P4** per-operation pending handle (answered for 1.18.11: none, so pending is report-only) and **P5** whether the accepted connect-phase classes prove non-delivery (informational only).  **P6** session-identity strength and **P7** ledger settle-record integrity under a hard kill are local/bound proofs; P7 also gates the strict recovery evidence reader used by the mandatory core.  The mandatory fail-closed core (reconcile/report + `mark_unrecoverable`) needs no remote proof and ships as "reconcile and report, never adopt, always fail closed" if the proofs fail.  Evidence/decision record: `docs/v0.3/V03E_SPEC.md` §19, §25, §28 |
| A hard kill may leave an inert `.*.tmp` file in the runs directory (P3, wording) | it is never listed as a run and never honoured (only `DR-<32 hex>.json` is read and runs are loaded by valid id); normal saves leave no residue, and no `fsync`/power-loss durability is claimed.  Evidence: `test_an_inert_temp_file_is_never_listed_or_honoured` |
| Accepted v0.3-A / v0.3-C reasoning-part normalization (P3-1, carried, **not fixed**) | the accepted v0.3-A normalization maps a provider `reasoning` part to `kind="text"`; the real smoke's raw API proved that turns 2 and 4 carried a `reasoning` part next to the `text` part, so an "entire message character-for-character equal" criterion is fragile and must instead assert "the original answer *text* part is exactly the sentinel".  It does not affect v0.3-D, which persists no message text |
| `legal_next_actions` display shape (P3-2, informational, retained) | in `AWAITING_DECISION` it returns the human-readable string `devrelay_decide_run(complete|request_changes|stop)` rather than a bare tool name; retained deliberately for planner guidance |
| `terminal` is derived, not persisted (P3-3, informational, retained) | the durable document stores only `state`; `terminal` is computed from the terminal-state set, which is why the validator re-derives it rather than trusting a field |
| Start-edge timestamp/default metadata (final-review observation, carried, unresolved) | recorded as a minor documentation/audit observation from the final review; it does not block acceptance, and a docs-only closeout may not change runtime code, so it is carried for a later stage |
| Historical frozen v0.3-B wording says "process-scoped"/"process-wide" (final-review observation, carried) | those accepted v0.3-B documents and CHANGELOG entries remain **historical records and are not rewritten**; the current per-surface wording in `src/devrelay/mcp/tools.py`, the `devrelay_status` block, README and `V03_PLAN` supersedes them for the shipped server (one surface, all 17 tools serialized; several surfaces or writer processes unsupported).  Treat the older wording as superseded, not as the current contract |
| README model-turn wording nit (final-review observation, carried) | README/`V03_PLAN`/spec already say "reserved/consumed model-turn budget slots (at most six model POST attempts)" after the second remediation; the note is retained in case the reviewer meant a different surface, and no runtime change is authorized here |
| Corruption detection is structural + semantic, not cryptographic | nothing signs a run document, so an attacker who can rewrite the file can also rewrite a consistent lie within the invariants (for example a different route snapshot); the store's defences are the strict schema, the invariant pass, the workspace binding and single-writer access, not tamper-evidence |

## 6. Deferred follow-ups from v0.3-C agent role routing (recorded; **non-blocking for v0.3-C acceptance**)

| Item | Note |
| --- | --- |
| Real role-routed model smoke against a real OpenCode server | **done before acceptance**: two bounded runs - implementer → `opencode-go/deepseek-v4.1-flash` and reviewer → `opencode-go/glm-5.3-flash`, one explicit role turn and one `POST /session/{id}/message` each, three-way route agreement; a first two-role harness run is preserved as `FAIL` because its exact-whole-message condition was too strict for the provider-part normalization model |
| Generic / arbitrary role taxonomy and a role registry | v0.3-C ships exactly `implementer` and `reviewer` on purpose: a configurable role registry, role inheritance or per-role capability sets would freeze a taxonomy before the orchestration stage needs one; the internal model type is reusable so migration stays cheap |
| Session policy per role (session-per-role provisioning, binding or inference) | explicitly out of scope for v0.3-C: every role-aware send requires an explicit `session_id`, no session is created, bound, inferred or remembered, and a reviewer session is never derived from an implementer session |
| Role-level prompt templates / personas / system instructions | deliberately unsupported: role configuration carries identifiers only, so a role can never smuggle policy, prompts or credentials into a submission |
| Orchestration (automatic implementer -> reviewer sequencing, repair loops, bounded loops) | v0.3-D territory; v0.3-C routes and stops there |
| Role-aware cancellation leaves the same evidence as the raw path (no envelope, settled ledger record) | accepted v0.3-A behavior preserved on purpose; a future stage could add an explicit "role send in flight" reporting surface |

### Carried findings at v0.3-C acceptance (**non-blocking for v0.3-C acceptance**)

**v0.3-C-specific (from the independent review and the bounded real smokes)**

* **P3-1** — extra protocol members (`model`, `agent`, `endpoint`, `workspace`,
  `retry`) on `devrelay_send_role_prompt` are **accepted and silently discarded**
  by the SDK argument binding; they cannot influence the effective route.  Docs
  and descriptions must keep saying *ignored*, never *rejected*.
* **P3-2** — the role is resolved twice internally (MCP tool path and
  `RoleRouter`/service path).  Deterministic and harmless, but redundant; the
  tool-local route object is used only for the failure-envelope evidence.
* **P3-3** — caller-supplied role text may be echoed in bounded routing errors
  (recognized secret shapes such as `sk-…` are redacted).  Caller-input feedback,
  not a prompt/credential channel.
* **P3-4** — surrounding whitespace around a role name is trimmed, and the
  accepted model grammar stays somewhat lenient because the role path
  intentionally shares the accepted v0.3-A parser (identical raw/role outcomes).
* **P3-5** — **normalization fidelity / message-part typing**: real provider
  assistant messages contain distinct `reasoning` and `text` parts, but the
  accepted v0.3-A normalization currently maps `reasoning` content into the
  normalized `kind="text"` representation, so a normalized assistant message can
  mix model reasoning with the actual answer.  This explained the first v0.3-C
  implementer smoke's apparent extra preamble.  Possible future remediation:
  preserve reasoning as its own normalized kind instead of conflating it with
  answer text.  This is a **v0.3-A normalization item, not a role-routing
  defect**, and it must not be fixed without a separately authorized change.

**Inherited from v0.3-B (unchanged, still open)**

* SDK argument-schema errors may reflect the caller-provided `input_value`
  (documentation must not claim universal redaction on that path);
* a post-POST unexpected exception may collapse the convenient MCP evidence to
  `data={}` while the durable ledger remains the recovery evidence;
* the filesystem ledger remains single-writer (no multi-process concurrency);
* a long `wait_idle` serializes subsequent MCP calls in the same process;
* `retry_safe` is absent rather than explicit `false` for some pre-bridge
  failures;
* bound-root vs `config.workspace` reporting nuance in `devrelay_status`;
* `opencode_interrupt` queues behind an active send;
* non-prompt route prompt-echo edge cases;
* parser / test-id / dead-symbol cleanup items (dead `_ENVELOPE_KEY`,
  `ServerMiddleware` protocol-check import, stale comment wording, `%TEMP%`
  hygiene note);
* provider `created_at` is passed through as a text/object representation.

## 7. Deferred follow-ups after v0.3-A acceptance (recorded; **do not block acceptance**)

v0.3-A was accepted on the strength of the final real A33 smoke (see
`docs/v0.3/V03A_ACCEPTANCE.md`).  Every item below is explicitly **non-blocking**
and outside the accepted scope:

| Item | Note |
| --- | --- |
| Follow-up-only F1 window-correlation hardening | the final smoke showed a stable window (`cursor_unknown=false`, `replayed=false`, no truncation) and used the direct synchronous reply as the strongest evidence; a *follow-up-only* correlation path could still be hardened later |
| OpenCode Basic-vs-Bearer auth-mode compatibility | real OpenCode server auth is HTTP Basic when `OPENCODE_SERVER_PASSWORD` is set; DevRelay sends a bearer token from `DEVRELAY_OPENCODE_TOKEN` and the equivalence was never exercised (A33 ran without server auth) |
| Multi-process ledger locking | call ids are unique under the supported single-process model only |
| Cross-host/container workspace path mapping | ownership compares paths in DevRelay's own namespace; such sessions fail closed |
| Server-side pagination | the message window is local and reports truncation |
| Corrupt-ledger UX (`devrelay opencode calls`) | allocation fails closed; reporting/repair UX is not designed |
| Narrow exception/settlement documentation accuracy | keep the documented mapping between transport failures, settlement and result states precise as the code evolves |
| Windows Codex `pwsh.exe` alias (`exec_command` rejected) | carried forward from the v0.2-C smoke (item 2) |
| v0.2-C remaining real E2E evidence | still pending (item 1) |

The user's broken global OpenCode default (`coding-plan/deepseek-v4-pro`
referencing a provider disabled by the same configuration) is an
**environment/user configuration issue** — recorded here for context only, not a
DevRelay defect and not a backlog item.

## 8. Deferred beyond the second v0.3-A remediation (recorded, not started)

| Item | Why it is deferred |
| --- | --- |
| Cross-process ledger locking / multi-process call-id allocation | v0.3-A is a single-process bridge; a locking protocol needs its own design (and a decision about the supported concurrency model) |
| Call-id lexical ordering beyond `OC-9999` | the `OC-%04d` format is documented; changing the width would affect durable evidence compatibility |
| SSE/streaming instead of `wait_idle` polling, server-side pagination | explicitly out of the v0.3-A contract |
| Cross-host/container workspace path mapping | ownership is compared in DevRelay's namespace; a mapping would weaken the check and needs its own design |
| Proxy/CA configuration mechanism | ambient routing is disabled outright today; a reviewed mechanism is a separate feature |
| Post-abort verification polling (`interrupt_verified`) | accepted-but-unverified is the documented v0.3-A semantic |
| Attachment/tool-argument modeling | deliberately dropped in v0.3-A |

## 9. Pre-existing test-environment hygiene: shared `%TEMP%` residue

| Field | Value |
| --- | --- |
| Status | **OPEN (test hygiene, pre-existing)** — explicitly **not** fixed in the v0.3-A remediation |
| Symptom | `tests/test_baseline_ignored_self.py::test_real_index_bytes_unchanged_and_temp_index_cleaned` can fail when the shared `%TEMP%` already contains leftover `devrelay-index-*` directories from other runs |
| Evidence | the independent review demonstrated shared `%TEMP%` residue and that an isolated temporary directory restores the full suite to green (the suite is run with fresh `TEMP`/`TMP`/`TMPDIR` for every reported result) |
| Impact | environment-dependent test flake only; no production behaviour involved |
| Scope note | unrelated to the OpenCode bridge; must be handled as its own hygiene task (unique per-run temp roots or a tolerant assertion) |
