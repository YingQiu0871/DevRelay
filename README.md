# DevRelay

> Plan with one model, build with Codex, review with another - without
> copy-pasting between agents.

DevRelay is a **local AI coding orchestrator** (CLI) that automates the
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

DevRelay is **project-agnostic** (it does not know or care about any specific
codebase) and **does not burn subscription quota on re-reviewing the whole
repository every round**: reviewers receive the current Task Packet, the
*task-relative* delta, test evidence and previous findings - not a repository
dump.

**DevRelay can start from a dirty Git workspace without confusing pre-existing
user changes with agent changes.** That is the v0.1-RC core capability:
a durable *Task Baseline* is captured at task start, and every later diff is
computed against that baseline - never blindly against `HEAD`.

## Why

- Stop copy-pasting prompts, diffs and review findings between agents.
- Keep the state machine in the repo (`.devrelay/`), not in a chat context that
  disappears.
- Enforce a bounded fix loop (default 3 iterations) - never an infinite
  agent loop.
- Make reviews structural: P0/P1/P2 findings are blocking by policy; P3-only
  reviews pass by default; decisions come from the policy, not from natural
  language.
- Start tasks in dirty workspaces: pre-existing user edits, staged changes,
  deletions, renames, untracked files and binary files are baselined, so
  reviewers only see the *current task's* delta.
- Save expensive "re-scan everything" work: current delta first, previously
  approved scope stays closed unless the current delta can affect it.

## Example: dirty workspace in, clean task delta out

```
Before DevRelay:
  A.py contains uncommitted user work ("USER_CHANGE").

  devrelay start "Fix widget"
  Codex modifies A.py further and creates B.py.

  Reviewer receives ONLY:
    Codex's delta to A.py  (+AGENT_CHANGE)
    + B.py

  ... NOT the user's pre-existing A.py modifications.
```

```diff
@@ -1,3 +1,4 @@
  def widget():            # <- context lines may be shown
      user_work()          # <- never appears as an added (+) line
+     agent_fix()
```

## Architecture

```
src/devrelay/
├── cli.py                 # Typer CLI (devrelay ...)
├── config.py              # YAML profiles -> validated Pydantic config
├── models.py              # TaskPacket / Finding / ReviewResult / TaskRun,
│                          #   WorkspaceBaseline / PolicyViolation / TaskDelta
├── errors.py              # exception hierarchy
├── redact.py              # secret redaction for logs/artifacts
├── baseline/
│   ├── store.py           # durable baseline artifacts (json/patch/blobs)
│   ├── capture.py         # temporary-GIT_INDEX_FILE tree building
│   ├── comparator.py      # task-relative diff + tree reconstruction
│   ├── guard.py           # repository policy postcondition checks
│   └── service.py         # facade used by the engine/CLI
├── pipeline/
│   ├── states.py          # state machine (enum + transition table)
│   ├── policy.py          # config-driven decisions (severities, caps)
│   └── engine.py          # orchestrator: stages, artifacts, persistence
├── providers/
│   ├── base.py            # ImplementerProvider / ReviewerProvider
│   ├── codex_cli.py       # official Codex CLI adapter (stdin transport)
│   ├── manual.py          # manual reviewer handoff (markdown)
│   └── openai_compatible.py  # DeepSeek-style HTTP reviewer
├── workspace/
│   ├── runner.py          # subprocess runner (shell=False, UTF-8, timeouts)
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

## Task Baseline (RC core)

When `devrelay start "..."` runs, DevRelay captures the real task-start
workspace state **before any provider work**:

* HEAD SHA, branch, real-index tree, `git status --porcelain=v2` output;
* pre-existing tracked changes (staged + unstaged, deletions, renames,
  binaries) as a `HEAD -> worktree` binary-capable patch;
* pre-existing non-ignored untracked files as raw content copies with
  mode/symlink metadata;
* a **worktree tree** (HEAD + tracked edits + untracked files) built in a
  temporary index - stored as `baseline_worktree_tree_sha`.

Ignored files never enter the baseline; `.devrelay/` itself is always
excluded.  Per-file size limits are enforced: files above
`baseline.max_untracked_file_bytes` fail task creation with an explicit
message (file, size, limit) - never a silent skip.

### Temporary index strategy - the real index is never modified

Baseline and delta computation run git with `GIT_INDEX_FILE=<temp>`:
`git read-tree HEAD`, `git add -A -- .` (excluding `.devrelay`) and
`git write-tree` all happen against a throwaway index. Index-reading commands
that can opportunistically refresh stat data (`git status`, `git diff`,
`git write-tree`) run against a *clone* of the real index under the same
temporary mechanism, so even stat refreshes never touch `.git/index`.
DevRelay never runs `git add/reset/checkout/stash/commit` against the real
index. Tests prove `.git/index` bytes are unchanged across capture and delta
computation, and that no temporary index files are left behind.

### Durable persistence - no reliance on unreachable trees

A tree SHA written by `git write-tree` is only a fast path; if git garbage
collects it, the baseline must survive. Every task therefore stores durable
artifacts:

```
.devrelay/tasks/DR-0001/
├── task.json  task.md  state.json  config.snapshot.yaml
├── baseline/
│   ├── baseline.json      # validated WorkspaceBaseline (machine truth)
│   ├── manifest.json      # entries + dirty/untracked lists
│   ├── tracked.patch      # HEAD -> task-start worktree (--binary, renames)
│   └── files/             # raw copies of pre-existing untracked files
├── implementation/iteration-01.md ...
├── reviews/review-01-request.md  review-01-result.json ...
├── logs/codex-01.stdout.log  test-01-01.log ...
├── policy/pre-run-01.json  post-run-01.json  violations-01.json ...
└── final/final-review-request.md  report.md
```

`BaselineStore.load()` validates every artifact; corruption raises
`BaselineCorruptError` ("DevRelay does not guess"). If the recorded tree
object is gone, the tree is reconstructed from `baseline.head_sha` +
`tracked.patch` + saved untracked blobs in another temporary index, and its
SHA is verified against the recorded one before any diff is produced.

## Task-relative delta

Reviewers, implementation reports, `devrelay diff` and the final report all
use:

```
task-start baseline tree  ->  current worktree tree
```

Outputs: text diff, rename-aware name-status, name-only, stat, changed-file
list, and a binary-safe patch (`devrelay diff --binary --out task.patch`).
Binary files are detected from the tree diff and listed separately; raw
content is never force-decoded as text.  The review request and final report
explicitly separate:

* **PRE-EXISTING workspace changes** (baseline, listed by name, never in the
  diff content) from
* **TASK changes** (the true agent delta).

Legacy tasks created before baselines have `baseline: null` and an explicit
`state_schema_version` guard: DevRelay refuses to guess a diff for them and
reports `baseline_error` (BLOCKED for pipeline paths, clear error for CLI
commands). Create a new task to obtain precise deltas.

## Repository policy guard (post-run)

Prompts tell Codex not to commit/push/tag/switch/reset and to preserve
unrelated user changes - but prompts are not guarantees. Every Codex pass is
therefore wrapped:

```
PRE SNAPSHOT (HEAD, branch, tags, refs, real-index tree)
   -> provider run
POST SNAPSHOT
   -> structured PolicyViolation records -> BLOCKED on violation
```

| Check | Enforced locally | Outcome |
| --- | --- | --- |
| HEAD changed | yes (`git.allow_commit=false`) | BLOCKED, never auto-reset |
| branch switched | yes | BLOCKED |
| tags created/deleted/moved | yes (`git.allow_tag=false`) | BLOCKED |
| other local refs mutated | yes | BLOCKED |
| real git index staging mutated | yes (`git.allow_index_mutation=false`) | BLOCKED, never auto-unstage |
| push performed | **BEST-EFFORT / PROVIDER-LIMITED** | see below |

Violations are structured (`id/type/severity/before/after/description`),
persisted under `policy/` and in `state.json`, and survive restarts. DevRelay
**never automatically repairs repository state**; the human decides and may
use `devrelay unblock --reason ...`.

**Push enforcement limitation (stated honestly):** a local postcondition
check cannot mathematically prove that no `git push` occurred. The installed
Codex CLI (0.150.1) exposes sandbox modes (`--sandbox read-only |
workspace-write | danger-full-access`) but **no network-disable option**.
With `git.allow_push=false` DevRelay therefore enforces the prompt and the
sandbox it configures, and documents this as BEST-EFFORT - it does not invent
a guarantee it cannot verify.

## Codex CLI mode (no OpenAI API key)

The implementer is the **official Codex CLI** running against the user's own
already-authenticated Codex/ChatGPT login:

- DevRelay **does not require `OPENAI_API_KEY`** for the Codex path.
- DevRelay **never reads or manages ChatGPT credentials** - no cookie
  grabbing, no session tokens, no web automation, no undocumented auth.
- You are responsible for installing and authenticating the official Codex
  CLI (`codex --version`, `codex login`).

### Prompt transport: stdin is canonical

Verified against the installed CLI (`codex exec --help`, codex-cli 0.150.1):

> If not provided as an argument (or if `-` is used), instructions are read
> from stdin. If stdin is piped and a prompt is also provided, stdin is
> appended as a `<stdin>` block.

DevRelay therefore streams the full Task Packet + findings + constraints on
**stdin** by default (never in argv - Windows argv length limits and shell
interpretation never apply). `argv` survives only as an explicit
compatibility fallback (`codex.prompt_mode: argv`).

**Important:** this CLI version does **not** offer `--full-auto`; the shipped
default is the documented sandbox invocation:

```yaml
codex:
  executable: codex
  args: ["exec", "--sandbox", "workspace-write"]
  prompt_mode: stdin
  timeout_seconds: 1800
```

`devrelay doctor` verifies the configured `codex.args` against the installed
CLI's `codex exec --help` and rejects unknown flags before any run starts.
Sandbox/approval semantics (e.g. whether `--approve-for-me` or a
`danger-full-access` policy is needed for your repo) are **provider-runtime
behavior to verify on your machine with a no-op task**; DevRelay refuses to
pretend otherwise.

## Quick start

Requirements: Python >= 3.11, git, and a repository with **at least one
commit** (baselines snapshot `HEAD`).

```bash
pip install devrelay          # or: pip install -e .   (from this checkout)
cd your-project
devrelay init                 # creates .devrelay/config.yaml (never overwrites)
devrelay start "Fix Wear tile rendering"     # -> DR-0001, state PLAN_REQUIRED
```

Even when your working tree is dirty (uncommitted user work, staged changes,
untracked scratch files), `start` captures the baseline and proceeds.

```bash
devrelay plan show            # show the current task.md
devrelay plan import task.md  # or task.json -> state PLAN_READY
devrelay continue             # run the next pipeline stage(s)
devrelay status               # Planner/Implementer/Tests/Reviewer/Final Gate/Baseline
devrelay diff                 # TASK-RELATIVE diff (baseline -> now)
devrelay diff --binary --out task.patch   # binary-safe task patch
devrelay logs                 # codex + test logs for the current task
```

If `start` fails because a pre-existing file exceeds
`baseline.max_untracked_file_bytes`, the error names the file, its size and
the config knob - nothing is silently dropped.

## Manual mode & example workflow

The full manual workflow (no API reviewer configured):

```bash
devrelay start "Add PK chart interaction"          # DR-0001 (baseline captured)
devrelay plan import task.md                        # PLAN_READY
devrelay continue                                   # Codex implements, tests run,
                                                    # stops at REVIEWING (manual)
# reviewer (human or another model) reads reviews/review-01-request.md
devrelay review import review.json                  # PASS -> FINAL_GATE_REQUIRED
                                                    # or blocking finding -> FIX_REQUIRED
devrelay final export                               # final gate package (task-relative)
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

## Reviewer configuration

Reviewers never modify code. v0.1 ships two providers:

1. **Manual (default)** - DevRelay stops at `REVIEWING` and writes
   `reviews/review-01-request.md` containing the task-relative delta (the
   request header states the diff scope explicitly).
2. **OpenAI-compatible HTTP reviewer (DeepSeek and friends)** via env:

```bash
export DEVRELAY_REVIEWER_BASE_URL=https://api.deepseek.com/v1
export DEVRELAY_REVIEWER_API_KEY=...   # required; never stored
export DEVRELAY_REVIEWER_MODEL=deepseek-chat
```

```yaml
review:
  provider: openai_compatible
  blocking_severities: [P0, P1, P2]
  retries: 1                    # invalid-JSON retries before BLOCKED
  max_diff_bytes: 300000        # oversized diffs are truncated + flagged
```

The reviewer must answer with a single JSON object matching the
`ReviewResult` schema. Output is schema-validated; invalid JSON is retried
and **never guessed** - persistent failure routes the task to `BLOCKED`.

## Policy (default profile)

```yaml
pipeline:
  max_fix_iterations: 3
  auto_fix_tests: false
review:
  provider: manual
  blocking_severities: [P0, P1, P2]
  retries: 1
  max_diff_bytes: 300000
baseline:
  max_untracked_file_bytes: 52428800   # per-file cap for untracked copies
tests:
  targeted: []              # project commands, e.g. ["./gradlew test"]
  full: []
  full_regression: release_only
scope:
  reuse_approved_scope: true
  current_delta_first: true
git:
  allow_commit: false       # v0.1 hard-disables commit/push/tag/reset and
  allow_push: false         #   any real-index mutation: setting any of
  allow_tag: false          #   these true is a CONFIG ERROR
  allow_reset_hard: false
  allow_index_mutation: false
codex:
  executable: codex
  args: ["exec", "--sandbox", "workspace-write"]
  prompt_mode: stdin        # canonical; argv is an explicit fallback
  timeout_seconds: 1800
```

The policy is enforced, not decorative: severity lists drive pass/fix
decisions, caps drive the BLOCKED state, test commands drive the TESTING
stage, and any `git.allow_*: true` is rejected at config load. Test commands
run with `shell=False` and timeouts; every execution result is saved under
`logs/`.

## Security model

- **No credential handling**: Codex uses the user's own login; reviewer keys
  come from environment variables only; secret-shaped values are redacted
  from logs and artifacts (`[REDACTED]`).
- **No shell execution** of reviewer output or agent reports: commands come
  exclusively from the validated profile; all subprocesses use argv lists
  (`shell=False`) with UTF-8 pipes.
- **No destructive git**: DevRelay never commits, pushes, merges, tags,
  resets, or touches the user's real index. Repository control state is
  snapshotted before/after every provider run and violations BLOCK the task;
  nothing is auto-repaired.
- **Reviewers only see the task delta**: Task Packet + task-relative diff +
  changed files + test evidence + reports (size capped), never the full
  repository, never pre-existing user content.
- **Workspace boundary**: tasks operate only inside the initialized workspace.
- **Bounded automation**: fix loops capped, no auto git actions, `BLOCKED`
  requires an explicit human `unblock` with a reason.
- **Provider limits are stated, not hidden**: push prohibition is
  BEST-EFFORT/PROVIDER-LIMITED and documented as such.

## Current limitations (v0.1)

- One implementer: official Codex CLI (stdin transport). Codex argv/sandbox
  behavior must be validated on your machine (DevRelay rejects flags the
  installed CLI does not document).
- Codex structured event output (`--json` / `--output-schema`) is **not**
  parsed in v0.1 - recorded on the v0.2 roadmap. Exit codes and full stdout
  are captured today.
- One active task at a time; no concurrency.
- Real-git index byte-immutability is guaranteed for baseline/delta paths
  (tested); other git read commands use `--no-optional-locks` where possible.
- Test commands are profile-configured whole commands; no per-language
  auto-detection.
- OpenAI-compatible reviewer requires a JSON-object-capable endpoint.
- Push prohibition cannot be mathematically enforced with the current Codex
  CLI (no network-disable flag) - see the policy-guard section.
- No ChatGPT plugin / MCP / web UI / GitHub app yet - see Roadmap.

## Roadmap

- **v0.1** - local orchestration core with task baselines, task-relative
  deltas and repository policy guards (this release)
- **v0.2** - structured Codex event output (`codex exec --json`),
  improved provider adapters / project profiles / state-driven UI
- **v0.3** - MCP server
- **v0.4** - ChatGPT integration / plugin
- **v0.5** - optional release automation with explicit approvals

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

116 tests run fully offline with mocked subprocesses/HTTP where needed and
real (tiny) git repositories for baseline/guard coverage - no real Codex,
DeepSeek or network required. Coverage includes: state transitions and
rejected invalid transitions; max-iteration blocking; P0/P1/P2 ->
FIX_REQUIRED; P3-only pass policy; Codex missing/success/failure/timeout;
stdin transport (long/Unicode/shell-metacharacter prompts stay on stdin);
config parsing and invalid config; artifact persistence and resume; dirty
workspace baselines (same-file user+agent edits, untracked, staged +
staged/unstaged mixes, deletions, renames, binary, Unicode and space
filenames, ignored files); baseline tree reconstruction after `git gc`;
manifest corruption as explicit error; real-index immutability; temp-index
cleanup; HEAD/branch/tag/index-mutation policy violations -> BLOCKED without
auto-repair; review request and final report separation of PRE-EXISTING vs
TASK changes; secret redaction; shell safety.

## License

MIT - see [LICENSE](LICENSE).
