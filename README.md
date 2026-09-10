# DevRelay

> Plan with one model, build with Codex, review with another - without
> copy-pasting between agents.

**Supported release: v0.1.0** (see [CHANGELOG.md](CHANGELOG.md); the CLI
reports the same version via `devrelay version`).
Source: <https://github.com/YingQiu0871/DevRelay> -
[Issues](https://github.com/YingQiu0871/DevRelay/issues)

> **v0.2-A candidate (unreleased)**: the automatic review loop described under
> [Automatic review loop (v0.2-A)](#automatic-review-loop-v02-a) is implemented
> in this working branch as a candidate for independent review. It is not part
> of the v0.1.0 release, the version number is unchanged, and its behaviour was
> validated with fake providers only. Specification and acceptance matrix:
> [docs/v0.2/V02_SPEC.md](docs/v0.2/V02_SPEC.md),
> [docs/v0.2/V02_ACCEPTANCE.md](docs/v0.2/V02_ACCEPTANCE.md).

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
- Cap external work with an enforced execution budget (v0.2-A): every
  implementer/reviewer invocation is pre-flight checked and persisted, so a
  runaway loop stops at `BLOCKED` instead of quietly spending calls.
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
│                          #   WorkspaceBaseline / PolicyViolation / TaskDelta,
│                          #   ProviderCallRecord / ReviewAttempt (v0.2-A)
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
│   ├── budget.py          # execution budget: pre-flight + usage accounting
│   ├── review_lifecycle.py # review attempts, call evidence, fingerprints
│   └── engine.py          # orchestrator: stages, artifacts, persistence
├── providers/
│   ├── base.py            # ImplementerProvider / ReviewerProvider
│   ├── evidence.py        # CallSink protocol + ReviewCallPolicy (v0.2-A)
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

### Binary-exact patch transport

`tracked.patch` is binary-sensitive durable data, so it never travels through a
text-mode pipe: `git diff --binary` output is captured as raw bytes, stored
verbatim (`raw git diff bytes == stored tracked.patch bytes`, byte-for-byte),
and fed back to `git apply --cached --binary -` as raw bytes. No
universal-newline translation and no implicit encode/decode can occur on that
path (on Windows, text-mode stdin would otherwise rewrite `\n` to `\r\n` and
silently corrupt the patch). Repositories whose *repo-form* content contains
CRLF are covered by dedicated fidelity tests.

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
│          review-01-<attempt-id>-meta.json    # immutable per review attempt
│          review-01-meta.json                 # latest view of that round
├── logs/codex-01.stdout.log  <attempt-id>.stdout.log  test-01-01.log ...
├── policy/attempt-01.json  pre-run-01.json  post-run-01.json   # latest views
│          attempts/<attempt-id>.json          # immutable per attempt
│          calls/<call-id>.json                # immutable per external call
│          runs/<attempt-id>-{pre,post,violations}.json
│          policy-refresh-NN-{before,after}.yaml + -NN.json
│          violations-01.json ...
└── final/final-review-request.md  report.md
```

Identities in file names (`<call-id>` = `DR-0001-C0007`, `<attempt-id>` =
`DR-0001-A0002` / `DR-0001-R0002`) come from persisted task sequences, so
immutable evidence is never overwritten by a retry; the `NN`-named files are
documented "latest view" convenience copies.

`BaselineStore.load()` validates every artifact; corruption raises
`BaselineCorruptError` ("DevRelay does not guess"). If the recorded tree
object is gone, the tree is reconstructed from `baseline.head_sha` +
`tracked.patch` + saved untracked blobs in another temporary index, and its
SHA is verified against the recorded one before any diff is produced. The
recovery path is regression-tested against a real `git gc --prune=now` for
pre-existing tracked modifications, deletions, renames, binary changes, staged
new files, staged+unstaged mixes and CRLF content - and it still fails closed
(never a HEAD fallback) when an artifact is corrupt.

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

* **PRE-EXISTING workspace changes** (baseline, listed by name; they are never
  attributed as task additions) from
* **TASK changes** (the true agent delta).

A unified diff necessarily shows surrounding *context* lines, so pre-existing
content can appear unmarked as context; it never appears as an added (`+`) task
modification.

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
| index state cannot be captured reliably (unresolved merge conflict, unreadable index) | yes - **fail closed** | BLOCKED *before* the provider runs (pre-check) or after the run (post-check); never treated as "no change" |
| push performed | **BEST-EFFORT / PROVIDER-LIMITED** | see below |

Violations are structured (`id/type/severity/before/after/description`),
persisted under `policy/` and in `state.json`, and survive restarts. DevRelay
**never automatically repairs repository state**; the human decides and may
use `devrelay unblock --reason ...`.

### Interrupted provider attempts (fail closed)

Every implement/fix run is a persisted *attempt* with a durable identity
(`policy/attempts/<attempt-id>.json`, plus `policy/attempt-NN.json` as the
latest view of logical pass NN).
The PRE snapshot **and** an in-flight crash marker are written *before* the
provider starts, and the POST snapshot + policy guard run for every outcome -
success, non-zero exit, timeout, `KeyboardInterrupt` or any Python exception.
Consequences:

* A provider that raises after modifying the workspace still gets POST
  evidence and policy verification; a policy violation takes priority over the
  provider error, and the task goes BLOCKED (no auto-repair of the repo).
* If an attempt raised without policy violations, the task is BLOCKED as
  `interrupted_attempt`: the workspace may have been modified, so a human must
  acknowledge with `devrelay unblock --reason "..."` before DevRelay will run a
  provider again.
* If the process died hard (kill -9 / power loss) the in-flight marker stays
  persisted; on restart DevRelay refuses to auto-rerun the provider and reports
  *"Previous provider attempt may have modified the workspace. Manual
  acknowledgement is required."*

Repositories with **unresolved merge conflicts** must be resolved (or the index
made readable) before an automated provider run: DevRelay blocks because it
cannot guarantee index-mutation detection. Baseline capture itself still works
in such repos.

**Push enforcement limitation (stated honestly):** a local postcondition
check cannot mathematically prove that no `git push` occurred. The installed
Codex CLI (0.150.1) exposes sandbox modes (`--sandbox read-only |
workspace-write | danger-full-access`) but **no network-disable option**.
With `git.allow_push=false` DevRelay therefore enforces the prompt and the
sandbox it configures, and documents this as BEST-EFFORT - it does not invent
a guarantee it cannot verify.

## Codex CLI mode (no OpenAI API key)

DevRelay invokes the **official Codex CLI**; the Codex CLI may be authenticated
using the user's own ChatGPT subscription login:

- DevRelay **does not read or manage ChatGPT credentials** - no cookie
  grabbing, no session tokens, no web automation, no undocumented auth.
- **No OpenAI API key is required for the Codex CLI execution path.**
- You are responsible for installing and authenticating the official Codex
  CLI (`codex --version`, `codex login`).
- Codex usage is governed by your own Codex/ChatGPT plan and limits; DevRelay
  makes no claim about how much usage any plan provides, and it never retries
  a failed real invocation on its own - a failed or interrupted attempt is
  surfaced as BLOCKED and requires explicit human acknowledgement.

### Prompt transport: stdin is canonical

Verified against the installed CLI (`codex exec --help`, codex-cli 0.150.1):

> If not provided as an argument (or if `-` is used), instructions are read
> from stdin. If stdin is piped and a prompt is also provided, stdin is
> appended as a `<stdin>` block.

DevRelay therefore streams the full Task Packet + findings + constraints on
**stdin** by default (never in argv - Windows argv length limits and shell
interpretation never apply). The stdin bytes are written byte-exactly (LF stays
LF; no text-mode `\r\n` translation). `argv` survives only as an explicit
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
commit** (baselines snapshot `HEAD`; DevRelay reports a clear error instead of
a Git error when the repository has no commits yet).

DevRelay v0.1.0 is distributed from source (a PyPI release is planned):

```bash
# from a checkout or an unpacked sdist/wheel
python -m pip install .
# or isolated CLI install
pipx install .
```

Build the wheel/sdist yourself with `python -m build` (dev extra:
`python -m pip install -e ".[dev]"`).

```bash
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
                              #   + budget used/max, last review attempt, policy source
devrelay usage                # provider call audit (read-only, never resets budget)
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
  retries: 1                    # invalid-JSON (format) retries before BLOCKED
  transport_retries: 0          # network/HTTP retries: opt-in, each one is a call
  max_response_chars: 200000    # response *parsing/persistence* cap (see below)
  max_diff_bytes: 300000        # oversized diffs are truncated + flagged
```

The reviewer must answer with a single JSON object matching the
`ReviewResult` schema. Output is schema-validated; invalid JSON is retried
and **never guessed** - persistent failure routes the task to `BLOCKED`.

With `provider: openai_compatible` the review step runs automatically (see
below). With the default `provider: manual`, DevRelay stops at `REVIEWING`,
`devrelay review export`/`review import` drive the loop, and **zero** external
provider calls are made.

## Automatic review loop (v0.2-A)

v0.2-A makes the review step a bounded, fully accounted loop: DevRelay calls
the configured reviewer itself, feeds blocking findings straight back into the
fix prompt, and stops with hard evidence when a limit is reached. The state
machine is unchanged - still `PipelineState`
(`IMPLEMENTING -> TESTING -> REVIEWING -> FIX_REQUIRED -> FIXING -> ... ->
FINAL_GATE_REQUIRED`), and never `DONE` without a human final approval.

### Execution budget (always enforced)

```yaml
budget:
  max_implementer_calls: 4
  max_reviewer_calls: 4
  max_total_provider_calls: 8
```

Every external invocation is recorded *before* it happens (`ProviderCallRecord`
in task state plus `reviews/review-NN-call-MM-meta.json`) and the budget is
checked *before* the call starts. When a limit would be exceeded the task goes
`BLOCKED` with code `provider_budget_exhausted` and a message that reports
used/max for all three limits. The budget is **never reset automatically** -
not by `continue`, not by a restart, not by the fix loop. The only supported
way to change it for a running task is the audited
`devrelay unblock --refresh-policy --reason "..."`.

What counts as one call (invocation counting, not billing):

| Action | Counted as |
| --- | --- |
| Implementer (Codex) pass that actually ran | 1 |
| Implementer pass refused before start (CLI unavailable, index pre-flight) | 0 |
| Remote reviewer HTTP attempt | 1 |
| ...including the attempt whose answer was invalid JSON (format retry) | 1 each |
| Reviewer transport failure (the request was started) | 1 |
| Manual review import | 0 (a `ReviewAttempt` is still recorded) |

**Honesty**: the budget counts *DevRelay-initiated invocations*. It is not a
token, cost or subscription meter - it cannot see retries inside the provider
CLI, provider-side billing or plan quota. "4 implementer calls" means "at most
4 requests leave this machine", and says nothing about money.

`review.max_response_chars` is a **parsing/persistence cap**, not a
network-level memory limit: the HTTP client may buffer a response body before
DevRelay applies the cap. What it guarantees is that oversized reviewer content
is never parsed, never truncated-and-guessed and never persisted - it fails
closed. A true streaming byte limit is a later-stage item.

### Reviewer attempt lifecycle and crash safety

Each automatic review round writes immutable per-attempt evidence
(`reviews/review-NN-<attempt-id>-meta.json`, plus `reviews/review-NN-meta.json`
as the latest view) and one immutable file per call
(`policy/calls/<call-id>.json`). Identities come from durable, task-scoped
sequences allocated *before* anything leaves the machine (`DR-0001-C0007`,
`DR-0001-R0002`, `DR-0001-A0002`), so restarts, unblocks and retries can never
reuse an identity or overwrite another call's evidence.

Crashes are handled by evidence, not by guessing:

| What was persisted when the process died | On the next `devrelay continue` |
| --- | --- |
| Nothing (call may have been billed) | fail closed: `BLOCKED interrupted_reviewer_attempt`, needs `devrelay unblock --reason "..."` |
| A schema-valid, sanitized **result** (but not yet applied) | **replayed locally with 0 external calls** into the policy-defined state |
| Result applied, terminal transition missing | the transition is completed locally with 0 external calls |

A review round that was started but never finalized is detected from the
persisted attempt and fails closed the same way - an acknowledging `unblock`
closes it as `INTERRUPTED`, keeps its call evidence, and the retried round gets
its own attempt identity (`A0002`/`R0002`, never a reused `A0001`).

Transport failures (network/HTTP/timeout) and format failures (schema-invalid
answer) are separated, and the phase label follows the *cause*: a mixed
format -> transport -> format sequence is recorded as `REVIEW`,
`REVIEW_FORMAT_RETRY`, `REVIEW_TRANSPORT_RETRY`, `REVIEW_FORMAT_RETRY`.
`review.retries` (default 1) retries only *format* failures; transport retries
are opt-in via `review.transport_retries` (default 0) and are counted like any
other call. HTTP error bodies and model output pass through the same redaction
boundary as reviewer input before they are persisted.

### Repeated findings

Every finding gets a deterministic fingerprint
(`sha256(severity | normalized title | files | description)`) and per-task
seen counts. `pipeline.max_same_finding_cycles` (default `0` = disabled) can
stop a loop that keeps re-reporting the same findings; fingerprints and counts
are recorded either way and are visible in `devrelay status` / `devrelay usage`.

### Policy snapshot

Budget, blocking severities, retry counts, test commands, scope and
`max_same_finding_cycles` are captured into
`.devrelay/tasks/<id>/config.snapshot.yaml` at `start` (with
`policy_source: snapshot` persisted immediately, not inferred later) and apply
for the whole task, so editing `.devrelay/config.yaml` mid-task cannot silently
change the rules a task is judged by (`devrelay status` shows the source:
`snapshot` or `live-fallback`). Codex executable/args and the reviewer
endpoint/credentials remain live environment wiring.

`devrelay unblock --refresh-policy --reason "..."` is the only supported way to
change a running task's budget/blocking policy. It preserves the previous policy
durably (`policy/policy-refresh-NN-before.yaml`, `-after.yaml`, `-NN.json` with
before/after SHA-256) and never resets, deletes or renumbers usage: a tightened
budget still counts the calls already spent.

### Visibility commands

```bash
devrelay status     # state, budget used/max, last review attempt, policy source
devrelay usage      # read-only: every provider call, every review attempt
devrelay doctor     # checks env var PRESENCE only - it sends no request
```

`devrelay usage` is the audit view: per-call kind/phase/success/error type,
duration, model and endpoint *host* (never a URL with credentials). There is
deliberately no command that resets or forges usage, and `doctor` never spends
a call: it reports `set`/`MISSING` for `DEVRELAY_REVIEWER_BASE_URL`,
`DEVRELAY_REVIEWER_API_KEY` and `DEVRELAY_REVIEWER_MODEL` without contacting
the endpoint.

### Authority

The reviewer is *advisory*. Policy decides: a `PASS` decision that still
carries a blocking finding does not pass, blocking findings route to
`FIX_REQUIRED` / `BLOCKED`, and the final gate stays manual
(`devrelay final approve`) with zero provider calls.

## Policy (default profile)

```yaml
pipeline:
  max_fix_iterations: 3
  max_same_finding_cycles: 0        # 0 = disabled; fingerprints recorded anyway
  auto_fix_tests: false
budget:
  max_implementer_calls: 4          # checked before every external call
  max_reviewer_calls: 4
  max_total_provider_calls: 8
review:
  provider: manual
  blocking_severities: [P0, P1, P2]
  retries: 1
  transport_retries: 0
  max_response_chars: 200000
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
decisions, caps drive the BLOCKED state, the execution budget gates every
external call before it starts, test commands drive the TESTING stage, and any
`git.allow_*: true` is rejected at config load. These policy values are
snapshotted into the task at `devrelay start` (see the automatic review loop
section). Test commands run with `shell=False` and timeouts; every execution
result is saved under `logs/`.

## Security model

- **No credential handling**: Codex uses the user's own login; reviewer keys
  come from environment variables only.
- **Redaction is best-effort, not DLP**: secret-shaped values (`sk-...`,
  `Bearer ...`, `Authorization: ...`, `API_KEY=...`, `token=...`, and values of
  secret-looking environment variables) are pattern-redacted from logs, from
  everything a reviewer receives, and from the manual review-request artifact.
  This is pattern-based protection applied at a single
  `sanitize_review_bundle()` boundary shared by the remote and manual reviewer
  paths - it is **not** a full data-loss-prevention system and cannot guarantee
  that no secret ever leaves the machine (the task diff is your own code).
- **No shell execution** of reviewer output or agent reports: commands come
  exclusively from the validated profile; all subprocesses use argv lists
  (`shell=False`) with byte-exact or explicitly decoded pipes.
- **No destructive git**: DevRelay never commits, pushes, merges, tags,
  resets, or touches the user's real index. Repository control state is
  snapshotted before/after every provider run and violations BLOCK the task;
  nothing is auto-repaired.
- **Reviewers only see the task delta**: Task Packet + task-relative diff +
  changed files + test evidence + reports (size capped), never the full
  repository. Pre-existing changes are never attributed as task additions;
  unified-diff context lines may still show surrounding pre-existing content.
- **Workspace boundary**: tasks operate only inside the initialized workspace.
- **Bounded automation**: fix loops capped, an execution budget caps every
  external provider call (pre-flight, never auto-reset), no auto git actions,
  and `BLOCKED` requires an explicit human `unblock` with a reason (including
  interrupted provider attempts and exhausted budgets).
- **Provider limits are stated, not hidden**: push prohibition is
  BEST-EFFORT/PROVIDER-LIMITED and documented as such.

## Current limitations (v0.1 core + v0.2-A candidate)

- The automatic review loop (v0.2-A) is a **candidate under independent
  review**: it is merged into no release, the version stays `0.1.0`, and the
  reviewed behaviour is exercised with fake providers only (no real Codex run
  and no real reviewer endpoint were used to validate it).
- The execution budget counts *invocations*, not tokens, cost, plan quota or
  provider-side billing - there is no billing integration in v0.2-A.
- One implementer: official Codex CLI (stdin transport). Codex argv/sandbox
  behavior must be validated on your machine (DevRelay rejects flags the
  installed CLI does not document).
- Codex structured event output (`--json` / `--output-schema`) is **not**
  parsed in v0.1 - recorded on the v0.2 roadmap. Exit codes and full stdout
  are captured today.
- One active task at a time; no concurrency.
- Repositories with unresolved merge conflicts are refused by the policy guard
  (fail closed) until the index is resolvable again; baseline capture itself
  still works in such repos.
- Real-git index byte-immutability is guaranteed for baseline/delta paths
  (tested); other git read commands use `--no-optional-locks` where possible.
- Secret redaction is best-effort pattern matching (see Security model), not a
  DLP guarantee.
- Test commands are profile-configured whole commands; no per-language
  auto-detection.
- OpenAI-compatible reviewer requires a JSON-object-capable endpoint.
- Push prohibition cannot be mathematically enforced with the current Codex
  CLI (no network-disable flag) - see the policy-guard section.
- No ChatGPT plugin / MCP / web UI / GitHub app yet - see Roadmap.

## Roadmap

- **v0.1** - local orchestration core with task baselines, task-relative
  deltas and repository policy guards
- **v0.2-A** - automatic review loop with an enforced execution budget,
  reviewer attempt lifecycle and fingerprint accounting (candidate under
  independent review)
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

219 tests run fully offline with mocked subprocesses/HTTP where needed and
real (tiny) git repositories for baseline/guard/recovery coverage - no real
Codex, DeepSeek or network required. Coverage includes: state transitions and
rejected invalid transitions; max-iteration blocking; P0/P1/P2 ->
FIX_REQUIRED; P3-only pass policy; Codex missing/success/failure/timeout;
stdin transport (long/Unicode/shell-metacharacter prompts stay on stdin, and
stdin/stdout are byte-exact - no newline translation);
config parsing and invalid config; artifact persistence and resume; dirty
workspace baselines (same-file user+agent edits, untracked, staged +
staged/unstaged mixes, deletions, renames, binary, Unicode and space
filenames, ignored files); byte-faithful `tracked.patch` (LF, CRLF and binary);
baseline tree reconstruction after a real `git gc --prune=now` for tracked
modify/delete/rename/binary/staged/CRLF changes; manifest and patch corruption
as explicit errors (never a HEAD fallback); real-index immutability; temp-index
cleanup; HEAD/branch/tag/index-mutation policy violations -> BLOCKED without
auto-repair; conflicted-index fail-closed (blocked before the provider runs);
provider exception / `KeyboardInterrupt` still persisting post-run evidence and
blocking auto-rerun after restart; reviewer payload and manual artifact
redaction; review request and final report separation of PRE-EXISTING vs TASK
changes; shell safety.

v0.2-A audit remediation adds: replay of a persisted review result after a crash
(zero external calls), single-application idempotency with durable applied
markers, durable task-scoped call/attempt/review identities, immutable
identity-keyed evidence, before/after policy-refresh evidence, truthful retry
phase labels, separator-normalized fingerprints, eagerly persisted
`policy_source` and read-only legacy `status`/`usage`.

v0.2-A adds: pre-flight budget refusal for implementer/reviewer/total limits
(no call is attempted once a limit is reached); exact call accounting for
success, format retry, transport failure and manually imported reviews; format
vs transport retry separation; response-size cap; sanitized HTTP error bodies
and model output; reviewer attempt lifecycle incl. the persisted in-flight
marker and fail-closed `interrupted_reviewer_attempt` recovery; policy
authority over a `PASS` decision that carries blocking findings; task policy
snapshot plus audited `unblock --refresh-policy`; repeated-finding
fingerprints/seen counts and the opt-in stall guard; automatic-fix handoff of
structured findings; state-schema migration with v0.1 fixture compatibility;
`status`/`usage`/`doctor` visibility (offline, zero-cost); and a full
engine-level fake-provider end-to-end loop (2 implementer + 2 reviewer calls
-> `FINAL_GATE_REQUIRED`, never automatic `DONE`); fail-closed recovery for a
review round that started but never finalized (acknowledged explicitly).

## License

MIT - see [LICENSE](LICENSE).
