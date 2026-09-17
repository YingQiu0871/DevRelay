"""v0.3-D orchestration service: bounds, authority, fail-closed, persistence.

Offline: the real service over the real v0.3-C role router and the accepted
v0.3-A bridge wired to the deterministic OpenCode stub.
"""

from __future__ import annotations

import json

import pytest

from devrelay.errors import OrchestrationStateCorruptError

from opencode_stub import StubOpenCodeServer
from v03d_helpers import (
    IMPLEMENTER_SESSION,
    REVIEWER_SESSION,
    RUN_ID,
    build,
    call,
    decide,
    fixed_run_ids,
    get_run,
    phase,
    raw_payload,
    run_id_of,
    start,
    two_session_stub,
    write_roles,
)


def impl_posts(harness) -> list[str]:
    return [p for m, p in harness.stub.requests if m == "POST" and IMPLEMENTER_SESSION in p]


def rev_posts(harness) -> list[str]:
    return [p for m, p in harness.stub.requests if m == "POST" and REVIEWER_SESSION in p]


def both_posts(harness) -> list[str]:
    return [p for m, p in harness.stub.requests if m == "POST"]


# ---------------------------------------------------------------------------
# A. start_run
# ---------------------------------------------------------------------------
def test_start_run_creates_bounded_state_with_zero_model_posts(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    envelope = start(harness.server, max_cycles=2)
    assert envelope["ok"] is True
    data = envelope["data"]
    assert data["run_id"] == RUN_ID
    assert data["state"] == "READY_IMPLEMENTER"
    assert data["cycle"] == 1 and data["completed_cycles"] == 0
    assert data["max_cycles"] == 2
    assert data["model_turn_budget"] == 4
    assert data["model_turns_used"] == 0
    assert data["terminal"] is False
    assert data["legal_next_actions"] == ["devrelay_run_implementer"]
    assert both_posts(harness) == [], "start_run must never perform a model POST"
    assert all(record.method == "GET" for record in harness.ledger.records())


def test_start_run_captures_sanitized_route_snapshots(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    data = start(harness.server, max_cycles=1)["data"]
    assert data["route_snapshot"]["implementer"]["model"] == "provider-a/model-a"
    assert data["route_snapshot"]["reviewer"]["model"] == "provider-b/model-b"
    assert data["route_snapshot"]["reviewer"]["route_source"] == "workspace_config"
    assert data["route_snapshot"]["reviewer"]["agent"] is None


def test_start_run_ignores_a_caller_prompt_because_it_accepts_none(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    import asyncio

    result = asyncio.run(
        harness.server.call_tool(
            "devrelay_start_run",
            {
                "implementer_session_id": IMPLEMENTER_SESSION,
                "reviewer_session_id": REVIEWER_SESSION,
                "max_cycles": 1,
                "prompt": "sneaky task prompt",
            },
        )
    )
    assert result.structured_content["ok"] is True
    payload = raw_payload(harness.ws, RUN_ID)
    assert "sneaky task prompt" not in json.dumps(payload)


@pytest.mark.parametrize("max_cycles", [0, 4, -1, 10])
def test_start_run_rejects_out_of_bound_cycles(tmp_path, max_cycles):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    envelope = start(harness.server, max_cycles=max_cycles)
    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "mcp_invalid_argument"
    assert both_posts(harness) == []
    assert not (harness.ws / ".devrelay" / "orchestration" / "runs").exists() or not list(
        (harness.ws / ".devrelay" / "orchestration" / "runs").glob("*.json")
    )


def test_start_run_accepts_the_hard_bound_but_not_beyond(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    assert start(harness.server, max_cycles=3)["data"]["model_turn_budget"] == 6
    assert start(harness.server, max_cycles=4)["error"]["type"] == "mcp_invalid_argument"


def test_identical_role_sessions_are_rejected(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    envelope = start(
        harness.server,
        implementer_session=IMPLEMENTER_SESSION,
        reviewer_session=IMPLEMENTER_SESSION,
    )
    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "orchestration_session_conflict"
    assert both_posts(harness) == []


def test_foreign_or_missing_sessions_fail_before_a_run_exists(tmp_path):
    stub = two_session_stub(tmp_path / "ws") if False else None  # placeholder
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    # make the reviewer session foreign
    harness.stub.sessions[1]["directory"] = "C:/elsewhere"
    envelope = start(harness.server, max_cycles=2)
    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "orchestration_session_conflict"
    assert both_posts(harness) == []
    runs = harness.ws / ".devrelay" / "orchestration" / "runs"
    assert not runs.exists() or list(runs.glob("*.json")) == []


def test_unknown_session_fails_before_a_run_exists(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    harness.stub.sessions = [s for s in harness.stub.sessions if s["id"] == IMPLEMENTER_SESSION]
    envelope = start(harness.server, max_cycles=2)
    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "orchestration_session_conflict"
    assert both_posts(harness) == []


# ---------------------------------------------------------------------------
# B. happy paths
# ---------------------------------------------------------------------------
def test_one_cycle_happy_path_uses_exactly_two_model_posts(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)

    impl = phase(harness.server, "devrelay_run_implementer", run_id, "implement it")
    assert impl["ok"] is True
    assert impl["data"]["state"] == "READY_REVIEWER"
    assert impl["data"]["model_turns_used"] == 1
    assert len(impl_posts(harness)) == 1 and rev_posts(harness) == []

    rev = phase(harness.server, "devrelay_run_reviewer", run_id, "review it")
    assert rev["ok"] is True
    assert rev["data"]["state"] == "AWAITING_DECISION"
    assert rev["data"]["completed_cycles"] == 1
    assert len(impl_posts(harness)) == 1 and len(rev_posts(harness)) == 1

    done = decide(harness.server, run_id, "complete")
    assert done["ok"] is True
    assert done["data"]["state"] == "COMPLETED"
    assert done["data"]["terminal"] is True
    assert both_posts(harness) == impl_posts(harness) + rev_posts(harness)
    assert len(both_posts(harness)) == 2, "exactly two model POSTs in a one-cycle run"


def test_two_cycle_request_changes_flow_uses_four_model_posts(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)

    for cycle in (1, 2):
        impl = phase(harness.server, "devrelay_run_implementer", run_id, f"impl {cycle}")
        assert impl["ok"] is True and impl["data"]["cycle"] == cycle
        rev = phase(harness.server, "devrelay_run_reviewer", run_id, f"rev {cycle}")
        assert rev["ok"] is True
        assert rev["data"]["state"] == "AWAITING_DECISION"
        assert rev["data"]["completed_cycles"] == cycle
        decision = "request_changes" if cycle == 1 else "complete"
        decided = decide(harness.server, run_id, decision)
        assert decided["ok"] is True

    final = get_run(harness.server, run_id)["data"]
    assert final["state"] == "COMPLETED"
    assert final["completed_cycles"] == 2
    assert len(impl_posts(harness)) == 2 and len(rev_posts(harness)) == 2
    assert len(both_posts(harness)) == 4


def test_hard_cap_three_cycles_then_limit_reached_without_a_seventh_call(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=3)

    for cycle in (1, 2, 3):
        assert phase(harness.server, "devrelay_run_implementer", run_id, f"i{cycle}")["ok"] is True
        rev = phase(harness.server, "devrelay_run_reviewer", run_id, f"r{cycle}")
        assert rev["ok"] is True and rev["data"]["completed_cycles"] == cycle
        if cycle < 3:
            assert decide(harness.server, run_id, "request_changes")["data"]["state"] == "READY_IMPLEMENTER"

    assert len(both_posts(harness)) == 6, "3 cycles x (1 implementer + 1 reviewer)"
    limited = decide(harness.server, run_id, "request_changes")
    assert limited["ok"] is True
    assert limited["data"]["state"] == "LIMIT_REACHED"
    assert limited["data"]["blocked_reason"] == "cycle_limit"
    assert limited["data"]["terminal"] is True
    assert len(both_posts(harness)) == 6, "LIMIT_REACHED spends no model turn"
    after = phase(harness.server, "devrelay_run_implementer", run_id, "cycle 4")
    assert after["ok"] is False
    assert after["error"]["type"] == "orchestration_invalid_transition"
    assert len(both_posts(harness)) == 6


def test_stop_is_a_terminal_administrative_transition(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)
    phase(harness.server, "devrelay_run_implementer", run_id, "i")
    phase(harness.server, "devrelay_run_reviewer", run_id, "r")
    stopped = decide(harness.server, run_id, "stop")
    assert stopped["data"]["state"] == "STOPPED" and stopped["data"]["terminal"] is True
    assert len(both_posts(harness)) == 2


# ---------------------------------------------------------------------------
# C. the Planner is authoritative: reviewer text never drives state
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("reply", ["APPROVE", "REQUEST_CHANGES", "LGTM", "PASS", "FAIL"])
def test_reviewer_prose_never_drives_the_state_machine(tmp_path, reply):
    from test_v03b_mcp_tools import real_reply

    stub = two_session_stub(tmp_path / "ws", prompt_reply=real_reply(message_id="msg_impl", text="implemented"))
    harness = build(tmp_path, stub=stub, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)
    assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is True
    stub.prompt_reply = real_reply(message_id=f"msg_review_{reply}", text=reply)
    reviewed = phase(harness.server, "devrelay_run_reviewer", run_id, "r")

    assert reviewed["ok"] is True
    assert reviewed["data"]["state"] == "AWAITING_DECISION", (
        f"reviewer text {reply!r} must never advance the run"
    )
    assert len(both_posts(harness)) == 2, "no automatic follow-up call"
    assert reviewed["data"]["decision_history"] == []

    # only an explicit external decision may advance it
    decided = decide(harness.server, run_id, "complete")
    assert decided["data"]["state"] == "COMPLETED"
    record = decided["data"]["decision_history"][-1]
    assert record["decision"] == "complete"
    assert record["source"] == "external_planner"


def test_request_changes_text_does_not_start_the_next_cycle(tmp_path):
    from test_v03b_mcp_tools import real_reply

    stub = two_session_stub(tmp_path / "ws", prompt_reply=real_reply(message_id="msg_impl", text="implemented"))
    harness = build(tmp_path, stub=stub, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)
    assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is True
    stub.prompt_reply = real_reply(message_id="msg_r", text="REQUEST_CHANGES: fix the parser")
    phase(harness.server, "devrelay_run_reviewer", run_id, "r")
    assert len(both_posts(harness)) == 2, "reviewer prose must not trigger another implementer turn"
    state = get_run(harness.server, run_id)["data"]["state"]
    assert state == "AWAITING_DECISION"


def test_orchestration_never_claims_reviewer_approval(tmp_path):
    from test_v03b_mcp_tools import real_reply

    stub = two_session_stub(tmp_path / "ws", prompt_reply=real_reply(message_id="msg_impl", text="implemented"))
    harness = build(tmp_path, stub=stub, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)
    assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is True
    stub.prompt_reply = real_reply(message_id="msg_approve", text="APPROVE")
    reviewed = phase(harness.server, "devrelay_run_reviewer", run_id, "r")
    blob = json.dumps(reviewed)
    for forbidden in ("reviewer_approved", "approved", "verdict", "review_passed", "decision\""):
        assert forbidden not in blob, forbidden
    assert reviewed["data"]["acceptance_authority"] is False


# ---------------------------------------------------------------------------
# D. invalid transitions
# ---------------------------------------------------------------------------
def test_reviewer_before_implementer_is_refused(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)
    envelope = phase(harness.server, "devrelay_run_reviewer", run_id, "r")
    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "orchestration_invalid_transition"
    assert envelope["data"]["state"] == "READY_IMPLEMENTER"
    assert both_posts(harness) == []


def test_decision_before_reviewer_is_refused(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)
    phase(harness.server, "devrelay_run_implementer", run_id, "i")
    envelope = decide(harness.server, run_id, "complete")
    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "orchestration_invalid_transition"
    assert envelope["data"]["state"] == "READY_REVIEWER"
    assert len(both_posts(harness)) == 1


def test_implementer_twice_is_refused_without_a_second_post(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)
    assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is True
    again = phase(harness.server, "devrelay_run_implementer", run_id, "i again")
    assert again["ok"] is False
    assert again["error"]["type"] == "orchestration_invalid_transition"
    assert len(impl_posts(harness)) == 1, "the duplicate guard prevents a second submission"
    assert len(both_posts(harness)) == 1


def test_reviewer_twice_is_refused_without_a_second_post(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)
    phase(harness.server, "devrelay_run_implementer", run_id, "i")
    phase(harness.server, "devrelay_run_reviewer", run_id, "r")
    again = phase(harness.server, "devrelay_run_reviewer", run_id, "r again")
    assert again["ok"] is False
    assert len(rev_posts(harness)) == 1


def test_implementer_and_reviewer_while_awaiting_decision_are_refused(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)
    phase(harness.server, "devrelay_run_implementer", run_id, "i")
    phase(harness.server, "devrelay_run_reviewer", run_id, "r")
    for tool in ("devrelay_run_implementer", "devrelay_run_reviewer"):
        envelope = phase(harness.server, tool, run_id, "x")
        assert envelope["ok"] is False
        assert envelope["error"]["type"] == "orchestration_invalid_transition"
        assert envelope["data"]["state"] == "AWAITING_DECISION"
    assert len(both_posts(harness)) == 2


def test_complete_twice_and_request_changes_after_complete_are_refused(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)
    phase(harness.server, "devrelay_run_implementer", run_id, "i")
    phase(harness.server, "devrelay_run_reviewer", run_id, "r")
    assert decide(harness.server, run_id, "complete")["ok"] is True
    for decision in ("complete", "request_changes", "stop"):
        envelope = decide(harness.server, run_id, decision)
        assert envelope["ok"] is False
        assert envelope["error"]["type"] == "orchestration_invalid_transition"
        assert envelope["data"]["state"] == "COMPLETED"
    assert len(both_posts(harness)) == 2


def test_model_bearing_actions_after_stop_or_block_are_refused(tmp_path):
    # STOPPED
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    stopped_id = run_id_of(harness.server, max_cycles=1)
    phase(harness.server, "devrelay_run_implementer", stopped_id, "i")
    phase(harness.server, "devrelay_run_reviewer", stopped_id, "r")
    decide(harness.server, stopped_id, "stop")
    assert phase(harness.server, "devrelay_run_implementer", stopped_id, "i")["error"]["type"] == (
        "orchestration_invalid_transition"
    )

    # BLOCKED (a failing implementer turn)
    failing = build(
        tmp_path / "blocked",
        stub=two_session_stub(tmp_path / "blocked" / "ws", prompt_exception="read_timeout"),
        run_id_factory=fixed_run_ids("DR-" + "b" * 32),
    )
    blocked_id = run_id_of(failing.server, max_cycles=1)
    blocked = phase(failing.server, "devrelay_run_implementer", blocked_id, "i")
    assert blocked["ok"] is False and blocked["data"]["state"] == "BLOCKED"
    again = phase(failing.server, "devrelay_run_implementer", blocked_id, "i")
    assert again["error"]["type"] == "orchestration_invalid_transition"
    assert len(both_posts(failing)) == 1


def test_unknown_run_id_and_corrupt_run_fail_closed(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    missing = get_run(harness.server, "DR-" + "f" * 32)
    assert missing["ok"] is False
    assert missing["error"]["type"] == "orchestration_run_not_found"

    run_id = run_id_of(harness.server, max_cycles=1)
    path = harness.ws / ".devrelay" / "orchestration" / "runs" / f"{run_id}.json"
    path.write_text("{corrupt", encoding="utf-8")
    corrupt = phase(harness.server, "devrelay_run_implementer", run_id, "i")
    assert corrupt["ok"] is False
    assert corrupt["error"]["type"] == "orchestration_state_corrupt"
    assert both_posts(harness) == []
    assert path.read_text(encoding="utf-8") == "{corrupt", "a corrupt run is never reset"


@pytest.mark.parametrize("decision", ["approve", "reject", "merge", "retry", "rerun", "", None])
def test_unsupported_decisions_are_refused(tmp_path, decision):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)
    phase(harness.server, "devrelay_run_implementer", run_id, "i")
    phase(harness.server, "devrelay_run_reviewer", run_id, "r")
    envelope = call(harness.server, "devrelay_decide_run", {"run_id": run_id, "decision": decision})
    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "mcp_invalid_argument"
    assert envelope["data"]["state"] == "AWAITING_DECISION", (
        "a run-scoped argument failure still reports the current run state"
    )
    assert envelope["data"]["run_id"] == run_id
    assert len(both_posts(harness)) == 2


def test_a_non_string_decision_is_rejected_at_the_sdk_boundary(tmp_path):
    import asyncio

    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)
    phase(harness.server, "devrelay_run_implementer", run_id, "i")
    phase(harness.server, "devrelay_run_reviewer", run_id, "r")
    with pytest.raises(Exception) as excinfo:
        asyncio.run(harness.server.call_tool("devrelay_decide_run", {"run_id": run_id, "decision": 7}))
    assert "decision" in str(excinfo.value)
    assert len(both_posts(harness)) == 2, "the SDK schema rejection spends no model turn"


# ---------------------------------------------------------------------------
# E. failure matrices (fail closed, never retry, never the other role)
# ---------------------------------------------------------------------------
IMPLEMENTER_FAILURES = [
    ("connect_error", {"prompt_exception": "connect_error"}),
    ("connect_timeout", {"prompt_exception": "connect_timeout"}),
    ("read_timeout", {"prompt_exception": "read_timeout"}),
    ("write_timeout", {"prompt_exception": "write_timeout"}),
    ("read_error", {"prompt_exception": "read_error"}),
    ("write_error", {"prompt_exception": "write_error"}),
    ("remote_protocol_error", {"prompt_exception": "remote_protocol_error"}),
    ("malformed_2xx", {"prompt_html_fallback": True}),
    ("http_500", {"prompt_http_status": 500}),
    ("accepted_pending", {"prompt_raw_reply": {"ok": True}}),
]


@pytest.mark.parametrize(
    "label,stub_kwargs", IMPLEMENTER_FAILURES, ids=[case[0] for case in IMPLEMENTER_FAILURES]
)
def test_implementer_failure_blocks_the_run_without_a_reviewer_turn(tmp_path, label, stub_kwargs):
    stub = two_session_stub(tmp_path / "ws", **stub_kwargs)
    harness = build(tmp_path, stub=stub, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)
    envelope = phase(harness.server, "devrelay_run_implementer", run_id, "i")

    assert envelope["ok"] is False, label
    assert envelope["data"]["state"] == "BLOCKED", label
    assert envelope["data"]["terminal"] is True
    assert envelope["data"]["blocked_reason"], label
    assert envelope["data"]["model_turns_used"] == 1, label
    assert rev_posts(harness) == [], f"{label}: the reviewer must never be invoked"
    assert len(impl_posts(harness)) <= 1, f"{label}: no retry"
    # reviewer phase is refused from the blocked state
    assert phase(harness.server, "devrelay_run_reviewer", run_id, "r")["error"]["type"] == (
        "orchestration_invalid_transition"
    )
    # and the decision path is refused too
    assert decide(harness.server, run_id, "complete")["error"]["type"] == (
        "orchestration_invalid_transition"
    )


@pytest.mark.parametrize(
    "label,stub_kwargs", IMPLEMENTER_FAILURES, ids=[case[0] for case in IMPLEMENTER_FAILURES]
)
def test_reviewer_failure_blocks_the_run_without_another_cycle(tmp_path, label, stub_kwargs):
    from test_v03b_mcp_tools import real_reply

    stub = two_session_stub(
        tmp_path / "ws", prompt_reply=real_reply(message_id="msg_impl_ok", text="implemented")
    )
    harness = build(tmp_path, stub=stub, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)

    # the implementer succeeds, then the reviewer phase hits the failure knob
    assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is True
    stub.prompt_reply = None
    for key, value in stub_kwargs.items():
        setattr(stub, key, value)

    envelope = phase(harness.server, "devrelay_run_reviewer", run_id, "r")
    assert envelope["ok"] is False, label
    assert envelope["data"]["state"] == "BLOCKED", label
    assert envelope["data"]["model_turns_used"] == 2, label
    assert len(impl_posts(harness)) == 1, f"{label}: no further implementer turn"
    assert len(rev_posts(harness)) <= 1, f"{label}: no reviewer retry"
    assert decide(harness.server, run_id, "complete")["error"]["type"] == (
        "orchestration_invalid_transition"
    )


def test_uncertain_submission_blocks_and_records_durable_evidence(tmp_path):
    stub = two_session_stub(tmp_path / "ws", prompt_exception="read_timeout")
    harness = build(tmp_path, stub=stub, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)
    envelope = phase(harness.server, "devrelay_run_implementer", run_id, "i")

    turn = envelope["data"]["implementer_turns"][-1]
    assert turn["outcome"] == "blocked"
    assert turn["submission_uncertain"] is True
    assert turn["reply_pending"] is True
    assert turn["retry_safe"] is False
    assert turn["call_ids"], "durable call ids are kept as evidence"
    assert envelope["data"]["blocked_reason"] == "read_timeout"
    assert turn["blocked_reason"] == "read_timeout"
    payload = raw_payload(harness.ws, run_id)
    assert payload["state"] == "BLOCKED"
    assert payload["blocked_reason"] == "read_timeout"


# ---------------------------------------------------------------------------
# F. route snapshot and session ownership invariants
# ---------------------------------------------------------------------------
def test_a_changed_role_route_fails_the_run_closed(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)
    assert phase(harness.server, "devrelay_run_implementer", run_id, "i")["ok"] is True

    # the same workspace is rebuilt with a different reviewer route
    write_roles(harness.ws, {"implementer": {"model": "provider-a/model-a"}, "reviewer": {"model": "provider-z/model-z"}})
    changed_stub = two_session_stub(harness.ws)
    changed = build(harness.ws.parent, stub=changed_stub) if False else None
    from devrelay.mcp.server import build_surface, create_server
    from devrelay.opencode.accounting import FilesystemOpenCodeLedger

    ledger = FilesystemOpenCodeLedger(harness.ws / ".devrelay")
    surface = build_surface(
        harness.ws, bridge_factory=lambda: changed_stub.bridge(workspace_root=str(harness.ws), ledger=ledger)
    )
    server = create_server(surface)

    envelope = phase(server, "devrelay_run_reviewer", run_id, "r")
    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "orchestration_route_changed"
    assert envelope["data"]["state"] == "BLOCKED"
    assert envelope["data"]["blocked_reason"] == "route_changed"
    assert [p for m, p in changed_stub.requests if m == "POST"] == [], (
        "no model POST may happen under a changed route"
    )


def test_a_session_that_stops_being_owned_blocks_the_run(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)
    harness.stub.sessions[0]["directory"] = "C:/elsewhere"
    envelope = phase(harness.server, "devrelay_run_implementer", run_id, "i")
    assert envelope["ok"] is False
    assert envelope["error"]["type"] == "orchestration_session_conflict"
    assert envelope["data"]["state"] == "BLOCKED"
    assert envelope["data"]["blocked_reason"] == "session_not_owned"
    assert both_posts(harness) == []


# ---------------------------------------------------------------------------
# G. persistence, restart and interrupted turns (no recovery claims)
# ---------------------------------------------------------------------------
def test_get_run_reads_durable_state_without_network_or_mutation(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)
    phase(harness.server, "devrelay_run_implementer", run_id, "i")
    before_requests = list(harness.stub.requests)
    before_bytes = (harness.ws / ".devrelay" / "orchestration" / "runs" / f"{run_id}.json").read_bytes()

    envelope = get_run(harness.server, run_id)
    assert envelope["ok"] is True
    assert envelope["data"]["state"] == "READY_REVIEWER"
    assert list(harness.stub.requests) == before_requests, "get_run performs no OpenCode request"
    after_bytes = (harness.ws / ".devrelay" / "orchestration" / "runs" / f"{run_id}.json").read_bytes()
    assert after_bytes == before_bytes, "get_run must not mutate the run"


def test_a_new_service_reads_the_same_run_after_a_restart(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)
    phase(harness.server, "devrelay_run_implementer", run_id, "i")

    # a brand-new surface/service over the same workspace (process-restart stand-in)
    from devrelay.mcp.server import build_surface, create_server
    from devrelay.opencode.accounting import FilesystemOpenCodeLedger

    restarted_stub = two_session_stub(harness.ws)
    ledger = FilesystemOpenCodeLedger(harness.ws / ".devrelay")
    surface = build_surface(
        harness.ws, bridge_factory=lambda: restarted_stub.bridge(workspace_root=str(harness.ws), ledger=ledger)
    )
    server = create_server(surface)

    envelope = get_run(server, run_id)
    assert envelope["ok"] is True
    assert envelope["data"]["state"] == "READY_REVIEWER"
    assert envelope["data"]["run_id"] == run_id
    assert [p for m, p in restarted_stub.requests if m == "POST"] == []

    reviewed = phase(server, "devrelay_run_reviewer", run_id, "r")
    assert reviewed["ok"] is True
    assert reviewed["data"]["state"] == "AWAITING_DECISION"
    assert len([p for m, p in restarted_stub.requests if m == "POST"]) == 1


def test_a_persisted_in_flight_turn_is_never_replayed(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)
    path = harness.ws / ".devrelay" / "orchestration" / "runs" / f"{run_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["in_flight_turn"] = {
        "role": "implementer",
        "cycle": 1,
        "prompt_sha256": "deadbeef",
        "prompt_chars": 4,
        "resolved_model": "provider-a/model-a",
        "outcome": "in_flight",
    }
    payload["turn_attempts"] = 1
    payload["model_turns_used"] = 1
    path.write_text(json.dumps(payload), encoding="utf-8")

    # reading stays truthful (the attempt is visible, nothing is replayed)
    read = get_run(harness.server, run_id)
    assert read["data"]["in_flight"] is True
    assert read["data"]["state"] == "READY_IMPLEMENTER"

    # the next mutating action fails the run closed without any model call
    envelope = phase(harness.server, "devrelay_run_implementer", run_id, "i")
    assert envelope["ok"] is False
    assert envelope["data"]["state"] == "BLOCKED"
    assert envelope["data"]["blocked_reason"] == "turn_interrupted"
    assert both_posts(harness) == [], "an interrupted turn is never replayed"
    assert get_run(harness.server, run_id)["data"]["state"] == "BLOCKED"


# ---------------------------------------------------------------------------
# H. persistence content policy
# ---------------------------------------------------------------------------
def test_persisted_runs_hold_no_prompts_replies_or_credentials(tmp_path, monkeypatch):
    from test_v03b_mcp_tools import real_reply

    monkeypatch.setenv("DEVRELAY_OPENCODE_TOKEN", "oc-token-V03D-SENTINEL-4711")
    prompt_sentinel = "PROMPT-SENTINEL-V03D-4711"
    reply_sentinel = "REPLY-SENTINEL-V03D-4711"
    stub = two_session_stub(
        tmp_path / "ws", prompt_reply=real_reply(message_id="msg_reply", text=reply_sentinel)
    )
    harness = build(tmp_path, stub=stub, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)
    phase(harness.server, "devrelay_run_implementer", run_id, prompt_sentinel)
    phase(harness.server, "devrelay_run_reviewer", run_id, prompt_sentinel)
    decide(harness.server, run_id, "complete")

    blob = (harness.ws / ".devrelay" / "orchestration" / "runs" / f"{run_id}.json").read_text(
        encoding="utf-8"
    )
    assert prompt_sentinel not in blob
    assert reply_sentinel not in blob
    assert "oc-token-V03D-SENTINEL-4711" not in blob
    assert "Authorization" not in blob and "Bearer" not in blob
    payload = json.loads(blob)
    assert payload["implementer_turns"][0]["prompt_sha256"]
    assert payload["implementer_turns"][0]["prompt_chars"] == len(prompt_sentinel)
    assert payload["implementer_turns"][0]["assistant_message_ids"] == ["msg_reply"]


def test_turn_evidence_carries_routes_and_call_ids(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)
    envelope = phase(harness.server, "devrelay_run_implementer", run_id, "i")
    turn = envelope["data"]["implementer_turns"][-1]
    assert turn["resolved_model"] == "provider-a/model-a"
    assert turn["route_source"] == "workspace_config"
    assert turn["operation_state"] == "COMPLETED"
    assert turn["submission_attempted"] is True
    assert turn["submission_status"] == 200
    assert turn["submission_uncertain"] is False
    assert turn["reply_pending"] is False
    assert turn["call_ids"]
    assert turn["role"] == "implementer" and turn["cycle"] == 1


def test_model_turn_accounting_is_exact(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)
    assert get_run(harness.server, run_id)["data"]["model_turns_used"] == 0
    phase(harness.server, "devrelay_run_implementer", run_id, "i")
    assert get_run(harness.server, run_id)["data"]["model_turns_used"] == 1
    phase(harness.server, "devrelay_run_reviewer", run_id, "r")
    data = get_run(harness.server, run_id)["data"]
    assert data["model_turns_used"] == 2
    assert data["model_turn_budget"] == 4
    assert data["model_turns_remaining"] == 2
    assert data["turn_attempts"] == 2


def test_decision_history_records_only_external_decisions(tmp_path):
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)
    for cycle, decision in ((1, "request_changes"), (2, "complete")):
        phase(harness.server, "devrelay_run_implementer", run_id, f"i{cycle}")
        phase(harness.server, "devrelay_run_reviewer", run_id, f"r{cycle}")
        decide(harness.server, run_id, decision)
    history = get_run(harness.server, run_id)["data"]["decision_history"]
    assert [item["decision"] for item in history] == ["request_changes", "complete"]
    assert all(item["source"] == "external_planner" for item in history)
