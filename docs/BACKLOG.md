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

## 4. Deferred beyond the second v0.3-A remediation (recorded, not started)

| Item | Why it is deferred |
| --- | --- |
| Cross-process ledger locking / multi-process call-id allocation | v0.3-A is a single-process bridge; a locking protocol needs its own design (and a decision about the supported concurrency model) |
| Call-id lexical ordering beyond `OC-9999` | the `OC-%04d` format is documented; changing the width would affect durable evidence compatibility |
| SSE/streaming instead of `wait_idle` polling, server-side pagination | explicitly out of the v0.3-A contract |
| Cross-host/container workspace path mapping | ownership is compared in DevRelay's namespace; a mapping would weaken the check and needs its own design |
| Proxy/CA configuration mechanism | ambient routing is disabled outright today; a reviewed mechanism is a separate feature |
| Post-abort verification polling (`interrupt_verified`) | accepted-but-unverified is the documented v0.3-A semantic |
| Attachment/tool-argument modeling | deliberately dropped in v0.3-A |

## 5. Pre-existing test-environment hygiene: shared `%TEMP%` residue

| Field | Value |
| --- | --- |
| Status | **OPEN (test hygiene, pre-existing)** — explicitly **not** fixed in the v0.3-A remediation |
| Symptom | `tests/test_baseline_ignored_self.py::test_real_index_bytes_unchanged_and_temp_index_cleaned` can fail when the shared `%TEMP%` already contains leftover `devrelay-index-*` directories from other runs |
| Evidence | the independent review demonstrated shared `%TEMP%` residue and that an isolated temporary directory restores the full suite to green (the suite is run with fresh `TEMP`/`TMP`/`TMPDIR` for every reported result) |
| Impact | environment-dependent test flake only; no production behaviour involved |
| Scope note | unrelated to the OpenCode bridge; must be handled as its own hygiene task (unique per-run temp roots or a tolerant assertion) |
