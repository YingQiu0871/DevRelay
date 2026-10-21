"""v0.3-A real-protocol regression suite (A33 remediation).

Every fixture here is derived from the **installed OpenCode 1.18.11 OpenAPI
document** (`/doc`, preserved as A33 evidence), not from an invented shape:

* synchronous submission = ``POST /session/{id}/message`` returning
  ``{info: AssistantMessage, parts: Part[]}`` (both required);
* ``AssistantMessage``: ``id`` (``^msg``), ``sessionID`` (``^ses``),
  ``role`` enum ``["assistant"]``, ``time.created``;
* ``TextPart``: required ``id``, ``sessionID``, ``messageID``, ``type``,
  ``text``; request ``TextPartInput``: required ``type`` + ``text`` only;
* model override = ``{providerID, modelID}`` (both required);
* runtime state = ``GET /session/status`` (``SessionStatus`` = idle | busy |
  retry); an **idle session is absent** from the map (verified against the real
  server), and the session object has **no** ``state``/``status`` field;
* an unmatched route (e.g. the nonexistent ``/session/{id}/prompt``) answers
  ``200 text/html`` with the SPA shell.

Offline throughout: the deterministic stub over ``httpx.MockTransport``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from typer.testing import CliRunner

from devrelay.cli import app
from devrelay.errors import OpenCodeConfigError
from devrelay.opencode.accounting import FilesystemOpenCodeLedger
from devrelay.opencode.bridge import OpenCodeBridge
from devrelay.opencode.models import (
    OpenCodeCallState,
    OpenCodeOperationState,
    OpenCodeSessionState,
)

from helpers import make_git_repo
from opencode_stub import DEFAULT_WORKSPACE, SPA_FALLBACK_HTML, StubOpenCodeServer, _session
from test_v03a_remediation import _Clock

WS = DEFAULT_WORKSPACE
SESSION_ID = "ses_match"
MESSAGE_PATH = f"/session/{SESSION_ID}/message"
OLD_PROMPT_PATH = f"/session/{SESSION_ID}/prompt"
REPLY_TEXT = "DEVRELAY_A33_OK"


# ---------------------------------------------------------------------------
# fixtures shaped exactly like the real OpenAPI contract
# ---------------------------------------------------------------------------
def real_text_part(
    message_id: str = "msg_assistant_new",
    text: str = REPLY_TEXT,
    *,
    session_id: str = SESSION_ID,
    part_id: str = "prt_1",
) -> dict[str, Any]:
    """A real ``TextPart`` (all five members required by the schema)."""
    return {
        "id": part_id,
        "sessionID": session_id,
        "messageID": message_id,
        "type": "text",
        "text": text,
    }


def real_assistant_message(
    message_id: str = "msg_assistant_new",
    text: str = REPLY_TEXT,
    *,
    session_id: str = SESSION_ID,
    role: str = "assistant",
) -> dict[str, Any]:
    """A real ``{info, parts}`` synchronous response body."""
    return {
        "info": {
            "id": message_id,
            "sessionID": session_id,
            "role": role,
            "time": {"created": 1_789_554_011_423},
        },
        "parts": [real_text_part(message_id, text, session_id=session_id)],
    }


def real_status(status_type: str, **extra: Any) -> dict[str, Any]:
    """A real ``SessionStatus`` entry (idle | busy | retry)."""
    return {"type": status_type, **extra}


def real_retry(attempt: int = 2, message: str = "rate limited", next_in: int = 5_000):
    return {
        "type": "retry",
        "attempt": attempt,
        "message": message,
        "next": next_in,
    }


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _ledger(tmp_path: Path) -> FilesystemOpenCodeLedger:
    return FilesystemOpenCodeLedger(tmp_path / ".devrelay")


def _records(tmp_path: Path):
    return _ledger(tmp_path).read_records()


def _idle_session():
    """A session object exactly like the real one: no state/status field."""
    return _session(SESSION_ID, workspace=WS)


def _bridge(tmp_path: Path, stub: StubOpenCodeServer, **kwargs: Any) -> OpenCodeBridge:
    return OpenCodeBridge(
        base_url="http://opencode.invalid",
        workspace_root=WS,
        transport=stub.transport(),
        ledger=_ledger(tmp_path),
        **kwargs,
    )


def _posts(stub: StubOpenCodeServer) -> list[str]:
    return [path for method, path in stub.requests if method == "POST"]


def _assert_settled(tmp_path: Path, result) -> None:
    records = _records(tmp_path)
    assert result.request_count == len(records)
    assert set(result.call_ids) == {r.call_id for r in records}
    assert not [r for r in records if r.state is OpenCodeCallState.ISSUED]
    assert all(r.completed_at for r in records)


# ---------------------------------------------------------------------------
# 1-3, 13-15: the real submission route, body, single POST and ledger
# ---------------------------------------------------------------------------
def test_submission_uses_the_real_message_route_exactly_once(tmp_path):
    stub = StubOpenCodeServer(sessions=[_idle_session()], prompt_reply=real_assistant_message())
    result = _bridge(tmp_path, stub).send_prompt(SESSION_ID, "hello")

    assert _posts(stub) == [MESSAGE_PATH], "exactly one POST, on the real route"
    # the nonexistent legacy route is never touched (not even as a fallback)
    assert not [p for _m, p in stub.requests if "prompt" in p]
    assert result.operation == "send_prompt"
    assert result.state is OpenCodeOperationState.COMPLETED
    _assert_settled(tmp_path, result)
    assert result.request_count == 4  # probe + boundary session + boundary list + POST


def test_minimum_request_body_is_parts_only(tmp_path):
    stub = StubOpenCodeServer(sessions=[_idle_session()], prompt_reply=real_assistant_message())
    _bridge(tmp_path, stub).send_prompt(SESSION_ID, "hello")

    assert stub.prompts[0] == {"parts": [{"type": "text", "text": "hello"}]}
    # TextPartInput allows no other required member and DevRelay adds none
    assert set(stub.prompts[0]["parts"][0]) == {"type", "text"}


def test_agent_is_forwarded_and_model_is_a_structured_identity(tmp_path):
    stub = StubOpenCodeServer(sessions=[_idle_session()], prompt_reply=real_assistant_message())
    _bridge(tmp_path, stub).send_prompt(
        SESSION_ID, "hello", agent="build", model="anthropic/claude-sonnet-4"
    )
    body = stub.prompts[0]
    assert body["agent"] == "build"
    assert body["model"] == {
        "providerID": "anthropic",
        "modelID": "claude-sonnet-4",
    }
    assert set(body["model"]) == {"providerID", "modelID"}


@pytest.mark.parametrize("bad_model", ["glm-4.6", "/model", "provider/", "  "])
def test_unmappable_model_override_fails_locally_before_any_request(tmp_path, bad_model):
    """Never guess a wire encoding: fail before the probe and the POST."""
    stub = StubOpenCodeServer(sessions=[_idle_session()])
    with pytest.raises(OpenCodeConfigError) as excinfo:
        _bridge(tmp_path, stub).send_prompt(SESSION_ID, "hello", model=bad_model)
    assert "providerID" in str(excinfo.value) or "provider" in str(excinfo.value)
    assert stub.requests == []
    assert _records(tmp_path) == []


# ---------------------------------------------------------------------------
# 4-6: real synchronous response normalization
# ---------------------------------------------------------------------------
def test_real_sync_response_normalizes_to_one_new_assistant_reply(tmp_path):
    stub = StubOpenCodeServer(sessions=[_idle_session()], prompt_reply=real_assistant_message())
    result = _bridge(tmp_path, stub).send_prompt(SESSION_ID, "hello")

    assert result.reply_pending is False
    assert result.submission_body == ""
    assert result.submission_contract == ""
    assert result.submission_status == 200
    assert len(result.messages) == 1, "exactly one newly correlated assistant reply"
    message = result.messages[0]
    assert message.message_id == "msg_assistant_new"
    assert message.role == "assistant"
    assert message.text == REPLY_TEXT
    # the raw wire object never escapes the provider package
    assert not hasattr(message, "info") and not hasattr(message, "sessionID")
    _assert_settled(tmp_path, result)


def test_real_sync_response_with_unknown_parts_stays_limited(tmp_path):
    reply = real_assistant_message()
    reply["parts"].append(
        {
            "id": "prt_2",
            "sessionID": SESSION_ID,
            "messageID": "msg_assistant_new",
            "type": "tool",
            "tool": "bash",
            "state": {"input": "rm -rf /"},
        }
    )
    stub = StubOpenCodeServer(sessions=[_idle_session()], prompt_reply=reply)
    result = _bridge(tmp_path, stub).send_prompt(SESSION_ID, "hello")

    message = result.messages[0]
    assert message.text == REPLY_TEXT
    assert [part.kind for part in message.parts] == ["text", "tool"]
    assert message.parts[1].name == "bash"
    assert "rm -rf" not in json.dumps(result.model_dump(mode="json"))


@pytest.mark.parametrize(
    "reply",
    [
        real_assistant_message(role="user"),
        {"info": {"id": "msg_x", "sessionID": SESSION_ID, "role": "assistant"}},
        {"info": "not-an-object", "parts": []},
        {"parts": [real_text_part()]},
    ],
)
def test_non_assistant_or_incomplete_response_is_not_a_reply(tmp_path, reply):
    """Fail closed: an unusable/incomplete body is never treated as the reply."""
    stub = StubOpenCodeServer(
        sessions=[_idle_session()], prompt_raw_reply=reply, prompt_content_type="application/json"
    )
    result = _bridge(tmp_path, stub).send_prompt(SESSION_ID, "hello")

    assert _posts(stub) == [MESSAGE_PATH]
    assert result.operation == "send_prompt"
    assert result.reply_pending is True
    assert result.messages == [] and result.page is None
    assert result.submission_uncertain is False, "a usable JSON 2xx body is acceptance"
    _assert_settled(tmp_path, result)


def test_ack_only_json_body_stays_accepted_but_pending(tmp_path):
    """A JSON 2xx without an inline reply is accepted, never 'definitely failed'."""
    stub = StubOpenCodeServer(
        sessions=[_idle_session()], prompt_raw_reply={"ok": True}
    )
    result = _bridge(tmp_path, stub).send_prompt(SESSION_ID, "hello")

    assert _posts(stub) == [MESSAGE_PATH]
    assert result.submission_uncertain is False
    assert result.reply_pending is True
    assert result.messages == []
    _assert_settled(tmp_path, result)


def test_json_endpoint_with_a_broken_body_is_accepted_not_uncertain(tmp_path):
    """`all invalid JSON 2xx definitely failed` is explicitly NOT the rule."""
    stub = StubOpenCodeServer(
        sessions=[_idle_session()],
        prompt_http_status=200,
        prompt_error_body="{not json",
        prompt_content_type="application/json",
    )
    result = _bridge(tmp_path, stub).send_prompt(SESSION_ID, "hello")

    assert _posts(stub) == [MESSAGE_PATH]
    assert result.submission_status == 200
    assert result.submission_body == "invalid_json"
    assert result.submission_contract == "json"
    assert result.submission_uncertain is False
    assert result.reply_pending is True
    _assert_settled(tmp_path, result)


# ---------------------------------------------------------------------------
# 7: the real SPA fallback observation -> submission uncertain
# ---------------------------------------------------------------------------
def test_html_200_fallback_is_submission_uncertain(tmp_path):
    stub = StubOpenCodeServer(sessions=[_idle_session()], prompt_html_fallback=True)
    result = _bridge(tmp_path, stub).send_prompt(SESSION_ID, "hello")

    assert _posts(stub) == [MESSAGE_PATH], "exactly one POST, no fallback, no retry"
    assert result.operation == "send_prompt"
    assert result.submission_attempted is True
    assert result.submission_status == 200
    assert result.submission_uncertain is True
    assert result.submission_contract == "unexpected_media_type:text/html"
    assert result.reply_pending is True
    assert result.messages == [] and result.page is None
    assert "unexpected" in result.error and "not credible" in result.error
    _assert_settled(tmp_path, result)
    post = [r for r in _records(tmp_path) if r.method == "POST"][0]
    assert post.http_status == 200
    assert post.response_media_type == "text/html"
    assert post.submission_uncertain is True


def test_html_200_fallback_never_substitutes_a_stale_reply(tmp_path):
    stub = StubOpenCodeServer(sessions=[_idle_session()], prompt_html_fallback=True)
    result = _bridge(tmp_path, stub).send_prompt(SESSION_ID, "hello")
    assert "hi there" not in json.dumps(result.model_dump(mode="json"))


def test_unknown_route_in_the_stub_matches_the_real_spa_behaviour():
    """The stub itself must model 200 text/html, not a 404."""
    stub = StubOpenCodeServer()
    response = stub.handler(
        __import__("httpx").Request("POST", "http://opencode.invalid" + OLD_PROMPT_PATH)
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.text == SPA_FALLBACK_HTML


# ---------------------------------------------------------------------------
# 8-12: real /session/status driven wait_idle
# ---------------------------------------------------------------------------
def test_wait_idle_status_idle_completes(tmp_path):
    stub = StubOpenCodeServer(
        sessions=[_idle_session()], status_map={SESSION_ID: real_status("idle")}
    )
    result = _bridge(tmp_path, stub).wait_idle(SESSION_ID, 5.0)

    assert result.state is OpenCodeOperationState.COMPLETED
    assert result.session is not None
    assert result.session.state is OpenCodeSessionState.IDLE
    assert result.request_count == 2  # ownership probe + status poll
    _assert_settled(tmp_path, result)


def test_wait_idle_busy_then_idle(tmp_path):
    stub = StubOpenCodeServer(
        sessions=[_idle_session()],
        status_sequence=[
            {SESSION_ID: real_status("busy")},
            {SESSION_ID: real_status("busy")},
            {SESSION_ID: real_status("idle")},
        ],
    )
    result = _bridge(tmp_path, stub, poll_interval_seconds=0.01).wait_idle(SESSION_ID, 5.0)

    assert result.state is OpenCodeOperationState.COMPLETED
    assert result.request_count == 4  # probe + 3 status polls
    assert result.status_detail == "busy"
    _assert_settled(tmp_path, result)


def test_wait_idle_retry_keeps_evidence_and_continues(tmp_path):
    stub = StubOpenCodeServer(
        sessions=[_idle_session()],
        status_sequence=[
            {SESSION_ID: real_retry(attempt=2, message="rate limited", next_in=5_000)},
            {SESSION_ID: real_status("idle")},
        ],
    )
    result = _bridge(tmp_path, stub, poll_interval_seconds=0.01).wait_idle(SESSION_ID, 5.0)

    assert result.state is OpenCodeOperationState.COMPLETED
    assert "retry attempt 2" in result.status_detail
    assert "rate limited" in result.status_detail
    _assert_settled(tmp_path, result)


def test_wait_idle_bounded_busy_timeout(tmp_path):
    # Drive the whole-operation deadline with a fake clock: a real 0.2 s budget
    # is tight enough that a slow ledger fsync can consume it before the first
    # status poll, making the "last observed status" assertion timing-dependent.
    clock = _Clock()
    stub = StubOpenCodeServer(
        sessions=[_idle_session()], status_map={SESSION_ID: real_status("busy")}
    )
    result = _bridge(
        tmp_path,
        stub,
        poll_interval_seconds=0.05,
        sleep=clock.sleep,
        monotonic=clock.monotonic,
    ).wait_idle(SESSION_ID, 0.2)

    assert result.state is OpenCodeOperationState.TIMED_OUT
    assert result.error_type == "idle_timeout"
    assert "last observed status: busy" in result.error
    assert result.status_detail == "busy"
    assert result.request_count == len(_records(tmp_path))
    assert result.request_count >= 2
    assert not [r for r in _records(tmp_path) if r.state is OpenCodeCallState.ISSUED]


def test_wait_idle_missing_entry_means_idle(tmp_path):
    """Verified 1.18.11 semantics: an idle session is absent from the map."""
    stub = StubOpenCodeServer(sessions=[_idle_session()], status_map={})
    result = _bridge(tmp_path, stub).wait_idle(SESSION_ID, 5.0)

    assert result.state is OpenCodeOperationState.COMPLETED
    assert result.session is not None and result.session.state is OpenCodeSessionState.IDLE
    assert result.request_count == 2


def test_wait_idle_target_absent_while_another_session_is_busy(tmp_path):
    stub = StubOpenCodeServer(
        sessions=[_idle_session()], status_map={"ses_other": real_status("busy")}
    )
    result = _bridge(tmp_path, stub).wait_idle(SESSION_ID, 5.0)

    assert result.state is OpenCodeOperationState.COMPLETED, "the target is idle"
    assert result.request_count == 2


@pytest.mark.parametrize(
    "payload",
    [
        [{"type": "busy"}],                      # not a map
        {SESSION_ID: "busy"},                    # entry is not an object
        {SESSION_ID: {"type": "weird"}},         # unknown status type
        {SESSION_ID: {}},                        # missing type
    ],
)
def test_wait_idle_malformed_status_fails_closed(tmp_path, payload):
    stub = StubOpenCodeServer(sessions=[_idle_session()], status_map=payload)
    result = _bridge(tmp_path, stub).wait_idle(SESSION_ID, 5.0)

    assert result.state is OpenCodeOperationState.MALFORMED_RESPONSE
    assert result.error_type.startswith("unexpected_shape") or result.error_type == ""
    assert result.error
    _assert_settled(tmp_path, result)


def test_wait_idle_does_not_poll_the_session_detail_for_state(tmp_path):
    """The nonexistent session state field must no longer be polled."""
    stub = StubOpenCodeServer(
        sessions=[_idle_session()],
        status_sequence=[{SESSION_ID: real_status("busy")}, {SESSION_ID: real_status("idle")}],
    )
    _bridge(tmp_path, stub, poll_interval_seconds=0.01).wait_idle(SESSION_ID, 5.0)

    session_gets = [p for m, p in stub.requests if m == "GET" and p == f"/session/{SESSION_ID}"]
    status_gets = [p for m, p in stub.requests if m == "GET" and p == "/session/status"]
    assert len(session_gets) == 1, "only the ownership probe reads the session detail"
    assert len(status_gets) == 2, "runtime state comes from /session/status"


# ---------------------------------------------------------------------------
# human/JSON truth for the unexpected-contract case
# ---------------------------------------------------------------------------
def test_human_output_reports_the_unexpected_contract(tmp_path, monkeypatch):
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    monkeypatch.chdir(repo)
    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    config_path = repo / ".devrelay" / "config.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    data["opencode"] = {
        "base_url": "http://opencode.invalid",
        "workspace": str(repo.resolve()),
        "default_session": SESSION_ID,
    }
    config_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    stub = StubOpenCodeServer(
        workspace=str(repo.resolve()),
        sessions=[_session(SESSION_ID, workspace=str(repo.resolve()))],
        prompt_html_fallback=True,
    )
    import devrelay.opencode.bridge as bridge_module

    original = bridge_module.OpenCodeTransport
    bridge_module.OpenCodeTransport = lambda *a, **k: stub.transport()
    try:
        human = runner.invoke(app, ["opencode", "send", "--prompt", "hello"])
        machine = runner.invoke(app, ["opencode", "send", "--prompt", "hello", "--json"])
    finally:
        bridge_module.OpenCodeTransport = original

    assert human.exit_code == 2, human.output
    assert "response contract was unexpected (text/html)" in human.output
    assert "do not resubmit automatically" in human.output
    assert "reply      pending" in human.output
    assert "hi there" not in human.output
    payload = json.loads(machine.output)
    assert machine.exit_code == 2
    assert payload["submission_uncertain"] is True
    assert payload["submission_status"] == 200
    assert payload["submission_contract"] == "unexpected_media_type:text/html"
    assert payload["messages"] == [] and payload["page"] is None
