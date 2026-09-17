# DevRelay v0.3-E — recovery and reconciliation (design)

Status: **DESIGN / NOT IMPLEMENTED / NOT ACCEPTED / UNRELEASED** — this document
freezes the v0.3-E *contract* for independent review; **no recovery code exists**,
no runtime source or test was modified by this design round, no real provider/model
call was made, and v0.3-E implementation must not start until the design is
independently reviewed and the open platform proofs in §15 are resolved.

* Branch: `v0.3-e-recovery-reconciliation` (design only).
* Parent: `56e7842a414777d20a3882cad641da383964bab3` (v0.3-D acceptance closeout
  follow-up).  Accepted v0.3-D runtime candidate:
  `8b70610a5cdda600ef57cf8378c4f69cd33d5be4`.
* Package version stays `0.1.0`; the only public tag is `v0.1.0`; nothing is
  pushed, merged, tagged or released.

## 1. Purpose and boundary

v0.3-D fails closed: when DevRelay cannot *know* what happened to a model-bearing
turn, it materializes the interruption and blocks the run
(`blocked_reason=turn_interrupted`) or blocks on a failed/uncertain submission.
That is safe, and it is deliberately terminal — an interrupted v0.3-D run is
resolved by a human, not by DevRelay.

v0.3-E exists to define **safe** behaviour when the outcome of exactly one
already-issued orchestration model turn can be determined *after the fact* from
evidence that still exists, without ever issuing a second provider call on a
guess.  Its scope is: read evidence, decide what already happened, and — only when
that is provable — write the already-established truth into durable run state so
the Planner can continue legally.

It is **not** a retry engine, not a scheduler, not a background daemon, and not a
repair tool for arbitrary corruption.

## 2. Inventory: the recovery-related surface that exists today

Read-only inventory taken on the design parent `56e7842` (accepted v0.3-D runtime
`8b70610`).  Nothing below was modified by this round.

**Orchestration (v0.3-D, accepted)**

* `src/devrelay/orchestration/models.py` — `RunState`
  (`READY_IMPLEMENTER`, `READY_REVIEWER`, `AWAITING_DECISION`, `COMPLETED`,
  `STOPPED`, `BLOCKED`, `LIMIT_REACHED`; the last four are terminal);
  `TurnRecord` carries the sanitized per-turn evidence
  (`prompt_sha256`, `prompt_chars`, `resolved_model`, `resolved_agent`,
  `route_source`, `operation_state`, `submission_attempted`,
  `submission_status`, `submission_uncertain`, `reply_pending`, `retry_safe`,
  `call_ids`, `assistant_message_ids`, `outcome`, `blocked_reason`);
  `OrchestrationRun.in_flight_turn` is the live durable intent;
  `summary()["legal_next_actions"]` is empty while an intent is live.
* `src/devrelay/orchestration/service.py` — `_run_role` persists the in-flight
  intent **before** the role call (`store.save`), captures the accepted role
  result's evidence afterwards, and finalizes the turn;
  `_materialize_interrupted_turn` (called from `_load_for_action`) turns a
  persisted live intent into a finished `blocked`/`turn_interrupted` record and
  blocks the run; `_block(reason=...)` handles route invalidation and ownership
  loss; `_require_route_unchanged` compares the live route against the immutable
  snapshot; `_verify_session` re-checks workspace ownership.
* `src/devrelay/orchestration/state_machine.py` — `require_not_terminal`,
  `require_no_in_flight_turn` (message: *"recovery is out of scope for v0.3-D"*),
  `require_state`, `require_cycle_budget`, `after_role_turn`, `after_decision`.
* `src/devrelay/orchestration/store.py` + `invariants.py` — strict single-writer
  store; load/save re-derive every structural and reachability invariant;
  corruption fails closed and is never repaired.
* `src/devrelay/orchestration/models.py` — `model_turns_used` means **consumed
  orchestration model-turn budget slots**, not confirmed POSTs; nothing refunds a
  slot.

**OpenCode bridge (accepted v0.3-A)**

* `src/devrelay/opencode/bridge.py` — operations: `health`, `list_sessions`,
  `get_session`, `read_messages` (explicit cursor, read-only),
  `send_prompt` (exactly one submission POST), `wait_idle` (bounded session-status
  polling), `interrupt` (an accepted abort request is **not** a verified terminal
  state).  `_request` allocates a durable call id and writes the ledger record
  **before the request leaves the machine**, then settles it with the outcome.
* `src/devrelay/opencode/accounting.py` — `allocate_call_id` (durable, monotonic
  `OC-NNNN`, never reused; a corrupt sequence fails closed), `begin` (immutable
  create-new record), `finish` (settle in place), `read_records` (read every
  persisted record).
* `src/devrelay/opencode/models.py` — `OpenCodeCallRecord` (durable per-request
  evidence: `call_id`, `operation`, `state` ∈ `ISSUED|COMPLETED|TIMED_OUT|
  PROVIDER_UNAVAILABLE|MALFORMED_RESPONSE`, `method`, `path`, `session_id`,
  `issued`, `external_request_count`, `http_status`, `error_type`, `started_at`,
  `completed_at`, `duration_ms`, `submission_uncertain`, `response_media_type`,
  `prompt_sha256`, `prompt_chars`, `agent`, `model` — **never** prompt text,
  transcript or credential); `OpenCodeOperationResult` (in-memory result of one
  operation, including `submission_attempted`, `submission_status`,
  `submission_uncertain`, `submission_contract`, `reply_pending`,
  `reply_boundary`, `follow_up_state`, `call_ids`, `messages`);
  `OpenCodeMessage` (`message_id`, `role`, `created_at`, `parts[].text` — the
  session history exposes both user and assistant text); `prompt_digest`
  (unsalted SHA-256 of the exact prompt: an identifier, not a secrecy mechanism).
* Existing read surfaces over the same evidence: `opencode_read_messages`,
  `opencode_get_session`, `opencode_wait_idle`, `opencode_calls` (read-only MCP
  tools; the ledger projection is bounded and reports corruption instead of
  hiding it).

**MCP surface (accepted v0.3-B / v0.3-D)**

* 17 tools; orchestration tools `devrelay_start_run`, `devrelay_get_run`
  (read-only), `devrelay_run_implementer`, `devrelay_run_reviewer`,
  `devrelay_decide_run`.  One re-entrant execution lock **per tool surface**
  serializes every tool body; the shipped stdio server builds exactly one surface.

**Documents that already describe the gap**

* `docs/v0.3/V03D_SPEC.md` §6/§10 ("crash reconciliation … out of scope"),
  `docs/v0.3/V03D_ACCEPTANCE.md` (E2), `docs/BACKLOG.md` §5 (v0.3-E recovery,
  multi-surface/multi-process, read-only `get_run`).

**Not v0.3-E.**  `src/devrelay/pipeline/engine.py`
(`recover_pending_implementation`, `recover_pending_review`) and
`src/devrelay/providers/codex_runtime.py` (`reconcile_observed_files`) are
pre-existing **v0.2 Codex-pipeline** functions.  They are unrelated to
orchestration recovery, were not touched, and must not be reused or cited as
v0.3-E machinery.

## 3. Preserved v0.3-D invariants (all of them bind v0.3-E)

1. Reviewer prose has **zero** state-machine authority.
2. Only an explicit external planner decision leaves `AWAITING_DECISION`
   (`decision_history` source is always `external_planner`).
3. `1 <= max_cycles <= 3`; `model_turn_budget = 2 × max_cycles`; absolute ceiling
   six slots per run.
4. No hidden retry; no fallback model or route; no automatic
   implementer→reviewer sequencing; one explicit phase call causes at most one
   model submission.
5. Terminal runs never reopen (this document's §7 explains how v0.3-E keeps that
   true while still allowing a *provable* completion to be adopted).
6. Route snapshots are immutable historical identity; session/workspace ownership
   stays explicit; implementer and reviewer sessions stay distinct.
7. Persisted-state corruption fails closed and is never repaired; persisted types
   stay strict; reachability rules stay enforced on load and save.
8. No raw prompt, provider response, reasoning or credential is persisted.
9. Accounting semantics stay intact: a consumed slot is never refunded, and no
   restart creates budget.

Any recovery mechanism that weakens any of these is unacceptable, and the design
below is written so that a violation is a design bug, not a trade-off.

## 4. Recovery problem taxonomy

These are **distinct** outcomes with distinct evidence and distinct allowed
actions.  They must never collapse into one "retryable" bucket.

| # | Case | What is known | Evidence (durable → remote) | Model call allowed to resolve? |
| --- | --- | --- | --- | --- |
| A | **Pre-submission failure** | No durable intent exists, or submission provably never started | Run document (no intent / intent with no ledger call), ledger (no record for the intended operation), accepted guards | No |
| B | **Definitely not delivered** | The accepted v0.3-A taxonomy proves the request never reached the provider (connect-phase failure: `connect_error`, `connect_timeout`, `pool_timeout`) | Ledger record settled with that state, `submission_uncertain = false`, `submission_attempted` as reported | No |
| C | **Submission attempted, response known** | The normal completed turn | Turn record with `call_ids`, `assistant_message_ids`, `operation_state`, `submission_*` | No |
| D | **Submission uncertain** | The request may have reached OpenCode/provider; local evidence cannot prove either way (read/write timeout, mid-transfer failure, or a 2xx body that did not match the media/JSON contract) | Ledger record with `submission_uncertain = true` and/or `submission_contract` evidence; run intent | **Never automatically**; only §12/§13 proofs |
| E | **Reply pending** | Positive evidence that an accepted submission may still produce an observable reply (`reply_pending = true`, `reply_boundary` cursor) | Ledger record (2xx, JSON contract) plus the run intent; session history readable | No model call: resolution is a **read** (§11) |
| F | **Process crash with durable in-flight intent** | DevRelay died between intent persistence and turn finalization | Run document with live `in_flight_turn`; ledger record (ISSUED or settled) | No |
| G | **Remote completion / local persistence gap** | The provider really produced the reply, but DevRelay never recorded the finished turn | Ledger record settled `COMPLETED` matching the intent identity **and** a session-history match per §12 | No — adopting existing evidence is not a submission |
| H | **Contradictory or insufficient evidence** | Yes/no cannot be decided (two candidate matches, mismatch on identity, missing session, unreadable ledger, route/model mismatch) | Any combination above | No — **fail closed** |

## 5. Terms: reconcile, materialize, resume, retry

* **RECONCILE** — read existing durable/local/remote evidence and determine what
  already happened.  Read-only.  Never a model call.  Never mutates run state.
* **MATERIALIZE** — write an already-established fact into durable run state
  (for example: "this turn completed").  Mutating, explicit, idempotent, never a
  model call, allowed only when reconciliation proved the fact.
* **RESUME** — continue orchestration from a state that reconciliation produced
  legally.  Resume itself issues nothing: the next model call still requires an
  explicit planner phase action in the legal state.
* **RETRY** — issue another model submission.  v0.3-E does **not** do this
  implicitly, ever; §7 defines the only (explicit, planner-authorized,
  evidence-gated) form in which a *new attempt* could ever exist, and the design
  prefers not to have one at all.

Reconcile/resume must never be *implemented as* retry, and a timeout must never
become a free retry.

## 6. Recovery authority

* The provider/reviewer/model has **zero** recovery authority.  Model prose is
  never parsed, never a signal, never an input to a recovery decision.
* Recovery is driven by (a) deterministic evidence and (b) an explicit external
  planner action.  Both are required for any mutation: evidence establishes the
  fact, the planner authorizes the write.
* Recovery actions are **explicit tools** with strict arguments — not semantic
  parsing, not heuristics, not "best guess".
* The planner cannot authorize a fact into existence: a `resolve` call whose
  evidence cannot be re-verified at mutation time is refused.

## 7. State model

**Decision: add exactly one new run state, non-terminal and execution-frozen.**

v0.3-D's `BLOCKED` is terminal by accepted invariant, and "terminal runs never
reopen" is a preserved invariant (§3, invariant 5).  A provable remote completion therefore
cannot be adopted by moving a `BLOCKED` run forward — that would be a silent
reinterpretation of accepted history.  At the same time, leaving the run
recoverable-but-invisible inside `BLOCKED` would either weaken the invariant or
force v0.3-E to reopen terminal runs.

Proposal (to be reviewed and frozen; not implemented):

* new state **`RECOVERY_REQUIRED`** (spelled exactly; added to `RunState`);
* nature: **non-terminal**, **execution-frozen** — while a run is in this state
  *no* model-bearing action (`run_implementer`, `run_reviewer`), *no*
  `decide_run`, *no* `start_run` side effects on it, and *no* automatic anything
  is legal; `legal_next_actions` is exactly the recovery actions (plus read-only
  reads);
* entry conditions: (i) a live persisted `in_flight_turn` is materialized after a
  restart (v0.3-D would have produced `BLOCKED`/`turn_interrupted`); (ii) a turn
  ends with `submission_uncertain` or `reply_pending`; (iii) an interrupted turn's
  role/cycle evidence cannot be finalized into a role history entry;
* required metadata: `recovery_reason` (constrained vocabulary:
  `turn_interrupted`, `submission_uncertain`, `reply_pending`, `evidence_gap`,
  `evidence_conflict`) and a `recovery` block (§10);
* legal exits: (a) explicit `resolve` adopting a **proved** completed turn →
  the state that turn legally produces (implementer completed → `READY_REVIEWER`;
  reviewer completed → `AWAITING_DECISION`); (b) explicit `resolve` marking the
  run unrecoverable → `BLOCKED` with the same reason (still terminal);
  (c) nothing else — no exit to `READY_*` without a materialized completion;
* model-call allowance: **zero** in this state, for every action;
* restart semantics: after a restart the state is re-derived from the document
  (it is persisted), reconciliation is idempotent, and no restart performs work.

Alternatives considered and rejected:

* *keep `BLOCKED` only* — rejected: either the completion can never be adopted
  (v0.3-E would do nothing) or terminal runs would reopen (invariant violation).
* *a dedicated `RECONCILIATION_REQUIRED` + `RECOVERY_REQUIRED` pair* — rejected as
  state inflation: one state plus explicit recovery evidence covers both "needs
  evidence" and "evidence gathered"; the distinction lives in the `recovery`
  metadata, not in the state machine.
* *putting `submission_uncertain`/`reply_pending` into run state as new states* —
  rejected: they are **turn/reconciliation evidence**, not lifecycle states.  They
  stay in the turn audit (they already exist there) and are copied into the
  recovery metadata for the crashed turn only.

## 8. Exact call identity

What exists, and when (all facts verified against the accepted bridge code):

| Identifier | Before submission | During submission | After response | Durable? |
| --- | --- | --- | --- | --- |
| `run_id`, `role`, `cycle`, session id, route snapshot | yes (run document) | yes | yes | yes |
| prompt `prompt_sha256` + `prompt_chars` (intent) | yes | yes | yes | yes |
| DevRelay `call_id` (`OC-NNNN`, monotonic, never reused) | allocated and **written as an ISSUED ledger record before the request leaves the machine** | yes | yes (same id, settled) | yes |
| ledger settle fields (`state`, `http_status`, `external_request_count`, `submission_uncertain`, `response_media_type`, `completed_at`) | no (record is ISSUED) | ISSUED | yes | yes |
| `reply_boundary` cursor | no | in memory | in memory | **no** |
| assistant `message_id`(s) | no | no | in memory (run turn record only if the turn was finalized) | only via the run document |
| OpenCode-side operation/job id or idempotency key | **does not exist** in the accepted client path (the submission is a single synchronous `POST /session/{id}/message`; OpenCode assigns message ids server-side and DevRelay sends no client id) | — | — | — |

Design consequences (no invented facilities):

* The **durable pre-submission identity** of an attempt is
  `(run_id, role, cycle, session_id, model, agent, prompt_sha256, prompt_chars,
  call_id)` — the run intent provides the first eight, the ledger record the last
  plus the transport evidence.
* There is **no OpenCode idempotency key**; v0.3-E therefore cannot ask OpenCode
  "did *this* request complete?" by id.  It must match *evidence* (§12).
* A crash between the response and the finalized turn loses the assistant
  `message_id` from *local* memory; §12 defines how it can be re-derived from the
  session history without persisting prompt text.

## 9. Reconciliation sources

| Source | Authoritative for | Mode | Absence / failure meaning | Ambiguity meaning | Survives restart | Distinguishes "not submitted" from "submitted, unobserved"? |
| --- | --- | --- | --- | --- | --- | --- |
| DevRelay run document | state, cycle, counters, intent, decision history, route snapshot | read (strict validation) | no run / corrupt run → fail closed | contradictory fields → fail closed (existing invariants) | yes (filesystem) | It records *intent*, never delivery |
| DevRelay ledger (`OC-*` records) | that DevRelay issued exactly one request, its transport outcome class, and the prompt/session/model identity of that request | read-only (`opencode_calls`, `read_records`) | no record → no submission was issued by DevRelay | two matching records → fail closed | yes (filesystem) | Yes for the "no record ⇒ never issued" direction; for delivery it is evidence, not proof (see §13) |
| OpenCode session history (`read_messages`) | what the provider actually produced in that session: message ids, roles, timestamps, text of user/assistant messages | read-only (explicit cursor) | session missing / empty / unreadable → fail closed | more than one candidate match → fail closed | **PROOF REQUIRED** (P1/P2 in §15) | Yes, when the sent user message is present (its text hashes to the stored digest) |
| OpenCode session state (`get_session`, `wait_idle`) | whether the session is busy/idle right now | read-only; **not** a model call; never a wait-for-result | unknown state → do not act | busy with no matching message → stay frozen | session existence survives; *state* does not | Only "may still be running", never "definitely delivered" |
| Current role configuration | drift detection only | read-only | missing/invalid route → the run cannot legally proceed under that route | drift → fail closed for the run (existing v0.3-D rule) | yes | n/a — must never rewrite the snapshot |
| Accepted v0.3-A failure taxonomy | the *classification* of a transport outcome (definitely-not-delivered vs uncertain) | static (code/docs) | unknown class → treat as uncertain | conflicting classes → treat as uncertain | yes | Yes for connect-phase classes, by accepted evidence |

## 10. Run-document additions (proposal, not implemented)

New persisted fields on `OrchestrationRun` (all strict):

* `recovery_reason: str` — constrained vocabulary (§7); required non-empty when
  `state == RECOVERY_REQUIRED`, empty otherwise (mirroring the `blocked_reason`
  discipline).
* `recovery: RecoveryRecord | None` — the durable recovery record for the *one*
  in-flight/interrupted attempt (never a log):
  * `attempt` — the materialized sanitized turn identity (role, cycle,
    `prompt_sha256`, `prompt_chars`, `resolved_model`, `resolved_agent`,
    `route_source`, `started_at`, ledger `call_ids`);
  * `evidence` — the frozen evidence snapshot used by the last reconcile:
    run-intent digest, ledger `call_id` + state + `http_status` +
    `submission_uncertain` + `response_media_type`, remote match
    (`message_id`, `role`, `created_at`, matched-digest flag), and a *digest of
    the evidence set* (`evidence_sha256`) that the mutating `resolve` must
    re-derive;
  * `resolution` — `""` | `adopted_completed_turn` | `marked_unrecoverable`;
  * `resolved_at: str`.

`schema_version` becomes **2** for documents written by v0.3-E (policy in §14).
No safety-critical field gets a silent default: a document claiming
`RECOVERY_REQUIRED` without a reason or without a recovery record is corrupt.

## 11. Crash-window matrix

W0–W6 as required, with the accepted code's actual ordering (intent → ledger
ISSUED → request → response → turn finalization):

| Window | Durable disk evidence | Possible remote evidence | Slot consumed? | `submission_uncertain`? | `reply_pending`? | Allowed recovery action | Forbidden | Final safe state |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **W0** before durable intent | run document unchanged (no intent, counters unchanged) | none | no | n/a | n/a | none needed (the phase was never attempted) | any recovery | unchanged state |
| **W1** after intent, before HTTP submission | live `in_flight_turn`; no ledger record for that operation | none | yes | no | no | materialize `RECOVERY_REQUIRED` with reason `turn_interrupted`; planner may resolve as unrecoverable → `BLOCKED` | any automatic submission; any refund | `RECOVERY_REQUIRED` (or `BLOCKED` by explicit resolve) |
| **W2** during connection establishment | live intent; ledger record settled with a connect-phase state | none (connect never reached the provider) | yes | no (`submission_uncertain = false`) | no | as W1, with evidence "definitely not delivered" (case B) recorded | auto-resubmit | `RECOVERY_REQUIRED`; never a free retry |
| **W3** request may have been delivered, before response headers | live intent; ledger record ISSUED (never settled) or settled mid-transfer | unknown: the provider may have produced a reply | yes | yes | unknown | reconcile only; if the session history yields exactly one matching completion → §12 adoption; else stay frozen | any submission; guessing from session busy/idle | `RECOVERY_REQUIRED` (adopted only on proof) |
| **W4** response received, assistant identity not yet captured | live intent; ledger record settled `COMPLETED` (2xx, JSON contract) | the assistant message exists in the session | yes | no | no | reconcile via §12 (ledger + session-history digest match) | treating "ledger COMPLETED" alone as a finished turn | adopted turn or `RECOVERY_REQUIRED` |
| **W5** assistant result known, completed turn not persisted | live intent; ledger settled `COMPLETED` | assistant message exists | yes | no | no | §12 adoption (strongest case) | issuing any provider call | legal post-turn state |
| **W6** completed turn persisted, response not returned to the MCP client | no intent; the finished turn is in the run document | n/a | yes | recorded as false | recorded as false | none (state is already the truth); the client may simply re-read | re-running the phase | unchanged (truthful) state |

Explicit non-claims: "HTTP client raised" ≠ "provider did not receive"; a session
that is `busy` ≠ "the reply will arrive"; a ledger `COMPLETED` ≠ "the run's turn
completed" (adoption needs the §12 match).

## 12. Reconciled completion (the strongest safe case)

Adoption of an already-completed turn is allowed only when **all** of the
following are re-derived at mutation time (not trusted from a previous dry run):

1. the run is in `RECOVERY_REQUIRED` with exactly one materialized attempt;
2. the ledger contains **exactly one** record for the intended operation whose
   `operation` is the submission, `session_id` equals the run's session for that
   role, `model`/`agent` equal the immutable route snapshot entry, and
   `prompt_sha256`/`prompt_chars` equal the intent's;
3. that record is settled `COMPLETED`, `http_status` 2xx, JSON media type,
   `submission_uncertain = false`;
4. the OpenCode session history (read-only, bounded, explicit cursor) contains
   **exactly one** user message whose `parts[].text` hashes to the stored
   `prompt_sha256`, and **exactly one** assistant message that directly follows it
   in that session (the "corresponding response");
5. workspace ownership, session ownership and role/session distinctness re-verify
   (the same checks v0.3-D performs);
6. the cycle and role of the attempt still match the run's current cycle and the
   phase the state expects;
7. the run's route snapshot is unchanged (drift → fail closed, §12.1);
8. no second candidate matches (two sessions, two messages, two ledger records →
   fail closed).

Only then may `devrelay_resolve_recovery` write the already-completed turn
(objective C semantics: `outcome=completed`, `call_ids` from the ledger,
`assistant_message_ids` from the matched message) and move the run to the state
that turn legally produces — **without any provider call**, with the consumed slot
unchanged and with `decision_history` untouched.

**What is not proven by the above:** that the provider's stored user text is
byte-identical to what DevRelay sent (P2 in §15).  If it is not, step 4 cannot
match and the run stays frozen — which is the required failure mode, not a bug.

## 12.1 Route drift during recovery

The captured route snapshot remains the authoritative historical identity.
Current configuration is read **only** to detect drift.  If the current route for
the role differs from the snapshot (or is unresolvable), reconciliation cannot
adopt a completion for a *different* route: the attempt is recorded as
`evidence_gap`/`evidence_conflict` and the run stays `RECOVERY_REQUIRED` until the
planner resolves it as unrecoverable (`BLOCKED`).  Remote evidence that does not
match the snapshot model/agent is never adopted.

## 13. Reconciled non-delivery

Only the accepted v0.3-A taxonomy's connect-phase classes (`connect_error`,
`connect_timeout`, `pool_timeout`) are treated as evidence that the request never
reached the provider; every other failure class (read/write timeout, mid-transfer
error, unusable 2xx body, unknown) is *uncertain* by definition.

For a proved non-delivery:

* the consumed slot **stays consumed** (no refund, ever);
* the run does **not** silently return to `READY_*`; it becomes
  `RECOVERY_REQUIRED` with reason `submission_uncertain`/`turn_interrupted` and
  remains execution-frozen;
* the planner's options are exactly: (a) resolve as unrecoverable → `BLOCKED`
  (terminal, human decides what to do next), or (b) — **only if a future,
  separately reviewed retry protocol exists** — authorize a *new* attempt; the
  design does **not** include that protocol, and without it a new attempt requires
  a new run;
* no design path creates a same-cycle or new-cycle retry, and no path rewrites the
  materialized attempt's history (the attempt stays in the role history exactly
  once).

## 14. Pending replies

If `reply_pending` is recorded (or an ISSUED ledger record exists without a
settlement and the session is still busy), the run is `RECOVERY_REQUIRED` and
execution-frozen.  Resolution is a **read**, never a model call:

* `devrelay_reconcile_run` may read the session history (bounded page window, the
  accepted `read_messages` cursor semantics) and/or the session state;
* **no automatic waiting, no unbounded polling, no daemon**: each reconcile call
  is one bounded, explicit, read-only evidence pass (at most a fixed small number
  of read requests, defined at implementation time);
* when the history finally shows the matching completion, the same §12 adoption
  applies; when it shows nothing and the session is idle, the evidence remains
  insufficient and the run stays frozen (or the planner marks it unrecoverable);
* `wait_idle` is session-level only and must never be used as "the reply arrived";
* reconciliation reads are not model calls and must never be counted as slots.

## 15. Open platform proofs (DESIGN BLOCKERS / PROOF REQUIRED)

These cannot be settled offline in a design-only round (a real platform probe is
not authorized here), and the corresponding policies must not be implemented
until they are:

* **P1 — history durability.** Does an OpenCode session's message history survive
  a *server* restart (and a client restart) with the same message ids and text?
  The accepted client can read history after a client restart, but server-side
  persistence of the exact messages has not been proven.
* **P2 — verbatim user text.** Is the user message stored byte-identical to what
  was sent, so that `sha256(stored text)` equals the stored `prompt_sha256`?
  Known normalization exists elsewhere in the platform (the accepted v0.3-A
  reasoning-part normalization), so this must be proven before §12 step 4 can be
  relied on.
* **P3 — uniqueness/ordering.** Can two identical prompts in one session be
  disambiguated deterministically (time window + exclusivity)?  The design
  requires "exactly one candidate" and fails closed otherwise, but whether a
  bounded window is always sufficient is unproven.
* **P4 — pending-operation visibility.** Does OpenCode expose any per-operation
  pending/queued handle for a submission (beyond session busy/idle) that a
  restarted client could query without issuing a model call?  The accepted client
  path suggests "no", but this must be confirmed.
* **P5 — failure-class semantics.** Are the accepted taxonomy's connect-phase
  classes *always* pre-delivery on this platform and transport stack (including
  proxies/retries inside the client), i.e. is "definitely not delivered" a proof
  and not just a classification?
* **P6 — session identity strength.** Is a session id + workspace `directory`
  check sufficient to exclude a deleted/recreated or copied session, and what
  happens to reconciliation when a session disappeared entirely?
* **P7 — ledger settle atomicity under kill.** The ledger writes ISSUED before
  the request and settles afterwards; is a *partially* written settle record
  possible under a hard kill, and how must reconciliation treat it?  (The design
  treats an unreadable/unsettled record as insufficient evidence and fails
  closed either way.)

Until P1–P4 are proven, the **adoption** path (§12) and the **pending** policy
(§14) are design-only; until P5 is proven, the **non-delivery** policy (§13) rests
on accepted evidence rather than a platform proof.  Everything else in this
document — the frozen fail-closed core — is provable offline today.

## 16. Dedicated states: entry/exit summary

| State | Entry | Legal exits | Terminal? | Planner actions | Model calls | Restart semantics |
| --- | --- | --- | --- | --- | --- | --- |
| existing `READY_IMPLEMENTER` / `READY_REVIEWER` / `AWAITING_DECISION` | unchanged (v0.3-D) | unchanged | no | unchanged | unchanged | unchanged |
| existing `COMPLETED` / `STOPPED` / `LIMIT_REACHED` / `BLOCKED` | unchanged | unchanged (never reopen) | yes | read-only; recovery tools refuse locally | none | unchanged |
| **`RECOVERY_REQUIRED`** (new in v0.3-E) | §7 entry conditions | (a) `resolve` adopting a proved completed turn → `READY_REVIEWER` / `AWAITING_DECISION`; (b) `resolve` as unrecoverable → `BLOCKED` | **no** (but execution-frozen) | `devrelay_reconcile_run` (read-only), `devrelay_resolve_recovery` (mutating), `devrelay_get_run` | **none, ever** | persisted; reconciliation idempotent; no work on restart |

## 17. Explicit recovery tools (minimum surface)

Exactly **two** new tools (preferred over three; the read/write split is the
safety boundary):

1. `devrelay_reconcile_run(run_id)` — **read-only**.  Legal for any
   non-terminal run and for `RECOVERY_REQUIRED`; refuses locally for terminal
   states (no model call, no mutation).  Returns the structured reconciliation
   report: the materialized attempt identity, the ledger evidence, the remote
   match candidates, the proof checklist of §12 with per-item pass/fail, and the
   blockers (P1–P6).  **No durable mutation, no model call, idempotent by
   construction, restart-safe.**  It never performs a phase turn.
2. `devrelay_resolve_recovery(run_id, resolution)` — **mutating**, the only
   recovery write.  `resolution ∈ {adopt_completed_turn, mark_unrecoverable}`.
   Legal only in `RECOVERY_REQUIRED`; refuses for terminal states and for any
   other state.  It re-derives **all** §12 evidence at call time (a previous
   reconcile report is not a token), performs no provider call, appends the
   already-completed turn exactly once (idempotent per `evidence_sha256`), and
   moves the run through the single legal exit.  Errors use the accepted envelope
   with a stable code (proposed `orchestration_recovery_invalid` /
   `orchestration_recovery_unproven`) and the run state visible.

Rejected alternatives: a mutating `get_run` (would break v0.3-D's read-only
guarantee), a combined reconcile+resolve tool (mixes proof and write), an
`auto_recover` flag, a background recovery runner, and any tool that performs an
implementer/reviewer phase.  `devrelay_get_run` stays **read-only** (v0.3-D's
decision is preserved: reads never mutate).

## 18. Terminal runs

`COMPLETED`, `STOPPED`, `LIMIT_REACHED` and `BLOCKED` never enter recovery: they
are terminal, they never reopen, and a recovery tool aimed at them fails locally
(`orchestration_invalid_transition`) with zero model calls and zero mutation.  A
terminal document that carries a live in-flight intent remains **corrupt**
(v0.3-D rule) and is never repaired.

## 19. Workspace, session and route identity during recovery

Re-verified before any adoption: workspace binding (the run's workspace is this
store's workspace), implementer/reviewer session ownership (`workspace_match`),
role/session distinctness, and the immutable route snapshot.  A run document
copied into another workspace is **not recoverable** (it is corrupt there, as in
v0.3-D).  If a session has disappeared, or the session belongs to another
workspace, reconciliation stops with `evidence_gap` and the run stays frozen
(`resolve` may only mark it unrecoverable) — never "adopt into another session".

## 20. Budget and accounting policy

`model_turns_used` keeps its accepted meaning (**consumed slots**, not confirmed
POSTs) and no recovery path may reset, decrement, refund or recompute it:

| Case | Slot | Run state | Can a model call happen afterwards? |
| --- | --- | --- | --- |
| pre-intent failure (W0) | not consumed | unchanged | yes, by a new explicit phase call in the legal state |
| intent persisted, nothing sent (W1) | consumed | `RECOVERY_REQUIRED` | no |
| intent + connect-phase failure (W2) | consumed | `RECOVERY_REQUIRED` | no (no retry protocol) |
| submission attempted (W3/W4) | consumed | `RECOVERY_REQUIRED` → adopted or blocked | only via the legal post-adoption state |
| submission uncertain | consumed | `RECOVERY_REQUIRED` | no |
| reply pending | consumed | `RECOVERY_REQUIRED` (reads only) | no |
| reconciled completion adopted | consumed exactly once | legal post-turn state | the normal next phase (new slot) |
| reconciled failure / non-delivery | consumed | `RECOVERY_REQUIRED` → `BLOCKED` | no |
| unrecoverable ambiguity | consumed | `BLOCKED` | no |

Restart never creates budget: the counters come from the document and the
invariants re-derive them.

## 21. Concurrency

Recovery actions run through the accepted per-`McpToolSurface` execution lock,
exactly like `run_implementer`, `run_reviewer` and `decide_run`, so no recovery
read/write can interleave with a phase or a decision within one surface.  The
stdin/session-level "one surface" scope is unchanged: **multi-surface or
multi-process coordination on one workspace remains unsupported** unless a later
stage explicitly expands that scope, and no part of v0.3-E may claim a
process-wide lock.  A crash during recovery leaves the document in either the
pre-recovery or the post-recovery shape (single atomic write), never in between.

## 22. Privacy

Reconciliation must never require persisting raw prompt text, raw model responses,
reasoning, credentials or authorization headers.  Matching uses digests, ids,
roles, timestamps and metadata only:

* the run document keeps digests/lengths/ids (already true);
* the reconciliation record keeps a *digest* of the evidence set, ledger ids and
  matched message ids — never message text;
* reading the session history transiently exposes message text **in memory** (and
  it is already exposed to the Planner by the accepted read-only tools); the
  design performs digest comparison in memory, redacts as the accepted bridge
  does, and persists nothing derived from the text except the comparison result.

## 23. Persisted schema and versioning

* `schema_version` becomes **2** for documents written by v0.3-E.
* New strict fields: `recovery_reason` (constrained vocabulary) and `recovery`
  (`RecoveryRecord | None`) as defined in §10, plus the new `RunState` member.
* **No silent defaults for safety-critical fields**: a v2 document in
  `RECOVERY_REQUIRED` without `recovery_reason` or without a `recovery` record is
  corrupt; unknown/extra fields stay forbidden.
* **Migration policy**: v0.3-E **does not migrate** v1 documents.  A v1 document
  keeps loading under its own rules and behaves exactly as accepted in v0.3-D
  (including `BLOCKED` staying terminal, and a live in-flight intent
  materializing to `BLOCKED`/`turn_interrupted`).  A v1 run cannot be "upgraded
  into" recovery; if the planner wants recovery, that requires a new run
  (v0.3-E writes v2 documents only).  This avoids reinterpreting accepted history.
* Corrupt/unknown-version documents fail closed as `orchestration_state_corrupt`;
  the reachability invariants extend to the new fields (a `RECOVERY_REQUIRED`
  document must be reachable: exactly one materialized attempt, counters
  accounting for it, no decision history entry for it, and a legal
  `last_transition` edge into the new state).

## 24. Backward compatibility with v0.3-D documents

| Existing document | v0.3-E behaviour |
| --- | --- |
| completed v0.3-D run | loads, terminal, never enters recovery |
| `STOPPED` / `LIMIT_REACHED` | unchanged, terminal |
| `BLOCKED` (any v0.3-D reason) | unchanged, terminal, **not** recoverable (no reopening) |
| valid v1 interrupted/in-flight document | loads under v1 rules; its next mutating action materializes `BLOCKED`/`turn_interrupted` exactly as v0.3-D did, unless the implementation explicitly adopts v2 materialization **for new attempts only** (design decision: v1 documents keep v1 semantics; new v2 runs get `RECOVERY_REQUIRED`) |
| old `schema_version` (1) | never migrated, never rewritten, never reinterpreted |
| no recovery metadata | legal for v1 documents; required for v2 `RECOVERY_REQUIRED` |

## 25. Non-goals (kept out of v0.3-E)

Automatic retry · automatic planner decisions · automatic role sequencing ·
provider/model fallback · automatic interrupt/resubmission · distributed
multi-process or multi-surface locking · cross-machine recovery · background
daemon or scheduler polling · WebUI recovery UI · HTTP control plane ·
release/version bump · automatic resume without explicit planner action ·
semantic interpretation of any model output · repairing arbitrary corruption ·
reconstructing lost prompts or replies.

## 26. Test strategy (designed now, implemented later)

* deterministic offline crash-window simulations: the existing crash doubles
  (`SystemExit` at submission, gated transports) extended to kill at each of
  W0–W6, with the *real* service/router/bridge against the stub;
* restart/reconciliation tests: save → destroy the surface → recreate → reconcile
  → resolve → verify, for every case A–H;
* no-duplicate-submission assertions: the total prompt-POST count is asserted
  unchanged across every recovery scenario (the central safety test);
* budget preservation: `model_turns_used` never changes except by a normal
  consumed slot;
* route/workspace/session matching: drift, foreign session, copied document, and
  deleted-session cases all fail closed;
* ambiguity: two candidate messages / two ledger records / mismatched digests →
  refuse and stay frozen;
* terminal immunity: recovery tools against every terminal state are local,
  mutation-free and model-call-free;
* reviewer authority stays zero (prose variants, unchanged);
* mutation tests for recovery-critical invariants (no second submission, no
  refund, no adoption without the §12 checklist, no reopening of terminals,
  read-only reconcile);
* a production-generated honest recovery corpus (each case A–H produced by the
  real service plus fake remote evidence variants) with a per-mutation
  differential battery, mirroring the v0.3-D corpus discipline;
* zero real provider calls during unit/integration testing.

## 27. Future real-smoke design (not authorized now)

One minimal bounded scenario, **only if §15 P1–P4 are proven**: a real implementer
turn succeeds remotely → a *controlled* local interruption is injected before the
completed turn is persisted (for example a persistence failure right after the
response, or a hard kill of the DevRelay process while the provider reply
exists) → restart → explicit `devrelay_reconcile_run` shows a provable match →
explicit `devrelay_resolve_recovery(adopt_completed_turn)` → the existing remote
result is materialized with **zero additional provider calls** (asserted by the
provider log and the ledger's `external_request_count`), the slot count unchanged,
and the run legal to continue.  If P1–P4 cannot be proven, this smoke cannot be
made reliable and v0.3-E must ship as "reconcile and report, never adopt, always
fail closed" — which is an acceptable, honest outcome to design for.

## 28. Design decisions table

| Topic | Decision | Reason | Safety invariant | Open question |
| --- | --- | --- | --- | --- |
| Recovery state model | add one non-terminal, execution-frozen `RECOVERY_REQUIRED`; keep `BLOCKED` terminal | `BLOCKED` is terminal and terminals never reopen; adoption must not silently reinterpret history | terminal runs never reopen; no exit to `READY_*` without proof | is one state enough for both "needs evidence" and "evidence gathered"? (design says yes via metadata) |
| Reconcile authority | deterministic evidence **and** an explicit planner action; provider prose has none | preserves the v0.3-D authority invariant | reviewer prose has zero authority | should a reconcile report be attachable to a decision record for audit? |
| Retry policy | no implicit retry; no retry protocol in v0.3-E at all | a timeout must never become a free retry; no idempotency key exists | no hidden retry; no fallback; ≤1 submission per explicit phase call | does any real use case require an explicit retry protocol later? |
| Exact operation identity | `(run_id, role, cycle, session_id, model, agent, prompt_sha256, prompt_chars, call_id)`; no OpenCode idempotency key | only identities that actually exist are used | no invented platform facility | can the ledger record's identity be matched to a remote message without text? (§12 mechanism, pending P2) |
| Crash windows | W0–W6 matrix with per-window allowed/forbidden actions | makes every kill point explicit and testable | fail closed everywhere; no auto-submission | is a hard kill during the ledger settle reachable in practice? (P7) |
| Pending replies | reads only, bounded, explicit; no waiting/polling daemon | prevents unbounded loops and hidden work | no model call to resolve; no automatic anything | does OpenCode expose a per-operation pending handle? (P4) |
| Budget semantics | consumed slots, never refunded, no restart budget | preserves accepted v0.3-D accounting | no refund/reset/free retry | none (decision is closed) |
| Schema/versioning | `schema_version` 2 for new documents; v1 never migrated or reinterpreted | avoids silently changing accepted history | no silent default for safety-critical fields | should v2 also be written for non-recovery runs (design: yes, one current schema) |
| Terminal handling | terminals never enter recovery; recovery tools are local failures there | preserves v0.3-D terminal semantics | terminal runs never reopen | none (decision is closed) |
| Route drift | snapshot is authoritative; drift blocks adoption | route identity is historical | immutable snapshot; no fallback | none (decision is closed) |
| Workspace/session identity | re-verify workspace, ownership and role distinctness before adoption; missing session fails closed | a copied run or foreign session must never be recovered | explicit ownership; distinct sessions | is session-id + directory strong enough against recreation? (P6) |
| Concurrency | recovery actions share the accepted per-surface lock; multi-surface/multi-process still unsupported | no new locking model, no false claims | one lock per surface; no process-wide claim | none (decision is closed) |
| Privacy | digests/ids/metadata only; transient in-memory text allowed, never persisted | preserves the v0.3-D privacy contract | no prompt/response/reasoning/credential persistence | does digest matching need the verbatim text? (P2) |
| Compatibility | v1 documents keep v1 semantics; new runs are v2; no migration | accepted history must not be reinterpreted | corruption fails closed; no repair | do we need a read-only "v1 run cannot be recovered" hint in the report? |

## 29. Explicit unresolved questions (blocks implementation)

See §15 (P1–P7).  Until they are answered by a platform proof, the following are
**not frozen**: reconciled-completion adoption, pending-reply resolution,
non-delivery as a proof, and the real-smoke scenario.  The fail-closed core —
authority, no-retry, budget, terminal immunity, privacy, concurrency,
crash-window handling for W0/W1/W2/W6, and "reconcile reports but never guesses" —
is frozen by this document and is provable offline today.

## 30. Minimal local setup (future)

```text
devrelay mcp serve --workspace <ws>     # unchanged 17 tools; v0.3-E adds exactly
                                        # devrelay_reconcile_run (read-only)
                                        # devrelay_resolve_recovery (mutating)
```

An MCP Planner would: read `devrelay_get_run`, call `devrelay_reconcile_run` after
a restart, read the proof checklist, and then either call
`devrelay_resolve_recovery(adopt_completed_turn)` (only when every checklist item
passed) or `devrelay_resolve_recovery(mark_unrecoverable)` and handle the terminal
`BLOCKED` run itself.  DevRelay still never sequences anything.
