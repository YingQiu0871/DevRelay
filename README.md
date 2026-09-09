# DevRelay

> Plan with one model, build with Codex, review with another - without
> copy-pasting between agents.

DevRelay is a **local AI coding orchestrator** (CLI, v0.1) that automates the
mechanical handoffs of a multi-model development workflow:

```
PLAN -> IMPLEMENT -> TEST -> REVIEW -> FIX(loop) -> FINAL_GATE -> DONE
```

Today most people run this pipeline by copying text between chat windows:
ChatGPT plans, Codex implements, another model reviews, someone pastes the
findings back into Codex, repeat. DevRelay makes the handoffs structured and
persistent: every stage writes human-readable artifacts and a machine-readable
state file, so the pipeline can be paused, resumed, audited and reviewed
without losing context - and previously approved scope stays closed.

DevRelay is **project-agnostic** (it does not know or care about Evolune or any
other codebase) and **does not burn subscription quota on re-reviewing the
whole repository every round**: reviewers receive the current Task Packet, the
current delta, test evidence and previous findings - not the repository dump.

## Why

- Stop copy-pasting prompts, diffs and review findings between agents.
- Keep the state machine in the repo (`.devrelay/`), not in a chat context that
  disappears.
- Enforce a bounded fix loop (default 3 iterations) - never an infinite
  agent loop.
- Make reviews structural: P0/P1/P2 findings are blocking by policy; P3-only
  reviews pass by default; decisions come from the policy, not from natural
  language.
- Save expensive "re-scan everything" work: current delta first, previously
  approved scope stays closed unless the current delta can affect it.

## Architecture

```
src/devrelay/
├── cli.py                 # Typer CLI (devrelay ...)
├── config.py              # YAML profiles -> validated Pydantic config
├── models.py              # TaskPacket / Finding / ReviewResult / TaskRun ...
├── errors.py              # exception hierarchy
├── redact.py              # secret redaction for logs/artifacts
├── pipeline/
│   ├── states.py          # state machine (enum + transition table)
│   ├── policy.py          # config-driven decisions (severities, caps)
│   └── engine.py          # orchestrator: stages, artifacts, persistence
├── providers/
│   ├── base.py            # ImplementerProvider / ReviewerProvider
│   ├── codex_cli.py       # official Codex CLI adapter (mock-tested)
│   ├── manual.py          # manual reviewer handoff (markdown)
│   └── openai_compatible.py  # DeepSeek-style HTTP reviewer
├── workspace/
│   ├── runner.py          # subprocess runner (shell=False, timeouts)
│   ├── git.py             # GitWorkspace (read-only git access)
│   └── discovery.py       # workspace root discovery
└── artifacts/
    ├── store.py           # .devrelay artifact store (atomic JSON/markdown)
    └── renderer.py        # task.md / review requests / final report
```

The pipeline is a state machine with real enum states
(`NEW`, `PLAN_REQUIRED`, `PLAN_READY`, `IMPLEMENTING`, `TESTING`,
`REVIEWING`, `FIX_REQUIRED`, `FIXING`, `FINAL_GATE_REQUIRED`, `BLOCKED`,
`DONE`, `FAILED`). Every transition is validated, audited and persisted before
the next stage starts - if DevRelay is killed mid-task, `devrelay status` /
`devrelay continue` resumes from the persisted state.

## Quick start

Requirements: Python >= 3.11 and a git repository for the workspace.

```bash
pip install devrelay          # or: pip install -e .   (from this checkout)
cd your-project
devrelay init                 # creates .devrelay/config.yaml (never overwrites)
devrelay start "Fix Wear tile rendering"     # -> DR-0001, state PLAN_REQUIRED
```

Write the Task Packet (`.devrelay/tasks/DR-0001/task.md`) or import one:

```bash
devrelay plan show            # show the current task.md
devrelay plan import task.md  # or task.json -> state PLAN_READY
devrelay continue             # run the next pipeline stage(s)
devrelay status               # Planner/Implementer/Tests/Reviewer/Final Gate
devrelay diff                 # working-tree diff vs initial HEAD
devrelay logs                 # codex + test logs for the current task
```

Per-task artifacts (all human-readable, `state.json` is machine-readable):

```
.devrelay/tasks/DR-0001/
├── task.json  task.md  state.json  config.snapshot.yaml
├── implementation/iteration-01.md ...
├── reviews/review-01-request.md  review-01-result.json ...
├── logs/codex-01.stdout.log  test-01-01.log ...
└── final/final-review-request.md  report.md
```

## Codex CLI mode (no OpenAI API key)

The implementer is the **official Codex CLI** running against the user's own
already-authenticated Codex/ChatGPT login:

- DevRelay **does not require `OPENAI_API_KEY`** for the Codex path.
- DevRelay **never reads or manages ChatGPT credentials** - no cookie
  grabbing, no session tokens, no web automation, no undocumented auth.
- You are responsible for installing and authenticating the official Codex
  CLI (`codex --version`, `codex login`).
- Codex is executed as a subprocess with `shell=False` inside the workspace,
  with a configurable timeout (default 1800 s). Prompt, timeout, executable
  and extra args are configurable under the `codex:` profile section.

```yaml
# .devrelay/config.yaml
codex:
  executable: codex
  args: ["exec", "--full-auto"]   # your Codex CLI invocation
  prompt_mode: stdin              # stdin | argv
  timeout_seconds: 1800
```

DevRelay builds the implementation prompt itself (Task Packet, current
iteration, workspace, reviewer findings for fix passes, forbidden actions,
required completion report sections). When Codex is missing, DevRelay reports
`Codex CLI is not installed or not available on PATH.` and the task stays
put - `--help`, `init`, `status`, `plan ...`, `logs` and `diff` keep working
without Codex.

> Codex-specific behavior (stdin prompting, `--full-auto`, whether your CLI
> version auto-commits) is **not verified inside DevRelay** - the argv is a
> profile value you own. If your Codex version auto-commits, append the
> appropriate flag (e.g. `--no-commit`) to `codex.args`.

## Reviewer configuration

Reviewers never modify code. v0.1 ships two providers:

### 1. Manual (default)

DevRelay stops at `REVIEWING`, writes
`reviews/review-01-request.md` (Task Packet, initial HEAD, changed files,
current diff, test evidence, implementation report, previous findings) and
waits:

```bash
devrelay review export
# review the diff yourself (or paste the request into the model of your choice)
devrelay review import review.json
```

### 2. OpenAI-compatible HTTP reviewer (DeepSeek and friends)

Configure the provider in the profile and export environment variables -
DevRelay never stores keys:

```bash
export DEVRELAY_REVIEWER_BASE_URL=https://api.deepseek.com/v1
export DEVRELAY_REVIEWER_API_KEY=...   # required
export DEVRELAY_REVIEWER_MODEL=deepseek-chat
```

```yaml
review:
  provider: openai_compatible   # manual | openai_compatible
  blocking_severities: [P0, P1, P2]
  retries: 1                    # invalid-JSON retries before BLOCKED
  max_diff_bytes: 300000        # oversized diffs are truncated + flagged
```

The reviewer must answer with a single JSON object matching the `ReviewResult`
schema (decision + findings with severity P0-P3). Output is schema-validated;
invalid JSON is retried (default once) and **never guessed** - if it still
fails, the task goes `BLOCKED` for human handling.

## Manual mode & example workflow

The full manual workflow (no API reviewer configured):

```bash
devrelay start "Add PK chart interaction"          # DR-0001
devrelay plan import task.md                        # PLAN_READY
devrelay continue                                   # Codex implements, tests run,
                                                    # stops at REVIEWING (manual)
# reviewer (human or another model) reads reviews/review-01-request.md
devrelay review import review.json                  # PASS -> FINAL_GATE_REQUIRED
                                                    # or blocking finding -> FIX_REQUIRED
devrelay final export                               # final gate package
devrelay final approve --note "verified on device"  # DONE + final/report.md
```

`review.json` shape:

```json
{
  "decision": "REQUEST_CHANGES",
  "summary": "one real bug, one nit",
  "findings": [
    {"severity": "P2", "title": "...", "description": "...",
     "files": ["src/x.py"], "evidence": "...", "recommendation": "..."}
  ]
}
```

If a fix round is required, `devrelay continue` embeds the findings into the
next Codex prompt automatically. After `max_fix_iterations` (default 3)
blocking rounds the task goes `BLOCKED`; `devrelay unblock --reason "..."`
is the only, audited way to override it - it never silently skips findings.

## Policy (default profile)

```yaml
pipeline:
  max_fix_iterations: 3     # bounded fix loop
  auto_fix_tests: false     # failing tests -> BLOCKED unless enabled
review:
  provider: manual
  blocking_severities: [P0, P1, P2]   # P3-only reviews pass by default
tests:
  targeted: []              # project commands, e.g. ["./gradlew test"]
  full: []                  # release regression commands
  full_regression: release_only
scope:
  reuse_approved_scope: true
  current_delta_first: true
git:
  allow_commit: false       # v0.1 hard-disables commit/push/tag/reset
codex:
  executable: codex
  args: ["exec", "--full-auto"]
  prompt_mode: stdin
  timeout_seconds: 1800
```

The policy is enforced, not decorative: severity lists drive pass/fix
decisions, caps drive the BLOCKED state, test commands drive the TESTING stage,
and any `git.allow_*: true` is rejected at config load. Test commands run with
`shell=False` and timeouts; every execution result is saved under `logs/`.

## Security model

- **No credential handling**: Codex uses the user's own login; reviewer keys
  come from environment variables only; secret-shaped values are redacted from
  logs and artifacts (`[REDACTED]`).
- **No shell execution** of reviewer output or agent reports: commands come
  exclusively from the validated profile; all subprocesses use argv lists
  (`shell=False`).
- **No destructive git**: DevRelay never commits, pushes, merges, tags,
  resets or deletes branches. It records the initial HEAD, branch and
  preexisting dirty files so agent changes are never confused with yours.
- **Reviewers only see the delta**: Task Packet + changed files + diff +
  test evidence + reports (diff size capped), never the full repository.
- **Workspace boundary**: tasks operate only inside the initialized workspace.
- **Bounded automation**: fix loops capped, no auto git actions, `BLOCKED`
  requires an explicit human `unblock` with a reason.

## Current limitations (v0.1)

- One implementer: official Codex CLI. No other coding agents yet.
- One active task at a time; no concurrency.
- Reviewer input is the git working-tree delta vs the initial HEAD; the
  preexisting-dirty baseline is recorded but a perfectly separated task-only
  diff needs commits (which v0.1 intentionally never makes).
- Test commands are profile-configured whole commands; no per-language
  auto-detection.
- OpenAI-compatible reviewer requires a JSON-object-capable endpoint.
- No ChatGPT plugin / MCP / web UI / GitHub app yet - see Roadmap.

## Roadmap

- **v0.1** - local orchestration core (this release)
- **v0.2** - improved provider adapters / project profiles / state-driven UI
- **v0.3** - MCP server
- **v0.4** - ChatGPT integration / plugin
- **v0.5** - optional release automation with explicit approvals

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

The test-suite runs fully offline with mocked subprocesses/HTTP - no real
Codex, DeepSeek or network required. Covered: state transitions and rejected
invalid transitions, max-iteration blocking, P0/P1/P2 -> FIX_REQUIRED,
P3-only pass policy, Codex missing/success/failure/timeout, config parsing and
invalid config, artifact persistence and resume across store instances, dirty
workspace snapshots, manual review import validation, malformed reviewer JSON
(blocked, never guessed), secret redaction and shell-safety.

## License

MIT - see [LICENSE](LICENSE).
