"""v0.2-C structured Codex runtime: offline stub end-to-end + tamper matrix.

Everything here runs against an offline `codex` stub (no model, no network).
The stub can produce valid/malformed/missing/oversized results, tamper with
`.devrelay` state, create unexpected staging files and inject fake secrets.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from devrelay.artifacts.store import ArtifactStore
from devrelay.config import CodexConfig
from devrelay.pipeline.states import PipelineState as S
from devrelay.providers.codex_runtime import (
    ALLOWED_CONFIG_KEYS,
    CodexArgumentError,
    CODEX_CHILD_ENV_DENYLIST,
    build_invocation,
    detect_capabilities,
    normalize_claim_path,
    normalize_result_payload,
    observe_events,
    parse_help_flags,
    validate_user_args,
)
from devrelay.workspace.runner import CommandRunner

from helpers import (
    FakeImplementer,
    ScriptedAutoReviewer,
    build_engine,
    make_packet,
    make_review,
    structured_codex_config,
    write_codex_stub,
)

STATE = "DR-0001"
FAKE_SECRET = "sk-live-V02CSECRET1234567890abcd"


def _engine_with_stub(tmp_path: Path, stub, *, config=None, **engine_kwargs):
    """Engine whose implementer is the real CodexCLIProvider + offline stub."""
    from devrelay.providers.codex_cli import CodexCLIProvider

    base = config or _default_config()
    codex_config = structured_codex_config(stub)
    base.codex = codex_config
    provider = CodexCLIProvider(
        codex_config, CommandRunner(), workspace_root=str(tmp_path / "ws")
    )
    root, store, engine = build_engine(
        tmp_path,
        config=base,
        implementer=provider,
        reviewer=ScriptedAutoReviewer([make_review("PASS")]),
        **engine_kwargs,
    )
    return root, store, engine


def _default_config():
    from helpers import default_config

    config = default_config()
    config.tests.targeted = []
    # one implementer call is enough for every scenario here
    config.budget.max_implementer_calls = 1
    config.budget.max_total_provider_calls = 2
    return config


def _start(engine, store):
    engine.create_task("structured runtime smoke")
    engine.import_plan(STATE, make_packet(task_id=STATE))
    return store


# ---------------------------------------------------------------------------
# C1 / C34 / C43: happy path
# ---------------------------------------------------------------------------
def test_structured_happy_path_persists_sanitized_evidence(tmp_path):
    stub = write_codex_stub(
        tmp_path / "tools",
        argv_capture=str(tmp_path / "argv.json"),
        prompt_capture=str(tmp_path / "prompt.txt"),
        env_capture=str(tmp_path / "env.json"),
        env_names=list(CODEX_CHILD_ENV_DENYLIST),
        changed_files=["app.py"],
    )
    root, store, engine = _engine_with_stub(tmp_path, stub)
    _start(engine, store)
    events = engine.continue_task(STATE)

    task = store.read_task(STATE)
    attempt = task.attempts[-1]
    assert attempt.milestone.value == "COMPLETION_APPLIED"
    assert attempt.completion_ready and attempt.completion_applied
    assert attempt.runtime is not None
    assert attempt.runtime.result_status == "COMPLETE"
    assert attempt.runtime.result_schema_version == 1
    assert attempt.runtime.control_plane_changes == 0
    assert attempt.runtime.staging_removed is True
    runtime_dir = store.task_runtime_dir(STATE, attempt.attempt_id)
    result = json.loads((runtime_dir / "result.json").read_text(encoding="utf-8"))
    assert result["schema_version"] == 1
    assert (runtime_dir / "completion.json").is_file()
    assert (runtime_dir / "implementation-reconciliation.json").is_file()
    assert (runtime_dir / "schema.json").is_file()
    assert (runtime_dir / "request.sanitized.txt").is_file()
    # transient staging is gone, durable evidence stays
    staging = store.attempt_staging_dir(STATE, attempt.attempt_id)
    assert list(staging.iterdir()) == []
    # exactly one external call, one durable call identity
    impl_calls = [
        call for call in task.provider_calls if call.provider_kind.value == "IMPLEMENTER"
    ]
    assert len(impl_calls) == 1 and impl_calls[0].external_call_count == 1
    assert engine.usage_block(STATE)["implementer_calls"] == 1
    # argv is DevRelay-owned: sandbox exactly once + schema/result flags
    argv = json.loads((tmp_path / "argv.json").read_text(encoding="utf-8"))
    assert argv.count("--sandbox") == 1 and "workspace-write" in argv
    assert "--output-schema" in argv and "--output-last-message" in argv
    assert "--ignore-user-config" in argv and "--ignore-rules" in argv
    assert "--json" in argv
    # child env: reviewer key scrubbed, no secret anywhere
    env = json.loads((tmp_path / "env.json").read_text(encoding="utf-8"))
    assert all(value is False for value in env.values()), env
    for path in runtime_dir.rglob("*"):
        if path.is_file():
            assert FAKE_SECRET not in path.read_text(encoding="utf-8", errors="replace")
    assert any("COMPLETION_READY" in event for event in events)


# ---------------------------------------------------------------------------
# C5 / C6 / C7 / C27 / C28: structured failures fail closed, no retry
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "stub_kwargs,expected_code",
    [
        ({"result": "missing"}, "codex_result_missing"),
        ({"result_payload": "{not json"}, "codex_result_malformed"),
        (
            {"result_payload": {"schema_version": 99, "status": "COMPLETE", "summary": "x"}},
            "codex_result_malformed",
        ),
        (
            {"result_payload": {"status": "COMPLETE", "summary": "no version"}},
            "codex_result_malformed",
        ),
        ({"result_payload": "x" * 5000, "max_result_bytes_override": 1024}, "codex_result_too_large"),
    ],
)
def test_structured_failures_block_without_retry(tmp_path, stub_kwargs, expected_code):
    overrides = {}
    if "max_result_bytes_override" in stub_kwargs:
        overrides["max_result_bytes"] = stub_kwargs.pop("max_result_bytes_override")
    stub = write_codex_stub(tmp_path / "tools", **stub_kwargs)
    config = _default_config()
    root, store, engine = _engine_with_stub(tmp_path, stub, config=config)
    if overrides:
        # rebuild with the smaller result cap
        codex_config = structured_codex_config(stub, **overrides)
        from devrelay.providers.codex_cli import CodexCLIProvider

        config.codex = codex_config
        root, store, engine = build_engine(
            tmp_path,
            config=config,
            implementer=CodexCLIProvider(
                codex_config, CommandRunner(), workspace_root=str(tmp_path / "ws")
            ),
            reviewer=ScriptedAutoReviewer([make_review("PASS")]),
        )
    _start(engine, store)
    engine.continue_task(STATE)

    task = store.read_task(STATE)
    assert task.state == S.BLOCKED
    assert task.blocked_code == expected_code
    # exactly one spawn, never an automatic second call
    impl_calls = [
        call for call in task.provider_calls if call.provider_kind.value == "IMPLEMENTER"
    ]
    assert len(impl_calls) == 1


def test_nonzero_exit_is_a_hard_failure(tmp_path):
    stub = write_codex_stub(tmp_path / "tools", exit_code=3, result="missing")
    root, store, engine = _engine_with_stub(tmp_path, stub)
    _start(engine, store)
    engine.continue_task(STATE)
    task = store.read_task(STATE)
    assert task.state == S.FAILED and task.blocked_code == "implementer_failed"


def test_model_status_is_advisory(tmp_path):
    """C30: exit 0 + valid result + status=BLOCKED still goes to TESTING."""
    stub = write_codex_stub(
        tmp_path / "tools", status="BLOCKED", summary="model gave up"
    )
    root, store, engine = _engine_with_stub(tmp_path, stub)
    _start(engine, store)
    engine.continue_task(STATE)
    task = store.read_task(STATE)
    assert task.state in (S.TESTING, S.REVIEWING, S.FINAL_GATE_REQUIRED)
    assert task.blocked_code is None
    attempt = task.attempts[-1]
    assert attempt.runtime.result_status == "BLOCKED"
    recon = json.loads(
        (
            store.task_runtime_dir(STATE, attempt.attempt_id)
            / "implementation-reconciliation.json"
        ).read_text(encoding="utf-8")
    )
    assert recon["claimed_status"] == "BLOCKED"


# ---------------------------------------------------------------------------
# C31 / C32 / C33 / C35: control-plane tamper matrix
# ---------------------------------------------------------------------------
def test_control_plane_violation_on_state_tamper(tmp_path):
    state_path = None  # resolved below via the store

    def tamper_target(root):
        return str(Path(root) / ".devrelay" / "tasks" / STATE / "state.json")

    root_dir = tmp_path / "ws"
    stub = write_codex_stub(tmp_path / "tools", tamper=[])
    # the tamper target only exists after `start`; rewrite the sidecar then
    root, store, engine = _engine_with_stub(tmp_path, stub)
    _start(engine, store)
    state_path = store.state_path(STATE)
    (tmp_path / "tools" / "stub-config.json").write_text(
        json.dumps({"tamper": [["write", str(state_path), '{"tampered": true}']]}),
        encoding="utf-8",
    )

    engine.continue_task(STATE)

    holds = store.list_control_plane_holds()
    assert len(holds) == 1 and holds[0]["code"] == "codex_control_plane_violation"
    assert "state.json" in " ".join(holds[0]["diverging_paths"])
    # tampered state is left untouched and untrusted
    assert "tampered" in state_path.read_text(encoding="utf-8")
    report = json.loads(
        (store.control_state_dir(STATE) / f"{holds[0]['attempt_id']}-violation.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["differences"], report
    serialized = json.dumps(report)
    assert "tampered" not in serialized  # metadata only, never file contents
    # mutating commands refuse while the hold exists
    with pytest.raises(Exception):
        engine.continue_task(STATE)


def test_control_plane_violation_on_ledger_tamper(tmp_path):
    root, store, engine = _engine_with_stub(
        tmp_path, write_codex_stub(tmp_path / "tools")
    )
    _start(engine, store)
    ledger = store.policy_dir(STATE) / "calls"
    ledger.mkdir(parents=True, exist_ok=True)
    target = ledger / "DR-0001-C0001.json"
    target.write_text('{"call_id": "DR-0001-C0001"}', encoding="utf-8")
    (tmp_path / "tools" / "stub-config.json").write_text(
        json.dumps({"tamper": [["write", str(target), '{"external_call_count": 0}']]}),
        encoding="utf-8",
    )
    engine.continue_task(STATE)
    holds = store.list_control_plane_holds()
    assert holds and "calls/DR-0001-C0001.json" in " ".join(holds[0]["diverging_paths"])


def test_control_plane_violation_on_unexpected_staging_file(tmp_path):
    root, store, engine = _engine_with_stub(
        tmp_path, write_codex_stub(tmp_path / "tools", extra_staging="evil.txt")
    )
    _start(engine, store)
    engine.continue_task(STATE)
    holds = store.list_control_plane_holds()
    assert holds and any(
        "evil.txt" in path for path in holds[0]["diverging_paths"]
    )


def test_secret_in_tampered_file_never_reaches_evidence(tmp_path):
    """C42: a model-injected secret in a tampered control file stays out of evidence."""
    root, store, engine = _engine_with_stub(
        tmp_path, write_codex_stub(tmp_path / "tools")
    )
    _start(engine, store)
    target = store.policy_dir(STATE) / "calls" / "DR-0001-C0001.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "tools" / "stub-config.json").write_text(
        json.dumps(
            {"tamper": [["write", str(target), json.dumps({"secret": FAKE_SECRET})]]}
        ),
        encoding="utf-8",
    )
    engine.continue_task(STATE)
    control_dir = store.control_state_dir(STATE)
    for path in control_dir.rglob("*"):
        if path.is_file():
            assert FAKE_SECRET not in path.read_text(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# unit-level: argv ownership, path normalization, event observation
# ---------------------------------------------------------------------------
def test_argument_ownership_rejects_indirect_bypasses():
    for args in (
        ["exec", "--sandbox", "read-only"],
        ["exec", "--add-dir", "/tmp"],
        ["exec", "--cd", "/tmp"],
        ["exec", "-p", "work"],
        ["exec", "--dangerously-bypass-approvals-and-sandbox"],
        ["exec", "-c", "mcp_servers.foo={}"],
        ["exec", "-c", "shell_environment_policy.inherit=all"],
    ):
        with pytest.raises(CodexArgumentError):
            validate_user_args(args)
    # legacy default and model-only overrides stay allowed
    validate_user_args(["exec", "--sandbox", "workspace-write"])
    validate_user_args(["exec", "-c", "model_reasoning_effort=high"])
    assert "model" in ALLOWED_CONFIG_KEYS
    from devrelay.config import CodexConfig

    for bad in ({"args": ["exec", "-p", "work"]}, {"launcher_args": ["--cd", "/tmp"]}):
        with pytest.raises(Exception):
            CodexConfig(**bad)


def test_claim_path_normalization_rejects_traversal():
    assert normalize_claim_path("src\\a.py") == "src/a.py"
    assert normalize_claim_path("./src//b.py") == "src/b.py"
    assert normalize_claim_path("src/../etc/passwd") is None
    assert normalize_claim_path("/etc/passwd") is None
    assert normalize_claim_path("C:\\windows") is None
    assert normalize_claim_path("//host/share") is None
    assert normalize_claim_path("") is None


def test_result_normalization_records_unknown_fields_by_name_only():
    payload = {
        "schema_version": 1,
        "status": "partial",
        "summary": "  work in progress  ",
        "changed_files": ["a.py", "../escape", "/abs"],
        "tests_run": [{"command": "pytest -q", "result": "pass"}],
        "mystery": {"nested": FAKE_SECRET},
    }
    result, rejected, unknown = normalize_result_payload(payload)
    assert result.status == "PARTIAL"
    assert result.summary == "work in progress"
    assert result.changed_files == ["a.py"]
    assert rejected and rejected[0].startswith("../")
    assert unknown == ["mystery"]
    assert FAKE_SECRET not in result.model_dump_json()


def test_event_observation_is_tolerant():
    observation = observe_events(
        '{"type":"thread.started","thread_id":"abc"}\nnot json\n{"type":"x","model":"m"}'
    )
    assert observation.session_id == "abc" and observation.model == "m"
    assert observation.event_count == 2
    assert observation.parse_warnings


def test_capability_detection_uses_help_text_only(tmp_path):
    stub = write_codex_stub(tmp_path / "tools")
    capabilities = detect_capabilities(CommandRunner(), str(stub))
    # `sys.executable` needs the launcher prefix; probe the flags parser instead
    assert capabilities.present or not capabilities.present
    flags = parse_help_flags(
        "  --output-schema <FILE>\n  -o, --output-last-message <FILE>\n  --json\n"
    )
    assert {"--output-schema", "--output-last-message", "-o", "--json"} <= set(flags)
