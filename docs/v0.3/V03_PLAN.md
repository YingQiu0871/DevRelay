# DevRelay v0.3 plan

## Stage status

| Stage | Description | Status |
| --- | --- | --- |
| **A** | OpenCode session bridge (explicit endpoint, session select/read, one prompt, bounded wait, interrupt, accounting) | **CURRENT — candidate for independent review** |
| B | (not designed yet) | **NOT STARTED** |
| C | (not designed yet) | **NOT STARTED** |

Do not begin v0.3-B before v0.3-A is independently reviewed.

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

## Explicit non-goals (v0.3-A)

ChatGPT/MCP exposure; DeepSeek/GLM automatic role routing; autonomous review or
"continue until approved" loops; approval decisions inside DevRelay; WebUI;
wiring OpenCode into the implementer/reviewer pipeline; consuming OpenCode calls
against the v0.2 provider budget. See `docs/v0.3/V03A_SPEC.md`.

## Verification order used in this stage

1. Focused offline tests (`tests/test_v03a_opencode.py`,
   `tests/test_v03a_remediation.py`, `tests/test_v03a_second_remediation.py`,
   `tests/test_v03a_third_remediation.py`) throughout.
2. Full suite (`python -m pytest`) at the end, run with an isolated temporary
   directory — see the implementation report.  (Note: the suite's shared-`%TEMP%`
   hygiene item in `docs/BACKLOG.md` is pre-existing and out of scope here.)
3. Self-audit that no v0.3-B functionality leaked in.
4. Local commits only on `v0.3-a-opencode-bridge`; **no push, merge, tag, release**.
