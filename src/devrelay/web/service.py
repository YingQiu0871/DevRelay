"""Bounded read adapter plus the A2 configuration-write facade."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from devrelay import __version__
from devrelay.errors import OrchestrationError
from devrelay.mcp.models import McpEnvelope
from devrelay.mcp.tools import McpToolSurface
from devrelay.orchestration.store import valid_run_id
from devrelay.redact import redact_text
from devrelay.web.config import ConfigWriter
from devrelay.web.errors import WebApiError
from devrelay.web.models import MAX_LIST_LIMIT

MAX_RUN_SCAN = 500


class WebReadService:
    """Read operations plus the curated A2 config write.

    The service holds exactly one ``McpToolSurface`` bound to the registered
    workspace.  It never calls an orchestration action tool and never constructs
    a second engine; the only write is the allowlisted configuration patch.
    """

    def __init__(
        self,
        *,
        workspace_root: Path,
        wiring: Any,
        devrelay_dir: Path,
        surface: McpToolSurface | None = None,
    ) -> None:
        self.workspace_root = Path(workspace_root)
        self.wiring = wiring
        self.devrelay_dir = Path(devrelay_dir)
        self.surface = surface or McpToolSurface(
            workspace_root=self.workspace_root,
            wiring=self.wiring,
            devrelay_dir=self.devrelay_dir,
            package_version=__version__,
        )
        self.config_writer = ConfigWriter(self.workspace_root, self.devrelay_dir)

    @classmethod
    def from_workspace(cls, root: Path, wiring: Any, devrelay_dir: Path) -> "WebReadService":
        return cls(workspace_root=root, wiring=wiring, devrelay_dir=devrelay_dir)

    # ------------------------------------------------------------------
    # envelope conversion
    # ------------------------------------------------------------------
    @staticmethod
    def _data(envelope: McpEnvelope, *, operation: str) -> dict[str, Any]:
        if envelope.ok:
            return dict(envelope.data)
        error = envelope.error
        code = error.type if error is not None and error.type else "upstream_error"
        message = error.message if error is not None and error.message else f"{operation} failed"
        raise WebApiError(code, message, status_code=503)

    # ------------------------------------------------------------------
    # read operations
    # ------------------------------------------------------------------
    def health(self, *, project_id: str) -> dict[str, Any]:
        return {
            "package_version": __version__,
            "project_id": project_id,
            "workspace": str(self.workspace_root),
            "read_only": True,
        }

    def status(self) -> dict[str, Any]:
        return self._data(self.surface.devrelay_status(), operation="status")

    def roles(self) -> dict[str, Any]:
        return self._data(self.surface.devrelay_list_roles(), operation="roles")

    def runs(self, *, limit: int = 20) -> dict[str, Any]:
        bound = max(1, min(int(limit), MAX_LIST_LIMIT))
        ids = self.surface.orchestration.list_run_ids()
        if len(ids) > MAX_RUN_SCAN:
            raise WebApiError(
                "run_list_too_large",
                f"more than {MAX_RUN_SCAN} runs exist; narrow the workspace before listing",
                status_code=503,
            )
        summaries = []
        for run_id in ids:
            try:
                run = self.surface.orchestration.get_run(run_id)
            except OrchestrationError as exc:
                raise WebApiError(
                    getattr(exc, "code", "orchestration_error"),
                    "one or more run documents are unreadable",
                    status_code=503,
                ) from exc
            summaries.append(run.summary())
        summaries.sort(key=lambda item: str(item.get("updated_at", "")), reverse=True)
        return {
            "runs": summaries[:bound],
            "returned": min(len(summaries), bound),
            "total": len(summaries),
            "limit": bound,
            "truncated": len(summaries) > bound,
        }

    def run(self, run_id: str) -> dict[str, Any]:
        if not valid_run_id(run_id):
            raise WebApiError(
                "invalid_run_id",
                "run id must be DR-<32 lowercase hex characters>",
            )
        try:
            return self.surface.orchestration.get_run(run_id).summary()
        except OrchestrationError as exc:
            code = getattr(exc, "code", "orchestration_error")
            status = 404 if code == "orchestration_run_not_found" else 503
            raise WebApiError(code, redact_text(str(exc))[:300], status_code=status) from exc

    def config(self) -> dict[str, Any]:
        opencode = self.wiring.opencode
        codex = self.wiring.codex
        return {
            "config_sha256": self.config_writer.sha256(),
            "review_provider": self.wiring.review_provider,
            "opencode": {
                "configured": bool(opencode.configured),
                "base_url": opencode.base_url,
                # A configured workspace may point outside the registered root;
                # expose only whether an override exists, never its path.
                "workspace_override": bool(opencode.workspace),
                "timeout_seconds": float(opencode.timeout_seconds),
                "idle_timeout_seconds": float(opencode.idle_timeout_seconds),
                "poll_interval_seconds": float(opencode.poll_interval_seconds),
                "max_messages": int(opencode.max_messages),
                "allow_unknown_workspace": bool(opencode.allow_unknown_workspace),
                "token_source": "DEVRELAY_OPENCODE_TOKEN (environment only)",
            },
            "codex": {
                # Only the program name: a wrapper path may itself contain a
                # credential-like component.  Arbitrary argv is never echoed.
                "executable": Path(codex.executable).name,
                "runtime_mode": codex.runtime_mode,
                "timeout_seconds": float(codex.timeout_seconds),
            },
            "roles": self.surface.roles.summary(),
            "read_only": False,
            "write_supported": True,
            "write_scope": "workspace configuration only",
        }

    def validate_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Validate a proposed workspace document without writing it."""
        errors = self.config_writer.validate(config)
        return {"valid": not errors, "errors": errors, "write_supported": True}

    def apply_config(self, config: dict[str, Any], expected_sha256: str) -> dict[str, Any]:
        return self.config_writer.apply(config, expected_sha256)
