"""Shared offline harness for the v0.3-D bounded-orchestration suites.

Deterministic and offline: the real MCP SDK dispatch, the real v0.3-D
orchestration service, the real v0.3-C role router and the real accepted v0.3-A
bridge wired to the accepted OpenCode stub (``httpx.MockTransport``).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from devrelay.mcp.server import build_surface, create_server
from devrelay.opencode.accounting import FilesystemOpenCodeLedger
from devrelay.orchestration import OrchestrationStore

from opencode_stub import StubOpenCodeServer
from test_v03b_mcp_tools import envelope_of, make_workspace

#: Two distinct role sessions (v0.3-D forbids sharing one session).
IMPLEMENTER_SESSION = "ses_impl"
REVIEWER_SESSION = "ses_rev"

DISTINCT_ROLES: dict[str, Any] = {
    "implementer": {"model": "provider-a/model-a"},
    "reviewer": {"model": "provider-b/model-b"},
}
AGENT_ROLES: dict[str, Any] = {
    "implementer": {"model": "provider-a/model-a", "agent": "build"},
    "reviewer": {"model": "provider-b/model-b", "agent": "review"},
}

RUN_ID = "DR-" + "a" * 32


def fixed_run_ids(*ids: str):
    """A deterministic run-id factory for tests."""
    remaining = list(ids) or [RUN_ID]

    def factory() -> str:
        return remaining.pop(0) if len(remaining) > 1 else remaining[0]

    return factory


def honest_run(
    state: Any = None,
    *,
    max_cycles: int = 2,
    run_id: str = RUN_ID,
    workspace: str = "C:/ws",
) -> Any:
    """A run document the production state machine could honestly have produced.

    Mirrors exactly what ``OrchestrationService`` writes for the requested state
    (turn records, transitions, decision records, counters, in-flight intents),
    so :func:`validate_run_semantics` accepts it.  Used as the *valid* baseline
    that tamper tests then corrupt.
    """
    from devrelay.orchestration import (
        DecisionRecord,
        OrchestrationRun,
        RoleRouteSnapshot,
        RunState,
        TransitionRecord,
        TurnRecord,
    )

    impl_model = "provider-a/model-a"
    rev_model = "provider-b/model-b"
    snapshot = {
        "implementer": RoleRouteSnapshot(role="implementer", model=impl_model),
        "reviewer": RoleRouteSnapshot(role="reviewer", model=rev_model),
    }
    run = OrchestrationRun(
        run_id=run_id,
        workspace=workspace,
        implementer_session_id=IMPLEMENTER_SESSION,
        reviewer_session_id=REVIEWER_SESSION,
        max_cycles=max_cycles,
        model_turn_budget=2 * max_cycles,
        route_snapshot=snapshot,
    )
    run.last_transition = TransitionRecord(
        action="start",
        source="external_planner",
        previous_state="",
        next_state="READY_IMPLEMENTER",
        cycle=1,
        note="external start",
    )

    def turn(role: str, cycle: int, outcome: str) -> Any:
        return TurnRecord(
            role=role,
            cycle=cycle,
            prompt_sha256="0" * 64,
            prompt_chars=4,
            resolved_model=impl_model if role == "implementer" else rev_model,
            route_source="workspace_config",
            operation_state="COMPLETED" if outcome == "completed" else "",
            submission_attempted=True,
            submission_status=200 if outcome == "completed" else None,
            call_ids=[f"OC-{cycle:04d}"],
            assistant_message_ids=[f"msg_{role}_{cycle}"],
            outcome=outcome,
            blocked_reason="" if outcome == "completed" else "read_timeout",
        )

    def close_cycle(target: Any, cycle: int) -> None:
        target.implementer_turns.append(turn("implementer", cycle, "completed"))
        target.reviewer_turns.append(turn("reviewer", cycle, "completed"))
        target.model_turns_used += 2
        target.turn_attempts += 2
        target.completed_cycles = cycle
        target.last_transition = TransitionRecord(
            action="run_reviewer",
            source="model_bearing",
            previous_state="READY_REVIEWER",
            next_state="AWAITING_DECISION",
            cycle=cycle,
            role="reviewer",
            note="confirmed completion",
        )

    def decide(target: Any, decision: str, next_state: str, *, reason: str = "") -> None:
        previous = target.state.value
        target.decision_history.append(
            DecisionRecord(
                decision=decision,
                previous_state=previous,
                next_state=next_state,
            )
        )
        target.state = RunState(next_state)
        target.blocked_reason = reason
        target.last_transition = TransitionRecord(
            action="decide",
            source="external_planner",
            previous_state=previous,
            next_state=next_state,
            cycle=target.current_cycle,
            note=f"external decision={decision}",
        )

    target_state = RunState.READY_IMPLEMENTER if state is None else RunState(state)
    if target_state is RunState.READY_IMPLEMENTER:
        return run
    if target_state is RunState.READY_REVIEWER:
        run.implementer_turns.append(turn("implementer", 1, "completed"))
        run.model_turns_used = 1
        run.turn_attempts = 1
        run.state = RunState.READY_REVIEWER
        run.last_transition = TransitionRecord(
            action="run_implementer",
            source="model_bearing",
            previous_state="READY_IMPLEMENTER",
            next_state="READY_REVIEWER",
            cycle=1,
            role="implementer",
            note="confirmed completion",
        )
        return run
    if target_state is RunState.AWAITING_DECISION:
        close_cycle(run, 1)
        run.state = RunState.AWAITING_DECISION
        return run
    if target_state in (RunState.COMPLETED, RunState.STOPPED):
        close_cycle(run, 1)
        run.state = RunState.AWAITING_DECISION
        decide(
            run,
            "complete" if target_state is RunState.COMPLETED else "stop",
            target_state.value,
        )
        return run
    if target_state is RunState.LIMIT_REACHED:
        for cycle in range(1, max_cycles + 1):
            close_cycle(run, cycle)
            run.state = RunState.AWAITING_DECISION
            if cycle == max_cycles:
                decide(
                    run,
                    "request_changes",
                    RunState.LIMIT_REACHED.value,
                    reason="cycle_limit",
                )
            else:
                decide(run, "request_changes", RunState.READY_IMPLEMENTER.value)
                run.state = RunState.READY_IMPLEMENTER
                run.current_cycle = cycle + 1
        return run
    if target_state is RunState.BLOCKED:
        # A failed implementer turn in cycle 1 (the fail-closed shape).
        run.implementer_turns.append(turn("implementer", 1, "blocked"))
        run.model_turns_used = 1
        run.turn_attempts = 1
        run.state = RunState.BLOCKED
        run.blocked_reason = "read_timeout"
        run.last_transition = TransitionRecord(
            action="run_implementer",
            source="model_bearing",
            previous_state="READY_IMPLEMENTER",
            next_state="BLOCKED",
            cycle=1,
            role="implementer",
            note="blocked: read_timeout",
        )
        return run
    raise AssertionError(f"honest_run cannot build state {target_state.value}")


def honest_ready_implementer_cycle2(
    *, max_cycles: int = 2, run_id: str = RUN_ID, workspace: str = "C:/ws"
) -> Any:
    """``READY_IMPLEMENTER`` for cycle 2 after one explicit ``request_changes``."""
    from devrelay.orchestration import (
        DecisionRecord,
        RunState,
        TransitionRecord,
    )

    run = honest_run(
        RunState.AWAITING_DECISION,
        max_cycles=max_cycles,
        run_id=run_id,
        workspace=workspace,
    )
    run.decision_history.append(
        DecisionRecord(
            decision="request_changes",
            previous_state="AWAITING_DECISION",
            next_state="READY_IMPLEMENTER",
        )
    )
    run.state = RunState.READY_IMPLEMENTER
    run.current_cycle = 2
    run.last_transition = TransitionRecord(
        action="decide",
        source="external_planner",
        previous_state="AWAITING_DECISION",
        next_state="READY_IMPLEMENTER",
        cycle=1,
        note="external decision=request_changes",
    )
    return run


def with_in_flight(run: Any, role: str) -> Any:
    """Add an honest in-flight intent for *role* to a ``READY_*`` run."""
    from devrelay.orchestration import TurnOutcomeState, TurnRecord

    run.in_flight_turn = TurnRecord(
        role=role,
        cycle=run.current_cycle,
        prompt_sha256="1" * 64,
        prompt_chars=11,
        resolved_model=run.route_snapshot[role].model,
        resolved_agent=run.route_snapshot[role].agent,
        route_source=run.route_snapshot[role].route_source,
        outcome=TurnOutcomeState.IN_FLIGHT.value,
    )
    run.turn_attempts += 1
    run.model_turns_used += 1
    return run


def make_run(**overrides: Any):
    """Back-compat alias: an honest ``READY_IMPLEMENTER`` run."""
    state = overrides.pop("state", None)
    run = honest_run(state, **overrides)
    return run


def save_run(store: Any, run: Any) -> Any:
    store.save(run)
    return run


def write_roles(ws: Path, roles: dict[str, Any] | None) -> None:
    path = ws / ".devrelay" / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if roles is None:
        data.pop("roles", None)
    else:
        data["roles"] = roles
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def two_session_stub(ws: Path, **kwargs: Any) -> StubOpenCodeServer:
    stub = StubOpenCodeServer(workspace=str(ws), **kwargs)
    base = dict(stub.sessions[0])
    stub.sessions = [
        dict(base, id=IMPLEMENTER_SESSION, directory=str(ws)),
        dict(base, id=REVIEWER_SESSION, directory=str(ws)),
    ]
    stub.workspace = str(ws)
    for session in stub.sessions:
        session["directory"] = str(ws)
    return stub


@dataclass(frozen=True)
class Harness:
    surface: Any
    server: Any
    stub: StubOpenCodeServer
    ws: Path
    ledger: Any

    @property
    def service(self) -> Any:
        return self.surface.orchestration

    @property
    def posts(self) -> list[str]:
        return [path for method, path in self.stub.requests if method == "POST"]

    @property
    def requests(self) -> list[tuple[str, str]]:
        return list(self.stub.requests)


def build(
    tmp_path: Path,
    *,
    roles: dict[str, Any] | None = DISTINCT_ROLES,
    stub: StubOpenCodeServer | None = None,
    run_id_factory: Any = None,
    bridge_factory: Any = None,
) -> Harness:
    ws = make_workspace(tmp_path)
    write_roles(ws, roles)
    stub = stub or two_session_stub(ws)
    ledger = FilesystemOpenCodeLedger(ws / ".devrelay")
    if bridge_factory is None:

        def bridge_factory() -> Any:  # noqa: F811 - injected factory
            return stub.bridge(workspace_root=str(ws), ledger=ledger)

    surface = build_surface(ws, bridge_factory=bridge_factory)
    if run_id_factory is not None:
        surface.orchestration.store = OrchestrationStore(
            ws / ".devrelay", run_id_factory=run_id_factory
        )
    return Harness(
        surface=surface,
        server=create_server(surface),
        stub=stub,
        ws=ws,
        ledger=ledger,
    )


def restart_surface(harness: "Harness", *, stub: StubOpenCodeServer | None = None) -> "Harness":
    """A brand-new surface and server over the *same* workspace (a restart).

    Nothing is shared with *harness* except the workspace directory, so this
    models a fresh MCP server process reading the durable run documents.
    """
    ws = harness.ws
    stub = stub or two_session_stub(ws)
    ledger = FilesystemOpenCodeLedger(ws / ".devrelay")
    surface = build_surface(
        ws, bridge_factory=lambda: stub.bridge(workspace_root=str(ws), ledger=ledger)
    )
    return Harness(
        surface=surface,
        server=create_server(surface),
        stub=stub,
        ws=ws,
        ledger=ledger,
    )


def call(server: Any, tool: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    return envelope_of(asyncio.run(server.call_tool(tool, arguments or {})))


def call_result(server: Any, tool: str, arguments: dict[str, Any] | None = None) -> Any:
    return asyncio.run(server.call_tool(tool, arguments or {}))


def start(
    server: Any,
    *,
    max_cycles: int = 1,
    implementer_session: str = IMPLEMENTER_SESSION,
    reviewer_session: str = REVIEWER_SESSION,
) -> dict[str, Any]:
    return call(
        server,
        "devrelay_start_run",
        {
            "implementer_session_id": implementer_session,
            "reviewer_session_id": reviewer_session,
            "max_cycles": max_cycles,
        },
    )


def run_id_of(server: Any, **kwargs: Any) -> str:
    envelope = start(server, **kwargs)
    assert envelope["ok"] is True, envelope
    return envelope["data"]["run_id"]


def phase(server: Any, tool: str, run_id: str, prompt: str = "phase prompt") -> dict[str, Any]:
    return call(server, tool, {"run_id": run_id, "prompt": prompt})


def decide(server: Any, run_id: str, decision: str) -> dict[str, Any]:
    return call(server, "devrelay_decide_run", {"run_id": run_id, "decision": decision})


def get_run(server: Any, run_id: str) -> dict[str, Any]:
    return call(server, "devrelay_get_run", {"run_id": run_id})


def state_path(ws: Path, run_id: str) -> Path:
    return ws / ".devrelay" / "orchestration" / "runs" / f"{run_id}.json"


def raw_payload(ws: Path, run_id: str) -> dict[str, Any]:
    import json

    return json.loads(state_path(ws, run_id).read_text(encoding="utf-8"))
