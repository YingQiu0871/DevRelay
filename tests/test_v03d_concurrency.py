"""v0.3-D orchestration under the accepted v0.3-B execution boundary.

Harness note: every wait for a bridge entry is bounded (``await_entry``).  A
setup mistake therefore fails fast instead of hanging, and nothing here sleeps
longer than a few hundred milliseconds.
"""

from __future__ import annotations

import asyncio
import threading

import pytest

from devrelay.mcp.server import build_surface, create_server
from devrelay.opencode.models import OpenCodeOperationResult, OpenCodeOperationState, OpenCodeSession
from devrelay.orchestration import OrchestrationStore

from v03d_helpers import (
    IMPLEMENTER_SESSION,
    REVIEWER_SESSION,
    make_workspace,
    write_roles,
)

FIXED_ID = "DR-" + "c" * 32

#: How long the held body may take to reach the bridge before the test fails.
ENTRY_TIMEOUT = 5.0

#: The bridge operation the gated (held) body reaches first.  A phase tool
#: performs its accepted ownership probe (``get_session``) *before* the single
#: ``send_prompt`` submission, so that probe is what the gate parks on.
HOLDER_FIRST_ENTRY = {
    "opencode_read_messages": "read_messages",
    "devrelay_run_implementer": "get_session",
    "devrelay_run_reviewer": "get_session",
}


class OrchestrationGateBridge:
    """Fake bridge that measures overlap and can gate its first caller."""

    def __init__(self) -> None:
        self._guard = threading.Lock()
        self.gate_enabled = False
        self.active = 0
        self.max_concurrent_execution = 0
        self.entered: list[str] = []
        self.submissions: list[dict] = []
        self.interrupts = 0
        self.first_entered = threading.Event()
        self.release = threading.Event()

    def _enter(self, operation: str) -> None:
        with self._guard:
            self.active += 1
            self.max_concurrent_execution = max(self.max_concurrent_execution, self.active)
            self.entered.append(operation)
            first = len(self.entered) == 1
        self.first_entered.set()
        if first and self.gate_enabled:
            self.release.wait(timeout=5)
        with self._guard:
            self.active -= 1

    @staticmethod
    def _result(operation: str, state: OpenCodeOperationState = OpenCodeOperationState.COMPLETED):
        return OpenCodeOperationResult(
            operation=operation,
            state=state,
            session_id=IMPLEMENTER_SESSION,
            call_ids=[f"GATE-{operation}"],
            request_count=1,
            submission_attempted=operation == "send_prompt",
            submission_status=200 if operation == "send_prompt" else None,
        )

    def get_session(self, session_id: str):
        self._enter("get_session")
        result = self._result("get_session")
        return result.model_copy(
            update={
                "session": OpenCodeSession(
                    session_id=session_id, workspace="C:/ws", workspace_match=True
                )
            }
        )

    def read_messages(self, *args, **kwargs):
        self._enter("read_messages")
        return self._result("read_messages")

    def health(self):
        self._enter("health")
        return self._result("health")

    def send_prompt(self, session_id, prompt, *, agent="", model=""):
        self._enter("send_prompt")
        self.submissions.append({"session_id": session_id, "agent": agent, "model": model})
        return self._result("send_prompt")

    def interrupt(self, session_id):
        self.interrupts += 1
        self._enter("interrupt")
        return self._result("interrupt", OpenCodeOperationState.INTERRUPTED)


def build_gated(tmp_path):
    ws = make_workspace(tmp_path)
    write_roles(
        ws,
        {
            "implementer": {"model": "provider-a/model-a"},
            "reviewer": {"model": "provider-b/model-b"},
        },
    )
    bridge = OrchestrationGateBridge()
    surface = build_surface(ws, bridge_factory=lambda: bridge)
    surface.orchestration.store = OrchestrationStore(
        ws / ".devrelay", run_id_factory=lambda: FIXED_ID
    )
    return bridge, create_server(surface), ws


def ungate(bridge: OrchestrationGateBridge) -> None:
    bridge.gate_enabled = False
    bridge.entered.clear()
    bridge.first_entered.clear()
    bridge.release.clear()


def gate(bridge: OrchestrationGateBridge) -> None:
    bridge.gate_enabled = True
    bridge.entered.clear()
    bridge.first_entered.clear()
    bridge.release.clear()


def start_call(server, *, max_cycles: int = 2):
    return server.call_tool(
        "devrelay_start_run",
        {
            "implementer_session_id": IMPLEMENTER_SESSION,
            "reviewer_session_id": REVIEWER_SESSION,
            "max_cycles": max_cycles,
        },
    )


def call_sync(server, tool: str, arguments: dict):
    return asyncio.run(server.call_tool(tool, arguments)).structured_content


async def await_entry(bridge: OrchestrationGateBridge, *, timeout: float = ENTRY_TIMEOUT) -> None:
    """Bounded wait: the held body must reach the bridge, or the test fails."""
    deadline = asyncio.get_running_loop().time() + timeout
    while not bridge.first_entered.is_set():
        if asyncio.get_running_loop().time() > deadline:
            raise AssertionError(
                "the held tool body never reached the bridge within "
                f"{timeout}s (entered={bridge.entered}); the orchestration setup "
                "must leave the run in the phase's legal state"
            )
        await asyncio.sleep(0.01)


# ---------------------------------------------------------------------------
# cross-tool serialization
# ---------------------------------------------------------------------------
def prepare_none(bridge, server) -> str:
    """Create the run (READY_IMPLEMENTER) so get_run has something to read."""
    result = call_sync(server, "devrelay_start_run", {
        "implementer_session_id": IMPLEMENTER_SESSION,
        "reviewer_session_id": REVIEWER_SESSION,
        "max_cycles": 2,
    })
    assert result["ok"] is True
    return FIXED_ID


def prepare_ready_implementer(bridge, server) -> str:
    result = call_sync(server, "devrelay_start_run", {
        "implementer_session_id": IMPLEMENTER_SESSION,
        "reviewer_session_id": REVIEWER_SESSION,
        "max_cycles": 2,
    })
    assert result["ok"] is True
    return FIXED_ID


def prepare_ready_reviewer(bridge, server) -> str:
    result = call_sync(server, "devrelay_start_run", {
        "implementer_session_id": IMPLEMENTER_SESSION,
        "reviewer_session_id": REVIEWER_SESSION,
        "max_cycles": 2,
    })
    assert result["ok"] is True
    implemented = call_sync(
        server, "devrelay_run_implementer", {"run_id": FIXED_ID, "prompt": "implement"}
    )
    assert implemented["ok"] is True and implemented["data"]["state"] == "READY_REVIEWER"
    return FIXED_ID


CASES = [
    (
        "get_run+read",
        prepare_none,
        ("opencode_read_messages", {"session_id": IMPLEMENTER_SESSION}),
        ("devrelay_get_run", {"run_id": FIXED_ID}),
    ),
    (
        "start_run+read",
        None,
        ("opencode_read_messages", {"session_id": IMPLEMENTER_SESSION}),
        (
            "devrelay_start_run",
            {
                "implementer_session_id": IMPLEMENTER_SESSION,
                "reviewer_session_id": REVIEWER_SESSION,
                "max_cycles": 1,
            },
        ),
    ),
    (
        "run_implementer+raw_send",
        prepare_ready_implementer,
        ("devrelay_run_implementer", {"run_id": FIXED_ID, "prompt": "implement"}),
        ("opencode_send_prompt", {"session_id": IMPLEMENTER_SESSION, "prompt": "raw"}),
    ),
    (
        "run_reviewer+role_send",
        prepare_ready_reviewer,
        ("devrelay_run_reviewer", {"run_id": FIXED_ID, "prompt": "review"}),
        (
            "devrelay_send_role_prompt",
            {"role": "reviewer", "session_id": REVIEWER_SESSION, "prompt": "role"},
        ),
    ),
]


@pytest.mark.parametrize(
    "label,prepare,held,waiting", CASES, ids=[case[0] for case in CASES]
)
def test_orchestration_tools_share_the_one_execution_boundary(
    tmp_path, label, prepare, held, waiting
):
    bridge, server, _ws = build_gated(tmp_path)
    if prepare is not None:
        ungate(bridge)
        prepare(bridge, server)
    gate(bridge)
    submissions_before = len(bridge.submissions)

    async def run() -> dict:
        held_task = asyncio.create_task(server.call_tool(*held))
        await await_entry(bridge)
        waiting_task = asyncio.create_task(server.call_tool(*waiting))
        await asyncio.sleep(0.3)
        blocked = not waiting_task.done()
        entered_while_gated = list(bridge.entered)
        submissions_while_gated = len(bridge.submissions) - submissions_before
        bridge.release.set()
        held_result = await asyncio.wait_for(held_task, timeout=10)
        waiting_result = await asyncio.wait_for(waiting_task, timeout=10)
        return {
            "blocked": blocked,
            "entered_while_gated": entered_while_gated,
            "submissions_while_gated": submissions_while_gated,
            "held": held_result.structured_content,
            "waiting": waiting_result.structured_content,
        }

    observed = asyncio.run(run())
    assert observed["blocked"] is True, (
        f"{label}: the waiting tool must not run beside the body holding the boundary"
    )
    assert observed["entered_while_gated"] == [HOLDER_FIRST_ENTRY[held[0]]], (
        f"{label}: while the boundary was held only the held body may be inside "
        f"the bridge (saw {observed['entered_while_gated']})"
    )
    if held[0].startswith("devrelay_run_"):
        assert observed["submissions_while_gated"] == 0, (
            f"{label}: no submission may happen while the run is parked on its "
            "ownership probe"
        )
    assert bridge.max_concurrent_execution == 1, (
        f"{label}: measured {bridge.max_concurrent_execution} concurrent bridge entries"
    )
    assert observed["held"]["ok"] is True, observed["held"]
    assert observed["waiting"]["ok"] is True, observed["waiting"]
    assert bridge.active == 0


def test_decide_run_waits_for_the_boundary_too(tmp_path):
    bridge, server, _ws = build_gated(tmp_path)
    ungate(bridge)
    assert call_sync(server, "devrelay_start_run", {
        "implementer_session_id": IMPLEMENTER_SESSION,
        "reviewer_session_id": REVIEWER_SESSION,
        "max_cycles": 2,
    })["ok"] is True
    assert call_sync(server, "devrelay_run_implementer", {"run_id": FIXED_ID, "prompt": "i"})["ok"]
    reviewed = call_sync(server, "devrelay_run_reviewer", {"run_id": FIXED_ID, "prompt": "r"})
    assert reviewed["data"]["state"] == "AWAITING_DECISION"
    gate(bridge)

    async def run() -> dict:
        held = asyncio.create_task(
            server.call_tool("opencode_read_messages", {"session_id": IMPLEMENTER_SESSION})
        )
        await await_entry(bridge)
        deciding = asyncio.create_task(
            server.call_tool("devrelay_decide_run", {"run_id": FIXED_ID, "decision": "complete"})
        )
        await asyncio.sleep(0.3)
        blocked = not deciding.done()
        entered_while_gated = list(bridge.entered)
        bridge.release.set()
        return {
            "blocked": blocked,
            "entered_while_gated": entered_while_gated,
            "decision": (await asyncio.wait_for(deciding, timeout=10)).structured_content,
            "held": (await asyncio.wait_for(held, timeout=10)).structured_content,
        }

    observed = asyncio.run(run())
    assert observed["blocked"] is True
    assert observed["entered_while_gated"] == ["read_messages"]
    assert observed["decision"]["ok"] is True
    assert observed["decision"]["data"]["state"] == "COMPLETED"
    assert bridge.max_concurrent_execution == 1


# ---------------------------------------------------------------------------
# duplicate same-phase invocation under concurrency
# ---------------------------------------------------------------------------
def test_two_concurrent_implementer_attempts_submit_exactly_once(tmp_path):
    bridge, server, _ws = build_gated(tmp_path)
    ungate(bridge)
    assert call_sync(server, "devrelay_start_run", {
        "implementer_session_id": IMPLEMENTER_SESSION,
        "reviewer_session_id": REVIEWER_SESSION,
        "max_cycles": 1,
    })["ok"] is True
    gate(bridge)

    async def run() -> list:
        async def attempt():
            return await server.call_tool(
                "devrelay_run_implementer", {"run_id": FIXED_ID, "prompt": "implement"}
            )

        first = asyncio.create_task(attempt())
        await await_entry(bridge)
        second = asyncio.create_task(attempt())
        await asyncio.sleep(0.3)
        bridge.release.set()
        return [
            await asyncio.wait_for(first, timeout=10),
            await asyncio.wait_for(second, timeout=10),
        ]

    results = asyncio.run(run())
    envelopes = [result.structured_content for result in results]
    assert len(bridge.submissions) == 1, "only one attempt may reach the provider"
    assert sum(1 for envelope in envelopes if envelope["ok"]) == 1
    failures = [envelope for envelope in envelopes if not envelope["ok"]]
    assert len(failures) == 1
    assert failures[0]["error"]["type"] == "orchestration_invalid_transition"
    assert failures[0]["data"]["state"] == "READY_REVIEWER"
    assert all(
        submission["session_id"] == IMPLEMENTER_SESSION for submission in bridge.submissions
    )


def test_two_concurrent_reviewer_attempts_submit_exactly_once(tmp_path):
    bridge, server, _ws = build_gated(tmp_path)
    ungate(bridge)
    assert call_sync(server, "devrelay_start_run", {
        "implementer_session_id": IMPLEMENTER_SESSION,
        "reviewer_session_id": REVIEWER_SESSION,
        "max_cycles": 1,
    })["ok"] is True
    assert call_sync(server, "devrelay_run_implementer", {"run_id": FIXED_ID, "prompt": "i"})["ok"]
    submissions_before = len(bridge.submissions)
    gate(bridge)

    async def run() -> list:
        async def attempt():
            return await server.call_tool(
                "devrelay_run_reviewer", {"run_id": FIXED_ID, "prompt": "review"}
            )

        first = asyncio.create_task(attempt())
        await await_entry(bridge)
        second = asyncio.create_task(attempt())
        await asyncio.sleep(0.3)
        bridge.release.set()
        return [
            await asyncio.wait_for(first, timeout=10),
            await asyncio.wait_for(second, timeout=10),
        ]

    results = asyncio.run(run())
    envelopes = [result.structured_content for result in results]
    assert len(bridge.submissions) - submissions_before == 1
    assert sum(1 for envelope in envelopes if envelope["ok"]) == 1
    states = {envelope["data"].get("state") for envelope in envelopes}
    assert states == {"AWAITING_DECISION"}
    assert all(
        submission["session_id"] == REVIEWER_SESSION
        for submission in bridge.submissions[submissions_before:]
    )
