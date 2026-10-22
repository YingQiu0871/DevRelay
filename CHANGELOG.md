# Changelog

All notable changes to DevRelay are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- v0.4-A1 local HTTP control API: a loopback-only Starlette/uvicorn service with
  bearer and header-borne session authentication, Host/Origin validation,
  bounded request bodies, an explicit project registry, and `devrelay web
  serve` / `devrelay web project ...` commands.  The optional `web` extra keeps
  the core CLI small.
- v0.4-A2 backend-owned configuration write: `PUT /api/config` with a current
  SHA-256 guard, `X-DevRelay-Confirm: apply`, allowlisted `WorkspaceFile`
  validation, secret-key/value rejection, a cross-process writer lock, an
  owner-only backup, and atomic replacement.  Comments are not preserved; the
  live process reloads on restart.  Review and the resolved localhost
  cookie-scope item are recorded in `docs/v0.4/V04A_REVIEW.md` and
  `docs/BACKLOG.md`.
- v0.4-B local WebUI: a static, no-build single page served at `/` by
  `devrelay web serve`, with fragment-token login, header sessions, summary
  cards, an allowlisted configuration form, read-only wiring display, status
  and recent runs.  The UI uses `X-DevRelay-Session`, a self-only CSP, fixed
  assets and no cookies; it deliberately does not edit OpenCode
  endpoint/workspace, profiles, argv or test shell commands.
- v0.4-B2 wiring API: `GET/PUT /api/wiring` writes only a **loopback**
  `opencode.base_url` through the same digest/confirmation/backup/atomic-write
  discipline as A2.  The response exposes credential environment names and a
  configured boolean, never the token, plus read-only local-stdio MCP metadata;
  remote endpoints, workspace overrides, `allow_unknown_workspace`, executables,
  argv, profiles and provider selection remain excluded.  A Connections tab
  drives it.
- v0.4-C1 read-only run dashboard: click-through run detail with state, cycle,
  budget, route snapshot, implementer/reviewer turn evidence, decision history
  and blocked/recovery reasons, plus manual refresh and optional 5-second
  auto-refresh.  No pause/interrupt/prompt/decide action is added; those remain
  C2.
- v0.4-C2a read-only task artifact dashboard: `GET /api/tasks` and
  `GET /api/tasks/{task_id}` expose test evidence, review findings/history,
  task-relative diff **stat only**, provider-call/review-attempt accounting and
  final-gate/blocked state.  Task IDs are grammar-checked, all text is bounded
  and redacted, token/cost data is explicitly unavailable, and no task/run
  control or full diff is exposed.
- v0.4-C2b bounded run control: `POST /api/runs/{run_id}/decide` records one of
  complete/request_changes/stop with an `expected_updated_at` guard, and
  `POST /api/runs/{run_id}/interrupt` aborts only the run's own
  implementer/reviewer session.  Both require `X-DevRelay-Confirm: apply` and an
  explicit body `confirm`.  Pause, manual prompt, raw streaming and run phase
  execution remain out of scope.
- v0.4-C2c manual prompt + normalized polling: `POST /api/runs/{run_id}/prompt`
  sends one bounded prompt to the run's implementer/reviewer session (no
  in-flight turn, no retry/fallback), and `GET /api/runs/{run_id}/messages`
  returns a cursor-windowed, redacted and bounded normalized message page.
  The UI confirms prompts and optionally polls every 5 seconds.  Pause remains
  unsupported because the state machine has no pause state; no WebSocket/SSE
  transport is added.
- v0.4-D1 project/session management: `POST /api/projects/{project_id}/activate`
  switches the active registered project in-memory under a lock with an explicit
  confirmation, and `GET /api/sessions` lists run-recorded implementer/reviewer
  session metadata.  The UI gains a project selector and Sessions list.  Active
  selection is not persisted across restarts; arbitrary paths/session ids,
  OpenCode session switching and HTTP project add/remove remain out of scope.
- v0.4-E1 packaging: the release workflow builds a PyInstaller onedir
  `DevRelay-Portable-Windows-x64.zip` on a Windows runner, includes it in
  `SHA256SUMS`, attaches it to the draft Release and requires it before
  publication.  The portable build is unsigned and has no installer/PATH/
  auto-update behavior.  The `.exe` installer, code signing and package-manager
  manifests remain deferred.

## 0.3.0 - 2026-10-21

Earlier entries record the status at their date.

Version `0.3.0` is single-sourced in `pyproject.toml` and in the
`src/devrelay/__init__.py` fallback constant, and is what `devrelay version`
reports.  The tag-driven workflow in `.github/workflows/release.yml` publishes
this release (2026-10-21); publication results are recorded in
`docs/RELEASE_CHECKLIST.md`.

### Added

- The v0.3 stage series is in the package: the OpenCode session bridge (v0.3-A),
  the ChatGPT/MCP stdio tool surface (v0.3-B), semantic agent role routing
  (v0.3-C), bounded orchestration (v0.3-D) and the v0.3-E mandatory fail-closed
  recovery core (local read-only reconciliation plus a one-shot
  `mark_unrecoverable`).
- `devrelay mcp serve --workspace <project>` exposes **19 MCP tools** over the
  official MCP Python SDK: eleven `devrelay_*` tools (including
  `devrelay_reconcile_run` and `devrelay_resolve_recovery`) and eight
  `opencode_*` tools.
- Offline CI (`.github/workflows/test.yml`, Python 3.11-3.14 on Linux and
  Windows) and a tag-driven release workflow
  (`.github/workflows/release.yml`).

### Changed

- Package version `0.1.0` -> `0.3.0` (`pyproject.toml`,
  `src/devrelay/__init__.py`); `tests/test_version.py` pins the release version
  to the packaged one.  The MCP server banner keeps its own `0.3.0-e`
  identifier.
- The sdist ships the packaged policy profiles
  (`recursive-include src/devrelay/profiles *.yaml` in `MANIFEST.in`).
- Recovery: adoption is refused structurally before any run mutation; a terminal
  run is refused as `orchestration_invalid_transition` before the
  adoption-disabled check.
- Recovery: the recovery reason is derived from the strict local ledger scan
  (W3/W4 `submission_uncertain`, W5/W6 `reply_pending`) rather than from bridge
  flags alone.
- The orchestration store now fsyncs a run document's temp file before
  `os.replace` (and the parent directory on POSIX); Windows cannot fsync a
  directory, so cross-power-loss rename durability is not claimed there, and the
  OpenCode call ledger still does not fsync.

### Security

- Publishing uses PyPI trusted publishing (GitHub OIDC, `pypi` environment, no
  stored credentials, attestations enabled).  The workflow validates the tag
  shape, pins the tag to the packaged version, requires the tag to be reachable
  from `origin/main`, requires a **draft** GitHub Release whose built artifacts
  the workflow uploads (the Release is undrafted only after PyPI and the three
  assets verify), and passes `workflow_dispatch` inputs to the shell only
  through environment variables.
- The Codex child keeps its explicit credential denylist (reviewer credentials,
  `DEVRELAY_OPENCODE_TOKEN` and common provider keys) - an explicit denylist,
  not general secret isolation.

### Known limitations

- v0.2-A (automatic review loop), v0.2-B (project profiles / frozen-policy
  integrity) and v0.2-C (structured Codex runtime) remain **candidates under
  independent review**; they were validated offline with fake providers only.
- v0.3-A to v0.3-D are accepted internally and closed, and shipped in 0.3.0.
- v0.3-E is scoped to the mandatory fail-closed core: `adopt_completed_turn`
  stays **DISABLED**, there is no automatic resume, and remote correlation was
  never exercised.  The **OpenCode call ledger** assumes a single writer and
  issues no `fsync`, so durability against power loss is not claimed there (the
  orchestration store now fsyncs — see *Changed* above).
- The platform proof gate stays **partially executed / not complete**:
  G0.1/P7 = PASS, G0.2 = PASS, G0.3/P5 = PASS, G0.4/P4 = authoritative FAIL /
  P4 UNPROVEN (no OpenCode base endpoint in the accepted workspace, 0 `GET /doc`
  issued), G0.5/P6 = NOT RUN, and G1/G2 not run.
- The offline test suite is 1,271 tests (`python -m pytest -q`; 1,270 pass and
  one POSIX-only test is skipped on Windows); it needs no model, no network and
  no installed Codex CLI.

## v0.3-E (2026-10-17) - mandatory fail-closed core accepted

**Design frozen.  Mandatory fail-closed core implemented and independently accepted (P0 = 0, P1 = 0, P2 = 2; 2026-10-17); adoption disabled; platform gates open; subsequently released in 0.3.0 (2026-10-21).**  The independent
design-freeze review approved candidate
`9f4a01804b9affe8938a272553df345b5a60aeed` with **P0 = 0, P1 = 0, P2 = 0** and
F1-F12 **CLOSED**, decision *APPROVE V0.3-E FAIL-CLOSED CORE DESIGN; PLATFORM PROOF
GATE REQUIRED BEFORE IMPLEMENTATION*.  Implementation was subsequently authorized
(`docs/v0.3/V03E_IMPLEMENTATION_AUTHORIZATION.md`, owner-issued and spent) and the
mandatory fail-closed core is implemented - `docs/v0.3/V03E_IMPLEMENTATION.md` - and
was independently accepted for that scope (`docs/v0.3/V03E_ACCEPTANCE.md` §0,
P0 = 0, P1 = 0, P2 = 2; adoption disabled, no platform gate claimed).  The
platform proof gate is **not complete** (**G0.1 / P7 = PASS** — authoritative,
independently approved by *APPROVE V0.3-E G0.1 / P7 PLATFORM PROOF* with
P0 = 0, P1 = 0, P2 = 0; G0.3 failed its original oracle, was independently reviewed as a TYPE-1 proof-plan failure and then independently approved after the corrected clean rerun - **G0.3 / P5 = PASS** - (see below); G0.4-G0.5, G1, G2 not run at freeze time (G0.4 has since been executed once and is an authoritative `FAIL / P4 UNPROVEN` - see below); G0.2 ran and, after one `REQUEST_CHANGES` review, was cleanly re-run under a precommitted oracle and then independently approved - `G0.2 = PASS` - see below), `adopt_completed_turn`
remains **disabled**, and
the recorded P3 observations (P3-1, P3-2, P3-4/P3-5) stay non-blocking.

**G0.1 / P7 (local ledger persistence under hard kill) was executed once** after the
freeze and produced a candidate result: six planned case executions (before the
durable ISSUED write, during that write, after ISSUED but before settlement, during
settlement publication, after settlement publication, and a corrupted-record
control) all met their predefined criteria against the real accepted ledger
persistence path, with the corruption-strict scanner never treating malformed
evidence as absence while the tolerant accounting reader demonstrably did.  That
candidate result was *CANDIDATE PASS / REQUIRES INDEPENDENT REVIEW*; the first
independent proof review returned `REQUEST_CHANGES` for **bookkeeping/status wording
only** (P0 = 0, P1 = 0, P2 = 1 - the evidence itself was found sufficient; fixed in
`8997071`), and the final independent proof review then issued
**APPROVE V0.3-E G0.1 / P7 PLATFORM PROOF** (P0 = 0, P1 = 0, P2 = 0), so
**G0.1 / P7 = PASS** (authoritative, independently approved) and it no longer blocks
mandatory-core implementation *eligibility*; implementation nonetheless remains
**not authorized** until a separately issued implementation authorization.  The
remaining gate steps (G0.3-G0.5, G1, G2) had **not** run at that point, so the platform
proof gate was recorded as **partially executed / not complete** (not passed, not
complete); `adopt_completed_turn` remains disabled, and 0 real provider/model calls were
made.  Evidence: `docs/v0.3/V03E_G0_1_P7_PROOF.md` (later rounds are recorded below).

**G0.2 (offline run<->call false-correlation proof) was executed once** at `4448f92`
with no runtime change and returned a **candidate pass**: all ten planned cases (A-J)
behaved fail-closed against real production-generated corpora (a live in-flight intent
from a real crash boundary plus the accepted ledger written by the real bridge/ledger
classes, offline).  A unique exact correlation is possible only when the complete
frozen identity tuple matches exactly one record in the run's role session; the
same-session/different-attempt, identical-prompt, weak-field-only, stale-cycle,
wrong-role/operation, foreign-run, duplicate, missing-identity and corrupt-look-alike
cases all end in `NO_MATCH` / `evidence_conflict` / `evidence_gap` / `corruption`
with no false attribution and no timestamp tie-break, and the corruption-strict scan
wins over a clean unique candidate (the tolerant accounting reader would silently skip
the torn artifact and claim uniqueness).  Two central findings: the ledger carries
**no run identity and no cycle/attempt identity**, and a live in-flight attempt never
durably contains the ledger `call_id`.  That round's result was a candidate pass; the
first independent review returned `REQUEST_CHANGES` (P0 = 0, P1 = 0, P2 = 2), and a
separately authorized **clean G0.2 re-run** was then executed under an oracle
precommitted in commit `12ea1b7` (`docs/v0.3/V03E_G0_2_RERUN_ORACLE.md`): the ten fixed
cases A-J ran once each, every verdict stayed inside its precommitted allowed set, the
oracle was unchanged during execution and no weak metadata produced an attribution.
That clean re-run was then independently reviewed and approved (**APPROVE V0.3-E G0.2
FALSE-CORRELATION PROOF**, P0 = 0, P1 = 0, P2 = 0), so **G0.2 = PASS** (authoritative,
independently approved).

**G0.3 (transport / non-delivery classification, P5) was executed once** offline at
`efa2ca3` under the oracle precommitted in `b9c4704`
(`docs/v0.3/V03E_G0_3_TRANSPORT_ORACLE.md`) and returned a **candidate FAIL**: all six
accepted non-delivery classes (`connect_timeout`, `pool_timeout`, `connect_error`,
`proxy_error`, `unsupported_protocol`, `local_protocol_error`) were independently shown
pre-send on the installed stack (no request header or body byte reached the network
stream), and every uncertain class stayed uncertain with `retry_safe` false; but
precommitted case G0.3-J (`write_error`) surfaced as `remote_protocol_error` instead of
its precommitted class because the installed httpcore suppresses a request-send
`WriteError` and continues to the read phase.  No non-delivery safety property was
violated and no capability depends on P5 (informational only), but per the precommitted
standard the candidate result is **FAIL** and the affected case/class is named.  0 real
provider/model calls, 0 real network requests.  Evidence:
`docs/v0.3/V03E_G0_3_TRANSPORT_PROOF.md`.  That failure was then independently reviewed
as **FAIL - V0.3-E G0.3 / P5 PROOF - TYPE 1 PROOF-PLAN FAILURE** (P0 = 0, P1 = 0, P2 = 0):
the candidate correctly failed its immutable oracle, case J's exact classification
expectation was wrong for the installed HTTP/1.1 request-send path, **no accepted
safe/non-delivery classifier bucket was shown to be unsafe**, and **no runtime
remediation is required**; a corrected clean rerun was separately authorized under a new
precommitted oracle (`docs/v0.3/V03E_G0_3_RERUN_ORACLE.md`).

**Corrected clean G0.3 / P5 rerun (executed once, one semantic execution per case):**
The corrected clean rerun was then independently reviewed and approved (**APPROVE
V0.3-E G0.3 / P5 TRANSPORT PROOF**, P0 = 0, P1 = 0, P2 = 0), so **G0.3 / P5 = PASS**
(authoritative, independently approved).  Under the corrected oracle
(`e328ec5`, manifest SHA-256 `9e4c7de6…`) the accepted safe buckets are class-wide
pre-send on the installed stack — `connect_timeout`, `pool_timeout`, `connect_error`,
`unsupported_protocol`, and the pre-send-only `local_protocol_error` mapping boundary (the
h11 request-construction mapping) — with no request header or body byte on the wire;
`proxy_error` is recorded as **UNREACHABLE_CURRENT_CONFIGURATION** (no proxy in the
accepted configuration, `trust_env=False`); every uncertain class (`read_timeout`,
`write_timeout`, `read_error`, `remote_protocol_error`, `close_error`) stayed
`submission_uncertain=True` with `retry_safe=False`; the corrected case J surfaced
`remote_protocol_error` with uncertainty exactly as precommitted (httpcore suppresses the
request-send `WriteError`), while `write_error` stays a defensive, unexercised mapping;
HTTP rejection (500) and the success control were never treated as non-delivery; and the
unmapped mid-send h11 escape path is recorded as a fail-closed observability limitation
(no runtime change).  0 provider/model calls, 0 network requests, 0 OpenCode processes.
Evidence: `docs/v0.3/V03E_G0_3_CLEAN_RERUN_PROOF.md`.  G0.1/P7 and G0.2 are authoritative PASS and mandatory-core
implementation remains **not authorized** pending a separate authorization; the
platform proof gate stays **partially executed / not complete** (G0.3/P5 = PASS,
authoritative; G0.4/G0.5/G1/G2 not run at that point; G0.4 has since been executed once and is an
authoritative **FAIL / P4 UNPROVEN** - the accepted workspace had no OpenCode base endpoint, so no
target instance could be bound and 0 `GET /doc` were issued: `docs/v0.3/V03E_G0_4_API_INSPECTION_PROOF.md`)
and
`adopt_completed_turn` stays **disabled**.  Clean-rerun evidence:
`docs/v0.3/V03E_G0_2_CLEAN_RERUN_PROOF.md`; original record (preserved):
`docs/v0.3/V03E_G0_2_FALSE_CORRELATION_PROOF.md`.

**G0.4 (installed-API inspection for a per-operation pending handle, P4) was executed
once** under its approved immutable revision-3 oracle
(`docs/v0.3/V03E_G0_4_API_INSPECTION_ORACLE.md`, committed-blob SHA-256 `b0c34fa1…`).
Case A could not establish `TARGET_BOUND`: the accepted workspace configuration
(`.devrelay/config.yaml`) resolves no OpenCode endpoint (`opencode.base_url` is empty;
`OpenCodeConfig.configured` is false), and DevRelay never discovers servers by scanning
ports or processes - so no target instance, listener or responder could be bound and the
binding reason is `TARGET_IDENTITY_UNRESOLVED`.  The precommitted failure path applied:
**0 loopback HTTP requests, 0 `GET /doc`**, cases B-H not executed, no substitute or
historical evidence, no rerun.  Final semantic outcome for the round:
`EVIDENCE_INSUFFICIENT` -> executor-stage **CANDIDATE FAIL / P4 UNPROVEN**.

The independent failed-proof review then issued **APPROVE V0.3-E G0.4 FAILED PROOF** with
**P0 = 0, P1 = 0, P2 = 0** and failure classification **TYPE 3 - SEMANTIC ENVIRONMENT /
CONFIGURATION RESULT** (the accepted workspace supplied no OpenCode base endpoint), which
makes the result authoritative: **G0.4 / P4 = FAIL / P4 UNPROVEN**.  No API/schema property
was established, so nothing follows about whether a durable per-operation handle exists;
P4 remains formally unproven, a rerun of this execution is **not authorized**, and repairing
the configuration would be a **new** execution requiring new external authorization under the
same immutable oracle.  The installed target's static identity was recorded
(`opencode-ai` 1.18.11, declared bin `./bin/opencode.exe`, executable SHA-256
`578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35`).  0 provider/model
calls, 0 network requests, 0 OpenCode starts/restarts.  Evidence:
`docs/v0.3/V03E_G0_4_API_INSPECTION_PROOF.md`.

**G0.5 / P6 definition was remediated** (documentation/definition only; no oracle, no
proof, no execution).  A prior read-only inventory returned *NOT READY — G0.5 DEFINITION
AMBIGUITY* (no frozen PASS/FAIL semantics, no method, no identity-dimension set, identity vs
ownership undefined, and an adoption-role contradiction between §19, §25, §27, §28 and E33).
The remediation freezes **P6 as a local identity/ownership VETO BOUND on adoption — not an
adoption-enabling proof**: G0.5 PASS clears only the local veto prerequisite and enables
nothing by itself, while G0.5 FAIL leaves the veto active and adoption DISABLED.  The
remote/platform *enabling* proofs remain **P1+P2+P3+P8 (+P9 if applicable)** through G1/G2,
and **both classes must be satisfied before adoption may ever be authorized**.  The frozen
definition (`V03E_SPEC.md` §25.1) fixes the exact question, the identity/ownership
definitions, the fail-closed original-owned-session rule, exactly **four case classes A–D**
(missing; foreign; recreated/originality-unprovable; copied — with **`session_id` equality
alone insufficient**), a **bounding PASS**, FAIL and insufficient-evidence semantics, a
**local/offline method** (0 HTTP, 0 `/doc`, 0 OpenCode start/restart, 0 session mutations, 0
provider/fake-provider calls; the missing G0.4 `base_url` is therefore **not** a G0.5
prerequisite), the identity-dimension matrix, the adoption dependency equation, evidence
fields, privacy rules, the status model and the no-probe-shopping discipline.  At that point
G0.5 remained **NOT RUN / DEFINITION REMEDIATED / AWAITING INDEPENDENT DEFINITION REVIEW**
(superseded by the accepted status recorded below); no G0.5 oracle existed and G1/G2 remained
unrun.

**G0.5/P6 oracle construction was attempted and stopped by a LOCAL REACHABILITY GAP.**  The
definition baseline was accepted by independent review (*APPROVE V0.3-E G0.5
ADOPTION-DEPENDENCY CLEANUP*, P0 = 0, P1 = 0, P2 = 0; commit `ad86a79`; the substantive §25.1
block was preserved byte-for-byte, SHA-256 `d3244ee0…`).  A pre-run oracle construction round
then performed a purely static, per-case source-reachability check against existing local
enforcement: **Case A (missing)** binds to the blank/missing session-reference validation,
**Case B (foreign)** to the pure session↔workspace ownership primitive, and **Case D (copied)**
to the run↔workspace binding check — but **Case C (recreated / originality-unprovable) has no
existing local original-session/provenance enforcement path**, so a complete four-case oracle
cannot be frozen; constructing one would require proof-only policy code or a new runtime
primitive, both prohibited.  The independent review approved that outcome (*APPROVE V0.3-E
G0.5 ORACLE FREEZABILITY FAILURE*, P0 = 0, P1 = 0, P2 = 0), classifying it as **C —
NOT-YET-IMPLEMENTED V0.3-E ENFORCEMENT PREREQUISITE** (not a definition defect, not a proof
failure, not a harness failure, not an installed-platform limitation).  **No G0.5 oracle was
created, no semantic case was executed, and therefore there is no G0.5 PASS and no G0.5
FAIL**: `G0.5/P6 = NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY
GAP`, with **P6 = UNPROVEN / UNSATISFIED**.  Adoption stays DISABLED, the mandatory core is
unaffected (G0.1/P7 remains the only hard gate and stays PASS/CLOSED), and G1/G2 remain unrun;
the attempt caused 0 runtime/test/config changes and 0 provider/HTTP/OpenCode activity.

**A new prerequisite information finding — G0.5-PRE / SIC (session-incarnation capability
finding) — was defined** (definition candidate only; nothing executed).  The independently
approved Case-C prerequisite design block (*APPROVE V0.3-E CASE-C PREREQUISITE DESIGN BLOCK*)
confirmed the stronger thesis **`BLOCKED — NO SOUND ORIGINAL-SESSION PROVENANCE ANCHOR
AVAILABLE`**: no currently accepted evidence source can soundly support ORIGINAL OWNERSHIP
PROVEN, purely local nonce/fingerprint approaches are not provenance, a fail-always guard
would permanently remove capability C and is therefore a product-scope change, G1/P1 does not
prove session incarnation, G2/P2/P3/P8/P9 do not themselves prove it, and G0.4/P4 is
unrelated and stays CLOSED.  SIC asks whether OpenCode 1.18.11 exposes, through a read-only
session representation, a per-session-incarnation property (or tuple) whose semantics are
strong enough to serve as a provenance anchor, with four precommitted outcomes
(`SIC_PRESENT_AND_SEMANTICS_ESTABLISHED`, `SIC_METADATA_PRESENT_BUT_SEMANTICS_UNPROVEN`,
`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`, `SIC_EVIDENCE_INSUFFICIENT`), a strictly read-only
method, a zero provider/model budget, static-string limits and no-probe-shopping discipline —
definition: `docs/v0.3/V03E_G0_5_PRE_SESSION_INCARNATION_FINDING.md`, status **SIC = NOT RUN /
DEFINITION CANDIDATE**, awaiting independent definition review.  No OpenCode instance was
started, no HTTP or `/doc`/`/session` access occurred and no provider/model call was made;
G0.5 stays `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP`,
G1/G2 stay NOT RUN, adoption stays DISABLED and implementation remains NOT AUTHORIZED.

**The SIC definition received `REQUEST_CHANGES` (`REQUEST_CHANGES — V0.3-E G0.5-PRE / SIC
DEFINITION`; P0 = 0, P1 = 1, P2 = 3) and only its blocking findings were remediated**
(`docs/v0.3/V03E_G0_5_PRE_SESSION_INCARNATION_FINDING.md`; status **SIC = NOT RUN /
DEFINITION CANDIDATE / AWAITING INDEPENDENT RE-REVIEW**).  **P1 — positive semantic
authority:** "observable contract evidence" is now defined normatively as an explicitly
declared/documented contract semantic from an authoritative surface associated with the exact
installed target, whose declared behaviour may be checked for runtime consistency; runtime
observations/response examples may support only field existence, runtime exposure,
target/version consistency, response shape/type consistency and consistency with an
already-declared contract, and may **never** establish immutability, incarnation sensitivity,
session-incarnation scope, non-reuse, uniqueness, stability or provenance — one sample,
multiple samples, repeated stable observations and cross-session differences are **all**
insufficient without an authoritative declared semantic.  `SIC_PRESENT_AND_SEMANTICS_ESTABLISHED`
now requires **both** actual exposure through the authorized surface **and** authoritative
declared semantics for **all** qualifying properties; declaration-free metadata exposure yields
`SIC_METADATA_PRESENT_BUT_SEMANTICS_UNPROVEN` with no empirical promotion.  **P2-A —
`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`** is legal only on complete, successful coverage of the
precommitted surface (partial/unreachable/truncated/ambiguous/incompletely-parsed coverage →
`SIC_EVIDENCE_INSUFFICIENT`), and it is a surface-and-version-scoped non-claim that must never
generalize to "OpenCode has no session-incarnation metadata"; incomplete inspection may not be
hidden behind `HARNESS_INVALID`.  **P2-B — mode precommit:** the oracle must freeze exactly one
of Mode A (offline/static), Mode B (live local read-only) or Mode C (precommitted bounded
static→live two-stage, with the transition condition defined before execution); mid-run mode
switching and endpoint shopping invalidate the attempt, and the mandatory precommit set now
covers mode, surfaces, discovery/extraction rule, endpoint, request set/count, transition rule,
evaluation criteria, target binding, stop conditions and outcome mapping.  **P2-C — actual
destination/responder binding:** the actual HTTP client destination must be the exact frozen
concrete endpoint (numeric loopback address, port, address family, scheme, client destination
URI/base) bound to one deterministic listener (PID, canonical executable path, executable hash,
creation identity, exact version) with pre/post-request identity snapshots; any address-family,
listener, port-sharing, PID, proxy or responder ambiguity is **TARGET BINDING INVALID** and
stops before semantic inspection; a pre/post unchanged process elsewhere on the host is
insufficient; continuity mismatch makes the evidence invalid and may not be reported as a SIC
result; this reuses the accepted G0.4 revision-3 binding lessons without reopening G0.4.  The
non-blocking P3 items were deliberately not addressed, no status other than the SIC definition
candidate changed, and 0 runtime/test/config, provider/model, HTTP, `/doc`/`/session` or
OpenCode activity occurred.

**The first (Mode-A) SIC oracle-construction attempt was independently approved as a
freezability failure, and a narrow outcome-mapping amendment was applied.**  The independent
review issued *APPROVE V0.3-E SIC ORACLE FREEZABILITY FAILURE* (**P0 = 0, P1 = 0, P2 = 0**)
with classification **NARROW SIC DEFINITION VOCABULARY / OUTCOME-MAPPING DEFECT**: the accepted
four-outcome vocabulary could not truthfully map the state "candidate metadata present with
authoritative declared semantics that affirmatively establish non-qualification", because
outcome #2 was worded as semantics being *not sufficiently established* while the remaining
outcomes require zero candidates (NOT_EXPOSED) or insufficient coverage (EVIDENCE_INSUFFICIENT);
folding the two together or inventing a fifth outcome was forbidden.  **No SIC semantic attempt
occurred and no SIC oracle exists.**  The amendment (Option A) keeps exactly the four tokens and
clarifies `SIC_METADATA_PRESENT_BUT_SEMANTICS_UNPROVEN` normatively as *"candidate metadata
exists/is exposed, but no discovered candidate establishes the required qualifying SIC
semantics"*, covering exactly two sub-classes — **A. qualifying semantics unestablished**
(absent/insufficient/incomplete/ambiguous/unproven) and **B. authoritatively non-qualifying**
(established semantics affirmatively failing at least one required criterion) — with an explicit
token-interpretation note that the token does not require all candidate semantics to be unknown,
that the outcome stays strictly non-positive, that a positive result still requires one candidate
satisfying all of criteria A–G, that `NOT_EXPOSED` remains available only for complete coverage
plus zero candidates (discovery is never retroactively erased), that sufficient negative evidence
is never `EVIDENCE_INSUFFICIENT`, that `HARNESS_INVALID` stays outside the semantics, and that
per-candidate verdicts (`QUALIFIES` / `SEMANTICS_UNPROVEN` / `NON_QUALIFYING_METADATA`) are never
global tokens.  A frozen global mapping and an 11-row compatibility matrix now cover every
reachable state.  Mode A/B/C rules, the mode-precommit/no-mode-shopping rules, the
static-vs-live semantic-authority boundary, target binding, actual-responder, no-alternate-endpoint
and pre/post-continuity rules are all preserved unchanged, as is the positive-evidence threshold
(runtime observations still cannot establish semantics).  Status: `SIC = NOT RUN / DEFINITION
ACCEPTED / DEFINITION AMENDMENT CANDIDATE / ORACLE NOT YET CREATED / ORACLE NOT FREEZABLE —
OUTCOME MAPPING GAP`; the amendment requires independent review before any oracle is frozen.
The recorded scoped static-surface fact is only that the inspected installed static package
surface (OpenCode 1.18.11 npm distribution) contains no readable session schema, OpenAPI
artifact, generated client, bundled session documentation or declared session-metadata
semantics — it is **not** a SIC result and must never be read as "OpenCode has no incarnation
metadata".  G0.5/P6, G1/G2, adoption and implementation statuses are unchanged; 0
runtime/test/config, provider/model, HTTP, `/doc`/`/session` or OpenCode activity occurred, and
no oracle or result artifact was created.

**The SIC outcome-mapping amendment was independently approved, and a Mode-A pre-run oracle
candidate was constructed.**  The independent review issued *APPROVE V0.3-E SIC
OUTCOME-MAPPING DEFINITION AMENDMENT*, which makes commit `829d3c0` (SIC definition artifact
blob `5463ac19…`) the accepted SIC definition baseline and **resolves the prior `ORACLE NOT
FREEZABLE — OUTCOME MAPPING GAP` at definition level** — that blocker was a pre-oracle
definition defect (the four-outcome vocabulary could not truthfully map authoritatively
non-qualifying metadata), never an SIC semantic result.  With the amended definition in force, a
**MODE-A (offline/static only) pre-run oracle candidate** was written to
`docs/v0.3/V03E_G0_5_PRE_SIC_ORACLE.md`: **PRE-RUN ORACLE CANDIDATE — NOT ACCEPTED, NOT FROZEN,
NOT EXECUTED**, `SIC = NOT RUN / DEFINITION ACCEPTED / ORACLE CANDIDATE`.  The oracle freezes the
exact Mode-A authorized surface — the whole installed `opencode-ai` 1.18.11 package tree,
re-enumerated at construction: **8 files / 6 directories** in lexicographic order with sizes and
SHA-256 (`LICENSE`; `bin/opencode.exe` `578d7eb3…`; the two `node_modules/opencode-windows-x64*`
platform trees — `opencode-windows-x64/bin/opencode.exe` byte-identical to the declared bin, and
`opencode-windows-x64-baseline/bin/opencode.exe` `0e80c444…` — plus their `package.json`
manifests; and `postinstall.mjs`) — each artifact classified exactly once
(`PACKAGE_METADATA` / `INSTALLER_LOGIC` / `LICENSE_TEXT` / `OPAQUE_COMPILED_BINARY`, with compiled
binaries hashed and recorded but never supplying candidate fields or semantic authority).  It
also freezes: the complete-coverage rule (any missing, extra, drifted, unreadable, unparseable,
unclassified or ambiguous artifact prevents `NOT_EXPOSED` and maps to `EVIDENCE_INSUFFICIENT`
unless strictly inside the pre-assertion `HARNESS_INVALID` boundary); a deterministic,
enumerable candidate-extraction rule with a session-anchored discovery grammar, frozen alias
normalization and explicit forbidden sources (no arbitrary binary strings, no UUID-shaped bytes,
no frequencies, no name guesses detached from a session contract); discovery-before-validation
with a frozen candidate set (a `NON_QUALIFYING_METADATA` candidate is never retroactively
erased); the accepted per-candidate vocabulary (`QUALIFIES` / `SEMANTICS_UNPROVEN` /
`NON_QUALIFYING_METADATA`) with a complete per-candidate record schema; criteria A–G with the
strict incarnation-sensitivity, stability and session-scope thresholds; the Mode-A
semantic-authority rules; the amended four-outcome mapping; the mandatory surface-scoped
`NOT_EXPOSED` non-claim; **no live fallback** (the mode is fixed before execution and
`EVIDENCE_INSUFFICIENT` ends the run); exactly one semantic attempt with no rerun, no alternate
package, no second static surface and no manifest update after results; the artifact-drift stop
rule; and the future result-artifact schema with zero-activity budgets and privacy prohibitions.
A surface-scoped construction fact is recorded for transparency — the frozen manifest contains
zero `DECLARATIVE_CONTRACT_CANDIDATE` artifacts — explicitly **not** a SIC result and never to be
read as "OpenCode has no incarnation metadata".  No SIC semantic attempt occurred, no result
artifact exists and no execution is authorized; G0.5/P6 remains `NOT RUN / DEFINITION ACCEPTED /
ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP` with P6 `UNPROVEN / UNSATISFIED`, G1/G2 remain
`NOT RUN`, adoption stays **DISABLED** and implementation remains **NOT AUTHORIZED**; 0
runtime/test/config, provider/model, HTTP, `/doc`/`/session` or OpenCode activity occurred.

**The Mode-A SIC oracle was independently accepted and frozen, and its single authorized
execution produced a candidate result.**  The independent decision *APPROVE V0.3-E SIC MODE-A
PRE-RUN ORACLE* froze `docs/v0.3/V03E_G0_5_PRE_SIC_ORACLE.md` (baseline `e1fb6ac`, blob
`31d7ac50…`), and the separate one-shot external authorization permitted **exactly one** offline
/static semantic attempt.  Executed evidence (`docs/v0.3/V03E_G0_5_PRE_SIC_RESULT.md`, a
**CANDIDATE SIC RESULT** pending independent review): target identity verified (`opencode-ai`
1.18.11, package root unchanged, declared bin `./bin/opencode.exe`, declared-bin SHA-256
`578d7eb3…`); the frozen manifest was re-enumerated and matched **exactly** — 8 files / 6
directories, no missing artifact, no extra artifact inside the package root, no size/hash drift;
all 8 artifacts were classified exactly once (`PACKAGE_METADATA` ×3, `INSTALLER_LOGIC` ×1,
`LICENSE_TEXT` ×1, `OPAQUE_COMPILED_BINARY` ×3, the binaries hashed and identified only — never
executed, never scanned for semantic strings); the deterministic Phase-A extraction enumerated 32
declared `package.json` key paths (22 + 5 + 5) and found **zero** session-anchor key paths, and the
`postinstall.mjs` declaration scan found no explicitly declared schema/type/field-table contract
structure and no session-anchor declaration; complete authoritative coverage therefore held and
the frozen candidate set was **empty (0 candidates)**, so Phase B was not applicable and the frozen
mapping row C yielded the candidate outcome **`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`**.  The
mandatory surface-scoped non-claim is recorded prominently: the result applies only to the exact
successfully inspected installed static package surface and frozen artifacts, does **not**
establish that OpenCode globally has no session-incarnation metadata, does **not** establish that a
live/local API exposes no additional contract surface, does **not** establish P6 and does **not**
enable `adopt_completed_turn`.  Zero-live budget held throughout (0 OpenCode starts, 0 HTTP, 0
`/doc`, 0 `/session`, 0 runtime response reads, 0 provider/model/fake-provider calls, 0 prompt
submissions, 0 session mutations, 0 network, 0 process discovery, 0 port scanning, 0 endpoint
configuration); only local static reads and hashing were performed.  The attempt is consumed (1 of
1), **no rerun is authorized**, no Mode B/C was created or executed, the accepted SIC definition
and the frozen oracle were not modified, and the candidate result must not be treated as
authoritative or as P6 proof.  `G0.5 / P6` remains `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT
FREEZABLE / LOCAL REACHABILITY GAP` with P6 `UNPROVEN / UNSATISFIED`; `G1`/`G2` remain `NOT RUN`;
Case-C and v0.3-E implementation remain **NOT AUTHORIZED**; `adopt_completed_turn` remains
**DISABLED**; 0 runtime/test/config changes occurred.

**The Mode-A SIC result was independently approved and is now the authoritative Mode-A finding.**
The independent result review issued *APPROVE V0.3-E SIC MODE-A RESULT* (**P0 = 0, P1 = 0, P2 = 0**;
classification **VALID SEMANTIC RESULT**), binding the reviewed, immutable result artifact
`docs/v0.3/V03E_G0_5_PRE_SIC_RESULT.md` (blob `ce6c503d3bd62fa09c34d52bbd570e1a98dab403d1164b2e740fe6c476ecadc6`)
to the decision: the **authoritative Mode-A SIC finding is `SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`**,
established by the single authorized offline/static attempt under the accepted/frozen oracle
(`docs/v0.3/V03E_G0_5_PRE_SIC_ORACLE.md`, blob `31d7ac50…`, baseline `e1fb6ac`) — attempt consumed,
no rerun, no Mode B/C and no live activity.  Active status is converged to `SIC MODE-A = EXECUTED
ONCE / DEFINITION ACCEPTED / ORACLE ACCEPTED AND FROZEN / AUTHORITATIVE FINDING =
SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT / ATTEMPT CONSUMED / NO RERUN AUTHORIZED`, and separately
**broader session-incarnation capability = NOT ESTABLISHED BY MODE-A STATIC SURFACE**.  The strict
scope and non-claims are preserved everywhere: the finding applies **only** to the exact
successfully inspected OpenCode 1.18.11 installed static package surface and frozen target/package
artifacts; it does **not** establish that OpenCode globally has no session-incarnation metadata, does
**not** establish that a live/local API exposes no additional contract surface, does **not**
establish P6 (neither `P6 PASS` nor `P6 FAIL`), is **not** `G0.5 PASS` or `G0.5 FAIL`, and does
**not** enable `adopt_completed_turn`.  Stale status wording in `docs/v0.3/V03E_SPEC.md`, `README.md`,
`docs/v0.3/V03_PLAN.md` and `docs/BACKLOG.md` (which still described SIC as `NOT RUN / DEFINITION
CANDIDATE`) was converged in the same round; the accepted SIC definition (`5463ac19…`), the frozen
oracle (`31d7ac50…`), the reviewed result artifact (`ce6c503d…`), the substantive §25.1 block
(`d3244ee0…`) and the G0.4 artifacts were **not** modified.  `G0.5 / P6` remains `NOT RUN /
DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN /
UNSATISFIED` and is **NOT CLOSED**; `G1`/`G2` remain `NOT RUN`; Case-C and v0.3-E implementation
remain **NOT AUTHORIZED**; `adopt_completed_turn` remains **DISABLED**; no Mode B/C oracle was
created and no sequencing decision about them was made; 0 new SIC attempts, 0 new HTTP/`/doc`/
`/session`, 0 OpenCode activity, 0 provider/model/fake-provider calls and 0 network activity
occurred, and 0 runtime/test/config changes were made.

**A Mode-B (live local read-only) SIC pre-run oracle construction round produced no oracle, and
that freezability failure was independently approved.**  The independent review issued *APPROVE
V0.3-E SIC MODE-B ORACLE FREEZABILITY FAILURE* (**P0 = 0, P1 = 0, P2 = 0**) for the scoped
pre-oracle finding **`SIC MODE-B ORACLE NOT FREEZABLE — CONCRETE ENDPOINT NOT ESTABLISHED`**
under **current** accepted configuration/state — an independent review decision, not executor
self-approval, and **not** `MODE-B FAIL`, `SIC FAIL`, `P6 FAIL` or `G0.5 FAIL`.  The accepted
cause is the endpoint-authority path itself: the only supported current runtime endpoint
authority for DevRelay's local OpenCode bridge is `<root>/.devrelay/config.yaml` →
`opencode.base_url`, with the `OpenCodeConfig` empty-string model default as the absent/empty
fallback, and the current value is `base_url: ""` — so no exact scheme, numeric loopback
address, address family, port or base URI is established.  Resolution precision (recorded as
independently reviewed): environment supplies no `opencode.base_url`; the CLI has no endpoint
override; profiles are policy-only and provide no runtime OpenCode wiring; state and task
snapshots are reproducibility/runtime records, not endpoint-resolution authority; no user-level
DevRelay endpoint config participates; OpenCode `provider.*.options.baseURL` values are upstream
model-provider endpoints, not the local OpenCode service endpoint; runtime
logs/database/storage are not accepted endpoint authority; and the documented
`127.0.0.1:4096` value is example text only.  Default/template precision: the packaged
`profiles/default.yaml` contains **no** `opencode` section, the runtime empty fallback derives
from the `OpenCodeConfig` model default, and `WORKSPACE_CONFIG_TEMPLATE` contains `base_url: ""`
as workspace-generation material — the workspace template is **not** the packaged runtime
default.  Current Mode-B status is therefore `SIC MODE-B = NOT RUN / NO ORACLE / ORACLE NOT
FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING
PREREQUISITE BLOCKER`, with **no semantic Mode-B attempt**; the `/doc`-completeness question,
the exact Mode-B request set, live schema parsing, reference traversal, live candidate
extraction and the Mode-B semantic outcome are all **NOT REACHED / UNDECIDED**, and no partial
Mode-B oracle, Mode-B result, Mode C or endpoint-prerequisite artifact exists.  Mode A is
untouched: it stays completed and authoritative with `SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`,
strictly scoped to its exact successfully inspected OpenCode 1.18.11 static package surface.
A future Mode-B design needs a deterministic, precommitted mechanism binding endpoint →
listener → PID → canonical executable → executable hash → process creation identity where
available; the independent review classified the executor's stronger "DevRelay itself must
launch OpenCode" claim as **TOO STRONG / MECHANISM NOT YET DETERMINED**, so a future design may
choose controlled launch **or** another sound deterministic read-only binding mechanism,
subject to later independent review — **no choice was made in this round**.  The next dependency
was recorded at that point only as **MODE-B ENDPOINT / TARGET-BINDING PREREQUISITE = NOT YET
DEFINED / NOT AUTHORIZED** (its future definition had to settle endpoint-selection ownership,
authoritative endpoint source, numeric loopback address, address family, deterministic port
policy, pre-existing-vs-explicitly-launched target policy, deterministic target-binding mechanism
and the no-endpoint-shopping rule; none of that was designed in that round — a **definition
candidate** for the prerequisite was subsequently created in the next round, recorded below).
Hygiene record (independent
finding, **P3 only**): the prior construction report's "NO FILES MODIFIED" wording was
overbroad, because a round record was appended to the git-ignored/untracked `PROJECT_MEMORY.md`;
that file is outside tracked repository content, is ignored/untracked, does not participate in
DevRelay runtime/config, altered no endpoint/config/oracle evidence, and left the tracked
worktree clean — the precise wording going forward is "**no tracked repository/config/oracle/
source/test/document artifact modified**", and `PROJECT_MEMORY.md` was **not** edited to address
the wording issue.  `G0.5 / P6` remains `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE /
LOCAL REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED` and **NOT CLOSED**; `G1`/`G2` remain
`NOT RUN`; Case-C and v0.3-E implementation remain **NOT AUTHORIZED**; `adopt_completed_turn`
remains **DISABLED**; no endpoint was established, no port was selected, `opencode.base_url` and
`.devrelay` configuration were **not** modified, no listener was created, no port was scanned
and no listener was probed; 0 new SIC semantic attempts, 0 Mode-B executions,
0 HTTP/`/doc`/`/session`, 0 OpenCode starts/restarts, 0 endpoint selection, 0
provider/model/fake-provider calls, 0 external network, 0 G0.5 and 0 G1/G2 activity occurred,
and 0 runtime/test/dependency/version/config changes were made.

**A definition candidate now exists for the Mode-B endpoint / target-binding prerequisite (ETB).**
`docs/v0.3/V03E_G0_5_PRE_MODE_B_ENDPOINT_BINDING.md` defines the narrow **pre-oracle**
prerequisite that must be satisfied before a Mode-B (live local read-only) SIC oracle can be
constructed, with status **`ETB = DEFINITION CANDIDATE / NOT ACCEPTED / NOT EXECUTED / NOT
AUTHORIZED`**.  It establishes **no endpoint**, authorizes **no configuration change** and
authorizes **no OpenCode launch**.  ETB sits **outside P1–P9** as a pre-oracle prerequisite only:
it proves nothing — not P6, not G0.5, not SIC semantics, not session incarnation, not turn or
message provenance, not pending-handle semantics — and success enables exactly one thing, the
resumption of Mode-B SIC oracle **construction** (never Mode-B execution, G0.5, Case-C
implementation or adoption).  It freezes the endpoint authority as exactly
`<root>/.devrelay/config.yaml` → `opencode.base_url` (current value still `""`), with environment,
profile, CLI, state-snapshot, log, database, port/listener/process scan, provider upstream
`baseURL`, documentation example, implicit `localhost` and implicit default port all **forbidden**
as endpoint authority; endpoint-selection ownership is **external / owner-authorized** and the
executor must not invent the tuple (`127.0.0.1:4096` is **not** automatically selected); the
required form is `http` + a numeric loopback address + an **explicit** address family + an
**explicit** integer port (no actual value selected in this round).  The deterministic port policy
is frozen as a requirement with two admissible classes — **A: owner-supplied fixed port**
(available today) and **B: an independently accepted deterministic allocation policy** (admissible
only once such a policy exists and is accepted; not invented here) — while trying `4096` then
another port, first-free-port, range scanning, random ports, OS-assigned ephemeral ports without a
precommitted durable freeze, failure-driven choice and port retries are **forbidden**; an
unbindable precommitted port ends the attempt.  Exactly **two mutually exclusive modes** are
allowed — **MODE L (controlled launch)** and **MODE P (pre-existing target)** — with **no
selection made in this round**, a mandatory mode precommit **before any operational action**, **no
`L → P` / `P → L` fallback**, no mode shopping, and a mode change requiring new external
authorization.  **MODE L** requires the frozen 1.18.11 identity, the accepted executable hash, an
already externally authorized address/port, launch arguments that explicitly bind that exact
address/port, a PID obtained from the launch act itself, no scanning to choose the target, and
attempt termination on bind failure — but its **launch capability is UNESTABLISHED**: accepted
evidence records only a dedicated loopback `opencode serve` (v0.3-A artifacts) and freezes no
flags, so **Mode L is conditional on a later separately reviewed launch-capability determination**
and no CLI flags are guessed.  **MODE P** requires the endpoint tuple to be already explicit in the
authoritative configuration and permits only **endpoint-scoped owner verification** (endpoint
**discovery** is forbidden); a read-only OS mechanism is admissible only if it queries only the
already-frozen exact endpoint and deterministically returns its owning PID, with ambiguity failing
closed — and **no concrete primitive is asserted as authoritative**, that remaining a future
ETB-oracle requirement.  The definition freezes the target-binding chain (endpoint tuple → exact
listener → unique owning PID → canonical executable path → executable SHA-256 → exact OpenCode
version → process creation identity where available, no single element sufficient), the
pre/post-request continuity requirements (ETB itself performs **no** Mode-B HTTP), the
process-creation-identity property (PID alone never proves continuity; unavailability must be
classified explicitly as fail-closed rather than silently dropped), the version binding to
OpenCode 1.18.11 / `578d7eb3…`, the configuration boundary (setting `base_url` only after the
tuple is externally authorized and the mode precommitted — and configuration **never** equals
binding), the no-endpoint-shopping prohibitions, the fail-closed conditions (**never** to be
reinterpreted as SIC results), `ETB SATISFIED` (an unambiguous evidence package; **not** SIC/P6/G0.5
PASS) and `ETB UNSATISFIED` (a prerequisite/control result only: Mode-B oracle construction stays
blocked; it does **not** mean SIC, P6 or G0.5 failed), the status model, and the frozen sequencing
(**definition accepted → separate ETB oracle design → separate authorization → execution →
independent result review → only if ETB SATISFIED may Mode-B SIC oracle construction resume**; no
direct jump to Mode-B execution).  The definition aligns with the accepted G0.4 oracle's existing
endpoint-scoped binding definition (§8.1–§8.8) and reuses its semantics, while recording explicitly
that that prior art was **never executed** (G0.4 Case A `TARGET_IDENTITY_UNRESOLVED`, no configured
endpoint, 0 HTTP), so it is a reviewed definition rather than validated capability evidence; three
platform facts are carried forward as future requirements (exact launch syntax/address-port binding
capability; the concrete endpoint→PID primitive and its semantics; availability and semantics of
process creation identity) and none is invented.  Mode A remains completed and authoritative
(`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`, strictly scoped to its frozen static surface); Mode-B
status is unchanged (`NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT
ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`) and the Mode-B SIC
oracle remains **not freezable**; `G0.5 / P6` remains `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT
FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED` and **NOT CLOSED**;
`G1`/`G2` remain `NOT RUN`; Case-C and v0.3-E implementation remain **NOT AUTHORIZED**;
`adopt_completed_turn` remains **DISABLED**; ETB is **not** accepted and **not** executed, and no
operational authorization exists.  This round established no endpoint, selected no port or
address, changed no configuration (`.devrelay/config.yaml` untouched, `opencode.base_url` still
`""`), started no OpenCode, created no listener, performed no port/listener/process scan, issued
**0** HTTP, touched neither `/doc` nor `/session`, created no ETB execution oracle and no Mode-B
oracle, executed no SIC attempt, ran no G0.5/G1/G2, and made 0 runtime/test/dependency/version
changes.

**The ETB definition candidate was independently approved, so the Mode-B endpoint / target-binding
prerequisite is now an accepted prerequisite (this supersedes the candidate status recorded in the
preceding entry).**  The independent definition review issued *APPROVE V0.3-E MODE-B ETB
PREREQUISITE DEFINITION* (**P0 = 0, P1 = 0, P2 = 0**; three non-blocking P3s), binding the
immutable definition artifact `docs/v0.3/V03E_G0_5_PRE_MODE_B_ENDPOINT_BINDING.md` (blob
`99cc6dcee4ab1a3f0589c3e7d11308d089601ba07d16cc2d37a9fc32c777b3a0`, commit `f3f625f`) to that
decision — an independent review decision, not executor self-approval.  The authoritative ETB
status is therefore **`ETB = DEFINITION ACCEPTED / NOT EXECUTED`**, recorded separately from
**`ETB EXECUTION / ORACLE = NOT YET DEFINED / NOT AUTHORIZED`**; the two are deliberately **not**
merged into a new semantic outcome, and no `ETB SATISFIED`, `ETB UNSATISFIED` or `ETB EXECUTED`
result exists or is claimed.  The accepted definition remains a **pre-oracle prerequisite outside
P1–P9**: it proves none of P6, G0.5, SIC semantics, session incarnation, turn provenance, message
provenance or pending-handle semantics, and definition acceptance authorizes **nothing
operational**.  The accepted endpoint-authority model is unchanged — the future authoritative
endpoint source is exactly `<root>/.devrelay/config.yaml` → `opencode.base_url`, with no
alternative authority, and the current value is still `base_url: ""` — so **no endpoint is
established**, and definition acceptance must not be confused with endpoint establishment.
Endpoint selection remains **EXTERNAL / OWNER-AUTHORIZED** (or derived under a separately
independently accepted deterministic allocation policy); no address, address family, port or base
URI has been selected and `127.0.0.1:4096` remains example text only; the accepted port-policy
classes remain **A (owner-supplied fixed port)** and **B (independently accepted deterministic
allocation policy)**, and class B currently has **no concrete accepted policy** (none invented).
The accepted mode model defines exactly **two mutually exclusive** future modes — **MODE L
(controlled launch)** and **MODE P (pre-existing target)** — with **no mode selected**, no
third/hybrid mode, no `L → P` / `P → L` fallback, and definition acceptance authorizing **neither**
mode operationally.  The **Mode-L gap** is recorded as **UNESTABLISHED** (exact OpenCode server
command, exact address-binding flag semantics, exact port-binding flag semantics — no flag is
inferred or invented), so Mode L remains conditional and cannot be operationally precommitted
until separately established.  The **Mode-P gap** is recorded as **UNESTABLISHED** (the
endpoint-scoped owner-verification mechanism), with the accepted semantic boundary unchanged:
endpoint **discovery is FORBIDDEN**, while endpoint-scoped verification against an already-frozen
endpoint is **POTENTIALLY ADMISSIBLE** only if a future reviewed ETB oracle freezes a
deterministic concrete mechanism — and **no Windows command/API has been accepted**.  The accepted
target-binding chain is unchanged (authoritative endpoint tuple → exact listener → unique owning
PID → canonical executable path → executable SHA-256 → exact OpenCode version → process creation
identity where available), with **no single element proving binding**, `base_url` alone
insufficient and listener existence alone insufficient; the accepted process-instance rule is also
unchanged — PID alone is insufficient, a platform-supported process-instance discriminator
protecting against PID reuse is required, inability to obtain the required process-instance
evidence on the currently accepted Windows proof environment **fails closed**, and the concrete
primitive/semantics remain unresolved for the ETB execution oracle.  Definition semantics are
recorded **without being executed**: a future ETB execution under a separately frozen execution
oracle may yield `ETB SATISFIED` — which will mean only that the endpoint/target-binding
prerequisite is established sufficiently for Mode-B SIC oracle construction to resume, **not**
`SIC PASS`, `P6 PASS` or `G0.5 PASS` — or `ETB UNSATISFIED`, which means only that Mode-B SIC
oracle construction **remains blocked**.  The accepted unresolved-fact register is carried
forward as future ETB-oracle work with **nothing marked resolved**: **U1** exact OpenCode launch
syntax / explicit bind capability; **U2** exact Windows frozen-endpoint → owning-PID verification
primitive and semantics; **U3** process-instance/creation-identity primitive and semantics; **U4**
concrete deterministic port allocation policy if class B is used; **U5** actual ETB mode
selection — the independent review determined that **none** of U1–U5 blocks definition
acceptance.  Review P3s are recorded accurately as **non-blocking**: **P3-1** the construction
instruction "No amend" was violated by amending a seconds-old, unreviewed, unpushed intermediate
local commit — classified as a **bounded process-hygiene deviation only** (no
accepted/reviewed/shared history rewritten; final ancestry deterministic), explicitly **not
normalized**, with future rounds required to honor **NO AMEND**; **P3-2** the ETB definition
freezes the future endpoint form as HTTP-only, narrower than config validation's http/https
acceptance, with an explicit future review escape clause — **not** broadened now; **P3-3** Mode-P
endpoint-scoped verification still leaves bounded mechanism discretion, which a future ETB oracle
must concretely precommit — **not** solved now.  The accepted sequencing is unchanged and no stage
may be skipped: ETB definition **ACCEPTED** → next, separately, ETB execution/oracle design →
independent oracle review → separate execution authorization → ETB execution → independent ETB
result review → **only if ETB SATISFIED** may Mode-B SIC oracle construction resume.  The accepted
definition artifact is **immutable** and was **not** modified: its own at-construction header may
remain `DEFINITION CANDIDATE / NOT ACCEPTED`, because acceptance is represented through the
independent approval record and the active authoritative status surfaces, following the existing
immutable-artifact + approval-record pattern.  Mode-B status is unchanged — `SIC MODE-B = NOT RUN /
NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION /
TARGET-BINDING PREREQUISITE BLOCKER` — and Mode-B oracle construction has **not** resumed,
precisely because ETB has **not** been executed and is **not** SATISFIED.  Mode A remains
completed and authoritative (`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`, strictly scoped to its
accepted frozen static surface); `G0.5 / P6` remains `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT
FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED` and **NOT CLOSED**;
`G1`/`G2` remain `NOT RUN`; Case-C and v0.3-E implementation remain **NOT AUTHORIZED**;
`adopt_completed_turn` remains **DISABLED**.  This bookkeeping round established no endpoint,
selected no endpoint or port, changed no configuration (`.devrelay/config.yaml` untouched,
`opencode.base_url` still `""`), started no OpenCode, created no listener, designed no ETB
execution oracle, executed no ETB, created no Mode-B oracle, issued **0** HTTP, touched neither
`/doc` nor `/session`, executed no SIC attempt, ran no G0.5/G1/G2, and made 0
runtime/test/dependency/version changes.

**A capability-resolution candidate for the ETB design-support questions U1 / U2 / U3 was produced
(design support only).**  `docs/v0.3/V03E_G0_5_PRE_ETB_CAPABILITY_RESOLUTION.md` records a bounded,
read-only resolution attempt for the three platform facts carried by the accepted ETB definition —
**U1** exact OpenCode launch syntax / explicit bind capability, **U2** exact Windows
frozen-endpoint → owning-PID verification primitive and semantics, and **U3** process-instance /
creation-identity primitive and semantics — under a **closed probe set** of exactly eleven
authorized probes (the exact target executable's `--help` and `serve --help`, plus `Get-Command` /
`Get-Help` / `Get-CimClass` metadata for `Get-NetTCPConnection`, `Get-CimInstance`, `Get-Process`
and `Get-FileHash`), with no addition, substitution or variant after observing output.  It is
**design support for a future ETB execution oracle** — **not** an ETB execution oracle, **not** ETB
execution, **not** a proof-ladder gate — and it establishes no endpoint, selects no mode and
authorizes nothing.  Results: **U1 = `U1_NOT_ESTABLISHED`** (facts A–D established from the exact
1.18.11 binary's own help — the `opencode serve` subcommand "starts a headless opencode server", and
explicit `--hostname <string>` "hostname to listen on" / `--port <number>` "port to listen on"
options with defaults `"127.0.0.1"` and `0` — while fact E, exact-bind/implicit-substitution and
bind-failure semantics, and fact F, deterministic launcher-visible process identity, are
`SEMANTICS_UNPROVEN`, so Mode-L launch/bind semantics cannot yet be frozen without invention);
**U2 = `U2_NOT_ESTABLISHED`** (the `Get-NetTCPConnection` interface shape is documented —
`-LocalAddress` position 0/alias `IPAddress`, `-LocalPort <uint16[]>`, `-State` admitting the
documented value `Listen`, `-OwningProcess` as an input parameter, output type
`MSFT_NetTCPConnection` — but the captured help is explicitly **partial** because the module's help
files are not installed, so exact-match filtering semantics, result-set semantics and an owning-PID
output property are not documented: `SEMANTICS_UNPROVEN` for the three filter facts and
`EVIDENCE_INSUFFICIENT` for owning-PID output exposure); **U3 = `U3_NOT_ESTABLISHED`** (a PID-scoped
process query is **ESTABLISHED** — `Get-Process -Id <int[]>` alias `PID` is a documented parameter
set — and SHA-256 exact-path hashing is **ESTABLISHED** from `Get-FileHash`'s documented
`-Path`/`-LiteralPath` plus the algorithm enum containing `SHA256`, but executable-path exposure,
canonical-path semantics and the process-instance/PID-reuse discriminator are all
`EVIDENCE_INSUFFICIENT` because no property enumeration or property semantics were captured and the
authorized `Get-CimClass` rendering truncated the `Win32_Process` property list, the gap being
recorded rather than worked around).  Consequences: **`MODE_L_MECHANISM_NOT_YET_FREEZABLE`** and
**`MODE_P_MECHANISM_NOT_YET_FREEZABLE`** (neither is a mode selection), while **U4** and **U5**
remain **UNRESOLVED BY DESIGN / OWNER-ORACLE DECISION REMAINS**.  These are **evidence-surface
limitations, not platform-absence findings** and **not** ETB outcomes: no `ETB PASS`/`ETB FAIL`/
`ETB SATISFIED`/`ETB UNSATISFIED`/SIC/P6 result is created.  Recorded side effect: invoking the
exact target binary for the two help probes appended **+246 bytes** to
`C:\Users\1\.local\share\opencode\log\opencode.log` (15 650 374 → 15 650 620 bytes) inside the probe
window, with the caveat that the OpenCode state directory is shared with the user's own active
OpenCode usage so the growth is consistent with, but not exclusively attributable to, this round;
the log contents were not read.  No other side effect occurred: `.devrelay` untouched
(`opencode.base_url` still `""`), no repository runtime/test/config modification, no OpenCode server
started, no listener created, no port scan or listener/process enumeration, **0** HTTP, neither
`/doc` nor `/session` touched, no provider/model call and no external network access.  The current
authoritative ETB status is **unchanged** by this design-support round — `ETB = DEFINITION ACCEPTED
/ NOT EXECUTED` and `ETB EXECUTION / ORACLE = NOT YET DEFINED / NOT AUTHORIZED` — and Mode-B oracle
construction has still **not** resumed.

**The ETB U1/U2/U3 capability-resolution candidate was independently approved, so its findings are
now authoritative design-support status (this supersedes the candidate status recorded in the
preceding entry).**  The independent review issued *APPROVE V0.3-E ETB U1/U2/U3 CAPABILITY
RESOLUTION* (**P0 = 0, P1 = 0, P2 = 0**; four non-blocking P3s), binding the immutable capability
artifact `docs/v0.3/V03E_G0_5_PRE_ETB_CAPABILITY_RESOLUTION.md` (blob
`59e8ef575fa3ab854f65fee5e25621c51f74c8b76615d7d4d9fb1e071b4049ac`, commit `3151f87`) to that
decision — an independent review decision, not executor self-approval.  The authoritative capability
findings are **`U1 = U1_NOT_ESTABLISHED`**, **`U2 = U2_NOT_ESTABLISHED`**, **`U3 =
U3_NOT_ESTABLISHED`**, **`MODE L = MODE_L_MECHANISM_NOT_YET_FREEZABLE`** and **`MODE P =
MODE_P_MECHANISM_NOT_YET_FREEZABLE`**, with **`U4 = UNRESOLVED BY DESIGN / OWNER-ORACLE DECISION
REMAINS`** and **`U5 = UNRESOLVED BY DESIGN / OWNER-ORACLE DECISION REMAINS`**.  These are
**capability / design-support findings only**: they are **evidence-surface limitations, not
platform-absence findings**, and they are **not** `ETB UNSATISFIED`, `ETB FAIL`, `SIC FAIL`,
`P6 FAIL` or `G0.5 FAIL`.  Accepted U1 detail: A (serve subcommand exists), B (exact command form),
C (explicit hostname/address option) and D (explicit port option) are `ESTABLISHED`, while E
(exact-bind / bind-failure / no-substitution semantics) and F (deterministic launcher-visible
process identity) are `SEMANTICS_UNPROVEN` — therefore `U1_NOT_ESTABLISHED`; this does **not** mean
Mode L is impossible and does **not** mean OpenCode cannot bind an exact endpoint, only that the
required semantics remain unestablished.  Accepted U2 detail: the `Get-NetTCPConnection` local help
is **PARTIAL**; exact-local-address filter semantics, exact-local-port filter semantics,
listener-state restriction semantics and multiple-result detectability are `SEMANTICS_UNPROVEN`, and
owning-PID **output** exposure is `EVIDENCE_INSUFFICIENT` — therefore `U2_NOT_ESTABLISHED`, with the
distinction preserved that the existence of `-OwningProcess` as an **input** filter does **not**
establish an owning-PID **output** property, and no `MSFT_NetTCPConnection` property is inferred from
general knowledge.  Accepted U3 detail: PID-scoped query and SHA-256 exact-path hashing are
`ESTABLISHED`, while executable-path exposure, canonical-path semantics and the process-instance
discriminator are `EVIDENCE_INSUFFICIENT` — therefore `U3_NOT_ESTABLISHED`, with no invented
`ExecutablePath`, canonicalization or `CreationDate`/`StartTime` semantics.  Reviewed
next-information ordering (recorded as **current design-support status, not authorization**):
**FIRST** — U2: authoritative parameter semantics for `-LocalAddress`, `-LocalPort` and `-State`,
plus authoritative `MSFT_NetTCPConnection` output-property semantics, especially an owning-PID
output property; **SECOND** — U3: a documented executable-path property with path-comparison /
canonicalization semantics, plus a documented process-instance / creation-identity property whose
semantics are strong enough to discriminate PID reuse; **THIRD** — U1: exact-bind, bind-failure and
no-substitution semantics for `--hostname`/`--port` (including the meaning of `--port 0`), plus a
deterministic launcher-visible process-identity mechanism.  **The repository does not yet contain
enough information to construct a sound final ETB execution oracle; additional bounded capability
evidence is required first** — and no follow-up capability round is designed or authorized here.
Review P3s are recorded accurately as **non-blocking standing observations, none presented as
resolved**: **P3-1** the intended PowerShell execution helper failed (`node.exe ENOENT`) and the same
frozen W1–W9 commands were executed through `powershell.exe -NoProfile -NonInteractive` — a
non-material process/harness deviation; **P3-2** the OpenCode help invocations produced the disclosed
**+246-byte** growth in `C:\Users\1\.local\share\opencode\log\opencode.log` during the probe window —
a non-blocking local metadata/hygiene side effect on which no semantic evidence depended; **P3-3**
the "no untracked leftovers" wording was technically overbroad because the ignored/untracked
`PROJECT_MEMORY.md` exists — no runtime/config/evidence impact; **P3-4** previously carried project
P3s were not re-promoted.  Raw-capture treatment: the review independently corroborated the raw
captures under `C:\Users\1\AppData\Local\Temp\etb-cap.PC89OZ` during review, but that **ephemeral
path is not an authoritative long-term repository source**; the accepted repository artifact carries
the durable summarized evidence and hash record, and future evidence rounds should preserve required
raw/surrogate evidence in a **durable tracked form** when authorized — user logs and private data
must never be copied into the repository.  ETB status is unchanged by this acceptance: `ETB =
DEFINITION ACCEPTED / NOT EXECUTED` and `ETB EXECUTION / ORACLE = NOT YET DEFINED / NOT AUTHORIZED`;
capability-finding acceptance creates **no** ETB execution oracle, **no** ETB execution
authorization, **no** `ETB SATISFIED` and **no** `ETB UNSATISFIED`.  Endpoint and mode state is
unchanged: `opencode.base_url` is still `""`, no endpoint is established, no address, address
family, port or base URI is selected, no port policy is instantiated, and neither Mode L nor Mode P
is selected.  Mode A remains completed and authoritative (`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`,
strictly scoped to the accepted static surface); Mode-B status is unchanged (`NOT RUN / NO ORACLE /
ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING
PREREQUISITE BLOCKER`) and Mode-B oracle construction has **not** resumed; `G0.5 / P6` remains
`NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN /
UNSATISFIED` and **NOT CLOSED**; `G1`/`G2` remain `NOT RUN`; Case-C and v0.3-E implementation remain
**NOT AUTHORIZED**; `adopt_completed_turn` remains **DISABLED**.  This bookkeeping round ran no
capability probe, no web lookup, no PowerShell help install and no OpenCode help invocation;
established no endpoint; selected no endpoint, port, address family or mode; changed no
configuration; started no OpenCode server; created no listener; performed no process/listener/port
query; did no ETB oracle work and no ETB execution; issued **0** HTTP; touched neither `/doc` nor
`/session`; executed no SIC attempt; ran no G0.5/G1/G2; and made 0 runtime/test/dependency/version
changes.

**A round-2 candidate capability finding resolved the ETB U2 and U3 semantic gaps (design support
only; not accepted).**  `docs/v0.3/V03E_G0_5_PRE_ETB_U2_U3_AUTHORITY_RESOLUTION.md` records a bounded
resolution of **U2** (frozen-endpoint → unique owning PID) and **U3** (known PID → executable
identity + process-instance identity + canonical executable path) using a **closed authoritative
source set** — exactly **nine** approved Microsoft Learn pages (D1–D9, all HTTP 200, bodies hashed,
no page body committed, no search-engine result or third-party source used as evidence) — plus
exactly **four** local metadata/schema probes (S1–S4) that retrieved **no** instance and performed
**no** live TCP, listener, port or process query.  Durable evidence is tracked under
`docs/v0.3/evidence/etb-u2-u3-authoritative-semantics/` (14 evidence files + `MANIFEST.sha256`, all
hashes verified).  Candidate results: **`U2 = U2_ESTABLISHED`** — the exact-local-address and
exact-local-port filter semantics are documented (both `Supports wildcards: False`), `-State`
restricts to the states specified with `Listen` among the accepted values (and `State` is a read-only
property whose `Listen` value means waiting for a connection request), the installed command metadata
binds `OutputType` to `…CimInstance#ROOT/StandardCimv2/MSFT_NetTCPConnection` (corroborated by the
class documentation's `Root\StandardCimv2` namespace and by local class metadata), `OwningProcess` is
documented as a **read-only** uint32 property holding "the PID of the owning process of the TCP
connection" (kept distinct from the `-OwningProcess` **input** filter), and `@(...)`+`.Count`
deterministically distinguishes 0/1/N results — so the endpoint-scoped verification
`-LocalAddress <frozen> -LocalPort <frozen> -State Listen` with `@(...).Count == 1` and a read of
`OwningProcess` is freezable, with wildcard-bound or multi-match cases failing closed; and
**`U3 = U3_ESTABLISHED`** — the WQL/CQL `-Filter` contract plus the documented `=` **Equal** operator
(with `LIKE` as the separate wildcard form) establish the exact PID-scoped predicate,
`ProcessId`/`ExecutablePath`/`CreationDate` are all present locally as read-only properties,
`ExecutablePath` is documented as "Path to the executable file of the process", `CreationDate` is
documented (qualifier `Fixed`) as "Date the process begins executing" so a reused PID necessarily
belongs to a newly started instance with a different creation date, and the canonical/final-path
capability is established by `GetFinalPathNameByHandleW` (`FILE_NAME_NORMALIZED` = "Return the
normalized drive name", "A final path is the path that is returned when a path is fully resolved")
with a read-only `GENERIC_READ` + `OPEN_EXISTING` handle (no creation, no truncation) invoked through
`Add-Type` P/Invoke (present locally), SHA-256 hashing being already accepted.  Consequently the
candidate **`MODE P = MODE_P_MECHANISM_FREEZABLE`** — mechanism semantics are now sufficient for later
ETB oracle design — while **U1 = `U1_NOT_ESTABLISHED`** and **MODE L =
`MODE_L_MECHANISM_NOT_YET_FREEZABLE`** are **unchanged** (no OpenCode probe, no server launch, no
contradicting evidence), and **U4/U5 remain `UNRESOLVED BY DESIGN / OWNER-ORACLE DECISION REMAINS`**
(Mode-P mechanism freezability is **not** mode selection).  Recorded fail-closed caveats (design
requirements, not gaps): the `SeDebugPrivilege` qualifier on `ExecutablePath`; `ERROR_ACCESS_DENIED`
on component-access failure under normalized resolution; the `\\?\` DOS-prefix form requiring the
**identical** canonicalization on both sides; and `ExecutablePath` never being treated as canonical
without that route.  No endpoint was established, no port or address selected, no mode selected, no
configuration changed (`opencode.base_url` still `""`), no OpenCode started, no listener created, no
HTTP issued, no `/doc` or `/session` access, no provider/model call, and no ETB execution, ETB oracle
or Mode-B oracle work occurred; this round is a **candidate only until independent review**, and the
current authoritative state remains `ETB = DEFINITION ACCEPTED / NOT EXECUTED` with `ETB EXECUTION /
ORACLE = NOT YET DEFINED / NOT AUTHORIZED`.

**The round-2 ETB U2/U3 authoritative-semantics candidate was independently approved, so its results
are now authoritative capability status (this supersedes the U2/U3 and Mode-P results recorded in the
preceding capability entries).**  The independent review issued *APPROVE V0.3-E ETB U2/U3
AUTHORITATIVE SEMANTICS ROUND-2* (**P0 = 0, P1 = 0, P2 = 0**; five non-blocking P3s), binding the
immutable Round-2 artifact `docs/v0.3/V03E_G0_5_PRE_ETB_U2_U3_AUTHORITY_RESOLUTION.md` (blob
`49b22a88a593ce9ce59e7da6ae5221d8300d4963cca5b9fdc2dc8c2b47a91453`, commit `dcf899d`) together with
its tracked evidence manifest `docs/v0.3/evidence/etb-u2-u3-authoritative-semantics/MANIFEST.sha256`
(blob `579e21e6596e552a1ee453a0a3c08489f4911ff51a1f922dae5bfa71c770a15a`; 14 evidence files,
manifest re-verified **14 OK / 0 mismatch** against the committed blobs) to that decision — an
independent review decision, not executor self-approval.  The authoritative capability state is
therefore **`U1 = U1_NOT_ESTABLISHED`** (unchanged), **`U2 = U2_ESTABLISHED`**, **`U3 =
U3_ESTABLISHED`**, **`MODE L = MODE_L_MECHANISM_NOT_YET_FREEZABLE`** (unchanged) and **`MODE P =
MODE_P_MECHANISM_FREEZABLE`**, with **`U4 = UNRESOLVED BY DESIGN / OWNER-ORACLE DECISION REMAINS`**
and **`U5 = UNRESOLVED BY DESIGN / OWNER-ORACLE DECISION REMAINS`**; this supersedes the previous
capability state **only** for U2/U3 and the Mode-P mechanism-freezability consequence, and U1/Mode-L
are **not** changed (Mode L is not claimed impossible).  Accepted U2 detail: exact `LocalAddress`
filtering, exact `LocalPort` filtering, `State`/`Listen` filtering, installed output-class binding to
`ROOT/StandardCimv2/MSFT_NetTCPConnection`, `OwningProcess` **output-property** semantics, and 0/1/N
cardinality normalization with the `Count == 1` uniqueness rule are all ESTABLISHED — with the
mechanism boundary preserved: the future query is **endpoint-scoped verification against one
already-frozen exact endpoint**, **not endpoint discovery**.  Accepted U3 detail: the PID-scoped
`Win32_Process` equality filter, the local `ProcessId` property, the local `ExecutablePath` property,
`ExecutablePath`'s documented meaning, the local `CreationDate` property, `CreationDate`'s
process-start semantics, the process-instance-discriminator use at the accepted ETB capability level,
the `GetFinalPathNameByHandleW` final-path capability, the `CreateFileW` existing-file handle
capability, the `Add-Type`/P-Invoke local invocation route and SHA-256 exact-path hashing are all
ESTABLISHED.  Accepted canonicalization chain (freezable semantics; **no implementation code
written** and the exact implementation rules **not** claimed frozen): raw `Win32_Process.ExecutablePath`
→ `CreateFileW` on the existing executable under a future fail-closed deterministic share/access rule
→ `GetFinalPathNameByHandleW` with `FILE_NAME_NORMALIZED` + `VOLUME_NAME_DOS` → the identical
final-path procedure applied to the accepted target executable → deterministic comparison → SHA-256
verification.  Mode-P consequence: `MODE_P_MECHANISM_FREEZABLE` holds because `U2_ESTABLISHED` **and**
`U3_ESTABLISHED` with no contradiction to the accepted ETB definition — and
**`MODE_P_MECHANISM_FREEZABLE` is NOT Mode-P selection**; it establishes no endpoint, port, address
family or base URI, no ETB oracle, no ETB execution authorization and no `ETB SATISFIED`.  Review P3s
are recorded accurately as **non-blocking standing observations, none presented as resolved or
blocking**: **P3-1** D1 was delivered in the `windowsserver2025-ps` view after the requested
PowerShell-5.1 fallback and was locally bound through S1/S2 — classified non-material; **P3-2**
`CreateFileW` `dwShareMode` is not yet precommitted — a deterministic future-oracle implementation
rule, not a capability semantic gap; **P3-3** `CreationDate` carries a residual precision/collision
caveat — no mathematical global uniqueness is claimed, and the future ETB oracle must explicitly
record the residual and use exact pre/post equality with fail-closed treatment of any mismatch or
ambiguity; **P3-4** the evidence `.txt`/`.json`/`.sha256` paths may materialize CRLF on a future
checkout — committed Git blobs are authoritative and manifest verification must be against committed
blobs; **P3-5** web search, where used, only located already-precommitted URLs and supplied no
semantic evidence; the standing `PROJECT_MEMORY` wording P3 is preserved.  Still **NOT FROZEN**
(future ETB execution-oracle design items; they do **not** invalidate U2/U3 capability establishment):
the exact canonicalization comparison rule, `\\?\` prefix handling, case normalization/comparison,
slash normalization, drive-letter normalization, `CreateFileW` `dwShareMode`,
`SeDebugPrivilege`/access-denied fail-closed behaviour, the pre/post target snapshot exact field set,
the pre/post equality/comparison rule, and the exact `Count == 1` expression and failure handling.
The narrow next stage is recorded as **OWNER / ORACLE-PARAMETER DECISION = NOT YET EXECUTED** (purpose:
U5 mode selection and, **only if Mode P is selected**, U4 endpoint parameter selection); recording it
does **not** authorize it, and no such decision was made in this round.  Preserved unchanged: `ETB =
DEFINITION ACCEPTED / NOT EXECUTED`; `ETB EXECUTION / ORACLE = NOT YET DEFINED / NOT AUTHORIZED` (the
ETB oracle does not yet exist and ETB execution is not authorized even though Mode-P mechanism
semantics are now freezable); `opencode.base_url` is still `""` with no endpoint established, no
address, address family, port or base URI selected and no configuration change; Mode A remains
completed and authoritative (`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`, strictly scoped to its accepted
static surface); Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT
ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER` with oracle construction
**not** resumed; `G0.5 / P6` remains `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL
REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED` and **NOT CLOSED**; `G1`/`G2` remain `NOT RUN`;
Case-C and v0.3-E implementation remain **NOT AUTHORIZED**; `adopt_completed_turn` remains
**DISABLED**.  This bookkeeping round performed **0** web retrievals, **0** schema probes, **0** live
TCP queries, **0** live process queries, **0** port/listener/process enumeration, **0** endpoint
establishments or selections, **0** port selections, **0** mode selections, **0** configuration
changes, **0** OpenCode starts, **0** listener work, **0** ETB oracle design, **0** ETB executions,
**0** OpenCode HTTP, **0** `/doc`, **0** `/session`, **0** SIC attempts, **0** Mode-B oracle work,
**0** provider/model calls, **0** network, **0** G0.5 and **0** G1/G2 activity, and **0**
runtime/test/dependency/version changes.  The accepted Round-2 artifact and every file under its
evidence directory were **not** modified (artifact blob `49b22a88…`, manifest blob `579e21e6…`,
manifest re-verified 14 OK / 0 mismatch); the artifact retains its `ROUND-2 CANDIDATE FINDING / NOT
ACCEPTED` header because acceptance is carried by the independent review record and the active
authoritative status surfaces.

**The human owner has explicitly decided the ETB mode and endpoint parameters; a candidate repository
record of that decision now exists (not yet independently accepted).**
`docs/v0.3/V03E_G0_5_PRE_ETB_OWNER_ORACLE_PARAMETERS.md` records the owner's decision as **frozen
external input** for a future ETB execution-oracle design: **U5 = MODE P — PRE-EXISTING TARGET
(selected by the owner; MODE L = NOT SELECTED)**, **U4 = CLASS A — OWNER-SUPPLIED FIXED ENDPOINT**, and
the indivisible endpoint tuple **scheme `http` / address family IPv4 / numeric loopback address
`127.0.0.1` / port `4096` / base URI `http://127.0.0.1:4096`**, with **fallback = NONE**.  The record is
marked **CANDIDATE RECORD / HUMAN OWNER DECISION / NOT YET INDEPENDENTLY ACCEPTED**, so the active status
is `OWNER / ORACLE-PARAMETER DECISION = CANDIDATE RECORD / OWNER INPUT FROZEN / INDEPENDENT FIDELITY
REVIEW PENDING`.  Acceptance-critical provenance: the **executor did not choose** Mode P, IPv4,
`127.0.0.1`, `4096` or the base URI — the human owner supplied them and the executor must not
reinterpret, replace or extend them; the historical documentation example `127.0.0.1:4096` is **not**
the source of authority.  The record freezes the no-fallback prohibitions (IPv4 → IPv6;
`127.0.0.1` → `localhost`; `127.0.0.1` → `::1`; `4096` → another port, first-free port or ephemeral
port; Mode P → Mode L; alternate OpenCode binary or installation; endpoints discovered from logs,
listener scans or process scans; and retry on another endpoint after failure), requires that a later
ETB execution verify **the exact frozen endpoint only with no endpoint discovery**, and states the
fail-closed consequence: no listener at `127.0.0.1:4096`, more than one matching listener, no owning
PID, ambiguous owner, wrong executable, wrong hash, wrong OpenCode version, process-instance mismatch,
or unavailable required identity evidence ⇒ **ETB must not be considered SATISFIED**, with **no**
fallback endpoint or mode attempted.  **Configuration is deliberately untouched:** the owner-authorized
endpoint is `http://127.0.0.1:4096` while `.devrelay/config.yaml` → `opencode.base_url` **remains `""`**
— the owner parameter decision exists, but the endpoint is **not** yet established in configuration; a
future separately authorized action may set `base_url` to the frozen tuple, and this round does **not**
authorize that mutation.  Preserved unchanged: `U1 = U1_NOT_ESTABLISHED` and `MODE L =
MODE_L_MECHANISM_NOT_YET_FREEZABLE` (Mode L is neither invalid nor impossible, and no automatic
Mode P → Mode L fallback exists); `U2 = U2_ESTABLISHED`, `U3 = U3_ESTABLISHED` and `MODE P =
MODE_P_MECHANISM_FREEZABLE` (not reopened, and the U2/U3 mechanism was **not** executed); the target
identity (OpenCode / `opencode-ai` 1.18.11,
`C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe`, SHA-256 `578d7eb3…`) with no
alternate binary, installation or retargeting; `ETB = DEFINITION ACCEPTED / NOT EXECUTED` and
`ETB EXECUTION / ORACLE = NOT YET DEFINED / NOT AUTHORIZED`, with no `ETB SATISFIED`,
`ETB UNSATISFIED` or `ETB EXECUTED` created; Mode-B `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE /
CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`
with oracle construction not resumed; `G0.5 / P6` unchanged with `P6 = UNPROVEN / UNSATISFIED` and G0.5
**NOT CLOSED**; Case-C and v0.3-E implementation `NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`;
`adopt_completed_turn` **DISABLED**.  The future-oracle rules left explicitly open (exact
`Get-NetTCPConnection` expression; exact `Count == 1` enforcement and failure handling; exact
`Win32_Process` PID query expression; pre/post target snapshot field sets and equality rules;
`CreationDate` precision-residual handling; `CreateFileW` `dwShareMode`; `ExecutablePath` access-failure
handling; `SeDebugPrivilege` failure handling; `GetFinalPathNameByHandleW` access-failure handling;
`\\?\` prefix handling; case comparison, slash normalization and drive-letter normalization rules;
target-executable canonicalization procedure details; exact evidence serialization; and any
`HARNESS_INVALID` vs `ETB UNSATISFIED` boundary) were **not** solved in this round.  Sequencing is
unchanged and no stage may be skipped: owner decision → independent review and acceptance → ETB
execution-oracle design → independent oracle review → separate execution/configuration authorization →
configuration establishment as authorized → ETB execution → independent ETB result review → only if
ETB SATISFIED may Mode-B SIC oracle construction resume.  This round performed **0** web retrievals,
**0** schema probes, **0** live TCP queries, **0** live process queries, **0** port/listener/process
enumeration, **0** endpoint establishment or probing, **0** configuration mutations, **0** OpenCode
starts/restarts, **0** listener work, **0** HTTP, **0** `/doc`, **0** `/session`, **0** ETB oracle
design, **0** ETB executions, **0** SIC attempts, **0** Mode-B oracle work, **0** provider/model calls,
**0** network, **0** G0.5 and **0** G1/G2 activity, and **0** runtime/test/dependency/version changes;
`opencode.base_url` remains `""`.

**The human owner's ETB mode / endpoint decision record was independently fidelity-reviewed and is
now authoritative accepted status.**  The independent fidelity review issued *APPROVE V0.3-E ETB
OWNER / ORACLE-PARAMETER DECISION RECORD* (**P0 = 0, P1 = 0, P2 = 0**; two non-blocking P3s), binding
the immutable decision record `docs/v0.3/V03E_G0_5_PRE_ETB_OWNER_ORACLE_PARAMETERS.md` (blob
`152311341b8bc8cfb93964f3709a6922a62d914c8a297dea1e3634940bb34cbe`, commit `bab4979`) to that
decision — an independent review decision, not executor self-approval — so the **HUMAN OWNER DECISION
IS ACCEPTED AS FAITHFULLY RECORDED**.  Authoritative owner-decision state: **U5 = MODE P — PRE-EXISTING
TARGET, SELECTED BY HUMAN OWNER** with **MODE L = NOT SELECTED** (Mode L is neither invalid nor
impossible, U1 is **not** resolved, and no automatic Mode P → Mode L fallback exists); **U4 = CLASS A —
OWNER-SUPPLIED FIXED ENDPOINT** with the indivisible tuple **`http` / IPv4 / `127.0.0.1` / `4096` /
`http://127.0.0.1:4096`** and **fallback = NONE**; the **executor selected none of these values**, and
the historical example `127.0.0.1:4096` is **not** the source of authority — the source of authority is
the human owner's explicit decision.  The authoritative no-fallback prohibitions remain frozen
(IPv4 → IPv6; `127.0.0.1` → `localhost`; `127.0.0.1` → `::1`; `4096` → any other port, first-free or
ephemeral; Mode P → Mode L; alternate OpenCode binary or installation; endpoint discovery from logs,
listeners or processes; retry against an alternate endpoint), and a later inability to satisfy the
frozen tuple must **fail closed**.  **Owner authority vs configuration (acceptance-critical):** the
**owner-authorized endpoint** is `http://127.0.0.1:4096`, but the **current configured endpoint is
NONE** — `.devrelay/config.yaml` → `opencode.base_url` **remains `""`** and is unchanged, so **owner
endpoint parameters are authoritative while the endpoint is NOT yet established in configuration**; no
configuration mutation is authorized by this bookkeeping round.  **Pre-existing target:** Mode P means
the target must be pre-existing for the later ETB attempt; this status does **not** assert that OpenCode
is running, that a listener exists, that `127.0.0.1:4096` is reachable, or that the endpoint currently
satisfies ETB, and the future ETB execution attempt must verify **exactly the frozen endpoint** with
**no discovery**.  **Frozen external inputs** for future ETB-oracle design (the oracle MUST consume them
and MUST NOT choose, derive, negotiate, normalize into substitutes or replace them): mode = MODE P;
endpoint policy = CLASS A OWNER-SUPPLIED FIXED ENDPOINT; scheme = `http`; address family = IPv4; host =
`127.0.0.1`; port = `4096`; base URI = `http://127.0.0.1:4096`; fallback = NONE.  **Target identity
preserved:** OpenCode / `opencode-ai` 1.18.11,
`C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe`, SHA-256 `578d7eb3…` — no
alternate binary, no alternate installation, no retargeting.  **Mode-P capability state preserved and
kept distinct:** `U2 = U2_ESTABLISHED`, `U3 = U3_ESTABLISHED` and `MODE P =
MODE_P_MECHANISM_FREEZABLE` remain accepted, and `MODE P = SELECTED BY HUMAN OWNER` is recorded
separately — mechanism freezability ≠ mode selection ≠ oracle implementation ≠ ETB execution.  **Still
NOT FROZEN** (ETB execution-oracle design items; not solved now): the exact `Get-NetTCPConnection`
expression; exact `Count == 1` enforcement/failure handling; exact `Win32_Process` PID query expression;
pre-request and post-request target snapshot exact field sets; pre/post equality and comparison rules;
`CreationDate` precision-residual handling; `CreateFileW` `dwShareMode`; `ExecutablePath` access-failure
handling; `SeDebugPrivilege` failure handling; `GetFinalPathNameByHandleW` access-failure handling;
`\\?\` prefix handling; case comparison, slash normalization and drive-letter normalization rules;
target-executable canonicalization details; exact evidence serialization; and the `HARNESS_INVALID` vs
`ETB UNSATISFIED` boundary if needed.  **Configuration authorization boundary:** a **future separately
authorized** stage may configure `opencode.base_url = http://127.0.0.1:4096` because the tuple is
owner-authorized and Mode P is owner-selected — this round **does not authorize and does not perform**
that mutation.  **Sequencing (no stage may be skipped):** OWNER / ORACLE-PARAMETER DECISION → fidelity
reviewed → acceptance bookkept and independently confirmed → **ETB EXECUTION-ORACLE DESIGN** →
independent oracle review → separate execution/configuration authorization → configuration
establishment as authorized → ETB execution → independent ETB-result review → **only if ETB SATISFIED**
may Mode-B SIC oracle construction resume.  **Preserved unchanged:** `ETB = DEFINITION ACCEPTED / NOT
EXECUTED` and `ETB EXECUTION / ORACLE = NOT YET DEFINED / NOT AUTHORIZED` (no `ETB SATISFIED`,
`ETB UNSATISFIED` or `ETB EXECUTED` created); `U1 = U1_NOT_ESTABLISHED` and `MODE L =
MODE_L_MECHANISM_NOT_YET_FREEZABLE`; Mode-B = `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE
ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER` with oracle
construction **not** resumed (the owner-authorized tuple does **not** mean the endpoint is configured or
established); `G0.5 / P6 = NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY
GAP` with `P6 = UNPROVEN / UNSATISFIED` and G0.5 **NOT CLOSED**; Case-C and v0.3-E implementation
`NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`; `adopt_completed_turn` **DISABLED**.  Review P3s recorded as
**non-blocking** (neither presented as blocking nor as resolved): **P3-1** the recurring phrase "no
untracked leftovers" is technically overbroad because `PROJECT_MEMORY.md` remains ignored/untracked —
preferred wording going forward, adopted in this entry, is "**tracked worktree clean; ignored/untracked
`PROJECT_MEMORY.md` persists**"; **P3-2** previously carried project P3s were not re-promoted.  This
bookkeeping round performed **0** web retrievals, **0** schema probes, **0** live TCP queries, **0** live
process queries, **0** port/listener/process enumeration, **0** endpoint establishment or probing,
**0** configuration mutations, **0** OpenCode starts/restarts, **0** listener work, **0** HTTP, **0**
`/doc`, **0** `/session`, **0** ETB oracle design, **0** ETB executions, **0** SIC attempts, **0**
Mode-B oracle work, **0** provider/model calls, **0** network, **0** G0.5 and **0** G1/G2 activity, and
**0** runtime/test/dependency/version changes; `opencode.base_url` remains `""`, the tracked worktree is
clean, and the ignored/untracked `PROJECT_MEMORY.md` persists.

**A candidate ETB execution oracle for Mode P / Class-A fixed endpoint now exists (design only; not
accepted, not frozen, not executed).**  `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md` freezes every
semantic rule a later authorized ETB attempt must apply — so that the executor chooses no semantic rule
at runtime — for the owner-selected **MODE P — PRE-EXISTING TARGET** with the **CLASS A
OWNER-SUPPLIED FIXED ENDPOINT** `http` / IPv4 / `127.0.0.1` / `4096` / `http://127.0.0.1:4096` and
**fallback = NONE**, against OpenCode / `opencode-ai` **1.18.11**
(`C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe`, SHA-256 `578d7eb3…`).
The artifact is marked **ETB EXECUTION ORACLE / MODE P / CLASS A OWNER-SUPPLIED FIXED ENDPOINT / ORACLE
CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EXECUTED / DOES NOT MODIFY CONFIGURATION / DOES NOT START
OPENCODE / DOES NOT PERFORM HTTP / DOES NOT AUTHORIZE ETB EXECUTION**, so the recorded status is
`ETB = DEFINITION ACCEPTED / NOT EXECUTED` with `ETB EXECUTION / ORACLE = CANDIDATE / NOT ACCEPTED / NOT
AUTHORIZED / NOT EXECUTED`.  Static design findings and frozen rules (no runtime choice remains): the
**production config-read mechanism is the existing `src/devrelay/config.py` function
`load_wiring_config(root_or_path) -> WiringConfig`**, consumed read-only and deterministically through
`WiringConfig.opencode.base_url` (the validator-normalized field, trailing `/` stripped) with the frozen
invocation `PYTHONPATH=<repo>/src python -c "…load_wiring_config(sys.argv[1]).opencode.base_url" "<repo>"`,
required to equal `http://127.0.0.1:4096` exactly (`-ceq`), with precommitted failure mapping (loader
module import failure → `HARNESS_INVALID`; `ConfigError`/absent file/`""`/mismatch → `ETB_UNSATISFIED`);
the **exact listener query** `@(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 4096 -State
Listen)` with `Count -eq 1` plus `LocalAddress -ceq '127.0.0.1'`, `LocalPort -eq 4096`, `State -eq
'Listen'` and a present positive `OwningProcess`; the **exact PID-scoped process query**
`@(Get-CimInstance -Namespace root/cimv2 -ClassName Win32_Process -Filter "ProcessId = <pid>")` with
`Count -eq 1` and required `ProcessId` / `ExecutablePath` / `CreationDate`; **process-instance identity =
PID + `CreationDate.Ticks`** (serialized as `ToString("o", InvariantCulture)` and `.Ticks`) with the
accepted **sub-resolution collision residual recorded** and no mathematical uniqueness claimed;
**canonicalization through `CreateFileW`** (`GENERIC_READ` `0x80000000`, share
`READ|WRITE|DELETE` `0x00000007`, `NULL` security attributes, `OPEN_EXISTING` `3`,
`FILE_ATTRIBUTE_NORMAL` `0x00000080`, `NULL` template) **plus
`GetFinalPathNameByHandleW(FILE_NAME_NORMALIZED + VOLUME_NAME_DOS, flags = 0, 32768-WCHAR buffer)`**
with return `0` or `>= 32768` failing closed and `CloseHandle` always on a `finally`-equivalent path;
**path text kept exactly as returned** (`\\?\` retained, no slash/case/drive-letter normalization) and
compared with **`-ceq`** (safe false-negative preferred over permissive equivalence); **SHA-256 via
`Get-FileHash -Algorithm SHA256 -LiteralPath`** on both the process-reported path and the accepted
target literal, each required to equal the accepted digest (hex letter case the only normalization,
`-ieq`); **version verification only through the exact frozen `package.json`** (no binary invocation, no
PATH/npm lookup) requiring `name = opencode-ai`, `version = 1.18.11` and a `bin.opencode` that resolves
under the accepted package root to the accepted executable canonicalized by the same procedure; a
**25-field identity snapshot**; the **S0/S1 two-snapshot plan** (no HTTP between them, full identity
equality required) that also freezes the **later Mode-B PRE/POST target-continuity contract** (contract
only — no Mode-B request set, no SIC outcome, no HTTP); the **three-outcome taxonomy**
`ETB_SATISFIED` / `ETB_UNSATISFIED` / `HARNESS_INVALID` with `ETB_UNSATISFIED` explicitly **not** SIC/P6/
G0.5 failure and `HARNESS_INVALID` reserved for untrustworthy oracle machinery only (no ETB semantic
result, no retry, stop and re-authorize); and **evidence serialization** at
`docs/v0.3/evidence/etb-execution/ETB_EVIDENCE.json` (`schema_version` `devrelay-etb-v1`, ordered
top-level fields, UTF-8 no-BOM, LF only, one final LF, no comments, no user/session/prompt/provider
content, frozen `UTF8Encoding($false)` writer) plus `MANIFEST.sha256` and a result artifact
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT.md` marked **CANDIDATE ETB RESULT / AWAITING INDEPENDENT
RESULT REVIEW**.  Even an accepted `ETB_SATISFIED` would mean only that the exact configured endpoint is
deterministically bound to the accepted target and that Mode-B SIC oracle **construction** may resume
after independent ETB result acceptance — it would not establish SIC semantics, P6, G0.5, session
incarnation, provenance, Mode-B PASS, Case-C authorization or `adopt_completed_turn`.  Preserved
unchanged: `opencode.base_url` is still `""` (no configuration mutation in this round and none before a
separate authorization); no endpoint is established; no listener existence or OpenCode liveness is
asserted; Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED /
PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`; `G0.5 / P6` remains `NOT RUN /
DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED`
and G0.5 **NOT CLOSED**; `G1`/`G2` remain `NOT RUN`; Case-C and v0.3-E implementation remain **NOT
AUTHORIZED**; `adopt_completed_turn` remains **DISABLED**; `U1 = U1_NOT_ESTABLISHED`,
`U2 = U2_ESTABLISHED`, `U3 = U3_ESTABLISHED`, `MODE L = MODE_L_MECHANISM_NOT_YET_FREEZABLE`,
`MODE P = MODE_P_MECHANISM_FREEZABLE` and the accepted owner decision are unchanged.  This design round
performed **0** web/network access, **0** `Get-NetTCPConnection` executions, **0** live `Get-CimInstance`
process queries, **0** listener/process/port enumeration, **0** endpoint probes, **0** config mutations,
**0** OpenCode starts, **0** HTTP, **0** `/doc`, **0** `/session`, **0** ETB executions, **0** SIC
attempts, **0** Mode-B oracle work, **0** provider/model calls, **0** G0.5 and **0** G1/G2 activity, and
**0** runtime/test/dependency/version changes; the tracked worktree is clean, and the ignored/untracked
`PROJECT_MEMORY.md` persists.

**The ETB Mode-P execution-oracle candidate was rejected by independent review, and a round-2
remediation revision now exists (still a candidate: not accepted, not frozen, not executed).**  The
independent review issued *REQUEST_CHANGES — V0.3-E ETB MODE-P EXECUTION ORACLE* (**P0 = 0, P1 = 3,
P2 = 2**) against candidate `b117daf` (blob `280e688b…`), so that candidate is **not** accepted and
**not** frozen and the last authoritative pre-oracle baseline remains `b3be79d`.
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md` was revised **in place** (no second oracle file) into a
self-contained round-2 remediation candidate.  The review's accepted portions are **preserved
unchanged** — owner tuple; ETB-definition conformance; production config-reader semantics
(**CONFIG_EXACTNESS_SOUND**); listener query and `Count == 1`; PID/process query; `CreationDate` identity
semantics; `CreateFileW` parameter values; `GetFinalPathNameByHandleW` flags/buffer size; AS-IS `\\?\`
with `-ceq`; package/version/bin binding; dual SHA-256 target rule; 25-field snapshot; S0/S1 plan; later
Mode-B PRE/POST contract; `HARNESS_INVALID` as pre-semantic/no-ETB-result; no-shopping; configuration
timing; status preservation — and **only the five blocking gaps were tightened**: **P1-A** native
machinery frozen verbatim (exact type `DevRelayEtbNativeV1`; the complete ready-to-use C# `Add-Type`
source with three `kernel32.dll` `DllImport` declarations using `EntryPoint`/`CharSet.Unicode`/
`ExactSpelling`/`SetLastError`, `LPWStr` marshaling, `StringBuilder [Out]` buffer and `bool`
`CloseHandle` return; the exact `Add-Type -TypeDefinition $nativeSource -Language CSharp -ErrorAction
Stop` invocation; `IntPtr` handles with `INVALID_HANDLE_VALUE = [IntPtr](-1)`; the
`[System.Text.StringBuilder]::new(32768)` buffer with the exact `$buffer.ToString(0, [int]$length)`
read-out; no NUL-terminated unbounded read, no resize, no retry; `CloseHandle` always on a
`finally`-equivalent path with a `false` return classified `HARNESS_INVALID`; the same helper applied to
both paths); **P1-B** atomic evidence publication frozen (directory `docs/v0.3/evidence/etb-execution`;
three finals plus three **same-directory** `.tmp` paths; the six-path preexistence rule where any existing
path yields `HARNESS_INVALID` with no delete/overwrite/cleanup/retry; the temp write primitive
`UTF8Encoding(false)` → `FileStream` `CreateNew`/`Write`/`FileShare.None` → `Flush(true)` → close →
`ReadAllBytes` byte-equality; evidence temp verification for byte equality, exactly one final LF, the
byte before it being neither LF nor CR, no BOM, `ConvertFrom-Json` parse, matching `schema_version` and
`outcome`; in-memory result construction written only to the result temp; and `System.IO.File.Move(temp,
final)` with no overwrite only after all three temps verify, in the exact order evidence → manifest →
result with the result published **last**, followed by per-move and post-set verification); **P1-C**
manifest construction/verification frozen (coverage of exactly the one evidence file, never itself and
never the Markdown result; exactly one line `<64-lowercase-sha256><two ASCII spaces>docs/v0.3/evidence/
etb-execution/ETB_EVIDENCE.json<LF>`; no header or comments; UTF-8 no-BOM/LF; digest computed over the
intended evidence bytes before publication; read-back byte equality plus digest/spaces/path exactness;
and the frozen in-memory hasher `SHA256.Create()` → `ComputeHash` → lowercase hex, which is
evidence-machinery hashing only and does not change the `Get-FileHash` target-executable rule); **P2-A**
failure taxonomy frozen per class via a deterministic table (config reader, PowerShell command
availability, listener, process, Add-Type/P-Invoke, hashing, package manifest, evidence machinery) with
any unclassified unexpected exception classified `HARNESS_INVALID`, no ETB semantic result, no retry,
stop; **P2-B** timestamps and JSON frozen (`[System.DateTimeOffset]::UtcNow` formatted
`yyyy-MM-dd'T'HH:mm:ss.fffffff'Z'` with `InvariantCulture` for both timestamps, no local time;
`ConvertTo-Json -Depth 12 -Compress` written with `UTF8Encoding($false)` as one JSON line plus exactly
one LF and no CRLF conversion; every object `[ordered]` with the frozen top-level, `endpoint`, `target`,
snapshot, `checks` (18 keys valued only `PASS`/`FAIL`/`NOT_REACHED`), `non_claims` (6 ordered entries)
and `activity_counters` (14 ordered keys) orders, plus a frozen value vocabulary — `MODE_P`, `http`,
`IPv4`, `127.0.0.1`, `4096`, `http://127.0.0.1:4096`, `NONE`, `Listen`, lowercase-hex digests, integer
PIDs/ports/ticks — so no executor choice remains).  Also newly frozen: partial-publication semantics (any
partial output set is non-authoritative and invalid as an ETB result, nothing is deleted, and the
existence of the evidence or manifest file — or even the Markdown result — without a fully verified final
set never means an ETB result exists) and the rule that a provisional `ETB_SATISFIED`/`ETB_UNSATISFIED`
**must not survive** an evidence-integrity failure, the final classification becoming `HARNESS_INVALID /
NO ETB SEMANTIC RESULT`; the configuration-establishment fidelity requirement that the future separately
authorized stage write the exact owner literal `http://127.0.0.1:4096` with no trailing slash; and
static-anchor hygiene (line numbers informational only — module path, symbol names and the semantic call
path are the frozen authority).  Recorded status is unchanged and unimplicated as accepted: `ETB =
DEFINITION ACCEPTED / NOT EXECUTED` and `ETB EXECUTION / ORACLE = CANDIDATE / NOT ACCEPTED / NOT
AUTHORIZED / NOT EXECUTED`.  The executor-choice self-check over the nineteen machinery items found **no
remaining runtime choice**, which is why the revision may be committed as a candidate.  `opencode.base_url`
remains `""`; no evidence directory or evidence file was created; no native type was compiled; no
PowerShell oracle code was executed; the tracked worktree is clean and the ignored/untracked
`PROJECT_MEMORY.md` persists.  This remediation round performed **0** web/network access, **0** live
endpoint queries, **0** `Get-NetTCPConnection` executions, **0** live `Get-CimInstance` queries, **0**
listener/process/port enumeration, **0** config mutations, **0** OpenCode starts, **0** HTTP, **0**
`/doc`, **0** `/session`, **0** `Add-Type` executions, **0** P/Invoke executions, **0** evidence
publications, **0** ETB executions, **0** SIC attempts, **0** Mode-B oracle work, **0** provider/model
calls, **0** G0.5 and **0** G1/G2 activity, and **0** runtime/test/dependency/version changes.  Preserved:
Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED /
PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`; `G0.5 / P6` remains `NOT RUN / DEFINITION
ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED` and G0.5
**NOT CLOSED**; `G1`/`G2` remain `NOT RUN`; Case-C and v0.3-E implementation remain **NOT AUTHORIZED**;
`adopt_completed_turn` remains **DISABLED**.

**The Round-2 ETB Mode-P execution oracle was independently approved and is now authoritative accepted
repository status: ACCEPTED / FROZEN / NOT EXECUTED / EXECUTION NOT AUTHORIZED.**  The independent review
issued *APPROVE V0.3-E ETB MODE-P ROUND-2 EXECUTION ORACLE* (**P0 = 0, P1 = 0, P2 = 0**; two
non-blocking P3s) — an independent review decision, not executor self-approval — binding exactly
`oracle_commit = 1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc` and `oracle_sha256 =
01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921`
(`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md`).  **Oracle provenance rule (permanent, authoritative):**
that `oracle_commit`/`oracle_sha256` pair is the accepted immutable oracle identity; a later
acceptance-bookkeeping commit, a later execution/configuration-authorization commit, and the current HEAD
at execution time **MUST NOT** replace `oracle_commit`, and the future ETB evidence fields
`oracle_commit`/`oracle_sha256` must reference exactly this independently accepted oracle.  The artifact
itself is **immutable** and was **not** modified: it keeps its construction-time `ORACLE CANDIDATE / NOT
ACCEPTED / NOT FROZEN` header under the established immutable-candidate-artifact + independent
approval-record + authoritative active-status pattern.  Authoritative status now reads `ETB = DEFINITION
ACCEPTED / NOT EXECUTED` together with `ETB EXECUTION / ORACLE = ACCEPTED / FROZEN / NOT EXECUTED /
EXECUTION NOT AUTHORIZED`; **no** `ETB_SATISFIED`, `ETB_UNSATISFIED`, `HARNESS_INVALID` result or
`ETB_EXECUTED` is created.  Accepted oracle scope (independently reviewed, semantics unchanged): the
production config-reader semantics; exact Mode-P endpoint verification; the unique-listener rule; the
unique owning-PID rule; the PID + `CreationDate` identity discriminator; the exact P/Invoke declarations;
the `CreateFileW` parameters; the `GetFinalPathNameByHandleW` procedure; the canonical-path AS-IS /
case-sensitive equality rule; the dual executable SHA-256 checks; package/version/bin binding; the
25-field identity snapshot; the S0/S1 ETB snapshot plan; the later Mode-B PRE/POST continuity contract;
the deterministic failure taxonomy; the UTC timestamp format; the ordered JSON schema; the exact JSON
writer settings; temp/final paths; the preexistence policy; `CreateNew` + `Flush(true)` + read-back
verification; manifest coverage/format/SHA-256 procedure; the result template; the same-directory
`File.Move` publication procedure; publication ordering; post-publication verification; partial-output
semantics; `HARNESS_INVALID` = NO ETB SEMANTIC RESULT; and no shopping / no fallback / no HTTP.  Owner
inputs remain frozen and unreinterpreted — **MODE P — PRE-EXISTING TARGET**; **CLASS A — OWNER-SUPPLIED
FIXED ENDPOINT**; `http` / IPv4 / `127.0.0.1` / `4096` / `http://127.0.0.1:4096`; fallback **NONE**.
Configuration state is unchanged: the owner-authorized endpoint is `http://127.0.0.1:4096` while the
currently configured endpoint is **NONE** and `.devrelay/config.yaml` → `opencode.base_url` remains
`""`; no configuration mutation is authorized or performed in this round, and the separately authorized
future configuration-establishment stage must write the exact owner literal `http://127.0.0.1:4096`
with **no trailing slash**.  **Rejected-candidate history preserved:** `b117daf` was rejected with
*REQUEST_CHANGES — V0.3-E ETB MODE-P EXECUTION ORACLE* (P0 = 0, P1 = 3, P2 = 2) and remains
unrewritten; the accepted oracle is the Round-2 remediation at `1c6c7cd`, **not** `b117daf`.  Review P3s
recorded as **non-blocking** (neither an unresolved oracle blocker): **P3-1** the executor's chat report
rendering lost the PowerShell backtick in the displayed `$json + "`n"` expression while the actual
tracked oracle text was verified correct; **P3-2** the standing `PROJECT_MEMORY` wording issue remains,
with the preferred wording "**tracked worktree clean; ignored/untracked `PROJECT_MEMORY.md` persists**"
used here.  **Next-stage classification:** `ETB EXECUTION / CONFIGURATION AUTHORIZATION = NOT YET GRANTED
/ NOT YET EXECUTED`; the next possible stage after this bookkeeping is independently confirmed is a
**separate ETB execution/configuration authorization**, which may authorize setting
`opencode.base_url = http://127.0.0.1:4096` and exactly one ETB execution under the accepted frozen
oracle — **this bookkeeping authorizes neither**.  **Sequencing (no stage may be skipped):** ETB
definition accepted → capability prerequisites accepted → owner mode/endpoint decision accepted → ETB
execution oracle designed → independent oracle approval → acceptance bookkeeping → independent
bookkeeping confirmation; **then only**: separate execution/configuration authorization → configuration
establishment → exactly one ETB execution attempt → independent ETB result review → only if
`ETB_SATISFIED` is independently accepted may Mode-B SIC oracle construction resume.  An accepted ETB
execution oracle does **not** itself mean the endpoint has been configured or ETB has been satisfied, so
Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED /
PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`; `G0.5 / P6` remains `NOT RUN /
DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED`
and G0.5 **NOT CLOSED**; `G1`/`G2` remain `NOT RUN`; Case-C and v0.3-E implementation remain **NOT
AUTHORIZED**; `adopt_completed_turn` remains **DISABLED**.  This bookkeeping round performed **0**
web/network access, **0** endpoint queries, **0** `Get-NetTCPConnection` executions, **0** live
`Get-CimInstance` queries, **0** listener/process/port enumeration, **0** config mutations, **0** OpenCode
starts, **0** HTTP, **0** `/doc`, **0** `/session`, **0** `Add-Type` executions, **0** P/Invoke
executions, **0** evidence publications, **0** ETB executions, **0** SIC attempts, **0** Mode-B oracle
work, **0** provider/model calls, **0** G0.5 and **0** G1/G2 activity, and **0**
runtime/test/dependency/version changes; no evidence file and no result artifact were created; the
tracked worktree is clean and the ignored/untracked `PROJECT_MEMORY.md` persists.

**A candidate authorization record for the one-shot ETB execution / configuration action now exists (not
accepted, not effective, not executed).**  `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_AUTHORIZATION.md` is
marked **ETB EXECUTION / CONFIGURATION AUTHORIZATION / CANDIDATE RECORD / NOT ACCEPTED / NOT EFFECTIVE /
DOES NOT MODIFY CONFIGURATION / DOES NOT EXECUTE ETB / DOES NOT START OPENCODE / DOES NOT AUTHORIZE HTTP /
ONE ETB ATTEMPT ONLY IF LATER INDEPENDENTLY ACCEPTED**, so the current active authorization status is
`ETB EXECUTION / CONFIGURATION AUTHORIZATION = CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT EXECUTED`.
Only if a separate independent authorization review accepts it may it authorize, in order, (A) exactly
one configuration establishment — writing `http://127.0.0.1:4096` (no trailing slash, no alternate URI,
no other field) to `<root>/.devrelay/config.yaml` → `opencode.base_url`, currently `""`, with the exact
before/after diff recorded — and then (B) **exactly ONE** ETB execution attempt under the accepted frozen
oracle, bound permanently to `oracle_commit = 1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc` and
`oracle_sha256 = 01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921` — the future
execution must **not** use `d058b38`, the authorization commit, the execution-time HEAD or any later
commit as `oracle_commit`, and no oracle modification is authorized.  Frozen boundaries: Mode P remains
**pre-existing target** (no OpenCode start/restart, no new instance, no listener creation, no rebinding,
no Mode P → Mode L switch, and no recovery by target creation); fallback stays **NONE** (no IPv4 → IPv6,
`localhost`, `::1`, other/first-free/ephemeral port, alternate executable or installation, PATH-selected
target, log/listener/process-derived endpoint, or retry against another endpoint); the authorized
**attempt budget is exactly one**, consumed immediately before the **first oracle operational probe after
configuration establishment** (pure configuration establishment and static preflight of oracle
provenance, authorization identity and pre-mutation config state do **not** consume it), with no rerun, no
"verification rerun" and no second attempt after `ETB_SATISFIED`, `ETB_UNSATISFIED` or `HARNESS_INVALID`
— any further attempt needs new authorization plus independent review; a non-deterministic configuration
mutation must **not** be improvised but returned as a control failure for review (no substitute endpoint,
no other field, no alternate config mechanism); outputs may use **only** the oracle-frozen evidence/result
paths; the result may only be `ETB_SATISFIED`, `ETB_UNSATISFIED` or `HARNESS_INVALID / NO ETB SEMANTIC
RESULT`, and none is authoritative before separate independent ETB-result review; `ETB_UNSATISFIED` is
**not** SIC/P6/G0.5 failure and not a claim that OpenCode cannot support Mode B; `HARNESS_INVALID` means
**no ETB semantic result exists**, with no retry or repair-and-continue inside the same authorization;
**no HTTP**, no `/doc`, no `/session` and no provider/model request are authorized, and no Mode-B HTTP
activity is authorized; **no OpenCode start/restart** is authorized; the frozen future execution order is
authorization identity → oracle provenance → config precondition → exact `base_url` write → production
reader verification → configuration-establishment evidence → exactly one ETB attempt → consume 1 of 1
before the first live probe → execute the frozen oracle → publish the oracle-defined candidate
evidence/result → **STOP** → independent ETB result review (no Mode-B construction in the same round);
**no automatic configuration rollback is authorized** — `opencode.base_url` remains
`http://127.0.0.1:4096` after the attempt unless a future separately authorized action changes it, with no
rollback-on-failure and no executor discretion; and the accepted oracle's output-preexistence rule is
preserved (no deletion and no overwrite of old outputs; a failed precondition follows the frozen
`HARNESS_INVALID`/no-result semantics).  Even a future accepted `ETB_SATISFIED` would establish none of
SIC semantics, P6, G0.5, session incarnation, turn provenance, message provenance, pending-handle
semantics, Mode-B PASS, Case-C authorization or `adopt_completed_turn`; it would only permit independent
ETB result review and, only once `ETB_SATISFIED` is independently accepted, the resumption of Mode-B SIC
oracle construction.  Preserved unchanged: `ETB = DEFINITION ACCEPTED / NOT EXECUTED`; `ETB EXECUTION /
ORACLE = ACCEPTED / FROZEN / NOT EXECUTED / EXECUTION NOT AUTHORIZED`; owner inputs (**MODE P**,
**CLASS A**, `http` / IPv4 / `127.0.0.1` / `4096` / `http://127.0.0.1:4096`, fallback **NONE**) with no
reinterpretation; `opencode.base_url` still `""` with no configuration mutation in this round; Mode-B
remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE
CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER` (this authorization candidate does **not** unblock
it); `G0.5 / P6` remains `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP`
with `P6 = UNPROVEN / UNSATISFIED` and G0.5 **NOT CLOSED**; `G1`/`G2` remain `NOT RUN`; Case-C and v0.3-E
implementation remain **NOT AUTHORIZED**; `adopt_completed_turn` remains **DISABLED**.  This
authorization-recording round performed **0** web/network access, **0** endpoint queries, **0**
`Get-NetTCPConnection` executions, **0** live `Get-CimInstance` queries, **0** port/listener/process
enumeration, **0** config mutations, **0** OpenCode starts/restarts, **0** HTTP, **0** `/doc`, **0**
`/session`, **0** `Add-Type` executions, **0** P/Invoke executions, **0** evidence publications, **0** ETB
executions, **0** SIC attempts, **0** Mode-B oracle work, **0** provider/model calls, **0** G0.5 and **0**
G1/G2 activity, and **0** runtime/test/dependency/version changes; no evidence file and no result
artifact were created; the tracked worktree is clean and the ignored/untracked `PROJECT_MEMORY.md`
persists.

**The ETB execution/configuration authorization candidate was rejected by independent review, and a
round-2 remediation revision now exists (still a candidate: not accepted, not effective, not executed).**
The independent review issued *REQUEST_CHANGES — V0.3-E ETB EXECUTION / CONFIGURATION AUTHORIZATION*
(**P0 = 0, P1 = 2, P2 = 2**) against `f52cb2b4c0ece73097511c816b448d9ede649fb5`, which **remains rejected**
and unamended; the last authoritative pre-authorization baseline remains `d058b38`.
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_AUTHORIZATION.md` was revised **in place** (no second authorization
artifact) into a self-contained round-2 remediation candidate that preserves the review's accepted
portions (authorization scope; oracle provenance; owner tuple; one-ETB-attempt ceiling; no OpenCode start;
no HTTP; fallback NONE; configuration-after-attempt policy; ETB result/non-claim semantics; Mode-B/G0.5
preservation) and closes exactly four gaps.  **P1-A config-mutation mechanism** is now frozen byte-exactly
from a read-only static audit of the current file: `PRE_CONFIG_SHA256 =
daaf72578cb4a91b5adeb481530baf47577174325167caddf7249964da7923a8`, `PRE_CONFIG_SIZE = 1876` bytes, **no
BOM**, **LF only** (0 CRLF, final LF), valid UTF-8, a **clean duplicate-key structural audit** (exactly one
effective `opencode` key and exactly one effective `base_url` key; no anchors, aliases or merge keys), and
production-resolved `opencode.base_url == ""`; the mutation is a **byte-exact patch** over the unique
24-byte span `OLD_CONFIG_SPAN_HEX = 6f70656e636f64653a0a2020626173655f75726c3a202222` (occurrence count
exactly 1) replaced by `NEW_CONFIG_SPAN_HEX =
6f70656e636f64653a0a2020626173655f75726c3a2022687474703a2f2f3132372e302e302e313a3430393622`,
yielding the statically constructed post-image `POST_CONFIG_SIZE = 1897` bytes / `POST_CONFIG_SHA256 =
b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf`, with a verified byte-diff witness
that only that span changes (1065 unchanged prefix bytes, 787 unchanged suffix bytes) and **no**
`yaml.safe_dump`, regex edit, generic string replacement or manual-editor mutation authorized; the writer
is frozen as a single `python` invocation using exclusive-create (`xb`), complete post-image write,
stream flush, `os.fsync`, close, read-back byte/hash verification, publication by exactly
`os.replace(CONFIG_TEMP, CONFIG_FINAL)` in the same directory, post-replace read-back verification and one
production-reader invocation requiring the resolved value `http://127.0.0.1:4096`, with
`CONFIG TEMP = <root>/.devrelay/config.yaml.etb-auth.tmp`, **CONFIG BACKUP = NONE** and a temp
non-existence precondition.  **P1-B authorization-use / pre-ETB failure / reuse semantics** are frozen:
two **separate** one-shot budgets — `AUTHORIZATION_USE_BUDGET = 1 of 1` and `ETB_ATTEMPT_BUDGET = 1 of 1`
— where the authorization is consumed **immediately at the start of the future operational round, before
config mutation, config-evidence creation, oracle output checks or ETB execution**, can never be reused,
and any later failure (even with ETB never started) stops the round with the frozen pre-ETB token
**`AUTHORIZATION_CONTROL_FAILURE`** (authorization consumed, ETB NOT started, `ETB_ATTEMPT = 0/1`, **no**
ETB semantic result — and explicitly not `ETB_UNSATISFIED`/`ETB_SATISFIED`/`HARNESS_INVALID`/SIC/P6/G0.5
failure), with no retry, no repair-and-continue and no preparation-retry loophole.  **P2-A
output-precondition timing** is reconciled: the authorization layer no longer pre-checks the oracle's six
output paths; instead `ETB_ATTEMPT = 1 of 1` is consumed **immediately before entering the accepted frozen
oracle at its first step**, so all oracle machinery (identity checks, output-preexistence checks, HARNESS
validation, live queries) runs **inside** the single consumed attempt and an oracle preexistence failure
correctly yields `HARNESS_INVALID / NO ETB SEMANTIC RESULT` with the attempt already consumed.  **P2-B
config-establishment evidence** is frozen at `docs/v0.3/evidence/etb-execution/CONFIG_ESTABLISHMENT.json`
(+ `.tmp`) as **authorization/configuration control evidence only** — not ETB semantic evidence, not
covered by the oracle `MANIFEST.sha256`, not an ETB result — with `schema_version =
devrelay-etb-config-establishment-v1`, an exact 17-field ordered top-level schema (`schema_version`,
`authorization_commit`, `authorization_sha256`, `oracle_commit`, `oracle_sha256`, `config_path`,
`pre_config_sha256`, `expected_pre_config_sha256`, `pre_resolved_base_url`, `authorized_base_url`,
`post_config_sha256`, `expected_post_config_sha256`, `post_resolved_base_url`, `mutation_scope`,
`authorization_use`, `etb_attempt`, `control_status`), frozen values (`config_path =
.devrelay/config.yaml`; `authorized_base_url = http://127.0.0.1:4096`; `mutation_scope =
opencode.base_url_only`; `authorization_use = 1/1_CONSUMED`; `etb_attempt = 0/1_NOT_STARTED`;
`control_status = CONFIG_ESTABLISHED`), and the accepted oracle's deterministic serialization discipline
(`ConvertTo-Json -Depth 12 -Compress`, UTF-8 no-BOM, one JSON line plus exactly one LF, `UTF8Encoding(false)`,
temp exclusive create → write → durable flush → close → read-back verification → same-directory
`System.IO.File.Move(temp, final)` without overwrite).  The authorization identity model is frozen too
(`authorization_commit`/`authorization_sha256` = the independently accepted commit and blob of **this**
revision, not replaceable by later bookkeeping or execution-time HEAD), and a 19-step future operational
order is frozen (enter authorization → consume authorization use → verify identities → verify config
pre-image and pre-value → construct post-image → write/flush/read-back temp → `os.replace` → read-back
verify → production-reader verify → publish config evidence → consume ETB attempt → invoke the frozen
oracle from its first step → allow only the oracle's control state → publish only oracle-defined outputs →
STOP → independent ETB result review), with **no automatic configuration rollback** after any failure and
the accepted oracle artifact left **immutable**.  Preserved unchanged: `ETB = DEFINITION ACCEPTED / NOT
EXECUTED`; `ETB EXECUTION / ORACLE = ACCEPTED / FROZEN / NOT EXECUTED / EXECUTION NOT AUTHORIZED`; owner
inputs (MODE P, CLASS A, `http` / IPv4 / `127.0.0.1` / `4096`, fallback NONE); `opencode.base_url` still
`""` with **no** configuration mutation in this round; Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT
FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE
BLOCKER`; `G0.5 / P6` remains `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY
GAP` with `P6 = UNPROVEN / UNSATISFIED` and G0.5 **NOT CLOSED**; `G1`/`G2` remain `NOT RUN`; Case-C and
v0.3-E implementation remain **NOT AUTHORIZED**; `adopt_completed_turn` remains **DISABLED**.  The current
authorization status is `ETB EXECUTION / CONFIGURATION AUTHORIZATION = ROUND-2 CANDIDATE / NOT ACCEPTED /
NOT EFFECTIVE / NOT EXECUTED` — no authorization is granted, no config changed and no ETB executed.  The
executor-choice self-check over the eighteen machinery items found **no remaining runtime choice**.  This
remediation-design round performed **0** web/network access, **0** endpoint queries, **0**
`Get-NetTCPConnection` executions, **0** live `Get-CimInstance` queries, **0** port/listener/process
enumeration, **0** config mutations, **0** OpenCode starts, **0** HTTP, **0** `/doc`, **0** `/session`,
**0** `Add-Type` executions, **0** P/Invoke executions, **0** execution-evidence publications, **0** ETB
executions, **0** SIC attempts, **0** Mode-B oracle work, **0** provider/model calls, **0** G0.5 and **0**
G1/G2 activity, and **0** runtime/test/dependency/version changes; static read-only config
reads/hashes/audit are recorded separately and are not operational ETB activity; the tracked worktree is
clean and the ignored/untracked `PROJECT_MEMORY.md` persists.

**The ETB execution/configuration authorization Round-2 candidate was rejected by independent review, and
a round-3 durable-claim remediation candidate now exists (still a candidate: not accepted, not effective,
not executed).**  The independent review issued *REQUEST_CHANGES — V0.3-E ETB EXECUTION / CONFIGURATION
AUTHORIZATION ROUND-2* (**P0 = 0, P1 = 1, P2 = 0, P3 = 2**) against `390eda1aeacb33032611030d47727e0a69650459`,
which **remains rejected** and unamended (as does the earlier `f52cb2b` rejection with P0 = 0, P1 = 2,
P2 = 2); the last authoritative pre-authorization baseline remains `d058b38`.  The review **closed**
`P1_A_CONFIG_MUTATION`, `P1_B_AUTHORIZATION_REUSE`, `P2_A_OUTPUT_TIMING` and `P2_B_CONFIG_EVIDENCE`, and all
Round-2 frozen semantics are preserved unchanged (byte-exact config mutation with `PRE_CONFIG_SHA256 =
daaf7257…` / 1876 bytes → `POST_CONFIG_SHA256 = b5e4abab…` / 1897 bytes through the unique 24-byte span;
`CONFIG TEMP`/`CONFIG FINAL` with `CONFIG BACKUP = NONE`; the `python` `xb`/`os.fsync`/`os.replace` writer
with read-back verification; the 17-field `devrelay-etb-config-establishment-v1` control-evidence schema and
its deterministic serialization; both 1-of-1 budgets; the `AUTHORIZATION_CONTROL_FAILURE` token;
no-rollback; no-retry; owner inputs; oracle provenance).  `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_AUTHORIZATION.md`
was revised **in place** (no second authorization artifact) as a self-contained round-3 remediation
candidate that closes the remaining blocking finding — the execution-evidence directory does not exist and
parent-directory creation behaviour was unfrozen — and tightens the crash/replay nuance so that repository
state alone durably distinguishes the three states without chat history, executor memory or an ephemeral
process.  **Durable one-shot claim markers** now live under the **already existing** parent
`docs/v0.3/evidence` (deliberately not inside the not-yet-existent `etb-execution` directory):
`docs/v0.3/evidence/ETB_AUTHORIZATION_USE.claim` (+ `.tmp`) with `schema_version =
devrelay-etb-authorization-use-v1` and the ordered fields `schema_version`, `authorization_commit`,
`authorization_sha256`, `oracle_commit`, `oracle_sha256`, `state = CONSUMED` (UTF-8, no BOM, one LF), and
`docs/v0.3/evidence/ETB_ATTEMPT_USE.claim` (+ `.tmp`) with `schema_version =
devrelay-etb-attempt-use-v1` and the same ordered fields; **temp-or-final presence is authoritative and
fail-closed** (no parser success required), so a crash during claim writing or a missing final rename still
means CONSUMED.  The **durable consumption boundaries** are frozen: `AUTHORIZATION_USE = 1/1 CONSUMED` the
moment exclusive creation of the authorization claim temp succeeds (performed before config mutation,
before creating the `etb-execution` directory, before config evidence, before ETB-attempt claiming and
before ETB execution), and `ETB_ATTEMPT = 1/1 CONSUMED` the moment exclusive creation of the ETB attempt
claim temp succeeds (after successful configuration establishment and `CONFIG_ESTABLISHMENT.json`
publication, before entering the frozen oracle).  **Crash recovery** is frozen: a crash before successful
exclusive creation of the authorization claim temp leaves the authorization **UNUSED** (the only window in
which it remains unused), while a crash after it leaves it **CONSUMED** with no ambiguous pre-mutation
window; `PRE_CONFIG_SHA256` is **demoted to a corroborating invariant only** and is no longer the sole
authorization-consumption marker; a crash after ETB-attempt consumption can never permit rerunning ETB.  A
**durable state recovery table** fixes the interpretation: authorization claim absent + ETB claim absent →
`AUTHORIZATION UNUSED`; authorization present + ETB absent → `AUTHORIZATION CONSUMED / ETB NOT STARTED`;
both present → `AUTHORIZATION CONSUMED / ETB ATTEMPT CONSUMED`; ETB present while authorization absent →
**control-state inconsistency / fail closed / no execution / independent review required**.  The
**execution-evidence directory rule** is frozen: `docs/v0.3/evidence/etb-execution` is created only after
the authorization claim is durably consumed and before configuration mutation, exactly via
`[System.IO.Directory]::CreateDirectory("docs/v0.3/evidence/etb-execution")` (repository-root-resolved
exact equivalent allowed), with no alternate directory, parent search, timestamped directory, suffix or
fallback path, followed by a requirement that the exact path exists and **is a directory**; failure or a
non-directory at that path → `AUTHORIZATION_CONTROL_FAILURE` with authorization consumed and ETB not
started; a pre-existing **actual directory** is permitted (idempotent, never deleted or recreated), which
removes executor choice.  Claim markers are **never deleted** after success, `ETB_UNSATISFIED`,
`HARNESS_INVALID`, `AUTHORIZATION_CONTROL_FAILURE` or crash recovery — they are durable one-shot witnesses
— and a **future new authorization must define its own claim-marker namespace/path** before execution (no
executor may delete the markers to reuse the paths).  A 22-step operational order is frozen (static
identity/oracle verification → require authorization claim absent → **exclusive-create it (AUTHORIZATION
CONSUMED)** → publish it → create-or-verify the evidence directory → config-evidence paths absent → config
pre-image verification → production pre-value `""` → post-image construction → write/fsync/read-back temp →
`os.replace` → final SHA verification → production post-value verification → publish config evidence →
require ETB claim absent → **exclusive-create it (ETB ATTEMPT CONSUMED)** → publish it → invoke the frozen
oracle from its first step → only frozen control/result state → only oracle-defined outputs → STOP →
independent ETB-result review), with failure semantics frozen per window (pre-authorization-claim: still
UNUSED and no alternate action; post-authorization-claim/pre-ETB: consumed, `AUTHORIZATION_CONTROL_FAILURE`,
new authorization required; post-ETB-claim: attempt consumed, no second attempt, no ETB semantic result if
the oracle was never entered) and no-rollback preserved.  Current status:
`ETB EXECUTION / CONFIGURATION AUTHORIZATION = ROUND-3 CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT
EXECUTED`; **no claim marker currently exists**, no evidence directory is created now, and no config
mutation occurs now.  Preserved unchanged: `ETB = DEFINITION ACCEPTED / NOT EXECUTED`; `ETB EXECUTION /
ORACLE = ACCEPTED / FROZEN / NOT EXECUTED / EXECUTION NOT AUTHORIZED`; owner inputs; `opencode.base_url`
still `""`; Mode-B blocked (`NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED
/ PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`); `G0.5 / P6` unchanged with `P6 =
UNPROVEN / UNSATISFIED` and G0.5 **NOT CLOSED**; Case-C and v0.3-E implementation **NOT AUTHORIZED**;
`G1`/`G2` `NOT RUN`; `adopt_completed_turn` **DISABLED**.  This remediation-design round created **no**
claim markers, **no** `etb-execution` directory, **no** config-establishment evidence, **no** ETB evidence
or result, **no** config temp and **no** config mutation, and performed **0** web/network access, **0**
endpoint queries, **0** `Get-NetTCPConnection` executions, **0** live `Get-CimInstance` queries, **0**
port/listener/process enumeration, **0** OpenCode starts, **0** HTTP, **0** `/doc`, **0** `/session`, **0**
`Add-Type` executions, **0** P/Invoke executions, **0** ETB executions, **0** SIC attempts, **0** Mode-B
work, **0** provider/model calls, **0** G0.5 and **0** G1/G2 activity, and **0**
runtime/test/dependency/version changes; the tracked worktree is clean and the ignored/untracked
`PROJECT_MEMORY.md` persists.

**The ETB execution/configuration authorization Round-3 candidate was rejected by independent review, and
a round-4 claim-writer mechanical-closure candidate now exists (still a candidate: not accepted, not
effective, not executed).**  The independent review issued *REQUEST_CHANGES — V0.3-E ETB EXECUTION /
CONFIGURATION AUTHORIZATION ROUND-3* (**P0 = 0, P1 = 1, P2 = 1, P3 = 2**) against
`c106b2d93b272fb337795e8712f58e0c273088fa` (artifact blob
`29019f683c4c217654034fc1408d2942b0b384832125fe80b7a6303927d015b0`), which **remains rejected** and
unamended (as do `390eda1` with P0 = 0, P1 = 1, P2 = 0, P3 = 2 and `f52cb2b` with P0 = 0, P1 = 2, P2 = 2);
the last authoritative pre-authorization baseline remains `d058b38`.  `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_AUTHORIZATION.md`
was revised **in place** (no second authorization artifact) as a self-contained round-4 remediation
candidate that closes exactly the four Round-3 findings and redesigns nothing else.  **P1 — claim-writer
exactness:** both claim writers are now frozen to **Windows PowerShell / .NET only** (no Python claim
writer, no `os.fsync` alternative, no alternate language, no executor-authored replacement code) with one
exact implementation, `Write-DevRelayOneShotClaim`, embedded **verbatim** in the artifact (104 lines,
byte-identical to the frozen source): `[ordered]` claim object; `ConvertTo-Json -Depth 4 -Compress`;
`$json + "`n"` (exactly one final LF); `[System.Text.UTF8Encoding]::new($false)` (no BOM);
`[System.IO.FileStream]::new($TempPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write,
[System.IO.FileShare]::None)`; a single `$stream.Write($bytes, 0, $bytes.Length)`; `$stream.Flush($true)`;
`$stream.Dispose()` on a `finally`-equivalent path; `[System.IO.File]::ReadAllBytes` with explicit
byte-by-byte equality for both the temp and the published final; and publication by the **two-argument**
`[System.IO.File]::Move($TempPath, $FinalPath)` as the **sole** publication primitive, which must fail
rather than overwrite an existing destination (the explicit `File.Exists` check before the move is only an
additional fail-closed check) — with every alternative forbidden: no overwrite `File.Move` overload, no
`File.Replace`, no `Move-Item`, no `Rename-Item`, no Python rename, no `os.rename`, no `os.replace`, no
other primitive.  The **consumption boundary** remains the successful return of `FileMode.CreateNew` (which
MUST fail if the temp exists; no truncation, reuse or overwrite), and the exact future invocations for both
claims are frozen (authorization claim: temp/final `docs/v0.3/evidence/ETB_AUTHORIZATION_USE.claim.tmp` /
`.claim` with `devrelay-etb-authorization-use-v1`; ETB attempt claim: temp/final
`docs/v0.3/evidence/ETB_ATTEMPT_USE.claim.tmp` / `.claim` with `devrelay-etb-attempt-use-v1`; both bound to
the independently accepted authorization commit/SHA and to oracle `1c6c7cd` / `01675fa7…`), with writer
failure semantics frozen per claim (pre-existing temp or final ⇒ already CONSUMED ⇒ STOP without invoking
the writer; any later writer exception ⇒ remains CONSUMED, `AUTHORIZATION_CONTROL_FAILURE` for the
authorization claim with ETB not started, and for the ETB claim no ETB semantic result if the oracle was not
entered; no cleanup, no retry, no alternate writer, no second attempt).  **P2 — durability narrowing:** the
supported guarantee is now explicitly **PROCESS-CRASH RECOVERY** only — "if the PowerShell/executor process
terminates after successful OS-visible exclusive creation of a claim temp file, the next executor is
required to interpret TEMP or FINAL presence as CONSUMED and fail closed" — with an explicit non-claim
("THIS AUTHORIZATION DOES NOT CLAIM POWER-LOSS DURABILITY OR MACHINE-CRASH DURABILITY FOR CLAIM DIRECTORY
METADATA"), `Flush(true)` described as **file-content** flushing only, no parent-directory fsync guarantee,
and no guarantee for sudden power loss between filesystem metadata operations; unbounded
"durable/durably/durability" wording for claim markers was replaced with process-crash-recovery terminology
("process-crash recovery consumption boundary", "process-crash-persistent one-shot marker",
"filesystem-presence one-shot witness") without changing the logical state machine.  **P3-1 — tracking
policy:** the four claim paths are declared intended **untracked operational control-state artifacts**,
**not** part of the tracked-worktree-clean predicate, whose presence is expected after operational
authorization use; they MUST NOT be `git add`ed, staged, committed, deleted, renamed, archived or
normalized before independent ETB-result review; bookkeeping commits before that review MUST use an exact
allowlist of intended tracked documentation files and MUST exclude the markers; `.gitignore` must not be
modified; "**tracked worktree clean**" is frozen to mean *no tracked-file modification outside the
explicitly authorized operational changes* (not a globally empty `git status --porcelain`), and future
reports must list expected untracked operational artifacts separately rather than classifying the expected
markers as worktree drift; if a marker is found staged → STOP without auto-unstaging/deleting, and if found
committed unexpectedly → STOP without rewriting history, both reported for independent review, with the
presence semantics remaining fail-closed regardless of Git tracking state.  **P3-2 — restored invariant:**
the explicit rule is restored verbatim — the authorization layer MUST NOT pre-check, pre-interpret, delete,
repair or otherwise act on the accepted oracle's six frozen temp/final ETB output paths; only after
configuration establishment succeeds, `CONFIG_ESTABLISHMENT.json` succeeds and the ETB claim is
consumed/finalized does execution enter the accepted frozen oracle from its FIRST STEP, and the oracle
alone performs its own six-path output-preexistence validation inside the already-consumed ETB attempt.
Preserved semantically unchanged: the byte-exact config mutation (`PRE_CONFIG_SHA256 = daaf7257…` / 1876 →
`POST_CONFIG_SHA256 = b5e4abab…` / 1897 through the unique 24-byte span), the Python `xb`/`fsync`/`os.replace`
config writer and read-back, config no-rollback, the `devrelay-etb-config-establishment-v1`
path/schema/serialization, the exact `Directory.CreateDirectory` directory create/verify rule (still
CLOSED), the four-row state machine and TEMP-or-FINAL-means-consumed rule with no parser success required,
claim non-deletion, the future claim-namespace rule, the ETB attempt boundary, oracle provenance and the
owner tuple, and Mode-B/G0.5/implementation preservation.  Current status:
`ETB EXECUTION / CONFIGURATION AUTHORIZATION = ROUND-4 CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT
EXECUTED`; no operational authorization is granted, no claim is created now, no directory is created now,
no config is changed now and no ETB is executed now.  This remediation round performed **0** web/network
access, **0** endpoint queries, **0** `Get-NetTCPConnection` executions, **0** live `Get-CimInstance`
queries, **0** port/listener/process enumeration, **0** config mutations, **0** OpenCode starts, **0** HTTP,
**0** `/doc`, **0** `/session`, **0** `Add-Type` executions, **0** P/Invoke executions, **0**
execution-evidence publications, **0** ETB executions, **0** SIC attempts, **0** Mode-B work, **0**
provider/model calls, **0** G0.5 and **0** G1/G2 activity, and **0** runtime/test/dependency/version
changes; the tracked worktree is clean and the ignored/untracked `PROJECT_MEMORY.md` persists.

**The ETB execution/configuration authorization Round-4 candidate was rejected by independent review, and
a round-5 claim-path type semantic closure candidate now exists (still a candidate: not accepted, not
effective, not executed).**  The independent review issued *REQUEST_CHANGES — V0.3-E ETB EXECUTION /
CONFIGURATION AUTHORIZATION ROUND-4* (**P0 = 0, P1 = 0, P2 = 1, P3 = 2**) against
`008115d6988c76d3c4ce185f73d047d44f5d8579` (artifact blob
`dfe673e6ff961a7bdb324912ea541008d2ade98a5789b9bfc1581efe7f54bc10`); its **only blocking finding** was
`CLAIM_PATH_TYPE_SEMANTICS = OPEN` — the recovery/state-machine text treated TEMP or FINAL "presence" as
consumed while the exact writer checked only `[System.IO.File]::Exists(path)`, and `File.Exists` returns
false when the exact path is occupied by a directory, so a directory at a claim path was classified
differently by the state machine and by the writer (no authorization-reuse or ETB hazard was demonstrated,
but the classification was not deterministic).  The candidate **remains rejected** and unamended, as do
`c106b2d` (P0 = 0, P1 = 1, P2 = 1, P3 = 2), `390eda1` (P0 = 0, P1 = 1, P2 = 0, P3 = 2) and `f52cb2b`
(P0 = 0, P1 = 2, P2 = 2); the last authoritative pre-authorization baseline remains `d058b38`.
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_AUTHORIZATION.md` was revised **in place** (no second authorization
artifact) as a self-contained round-5 remediation candidate that closes exactly that finding and redesigns
nothing else.  **One exact path-occupancy predicate is now frozen**: `CLAIM_PATH_OCCUPIED(path) :=
[System.IO.File]::Exists(path) -or [System.IO.Directory]::Exists(path)`, with `CLAIM PATH ABSENT :=
File.Exists(path) == false AND Directory.Exists(path) == false`, applied **identically** to the
authorization claim TEMP, the authorization claim FINAL, the ETB-attempt claim TEMP and the ETB-attempt
claim FINAL, and no other meaning of "present", "exists" or "occupied" is permitted for claim-path state.
A **directory at any claim TEMP/FINAL path is OCCUPIED**: for the authorization claim that means
AUTHORIZATION CONSUMED → STOP → the writer MUST NOT proceed to `CreateNew` → no cleanup, no deletion, no
rename, no retry → independent review required before any future action; for the ETB-attempt claim it means
ETB ATTEMPT CONSUMED → STOP → no rerun → the writer MUST NOT proceed to `CreateNew` → no cleanup, no
deletion, no rename.  The artifact explicitly forbids trying to determine whether such a directory is
legitimate claim content — **occupancy alone is fail-closed** — and states that a partial claim file, a
zero-length claim file, a malformed claim file and a claim directory all count as OCCUPIED whenever the
predicate is true, with no parsing required and no repair authorized.  The **frozen writer source was
modified in place** (not replaced or redesigned) at exactly its three path checks — the initial TEMP
pre-check, the initial FINAL pre-check and the pre-`Move` FINAL re-check — to the multi-line
`File.Exists(...) -or Directory.Exists(...)` form (the function is otherwise byte-identical: same
`[ordered]` claim object, `ConvertTo-Json -Depth 4 -Compress`, real PowerShell LF, `UTF8Encoding(false)`,
`FileStream`/`FileMode.CreateNew`/`FileAccess.Write`/`FileShare.None`, single `Write(bytes,0,len)`,
`Flush(true)`, `Dispose()`, `ReadAllBytes` byte-by-byte verification, and the two-argument
`System.IO.File.Move`; the three `throw` lines are unchanged, and a mechanical reconstruction from the
Round-4 source applying only those three authorized replacements reproduces the new source exactly).  The
`FileMode.CreateNew` **consumption boundary is preserved for a previously ABSENT path**, while an OCCUPIED
temp path is now classified CONSUMED by fail-closed occupancy semantics and the writer must not attempt
`CreateNew` — so the directory-at-TEMP corner is never interpreted as UNUSED; the directory-at-FINAL
corners are covered both before invocation (FINAL OCCUPIED → already CONSUMED → STOP before `CreateNew`)
and after TEMP creation but before publication (the second frozen FINAL occupancy check throws
`DEVRELAY_CLAIM_FINAL_APPEARED`, the claim remains CONSUMED, and **no `File.Move` attempt is made**).  The
**recovery table is restated in OCCUPIED/ABSENT terms only** (both ABSENT → AUTHORIZATION UNUSED; auth
TEMP/FINAL OCCUPIED + ETB both ABSENT → AUTHORIZATION CONSUMED / ETB NOT STARTED; both OCCUPIED →
AUTHORIZATION CONSUMED / ETB ATTEMPT CONSUMED; auth both ABSENT + ETB TEMP/FINAL OCCUPIED → CONTROL-STATE
INCONSISTENCY / FAIL CLOSED / NO EXECUTION / INDEPENDENT REVIEW REQUIRED), with no undefined generic notion
of presence and no parser success required.  A **wording-only root binding** was added: future operational
execution MUST run with the repository root as its working directory before any relative frozen
claim/config/evidence path is evaluated, and all relative paths in this authorization are
repository-root-relative — no other root-resolution mechanism is introduced (the already accepted
root-binding verdict is not reopened).  Preserved semantically unchanged: the Round-3 claim-writer closure
and its PowerShell/.NET-only language, the process-crash-only recovery model with its explicit non-claim of
power-loss/machine-crash durability for claim directory metadata, the claim tracking/commit policy and the
frozen "tracked worktree clean" semantics, the future claim-namespace rule, claim non-deletion, the exact
`Directory.CreateDirectory` directory create/verify rule, the byte-exact config mutation
(`PRE_CONFIG_SHA256 = daaf7257…` / 1876 → `POST_CONFIG_SHA256 = b5e4abab…` / 1897), the
`devrelay-etb-config-establishment-v1` path/schema/serialization, both 1-of-1 budgets, the restored
output-precheck invariant (the authorization layer MUST NOT pre-check, pre-interpret, delete, repair or
otherwise act on the accepted oracle's six frozen temp/final ETB output paths — only the frozen oracle
checks them inside the consumed ETB attempt), the owner tuple, oracle provenance and Mode-B/G0.5
preservation.  Current status: `ETB EXECUTION / CONFIGURATION AUTHORIZATION = ROUND-5 CANDIDATE / NOT
ACCEPTED / NOT EFFECTIVE / NOT EXECUTED`; no authorization is granted, no claim is created, no directory is
created, no config mutation occurs and no ETB is executed.  This remediation round performed **0**
web/network access, **0** endpoint queries, **0** `Get-NetTCPConnection` executions, **0** live
`Get-CimInstance` queries, **0** port/listener/process enumeration, **0** config mutations, **0** OpenCode
starts, **0** HTTP, **0** `/doc`, **0** `/session`, **0** `Add-Type` executions, **0** P/Invoke executions,
**0** execution-evidence publications, **0** ETB executions, **0** SIC attempts, **0** Mode-B work, **0**
provider/model calls, **0** G0.5 and **0** G1/G2 activity, and **0** runtime/test/dependency/version
changes; the tracked worktree is clean and the ignored/untracked `PROJECT_MEMORY.md` persists.

**(Historical round entry — superseded by the `AUTHORIZATION_CONTROL_FAILURE` entry below, which records that
this authorization was subsequently consumed and is now SPENT / NOT REUSABLE.)**  The ETB
execution/configuration authorization is now INDEPENDENTLY ACCEPTED / GRANTED (Round 5), while no
operational action has occurred yet: authorization use UNUSED, ETB attempt NOT STARTED, `opencode.base_url`
still `""`.  The independent review — not executor self-approval — returned **APPROVE V0.3-E ETB
EXECUTION / CONFIGURATION AUTHORIZATION ROUND-5** with **P0 = 0, P1 = 0, P2 = 0, P3 = 2**, explicitly
closing `P1_A_CONFIG_MUTATION`, `P1_B_AUTHORIZATION_REUSE`, `P2_A_OUTPUT_TIMING`, `P2_B_CONFIG_EVIDENCE`,
`ROUND2_P1_DIRECTORY_RULE`, `ROUND3_P1_CLAIM_WRITER`, `ROUND3_P2_DURABILITY`, `ROUND3_P3_TRACKING_POLICY`,
`ROUND3_P3_OUTPUT_PRECHECK_EXPLICITNESS`, `CLAIM_PATH_ROOT_BINDING` and `CLAIM_PATH_TYPE_SEMANTICS`; the
authorization design phase is complete.  The approval binds **exactly** `authorization_commit =
64044fc45082cd63b0ae445c146d85720dfa1435` and `authorization_sha256 =
511ab1e2eb2e4f1194d2c55951e5b9616dc515d1180c6399dd658207d443d0d8` for the immutable artifact
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_AUTHORIZATION.md`.  **Permanent authorization provenance rule:** this
pair is immutable and must not be replaced by this acceptance-bookkeeping commit, by any later operational,
evidence or result-review bookkeeping commit, or by the execution-time HEAD; future authorization-claim
content and all operational provenance referencing this authorization must reference exactly this pair, and
**the bookkeeping commit produced by this round is NOT `authorization_commit`**.  The accepted authorization
identity and the accepted oracle identity remain **distinct** immutable provenance pairs — `oracle_commit =
1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc` / `oracle_sha256 =
01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921` (`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md`) —
and neither may replace the other.  **Current authoritative authorization status:**
`ETB EXECUTION / CONFIGURATION AUTHORIZATION = ACCEPTED / GRANTED / NOT EXECUTED / AUTHORIZATION USE UNUSED /
ETB ATTEMPT NOT STARTED`.  The accepted artifact remains an **immutable accepted object** whose
construction-time header still reads ROUND-5 CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT EXECUTED — exactly
the established immutable-artifact + approval-record + active-status pattern used for the accepted frozen ETB
oracle candidate — so the artifact was **not** edited by this bookkeeping; current status is represented only
by this CHANGELOG and by `docs/v0.3/V03E_ACCEPTANCE.md`.  **Current claim state (authoritative, verified):**
`AUTHORIZATION CLAIM TEMP = ABSENT`, `AUTHORIZATION CLAIM FINAL = ABSENT`, `ETB ATTEMPT CLAIM TEMP = ABSENT`,
`ETB ATTEMPT CLAIM FINAL = ABSENT`, therefore `AUTHORIZATION USE = UNUSED` and `ETB ATTEMPT = NOT STARTED`;
no claim has been created and no authorization has yet been operationally consumed.  **Current configuration
state:** owner-authorized endpoint `http://127.0.0.1:4096`; currently configured endpoint **NONE**;
`.devrelay/config.yaml` → `opencode.base_url = ""` with `PRE_CONFIG_SHA256 =
daaf72578cb4a91b5adeb481530baf47577174325167caddf7249964da7923a8` and `PRE_CONFIG_SIZE = 1876`; no config
mutation has occurred and none is performed by this bookkeeping.  **Future authorized configuration
mutation (not performed now):** the accepted authorization permits, only in the later operational execution
round, the exact already-frozen transition `opencode.base_url` from `""` to `http://127.0.0.1:4096` under the
byte-exact configuration procedure frozen in the accepted artifact.  **One-shot scope (referencing the
immutable artifact rather than reproducing it):** mode **MODE P — PRE-EXISTING TARGET**; endpoint policy
**CLASS A — OWNER-SUPPLIED FIXED ENDPOINT**; endpoint `http://127.0.0.1:4096`; fallback **NONE**;
authorization-use budget **1 of 1**; ETB-attempt budget **1 of 1**; OpenCode start/restart **NOT AUTHORIZED**;
HTTP **NOT AUTHORIZED**; Mode-B work in the operational ETB round **NOT AUTHORIZED**.  The accepted claim
model is summarised at status level only and is **not** strengthened: process-crash-only claim model,
filesystem-node occupancy predicate, exact PowerShell/.NET claim writer, repository-root path binding,
untracked claim-marker policy and distinct future namespace requirement — **no power-loss durability is
claimed**.  **Historical rejections preserved (not rewritten):** `f52cb2b` REQUEST_CHANGES (P0 = 0, P1 = 2,
P2 = 2); `390eda1` REQUEST_CHANGES ROUND-2 (P0 = 0, P1 = 1, P2 = 0, P3 = 2); `c106b2d` REQUEST_CHANGES
ROUND-3 (P0 = 0, P1 = 1, P2 = 1, P3 = 2); `008115d` REQUEST_CHANGES ROUND-4 (P0 = 0, P1 = 0, P2 = 1,
P3 = 2); then `64044fc` **APPROVE ROUND-5** (P0 = 0, P1 = 0, P2 = 0, P3 = 2).  The two Round-5 P3 findings
are recorded as **non-blocking only**: P3-1, an executor chat/report rendering loss of the PowerShell
backtick while the actual committed artifact was independently verified correct; P3-2, a small
mechanical-strengthening note around the repository-root/CWD binding whose actual binding was independently
accepted as CLOSED — **neither is an unresolved authorization blocker**.  **Mode-B is not unblocked** by this
approval: it remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED /
PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`, because configuration establishment has not
occurred, ETB has not executed, and `ETB_SATISFIED` has not been independently reviewed or accepted.
`G0.5 / P6` remains `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP` with
`P6 = UNPROVEN / UNSATISFIED` and G0.5 **NOT CLOSED** — authorization approval is **not** P6 evidence.
Case-C implementation `NOT AUTHORIZED`; v0.3-E implementation `NOT AUTHORIZED`; `G1 = NOT RUN`; `G2 = NOT
RUN`; `adopt_completed_turn` **DISABLED**.  **Authoritative sequence:** ETB definition accepted → capability
prerequisites accepted → owner mode/endpoint decision accepted → frozen ETB execution oracle independently
accepted → oracle acceptance bookkeeping independently accepted → execution/configuration authorization
designed → authorization Round-1 rejected → Round-2 rejected → Round-3 rejected → Round-4 rejected → Round-5
independently approved → **authorization acceptance bookkeeping (this round)** → independent bookkeeping
confirmation → exactly one operational authorization use → exact configuration establishment → exactly one
ETB attempt → independent ETB-result review → only an independently accepted `ETB_SATISFIED` may permit
Mode-B SIC oracle construction to resume; no stage may be skipped.  **Next stage classification:** after this
acceptance bookkeeping is independently confirmed, the next stage may be the **ETB EXECUTION / CONFIGURATION
OPERATIONAL ROUND** under exactly `authorization_commit = 64044fc…` / `authorization_sha256 = 511ab1e2…`
plus `oracle_commit = 1c6c7cd…` / `oracle_sha256 = 01675fa7…` — but **this bookkeeping round does not begin
that operational round**.  This bookkeeping round performed **0** web/network access, **0** endpoint queries,
**0** `Get-NetTCPConnection` executions, **0** live `Get-CimInstance` queries, **0** port/listener/process
enumeration, **0** config mutations, **0** claim creations, **0** claim-path directory creations, **0**
`etb-execution` directory creations, **0** OpenCode starts/restarts, **0** HTTP, **0** `/doc`, **0**
`/session`, **0** `Add-Type` executions, **0** P/Invoke executions, **0** `CONFIG_ESTABLISHMENT`
publications, **0** ETB evidence publications, **0** ETB executions, **0** SIC attempts, **0** Mode-B work,
**0** provider/model calls, **0** G0.5 and **0** G1/G2 activity, and **0** runtime/test/dependency/version
changes; the tracked worktree is clean and the ignored/untracked `PROJECT_MEMORY.md` persists.

**(Historical round entry — superseded by the Recovery-R1 acceptance entry below, which records that this
candidate was subsequently independently APPROVED and is now ACCEPTED / GRANTED / USE UNUSED.)**  The one-shot
ETB operational round was executed, consumed the accepted authorization exactly once, and
ended in `AUTHORIZATION_CONTROL_FAILURE`; a separate Recovery-R1 control-state recovery authorization
candidate now exists (not accepted, not effective, not executed).  What actually happened: the
pre-authorization prerequisites all passed; the authorization claim was created with the artifact's exact
frozen `Write-DevRelayOneShotClaim` writer, so `AUTHORIZATION_USE` became **1/1 CONSUMED** at the successful
`FileMode.CreateNew` of `docs/v0.3/evidence/ETB_AUTHORIZATION_USE.claim.tmp` and the published claim
(`docs/v0.3/evidence/ETB_AUTHORIZATION_USE.claim`, 372 bytes, SHA-256
`d84b428586f07a55a99f5b1391481d77763ec4ea697a40d1cec8aa0779613d4e`) carries the exact ordered schema with
`state = CONSUMED`; `docs/v0.3/evidence/etb-execution` was created exactly via
`[System.IO.Directory]::CreateDirectory`; the **exact frozen byte-level configuration transition completed
and verified** (pre-image `daaf7257…` / 1876 → post-image `b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf` / 1897 via
the unique 24-byte span, `xb` exclusive-create + write + flush + `os.fsync` + close + read-back +
`os.replace` + read-back, with the production reader resolving `""` before and
`http://127.0.0.1:4096` after); then the `CONFIG_ESTABLISHMENT.json` publication invocation **aborted
before entering any frozen primitive** because of **executor nonconformance** — an executor-authored,
non-frozen pre-write assertion miscompared the *current* (post-mutation) config hash against the *preimage*
hash and threw `PRE_SHA_NOT_PREIMAGE`.  No serialization ran, no temp was created, no bytes were written and
no move was attempted, so there is **no partial output** and the evidence directory is empty; per the frozen
rules (config-evidence "any failure → `AUTHORIZATION_CONTROL_FAILURE` / ETB NOT STARTED" plus §33.2
"post-authorization-claim failure … STOP, new authorization required, no reuse" and §12.2 "no
preparation-retry loophole exists") the invocation was **not retried**.  Final state of that round:
`AUTHORIZATION_CONTROL_FAILURE`; original authorization **SPENT / NOT REUSABLE**; `AUTHORIZATION USE = 1/1
CONSUMED`; original `ETB ATTEMPT = 0/1 NOT STARTED` (no `ETB_ATTEMPT_USE.claim` / `.tmp` was ever created);
**no ETB semantic result exists**; config left at the exact frozen post-image (**no rollback**); original
`CONFIG_ESTABLISHMENT = MISSING`; frozen oracle **NEVER ENTERED** (no `Get-NetTCPConnection`,
`Get-CimInstance`, `Add-Type`, P/Invoke, HTTP, `/doc`, `/session`, OpenCode start or ETB execution); no
commit was created (HEAD remained `14c5343`).  The independent control-failure review returned *CONFIRM
AUTHORIZATION_CONTROL_FAILURE STATE — NEW AUTHORIZATION REQUIRED* (**P0 = 0, P1 = 1, P2 = 0, P3 = 1**) and
separately concluded `STATE_MACHINE_FINAL_STATE = VALID`, `EXECUTION_PROCEDURE_FIDELITY = NONCONFORMANT`,
`CONFIG_EVIDENCE_SCHEMA = SOUND`, `FAILURE_CAUSE = EXECUTOR_NONCONFORMANCE`,
`ORIGINAL_AUTHORIZATION_REUSABLE = NO`, `CONFIG_MUTATION_REPLAY_ALLOWED = NO`.  A **new** artifact
`docs/v0.3/V03E_G0_5_PRE_ETB_RECOVERY_AUTHORIZATION.md` (not a revision — the accepted original
authorization artifact remains immutable) now records
`ETB CONTROL-STATE RECOVERY AUTHORIZATION = RECOVERY-R1 CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT
EXECUTED`: it is a **new authorization** with `recovery_authorization_commit` /
`recovery_authorization_sha256` to be bound only by a later independent approval, a **new and permanently
distinct claim namespace** (`ETB_RECOVERY_R1_AUTHORIZATION_USE.claim`(+`.tmp`) and
`ETB_RECOVERY_R1_ATTEMPT_USE.claim`(+`.tmp`)), the same frozen occupancy predicate
(`File.Exists` **or** `Directory.Exists`), a **byte-for-byte verbatim copy** of the accepted
`Write-DevRelayOneShotClaim` function (verified identical; the reviewer must diff the two functions), and
two separate 1-of-1 budgets whose consumption boundary is the successful `CreateNew` of the recovery
authorization claim temp.  Recovery **does not re-establish configuration**: it performs only read-only
verification of the existing post-image (`b5e4abab…` / 1897 / `http://127.0.0.1:4096`) and then
**recovers/publishes the missing original `CONFIG_ESTABLISHMENT.json`** as control evidence of the
transition that already occurred — so that file must retain the **original** authorization identity
(`64044fc…` / `511ab1e2…`), never the recovery identity, and the two provenance domains must not be
conflated.  The artifact reproduces the accepted `devrelay-etb-config-establishment-v1` schema as the exact
17 ordered fields with explicit values (no recovery-specific field, no added timestamp or comment), treats
`pre_config_sha256`/`expected_pre_config_sha256`/`pre_resolved_base_url` as **historical evidence inputs**
(`daaf7257…` / `daaf7257…` / `""`) that must **not** be validated against the current file, and freezes the
**absolute prohibition** on the `PRE_SHA_NOT_PREIMAGE` assertion and on any executor-authored pre-write
assertion, together with the exact `ConvertTo-Json -Depth 12 -Compress` / `UTF8Encoding(false)` / one-LF /
`CreateNew`+`Flush(true)`+read-back / two-argument `File.Move` publication rule and the rule that the
authorization/recovery layer must not touch the oracle's six frozen output paths.  Failure semantics are
frozen (`RECOVERY_AUTHORIZATION_CONTROL_FAILURE`, recovery use CONSUMED, recovery ETB attempt NOT STARTED,
no retry, no cleanup, no rollback, no original-claim deletion, a later Recovery-R2 would be required), as is
the boundary at which the one Recovery-R1 ETB attempt is consumed (successful `CreateNew` of the recovery
ETB claim temp, after successful `CONFIG_ESTABLISHMENT.json` publication) — which would be the **first
actual ETB attempt** — followed by entering the unchanged frozen oracle from its FIRST STEP.  Preserved
unchanged: `oracle_commit = 1c6c7cd…` / `oracle_sha256 = 01675fa7…` (recovery creates no new oracle); the
original spent claim and the empty `etb-execution` directory are never deleted or rewritten; the four new
recovery claim paths are untracked operational control-state artifacts; config is never rolled back to `""`;
Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE
CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER` (**the config now containing the endpoint does not
establish target binding**); `P6 = UNPROVEN / UNSATISFIED`; G0.5 **NOT CLOSED**; Case-C and v0.3-E
implementation `NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`; `adopt_completed_turn` **DISABLED**.  The current
authorization status is `ETB EXECUTION / CONFIGURATION AUTHORIZATION = SPENT / NOT REUSABLE / AUTHORIZATION
USE 1/1 CONSUMED / ETB ATTEMPT 0/1 NOT STARTED / ETB SEMANTIC RESULT NONE /
AUTHORIZATION_CONTROL_FAILURE`.  This Recovery-R1 design round performed **0** web/network access, **0**
endpoint queries, **0** `Get-NetTCPConnection` executions, **0** live `Get-CimInstance` queries, **0**
listener/process/port enumeration, **0** config mutations, **0** claim creations, **0** claim-path
directory creations, **0** `CONFIG_ESTABLISHMENT` publications, **0** OpenCode starts/restarts, **0** HTTP,
**0** `/doc`, **0** `/session`, **0** `Add-Type` executions, **0** P/Invoke executions, **0** ETB
executions, **0** SIC attempts, **0** Mode-B work, **0** provider/model calls, **0** G0.5 and **0** G1/G2
activity, and **0** runtime/test/dependency/version changes; the spent-authorization claim remains untracked
and unstaged, the git-ignored config remains uncommitted, and the ignored/untracked `PROJECT_MEMORY.md`
persists.

**The Recovery-R1 control-state recovery authorization has been INDEPENDENTLY ACCEPTED / GRANTED, while no
recovery action has occurred yet: recovery use UNUSED, recovery ETB attempt NOT STARTED, no Recovery-R1
claim, no `CONFIG_ESTABLISHMENT`, no oracle entry.**  The independent review — not executor self-approval —
returned **APPROVE V0.3-E ETB CONTROL-STATE RECOVERY AUTHORIZATION RECOVERY-R1** against
`3541c011cf92d9d66253989c5f576c2ad845ca33` (artifact
`docs/v0.3/V03E_G0_5_PRE_ETB_RECOVERY_AUTHORIZATION.md`, blob
`7fb1f28d427cc8c567491afc3137890f79b2bdb8bce88b4be2f63005824f3ab7`), confirming
`RECOVERY_CLAIM_WRITER = BYTE_IDENTICAL`, `CONFIG_MUTATION_REPLAY = FORBIDDEN`,
`CONFIG_ESTABLISHMENT_ATTESTATION = TRANSITION_FACT`, `DELAYED_PUBLICATION_PROVENANCE = SUFFICIENT`,
`CONTEMPORANEITY_SEMANTICS = TRUTHFUL`, and finding the design internally consistent, deterministic,
repository-self-sufficient, non-reusing of the spent original authorization and non-replaying of the
original config mutation, **with no blocking design finding**.  **Permanent Recovery-R1 provenance:**
`recovery_authorization_commit = 3541c011cf92d9d66253989c5f576c2ad845ca33` and
`recovery_authorization_sha256 = 7fb1f28d427cc8c567491afc3137890f79b2bdb8bce88b4be2f63005824f3ab7`; this
pair is immutable and must not be replaced by this acceptance-bookkeeping commit, by the Recovery-R1
operational HEAD, by an evidence commit, by a result-review bookkeeping commit or by any later HEAD — **the
bookkeeping commit created by this round is NOT `recovery_authorization_commit`**.  **Three distinct
immutable provenance domains now exist and none may replace another:** (A) the original
configuration-transition authorization `64044fc…` / `511ab1e2…` — preserved as `ORIGINAL ROUND-5
AUTHORIZATION = SPENT / NOT REUSABLE / AUTHORIZATION_CONTROL_FAILURE`, with Recovery-R1 never replacing or
reinterpreting it; (B) the Recovery-R1 publication/execution authorization `3541c01…` / `7fb1f28d…`; and
(C) the frozen ETB oracle `1c6c7cd…` / `01675fa7…`.  **Authoritative recovery status:**
`ETB CONTROL-STATE RECOVERY AUTHORIZATION = ACCEPTED / GRANTED / NOT EXECUTED / RECOVERY AUTHORIZATION USE
UNUSED / RECOVERY ETB ATTEMPT NOT STARTED`.  The accepted Recovery-R1 artifact remains an **immutable
accepted candidate object** whose construction-time header still reads RECOVERY-R1 CANDIDATE / NOT ACCEPTED
/ NOT EFFECTIVE / NOT EXECUTED — the established immutable-artifact + approval-record + active-status
pattern — so it was **not** edited by this bookkeeping; current status is represented only by this CHANGELOG
and `docs/v0.3/V03E_ACCEPTANCE.md`.  **Current filesystem/control state (verified):** original authorization
claim FINAL **OCCUPIED**, original authorization claim TEMP **ABSENT**, original ETB attempt claim TEMP and
FINAL **ABSENT**, and all four Recovery-R1 claim paths (`ETB_RECOVERY_R1_AUTHORIZATION_USE.claim`(+`.tmp`),
`ETB_RECOVERY_R1_ATTEMPT_USE.claim`(+`.tmp`)) **ABSENT** ⇒ `ORIGINAL AUTHORIZATION = SPENT`, `ORIGINAL ETB
ATTEMPT = 0/1 NOT STARTED`, `RECOVERY-R1 AUTHORIZATION USE = UNUSED`, `RECOVERY-R1 ETB ATTEMPT = NOT
STARTED`; no budget has yet been consumed.  **Current config state:** `opencode.base_url =
http://127.0.0.1:4096`, SHA-256 `b5e4ababf9b49f4e2bcdba1c1dd20fc320a0ec4aedbc98931f8595ff4416a8cf`, size
1897 — the exact frozen post-image (historical preimage `daaf7257…` / 1876 / `""` remains historical only);
config is not mutated by this round.  **`CONFIG_ESTABLISHMENT` state:** `docs/v0.3/evidence/etb-execution`
exists as a directory but is empty — `CONFIG_ESTABLISHMENT.json` and `.tmp` are ABSENT, therefore
`CONFIG_ESTABLISHMENT = MISSING`; the empty directory itself is not evidence publication.  **Recovery-R1
scope (by reference to the immutable artifact):** one Recovery-R1 authorization use → read-only
verification of the existing exact post-image → publication of the missing `CONFIG_ESTABLISHMENT` evidence
for the **original** configuration transition → one Recovery-R1 ETB attempt → entry into the unchanged
frozen ETB oracle.  Recovery-R1 must **not** mutate config, restore `""`, reapply the original config patch,
reuse the original authorization or its claim paths, start/restart OpenCode, perform HTTP, perform Mode-B
work or run G0.5.  **Delayed-publication provenance (independently accepted semantics):**
`CONFIG_ESTABLISHMENT_ATTESTATION = TRANSITION_FACT` — the recovered record describes the **original**
transition, so its embedded authorization provenance remains `64044fc…` / `511ab1e2…`, while Recovery-R1
authority to publish the delayed record is separately established by `3541c01…` / `7fb1f28d…` plus its
future Recovery-R1 claim; hence `DELAYED_PUBLICATION_PROVENANCE = SUFFICIENT` and
`CONTEMPORANEITY_SEMANTICS = TRUTHFUL`; this does **not** imply that the original authorization itself later
re-executes publication.  **Recovery-R1 namespace/budgets:** the four new claim paths are permanently
distinct (the original namespace stays reserved), and `RECOVERY_AUTHORIZATION_USE_BUDGET = 1/1` /
`RECOVERY_ETB_ATTEMPT_BUDGET = 1/1` are both unconsumed.  **Config replay prohibition:**
`CONFIG_MUTATION_REPLAY = FORBIDDEN` — Recovery-R1 operational execution may only verify the current
post-image SHA, size and resolved `base_url`, and must never restore `""`, re-run OLD→NEW, re-run the
original Python config writer, reuse the original config temp or perform `os.replace` on config.  **Original
control-failure history preserved (not erased by this approval):** *CONFIRM AUTHORIZATION_CONTROL_FAILURE
STATE — NEW AUTHORIZATION REQUIRED* (P0 = 0, P1 = 1, P2 = 0, P3 = 1) with
`STATE_MACHINE_FINAL_STATE = VALID`, `EXECUTION_PROCEDURE_FIDELITY = NONCONFORMANT`,
`CONFIG_EVIDENCE_SCHEMA = SOUND`, `FAILURE_CAUSE = EXECUTOR_NONCONFORMANCE`,
`ORIGINAL_AUTHORIZATION_REUSABLE = NO`, `CONFIG_MUTATION_REPLAY_ALLOWED = NO`.  **Preserved unchanged:**
Mode-B `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE
CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 **NOT CLOSED**;
Case-C and v0.3-E implementation `NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`; `adopt_completed_turn` **DISABLED**;
**Recovery-R1 approval is not target-binding evidence**.  **Next stage:** only after independent
confirmation of this Recovery-R1 acceptance bookkeeping may the next stage be the **RECOVERY-R1 OPERATIONAL
ROUND**, binding to exactly `3541c01…` / `7fb1f28d…` plus the original pair `64044fc…` / `511ab1e2…` and the
oracle pair `1c6c7cd…` / `01675fa7…`; **this bookkeeping round does not begin recovery**.  Authoritative
sequence: Round-5 authorization accepted → Round-5 acceptance bookkeeping accepted → original authorization
consumed → exact config mutation completed → `CONFIG_ESTABLISHMENT` publication failed due to executor
nonconformance → `AUTHORIZATION_CONTROL_FAILURE` → independent control-state review confirmed → original
authorization SPENT → Recovery-R1 design → **Recovery-R1 independently approved** → **Recovery-R1
acceptance bookkeeping (this round)** → independent Recovery-R1 bookkeeping confirmation → one Recovery-R1
authorization use → verify the exact existing post-image → recover/publish the missing
`CONFIG_ESTABLISHMENT` → consume one Recovery-R1 ETB attempt → frozen oracle once → independent ETB-result
review → only an independently accepted `ETB_SATISFIED` may permit Mode-B construction; no stage is skipped.
This bookkeeping round performed **0** config mutations, **0** claim creations, **0** claim deletions, **0**
`CONFIG_ESTABLISHMENT` publications, **0** endpoint queries, **0** listener/process enumerations, **0**
OpenCode starts/restarts, **0** HTTP, **0** ETB, **0** SIC, **0** Mode-B work, **0** G0.5, **0** G1/G2
activity and **0** runtime/test/dependency/version changes; the spent-authorization claim remains untracked
and unstaged, the git-ignored config remains uncommitted, and the ignored/untracked `PROJECT_MEMORY.md`
persists.

**The Recovery-R1 published candidate ETB result was REJECTED by independent review, and a new ETB
execution oracle R2 (execution-fidelity / output-namespace closure) design candidate now exists — still a
candidate: not accepted, not frozen, not executed.**  The independent final decision was **REJECT
RECOVERY-R1 PUBLISHED ETB RESULT — NO AUTHORITATIVE ETB SEMANTIC RESULT** (**P0 = 0, P1 = 1, P2 = 1,
P3 = 2**) with `RECOVERY_CONTROL_STATE = VALID`, `CONFIG_ESTABLISHMENT_RECOVERY = VALID`,
`ORACLE_IMPLEMENTATION_FIDELITY = NONCONFORMANT / INDETERMINATE`, `BLANKET_CATCH_CLASSIFICATION =
NONCONFORMANT`, `MANDATORY_STOP_FIDELITY = NONCONFORMANT`, `RESULT_ENCODING_FIDELITY = NONCONFORMANT`,
`RESULT_ARTIFACT_VALIDITY = VALID_WITH_NONBLOCKING_TEXT_DEFECT`, `PUBLISHED_RESULT_CLASSIFICATION =
UNRESOLVABLE`, `FROZEN_TAXONOMY_RESULT = INDETERMINATE DUE TO EXECUTION NONCONFORMANCE`,
`INDEPENDENT_RECLASSIFICATION_PERMITTED = NO` and `NEW_ETB_AUTHORIZATION_REQUIRED = YES`.  Therefore
`RECOVERY-R1 AUTHORIZATION = SPENT / NOT REUSABLE`, `RECOVERY-R1 ETB ATTEMPT = SPENT / NOT REUSABLE`,
`RECOVERY-R1 PUBLISHED ETB RESULT = REJECTED`, `AUTHORITATIVE ETB SEMANTIC RESULT = NONE`; the rejected
candidate is **not** relabelled as `ETB_UNSATISFIED`, as an authoritative `HARNESS_INVALID` or as
`ETB_SATISFIED`, and no independent reclassification is permitted.  Two blockers are recorded for why the
original oracle cannot simply be re-run: **(A) output namespace occupied** — the immutable Recovery-R1 finals
`docs/v0.3/evidence/etb-execution/ETB_EVIDENCE.json`, `…/MANIFEST.sha256` and
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT.md` are present, and the original oracle requires all six of its
output paths absent before a consumed attempt proceeds; **(B) executable implementation not frozen** — the
Recovery-R1 execution script was not preserved, so its actual executable bytes could not be compared against
the accepted oracle and a blanket catch materially changed classification.  This round therefore freezes a
**new oracle as two tracked artifacts**: the specification
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.md` and the **normative tracked executable**
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1`.  The script is **ASCII-only** (every byte ≤ `0x7F`,
mechanically verified; no BOM, LF only) and constructs the result template's em dash at runtime as
`$EmDash = [char]0x2014`, serialized through `[System.Text.UTF8Encoding]::new($false)` so the result artifact
carries the exact UTF-8 bytes `E2 80 94`, with a pre-publication byte check for those three bytes — this
eliminates the PowerShell-5.1 source-decoding ambiguity that corrupted the previous result artifact's first
line.  The listener taxonomy is now explicit and mechanically distinct in both the spec and the script:
`COMMAND_UNAVAILABLE` (cmdlet/module genuinely unavailable, decided by an explicit
`Get-Command -ErrorAction SilentlyContinue` availability branch **before** the query) → `HARNESS_INVALID`;
`QUERY_EXCEPTION`, `ZERO_ROWS`, `MULTIPLE_ROWS` and `FIELD_OR_PID_INVALID` → `ETB_UNSATISFIED`;
`ONE_VALID_ROW` → continue the target-binding chain; `NOT_REACHED` only before the listener stage or after an
earlier frozen terminal condition.  The exact listener query
(`@(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 4096 -State Listen -ErrorAction SilentlyContinue
-ErrorVariable qerr)`) has its own **narrow** try/catch, and a no-match condition surfaced as a terminating
exception is classified `ETB_UNSATISFIED`, never `HARNESS_INVALID`; **no blanket or outer catch may map
snapshot/listener exceptions to `HARNESS_INVALID`** — the only remaining catches are the narrow, typed ones
frozen by the original taxonomy (native invocation / `CloseHandle` false / `Add-Type` load /
config-reader failure → `HARNESS_INVALID`; process query, package manifest, hash read → `ETB_UNSATISFIED`),
plus a delimited evidence-publication stage that contains **no** listener, process, canonicalization, hash or
package logic.  The evidence schema keeps every accepted field and adds exactly **one** audit field,
`listener_probe_outcome`, placed between `checks` and `outcome`, whose value is bound to the published
semantic outcome by the frozen mapping (and re-verified on read-back, so a mismatch surfaces as the frozen
evidence-machinery `HARNESS_INVALID` rather than being executor-selectable); unobserved snapshot fields
remain truthful placeholders (`""` / `0`).  The output namespace is **new and disjoint**: evidence
`docs/v0.3/evidence/etb-execution-r2/ETB_EVIDENCE.json` (+`.tmp`), manifest
`docs/v0.3/evidence/etb-execution-r2/MANIFEST.sha256` (+`.tmp`) and result
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_R2.md` (+`.tmp`), all six required absent before publication
work (file **or** directory occupancy fails closed), with the old Recovery-R1 paths neither reused nor
inspected; publication order stays evidence → manifest → result **last** with the two-argument
`File.Move` and read-back verification, and the manifest covers only the R2 evidence file.  The executable
terminates immediately after final publication and verification — **no post-result `Get-Command`,
`Get-NetTCPConnection`, `Get-CimInstance`, endpoint/listener/process probe, diagnostic, repair,
reclassification or extra evidence collection**.  Identity model: after independent acceptance,
`oracle_r2_commit` (the accepted commit containing both files), `oracle_r2_script_sha256` and
`oracle_r2_spec_sha256` are immutable and must be bound by the future Recovery-R2 authorization; the
executor must run the tracked `.ps1` directly (no extraction from Markdown, no temporary script, no
translation, no wrapper, no injected assertions) via the frozen invocation
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File "docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1"`.
Static validation performed in this design round: **parser-only** syntax validation of the tracked script
(PowerShell AST parser: **0 parse errors**, 4638 tokens), an ASCII-byte sweep (**0 non-ASCII bytes**), a
structural audit of every `catch`/`throw`/`HARNESS_INVALID`/`ETB_UNSATISFIED` branch, and hash computation —
**the operational main path was not executed, no listener/process command was run and the endpoint was not
contacted**.  Current statuses: `ETB EXECUTION ORACLE-R2 = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT
EXECUTED`; `RECOVERY-R1 AUTHORIZATION = SPENT / NOT REUSABLE`; `RECOVERY-R1 ETB ATTEMPT = SPENT / NOT
REUSABLE`; `RECOVERY-R1 PUBLISHED ETB RESULT = REJECTED`; `AUTHORITATIVE ETB SEMANTIC RESULT = NONE`;
`NEW_ETB_AUTHORIZATION_REQUIRED = YES`.  No Recovery-R2 authorization and no Recovery-R2 claim namespace
exist; config remains the exact post-image (`b5e4abab…` / 1897 / `http://127.0.0.1:4096`) and
`CONFIG_ESTABLISHMENT = VALID / PRESENT`; the Recovery-R1 evidence/result artifacts and all claims remain
untouched historical artifacts; Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE
ENDPOINT NOT ESTABLISHED / PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`; `P6 = UNPROVEN /
UNSATISFIED`; G0.5 **NOT CLOSED**; Case-C and v0.3-E implementation `NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`;
`adopt_completed_turn` **DISABLED**.  This design round performed **0** config mutations, **0** claim
creations, **0** R2 directory or output creations, **0** Oracle-R2 executions, **0** old-oracle executions,
**0** endpoint queries, **0** `Get-NetTCPConnection` listener queries, **0** live `Get-CimInstance` queries,
**0** listener/process/port enumeration, **0** P/Invoke executions, **0** OpenCode starts/restarts, **0**
HTTP, **0** ETB executions, **0** SIC, **0** Mode-B work, **0** G0.5 and **0** G1/G2 activity, and **0**
runtime/test/dependency/version changes; the ignored/untracked `PROJECT_MEMORY.md` persists.

**The Oracle-R2 candidate `6d252a9` received `REQUEST_CHANGES` and was superseded by a narrow corrective
design round.**  The independent review issued *REQUEST_CHANGES — V0.3-E ETB EXECUTION ORACLE-R2* with
severity **P0 = 0, P1 = 1, P2 = 2, P3 = 5**, so that candidate was never accepted, never frozen and never
executed; it remains historical and is not relabelled as any semantic ETB result.  One blocking P1 was found —
**config-reader invocation fidelity**: the frozen oracle requires the config-reader subprocess to run with
`PYTHONPATH=<repo>/src`, and the rejected script invoked `python -c ... 'D:\DevRelay'` with no `PYTHONPATH`
established, which in a src-layout/non-installed environment could manufacture an artificial import failure
and turn a reachable result into `config_reader_failure` → `HARNESS_INVALID`, materially changing reachable
oracle behaviour.  Two blocking P2s were found: **evidence schema identity ambiguity** (the 16-field Oracle-R2
contract added `listener_probe_outcome` while retaining the closed original identifier `devrelay-etb-v1`) and
an **executable byte-identity design deadlock** (the accepted script blob is the 28024-byte LF sequence
`3e2cc721…`, while the canonical worktree under `* text=auto` with `core.autocrlf=true` materializes
28564-byte CRLF bytes `245e346c…`, and the rejected candidate froze no deterministic mechanism that lets a
canonical checkout contain the accepted executable bytes, so the accepted sequence would deterministically
deadlock before a Recovery-R2 authorization could be consumed).  Five P3s were closed as well.

**The corrective design round changed exactly five tracked paths** (`.gitattributes`, `CHANGELOG.md`,
`docs/v0.3/V03E_ACCEPTANCE.md`, `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.md`,
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1`) and no sixth tracked path.  **P1 remediation:** the
tracked script now deterministically establishes `PYTHONPATH = <repo>/src` for the config-reader subprocess —
capturing any prior process-level `PYTHONPATH` first, assigning exactly `<repo>/src` (never merged with,
prepended to or appended to pre-existing content), invoking the byte-identical frozen reader source with the
frozen repository root as its single repository argument, and restoring the prior state in a deterministic
`finally` block (restoring **absence**, not an invented empty value, when no prior `PYTHONPATH` existed) — so
the subprocess semantics are exactly equivalent to the original frozen oracle's
`PYTHONPATH=<repo>/src python -c "<frozen reader>" "<repo>"` shape.  The hard-coded `D:\DevRelay` is gone: the
frozen repository root is derived from the tracked script location, and config-reader stderr stays suppressed
and never participates in classification (classification depends only on the frozen subprocess exit code and
the returned reader value).  **P2-A remediation:** the Oracle-R2 evidence contract has the distinct identity
**`devrelay-etb-v1-r2`** (written and asserted on read-back), while `devrelay-etb-v1` remains only the
historical original closed schema of the Recovery-R1 evidence and is never reinterpreted.  **P2-B
remediation:** `.gitattributes` gains exactly **one** narrow rule —
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1 text eol=lf` (no repository-wide `*.ps1` rule, no other
text policy changed, `core.autocrlf` untouched), so a normal canonical checkout materializes the normative
executable as LF bytes independently of the local `core.autocrlf=true`, `git check-attr` resolves to
`text: set` / `eol: lf`, and the worktree bytes equal the committed blob bytes byte for byte — the accepted
fail-closed byte-identity gate is preserved unchanged and **no future ad-hoc repair stage is frozen**.  **P3
remediations:** `listener_probe_outcome` now has frozen total S0/S1 semantics (the published value is the
listener probe outcome of the last actually executed snapshot probe that determines or contributes to the
published terminal result, so "S0 or S1?" is not executor-selectable); the ambiguous section reference now
explicitly names the **original frozen oracle's §15.2** continuity comparison field set rather than this
specification's own local §15.2; publication failure emits exactly the constant stdout line
`ORACLE_R2_PUBLICATION_FAILURE` with no exception message, stack, provider text or environment data, and the
specification's frozen stdout contract now lists every possible Oracle-R2 stdout line; and `RESULT_R2` final
bytes are explicitly required to be byte-identical to the already validated result temp bytes, so all frozen
semantic fields are preserved by byte identity with no second semantic parser and no post-result probe.  The
listener taxonomy, the narrow typed catch structure, the output namespace, the six-path absence precondition,
the ASCII-only source with the runtime `[char]0x2014` construction through `UTF8Encoding(false)`, the
target-binding chain, canonicalization, hash/version checks, S0/S1 continuity, publication order, mandatory
stop, no HTTP, no OpenCode start/restart, no retry and no fallback are all **preserved without regression**.
Static validation for the corrective candidate: PowerShell **parser-only** validation with **0 parse errors**,
**0 non-ASCII bytes**, no BOM, LF only with **CR count = 0**, a `git check-attr` LF-contract confirmation,
residue scans for the corrected defects, and a committed-blob-versus-worktree byte comparison — **the
operational main path was not executed, no listener/process command was run and the endpoint was not
contacted**.  Current statuses: `ETB EXECUTION ORACLE-R2 (corrective candidate) = DESIGN CANDIDATE / NOT
ACCEPTED / NOT FROZEN / NOT EXECUTED`; `PREVIOUS ORACLE-R2 CANDIDATE 6d252a9 = REQUEST_CHANGES / SUPERSEDED AS
A CANDIDATE`; `RECOVERY-R1 AUTHORIZATION = SPENT / NOT REUSABLE`; `RECOVERY-R1 ETB ATTEMPT = SPENT / NOT
REUSABLE`; `RECOVERY-R1 PUBLISHED ETB RESULT = REJECTED`; `AUTHORITATIVE ETB SEMANTIC RESULT = NONE`;
`NEW_ETB_AUTHORIZATION_REQUIRED = YES`; and **no Recovery-R2 authorization and no Recovery-R2 claim namespace
exist**.  Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED /
PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 **NOT
CLOSED**; Case-C and v0.3-E implementation `NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`; `adopt_completed_turn`
**DISABLED**.  This corrective round performed **0** config mutations, **0** claim creations, **0** R2
directory or output creations, **0** Oracle-R2 executions, **0** old-oracle executions, **0** endpoint
queries, **0** `Get-NetTCPConnection` listener queries, **0** live `Get-CimInstance` queries, **0**
listener/process/port enumeration, **0** P/Invoke executions, **0** OpenCode starts/restarts, **0** HTTP,
**0** ETB executions, **0** SIC, **0** Mode-B work, **0** G0.5 and **0** G1/G2 activity, and **0**
runtime/test/dependency/version changes; the ignored/untracked `PROJECT_MEMORY.md` persists.

**The corrective Oracle-R2 candidate was independently approved, so Oracle-R2 is now `ACCEPTED / FROZEN /
NOT EXECUTED`.**  The independent review issued *APPROVE V0.3-E ETB EXECUTION ORACLE-R2 CORRECTIVE R2* with
severity **P0 = 0, P1 = 0, P2 = 0, P3 = 2**, which closes all three prior blockers — **P1 config-reader
invocation fidelity = RESOLVED**, **P2 evidence schema identity = RESOLVED** and **P2 executable byte-identity
deadlock = RESOLVED** — and leaves only two **non-blocking** P3 findings.  The permanently accepted Oracle-R2
identity is therefore `oracle_r2_commit = dfb78f34d919e8c9863a8398fb4f63ee301167bc`,
`oracle_r2_spec_sha256 = 5e9221e3950af6ec3e0612c4d962562c33e761899dfd6af42d10f5a9895f9f2f` and
`oracle_r2_script_sha256 = 22c5fbd61da609e6cc39e973be6030d4c360019ed1f56e69ca45f92fa1689c17`; these three
values together are the accepted Oracle-R2 identity, they are immutable, this acceptance-bookkeeping commit
does **not** replace `oracle_r2_commit`, and no future bookkeeping HEAD, Recovery-R2 authorization commit,
Recovery-R2 operational HEAD or ETB result-review commit may substitute for them.  Active Oracle-R2 status is
converged to **`ETB EXECUTION ORACLE-R2 = ACCEPTED / FROZEN / NOT EXECUTED`**, with `EXECUTABLE IDENTITY =
FROZEN`, `EXECUTION AUTHORITY = NOT GRANTED` and `RECOVERY-R2 AUTHORIZATION = DOES NOT EXIST`: **acceptance of
Oracle-R2 is design/oracle acceptance only and is NOT authorization to execute it.**  The accepted Oracle-R2
spec and script bytes are **frozen** and were **not** modified by this round; their own construction-time
headers may still read as design-candidate text, because acceptance is represented through the independent
approval record and the active authoritative status surfaces, following the established immutable-artifact +
approval-record pattern.  Historical provenance is preserved unchanged: candidate
`6d252a9466d768bb6345aad6c0c7a04562b8845c` = **REQUEST_CHANGES / SUPERSEDED AS A CANDIDATE / NEVER ACCEPTED
/ NEVER EXECUTED** — its `REQUEST_CHANGES` verdict is history only and is **not** the current Oracle-R2
verdict.  **No ETB semantic result follows from this acceptance:** `RECOVERY-R1 PUBLISHED ETB RESULT =
REJECTED`, `AUTHORITATIVE ETB SEMANTIC RESULT = NONE`, `RECOVERY-R1 AUTHORIZATION = SPENT / NOT REUSABLE`,
`RECOVERY-R1 ETB ATTEMPT = SPENT / NOT REUSABLE` and `NEW_ETB_AUTHORIZATION_REQUIRED = YES` are all preserved
exactly.  Recovery-R2 is explicitly **`NOT DESIGNED / NOT ACCEPTED / DOES NOT EXIST`**, its claim namespace is
**NOT CREATED** and its ETB attempt is **NOT STARTED**; no claim path was invented and no Recovery-R2
authorization was designed.  Mode-B remains `BLOCKED / NOT RUN`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 **NOT
CLOSED**; Case-C and v0.3-E implementation **NOT AUTHORIZED**; `G1`/`G2` `NOT RUN`;
`adopt_completed_turn` **DISABLED** — Oracle-R2 acceptance alone establishes neither target binding nor
`ETB_SATISFIED`.  **Non-blocking P3 recording (preserved, not promoted, not erased):** the review recorded
**P3 = 2 non-blocking**, and one explicitly noted residual edge case concerns Windows PowerShell
environment-variable semantics for a prior `PYTHONPATH` that is conceptually "present but empty"; the review
determined this has no result-classification effect and is non-blocking, and the accepted Oracle-R2 script was
**not** modified to address it in this round.  Authoritative sequence: Recovery-R1 rejected → Oracle-R2
initial candidate `6d252a9` → independent REQUEST_CHANGES → corrective Oracle-R2 candidate `dfb78f34` →
independent APPROVE → **Oracle-R2 acceptance bookkeeping (this round)** → independent acceptance-bookkeeping
confirmation → Recovery-R2 authorization design → independent Recovery-R2 authorization review → Recovery-R2
acceptance bookkeeping → independent bookkeeping confirmation → exactly one Recovery-R2 operational ETB
attempt → independent ETB-result review → only an independently accepted `ETB_SATISFIED` may permit Mode-B
oracle construction; **no stage may be skipped**.  This bookkeeping round performed **0** Oracle-R2
executions, **0** old-oracle executions, **0** claim creations, **0** claim deletions, **0** R2 output
creations, **0** R2 directory creations, **0** endpoint inspections, **0** listener queries, **0** process
queries, **0** operational P/Invoke, **0** OpenCode starts/restarts, **0** HTTP, **0** SIC, **0** Mode-B,
**0** G0.5, **0** G1/G2 activity, **0** config mutations, **0** R1 artifact mutations and **0**
runtime/test/dependency/version changes; the ignored/untracked `PROJECT_MEMORY.md` persists.

**A Recovery-R2 one-shot ETB execution authorization design candidate was created.**  The independent review
issued *APPROVE V0.3-E ETB EXECUTION ORACLE-R2 ACCEPTANCE BOOKKEEPING*, making
`9b17912a8b4bd6c87aa45eefc97a73eb3d22db34` the authoritative bookkeeping baseline (explicitly **not** the
Oracle-R2 provenance), and this round designs — as documentation only — the authorization under which exactly
**one** future ETB attempt may run the already accepted tracked Oracle-R2 executable.  The new artifact
`docs/v0.3/V03E_G0_5_PRE_ETB_RECOVERY_R2_AUTHORIZATION.md` is a **DESIGN CANDIDATE / NOT ACCEPTED / NOT
GRANTED / NOT EXECUTED**: it grants no execution authority today, creates no claim, mutates no configuration,
performs no endpoint/listener/process probe and does not enter Oracle-R2.  It binds permanently to the accepted
Oracle-R2 triple (`oracle_r2_commit = dfb78f34d919e8c9863a8398fb4f63ee301167bc`, `oracle_r2_spec_sha256 =
5e9221e3950af6ec3e0612c4d962562c33e761899dfd6af42d10f5a9895f9f2f`, `oracle_r2_script_sha256 =
22c5fbd61da609e6cc39e973be6030d4c360019ed1f56e69ca45f92fa1689c17`) plus the future independently accepted
`recovery_r2_authorization_commit` / `recovery_r2_authorization_sha256` pair.  It freezes a **new, permanently
distinct** claim namespace (four exact paths — `docs/v0.3/evidence/ETB_RECOVERY_R2_AUTHORIZATION_USE.claim`
(+`.tmp`) and `docs/v0.3/evidence/ETB_RECOVERY_R2_ATTEMPT_USE.claim` (+`.tmp`)), the accepted file-or-directory
occupancy predicate, two **new closed 7-field schemas** (`devrelay-etb-recovery-r2-authorization-use-v1` and
`devrelay-etb-recovery-r2-attempt-use-v1`, each ending in `state = CONSUMED` with no timestamp, hostname, PID,
operator, comment or extra field), the exact `Write-DevRelayRecoveryR2OneShotClaim` PowerShell/.NET writer
(exclusive `CreateNew` consumption point, exactly one LF, `UTF8Encoding(false)`, byte read-back, two-argument
no-overwrite `File.Move`, and TEMP-absent plus FINAL-occupied-as-file post-publication requirements), a **1/1**
authorization budget and a **1/1** ETB-attempt budget, and a complete 16-item read-only PRE-* checklist
(baseline HEAD, branch, accepted spec/script blob hashes, worktree byte identity, `text: set` / `eol: lf`, clean
tracked worktree, config hash/size/resolved value, `CONFIG_ESTABLISHMENT` hash, three historical claim
witnesses, all four new claim paths ABSENT, the accepted authorization artifact identity, and the
not-yet-consumed confirmations) with STOP-before-consumption on any failure.  It also freezes the boundary
rules that keep the oracle's own contract intact: **no authorization-layer precheck of the six Oracle-R2 output
paths**, **no target/listener/process pre-probe**, no config mutation and no `CONFIG_ESTABLISHMENT`
republication; the exact oracle entry invocation
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File "docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_R2.ps1"`
with no parameters, wrapper, generated or extracted script, alternate PowerShell implementation, environment
mutation, or pre/post-oracle helper; **no repeat of the byte-identity check after consumption** (it is a
pre-consumption PRE-* condition, and no permitted intervening step may modify the script); oracle-exclusive
ownership of target binding, the listener taxonomy, S0/S1 continuity, the evidence schema, classification,
publication and the mandatory stop, with any result **candidate-only** until independent ETB-result review; the
post-oracle stop rule (no rerun, no probe, no diagnostics, no repair, no reclassification, no retry of
publication, no HTTP, no SIC, no Mode-B, no G0.5/G1/G2); and the no-second-attempt rule (authorization writer
max **1**, attempt writer max **1**, Oracle-R2 invocation max **1**; no retry, no repair-and-rerun, no alternate
target/port/executable, no old-Oracle invocation, no `Mode P → Mode L` transition, no fallback).  Two explicit
control-failure classifications are frozen and are **not** ETB semantic results:
`RECOVERY_R2_AUTHORIZATION_CONTROL_FAILURE` (authorization 1/1 consumed, attempt 0/1 not started, result NONE)
and the post-attempt-claim failure state (authorization 1/1 consumed, attempt 1/1 consumed, result NONE,
Oracle-R2 not entered).  Static validation of the artifact: PowerShell **parser-only** validation of the
embedded writer with **0 parse errors** (605 tokens), byte-verified LF-only and BOM-free encoding, and
structural anchor plus PRE-* presence checks.  Historical state is preserved exactly: original Round-5
authorization `SPENT / NOT REUSABLE` with its claim FINAL OCCUPIED at `d84b4285…` and its ETB attempt `0/1
never started` (TEMP and FINAL ABSENT, still not reusable because the parent authorization is spent);
Recovery-R1 authorization `SPENT / NOT REUSABLE` (`8876bcc6…`); Recovery-R1 ETB attempt `SPENT / NOT REUSABLE`
(`5f1e9721…`); `AUTHORITATIVE ETB SEMANTIC RESULT = NONE`; config remains the exact post-image (`b5e4abab…` /
1897 / `http://127.0.0.1:4096`); `CONFIG_ESTABLISHMENT = VALID / PRESENT` (`ea9fc2bc…`).  Active statuses are
converged to `ETB EXECUTION ORACLE-R2 = ACCEPTED / FROZEN / NOT EXECUTED`, `EXECUTION AUTHORITY = NOT
GRANTED`, `RECOVERY-R2 AUTHORIZATION = DESIGN CANDIDATE / NOT ACCEPTED / NOT GRANTED / NOT EXECUTED`,
`RECOVERY-R2 AUTHORIZATION USE = UNUSED / 0 OF 1`, `RECOVERY-R2 ETB ATTEMPT = NOT STARTED / 0 OF 1` and
`RECOVERY-R2 CLAIM NAMESPACE = DEFINED BY CANDIDATE / NO CLAIM CREATED`.  Mode-B remains `BLOCKED / NOT RUN`;
`P6 = UNPROVEN / UNSATISFIED`; G0.5 **NOT CLOSED**; Case-C and v0.3-E implementation **NOT AUTHORIZED**;
`G1`/`G2` `NOT RUN`; `adopt_completed_turn` **DISABLED**.  This design round performed **0** Oracle-R2
executions, **0** old-oracle executions, **0** claim creations, **0** claim deletions, **0** R2 output
creations, **0** R2 directory creations, **0** endpoint inspections, **0** listener queries, **0** process
queries, **0** operational P/Invoke, **0** OpenCode starts/restarts, **0** HTTP, **0** `/doc` or `/session`,
**0** provider/model calls, **0** SIC, **0** Mode-B, **0** G0.5, **0** G1/G2 activity, **0** config mutations,
**0** R1 artifact mutations and **0** runtime/test/dependency/version changes; the ignored/untracked
`PROJECT_MEMORY.md` persists.

**The Recovery-R2 authorization candidate `af3ec9b7` received `REQUEST_CHANGES` and was corrected for a PRE-1
lifecycle contradiction.**  The independent review issued *REQUEST_CHANGES — V0.3-E RECOVERY-R2 ONE-SHOT ETB
EXECUTION AUTHORIZATION* with severity **P0 = 0, P1 = 1, P2 = 0, P3 = 1**, so that candidate is
**REQUEST_CHANGES / SUPERSEDED AS A CANDIDATE / NEVER ACCEPTED / NEVER GRANTED / NEVER EXECUTED** and remains
immutable historical provenance.  The blocking P1 was a **PRE-1 operational-HEAD lifecycle contradiction /
deterministic design deadlock**: the rejected artifact froze PRE-1 as an exact equality with the earlier
bookkeeping baseline `9b17912…` while the same artifact required the lifecycle *authorization design →
independent approval → authorization acceptance bookkeeping → independent bookkeeping confirmation →
operational attempt*, so a conformant operational HEAD must be a descendant of the accepted
authorization-design commit and can never equal that earlier baseline; the rejected PRE-1 also conflicted with
PRE-14, because returning HEAD to `9b17912…` would remove the authorization artifact that is introduced only
after it (independent verdict `PRE1_LIFECYCLE_BINDING = CONTRADICTORY`,
`RECOVERY_R2_OPERATIONAL_REACHABILITY = DESIGN_DEADLOCK`, `SEQUENCE_PRECONDITION_CONSISTENCY = FAIL`).  This
corrective round changes exactly three tracked paths — the authorization artifact, `CHANGELOG.md` and
`docs/v0.3/V03E_ACCEPTANCE.md` — and no fourth.  **P1 remediation:** the design-construction baseline and the
future operational-HEAD predicate are now separated — `9b17912…` is retained **only** as the RECOVERY-R2
AUTHORIZATION DESIGN-CONSTRUCTION BASELINE and as the historical predecessor bookkeeping baseline, is
explicitly **not** the future operational HEAD requirement, and must never appear in any future operational
`PRE-*` condition as an exact HEAD requirement; PRE-1 is replaced by a **lifecycle-correct structural binding**
requiring the operational HEAD to be a **single-parent** commit whose parent is exactly the accepted
`recovery_r2_authorization_commit`, whose sole tracked delta is exactly `M CHANGELOG.md` +
`M docs/v0.3/V03E_ACCEPTANCE.md` with no third path, whose authorization artifact bytes are byte-identical to
the accepted blob and hash to the accepted `recovery_r2_authorization_sha256`, and whose active bookkeeping
surfaces state `RECOVERY-R2 AUTHORIZATION = ACCEPTED / FROZEN / NOT EXECUTED` bound to that accepted pair —
structurally identifying the future bookkeeping commit **without** requiring its not-yet-known hash, with no
reset, no detached checkout, no alternate worktree procedure, no symbolic "latest commit" and no
executor-selected descendant.  The future acceptance-bookkeeping contract is frozen now (exactly one
single-parent child of the accepted design commit, exactly the two bookkeeping files, none of the protected
artifacts touched), the `PRE1_PRE14_COMPATIBILITY = REQUIRED` relationship is made explicit and mutually
satisfiable in the same canonical worktree, and `SEQUENCE_PRECONDITION_CONSISTENCY` is added as an explicit
invariant.  Static proof recorded on the current topology: the authorization artifact resolves to a `blob` at
`af3ec9b7` but **does not exist** at `9b17912…` (`git cat-file -t` → exit `128`), and the bookkeeping shape
precedent `9b17912` is itself single-parent with exactly the two-file delta — hence
`PRE1_LIFECYCLE_BINDING = STRUCTURALLY_SATISFIABLE` and `PRE1_PRE14_COMPATIBILITY = PASS`.  The non-blocking P3
(post-Oracle static-read boundary bounded but not exhaustively enumerated) is closed by replacing the vague
phrase with an **exact closed 12-item read list** plus an explicit forbidden-operation list after Oracle
return, and by freezing that post-Oracle reads exist only to inventory already-produced artifacts, bind hashes,
record one-shot claim state, record repository/config preservation and produce the execution report — never to
decide a different ETB semantic result, change the Oracle outcome, repair evidence, infer target state beyond
Oracle evidence or create new target-binding evidence.  Everything else is **preserved unchanged**: the
authorization provenance model (the accepted design commit, never the bookkeeping HEAD), the four-path claim
namespace, both closed 7-field claim schemas, the `Write-DevRelayRecoveryR2OneShotClaim` writer and its
`CreateNew` consumption semantics, the 1/1 + 1/1 budgets, PRE-2 … PRE-16, the no-Oracle-output-precheck rule,
the no-target-pre-probe rule, the post-authorization control boundary, the exact Oracle-R2 invocation, the
no-repeat identity check after consumption, Oracle-exclusive result ownership with candidate-only authority,
the no-second-attempt rule and the failure classifications.  The authorization lifecycle state model is now
frozen explicitly: `DESIGN CANDIDATE / NOT ACCEPTED / NOT GRANTED / NOT EXECUTED` today; after a future
independently approved acceptance-bookkeeping round `ACCEPTED / FROZEN / NOT EXECUTED` with `EXECUTION
AUTHORITY = GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY`; authorization use `UNUSED / 0 OF 1` and
ETB attempt `NOT STARTED / 0 OF 1` until their respective TEMP `CreateNew` succeeds; independent bookkeeping
confirmation still required before any operational consumption; and authority is **not** marked granted in this
design round.  Static validation: PowerShell parser-only re-validation of the embedded writer with **0 parse
errors**, LF-only and BOM-free encoding, unchanged claim paths and schemas, and the verified absence of the
rejected literal operational condition `HEAD == 9b17912…` from `PRE-*` semantics (historical references to
`9b17912…` appear only where explicitly marked as design-construction or predecessor history).  Active
statuses: `ETB EXECUTION ORACLE-R2 = ACCEPTED / FROZEN / NOT EXECUTED`; `EXECUTION AUTHORITY = NOT GRANTED`;
`PREVIOUS RECOVERY-R2 CANDIDATE af3ec9b7 = REQUEST_CHANGES / SUPERSEDED / NEVER ACCEPTED / NEVER GRANTED /
NEVER EXECUTED`; `RECOVERY-R2 AUTHORIZATION (corrective) = DESIGN CANDIDATE / NOT ACCEPTED / NOT GRANTED / NOT
EXECUTED`; `RECOVERY-R2 AUTHORIZATION USE = UNUSED / 0 OF 1`; `RECOVERY-R2 ETB ATTEMPT = NOT STARTED / 0 OF
1`; `RECOVERY-R2 CLAIM NAMESPACE = DEFINED / NO CLAIM CREATED`; `AUTHORITATIVE ETB SEMANTIC RESULT = NONE`.
Mode-B remains `BLOCKED / NOT RUN`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 **NOT CLOSED**; Case-C and v0.3-E
implementation **NOT AUTHORIZED**; `G1`/`G2` `NOT RUN`; `adopt_completed_turn` **DISABLED**; config remains the
exact post-image (`b5e4abab…` / 1897 / `http://127.0.0.1:4096`); `CONFIG_ESTABLISHMENT = VALID / PRESENT`
(`ea9fc2bc…`); the accepted Oracle-R2 triple and all R1 artifacts are untouched.  This corrective round
performed **0** Oracle-R2 executions, **0** claim creations or deletions, **0** R2 output or directory
creations, **0** endpoint/listener/process probes, **0** HTTP, **0** SIC, **0** Mode-B, **0** G0.5, **0**
G1/G2 activity, **0** config mutations and **0** runtime/test/dependency/version changes; the
ignored/untracked `PROJECT_MEMORY.md` persists.

**The corrective Recovery-R2 authorization design was independently approved, so the Recovery-R2 one-shot ETB
execution authorization is now `ACCEPTED / FROZEN / NOT EXECUTED` (acceptance bookkeeping only; no claim
created, nothing consumed).**  The independent design review issued *APPROVE V0.3-E RECOVERY-R2 ONE-SHOT ETB
EXECUTION AUTHORIZATION CORRECTIVE R1* with severity **P0 = 0, P1 = 0, P2 = 0, P3 = 1**, which resolved both
prior findings — **P1 PRE-1 lifecycle contradiction = RESOLVED** and **P3 post-Oracle read-boundary ambiguity
= RESOLVED** — and leaves exactly one **non-blocking** P3: the accepted artifact does not contain one
standalone sentence stating that the independent bookkeeping confirmation creates no commit, although the
accepted direct-child topology structurally requires confirmation to be review-only; the frozen authorization
artifact was **not** modified for it, and this status/bookkeeping layer records the missing statement
explicitly instead.  The permanently accepted immutable Recovery-R2 authorization identity is
`recovery_r2_authorization_commit = 02bef765f74d7349c592138b35280b8b51995a5d` and
`recovery_r2_authorization_sha256 = 91917bb55cc5b59a811c6a5f7bcbc3bf48ffa4f5688c379914912fe6f092d4ab` — the
accepted **authorization-design** commit/blob pair; this acceptance-bookkeeping commit explicitly does **not**
replace `recovery_r2_authorization_commit`, and no later bookkeeping-confirmation review, operational HEAD or
ETB-result review may substitute for it.  The permanently accepted Oracle-R2 identity is unchanged
(`oracle_r2_commit = dfb78f34d919e8c9863a8398fb4f63ee301167bc`, `oracle_r2_spec_sha256 =
5e9221e3950af6ec3e0612c4d962562c33e761899dfd6af42d10f5a9895f9f2f`, `oracle_r2_script_sha256 =
22c5fbd61da609e6cc39e973be6030d4c360019ed1f56e69ca45f92fa1689c17`); the accepted spec/script bytes were
re-verified byte-identical at this baseline, the worktree script still equals its accepted blob, and
`git check-attr text eol` still resolves the normative executable to `text: set` / `eol: lf`.  Active status
transition: **`RECOVERY-R2 AUTHORIZATION = ACCEPTED / FROZEN / NOT EXECUTED`** with **`EXECUTION AUTHORITY =
GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY`** and, simultaneously and mandatorily,
**`OPERATIONAL CONSUMPTION = BLOCKED PENDING INDEPENDENT BOOKKEEPING CONFIRMATION`** — the design is accepted
and its one-shot authority is defined, but no claim may be consumed until this bookkeeping commit itself
receives independent confirmation.  Budgets are preserved exactly:
`RECOVERY-R2 AUTHORIZATION USE = UNUSED / 0 OF 1` and `RECOVERY-R2 ETB ATTEMPT = NOT STARTED / 0 OF 1`
(consumption is defined **only** by the successful `CreateNew` of the respective TEMP claim; nothing is
consumed).  The claim namespace is **`ACCEPTED / FROZEN / NO CLAIM CREATED`**; the four exact accepted paths
(`docs/v0.3/evidence/ETB_RECOVERY_R2_AUTHORIZATION_USE.claim` (+`.tmp`) and
`docs/v0.3/evidence/ETB_RECOVERY_R2_ATTEMPT_USE.claim` (+`.tmp`)) were read-only verified still ABSENT, and
`docs/v0.3/evidence/etb-execution-r2/` does not exist.  **Independent authorization bookkeeping confirmation =
REVIEW-ONLY / NO COMMIT IS CREATED** — after confirmation the operational HEAD remains exactly this
acceptance-bookkeeping child commit, and no separate confirmation commit is ever created.  This bookkeeping
commit itself satisfies the accepted structural contract: its parent is exactly
`02bef765f74d7349c592138b35280b8b51995a5d` and its exact tracked delta is exactly `M CHANGELOG.md` +
`M docs/v0.3/V03E_ACCEPTANCE.md` with no third tracked path, so the accepted authorization artifact remains
byte-identical and this new HEAD is the structural HEAD a future operational PRE-1 validates:
`PRE1_LIFECYCLE_BINDING = STRUCTURALLY SATISFIABLE`, `PRE1_PRE14_COMPATIBILITY = PASS`,
`SEQUENCE_PRECONDITION_CONSISTENCY = PASS`.  `PRE-* OPERATIONAL EVALUATION = NOT RUN` and `RECOVERY-R2
AUTHORIZATION CONSUMPTION = NOT STARTED` — the actual PRE-1..PRE-16 operational gate runs only in the future
operational round after independent bookkeeping confirmation.  Preserved exactly: candidate `af3ec9b7…` =
REQUEST_CHANGES / SUPERSEDED AS A CANDIDATE / NEVER ACCEPTED / NEVER GRANTED / NEVER EXECUTED (history not
rewritten); `02bef765…` = ACCEPTED AUTHORIZATION DESIGN / FROZEN / NOT EXECUTED (the bookkeeping HEAD is never
called the authorization-design commit); `ETB EXECUTION ORACLE-R2 = ACCEPTED / FROZEN / NOT EXECUTED` (never
executed); `AUTHORITATIVE ETB SEMANTIC RESULT = NONE` — authorization acceptance creates no ETB semantic
result; `RECOVERY-R1 PUBLISHED ETB RESULT = REJECTED`, `RECOVERY-R1 AUTHORIZATION = SPENT / NOT REUSABLE`,
`RECOVERY-R1 ETB ATTEMPT = SPENT / NOT REUSABLE` and `NEW_ETB_AUTHORIZATION_REQUIRED = SATISFIED BY ACCEPTED
RECOVERY-R2 AUTHORIZATION DESIGN` while the authorization use remains unused and no operational attempt has
started; Mode-B = `BLOCKED / NOT RUN`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 **NOT CLOSED**; Case-C and v0.3-E
implementation **NOT AUTHORIZED**; `G1`/`G2` `NOT RUN`; `adopt_completed_turn` **DISABLED** — authorization
acceptance does not establish `ETB_SATISFIED`.  Authoritative sequence: Oracle-R2 accepted/frozen → Oracle-R2
bookkeeping independently confirmed → initial Recovery-R2 authorization candidate `af3ec9b7` → independent
REQUEST_CHANGES → corrective Recovery-R2 authorization candidate `02bef765` → independent APPROVE → Recovery-R2
authorization acceptance bookkeeping (this round) → independent bookkeeping confirmation (review-only, no
commit) → exactly one operational authorization consumption + exactly one ETB-attempt consumption + at most
one Oracle-R2 invocation → independent ETB-result review → only an independently accepted `ETB_SATISFIED` may
permit Mode-B construction; no reset, no detached checkout, no confirmation commit.  This bookkeeping round
performed **0** claim creations/deletions, **0** Oracle-R2/old-oracle executions, **0** R2 output or directory
creations, **0** endpoint/listener/process inspections, **0** operational P/Invoke, **0** OpenCode
starts/restarts, **0** HTTP, **0** SIC, **0** Mode-B, **0** G0.5, **0** G1/G2, **0** config mutations, **0** R1
mutations and **0** runtime/test/dependency/version changes; all protected artifacts and the seven historical
R1 operational hashes were re-verified unchanged; the ignored/untracked `PROJECT_MEMORY.md` persists.

**The Recovery-R2 published ETB result was independently reviewed and accepted, so the authoritative ETB
semantic result is now `ETB_UNSATISFIED`** (active status transition: `AUTHORITATIVE ETB SEMANTIC RESULT =
NONE` → **`AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED`**, applying exactly to the accepted one-shot
attempt, its accepted authorization and Oracle-R2 identities, its two spent claims and its three immutable
published result artifacts).  The independent result review issued *APPROVE V0.3-E RECOVERY-R2
PUBLISHED ETB RESULT — ETB_UNSATISFIED* with severity **P0 = 0, P1 = 0, P2 = 0, P3 = 0**, which promotes the
immutable published candidate to the **current authoritative semantic result** for the accepted one-shot
attempt.  This authority applies **exactly** to: the accepted Recovery-R2 one-shot attempt; the accepted
authorization identity `recovery_r2_authorization_commit = 02bef765f74d7349c592138b35280b8b51995a5d` /
`recovery_r2_authorization_sha256 = 91917bb55cc5b59a811c6a5f7bcbc3bf48ffa4f5688c379914912fe6f092d4ab`; the
accepted Oracle-R2 identity `oracle_r2_commit = dfb78f34d919e8c9863a8398fb4f63ee301167bc` /
`oracle_r2_spec_sha256 = 5e9221e3950af6ec3e0612c4d962562c33e761899dfd6af42d10f5a9895f9f2f` /
`oracle_r2_script_sha256 = 22c5fbd61da609e6cc39e973be6030d4c360019ed1f56e69ca45f92fa1689c17`; the two
permanently spent one-shot claims; and the three immutable published result artifacts.  **Immutable-artifact
handling:** the frozen `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_R2.md` **still preserves its
publication-time banner** `CANDIDATE ETB RESULT / AWAITING INDEPENDENT RESULT REVIEW` and was **not** modified;
under the established immutable-artifact + independent-approval-record model, the subsequent independent review
promotes that immutable published candidate to the current authoritative semantic result — the artifact's own
wording remains publication-time history, and the active status surfaces carry the authoritative result.
**Exact meaning of the authoritative result (recorded narrowly):** `ETB_UNSATISFIED` means that this frozen
Recovery-R2 attempt did **not** satisfy the ETB precondition required to proceed to Mode-B construction, with
accepted terminal facts `listener_probe_outcome = QUERY_EXCEPTION`, `terminal_stage = s0_listener` and
`classification = ETB_UNSATISFIED`.  It does **NOT** mean `P6 = FAIL`, `G0.5 = FAIL`, a failed SIC, a failed
Mode-B itself, that OpenCode is generally incompatible, that the endpoint can never become usable, or that
future target binding is impossible; the semantic result is **not** broadened beyond the above.  **Independent
review findings recorded (all as reviewed):** `AUTHORIZATION_CLAIM = VALID`, `ATTEMPT_CLAIM = VALID`,
`ONE_SHOT_BUDGET_STATE = SPENT`, `R2_EVIDENCE_SCHEMA = VALID`,
`EVIDENCE_ORACLE_IDENTITY_BINDING = CORRECT`, `S0_LISTENER_BRANCH = QUERY_EXCEPTION`,
`QUERY_EXCEPTION_FROZEN_CLASSIFICATION = ETB_UNSATISFIED`, `R1_TAXONOMY_REGRESSION = ABSENT`,
`PUBLISHED_CLASSIFICATION_FIDELITY = EXACT`, `TERMINAL_STAGE_CONSISTENCY = PASS`,
`ACTIVITY_COUNTERS = CONSISTENT`, `NON_CLAIMS = VALID`, `MANIFEST_BINDING = VALID`,
`RESULT_ARTIFACT = VALID`, `RESULT_EVIDENCE_CONSISTENCY = PASS`, `PUBLICATION_COMPLETENESS = PASS`,
`EXIT_CODE_CONSISTENCY = PASS`, `PRECHECK_AGGREGATION_ANOMALY = REPORTING_ARTIFACT`,
`PRECONSUMPTION_GATE_VALIDITY = VALID`, `DISCLOSED_PARSE_ERRORS = ZERO_SIDE_EFFECT_TOOLING_ERRORS`,
`PRE1_APPROVAL_RECORD_CHECK = CONFORMANT`, `OPERATIONAL_SEQUENCE = CONFORMANT`,
`POST_ORACLE_READ_COMPLIANCE = PASS` and `ONE_SHOT_EXECUTION_DISCIPLINE = PASS`.  **Recovery-R2 terminal
state:** `RECOVERY-R2 AUTHORIZATION = ACCEPTED / FROZEN / FULLY CONSUMED`; `RECOVERY-R2 AUTHORIZATION USE =
SPENT / NOT REUSABLE`; `RECOVERY-R2 ETB ATTEMPT = SPENT / NOT REUSABLE`; Oracle-R2 invocation count = **1 /
MAXIMUM REACHED**; `RECOVERY-R2 RETRY = NOT AUTHORIZED`; `RECOVERY-R2 SECOND ATTEMPT = NOT AUTHORIZED`.  This
authorization is **not** available and **may not** be described as available; no review or bookkeeping operation
may reopen either budget.  **No automatic new authorization:** `NEW RECOVERY AUTHORIZATION = NOT AUTHORIZED BY
THIS RESULT REVIEW` and **NO NEW AUTHORIZATION EXISTS** — the authoritative `ETB_UNSATISFIED` result does not
itself grant another attempt, and any future diagnostic, remediation or re-authorization path would require a
new explicitly designed and independently reviewed stage (not designed here).  Preserved exactly and unchanged
by this bookkeeping: `P6 = UNPROVEN / UNSATISFIED` (never PASS, FAIL, PROVEN or CLOSED — `ETB_UNSATISFIED` is a
prerequisite/control result, not the semantic execution of P6); `Mode-B = BLOCKED / NOT RUN` with `MODE-B
CONSTRUCTION = NOT AUTHORIZED` (only an independently accepted `ETB_SATISFIED` could permit Mode-B oracle
construction); `G0.5 = NOT CLOSED` (never PASS, FAIL or CLOSED — the authoritative ETB result settles the
Recovery-R2 prerequisite attempt but does not itself execute or close G0.5/P6); `Case-C = NOT AUTHORIZED`;
`v0.3-E implementation = NOT AUTHORIZED`; `G1`/`G2` = `NOT RUN`; `adopt_completed_turn` = **DISABLED**.  R1
history is untouched: `RECOVERY-R1 PUBLISHED ETB RESULT = REJECTED`, `RECOVERY-R1 AUTHORIZATION = SPENT / NOT
REUSABLE`, `RECOVERY-R1 ETB ATTEMPT = SPENT / NOT REUSABLE`.  Authoritative sequence (updated): Oracle-R2
accepted/frozen → Recovery-R2 authorization accepted/frozen → authorization bookkeeping independently confirmed
→ one-shot Recovery-R2 operational attempt → independent published-result review → **`ETB_UNSATISFIED` accepted
as authoritative (current state)** → **result acceptance bookkeeping (this round)** → independent
result-bookkeeping confirmation → **STOP at the G0.5-PRE reconciliation boundary**; any further
diagnostic/remediation/re-authorization decision requires a **NEW explicit owner-authorized stage**, and this
round does **not** automatically proceed to Mode-B, another ETB attempt, G0.5, G1, G2 or v0.3-E implementation.
Next-gate status: `MODE-B CONSTRUCTION = NOT AUTHORIZED`; `NEW ETB AUTHORIZATION = NOT AUTHORIZED`;
`G0.5 EXECUTION = NOT AUTHORIZED BY THIS BOOKKEEPING`; `NEXT REQUIRED STAGE AFTER BOOKKEEPING CONFIRMATION =
G0.5-PRE / ETB UNSATISFIED RECONCILIATION / OWNER DECISION` (decision and reconciliation only unless separately
authorized).  Restricted operational artifacts were reverified byte-identical and were **not** modified:
authorization claim `fd7336e4…` (488 bytes, `state = CONSUMED`), attempt claim `69eb6ef0…` (482 bytes,
`state = CONSUMED`), R2 evidence `6f903f05…` (3820 bytes), R2 manifest `b4701c90…` (120 bytes) and R2 result
`84f51bb5…` (729 bytes); all protected artifacts, config (`b5e4abab…` / 1897 / `http://127.0.0.1:4096`) and
`CONFIG_ESTABLISHMENT = VALID / PRESENT` (`ea9fc2bc…`) are unchanged.  This bookkeeping round performed **0**
oracle executions, **0** claim creations or deletions, **0** output mutations, **0** target/listener/process
probes, **0** OpenCode starts/restarts, **0** HTTP, **0** SIC, **0** Mode-B, **0** G0.5, **0** G1/G2, **0**
config mutations, **0** R1 mutations and **0** runtime/test/dependency/version changes; the ignored/untracked
`PROJECT_MEMORY.md` persists.

**Owner decision PATH B — a new `ETB QUERY_EXCEPTION DIAGNOSTIC D1` design candidate now exists (design
only; nothing executed).**  The authoritative state remains `AUTHORITATIVE ETB SEMANTIC RESULT =
ETB_UNSATISFIED` (published `listener_probe_outcome = QUERY_EXCEPTION`, `terminal_stage = s0_listener`) with
Recovery-R2 permanently `ACCEPTED / FROZEN / FULLY CONSUMED` (both one-shot budgets `SPENT / NOT REUSABLE`,
Oracle-R2 invocation `1 / MAXIMUM REACHED`) and `NEW RECOVERY AUTHORIZATION = NONE`; the owner elected to
continue G0.5-PRE work only through a new, separately authorized, read-only diagnostic stage whose sole
purpose is to capture the missing listener-query failure information — **ROOT_CAUSE_IDENTIFIABILITY =
PARTIALLY_CONSTRAINED**, **STATIC_ORACLE_R2_LISTENER_DEFECT = NOT_PROVEN**.  The new artifact
`docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_EXCEPTION_DIAGNOSTIC_D1_SPEC.md` is a **DESIGN CANDIDATE / NOT ACCEPTED /
NOT AUTHORIZED / NOT EXECUTED** with D1 AUTHORIZATION USE = `UNAVAILABLE / NOT YET GRANTED`, D1
DIAGNOSTIC ATTEMPT = `UNAVAILABLE / NOT YET GRANTED`, and a **D1 LISTENER QUERY INVOCATION maximum = 1**;
it is NOT an ETB semantic attempt and can never produce or replace `ETB_SATISFIED` / `ETB_UNSATISFIED` /
`HARNESS_INVALID` (a future diagnostic row observation MUST NOT be promoted to `ETB_SATISFIED`).  Frozen
inside the design: the exact same listener-query shape as accepted Oracle-R2 (`Get-NetTCPConnection
-LocalAddress '127.0.0.1' -LocalPort 4096 -State Listen` with `-ErrorAction SilentlyContinue -ErrorVariable
qerr`, initialized immediately before, executed exactly once, no second clarifying query, no alternate
address/port/IPv6/discovery); a **new permanently distinct D1 namespace** (`ETB_QUERY_DIAGNOSTIC_D1_*` claim
paths with `.tmp` variants, `docs/v0.3/evidence/etb-query-diagnostic-d1/` evidence/manifest, result
`V03E_G0_5_PRE_ETB_QUERY_DIAGNOSTIC_RESULT_D1.md` (+`.tmp`); nothing created this round); 1/1 + 1/1
diagnostic budgets wholly independent from Recovery-R2; a future provenance model without self-reference
(`diagnostic_d1_design_commit` / `diagnostic_d1_spec_sha256` populated only by a later independent approval
record); permanent source binding to the authoritative state at `93e44fe61c59ec5070e2823062a607347bb9163a`
(R2 evidence `6f903f05…`, result `84f51bb5…`, both R2 claims, the accepted authorization and Oracle-R2
identities); closed future **environment metadata** categories only (PowerShell `PSEdition`/`PSVersion`/
`Platform`/`OS` + command `Name`/`CommandType`/`Source`/`Version`/`ModuleName` + module metadata for the
command only — no broad inventory, no unrelated modules, no software/user lists); the exact future query
semantics ($qerr reset before the single query, terminating `$_` capture, all qerr records preserved, rows
not discarded); an explicit **non-ETB** diagnostic observation vocabulary (`COMMAND_UNAVAILABLE`,
`TERMINATING_EXCEPTION`, `ERROR_RECORDS_ZERO_ROWS`, `ERROR_RECORDS_WITH_ROWS`, `ZERO_ROWS`, `ONE_ROW`,
`MULTIPLE_ROWS`, `DIAGNOSTIC_HARNESS_INVALID`) that never collapses the terminating-catch vs error-record
distinction; row evidence limited to `LocalAddress`/`LocalPort`/`State`/`OwningProcess` + row count (no
process lookup, no `Win32_Process`, no binding); a closed **15-field error-record schema** (source,
FullyQualifiedErrorId, category/activity/reason/target name/target type, exception type/message/HResult,
inner type/message, error-details message, invocation position, script stack trace; unavailable fields →
exact frozen empty-string rule, no conditional omission); explicit persisted **command-availability**
evidence; explicit **query-shape** evidence (closing the gap where query parameters were not persisted);
a new closed evidence schema `devrelay-etb-query-diagnostic-d1-v1` with exact 19-field top-level order and
exact closed sub-schema orders; config binding through the same frozen reader shape; the non-claims list
(diagnostic observation alone establishes no ETB/P6/G0.5 outcome, no Mode-B authorization, no permanent
state claims, no Oracle-R2 correctness judgment); a closed activity-counter structure requiring
`listener_query_invocations <= 1` and all prohibited counters = 0; and a future publication/claim model on
new D1 paths only.  A future D1 result is **diagnostic evidence only**: it may become an authoritative
diagnostic result but can never replace `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED`; any later
new ETB authorization remains a separate owner decision.  Recorded: **PATH C — STATIC ORACLE CORRECTION**
currently lacks a static basis (`STATIC_ORACLE_R2_LISTENER_DEFECT = NOT_PROVEN`; D1 does not authorize
Oracle-R2 modification) and **PATH D — NEW ETB ATTEMPT** remains NOT AUTHORIZED.  Future sequence: D1
design review → bookkeeping → confirmation → separate implementation/execution-authorization round → its
own bookkeeping + confirmation → exactly one authorization consumption, one attempt consumption, one
listener-query invocation → publication → independent D1 result review → separate result bookkeeping →
owner reconciliation.  All current gate states are preserved unchanged (Mode-B BLOCKED/NOT RUN, P6
UNPROVEN/UNSATISFIED, G0.5 NOT CLOSED, Case-C/v0.3-E implementation NOT AUTHORIZED, G1/G2 NOT RUN,
adopt_completed_turn DISABLED); this design round performed **0** listener queries, **0** claims, **0**
diagnostic outputs, **0** Oracle executions, **0** live probes, **0** OpenCode starts/restarts, **0** HTTP,
**0** provider/model calls, **0** SIC, **0** Mode-B, **0** G0.5/G1/G2, **0** config mutations, **0**
Recovery-R2/R1 mutations and **0** runtime/test/dependency/version changes.

**D1 CORRECTIVE DESIGN R1 — the initial D1 design candidate `78266c95` was rejected.**  The
independent D1 design review issued **REQUEST_CHANGES — V0.3-E ETB QUERY_EXCEPTION
DIAGNOSTIC D1 DESIGN** with **P0 = 0, P1 = 0, P2 = 1, P3 = 2**, so
`78266c954087b33baf5a12dfab1cbdef845a0bbb` is **REJECTED / SUPERSEDED / NEVER ACCEPTED /
NOT AUTHORIZED / NOT EXECUTED** and is preserved permanently as historical provenance
(never relabelled as accepted).  The single blocking **P2** was narrow and purely
representational: `terminating_error` had no explicit closed schema, and the
null / absent / empty representations of the D1 evidence schema were not frozen.  A
**narrow corrective design round** has now closed it: `terminating_error` is explicitly
added to the closed sub-schema contract as exactly `null` **or** one closed 15-field
`ErrorRecord` object (`source = "TERMINATING_EXCEPTION"`), a **single** object and never an
array, whose remaining 14 fields reuse the exact §15 field names, ordering and scalar
rules, and which must contain only the actual `catch { $_ }` record; `error_records`
contains **only** `-ErrorVariable qerr` records in observed order (each with
`source = "ERROR_VARIABLE"`), a terminating catch record is never duplicated into it, and
a zero-record `qerr` yields `[]` — creating an explicit **mechanical** separation between
the two fields; one complete normative null / empty representation table now freezes
every field of the schema (every closed field is always emitted with no conditional key
omission; unavailable strings are `""` and never `null`; every array is always an array
and zero elements is `[]` and never `null`, explicitly for `rows`, `error_records` and
`non_claims`; the only absence form for the optional `terminating_error` is `null`; the
integer-valued required counters `row_count`, `query.query_invocation_count`, all activity
counters and `query.local_port` are always JSON integers and never `null`, with
`row_count = 0` when no rows are returned or no completed row result was reached, and
`query_invocation_count` `0` only when the listener query was not invoked — including
`COMMAND_UNAVAILABLE` — and `1` once the single allowed query was invoked, with **no
negative sentinels**; unavailable row integers `LocalPort` / `OwningProcess` are `null`
while the row key stays present, and unavailable row strings `LocalAddress` / `State` are
`""`; `command_metadata` is always present and, when `availability = "UNAVAILABLE"`, every
string metadata field — `Name`, `CommandType`, `Source`, `Version`, `ModuleName` — is
emitted as `""` with **no key omitted**; `powershell_environment` and `query` are always
present with their frozen values and only `query_invocation_count` varying between `0` and
`1`; `configured_base_url` still comes from the accepted frozen config-reader contract and
no placeholder is invented for config-reader failure, because that belongs to the future
harness/precondition failure path); every ErrorRecord field is frozen as a **JSON string**
with `exception_hresult` serialized as its invariant signed decimal **text**, not a JSON
number; per-class representations are frozen exhaustively for `TERMINATING_EXCEPTION`,
`COMMAND_UNAVAILABLE`, `ZERO_ROWS`, `ONE_ROW`, `MULTIPLE_ROWS`, `ERROR_RECORDS_ZERO_ROWS`
and `ERROR_RECORDS_WITH_ROWS` (the last covering one-row-plus-`qerr` and
multiple-rows-plus-`qerr` without introducing a new class), `DIAGNOSTIC_HARNESS_INVALID`
keeps its unchanged non-ETB semantic rule with only its serialization point clarified, and
a 13-case completeness walk leaves **no** choice between `null`, `""`, `[]` and an omitted
key (**`D1_NULL_EMPTY_RULES = COMPLETE`**, **`D1_SUBSCHEMAS = ALL_CLOSED`**).  The first
non-blocking **P3** is closed by explicit normative prose that
`source_authoritative_bookkeeping_commit = 93e44fe61c59ec5070e2823062a607347bb9163a`
anchors the tracked historical source state, that the accepted Recovery-R2 authorization
and the accepted Oracle-R2 tracked artifacts are mechanically recoverable from that
immutable Git ancestry/tree together with their already frozen accepted hashes, that the
Recovery-R2 manifest relationship stays externally frozen by the accepted R2 manifest
format and the D1-bound R2 evidence hash, and that the two untracked Recovery-R2 claim
hashes (`fd7336e4694f8d491ddd3067880851f96974a29a1117d48f7dd47eb2d629ccf7` and
`69eb6ef0352375311f72c211d04c8ed39e59d8f7b00b6d7738577044916167f9`) are rebound as
**mandatory future execution/authorization preconditions** — explicitly **not** as new
top-level evidence fields, with the 19-field schema unaltered.  The second **P3** is
deliberately **not** forced to zero: no arbitrary or lossy truncation was introduced, and
the honest record is **ERROR STRING MAXIMUM REPRESENTATION RULE = NOT YET FROZEN /
NON-BLOCKING DESIGN OBSERVATION**, because no accepted deterministic boundedness rule
exists for the message/stack fields and truncating them would silently destroy the
diagnostic evidence D1 exists to capture.  No design element that review already accepted
was redesigned: the PATH B owner decision, the D1 purpose, the non-ETB semantic boundary,
the diagnostic target, the `Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 4096
-State Listen` query shape, the one-query maximum, the no-retry rule, the D1 claim and
output namespaces (all still ABSENT), the 1/1 + 1/1 budgets, the provenance model, the
allowed environment-metadata categories, the observation vocabulary and its exhaustive
exclusive partition, the row evidence field set, the 15-field ErrorRecord field set, the
**19-field top-level schema and its exact order**, the config binding, the non-claims, the
activity counters, the publication sequence, the claim-model design-only boundary, the
diagnostic-result authority model, the future control sequence, the Path C / Path D status
and the Mode-B / P6 / G0.5 state are all **preserved verbatim**.  The corrective round is
still **design-only**: the active status is **ETB QUERY_EXCEPTION DIAGNOSTIC D1 —
CORRECTIVE DESIGN R1 = DESIGN CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED / NOT EXECUTED**
(not APPROVED, not ACCEPTED, not FROZEN, not AUTHORIZED, not EXECUTABLE and not READY FOR
LIVE DIAGNOSTIC EXECUTION) and it requires a fresh independent D1 design re-review; no
diagnostic execution, no claim creation, no new ETB authorization, no Mode-B, no `.ps1`
file and no D1 operational artifact of any kind was created; the corrective tracked delta
is exactly three files
(`docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_EXCEPTION_DIAGNOSTIC_D1_SPEC.md`, `CHANGELOG.md`,
`docs/v0.3/V03E_ACCEPTANCE.md`), `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED` is
untouched, and the corrective round performed **0** listener queries, **0** claims, **0**
diagnostic outputs, **0** Oracle executions, **0** live probes, **0** OpenCode
starts/restarts, **0** HTTP, **0** provider/model calls, **0** SIC, **0** Mode-B, **0**
G0.5/G1/G2, **0** config mutations, **0** Recovery-R2/R1 mutations and **0**
runtime/test/dependency/version changes.

**The corrective D1 diagnostic design was independently approved, so the ETB QUERY_EXCEPTION DIAGNOSTIC D1
DESIGN is now `ACCEPTED / FROZEN / NOT IMPLEMENTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED`
(design-acceptance bookkeeping only; no claim created, nothing executed).**  The independent re-review issued
*APPROVE V0.3-E ETB QUERY_EXCEPTION DIAGNOSTIC D1 CORRECTIVE DESIGN R1* with severity **P0 = 0, P1 = 0, P2 =
0, P3 = 1**, closing the initial blocking **P2** (narrowly representational: `terminating_error` had no
explicit closed schema and the null/absent/empty representations were unfrozen) through: (A) an explicit
closed `terminating_error` schema (exactly `null` or one closed 15-field `ErrorRecord` object with `source =
"TERMINATING_EXCEPTION"`, never an array/`{}`/`[]`/omitted, catch-path-only); (B) deterministic
`terminating_error` / `error_records` channel separation (qerr-only entries with `source =
"ERROR_VARIABLE"`, no catch-record duplication, no qerr → `[]`); (C) complete null/empty/absent
representation rules; (D) closed required-key semantics; (E) closed string/array/optional-object/integer
rules; (F) explicit nullable row-observation integer semantics; (G) a complete per-observation
representation matrix (13 walked cases, `D1_NULL_EMPTY_RULES = COMPLETE`); and (H) all sub-schemas closed
(`D1_SUBSCHEMAS = ALL_CLOSED`).  The permanently accepted D1 DESIGN provenance is
`diagnostic_d1_design_commit = 6ad917b950c12e7a93579c519cc63f89925c2ab0` and `diagnostic_d1_spec_sha256 =
e9c521ff9d9333999d1ccc2156f3f78400a5b0e5b19b42a7cf2280c8f0def466`; this acceptance-bookkeeping commit
explicitly does **not** replace `diagnostic_d1_design_commit`, and no later bookkeeping confirmation,
implementation candidate, execution authorization, operational HEAD or diagnostic-result review may
substitute another commit for this accepted design identity.  The frozen spec was re-verified byte-identical
before and after this round (worktree = committed blob, UTF-8, no BOM, LF-only).  Design acceptance records
the independent confirmation of: `D1_R1_TOPOLOGY = PASS`, `D1_R1_DELTA = EXACT`,
`WORKTREE_EQUALS_BLOB = YES`, `D1_R1_SCOPE_REGRESSION = NONE`, `D1_TERMINATING_ERROR_SCHEMA = CLOSED`,
`D1_ERROR_CHANNEL_SEPARATION = DETERMINISTIC`, `D1_ERROR_RECORD_SCHEMA = VALID`,
`D1_ERRORRECORD_SCALAR_NULL_RULE = CONSISTENT`, `D1_REQUIRED_KEY_RULE = CLOSED`,
`D1_STRING_EMPTY_RULE = DETERMINISTIC`, `D1_ARRAY_EMPTY_RULE = DETERMINISTIC`,
`D1_OPTIONAL_OBJECT_RULE = DETERMINISTIC`, `D1_INTEGER_RULE = DETERMINISTIC`, `D1_ROW_NULL_RULE =
CONSISTENT`, `D1_COMMAND_UNAVAILABLE_REPRESENTATION = COMPLETE`,
`D1_TERMINATING_EXCEPTION_REPRESENTATION = COMPLETE`, `D1_NORMAL_RESULT_REPRESENTATIONS = COMPLETE`,
`D1_QERR_REPRESENTATIONS = COMPLETE`, `D1_NULL_EMPTY_RULES = COMPLETE`, `D1_SUBSCHEMAS = ALL_CLOSED`,
`D1_TOPLEVEL_SCHEMA = PRESERVED`, `D1_OBSERVATION_VOCABULARY = PRESERVED`,
`D1_OBSERVATION_PARTITION = EXHAUSTIVE_AND_EXCLUSIVE`, `D1_HARNESS_INVALID_BOUNDARY = PRESERVED`,
`D1_SOURCE_PROVENANCE_P3 = CLOSED`, `D1_ERROR_STRING_BOUNDARY = NONBLOCKING_OPEN_P3`,
`D1_SEMANTIC_ISOLATION = PASS`, `D1_OPERATIONAL_ARTIFACT_STATE = ABSENT`,
`D1_COMMIT_IDENTITY_RECOVERY = ZERO_SIDE_EFFECT`, `D1_UNTRACKED_COUNT_ANOMALY = REPORTING_ARTIFACT`,
`D1_R1_CONTRADICTION_SWEEP = PASS`, `D1_R1_MATERIAL_EXECUTOR_CHOICE = NONE`,
`D1_R1_SELF_SUFFICIENCY = PASS`.  The initial candidate `78266c954087b33baf5a12dfab1cbdef845a0bbb` remains
permanently **D1 INITIAL DESIGN = REJECTED / SUPERSEDED / NEVER ACCEPTED / NOT AUTHORIZED / NOT EXECUTED**
with its historical review *REQUEST_CHANGES — V0.3-E ETB QUERY_EXCEPTION DIAGNOSTIC D1 DESIGN* (P0 = 0, P1 =
0, P2 = 1, P3 = 2); history is not rewritten as though it passed.  The accepted D1 design remains **DIAGNOSTIC
ONLY / NON-ETB SEMANTIC / ONE-QUERY MAXIMUM / NO RETRY / NO FALLBACK**: design acceptance does **not**
authorize execution, does **not** create any D1 executable, claim, evidence, manifest, result or output
directory, does **not** record either future budget as granted, and cannot itself produce or replace
`AUTHORITATIVE ETB_SATISFIED` / `AUTHORITATIVE ETB_UNSATISFIED` / P6 PASS / P6 FAIL / G0.5 PASS / G0.5 FAIL /
Mode-B authorization.  Accepted design contracts recorded by reference to the frozen spec: the exact
diagnostic query shape (`Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 4096 -State Listen` with
`-ErrorAction SilentlyContinue -ErrorVariable qerr`; future listener-query invocation maximum = 1, no
retry/repeat/polling/alternate command/CIM reconstruction/fallback — **design acceptance only, not
executed**); the closed non-ETB observation vocabulary (`COMMAND_UNAVAILABLE`, `TERMINATING_EXCEPTION`,
`ERROR_RECORDS_ZERO_ROWS`, `ERROR_RECORDS_WITH_ROWS`, `ZERO_ROWS`, `ONE_ROW`, `MULTIPLE_ROWS`,
`DIAGNOSTIC_HARNESS_INVALID`; no observation class maps directly to ETB semantic authority); the accepted
evidence schema `devrelay-etb-query-diagnostic-d1-v1` with its exact 19-field top-level order
(`schema_version, source_authoritative_bookkeeping_commit, source_r2_evidence_sha256,
source_r2_result_sha256, execution_started_at, execution_finished_at, diagnostic_mode, endpoint,
configured_base_url, powershell_environment, command_metadata, query, query_outcome, row_count, rows,
terminating_error, error_records, non_claims, activity_counters`); `D1_SUBSCHEMAS = ALL_CLOSED` and
`D1_NULL_EMPTY_RULES = COMPLETE` (the frozen spec is authoritative; the full spec is not duplicated into
bookkeeping).  Source binding preserved: source authoritative bookkeeping commit `93e44fe…`; R2 evidence
`6f903f05…`; R2 manifest `b4701c90…`; R2 result `84f51bb5…`; R2 authorization claim `fd7336e4…`; R2 attempt
claim `69eb6ef0…`; accepted Recovery-R2 authorization and Oracle-R2 provenance unchanged.  The D1 namespace
is **DEFINED / ACCEPTED / FROZEN / NO OPERATIONAL ARTIFACT CREATED** — all reserved paths verified still
ABSENT.  Future budget status remains **D1 AUTHORIZATION USE = UNAVAILABLE / NOT YET GRANTED**, **D1
DIAGNOSTIC ATTEMPT = UNAVAILABLE / NOT YET GRANTED**, **D1 LISTENER QUERY EXECUTION = NOT AUTHORIZED**
(1/1 + 1/1 + maximum-1 are DESIGN-DEFINITIONS only until a later separately accepted execution
authorization).  Implementation boundary: **D1 IMPLEMENTATION = NOT YET CREATED / NOT AUTHORIZED**; **D1
EXECUTION AUTHORIZATION = DOES NOT EXIST**; **D1 EXECUTION = NOT AUTHORIZED**; **D1 CLAIM WRITER = NOT YET
FROZEN**; **D1 PUBLICATION IMPLEMENTATION = NOT YET FROZEN**.  Authoritative future sequence: D1 corrective
design accepted (`6ad917b…` / `e9c521ff…`) → D1 design acceptance bookkeeping (this round) → **independent
D1 design-bookkeeping confirmation [REVIEW-ONLY / NO COMMIT IS CREATED]** (a later confirmation review must
leave the bookkeeping HEAD unchanged) → separate D1 implementation / execution-authorization candidate →
independent implementation/authorization review → if approved: execution-authorization bookkeeping →
independent execution-authorization bookkeeping confirmation → exactly one D1 authorization consumption →
exactly one D1 diagnostic-attempt consumption → exactly one listener-query invocation → D1 diagnostic
publication → independent D1 diagnostic-result review → result bookkeeping/confirmation → owner
reconciliation; no stage may be skipped.  Preserved states: `AUTHORITATIVE ETB SEMANTIC RESULT =
ETB_UNSATISFIED`; Recovery-R2 authorization use / attempt = `SPENT / NOT REUSABLE`; Mode-B = `BLOCKED / NOT
RUN`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 = `NOT CLOSED`; G0.5 execution / Case-C / v0.3-E implementation
`NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`; `adopt_completed_turn` **DISABLED** — D1 design acceptance changes
none of these.  Path preservation: **PATH C — STATIC ORACLE CORRECTION = NO STATIC BASIS / NOT AUTHORIZED**
(`STATIC_ORACLE_R2_LISTENER_DEFECT = NOT_PROVEN`); **PATH D — NEW ETB ATTEMPT = NOT AUTHORIZED** — D1 design
acceptance authorizes neither.  P3 status: source-provenance clarification = **CLOSED**; **ERROR STRING
MAXIMUM REPRESENTATION RULE = NOT YET FROZEN / NON-BLOCKING DESIGN OBSERVATION** (no truncation rule is
invented in bookkeeping; not silently closed; not an execution authority).  Contradiction sweep clean: no
text claims 78266c accepted, D1 execution authorized/executed, a D1 executable/claim exists, a new ETB
authorization exists, Recovery-R2 reusable, `ETB_SATISFIED`, a P6/G0.5 verdict, G0.5 CLOSED, Mode-B
authorized, Oracle-R2 defective or root cause determined.  This bookkeeping round performed **0**
listener-query executions, **0** `Get-NetTCPConnection` calls, **0** claim creations/deletions, **0** D1
evidence/result/output-directory creations, **0** Oracle executions, **0** target/listener/process probes,
**0** OpenCode starts/restarts, **0** HTTP, **0** provider/model calls, **0** SIC, **0** Mode-B, **0**
G0.5/G1/G2, **0** config mutations, **0** Recovery-R2/R1 mutations and **0** runtime/test/dependency/version
changes; all protected artifacts re-verified unchanged; the ignored/untracked `PROJECT_MEMORY.md` persists.

**D1 IMPLEMENTATION DESIGN GAP CLARIFICATION C1 — the accepted design was insufficiently complete to authorize implementation.**  An implementation / execution-authorization round was attempted against the accepted design `6ad917b950c12e7a93579c519cc63f89925c2ab0` / `e9c521ff9d9333999d1ccc2156f3f78400a5b0e5b19b42a7cf2280c8f0def466` and **stopped before any mutation**, returning **`D1 IMPLEMENTATION DESIGN GAP`** with **0 files created, 0 commits created, 0 claims, 0 queries and 0 budgets consumed**: two required members of the accepted 19-field top-level evidence schema had **no frozen JSON type or value** — **P1-1** `diagnostic_mode` (present as a field name but never typed or valued) and **P1-2** `endpoint` (referenced by a circular *"remains the frozen diagnostic endpoint representation"* clause while that representation was never given) — plus a non-blocking **P3** that `non_claims` was specified only semantically, its exact serialized string-array elements never frozen.  The previously accepted design is **NOT** relabelled REJECTED or NEVER ACCEPTED: `6ad917b…` remains **ACCEPTED / FROZEN / HISTORICAL AUTHORITATIVE PRECEDENT / IMPLEMENTATION BLOCKED BY SUBSEQUENTLY DISCOVERED DESIGN GAP** and its acceptance bookkeeping at `8738651a…` remains historically valid; the gap means only that the accepted revision was insufficiently complete.  A **narrow design-clarification round** now closes all three: `diagnostic_mode` is frozen as a required JSON **string** constant `"QUERY_EXCEPTION_DIAGNOSTIC_D1"` that never varies by runtime observation and encodes no query outcome, ETB result, P6 state or G0.5 state (no null/empty permitted); `endpoint` is frozen as a required JSON **string scalar** constant `"http://127.0.0.1:4096"` — explicitly **not an object**, explicitly **not** inheriting the `devrelay-etb-v1-r2` endpoint object schema (no `scheme`/`address_family`/`host`/`port`/`base_uri`/`fallback` nested fields; R2 is historical context only) — with the `endpoint` vs `configured_base_url` distinction frozen explicitly (the former is the constant diagnostic target contract, the latter the value actually established by the accepted frozen Recovery-R2 config reader, requiring `configured_base_url == endpoint == "http://127.0.0.1:4096"` before any claim consumption; the two are intentionally redundant for provenance, never merged and never inferred one from the other); `non_claims` is frozen as a JSON array of **exactly 13 strings in exact order** (`"does not establish ETB_SATISFIED"`, `"does not establish a replacement ETB_UNSATISFIED"`, `"does not establish P6 PASS"`, `"does not establish P6 FAIL"`, `"does not establish G0.5 PASS"`, `"does not establish G0.5 FAIL"`, `"does not authorize Mode-B"`, `"does not establish OpenCode general compatibility or incompatibility"`, `"does not establish permanent endpoint state"`, `"does not establish permanent listener state"`, `"does not establish process binding"`, `"does not establish target executable identity"`, `"does not establish Oracle-R2 general correctness or incorrectness"`) — a serialization formalization with a verified **13 → 13 bijective** mapping onto the already accepted §20 semantics, adding no new substantive non-claim and deleting none; and one normative **complete top-level 19-field closure table** now fixes for every field its JSON type, cardinality, value/source contract, runtime-variability and detailed-rule reference, backed by a closure audit rule (a field is CLOSED only via a complete scalar type+value/source rule, a closed object/array sub-schema by explicit cross-reference, or an explicitly authorized later implementation-stage formatting choice whose semantic type/source/cardinality are already frozen) yielding **`D1_TOPLEVEL_FIELD_CLOSURE = 19 / 19 CLOSED`**.  For `execution_started_at`/`execution_finished_at` this round freezes only JSON type = string, cardinality = required scalar and source = UTC runtime timestamp, preserving the previously authorized implementation-stage freedom to freeze **one** exact invariant textual format later (**TIMESTAMP STRING FORMAT = INTENTIONALLY DEFERRED TO IMPLEMENTATION / EXECUTION-AUTHORIZATION DESIGN — AN AUTHORIZED IMPLEMENTATION-LEVEL FORMAT CHOICE / NOT A MATERIAL D1 SEMANTIC GAP**).  A **REVIEW-COVERAGE CORRECTION** is recorded and explicitly **not** as evidence of malicious or invalid prior review: the prior Corrective R1 review verified the eight listed closed sub-schemas but did not cross-check every top-level member of the 19-field schema for an explicit scalar type/value/source rule or sub-schema binding, which allowed these two fields to remain materially underdefined; **future D1 design reviews MUST include a 19/19 top-level field closure audit**.  Nothing else was redesigned: the query contract (`Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 4096 -State Listen -ErrorAction SilentlyContinue -ErrorVariable qerr`), the one-query maximum, the no-retry rule, the eight-value observation vocabulary, the 15-field ErrorRecord schema, `terminating_error`, `error_records`, the row schema, the PowerShell environment schema, the command metadata schema, the null/empty rules, the activity counters, the claim namespace, the future budgets, the publication namespace, the source provenance (`93e44fe6…`; R2 evidence `6f903f05…`; R2 manifest `b4701c90…`; R2 result `84f51bb5…`; R2 authorization claim `fd7336e4…`; R2 attempt claim `69eb6ef0…`), the config contract and the Path C/D state are all **preserved verbatim**, and the standing **ERROR STRING MAXIMUM REPRESENTATION RULE = NOT YET FROZEN / NON-BLOCKING DESIGN OBSERVATION** P3 is unchanged with no truncation invented.  The clarification candidate is only **D1 IMPLEMENTATION DESIGN GAP CLARIFICATION C1 = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT AUTHORIZED / NOT EXECUTED**; `diagnostic_d1_design_commit` is **not** prematurely replaced, and the future provenance transition (in which the clarification candidate would become the new `diagnostic_d1_design_commit` and the clarified spec hash the new `diagnostic_d1_spec_sha256`, with `6ad917b…` recorded as PREVIOUSLY ACCEPTED / HISTORICAL PREDECESSOR / SUPERSEDED BY ACCEPTED CLARIFICATION rather than REJECTED) happens **only if** this clarification is independently approved and accepted.  No executable, execution-authorization document, claim, evidence, manifest, result or output directory was created; all D1 operational artifacts remain **ABSENT** and budgets remain **D1 AUTHORIZATION USE = `UNAVAILABLE / NOT YET GRANTED`**, **D1 DIAGNOSTIC ATTEMPT = `UNAVAILABLE / NOT YET GRANTED`**, **D1 LISTENER QUERY EXECUTION = `NOT AUTHORIZED`**; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED` is untouched, Recovery-R2 remains **SPENT / NOT REUSABLE**, and Mode-B stays **BLOCKED / NOT RUN**, `P6 = UNPROVEN / UNSATISFIED`, **G0.5 = NOT CLOSED**, G0.5 execution / Case-C / v0.3-E implementation **NOT AUTHORIZED**, `G1`/`G2` **NOT RUN**, `adopt_completed_turn` **DISABLED**, **PATH C = NO STATIC BASIS / NOT AUTHORIZED** and **PATH D = NOT AUTHORIZED**.  This clarification round performed **0** listener-query executions, **0** `Get-NetTCPConnection` calls, **0** claim creations, **0** evidence/manifest/result/output-directory creations, **0** Oracle executions, **0** target/listener/process probes, **0** OpenCode starts/restarts, **0** HTTP, **0** provider/model calls, **0** SIC, **0** Mode-B, **0** G0.5/G1/G2, **0** config mutations, **0** Recovery-R2/R1 mutations and **0** runtime/test/dependency/version changes.

**D1 DESIGN ACCEPTANCE BOOKKEEPING — CLARIFICATION C1 ACCEPTED.**  The independent re-review of the D1 IMPLEMENTATION DESIGN GAP CLARIFICATION C1 candidate issued **APPROVE V0.3-E ETB QUERY_EXCEPTION DIAGNOSTIC D1 IMPLEMENTATION DESIGN GAP CLARIFICATION C1** with **P0 = 0, P1 = 0, P2 = 0, P3 = 1**, so the clarification is now **`ACCEPTED / FROZEN / NOT IMPLEMENTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED`**.  Because the clarification received independent approval **and** this acceptance bookkeeping, the successor-provenance transition frozen by the clarification (§53) now takes effect: **`diagnostic_d1_design_commit = b8f8a67beac154894e496aaa601fa0a4cd4e9905`** and **`diagnostic_d1_spec_sha256 = 29f0f9cc1632f2f344f5cb4e01d25a832ba9acc78caedbdd43861b7d68ac4154`** are the new accepted D1 design provenance for all future D1 implementation / execution-authorization work.  The previously accepted design `6ad917b950c12e7a93579c519cc63f89925c2ab0` / `e9c521ff9d9333999d1ccc2156f3f78400a5b0e5b19b42a7cf2280c8f0def466` is **NOT** relabelled REJECTED or NEVER ACCEPTED: it is now recorded as **PREVIOUSLY ACCEPTED / HISTORICAL AUTHORITATIVE PREDECESSOR / SUPERSEDED BY ACCEPTED CLARIFICATION**, and its acceptance bookkeeping at `8738651ab805b9ccf07a4687627ef0a1d7bb7916` remains historically valid and is likewise a historical predecessor rather than a rejected round.  The clarification closed all three reported gaps: **P1-1** `diagnostic_mode` is now frozen as a required JSON **string** constant `"QUERY_EXCEPTION_DIAGNOSTIC_D1"` that never varies by runtime observation and encodes no query outcome, ETB result, P6 state or G0.5 state; **P1-2** `endpoint` is now frozen as a required JSON **string scalar** constant `"http://127.0.0.1:4096"` — explicitly **not an object**, explicitly **not** inheriting the `devrelay-etb-v1-r2` endpoint object schema (R2 is historical context only) — with the frozen distinction that `endpoint` is the constant diagnostic-target contract while `configured_base_url` is the value actually established by the accepted frozen Recovery-R2 config reader, requiring `configured_base_url == endpoint == "http://127.0.0.1:4096"` before any claim consumption; and **P3** `non_claims` is now frozen as a JSON array of **exactly 13 strings in exact order**, a serialization formalization with a verified **13 → 13 bijective** mapping onto the already accepted §20 semantics that adds no new substantive non-claim and deletes none.  A normative **complete top-level 19-field closure table** now fixes JSON type, cardinality, value/source contract, runtime-variability and detailed-rule reference for every top-level field, backed by the closure audit rule (three routes: complete scalar type+value/source rule; closed object/array sub-schema by explicit cross-reference; or an explicitly authorized later implementation-stage formatting choice whose semantic type/source/cardinality are already frozen), with the design stating **`D1_TOPLEVEL_FIELD_CLOSURE = 19 / 19 CLOSED`**; for `execution_started_at` / `execution_finished_at` only JSON type = string, cardinality = required scalar and source = UTC runtime timestamp are frozen now, the exact textual format remaining **INTENTIONALLY DEFERRED TO IMPLEMENTATION / EXECUTION-AUTHORIZATION DESIGN** as an **AUTHORIZED IMPLEMENTATION-LEVEL FORMAT CHOICE / NOT A MATERIAL D1 SEMANTIC GAP**.  The re-review independently re-derived the 19/19 closure table from the actual spec text (19 rows, contiguous 1..19, order identical to §18, zero fields lacking a JSON type, zero fields lacking a value/source or rule reference), performed an **ordinal, case-sensitive** comparison of the 13 `non_claims` elements against the required strings (**0 mismatches**), verified that the §20 → array mapping is bijective with no remainder on either side, confirmed the prior accepted design was **byte-unmodified** (the spec blob object id is identical at `6ad917b` and `8738651a`), verified the five protected Recovery-R2 artifacts hash-identical, confirmed the Oracle-R2 script SHA-256 is still `22c5fbd61da609e6cc39e973be6030d4c360019ed1f56e69ca45f92fa1689c17` (matching the frozen `oracle_r2_script_sha256` recorded in the D1 spec), confirmed `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED` and all downstream gate states unchanged, and found no range regression and no new blocking finding.  The one recorded **P3** is non-blocking and purely presentational: the §49 closure table's `terminating_error` row states its JSON type as the union ``object **OR** `null` ``, which is a faithful description already frozen by §31 and §33.4 and is unambiguous under the §50 closure routes.  A **REVIEW-COVERAGE CORRECTION** remains recorded (the prior Corrective R1 review verified the eight listed closed sub-schemas but did not cross-check every top-level member of the 19-field schema for an explicit scalar type/value/source rule or sub-schema binding), explicitly **not** as evidence of malicious or invalid prior review, and **future D1 design reviews MUST include a 19/19 top-level field closure audit**.  The accepted clarification spec is **byte-frozen** at `29f0f9cc…` (54910 bytes, 1161 lines, UTF-8, no BOM, LF-only, no NUL) and was **not** modified by this bookkeeping round, which changed only this file and `docs/v0.3/V03E_ACCEPTANCE.md` (two-file delta, no third path).  Nothing downstream changed: no D1 executable, execution-authorization document, claim, evidence, manifest, result or output directory was created and all D1 operational artifacts remain **ABSENT**; budgets remain **D1 AUTHORIZATION USE = `UNAVAILABLE / NOT YET GRANTED`**, **D1 DIAGNOSTIC ATTEMPT = `UNAVAILABLE / NOT YET GRANTED`** and **D1 LISTENER QUERY EXECUTION = `NOT AUTHORIZED`**; the standing **ERROR STRING MAXIMUM REPRESENTATION RULE = NOT YET FROZEN / NON-BLOCKING DESIGN OBSERVATION** P3 is unchanged with no truncation invented; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED` is untouched; Recovery-R2 authorization use and attempt remain **SPENT / NOT REUSABLE**; Mode-B is **BLOCKED / NOT RUN**; `P6 = UNPROVEN / UNSATISFIED`; **G0.5 = NOT CLOSED**; G0.5 execution / Case-C / v0.3-E implementation **NOT AUTHORIZED**; `G1`/`G2` **NOT RUN**; `adopt_completed_turn` **DISABLED**; **PATH C = NO STATIC BASIS / NOT AUTHORIZED**; **PATH D = NOT AUTHORIZED**.  This acceptance authorizes **no** execution and grants **no** budget: the next stage is a **separate D1 implementation / execution-authorization candidate round**, and this bookkeeping performs 0 listener-query executions, 0 `Get-NetTCPConnection` calls, 0 claim creations, 0 evidence/manifest/result/output-directory creations, 0 Oracle executions, 0 target/listener/process probes, 0 OpenCode starts/restarts, 0 HTTP, 0 provider/model calls, 0 SIC, 0 Mode-B, 0 G0.5/G1/G2, 0 config mutations, 0 Recovery-R2/R1 mutations and 0 runtime/test/dependency/version changes.

**D1 IMPLEMENTATION / EXECUTION-AUTHORIZATION CANDIDATE — post-C1 round.**  With the C1 clarification accepted and frozen (`b8f8a67…` / `29f0f9cc…`, `D1_TOPLEVEL_FIELD_CLOSURE = 19 / 19 CLOSED`) and its acceptance bookkeeping independently confirmed at `80e9378…`, the previously stopped implementation round was resumed and this round **constructed** the D1 implementation and execution-authorization **candidates** — it did **not** execute anything.  Two new tracked source artifacts now exist: `docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_EXCEPTION_DIAGNOSTIC_D1_EXECUTION.ps1` (the future execution entrypoint; ASCII-only source, 0 bytes above 0x7F) and `docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_EXCEPTION_DIAGNOSTIC_D1_EXECUTION_AUTHORIZATION.md` (the self-sufficient execution-authorization contract).  The script takes three **mandatory** future provenance parameters (`-AcceptedAuthorizationCommit`, `-ExpectedAuthorizationSha256`, `-ExpectedScriptSha256`) and deliberately embeds **neither** its own future commit id **nor** its own expected SHA-256 — the self-reference audit found only already-accepted historical identities (design commit `b8f8a67…`, spec hash `29f0f9cc…`, source bookkeeping `93e44fe6…`, R2 evidence/manifest/result and both R2 claim hashes, config `b5e4abab…`), so **D1_SELF_REFERENCE_MODEL = SOUND**.  The C1-closed top-level constants are implemented exactly: `schema_version = devrelay-etb-query-diagnostic-d1-v1`, `diagnostic_mode = "QUERY_EXCEPTION_DIAGNOSTIC_D1"` (constant, never runtime-variable), `endpoint = "http://127.0.0.1:4096"` (a **string scalar**, explicitly **not** an object and **not** inheriting the `devrelay-etb-v1-r2` endpoint object schema), with `configured_base_url` kept **distinct** and obtained only through the accepted frozen Recovery-R2 config reader (never derived by copying the endpoint constant), and the precondition requiring `configured_base_url == endpoint == "http://127.0.0.1:4096"` before any claim consumption.  The `non_claims` field emits **exactly 13 strings in exact order**, frozen verbatim with no split, join, rewording or reorder.  The script implements the full accepted contract: the closed authorization and attempt claim schemas (12 ordered fields, final `state=CONSUMED`, differing only in `schema_version`), the exact claim serialization (UTF-8, no BOM, LF-only, one terminal LF, `<field>=<value>` per line, no quoting, no spaces around `=`), the four permanently distinct D1 claim paths with `File.Exists` **or** `Directory.Exists` occupancy and fail-closed behaviour, the 14-step atomic consumption mechanics (TEMP `CreateNew` → write → `Flush(true)` → close → readback → two-argument `Move` → readback → SHA-256) with the **successful TEMP `CreateNew` as the irreversible consumption boundary**, the frozen consumption order (`PRECONDITIONS → AUTH → ATTEMPT → directory → availability → zero-or-one query → evidence → manifest → result → STOP`), and all sixteen preconsumption preconditions A–P stopping **before** any claim consumption.  Exactly **one** executable listener-query command site exists — statically verified — with the exact accepted shape (`Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 4096 -State Listen -ErrorAction SilentlyContinue -ErrorVariable qerr`), a one-query maximum, no retry, no fallback, and a narrow `Get-Command` availability probe that is **not** the listener query.  The eight-value observation vocabulary is the only classifier output; the 15-field ErrorRecord normalization and the `terminating_error` / `error_records` channel separation are implemented with the deterministic no-duplication rule (at most **one** final `qerr` entry suppressed, and only on a normalized 14-payload-field match excluding `source`); row evidence is restricted to the four accepted fields in order; the 19-field top-level evidence order is emitted exactly; the accepted null/empty contract is implemented (`""` for unavailable strings, `[]` for empty arrays, `null` for an absent `terminating_error`, JSON integers for required counters, `null`-or-integer for the two row integer properties); the C1-delegated timestamp format is frozen as `[DateTimeOffset]::UtcNow.ToString("yyyy-MM-dd'T'HH:mm:ss.fffffff'Z'", InvariantCulture)` for both timestamps with no local times; JSON uses ordered structures with `ConvertTo-Json -Depth 12 -Compress` (the accepted Oracle-R2 precedent; depth 12 verified sufficient, deepest object depth 3) and UTF-8/no-BOM/LF-only framing with exactly one terminal LF; atomic no-overwrite publication runs evidence → manifest → result; the manifest binds the evidence file only in the exact one-line format and never self-lists; and the result records the required provenance, hashes, outcome, both claims as `CONSUMED`, the diagnostic authority state `CANDIDATE / REQUIRES INDEPENDENT RESULT REVIEW`, `authoritative_etb_semantic_result=ETB_UNSATISFIED`, and the non-claims, without duplicating full ErrorRecord strings.  `DIAGNOSTIC_HARNESS_INVALID` is published only when the closed schema can still be constructed truthfully, otherwise nothing is fabricated and the control state becomes an operational harness/publication failure **outside** the `query_outcome` vocabulary; publication failure after consumption is reported as **D1 PUBLICATION INCOMPLETE**, an execution-control state that is not `ETB_UNSATISFIED` and not any listener observation; and a small closed exit-code mapping is frozen (`0` success, `10` precondition failure, `20` auth-claim failure, `30` attempt-claim failure, `40` post-consumption harness failure, `50` publication incomplete) and implemented identically in script and contract.  Static AST validation of the script returned **syntax errors = 0**, **`Get-NetTCPConnection` execution sites = exactly 1** with the exact required parameters, **dynamic invocation sites = 0**, and **zero** sites for `Invoke-Expression`, `Start-Process`, `Get-CimInstance`, `Get-WmiObject`, `Get-Process`, `Test-NetConnection`, `netstat`, `Invoke-WebRequest` and `Invoke-RestMethod` (confirmed by both AST command-site enumeration and a full-text scan).  The standing **ERROR STRING MAXIMUM REPRESENTATION RULE = NOT YET FROZEN / NON-BLOCKING DESIGN OBSERVATION** P3 is unchanged and is **not** claimed closed; this candidate serializes full observed values with no truncation and no hashing.  Both new files are UTF-8, no BOM, LF-only, no NUL, and worktree bytes equal their committed blobs after the candidate commit.  Candidate provenance (values only, **not** accepted): `diagnostic_d1_authorization_commit` = this candidate HEAD, `diagnostic_d1_authorization_sha256` = SHA-256 of the authorization contract, `diagnostic_d1_script_sha256` = SHA-256 of the script — none embedded in the files and none to be amended afterwards.  Nothing was executed: this round ran **0** listener queries, **0** `Get-NetTCPConnection` calls, **0** claim creations, **0** evidence/manifest/result/output-directory creations, **0** Oracle executions, **0** target/listener/process live probes, **0** OpenCode starts/restarts, **0** HTTP, **0** provider/model calls, **0** SIC, **0** Mode-B, **0** G0.5/G1/G2, **0** config mutations, **0** Recovery-R2/R1 mutations and **0** runtime/test/dependency/version changes.  Current authority after this candidate: **D1 DESIGN = ACCEPTED / FROZEN** at `b8f8a67…` / `29f0f9cc…`; **D1 IMPLEMENTATION = CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED**; **D1 EXECUTION AUTHORIZATION = CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE**; **D1 AUTHORIZATION USE = `UNAVAILABLE / NOT YET GRANTED`**; **D1 DIAGNOSTIC ATTEMPT = `UNAVAILABLE / NOT YET GRANTED`**; **D1 LISTENER QUERY EXECUTION = `NOT AUTHORIZED`**; **D1 CLAIMS = ABSENT**; **D1 RESULT = ABSENT**; the predecessor `6ad917b…` remains **PREVIOUSLY ACCEPTED / HISTORICAL AUTHORITATIVE PREDECESSOR / SUPERSEDED BY ACCEPTED C1 CLARIFICATION** and is **not** relabelled rejected; and `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED` is untouched, with Recovery-R2 **SPENT / NOT REUSABLE**, Mode-B **BLOCKED / NOT RUN**, `P6 = UNPROVEN / UNSATISFIED`, **G0.5 = NOT CLOSED**, G0.5 execution / Case-C / v0.3-E implementation **NOT AUTHORIZED**, `G1`/`G2` **NOT RUN**, `adopt_completed_turn` **DISABLED**, **PATH C = NO STATIC BASIS / NOT AUTHORIZED** and **PATH D = NOT AUTHORIZED**.

**D1 OVERLAP-SEMANTICS DESIGN CLARIFICATION C2 — OWNER SELECTED OPTION B.**  The independent implementation review of the candidate `a25e15416dba2c1d31918e6b41824204c219d948` returned **REQUEST_CHANGES — V0.3-E ETB QUERY_EXCEPTION DIAGNOSTIC D1 IMPLEMENTATION / EXECUTION-AUTHORIZATION CANDIDATE** with **P0 = 0, P1 = 0, P2 = 2, P3 = 2**, whose two blocking findings were **P2-1 = D1 DIRECTORY OCCUPANCY RACE / REUSE GAP (implementation-only correction)** and **P2-2 = QERR / TERMINATING OVERLAP SEMANTICS (design clarification required)**: the candidate silently suppressed one final `qerr` record when its normalized 14-field payload matched the terminating `catch` record, which the accepted design neither explicitly authorized nor logically required, and which changes observable D1 evidence.  A read-only owner decision packet established that the accepted design at `b8f8a67…` / `29f0f9cc…` **explicitly required** the opposite default — §12 states "all `qerr` entries are preserved for evidence", §35.1 states that captured `qerr` entries "remain independently represented" in `error_records`, and the terms `suppress` / `dedup` / `remove` / `drop` / `de-dup` appeared **zero** times in the accepted spec — so the suppression was an unauthorized evidence transformation, and the owner was presented with two options: **OPTION A — PRESERVE ALL ACTUAL QERR RECORDS** (raw channel preservation, zero semantic delta) and **OPTION B — SUPPRESS EXACTLY ONE FINAL NORMALIZED QERR RECORD WHEN IT DUPLICATES THE TERMINATING CATCH RECORD** (a normalization-time cross-channel policy carrying a material semantic delta relative to the prior text).  The human owner then selected, as a final decision for the C2 round, **OWNER DECISION = OPTION B**, and this round — **design clarification only, with no implementation modification** — has added the normative **C2 — NORMALIZED TERMINATING-DUPLICATE SUPPRESSION** section to the D1 design and narrowly cross-qualified the prior preservation wording so that the design now means: **ALL actually captured `qerr` entries are preserved in observed order EXCEPT for the one narrowly authorized C2-B cross-channel suppression**, which applies **only** to the **final** observed `qerr` record, **only** when a terminating `catch` exists, **only** when **all 14** normalized payload fields excluding `source` (`fully_qualified_error_id`, `category`, `category_activity`, `category_reason`, `category_target_name`, `category_target_type`, `exception_type`, `exception_message`, `exception_hresult`, `inner_exception_type`, `inner_exception_message`, `error_details_message`, `invocation_position_message`, `script_stack_trace`) compare **ordinal-string equal**, and **at most once**.  Normalization precedes comparison and reuses the accepted closed 15-field ErrorRecord schema with every field a JSON string and unavailable values `""`; comparison excludes `source` and nothing else; case folding, culture-aware comparison, partial comparison, message-only comparison, FQEI-only comparison, exception-type-only comparison, reference identity, object identity, hash comparison and timing heuristics are all **prohibited**.  Eligibility requires all three of: a terminating catch exists; at least one `qerr` record exists; and the candidate record is the **final** observed `qerr` record — no earlier `qerr` record is ever eligible.  All earlier `qerr` entries remain **unconditionally**, even when payload-identical to the catch record or to each other; **no `qerr`-to-`qerr` deduplication** is permitted; and **at most one** record may ever be suppressed per execution.  Published `error_records` order equals the original observed `qerr` order with at most the single eligible final entry omitted, with no sorting, regrouping, merge or rewrite; `terminating_error` stays **catch-only** and `error_records` stays **qerr-only**, with no `qerr`-only record populating `terminating_error` and no catch-only synthetic copy inserted into `error_records`.  Because disjoint capture paths do **not** imply disjoint payload values, the design now states explicitly that the two channels may expose records whose normalized 14-field payloads are equal, and that C2 authorizes **exactly one** normalization-time cross-channel publication transformation and no other; the rule is an **OWNER-SELECTED EVIDENCE NORMALIZATION POLICY**, not a claim that PowerShell guarantees the two channels to be semantically distinct.  A further non-inference rule is frozen: the suppression condition does **not** establish as fact that the two records are the same underlying PowerShell event — **payload equality = suppression eligibility, NOT proof of runtime event identity**.  The raw-versus-published distinction is frozen without touching the schema: `error_records` represents **published** `qerr` evidence and is not necessarily equal in length to the raw `qerr` count (published = raw − 1 when the final record is suppressed, otherwise published = raw); **no** new top-level raw-`qerr`-count field is added and the **19-field top-level schema is unchanged** (`D1_TOPLEVEL_FIELD_CLOSURE = 19 / 19 CLOSED`).  Query-outcome classification is explicitly required to use the **actual raw `qerr` capture state BEFORE** optional suppression, and the design records the consistency verification that **no** internal contradiction arises: both `ERROR_RECORDS_*` classes require `terminating_error = null` (i.e. no terminating catch) while C2-B eligibility requires a terminating catch to exist, so **C2-B can never suppress a record in either `ERROR_RECORDS_*` class** and their "one or more" representation remains satisfied under all C2-B executions; under `TERMINATING_EXCEPTION`, the already-accepted §37 case 2 admits `error_records` = "qerr entries, or `[]`", so a fully suppressed sole `qerr` record was **already** a representable outcome and no new representation rule is needed — therefore **no `C2 SECONDARY DESIGN GAP`** arises and **no `query_outcome` value is silently redefined**.  `TERMINATING_EXCEPTION` precedence is preserved (a terminating catch still yields `query_outcome = TERMINATING_EXCEPTION`), and C2 suppression affects **only** published `error_records`, never `terminating_error`, `query_outcome`, `row_count`, `rows` or the query invocation count.  No vocabulary value is added, removed, renamed or reinterpreted; the listener-query contract (exact `Get-NetTCPConnection` shape, maximum one query, no retry/repeat/polling/alternate command/CIM reconstruction/fallback) is unchanged; the 15-field ErrorRecord schema gains **no** duplicate flag, suppressed flag, `raw_qerr_count`, overlap flag, dedup metadata, event identity or suppression reason; and a normative eight-case C2 test matrix fixes the expected outcome for every catch/`qerr` combination (cases 1-8 suppressing `0`, `0`, `final one` → published length 0, `final one` → earlier retained, `0` → both retained, `final one only` → first retained, `0`, `0`).  The **rejected** candidate `a25e154…` remains **REQUEST_CHANGES / NOT ACCEPTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED** and is **not** retroactively approved merely because the owner selected Option B, because it still carries the **P2 directory occupancy race** and the **P3 authorization/exit-code consistency issue**, and because its provenance still binds to the pre-C2 design; it therefore requires a future corrected implementation candidate **after** C2 is accepted.  The **directory occupancy race** is carried forward unchanged as **IMPLEMENTATION-ONLY CORRECTION / OPEN**, to be fixed in that future implementation by checking `File.Exists(EvDir)` **or** `Directory.Exists(EvDir)` **after both claims are consumed and immediately before** evidence-directory creation, failing closed with exit class `40`, authorization `SPENT`, attempt `SPENT`, no directory reuse, no retry and no query if not yet invoked.  **P3-A** (**ERROR STRING MAXIMUM REPRESENTATION RULE = NOT YET FROZEN / NON-BLOCKING DESIGN OBSERVATION**) is preserved and **not** closed, with no truncation invented.  **P3-B** (unexpected internal exceptions may escape with host exit code 1 while the authorization document claims deterministic mapping into the six-code set) remains classified as an **IMPLEMENTATION / AUTHORIZATION-DOCUMENT CONSISTENCY ISSUE** and is **not** solved in C2.  The C2 candidate status is **D1 OVERLAP-SEMANTICS CLARIFICATION C2 = DESIGN CANDIDATE / OWNER OPTION B SELECTED / NOT ACCEPTED / NOT FROZEN / NOT AUTHORIZED / NOT EXECUTED**; the previously accepted design remains `b8f8a67…` / `29f0f9cc…` = **ACCEPTED / FROZEN / IMPLEMENTATION BLOCKED BY OVERLAP-SEMANTICS GAP**, and neither `diagnostic_d1_design_commit` nor `diagnostic_d1_spec_sha256` is prematurely replaced.  Only if C2 later receives independent design approval, design acceptance bookkeeping and independent bookkeeping confirmation does the C2 candidate commit become the **new** `diagnostic_d1_design_commit` and the clarified spec SHA the **new** `diagnostic_d1_spec_sha256`, at which point `b8f8a67…` becomes **PREVIOUSLY ACCEPTED / HISTORICAL AUTHORITATIVE PREDECESSOR / SUPERSEDED BY ACCEPTED C2 CLARIFICATION** — **not** REJECTED; that transition is **not** performed now.  This round changed **design only**: the rejected `.ps1` and authorization document remain **byte-identical** to candidate `a25e154` (`70052af0…` / `bca6dde5…`), the tracked delta is exactly three files (D1 spec, `CHANGELOG.md`, `V03E_ACCEPTANCE.md`) with no fourth path, and the round performed **0** listener queries, **0** `Get-NetTCPConnection` calls, **0** claim creations, **0** evidence/manifest/result/output-directory creations, **0** Oracle executions, **0** live probes, **0** OpenCode starts/restarts, **0** HTTP, **0** provider/model calls, **0** SIC, **0** Mode-B, **0** G0.5/G1/G2, **0** config mutations, **0** Recovery-R2/R1 mutations and **0** runtime/test/dependency/version changes; D1 budgets remain **`UNAVAILABLE / NOT YET GRANTED`** with **D1 LISTENER QUERY EXECUTION = `NOT AUTHORIZED`**, D1 claims and D1 result remain **ABSENT**, and `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED` is untouched with Recovery-R2 **SPENT / NOT REUSABLE**, Mode-B **BLOCKED / NOT RUN**, `P6 = UNPROVEN / UNSATISFIED`, **G0.5 = NOT CLOSED**, G0.5 execution / Case-C / v0.3-E implementation **NOT AUTHORIZED**, `G1`/`G2` **NOT RUN**, `adopt_completed_turn` **DISABLED**, **PATH C = NO STATIC BASIS / NOT AUTHORIZED** and **PATH D = NOT AUTHORIZED**.

**D1 DESIGN ACCEPTANCE BOOKKEEPING — OVERLAP-SEMANTICS CLARIFICATION C2 ACCEPTED.**  The independent design review of the C2 candidate `14b85bd2365d500ef87f357aeecb94de14211cc9` / `69b7cfda172658fe6c4e726430274a27a6dffb4c4d1c90a374d79feb6956e35d` issued **APPROVE V0.3-E ETB QUERY_EXCEPTION DIAGNOSTIC D1 OVERLAP-SEMANTICS DESIGN CLARIFICATION C2** with **P0 = 0, P1 = 0, P2 = 0, P3 = 2**, so C2 is now **ACCEPTED / FROZEN** (subject to independent bookkeeping confirmation of this bookkeeping commit) and the active D1 design state is **ACCEPTED / FROZEN / NOT IMPLEMENTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED**.  Because the clarification received independent approval **and** this acceptance bookkeeping, the successor-provenance transition frozen by C2 (§56.21, §29 of that round) now takes effect: **`diagnostic_d1_design_commit = 14b85bd2365d500ef87f357aeecb94de14211cc9`** and **`diagnostic_d1_spec_sha256 = 69b7cfda172658fe6c4e726430274a27a6dffb4c4d1c90a374d79feb6956e35d`** are the new accepted D1 design provenance for all future D1 work.  These values refer to the **accepted C2 design candidate** and **MUST NOT** be replaced by the bookkeeping commit created in this round: **the acceptance-bookkeeping commit does NOT become `diagnostic_d1_design_commit`**, and any later bookkeeping confirmation, corrected implementation candidate, execution-authorization candidate, execution HEAD or diagnostic-result review must continue to bind the D1 design to `14b85bd…` and `69b7cfda…` unless a later independently accepted design clarification explicitly supersedes C2.  The previously accepted design `b8f8a67beac154894e496aaa601fa0a4cd4e9905` / `29f0f9cc1632f2f344f5cb4e01d25a832ba9acc78caedbdd43861b7d68ac4154` is **NOT** relabelled REJECTED, INVALID or NEVER ACCEPTED: it is now **PREVIOUSLY ACCEPTED / HISTORICAL AUTHORITATIVE PREDECESSOR / SUPERSEDED BY ACCEPTED C2 CLARIFICATION**, and its prior C1 acceptance remains historically valid; its tracked spec blob was independently re-verified as still `29f0f9cc…` at `b8f8a67`.  Accepted C2 freezes the owner-selected evidence policy **OPTION B — NORMALIZED TERMINATING-DUPLICATE SUPPRESSION** with exactly these high-level semantics: normalization before comparison; comparison excludes `source` only; exact **14-field ordinal-string equality**; **only the final observed `qerr` record is eligible**; suppress **exactly one if and only if all 14 fields match**; **at most one** suppression per execution; **all earlier `qerr` retained** unconditionally; **surviving order preserved**; **no `qerr`-to-`qerr` deduplication**; `terminating_error` remains **catch-only**; `error_records` remains **qerr-only**; **payload equality is suppression eligibility, not proof of event identity**; the classifier uses the **raw pre-suppression `qerr` state**; the `query_outcome` vocabulary is **unchanged**; and the **one-query rule is unchanged** (this summary is normative-summary reference only and does not redefine the frozen spec §56).  The independent review's static findings are recorded: **`D1_C2_INTERNAL_CONSISTENCY = PASS`**, **`D1_C2_CASE_MATRIX = 8/8 DETERMINISTIC`**, **`D1_C2_EXECUTOR_CHOICE = NONE`** and **`C2 SECONDARY DESIGN GAP = NOT FOUND`** — these are **static design-review findings only**, not runtime execution results (no listener query was ever run).  Two non-blocking **P3** observations are preserved and **not** converted into blockers, and **P3 = 0 is NOT claimed**: **P3-1** — Option B has an inherent observability cost, because the published evidence contains neither a raw-`qerr`-count field nor a suppression flag, so a later reviewer cannot reconstruct solely from published evidence whether the raw `qerr` count was `n` or `n + 1` with one C2-B suppression; this is classified **P3 / OWNER-KNOWN OPTION-B INFORMATION-LOSS TRADEOFF / NON-BLOCKING** (the owner selected this policy with that tradeoff recorded in the decision packet).  **P3-2** — the §56.14 sentence "already a representable outcome" refers literally to `[]` being an already-representable **value** (pre-C2 it corresponded to "no `qerr` captured", post-C2 it also covers "sole `qerr` suppressed"); the sentence does **not** claim that the post-C2 trigger condition existed before C2 and is technically accurate, but a fast reader could misread it — classified **P3 / WORDING-ONLY / NON-BLOCKING**.  C2 spec bytes are frozen and were **not** modified by this bookkeeping: the worktree file, the blob at `14b85bd` and the post-bookkeeping HEAD blob are **byte-identical** at SHA-256 `69b7cfda…` (68388 bytes, UTF-8 valid, no BOM, LF-only, no CR, no NUL).  The **rejected** implementation candidate `a25e15416dba2c1d31918e6b41824204c219d948` is untouched and remains **REQUEST_CHANGES / NOT ACCEPTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED**: this acceptance does **not** retroactively approve it, because it still carries **P2-1 = D1 DIRECTORY OCCUPANCY RACE / REUSE GAP** (carried forward as **IMPLEMENTATION-ONLY CORRECTION / OPEN**, to be fixed in a future corrected implementation by checking `File.Exists(EvDir)` **or** `Directory.Exists(EvDir)` after both claims are consumed and immediately before evidence-directory creation, failing closed with exit class `40`, authorization `SPENT`, attempt `SPENT`, no directory reuse, no retry and no query if not yet invoked) and **P3-B = unexpected exception / six-code mapping mismatch** (an **IMPLEMENTATION / AUTHORIZATION-DOCUMENT CONSISTENCY ISSUE**, not solved here), and because its provenance still binds to the pre-C2 design.  The standing **P3-A** (**ERROR STRING MAXIMUM REPRESENTATION RULE = NOT YET FROZEN / NON-BLOCKING DESIGN OBSERVATION**) is preserved and **not** closed, with no truncation invented.  This acceptance authorizes **no** execution and grants **no** budget: D1 budgets remain **`UNAVAILABLE / NOT YET GRANTED`** with **D1 LISTENER QUERY EXECUTION = `NOT AUTHORIZED`**, D1 claims and D1 result remain **ABSENT**, all reserved D1 operational paths remain **ABSENT**, and no claim, evidence, manifest, result or evidence directory was created.  `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED` is untouched; Recovery-R2 authorization use and attempt remain **SPENT / NOT REUSABLE**; Mode-B is **BLOCKED / NOT RUN**; `P6 = UNPROVEN / UNSATISFIED`; **G0.5 = NOT CLOSED**; G0.5 execution / Case-C / v0.3-E implementation **NOT AUTHORIZED**; `G1`/`G2` **NOT RUN**; `adopt_completed_turn` **DISABLED**; **PATH C = NO STATIC BASIS / NOT AUTHORIZED**; **PATH D = NOT AUTHORIZED**.  This bookkeeping round changed exactly two files (`CHANGELOG.md` and `docs/v0.3/V03E_ACCEPTANCE.md`) with no third path, performed **0** listener queries, **0** `Get-NetTCPConnection` calls, **0** claim creations, **0** evidence/manifest/result/output-directory creations, **0** Oracle executions, **0** live probes, **0** OpenCode starts/restarts, **0** HTTP, **0** provider/model calls, **0** SIC, **0** Mode-B, **0** G0.5/G1/G2, **0** config mutations, **0** Recovery-R2/R1 mutations and **0** runtime/test/dependency/version changes; the next stage is an **independent D1 C2 design acceptance bookkeeping confirmation**, after which a **corrected** implementation / execution-authorization candidate round may be constructed against the newly accepted C2 design.

**D1 CORRECTED IMPLEMENTATION / EXECUTION-AUTHORIZATION CANDIDATE — post-C2 round.**  With the C2 clarification accepted and frozen (`14b85bd2365d500ef87f357aeecb94de14211cc9` / `69b7cfda172658fe6c4e726430274a27a6dffb4c4d1c90a374d79feb6956e35d`) and its acceptance bookkeeping independently confirmed at `ac8d23089c33e4d3b3c8960e8cdeea3171dff695`, this round **constructed a corrected D1 implementation and execution-authorization candidate** — it did **not** execute anything.  Starting identity was verified before mutation (HEAD `ac8d230…`, `HEAD^` `14b85bd…`, branch `v0.3-e-recovery-reconciliation`, tracked worktree clean, staged empty, untracked = the historical 12, package `0.1.0`, tag `v0.1.0` only, all D1 operational artifacts absent), a duplicate-candidate gate found **no** pre-existing corrected descendant (`ac8d230` has no child in any ref; the only commit ever touching the D1 execution paths is the rejected `a25e154…`, which is an ancestor), the accepted design was byte-frozen before and after construction (`69b7cfda…`, spec blob `aac90fc4e9a03bd11c6342137601703dde5406da` identical in the worktree, at `14b85bd…` and at `ac8d230…`), and the file delta was exactly **four** paths with **one** commit: `M CHANGELOG.md`, `M docs/v0.3/V03E_ACCEPTANCE.md`, `M docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_EXCEPTION_DIAGNOSTIC_D1_EXECUTION.ps1` and `M docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_EXCEPTION_DIAGNOSTIC_D1_EXECUTION_AUTHORIZATION.md` — the accepted spec was **not** modified.  **Design-provenance rebinding:** the previous implementation binding `b8f8a67…` / `29f0f9cc…` was replaced **everywhere** (script constants, both claim-schema byte constructions, both claim records, the result file, the authorization document and this record) by the accepted C2 design `14b85bd…` / `69b7cfda…`; the earlier design is recorded as **PREVIOUSLY ACCEPTED / HISTORICAL AUTHORITATIVE PREDECESSOR / SUPERSEDED BY ACCEPTED C2 CLARIFICATION** and is **not** relabelled rejected; the bookkeeping commit `ac8d230…` is **never** used as `diagnostic_d1_design_commit`.  **C2 Option B was implemented exactly as accepted** (owner-selected **NORMALIZED TERMINATING-DUPLICATE SUPPRESSION**): normalization happens before comparison; eligibility requires a terminating catch **and** at least one `qerr` record **and** the candidate being the **final** observed `qerr` record; comparison excludes `source` **only** and covers exactly the 14 fields `fully_qualified_error_id`, `category`, `category_activity`, `category_reason`, `category_target_name`, `category_target_type`, `exception_type`, `exception_message`, `exception_hresult`, `inner_exception_type`, `inner_exception_message`, `error_details_message`, `invocation_position_message`, `script_stack_trace` in that order under **ordinal string equality**; suppression happens **if and only if** all 14 match; **exactly one** record is suppressed and **at most once per execution**; all earlier `qerr` records are retained **unconditionally** even when payload-identical; there is **no** `qerr`-to-`qerr` deduplication; surviving order is preserved; `terminating_error` stays catch-only and `error_records` stays `qerr`-only; the classifier consumes the **raw pre-suppression** `qerr` count while the **published** `error_records` reflects the optional suppression; payload equality is documented as **suppression eligibility only**, **not** proof that the two records are the same underlying PowerShell event; and **no** `raw_qerr_count`, suppression flag, duplicate flag or overlap flag was added, so top-level closure remains `19 / 19 CLOSED`.  **Blocking P2 correction:** the previously confirmed directory-occupancy race was fixed by a **post-consumption directory occupancy gate** placed after **both** claims are consumed and **immediately before** evidence-directory creation (source lines 659–662), evaluating **both** `[System.IO.File]::Exists` **and** `[System.IO.Directory]::Exists`; if either is true the harness **fails closed** with the control state reported as a post-consumption harness failure, exit class **40**, authorization **SPENT**, attempt **SPENT**, listener-query invocations **0**, and explicit `DIRECTORY_REUSE_ATTEMPTED=0`, `DIRECTORY_DELETED=0` and `CLEANUP_ATTEMPTED=0`; directory creation follows only when both checks remain false, and creation that throws or is not observed afterwards is equally terminal (exit **40**) with **no** fall-through into command availability or the query.  **Blocking P3-B correction:** the rejected authorization document claimed a closed six-code mapping while some unexpected script-body exceptions could still escape as host exit code 1; a previously unnoticed **concrete** instance of exactly that leak was found and fixed — `Get-ListenerRow` assigned to **`$pid`**, which is a PowerShell **read-only automatic variable**, so `SessionStateUnauthorizedAccessException` was raised on any query path returning at least one row with a non-null `OwningProcess`, and that helper was invoked **outside** the rejected candidate's execution-phase `try/catch`, making a host exit 1 reachable (the behaviour was verified independently in this PowerShell host before the fix).  The corrected script now carries a script-scope failure mapping plus an irreversible-stage tracker (`PRE` → `AUTH` → `ATTEMPT` → `HARNESS` → `PUBLICATION`) and explicit per-stage catches, so every reachable script-body failure maps deterministically onto the closed set **{0, 10, 20, 30, 40, 50}** — before AUTH TEMP `CreateNew` ⇒ 10, during AUTH consumption ⇒ 20, after AUTH completion through ATTEMPT completion ⇒ 30, after ATTEMPT completion ⇒ 40, during publication ⇒ 50 — and per-stage consumption is reported from an **observed** flag set only once `CreateNew` returned a stream, so **no budget rollback is inferred from an exit code** and the claim files remain the forensic source.  The authorization document now states the same boundary explicitly: the six-code contract applies **once the script body has been entered after successful parsing and mandatory parameter binding**, while parser / host / parameter-binding failures occur **outside** D1 harness entry, cannot consume a claim and **must not** be classified as a D1 diagnostic observation — **`D1_EXIT_CODE_DOC_IMPLEMENTATION_CONSISTENCY = PASS`**.  Static audit of the corrected script: **0** syntax errors, **0** bytes above `0x7F`, no BOM, LF-only, exactly one terminal LF, exactly **1** executable `Get-NetTCPConnection` site (lines 708–713), **0** dynamic second-query capability, and **0** for `Invoke-Expression`, `Invoke-Command`, `Start-Process`, `Get-CimInstance`, `Get-WmiObject`, `Get-Process`, `Test-NetConnection`, `netstat`, `Invoke-WebRequest`, `Invoke-RestMethod`, OpenCode launch and HTTP/provider/model fallback.  Standing **P3-A = ERROR STRING MAXIMUM REPRESENTATION RULE = NOT YET FROZEN / NON-BLOCKING DESIGN OBSERVATION** was **preserved unchanged**: the corrected candidate serializes complete observed accepted string values with no truncation, no hashing in place of content, no dropped long value and **no invented maximum size**, and P3-A is **not** claimed closed.  **P2 and P3-B are recorded as `CORRECTED IN THIS CANDIDATE / REQUIRES INDEPENDENT REVIEW`** and are **not** stated to be closed, accepted or resolved.  The rejected predecessor `a25e15416dba2c1d31918e6b41824204c219d948` remains **REQUEST_CHANGES / HISTORICAL REJECTED IMPLEMENTATION CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED**, was preserved byte-for-byte (its recorded script SHA-256 `70052af0fe8aa33da3f5dbb270bbffbe68d7fbcadf08677fa049ac2d5a804635` and authorization SHA-256 `bca6dde5bacf9a4f6a0034cf830d801dbe86ff6f69309db844e6a2f91a40eb54` were re-verified only as a **rejected implementation baseline**, never as accepted provenance), and was neither amended, rewritten nor relabelled; the corrected candidate is a **new descendant candidate**.  The corrected script still embeds **neither** its own future commit id **nor** its own expected SHA-256, and **no** future corrected commit, script SHA-256 or authorization SHA-256 is hard-coded in either candidate file — those values are reported externally as candidate values only, with **no** post-commit amend to embed them.  Claim schemas and serialization were preserved exactly (authorization-use and attempt-use v1 schemas, the same 12 ordered fields, `state=CONSUMED`, UTF-8 without BOM, LF-only, one terminal LF, `CreateNew` `FileShare.None` consumption, `Flush(true)`, TEMP read-back equality, two-argument `Move`, FINAL read-back equality, no overwrite, no delete, no retry) and the frozen Recovery-R2 config reader was reused verbatim (no second YAML parser, `PYTHONPATH` restored to **absence** when it did not exist, runtime-derived `configured_base_url` required to equal both `endpoint` and `http://127.0.0.1:4096`, no config mutation).  This round performed **0** script executions, **0** listener-query executions, **0** `Get-NetTCPConnection` calls, **0** claim creations/deletions, **0** D1 evidence/manifest/result/output-directory creations, **0** Oracle executions, **0** target/listener/process probes, **0** OpenCode starts, **0** HTTP, **0** provider/model calls, **0** SIC, **0** Mode-B, **0** G0.5/G1/G2 and **0** budget consumptions; the authorization/attempt budgets remain **UNAVAILABLE / NOT YET GRANTED**, D1 LISTENER QUERY EXECUTION remains **NOT AUTHORIZED**, both D1 claim paths and all six output paths remain **ABSENT**, and **D1 AUTHORIZATION USE = UNAVAILABLE / NOT YET GRANTED**, **D1 DIAGNOSTIC ATTEMPT = UNAVAILABLE / NOT YET GRANTED** and **D1 RESULT = ABSENT** are unchanged.  Corrected candidate status is therefore **D1 IMPLEMENTATION = CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED** and **D1 EXECUTION AUTHORIZATION = CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE**; the exact next stage is an **independent corrected D1 implementation / execution-authorization review**, and no execution, no diagnostic query, no claim creation, no evidence creation, no result creation, no budget consumption, no new ETB attempt and no Mode-B occurred.  Preserved states: `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED`; Recovery-R2 authorization use / attempt = `SPENT / NOT REUSABLE`; Mode-B = `BLOCKED / NOT RUN`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 = `NOT CLOSED`; G0.5 execution / Case-C / v0.3-E implementation **NOT AUTHORIZED**; `G1`/`G2` **NOT RUN**; `adopt_completed_turn` **DISABLED**; **PATH C = NO STATIC BASIS / NOT AUTHORIZED**; **PATH D = NOT AUTHORIZED**.

**LF REPRODUCIBILITY CORRECTION CANDIDATE — the corrected D1 execution candidate `764927b` received REQUEST_CHANGES on one sole blocking P2, now narrowly corrected.**  The independent corrected-implementation review verified the entire diagnostic-semantic implementation of `764927bf305b1a834a4f960875bbc6c060b141ac` (C2 Option B normalization/dedup EXACT with raw-vs-published qerr separation, post-consumption directory occupancy gate with NO_MATERIAL_GAP residual TOCTOU, script-scope trap with complete stage-transition mapping onto the closed six-code set {0,10,20,30,40,50}, `$PID` collision eliminated, all 20 preconditions before consumption, atomic claim/output publication) and rejected it **solely** for **P2 OPERATIONAL REPRODUCIBILITY DEFECT**: the D1 execution script carried only the generic `* text=auto` attribute (`eol: unspecified`) while `core.autocrlf=true`, so an ordinary future checkout/reset would materialize CRLF worktree bytes and fail the script's own PRE-G self-hash gate (fail-closed, exit 10, before any claim) — making the one-shot diagnostic unreachable in the canonical environment (the same defect class as the earlier Oracle-R2 P2-B, resolved by the accepted Oracle-R2 LF rule).  `764927b…` is therefore recorded as **REQUEST_CHANGES / HISTORICAL CORRECTED IMPLEMENTATION CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED**.  This corrective child commit pins the D1 execution script with exactly one narrow rule —
`docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_EXCEPTION_DIAGNOSTIC_D1_EXECUTION.ps1 text eol=lf` — so ordinary supported Git materialization preserves the exact LF bytes bound by `ExpectedScriptSha256`; PRE-G **remains fail-closed** (the rule improves reproducibility only and does not weaken, replace or bypass the self-integrity gate); no diagnostic semantic change; the accepted Oracle-R2 LF rule is untouched; no `*.ps1` broad rule; no unrelated attribute change; no `.ps1` content edit (the script bytes remain exactly `17dceea35333c9067c3a07857a6dc5548ef41518101794fcc6ca03127d1a7227`, CR = 0, no BOM, one terminal LF, worktree = committed canonical bytes).  Read-only verification: `git check-attr` → `text: set` / `eol: lf`; `git ls-files --eol` → `i/lf w/lf attr/text eol=lf`; `core.autocrlf` unchanged (`true`) with the path-specific rule taking precedence.  All verified implementation fixes are statically preserved (C2 Option B, raw/published qerr model, directory gate and residual TOCTOU, trap/six-code mapping, consumption accounting, automatic-variable audit, authorization-document consistency, 19-field top-level evidence closure).  Current statuses: `ETB QUERY_EXCEPTION DIAGNOSTIC D1 DESIGN = ACCEPTED / FROZEN` (`14b85bd2365d500ef87f357aeecb94de14211cc9` / `69b7cfda172658fe6c4e726430274a27a6dffb4c4d1c90a374d79feb6956e35d`, never the bookkeeping commit `ac8d230…`); **D1 IMPLEMENTATION = CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED** (now carried by this LF-corrected descendant); **D1 EXECUTION AUTHORIZATION = CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE**; **D1 AUTHORIZATION USE = UNAVAILABLE / NOT YET GRANTED**; **D1 DIAGNOSTIC ATTEMPT = UNAVAILABLE / NOT YET GRANTED**; **D1 LISTENER QUERY = NOT AUTHORIZED**; all D1 claims/output paths **ABSENT**.  Preserved downstream state: `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED`; Recovery-R2 authorization/attempt = `SPENT / NOT REUSABLE`; Mode-B = `BLOCKED / NOT RUN`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 = `NOT CLOSED`; G0.5 execution / Case-C / v0.3-E implementation **NOT AUTHORIZED**; `G1`/`G2` **NOT RUN**; `adopt_completed_turn` **DISABLED**; **PATH C = NO STATIC BASIS / NOT AUTHORIZED**; **PATH D = NOT AUTHORIZED**.  P3 status: **P3-B = CORRECTION VERIFIED BY PRIOR INDEPENDENT REVIEW / NOT YET ACCEPTED AS PART OF AN ACCEPTED IMPLEMENTATION CANDIDATE**; standing **ERROR STRING MAXIMUM REPRESENTATION RULE = NOT YET FROZEN / NON-BLOCKING DESIGN OBSERVATION** (no truncation, no hash replacement, no invented maximum).  Protected artifacts re-verified unchanged (accepted C2 spec `69b7cfda…` at `14b85bd…`, five R2 operational artifacts, Oracle-R2 script `22c5fbd6…`, config `b5e4abab…`/1897, CONFIG_ESTABLISHMENT, R1 artifacts, src/devrelay, tests, pyproject.toml).  This corrective round performed **0** script executions, **0** listener queries, **0** claim creations, **0** D1 evidence/manifest/result/output-directory creations, **0** Oracle executions, **0** live probes, **0** OpenCode starts/restarts, **0** HTTP, **0** provider/model calls, **0** SIC, **0** Mode-B, **0** G0.5/G1/G2, **0** budget consumption, **0** config mutations, **0** Recovery-R2/R1 mutations and **0** runtime/test/dependency/version changes; checkout/reset was NOT used (attribute verification was read-only); the ignored/untracked `PROJECT_MEMORY.md` persists.

**D1 CORRECTED IMPLEMENTATION / EXECUTION-AUTHORIZATION ACCEPTANCE BOOKKEEPING — LF REPRODUCIBILITY APPROVED.**  The independent review of the LF-corrected candidate `4f29ad6541def300c5361fec57357d86ea871479` issued **APPROVE DEVRELAY v0.3-E D1 LF REPRODUCIBILITY CORRECTION / CORRECTED IMPLEMENTATION / EXECUTION-AUTHORIZATION** with **P0 = 0, P1 = 0, P2 = 0, P3 = 1**, the single P3 being the standing non-blocking observation **ERROR STRING MAXIMUM REPRESENTATION RULE = NOT YET FROZEN / NON-BLOCKING DESIGN OBSERVATION**; on that verdict — and subject to independent confirmation of THIS bookkeeping commit — the corrected D1 implementation and its execution-authorization artifact are now **ACCEPTED / FROZEN / NOT EXECUTED**.  Accepted implementation provenance: **`d1_implementation_commit = 4f29ad6541def300c5361fec57357d86ea871479`** and **`d1_script_sha256 = 17dceea35333c9067c3a07857a6dc5548ef41518101794fcc6ca03127d1a7227`**, giving **D1 CORRECTED IMPLEMENTATION = ACCEPTED / FROZEN / NOT EXECUTED** at that commit/hash pair.  Accepted execution-authorization artifact provenance: **`d1_execution_authorization_commit = 4f29ad6541def300c5361fec57357d86ea871479`** and **`d1_execution_authorization_sha256 = 0573c5833adde17fdfb3ea77540bc99b23ce256b21193375eb8163ad9a4ec269`**, giving **D1 EXECUTION-AUTHORIZATION ARTIFACT = ACCEPTED / FROZEN** as the frozen authorization artifact for a **future, separately granted** execution round.  Both values point at the **APPROVED CANDIDATE** commit; the bookkeeping commit created in this round is **BOOKKEEPING PROVENANCE ONLY** and **MUST NOT** replace `d1_implementation_commit`, `d1_execution_authorization_commit` or `diagnostic_d1_design_commit` — a later bookkeeping commit is **not** implementation provenance and **not** authorization-document provenance.  Accepted design provenance is preserved without change: **`diagnostic_d1_design_commit = 14b85bd2365d500ef87f357aeecb94de14211cc9`** and **`diagnostic_d1_spec_sha256 = 69b7cfda172658fe6c4e726430274a27a6dffb4c4d1c90a374d79feb6956e35d`**; neither `ac8d230…`, nor `4f29ad6…`, nor the new bookkeeping commit is or becomes `diagnostic_d1_design_commit`.  **Acceptance of the implementation and of the authorization artifact does NOT itself authorize execution, and no such authority is asserted here.**  The independent review's verified findings are recorded as accepted-artifact conclusions: **`LF OPERATIONAL REPRODUCIBILITY P2 = CLOSED BY ACCEPTED CORRECTION`**, because the D1 execution script now carries the explicit repository materialization rule `docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_EXCEPTION_DIAGNOSTIC_D1_EXECUTION.ps1 text eol=lf` and independent review established `text = set`, `eol = lf`, index = LF and worktree = LF under `core.autocrlf = true` while the script bytes remained unchanged at `17dceea3…`; `.gitattributes` is **repository materialization policy only** and is **not** a D1 diagnostic semantic rule.  **PRE-G remains FAIL-CLOSED / EXACT-BYTE SELF-INTEGRITY GATE**: it was neither weakened nor bypassed by the LF correction, the accepted script bytes remain `17dceea35333c9067c3a07857a6dc5548ef41518101794fcc6ca03127d1a7227`, and **no normalized-hash alternative exists**.  C2 policy acceptance is preserved: **`D1_C2_OPTION_B_IMPLEMENTATION = EXACT`**, **`D1_RAW_VS_PUBLISHED_QERR_MODEL = CORRECT`**, terminating-exception precedence **PRESERVED**, and payload equality frozen as **SUPPRESSION ELIGIBILITY ONLY / NOT EVENT-IDENTITY PROOF**; the design specification is neither restated nor modified.  Further accepted implementation findings: **`D1_DIRECTORY_OCCUPANCY_CORRECTION = PASS`**, **`D1_DIRECTORY_RESIDUAL_TOCTOU = NO_MATERIAL_GAP`**, **`D1_SCRIPT_BODY_EXIT_CODE_SET = {0,10,20,30,40,50}`**, **`D1_TRAP_MODEL = SOUND`**, **`D1_CONSUMPTION_ACCOUNTING = CORRECT`**, **`D1_AUTOMATIC_VARIABLE_COLLISION_AUDIT = PASS`** and **`D1_EXIT_CODE_DOC_IMPLEMENTATION_CONSISTENCY = PASS`**, so **`P3-B = CORRECTION VERIFIED / ACCEPTED AS PART OF THIS IMPLEMENTATION ARTIFACT`** — P3-B is no longer a standing open defect and is **not** to be confused with standing **P3-A**, which remains exactly **ERROR STRING MAXIMUM REPRESENTATION RULE = NOT YET FROZEN / NON-BLOCKING DESIGN OBSERVATION**, unclosed, with no truncation, no hash substitution, no maximum representation length and no lossy serialization invented.  Historical statuses are preserved unchanged and are **not** retroactively promoted: `764927bf305b1a834a4f960875bbc6c060b141ac` remains **REQUEST_CHANGES / HISTORICAL CORRECTED IMPLEMENTATION CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED**, rejected **solely** for the missing explicit D1 script LF repository materialization contract, and it is **not** relabelled accepted merely because its child is accepted; `a25e15416dba2c1d31918e6b41824204c219d948` remains **REQUEST_CHANGES / HISTORICAL REJECTED IMPLEMENTATION CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED** with its historical findings unrewritten.  Current authority after this bookkeeping: **D1 DESIGN = ACCEPTED / FROZEN** at `14b85bd…` / `69b7cfda…`; **D1 IMPLEMENTATION = ACCEPTED / FROZEN** at `4f29ad6…` / `17dceea3…`; **D1 EXECUTION-AUTHORIZATION ARTIFACT = ACCEPTED / FROZEN** at `4f29ad6…` / `0573c583…`; but **D1 EXECUTION = NOT AUTHORIZED / NOT EFFECTIVE**, **D1 AUTHORIZATION USE = UNAVAILABLE / NOT YET GRANTED**, **D1 DIAGNOSTIC ATTEMPT = UNAVAILABLE / NOT YET GRANTED**, **D1 LISTENER QUERY = NOT AUTHORIZED**, and D1 claims, D1 evidence and D1 result all **ABSENT** — artifact acceptance is **not** collapsed into effective execution authority, and **no** statement of `EXECUTION AUTHORIZATION EFFECTIVE`, `AUTHORIZATION GRANTED`, `BUDGET GRANTED` or `READY TO EXECUTE` is made or implied.  **Independent bookkeeping confirmation is still required before any separate one-shot execution-authorization stage may even be considered.**  Preserved downstream state: `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED`; Recovery-R2 authorization / attempt = `SPENT / NOT REUSABLE`; Mode-B = `BLOCKED / NOT RUN`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 = `NOT CLOSED`; G0.5 execution / Case-C / v0.3-E execution **NOT AUTHORIZED**; `G1`/`G2` **NOT RUN**; `adopt_completed_turn` **DISABLED**; **PATH C = NO STATIC BASIS / NOT AUTHORIZED**; **PATH D = NOT AUTHORIZED**.  This bookkeeping round performed **0** script executions, **0** listener queries, **0** `Get-NetTCPConnection` calls, **0** claim creations, **0** D1 evidence/manifest/result/output-directory creations, **0** Oracle executions, **0** live probes, **0** OpenCode starts/restarts, **0** HTTP, **0** provider/model calls, **0** SIC, **0** Mode-B, **0** G0.5/G1/G2, **0** budget grants or consumptions, **0** config mutations, **0** Recovery-R2/R1 mutations, **0** `.gitattributes` changes and **0** runtime/test/dependency/version changes; the accepted C2 spec, the accepted D1 script, the accepted D1 authorization document and the `.gitattributes` rule were all re-verified unchanged by byte freeze, and the ignored/untracked `PROJECT_MEMORY.md` persists.

**D1 TWO-STAGE EFFECTIVITY GOVERNANCE CLARIFICATION — OWNER OPTION A (candidate).**  The human owner selected **OWNER DECISION = A — USE EXISTING TWO-STAGE R2 / ETB EFFECTIVITY MODEL**, and this round records the resulting governance/status clarification **as a candidate only**: **D1 TWO-STAGE EFFECTIVITY GOVERNANCE CLARIFICATION = CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE**.  It introduces **NO THIRD GRANT ARTIFACT, NO THIRD GRANT SCHEMA, NO THIRD GRANT PATH, NO THIRD GRANT-FIELD LIST and NO THIRD GOVERNANCE STAGE**; it creates no new artifact; it modifies no frozen artifact; and in this candidate round it **activates nothing** — live state remains **D1 EXECUTION = NOT AUTHORIZED / NOT EFFECTIVE**, **D1 AUTHORIZATION USE = UNAVAILABLE / NOT YET GRANTED**, **D1 DIAGNOSTIC ATTEMPT = UNAVAILABLE / NOT YET GRANTED** and **D1 LISTENER QUERY = NOT AUTHORIZED**, with D1 claims / evidence / result still **ABSENT**.  **Precedent reconstruction (read-only, from repository objects; exact wording, not paraphrase).**  `f52cb2b` *"docs(v03e): define one-shot ETB execution authorization"* created `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_AUTHORIZATION.md` with delta `A` (artifact) + `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md`; its Round-5 revision `64044fc` was independently approved; and `14c5343` *"docs(v03e): accept one-shot ETB execution authorization"* performed the acceptance bookkeeping with delta **exactly** `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md` and **no artifact modification**.  That accept round states that the accepted artifact "remains an **immutable accepted object** whose construction-time header still reads ROUND-5 CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT EXECUTED — exactly the established **immutable-artifact + approval-record + active-status** pattern … so the artifact was **not** edited by this bookkeeping; current status is represented only by this CHANGELOG and by `docs/v0.3/V03E_ACCEPTANCE.md`", and it records post-acceptance status as `ETB EXECUTION / CONFIGURATION AUTHORIZATION = ACCEPTED / GRANTED / NOT EXECUTED / AUTHORIZATION USE UNUSED / ETB ATTEMPT NOT STARTED`.  `docs/v0.3/V03E_G0_5_PRE_ETB_RECOVERY_R2_AUTHORIZATION.md` §3.6 *"Authorization lifecycle state model (frozen)"* freezes the same two-stage rule: during the design candidate `RECOVERY-R2 AUTHORIZATION = DESIGN CANDIDATE / NOT ACCEPTED / NOT GRANTED / NOT EXECUTED` with `EXECUTION AUTHORITY = NOT GRANTED`, and **after a future independently approved acceptance-bookkeeping round** `RECOVERY-R2 AUTHORIZATION = ACCEPTED / FROZEN / NOT EXECUTED` with `EXECUTION AUTHORITY = GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY`, while "Authorization use remains `UNUSED / 0 OF 1` until the authorization TEMP `CreateNew` succeeds, and the ETB attempt remains `NOT STARTED / 0 OF 1` until the attempt TEMP `CreateNew` succeeds"; §3.6 further requires that "**Independent bookkeeping confirmation is still required before any operational consumption**"; §33.1 repeats that `EXECUTION AUTHORITY` "becomes `GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY` only after a future independently approved acceptance-bookkeeping round (§3.6)"; §3.7 states that the acceptance-bookkeeping commit "is structurally identified by §11.7 and verified by §11.4; its commit hash need **not** be known in advance by any executor"; §11.7 freezes that contract (exactly **one** child commit of the accepted authorization-design commit, tracked delta exactly `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md`, **no third path**, artifact not modified); and §11.4 PRE-1 (A–F) turns those structural facts into the operational acceptance-bookkeeping HEAD gate.  **Effectivity point.**  **`D1_TWO_STAGE_EFFECTIVITY_POINT = b35777e4a14ba105c1817e2dcaebf835f77a5dff`**, and it is so **uniquely**: the accepted authorization-design commit for D1 is `d1_execution_authorization_commit = 4f29ad6541def300c5361fec57357d86ea871479`; `b35777e` is a **single-parent** commit whose `HEAD^` is exactly that commit (§11.4 B–C); its tracked delta against that parent is exactly `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md` with **no third path** (§11.4 D); at it the authorization artifact is **byte-identical** to the `4f29ad6` blob and hashes to `0573c583…` (§11.4 E); and every protected artifact is unchanged across it (§11.4 F).  The only competing reading — a *prospective* effectivity point at a later clarification-bookkeeping commit — is **structurally excluded** rather than merely disfavoured: such a commit's parent would be `b35777e`, not `4f29ad6`, so it fails §11.4-C, and §11.7 permits exactly **one** child of the accepted authorization-design commit.  The earlier `D1 EXECUTION = NOT AUTHORIZED / NOT EFFECTIVE` and "future, separately granted execution round" wording is therefore recorded as the **governance inconsistency being clarified**, not as a third lifecycle stage.  **No retroactive execution claim.**  This clarification distinguishes governance effectivity semantics from historical runtime activity and asserts **no** historical operation: D1 was **not** executed, **no** listener query occurred, **no** claim was consumed, **no** budget was consumed, **no** evidence and **no** result ever existed, and `D1 AUTHORIZATION USE = UNUSED / 0 OF 1` and `D1 DIAGNOSTIC ATTEMPT = NOT STARTED / 0 OF 1` remain historical realities.  It corrects authority semantics only.  **Post-effectivity mapping (frozen exact vocabulary, derived from the precedents above and inventing no label).**  Once this clarification's own independent review, acceptance bookkeeping and independent bookkeeping confirmation have completed, the Option-A interpretation becomes authoritative and recognises `b35777e…` as the historical lifecycle effectivity point, mapping live authority to: **`D1 EXECUTION AUTHORITY = GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY`** (R2 §3.6 vocabulary, matching the ETB `ACCEPTED / GRANTED / NOT EXECUTED` record); **`D1 AUTHORIZATION USE = UNUSED / 0 OF 1`** (R2 §3.6 vocabulary, matching ETB `AUTHORIZATION USE UNUSED`); **`D1 DIAGNOSTIC ATTEMPT = NOT STARTED / 0 OF 1`** (R2 §3.6 vocabulary, matching ETB `ETB ATTEMPT NOT STARTED`); and **`D1 LISTENER QUERY AUTHORITY` carried by that same one-shot grant — `NOT EXECUTED`, `MAXIMUM 1` invocation**, the accepted query remaining exactly `Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 4096 -State Listen -ErrorAction SilentlyContinue -ErrorVariable qerr` with no retry, no repeat, no polling, no second listener query, no alternate listener command and no fallback.  One-shot non-reuse is unchanged: authorization use `1 OF 1`, diagnostic attempt `1 OF 1`, listener query `MAXIMUM 1`, claim consumption irreversible, no retry, no reuse.  **No new governance layer.**  Option A introduces **no** approval or grant stage between effectivity and the already-frozen pre-execution gates: the precise next operational step remains the existing, already-frozen D1 pre-execution sequence inside `docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_EXCEPTION_DIAGNOSTIC_D1_EXECUTION.ps1` (its preconditions A–P and the LF materialization requirement), invoked by the unchanged accepted invocation `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_EXCEPTION_DIAGNOSTIC_D1_EXECUTION.ps1" -AcceptedAuthorizationCommit "4f29ad6541def300c5361fec57357d86ea871479" -ExpectedAuthorizationSha256 "0573c5833adde17fdfb3ea77540bc99b23ce256b21193375eb8163ad9a4ec269" -ExpectedScriptSha256 "17dceea35333c9067c3a07857a6dc5548ef41518101794fcc6ca03127d1a7227"` — not executed here, with no invented mandatory parameter and no new substantive gate.  **Provenance preservation.**  Authoritative design `14b85bd2365d500ef87f357aeecb94de14211cc9` / `69b7cfda172658fe6c4e726430274a27a6dffb4c4d1c90a374d79feb6956e35d`; accepted implementation `4f29ad65…` / `17dceea3…`; accepted execution-authorization artifact `4f29ad65…` / `0573c583…`; confirmed acceptance bookkeeping `b35777e…`; clarification candidate = the commit carrying this text, which is **not** design provenance, **not** implementation provenance and **not** authorization-artifact provenance.  Historical statuses are unchanged and not rewritten: `764927bf305b1a834a4f960875bbc6c060b141ac` = **REQUEST_CHANGES / HISTORICAL CORRECTED IMPLEMENTATION CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED**; `a25e15416dba2c1d31918e6b41824204c219d948` = **REQUEST_CHANGES / HISTORICAL REJECTED IMPLEMENTATION CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED**.  Standing **P3-A = ERROR STRING MAXIMUM REPRESENTATION RULE = NOT YET FROZEN / NON-BLOCKING DESIGN OBSERVATION** is untouched and unclosed, with no truncation, no hash substitution and no invented maximum.  Preserved downstream state: `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED`; Recovery-R2 authorization / attempt = `SPENT / NOT REUSABLE`; Mode-B = `BLOCKED / NOT RUN`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 = `NOT CLOSED`; G0.5 execution / Case-C / v0.3-E execution **NOT AUTHORIZED**; `G1`/`G2` **NOT RUN**; `adopt_completed_turn` **DISABLED**; **PATH C = NO STATIC BASIS / NOT AUTHORIZED**; **PATH D = NOT AUTHORIZED**.  This clarification round performed **0** script executions, **0** listener queries, **0** `Get-NetTCPConnection` calls, **0** claim creations, **0** D1 evidence/manifest/result/output-directory creations, **0** Oracle executions, **0** live probes, **0** OpenCode starts, **0** HTTP, **0** provider/model calls, **0** SIC, **0** Mode-B, **0** G0.5/G1/G2, **0** budget grants or consumptions, **0** frozen-artifact modifications and **0** runtime/test/dependency/version changes.

**D1 TWO-STAGE EFFECTIVITY GOVERNANCE CLARIFICATION ACCEPTANCE BOOKKEEPING — Owner Option A accepted (bookkeeping only; nothing executed, no budget granted or consumed).**  The independent design review issued *APPROVE V0.3-E D1 TWO-STAGE EFFECTIVITY GOVERNANCE CLARIFICATION DESIGN CANDIDATE* with severity **P0 = 0, P1 = 0, P2 = 0, P3 = 1**; the accepted clarification candidate is `75313c981afcced2bd669ce59993277c4c7d1ee1` (parent `b35777e4a14ba105c1817e2dcaebf835f77a5dff`, the independently confirmed D1 implementation/execution-authorization acceptance bookkeeping).  **Owner decision recorded: OPTION A — USE EXISTING TWO-STAGE R2 / ETB EFFECTIVITY MODEL**, with the accepted governance conclusions **NO THIRD GRANT ARTIFACT / NO THIRD GRANT SCHEMA / NO THIRD GRANT PATH / NO THIRD GRANT-FIELD LIST / NO THIRD GOVERNANCE STAGE**.  **Permanently recorded clarification provenance:** `d1_two_stage_effectivity_clarification_commit = 75313c981afcced2bd669ce59993277c4c7d1ee1`; this acceptance-bookkeeping commit is **bookkeeping provenance only** and explicitly does **not** replace the clarification commit, and no later bookkeeping-confirmation, implementation, execution-authorization, operational or result-review HEAD may substitute for it.  **Preserved provenance, unchanged:** accepted D1 design `diagnostic_d1_design_commit = 14b85bd2365d500ef87f357aeecb94de14211cc9` / `diagnostic_d1_spec_sha256 = 69b7cfda172658fe6c4e726430274a27a6dffb4c4d1c90a374d79feb6956e35d`; accepted D1 implementation `d1_implementation_commit = 4f29ad6541def300c5361fec57357d86ea871479` / `d1_script_sha256 = 17dceea35333c9067c3a07857a6dc5548ef41518101794fcc6ca03127d1a7227`; accepted D1 execution-authorization artifact `d1_execution_authorization_commit = 4f29ad6541def300c5361fec57357d86ea871479` / `d1_execution_authorization_sha256 = 0573c5833adde17fdfb3ea77540bc99b23ce256b21193375eb8163ad9a4ec269`; neither `75313c9…` nor this new bookkeeping HEAD substitutes for any of them.  **Accepted effectivity point: `D1_TWO_STAGE_EFFECTIVITY_POINT = b35777e4a14ba105c1817e2dcaebf835f77a5dff`** — ACCEPTED GOVERNANCE INTERPRETATION / FROZEN SUBJECT TO INDEPENDENT BOOKKEEPING CONFIRMATION; `b35777e…` is the **historical lifecycle effectivity point only** — this record does **not** state that D1 execution occurred at `b35777e…` and does **not** state that any claim, budget or query was consumed there; it is a governance-effectivity interpretation.  **Historical runtime facts preserved exactly:** D1 execution = **NEVER OCCURRED**; listener query = **NEVER OCCURRED**; authorization-use claim = **NOT CONSUMED**; attempt-use claim = **NOT CONSUMED**; authorization-use consumption = **0 OF 1**; diagnostic-attempt consumption = **0 OF 1**; evidence = **ABSENT**; result = **ABSENT** — runtime activity is **never** inferred from lifecycle effectivity.  **Accepted post-effectivity authority state (R2 §3.6 vocabulary mapped to D1 under Option A; exact labels, no invented alternatives):** `D1 EXECUTION AUTHORITY = GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY`; `D1 AUTHORIZATION USE = UNUSED / 0 OF 1` (capacity 1 OF 1 distinguished from consumption state UNUSED / 0 OF 1); `D1 DIAGNOSTIC ATTEMPT = NOT STARTED / 0 OF 1` (capacity 1 OF 1 distinguished from consumption state NOT STARTED / 0 OF 1); `D1 LISTENER QUERY = NOT EXECUTED` with `LISTENER QUERY INVOCATION = MAXIMUM 1` (the listener query is the object of the accepted one-shot execution authority; no new query-authority label invented).  **Temporal distinction for this bookkeeping round (mandatory):** the clarification does **not** become operationally authoritative until **this** bookkeeping commit itself receives independent confirmation, so the live state preserved here remains `D1 EXECUTION = NOT AUTHORIZED / NOT EFFECTIVE`; `D1 AUTHORIZATION USE = UNAVAILABLE / NOT YET GRANTED`; `D1 DIAGNOSTIC ATTEMPT = UNAVAILABLE / NOT YET GRANTED`; `D1 LISTENER QUERY = NOT AUTHORIZED` — this round does **not** activate the future state by itself.  **Acceptance-chain effect (conditional on independent confirmation of this bookkeeping commit):** at that point the accepted Option-A interpretation becomes authoritative, live governance transitions to the post-effectivity state above (GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY; UNUSED / 0 OF 1; NOT STARTED / 0 OF 1; NOT EXECUTED / MAXIMUM 1) while historical runtime activity remains zero; that transition is **GOVERNANCE-STATUS EFFECTIVITY** — not execution, not claim consumption, not budget consumption, not query execution.  **Non-blocking P3 (independent review):** R2 operational authorization binds by HEAD position while D1 binds by accepted artifact/blob/worktree content — no R2 HEAD gate is imported into D1; accepted conclusion `D1_OPERATIONAL_HEAD_BINDING = NO_GAP` (adding a HEAD-structure gate later would be a **NEW SUBSTANTIVE D1 gate** requiring its own design round; none is added here).  **Next pre-execution stage:** D1 ONE-SHOT PRE-EXECUTION GATE VERIFICATION / AUTHORIZED INVOCATION ROUND — **not another grant stage**; it begins with the already-frozen D1 PRE-* / A–P gate sequence, and only if all gates pass may the accepted one-shot consumption/invocation flow proceed.  **Future invocation preserved unchanged (not executed):** `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_EXCEPTION_DIAGNOSTIC_D1_EXECUTION.ps1" -AcceptedAuthorizationCommit "4f29ad6541def300c5361fec57357d86ea871479" -ExpectedAuthorizationSha256 "0573c5833adde17fdfb3ea77540bc99b23ce256b21193375eb8163ad9a4ec269" -ExpectedScriptSha256 "17dceea35333c9067c3a07857a6dc5548ef41518101794fcc6ca03127d1a7227"`; accepted query contract unchanged (`Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 4096 -State Listen -ErrorAction SilentlyContinue -ErrorVariable qerr`, maximum 1, no retry/repeat/polling/second query/alternate listener command/fallback).  **Reviewed implementation findings preserved as accepted findings (not runtime results):** `D1_C2_OPTION_B_IMPLEMENTATION = EXACT`; `D1_RAW_VS_PUBLISHED_QERR_MODEL = CORRECT`; terminating-exception precedence = PRESERVED; `D1_DIRECTORY_OCCUPANCY_CORRECTION = PASS`; `D1_DIRECTORY_RESIDUAL_TOCTOU = NO_MATERIAL_GAP`; `D1_SCRIPT_BODY_EXIT_CODE_SET = {0,10,20,30,40,50}`; `D1_TRAP_MODEL = SOUND`; `D1_CONSUMPTION_ACCOUNTING = CORRECT`; `D1_AUTOMATIC_VARIABLE_COLLISION_AUDIT = PASS`; `D1_EXIT_CODE_DOC_IMPLEMENTATION_CONSISTENCY = PASS`.  Standing P3-A unchanged: **ERROR STRING MAXIMUM REPRESENTATION RULE = NOT YET FROZEN / NON-BLOCKING DESIGN OBSERVATION** (not closed; no truncation, no invented maximum length, no hash-substituted text).  Historical statuses preserved: `764927bf…` = REQUEST_CHANGES / HISTORICAL CORRECTED IMPLEMENTATION CANDIDATE / NOT ACCEPTED / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED; `a25e154…` = REQUEST_CHANGES / HISTORICAL REJECTED IMPLEMENTATION CANDIDATE / NOT AUTHORIZED FOR EXECUTION / NOT EXECUTED.  Preserved downstream state (until independent confirmation of this bookkeeping commit): `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED`; Recovery-R2 authorization/attempt = `SPENT / NOT REUSABLE`; Mode-B = `BLOCKED / NOT RUN`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 = `NOT CLOSED`; G0.5 execution / Case-C / v0.3-E execution **NOT AUTHORIZED**; `G1`/`G2` **NOT RUN**; `adopt_completed_turn` **DISABLED**; **PATH C = NO STATIC BASIS / NOT AUTHORIZED**; **PATH D = NOT AUTHORIZED**.  Byte freeze verified before and after this round: C2 spec `69b7cfda…`; D1 script `17dceea…`; D1 execution authorization `0573c583…`; `.gitattributes` unchanged with the D1 `eol=lf` rule intact (`git ls-files --eol` → `i/lf w/lf attr/text eol=lf`).  Protected artifacts re-verified: five R2 operational artifacts, Oracle-R2 script/spec, config `b5e4abab…`/1897, CONFIG_ESTABLISHMENT, R1 artifacts, src/devrelay, tests, pyproject.toml — zero mutation.  All D1 operational artifacts (authorization-use TEMP/FINAL, attempt-use TEMP/FINAL, evidence directory, evidence/manifest/result TEMP/FINAL) remain **absent**.  Contradiction sweep: **CLEAN** — no unscoped current claim that D1 execution is already authorized/effective, that either budget is already usable, that the listener query is already authorized, or that any claim/query/evidence/result exists, and no ETB_SATISFIED / P6 verdict / G0.5 verdict / G0.5 CLOSED / Mode-B authorized / Oracle-R2 defective / root-cause-determined claim; future post-confirmation state is described only conditionally.  This bookkeeping round modified exactly two files (`M CHANGELOG.md`, `M docs/v0.3/V03E_ACCEPTANCE.md`) and performed **0** script executions, **0** listener queries, **0** claim creations, **0** D1 evidence/manifest/result/output creations, **0** Oracle executions, **0** live probes, **0** OpenCode starts/restarts, **0** HTTP, **0** provider/model calls, **0** SIC, **0** Mode-B, **0** G0.5/G1/G2, **0** budget grants or consumptions, **0** frozen-artifact modifications and **0** runtime/test/dependency/version changes; the ignored/untracked `PROJECT_MEMORY.md` persists.

**D1 DIAGNOSTIC RESULT ACCEPTANCE BOOKKEEPING — OWNER OPTION A RECORDED.**  The human owner selected **OWNER DECISION = A — RESULT-REVIEW APPROVAL SATISFIES "AS SEPARATELY AUTHORIZED"**, which resolves the previously reported `D1 POST-RESULT BOOKKEEPING AUTHORIZATION GAP`: the already-completed independent D1 result review is the distinct authorization event required by accepted spec §25 ("result bookkeeping / confirmation as separately authorized"), and therefore there is **NO** new result-bookkeeping authorization artifact, **NO** authorization candidate, **NO** authorization-design round, **NO** authorization acceptance bookkeeping, **NO** separate owner-authorization artifact and **NO** third authorization stage.  The independent result review issued **APPROVE V0.3-E D1 ONE-SHOT EXECUTION / DIAGNOSTIC RESULT** with blocking severity **P0 = 0, P1 = 0, P2 = 0**, and its reviewed findings are recorded here as reviewed facts, not re-executed: `D1_AUTHORIZATION_USE_CLAIM = VALID`, `D1_DIAGNOSTIC_ATTEMPT_CLAIM = VALID`, `D1_ONE_SHOT_EXECUTION_INTEGRITY = PASS`, `D1_SOURCE_AUTHORITATIVE_BOOKKEEPING_BINDING = EXACT`, `D1_QUERY_OUTCOME_CLASSIFICATION = EXACT`, `D1_C2_OPTION_B_RUNTIME_CONFORMANCE = NOT_APPLICABLE_WITH_PASS`, `D1_MANIFEST = VALID`, `RESULT VALIDATION = VALID`, `D1_DIAGNOSTIC_VS_ETB_SEMANTIC_SEPARATION = PASS`, `D1_EXECUTION_RESULT_CONTRADICTION_SWEEP = CLEAN`, with `query_outcome = ERROR_RECORDS_ZERO_ROWS`, `row_count = 0`, `rows = []`, `terminating_error = null`, `error_records` = exactly one `ERROR_VARIABLE` record, and `listener_query_invocations = 1`.  **Result provenance bound exactly (immutable):** authorization claim `cfc5652c662f5bb9090503113537fb618bb7e5cd367504cb5c5a33963c0a5e28`; attempt claim `e7592c344789cf8892d9bf6c5aa0121b6fef99eed99c700f6ce6b6bbbb278ec0`; evidence `0f4cfb19ad734511dddb8d8928afafd4d1dc4e077b91df508b3dc0f3e1345258`; manifest `45c26830dee6b0cef95113eb641ea6382f88256a6fbf18896a4a54038c43da4c`; result `a23e91c1e54c2065897600465b33fcbd5dd696b99851449c325cdfba205aa877`; and `source_authoritative_bookkeeping_commit = 93e44fe61c59ec5070e2823062a607347bb9163a` — which **MUST NOT** be replaced by `b35777e…`, `75313c9…`, `1dd35b49…` or this bookkeeping commit.  **Artifact-tracking model (uniquely derived, not chosen for convenience):** the accepted Recovery-R2 result-acceptance precedent `93e44fe61c59ec5070e2823062a607347bb9163a` (parent `2029003…`, tracked delta exactly `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md`, numstat `71/0` and `2/2`) read together with the frozen R2 §29.1 policy — the four Recovery-R2 claim paths are "**untracked operational control-state artifacts**" that "must not be `git add`ed, staged, committed, deleted, renamed, archived or normalized", and are "not part of the tracked-worktree-clean predicate" — and with accepted D1 spec §38-D, which records those artifacts as "**untracked operational control state** … **not part of the Git tree**", establishes that **all twelve historical operational artifacts (R2 ×5, R1 ×3, original ETB ×4) have never been tracked and remain untracked**; this round therefore follows **MODEL A**: the five approved D1 generated artifacts **remain untracked and byte-unchanged**, and this acceptance-bookkeeping commit modifies **only** the two established active status surfaces.  **Result-acceptance status model (established immutable-artifact + independent-approval-record pattern):** the frozen result artifact `docs/v0.3/V03E_G0_5_PRE_ETB_QUERY_DIAGNOSTIC_RESULT_D1.md` **preserves its construction-time banner** `diagnostic_authority_state=CANDIDATE / REQUIRES INDEPENDENT RESULT REVIEW` and was **not** edited, renamed, normalized or regenerated; the active accepted-result status is carried **only** by this CHANGELOG and by `docs/v0.3/V03E_ACCEPTANCE.md`, exactly as the R2 precedent did ("the artifact's own wording remains publication-time history, and the active status surfaces carry the authoritative result").  **Result-acceptance effectivity point (uniquely derived from the established D1 pattern):** the D1 diagnostic result becomes active/authoritative **only after independent bookkeeping confirmation of this commit** — every prior D1 acceptance-bookkeeping commit carries the same "accepted … **subject to independent confirmation of THIS bookkeeping commit**" construction — so this record states the accepted status **conditionally**: upon that independent confirmation, the independently reviewed D1 diagnostic result becomes the accepted/frozen **`AUTHORITATIVE DIAGNOSTIC RESULT`**, the exact vocabulary frozen by accepted spec §24.  Even then it remains **diagnostic-only**: `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED` is carried forward unchanged as the pre-existing Recovery-R2 semantic result, and this record does **not** claim that D1 proves `ETB_UNSATISFIED`, proves `ETB_SATISFIED`, proves root cause, proves Oracle-R2 defective, authorizes Mode-B, resolves P6 or closes G0.5.  **One-shot finality preserved exactly:** `D1 AUTHORIZATION USE = SPENT / 1 OF 1 / IRREVERSIBLE / NOT REUSABLE`; `D1 DIAGNOSTIC ATTEMPT = SPENT / 1 OF 1 / IRREVERSIBLE / NOT REUSABLE`; `D1 LISTENER QUERY EXECUTION = EXECUTED ONCE`; **NO RETRY AUTHORIZED**; no bookkeeping status here implies `UNUSED`, `NOT STARTED`, `AVAILABLE`, `RESET`, `REUSABLE`, a second attempt or a second query.  Preserved provenance: design `14b85bd2365d500ef87f357aeecb94de14211cc9` / `69b7cfda172658fe6c4e726430274a27a6dffb4c4d1c90a374d79feb6956e35d`; implementation `4f29ad6541def300c5361fec57357d86ea871479` / `17dceea35333c9067c3a07857a6dc5548ef41518101794fcc6ca03127d1a7227`; execution authorization `4f29ad65…` / `0573c5833adde17fdfb3ea77540bc99b23ce256b21193375eb8163ad9a4ec269`; effectivity clarification `75313c981afcced2bd669ce59993277c4c7d1ee1`; confirmed effectivity bookkeeping `1dd35b49a36218296e0e7a9452307e7288a6c74d`; historical lifecycle effectivity point `b35777e4a14ba105c1817e2dcaebf835f77a5dff` — this new commit is **bookkeeping provenance only** and replaces none of them.  Standing **P3-A = ERROR STRING MAXIMUM REPRESENTATION RULE = NOT YET FROZEN / NON-BLOCKING DESIGN OBSERVATION** remains open: the observed 232-character exception string was serialized complete, with no truncation, no hash substitution and no invented maximum; no non-blocking observation was promoted into a defect.  Preserved downstream state: `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED`; Recovery-R2 authorization / attempt = `SPENT / NOT REUSABLE`; Mode-B = `BLOCKED / NOT RUN`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 = `NOT CLOSED`; G0.5 execution / Case-C / v0.3-E implementation **NOT AUTHORIZED**; `G1`/`G2` **NOT RUN**; `adopt_completed_turn` **DISABLED**; **PATH C = NO STATIC BASIS / NOT AUTHORIZED**; **PATH D = NOT AUTHORIZED**.  **Owner reconciliation was NOT performed in this round** and remains blocked until this bookkeeping commit's independent confirmation approves; no owner reconciliation, no new ETB semantic verdict, no Mode-B authorization, no P6 resolution and no G0.5 closure occurs here.  This bookkeeping round performed **0** script executions, **0** listener queries, **0** `Get-NetTCPConnection` calls, **0** claim creations or deletions, **0** evidence/manifest/result modifications, **0** evidence regenerations, **0** budget consumptions, **0** retries, **0** Oracle executions, **0** OpenCode starts, **0** HTTP, **0** provider/model calls, **0** SIC, **0** Mode-B, **0** G0.5/G1/G2 and **0** runtime/test/dependency/version changes; all fifteen protected artifacts and all five approved generated artifacts were re-verified byte-identical before and after, and the ignored/untracked `PROJECT_MEMORY.md` persists.

That approval followed three earlier review rounds: the first independent design
review returned `REQUEST_CHANGES` (P0 = 1, P1 = 6, P2 = 5) and the
recovery/reconciliation contract was repaired in `f67bf9e`; two narrow re-reviews
then returned `REQUEST_CHANGES` for a stale status/gating pointer (fixed in
`5b7c65a`) and for a G0.1/P7 hard-gate contradiction (fixed in `9f4a018`).  The
remediated design
splits a **mandatory fail-closed core** (reconcile/report + an explicit
`mark_unrecoverable` exit; no provider submission, no retry, no auto-resume, no
adoption) from an **optional gated** `adopt_completed_turn` capability and a
**report-only** pending capability, so that no optional capability can block the
core:

* recovery entry is an explicit legal planner action
  (`devrelay_resolve_recovery` on a valid v2 document with a live in-flight intent,
  or on `RECOVERY_REQUIRED`), fixing the review's P0 deadlock; v2 phase/decide calls
  refuse without mutating, so no transition is a side effect of an invalid action;
* the interrupted attempt is represented by exactly one `recovery.attempt` record
  and is converted once (into one blocked or one completed role turn) at
  resolution, with the complete `RECOVERY_REQUIRED` document shape and pinned
  accounting equations published (a consumed slot is never refunded and is counted
  exactly once);
* corruption is explicitly never recovery (violations outside the enumerated deltas
  become `orchestration_state_corrupt`: no entry, no override, no repair);
* a strict recovery evidence reader replaces "no ledger record, therefore never
  issued" (identity-scoped, no silent skipping, no truncation-as-proof, an interval
  proof, otherwise `evidence_gap`);
* adoption claims are downgraded: reconcile may report a candidate, but
  `resolve_recovery` must refuse `adopt_completed_turn` until the operation
  attribution proofs P1, P2, P3 and P8 (plus P9 if timestamps are used) pass;
* schema handling is version-dispatched (v1 validated by the frozen v0.3-D rules and
  never migrated or reinterpreted; v2 uses the v0.3-E rules; anything else is
  corrupt), `evidence_sha256` has a canonical metadata-only definition with a
  stable already-resolved error, the crash-window matrix gains the window where the
  response exists but the ledger settle is not durable, and pending results are
  report-only.

The full contract (case taxonomy, `RECOVERY_REQUIRED` state, crash-window and
restart matrices, minimum two-tool surface, capability dependency table, platform
proof gate) is in `docs/v0.3/V03E_SPEC.md` with the design-phase matrix in
`docs/v0.3/V03E_ACCEPTANCE.md`.  It contains no retry protocol, keeps
`model_turns_used` as consumed slots that are never refunded, keeps terminal runs
closed and keeps `devrelay_get_run` read-only.  Implementation is gated in two
separate stages, and both of its prerequisites are now satisfied (design frozen;
**G0.1/P7 = PASS**, authoritative and independently approved): the **mandatory
fail-closed core**
(reconcile/report + `mark_unrecoverable`; no retry, no model submission, no
auto-resume) requires the design freeze **and** the local strict-reader /
ledger-integrity proof **G0.1/P7 to PASS first** (design frozen -> G0.1/P7 PASS ->
implementation may be authorized; there is no degraded-implementation path) - both of
those steps have happened, so implementation awaits only a separately issued
authorization - while
the **optional** `adopt_completed_turn` capability stays disabled and requires **both**
the independently satisfied local **P6/G0.5 identity/ownership veto bound** (SPEC §25.1)
**and** the independently satisfied remote/platform *enabling* proofs
P1 + P2 + P3 + P8 (plus P9 if timestamp/order correlation is used) through G1/G2,
together with the remaining platform proof gate.  Pending-result handling stays report-only and
non-delivery classification stays informational.  No runtime source, test, schema, dependency,
version or tag changed; no real provider/model call was made and no OpenCode
instance was started.  Design branch: `v0.3-e-recovery-reconciliation` (parent
`56e7842`).

The first design revision of this section read: `docs/v0.3/V03E_SPEC.md` (case taxonomy A-H, preserved v0.3-D
invariants, one new non-terminal execution-frozen `RECOVERY_REQUIRED` state,
exact call-identity model, reconciliation evidence sources, crash-window matrix
W0-W6, restart matrix, reconciled completion / non-delivery / pending-reply
policies, budget and privacy rules, minimum two-tool MCP surface, design-decisions
table) and `docs/v0.3/V03E_ACCEPTANCE.md` (design-phase matrix).  The design
forbids implicit retry, model fallback, automatic sequencing and automatic resume,
keeps `model_turns_used` as consumed slots that are never refunded, keeps terminal
runs closed, and keeps `devrelay_get_run` read-only.  Two tools are proposed and
**not** implemented: `devrelay_reconcile_run` (read-only) and
`devrelay_resolve_recovery` (mutating, evidence-gated).  Implementation is gated on
an independent design review and the open platform proofs in SPEC section 15
(P1-P7).  No runtime source, test, schema, dependency, version or tag changed; no
real provider/model call was made.  Design branch:
`v0.3-e-recovery-reconciliation` (parent `56e7842`).

**ORACLE-PATHD (PATH D NEW EXECUTION ORACLE) DESIGN CANDIDATE — OWNER D-EXEC-1 + OWNER NAMING DECISION N-C.**
The human owner selected **PATH D — NEW ETB ATTEMPT**; the Path-D authorization design round then returned
`PATH_D_EXECUTION_ORACLE = NOT AVAILABLE` because Oracle-R2's six-path ABSENT precondition can no longer be
satisfied (three of its finals are present), the original oracle has no preserved executable, and Oracle-R2
§17.1/§17.4 forbid modification, wrapping, translation, parameterization, temporary-script reconstruction or
output-path injection.  The owner therefore selected **D-EXEC-1 — AUTHORIZE A NEW PATH-D ORACLE DESIGN ROUND**
and, after the naming round returned `PATH_D_ORACLE_IDENTITY = NOT UNIQUELY DETERMINED` (the recovered naming
rule is `Oracle-<served Recovery cycle>` — `Oracle-R1` does not exist and R1 created no new oracle — which does
not apply to Path D), selected **N-C — `Oracle-PathD`** with canonical identity token **`PATH_D`**;
`Oracle-R3`, `Oracle-D` and `Oracle-PD` are **not** used.  This round creates the Oracle-PathD oracle as two new
tracked artifacts — the normative tracked executable
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1` (ASCII-only, every byte `<= 0x7F`, no BOM, LF only,
CR count `0`, one terminal LF, `31328` bytes, worktree SHA-256
`8bdeb434794c43fe4a199e7338790ba0dbd319728b6766d54299c894a16ac738`, parser-only validation **0 parse errors**)
and its specification `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.md` — plus exactly **one** new narrow
`.gitattributes` rule (`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1 text eol=lf`; no `*.ps1`
wildcard, no other text policy changed, `core.autocrlf` unaltered, `git check-attr` resolving to `text: set` /
`eol: lf`) and the minimum status-surface updates in this file and `docs/v0.3/V03E_ACCEPTANCE.md`.  Oracle-PathD
is the **minimum semantic successor** of accepted Oracle-R2: the exhaustive line-level diff is **43 added / 39
removed** lines across **19 hunks**, every hunk mapping to `NEW_ORACLE_IDENTITY`, `NEW_OUTPUT_NAMESPACE` or
`MECHANICAL_REFERENCE_FOR_NEW_IDENTITY_OR_NAMESPACE`, so **`ORACLE_SEMANTIC_DRIFT = NONE`**; the listener
predicate (`127.0.0.1` / `4096` / `Listen`) and its decision order, the endpoint `http://127.0.0.1:4096`, the
accepted target literal and `$ExpectedSha` `578d7eb3…`, the `opencode-ai` / `1.18.11` / `bin.opencode` package
identity, `$OriginalOracleCommit` `1c6c7cd…` / `$OriginalOracleSha` `01675fa7…`, the process-instance identity
(PID **and** `CreationDate.Ticks`), the `CreateFileW`/`GetFinalPathNameByHandleW` canonicalization chain, the
S0/S1 continuity comparison field set, the 18 `checks` keys, the 14 `activity_counters` keys, the six
`non_claims` strings, the publication order and every read-back verification are **provably unchanged** by
their absence from that diff.  The new output namespace is `docs/v0.3/evidence/etb-execution-path-d/` with six
exact paths (`ETB_EVIDENCE.json{,.tmp}`, `MANIFEST.sha256{,.tmp}`,
`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_D.md{,.tmp}`); the new evidence schema identity is
`devrelay-etb-v1-path-d`, leaving `devrelay-etb-v1` and `devrelay-etb-v1-r2` historical and unreinterpreted; the
new claim lineage is `PATH_D` (`ETB_PATH_D_AUTHORIZATION_USE.claim{,.tmp}` and
`ETB_PATH_D_ATTEMPT_USE.claim{,.tmp}` under `docs/v0.3/evidence/`, permanently distinct from every historical
claim path); and the new provenance field names are `oracle_path_d_commit`, `oracle_path_d_spec_sha256` and
`oracle_path_d_script_sha256`, which remain **UNKNOWN** until a future independent approval record populates
them.  All eleven Path-D namespace paths (six output paths, the namespace directory and four claim paths) were
verified **ABSENT** under the file-or-directory occupancy predicate, and the design-construction baseline is
`0bd97206584d0726cf86317de8f385ec2720d423`.  Oracle-PathD is **`DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN /
NOT EXECUTED`**: **PATH-D AUTHORIZATION DESIGN = BLOCKED PENDING ORACLE ACCEPTANCE**, **PATH-D ETB EXECUTION =
NOT AUTHORIZED**, **ORACLE EXECUTION = NOT AUTHORIZED**, **LISTENER QUERY = NOT EXECUTED**; oracle-design
acceptance is explicitly **not** Path-D execution authorization, and after acceptance the Path-D `NEW ETB
EXECUTION AUTHORIZATION DESIGN` stage must resume.  Nothing historical was modified, moved, archived,
normalized, deleted or reused: Oracle-R2, Recovery-R1, Recovery-R2, D1 and the original oracle artifacts,
claims, evidence, manifests, results and construction-time banners are untouched, and no occupied historical
output path was disturbed to make room.  The round performed 0 oracle executions, 0 ETB executions, 0 listener
queries, 0 `Get-NetTCPConnection` calls, 0 claim creations, 0 evidence/manifest/result creations, 0 budget
consumptions, 0 config mutations, 0 HTTP, 0 provider/model calls, 0 SIC, 0 Mode-B, 0 G0.5/G1/G2 and 0
runtime/test/dependency/version changes.  Preserved unchanged: `AUTHORITATIVE ETB SEMANTIC RESULT =
ETB_UNSATISFIED`; Recovery-R2 authorization/attempt `SPENT / NOT REUSABLE`; `D1 = ACCEPTED / FROZEN /
AUTHORITATIVE DIAGNOSTIC RESULT`; `D1 LISTENER QUERY = EXECUTED ONCE`; Mode-B `BLOCKED / NOT RUN`;
`P6 = UNPROVEN / UNSATISFIED`; G0.5 `NOT CLOSED`; G0.5 execution / Case-C / v0.3-E implementation
`NOT AUTHORIZED`; `G1`/`G2` `NOT RUN`; `adopt_completed_turn` `DISABLED`; **PATH C = NO STATIC BASIS /
NOT AUTHORIZED**.  The exact next stage is an **independent Oracle-PathD design review**; only after that
review, Oracle-PathD acceptance bookkeeping and independent bookkeeping confirmation may the Path-D `NEW ETB
EXECUTION AUTHORIZATION DESIGN` resume.  No tag, no release and no push occurred.

**ORACLE-PATHD ACCEPTANCE BOOKKEEPING — THIRD-PARTY DESIGN REVIEW APPROVED (bookkeeping only; nothing executed, no budget consumed, no reviewed artifact modified).**  The **third-party independent design review** of candidate `3276ef0bb0808ac10b2b82fca68ff282759856fe` issued **`APPROVE V0.3-E ORACLE-PATHD DESIGN CANDIDATE — THIRD-PARTY INDEPENDENT REVIEW`** with **P0 = 0, P1 = 0, P2 = 0, P3 = 3**, and recorded **`THIRD-PARTY INDEPENDENCE = SATISFIED`** (the reviewer is not the agent/session that constructed the candidate, and produced no prior review of it).  Reviewed findings are recorded as reviewed facts, not re-derived here: `ORACLE_PATHD_DELTA = BOUNDED`; `ORACLE_R2_PREDECESSOR_AUTHORITY = EXACT`; `OWNER_DECISION_BINDING = EXACT`; `ORACLE_PATHD_NAMING = CONSISTENT`; `HISTORICAL_IMMUTABILITY = PRESERVED`; `PATH-D RUNTIME NAMESPACE OCCUPANCY = 0 / 11`; `ORACLE_PATHD_BYTE_IDENTITY = EXACT`; `ORACLE_PATHD_PARSE = PASS`; `ORACLE_SEMANTIC_DRIFT = NONE`; `LISTENER_ENDPOINT_CONTRACT = UNCHANGED`; `TARGET_IDENTITY_CONTRACT = UNCHANGED`; `PATHD_SCHEMA = CLOSED / CONSISTENT`; `RESULT_MODEL = UNCHANGED`; `PUBLICATION_MODEL = UNCHANGED`; `FAIL_CLOSED_CONTRACT = PRESERVED`; `ORACLE_PATHD_SPEC = COMPLETE`; `STATUS_SURFACE_CONSISTENCY = CONSISTENT`; `ORACLE_PATHD_EFFECTIVITY_MODEL = EXACT`; `MODEL A = PRESERVED`.  **Accepted design identity (immutable):** `oracle_path_d_commit` = `3276ef0bb0808ac10b2b82fca68ff282759856fe`, tree `b6d058ddf196ed37c2698e5e087ccc789fb52b5a`; human identifier `Oracle-PathD`; canonical token `PATH_D`; uppercase token `ORACLE_PATH_D`; spec `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.md` with committed-blob SHA-256 `15e39452f5efae1f87f03e38fd72ca3336fe3b591affbd93c9104e785fa9884b` (34 659 bytes); executable `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1` with committed-blob SHA-256 `8bdeb434794c43fe4a199e7338790ba0dbd319728b6766d54299c894a16ac738` (31 328 bytes; ASCII-only, no BOM, LF only, single terminal LF); output namespace `docs/v0.3/evidence/etb-execution-path-d/`; schema identity `devrelay-etb-v1-path-d`; claim lineage `PATH_D`; provenance field names `oracle_path_d_commit` / `oracle_path_d_spec_sha256` / `oracle_path_d_script_sha256`.  **Predecessor bound unchanged:** `oracle_r2_commit = dfb78f34d919e8c9863a8398fb4f63ee301167bc`, `oracle_r2_spec_sha256 = 5e9221e3950af6ec3e0612c4d962562c33e761899dfd6af42d10f5a9895f9f2f`, `oracle_r2_script_sha256 = 22c5fbd61da609e6cc39e973be6030d4c360019ed1f56e69ca45f92fa1689c17`.  **Owner decisions preserved:** `D-EXEC-1 — AUTHORIZE NEW PATH-D EXECUTION ORACLE DESIGN`; `N-C — Oracle-PathD`; canonical id token `PATH_D`.  These authorize the Oracle design lineage only and do **not** themselves authorize ETB execution.  **Accepted semantic conclusion (summarized, not rewritten):** Oracle-PathD is semantically equivalent to accepted Oracle-R2 except for `NEW_ORACLE_IDENTITY`, `NEW_OUTPUT_NAMESPACE` and `MECHANICAL_REFERENCE_FOR_NEW_IDENTITY_OR_NAMESPACE`; no authorized semantic change exists in the listener predicate, endpoint, Mode P, process identity, binary identity, package identity, canonicalization, S0/S1 continuity, result model, publication model, fail-closed behaviour, or retry/fallback policy.  **P3 disposition (recorded, deliberately NOT fixed):** `P3 = 3`, all **BOUNDED / NON-BLOCKING / NO DESIGN SEMANTIC IMPACT** — P3-1 minor wording variance between status surfaces; P3-2 minor imprecision in the explanatory wording of the `MECHANICAL_REFERENCE` diff category; P3-3 the historical generic `oracle_commit` / `oracle_sha256` versus future Oracle-PathD-specific `oracle_path_d_*` provenance distinction is not centralized in one explanatory location.  **Neither the Oracle-PathD spec nor the Oracle-PathD executable was edited in this round** — doing so would change the independently reviewed candidate bytes; any future clarification of these P3 observations must be separately governed.  **Accepted-effectivity model (bookkeeping and confirmation are NOT collapsed):** this commit is **acceptance bookkeeping provenance only**; immediately after it, `ORACLE-PATHD DESIGN REVIEW = APPROVED`, `ORACLE-PATHD ACCEPTANCE BOOKKEEPING = COMMITTED / PENDING INDEPENDENT CONFIRMATION`, and `ORACLE-PATHD = CONDITIONALLY ACCEPTED / NOT YET FROZEN / NOT YET EFFECTIVE`.  Oracle-PathD becomes **`ACCEPTED / FROZEN`** only **after independent confirmation of THIS bookkeeping commit**; `oracle_path_d_commit` remains the independently reviewed **design** commit and is never substituted by this bookkeeping HEAD.  **Gates remain closed until that confirmation:** `PATH-D AUTHORIZATION DESIGN = REMAINS BLOCKED PENDING ORACLE-PATHD ACCEPTANCE CONFIRMATION`; `PATH-D ETB EXECUTION = NOT AUTHORIZED`; `ORACLE-PATHD EXECUTION = NOT AUTHORIZED`; `LISTENER QUERY = NOT EXECUTED`; claims `NOT CREATED`; budget `NOT CONSUMED`.  **MODEL A preserved:** all thirteen historical untracked operational artifacts remain untracked and byte-unchanged, and this commit modifies **only** the two established active status surfaces (`CHANGELOG.md` and `docs/v0.3/V03E_ACCEPTANCE.md`).  This bookkeeping round performed **0** oracle executions, **0** ETB executions, **0** listener queries, **0** `Get-NetTCPConnection` calls, **0** claim creations, **0** evidence/manifest/result creations, **0** budget consumptions, **0** config mutations, **0** HTTP, **0** provider/model calls, **0** reviewed-artifact mutations and **0** runtime/test/dependency/version changes.  The exact next stage is **independent Oracle-PathD acceptance-bookkeeping confirmation** (review-only, no commit), which must verify this bookkeeping commit against the approved candidate and the third-party review authority.  No tag, no release and no push occurred.

**PATH-D NEW ETB EXECUTION AUTHORIZATION DESIGN CANDIDATE — DESIGN / GOVERNANCE ONLY (nothing executed, no claim created, no budget consumed, no namespace occupied).**  With Oracle-PathD independently confirmed as **`ACCEPTED / FROZEN / EFFECTIVE`**, the previously blocked stage `NEW ETB EXECUTION AUTHORIZATION DESIGN` resumed and produced exactly **one** new normative artifact: `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_D_AUTHORIZATION.md` (committed-blob SHA-256 `49e7c29a4c2367764aba195931908c627b9c7226725c76e66b1ef60eecb6f9bf`, `35007` bytes, 738 lines, UTF-8, no BOM, LF only, CR count `0`, one terminal LF, 29 sections).  Path naming was **mechanically derived, not chosen for convenience**: the recovered authorization-document rule is `V03E_G0_5_PRE_ETB_<IDENTITY>_AUTHORIZATION.md` (precedents: the original Round-5 authorization, `…_RECOVERY_AUTHORIZATION.md`, `…_RECOVERY_R2_AUTHORIZATION.md`, `…_QUERY_EXCEPTION_DIAGNOSTIC_D1_EXECUTION_AUTHORIZATION.md`), so the frozen canonical token `PATH_D` maps to `V03E_G0_5_PRE_ETB_PATH_D_AUTHORIZATION.md`; no tracked rule specifies a different exact path, and the path was verified unoccupied.  **Owner decisions bound exactly:** `OWNER DECISION = PATH D — NEW ETB ATTEMPT`; `OWNER EXECUTION-SHAPE DECISION = D-EXEC-1`; `OWNER NAMING DECISION = N-C — Oracle-PathD`; canonical token `PATH_D`; `NEW ETB ATTEMPT = AUTHORIZED FOR DESIGN ONLY AT THIS STAGE`; `ETB EXECUTION = NOT YET AUTHORIZED`; and the artifact states in terms **`THIS IS NOT A RETRY`** — it is a new authorization lineage, not a retry of Recovery-R2, not a reuse of Recovery-R2 or D1 authorization, not a second D1 execution, and it resets no spent budget.  **Oracle-PathD authority bound:** `oracle_path_d_commit = 3276ef0bb0808ac10b2b82fca68ff282759856fe` (the independently reviewed **design** commit, never substituted by the acceptance-bookkeeping commit `806ade0…` or any later HEAD), `oracle_path_d_spec_sha256 = 15e39452f5efae1f87f03e38fd72ca3336fe3b591affbd93c9104e785fa9884b` (34 659 bytes), `oracle_path_d_script_sha256 = 8bdeb434794c43fe4a199e7338790ba0dbd319728b6766d54299c894a16ac738` (31 328 bytes); Oracle-R2 (`dfb78f34…` / `5e9221e3…` / `22c5fbd6…`) is retained as **historical predecessor authority only**, and the Path-D authorization binds to Oracle-PathD, not to Oracle-R2.  **Provenance distinction centralized (the previously recorded non-blocking observation does NOT propagate):** the new artifact's §3 freezes, in one place, that the generic historical evidence fields `oracle_commit` / `oracle_sha256` (original oracle `1c6c7cd…` / `01675fa7…`, inherited closed ETB evidence semantics, **not** modified or reinterpreted) are a **different family** from the Path-D authorization provenance fields `oracle_path_d_commit` / `oracle_path_d_spec_sha256` / `oracle_path_d_script_sha256`; the accepted Oracle-PathD specification was **not** edited to add this clarification.  **New claim namespace (permanently distinct):** lineage `PATH_D` with `docs/v0.3/evidence/ETB_PATH_D_AUTHORIZATION_USE.claim{,.tmp}` and `docs/v0.3/evidence/ETB_PATH_D_ATTEMPT_USE.claim{,.tmp}` in the accepted claim-control directory `docs/v0.3/evidence/`; no historical claim path is reset, removed, renamed, archived or reused.  **Frozen closed claim schemas:** `devrelay-etb-path-d-authorization-use-v1` and `devrelay-etb-path-d-attempt-use-v1`, each exactly seven ordered fields with `state = CONSUMED`, UTF-8, no BOM, exactly one final LF, and a verbatim frozen claim writer (`Write-DevRelayPathDOneShotClaim`) using `ConvertTo-Json -Depth 4 -Compress`, exclusive `CreateNew`, byte-identical read-back verification, BOM/final-LF assertions and a two-argument `System.IO.File.Move` publication with no overwrite.  **New one-shot budgets:** `PATH_D_AUTHORIZATION_USE_BUDGET = 1 OF 1` with `PATH_D_AUTHORIZATION_USE = 0 OF 1 / NOT CONSUMED` and `PATH_D_ETB_ATTEMPT_BUDGET = 1 OF 1` with `PATH_D_ETB_ATTEMPT = 0 OF 1 / NOT STARTED`; the authorization budget is consumed at the successful `CreateNew` of the authorization TEMP claim and the attempt budget at the successful `CreateNew` of the attempt TEMP claim, irreversibly, with **no** retry, **no** fallback, **no** automatic cleanup, **no** claim deletion, **no** claim reuse, **no** output overwrite, **no** historical-artifact mutation and **no** budget reset; a later publication failure MUST NOT reopen a consumed budget.  **Historical budgets preserved unchanged:** `RECOVERY-R2 AUTHORIZATION / ATTEMPT = SPENT / NOT REUSABLE`; `RECOVERY-R1 = SPENT / NOT REUSABLE`; original Round-5 authorization `SPENT / NOT REUSABLE`; `D1 AUTHORIZATION / DIAGNOSTIC ATTEMPT = SPENT / 1 OF 1 / IRREVERSIBLE / NOT REUSABLE`; `D1 LISTENER QUERY = EXECUTED ONCE / NO RETRY`.  **Fifteen PRE-* prerequisites** freeze branch identity, artifact self-identity, Oracle-PathD accepted/frozen/effective state via confirmed bookkeeping `806ade0…`, exact script/spec blob hashes, worktree byte-identity, the `.gitattributes` LF resolution, tracked-worktree cleanliness, config identity (`b5e4abab…`, 1897 bytes, `http://127.0.0.1:4096` via the frozen reader shape), `CONFIG_ESTABLISHMENT` identity, historical marker integrity, claim-path and runtime-path ABSENT states, and zero prior consumption; **the runtime semantic checks belong exclusively to Oracle-PathD and are NOT duplicated into the authorization layer**; any failure → STOP before consuming anything.  **Execution shape bound, not redesigned:** `MODE P / pre-existing target`; `configured_base_url = http://127.0.0.1:4096`; listener predicate `LocalAddress = 127.0.0.1`, `LocalPort = 4096`, `State = Listen`; no endpoint discovery, no fallback, no alternate port, no `localhost` alias, no IPv6 alternate, no OpenCode start/restart, no HTTP, no `/doc`, no provider/model invocation; target identity `…\opencode-ai\bin\opencode.exe`, binary SHA-256 `578d7eb3…`, package `opencode-ai`, version `1.18.11`, `bin.opencode`, with `OwningProcess`/PID/`Win32_Process`/`ExecutablePath`/`CreationDate` process-instance identity, canonicalization, dual hash validation, `package.json` validation and S0/S1 continuity all preserved; oracle entry is exactly `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1"` with no parameters, no wrapper and no generated script.  **Result authority:** an execution observation is distinct from the authoritative semantic result; a raw generated result file MUST NOT silently replace it, and it becomes authoritative **only** after independent result review → result bookkeeping → bookkeeping confirmation; until then `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`.  **Result classes:** exactly `ETB_SATISFIED`, `ETB_UNSATISFIED`, `HARNESS_INVALID / NO ETB SEMANTIC RESULT`, with no `PASS`/`FAIL`/`PARTIAL`/`UNKNOWN`/`PROBABLE`/`RETRY` and no preselected outcome.  **Namespace occupancy verified at design time:** `PATH-D RUNTIME OCCUPANCY = 0 / 11` (six Oracle-PathD output paths, the `docs/v0.3/evidence/etb-execution-path-d` directory and four Path-D claim paths all ABSENT); no claim, evidence, manifest, result or output directory was created.  **Operational inventory terminology frozen precisely for future use** (both counting models, no "thirteen historical artifacts" phrasing): `git status --porcelain` collapsed entries `13`; expanded untracked files `17`; expanded composition `12 historical operational files + 5 accepted D1 operational files`.  **MODEL A preserved** and **historical immutability preserved**: the Oracle-PathD spec/executable, Oracle-R2, Recovery-R1, Recovery-R2, D1, the original oracle artifacts, all historical claims, evidence, manifests, results and construction-time banners are unmodified, and this round modifies only this CHANGELOG and `docs/v0.3/V03E_ACCEPTANCE.md` in addition to the one new artifact.  **Current effectivity:** `PATH-D AUTHORIZATION = CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE`; `PATH-D ETB EXECUTION = NOT AUTHORIZED`; `ORACLE-PATHD EXECUTION = NOT AUTHORIZED`; this candidate grants **no** execution effectivity and collapses **no** acceptance stage.  This design round performed 0 oracle executions, 0 ETB executions, 0 listener queries, 0 `Get-NetTCPConnection` calls, 0 claim creations, 0 evidence/manifest/result creations, 0 budget consumptions, 0 config mutations, 0 endpoint-state modifications, 0 OpenCode starts/restarts, 0 HTTP, 0 `/doc`, 0 provider/model calls, 0 historical-artifact mutations and 0 runtime/test/dependency/version changes.  **Exact next stage:** an **independent review of the Path-D new ETB execution authorization design candidate**; acceptance bookkeeping is **not** performed in this round.  No tag, no release and no push occurred.

**PATH-D AUTHORIZATION ACCEPTANCE BOOKKEEPING — THIRD-PARTY AUTHORIZATION DESIGN REVIEW APPROVED (bookkeeping only; nothing executed, no claim created, no budget consumed, no reviewed artifact modified).**  The **third-party independent review** of the Path-D authorization design candidate `29bf27fc2f76d415eb9c07d890f50b665aca6846` (tree `63979c0851500c457074194d6b274179f9558509`; subject `docs(v03e): define Path-D ETB authorization candidate`) issued **`APPROVE V0.3-E PATH-D NEW ETB EXECUTION AUTHORIZATION DESIGN CANDIDATE — THIRD-PARTY INDEPENDENT REVIEW`** with **P0 = 0, P1 = 0, P2 = 0, P3 = 4**, and recorded **`THIRD-PARTY INDEPENDENCE = SATISFIED`**.  Reviewed findings are recorded as reviewed facts, not re-derived here: `PATHD_AUTHORIZATION_DELTA = BOUNDED`; `ORACLE_PATHD_AUTHORITY = EXACT`; `PATHD_OWNER_BINDING = EXACT`; `PATHD_AUTHORIZATION_ARTIFACT_IDENTITY = EXACT`; `PATHD_AUTHORIZATION_IDENTITY_MODEL = CLOSED`; `PATHD_CLAIM_NAMESPACE = DISTINCT`; `PATH-D RUNTIME OCCUPANCY = 0 / 11`; `PATHD_BUDGET_MODEL = DISTINCT / CLOSED`; `ORACLE_PATHD_PROVENANCE_BINDING = EXACT`; `ORACLE_PROVENANCE_SEPARATION = EXACT`; `PATHD_EXECUTION_SHAPE = EXACT`; `PATHD_TARGET_IDENTITY = UNCHANGED`; `PATHD_PRECONDITION_MODEL = CLOSED / FAIL-CLOSED`; `PATHD_CLAIM_WRITER = DETERMINISTIC / FAIL-CLOSED`; `PATHD_CONSUMPTION_SEMANTICS = IRREVERSIBLE / EXACT`; `PATHD_FAIL_CLOSED = PRESERVED`; `PATHD_RESULT_AUTHORITY_MODEL = EXACT`; `PATHD_RESULT_MODEL = UNCHANGED`; `MODEL_A = PRESERVED`; `HISTORICAL_IMMUTABILITY = PRESERVED`; `PATHD_AUTHORIZATION_EFFECTIVITY_MODEL = EXACT`; `STATUS_SURFACE_CONSISTENCY = CONSISTENT`.  **Reviewed authorization-design identity established (immutable):** `path_d_authorization_commit` = `29bf27fc2f76d415eb9c07d890f50b665aca6846`; `path_d_authorization_sha256` = `49e7c29a4c2367764aba195931908c627b9c7226725c76e66b1ef60eecb6f9bf`; authorization artifact `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_D_AUTHORIZATION.md` (committed-blob SHA-256 `49e7c29a4c2367764aba195931908c627b9c7226725c76e66b1ef60eecb6f9bf`, `35007` bytes, 738 lines, CR count `0`, exactly one terminal LF, worktree byte-identical to the committed blob).  The future executor must bind to those exact values once acceptance becomes effective; **this bookkeeping commit MUST NOT replace either value**, and neither may any later confirmation HEAD, operational HEAD or result-review HEAD.  **Oracle-PathD frozen provenance (unchanged, re-verified):** `oracle_path_d_commit = 3276ef0bb0808ac10b2b82fca68ff282759856fe` (the independently reviewed **design** commit, never substituted by the acceptance-bookkeeping commit `806ade0c51c1a3e2751abe2f0167c1267b2000b0` or by this new commit), `oracle_path_d_spec_sha256 = 15e39452f5efae1f87f03e38fd72ca3336fe3b591affbd93c9104e785fa9884b` (34 659 bytes), `oracle_path_d_script_sha256 = 8bdeb434794c43fe4a199e7338790ba0dbd319728b6766d54299c894a16ac738` (31 328 bytes); `ORACLE-PATHD = ACCEPTED / FROZEN / EFFECTIVE`; `ORACLE-PATHD EXECUTION = NOT AUTHORIZED`.  **Owner decisions preserved:** `OWNER DECISION = PATH D — NEW ETB ATTEMPT`; `OWNER EXECUTION-SHAPE DECISION = D-EXEC-1`; `OWNER NAMING DECISION = N-C — Oracle-PathD`; canonical id token `PATH_D`; **`THIS IS NOT A RETRY`**.  These decisions authorize the Path-D lineage only through the governed acceptance lifecycle; **they do not authorize ETB execution in this round**, and no owner decision was expanded into execution authority.  **New claim namespace (permanently distinct, still empty):** `docs/v0.3/evidence/ETB_PATH_D_AUTHORIZATION_USE.claim{,.tmp}` and `docs/v0.3/evidence/ETB_PATH_D_ATTEMPT_USE.claim{,.tmp}` — all four paths remain **ABSENT**, and the complete Path-D runtime namespace remains **`PATH-D RUNTIME OCCUPANCY = 0 / 11`**, verified both before mutation and after this commit; no claim, evidence, manifest, result or output directory was created.  **Budget state (unchanged; no budget consumed by bookkeeping):** `PATH_D_AUTHORIZATION_USE_BUDGET = 1 OF 1` with `PATH_D_AUTHORIZATION_USE = 0 OF 1 / NOT CONSUMED`; `PATH_D_ETB_ATTEMPT_BUDGET = 1 OF 1` with `PATH_D_ETB_ATTEMPT = 0 OF 1 / NOT STARTED`; `ORACLE-PATHD EXECUTION = NOT AUTHORIZED`; `LISTENER QUERY = NOT EXECUTED`.  Historical spent budgets remain spent and not reusable: original Round-5 authorization `SPENT / NOT REUSABLE`, Recovery-R1 `SPENT / NOT REUSABLE`, Recovery-R2 authorization / attempt `SPENT / NOT REUSABLE`, `D1 AUTHORIZATION / DIAGNOSTIC ATTEMPT = SPENT / 1 OF 1 / IRREVERSIBLE / NOT REUSABLE`, `D1 LISTENER QUERY = EXECUTED ONCE / NO RETRY`.  **Result authority preserved:** `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED`; the authorization-design acceptance creates **no** new semantic result, and any future Path-D execution observation must still pass **independent result review → result bookkeeping → independent bookkeeping confirmation** before becoming authoritative.  **P3 disposition (recorded, deliberately NOT fixed):** `P3 = 4`, all **BOUNDED / NON-BLOCKING / NO AUTHORIZATION-SEMANTIC IMPACT / NO EXECUTION-CONTROL WEAKENING** — P3-1 legacy untracked-inventory wording remains in historical status records while the new authorization document now freezes the precise 13-collapsed / 17-expanded / 12-historical + 5-D1 model; P3-2 the Oracle-PathD bookkeeping confirmation is a review-only event and therefore is not itself represented by a dedicated repository object; P3-3 some checklist state tokens are represented with semantically equivalent precedent terminology (`NOT CONSUMED` / `NOT STARTED` / `NOT AUTHORIZED`) instead of the exact literal strings `= 0` or `SPENT = NO`; P3-4 the candidate and status surfaces use substantively equivalent but not byte-identical state wording for `REQUIRES INDEPENDENT REVIEW` / `CLAIMS NOT CREATED`.  **No reviewed artifact was modified to "fix" any P3** — the authorization artifact, the Oracle-PathD spec and the Oracle-PathD executable are byte-unchanged.  **Two-stage acceptance effectivity (bookkeeping and confirmation are NOT collapsed):** this commit is **acceptance bookkeeping provenance only**; immediately after it, `PATH-D AUTHORIZATION DESIGN REVIEW = APPROVED`, `PATH-D AUTHORIZATION ACCEPTANCE BOOKKEEPING = COMMITTED / PENDING INDEPENDENT CONFIRMATION`, and `PATH-D AUTHORIZATION = CONDITIONALLY ACCEPTED / NOT YET FROZEN / NOT YET EFFECTIVE`.  The Path-D authorization becomes **`ACCEPTED / FROZEN / EFFECTIVE`** only **after independent confirmation of THIS bookkeeping commit**, and only after that may the execution-authorization lineage advance to the next explicitly governed execution step.  **Execution remains closed until confirmation:** NO authorization-use claim, NO attempt-use claim, NO Oracle-PathD execution, NO ETB execution, NO listener query, NO budget consumption, NO evidence, NO manifest, NO result — and no status surface implies otherwise.  **MODEL A preserved:** no runtime/generated Path-D artifact became tracked, current operational artifacts remain untouched, and the Path-D namespace remains empty; the current inventory is `git status --porcelain` collapsed entries `13` / expanded untracked files `17` / composition `12 historical operational files + 5 accepted D1 operational files`.  This bookkeeping round performed **0** authorization-use claim creations, **0** attempt-use claim creations, **0** Oracle-PathD executions, **0** ETB executions, **0** listener queries, **0** `Get-NetTCPConnection` calls, **0** budget consumptions, **0** evidence/manifest/result creations, **0** endpoint-state modifications, **0** OpenCode starts/restarts, **0** reviewed-artifact mutations and **0** runtime/test/dependency/version changes.  The exact next stage is **independent Path-D authorization acceptance-bookkeeping confirmation** (review-only, no commit), which must verify this bookkeeping commit against candidate `29bf27fc2f76d415eb9c07d890f50b665aca6846` and the third-party review authority.  No tag, no release and no push occurred.

**PATH-D AUTHORIZATION CONFIRMATION-RECORD CLOSURE — REPOSITORY-VERIFIABLE MATERIALIZATION OF THE COMPLETED THIRD-PARTY CONFIRMATION (governance record only; nothing executed, no claim created, no budget consumed, no reviewed artifact modified).**  This is a **GOVERNANCE-ONLY record-closure round**: it does **not** retry the ETB, does **not** re-run or re-authorize Oracle-PathD, does **not** perform a second authorization acceptance, does **not** produce a new authorization design, does **not** grant new owner execution authorization, does **not** consume any claim, and performs **no** operational action.  **Recovered precedent (structure determined by existing precedent, not invented):** the DevRelay bookkeeping-structure contract already frozen by the accepted Recovery-R2 authorization (`PRE-1`, §11.4 and §11.7) requires that a governed state transition become a repository-verifiable fact through **exactly ONE single-parent child commit whose sole tracked delta against its parent is `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md` and NO third tracked path**, with the active status surfaces stating the accepted state bound to the accepted identity pair; the recovered two-file bookkeeping-shape precedent is `9b17912…`, which is itself a **single-parent** commit with exactly that two-file delta.  **That precedent determines this round's shape; no new structure was invented and no confirmation artifact was created.**  The **third-party independent confirmation** of the Path-D authorization acceptance bookkeeping — completed in the immediately preceding round as a **review-only event with no commit** — is hereby **materialized as a repository-verifiable fact**: `CONFIRMATION VERDICT = APPROVE V0.3-E PATH-D AUTHORIZATION ACCEPTANCE-BOOKKEEPING CONFIRMATION`; `CONFIRMED BOOKKEEPING COMMIT = a7e3cccf5fa50a127ce92c2ed3529da1e926d5ed`; `CONFIRMED AUTHORIZATION DESIGN = 29bf27fc2f76d415eb9c07d890f50b665aca6846`; `THIRD-PARTY INDEPENDENCE = SATISFIED`; `CONFIRMATION RESULT = P0 = 0, P1 = 0, P2 = 0, P3 = 3`.  **Repository-verifiable effectivity contract (frozen by this record; derivable only from Git commit topology plus tracked status-surface bytes plus frozen authorization artifact identity — never from chat history, conversation transcripts or agent memory):** (1) authorization design commit `path_d_authorization_commit = 29bf27fc2f76d415eb9c07d890f50b665aca6846`; (2) authorization artifact `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_D_AUTHORIZATION.md` with committed-blob SHA-256 `path_d_authorization_sha256 = 49e7c29a4c2367764aba195931908c627b9c7226725c76e66b1ef60eecb6f9bf`; (3) acceptance-bookkeeping commit `a7e3cccf5fa50a127ce92c2ed3529da1e926d5ed`; (4) third-party confirmation of that bookkeeping commit `= APPROVED` with `THIRD-PARTY INDEPENDENCE = SATISFIED`; (5) `PATH-D AUTHORIZATION = ACCEPTED / FROZEN / EFFECTIVE`; (6) `PATH_D_AUTHORIZATION_USE = 0 OF 1 / NOT CONSUMED` and `PATH_D_ETB_ATTEMPT = 0 OF 1 / NOT STARTED`.  **Mechanical recognition rule for a future executor (topology plus content, requiring no external testimony):** the confirmation-record commit is the **single-parent** commit whose parent is exactly `a7e3cccf5fa50a127ce92c2ed3529da1e926d5ed`, whose sole tracked delta against that parent is **exactly** `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md` (**no third tracked path**), and whose active status surfaces state `PATH-D AUTHORIZATION = ACCEPTED / FROZEN / EFFECTIVE` bound to design commit `29bf27fc2f76d415eb9c07d890f50b665aca6846` and artifact SHA-256 `49e7c29a4c2367764aba195931908c627b9c7226725c76e66b1ef60eecb6f9bf`; all of those conditions hold simultaneously and are checked mechanically.  **No self-reference:** this record deliberately does **not** embed its own commit SHA — it is identified only by its parent, its subject, its changed-path set and the frozen provenance stated here; the subject is `docs(v03e): record Path-D authorization confirmation`, which is **not** an acceptance subject and does **not** imply a second acceptance-bookkeeping event.  **Anti-recursion (no new effectivity dependency is created):** this confirmation record becomes the repository-verifiable **effectivity fact**, and the follow-up **third-party read-only verification of this closure** is a **verification of an existing record, not a new acceptance or effectivity event** — it spawns **no** further record commit, **no** recursive lifecycle and **no** additional dependency chain.  **Prior stopped operational round recorded as governance fact only (it is NOT a retry and does NOT create an attempt number):** `OPERATIONAL ROUND 1 = STOPPED BEFORE CONSUMPTION`; `FAILED GATE = PRE-2`; `CAUSE = the independent confirmation of a7e3ccc… was not yet repository-verifiable, so "authorization effectivity established as repository fact" could not be mechanically proven`; `AUTHORIZATION CONSUMPTION = NONE`; `ATTEMPT CONSUMPTION = NONE`; `ORACLE INVOCATIONS = 0`; `LISTENER QUERIES = 0`; `GENERATED PATH-D ARTIFACTS = NONE`; `FAILURE CLASS = A. PRECONDITION_FAILURE_BEFORE_CONSUMPTION`; it consumed **no** retry budget and created **no** attempt number, and every Path-D path remained **ABSENT** (`PATH-D RUNTIME OCCUPANCY = 0 / 11`).  **Authoritative root cause recorded (not repaired by rewriting confirmed bytes):** the Path-D authorization artifact never froze an explicit recording carrier for the confirmation event, unlike the Recovery-R2 authorization which froze acceptance bookkeeping as exactly one child commit plus two status surfaces; and because confirmation was correctly designed as a review-only event, it produced no repository object — this round supplies exactly that missing repository object and nothing more.  **Budgets remain pristine and untouched by this record:** `PATH_D_AUTHORIZATION_USE_BUDGET = 1 OF 1` with `PATH_D_AUTHORIZATION_USE = 0 OF 1 / NOT CONSUMED`; `PATH_D_ETB_ATTEMPT_BUDGET = 1 OF 1` with `PATH_D_ETB_ATTEMPT = 0 OF 1 / NOT STARTED`; every historical budget remains spent and not reusable — original Round-5 authorization `SPENT / NOT REUSABLE`, Recovery-R1 `SPENT / NOT REUSABLE`, Recovery-R2 authorization / attempt `SPENT / NOT REUSABLE`, `D1 AUTHORIZATION / DIAGNOSTIC ATTEMPT = SPENT / 1 OF 1 / IRREVERSIBLE / NOT REUSABLE`, `D1 LISTENER QUERY = EXECUTED ONCE / NO RETRY`.  **Execution remains closed:** `PATH-D ETB EXECUTION = NOT AUTHORIZED`; `ORACLE-PATHD EXECUTION = NOT AUTHORIZED`; `LISTENER QUERY = NOT EXECUTED`; NO authorization-use claim, NO attempt-use claim, NO evidence, NO manifest, NO result; this record grants **no** execution effectivity and collapses **no** execution stage.  **Result authority preserved:** `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED`; a confirmation record creates **no** semantic result, and any future Path-D execution observation must still pass **independent result review → result bookkeeping → independent bookkeeping confirmation** before becoming authoritative.  **MODEL A preserved:** no runtime/generated Path-D artifact became tracked; all operational artifacts remain untracked and byte-unchanged; the current untracked inventory terminology is frozen precisely — `git status --porcelain` collapsed entries `13`, expanded untracked files `17`, composition `12 historical operational files + 5 accepted D1 operational files`.  **Historical immutability preserved:** the Path-D authorization artifact, the Oracle-PathD spec and executable, Oracle-R2, Recovery-R1, Recovery-R2, D1, the original oracle artifacts, `.gitattributes`, all claims, evidence, manifests, results, configuration and construction-time banners are **byte-unchanged**, and no P3 observation was "fixed" by rewriting any reviewed or confirmed byte.  This governance record round performed **0** authorization-use claim creations, **0** attempt-use claim creations, **0** Oracle-PathD executions, **0** ETB executions, **0** listener queries, **0** `Get-NetTCPConnection` calls, **0** budget consumptions, **0** evidence/manifest/result creations, **0** config mutations, **0** endpoint-state modifications, **0** OpenCode starts/restarts, **0** HTTP, **0** provider/model calls, **0** reviewed-artifact mutations and **0** runtime/test/dependency/version changes.  **Exact next stage:** **third-party read-only verification of the Path-D authorization confirmation-record closure** (read-only; no commit required and none expected); the next **operational** stage — a fresh-agent Path-D one-shot operational round — is **not** authorized by this record and requires its own explicit owner authorization.  No tag, no release and no push occurred.

**PATH-D POST-CLOSURE LISTENER-PROBE GOVERNANCE RECONCILIATION — CORRECTIVE SUCCESSOR RECORD (governance record only; nothing executed, no probe performed, no claim created, no budget consumed, no reviewed artifact modified).**  This round performs **exactly one** narrow corrective governance act: it corrects a **false tracked governance fact** created by `c1d7bd38be16ee7807c98044cdd8f17d83e97729` **without rewriting, amending, deleting or reinterpreting that commit**, which remains permanently immutable.  **Recovered correction precedent (determinative at shape level; no new structure invented, no third path created):** the DevRelay corrective-successor pattern is `docs(v03e): <verb> <object>` realized as **exactly one single-parent successor commit** whose tracked delta is **exactly** `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md` (**no third path**) — the closest shape analogue is `75313c9` (`2 0` CHANGELOG / `1 1` ACCEPTANCE, two files only), the `clarify` family shows 3 prior instances and the `correct` family 3 prior instances, and the accepted vocabulary already uses **explicit supersession language** for superseded governance facts (e.g. the `(Historical round entry — superseded by the … entry below, …)` markers).  **Nothing was rewritten:** the faulty commit's bytes are untouched and the supersession is declared only inside this successor record.  **FAULTY CLOSURE RECORD = `c1d7bd38be16ee7807c98044cdd8f17d83e97729`** (parent `a7e3cccf5fa50a127ce92c2ed3529da1e926d5ed`).  **THE EXACT FALSE PRIOR ACTIVITY ASSERTION (quoted verbatim from the closure record for unambiguous identification — NOT deleted, NOT rewritten):** the closure record asserted that the closure round performed **0** listener queries and **0** `Get-NetTCPConnection` calls — in the CHANGELOG as: This governance record round performed **0** authorization-use claim creations, **0** attempt-use claim creations, **0** Oracle-PathD executions, **0** ETB executions, **0** listener queries, **0** `Get-NetTCPConnection` calls, **0** budget consumptions, … — and in the active acceptance row with the substantively identical wording This round performed 0 authorization-use claim creations, … 0 listener queries, 0 `Get-NetTCPConnection` calls, …  **That activity-count assertion is SUPERSEDED by this successor governance record.**  **CORRECTED CLOSURE-ROUND ACTIVITY HISTORY (authoritative):** listener queries = **1 OUT-OF-BAND READ-ONLY PROBE**; `Get-NetTCPConnection` calls = **1**; authoritative listener observations = **0**; Path-D operational-attempt listener queries = **0**; Oracle-PathD listener queries = **0**; budget-consuming listener actions = **0**; and every other closure-round count stood unchanged: authorization-use claim creations = **0**; attempt-use claim creations = **0**; Oracle-PathD executions = **0**; ETB executions = **0**; budget consumptions = **0**; evidence/manifest/result creations = **0**; config mutations = **0**; endpoint-state modifications = **0**; OpenCode starts/restarts = **0**; HTTP = **0**; provider/model calls = **0**; reviewed-artifact mutations = **0**; runtime/test/dependency/version changes = **0**.  **OUT-OF-BAND PROBE — frozen semantics:** `OUT-OF-BAND PROBE COMMAND = Get-NetTCPConnection -LocalPort 4096`; `ROUND = confirmation-record closure construction round`; `TIMING = after c1d7bd3 commit creation, during final snapshot/reporting activity of that same governance round`; `OBSERVATION = zero listener rows`; `AUTHORITY = NON-AUTHORITATIVE / MUST NOT BE REUSED`; `CONTRACT STATUS = PROHIBITED PRE-ORACLE PROBE` (the accepted Path-D authorization §14.1 forbids running `Get-NetTCPConnection`, listener/process enumeration and port scan before Oracle-PathD entry, §14.2 assigning target binding exclusively to Oracle-PathD); `CONSUMPTION EFFECT = NONE`; `AUTHORIZATION BUDGET EFFECT = NONE`; `ATTEMPT BUDGET EFFECT = NONE`; `ORACLE INVOCATION EFFECT = NONE`; `PATH-D RUNTIME ARTIFACT EFFECT = NONE`; `FUTURE ORACLE LISTENER QUERY = STILL PERMITTED BY THE ACCEPTED CONTRACT`.  **The zero-row result MUST NOT become an ETB semantic input** and is **not** `ETB_SATISFIED`, **not** `ETB_UNSATISFIED`, **not** `HARNESS_INVALID` and not any semantic ETB result — it is governance history only.  **No `PRE-*` reinterpretation:** the accepted Path-D `PRE-1`…`PRE-15` contract contains **NO** prior-listener-query-history precondition; **no new gate was added**, **no `PRE-16` was created**, and the disclosed probe was **not** converted into an authorization or attempt consumption event; the accepted authorization artifact was not modified.  **The next Oracle-PathD listener query is NOT a retry and NOT a second attempt-internal listener query** — the accepted contract scopes listener-query counting only to an actually-started Path-D operational attempt, and `PATH_D_ETB_ATTEMPT = 0 OF 1 / NOT STARTED`.  **Effectivity preserved and explicitly NOT rolled back:** `PATH-D AUTHORIZATION = ACCEPTED / FROZEN / EFFECTIVE / REPOSITORY-VERIFIABLE`.  The bound third-party verification result established `CONFIRMATION-RECORD STRUCTURE = EXACT / BOUNDED`, `CONFIRMATION_RECORD_PRECEDENT = DETERMINATIVE AT SHAPE LEVEL`, `PATHD_EFFECTIVITY_REPOSITORY_VERIFIABILITY = ESTABLISHED`, `OUT_OF_BAND_LISTENER_PROBE = PROHIBITED-BUT-NONCONSUMING`, `LISTENER_QUERY_HISTORY_FOR_NEXT_OPERATION = NONPRISTINE-BUT-PERMITTED`, `REPOSITORY_HISTORY = MATERIALLY FALSE`, `SEVERITY = P0 = 0 / P1 = 0 / P2 = 1 / P3 = 0`, the single P2 being exactly that the two tracked normative status surfaces stated a closure-round activity count that the disclosed probe directly contradicts.  **Corrected readiness state:** `PATH-D OPERATIONAL READINESS = BLOCKED PENDING THIRD-PARTY VERIFICATION OF THIS RECONCILIATION` — the blocker is **operational readiness**, **not** authorization acceptance or effectivity, which remain established.  **Prior stopped operational round preserved and NOT conflated:** `OPERATIONAL ROUND 1 = STOPPED BEFORE CONSUMPTION`; `FAILED GATE = PRE-2`; `FAILURE CLASS = A. PRECONDITION_FAILURE_BEFORE_CONSUMPTION`; `AUTHORIZATION CONSUMPTION = NONE`; `ATTEMPT CONSUMPTION = NONE`; `ORACLE INVOCATIONS = 0`; `GENERATED PATH-D ARTIFACTS = NONE`; `LISTENER QUERY DURING THAT OPERATIONAL ROUND = 0` — that remains true, because the disclosed out-of-band probe occurred in a **different** governance round.  **Budgets remain pristine and untouched by this reconciliation:** `PATH_D_AUTHORIZATION_USE_BUDGET = 1 OF 1` with `PATH_D_AUTHORIZATION_USE = 0 OF 1 / NOT CONSUMED`; `PATH_D_ETB_ATTEMPT_BUDGET = 1 OF 1` with `PATH_D_ETB_ATTEMPT = 0 OF 1 / NOT STARTED`; `ORACLE-PATHD INVOCATIONS = 0`; every historical budget remains `SPENT / NOT REUSABLE`.  **Runtime occupancy:** `PATH-D RUNTIME OCCUPANCY = 0 / 11` — all four Path-D claim paths and all Path-D output paths ABSENT; no operational artifact was created.  **Result authority preserved:** `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`.  **MODEL A preserved:** no runtime/generated Path-D artifact became tracked; the untracked inventory terminology is frozen precisely — `git status --porcelain` collapsed entries `13`, expanded untracked files `17`, composition `12 historical operational files + 5 accepted D1 operational files`, all bytes unchanged.  **THIS reconciliation round performed ZERO listener queries:** no `Get-NetTCPConnection`, no `netstat`, no `Get-NetConnectionProfile` or equivalent target probe, no port 4096 scan, no `localhost`/`127.0.0.1` probe, no HTTP, no OpenCode query — the fact to be recorded was already established by the disclosed prior-round event and was deliberately **not** reproduced.  **Frozen artifacts byte-unchanged:** the Path-D authorization artifact (`49e7c29a4c2367764aba195931908c627b9c7226725c76e66b1ef60eecb6f9bf`), the Oracle-PathD spec (`15e39452f5efae1f87f03e38fd72ca3336fe3b591affbd93c9104e785fa9884b`), the Oracle-PathD executable (`8bdeb434794c43fe4a199e7338790ba0dbd319728b6766d54299c894a16ac738`), Oracle-R2, Recovery-R1, Recovery-R2, D1, `.gitattributes`, configuration, claims, evidence, manifests, results and construction-time banners are all untouched, and this round modifies only these two active status surfaces.  **Remote-state distinction (reported separately and deliberately NOT reconciled):** `LOCAL REMOTE-TRACKING REF origin/main = 345694265b4df99ebb1ae08724dde7e27b3f89cb`; `LIVE REMOTE REF refs/heads/main = 83b0ae44457736d0fff06d65dad2fc4b6433376c` (observed by the prior independent verifier; absent from the local object database) — treated as **unrelated remote drift**; live-remote equality is explicitly **NOT** a gate for this governance correction, and no fetch, merge, reset or rebase was performed.  **Exact next stage:** `THIRD-PARTY READ-ONLY VERIFICATION OF PATH-D POST-CLOSURE LISTENER-PROBE GOVERNANCE RECONCILIATION`, which must verify the correction successor structure, verify that `c1d7bd3` remains immutable, verify that the actual probe is now truthfully represented and remains non-authoritative, verify budgets remain pristine, verify that no new listener probe occurred, and decide whether operational readiness can now become READY; that review creates **no** new effectivity dependency and, if it approves, **no** additional correction-record commit is required.  No tag, no release and no push occurred.

**PATH-D ONE-SHOT OPERATIONAL RESULT ACCEPTANCE BOOKKEEPING — THIRD-PARTY RESULT REVIEW APPROVED (governance bookkeeping only; nothing executed, no claim created, altered or deleted, no budget reset, no output synthesized, no reviewed artifact modified).**  This round records the **third-party independently reviewed execution outcome** of the already-completed, irreversible Path-D one-shot operational round.  It is **not** an ETB retry, **not** an Oracle retry, **not** a new operational attempt, **not** a new authorization, **not** a new Path-D lineage, **not** a repair round, **not** an Oracle modification round, **not** claim cleanup, **not** budget reset and **not** result synthesis.  **Recovered bookkeeping precedent (shape determinative; no new structure invented):** the accepted DevRelay result-bookkeeping pattern is **exactly one single-parent commit whose sole tracked delta is `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md`, with NO third tracked path** — precedents `93e44fe` (`docs(v03e): accept Recovery-R2 ETB unsatisfied result`, two files, `71 0` CHANGELOG / `2 2` ACCEPTANCE) and `0bd9720` (`docs(v03e): accept D1 diagnostic result`, two files, `2 0` / `1 1`), with the same shape recurring at `806ade0`, `a7e3ccc`, `c1d7bd3` and `81d1feb`.  **Critically, there is NO Path-D Oracle result artifact to accept or modify** — the operative Path-D output namespace is entirely ABSENT, and the historical result files of other lineages (`…_EXECUTION_RESULT_R2.md`, `…_QUERY_DIAGNOSTIC_RESULT_D1.md`) are deliberately MODEL A **untracked** and were never modified by their own bookkeeping commits; accordingly **no result artifact was invented** merely to imitate another lineage, and the narrow two-status-surface model is used.  **Subject discipline:** the form `docs(v03e): record Path-D operational outcome` is used rather than `docs(v03e): accept Path-D operational result`, because `PATH-D ETB SEMANTIC RESULT = NONE` in this round and a "result" subject would falsely imply that a semantic ETB result exists; the governing precedent family is the `record <failure fact>` family (`docs(v03e): record G0.5 oracle reachability gap`, `docs(v03e): record authoritative G0.4 proof failure`, `docs(v03e): record failed G0.4 installed-API proof`, `docs(v03e): record failed G0.3 transport proof`).  **BOUND IDENTITIES:** operational authorization design = `29bf27fc2f76d415eb9c07d890f50b665aca6846`; operational governance HEAD = `81d1febf954fbe26514ef56ccac8f08d1aa4eedc`; authorization FINAL claim SHA-256 `5e33a8f3da06ba36582b357fb114011e51bae30cafae1449a9c90de59f3ef017`; attempt FINAL claim SHA-256 `64f86fcc7f3d63501b32dba5a5bf0905173002ee55d6ec008bed527472653db0`.  **THIRD-PARTY RESULT REVIEW VERDICT (bound exactly):** `REVIEWED EXECUTION OUTCOME = UNCLASSIFIED CONTROL FAILURE / NO ETB SEMANTIC RESULT`; `ORACLE-REPORTED CLASSIFICATION = NONE`; `PATH-D ETB SEMANTIC RESULT = NONE`; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`; `PATH-D EXECUTION OUTPUTS = NONE`; `RETRY AUTHORITY = NONE`.  **Rejected narrative classification (recorded as a review correction, NOT adopted into governance history):** the earlier operational narrative phrase `MODEL-CLASS EQUIVALENT (NOT ORACLE-REPORTED) = HARNESS_INVALID / NO ETB SEMANTIC RESULT` was **REJECTED BY THIRD-PARTY RESULT REVIEW** and is **NOT** adopted; the accepted replacement is `UNCLASSIFIED CONTROL FAILURE / NO ETB SEMANTIC RESULT`.  This correction applies to the **narrative classification only** and does **not** alter immutable execution facts.  **No `HARNESS_INVALID` class is accepted as the reviewed Path-D execution outcome**, and **no fourth ETB semantic class is created**: the operational outcome label is an **OBSERVATION DESCRIPTOR**, and the closed Oracle semantic class set remains exactly `ETB_SATISFIED`, `ETB_UNSATISFIED`, `HARNESS_INVALID / NO ETB SEMANTIC RESULT`.  **Why retrospective `HARNESS_INVALID` is rejected (classification authority):** every result classification belongs **exclusively** to the accepted Oracle-PathD executable (authorization §13.3); the Oracle **emitted no classification** and **published no result**; exit code `1` is an "other termination" that under the accepted Oracle contract (spec §13.5) produces **no trusted output** rather than a class; and **no accepted rule** allows an independent reviewer to execute the missing `HARNESS_INVALID` branch retrospectively.  **IRREVERSIBLE CONSUMPTION STATE (verified, irreversible historical facts):** `PATH-D AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `PATH-D ETB ATTEMPT = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `ORACLE-PATHD INVOCATIONS = 1 OF 1 / MAXIMUM REACHED`.  Neither budget is available and the attempt is **not** retryable.  **Immutable claim identities:** authorization FINAL claim `docs/v0.3/evidence/ETB_PATH_D_AUTHORIZATION_USE.claim` **PRESENT**, `495` bytes, SHA-256 `5e33a8f3da06ba36582b357fb114011e51bae30cafae1449a9c90de59f3ef017`, schema `devrelay-etb-path-d-authorization-use-v1`, `state = CONSUMED`; attempt FINAL claim `docs/v0.3/evidence/ETB_PATH_D_ATTEMPT_USE.claim` **PRESENT**, `489` bytes, SHA-256 `64f86fcc7f3d63501b32dba5a5bf0905173002ee55d6ec008bed527472653db0`, schema `devrelay-etb-path-d-attempt-use-v1`, `state = CONSUMED`; both `.tmp` paths **ABSENT**; both FINAL claims remain **UNTRACKED / UNSTAGED / UNCOMMITTED / BYTE-IMMUTABLE** and unmodified.  **Reviewed immutable execution observation:** Oracle command `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1"` (no parameters, no wrapper); `process started = YES`; reported `PID = 13872`; reported start `2026-09-29T12:56:52.8074598Z`; reported end `2026-09-29T12:56:53.1494528Z`; reported duration `369 ms`; `exit code = 1`; `stdout = 0 bytes`; stderr trigger `CommandNotFoundException` for `Get-FileHash` at `V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_D.ps1` **line 117, character 19**; `Oracle listener query reached = NO`; `evidence published = NO`; `manifest published = NO`; `result published = NO`; `output namespace created = NO`.  **Transient PID/time facts are reviewed execution observations, NOT independently reproducible repository facts**, and are recorded as such.  **PROCESS TERMINATION (independently reviewed wording; `EXITED_NORMALLY` is NOT carried forward as an accepted semantic description):** `OS PROCESS EXITED ON ITS OWN / EXIT CODE 1 / UNCAUGHT TERMINATING POWERSHELL ERROR / SCRIPT DID NOT COMPLETE`.  **ORACLE IMPLEMENTATION DEFECT = YES / NOT REPAIRED (reviewed finding, carried forward):** `Get-FileHash` is first used unprotected at **line 117** and again at **line 118**, while its availability is only checked later at **line 189**; the line-189 infrastructure gate **includes** `Get-FileHash` but was **unreachable** because the first unprotected use already terminated the script.  Consequences established by review: the intended `HARNESS_INVALID` branch was not reached; evidence publication was not reached; manifest publication was not reached; result publication was not reached; the listener query was not reached; target binding was not reached; S0/S1 continuity was not reached; the one-shot attempt ended before any ETB semantics; and process exit code `1` fell outside the Oracle's intended `0`/`3` completion model.  **The defect is NOT repaired in this round and the frozen Oracle artifacts are NOT modified** — repairing them would mutate independently reviewed and accepted bytes, which the authorization forbids.  **Immediate trigger / root cause kept distinct:** `IMMEDIATE EXECUTION TRIGGER = COMMAND UNAVAILABLE / Get-FileHash CommandNotFoundException`; `ENVIRONMENTAL ROOT CAUSE = PLAUSIBLE-BUT-NOT-PROVEN` (no repository object records the runtime module inventory, `PSModulePath`, host configuration or any constrained-mode state, so **no specific deeper environment cause is claimed** — neither a definitely-missing PowerShell module nor a definitely-misconfigured harness); `ORACLE CONTROL-FLOW CONTRIBUTION = ESTABLISHED`.  **Reviewed severity findings carried forward (findings about the Oracle and the execution — distinct from this bookkeeping commit, which is P0 = 0, P1 = 0, P2 = 0):** `P0 = 0`, `P1 = 1`, `P2 = 2`, `P3 = 3`; `P1-1 = Oracle implementation/control-flow defect: Get-FileHash used before its own availability gate; real defect; NOT REPAIRED; NO RETRY implied`; `P2-1 = the operational report's retrospective HARNESS_INVALID equivalence was not authorized by the frozen contract and is rejected`; `P2-2 = the frozen lifecycle has no dedicated ETB semantic label for this uncaught pre-classifier termination; the accepted bookkeeping label is an observation descriptor, not a fourth ETB class`; `P3 = EXITED_NORMALLY wording must not be carried forward; prior design reviews did not detect the line-117 ordering defect; transient process facts have evidentiary limitations`.  **Listener-query ownership (recorded; no query was run in this bookkeeping round):** external pre-Oracle listener queries in the operational round = `0`; Oracle listener query reached = `0`; supplemental/concurrent listener queries = `0`; the historical governance-round out-of-band probe = **NOT REUSED**.  **Output state (read-only verified):** `docs/v0.3/evidence/etb-execution-path-d/` **ABSENT**; `ETB_EVIDENCE.json` **ABSENT**; `ETB_EVIDENCE.json.tmp` **ABSENT**; `MANIFEST.sha256` **ABSENT**; `MANIFEST.sha256.tmp` **ABSENT**; `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_D.md` **ABSENT**; `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_D.md.tmp` **ABSENT** — nothing was synthesized and no substitute result artifact was created.  **Result-authority state preserved exactly:** `PATH-D ETB SEMANTIC RESULT = NONE`; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`.  This bookkeeping accepts an **execution outcome record**; it does **not** create a new ETB semantic result and does **not** replace the existing authoritative `ETB_UNSATISFIED` result.  **NO-RETRY STATE:** `RETRY AUTHORITY = NONE`; `PATH-D ORACLE RERUN UNDER THIS AUTHORIZATION = PROHIBITED`; `CLAIM DELETION TO REOPEN BUDGET = PROHIBITED`; `BUDGET RESET = PROHIBITED`; `"FIX Get-FileHash AND TRY AGAIN UNDER PATH_D" = PROHIBITED`.  Any possible future attempt would require an entirely **new owner-governed lineage**; **that lineage is NOT designed here**.  **MODEL A preserved:** the two Path-D claims remain **UNTRACKED / UNSTAGED / UNCOMMITTED / BYTE-IMMUTABLE**; the untracked inventory terminology is frozen precisely — `git status --porcelain` collapsed entries `15`, expanded untracked files `19`, composition `12 historical operational files + 5 accepted D1 operational files + 2 Path-D claim files`.  **Frozen artifact immutability verified before and after bookkeeping:** Path-D authorization artifact SHA-256 `49e7c29a4c2367764aba195931908c627b9c7226725c76e66b1ef60eecb6f9bf`; Oracle-PathD spec SHA-256 `15e39452f5efae1f87f03e38fd72ca3336fe3b591affbd93c9104e785fa9884b`; Oracle-PathD executable SHA-256 `8bdeb434794c43fe4a199e7338790ba0dbd319728b6766d54299c894a16ac738`; all three plus `.gitattributes` and the two claims remain byte-identical.  **TWO-STAGE RESULT BOOKKEEPING EFFECTIVITY (bookkeeping and confirmation are NOT collapsed):** the accepted sequence is one-shot execution completed → third-party result review APPROVED → **THIS result acceptance bookkeeping commit** → **independent confirmation of THIS bookkeeping commit** → only after that does the Path-D operational outcome record become **ACCEPTED / FROZEN** as reviewed governance history → then owner reconciliation.  Immediately after this commit: `PATH-D OPERATIONAL RESULT REVIEW = APPROVED`; `PATH-D OPERATIONAL RESULT ACCEPTANCE BOOKKEEPING = COMMITTED / PENDING INDEPENDENT CONFIRMATION`; `PATH-D OPERATIONAL OUTCOME = UNCLASSIFIED CONTROL FAILURE / NO ETB SEMANTIC RESULT / NOT YET FROZEN AS BOOKKEEPED GOVERNANCE HISTORY`; `PATH-D ETB SEMANTIC RESULT = NONE`; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`.  The absence of an ETB semantic result remains unchanged throughout.  This bookkeeping round performed **0** Oracle-PathD executions, **0** ETB executions, **0** `Get-NetTCPConnection` calls, **0** listener queries, **0** port-4096 or `localhost`/`127.0.0.1` probes, **0** OpenCode starts/restarts, **0** HTTP calls, **0** claim creations, **0** claim modifications or deletions, **0** budget resets, **0** evidence/manifest/result creations, **0** output syntheses and **0** frozen-artifact mutations.  **Exact next stage:** `THIRD-PARTY INDEPENDENT PATH-D OPERATIONAL RESULT ACCEPTANCE-BOOKKEEPING CONFIRMATION` (read-only, no commit, no Oracle, no listener query, no claim mutation, no retry).  No tag, no release and no push occurred.

**PATH-E / ORACLE-PATHE — NEW ETB LINEAGE EXECUTION-ORACLE DESIGN CANDIDATE (design and governance only; nothing executed, no budget created or consumed, no claim created, no runtime namespace occupied, no Path-D artifact modified).**  **OWNER DECISION = OPEN A NEW ETB LINEAGE**; `NEW LINEAGE = PATH E — NEW ETB ATTEMPT`; `NEW EXECUTION ORACLE = Oracle-PathE`; canonical lineage token `PATH_E`; canonical oracle token `ORACLE_PATH_E`.  **This is a NEW lineage and explicitly NOT** a retry of Path D, `Recovery-R3`, `Oracle-R3`, `Oracle-D`, `Oracle-PD`, `Oracle-PathD2`, a reuse of Path-D authorization, a reset of Path-D budgets, or a repair-and-rerun of Oracle-PathD; historical naming exclusions remain historical and preserved, and none of those identifiers is used as an active oracle identity.  **Path-D terminal state preserved unchanged as frozen historical fact:** `PATH-D AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `PATH-D ETB ATTEMPT = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `ORACLE-PATHD INVOCATIONS = 1 OF 1 / MAXIMUM REACHED`; `PATH-D BOOKKEEPED OPERATIONAL OUTCOME = UNCLASSIFIED CONTROL FAILURE / NO ETB SEMANTIC RESULT / ACCEPTED / FROZEN AS GOVERNANCE HISTORY`; `PATH-D ETB SEMANTIC RESULT = NONE`; `PATH-D EXECUTION OUTPUTS = NONE`; `PATH-D RETRY AUTHORITY = NONE`; `PATH-D LINEAGE = EXHAUSTED / CLOSED` — **Path D is not reopened, not repaired and not rerun.**  **Design motivation — the reviewed predecessor defect (carried forward, NOT repaired in the frozen artifact):** `ORACLE-PATHD IMPLEMENTATION DEFECT = YES / ACCEPTED / NOT REPAIRED`; `Get-FileHash` was **used** unprotected at the predecessor's **lines 117 and 118** for oracle self-identity while its availability was only **checked** at **line 189**, inside an infrastructure gate whose own list **includes** `Get-FileHash`, making that gate unreachable in exactly the scenario it exists to handle; the observed consequences were that the intended infrastructure `HARNESS_INVALID` path was never reached, evidence/manifest/result publication was never reached, the listener query was never reached, target binding was never reached, S0/S1 were never reached, the one-shot attempt terminated before any ETB semantics, and exit code `1` fell outside the intended `0`/`3` oracle completion contract.  **Normative correction frozen in the new candidate:** `NO REQUIRED COMMAND MAY BE USED BEFORE ITS REQUIRED-AVAILABILITY CONDITION HAS BEEN SAFELY ESTABLISHED`; in particular `Get-FileHash` must not be invoked before Oracle-PathE has safely established whether it is available — and Oracle-PathE satisfies this **by never calling `Get-FileHash` at all**.  **Candidate identity (immutable once accepted, currently NOT accepted):** spec `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.md` (496 lines, `21316` bytes) and executable `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.ps1` (`37819` bytes; ASCII-only with `MAXBYTE = 125`, no BOM, `CR = 0`, LF-only, exactly one terminal LF, PowerShell parser errors `0`); the two artifacts are bound by exact-path LF rules in `.gitattributes` (`…PATH_E.ps1 text eol=lf`, **no** wildcard), and `git check-attr` resolves them to `text: set` / `eol: lf`.  **Bootstrap safety model:** an explicit `step 0` BOOTSTRAP SAFETY PHASE runs before every other stage; assumed bootstrap primitives are PowerShell language constructs plus `System.*` type literals and static .NET members of the already-loaded runtime (`System.IO.*`, `System.Text.*`, `System.Security.Cryptography.SHA256`, `System.DateTimeOffset`, `System.Globalization.*`, `System.Environment`) — deliberately replacing `Split-Path`, `Set-Location`, `Get-Content` and `Test-Path` with their .NET equivalents so bootstrap depends on no cmdlet; every other cmdlet or external executable is a **GATED FACILITY** (`python`, `Add-Type`, `Get-NetTCPConnection`, `Get-CimInstance`, `ConvertTo-Json`, `ConvertFrom-Json`) checked in `step 0` before any use; the checker itself (`Test-BootstrapFacility`) is wrapped in `try`/`catch` so that even `Get-Command` being unavailable is reported as an unavailable facility instead of escaping as an uncaught terminating error.  **Self-identity mechanism (frozen, one mechanism only):** `.NET SHA-256` via `[System.Security.Cryptography.SHA256]::Create()` reading the file with `[System.IO.File]::ReadAllBytes` (`Get-Utf8FileSha256`); it is deterministic, reviewable, fail-closed, fully specified and executable before any target probing, and it is also used for the target binary hashes.  **Command-availability ordering (normative invariant: check stage < first-use stage):** `python` check `step 0` / use `step 2`; `Add-Type` check `step 0` / use `step 3`; `Get-NetTCPConnection` check `step 0` / use `step 4`; `Get-CimInstance` check `step 0` / use `step 4`; `ConvertFrom-Json` check `step 0` / use `step 4` and `step 5`; `ConvertTo-Json` check `step 0` / use `step 5`; `Get-FileHash` **not gated because not used at all** (vacuous).  Measured on the candidate revision: last bootstrap-check call at line **215**, earliest gated-facility call at line **225**, and the listener query only at line **359 inside `Take-Snapshot` (lines 351–479)** — the invariant holds, and review must re-measure it independently.  **Failure model (explicit, no unexplained bucket):** EXPECTED INFRASTRUCTURE FAILURES are oracle-classifiable and never escape — unavailable gated facility → `HARNESS_INVALID` with `terminal_stage = infrastructure_command_unavailable:<facility>`; `python` unresolvable/unlaunchable → `config_reader_failure`; `Add-Type` failure → `native_type_load_failure`; P/Invoke or handle-close failure → `HARNESS_INVALID` at the corresponding path stage; listener/process query failure → `ETB_UNSATISFIED`; and infrastructure problems are never silently converted into ETB verdicts nor ETB semantic failures misclassified as `HARNESS_INVALID`.  UNEXPECTED INTERNAL OR HOST FAILURES are caught by a **top-level `trap`** installed before anything else runs, which emits a constant `ORACLE_PATH_E_UNEXPECTED_HOST_FAILURE` surface with `FINAL_CLASSIFICATION=HARNESS_INVALID`, `SEMANTIC_RESULT=NONE` and `exit 4`, capturing no exception text, stack, provider text or environment data.  **Exit-code contract (total; no accidental path):** `0` = completed and published one of the three result classes; `2` = expected infrastructure failure classified but the result could not be published because a publication facility was itself unavailable (fail-closed); `3` = publication/control stage failed after the semantic outcome was decided; `4` = unexpected internal or host failure reached the top-level guard; **the predecessor's undeclared `exit 1` accidental path no longer exists**, and any other value is a defect of the artifact rather than a contract outcome.  **Result-class model unchanged and closed:** exactly `ETB_SATISFIED`, `ETB_UNSATISFIED`, `HARNESS_INVALID / NO ETB SEMANTIC RESULT`; the only writers of the semantic outcome assign one of those three; **no fourth class is introduced** and the historical Path-D governance phrase `UNCLASSIFIED CONTROL FAILURE` is **not** a class of this oracle (it appears only inside a non-normative comment recording what must not be resurrected); no `PASS`/`FAIL`/`PARTIAL`/`UNKNOWN`/`PROBABLE`/`RETRY` is a result class (`PASS`/`FAIL` are `$Checks` status values only, as in the predecessor).  **Target semantic question preserved and NOT weakened:** endpoint `http://127.0.0.1:4096`; listener predicate `LocalAddress = 127.0.0.1` / `LocalPort = 4096` / `State = Listen`; expected target executable SHA-256 `578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35`; accepted target path `C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe`; package `opencode-ai`; version `1.18.11`; bin `opencode`; Mode P with no endpoint discovery, no fallback, no alternate port, no `localhost` alias, no IPv6 alternate, no OpenCode start/restart, no HTTP, no `/doc`, no `/session` and no provider/model call.  **Listener ownership preserved:** the exact listener query belongs only to Oracle-PathE inside the snapshot stage after the bootstrap phase; there is no external authorization-layer target/listener pre-probe, and the historical Path-D or out-of-band observations are **not** reused as Path-E evidence.  **Target-binding sequence preserved in full:** listener uniqueness → `OwningProcess` → PID → `Win32_Process` → `ExecutablePath` → `CreationDate` → PID + `CreationDate.Ticks` process-instance identity → `CreateFileW`/`GetFinalPathNameByHandleW` canonicalization → exact canonical path equality → binary SHA-256 → package identity (name/version/declared bin canonicalized and compared) → S0 → S1 → S0/S1 continuity over the frozen field set; the only implementation change is that binary SHA-256 uses the .NET primitive, which is not a semantic change.  **Publication model preserved (fail-closed, no overwrite):** six-path occupancy precondition, `CreateDirectory`, TEMP `CreateNew` with `FileShare::None`, write, `Flush($true)`, full byte read-back, terminal-LF / no-double-LF / no-BOM assertions, JSON validation including `schema_version`/`outcome`/`listener_probe_outcome` agreement, manifest line `<digest>  <path>`, publication order evidence → manifest → result last, post-move byte verification and semantic re-validation, and a narrow local `try`/`catch` producing the frozen constant publication-failure surface with `exit 3`; **no Path-D output path is referenced anywhere in Oracle-PathE**.  **Namespace reservations (design only; NOTHING created in this round):** runtime namespace `docs/v0.3/evidence/etb-execution-path-e/`; `ETB_EVIDENCE.json{,.tmp}`; `MANIFEST.sha256{,.tmp}`; `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_E.md{,.tmp}`; claims `docs/v0.3/evidence/ETB_PATH_E_AUTHORIZATION_USE.claim{,.tmp}` and `docs/v0.3/evidence/ETB_PATH_E_ATTEMPT_USE.claim{,.tmp}` — all verified ABSENT; evidence schema identity for the future lineage `devrelay-etb-v1-path-e`; Path-E provenance fields `oracle_path_e_commit`/`oracle_path_e_spec_sha256`/`oracle_path_e_script_sha256` recorded as `UNKNOWN` until a future independent approval record populates them, never inferred, defaulted or fabricated.  **Budget model (design only):** NO consumable Path-E budget exists in this round; a future Path-E authorization-design stage may propose `AUTHORIZATION_USE_BUDGET = 1 OF 1` and `ETB_ATTEMPT_BUDGET = 1 OF 1`, but those budgets must not become executable merely because an Oracle-PathE design exists — Oracle acceptance and Path-E authorization acceptance remain separate gates.  **Static adversarial verification (STATIC ONLY; the executable was parsed, never executed):** parser errors `0`; ASCII-only with `MAXBYTE = 125`, no BOM, `CR = 0`, exactly one terminal LF; **`Get-FileHash` command calls = 0**; **bootstrap availability checks precede the first call of every gated facility** (last check line 215 < earliest gated call line 225); `Get-NetTCPConnection` occurs only inside `Take-Snapshot`; Path-D output-namespace references `0`; `ETB_PATH_D_` references `0`; excluded oracle identifiers `Oracle-R3`/`Oracle-D`/`Oracle-PD`/`Oracle-PathD2`/`Recovery-R3` each `0`; result-class set exactly three; no retry, fallback, `Start-Sleep` or `while` logic (only bounded byte-compare and dash-scan `for` loops); exit-code surface exactly `0`/`2`/`3`/`4`.  **Regression test for the Path-D failure (static, non-target-reaching, no budget consumed, no production runtime namespace used):** Property A — zero `Get-FileHash` command calls, so the predecessor's use-before-availability sequence **cannot** recur; Property B — every availability check precedes the first call of every gated facility; Property C — an unavailable required facility sets the terminal `HARNESS_INVALID` outcome with `terminal_stage = infrastructure_command_unavailable:<facility>` and reaches the oracle's own publication/exit path instead of terminating at an unchecked first use.  **Effectivity:** `ORACLE-PATHE = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE`; `PATH-E EXECUTION AUTHORIZATION = NOT DESIGNED / NOT ACCEPTED`; `PATH-E AUTHORIZATION USE = NOT AVAILABLE FOR CONSUMPTION`; `PATH-E ETB ATTEMPT = NOT AVAILABLE FOR CONSUMPTION`; `PATH-E ETB EXECUTION = NOT AUTHORIZED`; `PATH-E OWNER DECISION = NEW ETB LINEAGE AUTHORIZED FOR DESIGN`; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED` (unchanged; this design creates no ETB observation).  **MODEL A preserved:** the untracked inventory terminology is frozen precisely — `git status --porcelain` collapsed entries `15`, expanded untracked files `19`, composition `12 historical operational files + 5 accepted D1 operational files + 2 Path-D claim files` — and no Path-D or historical artifact was deleted, normalized, moved or modified.  **Historical immutability preserved:** the Path-D authorization artifact (`49e7c29a…`), the Oracle-PathD spec (`15e39452…`), the Oracle-PathD executable (`8bdeb434…`, frozen even though it contains the confirmed defect), the Path-D FINAL claims, D1 artifacts, Recovery-R1/R2 artifacts, original ETB artifacts, historical claims, evidence, manifests and results are all untouched.  This design round performed **0** Oracle executions, **0** ETB executions, **0** listener queries, **0** `Get-NetTCPConnection` calls, **0** port-4096 or `localhost`/`127.0.0.1` probes, **0** endpoint probes, **0** OpenCode starts/restarts, **0** HTTP calls, **0** provider/model calls, **0** claim creations, **0** budget creations or consumptions, **0** evidence/manifest/result creations, **0** Path-D modifications and **0** runtime/test/dependency/version changes.  **Exact next stage:** `THIRD-PARTY INDEPENDENT REVIEW OF ORACLE-PATHE DESIGN CANDIDATE`, which must explicitly attempt to reproduce or detect the historical Oracle-PathD `Get-FileHash`-before-availability-gate defect and must independently re-measure the ordering invariant; **acceptance bookkeeping is NOT performed in this round**, and no ETB execution stage may be skipped.  No tag, no release and no push occurred.

**PATH-E / ORACLE-PATHE — AUTHOR REMEDIATION OF THIRD-PARTY DESIGN-REVIEW FINDINGS (design and governance only; nothing executed, no budget created or consumed, no claim created, no runtime namespace occupied, no Path-D artifact modified).**  **THIRD-PARTY DESIGN REVIEW = REQUEST_CHANGES**; **REVIEWED CANDIDATE = `3b085dae4ff89512bcf23f80043b78ddc82a490f`**; **SEVERITY = P0 = 0 / P1 = 1 / P2 = 1 / P3 = 3**; **BLOCKING FINDINGS = P1-1** (the top-level guard and every reporting surface depended on the ungated cmdlet `Write-Output`, so in an environment where that cmdlet's module is unavailable the guard aborted before `exit 4` and the process terminated with an undocumented exit code 1) **and P2-1** (`Write-Output` and `ForEach-Object` were operational cmdlets outside the declared facility model); **BOUNDED FINDINGS = P3-1** (regression completeness claim overstated what had been enumerated), **P3-2** (exit-3 wording could be read as "no output artifact exists"), **P3-3** (runtime occupancy reported as `0 / 6` instead of the derived `0 / 11`); **REMEDIATION STATUS = IMPLEMENTED IN SUCCESSOR CANDIDATE**.  **FIX 1 — NO REPORTING SURFACE DEPENDS ON A CMDLET:** all 20 reporting sites, including the three guard lines, now write through the frozen bootstrap primitive `[System.Console]::Out.WriteLine`, declared in the spec's bootstrap-primitive model as a non-cmdlet .NET member of the runtime layer already required to execute the script; **`Write-Output` command invocations = 0**. **FIX 2 — THE GUARD IS FAIL-CLOSED:** the guard's emergency reporting is wrapped in its own `try`/`catch` and `exit 4` sits deliberately outside that `try`/`catch`, so an exception inside the emergency reporting path cannot prevent the frozen process-control termination; the guard body invokes **no cmdlet** (guard `CommandAst` count = 0) and prints frozen constants only. **FIX 3 — NO ITERATION CMDLET:** all four `ForEach-Object` sites were replaced by the `foreach` language statement, including a new script-local `Get-LowerHex` helper that renders digests without a pipeline; **`ForEach-Object` command invocations = 0**; **`Get-FileHash` command invocations remain 0**. **FIX 4 — TAXONOMY COMPLETENESS IS NOW NORMATIVE:** the spec requires every `CommandAst` in the executable to be classified as a script-local function, a declared bootstrap primitive, a declared gated facility or a declared external executable, and states that an undeclared operational command is a design-review failure; the regression test must prove membership for every enumerated command and fails whenever the enumerated command count exceeds the declared taxonomy entries. **FIX 5 — ARTIFACT-PRESENCE WORDING:** exit 3 and exit 4 are explicitly **not** artifact-absence assertions; only exit 2 asserts that no output artifact was created, because that branch is reached before any output path is touched. **FIX 6 — OCCUPANCY COUNT CORRECTED:** the derived reserved Path-E runtime/control namespace is **11 paths**; **PATH-E RUNTIME OCCUPANCY = 0 / 11**, with `0 / 6` retained only as the six-output-path subset asserted by the publication occupancy precondition.  **REMEDIATED ARTIFACT IDENTITIES:** `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.ps1` = 41 610 bytes / 772 lines / SHA-256 `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb`; `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.md` = 33 881 bytes / 676 lines / SHA-256 `78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b`.  **STATIC VERIFICATION (parser/AST only; the executable was parsed, never executed):** PowerShell parser errors = 0; `CommandAst` nodes = 28, all classified, taxonomy violations = 0; dynamic command name / alias / `Invoke-*` / `Invoke-Expression` = 0; `Write-Output` = 0; `ForEach-Object` = 0; `Get-FileHash` = 0; `Split-Path` / `Set-Location` / `Get-Content` / `Test-Path` = 0 each; ASCII-only source, BOM absent, CR = 0, exactly one terminal LF (`MAXBYTE = 125`); last bootstrap-availability call at line 267 precedes the earliest gated-facility call at line 277; `Get-NetTCPConnection` only inside `Take-Snapshot` (line 411 within lines 403–531); exit surface exactly `0 / 2 / 3 / 4` (lines 772 / 582 / 760 / 112); result classes exactly three. **ISOLATED LANGUAGE-SEMANTICS PROBE (no DevRelay artifact, no DevRelay path):** with a working emergency channel a simulated host failure terminates at `exit 4` and prints the three frozen guard lines; with the emergency channel itself throwing it **still** terminates at `exit 4` and prints nothing; the unguarded predecessor shape (a trap body whose command is unavailable) still terminates at `exit 1`, which is exactly the defect class now removed.  **EFFECTIVITY:** the rejected first candidate `3b085dae…` remains **NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE** and is superseded by this successor; **ORACLE-PATHE = REVISED DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE**; **PATH-E EXECUTION AUTHORIZATION = NOT DESIGNED / NOT ACCEPTED**; **PATH-E AUTHORIZATION USE = NOT AVAILABLE FOR CONSUMPTION**; **PATH-E ETB ATTEMPT = NOT AVAILABLE FOR CONSUMPTION**; **PATH-E ETB EXECUTION = NOT AUTHORIZED**; **AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED**; **PATH-D = EXHAUSTED / CLOSED / IMMUTABLE** with **PATH-D AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE**, **PATH-D ETB ATTEMPT = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE**, **ORACLE-PATHD INVOCATIONS = 1 OF 1 / MAXIMUM REACHED**, **PATH-D ETB SEMANTIC RESULT = NONE**, **PATH-D RETRY AUTHORITY = NONE** and no Path-D artifact modified. **NO EXECUTION:** 0 Oracle-PathE executions, 0 Oracle-PathD executions, 0 ETB executions, 0 listener queries, 0 `Get-NetTCPConnection` runtime invocations, 0 endpoint probes, 0 port-4096 probes, 0 OpenCode start/restart, 0 HTTP/provider/model calls, 0 claims, 0 budgets, 0 evidence, 0 manifest, 0 result. **NEXT STAGE = NEW THIRD-PARTY INDEPENDENT REVIEW OF THE REMEDIATED ORACLE-PATHE DESIGN CANDIDATE**; acceptance bookkeeping is **NOT** performed in this round.  No tag, no release and no push occurred.

**ORACLE-PATHE ACCEPTANCE BOOKKEEPING — THIRD-PARTY DESIGN REVIEW APPROVED (bookkeeping only; nothing executed, no budget consumed, no reviewed artifact modified).**  The **third-party independent design review** of candidate `f7cafd83a95225e1ce9565a9336ded8575b65335` issued **`APPROVE V0.3-E PATH-E REMEDIATED ORACLE-PATHE EXECUTION-ORACLE DESIGN CANDIDATE — THIRD-PARTY INDEPENDENT REVIEW`** with **P0 = 0, P1 = 0, P2 = 0, P3 = 3**, and recorded **`THIRD-PARTY INDEPENDENCE = SATISFIED`** (methodological independence: no author claim was inherited, every value was independently re-derived from committed bytes, and falsification was attempted; the review ran as a separate read-only round with no commit, no execution and no listener query).  Reviewed findings are recorded as reviewed facts, not re-derived here: `HISTORICAL_PATHD_GETFILEHASH_DEFECT = NOT REPRODUCED`; `WRITE-OUTPUT COMMAND INVOCATIONS = 0`; `FOREACH-OBJECT COMMAND INVOCATIONS = 0`; `TOP-LEVEL TRAP SAFETY = CLOSED`; `EMERGENCY-GUARD SEMANTICS = CLOSED`; `GET-COMMAND BOOTSTRAP = SAFE`; `INFRASTRUCTURE-GATE COVERAGE = COMPLETE`; `COMPLETE COMMAND TAXONOMY = CLOSED`; `GATED FIRST-USE ORDERING = CLOSED`; `HASH SEMANTICS = PRESERVED`; `EXIT-CODE CONTRACT = CLOSED`; `EXIT-2 SEMANTICS = EXACT`; `EXIT-3 ARTIFACT SEMANTICS = CORRECT`; `POST-PUBLICATION EXIT-4 SEMANTICS = CONSISTENT`; `RESULT CLASS SET = EXACTLY THREE`; `LISTENER QUERY OWNERSHIP = EXCLUSIVE`; `SNAPSHOT QUERY MODEL = CONSISTENT`; `TARGET BINDING = PRESERVED`; `PUBLICATION MODEL = FAIL-CLOSED`; `PATH-E RUNTIME NAMESPACE = 11`; `PATH-E RUNTIME OCCUPANCY = 0 / 11`; `MODEL A = PRESERVED`.  **Accepted design identity (immutable):** `oracle_path_e_commit` = `f7cafd83a95225e1ce9565a9336ded8575b65335`, tree `0101461d95bdbc72d809dcf259b0fae1bf5be7ca`; human identifier `Oracle-PathE`; canonical lineage token `PATH_E`; uppercase oracle token `ORACLE_PATH_E`; spec `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.md` with committed-blob SHA-256 `78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b` (33 881 bytes; 676 lines); executable `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.ps1` with committed-blob SHA-256 `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb` (41 610 bytes; 772 lines; ASCII-only, no BOM, LF only, single terminal LF); output namespace `docs/v0.3/evidence/etb-execution-path-e/`; schema identity `devrelay-etb-v1-path-e`; claim lineage `PATH_E`; provenance field names `oracle_path_e_commit` / `oracle_path_e_spec_sha256` / `oracle_path_e_script_sha256`.  **Lineage and ancestors bound unchanged:** `NEW ETB LINEAGE = PATH E — NEW ETB ATTEMPT`; original oracle `oracle_commit` = `1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc`, `oracle_sha256` = `01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921`; exhausted predecessor `PATH-D = EXHAUSTED / CLOSED / IMMUTABLE` with `PATH-D AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`, `PATH-D ETB ATTEMPT = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`, `ORACLE-PATHD INVOCATIONS = 1 OF 1 / MAXIMUM REACHED`, `PATH-D ETB SEMANTIC RESULT = NONE`, `PATH-D RETRY AUTHORITY = NONE`.  **Owner decision preserved:** `OPEN A NEW ETB LINEAGE`, realized as `PATH E — NEW ETB ATTEMPT` with oracle `Oracle-PathE`; it authorizes the Oracle design lineage only and does **not** itself authorize ETB execution.  **Reviewed remediation scope (recorded, not re-adjudicated):** the accepted candidate is the remediation of the rejected candidate `3b085dae4ff89512bcf23f80043b78ddc82a490f`, whose findings P1-1 (top-level guard not fail-closed), P2-1 (two undeclared operational cmdlets), P3-1 (enumeration-completeness property), P3-2 (exit-3 artifact semantics) and P3-3 (namespace total not derived) the review independently reproduced against the rejected blob and confirmed **CLOSED** in this candidate; no reviewed artifact byte changed after that review.  **P3 disposition (recorded, deliberately NOT fixed):** `P3 = 3`, all **BOUNDED / NON-BLOCKING / NO DESIGN SEMANTIC IMPACT** — O-1 the publication-region SHA-256 object is not disposed (inherited unchanged from the rejected candidate; the frozen self-identity function does dispose in `finally`); O-2 spec §6 tables `ConvertFrom-Json` twice while the executable contains three sites (the ordering invariant holds for every site); O-3 spec §17 retains the base label `DESIGN CANDIDATE` while the header and §21 describe the revision as remediated (effectivity is identical and unambiguous).  **Neither the Oracle-PathE spec nor the Oracle-PathE executable was edited in this round** — doing so would change the independently reviewed candidate bytes; any future clarification of these observations must be separately governed.  **Accepted-effectivity model (bookkeeping and confirmation are NOT collapsed):** this commit is **acceptance bookkeeping provenance only**; immediately after it, `ORACLE-PATHE DESIGN REVIEW = APPROVED`, `ORACLE-PATHE ACCEPTANCE BOOKKEEPING = COMMITTED / PENDING INDEPENDENT CONFIRMATION`, and `ORACLE-PATHE = CONDITIONALLY ACCEPTED / NOT YET FROZEN / NOT YET EFFECTIVE`. Oracle-PathE becomes **`ACCEPTED / FROZEN`** only **after independent confirmation of THIS bookkeeping commit**; `oracle_path_e_commit` remains the independently reviewed **design** commit and is never substituted by this bookkeeping HEAD.  **Gates remain closed until that confirmation:** `PATH-E EXECUTION AUTHORIZATION = NOT DESIGNED / NOT ACCEPTED`; `PATH-E AUTHORIZATION DESIGN = REMAINS TO BE DESIGNED AFTER ORACLE-PATHE ACCEPTANCE CONFIRMATION`; `PATH-E AUTHORIZATION USE = NOT AVAILABLE FOR CONSUMPTION`; `PATH-E ETB ATTEMPT = NOT AVAILABLE FOR CONSUMPTION`; `PATH-E ETB EXECUTION = NOT AUTHORIZED`; `PATH-E RUNTIME OCCUPANCY = 0 / 11`; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`; `LISTENER QUERY = NOT EXECUTED`; claims `NOT CREATED`; budget `NOT CONSUMED`.  **MODEL A preserved:** all historical untracked operational artifacts (12 historical operational files, 5 accepted D1 operational files and 2 Path-D FINAL claim files; 15 porcelain entries / 19 untracked files) remain untracked and byte-unchanged, and this commit modifies **only** the two established active status surfaces (`CHANGELOG.md` and `docs/v0.3/V03E_ACCEPTANCE.md`).  This bookkeeping round performed **0** oracle executions, **0** ETB executions, **0** listener queries, **0** `Get-NetTCPConnection` calls, **0** claim creations, **0** evidence/manifest/result creations, **0** budget consumptions, **0** config mutations, **0** HTTP, **0** provider/model calls, **0** reviewed-artifact mutations and **0** runtime/test/dependency/version changes.  The exact next stage is **third-party independent Oracle-PathE design acceptance-bookkeeping confirmation** (review-only, no commit), which must verify this bookkeeping commit against the approved candidate and the third-party review authority.  No tag, no release and no push occurred.

**ORACLE-PATHE / PATH-E — THIRD-PARTY REVIEW INDEPENDENCE: OWNER GOVERNANCE DETERMINATION (governance recording only; nothing executed, nothing accepted, frozen or activated, no reviewed artifact modified).**  The human owner resolved the governance ambiguity reported by the withheld Oracle-PathE acceptance-bookkeeping confirmation round: **OWNER DETERMINATION = THIRD-PARTY INDEPENDENCE REQUIRES DIFFERENT AGENT/SESSION** — the token `THIRD-PARTY INDEPENDENT REVIEW`, and for future stages the terms `third-party review`, `third-party independent review`, `fresh independent reviewer` and `independent confirmation`, are satisfied only by **ORGANIZATIONAL / AGENT-SESSION SEPARATION**.  A qualifying third-party reviewer **MUST NOT** be the agent/session that (a) authored the candidate under review, (b) performed remediation of that candidate, (c) created the acceptance/bookkeeping mutation being confirmed, or (d) already reviewed that exact candidate or bookkeeping object when the stage requires a fresh independent reviewer.  **METHODOLOGICAL SAME-SESSION REVIEW = VALID AS ADVERSARIAL SELF-REVIEW / NOT SUFFICIENT FOR THIRD-PARTY INDEPENDENCE**: a later same-session round that re-derives all evidence, discards inherited conclusions, uses adversarial falsification and performs read-only review is technically valid and valuable, but it does **not** satisfy the token `THIRD-PARTY INDEPENDENCE = SATISFIED`.  **Basis (Owner):** the repository's only explicit gloss of that token, in the Oracle-PathD acceptance history (`806ade0c`), states in substance that the reviewer is not the agent/session that constructed the candidate and produced no prior review of it; the current Path-E lifecycle explicitly calls for a third-party independent review rather than self-review or re-review; and the ambiguity arose precisely because methodological independence was used inside the same harness session.  This determination **does not dispute the technical quality** of the same-session review already performed — it determines only that that review cannot carry the governance token, and it makes **no false retroactive claim**: the prior review was technically adversarial and independently re-derived, it accurately disclosed its same-session provenance, and governance had not yet resolved whether that provenance met the token; the Owner now resolves the ambiguity prospectively.  **SCOPE = CURRENT UNRESOLVED PATH-E LIFECYCLE + FUTURE THIRD-PARTY REVIEW STAGES**, unless a later explicit Owner governance decision changes the rule.  **RETROACTIVE REOPENING OF CLOSED/FROZEN HISTORICAL LINEAGES = NO** — D1, Recovery-R1, Recovery-R2, Path-D and every other already accepted or frozen lineage remain closed and are **not** reopened merely because repository objects do not carry reviewer/session identity metadata.  **CURRENT PATH-E DESIGN CANDIDATE = `f7cafd83a95225e1ce9565a9336ded8575b65335` / UNCHANGED / REVIEW REQUIRED** — spec `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.md` SHA-256 `78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b` and executable `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.ps1` SHA-256 `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb` are preserved byte-unchanged; the candidate requires a **new qualifying third-party review**, not another author remediation, and no spec, script, `.gitattributes` or candidate-commit modification occurs in this round.  **CURRENT BOOKKEEPING COMMIT = `a5e592bd9265fe4f20a97ed10d7ed39b4531be98` / HISTORICAL / NOT CONFIRMED / NOT EFFECTIVE FOR ACCEPTANCE** — it is not deleted, reset, rewritten, amended or hidden, but its embedded statement `THIRD-PARTY INDEPENDENCE = SATISFIED (methodological independence)` is **not** promoted to frozen acceptance truth and the commit is **not** confirmed in its current authority chain.  **REVIEWER ROLE-SEPARATION RECORDING RULE (future third-party reviews):** any future review requiring third-party independence must explicitly declare, **before any technical conclusion**, `THIRD-PARTY REVIEWER SESSION SEPARATION = SATISFIED`, `REVIEWER WAS NOT THE CANDIDATE-AUTHOR SESSION = YES`, `REVIEWER WAS NOT THE BOOKKEEPING-AUTHOR SESSION = YES` (when applicable) and `REVIEWER DID NOT PREVIOUSLY REVIEW THIS EXACT OBJECT = YES` (when a fresh reviewer is required); no personal identity, machine identity, account identity or raw internal harness session identifier is required, recorded or persisted — only governance-role/session separation is required.  **Consequence for the acceptance chain:** a future qualifying approval of `f7cafd83…` does **not** automatically confirm `a5e592bd…`, because that commit binds the earlier methodological review authority; the narrow corrective/superseding Oracle-PathE acceptance-bookkeeping action needed to bind the new qualifying review must be recovered from precedent and separately authorized, followed by its independent confirmation, and only then may Oracle-PathE become `ACCEPTED / FROZEN / EFFECTIVE` and the Path-E execution-authorization design begin.  **Live state after this recording (unchanged by it):** `ORACLE-PATHE = NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE`; `PATH-E EXECUTION AUTHORIZATION = NOT DESIGNED / NOT ACCEPTED`; `PATH-E AUTHORIZATION USE = NOT AVAILABLE FOR CONSUMPTION`; `PATH-E ETB ATTEMPT = NOT AVAILABLE FOR CONSUMPTION`; `PATH-E ETB EXECUTION = NOT AUTHORIZED`; `PATH-E RUNTIME OCCUPANCY = 0 / 11`; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`; `PATH-D = EXHAUSTED / CLOSED / IMMUTABLE`.  This governance record creates **no new artifact**, modifies **no frozen artifact**, grants **no** execution authority or budget, freezes and activates **nothing**, and claims no accepted status for itself.  **NEXT STAGE = FRESH THIRD-PARTY INDEPENDENT REVIEW OF `f7cafd83a95225e1ce9565a9336ded8575b65335` IN A DIFFERENT AGENT/SESSION.**  0 Oracle executions, 0 ETB executions, 0 listener queries, 0 `Get-NetTCPConnection` calls, 0 endpoint probes, 0 claims, 0 budgets, 0 evidence/manifest/result creations, 0 execution-authorization design, 0 config mutations, 0 HTTP/provider/model calls, 0 reviewed-artifact mutations, 0 historical-lineage reopenings, 0 runtime/test/dependency/version changes.  No tag, no release and no push occurred.

**ORACLE-PATHE DESIGN ACCEPTANCE AUTHORITY — CORRECTIVE / SUPERSEDING ACCEPTANCE BOOKKEEPING BOUND TO THE QUALIFYING THIRD-PARTY INDEPENDENT REVIEW (governance bookkeeping only; nothing executed, no budget created or consumed, no claim created, no runtime namespace occupied, no reviewed artifact modified).**  This round performs **exactly one** narrow corrective governance act: it binds the **new qualifying third-party independent review** of `f7cafd83a95225e1ce9565a9336ded8575b65335` and supersedes, **for review-authority purposes only**, the historical acceptance-bookkeeping record `a5e592bd9265fe4f20a97ed10d7ed39b4531be98` — **without rewriting, amending, deleting, hiding, resetting or confirming that commit**, which remains permanently immutable in history.  **Recovered corrective-bookkeeping precedent (determinative at shape level; no new structure invented, no third path created):** the DevRelay corrective-successor pattern is `docs(v03e): <verb> <object>` realized as **exactly one single-parent successor commit** whose sole tracked delta is **exactly** `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md` (**no third tracked path**) — the accepted bookkeeping-structure contract already frozen by the accepted Recovery-R2 authorization (`PRE-1`, §11.4 / §11.7), with the same two-file shape recurring at `9b17912`, `93e44fe`, `0bd9720`, `806ade0`, `a7e3ccc`, `c1d7bd3`, `81d1feb`, `75313c9`, `1dd35b4`, `b35777e`, `a5e592bd` and `eb54fde`; the closest **shape** analogue for a corrective successor over an established governance record is `81d1feb` (`docs(v03e): reconcile Path-D closure listener probe`; `2 0` CHANGELOG / `1 1` ACCEPTANCE, two files only, reviewed artifacts untouched); the `correct` family already shows prior instances (`02bef76`, `dfb78f3`, `764927b`) and the `clarify` family three; **no prior subject uses `supersede` as its verb**, so the mechanically strongest **precedent-supported** form is used — **`docs(v03e): correct Oracle-PathE design acceptance authority`** — and **no dedicated corrective artifact is required** (the two status surfaces are sufficient, exactly as in `81d1feb`; `02bef76` modified a third path only because it corrected an authorization *candidate*, which this round explicitly must not do).  **Nothing is rewritten:** the superseded record's bytes are untouched and the supersession is declared **only inside this successor record**; the historical entry is named by its full commit id and by its recorded subject `docs(v03e): accept Oracle-PathE design`.  **QUALIFYING THIRD-PARTY REVIEW AUTHORITY BOUND = `APPROVE V0.3-E PATH-E ORACLE-PATHE REMEDIATED DESIGN CANDIDATE — QUALIFYING THIRD-PARTY INDEPENDENT REVIEW`**, with **P0 = 0, P1 = 0, P2 = 0, P3 = 4** (approval bar satisfied: P0 = 0, P1 = 0, P2 = 0), and with the four mandatory independence declarations recorded **before any technical conclusion**: `THIRD-PARTY REVIEWER SESSION SEPARATION = SATISFIED`; `REVIEWER WAS NOT THE CANDIDATE-AUTHOR SESSION = YES`; `REVIEWER WAS NOT THE BOOKKEEPING-AUTHOR SESSION = YES`; `REVIEWER DID NOT PREVIOUSLY REVIEW THIS EXACT OBJECT = YES`.  **OWNER INDEPENDENCE CRITERION (preserved, not weakened or reinterpreted):** `OWNER DETERMINATION = THIRD-PARTY INDEPENDENCE REQUIRES DIFFERENT AGENT/SESSION`; `METHODOLOGICAL SAME-SESSION REVIEW = ADVERSARIAL SELF-REVIEW / NOT SUFFICIENT FOR THIRD-PARTY INDEPENDENCE`; `SCOPE = CURRENT UNRESOLVED PATH-E LIFECYCLE + FUTURE THIRD-PARTY REVIEW STAGES`; `RETROACTIVE REOPENING OF CLOSED/FROZEN HISTORICAL LINEAGES = NO`.  **Reviewed findings are recorded here as reviewed authority, not re-derived in this round:** `HISTORICAL PATH-D GETFILEHASH DEFECT = NOT REPRODUCED`; `WRITE-OUTPUT COMMAND INVOCATIONS = 0`; `FOREACH-OBJECT COMMAND INVOCATIONS = 0`; `TOP-LEVEL TRAP SAFETY = CLOSED`; `EMERGENCY-GUARD SEMANTICS = CLOSED`; `INFRASTRUCTURE-GATE COVERAGE = COMPLETE`; `COMPLETE COMMAND TAXONOMY = CLOSED`; `GET-COMMAND BOOTSTRAP = SAFE`; `GATED FIRST-USE ORDERING = CLOSED`; `EXIT-CODE CONTRACT = CLOSED`; `EXIT-2 SEMANTICS = EXACT`; `EXIT-3 ARTIFACT SEMANTICS = CORRECT`; `POST-PUBLICATION EXIT-4 SEMANTICS = CONSISTENT`; `RESULT CLASS SET = EXACTLY THREE`; `LISTENER QUERY OWNERSHIP = EXCLUSIVE`; `SNAPSHOT QUERY MODEL = CONSISTENT`; `TARGET BINDING SEMANTICS = PRESERVED`; `HASH SEMANTICS = PRESERVED`; `GET-LOWERHEX = EQUIVALENT`; `PUBLICATION MODEL = FAIL-CLOSED`; `FAILURE-HANDLER PRECEDENCE = CORRECT`; `PATH-E RUNTIME OCCUPANCY = 0 / 11`; `MODEL A = PRESERVED`; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`.  **ACCEPTED DESIGN CANDIDATE = `f7cafd83a95225e1ce9565a9336ded8575b65335`** (parent `3b085dae4ff89512bcf23f80043b78ddc82a490f`, tree `0101461d95bdbc72d809dcf259b0fae1bf5be7ca`, subject `fix(v03e): remediate Oracle-PathE design review findings`); spec `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.md` SHA-256 `78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b` (**33 881** bytes, 676 lines); executable `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.ps1` SHA-256 `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb` (**41 610** bytes, 772 lines); both are byte-identical at the reviewed candidate commit, at this commit's parent and in the worktree, and **neither artifact is modified by this round**.  **A5E592BD DISPOSITION (explicit, current, prospective only):** `A5E592BD BOOKKEEPING = HISTORICAL / NOT CONFIRMED / NOT EFFECTIVE FOR ACCEPTANCE / SUPERSEDED FOR REVIEW-AUTHORITY PURPOSES`, because it bound the earlier **same-session methodological review**, which the Owner determination holds does not satisfy the third-party criterion; the commit is **not** deleted, reset, rewritten, amended, hidden or confirmed, and **no false retroactive claim** is made about it.  **FOUR NONBLOCKING P3 FINDINGS CARRIED ACCURATELY (documentation-only; not repaired in this round, by explicit instruction):** `P3-1 / O-1` — the publication-region `System.Security.Cryptography.SHA256` object created in the publication region (executable line 648) is not disposed, although the helper's own instance is disposed; disposition `REPRODUCED / NONBLOCKING / NO FAIL-CLOSED IMPACT / NOT REPAIRED`; `P3-2 / O-2` — spec §6 lists `ConvertFrom-Json` **twice** while the executable has **three** actual sites; disposition `DOCUMENTATION PRECISION / FIRST-USE ORDERING HOLDS FOR ALL SITES / NONBLOCKING / NOT REPAIRED`; `P3-3 / O-3` — spec §17 retains the base `DESIGN CANDIDATE` terminology; disposition `TERMINOLOGY ONLY / EFFECTIVITY UNAMBIGUOUS / NONBLOCKING / NOT REPAIRED`; `P3-4` — spec §4.2's narrative enumeration double-counts `python` (counted inside the six gated facilities **and** again as the one external executable) and omits the single `Get-Command` bootstrap invocation (declared separately by the spec as the checker's own mechanism), although the actual technical state is `CommandAst total = 28`, `distinct command names = 13`, `undeclared operational commands = 0`, so the taxonomy invariant's substance holds; disposition `DOCUMENTATION / TAXONOMY ENUMERATION PRECISION / NONBLOCKING / NO EXECUTABLE SEMANTIC IMPACT / NOT REPAIRED`.  **TWO-STAGE EFFECTIVITY (explicit):** `QUALIFYING THIRD-PARTY DESIGN REVIEW = APPROVED`; `CORRECTIVE / SUPERSEDING ACCEPTANCE BOOKKEEPING = COMMITTED / PENDING INDEPENDENT CONFIRMATION`; `ORACLE-PATHE = CONDITIONALLY ACCEPTED / NOT YET FROZEN / NOT YET EFFECTIVE` — this round deliberately does **not** state `ORACLE-PATHE = ACCEPTED / FROZEN / EFFECTIVE`, grants **no** execution authority, and creates **no** budget, claim, evidence, manifest, result or runtime namespace entry.  **Live state after this round (unchanged except the conditional statuses above):** `PATH-E EXECUTION AUTHORIZATION = NOT DESIGNED / NOT ACCEPTED`; `PATH-E AUTHORIZATION USE = NOT AVAILABLE FOR CONSUMPTION`; `PATH-E ETB ATTEMPT = NOT AVAILABLE FOR CONSUMPTION`; `PATH-E ETB EXECUTION = NOT AUTHORIZED`; `PATH-E RUNTIME OCCUPANCY = 0 / 11`; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`; `PATH-D = EXHAUSTED / CLOSED / IMMUTABLE`; `PATH-D AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `PATH-D ETB ATTEMPT = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `ORACLE-PATHD INVOCATIONS = 1 OF 1 / MAXIMUM REACHED`; `PATH-D ETB SEMANTIC RESULT = NONE`; `PATH-D RETRY AUTHORITY = NONE`; all five frozen Path-D hashes (`49e7c29a…`, `15e39452…`, `8bdeb434…`, `5e33a8f3…`, `64f86fcc…`) were verified unchanged before and after this round.  **NO SELF-REFERENCE:** this record embeds **neither** its own commit id **nor** its own tree; the bookkeeping commit is identified mechanically by its **parent** (`eb54fde563524f51d4e729655639a7c0386cb43a`), its **subject** and its **delta**, and the authority it binds is the reviewed candidate and the qualifying review, not itself.  **CONFIRMATION REQUIREMENT (next stage; NOT performed in this round):** the new bookkeeping is **not effective merely because it is committed**; its next stage is `FRESH THIRD-PARTY INDEPENDENT CONFIRMATION OF THE CORRECTIVE / SUPERSEDING ORACLE-PATHE DESIGN ACCEPTANCE BOOKKEEPING`, performed in a **different agent/session** that must declare `THIRD-PARTY REVIEWER SESSION SEPARATION = SATISFIED`, `REVIEWER WAS NOT THE CORRECTIVE-BOOKKEEPING-AUTHOR SESSION = YES` and `REVIEWER DID NOT PREVIOUSLY CONFIRM THIS EXACT BOOKKEEPING OBJECT = YES`; recovered precedent requires **no additional separation stage beyond the Owner role-separation rule (a)–(d)** — separation from the candidate author, from any remediation author, from the author of the mutation being confirmed, and from any prior reviewer of the exact object under confirmation — and because the qualifying design review and this corrective bookkeeping were both authored in the **same** agent session, that session is disqualified from confirming its own bookkeeping under rules (c) and (d), so the confirmer must be a fresh session in every case; `CURRENT BOOKKEEPING COMMIT` is bound to `a5e592bd9265fe4f20a97ed10d7ed39b4531be98` only as **historical**, and **no automatic confirmation follows**.  This governance record creates **no new artifact**, modifies **no frozen artifact**, grants **no** execution authority or budget, freezes and activates **nothing** in effect (Oracle-PathE is **conditionally** accepted only and remains **NOT YET FROZEN / NOT YET EFFECTIVE**), and claims **no accepted status for itself**.  `NEXT STAGE = OWNER AUTHORIZATION FOR THE FRESH THIRD-PARTY INDEPENDENT CONFIRMATION OF THIS CORRECTIVE / SUPERSEDING ORACLE-PATHE DESIGN ACCEPTANCE BOOKKEEPING` (the confirmation itself is **not** performed in this round).  0 Oracle executions, 0 ETB executions, 0 listener queries, 0 `Get-NetTCPConnection` calls, 0 endpoint probes, 0 claims, 0 budgets, 0 evidence/manifest/result creations, 0 execution-authorization design, 0 config mutations, 0 HTTP/provider/model calls, 0 reviewed-artifact mutations, 0 historical-lineage reopenings, 0 runtime/test/dependency/version changes.  No tag, no release and no push occurred.
**ORACLE-PATHE DESIGN ACCEPTANCE BOOKKEEPING — FRESH THIRD-PARTY INDEPENDENT CONFIRMATION: CONFIRMATION-RECORD CLOSURE (governance record only; nothing executed, no claim created, no budget created or consumed, no reviewed artifact modified).**  This is a **GOVERNANCE-ONLY record-closure round**: it does **not** retry the ETB, does **not** re-run or re-authorize Oracle-PathE or Oracle-PathD, does **not** perform a second design acceptance or a second acceptance bookkeeping, does **not** produce a new oracle design, does **not** design or grant any execution authorization, does **not** consume any claim, and performs **no** operational action.  **Recovered precedent (structure determined by existing precedent, not invented):** the DevRelay bookkeeping-structure contract frozen by the accepted Recovery-R2 authorization (`PRE-1`, §11.4, §11.7) requires a governed state transition to become a repository-verifiable fact through **exactly ONE single-parent child commit whose sole tracked delta against its parent is `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md` and NO third tracked path**; the directly governing precedent is `c1d7bd3` (**`docs(v03e): record Path-D authorization confirmation`**), which materialized the completed Path-D third-party confirmation as exactly such a record commit, and the two-file bookkeeping-shape precedent is `9b17912…`.  **That precedent determines this round's shape; no new structure was invented and no confirmation artifact was created.**  The **fresh third-party independent confirmation** of the corrective / superseding Oracle-PathE design acceptance bookkeeping — completed in the immediately preceding round as a **review-only event with no commit** — is hereby **materialized as a repository-verifiable fact**: `CONFIRMATION VERDICT = APPROVE V0.3-E PATH-E CORRECTIVE / SUPERSEDING ORACLE-PATHE DESIGN ACCEPTANCE-BOOKKEEPING CONFIRMATION`; `CONFIRMED BOOKKEEPING COMMIT = 302dd74aa9f22640eaacb34bfbbc96de93dbaa9b`; `CONFIRMED CORRECTIVE BOOKKEEPING = CORRECTIVE / SUPERSEDING ACCEPTANCE BOOKKEEPING BOUND TO THE QUALIFYING THIRD-PARTY INDEPENDENT REVIEW`; `CONFIRMED BOOKKEEPING TREE = fe2963fea5d2e8e9c20db52902c71bee3a883fa3`; `CONFIRMED QUALIFYING DESIGN REVIEW = APPROVE V0.3-E PATH-E ORACLE-PATHE REMEDIATED DESIGN CANDIDATE — QUALIFYING THIRD-PARTY INDEPENDENT REVIEW`; `CONFIRMED ACCEPTED DESIGN IDENTITY = f7cafd83a95225e1ce9565a9336ded8575b65335`; `THIRD-PARTY REVIEWER SESSION SEPARATION = SATISFIED`; `REVIEWER WAS NOT THE CANDIDATE-AUTHOR / REMEDIATION SESSION = YES`; `REVIEWER WAS NOT THE CORRECTIVE-BOOKKEEPING-AUTHOR SESSION = YES`; `REVIEWER DID NOT PREVIOUSLY CONFIRM THIS EXACT BOOKKEEPING OBJECT = YES`; `CONFIRMATION RESULT = P0 = 0, P1 = 0, P2 = 0, P3 = 1` (the single non-blocking P3 is a **status-surface review-token rendering variance** — one surface carries the complete review title with the lineage token, the other its equivalent short form; both bind the same independently reviewed design commit `f7cafd83…`; no correction was required and none was performed).  **Repository-verifiable effectivity contract (frozen by this record; derivable only from Git commit topology plus tracked status-surface bytes plus frozen artifact identity — never from chat history, conversation transcripts or agent memory):** (1) accepted corrective / superseding acceptance bookkeeping commit `= 302dd74aa9f22640eaacb34bfbbc96de93dbaa9b`; (2) accepted design commit `oracle_path_e_commit = f7cafd83a95225e1ce9565a9336ded8575b65335`; (3) accepted Oracle-PathE specification `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.md` with committed-blob SHA-256 `78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b` (33 881 bytes, 676 lines); (4) accepted Oracle-PathE executable `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.ps1` with committed-blob SHA-256 `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb` (41 610 bytes, 772 lines); (5) that bookkeeping commit's third-party independent confirmation `= APPROVED`, `THIRD-PARTY REVIEWER SESSION SEPARATION = SATISFIED`; (6) `QUALIFYING THIRD-PARTY DESIGN REVIEW = APPROVED / FROZEN`; (7) `CORRECTIVE / SUPERSEDING ORACLE-PATHE DESIGN ACCEPTANCE BOOKKEEPING = CONFIRMED / FROZEN`; (8) `ORACLE-PATHE = ACCEPTED / FROZEN / EFFECTIVE`.  **Mechanical recognition rule for a future executor (topology plus content, requiring no external testimony):** the confirmation-record commit is the **single-parent** commit whose parent is exactly `302dd74aa9f22640eaacb34bfbbc96de93dbaa9b`, whose sole tracked delta against that parent is **exactly** `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md` (**no third tracked path**), and whose active status surfaces state `ORACLE-PATHE = ACCEPTED / FROZEN / EFFECTIVE` bound to accepted design commit `f7cafd83a95225e1ce9565a9336ded8575b65335`, specification SHA-256 `78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b` and executable SHA-256 `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb`; all of those conditions hold simultaneously and are checked mechanically.  **No self-reference:** this record deliberately does **not** embed its own commit SHA — it is identified only by its parent, its subject, its changed-path set and the frozen provenance stated here; the subject is `docs(v03e): record Oracle-PathE design acceptance bookkeeping confirmation`, which is **not** an acceptance subject and does **not** imply a second acceptance-bookkeeping event.  **Anti-recursion (no new effectivity dependency is created):** this confirmation record becomes the repository-verifiable **effectivity fact**; any follow-up read-only verification of this closure is a **verification of an existing record, not a new acceptance or effectivity event** — it spawns **no** further record commit, **no** recursive lifecycle and **no** additional dependency chain.  **Recorded root cause of why this record was required (not repaired by rewriting confirmed bytes):** the corrective bookkeeping at `302dd74…` froze a **conditional** effectivity (`ORACLE-PATHE = CONDITIONALLY ACCEPTED / NOT YET FROZEN / NOT YET EFFECTIVE`, becoming accepted only after the independent confirmation) and — like the Path-D authorization artifact before it — froze **no explicit recording carrier** for the confirmation event itself; because confirmation was correctly designed as a review-only event, it produced **no repository object**, so the satisfied condition was not repository-verifiable.  This round supplies exactly that missing repository object and **nothing more**.  **Historical immutability preserved:** `a5e592bd9265fe4f20a97ed10d7ed39b4531be98` remains **HISTORICAL / NOT CONFIRMED / NOT EFFECTIVE FOR ACCEPTANCE / SUPERSEDED FOR REVIEW-AUTHORITY PURPOSES** — it still exists, was **not** amended, was **not** reset away, its chronology remains visible, and only its current review-authority status remains prospectively superseded; the corrective bookkeeping commit `302dd74…`, the independently reviewed design commit `f7cafd83…`, both accepted Oracle-PathE artifacts, the Oracle-PathD spec and executable, Oracle-R2, Recovery-R1, Recovery-R2, D1, the original oracle artifacts, `.gitattributes`, all Path-D artifacts and all claims, evidence, manifests, results, configuration and construction-time banners are **byte-unchanged**; the four recorded non-blocking Oracle-PathE design-review observations (`P3-1 / O-1` publication-region SHA-256 object not disposed; `P3-2 / O-2` spec §6 `ConvertFrom-Json` listed twice against three executable sites; `P3-3 / O-3` spec §17 base `DESIGN CANDIDATE` terminology retained; `P3-4` spec §4.2 narrative enumeration precision) remain **NONBLOCKING / NOT REPAIRED / NO EXECUTABLE SEMANTIC IMPACT**, and none was "fixed" by rewriting a reviewed or confirmed byte.  **Gates remain closed and unchanged by this record:** `PATH-E EXECUTION AUTHORIZATION = NOT DESIGNED / NOT ACCEPTED`; `PATH-E AUTHORIZATION DESIGN = NEXT STAGE / NOT PERFORMED IN THIS ROUND`; `PATH-E AUTHORIZATION USE = NOT AVAILABLE FOR CONSUMPTION`; `PATH-E ETB ATTEMPT = NOT AVAILABLE FOR CONSUMPTION`; `PATH-E ETB EXECUTION = NOT AUTHORIZED`; `PATH-E RUNTIME OCCUPANCY = 0 / 11` (all eleven reserved Path-E runtime/control paths absent); `JUST-IN-TIME BUDGETS = NOT AVAILABLE / NOT YET GRANTED` (`PATH_E_AUTHORIZATION_USE_BUDGET = 1 OF 1` and `PATH_E_ETB_ATTEMPT_BUDGET = 1 OF 1` become consumable only after a future separately accepted authorization); `ORACLE-PATHE EXECUTION = NOT AUTHORIZED`; `ORACLE-PATHD EXECUTION = NOT AUTHORIZED`; `LISTENER QUERY = NOT EXECUTED`.  **Result authority preserved:** `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`; a confirmation record creates **no** ETB observation, **no** semantic result and **no** replacement authority, and any future Oracle-PathE observation must still pass **independent result review → result bookkeeping → independent bookkeeping confirmation** before becoming authoritative.  **Path-D preserved:** `PATH-D = EXHAUSTED / CLOSED / IMMUTABLE`; `PATH-D AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `PATH-D ETB ATTEMPT = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `ORACLE-PATHD INVOCATIONS = 1 OF 1 / MAXIMUM REACHED`; `PATH-D ETB SEMANTIC RESULT = NONE`; `PATH-D RETRY AUTHORITY = NONE`; all five frozen Path-D hashes (`49e7c29a…`, `15e39452…`, `8bdeb434…`, `5e33a8f3…`, `64f86fcc…`) verified unchanged.  **MODEL A preserved:** no runtime or generated artifact became tracked; the untracked operational inventory remains `15` collapsed `git status --porcelain` entries / `19` expanded untracked files, composition `12 historical operational files + 5 accepted D1 operational files + 2 Path-D FINAL claim files`, and this commit modifies **only** the two established active status surfaces (`CHANGELOG.md` and `docs/v0.3/V03E_ACCEPTANCE.md`).  This governance record round performed **0** Oracle executions, **0** ETB executions, **0** listener queries, **0** `Get-NetTCPConnection` calls, **0** endpoint probes, **0** port-4096 probes, **0** OpenCode starts/restarts, **0** HTTP/provider/model calls, **0** claims, **0** budgets, **0** evidence/manifest/result creations, **0** execution-authorization design, **0** config mutations, **0** reviewed-artifact mutations, **0** historical-lineage reopenings and **0** runtime/test/dependency/version changes.  **Exact next stage:** **PATH-E ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE** (design and governance only; it will create no claim, grant no budget, mutate no frozen artifact and authorize no execution).  No tag, no release and no push occurred.
**PATH-E / ORACLE-PATHE 鈥?ONE-SHOT ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE (design and governance only; nothing executed, no budget created or consumed, no claim created, no runtime namespace occupied, no Path-E runtime artifact created, no accepted artifact modified, Path-D not reopened).**  This round designs the **one-shot ETB execution-authorization model for the PATH E 鈥?NEW ETB ATTEMPT lineage** and commits it as a **design candidate only**, binding the already accepted Oracle-PathE design without redefining it.  **Recovered precedent (shape determinative; no new structure invented):** the DevRelay authorization-candidate shape is **exactly THREE changed paths 鈥?the new authorization artifact plus `CHANGELOG.md` plus `docs/v0.3/V03E_ACCEPTANCE.md` and no fourth path** (Path-D analogue `29bf27fc2f76d415eb9c07d890f50b665aca6846` = `738 0` new artifact / `2 0` CHANGELOG / `1 1` ACCEPTANCE), whereas accept / reconcile / clarify / record rounds use the two-file `CHANGELOG.md` + acceptance-surface shape.  **That precedent is followed; no third status surface, no runtime file, no evidence, no manifest and no result was invented.**  **Confirmed governance base:** the fresh third-party independent confirmation of the corrective / superseding Oracle-PathE design acceptance bookkeeping was completed as a review-only event and has been materialized as a repository-verifiable record commit `367aca3f61e6387940deb976d0302ebc7d8b07c4` (`docs(v03e): record Oracle-PathE design acceptance bookkeeping confirmation`, sole delta `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md`, 3 insertions / 1 deletion), so `ORACLE-PATHE = ACCEPTED / FROZEN / EFFECTIVE` is now a tracked, mechanically checkable fact and is no longer merely asserted; the authorization design binds **only** that accepted authority.  **Authorized scope of this round:** recover the Path-D authorization precedent, design the Path-E authorization model, create the design-candidate artifact, update the minimum precedent-required status surfaces and create exactly one local candidate commit.  **BOUND ACCEPTED ORACLE-PATHE IDENTITY (frozen; not modified by this round):** `oracle_path_e_commit = f7cafd83a95225e1ce9565a9336ded8575b65335` (parent `3b085dae4ff89512bcf23f80043b78ddc82a490f`, tree `0101461d95bdbc72d809dcf259b0fae1bf5be7ca`, subject `fix(v03e): remediate Oracle-PathE design review findings`); spec `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.md` SHA-256 `78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b` (33 881 bytes, 676 lines); executable `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.ps1` SHA-256 `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb` (41 610 bytes, 772 lines); design acceptance bookkeeping `302dd74aa9f22640eaacb34bfbbc96de93dbaa9b` (tree `fe2963fea5d2e8e9c20db52902c71bee3a883fa3`).  **NEW AUTHORIZATION ARTIFACT:** `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_E_AUTHORIZATION.md`, 29 sections, ASCII with LF-only line endings, no BOM, exactly one terminal LF; `path_e_authorization_commit` and `path_e_authorization_sha256` are deliberately left as explicit placeholders there and are populated **only** by the later independent acceptance record 鈥?an executor may never compute, infer or choose them at runtime.  **AUTHORIZATION MODEL FROZEN BY THE ARTIFACT:** the authorization layer verifies static artifact identity and governance preconditions only and is **forbidden** to perform target binding, listener query, process/handle inspection, S0/S1 snapshots or any result classification, all of which belong **exclusively** to the accepted Oracle-PathE executable (auth 搂13.3); an explicit **no target pre-probe** prohibition (auth 搂14) bans `Get-NetTCPConnection`, `netstat`, any port-4096 scan, any `localhost` / `127.0.0.1` probe, any endpoint or HTTP reachability check, any OpenCode start/restart, `Test-NetConnection`, `Invoke-WebRequest` / `Invoke-RestMethod` / `curl`, `Get-CimInstance` / `Get-WmiObject` target binding, `Get-Process` discovery, target `Get-FileHash`, target `CreateFileW` / `GetFinalPathNameByHandleW` and target `package.json` reads, because such a probe would create an **unbudgeted ETB observation** (the historical Path-D closure incident is recorded as accepted history and is not re-litigated); `PRE-1` 鈥?`PRE-15` are mandatory, ordered and fail-closed, and a precondition failure consumes **no** budget.  **ONE-SHOT BUDGET MODEL (design only; NOT consumable in this round):** `PATH_E_AUTHORIZATION_USE_BUDGET = 1 of 1`, `PATH_E_ETB_ATTEMPT_BUDGET = 1 of 1`, `ORACLE-PATHE INVOCATIONS = 1 of 1`; the **irreversible consumption point is the successful `CreateNew` of the TEMP claim**, not its publication to FINAL, so a TEMP claim that exists means the budget is spent permanently even if publication fails, the Oracle is never entered or the process is killed; there is **no** reset, no refund, no deletion-to-reuse, no `git reset` / `checkout` / reset-to-reuse path and no retry under the same authorization 鈥?any further attempt requires an entirely new Owner-authorized lineage; ordering is strict (authorization claim 鈫?attempt claim 鈫?Oracle entry), never speculative, never merged and never collapsed.  **CLAIM SCHEMAS AND FROZEN WRITER:** `devrelay-etb-path-e-authorization-use-v1` and `devrelay-etb-path-e-attempt-use-v1`, closed seven-field ordered single-line JSON with `state = CONSUMED`, UTF-8 without BOM and exactly one terminal LF, created only by the verbatim frozen `Write-DevRelayPathEOneShotClaim` primitive reproduced in the artifact (TEMP and FINAL existence checks first, `CreateNew` with `FileShare::None`, `Flush($true)`, byte-identical read-back, terminal-LF and no-BOM assertions, two-argument `[System.IO.File]::Move` no-overwrite publication, final byte verification, and **no** deletion, cleanup, retry or wrapper on any failure path); the four claim paths (`docs/v0.3/evidence/ETB_PATH_E_AUTHORIZATION_USE.claim{,.tmp}` and `docs/v0.3/evidence/ETB_PATH_E_ATTEMPT_USE.claim{,.tmp}`) are all **ABSENT** at design stage and were **not** created.  **RESULT AUTHORITY PRESERVED:** the closed class set remains exactly `ETB_SATISFIED`, `ETB_UNSATISFIED`, `HARNESS_INVALID / NO ETB SEMANTIC RESULT` 鈥?**no fourth ETB class**, no `PASS` / `FAIL` / `PARTIAL` / `UNKNOWN` / `PROBABLE` / `RETRY` result class, and the historical Path-D phrase `UNCLASSIFIED CONTROL FAILURE` is explicitly **not** a class of this lineage; the artifact freezes that a raw observation must still pass **independent result review 鈫?result bookkeeping 鈫?independent bookkeeping confirmation** before it may replace the authoritative result, which therefore remains `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`, and the authorization, its acceptance, its claims, their consumption and the Oracle invocation itself never replace it.  **RUNTIME NAMESPACE:** `docs/v0.3/evidence/etb-execution-path-e/` with `ETB_EVIDENCE.json{,.tmp}` and `MANIFEST.sha256{,.tmp}`, plus `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_E.md{,.tmp}`, plus the two claim TEMP/FINAL pairs 鈥?exactly **11 reserved paths, all ABSENT: `PATH-E RUNTIME OCCUPANCY = 0 / 11`**; no Path-D output path is referenced anywhere and the future evidence schema identity is `devrelay-etb-v1-path-e`.  **PATH-D PRESERVED:** `PATH-D = EXHAUSTED / CLOSED / IMMUTABLE`; `PATH-D AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `PATH-D ETB ATTEMPT = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `ORACLE-PATHD INVOCATIONS = 1 OF 1 / MAXIMUM REACHED`; `PATH-D ETB SEMANTIC RESULT = NONE`; `PATH-D RETRY AUTHORITY = NONE`; all five frozen Path-D hashes (`49e7c29a鈥, `15e39452鈥, `8bdeb434鈥, `5e33a8f3鈥, `64f86fcc鈥) verified unchanged and **not** reused as Path-E budgets or namespace.  **a5e592bd PRESERVED:** `a5e592bd9265fe4f20a97ed10d7ed39b4531be98` remains `HISTORICAL / NOT CONFIRMED / NOT EFFECTIVE FOR ACCEPTANCE / SUPERSEDED FOR REVIEW-AUTHORITY PURPOSES`, not reopened, not re-confirmed, not rewritten.  **MODEL A preserved:** no runtime or generated artifact became tracked; the untracked operational inventory remains `15` collapsed `git status --porcelain` entries / `19` expanded untracked files, composition `12 historical operational files + 5 accepted D1 operational files + 2 Path-D FINAL claim files`, and this round modifies only its own authorization candidate artifact plus the two established active status surfaces.  **Effectivity immediately after this candidate commit:** `PATH-E AUTHORIZATION = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / NOT EXECUTED`; `EXECUTION AUTHORITY = NOT GRANTED BY THIS ROUND`; `PATH-E AUTHORIZATION USE = NOT AVAILABLE FOR CONSUMPTION`; `PATH-E ETB ATTEMPT = NOT AVAILABLE FOR CONSUMPTION`; `PATH-E ETB EXECUTION = NOT AUTHORIZED`; `ORACLE-PATHE = ACCEPTED / FROZEN / EFFECTIVE`; `ORACLE-PATHE EXECUTION = NOT AUTHORIZED`; `PATH-E RUNTIME OCCUPANCY = 0 / 11`; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`.  **Non-collapsed lifecycle frozen by the artifact:** design candidate 鈫?qualifying third-party independent review in a **different agent/session** 鈫?authorization acceptance bookkeeping (exactly one single-parent commit, two-file delta) 鈫?fresh independent confirmation of that acceptance bookkeeping 鈫?materialization of the confirmation as a repository-verifiable record commit 鈫?**only then** `PATH-E AUTHORIZATION = ACCEPTED / FROZEN / EFFECTIVE` with `EXECUTION AUTHORITY = GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY` 鈫?fresh operational execution session; every stage that requires independence must declare `THIRD-PARTY REVIEWER SESSION SEPARATION = SATISFIED`, `REVIEWER WAS NOT THE AUTHORIZATION-CANDIDATE-AUTHOR SESSION = YES` and `REVIEWER DID NOT PREVIOUSLY REVIEW THIS EXACT AUTHORIZATION OBJECT = YES` before any technical conclusion, and no stage may be skipped, merged, collapsed or self-performed.  **Self-review of this candidate: `P0 = 0`, `P1 = 0`, `P2 = 0`** (commit gate satisfied); two documentation-precision observations are carried as nonblocking and **NOT repaired**: `P3-1` the claim-writer block reproduced in auth 搂11 must remain byte-identical to the frozen lineage writer and was not executed in this round, and `P3-2` the `path_e_authorization_commit` / `path_e_authorization_sha256` placeholders must be replaced only by the independent acceptance record, never by an executor.  **This design round performed** 0 Oracle-PathE executions, 0 Oracle-PathD executions, 0 ETB executions, 0 listener queries, 0 `Get-NetTCPConnection` calls, 0 port-4096 probes, 0 `localhost` / `127.0.0.1` probes, 0 endpoint probes, 0 OpenCode starts/restarts, 0 HTTP / provider / model calls, 0 claim creations, 0 budget creations, 0 budget consumptions, 0 evidence / manifest / result creations, 0 Path-E runtime artifact creations, 0 Path-D modifications, 0 accepted-artifact mutations, 0 historical-lineage reopenings and 0 runtime / test / dependency / version changes.  **Exact next stage:** `FRESH QUALIFYING THIRD-PARTY INDEPENDENT REVIEW OF THE PATH-E EXECUTION-AUTHORIZATION DESIGN CANDIDATE` 鈥?no review, no acceptance and no execution is performed in this round.  No tag, no release and no push occurred.
**ORACLE-PATHE / PATH-E — OWNER RATIFICATION OF THE 367ACA3 CONFIRMATION-MATERIALIZATION COMMIT (governance record only; nothing executed, no claim created, no budget created or consumed, no runtime namespace occupied, no accepted or frozen artifact mutated, no history rewritten).** A strictly read-only independent governance reconciliation of the sequence `302dd74aa9f22640eaacb34bfbbc96de93dbaa9b` → `367aca3f61e6387940deb976d0302ebc7d8b07c4` → `26b183083fbbe323441283f99f3cf2c931acd6ff` returned the single verdict **A. RATIFIABLE AS-IS — 367ACA3 CONTENT CORRECT; 26B1830 LINEAGE MAY REMAIN INTACT; OWNER RATIFICATION RECORD REQUIRED BEFORE THIRD-PARTY REVIEW**, with process severity `PROCESS P0 = 0`, `PROCESS P1 = 0`, `PROCESS P2 = 1`, `PROCESS P3 = 1`: the design/build round created the additional confirmation-record commit that the original round text did not explicitly name (P2), so its authorization provenance was not repository-verifiable, and the Owner had prospectively directed that materialization before it was created; the authorization candidate also carries a trailing LF run of 5 rather than exactly one terminal LF (P3). The Owner now records: `OWNER RATIFICATION = 367ACA3 CONFIRMATION-MATERIALIZATION COMMIT RATIFIED AS-IS`; `RATIFIED COMMIT = 367aca3f61e6387940deb976d0302ebc7d8b07c4` (subject `docs(v03e): record Oracle-PathE design acceptance bookkeeping confirmation`, sole parent `302dd74aa9f22640eaacb34bfbbc96de93dbaa9b`, tree `922d0b93d1e14cfc82d48de1d69ca23c1ce5ddb4`, sole delta `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md`, 2 files changed / 4 insertions / 1 deletion, no candidate artifact mutation, no runtime mutation, no self-reference); `ORIGINAL CONFIRMED BOOKKEEPING = 302dd74aa9f22640eaacb34bfbbc96de93dbaa9b`; `AUTHORIZATION CANDIDATE = 26b183083fbbe323441283f99f3cf2c931acd6ff`; `OWNER CONFIRMS = THE MATERIALIZATION WAS DIRECTED BEFORE CREATION`; `REPOSITORY-PROVENANCE GAP = CLOSED BY THIS SUCCESSOR RATIFICATION RECORD`; `367ACA3 CONTENT = CORRECT / NON-SUBSTANTIVE / GOVERNANCE-ONLY`; `367ACA3 CREATED = NO EXECUTION AUTHORITY / NO BUDGET / NO CLAIM / NO RUNTIME STATE / NO ETB RESULT`; `26B1830 LINEAGE = PRESERVED / NO REBUILD / NO REPARENTING / NO AMEND / NO RESET / NO CHERRY-PICK`. Latest resolved governance state: `367ACA3 = OWNER-RATIFIED / VALID GOVERNANCE MATERIALIZATION`; `ORACLE-PATHE = ACCEPTED / FROZEN / EFFECTIVE`, accepted design candidate `f7cafd83a95225e1ce9565a9336ded8575b65335`, spec `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.md` SHA-256 `78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b`, executable `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.ps1` SHA-256 `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb`; `26B1830 = VALID / REVIEW PENDING` with artifact `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_E_AUTHORIZATION.md` SHA-256 `d8b75b7dbfda3075bd984f0f3da8569574a1fe4d3363da99ca395fbae87ac8a4` / 52469 bytes / 769 LF-terminated lines (770 by LF-split count); `PATH-E AUTHORIZATION = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE`; `PATH-E AUTHORIZATION USE = NOT AVAILABLE FOR CONSUMPTION`; `PATH-E ETB ATTEMPT = NOT AVAILABLE FOR CONSUMPTION`; `PATH-E ETB EXECUTION = NOT AUTHORIZED`; `PATH-E EXECUTION = NOT AUTHORIZED`; `PATH-E RUNTIME OCCUPANCY = 0 / 11`; `PATH-D = EXHAUSTED / CLOSED / IMMUTABLE`; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`; `MODEL A = 15 collapsed / 19 expanded` (12 historical operational files + 5 accepted D1 operational files + 2 Path-D FINAL claim files, no Path-E runtime artifact); known nonblocking `AUTHORIZATION-CANDIDATE P3 = trailing LF run of 5 instead of exactly one terminal LF — P3 / NONBLOCKING / BYTE-FORMAT PRECISION / NO SEMANTIC IMPACT / NOT REPAIRED IN THIS RATIFICATION ROUND / CARRIED INTO THE THIRD-PARTY AUTHORIZATION REVIEW`; this ratification grants no execution authority, consumes no budget, creates no claim, no evidence, no manifest, no result and no runtime namespace entry, performs no Oracle or ETB execution, queries no listener, probes no endpoint, and rewrites no history; `NEXT STAGE = FRESH QUALIFYING THIRD-PARTY INDEPENDENT REVIEW OF THE PATH-E EXECUTION-AUTHORIZATION DESIGN CANDIDATE`.  No tag, no release and no push occurred.

**PATH-E ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE - P2 REVIEW-FINDING REMEDIATION (design and governance only; nothing executed, no budget created or consumed, no claim created, no runtime namespace occupied, no Path-E runtime artifact created, no accepted artifact modified, no frozen Oracle-PathE artifact modified, Path-D not reopened).**  The fresh qualifying third-party independent review of authorization-design candidate `26b183083fbbe323441283f99f3cf2c931acd6ff` (artifact `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_E_AUTHORIZATION.md`, SHA-256 `d8b75b7dbfda3075bd984f0f3da8569574a1fe4d3363da99ca395fbae87ac8a4`, 52469 bytes, 769 LF) was completed read-only with independence declared `THIRD-PARTY REVIEWER SESSION SEPARATION = SATISFIED`, `REVIEWER WAS NOT THE AUTHORIZATION-CANDIDATE-AUTHOR SESSION = YES`, `REVIEWER WAS NOT THE RATIFICATION-RECORD-AUTHOR SESSION = YES` and `REVIEWER DID NOT PREVIOUSLY REVIEW THIS EXACT AUTHORIZATION OBJECT = YES`, and returned **`REQUEST_CHANGES - V0.3-E PATH-E ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE`** with severity **`P0 = 0`, `P1 = 0`, `P2 = 2`, `P3 = 3`** - so the approval bar `P0 = 0 / P1 = 0 / P2 = 0` was **NOT** met.  **The two blocking findings were exactly:** `P2-1` **PRE-2 unsatisfiable self-identity gate** - PRE-2 required that no placeholder remain in the authorization-design commit own artifact, which is false by construction because the design-candidate state defined in 5.1 is precisely the placeholder state, and the clause additionally wired `path_e_authorization_commit` into a delta check over a value not determined until after the gated stage; and `P2-2` **PRE-3 contradictory effectivity gate** - PRE-3 purpose clause demanded that the authorization state be `non-effective` while its evidence clause demanded a tracked token that does not exist in any accepted control surface, verified absent at HEAD `d921dc90b4fd08dd7c8e28127d1bafe8d008d966` by `git grep`, whose surfaces carry `PATH-E EXECUTION AUTHORIZATION = NOT DESIGNED / NOT ACCEPTED` and `PATH-E AUTHORIZATION = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE` instead - classified by the reviewer as unexplained D-to-E semantic drift, since Path-D PRE-3 contained no such clause (Path-D precedent recovered and bound: candidate `29bf27fc2f76d415eb9c07d890f50b665aca6846`, review verdict `APPROVE`, acceptance bookkeeping `a7e3cccf5fa50a127ce92c2ed3529da1e926d5ed`, confirmation record `c1d7bd38be16ee7807c98044cdd8f17d83e97729`).  **No additional blocking finding was invented and no passed review area was altered:** candidate topology `EXACT`, Oracle-PathE binding `EXACT`, self-identity model `SAFE`, both claim schemas `CLOSED`, claim writer `FAIL-CLOSED`, all three budget models `EXACT`, irreversibility `CLOSED`, static-config binding `EXACT`, listener ownership `EXCLUSIVE`, target-binding ownership `ORACLE_ONLY`, runtime namespace `11` with occupancy `0 / 11`, result-class model `CLOSED`, result authority `PRESERVED`, failure model `FAIL-CLOSED`, current-effectivity boundary `CLOSED`, lifecycle `COMPLETE`, future review separation `CONSISTENT`, Path-D immutability `PRESERVED`, frozen Oracle-PathE P3 preservation `PRESERVED`, ratification state `CLOSED`, MODEL A `PRESERVED`.  **Owner-authorized bounded remediation performed - exactly two gate rows rewritten, plus the minimum directly associated wording, and nothing else.**  `P2-1` is corrected by rewriting PRE-2 so the future operational gate validates values frozen by the later **accepted control surfaces** rather than requiring the design-candidate artifact to rewrite itself: the accepted surfaces must already contain populated frozen values for both `path_e_authorization_commit` and `path_e_authorization_sha256`, populated only through the acceptance / confirmation lifecycle; no unresolved angle-bracket placeholder may remain **in those accepted surfaces**; the executor may not choose, guess, infer from `HEAD` or rewrite either value; and the design-candidate revision is explicitly **not** required to contain its own future accepted values.  `P2-2` is corrected by rewriting PRE-3 as a satisfiable **future operational** gate that separates three layers - (A) Oracle-PathE **design** effectivity, (B) Path-E **execution-authorization** effectivity, and (C) consumable authorization / attempt / execution state - evaluated immediately before the first irreversible authorization-use claim create, citing only tokens that are repository-verifiable in the accepted control surfaces (`ORACLE-PATHE = ACCEPTED / FROZEN / EFFECTIVE`, `QUALIFYING THIRD-PARTY DESIGN REVIEW = APPROVED`, `CORRECTIVE / SUPERSEDING ORACLE-PATHE DESIGN ACCEPTANCE BOOKKEEPING = CONFIRMED`, and the future `PATH-E AUTHORIZATION = ACCEPTED / FROZEN / EFFECTIVE` with `EXECUTION AUTHORITY = GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY`); the contradictory requirement that the authorization be `non-effective` at that same point is **deleted** and is stated instead as the design-candidate-stage fact it is.  The state model at 5.2 now marks the projection blocks as the future contract, and the current-status block at 27 now records `QUALIFYING THIRD-PARTY AUTHORIZATION DESIGN REVIEW OF 26B1830 = REQUEST_CHANGES` with severity `P0 = 0 / P1 = 0 / P2 = 2 / P3 = 3` and blocking findings `P2-1 PRE-2 UNSATISFIABLE SELF-IDENTITY GATE` and `P2-2 PRE-3 CONTRADICTORY EFFECTIVITY GATE`, records `26B1830 = HISTORICAL REJECTED CANDIDATE / SUPERSEDED BY A CORRECTED SUCCESSOR`, and separates the Oracle-PathE review-authority tokens from the Path-E authorization design-review verdict, which they never were.  **Byte discipline:** the artifact remains UTF-8 without BOM and LF-only with `CR = 0`, the known nonblocking `P3-2` trailing-LF run of 5 is **deliberately preserved and not normalised**, and `git diff --check` is clean; changed paths are exactly three and no fourth path exists - the authorization artifact (`12` insertions / `5` deletions net `+7` lines) plus `M CHANGELOG.md` plus `M docs/v0.3/V03E_ACCEPTANCE.md`.  The rejected artifact `d8b75b7dbfda3075bd984f0f3da8569574a1fe4d3363da99ca395fbae87ac8a4` / `52469` bytes / `769` LF is retained in history unamended and unreset; the corrected artifact SHA-256 is recorded by this commit.  **Self-review before commit: `P0 = 0`, `P1 = 0`, `P2 = 0`**, PRE-1 through PRE-15 all satisfiable, `PRE_GATE_MODEL = COMPLETE`, all three nonblocking P3 observations carried and **not** repaired (`P3-1` section-count characterisation, `P3-2` trailing LF run, `P3-3` generic-versus-Path-E UNKNOWN disambiguation contained in this document rather than the frozen Oracle spec).  **Effectivity is unchanged by this round:** `PATH-E AUTHORIZATION = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE`, `PATH-E AUTHORIZATION USE = NOT AVAILABLE FOR CONSUMPTION`, `PATH-E ETB ATTEMPT = NOT AVAILABLE FOR CONSUMPTION`, `PATH-E ETB EXECUTION = NOT AUTHORIZED`, `ORACLE-PATHE = ACCEPTED / FROZEN / EFFECTIVE`, `PATH-E RUNTIME OCCUPANCY = 0 / 11`, `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`.  **This remediation round performed** 0 Oracle-PathE executions, 0 Oracle-PathD executions, 0 ETB executions, 0 listener queries, 0 `Get-NetTCPConnection` calls, 0 port-4096 probes, 0 `localhost` / `127.0.0.1` probes, 0 endpoint probes, 0 OpenCode starts/restarts, 0 HTTP / provider / model calls, 0 claim creations, 0 budget creations, 0 budget consumptions, 0 evidence / manifest / result creations, 0 Path-E runtime artifact creations, 0 Path-D modifications, 0 frozen Oracle-PathE artifact modifications, 0 accepted-artifact mutations, 0 historical-lineage reopenings and 0 runtime / test / dependency / version changes.  **Exact next stage:** `FRESH QUALIFYING THIRD-PARTY INDEPENDENT REVIEW OF THE CORRECTED PATH-E EXECUTION-AUTHORIZATION DESIGN CANDIDATE`, which must run in a different agent/session from this remediation-author session - no third-party review, no authorization acceptance and no execution is performed in this round.  No tag, no release and no push occurred.  **PATH-E ETB EXECUTION-AUTHORIZATION ACCEPTANCE BOOKKEEPING - QUALIFYING THIRD-PARTY AUTHORIZATION DESIGN REVIEW APPROVED (design and governance only; nothing executed, no claim created, no budget created or consumed, no runtime namespace occupied, no reviewed artifact modified).**  The fresh qualifying third-party independent review of the corrected authorization-design candidate `4900625114a38a86aa03a5fa4861c5bcd9436dc5` (artifact `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_E_AUTHORIZATION.md`, SHA-256 `01d8dc6806e622cb361f47abee178e5beeddb8f95199ff21362938312a299d06`, 56105 bytes, 776 LF, CR `0`, no BOM, trailing LF run 5) was completed read-only in a different agent/session with the independence declarations recorded before any technical conclusion - `THIRD-PARTY REVIEWER SESSION SEPARATION = SATISFIED`, `REVIEWER WAS NOT THE CORRECTED-AUTHORIZATION-CANDIDATE-AUTHOR SESSION = YES`, `REVIEWER DID NOT PREVIOUSLY REVIEW THIS EXACT CORRECTED AUTHORIZATION OBJECT = YES` - and returned **`APPROVE V0.3-E PATH-E CORRECTED ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE - QUALIFYING THIRD-PARTY INDEPENDENT REVIEW`** with severity **`P0 = 0`, `P1 = 0`, `P2 = 0`, `P3 = 3`**, so the approval bar `P0 = 0 / P1 = 0 / P2 = 0` was **met**.  Both former blocking findings are independently confirmed closed: `P2-1 PRE-2 SELF-IDENTITY DEFECT = CLOSED` - the corrected PRE-2 validates the populated frozen values in the later accepted control surfaces, exempts the design-candidate revision, and removes the absolute no-placeholder clause that made the gate unsatisfiable by construction; and `P2-2 PRE-3 EFFECTIVITY CONTRADICTION = CLOSED` - the contradictory `non-effective` requirement is deleted from the future operational gate and retained only as the design-candidate-stage fact it is; `PRE-1` through `PRE-15` are independently re-measured as **ALL SATISFIABLE**, `PRE_GATE_MODEL = COMPLETE`, and `D-to-E SEMANTIC DRIFT = NONE UNEXPLAINED` (the corrected PRE-2 wording is a faithful semantic port of the approved Path-D precedent, which itself carries the same two placeholders, and the superseded absolute clause was the actual drift).  **Formal review severity is recorded exactly as the qualifying review classified it:** `P0 = 0` / `P1 = 0` / `P2 = 0` / `P3 = 3`, where the three formal `P3` findings are `P3-A` section-count / ASCII characterisation inaccuracy in historical governance prose (disposition `P3 / DOCUMENTATION CHARACTERISATION / NONBLOCKING / NOT REPAIRED`), `P3-B` trailing LF run of `5` (disposition `P3 / BYTE-FORMAT PRECISION / NONBLOCKING / NOT NORMALIZED`, deliberately preserved because normalising it would itself change the frozen blob identity), and `P3-C` remediation-author elevated execution-context disclosure not materialised in the tracked governance surfaces (disposition `P3 / PROCESS TRANSPARENCY / NONBLOCKING`); separately carried and **explicitly NOT counted as formal P3 findings** are two additional nonblocking observations - `OBSERVATION-1` the design candidate does not embed its own future accepted commit/SHA (disposition `REQUIRED BY DESIGN / NONBLOCKING / NOT A SELF-IDENTITY DEFECT`, since embedding it would re-create `P2-1`) and `OBSERVATION-2` generic-versus-Path-E `UNKNOWN` disambiguation is centralised in the authorization artifact rather than modifying the frozen Oracle-PathE spec (disposition `REQUIRED / DEFENSIBLE CONTAINMENT / NONBLOCKING`), so **no nonblocking observation is promoted or demoted and no extra `P3` is invented**.  **Accepted authorization identity frozen by this bookkeeping (immutable):** `path_e_authorization_commit` = `4900625114a38a86aa03a5fa4861c5bcd9436dc5` - the independently approved authorization-design commit, **not** the acceptance commit and **not** the later confirmation record; `path_e_authorization_sha256` = `01d8dc6806e622cb361f47abee178e5beeddb8f95199ff21362938312a299d06`; artifact bytes `56105`, LF `776`, CR `0`, BOM absent, trailing LF run `5`, UTF-8 and LF-only, worktree byte-identical to the committed blob; the corrected candidate does **not** and may **not** rewrite its own artifact to substitute either value, and the executor may never choose, guess, infer from `HEAD` or rewrite them.  **Oracle-PathE frozen provenance re-verified and preserved:** `oracle_path_e_commit` = `f7cafd83a95225e1ce9565a9336ded8575b65335`, `oracle_path_e_spec_sha256` = `78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b` (`33881` bytes), `oracle_path_e_script_sha256` = `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb` (`41610` bytes), `ORACLE-PATHE = ACCEPTED / FROZEN / EFFECTIVE`, `ORACLE-PATHE EXECUTION = NOT AUTHORIZED`; neither frozen Oracle-PathE artifact was modified.  **Rejected predecessor disposition preserved:** `26B1830 = HISTORICAL / REVIEW RETURNED REQUEST_CHANGES / SUPERSEDED BY A CORRECTED SUCCESSOR`, retained in history unamended, unreset and undeleted.  **Two-stage effectivity (NOT collapsed):** this commit is **acceptance bookkeeping provenance only** and replaces neither frozen authorization value; the authorization becomes `ACCEPTED / FROZEN / EFFECTIVE` **only** after a **fresh independent confirmation of THIS bookkeeping commit** performed in a different agent/session from this acceptance-bookkeeping-author session, so immediately after this bookkeeping the state is `PATH-E EXECUTION AUTHORIZATION = CONDITIONALLY ACCEPTED / NOT YET FROZEN / NOT YET EFFECTIVE` (the established repository form for the acceptance-bookkeeping stage, recovered from the Path-D precedent), `PATH-E AUTHORIZATION USE = NOT AVAILABLE FOR CONSUMPTION`, `PATH-E ETB ATTEMPT = NOT AVAILABLE FOR CONSUMPTION`, `PATH-E ETB EXECUTION = NOT AUTHORIZED`, `ORACLE-PATHE INVOCATION = NOT AUTHORIZED BY THIS ROUND`, `PATH-E RUNTIME OCCUPANCY = 0 / 11`, `PATH-E CLAIM PATHS = ABSENT (4 / 4)`.  **Execution remains closed until confirmation:** the authorization-use budget `PATH_E_AUTHORIZATION_USE_BUDGET = 1 OF 1` and the attempt budget `PATH_E_ETB_ATTEMPT_BUDGET = 1 OF 1` remain unavailable for operational consumption and unconsumed, `ORACLE-PATHE INVOCATIONS = 1 OF 1` remains unavailable, the claim schemas `devrelay-etb-path-e-authorization-use-v1` and `devrelay-etb-path-e-attempt-use-v1` and the frozen writer `Write-DevRelayPathEOneShotClaim` are unchanged, no claim TEMP or FINAL file was created, no evidence, manifest or result was created, no listener was queried, no endpoint was probed, `PATH-D = EXHAUSTED / CLOSED / IMMUTABLE` with zero Path-D reuse, and `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED` with no ETB observation and no authoritative-result replacement.  **This acceptance-bookkeeping round performed** 0 Oracle-PathE executions, 0 Oracle-PathD executions, 0 ETB executions, 0 listener queries, 0 `Get-NetTCPConnection` calls, 0 endpoint probes, 0 port-4096 probes, 0 `localhost` / `127.0.0.1` probes, 0 OpenCode starts/restarts, 0 HTTP / provider / model calls, 0 claim creations, 0 budget creations, 0 budget consumptions, 0 evidence / manifest / result creations, 0 Path-E runtime artifact creations, 0 Path-D modifications, 0 frozen Oracle-PathE artifact modifications, 0 accepted-artifact mutations, 0 authorization-artifact modifications and 0 runtime / test / dependency / version changes.  **Exact next stage:** `FRESH THIRD-PARTY INDEPENDENT CONFIRMATION OF THE PATH-E ETB EXECUTION-AUTHORIZATION ACCEPTANCE BOOKKEEPING`, which must run in a different agent/session from this acceptance-bookkeeping-author session - no independent confirmation, no claim creation, no budget creation or consumption and no execution is performed in this round.  No tag, no release and no push occurred.

**PATH-E ETB EXECUTION-AUTHORIZATION - THIRD-PARTY INDEPENDENT CONFIRMATION: CONFIRMATION-RECORD CLOSURE (governance record only; nothing executed, no claim created, no budget created or consumed, no reviewed artifact modified).**  This is a **GOVERNANCE-ONLY record-closure round**: it does **not** retry the ETB, does **not** re-run or re-authorize Oracle-PathE or Oracle-PathD, does **not** perform a second authorization acceptance, does **not** perform a second acceptance bookkeeping, does **not** produce a new authorization design, does **not** grant new owner execution authorization, does **not** consume any claim, and performs **no** operational action.  **Recovered precedent (structure determined by existing precedent, not invented):** the DevRelay bookkeeping-structure contract frozen by the accepted Recovery-R2 authorization (`PRE-1`, `11.4`, `11.7`) requires a governed state transition to become a repository-verifiable fact through **exactly ONE single-parent child commit whose sole tracked delta against its parent is `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md` and NO third tracked path**; the **directly governing precedent is `c1d7bd38be16ee7807c98044cdd8f17d83e97729`** (`docs(v03e): record Path-D authorization confirmation`), which materialized the completed Path-D third-party confirmation as exactly such a record commit with the same two-file delta, and the two-file bookkeeping-shape precedent is `9b17912...`; the same two-stage authorization-confirmation structure was already recovered and applied for the Oracle-PathE design acceptance bookkeeping.  **That precedent determines this round's shape; no new structure was invented, no third status surface was created and no confirmation artifact was created.**  The **fresh third-party independent confirmation** of the Path-E ETB execution-authorization acceptance bookkeeping `48e9b66dd5aeb147795dbc57e822e6b3d38e4565` - completed in the immediately preceding round as a **review-only event with no commit** - is hereby **materialized as a repository-verifiable fact**: `CONFIRMATION VERDICT = APPROVE V0.3-E PATH-E ETB EXECUTION-AUTHORIZATION ACCEPTANCE-BOOKKEEPING CONFIRMATION`; `CONFIRMED BOOKKEEPING COMMIT = 48e9b66dd5aeb147795dbc57e822e6b3d38e4565`; `CONFIRMED AUTHORIZATION DESIGN = 4900625114a38a86aa03a5fa4861c5bcd9436dc5`; `THIRD-PARTY INDEPENDENCE = SATISFIED`; `CONFIRMATION RESULT = P0 = 0, P1 = 0, P2 = 0, P3 = 3`.  **Confirmation-stage independence declarations (recorded before any technical conclusion, and materialized by this record):** `THIRD-PARTY CONFIRMER SESSION SEPARATION = SATISFIED`; `CONFIRMER WAS NOT THE CORRECTED-AUTHORIZATION-CANDIDATE-AUTHOR SESSION = YES`; `CONFIRMER WAS NOT THE QUALIFYING AUTHORIZATION-DESIGN-REVIEW SESSION = YES`; `CONFIRMER WAS NOT THE ACCEPTANCE-BOOKKEEPING-AUTHOR SESSION = YES`; `CONFIRMER DID NOT PREVIOUSLY CONFIRM THIS EXACT BOOKKEEPING OBJECT = YES`; the confirmation was performed read-only, in a different agent/session from the accepted-design author, the qualifying-review session and the acceptance-bookkeeping-author session.  **Thirteen confirmation checks independently re-performed and PASSED:** (1) **parent** - the bookkeeping commit has parent `4900625114a38a86aa03a5fa4861c5bcd9436dc5` exactly; (2) **subject** - `docs(v03e): accept Path-E ETB authorization`; (3) **two-file governance-only delta** - sole tracked delta against that parent is exactly `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md`, `1 1` / `1 1`, **no third tracked path**, and both changes are **pure in-place appends** (the acceptance-surface delta shares a common prefix of `181356` characters and the same 47-character terminal suffix, with an **empty** removed-only middle, so no accepted byte was deleted or rewritten); (4) **qualifying review bound exactly** - `APPROVE V0.3-E PATH-E CORRECTED ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE - QUALIFYING THIRD-PARTY INDEPENDENT REVIEW` bound to candidate `4900625114a38a86aa03a5fa4861c5bcd9436dc5`; (5) `P2-1 PRE-2 SELF-IDENTITY DEFECT = CLOSED`; (6) `P2-2 PRE-3 EFFECTIVITY CONTRADICTION = CLOSED`; (7) `PRE_GATE_MODEL = COMPLETE` with `PRE-1 ... PRE-15 = ALL SATISFIABLE`; (8) **formal review severity** `P0 = 0 / P1 = 0 / P2 = 0 / P3 = 3`; (9) **accepted authorization identity** exactly `path_e_authorization_commit = 4900625114a38a86aa03a5fa4861c5bcd9436dc5`; (10) **accepted artifact SHA-256** exactly `path_e_authorization_sha256 = 01d8dc6806e622cb361f47abee178e5beeddb8f95199ff21362938312a299d06`, recomputed from the committed blob `061f61ef686db1553842f1c26295fb6d33f41127` (`56105` bytes, `776` LF, CR `0`, NO BOM, UTF-8, trailing LF run `5`) and byte-identical to the worktree file; (11) **Oracle-PathE frozen identities unchanged** - `oracle_path_e_commit = f7cafd83a95225e1ce9565a9336ded8575b65335`, `oracle_path_e_spec_sha256 = 78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b`, `oracle_path_e_script_sha256 = c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb`, both independent Oracle-PathE artifacts byte-unchanged; (12) **Path-D immutability** - `PATH-D = EXHAUSTED / CLOSED / IMMUTABLE`, `PATH-D RETRY AUTHORITY = NONE`, `PATH-D AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`, `PATH-D ETB ATTEMPT = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`, `ORACLE-PATHD INVOCATIONS = 1 OF 1 / MAXIMUM REACHED`, both Path-D claims byte-frozen and both Path-D authorization artifacts byte-unchanged, with **zero Path-D reuse or modification**; (13) **Path-E absence, budgets and runtime** - all four Path-E claim paths **ABSENT**, `PATH-E RUNTIME OCCUPANCY = 0 / 11`, `PATH-E AUTHORIZATION USE` and `PATH-E ETB ATTEMPT` **unconsumed at `0 OF 1` each**, `ORACLE-PATHE INVOCATIONS = 0 OF 1`, and `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`; the absence of every Path-E claim and of every reserved Path-E runtime path was proven by **positive per-path existence testing** (`.NET` file and directory existence checks over all eleven reserved paths), **not** by any zero-match text search, and no `Select-String` zero-match result was used as evidence anywhere in this round.  **Repository-verifiable effectivity contract (frozen by this record; derivable only from Git commit topology plus tracked status-surface bytes plus frozen authorization artifact identity - never from chat history, conversation transcripts or agent memory):** (1) authorization design commit `path_e_authorization_commit = 4900625114a38a86aa03a5fa4861c5bcd9436dc5`; (2) authorization artifact `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_E_AUTHORIZATION.md` with committed-blob SHA-256 `path_e_authorization_sha256 = 01d8dc6806e622cb361f47abee178e5beeddb8f95199ff21362938312a299d06`; (3) acceptance-bookkeeping commit `48e9b66dd5aeb147795dbc57e822e6b3d38e4565`; (4) third-party independent confirmation of that bookkeeping commit `= APPROVED` with `THIRD-PARTY INDEPENDENCE = SATISFIED`; (5) `PATH-E AUTHORIZATION = ACCEPTED / FROZEN / EFFECTIVE`; (6) `EXECUTION AUTHORITY = GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY`; (7) `PATH-E AUTHORIZATION USE = 1 OF 1 / AVAILABLE FOR CONSUMPTION` with actual consumption `0 OF 1 / NOT CONSUMED`; (8) `PATH-E ETB ATTEMPT = 1 OF 1 / AVAILABLE FOR CONSUMPTION` with actual consumption `0 OF 1 / NOT STARTED`; (9) `ORACLE-PATHE INVOCATIONS = 1 OF 1 / AVAILABLE ONLY AFTER BOTH CLAIMS EXIST` with actual invocations `0`.  **Mechanical recognition rule for a future executor (topology plus content, requiring no external testimony):** the confirmation-record commit is the **single-parent** commit whose parent is exactly `48e9b66dd5aeb147795dbc57e822e6b3d38e4565`, whose sole tracked delta against that parent is **exactly** `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md` (**no third tracked path**), and whose active status surfaces state `PATH-E AUTHORIZATION = ACCEPTED / FROZEN / EFFECTIVE` bound to design commit `4900625114a38a86aa03a5fa4861c5bcd9436dc5` and artifact SHA-256 `01d8dc6806e622cb361f47abee178e5beeddb8f95199ff21362938312a299d06`, with both Path-E budgets stated `1 OF 1 / AVAILABLE FOR CONSUMPTION` yet `NOT CONSUMED`; all of those conditions hold simultaneously and are checked mechanically.  **No self-reference:** this record deliberately does **not** embed its own commit SHA - it is identified only by its parent, its subject, its changed-path set and the frozen provenance stated here; the subject is `docs(v03e): record Path-E authorization confirmation`, which is **not** an acceptance subject and does **not** imply a second acceptance-bookkeeping event.  **Anti-recursion (no new effectivity dependency is created):** this confirmation record becomes the repository-verifiable **effectivity fact**, and any follow-up **third-party read-only verification of this closure** is a **verification of an existing record, not a new acceptance or effectivity event** - it spawns **no** further record commit, **no** recursive lifecycle and **no** additional dependency chain.  **Frozen sequence position (recovered, not invented):** the accepted design (`26`, `5.3`) freezes the ordered lifecycle `1` design candidate, `2` qualifying third-party independent review, `3` acceptance bookkeeping as exactly one two-file single-parent commit, `4` fresh independent confirmation of that bookkeeping, `5` materialization of that confirmation as exactly one record commit of the same two-file shape, `6` authorization effectivity (`ACCEPTED / FROZEN / EFFECTIVE` with `EXECUTION AUTHORITY = GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY`), `7` a fresh operational execution session performing `13` through `20` in order.  This single confirmer session performed stage `4` and stage `5`, and **nothing more**; the effectivity of stage `6` is stated here as the **result of the completed stages `4` and `5`** and is carried **only** by the two accepted control surfaces.  **Authorization effectivity is now established and is NOT consumed:** `PATH-E EXECUTION AUTHORIZATION = ACCEPTED / FROZEN / EFFECTIVE`; `PATH-E AUTHORIZATION USE = 1 OF 1 / AVAILABLE FOR CONSUMPTION` while `AUTHORIZATION-USE CLAIM = ABSENT` and `AUTHORIZATION BUDGET CONSUMED = 0 OF 1`; `PATH-E ETB ATTEMPT = 1 OF 1 / AVAILABLE FOR CONSUMPTION` while `ATTEMPT-USE CLAIM = ABSENT` and `ETB-ATTEMPT BUDGET CONSUMED = 0 OF 1`; `ORACLE-PATHE INVOCATIONS = 1 OF 1 / AVAILABLE ONLY AFTER BOTH CLAIMS EXIST` while `ORACLE-PATHE INVOCATION CONSUMED = 0 OF 1`.  **Making the one-shot authority operationally available does NOT consume it**; no claim TEMP or FINAL file was created, and the claim schemas `devrelay-etb-path-e-authorization-use-v1` and `devrelay-etb-path-e-attempt-use-v1` together with the frozen writer `Write-DevRelayPathEOneShotClaim` remain unchanged.  **Budgets remain pristine and untouched by this record:** `PATH_E_AUTHORIZATION_USE_BUDGET = 1 OF 1` with `PATH_E_AUTHORIZATION_USE = 0 OF 1 / NOT CONSUMED`; `PATH_E_ETB_ATTEMPT_BUDGET = 1 OF 1` with `PATH_E_ETB_ATTEMPT = 0 OF 1 / NOT STARTED`; every historical budget remains spent and not reusable - the original Round-5 authorization `SPENT / NOT REUSABLE`, Recovery-R1 `SPENT / NOT REUSABLE`, Recovery-R2 authorization and attempt `SPENT / NOT REUSABLE`, `D1 AUTHORIZATION / DIAGNOSTIC ATTEMPT = SPENT / 1 OF 1 / IRREVERSIBLE / NOT REUSABLE`, `D1 LISTENER QUERY = EXECUTED ONCE / NO RETRY`, Path-D authorization use and attempt `SPENT / IRREVERSIBLE / NOT REUSABLE`.  **Execution remains closed:** `PATH-E ETB EXECUTION = NOT AUTHORIZED BY THIS ROUND`; `ORACLE-PATHE EXECUTION = NOT AUTHORIZED BY THIS ROUND`; `ORACLE-PATHD EXECUTION = NOT AUTHORIZED`; `LISTENER QUERY = NOT EXECUTED`; `TARGET PROBE = NOT EXECUTED`; NO authorization-use claim, NO attempt-use claim, NO evidence, NO manifest, NO result; `PATH-E RUNTIME OCCUPANCY = 0 / 11`; `PATH-E CLAIM PATHS = ABSENT (4 / 4)`; this record grants **no** execution effectivity of its own, collapses **no** execution stage, and the execution attempt remains governed by `13` through `20` in a **separate fresh operational execution session**.  **Result authority preserved:** `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`; a confirmation record creates **no** semantic result, and any future Path-E execution observation must still pass **independent result review - result bookkeeping - independent bookkeeping confirmation** before becoming authoritative.  **Oracle-PathE design effectivity preserved (separate layer, unchanged):** `ORACLE-PATHE = ACCEPTED / FROZEN / EFFECTIVE`; `QUALIFYING THIRD-PARTY DESIGN REVIEW = APPROVED`; `CORRECTIVE / SUPERSEDING ORACLE-PATHE DESIGN ACCEPTANCE BOOKKEEPING = CONFIRMED`; both frozen Oracle-PathE artifacts byte-unchanged; `26B1830 = HISTORICAL / REQUEST_CHANGES / SUPERSEDED BY A CORRECTED SUCCESSOR`, retained unamended, unreset and undeleted.  **MODEL A preserved:** no runtime, generated or operational Path-E artifact became tracked and **no** Path-E runtime artifact was created at all; all operational artifacts remain untracked and byte-unchanged; the only tracked advance is the two accepted active status surfaces.  **Historical immutability preserved:** the Path-E authorization artifact, both accepted Oracle-PathE artifacts, the Path-D authorization artifact, both Path-D claims, the Path-D spec and executable, Oracle-R2, Recovery-R1, Recovery-R2, D1, the original oracle artifacts, `.gitattributes`, all claims, evidence, manifests, results, configuration and construction-time banners are **byte-unchanged**, and no `P3` observation was "fixed" by rewriting any reviewed, accepted or confirmed byte.  This governance record round performed **0** authorization-use claim creations, **0** attempt-use claim creations, **0** Path-E claim creations of any kind, **0** Oracle-PathE executions, **0** Oracle-PathD executions, **0** ETB executions, **0** listener queries, **0** `Get-NetTCPConnection` calls, **0** endpoint probes, **0** port-4096 probes, **0** `localhost` probes, **0** `127.0.0.1` probes, **0** OpenCode starts or restarts, **0** HTTP calls, **0** provider or model calls, **0** budget consumptions, **0** evidence/manifest/result creations, **0** Path-E runtime namespace entries created, **0** configuration mutations, **0** endpoint-state modifications, **0** reviewed-artifact mutations, **0** Path-D modifications and **0** runtime/test/dependency/version changes.  **Exact next stage:** a **SEPARATE FRESH PATH-E ONE-SHOT OPERATIONAL EXECUTION SESSION** that performs `13` through `20` in order under the now-effective authority (stage `7` of the frozen sequence) - this confirmation session makes **no** execution attempt and takes **no** operational action.  No tag, no release and no push occurred.

**PATH-E BLOCKED RAW OPERATIONAL RESULT - OWNER-AUTHORIZED GOVERNANCE DISPOSITION (governance record only; nothing executed, nothing retried, no claim created, altered or deleted, no budget reset, no namespace cleanup, no raw artifact rewritten, no ACL removed or restored, no Path-D touched, no output synthesized, no reviewed artifact modified).**  This is a **GOVERNANCE-ONLY disposition round** for the **blocked** Path-E raw operational result: it does **not** execute anything, does **not** retry anything, does **not** promote anything and does **not** rewrite any reviewed or raw byte.  The Path-E one-shot operational round was executed in a separate operational session and consumed the accepted one-shot authorization exactly once.  **Control-layer outcome:** the first authorization-claim `CreateNew` (TEMP publication) threw before consumption, and `15` of the accepted authorization requires that on any thrown error the round "stop[s] immediately", does not retry, does not delete the TEMP file, does not proceed to `16` or `18`, and "ends as a control failure under `17`" - so the round's frozen control-layer outcome is `PATH-E AUTHORIZATION CONTROL FAILURE`, which `17` states "is **not** `ETB_UNSATISFIED`, **not** `HARNESS_INVALID`, **not** an ETB semantic result and **not** `ETB_SATISFIED`".  **Deviations recorded rather than concealed:** `17` consequences 1 and 2 were **not** respected by the subsequent operational conduct - the failed `CreateNew` was non-consuming, yet a later authorization-claim creation was performed anyway (**P2-1**, unauthorized post-failure re-attempt) and the Oracle was consequently entered, so an ETB attempt **was** made and the attempt budget **was** consumed; consequences 3, 4 and 5 stand as recorded below.  **Raw observation - present, valid, retained and NOT promoted:** `RAW ORACLE BYTES = PRESENT / VALID`; `RAW ORACLE OBSERVATION = ETB_UNSATISFIED`; identities `docs/v0.3/evidence/ETB_PATH_E_AUTHORIZATION_USE.claim` (`495` bytes, SHA-256 `015b4bfa0d8d80465f59b219f03dea63ff262f98d5846976246d1545565b5f63`), `docs/v0.3/evidence/ETB_PATH_E_ATTEMPT_USE.claim` (`489` bytes, SHA-256 `baa14916c1c3b65bcdffc1ec1e1c96abc44440611fb8fa76f51dba53121d4cee`), `docs/v0.3/evidence/etb-execution-path-e/ETB_EVIDENCE.json` (`4373` bytes, SHA-256 `0e28ffe19ac3c9ff8f7b630687b93f79897013a5902e496078cb4a1c9f6c0d1d`), `docs/v0.3/evidence/etb-execution-path-e/MANIFEST.sha256` (`124` bytes, SHA-256 `6ee974ef20e37831f5c5a70e8521ef83a1d7f1d4c5e30188865189bb3dccf30a`), `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_E.md` (`761` bytes, SHA-256 `21eeea13f3fee714a8c8d8967e0861fd09d9fecc2bb3ee6bf7d8fc11d7050711`); all remain **untracked, unstaged, uncommitted and byte-unchanged** (`MODEL A` preserved) and the raw result still carries its construction-time banner `CANDIDATE ETB RESULT / AWAITING INDEPENDENT RESULT REVIEW` - no `ACCEPTED`, no `FROZEN`, no `EFFECTIVE`, no promotion.  **Qualifying third-party raw-result review:** performed by a fresh session-separated reviewer (`THIRD-PARTY RAW-RESULT REVIEWER SESSION SEPARATION = SATISFIED`, pre-gate model complete) which returned `RAW RESULT PROMOTION ELIGIBILITY = REJECTED / BLOCKED` with severity `P0 = 0 / P1 = 0 / P2 = 2 / P3 = 2`: blocking **P2-1** (the failed pre-consumption `CreateNew` was non-consuming, but the re-attempt was not authorized by the frozen contract) and **P2-2** (the ACL mutation of `docs`, `docs\v0.3` and `docs\v0.3\evidence` was unauthorized; `SEMANTIC EFFECT = NON-SEMANTIC`; the ACL state is not normalized, not restored in this round, and no rollback script is inferred to authorize restoration), nonblocking **P3-1** (full-file-access escalation / nonblocking process variance) and **P3-2** (operator runtime occupancy reported `2 / 11` against an actual frozen-namespace occupancy of `6 / 11`; reporting-only).  **Promotion gate FAILED:** the `21` promotion pipeline stopped at its result-review stage, so no new ETB semantic result becomes authoritative; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED` is **unchanged** - its authority derives from the previously accepted Recovery-R2 result, **not** from this Path-E attempt, and the coincidence of the raw and authoritative strings is **not** promotion; `PATH-E ETB SEMANTIC RESULT = NONE`.  **One-shot consumption, freshly verified:** `PATH-E AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `PATH-E ETB ATTEMPT = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `ORACLE-PATHE INVOCATIONS = 1 OF 1 / MAXIMUM REACHED`; both FINAL claims present and all TEMP claim paths absent; the exhausted state, in the precedent composite status-line form (`3541c01`), is `PATH-E AUTHORIZATION = SPENT / NOT REUSABLE / AUTHORIZATION USE 1 OF 1 CONSUMED / ETB ATTEMPT 1 OF 1 CONSUMED / ETB SEMANTIC RESULT NONE / PATH-E AUTHORIZATION CONTROL FAILURE`.  **`RETRY AUTHORITY = NONE`** - no retry, no reuse of any Path-E claim, budget, namespace or authorization, and this round creates no new authorization.  **Namespace accounting:** `PATH-E RUNTIME NAMESPACE = 11 PATHS`; `PATH-E RUNTIME OCCUPANCY = 6 / 11` (present: the runtime directory `docs/v0.3/evidence/etb-execution-path-e`, `ETB_EVIDENCE.json`, `MANIFEST.sha256`, the result FINAL, the authorization-use claim FINAL, the attempt-use claim FINAL; absent: the five TEMP paths `ETB_PATH_E_AUTHORIZATION_USE.claim.tmp`, `ETB_PATH_E_ATTEMPT_USE.claim.tmp`, `etb-execution-path-e/ETB_EVIDENCE.json.tmp`, `etb-execution-path-e/MANIFEST.sha256.tmp`, `V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_E.md.tmp`) - recorded, not normalized; nothing was deleted, moved, renamed, truncated or rewritten and occupancy is **not** restored to zero.  **Path-D preserved:** `PATH-D = EXHAUSTED / CLOSED / IMMUTABLE`, both Path-D budgets `SPENT / IRREVERSIBLE / NOT REUSABLE`, `ORACLE-PATHD INVOCATIONS = 1 OF 1 / MAXIMUM REACHED`, `PATH-D ETB SEMANTIC RESULT = NONE`, `PATH-D RETRY AUTHORITY = NONE` - zero reuse, no reopen, no repair, no rerun.  **Accounting reconciled:** collapsed `git status --porcelain` entries `19`, expanded file-level inventory `24` (`11` claim files + `4` result documents + `9` files inside the four evidence directories), staged `0`, tracked worktree clean.  **Commit shape:** this disposition is a **single-parent** commit whose parent is exactly `c7ac36a8c596ae2ede8db7bce2e625f8c6ffa21c` and whose sole tracked delta is `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md` with **no third path** (shape precedent `15dc615`, the Path-D operational-outcome record, plus the accepted `21` stage 3 / `26` stage 3 requirement).  **MODEL A preserved**; no `P3` observation was "fixed" by rewriting confirmed bytes; the raw result was **not** rewritten and its candidate banner was **not** upgraded.  This record round performed 0 authorization-use claim creations, 0 attempt-use claim creations, 0 Oracle-PathE executions, 0 Oracle-PathD executions, 0 ETB executions, 0 retries, 0 claim deletions or modifications, 0 listener queries, 0 `Get-NetTCPConnection` calls, 0 endpoint or port probes, 0 OpenCode starts/restarts, 0 HTTP, 0 provider/model calls, 0 budget consumptions or resets, 0 evidence/manifest/result creations, 0 runtime cleanups, 0 ACL changes, 0 config mutations, 0 raw-result mutations, 0 Path-D modifications and 0 runtime/test/dependency/version changes.  **Exact next stage:** a **THIRD-PARTY INDEPENDENT PATH-E BLOCKED-RESULT DISPOSITION-BOOKKEEPING CONFIRMATION** (read-only, no commit, no Oracle, no listener query, no claim mutation, no retry; a different agent/session, **not** performed in this round) - this round makes **no** execution attempt and takes **no** operational action.  No tag, no release and no push occurred.

**PATH-E POST-DISPOSITION GOVERNANCE RECONCILIATION (corrective successor record; governance only - nothing executed, no Oracle invocation, no retry, no claim created, altered or deleted, no budget created, consumed or reset, no raw artifact rewritten, no ACL changed, no Path-D touched, no semantic result created).**  **Owner decision recorded:** `OWNER DECISION = OPTION C / BOUNDED POST-DISPOSITION GOVERNANCE RECONCILIATION`, taken before - and without making - the still-deferred decision between declaring Path-E lineage closure and opening a new successor ETB lineage.  This successor record bounds the two nonblocking observations of the fresh third-party independent confirmation of `44471fcfec8f3378dd6feb9c3803207db477a713` (verdict `APPROVE V0.3-E PATH-E BLOCKED RAW RESULT DISPOSITION BOOKKEEPING - THIRD-PARTY INDEPENDENT CONFIRMATION`); the confirmed commit is **NOT** deleted, **NOT** rewritten and **NOT** reversed in any operational fact, and no reviewed, accepted or frozen artifact is modified.  **`P3-A = CROSS-DOCUMENT PROVENANCE WORDING TENSION - RECONCILED / BOUNDED`:** Oracle-produced evidence, manifest and result bytes are governed by the accepted `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_E.md` specification, which owns artifact content, publication order and identity binding (`§13.3` assigns the listener query, target resolution, snapshot acquisition, continuity evaluation and all ETB result classification exclusively to the accepted Oracle-PathE executable, and `§20` states that the Oracle's own identity binding, publication order and exit-code contract are owned by that specification and are **not** restated, amended, weakened or extended by the authorization), so its Path-E-specific provenance fields `oracle_path_e_commit`, `oracle_path_e_spec_sha256` and `oracle_path_e_script_sha256` may remain the literal value `UNKNOWN` exactly as frozen - which authorizes **no** inference, **no** defaulting and **no** fabrication, and is **not** corrected by editing the specification (authorization `§3` consequence 1 already declares those specification-level `UNKNOWN` values **not defects**).  Authorization `§3` consequence 2 is read as a **lineage-binding and anti-substitution rule** - no Path-D, Oracle-R2, Recovery-R1, Recovery-R2 or D1 identity may stand in for a Path-E identity anywhere in this lineage - and **NOT** as a requirement to rewrite, regenerate, normalize, republish or post-hoc edit Oracle-generated evidence.  **Precedence (clarified here and nowhere else; neither frozen document is modified and neither is defective):** for the **content** of an Oracle-generated artifact the accepted **Oracle-PathE specification** governs; for the **lineage binding** the accepted **Path-E authorization `§3`** governs, and the binding is carried repository-verifiably by the executor-owned one-shot claims, which do carry the frozen triple `f7cafd83a95225e1ce9565a9336ded8575b65335` / `78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b` / `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb`, together with `authorization_commit 4900625114a38a86aa03a5fa4861c5bcd9436dc5` and `authorization_sha256 01d8dc6806e622cb361f47abee178e5beeddb8f95199ff21362938312a299d06`, and additionally by these governance/status surfaces, which supply the external lineage binding between the raw Oracle bytes and the accepted Path-E frozen triple.  A literal `UNKNOWN` in Oracle-produced bytes is not a promotion, not an acceptance, not an effectivity and not an ETB semantic result, and populating those fields would require its own separately Owner-authorized round.  The blocked raw result remains non-promotable for the already-confirmed `P2` control violations, independently of this wording issue.  **`P3-B = PRE_GATE_MODEL BINDING PRECISION - CLOSED`:** the qualifying raw-result review, whose verdict binds as `RAW RESULT PROMOTION ELIGIBILITY = REJECTED / BLOCKED` with severity `P0 = 0 / P1 = 0 / P2 = 2 / P3 = 2` and with both `P2` control violations intact, established `QUALIFYING RAW-RESULT REVIEW PRE_GATE_MODEL = COMPLETE`; recording that literal token here supplies a **completeness** statement of the confirmed review and changes no review verdict, no severity, no finding, no promotion eligibility and no semantic result, so the raw result stays blocked and non-promotable.  **ACL residual-state governance note:** `ACL MUTATION DURING OPERATIONAL ROUND = UNAUTHORIZED`; `SEMANTIC EFFECT = NON-SEMANTIC`; the residual ACL state exists only **outside** tracked Git content and is preserved as found - `ACL STATE = NOT NORMALIZED`, `ACL RESTORATION = NOT AUTHORIZED BY THIS ROUND`, `ROLLBACK SCRIPTS = NOT AUTHORITY`; any future restoration or normalization requires separate explicit Owner authorization and must be evaluated against the no-cleanup / preserved-state constraints, and this round does not decide it, does not inspect-modify it and executes no rollback script.  **Preserved unchanged by this round:** `RAW ORACLE BYTES = PRESENT / VALID`; `RAW ORACLE OBSERVATION = ETB_UNSATISFIED`; `RAW RESULT PROMOTION ELIGIBILITY = REJECTED / BLOCKED`; `PATH-E ETB SEMANTIC RESULT = NONE`; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`; `PATH-E AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `PATH-E ETB ATTEMPT = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `ORACLE-PATHE INVOCATIONS = 1 OF 1 / MAXIMUM REACHED`; `RETRY AUTHORITY = NONE`; `PATH-E RUNTIME NAMESPACE = 11 PATHS` and `PATH-E RUNTIME OCCUPANCY = 6 / 11`; `PATH-D = EXHAUSTED / CLOSED / IMMUTABLE` with both Path-D budgets `SPENT / IRREVERSIBLE / NOT REUSABLE`, `ORACLE-PATHD INVOCATIONS = 1 OF 1 / MAXIMUM REACHED`, `PATH-D ETB SEMANTIC RESULT = NONE` and `PATH-D RETRY AUTHORITY = NONE` - zero Path-D reuse, zero reopen, zero repair, zero rerun.  **No closure, no new lineage, no new authority:** `PATH-E LINEAGE CLOSURE = NOT DECLARED / OWNER DECISION DEFERRED`; this round creates no closure declaration, no successor lineage, no new oracle, no authorization, no budget, no claim, no evidence, no manifest, no result and no new one-shot authority.  Round counters: 0 Oracle invocations, 0 ETB attempts, 0 retries, 0 listener queries, 0 endpoint or port probes, 0 OpenCode starts or restarts, 0 HTTP requests, 0 provider or model calls, 0 claim creations, alterations or deletions, 0 budget consumptions or resets, 0 evidence/manifest/result creations or modifications, 0 raw-result mutations, 0 runtime cleanups, 0 ACL changes, 0 Path-D modifications, 0 config mutations and 0 source/test/dependency/version changes.  **Exact next stage:** `THIRD-PARTY READ-ONLY INDEPENDENT CONFIRMATION OF PATH-E POST-DISPOSITION GOVERNANCE RECONCILIATION` (read-only; creates no new effectivity dependency and, if it approves, no additional correction-record commit is required), after which the Owner's separate, still-deferred decision between declaring Path-E lineage closure and opening a new successor ETB lineage may be taken in its own round.  Process disclosure: because residual ACL restrictions on `docs` and `docs\v0.3` deny ordinary sandboxed writes, the status-surface writes of this governance-only round used harness escalation; escalation is a mechanical path that changes no content, creates no authority and has no operational effect.  This round makes **no** execution attempt and takes **no** operational action.  No tag, no release and no push occurred.

**PATH-F / ORACLE-PATHF — NEW ETB LINEAGE EXECUTION-ORACLE DESIGN CANDIDATE (design and governance only; nothing executed, no budget created or consumed, no claim created, no runtime namespace occupied, no Path-E artifact modified, no Path-D artifact modified).**  **OWNER DECISION = OPEN A NEW ETB LINEAGE**; `PREDECESSOR LINEAGE = PATH E`; `NEW LINEAGE = PATH F — NEW ETB ATTEMPT`; `NEW EXECUTION ORACLE = Oracle-PathF`; `OWNER NAMING DECISION = PATH-F / Oracle-PathF`; canonical lineage token `PATH_F`; canonical oracle token `ORACLE_PATH_F`.  **This is a NEW lineage and explicitly NOT** a Path-E retry, a Path-E continuation, a Path-E budget reset, a Path-E claim reuse, a Path-E repair, a Path-D retry, `Recovery-R3` unless separately and explicitly defined, `Oracle-PathE` v2, or an Oracle-PathD reuse; historical naming exclusions remain historical and preserved, and none of those identifiers is used as an active oracle identity.  **Path-E terminal state preserved unchanged:** `RAW PATH-E ORACLE OBSERVATION = ETB_UNSATISFIED`; `RAW PATH-E RESULT PROMOTION ELIGIBILITY = REJECTED / BLOCKED`; `PATH-E ETB SEMANTIC RESULT = NONE`; `PATH-E AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `PATH-E ETB ATTEMPT = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `ORACLE-PATHE INVOCATIONS = 1 OF 1 / MAXIMUM REACHED`; `PATH-E RETRY AUTHORITY = NONE`; `PATH-E RUNTIME NAMESPACE = 11 PATHS` and `PATH-E RUNTIME OCCUPANCY = 6 / 11`; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`; `PATH-D = EXHAUSTED / CLOSED / IMMUTABLE` with zero Path-D reuse, zero reopen, zero repair and zero rerun.  **PATH-E LINEAGE CLOSURE DECLARED BY THIS ROUND (precedent-derived vocabulary):** `PATH-E LINEAGE = EXHAUSTED / CLOSED` — Path E is not reopened, not repaired and not rerun; closure is a governance statement about the lineage and **not** an ETB semantic result, it does not promote the raw Path-E observation, does not alter `PATH-E ETB SEMANTIC RESULT = NONE` and creates no retry authority; the three-term `EXHAUSTED / CLOSED / IMMUTABLE` form is deliberately not used here because the directly governing predecessor precedent (`3b085dae`, `docs(v03e): define Path-E execution oracle candidate`) declares predecessor closure at this stage in the two-term form.  **Design motivation (lessons carried forward, NOT repaired in any frozen artifact):** `ORACLE-PATHD IMPLEMENTATION DEFECT = YES / ACCEPTED / NOT REPAIRED` — `Get-FileHash` used unprotected at predecessor lines 117/118 while its availability was only checked at line 189; Path-E operational lessons `L1` unauthorized pre-consumption re-attempt after a claim-create failure, `L2` unauthorized access-control-list mutation during the operational round (`ACL STATE = NOT NORMALIZED`; `ACL RESTORATION = NOT AUTHORIZED BY THAT ROUND`; rollback scripts `NOT AUTHORITY`; semantic effect `NON-SEMANTIC`), `L3` cross-document provenance wording tension between the authorization artifact and the accepted Oracle specification, `L4` runtime occupancy reported `2 / 11` against actual `6 / 11` (reporting-only), `L5` escalated file-access mode (nonblocking process variance).  **Normative correction preserved:** `NO REQUIRED COMMAND MAY BE USED BEFORE ITS REQUIRED-AVAILABILITY CONDITION HAS BEEN SAFELY ESTABLISHED`, satisfied by never calling `Get-FileHash` at all.  **Candidate identity:** spec `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.md` (733 lines, `34308` bytes, SHA-256 `b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5`) and executable `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.ps1` (894 lines, `49704` bytes, ASCII-only `MAXBYTE = 125`, no BOM, `CR = 0`, LF-only, one terminal LF, parser errors `0`, SHA-256 `4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0`); the executable is covered by an **exact-path** `.gitattributes` LF rule (`docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.ps1 text eol=lf`; no wildcard rule added, no existing rule modified) and the spec by the existing `*.md text eol=lf` rule.  **Bootstrap safety model (step 0 before every other stage):** assumed primitives are PowerShell language constructs plus `System.*` type literals and static .NET members of the already-loaded runtime (`System.IO.Path`, `System.IO.File`, `System.IO.Directory`, `System.IO.FileStream`, `System.IO.FileMode`, `System.IO.FileAccess`, `System.IO.FileShare`, `System.Text.StringBuilder`, `System.Text.UTF8Encoding`, `System.Text.Encoding`, `System.Guid`, `System.IntPtr`, `System.Security.Cryptography.SHA256`, `System.DateTimeOffset`, `System.Console`, `System.Globalization.CultureInfo`, `System.Environment`), deliberately replacing `Split-Path` / `Set-Location` / `Get-Content` / `Test-Path` with their .NET equivalents; every other cmdlet or external executable is a **GATED FACILITY** (`python`, `Add-Type`, `Get-NetTCPConnection`, `Get-CimInstance`, `ConvertTo-Json`, `ConvertFrom-Json`) checked before its first operational use; complete `CommandAst` taxonomy coverage with **28** nodes (19 script-local function calls, 8 gated-facility calls, 1 `Get-Command` inside the wrapped availability checker), no dynamic command name, no alias and no `Invoke-*`, and the top-level `trap` guard body contains 0 command invocations; measured ordering invariant `check stage < first-use stage` (last bootstrap check `L376` < earliest gated use `L386`; `Get-NetTCPConnection` only at `L520` inside `Take-Snapshot` `L512-640`); exit sites `exit 4` `L151`, `exit 2` `L691`, `exit 3` `L882`, `exit 0` `L894`.  **NEW IN PATH-F — step 1.5 PRE-PUBLICATION WRITE-VIABILITY GATE (normative, region `L305-365`, marker `L360`):** proves, without consuming one-shot authority and without creating any governed path, that the process can create, write, read back and delete a non-reserved probe file `.path-f-write-viability-probe-<guid>.tmp` in `docs/v0.3/evidence` and in `docs/v0.3`, using the file-access mode that is ALREADY established; .NET-only, not a gated facility, runs before the config read, before every target probe and before any publication step; on any failure it fails closed — `HARNESS_INVALID`, terminal stage `write_viability:<directory>`, listener probe outcome `NOT_REACHED`, exit `2`, no governed path created, no retry, no permission change, un-deletable residue reported on the marker line `ORACLE_PATH_F_WRITE_VIABILITY ok=... stage=... residue=...`; it creates no claim, consumes no budget and records `acl_mutation_attempted = false` and `acl_commands_used = 0`.  **ACL and environment policy (normative):** `icacls` / `Set-Acl` / `Get-Acl` command counts `0`; no access-control list is ever read, modified, restored, normalized or repaired by the oracle; an insufficient permission mode fails closed at the gate; `ACL STATE = NOT NORMALIZED` unchanged by this round; `ACL RESTORATION / NORMALIZATION = OUT OF SCOPE` and requires separate Owner authorization; rollback scripts `NOT AUTHORITY`; the only environment interaction is the process-scoped `PYTHONPATH` value required by the config reader, set immediately before that subprocess and restored in a `finally` block before any irreversible step.  **Sandbox / file-access mode policy (normative):** the required mode must be established BEFORE the gate; the gate observes and never escalates; a future authorization record must state the required mode and must not create escalation authority; escalation after the irreversible sequence begins is forbidden; the Path-E escalated-mode observation grants nothing.  **Provenance model (normative, stated once in spec section 19):** `MODEL_2_EXTERNAL_LINEAGE_BINDING`; content provenance is owned by the Oracle-PathF specification, which reserves `oracle_path_f_commit`, `oracle_path_f_spec_sha256` and `oracle_path_f_script_sha256` as `UNKNOWN` — never inferred, defaulted or fabricated; lineage binding is owned externally by the future Path-F execution-authorization record and the Path-F claim artifacts, which carry the frozen Path-F values verifiably from the repository; the two ownerships must never contradict each other and a future authorization must not require the evidence artifact to record values the specification reserves as `UNKNOWN` — the design-time elimination of lesson `L3`; runtime self-identity observations are recorded under distinct field names and are not provenance; the historical original ETB oracle identity (`1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc` / `01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921`) is recorded for continuity only, is never an active oracle identity and never substitutes for Path-F provenance, and no Path-D, Oracle-R2, Recovery-R1, Recovery-R2 or D1 identity is substituted; published evidence is never rewritten after the fact.  **Runtime namespace (design only; nothing created):** exactly 11 reserved Path-F paths (`docs/v0.3/evidence/ETB_PATH_F_AUTHORIZATION_USE.claim` and `.tmp`, `docs/v0.3/evidence/ETB_PATH_F_ATTEMPT_USE.claim` and `.tmp`, the `docs/v0.3/evidence/etb-execution-path-f/` directory, `ETB_EVIDENCE.json` and `.tmp`, `MANIFEST.sha256` and `.tmp` inside it, and `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_RESULT_PATH_F.md` and `.tmp`), with occupancy counted by path exactly as defined so that lesson `L4` cannot recur; `PATH-F RUNTIME NAMESPACE OCCUPANCY = 0 / 11`.  **One-shot budget model (design only):** `PATH-F AUTHORIZATION-USE BUDGET`, `PATH-F ETB-ATTEMPT BUDGET` and `ORACLE-PATHF INVOCATION BUDGET` are all `NOT CREATED / NOT AVAILABLE FOR CONSUMPTION / NOT AUTHORIZED`; each future budget is `1 OF 1`, its exact irreversible consumption event is the successful `[System.IO.FileMode]::CreateNew` of the corresponding governed TEMP claim, after which it is `SPENT / IRREVERSIBLE / NOT REUSABLE`; a `CreateNew` that fails before creation does not consume the budget but terminates the round fail-closed — no retry, no permission change, no pre-consumption re-attempt authority of any kind, and any further attempt requires a new Owner decision; no Path-D or Path-E budget may be reused, reset, extended or reinterpreted.  **Result-class model:** exactly three ETB semantic classes (`ETB_SATISFIED`, `ETB_UNSATISFIED`, `HARNESS_INVALID / NO ETB SEMANTIC RESULT`), no fourth class, `UNCLASSIFIED CONTROL FAILURE` is a governance phrase and not a class; a raw Path-F result must never become authoritative in the operational session — it must pass a fresh qualifying third-party result review, then acceptance bookkeeping, then independent confirmation of that bookkeeping, and only then may promotion eligibility be evaluated; until then `RAW RESULT PROMOTION ELIGIBILITY = REJECTED / BLOCKED`.  **Exit-code contract:** exactly `0` / `2` / `3` / `4`; no new exit code is introduced — the pre-publication write-viability failure reuses exit `2`, the only exit that asserts the absence of an artifact, while exits `3` and `4` are not artifact-absence assertions and require on-disk inspection.  **Effectivity immediately after this commit:** `ORACLE-PATHF = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE`; `PATH-F EXECUTION AUTHORIZATION = NOT CREATED / NOT EFFECTIVE`; `PATH-F EXECUTION AUTHORITY = NONE`; `PATH-F CLAIM BUDGETS = NOT OPERATIONALLY AVAILABLE`; `PATH-F ETB ATTEMPT = NOT AVAILABLE`; `ORACLE-PATHF INVOCATION = NOT AUTHORIZED`; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`.  **Design self-audit (this round; not a third-party review):** `P0 = 0`, `P1 = 0`, `P2 = 0`, `P3 = 3` — P3-1 the design round required a harness file-access escalation to write under `docs/` because of the residual ACL condition (nonblocking process variance; no content effect, no authority and no ACL mutation); P3-2 the write-viability gate proves capability by writing a probe file, so a failed probe can leave a reported residue path that this design deliberately does not clean, retry or repair (fail-closed residue reporting); P3-3 the two-term predecessor-closure vocabulary `EXHAUSTED / CLOSED` is used instead of the three-term canonical form, by precedent, so that the round does not silently upgrade the Path-E lineage state.  Round counters: 0 Oracle-PathD invocations, 0 Oracle-PathE invocations, 0 Oracle-PathF invocations, 0 ETB executions, 0 ETB attempts, 0 retries, 0 listener queries, 0 endpoint or port probes, 0 OpenCode starts or restarts, 0 HTTP requests, 0 provider or model calls, 0 claim creations, alterations or deletions, 0 budget creations, consumptions or resets, 0 evidence/manifest/result creations or modifications, 0 raw-result mutations, 0 result promotions, 0 Path-E modifications, 0 Path-D modifications, 0 runtime cleanups, 0 ACL changes, 0 config mutations and 0 source/test/dependency/version changes.  Process disclosure: because residual ACL restrictions on `docs` and `docs\v0.3` deny ordinary sandboxed writes, the artifact and status-surface writes of this governance-only round used harness escalation; escalation is a mechanical path that changes no content, creates no authority and has no operational effect.  **Exact next stage:** `FRESH QUALIFYING THIRD-PARTY INDEPENDENT REVIEW OF THE ORACLE-PATHF DESIGN CANDIDATE` (read-only; acceptance bookkeeping, freeze and confirmation are NOT performed in this round, and no independent confirmation is required at the design-candidate stage).  No tag, no release and no push occurred.
**ORACLE-PATHF ACCEPTANCE BOOKKEEPING — THIRD-PARTY DESIGN REVIEW APPROVED (bookkeeping only; nothing executed, no budget consumed, no claim created, no runtime namespace occupied, no reviewed artifact modified).**  The **fresh qualifying third-party independent design review** of candidate `a5d598a05a0467eea98cd0bf16e4486cceb72c23` issued **`APPROVE V0.3 PATH-F ORACLE-PATHF DESIGN CANDIDATE — QUALIFYING THIRD-PARTY INDEPENDENT REVIEW`** with **P0 = 0, P1 = 0, P2 = 0, P3 = 3**, and recorded **`THIRD-PARTY SESSION SEPARATION = SATISFIED`**, **`REVIEWER WAS NOT THE DESIGN-CANDIDATE AUTHOR SESSION = YES`** and **`REVIEWER DID NOT PREVIOUSLY REVIEW THIS EXACT CANDIDATE = YES`** declared before any technical work; the review ran read-only (0 repository writes, 0 staging, 0 commits, 0 ACL or permission changes, 0 claims, 0 runtime publication, 0 Oracle executions, 0 listener queries, 0 endpoint probes), the Path-F executable was parsed but never executed, and no reviewed artifact byte changed after that review.  **Exact review reference:** the `m00001` qualifying-review round of the third-party review session on 2026-09-30.  Reviewed findings are bound as reviewed facts (recorded, **not** re-derived, **not** strengthened and **not** weakened here): `PATH_D_TO_PATH_E_SUCCESSOR_PRECEDENT = DETERMINATIVE`; `PATH_E_SUCCESSOR_ROUND_CLOSURE = SUPPORTED`; `PATHF_LINEAGE_DEFINITION = EXACT`; `PATHF_EFFECTIVITY_BOUNDARY = PRESERVED`; `OBJECTIVES A–O = ALL SATISFIED`; `WRITE_VIABILITY_GATE_ORDERING = PRE_CONSUMPTION`; `WRITE_VIABILITY_GATE_BUDGET_EFFECT = NON_CONSUMING`; `FAILED_VIABILITY_RESIDUE_MODEL = COHERENT_AND_FAIL_CLOSED`; `PATHF_PRECONSUMPTION_REATTEMPT_RULE = EXPLICIT_NO_REATTEMPT`; `PATHF_ACL_POLICY = DETERMINISTIC`; `PATHF_FILE_ACCESS_POLICY = DETERMINISTIC`; `PATHF_PROVENANCE_MODEL = INTERNALLY_COHERENT`; `SCRIPT_SPEC_CONFORMANCE = EXACT`; `LISTENER_TARGET_OWNERSHIP = EXCLUSIVE_AND_CLOSED`; `PATHF_RUNTIME_NAMESPACE = CLOSED`; `PATHF_CURRENT_OCCUPANCY = 0 / 11`; `PATHF_ONE_SHOT_MODEL = DETERMINISTIC`; `PATHF_RESULT_MODEL = CLOSED_AND_VALID`; `PATHF_PUBLICATION_MODEL = DETERMINISTIC_FAIL_CLOSED`; `PATHF_EXIT_CONTRACT = CLOSED`; `GITATTRIBUTES_DELTA = BOUNDED`; `GOVERNANCE_DELTA = BOUNDED`; `PREDECESSOR_INTEGRITY = PRESERVED`; `DESIGN_ONLY_BOUNDARY = PRESERVED`.  **Accepted design identity (immutable):** `oracle_path_f_design_commit` = `a5d598a05a0467eea98cd0bf16e4486cceb72c23`, tree `c4572c9e42e2ee0484e85536f3d1c7c32335f232`; human identifier `Oracle-PathF`; canonical lineage token `PATH_F`; uppercase oracle token `ORACLE_PATH_F`; spec `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.md` with committed-blob SHA-256 `b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5` (34 308 bytes; 733 lines); executable `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.ps1` with committed-blob SHA-256 `4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0` (49 704 bytes; 894 lines; ASCII-only, no BOM, LF only); output namespace `docs/v0.3/evidence/etb-execution-path-f/`; schema identity `devrelay-etb-v1-path-f`; claim lineage `PATH_F`; provenance field names `oracle_path_f_commit` / `oracle_path_f_spec_sha256` / `oracle_path_f_script_sha256`; the accepted identities are recorded here and were **never** substituted by this bookkeeping commit or by any later confirmation commit, and no candidate artifact was edited to self-populate them.  **Formal P3 dispositions (three, preserved exactly — not added to, merged, dropped or reclassified):** `AUTHOR_P3_1` = authoring-round harness file-access escalation disclosure — **NONBLOCKING / MECHANICAL AUTHORING VARIANCE / NOT A DESIGN AUTHORITY / NO DESIGN CORRECTION REQUIRED**; `AUTHOR_P3_2` = failed write-viability probe may leave an inert random-named residue outside the frozen 11-path namespace — **COHERENT AND FAIL-CLOSED / NONGOVERNED / NO BUDGET EFFECT / NO RETRY AUTHORITY / NO DESIGN CORRECTION REQUIRED**; `AUTHOR_P3_3` = two-term Path-E closure vocabulary `EXHAUSTED / CLOSED` rather than a later three-term canonicalized form — **PRECEDENT-CONFORMANT AT THIS SUCCESSOR-DESIGN STAGE / NONBLOCKING / NO SEMANTIC RESULT IMPLIED / NO DESIGN CORRECTION REQUIRED**.  **Accepted-emphasis boundary (the design artifact's own Status line is preserved, not overridden):** before confirmation `ORACLE-PATHF DESIGN REVIEW = APPROVED`, `ORACLE-PATHF DESIGN ACCEPTANCE BOOKKEEPING = RECORDED`, `ORACLE-PATHF DESIGN = CONDITIONALLY ACCEPTED / NOT YET FROZEN / NOT YET EFFECTIVE`, and the artifact-level status `DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE` recorded in the spec header and spec §21 remains the design object's own state; `CONDITIONALLY ACCEPTED` is an emphasis of the acceptance record and **does not** supersede, cancel or weaken the artifact's own recorded status, and **no** oracle state is strengthened by this round.  `ORACLE-PATHF CONFIRMATION = REQUIRED / NOT YET PERFORMED`; Oracle-PathF becomes **`ACCEPTED / FROZEN / EFFECTIVE`** only after a **separate-session** fresh third-party independent confirmation of **this** bookkeeping commit; acceptance bookkeeping alone establishes none of those three states.  **Lineage and ancestors bound unchanged:** `NEW ETB LINEAGE = PATH F — NEW ETB ATTEMPT` with oracle `Oracle-PathF`; original oracle `oracle_commit` = `1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc`, `oracle_sha256` = `01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921`; `PATH-E LINEAGE = EXHAUSTED / CLOSED`; `PATH-E RAW RESULT = BLOCKED / NON-PROMOTABLE`; `PATH-E ETB SEMANTIC RESULT = NONE`; `PATH-E AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `PATH-E ETB ATTEMPT = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `ORACLE-PATHE INVOCATIONS = 1 OF 1 / MAXIMUM REACHED`; `PATH-E RETRY AUTHORITY = NONE`; `PATH-E NAMESPACE OCCUPANCY = 6 / 11` preserved and byte-unchanged; `PATH-D = EXHAUSTED / CLOSED / IMMUTABLE`; the frozen Path-E oracle identity `78fc6f3668aad9fae112edff0fa7deadd4ea1ff8eb7c64d1a7d2edf7196a425b` / `c08c626cbd859003c3f2a148e4f137f053aef0ccc8cadfd6f4d6bb2a1271badb` and the frozen Path-E authorization identity `01d8dc6806e622cb361f47abee178e5beeddb8f95199ff21362938312a299d06` were **re-hashed and confirmed unchanged before this round's mutation**.  **Design acceptance creates no execution authority (unchanged and explicitly preserved):** `PATH-F EXECUTION AUTHORIZATION = NOT CREATED`; `PATH-F EXECUTION AUTHORITY = NONE`; `PATH-F AUTHORIZATION-USE BUDGET = NOT CREATED / NOT AVAILABLE FOR CONSUMPTION`; `PATH-F ETB-ATTEMPT BUDGET = NOT CREATED / NOT AVAILABLE FOR CONSUMPTION`; `ORACLE-PATHF INVOCATION = NOT AUTHORIZED`; `PATH-F CLAIMS = ABSENT`; `PATH-F RUNTIME NAMESPACE = CLOSED`; `PATH-F RUNTIME NAMESPACE OCCUPANCY = 0 / 11`; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`.  **Scope discipline:** this acceptance-bookkeeping round performed **0** oracle executions, **0** ETB executions, **0** listener queries, **0** `Get-NetTCPConnection` calls, **0** claim creations, **0** budget creations or consumptions, **0** evidence/manifest/result creations, **0** config mutations, **0** HTTP, **0** provider/model calls, **0** reviewed-artifact mutations, **0** ACL or permission changes, **0** Path-E or Path-D artifact mutations, **0** Path-E or Path-D cleanups, and **0** history rewrites; its **sole** tracked delta is `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md`, with no third tracked path.  **Exact next stage:** `FRESH THIRD-PARTY INDEPENDENT CONFIRMATION OF THE ORACLE-PATHF DESIGN ACCEPTANCE BOOKKEEPING` (a separate session; third-party independent; review-only against this bookkeeping commit).  No tag, no release and no push occurred.
**ORACLE-PATHF DESIGN ACCEPTANCE BOOKKEEPING — CONFIRMATION MATERIALIZATION (governance record only; nothing executed, no claim created, no budget created or consumed, no runtime namespace occupied, no accepted, reviewed or frozen artifact mutated, no history rewritten).**  This is a **governance-only confirmation-materialization round**: it does **not** retry the ETB, does **not** decide, design or create any execution authorization, does **not** re-run or re-authorize Oracle-PathF, Oracle-PathE, Oracle-PathD or any predecessor oracle, does **not** perform a second design acceptance or a second acceptance bookkeeping, does **not** produce a new oracle design, does **not** consume any claim or budget, and performs **no** operational action.  **Recovered materialization precedent (structure determined by existing precedent, not invented):** the DevRelay bookkeeping-structure contract frozen by the accepted Recovery-R2 authorization (`PRE-1`, §11.4, §11.7) requires a governed state transition to become a repository-verifiable fact through **exactly ONE single-parent child commit whose sole tracked delta against its parent is `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md` and NO third tracked path**; the directly governing materialization precedent for Path-D is `c1d7bd38be16ee7807c98044cdd8f17d83e97729` (**`docs(v03e): record Path-D authorization confirmation`**; sole parent `a7e3cccf5fa50a127ce92c2ed3529da1e926d5ed`, tree `0ced40713c028391df0b685a5f8a93d2f5e29768`, 2 files changed / 3 insertions / 1 deletion) and the materialization analogue closest to this object is `367aca3f61e6387940deb976d0302ebc7d8b07c4` (**`docs(v03e): record Oracle-PathE design acceptance bookkeeping confirmation`**; sole parent `302dd74aa9f22640eaacb34bfbbc96de93dbaa9b`, tree `922d0b93d1e14cfc82d48de1d69ca23c1ce5ddb4`, 2 files changed / 4 insertions / 1 deletion); the two-file bookkeeping-shape precedent is `9b17912…`, itself single-parent with exactly that two-file delta.  **Precedent classification: `ORACLE_PATHF_CONFIRMATION_MATERIALIZATION_PRECEDENT = DETERMINATIVE`** — the materialization commit shape, the subject family `docs(v03e): record <lineage> <object> confirmation`, the two-path mutation surface, the effectivity transition and the anti-recursion rule are all fixed by that precedent; **no new structure was invented, no confirmation artifact was created and no third tracked path exists**.  The recovered precedent verb for this object is `record` (not `accept`, not `supersede`, not `materialize`), giving the mechanically strongest precedent-supported subject **`docs(v03e): record Oracle-PathF design acceptance bookkeeping confirmation`** by direct substitution into the `367aca3` analogue, which is **not** an acceptance subject and does **not** imply a second acceptance-bookkeeping event.  **EXPLICIT OWNER MATERIALIZATION AUTHORITY (repository-recorded, closing the historical authority gap):** the Owner explicitly authorized **exactly one** tracked Oracle-PathF design-confirmation materialization round, naming and permitting the materialization itself — creation of exactly one local confirmation-materialization successor commit; mutation of exactly the precedent-supported governance/status surfaces; repository materialization of the already-completed independent confirmation; and transition of the accepted Oracle-PathF design to the exact precedent-supported post-materialization effectivity state.  The Owner did **not** authorize execution-authorization design in this round, Path-F execution, claim creation, budget creation, Oracle invocation, listener query, endpoint probe, runtime publication, ACL mutation or restoration, Path-E or Path-D mutation, result promotion, push, tag or release.  **HISTORICAL AUTHORITY GAP NOT REPEATED (explicit):** the Path-E precedent `367aca3f61e6387940deb976d0302ebc7d8b07c4` recorded the Oracle-PathE design acceptance bookkeeping confirmation whose authorization provenance was **not** repository-verifiable, because the design/build round created the confirmation-record commit that the original round text did not explicitly name; that produced a `P2` process finding and the gap later required the successor Owner-ratification record `d921dc90b4fd08dd7c8e28127d1bafe8d008d966` (`OWNER RATIFICATION = 367ACA3 CONFIRMATION-MATERIALIZATION COMMIT RATIFIED AS-IS`; `REPOSITORY-PROVENANCE GAP = CLOSED BY THIS SUCCESSOR RATIFICATION RECORD`).  **That history is NOT repeated for Path-F:** the materialization is named and authorized explicitly in the current round text (`EXPLICIT OWNER MATERIALIZATION AUTHORITY`), so this materialization's authorization provenance **is** repository-verifiable and **no successor ratification record is required** for it.  **ANTI-RECURSION (materialized explicitly):** `DESIGN ACCEPTANCE CONFIRMATION RECURSION = NONE`; this commit is the **single** tracked materialization of the already-completed independent confirmation; it does **not** require confirmation-of-confirmation, materialization-of-materialization or ratification-of-materialization, because the explicit Owner authorization is correctly recorded here; it spawns **no** further record commit and **no** recursive lifecycle and creates **no** additional effectivity dependency — any follow-up read-only verification of this closure is a **verification of an existing record, not a new acceptance or effectivity event**.  **The fresh independent confirmation materialized as a repository-verifiable fact:** the confirmation of the Oracle-PathF design acceptance bookkeeping `7ad12d1d0b9727548b271981116267f76c362f48` — completed in the immediately preceding round as a **review-only event with no commit** — is hereby recorded: `CONFIRMATION VERDICT = APPROVE V0.3 PATH-F ORACLE-PATHF DESIGN ACCEPTANCE BOOKKEEPING — THIRD-PARTY INDEPENDENT CONFIRMATION`; `CONFIRMED BOOKKEEPING COMMIT = 7ad12d1d0b9727548b271981116267f76c362f48`; `CONFIRMED BOOKKEEPING TREE = 074b703dc6512b78ebd8381aa4147a3a96be2deb`; `THIRD-PARTY PATH-F DESIGN-ACCEPTANCE CONFIRMER SESSION SEPARATION = SATISFIED`; `CONFIRMER WAS NOT THE PATH-F DESIGN-CANDIDATE AUTHOR SESSION = YES`; `CONFIRMER WAS NOT THE QUALIFYING PATH-F DESIGN-REVIEW SESSION = YES`; `CONFIRMER WAS NOT THE PATH-F DESIGN-ACCEPTANCE-BOOKKEEPING AUTHOR SESSION = YES`; `CONFIRMER DID NOT PREVIOUSLY CONFIRM THIS EXACT BOOKKEEPING OBJECT = YES`; `CONFIRMATION RESULT = P0 = 0, P1 = 0, P2 = 0, P3 = 3` (the approval bar is satisfied at `P0 = 0`, `P1 = 0`, `P2 = 0`).  **Repository-verifiable effectivity contract (frozen by this record; derivable only from Git commit topology plus tracked status-surface bytes plus frozen artifact identity, and explicitly NOT from chat history, conversation transcripts, agent memory or any other external testimony):** (1) accepted Path-F design candidate commit `oracle_path_f_design_commit = a5d598a05a0467eea98cd0bf16e4486cceb72c23`; (2) accepted Oracle-PathF specification `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.md` with committed-blob SHA-256 `b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5` (34 308 bytes; 733 lines); (3) accepted Oracle-PathF executable `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.ps1` with committed-blob SHA-256 `4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0` (49 704 bytes; 894 lines; ASCII-only, no BOM, LF only); (4) accepted design acceptance bookkeeping commit `= 7ad12d1d0b9727548b271981116267f76c362f48` with tree `074b703dc6512b78ebd8381aa4147a3a96be2deb`; (5) that bookkeeping commit's fresh third-party independent confirmation `= APPROVED` with `THIRD-PARTY PATH-F DESIGN-ACCEPTANCE CONFIRMER SESSION SEPARATION = SATISFIED`; (6) `QUALIFYING THIRD-PARTY PATH-F DESIGN REVIEW = APPROVED`; (7) `ORACLE-PATHF DESIGN ACCEPTANCE BOOKKEEPING = CONFIRMED / FROZEN`; (8) `ORACLE-PATHF DESIGN = ACCEPTED / FROZEN / EFFECTIVE`.  All four lifecycle stages now exist as tracked, mechanically checkable facts: the design candidate, the qualifying independent design review, the design acceptance bookkeeping, and the fresh independent confirmation materialized by this explicit Owner-authorized record.  **Mechanical recognition rule for a future executor (topology plus content, requiring no external testimony):** the confirmation-materialization record commit is the **single-parent** commit whose parent is exactly `7ad12d1d0b9727548b271981116267f76c362f48`, whose sole tracked delta against that parent is **exactly** `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md` (**no third tracked path**), and whose active status surfaces state `ORACLE-PATHF DESIGN = ACCEPTED / FROZEN / EFFECTIVE` bound to accepted design commit `a5d598a05a0467eea98cd0bf16e4486cceb72c23`, specification SHA-256 `b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5` and executable SHA-256 `4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0`; all of those conditions hold simultaneously and are checked mechanically.  **NO SELF-REFERENCE:** this record deliberately does **not** embed its own commit SHA and does **not** embed its own tree; the materialization commit is identified mechanically only by its **parent** (`7ad12d1d0b9727548b271981116267f76c362f48`), its **subject** (`docs(v03e): record Oracle-PathF design acceptance bookkeeping confirmation`) and its **changed-path set**; the authority it binds is the accepted design candidate and the completed qualifying confirmation, **not** itself, and the frozen artifact identity is bound to `oracle_path_f_design_commit` and **must never** be substituted by this materialization commit's SHA or by any later HEAD.  **Recorded root cause of why this record was required (not repaired by rewriting confirmed bytes):** the acceptance bookkeeping at `7ad12d1d0b9727548b271981116267f76c362f48` froze a **conditional** effectivity (`ORACLE-PATHF DESIGN = CONDITIONALLY ACCEPTED / NOT YET FROZEN / NOT YET EFFECTIVE`, becoming accepted only after the separate-session independent confirmation) and — like the Path-D and Path-E bookkeeping commits before it — froze **no explicit recording carrier** for the confirmation event itself; because the confirmation was correctly designed as a **review-only event**, it produced **no repository object**, so the satisfied condition was not repository-verifiable.  This round supplies exactly that missing repository object and **nothing more**.  **CONFIRMATION P3-1 — STALE REVIEW-DATE TOKEN (recorded accurately; nonblocking; correction recorded, history NOT rewritten):** the acceptance bookkeeping text refers to the qualifying review as occurring on `2026-09-30`, but repository topology proves the Path-F design candidate `a5d598a05a0467eea98cd0bf16e4486cceb72c23` did not yet exist on that date, so that **date token is stale / inaccurate**.  Class: `REPORTING / PROVENANCE-DATE INACCURACY / NONBLOCKING`.  Required materialization treatment, performed exactly: the prior date token is **explicitly identified as stale / inaccurate**; the history of `7ad12d1d0b9727548b271981116267f76c362f48` is **NOT rewritten and NOT deleted** and its bytes remain immutable; **this successor materialization supersedes that date token for governance interpretation**; the qualifying review is bound by **repository-verifiable identifiers** instead of by any calendar date — design commit `a5d598a05a0467eea98cd0bf16e4486cceb72c23`, spec SHA-256 `b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5`, script SHA-256 `4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0`, verdict `APPROVE V0.3 PATH-F ORACLE-PATHF DESIGN CANDIDATE — QUALIFYING THIRD-PARTY INDEPENDENT REVIEW`, severity `P0 = 0 / P1 = 0 / P2 = 0 / P3 = 3`, and the declared independence; and **no replacement calendar date is invented** anywhere in this record, because no exact source exists — the correct date may be recorded only in a future round that recovers an exact source for it.  **CONFIRMATION P3-2 — PROCESS-DISCLOSURE COMPLETENESS (recorded accurately; nonblocking):** the bookkeeping status surfaces did not carry the authoring-round harness escalation disclosure that was present in the preceding governance rounds.  Class: `DOCUMENTATION COMPLETENESS / NONBLOCKING`.  Materialized disclosure: the bookkeeping writes, staging and commit used **harness escalation** because ordinary sandbox and index-lock writes were denied; this was **mechanical only**; **no ACL mutation occurred**; **no authority was created**; and **no design or content identity changed**.  **CONFIRMATION P3-3 — NEXT-STAGE NAMING BREADTH (resolved by this round; nonblocking):** the bookkeeping named only the review-only confirmation and not the subsequent tracked materialization step.  Class: `PRECEDENT-CONFORMANT BUT INCOMPLETE LIFECYCLE NAMING / NONBLOCKING`.  This materialization round **resolves** it by explicitly recording the non-collapsed lifecycle: `review-only confirmation COMPLETED` → `tracked materialization REQUIRED` → `this Owner-authorized materialization RECORDS it` → `effectivity FOLLOWS`.  **None of the three confirmation P3 observations is carried as a `P2` or blocking defect**, no observation was "fixed" by rewriting a reviewed or confirmed byte, and the three are recorded as `NONBLOCKING / CORRECTED-BY-SUCCESSOR-RECORD / NO DESIGN CORRECTION REQUIRED`.  **Artifact integrity before and after mutation (verified):** the Oracle-PathF specification `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.md` remains `34 308` bytes with SHA-256 `b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5`, and the executable `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.ps1` remains `49 704` bytes with SHA-256 `4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0`; both were re-measured **before and after** this round's mutation, both are byte-unchanged, and neither was edited to self-populate any identity.  **Design effectivity creates NO execution authority (explicit and preserved):** `PATH-F EXECUTION AUTHORIZATION = NOT CREATED`; `PATH-F EXECUTION AUTHORITY = NONE`; `PATH-F AUTHORIZATION-USE BUDGET = NOT CREATED / NOT AVAILABLE FOR CONSUMPTION`; `PATH-F ETB-ATTEMPT BUDGET = NOT CREATED / NOT AVAILABLE FOR CONSUMPTION`; `ORACLE-PATHF INVOCATION = NOT AUTHORIZED`; `PATH-F CLAIMS = ABSENT`; `PATH-F RUNTIME NAMESPACE = CLOSED`; `PATH-F RUNTIME NAMESPACE OCCUPANCY = 0 / 11`; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`.  **Design effectivity MUST NOT be interpreted as execution authority**; it is a design-lifecycle state only and grants nothing operational.  **Predecessor boundary preserved unchanged:** `PATH-E LINEAGE = EXHAUSTED / CLOSED`; `PATH-E RAW RESULT = BLOCKED / NON-PROMOTABLE`; `PATH-E ETB SEMANTIC RESULT = NONE`; `PATH-E AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `PATH-E ETB ATTEMPT = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `ORACLE-PATHE INVOCATIONS = 1 OF 1 / MAXIMUM REACHED`; `PATH-E RETRY AUTHORITY = NONE`; `PATH-E NAMESPACE OCCUPANCY = 6 / 11` preserved; `PATH-D = EXHAUSTED / CLOSED / IMMUTABLE`; `PATH-D AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `PATH-D ETB ATTEMPT = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `ORACLE-PATHD INVOCATIONS = 1 OF 1 / MAXIMUM REACHED`; `PATH-D ETB SEMANTIC RESULT = NONE`; `PATH-D RETRY AUTHORITY = NONE`; no predecessor was reused, mutated, reopened, repaired or rerun.  **Result authority preserved:** `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED`; a confirmation-materialization record creates **no** ETB observation, **no** semantic result and **no** replacement authority, and any future Oracle-PathF observation must still pass **independent result review → result bookkeeping → independent bookkeeping confirmation** before it may replace the authoritative result.  **Scope discipline:** this materialization round performed **0** oracle executions, **0** ETB executions or attempts, **0** retries, **0** listener queries, **0** `Get-NetTCPConnection` calls, **0** endpoint or port probes, **0** HTTP requests, **0** provider or model calls, **0** claim creations, **0** budget creations, consumptions or resets, **0** evidence/manifest/result creations, **0** runtime publications, **0** ACL changes or restorations, **0** config mutations, **0** result promotions, **0** reviewed-artifact mutations, **0** Path-E or Path-D artifact mutations, **0** Path-E cleanups, **0** history rewrites, and **0** runtime/test/dependency/version changes; its **sole** tracked delta is `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md`, with no third tracked path.  **Materialization self-audit (author self-audit only; no further independent confirmation is created by this round, because the recovered precedent does not require a read-only verification of a materialization record):** `P0 = 0`, `P1 = 0`, `P2 = 0`, `P3 = 3`; the **P3-1** stale review-date token is recorded, corrected by supersession and deliberately not rewritten; the **P3-2** missing authoring-round escalation disclosure is supplied here; and the **P3-3** incomplete next-stage naming is resolved by this record's explicit lifecycle statement.  **Exact next stage:** `PATH-F ETB EXECUTION-AUTHORIZATION DESIGN` — the exact Path-E/Path-D precedent-supported next stage for a lineage whose design is `ACCEPTED / FROZEN / EFFECTIVE`; it is **NOT** begun in this round, and no authorization artifact, budget or claim is created here.  No tag, no release and no push occurred.
**PATH-F / ORACLE-PATHF — ONE-SHOT ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE (design and governance only; nothing executed, no budget created or consumed, no claim created, no runtime namespace occupied, no Path-F runtime artifact created, no accepted artifact modified, no ACL read or mutated, Path-E not reopened, Path-D not reopened).** OWNER DECISION = BEGIN PATH-F ETB EXECUTION-AUTHORIZATION DESIGN / ONE BOUNDED DESIGN ROUND BASELINE (verified exact before mutation): - HEAD = `1d06f2857840b9f4096bbedc156e3ac4c9eaddec`; parent = `7ad12d1d0b9727548b271981116267f76c362f48`; tree = `28118b135377277de5404f17c92779a928b71b32`; subject = `docs(v03e): record Oracle-PathF design acceptance bookkeeping confirmation`; branch = `v0.3-e-recovery-reconciliation` - tracked worktree = clean; staged = 0; untracked porcelain = 19; Path-F namespace = 0 / 11; Path-E namespace = 6 / 11 - `ORACLE-PATHF DESIGN = ACCEPTED / FROZEN / EFFECTIVE`; `ORACLE-PATHF DESIGN ACCEPTANCE BOOKKEEPING = 7ad12d1d0b9727548b271981116267f76c362f48`; `ORACLE-PATHF DESIGN ACCEPTANCE CONFIRMATION MATERIALIZATION = 1d06f2857840b9f4096bbedc156e3ac4c9eaddec`; `ORACLE-PATHF DESIGN CONFIRMATION RECURSION = NONE` - frozen Oracle-PathF design identity preserved unchanged: `oracle_path_f_commit = a5d598a05a0467eea98cd0bf16e4486cceb72c23`; `oracle_path_f_spec_sha256 = b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5`; `oracle_path_f_script_sha256 = 4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0` PRECEDENT: `PATHF_EXECUTION_AUTHORIZATION_DESIGN_PRECEDENT = DETERMINATIVE`. Recovered from `29bf27fc2f76d415eb9c07d890f50b665aca6846` (Path-D ETB authorization design candidate: three paths — `2 0 CHANGELOG.md`, `1 1 docs/v0.3/V03E_ACCEPTANCE.md`, `738 0 docs/v0.3/V03E_G0_5_PRE_ETB_PATH_D_AUTHORIZATION.md`; 741 insertions, 1 deletion), `26b183083fbbe323441283f99f3cf2c931acd6ff` (Path-E ETB authorization design candidate, same three-path shape; 772 insertions, 1 deletion), `4900625114a38a86aa03a5fa4861c5bcd9436dc5` (`fix(v03e): remediate Path-E ETB authorization design review findings`; `2 0`, `1 1`, `12 5 docs/v0.3/V03E_G0_5_PRE_ETB_PATH_E_AUTHORIZATION.md`), `48e9b66dd5aeb147795dbc57e822e6b3d38e4565` (acceptance stage: two files only, `1 1`, `1 1`, artifact not modified) and `c7ac36a8c596ae2ede8db7bce2e625f8c6ffa21c` (authorization confirmation record: two files only, `2 0`, `1 1`). The candidate shape is therefore exactly THREE tracked paths — `M CHANGELOG.md`, `M docs/v0.3/V03E_ACCEPTANCE.md` and the new authorization artifact — and, unlike the Oracle design candidates, NO .gitattributes change, because an authorization artifact is markdown covered by the repository-wide `*.md text eol=lf` rule and introduces no new executable or specification file type. DESIGN OBJECT - new tracked artifact: `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_F_AUTHORIZATION.md` = `84894` bytes / SHA-256 `c147af8714164dae8b81cafa4eb01945a3ceb8c74b36f0fc18fbd56db284c4de` / LF `1147` / CR `0` / non-ASCII bytes `469` / max byte `226` / BOM `no` / encoding UTF-8 - `PATH-F AUTHORIZATION = DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / NOT EXECUTED` - the artifact designs, and does not create, three separate one-shot authorities: the Path-F authorization-use budget (1 of 1, consumed at successful `CreateNew` of `docs/v0.3/evidence/ETB_PATH_F_AUTHORIZATION_USE.claim.tmp`), the Path-F ETB-attempt budget (1 of 1, consumed at successful `CreateNew` of `docs/v0.3/evidence/ETB_PATH_F_ATTEMPT_USE.claim.tmp`, available only after the authorization-use budget is spent in the same authorized round), and the Oracle-PathF invocation authority (maximum 1 of 1, available only after both claims exist) - claim schemas `devrelay-etb-path-f-authorization-use-v1`, `devrelay-etb-path-f-attempt-use-v1`: seven ordered fields (`schema_version`, `authorization_commit`, `authorization_sha256`, `oracle_path_f_commit`, `oracle_path_f_spec_sha256`, `oracle_path_f_script_sha256`, `state` with `state = CONSUMED`), UTF-8 without BOM, exactly one terminal LF, no timestamp/hostname/PID/operator/comment/extra field; the two schemas differ only in field 1 - frozen writer `Write-DevRelayPathFOneShotClaim`: exclusive `CreateNew` plus `FileShare::None`, `ConvertTo-Json -Depth 4 -Compress`, `Flush($true)`, byte-for-byte read-back, terminal-LF and BOM checks before publication, two-argument `System.IO.File.Move` publication with no overwrite, no deletion on any failure path, no retry and no cleanup - closed PRE-gate model `PRE-1` ... `PRE-18` = twelve preserved predecessor rows plus three Path-F-specific rows (`PRE-16` established execution/file-access mode with no ACL repair pending, `PRE-17` write-viability capacity established without consuming authority or creating a governed path, `PRE-18` non-consuming failure confers no re-attempt authority); `PRE_GATE_MODEL = CLOSED / COMPLETE` as a structural description of the candidate only, not a review verdict - Path-E `P2-1` (unsatisfiable self-identity gate) eliminated by construction: `PRE-2` binds the frozen accepted values that exist only after the acceptance/confirmation lifecycle and explicitly does not require the design candidate to contain its own future commit or SHA; the candidate carries the two explicit angle-bracket placeholders `<path_f_authorization_commit>`, `<path_f_authorization_sha256>` that no executor and no author round may substitute - Path-E `P2-2` (contradictory effectivity gate) eliminated by construction: `PRE-3` is a three-layer gate evaluated at the future operational consumption point — layer A Oracle-PathF design effectivity, layer B Path-F execution-authorization effectivity, layer C consumable state 1 of 1 available with both claims still absent and the runtime namespace still 0 / 11 — and it states explicitly that the non-effective requirement applies to the design-candidate stage only and must not be required at the gate; the state block is to be read as a projection, not as a current claim. Layer B does not contradict layer C: accepted, frozen and effective describes the authorization instrument, available for consumption describes its unused budget, and consumption is a later event - provenance compatibility recorded: `PATHF_AUTHORIZATION_PROVENANCE_COMPATIBILITY = COHERENT`; the authorization contains no sentence requiring Oracle-generated evidence to carry frozen Path-F identities and no sentence contradicting the literal UNKNOWN that the accepted Oracle-PathF specification section 19 reserves for `oracle_path_f_commit`, `oracle_path_f_spec_sha256`, `oracle_path_f_script_sha256`; lineage binding is external — this authorization artifact, the two claims and the accepted control surfaces; no inference, defaulting, fabrication or post-hoc evidence rewriting is permitted, which closes Path-E lesson `L3` for Path-F by construction rather than by editing a frozen predecessor byte - ACL and access-mode policy closed explicitly: ACL mutation, ACL restoration/normalization, permission repair after any failed gate, sandbox/file-access escalation after the irreversible sequence begins and improvisational retry after an access failure are all FORBIDDEN for any round governed by this authorization; `icacls`, `Set-Acl`, ACL-repair and permission-normalization scripts are NOT AUTHORIZED as part of execution; if required write/file-access viability is not established before the irreversible sequence the round FAILS CLOSED with no claim consumption, no Oracle invocation, no same-round repair and no same-round retry, and a later attempt requires a new explicit Owner-governed authority lifecycle (closes Path-E lessons `L1`, `L2`, `L5`) - non-consuming-failure rule frozen without interpretation gap: a `CreateNew` failure occurring before the TEMP file is created consumes no budget and nevertheless TERMINATES the round, under the rule `NON-CONSUMING FAILURE DOES NOT MEAN RE-ATTEMPT AUTHORITY`; no hidden retry, no sleep-and-retry, no alternate port, no alternate path and no permission-change-and-retry path exists - listener and target ownership preserved: the authorization layer may verify only static artifact identity, governance and precondition state and established execution-mode capacity; listener query, ownership resolution, process identity, path canonicalization, target hashing, package identity, S0/S1 snapshot acquisition and continuity evaluation remain EXCLUSIVELY owned by the frozen Oracle-PathF executable; no target pre-probe of any kind is authorized, and a pre-Oracle probe would create an unbudgeted observation, which the result-authority model forbids - result boundary preserved: exactly three ETB semantic classes — `ETB_SATISFIED`, `ETB_UNSATISFIED`, `HARNESS_INVALID / NO ETB SEMANTIC RESULT`; no fourth class is created and none is renamed, split, merged or reordered; authorization-layer and control-layer failures are governance and control descriptors only and are never HARNESS_INVALID and never an ETB observation; the Path-D governance phrase UNCLASSIFIED CONTROL FAILURE is not resurrected as a class - runtime namespace preserved: exactly eleven reserved Path-F paths, occupancy counted by path with the output directory counting as one member; `PATH-F RUNTIME NAMESPACE = 11 PATHS`; `PATH-F RUNTIME OCCUPANCY = 0 / 11`; no twelfth governed runtime path is added, and no probe residue is a claim, an attempt or a budget-consumption event - promotion pipeline preserved: a future raw Path-F observation remains non-authoritative until independent result review, result bookkeeping and independent confirmation of that bookkeeping complete; until then `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED` and `RAW RESULT PROMOTION ELIGIBILITY = REJECTED / BLOCKED` - authorization lifecycle further stages named but NOT performed and NOT begun in this commit: (1) fresh qualifying third-party independent review of this design candidate in a different agent/session; (2) authorization acceptance bookkeeping in exactly one single-parent two-file commit; (3) fresh independent confirmation of that bookkeeping in a different agent/session; (4) materialization of that confirmation as a repository-verifiable record commit; only after all four does PATH-F AUTHORIZATION become ACCEPTED / FROZEN / EFFECTIVE with EXECUTION AUTHORITY = GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY ARTIFACT IMMUTABILITY (verified unchanged before and after this round): - Path-F specification `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.md` = 34308 bytes / SHA-256 `b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5` / LF 733 / CR 0 / BOM absent - Path-F executable `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.ps1` = 49704 bytes / SHA-256 `4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0` / LF 894 / CR 0 / non-ASCII bytes 0 / BOM absent - `.gitattributes` not modified; no wildcard rule added; no existing rule changed; the new artifact resolves text: set and eol: lf through the repository-wide `*.md text eol=lf` rule - Path-E artifacts, Path-E claims, Path-D artifacts, Path-D claims, ACLs, source, tests, dependencies and version files not modified MUTATION SURFACE = CHANGELOG.md modified, docs/v0.3/V03E_ACCEPTANCE.md modified, the new authorization artifact added — exactly three tracked paths, no fourth path. POST-ROUND STATE (all values recorded; none of them created by this commit): - `ORACLE-PATHF DESIGN = ACCEPTED / FROZEN / EFFECTIVE` - `PATH-F AUTHORIZATION DESIGN = CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE` - `PATH-F EXECUTION AUTHORIZATION = NOT CREATED / NOT EFFECTIVE`; `PATH-F EXECUTION AUTHORITY = NONE` - `PATH-F AUTHORIZATION-USE BUDGET = NOT CREATED / NOT AVAILABLE FOR CONSUMPTION`; `PATH-F ETB-ATTEMPT BUDGET = NOT CREATED / NOT AVAILABLE FOR CONSUMPTION` - `ORACLE-PATHF INVOCATION = NOT AUTHORIZED`; `PATH-F CLAIMS = ABSENT (4 / 4)`; `PATH-F RUNTIME OCCUPANCY = 0 / 11`; `PATH-F ETB EXECUTION = NOT AUTHORIZED` - `LISTENER QUERY = NOT EXECUTED`; `TARGET PROBE = NOT EXECUTED` - `ACL MUTATION / RESTORATION = NOT PERFORMED / NOT AUTHORIZED BY THIS ROUND`; `CURRENT ACL STATE = NOT NORMALIZED (unchanged by this round)` - `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED` - `PATH-E LINEAGE = EXHAUSTED / CLOSED`; `PATH-E RAW RESULT = BLOCKED / NON-PROMOTABLE`; `PATH-E ETB SEMANTIC RESULT = NONE`; `PATH-E RETRY AUTHORITY = NONE`; `PATH-E RUNTIME OCCUPANCY = 6 / 11` (unchanged; no cleanup, no reuse, no mutation) - `PATH-D = EXHAUSTED / CLOSED / IMMUTABLE`; `PATH-D AUTHORIZATION USE = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `PATH-D ETB ATTEMPT = 1 OF 1 / SPENT / IRREVERSIBLE / NOT REUSABLE`; `ORACLE-PATHD INVOCATIONS = 1 OF 1 / MAXIMUM REACHED`; `PATH-D ETB SEMANTIC RESULT = NONE`; `PATH-D RETRY AUTHORITY = NONE` DESIGN SELF-AUDIT (author self-audit only; NOT a review, NOT an acceptance and NOT an independent confirmation): `P0 = 0 / P1 = 0 / P2 = 0 / P3 = 1`. `P3-1` = the accepted Oracle-PathF specification section 22.1 records a byte-class table for the executable, while this authorization quotes only the SHA-256 values; the quoted values were re-measured and agree, and the byte-class table is deliberately not duplicated because it belongs to the specification and to the review stage. Class DOCUMENTATION COMPLETENESS / NONBLOCKING / NO EXECUTABLE SEMANTIC IMPACT. No P0, P1 or P2 condition was found. This authorization performs no review of itself and claims no accepted status. PROCESS DISCLOSURE: no ACL command was run and no permission was changed at any point in this round. All tracked writes, the staging of the three paths and the commit itself were performed through the harness with escalated file access because the ordinary workspace-write sandbox denied writes to the status surfaces and to repository metadata; the escalation was mechanical only and changed no design content, no artifact identity and no authority. CURRENT ACL STATE remains NOT NORMALIZED and outside tracked Git governance, exactly as before. ACTIVITY COUNTERS: Oracle-PathF executions 0; ETB executions 0; listener queries 0; endpoint probes 0; OpenCode starts 0; claims created 0; budgets created 0; budgets consumed 0; evidence, manifest and result creations 0; runtime namespace entries created 0; ACL reads, mutations and restorations 0; predecessor cleanups 0; Path-E modifications 0; Path-D modifications 0; tags 0; releases 0; pushes 0. NEXT STAGE = FRESH QUALIFYING THIRD-PARTY INDEPENDENT REVIEW OF THE PATH-F ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE, which MUST occur in a different agent/session and is NOT performed here. Nothing was executed, no budget was created or consumed, no claim was created, no runtime namespace entry was created, no accepted artifact was modified, and no ACL was read or changed. No tag, no release and no push occurred.
**PATH-F ETB EXECUTION-AUTHORIZATION ACCEPTANCE BOOKKEEPING — QUALIFYING THIRD-PARTY AUTHORIZATION DESIGN REVIEW APPROVED (design and governance only; nothing executed, no budget created or consumed, no claim created, no runtime namespace occupied, no Path-F runtime artifact created, no reviewed artifact modified, no frozen Oracle-PathF artifact modified, Path-D not reopened, Path-E not reopened).**  The fresh qualifying third-party independent review of authorization-design candidate ed112f8c5f1e35d87092d0339698a792ce0b145a (artifact docs/v0.3/V03E_G0_5_PRE_ETB_PATH_F_AUTHORIZATION.md, SHA-256 c147af8714164dae8b81cafa4eb01945a3ceb8c74b36f0fc18fbd56db284c4de, 84894 bytes, LF 1147, CR 0, no BOM, terminal LF present) was completed read-only in a different agent/session with the independence declarations recorded before any substantive inspection — THIRD-PARTY PATH-F AUTHORIZATION-DESIGN REVIEWER SESSION SEPARATION = SATISFIED, REVIEWER WAS NOT THE PATH-F AUTHORIZATION-DESIGN CANDIDATE AUTHOR SESSION = YES, REVIEWER DID NOT PREVIOUSLY REVIEW THIS EXACT AUTHORIZATION-DESIGN CANDIDATE = YES — and returned **APPROVE V0.3 PATH-F ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE — QUALIFYING THIRD-PARTY INDEPENDENT REVIEW** with severity **P0 = 0, P1 = 0, P2 = 0, P3 = 7**, so the approval bar P0 = 0 / P1 = 0 / P2 = 0 was **met**.  **Review classifications recorded exactly as the qualifying review established them:** PATHF_EXECUTION_AUTHORIZATION_DESIGN_PRECEDENT = DETERMINATIVE; PATHF_AUTHORIZATION_ARTIFACT_IDENTITY = EXACT; FROZEN_ORACLE_PATHF_BINDING = EXACT; HISTORICAL_P2_1_REPRODUCED = YES; HISTORICAL_P2_2_REPRODUCED = YES; PATHF_P2_1_SELF_IDENTITY_DEFECT = ABSENT; PATHF_P2_2_EFFECTIVITY_CONTRADICTION = ABSENT; PATHF_AUTHORIZATION_SELF_IDENTITY_MODEL = SATISFIABLE; PRE_2 = SATISFIABLE_AND_EXTERNALLY_BOUND; PRE_3 = LOGICALLY_CONSISTENT; PATHF_AUTHORIZATION_PROVENANCE_COMPATIBILITY = COHERENT; PRE-1 ... PRE-18 = ALL SATISFIED-BY-DESIGN; PRE_GATE_MODEL = CLOSED_AND_SATISFIABLE; PRE_17_WRITE_VIABILITY_CAPACITY = COHERENT; PRE_18_NO_REATTEMPT = EXPLICIT_AND_CLOSED; PATHF_AUTHORIZATION_ACL_POLICY = DETERMINISTIC; PATHF_AUTHORIZATION_FILE_ACCESS_POLICY = DETERMINISTIC; PATHF_AUTHORIZATION_BUDGET_MODEL = DETERMINISTIC; PATHF_CLAIM_MODEL = DETERMINISTIC; PATHF_CLAIM_WRITER_MODEL = CLOSED; LISTENER_TARGET_OWNERSHIP = EXCLUSIVE_TO_ORACLE_PATHF; PATHF_AUTHORIZATION_RESULT_BOUNDARY = CLOSED; RAW_RESULT_PROMOTION_BOUNDARY = PRESERVED; PATHF_NAMESPACE_COMPATIBILITY = EXACT; PATHF_AUTHORIZATION_EFFECTIVITY_BOUNDARY = PRESERVED; PATHF_AUTHORIZATION_LIFECYCLE = COHERENT; AUTHORIZATION_DESIGN_PROCESS_VARIANCE = NONBLOCKING; AUTHORIZATION_DESIGN_GOVERNANCE_DELTA = BOUNDED; PREDECESSOR_INTEGRITY = PRESERVED; DESIGN_ONLY_BOUNDARY = PRESERVED.  **Formal review severity is recorded exactly as the qualifying review classified it:** P0 = 0 / P1 = 0 / P2 = 0 / P3 = 7, where the seven formal P3 findings are P3-A three internal references cite a non-existent section 26 where the intended target is section 20 (class CROSS-REFERENCE PRECISION / NONBLOCKING), P3-B wording says twelve preserved rows plus three although the predecessor family is PRE-1 ... PRE-15 and Path-F adds PRE-16 ... PRE-18 (class DOCUMENTATION COUNT DESCRIPTION / NONBLOCKING), P3-C section 5.1 points to sections 13/25 for the accepted control surfaces although PRE-2 and the lifecycle define the actual tracked governance surfaces (class CROSS-REFERENCE PRECISION / NONBLOCKING), P3-D PRE-3 points to section 24 for current stage state where section 23 is the live-state block (class CROSS-REFERENCE PRECISION / NONBLOCKING), P3-E section 19.4 points to section 21.4 for the provenance audit result while the actual result is in sections 3.3 / 19.4 (class CROSS-REFERENCE PRECISION / NONBLOCKING), P3-F section 15 cites the result-authority model as section 18 where the correct model is section 17.4 (class CROSS-REFERENCE PRECISION / NONBLOCKING), and P3-G PRE-17 wording could be misread as requiring an empirical authorization-layer write probe while section 6.2 forbids that probe (class WORDING PRECISION / NONBLOCKING / NO UNSATISFIABLE REQUIREMENT / NO OWNERSHIP VIOLATION); **no P3 was repaired, reclassified or promoted, and no additional finding was invented.**  **Accepted authorization-design identity frozen by this bookkeeping (immutable):** path_f_authorization_commit = ed112f8c5f1e35d87092d0339698a792ce0b145a — the independently approved authorization-design commit, **not** this acceptance-bookkeeping commit, **not** the later confirmation record and **not** any later operational HEAD; path_f_authorization_sha256 = c147af8714164dae8b81cafa4eb01945a3ceb8c74b36f0fc18fbd56db284c4de; artifact bytes 84894, LF 1147, CR 0, BOM absent, terminal LF present, UTF-8 and LF-only, worktree byte-identical to the committed blob 0a92c033e079ebdc84df33a7d0fa915092f8a16e; the reviewed artifact is **not** rewritten, not edited and not corrected by this round, so its identity remains exactly the reviewed identity, and any future editorial cleanup would require its own successor design decision and would create a different authorization-design identity.  **Oracle-PathF frozen provenance re-verified and preserved:** oracle_path_f_design_commit = a5d598a05a0467eea98cd0bf16e4486cceb72c23, oracle_path_f_spec_sha256 = b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5 (34308 bytes), oracle_path_f_script_sha256 = 4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0 (49704 bytes), ORACLE-PATHF DESIGN = ACCEPTED / FROZEN / EFFECTIVE, ORACLE-PATHF EXECUTION = NOT AUTHORIZED; both Oracle-PathF artifacts are byte-identical at the accepted design commit, at the previous HEAD, in the index and in the worktree, and neither was modified by this round.  **Two-stage effectivity (NOT collapsed):** this commit is **acceptance-bookkeeping provenance only**; it replaces neither frozen authorization value and it does not freeze or effectuate the authorization.  The authorization becomes ACCEPTED / FROZEN / EFFECTIVE **only** after a **fresh independent confirmation of THIS bookkeeping commit** performed in a different agent/session from this acceptance-bookkeeping-author session, followed by the precedent-required tracked materialization of that confirmation; immediately after this bookkeeping the state is PATH-F ETB EXECUTION AUTHORIZATION = CONDITIONALLY ACCEPTED / NOT YET FROZEN / NOT YET EFFECTIVE (the established repository form for the acceptance-bookkeeping stage, recovered from the Path-D precedent), PATH-F AUTHORIZATION DESIGN = CONDITIONALLY ACCEPTED / NOT YET FROZEN / NOT YET EFFECTIVE, PATH-F AUTHORIZATION DESIGN REVIEW = APPROVED, PATH-F AUTHORIZATION DESIGN ACCEPTANCE BOOKKEEPING = RECORDED, PATH-F AUTHORIZATION CONFIRMATION = REQUIRED / NOT YET PERFORMED.  **Execution remains closed until confirmation:** PATH-F EXECUTION AUTHORITY = NONE; PATH-F AUTHORIZATION USE = NOT AVAILABLE FOR CONSUMPTION; PATH-F ETB ATTEMPT = NOT AVAILABLE FOR CONSUMPTION; PATH-F AUTHORIZATION-USE BUDGET = NOT CREATED / NOT AVAILABLE FOR CONSUMPTION; PATH-F ETB-ATTEMPT BUDGET = NOT CREATED / NOT AVAILABLE FOR CONSUMPTION; ORACLE-PATHF INVOCATION = NOT AUTHORIZED; PATH-F CLAIMS = ABSENT (4 / 4); PATH-F RUNTIME OCCUPANCY = 0 / 11; the claim schemas devrelay-etb-path-f-authorization-use-v1 and devrelay-etb-path-f-attempt-use-v1 and the frozen writer Write-DevRelayPathFOneShotClaim are unchanged; no claim TEMP or FINAL file was created; no evidence, manifest or result was created; no listener was queried; no target or endpoint was probed; and no ACL was read, changed, restored or normalized.  **PRE-2 / PRE-3 acceptance binding:** the qualifying review independently confirmed PRE_2 = SATISFIABLE_AND_EXTERNALLY_BOUND and PRE_3 = LOGICALLY_CONSISTENT with PATHF_P2_1_SELF_IDENTITY_DEFECT = ABSENT and PATHF_P2_2_EFFECTIVITY_CONTRADICTION = ABSENT; this bookkeeping commit is one of the accepted control surfaces that will later carry the two frozen values externally, but it does **not** make PRE-2 operationally usable and it does **not** satisfy PRE-2 or PRE-3 for any operational round, because the complete acceptance / confirmation / materialization lifecycle has not yet reached effectivity; the candidate artifact is not required to be rewritten and was not rewritten.  **Provenance boundary preserved:** MODEL_2_EXTERNAL_LINEAGE_BINDING is preserved; executor-owned claims will later bind the frozen lineage identities externally; Oracle-generated evidence remains governed by the frozen Oracle-PathF specification; no Oracle-generated oracle_path_f_commit / oracle_path_f_spec_sha256 / oracle_path_f_script_sha256 field is required to cease being the literal UNKNOWN where the frozen Oracle model reserves UNKNOWN; and no post-hoc evidence rewrite is permitted or performed.  **Predecessor boundary preserved:** PATH-E LINEAGE = EXHAUSTED / CLOSED; PATH-E RAW RESULT = BLOCKED / NON-PROMOTABLE; PATH-E ETB SEMANTIC RESULT = NONE; PATH-E RETRY AUTHORITY = NONE; PATH-E RUNTIME OCCUPANCY = 6 / 11 unchanged; PATH-D = EXHAUSTED / CLOSED / IMMUTABLE with zero Path-D reuse; ORACLE-PATHF DESIGN = ACCEPTED / FROZEN / EFFECTIVE; and AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED with no ETB observation, no promotion and no authoritative-result replacement.  **Confirmation-recursion and materialization-authority rule preserved:** CONFIRMATION RECURSION = NONE, and a read-only confirmation verdict does **not** by itself become repository-verifiable effectivity where precedent requires tracked materialization — **no tracked confirmation materialization may be created without a separate, explicit Owner authorization naming that materialization round**, and the historical materialization-authority gap is not repeated by this round.  **This acceptance-bookkeeping round performed** 0 Oracle-PathF executions, 0 Oracle-PathE executions, 0 Oracle-PathD executions, 0 ETB executions, 0 listener queries, 0 Get-NetTCPConnection calls, 0 port-4096 probes, 0 localhost / 127.0.0.1 probes, 0 endpoint probes, 0 OpenCode starts/restarts, 0 HTTP / provider / model calls, 0 claim creations, 0 budget creations, 0 budget consumptions, 0 evidence / manifest / result creations, 0 Path-F runtime artifact creations, 0 Path-E or Path-D modifications, 0 frozen Oracle-PathF artifact modifications, 0 accepted-artifact mutations, 0 authorization-artifact modifications and 0 runtime / test / dependency / version changes.  **Exact next stage:** FRESH THIRD-PARTY INDEPENDENT CONFIRMATION OF THE PATH-F ETB EXECUTION-AUTHORIZATION DESIGN ACCEPTANCE BOOKKEEPING, which must run in a different agent/session from this acceptance-bookkeeping-author session — no independent confirmation, no confirmation materialization, no claim creation, no budget creation or consumption and no execution is performed in this round.  No tag, no release and no push occurred.
**PATH-F ETB EXECUTION-AUTHORIZATION CONFIRMATION MATERIALIZATION - EXPLICIT OWNER-AUTHORIZED GOVERNANCE RECORD (governance and status surfaces only; nothing executed, no claim created, no budget created or consumed, no runtime namespace occupied, no Path-F runtime artifact created, no reviewed artifact modified, no frozen Oracle-PathF artifact modified, Path-D not reopened, Path-E not reopened; no push, no tag, no release).**  This is the single tracked repository materialization of an already-completed read-only confirmation, authorized in advance by an explicit Owner order that names: the confirmed acceptance-bookkeeping commit `1de258ff8fb0e4113d2eab73e13b51e502cd20fe`; the accepted authorization-design commit `ed112f8c5f1e35d87092d0339698a792ce0b145a`; the authorization artifact `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_F_AUTHORIZATION.md` with SHA-256 `c147af8714164dae8b81cafa4eb01945a3ceb8c74b36f0fc18fbd56db284c4de`; the qualifying design-review verdict `APPROVE V0.3 PATH-F ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE - QUALIFYING THIRD-PARTY INDEPENDENT REVIEW`; the confirmation verdict `APPROVE V0.3 PATH-F ETB EXECUTION-AUTHORIZATION DESIGN ACCEPTANCE BOOKKEEPING - THIRD-PARTY INDEPENDENT CONFIRMATION`; the exact materialization mutation surface (exactly one two-file tracked status delta and no third path); the effectivity consequence (the transition to `ACCEPTED / FROZEN / EFFECTIVE`); and the anti-recursion rule.  `PATH-F AUTHORIZATION CONFIRMATION MATERIALIZATION AUTHORITY = EXPLICITLY GRANTED IN ADVANCE BY OWNER`, so no successor ratification is required and the historical Path-E materialization-authority gap is not repeated.  **Confirmation facts materialized:** `CONFIRMED BOOKKEEPING COMMIT = 1de258ff8fb0e4113d2eab73e13b51e502cd20fe`; `THIRD-PARTY PATH-F AUTHORIZATION-ACCEPTANCE CONFIRMER SESSION SEPARATION = SATISFIED`; `CONFIRMER WAS NOT THE PATH-F AUTHORIZATION-DESIGN CANDIDATE AUTHOR SESSION = YES`; `CONFIRMER WAS NOT THE QUALIFYING AUTHORIZATION-DESIGN REVIEW SESSION = YES`; `CONFIRMER WAS NOT THE AUTHORIZATION-DESIGN ACCEPTANCE-BOOKKEEPING AUTHOR SESSION = YES`; `CONFIRMER DID NOT PREVIOUSLY CONFIRM THIS EXACT BOOKKEEPING OBJECT = YES`; `CONFIRMATION VERDICT = APPROVE V0.3 PATH-F ETB EXECUTION-AUTHORIZATION DESIGN ACCEPTANCE BOOKKEEPING - THIRD-PARTY INDEPENDENT CONFIRMATION`; `FRESH CONFIRMATION SEVERITY = P0 = 0, P1 = 0, P2 = 0, P3 = 1`.  **Materialization shape (precedent-determined, not invented):** exactly one single-parent child commit of `1de258ff8fb0e4113d2eab73e13b51e502cd20fe` whose sole tracked delta against that parent is `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md` and NO third tracked path, directly governed by the Path-D authorization confirmation record `c1d7bd38be16ee7807c98044cdd8f17d83e97729` and the Path-E authorization confirmation record `c7ac36a8c596ae2ede8db7bce2e625f8c6ffa21c`.  **Effectivity transition (all five lifecycle stages now exist: design candidate, qualifying third-party design review, acceptance bookkeeping, fresh independent confirmation of that bookkeeping, and this explicitly authorized tracked materialization):** `PATH-F AUTHORIZATION DESIGN = ACCEPTED / FROZEN / EFFECTIVE`; `PATH-F ETB EXECUTION AUTHORIZATION = ACCEPTED / FROZEN / EFFECTIVE`; frozen authorization identity remains `path_f_authorization_commit = ed112f8c5f1e35d87092d0339698a792ce0b145a` and `path_f_authorization_sha256 = c147af8714164dae8b81cafa4eb01945a3ceb8c74b36f0fc18fbd56db284c4de`; this materialization commit is NOT the authorization-design identity.  **Execution authority semantics:** `PATH-F EXECUTION AUTHORITY = GRANTED SUBJECT TO ALL PRE-* CONDITIONS / ONE-SHOT ONLY`; authorization effectivity is NOT operational execution - operational use may occur only in a separate, fresh Path-F one-shot ETB operational execution session, and nothing is executed, claimed, consumed or invoked in this round.  **Repository-verifiable effectivity contract (derivable only from Git topology plus tracked status-surface bytes plus frozen artifact identity, never from chat history):** single parent `1de258ff8fb0e4113d2eab73e13b51e502cd20fe`; sole tracked delta = the two status surfaces; no third path; artifact SHA-256 `c147af8714164dae8b81cafa4eb01945a3ceb8c74b36f0fc18fbd56db284c4de` (84894 bytes, LF 1147, CR 0, no BOM, terminal LF present); status surfaces state `ACCEPTED / FROZEN / EFFECTIVE` bound to design `ed112f8c5f1e35d87092d0339698a792ce0b145a`.  **No self-reference:** this record deliberately does not embed its own commit SHA; it is identified by its parent, its subject `docs(v03e): record Path-F authorization confirmation` and its changed-path set, and that subject is not an acceptance subject and does not imply a second acceptance-bookkeeping event.  **Anti-recursion:** `AUTHORIZATION CONFIRMATION RECURSION = NONE`; any follow-up third-party read-only verification is a verification of an existing record, not a new acceptance or effectivity event - it spawns no further record commit, no materialization-of-materialization, no recursive lifecycle and no ratification.  **Authorization available, NOT consumed:** `PATH-F AUTHORIZATION USE = 1 OF 1 / AVAILABLE FOR CONSUMPTION` (`0 OF 1 / NOT CONSUMED`); `PATH-F ETB ATTEMPT = 1 OF 1 / AVAILABLE FOR CONSUMPTION` (`0 OF 1 / NOT STARTED`); `ORACLE-PATHF INVOCATIONS = 1 OF 1 / AVAILABLE ONLY AFTER BOTH CLAIMS EXIST` (`0 OF 1` invoked); `AUTHORIZATION-USE CLAIM = ABSENT`; `ATTEMPT-USE CLAIM = ABSENT`; `PATH-F CLAIM PATHS = ABSENT (4 / 4)`; `PATH-F RUNTIME OCCUPANCY = 0 / 11`.  **Execution remains closed:** `PATH-F ETB EXECUTION = NOT AUTHORIZED BY THIS ROUND`; `ORACLE-PATHF INVOCATION = NOT PERFORMED BY THIS ROUND`; `LISTENER QUERY = NOT EXECUTED`; `TARGET PROBE = NOT EXECUTED`; `ENDPOINT PROBE = NOT EXECUTED`; claims `NOT CREATED`; budgets `NOT CONSUMED`; no ACL mutation or restoration; no retry; no runtime publication; no result promotion.  **PRE-2 / PRE-3 effect:** `PRE-2 external identity source = REPOSITORY-VERIFIABLE AND FROZEN`; `PRE-3 authorization effectivity layer = NOW ESTABLISHED BY GOVERNANCE MATERIALIZATION`; `PRE-3 consumable-state layer = NOT EVALUATED IN THIS MATERIALIZATION ROUND`; no PRE gate is operationally evaluated here and no execution begins here.  **Provenance boundary preserved:** `MODEL_2_EXTERNAL_LINEAGE_BINDING` preserved; claims, when later created in the operational round, carry the frozen external lineage values; no Oracle-generated `oracle_path_f_commit` / `oracle_path_f_spec_sha256` / `oracle_path_f_script_sha256` field is required to cease being the literal `UNKNOWN` where the frozen Oracle model reserves `UNKNOWN`, and no post-hoc evidence rewrite is permitted or performed.  **Frozen Oracle-PathF binding preserved:** `oracle_path_f_design_commit = a5d598a05a0467eea98cd0bf16e4486cceb72c23`, `oracle_path_f_spec_sha256 = b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5` (34308 bytes), `oracle_path_f_script_sha256 = 4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0` (49704 bytes), `ORACLE-PATHF DESIGN = ACCEPTED / FROZEN / EFFECTIVE`; neither frozen Oracle artifact modified.  **Presentation variance recorded, NOT repaired:** the sole fresh confirmation finding `P3-BK-1` - `docs/v0.3/V03E_ACCEPTANCE.md` row 126 terminating with a bare closing pipe instead of the prevalent space-then-pipe form, class PRESENTATION CONSISTENCY ONLY / P3 / NONBLOCKING - is recorded accurately; the accepted bookkeeping commit is not rewritten, history is not amended, the authorization artifact is not edited, severity is not escalated, no correction is required for effectivity, and any future cosmetic repair would require its own explicit Owner-authorized governance round.  The accepted authorization artifact remains byte-frozen (`c147af87...c4de`, 84894 bytes, LF 1147, CR 0, no BOM, terminal LF present) and none of its seven qualifying-review findings (P3-A through P3-G) is repaired, reclassified or promoted.  **Predecessor boundary preserved:** `PATH-E LINEAGE = EXHAUSTED / CLOSED`; `PATH-E RAW RESULT = BLOCKED / NON-PROMOTABLE`; `PATH-E ETB SEMANTIC RESULT = NONE`; `PATH-E RETRY AUTHORITY = NONE`; `PATH-E RUNTIME OCCUPANCY = 6 / 11`; `PATH-D = EXHAUSTED / CLOSED / IMMUTABLE`; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED` with no promotion and no authoritative-result replacement.  This materialization round performed 0 authorization-use claim creations, 0 attempt-use claim creations, 0 Oracle-PathF executions, 0 Oracle-PathE executions, 0 Oracle-PathD executions, 0 ETB executions, 0 listener queries, 0 Get-NetTCPConnection calls, 0 port-4096 probes, 0 localhost / 127.0.0.1 probes, 0 endpoint probes, 0 OpenCode starts/restarts, 0 HTTP / provider / model calls, 0 budget creations, 0 budget consumptions, 0 evidence / manifest / result creations, 0 Path-F runtime entries created, 0 Path-E or Path-D modifications, 0 frozen Oracle-PathF artifact modifications, 0 accepted-artifact mutations, 0 authorization-artifact modifications, 0 ACL reads / mutations / restorations and 0 runtime / test / dependency / version changes.  **NEXT STAGE = SEPARATE FRESH PATH-F ONE-SHOT ETB OPERATIONAL EXECUTION SESSION** performing `13` through `20` in order (stage `7` of the frozen authorization sequence), separate from this materialization session, which must perform all PRE gates before consumption, respect PRE-17 write-viability capacity and PRE-18 no-reattempt, create claims only through the frozen writer `Write-DevRelayPathFOneShotClaim`, invoke Oracle-PathF at most once, never mutate ACLs, and never repair or retry after a failed non-consuming `CreateNew`.  No tag, no release and no push occurred.

**PATH-F PRE-16 OPERATIONAL PRECONDITION STOP — OWNER-GOVERNED DISPOSITION AND REMEDIATION-PATH DETERMINATION (governance record only; nothing executed, nothing retried, no claim created, no budget consumed, no Oracle invocation, no listener query, no endpoint probe, no ACL mutation, no frozen artifact modified, no new authorization created).**  The one-shot Path-F ETB operational execution round was executed in a separate operational session and ended at its first failed precondition, **before consumption**: `PATH-F OPERATIONAL EXECUTION = NOT STARTED`; `BLOCKER = REQUIRED FILE-ACCESS MODE NOT ESTABLISHED BEFORE IRREVERSIBLE SEQUENCE`; first failed gate `PRE-16`; `PRE-1 … PRE-15 = PASS`; `PRE-16 = FAIL`; `PRE-17 = FAIL / DEPENDENT ON PRE-16`; `PRE-18 = NOT REACHED`; terminal state `PRECONDITION STOP BEFORE CONSUMPTION / REQUIRED EXECUTION / FILE-ACCESS MODE NOT ESTABLISHED BEFORE THE IRREVERSIBLE SEQUENCE`.  Claims `ABSENT (4 / 4)`; `PATH-F RUNTIME OCCUPANCY = 0 / 11`; 0 claim `CreateNew` attempts; 0 budget consumption; `ORACLE-PATHF INVOCATIONS = 0 OF 1`; 0 Oracle executions; 0 listener queries; 0 target / endpoint probes; 0 runtime artifacts; 0 repository writes from the operational round.  **Structural gap independently reproduced in this disposition session:** the accepted Oracle-PathF specification `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE_PATH_F.md` §9.2 (lines 321-322) freezes `REQUIRED_FILE_ACCESS_MODE_REQUIREMENT = PRESENT` — "A future Path-F execution authorization record must state the required mode explicitly and must not create escalation authority" — while the accepted, frozen and effective authorization artifact `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_F_AUTHORIZATION.md` (`c147af8714164dae8b81cafa4eb01945a3ceb8c74b36f0fc18fbd56db284c4de`, 84894 bytes) carries `EFFECTIVE_AUTHORIZATION_CONCRETE_MODE_DECLARATION = ABSENT`: an exhaustive `mode` sweep and a `mode` / `sandbox` / `escalation` / `elevation` sweep return only placeholder wording ("the required execution/file-access mode is **already established** for the round", line 319; "the required mode was **not** obtained by modifying an access-control list", line 321; the fail-closed token at line 339; the PRE-16 row at line 662) and name **no** concrete, repository-verifiable, operationally actionable required mode, so `PATHF_PRE16_STRUCTURAL_GAP = CONFIRMED`.  **Prospective mode versus reactive escalation:** `PROSPECTIVE_MODE_DECLARATION_COMPATIBILITY = COMPATIBLE` — stating a required mode in advance is exactly what §9.1 and §9.2 require and creates no escalation authority, while the frozen prohibition targets the reactive elevation invoked after a failure or after the irreversible sequence begins (§9.3, §9.4; authorization §6.2, §7); the mode itself is **not** established, tested, probed or operated in this round.  **Remediation route, single classification:** `REMEDIATION ROUTE = ROUTE A / CORRECTIVE SUCCESSOR PATH-F ETB EXECUTION-AUTHORIZATION DESIGN LIFECYCLE REQUIRED`, because the missing concrete mode is a defect of the **authorization** layer (spec §9.2 places the obligation on the authorization record), the frozen artifact must remain immutable, and correction therefore requires a new successor design identity that must itself pass a fresh qualifying third-party independent review, acceptance bookkeeping, independent confirmation and explicit materialization before any new operational round may be authorized. `ROUTE B = NOT SELECTED` — spec §9.2 requires the authorization record itself to state the required mode, PRE-2 binds the executor to that record's identity, and no direct precedent supports supplying a design-required authorization parameter from a separate layered record, so its condition 1 and condition 5 fail. `ROUTE C = NOT SELECTED` — the current Path-F authorization lifecycle **can** be corrected by a successor revision, as directly precedented by the Path-E corrected successor `4900625114a38a86aa03a5fa4861c5bcd9436dc5` succeeding candidate `26b183083fbbe323441283f99f3cf2c931acd6ff`. `ROUTE D = NOT SELECTED`.  **Budget semantics preserved:** `PATH-F AUTHORIZATION USE = 1 OF 1 / AVAILABLE FOR CONSUMPTION / 0 OF 1 / NOT CONSUMED`; `PATH-F ETB ATTEMPT = 1 OF 1 / AVAILABLE FOR CONSUMPTION / 0 OF 1 / NOT STARTED`; `ORACLE-PATHF INVOCATIONS = 0 OF 1`; neither budget is spent, reset or replaced, and neither is automatically reusable — same-round retry `FORBIDDEN`, automatic new-session retry under the same governance `FORBIDDEN`, and a **NEW explicit Owner-governed authority lifecycle is REQUIRED** (authorization §6.3 and the PRE-18 row).  **Effectivity preserved, operational usability blocked:** `PATHF_AUTHORIZATION_EFFECTIVITY_AFTER_PRE16_STOP = ACCEPTED / FROZEN / EFFECTIVE` (governance record; identity unchanged; not revoked, not altered and not superseded by this round) while `PATHF_OPERATIONAL_USABILITY_AFTER_PRE16_STOP = BLOCKED PENDING NEW OWNER-GOVERNED AUTHORITY LIFECYCLE`.  **No result lifecycle:** `PATH-F RAW ETB RESULT = NONE`; `HARNESS_INVALID = NONE`; `PATH-F RESULT PROMOTION = NOT APPLICABLE / BLOCKED`; no result review, bookkeeping or promotion is created; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED` unchanged, its authority deriving from the previously accepted Recovery-R2 result and **not** from any Path-F attempt.  **Precedent class:** `PATHF_PRE16_DISPOSITION_PRECEDENT = DETERMINATIVE` — a stopped operational round must be recorded as a tracked disposition (`15dc6157aeac02a562396c6744700735b8b75251`, `44471fcfec8f3378dd6feb9c3803207db477a713`), the disposition mutation shape is exactly `M CHANGELOG.md` + `M docs/v0.3/V03E_ACCEPTANCE.md` with **no third tracked path** (`15dc6157` numstat `2 0` / `1 1`; `44471fcf` numstat `2 0` / `1 1`; corrective successor record `c45fb94068d5384dd9662f822be4722951f4200b` identical), the subject family is `docs(v03e): record Path-X operational outcome`, accepted and frozen artifacts are never repaired in place, and supersession is recorded by a corrective or superseding successor record that preserves every prior entry and amends none.  **Disposition materialization:** `PRE16_DISPOSITION_MATERIALIZATION = REQUIRED`; exactly one local single-parent successor commit of `62a4098ad34447fc8658d1d73a9aba484b27d4ba`, governance-only, no amend, no reset, no rebase and no history rewrite.  **Protected identities verified unchanged:** authorization artifact `c147af8714164dae8b81cafa4eb01945a3ceb8c74b36f0fc18fbd56db284c4de` / 84894 bytes; Oracle-PathF design commit `a5d598a05a0467eea98cd0bf16e4486cceb72c23`; spec `b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5` / 34308 bytes; executable `4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0` / 49704 bytes.  **Predecessor boundary preserved:** `PATH-E LINEAGE = EXHAUSTED / CLOSED`; `PATH-E RAW RESULT = BLOCKED / NON-PROMOTABLE`; `PATH-E ETB SEMANTIC RESULT = NONE`; `PATH-E RETRY AUTHORITY = NONE`; `PATH-E RUNTIME OCCUPANCY = 6 / 11`; `PATH-D = EXHAUSTED / CLOSED / IMMUTABLE`; no cleanup and no reuse.  This disposition round performed 0 claim creations, 0 budget consumptions, 0 Oracle-PathF invocations, 0 ETB executions, 0 listener queries, 0 port-4096 probes, 0 endpoint probes, 0 OpenCode starts or restarts, 0 HTTP / provider / model calls, 0 ACL reads, mutations, restorations or normalizations, 0 `icacls` / `Set-Acl` calls, 0 elevation-mechanism invocations, 0 empirical governed-path write probes, 0 authorization-artifact edits, 0 corrective authorization designs, 0 result promotions, 0 Path-E or Path-D modifications and 0 runtime / test / dependency / version changes.  **NEXT STAGE = OWNER AUTHORIZATION FOR A CORRECTIVE SUCCESSOR PATH-F ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE**, which must state the required execution / file-access mode explicitly without creating escalation authority, and must pass a fresh qualifying third-party independent review, acceptance bookkeeping, independent confirmation and explicit materialization before any new operational round may be authorized; this round does not begin that stage and does not author the corrective design.  Process disclosure: because residual ACL restrictions on `docs` and `docs\v0.3` deny ordinary sandboxed writes, the status-surface writes and the commit of this governance-only round used harness escalation; escalation is a mechanical path that changes no content, creates no authority and has no operational effect.  No tag, no release and no push occurred.

**PATH-F CORRECTIVE SUCCESSOR ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE — EXPLICIT OWNER-AUTHORIZED AUTHORING ROUND (design and governance only; nothing executed, nothing retried, no claim created, no budget consumed, no Oracle invocation, no listener query, no endpoint probe, no ACL mutation, no permission repair, no execution-mode establishment or test, no frozen artifact modified, no operational authority created).**  The Owner recorded `OWNER DECISION = AUTHOR ONE CORRECTIVE SUCCESSOR PATH-F ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE` after the one-shot Path-F operational round ended at its first failed precondition, and this round authors exactly that corrective successor revision of `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_F_AUTHORIZATION.md`.  It is bound by the disposition commit `5fae11eefdcaddc27b4abf28d3a2258ad654d84d`, by `PATHF_PRE16_STRUCTURAL_GAP = CONFIRMED` and by `REMEDIATION ROUTE = ROUTE A`; it does not re-review, re-materialize or reopen that disposition, and it does not execute, retry or probe anything.  **The structural defect repaired:** the accepted authorization record never stated the required execution / file-access mode, which is what the accepted Oracle-PathF specification §9.2 requires of an execution-authorization record, so `PRE-16` was not evaluable and the first operational round stopped before consumption (`PATH-F OPERATIONAL EXECUTION = NOT STARTED`; `BLOCKER = REQUIRED FILE-ACCESS MODE NOT ESTABLISHED BEFORE IRREVERSIBLE SEQUENCE`; `PRE-1 … PRE-15 = PASS`, `PRE-16 = FAIL`, `PRE-17 = FAIL (dependent on PRE-16)`, `PRE-18 = NOT REACHED`; 0 claim `CreateNew` attempts, 0 budgets consumed, 0 Oracle invocations, no raw result, `HARNESS_INVALID = NONE`, same-round retry `FORBIDDEN`).  **The concrete declaration:** `REQUIRED PATH-F OPERATIONAL EXECUTION / FILE-ACCESS MODE = full-file-access`; `workspace-write = INSUFFICIENT FOR PATH-F OPERATIONAL EXECUTION`; `full-file-access = REQUIRED PRE-EXISTING OPERATIONAL EXECUTION MODE`; `PROSPECTIVE EXECUTION-MODE REQUIREMENT = PERMITTED / REQUIRED` and `REACTIVE ESCALATION AFTER FAILURE = FORBIDDEN`, so the future operational executor must start its session already provisioned in the required mode and may not start in `workspace-write` and "try", probe a claim path or governed path to discover whether permissions work, request or acquire the mode after a failure, invoke elevation after the irreversible sequence begins, mutate, restore or normalize an access-control list, repair permissions, use `icacls` or `Set-Acl`, or create any authorization-layer empirical governed-path write probe.  `PRE-16` is now directly evaluable through seven explicit criteria — the session execution / file-access mode is exactly `full-file-access`, it existed before the irreversible sequence, it was not obtained in response to a failed gate or claim operation, no ACL repair is planned, pending or active, no permission repair is planned, pending or active, no execution-time elevation mechanism is authorized, invoked or available, and the mode is verifiable from the session environment without ACL enumeration, access-control-list read or empirical governed-path write probe — with inability to verify the exact mode failing closed as `PRE-16 = FAIL` rather than licensing a test; `PRE-17` is clarified as a non-probing control-state / capacity gate satisfied by the established mode plus the frozen publication contract, requiring zero file creation, zero governed-path write and no probe on the Oracle's behalf, and preserving the Oracle's exclusively owned write-viability gate; `PRE-18` is preserved in substance and extended so that changing the session's execution / file-access mode to answer a non-consuming failure, and any reactive escalation in response to it, are `FORBIDDEN`.  **Supersession:** the previously accepted authorization `ed112f8c5f1e35d87092d0339698a792ce0b145a` / `c147af8714164dae8b81cafa4eb01945a3ceb8c74b36f0fc18fbd56db284c4de` remains `ACCEPTED / FROZEN / EFFECTIVE` as immutable history, is never amended, revoked or relabelled, and only its operational usability is `BLOCKED AFTER THE PRE-16 PRECONDITION STOP`; `SUPERSESSION EFFECT = PROSPECTIVE ONLY`; the corrective successor is `DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / NOT OPERATIONALLY USABLE` and carries the two external identity placeholders exactly as its predecessor did.  **Budget carry-forward (acceptance-critical):** `PATHF_CORRECTIVE_BUDGET_CARRY_FORWARD_MODEL = SAME LINEAGE-LEVEL ONE-SHOT BUDGETS CARRIED FORWARD, IDENTITY RE-BOUND TO THE NEW ACCEPTED CORRECTIVE AUTHORIZATION (NO SECOND BUDGET, NO RESET, NO AUTOMATIC REUSE)` — the lineage holds exactly one authorization-use budget and exactly one ETB-attempt budget at the frozen eleven-path namespace claim pairs, there is no second or successor budget path and no twelfth namespace member, both budgets remain `0 OF 1 / NOT CONSUMED` and `0 OF 1 / NOT STARTED`, and they are carried forward to the new accepted corrective identity with no reuse authority under either identity until the effectivity lifecycle completes; any future claim must bind the new accepted corrective `authorization_commit` / `authorization_sha256` and never `ed112f8c…` / `c147af87…`.  **Also corrected:** the recorded design findings P3-A (non-existent `§26` lifecycle references, now `§20`), P3-B (`twelve preserved rows plus three` → `fifteen preserved rows plus three`), P3-C (incorrect `§13/§25` accepted-control-surface pointer), P3-D (`§24` live-state reference → the `§23` live-state surface), P3-E (`§21.4` provenance audit-result pointer → `§3.3` and `§19.4`), P3-F (`§18` result-authority pointer → `§17.4`) and P3-G (`PRE-17` empirical-write-probe ambiguity).  **Unchanged and preserved:** the accepted Oracle-PathF design `a5d598a05a0467eea98cd0bf16e4486cceb72c23` with specification `b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5` (34308 bytes) and executable `4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0` (49704 bytes), `MODEL_2_EXTERNAL_LINEAGE_BINDING`, the exactly eleven-path namespace, the frozen claim schemas and claim writer, the exclusively Oracle-PathF-owned listener / target / probe / classification boundary, the closed three-class result model (`ETB_SATISFIED`, `ETB_UNSATISFIED`, `HARNESS_INVALID / NO ETB SEMANTIC RESULT`) with no fourth ETB class, the Path-E and Path-D terminal boundaries, `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED` and `RAW PATH-F RESULT PROMOTION = REJECTED / BLOCKED`; the historical status-surface findings `P3-BK-1` and `P3-MAT-1` are **not** repaired.  Post-candidate state: `PATH-F OPERATIONAL EXECUTION = BLOCKED`, `PATH-F CLAIMS = ABSENT (4 / 4)`, `PATH-F RUNTIME OCCUPANCY = 0 / 11`, `PATH-E RUNTIME OCCUPANCY = 6 / 11`, `ORACLE-PATHF INVOCATIONS = 0 OF 1`, `PATH-F EXECUTION AUTHORITY = NONE`, `CURRENT ACL STATE = NOT NORMALIZED` and unchanged.  This round performed 0 claim creations, 0 budget consumptions, 0 Oracle-PathF invocations, 0 ETB executions, 0 listener queries, 0 port-4096 probes, 0 endpoint probes, 0 OpenCode starts or restarts, 0 HTTP / provider / model calls, 0 ACL reads, mutations, restorations or normalizations, 0 `icacls` / `Set-Acl` calls, 0 elevation-mechanism invocations, 0 execution-mode establishments, verifications or tests, 0 empirical governed-path write probes, 0 runtime namespace entries, 0 result promotions, 0 Path-E or Path-D modifications and 0 runtime / test / dependency / version changes; the tracked mutation surface is exactly `M CHANGELOG.md`, `M docs/v0.3/V03E_ACCEPTANCE.md` and `M docs/v0.3/V03E_G0_5_PRE_ETB_PATH_F_AUTHORIZATION.md`, and the corrective candidate commit is the single-parent successor of `5fae11eefdcaddc27b4abf28d3a2258ad654d84d`.  `NEXT STAGE = FRESH QUALIFYING THIRD-PARTY INDEPENDENT REVIEW OF THE CORRECTIVE SUCCESSOR PATH-F ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE` in a different agent / session, followed by acceptance bookkeeping, fresh independent confirmation and explicit materialization before any new operational round may be authorized; this round performs none of those stages.  Process disclosure: because residual ACL restrictions on `docs` and `docs\v0.3` deny ordinary sandboxed writes, the artifact and status-surface writes of this governance-only round used harness escalation; escalation is a mechanical path that changes no content, creates no authority and has no operational effect.  No tag, no release and no push occurred.





**PATH-F CORRECTIVE SUCCESSOR ETB EXECUTION-AUTHORIZATION DESIGN — BOUNDED P2 REMEDIATION REVISION (explicit Owner-authorized governance-authoring round; design and governance only; nothing executed, nothing retried, no claim created, no budget created / consumed / reset / replaced, no Oracle-PathF invocation, no listener query, no target probe, no endpoint probe, no ACL read, no ACL mutation, no ACL restoration, no permission repair, no permission normalization, no execution-mode establishment / verification / switch / test, no governed-path probe, no runtime namespace entry, no result promotion, no reviewed artifact modified, no frozen artifact modified, no operational authority created).**  The Owner recorded the qualifying third-party review of the first corrective candidate `d895856d2efc9683b91b182c33647efe57b01fc3` / artifact SHA-256 `c281f93e6ddfe09351c435e698c5d50c3a5cfcda2053f27159ba921e2eed72eb` as `REQUEST_CHANGES — V0.3 PATH-F CORRECTIVE SUCCESSOR ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE` with severity `P0 = 0`, `P1 = 0`, `P2 = 1`, `P3 = 4`; the sole blocking P2 was `FULL_FILE_ACCESS_MODE_IDENTITY = LABEL_PRESENT_BUT_NOT_OPERATIONALLY_VERIFIABLE` with `CORRECTED_PRE_16 = AMBIGUOUS`.  **Root cause:** the candidate used `full-file-access` as though it were a real DSH mode, while DSH's closed canonical mode vocabulary is `read-only` / `workspace-write` / `danger-full-access`.  **Owner corrected decision:** `REQUIRED PATH-F DSH OPERATIONAL EXECUTION / FILE-ACCESS MODE = danger-full-access`; `CANONICAL REQUIRED MODE = danger-full-access`; `full-file-access` is superseded as a normative DSH mode token and may survive only where explicitly marked `HISTORICAL / DESCRIPTIVE ONLY / NOT A DSH MODE TOKEN / NOT ACCEPTABLE AS PRE-16 EVIDENCE`.  This round authors exactly one bounded corrective successor revision of `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_F_AUTHORIZATION.md`, in the same tracked three-path governance surface as its predecessor, and performs no broader redesign.  **Recovered DSH canonical mode model (from the installed harness resources, independently re-established in this authoring session):** the bundled type catalog declares `SandboxMode = 'read-only' | 'workspace-write' | 'danger-full-access'`; the permission presets map `read-only → {sandbox: read-only, approval: ask}`, `workspace-write → {sandbox: workspace-write, approval: ask}` and `danger-full-access → {sandbox: danger-full-access, approval: never}`; the behaviour table defines `danger-full-access` as "No confinement; the provider is never consulted, and results carry `sandbox: { mode, denied: false }`".  `DSH_CANONICAL_MODE_MODEL = DETERMINATE`; `DSH_REQUIRED_UNCONFINED_MODE_TOKEN = danger-full-access`.  **Recovered non-mutating session-mode observation channel:** the sandbox-policy owner contributes exactly one capability-neutral runtime-context entry named `sandbox:policy` to the **current runtime-context snapshot of every agent session**, and the agent loop logs that snapshot in the session as a **sourced `user/message`**; the entry renders the session's resolved canonical mode as a closed verbatim literal, of which the required one is exactly ``Current DSH file policy: danger-full-access. The DSH file sandbox does not restrict file modifications by available operations.``.  `DSH_SESSION_MODE_OBSERVATION_CHANNEL = the session-visible sandbox:policy runtime-context declaration; the canonical token following the literal "Current DSH file policy: " must be exactly danger-full-access`.  `DEPENDENCE ON A SHELL ENVIRONMENT VARIABLE = NONE / FORBIDDEN`: the harness consumes `DSH_PERMISSION_MODE` in the **launching** process to configure the sandbox and approval policies, and that variable is **not** guaranteed to be exported into the child shell — in this authoring session it was demonstrably absent while `DSH_HOME`, `DSH_PROFILE`, `DSH_PROFILE_DIR`, `DSH_SESSION_ID`, `DSH_SHELL` and `DSH_WEB_URL` were present — so no environment-variable test may be used as primary evidence and no environment variable may be invented as one.  **Artifact changes (bounded):** the normative declaration becomes exactly `REQUIRED PATH-F DSH OPERATIONAL EXECUTION / FILE-ACCESS MODE = danger-full-access` with `read-only = INSUFFICIENT FOR PATH-F OPERATIONAL EXECUTION`, `workspace-write = INSUFFICIENT FOR PATH-F OPERATIONAL EXECUTION` and `danger-full-access = REQUIRED PRE-EXISTING DSH OPERATIONAL EXECUTION MODE`; a new §6.4 specifies the observation mechanism, the required observed value, the fail-closed condition and the zero-cost table (`filesystem writes`, `claim-path accesses`, `governed-path probes`, `ACL reads`, `ACL mutations`, `permission repairs`, `runtime escalation`, `trial CreateNew calls` all `= 0`), with approval-policy corroboration admitted as secondary evidence only; `PRE-16` is rewritten as an objectively and deterministically evaluable eight-clause rule — (1) the session-visible policy declaration reports the canonical mode exactly `danger-full-access`; (2) that mode was provisioned before the Path-F operational round entered the irreversible sequence; (3) it was not obtained or requested in response to any failed Path-F PRE gate, claim operation, Oracle action or runtime failure; (4) no ACL repair is planned, pending or active; (5) no permission repair is planned, pending or active; (6) no reactive execution-time elevation path is authorized for the round; (7) the check uses only the recovered non-mutating observation mechanism; (8) inability to observe or establish the exact canonical token is `PRE-16 = FAIL`; the rule requires `NO REACTIVE ELEVATION AUTHORITY OR PATH IS AVAILABLE TO THIS PATH-F ROUND` and explicitly does **not** require proving that the host operating system contains no possible elevation facility.  The harness per-call sandbox-escalation facility (`sandbox_permissions`) is named as a reactive elevation path and is **NOT AUTHORIZED**; relying on a shell environment variable to establish the mode is recorded as **NOT AUTHORITY**.  `MODE_TOKEN_GLOBAL_NORMALIZATION = COMPLETE`: exactly one normative mode token, no second source of truth, no surviving generic mode phrase whose normative value cannot be traced to `danger-full-access`; the artifact retains four `full-file-access` occurrences, **all non-normative** — one auditable historical record in §0 decision 13 explicitly qualified `HISTORICAL / DESCRIPTIVE ONLY / NOT A DSH MODE TOKEN / NOT ACCEPTABLE AS PRE-16 EVIDENCE`, and three explicit absence assertions (`normative full-file-access occurrences = 0` in the round-bounds record, the §21.2 self-audit row, and the §24 review checklist) — so `NORMATIVE full-file-access OCCURRENCES = 0`.  **Preserved without regression:** `PRE-17` remains `CONTROL-STATE / CAPACITY ONLY` and non-probing (no file creation, no claim-path test, no governed-path probe, no write/flush/read-back test, no TEMP, evidence, manifest or result, no runtime-namespace touch), now anchored on `PRE-16` having already confirmed `danger-full-access` through §6.4, with the Oracle's own pre-publication write-viability gate remaining exclusively Oracle-owned; `PRE-18` remains `EXPLICIT_AND_CLOSED` — for a failed claim `CreateNew` before creation, budget consumed `NO`, round terminated `YES`, same-round retry `NO`, mode switching `NO`, reactive escalation `NO`, permission repair `NO`, ACL repair `NO`, and a future attempt requires a **NEW OWNER-GOVERNED AUTHORITY LIFECYCLE**; `PROSPECTIVE_VS_REACTIVE_ACCESS_MODEL = CLOSED`; `PATHF_CORRECTIVE_BUDGET_CARRY_FORWARD_MODEL = SAME LINEAGE-LEVEL ONE-SHOT BUDGETS CARRIED FORWARD, IDENTITY RE-BOUND TO THE NEW ACCEPTED CORRECTIVE AUTHORIZATION, NO SECOND BUDGET, NO RESET, NO AUTOMATIC REUSE` with `PATH-F AUTHORIZATION USE = 1 OF 1 / 0 OF 1 CONSUMED` and `PATH-F ETB ATTEMPT = 1 OF 1 / 0 OF 1 STARTED`; `P3-A` … `P3-G` remain corrected and the historical governance-only observations `P3-BK-1` and `P3-MAT-1` remain unrepaired.  **Supersession chain recorded:** the historical authorization `ed112f8c5f1e35d87092d0339698a792ce0b145a` / `c147af8714164dae8b81cafa4eb01945a3ceb8c74b36f0fc18fbd56db284c4de` stays `ACCEPTED / FROZEN / EFFECTIVE / OPERATIONALLY BLOCKED AFTER THE PRE-16 STOP`; the first corrective candidate `d895856…` / `c281f93e…` is `REQUEST_CHANGES` / `NOT ACCEPTED` / `NOT FROZEN` / `NOT EFFECTIVE` / `SUPERSEDED PROSPECTIVELY BY THIS SUCCESSOR`; this new bounded P2-remediation successor is a `DESIGN CANDIDATE / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / NOT OPERATIONALLY USABLE`.  No historical object is erased, revoked, amended or relabelled, and no historical status surface is rewritten by this round.  **Identity and future claims:** the successor embeds no future commit SHA and no future artifact SHA; `path_f_authorization_commit` and `path_f_authorization_sha256` remain externally bound placeholders to be filled by later governance surfaces after independent acceptance.  Any future Path-F claim must bind the **new** accepted corrective identity and must **not** bind `ed112f8c…` / `c147af87…`, and must **not** bind `d895856…` / `c281f93e…` unless that candidate were accepted, which it is not.  **Unchanged and preserved:** Oracle-PathF design `a5d598a05a0467eea98cd0bf16e4486cceb72c23`, specification SHA-256 `b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5` (34308 bytes) and executable SHA-256 `4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0` (49704 bytes), `MODEL_2_EXTERNAL_LINEAGE_BINDING`, the exactly eleven-path runtime namespace, the frozen claim schemas and claim writer, the exclusively Oracle-PathF-owned listener / target / probe / classification boundary, the closed three-class result model (`ETB_SATISFIED`, `ETB_UNSATISFIED`, `HARNESS_INVALID / NO ETB SEMANTIC RESULT`) with no fourth ETB class, the Path-E terminal boundary (`EXHAUSTED / CLOSED`, raw result `BLOCKED / NON-PROMOTABLE`, ETB semantic result `NONE`, retry authority `NONE`, runtime occupancy `6 / 11`), the Path-D boundary (`EXHAUSTED / CLOSED / IMMUTABLE`), `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED` and `RAW PATH-F RESULT PROMOTION = REJECTED / BLOCKED`.  Post-candidate state: `PATH-F OPERATIONAL EXECUTION = BLOCKED`, `PATH-F EXECUTION AUTHORITY = NONE`, `PATH-F CLAIMS = ABSENT (4 / 4)`, `PATH-F RUNTIME OCCUPANCY = 0 / 11`, `ORACLE-PATHF INVOCATIONS = 0 OF 1 / NOT AUTHORIZED`, `CURRENT ACL STATE = NOT NORMALIZED` and unchanged.  This round performed 0 claim creations, 0 budget creations / consumptions / resets / replacements, 0 Oracle-PathF invocations, 0 ETB executions, 0 listener queries, 0 port-4096 probes, 0 target / endpoint probes, 0 OpenCode starts or restarts, 0 HTTP / provider / model calls, 0 ACL reads, mutations, restorations or normalizations, 0 `icacls` / `Set-Acl` calls, 0 permission repairs, 0 execution-mode establishments, verifications, switches or tests, 0 governed-path probes, 0 runtime namespace entries, 0 result promotions, 0 Path-E or Path-D modifications and 0 runtime / test / dependency / version changes; the tracked mutation surface is exactly `M CHANGELOG.md`, `M docs/v0.3/V03E_ACCEPTANCE.md` and `M docs/v0.3/V03E_G0_5_PRE_ETB_PATH_F_AUTHORIZATION.md`, and the successor candidate commit is the single-parent successor of `d895856d2efc9683b91b182c33647efe57b01fc3`.  Author self-audit of this round: `P0 = 0`, `P1 = 0`, `P2 = 0`, `P3 = 1`; the sole P3 is the recorded review-finding remediation boundary, and this classification binds no reviewer.  `NEXT STAGE = FRESH QUALIFYING THIRD-PARTY INDEPENDENT REVIEW OF THE BOUNDED P2 REMEDIATION SUCCESSOR PATH-F ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE` in a different agent / session, followed by acceptance bookkeeping, fresh independent confirmation and explicit materialization before any new operational round may be authorized; this round performs none of those stages.  Process disclosure: because residual ACL restrictions on `docs` and `docs\v0.3` deny ordinary sandboxed writes, the artifact and status-surface writes of this governance-authoring round used harness escalation; escalation is a mechanical path that changes no content, creates no authority and has no operational effect, and it does **not** establish the future Path-F operational mode, does **not** satisfy `PRE-16` and grants no operational or retry authority.  No tag, no release and no push occurred.
**PATH-F CORRECTIVE SUCCESSOR ETB EXECUTION-AUTHORIZATION DESIGN ACCEPTANCE BOOKKEEPING — QUALIFYING THIRD-PARTY AUTHORIZATION DESIGN REVIEW APPROVED (explicit Owner-authorized governance-bookkeeping round; governance only; nothing executed, nothing retried, no budget created / consumed / reset / replaced, no claim created, no runtime namespace occupied, no Path-F runtime artifact created, no reviewed artifact modified, no frozen Oracle-PathF artifact modified, no operational authority created, Path-D not reopened, Path-E not reopened).**  The fresh qualifying third-party independent review of the bounded P2-remediation successor Path-F ETB execution-authorization design candidate `89d8a7c851dca935c8ed119c13cca1e446e6c232` (artifact `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_F_AUTHORIZATION.md`, SHA-256 `3dbc20a5dd1324f558a3c9c0644141928c07951062a6279502d2bc930758d628`, 124650 bytes, blob `16fd027f5af40f08dc33ad43228566a894dde518`, LF 1446, CR 0, no BOM, terminal LF present) was completed read-only in a different agent/session with the independence declarations recorded before any substantive inspection — THIRD-PARTY PATH-F CORRECTIVE-SUCCESSOR AUTHORIZATION-DESIGN REVIEWER SESSION SEPARATION = SATISFIED, REVIEWER WAS NOT THE CORRECTIVE-SUCCESSOR AUTHORIZATION-DESIGN CANDIDATE AUTHOR SESSION = YES, REVIEWER DID NOT PREVIOUSLY REVIEW THIS EXACT CORRECTIVE-SUCCESSOR AUTHORIZATION-DESIGN OBJECT = YES — and returned **APPROVE V0.3 PATH-F BOUNDED P2-REMEDIATION SUCCESSOR ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE — QUALIFYING THIRD-PARTY INDEPENDENT REVIEW** with severity **P0 = 0, P1 = 0, P2 = 0, P3 = 3**, so the approval bar P0 = 0 / P1 = 0 / P2 = 0 was **met**; the Owner has accepted that qualifying review as the basis for acceptance bookkeeping, and this round materializes exactly that acceptance as status / governance bookkeeping only.  **Review classifications recorded exactly as the qualifying review established them:** BOUNDED_P2_SUCCESSOR_ARTIFACT_IDENTITY = EXACT; P2_REMEDIATION_BINDING = EXACT; DSH_CANONICAL_MODE_MODEL = DETERMINATE; DSH_UNCONFINED_CANONICAL_TOKEN = danger-full-access; DSH_SESSION_MODE_OBSERVATION_CHANNEL = REAL_DETERMINISTIC_AND_SESSION_VISIBLE; CANONICAL_MODE_DECLARATION = EXPLICIT_AND_UNIQUE; FULL_FILE_ACCESS_NORMALIZATION = COMPLETE; CORRECTED_PRE_16 = SATISFIABLE_AND_DETERMINISTIC; PROSPECTIVE_VS_REACTIVE_ACCESS_MODEL = CLOSED; CORRECTED_PRE_17 = COHERENT_AND_NON_PROBING; CORRECTED_PRE_18 = EXPLICIT_AND_CLOSED; MODE_TOKEN_GLOBAL_NORMALIZATION = COMPLETE; P3-A THROUGH P3-G = CORRECTED; BUDGET_CARRY_FORWARD_NON_REGRESSION = PRESERVED; FUTURE_CLAIM_IDENTITY_MODEL = DETERMINISTIC; SUCCESSOR_SUPERSESSION_MODEL = COHERENT; SUCCESSOR_SELF_IDENTITY_MODEL = SATISFIABLE_AND_EXTERNALLY_BOUND; ORACLE_PATHF_INTEGRITY = PRESERVED; SUCCESSOR_NAMESPACE_AND_CLAIM_MODEL = EXACT; LISTENER_TARGET_OWNERSHIP = EXCLUSIVE_TO_ORACLE_PATHF; RESULT_CLASS_MODEL = CLOSED; PREDECESSOR_INTEGRITY = PRESERVED; BOUNDED_P2_GOVERNANCE_DELTA = BOUNDED; BOUNDED_P2_AUTHORING_PROCESS_VARIANCE = NONBLOCKING / P3; BOUNDED_P2_DESIGN_ONLY_BOUNDARY = PRESERVED.  **Formal review severity is recorded exactly as the qualifying review classified it:** P0 = 0 / P1 = 0 / P2 = 0 / P3 = 3, where the three formal P3 findings are P3-1 retained historical / descriptive `full-file-access` occurrences, all non-normative, documentation hygiene only (class DOCUMENTATION HYGIENE / NONBLOCKING), P3-2 status-surface wording reports four retained occurrences while explicitly enumerating only three, reporting-only with no semantic effect (class REPORTING PRECISION / NONBLOCKING), and P3-3 authoring-environment process variance involving mechanical harness escalation for staging / commit, content-neutral and non-operational (class PROCESS DISCLOSURE / NONBLOCKING); all three are **accepted as nonblocking review findings and left unrepaired** — no P3 was repaired, reclassified or promoted, no additional finding was invented, no artifact byte was edited and no history was rewritten — and any future cosmetic change would require its own separate explicit Owner authorization.  **Accepted corrective successor identity frozen by this bookkeeping (immutable):** path_f_authorization_commit = `89d8a7c851dca935c8ed119c13cca1e446e6c232` — the independently approved corrective-successor authorization-design commit, **not** this acceptance-bookkeeping commit, **not** the later confirmation record, **not** the later materialization commit and **not** any later operational HEAD; path_f_authorization_sha256 = `3dbc20a5dd1324f558a3c9c0644141928c07951062a6279502d2bc930758d628`; artifact bytes 124650, LF 1446, CR 0, BOM absent, terminal LF present, UTF-8 and LF-only, worktree byte-identical to the committed blob `16fd027f5af40f08dc33ad43228566a894dde518` at index and at `HEAD`; the reviewed artifact is **not** rewritten, not edited and not corrected by this round, so its identity remains exactly the reviewed identity, and any future editorial cleanup would require its own successor design decision and would create a different authorization-design identity.  **Mode-token remediation bound by acceptance:** REQUIRED PATH-F DSH OPERATIONAL EXECUTION / FILE-ACCESS MODE = `danger-full-access`; DSH_REQUIRED_UNCONFINED_MODE_TOKEN = `danger-full-access`; the session-visible observation channel accepted by the review is the capability-neutral DSH `sandbox:policy` runtime-context declaration with the required visible token `Current DSH file policy: danger-full-access.`; `full-file-access` is superseded as a normative DSH mode token and survives only in explicitly non-normative historical / descriptive occurrences with NORMATIVE `full-file-access` OCCURRENCES = 0; CORRECTED PRE-16 = SATISFIABLE_AND_DETERMINISTIC, CORRECTED PRE-17 = COHERENT_AND_NON_PROBING and CORRECTED PRE-18 = EXPLICIT_AND_CLOSED; **binding this mode in acceptance bookkeeping does not establish `danger-full-access` for any operational round, does not satisfy PRE-16, creates no execution or retry authority and consumes no budget**, and these artifact bytes are not re-edited by this round.  **Oracle-PathF frozen provenance re-verified and preserved:** oracle_path_f_design_commit = `a5d598a05a0467eea98cd0bf16e4486cceb72c23`, oracle_path_f_spec_sha256 = `b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5` (34308 bytes), oracle_path_f_script_sha256 = `4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0` (49704 bytes), ORACLE-PATHF DESIGN = ACCEPTED / FROZEN / EFFECTIVE, ORACLE-PATHF EXECUTION = NOT AUTHORIZED; both Oracle-PathF artifacts are byte-identical at the accepted design commit, at the previous HEAD, in the index and in the worktree, and neither was modified by this round.  **Two-stage effectivity (NOT collapsed):** this commit is **acceptance-bookkeeping provenance only**; it replaces no frozen identity and it does not freeze or effectuate the corrective-successor execution authorization.  The corrective-successor execution authorization becomes ACCEPTED / FROZEN / EFFECTIVE **only** after a **fresh independent confirmation of THIS bookkeeping commit** performed in a different agent/session from this acceptance-bookkeeping-author session, followed by the precedent-required tracked materialization of that confirmation; immediately after this bookkeeping the state is PATH-F CORRECTIVE SUCCESSOR AUTHORIZATION DESIGN = ACCEPTED / FROZEN, PATH-F CORRECTIVE SUCCESSOR EXECUTION AUTHORIZATION = CONDITIONALLY ACCEPTED / NOT YET EFFECTIVE, PATH-F CORRECTIVE SUCCESSOR EXECUTION-AUTHORIZATION EFFECTIVITY = PENDING INDEPENDENT CONFIRMATION AND EXPLICIT MATERIALIZATION, PATH-F CORRECTIVE SUCCESSOR AUTHORIZATION DESIGN REVIEW = APPROVED, PATH-F CORRECTIVE SUCCESSOR AUTHORIZATION DESIGN ACCEPTANCE BOOKKEEPING = RECORDED, PATH-F CORRECTIVE SUCCESSOR AUTHORIZATION CONFIRMATION = REQUIRED / NOT YET PERFORMED and PATH-F CORRECTIVE SUCCESSOR AUTHORIZATION MATERIALIZATION = NOT PERFORMED.  **Execution remains closed until confirmation:** PATH-F OPERATIONAL USABILITY = BLOCKED; PATH-F EXECUTION AUTHORITY = NONE; PATH-F AUTHORIZATION USE = 1 OF 1 / 0 OF 1 CONSUMED / NOT AVAILABLE FOR CONSUMPTION; PATH-F ETB ATTEMPT = 1 OF 1 / 0 OF 1 STARTED / NOT AVAILABLE FOR CONSUMPTION; ORACLE-PATHF INVOCATION = 0 OF 1 / NOT AUTHORIZED; PATH-F CLAIMS = ABSENT (4 / 4); PATH-F RUNTIME OCCUPANCY = 0 / 11; the claim schemas devrelay-etb-path-f-authorization-use-v1 and devrelay-etb-path-f-attempt-use-v1 and the frozen writer Write-DevRelayPathFOneShotClaim are unchanged; no claim TEMP or FINAL file was created; no budget file was created; no evidence, manifest or result was created; no listener was queried; no target or endpoint was probed; and no ACL was read, changed, restored or normalized.  **Budget carry-forward model preserved:** PATHF_CORRECTIVE_BUDGET_CARRY_FORWARD_MODEL = SAME LINEAGE-LEVEL ONE-SHOT BUDGETS CARRIED FORWARD, IDENTITY RE-BOUND TO THE NEW ACCEPTED CORRECTIVE AUTHORIZATION, NO SECOND BUDGET, NO RESET, NO AUTOMATIC REUSE; the two lineage-level one-shot budgets remain UNCONSUMED / UNSTARTED / NOT OPERATIONALLY USABLE YET until confirmation and materialization establish corrective-authorization effectivity, and this round created, consumed, reset or replaced nothing.  **Supersession chain recorded without rewriting history:** the historical original authorization `ed112f8c5f1e35d87092d0339698a792ce0b145a` / `c147af8714164dae8b81cafa4eb01945a3ceb8c74b36f0fc18fbd56db284c4de` stays ACCEPTED / FROZEN / EFFECTIVE / OPERATIONALLY BLOCKED AFTER THE PRE-16 STOP, unrevoked and unrewritten; the first corrective candidate `d895856d2efc9683b91b182c33647efe57b01fc3` / `c281f93e6ddfe09351c435e698c5d50c3a5cfcda2053f27159ba921e2eed72eb` remains REQUEST_CHANGES / P2 = 1 / NOT ACCEPTED / NOT FROZEN / NOT EFFECTIVE / SUPERSEDED PROSPECTIVELY and is **not** relabelled as accepted; this bounded P2-remediation successor `89d8a7c…` / `3dbc20a5…` is now ACCEPTED / FROZEN BY THIS BOOKKEEPING ROUND **but NOT YET EFFECTIVE FOR OPERATIONAL USE**.  No historical object is erased, revoked, amended or relabelled, and no historical status surface is rewritten by this round.  **Identity and future claims:** after later effectivity any future Path-F claim must bind path_f_authorization_commit = `89d8a7c851dca935c8ed119c13cca1e446e6c232` and path_f_authorization_sha256 = `3dbc20a5dd1324f558a3c9c0644141928c07951062a6279502d2bc930758d628`, must **not** bind `ed112f8c…` / `c147af87…` and must **not** bind `d895856…` / `c281f93e…`; no claim is created by this round.  **Provenance boundary preserved:** MODEL_2_EXTERNAL_LINEAGE_BINDING is preserved; executor-owned claims will later bind the frozen lineage identities externally; Oracle-generated evidence remains governed by the frozen Oracle-PathF specification; no Oracle-generated oracle_path_f_commit / oracle_path_f_spec_sha256 / oracle_path_f_script_sha256 field is required to cease being the literal UNKNOWN where the frozen Oracle model reserves UNKNOWN; and no post-hoc evidence rewrite is permitted or performed.  **Predecessor boundary preserved:** PATH-E LINEAGE = EXHAUSTED / CLOSED; PATH-E RAW RESULT = BLOCKED / NON-PROMOTABLE; PATH-E ETB SEMANTIC RESULT = NONE; PATH-E RETRY AUTHORITY = NONE; PATH-E RUNTIME OCCUPANCY = 6 / 11 unchanged; PATH-D = EXHAUSTED / CLOSED / IMMUTABLE with zero Path-D reuse; the exactly eleven-path Path-F runtime namespace, the exclusively Oracle-PathF-owned listener / target / probe / classification boundary and the closed three-class result model are unchanged; and AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED with no ETB observation, no promotion and no authoritative-result replacement.  **Confirmation-recursion and materialization-authority rule preserved:** CONFIRMATION RECURSION = NONE, and a read-only confirmation verdict does **not** by itself become repository-verifiable effectivity where precedent requires tracked materialization — **no tracked confirmation materialization may be created without a separate, explicit Owner authorization naming that materialization round**, and the historical materialization-authority gap is not repeated by this round.  **This acceptance-bookkeeping round performed** 0 Oracle-PathF executions, 0 Oracle-PathE executions, 0 Oracle-PathD executions, 0 ETB executions, 0 listener queries, 0 Get-NetTCPConnection calls, 0 port-4096 probes, 0 localhost / 127.0.0.1 probes, 0 endpoint probes, 0 OpenCode starts/restarts, 0 HTTP / provider / model calls, 0 claim creations, 0 budget creations, 0 budget consumptions, 0 evidence / manifest / result creations, 0 Path-F runtime artifact creations, 0 Path-E or Path-D modifications, 0 frozen Oracle-PathF artifact modifications, 0 accepted-artifact mutations, 0 authorization-artifact modifications and 0 runtime / test / dependency / version changes; the tracked mutation surface is exactly `M CHANGELOG.md` and `M docs/v0.3/V03E_ACCEPTANCE.md`, and the acceptance-bookkeeping commit is the single-parent successor of `89d8a7c851dca935c8ed119c13cca1e446e6c232`.  Process disclosure: because residual ACL restrictions on `docs` and `docs\v0.3` deny ordinary sandboxed writes, the status-surface writes and the staging / commit operation of this governance-bookkeeping round used harness escalation; escalation is a mechanical path that changes no content, creates no authority and has no operational effect, and it does **not** establish `danger-full-access` for Path-F operational execution, does **not** satisfy `PRE-16`, grants no execution or retry authority, consumes no budget and changes no ACL state.  **Exact next stage:** FRESH THIRD-PARTY INDEPENDENT CONFIRMATION OF THE BOUNDED P2-REMEDIATION SUCCESSOR PATH-F ETB EXECUTION-AUTHORIZATION DESIGN ACCEPTANCE BOOKKEEPING, which must run in a different agent/session from this acceptance-bookkeeping-author session — no independent confirmation, no confirmation materialization, no claim creation, no budget creation or consumption and no execution is performed in this round.  No tag, no release and no push occurred.
**PATH-F CORRECTIVE SUCCESSOR ETB EXECUTION-AUTHORIZATION DESIGN ACCEPTANCE-BOOKKEEPING STATE-TOKEN CORRECTION — OWNER-GOVERNED BOUNDED CORRECTIVE DISPOSITION (explicit Owner-authorized governance-correction round; governance only; nothing executed, nothing retried, no budget created / consumed / reset / replaced, no claim created, no runtime namespace occupied, no Path-F runtime artifact created, no reviewed artifact modified, no accepted artifact modified, no frozen Oracle-PathF artifact modified, no operational authority created, no independent confirmation performed, no confirmation materialized, no result promoted, Path-D not reopened, Path-E not reopened).**  **EXACT DEFECT BOUND (sole blocking P2).**  The fresh third-party independent confirmation of the acceptance-bookkeeping commit `335c10b9fb43178e38f48975610143bf3477174e` (parent `89d8a7c851dca935c8ed119c13cca1e446e6c232`, tree `08215a4c003ebe1b0cab4ca1e01299ec7238ffdf`, subject `docs(v03e): accept Path-F ETB authorization`) was performed read-only in a different agent/session and returned `REQUEST_CHANGES` with severity `P0 = 0, P1 = 0, P2 = 1, P3 = 1`. Its sole blocking finding is **`P2-1 = BOOKKEEPING STATE TOKEN PREMATURELY ADVANCED`**.  The defect is localized and purely token-level: the two status surfaces committed by `335c10b` assert `...immediately after this bookkeeping the state is PATH-F CORRECTIVE SUCCESSOR AUTHORIZATION DESIGN = ACCEPTED / FROZEN, PATH-F CORRECTIVE SUCCESSOR EXECUTION AUTHORIZATION = CONDITIONALLY ACCEPTED / NOT YET EFFECTIVE...` and conclude `...is now ACCEPTED / FROZEN BY THIS BOOKKEEPING ROUND but NOT YET EFFECTIVE FOR OPERATIONAL USE.`  The design-state token `ACCEPTED / FROZEN` advances the derived state one full lifecycle stage ahead of the directly governing acceptance-bookkeeping stage, whose direct-precedent form is **`CONDITIONALLY ACCEPTED / NOT YET FROZEN / NOT YET EFFECTIVE`** until a fresh independent confirmation of the bookkeeping and a separate explicit Owner-authorized tracked confirmation materialization have both occurred.  **NON-DEFECTIVE SENTENCES IN THE SAME RECORD (explicitly preserved, deliberately NOT corrected).**  The same `335c10b` surfaces correctly state that the corrective-successor execution authorization `becomes ACCEPTED / FROZEN / EFFECTIVE **only** after a fresh independent confirmation of THIS bookkeeping commit performed in a different agent/session, followed by the precedent-required tracked materialization of that confirmation`; they correctly carry `ORACLE-PATHF DESIGN = ACCEPTED / FROZEN / EFFECTIVE` (the Oracle design genuinely is frozen and effective); and they correctly carry the historical original authorization `ed112f8c5f1e35d87092d0339698a792ce0b145a` as `ACCEPTED / FROZEN / EFFECTIVE / OPERATIONALLY BLOCKED AFTER THE PRE-16 STOP`.  This corrective round changes none of those and does not reopen the accepted design.  **DIRECT CORRECTIVE PRECEDENT REVALIDATED (shape determinative; no new structure invented and no third tracked path created).**  Recovered mechanically from the governing lineage before mutation. The Path-F acceptance-bookkeeping precedent `1de258ff8fb0e4113d2eab73e13b51e502cd20fe` states verbatim that `this commit is acceptance-bookkeeping provenance only and freezes or effectuates nothing; the authorization becomes ACCEPTED / FROZEN / EFFECTIVE only after a fresh independent confirmation of THIS bookkeeping commit in a different agent/session plus the precedent-required tracked materialization, so immediately after this bookkeeping the state is PATH-F ETB EXECUTION AUTHORIZATION = CONDITIONALLY ACCEPTED / NOT YET FROZEN / NOT YET EFFECTIVE (the established repository form for the acceptance-bookkeeping stage, recovered from the Path-D precedent)` with `PATH-F AUTHORIZATION CONFIRMATION = REQUIRED`; the Path-D analogue `a7e3ccc` records `PATH-D AUTHORIZATION ACCEPTANCE BOOKKEEPING = COMMITTED / PENDING INDEPENDENT CONFIRMATION` and `PATH-D AUTHORIZATION = CONDITIONALLY ACCEPTED / NOT YET FROZEN / NOT YET EFFECTIVE`; the Path-E analogue `48e9b66` records `PATH-E EXECUTION AUTHORIZATION = CONDITIONALLY ACCEPTED / NOT YET FROZEN / NOT YET EFFECTIVE` with `PATH-E AUTHORIZATION USE = NOT AVAILABLE FOR CONSUMPTION`; and the bare `ACCEPTED / FROZEN / EFFECTIVE` token for a design appears only in the later tracked confirmation-materialization rounds (`62a4098` for Path-F, `c1d7bd3` for Path-D, `c7ac36a` for Path-E). Therefore `CORRECTIVE_BOOKKEEPING_STATE_PRECEDENT = DETERMINATIVE`, `ACCEPTANCE-BOOKKEEPING STAGE = CONDITIONALLY ACCEPTED / NOT YET FROZEN / NOT YET EFFECTIVE`, `INDEPENDENT CONFIRMATION = REQUIRED`, `TRACKED CONFIRMATION MATERIALIZATION = REQUIRED`, `ACCEPTED / FROZEN / EFFECTIVE = ONLY AFTER THE ORDERED CONFIRMATION + MATERIALIZATION LIFECYCLE`.  The corrective-successor shape itself is the established repository form: exactly one single-parent governance successor commit whose sole tracked delta is exactly `M CHANGELOG.md` plus `M docs/v0.3/V03E_ACCEPTANCE.md`, no third tracked path — the shape realized by `302dd74 docs(v03e): correct Oracle-PathE design acceptance authority`, `d921dc9 docs(v03e): reconcile Oracle-PathE confirmation materialization authority` and `1dd35b4`, and the supersession is declared only inside this successor record.  **Corrected bookkeeping state tokens (this record is the latest resolved current state for these surfaces; prior chronology is preserved and no earlier entry is deleted, rewritten or amended).**  `89d8a7c BOUNDED P2-REMEDIATION SUCCESSOR DESIGN = CONDITIONALLY ACCEPTED / NOT YET FROZEN / NOT YET EFFECTIVE`; `PATH-F CORRECTIVE SUCCESSOR AUTHORIZATION DESIGN = CONDITIONALLY ACCEPTED / NOT YET FROZEN / NOT YET EFFECTIVE`; `CORRECTIVE SUCCESSOR EXECUTION-AUTHORIZATION EFFECTIVITY = PENDING FRESH INDEPENDENT CONFIRMATION OF THE CORRECTED BOOKKEEPING AND SUBSEQUENT EXPLICIT TRACKED MATERIALIZATION / NOT YET EFFECTIVE`; `PATH-F OPERATIONAL EXECUTION = BLOCKED`; `PATH-F OPERATIONAL USABILITY = BLOCKED`; `PATH-F EXECUTION AUTHORITY = NONE`; `PATH-F CLAIM CREATION AUTHORITY = NONE`; `PATH-F BUDGET CONSUMPTION AUTHORITY = NONE`; `ORACLE-PATHF INVOCATION AUTHORITY = NONE`.  Where a surface committed by `335c10b` states `ACCEPTED / FROZEN` for the current bookkeeping-stage design state, that token is **historical, overstated and prospectively superseded** by this corrective record and is **not** the current state; the current state is the direct-precedent form stated above.  **Disposition of the defective commit (no history rewrite).**  `335c10b` was a valid acceptance-bookkeeping **attempt** with the correct accepted design identity and the correct two-surface mutation shape; no accepted artifact byte was wrong, no accepted commit or SHA binding was wrong, no qualifying review binding in the committed surfaces was wrong, no operational effect resulted, and no budget, claim, Oracle or runtime action occurred.  It returned `REQUEST_CHANGES` on a single bookkeeping-state token, is **not** amended, reset, rebased, reparented or erased, and remains a permanent historical lineage node superseded prospectively by this corrective governance record only.  `PATH-F CORRECTIVE SUCCESSOR AUTHORIZATION DESIGN = ACCEPTED / FROZEN` is **not** used as the current bookkeeping-stage design state and `EFFECTIVE` is **not** used for the corrective successor authorization.  **Supersession chain (composite bookkeeping lineage confirmed by the next stage as `89d8a7c` → `335c10b` → this corrective bookkeeping-state successor).**  `STAGE 0` historical original authorization `ed112f8c5f1e35d87092d0339698a792ce0b145a` = `ACCEPTED / FROZEN / EFFECTIVE / OPERATIONALLY BLOCKED AFTER PRE-16 STOP`; `STAGE 1` `d895856d2efc9683b91b182c33647efe57b01fc3` = `REQUEST_CHANGES / SUPERSEDED PROSPECTIVELY / NOT ACCEPTED / NOT EFFECTIVE`; `STAGE 2` `89d8a7c851dca935c8ed119c13cca1e446e6c232` design = `QUALIFYING REVIEW APPROVED / CONDITIONALLY ACCEPTED / NOT YET FROZEN / NOT YET EFFECTIVE`; `STAGE 3` `335c10b9fb43178e38f48975610143bf3477174e` bookkeeping = `HISTORICAL BOOKKEEPING COMMIT / FRESH CONFIRMATION REQUEST_CHANGES / P2 STATE-TOKEN DEFECT / SUPERSEDED PROSPECTIVELY BY THIS CORRECTIVE GOVERNANCE RECORD`.  **Non-blocking finding disposition.**  The confirmation's `P3-1 = REPORT-LEVEL V03 DUPLICATION` is `NONBLOCKING`, `REPORT-PROSE ONLY`; the committed bookkeeping verdict binding is `EXACT` and **no repository repair is required or performed for this P3** — no fake repository correction is inserted for a defect that exists only in the earlier prose report.  **Preserved without change.**  `APPROVE V0.3 PATH-F BOUNDED P2-REMEDIATION SUCCESSOR ETB EXECUTION-AUTHORIZATION DESIGN CANDIDATE — QUALIFYING THIRD-PARTY INDEPENDENT REVIEW` with `P0 = 0, P1 = 0, P2 = 0, P3 = 3` and all its accepted findings are preserved verbatim; the accepted authorization-design identity remains exactly `path_f_authorization_commit = 89d8a7c851dca935c8ed119c13cca1e446e6c232`, `path_f_authorization_sha256 = 3dbc20a5dd1324f558a3c9c0644141928c07951062a6279502d2bc930758d628`, artifact `docs/v0.3/V03E_G0_5_PRE_ETB_PATH_F_AUTHORIZATION.md`, 124650 bytes, blob `16fd027f5af40f08dc33ad43228566a894dde518`, byte-identical at the design commit, at `335c10b` and in the worktree; this corrective governance commit is **not** bound as the authorization design and neither `335c10b` nor any later confirmation or materialization commit is substituted for it.  Reopened: nothing — `danger-full-access`, `sandbox:policy`, `PRE-16`, `PRE-17`, `PRE-18`, the budget carry-forward model, future claim identity, Oracle ownership, the namespace and the result-class model are all untouched.  `REQUIRED PATH-F DSH OPERATIONAL EXECUTION / FILE-ACCESS MODE = danger-full-access` with observation channel `DSH sandbox:policy` runtime-context declaration and required visible token `Current DSH file policy: danger-full-access.`; `PRE-16 = SATISFIABLE_AND_DETERMINISTIC`; `PRE-17 = COHERENT_AND_NON_PROBING`; `PRE-18 = EXPLICIT_AND_CLOSED`.  The confirmation's governance finding is preserved as `BOOKKEEPING_GOVERNANCE_MODE_TRANSITION = FINDINGS` with `OPERATIONAL_EFFECT_OF_TRANSITION = NONE`, `PRE16_EFFECT_OF_TRANSITION = NONE` and `BOOKKEEPING_MODE_COUNTER_ACCURACY = ACCURATE`; the session-scoped runtime-context transition reported by the `335c10b` author was not repository-verifiable and was not load-bearing, and no mode-transition correction is invented here.  **Budget and claim state (unchanged).**  `PATHF_CORRECTIVE_BUDGET_CARRY_FORWARD_MODEL = SAME LINEAGE-LEVEL ONE-SHOT BUDGETS CARRIED FORWARD, IDENTITY RE-BOUND TO THE NEW ACCEPTED CORRECTIVE AUTHORIZATION, NO SECOND BUDGET, NO RESET, NO AUTOMATIC REUSE`; `PATH-F AUTHORIZATION USE = 1 OF 1 / 0 OF 1 CONSUMED / NOT AVAILABLE FOR OPERATIONAL USE`; `PATH-F ETB ATTEMPT = 1 OF 1 / 0 OF 1 STARTED / NOT AVAILABLE FOR OPERATIONAL USE`; `PATH-F CLAIMS = ABSENT 4 / 4`; `PATH-F RUNTIME OCCUPANCY = 0 / 11` (all eleven reserved paths of the frozen namespace verified absent under the `File.Exists`-or-`Directory.Exists` occupancy predicate); `ORACLE-PATHF INVOCATIONS = 0 OF 1 / NOT AUTHORIZED`.  No claim was created, no budget file was created, no budget was consumed or reset.  After later successful confirmation and materialization, future Path-F claims bind `authorization_commit = 89d8a7c851dca935c8ed119c13cca1e446e6c232` and `authorization_sha256 = 3dbc20a5dd1324f558a3c9c0644141928c07951062a6279502d2bc930758d628` — never `ed112f8c…` / `c147af87…`, never `d895856…` / `c281f93e…`, never `335c10b…` and never this corrective bookkeeping commit.  **Oracle, result, ownership and predecessor boundary (preserved exactly).**  `ORACLE-PATHF DESIGN` = `a5d598a05a0467eea98cd0bf16e4486cceb72c23`; Oracle specification = 34308 bytes / `b07a822b9b1447c65c60a6707f0f2ece2edec1c9b9c4bdee75d224993bf4f4e5`; Oracle script = 49704 bytes / `4c30a68204d46ffcc875265de31e55e0a8fb70b9f0b33b5783fa28ca6eaa25b0`; `MODEL_2_EXTERNAL_LINEAGE_BINDING = PRESERVED`; listener / target ownership = `EXCLUSIVE TO ORACLE-PATHF`; result classes remain exactly `ETB_SATISFIED`, `ETB_UNSATISFIED` and `HARNESS_INVALID / NO ETB SEMANTIC RESULT`; `AUTHORITATIVE ETB SEMANTIC RESULT = ETB_UNSATISFIED / PRESERVED` with no promotion; `PATH-E = EXHAUSTED / CLOSED` with `PATH-E RETRY = NONE` and `PATH-E RUNTIME OCCUPANCY = 6 / 11` unchanged; `PATH-D = EXHAUSTED / CLOSED / IMMUTABLE`; no cleanup, no reuse, no repair, no result promotion and no reopening of any predecessor lineage.  **Mutation surface and process boundary.**  The tracked mutation surface of this corrective round is exactly `M CHANGELOG.md` and `M docs/v0.3/V03E_ACCEPTANCE.md`; there is no third tracked path, and the accepted authorization artifact, the two frozen Oracle-PathF artifacts, the Oracle specification, the Oracle executable, `.gitattributes`, claims, the runtime namespace, source, tests, dependencies, version files and all Path-D and Path-E artifacts are untouched.  This corrective round amends no commit, performs no reset, no rebase and no reparenting, and creates no confirmation, no materialization, no execution, no claim, no budget and no Oracle invocation.  **NO SELF-REFERENCE:** this record embeds neither its own commit id nor its own tree; the corrective bookkeeping-state commit is identified mechanically by its parent `335c10b9fb43178e38f48975610143bf3477174e`, its subject and its delta.  **Exact next stage:** FRESH THIRD-PARTY INDEPENDENT CONFIRMATION OF THE CORRECTED BOUNDED P2-REMEDIATION SUCCESSOR PATH-F ETB EXECUTION-AUTHORIZATION DESIGN ACCEPTANCE BOOKKEEPING, which must run in a genuinely new top-level DSH session and must confirm the corrected state-token record and the composite bookkeeping lineage `89d8a7c851dca935c8ed119c13cca1e446e6c232` → `335c10b9fb43178e38f48975610143bf3477174e` → this corrective bookkeeping-state successor.  No independent confirmation, no confirmation materialization, no claim creation, no budget creation or consumption, no Oracle invocation, no listener query, no target probe, no endpoint probe, no ACL mutation, no ACL restoration, no permission normalization, no result promotion and no operational execution is performed in this round; 0 Oracle executions, 0 ETB executions, 0 listener queries, 0 endpoint probes, 0 claims, 0 budgets, 0 evidence / manifest / result creations, 0 Path-F runtime artifact creations, 0 accepted-artifact mutations and 0 runtime / test / dependency / version changes.  No tag, no release and no push occurred.

## Unreleased - v0.3-D accepted (bounded orchestration)

Durable, **bounded** orchestration state over the accepted v0.3-C role path: a
Planner creates a run, explicitly runs each phase, and records its own decision -
DevRelay remembers where the run is, enforces a hard cycle bound and fails closed
on uncertainty.  **Accepted internally, closed and unreleased** at candidate
`8b70610a5cdda600ef57cf8378c4f69cd33d5be4` after two independent remediations and
one authorized bounded real orchestration smoke (`PASS — V0.3-D REAL BOUNDED
ORCHESTRATION SMOKE`): the package version stays `0.1.0`, the supported public
release remains `v0.1.0`, there is no `v0.3-D` tag, nothing is pushed, merged,
tagged or published, and v0.3-E has not started.

### Added

- **`src/devrelay/orchestration/`** (`models.py`, `store.py`, `state_machine.py`,
  `service.py`): the explicit run states (`READY_IMPLEMENTER`, `READY_REVIEWER`,
  `AWAITING_DECISION`, `COMPLETED`, `STOPPED`, `BLOCKED`, `LIMIT_REACHED`), hard
  bounds (`max_cycles` 1..3 with `HARD_MAX_CYCLES = 3`, default 2, model-turn
  budget `2 x max_cycles`, absolute ceiling six turns), a strict durable run
  document with a Planner-complete summary, a single-writer atomic store under
  `.devrelay/orchestration/runs/<run_id>.json`, a pure transition policy and the
  service that binds them to the accepted role router and bridge.
- **Five MCP tools** (the accepted twelve unchanged, total **17**):
  `devrelay_start_run` (two existing role sessions + `max_cycles`; no model call),
  `devrelay_get_run` (read-only, local), `devrelay_run_implementer` and
  `devrelay_run_reviewer` (one explicit phase turn each) and
  `devrelay_decide_run` (`complete` | `request_changes` | `stop`; no model call).
  All five share the accepted execution boundary, so one MCP surface still
  serializes all seventeen tools.
- **Durable audit**: previous/next state, timestamp, action, external vs
  model-bearing source, cycle, role, prompt digest and length, resolved
  model/agent, call ids, submission status/flags, uncertainty/pending and
  assistant message ids - never a raw prompt, provider reply, model reasoning or
  credential.
- **Fail-closed bounds**: an uncertain, pending or failed phase blocks the run
  (no retry, no fallback, no role switch, no automatic interrupt); a changed **or
  unresolvable** role route or an ownership loss fails the run closed with zero
  model POST; a persisted in-flight turn is never replayed; a corrupt run document
  is reported as `orchestration_state_corrupt` and never reset.
- **255 offline tests** (154 at the candidate, 101 added by the remediation)
  plus the v0.3-D spec and acceptance matrix.

### Notes

- **The external Planner stays authoritative.**  DevRelay never parses reviewer
  prose (`APPROVE`/`REQUEST_CHANGES`/anything else) to choose a state: a
  successful reviewer turn always stops at `AWAITING_DECISION`, and only an
  explicit decision (recorded with `source = external_planner`) advances the run.
- **Still no automatic sequencing**: no automatic implementer -> reviewer call, no
  repair loop, no scheduler, no background runner, no semantic judgement of review
  content, no automatic acceptance or merge, no session creation.
- **Backward compatibility**: the accepted v0.3-A/B/C behaviour is unchanged; the
  raw `opencode_send_prompt` and role `devrelay_send_role_prompt` paths are
  untouched, and the only test-expectation updates are the intended tool
  inventory (12 -> 17) and the advertised server version (`0.3.0-c` -> `0.3.0-d`).
### Remediation (independent gate: `REQUEST_CHANGES`, P0 = 0, one blocking P1)

The first v0.3-D candidate trusted persisted run state as input.  Fixed at the
model/store load boundary rather than by adding checks to `start_run`:

- **Persisted state is untrusted input** (`src/devrelay/orchestration/invariants.py`):
  every load *and* every save re-derives the invariants the state machine
  guarantees - fixed schema version, `1 <= max_cycles <= 3`, budget `2 x
  max_cycles`, counters consistent with the recorded turns, `turn_attempts ==
  model_turns_used`, every reserved slot accounted for by a finished turn or the
  live in-flight intent, two distinct non-blank sessions, a complete and mappable
  two-role snapshot, one turn per role per cycle with the implementer first,
  `completed_cycles` equal to the completed reviewer turns, the state/cycle
  relation, `LIMIT_REACHED` only at the cap with `blocked_reason=cycle_limit`,
  `BLOCKED` only with a reason, the in-flight shape (matching `READY_*` state,
  current cycle, `outcome=in_flight`, snapshot model, well-formed prompt
  evidence), an external-only decision history consistent with the current state,
  and start provenance that claims no previous state.  Anything else is
  `orchestration_state_corrupt`: refused, never repaired, never migrated, never
  rewritten, never able to reach a model call.  The store additionally requires
  transition provenance for a persisted document and binds it to its workspace.
- **The gate's four reproductions are refused**: `max_cycles=99`/budget 198 cannot
  run a single extra turn, identical role sessions are rejected, `max_cycles=1000`
  cannot open five cycles, and `AWAITING_DECISION` with `completed_cycles=0` and
  no reviewer turn cannot open one.  A 20-case tamper matrix plus 22 additional
  corruption cases assert this, including that the file is byte-identical after
  every refused attempt.
- **An unresolvable role route** (role removed, or its configured route invalid)
  now fails an existing run closed with `orchestration_route_changed`, durable
  `BLOCKED`/`blocked_reason=route_changed`, an immutable snapshot and zero model
  POST; at `start_run` there is nothing durable to block, so the same failure is
  reported as `orchestration_route_changed` with no run created.
- **An interrupted turn keeps its audit trail**: the sanitized attempt is
  finalized as `blocked`/`turn_interrupted` and appended to the role history (so
  the reserved slot keeps a matching record and the transition keeps the phase
  action and role) before the run fails closed; `legal_next_actions` is empty while
  an intent is live.
- **The durable in-flight intent provably precedes submission**: a transport-level
  callback observes the on-disk document at the exact moment the prompt POST is
  sent (no sleeps, no polling), and a real process death (`SystemExit`) at
  submission leaves a loadable in-flight document that a fresh surface
  materializes into an auditable `BLOCKED` run.  The previously undetected
  Mutation F (bypassing the pre-call save) now fails four tests.
- **Accounting, vocabulary and identity wording**: `model_turns_used` is
  documented and tested as *consumed slots* that are never refunded (a ten-kind
  failure matrix asserts one slot, one turn record, no retry); turn `outcome` is
  constrained to `in_flight`/`completed`/`blocked`; run ids are matched with a
  strict full match; and the docs/status no longer overclaim (atomic against a
  crash of this process, **no** power-loss `fsync` claim; the execution lock is
  per tool surface, the shipped stdio server builds exactly one surface, and
  multiple surfaces or processes are unsupported).
- **Recorded, not fixed (P3)**: the MCP SDK's lax argument model normalizes JSON
  `true`/`"2"`/`2.0` to integers before the tool body (and refuses `1.5`), so a
  boolean `max_cycles` reaches the body as `1`.  DevRelay still rejects a real
  `bool` at its own boundary and the 1..3 ceiling can never be raised (`false`
  normalizes to 0 and is refused).

### Second remediation (independent gate: P0 = 0, three blocking P1s)

The second gate proved that a persisted run only had to have *plausible fields*.
Three exploits are closed by making the current state **provable from the
persisted history** (turn history, decision history, counters, transition
provenance, cycle structure and in-flight intent), still with **0 real model
calls** and still **NOT ACCEPTED at that point** (historical: v0.3-D was
accepted later in this same Unreleased section, after the smoke in the next
subsection):

- **P1-A**: `READY_REVIEWER` - and a live reviewer in-flight intent - now requires
  exactly one **completed** implementer turn in the current cycle.  A forged
  reviewer phase used to reach `POST /session/<reviewer>/message` before the
  post-call save noticed; it is now `orchestration_state_corrupt` at the load
  boundary with zero requests and a byte-identical file.
- **P1-B**: a historical `blocked` turn implies `BLOCKED` (a failed phase fails the
  run closed and nothing reopens it), so a blocked turn can no longer sit inside an
  active or completed run; a completed reviewer turn also requires exactly one
  completed implementer turn in the same cycle.  All five honest `BLOCKED` variants
  (implementer failure, reviewer failure, route change, interrupted implementer,
  interrupted reviewer) stay valid.
- **P1-C**: an exhausted `max_cycles=3` run rolled back toward cycle 1 can no
  longer spend again.  The validator now requires the last transition to be a real
  state-machine edge **ending at the current state** (with the action, previous
  state, role and cycle that edge implies), the decision history to equal
  `completed_cycles - (1 if AWAITING_DECISION else 0)`, every decision to be a legal
  `AWAITING_DECISION` edge whose terminal decision is last, the opened cycles to
  equal `current_cycle - 1`, no turn from a future cycle, and the persisted spend
  to be possible for the cycle structure (`model_turns_used <= 2 x current_cycle`).
  Ten rollback variants (counters/history/decisions reset in every combination,
  stale or rewritten transition, missing `request_changes`, fabricated cycle 3,
  future-cycle turn, terminal-to-active rollback, reviewer evidence without
  implementer evidence, blocked turn injected into a completed history) are all
  refused before any submission.
- **Strict persisted types**: `schema_version` and `model_turn_budget` are required
  (no default) and `schema_version`, `max_cycles`, `current_cycle`,
  `completed_cycles`, `turn_attempts`, `model_turn_budget`, `model_turns_used` (plus
  per-turn `cycle`/`prompt_chars` and the transition cycle) are strict integers, so
  a persisted `"2"`, `2.0`, `true`, `false`, `null` or a missing `schema_version`
  is a malformed document - never a coerced number, never a migration.
- **Turn audit consistency**: finished turns need a valid `completed_at`, a
  lowercase sha256 prompt digest, a positive prompt length, no `blocked_reason`
  when completed and a non-empty one when blocked; an in-flight intent claims
  neither completion nor a blocked reason; `resolved_model`, `resolved_agent` and
  `route_source` must all agree with the captured snapshot.
- **Honest corpus and differential proof**: a new production-generated corpus
  (`tests/v03d_corpus.py`, 19 states including both in-flight roles in cycles 1-2
  and all five `BLOCKED` shapes, with crash boundaries produced by a real
  `SystemExit`) must load, re-save, restart and reload unchanged, and each member
  must reject a 15-mutation battery one mutation at a time.  The hand-written
  in-flight fixtures were replaced by the real crash path.
- **Save-side invariants** are covered directly (state/history relation, identical
  sessions, budget, decision history): an impossible in-memory run cannot be
  written, and the previous document stays byte-identical.
- **Truthfulness fixes**: failure messages are shaped from the recorded
  `submission_attempted`/`submission_uncertain`/`reply_pending`/`submission_status`
  evidence (a connect error is no longer described as uncertain); the
  `devrelay_run_implementer` description explains that a persisted interrupted
  phase is first materialized into `BLOCKED`; `devrelay_get_run` says an
  unreachable document is refused as corrupt; the lock scope is stated per tool
  surface with `lock_scope`/`surfaces`/`multiple_surfaces_or_processes` status keys;
  the model-turn ceiling is described as six reserved/consumed **slots** (at most
  six POST attempts); atomic file replacement no longer implies hard-kill cleanup
  (an inert `.tmp` file is never listed or honoured, and no `fsync`/power-loss
  durability is claimed).
- **Recorded P3s**: the MCP SDK pre-parses JSON-looking *string* prompts
  (`{"task": ...}`) into dict/list and refuses them at its own boundary with **no
  submission** (a `str`-only annotation would break the documented
  `mcp_invalid_argument` envelope, so it is recorded rather than changed); and the
  honest bound of self-contained validation - a fully rewritten but internally
  consistent history cannot be distinguished from an honest one without an external
  integrity anchor (no journal or chain is added).
- **Tests**: the v0.3-D suite grows from 255 to **357** (the new reachability suite
  plus the corpus), the full offline suite from 1064 to **1166**, with mutations
  A-K all detected (A 105, B 19, C 6, D 104, E 6, F 18, G 3, H 2, I 4, J 4, K 4;
  control 357 v0.3-D tests green).

### Accepted — one bounded real orchestration smoke (`PASS`)

The single authorized real run was executed against real OpenCode and real provider
inference and passed: **`PASS — V0.3-D REAL BOUNDED ORCHESTRATION SMOKE`**
(candidate `8b70610a5cdda600ef57cf8378c4f69cd33d5be4`, run id
`DR-dfb23a14e4654a5d9b75b296a27b1245`, 2026-09-17).

* **Exactly four real model-bearing turns** and **exactly four**
  `POST /session/{id}/message` submissions for `max_cycles = 2`: implementer c1
  (`opencode-go/deepseek-v4.1-flash`), reviewer c1 (`opencode-go/glm-5.3-flash`),
  implementer c2, reviewer c2 - four-way route agreement (configuration =
  `devrelay_get_role` = durable `resolved_model` = provider runtime log);
* **0 retries, 0 fallbacks, 0 automatic role calls, 0 interrupts/aborts, and no
  fifth model turn**; `model_turns_used = 4` of `model_turn_budget = 4`; ledger
  final state 30 records, all `COMPLETED`, 0 `ISSUED`;
* **reviewer authority proved against real prose:** the cycle-1 provider answer
  `REQUEST_CHANGES` left the run at `AWAITING_DECISION` with an empty decision
  history (only an explicit `devrelay_decide_run(request_changes)` opened cycle 2),
  and the cycle-2 provider answer `APPROVE` did **not** complete the run (only an
  explicit `devrelay_decide_run(complete)` produced `COMPLETED`).  Both decisions
  cost 0 model calls;
* **terminal guard proved without spending a fifth turn:** a repeated
  `devrelay_decide_run` on the terminal run returned
  `orchestration_invalid_transition` ("never reopened") with the state visible,
  unchanged, a byte-identical run file and 0 new POSTs, and the same document was
  re-checked offline with a throw-on-touch stub bridge that was never touched;
* **durability/privacy audit 45/45:** four completed durable turn records (two
  implementer, two reviewer, correct cycles), no in-flight intent at completion,
  unchanged route snapshot, prompt digests/lengths independently recomputed and
  matching (150/150/177/169), and no prompt, provider answer, reasoning or
  credential material anywhere under `.devrelay`;
* containment: both disposable sessions deleted, the dedicated OpenCode instance
  stopped, the user's own processes untouched, no MCP child process left, and the
  repository HEAD/branch/tag/working tree unchanged.

Carried findings stay recorded (they do not block acceptance): the accepted v0.3-A
reasoning-part normalization limitation, the information-only
`legal_next_actions` display shape, the derived (not persisted) `terminal` field,
the MCP SDK argument-normalization and JSON-shaped-string prompt boundaries, the
non-cryptographic bound of persisted-state validation, inert temp files after a
hard kill, read-only `get_run`, no `fsync`/power-loss durability, and no
multi-surface/multi-process coordination.  v0.3-E recovery remains explicitly out
of scope and not started.

- `MCP_SERVER_VERSION` is `0.3.0-d`.  v0.3-D is accepted/closed and unreleased; no
  further real orchestration smoke is authorized, and v0.3-E recovery is explicitly
  out of scope and not started.

## Unreleased - v0.3-C accepted (agent role routing)

Explicit, deterministic **role -> route resolution** on top of the accepted
v0.3-B MCP surface: an MCP caller selects a semantic role and DevRelay supplies
the exact workspace-configured model (and optional OpenCode agent).  **Accepted
internally / unreleased**: the accepted functional candidate is
`eabb667d1bd9e379d3b7105d72b6a2751bc2a32b`, the package version stays `0.1.0`, the
supported public release remains `v0.1.0`, nothing is pushed, merged, tagged or
published, and no public v0.3 release exists.

### Accepted (real role-routing smoke)

- Semantic roles are exactly `implementer` and `reviewer`, resolved from an
  immutable workspace `roles:` wiring section (`model` + optional `agent`;
  identifiers only - no prompts, credentials, endpoints, retries, fallbacks or
  candidate lists).
- The caller cannot influence the configured route: the role tool accepts only
  `role`, `session_id` and `prompt`; extra protocol members are ignored, and the
  effective route always comes from configuration (no default route, no fallback,
  no role switching).
- Three role-aware MCP tools (`devrelay_list_roles`, `devrelay_get_role`,
  `devrelay_send_role_prompt`) - total MCP inventory **12** - all routed through
  the one accepted global execution-serialization boundary.
- The raw `opencode_send_prompt` path is preserved unchanged, including its
  caller-supplied model/agent semantics.
- Real routing verified by two bounded runs: implementer →
  `opencode-go/deepseek-v4.1-flash` and reviewer → `opencode-go/glm-5.3-flash`,
  each with exactly one `devrelay_send_role_prompt`, exactly one real inference
  (OpenCode `1.18.11` provider log) and exactly one
  `POST /session/{id}/message`; three-way route agreement
  (`devrelay_get_role` = response `resolved_model_identity` = provider log);
  `ok=true`, `isError=false`, `submission_uncertain=false`,
  `reply_pending=false`, `retry_safe=false`; no retry, no fallback, no alternate
  model.
- No automatic acceptance, no review loops and no orchestration: an implementer
  completion did not invoke the reviewer, and the reviewer completion triggered
  nothing - each role ran only because it was explicitly invoked.
- Complete containment and cleanup in both runs: disposable workspace unchanged,
  disposable sessions deleted, dedicated OpenCode stopped, MCP process exited,
  evidence kept outside the repository.

### Added

- **`src/devrelay/roles/`** (`models.py`, `resolver.py`, `service.py`): the role
  vocabulary (`implementer`, `reviewer` - no generic taxonomy yet, no vendor or
  model identifier in code), a frozen `RoleRoute` value object (role, model,
  agent, source) with sanitized read-only/audit views, deterministic exact
  resolution, and `RoleRouter.send_role_prompt(bridge, role, session_id, prompt)`
  which resolves first and then delegates to the accepted
  `OpenCodeBridge.send_prompt`.
- **Local error taxonomy**: `role_unknown`, `role_unconfigured` and
  `role_invalid_route` (`CodedError` subclasses) - local routing failures raised
  before any request that could submit a model turn, never mislabeled as provider
  failures.
- **`roles:` workspace wiring section**: `roles.implementer` / `roles.reviewer`
  with `model` (`<providerID>/<modelID>`, the accepted grammar) and an optional
  `agent`.  Identifiers only: prompt templates, shell commands, environment
  variables, endpoint/workspace overrides, retry policies, fallback models,
  candidate lists and credentials are rejected by the schema.  Runtime wiring,
  never task policy (excluded from policy overrides; tolerated-and-dropped in
  legacy full-config dumps).  The section is optional - an existing v0.3-B
  workspace stays valid and `devrelay mcp serve` never refuses to start because
  role routing is absent.
- **Three MCP tools** (the accepted nine are unchanged, total 12):
  `devrelay_list_roles` (read-only), `devrelay_get_role` (read-only) and
  `devrelay_send_role_prompt` (`role`, `session_id`, `prompt` only).  Their
  descriptions state the routing contract: the caller selects the role, DevRelay
  resolves the exact configured model/agent, the route cannot be overridden,
  exactly one model turn is sent, nothing is retried, and a reviewer reply is
  provider text rather than an acceptance decision.
- **Role-routing evidence in the send envelope**: `role`, `resolved_model`,
  `resolved_model_identity`, `resolved_agent`, `route_source` alongside every
  accepted v0.3-A send field, so a planner can audit which role and route were
  used; an accepted bridge failure keeps its exact code and additionally reports
  the attempted route.
- **140 offline tests** (`tests/test_v03c_role_config.py`,
  `tests/test_v03c_roles.py`, `tests/test_v03c_role_tools.py`,
  `tests/test_v03c_role_concurrency.py`, `tests/test_v03c_stdio_roles.py`,
  `tests/v03c_helpers.py`) plus the v0.3-C spec/acceptance documents.

### Notes

- **No orchestration**: no automatic implementer -> reviewer sequencing, no
  repair loops, no retry loops, no automatic acceptance or rejection, no merge
  decisions, no Planner role inside DevRelay, no session creation or lifecycle
  management, no model ranking/fallback, no WebUI/HTTP control API.  The external
  planner still decides which role to call, when and what to do next.
- **Backward compatibility**: the raw `opencode_send_prompt` tool is byte-for-byte
  unchanged (caller-supplied model/agent still reach the wire, no role key in its
  envelope) and both paths can be used in the same session.  Role routing is
  never inferred from prompt text, session title or model availability.
- **The v0.3-B execution boundary still applies**: all twelve tool bodies run
  under the same one per-surface execution lock (no role lock, no scheduler), so
  the accepted single-writer filesystem ledger never sees concurrent access.
- `MCP_SERVER_VERSION` is `0.3.0-c` (the advertised surface changed from nine to
  twelve tools).  The real role-routed model smoke is **done** (see "Accepted
  (real role-routing smoke)" above); a first two-role harness run failed only
  because it required the whole normalized assistant text to equal a sentinel -
  real providers also return a reasoning part that the accepted v0.3-A
  normalization currently presents as `kind="text"` (recorded as a non-blocking
  P3 in `docs/BACKLOG.md`).  That history is preserved, not rewritten.

## Unreleased - v0.2-B project profiles (candidate under independent review)

Reusable project policy profiles on top of a frozen, integrity-verified task
policy. **Not released**: the package version stays `0.1.0`, nothing is pushed,
merged, tagged or published, and all v0.2-B behaviour was validated offline with
fake providers (no real Codex invocation, no real reviewer endpoint).

### Added

- **Project profiles** - `.devrelay/profiles/<name>.yaml` plus an ordered
  `profiles: [base, python]` selector in `.devrelay/config.yaml`. Precedence:
  packaged policy defaults < profiles in selector order < workspace overrides.
  Profile files are *policy only*: `review.provider`, `codex.*`, `git.*` and the
  selector itself are rejected (the model is the allowlist). Limits: <= 8
  profiles, <= 1 MiB per file, `yaml.safe_load`, no `extends`, no user/global
  profile directory, no CLI override, one name grammar, strict path containment.
- **Raw profile diagnostics** - `devrelay profile list|show|validate`, which work
  even when the selector is broken, and `profile validate` reports *all*
  problems (invalid filenames, per-file errors, selector syntax, duplicates,
  missing references) instead of stopping at the first one.
- **`devrelay config show` / `--resolved`** - the first prints live runtime
  wiring plus the raw, unresolved selector and explicitly says it is not the
  effective task policy; the second is the authoritative, fail-closed resolver.
- **`devrelay doctor`** now reports raw profile inspection and the full policy
  chain separately, flags pre-schema-5 tasks and profile drift, and has
  `--strict` for CI use (exit non-zero when anything is not OK).
- **Snapshot integrity** - `tasks/<id>/config.snapshot.yaml` is verified by
  SHA-256 over its exact on-disk bytes *before* it is parsed, and
  `devrelay unblock --reason "..." --refresh-policy` recovers a missing,
  invalid or hash-mismatched snapshot (recording `before_snapshot_available`
  instead of inventing a before-snapshot).

### Changed

- **Runtime wiring and task policy are separate types.** `WiringConfig`
  (`review.provider`, `codex.*`) is live and never frozen; `PolicyDocument`
  (`pipeline`, `budget`, `review` policy knobs, `tests`, `scope`, `baseline`,
  `git`) is resolved once and frozen into the task. `PipelinePolicy` accepts only
  a `PolicyDocument`; a workspace config can no longer be used as task policy.
- **`state_schema_version` 4 -> 5**: tasks persist `policy_snapshot_path`,
  `policy_config_sha256` and `policy_provenance` (selector, per-profile raw-byte
  hashes, workspace-config hash, generation, integrity). Before the first write
  that upgrades an older task, its state is copied once to
  `state.v<old>.json.bak`. State written by a *newer* DevRelay now produces a
  dedicated `state_schema_too_new` diagnostic instead of a model error.
- **All textual artifacts are written as UTF-8 with LF endings**, and every
  recorded digest is the digest of the bytes actually written (on Windows,
  `Path.write_text` used to turn LF into CRLF while hashes were computed over
  LF text, so recorded hashes could never match the disk).
- **`status`, `usage`, `diff` and `logs` are state-only**: they never validate
  live policy, never resolve the profile chain and never read a profile file, so
  deleting or editing profiles cannot break them. Live drift belongs to
  `doctor` and `config show --resolved`.
- **Execution commands classify the snapshot before any provider object is
  constructed**, so a damaged snapshot fails closed without building a Codex or
  reviewer client.
- `devrelay init` installs a workspace template (wiring + selector + commented
  policy overrides) instead of a copy of the policy defaults, and creates
  `.devrelay/profiles/`. The packaged `src/devrelay/profiles/default.yaml` is now
  the single editable default authority: the in-code `DEFAULT_PROFILE_YAML`
  literal and the repository-root `profiles/default.yaml` copy are gone.

### Removed

- The v0.2-A silent policy downgrade: a task whose snapshot is missing, invalid
  or hash-mismatched no longer continues under live wiring/workspace defaults.
  Only genuine pre-snapshot ("legacy") tasks resolve live policy, and the
  execution path never writes `policy_source`.

### Fixed (independent-review P2 remediation)

- **P2-1 - real state-schema migration.** The first *mutating* write of a task
  whose persisted `state_schema_version` is older than the current schema now
  keeps the exact previous `state.json` bytes in a one-time
  `state.v<old>.json.bak` and only then writes the upgraded (schema-current)
  document. The backup is created once, is never overwritten, and a backup
  failure aborts the write with `state.json` untouched; the upgraded document is
  a serialized copy, so the caller's in-memory task is never mutated and a
  failed write stays retryable. v5-only fields can no longer land in a file that
  still claims schema 4, and `doctor` stops reporting a permanently pending
  migration. Read-only commands still never migrate and never create a backup.
  A *migrated* v0.2-A task still uses its digest-less legacy snapshot: the
  integrity-metadata requirement now keys off the recorded snapshot path rather
  than the bare schema number.
- **P2-2 - refresh evidence is append-only.** Refresh evidence identity no
  longer comes from `len(task.policy_refreshes) + 1`. Every attempt that starts
  writing evidence consumes a unique, never-reused *evidence attempt* number
  allocated from both persisted records and on-disk `policy-refresh-NN-*`
  artifacts (gaps tolerated, `max(seen) + 1`), and the evidence files are
  written with create-new writers that refuse to replace an existing path. A
  failed attempt's artifacts therefore survive a retry untouched: attempt 01
  stays on disk as orphan evidence while the successful retry is attempt 02 and
  may still advance generation 1 -> 2. An on-disk artifact is evidence of an
  *attempt*; a refresh counts as applied only when the persisted task references
  that record and its generation/digest/provenance describe the applied
  generation. Orphan evidence is never deleted, never overwritten and never
  treated as applied.

## Unreleased - v0.3-B accepted (MCP tool surface)

A narrow local **Model Context Protocol adapter** over the accepted v0.3-A
OpenCode bridge, so an MCP-capable client (for example a ChatGPT planner) can
invoke DevRelay programmatically.  **Accepted internally / unreleased**: the
final real MCP smoke passed at accepted candidate
`d058d62341a173414bdba88fe357b08c236c8bb4`, the package version stays `0.1.0`,
the supported public release remains v0.1.0, nothing is pushed, merged, tagged or
published, and no public v0.3 release exists.  The automated suite still makes no
real network/model call; the real chain was one separately authorized one-shot
smoke.

### Accepted (final real MCP smoke)

- Official MCP Python SDK **2.2** (`mcp>=2.2,<3`), stdio-only MCP server, exactly
  nine bounded tools, one-workspace binding per server process.
- Truthful structured envelopes (`schema_version 1`) with `structuredContent` plus
  a JSON text fallback, and `isError` mechanically `not ok`.
- Exact-one-submission semantics inherited unchanged from v0.3-A (never retries,
  never falls back, never resubmits; `submission_uncertain`/`reply_pending` are
  reported as evidence).
- **Global serialized MCP execution** over the accepted filesystem ledger: one
  process-wide re-entrant lock covers all nine tool bodies, because the accepted
  ledger allocates call identities with a non-atomic read-modify-write.
- Final real smoke `PASS — V0.3-B LOCAL REAL MCP SMOKE`: real `mcp 2.2.0` client
  -> stdio -> `devrelay mcp serve --workspace <ws>` -> accepted v0.3-A bridge ->
  real OpenCode `1.18.11` -> explicit `opencode-go/deepseek-v4.1-flash`.  Exactly
  one MCP `opencode_send_prompt`, exactly one `POST /session/{id}/message`
  (HTTP 200, no `/prompt`, no `prompt_async`, no retry, no fallback), provider
  inference confirmed, `isError=false`, `ok=true`, `submission_uncertain=false`,
  `reply_pending=false`, `retry_safe=false`, assistant reply exactly
  `DEVRELAY_V03B_MCP_OK`, final history `user -> assistant`, 13 settled ledger
  records with zero `ISSUED` and no raw prompt in durable evidence.
- Complete containment and cleanup: disposable workspace unchanged (README hash,
  clean `git status`, no model-created files), disposable session deleted
  (`GET` -> 404), dedicated OpenCode stopped, MCP process exited, evidence kept
  outside the repository.

### Added

- `devrelay mcp serve --workspace <absolute-path>`: a local **stdio** MCP server
  bound to exactly one DevRelay workspace.  stdout carries MCP protocol frames
  only, diagnostics go to stderr, there is no HTTP listener and no LAN exposure;
  an invalid workspace fails closed (exit 2) before any tool is served.
- Nine high-level tools over the accepted v0.3-A bridge: `devrelay_status`,
  `opencode_health`, `opencode_list_sessions`, `opencode_get_session`,
  `opencode_read_messages`, `opencode_calls`, `opencode_send_prompt`,
  `opencode_wait_idle`, `opencode_interrupt`.  No dangerous low-level tool
  (HTTP/shell/file/git/config/env/delete/token) is exposed.
- One stable result envelope (`schema_version 1`, `ok`/`tool`/`data`/`error`) with
  `structuredContent` plus a JSON text fallback; a failed call also sets the
  protocol `isError` flag while keeping the full envelope.
- Honest MCP tool annotations: read-only hints for read tools, side-effecting for
  `send_prompt`/`interrupt`, no false idempotency claim, and planner-oriented
  descriptions that say "exactly one prompt, never retries, do not resubmit when
  `submission_uncertain`/`reply_pending`".
- Strict `<providerID>/<modelID>` model grammar, bounded prompt/timeout/limit
  validation, and a strict read-only ledger view that reports corruption instead
  of returning an empty list.
- Offline acceptance harness: an in-process tool matrix (real bridge over the
  deterministic stub) and a real stdio subprocess suite driven by the official
  MCP client and a raw JSON-RPC probe against a loopback fake OpenCode server.

### Fixed (independent-review gate remediation)

- **Envelope truthfulness (P1)**: `opencode_get_session` reported `ok: true` /
  `isError: false` for HTTP 500, malformed provider responses and unreachable
  endpoints.  Every bridge-backed tool now derives its envelope from one shared
  rule in the tool layer (`McpToolSurface._bridge_envelope`): `ok` is true only
  when the accepted operation reached that tool's success state, and the protocol
  flag is mechanical (`isError == not ok`, no per-tool special case in the
  server).  Sanitized operation evidence is always preserved in `data`.
- **stdio harness candidate pinning**: every child MCP process is launched with
  `PYTHONPATH` pinned to the checkout under test and a stripped environment, so
  the suite can no longer silently exercise an ambient editable installation; a
  mutation-propagation test proves the executed tree is the one the harness
  points at.
- **Malformed MCP input**: the documented behaviour now matches the observed SDK
  behaviour - unparseable / non-JSON-RPC / method-less frames are silently
  dropped (no reply, process alive), unknown methods answer `-32601`, invalid
  params answer `-32602`; DevRelay never claims a protocol error it does not emit.
- **Ledger ordering**: `opencode_calls` orders records by numeric call sequence
  (`OC-9999` before `OC-10000`) and reports a non-`OC-<number>` file instead of
  ranking it.
- **Cancellation evidence**: strengthened tests prove no submission is recorded
  before the gate, an already-issued POST leaves an inspectable settled record
  with no `retry_safe` claim, no automatic resubmit/interrupt happens, and the
  execution lock is released for later calls.
- **Global execution serialization (P2, post-re-gate)**: parallel MCP tool
  executions raced the accepted v0.3-A filesystem ledger, which allocates durable
  `OC-*` identities with a non-atomic read-modify-write and refuses identity
  reuse.  With 8 concurrent `opencode_read_messages` on one server, 7 of 8 calls
  failed (`internal_error` from a `PermissionError` on the shared
  `.sequence.json.tmp` rename, and `opencode_ledger_error` from a colliding
  `OC-0001`) and the durable ledger was truncated to 2 of 8 records.  All nine
  tool bodies - reads included - now run under exactly **one** process-scoped,
  re-entrant execution lock (`McpToolSurface._execution_lock`); the redundant
  `_side_effect_lock` and the separate bridge-construction lock are gone, so
  there is no lock order to get wrong and no scheduler to reason about.  The same
  8-call batch now returns 8/8 success with 16 unique, settled, contiguously
  numbered call identities and a measured maximum of one concurrent ledger entry.
  `devrelay_status` reports `execution_serialized: true`.  Consequences: a long
  `opencode_wait_idle` body delays other calls in the same process, cancelling a
  request does not let another body overtake an already-running one, and two
  `devrelay mcp serve` processes over one workspace are still not serialized
  against each other (single-writer ledger hardening remains deferred).

### Notes

- v0.3-A sources, semantics and tests are unchanged; every v0.3-A guarantee
  (exactly one submission POST, no retry/fallback, submission-uncertainty
  distinction, stale-reply suppression, durable accounting, credential/prompt
  containment) holds through the MCP layer.
- **All** tool execution (reads included) is serialized per MCP server process by
  one re-entrant execution lock, because the accepted v0.3-A filesystem ledger is
  a single-writer store; cancelling a local MCP request never implies "not
  submitted" and never triggers an automatic abort.
- The real MCP-client smoke is **done** (see "Accepted (final real MCP smoke)"
  above).  Still deferred: Streamable HTTP/SSE transport, multi-process /
  multi-workspace serving, and any role routing or orchestration (v0.3-C, not
  started).

## Unreleased - v0.3-A accepted (OpenCode session bridge)

A narrow, provider-contained bridge to one explicitly configured, already running
OpenCode server. **Accepted internally and still unreleased**: the package
version stays `0.1.0`, nothing is pushed, merged, tagged or published, and the
supported public release remains v0.1.0.

### Accepted

- **Final decision:** `ACCEPT — V0.3-A OPENCODE SESSION BRIDGE`, functional
  candidate `bcf9627e92ef839abb756810e3c615e6d01b6576`; v0.3-A functional
  development is closed and the runtime implementation is frozen at that commit.
- **Real compatibility verified** against a dedicated **OpenCode 1.18.11** server:
  health, prompt-free session creation, explicit disposable session, workspace
  ownership, empty baseline read, exactly **one** real
  `POST /session/{id}/message` with the explicit model
  `opencode-go/deepseek-v4.1-flash` (wire `{providerID, modelID}`), provider
  inference confirmed, synchronous `{info, parts}` response (HTTP `200`,
  `application/json`) normalized to one correlated assistant reply whose text is
  exactly `DEVRELAY_A33_OK`, runtime status via `GET /session/status` (idle
  represented by the session's absence from the map), real provider message
  ordering **oldest → newest**, stable window (`cursor_unknown=false`,
  `replayed=false`, no truncation), workspace unchanged, 15 settled ledger
  records with no `ISSUED`, no raw prompt and no credentials persisted, and the
  disposable session/server cleaned up afterwards.
- **Historical A33 attempts are preserved as evidence, not rewritten:** the first
  attempt was `BLOCKED` (no provisioned endpoint/session), the first real
  protocol attempt was `FAIL` (the obsolete `/session/{id}/prompt` route does not
  exist on 1.18.11), a second real attempt was `FAIL` (the *user's* global default
  model referenced a provider disabled by the same configuration), and a
  zero-model diagnostic proved that failure was an OpenCode/environment
  configuration issue with **no DevRelay defect** before the final explicit-model
  smoke passed.
- Non-blocking follow-ups (F1 follow-up-only hardening, Basic-vs-Bearer auth
  compatibility, multi-process ledger locking, cross-host/container path mapping,
  server-side pagination, corrupt-ledger UX, Windows Codex `pwsh.exe`, remaining
  v0.2-C real E2E evidence) stay recorded in `docs/BACKLOG.md`.

### Added

- `devrelay/opencode/`: normalized DevRelay-owned models (`OpenCodeSession`,
  `OpenCodeMessage`/`OpenCodeMessagePart`, `OpenCodeMessagePage`,
  `OpenCodeHealth`, `OpenCodeOperationResult`, `OpenCodeCallRecord`), an explicit
  operation/call state vocabulary, an HTTP transport with one configured endpoint
  (never port scanning) and bounded response reads, a durable per-request call
  ledger (`.devrelay/opencode/calls/<call-id>.json`, monotonic `OC-NNNN` ids) and
  the `OpenCodeBridge` capability surface: `health`, `list_sessions`,
  `get_session`, `read_messages`, `send_prompt`, `wait_idle`, `interrupt`.
- Workspace/session ownership enforcement: the configured workspace must match the
  session's reported workspace; unknown sessions and cross-workspace reuse are
  hard failures, and a session that reports no workspace fails closed unless the
  unsafe opt-in is set explicitly.
- Bounded `wait_idle` (idle/terminal or `TIMED_OUT`, no retry) and interrupt that
  reports `interrupt_unsupported` instead of pretending a cancellation happened.
- `opencode:` runtime wiring in the workspace config (explicit `base_url`,
  workspace, optional session/agent/model, timeouts, response/message caps) plus
  `DEVRELAY_OPENCODE_TOKEN` read from the environment only. The section is never
  task policy: it is excluded from the frozen policy projection and tolerated as
  a known wiring key in legacy full-config snapshots.
- `devrelay opencode health|sessions|show|read|send|wait|interrupt|calls` — thin
  CLI wrappers that print normalized results (no OpenCode logic in the CLI).
- `tests/opencode_stub.py` + `tests/test_v03a_opencode.py`: deterministic offline
  coverage of discovery, selection, reading, one prompt, idle completion, provider
  failure, malformed response, timeout, interrupt, unknown session,
  workspace/session mismatch, cursor replay and accounting.

### Fixed (independent-review remediation)

Remediation of the `REQUEST_CHANGES - V0.3-A` findings, still entirely offline
(58 of the 66 new tests in `tests/test_v03a_remediation.py` fail against the
pre-remediation source):

- **P1** `wait_idle` now establishes the whole-operation deadline *before* the
  ownership probe and clamps every request (probe included) and the inter-poll
  sleep to the remaining budget, so the declared/idle timeout is genuinely
  enforced and nothing runs after the return.
- **P1** `read_messages` keeps the **newest** messages (`messages[-max:]`) and
  reports `provider_message_count`/`window_truncated` instead of head-truncating
  a large payload and calling it a complete replay; `max_messages` is bounded to
  the 200-message wire maximum in config validation.
- **P1** `send_prompt` correlates a reply only as a *new assistant* message
  (inline candidate or one explicit follow-up read): no stale reply, no
  id-bearing envelope treated as a reply, `reply_pending` when nothing new is
  visible, a follow-up `404`/`500` reported as a post-acceptance condition
  (never "your prompt was not submitted"), merged accounting on every path, and
  no automatic resubmission.
- **P1** `DEVRELAY_OPENCODE_TOKEN` joined `CODEX_CHILD_ENV_DENYLIST`: a Codex
  child process never inherits the OpenCode bearer credential.
- **P2** `trust_env=False` on the control-channel client (ambient proxy/CA
  variables cannot reroute it); strict session-id grammar plus a returned-id
  mismatch check (invalid ids issue zero requests); explicit interrupt semantics
  (`204`/JSON accepted → `INTERRUPTED` with `interrupt_verified: false`, `404` →
  `interrupt_session_not_found`, `405`/`501` → `interrupt_unsupported`, otherwise
  the real provider error or `MALFORMED_RESPONSE`); provider echoes of the prompt
  or token are scrubbed from error snippets in the submission *and* in
  post-submission reads/polls (literal-value scrubbing, documented as such, with
  the unsalted prompt SHA-256 documented as an identifier and not as secrecy);
  ledger allocation fails closed (corrupt sequence, identity collision) and
  recovers from existing records otherwise; `--json` keeps a non-zero exit status
  for a failed operation in both output modes.
- Config hardening: base-URL validation (scheme/host/embedded credentials/path
  prefix/query/fragment), fail-closed numeric bounds, `extra="forbid"` preserved,
  and an empty (`null`) section body now means "not configured" instead of a
  validation error.

### Documentation

- `docs/v0.3/V03A_SPEC.md`, `docs/v0.3/V03A_ACCEPTANCE.md`,
  `docs/v0.3/V03_PLAN.md`, and `docs/BACKLOG.md` (which carries the pending
  v0.2-C real Codex smoke and a separate Windows Codex shell P2 investigation).

### Fixed (A33 real-protocol remediation)

Real-protocol compatibility with the installed OpenCode 1.18.11 server, after the
authorized A33 smoke returned `FAIL` on a genuine product/protocol mismatch
(28 of the 30 new tests in `tests/test_v03a_real_protocol.py` fail against
`780c2fd`; no real model call was made during this remediation):

- **Submission route**: the default prompt path is now the documented
  `POST /session/{id}/message` (the old `/session/{id}/prompt` route does not
  exist on 1.18.11 - the server answers unmatched paths with a `200 text/html`
  SPA shell).  There is deliberately **no** compatibility fallback and no switch
  to `prompt_async`: exactly one POST, on the real route.
- **Request contract**: the minimum body is
  `{"parts":[{"type":"text","text":...}]}` with every optional member omitted;
  `agent` is forwarded as the documented string and `model` is encoded as the real
  structured identity `{providerID, modelID}` via the explicit
  `<providerID>/<modelID>` grammar - an unmappable override fails locally before
  any request is issued.
- **Response normalization**: the real synchronous `{info, parts}` body
  normalizes to exactly one assistant message (role must be `assistant`, text
  parts normalize, unknown parts stay limited, raw wire objects never escape); an
  incomplete/non-assistant body remains an honest pending/fail-closed result.
- **Runtime status**: `wait_idle` polls the real `GET /session/status` map
  (`idle` completes, `busy`/`retry` keep polling with retry evidence preserved in
  `status_detail`, a **missing entry means idle** - verified: 1.18.11 omits
  non-running sessions, and the session object has no state field), instead of
  polling a session state field that does not exist. All deadline/ownership/
  clamping/accounting guarantees are unchanged.
- **2xx evidence**: a 2xx is credible acceptance only when its media/body contract
  matches the endpoint. A JSON body with an unusable body stays "accepted,
  unusable body"; a 2xx whose media type cannot carry the documented contract
  (the SPA `text/html` fallback) is **submission-uncertain** with the media type
  preserved on the result (`submission_contract`) and on the durable record
  (`response_media_type`), never presented as accepted and never retried.

### Fixed (third independent-review blocker remediation)

Third remediation pass on `6e0eb61` (22 of the 23 new tests in
`tests/test_v03a_third_remediation.py` fail against it), still entirely offline:

- **Blocker P1** transport failures around the submission POST are now classified
  instead of treated alike: `connect_timeout`/`pool_timeout`/`connect_error` and
  local refusals prove nothing was submitted, while `read_timeout`,
  `write_timeout`, read/write errors, remote protocol errors and anything
  unclassified are *submission-uncertain*.  An uncertain POST reports
  `submission_uncertain: true`, `reply_pending: true` (unless a new assistant
  reply is correlated), explains that the prompt may already have been accepted
  and that DevRelay will not resubmit automatically, performs exactly one bounded
  follow-up read and never retries the POST.
- **Blocker P2** a post-acceptance result can no longer expose the
  pre-submission message window: `messages` is empty and `page` is `null`
  whenever no new assistant reply was positively correlated (follow-up 500,
  timeout, provider unavailable, vanished session, malformed follow-up, still
  pending, or an uncertain submission), so `messages[-1]` can never be mistaken
  for the answer to the prompt just sent.  The boundary cursor stays available as
  `reply_boundary`.
- **Adjacent** the human CLI now states the submission verdict and the reply
  state explicitly ("submission accepted (HTTP nnn …)", "submission uncertain …
  do not resubmit automatically", "submission rejected (HTTP nnn)", "submission
  not accepted", "reply pending: no new assistant message was confirmed"), never
  prints an old reply, and agrees with `--json`; a genuine HTTP rejection keeps
  its status as submission evidence (`submission_status`) and is not described as
  an unusable body; a malformed follow-up clears the page as well as the
  messages; and `submission_uncertain` results are never a clean exit.

### Fixed (second independent-review remediation)

Second remediation pass on `f5d487d` (36 of the 49 new tests in
`tests/test_v03a_second_remediation.py` fail against it), still entirely offline:

- **P1** every Codex child process - legacy text runtime, `--version`,
  `exec --help`, capability detection, doctor probes - now spawns through one
  centralized credential-scrubbing adapter, so the OpenCode token and the other
  denylisted provider credentials can no longer reach any Codex child (the parent
  process keeps its credentials).
- **P1** a 2xx prompt submission with an unusable body (`204`, empty `200`,
  invalid JSON, oversized) is a *post-acceptance* result, not a failed
  submission: `submission_body`/`submission_status` record the evidence, the
  bounded follow-up read still runs, `reply_pending` stays honest and nothing is
  resubmitted.
- **P1** the anti-DoS pre-cap on provider message lists keeps the true newest
  tail (previously `raw[:2000]` could hide the newest messages of a large session
  and break reply correlation).
- **P1** provider echoes of the prompt/token are now scrubbed in their JSON-,
  backslash- and percent-escaped forms (two escaping levels) on the POST, the
  follow-up read and every wait/poll request, before anything reaches the ledger,
  the result or the console.
- **P1** parser bombs (extreme JSON nesting, over-long integer literals) and
  invalid JSON normalize into `MALFORMED_RESPONSE` with a specific error type,
  and the durable call record is always settled - a provider body can no longer
  strand a record at `ISSUED` or traceback the CLI. Programming errors still
  propagate.
- **Adjacent** operation accounting survives a failing ownership/boundary probe;
  a malformed follow-up keeps the `send_prompt` identity; dot-segment session ids
  are refused; the full (untruncated) returned session id is compared; malformed
  URL authorities are configuration errors before httpx and config errors no
  longer echo an embedded password; a refused create-new leaves no phantom
  in-memory ledger record.

## Unreleased - v0.2-C candidate (structured Codex runtime)

Structured, isolated, tamper-evident and replayable Codex runtime. **Not
released**: version stays `0.1.0`, nothing is pushed/merged/tagged/published, and
everything below is validated offline with a stub Codex CLI (no model call, no
network).

### Added

- Structured implementer contract: `--output-schema` + `--output-last-message`
  with a validated `ImplementationResult` (`schema_version = 1`); `--json` events
  are observational only and never required for a run to count.
- Transient raw result staging under `.devrelay/tmp/runtime/<attempt-id>/`:
  bounded read, `raw_result_sha256`, sanitized immutable `result.json` (create-new
  writers), best-effort removal, stale-staging cleanup-or-refuse policy.
- DevRelay-owned Codex argv: `exec`, `--sandbox workspace-write` (exactly once),
  `--ignore-user-config`, `--ignore-rules`, `--json`, schema/result flags, cwd and
  stdin prompt. `-p/--profile`, user `--sandbox`, `--add-dir`, `--cd`,
  `--skip-git-repo-check`, `--approve-for-me`, bypass flags, output-path flags and
  unsafe `-c` namespaces are rejected; a repository Codex config fails structured
  mode closed (`codex.runtime_mode: text` is the explicit opt-out).
- Codex child environment scrub (reviewer + enumerated LLM provider credentials),
  honestly documented as an explicit denylist, not general secret isolation.
- Control-plane guard: in-memory PRE manifest, POST verification before any state
  re-read, `codex_control_plane_violation` fail-closed path, metadata-only
  violation evidence (no raw tampered content), durable hold with
  verification-gated recovery (`--acknowledge-control-plane-violation`,
  `--restore-state-from-pre`).
- Durable implementer milestones (`PROCESS_EXITED` … `COMPLETION_READY` …
  `COMPLETION_APPLIED`) with idempotent application; `attempt_in_flight` is only
  cleared once a replay-safe verdict exists.
- Completion replay: a `COMPLETION_READY` attempt with matching identities is
  applied locally with **0 external calls**; drift blocks as
  `implementer_replay_workspace_changed` / `replay_control_state_changed`;
  `devrelay unblock --replay-completion` applies it explicitly after a human
  restored the workspace.
- Two-stage reconciliation (`implementation-reconciliation.json`,
  `test-reconciliation-NN.json`) surfacing claimed-vs-observed files, rejected
  traversal claims, unknown result field names and test-claim disagreements.
- Baseline root hardening: `baseline.json`/`manifest.json`/`tracked.patch` are
  content-hashed by the guard and untracked blobs are verified against their
  declared SHA-256 before use.
- Bounded, deadlock-free process capture (always-drain reader threads, head+tail
  retention) with truncation evidence, `env_remove` support and terminate→kill
  fallback.
- `doctor` reports the effective runtime mode, structured capability and the
  scrubbed credential names; `status`/`usage` show runtime milestones and results.

### Changed

- `state_schema_version` 5 → 6 (durable milestones, workspace/control-plane
  identity, runtime evidence), reusing the existing migration/backup/too-new
  machinery; v0.2-B tasks keep loading and read-only commands still never migrate.
- Bumped `MAX_SUPPORTED_STATE_SCHEMA` accordingly; a v0.2-B binary refuses v6 with
  `state_schema_too_new` instead of guessing.

### Fixed (independent-review P1 remediation)

- **P1-A — structured mode was silently downgraded on every frozen-task CLI
  path.** The effective runtime mode was read from the *task policy* source, but
  the CLI builds engines with `config=None` for tasks that own a frozen snapshot,
  so `devrelay continue` fell back to `text`: no `--output-schema`, no bounded
  result read, no child environment scrub, no control-plane PRE/POST guard and no
  containment — a silent loss of the whole v0.2-C contract. The mode now comes
  from the live `WiringConfig` only (`self.runtime_config.codex.runtime_mode`),
  the frozen document stays authoritative for policy only (it carries no `codex`
  section at all), and a mis-wired engine fails pre-flight instead of
  downgrading. `status` prints the effective mode as `Runtime:` and `doctor`
  reports mode, capability and containment. Regression coverage drives the *real
  CLI* end-to-end (`test_cli_continue_runs_the_structured_runtime`,
  `test_cli_runtime_mode_text_is_explicit_and_stays_text`), not just an internal
  helper.
- **P1-B — a detached descendant could mutate the control plane after POST.**
  Nothing contained the Codex process tree: the child could spawn a detached
  grandchild that outlived it, wait for the POST manifest comparison to pass and
  then rewrite `.devrelay/tasks/<id>/state.json` (and drop arbitrary files) with
  no violation and no trace. New module `devrelay/workspace/containment.py`
  provides the abstraction (`spawn_contained` / `wait_contained` /
  `terminate_contained` / `kill_contained` / `all_contained_processes_dead`) and a
  race-free Windows Job Object backend (`KILL_ON_JOB_CLOSE`, no breakaway, broker
  hand-off *before* Codex runs). The runner ends a contained window by closing the
  job and verifying `all_contained_processes_dead()` **before** the engine
  computes POST, so a surviving descendant can no longer land after the guard. The
  refusal is honest: on POSIX (where a process group cannot contain a
  `setsid`/double-fork descendant) structured mode fails pre-flight with
  `codex_process_containment_unsupported` and **0 provider calls** instead of
  claiming weak containment, and `doctor` flags the missing capability.
  Containment facts (`containment`, `containment_all_dead`) are persisted in the
  attempt runtime evidence, in the violation report and in the hold. If the tree
  cannot be confirmed dead within the containment deadline, the run fails closed
  as `codex_containment_unverified`: the POST comparison is skipped entirely, no
  state is overwritten, a post-mortem hold is written for manual recovery, and
  the invocation stays charged (the process really ran).
- **P1-D — a consumed call disappeared from `provider_calls`/budget on the
  control-plane-violation path.** The pre-run attempt write persisted a stale
  in-memory `TaskRun` and erased the accounting intent recorded moments earlier,
  so a *real* Codex invocation that was voided by the guard left
  `provider_calls == []`, budget usage `0` and an orphan `policy/calls/*.json`
  entry. The pre-run write now merges the persisted accounting facts (call list
  plus the monotonic sequencing counters, `max()` of both sides) into the record
  it writes while the caller's in-memory transition is preserved. A voided run is
  now fully charged: call id `DR-0001-C0001`, usage `implementer_calls == 1`,
  ledger entry present, hold referencing the same call id, and the trusted
  parent-held `*-state.pre.json` copy contains it.
- **C7 / C16 acceptance closure.** `C7`: a non-zero exit with a *valid* model
  result is still a failure (`implementer_failed`, no `COMPLETION_READY`, no
  durable `result.json`) and is still charged once. `C16`: unicode workspace
  roots, staging paths and claimed file names survive the whole structured
  runtime (manifest, reconciliation, evidence).

### Fixed (real-smoke structured schema remediation)

- **The transport schema was rejected by the real Structured Outputs endpoint.**
  The one approved real Codex smoke (call `DR-0001-C0001` against `301e891`)
  authenticated via ChatGPT, ran the real structured argv, passed containment and
  a clean control-plane check, and was then refused with HTTP 400
  `invalid_json_schema`: *"'additionalProperties' is required to be supplied and
  to be false"*. `result_json_schema()` emitted a tolerant schema
  (`additionalProperties: true`, only three required root fields), which the
  offline stub accepted, so no test could see it. The transport schema is now
  strict: every object node (root and `tests_run` items) sets
  `additionalProperties: false`, `required` lists exactly the declared
  properties, `schema_version` is `{"type": "integer", "enum": [1]}`, and
  optionality is expressed only by deterministic empty values (`[]` / `""`).
  The local post-parse model is unchanged and stays defensive (caps,
  `schema_version`/status enforcement, claim-path rejection, unknown-field
  recording) - a strict transport contract is not a weaker trust model.
- **The offline Codex stub is now as strict as the real endpoint.** Before
  writing a structured result it lints the supplied `--output-schema`
  recursively (closed objects, fully required objects, declared required keys,
  `schema_version` pinned to 1) and refuses (`invalid_json_schema`, exit 3)
  otherwise, so the pre-fix schema now fails offline too. Regression coverage:
  `tests/test_v02c_schema_strictness.py` (recursive strictness lint, nested item
  contract, no risky constructs, pre-fix schema rejected end-to-end with exactly
  one charged call, strict-schema happy path, parser caps/security intact).

## Unreleased - v0.2-A candidate (audit remediation, closure audit pending)

Automatic review loop with an enforced execution budget, plus the remediation of
the independent audit of commit `fe4b044` (one P1, three P2, six P3 findings).
**Not released**: the package version stays `0.1.0`, nothing is pushed, merged,
tagged or published, and the behaviour below was validated with fake providers
only (no real Codex invocation and no real reviewer endpoint were used).

### Fixed

- Baseline capture no longer fails with `git add -A -- . :(exclude).devrelay
  failed: The following paths are ignored ...: .devrelay` in repositories whose
  `.gitignore` lists `.devrelay/` (the normal, documented setup). The worktree
  tree is now built from an explicit list of eligible paths (tracked changes +
  non-ignored new files, `.devrelay` filtered in DevRelay code) against the
  temporary index, never from an explicitly named ignored pathspec, and never
  with `git add -f` (which would include unrelated ignored files). A repository
  that *tracks* `.devrelay/**` is excluded symmetrically. Regression coverage:
  `tests/test_baseline_ignored_self.py`.

### Fixed (audit remediation)

- **P1-01** - the crash window between persisting a reviewer result and applying
  it can no longer cost a second paid reviewer call. A persisted, schema-valid,
  sanitized result is now an authoritative, replayable result: the next
  `continue` replays it locally with **0 external calls** and enters the
  policy-defined state (`FIX_REQUIRED` / `FINAL_GATE_REQUIRED` / `BLOCKED`).
  An *uncertain* call still fails closed - DevRelay never invents a result.
- **P1-01 (idempotency)** - the whole semantic application (history, seen
  counters, findings, applied marker, transition, audit) lands in **one atomic
  state write**, guarded by a stable result identity plus an
  `AppliedReviewRecord`. Restart replays therefore never duplicate history,
  counters, transitions or audit events; content equality alone is not treated
  as proof (two legitimately identical rounds still apply separately), and a
  missing terminal transition is completed locally only with proof that nothing
  happened since.
- **P2-01 / P2-02** - one durable, task-scoped identity system replaces
  process-local counters and success-derived numbering: call ids
  (`DR-0001-C0007`), implementer attempts (`DR-0001-A0002`) and review attempts
  (`DR-0001-R0002`) are allocated from persisted monotonic sequences before the
  invocation, never reused after a failure, and never reset by `unblock` or a
  policy refresh. Calls link to attempts (`parent_attempt_id`, `call_ids`).
- **P2-01 / P2-02 (evidence)** - immutable evidence is keyed by those identities
  (`policy/calls/<call-id>.json`, `policy/attempts/<attempt-id>.json`,
  `policy/runs/<attempt-id>-*.json`, `logs/<attempt-id>.*`,
  `reviews/review-NN-<attempt-id>-meta.json`); a retry can no longer overwrite a
  failed attempt's or another call's evidence. The legacy `NN`-named artifacts
  remain as documented "latest view" convenience copies.
- **P2-03** - `unblock --refresh-policy` preserves the previous policy:
  `PolicyRefreshRecord` plus `policy/policy-refresh-NN-{before,after}.yaml` and
  `-NN.json` (before/after SHA-256, actor, reason). Usage is never reset,
  deleted or renumbered, and existing calls count against the new limits.
- **P3-01** - `max_response_chars` is documented (config, README, error message)
  as a parsing/persistence cap; the HTTP client may buffer the body first, so it
  is not a network-level memory limit.
- **P3-02** - retry phase labels follow the failure cause; a mixed
  format/transport/format sequence no longer mislabels a transport retry as
  `REVIEW_FORMAT_RETRY`.
- **P3-03** - finding fingerprints normalize path separators and file order but
  never case-fold paths (POSIX repositories may contain both `A.py` and `a.py`).
- **P3-04** - `policy_source` is persisted as `snapshot` at task creation;
  `status`/`usage` resolve it read-only and never rewrite task state (legacy
  tasks keep reporting `live-fallback` unmodified).
- **P3-05** - AUD-09 stays open as a backlog item; `unblock` still clears the
  block record but now preserves it verbatim in the audit trail and deletes no
  evidence (calls, attempts, review attempts, policy refreshes).
- **P3-06** - review-history growth was analysed and proven linear/non-nested
  (one summary line per previous round, bounded by `max_reviewer_calls`); prompt
  compaction stays deferred.
- State schema bumped to **4** with public v0.1 state compatibility and a
  `finish_only` recovery path for private `fe4b044` state.

### Added

- Automatic review loop: the engine drives the reviewer itself and feeds
  blocking findings back into the fix prompt. The state machine is unchanged
  and the final gate stays manual - never an automatic `DONE`.
- Execution budget (`budget.max_implementer_calls` 4, `max_reviewer_calls` 4,
  `max_total_provider_calls` 8) checked **before** every external call;
  exceeding a limit BLOCKS the task with code `provider_budget_exhausted` and
  reports used/max for all three limits. The budget is never reset
  automatically.
- Persisted `ProviderCallRecord` for every attempted external invocation
  (kind, phase, success, error type, duration, model, endpoint host - never
  credentials or full URLs) plus `reviews/review-NN-call-MM-meta.json`.
- Reviewer attempt lifecycle (`ReviewAttempt`) with `review-NN-meta.json`:
  status, transport/format attempt counts and external calls consumed.
- Crash-safe in-flight marker (`review_call_in_flight`) persisted before the
  request: a hard kill leaves evidence, and the next `continue` fails closed
  with `interrupted_reviewer_attempt` until a human `unblock --reason ...`.
  A review round that was started but never finalized (crash after the provider
  answered, before the result was persisted) is detected from the persisted
  attempt and fails closed the same way; acknowledging it closes the round as
  `INTERRUPTED` without deleting its call evidence, and the retried round gets
  a unique attempt identity.
- Transport vs format failure separation (`transport_retries` default 0 is
  opt-in; every retry is a counted call) and a `max_response_chars`
  parsing/persistence cap - oversized answers are refused with an explicit
  error, never silently cut or guessed.
- Sanitized HTTP error bodies and model output (same redaction boundary as
  reviewer input) before persistence.
- Finding fingerprints
  (`sha256(severity | normalized title | files | description)`) with per-task
  seen counts, and the opt-in `pipeline.max_same_finding_cycles` stall guard
  (`0` = disabled; fingerprints are recorded either way).
- Task policy snapshot (`tasks/<id>/config.snapshot.yaml`) applied for the
  whole task, `policy_source` visibility, and the audited
  `devrelay unblock --refresh-policy --reason "..."` as the only supported way
  to change a running task's budget/blocking policy.
- `devrelay usage` (read-only provider usage/audit view); `status` now shows
  budget used/max, last review attempt and policy source; `doctor` reports
  reviewer env var **presence** only (`set`/`MISSING`) without sending a
  request, and prints the configured budget.
- State schema version 3 (`provider_calls`, `review_attempts`,
  `finding_seen_counts`, ...) with v0.1 fixture compatibility.

### Changed

- Policy authority over the reviewer: a `PASS` decision that still carries a
  blocking finding does not pass - the configured `blocking_severities` decides.
- The Codex FIX prompt carries structured findings (`- [P2] id=... title=...`
  with `description:` / `files:` / `evidence:` / `recommendation:` lines).
- Manual reviewing is unchanged and still makes zero external calls (a
  `ReviewAttempt` with `external_calls = 0` is recorded for audit).

### Security

- Reviewer credentials stay in environment variables; they never appear in
  `config.yaml`, task state, provider call records, artifacts or logs, and
  `doctor` prints presence rather than values.
- Budget/attempt evidence is append-only: no command resets or forges usage.

### Tests

- 227 tests, fully offline (fake providers, `httpx.MockTransport`, real tiny
  git repositories): 38 v0.2-A tests covering budget pre-flight, exact call
  accounting, format/transport separation, crash recovery, policy authority,
  fingerprints, snapshot/refresh-policy, CLI visibility and a fake-provider
  engine-level end-to-end loop, plus 22 audit-remediation tests covering the
  required crash/identity/policy matrix (persisted-result replay with zero
  calls, single application, immutable evidence, durable ids, policy-refresh
  evidence, retry labelling, fingerprint normalization, read-only legacy
  status/usage, budget regressions), plus 8 baseline-capture tests for the
  ignored-`.devrelay` smoke blocker.

## 0.1.0 - 2026-09-10

First public release: local AI coding orchestration with a task baseline, a
bounded review/fix loop and repository policy guards.

### Added

- Local AI coding orchestration pipeline (PLAN -> IMPLEMENT -> TEST -> REVIEW
  -> FIX loop -> FINAL_GATE -> DONE)
- Persistent task state machine with audited transitions and resume after
  process restart
- Official Codex CLI implementer (prompt streamed on stdin, no OpenAI API key
  required)
- Codex execution path that works with a ChatGPT-subscription-authenticated
  Codex CLI login
- Manual planner workflow (Task Packet `plan show` / `plan import`)
- Manual reviewer workflow (`review export` / `review import`)
- OpenAI-compatible reviewer provider for HTTP review endpoints
- Dirty-workspace task baselines: pre-existing tracked/untracked changes,
  staged and unstaged mixes, deletions, renames and binary files are captured
  without touching the user's real Git index
- Task-relative diffs: reviewers and reports see the baseline -> current
  workspace delta, never HEAD-relative attribution of pre-existing user work
- Durable baseline recovery: byte-faithful `tracked.patch` plus untracked
  blobs, reconstructed and SHA-verified after `git gc` prunes the baseline tree
- Git repository policy guards: HEAD, branch, tag, other local refs and real
  index staging are snapshotted before/after every provider run; violations
  BLOCK the task and are never auto-repaired
- Interrupted provider attempt recovery: persisted attempt lifecycle, post-run
  evidence for exceptions/timeouts/KeyboardInterrupt, fail-closed restart
  requiring explicit human acknowledgement
- Reviewer secret redaction (best-effort pattern based) applied at a single
  boundary shared by the remote and manual reviewer paths
- CLI commands: `init`, `doctor`, `start`, `status`, `plan`, `continue`,
  `diff`, `logs`, `review`, `final`, `unblock`, `version`
- Artifact/evidence generation per task (baseline, implementation reports,
  review requests/results, logs, policy snapshots, final report)
- Release/final gate with a human-readable `final/report.md` answering "why is
  this task considered complete?"

### Security

- No ChatGPT credential scraping, no browser/session automation, no
  undocumented authentication paths
- No OpenAI API key requirement for the Codex CLI execution path
- `shell=False` subprocess execution with argv lists and timeouts
- Git HEAD/branch/ref/index mutation guards with structured violations
- Fail-closed handling of conflicted or otherwise unverifiable Git index state
  (blocked before a provider run can start)
- Best-effort reviewer secret redaction (not a data-loss-prevention system)
- Push prevention remains **provider-limited / best-effort**: the local
  postcondition check cannot mathematically prove that no `git push` happened

### Known limitations

- One active task at a time (no concurrency)
- One implementer: the official Codex CLI
- No MCP server, ChatGPT plugin, web UI or VS Code extension yet
- No mathematical push prevention (see Security)
- Reviewer redaction is pattern-based best effort, not DLP
- Structured Codex event stream (`codex exec --json`) is not parsed yet
- Remaining P3 backlog tracked for a later release:
  - dead HEAD-relative helpers in `GitWorkspace` (unused since task-relative
    deltas landed)
  - `unblock` clears the raw `blocked_reason` field (the audit trail, policy
    snapshots and attempt evidence are retained)
  - files marked `assume-unchanged` / `skip-worktree` do not appear in
    `preexisting_dirty_files` metadata (the task delta itself stays correct)
  - `final/report.md` header line is rendered at the moment of approval
