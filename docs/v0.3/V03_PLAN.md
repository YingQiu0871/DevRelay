# DevRelay v0.3 plan

## Stage status

| Stage | Description | Status |
| --- | --- | --- |
| **A** | OpenCode session bridge (explicit endpoint, session select/read, one prompt, bounded wait, interrupt, accounting) | **COMPLETE / ACCEPTED** — candidate `bcf9627e92ef839abb756810e3c615e6d01b6576`, real A33 smoke `PASS` against OpenCode `1.18.11` |
| B | ChatGPT/MCP tool surface (local stdio MCP adapter over the accepted v0.3-A bridge) | **COMPLETE / ACCEPTED** — accepted candidate `d058d62341a173414bdba88fe357b08c236c8bb4`, real MCP smoke `PASS — V0.3-B LOCAL REAL MCP SMOKE` (accepted internally, **unreleased**) |
| C | Agent role routing (semantic role -> workspace-configured model/agent; routing only, no orchestration) | **COMPLETE / ACCEPTED / UNRELEASED** — accepted candidate `eabb667d1bd9e379d3b7105d72b6a2751bc2a32b`; real routing verified by two bounded runs (implementer `opencode-go/deepseek-v4.1-flash`, reviewer `opencode-go/glm-5.3-flash`) |
| D | Bounded orchestration (durable run state, legal transitions, hard cycle bound, fail-closed; still no automatic sequencing) | **CANDIDATE IMPLEMENTATION COMPLETE — ready for independent review** (unreleased) |
| E | Orchestration recovery (crash-during-submission reconciliation, uncertain-call recovery, resume) | **NOT STARTED** (not designed yet) |

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

v0.3-C (agent role routing) is **accepted internally and closed** at candidate
`eabb667d1bd9e379d3b7105d72b6a2751bc2a32b` on branch
`v0.3-c-agent-role-routing`, based on the v0.3-B acceptance closeout `c883bab…`:
see `docs/v0.3/V03C_SPEC.md` and `docs/v0.3/V03C_ACCEPTANCE.md`.  It routes a
semantic role (`implementer` | `reviewer`) to the exact model/agent the workspace
configures and adds exactly three MCP tools (12 in total); it does **not**
orchestrate anything.  Real routing was verified by two bounded runs: implementer
→ `opencode-go/deepseek-v4.1-flash` and reviewer → `opencode-go/glm-5.3-flash`,
one explicit model turn and one `POST /session/{id}/message` each, with
three-way route agreement (`devrelay_get_role`, response metadata, OpenCode
provider log).  The package version stays `0.1.0` and the public release remains
`v0.1.0`.

v0.3-D (bounded orchestration) is implemented as an **unreleased, NOT ACCEPTED
candidate** on branch `v0.3-d-bounded-orchestration`, based on the v0.3-C
acceptance closeout `e0a06fa…`: see `docs/v0.3/V03D_SPEC.md` and
`docs/v0.3/V03D_ACCEPTANCE.md`.  It adds durable run state, legal transitions, a
hard cycle bound (`max_cycles` 1..3, at most six reserved/consumed model-turn budget slots per run), durable
audit and fail-closed behaviour over the accepted role path - and exactly five MCP
tools (17 in total).  It still does **not** sequence roles automatically, never
interprets reviewer text, never retries and makes **0 real model calls**; a
bounded real orchestration smoke requires independent review and a separate
authorization.

An independent review of the first v0.3-D candidate returned `REQUEST_CHANGES`
(P0 = 0, one blocking P1: persisted run state was trusted as input, plus P2/P3
findings), and a second review returned `REQUEST_CHANGES` with **three** blocking
P1s: a persisted run needed only plausible fields, not a state provable from its
history.  Both **remediations are complete and ready for independent re-review**:
the first closed the trusted-input boundary, and the second adds reachability
validation (`READY_REVIEWER` requires this cycle's completed implementer turn, a
blocked turn implies `BLOCKED`, the last transition must end at the current state,
the decision history must equal the completed cycles, no future-cycle evidence,
and the persisted spend must be possible for the cycle structure), strict persisted
types, turn-audit consistency, and a production-generated honest corpus with a
per-mutation differential battery.  Details: persisted state is now validated by a semantic invariant
pass on load *and* save (the four gate reproductions A-D are refused), an
unresolvable role route fails closed like a changed one, an interrupted turn is
materialized into the role history with its sanitized audit fields, the durable
in-flight intent is proven to precede submission (Mutation F is now detected), and
the accounting/outcome/run-id/wording findings are fixed or recorded.  The stage
remains **NOT ACCEPTED** until that re-review passes.

v0.3-E (recovery: crash-during-submission reconciliation, uncertain-call
recovery, automatic resume) has **not** started and must not begin without a
separate authorization.  See `docs/BACKLOG.md` for deferred, non-blocking
follow-ups.

## v0.3-D scope (implemented + remediated, candidate, NOT ACCEPTED)

1. `src/devrelay/orchestration/models.py` — the explicit state enum, hard bounds
   (`HARD_MAX_CYCLES = 3`, default 2, model-turn budget = 2 x max_cycles), the
   strict run document (identifiers/digests/evidence only) and its
   Planner-complete summary projection.
2. `src/devrelay/orchestration/store.py` — durable single-writer store under
   `.devrelay/orchestration/runs/`, generated `DR-<32 hex>` ids validated before
   any filesystem access, atomic writes, and `orchestration_state_corrupt`
   instead of any silent reset.
3. `src/devrelay/orchestration/state_machine.py` — the pure transition policy
   (phase legality, cycle accounting, fail-closed blocking, the three external
   decisions and the cycle cap).
4. `src/devrelay/orchestration/service.py` — `start_run`, `get_run`,
   `run_implementer`, `run_reviewer`, `decide_run` over the accepted role router
   and bridge: route-snapshot comparison, session ownership checks, one role turn
   per explicit phase, a durable in-flight intent record that is never replayed,
   and no reviewer-text interpretation.
5. `src/devrelay/mcp/tools.py` + `server.py` — exactly five new tools (17 in
   total) routed through the one accepted `_execute` boundary, run-state-visible
   failure envelopes, a sanitized `devrelay_status.orchestration` block and the
   advertised surface version `0.3.0-d`.
6. `tests/test_v03d_models.py`, `tests/test_v03d_state_machine.py`,
   `tests/test_v03d_store.py`, `tests/test_v03d_orchestration.py`,
   `tests/test_v03d_mcp_tools.py`, `tests/test_v03d_concurrency.py`,
   `tests/test_v03d_stdio.py` (+ `tests/v03d_helpers.py`) — 154 offline tests
   covering bounds, the store, the state machine, the phase matrices, the
   authority invariant, invalid transitions, persistence, concurrency and the
   real stdio boundary.

## v0.3-C scope (implemented, accepted)

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
   documented evidence, and **one re-entrant execution lock per tool surface over
   all tool bodies** (the shipped stdio server builds exactly one surface; the
   accepted v0.3-A filesystem ledger is a single-writer store, so reads are
   serialized too, and several surfaces or writer processes are unsupported).
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
