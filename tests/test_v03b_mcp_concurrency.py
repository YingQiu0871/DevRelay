"""v0.3-B concurrency remediation suite: the serialization boundary.

The gate review found that parallel MCP tool executions race the **accepted
v0.3-A filesystem ledger** (``FilesystemOpenCodeLedger`` allocates durable
``OC-*`` identities with a non-atomic read-modify-write over one fixed-name temp
file and refuses identity reuse, so it is a single-writer store).  Two failures
are reproducible with 8 parallel ``opencode_read_messages`` calls on the
pre-remediation candidate (``59f81c0``): ``internal_error`` from
``PermissionError`` on the shared ``.sequence.json.tmp`` rename, and
``opencode_ledger_error`` from a colliding ``OC-0001`` identity.

v0.3-B therefore serializes **all** tool execution in one MCP server process
with a single re-entrant execution lock.  These tests drive the real MCP SDK
dispatch, the real accepted v0.3-A bridge and the real filesystem ledger (stub
OpenCode over ``httpx.MockTransport``); fakes are used only where the point is
the *lock*.  No test contacts a network, a model or a real OpenCode process.
"""

from __future__ import annotations

import ast
import asyncio
import inspect
import threading
from pathlib import Path
from typing import Any

import pytest

from devrelay.mcp import tools as tools_module
from devrelay.mcp.ledger import read_records_strict, sequence_state
from devrelay.mcp.server import build_surface, create_server
from devrelay.mcp.tools import TOOL_NAMES
from devrelay.opencode.accounting import FilesystemOpenCodeLedger
from devrelay.opencode.models import (
    OpenCodeCallRecord,
    OpenCodeCallState,
    OpenCodeMessage,
    OpenCodeMessagePart,
    OpenCodeOperationResult,
    OpenCodeOperationState,
    OpenCodeSession,
    prompt_digest,
)

from opencode_stub import StubOpenCodeServer, _session
from test_v03b_mcp_tools import call, envelope_of, make_workspace

# ---------------------------------------------------------------------------
# builders and probes
# ---------------------------------------------------------------------------


def build_parts(
    tmp_path: Path,
    stub: StubOpenCodeServer | None = None,
    *,
    bridge_factory: Any = None,
    bind_stub: bool = True,
) -> tuple[Any, Any, StubOpenCodeServer, Path]:
    """A real surface + server, returning the surface (for lock inspection)."""
    ws = make_workspace(tmp_path)
    stub = stub or StubOpenCodeServer(workspace=str(ws))
    if bind_stub:
        stub.workspace = str(ws)
        for session in stub.sessions:
            session["directory"] = str(ws)
    if bridge_factory is None:
        ledger = FilesystemOpenCodeLedger(ws / ".devrelay")

        def bridge_factory() -> Any:  # noqa: F811 - injected factory
            return stub.bridge(workspace_root=str(ws), ledger=ledger)

    surface = build_surface(ws, bridge_factory=bridge_factory)
    return surface, create_server(surface), stub, ws


class LedgerOverlapProbe:
    """Delegating ledger that measures concurrent entry into the ledger.

    Every tool body reaches the accepted ledger through ``allocate_call_id`` /
    ``begin`` / ``finish``; with the v0.3-B boundary in place the measured
    maximum must be exactly 1.  The probe never changes behaviour, so a
    legitimate read/write is unaffected (it deliberately is *not* a lock: a
    regression must show up as measured overlap, not as a self-inflicted fix).
    """

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self._guard = threading.Lock()
        self.active = 0
        self.max_overlap = 0
        self.entries = 0

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def _note_enter(self) -> None:
        with self._guard:
            self.active += 1
            self.entries += 1
            self.max_overlap = max(self.max_overlap, self.active)

    def _note_exit(self) -> None:
        with self._guard:
            self.active -= 1

    def allocate_call_id(self) -> Any:
        self._note_enter()
        try:
            return self._inner.allocate_call_id()
        finally:
            self._note_exit()

    def begin(self, record: Any) -> Any:
        self._note_enter()
        try:
            return self._inner.begin(record)
        finally:
            self._note_exit()

    def finish(self, record: Any) -> Any:
        self._note_enter()
        try:
            return self._inner.finish(record)
        finally:
            self._note_exit()


def probed_server(
    tmp_path: Path, stub: StubOpenCodeServer | None = None, *, bind_stub: bool = True
) -> tuple[Any, Any, StubOpenCodeServer, Path, LedgerOverlapProbe]:
    """A real server whose real bridge writes the real (probed) ledger."""
    holder: dict[str, Any] = {}

    def factory() -> Any:
        return stub.bridge(  # type: ignore[union-attr]
            workspace_root=str(holder["ws"]), ledger=holder["ledger"]
        )

    ws = make_workspace(tmp_path)
    stub = stub or StubOpenCodeServer(workspace=str(ws))
    if bind_stub:
        stub.workspace = str(ws)
        for session in stub.sessions:
            session["directory"] = str(ws)
    holder["ws"] = ws
    holder["ledger"] = LedgerOverlapProbe(FilesystemOpenCodeLedger(ws / ".devrelay"))
    surface = build_surface(ws, bridge_factory=factory)
    return surface, create_server(surface), stub, ws, holder["ledger"]


async def gather_tools(server: Any, calls: list[tuple[str, dict[str, Any]]]) -> list[Any]:
    """Run MCP tool calls concurrently, exactly as a parallel client would."""
    return await asyncio.gather(
        *[server.call_tool(name, arguments) for name, arguments in calls]
    )


def read_calls(n: int, session: str = "ses_match") -> list[tuple[str, dict[str, Any]]]:
    return [("opencode_read_messages", {"session_id": session}) for _ in range(n)]


def ledger_records(ws: Path, limit: int = 200) -> list[dict[str, Any]]:
    return read_records_strict(ws / ".devrelay", limit=limit)


def assert_ledger_integrity(ws: Path, records: list[dict[str, Any]]) -> None:
    """Every durable call identity is unique, settled and contiguously numbered."""
    ids = [record["call_id"] for record in records]
    assert len(ids) == len(set(ids)), f"duplicate OpenCode call identity: {ids}"
    numbers = sorted(int(call_id.split("-")[1]) for call_id in ids)
    assert numbers == list(range(1, len(numbers) + 1)), numbers
    issued = [
        record["call_id"]
        for record in records
        if record["state"] == OpenCodeCallState.ISSUED.value
    ]
    assert issued == [], f"settled parallel batch left ISSUED records: {issued}"
    assert sequence_state(ws / ".devrelay")["next_call_sequence"] == len(ids) + 1


# ---------------------------------------------------------------------------
# parallel reads: the reported smoke blocker
# ---------------------------------------------------------------------------
def test_parallel_read_tools_never_race_the_ledger(tmp_path):
    """8 concurrent reads must all succeed with unique, settled call identities."""
    surface, server, stub, ws, ledger = probed_server(tmp_path)

    results = asyncio.run(gather_tools(server, read_calls(8)))
    envelopes = [envelope_of(result) for result in results]

    failures = [
        (envelope["error"]["type"], envelope["error"]["message"])
        for envelope in envelopes
        if not envelope["ok"]
    ]
    assert failures == [], f"parallel reads failed: {failures}"
    assert ledger.max_overlap == 1, (
        "at most one tool body may touch the accepted ledger at a time "
        f"(measured max overlap: {ledger.max_overlap})"
    )
    for envelope in envelopes:
        assert envelope["error"] is None, envelope

    records = ledger_records(ws)
    call_ids = [
        call_id for envelope in envelopes for call_id in envelope["data"]["call_ids"]
    ]
    assert len(call_ids) == len(set(call_ids)), "a read reused another read's call id"
    assert len(call_ids) == len(records), (call_ids, [r["call_id"] for r in records])
    assert_ledger_integrity(ws, records)

    # A read never submits: no POST may appear anywhere in the batch.
    assert [path for method, path in stub.requests if method == "POST"] == []
    assert sum(1 for method, path in stub.requests if path.endswith("/message")) == 8
    assert surface is not None


def test_parallel_reads_keep_the_reported_message_window_intact(tmp_path):
    """Serialized reads still return the provider's real message window."""
    _surface, server, _stub, _ws, ledger = probed_server(tmp_path)
    results = asyncio.run(gather_tools(server, read_calls(6)))
    for result in results:
        envelope = envelope_of(result)
        assert envelope["ok"] is True, envelope
        assert [message["message_id"] for message in envelope["data"]["messages"]] == [
            "msg_01",
            "msg_02",
        ]
    assert ledger.max_overlap == 1


# ---------------------------------------------------------------------------
# mixed batch: reads must never duplicate or race a submission POST
# ---------------------------------------------------------------------------
def test_parallel_reads_with_one_send_prompt_post_exactly_once(tmp_path):
    _surface, server, stub, ws, ledger = probed_server(tmp_path)
    calls = read_calls(4) + [
        ("opencode_send_prompt", {"session_id": "ses_match", "prompt": "one prompt"})
    ]

    results = asyncio.run(gather_tools(server, calls))
    envelopes = [envelope_of(result) for result in results]

    failures = [envelope for envelope in envelopes if not envelope["ok"]]
    assert failures == [], failures
    assert ledger.max_overlap == 1, f"measured max overlap: {ledger.max_overlap}"

    submissions = [path for method, path in stub.requests if method == "POST"]
    assert submissions == ["/session/ses_match/message"], (
        f"exactly one submission POST, never a retry or a duplicate: {submissions}"
    )
    assert len(stub.prompts) == 1, stub.prompts

    send_envelope = envelopes[-1]
    assert send_envelope["data"]["call_ids"], send_envelope
    assert send_envelope["data"]["retry_safe"] is False, (
        "an accepted submission is never retry_safe"
    )

    records = ledger_records(ws)
    assert_ledger_integrity(ws, records)
    send_records = [
        r
        for r in records
        if r["operation"] == "send_prompt" and r["method"] == "POST"
    ]
    assert len(send_records) == 1, (
        "exactly one recorded submission POST for the whole mixed batch: "
        f"{send_records}"
    )
    assert send_records[0]["state"] == OpenCodeCallState.COMPLETED.value
    assert send_records[0]["external_request_count"] >= 1, send_records[0]
    assert [p for m, p in stub.requests if m == "POST"] == ["/session/ses_match/message"]
    assert len(records) > len(send_records), "the four reads must have recorded too"


# ---------------------------------------------------------------------------
# cross-tool serialization matrix
# ---------------------------------------------------------------------------
class GateBridge:
    """Fake bridge that holds its first caller until the test releases it.

    Overlap is measured at the bridge boundary: if two tool bodies could run at
    the same time, the second one is guaranteed to be observed inside the bridge
    while the first is gated (the tool bodies are otherwise microseconds long).
    """

    def __init__(self) -> None:
        self._guard = threading.Lock()
        self.active = 0
        self.max_concurrent_execution = 0
        self.entered: list[str] = []
        self.first_entered = threading.Event()
        self.release = threading.Event()

    def _enter(self, operation: str) -> None:
        with self._guard:
            self.active += 1
            self.max_concurrent_execution = max(
                self.max_concurrent_execution, self.active
            )
            self.entered.append(operation)
            index = len(self.entered)
        self.first_entered.set()
        if index == 1:
            self.release.wait(timeout=5)
        with self._guard:
            self.active -= 1

    @staticmethod
    def _result(operation: str, state: OpenCodeOperationState) -> OpenCodeOperationResult:
        return OpenCodeOperationResult(
            operation=operation,
            state=state,
            session_id="ses_match",
            call_ids=[f"GATE-{operation}"],
            request_count=1,
            submission_attempted=operation == "send_prompt",
            submission_status=200 if operation == "send_prompt" else None,
        )

    # -- read paths ----------------------------------------------------
    def health(self) -> OpenCodeOperationResult:
        self._enter("health")
        return self._result("health", OpenCodeOperationState.COMPLETED)

    def list_sessions(self, **_kwargs: Any) -> OpenCodeOperationResult:
        self._enter("list_sessions")
        return self._result("list_sessions", OpenCodeOperationState.COMPLETED)

    def get_session(self, session_id: str) -> OpenCodeOperationResult:
        self._enter("get_session")
        result = self._result("get_session", OpenCodeOperationState.COMPLETED)
        return result.model_copy(
            update={
                "session": OpenCodeSession(
                    session_id=session_id, workspace="C:/workspace", title="gated"
                )
            }
        )

    def read_messages(self, session_id: str, cursor: Any = None) -> OpenCodeOperationResult:
        self._enter("read_messages")
        result = self._result("read_messages", OpenCodeOperationState.COMPLETED)
        return result.model_copy(
            update={
                "messages": [
                    OpenCodeMessage(
                        message_id="msg_gate",
                        role="assistant",
                        parts=[OpenCodeMessagePart(kind="text", text="gated reply")],
                    )
                ]
            }
        )

    def wait_idle(self, session_id: str, timeout: Any = None) -> OpenCodeOperationResult:
        self._enter("wait_idle")
        return self._result("wait_idle", OpenCodeOperationState.COMPLETED)

    # -- side-effecting paths ------------------------------------------
    def send_prompt(
        self, session_id: str, prompt: str, *, agent: str = "", model: str = ""
    ) -> OpenCodeOperationResult:
        self._enter("send_prompt")
        return self._result("send_prompt", OpenCodeOperationState.COMPLETED)

    def interrupt(self, session_id: str) -> OpenCodeOperationResult:
        self._enter("interrupt")
        return self._result("interrupt", OpenCodeOperationState.INTERRUPTED)


MATRIX_PAIRS: tuple[tuple[str, tuple[str, dict[str, Any]], tuple[str, dict[str, Any]]], ...] = (
    (
        "read+read",
        ("opencode_read_messages", {"session_id": "ses_match"}),
        ("opencode_read_messages", {"session_id": "ses_match"}),
    ),
    (
        "read+send",
        ("opencode_read_messages", {"session_id": "ses_match"}),
        ("opencode_send_prompt", {"session_id": "ses_match", "prompt": "hi"}),
    ),
    (
        "read+interrupt",
        ("opencode_read_messages", {"session_id": "ses_match"}),
        ("opencode_interrupt", {"session_id": "ses_match"}),
    ),
    (
        "send+interrupt",
        ("opencode_send_prompt", {"session_id": "ses_match", "prompt": "hi"}),
        ("opencode_interrupt", {"session_id": "ses_match"}),
    ),
    (
        "send+send",
        ("opencode_send_prompt", {"session_id": "ses_match", "prompt": "one"}),
        ("opencode_send_prompt", {"session_id": "ses_match", "prompt": "two"}),
    ),
)


@pytest.mark.parametrize(
    "label,first,second", MATRIX_PAIRS, ids=[pair[0] for pair in MATRIX_PAIRS]
)
def test_cross_tool_matrix_never_overlaps(tmp_path, label, first, second):
    """No pair of tools may execute at the same time in one server process."""
    bridge = GateBridge()
    _surface, server, _stub, _ws = build_parts(tmp_path, bridge_factory=lambda: bridge)

    async def run() -> list[Any]:
        running = asyncio.create_task(server.call_tool(*first))
        while not bridge.first_entered.is_set():
            await asyncio.sleep(0.01)
        second_task = asyncio.create_task(server.call_tool(*second))
        try:
            # The whole point: while the first body owns the boundary, the
            # second body must not reach the bridge at all.
            for _ in range(30):
                await asyncio.sleep(0.01)
                assert bridge.max_concurrent_execution == 1, (
                    f"{label}: {bridge.max_concurrent_execution} tool bodies "
                    "touched the bridge at once"
                )
            assert bridge.entered == [first[0].removeprefix("opencode_")], bridge.entered
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
    assert bridge.active == 0, "every tool body released the boundary"


# ---------------------------------------------------------------------------
# foreign-workspace isolation under parallel load (semantics unchanged)
# ---------------------------------------------------------------------------
def test_parallel_foreign_workspace_reads_fail_closed_without_ledger_writes(tmp_path):
    foreign = StubOpenCodeServer(
        workspace="C:/elsewhere",
        sessions=[_session("ses_foreign", workspace="C:/elsewhere")],
    )
    _surface, server, _stub, ws, ledger = probed_server(tmp_path, foreign, bind_stub=False)

    results = asyncio.run(gather_tools(server, read_calls(4, session="ses_foreign")))
    for result in results:
        envelope = envelope_of(result)
        assert envelope["ok"] is False, envelope
        assert envelope["error"]["type"] == "opencode_session_workspace_mismatch", envelope
    assert ledger.max_overlap == 1
    # A refused foreign session is never submitted to, and the ownership probe
    # that proved the refusal is itself recorded - once, settled, contiguously.
    records = ledger_records(ws)
    assert [record["method"] for record in records] == ["GET"] * 4, records
    assert [path for method, path in _stub.requests if method == "POST"] == []
    assert_ledger_integrity(ws, records)


# ---------------------------------------------------------------------------
# the lock is released after every failure kind
# ---------------------------------------------------------------------------
class ScriptedBridge:
    """Fake bridge whose behaviour is switched between the failure and the retry."""

    def __init__(self, mode: str = "ok") -> None:
        self.mode = mode
        self.calls = 0

    def _respond(self, operation: str) -> Any:
        self.calls += 1
        if self.mode == "raise":
            raise RuntimeError("unexpected bridge explosion")
        if self.mode == "malformed":
            return "not-an-operation-result"
        if self.mode == "unavailable":
            return OpenCodeOperationResult(
                operation=operation,
                state=OpenCodeOperationState.PROVIDER_UNAVAILABLE,
                error_type="provider_unavailable",
                error="provider refused the request",
            )
        if self.mode == "uncertain":
            return OpenCodeOperationResult(
                operation=operation,
                state=OpenCodeOperationState.TIMED_OUT,
                session_id="ses_match",
                submission_attempted=True,
                submission_uncertain=True,
                reply_pending=True,
                error_type="read_timeout",
                error="the submission may already have reached the server",
            )
        if self.mode == "interrupt_not_accepted":
            return OpenCodeOperationResult(
                operation=operation,
                state=OpenCodeOperationState.COMPLETED,
                session_id="ses_match",
                call_ids=["SCRIPTED"],
                request_count=1,
            )
        return OpenCodeOperationResult(
            operation=operation,
            state=OpenCodeOperationState.COMPLETED,
            session_id="ses_match",
            call_ids=[f"SCRIPTED-{operation}"],
            request_count=1,
        )

    def health(self, *_args: Any, **_kwargs: Any) -> Any:
        return self._respond("health")

    def read_messages(self, *_args: Any, **_kwargs: Any) -> Any:
        return self._respond("read_messages")

    def send_prompt(self, *_args: Any, **_kwargs: Any) -> Any:
        return self._respond("send_prompt")

    def interrupt(self, *_args: Any, **_kwargs: Any) -> Any:
        return self._respond("interrupt")


FAILURE_KINDS: tuple[tuple[str, str, str, str, dict[str, Any]], ...] = (
    (
        "invalid_session_argument",
        "ok",
        "opencode_read_messages",
        "mcp_invalid_argument",
        {"session_id": "not a session id"},
    ),
    (
        "invalid_limit_argument",
        "ok",
        "opencode_calls",
        "mcp_invalid_argument",
        {"limit": 0},
    ),
    (
        "provider_unavailable",
        "unavailable",
        "opencode_health",
        "provider_unavailable",
        {},
    ),
    ("malformed_result", "malformed", "opencode_health", "internal_error", {}),
    ("unexpected_exception", "raise", "opencode_health", "internal_error", {}),
    (
        "interrupt_not_accepted",
        "interrupt_not_accepted",
        "opencode_interrupt",
        "interrupt_not_accepted",
        {"session_id": "ses_match"},
    ),
    (
        "submission_uncertain",
        "uncertain",
        "opencode_send_prompt",
        "read_timeout",
        {"session_id": "ses_match", "prompt": "hi"},
    ),
)


@pytest.mark.parametrize(
    "label,mode,tool,error_type,arguments",
    FAILURE_KINDS,
    ids=[case[0] for case in FAILURE_KINDS],
)
def test_execution_lock_is_released_after_every_failure(
    tmp_path, label, mode, tool, error_type, arguments
):
    bridge = ScriptedBridge(mode)
    surface, server, _stub, _ws = build_parts(tmp_path, bridge_factory=lambda: bridge)

    failed = call(server, tool, arguments)
    assert failed["ok"] is False, (label, failed)
    assert failed["error"]["type"] == error_type, (label, failed)

    # The boundary must be free again: a real acquire from this thread cannot
    # succeed while the execution lock is still held.
    acquired = surface._execution_lock.acquire(timeout=2)
    assert acquired, f"{label}: the execution lock was not released"
    surface._execution_lock.release()

    # ... and the surface must still work end to end through the same bridge.
    bridge.mode = "ok"
    recovered = call(server, "opencode_health")
    assert recovered["ok"] is True, (label, recovered)


def test_lock_released_after_real_bridge_provider_failure(tmp_path):
    """The same rule against the real accepted bridge (stub HTTP 500)."""
    stub = StubOpenCodeServer(
        messages_http_status=500, messages_error_body='{"error":"nope"}'
    )
    surface, server, _stub, _ws, ledger = probed_server(tmp_path, stub)

    failed = call(server, "opencode_read_messages", {"session_id": "ses_match"})
    assert failed["ok"] is False, failed
    assert failed["error"]["type"] != "internal_error", failed

    acquired = surface._execution_lock.acquire(timeout=2)
    assert acquired, "the execution lock was not released after a provider failure"
    surface._execution_lock.release()
    assert ledger.max_overlap == 1


# ---------------------------------------------------------------------------
# cancellation: honest, bounded, never retried, never auto-interrupted
# ---------------------------------------------------------------------------
class CancellableSubmitBridge:
    """Records a submission, then blocks inside the bridge until released."""

    def __init__(self, ledger: FilesystemOpenCodeLedger) -> None:
        self.ledger = ledger
        self.submissions = 0
        self.interrupt_calls = 0
        self.health_calls = 0
        self.entered = threading.Event()
        self.release = threading.Event()
        self.finished = threading.Event()

    def send_prompt(
        self, session_id: str, prompt: str, *, agent: str = "", model: str = ""
    ) -> OpenCodeOperationResult:
        from devrelay.models import utcnow_iso

        self.submissions += 1
        record = OpenCodeCallRecord(
            call_id=self.ledger.allocate_call_id(),
            operation="send_prompt",
            state=OpenCodeCallState.ISSUED,
            method="POST",
            path="/session/ses_match/message",
            session_id=session_id,
            prompt_sha256=prompt_digest(prompt),
            prompt_chars=len(prompt),
        )
        self.ledger.begin(record)
        self.entered.set()
        try:
            self.release.wait(timeout=10)
            self.ledger.finish(
                record.model_copy(
                    update={
                        "state": OpenCodeCallState.TIMED_OUT,
                        "completed_at": utcnow_iso(),
                        "error_type": "read_timeout",
                        "submission_uncertain": True,
                    }
                )
            )
        finally:
            self.finished.set()
        return OpenCodeOperationResult(
            operation="send_prompt",
            state=OpenCodeOperationState.TIMED_OUT,
            session_id=session_id,
            submission_attempted=True,
            submission_uncertain=True,
            reply_pending=True,
            error_type="read_timeout",
            error="the submission may already have reached the server",
        )

    def health(self) -> OpenCodeOperationResult:
        self.health_calls += 1
        return OpenCodeOperationResult(
            operation="health", state=OpenCodeOperationState.COMPLETED
        )

    def interrupt(self, session_id: str) -> OpenCodeOperationResult:
        self.interrupt_calls += 1
        return OpenCodeOperationResult(
            operation="interrupt",
            state=OpenCodeOperationState.INTERRUPTED,
            session_id=session_id,
        )


def test_cancellation_keeps_the_boundary_until_the_body_exits(tmp_path):
    """Cancelling the await must not release the boundary or fake a clean stop."""
    ws = make_workspace(tmp_path)
    ledger = FilesystemOpenCodeLedger(ws / ".devrelay")
    bridge = CancellableSubmitBridge(ledger)
    surface, server, _stub, _ws = build_parts(tmp_path, bridge_factory=lambda: bridge)

    async def run() -> dict[str, Any]:
        task = asyncio.create_task(
            server.call_tool(
                "opencode_send_prompt", {"session_id": "ses_match", "prompt": "one"}
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

        # The client's request is gone, but the worker body still owns the
        # boundary: a concurrent tool call must NOT run yet.
        follow_up = asyncio.create_task(server.call_tool("opencode_health", {}))
        await asyncio.sleep(0.3)
        blocked_while_body_runs = not follow_up.done()
        bridge.release.set()
        health = await asyncio.wait_for(follow_up, timeout=10)
        return {
            "outcome": outcome,
            "blocked_while_body_runs": blocked_while_body_runs,
            "health": envelope_of(health),
        }

    observed = asyncio.run(run())

    assert observed["outcome"] == "cancelled"
    assert observed["blocked_while_body_runs"] is True, (
        "cancelling the MCP await does not stop an already-running tool body: "
        "the boundary must stay held until that body exits"
    )
    assert observed["health"]["ok"] is True, observed["health"]
    assert bridge.submissions == 1, "a cancelled submission must never be retried"
    assert bridge.interrupt_calls == 0, "no automatic interrupt may be issued"
    assert bridge.health_calls == 1
    assert bridge.finished.is_set(), "the worker body finished before the lock freed"

    records = ledger_records(ws)
    assert len(records) == 1, records
    assert records[0]["state"] == OpenCodeCallState.TIMED_OUT.value
    assert records[0]["submission_uncertain"] is True
    assert records[0]["prompt_chars"] == len("one")
    assert records[0]["method"] == "POST"

    # The lock is free again once the body really exited.
    acquired = surface._execution_lock.acquire(timeout=2)
    assert acquired, "the boundary must be free after the cancelled body exited"
    surface._execution_lock.release()


# ---------------------------------------------------------------------------
# lock identity: one lock, shared, re-entrant, and no leftover second lock
# ---------------------------------------------------------------------------
def test_one_reentrant_execution_lock_and_no_second_lock(tmp_path):
    surface, server, _stub, _ws = build_parts(tmp_path)
    lock = surface._execution_lock
    assert isinstance(lock, type(threading.RLock())), type(lock)
    assert lock is surface._execution_lock, "one lock per surface"
    assert not hasattr(surface, "_side_effect_lock"), (
        "the redundant side-effect lock must be gone: serialization is global"
    )
    assert not hasattr(surface, "_bridge_lock"), (
        "bridge construction uses the same execution lock"
    )

    # Re-entrancy is required: a tool body lazily constructs the bridge while
    # already holding the boundary.
    assert lock.acquire(timeout=2)
    try:
        surface.bridge()  # must not deadlock
        assert lock.acquire(timeout=2), "the execution lock must be re-entrant"
        lock.release()
    finally:
        lock.release()

    # And the boundary really is shared with the running server.
    assert call(server, "devrelay_status")["ok"] is True

    source = Path(tools_module.__file__).read_text(encoding="utf-8")
    assert source.count("threading.RLock()") == 1, "exactly one execution lock"
    assert "threading.Lock()" not in source, "no second, non-reentrant lock"


# ---------------------------------------------------------------------------
# structural proof that the boundary covers all nine tools
# ---------------------------------------------------------------------------
def test_every_advertised_tool_runs_through_the_execution_choke_point():
    tree = ast.parse(Path(tools_module.__file__).read_text(encoding="utf-8"))
    surface = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "McpToolSurface"
    )
    bodies: dict[str, ast.FunctionDef] = {}
    for node in surface.body:
        if isinstance(node, ast.FunctionDef) and node.name in TOOL_NAMES:
            bodies[node.name] = node
    assert sorted(bodies) == sorted(TOOL_NAMES), "every advertised tool is defined here"
    for name, node in bodies.items():
        routed = [
            call_node
            for call_node in ast.walk(node)
            if isinstance(call_node, ast.Call)
            and isinstance(call_node.func, ast.Attribute)
            and call_node.func.attr == "_execute"
        ]
        assert routed, f"{name} must route its body through _execute (the boundary)"
    assert "_execution_lock" in inspect.getsource(tools_module.McpToolSurface._execute)


def test_status_reports_the_global_serialization_boundary(tmp_path):
    _surface, server, _stub, _ws = build_parts(tmp_path)
    data = call(server, "devrelay_status")["data"]
    assert data["mcp"]["execution_serialized"] is True
    assert data["mcp"]["side_effects_serialized"] is True
    assert "lock" in data["mcp"]["serialization"]
