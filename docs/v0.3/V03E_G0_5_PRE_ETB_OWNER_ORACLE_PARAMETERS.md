# DevRelay v0.3-E — G0.5-PRE / SIC — ETB owner / oracle-parameter decision (Mode + endpoint freeze)

> **ETB OWNER / ORACLE-PARAMETER DECISION**
> **CANDIDATE RECORD**
> **HUMAN OWNER DECISION**
> **NOT YET INDEPENDENTLY ACCEPTED**
> **DOES NOT ESTABLISH ENDPOINT**
> **DOES NOT MODIFY CONFIGURATION**
> **DOES NOT START OPENCODE**
> **DOES NOT CREATE ETB ORACLE**
> **DOES NOT AUTHORIZE ETB EXECUTION**

Status: **OWNER / ORACLE-PARAMETER DECISION = CANDIDATE RECORD / OWNER INPUT FROZEN / INDEPENDENT FIDELITY REVIEW PENDING**

Baseline: `16172cbc9bf88d3948fd9ea54437e6de402bfaf2` (branch `v0.3-e-recovery-reconciliation`).

This artifact is a **record only**.  It freezes the human owner's decision on the mode (**U5**) and the
endpoint parameters (**U4**) as **frozen external input** for a future ETB execution-oracle design.  It
does **not** configure an endpoint, does **not** prove any listener exists, does **not** prove OpenCode
owns any listener, does **not** execute ETB, does **not** create `ETB SATISFIED` and does **not**
authorize Mode-B work.  The human decision itself is authoritative input; **this repository recording
still requires independent fidelity review**.

Anchors (committed Git blobs):

| Anchor | Identity |
| --- | --- |
| accepted ETB definition | `docs/v0.3/V03E_G0_5_PRE_MODE_B_ENDPOINT_BINDING.md`, blob `99cc6dcee4ab1a3f0589c3e7d11308d089601ba07d16cc2d37a9fc32c777b3a0` |
| accepted Round-2 U2/U3 artifact | `docs/v0.3/V03E_G0_5_PRE_ETB_U2_U3_AUTHORITY_RESOLUTION.md`, blob `49b22a88a593ce9ce59e7da6ae5221d8300d4963cca5b9fdc2dc8c2b47a91453` |
| accepted prior U1/U2/U3 capability artifact | `docs/v0.3/V03E_G0_5_PRE_ETB_CAPABILITY_RESOLUTION.md`, blob `59e8ef575fa3ab854f65fee5e25621c51f74c8b76615d7d4d9fb1e071b4049ac` |
| accepted SIC definition | `docs/v0.3/V03E_G0_5_PRE_SESSION_INCARNATION_FINDING.md`, blob `5463ac19ddc532f2a5f4f73c1076284f4c5f75b94338a5720a189b955e23ad11` |
| Mode-A oracle / result | `31d7ac5020ba6a7e3a4eb700df0feedc8f480d67a89f7124091e87df9ff7dc78` / `ce6c503d3bd62fa09c34d52bbd570e1a98dab403d1164b2e740fe6c476ecadc6` |
| §25.1 protected block | `d3244ee0d24f5d740b34dac358378870d4d8238b0755787cffb7313d01044ee0` |
| G0.4 oracle | `b0c34fa19c3e639b5637d74d49e1c9c357b7db914ee1becf70229f3e5ed4bfa4` |

## 1. Owner decision provenance (acceptance-critical)

**1.1 The decision is the HUMAN OWNER's, not the executor's.**  The human owner explicitly confirmed:

* **U5 = MODE P — PRE-EXISTING TARGET** (selected by the owner);
* **U4 = CLASS A — OWNER-SUPPLIED FIXED ENDPOINT** (supplied by the owner);
* the endpoint tuple **scheme `http`, address family IPv4, numeric loopback address `127.0.0.1`, port
  `4096`, base URI `http://127.0.0.1:4096`**;
* **fallback policy = NONE**.

**1.2 The executor did NOT choose** Mode P, IPv4, `127.0.0.1`, `4096`, or the base URI, and **must not**
reinterpret, replace, extend or "improve" the decision.  This artifact records the owner's values
verbatim; it does not derive them, and it does not treat the historical documentation example
`127.0.0.1:4096` as the source of authority — the source of authority is the owner's explicit decision.

**1.3 Repository fidelity.**  Because the decision arrived as owner input rather than as a repository
artifact, the *recording* is a **candidate record**: the human decision is authoritative, while the
repository record awaits **independent fidelity review** (see §10).

## 2. U5 freeze — mode

**2.1 Frozen:**

```
U5 = MODE P SELECTED BY OWNER
MODE L = NOT SELECTED
```

**2.2 This does NOT mean** Mode L is invalid, Mode L is impossible, or U1 is resolved.  Preserved
unchanged: **`U1 = U1_NOT_ESTABLISHED`** and **`MODE L = MODE_L_MECHANISM_NOT_YET_FREEZABLE`**.

**2.3 No future automatic fallback** from Mode P to Mode L exists.  A mode change would require a new
explicit owner decision and its own authorization.

## 3. U4 freeze — endpoint policy class

**3.1 Frozen:**

```
U4 PORT / ENDPOINT POLICY = CLASS A — OWNER-SUPPLIED FIXED ENDPOINT
```

**3.2 Forbidden:** using **CLASS B**; creating a deterministic allocation policy; searching for a free
port; substituting another port if `4096` is unavailable; instantiating any port policy other than the
owner-supplied fixed endpoint.

## 4. Exact endpoint tuple (indivisible)

| Field | Frozen value |
| --- | --- |
| scheme | `http` |
| address family | IPv4 |
| host | `127.0.0.1` (numeric loopback address) |
| port | `4096` |
| base URI | `http://127.0.0.1:4096` |

**4.1 The tuple is indivisible for all later ETB work.**  No field may be changed independently by the
executor, and no field may be re-derived, re-negotiated or "normalized" into a different value.

## 5. No-fallback policy

**5.1 Frozen as forbidden:**

* IPv4 → IPv6 fallback;
* `127.0.0.1` → `localhost` substitution;
* `127.0.0.1` → `::1` substitution;
* `4096` → another port;
* `4096` → first-free port;
* `4096` → ephemeral port;
* Mode P → Mode L fallback;
* alternate OpenCode binary;
* alternate OpenCode installation;
* alternate endpoint discovered from logs;
* alternate endpoint discovered from a listener scan;
* alternate endpoint discovered from a process scan;
* retry on another endpoint after failure.

**5.2 Consequence.**  If the frozen Mode-P endpoint cannot satisfy later ETB conditions, the authorized
ETB attempt **must fail closed** (§8).  No alternate endpoint, port, address family or mode may be
attempted.

## 6. Pre-existing target semantics

**6.1** The target must be **PRE-EXISTING** for the later ETB execution attempt.  This decision does
**not** start it, does **not** create it, and does **not** assert that it currently exists.

**6.2** A later ETB execution oracle must verify **the exact frozen endpoint only**; **no endpoint
discovery is permitted**.  The accepted ETB boundary is preserved: this is endpoint-scoped owner
verification, never endpoint discovery.

## 7. Mode-P mechanism status

**7.1** **`MODE_P_MECHANISM_FREEZABLE`** remains the accepted capability state (accepted Round-2
finding: `U2_ESTABLISHED` ∧ `U3_ESTABLISHED` with no contradiction to the accepted ETB definition).

**7.2** This owner decision advances **only** mode selection and endpoint parameter selection.  It does
**not** mean: ETB mechanism implementation frozen; ETB oracle exists; ETB execution authorized; or
`ETB SATISFIED`.

## 8. Target binary identity (preserved)

**8.1** OpenCode / `opencode-ai` = **1.18.11**; expected executable
`C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe`; expected SHA-256
`578d7eb3fff2c807fc0dedaab5e5d9177713a9560fa4304db6a0161111e9cc35`.

**8.2** No alternate binary, no alternate installation, no retargeting.

## 9. Future-oracle frozen inputs vs still-open rules

**9.1 FROZEN EXTERNAL INPUTS** (the future ETB execution-oracle design must treat these as given and
must **not** choose or derive them):

```
selected mode    = MODE P
endpoint policy  = CLASS A OWNER-SUPPLIED FIXED ENDPOINT
scheme           = http
address family   = IPv4
host             = 127.0.0.1
port             = 4096
base URI         = http://127.0.0.1:4096
fallback         = NONE
```

**9.2 STILL NOT FROZEN** (explicitly unresolved ETB execution-oracle design items; none of them may be
solved in this owner-decision round):

* exact `Get-NetTCPConnection` expression;
* exact `Count == 1` enforcement and failure handling;
* exact `Win32_Process` PID query expression;
* pre-request target snapshot exact field set;
* post-request target snapshot exact field set;
* pre/post equality rules;
* `CreationDate` precision residual handling;
* `CreateFileW` `dwShareMode`;
* `ExecutablePath` access-failure handling;
* `SeDebugPrivilege` failure handling;
* `GetFinalPathNameByHandleW` access-failure handling;
* `\\?\` prefix handling;
* case comparison rule;
* slash normalization rule;
* drive-letter normalization rule;
* target-executable canonicalization procedure details;
* exact evidence serialization;
* the `HARNESS_INVALID` vs `ETB UNSATISFIED` boundary, if needed.

## 10. Status model for this record

```
OWNER / ORACLE-PARAMETER DECISION = CANDIDATE / NOT YET ACCEPTED
  U5       = MODE P SELECTED BY OWNER
  U4       = CLASS A OWNER-SUPPLIED FIXED ENDPOINT
  endpoint = http://127.0.0.1:4096
  fallback = NONE
```

**10.1** The owner-decision repository record must **not** be marked accepted until independent review.
The human decision itself is authoritative input; the repository recording still requires independent
**fidelity review** (that it states the owner's decision exactly, without reinterpretation).

## 11. Endpoint authority vs configuration (critical distinction)

**11.1 After this decision round:**

* **owner-authorized endpoint** = `http://127.0.0.1:4096` (frozen input, §9.1);
* **currently configured endpoint** = **none** — `.devrelay/config.yaml` → `opencode.base_url` must
  remain `""`.

**11.2 Therefore:** the **owner parameter decision exists**, but the **endpoint is NOT yet established
in configuration**.  This round does **not** write `base_url`.

**11.3 Configuration-establishment boundary.**  A **future, separately authorized** action *may* set
`.devrelay/config.yaml` → `opencode.base_url = http://127.0.0.1:4096`, because the tuple is now
owner-authorized and Mode P is now owner-selected — **but this round does not authorize that mutation**,
and the mutation must occur only under a later explicit authorization consistent with the accepted ETB
sequence (§12).

## 12. ETB sequencing after the owner decision

```
OWNER / ORACLE-PARAMETER DECISION
  → independently reviewed and accepted
THEN:
ETB EXECUTION-ORACLE DESIGN
  → independent oracle review
  → separate execution/configuration authorization
  → configuration establishment as authorized
  → ETB execution
  → independent ETB result review
  → ONLY IF ETB SATISFIED: Mode-B SIC oracle construction may resume
```

**12.1** No stage may be skipped.  In particular, this decision round does not itself authorize the
configuration mutation, the ETB oracle design, or ETB execution.

## 13. Fail-closed consequence (future semantics only; not executed here)

**13.1** If a later ETB execution finds: no listener at `127.0.0.1:4096`; or more than one matching
listener; or no owning PID; or an ambiguous owner; or the wrong executable; or the wrong hash; or the
wrong OpenCode version; or a process-instance mismatch; or required identity evidence unavailable —
then **ETB must NOT be considered SATISFIED**, and **no fallback endpoint or mode may be attempted**.

**13.2** None of these checks is performed in this round.

## 14. Preserved state

**14.1 ETB.**  `ETB = DEFINITION ACCEPTED / NOT EXECUTED`; `ETB EXECUTION / ORACLE = NOT YET DEFINED /
NOT AUTHORIZED`.  No `ETB SATISFIED`, `ETB UNSATISFIED` or `ETB EXECUTED` is created.

**14.2 Capability state (unchanged).**  `U1 = U1_NOT_ESTABLISHED`; `U2 = U2_ESTABLISHED`; `U3 =
U3_ESTABLISHED`; `MODE L = MODE_L_MECHANISM_NOT_YET_FREEZABLE`; `MODE P =
MODE_P_MECHANISM_FREEZABLE`.  U2/U3 findings are **not** reopened, and the U2/U3 mechanism is **not**
executed in this round.

**14.3 Mode-B.**  `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED /
PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER` — unchanged; Mode-B oracle construction
has not resumed.

**14.4 G0.5 / P6.**  `G0.5 / P6 = NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL
REACHABILITY GAP`; `P6 = UNPROVEN / UNSATISFIED`; G0.5 **NOT CLOSED**.

**14.5 Implementation / adoption.**  Case-C implementation `NOT AUTHORIZED`; v0.3-E implementation `NOT
AUTHORIZED`; `G1 = NOT RUN`; `G2 = NOT RUN`; `adopt_completed_turn` **DISABLED**.

## 15. Non-claims

This record does **not**: select a mode on the executor's behalf (the owner did); establish an endpoint;
modify configuration; start or restart OpenCode; assert that a listener exists at `127.0.0.1:4096`; assert
that OpenCode owns any listener; create or design an ETB execution oracle; authorize ETB execution;
create `ETB SATISFIED`; authorize Mode-B SIC oracle construction or execution; authorize Case-C
implementation; prove P6 or G0.5; or enable `adopt_completed_turn`.

## 16. Activity counters

Web retrievals 0; schema probes 0; live TCP queries 0; live process queries 0; port/listener/process
enumeration 0; endpoint establishment 0; endpoint probing 0; configuration mutation 0; OpenCode
start/restart 0; listener work 0; HTTP 0; `/doc` 0; `/session` 0; ETB oracle design 0; ETB execution 0;
SIC attempts 0; Mode-B oracle work 0; provider/model calls 0; network 0; G0.5 0; G1/G2 0; runtime, test,
dependency and version changes 0.

**End of owner / oracle-parameter decision candidate record.**
