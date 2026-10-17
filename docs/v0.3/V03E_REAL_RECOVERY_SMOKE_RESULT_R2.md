# V03-E Real Crash-and-Recovery Smoke — Result, revision 2

**Status:** EXECUTED ONCE / AUTHORIZATION R2 SPENT / **VERDICT: PASS — V0.3-E
REAL CRASH-AND-RECOVERY SMOKE (R2)** / ORACLE→DRIVER CONFORMANCE COMPLETE /
**NOT ACCEPTANCE**

**Executed:** 2026-10-17, 18:06:35–18:06:51 UTC, by the implementing agent, via
`docs/v0.3/V03E_REAL_RECOVERY_SMOKE_DRIVER_R2.py` (precommitted, unmodified).
**Run id:** `DR-ea1c53353d82430e97e3ce9365922b49`
**Evidence:** `C:\Users\1\AppData\Local\Temp\devrelay-recovery-smoke-20261017T180635Z\evidence`
(outside the repository, per oracle R2 §7).

This document records what happened. A PASS here is **evidence**, not acceptance:
the independent acceptance review is still required, and no
`V03E_ACCEPTANCE.md` row is marked COVERED by this document.

---

## 1. Authorization that governed the run

- Work authorization: `docs/v0.3/V03E_REAL_RECOVERY_SMOKE_AUTHORIZATION_R2.md`,
  issued for this agent by the human (`m02306`:
  *"准备修正版 oracle + 新授权请求 + 重跑，之后独立验收评审"*).
- Baseline at authorization: `312dd74`; precommit that froze the artifacts:
  `cf72e5a813cd3545dd2967e75047d9559ba6c282` (committed bytes, verified):
  - oracle `docs/v0.3/V03E_REAL_RECOVERY_SMOKE_ORACLE_R2.md`
    SHA-256 `60e0613a2810b70dc58d7235723044fbc99e2ca2001650c17a6e7097b7cd7289`;
  - driver `docs/v0.3/V03E_REAL_RECOVERY_SMOKE_DRIVER_R2.py`
    SHA-256 `3ce16c502788f83e5a0a9264b7c527ed4fe401a9c054cc416df379d307ba6bf0`.
- The authorization is **single-use** and was spent by this run; no second run
  was performed. No source file was edited in this round.

## 2. Environment

| item | value |
| --- | --- |
| OpenCode | 1.18.11, `C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe` |
| instance | `opencode serve --port <free> --hostname 127.0.0.1 --print-logs --log-level INFO` |
| implementer route | `opencode/deepseek-v4.1-flash-free` |
| reviewer route | `opencode/glm-5.3-flash-free` |
| workspace | disposable `%TEMP%\devrelay-recovery-smoke-20261017T180635Z\ws`, removed at S8 |
| DevRelay surface | `python -m devrelay mcp serve --workspace <ws>` over MCP stdio |
| Python | 3.13 (driver-reported) |

`opencode-go/*` was rejected earlier with HTTP 403 ("An active OpenCode Go
subscription is required"), so the free `opencode` provider was used — oracle R2
§2 fixes that substitute route.

## 3. Phases

| phase | result | measured (abridged) |
| --- | --- | --- |
| S0 preflight | PASS | instance 200, two prompt-free sessions, config written, repo head `cf72e5a`, submission count `posts 0 / probes 0 / lines 0` |
| S1 baseline | PASS | `READY_IMPLEMENTER`, `schema_version == 2`, 0 turns, no intent, count 0 |
| S2 real crash | PASS | child killed (`taskkill /F /T` rc 0) 3.14 s after start, 0.6 s after `OC-0007` appeared; run doc schema 2 `READY_IMPLEMENTER`, live `in_flight_turn` implementer cycle 1, digest `ccdb5dba…6063`, 188 chars; exactly one submitted POST `OC-0007` state `ISSUED`; exactly one clocked probe GET; `message=process` lines 1; posts == lines == 1; no prompt text in the doc; remote session held 2 messages (`user`, `assistant`) at kill — the reply had already arrived and was later shown not to be adopted |
| S3 refusals on a fresh surface | PASS | `get_run` shows the live intent; `run_implementer`, `run_reviewer`, `decide_run` → `orchestration_recovery_required`; run doc byte-identical; count record unchanged |
| S4 reconcile | PASS | `.devrelay` manifest byte-identical (`added 0 / removed 0 / changed 0`); `recoverable == true`, `v1_frozen == false`; `ledger.outcome == exactly_one_match`, call `OC-0007`; `remote.outcome == evidence_gap` with the "reads no session history" reason; adoption unavailable; checklist exactly the nine items (`ledger settlement` fail, `remote correlation` unknown, `adoption capability` fail, `platform proofs` unknown, rest pass); blockers non-empty incl. "adoption is disabled" |
| S5 resolve (`mark_unrecoverable`) | PASS | `BLOCKED`, `terminal == true`, `legal_next_actions == []`; `blocked_reason == recovery_reason == turn_interrupted`; `resolved_at 2026-10-17T20:06:48+02:00`; evidence digest `47076c9e…bbee` recomputed equal; attempt booked once; `last_transition` recover `RECOVERY_REQUIRED → BLOCKED`; no temp residue |
| S6 terminality | PASS | `run_implementer`/`run_reviewer`/`decide_run` → `orchestration_invalid_transition`; second resolve → `orchestration_recovery_already_resolved`; `reconcile_run` → `orchestration_recovery_unsupported`; doc unchanged; count unchanged |
| S7 leakage | PASS | oracle sentinel, remote reply text and credential needles absent from every `<ws>/.devrelay` file (`hits {}`, `secrets {}`), although one assistant message existed at kill |
| S8 cleanup | PASS | sessions deleted `(200, True)`, instance stopped, port free, repo head/branch/porcelain unchanged (`cf72e5a`), no MCP child survives, workspace removed; in-workspace count `posts 1 / lines 1` |
| R2 oracle conformance | PASS | 14/14 rules mapped to asserted, passing criteria; `oracle-conformance.json` written |

## 4. The submission count (the revision-1 defect, now normative)

Oracle R2 §3 was implemented literally: a submission is a ledger record with
`method == "POST"`, `operation == "send_prompt"`, the implementer session and a
non-empty prompt digest; the count must equal the instance log's
`message=process session.id=<impl>` lines.

| phase | posts | probe GETs | `send_prompt` records | `message=process` lines | agree |
| --- | --- | --- | --- | --- | --- |
| S0 | 0 | 0 | 0 | 0 | true |
| S1 | 0 | 0 | 0 | 0 | true |
| S2 | 1 | 1 | 2 | 1 | true |
| S3–S6 | 1 | 1 | 2 | 1 | true (unchanged) |
| S8 | 1 | 1 | 2 | 1 | true |

The final record in `submission-count.json` is taken **after** S8 removed the
workspace, so the ledger is legitimately empty while the instance log still holds
the single `message=process` line (`posts 0`, `lines 1`). It is not a measurement
failure and is not used by any phase criterion; the S8 in-workspace count above is
the authoritative one.

This is exactly the ambiguity revision 1 got wrong: its count included the
non-submitting ownership probe (2 records vs 1 line), so the equality rule could
never hold. Revision 2 records the probe separately and asserts the POST count.

## 5. Oracle → driver conformance

Oracle R2 §4 requires every normative rule to map to a named, asserted driver
criterion. `oracle-conformance.json` (SHA-256 `09419dfe94629e33555a2579011968b638342cf85489f5633a833daab1a55df6`)
records 14/14 rules PASS; the mapping is reproduced here:

| rule | asserted criteria (labels) | result |
| --- | --- | --- |
| R-S0 | instance answers, two distinct sessions, config written, repo recorded | PASS |
| R-S0-count | `submission count is 0 (posts)` | PASS |
| R-S1 | state/schema/turns/attempts/no intent/no recovery | PASS |
| R-S1-count | `submission count is 0 (posts, S1)` | PASS |
| R-S2-crash | child killed, live intent, identity digest, state | PASS |
| R-S2-post | `exactly one submitted POST for the identity` | PASS |
| R-S2-probe | `exactly one ownership-probe GET recorded` | PASS |
| R-S2-count | `submission count agrees (posts == message=process)` | PASS |
| R-S3 | intent shown, three refusals, byte-identical doc, count unchanged | PASS |
| R-S4 | manifest identical, ledger attribution, remote gap, adoption unavailable, checklist, blockers, count unchanged | PASS |
| R-S5 | BLOCKED, terminal, no legal actions, reason equality, digest recompute, single booking, transition | PASS |
| R-S6 | three invalid-transition refusals, already-resolved, unsupported, doc identical | PASS |
| R-S7 | sentinel absent, no prompt text, no credentials | PASS |
| R-S8 | sessions deleted, instance stopped, port free, repo unchanged, no child, workspace removed | PASS |

## 6. Evidence and hashes

```
<evidence>/smoke.json                b747bc77145296c21056685f6ed1365c8d4d502b12f1d8c92bf22b6090b84baa
<evidence>/oracle-conformance.json   09419dfe94629e33555a2579011968b638342cf85489f5633a833daab1a55df6
<evidence>/submission-count.json     6bb42c4b3d0a8076e720e6c7afb62c839444470d1ac92f44f5aa016265f2c894
<evidence>/server.log                c851238595a9515de728f5ee6fb0ff42c866611f9c5a14188e98622dab1855d6
<evidence>/driver.log                f4a83794ce622682698283e3620308aaf4ff2ddf18fdd94b70a6ac7d937316c4
<evidence>/crash_child.py            5614d03af392607d399639c1b9d6f7fc487efad3eb08a753075b14ffc5bae48f
<evidence>/phase-S0.json             3a523c283aa077dd39c3f3192638e9e5b953358a3d6ab4f5e9aa9585266eb74c
<evidence>/phase-S1.json             ac57c0a9984ca4f58b9000dd0ca9c66a23c66ca0cd74ec02a430b537ae2937fc
<evidence>/phase-S2.json             2bc1bea554af2efc04d09bbf513b16e4883fde1522686f46375e651c33b320ec
<evidence>/phase-S3.json             b7c00dd872dec28f51322da8793dd162d1265cdc523c552ab093d38fa3b203cc
<evidence>/phase-S4.json             9203f2e6484df030c929ccb4ac5d94621481a7796230071728d41b564b9edca3
<evidence>/phase-S5.json             5c6471eb88d9cd7bdd64a21d64783beaf19cc7cfea5060579eb71fa286390d98
<evidence>/phase-S6.json             fbcc63bd17cc62094dbafd91aca0e808da02f30c9c4eece17d3453deb42e531b
<evidence>/phase-S7.json             e9bf505a0b3d4074a21e2727056e30b83c90bec9ad858bb7cb0cbbf43f0d071a
<evidence>/phase-S8.json             6f25ce68e7b3775e7c4468159c3dfc83e5d7777df30b61b374d356d34f85d82a
<evidence>/repo-state.json           7d40a825c2dc994232094122b26536d1a2a597480e39c88ce0a992a9f143ddba
```

The driver's console log is untracked (`build/smoke-r2-console.log`); the
authoritative driver output is the evidence `driver.log` above.

## 7. What this PASS proves, and what it does not

Proven as observed (not inferred):

1. a real, model-bearing submission can be interrupted after the ledger record and
   the remote `POST` are issued, leaving a durable v2 live intent whose identity
   matches the ledger record (`OC-0007`, digest `ccdb5dba…6063`);
2. a fresh MCP surface refuses to replay it and does not mutate the document;
3. `reconcile` is read-only at byte level, attributes the attempt to exactly one
   ledger record, and reports the remote correlation honestly as unavailable;
4. `mark_unrecoverable` resolves exactly once, ends BLOCKED with a
   digest-consistent evidence record, and books the attempt once;
5. the run is terminal, and the remote assistant reply — which **did** exist at
   kill time — is neither adopted nor persisted (sentinel and reply text absent);
6. the harness now measures what its oracle says: the count rule and all 14
   normative rules are asserted and mapped.

Not proven: acceptance. No acceptance row is COVERED. Adoption,
`adopt_completed_turn`, remote correlation, the adoption gates (G0.4/G0.5/G1/G2,
P1/P2/P3/P4/P6/P8) and release remain out of scope and untouched. The
independently authorized acceptance review decides whether these results support
any acceptance claim.

## 8. Relation to revision 1

Revision 1 (`docs/v0.3/V03E_REAL_RECOVERY_SMOKE_RESULT.md`, run
`DR-7248335182ec4207adb8d9d31b397287`, commit `312dd74`) stays **FAIL**: its oracle
counted the ownership-probe GET and its driver never asserted the equality rule, so
its printed PASS was void. This revision-2 result supersedes it as the current
evidence for the real-smoke round, and does not alter that FAIL record.

## 9. Next step

The independent acceptance review requested in `m02306` is the next action. This
document marks no acceptance row COVERED and claims no independent approval.
