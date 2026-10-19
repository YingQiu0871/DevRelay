# DevRelay v0.3-D — bounded orchestration

Status: **ACCEPTED / CLOSED / UNRELEASED** (closeout bookkeeping change pending
one final independent closeout review) - real bounded orchestration smoke
**`PASS — V0.3-D REAL BOUNDED ORCHESTRATION SMOKE`** at candidate
`8b70610a5cdda600ef57cf8378c4f69cd33d5be4`; see
`docs/v0.3/V03D_ACCEPTANCE.md` §L for the real-run evidence.  Package version stays
`0.1.0`; the supported public release remains `v0.1.0`; no `v0.3-D` tag exists and
**v0.3-E has not started**.  The semantics in this specification are frozen as
accepted; this closeout does not change them.  Accepted baselines this stage builds on: v0.3-A
OpenCode session bridge (`bcf9627…`), v0.3-B MCP tool surface (`d058d62…`) and
v0.3-C agent role routing (`eabb667…`, closeout `e0a06fa…`).  Branch:
`v0.3-d-bounded-orchestration`; implementation commit `78d4e5d…` (unchanged by the
remediation, which is additive).

> Later status (2026-10-19): this stage was subsequently accepted and is part of the 0.3.0 tree (unreleased); the package version is now 0.3.0 and v0.3-E is implemented with adoption DISABLED.

## 1. Objective and boundary

v0.3-D remembers **where a run is**, allows only legal next phases, enforces a hard
cycle bound, keeps durable audit evidence and fails closed on uncertainty.  It
never decides whether the work is good.

```text
Human -> ChatGPT Planner / Arbiter
           | explicit orchestration actions (MCP)
        DevRelay v0.3-D
           |  state | bounds | transition policy | audit
        v0.3-C role routing (implementer | reviewer)
           |
        v0.3-B / v0.3-A  -> OpenCode -> configured provider/model
```

The initial (and only) workflow graph:

```text
READY_IMPLEMENTER --explicit run_implementer--> READY_REVIEWER
       ^                                              |
       |                                     explicit run_reviewer
       |                                              v
       |                                        AWAITING_DECISION
       |                                        /       |        \
       |                       decision=        /        |         \
       +---- request_changes -----------------+   complete   stop
           (only while cycle budget remains)        |          |
                                                    v          v
                                                COMPLETED    STOPPED
   (request_changes with no budget left -> LIMIT_REACHED)
```

## 2. What v0.3-D does and does not give DevRelay

Gives: bounded run state; legal transitions; cycle limits; durable audit;
fail-closed behaviour on uncertainty/failure; explicit Planner authority.

Still does **not** give: semantic judgement of reviewer output; automatic
approval or rejection; automatic merge; unrestricted loops; a background
scheduler; crash reconciliation; multi-process orchestration; automatic session
creation; role switching; retries or model fallback.

## 3. Authority invariant (P1)

DevRelay never parses reviewer prose (`APPROVE`, `REQUEST_CHANGES`, `LGTM`,
`PASS`, `FAIL`, or anything else) to choose a state.  After a reviewer turn
succeeds the run **must** stop at `AWAITING_DECISION`, and only an explicit
external `devrelay_decide_run` may advance it.  Reviewer output is evidence, not
authority; an implementer never self-approves and a reviewer never triggers
remediation.  Every decision record is written with `source =
"external_planner"`, and the orchestration envelopes contain no
`reviewer_approved`/`approved`/`verdict`/`review_passed` field.

## 4. States, bounds and accounting

States (explicit enum, no fuzzy strings): `READY_IMPLEMENTER`, `READY_REVIEWER`,
`AWAITING_DECISION`, `COMPLETED`, `STOPPED`, `BLOCKED`, `LIMIT_REACHED`.
Terminal states are `COMPLETED`, `STOPPED`, `BLOCKED`, `LIMIT_REACHED`; a
terminal run accepts no model-bearing action (and no further decision).

Bounds: `1 <= max_cycles <= HARD_MAX_CYCLES = 3` (default `2`); a caller can
never raise the hard bound.  One cycle is at most one implementer turn plus one
reviewer turn, so `model_turn_budget = 2 x max_cycles` and the absolute v0.3-D
maximum is **six reserved/consumed model-turn budget slots per run** - allowing at
most six model POST attempts/submissions under the bounded workflow, and there is
no path around it.  A consumed slot is not a confirmed request: see the accounting
paragraph below.

Cycle accounting: a cycle is complete when the reviewer turn reaches
`AWAITING_DECISION` (that is when `completed_cycles` increments);
`request_changes` opens the next cycle only while `completed_cycles < max_cycles`
and otherwise produces `LIMIT_REACHED` with **zero** model POSTs.

Persisted types are **strict** (no coercion, no migration): `schema_version` and
`model_turn_budget` are required and have no default, and `schema_version`,
`max_cycles`, `current_cycle`, `completed_cycles`, `turn_attempts`,
`model_turn_budget` and `model_turns_used` are strict integers, so a persisted
`"2"`, `2.0`, `true`, `false` or `null` is a malformed document rather than a
number.  A missing `schema_version` is rejected outright: DevRelay never silently
supplies a default when reading persisted state.  The same strictness applies to
per-turn `cycle`/`prompt_chars` and to the transition cycle.

Model-turn accounting (`model_turns_used`, authoritative): the counter records
**consumed orchestration model-turn budget slots**, not confirmed provider/HTTP
submissions.  A slot is consumed when the durable in-flight intent is committed,
*before* the role/model call is entered, so `model_turns_used = 1` with zero
actual POSTs (a connect failure after the slot was reserved) is valid and
intentional.  No failure path decrements or refunds a slot, and the truth about an
actual submission lives in the accepted ledger plus the per-turn
`submission_attempted`/`submission_status`/`submission_uncertain`/`call_ids`
evidence.  `turn_attempts` equals `model_turns_used` in every honest state, and
each reserved slot is accounted for either by a finished turn record in the role
history or by the live in-flight intent.

Turn outcome vocabulary (constrained): a recorded turn's `outcome` is exactly
`in_flight`, `completed` or `blocked`; an in-flight intent is `in_flight` until
the accepted result is recorded.  While a turn is in flight,
`legal_next_actions = []` (recovery is out of scope for v0.3-D), and a persisted
in-flight intent is finalized as `blocked`/`turn_interrupted` before the run fails
closed.

A cycle budget is **not** a retry budget: an individual turn that times out, is
uncertain, stays pending, fails the provider, produces a malformed state or fails
ownership blocks the run instead of spending another turn.  Recovery of failed or
uncertain runs is explicitly out of scope (v0.3-E).

## 5. Sessions and routes

* a run requires **two explicit, different** sessions
  (`implementer_session_id`, `reviewer_session_id`); v0.3-D never creates,
  infers, reuses or substitutes a session, and one session for both roles is
  refused (`orchestration_session_conflict`);
* at creation both sessions must belong to the bound workspace (bounded read-only
  ownership probes; nothing is created on failure) and the reviewer session stays
  independent - the Planner supplies both prompts and decides what the reviewer
  sees;
* the run captures a **sanitized route snapshot** (role, model, agent,
  route_source) at creation.  Before every role turn the route is resolved again
  and compared; a difference fails the run closed with
  `orchestration_route_changed` and **zero** model POST - a run never continues
  silently under a changed route.  A route that can no longer be **resolved at
  all** (the role was removed from the configuration, or its configured route
  became invalid) is treated exactly the same way: the existing run keeps its
  immutable snapshot and becomes durable `BLOCKED` with
  `blocked_reason = route_changed`, still with zero model POST and no fallback to
  another role or a default model.  At `start_run` nothing durable exists yet, so
  an unresolvable route is reported as `orchestration_route_changed` with **no run
  created** (there is no snapshot to store and no run to block).

## 6. Durable state and audit

```text
<workspace>/.devrelay/orchestration/runs/<run_id>.json
```

* run ids are generated (`DR-<32 hex characters>`) and validated with a strict
  full match (no prefix, suffix, trailing newline or CR) before any filesystem
  access, so a caller-supplied id can never be a traversal primitive;
  unknown/malformed ids are local `orchestration_run_not_found`/argument errors;
* writes are atomic (unique temp file + `os.replace`): a partially written
  document never appears as a valid run; a missing run is
  `orchestration_run_not_found` and an unreadable/malformed one is
  `orchestration_state_corrupt` - it is **never** silently reset or recreated.
  Honest scope: the final document is replaced atomically, so a reader sees either
  the complete previous document or the complete new one.  A hard kill may leave an
  **inert** `.*.tmp` file behind: it is never listed as a run and never honoured
  (only `DR-<32 hex>.json` is read, and a run is only ever loaded by its valid id),
  and normal saves leave no residue.  Durability against power loss is **not**
  claimed - no `fsync` is issued;
* **persisted state is untrusted input.**  A run document found on disk is
  re-validated before it is believed: the strict schema, then a semantic
  invariant pass that re-derives everything the state machine guarantees (fixed
  schema version; `1 <= max_cycles <= 3`; `model_turn_budget = 2 x max_cycles`;
  cycle counters inside their bounds and consistent with the recorded turns;
  `turn_attempts = model_turns_used`; every reserved turn accounted for by a
  finished record or the live in-flight intent; two distinct non-blank sessions;
  a two-role snapshot whose models are mappable and whose declared roles match
  their keys; at most one turn per role per cycle and never a reviewer turn
  before its implementer turn; `completed_cycles` equal to the number of
  completed reviewer turns; the state/cycle relation; `LIMIT_REACHED` only at the
  cap and with `blocked_reason = cycle_limit`; `BLOCKED` only with a reason;
  in-flight shape: matching `READY_*` state, current cycle, `outcome =
  in_flight`, snapshot model, well-formed prompt evidence; a decision history made
  only of external decisions with the decision and next state the current state
  requires; start provenance that claims no previous state; and a persisted
  document that records the transition that produced it and is bound to the
  workspace it was created in).  The same pass runs on save, so an internally
  inconsistent document cannot reach the disk either.  Anything else is
  `orchestration_state_corrupt`: it is refused at the boundary, never repaired,
  never migrated, never normalized, never rewritten - and it can never reach a
  model call.  A run copied in from another workspace is corrupt *here* and is
  never adopted;
* every state-changing operation records previous/next state, timestamp, action,
  whether the transition was external or model-bearing, cycle, role, prompt
  digest and length, resolved model/agent, call ids, submission status/flags,
  uncertainty/pending and assistant message ids;
* **no raw prompt, no provider reply body, no model reasoning and no credential
  material is persisted**; the provider/OpenCode session history remains the
  canonical conversational content and the Planner receives the live response;
* one tool surface writes here (the shipped stdio MCP server builds exactly one
  surface, and that surface serializes every tool body with one execution lock).
  Running several surfaces - or several processes - against one workspace is
  **unsupported** for v0.3-D: there is no cross-process lock, no writer lease and
  no recovery, and multi-process orchestration and crash reconciliation are out of
  scope.

### Reachability: the state must be provable from the persisted history

Valid fields are not enough.  Before a persisted run may drive anything, its
**current state must be reachable** from its own turn history, decision history,
counters, transition provenance, cycle structure and in-flight intent.  The rules
below are all satisfied by every honestly generated document and are enforced on
load *and* save:

* the last recorded transition must be a real edge of the state machine that
  **ends at the current state**, with the action, previous state, role and cycle
  that edge implies (`start` only for a fresh cycle-1 `READY_IMPLEMENTER` and only
  with an empty previous state; `decide` for a state entered by a decision, at the
  cycle the decision was taken in; `run_implementer`/`run_reviewer` for
  `READY_REVIEWER`/`AWAITING_DECISION`; `run_*` or `block` into `BLOCKED`);
* `len(decision_history) == completed_cycles - (1 if state == AWAITING_DECISION
  else 0)`: every completed cycle has exactly one external decision except the
  cycle that is still awaiting one, and no phantom decision exists;
* every decision record leaves `AWAITING_DECISION`, uses an allowed edge
  (`complete`→`COMPLETED`, `stop`→`STOPPED`, `request_changes`→
  `READY_IMPLEMENTER`|`LIMIT_REACHED`) and a decision that ends the run is the last
  record;
* the number of `request_changes` decisions that opened a new cycle equals
  `current_cycle - 1`, so cycle 2 needs one such decision, cycle 3 needs two, and
  `current_cycle = 3` with `completed_cycles = 2` cannot be fabricated from a
  single decision;
* no turn may come from a future cycle (`turn.cycle <= current_cycle`), there is
  at most one turn per role per cycle, an implementer turn always precedes its
  reviewer turn, and a completed reviewer turn requires exactly one completed
  implementer turn in the same cycle;
* `READY_REVIEWER` - and a live reviewer in-flight intent - requires exactly one
  **completed** implementer turn in the current cycle: the reviewer phase is
  unreachable from a cycle whose implementer phase never completed;
* a historical `blocked` turn implies the run state is `BLOCKED` (a failed phase
  fails the run closed and nothing reopens it), so a blocked turn can never sit
  inside an active or completed run;
* the persisted spend cannot exceed what the cycle structure could have produced
  (`model_turns_used <= 2 x current_cycle`), on top of the hard budget bound;
* each turn (and the in-flight intent) carries a well-formed audit record for its
  outcome: lowercase sha256 prompt digest, positive prompt length, valid
  `started_at`, valid `completed_at` once finished, no `blocked_reason` on a
  completed turn, a non-empty `blocked_reason` on a blocked one, and an in-flight
  intent that claims neither completion nor a blocked reason; `resolved_model`,
  `resolved_agent` and `route_source` must agree with the captured snapshot.

**Honest bound.**  A run document is self-contained mutable JSON with no external
integrity anchor, so the guarantee is exactly: every structural and semantic
reachability invariant holds, and every malformed, inconsistent or partially
rolled-back document fails closed **before** any model call.  v0.3-D does **not**
provide cryptographic or append-only tamper evidence: an attacker who rewrites
*every* field into a different but internally consistent history (for example
resetting an exhausted run to a fresh-looking cycle 1) cannot be detected from the
document alone.  That limitation is recorded rather than papered over; an
append-only journal or a signed chain would be later hardening, not this stage.

A model-bearing phase writes a durable **in-flight** record *before* the call is
submitted (the intent is on disk before the role call reaches submission; this is
asserted through a transport-level callback, not by timing).  A persisted
in-flight turn is never replayed: its sanitized evidence (role, cycle, prompt
digest and length, resolved model/agent, route source) is appended to that role's
turn history as `blocked`/`turn_interrupted` and only then does the run become
durable `BLOCKED` with `blocked_reason = turn_interrupted` and
`legal_next_actions = []`.  An intact run record can be read by a new process and
legal explicit transitions operate from persisted state - nothing more is claimed.

## 7. MCP surface (17 tools)

The accepted twelve tools are unchanged; exactly five are appended:

| # | Tool | Inputs | Model call |
| --- | --- | --- | --- |
| 13 | `devrelay_start_run` | `implementer_session_id`, `reviewer_session_id`, `max_cycles` | **no** |
| 14 | `devrelay_get_run` | `run_id` (read-only, local) | **no** |
| 15 | `devrelay_run_implementer` | `run_id`, `prompt` | exactly one |
| 16 | `devrelay_run_reviewer` | `run_id`, `prompt` | exactly one |
| 17 | `devrelay_decide_run` | `run_id`, `decision` (`complete` \| `request_changes` \| `stop`) | **no** |

There is no sixth orchestration tool, no run-list API, no auto-run tool and no
background runner.  `start_run` accepts no task prompt (and no model/agent/
endpoint/workspace argument): the Planner supplies prompt text for every phase,
so DevRelay neither invents task instructions nor persists task content.

All five bodies run through the same `_execute` choke point, so **every** tool
body of one surface runs under that surface's execution lock; there is no
orchestration lock, no role lock and no scheduler.  Lock scope is honest: the lock
is per tool surface, the shipped stdio server builds exactly one surface (so in it
every tool body is serialized), and multiple surfaces or multiple writer processes
against one workspace are unsupported and not covered by that lock.  Run-scoped
failures report the
current run state (`state`, `previous_state`, cycle accounting, model-turn
budget, `terminal`, `blocked_reason`, `legal_next_actions`) next to the stable
error code, and `devrelay_status` gains a sanitized capability block
(`hard_max_cycles: 3`, `automatic_role_sequencing: false`,
`automatic_decisions: false`, `durable_state: true`) that never inlines raw runs.
`MCP_SERVER_VERSION` is `0.3.0-d`.

## 8. Error taxonomy

`orchestration_run_not_found`, `orchestration_invalid_transition`,
`orchestration_cycle_limit`, `orchestration_session_conflict`,
`orchestration_route_changed`, `orchestration_state_corrupt` (plus the accepted
`mcp_invalid_argument` for malformed tool arguments).  None of these is ever
reported as a provider failure, and bridge/role failures keep their accepted
taxonomy (`read_timeout`, `http_status`, `submission_not_confirmed`, …) as the
run's `blocked_reason`.

## 9. Success, uncertainty and duplicates

For transition purposes a role turn is successful only when the accepted role
result proves `ok = true`, `submission_uncertain = false` and
`reply_pending = false`.  The text of the assistant message is never inspected,
no sentinel is required and no verdict is interpreted.

If a submission is uncertain or a reply is pending the run becomes `BLOCKED`,
the durable call ids remain as evidence, and DevRelay does not rerun the role,
advance to the other role, spend another cycle, call `interrupt` automatically or
call another model.

Because each model-bearing phase has exactly one legal state, a repeated
`run_implementer`/`run_reviewer` fails locally with the state unchanged and zero
model POST - that is the primary duplicate-submission guard (no idempotency claim
is made for the model-bearing tools themselves).

## 10. Verification status and known boundaries

**Historical (pre-acceptance review state, kept for the record):** during
implementation and the first two reviews no real orchestration/model smoke had been
run - real model turns were 0 in those rounds, and all evidence was offline
(deterministic stub over `httpx.MockTransport`) or the real stdio boundary against
a deterministic loopback fake.  A bounded real smoke required independent review
first and a separate authorization at that time.

**Current status (v0.3-D is accepted and closed, unreleased):** exactly one
separately authorized bounded real orchestration smoke was run at candidate
`8b70610a5cdda600ef57cf8378c4f69cd33d5be4` and the result is
**`PASS — V0.3-D REAL BOUNDED ORCHESTRATION SMOKE`**: `max_cycles = 2`, **4 real
model-bearing turns**, **exactly 4 `/message` POSTs**, **0 retries**, **0
fallbacks**, **0 automatic role calls** and **0 fifth turn**, ending in
`COMPLETED` after an explicit external decision.  The full real-run evidence
(identity, cycle-by-cycle transitions, both authority probes, accounting, route
agreement, durability/privacy audit and the terminal guard) is recorded in
`docs/v0.3/V03D_ACCEPTANCE.md` §L.  **No second smoke is authorized or required for
v0.3-D acceptance**, and **v0.3-E remains NOT STARTED** (recovery is still out of
scope for v0.3-D).

* Out of scope: v0.3-E recovery (reconciliation after a crash during submission,
  uncertain-call recovery, orphan-process recovery, automatic resume), any
  semantic judgement of review content, WebUI/HTTP control API, background
  scheduling, multi-process orchestration.
* **Known boundary, recorded (P3):** the MCP SDK builds a lax pydantic argument
  model from the declared tool schema, so a JSON ``true``/``"2"``/``2.0`` reaches
  the tool body as the integer 1/2/2 (and ``1.5`` is refused by the SDK before the
  body runs).  The DevRelay bound is applied to the normalized value - the v0.3-D
  ceiling can never be raised, ``false`` normalizes to 0 and is refused - and the
  tool body itself rejects a real ``bool`` whenever it sees one.  No fix is
  attempted at the adapter layer because the normalization happens above it; the
  DevRelay-side check is kept and asserted.  Persisted documents are unaffected:
  they are validated with strict types, not through the MCP argument model.
* **Known boundary, recorded (P3):** the same SDK pre-parses a *string* argument
  that happens to be JSON (``{"task": ...}``, ``[1, 2, 3]``) into a dict/list
  because ``FuncMetadata.pre_parse_json`` acts whenever the declared annotation is
  not plain ``str``; such a prompt is then refused by the SDK's own argument
  validation before DevRelay's envelope exists, and **nothing is submitted**.  A
  plain ``str`` annotation would suppress the coercion but would also replace the
  documented ``mcp_invalid_argument`` envelope for a missing prompt with an
  SDK-level error, so the trade-off is recorded instead of destabilizing the
  adapter.  Non-JSON prompts (including malformed JSON text) work normally.
* **Known bound of non-cryptographic state validation:** see §6 - a fully
  rewritten but internally consistent history cannot be distinguished from an
  honest one without an external integrity anchor.

## 11. Minimal local setup

```bash
devrelay mcp serve --workspace /path/to/project     # stdio MCP server, 17 tools
```

An MCP Planner then: creates two sessions in that workspace (through OpenCode),
calls `devrelay_start_run(max_cycles=2)`, explicitly runs the implementer phase,
explicitly runs the reviewer phase (which always stops at `AWAITING_DECISION`),
and records its own decision (`request_changes` for another bounded cycle, or
`complete`/`stop` to finish).  DevRelay never sequences those calls.
