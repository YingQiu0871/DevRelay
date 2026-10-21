# DevRelay v0.4-A2 — independent review record

Status: **A2 re-reviewed: APPROVE WITH FINDINGS (P0/P1 = 0); the two P2
findings were remediated, and A2 was accepted by the owner on 2026-10-22.**
This is a stage acceptance, not a tag or release.  A1 remains APPROVE WITH
FINDINGS with R1 resolved by the header-session change.  See
[V04A_ACCEPTANCE.md](V04A_ACCEPTANCE.md).

- Review target: the A2 `PUT /api/config` implementation and the R1 header
  session migration.
- First verdict: **REQUEST CHANGES** (P0 = 0, P1 = 2, P2 = 4, P3 = 5).
- Re-review verdict after remediation: **APPROVE WITH FINDINGS** (P0 = 0,
  P1 = 0); the remaining P2s and P3s are recorded below.  No A2 tag or release
  is implied.

## Blocking findings and remediation

| ID | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| A2-P1-1 | P1 | A full-document write could repoint `codex.executable`, `opencode.base_url`/`workspace` and `profiles`, turning authenticated config write into arbitrary execution/wiring control. | Fixed by a curated allowlist and a merge-over-current patch model.  `codex.executable`, `codex.args`, `codex.launcher_args`, `opencode.base_url`, `opencode.workspace`, `opencode.allow_unknown_workspace`, `profiles` and `tests.targeted`/`tests.full` are rejected with `422 config_field_not_editable`; current values are preserved. |
| A2-P1-2 | P1 | The write could change task policy and shell-valued test commands. | Clarified and narrowed: policy fields are editable for **future** tasks only; a running task's frozen snapshot is never rewritten.  Shell-valued `tests.targeted`/`tests.full` are not editable.  The live process keeps its startup wiring and reports `restart_required`. |

## Non-blocking findings

| ID | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| A2-P2-1 | P2 | TOCTOU between digest read and replace; concurrent PUTs could lose an update. | In-process `RLock` serializes writers; the digest is re-read and the backup is taken under the lock immediately before replace.  External-editor races remain optimistic (documented); no cross-process filesystem lock is claimed. |
| A2-P2-2 | P2 | `yaml.safe_dump` could fail after validation reported success. | Serialization now occurs inside the shared validation path and is mapped to `422 config_not_serializable`; no backup or write occurs first. |
| A2-P2-3 | P2 | Secret scanning missed `sk-ant-*`, `Basic`, `AKIA*`, `xox*`, URL userinfo and PEM values. | Expanded value regex and key screening; tests cover `Bearer`, `sk-ant-*` and `Basic`.  This is a safety net, not a proof that every possible credential encoding is detected. |
| A2-P2-4 | P2 | Empty/partial documents could erase wiring, and `profiles` could persist an invalid selector. | A2 is now a merge patch: omitted fields are preserved; an empty patch is an explicit no-op; `profiles` is not editable. |
| A2-P3-1 | P3 | Symlinked config could be silently replaced. | Symlinked config is rejected with `409 config_symlink_rejected`; the regression test skips only when the host cannot create symlinks. |
| A2-P3-2 | P3 | Backup accumulation/orphan backup on write failure; no Windows directory fsync. | Backup accumulation is recorded as a future hygiene item; an orphan backup is retained rather than deleted because it preserves the pre-write bytes.  Windows directory fsync is intentionally skipped. |
| A2-P3-3 | P3 | Body `confirm` check was dead after the pydantic literal; a stray invalid `Authorization` header overrode a valid session. | Dead check removed (missing body `confirm` is `422`).  An invalid `Authorization` now falls through to a valid session header; no session means `401`. |
| A2-P3-4 | P3 | `GET /api/config` after PUT mixed the new digest with old startup wiring. | Response adds `restart_required`; the spec documents that the live process reloads on restart. |
| A2-P3-5 | P3 | Documentation drift (PUT absent from route table, stale A2-absent text, read-only docstring). | Corrected in `V04A_SPEC.md`, `V04A_REVIEW.md`, `ROADMAP.md`, `PROJECT_STATUS.md` and the service docstring. |

## Re-review disposition

The re-review found no P0/P1.  Two P2 items were raised and fixed after that
review:

- `review.provider` was editable wholesale.  The allowlist now names only the
  non-provider review-policy fields; `review.provider` is rejected.
- Cross-process writers could both pass the digest check.  A best-effort
  `.devrelay/web/config.lock` advisory lock (msvcrt on Windows, flock on POSIX)
  now serializes writers with a 5-second timeout and `409 config_busy`.

The remaining P3 notes are retained: validate/apply missing-file asymmetry was
closed (validate now requires an existing file), post-replace directory-fsync
errors are ignored, and the symlink-check/read TOCTOU and backup accumulation
remain documented limitations.  A2 is **accepted with findings**, not tagged or
released.
