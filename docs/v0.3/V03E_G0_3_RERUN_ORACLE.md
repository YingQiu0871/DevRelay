# DevRelay v0.3-E — corrected G0.3 / P5 transport proof oracle (immutable pre-run manifest)

This is the **new immutable pre-run oracle** for the separately authorized **corrected
clean G0.3 / P5 rerun**.  It was committed **before any corrected semantic case was
executed**, it is not modified after that commit, and its commit SHA and file SHA-256 are
recorded in `V03E_G0_3_CLEAN_RERUN_PROOF.md`.  The **original** oracle
(`V03E_G0_3_TRANSPORT_ORACLE.md`, SHA-256
`6ca090b5d7a742be22046e0f67c8bf3980f81faea67f9e67d4b4419fbbb868e9`) and the original
failed execution record (`V03E_G0_3_TRANSPORT_PROOF.md`) remain historical and are **not**
modified.

## 1. Identity

| Item | Value |
| --- | --- |
| Repository HEAD at precommit | `c889636420f59044cda5cd62fdb61db991f876c4` |
| Branch | `v0.3-e-recovery-reconciliation` |
| Package version / public tags | `0.1.0` / `v0.1.0` only; no upstream |
| Frozen semantic design candidate | `9f4a01804b9affe8938a272553df345b5a60aeed` |
| Prior proof state | `G0.1 / P7 = PASS`, `G0.2 = PASS`, **`G0.3 = FAILED / NOT PASSED`** (`c889636`, candidate FAIL), `G0.4–G2 = NOT RUN` |
| v0.3-E status | DESIGN FROZEN / NOT IMPLEMENTED / NOT ACCEPTED / UNRELEASED |
| mandatory-core implementation | **NOT AUTHORIZED**; `adopt_completed_turn` = **DISABLED** |
| Installed stack (verified again before this freeze) | **httpx 0.28.1**, **httpcore 1.0.9**, h11 0.16.0, Python 3.14.6 |
| Budget | **0** provider/model inference calls, **0** real external network requests, **0** OpenCode processes |

## 2. Previous Type-1 failure chronology (preserved, not flattened)

original G0.3 execution (`b9c4704` pre-run oracle → `c889636` execution) → case **J**
classification mismatch (the precommitted `write_error` exposure was not produced) →
**G0.3 CANDIDATE FAIL** → independent review decision **FAIL — V0.3-E G0.3 / P5 PROOF —
TYPE 1 PROOF-PLAN FAILURE** with **P0 = 0, P1 = 0, P2 = 0** → corrected clean rerun
separately authorized (this manifest).

Recorded distinction (from the independent review, unchanged by this rerun):

* **old proof result: FAIL** (`c889636` stays FAILED; it is not rewritten as PASS);
* **old safety finding: no classifier safety failure established** — no accepted
  safe/non-delivery bucket was shown to be unsafe;
* **reason: the immutable case-J exact-classification expectation was wrong for the
  installed HTTP/1.1 request-send path** (a proof-plan/installed-stack reachability
  mismatch, TYPE 1), and **no runtime remediation is required** by the review.

## 3. Accepted classifier (re-derived from current source before this freeze)

`src/devrelay/opencode/transport.py::transport_failure`, re-verified by direct
invocation:

| Bucket | Exception | `submission_uncertain` | `state` |
| --- | --- | --- | --- |
| `connect_timeout` | `httpx.ConnectTimeout` | False | `TIMED_OUT` |
| `pool_timeout` | `httpx.PoolTimeout` | False | `TIMED_OUT` |
| `connect_error` | `httpx.ConnectError` | False | `PROVIDER_UNAVAILABLE` |
| `proxy_error` | `httpx.ProxyError` | False | `PROVIDER_UNAVAILABLE` |
| `unsupported_protocol` | `httpx.UnsupportedProtocol` | False | `PROVIDER_UNAVAILABLE` |
| `local_protocol_error` | `httpx.LocalProtocolError` | False | `PROVIDER_UNAVAILABLE` |
| `read_timeout` | `httpx.ReadTimeout` | True | `TIMED_OUT` |
| `write_timeout` | `httpx.WriteTimeout` | True | `TIMED_OUT` |
| `read_error` / `write_error` / `remote_protocol_error` / `close_error` / anything else | the exception's snake-case name | True | `PROVIDER_UNAVAILABLE` |
| `http_status` (HTTP rejection) | non-2xx response | False | `PROVIDER_UNAVAILABLE` |
| `""` (success) | 2xx JSON | False | `COMPLETED` |

Non-transport `httpx.HTTPError` and `OSError` are `submission_uncertain=True`;
`bridge.py::send_prompt` routes definite failures through `_failure` and uncertain ones
through `_uncertain_submission` (one bounded follow-up read, never a second POST);
`mcp/tools.py::_retry_safe` exposes `retry_safe` as **evidence only**.

**This matches the independently reviewed state; no classifier drift was found.**

## 4. Class-wide installed-source findings (precommitted; part of the proof)

These are **class-wide** statements about the installed stack, not single-fixture
observations.  The harness asserts each source location mechanically before/with the
cases.

| Class | Class-wide finding | Installed-source location / phase |
| --- | --- | --- |
| **A `connect_timeout`** | **CLASS-WIDE PRE-SEND** | `httpcore/_backends/sync.py` `connect_tcp` maps `socket.timeout → ConnectTimeout` (and `start_tls` maps the same for the TLS handshake); `httpcore/_sync/connection.py::HTTPConnection._connect` is the only place a stream is created, before the connection can send any request byte |
| **B `pool_timeout`** | **CLASS-WIDE PRE-SEND** | `httpcore/_synchronization.py` thread-based `Event.wait` raises `PoolTimeout`; it is reached from `httpcore/_sync/connection_pool.py` `PoolRequest.wait_for_connection(timeout=…)`, i.e. while waiting for pool assignment, before the request is handed to any connection |
| **C `connect_error`** | **CLASS-WIDE PRE-SEND for the accepted configuration** | `httpcore/_backends/sync.py` `connect_tcp` / `start_tls` map `OSError → ConnectError`; the accepted paths arise in connection establishment / TLS / connect-phase failures, before any request byte can be written |
| **D `proxy_error`** | **UNREACHABLE / NON-AUTHORITATIVE FOR THE CURRENT ACCEPTED CONFIGURATION** | `src/devrelay/opencode/transport.py` builds `httpx.Client(..., trust_env=False)` with **no** proxy argument and records that DevRelay has no reviewed proxy configuration mechanism; `httpx/_transports/default.py` constructs `httpcore.HTTPProxy`/`SOCKSProxy` only behind an explicit proxy branch.  A synthetic injected-proxy probe may demonstrate phase behaviour but **must not** become current-production positive evidence; future configurable proxy support requires a new review |
| **E `unsupported_protocol`** | **CLASS-WIDE PRE-SEND** | `httpcore/_sync/connection_pool.py::handle_request` rejects a missing/unsupported scheme before any connection is created.  Practical reachability under the accepted `http`/`https` base URL is a separate recorded caveat |
| **F `local_protocol_error`** | **THE ACCEPTED BUCKET IS PRE-SEND-ONLY** | the accepted mapping `h11.LocalProtocolError → httpcore.LocalProtocolError` wraps **only** the pre-network `h11.Request(...)` construction in `httpcore/_sync/http11.py::_send_request_headers`; the later `_send_event` (`self._h11_state.send(event)` → `network_stream.write`) is **outside** that mapping, so a mid-send `h11.LocalProtocolError` does **not** become DevRelay's `local_protocol_error` / `submission_uncertain=False` / `retry_safe=True` bucket — it escapes the accepted transport normalization layer instead |

Corrections recorded against the earlier round:

* the **stale httpcore comment** in `_sync/http11.py::_receive_event` ("treat it as a
  ConnectError") must **not** be used as evidence: the code raises
  `RemoteProtocolError` in that path, which is what the executed cases observed;
* `write_error` is a **defensive accepted classifier mapping** that this installed
  HTTP/1.1 request-send path does **not** exercise (see §5 and the corrected case J).

## 5. Corrected case J semantics (the TYPE-1 correction)

Precommitted trigger (unchanged from the original proof plan):

```
request headers written
→ request-body write raises httpcore.WriteError
```

Precommitted **end-to-end exposed class and safety result** for the installed stack:

```
httpcore HTTP/1.1 handle_request catches/suppresses WriteError
→ response-read phase continues
→ closed / no-response peer yields RemoteProtocolError
→ httpx.RemoteProtocolError
→ DevRelay remote_protocol_error
→ submission_uncertain = True
→ retry_safe = False
```

Expected corrected verdict: **SUBMISSION_UNCERTAIN** with **no** non-delivery authority,
**no** retry, **no** refund, **no** state authority.  If any other result occurs, case J
FAILS and the corrected rerun FAILS (no retry).

Recorded separately: `httpx.WriteError → write_error → submission_uncertain=True`
remains a valid defensive classifier mapping, but the precommitted body-write
`WriteError` trigger does **not** reach it on this installed HTTP/1.1 request-send path.
It is **not** claimed that `write_error` can never arise anywhere in any future stack.

## 6. Unmapped mid-send h11 limitation (precommitted static assertion + limitation)

Precommitted static assertions (checked mechanically by the harness, not a new semantic
case): `h11.LocalProtocolError` is **not** a subclass of `httpx.TransportError`,
`httpx.HTTPError` or `OSError`; therefore a mid-send `h11.LocalProtocolError` escapes
`OpenCodeTransport.request`'s handlers (`httpx.TransportError` → `transport_failure`,
`httpx.HTTPError`, `OSError`) and reaches the higher internal error boundary
(`orchestration/service.py` `except Exception` → `error_type="internal_error"`).

Recorded **limitation / future remediation item** (from the independent review, not a
claim of correctness): this escape path currently remains fail-closed for authority
purposes — no `retry_safe=true`, no P5 proven-non-delivery classification, the turn ends
blocked / internal-error — **but** the turn-record defaults may show
`submission_uncertain=False` and `submission_attempted=False`, which is an
**observability weakness**.  Recommended future behaviour: default previously
unclassified transport-layer escape paths to uncertainty.  **This rerun does not modify
runtime code.**  P5 does **not** prove that anything on this path was not submitted.

## 7. Verdict classes (precommitted)

* **PROVEN_NON_DELIVERY** — used only for a **current accepted reachable** class whose
  **entire accepted bucket** is proven pre-submission (class-wide source mapping plus the
  deterministic boundary probe).
* **UNREACHABLE_CURRENT_CONFIGURATION** — the phase may be understood, but the class
  cannot occur through the current accepted production configuration and therefore must
  not be relied on positively by current recovery logic.
* **SUBMISSION_UNCERTAIN** — submission may have begun (bytes may have left the process);
  non-delivery is not proven.
* **NOT_A_NON_DELIVERY_CLASS** — HTTP responses and success control; never non-delivery
  evidence, never `retry_safe` on their own.
* **UNCLASSIFIED_FAIL_CLOSED** — an escape path not normalized by the accepted transport
  classifier (recorded as fail-closed, never as non-delivery).
* **CLASSIFICATION_MISMATCH** — only if the actual end-to-end classification differs from
  the **corrected** precommitted installed-stack expectation.

## 8. Fixed corrected A–N matrix (one semantic execution per case)

| Case | Trigger | Precommitted expected outcome |
| --- | --- | --- |
| **A** `connect_timeout` | connect call raises the connect-phase timeout before any stream exists | **PROVEN_NON_DELIVERY** |
| **B** `pool_timeout` | the single pooled connection is held; the submission never acquires a connection | **PROVEN_NON_DELIVERY** |
| **C** `connect_error` | connect call raises the connect-phase connection error | **PROVEN_NON_DELIVERY** |
| **D** `proxy_error` | synthetic injected-proxy phase demonstration (recorded separately) | **UNREACHABLE_CURRENT_CONFIGURATION** (the synthetic phase demonstration must not be promoted to current-production positive evidence) |
| **E** `unsupported_protocol` | non-http(s) scheme rejected by the pool before any connect | **PROVEN_NON_DELIVERY** (reachability caveat recorded separately) |
| **F** `local_protocol_error` | illegal configured header rejected while the h11 request event is constructed, before any write; class-wide stated from the installed source mapping | **PROVEN_NON_DELIVERY** for the accepted bucket |
| **G** `read_timeout` | request fully written, then the read phase times out | **SUBMISSION_UNCERTAIN** |
| **H** `write_timeout` | request headers written, then the body write times out | **SUBMISSION_UNCERTAIN** |
| **I** `read_error` | request fully written, then the read phase raises the I/O error | **SUBMISSION_UNCERTAIN** |
| **J** body-write `httpcore.WriteError` | headers written → body write raises `WriteError` → suppressing stack path | exposed class **`remote_protocol_error`**, verdict **SUBMISSION_UNCERTAIN** |
| **K** `remote_protocol_error` | request fully written, then protocol-violating peer bytes | **SUBMISSION_UNCERTAIN** |
| **L** `close_error` / unclassified safe-set miss | a concrete installed `httpx.TransportError` the safe set does not name, delivered at the accepted transport boundary | **SUBMISSION_UNCERTAIN** or **UNCLASSIFIED_FAIL_CLOSED** according to the exact accepted boundary — **never PROVEN_NON_DELIVERY** |
| **M** HTTP rejection | deterministic non-2xx response, no real network | **NOT_A_NON_DELIVERY_CLASS** |
| **N** success | deterministic valid 2xx JSON | **NOT_A_NON_DELIVERY_CLASS** |

These sets are **not** broadened after execution starts.

## 9. Consistency relations to be verified

* PROVEN_NON_DELIVERY ⇒ `submission_uncertain == False` (the reverse is **not**
  sufficient; case M demonstrates the reverse);
* a submitted, uncertain operation is never `retry_safe` and never causes another POST;
* `UNREACHABLE_CURRENT_CONFIGURATION` (D) carries **no** positive evidence value for the
  current production configuration;
* no false-safe classification: no class that can occur post-send may be labelled
  non-delivery.

## 10. `retry_safe` authority boundary (precommitted)

`retry_safe` is **not** P5 authority.  For the current exposed surface,
PROVEN_NON_DELIVERY may correspond to `retry_safe=true`, but frozen v0.3-E still gives
it **no** automatic retry authority, **no** explicit recovery retry authority, **no**
refund authority, **no** state-transition authority and **no** adoption authority.  For
SUBMISSION_UNCERTAIN, UNCLASSIFIED_FAIL_CLOSED, HTTP rejection and success, `retry_safe`
must never become a licence to resubmit.  P5 evidence remains **informational only**
(`V03E_SPEC.md` §15, §19 row E): `mark_unrecoverable` stays the mandatory fail-closed
resolution and adoption stays disabled.

## 11. No-probe-shopping rule (precommitted)

The corrected A–N matrix is fixed before execution; **one semantic execution per case**.
A rerun is permitted only for a mechanical harness defect that prevents the case from
reaching the precommitted assertion point (recorded separately and excluded).  If a case
reaches its semantic assertion and differs from this corrected oracle, **that result
counts**: no expected class change, no exception-family substitution, no source
interpretation change, no alternate trigger, no rerun until the expected output appears.

## 12. Budget and offline constraints

0 provider/model inference calls, 0 real external network requests, 0 OpenCode processes.
Only installed-source inspection, the real accepted classifier, the real
httpx/httpcore/h11 stack driven by an in-process scripted `NetworkBackend`/
`NetworkStream`, and a deterministic fake transport where needed — no DNS, TCP,
localhost server, provider API, model inference or Internet access, and no repository
write beyond the documented docs/evidence files.

## 13. Immutability

After the pre-run commit that introduces this file it is **not modified**; a correction
would require a new authorization and a new manifest with its own pre-run commit.  The
evidence document records this file's commit SHA and SHA-256 so a reviewer can verify the
oracle existed before the corrected execution.
