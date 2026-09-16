# DevRelay v0.3 plan

## Stage status

| Stage | Description | Status |
| --- | --- | --- |
| **A** | OpenCode session bridge (explicit endpoint, session select/read, one prompt, bounded wait, interrupt, accounting) | **COMPLETE / ACCEPTED** — candidate `bcf9627e92ef839abb756810e3c615e6d01b6576`, real A33 smoke `PASS` against OpenCode `1.18.11` |
| B | ChatGPT/MCP tool surface (local stdio MCP adapter over the accepted v0.3-A bridge) | **COMPLETE / ACCEPTED** — accepted candidate `d058d62341a173414bdba88fe357b08c236c8bb4`, real MCP smoke `PASS — V0.3-B LOCAL REAL MCP SMOKE` (accepted internally, **unreleased**) |
| C | Agent role routing (semantic role -> workspace-configured model/agent; routing only, no orchestration) | **CANDIDATE IMPLEMENTATION COMPLETE — ready for independent review** (unreleased) |
| D | Orchestration (automatic implementer -> reviewer sequencing, repair loops) | **NOT STARTED** (not designed yet) |

v0.3-A is accepted and its runtime implementation is frozen at the accepted
candidate (`bcf9627…`); v0.3-A sources were not modified by v0.3-B.

v0.3-B (MCP tool surface) is **accepted internally and closed** at candidate
`d058d62341a173414bdba88fe357b08c236c8bb4` on branch `v0.3-b-mcp-tool-surface`:
see `docs/v0.3/V03B_SPEC.md` and `docs/v0.3/V03B_ACCEPTANCE.md`.  It is
**unreleased** (package version `0.1.0`, public release `v0.1.0`) and its final
evidence includes one separately authorized real MCP smoke
(`PASS — V0.3-B LOCAL REAL MCP SMOKE`: real official MCP Python SDK 2.2.0 client
-> stdio -> this server -> the accepted v0.3-A bridge -> real OpenCode 1.18.11 ->
one explicit `opencode-go/deepseek-v4.1-flash` turn, exactly one
`POST /session/{id}/message`, reply `DEVRELAY_V03B_MCP_OK`).

v0.3-C (agent role routing) is implemented as an **unreleased candidate** on
branch `v0.3-c-agent-role-routing`, based on the v0.3-B acceptance closeout
`c883bab…`: see `docs/v0.3/V03C_SPEC.md` and `docs/v0.3/V03C_ACCEPTANCE.md`.  It
routes a semantic role (`implementer` | `reviewer`) to the exact model/agent the
workspace configures and adds exactly three MCP tools (12 in total); it does
**not** orchestrate anything.  It makes **0 real model calls** and awaits
independent review before any real role-routing smoke is even considered.

v0.3-D (orchestration: automatic sequencing, repair loops, acceptance decisions)
has **not** started; it must not begin without a separate authorization.  See
`docs/BACKLOG.md` for deferred, non-blocking follow-ups.

## v0.3-C scope (implemented, candidate)

1. `src/devrelay/roles/models.py` — the role vocabulary (`implementer`,
   `reviewer`), the frozen `RoleRoute` value object and the `RolesConfig` wiring
   schema (identifiers only; no prompts, credentials, endpoints or fallbacks).
2. `src/devrelay/roles/resolver.py` — deterministic exact resolution with the
   local error taxonomy (`role_unknown` / `role_unconfigured` /
   `role_invalid_route`) and the sanitized read-only views.
3. `src/devrelay/roles/service.py` — `RoleRouter.send_role_prompt(bridge, role,
   session_id, prompt)`: resolve first, then delegate to the accepted
   `OpenCodeBridge.send_prompt` with the configured model/agent.  No model/agent
   parameter exists (P1), no second HTTP path exists.
4. `src/devrelay/config.py` — the optional `roles:` wiring section (never task
   policy; absent is valid so v0.3-B workspaces keep working).
5. `src/devrelay/mcp/tools.py` + `server.py` — exactly three new tools
   (`devrelay_list_roles`, `devrelay_get_role`, `devrelay_send_role_prompt`), all
   routed through the one v0.3-B `_execute` execution boundary; the accepted nine
   tools, the enveloping rule and the raw path are unchanged.
6. `tests/test_v03c_role_config.py`, `tests/test_v03c_roles.py`,
   `tests/test_v03c_role_tools.py`, `tests/test_v03c_role_concurrency.py`,
   `tests/test_v03c_stdio_roles.py` (+ `tests/v03c_helpers.py`) — 140 offline
   tests: configuration, resolution, route separation, override rejection,
   failure taxonomy, the accepted send-semantics matrix through the role path,
   serialization/cancellation and the real stdio MCP boundary.

## v0.3-B scope (implemented, accepted)

1. `src/devrelay/mcp/models.py` — the one stable MCP envelope (`schema_version 1`)
   and the documented MCP input bounds.
2. `src/devrelay/mcp/ledger.py` — strict, bounded, read-only ledger projection
   that reports corruption instead of hiding it.
3. `src/devrelay/mcp/tools.py` — one adapter per capability over the accepted
   `OpenCodeBridge` (health, list/get session, read messages, send_prompt,
   wait_idle, interrupt, calls) with v0.3-A validation, `retry_safe` derived from
   documented evidence, and **one process-scoped re-entrant execution lock over
   all nine tool bodies** (the accepted v0.3-A filesystem ledger is a
   single-writer store, so reads are serialized too).
4. `src/devrelay/mcp/server.py` — bound-workspace startup (fail closed), the
   exact nine-tool inventory with honest annotations and planner-oriented
   descriptions, envelope-for-every-failure, stderr-only diagnostics, stdio run.
5. `src/devrelay/cli_mcp.py` + one registration line — `devrelay mcp serve
   --workspace <path>`.
6. `tests/test_v03b_mcp_tools.py`, `tests/test_v03b_mcp_stdio.py` — the offline
   in-process matrix and the real stdio subprocess harness.
7. `tests/test_v03b_mcp_concurrency.py` — the concurrency-remediation suite: the
   parallel-read ledger regression, the mixed read+send batch, the cross-tool
   serialization matrix, lock release after every failure kind, and cancellation
   under the global boundary; 19 of its 21 tests fail against the
   pre-remediation candidate `59f81c0` (only the two all-side-effecting pairs
   pass there).

## v0.3-A scope (implemented)

1. `devrelay/opencode/models.py` — normalized DevRelay-owned session/message/
   page/health/operation/call models and the explicit state vocabularies.
2. `devrelay/opencode/transport.py` — one configured endpoint, one attempt per
   request, bounded response reads, sanitized errors, no shell, no port scanning.
3. `devrelay/opencode/accounting.py` — durable per-request ledger
   (`.devrelay/opencode/calls/<call-id>.json`) with a monotonic sequence.
4. `devrelay/opencode/bridge.py` — the capability surface, ownership validation,
   bounded idle wait, interrupt semantics.
5. `devrelay/config.py` — `opencode:` runtime wiring (never task policy; excluded
   from the frozen policy projection and tolerated in legacy snapshots).
6. `devrelay/cli_opencode.py` + a one-line registration in `cli.py` — thin wrappers
   (`health`, `sessions`, `show`, `read`, `send`, `wait`, `interrupt`, `calls`).
7. `tests/opencode_stub.py` + `tests/test_v03a_opencode.py` — deterministic
   offline coverage of every acceptance criterion (A1–A32).
8. `tests/test_v03a_remediation.py` — focused regression tests for the
   independent-review findings (R1–R11 in `V03A_ACCEPTANCE.md`); 58 of its 66
   tests fail against the pre-remediation source.
9. `tests/test_v03a_second_remediation.py` — focused regression tests for the
   second independent review (S1–S11 in `V03A_ACCEPTANCE.md`); 36 of its 49 tests
   fail against `f5d487d`.
10. `tests/test_v03a_third_remediation.py` — focused regression tests for the
    third independent review's smoke blockers (T1–T6 in `V03A_ACCEPTANCE.md`);
    22 of its 23 tests fail against `6e0eb61`.
11. `tests/test_v03a_real_protocol.py` — real-protocol regression tests for the
    A33 findings (V1–V8 in `V03A_ACCEPTANCE.md`), with fixtures derived from the
    installed OpenCode 1.18.11 `/doc`; 28 of its 30 tests fail against `780c2fd`.

## Explicit non-goals (v0.3-A)

ChatGPT/MCP exposure; DeepSeek/GLM automatic role routing; autonomous review or
"continue until approved" loops; approval decisions inside DevRelay; WebUI;
wiring OpenCode into the implementer/reviewer pipeline; consuming OpenCode calls
against the v0.2 provider budget. See `docs/v0.3/V03A_SPEC.md`.

## Verification order used in this stage

0. Real smoke (A33) against a dedicated OpenCode 1.18.11 server — `PASS`
   (explicit model `opencode-go/deepseek-v4.1-flash`, exactly one
   `POST /session/{id}/message`, reply `DEVRELAY_A33_OK`); outcome and the full
   historical sequence are recorded in `V03A_ACCEPTANCE.md`.
1. Focused offline tests (`tests/test_v03a_opencode.py`,
   `tests/test_v03a_remediation.py`, `tests/test_v03a_second_remediation.py`,
   `tests/test_v03a_third_remediation.py`, `tests/test_v03a_real_protocol.py`)
   throughout.
2. Full suite (`python -m pytest`) at the end, run with an isolated temporary
   directory — see the implementation report.  (Note: the suite's shared-`%TEMP%`
   hygiene item in `docs/BACKLOG.md` is pre-existing and out of scope here.)
3. Self-audit that no v0.3-B functionality leaked in.
4. Local commits only on `v0.3-a-opencode-bridge`; **no push, merge, tag, release**.
