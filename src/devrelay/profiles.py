"""Project profile resolution (v0.2-B).

One workspace policy is resolved from three layers, lowest precedence first::

    packaged policy defaults  <  selected project profiles  <  workspace overrides

``resolve_policy_config`` is the single entry point that produces a
:class:`~devrelay.config.ResolvedPolicy`; nothing else assembles task policy from
files.  Profile files live at ``.devrelay/profiles/<name>.yaml`` and carry
*policy* only - never ``review.provider``, ``codex.*``, ``git.*`` or the
selector, which are runtime wiring / workspace concerns.

Two independent surfaces are exposed here:

* **resolution** (``resolve_policy_config``): full validation, fail closed.
* **raw inspection** (``discover_profiles``/``load_profile``/
  ``validate_profiles``): per-file, never requires a working selector, so the
  diagnostics stay usable when the chain itself is broken.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from devrelay.artifacts.store import encode_lf, sha256_hex
from devrelay.config import (
    BaselineConfig,
    BudgetConfig,
    ConfigError,
    DevRelayConfig,
    PipelineConfig,
    PolicyDocument,
    ProfileDocument,
    ResolvedPolicy,
    ReviewPolicy,
    ScopeConfig,
    TestsConfig,
    WorkspaceFile,
    _parse_yaml_bytes,
    load_workspace_file,
)
from devrelay.errors import (
    ProfileCountExceededError,
    ProfileDuplicateError,
    ProfileError,
    ProfileKeyForbiddenError,
    ProfileNameInvalidError,
    ProfileNotFoundError,
    ProfilePathEscapeError,
    ProfileSelectorError,
    ProfileTooLargeError,
)
from devrelay.models import ProfileRef
from devrelay.snapshot import build_provenance

# The one and only profile name grammar (single source for code, docs, tests).
PROFILE_NAME_PATTERN = r"^[a-z0-9][a-z0-9_-]{0,63}$"
PROFILE_NAME_RE = re.compile(PROFILE_NAME_PATTERN)

MAX_PROFILES = 8
MAX_PROFILE_BYTES = 1024 * 1024
PROFILES_DIRNAME = "profiles"
PROFILE_SUFFIX = ".yaml"

# The profile allowlist, by section.  Anything else in a profile file (git,
# codex, review.provider, profiles, endpoint/model/api-key, executable wiring,
# unknown keys) is rejected: profiles carry policy only.
PROFILE_SECTIONS = {
    "pipeline": PipelineConfig,
    "budget": BudgetConfig,
    "review": ReviewPolicy,
    "tests": TestsConfig,
    "scope": ScopeConfig,
    "baseline": BaselineConfig,
}


def _check_profile_keys(doc: dict, name: str) -> None:
    """Reject any key a project profile may not set (fail closed)."""
    for key, value in doc.items():
        model = PROFILE_SECTIONS.get(key)
        if model is None:
            raise ProfileKeyForbiddenError(
                f"profile {name!r}: key {key!r} is not allowed in a project "
                "profile (runtime wiring, git policy and the selector live in "
                ".devrelay/config.yaml)"
            )
        if value is None:
            continue
        if not isinstance(value, dict):
            raise ProfileError(
                f"profile {name!r}: section {key!r} must be a mapping"
            )
        for sub in value:
            if sub not in model.model_fields:
                raise ProfileKeyForbiddenError(
                    f"profile {name!r}: key {key}.{sub} is not allowed in a "
                    "project profile"
                )


def config_path(root: str | Path) -> Path:
    """``<root>/.devrelay/config.yaml``"""
    return Path(root) / ".devrelay" / "config.yaml"


def profiles_dir(root: str | Path) -> Path:
    return Path(root) / ".devrelay" / PROFILES_DIRNAME


def profile_path(root: str | Path, name: str) -> Path:
    """Contained path of one profile, or a typed error."""
    if not isinstance(name, str) or not PROFILE_NAME_RE.match(name):
        raise ProfileNameInvalidError(
            f"invalid profile name {name!r}: expected {PROFILE_NAME_PATTERN}"
        )
    base = profiles_dir(root)
    path = (base / f"{name}{PROFILE_SUFFIX}").resolve()
    try:
        path.relative_to(base.resolve())
    except ValueError as exc:  # pragma: no cover - regex already blocks '..'
        raise ProfilePathEscapeError(
            f"profile {name!r} resolves outside {base}"
        ) from exc
    return path


def workspace_config_sha256(root: str | Path) -> str:
    """Raw-byte hash of the workspace config file (provenance, not a trust anchor)."""
    path = config_path(root)
    if not path.is_file():
        return ""
    return sha256_hex(path.read_bytes())


# ---------------------------------------------------------------------------
# raw inspection (never needs a working selector)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ProfileEntry:
    """One discovered profile file and its individual validity."""

    name: str
    path: Path
    sha256: str = ""
    ok: bool = True
    error: str = ""


def discover_profiles(root: str | Path) -> tuple[list[str], list[str]]:
    """(valid profile names, filenames that are not valid profiles)."""
    directory = profiles_dir(root)
    if not directory.is_dir():
        return [], []
    names: list[str] = []
    invalid: list[str] = []
    for entry in sorted(directory.iterdir()):
        if entry.is_dir():
            invalid.append(entry.name + "/")
            continue
        if entry.suffix != PROFILE_SUFFIX:
            invalid.append(entry.name)
            continue
        stem = entry.stem
        if not PROFILE_NAME_RE.match(stem):
            invalid.append(entry.name)
            continue
        names.append(stem)
    return names, invalid


def load_profile(root: str | Path, name: str) -> tuple[ProfileDocument, str]:
    """Load exactly one profile: (document, sha256 of its bytes)."""
    path = profile_path(root, name)
    if not path.is_file():
        raise ProfileNotFoundError(f"profile {name!r} not found at {path}")
    data = path.read_bytes()
    if len(data) > MAX_PROFILE_BYTES:
        raise ProfileTooLargeError(
            f"profile {name!r} is {len(data)} bytes (limit {MAX_PROFILE_BYTES})"
        )
    doc = _parse_yaml_bytes(data, str(path))
    _check_profile_keys(doc, name)
    try:
        profile = ProfileDocument.model_validate(doc)
    except Exception as exc:
        raise ProfileError(f"profile {name!r} is invalid: {exc}") from exc
    return profile, sha256_hex(data)


def inspect_profile(root: str | Path, name: str) -> ProfileEntry:
    """Raw, individually-failing inspection of one profile."""
    try:
        path = profile_path(root, name)
    except ProfileError as exc:
        return ProfileEntry(name=name, path=profiles_dir(root), ok=False, error=str(exc))
    try:
        _profile, digest = load_profile(root, name)
    except ProfileError as exc:
        exists = path if path.is_file() else path
        return ProfileEntry(name=name, path=exists, ok=False, error=str(exc))
    return ProfileEntry(name=name, path=path, sha256=digest, ok=True)


@dataclass
class ProfileReport:
    """Collect-all diagnostics: every problem, not just the first."""

    selector_raw: list[str] = field(default_factory=list)
    entries: list[ProfileEntry] = field(default_factory=list)
    invalid_filenames: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    composed: bool = False

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_selector(selector: list[str]) -> None:
    """Raw selector syntax: names, count, duplicates (fail closed)."""
    if not isinstance(selector, list):
        raise ProfileSelectorError("profiles must be a list of profile names")
    if len(selector) > MAX_PROFILES:
        raise ProfileCountExceededError(
            f"selector lists {len(selector)} profiles (limit {MAX_PROFILES})"
        )
    seen: set[str] = set()
    for name in selector:
        if not isinstance(name, str) or not PROFILE_NAME_RE.match(name):
            raise ProfileNameInvalidError(
                f"invalid profile name {name!r} in the selector: expected "
                f"{PROFILE_NAME_PATTERN}"
            )
        if name in seen:
            raise ProfileDuplicateError(f"profile {name!r} is selected twice")
        seen.add(name)


def validate_profiles(root: str | Path) -> ProfileReport:
    """Validate every discovered profile plus the raw selector (collect-all)."""
    root = Path(root)
    report = ProfileReport()
    names, invalid = discover_profiles(root)
    report.invalid_filenames = invalid
    for filename in invalid:
        report.errors.append(
            f"ignored {profiles_dir(root) / filename}: not a valid profile file "
            f"(expected <name>{PROFILE_SUFFIX} with name {PROFILE_NAME_PATTERN})"
        )
    report.entries = [inspect_profile(root, name) for name in names]
    for entry in report.entries:
        if not entry.ok:
            report.errors.append(entry.error)

    try:
        workspace = load_workspace_file(config_path(root))
    except ConfigError as exc:
        report.errors.append(str(exc))
        return report
    report.selector_raw = list(workspace.profiles)

    missing = [name for name in report.selector_raw if name not in names]
    for name in missing:
        report.errors.append(
            f"selector references profile {name!r}, which does not exist at "
            f"{profiles_dir(root) / (name + PROFILE_SUFFIX)}"
        )
    if missing:
        # Still validate everything else; composition is reported separately.
        return report
    try:
        validate_selector(report.selector_raw)
        compose_policy(root, workspace)
    except ProfileError as exc:
        report.errors.append(str(exc))
        return report
    report.composed = True
    return report


def compose_policy(
    root: str | Path, workspace: WorkspaceFile
) -> tuple[PolicyDocument, list[ProfileRef]]:
    """Compose the policy document: packaged defaults < profiles < overrides."""
    from devrelay.config import packaged_default_policy, workspace_policy_overrides

    validate_selector(list(workspace.profiles))
    document = packaged_default_policy()
    refs: list[ProfileRef] = []
    for name in workspace.profiles:
        profile, digest = load_profile(root, name)
        refs.append(ProfileRef(name=name, sha256=digest))
        document = PolicyDocument.from_overrides(
            document, profile.policy_overrides(), source=f"profile {name!r}"
        )
    overrides = workspace_policy_overrides(root)
    document = PolicyDocument.from_overrides(
        document, overrides, source=str(config_path(root))
    )
    return document, refs


def resolve_policy_config(root: str | Path) -> ResolvedPolicy:
    """Resolve the live workspace policy (full validation, fail closed).

    The caller is creating a task, refreshing/recovering a task policy, or
    explicitly asking for the effective chain.  Execution of a task with a valid
    frozen snapshot never calls this.
    """
    root = Path(root)
    workspace = load_workspace_file(config_path(root))
    document, refs = compose_policy(root, workspace)
    provenance = build_provenance(
        generation=1,
        selector_raw=list(workspace.profiles),
        profiles=refs,
        workspace_config_sha256=workspace_config_sha256(root),
        integrity="live_resolution",
    )
    return ResolvedPolicy(
        document=document, provenance=provenance, source="live-fallback"
    )


def resolved_live_config(root: str | Path) -> DevRelayConfig:
    """The workspace document with profiles applied (for display/diagnostics)."""
    return load_workspace_file(config_path(root))
