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
| Evidence | left exactly as produced (historical smoke directory and artifacts untouched by v0.3-A) |
| Next step | a replacement single-call smoke once Codex provider availability returns; the offline suite (338 tests) already covers everything except real-provider delivery |

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
* The wire paths in `OpenCodePaths` are configurable defaults; the exact server
  contract is only confirmable by a real smoke (separately proposed).
* The bridge is **not** wired into the pipeline: it neither implements nor routes
  any implementer/reviewer role.

## 4. Pre-existing test-environment hygiene: shared `%TEMP%` residue

| Field | Value |
| --- | --- |
| Status | **OPEN (test hygiene, pre-existing)** — explicitly **not** fixed in the v0.3-A remediation |
| Symptom | `tests/test_baseline_ignored_self.py::test_real_index_bytes_unchanged_and_temp_index_cleaned` can fail when the shared `%TEMP%` already contains leftover `devrelay-index-*` directories from other runs |
| Evidence | the independent review demonstrated shared `%TEMP%` residue and that an isolated temporary directory restores the suite to 390/390 |
| Impact | environment-dependent test flake only; no production behaviour involved |
| Scope note | unrelated to the OpenCode bridge; must be handled as its own hygiene task (unique per-run temp roots or a tolerant assertion) |
