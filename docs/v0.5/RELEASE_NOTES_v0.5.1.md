# DevRelay v0.5.1 — release notes

Status: **PUBLISHED 2026-10-29.**  Tag `v0.5.1` peels to
`9135150883a423b9ea18749d752ff033dc47b1c6`; PyPI and the GitHub Release are
public.  Evidence is recorded in [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md).

## Highlights

v0.5.1 is a patch release on top of [v0.5.0](RELEASE_NOTES_v0.5.0.md).  It closes
the 0.5.0 known limitation where a run could not switch again after its switch
target lease had been released through generic lease recovery:

- `POST /api/runs/{run_id}/session/lease/reattach` (`role`,
  `expected_updated_at`, `confirm: "apply"`, header `X-DevRelay-Confirm: apply`)
  gives the run's current role session an active lease again and releases any
  other active lease left for the same run/role (the orphaned source) in the same
  write.  The run can then switch again.
- Refused, with nothing written, for a terminal run (`run_terminal`), a stale
  revision (`run_changed`), an unresolved switch (`switch_pending`), a session
  that already holds the lease (`lease_already_active`) or a session leased by
  another run (`session_leased`).
- `GET /api/runs/{run_id}` reports `role_leases` per role, and the WebUI run
  detail shows a confirmed **Re-attach lease** control.

## Install / upgrade

- PyPI: `python -m pip install devrelay==0.5.1`
- GitHub Release: wheel, sdist, `SHA256SUMS`,
  `DevRelay-Portable-Windows-x64.zip`, `DevRelay-SBOM.cdx.json`

The portable zip is unsigned.  Extract it as a whole and verify `SHA256SUMS`
before running `devrelay.exe`.

## Security notes

- Re-attachment performs no provider I/O and writes no run document; the session
  id comes from the run document, never from the client.

## Known limitations

Unchanged from 0.5.0 except the closed re-attachment item:

- `adopt_completed_turn` stays **disabled**.  v0.3-E platform gates:
  G0.1/P7, G0.2, G0.3/P5 PASS; G0.4/P4 authoritative FAIL / P4 UNPROVEN
  (confirmed by the 2026-10-29 rerun); G0.5/P6, G1, G2 NOT RUN.
- Switch run write and lease commit are not one cross-store transaction; a
  failure between them needs the explicit resolve action.
- One Web writer and one MCP surface per workspace; active project selection is
  in-memory; advisory hold is not a provider pause; interrupt is still an abort.
- No `.exe` installer, code signing, winget/scoop or auto-update.

## Verification

Recorded in [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md) § v0.5.1.
