# DevRelay v0.3 plan

## Stage status

| Stage | Description | Status |
| --- | --- | --- |
| **A** | OpenCode session bridge (explicit endpoint, session select/read, one prompt, bounded wait, interrupt, accounting) | **COMPLETE / ACCEPTED** — candidate `bcf9627e92ef839abb756810e3c615e6d01b6576`, real A33 smoke `PASS` against OpenCode `1.18.11` |
| B | ChatGPT/MCP tool surface (local stdio MCP adapter over the accepted v0.3-A bridge) | **CANDIDATE + GATE REMEDIATION COMPLETE — ready for re-gate** (unreleased) |
| C | (not designed yet) | **NOT STARTED** |

v0.3-A is accepted and its runtime implementation is frozen at the accepted
candidate (`bcf9627…`); v0.3-A sources were not modified by v0.3-B.

v0.3-B (MCP tool surface) is implemented on `v0.3-b-mcp-tool-surface` as a
candidate for independent review: see `docs/v0.3/V03B_SPEC.md` and
`docs/v0.3/V03B_ACCEPTANCE.md`.  It is **unreleased** and makes **no** real model
call; a real MCP-client smoke is explicitly deferred until after review.

v0.3-C (role routing / orchestration) has **not** started and must not begin
without a separate authorization.  See `docs/BACKLOG.md` for deferred,
non-blocking follow-ups.

## v0.3-B scope (implemented)

1. `src/devrelay/mcp/models.py` — the one stable MCP envelope (`schema_version 1`)
   and the documented MCP input bounds.
2. `src/devrelay/mcp/ledger.py` — strict, bounded, read-only ledger projection
   that reports corruption instead of hiding it.
3. `src/devrelay/mcp/tools.py` — one adapter per capability over the accepted
   `OpenCodeBridge` (health, list/get session, read messages, send_prompt,
   wait_idle, interrupt, calls) with v0.3-A validation, `retry_safe` derived from
   documented evidence, and one narrow lock for side-effecting tools.
4. `src/devrelay/mcp/server.py` — bound-workspace startup (fail closed), the
   exact nine-tool inventory with honest annotations and planner-oriented
   descriptions, envelope-for-every-failure, stderr-only diagnostics, stdio run.
5. `src/devrelay/cli_mcp.py` + one registration line — `devrelay mcp serve
   --workspace <path>`.
6. `tests/test_v03b_mcp_tools.py`, `tests/test_v03b_mcp_stdio.py` — the offline
   in-process matrix and the real stdio subprocess harness.

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
