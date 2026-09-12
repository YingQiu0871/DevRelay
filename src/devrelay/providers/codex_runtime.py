"""Codex structured runtime (v0.2-C).

DevRelay owns the runtime-safety, isolation and evidence flags of the Codex
invocation; the model may only fill in a JSON object the *parent* validates and
sanitizes.  Nothing here spawns a process - the provider does that through the
single audited :class:`~devrelay.workspace.runner.CommandRunner`.

Trust rules:

* the structured result is **advisory** evidence; the worktree delta, Git guard
  and DevRelay-run tests remain authoritative;
* raw model bytes never become durable evidence - they live in an
  attempt-scoped staging file, are read with a hard cap, hashed, sanitized and
  only then persisted;
* every failure mode fails closed: no invisible repair call, no silent
  downgrade from structured to text mode.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

from pydantic import ValidationError

from devrelay.errors import DevRelayError
from devrelay.models import (
    IMPLEMENTATION_RESULT_SCHEMA_VERSION,
    ImplementationResult,
    TestClaim,
    utcnow_iso,
)
from devrelay.redact import sanitize

# ---------------------------------------------------------------------------
# argument ownership
# ---------------------------------------------------------------------------
LEGACY_DEFAULT_ARGS = ["exec", "--sandbox", "workspace-write"]

DEVRELAY_OWNED_FLAGS = (
    "exec",
    "--sandbox",
    "--ignore-user-config",
    "--ignore-rules",
    "--json",
    "--output-schema",
    "--output-last-message",
)

FORBIDDEN_FLAGS = (
    "-p",
    "--profile",
    "--sandbox",
    "--dangerously-bypass-approvals-and-sandbox",
    "--dangerously-bypass-hook-trust",
    "--add-dir",
    "--cd",
    "-C",
    "--skip-git-repo-check",
    "--approve-for-me",
    "--oss",
    "--local-provider",
    "-i",
    "--image",
    "--output-schema",
    "--output-last-message",
    "-o",
    "--json",
)

# Only these ``-c key=value`` namespaces survive; everything safety-relevant
# (sandbox/approval/exec/tools/mcp/plugins/providers/projects/features/shell
# environment policy) is rejected so no indirect config can weaken the runtime.
ALLOWED_CONFIG_KEYS = frozenset(
    {
        "model",
        "model_reasoning_effort",
        "model_reasoning_summary",
        "model_verbosity",
        "hide_agent_reasoning",
        "show_raw_agent_reasoning",
        "disable_response_storage",
    }
)

FORBIDDEN_CONFIG_PREFIXES = (
    "sandbox",
    "approval",
    "exec",
    "tools",
    "mcp_servers",
    "plugins",
    "model_providers",
    "projects",
    "features",
    "shell_environment_policy",
    "notify",
    "windows",
    "desktop",
)

# Credentials DevRelay knows must never reach the Codex child.  This is an
# explicit denylist, NOT general secret isolation: ambient user secrets such as
# AWS_SECRET_ACCESS_KEY / GITHUB_TOKEN / NPM_TOKEN stay visible and are
# documented as outside the v0.2-C boundary.
CODEX_CHILD_ENV_DENYLIST = (
    "DEVRELAY_REVIEWER_API_KEY",
    "DEVRELAY_REVIEWER_BASE_URL",
    "DEVRELAY_REVIEWER_MODEL",
    "OPENAI_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "MISTRAL_API_KEY",
    "COHERE_API_KEY",
    "DEEPSEEK_API_KEY",
    "OPENROUTER_API_KEY",
    "TOGETHER_API_KEY",
)

REPO_CODEX_CONFIG_CANDIDATES = (
    ".codex/config.toml",
    ".codex/config.json",
    "codex.toml",
)

RESULT_STATUSES = ("COMPLETE", "PARTIAL", "BLOCKED", "FAILED")
MAX_SUMMARY_CHARS = 8000
MAX_CLAIMED_FILES = 500
MAX_CLAIM_ENTRY_CHARS = 1024
MAX_TEST_CLAIMS = 100
MAX_LIST_ITEMS = 50
MAX_LIST_ITEM_CHARS = 500
MAX_UNKNOWN_FIELDS = 50
MAX_UNKNOWN_FIELD_NAME_CHARS = 100


class CodexRuntimeError(DevRelayError):
    """Runtime/configuration problem detected before or around a Codex run."""

    code = "codex_runtime_error"


class CodexRuntimeUnsupportedError(CodexRuntimeError):
    code = "codex_runtime_unsupported"


class CodexContainmentUnsupportedError(CodexRuntimeUnsupportedError):
    """Structured runtime requires strong descendant containment that this host
    cannot provide; refusing pre-flight (0 provider calls) instead of running a
    guard that a detached descendant could outlive."""

    code = "codex_process_containment_unsupported"


class CodexResultError(CodexRuntimeError):
    """Structured result problem (missing/malformed/oversized/unsupported)."""

    code = "codex_result_malformed"


class CodexResultMissingError(CodexResultError):
    code = "codex_result_missing"


class CodexResultTooLargeError(CodexResultError):
    code = "codex_result_too_large"


class CodexRuntimeArtifactCollisionError(CodexRuntimeError):
    code = "codex_runtime_artifact_collision"


class CodexArgumentError(DevRelayError):
    code = "codex_argument_rejected"


# ---------------------------------------------------------------------------
# capability detection (help text only - never a model call)
# ---------------------------------------------------------------------------
@dataclass
class CodexCapabilities:
    present: bool = False
    version: str = ""
    flags: frozenset[str] = frozenset()
    diagnostic: str = ""

    @property
    def supports_output_schema(self) -> bool:
        return "--output-schema" in self.flags

    @property
    def supports_last_message(self) -> bool:
        return "--output-last-message" in self.flags or "-o" in self.flags

    @property
    def supports_json_events(self) -> bool:
        return "--json" in self.flags

    @property
    def supports_ignore_user_config(self) -> bool:
        return "--ignore-user-config" in self.flags

    @property
    def structured_supported(self) -> bool:
        return bool(
            self.present
            and self.supports_output_schema
            and self.supports_last_message
        )

    def missing_structured_flags(self) -> list[str]:
        missing = []
        if not self.supports_output_schema:
            missing.append("--output-schema")
        if not self.supports_last_message:
            missing.append("--output-last-message")
        return missing

    def describe(self) -> str:
        if not self.present:
            return "Codex CLI not available"
        supported = "supported" if self.structured_supported else "unsupported"
        extra = (
            ""
            if self.structured_supported
            else " (missing: " + ", ".join(self.missing_structured_flags()) + ")"
        )
        return f"structured runtime {supported}{extra}"


def parse_help_flags(help_text: str) -> frozenset[str]:
    flags = set()
    for line in help_text.splitlines():
        for match in re.finditer(r"(?<![A-Za-z0-9])(--[a-z0-9-]+|-[a-z])\b", line):
            flags.add(match.group(1).lower())
    return frozenset(flags)


def detect_capabilities(
    runner, executable: str, launcher_args: Sequence[str] = ()
) -> CodexCapabilities:
    """Probe the installed CLI via `--version` and `exec --help` only.

    A configured launcher prefix (wrapper script) is part of the executable
    surface, so every probe runs through it exactly like the real invocation.
    """
    prefix = [executable, *launcher_args]
    if not runner.which(executable):
        return CodexCapabilities(present=False, diagnostic="executable not found")
    version = runner.run([*prefix, "--version"], timeout_seconds=30)
    text = (version.stdout or "").strip()
    if not version.success:
        return CodexCapabilities(
            present=False,
            diagnostic=(
                "version probe failed: "
                + ((version.stderr or version.error or "").strip()[:200])
            ),
        )
    help_result = runner.run([*prefix, "exec", "--help"], timeout_seconds=60)
    flags = parse_help_flags(help_result.stdout or "") if help_result.success else frozenset()
    return CodexCapabilities(present=True, version=text, flags=flags)


def detect_repo_codex_config(workspace_root: Path) -> list[str]:
    """In-repo Codex configuration files (structured mode refuses them)."""
    found: list[str] = []
    root = Path(workspace_root)
    for candidate in REPO_CODEX_CONFIG_CANDIDATES:
        path = root / candidate
        if path.exists():
            found.append(candidate)
    return found


# ---------------------------------------------------------------------------
# argv building / validation
# ---------------------------------------------------------------------------
def _config_key(token: str) -> str:
    return token.split("=", 1)[0].strip().lower()


def validate_user_args(args: Sequence[str], *, launcher_args: Sequence[str] = ()) -> None:
    """Reject user args/launcher tokens that could weaken the runtime.

    The shipped default ``args`` (``exec --sandbox workspace-write``) is
    recognised and normalised away, so existing configurations keep working even
    when a launcher prefix (wrapper script) is configured.  Launcher tokens get
    no such exemption: they are a fixed prefix, never a runtime-control surface.
    """
    if list(launcher_args):
        _scan_for_forbidden(list(launcher_args))
    if list(args) == LEGACY_DEFAULT_ARGS:
        return
    _scan_for_forbidden(list(args))


def _scan_for_forbidden(tokens: Sequence[str]) -> None:
    for index, token in enumerate(tokens):
        name = token.split("=", 1)[0].lower()
        if name in ("-c", "--config"):
            value = token.split("=", 1)[1] if "=" in token else None
            if value is None and index + 1 < len(tokens):
                value = tokens[index + 1]
            if value is None:
                raise CodexArgumentError("codex config override is missing a key")
            key = _config_key(value)
            if key not in ALLOWED_CONFIG_KEYS:
                raise CodexArgumentError(
                    f"codex config override '-c {key}=...' is not allowed in "
                    "v0.2-C; safety-relevant configuration is owned by DevRelay"
                )
            continue
        if token.startswith("--config="):
            key = _config_key(token.split("=", 1)[1])
            if key not in ALLOWED_CONFIG_KEYS:
                raise CodexArgumentError(
                    f"codex config override '--config={key}=...' is not allowed"
                )
            continue
        if name in FORBIDDEN_FLAGS:
            raise CodexArgumentError(
                f"codex argument '{name}' is owned or forbidden in v0.2-C "
                "(DevRelay owns sandbox, isolation, output-path and result flags)"
            )
        if token.startswith("-c") and token != "-c" and not token.startswith("--"):
            value = token[2:]
            key = _config_key(value)
            if key not in ALLOWED_CONFIG_KEYS:
                raise CodexArgumentError(
                    f"codex config override '-c{key}=...' is not allowed in v0.2-C"
                )
    for token in tokens:
        if token.startswith("-") and not token.startswith("--") and token not in ("-c",):
            name = token.split("=", 1)[0]
            if name in FORBIDDEN_FLAGS:
                raise CodexArgumentError(
                    f"codex argument '{name}' is forbidden in v0.2-C"
                )


def _user_passthrough(args: Sequence[str]) -> list[str]:
    """User args minus the recognised legacy default/`exec` subcommand."""
    if list(args) == LEGACY_DEFAULT_ARGS:
        return []
    passthrough: list[str] = []
    for token in args:
        if token == "exec":
            continue
        passthrough.append(token)
    return passthrough


@dataclass
class CodexInvocation:
    """The exact, deterministic invocation DevRelay will run."""

    argv: list[str]
    env_remove: list[str]
    runtime_mode: str
    staging_path: str
    schema_path: str
    workdir: str
    prompt_sha256: str
    capabilities: CodexCapabilities = field(default_factory=CodexCapabilities)

    def describe(self) -> dict[str, Any]:
        return {
            "argv": list(self.argv),
            "argv_sha256": hashlib.sha256(
                "\0".join(self.argv).encode("utf-8")
            ).hexdigest(),
            "runtime_mode": self.runtime_mode,
            "workdir": self.workdir,
            "prompt_sha256": self.prompt_sha256,
            "env_removed": list(self.env_remove),
            "staging_path": self.staging_path,
            "schema_path": self.schema_path,
            "codex_version": self.capabilities.version,
            "structured_supported": self.capabilities.structured_supported,
        }


def build_invocation(
    *,
    config,
    capabilities: CodexCapabilities,
    workdir: Path,
    prompt: str,
    staging_path: Path,
    schema_path: Path,
    runtime_mode: str,
) -> CodexInvocation:
    """Build the DevRelay-owned argv for one Codex run."""
    validate_user_args(config.args, launcher_args=getattr(config, "launcher_args", ()))
    argv: list[str] = [config.executable]
    argv.extend(getattr(config, "launcher_args", []) or [])
    argv.append("exec")
    argv.extend(["--sandbox", "workspace-write"])
    if runtime_mode == "structured":
        if not capabilities.structured_supported:
            raise CodexRuntimeUnsupportedError(
                "structured runtime requested but the installed Codex CLI does "
                "not support "
                + ", ".join(capabilities.missing_structured_flags())
                + "; set codex.runtime_mode: text explicitly to use the legacy "
                "text runtime (DevRelay never downgrades silently)"
            )
        argv.extend(["--ignore-user-config", "--ignore-rules"])
        if capabilities.supports_json_events:
            argv.append("--json")
        argv.extend(["--output-schema", str(schema_path)])
        argv.extend(["--output-last-message", str(staging_path)])
    argv.extend(_user_passthrough(config.args))
    return CodexInvocation(
        argv=argv,
        env_remove=list(CODEX_CHILD_ENV_DENYLIST),
        runtime_mode=runtime_mode,
        staging_path=str(staging_path),
        schema_path=str(schema_path),
        workdir=str(workdir),
        prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        capabilities=capabilities,
    )


# ---------------------------------------------------------------------------
# result schema + parsing
# ---------------------------------------------------------------------------
def result_json_schema() -> dict[str, Any]:
    """The JSON Schema handed to Codex (tolerant: extras never break a run)."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "DevRelay ImplementationResult",
        "type": "object",
        "additionalProperties": True,
        "required": ["schema_version", "status", "summary"],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": IMPLEMENTATION_RESULT_SCHEMA_VERSION,
            },
            "status": {"type": "string", "enum": list(RESULT_STATUSES)},
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
                        "result": {
                            "type": "string",
                            "enum": ["PASS", "FAIL", "NOT_RUN"],
                        },
                        "notes": {"type": "string"},
                    },
                },
            },
            "unresolved_items": {"type": "array", "items": {"type": "string"}},
            "known_risks": {"type": "array", "items": {"type": "string"}},
        },
    }


def normalize_claim_path(raw: str) -> str | None:
    """Normalize one claimed path; return ``None`` when the claim is rejected.

    Traversal syntax is *rejected*, never stripped: a claim containing ``..``,
    an absolute path, a drive letter or a UNC prefix is not a path DevRelay will
    ever treat as a file location.
    """
    if not isinstance(raw, str):
        return None
    candidate = raw.strip()
    if not candidate or len(candidate) > MAX_CLAIM_ENTRY_CHARS:
        return None
    if any(ord(ch) < 32 for ch in candidate):
        return None
    candidate = candidate.replace("\\", "/")
    if candidate.startswith("/") or candidate.startswith("//"):
        return None
    if re.match(r"^[A-Za-z]:", candidate):
        return None
    parts: list[str] = []
    for part in candidate.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            return None
        parts.append(part)
    if not parts:
        return None
    return "/".join(parts)


def _clean_text(value: Any, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    return sanitize(value.strip())[:limit]


def _clean_list(value: Any, *, max_items: int, item_limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value[:max_items]:
        text = _clean_text(item, item_limit)
        if text:
            out.append(text)
    return out


def normalize_result_payload(
    payload: dict[str, Any], *, case_insensitive: bool = False
) -> tuple[ImplementationResult, list[str], list[str]]:
    """Validate/normalize a raw result payload.

    Returns ``(result, rejected_paths, unknown_field_names)``.  Unknown fields
    are recorded **by name only** - their values are dropped, so model-authored
    extras can never influence a workflow decision.
    """
    if not isinstance(payload, dict):
        raise CodexResultError("structured result is not a JSON object")
    raw_version = payload.get("schema_version", None)
    if raw_version is None:
        raise CodexResultError(
            "structured result is missing schema_version "
            f"(expected {IMPLEMENTATION_RESULT_SCHEMA_VERSION})"
        )
    if not isinstance(raw_version, int) or isinstance(raw_version, bool):
        raise CodexResultError("structured result schema_version is not an integer")
    if raw_version != IMPLEMENTATION_RESULT_SCHEMA_VERSION:
        raise CodexResultError(
            f"structured result schema_version {raw_version} is not supported "
            f"(this DevRelay understands {IMPLEMENTATION_RESULT_SCHEMA_VERSION})"
        )
    status = _clean_text(payload.get("status", ""), 32).upper()
    if status not in RESULT_STATUSES:
        raise CodexResultError(
            f"structured result status {status or '(missing)'!r} is not one of "
            + ", ".join(RESULT_STATUSES)
        )
    claimed_raw = payload.get("changed_files", [])
    if not isinstance(claimed_raw, list):
        claimed_raw = []
    claimed: list[str] = []
    rejected: list[str] = []
    for entry in claimed_raw[:MAX_CLAIMED_FILES]:
        normalized = normalize_claim_path(entry)
        if normalized is None:
            if isinstance(entry, str) and entry.strip():
                rejected.append(_clean_text(entry, MAX_CLAIM_ENTRY_CHARS))
            continue
        claimed.append(normalized)
    if case_insensitive:
        seen: set[str] = set()
        deduped: list[str] = []
        for path in claimed:
            key = path.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(path)
        claimed = deduped
    else:
        claimed = sorted(set(claimed))

    tests: list[TestClaim] = []
    raw_tests = payload.get("tests_run", [])
    if isinstance(raw_tests, list):
        for item in raw_tests[:MAX_TEST_CLAIMS]:
            if not isinstance(item, dict):
                continue
            result = _clean_text(item.get("result", ""), 16).upper() or "NOT_RUN"
            if result not in ("PASS", "FAIL", "NOT_RUN"):
                result = "NOT_RUN"
            tests.append(
                TestClaim(
                    command=_clean_text(item.get("command", ""), MAX_LIST_ITEM_CHARS),
                    result=result,
                    notes=_clean_text(item.get("notes", ""), MAX_LIST_ITEM_CHARS),
                )
            )

    known = {
        "schema_version",
        "status",
        "summary",
        "changed_files",
        "tests_run",
        "unresolved_items",
        "known_risks",
    }
    unknown = sorted(
        str(key)[:MAX_UNKNOWN_FIELD_NAME_CHARS]
        for key in payload
        if key not in known
    )[:MAX_UNKNOWN_FIELDS]

    result = ImplementationResult(
        schema_version=raw_version,
        status=status,
        summary=_clean_text(payload.get("summary", ""), MAX_SUMMARY_CHARS),
        changed_files=claimed,
        tests_run=tests,
        unresolved_items=_clean_list(
            payload.get("unresolved_items", []),
            max_items=MAX_LIST_ITEMS,
            item_limit=MAX_LIST_ITEM_CHARS,
        ),
        known_risks=_clean_list(
            payload.get("known_risks", []),
            max_items=MAX_LIST_ITEMS,
            item_limit=MAX_LIST_ITEM_CHARS,
        ),
    )
    return result, rejected, unknown


def parse_result_bytes(
    data: bytes, *, case_insensitive: bool = False
) -> tuple[ImplementationResult, list[str], list[str]]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CodexResultError(f"structured result is not valid UTF-8: {exc}") from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CodexResultError(f"structured result is not valid JSON: {exc}") from exc
    return normalize_result_payload(payload, case_insensitive=case_insensitive)


# ---------------------------------------------------------------------------
# JSONL observation (never authoritative)
# ---------------------------------------------------------------------------
_EVENT_KEYS = (
    "thread_id",
    "session_id",
    "conversation_id",
    "model",
)


@dataclass
class EventObservation:
    session_id: str = ""
    model: str = ""
    event_count: int = 0
    parse_warnings: list[str] = field(default_factory=list)
    types: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "model": self.model,
            "event_count": self.event_count,
            "types": self.types[:50],
            "parse_warnings": self.parse_warnings[:50],
        }


def observe_events(text: str) -> EventObservation:
    """Parse a JSONL event stream opportunistically; never required for success."""
    observation = EventObservation()
    seen_types: set[str] = set()
    for index, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            if len(observation.parse_warnings) < 20:
                observation.parse_warnings.append(f"line {index}: invalid JSON")
            continue
        observation.event_count += 1
        if not isinstance(payload, dict):
            continue
        for key in ("type", "event", "kind"):
            value = payload.get(key)
            if isinstance(value, str) and value and value not in seen_types:
                seen_types.add(value)
                observation.types.append(value)
                break
        if not observation.session_id:
            for key in _EVENT_KEYS:
                value = payload.get(key)
                if isinstance(value, str) and len(value) <= 200 and value:
                    if key == "model":
                        if not observation.model:
                            observation.model = sanitize(value)
                        continue
                    observation.session_id = sanitize(value)
                    break
        if not observation.model:
            value = payload.get("model")
            if isinstance(value, str) and value:
                observation.model = sanitize(value[:200])
    return observation


# ---------------------------------------------------------------------------
# identity helpers (authoritative values come from DevRelay's own machinery)
# ---------------------------------------------------------------------------
def guard_identity(snapshot) -> str:
    payload = {
        "head_sha": snapshot.head_sha,
        "branch": snapshot.branch,
        "index_tree_sha": snapshot.index_tree_sha,
        "index_snapshot_status": snapshot.index_snapshot_status.value
        if hasattr(snapshot.index_snapshot_status, "value")
        else str(snapshot.index_snapshot_status),
        "index_status_porcelain": snapshot.index_status_porcelain,
        "local_refs": sorted(snapshot.local_refs),
        "tags": sorted(snapshot.tags),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def delta_identity(delta) -> str:
    payload = {
        "from_tree": delta.from_tree,
        "to_tree": delta.to_tree,
        "changed_files": sorted(delta.changed_files),
        "name_status": [
            [entry.status, entry.old_path or "", entry.new_path]
            for entry in delta.name_status
        ],
        "binary_files": sorted(delta.binary_files),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def state_bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# reconciliation (advisory claims vs authoritative observations)
# ---------------------------------------------------------------------------
def reconcile_observed_files(
    claimed: Iterable[str],
    observed: Iterable[str],
    *,
    case_insensitive: bool = False,
) -> tuple[list[str], list[str]]:
    """Return (claimed_not_changed, unclaimed_change), de-duplicated and sorted."""
    observed_list = sorted(set(observed))
    if case_insensitive:
        observed_lookup = {path.lower(): path for path in observed_list}
        claimed_keys = {path.lower() for path in claimed}
        claimed_not_changed = sorted(
            path for path in claimed if path.lower() not in observed_lookup
        )
        unclaimed = sorted(
            path for path in observed_list if path.lower() not in claimed_keys
        )
    else:
        observed_set = set(observed_list)
        claimed_set = set(claimed)
        claimed_not_changed = sorted(claimed_set - observed_set)
        unclaimed = sorted(observed_set - claimed_set)
    return claimed_not_changed, unclaimed


def repo_is_case_insensitive(runner, root: Path) -> bool:
    """Ask git itself whether this repository is case-insensitive (read-only)."""
    result = runner.run(
        ["git", "-C", str(root), "config", "--get", "core.ignorecase"],
        cwd=root,
        timeout_seconds=30,
    )
    return (result.stdout or "").strip().lower() in ("true", "1", "yes")


def tests_claimed_passed(result: ImplementationResult) -> list[str]:
    return [claim.command for claim in result.tests_run if claim.result == "PASS"]


def write_json_new(path: Path, payload: dict[str, Any]) -> Path:
    """Create an immutable JSON evidence file (refuse to overwrite)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "xb") as handle:
            handle.write(
                json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True).encode(
                    "utf-8"
                )
            )
    except FileExistsError as exc:
        raise CodexRuntimeArtifactCollisionError(
            f"refusing to overwrite existing runtime evidence {path}"
        ) from exc
    return path


def write_text_new(path: Path, text: str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    try:
        with open(path, "xb") as handle:
            handle.write(data)
    except FileExistsError as exc:
        raise CodexRuntimeArtifactCollisionError(
            f"refusing to overwrite existing runtime evidence {path}"
        ) from exc
    return path


def sanitized_summary_markdown(
    *,
    attempt: int,
    attempt_id: str,
    provider: str,
    result: ImplementationResult | None,
    raw_report: str,
    reconciliation_path: str = "",
    warnings: Sequence[str] = (),
) -> str:
    """Human-readable implementation report (sanitized, bounded)."""
    lines = [
        f"# Implementation report — attempt {attempt} ({attempt_id})",
        "",
        f"Generated at {utcnow_iso()} by provider '{sanitize(provider)}'.",
    ]
    if result is not None:
        lines += [
            "",
            f"- status: {result.status} (advisory)",
            f"- schema_version: {result.schema_version}",
        ]
        if result.summary:
            lines += ["", "## Summary (model-reported)", "", result.summary]
        if result.changed_files:
            lines += ["", "## Claimed changed files (advisory)", ""]
            lines += [f"- {path}" for path in result.changed_files]
        if result.tests_run:
            lines += ["", "## Claimed tests (advisory)", ""]
            lines += [
                f"- [{claim.result}] {claim.command}"
                + (f" — {claim.notes}" if claim.notes else "")
                for claim in result.tests_run
            ]
        if result.unresolved_items:
            lines += ["", "## Unresolved items (model-reported)", ""]
            lines += [f"- {item}" for item in result.unresolved_items]
        if result.known_risks:
            lines += ["", "## Known risks (model-reported)", ""]
            lines += [f"- {item}" for item in result.known_risks]
        if reconciliation_path:
            lines += ["", f"Reconciliation: {reconciliation_path}"]
        if warnings:
            lines += ["", "## Runtime warnings", ""]
            lines += [f"- {warning}" for warning in warnings]
        return "\n".join(lines) + "\n"
    body = sanitize(raw_report or "")
    return (
        f"# Implementation report — attempt {attempt} ({attempt_id})\n\n"
        f"Generated at {utcnow_iso()} by provider '{sanitize(provider)}'.\n\n"
        f"{body[:200_000]}\n"
    )
