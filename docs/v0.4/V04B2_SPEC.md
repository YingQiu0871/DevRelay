# DevRelay v0.4-B2 — Wiring API

Status: **IMPLEMENTED + INDEPENDENTLY REVIEWED — APPROVE WITH FINDINGS; P2
findings remediated; pending owner acceptance.**  The review is recorded in
[V04B2_REVIEW.md](V04B2_REVIEW.md).  B2 adds a separate, narrow wiring surface on
top of the accepted B1 UI.  It does not widen the A2 configuration allowlist and
does not add run control.

## Objective

Let the local owner set the **OpenCode endpoint** and see the MCP/credential
references without putting any credential or arbitrary execution path into the
configuration API.

## Scope

Editable through `PUT /api/wiring`:

- `opencode.base_url` only.  Empty string disables the OpenCode bridge.
- The existing `OpenCodeConfig` URL validator applies: `http://` or `https://`,
  no userinfo, no query/fragment, no path prefix, valid port.
- The host must be loopback (`127.0.0.1`, `localhost`, `::1`).  A remote
  endpoint is intentionally not writable through B2, because the OpenCode
  transport would send `DEVRELAY_OPENCODE_TOKEN` and prompts there; a remote
  endpoint remains a manual config edit with its own risk decision.

Read-only, displayed by `GET /api/wiring`:

- `opencode.allow_unknown_workspace` (false; not editable);
- whether an `opencode.workspace` override exists (path never returned);
- `DEVRELAY_OPENCODE_TOKEN` as an environment reference, with `configured:
  true/false` only (never the value);
- MCP transport/command/credential reference: local stdio, no HTTP listener,
  no stored credential;
- config digest, `restart_required` and `write_supported`.

Explicitly excluded from both B2 and A2: `codex.executable`, `codex.args`,
`codex.launcher_args`, `opencode.workspace`, `opencode.allow_unknown_workspace`,
`profiles`, `review.provider`, and shell-valued test commands.

## API

`GET /api/wiring` (authenticated):

```json
{
  "config_sha256": "...",
  "restart_required": false,
  "write_supported": true,
  "opencode": {
    "base_url": "http://127.0.0.1:4096",
    "allow_unknown_workspace": false,
    "workspace_override": false
  },
  "credentials": {
    "opencode_token": {"env": "DEVRELAY_OPENCODE_TOKEN", "configured": true}
  },
  "mcp": {
    "transport": "stdio",
    "command": "devrelay mcp serve --workspace <registered workspace>",
    "credentials": "client-side / environment only"
  },
  "write_scope": "OpenCode endpoint wiring only"
}
```

`PUT /api/wiring` (authenticated):

```json
{
  "expected_sha256": "<current digest>",
  "wiring": {"opencode": {"base_url": "http://127.0.0.1:4096"}},
  "confirm": "apply"
}
```

Requires `X-DevRelay-Confirm: apply`.  The write uses the same file-level
validation, secret scan, cross-process lock, owner-only backup, atomic replace
and `restart_required` semantics as A2, but a narrower allowlist.  Unknown or
excluded fields are `422 config_field_not_editable`; a stale digest is
`409 config_changed`.

## UI

A **Connections** tab contains:

- an OpenCode Base URL field and Save button;
- read-only endpoint state, allow-unknown-workspace, workspace-override flag,
  credential environment status, digest and restart state;
- a read-only MCP card (stdio transport, command template, credential
  reference).

No token, password, profile path, executable or argv input exists in the UI.
The save flow uses the same explicit confirmation as B1 and reloads the wiring
view after success.

## Security boundary

- Separate endpoint and separate allowlist; A2's `PUT /api/config` still rejects
  `opencode.base_url`.
- Credentials are environment references only; the API never reads or returns
  the token value.
- No arbitrary filesystem path, shell command, executable, profile selector or
  MCP credential enters the document.
- `allow_unknown_workspace` remains false and read-only.
- Same loopback bind, Host/Origin checks, session/bearer auth and body limits.
- The API checks only whether `DEVRELAY_OPENCODE_TOKEN` is present; it never
  reads or returns the value.

## Non-goals

- No editing of Codex executable/argv or profile selectors.
- No enabling `allow_unknown_workspace`.
- No hosted MCP connector or credential storage.
- No project switching (v0.4-D) or run control (v0.4-C).

## Test plan

- 7 B2 tests plus the existing B1 suite (19 UI tests total).
- GET wiring shape, no absolute workspace path/token value.
- PUT endpoint success, backup, merge preservation, digest/restart.
- Reject workspace/allow-unknown/codex fields and missing confirmation/stale
  digest.
- UI Connections form has no credential/workspace input.
- Full suite: **1,324 collected** (1,322 pass + 2 environment skips on this
  Windows host).

## Acceptance IDs

| ID | Criterion |
| --- | --- |
| B2-1 | `/api/wiring` requires auth and returns endpoint + reference-only metadata |
| B2-2 | Only `opencode.base_url` is writable; all other fields are rejected |
| B2-3 | Credentials appear only as env name + configured boolean |
| B2-4 | MCP is shown as local stdio with no stored credential |
| B2-5 | PUT requires confirmation, current digest, backup and atomic replace |
| B2-6 | A2 config writes still reject `opencode.base_url` |
| B2-7 | UI Connections tab has no token/workspace/executable input |
| B2-8 | Full suite remains green |
