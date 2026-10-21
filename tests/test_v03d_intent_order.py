"""v0.3-D remediation: intent-before-submission ordering and turn accounting.

This module proves the two claims that the independent gate could not verify from
the previous evidence:

* **§14** the durable in-flight intent is committed to disk *before* the role
  call reaches submission (observed through a transport-level callback, with no
  sleeps and no polling);
* **§15** ``model_turns_used`` counts *reserved orchestration turn slots*: a slot
  is consumed when the durable intent is written, is never refunded, and always
  has exactly one matching turn record once the turn ends.

The same callback is used to simulate a real process death (``SystemExit``, which
the service's defensive ``except Exception`` boundary deliberately does not
catch) so the crash boundary can be produced honestly rather than by hand-editing
files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from devrelay.opencode.models import prompt_digest
from devrelay.orchestration import OrchestrationStore

from v03d_helpers import (
    RUN_ID,
    build,
    decide,
    fixed_run_ids,
    freeze_v03d,
    get_run,
    phase,
    raw_payload,
    restart_surface,
    run_id_of,
    two_session_stub,
)

PROMPT = "intent-first implementer prompt"
REVIEWER_PROMPT = "intent-first reviewer prompt"


def only_run_document(ws: Path) -> dict[str, Any]:
    """The single durable run document of this workspace, read from disk."""
    runs = sorted((ws / ".devrelay" / "orchestration" / "runs").glob("DR-*.json"))
    assert len(runs) == 1, runs
    return json.loads(runs[0].read_text(encoding="utf-8"))


def observing_stub(ws: Path, sink: list[dict[str, Any]]) -> Any:
    """A stub that snapshots the durable document at each prompt submission.

    The transport callback runs *before* the accepted bridge sees a response, and
    the stub records the request only after this snapshot, so
    ``posts_recorded_so_far == 0`` proves the intent was already durable before
    the submission left the process.  The stub must be patched before the harness
    is built: the accepted bridge binds its transport handler once, at creation.
    """
    stub = two_session_stub(ws)
    original = stub.handler
    state = {"posts": 0}

    def handler(request: Any) -> Any:
        if request.method.upper() == "POST" and request.url.path.endswith("/message"):
            state["posts"] += 1
            sink.append(
                {
                    "index": state["posts"],
                    "posts_recorded_so_far": len(
                        [item for item in stub.requests if item[0] == "POST"]
                    ),
                    "document": only_run_document(ws),
                }
            )
        return original(request)

    stub.handler = handler
    return stub


def dying_stub(ws: Path, *, on_post: int = 1) -> Any:
    """A stub that dies (``SystemExit``) at the *on_post*-th prompt submission.

    ``SystemExit`` is a ``BaseException``: the service's defensive
    ``except Exception`` boundary deliberately does not catch it, so this is a
    real process-death simulation rather than a shaped failure.  The stub must be
    patched before the harness is built (the accepted bridge binds its transport
    handler once, at creation).
    """
    stub = two_session_stub(ws)
    original = stub.handler
    state = {"posts": 0}

    def handler(request: Any) -> Any:
        if request.method.upper() == "POST" and request.url.path.endswith("/message"):
            state["posts"] += 1
            if state["posts"] == on_post:
                raise SystemExit("simulated process death at submission")
        return original(request)

    stub.handler = handler
    return stub


# ---------------------------------------------------------------------------
# §14 - the intent is durable before submission (Mutation F regression)
# ---------------------------------------------------------------------------
def test_the_durable_in_flight_intent_precedes_the_submission(tmp_path: Path) -> None:
    observed: list[dict[str, Any]] = []
    stub = observing_stub(tmp_path / "ws", observed)
    harness = build(tmp_path, stub=stub, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)

    envelope = phase(harness.server, "devrelay_run_implementer", run_id, PROMPT)
    assert envelope["ok"] is True

    assert len(observed) == 1, "exactly one submission was observed"
    at_submission = observed[0]
    assert at_submission["posts_recorded_so_far"] == 0, (
        "the snapshot must be taken before the submission is recorded"
    )
    document = at_submission["document"]
    assert document["state"] == "READY_IMPLEMENTER"
    assert document["model_turns_used"] == 1, "the slot is consumed before the call"
    assert document["turn_attempts"] == 1
    assert document["implementer_turns"] == [], "the turn has not finished yet"
    intent = document["in_flight_turn"]
    assert intent is not None, "the durable intent must exist before submission"
    assert intent["role"] == "implementer"
    assert intent["cycle"] == 1
    assert intent["outcome"] == "in_flight"
    assert intent["prompt_sha256"] == prompt_digest(PROMPT)
    assert intent["prompt_chars"] == len(PROMPT)
    assert intent["resolved_model"] == "provider-a/model-a"
    assert intent["route_source"] == "workspace_config"

    # once the accepted result is recorded the intent is finalized in place
    final = raw_payload(harness.ws, run_id)
    assert final["in_flight_turn"] is None
    assert final["model_turns_used"] == final["turn_attempts"] == 1
    assert len(final["implementer_turns"]) == 1
    turn = final["implementer_turns"][0]
    assert turn["outcome"] == "completed"
    assert turn["prompt_sha256"] == prompt_digest(PROMPT)
    assert turn["cycle"] == 1
    store = OrchestrationStore(harness.ws / ".devrelay")
    store.load(run_id)  # the finished document is still honest


def test_both_roles_commit_their_intent_before_their_submission(tmp_path: Path) -> None:
    observed: list[dict[str, Any]] = []
    stub = observing_stub(tmp_path / "ws", observed)
    harness = build(tmp_path, stub=stub, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)

    assert phase(harness.server, "devrelay_run_implementer", run_id, PROMPT)["ok"] is True
    assert phase(harness.server, "devrelay_run_reviewer", run_id, REVIEWER_PROMPT)["ok"] is True

    assert [item["index"] for item in observed] == [1, 2]
    first, second = observed
    assert first["posts_recorded_so_far"] == 0
    assert second["posts_recorded_so_far"] == 1, "the earlier POST is already recorded"
    assert first["document"]["in_flight_turn"]["role"] == "implementer"
    assert second["document"]["in_flight_turn"]["role"] == "reviewer"
    assert second["document"]["in_flight_turn"]["resolved_model"] == "provider-b/model-b"
    assert second["document"]["in_flight_turn"]["prompt_sha256"] == prompt_digest(
        REVIEWER_PROMPT
    )
    assert second["document"]["model_turns_used"] == 2
    assert len(second["document"]["implementer_turns"]) == 1
    assert second["document"]["reviewer_turns"] == []
    assert second["document"]["state"] == "READY_REVIEWER"


# ---------------------------------------------------------------------------
# §32 - a real crash boundary, then a fresh process
# ---------------------------------------------------------------------------
def test_a_crash_at_submission_leaves_a_loadable_in_flight_intent(tmp_path: Path) -> None:
    stub = dying_stub(tmp_path / "ws")
    harness = build(tmp_path, stub=stub, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)
    # The frozen v0.3-D (v1) crash contract is certified here; v0.3-E's v2
    # refusal + recovery contract is certified in tests/test_v03e_*.py.
    freeze_v03d(harness.ws, run_id)

    with pytest.raises(SystemExit):
        phase(harness.server, "devrelay_run_implementer", run_id, PROMPT)

    crashed = raw_payload(harness.ws, run_id)
    assert crashed["state"] == "READY_IMPLEMENTER"
    assert crashed["in_flight_turn"]["role"] == "implementer"
    assert crashed["in_flight_turn"]["prompt_sha256"] == prompt_digest(PROMPT)
    assert crashed["implementer_turns"] == [] and crashed["reviewer_turns"] == []
    assert crashed["model_turns_used"] == crashed["turn_attempts"] == 1
    # the crash boundary is a legal document: a fresh process must be able to read it
    assert OrchestrationStore(harness.ws / ".devrelay").load(run_id).in_flight_turn is not None

    restarted = restart_surface(harness)
    read = get_run(restarted.server, run_id)
    assert read["ok"] is True
    assert read["data"]["in_flight"] is True
    assert read["data"]["legal_next_actions"] == []
    assert read["data"]["model_turns_used"] == 1
    assert restarted.posts == []

    envelope = phase(restarted.server, "devrelay_run_implementer", run_id, PROMPT)
    assert envelope["ok"] is False
    assert envelope["data"]["state"] == "BLOCKED"
    assert envelope["data"]["blocked_reason"] == "turn_interrupted"
    assert restarted.posts == [], "the interrupted turn is never replayed"
    assert decide(restarted.server, run_id, "complete")["ok"] is False

    materialized = raw_payload(harness.ws, run_id)
    assert materialized["state"] == "BLOCKED"
    assert materialized["in_flight_turn"] is None
    assert materialized["model_turns_used"] == 1
    assert len(materialized["implementer_turns"]) == 1
    interrupted = materialized["implementer_turns"][0]
    assert interrupted["outcome"] == "blocked"
    assert interrupted["blocked_reason"] == "turn_interrupted"
    assert interrupted["prompt_sha256"] == prompt_digest(PROMPT)
    assert materialized["last_transition"]["action"] == "run_implementer"
    assert materialized["last_transition"]["role"] == "implementer"
    OrchestrationStore(harness.ws / ".devrelay").load(run_id)


def test_a_crash_during_the_reviewer_turn_blocks_without_closing_a_cycle(
    tmp_path: Path,
) -> None:
    # the implementer submission succeeds; the reviewer submission dies
    stub = dying_stub(tmp_path / "ws", on_post=2)
    harness = build(tmp_path, stub=stub, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)
    freeze_v03d(harness.ws, run_id)
    assert phase(harness.server, "devrelay_run_implementer", run_id, PROMPT)["ok"] is True

    with pytest.raises(SystemExit):
        phase(harness.server, "devrelay_run_reviewer", run_id, REVIEWER_PROMPT)

    crashed = raw_payload(harness.ws, run_id)
    assert crashed["state"] == "READY_REVIEWER"
    assert crashed["in_flight_turn"]["role"] == "reviewer"
    assert crashed["in_flight_turn"]["cycle"] == 1
    assert crashed["in_flight_turn"]["resolved_model"] == "provider-b/model-b"
    assert len(crashed["implementer_turns"]) == 1 and crashed["reviewer_turns"] == []
    assert crashed["completed_cycles"] == 0
    assert crashed["model_turns_used"] == crashed["turn_attempts"] == 2

    restarted = restart_surface(harness)
    assert get_run(restarted.server, run_id)["data"]["legal_next_actions"] == []
    envelope = decide(restarted.server, run_id, "complete")
    assert envelope["ok"] is False
    assert envelope["data"]["state"] == "BLOCKED"
    assert envelope["data"]["blocked_reason"] == "turn_interrupted"
    assert envelope["data"]["completed_cycles"] == 0, "an interrupted review closes no cycle"
    assert envelope["data"]["decision_history"] == []
    assert restarted.posts == []

    materialized = raw_payload(harness.ws, run_id)
    assert materialized["reviewer_turns"][0]["outcome"] == "blocked"
    assert materialized["reviewer_turns"][0]["blocked_reason"] == "turn_interrupted"
    assert materialized["last_transition"]["action"] == "run_reviewer"
    assert materialized["last_transition"]["previous_state"] == "READY_REVIEWER"
    assert materialized["current_cycle"] == 1 and materialized["completed_cycles"] == 0
    OrchestrationStore(harness.ws / ".devrelay").load(run_id)


# ---------------------------------------------------------------------------
# §15 - the model-turn accounting matrix
# ---------------------------------------------------------------------------
ACCOUNTING_FAILURES = [
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
    "label,stub_kwargs", ACCOUNTING_FAILURES, ids=[case[0] for case in ACCOUNTING_FAILURES]
)
def test_a_failed_turn_consumes_exactly_one_slot_and_never_refunds_it(
    tmp_path: Path, label: str, stub_kwargs: dict[str, Any]
) -> None:
    stub = two_session_stub(tmp_path / "ws", **stub_kwargs)
    harness = build(tmp_path, stub=stub, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=1)

    envelope = phase(harness.server, "devrelay_run_implementer", run_id, PROMPT)
    assert envelope["ok"] is False, label
    summary = envelope["data"]
    assert summary["state"] == "BLOCKED", label
    assert summary["model_turns_used"] == 1, f"{label}: the slot is consumed, not refunded"
    assert summary["turn_attempts"] == 1, label
    assert summary["model_turn_budget"] == 2, label
    assert summary["model_turns_remaining"] == 1, label
    assert summary["in_flight"] is False, label

    on_disk = raw_payload(harness.ws, run_id)
    assert on_disk["in_flight_turn"] is None, f"{label}: in-flight is cleared on every path"
    assert len(on_disk["implementer_turns"]) == 1, label
    assert on_disk["reviewer_turns"] == [], f"{label}: the other role is never invoked"
    assert on_disk["implementer_turns"][0]["outcome"] == "blocked", label
    assert on_disk["implementer_turns"][0]["cycle"] == 1, label
    assert on_disk["model_turns_used"] == on_disk["turn_attempts"] == 1, label
    assert on_disk["blocked_reason"], label

    # no retry and no further slot can be spent from a blocked run
    assert phase(harness.server, "devrelay_run_implementer", run_id, PROMPT)["ok"] is False
    assert raw_payload(harness.ws, run_id)["model_turns_used"] == 1, f"{label}: no retry"
    OrchestrationStore(harness.ws / ".devrelay").load(run_id)


def test_a_successful_turn_consumes_exactly_one_slot_and_records_one_turn(tmp_path: Path) -> None:
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=2)

    first = phase(harness.server, "devrelay_run_implementer", run_id, PROMPT)
    assert first["ok"] is True
    assert first["data"]["model_turns_used"] == 1
    assert first["data"]["turn_attempts"] == 1
    assert first["data"]["state"] == "READY_REVIEWER"

    second = phase(harness.server, "devrelay_run_reviewer", run_id, REVIEWER_PROMPT)
    assert second["ok"] is True
    assert second["data"]["model_turns_used"] == 2
    assert second["data"]["model_turns_remaining"] == 2
    assert second["data"]["state"] == "AWAITING_DECISION"
    assert second["data"]["completed_cycles"] == 1

    on_disk = raw_payload(harness.ws, run_id)
    assert on_disk["in_flight_turn"] is None
    assert [turn["outcome"] for turn in on_disk["implementer_turns"]] == ["completed"]
    assert [turn["outcome"] for turn in on_disk["reviewer_turns"]] == ["completed"]
    assert on_disk["model_turns_used"] == on_disk["turn_attempts"] == 2


def test_the_budget_is_never_exceeded_over_a_full_run(tmp_path: Path) -> None:
    """max_cycles=3 -> six slots; a seventh turn is impossible."""
    harness = build(tmp_path, run_id_factory=fixed_run_ids(RUN_ID))
    run_id = run_id_of(harness.server, max_cycles=3)
    for cycle in range(1, 4):
        assert phase(
            harness.server, "devrelay_run_implementer", run_id, f"i{cycle}"
        )["ok"] is True
        assert phase(harness.server, "devrelay_run_reviewer", run_id, f"r{cycle}")["ok"] is True
        envelope = decide(harness.server, run_id, "request_changes")
        if cycle < 3:
            assert envelope["ok"] is True
        else:
            assert envelope["ok"] is True
            assert envelope["data"]["state"] == "LIMIT_REACHED"
            assert envelope["data"]["blocked_reason"] == "cycle_limit"

    on_disk = raw_payload(harness.ws, run_id)
    assert on_disk["model_turns_used"] == on_disk["turn_attempts"] == 6
    assert on_disk["model_turns_used"] == on_disk["model_turn_budget"]
    assert len(harness.posts) == 6, "exactly six submissions for six slots"
    assert on_disk["completed_cycles"] == 3
    assert phase(harness.server, "devrelay_run_implementer", run_id, "extra")["ok"] is False
    assert len(harness.posts) == 6, "the absolute ceiling holds"
