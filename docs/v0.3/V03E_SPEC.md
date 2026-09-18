# DevRelay v0.3-E — recovery and reconciliation (design, FROZEN)

Status: **DESIGN FROZEN / NOT IMPLEMENTED / NOT ACCEPTED / UNRELEASED**

Independent design-freeze review of candidate
`9f4a01804b9affe8938a272553df345b5a60aeed`: **P0 = 0, P1 = 0, P2 = 0**, F1–F12
**CLOSED**, decision **APPROVE V0.3-E FAIL-CLOSED CORE DESIGN; PLATFORM PROOF GATE
REQUIRED BEFORE IMPLEMENTATION**.  The design is therefore **frozen**; the
implementation is **NOT authorized**, the pre-implementation platform proof gate is
**NOT complete** (**G0.1 / P7 = PASS — AUTHORITATIVE PASS / INDEPENDENTLY APPROVED**
by the final proof review *APPROVE V0.3-E G0.1 / P7 PLATFORM PROOF* (P0 = 0, P1 = 0,
P2 = 0) — `V03E_G0_1_P7_PROOF.md`; **G0.2 = PASS — AUTHORITATIVE PASS /
INDEPENDENTLY APPROVED** by the clean-rerun review *APPROVE V0.3-E G0.2
FALSE-CORRELATION PROOF* (P0 = 0, P1 = 0, P2 = 0) — the original round was followed by
one `REQUEST_CHANGES` review and a separately authorized clean re-run under the oracle
precommitted in commit `12ea1b7`; the ten fixed cases A-J ran once each, all
fail-closed, 0 provider/model calls — `V03E_G0_2_CLEAN_RERUN_PROOF.md` (original record
preserved: `V03E_G0_2_FALSE_CORRELATION_PROOF.md`); the original G0.3 round failed as
**CANDIDATE FAIL** at `c889636` (case G0.3-J surfaced `remote_protocol_error` instead of the
precommitted `write_error` class; independently reviewed as a **TYPE-1 proof-plan failure**
with no classifier-safety failure and no runtime remediation requirement —
`V03E_G0_3_TRANSPORT_PROOF.md`), and the separately authorized **corrected clean rerun**
under the new precommitted oracle `e328ec5`/`V03E_G0_3_RERUN_ORACLE.md` produced
**G0.3 / P5 = PASS** (authoritative, independently approved: the independent review of the corrected clean proof issued *APPROVE V0.3-E G0.3 / P5 TRANSPORT PROOF* with P0 = 0, P1 = 0, P2 = 0 — this PASS comes from that independent review, never from executor self-approval): the accepted safe buckets
are class-wide pre-send, `proxy_error` is `UNREACHABLE_CURRENT_CONFIGURATION`, every
uncertain class stayed `submission_uncertain` with `retry_safe` false, and corrected case J
surfaced `remote_protocol_error` exactly as precommitted — `V03E_G0_3_CLEAN_RERUN_PROOF.md`;
**G0.4 has since been executed once and is an authoritative `FAIL / P4 UNPROVEN`**
(independently approved failed proof: *APPROVE V0.3-E G0.4 FAILED PROOF*, P0 = 0, P1 = 0,
P2 = 0, failure type **TYPE 3 — SEMANTIC ENVIRONMENT / CONFIGURATION RESULT**; the accepted
workspace had no OpenCode base endpoint, so no target instance could be bound and 0 `GET /doc`
were issued — `V03E_G0_4_API_INSPECTION_PROOF.md`), while steps G0.5, G1 and G2 have **not** run),
`adopt_completed_turn` remains **DISABLED**, and no provider/model call occurred during
the reviews (the reviews were static/documentary).

* Frozen contract: this document; acceptance target:
  `docs/v0.3/V03E_ACCEPTANCE.md`.
* Branch: `v0.3-e-recovery-reconciliation` (design only, no upstream).
* Design lineage (preserved): `673632d` initial design candidate → independent
  `REQUEST_CHANGES` (P0 = 1, P1 = 6, P2 = 5) → remediation `f67bf9e` → narrow
  re-review `REQUEST_CHANGES` (P2: stale status/gating pointer) → status fix
  `5b7c65a` → narrow re-review `REQUEST_CHANGES` (P2: G0.1/P7 hard-gate
  contradiction) → hard-gate policy fix `9f4a018` → **final independent
  design-freeze approval (P0 = 0, P1 = 0, P2 = 0)**.  The branch parent is
  `56e7842a414777d20a3882cad641da383964bab3` (v0.3-D closeout follow-up).
* Accepted v0.3-D runtime candidate:
  `8b70610a5cdda600ef57cf8378c4f69cd33d5be4` (ACCEPTED / CLOSED / UNRELEASED).
* Package version stays `0.1.0`; the only public tag is `v0.1.0`; nothing is
  pushed, merged, tagged or released.

## 1. Scope decision — the mandatory core vs the gated capability

v0.3-E is split so that the fail-closed core needs **no remote platform proof**
(only the local **G0.1 / P7** gate first, §25) and can therefore be implemented and
accepted once that gate passes - that gate **has** passed (§25/§28, authoritative and
independently approved), and implementation still requires a separately issued
authorization - and so that no optional capability can block it.

**MANDATORY v0.3-E CORE (implementable; no remote platform proof required):**

| # | Capability | Meaning |
| --- | --- | --- |
| A | `devrelay_reconcile_run` (**report**) | read the durable and (when available) remote evidence for one interrupted attempt and *report* it: identity, strict-reader result, session-history candidates, per-item proof checklist, blockers.  Read-only: no mutation, no model call, no submission. |
| B | `devrelay_resolve_recovery(mark_unrecoverable)` | the explicit, planner-authorized, fail-closed exit: convert the recovery attempt into exactly one blocked role turn and enter terminal `BLOCKED`.  Local only. |
| C | no provider/model submission | no recovery action ever submits a model turn. |
| D | no retry | v0.3-E contains **no** retry protocol; a timeout or transport classification never becomes a free retry. |
| E | no auto-resume | nothing runs by itself: no scheduler, no daemon, no polling loop, no work on restart. |
| F | no adoption | a remote result is **never** adopted unless the optional adoption capability gate (§11) has independently passed. |

**OPTIONAL GATED CAPABILITY (not part of the mandatory implementation scope):**

* `adopt_completed_turn` — materialize an already-completed remote turn *without*
  a new submission.  Requires **both** the independently satisfied **local P6
  identity/ownership veto bound** (§12.4, §25.1; proved by G0.5) **and** the
  independently satisfied remote/platform operation-attribution *enabling* proofs
  P1, P2, P3, P8 (+ P9 if timestamp correlation is used, through G1/G2), plus the
  verified local ledger/session integrity rules (§11, §12.6) and all other frozen
  runtime/adoption invariants.  Until then it is documented and **refused**.

**PENDING-RESULT capability:** report-only (§14) unless a future proof establishes
an operation-specific handle.

**NON-DELIVERY classification:** informational transport evidence only (§15); no
orchestration authority, and it can never authorize a submission.

Rule: optional capabilities never block the core, and the core never performs an
optional capability's work "as a fallback".

## 2. Inventory: the recovery-related surface that exists today

Read-only inventory on this design lineage (accepted v0.3-D runtime `8b70610`).
Nothing below was modified.

**Orchestration (v0.3-D, accepted)**

* `src/devrelay/orchestration/models.py` — `RunState`
  (`READY_IMPLEMENTER`, `READY_REVIEWER`, `AWAITING_DECISION`, `COMPLETED`,
  `STOPPED`, `BLOCKED`, `LIMIT_REACHED`; last four terminal); `TurnRecord`
  (sanitized evidence: `prompt_sha256`, `prompt_chars`, `resolved_model`,
  `resolved_agent`, `route_source`, `operation_state`, `submission_attempted`,
  `submission_status`, `submission_uncertain`, `reply_pending`, `retry_safe`,
  `call_ids`, `assistant_message_ids`, `outcome`, `blocked_reason`);
  `OrchestrationRun.in_flight_turn`; `summary()["legal_next_actions"]`.
* `src/devrelay/orchestration/service.py` — `_run_role` persists the in-flight
  intent **before** the role call and finalizes the turn afterwards;
  `_materialize_interrupted_turn` (reached from `_load_for_action`) currently
  converts a live intent into a finished `blocked`/`turn_interrupted` turn **as a
  side effect of the next mutating action**; `_block`; `_require_route_unchanged`;
  `_verify_session`.
* `src/devrelay/orchestration/state_machine.py` — `require_not_terminal`,
  `require_no_in_flight_turn`, `require_state`, `require_cycle_budget`,
  `after_role_turn`, `after_decision`.
* `src/devrelay/orchestration/store.py` + `invariants.py` — strict single-writer
  store; load/save re-derive structural and reachability invariants; corruption
  fails closed and is never repaired.
* `model_turns_used` = **consumed orchestration model-turn budget slots**, never
  refunded.

**OpenCode bridge (accepted v0.3-A)**

* `src/devrelay/opencode/bridge.py` — `health`, `list_sessions`, `get_session`,
  `read_messages` (explicit cursor, read-only), `send_prompt` (exactly one
  submission POST), `wait_idle` (bounded session-status polling), `interrupt` (an
  accepted abort is **not** a verified terminal state); `_request` allocates a
  durable call id and writes the ledger record **before the request leaves the
  machine**, then settles it.
* `src/devrelay/opencode/accounting.py` — `allocate_call_id` (durable monotonic
  `OC-NNNN`, never reused; a corrupt sequence fails closed), `begin` (immutable
  create-new), `finish` (settle in place), `records`, `read_records`.
* `src/devrelay/opencode/models.py` — `OpenCodeCallRecord` (durable per-request
  evidence: `call_id`, `operation`, `state`, `method`, `path`, `session_id`,
  `issued`, `external_request_count`, `http_status`, `error_type`, `started_at`,
  `completed_at`, `duration_ms`, `submission_uncertain`, `response_media_type`,
  `prompt_sha256`, `prompt_chars`, `agent`, `model`; **never** prompt text);
  `OpenCodeOperationResult`; `OpenCodeMessage` (`message_id`, `role`,
  `created_at`, `parts[].text`, with `.text` = `"\n".join(part.text …)`);
  `prompt_digest` (unsalted SHA-256 of the exact prompt string).
* Read surfaces over that evidence: `opencode_read_messages`,
  `opencode_get_session`, `opencode_wait_idle`, `opencode_calls`.

**MCP surface (accepted v0.3-B / v0.3-D)**

* 17 tools; orchestration tools `devrelay_start_run`, `devrelay_get_run`
  (read-only), `devrelay_run_implementer`, `devrelay_run_reviewer`,
  `devrelay_decide_run`; one re-entrant execution lock **per tool surface**.

**Documents**

* `docs/v0.3/V03D_SPEC.md` §6/§10, `docs/v0.3/V03D_ACCEPTANCE.md` (E2),
  `docs/BACKLOG.md` §5 (v0.3-E recovery; platform proofs P1-P9 and the split
  implementation gate recorded: local G0.1/P7 for the mandatory core; for the optional
  adoption capability the **local P6/G0.5 identity/ownership veto-bound prerequisite**
  **plus** the P1/P2/P3/P8 (+P9 if timestamps are used) **G1/G2 remote/platform
  *enabling* proofs** — both classes are required).

**Not v0.3-E.**  `recover_pending_implementation` / `recover_pending_review`
(`src/devrelay/pipeline/engine.py`) and `reconcile_observed_files`
(`src/devrelay/providers/codex_runtime.py`) are pre-existing **v0.2 Codex-pipeline**
functions, unrelated to orchestration recovery, untouched, and not to be reused.

## 3. Preserved v0.3-D invariants (all binding)

1. Reviewer prose has **zero** state-machine authority.
2. Only an explicit external planner decision leaves `AWAITING_DECISION`.
3. `1 <= max_cycles <= 3`; `model_turn_budget = 2 × max_cycles`; six-slot ceiling.
4. No hidden retry, no fallback model/route, no automatic
   implementer→reviewer sequencing, at most one submission per explicit phase call.
5. Terminal runs never reopen.
6. Route snapshots are immutable; workspace/session ownership stays explicit;
   implementer and reviewer sessions stay distinct.
7. Corruption fails closed and is never repaired; persisted types stay strict;
   reachability rules stay enforced on load and save.
8. No raw prompt, provider response, reasoning or credential is persisted.
9. Accounting stays intact: a consumed slot is never refunded; no restart creates
   budget; `turn_attempts == model_turns_used` always.

## 4. Recovery problem taxonomy

Distinct cases, never one "retryable" bucket.

| # | Case | What is known | Evidence | May a model call resolve it? |
| --- | --- | --- | --- | --- |
| A | Pre-submission failure | no durable intent, or submission provably never started | run document, strict ledger reader, accepted guards | no |
| B | Transport-classified non-delivery | the accepted v0.3-A connect-phase classes were recorded | ledger record; **reported as evidence only** (§15) | no |
| C | Submission attempted, response known | the normal completed turn | turn record | no |
| D | Submission uncertain | the request may have reached OpenCode/provider | ledger `submission_uncertain`, run intent | no — only gated adoption (§11) or `mark_unrecoverable` |
| E | Reply pending | positive evidence that an accepted submission may still produce a reply | ledger 2xx + JSON contract, session state (**session-level only**, §14) | no — report-only |
| F | Process crash with durable in-flight intent | DevRelay died between intent persistence and finalization | live `in_flight_turn`, strict ledger reader | no |
| G | Remote completion / local persistence gap | the provider really produced the reply but the finished turn was never persisted | strict ledger reader + session history, only under §11 | no (adoption is local materialization, not a submission) |
| H | Contradictory or insufficient evidence | yes/no cannot be decided | any combination | no — fail closed |
| **X** | **Corrupt document** | the persisted document violates accepted invariants outside the enumerated recovery deltas | strict validation | **not recovery**: `orchestration_state_corrupt`, no entry, no override (§6) |

## 5. Terms

* **RECONCILE** — read existing durable/local/remote evidence and determine what
  already happened.  Read-only; never a model call; never mutates run state.
* **MATERIALIZE** — write an already-established fact into durable run state
  (adopting a proven completion).  Explicit, atomic, idempotent per evidence, only
  after reconciliation proved it, and only when the adoption capability is enabled.
* **RESUME** — continue orchestration from a state reconciliation produced
  legally.  Resume itself issues nothing; the next model call still requires an
  explicit planner phase action in a legal state.
* **RETRY** — issue another model submission.  **v0.3-E has no retry protocol of
  any kind** (§18); bridge-level `retry_safe` metadata has **no orchestration
  recovery authority** and is never an input to a recovery decision.

## 6. Corruption is never recovery

Recovery operates **only** on an otherwise-valid document whose ambiguity comes
from the known crash/submission boundary.  If the persisted document violates any
accepted structural or semantic invariant outside the explicitly enumerated
recovery deltas below, the result is `orchestration_state_corrupt`: **no recovery
action, no transition into `RECOVERY_REQUIRED`, no planner override, no repair**.

Enumerated recovery deltas (the only relaxations while `state ==
RECOVERY_REQUIRED`, v2 documents only):

1. one consumed slot is held by the single `recovery.attempt` record instead of a
   role-history turn (see the accounting equations in §8.3);
2. `recovery_reason` is required and `blocked_reason` is empty;
3. `last_transition.action == "recover"` is a legal edge (the new edges in §8.4);
4. `legal_next_actions` is exactly the recovery actions (§8.2).

Removed from the earlier design: "an interrupted attempt whose role/cycle evidence
cannot be finalized into a role history entry" as an entry into recovery — that is
either a crash-boundary case handled by §8 (whose attempt evidence is complete by
construction) or corruption (this section).

## 7. Authority, actions and the entry deadlock fix (F1)

**Authority.** Deterministic evidence **and** an explicit external planner action
are both required for any write.  The provider/reviewer/model has zero recovery
authority; no prose parsing, no heuristics.  The planner cannot authorize a fact
into existence: `adopt_completed_turn` re-verifies every condition at call time.

**Entry deadlock (review P0) and its fix.**  A v0.3-D-shaped document can be
`READY_IMPLEMENTER`/`READY_REVIEWER` with a live `in_flight_turn`; `reconcile` and
`get_run` are read-only, and `resolve_recovery` was legal only *in*
`RECOVERY_REQUIRED` — so no legal action could ever create that state, and the only
existing materialization path was a hidden side effect of a *refused* phase call.
Fixed normatively:

> **Every transition into `RECOVERY_REQUIRED` has a named, explicit, legal planner
> action.  No transition is ever a side effect of an invalid action.**

`devrelay_resolve_recovery(run_id, resolution)` is legal for exactly two input
shapes:

| # | Input document | What the action does (one atomic state write) |
| --- | --- | --- |
| 1 | a **valid, non-terminal** v2 document carrying a legal live `in_flight_turn` (`READY_IMPLEMENTER` + implementer intent, or `READY_REVIEWER` + reviewer intent) and satisfying §8 | validate the document as otherwise legal → materialize the interrupted attempt into the single `recovery.attempt` record → enter `RECOVERY_REQUIRED` → apply exactly one resolution that is legal for the enabled scope.  In the mandatory core that resolution is `mark_unrecoverable` (so the core always has a legal exit in one call); `adopt_completed_turn` is accepted here only when the adoption capability is enabled and §11 passes |
| 2 | a document already in `RECOVERY_REQUIRED` | apply exactly one resolution (`mark_unrecoverable`, or `adopt_completed_turn` when the capability is enabled and §11 passes) |

Consequences, stated normatively:

* for a **v2** document with a live intent, the model-bearing tools
  (`run_implementer`, `run_reviewer`) and `decide_run` **refuse without mutating**
  with a stable local error (`orchestration_recovery_required`) — they no longer
  materialize anything as a side effect;
* for a **v1** document the accepted v0.3-D behaviour is preserved *exactly* (its
  next mutating action materializes `BLOCKED`/`turn_interrupted`); v0.3-E's explicit
  entry applies to v2 documents only (§10);
* `devrelay_start_run` never creates a document with a live intent, so it is not an
  entry path.

## 8. `RECOVERY_REQUIRED`: one state, one attempt representation, exact shape

### 8.1 One legal attempt representation (F2)

> The interrupted attempt is represented by **exactly one `recovery.attempt`
> record** — never by a normal role-history turn — while the run is in
> `RECOVERY_REQUIRED`.  Normal `implementer_turns`/`reviewer_turns` contain only
> finalized normal orchestration history.

Resolution converts that *same* attempt exactly once, in one atomic write:

* `mark_unrecoverable` → the recovery attempt becomes **exactly one blocked role
  turn** and the run enters terminal `BLOCKED`;
* `adopt_completed_turn` (gated) → the same attempt becomes **exactly one
  completed role turn** and the run enters the legal post-turn state
  (`READY_REVIEWER` for an implementer attempt, `AWAITING_DECISION` for a reviewer
  attempt).

Hard rules: never two role records for the same role/cycle; no normal blocked turn
exists while `state != BLOCKED`; the recovery record never again authorizes a write
after resolution (it is retained only as that attempt's resolution audit).  This
removes the earlier contradiction between "adoption appends a turn" and "recovery
never rewrites the attempt": the attempt is not appended *and* rewritten, it is
**converted once**.

### 8.2 Normative document shape (F3)

Every v2 document in `RECOVERY_REQUIRED` must satisfy exactly this shape (all
fields strict; anything else is corrupt per §6):

| Field | Required value in `RECOVERY_REQUIRED` |
| --- | --- |
| `schema_version` | `2` |
| `state` | `RECOVERY_REQUIRED` |
| `current_cycle` | `completed_cycles + 1` (open-cycle relation) and `1 <= current_cycle <= max_cycles` |
| `completed_cycles` | `0 <= completed_cycles <= max_cycles`; equals the number of completed reviewer turns in the normal history |
| `max_cycles` | `1..3` (unchanged) |
| `model_turn_budget` | exactly `2 × max_cycles` |
| `model_turns_used` | unchanged by recovery: identical to the pre-entry value; never refunded |
| `turn_attempts` | `== model_turns_used` |
| `in_flight_turn` | **`null`** — the entry mutation cleared it in the same atomic write |
| `recovery` | present: exactly one record with `attempt` (the materialized sanitized attempt), `resolution == ""`, `resolved_at == ""`, and the frozen `evidence` snapshot (incl. `evidence_sha256`) |
| `recovery_reason` | non-empty, one of `turn_interrupted`, `submission_uncertain`, `reply_pending` |
| normal `implementer_turns` + `reviewer_turns` | only finalized history; at most one turn per role per cycle, implementer before reviewer, every completed reviewer turn has exactly one completed implementer turn in the same cycle |
| `decision_history` | `len == completed_cycles` (the state is not `AWAITING_DECISION`), accepted edges only |
| `blocked_reason` | empty |
| `last_transition` | the `recover` edge that entered the state (§8.4), `source == external_planner`, `cycle == current_cycle`, `role == attempt.role` |
| `legal_next_actions` | `["devrelay_reconcile_run", "devrelay_resolve_recovery(mark_unrecoverable)"]`; `adopt_completed_turn` is appended only when the adoption capability is enabled and §11 passes |

### 8.3 Accounting equations (pinned)

Let `impl = len(implementer_turns)`, `rev = len(reviewer_turns)`,
`ra = 1 if recovery.attempt else 0`, `live = 1 if in_flight_turn else 0`.

* **Always, every state:** `turn_attempts == model_turns_used`.
* **Before the entry mutation (live-intent document):**
  `impl + rev + live == model_turns_used` and `ra == 0`.
* **During the single entry write:** the live intent is replaced by the recovery
  attempt — `live: 1→0`, `ra: 0→1` — so the sum is preserved and
  `model_turns_used` is unchanged.  No intermediate document is observable (one
  atomic write).
* **In `RECOVERY_REQUIRED`:** `impl + rev + ra == model_turns_used`, `live == 0`,
  and the recovery attempt accounts for exactly one consumed slot.
* **After `mark_unrecoverable`:** `impl + rev == model_turns_used`, the recovery
  record is retained as the resolution audit, `state == BLOCKED`,
  `blocked_reason == recovery_reason`, `legal_next_actions == []`.
* **After `adopt_completed_turn`:** `impl + rev == model_turns_used` with the
  converted attempt now counted as one completed role turn.
* **Never:** any equation that refunds a slot, decrements a counter, or counts the
  same slot twice.

### 8.4 New `last_transition` edges

| From | Action (`source == external_planner`) | To | role / cycle |
| --- | --- | --- | --- |
| `READY_IMPLEMENTER` + implementer live intent | `recover` (`resolve_recovery`) | `RECOVERY_REQUIRED` | `implementer` / `current_cycle` |
| `READY_REVIEWER` + reviewer live intent | `recover` (`resolve_recovery`) | `RECOVERY_REQUIRED` | `reviewer` / `current_cycle` |
| `RECOVERY_REQUIRED` | `recover` (`mark_unrecoverable`) | `BLOCKED` | `attempt.role` / `current_cycle` |
| `RECOVERY_REQUIRED` | `recover` (`adopt_completed_turn`, gated) | `READY_REVIEWER` | `implementer` / `current_cycle` |
| `RECOVERY_REQUIRED` | `recover` (`adopt_completed_turn`, gated) | `AWAITING_DECISION` | `reviewer` / `current_cycle` |

The accepted reachability validator extends with exactly these edges; no other
transition into or out of `RECOVERY_REQUIRED` exists.

## 9. Strict recovery evidence reader (F5)

The earlier claim "no ledger record ⇒ never issued" is **removed**: absence of
visible evidence is not proof of absence.  v0.3-E therefore defines a dedicated
**strict recovery evidence reader** (design; not implemented) with these normative
properties:

1. **identity-scoped scan** — scan the workspace ledger for records matching the
   attempt identity (operation, `session_id`, `prompt_sha256`, `prompt_chars`,
   `model`, `agent`) within the proven interval;
2. **no silent skipping** — an unreadable, unparsable, torn or schema-invalid
   record is **never** skipped; it yields `evidence_gap` (the ordinary MCP
   accounting reader may keep its tolerant UX behaviour, but recovery never uses it
   as proof);
3. **no truncation as proof** — the accounting reader's newest-N / max-N window
   must never be used to conclude that no record exists; the recovery reader proves
   the scanned interval instead;
4. **interval proof** — the reader must demonstrate that the full relevant
   sequence interval was scanned (from a proven floor to a proven ceiling using the
   durable call-sequence evidence) or return `evidence_gap`;
5. **outcomes** — `exactly_one_match` · `multiple_matches` (→ `evidence_conflict`)
   · `no_record_in_proven_interval` (reportable as "no DevRelay ledger record found
   in the proven interval", **never** as "never submitted") · `evidence_gap`
   (unreadable/corrupt/unproven interval);
6. **no inference from absence** — no recovery decision may treat a missing record
   as proof of non-delivery; only §15's transport classification is reported, and
   `mark_unrecoverable` needs none of it.

## 10. Schema dispatch (F7)

Validation is **version-dispatched**; there is no single-equality check and no
migration:

```text
if schema_version == 1:
    validate with the frozen v0.3-D v1 validator (unchanged)
    the document is never written, never migrated, never upgraded
    no entry into RECOVERY_REQUIRED
    reconcile         -> report only (local evidence; remote reads optional, report-only)
    resolve_recovery  -> refuse locally (stable error, no mutation)
    a v1 live-in-flight document keeps EXACTLY the accepted v0.3-D behaviour
    (its next mutating action materializes BLOCKED/turn_interrupted)

if schema_version == 2:
    validate with the v0.3-E v2 rules (accepted v1 rules + the §8 shape and edges)
    recovery metadata and RECOVERY_REQUIRED are legal

otherwise:
    orchestration_state_corrupt (unsupported schema_version; no default insertion)
```

**How new runs become v2:** `devrelay_start_run` in a v0.3-E build writes
`schema_version = 2` for **new** runs (the exact switch is an implementation-time
change with its own tests).  No existing document is rewritten, and a missing
`schema_version` remains a malformed document (no default).

## 11. Adoption capability gate (F6)

`adopt_completed_turn` is an **optional gated capability**.  The earlier claim that
an eight-item checklist *proves* exact operation attribution is withdrawn: it does
not.  Reconcile may therefore **report a candidate**, but `resolve_recovery` MUST
**refuse** `adopt_completed_turn` as long as the gate has not independently passed —
no "likely match", no heuristic, no partial credit.

When (and only when) the platform proofs pass, adoption requires **all** of:

1. every §12.6 local-integrity condition (strict reader, workspace binding, session
   ownership, role/session distinctness, route snapshot unchanged, atomic writes,
   execution lock);
2. exactly one ledger record matching the attempt identity, settled `COMPLETED`,
   2xx, JSON media type, `submission_uncertain == false`;
3. exactly one session-history user message whose accepted joined text hashes to
   the stored `prompt_sha256`, and that message is the **last relevant user
   message** in the evidence window;
4. exactly one assistant message **directly associated with** that user message,
   and it is the **final relevant assistant message** in the window;
5. **no unexpected session message** appears inside the evidence window;
6. **no other DevRelay ledger operation touches that session** inside the window
   (the local half of P8);
7. captured workspace/session/role/model identity all match;
8. **P1** history durability, **P2** submitted-text fidelity, **P3**
   identical-prompt uniqueness and **P8** session exclusivity all PASS — plus
   **P9** if any timestamp or relative-order correlation is used — and, separately, the
   **local P6 identity/ownership veto bound** (§12.4, §25.1) is independently satisfied:
   the remote/platform *enabling* proofs and the local *veto bound* are two distinct
   classes, and **both** must hold before adoption may ever be authorized;
9. the run's cycle/role/phase expectation still matches the attempt.

Any missing or ambiguous item → refuse; the run stays `RECOVERY_REQUIRED` and the
only remaining resolution is `mark_unrecoverable`.

**`mark_unrecoverable` independence (F8).**  The checklist above applies to
`adopt_completed_turn` **only**.  `mark_unrecoverable` requires nothing more than a
legal recovery entry/document (§7), planner authority, local state invariants and an
uncorrupted document: it must **never** require remote session history to exist, and
a missing/foreign/unreadable session, an absent ledger record, or `evidence_gap`
must never block it.  It is the fail-closed safety exit and is always available.

## 12. Reconciliation sources and identity

### 12.1 Sources

| Source | Authoritative for | Mode | Absence / failure | Ambiguity | Survives restart | Distinguishes not-submitted from unobserved? |
| --- | --- | --- | --- | --- | --- | --- |
| run document | state, cycle, counters, intent, decision history, snapshot | read (strict) | corrupt → fail closed | contradictory → corrupt (§6) | yes | records intent only |
| ledger via the **strict reader** (§9) | that DevRelay issued a request, its transport outcome class and the request identity | read-only | `evidence_gap` or `no_record_in_proven_interval` (report-only) | `multiple_matches` → conflict | yes | only in the report-only sense (§15); never a proof |
| session history (`read_messages`) | what the provider produced in that session | read-only | missing/empty/unreadable → `evidence_gap` | more than one candidate → refuse | **P1** | yes under P2/P3/P8 |
| session state (`get_session`, `wait_idle`) | current session busy/idle | read-only, not a model call | unknown → do not act | busy with no matching message → stay frozen | session existence only | "may still be running", never delivery |
| current role configuration | drift detection only | read-only | missing/invalid → cannot proceed under that route | drift → fail closed | yes | n/a — never rewrites the snapshot |
| accepted v0.3-A taxonomy | transport classification (report-only) | static | unknown class → report `evidence_gap` | conflicting classes → report uncertain | yes | classification, not proof (§15) |

### 12.2 Prompt digest and text semantics (F12)

* `prompt_sha256` is the accepted bridge's digest of the **exact prompt string the
  tool received** (UTF-8, no normalization, no stripping, no BOM insertion).
* The remote comparison uses the **accepted joined-text representation** of a
  session message: `"\n".join(part.text for part in parts if part.text)` — the same
  rule the accepted `OpenCodeMessage.text` implements.  A "single content part" is
  **not** assumed:
  * multiple text parts are joined with `\n` in part order;
  * line endings are **not** normalized (a `\r\n` in the sent text must appear as
    `\r\n` in the stored text);
  * encoding is UTF-8 throughout;
  * an empty prompt is impossible (the tool boundary rejects it); an empty or
    missing remote text counts as **no match** (fail closed);
  * missing or invalid timestamps are never used as identity evidence unless
    **P9** passes.
* If canonical text fidelity cannot be established, that is exactly **P2**, and
  adoption stays disabled.

### 12.3 Route drift

Snapshot is authoritative; current configuration is drift detection only.  Drift
(or an unresolvable role) → no adoption; the run stays `RECOVERY_REQUIRED` until
`mark_unrecoverable`.  No fallback, no snapshot rewrite.

### 12.4 Workspace and session identity (P6)

Before any adoption: workspace binding, session ownership (`workspace_match`),
role/session distinctness and the route snapshot are re-verified.  A run document
copied into another workspace is **not** recoverable.  If a session is missing,
foreign, recreated, copied or otherwise cannot be proven to be the original owned
session, **adoption is unavailable** — the mandatory report/`mark_unrecoverable`
still works and never claims remote completion.

**Identity vs ownership (normative, P6 sense).**  *Session identity* is the remote OpenCode
session reference, principally `session_id`, treated strictly as an **opaque remote
identifier**; *session ownership* is the **local recovery claim** that the referenced
session is sufficiently bound to the original DevRelay recovery context.  **`session_id`
equality alone must never clear the P6 veto**, and no single field alone proves ownership.
If originality cannot be proven with the permitted local evidence, the result is
**IDENTITY / OWNERSHIP NOT PROVEN** and adoption remains unavailable — never "probably the
same session".  The frozen G0.5/P6 proof definition (exact question, four case classes A–D,
PASS/FAIL/insufficient-evidence semantics, local-offline method, budget, dimension matrix and
evidence fields) is **§25.1**.

### 12.5 Terminal states

`COMPLETED`, `STOPPED`, `LIMIT_REACHED`, `BLOCKED` never enter recovery and never
reopen; recovery tools against them fail locally with zero mutation and zero model
calls; a terminal document with a live intent remains **corrupt**.

### 12.6 Local integrity conditions (required for adoption; locally provable)

Strict reader per §9; ledger/session integrity per P7; the run's own invariants and
reachability; atomic single-writer document updates; and the per-surface execution
lock held for the whole recovery action.

## 13. `evidence_sha256` (F10)

`evidence_sha256` is the digest of the **canonical metadata-only evidence set** used
by a resolution; it is deterministic and contains no prompt/response/reasoning text.

* **Fields, in exactly this order:**
  `["devrelay-evidence-v1", run_id, schema_version, state, current_cycle,
  completed_cycles, model_turns_used, turn_attempts, attempt.role, attempt.cycle,
  attempt.prompt_sha256, attempt.prompt_chars, attempt.resolved_model,
  attempt.resolved_agent, attempt.route_source, attempt.started_at,
  attempt.call_ids…, ledger.call_id, ledger.state, ledger.http_status,
  ledger.submission_uncertain, ledger.response_media_type, ledger.completed_at,
  remote.message_id, remote.role, remote.created_at, remote.matched_digest]`
* **Ordering:** the listed field order; list fields (`attempt.call_ids`) in their
  recorded order.
* **Encoding:** UTF-8; each value serialized as a JSON scalar; fields joined with
  `"\n"`; no trailing newline; the **version marker** `devrelay-evidence-v1` is the
  first line so the canonical form can evolve explicitly.
* **Absent/null representation:** the empty string for absent strings, `null` for
  absent numbers/ids — never omitted (the position always exists).
* **Never hashed:** raw prompt text, provider response text, reasoning, credentials.
* **Repeated resolve after success — decision: B (stable local error).**  A second
  `resolve_recovery` for an already-resolved run returns the stable local error
  `orchestration_recovery_already_resolved` carrying the recorded resolution and
  `resolved_at`, and performs **no** write.  (Option A, "idempotent success", was
  rejected: a mutating tool must not report success for a write it did not
  perform.)

## 14. Pending results (P4) — report-only

Recorded independent-review conclusion (historical knowledge, **not** a formal proof
result): **OpenCode 1.18.11 exposes session-level status only; there is no durable
per-operation pending handle.**  The formal proof status of that question is the G0.4
step (§25/§28), which was **executed once** under its approved immutable revision-3 oracle
and was then independently approved as a **FAILED PROOF** (*APPROVE V0.3-E G0.4 FAILED
PROOF*; P0 = 0, P1 = 0, P2 = 0; **TYPE 3 — SEMANTIC ENVIRONMENT / CONFIGURATION RESULT**),
so **G0.4/P4 = FAIL / P4 UNPROVEN** (Case A could not bind a target instance: the accepted
workspace had no OpenCode base endpoint, so 0 `GET /doc` were issued —
`V03E_G0_4_API_INSPECTION_PROOF.md`; no API/schema property was established); the report-only
policy below applies regardless of whether G0.4 passes, fails or is never run.
Therefore, in the current v0.3-E scope:

* `reply_pending` is **report-only**: `reconcile` may report it as evidence;
* there is **no** pending-result adoption, **no** polling loop, **no** automatic
  wait, and **no** pending-driven state advance;
* a session that is merely `busy` never advances anything;
* if a future platform version exposes an operation handle, using it requires a new
  reviewed capability extension (new proof, new design).

## 15. Non-delivery classification (P5) — informational only

The accepted transport classification (`connect_error`, `connect_timeout`,
`pool_timeout` = pre-delivery; read/write timeouts and unusable 2xx bodies =
uncertain) is **reported as transport evidence only**.  It has **no execution
authority**: it never authorizes a submission, never authorizes a retry, never
refunds a slot, and never changes a run state by itself.  `mark_unrecoverable`
remains the only mandatory-core resolution, and a future retry protocol would need
a stronger, separately reviewed proof (including P5-class semantics and an
exclusivity proof) before it could exist at all.

## 16. Crash-window matrix (F11)

Ordering follows the accepted code: intent (run document) → ledger `ISSUED` →
request → response → ledger settle → turn finalization → MCP response.

| Window | Durable disk evidence | Possible remote evidence | Slot consumed? | `submission_uncertain`? | `reply_pending`? | Allowed action | Forbidden | Final safe state |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **W0** before durable intent | document unchanged | none | no | n/a | n/a | none needed | any recovery | unchanged |
| **W1** after intent, before HTTP submission | live intent; strict reader: no record in the proven interval | none | yes | no | no | `resolve_recovery` → `RECOVERY_REQUIRED` (reason `turn_interrupted`), then `mark_unrecoverable` | submission; refund; any side-effect entry | `RECOVERY_REQUIRED` → `BLOCKED` |
| **W2** during connection establishment | live intent; ledger record settled with a connect-phase state | none (reported only) | yes | no | no | as W1 (non-delivery is reported, never acted on) | auto-resubmit; treating the class as a retry licence | `RECOVERY_REQUIRED` → `BLOCKED` |
| **W3** request may have been delivered, before response headers | live intent; ledger record `ISSUED` (unsettled) or settled mid-transfer | unknown | yes | yes | unknown | `resolve_recovery` → `RECOVERY_REQUIRED` (reason `submission_uncertain`); reconcile may **report** a candidate; resolve may **only** `mark_unrecoverable` until the adoption gate passes | adoption without the gate; guessing from session busy/idle; any submission | `RECOVERY_REQUIRED` → `BLOCKED` (adoption only if gated) |
| **W4** *(added)* response received / local bridge result exists, **ledger settle not durably written** | live intent; ledger record still `ISSUED` (or an unreadable settle → `evidence_gap`) | the provider's reply exists | yes | no | no | as W3: report + `mark_unrecoverable`; adoption only under the gate, and then only if the strict reader proves the settle record (an unreadable settle is `evidence_gap`, not a match) | treating an in-memory result as durable evidence; adoption on `evidence_gap` | `RECOVERY_REQUIRED` → `BLOCKED` |
| **W5** ledger settled, assistant identity not yet captured | live intent; settled `COMPLETED` record | assistant message exists | yes | no | no | report; adoption only under the full §11 gate; otherwise `mark_unrecoverable` | "ledger COMPLETED ⇒ finished turn" | `RECOVERY_REQUIRED` → `BLOCKED` (or adopted, gated) |
| **W6** result known locally, completed turn not persisted | live intent; settled record | assistant message exists | yes | no | no | as W5 | issuing any provider call | as W5 |
| **W7** completed turn persisted, MCP response not returned | no intent; the finished turn is in the document | n/a | yes | recorded | recorded | none (the document is already the truth); the client re-reads | re-running the phase | unchanged truthful state |

No cell authorizes behaviour forbidden elsewhere; every "adoption" cell is
conditioned on the §11 gate, and every window's mandatory-core action ends in
terminal `BLOCKED`.

## 17. Restart matrix

| Persisted situation | After restart | Allowed | Forbidden |
| --- | --- | --- | --- |
| `READY_IMPLEMENTER` / `READY_REVIEWER`, no intent | unchanged | the normal phase action | nothing new |
| `READY_IMPLEMENTER` / `READY_REVIEWER` + live intent (v2) | unchanged; `get_run` reports `in_flight: true`, `legal_next_actions = ["devrelay_resolve_recovery"]` | explicit `resolve_recovery` (entry per §7) | phase/decide calls (they refuse without mutating); any submission |
| `RECOVERY_REQUIRED` | persisted state | `reconcile` (read-only), `resolve_recovery` | model calls; automatic work |
| `AWAITING_DECISION` | unchanged | `decide_run` | phases |
| `BLOCKED` / `COMPLETED` / `STOPPED` / `LIMIT_REACHED` | unchanged | read-only | recovery and phases |
| v1 document with live intent | accepted v0.3-D behaviour | its next mutating action materializes `BLOCKED`/`turn_interrupted` | v0.3-E recovery entry |
| uncertain submission / pending reply (v2) | `RECOVERY_REQUIRED` | report + `mark_unrecoverable` | adoption without the gate; waiting loops |

No restart performs work, creates budget, refunds a slot or issues a request.

## 18. Retry wording (F9) and the no-retry guarantee

A wording rule for this design and its future implementation:

* bridge-level `retry_safe` is **accepted v0.3-A transport metadata**: it says
  whether *DevRelay could re-issue a request at the bridge level*.  It has **no
  orchestration recovery authority** — recovery never reads it, it never gates an
  action, and it never authorizes a submission.
* v0.3-E contains **no retry protocol**: no automatic retry, no retry tool, no
  "try again" / "resubmit" / "resume submission" behaviour — **no recovery
  resolution submits a model turn**, and no resolution may cause a submission
  indirectly (no phase call, no auto-resume, no background work).
* the words *retry* / *retryable* / *resubmit* appear here only in negated form or
  as the name of the accepted bridge field explicitly excluded from recovery
  authority.
* a future retry protocol would require its own design, proof gate and independent
  review; it is not implied, planned or pre-authorized by v0.3-E.

## 19. Capability dependency table

| Capability | Remote platform proofs | Local requirements | Consequence if unavailable |
| --- | --- | --- | --- |
| **A — reconcile/report** | none (remote reads are optional and report-only) | strict recovery evidence reader (§9) implemented and correct; **G0.1 / P7 must PASS before core implementation is authorized** | the local prerequisite is now **satisfied** (**G0.1 / P7 = PASS**, authoritative and independently approved, §25/§28); had it failed, mandatory-core implementation would have remained **blocked** (there is no degraded-implementation path).  `evidence_gap` is a *runtime* fail-closed outcome for an individual ambiguous/corrupt/unproven evidence case **after** implementation - it is never a waiver of the G0.1/P7 gate |
| **B — `mark_unrecoverable` → `BLOCKED`** | **none** | legal recovery entry/document (§7), planner authority, local invariants, no corruption | none: this is the fail-closed safety exit and is always available |
| **C — `adopt_completed_turn`** | remote/platform ***enabling* proofs: P1 + P2 + P3 + P8** (+ **P9** if timestamps/order are used), through G1/G2 — a **distinct class** from the local veto bound below | the core's prerequisite (G0.1 / P7 PASS) plus the §11 checklist, **plus the local identity/ownership *veto bound* P6 / G0.5 (§12.4, §25.1)** | capability stays disabled; resolve refuses it; reconcile reports candidates only.  **Both classes must be satisfied: an unsatisfied or failed P6 veto keeps adoption disabled even if G1/G2 later pass, and P6 PASS alone enables nothing** |
| **D — pending-result handling** | would require an operation-specific handle proof | — | **report-only in v0.3-E**; no mutation capability |
| **E — non-delivery classification** | would require a P5-class proof for any authority | — | informational only; no orchestration authority |

## 20. `RECOVERY_REQUIRED` state summary

| Aspect | Value |
| --- | --- |
| Nature | **non-terminal**, execution-frozen (no model-bearing action, no `decide_run`, no automatic anything) |
| Entry | exactly one explicit planner action: `devrelay_resolve_recovery` on a valid v2 live-intent document or on an existing `RECOVERY_REQUIRED` document (§7) |
| Reasons (vocabulary) | `turn_interrupted`, `submission_uncertain`, `reply_pending` |
| Legal exits | `mark_unrecoverable` → `BLOCKED`; `adopt_completed_turn` (gated) → `READY_REVIEWER` / `AWAITING_DECISION` |
| Model calls | **zero**, for every action |
| Restart | persisted; reconciliation idempotent; no work on restart |
| `legal_next_actions` | `["devrelay_reconcile_run", "devrelay_resolve_recovery(mark_unrecoverable)"]` (+ `adopt_completed_turn` when the capability is enabled) |

## 21. MCP tool surface (minimum, not implemented)

1. `devrelay_reconcile_run(run_id)` — **read-only** report: legal for any
   non-terminal v2 document (including a live-intent document) and for
   `RECOVERY_REQUIRED`; refuses locally for terminal states and for v1 documents
   (report-only, no mutation); returns the attempt identity, strict-reader result,
   session-history candidates, the per-item checklist with pass/fail/unknown, and
   the blockers.  No durable mutation, no model call, idempotent by construction.
2. `devrelay_resolve_recovery(run_id, resolution)` — the **only** recovery write;
   legal exactly per §7; `resolution ∈ {mark_unrecoverable, adopt_completed_turn}`;
   `adopt_completed_turn` is refused unless the capability is enabled and §11
   passes; performs no provider call; one atomic write; a repeat after success
   returns `orchestration_recovery_already_resolved` with the recorded outcome
   (§13).

Both run under the accepted per-surface execution lock.  `devrelay_get_run` stays
**read-only**.  No tool performs a phase turn, waits, polls or retries.

## 22. Privacy, concurrency, budget

* **Privacy:** digests, ids, roles, timestamps and metadata only; the recovery
  record keeps `evidence_sha256` and matched message ids, never message text; no
  prompt/response/reasoning/credential is persisted; session-history text is
  transient in memory for digest comparison and redacted as the accepted bridge
  does.
* **Concurrency:** recovery actions share the accepted per-`McpToolSurface`
  execution lock; multi-surface/multi-process same-workspace coordination remains
  **unsupported** and no part of v0.3-E claims a process-wide lock; a crash during
  recovery leaves either the pre- or the post-recovery document.
* **Budget:** `model_turns_used`/`turn_attempts` semantics unchanged; the §8.3
  equations are the only accounting; no refund, no reset, no recomputation, no
  restart budget.

## 23. Non-goals

Automatic retry · automatic planner decisions · automatic role sequencing ·
provider/model fallback · automatic interrupt or resubmission · pending-result
adoption · distributed multi-process/multi-surface locking · cross-machine
recovery · background daemon or scheduler polling · WebUI recovery UI · HTTP
control plane · release/version bump · automatic resume without explicit planner
action · parsing model output · repairing corruption · reconstructing lost prompts
or replies · heuristic or probabilistic attribution.

## 24. Test strategy (designed, not implemented)

* deterministic offline crash-window kills W0–W7 with the real service/router/bridge
  against the stub, asserting the §8 shape after each entry;
* entry tests: the explicit `resolve_recovery` entry (both input shapes) plus the
  assertion that phase/decide calls refuse **without mutating** on a v2 live-intent
  document;
* accounting tests: the §8.3 equations before/at/after every resolution, including
  "the recovery attempt is counted exactly once";
* strict-reader tests: unreadable/torn/unparsable records → `evidence_gap`; the
  newest-N accounting window never used as proof of absence; interval proof;
* corruption tests: every invariant violation outside the enumerated deltas →
  `orchestration_state_corrupt`, no entry, no override, byte-identical document;
* adoption-gate tests: every §11 item individually false → refuse; the checklist is
  never satisfiable while the capability flag is off;
* `mark_unrecoverable` independence: works with no session history at all and with
  a missing/foreign session;
* no-submission assertions: the prompt-POST count and `external_request_count` are
  unchanged across every recovery scenario;
* terminal immunity, restart matrix, v1/v2 dispatch, privacy scans, and mutation
  tests for the recovery-critical invariants;
* a production-generated honest recovery corpus (cases A–H plus fake remote
  evidence variants) with a per-mutation differential battery;
* zero real provider/model calls during unit/integration testing.

## 25. Platform proof gate (partially executed — not complete)

**Current gate status (updated after the G0.1/P7 execution and the G0.2 offline
run):** platform proof gate = **PARTIALLY EXECUTED / NOT COMPLETE**.  **G0.1 / P7 =
PASS** (authoritative, independently approved: the final proof review issued *APPROVE
V0.3-E G0.1 / P7 PLATFORM PROOF* with P0 = 0, P1 = 0, P2 = 0 — this PASS comes from
that independent review of the proof candidate, never from executor self-approval);
**G0.2 = PASS** (authoritative, independently approved: the clean-rerun review issued
*APPROVE V0.3-E G0.2 FALSE-CORRELATION PROOF* with P0 = 0, P1 = 0, P2 = 0 — this PASS
comes from that independent review, never from executor self-approval; the original
round was reviewed once with `REQUEST_CHANGES` and then cleanly re-run under the oracle
precommitted in commit `12ea1b7`; the ten fixed cases A-J ran once each and failed
closed: a unique `MATCH` only when the complete identity tuple matches exactly one
record in the run's role session, otherwise `NO_MATCH` / `evidence_conflict` /
`evidence_gap` / `corruption`; no timestamp tie-break; the oracle was unchanged during
execution; 0 provider/model calls — `V03E_G0_2_CLEAN_RERUN_PROOF.md`; original round:
`V03E_G0_2_FALSE_CORRELATION_PROOF.md`);
**G0.3 / P5 = PASS** (authoritative, independently approved through *APPROVE V0.3-E G0.3 / P5 TRANSPORT PROOF*, P0 = 0, P1 = 0, P2 = 0 — corrected clean rerun
executed once under the oracle precommitted in `e328ec5`, one semantic execution per case:
the accepted safe buckets — `connect_timeout`, `pool_timeout`, `connect_error`,
`unsupported_protocol`, and the pre-send-only `local_protocol_error` mapping boundary —
are **class-wide pre-send** on the installed stack with no request header or body byte on
the wire; `proxy_error` is **UNREACHABLE_CURRENT_CONFIGURATION** (`trust_env=False`, no
reviewed proxy configuration; the synthetic demonstration carries no current-production
evidence); every uncertain class (`read_timeout`, `write_timeout`, `read_error`,
`remote_protocol_error`, `close_error`) stayed `submission_uncertain == true` with
`retry_safe == false`; corrected case **G0.3-J** surfaced `remote_protocol_error` exactly
as precommitted (httpcore suppresses the request-send `WriteError`, which remains a
defensive, unexercised mapping); HTTP rejection and success were never non-delivery; P5
evidence remains informational only — `V03E_G0_3_CLEAN_RERUN_PROOF.md`; the original failed
round is preserved as **CANDIDATE FAIL** with its independent TYPE-1 review outcome —
`V03E_G0_3_TRANSPORT_PROOF.md`),
**G0.4/P4 = AUTHORITATIVE FAIL / P4 UNPROVEN** (executed once under the approved immutable revision-3 oracle; independently approved failed proof — *APPROVE V0.3-E G0.4 FAILED PROOF*, P0 = 0, P1 = 0, P2 = 0, TYPE 3 — SEMANTIC ENVIRONMENT / CONFIGURATION RESULT; Case A could not bind a target instance — no OpenCode base endpoint configured, so 0 loopback HTTP requests / 0 `GET /doc` and cases B–H were not executed — `V03E_G0_4_API_INSPECTION_PROOF.md`), **G0.5 = NOT RUN**,
**G1 = NOT RUN**, **G2 = NOT RUN**.  The design's local hard prerequisite is
therefore **satisfied**: G0.1/P7 **no longer blocks mandatory-core implementation
eligibility**, but implementation remains **NOT AUTHORIZED** until a separately
issued implementation authorization.  `adopt_completed_turn` = **DISABLED**.  G0.1/P7
and G0.2 are authoritative PASS and mandatory-core implementation remains **NOT
AUTHORIZED** pending a separate authorization; neither PASS, alone or together,
authorizes implementation, and the executing agent did not self-approve either.  The
platform proof gate is **PARTIALLY EXECUTED** — **not** passed and **not** complete
(G0.3/P5 = PASS/CLOSED; G0.4/P4 was executed once and is **AUTHORITATIVE FAIL / P4
UNPROVEN**; G0.5/G1/G2 remain unrun), and no part
of this status may be read as an implementation or smoke authorization.

To be executed **before any implementation** that trusts remote/local recovery
evidence.  Maximum real provider/model calls: **0** (a local fake
OpenAI-compatible provider may be used in G2; nothing runs in this design round).

| Step | Purpose | Real provider calls | Scope |
| --- | --- | --- | --- |
| **G0.1** | local DevRelay hard-kill around `ISSUED`/settle writes; the strict reader must return a complete valid record or `evidence_gap`/corruption, never silently skip (**P7/F5**) | 0 | local |
| **G0.2** | offline run↔call false-correlation cases (two runs, reused prompts, reused sessions, neighbouring call ids) | 0 | local |
| **G0.3** | transport/non-delivery classification checks against the accepted taxonomy (**P5**) — original round candidate FAIL (case G0.3-J surfaced `remote_protocol_error`), independently reviewed as a TYPE-1 proof-plan failure, then corrected and cleanly re-run, and the corrected proof was independently approved: **G0.3 / P5 = PASS** (authoritative; accepted safe buckets class-wide pre-send; `proxy_error` `UNREACHABLE_CURRENT_CONFIGURATION`; every uncertain class fail-closed) | 0 | local/fake transport |
| **G0.4** | OpenCode installed-API inspection for a per-operation pending handle (**P4**) — **AUTHORITATIVE FAIL / P4 UNPROVEN**: the single authorized execution under the approved immutable revision-3 oracle (`V03E_G0_4_API_INSPECTION_ORACLE.md`, committed-blob SHA-256 `b0c34fa1…`) was independently approved as a **FAILED PROOF** (*APPROVE V0.3-E G0.4 FAILED PROOF*, P0 = 0, P1 = 0, P2 = 0, **TYPE 3 — SEMANTIC ENVIRONMENT / CONFIGURATION RESULT**).  Case A did not reach `TARGET_BOUND` (`TARGET_IDENTITY_UNRESOLVED` — the accepted workspace had no OpenCode base endpoint), so 0 loopback HTTP requests / 0 `GET /doc` were issued and cases B–H were not executed; no API/schema property was established and a rerun is not authorized (`V03E_G0_4_API_INSPECTION_PROOF.md`) | 0 | read-only inspection |
| **G0.5** | P6 **local identity/ownership veto bound** on adoption — four case classes A–D (missing, foreign, recreated/originality-unprovable, copied); frozen definition in **§25.1**; **NOT RUN** (definition remediated, awaiting independent definition review) | 0 | local (offline) |
| **G1** | real **LOCAL** OpenCode `1.18.11` session-history restart proof (**P1**: durability of ids/text across a server restart) | 0 | local OpenCode, no inference |
| **G2** | real **LOCAL** OpenCode + **local fake OpenAI-compatible provider**: submitted-text fidelity (**P2**), duplicate-identical-prompt uniqueness (**P3**), session-exclusivity assumptions as far as observable (**P8**), timestamp/order fidelity if used (**P9**) | 0 | local fake provider |

Rules: **no probe shopping** — one planned probe per case; a failed proof *removes*
the gated capability instead of triggering another probe; results are recorded in
`V03E_ACCEPTANCE.md`, whose implementation rows stay FUTURE / NOT RUN until then.
Harness-invalid attempts (a case that never reached its assertion point because of a
harness defect) are recorded separately and excluded; a case is never re-run to search
for a passing configuration.

**G0.1 / P7 was the hard gate on the mandatory core, and the only such gate.**
Implementation ordering is: **design frozen → G0.1 / P7 PASS → mandatory-core
implementation may be authorized.**  The second step is now **satisfied**: the proof
was executed once and the final independent proof review issued *APPROVE V0.3-E
G0.1 / P7 PLATFORM PROOF* (**P0 = 0, P1 = 0, P2 = 0**), so **G0.1 / P7 = PASS**
(authoritative, independently approved).  Had G0.1 / P7 failed, mandatory-core
implementation would have remained **BLOCKED**; there is **no
degraded-implementation path** in this design (a degraded scope would need its own
design change and independent review).  The PASS satisfies the local prerequisite but
authorizes nothing by itself: implementation still requires a separately issued
authorization.  G0.4 remains relevant to the reporting language (what the recovery
report may claim), and G0.5/P6 defines the local identity/ownership **veto bound** on
adoption (§25.1); neither may blur that gate.  **G1/G2 provide the optional adoption
capability's remote/platform *enabling* proofs, while G0.5/P6 separately proves the local
identity/ownership *veto bound*; both classes must be satisfied before adoption may ever be
authorized (§11 item 8, §19 row C, §25.1), and neither enables adoption by itself.**
Maximum real provider/model inference for the
whole gate: **0**.

G0.1 / P7 proves the *local persistence/ledger assumptions* the future
implementation is allowed to rely on (hard kills around `ISSUED`/settle
boundaries, valid records distinguishable from torn/corrupt/incomplete state,
fail-closed `evidence_gap`/corruption processing, no silent skipping treated as
authoritative).  It does **not** prove the future production implementation itself:
that implementation still needs its own tests.

### 25.1 G0.5 / P6 — frozen local identity/ownership veto-bound definition (definition only; not executed)

**Role (normative).**  P6 is a **local identity/ownership veto bound for adoption** — **not**
an adoption-enabling proof.  **G0.5 PASS clears only the local P6 veto prerequisite** and
enables nothing by itself; **G0.5 FAIL leaves the P6 veto active** and adoption stays
**DISABLED**.  Neither outcome affects: reconcile/report (A), `mark_unrecoverable` (B),
G0.1/P7, the pending/report-only policy, G1's ability to characterize P1, or G2's ability to
characterize P2/P3/P8/P9.  The remote/platform adoption **enabling** proofs remain
**P1 + P2 + P3 + P8** (+ **P9** only when timestamp/order correlation is used) through
**G1/G2**.

**Exact P6 question.**  *Can DevRelay's locally available session identity/ownership
evidence safely establish the original owned-session bound for recovery, such that missing,
foreign, recreated, copied, or otherwise unprovable session references can never clear the
adoption identity veto?*  The question is about **safe local bounding**, not about
**positive remote session identity**, and P6 does **not** require proving global uniqueness
of OpenCode session ids.

**Definitions.**
* **Session identity (P6 sense)** — the remote OpenCode session reference, principally
  `session_id`, treated strictly as an **opaque remote identifier**.  It identifies a
  referenced remote session record and is necessary as a reference, but it is **not by
  itself** proof that the referenced session is the original DevRelay-owned session, **not**
  proof of workspace ownership, **not** proof against recreation/reuse, and **not** proof of
  one submitted turn.  No OpenCode uniqueness property may be claimed that has not been
  formally proved.
* **Session ownership (P6 sense)** — the **local recovery claim** that the referenced remote
  session is sufficiently bound to the original DevRelay recovery context for the identity
  veto to clear.  Ownership evidence uses only the frozen locally available checks:
  configured/stored `session_id` reference; workspace binding / `workspace_match` and the
  configured workspace root; role/session distinctness; the persisted route/session
  snapshot; applicable stored DevRelay recovery/ledger identity.  **No single field alone
  proves ownership**; in particular **`session_id` equality alone MUST NOT clear the P6
  veto**.
* **Original-owned-session rule (fail closed)** — if DevRelay cannot prove, using the
  permitted local evidence model, that the current reference is consistent with the original
  owned recovery session, the P6 result for that recovery context is **IDENTITY / OWNERSHIP
  NOT PROVEN** and **adoption remains unavailable**.  This may never be converted into
  "probably the same session" or "same id, therefore owned".

**Scope and exclusions.**  G0.5 scope is **local**.  Explicitly **excluded** (each owned by
another proof): OpenCode restart persistence and history/text survival across restart →
**G1/P1**; verbatim completion-text fidelity → **G2/P2**; identical-prompt/completion
uniqueness → **G2/P3**; session exclusivity / concurrent-writer proof → **G2/P8**;
timestamp/order fidelity → **G2/P9**; per-operation pending handle → **G0.4/P4**; local
durable state correctness → **G0.1/P7**.  G0.5 must not absorb any of them.

**Restart boundary.**  G0.5 performs **no** OpenCode restart and makes **no** conclusion
about session identity surviving an OpenCode restart; any cross-OpenCode-restart
identity/history claim belongs to **G1/P1**.  DevRelay's own persisted local session
reference may exist across a local process restart, but that fact alone is **not** a P6 proof
of the remote session's originality.

**Four precommitted case classes (exactly four; normative).**

| Case | Definition | Expected bound |
| --- | --- | --- |
| **G0.5-A — MISSING** | the persisted recovery context refers to a session that cannot be resolved as the required original session (missing session reference; session-not-found; required local session identity field absent) | original ownership **NOT PROVEN** → veto active; report/reconcile remains available; `mark_unrecoverable` remains available; no remote-completion claim |
| **G0.5-B — FOREIGN** | the referenced session resolves to evidence inconsistent with the recovery workspace/ownership context (workspace mismatch; foreign workspace; workspace identity unavailable where strict ownership requires it; other locally provable ownership mismatch) | ownership **NOT PROVEN / FOREIGN** → veto active; no adoption; no remote-completion claim |
| **G0.5-C — RECREATED / ORIGINALITY-UNPROVABLE** | the current remote reference presents the same or otherwise plausible identifier/context, but the permitted evidence cannot establish that it is the original owned session rather than a recreated/replaced/reused one | **`session_id` equality alone is insufficient**; same id + same apparent workspace alone must not be promoted to proof of original-session identity unless another separately accepted proof supplies that authority; if originality cannot be established → **IDENTITY / OWNERSHIP NOT PROVEN** → veto active.  G0.5 does **not** need to prove that OpenCode actually reuses ids, and no id-reuse claim may be invented: the case proves the bound against the **possibility** that the available local evidence cannot distinguish original from recreated |
| **G0.5-D — COPIED** | DevRelay recovery/run/ledger identity material is copied or replayed into a different workspace or incompatible route/recovery context | workspace/route/ownership consistency fails → veto active; a copied run document/reference must not become recoverable merely because the same remote `session_id` appears |

No fifth semantic case may be added at definition level; the later oracle may instantiate
exact fixtures for these four classes.

**PASS semantics (bounding PASS).**  PASS means: the permitted local identity/ownership
evidence model and its fail-closed rules are sufficient to establish that **all four case
classes cannot clear the P6 adoption veto** when original ownership is missing,
contradictory or unprovable.  PASS does **not** mean: OpenCode session ids are globally
unique; ids cannot be recreated; ids survive restart; an id proves ownership; OpenCode
guarantees workspace binding; identity proves one submitted turn; or adoption is enabled.
A PASS clears **only** the P6 local identity-veto prerequisite; G1/G2 remain separately
required before adoption may ever be authorized.

**FAIL semantics.**  FAIL occurs if the proof shows that any of the four case classes can
clear — or cannot be shown to remain behind — the P6 adoption veto under the frozen local
evidence model (examples: `session_id` equality treated as sufficient ownership; a
foreign/copy mismatch accepted; a recreated/originality-unprovable state treated as
original; a required ownership contradiction ignored; an evidence model insufficient to
establish the fail-closed bound).  Consequence: **P6 remains UNSATISFIED**,
`adopt_completed_turn` remains **DISABLED**, no degraded adoption mode, no automatic retry
and no alternative identity heuristic; the mandatory core and `mark_unrecoverable` are
unaffected; G1/G2 may still be characterized, but even a future G1/G2 PASS cannot enable
adoption while P6 remains unsatisfied.

**Insufficient-evidence semantics.**  If the future proof cannot determine whether the local
P6 bound holds, uncertainty is **not** PASS: the result must **preserve the veto**
(P6 not satisfied → adoption remains DISABLED), with no optimistic inference.  The later
oracle may fix the exact final-result vocabulary.

**Method — local offline only.**  The proof method class is **local offline deterministic
identity-bound characterization**.  Allowed: repository/source inspection; deterministic
local invocation of already-existing DevRelay identity/ownership primitives; deterministic
local fixtures/stubs representing session metadata and recovery/workspace context; existing
local unit-level harnesses that require no network or external service; local file/state
inspection; local hashing and evidence recording.  Not allowed: live OpenCode HTTP; `/doc`;
`/session` API calls; prompt submission; session creation; session deletion; OpenCode
process discovery; port scanning; OpenCode start/restart; provider/model calls; fake
provider; external network; changing `opencode.base_url`.  Consequently the missing
configured `base_url` observed in G0.4 is **not** a prerequisite or blocker for G0.5.

**Live-OpenCode non-claim.**  Because G0.5 is offline/local, it proves **DevRelay's local P6
identity/ownership bound** and **not** actual OpenCode platform guarantees about id
uniqueness, id reuse, server lifetime, restart persistence or session-database semantics;
those require their separately owned proofs or a future capability extension.  Installed
binary string counts are **contextual only** and may not drive PASS.

**Budget (frozen).**  real provider calls **0**; fake provider calls **0**; model inference
calls **0**; model turns **0**; prompt submissions **0**; HTTP requests **0**; loopback HTTP
requests **0**; external network requests **0**; OpenCode starts **0**; OpenCode restarts
**0**; OpenCode session mutations **0**.  The proof is entirely local/offline.

**Identity-dimension matrix (normative).**

| Dimension | Classification |
| --- | --- |
| session_id as opaque reference | **REQUIRED** |
| workspace binding | **REQUIRED** |
| original-ownership bound | **REQUIRED** |
| role/session distinctness | **REQUIRED where applicable to the recovery route** |
| persisted route/session snapshot consistency | **REQUIRED** |
| foreign-session detection | **REQUIRED** |
| copied-workspace/context detection | **REQUIRED** |
| session_id global uniqueness | **NOT CLAIMED / OUT OF SCOPE** |
| session_id uniqueness across OpenCode instances | **NOT CLAIMED / OUT OF SCOPE** |
| session_id reuse impossibility | **NOT CLAIMED / OUT OF SCOPE** |
| OpenCode restart persistence | **OWNED BY G1/P1** |
| verbatim text fidelity | **OWNED BY G2/P2** |
| prompt/completion uniqueness | **OWNED BY G2/P3** |
| session exclusivity | **OWNED BY G2/P8** |
| timestamp/order fidelity | **OWNED BY G2/P9** |
| per-operation pending handle | **OWNED BY G0.4/P4** |
| turn correlation | **not supplied by P6 alone** |

**Discipline (no probe shopping).**  Exactly **one** planned semantic execution per case
A–D.  The later oracle must precommit, per case: the exact local fixture/input; the exact
DevRelay primitive/path inspected or invoked; the expected fail-closed identity result; the
expected adoption-veto consequence; the assertion point; and the harness-invalid boundary.
A semantic failure must not be retried with a different fixture to obtain PASS; fixtures may
not be modified after observing a semantic result; harness-invalid attempts (failure before
the precommitted assertion point) may be retried, must be recorded separately and are
excluded from the semantic case count.

**Minimum evidence fields (future oracle/proof).**  Repository HEAD/branch/worktree; frozen
definition/oracle identity; case identifier A–D; local fixture identity; stored
`session_id`/reference; stored/configured workspace identity; returned/synthetic session
workspace identity as applicable; `workspace_match`/ownership verdict; route/session
snapshot consistency as applicable; role/session distinctness verdict as applicable;
original-ownership-provable verdict; expected P6 veto result; observed local result;
adoption-veto consequence; mandatory-core-unaffected confirmation; activity counters;
privacy/non-claims; harness-invalid vs semantic outcome.  Live remote-session data is **not**
required.

**Privacy.**  Future G0.5 evidence must not persist credentials, tokens, raw prompts, model
responses or reasoning; synthetic/non-secret local identifiers should be used in fixtures
where possible; environment-specific paths may be recorded only when materially needed and
must be labelled environment-derived.

**Status model.**  `G0.5 = NOT RUN` → after a separately authorized execution **CANDIDATE
PASS** or **CANDIDATE FAIL / P6 UNSATISFIED** → independent review → authoritative PASS or
authoritative FAIL.  The executing agent never self-approves, and a PASS/FAIL does not by
itself authorize adoption or implementation.

**Mandatory-core consequence.**  G0.5/P6 is **not** the mandatory-core hard gate; the hard
prerequisite remains **G0.1/P7 = PASS / CLOSED**.  Any G0.5 outcome does not revoke G0.1,
does not block reconcile/report, does not block `mark_unrecoverable`, does not authorize
mandatory-core implementation and does not create a degraded mode.

**Adoption dependency equation.**  Adoption may be **considered** only if: the P6 local
identity/ownership veto bound is **SATISFIED** by an independently approved G0.5; **and** the
required remote/platform adoption **enabling** proofs P1 + P2 + P3 + P8 (+ P9 if applicable)
are independently satisfied through G1/G2; **and** all other frozen runtime/adoption
invariants hold; **and** a separate external implementation/feature authorization is issued.
No single proof enables adoption: **P6 PASS alone enables nothing**, and **G1/G2 PASS alone
cannot bypass P6**.

## 26. Future real acceptance smoke (not authorized)

Only if `adopt_completed_turn` survives the proof gate may a later acceptance smoke
use **exactly one** real model turn to prove: remote completion → controlled local
persistence interruption → restart → explicit reconcile → explicit resolve/adopt →
**no duplicate provider call**.  If adoption is removed or disabled after failed
proofs, **no real adoption smoke is required**: the reduced core (report +
`mark_unrecoverable`, fully local) may be accepted without any real model call.

## 27. Design decisions table

| Topic | Decision | Reason | Safety invariant | Open question |
| --- | --- | --- | --- | --- |
| Scope split | mandatory core (report + `mark_unrecoverable`; no submission, no retry, no auto-resume, no adoption) vs optional gated adoption | optional capabilities must never block the fail-closed core | the core never submits; failure is always a legal terminal `BLOCKED` | none (decision closed) |
| Entry into recovery | exactly one explicit action (`resolve_recovery`, both input shapes); no side-effect transitions | the review's P0: a read-only-only path could never create the state | every entry has a named legal action; no transition from an invalid action | none (decision closed) |
| Attempt representation | one `recovery.attempt` record, converted once into exactly one role turn at resolution | avoids a blocked turn inside a non-`BLOCKED` run and the append-vs-rewrite contradiction | never two role records for one role/cycle | none (decision closed) |
| Corruption | never recovery: violations outside the enumerated deltas → corrupt | recovery must not become a repair path | no planner override; no repair | none (decision closed) |
| Evidence absence | strict reader with interval proof; absence is never proof of non-delivery | silently skipped or unreadable records would fake certainty | no inference from missing evidence | none (decision closed) |
| Adoption | optional; requires **BOTH** the independently satisfied P6/G0.5 **local identity/ownership veto bound** (§25.1) **AND** the P1+P2+P3+P8 (+P9 when applicable) **remote/platform *enabling* proofs via G1/G2**; report-only until then | the earlier checklist did not prove attribution, and identity/ownership neither enables adoption nor may be skipped | resolve refuses adoption without the gate | will the proofs be attainable at all? (the gate decides) |
| Pending | report-only; no handle exists in 1.18.11 | no durable per-operation handle | no polling, no waiting, no advance | a future platform handle would need a new capability review |
| Non-delivery | informational only | a transport class must never create a free retry | no orchestration authority | a retry design would need stronger proof |
| Schema | version dispatch (v1 frozen / v2 v0.3-E / else corrupt); no migration | one equality check cannot implement the compatibility policy | no silent default, no migration, no rewrite | none (decision closed) |
| `evidence_sha256` | canonical metadata-only field list with a version marker; repeat resolve → stable `already_resolved` error | determinism, and no false success from a mutating tool | no raw text hashed; no second write | none (decision closed) |
| Budget | the §8.3 equations; a slot is never refunded | preserves accepted accounting | the recovery attempt is counted exactly once | none (decision closed) |
| Terminal | never enters recovery, never reopens | preserves v0.3-D terminal semantics | terminal immunity | none (decision closed) |
| Identity | workspace/session/role/snapshot re-verified; P6 is a **local fail-closed identity/ownership veto bound** on adoption — "gate" here means **veto bound, never positive capability enablement** | a copied or recreated session must not be adopted | explicit ownership; distinct sessions | P6 strength (proof) — definition frozen in §12.4/§25.1; G0.5 NOT RUN |
| Concurrency | per-surface lock; multi-surface/multi-process unsupported | no new locking model, no false claims | one lock per surface | none (decision closed) |
| Privacy | digests/ids/metadata only | preserves the v0.3-D privacy contract | no prompt/response/reasoning/credential persistence | P2 fidelity is a platform question |

## 28. Open questions and proof status

| Proof | Question | Gates | Status |
| --- | --- | --- | --- |
| P1 | does session history survive an OpenCode server restart with the same ids/text? | adoption (C); reporting quality | PROOF REQUIRED (G1) |
| P2 | is the submitted user text preserved verbatim so the digest match is sound? | adoption (C) | PROOF REQUIRED (G2) |
| P3 | can identical prompts in one session be disambiguated deterministically? | adoption (C) | PROOF REQUIRED (G2) |
| P4 | does a durable per-operation pending handle exist? | pending capability (D) | **historical review answer** for 1.18.11: no (session-level status only) — report-only, and **not** a formal G0.4 result; **formal proof status: G0.4/P4 = AUTHORITATIVE FAIL / P4 UNPROVEN** (independently approved failed proof — *APPROVE V0.3-E G0.4 FAILED PROOF*, P0 = 0, P1 = 0, P2 = 0, TYPE 3; no configured endpoint → no target instance bound → 0 `GET /doc`, no API/schema property established; `V03E_G0_4_API_INSPECTION_PROOF.md`) |
| P5 | do the accepted connect-phase classes prove non-delivery? | non-delivery authority (E) | **executed under G0.3: **PASS** (authoritative, independently approved through *APPROVE V0.3-E G0.3 / P5 TRANSPORT PROOF*, P0 = 0, P1 = 0, P2 = 0) in the corrected clean rerun under the oracle precommitted in `e328ec5`: the accepted safe buckets are class-wide pre-send (`connect_timeout`, `pool_timeout`, `connect_error`, `unsupported_protocol`) plus the pre-send-only `local_protocol_error` mapping boundary, `proxy_error` is `UNREACHABLE_CURRENT_CONFIGURATION`, and every uncertain class stayed fail-closed; the original round's candidate FAIL (case G0.3-J surfaced `remote_protocol_error`; the request-send `WriteError` mapping is defensive/unexercised) and its independent TYPE-1 review remain historical; P5 stays informational/report-only (`V03E_G0_3_CLEAN_RERUN_PROOF.md`) |
| P6 | can DevRelay's **locally available** session identity/ownership evidence safely establish the original owned-session bound for recovery, such that missing, foreign, recreated, copied, or otherwise unprovable session references can never clear the adoption identity veto? (**not** a global session-id uniqueness question — §25.1) | adoption (C) — as a **fail-closed veto bound only**, not an enabling proof (enabling proofs are P1+P2+P3+P8 (+P9) through G1/G2) | PROOF REQUIRED (G0.5); **definition remediated (§25.1), awaiting independent definition review**; bounds adoption now |
| P7 | is the ledger settle record complete-or-absent under a hard kill? | all ledger-trusting logic | **PASS** (authoritative, independently approved; executed once under G0.1 — `V03E_G0_1_P7_PROOF.md`; local, 0 provider calls) |
| P8 | can session exclusivity (no other writer in the window) be established? | adoption (C) | PROOF REQUIRED (G2 + local cross-checks) |
| P9 | is `created_at`/ordering fidelity sufficient if timestamps are used? | adoption (C) *only if* timestamps are used | PROOF REQUIRED (G2) |

### Recorded P3 observations (non-blocking; do not block design freeze)

* **P3-1** — `evidence_sha256` includes timestamp-derived metadata, but digest
  equality has **no identity authority** and must not be treated as timestamp
  fidelity proof (that would require P9).
* **P3-2** — "directly associated assistant message" remains a **proof-gated
  platform assumption** (it is part of the optional adoption gate, not of the
  mandatory core).
* **P3-4 / P3-5** — minor clarity observations recorded by the reviewer around
  summary wording; they are informational and require no design change for freeze.
* **Proof-review P3 notes (G0.1/P7 round, non-blocking)** — the four recorded
  observations from the proof round (`sequence.json` missing-vs-corrupt wording, the
  A2 fault-injection disclosure, the uncommitted disposable harness, and the
  enumeration-not-arithmetic interval statement) stay recorded in
  `V03E_G0_1_P7_PROOF.md` §7.1/§8; they do not change the PASS or its scope.
* These observations stay recorded; `P3` is **not** claimed to be zero.

**G0.1 / P7 has passed** (authoritative, independently approved), so it no longer
blocks mandatory-core implementation *eligibility*; implementation nonetheless
remains **NOT AUTHORIZED** until a separately issued authorization: no recovery
runtime is implemented, the design remains frozen but pre-implementation, and
`evidence_gap` stays part of the *future runtime* fail-closed semantics rather than a
waiver of the proof gate.  Had G0.1 / P7 failed, mandatory-core implementation would
have remained **blocked** pending a new reviewed design decision (there is no
degraded-implementation path).  Until P1-P3 and P8 pass,
`adopt_completed_turn` stays **disabled** and the core provides report +
`mark_unrecoverable` only.

## 29. Minimal local setup (future)

```text
devrelay mcp serve --workspace <ws>   # 17 accepted tools + exactly two v0.3-E tools:
                                      #   devrelay_reconcile_run     (read-only)
                                      #   devrelay_resolve_recovery  (mutating, gated)
```

An MCP Planner would: `devrelay_get_run` → `devrelay_reconcile_run` (read the
checklist and blockers) → `devrelay_resolve_recovery(mark_unrecoverable)` to close
the run safely, or — only when adoption is enabled and every §11 item passed —
`devrelay_resolve_recovery(adopt_completed_turn)` to continue from the already
existing result.  DevRelay still never sequences anything and never retries.
