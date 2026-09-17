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

## 5. Deferred follow-ups from v0.3-D bounded orchestration (recorded; **non-blocking for v0.3-D review**)

| Item | Note |
| --- | --- |
| Bounded real orchestration smoke (two cycles maximum / four model turns) | requires independent review first (`P0 = 0`, `P1 = 0`, no smoke-blocking P2) and a separate authorization; the v0.3-D implementation round makes **0 real model calls** |
| v0.3-E recovery: reconciliation after a crash during a model submission, uncertain-call recovery, orphan-process recovery, automatic resume | explicitly out of scope for v0.3-D: a persisted in-flight turn fails the run closed (`blocked_reason=turn_interrupted`) and is never replayed, so an interrupted run must be resolved by a human or a later stage |
| Multi-process orchestration locking | v0.3-D assumes one MCP server process (accepted global serialization) and a single-writer store; multi-process orchestration needs its own design |
| Run listing / run-history API and run-document retention | not needed for the bounded workflow; run documents accumulate under `.devrelay/orchestration/runs/` |
| `devrelay_get_run` does not materialize an interrupted turn (it reports `in_flight: true`) | deliberate: reads never mutate; the next mutating action fails the run closed |
| Repeated transition/read duplication (the service re-resolves routes before every phase) | cheap and deterministic; a future stage could cache per-run resolutions |

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
