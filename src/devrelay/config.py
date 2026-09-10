"""DevRelay configuration loading and validation."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from devrelay.errors import ConfigError
from devrelay.models import Severity

# The exact same content as profiles/default.yaml at the repository root.
# Loaded via importlib.resources-compatible fallback in _bundled_default().
DEFAULT_PROFILE_NAME = "default.yaml"

DEFAULT_PROFILE_YAML = """\
pipeline:
  max_fix_iterations: 3
  auto_fix_tests: false
  # Stop the loop when the same blocking finding keeps coming back
  # (0 disables; fingerprints are always recorded). v0.2-A.
  max_same_finding_cycles: 0

budget:
  # External provider invocations allowed for one task. Counts are taken from
  # persisted ProviderCallRecord entries, never inferred from iterations.
  max_implementer_calls: 4
  max_reviewer_calls: 4
  max_total_provider_calls: 8

review:
  provider: manual
  blocking_severities: [P0, P1, P2]
  # Format retries: HTTP 200 with non-schema JSON (each retry is a real call).
  retries: 1
  # Transport retries: network/HTTP failures. Default 0 so a flaky endpoint
  # never silently spends reviewer calls.
  transport_retries: 0
  # Reviewer response *parsing/persistence* cap: a larger response is refused
  # (fail closed, never truncated-and-guessed). The HTTP client may buffer the
  # body before this cap is applied - it is NOT a network-level memory limit.
  max_response_chars: 200000
  max_diff_bytes: 300000
  timeout_seconds: 120

baseline:
  # Per-file cap for pre-existing untracked files copied into the baseline.
  # Files above this limit fail task creation with an explicit error.
  max_untracked_file_bytes: 52428800

tests:
  targeted: []
  full: []
  full_regression: release_only
  timeout_seconds: 900

scope:
  reuse_approved_scope: true
  current_delta_first: true

git:
  allow_commit: false
  allow_push: false
  allow_tag: false
  allow_reset_hard: false
  allow_index_mutation: false

codex:
  executable: codex
  # Verified against `codex exec --help` (codex-cli 0.150.1): this CLI does not
  # offer --full-auto; the documented sandbox flag is used instead.  The
  # implementation prompt is streamed on stdin (canonical transport); argv is
  # kept only as an explicit compatibility fallback.
  args: ["exec", "--sandbox", "workspace-write"]
  prompt_mode: stdin
  timeout_seconds: 1800
"""


class PipelineConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_fix_iterations: int = Field(default=3, ge=1)
    auto_fix_tests: bool = False
    # 0 = disabled (default): fingerprints/seen-counts are always recorded, but
    # the loop is never stopped for repetition unless a project opts in.
    max_same_finding_cycles: int = Field(default=0, ge=0, le=10)


class BudgetConfig(BaseModel):
    """External provider call budget for one task (v0.2-A)."""

    model_config = ConfigDict(extra="forbid")

    max_implementer_calls: int = Field(default=4, ge=1)
    max_reviewer_calls: int = Field(default=4, ge=0)
    max_total_provider_calls: int = Field(default=8, ge=1)


class ReviewConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["manual", "openai_compatible"] = "manual"
    blocking_severities: list[Severity] = Field(
        default_factory=lambda: [Severity.P0, Severity.P1, Severity.P2]
    )
    # Format retries (HTTP 200 but not schema-valid JSON).
    retries: int = Field(default=1, ge=0, le=5)
    # Transport retries (network/HTTP failures); separate on purpose.
    transport_retries: int = Field(default=0, ge=0, le=5)
    # Parsing/persistence cap on the reviewer response body (fail closed, never
    # truncate-and-guess). The HTTP client may buffer the body first: this is not
    # a network-level memory limit.
    max_response_chars: int = Field(default=200_000, ge=1_000)
    max_diff_bytes: int = Field(default=300_000, ge=1_000)
    timeout_seconds: float = Field(default=120.0, gt=0)


class TestsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    targeted: list[str] = Field(default_factory=list)
    full: list[str] = Field(default_factory=list)
    full_regression: Literal["release_only", "always", "never"] = "release_only"
    timeout_seconds: float = Field(default=900.0, gt=0)


class ScopeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reuse_approved_scope: bool = True
    current_delta_first: bool = True


class BaselineConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_untracked_file_bytes: int = Field(default=50 * 1024 * 1024, ge=1024)


class GitPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allow_commit: bool = False
    allow_push: bool = False
    allow_tag: bool = False
    allow_reset_hard: bool = False
    allow_index_mutation: bool = False


class CodexConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executable: str = "codex"
    # Defaults verified against codex-cli 0.150.1 `codex exec --help`:
    # prompts travel on stdin (canonical); --full-auto is NOT offered by this
    # CLI version, so the shipped default uses the documented sandbox flag.
    args: list[str] = Field(
        default_factory=lambda: ["exec", "--sandbox", "workspace-write"]
    )
    prompt_mode: Literal["stdin", "argv"] = "stdin"
    timeout_seconds: float = Field(default=1800.0, gt=0)


class DevRelayConfig(BaseModel):
    """Validated DevRelay configuration (workspace .devrelay/config.yaml)."""

    model_config = ConfigDict(extra="forbid")

    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    tests: TestsConfig = Field(default_factory=TestsConfig)
    scope: ScopeConfig = Field(default_factory=ScopeConfig)
    git: GitPolicyConfig = Field(default_factory=GitPolicyConfig)
    baseline: BaselineConfig = Field(default_factory=BaselineConfig)
    codex: CodexConfig = Field(default_factory=CodexConfig)

    @model_validator(mode="after")
    def _hard_git_boundaries(self) -> "DevRelayConfig":
        allowed = {
            "allow_commit": self.git.allow_commit,
            "allow_push": self.git.allow_push,
            "allow_tag": self.git.allow_tag,
            "allow_reset_hard": self.git.allow_reset_hard,
            "allow_index_mutation": self.git.allow_index_mutation,
        }
        enabled = [name for name, value in allowed.items() if value]
        if enabled:
            raise ValueError(
                "DevRelay v0.1 hard-disables automatic git mutations "
                f"({', '.join(sorted(enabled))}); keep these false."
            )
        return self


def bundled_default_path() -> Path:
    """Path of the bundled profile shipped inside the package."""
    return Path(__file__).resolve().parent / "profiles" / DEFAULT_PROFILE_NAME


def bundled_default_yaml() -> str:
    path = bundled_default_path()
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return DEFAULT_PROFILE_YAML


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _parse_yaml(text: str, source: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:  # pragma: no cover - depends on input
        raise ConfigError(f"Invalid YAML in {source}: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"{source} must contain a YAML mapping at top level")
    return data


def load_config(user_config_path: str | Path | None = None) -> DevRelayConfig:
    """Load the bundled defaults merged with the optional workspace profile."""
    defaults = _parse_yaml(bundled_default_yaml(), "bundled default profile")
    merged: dict[str, Any] = defaults
    if user_config_path is not None:
        path = Path(user_config_path)
        if path.is_file():
            user = _parse_yaml(path.read_text(encoding="utf-8"), str(path))
            merged = _deep_merge(defaults, user)
    try:
        return DevRelayConfig.model_validate(merged)
    except Exception as exc:  # pydantic ValidationError etc.
        raise ConfigError(f"Invalid DevRelay configuration: {exc}") from exc


def dump_config_yaml(config: DevRelayConfig) -> str:
    data = config.model_dump(mode="json")
    return yaml.safe_dump(data, sort_keys=False, default_flow_style=False)


def install_default_config(destination: str | Path) -> Path:
    """Write the merged default profile to *destination* (never overwrite)."""
    dest = Path(destination)
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Prefer the human-readable repository profile when running from a source
    # checkout; otherwise use the bundled copy.
    text = bundled_default_yaml()
    dest.write_text(text, encoding="utf-8")
    return dest
