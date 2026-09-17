"""v0.3-C: role tools and the accepted v0.3-B serialization boundary.

The three new tools must go through the **same** per-surface execution lock as
the accepted nine - no second lock, no role-specific serialization, no scheduler.
Offline: real dispatch over the real v0.3-A bridge and the deterministic stub.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from devrelay.mcp.tools import TOOL_NAMES
from devrelay.opencode.accounting import FilesystemOpenCodeLedger

from test_v03b_mcp_concurrency import (
    CancellableSubmitBridge,
    GateBridge,
    LedgerOverlapProbe,
)
from test_v03b_mcp_tools import envelope_of, make_workspace
from v03c_helpers import (
    DISTINCT_ROLES,
    IMPLEMENTER_WIRE,
    REVIEWER_WIRE,
    build_roles_server,
    posts,
    send_role,
    wire_bodies,
)

ROLE_TOOL = "devrelay_send_role_prompt"

#: Which accepted bridge operation each tool body reaches (the gate label).
BRIDGE_OPERATION = {
    "opencode_read_messages": "read_messages",
    "opencode_send_prompt": "send_prompt",
    "opencode_health": "health",
    "opencode_interrupt": "interrupt",
    ROLE_TOOL: "send_prompt",
}

MATRIX_PAIRS: tuple[tuple[str, tuple[str, dict[str, Any]], tuple[str, dict[str, Any]]], ...] = (
    (
        "role_send+read",
        (ROLE_TOOL, {"role": "reviewer", "session_id": "ses_match", "prompt": "hi"}),
        ("opencode_read_messages", {"session_id": "ses_match"}),
    ),
    (
        "role_send+raw_send",
        (ROLE_TOOL, {"role": "reviewer", "session_id": "ses_match", "prompt": "hi"}),
        ("opencode_send_prompt", {"session_id": "ses_match", "prompt": "raw"}),
    ),
    (
        "implementer+reviewer",
        (ROLE_TOOL, {"role": "implementer", "session_id": "ses_match", "prompt": "impl"}),
        (ROLE_TOOL, {"role": "reviewer", "session_id": "ses_match", "prompt": "rev"}),
    ),
)


@pytest.mark.parametrize(
    "label,first,second", MATRIX_PAIRS, ids=[pair[0] for pair in MATRIX_PAIRS]
)
def test_role_tools_never_overlap_the_accepted_tools(tmp_path, label, first, second):
    bridge = GateBridge()
    harness = build_roles_server(tmp_path, DISTINCT_ROLES, bridge_factory=lambda: bridge)
    server = harness.server

    async def run() -> list[Any]:
        running = asyncio.create_task(server.call_tool(*first))
        while not bridge.first_entered.is_set():
            await asyncio.sleep(0.01)
        second_task = asyncio.create_task(server.call_tool(*second))
        try:
            for _ in range(30):
                await asyncio.sleep(0.01)
                assert bridge.max_concurrent_execution == 1, (
                    f"{label}: {bridge.max_concurrent_execution} tool bodies "
                    "touched the boundary at once"
                )
            assert bridge.entered == [BRIDGE_OPERATION[first[0]]], bridge.entered
        finally:
            bridge.release.set()
        return [await running, await second_task]

    first_result, second_result = asyncio.run(run())
    assert bridge.max_concurrent_execution == 1, (
        f"{label}: max_concurrent_execution must be 1, "
        f"measured {bridge.max_concurrent_execution}"
    )
    assert len(bridge.entered) == 2, bridge.entered
    assert envelope_of(first_result)["ok"] is True, envelope_of(first_result)
    assert envelope_of(second_result)["ok"] is True, envelope_of(second_result)
    assert bridge.active == 0


@pytest.mark.parametrize("role_tool", ["devrelay_list_roles", "devrelay_get_role"])
def test_role_read_tools_wait_for_the_same_execution_boundary(tmp_path, role_tool):
    """The read-only role views are local, but they still take the one lock."""
    bridge = GateBridge()
    harness = build_roles_server(tmp_path, DISTINCT_ROLES, bridge_factory=lambda: bridge)
    server = harness.server
    arguments = {"role": "reviewer"} if role_tool == "devrelay_get_role" else {}

    async def run() -> dict[str, Any]:
        sending = asyncio.create_task(
            server.call_tool(
                ROLE_TOOL, {"role": "reviewer", "session_id": "ses_match", "prompt": "hi"}
            )
        )
        while not bridge.first_entered.is_set():
            await asyncio.sleep(0.01)
        reader = asyncio.create_task(server.call_tool(role_tool, arguments))
        await asyncio.sleep(0.3)
        blocked = not reader.done()
        bridge.release.set()
        return {
            "blocked": blocked,
            "reader": envelope_of(await asyncio.wait_for(reader, timeout=10)),
            "sender": envelope_of(await sending),
        }

    observed = asyncio.run(run())
    assert observed["blocked"] is True, (
        f"{role_tool} must wait for the one execution boundary, not run beside it"
    )
    assert observed["reader"]["ok"] is True
    assert observed["sender"]["ok"] is True
    assert bridge.max_concurrent_execution == 1


def test_parallel_reads_and_both_role_sends_keep_the_ledger_intact(tmp_path):
    """Mixed load: the accepted ledger must stay single-writer with role sends."""
    ws = make_workspace(tmp_path)
    probe = LedgerOverlapProbe(FilesystemOpenCodeLedger(ws / ".devrelay"))
    harness = build_roles_server(tmp_path, DISTINCT_ROLES, ledger=probe)
    server, stub = harness.server, harness.stub

    calls = [
        ("opencode_read_messages", {"session_id": "ses_match"}),
        ("opencode_read_messages", {"session_id": "ses_match"}),
        (ROLE_TOOL, {"role": "implementer", "session_id": "ses_match", "prompt": "impl"}),
        ("opencode_read_messages", {"session_id": "ses_match"}),
        (ROLE_TOOL, {"role": "reviewer", "session_id": "ses_match", "prompt": "rev"}),
        ("opencode_read_messages", {"session_id": "ses_match"}),
    ]

    async def run() -> list[Any]:
        return await asyncio.gather(
            *[server.call_tool(name, arguments) for name, arguments in calls]
        )

    envelopes = [envelope_of(result) for result in asyncio.run(run())]
    failures = [envelope for envelope in envelopes if not envelope["ok"]]
    assert failures == [], failures
    assert probe.max_overlap == 1, f"measured ledger overlap: {probe.max_overlap}"

    assert posts(stub) == ["/session/ses_match/message"] * 2, (
        "exactly one submission POST per role send"
    )
    models = {tuple(sorted(body["model"].items())) for body in wire_bodies(stub)}
    assert models == {
        tuple(sorted(IMPLEMENTER_WIRE.items())),
        tuple(sorted(REVIEWER_WIRE.items())),
    }, "each role reached its own configured model"

    from devrelay.mcp.ledger import read_records_strict

    records = read_records_strict(ws / ".devrelay", limit=200)
    ids = [record["call_id"] for record in records]
    assert len(ids) == len(set(ids)), ids
    assert all(record["state"] != "ISSUED" for record in records), records
    numbers = sorted(int(call_id.split("-")[1]) for call_id in ids)
    assert numbers == list(range(1, len(numbers) + 1)), numbers
    assert len(records) >= 6, "reads and both role sends must be recorded"


def test_role_tools_share_the_one_execution_lock(tmp_path):
    """v0.3-C adds no second lock, no role lock and no scheduler."""
    from pathlib import Path as _Path

    from devrelay.mcp import tools as tools_module

    harness = build_roles_server(tmp_path, DISTINCT_ROLES)
    surface = harness.surface
    assert len(TOOL_NAMES) == 17
    acquired = surface._execution_lock.acquire(timeout=2)
    assert acquired
    surface._execution_lock.release()
    for forbidden in ("_role_lock", "_router_lock", "_bridge_lock", "_side_effect_lock"):
        assert not hasattr(surface, forbidden), forbidden

    source = _Path(tools_module.__file__).read_text(encoding="utf-8")
    assert source.count("threading.RLock()") == 1, "exactly one execution lock"
    assert "threading.Lock()" not in source, "no second, non-reentrant lock"
    assert source.count("with self._execution_lock:") == 2, (
        "the lock is taken in exactly two places: _execute and bridge construction"
    )


class RoleCancellableBridge(CancellableSubmitBridge):
    """Cancellable bridge that also records which route reached the wire."""

    def __init__(self, ledger: FilesystemOpenCodeLedger) -> None:
        super().__init__(ledger)
        self.routed: list[dict[str, Any]] = []

    def send_prompt(
        self, session_id: str, prompt: str, *, agent: str = "", model: str = ""
    ) -> Any:
        self.routed.append({"agent": agent, "model": model})
        return super().send_prompt(session_id, prompt, agent=agent, model=model)


def test_cancelled_role_send_keeps_evidence_and_never_switches_role(tmp_path):
    ws = make_workspace(tmp_path)
    ledger = FilesystemOpenCodeLedger(ws / ".devrelay")
    bridge = RoleCancellableBridge(ledger)
    harness = build_roles_server(tmp_path, DISTINCT_ROLES, bridge_factory=lambda: bridge)
    server = harness.server

    async def run() -> dict[str, Any]:
        task = asyncio.create_task(
            server.call_tool(
                ROLE_TOOL, {"role": "reviewer", "session_id": "ses_match", "prompt": "review this"}
            )
        )
        while not bridge.entered.is_set():
            await asyncio.sleep(0.01)
        task.cancel()
        outcome = "completed"
        try:
            await task
        except asyncio.CancelledError:
            outcome = "cancelled"

        follow_up = asyncio.create_task(server.call_tool("opencode_health", {}))
        await asyncio.sleep(0.3)
        blocked_while_body_runs = not follow_up.done()
        bridge.release.set()
        health = await asyncio.wait_for(follow_up, timeout=10)
        return {
            "outcome": outcome,
            "blocked": blocked_while_body_runs,
            "health": envelope_of(health),
        }

    observed = asyncio.run(run())
    assert observed["outcome"] == "cancelled"
    assert observed["blocked"] is True, "the boundary stays held until the body exits"
    assert observed["health"]["ok"] is True
    assert bridge.submissions == 1, "a cancelled role send is never retried"
    assert bridge.interrupt_calls == 0, "no automatic interrupt and no role switch"
    assert bridge.routed == [{"agent": "", "model": "provider-b/model-b"}], bridge.routed

    from devrelay.mcp.ledger import read_records_strict

    records = read_records_strict(ws / ".devrelay", limit=50)
    assert len(records) == 1
    assert records[0]["state"] == "TIMED_OUT"
    assert records[0]["submission_uncertain"] is True
    assert records[0]["operation"] == "send_prompt"


def test_role_send_envelope_never_claims_retry_safety_after_cancellation(tmp_path):
    """No envelope exists for a cancelled call, so the durable record is the evidence."""
    ws = make_workspace(tmp_path)
    ledger = FilesystemOpenCodeLedger(ws / ".devrelay")
    bridge = RoleCancellableBridge(ledger)
    harness = build_roles_server(tmp_path, DISTINCT_ROLES, bridge_factory=lambda: bridge)

    async def run() -> str:
        task = asyncio.create_task(
            harness.server.call_tool(
                ROLE_TOOL, {"role": "implementer", "session_id": "ses_match", "prompt": "x"}
            )
        )
        while not bridge.entered.is_set():
            await asyncio.sleep(0.01)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            return "cancelled"
        return "completed"

    assert asyncio.run(run()) == "cancelled"
    bridge.release.set()
    assert bridge.routed[0]["model"] == "provider-a/model-a"
    assert bridge.submissions == 1 and bridge.interrupt_calls == 0
    envelope = send_role(harness.server, "reviewer")
    assert envelope["data"]["retry_safe"] is False
