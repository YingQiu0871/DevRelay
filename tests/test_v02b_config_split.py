"""v0.2-B stage 2: runtime wiring vs task policy type boundary."""

from __future__ import annotations

import pytest
import yaml

from devrelay.config import (
    DevRelayConfig,
    PolicyDocument,
    ProfileDocument,
    WiringConfig,
    dump_policy_yaml,
    load_config,
    load_policy_snapshot,
    load_workspace_file,
    load_wiring_config,
)
from devrelay.errors import ConfigError
from devrelay.pipeline.policy import PipelinePolicy
from devrelay.pipeline.budget import ProviderBudget

from tests.helpers import build_engine, default_config


def test_wiring_config_shares_no_field_with_policy() -> None:
    wiring_fields = set(WiringConfig.model_fields)
    policy_fields = set(PolicyDocument.model_fields)
    assert wiring_fields & policy_fields == set()
    assert "budget" not in wiring_fields
    assert "pipeline" not in wiring_fields
    assert "provider" not in set(getattr(f, "annotation", "").__name__ and "" for f in [])


def test_policy_document_excludes_wiring_and_selector() -> None:
    names = set(PolicyDocument.model_fields)
    assert names == {
        "pipeline",
        "budget",
        "review",
        "tests",
        "scope",
        "baseline",
        "git",
    }
    assert "profiles" not in names
    assert "codex" not in names
    assert "provider" not in PolicyDocument.model_fields["review"].annotation.model_fields


def test_pipeline_policy_rejects_a_config_object() -> None:
    config = default_config()
    with pytest.raises(TypeError):
        PipelinePolicy(config)  # type: ignore[arg-type]
    PipelinePolicy(PolicyDocument.from_workspace_config(config))  # must not raise


def test_engine_runtime_config_carries_no_policy(tmp_path) -> None:
    _root, _store, engine = build_engine(tmp_path)
    runtime = engine.runtime_config
    assert isinstance(runtime, WiringConfig)
    for attribute in ("budget", "pipeline", "tests", "scope", "baseline", "git"):
        with pytest.raises(AttributeError):
            getattr(runtime, attribute)

def _policy_of(engine) -> PolicyDocument:
    return engine._task_config(engine.store.read_task("DR-0001"))


def test_task_snapshot_is_a_policy_document(tmp_path) -> None:
    _root, store, engine = build_engine(tmp_path)
    engine.create_task("t")
    snapshot = store.task_dir("DR-0001") / "config.snapshot.yaml"
    data = yaml.safe_load(snapshot.read_text(encoding="utf-8"))
    assert set(data) == {
        "pipeline",
        "budget",
        "review",
        "tests",
        "scope",
        "baseline",
        "git",
    }
    assert "codex" not in data and "profiles" not in data
    assert "provider" not in data["review"]
    document, dropped = load_policy_snapshot(
        snapshot.read_bytes(), strict=True, source=str(snapshot)
    )
    assert isinstance(document, PolicyDocument) and dropped == []


def test_profile_document_is_policy_only() -> None:
    for forbidden in (
        {"git": {"allow_push": False}},
        {"codex": {"executable": "codex"}},
        {"review": {"provider": "openai_compatible"}},
        {"profiles": ["base"]},
        {"baseline": {"max_untracked_file_bytes": 10}, "unknown": 1},
    ):
        with pytest.raises(Exception):
            ProfileDocument.model_validate(forbidden)


def test_profile_partial_overrides_keep_only_written_fields() -> None:
    profile = ProfileDocument.model_validate({"budget": {"max_reviewer_calls": 2}})
    assert profile.policy_overrides() == {"budget": {"max_reviewer_calls": 2}}
    base = PolicyDocument.from_workspace_config(default_config())
    merged = PolicyDocument.from_overrides(base, profile.policy_overrides(), source="p")
    assert merged.budget.max_reviewer_calls == 2
    assert merged.budget.max_implementer_calls == base.budget.max_implementer_calls
    assert merged.pipeline == base.pipeline


def test_workspace_selector_is_split_away_from_config(tmp_path) -> None:
    path = tmp_path / ".devrelay" / "config.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("profiles: [base, python]\n", encoding="utf-8")
    workspace = load_workspace_file(path)
    assert workspace.profiles == ["base", "python"]
    config = load_config(path)
    assert isinstance(config, DevRelayConfig)
    assert not hasattr(config, "profiles")
    # ...and the selector can never reach a snapshot or a policy document.
    assert "profiles" not in dump_policy_yaml(
        PolicyDocument.from_workspace_config(config)
    )


def test_wiring_loader_ignores_broken_policy_sections(tmp_path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "budget": {"max_total_provider_calls": "THIS IS NOT AN INTEGER"},
                "pipeline": {"max_fix_iterations": "nope"},
                "review": {"provider": "manual"},
                "codex": {"executable": "codex"},
            }
        ),
        encoding="utf-8",
    )
    wiring = load_wiring_config(path)  # policy sections are not validated here
    assert wiring.review_provider == "manual"
    assert wiring.codex.executable == "codex"
    with pytest.raises(ConfigError):
        load_workspace_file(path)


def test_policy_serialization_is_deterministic() -> None:
    document = PolicyDocument.from_workspace_config(default_config())
    first = dump_policy_yaml(document)
    second = dump_policy_yaml(document)
    assert first == second
    reloaded, dropped = load_policy_snapshot(first.encode("utf-8"), strict=True)
    assert reloaded == document and dropped == []


def test_engine_budget_comes_from_the_policy(tmp_path) -> None:
    config = default_config()
    config.budget.max_reviewer_calls = 3
    _root, _store, engine = build_engine(tmp_path, config=config)
    engine.create_task("t")
    budget = engine._budget_for(engine.store.read_task("DR-0001"))
    assert isinstance(budget, ProviderBudget)
    assert budget.limits.max_reviewer_calls == 3
    # The task's effective policy is a policy *document*, not a config object.
    assert isinstance(_policy_of(engine), PolicyDocument)
