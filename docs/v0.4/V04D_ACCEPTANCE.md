# DevRelay v0.4-D1 — owner acceptance record

Status: **ACCEPTED / CLOSED by the owner on 2026-10-22.**  This is a D1 stage
acceptance, not a v0.4 release; no tag or publication was created.

## Accepted scope

D1 adds:

- `POST /api/projects/{project_id}/activate` — registry-id-only, header+body
  confirmation, fresh service built outside the lock, no-await atomic swap;
- active project is process-local and non-persistent;
- `GET /api/sessions` — run-recorded implementer/reviewer session inventory with
  bounded run ids and truncation flags, no arbitrary session lookup or switch;
- UI project selector/activation and Sessions list, with workspace-epoch guards.

## Evidence

| Item | Value |
| --- | --- |
| Implementation commit | `9337d40` |
| CI | [run 39832216525](https://github.com/YingQiu0871/DevRelay/actions/runs/39832216525) — 8/8 jobs |
| Local suite | 1,342 collected — 1,340 passed + 2 environment skips |
| Review | independent read-only review: REQUEST CHANGES (one P1) → remediated to APPROVE WITH FINDINGS, P0/P1 = 0 |
| Review record | [V04D_REVIEW.md](V04D_REVIEW.md) |
| Tests | activation confirmation/auth/422, invalid id 404, failure rollback, concurrent activation, post-switch isolation, health id, session inventory/auth |

## Limitations carried forward

- Active project selection is in-memory; restart returns to the CLI workspace.
- A registered root replaced at the same path is trusted (same-user registry
  residual); activation rejects non-absolute roots.
- OpenCode session switching/ownership transfer is not implemented.
- HTTP project add/remove and archived-run mutation are not implemented.
- `/api/projects` continues to expose absolute roots to an authenticated local
  caller as part of the accepted registry view.

## Immutability

`v0.3.0` remains the published release.  D1 is unreleased `main` work.
