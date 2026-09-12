"""DevRelay configuration loading and validation."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from devrelay.artifacts.store import encode_lf
from devrelay.errors import ConfigError
from devrelay.models import PolicyProvenance, Severity

# The packaged default policy file (the only default authority).
DEFAULT_PROFILE_NAME = "default.yaml"



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
    # Fixed launcher prefix for wrapper scripts / alternative entry points
    # (e.g. ["python", "wrapper.py"]).  Never a runtime-control surface: the
    # same argument-ownership validation applies to it.
    launcher_args: list[str] = Field(default_factory=list)
    # Defaults verified against codex-cli 0.150.1 `codex exec --help`:
    # prompts travel on stdin (canonical); --full-auto is NOT offered by this
    # CLI version, so the shipped default uses the documented sandbox flag.
    args: list[str] = Field(
        default_factory=lambda: ["exec", "--sandbox", "workspace-write"]
    )
    prompt_mode: Literal["stdin", "argv"] = "stdin"
    timeout_seconds: float = Field(default=1800.0, gt=0)
    # v0.2-C: structured Codex runtime is the default; `text` is the explicit,
    # visible compatibility opt-out (never an automatic downgrade).
    runtime_mode: Literal["structured", "text"] = "structured"
    # Bounded reads/captures for the structured runtime (bytes).
    max_result_bytes: int = Field(default=262_144, ge=1_024, le=8_388_608)
    max_capture_bytes: int = Field(default=262_144, ge=1_024, le=8_388_608)

    @model_validator(mode="after")
    def _validate_argument_ownership(self) -> "CodexConfig":
        # Imported lazily: codex_runtime imports models, not config.
        from devrelay.providers.codex_runtime import validate_user_args

        validate_user_args(self.args, launcher_args=self.launcher_args)
        return self


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


# ---------------------------------------------------------------------------
# v0.2-B: runtime wiring vs task policy
#
# Runtime wiring (WiringConfig)  = which local tool/endpoint runs and how it is
#                                  invoked.  Live, environment-specific, never
#                                  frozen and never supplied by a profile.
# Task policy (PolicyDocument)   = everything that decides blocking, budget
#                                  consumption, test policy and the git guard.
#                                  Resolved once, frozen into the task.
# ---------------------------------------------------------------------------


class ReviewPolicy(BaseModel):
    """Review knobs that are task policy.

    ``review.provider`` is deliberately absent: provider selection is runtime
    wiring, so a project profile can never switch the reviewer backend.
    """

    model_config = ConfigDict(extra="forbid")

    blocking_severities: list[Severity] = Field(
        default_factory=lambda: [Severity.P0, Severity.P1, Severity.P2]
    )
    retries: int = Field(default=1, ge=0, le=5)
    transport_retries: int = Field(default=0, ge=0, le=5)
    max_response_chars: int = Field(default=200_000, ge=1_000)
    max_diff_bytes: int = Field(default=300_000, ge=1_000)
    timeout_seconds: float = Field(default=120.0, gt=0)


class FrozenBudget(BudgetConfig):
    """A budget carried by a resolved :class:`PolicyDocument`.

    The marker subclass lets the execution path assert that the limits it
    enforces came from a policy resolution, never from live wiring/workspace
    defaults.
    """


class WiringConfig(BaseModel):
    """Live runtime wiring: how DevRelay talks to the outside world.

    Deliberately contains **no** policy field, so ``self.runtime_config`` can
    never become a policy fallback: there is no budget, severity list or test
    policy to read from it.
    """

    model_config = ConfigDict(extra="forbid")

    review_provider: Literal["manual", "openai_compatible"] = "manual"
    codex: CodexConfig = Field(default_factory=CodexConfig)

    @classmethod
    def from_workspace_config(cls, config: "DevRelayConfig") -> "WiringConfig":
        return cls(review_provider=config.review.provider, codex=config.codex)


class PolicyDocument(BaseModel):
    """The resolved, frozen task policy (the only policy authority).

    Serialized verbatim into ``tasks/<id>/config.snapshot.yaml``; contains no
    selector, no provider, no codex and no other wiring.
    """

    model_config = ConfigDict(extra="forbid")

    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    budget: FrozenBudget = Field(default_factory=FrozenBudget)
    review: ReviewPolicy = Field(default_factory=ReviewPolicy)
    tests: TestsConfig = Field(default_factory=TestsConfig)
    scope: ScopeConfig = Field(default_factory=ScopeConfig)
    baseline: BaselineConfig = Field(default_factory=BaselineConfig)
    git: GitPolicyConfig = Field(default_factory=GitPolicyConfig)

    @model_validator(mode="after")
    def _hard_git_boundaries(self) -> "PolicyDocument":
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

    @classmethod
    def from_workspace_config(cls, config: "DevRelayConfig") -> "PolicyDocument":
        """Policy view of a workspace document (wiring sections are dropped)."""
        return cls(
            pipeline=config.pipeline.model_copy(deep=True),
            budget=FrozenBudget(**config.budget.model_dump()),
            review=ReviewPolicy(
                **{
                    name: getattr(config.review, name)
                    for name in ReviewPolicy.model_fields
                }
            ),
            tests=config.tests.model_copy(deep=True),
            scope=config.scope.model_copy(deep=True),
            baseline=config.baseline.model_copy(deep=True),
            git=config.git.model_copy(deep=True),
        )

    @classmethod
    def from_overrides(
        cls, base: "PolicyDocument", overrides: dict[str, Any], *, source: str
    ) -> "PolicyDocument":
        """Deep-merge partial policy overrides onto *base* (lists replace)."""
        if not overrides:
            return base.model_copy(deep=True)
        merged = _deep_merge(base.model_dump(mode="python"), overrides)
        try:
            return cls.model_validate(merged)
        except Exception as exc:
            raise ConfigError(f"invalid policy overrides in {source}: {exc}") from exc


class ProfileDocument(BaseModel):
    """A project profile file: partial policy only.

    Sections are optional; ``model_dump(exclude_unset=True)`` yields exactly
    what the file wrote, which is what the merge applies.  The model itself is
    the allowlist: ``git``, ``codex``, ``review.provider`` and ``profiles`` are
    not fields, so ``extra="forbid"`` rejects them inside a profile.
    """

    model_config = ConfigDict(extra="forbid")

    pipeline: Optional[PipelineConfig] = None
    budget: Optional[BudgetConfig] = None
    review: Optional[ReviewPolicy] = None
    tests: Optional[TestsConfig] = None
    scope: Optional[ScopeConfig] = None
    baseline: Optional[BaselineConfig] = None

    def policy_overrides(self) -> dict[str, Any]:
        return self.model_dump(exclude_unset=True, exclude_none=True, mode="python")


class WorkspaceFile(DevRelayConfig):
    """Parsed ``.devrelay/config.yaml``: wiring + policy overrides + selector.

    ``profiles`` is a workspace-level field.  It is split away from the
    :class:`DevRelayConfig` view by :func:`load_workspace_file`, and it is not a
    member of :class:`PolicyDocument`, so it can never be frozen into a task
    snapshot or handed to the engine as task policy.
    """

    profiles: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class ResolvedPolicy:
    """A policy document plus the provenance that produced it."""

    document: PolicyDocument
    provenance: PolicyProvenance
    source: str = "live-fallback"

    @classmethod
    def from_workspace_config(
        cls, config: "DevRelayConfig", *, generation: int = 1
    ) -> "ResolvedPolicy":
        document = PolicyDocument.from_workspace_config(config)
        return cls(
            document=document,
            provenance=PolicyProvenance(
                generation=generation, integrity="workspace_overrides"
            ),
            source="live-fallback",
        )


def bundled_default_path() -> Path:
    """Path of the bundled profile shipped inside the package."""
    return Path(__file__).resolve().parent / "profiles" / DEFAULT_PROFILE_NAME


def bundled_default_yaml() -> str:
    """The single editable default policy authority, shipped in the package."""
    path = bundled_default_path()
    if not path.is_file():  # pragma: no cover - packaging failure
        raise ConfigError(
            f"packaged default policy is missing: {path}. "
            "Reinstall DevRelay; there is deliberately no in-code fallback."
        )
    return path.read_text(encoding="utf-8")


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


def _parse_yaml_bytes(data: bytes, source: str) -> dict[str, Any]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ConfigError(f"{source} is not valid UTF-8: {exc}") from exc
    return _parse_yaml(text, source)


def _merge_bundled_defaults(user_path: Path | None) -> dict[str, Any]:
    defaults = _parse_yaml(bundled_default_yaml(), "bundled default profile")
    if user_path is not None and user_path.is_file():
        user = _parse_yaml(user_path.read_text(encoding="utf-8"), str(user_path))
        return _deep_merge(defaults, user)
    return defaults


def load_workspace_file(user_config_path: str | Path | None = None) -> WorkspaceFile:
    """Load the workspace document: bundled defaults < workspace config file.

    Unlike :func:`load_config`, the ``profiles`` selector is visible here (it is
    a workspace-level input) and is stripped from the returned
    :class:`DevRelayConfig` view.
    """
    path = Path(user_config_path) if user_config_path is not None else None
    merged = _merge_bundled_defaults(path)
    try:
        return WorkspaceFile.model_validate(merged)
    except Exception as exc:  # pydantic ValidationError etc.
        raise ConfigError(f"Invalid DevRelay configuration: {exc}") from exc


def load_config(user_config_path: str | Path | None = None) -> DevRelayConfig:
    """Backward-compatible view: the workspace document without the selector."""
    workspace = load_workspace_file(user_config_path)
    return DevRelayConfig.model_validate(
        workspace.model_dump(exclude={"profiles"}, mode="python")
    )


def load_wiring_config(root_or_path: str | Path) -> WiringConfig:
    """Load live runtime wiring only.

    Policy sections (``pipeline``/``budget``/policy ``review`` knobs/``tests``/
    ``scope``/``baseline``) are deliberately **not** validated here: a malformed
    live policy override must never become an execution prerequisite for a task
    that already owns a frozen snapshot.  Whole-file YAML that cannot be parsed
    at all is still an error, because wiring cannot be extracted from it.
    """
    path = Path(root_or_path)
    if path.is_dir():
        path = path / ".devrelay" / "config.yaml"
    if not path.is_file():
        return WiringConfig()
    data = _parse_yaml_bytes(path.read_bytes(), str(path))
    review = data.get("review")
    if review is not None and not isinstance(review, dict):
        raise ConfigError(
            f"Invalid DevRelay configuration: review must be a mapping in {path}"
        )
    provider: Any = "manual"
    if isinstance(review, dict) and "provider" in review:
        provider = review["provider"]
    try:
        return WiringConfig(review_provider=provider, codex=data.get("codex", {}))
    except Exception as exc:
        raise ConfigError(f"Invalid DevRelay runtime wiring in {path}: {exc}") from exc


def packaged_default_policy() -> PolicyDocument:
    """The packaged default *policy* (wiring keys in the file are ignored)."""
    data = bundled_default_yaml().encode("utf-8")
    document, _dropped = load_policy_snapshot(
        data, strict=False, source="bundled default profile"
    )
    return document


def workspace_policy_overrides(root_or_path: str | Path) -> dict[str, Any]:
    """Policy overrides the user actually wrote in ``.devrelay/config.yaml``.

    Only the user's own keys count: the packaged defaults must stay *below* the
    profiles in the precedence order, and the selector/wiring are not policy.
    The file as a whole was already validated by :func:`load_workspace_file`.
    """
    path = Path(root_or_path)
    if path.is_dir():
        path = path / ".devrelay" / "config.yaml"
    if not path.is_file():
        return {}
    data = _parse_yaml_bytes(path.read_bytes(), str(path))
    data.pop("profiles", None)
    data.pop("codex", None)
    review = data.get("review")
    if isinstance(review, dict):
        review.pop("provider", None)
        if not review:
            data.pop("review")
    return data


def dump_policy_yaml(document: PolicyDocument) -> str:
    """Deterministic policy serialization (stable key order, LF, no aliases)."""
    data = document.model_dump(mode="json")
    return yaml.safe_dump(data, sort_keys=False, default_flow_style=False)


def load_policy_snapshot(
    data_or_path: bytes | str | Path, *, strict: bool = True, source: str = ""
) -> tuple[PolicyDocument, list[str]]:
    """Parse a policy snapshot document, returning (document, dropped_keys).

    ``strict=True`` is the schema-5 rule: the document must be exactly a policy
    document (any unknown key fails closed).  ``strict=False`` is the approved
    legacy tolerance for digest-less v0.2-A snapshots, which were a full
    workspace-config dump: only the known wiring keys ``codex``, ``profiles``
    and ``review.provider`` are dropped - any other unknown key still fails.
    """
    if isinstance(data_or_path, (str, Path)):
        path = Path(data_or_path)
        source = source or str(path)
        data = path.read_bytes()
    else:
        data = data_or_path
    doc = _parse_yaml_bytes(data, source or "policy snapshot")
    dropped: list[str] = []
    if not strict:
        if "codex" in doc:
            doc.pop("codex")
            dropped.append("codex")
        if "profiles" in doc:
            doc.pop("profiles")
            dropped.append("profiles")
        review = doc.get("review")
        if isinstance(review, dict) and "provider" in review:
            review.pop("provider")
            dropped.append("review.provider")
    try:
        return PolicyDocument.model_validate(doc), dropped
    except Exception as exc:
        raise ConfigError(f"invalid policy snapshot {source}: {exc}") from exc


def dump_config_yaml(config: DevRelayConfig) -> str:
    data = config.model_dump(mode="json")
    return yaml.safe_dump(data, sort_keys=False, default_flow_style=False)


WORKSPACE_CONFIG_TEMPLATE = """# DevRelay workspace configuration (installed once by `devrelay init`).
#
# This file is runtime wiring plus optional policy overrides.  Reusable policy
# belongs in .devrelay/profiles/<name>.yaml, selected by `profiles:` below.
#
# Precedence:  packaged policy defaults  <  profiles (in order)  <  the policy
#              overrides written here
#
# A task freezes the resolved policy at `devrelay start`; editing this file
# afterwards never changes a running task (an explicit, audited
# `devrelay unblock --refresh-policy` is required).

# Project profiles, applied in order (later wins).  Profile files may set
# pipeline / budget / review policy / tests / scope / baseline - never
# review.provider, codex.*, git.* or this selector.
profiles: []

# ---- runtime wiring (environment-specific, live, never frozen) -------------
review:
  # manual | openai_compatible
  provider: manual

codex:
  executable: codex
  # Verified against `codex exec --help` (codex-cli 0.150.1): no --full-auto.
  args: ["exec", "--sandbox", "workspace-write"]
  prompt_mode: stdin
  timeout_seconds: 1800

# ---- optional policy overrides (uncomment what this workspace pins) --------
# budget:
#   max_reviewer_calls: 2
#   max_total_provider_calls: 6
# tests:
#   targeted: ["pytest -q"]
#   full: []
# scope:
#   reuse_approved_scope: true
"""


def install_default_config(destination: str | Path) -> Path:
    """Write the workspace config template to *destination* (never overwrite).

    The template carries live wiring, the (empty) profile selector and commented
    policy-override examples - not the policy defaults, which stay editable in
    exactly one place: the packaged ``profiles/default.yaml``.
    """
    dest = Path(destination)
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(encode_lf(WORKSPACE_CONFIG_TEMPLATE))
    return dest
