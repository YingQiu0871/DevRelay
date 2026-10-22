# DevRelay v0.4-B2 — independent review record

Status: **B2 reviewed: APPROVE WITH FINDINGS (P0/P1 = 0); P2 findings
remediated; accepted by the owner on 2026-10-22.**  No v0.4 tag or release is
implied.  See [V04B2_ACCEPTANCE.md](V04B2_ACCEPTANCE.md).

The review covered the separate wiring API, the ConfigWriter refactor, the
Connections tab and the B2 tests.

## Findings and disposition

| ID | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| B2-R1 | P2 | `opencode.base_url` accepted any http(s) host.  After a save and restart, the OpenCode transport would send `DEVRELAY_OPENCODE_TOKEN` and prompts to that host. | Fixed: B2 accepts only loopback hosts (`127.0.0.1`, `localhost`, `::1`).  Remote endpoints remain a manual config edit with a separate risk decision.  The UI rejects remote hosts and names the target in the confirmation. |
| B2-R2 | P2 | Privacy tests were weak: no configured workspace override / real token value, no invalid-URL case, no merge-preservation or rejected-write file assertion. | Fixed: tests set `DEVRELAY_OPENCODE_TOKEN` and an `opencode.workspace` override, assert neither value is returned, reject remote endpoints, and assert the config file is unchanged after a rejected write; the successful write test asserts unrelated `review`/`opencode` sections survive. |
| B2-R3 | P3 | `_path_allowed` admits descendants of a leaf prefix; nested-object rejection rests on pydantic. | Retained: the merged `WorkspaceFile` validation rejects nested objects before any write; no bypass was found. |
| B2-R4 | P3 | `GET /api/wiring` echoes `base_url` raw and reports an unreadable config as an empty object with 200. | `base_url` is a non-secret endpoint; the UI shows locality.  A distinct unreadable-config state remains a polish item. |
| B2-R5 | P3 | GET reports file state, not the loaded startup wiring. | `restart_required` is returned and the UI/doc state that a restart is needed; the live process keeps startup wiring. |
| B2-R6 | P3 | Post-success reload could overwrite the success message; a reload failure in the `config_changed` branch could reject. | Fixed: success is shown after reload; reload failures preserve the success message or report the reload error; `config_changed` reload is wrapped. |
| B2-R7 | P3 | No cross-process `config_busy` test; trailing-slash/whitespace normalization is not persisted. | The lock is best-effort and the existing A2 hardening records this residual; B2 uses the same lock.  Normalization is performed by the OpenCode validator/transport. |
| B2-R8 | P3 | Doc drift: config/service docstrings implied no endpoint/wiring writes. | Corrected to describe A2 config + B2 loopback endpoint writes. |

## Verified good

- Only `opencode.base_url` is writable; merge preserves all other sections and
  `WorkspaceFile` rejects unknown/nested fields.
- A2 `PUT /api/config` still rejects `opencode.base_url`; B2 did not widen the
  A2 allowlist.
- `GET /api/wiring` exposes no workspace path, token value, profile,
  executable/argv or raw config.
- Credentials are an environment name plus a configured boolean.
- MCP is read-only local stdio metadata.
- PUT requires `X-DevRelay-Confirm: apply`, the current digest, and uses the
  existing lock/backup/atomic replacement.
- The Connections UI has no credential/workspace/executable input.

## Remaining gate

B2 is implemented and reviewed with findings.  Owner acceptance is pending.
Remote OpenCode endpoints and MCP/credential storage remain manual/out of scope.
