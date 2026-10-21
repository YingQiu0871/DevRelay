"""v0.3-A third review blocker remediation: focused regression tests.

Two smoke blockers (plus the directly adjacent inconsistencies) are covered here,
and every test below fails against `6e0eb61` for the actual mechanism:

* P1   a POST read/write timeout is *submission-uncertain* (the prompt may already
       have been accepted) and is never presented as safely retryable, while a
       connect timeout/error stays a definite "not submitted" outcome;
* P2   a post-acceptance result never exposes the pre-submission message window,
       so `messages[-1]` can never look like an answer to the prompt just sent;
* adj. the malformed-follow-up page is cleared, a genuine HTTP rejection keeps its
       status as submission evidence, and human output tells the same truth as
       `--json`.

Everything is offline: the deterministic OpenCode stub over
`httpx.MockTransport` (per-route transport failures included), no network, no
model, no real OpenCode server.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import yaml
from typer.testing import CliRunner

from devrelay.cli import app
from devrelay.errors import ConfigError
from devrelay.opencode.accounting import FilesystemOpenCodeLedger
from devrelay.opencode.bridge import OpenCodeBridge
from devrelay.opencode.models import OpenCodeCallState, OpenCodeOperationState

from helpers import make_git_repo
from opencode_stub import DEFAULT_WORKSPACE, StubOpenCodeServer

WS = DEFAULT_WORKSPACE
#: The pre-submission assistant text the stub always starts with.
STALE_REPLY = "hi there"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _ledger(tmp_path: Path) -> FilesystemOpenCodeLedger:
    return FilesystemOpenCodeLedger(tmp_path / ".devrelay")


def _bridge(tmp_path: Path, stub: StubOpenCodeServer, **kwargs: Any) -> OpenCodeBridge:
    return OpenCodeBridge(
        base_url="http://opencode.invalid",
        workspace_root=WS,
        token=kwargs.pop("token", ""),
        transport=stub.transport(token=kwargs.pop("transport_token", "")),
        ledger=_ledger(tmp_path),
        **kwargs,
    )


def _records(tmp_path: Path):
    return _ledger(tmp_path).read_records()


def _post_count(stub: StubOpenCodeServer) -> int:
    """Model-submission POSTs only (the GET message list shares the route)."""
    return sum(
        1
        for method, path in stub.requests
        if method == "POST" and path.endswith("/message")
    )


def _message_reads(stub: StubOpenCodeServer) -> int:
    """Message *list* reads (GET on the shared route)."""
    return sum(
        1
        for method, path in stub.requests
        if method == "GET" and path.endswith("/message")
    )


def _assert_accounting_is_settled(tmp_path: Path, result) -> None:
    """Operation accounting == durable ledger accounting, nothing left ISSUED."""
    records = _records(tmp_path)
    assert result.request_count == len(records)
    assert set(result.call_ids) == {record.call_id for record in records}
    assert not [record for record in records if record.state is OpenCodeCallState.ISSUED]
    for record in records:
        assert record.completed_at, record.call_id


# ---------------------------------------------------------------------------
# P1: transport-failure classification
# ---------------------------------------------------------------------------
def test_transport_failure_classes_are_classified():
    """The semantic model: only mid-transfer failures are submission-uncertain."""
    from devrelay.opencode.transport import transport_failure

    not_submitted = [
        httpx.ConnectTimeout("x"),
        httpx.PoolTimeout("x"),
        httpx.ConnectError("x"),
        httpx.ProxyError("x"),
        httpx.UnsupportedProtocol("x"),
        httpx.LocalProtocolError("x"),
    ]
    uncertain = [
        httpx.ReadTimeout("x"),
        httpx.WriteTimeout("x"),
        httpx.ReadError("x"),
        httpx.WriteError("x"),
        httpx.RemoteProtocolError("x"),
    ]
    for exc in not_submitted:
        response = transport_failure(exc, error="e", duration_ms=1)
        assert response.submission_uncertain is False, type(exc).__name__
    for exc in uncertain:
        response = transport_failure(exc, error="e", duration_ms=1)
        assert response.submission_uncertain is True, type(exc).__name__
    # exact error types (no permissive "one of" assertions)
    expected = {
        httpx.ConnectTimeout: ("connect_timeout", OpenCodeCallState.TIMED_OUT),
        httpx.PoolTimeout: ("pool_timeout", OpenCodeCallState.TIMED_OUT),
        httpx.ConnectError: ("connect_error", OpenCodeCallState.PROVIDER_UNAVAILABLE),
        httpx.ReadTimeout: ("read_timeout", OpenCodeCallState.TIMED_OUT),
        httpx.WriteTimeout: ("write_timeout", OpenCodeCallState.TIMED_OUT),
        httpx.ReadError: ("read_error", OpenCodeCallState.PROVIDER_UNAVAILABLE),
    }
    for exc_type, (error_type, state) in expected.items():
        response = transport_failure(exc_type("x"), error="e", duration_ms=1)
        assert response.error_type == error_type
        assert response.state is state


@pytest.mark.parametrize("failure", ["read_timeout", "write_timeout"])
def test_post_timeout_is_submission_uncertain(tmp_path, failure):
    """Case A/B: the POST may already have been accepted - never safely retryable."""
    stub = StubOpenCodeServer(prompt_exception=failure)
    result = _bridge(tmp_path, stub).send_prompt("ses_match", "hello")

    assert _post_count(stub) == 1, "the POST is issued exactly once and never retried"
    assert result.operation == "send_prompt"
    assert result.state is OpenCodeOperationState.TIMED_OUT
    assert result.error_type == failure
    assert result.submission_attempted is True
    assert result.submission_uncertain is True
    assert result.submission_status is None
    assert result.reply_pending is True
    assert result.reply_boundary == "msg_02"
    assert result.messages == []
    assert result.page is None
    assert "may" in result.error and "resubmit" in result.error
    # exactly one bounded follow-up read was performed (it never resubmits)
    assert _message_reads(stub) == 2
    _assert_accounting_is_settled(tmp_path, result)
    assert result.request_count == 6
    post = [record for record in _records(tmp_path) if record.method == "POST"]
    assert len(post) == 1
    assert post[0].state is OpenCodeCallState.TIMED_OUT
    assert post[0].submission_uncertain is True


@pytest.mark.parametrize(
    "failure,expected_state",
    [
        ("connect_timeout", OpenCodeOperationState.TIMED_OUT),
        ("connect_error", OpenCodeOperationState.PROVIDER_UNAVAILABLE),
    ],
)
def test_post_connect_failure_is_definitely_not_submitted(
    tmp_path, failure, expected_state
):
    """Case C/D: nothing reached the server, so there is no pending submission."""
    stub = StubOpenCodeServer(prompt_exception=failure)
    result = _bridge(tmp_path, stub).send_prompt("ses_match", "hello")

    assert _post_count(stub) == 1, "no retry"
    assert result.operation == "send_prompt"
    assert result.state is expected_state
    assert result.error_type == failure
    assert result.submission_attempted is True
    assert result.submission_uncertain is False
    assert result.submission_status is None
    assert result.reply_pending is False
    assert result.messages == []
    assert result.page is None
    assert "not submitted" in result.error
    # no follow-up read that would imply acceptance
    assert _message_reads(stub) == 1
    _assert_accounting_is_settled(tmp_path, result)
    assert result.request_count == 4
    post = [record for record in _records(tmp_path) if record.method == "POST"]
    assert post[0].submission_uncertain is False


def test_later_reply_after_a_post_timeout_stays_flagged_uncertain(tmp_path):
    """A correlated reply is reported, but never as a confirmed submission."""
    stub = StubOpenCodeServer(
        prompt_exception="read_timeout",
        prompt_append={
            "info": {"id": "msg_03", "role": "assistant"},
            "parts": [{"type": "text", "text": "late reply"}],
        },
    )
    result = _bridge(tmp_path, stub).send_prompt("ses_match", "hello")

    assert _post_count(stub) == 1
    assert result.operation == "send_prompt"
    assert result.submission_uncertain is True
    assert result.reply_pending is False
    assert [message.message_id for message in result.messages] == ["msg_03"]
    assert STALE_REPLY not in json.dumps(result.model_dump(mode="json"))
    _assert_accounting_is_settled(tmp_path, result)


def test_non_post_read_timeout_is_not_a_submission_uncertainty(tmp_path):
    """Only a submission can be submission-uncertain."""
    stub = StubOpenCodeServer()
    stub.timeout = True  # every route raises httpx.ReadTimeout
    result = _bridge(tmp_path, stub).health()
    assert result.state is OpenCodeOperationState.TIMED_OUT
    assert result.error_type == "read_timeout"
    assert result.submission_attempted is False
    assert result.submission_uncertain is False
    _assert_accounting_is_settled(tmp_path, result)


# ---------------------------------------------------------------------------
# P2: no pre-submission reply is ever exposed as the current result
# ---------------------------------------------------------------------------
ACCEPTED_THEN_FAILING = [
    ("follow_up_500", {"prompt_raw_reply": {"ok": True}, "session_http_status_after_prompt": 500}, True),
    ("follow_up_timeout", {"prompt_raw_reply": {"ok": True}, "session_exception_after_prompt": "read_timeout"}, True),
    ("follow_up_unavailable", {"prompt_raw_reply": {"ok": True}, "session_exception_after_prompt": "connect_error"}, True),
    ("session_vanished", {"prompt_raw_reply": {"ok": True}, "vanish_after_prompt": True}, True),
    ("malformed_follow_up", {"prompt_raw_reply": {"ok": True}, "malformed_after_prompt": "invalid_json"}, True),
    ("reply_still_pending", {"prompt_raw_reply": {"ok": True}}, True),
    ("post_read_timeout", {"prompt_exception": "read_timeout"}, True),
]


@pytest.mark.parametrize(
    "label,stub_kwargs,expect_pending",
    ACCEPTED_THEN_FAILING,
    ids=[case[0] for case in ACCEPTED_THEN_FAILING],
)
def test_no_pre_submission_reply_is_exposed(tmp_path, label, stub_kwargs, expect_pending):
    stub = StubOpenCodeServer(**stub_kwargs)
    result = _bridge(tmp_path, stub).send_prompt("ses_match", "hello")

    assert _post_count(stub) == 1
    assert result.operation == "send_prompt"
    assert result.reply_pending is expect_pending
    # the whole point: no message window at all when no reply was correlated
    assert result.messages == []
    assert result.page is None
    assert result.reply_boundary == "msg_02", "the boundary stays as metadata"
    dumped = json.dumps(result.model_dump(mode="json"))
    assert STALE_REPLY not in dumped
    assert "msg_02" not in [message["message_id"] for message in result.model_dump()["messages"]]
    _assert_accounting_is_settled(tmp_path, result)


def test_a_correlated_reply_is_still_returned(tmp_path):
    """The fix must not hide a *new* reply."""
    stub = StubOpenCodeServer(prompt_ack_only=True)
    result = _bridge(tmp_path, stub).send_prompt("ses_match", "hello")

    assert result.operation == "send_prompt"
    assert result.reply_pending is False
    assert [message.message_id for message in result.messages] == ["msg_03"]
    assert result.messages[0].text == "echo: hello"
    assert "msg_02" not in [message.message_id for message in result.messages]
    _assert_accounting_is_settled(tmp_path, result)


# ---------------------------------------------------------------------------
# Adjacent cleanup 2: a real HTTP rejection keeps its status as evidence
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("status", [401, 500])
def test_rejected_submission_keeps_the_http_status(tmp_path, status):
    stub = StubOpenCodeServer(prompt_http_status=status, prompt_error_body='{"error":"nope"}')
    result = _bridge(tmp_path, stub).send_prompt("ses_match", "hello")

    assert result.operation == "send_prompt"
    assert result.submission_attempted is True
    assert result.submission_status == status
    assert result.submission_uncertain is False
    assert result.submission_body == ""
    assert result.reply_pending is False
    assert result.messages == [] and result.page is None
    assert _post_count(stub) == 1
    _assert_accounting_is_settled(tmp_path, result)
    post = [record for record in _records(tmp_path) if record.method == "POST"]
    assert post[0].http_status == status


# ---------------------------------------------------------------------------
# Human CLI: the same truth as --json, and never an old answer
# ---------------------------------------------------------------------------
def _cli_workspace(tmp_path: Path, monkeypatch, stub: StubOpenCodeServer):
    """Initialize a CLI workspace whose OpenCode transport is the offline stub."""
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
    stub.workspace = str(repo.resolve())
    for session in stub.sessions:
        session["directory"] = str(repo.resolve())
    import devrelay.opencode.bridge as bridge_module

    original = bridge_module.OpenCodeTransport
    bridge_module.OpenCodeTransport = lambda *a, **k: stub.transport()
    return repo, original


@pytest.mark.parametrize(
    "label,stub_kwargs,expected_submission",
    [
        ("accepted_pending", {"prompt_raw_reply": {"ok": True}}, "submission accepted (HTTP 200)"),
        (
            "accepted_unusable_body",
            {"prompt_http_status": 200, "prompt_error_body": "{not json"},
            "submission accepted (HTTP 200; response body unusable: invalid_json)",
        ),
        (
            "uncertain",
            {"prompt_exception": "read_timeout"},
            "submission uncertain",
        ),
        (
            "rejected",
            {"prompt_http_status": 500},
            "submission rejected (HTTP 500)",
        ),
        (
            "not_submitted",
            {"prompt_exception": "connect_error"},
            "submission not accepted",
        ),
    ],
    ids=["accepted_pending", "accepted_unusable_body", "uncertain", "rejected", "not_submitted"],
)
def test_human_output_states_the_submission_truth(
    tmp_path, monkeypatch, label, stub_kwargs, expected_submission
):
    stub = StubOpenCodeServer(**stub_kwargs)
    repo, original = _cli_workspace(tmp_path, monkeypatch, stub)
    try:
        human = CliRunner().invoke(app, ["opencode", "send", "--prompt", "hello"])
        machine = CliRunner().invoke(
            app, ["opencode", "send", "--prompt", "hello", "--json"]
        )
    finally:
        import devrelay.opencode.bridge as bridge_module

        bridge_module.OpenCodeTransport = original

    assert human.exit_code == 2, human.output
    assert expected_submission in human.output, human.output
    assert STALE_REPLY not in human.output, "an old reply must never be printed"

    payload = json.loads(machine.output)
    assert machine.exit_code == 2
    if "uncertain" in expected_submission:
        assert payload["submission_uncertain"] is True
        assert payload["reply_pending"] is True
    elif "rejected" in expected_submission:
        assert payload["submission_status"] == 500
        assert payload["submission_uncertain"] is False
    elif "not accepted" in expected_submission:
        assert payload["submission_attempted"] is True
        assert payload["submission_status"] is None
        assert payload["reply_pending"] is False
    assert payload["messages"] == []
    assert payload["page"] is None
    # human and JSON agree on the high-level truth
    if payload["reply_pending"]:
        assert "reply      pending" in human.output


def test_pending_human_output_says_do_not_resubmit(tmp_path, monkeypatch):
    stub = StubOpenCodeServer(
        prompt_raw_reply={"ok": True},
        session_http_status_after_prompt=500,
    )
    repo, original = _cli_workspace(tmp_path, monkeypatch, stub)
    try:
        human = CliRunner().invoke(app, ["opencode", "send", "--prompt", "hello"])
    finally:
        import devrelay.opencode.bridge as bridge_module

        bridge_module.OpenCodeTransport = original

    assert human.exit_code == 2
    assert "submission accepted (HTTP 200)" in human.output
    assert "reply      pending" in human.output
    assert "do not resubmit automatically" in human.output
    assert STALE_REPLY not in human.output
