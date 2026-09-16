"""v0.3-A second review remediation: focused regression tests.

Each test here exists because of one specific finding of the second independent
review (`71feaff..f5d487d`) and fails against `f5d487d` for the actual failure
mechanism:

* P1-A  every Codex child process (probes included) is scrubbed
* P1-B  a 2xx submission with an unusable body is post-acceptance, not a failure
* P1-C  the >2000-message anti-DoS cap keeps the true newest tail
* P1-D  escaped (JSON/unicode/percent) provider echoes are redacted too
* P1-E  parser bombs normalize into MALFORMED_RESPONSE and settle the ledger
* PART II A-F  adjacent hardening (accounting, identity, id grammar, id
  comparison, URL authority validation, phantom ledger record)

Everything is offline: the deterministic OpenCode stub (`httpx.MockTransport`),
the offline Codex stub spawned as a real child process, no network, no model.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote, quote_plus

import httpx
import pytest
import yaml
from pydantic import ValidationError
from typer.testing import CliRunner

from devrelay.cli import app
from devrelay.config import OpenCodeConfig, load_wiring_config
from devrelay.errors import (
    ConfigError,
    OpenCodeConfigError,
    OpenCodeLedgerError,
)
from devrelay.opencode.accounting import FilesystemOpenCodeLedger
from devrelay.opencode.bridge import OpenCodeBridge
from devrelay.opencode.models import (
    OpenCodeCallRecord,
    OpenCodeCallState,
    OpenCodeOperationState,
)
from devrelay.opencode.transport import OpenCodeTransport
from devrelay.providers.base import ImplementerContext
from devrelay.providers.codex_cli import CodexCLIProvider
from devrelay.providers.codex_runtime import (
    CODEX_CHILD_ENV_DENYLIST,
    detect_capabilities,
)
from devrelay.workspace.runner import CommandRunner

from helpers import (
    FakeCommandRunner,
    make_git_repo,
    make_packet,
    structured_codex_config,
    write_codex_stub,
)
from opencode_stub import DEFAULT_WORKSPACE, StubOpenCodeServer, _message, _session

WS = DEFAULT_WORKSPACE
TOKEN = "oc-token-SECOND-4711-abcdef"
NASTY_PROMPT = 'sum "quoted" \\ tab\there\nnewline é 秘密'
#: A bearer token must be header-safe (no control characters), but it can still
#: contain quotes and backslashes that a provider may echo in escaped form.
NASTY_TOKEN = 'oc-token-"quoted"\\back-4711'

#: Denylisted names this suite actually populates (asserted to be denylisted).
CREDENTIALS = {
    "DEVRELAY_OPENCODE_TOKEN": "oc-live-SECONDREMEDIATION-4711",
    "DEVRELAY_REVIEWER_API_KEY": "sk-live-REVIEWER-SECOND-4711",
    "OPENAI_API_KEY": "sk-openai-SECOND-4711",
    "ANTHROPIC_API_KEY": "sk-ant-SECOND-4711",
    "GEMINI_API_KEY": "AIza-SECOND-4711",
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _ledger(tmp_path: Path) -> FilesystemOpenCodeLedger:
    return FilesystemOpenCodeLedger(tmp_path / ".devrelay")


def _stub(prompt_status: int = 200, prompt_body: str | None = None, **kwargs: Any):
    """OpenCode stub whose /prompt route answers with a raw status/body."""
    return StubOpenCodeServer(
        prompt_http_status=prompt_status,
        prompt_error_body=prompt_body,
        **kwargs,
    )


def _encoded_forms(value: str) -> list[str]:
    """Every realistic encoding of *value* a provider could echo.

    Built independently of the implementation so the assertion is about the
    observable contract ("no recoverable form survives"), not about a helper.
    """
    forms = [value]
    frontier = [value]
    for _ in range(2):
        nxt: list[str] = []
        for item in frontier:
            nxt.extend(
                [
                    json.dumps(item)[1:-1],
                    item.encode("unicode_escape").decode("ascii"),
                    quote(item, safe=""),
                    quote_plus(item, safe=""),
                ]
            )
        forms.extend(nxt)
        frontier = nxt
    return [form for form in forms if len(form) >= 4]


def _assert_no_recoverable(text: str, *values: str) -> None:
    for value in values:
        for form in _encoded_forms(value):
            assert form not in text, f"recoverable secret form leaked: {form!r}"


def _bridge(tmp_path: Path, stub: StubOpenCodeServer, **kwargs: Any) -> OpenCodeBridge:
    max_response_bytes = kwargs.get("max_response_bytes", 1_048_576)
    return OpenCodeBridge(
        base_url="http://opencode.invalid",
        workspace_root=WS,
        token=kwargs.pop("token", ""),
        transport=stub.transport(
            token=kwargs.pop("transport_token", ""),
            max_response_bytes=max_response_bytes,
        ),
        ledger=_ledger(tmp_path),
        **kwargs,
    )


def _records(tmp_path: Path) -> list[OpenCodeCallRecord]:
    return _ledger(tmp_path).read_records()


def _all_durable_text(tmp_path: Path) -> str:
    chunks: list[str] = []
    for path in (tmp_path / ".devrelay").rglob("*"):
        if path.is_file():
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def _codex_launcher(tmp_path: Path, stub: Path) -> Path:
    """A real executable that runs the offline Codex stub.

    The availability probe runs the configured executable *directly* (no launcher
    prefix), so capturing that child's environment needs a real executable rather
    than an ``executable + launcher_args`` pair.
    """
    if os.name == "nt":
        launcher = tmp_path / "codex.cmd"
        launcher.write_text(
            "@echo off" + chr(13) + chr(10)
            + f'"{sys.executable}" "{stub}" %*' + chr(13) + chr(10),
            encoding="utf-8",
        )
    else:  # pragma: no cover - POSIX portability
        launcher = tmp_path / "codex"
        launcher.write_text(
            "#!/bin/sh" + chr(10)
            + f'exec "{sys.executable}" "{stub}" "$@"' + chr(10),
            encoding="utf-8",
        )
        launcher.chmod(0o755)
    return launcher


def _codex_child_log(tmp_path: Path) -> Path:
    return tmp_path / "codex-invocations.jsonl"


def _write_capturing_codex_stub(tmp_path: Path, **overrides: Any) -> Path:
    payload: dict[str, Any] = {
        "invocation_log": str(_codex_child_log(tmp_path)),
        "env_names": list(CODEX_CHILD_ENV_DENYLIST),
        "changed_files": ["app.py"],
    }
    payload.update(overrides)
    return write_codex_stub(tmp_path / "tools", **payload)


def _read_codex_child_log(tmp_path: Path) -> list[dict[str, Any]]:
    path = _codex_child_log(tmp_path)
    assert path.is_file(), "no Codex child invocation was captured"
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _assert_children_scrubbed(entries: list[dict[str, Any]]) -> None:
    assert entries, "no Codex child invocation was captured"
    for entry in entries:
        for name in CODEX_CHILD_ENV_DENYLIST:
            assert entry["env"].get(name) is False, (name, entry["argv"])


def _assert_parent_keeps_credentials() -> None:
    for name, value in CREDENTIALS.items():
        assert os.environ.get(name) == value, (
            "the parent DevRelay environment must keep its credentials"
        )


def _impl_context(root: Path) -> ImplementerContext:
    return ImplementerContext(
        task_id="DR-0001",
        packet=make_packet(),
        attempt=1,
        workspace_root=str(root),
        is_fix=False,
        findings=[],
    )


# ---------------------------------------------------------------------------
# P1-A: every Codex child process receives the denylist
# ---------------------------------------------------------------------------
def test_denylist_names_used_by_this_suite_are_really_denylisted():
    for name in CREDENTIALS:
        assert name in CODEX_CHILD_ENV_DENYLIST, name


def test_every_codex_child_path_is_scrubbed(tmp_path, monkeypatch):
    """Real child processes: probes, text runtime, structured runtime, doctor."""
    for name, value in CREDENTIALS.items():
        monkeypatch.setenv(name, value)
    stub = _write_capturing_codex_stub(tmp_path)
    launcher = _codex_launcher(tmp_path, stub)
    workspace = tmp_path / "ws"
    workspace.mkdir()

    # 1. availability probe (`codex --version`) and 2. help probe (`exec --help`)
    provider = CodexCLIProvider(
        structured_codex_config(stub, executable=str(launcher)),
        CommandRunner(),
        workspace_root=str(workspace),
    )
    available, _diagnostic = provider.availability()
    assert available is True
    provider.unknown_arg_warnings()
    after_probes = _read_codex_child_log(tmp_path)
    assert ["--version"] in [entry["argv"] for entry in after_probes]
    assert any("--help" in entry["argv"] for entry in after_probes)
    _assert_children_scrubbed(after_probes)

    # 3. capability detection (the doctor path, called with a bare runner)
    capabilities = detect_capabilities(CommandRunner(), str(launcher))
    assert capabilities.present is True
    _assert_children_scrubbed(_read_codex_child_log(tmp_path))

    # 4. legacy text runtime (no structured plan on the context)
    text_provider = CodexCLIProvider(
        structured_codex_config(
            stub,
            executable=str(launcher),
            runtime_mode="text",
            args=["exec", "--sandbox", "workspace-write"],
        ),
        CommandRunner(),
        workspace_root=str(workspace),
    )
    text_result = text_provider.run(_impl_context(workspace))
    assert text_result.exit_code == 0, text_result.stderr
    entries = _read_codex_child_log(tmp_path)
    text_entries = [
        entry
        for entry in entries
        if entry["argv"][:1] == ["exec"] and "--help" not in entry["argv"]
    ]
    assert text_entries, "the text runtime did not spawn a real child"
    _assert_children_scrubbed(entries)

    # 5. structured runtime (the full offline engine path)
    from test_v02c_structured import STATE, _default_config, _engine_with_stub, _start

    root, store, engine = _engine_with_stub(tmp_path / "structured", stub)
    _start(engine, store)
    engine.continue_task(STATE)
    entries = _read_codex_child_log(tmp_path)
    structured = [entry for entry in entries if "--output-schema" in entry["argv"]]
    assert structured, "the structured runtime did not spawn a real child"
    _assert_children_scrubbed(entries)

    # the parent keeps every credential, and no child ever persisted one
    _assert_parent_keeps_credentials()
    for value in CREDENTIALS.values():
        assert value not in _all_durable_text(tmp_path)


def test_provider_probes_pass_the_denylist_to_the_runner(tmp_path):
    """Production boundary: the runner call itself carries the denylist."""
    runner = FakeCommandRunner()
    provider = CodexCLIProvider(
        structured_codex_config(tmp_path / "codex_stub.py"),
        runner,
        workspace_root=str(tmp_path),
    )
    provider.availability()
    provider.unknown_arg_warnings()
    assert len(runner.calls) >= 2
    for call in runner.calls:
        assert call["env_remove"] == list(CODEX_CHILD_ENV_DENYLIST)


def test_doctor_codex_probes_are_scrubbed(tmp_path, monkeypatch):
    for name, value in CREDENTIALS.items():
        monkeypatch.setenv(name, value)
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    monkeypatch.chdir(repo)
    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    stub = _write_capturing_codex_stub(tmp_path)
    launcher = _codex_launcher(tmp_path, stub)
    config_path = repo / ".devrelay" / "config.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    data["codex"] = {
        "executable": str(launcher),
        "args": ["exec", "--sandbox", "workspace-write"],
        "runtime_mode": "text",
    }
    config_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0, result.output
    entries = _read_codex_child_log(tmp_path)
    _assert_children_scrubbed(entries)
    assert any("--version" in entry["argv"] for entry in entries)
    _assert_parent_keeps_credentials()
    for value in CREDENTIALS.values():
        assert value not in result.output


# ---------------------------------------------------------------------------
# P1-B: 2xx + unusable body = accepted submission, never a failed one
# ---------------------------------------------------------------------------
UNUSABLE_BODIES = [
    ("empty_response", 204, ""),
    ("empty_response", 200, ""),
    ("invalid_json", 200, "{not json"),
    ("response_too_large", 200, '{"pad":"' + "y" * 5_000 + '"}'),
]


@pytest.mark.parametrize("expected_body,status,body", UNUSABLE_BODIES)
def test_2xx_with_an_unusable_body_is_post_acceptance(
    tmp_path, expected_body, status, body
):
    stub = _stub(status, body)
    kwargs: dict[str, Any] = {}
    if expected_body == "response_too_large":
        kwargs["max_response_bytes"] = 1_024
    result = _bridge(tmp_path, stub, **kwargs).send_prompt("ses_match", "hello")

    # exactly one POST, never a resubmission
    posts = [path for _method, path in stub.requests if path.endswith("/prompt")]
    assert posts == ["/session/ses_match/prompt"]
    # the follow-up read was performed (the session still exists)
    assert sum(1 for _m, path in stub.requests if path.endswith("/message")) == 2
    # the operation keeps its own identity and never claims "not submitted"
    assert result.operation == "send_prompt"
    assert result.state is OpenCodeOperationState.COMPLETED
    assert result.reply_pending is True
    assert result.messages == []
    assert result.submission_body == expected_body
    assert result.submission_status == status
    assert result.error_type == "reply_pending"
    assert "unusable" in result.error and "resubmit" in result.error
    assert result.reply_boundary == "msg_02"
    assert "not submitted" not in result.error
    # accounting: every issued request appears in the operation and the ledger
    records = _records(tmp_path)
    assert result.request_count == len(records) == 6
    assert set(result.call_ids) == {record.call_id for record in records}
    assert [r.http_status for r in records if r.method == "POST"] == [status]
    assert not [r for r in records if r.state is OpenCodeCallState.ISSUED]


def test_2xx_with_an_unusable_body_still_correlates_a_later_reply(tmp_path):
    stub = _stub(200, "{not json", prompt_append=_message("msg_03", "assistant", "later"))
    result = _bridge(tmp_path, stub).send_prompt("ses_match", "hello")

    assert result.operation == "send_prompt"
    assert result.submission_body == "invalid_json"
    assert result.reply_pending is False
    assert [message.message_id for message in result.messages] == ["msg_03"]
    assert result.request_count == len(_records(tmp_path)) == 6


def test_4xx_submission_is_still_a_failed_operation(tmp_path):
    """The 2xx rule must not weaken genuine submission failures."""
    stub = _stub(500, '{"error":"boom"}')
    result = _bridge(tmp_path, stub).send_prompt("ses_match", "hello")

    assert result.operation == "send_prompt"
    assert result.state is OpenCodeOperationState.PROVIDER_UNAVAILABLE
    assert result.reply_pending is False
    assert result.submission_body == ""
    assert result.error_type == "http_status"
    assert sum(1 for _m, path in stub.requests if path.endswith("/prompt")) == 1
    assert result.request_count == len(_records(tmp_path)) == 4


# ---------------------------------------------------------------------------
# P1-C: the anti-DoS cap keeps the true tail
# ---------------------------------------------------------------------------
def _bulk_messages(count: int) -> list[dict[str, Any]]:
    return [
        _message("msg_%04d" % index, "user", "text %d" % index)
        for index in range(1, count + 1)
    ]


@pytest.mark.parametrize("count", [2100, 2300])
def test_large_payloads_keep_the_true_newest_messages(count):
    stub = StubOpenCodeServer(messages=_bulk_messages(count))
    result = stub.bridge().read_messages("ses_match")

    newest = "msg_%04d" % count
    ids = [message.message_id for message in result.messages]
    assert len(ids) == 50
    assert ids[-1] == newest, "the true newest message must be visible"
    assert ids[0] == "msg_%04d" % (count - 49)
    assert result.page is not None
    assert result.page.provider_message_count == count
    assert result.page.window_truncated is True
    assert result.page.next_cursor == newest
    assert result.page.replayed is False
    assert result.page.cursor_unknown is False


def test_large_payload_cursor_and_replay_semantics_are_honest():
    stub = StubOpenCodeServer(messages=_bulk_messages(2100))
    bridge = stub.bridge()

    tail = bridge.read_messages("ses_match", "msg_2099")
    assert [message.message_id for message in tail.messages] == ["msg_2100"]
    assert tail.page is not None and tail.page.replayed is False

    newest = bridge.read_messages("ses_match", "msg_2100")
    assert newest.messages == []
    assert newest.page is not None and newest.page.replayed is True

    # a cursor from the (unkept) head is flagged, never silently replayed
    head = bridge.read_messages("ses_match", "msg_0001")
    assert head.page is not None
    assert head.page.cursor_unknown is True
    assert [m.message_id for m in head.messages][-1] == "msg_2100"


def test_send_prompt_sees_a_reply_appended_to_a_large_session(tmp_path):
    stub = StubOpenCodeServer(messages=_bulk_messages(2100), prompt_ack_only=True)
    result = _bridge(tmp_path, stub).send_prompt("ses_match", "hello")

    assert result.reply_pending is False, (
        "a reply appended to the true tail of a large session must be correlated"
    )
    assert [message.message_id for message in result.messages] == ["msg_2101"]
    assert result.request_count == len(_records(tmp_path)) == 6


# ---------------------------------------------------------------------------
# P1-D: escaped provider echoes are redacted too
# ---------------------------------------------------------------------------
def test_post_failure_echo_is_scrubbed_in_every_encoding(tmp_path):
    echo = json.dumps({"error": NASTY_PROMPT, "auth": NASTY_TOKEN})
    stub = StubOpenCodeServer(
        prompt_http_status=500, prompt_error_body=echo
    )
    result = _bridge(tmp_path, stub, token=NASTY_TOKEN, transport_token=NASTY_TOKEN).send_prompt(
        "ses_match", NASTY_PROMPT
    )

    assert result.error_type == "http_status" and result.http_status == 500
    _assert_no_recoverable(result.error, NASTY_PROMPT, NASTY_TOKEN)
    _assert_no_recoverable(json.dumps(result.model_dump(mode="json")), NASTY_PROMPT, NASTY_TOKEN)
    _assert_no_recoverable(_all_durable_text(tmp_path), NASTY_PROMPT, NASTY_TOKEN)
    # evidence that mattered is still there
    post = [record for record in _records(tmp_path) if record.method == "POST"]
    assert post and post[0].http_status == 500 and post[0].error_type == "http_status"


def test_follow_up_and_poll_echoes_are_scrubbed_in_every_encoding(tmp_path):
    echo = json.dumps({"error": NASTY_PROMPT, "auth": NASTY_TOKEN, "pad": "z" * 4_000})

    follow_up_stub = StubOpenCodeServer(
        prompt_raw_reply={"ok": True},
        session_http_status_after_prompt=500,
        session_error_body_after_prompt=echo,
    )
    follow_up = _bridge(
        tmp_path / "follow", follow_up_stub, token=NASTY_TOKEN, transport_token=NASTY_TOKEN
    ).send_prompt("ses_match", NASTY_PROMPT)
    assert follow_up.error_type == "http_status"
    _assert_no_recoverable(follow_up.error, NASTY_PROMPT, NASTY_TOKEN)
    _assert_no_recoverable(
        _all_durable_text(tmp_path / "follow"), NASTY_PROMPT, NASTY_TOKEN
    )
    assert len(follow_up.error) <= 600

    poll_stub = StubOpenCodeServer(http_status=500, error_body=echo)
    polled = OpenCodeBridge(
        base_url="http://opencode.invalid",
        workspace_root=WS,
        token=NASTY_TOKEN,
        transport=poll_stub.transport(token=NASTY_TOKEN),
        ledger=_ledger(tmp_path / "poll"),
        sleep=lambda _seconds: None,
    ).wait_idle("ses_match", 1.0, redact_values=(NASTY_PROMPT,))
    assert polled.error_type == "http_status"
    _assert_no_recoverable(polled.error, NASTY_PROMPT, NASTY_TOKEN)
    _assert_no_recoverable(_all_durable_text(tmp_path / "poll"), NASTY_PROMPT, NASTY_TOKEN)


def test_cli_output_never_renders_a_recoverable_echo(tmp_path, monkeypatch):
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

    stub = StubOpenCodeServer(
        workspace=str(repo.resolve()),
        prompt_http_status=500,
        prompt_error_body=json.dumps({"error": NASTY_PROMPT, "auth": NASTY_TOKEN}),
    )
    import devrelay.opencode.bridge as bridge_module

    original = bridge_module.OpenCodeTransport
    bridge_module.OpenCodeTransport = lambda *a, **k: stub.transport(token=NASTY_TOKEN)
    monkeypatch.setenv("DEVRELAY_OPENCODE_TOKEN", NASTY_TOKEN)
    try:
        human = runner.invoke(
            app, ["opencode", "send", "--prompt", NASTY_PROMPT]
        )
        assert human.exit_code == 2, human.output
        _assert_no_recoverable(human.output, NASTY_PROMPT, NASTY_TOKEN)

        machine = runner.invoke(
            app, ["opencode", "send", "--prompt", NASTY_PROMPT, "--json"]
        )
        assert machine.exit_code == 2, machine.output
        _assert_no_recoverable(machine.output, NASTY_PROMPT, NASTY_TOKEN)
    finally:
        bridge_module.OpenCodeTransport = original
    _assert_no_recoverable(_all_durable_text(repo), NASTY_PROMPT, NASTY_TOKEN)


# ---------------------------------------------------------------------------
# P1-E: parser bombs normalize and always settle the ledger
# ---------------------------------------------------------------------------
PARSER_BOMBS = [
    ("deep_json", "json_too_deep"),
    ("huge_int", "json_unparsable"),
    ("invalid_json", "invalid_json"),
]


@pytest.mark.parametrize("malformed,expected", PARSER_BOMBS)
@pytest.mark.parametrize("operation", ["health", "get_session"])
def test_parser_bombs_are_malformed_and_settled(tmp_path, malformed, expected, operation):
    stub = StubOpenCodeServer(malformed=malformed)
    bridge = _bridge(tmp_path, stub)
    result = bridge.health() if operation == "health" else bridge.get_session("ses_match")

    assert result.state is OpenCodeOperationState.MALFORMED_RESPONSE
    assert result.error_type == expected
    records = _records(tmp_path)
    assert len(records) == 1
    record = records[0]
    assert record.state is OpenCodeCallState.MALFORMED_RESPONSE
    assert record.error_type == expected
    assert record.completed_at, "the durable record must be settled, not left ISSUED"
    assert not [r for r in records if r.state is OpenCodeCallState.ISSUED]


def test_parser_bomb_does_not_traceback_in_the_cli(tmp_path, monkeypatch):
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    monkeypatch.chdir(repo)
    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    config_path = repo / ".devrelay" / "config.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    data["opencode"] = {
        "base_url": "http://opencode.invalid",
        "workspace": str(repo.resolve()),
    }
    config_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    stub = StubOpenCodeServer(malformed="deep_json")
    import devrelay.opencode.bridge as bridge_module

    original = bridge_module.OpenCodeTransport
    bridge_module.OpenCodeTransport = lambda *a, **k: stub.transport()
    try:
        result = runner.invoke(app, ["opencode", "health"])
        assert result.exit_code == 2, result.output
        assert "Traceback" not in result.output
        assert "MALFORMED_RESPONSE" in result.output
    finally:
        bridge_module.OpenCodeTransport = original


def test_programming_errors_still_propagate(tmp_path):
    """The parser guard must not swallow DevRelay's own bugs."""

    class ExplodingTransport:
        base_url = "http://opencode.invalid"

        def request(self, *args: Any, **kwargs: Any):  # pragma: no cover - raises
            raise TypeError("a programming error, not provider content")

    bridge = OpenCodeBridge(
        base_url="http://opencode.invalid",
        workspace_root=WS,
        transport=ExplodingTransport(),
        ledger=_ledger(tmp_path),
    )
    with pytest.raises(TypeError):
        bridge.health()
    # A DevRelay bug fails loudly and is deliberately *not* normalized into a
    # provider condition (the review only requires normalizing untrusted content).
    assert _records(tmp_path)[0].state is OpenCodeCallState.ISSUED


# ---------------------------------------------------------------------------
# PART II-A: accounting survives an early validation failure
# ---------------------------------------------------------------------------
def test_boundary_failure_keeps_the_probe_accounting(tmp_path):
    stub = StubOpenCodeServer(messages_http_status=500)
    result = _bridge(tmp_path, stub).send_prompt("ses_match", "hello")

    assert result.operation == "send_prompt"
    assert result.error_type == "http_status"
    records = _records(tmp_path)
    assert result.request_count == len(records) == 3
    assert set(result.call_ids) == {record.call_id for record in records}
    assert [record.operation for record in records] == [
        "send_prompt",       # ownership probe
        "read_messages",     # boundary session read
        "read_messages",     # boundary message read (the failure)
    ]


def test_probe_failure_keeps_its_own_call(tmp_path):
    stub = StubOpenCodeServer(http_status=500)  # the probe itself fails
    result = _bridge(tmp_path, stub).send_prompt("ses_match", "hello")
    assert result.ok is False
    records = _records(tmp_path)
    assert result.request_count == len(records) == 1
    assert result.call_ids == [records[0].call_id]


# ---------------------------------------------------------------------------
# PART II-B: send_prompt identity survives a malformed follow-up
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("malformed", ["invalid_json", "not_object"])
def test_malformed_follow_up_keeps_the_send_identity(tmp_path, malformed):
    stub = StubOpenCodeServer(
        prompt_raw_reply={"ok": True}, malformed_after_prompt=malformed
    )
    result = _bridge(tmp_path, stub).send_prompt("ses_match", "hello")

    assert result.operation == "send_prompt"
    assert result.state is OpenCodeOperationState.MALFORMED_RESPONSE
    assert result.reply_pending is True
    assert result.follow_up_state == OpenCodeOperationState.MALFORMED_RESPONSE.value
    assert result.messages == []
    records = _records(tmp_path)
    assert result.request_count == len(records) == 5
    assert set(result.call_ids) == {record.call_id for record in records}


# ---------------------------------------------------------------------------
# PART II-C: dot-segment session ids are refused
# ---------------------------------------------------------------------------
DOT_IDS = [".", "..", "...", "....", ". ."]


@pytest.mark.parametrize("bad", DOT_IDS)
def test_dot_segment_session_ids_issue_zero_requests(bad):
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
    assert stub.requests == [], "a dot segment must never reach URL construction"


def test_dotted_ids_that_are_not_dot_segments_still_work():
    session_id = "ses.1.a~b"
    stub = StubOpenCodeServer(sessions=[_session(session_id, workspace=WS)])
    result = stub.bridge().get_session(session_id)
    assert result.ok is True
    assert stub.requests == [("GET", f"/session/{session_id}")]


# ---------------------------------------------------------------------------
# PART II-D: the full returned id is compared
# ---------------------------------------------------------------------------
def test_returned_id_suffix_cannot_hide_behind_truncation():
    requested = "s" * 200                        # the supported maximum
    stub = StubOpenCodeServer(
        sessions=[_session(requested, workspace=WS)],
        session_id_override=requested + "EXTRA",
    )
    result = stub.bridge().get_session(requested)

    assert result.state is OpenCodeOperationState.MALFORMED_RESPONSE
    assert "longer than 200" in result.error
    assert not [m for m, _p in stub.requests if m != "GET"]


def test_returned_id_mismatch_is_still_detected():
    stub = StubOpenCodeServer(session_id_override="ses_other")
    result = stub.bridge().get_session("ses_match")
    assert result.state is OpenCodeOperationState.MALFORMED_RESPONSE
    assert "ses_other" in result.error


# ---------------------------------------------------------------------------
# PART II-E: URL/authority validation before httpx
# ---------------------------------------------------------------------------
BAD_URLS = [
    "http://127.0.0.1:notaport",
    "http://127.0.0.1:1:2",
    "http://127.0.0.1:99999",
    "http://127.0.0.1:4096\x00",
    "http://127.0.0.1:40 96",
    "http://127.0.0.1%2Fadmin:4096",
    "http://127.0.0.1:4096/%2e%2e/admin",
]


@pytest.mark.parametrize("bad", BAD_URLS)
def test_malformed_urls_are_configuration_errors(bad):
    with pytest.raises(ValidationError):
        OpenCodeConfig(base_url=bad)


@pytest.mark.parametrize(
    "bad", ["http://127.0.0.1:notaport", "http://127.0.0.1:1:2"]
)
def test_malformed_authority_never_reaches_httpx(bad):
    # (A port above 65535 is syntactically valid for httpx and is refused by the
    # config layer instead - see test_malformed_urls_are_configuration_errors.)
    """A URL httpx would refuse must become a DevRelay configuration error."""
    try:
        transport = OpenCodeTransport(bad)
    except OpenCodeConfigError as exc:
        assert "not a usable URL" in str(exc)
        assert "Traceback" not in str(exc)
    except httpx.InvalidURL:  # pragma: no cover - the defect under test
        pytest.fail("httpx.InvalidURL escaped the provider boundary")
    else:  # pragma: no cover - the defect under test
        transport._client.close()
        pytest.fail("a malformed authority was accepted by the transport")


def test_config_errors_never_echo_an_embedded_password(tmp_path):
    secret = "sup3rsecret-password-4711"
    url = f"http://devrelay:{secret}@127.0.0.1:4096"
    with pytest.raises(ValidationError) as excinfo:
        OpenCodeConfig(base_url=url)
    assert secret not in str(excinfo.value)
    assert "[redacted]" in str(excinfo.value) or "redacted" in str(excinfo.value)

    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    config_path = repo / ".devrelay" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(f"opencode:\n  base_url: {url}\n", encoding="utf-8")
    with pytest.raises(ConfigError) as wiring_error:
        load_wiring_config(repo)
    assert secret not in str(wiring_error.value)


def test_accepted_urls_construct_a_transport():
    for value in ("http://127.0.0.1:4096", "https://opencode.internal:8443/"):
        transport = OpenCodeTransport(value)
        assert transport.base_url.startswith(("http://", "https://"))
        transport._client.close()


# ---------------------------------------------------------------------------
# PART II-F: no phantom in-memory ledger record
# ---------------------------------------------------------------------------
def test_refused_create_new_leaves_no_phantom_record(tmp_path):
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

    assert ledger.records() == [], (
        "a refused durable identity must not leave an in-memory phantom call "
        "(it would inflate elapsed totals and readback)"
    )
    assert json.loads(target.read_text(encoding="utf-8")) == {"sentinel": True}
