# DevRelay v0.3-A — OpenCode session bridge

Status: **CURRENT — candidate for independent review** (stage A of v0.3 only;
v0.3-B and later are NOT STARTED).

## Objective (and its hard boundary)

Establish a narrow, testable, provider-contained bridge between DevRelay and an
**already running** OpenCode server/session:

1. address one explicitly configured OpenCode endpoint;
2. list sessions;
3. read one explicitly selected session;
4. retrieve new assistant/session output;
5. send exactly one prompt to one explicitly selected session;
6. wait for idle/terminal with a bounded timeout;
7. return a normalized DevRelay-owned representation;
8. interrupt/cancel when the server supports it;
9. fail closed when the endpoint/session/capability is unavailable or inconsistent.

**v0.3-A performs no autonomous orchestration**: no "continue until approved"
loop, no role routing (DeepSeek → GLM is NOT implemented), no approval decision
inside DevRelay, no ChatGPT/MCP exposure, no WebUI. The bridge answers questions
and returns normalized results; deciding anything remains a human/pipeline
concern.

## Provider boundary

```
devrelay/cli.py            → only `app.add_typer(opencode_app)` (no OpenCode logic)
devrelay/cli_opencode.py   → argument parsing + printing of normalized results
devrelay/opencode/bridge.py       → the capability surface + ownership validation
devrelay/opencode/transport.py    → HTTP: one endpoint, one attempt, bounded reads
devrelay/opencode/accounting.py   → durable per-request call ledger
devrelay/opencode/models.py       → normalized DevRelay-owned models
```

No pipeline/engine code knows about OpenCode; nothing in `devrelay.opencode`
imports the pipeline. Wire-format objects never leave the package.

## Configuration (runtime wiring, never task policy)

```yaml
opencode:
  base_url: ""                 # REQUIRED to use the bridge, e.g. http://127.0.0.1:4096
  workspace: ""                # defaults to this repository root
  default_session: ""          # convenience only; every operation still takes an explicit id
  agent: ""                    # optional default agent selection
  model: ""                    # optional default model selection
  timeout_seconds: 30          # per HTTP request
  idle_timeout_seconds: 300    # bound for wait_idle
  poll_interval_seconds: 1.0   # wait_idle polling cadence
  max_response_bytes: 1048576  # hard cap: larger responses fail closed, never truncated-and-parsed
  max_messages: 50             # read window size
  allow_unknown_workspace: false   # true = accept sessions that report no workspace (unsafe, documented)
```

* The endpoint is **explicit**; DevRelay never scans ports or processes.
* `DEVRELAY_OPENCODE_TOKEN` (environment only) is sent as a bearer token when set.
  It is never written to the config, the policy snapshot, the call ledger or any
  artifact, and `doctor` reports presence, not value.
* The section is runtime wiring: `devrelay init` writes it disabled (empty
  `base_url`), and it is excluded from the frozen task policy exactly like
  `codex:` is (a legacy full-config snapshot may still contain it; the policy
  reader drops it as a known wiring key).

## Bridge surface

| Method | Semantics |
| --- | --- |
| `health()` | probe the endpoint; returns normalized `OpenCodeHealth` (healthy/version/capabilities). No session data. |
| `list_sessions(include_other_workspaces=False)` | normalized sessions, each carrying its ownership verdict; other-workspace sessions are hidden unless explicitly requested. |
| `get_session(session_id)` | read one explicitly selected session; unknown id → `opencode_session_not_found`; wrong workspace → `opencode_session_workspace_mismatch` (hard failures). |
| `read_messages(session_id, cursor=None)` | normalized message window + explicit cursor semantics (`next_cursor`, `cursor_unknown`, `replayed`). |
| `send_prompt(session_id, prompt, agent="", model="")` | exactly one prompt to exactly one session; returns the normalized assistant reply when the server provides one (ack-only servers trigger exactly one explicit follow-up read). |
| `wait_idle(session_id, timeout=None)` | bounded polling until idle/terminal; `TIMED_OUT` on expiry — no retry, no unbounded wait. |
| `interrupt(session_id)` | abort; `INTERRUPTED` on success, `PROVIDER_UNAVAILABLE` + `interrupt_unsupported` when the server cannot abort (never claims a cancellation that did not happen). |

`devrelay opencode health|sessions|show|read|send|wait|interrupt|calls` are thin
wrappers over these methods; `send --wait` composes send → wait → read without
retrying anything.

## Normalized models

`OpenCodeHealth`, `OpenCodeSession` (id, workspace + `workspace_known`/
`workspace_match`, title, `OpenCodeSessionState`, agent, model, updated_at,
parent_id), `OpenCodeMessage`/`OpenCodeMessagePart` (text sanitized and capped;
tool parts keep the tool *name* only), `OpenCodeMessagePage` (cursor semantics),
`OpenCodeOperationResult` (state, ids, counts, timings, http status, error),
`OpenCodeCallRecord` (accounting). All textual fields pass the shared
`redact.sanitize` boundary and size caps before they can reach the console or an
artifact; the raw transcript is never persisted.

## State and error model

Operation states (explicit, never inferred):

```
ACCEPTED_LOCALLY      validated locally, nothing issued
ISSUED                an external request has been sent
IN_FLIGHT             still running on the server (wait_idle)
COMPLETED             terminal/idle outcome reached
TIMED_OUT             the bounded wait expired (no retry)
INTERRUPTED           an in-flight operation was aborted on request
PROVIDER_UNAVAILABLE  transport failure, HTTP error, abort unsupported, endpoint unset
MALFORMED_RESPONSE    unexpected/oversized/empty/invalid-JSON payload
```

Split of responsibilities, deliberately:

* **Provider conditions are returned** as a result state (a caller cannot mistake
  a timeout or an unreachable server for success).
* **Hard validation failures raise**: missing configuration
  (`opencode_config_invalid`), unknown session (`opencode_session_not_found`),
  workspace mismatch (`opencode_session_workspace_mismatch`).

Per-request call states: `ISSUED → COMPLETED | TIMED_OUT |
PROVIDER_UNAVAILABLE | MALFORMED_RESPONSE`.

## Workspace / session ownership

* Every operation resolves the session first and validates ownership **before**
  sending anything: the session's reported workspace (normalized absolute path)
  must equal the configured workspace root.
* A session that reports **no** workspace fails closed, because ownership cannot
  be proven; `allow_unknown_workspace: true` is the explicit, documented, unsafe
  opt-in.
* Cross-workspace reuse is refused with a hard failure — never silently retried,
  never rewritten, never "adopted".
* `list_sessions` shows the verdict per session and hides foreign sessions unless
  `--all-workspaces` is passed.

## Timeout semantics

* `timeout_seconds` bounds every single HTTP request (connect+read).
* `idle_timeout_seconds` (or `--timeout`) bounds the whole `wait_idle` operation;
  expiry yields `TIMED_OUT` with the last observed session state, and **no**
  automatic retry or continued polling.
* A request that times out is recorded as `TIMED_OUT` in the ledger and counts as
  one issued request.

## Call accounting

* One issued HTTP request = one `OpenCodeCallRecord` with a durable, monotonic,
  never-reused id (`OC-0001`, allocated from `.devrelay/opencode/sequence.json`
  *before* the request leaves the machine).
* Records live at `.devrelay/opencode/calls/<call-id>.json` and are settled in
  place (same call id); `devrelay opencode calls` shows them.
* A record never contains prompt text, transcripts, environment values or
  credentials — only operation, method/path, session id, state, counts, timings,
  http status, error type/sanitized error and a prompt hash/length.
* `OpenCodeOperationResult.request_count` counts **every** request the operation
  issued (ownership probe + submission + explicit follow-up read + every
  `wait_idle` poll), and `call_ids` lists them.
* **No hidden retries**: exactly one attempt per request, no automatic retry of a
  failed or timed-out operation, and v0.3-A does not touch the implementer/
  reviewer provider budget (`ProviderCallRecord` remains the only budget
  authority for those roles).

## Known limitations

* Polling `wait_idle` (no SSE/stream subscription yet).
* Wire paths are configurable defaults (`OpenCodePaths`), matching the documented
  OpenCode server shape; the exact contract needs a real smoke to confirm.
* Only text/tool-name parts are normalized; tool arguments and file attachments
  are deliberately dropped.
* The bridge is not wired into the pipeline: it cannot implement, review, approve
  or advance a task, and it makes no decisions.
* No MCP/ChatGPT exposure, no role routing, no orchestration (see non-goals).
