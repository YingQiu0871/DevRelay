# DevRelay v0.3 plan

## Stage status

| Stage | Description | Status |
| --- | --- | --- |
| **A** | OpenCode session bridge (explicit endpoint, session select/read, one prompt, bounded wait, interrupt, accounting) | **COMPLETE / ACCEPTED** — candidate `bcf9627e92ef839abb756810e3c615e6d01b6576`, real A33 smoke `PASS` against OpenCode `1.18.11` |
| B | ChatGPT/MCP tool surface (local stdio MCP adapter over the accepted v0.3-A bridge) | **COMPLETE / ACCEPTED** — accepted candidate `d058d62341a173414bdba88fe357b08c236c8bb4`, real MCP smoke `PASS — V0.3-B LOCAL REAL MCP SMOKE` (accepted internally, **unreleased**) |
| C | Agent role routing (semantic role -> workspace-configured model/agent; routing only, no orchestration) | **COMPLETE / ACCEPTED / UNRELEASED** — accepted candidate `eabb667d1bd9e379d3b7105d72b6a2751bc2a32b`; real routing verified by two bounded runs (implementer `opencode-go/deepseek-v4.1-flash`, reviewer `opencode-go/glm-5.3-flash`) |
| D | Bounded orchestration (durable run state, legal transitions, hard cycle bound, fail-closed; still no automatic sequencing) | **COMPLETE / ACCEPTED / CLOSED / UNRELEASED** — accepted candidate `8b70610a5cdda600ef57cf8378c4f69cd33d5be4` after two remediations and the real bounded smoke `PASS — V0.3-D REAL BOUNDED ORCHESTRATION SMOKE` (4 real model turns / 4 POSTs, 0 retries, 0 fallbacks) |
| E | Orchestration recovery (crash-during-submission reconciliation, uncertain-call recovery, resume) | **DESIGN FROZEN / NOT IMPLEMENTED / NOT ACCEPTED / UNRELEASED** — independent design-freeze review of candidate `9f4a01804b9affe8938a272553df345b5a60aeed` approved the fail-closed core design (**P0 = 0, P1 = 0, P2 = 0**, F1–F12 **CLOSED**, decision *APPROVE V0.3-E FAIL-CLOSED CORE DESIGN; PLATFORM PROOF GATE REQUIRED BEFORE IMPLEMENTATION*); frozen contract in `docs/v0.3/V03E_SPEC.md` + `docs/v0.3/V03E_ACCEPTANCE.md` (branch `v0.3-e-recovery-reconciliation`, parent `56e7842`).  **Implementation is gated in two separate stages:** the **mandatory fail-closed core** (reconcile/report + `mark_unrecoverable`; no retry, no model submission, no auto-resume) needs a successful independent design review/freeze plus the **local** strict-reader / ledger-integrity proof (gate step **G0.1** / **P7**), while the **optional** `adopt_completed_turn` capability stays disabled and is separately gated on **P1 + P2 + P3 + P8** (plus **P9** only if timestamp/order correlation is used) and the corresponding platform proof gate (SPEC §19, §25, §28) |

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

v0.3-D (bounded orchestration) is **accepted internally and closed, unreleased**
at candidate `8b70610a5cdda600ef57cf8378c4f69cd33d5be4` on branch
`v0.3-d-bounded-orchestration`, based on the v0.3-C acceptance closeout
`e0a06fa…`: see `docs/v0.3/V03D_SPEC.md` and
`docs/v0.3/V03D_ACCEPTANCE.md`.  It adds durable run state, legal transitions, a
hard cycle bound (`max_cycles` 1..3, at most six reserved/consumed model-turn
budget slots per run), durable audit and fail-closed behaviour over the accepted
role path - and exactly five MCP tools (17 in total).  It still does **not**
sequence roles automatically, never interprets reviewer text and never retries.
Its one authorized bounded real smoke was a **`PASS`** (4 real model turns / 4
POSTs, 0 retries, 0 fallbacks, terminal guard proved twice; evidence in
`docs/v0.3/V03D_ACCEPTANCE.md` §L); no second smoke was performed.

An independent review of the first v0.3-D candidate returned `REQUEST_CHANGES`
(P0 = 0, one blocking P1: persisted run state was trusted as input, plus P2/P3
findings), and a second review returned `REQUEST_CHANGES` with **three** blocking
P1s: a persisted run needed only plausible fields, not a state provable from its
history.  Historically, both **remediations were complete and ready for independent
re-review** at that point; that re-review later passed and v0.3-D was accepted and
closed (see the stage table and `V03D_ACCEPTANCE.md` §L).  The first closed the
trusted-input boundary, the second added reachability
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
remained **NOT ACCEPTED** until that re-review passed (historical: the re-review
approved one bounded real smoke, the smoke passed, and v0.3-D was accepted - see
`docs/v0.3/V03D_ACCEPTANCE.md` §L).  The accepted runtime candidate stays
`8b70610a5cdda600ef57cf8378c4f69cd33d5be4`; the acceptance bookkeeping commit is
`be4dce7` (documentation only).

v0.3-E (recovery: crash-during-submission reconciliation, uncertain-call
recovery, resume) is **design-only and FROZEN**: after the independent design review's
first `REQUEST_CHANGES` (P0 = 1, P1 = 6, P2 = 5), two narrow re-reviews and their
fixes (`f67bf9e`, `5b7c65a`, `9f4a018`), the final independent design-freeze review
approved the contract at candidate `9f4a018` (**P0 = 0, P1 = 0, P2 = 0**, F1–F12
CLOSED) - see `docs/v0.3/V03E_SPEC.md`, with the design-phase matrix
`docs/v0.3/V03E_ACCEPTANCE.md`, on the design branch
`v0.3-e-recovery-reconciliation`, parent `56e7842a414777d20a3882cad641da383964bab3`.
The remediated contract splits a **mandatory fail-closed core** (reconcile/report +
`mark_unrecoverable`; no submission, no retry, no auto-resume, no adoption) from an
**optional gated** `adopt_completed_turn` capability and a **report-only** pending
capability; the core needs no remote platform proof, while adoption requires the
proof gate (P1, P2, P3, P8, plus P9 if timestamps are used).
**No recovery code exists** and the accepted v0.3-D runtime candidate
`8b70610a5cdda600ef57cf8378c4f69cd33d5be4` is untouched.  The design re-review
**has passed** and the v0.3-E design is **frozen** (candidate `9f4a018`, P0 = 0,
P1 = 0, P2 = 0); mandatory-core implementation nonetheless must not start until
**G0.1/P7 passes** — and it now **does** pass: the proof was executed once
(`docs/v0.3/V03E_G0_1_P7_PROOF.md`: six hard-kill case executions, all meeting their
predefined criteria, 0 real provider/model calls) and the final independent proof
review issued *APPROVE V0.3-E G0.1 / P7 PLATFORM PROOF* (**P0 = 0, P1 = 0, P2 = 0**),
making **G0.1 / P7 = PASS** (authoritative, independently approved).  **G0.2**
(offline run<->call false-correlation) was then executed once at `4448f92` and
returned a candidate pass; the first independent review returned `REQUEST_CHANGES`
(P0 = 0, P1 = 0, P2 = 2), so a separately authorized **clean re-run** was executed
under an oracle precommitted in commit `12ea1b7`: the ten fixed cases A-J ran once each,
all behaved fail-closed against production-generated corpora, a unique correlation is
possible only when the complete frozen identity tuple matches exactly one record in the
run's role session, the oracle was unchanged during execution, and 0 real
provider/model calls were made.  Current result: the independent clean-rerun review issued **APPROVE V0.3-E G0.2
FALSE-CORRELATION PROOF** (P0 = 0, P1 = 0, P2 = 0), so **G0.2 = PASS** (authoritative,
independently approved) — `docs/v0.3/V03E_G0_2_CLEAN_RERUN_PROOF.md`; the original
round is preserved in `docs/v0.3/V03E_G0_2_FALSE_CORRELATION_PROOF.md`.  G0.1/P7 therefore no longer blocks
mandatory-core implementation *eligibility*; implementation nonetheless remains
**NOT AUTHORIZED** until a separately issued implementation authorization, and
G0.3-G0.5/G1/G2 remain unrun (G0.2 = PASS, authoritative, independently approved), so the platform
proof gate is **PARTIALLY EXECUTED / NOT COMPLETE** (not passed, not complete).  The mandatory core's gate was **G0.1/P7 PASS
first** — and it **has** passed, so the second step of the ordering design frozen →
G0.1/P7 PASS → mandatory-core implementation may be authorized is now satisfied;
had G0.1/P7 failed, core implementation would have stayed **blocked**
(no degraded-implementation path; a degraded scope would need its own
design change and review).  G0.4-G0.5 remain relevant to the
reporting language.  `adopt_completed_turn` stays disabled until P1, P2, P3 and P8
(and P9 if timestamps are used) pass the platform proof gate (SPEC §25, §28); if
those optional-adoption proofs fail, that capability is removed/disabled and no real
adoption smoke is required, while the core is unaffected because it has already
passed its own local gate.  v0.3-E keeps every accepted v0.3-D
invariant: no implicit retry, no fallback, no automatic sequencing, no automatic
resume, no budget refund, terminal runs never reopen.  See `docs/BACKLOG.md` for
deferred, non-blocking follow-ups.

## v0.3-D scope (implemented, remediated, accepted and closed — unreleased)

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

## v0.3-E scope (designed, not implemented)

1. `docs/v0.3/V03E_SPEC.md` — the remediated recovery/reconciliation contract:
   the mandatory-core / gated-capability / report-only scope split, the explicit
   recovery entry action (`resolve_recovery` on a valid v2 live-intent document or
   on `RECOVERY_REQUIRED`), the single `recovery.attempt` representation, the exact
   `RECOVERY_REQUIRED` document shape with pinned accounting equations, the
   corruption-is-never-recovery rule, the strict recovery evidence reader, the
   capability dependency table, the added proofs P8 (session exclusivity) and P9
   (timestamp/order fidelity), case taxonomy
   A–H, reconcile/materialize/resume/retry definitions, recovery authority,
   preserved v0.3-D invariants, one new non-terminal execution-frozen run state
   (`RECOVERY_REQUIRED`), exact call-identity model, reconciliation evidence
   sources, crash-window matrix W0–W7, restart matrix, reconciled
   completion/non-delivery/pending policies, budget table, route/workspace/session
   identity rules, terminal immunity, proposed schema version 2 with a no-migration
   policy, privacy, concurrency, the minimum two-tool MCP surface
   (`devrelay_reconcile_run` read-only, `devrelay_resolve_recovery` mutating), the
   design-decisions table, the capability dependency table and the open platform
   proofs P1–P9 with the pre-implementation proof gate (the **local** G0.1/P7
   strict-reader proof gates the mandatory core; **P1/P2/P3/P8** - and **P9** only
   if timestamps are used - gate the optional adoption capability).
2. `docs/v0.3/V03E_ACCEPTANCE.md` — the design-phase acceptance matrix:
   mandatory-core criteria (E1–E25), the gated adoption capability (E26–E30),
   report-only pending/non-delivery/identity bounds (E31–E33), local proofs
   (E34–E38), remote proofs (E39–E40), future implementation evidence
   (E41–E51, all FUTURE / NOT RUN) and carried deferrals (F1–F4).
3. Not implemented in this stage: no runtime source, no tests, no new tool, no
   schema change, no real provider/model call, no v0.3-E smoke.

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
