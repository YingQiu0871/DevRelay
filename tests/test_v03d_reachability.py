"""v0.3-D second remediation: persisted-state **reachability** validation.

Three P1s are reproduced and closed here, and one documented bound is stated:

* **P1-A** a forged ``READY_REVIEWER`` run without this cycle's completed
  implementer turn used to reach ``POST /session/<reviewer>/message``;
* **P1-B** a historical ``blocked`` turn inside an active run used to let the run
  continue and submit again;
* **P1-C** an exhausted run (``max_cycles=3``, six consumed slots) rolled back
  toward cycle 1 used to be able to spend another six slots.

Every honest document in this module is produced by the real service
(``tests/v03d_corpus.py``); nothing hand-writes a "valid" run, and crash
boundaries come from a real ``SystemExit`` at submission.  All checks are offline:
the OpenCode stub, no provider, no network.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import pytest

from devrelay.errors import OrchestrationStateCorruptError
from devrelay.orchestration import OrchestrationStore
from devrelay.orchestration.invariants import validate_run_semantics

from v03d_corpus import CORPUS_STATES, build_state, corpus
from v03d_helpers import (
    Harness,
    get_run,
    phase,
    prompt_posts,
    restart_surface,
)

NUMERIC_FIELDS = (
    "schema_version",
    "max_cycles",
    "current_cycle",
    "completed_cycles",
    "turn_attempts",
    "model_turn_budget",
    "model_turns_used",
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def member(tmp_path: Path, name: str) -> dict[str, Any]:
    harness, run_id = build_state(name, tmp_path / name)
    return {
        "harness": harness,
        "run_id": run_id,
        "ws": harness.ws,
        "path": harness.ws / ".devrelay" / "orchestration" / "runs" / f"{run_id}.json",
    }


def write_payload(target: dict[str, Any], payload: dict[str, Any]) -> bytes:
    target["path"].write_text(json.dumps(payload), encoding="utf-8")
    return target["path"].read_bytes()


def read_payload(target: dict[str, Any]) -> dict[str, Any]:
    return json.loads(target["path"].read_text(encoding="utf-8"))


def seeded_store(tmp_path: Path, payload: dict[str, Any]) -> OrchestrationStore:
    """A store whose workspace matches *payload*, seeded with the document."""
    root = tmp_path / "seeded"
    runs = root / ".devrelay" / "orchestration" / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    payload = dict(payload)
    payload["workspace"] = str(root.resolve())
    (runs / f"{payload['run_id']}.json").write_text(json.dumps(payload), encoding="utf-8")
    return OrchestrationStore(root / ".devrelay")


def expect_refused_at_the_boundary(
    target: dict[str, Any],
    payload: dict[str, Any],
    needle: str,
    *,
    tool: str = "devrelay_run_implementer",
) -> None:
    """The tampered document is refused and never reaches a submission."""
    before = write_payload(target, payload)
    store = OrchestrationStore(target["ws"] / ".devrelay")
    with pytest.raises(OrchestrationStateCorruptError) as excinfo:
        store.load(target["run_id"])
    assert needle in str(excinfo.value), str(excinfo.value)

    # a fresh server over the same workspace must refuse too - and issue nothing
    restarted = restart_surface(target["harness"])
    envelope = phase(restarted.server, tool, target["run_id"], "tampered attempt")
    assert envelope["ok"] is False, envelope
    assert envelope["error"]["type"] == "orchestration_state_corrupt", envelope
    assert prompt_posts(restarted.stub) == [], "a corrupt run can never submit"
    assert target["path"].read_bytes() == before, "a corrupt run is never rewritten"


# ---------------------------------------------------------------------------
# P1-A: READY_REVIEWER (and a live reviewer intent) require implementer evidence
# ---------------------------------------------------------------------------
def test_p1a_a1_valid_ready_reviewer_without_implementer_turns(tmp_path: Path) -> None:
    target = member(tmp_path, "ready_reviewer_c1")
    payload = read_payload(target)
    assert payload["implementer_turns"], "the honest base has implementer evidence"
    payload["implementer_turns"] = []
    payload["model_turns_used"] = 0
    payload["turn_attempts"] = 0
    expect_refused_at_the_boundary(
        target, payload, "reviewer phase without exactly one completed implementer turn",
        tool="devrelay_run_reviewer",
    )


def test_p1a_a2_state_switched_to_ready_reviewer_without_evidence(tmp_path: Path) -> None:
    target = member(tmp_path, "ready_implementer_c1")
    payload = read_payload(target)
    payload["state"] = "READY_REVIEWER"
    payload["last_transition"] = {
        "action": "run_implementer",
        "source": "model_bearing",
        "previous_state": "READY_IMPLEMENTER",
        "next_state": "READY_REVIEWER",
        "cycle": 1,
        "role": "implementer",
        "note": "forged completion",
    }
    expect_refused_at_the_boundary(
        target, payload, "reviewer phase without exactly one completed implementer turn",
        tool="devrelay_run_reviewer",
    )


def test_p1a_a3_live_reviewer_intent_without_implementer_evidence(tmp_path: Path) -> None:
    target = member(tmp_path, "reviewer_in_flight_c1")
    payload = read_payload(target)
    assert payload["in_flight_turn"]["role"] == "reviewer"
    payload["implementer_turns"] = []
    payload["model_turns_used"] = 1
    payload["turn_attempts"] = 1
    expect_refused_at_the_boundary(
        target, payload, "reviewer phase without exactly one completed implementer turn",
        tool="devrelay_run_reviewer",
    )


def test_p1a_controls_are_accepted(tmp_path: Path) -> None:
    """An honest READY_REVIEWER and an honest crashed reviewer intent stay valid."""
    for name in ("ready_reviewer_c1", "reviewer_in_flight_c1", "reviewer_in_flight_c2"):
        target = member(tmp_path, name)
        payload = read_payload(target)
        OrchestrationStore(target["ws"] / ".devrelay").load(target["run_id"])
        validate_run_semantics(
            OrchestrationStore(target["ws"] / ".devrelay").load(target["run_id"])
        )
        assert payload["state"] == "READY_REVIEWER"


# ---------------------------------------------------------------------------
# P1-B: a blocked turn may never live in an active run
# ---------------------------------------------------------------------------
def test_p1b_b1_blocked_historical_turn_inside_an_active_run(tmp_path: Path) -> None:
    target = member(tmp_path, "ready_implementer_c2")
    payload = read_payload(target)
    payload["implementer_turns"][0]["outcome"] = "blocked"
    payload["implementer_turns"][0]["blocked_reason"] = "read_timeout"
    expect_refused_at_the_boundary(
        target, payload, "blocked turn(s)", tool="devrelay_run_implementer"
    )


def test_p1b_b2_completed_reviewer_without_any_implementer_evidence(tmp_path: Path) -> None:
    """Reviewer completion cannot exist without implementer completion (cycle N)."""
    target = member(tmp_path, "awaiting_decision_c1")
    payload = read_payload(target)
    payload["implementer_turns"] = []
    payload["model_turns_used"] = 1
    payload["turn_attempts"] = 1
    expect_refused_at_the_boundary(
        target,
        payload,
        "reviewer turn before any implementer turn",
        tool="devrelay_run_reviewer",
    )


def test_p1b_b3_completed_reviewer_whose_implementer_turn_failed(tmp_path: Path) -> None:
    """The stronger dependency rule: a completed reviewer needs a *completed*
    implementer in the same cycle, not merely a recorded one."""
    from v03d_helpers import failing_post_stub, fixed_run_ids, run_id_of
    from v03d_helpers import build as build_harness

    stub = failing_post_stub(tmp_path / "b3" / "ws", on_post=3)
    harness = build_harness(
        tmp_path / "b3", stub=stub, run_id_factory=fixed_run_ids("DR-" + "a" * 32)
    )
    run_id = run_id_of(harness.server, max_cycles=3)
    for tool, prompt in (
        ("devrelay_run_implementer", "i1"),
        ("devrelay_run_reviewer", "r1"),
    ):
        assert phase(harness.server, tool, run_id, prompt)["ok"] is True
    from v03d_helpers import decide

    assert decide(harness.server, run_id, "request_changes")["ok"] is True
    failed = phase(harness.server, "devrelay_run_implementer", run_id, "i2")
    assert failed["ok"] is False and failed["data"]["state"] == "BLOCKED", failed

    path = harness.ws / ".devrelay" / "orchestration" / "runs" / f"{run_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    forged_reviewer = dict(payload["reviewer_turns"][0], cycle=2)
    payload["reviewer_turns"].append(forged_reviewer)
    payload["model_turns_used"] = 4
    payload["turn_attempts"] = 4
    target = {"harness": harness, "run_id": run_id, "ws": harness.ws, "path": path}
    expect_refused_at_the_boundary(
        target,
        payload,
        "completed reviewer turn without exactly one completed implementer turn",
        tool="devrelay_run_reviewer",
    )


HONEST_BLOCKED = (
    "blocked_implementer_failure",
    "blocked_reviewer_failure",
    "blocked_route_change",
    "blocked_interrupted_implementer",
    "blocked_interrupted_reviewer",
)


@pytest.mark.parametrize("name", HONEST_BLOCKED, ids=list(HONEST_BLOCKED))
def test_p1b_controls_every_honest_blocked_variant_stays_valid(tmp_path: Path, name: str) -> None:
    target = member(tmp_path, name)
    payload = read_payload(target)
    assert payload["state"] == "BLOCKED"
    assert payload["blocked_reason"]
    store = OrchestrationStore(target["ws"] / ".devrelay")
    run = store.load(target["run_id"])
    validate_run_semantics(run)
    store.save(run)


def test_restoring_the_route_configuration_does_not_resurrect_a_blocked_run(tmp_path: Path) -> None:
    """§18: the route came back, the run must not."""
    from v03d_helpers import DISTINCT_ROLES, write_roles

    target = member(tmp_path, "blocked_route_change")
    write_roles(target["ws"], DISTINCT_ROLES)
    from v03d_helpers import call

    restarted = restart_surface(target["harness"])
    for tool, arguments in (
        ("devrelay_run_reviewer", {"run_id": target["run_id"], "prompt": "r"}),
        ("devrelay_run_implementer", {"run_id": target["run_id"], "prompt": "i"}),
        ("devrelay_decide_run", {"run_id": target["run_id"], "decision": "complete"}),
    ):
        envelope = call(restarted.server, tool, arguments)
        assert envelope["ok"] is False, envelope
        assert envelope["error"]["type"] == "orchestration_invalid_transition", envelope
    assert prompt_posts(restarted.stub) == []
    assert read_payload(target)["state"] == "BLOCKED"


# ---------------------------------------------------------------------------
# P1-C: an exhausted run can never be rolled back into spending again
# ---------------------------------------------------------------------------
def exhausted(tmp_path: Path) -> dict[str, Any]:
    """A real max_cycles=3 run, spent honestly to LIMIT_REACHED (6 POSTs)."""
    target = member(tmp_path, "limit_reached")
    payload = read_payload(target)
    assert payload["max_cycles"] == 1  # rebuilt below with three cycles
    return target


def exhausted_three_cycles(tmp_path: Path) -> dict[str, Any]:
    root = tmp_path / "exhausted"
    harness, run_id = build_state("ready_implementer_c3", root)
    from v03d_helpers import decide, phase as call_phase

    assert call_phase(harness.server, "devrelay_run_implementer", run_id, "i3")["ok"] is True
    assert call_phase(harness.server, "devrelay_run_reviewer", run_id, "r3")["ok"] is True
    final = decide(harness.server, run_id, "request_changes")
    assert final["ok"] is True and final["data"]["state"] == "LIMIT_REACHED", final
    posts = prompt_posts(harness.stub)
    assert len(posts) == 6, posts
    path = harness.ws / ".devrelay" / "orchestration" / "runs" / f"{run_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["model_turns_used"] == 6 and payload["model_turn_budget"] == 6
    return {"harness": harness, "run_id": run_id, "ws": harness.ws, "path": path}


def test_p1c_the_raw_exploit_from_the_gate_is_refused(tmp_path: Path) -> None:
    """Roll the exhausted run back toward cycle 1 and try to spend six more slots.

    The gate's attack rewrote state/cycle/counters and supplied plausible
    transition data.  Every partial rewrite is refused before any submission; a
    *fully* consistent rewrite is the documented bound (next test).
    """
    target = exhausted_three_cycles(tmp_path)
    payload = read_payload(target)
    payload.update(
        state="READY_IMPLEMENTER",
        current_cycle=1,
        completed_cycles=0,
        model_turns_used=0,
        turn_attempts=0,
        blocked_reason="",
        last_transition={
            "action": "start",
            "source": "external_planner",
            "previous_state": "",
            "next_state": "READY_IMPLEMENTER",
            "cycle": 1,
            "role": "",
            "note": "forged start",
        },
    )
    expect_refused_at_the_boundary(
        target, payload, "do not account for", tool="devrelay_run_implementer"
    )


ROLLBACK_VARIANTS: list[tuple[str, Callable[[dict[str, Any]], None], str]] = [
    (
        # state/cycle/counters reset, histories and decisions kept
        "state_cycle_counters_reset_but_history_kept",
        lambda p: p.update(
            state="READY_IMPLEMENTER",
            current_cycle=1,
            completed_cycles=0,
            model_turns_used=0,
            turn_attempts=0,
            blocked_reason="",
        ),
        "do not account for",
    ),
    (
        # state/cycle/counters reset and turns dropped, decisions kept
        "counters_and_turns_reset_but_decisions_kept",
        lambda p: p.update(
            state="READY_IMPLEMENTER",
            current_cycle=1,
            completed_cycles=0,
            model_turns_used=0,
            turn_attempts=0,
            blocked_reason="",
            implementer_turns=[],
            reviewer_turns=[],
        ),
        "decision(s) are recorded",
    ),
    (
        # everything reset except a stale transition (the lazy rollback)
        "everything_reset_but_the_transition_kept",
        lambda p: p.update(
            state="READY_IMPLEMENTER",
            current_cycle=1,
            completed_cycles=0,
            model_turns_used=0,
            turn_attempts=0,
            blocked_reason="",
            implementer_turns=[],
            reviewer_turns=[],
            decision_history=[],
        ),
        "the last transition ends at",
    ),
    (
        # a rewritten transition that is not a legal edge into the claimed state
        "transition_rewritten_to_a_non_edge",
        lambda p: p["last_transition"].update(
            action="run_reviewer",
            previous_state="READY_REVIEWER",
            next_state="READY_IMPLEMENTER",
            cycle=1,
            role="reviewer",
        ),
        "the last transition ends at",
    ),
    (
        # the §7 relation: one external decision per completed cycle
        "one_request_changes_decision_removed",
        lambda p: p["decision_history"].pop(0),
        "requires exactly",
    ),
    (
        # a fabricated cycle 3 that the decision chain cannot justify
        "cycle_three_claimed_with_one_request_changes",
        lambda p: (
            p["decision_history"].pop(0),
            p.update(state="READY_IMPLEMENTER", current_cycle=3, completed_cycles=2),
        ),
        "does not match",
    ),
    (
        # evidence from a cycle the run has not reached (and over budget too)
        "future_cycle_turn_injected",
        lambda p: (
            p["implementer_turns"].append(
                dict(p["implementer_turns"][0], cycle=p["max_cycles"] + 1)
            ),
            p.update(model_turns_used=7, turn_attempts=7),
        ),
        "exceeds the model-turn budget",
    ),
    (
        # terminal -> active rollback without touching the transition
        "terminal_run_rolled_back_to_an_active_state",
        lambda p: p.update(state="READY_REVIEWER"),
        "requires current_cycle == completed_cycles + 1",
    ),
    (
        # reviewer evidence survives, implementer evidence does not
        "reviewer_evidence_without_implementer_evidence",
        lambda p: p.update(implementer_turns=[]),
        "do not account for",
    ),
    (
        # a blocked turn smuggled into a completed history
        "blocked_turn_injected_into_the_history",
        lambda p: p["implementer_turns"][0].update(
            outcome="blocked", blocked_reason="read_timeout"
        ),
        "blocked turn(s)",
    ),
    (
        # the transition rewritten so that it points somewhere else entirely
        "transition_next_state_flipped",
        lambda p: p["last_transition"].update(next_state="STOPPED"),
        "the last transition ends at",
    ),
]


@pytest.mark.parametrize(
    "label,mutate,needle", ROLLBACK_VARIANTS, ids=[case[0] for case in ROLLBACK_VARIANTS]
)
def test_p1c_stronger_rollback_variants_are_all_refused(
    tmp_path: Path, label: str, mutate: Callable[[dict[str, Any]], None], needle: str
) -> None:
    target = exhausted_three_cycles(tmp_path)
    payload = read_payload(target)
    mutate(payload)
    expect_refused_at_the_boundary(target, payload, needle)


def test_p1c_a_perfectly_rewritten_history_is_the_documented_bound(tmp_path: Path) -> None:
    """Honest limit of a self-contained document: no external integrity anchor.

    A run document is mutable JSON with nothing outside it to anchor how much was
    already spent, so an attacker who rewrites *every* field into a different but
    internally consistent history cannot be detected by a self-contained
    validator.  v0.3-D therefore claims: all structural/semantic reachability
    invariants hold, every inconsistent or partially rolled-back document fails
    closed before any model call, and there is **no** cryptographic or
    append-only tamper evidence (see ``docs/BACKLOG.md`` §5).  This test states
    that bound instead of pretending to detect it.
    """
    target = exhausted_three_cycles(tmp_path)
    payload = read_payload(target)
    payload.update(
        state="READY_IMPLEMENTER",
        current_cycle=1,
        completed_cycles=0,
        model_turns_used=0,
        turn_attempts=0,
        implementer_turns=[],
        reviewer_turns=[],
        decision_history=[],
        blocked_reason="",
        last_transition={
            "action": "start",
            "source": "external_planner",
            "previous_state": "",
            "next_state": "READY_IMPLEMENTER",
            "cycle": 1,
            "role": "",
            "note": "forged start",
        },
    )
    write_payload(target, payload)
    # the rewritten document is a *fresh-looking* run: accepted, and that is the
    # documented bound, not a hidden failure of the reachability rules
    run = OrchestrationStore(target["ws"] / ".devrelay").load(target["run_id"])
    validate_run_semantics(run)
    assert run.model_turns_used == 0


# ---------------------------------------------------------------------------
# the production corpus: accepted, stable, and never a POST on load
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", CORPUS_STATES, ids=list(CORPUS_STATES))
def test_every_honest_member_survives_save_restart_load_and_resave(
    tmp_path: Path, name: str
) -> None:
    target = member(tmp_path, name)
    store = OrchestrationStore(target["ws"] / ".devrelay")
    run = store.load(target["run_id"])
    validate_run_semantics(run)
    summary = run.summary()

    store.save(run)  # re-save is a fixed point
    reloaded = store.load(target["run_id"])
    assert reloaded.model_dump(mode="json") == run.model_dump(mode="json")
    assert reloaded.summary() == summary

    # the service is destroyed and recreated: a fresh surface reads the same run
    restarted = restart_surface(target["harness"])
    read = get_run(restarted.server, target["run_id"])
    assert read["ok"] is True, read
    assert read["data"]["state"] == summary["state"]
    assert read["data"]["model_turns_used"] == summary["model_turns_used"]
    assert read["data"]["legal_next_actions"] == summary["legal_next_actions"]
    assert prompt_posts(restarted.stub) == [], "loading a run never submits anything"


MUTATION_BATTERY: list[tuple[str, Callable[[dict[str, Any]], bool], Callable[[dict[str, Any]], None]]] = [
    (
        "budget_raised_by_two",
        lambda p: True,
        lambda p: p.update(model_turn_budget=p["model_turn_budget"] + 2),
    ),
    (
        "turn_attempts_as_a_string",
        lambda p: True,
        lambda p: p.update(turn_attempts="1"),
    ),
    (
        "max_cycles_as_a_string",
        lambda p: True,
        lambda p: p.update(max_cycles="2"),
    ),
    (
        "spend_increased_by_one",
        lambda p: True,
        lambda p: p.update(
            model_turns_used=p["model_turns_used"] + 1,
            turn_attempts=p["turn_attempts"] + 1,
        ),
    ),
    (
        "schema_version_removed",
        lambda p: True,
        lambda p: p.pop("schema_version", None),
    ),
    (
        "last_transition_next_state_flipped",
        lambda p: p.get("last_transition") is not None,
        lambda p: p["last_transition"].update(
            next_state="BLOCKED" if p["state"] != "BLOCKED" else "COMPLETED"
        ),
    ),
    (
        "decision_history_cleared",
        lambda p: bool(p["decision_history"]),
        lambda p: p.update(decision_history=[]),
    ),
    (
        "decision_previous_state_flipped",
        lambda p: bool(p["decision_history"]),
        lambda p: p["decision_history"][0].update(previous_state="READY_IMPLEMENTER"),
    ),
    (
        "last_turn_marked_blocked",
        lambda p: p["state"] != "BLOCKED"
        and bool(p["implementer_turns"] or p["reviewer_turns"]),
        lambda p: (
            p["implementer_turns"] or p["reviewer_turns"]
        )[-1].update(outcome="blocked", blocked_reason="read_timeout"),
    ),
    (
        "turn_moved_into_the_future",
        lambda p: p["current_cycle"] < p["max_cycles"]
        and bool(p["implementer_turns"] or p["reviewer_turns"]),
        lambda p: (p["implementer_turns"] or p["reviewer_turns"])[-1].update(
            cycle=p["current_cycle"] + 1
        ),
    ),
    (
        "implementer_evidence_removed_but_reviewer_kept",
        lambda p: bool(p["reviewer_turns"]),
        lambda p: p.update(
            implementer_turns=[],
            model_turns_used=len(p["reviewer_turns"]) + (1 if p["in_flight_turn"] else 0),
            turn_attempts=len(p["reviewer_turns"]) + (1 if p["in_flight_turn"] else 0),
        ),
    ),
    (
        "prompt_digest_made_invalid",
        lambda p: bool(p["implementer_turns"] or p["reviewer_turns"]),
        lambda p: (p["implementer_turns"] or p["reviewer_turns"])[0].update(
            prompt_sha256="not-a-digest"
        ),
    ),
    (
        "turn_route_source_blanked",
        lambda p: bool(p["implementer_turns"] or p["reviewer_turns"]),
        lambda p: (p["implementer_turns"] or p["reviewer_turns"])[0].update(route_source=""),
    ),
    (
        "turn_resolved_agent_changed",
        lambda p: bool(p["implementer_turns"] or p["reviewer_turns"]),
        lambda p: (p["implementer_turns"] or p["reviewer_turns"])[0].update(
            resolved_agent="forged-agent"
        ),
    ),
    (
        "turn_completed_at_removed",
        lambda p: bool(p["implementer_turns"] or p["reviewer_turns"]),
        lambda p: (p["implementer_turns"] or p["reviewer_turns"])[0].update(completed_at=""),
    ),
]


def test_every_honest_member_rejects_every_semantic_mutation(tmp_path: Path) -> None:
    """Differential proof: honest corpus accepted, one mutation at a time rejected."""
    members = corpus(tmp_path / "differential")
    applied = 0
    for name, info in members.items():
        original = info["payload"]
        for label, applicable, mutate in MUTATION_BATTERY:
            payload = json.loads(json.dumps(original))
            if not applicable(payload):
                continue
            mutate(payload)
            store = seeded_store(tmp_path / f"seeded-{name}-{label}", payload)
            with pytest.raises(OrchestrationStateCorruptError) as excinfo:
                store.load(payload["run_id"])
            assert "semantically corrupt" in str(excinfo.value) or "malformed" in str(
                excinfo.value
            ), (name, label, str(excinfo.value))
            applied += 1
    assert applied >= 150, f"the differential battery must exercise the corpus ({applied})"


# ---------------------------------------------------------------------------
# §12 strict persisted types / §13 turn audit fields
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("field", NUMERIC_FIELDS, ids=list(NUMERIC_FIELDS))
@pytest.mark.parametrize("bad_value", ["2", 2.0, True, False, None], ids=repr)
def test_persisted_numeric_fields_are_strict(
    tmp_path: Path, field: str, bad_value: Any
) -> None:
    base = build_state("ready_implementer_c1", tmp_path / "base")[1]
    payload = json.loads(
        (
            Path(tmp_path / "base" / "ws" / ".devrelay" / "orchestration" / "runs")
            / f"{base}.json"
        ).read_text(encoding="utf-8")
    )
    payload[field] = bad_value
    store = seeded_store(tmp_path / f"strict-{field}-{bad_value!r}", payload)
    with pytest.raises(OrchestrationStateCorruptError):
        store.load(payload["run_id"])


@pytest.mark.parametrize("field", ["schema_version", "model_turn_budget"])
def test_missing_persisted_fields_are_rejected(tmp_path: Path, field: str) -> None:
    base = build_state("ready_implementer_c1", tmp_path / "base")[1]
    payload = json.loads(
        (
            Path(tmp_path / "base" / "ws" / ".devrelay" / "orchestration" / "runs")
            / f"{base}.json"
        ).read_text(encoding="utf-8")
    )
    payload.pop(field)
    store = seeded_store(tmp_path / f"missing-{field}", payload)
    with pytest.raises(OrchestrationStateCorruptError):
        store.load(payload["run_id"])


def test_model_turn_budget_has_no_impossible_default() -> None:
    """§26: the model cannot be constructed without a coherent budget."""
    from pydantic import ValidationError

    from devrelay.orchestration.models import ORCHESTRATION_SCHEMA_VERSION, OrchestrationRun

    with pytest.raises(ValidationError) as excinfo:
        OrchestrationRun(  # type: ignore[call-arg]
            schema_version=ORCHESTRATION_SCHEMA_VERSION,
            run_id="DR-" + "a" * 32,
            workspace="C:/ws",
            implementer_session_id="ses_impl",
            reviewer_session_id="ses_rev",
        )
    assert "model_turn_budget" in str(excinfo.value)


AUDIT_MUTATIONS: list[tuple[str, str, Callable[[dict[str, Any]], None], str]] = [
    (
        "completed_turn_at_removed",
        "awaiting_decision_c1",
        lambda p: p["implementer_turns"][0].update(completed_at=""),
        "completed_at",
    ),
    (
        "completed_turn_digest_uppercase",
        "awaiting_decision_c1",
        lambda p: p["implementer_turns"][0].update(prompt_sha256="A" * 64),
        "prompt digest",
    ),
    (
        "completed_turn_zero_length_prompt",
        "awaiting_decision_c1",
        lambda p: p["implementer_turns"][0].update(prompt_chars=0),
        "prompt length",
    ),
    (
        "completed_turn_with_blocked_reason",
        "awaiting_decision_c1",
        lambda p: p["implementer_turns"][0].update(blocked_reason="read_timeout"),
        "completed but carries blocked_reason",
    ),
    (
        "blocked_turn_without_reason",
        "blocked_implementer_failure",
        lambda p: p["implementer_turns"][0].update(blocked_reason=""),
        "blocked but carries no blocked_reason",
    ),
    (
        "in_flight_intent_claims_completion",
        "implementer_in_flight",
        lambda p: p["in_flight_turn"].update(completed_at="2026-01-01T00:00:00+00:00"),
        "must not claim a completion timestamp",
    ),
    (
        "in_flight_intent_with_blocked_reason",
        "implementer_in_flight",
        lambda p: p["in_flight_turn"].update(blocked_reason="read_timeout"),
        "must not carry a blocked_reason",
    ),
    (
        "turn_agent_mismatch",
        "awaiting_decision_c1",
        lambda p: p["implementer_turns"][0].update(resolved_agent="someone-else"),
        "recorded against agent",
    ),
    (
        "in_flight_agent_mismatch",
        "implementer_in_flight",
        lambda p: p["in_flight_turn"].update(resolved_agent="someone-else"),
        "in-flight intent was recorded against agent",
    ),
]


@pytest.mark.parametrize(
    "label,name,mutate,needle", AUDIT_MUTATIONS, ids=[case[0] for case in AUDIT_MUTATIONS]
)
def test_turn_audit_fields_are_consistent(
    tmp_path: Path,
    label: str,
    name: str,
    mutate: Callable[[dict[str, Any]], None],
    needle: str,
) -> None:
    payload = json.loads(
        json.dumps(corpus(tmp_path / "audit", names=(name,))[name]["payload"])
    )
    mutate(payload)
    store = seeded_store(tmp_path / f"audit-{label}", payload)
    with pytest.raises(OrchestrationStateCorruptError) as excinfo:
        store.load(payload["run_id"])
    assert needle in str(excinfo.value), str(excinfo.value)


# ---------------------------------------------------------------------------
# §15 save-side invariants (defense in depth)
# ---------------------------------------------------------------------------
SAVE_SIDE_MUTATIONS: list[tuple[str, Callable[[Any], None], str]] = [
    (
        "state_history_relation_broken",
        lambda run: setattr(run, "state", run.state.__class__.READY_IMPLEMENTER),
        "requires current_cycle == completed_cycles + 1",
    ),
    (
        "sessions_made_identical",
        lambda run: setattr(run, "reviewer_session_id", run.implementer_session_id),
        "identical",
    ),
    (
        "budget_mutated",
        lambda run: setattr(run, "model_turn_budget", run.model_turn_budget + 2),
        "does not equal",
    ),
    (
        "decision_history_mutated",
        lambda run: run.decision_history.clear(),
        "requires exactly",
    ),
]

#: The decision-history mutation needs a document that legitimately has one.
SAVE_SIDE_BASE = {
    "state_history_relation_broken": "awaiting_decision_c1",
    "sessions_made_identical": "awaiting_decision_c1",
    "budget_mutated": "awaiting_decision_c1",
    "decision_history_mutated": "ready_implementer_c2",
}


@pytest.mark.parametrize(
    "label,mutate,needle", SAVE_SIDE_MUTATIONS, ids=[case[0] for case in SAVE_SIDE_MUTATIONS]
)
def test_save_refuses_an_impossible_in_memory_run(
    tmp_path: Path, label: str, mutate: Callable[[Any], None], needle: str
) -> None:
    target = member(tmp_path, SAVE_SIDE_BASE[label])
    store = OrchestrationStore(target["ws"] / ".devrelay")
    before = target["path"].read_bytes()
    run = store.load(target["run_id"])
    mutate(run)  # assignment is deliberately unvalidated in-memory tampering
    with pytest.raises(OrchestrationStateCorruptError) as excinfo:
        store.save(run)
    assert needle in str(excinfo.value), str(excinfo.value)
    assert target["path"].read_bytes() == before, "the prior document is never touched"


# ---------------------------------------------------------------------------
# §21 message truthfulness, §23 lock scope, §14 helper/production agreement
# ---------------------------------------------------------------------------
def test_failure_messages_follow_the_structured_evidence(tmp_path: Path) -> None:
    """§21: the message may only claim what the machine evidence says."""
    from v03d_helpers import build as build_harness
    from v03d_helpers import fixed_run_ids, run_id_of, two_session_stub

    modes: list[tuple[str, dict[str, Any]]] = [
        ("connect_error", {"prompt_exception": "connect_error"}),
        ("read_timeout", {"prompt_exception": "read_timeout"}),
        ("http_500", {"prompt_http_status": 500}),
        ("accepted_pending", {"prompt_raw_reply": {"ok": True}}),
        ("malformed_2xx", {"prompt_html_fallback": True}),
    ]
    checked = 0
    for label, stub_kwargs in modes:
        stub = two_session_stub(tmp_path / label / "ws", **stub_kwargs)
        harness = build_harness(
            tmp_path / label, stub=stub, run_id_factory=fixed_run_ids("DR-" + "a" * 32)
        )
        run_id = run_id_of(harness.server, max_cycles=1)
        envelope = phase(harness.server, "devrelay_run_implementer", run_id, "i")
        assert envelope["ok"] is False, label
        turn = envelope["data"]["implementer_turns"][0]
        message = envelope["error"]["message"]

        uncertain = turn["submission_uncertain"]
        pending = turn["reply_pending"]
        if uncertain:
            assert "may have reached OpenCode" in message, (label, message)
        else:
            assert "uncertain" not in message, (label, message)
        if pending:
            assert "still pending" in message, (label, message)
        else:
            assert "pending" not in message, (label, message)
        if not uncertain and not pending and turn["submission_attempted"]:
            assert "was attempted and did not complete" in message, (label, message)
            if turn["submission_status"] is not None:
                assert f"HTTP {turn['submission_status']}" in message, (label, message)
        if not uncertain and not pending and not turn["submission_attempted"]:
            assert "no submission was attempted" in message, (label, message)
        checked += 1
    assert checked == len(modes)


def test_json_shaped_prompts_are_refused_at_the_sdk_boundary(tmp_path: Path) -> None:
    """§25 (recorded P3): the MCP SDK pre-parses JSON-looking *strings*.

    ``FuncMetadata.pre_parse_json`` converts a string argument into dict/list
    whenever the declared annotation is not plain ``str``, so a planner prompt
    that happens to be JSON (``{"task": ...}``) is refused by the SDK's own
    argument validation before DevRelay's envelope exists.  Safety-relevant part:
    nothing is submitted.  Non-JSON prompts (including malformed JSON text) are
    unaffected.  A ``str``-only annotation would suppress the coercion but would
    also replace the documented ``mcp_invalid_argument`` envelope for a missing
    prompt with an SDK-level error, so this is recorded rather than "fixed" here.
    """
    target = member(tmp_path, "ready_implementer_c1")
    before = len(prompt_posts(target["harness"].stub))
    for prompt in ('{"task": "do it"}', "[1, 2, 3]", '  {"a": 1}  '):
        with pytest.raises(Exception) as excinfo:
            phase(target["harness"].server, "devrelay_run_implementer", target["run_id"], prompt)
        assert "prompt" in str(excinfo.value), (prompt, str(excinfo.value))
    assert len(prompt_posts(target["harness"].stub)) == before, "nothing was submitted"

    # a non-JSON prompt (even one that merely looks like broken JSON) still works
    ok = phase(
        target["harness"].server, "devrelay_run_implementer", target["run_id"], '{"broken": '
    )
    assert ok["ok"] is True, ok
    assert len(prompt_posts(target["harness"].stub)) == before + 1


def test_status_advertises_the_exact_lock_scope(tmp_path: Path) -> None:
    from v03d_helpers import call

    harness = build_state("ready_implementer_c1", tmp_path / "status")[0]
    data = call(harness.server, "devrelay_status")["data"]
    block = data["mcp"]
    assert block["execution_serialized"] is True
    assert block["side_effects_serialized"] is True
    assert block["lock_scope"] == "per tool surface (one lock instance)"
    assert "one surface" in block["surfaces"]
    assert "unsupported" in block["multiple_surfaces_or_processes"]
    assert "process-wide" not in json.dumps(block)
    assert "process-scoped" not in json.dumps(block)


def test_an_inert_temp_file_is_never_listed_or_honoured(tmp_path: Path) -> None:
    """§27: a hard kill may leave an inert temp file - it is not a run."""
    target = member(tmp_path, "ready_implementer_c1")
    store = OrchestrationStore(target["ws"] / ".devrelay")
    runs = store.root
    inert = runs / f".{target['run_id']}.json.deadbeef.tmp"
    inert.write_text("{ this was never a run", encoding="utf-8")

    listed = sorted(path.stem for path in runs.glob("DR-*.json"))
    assert listed == [target["run_id"]], listed
    assert store.load(target["run_id"]).state.value == "READY_IMPLEMENTER"
    # an inert file is not adopted under its own name either
    with pytest.raises(Exception):
        store.load(inert.name)
    store.save(store.load(target["run_id"]))
    assert sorted(p.name for p in runs.iterdir()) == [
        f".{target['run_id']}.json.deadbeef.tmp",
        f"{target['run_id']}.json",
    ]


def test_the_in_memory_replay_helper_matches_production_shapes(tmp_path: Path) -> None:
    """§14 anti-drift: the replay helper and production documents agree."""
    from v03d_helpers import honest_run

    for name, state in (
        ("ready_implementer_c1", "READY_IMPLEMENTER"),
        ("ready_reviewer_c1", "READY_REVIEWER"),
        ("awaiting_decision_c1", "AWAITING_DECISION"),
    ):
        production = corpus(tmp_path / f"shape-{name}", names=(name,))[name]["payload"]
        replay = honest_run(state).model_dump(mode="json")
        assert set(replay) == set(production), (name, set(replay) ^ set(production))
        for key in ("implementer_turns", "reviewer_turns", "decision_history"):
            for replay_item, production_item in zip(replay[key], production[key]):
                assert set(replay_item) == set(production_item), (name, key)
        validate_run_semantics(honest_run(state))
