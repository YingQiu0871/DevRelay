# DevRelay v0.3-E — G0.3 / P5 transport classification: precommitted proof oracle (immutable pre-run manifest)

This file is the **immutable pre-run proof manifest** for the separately authorized
**G0.3 / P5** platform proof (transport failure classes vs non-delivery).  It was
committed **before any semantic G0.3 probe was executed**, it is not modified after
that commit, and its commit SHA and file SHA-256 are recorded in
`V03E_G0_3_TRANSPORT_PROOF.md`.

## 1. Identity of this manifest

| Item | Value |
| --- | --- |
| Repository HEAD at precommit | `efa2ca32a2f979cf88860c222e411181b451956b` |
| Branch | `v0.3-e-recovery-reconciliation` |
| Package version / public tags | `0.1.0` / `v0.1.0` only; no upstream |
| Frozen semantic design candidate | `9f4a01804b9affe8938a272553df345b5a60aeed` |
| Prior authoritative proof state | `G0.1 / P7 = PASS`; `G0.2 = PASS` |
| Gate steps not run | `G0.3 = NOT RUN` (this manifest opens it), `G0.4`, `G0.5`, `G1`, `G2` = NOT RUN |
| v0.3-E status | DESIGN FROZEN / NOT IMPLEMENTED / NOT ACCEPTED / UNRELEASED |
| mandatory-core implementation | **NOT AUTHORIZED** |
| `adopt_completed_turn` | **DISABLED** |
| Installed HTTP stack (proof target) | **httpx 0.28.1**, **httpcore 1.0.9**, h11 0.16.0, Python 3.14 |
| Provider / model / network budget | **0** inference calls, **0** real external network requests, **0** OpenCode processes |

## 2. Purpose and frozen authority boundary

G0.3 proves or falsifies the accepted v0.3-A transport / non-delivery classification
that frozen v0.3-E **P5** relies on.  The narrow question is: *which accepted
transport failure classes can be treated, on the installed accepted HTTP stack, as
evidence that the model-turn submission was definitely NOT delivered?*

Frozen boundary (`V03E_SPEC.md` §15, §19 row E, §28 P5; `V03E_ACCEPTANCE.md` E36):

* only accepted v0.3-A **connect / pre-submission** classes may count as non-delivery
  evidence;
* "HTTP client raised" is **not** by itself proof of non-delivery;
* transport classification is **informational only** and never changes orchestration
  state, never refunds a consumed slot, never grants retry authority;
* v0.3-E contains **no retry protocol**; `mark_unrecoverable` remains the mandatory
  fail-closed resolution;
* P5 evidence must never authorize retry, resubmission, budget refund, automatic
  resume, `READY_*` restoration, adoption or any provider/model call.

## 3. Accepted source classification (derived from the repository before probes)

Source of truth: `src/devrelay/opencode/transport.py::transport_failure`
(lines ~150-193), with the bridge paths in `src/devrelay/opencode/bridge.py` and the
MCP-level `retry_safe` derivation in `src/devrelay/mcp/tools.py::_retry_safe`.

| Accepted `error_type` | Underlying exception | Accepted `submission_uncertain` | Accepted `state` |
| --- | --- | --- | --- |
| `connect_timeout` | `httpx.ConnectTimeout` | `False` | `TIMED_OUT` |
| `pool_timeout` | `httpx.PoolTimeout` | `False` | `TIMED_OUT` |
| `connect_error` | `httpx.ConnectError` | `False` | `PROVIDER_UNAVAILABLE` |
| `proxy_error` | `httpx.ProxyError` | `False` | `PROVIDER_UNAVAILABLE` |
| `unsupported_protocol` | `httpx.UnsupportedProtocol` | `False` | `PROVIDER_UNAVAILABLE` |
| `local_protocol_error` | `httpx.LocalProtocolError` | `False` | `PROVIDER_UNAVAILABLE` |
| `read_timeout` | `httpx.ReadTimeout` | `True` | `TIMED_OUT` |
| `write_timeout` | `httpx.WriteTimeout` | `True` | `TIMED_OUT` |
| `read_error`, `write_error`, `remote_protocol_error`, `close_error`, **any other** transport failure | the exception's snake-case class name | `True` (fail-closed default) | `PROVIDER_UNAVAILABLE` |
| `http_status` (HTTP rejection) | a non-2xx HTTP response | `False` (no transport uncertainty) | `PROVIDER_UNAVAILABLE` |
| `""` (success) | 2xx JSON response | `False` | `COMPLETED` |

Also derived from source: `transport.py` catches non-transport `httpx.HTTPError` and
`OSError` as `submission_uncertain=True`; `bridge.py::send_prompt` sets
`submission_attempted=True` after the POST returns, routes uncertain POSTs through
`_uncertain_submission` (one bounded follow-up read, never a second POST,
`reply_pending=True`), and `tools.py::_retry_safe` returns `True` only when no POST was
attempted, or when a POST produced no HTTP status at all with no uncertainty and no
pending reply.

**Pre-probe comparison with the expected historical model**: identical to the expected
list (connect/pool timeout, connect error, proxy error, unsupported protocol, local
protocol error = non-delivery candidates; read/write timeout, read/write error, remote
protocol error and anything unclassified = uncertain).  No `CLASSIFICATION_MISMATCH`
was found in the accepted classifier before probes.  The proof's remaining question is
therefore the **stack-phase** question, not the classifier-name question.

## 4. Verdict classes (precommitted)

* **PROVEN_NON_DELIVERY** — the accepted stack/source semantics **and** the
  deterministic local probe establish that the submission request's bytes could not
  have been sent for that failure class (the request never reached the submission-send
  boundary; the prompt body was never handed to the network stream).
* **SUBMISSION_UNCERTAIN** — the failure can occur after submission may have begun or
  after bytes may have left the process; non-delivery is therefore **not** proven.
* **UNPROVEN_CLASSIFICATION** — the accepted source labels the class as non-delivery,
  but this proof cannot establish the necessary pre-send property on the installed
  stack.
* **CLASSIFICATION_MISMATCH** — the accepted runtime/source classification differs from
  this precommitted expected classifier.
* **NOT_A_NON_DELIVERY_CLASS** — the observed outcome is not a transport non-delivery
  classification at all (HTTP rejection, success control); it must never be promoted to
  non-delivery evidence, retry authority or a budget refund.

Required evidence level for PROVEN_NON_DELIVERY: **both** (1) accepted classifier plus
installed httpx/httpcore call path show the exception belongs to a phase before request
submission can occur, **and** (2) a controlled offline probe instruments the transport
boundary and shows the failure occurs before the request body/submission send boundary.
Exception names alone and documentation prose alone are never sufficient.

## 5. Instrumentation (precommitted hooks; real installed protocol only)

The probe drives the **real accepted path** (DevRelay transport/bridge → real
`httpx.Client` → real `httpx.HTTPTransport` → real `httpcore.ConnectionPool`/`HTTPProxy`
→ real h11) with a **scripted in-process `httpcore.NetworkBackend`/`NetworkStream`**
that never touches the network.  No hook name is invented: the instrumentation uses the
installed `httpcore.NetworkStream` protocol methods (`write`, `read`, `close`) and the
`httpcore.NetworkBackend` methods (`connect_tcp`, `connect_unix_socket`, `sleep`), and
the exceptions raised are the ones the real installed backend raises at those same
phases (`httpcore.ConnectError` / `ConnectTimeout` from the connect call;
`ReadTimeout` / `WriteTimeout` / `ReadError` / `WriteError` from the stream I/O calls —
the real `httpcore._backends.sync` maps its socket errors to exactly these classes
inside those methods).

Recorded per case:

* `connection_acquired` — whether the target request's connect returned a stream;
* `request_headers_send_started` — whether a request-header block of the target method
  (`POST `) was handed to `NetworkStream.write`;
* `request_body_send_started` — whether a non-header write for the target request was
  handed to `NetworkStream.write`;
* `request_body_bytes_observed` — whether the case-unique prompt marker bytes appeared
  in any `NetworkStream.write` buffer (the prompt body is the submission payload);
* `proxy_connect_bytes_observed` — whether `CONNECT ` bytes were written (proxy
  flavours only; recorded separately because they are not origin request bytes);
* request inventory (method + path per request observed at the stream boundary) and the
  POST count for the DevRelay-level probe (exactly-one-submission / no-retry evidence).

Pre-send classes must additionally satisfy: `request_headers_send_started == False`
and `request_body_bytes_observed == False` for the target request.

## 6. Fixed case matrix and precommitted expected results (one execution per case)

| Case | Class / accepted `error_type` | Precommitted trigger | Precommitted expected verdict |
| --- | --- | --- | --- |
| G0.3-A | `connect_timeout` | connect call raises the accept-phase timeout before any stream exists | **PROVEN_NON_DELIVERY** |
| G0.3-B | `pool_timeout` | the single pooled connection is held by another request; the target submission never acquires a connection | **PROVEN_NON_DELIVERY** |
| G0.3-C | `connect_error` | connect call raises the accept-phase connection error | **PROVEN_NON_DELIVERY** |
| G0.3-D | `proxy_error` | HTTP proxy configured: (flavour 1) connect to the proxy fails; (flavour 2) the proxy rejects the CONNECT tunnel | **PROVEN_NON_DELIVERY** for origin request bytes (recorded proxy nuance) |
| G0.3-E | `unsupported_protocol` | a non-http(s) scheme is rejected by the pool before any connect | **PROVEN_NON_DELIVERY** |
| G0.3-F | `local_protocol_error` | an accepted-configuration illegal header value (configured bearer token) is rejected while the request event is constructed, before any write | **PROVEN_NON_DELIVERY** for the reachable trigger, with the class-scope limitation recorded |
| G0.3-G | `read_timeout` | request fully written, then the read phase times out | **SUBMISSION_UNCERTAIN** |
| G0.3-H | `write_timeout` | request headers written, then the body write times out | **SUBMISSION_UNCERTAIN** |
| G0.3-I | `read_error` | request fully written, then the read phase raises the I/O error | **SUBMISSION_UNCERTAIN** |
| G0.3-J | `write_error` | request headers written, then the body write raises the I/O error | **SUBMISSION_UNCERTAIN** |
| G0.3-K | `remote_protocol_error` | request fully written, then the peer's bytes violate the protocol | **SUBMISSION_UNCERTAIN** |
| G0.3-L | unclassified transport failure (a concrete installed `httpx.TransportError` the accepted safe set does not name: `CloseError`), raised through the accepted classifier as a constructed classifier probe (no phase claim) | **SUBMISSION_UNCERTAIN** (fail-closed default); never PROVEN_NON_DELIVERY |
| G0.3-M | HTTP rejection (deterministic non-2xx response, no real network) | **NOT_A_NON_DELIVERY_CLASS**; the request was submitted sufficiently to receive a status |
| G0.3-N | success control (deterministic valid 2xx JSON response) | **NOT_A_NON_DELIVERY_CLASS** (ordinary completion) |

Precommitted consistency relations to be checked and recorded:

* PROVEN_NON_DELIVERY ⇒ `submission_uncertain == False` (the reverse is **not**
  sufficient proof — case M demonstrates the reverse);
* SUBMISSION_UNCERTAIN ⇒ never `retry_safe == True` on the exposed surface;
* exactly one submission POST attempt per DevRelay-level case; zero automatic POST
  retries; no hidden fallback; an uncertain classification never causes another POST.

## 7. Fixed no-probe-shopping rule (precommitted)

A–N are the complete planned semantic matrix; **one semantic execution per case**.  A
re-run is permitted only if a mechanical harness defect prevents the case from reaching
the precommitted assertion point; such attempts are recorded separately and excluded.
If a case reaches its semantic assertion and returns an unexpected result, **that
result counts**: the class definition, the expected result and the send-boundary hook
location are not changed, no substitute exception from the same family is used, and no
case is repeated until a safe-looking result appears.  If a class relied upon as
non-delivery evidence cannot be proven, that class is named in the evidence and the
candidate result is **FAIL** (no intermediate gate status exists in the frozen
contract, and none is invented here).

## 8. Non-authority rule (precommitted)

Even a fully proven pre-send class has **no orchestration execution authority** in
v0.3-E.  `retry_safe` (where the accepted MCP surface exposes it) may be reported as
evidence only: it must not cause a retry, a resubmission, an automatic follow-up model
turn, a budget refund, a state transition or a slot restoration.  The mandatory core's
fail-closed resolution remains `mark_unrecoverable`, and adoption remains disabled.

## 9. Budget and offline constraints

Disposable local proof state only: installed source inspection, an in-process scripted
`httpcore` network backend, the accepted deterministic stub payloads, direct classifier
invocation and monkeypatching inside the disposable harness.  No DNS, no TCP, no
localhost server, no OpenCode, no provider API, no model inference, no Internet access,
no repository writes (except this manifest and the documented docs/evidence files).

## 10. Immutability

After the pre-run commit that introduces this file, it is **not modified**.  A
correction would require a new authorization and a new manifest with its own pre-run
commit; the evidence document records this file's commit SHA and SHA-256 so a reviewer
can verify that the oracle existed before the execution.
