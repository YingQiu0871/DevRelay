"""v0.3-D remediation: tamper matrix, honest corpus, load-boundary invariants.

Every case is offline and deterministic: the real MCP SDK dispatch, the real
v0.3-D orchestration service, the real v0.3-C role router and the accepted
v0.3-A bridge wired to the accepted OpenCode stub (``httpx.MockTransport``).  No
model, provider or network call is made anywhere in this module.

The contract under test: **persisted orchestration state is untrusted input**.
A document the production state machine could not have produced must be refused
with ``orchestration_state_corrupt`` at the load boundary, must never be
rewritten or repaired, and must never lead to a model call.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import pytest

from devrelay.errors import OrchestrationStateCorruptError
from devrelay.orchestration import OrchestrationRun, OrchestrationStore, TurnRecord
from devrelay.orchestration.invariants import validate_run_semantics
from devrelay.orchestration.models import RunState, TurnOutcomeState

from test_v03b_mcp_tools import real_reply
from v03d_helpers import (
    RUN_ID,
    Harness,
    build,
    call,
    decide,
    fixed_run_ids,
    get_run,
    honest_run,
    phase,
    raw_payload,
    restart_surface,
    run_id_of,
    start,
    state_path,
    two_session_stub,
    with_in_flight,
    write_roles,
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def fail_second_prompt(stub: Any) -> None:
    """Make exactly the second prompt POST fail like the real transport."""
    original = stub.handler
    state = {"posts": 0}

    def handler(request: Any) -> Any:
        if request.method.upper() == "POST" and request.url.path.endswith("/message"):
            state["posts"] += 1
            if state["posts"] == 2:
                stub.prompt_exception = "read_timeout"
        return original(request)

    stub.handler = handler


def unique_reply_per_prompt(stub: Any, texts: list[str]) -> None:
    """Give every prompt POST its own assistant reply (never a stale id)."""
    original = stub.handler
    state = {"posts": 0}

    def handler(request: Any) -> Any:
        if request.method.upper() == "POST" and request.url.path.endswith("/message"):
            index = min(state["posts"], len(texts) - 1)
            state["posts"] += 1
            stub.prompt_reply = real_reply(
                message_id=f"msg_v03d_{state['posts']}", text=texts[index]
            )
        return original(request)

    stub.handler = handler


# ---------------------------------------------------------------------------
# harness bases: honest runs the state machine really produced
# ---------------------------------------------------------------------------


def _fresh(tmp_path: Path) -> tuple[Harness, str]:
    """READY_IMPLEMENTER, cycle 1 (start only; zero POSTs)."""
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    return harness, run_id_of(harness.server, max_cycles=2)


def _reviewed(tmp_path: Path) -> tuple[Harness, str]:
    """AWAITING_DECISION after one complete cycle (two POSTs)."""
    harness, run_id = _fresh(tmp_path)
    assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is True
    assert phase(harness.server, "devrelay_run_reviewer", run_id, "r")["ok"] is True
    return harness, run_id


def _reviewer_ready(tmp_path: Path) -> tuple[Harness, str]:
    """READY_REVIEWER: the implementer turn completed, the reviewer has not run."""
    harness, run_id = _fresh(tmp_path)
    assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is True
    return harness, run_id


def _cap_reviewed(tmp_path: Path) -> tuple[Harness, str]:
    """AWAITING_DECISION with completed_cycles == max_cycles == 1."""
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)
    assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is True
    assert phase(harness.server, "devrelay_run_reviewer", run_id, "r")["ok"] is True
    return harness, run_id


def _cycle2(tmp_path: Path) -> tuple[Harness, str]:
    """READY_IMPLEMENTER for cycle 2 after an explicit request_changes."""
    harness, run_id = _reviewed(tmp_path)
    assert decide(harness.server, run_id, "request_changes")["ok"] is True
    return harness, run_id


def _completed(tmp_path: Path) -> tuple[Harness, str]:
    """COMPLETED after an explicit external complete."""
    harness, run_id = _reviewed(tmp_path)
    assert decide(harness.server, run_id, "complete")["ok"] is True
    return harness, run_id


def _blocked(tmp_path: Path) -> tuple[Harness, str]:
    """BLOCKED after a failed reviewer turn (transport read timeout)."""
    stub = two_session_stub(tmp_path / "ws")
    fail_second_prompt(stub)
    harness = build(tmp_path, stub=stub, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)
    assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is True
    blocked = phase(harness.server, "devrelay_run_reviewer", run_id, "r")
    assert blocked["ok"] is False and blocked["data"]["state"] == "BLOCKED"
    return harness, run_id


def _blocked_implementer(tmp_path: Path) -> tuple[Harness, str]:
    """BLOCKED after a failed implementer turn, produced by the real service."""
    from v03d_corpus import build_state

    return build_state("blocked_implementer_failure", tmp_path)


BASES: dict[str, Callable[[Path], tuple[Harness, str]]] = {
    "fresh": _fresh,
    "blocked_impl": _blocked_implementer,
    "reviewed": _reviewed,
    "cap_reviewed": _cap_reviewed,
    "cycle2": _cycle2,
    "completed": _completed,
    "blocked": _blocked,
}


def _reject(harness: Harness, run_id: str, needle: str, posts_before: int) -> None:
    """The tampered document is refused everywhere and never repaired."""
    path = state_path(harness.ws, run_id)
    before = path.read_bytes()

    store = OrchestrationStore(harness.ws / ".devrelay")
    with pytest.raises(OrchestrationStateCorruptError) as excinfo:
        store.load(run_id)
    assert needle in str(excinfo.value), str(excinfo.value)

    read = get_run(harness.server, run_id)
    assert read["ok"] is False
    assert read["error"]["type"] == "orchestration_state_corrupt"

    action = phase(harness.server, "devrelay_run_implementer", run_id, "tampered")
    assert action["ok"] is False
    assert action["error"]["type"] == "orchestration_state_corrupt"
    decided = decide(harness.server, run_id, "request_changes")
    assert decided["ok"] is False
    assert decided["error"]["type"] == "orchestration_state_corrupt"

    assert len(harness.posts) == posts_before, "a corrupt run can never reach a model call"
    assert path.read_bytes() == before, "a corrupt run is never rewritten, repaired or reset"


# ---------------------------------------------------------------------------
# §25 - the 20-case corruption / tamper matrix
# ---------------------------------------------------------------------------
#: ``(case id, honest base, tamper, expected invariant message)``
TAMPER_MATRIX: list[tuple[str, str, Callable[[dict[str, Any]], None], str]] = [
    (
        "T01_schema_version_2",
        "fresh",
        lambda p: p.update(schema_version=2),
        "schema_version 2 is not the supported",
    ),
    (
        "T02_max_cycles_99_budget_198",
        "fresh",
        lambda p: p.update(max_cycles=99, model_turn_budget=198),
        "max_cycles 99 is outside the hard bound",
    ),
    (
        "T03_max_cycles_1000_budget_2000",
        "fresh",
        lambda p: p.update(max_cycles=1000, model_turn_budget=2000),
        "max_cycles 1000 is outside the hard bound",
    ),
    (
        "T04_max_cycles_zero",
        "fresh",
        lambda p: p.update(max_cycles=0, model_turn_budget=0),
        "max_cycles 0 is outside the hard bound",
    ),
    (
        "T05_budget_not_two_times_max_cycles",
        "fresh",
        lambda p: p.update(model_turn_budget=3),
        "does not equal",
    ),
    (
        "T06_completed_cycles_above_max",
        "reviewed",
        lambda p: p.update(completed_cycles=5),
        "completed_cycles 5 is outside 0..2",
    ),
    (
        "T07_current_cycle_out_of_range",
        "reviewed",
        lambda p: p.update(current_cycle=7),
        "current_cycle 7 is outside 1..2",
    ),
    (
        "T08_model_turns_used_above_budget",
        "reviewed",
        lambda p: p.update(model_turns_used=99, turn_attempts=99),
        "exceeds the model-turn budget",
    ),
    (
        "T09_turn_attempts_disagrees_with_used",
        "reviewed",
        lambda p: p.update(turn_attempts=7),
        "disagrees with model_turns_used",
    ),
    (
        "T10_turns_do_not_account_for_reserved",
        "reviewed",
        lambda p: p.update(reviewer_turns=[]),
        "do not account for",
    ),
    (
        "T11_identical_role_sessions",
        "fresh",
        lambda p: p.update(reviewer_session_id=p["implementer_session_id"]),
        "identical",
    ),
    (
        "T12_blank_role_session",
        "fresh",
        lambda p: p.update(implementer_session_id="   "),
        "is missing or blank",
    ),
    (
        "T13_two_turns_for_one_role_cycle",
        "cycle2",
        lambda p: (
            p["implementer_turns"].append(dict(p["implementer_turns"][0])),
            p.update(model_turns_used=3, turn_attempts=3),
        ),
        "more than one turn in cycle 1",
    ),
    (
        "T14_reviewer_before_any_implementer",
        "fresh",
        lambda p: (
            p["reviewer_turns"].append(
                {
                    "role": "reviewer",
                    "cycle": 1,
                    "started_at": p["implementer_turns"][0]["started_at"]
                    if p["implementer_turns"]
                    else "2026-01-01T00:00:00+00:00",
                    "completed_at": "2026-01-01T00:00:01+00:00",
                    "prompt_sha256": "b" * 64,
                    "prompt_chars": 4,
                    "resolved_model": "provider-b/model-b",
                    "resolved_agent": "",
                    "route_source": "workspace_config",
                    "outcome": "completed",
                }
            ),
            p.update(model_turns_used=1, turn_attempts=1),
        ),
        "reviewer turn before any implementer turn",
    ),
    (
        "T15_completed_cycles_without_completed_reviewer",
        "reviewed",
        lambda p: (
            p.update(reviewer_turns=[], model_turns_used=1, turn_attempts=1),
            p["implementer_turns"][0].update(cycle=1),
        ),
        "completed reviewer turn(s)",
    ),
    (
        "T16_awaiting_decision_without_any_cycle",
        "fresh",
        lambda p: p.update(state="AWAITING_DECISION"),
        "requires current_cycle == completed_cycles",
    ),
    (
        "T17_limit_reached_below_the_cap",
        "reviewed",
        lambda p: p.update(state="LIMIT_REACHED", blocked_reason="cycle_limit"),
        "LIMIT_REACHED requires completed_cycles == max_cycles",
    ),
    (
        "T18_decision_from_a_non_external_source",
        "reviewed",
        lambda p: p.update(
            decision_history=[
                {
                    "decision": "request_changes",
                    "source": "reviewer_prose",
                    "previous_state": "AWAITING_DECISION",
                    "next_state": "READY_IMPLEMENTER",
                }
            ]
        ),
        "only external decisions may advance a run",
    ),
    (
        "T19_start_transition_claims_a_previous_state",
        "fresh",
        lambda p: p["last_transition"].update(previous_state="READY_IMPLEMENTER"),
        "the start transition must describe a fresh cycle-1",
    ),
    (
        "T20_in_flight_model_outside_the_snapshot",
        "fresh",
        lambda p: p.update(
            in_flight_turn={
                "role": "implementer",
                "cycle": 1,
                "started_at": "2026-01-01T00:00:00+00:00",
                "prompt_sha256": "a" * 64,
                "prompt_chars": 4,
                "resolved_model": "provider-z/model-z",
                "resolved_agent": "",
                "route_source": "workspace_config",
                "outcome": "in_flight",
            },
            model_turns_used=1,
            turn_attempts=1,
        ),
        "in-flight intent was recorded against model",
    ),
]

#: Additional corruptions beyond the required 20 (same contract, more shapes).
EXTRA_TAMPER_CASES: list[tuple[str, str, Callable[[dict[str, Any]], None], str]] = [
    (
        "X01_unknown_turn_outcome",
        "reviewed",
        lambda p: p["implementer_turns"][0].update(outcome="APPROVED"),
        "malformed",
    ),
    (
        "X02_terminal_state_with_a_live_in_flight_intent",
        "blocked_impl",
        lambda p: p.update(
            in_flight_turn={
                "role": "implementer",
                "cycle": 1,
                "started_at": "2026-01-01T00:00:00+00:00",
                "prompt_sha256": "a" * 64,
                "prompt_chars": 4,
                "resolved_model": "provider-a/model-a",
                "resolved_agent": "",
                "route_source": "workspace_config",
                "outcome": "in_flight",
            },
            model_turns_used=2,
            turn_attempts=2,
        ),
        "carries a live in-flight intent",
    ),
    (
        "X03_in_flight_role_state_mismatch",
        "cycle2",
        lambda p: (
            p["implementer_turns"].append(
                {
                    "role": "implementer",
                    "cycle": 2,
                    "started_at": "2026-01-01T00:00:00+00:00",
                    "completed_at": "2026-01-01T00:00:01+00:00",
                    "prompt_sha256": "b" * 64,
                    "prompt_chars": 4,
                    "resolved_model": "provider-a/model-a",
                    "resolved_agent": "",
                    "route_source": "workspace_config",
                    "outcome": "completed",
                }
            ),
            p.update(
                in_flight_turn={
                    "role": "reviewer",
                    "cycle": 2,
                    "started_at": "2026-01-01T00:00:02+00:00",
                    "prompt_sha256": "a" * 64,
                    "prompt_chars": 4,
                    "resolved_model": "provider-b/model-b",
                    "resolved_agent": "",
                    "route_source": "workspace_config",
                    "outcome": "in_flight",
                },
                model_turns_used=4,
                turn_attempts=4,
            ),
        ),
        "requires state READY_REVIEWER",
    ),
    (
        "X04_in_flight_outcome_completed",
        "fresh",
        lambda p: p.update(
            in_flight_turn={
                "role": "implementer",
                "cycle": 1,
                "prompt_sha256": "a" * 64,
                "prompt_chars": 4,
                "resolved_model": "provider-a/model-a",
                "outcome": "completed",
            },
            model_turns_used=1,
            turn_attempts=1,
        ),
        "outcome must be 'in_flight'",
    ),
    (
        "X05_in_flight_malformed_prompt_evidence",
        "fresh",
        lambda p: p.update(
            in_flight_turn={
                "role": "implementer",
                "cycle": 1,
                "started_at": "2026-01-01T00:00:00+00:00",
                "prompt_sha256": "deadbeef",
                "prompt_chars": 4,
                "resolved_model": "provider-a/model-a",
                "resolved_agent": "",
                "route_source": "workspace_config",
                "outcome": "in_flight",
            },
            model_turns_used=1,
            turn_attempts=1,
        ),
        "has no valid prompt digest",
    ),
    (
        "X06_in_flight_cycle_is_not_current",
        "cycle2",
        lambda p: p.update(
            in_flight_turn={
                "role": "implementer",
                "cycle": 1,
                "prompt_sha256": "a" * 64,
                "prompt_chars": 4,
                "resolved_model": "provider-a/model-a",
                "outcome": "in_flight",
            },
            model_turns_used=3,
            turn_attempts=3,
        ),
        "is not the current cycle",
    ),
    (
        "X07_blocked_without_a_reason",
        "fresh",
        lambda p: p.update(state="BLOCKED"),
        "requires a blocked_reason",
    ),
    (
        "X08_blocked_reason_on_a_healthy_state",
        "fresh",
        lambda p: p.update(blocked_reason="read_timeout"),
        "must not carry blocked_reason",
    ),
    (
        "X09_snapshot_missing_a_role",
        "fresh",
        lambda p: p["route_snapshot"].pop("reviewer"),
        "are not exactly",
    ),
    (
        "X10_snapshot_unknown_role",
        "fresh",
        lambda p: p["route_snapshot"].update(
            auditor={"role": "auditor", "model": "provider-a/model-a"}
        ),
        "are not exactly",
    ),
    (
        "X11_snapshot_role_key_mismatch",
        "fresh",
        lambda p: p["route_snapshot"]["implementer"].update(role="reviewer"),
        "declares role",
    ),
    (
        "X12_snapshot_blank_model",
        "fresh",
        lambda p: p["route_snapshot"]["reviewer"].update(model="  "),
        "has a blank model",
    ),
    (
        "X13_snapshot_unmappable_model",
        "fresh",
        lambda p: p["route_snapshot"]["reviewer"].update(model="no-slash-model"),
        "cannot be mapped",
    ),
    (
        "X14_snapshot_unsupported_route_source",
        "fresh",
        lambda p: p["route_snapshot"]["implementer"].update(route_source="default_model"),
        "unsupported route_source",
    ),
    (
        "X15_turn_model_outside_the_snapshot",
        "reviewed",
        lambda p: p["implementer_turns"][0].update(resolved_model="provider-x/model-x"),
        "but the snapshot says",
    ),
    (
        "X16_turn_cycle_out_of_range",
        "reviewed",
        lambda p: p["implementer_turns"][0].update(cycle=9),
        "outside 1..2",
    ),
    (
        "X17_unknown_decision_in_history",
        "reviewed",
        lambda p: p.update(
            decision_history=[
                {
                    "decision": "approve",
                    "previous_state": "AWAITING_DECISION",
                    "next_state": "COMPLETED",
                }
            ]
        ),
        "unknown decision",
    ),
    (
        "X18_decision_next_state_does_not_match",
        "completed",
        lambda p: p["decision_history"][0].update(next_state="READY_IMPLEMENTER"),
        "cannot lead to",
    ),
    (
        "X19_second_cycle_without_any_decision",
        "cycle2",
        lambda p: p.update(decision_history=[]),
        "requires exactly 1 external decision(s)",
    ),
    (
        "X20_completed_without_any_decision",
        "completed",
        lambda p: p.update(decision_history=[]),
        "requires exactly 1 external decision(s)",
    ),
    (
        "X21_limit_reached_without_the_cycle_limit_reason",
        "cap_reviewed",
        lambda p: p.update(state="LIMIT_REACHED"),
        "requires blocked_reason 'cycle_limit'",
    ),
    (
        "X22_non_start_transition_without_a_previous_state",
        "reviewed",
        lambda p: p["last_transition"].update(previous_state=""),
        "must record its previous state",
    ),
]


@pytest.mark.parametrize(
    "case_id,base,mutate,needle", TAMPER_MATRIX, ids=[case[0] for case in TAMPER_MATRIX]
)
def test_the_20_case_tamper_matrix_is_refused_at_the_load_boundary(
    tmp_path: Path,
    case_id: str,
    base: str,
    mutate: Callable[[dict[str, Any]], None],
    needle: str,
) -> None:
    harness, run_id = BASES[base](tmp_path)
    posts_before = len(harness.posts)
    payload = raw_payload(harness.ws, run_id)
    mutate(payload)
    state_path(harness.ws, run_id).write_text(json.dumps(payload), encoding="utf-8")
    _reject(harness, run_id, needle, posts_before)


@pytest.mark.parametrize(
    "case_id,base,mutate,needle",
    EXTRA_TAMPER_CASES,
    ids=[case[0] for case in EXTRA_TAMPER_CASES],
)
def test_additional_tampered_documents_are_refused_too(
    tmp_path: Path,
    case_id: str,
    base: str,
    mutate: Callable[[dict[str, Any]], None],
    needle: str,
) -> None:
    harness, run_id = BASES[base](tmp_path)
    posts_before = len(harness.posts)
    payload = raw_payload(harness.ws, run_id)
    mutate(payload)
    state_path(harness.ws, run_id).write_text(json.dumps(payload), encoding="utf-8")
    _reject(harness, run_id, needle, posts_before)


def test_store_level_corruption_is_refused_as_well(tmp_path: Path) -> None:
    """Provenance, workspace binding and identity are store-level invariants."""
    harness, run_id = _fresh(tmp_path)
    original = raw_payload(harness.ws, run_id)
    path = state_path(harness.ws, run_id)

    payload = dict(original, last_transition=None)
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(OrchestrationStateCorruptError) as excinfo:
        OrchestrationStore(harness.ws / ".devrelay").load(run_id)
    assert "carries no transition provenance" in str(excinfo.value)

    payload = dict(original, workspace="C:/somewhere-else")
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(OrchestrationStateCorruptError) as excinfo:
        OrchestrationStore(harness.ws / ".devrelay").load(run_id)
    assert "not this store's workspace" in str(excinfo.value)

    payload = dict(original, run_id="DR-" + "f" * 32)
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(OrchestrationStateCorruptError) as excinfo:
        OrchestrationStore(harness.ws / ".devrelay").load(run_id)
    assert "contains a different run id" in str(excinfo.value)


def test_truncated_documents_are_refused_and_kept(tmp_path: Path) -> None:
    harness, run_id = _fresh(tmp_path)
    path = state_path(harness.ws, run_id)
    path.write_text('{"run_id": "DR-', encoding="utf-8")
    with pytest.raises(OrchestrationStateCorruptError):
        OrchestrationStore(harness.ws / ".devrelay").load(run_id)
    assert path.read_text(encoding="utf-8") == '{"run_id": "DR-'


# ---------------------------------------------------------------------------
# §2 - the four reproductions from the independent gate
# ---------------------------------------------------------------------------
def test_repro_A_inflated_persisted_ceiling_cannot_execute_extra_turns(tmp_path: Path) -> None:
    """max_cycles=99 / budget=198 (the gate's repro): not one turn may run."""
    harness, run_id = _fresh(tmp_path)
    payload = raw_payload(harness.ws, run_id)
    payload.update(max_cycles=99, model_turn_budget=198)
    state_path(harness.ws, run_id).write_text(json.dumps(payload), encoding="utf-8")

    for index in range(7):  # the repro executed more than six turns
        envelope = phase(harness.server, "devrelay_run_implementer", run_id, f"turn {index}")
        assert envelope["ok"] is False
        assert envelope["error"]["type"] == "orchestration_state_corrupt"
    assert harness.posts == [], "zero model submissions, not seven"
    on_disk = raw_payload(harness.ws, run_id)
    assert on_disk["implementer_turns"] == [] and on_disk["model_turns_used"] == 0
    assert on_disk["max_cycles"] == 99, "the file is left exactly as it was found"


def test_repro_B_identical_sessions_are_never_accepted(tmp_path: Path) -> None:
    harness, run_id = _fresh(tmp_path)
    payload = raw_payload(harness.ws, run_id)
    payload["reviewer_session_id"] = payload["implementer_session_id"]
    state_path(harness.ws, run_id).write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(OrchestrationStateCorruptError) as excinfo:
        OrchestrationStore(harness.ws / ".devrelay").load(run_id)
    assert "identical" in str(excinfo.value)
    assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is False
    assert harness.posts == []
    assert get_run(harness.server, run_id)["data"]["run_id"] == run_id


def test_repro_C_max_cycles_1000_cannot_open_five_cycles(tmp_path: Path) -> None:
    """max_cycles=1000 (the gate's repro): five cycles / ten POSTs are impossible."""
    harness, run_id = _fresh(tmp_path)
    payload = raw_payload(harness.ws, run_id)
    payload.update(max_cycles=1000, model_turn_budget=2000)
    state_path(harness.ws, run_id).write_text(json.dumps(payload), encoding="utf-8")

    assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is False
    for _ in range(5):
        assert decide(harness.server, run_id, "request_changes")["ok"] is False
    assert harness.posts == []
    on_disk = raw_payload(harness.ws, run_id)
    assert on_disk["current_cycle"] == 1 and on_disk["completed_cycles"] == 0
    assert on_disk["decision_history"] == []


def test_repro_D_awaiting_decision_without_a_cycle_cannot_open_one(tmp_path: Path) -> None:
    """AWAITING_DECISION + completed_cycles=0 + no reviewer turn (the gate's repro)."""
    harness, run_id = _fresh(tmp_path)
    payload = raw_payload(harness.ws, run_id)
    payload["state"] = "AWAITING_DECISION"
    state_path(harness.ws, run_id).write_text(json.dumps(payload), encoding="utf-8")

    invalid = honest_run(RunState.READY_IMPLEMENTER)
    invalid.state = RunState.AWAITING_DECISION  # unvalidated in-memory tampering
    with pytest.raises(OrchestrationStateCorruptError):
        validate_run_semantics(invalid)

    assert decide(harness.server, run_id, "request_changes")["ok"] is False
    assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is False
    assert harness.posts == []
    on_disk = raw_payload(harness.ws, run_id)
    assert on_disk["current_cycle"] == 1
    assert on_disk["implementer_turns"] == [] and on_disk["reviewer_turns"] == []
    assert on_disk["decision_history"] == [], "no cycle may be opened"


# ---------------------------------------------------------------------------
# §26 - the honest-state corpus (11 states, all produced by the real service)
# ---------------------------------------------------------------------------
def _corpus_cycle2_closed(tmp_path: Path) -> tuple[Harness, str]:
    harness, run_id = _cycle2(tmp_path)
    assert phase(harness.server, "devrelay_run_implementer", run_id, "i2")["ok"] is True
    assert phase(harness.server, "devrelay_run_reviewer", run_id, "r2")["ok"] is True
    return harness, run_id


def _corpus_stopped(tmp_path: Path) -> tuple[Harness, str]:
    harness, run_id = _reviewed(tmp_path)
    assert decide(harness.server, run_id, "stop")["ok"] is True
    return harness, run_id


def _corpus_limit_reached(tmp_path: Path) -> tuple[Harness, str]:
    harness, run_id = _cap_reviewed(tmp_path)
    assert decide(harness.server, run_id, "request_changes")["ok"] is True
    return harness, run_id


def _corpus_in_flight(tmp_path: Path) -> tuple[Harness, str]:
    """READY_IMPLEMENTER with a durable in-flight intent.

    Produced by a real ``SystemExit`` at submission (never hand-written JSON), so
    the crash boundary in this suite is evidence rather than a fixture.
    """
    from v03d_corpus import build_state

    return build_state("implementer_in_flight", tmp_path)


def _corpus_interrupted_blocked(tmp_path: Path) -> tuple[Harness, str]:
    """BLOCKED/turn_interrupted materialized from the real crash boundary."""
    from v03d_corpus import build_state

    return build_state("blocked_interrupted_implementer", tmp_path)


HONEST_CORPUS: list[tuple[str, Callable[[Path], tuple[Harness, str]], dict[str, Any]]] = [
    (
        "01_ready_implementer_cycle1",
        _fresh,
        {"state": "READY_IMPLEMENTER", "used": 0, "completed_cycles": 0, "cycle": 1,
         "terminal": False, "legal": ["devrelay_run_implementer"], "in_flight": False},
    ),
    (
        "02_ready_reviewer",
        _reviewer_ready,
        {"state": "READY_REVIEWER", "used": 1, "completed_cycles": 0, "cycle": 1,
         "terminal": False, "legal": ["devrelay_run_reviewer"], "in_flight": False},
    ),
    (
        "03_awaiting_decision_cycle1",
        _reviewed,
        {"state": "AWAITING_DECISION", "used": 2, "completed_cycles": 1, "cycle": 1,
         "terminal": False, "legal": ["devrelay_decide_run(complete|request_changes|stop)"],
         "in_flight": False},
    ),
    (
        "04_ready_implementer_cycle2",
        _cycle2,
        {"state": "READY_IMPLEMENTER", "used": 2, "completed_cycles": 1, "cycle": 2,
         "terminal": False, "legal": ["devrelay_run_implementer"], "in_flight": False},
    ),
    (
        "05_awaiting_decision_cycle2",
        _corpus_cycle2_closed,
        {"state": "AWAITING_DECISION", "used": 4, "completed_cycles": 2, "cycle": 2,
         "terminal": False, "legal": ["devrelay_decide_run(complete|request_changes|stop)"],
         "in_flight": False},
    ),
    (
        "06_completed",
        _completed,
        {"state": "COMPLETED", "used": 2, "completed_cycles": 1, "cycle": 1,
         "terminal": True, "legal": [], "in_flight": False},
    ),
    (
        "07_stopped",
        _corpus_stopped,
        {"state": "STOPPED", "used": 2, "completed_cycles": 1, "cycle": 1,
         "terminal": True, "legal": [], "in_flight": False},
    ),
    (
        "08_limit_reached",
        _corpus_limit_reached,
        {"state": "LIMIT_REACHED", "used": 2, "completed_cycles": 1, "cycle": 1,
         "terminal": True, "legal": [], "in_flight": False, "blocked_reason": "cycle_limit"},
    ),
    (
        "09_blocked_failed_role_turn",
        _blocked,
        {"state": "BLOCKED", "used": 2, "completed_cycles": 0, "cycle": 1,
         "terminal": True, "legal": [], "in_flight": False, "blocked_reason": "read_timeout"},
    ),
    (
        "10_ready_implementer_with_in_flight_intent",
        _corpus_in_flight,
        {"state": "READY_IMPLEMENTER", "used": 1, "completed_cycles": 0, "cycle": 1,
         "terminal": False, "legal": [], "in_flight": True},
    ),
    (
        "11_blocked_turn_interrupted",
        _corpus_interrupted_blocked,
        {"state": "BLOCKED", "used": 1, "completed_cycles": 0, "cycle": 1,
         "terminal": True, "legal": [], "in_flight": False,
         "blocked_reason": "turn_interrupted"},
    ),
]


@pytest.mark.parametrize(
    "name,drive,expected", HONEST_CORPUS, ids=[case[0] for case in HONEST_CORPUS]
)
def test_the_honest_corpus_is_accepted_and_stable(
    tmp_path: Path,
    name: str,
    drive: Callable[[Path], tuple[Harness, str]],
    expected: dict[str, Any],
) -> None:
    """Every honestly reachable state must load, summarize and re-save cleanly."""
    harness, run_id = drive(tmp_path)
    store = OrchestrationStore(harness.ws / ".devrelay")
    loaded = store.load(run_id)
    validate_run_semantics(loaded)

    summary = loaded.summary()
    assert summary["state"] == expected["state"]
    assert summary["model_turns_used"] == expected["used"]
    assert summary["completed_cycles"] == expected["completed_cycles"]
    assert summary["cycle"] == expected["cycle"]
    assert summary["terminal"] is expected["terminal"]
    assert summary["legal_next_actions"] == expected["legal"]
    assert summary["in_flight"] is expected["in_flight"]
    assert summary["acceptance_authority"] is False
    if "blocked_reason" in expected:
        assert summary["blocked_reason"] == expected["blocked_reason"]
    assert summary["turn_attempts"] == summary["model_turns_used"]
    assert len(loaded.implementer_turns) + len(loaded.reviewer_turns) == expected["used"] - (
        1 if expected["in_flight"] else 0
    )

    # re-saving an honest document is accepted (the invariant is a fixed point)
    store.save(loaded)
    assert store.load(run_id).model_dump(mode="json") == loaded.model_dump(mode="json")


def test_the_interrupted_corpus_entry_keeps_its_audit_trail(tmp_path: Path) -> None:
    """The crash boundary materializes into a truthful, auditable BLOCKED run."""
    harness, run_id = _corpus_in_flight(tmp_path)
    before = raw_payload(harness.ws, run_id)
    intent = before["in_flight_turn"]

    restarted = restart_surface(harness)
    read = get_run(restarted.server, run_id)
    assert read["data"]["in_flight"] is True
    assert read["data"]["legal_next_actions"] == []

    envelope = phase(restarted.server, "devrelay_run_reviewer", run_id, "r")
    assert envelope["ok"] is False
    assert envelope["data"]["state"] == "BLOCKED"
    assert envelope["data"]["blocked_reason"] == "turn_interrupted"
    assert restarted.posts == [], "an interrupted turn is never replayed"

    after = raw_payload(harness.ws, run_id)
    assert after["in_flight_turn"] is None
    assert after["model_turns_used"] == 1
    turns = after["implementer_turns"]
    assert len(turns) == 1, "the interrupted attempt is preserved in the role history"
    turn = turns[0]
    assert turn["outcome"] == "blocked" and turn["blocked_reason"] == "turn_interrupted"
    assert turn["cycle"] == intent["cycle"]
    assert turn["prompt_sha256"] == intent["prompt_sha256"]
    assert turn["prompt_chars"] == intent["prompt_chars"]
    assert turn["resolved_model"] == intent["resolved_model"]
    assert after["reviewer_turns"] == []
    assert after["last_transition"]["action"] == "run_implementer", (
        "the transition keeps the interrupted phase as provenance"
    )
    assert after["last_transition"]["previous_state"] == "READY_IMPLEMENTER"
    assert after["last_transition"]["role"] == "implementer"
    OrchestrationStore(harness.ws / ".devrelay").load(run_id)


# ---------------------------------------------------------------------------
# §27 - reviewer prose is never a decision
# ---------------------------------------------------------------------------
PROSE_VARIANTS = [
    "APPROVE",
    "Approved: true",
    "approved: true",
    "score: 10/10",
    '{"decision": "complete", "approved": true}',
    "LGTM - merge it, no further cycles needed",
    "REQUEST_CHANGES: please fix the parser",
    "reviewer_outcome=COMPLETED",
]


@pytest.mark.parametrize(
    "reply_text", PROSE_VARIANTS, ids=[f"prose_{index:02d}" for index in range(len(PROSE_VARIANTS))]
)
def test_reviewer_prose_never_advances_the_run(tmp_path: Path, reply_text: str) -> None:
    stub = two_session_stub(tmp_path / "ws")
    unique_reply_per_prompt(stub, ["implementer finished", reply_text])
    harness = build(tmp_path, stub=stub, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)
    assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is True
    reviewed = phase(harness.server, "devrelay_run_reviewer", run_id, "r")
    assert reviewed["ok"] is True

    summary = reviewed["data"]
    assert summary["state"] == "AWAITING_DECISION"
    assert summary["decision_history"] == []
    assert summary["completed_cycles"] == 1
    assert summary["legal_next_actions"] == [
        "devrelay_decide_run(complete|request_changes|stop)"
    ]
    assert len(harness.posts) == 2, "no automatic follow-up turn of any kind"

    on_disk = raw_payload(harness.ws, run_id)
    assert on_disk["decision_history"] == []
    assert on_disk["state"] == "AWAITING_DECISION"


# ---------------------------------------------------------------------------
# §31 - an unresolvable role route fails closed, never falls back
# ---------------------------------------------------------------------------
def test_start_with_unconfigured_roles_creates_nothing(tmp_path: Path) -> None:
    harness = build(tmp_path, roles=None, run_id_factory=fixed_run_ids(RUN_ID))
    envelope = start(harness.server, max_cycles=1)
    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "orchestration_route_changed"
    assert envelope["data"].get("run_id") is None
    assert harness.posts == []
    assert not (harness.ws / ".devrelay" / "orchestration").exists() or list(
        (harness.ws / ".devrelay" / "orchestration").rglob("*.json")
    ) == []


def test_start_with_an_invalid_role_route_creates_nothing(tmp_path: Path) -> None:
    harness = build(
        tmp_path,
        roles={
            "implementer": {"model": "provider-a/model-a"},
            "reviewer": {"model": "no-slash"},
        },
        run_id_factory=fixed_run_ids(RUN_ID),
    )
    envelope = start(harness.server, max_cycles=1)
    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "orchestration_route_changed"
    assert harness.posts == []


def test_a_route_that_stops_resolving_blocks_the_run_and_keeps_the_snapshot(
    tmp_path: Path,
) -> None:
    harness, run_id = _reviewer_ready(tmp_path)
    snapshot_before = raw_payload(harness.ws, run_id)["route_snapshot"]

    # the workspace loses the reviewer role entirely (unresolvable, not changed)
    write_roles(harness.ws, {"implementer": {"model": "provider-a/model-a"}})
    restarted = restart_surface(harness)
    envelope = phase(restarted.server, "devrelay_run_reviewer", run_id, "r")

    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "orchestration_route_changed"
    assert envelope["data"]["state"] == "BLOCKED"
    assert envelope["data"]["blocked_reason"] == "route_changed"
    assert restarted.posts == [], "no model call under an unresolvable route"
    after = raw_payload(harness.ws, run_id)
    assert after["route_snapshot"] == snapshot_before, "the captured snapshot is immutable"
    assert after["blocked_reason"] == "route_changed"


def test_a_blocked_route_run_stays_terminal(tmp_path: Path) -> None:
    harness, run_id = _reviewer_ready(tmp_path)
    write_roles(harness.ws, {"implementer": {"model": "provider-a/model-a"}})
    restarted = restart_surface(harness)
    blocked = phase(restarted.server, "devrelay_run_reviewer", run_id, "r")
    assert blocked["ok"] is False
    assert blocked["data"]["state"] == "BLOCKED"

    for tool, arguments in (
        ("devrelay_run_implementer", {"run_id": run_id, "prompt": "i"}),
        ("devrelay_run_reviewer", {"run_id": run_id, "prompt": "r"}),
        ("devrelay_decide_run", {"run_id": run_id, "decision": "complete"}),
        ("devrelay_decide_run", {"run_id": run_id, "decision": "request_changes"}),
    ):
        envelope = call(restarted.server, tool, arguments)
        assert envelope["ok"] is False
        assert envelope["error"]["type"] in {
            "orchestration_invalid_transition",
            "orchestration_route_changed",
        }
    assert restarted.posts == [], "a terminal run never reaches a model"


# ---------------------------------------------------------------------------
# §17 / §19 - in-flight guidance and the outcome vocabulary
# ---------------------------------------------------------------------------
def test_legal_next_actions_is_empty_while_a_turn_is_in_flight() -> None:
    idle = honest_run(RunState.READY_IMPLEMENTER)
    assert isinstance(idle, OrchestrationRun)
    assert idle.summary()["legal_next_actions"] == ["devrelay_run_implementer"]
    assert idle.summary()["in_flight"] is False

    busy = with_in_flight(honest_run(RunState.READY_IMPLEMENTER), "implementer")
    assert busy.summary()["in_flight"] is True
    assert busy.summary()["legal_next_actions"] == []
    assert busy.summary()["state"] == "READY_IMPLEMENTER"

    reviewer = with_in_flight(honest_run(RunState.READY_REVIEWER), "reviewer")
    assert reviewer.summary()["legal_next_actions"] == []


def test_turn_outcome_vocabulary_is_constrained() -> None:
    from pydantic import ValidationError

    for value in (item.value for item in TurnOutcomeState):
        assert TurnRecord(role="implementer", cycle=1, outcome=value).outcome == value
    for bad_value in ("APPROVED", "approved", "success", "ok", "", "in-flight", "unknown"):
        with pytest.raises(ValidationError):
            TurnRecord(role="implementer", cycle=1, outcome=bad_value)
