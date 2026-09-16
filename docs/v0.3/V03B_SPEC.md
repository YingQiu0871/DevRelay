# DevRelay v0.3-B — MCP tool surface

Status: **candidate implementation complete — not released** (package version
stays `0.1.0`).  Accepted v0.3-A baseline: `bcf9627…` (documentation closeout
`f4c92f3…`).  Branch: `v0.3-b-mcp-tool-surface`.

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
* malformed MCP input cannot crash the process: the SDK answers with a protocol
  error and DevRelay never emits a traceback as protocol output.

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
| `opencode_calls` | read-only, local | `openWorldHint=false` | durable call ledger, strict about corruption |
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
| `opencode_calls` | `limit: integer` (1..200, default 20) |
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
no traceback, no secret.  Verified SDK fact (mcp 2.2.0): a JSON `true` sent for a
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

* **Concurrency**: v0.3-B serializes side-effecting operations
  (`opencode_send_prompt`, `opencode_interrupt`) per MCP server process with one
  narrow lock; read tools are not serialized and there is no scheduler.  Two
  concurrent submissions therefore cannot overlap (asserted by a test).
* **Cancellation**: cancelling the local MCP request does **not** cancel a model
  POST that was already issued, and it never implies "not submitted".  v0.3-B
  deliberately does not send an automatic `interrupt` on cancellation; the
  durable call ledger keeps the evidence, so the client must inspect
  `opencode_calls`/`opencode_read_messages` instead of resending.
* **Logging discipline**: stdout is MCP-only; stderr carries bounded, redacted
  operational diagnostics.  The MCP server invokes library APIs directly and
  never shells out to `devrelay opencode ...` (no CLI output parsing).
* **Secret containment**: outputs never contain `DEVRELAY_OPENCODE_TOKEN`,
  reviewer/provider API keys, `Authorization` headers, OpenCode Basic
  credentials, environment values, or the raw prompt.  The prompt is supplied by
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

## 9. What is *not* verified yet

* No real MCP client (ChatGPT or any other host) has been connected to this
  server yet: the acceptance evidence is offline (in-process matrix plus a real
  stdio subprocess against a deterministic loopback fake OpenCode server).
* No real MCP → OpenCode model call has been made in this round: real network /
  model calls = 0.  A later, separately authorized acceptance step can connect an
  actual MCP client and a disposable OpenCode session.
* Multi-process concurrency, Streamable HTTP/SSE transport, multi-workspace
  serving and any orchestration remain out of scope.

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
