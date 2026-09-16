"""v0.3-A OpenCode session bridge: offline acceptance coverage.

Every scenario runs against the deterministic in-memory stub server
(`tests/opencode_stub.py`) — no real OpenCode instance, no network, no model.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from devrelay.cli import app
from devrelay.errors import (
    OpenCodeConfigError,
    OpenCodeSessionNotFoundError,
    OpenCodeSessionWorkspaceMismatchError,
)
from devrelay.opencode import OpenCodeBridge
from devrelay.opencode.accounting import FilesystemOpenCodeLedger, NullOpenCodeLedger
from devrelay.opencode.models import (
    OpenCodeCallState,
    OpenCodeOperationState,
    OpenCodeSessionState,
)

from opencode_stub import FAKE_SECRET, DEFAULT_WORKSPACE, StubOpenCodeServer, _message, _session

WS = DEFAULT_WORKSPACE


# ---------------------------------------------------------------------------
# health
# ---------------------------------------------------------------------------
def test_health_reports_capabilities():
    stub = StubOpenCodeServer(capabilities=["list_sessions", "messages", "interrupt"])
    result = stub.bridge().health()
    assert result.state is OpenCodeOperationState.COMPLETED
    assert result.health is not None and result.health.healthy
    assert result.health.version == "stub-9.9.9"
    assert result.health.supports("interrupt")
    assert result.request_count == 1 and len(result.call_ids) == 1


def test_health_fails_closed_when_unreachable():
    result = StubOpenCodeServer(unreachable=True).bridge().health()
    assert result.state is OpenCodeOperationState.PROVIDER_UNAVAILABLE
    assert result.error_type == "transport"


def test_health_fails_closed_on_timeout():
    result = StubOpenCodeServer(timeout=True).bridge().health()
    assert result.state is OpenCodeOperationState.TIMED_OUT
    assert result.error_type == "timeout"


def test_health_fails_closed_on_malformed_response():
    result = StubOpenCodeServer(malformed="invalid_json").bridge().health()
    assert result.state is OpenCodeOperationState.MALFORMED_RESPONSE
    assert result.error_type == "invalid_json"


# ---------------------------------------------------------------------------
# session discovery / selection
# ---------------------------------------------------------------------------
def test_list_sessions_filters_other_workspaces():
    stub = StubOpenCodeServer(
        sessions=[
            _session("ses_match", workspace=WS, title="mine"),
            _session("ses_other", workspace="/somewhere/else", title="theirs"),
        ]
    )
    result = stub.bridge().list_sessions()
    assert result.state is OpenCodeOperationState.COMPLETED
    assert [s.session_id for s in result.sessions] == ["ses_match"]
    assert result.sessions[0].workspace_match

    all_result = stub.bridge().list_sessions(include_other_workspaces=True)
    assert [s.session_id for s in all_result.sessions] == ["ses_match", "ses_other"]
    assert all_result.sessions[1].workspace_match is False


def test_get_session_reports_state():
    stub = StubOpenCodeServer(sessions=[_session("ses_a", state="busy")])
    result = stub.bridge().get_session("ses_a")
    assert result.ok and result.session is not None
    assert result.session.state is OpenCodeSessionState.BUSY
    assert result.session.workspace_match is True


def test_unknown_session_is_a_hard_failure():
    with pytest.raises(OpenCodeSessionNotFoundError):
        StubOpenCodeServer().bridge().get_session("ses_missing")


def test_workspace_mismatch_is_a_hard_failure():
    stub = StubOpenCodeServer(sessions=[_session("ses_other", workspace="/elsewhere")])
    with pytest.raises(OpenCodeSessionWorkspaceMismatchError):
        stub.bridge().get_session("ses_other")


def test_workspace_unknown_fails_closed_unless_explicitly_allowed():
    stub = StubOpenCodeServer(sessions=[_session("ses_a", include_workspace=False)])
    with pytest.raises(OpenCodeSessionWorkspaceMismatchError):
        stub.bridge().get_session("ses_a")
    allowed = stub.bridge(allow_unknown_workspace=True).get_session("ses_a")
    assert allowed.ok and allowed.session is not None
    assert allowed.session.workspace_known is False


def test_session_id_is_required_and_never_guessed():
    with pytest.raises(OpenCodeConfigError):
        StubOpenCodeServer().bridge().read_messages("")


# ---------------------------------------------------------------------------
# message reading + cursor semantics
# ---------------------------------------------------------------------------
def test_read_messages_window():
    stub = StubOpenCodeServer()
    result = stub.bridge().read_messages("ses_match")
    assert result.ok and result.page is not None
    assert [m.message_id for m in result.messages] == ["msg_01", "msg_02"]
    assert result.messages[1].role == "assistant"
    assert result.messages[1].text == "hi there"
    assert result.page.next_cursor == "msg_02"
    assert result.page.cursor_unknown is False and result.page.replayed is False


def test_read_messages_cursor_returns_only_new_messages():
    stub = StubOpenCodeServer()
    stub.messages.append(_message("msg_03", "assistant", "third"))
    result = stub.bridge().read_messages("ses_match", cursor="msg_02")
    assert [m.message_id for m in result.messages] == ["msg_03"]
    assert result.page.next_cursor == "msg_03"


def test_read_messages_replayed_cursor_is_reported_not_duplicated():
    stub = StubOpenCodeServer()
    result = stub.bridge().read_messages("ses_match", cursor="msg_02")
    assert result.page.replayed is True
    assert result.messages == []
    assert result.page.next_cursor == "msg_02"


def test_read_messages_unknown_cursor_is_flagged():
    stub = StubOpenCodeServer()
    result = stub.bridge().read_messages("ses_match", cursor="msg_gone")
    assert result.page.cursor_unknown is True
    assert [m.message_id for m in result.messages] == ["msg_01", "msg_02"]


def test_read_messages_malformed_payload_fails_closed():
    stub = StubOpenCodeServer(malformed="messages_not_array")
    result = stub.bridge().read_messages("ses_match")
    assert result.state is OpenCodeOperationState.MALFORMED_RESPONSE


# ---------------------------------------------------------------------------
# one prompt submission
# ---------------------------------------------------------------------------
def test_send_prompt_success_returns_normalized_reply():
    stub = StubOpenCodeServer()
    result = stub.bridge().send_prompt("ses_match", "please fix the widget")
    assert result.ok
    assert len(result.messages) == 1
    reply = result.messages[0]
    assert reply.role == "assistant" and "please fix the widget" in reply.text
    # every issued request is accounted for: ownership probe + pre-submission
    # boundary read (session + messages) + the prompt submission itself
    assert result.request_count == 4
    assert len(result.call_ids) == 4
    assert result.reply_boundary == "msg_02"
    assert stub.prompts[0]["parts"][0]["text"] == "please fix the widget"


def test_send_prompt_agent_and_model_selection_are_forwarded():
    stub = StubOpenCodeServer()
    stub.bridge().send_prompt("ses_match", "hi", agent="build", model="glm-4.6")
    assert stub.prompts[0]["agent"] == "build"
    assert stub.prompts[0]["model"] == "glm-4.6"


def test_send_prompt_ack_only_server_is_followed_by_one_read():
    stub = StubOpenCodeServer(prompt_ack_only=True)
    result = stub.bridge().send_prompt("ses_match", "hello")
    assert result.ok
    assert result.messages and result.messages[-1].role == "assistant"
    # the write + the explicit follow-up read are both accounted for
    assert result.request_count >= 2


def test_send_prompt_provider_error_is_sanitized():
    stub = StubOpenCodeServer(
        http_status=500, error_body=json.dumps({"error": f"boom {FAKE_SECRET}"})
    )
    result = stub.bridge().send_prompt("ses_match", "hello")
    assert result.state is OpenCodeOperationState.PROVIDER_UNAVAILABLE
    assert result.error_type == "http_status"
    assert FAKE_SECRET not in result.error


def test_send_prompt_requires_non_empty_prompt():
    with pytest.raises(OpenCodeConfigError):
        StubOpenCodeServer().bridge().send_prompt("ses_match", "   ")


# ---------------------------------------------------------------------------
# bounded idle wait
# ---------------------------------------------------------------------------
def test_wait_idle_completes_when_session_becomes_idle():
    stub = StubOpenCodeServer(
        sessions=[_session("ses_a", state="busy")],
        state_sequence=["busy", "busy", "idle"],
    )
    result = stub.bridge().wait_idle("ses_a", timeout=30)
    assert result.state is OpenCodeOperationState.COMPLETED
    assert result.session is not None and result.session.state is OpenCodeSessionState.IDLE
    assert result.request_count >= 3  # ownership probe + polls, all accounted


def test_wait_idle_times_out_without_retrying():
    stub = StubOpenCodeServer(sessions=[_session("ses_a", state="busy")])
    result = stub.bridge(idle_timeout_seconds=0.05).wait_idle("ses_a", timeout=0.05)
    assert result.state is OpenCodeOperationState.TIMED_OUT
    assert result.error_type == "idle_timeout"
    assert result.session is not None and result.session.state is OpenCodeSessionState.BUSY
    assert result.request_count >= 1


def test_wait_idle_returns_terminal_error_state():
    stub = StubOpenCodeServer(sessions=[_session("ses_a", state="error")])
    result = stub.bridge().wait_idle("ses_a", timeout=5)
    assert result.state is OpenCodeOperationState.COMPLETED
    assert result.session is not None and result.session.state is OpenCodeSessionState.ERROR


# ---------------------------------------------------------------------------
# interrupt / cancel
# ---------------------------------------------------------------------------
def test_interrupt_is_reported_when_supported():
    stub = StubOpenCodeServer(sessions=[_session("ses_a", state="busy")])
    result = stub.bridge().interrupt("ses_a")
    assert result.state is OpenCodeOperationState.INTERRUPTED
    assert stub.sessions[0]["state"] == "idle"


def test_interrupt_fails_closed_when_unsupported():
    stub = StubOpenCodeServer(abort_supported=False, sessions=[_session("ses_a")])
    result = stub.bridge().interrupt("ses_a")
    assert result.state is OpenCodeOperationState.PROVIDER_UNAVAILABLE
    assert result.error_type == "interrupt_unsupported"
    assert result.operation == "interrupt"


# ---------------------------------------------------------------------------
# accounting
# ---------------------------------------------------------------------------
def test_call_accounting_is_explicit_and_durable(tmp_path):
    stub = StubOpenCodeServer()
    ledger = FilesystemOpenCodeLedger(tmp_path / ".devrelay")
    bridge = stub.bridge(ledger=ledger)
    bridge.health()
    bridge.send_prompt("ses_match", "hello")
    bridge.read_messages("ses_match")

    records = ledger.records()
    assert len(records) >= 3
    assert len({record.call_id for record in records}) == len(records)
    assert all(record.external_request_count == 1 for record in records)
    assert all(record.state is OpenCodeCallState.COMPLETED for record in records)
    # the prompt text itself is never persisted - only its hash and length
    prompts = [
        record
        for record in records
        if record.operation == "send_prompt" and record.method == "POST"
    ]
    assert prompts and prompts[0].prompt_sha256 and prompts[0].prompt_chars == 5
    persisted = (
        tmp_path
        / ".devrelay"
        / "opencode"
        / "calls"
        / f"{prompts[0].call_id}.json"
    ).read_text(encoding="utf-8")
    assert "hello" not in persisted
    assert FAKE_SECRET not in persisted
    # sequence is durable and monotonic across a fresh ledger instance
    again = FilesystemOpenCodeLedger(tmp_path / ".devrelay")
    assert again.allocate_call_id() != records[0].call_id


def test_no_hidden_retries_on_failure():
    stub = StubOpenCodeServer(unreachable=True)
    ledger = NullOpenCodeLedger()
    result = stub.bridge(ledger=ledger).send_prompt("ses_match", "hello")
    assert result.state is OpenCodeOperationState.PROVIDER_UNAVAILABLE
    # exactly one issued request: the ownership probe is the only failure point
    assert result.request_count == 1
    assert len(ledger.records()) == 1


def test_oversized_response_fails_closed():
    stub = StubOpenCodeServer(oversize=True)
    result = stub.bridge(max_response_bytes=1024).health()
    assert result.state is OpenCodeOperationState.MALFORMED_RESPONSE
    assert result.error_type in ("response_too_large", "invalid_json")


def test_bridge_requires_an_explicit_endpoint():
    with pytest.raises(OpenCodeConfigError):
        OpenCodeBridge(base_url="", workspace_root=WS)


# ---------------------------------------------------------------------------
# CLI surface (thin wrappers; no OpenCode logic in the CLI)
# ---------------------------------------------------------------------------
def _cli_workspace(tmp_path: Path, monkeypatch) -> Path:
    import yaml

    from helpers import make_git_repo

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


def test_cli_opencode_health_and_sessions(tmp_path, monkeypatch):
    import devrelay.opencode.bridge as bridge_module

    repo = _cli_workspace(tmp_path, monkeypatch)
    stub = StubOpenCodeServer(workspace=str(repo.resolve()))
    original = bridge_module.OpenCodeTransport
    bridge_module.OpenCodeTransport = lambda *a, **k: stub.transport()
    try:
        runner = CliRunner()
        health = runner.invoke(app, ["opencode", "health"])
        assert health.exit_code == 0, health.output
        assert "health" in health.output and "stub-9.9.9" in health.output

        sessions = runner.invoke(app, ["opencode", "sessions"])
        assert sessions.exit_code == 0, sessions.output
        assert "ses_match" in sessions.output

        calls = runner.invoke(app, ["opencode", "calls"])
        assert calls.exit_code == 0, calls.output
        assert "health" in calls.output
    finally:
        bridge_module.OpenCodeTransport = original


def test_cli_opencode_requires_configuration(tmp_path, monkeypatch):
    from helpers import make_git_repo

    repo = make_git_repo(tmp_path / "repo2", initial_files={"a.txt": "a\n"})
    monkeypatch.chdir(repo)
    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    result = runner.invoke(app, ["opencode", "health"])
    assert result.exit_code == 1
    assert "base_url" in result.output

def test_token_never_reaches_durable_artifacts(tmp_path):
    """The bearer token lives in the request header only - never on disk."""
    import httpx

    token = "oc-secret-TOKEN-must-not-persist"
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization", "")
        return StubOpenCodeServer._json({"healthy": True, "version": "stub"})

    stub = StubOpenCodeServer()
    ledger = FilesystemOpenCodeLedger(tmp_path / ".devrelay")
    transport = stub.transport(
        token=token,
        client=httpx.Client(
            transport=httpx.MockTransport(handler), base_url="http://opencode.invalid"
        ),
    )
    bridge = OpenCodeBridge(
        base_url="http://opencode.invalid",
        workspace_root=WS,
        token=token,
        ledger=ledger,
        transport=transport,
    )
    assert bridge.health().ok
    assert seen["auth"] == f"Bearer {token}"          # sent to the server
    calls_dir = tmp_path / ".devrelay" / "opencode"
    for path in calls_dir.rglob("*"):
        if path.is_file():
            assert token not in path.read_text(encoding="utf-8", errors="replace")
