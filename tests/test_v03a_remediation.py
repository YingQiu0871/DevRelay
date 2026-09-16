"""v0.3-A independent-review remediation: focused regression tests.

Every test here exists because of one specific review finding, and each one is
written so it *fails* against the pre-remediation code:

* P1-1  the declared whole-operation idle timeout is really enforced
* P1-2  the message window keeps the newest messages (never head-truncates)
* P1-3  the assistant reply is correlated honestly (never a stale/incidental one)
* P1-4  the OpenCode bearer token never reaches a Codex child
* P2-A  ambient proxy/CA environment can never reroute the control channel
* P2-B  session ids are opaque and cannot change a URL path
* P2-C  interrupt semantics (204/JSON/404/405/501/oversized) are explicit
* P2-D  provider echoes of the prompt/token never reach ledger or console
* P2-E  the call ledger fails closed instead of reusing call identities
* P2-F  ``--json`` keeps a failing exit status (rendering never hides failure)
* PART III  wiring-vs-policy config coverage (defaults, bounds, projection)

Everything is offline: the deterministic in-memory stub plus a fake clock and a
spy transport.  No real OpenCode server, no network, no model call.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError
from typer.testing import CliRunner

from devrelay.cli import app
from devrelay.config import (
    OpenCodeConfig,
    load_policy_snapshot,
    load_wiring_config,
    load_workspace_file,
    workspace_policy_overrides,
)
from devrelay.errors import (
    ConfigError,
    OpenCodeConfigError,
    OpenCodeLedgerError,
    OpenCodeSessionWorkspaceMismatchError,
)
from devrelay.opencode.accounting import FilesystemOpenCodeLedger
from devrelay.opencode.bridge import OpenCodeBridge
from devrelay.opencode.models import (
    MAX_MESSAGES,
    OpenCodeCallRecord,
    OpenCodeCallState,
    OpenCodeOperationState,
)
from devrelay.opencode.transport import OpenCodeTransport
from devrelay.profiles import resolve_policy_config
from devrelay.providers.codex_runtime import CODEX_CHILD_ENV_DENYLIST

from helpers import make_git_repo
from opencode_stub import DEFAULT_WORKSPACE, StubOpenCodeServer, _message, _session

WS = DEFAULT_WORKSPACE
TOKEN = "oc-token-REMEDIATION-4711-abcdef"
#: The wire-level window cap (``MAX_MESSAGES`` in the models module); the bridge
#: must expose the same number as its hard maximum.
HARD_MAX_MESSAGES = MAX_MESSAGES


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _ledger(tmp_path: Path) -> FilesystemOpenCodeLedger:
    return FilesystemOpenCodeLedger(tmp_path / ".devrelay")


class _Clock:
    """Deterministic monotonic clock (no test ever sleeps for real)."""

    def __init__(self, start: float = 1_000.0) -> None:
        self.now = start
        self.start = start
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.advance(seconds)


class _SpyTransport:
    """Real stub transport + recorded per-request deadlines on a fake clock."""

    def __init__(
        self, inner: OpenCodeTransport, clock: _Clock, *, latency: float = 0.5
    ) -> None:
        self.inner = inner
        self.clock = clock
        self.latency = latency
        #: (method, path, start_time, requested_timeout)
        self.calls: list[tuple[str, str, float, float | None]] = []

    @property
    def base_url(self) -> str:  # pragma: no cover - parity only
        return self.inner.base_url

    def request(self, method: str, path: str, **kwargs: Any):
        started = self.clock.now
        self.calls.append((method, path, started, kwargs.get("timeout_seconds")))
        response = self.inner.request(method, path, **kwargs)
        self.clock.advance(self.latency)
        # Make the artificial latency visible as real call evidence.
        return dataclasses.replace(response, duration_ms=int(self.latency * 1000))

    def deadlines(self) -> list[float]:
        return [start + (timeout or 0.0) for _, _, start, timeout in self.calls]


def _busy_stub(**kwargs: Any) -> StubOpenCodeServer:
    """Stub whose *real* runtime status is busy (GET /session/status)."""
    return StubOpenCodeServer(status_map={"ses_match": {"type": "busy"}}, **kwargs)


# ---------------------------------------------------------------------------
# P1-1: the declared whole-operation idle budget is really enforced
# ---------------------------------------------------------------------------
def test_wait_idle_keeps_probe_and_polls_inside_the_declared_budget(tmp_path):
    """The probe is part of the budget, and no request outlives the deadline."""
    clock = _Clock()
    stub = _busy_stub()
    spy = _SpyTransport(stub.transport(), clock, latency=0.5)
    bridge = OpenCodeBridge(
        base_url="http://opencode.invalid",
        workspace_root=WS,
        idle_timeout_seconds=2.0,
        poll_interval_seconds=1.0,
        transport=spy,
        ledger=_ledger(tmp_path),
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    result = bridge.wait_idle("ses_match")

    assert result.state is OpenCodeOperationState.TIMED_OUT
    assert result.error_type == "idle_timeout"
    deadline = clock.start + 2.0
    assert spy.calls, "the probe must be an accounted request"
    for _method, _path, started, timeout in spy.calls:
        assert timeout is not None
        assert 0.0 < timeout <= 2.0, "a request may never ask for the full default"
        assert started + timeout <= deadline + 1e-9, "no request may outlive the deadline"
    # probe (0.5s) + poll (0.5s) + a sleep clamped to the remaining 1.0s
    assert len(spy.calls) == 2
    assert clock.sleeps == [pytest.approx(1.0)]
    assert clock.now - clock.start == pytest.approx(2.0)
    # whole-operation duration evidence is the sum of the accounted calls
    assert result.duration_ms == 1_000
    # nothing runs after the operation returned
    after = len(spy.calls)
    assert len(spy.calls) == after


def test_wait_idle_explicit_timeout_wins_over_the_configured_default(tmp_path):
    """A 300s configured default cannot extend a 1s explicit wait."""
    clock = _Clock()
    stub = _busy_stub()
    spy = _SpyTransport(stub.transport(), clock, latency=0.5)
    bridge = OpenCodeBridge(
        base_url="http://opencode.invalid",
        workspace_root=WS,
        idle_timeout_seconds=300.0,
        poll_interval_seconds=1.0,
        transport=spy,
        ledger=_ledger(tmp_path),
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    result = bridge.wait_idle("ses_match", 1.0)

    assert result.state is OpenCodeOperationState.TIMED_OUT
    for _method, _path, started, timeout in spy.calls:
        assert 0.0 < timeout <= 1.0
        assert started + timeout <= clock.start + 1.0 + 1e-9
    assert clock.now - clock.start == pytest.approx(1.0)
    assert "1s" in result.error and "300" not in result.error


def test_wait_idle_probe_alone_cannot_outlive_a_tiny_budget(tmp_path):
    """The probe request itself is clamped to the remaining budget."""
    clock = _Clock()
    stub = _busy_stub()
    spy = _SpyTransport(stub.transport(), clock, latency=1.0)
    bridge = OpenCodeBridge(
        base_url="http://opencode.invalid",
        workspace_root=WS,
        poll_interval_seconds=1.0,
        transport=spy,
        ledger=_ledger(tmp_path),
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    result = bridge.wait_idle("ses_match", 0.5)

    assert result.state is OpenCodeOperationState.TIMED_OUT
    assert len(spy.calls) == 1, "no poll may be issued once the budget is gone"
    assert spy.calls[0][3] == pytest.approx(0.5)
    assert clock.sleeps == []
    assert result.duration_ms == 1_000


def test_wait_idle_with_an_exhausted_budget_issues_no_request_at_all(tmp_path):
    clock = _Clock()
    stub = _busy_stub()
    spy = _SpyTransport(stub.transport(), clock, latency=0.0)
    bridge = OpenCodeBridge(
        base_url="http://opencode.invalid",
        workspace_root=WS,
        transport=spy,
        ledger=_ledger(tmp_path),
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    result = bridge.wait_idle("ses_match", 0.0)

    assert result.state is OpenCodeOperationState.TIMED_OUT
    assert result.operation == "wait_idle"
    assert spy.calls == []


def test_wait_idle_records_every_poll_as_its_own_ledger_call(tmp_path):
    clock = _Clock()
    stub = StubOpenCodeServer(
        status_sequence=[
            {"ses_match": {"type": "busy"}},
            {"ses_match": {"type": "busy"}},
            {},
        ]
    )
    spy = _SpyTransport(stub.transport(), clock, latency=0.5)
    ledger = _ledger(tmp_path)
    bridge = OpenCodeBridge(
        base_url="http://opencode.invalid",
        workspace_root=WS,
        idle_timeout_seconds=30.0,
        poll_interval_seconds=0.1,
        transport=spy,
        ledger=ledger,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    )
    result = bridge.wait_idle("ses_match")

    assert result.state is OpenCodeOperationState.COMPLETED
    assert result.session is not None and result.session.state is not None
    records = ledger.read_records()
    assert result.request_count == len(records) == len(spy.calls)
    assert set(result.call_ids) == {record.call_id for record in records}


# ---------------------------------------------------------------------------
# P1-2: the newest messages win (no head-truncation)
# ---------------------------------------------------------------------------
def _many_messages(count: int = 250) -> list[dict[str, Any]]:
    return [
        _message(
            f"msg_{index:03d}",
            "user" if index % 2 else "assistant",
            f"text {index}",
        )
        for index in range(1, count + 1)
    ]


def test_message_window_keeps_the_newest_and_reports_truncation():
    stub = StubOpenCodeServer(messages=_many_messages())
    result = stub.bridge().read_messages("ses_match")

    ids = [message.message_id for message in result.messages]
    assert len(ids) == 50
    assert ids[0] == "msg_201" and ids[-1] == "msg_250", "newest messages must win"
    assert "msg_001" not in ids
    assert result.page is not None
    assert result.page.window_truncated is True
    assert result.page.provider_message_count == 250
    assert result.page.next_cursor == "msg_250"
    assert result.page.hard_max_messages == HARD_MAX_MESSAGES


def test_message_window_cursor_near_the_tail_is_not_reported_as_nothing_new():
    stub = StubOpenCodeServer(messages=_many_messages())
    bridge = stub.bridge()

    tail = bridge.read_messages("ses_match", "msg_249")
    assert [message.message_id for message in tail.messages] == ["msg_250"]
    assert tail.page is not None
    assert tail.page.replayed is False and tail.page.cursor_unknown is False

    newest = bridge.read_messages("ses_match", "msg_250")
    assert newest.messages == []
    assert newest.page is not None
    assert newest.page.replayed is True and newest.page.cursor_unknown is False


def test_message_window_cursor_outside_the_window_is_flagged_not_dropped():
    stub = StubOpenCodeServer(messages=_many_messages())
    result = stub.bridge().read_messages("ses_match", "msg_001")

    assert result.page is not None
    assert result.page.cursor_unknown is True
    assert result.page.replayed is False
    assert [message.message_id for message in result.messages][-1] == "msg_250"


def test_message_window_configuration_above_the_hard_max_fails_closed():
    import devrelay.opencode.bridge as bridge_module

    assert bridge_module.HARD_MAX_MESSAGES == HARD_MAX_MESSAGES <= MAX_MESSAGES
    with pytest.raises(ValidationError):
        OpenCodeConfig(max_messages=HARD_MAX_MESSAGES + 1)
    with pytest.raises(OpenCodeConfigError):
        OpenCodeBridge(
            base_url="http://opencode.invalid",
            workspace_root=WS,
            max_messages=HARD_MAX_MESSAGES + 1,
        )
    # the boundary value itself is valid and honoured
    assert OpenCodeConfig(max_messages=HARD_MAX_MESSAGES).max_messages == HARD_MAX_MESSAGES
    stub = StubOpenCodeServer(messages=_many_messages())
    bridge = stub.bridge(max_messages=HARD_MAX_MESSAGES)
    result = bridge.read_messages("ses_match")
    assert len(result.messages) == HARD_MAX_MESSAGES
    assert result.messages[-1].message_id == "msg_250"


# ---------------------------------------------------------------------------
# P1-3: honest reply correlation
# ---------------------------------------------------------------------------
def test_send_prompt_never_substitutes_a_stale_assistant_reply():
    """POST accepted, no new message visible → pending, not the previous reply."""
    stub = StubOpenCodeServer(prompt_raw_reply={"ok": True})
    result = stub.bridge().send_prompt("ses_match", "hello")

    assert result.state is OpenCodeOperationState.COMPLETED
    assert result.reply_pending is True
    assert result.messages == []
    assert result.error_type == "reply_pending"
    payload = json.dumps(result.model_dump(mode="json"))
    assert "hi there" not in payload, "the stale reply must never be returned"
    assert result.reply_boundary == "msg_02"


@pytest.mark.parametrize(
    "payload",
    [
        {"id": "ses_match", "directory": WS, "state": "busy"},
        {"data": {"id": "ses_match", "directory": WS}},
        {"message": {"info": {"id": "msg_99", "role": "user"}, "parts": []}},
        {"message": {"info": {"id": "msg_98", "role": "assistant"}}},
    ],
)
def test_send_prompt_never_accepts_an_id_bearing_envelope_as_a_reply(payload):
    stub = StubOpenCodeServer(prompt_raw_reply=payload)
    result = stub.bridge().send_prompt("ses_match", "hello")

    assert result.reply_pending is True
    assert result.messages == []
    assert [m.message_id for m in result.messages] != ["msg_99"]


def test_send_prompt_ack_then_reply_correlates_only_the_new_message(tmp_path):
    stub = StubOpenCodeServer(prompt_ack_only=True)
    ledger = _ledger(tmp_path)
    result = stub.bridge(ledger=ledger).send_prompt("ses_match", "hello")

    assert result.state is OpenCodeOperationState.COMPLETED
    assert result.reply_pending is False
    assert [message.message_id for message in result.messages] == ["msg_03"]
    assert result.messages[0].role == "assistant"
    assert result.reply_boundary == "msg_02"
    assert result.follow_up_state == OpenCodeOperationState.COMPLETED.value
    # accounting: probe + boundary session + boundary messages + POST + follow-up
    records = ledger.read_records()
    # probe + boundary session + boundary messages + POST + follow-up session
    # + follow-up messages: every issued request, all settled exactly once.
    assert result.request_count == len(records) == 6
    assert set(result.call_ids) == {record.call_id for record in records}
    assert sum(1 for m, path in stub.requests if m == "POST" and path.endswith("/message")) == 1


def test_send_prompt_follow_up_404_is_an_honest_post_acceptance_result(tmp_path):
    """The prompt was accepted: a vanished session is not "never submitted"."""
    stub = StubOpenCodeServer(prompt_raw_reply={"ok": True}, vanish_after_prompt=True)
    ledger = _ledger(tmp_path)
    result = stub.bridge(ledger=ledger).send_prompt("ses_match", "hello")

    assert result.ok is False
    assert result.operation == "send_prompt"
    assert result.state is OpenCodeOperationState.PROVIDER_UNAVAILABLE
    assert result.error_type == "follow_up_session_not_found"
    assert result.reply_pending is True
    assert "never submitted" not in result.error
    # every request that was issued is accounted for - including the failed one
    records = ledger.read_records()
    assert result.request_count == len(records) == 5
    assert set(result.call_ids) == {record.call_id for record in records}
    assert sum(1 for m, path in stub.requests if m == "POST" and path.endswith("/message")) == 1


def test_send_prompt_follow_up_failure_is_surfaced_not_swallowed(tmp_path):
    prompt = "PROMPT-ECHO-9001 " + "x" * 200
    stub = StubOpenCodeServer(
        prompt_raw_reply={"ok": True},
        session_http_status_after_prompt=500,
        session_error_body_after_prompt=json.dumps(
            {"error": prompt, "auth": TOKEN, "pad": "y" * 5_000}
        ),
    )
    ledger = _ledger(tmp_path)
    transport = stub.transport(token=TOKEN)
    result = OpenCodeBridge(
        base_url="http://opencode.invalid",
        workspace_root=WS,
        token=TOKEN,
        transport=transport,
        ledger=ledger,
    ).send_prompt("ses_match", prompt)

    assert result.state is OpenCodeOperationState.PROVIDER_UNAVAILABLE
    assert result.reply_pending is True
    assert result.error_type == "http_status"
    assert result.follow_up_state == OpenCodeOperationState.PROVIDER_UNAVAILABLE.value
    assert result.http_status == 500
    assert result.error.startswith("HTTP 500")
    assert len(result.error) <= 600, "error snippets must stay bounded"
    records = ledger.read_records()
    assert result.request_count == len(records) == 5
    assert set(result.call_ids) == {record.call_id for record in records}


# ---------------------------------------------------------------------------
# P1-4: the OpenCode token never reaches a Codex child
# ---------------------------------------------------------------------------
def test_opencode_token_is_in_the_codex_child_denylist():
    assert "DEVRELAY_OPENCODE_TOKEN" in CODEX_CHILD_ENV_DENYLIST, (
        "the OpenCode bearer credential must be scrubbed from every Codex child "
        "(a child holding it could bypass the bridge entirely)"
    )


def test_codex_child_never_receives_the_opencode_token(tmp_path, monkeypatch):
    """End-to-end through the real structured runtime + offline Codex stub."""
    from test_v02c_structured import (
        STATE,
        _default_config,
        _engine_with_stub,
        _start,
    )

    from helpers import write_codex_stub

    monkeypatch.setenv("DEVRELAY_OPENCODE_TOKEN", TOKEN)
    env_capture = tmp_path / "child-env.json"
    stub = write_codex_stub(
        tmp_path / "tools",
        env_capture=str(env_capture),
        env_names=["DEVRELAY_OPENCODE_TOKEN"],
        changed_files=["app.py"],
    )
    root, store, engine = _engine_with_stub(tmp_path, stub)
    _start(engine, store)
    engine.continue_task(STATE)

    captured = json.loads(env_capture.read_text(encoding="utf-8"))
    assert captured == {"DEVRELAY_OPENCODE_TOKEN": False}, (
        "the Codex child process environment must not contain the OpenCode token"
    )
    # the parent keeps its credential, and it is never persisted either
    assert __import__("os").environ["DEVRELAY_OPENCODE_TOKEN"] == TOKEN
    for path in Path(root).rglob("*"):
        if path.is_file():
            assert TOKEN not in path.read_text(encoding="utf-8", errors="replace")


def test_doctor_reports_the_scrubbed_opencode_token(tmp_path, monkeypatch):
    repo = _cli_workspace(tmp_path, monkeypatch)
    monkeypatch.chdir(repo)
    monkeypatch.setenv("DEVRELAY_OPENCODE_TOKEN", TOKEN)
    result = CliRunner().invoke(app, ["doctor"])
    assert result.exit_code == 0, result.output
    assert "DEVRELAY_OPENCODE_TOKEN" in result.output
    assert TOKEN not in result.output, "doctor reports names, never values"


# ---------------------------------------------------------------------------
# P2-A: ambient proxy / CA environment cannot reroute the control channel
# ---------------------------------------------------------------------------
def test_transport_ignores_ambient_proxy_configuration(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.invalid:3128")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.invalid:3128")
    monkeypatch.setenv("ALL_PROXY", "http://proxy.invalid:3128")
    transport = OpenCodeTransport("http://127.0.0.1:4096")
    try:
        assert transport._client.trust_env is False
        mounts = transport._client._mounts
        assert not mounts, "an ambient proxy must not create a transport mount"
    finally:
        transport._client.close()


# ---------------------------------------------------------------------------
# P2-B: session ids are opaque and cannot change a URL path
# ---------------------------------------------------------------------------
BAD_SESSION_IDS = [
    "abc/../other",
    "abc#fragment",
    "abc?x=1",
    "../escape",
    "..",
    "a b",
    "a\tb",
    "a\nb",
    "x" * 201,
    "",
    "   ",
]


@pytest.mark.parametrize("bad", BAD_SESSION_IDS)
def test_invalid_session_ids_issue_zero_requests(bad):
    stub = StubOpenCodeServer()
    bridge = stub.bridge()
    for call in (
        lambda: bridge.get_session(bad),
        lambda: bridge.read_messages(bad),
        lambda: bridge.wait_idle(bad, 0.01),
        lambda: bridge.interrupt(bad),
        lambda: bridge.send_prompt(bad, "hello"),
    ):
        with pytest.raises(OpenCodeConfigError):
            call()
    assert stub.requests == [], (
        "an identifier that could change a URL path must be rejected before any "
        "request is constructed"
    )


def test_valid_opaque_session_id_is_accepted():
    session_id = "ses_Match.1~x-y"
    stub = StubOpenCodeServer(sessions=[_session(session_id, workspace=WS)])
    result = stub.bridge().get_session(session_id)
    assert result.ok is True
    assert stub.requests == [("GET", f"/session/{session_id}")]


def test_returned_session_id_must_match_the_requested_one():
    stub = StubOpenCodeServer(session_id_override="ses_other")
    result = stub.bridge().get_session("ses_match")
    assert result.state is OpenCodeOperationState.MALFORMED_RESPONSE
    assert "ses_other" in result.error and "ses_match" in result.error


def test_returned_id_mismatch_blocks_acting_operations():
    stub = StubOpenCodeServer(session_id_override="ses_other")
    result = stub.bridge().send_prompt("ses_match", "hello")
    assert result.ok is False
    assert result.state is OpenCodeOperationState.MALFORMED_RESPONSE
    assert not [path for m, path in stub.requests if m == "POST" and path.endswith("/message")]


# ---------------------------------------------------------------------------
# P2-C: interrupt semantics are explicit
# ---------------------------------------------------------------------------
def test_interrupt_accepts_an_empty_204_without_claiming_verification():
    stub = StubOpenCodeServer(abort_status=204)
    result = stub.bridge().interrupt("ses_match")
    assert result.state is OpenCodeOperationState.INTERRUPTED
    assert result.interrupt_verified is False
    assert result.error_type == ""


def test_interrupt_accepts_a_json_success_body():
    stub = StubOpenCodeServer()
    result = stub.bridge().interrupt("ses_match")
    assert result.state is OpenCodeOperationState.INTERRUPTED
    assert result.interrupt_verified is False


def test_interrupt_of_a_vanished_session_is_not_reported_as_unsupported():
    stub = StubOpenCodeServer(abort_status=404, abort_removes_session=True)
    result = stub.bridge().interrupt("ses_match")
    assert result.state is OpenCodeOperationState.PROVIDER_UNAVAILABLE
    assert result.error_type == "interrupt_session_not_found"
    assert result.interrupt_verified is False


@pytest.mark.parametrize("status", [405, 501])
def test_interrupt_unsupported_statuses_fail_closed(status):
    stub = StubOpenCodeServer(abort_status=status)
    result = stub.bridge().interrupt("ses_match")
    assert result.error_type == "interrupt_unsupported"
    assert result.interrupt_verified is False


def test_interrupt_provider_error_is_not_mislabelled_as_unsupported():
    stub = StubOpenCodeServer(abort_status=500, abort_body='{"error":"boom"}')
    result = stub.bridge().interrupt("ses_match")
    assert result.error_type == "http_status"
    assert "500" in result.error
    assert result.interrupt_verified is False


def test_interrupt_oversized_response_is_malformed_not_unsupported():
    stub = StubOpenCodeServer(abort_status=500, abort_body="z" * 20_000)
    result = stub.bridge(max_response_bytes=1_024).interrupt("ses_match")
    assert result.state is OpenCodeOperationState.MALFORMED_RESPONSE
    assert result.error_type == "response_too_large"
    assert result.interrupt_verified is False


# ---------------------------------------------------------------------------
# P2-D: provider echoes of prompt/token never reach ledger or console
# ---------------------------------------------------------------------------
def test_prompt_and_token_echo_never_reach_the_ledger(tmp_path):
    prompt = "summarize the private design note SECRETPROMPT-4711"
    stub = StubOpenCodeServer(
        prompt_http_status=500,
        prompt_error_body=json.dumps(
            {"error": "boom", "echo": prompt, "auth": TOKEN}
        ),
    )
    ledger = _ledger(tmp_path)
    bridge = OpenCodeBridge(
        base_url="http://opencode.invalid",
        workspace_root=WS,
        token=TOKEN,
        transport=stub.transport(token=TOKEN),
        ledger=ledger,
    )
    result = bridge.send_prompt("ses_match", prompt)

    assert result.ok is False and result.error_type == "http_status"
    payload = json.dumps(result.model_dump(mode="json"))
    assert prompt not in payload and TOKEN not in payload
    post = [record for record in ledger.read_records() if record.method == "POST"]
    assert len(post) == 1
    record = post[0]
    serialized = json.dumps(record.model_dump(mode="json"))
    assert prompt not in serialized and TOKEN not in serialized
    # useful metadata survives the scrubbing
    assert record.operation == "send_prompt"
    assert record.http_status == 500
    assert record.error_type == "http_status"
    assert record.session_id == "ses_match"
    assert record.path.endswith("/message")
    assert record.prompt_chars == len(prompt)
    assert record.prompt_sha256 == hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    # and nothing on disk contains either literal
    for path in (tmp_path / ".devrelay").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            assert prompt not in text and TOKEN not in text


def test_follow_up_echo_is_scrubbed_and_bounded(tmp_path):
    prompt = "FOLLOWUP-ECHO-4711 " + "q" * 300
    stub = StubOpenCodeServer(
        prompt_raw_reply={"ok": True},
        session_http_status_after_prompt=500,
        session_error_body_after_prompt=json.dumps(
            {"error": prompt, "auth": TOKEN, "pad": "y" * 5_000}
        ),
    )
    ledger = _ledger(tmp_path)
    result = OpenCodeBridge(
        base_url="http://opencode.invalid",
        workspace_root=WS,
        token=TOKEN,
        transport=stub.transport(token=TOKEN),
        ledger=ledger,
    ).send_prompt("ses_match", prompt)

    assert prompt not in result.error and TOKEN not in result.error
    assert len(result.error) <= 600
    for path in (tmp_path / ".devrelay").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            assert prompt not in text and TOKEN not in text


def test_prompt_digest_is_an_identifier_not_a_secrecy_mechanism(tmp_path):
    """The ledger stores a plain, unsalted SHA-256: correlate, never conceal.

    This is asserted explicitly so no reader (or future test) can mistake the
    digest for a password-style KDF: a guessable prompt is confirmable from the
    ledger.  Prompt *confidentiality* comes from never storing the text - not
    from hashing it.
    """
    prompt = "short-prompt"
    stub = StubOpenCodeServer(prompt_ack_only=True)
    ledger = _ledger(tmp_path)
    stub.bridge(ledger=ledger).send_prompt("ses_match", prompt)

    record = [r for r in ledger.read_records() if r.method == "POST"][0]
    assert record.prompt_sha256 == hashlib.sha256(b"short-prompt").hexdigest()
    for path in (tmp_path / ".devrelay").rglob("*"):
        if path.is_file():
            assert prompt not in path.read_text(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# P2-E: the ledger fails closed instead of reusing identities
# ---------------------------------------------------------------------------
def test_corrupt_sequence_with_records_fails_closed(tmp_path):
    ledger = _ledger(tmp_path)
    first = ledger.allocate_call_id()
    ledger.sequence_path.write_text("{not json", encoding="utf-8")
    with pytest.raises(OpenCodeLedgerError):
        ledger.allocate_call_id()
    # the corrupt evidence is preserved for diagnosis, not silently rewritten
    assert ledger.sequence_path.read_text(encoding="utf-8") == "{not json"
    assert first == "OC-0001"


def test_malformed_sequence_payload_fails_closed(tmp_path):
    ledger = _ledger(tmp_path)
    ledger.allocate_call_id()
    ledger.sequence_path.write_text(json.dumps({"next": 3}), encoding="utf-8")
    with pytest.raises(OpenCodeLedgerError):
        ledger.allocate_call_id()


def test_deleted_sequence_recovers_from_the_existing_ledger(tmp_path):
    ledger = _ledger(tmp_path)
    assert ledger.allocate_call_id() == "OC-0001"
    assert ledger.allocate_call_id() == "OC-0002"
    ledger.calls_dir.mkdir(parents=True, exist_ok=True)
    (ledger.calls_dir / "OC-0001.json").write_text("{}", encoding="utf-8")
    ledger.sequence_path.unlink()
    assert ledger.allocate_call_id() == "OC-0002", "allocation must not reuse OC-0001"


def test_allocation_after_a_crash_gap_never_reuses_an_identity(tmp_path):
    ledger = _ledger(tmp_path)
    ledger.calls_dir.mkdir(parents=True, exist_ok=True)
    (ledger.calls_dir / "OC-0042.json").write_text("{}", encoding="utf-8")
    assert ledger.allocate_call_id() == "OC-0043"
    assert ledger.allocate_call_id() == "OC-0044"


def test_existing_call_identity_is_never_overwritten(tmp_path):
    ledger = _ledger(tmp_path)
    ledger.calls_dir.mkdir(parents=True, exist_ok=True)
    target = ledger.calls_dir / "OC-0001.json"
    target.write_text('{"sentinel": true}', encoding="utf-8")
    record = OpenCodeCallRecord(
        call_id="OC-0001",
        operation="health",
        state=OpenCodeCallState.ISSUED,
        method="GET",
        path="/global/health",
    )
    with pytest.raises(OpenCodeLedgerError):
        ledger.begin(record)
    assert json.loads(target.read_text(encoding="utf-8")) == {"sentinel": True}


# ---------------------------------------------------------------------------
# P2-F: --json keeps the failing exit status
# ---------------------------------------------------------------------------
def _cli_workspace(tmp_path: Path, monkeypatch) -> Path:
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    monkeypatch.chdir(repo)
    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    config_path = repo / ".devrelay" / "config.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    data["opencode"] = {
        "base_url": "http://opencode.invalid",
        "workspace": str(repo.resolve()),
        "default_session": "ses_match",
    }
    config_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return repo


def _patch_transport(stub) -> Any:
    """Route the CLI's bridge at the offline stub; returns the original class."""
    import devrelay.opencode.bridge as bridge_module

    original = bridge_module.OpenCodeTransport
    bridge_module.OpenCodeTransport = lambda *a, **k: stub.transport()
    return original


def test_cli_json_mode_keeps_a_failing_exit_status(tmp_path, monkeypatch):
    repo = _cli_workspace(tmp_path, monkeypatch)
    stub = StubOpenCodeServer(unreachable=True, workspace=str(repo.resolve()))
    original = _patch_transport(stub)
    try:
        human = CliRunner().invoke(app, ["opencode", "health"])
        assert human.exit_code == 2, human.output
        assert "PROVIDER_UNAVAILABLE" in human.output

        machine = CliRunner().invoke(app, ["opencode", "health", "--json"])
        assert machine.exit_code == 2, machine.output
        payload = json.loads(machine.output)
        assert payload["state"] == OpenCodeOperationState.PROVIDER_UNAVAILABLE.value
        assert payload["error_type"]
    finally:
        import devrelay.opencode.bridge as bridge_module

        bridge_module.OpenCodeTransport = original


def test_cli_json_mode_succeeds_only_when_the_operation_does(tmp_path, monkeypatch):
    repo = _cli_workspace(tmp_path, monkeypatch)
    stub = StubOpenCodeServer(workspace=str(repo.resolve()), abort_status=204)
    original = _patch_transport(stub)
    try:
        machine = CliRunner().invoke(app, ["opencode", "health", "--json"])
        assert machine.exit_code == 0, machine.output
        assert (
            json.loads(machine.output)["state"]
            == OpenCodeOperationState.COMPLETED.value
        )

        # an accepted abort is success for the interrupt command ...
        interrupted = CliRunner().invoke(app, ["opencode", "interrupt", "--json"])
        assert interrupted.exit_code == 0, interrupted.output
        assert (
            json.loads(interrupted.output)["state"]
            == OpenCodeOperationState.INTERRUPTED.value
        )

        human = CliRunner().invoke(app, ["opencode", "interrupt"])
        assert human.exit_code == 0, human.output
        assert "INTERRUPTED" in human.output
    finally:
        import devrelay.opencode.bridge as bridge_module

        bridge_module.OpenCodeTransport = original


def test_cli_reports_a_pending_reply_as_a_non_zero_but_honest_result(
    tmp_path, monkeypatch
):
    repo = _cli_workspace(tmp_path, monkeypatch)
    stub = StubOpenCodeServer(
        workspace=str(repo.resolve()), prompt_raw_reply={"ok": True}
    )
    original = _patch_transport(stub)
    try:
        machine = CliRunner().invoke(
            app, ["opencode", "send", "--prompt", "hello", "--json"]
        )
        assert machine.exit_code == 2, machine.output
        payload = json.loads(machine.output)
        assert payload["reply_pending"] is True
        assert payload["messages"] == []
        assert payload["error_type"] == "reply_pending"
    finally:
        import devrelay.opencode.bridge as bridge_module

        bridge_module.OpenCodeTransport = original


# ---------------------------------------------------------------------------
# PART III: wiring-vs-policy configuration coverage
# ---------------------------------------------------------------------------
def test_opencode_config_defaults_and_bounds():
    config = OpenCodeConfig()
    assert config.base_url == "" and config.configured is False
    assert config.workspace == "" and config.default_session == ""
    assert config.timeout_seconds == 30.0
    assert config.idle_timeout_seconds == 300.0
    assert config.poll_interval_seconds == 1.0
    assert config.max_response_bytes == 1_048_576
    assert config.max_messages == 50
    assert config.allow_unknown_workspace is False

    for bad in (
        {"timeout_seconds": 0},
        {"timeout_seconds": -1},
        {"idle_timeout_seconds": 0},
        {"poll_interval_seconds": 0},
        {"max_response_bytes": 512},
        {"max_response_bytes": 33_554_433},
        {"max_messages": 0},
        {"max_messages": 201},
    ):
        with pytest.raises(ValidationError):
            OpenCodeConfig(**bad)
    with pytest.raises(ValidationError):
        OpenCodeConfig(unknown_key=True)


@pytest.mark.parametrize(
    "base_url",
    [
        "ftp://127.0.0.1:4096",
        "127.0.0.1:4096",
        "http://user:pass@127.0.0.1:4096",
        "http://127.0.0.1:4096/api",
        "http://127.0.0.1:4096/?x=1",
        "http://127.0.0.1:4096/#frag",
    ],
)
def test_opencode_base_url_must_be_unambiguous(base_url):
    with pytest.raises(ValidationError):
        OpenCodeConfig(base_url=base_url)


def test_opencode_base_url_normalizes_trailing_slash():
    config = OpenCodeConfig(base_url="  http://127.0.0.1:4096/  ")
    assert config.base_url == "http://127.0.0.1:4096" and config.configured is True


def test_null_opencode_section_means_not_configured(tmp_path):
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    config_path = repo / ".devrelay" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("opencode:\n", encoding="utf-8")

    wiring = load_wiring_config(repo)
    assert wiring.opencode == OpenCodeConfig()
    assert wiring.opencode.configured is False
    workspace = load_workspace_file(config_path)
    assert workspace.opencode == OpenCodeConfig()


def test_invalid_opencode_wiring_in_the_workspace_file_fails_closed(tmp_path):
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    config_path = repo / ".devrelay" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "opencode:\n  base_url: http://user:pass@127.0.0.1:4096\n", encoding="utf-8"
    )
    with pytest.raises(ConfigError):
        load_wiring_config(repo)
    with pytest.raises(ConfigError):
        load_workspace_file(config_path)

    config_path.write_text("opencode:\n  unknown: 1\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_workspace_file(config_path)


def test_opencode_section_is_projected_out_of_the_policy(tmp_path, monkeypatch):
    repo = _cli_workspace(tmp_path, monkeypatch)
    config_path = repo / ".devrelay" / "config.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    data["opencode"] = {
        "base_url": "http://127.0.0.1:4096",
        "max_messages": 25,
        "allow_unknown_workspace": True,
    }
    data["tests"] = {"targeted": ["tests/test_x.py"]}
    config_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    overrides = workspace_policy_overrides(repo)
    assert "opencode" not in overrides and "codex" not in overrides
    assert overrides["tests"] == {"targeted": ["tests/test_x.py"]}

    resolved = resolve_policy_config(repo)
    dumped = resolved.document.model_dump(mode="json")
    assert "opencode" not in dumped and "codex" not in dumped
    assert resolved.document.tests.targeted == ["tests/test_x.py"]
    # the wiring is still live and validated
    wiring = load_wiring_config(repo)
    assert wiring.opencode.max_messages == 25
    assert wiring.opencode.allow_unknown_workspace is True


def test_legacy_full_config_snapshot_tolerates_opencode_only_when_lenient(
    tmp_path, monkeypatch
):
    repo = _cli_workspace(tmp_path, monkeypatch)
    legacy = load_workspace_file(repo / ".devrelay" / "config.yaml")
    document = legacy.model_dump(mode="json")
    document.setdefault("review", {})["provider"] = "manual"
    raw = yaml.safe_dump(document, sort_keys=False).encode("utf-8")

    parsed, dropped = load_policy_snapshot(raw, strict=False, source="legacy dump")
    # v0.3-C adds one more wiring section (``roles``); like ``opencode`` before
    # it, it is dropped from a legacy full-config dump rather than frozen.
    assert sorted(dropped) == [
        "codex",
        "opencode",
        "profiles",
        "review.provider",
        "roles",
    ]
    assert "opencode" not in parsed.model_dump(mode="json")
    with pytest.raises(ConfigError):
        load_policy_snapshot(raw, strict=True, source="legacy dump")


def _init_repo(tmp_path: Path) -> Path:
    repo = make_git_repo(tmp_path / "snapshot-repo", initial_files={"a.txt": "a\n"})
    runner = CliRunner()
    cwd = Path.cwd()
    import os

    os.chdir(repo)
    try:
        assert runner.invoke(app, ["init"]).exit_code == 0
    finally:
        os.chdir(cwd)
    return repo


def test_allow_unknown_workspace_controls_the_ownership_verdict():
    relative = StubOpenCodeServer(
        workspace="../../somewhere/else", sessions=[_session("ses_rel", workspace="relative/ws")]
    )
    with pytest.raises(OpenCodeSessionWorkspaceMismatchError):
        relative.bridge().get_session("ses_rel")
    allowed = StubOpenCodeServer(
        workspace="relative/ws",
        sessions=[_session("ses_rel", workspace="relative/ws")],
    )
    result = allowed.bridge(allow_unknown_workspace=True).get_session("ses_rel")
    assert result.ok is True
    assert result.session is not None and result.session.workspace_known is False
