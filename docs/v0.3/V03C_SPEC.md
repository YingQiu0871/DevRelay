# DevRelay v0.3-C — agent role routing

Status: **ACCEPTED / CLOSED / UNRELEASED** — `ACCEPT — DEVRELAY v0.3-C AGENT
ROLE ROUTING` (accepted internally; package version stays `0.1.0`; public release
remains `v0.1.0`; next stage `v0.3-D` not started).  Accepted functional
candidate: `eabb667d1bd9e379d3b7105d72b6a2751bc2a32b`, verified by two bounded real
role-routing runs (implementer → `opencode-go/deepseek-v4.1-flash`, reviewer →
`opencode-go/glm-5.3-flash`).  Accepted baselines this stage builds on: v0.3-A
OpenCode session bridge (`bcf9627…`) and v0.3-B MCP tool surface (`d058d62…`,
documentation closeout `c883bab…`).  Branch: `v0.3-c-agent-role-routing`.

## 1. Objective and boundary

An MCP caller (for example a ChatGPT planner) selects a **semantic role**;
DevRelay resolves that role to the exact route its workspace configures and sends
one model turn through the accepted v0.3-A bridge.

```text
ChatGPT / Planner
       | MCP (stdio)
DevRelay v0.3-C role router      (semantic role -> configured route)
       |
resolved role configuration      (model, optional agent; identifiers only)
       |
accepted v0.3-B / v0.3-A layers  (tool surface, envelope, execution lock, bridge)
       |
OpenCode 1.18.11
       |
configured provider/model
```

The caller selects a role.  DevRelay supplies the model and the optional agent.
The caller **cannot** supply a different model or agent in a role-aware call.

## 2. Explicit non-goals (v0.3-C)

v0.3-C routes; it does **not** orchestrate.  Not implemented, not planned here:

* automatic implementer -> reviewer sequencing, reviewer -> implementer repair
  loops, bounded orchestration loops, retry loops;
* automatic acceptance, automatic rejection, merge decisions, model scoring or
  ranking, model fallback, candidate model lists, load balancing;
* a Planner role inside DevRelay, session creation or session lifecycle
  management, automatic session-per-role provisioning;
* multi-workspace orchestration, WebUI, HTTP control API, Direct API mode, cloud
  deployment, v0.3-D functionality.

The external Planner/Arbiter still decides **which** role to invoke, **when**,
**what** prompt to send and whether another role should run afterwards.

## 3. Authority boundary (critical)

DevRelay never decides that an implementation is approved, rejected, accepted,
ready to merge, correct or "passed review":

* the `reviewer` role routes a prompt to the configured reviewer model and
  returns provider text;
* reviewer output such as `APPROVE` or `REQUEST_CHANGES` is **never** interpreted
  as an execution command: it triggers no acceptance, no rejection, no repair and
  no role switch;
* an implementer never self-approves, and a reviewer never triggers remediation
  automatically.  The external Planner remains authoritative.

The role envelopes therefore contain routing and submission evidence only - no
`decision`, `verdict`, `approved`, `accepted` or `next_action` field exists.

## 4. Role vocabulary and configuration

Exactly two roles exist in v0.3-C: `implementer` and `reviewer`.  There is no
generic arbitrary-role plugin system yet and no vendor or model identifier is
hard-coded in DevRelay: which provider/model plays which role is workspace
configuration.

```yaml
# .devrelay/config.yaml (runtime wiring, never task policy)
roles:
  implementer:
    model: "providerID/modelID"     # required to enable the role
    agent: null                     # optional (accepted v0.3-A agent semantics)
  reviewer:
    model: "providerID/modelID"
    agent: null
```

* `model` uses the accepted `<providerID>/<modelID>` grammar (split at the first
  slash) - the *same* mapper the bridge uses, so the role path can never parse a
  model differently from the raw path;
* `agent` is optional; an omitted agent means "leave the member out of the
  request", never an empty-string agent;
* the section is optional.  When it is absent (or a model is empty) the
  role-aware tools fail locally with `role_unconfigured` and every v0.3-B tool
  keeps working unchanged - `devrelay mcp serve` never refuses to start because
  role routing is absent;
* role definitions cannot contain prompts, shell commands, environment variables,
  endpoint/workspace overrides, retry policies, fallback models, candidate lists
  or credentials: those keys are rejected by the configuration schema.

Role routes are **runtime wiring**, never task policy: they are excluded from
`workspace_policy_overrides` and dropped (with a recorded reason) when a legacy
full-config dump is parsed leniently, exactly like `opencode`/`codex`.

## 5. Resolution semantics

`resolve_role(role)` is a pure function of configuration:

* matching is **exact** (surrounding whitespace only): no case folding, no alias,
  no prefix or similarity match, no ranking and no availability probe;
* a role is never inferred from prompt text, session title, ordering or model
  availability; an omitted or blank role is `role_unknown`;
* the resolved route is a frozen value object `RoleRoute(role, model, agent,
  source)` where `source` is always `workspace_config`;
* failure taxonomy (all local, before any request that could submit a model turn):

| Condition | Error code |
| --- | --- |
| role not in `{implementer, reviewer}`, omitted or blank | `role_unknown` |
| role supported but no configured model (absent/blank) | `role_unconfigured` |
| configured model/agent cannot be mapped exactly | `role_invalid_route` |

These are *routing* failures and are never reported as provider failures;
conversely an accepted bridge failure (workspace mismatch, provider unavailable,
malformed response, submission uncertain) keeps its own code.

## 6. Role-aware execution

```text
send_role_prompt(role, session_id, prompt)      # library level
```

1. validate and resolve the role (local; a failure issues no request at all);
2. validate `session_id`/`prompt` with the accepted v0.3-A rules;
3. call the accepted `OpenCodeBridge.send_prompt` with the resolved `model` and
   the resolved optional `agent`;
4. preserve **all** accepted v0.3-A send semantics unchanged (exactly one
   `POST /session/{id}/message`, never a retry, never a fallback, never an
   automatic resubmission, `submission_uncertain`/`reply_pending` reported as
   evidence, `retry_safe` true only when nothing was submitted);
5. return routing metadata **plus** the existing send evidence.

There is no second HTTP submission path in v0.3-C.  The role router contains no
HTTP, no shell and no session state; it cannot create sessions, cannot pick a
session and cannot remember one.

### Caller cannot override the route (P1 invariant)

The role-aware send accepts `role`, `session_id` and `prompt` **only** - no
`model`, no `agent`, no `workspace`, no endpoint and no retry flag exists in the
signature or in the advertised MCP input schema.  Supplying such a key anyway has
no effect: the configured route still reaches the wire (asserted on the wire, the
ledger and the envelope).

## 7. Raw path vs role path (backward compatibility)

| Path | Tool | Route supplied by |
| --- | --- | --- |
| raw / low-level | `opencode_send_prompt` (v0.3-B, unchanged) | the caller (`model`, optional `agent`) |
| role-aware | `devrelay_send_role_prompt` (v0.3-C) | the workspace configuration for the selected role |

The raw tool is never redirected through role routing, never rewritten and never
deprecated: it keeps its caller-supplied model/agent behavior and its envelope
carries no role key.  Both paths may be used in the same session, and both keep
the accepted exactly-one-submission semantics.

## 8. MCP tool surface (12 tools)

The accepted v0.3-B nine tools are unchanged and keep their order; exactly three
are appended:

| # | Tool | Kind | Input |
| --- | --- | --- | --- |
| 10 | `devrelay_list_roles` | read-only | none |
| 11 | `devrelay_get_role` | read-only | `role` |
| 12 | `devrelay_send_role_prompt` | side-effecting | `role`, `session_id`, `prompt` |

* `devrelay_list_roles` returns the supported roles and, per role, the configured
  model/agent or its truthful `unconfigured`/`invalid` state (identifiers only,
  never a secret);
* `devrelay_get_role` returns the exact normalized route or a local typed error;
* `devrelay_send_role_prompt` sends one model turn as the selected role.

Descriptions are part of the LLM control surface: the role-send description
states that the caller selects a semantic role, that DevRelay resolves the exact
configured model/agent, that the route cannot be overridden, that it is exactly
one model turn with no retry and no automatic role switch, that
`submission_uncertain`/`reply_pending`/`retry_safe` must be inspected before
deciding anything, and that reviewer output is provider text rather than an
acceptance decision.  `MCP_SERVER_VERSION` is `0.3.0-c` (the advertised surface
changed from nine to twelve tools).

## 9. Execution serialization (unchanged boundary)

The accepted v0.3-B rule still holds: **all** tool bodies go through the one
per-surface `_execution_lock` (`_execute` is the single choke point), because the
accepted v0.3-A filesystem ledger is a single-writer store.  v0.3-C adds no role
lock, no bridge lock and no scheduler: one MCP surface -> one serialized boundary
-> all twelve tools, reads and role sends alike.  A long `opencode_wait_idle` (or
a role send whose reply is being correlated) therefore still delays other calls
in the same process.

## 10. Envelopes and auditability

The stable envelope is preserved (`schema_version`, `ok`, `tool`, `data`,
`error`; a failed envelope also sets the protocol `isError` flag).  A successful
role send adds routing evidence to `data`:

```json
{
  "role": "reviewer",
  "resolved_model": "providerID/modelID",
  "resolved_model_identity": {"providerID": "providerID", "modelID": "modelID"},
  "resolved_agent": "review",
  "route_source": "workspace_config",
  "role_routing": "semantic role resolved to the workspace-configured route; ...",
  "... accepted send_prompt evidence (state, call_ids, request_count,": "...",
  "... submission_attempted/status/uncertain, reply_pending, retry_safe, messages ...": "..."
}
```

A planner can therefore always answer: which semantic role was requested, which
model was selected, which agent was selected, whether the model POST occurred,
whether the submission is uncertain, and which OpenCode call ids belong to it.
The evidence states **configured routing** - never which model "should" be used.
An accepted bridge failure keeps its exact code/message and additionally reports
the attempted route, so routing stays auditable on the failure path too.

## 11. Failure semantics

| Situation | Behavior |
| --- | --- |
| unknown/omitted role | local `role_unknown`; no OpenCode request at all |
| unconfigured role | local `role_unconfigured`; no OpenCode request |
| malformed configured model/agent | local `role_invalid_route`; no OpenCode request |
| invalid session id / prompt | accepted `mcp_invalid_argument`; no request |
| workspace/session mismatch | accepted v0.3-A ownership failure; no submission |
| provider/model unavailable | accepted provider failure semantics preserved; never a silent role/model switch |
| uncertain submission | `submission_uncertain=true`, `retry_safe=false`, never auto-resubmitted |

## 12. Session policy

v0.3-C does **not** create, bind, infer or remember sessions.  Every role-aware
send requires an explicit `session_id` and the accepted v0.3-A workspace
ownership rules apply unchanged.  A reviewer session is never inferred from an
implementer session and no second session is ever created automatically.
Separate role sessions may be an operational convention, but session-management
policy belongs to a later stage.

## 13. Secret and logging boundary

Role configuration carries identifiers only (schema-enforced).  No role-aware
output exposes provider keys, `Authorization` headers, OpenCode credentials,
environment values or the raw prompt; durable evidence keeps only
`prompt_sha256`/`prompt_chars`.  Known accepted limitation, unchanged and not
broadened: an SDK-generated JSON-schema rejection is bounded SDK text outside
DevRelay's shaping path and may quote the offending caller value (recorded as a
non-blocking P2 in `docs/BACKLOG.md`).

## 14. Dependency direction

```text
devrelay.mcp           -> decoupled from: nothing new (imports roles)
devrelay.roles         -> devrelay.errors, devrelay.opencode (grammar only)
devrelay.opencode      -> must NOT import devrelay.roles (asserted by test)
```

The role router never imports MCP; the accepted bridge never imports roles and
contains no role/vendor knowledge.  Asserted by AST import analysis in
`tests/test_v03c_roles.py`.

## 15. Verified in the real role-routing smoke, and what stays out of scope

Verified by two bounded real runs (one explicit role turn each; see
`docs/v0.3/V03C_ACCEPTANCE.md` sections I.1-I.3):

* the two semantic roles and the `roles:` workspace wiring (exact
  `<providerID>/<modelID>` routes, optional agent, absent section valid);
* exact, deterministic route resolution and the local error taxonomy;
* the role-aware MCP send over the **official stdio MCP boundary** (12 tools,
  real `initialize`/`tools/list`/`tools/call`, `execution_serialized: true`);
* **call-time route override resistance** on the real path (the effective route
  came from configuration, never from a caller-supplied field);
* truthful role metadata (`role`, `resolved_model`, `resolved_model_identity`,
  `resolved_agent`, `route_source`) agreeing with the provider log;
* **exactly one submission per role call** with no retry, no fallback and no
  alternative model;
* **no orchestration**: an implementer completion did not invoke the reviewer, and
  the reviewer completion triggered nothing;
* **two distinct real provider/model routes**: implementer →
  `opencode-go/deepseek-v4.1-flash`, reviewer → `opencode-go/glm-5.3-flash`.

Honest note about message text: a real provider assistant message may contain both
a reasoning part and the answer part, and the accepted v0.3-A normalization
currently maps `reasoning` content into the normalized `kind="text"` view, so a
normalized assistant message can carry reasoning text next to the answer text
(recorded as P3-5 in `docs/BACKLOG.md`).  Nothing in this contract claims that the
whole normalized assistant text equals any particular string.

Not verified, unchanged non-claims (no product contract is added by the smoke):

* no orchestration or sequencing (no automatic implementer → reviewer call, no
  repair loops), no automatic acceptance or rejection, no merge decision, no
  Planner role inside DevRelay, no session creation/provisioning;
* no HTTP/SSE MCP transport, no WebUI, no HTTP control API, no multi-workspace
  serving;
* no generic role taxonomy or role registry (exactly `implementer` and
  `reviewer`);
* the automated suite still makes **0** real network/model calls: the real runs
  above were bounded manual smokes, not a repeatable CI job.

## 16. Minimal local setup

```yaml
# .devrelay/config.yaml
opencode:
  base_url: "http://127.0.0.1:4096"     # the accepted v0.3-A endpoint
roles:
  implementer:
    model: "provider-a/model-a"         # this workspace's implementer route
  reviewer:
    model: "provider-b/model-b"         # this workspace's reviewer route
    agent: review                       # optional
```

```bash
devrelay mcp serve --workspace /path/to/project
```

An MCP client then calls `devrelay_list_roles`/`devrelay_get_role` to inspect the
routes and `devrelay_send_role_prompt` to send one turn as a role.  The Planner
decides when each call happens; DevRelay never sequences them.
