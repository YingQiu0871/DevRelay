"""Configuration tests: defaults, merging, strict validation."""

import pytest
import yaml

from devrelay.config import (
    DevRelayConfig,
    dump_config_yaml,
    load_config,
)
from devrelay.errors import ConfigError


def test_default_config_values():
    config = load_config(None)
    assert config.pipeline.max_fix_iterations == 3
    assert config.pipeline.auto_fix_tests is False
    assert config.review.provider == "manual"
    assert [s.value for s in config.review.blocking_severities] == ["P0", "P1", "P2"]
    assert config.review.retries == 1
    assert config.review.max_diff_bytes == 300_000
    assert config.tests.full_regression == "release_only"
    assert config.tests.timeout_seconds == 900
    assert config.scope.reuse_approved_scope is True
    assert config.scope.current_delta_first is True
    assert config.codex.executable == "codex"
    assert config.codex.args == ["exec", "--full-auto"]
    assert config.codex.prompt_mode == "stdin"
    assert config.codex.timeout_seconds == 1800
    assert config.git.allow_commit is False
    assert config.git.allow_push is False


def test_user_config_deep_merges(tmp_path):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        yaml.safe_dump(
            {
                "pipeline": {"max_fix_iterations": 2},
                "tests": {"targeted": ["pytest -q"], "timeout_seconds": 5},
            }
        ),
        encoding="utf-8",
    )
    config = load_config(cfg_path)
    assert config.pipeline.max_fix_iterations == 2
    # untouched sibling sections keep defaults
    assert config.pipeline.auto_fix_tests is False
    assert config.tests.targeted == ["pytest -q"]
    assert config.tests.timeout_seconds == 5
    assert config.tests.full_regression == "release_only"


def test_dump_roundtrip():
    config = load_config(None)
    text = dump_config_yaml(config)
    reloaded = load_config_from_text(text)
    assert reloaded == config


def load_config_from_text(text: str):
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.yaml"
        path.write_text(text, encoding="utf-8")
        return load_config(path)


def test_unknown_top_level_key_rejected(tmp_path):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("unknown_section:\n  a: 1\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(cfg_path)


def test_unknown_nested_key_rejected(tmp_path):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        yaml.safe_dump({"codex": {"sneaky_flag": True}}), encoding="utf-8"
    )
    with pytest.raises(ConfigError):
        load_config(cfg_path)


def test_invalid_blocking_severity_rejected(tmp_path):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        yaml.safe_dump({"review": {"blocking_severities": ["P0", "P9"]}}),
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_config(cfg_path)


def test_invalid_yaml_rejected(tmp_path):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("pipeline: [unclosed", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(cfg_path)


def test_zero_max_iterations_rejected(tmp_path):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        yaml.safe_dump({"pipeline": {"max_fix_iterations": 0}}), encoding="utf-8"
    )
    with pytest.raises(ConfigError):
        load_config(cfg_path)


def test_git_mutations_hard_disabled(tmp_path):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        yaml.safe_dump({"git": {"allow_push": True}}), encoding="utf-8"
    )
    with pytest.raises(ConfigError):
        load_config(cfg_path)


def test_missing_user_config_is_ok(tmp_path):
    config = load_config(tmp_path / "does-not-exist.yaml")
    assert config.pipeline.max_fix_iterations == 3
