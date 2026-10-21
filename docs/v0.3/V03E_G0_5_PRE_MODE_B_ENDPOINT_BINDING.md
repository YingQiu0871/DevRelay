# DevRelay v0.3-E — G0.5-PRE / SIC — Mode-B endpoint / target-binding prerequisite (ETB)

> **MODE-B ENDPOINT / TARGET-BINDING PREREQUISITE**
> **DEFINITION CANDIDATE**
> **NOT ACCEPTED**
> **NOT EXECUTED**
> **DOES NOT ESTABLISH AN ENDPOINT**
> **DOES NOT AUTHORIZE CONFIGURATION CHANGE**
> **DOES NOT AUTHORIZE OPENCODE LAUNCH**

Status: **ETB = DEFINITION CANDIDATE / NOT ACCEPTED / NOT EXECUTED / NOT AUTHORIZED**

This artifact is a **definition only**.  It establishes no endpoint, changes no configuration,
starts nothing, binds no listener, issues no HTTP, executes no SIC attempt, and creates neither
an ETB execution oracle nor a Mode-B SIC oracle.  Abbreviation used throughout: **ETB**
(Endpoint / Target Binding).

Baseline: `b8fb639bf2c9561505b1c26595e0d9c5aad66c4c` (branch `v0.3-e-recovery-reconciliation`).

Frozen identities this definition is anchored to (committed Git blobs):

| Anchor | Identity |
| --- | --- |
| accepted SIC definition | `docs/v0.3/V03E_G0_5_PRE_SESSION_INCARNATION_FINDING.md`, commit `829d3c0`, blob `5463ac19ddc532f2a5f4f73c1076284f4c5f75b94338a5720a189b955e23ad11` |
| accepted/frozen Mode-A oracle | `docs/v0.3/V03E_G0_5_PRE_SIC_ORACLE.md`, commit `e1fb6ac`, blob `31d7ac5020ba6a7e3a4eb700df0feedc8f480d67a89f7124091e87df9ff7dc78` |
| reviewed Mode-A result | `docs/v0.3/V03E_G0_5_PRE_SIC_RESULT.md`, blob `ce6c503d3bd62fa09c34d52bbd570e1a98dab403d1164b2e740fe6c476ecadc6` |
| §25.1 protected block | `docs/v0.3/V03E_SPEC.md` §25.1, blob `d3244ee0d24f5d740b34dac358378870d4d8238b0755787cffb7313d01044ee0` |
| G0.4 oracle (prior-art binding definition) | `docs/v0.3/V03E_G0_4_API_INSPECTION_ORACLE.md`, blob `b0c34fa19c3e639b5637d74d49e1c9c357b7db914ee1becf70229f3e5ed4bfa4` |
| accepted target | OpenCode / `opencode-ai` **1.18.11**, declared executable `C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe`, SHA-256 `578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35` |

---

## 1. Purpose, scope and non-goals

**1.1 Purpose.**  ETB is the narrow **pre-oracle** prerequisite that must be satisfied before a
Mode-B (live local read-only) SIC oracle can be constructed.  It defines the
infrastructure/control conditions that make a later Mode-B oracle **target-specific and
non-ambiguous**: an explicit authorized endpoint, a precommitted establishment mode, and a
deterministic endpoint→process identity chain.

**1.2 In scope.**  Endpoint authority, endpoint-selection ownership, required endpoint form, the
deterministic port-policy requirement, the two allowed target-establishment modes, the
target-binding identity chain, continuity requirements, the configuration boundary, the
no-endpoint-shopping rule, fail-closed conditions, the satisfaction/unsatisfied semantics, the
status model and the sequencing to the Mode-B SIC oracle.

**1.3 Out of scope (non-goals).**  ETB does **not** select an actual endpoint, address family or
port; does **not** authorize a configuration change; does **not** authorize launching OpenCode;
does **not** bind or verify a real listener; does **not** issue HTTP; does **not** define a
Mode-B request set or `/doc` completeness; does **not** design the ETB execution oracle; and does
**not** implement Case C.

## 2. Role in the proof ladder

**2.1 ETB is a PRE-ORACLE prerequisite only.**  It sits **outside P1–P9** and is **not** a
P-number, not a proof, and not a gate of the adoption ladder.

**2.2 ETB does NOT prove or establish** P6; G0.5; SIC semantics; session incarnation; turn
provenance; message provenance; pending-handle semantics; or any v0.3-E implementation
property.

**2.3 ETB success enables exactly one thing:** *Mode-B SIC oracle construction may resume.*
ETB success does **not** enable Mode-B execution, G0.5, Case-C implementation, adoption,
implementation authorization, or any release action.  Those each require their own separate
authorization under the existing ladder.

**2.4 Relation to existing statuses.**  ETB is not G0.5/P6, not SIC, not G0.4, and not a
substitute for the Mode-A finding; the Mode-A result and the Mode-B endpoint-gate finding remain
separately authoritative within their own scopes (§3).

## 3. Current authoritative facts (preserved, not redefined)

**3.1 Endpoint authority (current).**  The only supported current runtime endpoint authority for
DevRelay's local OpenCode bridge is:

```
<root>/.devrelay/config.yaml
→ opencode.base_url
```

with the `OpenCodeConfig` empty-string model default as the absent/empty fallback.  Its current
value is `""`.  **No endpoint currently exists in accepted configuration/state.**  This is the
independently approved endpoint finding and is **not** redefined here; no alternative endpoint
source is introduced (§5).

**3.2 Mode-A.**  Mode A remains **completed and authoritative** with
`SIC_NOT_EXPOSED_IN_INSPECTED_CONTRACT`, strictly scoped to the exact successfully inspected
OpenCode 1.18.11 installed static package surface and frozen target/package artifacts.  Mode A is
not reopened, reinterpreted or weakened by ETB.

**3.3 Mode-B endpoint-gate finding (authoritative).**
`SIC MODE-B ORACLE NOT FREEZABLE — CONCRETE ENDPOINT NOT ESTABLISHED` under current accepted
configuration/state; Mode-B status =
`NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED / PRE-ORACLE
CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`.  No semantic Mode-B attempt occurred.

**3.4 G0.5 / P6.**  `NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY
GAP`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 **NOT CLOSED**.

**3.5 Implementation / adoption.**  Case-C implementation = `NOT AUTHORIZED`; v0.3-E
implementation = `NOT AUTHORIZED`; `G1`/`G2` = `NOT RUN`; `adopt_completed_turn` = `DISABLED`.

## 4. Accepted prior art: the G0.4 binding definition and its limits

**4.1 Prior art.**  The accepted, immutable G0.4 oracle already freezes a reviewed, read-only,
**endpoint-scoped** target-binding definition (its §8.1–§8.8): configured-endpoint-only
resolution; concrete loopback address/port resolution; address-family/listener ambiguity
fail-closed; package declared-bin binding; executable SHA-256 binding; process creation/start
identity; the pre-request `TARGET_BOUND` snapshot; and the post-request continuity snapshot.  ETB
**aligns with and reuses that semantics** instead of inventing a new mechanism, and keeps its
rule that local port/process metadata is **proof evidence only** — never a runtime
endpoint-resolution mechanism, never a way to select, adopt or reconfigure an endpoint.

**4.2 Limits of the prior art (explicit).**  That definition was **never executed**: G0.4's single
authorized execution ended at Case A with `TARGET_IDENTITY_UNRESOLVED` (no OpenCode base endpoint
was configured), issued **0** loopback HTTP requests / **0** `GET /doc`, and bound no target
instance.  It is therefore a reviewed **definition**, **not** validated capability evidence.  Its
concrete mechanism is described generically (a listening-socket listing plus a process query),
and its process-creation-identity statement is an assertion on the accepted Windows proof
environment that has never been exercised in practice.  ETB consequently treats the concrete
mechanisms as **future ETB-oracle requirements** (§26), not as solved facts, and never as
authority to select an endpoint.

## 5. Endpoint authority — future state

**5.1 Exact authority.**  The future authoritative endpoint source is defined as exactly:

```
<root>/.devrelay/config.yaml
→ opencode.base_url
```

**No alternative authority.**

**5.2 Forbidden endpoint authority.**  The following are explicitly **not** endpoint authority
and may never supply, imply, corroborate or substitute for the configured endpoint:

* environment fallback;
* profile fallback;
* CLI fallback;
* state/task snapshot;
* runtime log;
* database;
* port scan;
* listener scan;
* process scan;
* OpenCode provider upstream `baseURL` (an upstream model-provider endpoint, never the local
  OpenCode service endpoint);
* documentation example (including the illustrative `http://127.0.0.1:4096` comment text);
* implicit `localhost`;
* implicit default port.

**5.3 Explicitness requirement.**  The endpoint must become **explicit** in the authoritative
source before Mode-B SIC oracle construction resumes.

## 6. Endpoint-selection ownership

**6.1 Ownership is EXTERNAL / OWNER-AUTHORIZED.**  The executor **MUST NOT** invent the endpoint.
A future endpoint-establishment round must receive — or derive under an independently accepted
deterministic policy (§8) — an exact tuple:

* scheme;
* numeric loopback address;
* address family;
* port;
* base URI.

**6.2 No convenience selection.**  The agent performing establishment must not choose a value
because it is common, historical, documented as an example, previously used, or
available-looking.

**6.3 No automatic values.**  In particular `127.0.0.1:4096` is **NOT** automatically selected;
`localhost` is not selected; IPv4 is not preferred over IPv6 (or vice versa) by default; and no
default port is assumed.

## 7. Required endpoint form

**7.1 Shape (unless an independently reviewed future design requires otherwise).**

| Element | Requirement |
| --- | --- |
| scheme | `http` |
| host | a **numeric loopback address** (no hostname) |
| address family | **explicitly** IPv4 **or** IPv6 |
| port | an **explicit integer** in the valid TCP range |
| base URI | contains no ambiguity and no hostname expansion |

**7.2 No value is selected here.**  This definition round selects no address family, no address
and no port.  The concrete tuple remains externally authorized (§6).

**7.3 Non-loopback is invalid.**  Any endpoint whose destination is not loopback is fail-closed
(§19).

## 8. Deterministic port policy

**8.1 Requirement, not a value.**  A future establishment round **MUST precommit one
deterministic port policy before changing configuration**.  This definition freezes the
requirement and the admissible policy classes, **not** an actual port.

**8.2 Admissible policy classes.**

* **A — OWNER-SUPPLIED FIXED PORT.**  The external owner explicitly supplies the exact port.
  This is available today.
* **B — INDEPENDENTLY ACCEPTED DETERMINISTIC ALLOCATION POLICY.**  A **separately reviewed and
  accepted** policy deterministically yields exactly one port without probe-shopping.  Class B is
  admissible **only** once such a concrete policy exists and is accepted; until then it is
  unavailable, and this definition does not invent one merely to keep the option open.

**8.3 Forbidden.**  The following are forbidden in every case:

* trying `4096` and then another port;
* picking the first free port;
* scanning a port range;
* random port selection;
* OS-assigned ephemeral port **without** a precommitted durable way to freeze the resulting
  endpoint before Mode-B SIC oracle construction (no such durable-freeze design exists today, so
  this is currently inadmissible);
* choosing a port based on observed listener failures;
* any retry with a different port.

**8.4 Failure semantics.**  If the precommitted port cannot be bound, the authorized attempt
**ends** — the result is ETB **NOT SATISFIED** (§19, §21) and no alternate port or address may be
tried (§18).

## 9. Two target-establishment modes

**9.1 Exactly two mutually exclusive modes are allowed:**

* **MODE L — CONTROLLED LAUNCH** (§11); and
* **MODE P — PRE-EXISTING TARGET** (§12).

**9.2 No other mode exists.**  No hybrid, no implicit third mode, and no "either, whichever
works" behaviour is permitted.

**9.3 No selection in this definition round.**  The independent review determined that
"DevRelay itself must launch OpenCode" was **TOO STRONG / MECHANISM NOT YET DETERMINED**;
therefore this round **does not choose** between Mode L and Mode P, unless accepted evidence
makes one unsound.  No accepted evidence currently makes either mode unsound; Mode L is instead
made **conditional** on a missing capability determination (§11.3).

## 10. Mode precommit, no fallback, no mode shopping

**10.1 Precommit.**  A future ETB execution **MUST select exactly one mode before any operational
action** (before configuration change, launch, or any binding work), and record that selection in
its oracle.

**10.2 No runtime fallback.**  There is **no** `L → P` and **no** `P → L` fallback after a
failure.  A failure in the selected mode ends that authorized attempt.

**10.3 No mode shopping.**  Trying the other mode after a failure within the same authorization is
forbidden.

**10.4 Changing mode requires new external authorization** — and, if the accepted design requires
it, a new or follow-up oracle.  A mode switch may never be a side effect of a failed attempt.

## 11. MODE L — controlled launch semantics

**11.1 If a future execution precommits Mode L, it must satisfy all of:**

* the exact OpenCode version must be **1.18.11**;
* the exact executable path must be frozen;
* the executable hash must match the accepted target hash
  (`578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35`);
* the exact numeric loopback address, address family and port must **already be externally
  authorized** (§6);
* the launch arguments must **explicitly bind that exact address and port**;
* the launch action must **return or otherwise directly establish the target PID** (the PID is
  obtained from the launch act itself, not from a scan);
* **no listener/process scanning** may be used to choose the target;
* the launched process identity must be recorded;
* listener ownership must later be verified **against that exact process**;
* failure to bind the requested endpoint must **stop the attempt**;
* **no alternate port or address** may be used.

**11.2 No flag guessing.**  No specific launch flag, subcommand or CLI syntax may be asserted
unless authoritative evidence supports it.

**11.3 LAUNCH-CAPABILITY GAP (recorded, not solved).**  The exact OpenCode 1.18.11 **launch CLI
syntax, and the capability to bind a caller-chosen address/port**, are **UNESTABLISHED** in
accepted evidence: the accepted v0.3-A artifacts record only that a dedicated loopback
`opencode serve` server was used for the historical A33 smoke, and no accepted artifact freezes
its flags or establishes explicit address/port binding.  **MODE L is therefore dependent on a
later, separately reviewed launch-capability determination.**  Until that determination exists
and is accepted, Mode L cannot be precommitted and only Mode P is potentially available.

## 12. MODE P — pre-existing target semantics

**12.1 Precondition.**  If a future execution precommits Mode P, the endpoint tuple must **already
be explicitly present** in the authoritative DevRelay configuration (§5) before the attempt.

**12.2 Deterministic, precommitted binding.**  The binding mechanism must be deterministic and
precommitted in the ETB oracle.  It may verify ownership of the **EXACT already-frozen endpoint**;
it must **not** broadly discover endpoints.

**12.3 Discovery vs verification (distinct).**  The definition distinguishes:

* **endpoint discovery** — searching for, enumerating or inferring candidate endpoints,
  listeners, ports or processes: **forbidden**; from
* **endpoint-scoped owner verification** — querying only the already-frozen exact endpoint to
  determine its owning process: **potentially admissible**.

**12.4 Admissibility of a read-only OS mechanism.**  A future read-only OS mechanism **may** be
acceptable **if and only if** it queries only the already-frozen exact endpoint and
deterministically returns its owning PID, with no broad port or process scan.  If more than one
owner/result is possible, or ownership is ambiguous, the result is **FAIL CLOSED** (§19).

**12.5 MECHANISM GAP (recorded, not solved).**  No concrete OS command/API is specified as
authoritative by this definition: the accepted prior art describes the mechanism only generically
and was never executed (§4.2).  The concrete primitive, and the demonstration that it has the
required semantics on this platform, remain a **future ETB-oracle requirement** (§26).  This
definition freezes the required **semantic properties**; the future oracle establishes the
concrete mechanism.

## 13. Target-binding chain

**13.1 Required identity chain (either mode):**

```
authoritative endpoint tuple
→ exact listener
→ unique owning PID
→ canonical executable path
→ executable SHA-256
→ exact OpenCode version
→ process creation identity where available
```

**13.2 No single element alone is sufficient.**  A matching process name, a listening port, a
matching PID, a matching path, or a matching hash each prove nothing on their own; the chain must
be complete, deterministic and reviewable, and the equality requirements of the accepted prior
art (§4.1) apply.

## 14. Pre-request / post-request continuity

**14.1 ETB defines what later Mode-B execution must support** — a **PRE-REQUEST TARGET SNAPSHOT**
and a **POST-REQUEST TARGET SNAPSHOT** with full equality of:

* the same frozen endpoint;
* the same listener identity;
* the same PID;
* the same canonical executable path;
* the same executable hash;
* the same process creation identity where available;
* the same OpenCode version.

**14.2 ETB itself performs no Mode-B HTTP.**  ETB establishes only the conditions under which such
continuity can be taken and checked; it issues no request and reads no `/doc` or `/session`.

**14.3 Mismatch is invalidating.**  Any mismatch at later Mode-B execution invalidates the
binding evidence; no semantic SIC result may be derived from a changed target.

## 15. Process-creation identity

**15.1 Required property.**  "Process creation identity where available" means a
**platform-observable property capable of distinguishing a later process reuse of the same PID**
— for example an OS process creation/start timestamp, or another stable per-process-instance
identifier.

**15.2 Semantics must be platform-supported.**  The field's semantics must be supported by the
platform; the property may not be asserted merely because a similarly named field exists.

**15.3 PID alone is insufficient.**  A PID alone never proves process continuity.

**15.4 Unavailability must be explicit.**  If the property cannot be obtained, the later
target-binding oracle must **classify the resulting limitation explicitly** — as a fail-closed
condition (§19) — rather than silently dropping the criterion.  The accepted prior art's stricter
stance (creation/start identity is required on the accepted Windows proof environment and "not
available" is not an accepted answer) is carried forward as the default; any deviation requires a
separately reviewed design that names the limitation.

## 16. Version binding

**16.1 Target.**  The target remains exactly OpenCode / `opencode-ai` **1.18.11**, declared
executable `C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe`, accepted
executable SHA-256
`578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35`.

**16.2 No substitution.**  No alternate version, no second installation (including desktop
builds), no alternate binary, and no silent retargeting is permitted.

## 17. Configuration-establishment boundary

**17.1 A future ETB establishment action may be authorized to set**

```
.devrelay/config.yaml
→ opencode.base_url
```

**ONLY after** the exact endpoint tuple is externally authorized (§6) **and** the selected mode is
precommitted (§10).  This round performs no such change and grants no such authorization.

**17.2 Configuration is not binding.**  Setting `base_url` **does not** prove target binding.  A
configured endpoint without valid target-binding evidence remains **INSUFFICIENT** for Mode-B SIC
oracle construction.

**17.3 Ordering.**  Endpoint authorization → mode precommit → (authorized) configuration
establishment → (authorized) binding work → binding evidence → independent ETB result review →
(only if ETB SATISFIED) Mode-B oracle construction may resume.  No step may be skipped or merged.

## 18. No-endpoint-shopping rule

**18.1 Frozen prohibition.**  The following are forbidden:

* no `localhost` variant fallback;
* no IPv4/IPv6 fallback;
* no port retry;
* no alternate process;
* no second installation;
* no alternate binary;
* no history-derived endpoint;
* no log-derived endpoint;
* no "first listener found";
* no "first free port";
* no silent relaunch using another endpoint.

**18.2 One endpoint, one attempt.**  Exactly one endpoint and exactly one selected mode per
authorized attempt; a failure ends the attempt and does not license an alternative.

## 19. Fail-closed conditions

**19.1 Each of the following yields ETB NOT SATISFIED** (fail closed, no partial credit):

endpoint absent; endpoint malformed; endpoint non-loopback; address-family ambiguity; port
unspecified; configured endpoint differs from the authorized endpoint; listener missing; listener
ambiguous; multiple owners; owner PID unavailable; canonical executable unresolved; executable
path mismatch; binary hash mismatch; version mismatch; process creation identity required but
unavailable; selected-mode precondition missing; mode switch attempted.

**19.2 Not SIC results.**  None of these may be reinterpreted as a SIC result, as `P6 FAIL`, as
`G0.5 FAIL`, or as evidence that OpenCode cannot support Mode B.  They are prerequisite/control
outcomes only (§21).

## 20. ETB SATISFIED

**20.1 Definition.**  ETB is **SATISFIED** only when a future, independently authorized execution
produces **one unambiguous evidence package** containing:

* the exact authoritative endpoint tuple;
* the exact selected ETB mode;
* the configuration binding;
* unique listener ownership;
* a unique PID;
* the canonical executable path;
* the expected executable hash;
* the OpenCode version;
* process creation identity where available;
* pre/post continuity capability;
* no-shopping compliance.

**20.2 Non-claims.**  ETB SATISFIED is **not** `SIC PASS`, **not** `P6 PASS`, and **not** `G0.5
PASS`.  It enables only the resumption of Mode-B SIC oracle **construction** (§2.3, §23).

## 21. ETB UNSATISFIED

**21.1 ETB UNSATISFIED is a prerequisite/control result only.**  It means: **Mode-B SIC oracle
construction remains blocked.**

**21.2 It does NOT mean** SIC failed; P6 failed; G0.5 failed; or that OpenCode cannot support
Mode B.

## 22. Status model

**22.1** Before execution: `ETB = DEFINITION CANDIDATE` (**current status**).

**22.2** After independent definition approval: `ETB = DEFINITION ACCEPTED / NOT EXECUTED`.

**22.3** A future execution result may be `ETB SATISFIED`, `ETB UNSATISFIED`, or a separately
frozen harness-invalid classification if needed.

**22.4** No ETB execution oracle is created now, and the prerequisite is **not** claimed to be
satisfied.

## 23. Sequencing to the Mode-B SIC oracle

**23.1 Frozen sequencing:**

```
ETB definition accepted
→ separate ETB execution/oracle design
→ separate authorization
→ ETB execution
→ independent ETB result review
→ ONLY IF ETB SATISFIED: Mode-B SIC oracle construction may resume
```

**23.2 No direct jump** from this definition to Mode-B execution is permitted.

## 24. ETB vs configuration change vs listening alone

**24.1** A future configuration change **alone** must never be treated as ETB SATISFIED.

**24.2** Likewise, OpenCode **merely listening on a port** is **insufficient**: the listener must
be bound to the authorized endpoint **and** to the accepted target identity chain (§13).

**24.3** Both endpoint authority and target identity must be bound; neither alone suffices.

## 25. Five distinct concepts (self-consistency clause)

**25.1** This definition keeps the following **five concepts distinct** and does not collapse
them:

1. **endpoint selection** — the external, owner-authorized choice of the exact tuple (§6);
2. **endpoint configuration** — writing that tuple into the authoritative source (§5, §17);
3. **target launch/existence** — whether a target process exists, and under Mode L how it came to
   exist (§11, §12);
4. **target binding** — the deterministic endpoint→process identity chain and its evidence
   (§13–§16);
5. **later Mode-B HTTP execution** — the future frozen read-only request set, which ETB does not
   define, authorize or perform (§14.2).

**25.2 Mode exclusivity.**  Mode L and Mode P are **exclusive** alternatives (§9.1, §10); the
definition does not simultaneously require a DevRelay-controlled launch and permit a pre-existing
target within one attempt.

## 26. Unestablished platform facts carried forward

**26.1 Register (explicitly NOT invented, NOT solved by this definition).**

| # | Unestablished fact | How this definition handles it |
| --- | --- | --- |
| U1 | exact OpenCode 1.18.11 launch CLI syntax, and whether the installed CLI can explicitly bind a caller-chosen address/port | Mode L is conditional on a later separately reviewed **launch-capability determination** (§11.3); no flags are guessed |
| U2 | the exact read-only OS primitive that maps a frozen local endpoint to its owning PID, and demonstration of its semantics on this platform | required **semantic properties** frozen (§12.3, §12.4); concrete primitive is a future ETB-oracle requirement; no command/API is asserted as authoritative |
| U3 | availability and exact semantics of process creation/start identity on this platform | required as a property with explicit fail-closed classification if unavailable (§15); the accepted prior-art assertion is carried forward but has never been exercised (§4.2) |
| U4 | the concrete deterministic port policy if class B is ever used | class B admissible only after separate review/acceptance (§8.2); class A available today |
| U5 | which mode a future attempt will precommit | deliberately undecided (§9.3); must be precommitted before operational action (§10.1) |

**26.2 Rule.**  A sound definition may specify the required semantic property while leaving the
future oracle to establish the concrete mechanism; no platform fact may be invented to close
these gaps.

## 27. Privacy, safety and activity boundary

**27.1** ETB requires **no** user prompt, message, response or session content.

**27.2** ETB requires **no** provider/model call, **no** fake provider, **no** external internet,
and **no** session mutation.

**27.3** **No OpenCode semantic API call is required** merely to establish the binding
prerequisite, unless a later independently reviewed ETB oracle proves such a read-only call
necessary.  OS/process/config identity evidence is preferred.

**27.4** ETB defines no HTTP operation of its own, and the future ETB execution budget remains
`0` provider/model calls, `0` prompt submissions, `0` session mutations, `0` external network.

**27.5** `PROJECT_MEMORY.md` is **not** repository evidence and is **never** endpoint authority; it
is ignored/untracked agent-memory bookkeeping only, and must be distinguished from tracked
repository modifications.

## 28. Status surfaces, non-claims and protected artifacts

**28.1** While this artifact is a definition candidate, the recorded status is: ETB definition
candidate exists; **ETB NOT EXECUTED**; no endpoint established; no configuration change; Mode-B
SIC oracle remains **not freezable**; **no operational authorization**.  ETB is **not** marked
accepted.

**28.2 Non-claims.**  This definition does not establish an endpoint; does not authorize a
configuration change; does not authorize launching OpenCode; does not bind a listener; does not
prove P6, G0.5 or SIC semantics; does not enable Mode-B execution, Case-C implementation or
adoption; and does not change any status in §3.

**28.3 Protected artifacts.**  The accepted SIC definition, the Mode-A frozen oracle, the Mode-A
result, the §25.1 substantive block and the G0.4 oracle/proof are **not** modified by this
definition round and retain their recorded hashes.

## 29. Open items for the future (definition-level only)

**29.1** Independent review of this definition candidate.
**29.2** If Mode L is to remain available: the separately reviewed launch-capability determination
(U1).
**29.3** The ETB execution oracle design, including the concrete endpoint-scoped owner-verification
primitive and its semantics (U2), the process-creation-identity check (U3), the port-policy
precommit (§8) and the mode precommit (§10).
**29.4** The external authorization of the exact endpoint tuple (§6) — which is what ultimately
unblocks the currently recorded Mode-B endpoint gate.

**End of definition candidate.**
