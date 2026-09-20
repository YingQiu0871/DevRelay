# DevRelay v0.3-E — G0.5-PRE / SIC — ETB execution / configuration authorization

> **ETB EXECUTION / CONFIGURATION AUTHORIZATION**
> **CANDIDATE RECORD**
> **NOT ACCEPTED**
> **NOT EFFECTIVE**
> **DOES NOT MODIFY CONFIGURATION**
> **DOES NOT EXECUTE ETB**
> **DOES NOT START OPENCODE**
> **DOES NOT AUTHORIZE HTTP**
> **ONE ETB ATTEMPT ONLY IF LATER INDEPENDENTLY ACCEPTED**

Status: **ETB EXECUTION / CONFIGURATION AUTHORIZATION = CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT EXECUTED**

Baseline: `d058b38b5405743db80d10fab6767eb18ed17ca2` (branch `v0.3-e-recovery-reconciliation`).

This artifact is a **candidate authorization record only**.  It authorizes nothing today: it modifies no
configuration, executes no ETB attempt, starts no OpenCode, issues no HTTP, publishes no evidence and
creates no result.  It becomes effective **only** if a separate independent authorization review accepts
it.  It is self-contained for a future executor and for a future independent reviewer.

Accepted frozen oracle provenance (immutable; bound permanently by this authorization):

| Item | Value |
| --- | --- |
| `oracle_commit` | `1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc` |
| `oracle_artifact` | `docs/v0.3/V03E_G0_5_PRE_ETB_EXECUTION_ORACLE.md` |
| `oracle_sha256` | `01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921` |

Current authoritative status at the time of this record: `ETB = DEFINITION ACCEPTED / NOT EXECUTED`;
`ETB EXECUTION / ORACLE = ACCEPTED / FROZEN / NOT EXECUTED / EXECUTION NOT AUTHORIZED`.

## 1. Purpose and scope

**1.1** This candidate authorization, **only after independent authorization review and acceptance**,
may authorize exactly two things, in this order:

* **A. one exact configuration establishment** — write `http://127.0.0.1:4096` to
  `<root>/.devrelay/config.yaml` → `opencode.base_url`; and then
* **B. exactly ONE ETB execution attempt** under the already accepted frozen ETB oracle.

**1.2** This round performs **neither A nor B**, and does not authorize them.

## 2. Authorized configuration mutation (exact)

**2.1** The only authorized mutation is:

| Item | Value |
| --- | --- |
| file | `<root>/.devrelay/config.yaml` |
| field | `opencode.base_url` |
| before | `""` (current value) |
| after | **`http://127.0.0.1:4096`** |

**2.2** No trailing slash; no alternate URI; **no other configuration field change**.

**2.3** The future execution round must record the **exact before/after configuration diff**, limited to
`opencode.base_url`.

## 3. Owner inputs (preserved, not reinterpreted)

| Input | Frozen value |
| --- | --- |
| mode | **MODE P — PRE-EXISTING TARGET** |
| endpoint policy | **CLASS A — OWNER-SUPPLIED FIXED ENDPOINT** |
| scheme | `http` |
| address family | **IPv4** |
| host | `127.0.0.1` |
| port | `4096` |
| base URI | `http://127.0.0.1:4096` |
| fallback | **NONE** |

**3.1** No reinterpretation, no substitute, no normalization into an alternate owner decision.

## 4. Pre-existing target semantics

**4.1** Mode P means the ETB attempt verifies a **pre-existing** target.  This authorization does **NOT**
authorize: starting OpenCode; restarting OpenCode; launching another OpenCode instance; creating a
listener; rebinding another port; or switching to Mode L.

**4.2** If the exact pre-existing target is not present, or cannot satisfy the frozen oracle, the ETB
attempt must fail **according to the oracle** — **no recovery by target creation**.

## 5. No-fallback policy

**5.1** Fallback remains **NONE**.  Forbidden: IPv4 → IPv6; `127.0.0.1` → `localhost`; `127.0.0.1` →
`::1`; `4096` → any other port; `4096` → first-free port; `4096` → ephemeral port; Mode P → Mode L;
alternate OpenCode executable; alternate OpenCode installation; PATH-selected alternate target; endpoint
discovery from logs; endpoint discovery from listeners; endpoint discovery from processes; retry against
another endpoint.

## 6. Configuration-mutation limit

**6.1** If this authorization later becomes accepted, the execution round may change **only**
`.devrelay/config.yaml` → `opencode.base_url`, from `""` to exactly `http://127.0.0.1:4096`.

**6.2** No other `.devrelay` field; no source file; no test; no dependency; no version; no runtime
implementation.

## 7. Configuration failure rule

**7.1** The future authorized execution round must **NOT** improvise.  If the exact configuration mutation
cannot be performed deterministically: **do NOT execute ETB**; return an authorization/execution
**control failure** for independent review; do **not** choose a substitute endpoint; do **not** alter
another field; do **not** retry using another config mechanism.

## 8. Oracle immutability

**8.1** This authorization binds **permanently** to `oracle_commit =
1c6c7cda468fc4def2cafd85a9ff5da0c87d00bc` and `oracle_sha256 =
01675fa7e39f15451900cc306e975e9cde72d69eb01b26322bf21b8a5e54b921`.

**8.2** The future execution **MUST NOT** use `d058b38b5405743db80d10fab6767eb18ed17ca2`, the
authorization commit, the execution-time HEAD, or any later commit as `oracle_commit`.  **No oracle
modification is authorized.**

## 9. Attempt budget

**9.1** Authorized ETB semantic attempts = **1**, exactly one.

**9.2** Once operational ETB execution begins under the accepted authorization, the single attempt is
**consumed**.  No rerun.  No "verification rerun".  No second attempt after `ETB_SATISFIED`,
`ETB_UNSATISFIED` or `HARNESS_INVALID`.

**9.3** Any future additional attempt requires **new explicit authorization + independent review**.

## 10. Attempt-start boundary

**10.1** The ETB attempt is considered **STARTED**, and the one-attempt budget **consumed**, immediately
**before the first oracle operational probe after configuration establishment**.

**10.2** The **first operational probe** is the first frozen oracle action that inspects the configured
target/environment — **including the exact listener query**.

**10.3** **Pure configuration establishment itself does NOT consume** the ETB attempt.  **Static preflight
verification** of (i) the accepted oracle commit/hash, (ii) the authorization identity, and (iii) the
configuration file pre-mutation state **does NOT consume** the ETB attempt.

**10.4** Once the first live oracle probe begins, the attempt count becomes **1 of 1**.

## 11. Configuration-establishment evidence (recorded before ETB begins)

authorization identity; `oracle_commit`; `oracle_sha256`; configuration path; pre-mutation `base_url`
value; authorized target `base_url`; post-mutation **production-resolved** `base_url`; and the exact diff
limited to `opencode.base_url`.  No prompt/session/message/provider content.

## 12. Execution outputs

**12.1** The future authorized ETB attempt must use **only** the evidence/result paths already frozen by
the accepted oracle.  No new alternative evidence path, no alternative result path, no alternate
manifest, no executor-selected filenames.

## 13. ETB result boundary

**13.1** The future one-shot execution may produce only the oracle-defined control state:
`ETB_SATISFIED`, `ETB_UNSATISFIED`, or `HARNESS_INVALID / NO ETB SEMANTIC RESULT`.

**13.2** No result is authoritative until **separate independent ETB-result review**.

## 14. `ETB_SATISFIED` non-claims

**14.1** Even a future `ETB_SATISFIED` result does **NOT** itself establish: SIC semantics; P6; G0.5;
session incarnation; turn provenance; message provenance; pending-handle semantics; Mode-B PASS; Case-C
authorization; or `adopt_completed_turn`.

**14.2** It only allows **independent ETB result review** and, only after `ETB_SATISFIED` is independently
accepted, **Mode-B SIC oracle construction may resume**.

## 15. `ETB_UNSATISFIED` non-claims

**15.1** `ETB_UNSATISFIED` is only a prerequisite/control result.  It is **NOT** SIC FAIL, **NOT** P6
FAIL, **NOT** G0.5 FAIL, and **NOT** a claim that OpenCode cannot support Mode B.  Mode-B construction
remains blocked.

## 16. `HARNESS_INVALID` semantics

**16.1** `HARNESS_INVALID` means **NO ETB SEMANTIC RESULT EXISTS**.  No retry.  No repair-and-continue
within the same authorization.  The one authorized attempt is consumed once execution has started; any
new attempt requires **new authorization**.

## 17. HTTP boundary

**17.1** The ETB execution performs **NO HTTP**, **no `/doc`**, **no `/session`** and **no provider/model
request**.  This authorization does **NOT** authorize any Mode-B HTTP activity.

## 18. OpenCode start boundary

**18.1** This authorization explicitly does **NOT** authorize `opencode serve`, OpenCode launch, OpenCode
restart, process replacement or listener creation.  Mode P requires a **pre-existing** target.

## 19. Future execution order (frozen; only if this authorization is later accepted)

1. verify accepted authorization identity;
2. verify accepted oracle provenance (`oracle_commit`/`oracle_sha256` per §8);
3. verify current config precondition (`opencode.base_url == ""`);
4. write exactly `opencode.base_url = http://127.0.0.1:4096`;
5. read through the accepted production config reader and verify the exact resolved value;
6. record configuration-establishment evidence (§11);
7. begin exactly one ETB attempt;
8. consume attempt count = **1 of 1** immediately before the first live oracle probe (§10);
9. execute the frozen oracle exactly;
10. publish the oracle-defined candidate evidence/result;
11. **STOP**;
12. independent ETB result review.

**19.1** No Mode-B construction in the same round.

## 20. Configuration-after-attempt policy

**20.1** **No automatic configuration rollback is authorized.**  The authorization leaves
`opencode.base_url = http://127.0.0.1:4096` after the attempt unless a **future separately authorized**
action changes it.

**20.2** No rollback-on-failure; no executor discretion.  This is explicit so that execution does not
choose whether to restore `""`.

## 21. Output-precondition policy

**21.1** The accepted oracle's output-preexistence rule is preserved: before execution, **all**
oracle-frozen temp/final evidence paths must satisfy the oracle's required non-existence precondition.
If they do not, follow the frozen `HARNESS_INVALID` / no-result semantics.  Do **not** delete old outputs;
do **not** overwrite.

## 22. Current round status (this record)

```
ETB EXECUTION / CONFIGURATION AUTHORIZATION = CANDIDATE / NOT ACCEPTED / NOT EFFECTIVE / NOT EXECUTED
ETB EXECUTION / ORACLE                        = ACCEPTED / FROZEN / NOT EXECUTED
ETB                                           = DEFINITION ACCEPTED / NOT EXECUTED
```

**22.1** No configuration mutation now; no ETB execution now.

## 23. Mode-B preservation

**23.1** Mode-B remains `NOT RUN / NO ORACLE / ORACLE NOT FREEZABLE / CONCRETE ENDPOINT NOT ESTABLISHED /
PRE-ORACLE CONFIGURATION / TARGET-BINDING PREREQUISITE BLOCKER`.  **This authorization candidate does not
unblock Mode-B.**

## 24. G0.5 / P6 preservation

**24.1** `G0.5 / P6 = NOT RUN / DEFINITION ACCEPTED / ORACLE NOT FREEZABLE / LOCAL REACHABILITY GAP`;
`P6 = UNPROVEN / UNSATISFIED`; G0.5 **NOT CLOSED**.

## 25. Implementation / adoption preservation

**25.1** Case-C implementation `NOT AUTHORIZED`; v0.3-E implementation `NOT AUTHORIZED`; `G1 = NOT RUN`;
`G2 = NOT RUN`; `adopt_completed_turn` **DISABLED**.

## 26. Activity counters and non-claims (this recording round)

**26.1** This round performed: web/network `0`; endpoint queries `0`; `Get-NetTCPConnection` `0`; live
`Get-CimInstance` `0`; port/listener/process enumeration `0`; config mutation `0`; OpenCode
start/restart `0`; HTTP `0`; `/doc` `0`; `/session` `0`; `Add-Type` `0`; P/Invoke `0`; evidence
publication `0`; ETB execution `0`; SIC `0`; Mode-B oracle work `0`; provider/model `0`; G0.5 `0`;
G1/G2 `0`; runtime/test/dependency/version changes `0`.

**26.2 Non-claims.**  This candidate authorization does not grant authorization, does not modify
configuration, does not configure an endpoint, does not assert that a listener exists or that OpenCode is
running, does not execute ETB, does not perform HTTP, does not start OpenCode, does not publish evidence,
and produces no `ETB_SATISFIED` / `ETB_UNSATISFIED` / `HARNESS_INVALID` result.  It is a **candidate**
until a separate independent authorization review accepts it.

**End of ETB execution / configuration authorization candidate record.**
