# DevRelay v0.3-E — corrected clean G0.3 / P5 re-run proof (precommitted corrected oracle)

Status: **G0.3 / P5 = PASS** — authoritative and independently approved (**APPROVE V0.3-E G0.3 / P5 TRANSPORT PROOF** with **P0 = 0, P1 = 0, P2 = 0**; this PASS comes from the independent review of the corrected clean proof, never from executor self-approval).

* Platform proof gate: **PARTIALLY EXECUTED / NOT COMPLETE** — `G0.1 / P7 = PASS`,
  `G0.2 = PASS`, `G0.3 / P5 = PASS`; `G0.4`, `G0.5`, `G1`, `G2` are **NOT RUN**; there is no
  "platform proof gate passed" and no "platform proof gate complete" status.
* Implementation: `G0.1/P7`, `G0.2` and `G0.3/P5` are authoritative PASS and
  **mandatory-core implementation remains NOT AUTHORIZED** pending a separate
  authorization; this proof approves no implementation.
* `adopt_completed_turn`: **DISABLED** (G0.3/P5 does not prove P1, P2, P3, P4, P6, P8, P9,
  remote completion, delivery truth for uncertain submissions or adoption eligibility;
  G1/G2 unrun).

## 0. Authoritative status, independent approval and chronology

**Independent approval (recorded by the later bookkeeping round, from the already-issued
review):** `APPROVE V0.3-E G0.3 / P5 TRANSPORT PROOF`, final severities **P0 = 0, P1 = 0,
P2 = 0**.

The independent reviewer verified:

* the corrected oracle genuinely predates the corrected execution;
* the corrected oracle SHA was independently recomputed;
* the corrected oracle was immutable after execution;
* the old failed oracle remained immutable;
* the original `c889636` round remains **FAILED** and historical;
* the installed stack remained httpx 0.28.1 / httpcore 1.0.9 / h11 0.16.0;
* the accepted classifier inventory was unchanged;
* the class-wide source inspection independently supported the P5 result;
* A/B/C/E/F are class-wide pre-submission for the accepted current configuration;
* `proxy_error` is **UNREACHABLE / NON-AUTHORITATIVE** for the current accepted production
  configuration;
* the mid-send h11 escape does **not** enter the safe `local_protocol_error` bucket;
* the corrected case-J precommitment exactly matched the corrected observation;
* uncertain / post-send classes remain fail-closed;
* no unsafe `retry_safe` result exists;
* P5 remains informational evidence only;
* the original TYPE-1 failure history was preserved;
* P0/P1/P2 are all zero.

**Chronology (not flattened):** original G0.3 oracle `b9c4704` → original execution
`c889636` → original case-J mismatch → original CANDIDATE FAIL → independent TYPE-1
proof-plan failure review → corrected clean rerun separately authorized → corrected pre-run
oracle `e328ec5` → corrected A–N execution → `3143742` CLEAN CANDIDATE PASS → independent
corrected-proof **APPROVE** → **authoritative `G0.3 / P5 = PASS`** → the bookkeeping commit
that records it.

**Authoritative claim boundary (bounded to the independently approved claim):** for the
accepted installed stack and current accepted production configuration — reachable
safe-labelled P5 buckets A/B/C/E/F are class-wide pre-submission; `proxy_error` is
unreachable / non-authoritative; uncertain/post-send transport classes remain fail-closed;
the installed HTTP/1.1 request-send `WriteError` path surfaces as `remote_protocol_error`
and remains submission-uncertain; no false-safe non-delivery classification was
established; and `retry_safe` carries **no** v0.3-E recovery execution authority.  G0.3/P5
does **not** prove remote provider receipt/non-receipt beyond the proven pre-send
boundaries, safe retry, retry-protocol correctness, refund safety, automatic recovery,
adoption, P1/P2/P3/P4/P6/P8/P9, G0.4–G2, future httpx/httpcore/h11 versions, future proxy
configurations, or future v0.3-E implementation correctness.

This document records the separately authorized **corrected clean G0.3 / P5 re-run**
(TYPE-1 proof-plan remediation only) executed under the new immutable oracle
`docs/v0.3/V03E_G0_3_RERUN_ORACLE.md`, precommitted in commit
`e328ec5b45b97021007baf22aa5b5a49503fc02d` **before any corrected case was executed**.
The original failed round stays historical and is not flattened.

## 1. Identity

| Item | Value |
| --- | --- |
| Starting HEAD | `c889636420f59044cda5cd62fdb61db991f876c4` |
| Corrected pre-run oracle commit | `e328ec5b45b97021007baf22aa5b5a49503fc02d` (`docs(v03e): freeze corrected G0.3 transport oracle`), parent `c889636420f59044cda5cd62fdb61db991f876c4` |
| Corrected oracle SHA-256 | `9e4c7de67b9bba230cf0e5b50ba459e99edf05b2a720789b84c673522dbe862e` (`docs/v0.3/V03E_G0_3_RERUN_ORACLE.md`; verified unchanged at execution time) |
| Original (failed) oracle | `docs/v0.3/V03E_G0_3_TRANSPORT_ORACLE.md`, SHA-256 `6ca090b5d7a742be22046e0f67c8bf3980f81faea67f9e67d4b4419fbbb868e9` — **unmodified** |
| Original failed execution record | `docs/v0.3/V03E_G0_3_TRANSPORT_PROOF.md` (candidate FAIL at `c889636`) — preserved, now carrying the TYPE-1 pointer |
| Branch | `v0.3-e-recovery-reconciliation` |
| Frozen semantic design candidate | `9f4a01804b9affe8938a272553df345b5a60aeed` |
| Installed stack (re-verified before the freeze and at execution) | **httpx 0.28.1**, **httpcore 1.0.9**, h11 0.16.0, Python 3.14.6 |
| Proof start / completion (UTC) | `2026-09-18T09:26:15Z` / `2026-09-18T09:26:16Z` |
| v0.3-E status | DESIGN FROZEN / NOT IMPLEMENTED / NOT ACCEPTED / UNRELEASED |
| Provider / model calls · real network requests · OpenCode processes | **0** · **0** · **0** |
| Runtime / test / dependency / version change | **none** (`git diff efa2ca3 -- src/devrelay tests pyproject.toml` and `git diff c889636 -- …` both empty) |

## 2. Independent TYPE-1 failure authority (recorded, history preserved)

The independent review of the original failed round issued **FAIL — V0.3-E G0.3 / P5
PROOF — TYPE 1 PROOF-PLAN FAILURE** with **P0 = 0, P1 = 0, P2 = 0**, determining:

* the original G0.3 candidate **correctly failed its immutable oracle**; the `c889636`
  result stays **FAILED** and is not rewritten as PASS;
* case J expected the accepted `error_type = write_error`, but the installed HTTP/1.1
  stack suppresses the request-send `httpcore.WriteError` and later surfaces
  `remote_protocol_error`;
* that surfaced outcome remains submission-uncertain / fail-closed;
* **no accepted safe/non-delivery classifier bucket was shown to be unsafe**;
* the failure is a **proof-plan / installed-stack reachability mismatch**, not a
  classifier-safety failure, and **no runtime remediation is required**.

Chronology (unchanged): `b9c4704` original pre-run oracle → `c889636` execution → case J
classification mismatch → G0.3 CANDIDATE FAIL → independent TYPE-1 review → corrected
clean rerun authorized (`e328ec5`) → this corrected execution.

## 3. Accepted classifier (re-derived and re-verified)

`transport.py::transport_failure`, verified by direct invocation at freeze time: the six
non-delivery buckets (`connect_timeout`, `pool_timeout`, `connect_error`, `proxy_error`,
`unsupported_protocol`, `local_protocol_error`) → `submission_uncertain=False`; the
uncertain buckets (`read_timeout`, `write_timeout`, `read_error`, `write_error`,
`remote_protocol_error`, `close_error`, anything unclassified) → `submission_uncertain=True`;
non-transport `httpx.HTTPError`/`OSError` → uncertain; `http_status` and success are not
transport failure classes.  **No classifier drift** between the reviewed state and this
run.

## 4. Class-wide installed-source evidence (A–F) — mechanical assertions

All thirteen precommitted static assertions passed (`static_source_evidence`), and the
recorded source SHAs are: `httpcore/_backends/sync.py` `6e113877…`,
`httpcore/_sync/connection.py` `f5ec4639…`, `httpcore/_sync/connection_pool.py`
`6be4fc2d…`, `httpcore/_sync/http11.py` `205a1b0f…`, `httpcore/_synchronization.py`
`cd28b5de…`, `httpx/_transports/default.py` `03379a45…`,
`src/devrelay/opencode/transport.py` `cb476363…`,
`src/devrelay/orchestration/service.py` `08b436c0…`.

* **A `connect_timeout` — CLASS-WIDE PRE-SEND**: `_backends/sync.py` `connect_tcp` maps
  `socket.timeout → ConnectTimeout`; a `start_tls` body maps it too;
  `_sync/connection.py::_connect` is the only stream-creation site, before any request
  byte can be written.
* **B `pool_timeout` — CLASS-WIDE PRE-SEND**: `_synchronization.py` thread `Event.wait`
  raises `PoolTimeout`; reached from `_sync/connection_pool.py`
  `PoolRequest.wait_for_connection(...)`, i.e. before the request is handed to a
  connection.
* **C `connect_error` — CLASS-WIDE PRE-SEND for the accepted configuration**:
  `connect_tcp`/`start_tls` map `OSError → ConnectError` in the connect/TLS phase.  The
  **stale httpcore comment** in `_sync/http11.py::_receive_event` ("treat it as a
  ConnectError") is **not** evidence — the code raises `RemoteProtocolError` there, which
  is what the executed cases observed.
* **D `proxy_error` — UNREACHABLE / NON-AUTHORITATIVE for the current accepted
  configuration**: DevRelay builds `httpx.Client(..., trust_env=False)` with **no** proxy
  argument and records that it has no reviewed proxy configuration mechanism; httpx only
  constructs `httpcore.HTTPProxy`/`SOCKSProxy` behind an explicit proxy branch.  The
  synthetic injected-proxy demonstration is recorded separately (§6) and must not be
  promoted to current-production positive evidence; future configurable proxy support
  requires a new review.
* **E `unsupported_protocol` — CLASS-WIDE PRE-SEND**: the pool rejects a missing or
  unsupported scheme before creating any connection.  Reachability caveat recorded: the
  accepted base URL is http/https, so this is a misconfiguration path, not a routine one.
* **F `local_protocol_error` — THE ACCEPTED BUCKET IS PRE-SEND-ONLY**: the accepted
  mapping `h11.LocalProtocolError → httpcore.LocalProtocolError` appears **exactly once**
  in `_sync/http11.py` and wraps only the pre-network `h11.Request(...)` construction in
  `_send_request_headers`; `_send_event` (`self._h11_state.send(event)` →
  `network_stream.write`) is **outside** that mapping, so a mid-send h11
  `LocalProtocolError` never becomes DevRelay's `local_protocol_error` /
  `submission_uncertain=False` / `retry_safe=True` bucket.

## 5. Unmapped mid-send h11 limitation (recorded; not ideal, not remediated here)

Precommitted static assertions confirmed: `h11.LocalProtocolError` is **not** a subclass
of `httpx.TransportError`, `httpx.HTTPError` or `OSError`, so a mid-send
`h11.LocalProtocolError` escapes `OpenCodeTransport.request`'s handlers and reaches the
higher internal error boundary (`orchestration/service.py` `except Exception` →
`internal_error`).  The independent review found this remains **fail-closed for authority
purposes** — no `retry_safe=true`, no P5 proven-non-delivery classification, the turn ends
blocked/internal-error — **but** the turn-record defaults may show
`submission_uncertain=False` and `submission_attempted=False`, which is an
**observability weakness**.  Recommended future behaviour: default previously
unclassified transport-layer escape paths to uncertainty.  **No runtime code was modified
by this rerun**, and P5 does **not** claim that anything on that path was not submitted.

## 6. Cases A–N: corrected precommitted expectation vs observed (one execution each)

| Case | Precommitted (corrected) | Observed exposed class | Observed verdict | Case |
| --- | --- | --- | --- | --- |
| A `connect_timeout` | PROVEN_NON_DELIVERY | `connect_timeout` | **PROVEN_NON_DELIVERY** | PASS |
| B `pool_timeout` | PROVEN_NON_DELIVERY | `pool_timeout` | **PROVEN_NON_DELIVERY** | PASS |
| C `connect_error` | PROVEN_NON_DELIVERY | `connect_error` | **PROVEN_NON_DELIVERY** | PASS |
| D `proxy_error` | UNREACHABLE_CURRENT_CONFIGURATION | `proxy_error` (synthetic injected proxy, recorded separately) | **UNREACHABLE_CURRENT_CONFIGURATION** | PASS |
| E `unsupported_protocol` | PROVEN_NON_DELIVERY (reachability caveat separately) | `unsupported_protocol` | **PROVEN_NON_DELIVERY** | PASS |
| F `local_protocol_error` | PROVEN_NON_DELIVERY (accepted bucket, class-wide) | `local_protocol_error` | **PROVEN_NON_DELIVERY** | PASS |
| G `read_timeout` | SUBMISSION_UNCERTAIN | `read_timeout` | **SUBMISSION_UNCERTAIN** | PASS |
| H `write_timeout` | SUBMISSION_UNCERTAIN | `write_timeout` | **SUBMISSION_UNCERTAIN** | PASS |
| I `read_error` | SUBMISSION_UNCERTAIN | `read_error` | **SUBMISSION_UNCERTAIN** | PASS |
| J body-write `httpcore.WriteError` | exposed `remote_protocol_error`, SUBMISSION_UNCERTAIN | **`remote_protocol_error`** | **SUBMISSION_UNCERTAIN** | PASS |
| K `remote_protocol_error` | SUBMISSION_UNCERTAIN | `remote_protocol_error` | **SUBMISSION_UNCERTAIN** | PASS |
| L `close_error` / safe-set miss | SUBMISSION_UNCERTAIN or UNCLASSIFIED_FAIL_CLOSED | `close_error` | **SUBMISSION_UNCERTAIN** | PASS |
| M HTTP rejection | NOT_A_NON_DELIVERY_CLASS | `http_status` (500) | **NOT_A_NON_DELIVERY_CLASS** | PASS |
| N success | NOT_A_NON_DELIVERY_CLASS | `""` (2xx JSON) | **NOT_A_NON_DELIVERY_CLASS** | PASS |

Send-boundary detail (transport-level submission request):

| Case | connections | POST headers sent | body marker observed | proxy CONNECT bytes | boundary failure |
| --- | --- | --- | --- | --- | --- |
| A | 1 | **no** | **no** | no | `connect_tcp → ConnectTimeout` |
| B | 1 (pool holder; no submission connection) | **no** | **no** | no | pool wait → `PoolTimeout` |
| C | 1 | **no** | **no** | no | `connect_tcp → ConnectError` |
| D | 1 (synthetic proxy) | **no** | **no** | **yes** | proxy tunnel rejection → `ProxyError` (phase demo only) |
| E | **0** | **no** | **no** | no | scheme rejected before connect |
| F | 1 | **no** | **no** | no | h11 request-event construction rejected (illegal configured header) |
| G | 1 | yes | yes | no | `read → ReadTimeout` |
| H | 1 | yes | yes | no | `write_body → WriteTimeout` |
| I | 1 | yes | yes | no | `read → ReadError` |
| J | 1 | yes | yes | no | `write_body → WriteError` (suppressed by httpcore → read-phase `RemoteProtocolError`) |
| K | 1 | yes | yes | no | protocol-violating peer bytes → `RemoteProtocolError` |
| L | 0 (constructed transport) | n/a | n/a | no | constructed `CloseError` at the accepted boundary |
| M | 1 | yes | yes | no | HTTP 500 |
| N | 1 | yes | yes | no | 2xx JSON |

## 7. DevRelay-level matrix

| Case | state | `error_type` | `submission_attempted` | `submission_status` | `submission_uncertain` | `reply_pending` | `retry_safe` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | `TIMED_OUT` | `connect_timeout` | True | None | False | False | True |
| B | `TIMED_OUT` | `pool_timeout` | False (pool exhausted before the submission) | None | False | False | True |
| C | `PROVIDER_UNAVAILABLE` | `connect_error` | True | None | False | False | True |
| D | `PROVIDER_UNAVAILABLE` | `proxy_error` (synthetic) | True | None | False | False | True |
| E | `PROVIDER_UNAVAILABLE` | `unsupported_protocol` | False (rejected at the probe) | None | False | False | True |
| F | `PROVIDER_UNAVAILABLE` | `local_protocol_error` | False (rejected at the probe) | None | False | False | True |
| G | `TIMED_OUT` | `read_timeout` | True | None | **True** | **True** | **False** |
| H | `TIMED_OUT` | `write_timeout` | True | None | **True** | **True** | **False** |
| I | `PROVIDER_UNAVAILABLE` | `read_error` | True | None | **True** | **True** | **False** |
| J | `PROVIDER_UNAVAILABLE` | `remote_protocol_error` | True | None | **True** | **True** | **False** |
| K | `PROVIDER_UNAVAILABLE` | `remote_protocol_error` | True | None | **True** | **True** | **False** |
| L | `PROVIDER_UNAVAILABLE` | `close_error` | True | None | **True** | **True** | **False** |
| M | `PROVIDER_UNAVAILABLE` | `http_status` | True | 500 | False | False | **False** |
| N | `COMPLETED` | `""` | True | 200 | False | False | **False** |

Relations verified: PROVEN_NON_DELIVERY ⇒ `submission_uncertain == False` (the reverse is
not sufficient — case **M** has `submission_uncertain == False` while the request was fully
submitted and an HTTP status arrived, and it is never non-delivery, never `retry_safe`);
an uncertain *submitted* operation is never `retry_safe`; `UNREACHABLE_CURRENT_CONFIGURATION`
(D) carries no positive evidence for the current production configuration.

## 8. `write_error` reachability finding (explicit)

* **Classifier mapping exists**: `httpx.WriteError → write_error → submission_uncertain=True`
  (verified by direct invocation; the mapping is kept, and it is not erroneous).
* **Installed HTTP/1.1 request-send reachability**: the precommitted body-write
  `WriteError` trigger does **not** reach that mapping — httpcore suppresses it
  (`_sync/http11.py` `except WriteError: pass`) and the operation later surfaces
  `remote_protocol_error` (uncertain).
* Recorded status: `write_error` = **DEFENSIVE / NOT EXERCISED BY THIS INSTALLED
  REQUEST-SEND PATH**.  It is **not** claimed that `write_error` can never arise in any
  future stack.

## 9. Request-count / no-retry evidence

Exactly one submission POST was issued per case whose submission reached the wire
(observed 1 for G–N); the pre-send classes show 0 observed POST bytes while the bridge
still reports the logical attempt (A/C/D) or no attempt at all (B/E/F, where the
probe/scheme/header failed first) — the precommitted distinction between the logical
submission attempt and the bytes actually sent.  Ledger accounting: 4 call records for
A/C/D/M/N, 1 for B/E/F, 6 for G–L (probe + boundary read + POST + one follow-up read),
with exactly one prompt-carrying `send_prompt` record per case and unique call ids — no
automatic retry, no hidden fallback, no second model-turn submission, and an uncertain
classification never caused another POST.

## 10. `retry_safe` authority boundary

Precommitted and preserved: `retry_safe` is **not** P5 authority.  PROVEN_NON_DELIVERY may
correspond to `retry_safe=true`, but frozen v0.3-E gives it **no** automatic retry
authority, **no** explicit recovery retry authority, **no** refund authority, **no**
state-transition authority and **no** adoption authority; for SUBMISSION_UNCERTAIN,
UNCLASSIFIED_FAIL_CLOSED, HTTP rejection and success it is never a licence to resubmit.
P5 evidence remains **informational only**; `mark_unrecoverable` stays the mandatory
fail-closed resolution and adoption stays disabled.

## 11. Invalid attempts and no-probe-shopping compliance

* **Invalid harness attempts: none.**  The corrected A–N matrix executed once each and
  every case reached its precommitted assertion point on that single execution; no case
  was re-run.  (The only pre-execution correction was a mechanical harness static-assertion
  bug — the `start_tls` source-block locator picked the first `start_tls` body — fixed
  **before** any case ran; no semantic rule, class definition or expected result changed.)
* No expected class, exception family, source interpretation, trigger or allowed set was
  changed after execution started; no alternate trigger was added; nothing was re-run
  until an expected output appeared.

## 12. Limitations and non-claims

G0.3 does not prove remote receipt/non-receipt beyond the proven pre-send classes,
provider execution, delivery truth for uncertain classes, safe retry, retry-protocol
correctness, refund safety, automatic recovery, adoption, P1/P2/P3/P4/P6/P8/P9, G0.4–G2,
or future implementation correctness.  Additional recorded limitations: the scripted
backend emulates the installed backend's exception contract at the documented
`NetworkBackend`/`NetworkStream` boundary rather than real sockets; case B's and E's
DevRelay-level observations are probe-stage while the submission-level evidence is the
transport-level probe; case F's pre-send property is established for the accepted bucket
(the mid-send mapping escape is recorded as a limitation, not as P5 evidence); case D
carries no current-production evidence value; the mid-send h11 observability weakness
remains unremediated (runtime changes are out of scope); the harness and raw per-case
evidence live only in the OS temp area and are not committed.

**P3 — static-assertion auditability (retained limitation):** the thirteen static
assertions and the harness/raw per-case evidence were **not** fully committed; the
documentary record lists the source anchors (the A/C connect+TLS mappings, the B pool-wait
ordering, the E scheme rejection, the F request-construction mapping boundary, the D
`trust_env=False`/no-proxy configuration, the h11 class hierarchy and the service defensive
boundary) and the recorded source SHA-256 values (`httpcore/_backends/sync.py`
`6e113877…`, `httpcore/_sync/connection.py` `f5ec4639…`, `httpcore/_sync/connection_pool.py`
`6be4fc2d…`, `httpcore/_sync/http11.py` `205a1b0f…`, `httpcore/_synchronization.py`
`cd28b5de…`, `httpx/_transports/default.py` `03379a45…`,
`src/devrelay/opencode/transport.py` `cb476363…`,
`src/devrelay/orchestration/service.py` `08b436c0…`).  The independent reviewer
re-inspected the installed source and matched the recorded hashes; no raw-evidence
reproduction is claimed and the harness is neither reconstructed nor re-run.

**P3 — mid-send h11 observability gap (preserved, no runtime change in this task):** a
mid-send `h11.LocalProtocolError` outside the accepted normalization mapping may escape to
the `internal_error` boundary; it does **not** yield `retry_safe=true`, does **not** yield
P5 proven-non-delivery authority and does **not** create a classifier safety failure — but
turn-record defaults may still show `submission_uncertain=False` and
`submission_attempted=False` although delivery state is not proven.  Those defaults must
**not** be read as proof of non-delivery; the recommended future behaviour remains to
default previously unclassified transport-layer escape paths to uncertainty.

**P3 — future proxy configuration (preserved):** the current accepted production
configuration has no reviewed proxy configuration and uses `trust_env=False`, so
`proxy_error` is currently non-authoritative; if a proxy configuration is added later, its
P5 classification requires a new review/proof and is not covered by this proof.

## 13. Budget

0 real provider/model inference calls; 0 real external network requests; 0 OpenCode
processes started or restarted; no runtime/test/dependency/version change.

## 14. Result: clean candidate pass -> authoritative PASS

**Candidate stage (as recorded in `3143742`):** `G0.3 = CLEAN CANDIDATE PASS / AWAITING
INDEPENDENT REVIEW` — all fourteen corrected cases executed once each under the oracle
precommitted in `e328ec5`, every verdict inside its corrected precommitted allowed set, no
invalid attempts, one semantic execution per case.

**Authoritative stage (recorded by the later bookkeeping round):** the independent review
issued ****APPROVE V0.3-E G0.3 / P5 TRANSPORT PROOF** with **P0 = 0, P1 = 0, P2 = 0****, so **`G0.3 / P5 = PASS` — authoritative and independently
approved**.  The executing agent did not self-approve it; the candidate stage above stays
recorded as the pre-approval history.

Current-production `retry_safe` matrix (as independently reviewed): A `connect_timeout` =
True; B `pool_timeout` = True; C `connect_error` = True; D `proxy_error` = synthetic
fixture may show True, but current-production authority = **N/A / unreachable**;
E `unsupported_protocol` = True; F `local_protocol_error` = True; G `read_timeout` = False;
H `write_timeout` = False; I `read_error` = False; J corrected `remote_protocol_error` =
False; K `remote_protocol_error` = False; L `close_error` / safe-set miss = False;
M HTTP rejection = False; N success = False.  `retry_safe` is **not** P5 authority: frozen
v0.3-E gives it no retry, resubmission, budget-refund, slot-restoration, state-transition,
automatic-resume or adoption authority, and P5 remains informational only with
`mark_unrecoverable` as the mandatory fail-closed resolution.

History is preserved: the original failed round (`c889636`, and its immutable oracle
`b9c4704`) stays **FAILED** with its TYPE-1 review outcome visible in
`docs/v0.3/V03E_G0_3_TRANSPORT_PROOF.md`, and this document keeps the corrected
candidate stage above.

* A/B/C/E/F: the accepted safe-labelled buckets are **class-wide pre-send** on the
  installed stack, with the class-wide source mapping recorded and the deterministic probe
  showing no request header or body byte on the wire (F stated precisely as the accepted
  bucket's pre-send-only mapping boundary).
* D: explicitly **UNREACHABLE_CURRENT_CONFIGURATION / NOT CURRENT-PRODUCTION EVIDENCE**
  — its phase is understood and the synthetic injected-proxy demonstration is recorded
  separately (that fixture alone may show `retry_safe = true`), but it carries **no**
  current-production P5 authority and must never be read as `PROVEN_NON_DELIVERY` for
  current production.
* G/H/I/K/L: every uncertain class stayed uncertain and fail-closed.
* J: exactly the corrected end-to-end expectation — body-write `httpcore.WriteError` is
  suppressed by httpcore, the operation surfaces `remote_protocol_error` with
  `submission_uncertain=True` and `retry_safe=False`.
* M/N: HTTP rejection and success are never non-delivery and never retry-safe.
* No false-safe classification, no unsafe `retry_safe`, no oracle change after execution
  began, one semantic execution per case, and the budget stayed at zero.

Unchanged alongside it: `G0.1 / P7 = PASS` and `G0.2 = PASS` (authoritative, independently
approved); `G0.4`, `G0.5`, `G1`, `G2` = **NOT RUN**; overall platform proof gate =
**PARTIALLY EXECUTED / NOT COMPLETE**; mandatory-core implementation = **NOT AUTHORIZED**;
`adopt_completed_turn` = **DISABLED**.  The original failed round (`c889636`) remains
FAILED in the historical record, with its TYPE-1 review outcome recorded.
