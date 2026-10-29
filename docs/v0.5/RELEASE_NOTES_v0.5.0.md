# DevRelay v0.5.0 — release notes

Status: **RELEASE CANDIDATE (2026-10-29).**  Not published until the tag,
draft Release, `release.yml` run and PyPI upload are recorded in
[RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) § v0.5.0.

## Highlights

v0.5.0 is the post-v0.4 hardening line on top of the v0.4 Web control plane:

- **Supply chain**: CycloneDX 1.5 SBOM for the portable runtime closure, a
  five-asset release gate (wheel, sdist, `SHA256SUMS`, portable zip, SBOM),
  Node.js 24 action pins, published-version reruns that skip the Windows
  rebuild, and a Windows/Python 3.13 release lock with a passed double-build
  proof.
- **Durable run controls**: manual-prompt pending markers survive restarts
  (metadata only) with a confirmed recovery action; an advisory run hold blocks
  new web prompts and MCP implementer/reviewer actions.
- **Session ownership**: durable session leases acquired at
  `devrelay_start_run`, released on terminal outcomes, with explicit recovery.
- **Session switch (v3 run schema)**:
  - `POST /api/runs/{run_id}/session/switch` verifies the target belongs to
    the workspace, holds a pending target lease, appends validated
    `session_switch_history` evidence and atomically commits the lease;
  - WebUI run-detail switch panel with explicit confirmation and no automatic
    retry;
  - `POST /api/runs/{run_id}/session/switch/recover` resolves a
    pending/uncertain switch from the durable run document (commit or abort),
    failing closed on any mismatch.

## Install / upgrade

- PyPI: `python -m pip install devrelay==0.5.0`
- GitHub Release: wheel, sdist, `SHA256SUMS`,
  `DevRelay-Portable-Windows-x64.zip`, `DevRelay-SBOM.cdx.json`

The portable zip is unsigned.  Extract it as a whole and verify `SHA256SUMS`
before running `devrelay.exe`.

v1/v2 run documents stay readable; only v3 runs can carry switch history.
There is no automatic migration.

## Security notes

- Every new write endpoint requires `X-DevRelay-Confirm: apply` plus a body
  `confirm: "apply"`; session ids come from the run or are verified by the
  OpenCode bridge, never trusted from the client.
- Lease and switch recovery perform no provider I/O; switch recovery writes no
  run document.
- Markers, holds and leases store metadata only — no prompt text, replies or
  tokens.

## Known limitations

- `adopt_completed_turn` stays **disabled**.  v0.3-E platform gates:
  G0.1/P7, G0.2, G0.3/P5 PASS; G0.4/P4 authoritative FAIL / P4 UNPROVEN;
  G0.5/P6, G1, G2 NOT RUN.
- Switch run write and lease commit are not one cross-store transaction; a
  failure between them needs the explicit resolve action.  A run whose switch
  target lease was released by generic lease recovery before the resolve
  endpoint existed cannot switch again without manual lease re-attachment.
- One Web writer and one MCP surface per workspace; multi-process writers are
  unsupported.
- Active project selection is in-memory; advisory hold is not a provider pause;
  interrupt is still an abort.
- No `.exe` installer, code signing, winget/scoop or auto-update; the portable
  build has no hash-pinned wheelhouse or cross-runner reproducibility guarantee.

## Verification

Recorded in [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) § v0.5.0.
