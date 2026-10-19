# DevRelay v0.3-B — MCP tool surface

Status: **ACCEPT — v0.3-B CHATGPT/MCP TOOL SURFACE — accepted internally /
UNRELEASED; functional development CLOSED** (package version stays `0.1.0`;
public release remains `v0.1.0`).  Accepted functional candidate:
`d058d62341a173414bdba88fe357b08c236c8bb4`; final real MCP smoke:
`PASS — V0.3-B LOCAL REAL MCP SMOKE`.  This document reflects the remediation of
the independent review's `REQUEST_CHANGES — V0.3-B MCP TOOL SURFACE` findings
plus the concurrency remediation that followed the second re-gate.  Accepted
v0.3-A baseline: `bcf9627…` (documentation closeout `f4c92f3…`).  Branch:
`v0.3-b-mcp-tool-surface`.  Next stage: `v0.3-C` (role routing) — not started.

> Later status (2026-10-19): this stage was subsequently accepted and is part of the 0.3.0 release; the package version is now 0.3.0 and v0.3-C and later stages are no longer "not started".

## 1. Objective and boundary

Expose the **already accepted** v0.3-A OpenCode session bridge over the Model
Context Protocol so an MCP-capable client (for example a ChatGPT planner) can
invoke DevRelay programmatically:

```
ChatGPT / MCP client
        |
DevRelay MCP tool surface   (adapter: envelope, schemas, validation, stdio)
        |
accepted v0.3-A APIs        (OpenCodeBridge, durable ledger)
        |
OpenCode server             (unchanged; owns execution)
```

The MCP layer is an adapter.  It is **not** an execution engine, an
orchestration engine, a reviewer, an implementer, an approval authority or a
role router.  An MCP client may call several tools in sequence; DevRelay never
decides that sequence in v0.3-B.

### Explicit non-goals (v0.3-B)

DeepSeek/GLM role routing; planner/implementer/reviewer assignment; automatic
review or fix loops; task acceptance; autonomous retry; model fallback; WebUI;
browser control; local HTTP dashboard/API; Direct API Mode; embedded OpenCode;
multi-workspace orchestration; background agents; continuous monitoring; release
packaging; cloud deployment; Streamable HTTP/SSE MCP transport; v0.3-C/D work.

## 2. Transport: local stdio only

```bash
devrelay mcp serve --workspace <absolute-path-to-a-DevRelay-workspace>
```

* stdin/stdout carry MCP protocol traffic only; **diagnostics go to stderr**
  (bounded, redacted), and no startup banner or configuration dump is printed to
  stdout;
* no HTTP listener, no LAN exposure, no authentication server (stdio is a local
  pipe between the client and this process);
* the process exits cleanly on EOF/client disconnect and leaves no background
  worker or polling thread;
* malformed MCP input cannot crash the process, and the observed behaviour is
  recorded exactly (verified against the real stdio server, mcp 2.2.0):
  * a frame that is not parseable JSON, not JSON-RPC shaped, or a request without
    a `method` receives **no reply at all** - the SDK drops it, the process stays
    alive and keeps serving later requests;
  * an unknown method answers a JSON-RPC error `-32601 Method not found`;
  * a request with invalid/missing params answers `-32602 Invalid request
    parameters`.
  DevRelay does **not** emit its own protocol-error response for unparseable
  frames (it never claims one), and no traceback is ever produced as protocol
  output.

Streamable HTTP/SSE transport is deliberately **not** implemented in v0.3-B.

## 3. Bound-workspace model

One MCP server process is bound to **exactly one** DevRelay workspace:

* the path is resolved/canonicalized once at startup (`--workspace`), the
  workspace wiring/config is loaded then, and every later tool call operates
  inside that binding only;
* no tool accepts a workspace path, a `cwd`, a directory or any other way to
  reach outside the binding (asserted by tests against each tool's input schema);
* no disk scanning, no discovery, no cross-workspace switching; a session that
  belongs to another workspace still fails closed / stays hidden exactly as
  v0.3-A defines;
* an invalid workspace (missing, not initialized, unparsable or invalid wiring)
  **fails before serving tools** with exit code 2 and a stderr message.

## 4. Tool inventory (exact names)

| Tool | Kind | Annotations | Purpose |
| --- | --- | --- | --- |
| `devrelay_status` | read-only, local | `readOnlyHint=true`, `openWorldHint=false` | sanitized DevRelay/MCP status for the bound workspace |
| `opencode_health` | read-only | `readOnlyHint=true`, `openWorldHint=true` | `OpenCodeBridge.health()` |
| `opencode_list_sessions` | read-only | idem | sessions + ownership verdict (bound workspace only by default) |
| `opencode_get_session` | read-only | idem | one explicitly selected session |
| `opencode_read_messages` | read-only | idem | normalized message window + cursor semantics |
| `opencode_calls` | read-only, local | `openWorldHint=false` | durable call ledger, strict about corruption, numerically ordered |
| `opencode_send_prompt` | **side-effecting** | `readOnlyHint=false`, `destructiveHint=false`, `idempotentHint=false` | exactly one model turn through the accepted bridge |
| `opencode_wait_idle` | read-only | idempotent | bounded wait on `GET /session/status` |
| `opencode_interrupt` | **side-effecting** | `destructiveHint=true` | explicit abort request (never described as verified termination) |

No dangerous low-level tool exists: no arbitrary HTTP, shell, subprocess, file
read/write, Git, endpoint mutation, config editing, environment inspection,
ledger deletion, session deletion or token retrieval.

### Input schemas

| Tool | Arguments (all optional at the JSON-schema level; DevRelay validates) |
| --- | --- |
| `devrelay_status` | – |
| `opencode_health` | – |
| `opencode_list_sessions` | `include_other_workspaces: bool` (default false) |
| `opencode_get_session` | `session_id: string` |
| `opencode_read_messages` | `session_id: string`, `cursor: string` (opaque message id) |
| `opencode_calls` | `limit: integer` (1..200, default 20); records are ordered by **call number** (`OC-9999` sorts before `OC-10000`), and a file whose name does not follow `OC-<number>` is reported as a ledger error instead of being ranked |
| `opencode_send_prompt` | `session_id: string`, `prompt: string`, `agent: string`, `model: string` (`<providerID>/<modelID>`) |
| `opencode_wait_idle` | `session_id: string`, `timeout_seconds: number` |
| `opencode_interrupt` | `session_id: string` |

Every parameter is optional *in the schema* on purpose: DevRelay then owns the
validation and can answer with the envelope instead of an SDK-generated error
text.  Documented bounds:

* `prompt`: non-empty, ≤ **100 000** characters (control-plane abuse bound, far
  above a realistic coding prompt);
* `session_id`: the accepted v0.3-A opaque-identifier grammar
  (`[A-Za-z0-9._~-]{1,200}`, no traversal, no dot-only segment) - the same
  validator the bridge uses, never a second one;
* `cursor`: ≤ 200 characters;
* `agent`: ≤ 64 characters;
* `model`: the accepted `<providerID>/<modelID>` grammar (first `/` splits), mapped
  by the bridge to the real `{providerID, modelID}` wire object; an unmappable
  value fails **before any request**;
* `timeout_seconds`: finite, `> 0`, ≤ `min(opencode.idle_timeout_seconds, 600)`;
  an unlimited wait is not available;
* `limit`: integer `1..200`.

A value the SDK's own JSON-schema check rejects (for example a JSON object where
a string is required) is reported by the MCP SDK as a bounded validation error -
no traceback.  Honest limit: that SDK-generated text is **not** DevRelay-shaped
and may quote the offending caller-supplied value, so DevRelay does **not** claim
universal secret redaction on that SDK-level argument-validation path (recorded
as a non-blocking P2 in `docs/BACKLOG.md`); everything DevRelay itself shapes -
envelope, text fallback, diagnostics, durable evidence - stays bounded and
redacted.  Verified SDK fact (mcp 2.2.0): a JSON `true` sent for a
numeric parameter is coerced to `1.0` by the advertised schema, which is a
finite in-bounds wait; the "never unlimited" property is unaffected.

## 5. Result envelope

```json
{
  "schema_version": 1,
  "ok": true,
  "tool": "opencode_health",
  "data": { "...": "tool-specific, normalized DevRelay/Bridge fields" },
  "error": null
}
```

Failure keeps the same shape with `ok: false` and
`error: {"type": "<stable code>", "message": "<sanitized, bounded>"}`.

* **Envelope truthfulness (gate P1).** `ok` is true **only** when the accepted
  v0.3-A operation reached the success state that tool is defined to achieve -
  by default the bridge's own `result.ok` (`state is COMPLETED`), and for
  `opencode_interrupt` the accepted abort (`INTERRUPTED`, still carrying
  `interrupt_verified: false`).  Every bridge-backed tool derives its envelope
  from **one** rule in the tool layer (`McpToolSurface._bridge_envelope`), so a
  provider failure (HTTP error, malformed body, unreachable endpoint) can never
  be reported as `ok: true`, and `server.py` never special-cases `isError` per
  tool.  The protocol flag is mechanical: `isError == not envelope.ok`.
* `ok` describes **this tool call**, never a softened view of bridge state: an
  uncertain submission is `ok: false` with `data.submission_uncertain: true` and
  `data.reply_pending: true`.
* A failed envelope is delivered as an MCP result with `isError: true` **and**
  the complete envelope in `structuredContent` (plus a JSON text fallback), so a
  client that only checks the protocol flag still sees a failure while a client
  reading structured content keeps every nuance.
* `send_prompt` additionally carries `retry_safe`, derived only from documented
  evidence: `true` when no submission POST was issued, or when the POST failed
  without an HTTP response and without submission uncertainty (the v0.3-A
  "definitely not submitted" class).  An accepted submission (2xx, usable body or
  not), an uncertain submission and a pending reply are **never** `retry_safe`.
  The full truth table is asserted (`read`/`write` timeout, `read`/`write` error,
  remote protocol error, connect error, connect timeout, pool timeout, rejected
  status, `text/html` 2xx, accepted-unusable body, accepted pending, inline
  success, and a probe failure that never issued a POST).
* No tool ever returns a verdict such as "approved", "review passed" or "ready to
  merge": DevRelay v0.3-B has no acceptance authority, and the planner/arbiter
  stays outside this tool layer.

## 6. `send_prompt` semantics (P1 preservation)

`opencode_send_prompt` calls the accepted `OpenCodeBridge.send_prompt` - there is
no second HTTP path.  Everything v0.3-A guarantees therefore holds unchanged
through MCP: exactly one submission `POST /session/{id}/message`, no automatic
retry, no model fallback, no stale-reply substitution, `{info, parts}`
normalization, prompt redaction, durable accounting, `ReadTimeout`/`WriteTimeout`
→ **submission uncertain**, connect failures → **definitely not submitted**,
accepted-but-unusable body → accepted with `submission_body`.

The envelope never collapses `submission_uncertain` into "failed" or "safe to
retry"; the tool description tells the planner to inspect `submission_uncertain`
and `reply_pending` and to **not resubmit automatically**.

## 7. Concurrency, cancellation, logging, secrets

* **Test-harness candidate pinning**: every stdio child process is launched with
  `PYTHONPATH` pinned to the **checkout under test** (`<repo>/src`, absolute) and
  an environment stripped of `DEVRELAY_*`/`PYTHONPATH`/`PYTHONHOME`/
  `PYTHONSTARTUP`, so the suite can never silently exercise an ambient editable
  installation.  A mutation-propagation test copies the package, changes its
  server version and adds a marker to `devrelay_status`, and asserts the child
  advertises both - proving the executed tool code comes from the tree the
  harness points at.
* **Concurrency (remediated after the gate)**: v0.3-B serializes **all nine
  tool bodies** per MCP server process with exactly ONE process-scoped,
  re-entrant execution lock (`McpToolSurface._execution_lock`, a
  `threading.RLock`); there is no scheduler, no reader/writer lock and no second
  lock, so there is no lock order to get wrong.  The invariant is *at most one
  DevRelay MCP tool body may access the accepted v0.3-A bridge/ledger at a time
  within one MCP server process*.  This includes concurrent **reads**: every
  bridge request (including the ownership probe and the message read) allocates a
  durable `OC-*` identity through the accepted `FilesystemOpenCodeLedger`, whose
  allocation is a non-atomic read-modify-write over one fixed-name temp file and
  which refuses identity reuse - i.e. it is a single-writer store.  Before the
  remediation, 8 parallel `opencode_read_messages` calls on one server produced 7
  `internal_error`/`opencode_ledger_error` failures out of 8, colliding
  `OC-0001` identities and a truncated ledger; after it, the same batch returns
  8/8 success with 16 unique, settled, contiguously numbered call identities
  (asserted by `tests/test_v03b_mcp_concurrency.py`).  Consequences a client must
  expect: a long `opencode_wait_idle` body delays other tool calls in the same
  process, and cancelling an MCP request does not let another body overtake a
  still-running one.  `devrelay_status` reports `execution_serialized: true`.
  The `readOnlyHint` annotations are unchanged: they describe side-effect
  semantics, not concurrency.  Read concurrency can only be revisited together
  with a thread-/process-safe ledger (see BACKLOG), not by weakening this
  boundary.
* **Cancellation**: cancelling the local MCP request does **not** cancel a model
  POST that was already issued, and it never implies "not submitted".  v0.3-B
  deliberately does not send an automatic `interrupt` on cancellation; the
  durable call ledger keeps the evidence, so the client must inspect
  `opencode_calls`/`opencode_read_messages` instead of resending.
* **Logging discipline**: stdout is MCP-only; stderr carries bounded, redacted
  operational diagnostics.  The MCP server invokes library APIs directly and
  never shells out to `devrelay opencode ...` (no CLI output parsing).
* **Secret containment**: DevRelay-shaped outputs never contain
  `DEVRELAY_OPENCODE_TOKEN`, reviewer/provider API keys, `Authorization` headers,
  OpenCode Basic credentials, environment values, or the raw prompt.  (An
  SDK-generated JSON-schema rejection is bounded SDK text outside that shaping
  path; see the honest limit in section 4 and the recorded non-blocking P2 in
  `docs/BACKLOG.md`.)  The prompt is supplied by
  the MCP client and DevRelay cannot prevent that client from knowing it; the
  guarantees are: DevRelay does not log it unnecessarily, durable DevRelay
  evidence never stores the raw prompt text, error responses reuse the accepted
  sanitization, and a result only contains prompt text when it is the provider's
  own message content.  Durable records keep only `prompt_sha256` and
  `prompt_chars`.

## 8. Dependency

* Official MCP Python SDK (`mcp`), declared as the optional extra
  `devrelay[mcp]` with the constraint `mcp>=2.2,<3`; the `dev` extra includes it
  so the offline suite can run.  The upper bound is deliberate: in mcp 2.x
  `FastMCP` was renamed to `MCPServer` (`mcp.server.mcpserver.MCPServer`), which
  is the API this adapter was written and verified against.  No frontend/Node
  dependency is involved.
* The SDK is imported only when a server is actually built, so importing
  `devrelay` never requires the extra.
* Dependency direction: `devrelay.mcp` → `devrelay.opencode` (and config/models).
  `devrelay.opencode` must not import `devrelay.mcp`.

## 9. Verified in the final real smoke, and what stays out of scope

Verified end-to-end (one separately authorized one-shot smoke at candidate
`d058d62…`; `PASS — V0.3-B LOCAL REAL MCP SMOKE`):

* local **stdio MCP interoperability** with the official Python MCP SDK
  (`mcp 2.2.0`) — real `initialize`, real `tools/list` (exactly nine tools, in
  order) and real `tools/call`;
* `structuredContent` plus the JSON text fallback, and the bound workspace, over
  the wire;
* global-per-surface serialized execution observed at runtime
  (`execution_serialized: true`);
* real delegation to the accepted v0.3-A bridge over HTTP to a real
  **OpenCode 1.18.11** instance;
* real model tool invocation with the explicit model
  `opencode-go/deepseek-v4.1-flash` — exactly one MCP `opencode_send_prompt` and
  exactly one `POST /session/{id}/message`, no `/prompt`, no `prompt_async`, no
  retry, no fallback, provider inference confirmed by the provider log;
* truthful envelopes on the real path (`isError=false`, `ok=true`,
  `submission_uncertain=false`, `reply_pending=false`, `retry_safe=false`) with
  the correlated reply `DEVRELAY_V03B_MCP_OK` and a stable read window;
* real MCP ledger visibility (`opencode_calls`): every record settled, no
  `ISSUED`, unique contiguous call ids, exactly one model POST, and no raw prompt
  or credentials in durable evidence.

Not verified, unchanged non-claims (no product contract is added by the smoke):

* no HTTP/SSE MCP transport (stdio only), no WebUI, no multi-workspace serving,
  no role routing, no orchestration, no autonomous review/fix loop;
* ChatGPT product-native distribution/installation is **not** released, and no
  automatic DeepSeek/GLM routing exists;
* the automated suite still makes **0** real network/model calls; the real chain
  above was a manual one-shot smoke, not a repeatable CI job.

Boundary notes (unchanged by the smoke):

* Cancellation semantics are asserted at the boundary (no POST before the gate ⇒
  nothing recorded; cancellation around an issued POST ⇒ durable evidence stays
  inspectable, `retry_safe` is never claimed, no automatic resubmit, no automatic
  `interrupt`).  Cancellation cannot stop an already-running synchronous tool
  body, so the execution lock is released only when that body actually exits
  (asserted: a concurrent tool call stays blocked until then, and exactly one
  submission is ever issued).  Tool calls that arrive while another body holds
  the boundary wait on it inside MCP worker threads; no tool body ever calls
  another tool, so the boundary cannot deadlock, and the SDK's thread pool (not
  the lock) is the only fan-out limit.
* Multi-process concurrency, Streamable HTTP/SSE transport, multi-workspace
  serving and any orchestration remain out of scope.  The serialization
  boundary is **per MCP server process**: two `devrelay mcp serve` processes
  bound to the same workspace share one filesystem ledger and are NOT serialized
  against each other.  A single-writer ledger (lock file or atomic compare-and-
  swap identity allocation) is required before that is claimed.

## 10. Minimal local setup

```bash
# 1. one DevRelay workspace (already initialized)
cd /path/to/project
devrelay init                     # once, if needed
# 2. configure the OpenCode endpoint in .devrelay/config.yaml
#    opencode: { base_url: "http://127.0.0.1:4096" }
# 3. serve the MCP tool surface over stdio for that ONE workspace
devrelay mcp serve --workspace /path/to/project
```

An MCP client then configures a stdio server with exactly that command line.  The
server prints nothing on stdout except protocol frames; failures appear on stderr
with exit code 2 before any session starts.
