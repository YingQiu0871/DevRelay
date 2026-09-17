# DevRelay v0.3-D — bounded orchestration

Status: **candidate implementation complete — ready for independent review**
(unreleased candidate work; package version stays `0.1.0`; public release remains
`v0.1.0`; v0.3-E not started).  Accepted baselines this stage builds on: v0.3-A
OpenCode session bridge (`bcf9627…`), v0.3-B MCP tool surface (`d058d62…`) and
v0.3-C agent role routing (`eabb667…`, closeout `e0a06fa…`).  Branch:
`v0.3-d-bounded-orchestration`.

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
maximum is **6 model turns per run** - there is no path around it.

Cycle accounting: a cycle is complete when the reviewer turn reaches
`AWAITING_DECISION` (that is when `completed_cycles` increments);
`request_changes` opens the next cycle only while `completed_cycles < max_cycles`
and otherwise produces `LIMIT_REACHED` with **zero** model POSTs.

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
  silently under a changed route.

## 6. Durable state and audit

```text
<workspace>/.devrelay/orchestration/runs/<run_id>.json
```

* run ids are generated (`DR-<32 hex characters>`) and validated against a strict
  pattern before any filesystem access, so a caller-supplied id can never be a
  traversal primitive; unknown/malformed ids are local
  `orchestration_run_not_found`/argument errors;
* writes are atomic (unique temp file + `os.replace`): a partially written
  document never appears as a valid run; a missing run is
  `orchestration_run_not_found` and an unreadable/malformed one is
  `orchestration_state_corrupt` - it is **never** silently reset or recreated;
* every state-changing operation records previous/next state, timestamp, action,
  whether the transition was external or model-bearing, cycle, role, prompt
  digest and length, resolved model/agent, call ids, submission status/flags,
  uncertainty/pending and assistant message ids;
* **no raw prompt, no provider reply body, no model reasoning and no credential
  material is persisted**; the provider/OpenCode session history remains the
  canonical conversational content and the Planner receives the live response;
* one MCP server process writes here (the accepted v0.3-B execution boundary
  serializes every tool body).  Multi-process orchestration and crash
  reconciliation are out of scope.

A model-bearing phase writes a durable **in-flight** record *before* the call.  A
persisted in-flight turn is never replayed: the next mutating action fails the run
closed (`BLOCKED`, `blocked_reason=turn_interrupted`).  An intact run record can
be read by a new process and legal explicit transitions operate from persisted
state - nothing more is claimed.

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

All five bodies run through the same `_execute` choke point, so the accepted
v0.3-B execution lock still serializes **all seventeen** tools; there is no
orchestration lock, no role lock and no scheduler.  Run-scoped failures report the
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

## 10. What is not verified yet

* **No real orchestration/model smoke has been run**: real model turns = 0 in this
  round; all evidence is offline (deterministic stub over `httpx.MockTransport`)
  or the real stdio boundary against a deterministic loopback fake.
* A bounded real orchestration smoke requires independent review first
  (`P0 = 0`, `P1 = 0`, no smoke-blocking P2) and a separate authorization; its
  expected shape is two cycles at most (4 model turns) with an explicit
  `request_changes` and a final explicit `complete`.
* Out of scope: v0.3-E recovery (reconciliation after a crash during submission,
  uncertain-call recovery, orphan-process recovery, automatic resume), any
  semantic judgement of review content, WebUI/HTTP control API, background
  scheduling, multi-process orchestration.

## 11. Minimal local setup

```bash
devrelay mcp serve --workspace /path/to/project     # stdio MCP server, 17 tools
```

An MCP Planner then: creates two sessions in that workspace (through OpenCode),
calls `devrelay_start_run(max_cycles=2)`, explicitly runs the implementer phase,
explicitly runs the reviewer phase (which always stops at `AWAITING_DECISION`),
and records its own decision (`request_changes` for another bounded cycle, or
`complete`/`stop` to finish).  DevRelay never sequences those calls.
