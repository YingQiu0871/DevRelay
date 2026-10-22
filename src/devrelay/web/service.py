"""Bounded read adapter plus the A2 configuration-write facade."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from devrelay import __version__
from devrelay.artifacts.store import ArtifactStore
from devrelay.errors import DevRelayError, OrchestrationError, TaskNotFoundError
from devrelay.mcp.models import McpEnvelope
from devrelay.mcp.tools import McpToolSurface
from devrelay.orchestration.store import valid_run_id
from devrelay.pipeline.budget import ProviderBudget
from devrelay.redact import redact_text
from devrelay.workspace.runner import CommandRunner
from devrelay.web.config import ConfigWriter
from devrelay.web.errors import WebApiError
from devrelay.web.models import MAX_LIST_LIMIT

MAX_RUN_SCAN = 500
MAX_TASK_SCAN = 200
MAX_TASK_TEXT = 16_384
_TASK_ID_RE = re.compile(r"DR-[0-9]{4}\Z")


class WebReadService:
    """Read operations plus the curated A2 config and B2 wiring writes.

    The service holds exactly one ``McpToolSurface`` bound to the registered
    workspace.  It never calls an orchestration action tool and never constructs
    a second engine.  Writes are limited to the allowlisted configuration patch
    and the loopback OpenCode endpoint.
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
        # The process keeps the wiring it loaded at startup.  Comparing the
        # current file digest against this marker tells the UI that a restart is
        # required after a successful A2 write.
        self._loaded_config_sha = self.config_writer.sha256()

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
            "workspace_id": project_id,
            "read_only": False,
            "write_supported": True,
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
        current_sha = self.config_writer.sha256()
        return {
            "config_sha256": current_sha,
            "restart_required": current_sha != self._loaded_config_sha,
            "editable_config": self.config_writer.editable_document(),
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
            "write_supported": self.config_writer.available(),
            "write_scope": "workspace configuration only",
        }

    def validate_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Validate a proposed workspace document without writing it."""
        errors = self.config_writer.validate(config)
        return {"valid": not errors, "errors": errors, "write_supported": True}

    def apply_config(self, config: dict[str, Any], expected_sha256: str) -> dict[str, Any]:
        return self.config_writer.apply(config, expected_sha256)

    def wiring_status(self) -> dict[str, Any]:
        """The separate B2 wiring surface: endpoint + references, never values."""
        current_sha = self.config_writer.sha256()
        return {
            "config_sha256": current_sha,
            "restart_required": current_sha != self._loaded_config_sha,
            "write_supported": self.config_writer.available(),
            "opencode": self.config_writer.wiring_document(),
            "credentials": {
                "opencode_token": {
                    "env": "DEVRELAY_OPENCODE_TOKEN",
                    "configured": bool(os.environ.get("DEVRELAY_OPENCODE_TOKEN")),
                }
            },
            "mcp": {
                "transport": "stdio",
                "command": "devrelay mcp serve --workspace <registered workspace>",
                "credentials": "client-side / environment only",
            },
            "write_scope": "OpenCode endpoint wiring only",
        }

    def apply_wiring(
        self, wiring: dict[str, Any], expected_sha256: str
    ) -> dict[str, Any]:
        return self.config_writer.apply_wiring(wiring, expected_sha256)

    # -- C2a read-only task artifacts -----------------------------------
    @staticmethod
    def _bounded(value: Any, limit: int = 2_000) -> str:
        return redact_text(str(value or ""))[:limit]

    @classmethod
    def _finding_public(cls, finding: Any) -> dict[str, Any]:
        return {
            "id": getattr(finding, "id", None),
            "severity": getattr(getattr(finding, "severity", None), "value", ""),
            "title": cls._bounded(getattr(finding, "title", ""), 300),
            "description": cls._bounded(getattr(finding, "description", ""), 1_000),
            "files": [cls._bounded(item, 200) for item in getattr(finding, "files", [])[:20]],
            "evidence": cls._bounded(getattr(finding, "evidence", ""), 1_000),
            "recommendation": cls._bounded(getattr(finding, "recommendation", ""), 1_000),
            "fingerprint": cls._bounded(getattr(finding, "fingerprint", ""), 100),
        }

    @classmethod
    def _review_public(cls, review: Any) -> dict[str, Any]:
        return {
            "decision": getattr(getattr(review, "decision", None), "value", ""),
            "summary": cls._bounded(getattr(review, "summary", ""), 2_000),
            "reviewer": cls._bounded(getattr(review, "reviewer", ""), 200),
            "findings": [cls._finding_public(item) for item in getattr(review, "findings", [])[:50]],
        }

    def _task_diff(self, task: Any) -> dict[str, Any]:
        baseline = getattr(task, "baseline", None)
        tree = getattr(baseline, "baseline_worktree_tree_sha", None)
        if baseline is None or not getattr(baseline, "baseline_complete", False):
            return {"available": False, "reason": "no complete task baseline"}
        if not isinstance(tree, str) or not re.fullmatch(r"[0-9a-f]{40,64}", tree):
            return {"available": False, "reason": "no stored baseline tree"}
        try:
            # Read-only tree-vs-worktree stat.  No hash-object/write-tree and
            # no baseline reconstruction: this endpoint must not write objects.
            result = CommandRunner().run(
                [
                    "git",
                    "-c",
                    "core.quotepath=false",
                    "diff",
                    "--no-ext-diff",
                    "--no-textconv",
                    "--stat",
                    tree,
                ],
                cwd=self.workspace_root,
                timeout_seconds=15.0,
                max_capture_bytes=MAX_TASK_TEXT,
            )
            if result.exit_code != 0:
                return {"available": False, "reason": "task diff unavailable"}
            stat = self._bounded(result.stdout or "", MAX_TASK_TEXT)
            return {
                "available": True,
                "stat": stat,
                "truncated": bool(
                    getattr(result, "stdout_truncated", False)
                    or len(stat) >= MAX_TASK_TEXT
                ),
            }
        except Exception:  # noqa: BLE001 - a read surface must fail closed
            return {"available": False, "reason": "task diff unavailable"}

    def _task_detail(self, task: Any, *, current: bool) -> dict[str, Any]:
        usage = ProviderBudget.usage(task)
        calls = []
        for record in task.provider_calls[-100:]:
            calls.append(
                {
                    "call_id": record.call_id,
                    "kind": record.provider_kind.value,
                    "phase": record.phase.value,
                    "success": bool(record.success),
                    "external_calls": int(record.external_call_count),
                    "duration_seconds": float(record.duration_seconds),
                    "model": self._bounded(record.model or "", 200),
                    "endpoint_host": self._bounded(record.endpoint_host or "", 200),
                    "error_type": record.error_type.value if record.error_type else None,
                }
            )
        attempts = [
            {
                "review_number": attempt.review_number,
                "status": attempt.status.value,
                "provider": self._bounded(attempt.provider_name, 200),
                "transport_attempts": attempt.transport_attempts,
                "format_attempts": attempt.format_attempts,
                "external_calls": attempt.external_calls_consumed,
            }
            for attempt in task.review_attempts[-20:]
        ]
        review = task.last_review
        final_gate = task.final_gate
        return {
            "task_id": task.task_id,
            "title": self._bounded(task.title, 300),
            "state": task.state.value,
            "current": current,
            "plan_ready": bool(task.plan_ready),
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "implementation_passes": task.implementation_passes,
            "fix_iterations_used": task.fix_iterations_used,
            "baseline_available": bool(
                task.baseline is not None
                and getattr(task.baseline, "baseline_complete", False)
            ),
            "tests": {
                "passed": task.last_tests_passed,
                "evidence": [
                    self._bounded(line, 1_000) for line in task.test_evidence[-30:]
                ],
            },
            "review": {
                "last": self._review_public(review) if review is not None else None,
                "history": [
                    self._review_public(item) for item in task.review_history[-10:]
                ],
                "current_findings": [
                    self._finding_public(item) for item in task.current_findings[:50]
                ],
                "open_p3": [self._finding_public(item) for item in task.open_p3[:50]],
            },
            "git": self._task_diff(task),
            "usage": {
                "implementer_calls": usage.implementer_calls,
                "reviewer_calls": usage.reviewer_calls,
                "total_calls": usage.total_calls,
                "provider_calls": calls,
                "review_attempts": attempts,
                "token_usage_available": False,
                "cost_available": False,
            },
            "final_gate": (
                {
                    "approved_by": self._bounded(final_gate.approved_by, 200),
                    "approved_at": final_gate.approved_at,
                    "note": self._bounded(final_gate.note, 1_000),
                }
                if final_gate is not None
                else None
            ),
            "blocked": {
                "code": task.blocked_code,
                "reason": self._bounded(task.blocked_reason, 2_000),
            },
        }

    def tasks(self, limit: int = 20) -> dict[str, Any]:
        bound = max(1, min(int(limit), 100))
        store = ArtifactStore(self.workspace_root)
        try:
            raw_ids = store.list_task_ids()
            ids = [
                item
                for item in raw_ids
                if isinstance(item, str) and _TASK_ID_RE.fullmatch(item)
            ][:MAX_TASK_SCAN]
            current = store.current_task_id()
        except (DevRelayError, AttributeError, TypeError) as exc:
            raise WebApiError(
                "task_store_unreadable",
                "the workspace task index is unreadable",
                status_code=503,
            ) from exc
        summaries: list[dict[str, Any]] = []
        skipped = 0
        for task_id in ids[:bound]:
            try:
                task = store.read_task(task_id)
            except DevRelayError:
                skipped += 1
                continue
            summaries.append(
                {
                    "task_id": task.task_id,
                    "title": self._bounded(task.title, 300),
                    "state": task.state.value,
                    "current": task_id == current,
                    "updated_at": task.updated_at,
                    "baseline_available": bool(
                        task.baseline is not None
                        and getattr(task.baseline, "baseline_complete", False)
                    ),
                }
            )
        return {
            "tasks": summaries,
            "returned": len(summaries),
            "total": len(ids),
            "skipped": skipped,
            "limit": bound,
            "truncated": len(ids) > bound,
            "current_task": current if isinstance(current, str) else None,
        }

    def task(self, task_id: str) -> dict[str, Any]:
        if not _TASK_ID_RE.fullmatch(task_id):
            raise WebApiError("invalid_task_id", "invalid task id", status_code=400)
        store = ArtifactStore(self.workspace_root)
        try:
            task = store.read_task(task_id)
            current = store.current_task_id() == task_id
        except TaskNotFoundError as exc:
            raise WebApiError(
                "task_not_found",
                "task was not found",
                status_code=404,
            ) from exc
        except DevRelayError as exc:
            raise WebApiError(
                "task_store_unreadable",
                "the task state is unreadable",
                status_code=503,
            ) from exc
        return self._task_detail(task, current=current)
