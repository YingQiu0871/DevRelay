# DevRelay v0.4-B2 — owner acceptance record

Status: **ACCEPTED / CLOSED by the owner on 2026-10-22.**  This is a B2 stage
acceptance, not a v0.4 release; no tag or publication was created.

## Accepted scope

B2 is the separate wiring surface for the loopback OpenCode endpoint plus
read-only MCP/credential references:

- `GET /api/wiring` — endpoint state, loopback/locality flag, workspace-override
  and `allow_unknown_workspace` flags (no path), credential environment name and
  configured boolean (no value), local-stdio MCP metadata;
- `PUT /api/wiring` — writes **only** `opencode.base_url`, with
  `X-DevRelay-Confirm: apply`, `expected_sha256`, validation, secret scan,
  lock, backup, atomic replace and `restart_required`;
- loopback hosts only (`127.0.0.1`, `localhost`, `::1`); remote endpoints are
  rejected with `422 endpoint_not_local` because the OpenCode transport carries
  the token and prompts;
- Connections tab in the B1 UI;
- A2 `PUT /api/config` still rejects `opencode.base_url`.

## Evidence

| Item | Value |
| --- | --- |
| Implementation commit | `0f78ba3` |
| CI | [run 39696203698](https://github.com/YingQiu0871/DevRelay/actions/runs/39696203698) — 8/8 jobs |
| Local suite | 1,324 collected — 1,322 passed + 2 environment skips |
| Review | independent read-only review: APPROVE WITH FINDINGS, P0/P1 = 0 |
| Review record | [V04B2_REVIEW.md](V04B2_REVIEW.md) |
| Live smoke | endpoint save applied; remote endpoint rejected `endpoint_not_local` |
| Tests | remote rejection, rejected-write file identity, token/workspace non-disclosure, merge preservation |

## Limitations carried forward

- Remote OpenCode endpoints are manual config edits, not UI-writable.
- MCP is read-only local stdio metadata; no hosted connector or stored
  credential.
- Workspace override, `allow_unknown_workspace`, profiles, executables and argv
  remain non-editable.
- The cross-process lock is best-effort; no dedicated `config_busy` test.
- Remaining P3 notes are recorded in [V04B2_REVIEW.md](V04B2_REVIEW.md).

## Immutability

`v0.3.0` remains the published release.  B1/B2 are unreleased `main` work.
