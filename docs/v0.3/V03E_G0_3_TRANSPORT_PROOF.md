# DevRelay v0.3-E — G0.3 / P5 transport classification proof (offline)

Status: **G0.3 = CANDIDATE FAIL — TRANSPORT NON-DELIVERY SAFETY NOT ESTABLISHED**
(by the precommitted standard: case **G0.3-J** did not produce its precommitted result).
This result **remains FAILED** and is not rewritten.

> **Independent review outcome and corrected rerun (recorded afterwards; this record's
> evidence is unchanged):** the independent review of this failed round issued **FAIL —
> V0.3-E G0.3 / P5 PROOF — TYPE 1 PROOF-PLAN FAILURE** with **P0 = 0, P1 = 0, P2 = 0**.
> It determined that this candidate correctly failed its immutable oracle, that case J's
> exact classification expectation was wrong for the installed HTTP/1.1 request-send path
> (a proof-plan / installed-stack reachability mismatch), that the surfaced outcome
> remains submission-uncertain and fail-closed, that **no accepted safe/non-delivery
> classifier bucket was shown to be unsafe**, and that **no runtime remediation is
> required**.  A separately authorized corrected clean rerun under the new precommitted
> oracle `docs/v0.3/V03E_G0_3_RERUN_ORACLE.md` follows this record; its outcome is
> recorded in `docs/v0.3/V03E_G0_3_CLEAN_RERUN_PROOF.md`.

The six accepted "definitely not submitted" classes were all **proven pre-send** on the
installed stack, and no uncertain class was ever promoted to non-delivery — but one
precommitted semantic case (J, `write_error`) could not be observed as such, so the
clean candidate PASS conditions of the pre-run manifest are **not** met.  This is
recorded as-is: no oracle rule, class definition or expected result was changed, and
case J was **not** re-run.

## 1. Identity

| Item | Value |
| --- | --- |
| Starting HEAD | `efa2ca32a2f979cf88860c222e411181b451956b` |
| Pre-run oracle commit | `b9c47048e3ffc483e8ac6b37a1028ab194ebbc5b` (`docs(v03e): freeze G0.3 transport proof oracle`), parent `efa2ca32a2f979cf88860c222e411181b451956b` |
| Pre-run oracle file SHA-256 | `6ca090b5d7a742be22046e0f67c8bf3980f81faea67f9e67d4b4419fbbb868e9` (`docs/v0.3/V03E_G0_3_TRANSPORT_ORACLE.md`; unchanged at execution time) |
| Branch | `v0.3-e-recovery-reconciliation` |
| Frozen semantic design candidate | `9f4a01804b9affe8938a272553df345b5a60aeed` |
| Installed proof target | **httpx 0.28.1**, **httpcore 1.0.9**, h11 0.16.0, Python 3.14.6 |
| Frozen v0.3-E status | DESIGN FROZEN / NOT IMPLEMENTED / NOT ACCEPTED / UNRELEASED |
| Other gate steps | `G0.1 / P7 = PASS`, `G0.2 = PASS`; `G0.4`, `G0.5`, `G1`, `G2` = NOT RUN |
| Provider / model inference calls | **0** |
| Real external network requests | **0** (in-process scripted `httpcore` network backend only) |
| OpenCode processes started | **0** |
| Runtime / test / dependency / version change | **none** (`git diff efa2ca3 -- src/devrelay tests pyproject.toml` empty) |

## 2. Accepted source classification (verified before probes)

`src/devrelay/opencode/transport.py::transport_failure` maps transport exceptions to
`error_type` / `submission_uncertain` / `state`; `bridge.py::send_prompt` routes definite
failures through `_failure` (no uncertainty) and uncertain ones through
`_uncertain_submission` (one bounded follow-up read, never a second POST);
`mcp/tools.py::_retry_safe` exposes `retry_safe`.

Direct invocation of the accepted classifier (mechanical matrix, no case executed):

| Exception | `error_type` | `submission_uncertain` | `state` |
| --- | --- | --- | --- |
| `httpx.ConnectTimeout` | `connect_timeout` | `False` | `TIMED_OUT` |
| `httpx.PoolTimeout` | `pool_timeout` | `False` | `TIMED_OUT` |
| `httpx.ConnectError` | `connect_error` | `False` | `PROVIDER_UNAVAILABLE` |
| `httpx.ProxyError` | `proxy_error` | `False` | `PROVIDER_UNAVAILABLE` |
| `httpx.UnsupportedProtocol` | `unsupported_protocol` | `False` | `PROVIDER_UNAVAILABLE` |
| `httpx.LocalProtocolError` | `local_protocol_error` | `False` | `PROVIDER_UNAVAILABLE` |
| `httpx.ReadTimeout` | `read_timeout` | `True` | `TIMED_OUT` |
| `httpx.WriteTimeout` | `write_timeout` | `True` | `TIMED_OUT` |
| `httpx.ReadError` | `read_error` | `True` | `PROVIDER_UNAVAILABLE` |
| `httpx.WriteError` | `write_error` | `True` | `PROVIDER_UNAVAILABLE` |
| `httpx.RemoteProtocolError` | `remote_protocol_error` | `True` | `PROVIDER_UNAVAILABLE` |
| `httpx.CloseError` | `close_error` | `True` | `PROVIDER_UNAVAILABLE` |

This matches the precommitted matrix exactly: **no classifier-name mismatch** was found.
The proof's remaining question was therefore the **stack-phase** question, and that is
where case J failed.

## 3. Stack-phase evidence and send-boundary instrumentation

The real accepted path (DevRelay transport/bridge → real `httpx.Client` → real
`httpx.HTTPTransport` → real `httpcore.ConnectionPool`/`HTTPProxy` → real h11) was driven
with an in-process scripted `httpcore.NetworkBackend`/`NetworkStream` installed by
monkeypatching the pool constructor inside the disposable harness.  The scripted
backend/stream raises exactly the classes the installed real backend raises at the same
phases (`ConnectError`/`ConnectTimeout` from `connect_tcp`; `ReadTimeout`/`WriteTimeout`/
`ReadError`/`WriteError` from the stream I/O calls — the real
`httpcore._backends.sync` maps its socket errors to those classes inside those methods).
No network, DNS, socket or localhost server is involved.

Recorded boundary evidence per case (transport-level submission request; marker-based
body detection):

* `connection_acquired` (connections created for the request under test);
* `request_headers_send_started` — a `POST …` header block handed to `NetworkStream.write`;
* `request_body_send_started` / `request_body_bytes_observed` — the prompt marker bytes
  handed to `NetworkStream.write`;
* `proxy_connect_bytes_observed` — `CONNECT …` bytes (proxy flavours only);
* the failure phase/exception recorded at the stream boundary.

## 4. Cases A–N (one execution each; precommitted vs observed)

| Case | Precommitted class / expected | Observed class | Observed verdict | Transport `unc` | Case |
| --- | --- | --- | --- | --- | --- |
| G0.3-A | `connect_timeout` / PROVEN_NON_DELIVERY | `connect_timeout` | **PROVEN_NON_DELIVERY** | False | PASS |
| G0.3-B | `pool_timeout` / PROVEN_NON_DELIVERY | `pool_timeout` | **PROVEN_NON_DELIVERY** | False | PASS |
| G0.3-C | `connect_error` / PROVEN_NON_DELIVERY | `connect_error` | **PROVEN_NON_DELIVERY** | False | PASS |
| G0.3-D | `proxy_error` / PROVEN_NON_DELIVERY | `proxy_error` | **PROVEN_NON_DELIVERY** | False | PASS |
| G0.3-E | `unsupported_protocol` / PROVEN_NON_DELIVERY | `unsupported_protocol` | **PROVEN_NON_DELIVERY** | False | PASS |
| G0.3-F | `local_protocol_error` / PROVEN_NON_DELIVERY | `local_protocol_error` | **PROVEN_NON_DELIVERY** | False | PASS |
| G0.3-G | `read_timeout` / SUBMISSION_UNCERTAIN | `read_timeout` | **SUBMISSION_UNCERTAIN** | True | PASS |
| G0.3-H | `write_timeout` / SUBMISSION_UNCERTAIN | `write_timeout` | **SUBMISSION_UNCERTAIN** | True | PASS |
| G0.3-I | `read_error` / SUBMISSION_UNCERTAIN | `read_error` | **SUBMISSION_UNCERTAIN** | True | PASS |
| G0.3-J | `write_error` / SUBMISSION_UNCERTAIN | `remote_protocol_error` | **CLASSIFICATION_MISMATCH** | True | **FAIL** |
| G0.3-K | `remote_protocol_error` / SUBMISSION_UNCERTAIN | `remote_protocol_error` | **SUBMISSION_UNCERTAIN** | True | PASS |
| G0.3-L | unclassified (`CloseError`) / SUBMISSION_UNCERTAIN | `close_error` | **SUBMISSION_UNCERTAIN** | True | PASS |
| G0.3-M | HTTP rejection / NOT_A_NON_DELIVERY_CLASS | `http_status` (500) | **NOT_A_NON_DELIVERY_CLASS** | False | PASS |
| G0.3-N | success control / NOT_A_NON_DELIVERY_CLASS | `""` (2xx JSON) | **NOT_A_NON_DELIVERY_CLASS** | False | PASS |

Boundary detail (transport-level probe):

| Case | connections | POST headers sent | body marker observed | proxy CONNECT bytes | boundary failure |
| --- | --- | --- | --- | --- | --- |
| A | 1 | **no** | **no** | no | `connect_tcp` → `ConnectTimeout` |
| B | 1 (blocker only; the submission never acquired a connection) | **no** | **no** | no | pool exhaustion (`PoolTimeout` from the pool wait) |
| C | 1 | **no** | **no** | no | `connect_tcp` → `ConnectError` |
| D | 1 | **no** | **no** | **yes** (CONNECT rejected) | proxy tunnel rejection → `ProxyError` |
| E | **0** | **no** | **no** | no | scheme rejected by the pool before connect |
| F | 1 | **no** | **no** | no | illegal configured header rejected while the request event is constructed |
| G | 1 | yes | yes | no | `read` → `ReadTimeout` |
| H | 1 | yes | yes | no | `write_body` → `WriteTimeout` |
| I | 1 | yes | yes | no | `read` → `ReadError` |
| J | 1 | yes | yes | no | `write_body` → `WriteError` (**swallowed by httpcore**, see §5) |
| K | 1 | yes | yes | no | protocol-violating peer bytes → `RemoteProtocolError` |
| L | 0 (constructed transport) | n/a | n/a | no | constructed `CloseError` at the accepted transport boundary |
| M | 1 | yes | yes | no | HTTP 500 response |
| N | 1 | yes | yes | no | 2xx JSON response |

## 5. The failing case: G0.3-J (`write_error`)

* The precommitted trigger executed exactly as specified: the POST headers were written
  and the **body write raised `httpcore.WriteError`** (recorded at phase `write_body`).
* The installed httpcore **suppresses** a `WriteError` raised while sending a request:
  `httpcore/_sync/http11.py` (and its async twin) wraps the header/body send in
  `except WriteError: pass` and then proceeds to read the response.  With the peer
  closed, the read fails with `RemoteProtocolError` — so the accepted classifier
  observed **`remote_protocol_error`** (still `submission_uncertain=True`), not
  `write_error`.
* The accepted classifier itself is correct for the class (`WriteError` →
  `write_error` / uncertain, §2), so this is a **stack-reachability** result, not a
  classifier-name mismatch — but the case's precommitted result (SUBMISSION_UNCERTAIN
  with the `write_error` class) was not produced, and per the precommitted
  no-probe-shopping rule the result counts and the case was not re-run.
* Safety consequence: **none** — the surfaced class is submission-uncertain, so no
  non-delivery claim was derived from it.  The `write_error` branch is defensive and,
  on the installed HTTP/1.1 stack, not reachable through the accepted request path
  (`WriteTimeout` is *not* suppressed and did propagate — case H).
* Because P5 evidence is **informational only** in the frozen design (`V03E_SPEC.md`
  §15, §19 row E), no capability is silently degraded by this finding; the reviewer
  decides whether the P5 class list / trigger definition needs scoping.

## 6. DevRelay-level matrix (accepted bridge + MCP `retry_safe`)

| Case | state | `error_type` | `submission_attempted` | `submission_status` | `submission_uncertain` | `reply_pending` | `retry_safe` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | `TIMED_OUT` | `connect_timeout` | True | None | False | False | **True** |
| B | `TIMED_OUT` | `pool_timeout` | False (pool exhausted before the submission) | None | False | False | **True** |
| C | `PROVIDER_UNAVAILABLE` | `connect_error` | True | None | False | False | **True** |
| D | `PROVIDER_UNAVAILABLE` | `proxy_error` | True | None | False | False | **True** |
| E | `PROVIDER_UNAVAILABLE` | `unsupported_protocol` | False (scheme rejected at the probe) | None | False | False | **True** |
| F | `PROVIDER_UNAVAILABLE` | `local_protocol_error` | False (illegal header at the probe) | None | False | False | **True** |
| G | `TIMED_OUT` | `read_timeout` | True | None | **True** | **True** | **False** |
| H | `TIMED_OUT` | `write_timeout` | True | None | **True** | **True** | **False** |
| I | `PROVIDER_UNAVAILABLE` | `read_error` | True | None | **True** | **True** | **False** |
| J | `PROVIDER_UNAVAILABLE` | `remote_protocol_error` | True | None | **True** | **True** | **False** |
| K | `PROVIDER_UNAVAILABLE` | `remote_protocol_error` | True | None | **True** | **True** | **False** |
| L | `PROVIDER_UNAVAILABLE` | `close_error` | True | None | **True** | **True** | **False** |
| M | `PROVIDER_UNAVAILABLE` | `http_status` | True | 500 | False | False | **False** |
| N | `COMPLETED` | `""` | True | 200 | False | False | **False** |

Consistency relations (all verified in the recorded evidence):

* **PROVEN_NON_DELIVERY ⇒ `submission_uncertain == False`** ✓ (A–F).
* The reverse is **not** sufficient: case **M** has `submission_uncertain == False`
  while the request was fully submitted (headers and body bytes observed) and an HTTP
  status was received — it is never treated as non-delivery, never `retry_safe`, and
  nothing is refunded.
* **SUBMISSION_UNCERTAIN with an attempted submission ⇒ `retry_safe == False`** ✓
  (G–L).  Cases B/E/F report `retry_safe=True` because no submission POST was ever
  issued (the probe/scheme/header failed first) — the documented "nothing was
  submitted" reading, not a non-delivery claim about a submitted prompt.
* `reply_pending == True` exactly for the uncertain POST outcomes (G–L), matching the
  accepted `_uncertain_submission` path.

## 7. Request-count / no-retry evidence

* Scripted-boundary request inventory per case: the DevRelay-level probe issues the
  ownership probe, the `read_messages` ownership fetch, the boundary read, exactly
  **one** submission POST, and (uncertain cases only) one follow-up read — never a
  second POST (`request_headers_sent_count == 1` for every case whose submission
  reached the wire; `0` for the pre-send classes where no bytes were sent).
* Ledger accounting (accepted bridge, `NullOpenCodeLedger` with per-call evidence):
  pre-send classes A/C/D issue 4 call records, B/E/F issue 1 (the probe), uncertain
  cases G–L issue 6 (probe + boundary read + POST + follow-up read, all accounted),
  M/N issue 4.  Exactly **one** prompt-carrying `send_prompt` call record exists in
  every case where a submission was attempted — there is no hidden resubmission and no
  second model-turn submission.
* Important accounting distinction (precommitted manifest §5/§15): the DevRelay
  *logical* submission attempt (`submission_attempted=True`) and the request bytes
  actually sent are separate facts — a pre-send transport failure records a logical
  attempt with **zero** POST bytes on the wire, and the ledger still records the ISSUED
  call because the accepted bridge records the attempt before the request leaves.
* No automatic POST retry, no fallback, no second attempt was observed in any case; the
  uncertain classification never caused another POST.

## 8. `retry_safe` authority boundary (no recovery authority)

`retry_safe` is exposed **as evidence only**.  Frozen v0.3-E gives it **no** recovery
execution authority: it must not cause a retry, a resubmission, an automatic follow-up
model turn, a budget refund, a state transition, a slot restoration or adoption.  The
mandatory core's fail-closed resolution remains `mark_unrecoverable`, adoption remains
**DISABLED**, and `model_turns_used` is never refunded based on transport certainty.
Nothing in this proof changes that.

## 9. Invalid harness attempts (recorded, excluded)

Recorded in full in the harness evidence (`evidence/invalid_attempts.json`):

1. **G0.3-A, G0.3-C, G0.3-L — defective harness assertion (mechanical).**  A harness-level
   check required one observed POST header write whenever the bridge reported
   `submission_attempted=True`; for a pre-send failure the bridge legitimately reports a
   logical attempt with zero bytes on the wire (and the constructed-transport case
   bypasses httpcore entirely, so the stream instrumentation cannot see the POST).  The
   assertion was corrected to the precommitted distinction (at most one POST; exactly one
   only when the submission reached the wire; the observed POST count for the
   constructed case taken from its own transport handler).  No oracle rule, class
   definition or expected result changed; the excluded pass's verdicts were already
   correct, and the corrected re-runs are the evidence of record.
2. **G0.3-D — proxy fixture defect (mechanical).**  The bridge-level proxy script first
   answered the CONNECT request with the route factory and then was applied to an http
   origin (where the installed stack uses the forward-proxy form, no CONNECT), producing
   `invalid_json` / `empty_response` instead of the proxy class.  The script now answers
   CONNECT with `200 Connection Established`, serves the stub payload only for the
   tunnelled request, rejects the POST's CONNECT with 400, and runs the bridge probe
   against an https origin so the installed stack takes the tunnel path the
   `proxy_error` class belongs to.  The case verdict was already correct in the excluded
   pass; the corrected re-run is the evidence of record.
3. **G0.3-J was NOT re-run.**  Its precommitted trigger executed and produced a semantic
   result (`CLASSIFICATION_MISMATCH`), so per the precommitted rule the result counts.

No case was re-run to obtain a different semantic result, no substitute exception was
used, no expected outcome was changed, and no send-boundary hook was moved.

## 10. Limitations and non-claims

Even if re-reviewed, G0.3 does **not** prove: remote provider receipt or non-receipt
beyond the proven pre-send classes; provider execution; delivery truth for uncertain
classes; safe retry; retry-protocol correctness; budget-refund safety; automatic
recovery; adoption; P1/P2/P3/P4/P6/P8/P9; G0.4–G2; or future v0.3-E implementation
correctness.  Additional recorded limitations:

* the scripted network backend is an in-process fake; it emulates the installed
  backend's exception contract at the documented `NetworkStream`/`NetworkBackend`
  boundary, not real sockets (real-socket behaviour is out of scope for an offline
  proof and was not claimed);
* case B's DevRelay-level observation is the pool-exhaustion class arriving at the
  ownership probe (the submission never acquired a connection); the submission-level
  class evidence is the transport-level probe;
* case E's DevRelay-level observation is the scheme rejection at the ownership probe
  (all requests share the scheme); the submission-level class evidence is the
  transport-level probe;
* case F's class is proven pre-send for the trigger reachable through the accepted
  configuration (an illegal configured header value rejected while the h11 request event
  is constructed); the installed stack can also map a mid-send h11 state-machine
  rejection to `LocalProtocolError`, which the accepted path does not exercise and which
  this proof therefore does not claim to be pre-send;
* `proxy_error` is unreachable in the accepted production configuration (no proxy is
  configured and `trust_env=False` disables ambient proxies); the proof exercised it
  through an explicitly injected proxy client.  A forward-proxy (http origin) failure to
  reach the proxy surfaces as `connect_error`, not `proxy_error` (recorded observation);
* the executed harness and raw per-case evidence live only in the OS temp area and are
  not committed.

## 11. Budget

0 real provider/model inference calls; 0 real external network requests; 0 OpenCode
processes started or restarted; no runtime/test/dependency/version change.

## 12. Candidate conclusion

**G0.3 = CANDIDATE FAIL — TRANSPORT NON-DELIVERY SAFETY NOT ESTABLISHED.**

* All six accepted non-delivery classes (`connect_timeout`, `pool_timeout`,
  `connect_error`, `proxy_error`, `unsupported_protocol`, `local_protocol_error`) were
  independently shown **pre-send** on the installed stack: no request header or body
  byte reached the network stream, and their accepted classification is
  `submission_uncertain == False` (cases A–F).
* The uncertain classes stayed uncertain and fail-closed: `read_timeout`,
  `write_timeout`, `read_error`, `remote_protocol_error` and the unclassified
  `close_error` all reported `submission_uncertain=True` with `retry_safe=False`
  (cases G, H, I, K, L); HTTP rejection and success were never treated as non-delivery
  (cases M, N).
* The candidate **FAIL** is triggered solely by case **G0.3-J**: the precommitted
  `write_error` trigger produced `remote_protocol_error` at the accepted transport
  boundary (httpcore suppresses request-send `WriteError`), so the case did not lie in
  its precommitted allowed set.  No non-delivery safety property was violated, the
  affected class is an *uncertain* class, and P5 evidence is informational-only in the
  frozen design — but per the precommitted standard the candidate result is **FAIL**,
  and the affected case/class is named here rather than silently dropped.

Unchanged alongside it: `G0.1 / P7 = PASS` and `G0.2 = PASS` (authoritative, independently
approved); `G0.4`, `G0.5`, `G1`, `G2` = **NOT RUN**; overall platform proof gate =
**PARTIALLY EXECUTED / NOT COMPLETE** (not passed, not complete); mandatory-core
implementation = **NOT AUTHORIZED**; `adopt_completed_turn` = **DISABLED**.  This is a
candidate result only and is not self-approved.
