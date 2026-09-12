# DevRelay v0.2-C — Structured Codex Runtime (implementation)

Status: **CURRENT — candidate for independent review** (stage C only; D/E not started).

## What v0.2-C adds

The Codex runtime becomes structured, isolated, tamper-evident and replayable.
Codex is still the user's own authenticated CLI (ChatGPT subscription session);
DevRelay wraps it with a stronger runtime contract:

* **structured result contract** — `--output-schema` + `--output-last-message`
  produce a validated `ImplementationResult` (`schema_version = 1`);
  `--json` events are observational only and never required;
* **transient raw output** — the model writes into
  `.devrelay/tmp/runtime/<attempt-id>/last-message.raw.json`; the parent reads it
  with a hard cap, records `raw_result_sha256`, validates, sanitizes, writes the
  immutable `runtime/<attempt-id>/result.json` with create-new semantics and
  removes the staging file (or refuses to start the next attempt until it can);
* **argument ownership** — DevRelay owns `exec`, `--sandbox workspace-write`
  (exactly once), `--ignore-user-config`, `--ignore-rules`, `--json`,
  `--output-schema`, `--output-last-message`, the working directory and the stdin
  prompt. `-p/--profile`, user `--sandbox`, `--add-dir`, `--cd`,
  `--skip-git-repo-check`, `--approve-for-me`, dangerous bypass flags, output-path
  flags and unsafe `-c` namespaces are rejected at config load and pre-flight;
  a repository-level Codex config makes structured mode fail closed (the only
  escape is an explicit `codex.runtime_mode: text`);
* **environment scrub** — the Codex child never sees `DEVRELAY_REVIEWER_*` or the
  enumerated LLM provider credentials. This is an explicit denylist, **not** a
  general secret sandbox: other ambient secrets (`AWS_SECRET_ACCESS_KEY`,
  `GITHUB_TOKEN`, …) stay visible and are documented as out of scope;
* **control-plane guard** — the authoritative PRE identity lives only in parent
  memory while the child runs; after the child exits the parent recomputes a
  manifest of every protected `.devrelay` path *before* trusting or re-reading any
  state. Any unexpected change (state, frozen policy, ledgers, runs, reviews,
  other tasks, workspace config/profiles, staging extras, link/reparse
  substitution) fails closed as `codex_control_plane_violation`: no `TESTING`, no
  rerun, no blind overwrite, no rollback, and metadata-only evidence (paths,
  kinds, sizes, hashes — never the tampered bytes);
* **baseline root hardening** — `baseline.json`, `manifest.json` and
  `tracked.patch` are content-hashed; untracked baseline blobs are verified
  against their declared SHA-256 before use;
* **durable implementer milestones** — `PROCESS_EXITED → WORKSPACE_OBSERVED →
  GUARD_VERDICT_PERSISTED → RESULT_PERSISTED → COMPLETION_READY →
  COMPLETION_APPLIED`. `attempt_in_flight` stays set until a durable, replay-safe
  verdict exists;
* **completion replay** — a `COMPLETION_READY` attempt whose identities still
  match (worktree tree, Git guard, task delta, baseline integrity, protected
  control plane, `state.json` hash at READY) is applied locally with **0 external
  calls**; drift blocks as `implementer_replay_workspace_changed` or
  `replay_control_state_changed`;
* **two-stage reconciliation** — `implementation-reconciliation.json` at
  completion and immutable `test-reconciliation-NN.json` after DevRelay's own
  test run. Codex claims are advisory; the delta, guard and DevRelay tests stay
  authoritative;
* **hold recovery** — a same-process violation writes a post-mortem hold; the
  hold can only be cleared after the flagged control paths match their trusted PRE
  values again (`--acknowledge-control-plane-violation`, optionally
  `--restore-state-from-pre` for the hash-validated parent-held state copy). There
  is no “accept tampered state” path, and a hard parent crash offers no automatic
  restore (`control_plane_unverified` semantics: fail closed, manual recovery);
* **budget** — unchanged: `ProviderCallRecord` is the sole authority, intent is
  persisted before the spawn, replay/parsing/reconciliation cost nothing, and
  there is no invisible repair call.

## Configuration

```yaml
codex:
  executable: codex
  launcher_args: []                 # fixed prefix (wrapper scripts); never a runtime-control surface
  args: ["exec", "--sandbox", "workspace-write"]   # the shipped default is normalised away
  prompt_mode: stdin
  timeout_seconds: 1800
  runtime_mode: structured          # structured (default) | text (explicit compatibility opt-out)
  max_result_bytes: 262144          # bounded read of the model result
  max_capture_bytes: 262144         # bounded stdout/stderr capture (always drained, head+tail)
```

## Explicit limitations (honest boundary)

* Not a general sandbox: `--sandbox workspace-write` constrains model-executed
  shell commands inside the workspace; it does not contain external processes
  (MCP servers), the network, or ambient non-enumerated secrets.
* MCP/external tools are excluded by policy (no ambient MCP in structured mode),
  not contained; implementing MCP remains v0.3 scope.
* Codex session transcripts under `$CODEX_HOME` are outside this boundary
  (user-owned); `--ephemeral` is available as an explicit trade-off.
* Crash-replay and control-plane scenarios are validated offline with a stub
  Codex CLI; the single real Codex smoke is still pending.
* `state_schema_version` is **6** (v0.2-B schema-5 tasks load and migrate through
  the existing backup/too-new machinery; read-only commands never migrate).
