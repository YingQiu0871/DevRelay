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
  max_messages: 50             # read window size (1..200, the wire-level hard maximum)
  allow_unknown_workspace: false   # true = accept sessions that report no workspace (unsafe, documented)
```

* The endpoint is **explicit**; DevRelay never scans ports or processes.
* `base_url` must be unambiguous, because it is a bearer-token control channel:
  `http`/`https` only, a host is required, embedded credentials are refused (the
  token comes from the environment), and a path prefix, query or fragment is
  refused rather than silently dropped.  The authority is validated explicitly:
  a non-numeric, duplicated or out-of-range port, whitespace/control characters
  and percent-encoding inside the authority are configuration errors - never an
  `httpx.InvalidURL` at request time.  Embedded credentials are removed from the
  value *before* validation, so no error message, log or console line can echo a
  password.  A trailing `/` is normalized away; an
  empty value means "not configured" (the section is inert until it is set).
* Numeric limits fail closed at load time instead of being clamped at request
  time: `timeout_seconds`/`idle_timeout_seconds`/`poll_interval_seconds` must be
  `> 0`, `max_response_bytes` is bounded to `1 KiB .. 32 MiB`, and `max_messages`
  is bounded to `1 .. 200` (200 is the wire-level window; there is no server
  pagination in v0.3-A, so a larger window could not be honoured).
* An empty YAML body (`opencode:` with nothing under it) means "not configured"
  and falls back to the field defaults.  An unknown key inside the section is
  still rejected (`extra="forbid"`): a typo must never be ignored.
* Provider error snippets are scrubbed of the bearer token and of the prompt that
  was just submitted - in their literal form *and* in the encodings a provider
  realistically echoes (JSON-escaped, backslash-escaped, percent-encoded and their
  once/twice-escaped forms).  This applies to the submission POST, the follow-up
  read and every wait/poll request, and it happens *before* the snippet can reach
  the ledger, the result or the console.
* `DEVRELAY_OPENCODE_TOKEN` (environment only) is sent as a bearer token when set.
  It is never written to the config, the policy snapshot, the call ledger or any
  artifact, and `doctor` reports presence, not value.
* The token is also in `CODEX_CHILD_ENV_DENYLIST`: **every** Codex child process
  never inherits it.  The scrub is centralized in a runner adapter
  (`CodexChildRunner`) that the Codex provider spawns through, so the legacy text
  runtime, the probes (`--version`, `exec --help`), capability detection and the
  doctor path are all covered without each call site remembering it - and the
  parent DevRelay process keeps its credentials.  A child holding the credential
  could bypass the bridge entirely.
* The section is runtime wiring: `devrelay init` writes it disabled (empty
  `base_url`), and it is excluded from the frozen task policy exactly like
  `codex:` is (a legacy full-config snapshot may still contain it; the policy
  reader drops it as a known wiring key).

## Bridge surface

| Method | Semantics |
| --- | --- |
| `health()` | probe the endpoint; returns normalized `OpenCodeHealth` (healthy/version/capabilities). No session data. |
| `list_sessions(include_other_workspaces=False)` | normalized sessions, each carrying its ownership verdict; other-workspace sessions are hidden unless explicitly requested. |
| `get_session(session_id)` | read one explicitly selected session; unknown id → `opencode_session_not_found`; wrong workspace → `opencode_session_workspace_mismatch` (hard failures); a session id the server answers with that is not the requested one → `MALFORMED_RESPONSE` (never "adopt" another session). |
| `read_messages(session_id, cursor=None)` | normalized message window + explicit cursor semantics (`next_cursor`, `cursor_unknown`, `replayed`).  The **newest** messages win at every level: the anti-DoS pre-cap keeps the newest `2000` provider entries and the window is the newest `max_messages` of those, while `provider_message_count`/`window_truncated` report what the payload actually contained. |
| `send_prompt(session_id, prompt, agent="", model="")` | exactly one prompt to exactly one session.  **Submission acceptance is the HTTP status**: any 2xx means the server may have accepted the prompt, so an unusable body (`204`, empty `200`, invalid JSON, oversized) is recorded as evidence (`submission_body`, `submission_status`) and the operation continues as a post-acceptance result - never as "not submitted", never resubmitted.  A reply is correlated **only** as a new assistant message (inline candidate, or exactly one explicit follow-up read); no visible new reply yields `reply_pending: true` with `messages: []` and `page: null`, so a pre-submission message can never be read as the answer. |
| transport-timeout semantics | the POST outcome is classified, not guessed.  A failure that proves no connection was established (`connect_timeout`, `pool_timeout`, `connect_error`, local/proxy refusals) is **not submitted**: `submission_attempted: true`, `submission_status: null`, `submission_uncertain: false`, `reply_pending: false`.  A failure that may happen after the request bytes were sent (`read_timeout`, `write_timeout`, read/write errors, remote protocol errors, and anything unclassified) is **submission-uncertain**: `submission_uncertain: true`, `reply_pending: true` unless a new assistant reply is correlated, explicit "may already have been accepted; do not resubmit automatically" text, exactly one bounded follow-up read, and never a POST retry. |
| `wait_idle(session_id, timeout=None, *, redact_values=())` | bounded polling until idle/terminal; the deadline is established **before** the ownership probe and every request (probe included) is clamped to the remaining budget; `TIMED_OUT` on expiry — no retry, no continued polling. |
| `interrupt(session_id)` | abort request; 2xx (including an empty `204`) → `INTERRUPTED` with `interrupt_verified: false` (accepted is not verified), `404` → `interrupt_session_not_found`, `405`/`501` → `interrupt_unsupported`, any other failure → the provider error, and an oversized/unusable body → `MALFORMED_RESPONSE` (never "unsupported"). |

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
ACCEPTED_LOCALLY      reserved - never emitted (local validity failures are hard
                      errors, not a state)
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
* **Untrusted response content never escapes** as a Python exception: invalid
  JSON (`invalid_json`), extreme nesting (`json_too_deep`, `RecursionError`) and
  unparsable values such as an over-long integer literal (`json_unparsable`,
  `ValueError`) all normalize into `MALFORMED_RESPONSE`, and the durable call
  record is settled in every case (it is never left `ISSUED`).  A programming
  error in DevRelay's own code still propagates: only provider-controlled
  parsing failures are normalized.

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
* Session ids are treated as **opaque**: `[A-Za-z0-9._~-]{1,200}` with `..`
  refused, since the id is interpolated into a URL path.  Anything that could
  change that path (`/`, `?`, `#`, whitespace, control characters, traversal,
  overlong values) is rejected before a request is constructed → no request is
  issued at all.  Every acting operation additionally verifies that the session
  the server answers with is the session that was requested (a mismatch is
  `MALFORMED_RESPONSE`, never "adopt the session you got").

## Timeout semantics

* `timeout_seconds` bounds every single HTTP request (connect+read) when a caller
  issues one directly (`health`, `sessions`, `show`, `read`, `send`, `interrupt`).
* `idle_timeout_seconds` (or the explicit `timeout=`) bounds the **whole**
  `wait_idle` operation, enforced from before the ownership probe: the deadline is
  computed first, every request (the probe included) receives at most the
  remaining budget as its per-request timeout, and the inter-poll sleep is clamped
  to what is left.  No request can outlive the deadline, and no request is issued
  once the remaining budget is exhausted (a zero budget issues no request at all).
* Expiry yields `TIMED_OUT` with the last observed session state, the actual
  whole-operation `duration_ms` (the sum of the accounted calls) and **no**
  automatic retry or continued polling after the return.
* Transport failures are classified by stage, never by exception text: a
  connect/pool timeout, connect error or local refusal is *not submitted*; a
  read/write timeout, a read/write error or a remote protocol error may have
  happened after the request bytes reached the server, so a POST that fails that
  way is reported as *submission-uncertain* (see the bridge surface).  Unclassified
  transport failures default to uncertain: a caller is never told "safe to retry"
  on a guess.
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
  issued (ownership probe + boundary read + submission + explicit follow-up read
  + every `wait_idle` poll), and `call_ids` lists them.  A follow-up that fails
  *after* issuing requests still merges those calls, so operation accounting and
  ledger accounting always agree.
* Allocation fails closed: a corrupt/torn `sequence.json` raises
  `opencode_ledger_error` instead of restarting numbering, a missing sequence is
  recovered from the existing records (`max(existing) + 1`), each record is
  opened create-new *before* it is added to the in-memory view (a refused
  identity leaves no phantom call that could inflate elapsed totals), and a crash
  gap is acceptable while reuse is not.
* Call ids are unique and monotonic under the supported **single-process** model:
  there is no cross-process locking, so two DevRelay processes writing the same
  `.devrelay/opencode/` directory concurrently are outside the v0.3-A contract.
* `duration_ms` is the sum of the accounted calls' durations, so it measures time
  spent in requests and deliberately excludes the local inter-poll sleeps.
* The persisted `prompt_sha256` is an **unsalted** digest: an identifier for
  correlating a call with the prompt that produced it, not a secrecy mechanism (a
  guessable prompt is confirmable from the ledger).  Prompt confidentiality comes
  from never storing the text.
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
* `read_messages` has no server-side pagination: the local window is the newest
  `max_messages` (hard cap 200, anti-DoS pre-cap 2000 provider entries) and
  truncation is reported, not worked around.
* Message ordering is assumed to be the provider's own order (newest last) -
  DevRelay does not re-sort messages by timestamp, so a provider that returns
  them in another order would be reported as-is; cursor semantics stay honest
  (`cursor_unknown`) instead of guessing.
* `interrupt_verified: false` always means "the abort request was accepted", not
  "a terminal state was observed"; v0.3-A performs no post-abort verification
  polling.
* Call ids are only guaranteed unique under the single-process model (see Call
  accounting); cross-process locking is deferred.
* Provider-error scrubbing is bounded by construction: literal plus JSON/
  backslash/percent encodings up to two escaping levels.  A provider that
  paraphrases, fragments or differently encodes a secret is outside this
  boundary.
* Wire paths (`OpenCodePaths`) are code-level defaults, not configuration keys:
  v0.3-A exposes no `opencode.paths` setting.
* Prompt/credential scrubbing of provider error snippets is **literal-value**
  based: DevRelay removes the values it knows (the bearer token, and the prompt it
  just submitted - including in post-submission follow-up reads and polls), so a
  provider that *paraphrases* a prompt in an error body is out of scope.
* Workspace ownership compares paths in DevRelay's own namespace.  A provider that
  reports a different namespace (container, remote host, Windows drive mapping)
  cannot be matched automatically; such a session fails closed unless
  `allow_unknown_workspace` is set explicitly.
* `base_url` must not contain a path prefix, so a reverse-proxy prefix needs an
  explicit, reviewed change instead of a silently dropped path.
* Ambient proxy/CA environment variables (`HTTP_PROXY`, `HTTPS_PROXY`,
  `SSL_CERT_FILE`, ...) are ignored outright for the control channel
  (`trust_env=False`); DevRelay has no reviewed proxy configuration mechanism, so
  there is nothing to configure yet.
* CLI exit codes: `0` means the command achieved what was asked (`COMPLETED`, or
  `INTERRUPTED` for `interrupt`), `2` means any other outcome - including
  `reply_pending` (the prompt was accepted but no reply was visible) and
  `submission_uncertain` (even when a reply was later correlated, because the
  submission itself is unconfirmed) - in both human and `--json` output.
* Human `send_prompt` output states the submission verdict explicitly
  ("submission accepted", "submission uncertain ... do not resubmit
  automatically", "submission rejected (HTTP nnn)" or "submission not accepted")
  and the reply state ("reply pending: no new assistant message was confirmed"),
  and never prints a pre-submission message as the answer.
