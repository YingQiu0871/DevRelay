# DevRelay v0.3-E — G0.5-PRE / SIC Mode-A pre-run oracle (candidate)

> **MODE A — OFFLINE / STATIC ONLY.**
> **PRE-RUN ORACLE CANDIDATE — NOT ACCEPTED, NOT FROZEN, NOT EXECUTED.**
> **SIC = `NOT RUN / DEFINITION ACCEPTED / ORACLE CANDIDATE`.**
> This document defines one future finding.  It proves nothing, executes nothing, and contains
> no SIC result.  It becomes the accepted immutable pre-run oracle only after a separate
> independent oracle review; execution then requires its own separate authorization.

## 1. Identity and baselines

| Item | Value |
| --- | --- |
| Repository HEAD at construction | `829d3c0b5b6bbe2898156b1f175293fb042c6373` |
| Branch | `v0.3-e-recovery-reconciliation` |
| Package version / public tags | `0.1.0` / `v0.1.0` only; no upstream |
| Accepted SIC definition baseline | commit `829d3c0b5b6bbe2898156b1f175293fb042c6373` |
| Accepted SIC definition artifact | `docs/v0.3/V03E_G0_5_PRE_SESSION_INCARNATION_FINDING.md` |
| Accepted SIC definition blob SHA-256 | `5463ac19ddc532f2a5f4f73c1076284f4c5f75b94338a5720a189b955e23ad11` |
| Accepted §25.1 extracted-block SHA-256 | `d3244ee0d24f5d740b34dac358378870d4d8238b0755787cffb7313d01044ee0` |
| G0.4 oracle blob SHA-256 (unrelated; preserved) | `b0c34fa19c3e639b5637d74d49e1c9c357b7db914ee1becf70229f3e5ed4bfa4` |
| G0.5 / P6 status (unchanged by SIC) | `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP`; P6 `UNPROVEN / UNSATISFIED` |
| G1 / G2 | `NOT RUN` |
| Case-C and v0.3-E implementation | `NOT AUTHORIZED` |
| `adopt_completed_turn` | `DISABLED` |

The accepted SIC definition artifact is treated as **immutable**: it is not modified by this
oracle (its internal header records its drafting/amendment status; the active status lives in
the accepted status surfaces and in this oracle).

## 2. Purpose, mode and rationale

This oracle precommits **one** future semantic attempt of the accepted SIC finding in
**MODE A — OFFLINE / STATIC ONLY**, implementing the accepted definition exactly.

* **No live fallback exists in this oracle.**  Mode B (live local read-only) and Mode C
  (precommitted staged static→live) are **not** authorized here and must not be entered, even
  if Mode A returns `SIC_EVIDENCE_INSUFFICIENT`.
* **Why Mode A is the correct first mode:** a positive SIC result requires **authoritative
  declared contract semantics**; runtime observations cannot create immutability, incarnation
  sensitivity, session scope, non-reuse or provenance authority (accepted definition §3.1,
  §12, §15).  The first bounded finding therefore inspects the exact locally installed contract
  surfaces offline.
* **Mode A may legitimately return a non-positive result.**  The purpose is truth, not
  obtaining a positive SIC outcome.
* Exactly **one** semantic attempt (§16).

## 3. Target identity

* Product: **OpenCode 1.18.11** as shipped by the npm package **`opencode-ai`**.
* Package root (Windows, environment-derived): `C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai`.
* Declared executable: `bin/opencode.exe` (per `package.json` `bin.opencode`).
* Main executable SHA-256: `578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35`.

At future execution the following identity checks are **mandatory before any semantic work**,
and any mismatch means the oracle is not applicable (stop; no retargeting): package name
`opencode-ai`; version `1.18.11`; package root resolves to the frozen root; declared bin
resolves to the frozen relative path; the declared executable hash equals the frozen value;
every manifest artifact exists with the frozen size and SHA-256.  The executable is **never
started, executed or signalled**.

## 4. Exact frozen manifest (Mode-A authorized surface)

Traversal order is **lexicographic normalized relative path order** (forward slashes,
case-sensitive).  These 8 files in 6 directories are the **entire** authorized surface; **no
artifact outside this manifest belongs to this oracle**.

| # | Relative path | Type | Size (bytes) | SHA-256 | Classification |
| --- | --- | --- | --- | --- | --- |
| 1 | `LICENSE` | (none) | 1,065 | `625f0f619133f89bbbb2abe37369613dfa1885eba1e50d02170deb62bb42cb6b` | `LICENSE_TEXT` |
| 2 | `bin/opencode.exe` | `.exe` | 174,182,280 | `578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35` | `OPAQUE_COMPILED_BINARY` |
| 3 | `node_modules/opencode-windows-x64-baseline/bin/opencode.exe` | `.exe` | 174,182,280 | `0e80c44457a95108e1932a1c31bcaddc011e143943f13624891a114b21262347` | `OPAQUE_COMPILED_BINARY` |
| 4 | `node_modules/opencode-windows-x64-baseline/package.json` | `.json` | 149 | `f4b19768d7d29e0f49f2049571b1b9f9873f85e27a6365a553833c7939f019cf` | `PACKAGE_METADATA` |
| 5 | `node_modules/opencode-windows-x64/bin/opencode.exe` | `.exe` | 174,182,280 | `578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35` | `OPAQUE_COMPILED_BINARY` |
| 6 | `node_modules/opencode-windows-x64/package.json` | `.json` | 140 | `19b744c84045d274b02b482b9cbef518d2c8b397afda935356af105da3e55d2c` | `PACKAGE_METADATA` |
| 7 | `package.json` | `.json` | 825 | `de1da8f30650084a6261fe9a87a3126a63a6ea1365db2acdecb1cde640a86ee2` | `PACKAGE_METADATA` |
| 8 | `postinstall.mjs` | `.mjs` | 5,496 | `5a7c990fe552e76b16422cdba3f4b0550590c7a487f7932c773362f74317c87b` | `INSTALLER_LOGIC` |

Directories (6): `bin`, `node_modules`, `node_modules/opencode-windows-x64`,
`node_modules/opencode-windows-x64/bin`, `node_modules/opencode-windows-x64-baseline`,
`node_modules/opencode-windows-x64-baseline/bin`.

The manifest was re-enumerated statically at construction and matches the installed tree
exactly (8 files / 6 directories).  At execution the tree must be re-enumerated and must match
this manifest **exactly**, including the absence of any extra file inside the package root.

## 5. Artifact classification (exactly one class per artifact)

| Class | Meaning | Candidate/semantic role |
| --- | --- | --- |
| `DECLARATIVE_CONTRACT_CANDIDATE` | an artifact that **declares** a contract surface: a schema/OpenAPI document, a generated client/type definition, or declarative field documentation | eligible for candidate extraction and (if it declares semantics) for semantic authority |
| `PACKAGE_METADATA` | package/install metadata (`package.json` and platform sub-package manifests) | eligible for extraction **only** for declared contract structures; as installed it declares no session representation |
| `INSTALLER_LOGIC` | imperative install/provisioning script | eligible for extraction **only** for explicitly declared contract structures (schema literals, exported type/schema definitions, documented field tables) |
| `LICENSE_TEXT` | license prose | not eligible |
| `OPAQUE_COMPILED_BINARY` | compiled executable image | **never** supplies candidate fields or semantic authority; it may be hashed, identified and recorded only |

No artifact may be classified twice, and no artifact may be left unclassified.  Arbitrary
strings inside `OPAQUE_COMPILED_BINARY` artifacts are **not** evidence (accepted definition
§14): they may at most locate a surface, and this oracle authorizes **no** candidate creation
from them.

## 6. Complete-coverage rule

Mode-A **complete coverage** holds only if **all** of the following succeed under the frozen
deterministic rules:

1. every frozen manifest artifact exists;
2. every artifact's size and SHA-256 match the frozen values;
3. every artifact is readable as appropriate to its class;
4. every eligible declarative artifact is **completely** inspected;
5. every artifact is classified exactly once;
6. the deterministic candidate extraction completes;
7. no scope ambiguity remains (no unclassifiable artifact, no ambiguous eligibility);
8. **no extra unexpected artifact exists inside the frozen package root**.

Any missing artifact, extra unexpected artifact inside the package root, hash drift, read
failure, parse failure, truncation, unclassified artifact or ambiguous eligibility
**prevents** `SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT` and maps — per the accepted definition — to
`SIC_EVIDENCE_INSUFFICIENT`, unless the condition falls strictly inside the already accepted
`HARNESS_INVALID` **pre-assertion** boundary.

## 7. Deterministic, enumerable candidate-extraction rule

No human "promising-field" selection is permitted during execution.  The rule is mechanical
and enumerable:

* **R1 — Traverse** the frozen manifest in the frozen lexicographic order.
* **R2 — Apply the class rule** of §5 per artifact: `OPAQUE_COMPILED_BINARY` and `LICENSE_TEXT`
  yield no candidates; `PACKAGE_METADATA` enumerates every **declared JSON key path**
  (deterministic dotted path, arrays indexed by `[]`); `INSTALLER_LOGIC` enumerates only
  explicitly **declared** contract structures (schema literals, exported type/schema
  definitions, documented field tables) and never imperative statements, local variable names,
  filesystem paths or embedded binary strings; `DECLARATIVE_CONTRACT_CANDIDATE` enumerates every
  declared property of every session representation/object, including nested objects and arrays
  of objects.
* **R3 — Apply the discovery grammar** (§8) to each enumerated key path; a key path enters the
  candidate set only if the grammar matches **and** the key path is anchored to a declared
  session representation.
* **R4 — Aliases by deterministic rule only**: names are normalized (lowercase; non-alphanumeric
  characters removed) before grammar matching, so `sessionID`, `session_id`, `sessionId` and
  `sessionid` are treated identically; dotted nesting is preserved.  No further alias inference
  is permitted.
* **R5 — Forbidden candidate sources** (must never create a candidate): arbitrary executable
  strings; UUID-looking byte sequences; token frequencies; undocumented internal tokens;
  field-name guesses detached from a session contract; license or installer prose.
* **R6 — Ordered output**: the candidate set is emitted in manifest order, then key-path
  lexicographic order within an artifact, each entry recording artifact, exact source location,
  declared type and the exact relevant declarative text (if any).

## 8. Candidate discovery grammar

A field/property/tuple is a **candidate** only if **both** hold:

1. **Session anchor** — the frozen contract surface associates it with a **session
   representation**: a declared object/type/schema whose declared name or description denotes a
   session record/incarnation, or a declared session API surface.  A name that merely contains
   a session-like token without a declared session representation is **not** a candidate.
2. **Plausible identity semantics** — its declared type/description/contract placement could
   plausibly bear: identity; creation identity; incarnation; generation; revision; a stable
   creation marker; record identity; an immutable session key; or equivalent per-session
   identity semantics.

Discovery **must not** promote a candidate semantically; it only places it into Phase B.
Ancestry fields, created-like identity fields and opaque server-generated session properties
are **not** excluded from discovery merely because current DevRelay code does not parse them —
their semantic verdict remains governed by §11.

## 9. Discovery before validation (frozen execution order)

**PHASE A** — (1) identity/manifest verification (§3, §4); (2) complete static-surface coverage
(§6); (3) deterministic candidate extraction (§7, §8); (4) **freeze the ordered candidate set**.

**THEN AND ONLY THEN — PHASE B** — semantic validation of the frozen candidates (§10–§12).

No candidate may be added or removed after Phase B begins.  A candidate later classified
`NON_QUALIFYING_METADATA` **remains a discovered candidate**: semantic non-qualification must
never be used to turn "candidate exists" into "zero candidates".

## 10. Per-candidate verdicts and record

Per-candidate conclusions use exactly the accepted vocabulary: **`QUALIFIES`**,
**`SEMANTICS_UNPROVEN`**, **`NON_QUALIFYING_METADATA`** (per-candidate only; never global
tokens).

For every candidate the record must contain: candidate name/tuple; artifact; exact source
location; declared type; exact relevant declarative semantics; criterion A verdict; criterion B
verdict; criterion C verdict; criterion D verdict; criterion E verdict; criterion F verdict;
criterion G verdict; semantic-authority source; unproved-proof dependency (if any); and the
per-candidate verdict.

## 11. Qualifying criteria (all required for `QUALIFIES`)

* **A. SESSION-SCOPED** — declared semantics bind the candidate to the **specific session
  record/incarnation**.  Server-, process-, project- or workspace-level metadata **cannot**
  satisfy A.
* **B. INCARNATION-SENSITIVE** — authoritative contract semantics support the conclusion that a
  distinct recreated/replaced/new session incarnation **cannot legitimately present the same
  anchor while remaining contract-conformant**.  Words such as `id`, `unique`, `created`,
  `timestamp` or `session identifier` are **insufficient** unless their declared semantics
  establish that distinction; otherwise **B is not established** and the candidate cannot be
  positive.
* **C. STABLE FOR THE SAME INCARNATION** — authoritative semantics show suitability for
  comparison across the relevant recovery interval for the **same** incarnation.  Mutable
  metadata (`updated_at`, `status`, revision counters, `title`, route/agent/model fields) does
  **not** satisfy C merely because it is readable.
* **D. READ-ONLY OBSERVABLE** — in Mode A this may be established **only** by the declared
  read-only session representation/API/schema contract (no live read is performed).
* **E. LOCALLY PERSISTABLE / COMPARABLE** — a concrete serializable/comparable representation
  suitable for DevRelay persistence.  Persistability does **not** create provenance authority.
* **F. SEMANTICALLY ESTABLISHED** — supported by authoritative declared semantics (§12), never
  by a name, type name, UUID/timestamp shape, sample value, frequency, apparent uniqueness or
  source-naming inference.
* **G. NO DISQUALIFYING UNPROVED P2/P3/P8/P9 DEPENDENCY** — if a candidate requires an
  assumption from P1/P2/P3/P8/P9 that is not already accepted, the dependency is recorded and
  the candidate is **not currently established**.

`QUALIFIES` requires **all** of A–G.  There is **no partial positive** result.

## 12. Semantic authority in Mode A

**Eligible:** explicit schema descriptions; formal bundled field documentation; bundled
OpenAPI descriptions; generated contract comments traceable to the installed schema;
version-matched bundled official documentation; equivalent explicit declarative contract
material inside the frozen surface.

**Not semantic authority:** field names; type names; UUID shape; timestamp shape; variable
names; binary strings; sample values; frequency; apparent uniqueness; inference from source
naming.  Runtime observations are unavailable in Mode A and, per the accepted definition, could
never independently establish immutability, incarnation sensitivity, session scope, non-reuse,
uniqueness, stability or provenance authority.

## 13. Outcome mapping (accepted amended definition; exactly four outcomes)

| # | Reachable state | Global outcome |
| --- | --- | --- |
| **A** | ≥ 1 candidate `QUALIFIES` | `SIC_PRESENT_AND_SEMANTICS_ESTABLISHED` |
| **B** | 0 candidates qualify **and** ≥ 1 candidate exists — including all `SEMANTICS_UNPROVEN`, all `NON_QUALIFYING_METADATA`, or a mixture | `SIC_METADATA_PRESENT_BUT_SEMANTICS_UNPROVEN` |
| **C** | complete authoritative coverage **and** zero candidates | `SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT` |
| **D** | coverage/evidence insufficient to authoritatively perform the required classification | `SIC_EVIDENCE_INSUFFICIENT` |

`HARNESS_INVALID` remains **outside** the four semantic outcomes (pre-assertion
harness/environment failure only).  Sufficient negative evidence (complete coverage +
sufficient authoritative semantics + affirmative non-qualification) is **never**
`SIC_EVIDENCE_INSUFFICIENT`, and no fifth outcome may ever be introduced.

## 14. `NOT_EXPOSED` non-claim (mandatory wording if outcome C occurs)

> This result applies **only** to the exact successfully inspected OpenCode 1.18.11 installed
> static package surface and the frozen target/package artifacts.  It does **not** establish
> that OpenCode globally has no session-incarnation metadata, and it does **not** establish
> that a live/local API exposes no additional contract surface.

## 15. No live fallback; activity budget

**Mode A only.**  Budget for the one future attempt: OpenCode starts **0**; HTTP **0**;
`/doc` **0**; `/session` **0**; runtime response reads **0**; provider/model calls **0**; fake
provider **0**; prompt submissions **0**; session mutations **0**; external network **0**.
Process discovery, port scanning and endpoint configuration are **0**.  If the semantic result
is `SIC_EVIDENCE_INSUFFICIENT`, the run **ends**; it must not continue into Mode B or Mode C.

## 16. One attempt

Exactly **one** SIC Mode-A semantic attempt.  No retry for a different answer; no second static
surface; no alternate package or version; no manifest update after observing results; no
candidate or fixture changes after Phase B begins.  Any rerun requires **new external
authorization**.

## 17. Artifact drift

Package/artifact identity is frozen in §4.  If at execution time the tree, version, sizes or
hashes differ from the oracle, the oracle must **not** be updated in place: follow the frozen
coverage/drift rules (§6), classify the condition per the accepted definition, and stop as
appropriate (`SIC_EVIDENCE_INSUFFICIENT`, or `HARNESS_INVALID` strictly inside the pre-assertion
boundary).  No silent retargeting.

## 18. Evidence artifact schema (future result artifact)

Repository HEAD; branch/worktree; accepted SIC definition baseline/hash; accepted SIC oracle
baseline/hash; OpenCode package/product version; package root; the frozen manifest (paths,
types, sizes, SHA-256, classifications); coverage evidence; candidate-extraction rule identity;
ordered Phase-A candidate set; per-candidate evidence and verdicts; the A–G criterion matrix;
semantic-authority source per candidate; global SIC outcome; surface-scoped non-claims;
`HARNESS_INVALID` vs semantic classification; activity counters; privacy statement.

**Never persisted:** credentials, tokens, raw user prompts, model responses, reasoning.  No
executable is run, and no secret or user content is read.

## 19. Freezability self-check performed at construction

* Every reachable Mode-A state maps to exactly one accepted outcome or `HARNESS_INVALID`
  (§13; the 11-row matrix of the accepted definition §5.4 is fully covered).
* No discovered candidate can be retroactively erased (§9).
* `NON_QUALIFYING_METADATA` maps globally through outcome #2 (§13, row B).
* `NOT_EXPOSED` requires complete coverage **and** zero candidates (§6, §13 row C).
* Sufficient negative evidence is never `EVIDENCE_INSUFFICIENT` (§13).
* Compiled-binary strings supply no candidate and no semantic authority (§5, §7 R5, §12).
* No live fallback exists (§2, §15).
* No fifth outcome is introduced (§13).
* No accepted SIC definition rule is modified by this oracle: the definitions of the four
  outcomes, the per-candidate vocabulary, the criteria A–G, the semantic-authority rules, the
  mode rules and the coverage rules are used exactly as accepted.

## 20. Surface-scoped construction fact (not a SIC result)

Recorded as a **construction observation only**: the frozen manifest (§4) contains **zero**
`DECLARATIVE_CONTRACT_CANDIDATE` artifacts, and its `PACKAGE_METADATA` / `INSTALLER_LOGIC`
artifacts declare no session representation.  Consequently a future execution's Phase A is
*expected* to freeze an empty candidate set and — if coverage completes — to reach outcome C.
**This expectation is not the SIC outcome**, must not be pre-recorded as a result, and does not
authorize any inference beyond the inspected surface.

## 21. Non-claims of this oracle round

This document defines a future finding; it performs none of it.  It starts no OpenCode
instance, issues no HTTP request, reads no `/doc` or `/session` surface, inspects no live
endpoint, configures nothing, implements no Case-C logic, proves nothing about P6, and creates
no result/proof artifact.  It is **not** accepted, **not** frozen and **not** executed; no SIC
semantic attempt has occurred.  `G0.5 / P6 = NOT RUN / DEFINITION ACCEPTED / ORACLE NOT
FREEZABLE / LOCAL REACHABILITY GAP` with `P6 = UNPROVEN / UNSATISFIED`; `G1` and `G2` remain
`NOT RUN`; adoption remains **DISABLED**; implementation remains **NOT AUTHORIZED**; the
accepted §25.1 definition and the G0.4 artifacts are untouched.
