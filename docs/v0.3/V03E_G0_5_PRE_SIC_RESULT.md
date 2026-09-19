# DevRelay v0.3-E — G0.5-PRE / SIC Mode-A candidate result

> **CANDIDATE SIC RESULT — AWAITING INDEPENDENT RESULT REVIEW.**
> This is **not** AUTHORITATIVE, **not** ACCEPTED and **not** FINAL.  It is **not** `P6 PASS`,
> **not** `P6 FAIL`, **not** `G0.5 PASS` and **not** `G0.5 FAIL`.
> The single authorized Mode-A attempt was executed once; **no rerun is authorized**.

## 1. Authorization and baselines

| Item | Value |
| --- | --- |
| Repository HEAD before the attempt | `e1fb6ac5abb2c7a98984b0efa1c4c53200fa8b67` |
| Branch / package / tags | `v0.3-e-recovery-reconciliation` / `0.1.0` / `v0.1.0` only; no upstream |
| Worktree at attempt start | clean |
| Accepted SIC definition baseline | commit `829d3c0`, blob `5463ac19ddc532f2a5f4f73c1076284f4c5f75b94338a5720a189b955e23ad11` (verified, unchanged) |
| Accepted/frozen Mode-A oracle | `docs/v0.3/V03E_G0_5_PRE_SIC_ORACLE.md`, blob `31d7ac5020ba6a7e3a4eb700df0feedc8f480d67a89f7124091e87df9ff7dc78` (verified, unchanged) |
| Accepted §25.1 block | `d3244ee0d24f5d740b34dac358378870d4d8238b0755787cffb7313d01044ee0` (verified, unchanged) |
| G0.4 oracle blob | `b0c34fa19c3e639b5637d74d49e1c9c357b7db914ee1becf70229f3e5ed4bfa4` (verified, unchanged) |
| External authorization | one-shot Mode-A SIC execution, exactly **one** semantic attempt |
| Attempt count consumed | **1 of 1** |

## 2. Target identity (verified at execution time)

| Field | Value |
| --- | --- |
| Package / product | `opencode-ai` / OpenCode **1.18.11** |
| Package root | `C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai` |
| Declared bin | `./bin/opencode.exe` |
| Declared-bin resolved path | `<root>\bin\opencode.exe` |
| Declared-bin SHA-256 (observed) | `578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35` (matches the frozen value) |
| Identity verdict | **IDENTITY OK** (name, version, package root, declared-bin path and hash all match) |
| Executable execution | **none** — the binary was hashed only; it was never started, executed or signalled |

## 3. Execution-time manifest observation (frozen manifest re-enumerated)

Traversal: lexicographic normalized relative-path order (frozen rule).  Enumerated files: **8**;
frozen manifest files: **8**; missing: **none**; extra files inside the package root: **none**;
size/hash drift: **none**.

| # | Relative path | Type | Size (observed = frozen) | SHA-256 (observed = frozen) | Class |
| --- | --- | --- | --- | --- | --- |
| 1 | `LICENSE` | – | 1,065 | `625f0f619133f89bbbb2abe37369613dfa1885eba1e50d02170deb62bb42cb6b` | `LICENSE_TEXT` |
| 2 | `bin/opencode.exe` | `.exe` | 174,182,280 | `578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35` | `OPAQUE_COMPILED_BINARY` |
| 3 | `node_modules/opencode-windows-x64-baseline/bin/opencode.exe` | `.exe` | 174,182,280 | `0e80c44457a95108e1932a1c31bcaddc011e143943f13624891a114b21262347` | `OPAQUE_COMPILED_BINARY` |
| 4 | `node_modules/opencode-windows-x64-baseline/package.json` | `.json` | 149 | `f4b19768d7d29e0f49f2049571b1b9f9873f85e27a6365a553833c7939f019cf` | `PACKAGE_METADATA` |
| 5 | `node_modules/opencode-windows-x64/bin/opencode.exe` | `.exe` | 174,182,280 | `578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35` | `OPAQUE_COMPILED_BINARY` |
| 6 | `node_modules/opencode-windows-x64/package.json` | `.json` | 140 | `19b744c84045d274b02b482b9cbef518d2c8b397afda935356af105da3e55d2c` | `PACKAGE_METADATA` |
| 7 | `package.json` | `.json` | 825 | `de1da8f30650084a6261fe9a87a3126a63a6ea1365db2acdecb1cde640a86ee2` | `PACKAGE_METADATA` |
| 8 | `postinstall.mjs` | `.mjs` | 5,496 | `5a7c990fe552e76b16422cdba3f4b0550590c7a487f7932c773362f74317c87b` | `INSTALLER_LOGIC` |

Directories (6): `bin`, `node_modules`, `node_modules/opencode-windows-x64`,
`node_modules/opencode-windows-x64/bin`, `node_modules/opencode-windows-x64-baseline`,
`node_modules/opencode-windows-x64-baseline/bin`.  All 8 artifacts were classified exactly once
(8 classified / 0 unclassified).

## 4. Coverage determination

**COMPLETE AUTHORITATIVE COVERAGE = YES**, because under the frozen §6 rules: every frozen
artifact exists; every size and SHA-256 matches the frozen value; every artifact was readable as
appropriate to its class; every eligible declarative artifact was completely inspected; every
artifact was classified exactly once; the deterministic candidate extraction completed; no scope
ambiguity remained; and **no extra unexpected artifact exists inside the frozen package root**.
No missing/extra/drifted/unreadable/unparseable/truncated/unclassified/ambiguous condition
occurred, so no condition had to be mapped to `SIC_EVIDENCE_INSUFFICIENT` and no
`HARNESS_INVALID` condition arose.

## 5. Artifact-by-artifact inspection summary (reconstructable evidence)

| Artifact | Class | Inspection performed | Candidate outcome | Reason |
| --- | --- | --- | --- | --- |
| `LICENSE` | `LICENSE_TEXT` | hash + identity only | **no candidates** | class not eligible for candidate extraction |
| `bin/opencode.exe` | `OPAQUE_COMPILED_BINARY` | hash + identity only | **no candidates** | class never supplies candidate fields; arbitrary strings are not evidence and were **not** scanned |
| `node_modules/opencode-windows-x64/bin/opencode.exe` | `OPAQUE_COMPILED_BINARY` | hash + identity only | **no candidates** | as above (also byte-identical to the declared bin) |
| `node_modules/opencode-windows-x64-baseline/bin/opencode.exe` | `OPAQUE_COMPILED_BINARY` | hash + identity only | **no candidates** | as above |
| `package.json` | `PACKAGE_METADATA` | full JSON parse + declared key-path enumeration (22 paths) + session-anchor predicate | **no candidates** | no declared key path denotes a session representation (session-anchor key paths: **none**) |
| `node_modules/opencode-windows-x64/package.json` | `PACKAGE_METADATA` | full JSON parse + declared key-path enumeration (5 paths) + session-anchor predicate | **no candidates** | session-anchor key paths: **none** |
| `node_modules/opencode-windows-x64-baseline/package.json` | `PACKAGE_METADATA` | full JSON parse + declared key-path enumeration (5 paths) + session-anchor predicate | **no candidates** | session-anchor key paths: **none** |
| `postinstall.mjs` | `INSTALLER_LOGIC` | read + deterministic top-level declaration scan + frozen eligibility test | **no candidates** | no explicitly declared contract structure (schema literal / exported schema-type / documented field table): **none**; session-anchor declarations: **none** |

## 6. `PACKAGE_METADATA` declared key paths inspected (deterministic enumeration)

* `package.json` (22 paths): `name`, `bin`, `bin.opencode`, `scripts`, `scripts.postinstall`,
  `version`, `license`, `os[]`, `cpu[]`, `optionalDependencies`, and the 12
  `optionalDependencies.<platform-package>` entries (`opencode-linux-arm64-musl`,
  `opencode-linux-x64`, `opencode-darwin-x64-baseline`, `opencode-windows-arm64`,
  `opencode-linux-arm64`, `opencode-darwin-arm64`, `opencode-windows-x64-baseline`,
  `opencode-linux-x64-baseline-musl`, `opencode-linux-x64-baseline`, `opencode-windows-x64`,
  `opencode-darwin-x64`, `opencode-linux-x64-musl`).
* `node_modules/opencode-windows-x64/package.json` (5 paths): `name`, `version`,
  `preferUnplugged`, `os[]`, `cpu[]`.
* `node_modules/opencode-windows-x64-baseline/package.json` (5 paths): `name`, `version`,
  `preferUnplugged`, `os[]`, `cpu[]`.

**Session-anchor predicate result: none of the 32 declared key paths denotes a declared session
representation** (no session record/incarnation object, type or schema, and no declared session
API surface), so — per the frozen §8 grammar — **no key path can enter the candidate set even if
its name looked identity-like**.

## 7. `INSTALLER_LOGIC` declared-structure extraction

Deterministic top-level declaration scan of `postinstall.mjs` returned only implementation
structures and module imports: `__dirname`, `require`, `packageJson`, `platformMap`, `archMap`,
`platform`, `arch`, `base`, `sourceBinary`, `targetBinary`, `supportsAvx2`, `isMusl`,
`packageNames`, `resolveBinary`, `installPackage`, `copyBinary`, `verifyBinary`, `main`, plus the
imports `childProcess`, `fs`, `os`, `path`, `createRequire`, `fileURLToPath`.

**Explicitly declared contract structures (schema literal / exported schema-type / documented
field table): none.**  Session-anchor declarations: **none**.  Therefore this artifact
contributes **no candidates**.  Platform/architecture maps and installer functions are
implementation detail; they declare no contract surface and are not evidence of session
semantics.

## 8. Ordered Phase-A candidate set (frozen)

**CANDIDATE COUNT = 0** — the ordered Phase-A candidate set is **empty**, frozen before any
semantic verdicting.  Phase B (semantic validation, criteria A–G) is therefore **not applicable
and was not performed**; no per-candidate verdicts and no A–G matrix exist because there is no
candidate to evaluate.

## 9. Global candidate SIC outcome and mapping rationale

**`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`.**

Mapping rationale — the frozen oracle §13 row **C** applies exactly: the authorized surface was
covered **completely and authoritatively** (§4) **and** the deterministic extraction produced
**zero candidates** (§8).  Rows A and B require at least one candidate (none exists) and row D
requires insufficient coverage/evidence (coverage was complete), so row C is the unique truthful
mapping.  No fifth outcome was invented and no per-candidate classification was promoted to a
global token.

## 10. Mandatory surface-scoped non-claim

> **This result applies only to the exact successfully inspected OpenCode 1.18.11 installed
> static package surface and the frozen target/package artifacts.**  It does **not** establish
> that OpenCode globally has no session-incarnation metadata.  It does **not** establish that a
> live/local OpenCode API exposes no additional contract surface.  It does **not** establish P6.
> It does **not** enable `adopt_completed_turn`.

Additional non-claims: no statement is made about any other OpenCode version, installation,
platform package, live endpoint, or about `/doc`, `/session`, event, message or session-state
surfaces (none was inspected); this result is a **pre-proof, surface-scoped finding** and creates
no Case-C design authority.

## 11. Activity counters (hard zero-live budget)

| Counter | Value |
| --- | --- |
| OpenCode starts / restarts | **0** |
| HTTP requests (including loopback) | **0** |
| `/doc` accesses | **0** |
| `/session` accesses | **0** |
| Runtime response reads | **0** |
| Provider calls / model calls / fake provider | **0 / 0 / 0** |
| Prompt submissions / session mutations | **0 / 0** |
| External network requests | **0** |
| Process discovery / port scanning / endpoint configuration | **0 / 0 / 0** |
| Authorized activity actually performed | local static reads, hashing and deterministic text extraction of the frozen manifest only |

No counter was nonzero outside the authorized local static file reads; no violation was recorded.

## 12. Privacy

No credentials, tokens, raw user prompts, model responses or reasoning were read or persisted.
The attempt inspected only the frozen local static package surface (three small JSON manifests,
one installer script, one license text) and hashed the compiled binaries without executing or
semantically scanning them.

## 13. Attempt discipline

* Attempts consumed: **1 of 1**; the single authorized Mode-A semantic attempt is complete.
* **No rerun**, no second manifest, no alternate installation, no alternate package/version, no
  live continuation, no Mode B/C, and no "verification rerun" constituting another semantic
  attempt.  A future rerun requires separate external authorization.
* The frozen oracle and the accepted SIC definition were **not** modified; no artifact drift or
  manifest update occurred (the observed tree matched the frozen manifest exactly).

## 14. Status after execution (candidate, not authoritative)

`SIC = EXECUTED ONCE / DEFINITION ACCEPTED / ORACLE ACCEPTED AND FROZEN / CANDIDATE RESULT =
SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT / AWAITING INDEPENDENT RESULT REVIEW`.

`G0.5 / P6 = NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP`;
`P6 = UNPROVEN / UNSATISFIED`.  Case-C implementation `NOT AUTHORIZED`; v0.3-E implementation
`NOT AUTHORIZED`; `G1 = NOT RUN`; `G2 = NOT RUN`; `adopt_completed_turn = DISABLED`.  This
candidate result must **not** be turned into P6 proof, and it changes no adoption or
implementation status.
