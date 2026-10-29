# v0.3-E real-platform gate runbook

Status: **PREPARED / BLOCKED — NOT EXECUTED.**  `adopt_completed_turn` remains
disabled.  This runbook must not be treated as an authorization or as evidence.
Current readiness: [V03E_GATE_READINESS_2026-10-27.md](V03E_GATE_READINESS_2026-10-27.md).

## 0. Current state

| Gate | State |
| --- | --- |
| G0.1/P7 | PASS |
| G0.2 | PASS |
| G0.3/P5 | PASS |
| G0.4/P4 | authoritative FAIL / P4 UNPROVEN — confirmed by the 2026-10-29 rerun (`EVIDENCE_INSUFFICIENT`; `V03E_G0_4_RERUN_PROOF_2026-10-29.md`, review `V03E_G0_4_RERUN_REVIEW_2026-10-29.md`) |
| G0.5/P6 | NOT RUN / P6 UNPROVEN |
| G1 | NOT RUN |
| G2 | NOT RUN |

See [V03E_GATE_PREP.md](V03E_GATE_PREP.md) for prerequisites.

## 1. Owner-supplied inputs (required before any run)

- [ ] Real OpenCode base endpoint reachable from the target workspace.
- [ ] Initialized workspace and a session pair that passes the accepted
      workspace-ownership probe.
- [ ] Fresh frozen oracle for the exact gate.
- [ ] Fresh owner-issued one-shot authorization naming:
      gate, candidate commit, environment fingerprint, evidence path.
- [ ] Independent reviewer (not the implementing agent).
- [ ] Clean workspace/state; raw request/response capture path with redaction.
- [ ] Decision: proof rerun only, or a design change requiring separate review.

No endpoint URL, token or session string belongs in the git tree.  Record only
fingerprints/ids and redacted evidence.

## 2. Preflight commands (illustrative)

```powershell
git rev-parse HEAD
git status --short
python -m pytest -q
devrelay version
devrelay doctor --strict
```

Expected: clean tree, version matches the authorized commit, doctor succeeds,
and the authorization explicitly names the same commit.

## 3. G0.4 / P4 rerun

1. Freeze the new G0.4 oracle; record its digest.
2. Confirm the OpenCode endpoint is the intended instance and the workspace is
   bound.
3. Execute the oracle exactly once under the authorization.
4. Preserve raw `GET /doc`/request-count evidence with secrets removed.
5. Independent reviewer records PASS/FAIL.
6. If FAIL: do not edit the oracle post hoc; record a failed proof and stop.

## 4. G0.5 / P6

1. Reconfirm the accepted Session-Incarnation Capability definition.
2. Determine whether a sound original-session anchor exists.
3. If not, retain `BLOCKED — NO SOUND PROVENANCE ANCHOR`.
4. Do not infer ownership from a reused string or timestamp.
5. Independent reviewer records satisfiable/unsatisfiable.  A FAIL stays FAIL.

## 5. G1 / G2

1. Identify required remote/platform capabilities.
2. Freeze oracles and authorization first.
3. Execute once per gate; preserve raw evidence.
4. Independent review each gate.
5. Only both PASS may reopen adoption discussion.

## 6. Evidence package

Required, redacted:

```text
authorization.md
oracle.md + sha256
environment.txt
commands.log
raw-evidence/
review.md
result.md
```

No tokens, prompts, full provider bodies or personal paths.  Session ids may be
replaced with stable synthetic labels if raw evidence is kept out of band.

## 7. Stop conditions

- oracle or authorization digest changes after freeze;
- endpoint/workspace fingerprint differs from the authorization;
- a request is retried or a fallback model is used;
- raw evidence cannot be preserved/redacted;
- independent reviewer is unavailable;
- any gate fails.

## 8. Exit criteria

A gate is closed only by an independent review of raw evidence.  The AI must not
self-approve, and no tag/release/enablement follows automatically.  Until all
required gates pass, `adopt_completed_turn` stays disabled.
