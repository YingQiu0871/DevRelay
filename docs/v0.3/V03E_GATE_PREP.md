# v0.3-E platform gate preparation

Status: **PREPARATION ONLY — GATES NOT CLOSED.**  `adopt_completed_turn` remains
disabled.  This document does not authorize a proof run, a code change or a
release.  Executable checklist: [V03E_GATE_RUNBOOK.md](V03E_GATE_RUNBOOK.md).

## Current gate state

| Gate | State | Evidence / blocker |
| --- | --- | --- |
| G0.1 / P7 | PASS | `V03E_G0_1_P7_PROOF.md` |
| G0.2 | PASS | corrected clean rerun + independent approval |
| G0.3 / P5 | PASS | corrected clean rerun + independent approval |
| G0.4 / P4 | **AUTHORITATIVE FAIL / P4 UNPROVEN** | first round: no endpoint, 0 `GET /doc` (`V03E_G0_4_API_INSPECTION_PROOF.md`); 2026-10-29 rerun: bound target, 1 `GET /doc`, `EVIDENCE_INSUFFICIENT` — candidate identifier semantics unresolved (`V03E_G0_4_RERUN_PROOF_2026-10-29.md`) |
| G0.5 / P6 | **NOT RUN / P6 UNPROVEN** | local reachability gap; session-incarnation finding |
| G1 | **NOT RUN** | remote/platform enabling proof |
| G2 | **NOT RUN** | remote/platform enabling proof |

The mandatory fail-closed recovery core is implemented, accepted and shipped;
that is **not** the same as a complete platform gate.  `adopt_completed_turn`
must stay disabled until the veto bound (G0.5/P6) and all required enabling
proofs (G1/G2) are independently satisfied.

## Owner prerequisites before any rerun

1. A real OpenCode instance with a base endpoint reachable from the accepted
   workspace, plus a workspace that passes the accepted ownership probe.
2. A fresh, frozen oracle for the exact gate being rerun; no edits after freeze.
3. A fresh, owner-issued, one-shot authorization naming the gate, candidate
   commit, environment and evidence paths.
4. An independent reviewer/operator for the raw evidence; the implementing agent
   must not self-approve.
5. A clean workspace with no unrelated `.devrelay` state, and a way to preserve
   raw request/response logs without secrets.
6. Explicit decision on whether the run is a proof rerun (no product behavior
   change) or a design change requiring its own review.

## G0.4 / P4 rerun checklist

- [ ] Freeze a new G0.4 oracle under the accepted specification.
- [ ] Record the candidate commit and base endpoint (no secret in tree).
- [ ] Confirm the endpoint is the intended instance and the workspace is bound.
- [ ] Execute the oracle exactly once under the authorization.
- [ ] Preserve the raw `GET /doc` and request-count evidence.
- [ ] Independent review records PASS/FAIL and any new residual.
- [ ] If FAIL, do not patch the oracle post hoc; publish a failed proof and
      revise the design/authorization separately.

## G0.5 / P6 checklist

- [ ] Reconfirm the accepted Session-Incarnation Capability definition.
- [ ] Determine whether the provider exposes a sound original-session anchor.
- [ ] If not, keep `BLOCKED — NO SOUND PROVENANCE ANCHOR`.
- [ ] Do not infer ownership from a reused string or a timestamp alone.
- [ ] Independent review records whether P6 is satisfiable; no self-approval.

## G1 / G2 checklist

- [ ] Identify the remote/platform capabilities the oracle needs.
- [ ] Freeze oracles and authorization before any call.
- [ ] Run each gate once; preserve raw evidence.
- [ ] Reviews must be independent; a failed gate stays failed.
- [ ] Only after both pass may adoption be discussed.

## Hard boundaries

- No `adopt_completed_turn` enablement, tag, release or model-bearing product
  change follows from this document.
- No gate is closed by an offline test, a fake provider, a retry/fallback or an
  AI-written "proof".
- No authorization is implied by prior v0.3 authorizations; they are spent.
- No secrets, tokens or raw provider bodies are committed as evidence.

## Exit condition

The gate package is ready to rerun only when the owner supplies the real
endpoint, frozen oracle, fresh authorization, independent reviewer and clean
workspace.  Until then the correct state is **blocked**, not "almost done".
