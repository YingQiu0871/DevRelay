# Post-v0.4 hardening backlog

Date: 2026-10-23.  Status after v0.4.0 publication.  This document distinguishes
implemented hardening from design-only work; it does not claim new release
artifacts.

## Completed

- Pinned release/test actions, then upgraded them to Node.js 24 releases.
- Reruns on an already-published PyPI version skip the Windows portable rebuild.
- CycloneDX SBOM for the portable runtime closure; portable zip + standalone
  asset + five-asset release gate.
- Durable manual-prompt pending markers and confirmed recovery
  (`.devrelay/web/manual_prompts.json`, metadata only).
- Advisory hold (web-only) with durable `.devrelay/web/run_holds.json`,
  confirmation-gated hold/release and manual-prompt blocking.
- Session lease store foundation (`.devrelay/web/session_leases.json`), tested
  but not wired and with no switch endpoint.
- Reproducibility comparison helper (`scripts/compare_builds.py`) — harness only;
  no reproducibility claim.

## Pause — advisory hold implemented, true pause still design-only

Detailed proposal: [v0.5/PAUSE_DESIGN.md](v0.5/PAUSE_DESIGN.md).

The accepted orchestration state machine has no pause state.  Adding one is not
a rename of `interrupt`: interrupt is an abort request, not a pause.

Options considered:

1. **App-level hold gate** — reject the next model-bearing action while allowing
   an already in-flight turn to finish; the run state is unchanged.  Clear,
   resumable and small, but it cannot pause an executing provider turn.
2. **New `PAUSED` state** — a true state transition, but it needs decisions for
   in-flight turns, recovery, decisions, limits and terminality.  This is a
   state-machine change requiring a v0.5 design review.
3. **Process supervisor stop** — out of scope and dangerous: it would stop the
   whole web process, not one run.

Recommended direction: implement (1) first as an explicitly advisory hold,
visible in run detail, with a `pause_requested`/`resume` evidence trail; do not
pretend the provider is paused.  A true `PAUSED` state remains a separate v0.5
gate.  No endpoint is exposed today.

## OpenCode session switching — design only, not implemented

Detailed proposal:
[v0.5/SESSION_OWNERSHIP_DESIGN.md](v0.5/SESSION_OWNERSHIP_DESIGN.md).

Current D1 behavior is project activation plus run-recorded session inventory.
It does **not** switch a run to another OpenCode session.

Requirements before any switch endpoint:

- a durable session ownership/lease record (store foundation now exists, but it
  is not wired to any product path);
- proof that the target session belongs to the same workspace and is not used by
  another in-flight run;
- an explicit turn-boundary operation, not an arbitrary session-id parameter;
- recovery semantics when the old session has a pending reply.

Until those exist, the only session operations remain the run's own manual
prompt/read/interrupt.  A `session_id` request field is not accepted.

## Reproducible build / lock file — harness only, not proven

Detailed plan: [REPRODUCIBILITY_PLAN.md](REPRODUCIBILITY_PLAN.md).

The SBOM records resolved versions but the build is not byte-reproducible:
`pip install ".[web]"` resolves open ranges at release time, PyInstaller embeds
non-deterministic metadata, and no lock/SBOM hash chain is enforced.

A future pass should:

- generate a platform/Python-specific constraints lock for the portable build;
- install with `--no-deps`/constraints in a clean environment;
- compare a normalized SBOM and a second build digest;
- only then make a reproducibility claim.

No lock file is being invented from the current dev environment.

## v0.3-E platform gates — external evidence still open

Preparation checklist: [v0.3/V03E_GATE_PREP.md](v0.3/V03E_GATE_PREP.md).

The mandatory fail-closed core is shipped, but the platform gates are not
complete and cannot be closed by editing this repository:

- G0.4/P4: authoritative **FAIL / P4 UNPROVEN** (no OpenCode base endpoint).
- G0.5/P6: **NOT RUN / P6 UNPROVEN**; local reachability gap.
- G1/G2: **NOT RUN**.

`adopt_completed_turn` stays **disabled**.  Closing these gates requires a real
OpenCode instance, frozen oracles/authorizations and independent review; no
offline test can substitute.  See `docs/v0.3/V03_PLAN.md` and
`docs/v0.3/V03E_ACCEPTANCE.md`.

## Suggested order

1. Pause design review (advisory hold only) — v0.5.
2. Reproducibility/lock proof — before claiming deterministic portable builds.
3. Session ownership/lease design — before any session-switch endpoint.
4. v0.3-E platform gates — only when real-platform evidence is available.
