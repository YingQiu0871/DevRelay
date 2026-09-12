"""v0.2-C real-smoke schema remediation: strict structured-output contract.

The one approved real Codex smoke (call ``DR-0001-C0001`` against candidate
``301e891``) failed with HTTP 400 ``invalid_json_schema``:

    Invalid schema for response_format 'codex_output_schema':
    'additionalProperties' is required to be supplied and to be false.

The transport schema was tolerant (``additionalProperties: true``, only three
required root fields), which the real Structured Outputs endpoint refuses.  The
offline stub accepted it, so 349 tests stayed green.  These tests make the
strictness contract explicit and make the stub as strict as the real endpoint.
"""

from __future__ import annotations

import json
from pathlib import Path

from devrelay.pipeline.budget import ProviderBudget
from devrelay.providers.codex_cli import CodexCLIProvider
from devrelay.providers.codex_runtime import (
    IMPLEMENTATION_RESULT_SCHEMA_VERSION,
    parse_result_bytes,
    result_json_schema,
)
from devrelay.workspace.runner import CommandRunner

from helpers import (
    ScriptedAutoReviewer,
    build_engine,
    default_config,
    make_packet,
    make_review,
    structured_codex_config,
    write_codex_stub,
)

STATE = "DR-0001"

# The exact pre-fix transport schema (candidate 301e891): tolerant objects.
PRE_FIX_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "DevRelay ImplementationResult",
    "type": "object",
    "additionalProperties": True,
    "required": ["schema_version", "status", "summary"],
    "properties": {
        "schema_version": {"type": "integer", "const": 1},
        "status": {"type": "string", "enum": ["COMPLETE", "PARTIAL", "BLOCKED", "FAILED"]},
        "summary": {"type": "string"},
        "changed_files": {"type": "array", "items": {"type": "string"}},
        "tests_run": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "required": ["command", "result"],
                "properties": {
                    "command": {"type": "string"},
                    "result": {"type": "string", "enum": ["PASS", "FAIL", "NOT_RUN"]},
                    "notes": {"type": "string"},
                },
            },
        },
        "unresolved_items": {"type": "array", "items": {"type": "string"}},
        "known_risks": {"type": "array", "items": {"type": "string"}},
    },
}


def _object_nodes(schema, where="root"):
    """Yield (where, node) for every schema node that declares an object."""
    if isinstance(schema, dict):
        if schema.get("type") == "object" or "properties" in schema:
            yield where, schema
        for key, value in schema.items():
            if key in ("properties", "items", "$defs"):
                yield from _object_nodes(value, f"{where}.{key}")
    elif isinstance(schema, list):
        for index, item in enumerate(schema):
            yield from _object_nodes(item, f"{where}[{index}]")


# ---------------------------------------------------------------------------
# Recursive strictness lint (offline, no network, no provider call)
# ---------------------------------------------------------------------------
def test_schema_generation_is_pure_and_needs_no_provider_call():
    first, second = result_json_schema(), result_json_schema()
    assert first == second and first is not second  # pure, no cached mutation
    assert json.loads(json.dumps(first)) == first  # serialisable transport form


def test_every_object_node_is_closed_and_fully_required():
    schema = result_json_schema()
    nodes = list(_object_nodes(schema))
    assert nodes, "the transport schema must declare at least the root object"
    for where, node in nodes:
        assert node.get("additionalProperties") is False, (
            f"{where}: additionalProperties must be false "
            "(the real endpoint rejects anything else)"
        )
        props = node.get("properties")
        assert isinstance(props, dict) and props, f"{where}: properties missing"
        required = node.get("required")
        assert isinstance(required, list) and required, f"{where}: required missing"
        assert len(set(required)) == len(required), f"{where}: duplicate required key"
        assert set(required) == set(props), f"{where}: required must list every property"
        assert not [key for key in required if key not in props], (
            f"{where}: required key is not declared"
        )


def test_root_and_nested_contract_shape():
    schema = result_json_schema()
    assert set(schema["required"]) == {
        "schema_version",
        "status",
        "summary",
        "changed_files",
        "tests_run",
        "unresolved_items",
        "known_risks",
    }
    version = schema["properties"]["schema_version"]
    assert version == {"type": "integer", "enum": [IMPLEMENTATION_RESULT_SCHEMA_VERSION]}
    status = schema["properties"]["status"]
    assert status["type"] == "string"
    assert set(status["enum"]) == {"COMPLETE", "PARTIAL", "BLOCKED", "FAILED"}
    item = schema["properties"]["tests_run"]["items"]
    assert item["additionalProperties"] is False
    assert set(item["required"]) == {"command", "result", "notes"}
    assert set(item["properties"]) == {"command", "result", "notes"}
    assert set(item["properties"]["result"]["enum"]) == {"PASS", "FAIL", "NOT_RUN"}


def test_no_free_form_or_risky_constructs_remain():
    schema = result_json_schema()
    risky = {
        "oneOf", "anyOf", "allOf", "not", "$ref", "patternProperties",
        "unevaluatedProperties", "dependentSchemas", "dependentRequired",
        "propertyNames", "default", "examples", "if", "then", "else",
    }

    def walk(node, where="root"):
        if isinstance(node, dict):
            hits = risky.intersection(node)
            assert not hits, f"{where}: unsupported/risky keyword(s) {sorted(hits)}"
            for key, value in node.items():
                walk(value, f"{where}.{key}")
        elif isinstance(node, list):
            for index, item in enumerate(node):
                walk(item, f"{where}[{index}]")

    walk(schema)
    # no unbounded arbitrary object: arrays are strings/objects, never "items": {}
    assert schema["properties"]["changed_files"]["items"] == {"type": "string"}
    assert schema["properties"]["tests_run"]["items"]["type"] == "object"


# ---------------------------------------------------------------------------
# The offline stub is now as strict as the real endpoint
# ---------------------------------------------------------------------------
def _engine(tmp_path, stub, **over):
    cfg = default_config()
    cfg.tests.targeted = []
    cfg.codex = structured_codex_config(stub, **over)
    provider = CodexCLIProvider(
        cfg.codex, CommandRunner(), workspace_root=str(tmp_path / "ws")
    )
    root, store, engine = build_engine(
        tmp_path,
        config=cfg,
        implementer=provider,
        reviewer=ScriptedAutoReviewer([make_review("PASS")]),
        use_real_git=True,
    )
    engine.create_task("schema strictness")
    engine.import_plan(STATE, make_packet(task_id=STATE))
    return root, store, engine


def test_strict_stub_rejects_the_pre_fix_schema(tmp_path, monkeypatch):
    """Regression: the schema that failed the real smoke must fail offline too."""
    import devrelay.providers.codex_cli as codex_cli

    stub = write_codex_stub(tmp_path / "tools")
    root, store, engine = _engine(tmp_path, stub)
    monkeypatch.setattr(
        codex_cli, "result_json_schema", lambda: json.loads(json.dumps(PRE_FIX_SCHEMA))
    )

    events = engine.continue_task(STATE)
    task = store.read_task(STATE)
    usage = ProviderBudget.usage(task)
    assert task.state.value == "FAILED"
    assert task.blocked_code == "implementer_failed"
    assert usage.implementer_calls == 1 and usage.total_calls == 1  # no hidden repair
    assert task.attempts[-1].completion_ready is False
    assert not (
        store.task_runtime_dir(STATE, task.attempts[-1].attempt_id) / "result.json"
    ).exists()
    assert any("invalid_json_schema" in e or "exit=" in e for e in events), events
    stdout = (store.logs_dir(STATE) / f"{task.attempts[-1].attempt_id}.stdout.log").read_text(
        encoding="utf-8"
    )
    assert "invalid_json_schema" in stdout


def test_strict_schema_runs_end_to_end_with_one_call(tmp_path):
    stub = write_codex_stub(tmp_path / "tools", changed_files=["app.py"])
    root, store, engine = _engine(tmp_path, stub)
    engine.continue_task(STATE)
    task = store.read_task(STATE)
    attempt = task.attempts[-1]
    assert attempt.milestone.value == "COMPLETION_APPLIED"
    assert attempt.completion_ready and attempt.completion_applied
    assert ProviderBudget.usage(task).implementer_calls == 1
    assert (store.task_runtime_dir(STATE, attempt.attempt_id) / "result.json").is_file()


# ---------------------------------------------------------------------------
# Local parser stays defensive (strict transport != weak parser)
# ---------------------------------------------------------------------------
def _payload(**over):
    base = {
        "schema_version": 1,
        "status": "COMPLETE",
        "summary": "done",
        "changed_files": ["app.py"],
        "tests_run": [{"command": "pytest -q", "result": "PASS", "notes": ""}],
        "unresolved_items": [],
        "known_risks": [],
    }
    base.update(over)
    return json.dumps(base).encode("utf-8")


def test_parser_keeps_caps_and_security_after_the_schema_change():
    result, rejected, unknown = parse_result_bytes(_payload())
    assert result.schema_version == 1 and result.status == "COMPLETE"
    assert result.changed_files == ["app.py"] and not unknown and not rejected

    for bad_version in (0, 2, "1", 1.0, True):
        try:
            parse_result_bytes(_payload(schema_version=bad_version))
        except Exception as exc:
            assert "schema_version" in str(exc)
        else:  # pragma: no cover - defensive
            raise AssertionError(f"schema_version {bad_version!r} was accepted")

    try:
        parse_result_bytes(_payload(status="MAYBE"))
    except Exception as exc:
        assert "status" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("bad status accepted")

    long_summary = "x" * 20000
    result, _, _ = parse_result_bytes(_payload(summary=long_summary))
    assert len(result.summary) < len(long_summary)  # cap still enforced

    result, rejected, _ = parse_result_bytes(
        _payload(changed_files=["../../etc/passwd", "C:/windows/system32", "ok.py"])
    )
    assert result.changed_files == ["ok.py"] and len(rejected) == 2

    result, _, unknown = parse_result_bytes(_payload(extra_field="ignored"))
    assert unknown == ["extra_field"]  # recorded by name only, never applied
    assert not hasattr(result, "extra_field")
