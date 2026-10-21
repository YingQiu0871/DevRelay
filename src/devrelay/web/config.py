"""Backend-owned workspace configuration write (v0.4-A2).

The API deliberately accepts a **curated patch**, not an unrestricted full
document.  Execution/wiring fields that can repoint a local command, a provider
endpoint or a workspace path are not editable here; they are preserved from the
current file.  This keeps the WebUI configuration path from becoming an
arbitrary-shell or arbitrary-endpoint surface.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from devrelay.config import WorkspaceFile
from devrelay.redact import redact_text
from devrelay.web.errors import WebApiError

#: Paths the local API may change.  A container path is also allowed when it is
#: a prefix of an editable path, so `codex` is accepted as a container but
#: `codex.executable` is not.
_EDITABLE_PREFIXES = frozenset(
    {
        "pipeline",
        "budget",
        "review",
        "scope",
        "baseline",
        "git",
        "roles",
        "tests.full_regression",
        "tests.timeout_seconds",
        "codex.prompt_mode",
        "codex.timeout_seconds",
        "codex.runtime_mode",
        "codex.max_result_bytes",
        "codex.max_capture_bytes",
        "opencode.default_session",
        "opencode.agent",
        "opencode.model",
        "opencode.timeout_seconds",
        "opencode.idle_timeout_seconds",
        "opencode.poll_interval_seconds",
        "opencode.max_response_bytes",
        "opencode.max_messages",
    }
)

_SECRET_NAME_PARTS = (
    "token",
    "password",
    "passwd",
    "secret",
    "api_key",
    "api-key",
    "apikey",
    "credential",
)
_SECRET_VALUE_RE = re.compile(
    r"(?i)(?:bearer\s+\S+"
    r"|basic\s+[A-Za-z0-9+/=]{8,}"
    r"|(?:token|password|passwd|api[_-]?key|secret|authorization)\s*[:=]\s*\S+"
    r"|sk-(?:ant-|proj-)?[A-Za-z0-9_-]{16,}"
    r"|AKIA[0-9A-Z]{16}"
    r"|xox[baprs]-[A-Za-z0-9-]{10,}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|https?://[^/\s:@]+:[^/\s@]+@)"
)


def _path_allowed(path: tuple[str, ...]) -> bool:
    dotted = ".".join(path)
    return any(
        dotted == prefix
        or dotted.startswith(prefix + ".")
        or prefix.startswith(dotted + ".")
        for prefix in _EDITABLE_PREFIXES
    )


def _path_errors(value: Any, path: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = path + (str(key),)
            if not _path_allowed(child):
                errors.append(
                    {
                        "loc": list(child),
                        "type": "config_field_not_editable",
                        "msg": f"{'.'.join(child)} is not editable through the local API",
                    }
                )
                continue
            errors.extend(_path_errors(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_path_errors(item, path + (str(index),)))
    return errors


def _walk_keys(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            name = str(key)
            lowered = name.lower()
            if any(part in lowered for part in _SECRET_NAME_PARTS):
                dotted = ".".join(path + (name,))
                raise WebApiError(
                    "secret_key_rejected",
                    f"configuration key {dotted!r} is not accepted",
                    status_code=422,
                )
            _walk_keys(item, path + (name,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_keys(item, path + (str(index),))


def _walk_values(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, str):
        if _SECRET_VALUE_RE.search(value):
            dotted = ".".join(path) or "<root>"
            raise WebApiError(
                "secret_value_rejected",
                f"configuration value at {dotted!r} looks like a credential",
                status_code=422,
            )
    elif isinstance(value, dict):
        for key, item in value.items():
            _walk_values(item, path + (str(key),))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_values(item, path + (str(index),))


def _merge(base: Any, patch: Any) -> Any:
    if not isinstance(patch, dict):
        return patch
    result = dict(base) if isinstance(base, dict) else {}
    for key, value in patch.items():
        result[key] = _merge(result.get(key), value)
    return result


def _dump(document: dict[str, Any]) -> str:
    try:
        text = yaml.safe_dump(
            document,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )
    except (yaml.YAMLError, ValueError) as exc:
        raise WebApiError(
            "config_not_serializable",
            "configuration cannot be serialized safely",
            status_code=422,
        ) from exc
    if not text.endswith("\n"):
        text += "\n"
    return text


def _fsync_directory(directory: Path) -> None:
    if os.name == "nt":
        return
    try:
        fd = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class ConfigWriter:
    """Validate, merge, back up and atomically replace `.devrelay/config.yaml`."""

    def __init__(self, root: Path, devrelay_dir: Path) -> None:
        self.root = Path(root)
        self.devrelay_dir = Path(devrelay_dir)
        self.path = self.devrelay_dir / "config.yaml"
        self._lock = threading.RLock()

    def sha256(self) -> str | None:
        try:
            payload = self.path.read_bytes()
        except OSError:
            return None
        return hashlib.sha256(payload).hexdigest()

    def _read_current(self, *, required: bool) -> tuple[bytes, dict[str, Any]]:
        if self.path.is_symlink():
            raise WebApiError(
                "config_symlink_rejected",
                "the workspace configuration must be a regular file",
                status_code=409,
            )
        try:
            payload = self.path.read_bytes()
        except OSError as exc:
            if required:
                raise WebApiError(
                    "config_missing",
                    "the workspace configuration file does not exist",
                    status_code=409,
                ) from exc
            return b"", {}
        try:
            loaded = yaml.safe_load(payload)
        except yaml.YAMLError as exc:
            raise WebApiError(
                "config_unreadable",
                "the current workspace configuration is not valid YAML",
                status_code=409,
            ) from exc
        if loaded is None:
            return payload, {}
        if not isinstance(loaded, dict):
            raise WebApiError(
                "config_unreadable",
                "the current workspace configuration must be a mapping",
                status_code=409,
            )
        return payload, loaded

    @staticmethod
    def _validation_errors(exc: ValidationError) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        for item in exc.errors()[:20]:
            errors.append(
                {
                    "loc": [str(part) for part in item.get("loc", ())],
                    "type": str(item.get("type", "validation_error")),
                    "msg": redact_text(str(item.get("msg", "invalid value")))[:300],
                }
            )
        return errors

    def _validate_patch(
        self, config: dict[str, Any], current: dict[str, Any]
    ) -> list[dict[str, Any]]:
        try:
            _walk_keys(config)
            _walk_values(config)
        except WebApiError as exc:
            return [{"loc": [], "type": exc.code, "msg": exc.message}]
        errors = _path_errors(config)
        if errors:
            return errors
        merged = _merge(current, config)
        try:
            WorkspaceFile.model_validate(merged)
        except ValidationError as exc:
            return self._validation_errors(exc)
        try:
            _dump(merged)
        except WebApiError as exc:
            return [{"loc": [], "type": exc.code, "msg": exc.message}]
        return []

    def validate(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Return bounded validation errors; never writes or echoes values."""
        try:
            _payload, current = self._read_current(required=False)
        except WebApiError as exc:
            return [{"loc": [], "type": exc.code, "msg": exc.message}]
        return self._validate_patch(config, current)

    def _backup(self, payload: bytes) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        counter = 1
        while True:
            candidate = self.path.with_name(f"config.yaml.bak-{stamp}")
            if counter > 1:
                candidate = self.path.with_name(f"config.yaml.bak-{stamp}-{counter}")
            try:
                fd = os.open(
                    candidate,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    stat.S_IRUSR | stat.S_IWUSR,
                )
                break
            except FileExistsError:
                counter += 1
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        return candidate

    def _write(self, text: str) -> None:
        try:
            mode = stat.S_IMODE(self.path.stat().st_mode)
        except OSError:
            mode = stat.S_IRUSR | stat.S_IWUSR
        fd, tmp_name = tempfile.mkstemp(prefix=".config-", dir=self.devrelay_dir)
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.chmod(tmp, mode)
            except OSError:  # pragma: no cover - Windows ACL is the effective owner
                pass
            os.replace(tmp, self.path)
            _fsync_directory(self.devrelay_dir)
        except BaseException:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:  # pragma: no cover - defensive
                pass
            raise

    def apply(self, config: dict[str, Any], expected_sha256: str) -> dict[str, Any]:
        with self._lock:
            current_bytes, current = self._read_current(required=True)
            actual = hashlib.sha256(current_bytes).hexdigest()
            if actual != expected_sha256:
                raise WebApiError(
                    "config_changed",
                    "the configuration changed since it was read; reload and retry",
                    status_code=409,
                )
            errors = self._validate_patch(config, current)
            if errors:
                first = errors[0]
                code = str(first.get("type", "invalid_config"))
                if code not in {
                    "config_field_not_editable",
                    "secret_key_rejected",
                    "secret_value_rejected",
                    "config_not_serializable",
                }:
                    code = "invalid_config"
                    message = "configuration is invalid; call /api/config/validate for details"
                else:
                    message = str(first.get("msg", "configuration is not editable"))
                raise WebApiError(code, message, status_code=422)
            merged = _merge(current, config)
            if merged == current:
                return {
                    "applied": False,
                    "no_change": True,
                    "old_sha256": actual,
                    "new_sha256": actual,
                    "backup_created": False,
                    "comments_preserved": False,
                    "restart_required": False,
                    "write_scope": "workspace configuration patch",
                }
            text = _dump(merged)
            backup = self._backup(current_bytes)
            try:
                self._write(text)
            except OSError as exc:
                raise WebApiError(
                    "config_write_failed",
                    "the configuration could not be written atomically",
                    status_code=500,
                ) from exc
            new_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
            return {
                "applied": True,
                "old_sha256": actual,
                "new_sha256": new_sha,
                "backup_created": True,
                "backup_name": backup.name,
                "comments_preserved": False,
                "restart_required": True,
                "write_scope": "workspace configuration patch",
            }
