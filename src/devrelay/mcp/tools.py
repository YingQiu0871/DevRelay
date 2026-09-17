"""The DevRelay MCP tool surface: adapters over the accepted v0.3-A bridge.

Everything here is an **adapter**: each tool validates its arguments with the
accepted v0.3-A rules, calls exactly one :class:`~devrelay.opencode.bridge.OpenCodeBridge`
method (or the strict ledger view) and wraps the normalized result in the stable
MCP envelope.  No HTTP client, no retry, no orchestration, no acceptance
authority, no second validator for session ids or model overrides.

Safety properties carried over unchanged from v0.3-A (and asserted by tests):

* exactly one submission POST per ``opencode_send_prompt`` - never a retry, never
  a model fallback, never an automatic resubmission;
* read/write timeouts stay *submission-uncertain*, connect failures stay
  *definitely not submitted* (the envelope carries ``retry_safe`` derived from
  documented bridge evidence only);
* a pending/uncertain result never substitutes a stale reply;
* **all** tool execution is serialized per MCP server process by one re-entrant
  execution lock: the accepted v0.3-A filesystem ledger allocates durable call
  identities with a non-atomic read-modify-write and is therefore single-writer,
  so concurrent tool bodies (including concurrent reads) must not overlap;
* v0.3-D adds a **bounded orchestration path** on top of the role path:
  durable run state, legal transitions, a hard cycle bound, one role turn per
  explicit phase call, fail-closed blocking on uncertainty - and **no** parsing
  of reviewer prose, no automatic sequencing, no retry.  The raw path and the
  role path are unchanged;
* v0.3-C adds a **role path** on top of the unchanged raw path:
  ``opencode_send_prompt`` keeps its caller-supplied ``model``/``agent``, while
  ``devrelay_send_role_prompt`` accepts a semantic role only and takes the
  model/agent from workspace configuration.  The raw tool is never redirected
  through role routing;
* secrets are never logged or returned; error text is redacted and bounded.
"""

from __future__ import annotations

import math
import threading
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

from devrelay.errors import DevRelayError, OrchestrationError, RoleRoutingError
from devrelay.mcp.ledger import read_records_strict, sequence_state
from devrelay.mcp.models import (
    MCP_DEFAULT_CALL_LIMIT,
    MCP_MAX_CALL_LIMIT,
    MCP_MAX_WAIT_SECONDS,
    MCP_PROMPT_MAX_CHARS,
    McpEnvelope,
    bounded,
    error_envelope,
    ok_envelope,
)
from devrelay.opencode.bridge import OpenCodeBridge
from devrelay.opencode.models import OpenCodeOperationState, valid_session_id
from devrelay.roles.models import ROLE_ROUTE_SOURCE, SUPPORTED_ROLES
from devrelay.orchestration import (
    DEFAULT_MAX_CYCLES,
    HARD_MAX_CYCLES,
    Decision,
    OrchestrationService,
    valid_run_id,
)
from devrelay.roles.service import RoleRouter

#: Bridge operations this adapter exposes (status reporting only).
BRIDGE_OPERATIONS: tuple[str, ...] = (
    "health",
    "list_sessions",
    "get_session",
    "read_messages",
    "send_prompt",
    "wait_idle",
    "interrupt",
)

#: Cursor values are opaque provider message ids; bound them defensively.
_CURSOR_MAX_CHARS = 200
_AGENT_MAX_CHARS = 64


class McpArgumentError(DevRelayError):
    """An MCP tool argument failed DevRelay-side validation."""

    code = "mcp_invalid_argument"

    def __init__(self, message: str) -> None:
        super().__init__(f"{self.code}: {message}")


class McpToolSurface:
    """Bound-workspace MCP tool surface over the accepted v0.3-A bridge.

    One instance is bound to exactly one workspace (resolved once by the
    caller); no tool accepts a workspace path, a ``cwd`` or any other way to
    reach outside it.
    """

    def __init__(
        self,
        *,
        workspace_root: Path,
        wiring: Any,
        devrelay_dir: Path,
        bridge_factory: Callable[[], OpenCodeBridge] | None = None,
        package_version: str = "",
        mcp_server_version: str = "",
        diagnostics: Callable[[str], None] | None = None,
    ) -> None:
        self.workspace_root = Path(workspace_root)
        self.wiring = wiring
        self.devrelay_dir = Path(devrelay_dir)
        self.package_version = package_version
        self.mcp_server_version = mcp_server_version
        self._bridge_factory = bridge_factory
        self._bridge: OpenCodeBridge | None = None
        # v0.3-B concurrency boundary (P2 remediation): the accepted v0.3-A
        # filesystem ledger allocates durable ``OC-*`` identities with a
        # non-atomic read-modify-write (fixed-name temp file + replace) and
        # refuses identity reuse, so it is safe only for one caller at a time.
        # Exactly ONE process-scoped, re-entrant execution lock therefore covers
        # every MCP tool body: within one MCP server process at most one tool
        # body may touch the accepted bridge/ledger at any moment.  Re-entrant
        # because a tool body may lazily construct the bridge while already
        # holding it.  There is deliberately no second lock and therefore no
        # lock order to get wrong.
        self._execution_lock = threading.RLock()
        # v0.3-C: one role router per surface, fed by the same workspace wiring
        # the bridge uses.  It resolves roles for the three role-aware tools; it
        # holds no session state and never executes anything itself.
        self.roles = RoleRouter(getattr(wiring, "roles", None))
        # v0.3-D: one bounded-orchestration service per surface.  It persists
        # durable run state under the bound workspace and performs at most one
        # accepted role turn per explicit phase call; it never sequences roles,
        # never retries and never interprets provider text.
        self.orchestration = OrchestrationService(
            router=self.roles,
            bridge_provider=self.bridge,
            devrelay_dir=self.devrelay_dir,
            workspace_root=self.workspace_root,
        )
        self._diagnostics = diagnostics

    # ------------------------------------------------------------------
    # infrastructure
    # ------------------------------------------------------------------
    @property
    def opencode_config(self) -> Any:
        return self.wiring.opencode

    def bridge(self) -> OpenCodeBridge:
        """The one bridge instance for this bound workspace (built lazily).

        Construction happens under the same execution lock as every tool body
        (``RLock``, so re-entering from a tool body is legal): the bridge binds
        the workspace's ledger, and two bridges over one ledger would defeat the
        single-writer boundary.
        """
        with self._execution_lock:
            if self._bridge is None:
                if self._bridge_factory is not None:
                    self._bridge = self._bridge_factory()
                else:
                    self._bridge = self._build_bridge()
            return self._bridge

    def _build_bridge(self) -> OpenCodeBridge:
        import os

        config = self.opencode_config
        return OpenCodeBridge(
            base_url=config.base_url,
            workspace_root=config.workspace or self.workspace_root,
            token=os.environ.get("DEVRELAY_OPENCODE_TOKEN", ""),
            timeout_seconds=config.timeout_seconds,
            idle_timeout_seconds=config.idle_timeout_seconds,
            poll_interval_seconds=config.poll_interval_seconds,
            max_response_bytes=config.max_response_bytes,
            max_messages=config.max_messages,
            allow_unknown_workspace=config.allow_unknown_workspace,
            devrelay_dir=self.devrelay_dir,
        )

    def _diag(self, message: str) -> None:
        if self._diagnostics is not None:
            self._diagnostics(bounded(message))

    @staticmethod
    def _bridge_envelope(
        tool: str,
        result: Any,
        *,
        failure_message: str,
        expect: Callable[[Any], bool] | None = None,
        error_type_fallback: str = "operation_not_completed",
        extra: dict[str, Any] | None = None,
    ) -> McpEnvelope:
        """The single bridge-result-to-envelope rule (envelope truthfulness).

        ``ok`` is true **only** when the accepted v0.3-A operation reached the
        success state that tool is defined to achieve.  By default that is the
        bridge's own ``result.ok`` (``state is COMPLETED``); a tool whose
        accepted success state differs states it explicitly through ``expect``
        (``opencode_interrupt``: an accepted abort is ``INTERRUPTED``, which the
        accepted v0.3-A CLI also treats as success, and is still reported with
        ``interrupt_verified: false``).  A tool that composes the base rule with
        extra conditions (``opencode_send_prompt``) states them in ``expect``.

        Every bridge-backed tool derives its envelope here, so a failed
        operation can never be reported as success - and the protocol
        ``isError`` flag stays mechanically ``not envelope.ok`` because the
        server shapes it from this envelope alone.

        The full sanitized operation evidence is always preserved in ``data``.
        """
        data = result.model_dump(mode="json")
        if extra:
            data.update(extra)
        achieved = bool(expect(result)) if expect is not None else bool(result.ok)
        if achieved:
            return ok_envelope(tool, data)
        return error_envelope(
            tool,
            result.error_type or error_type_fallback,
            result.error or failure_message,
            data,
        )

    def _execute(self, tool: str, call: Callable[[], McpEnvelope]) -> McpEnvelope:
        """Run one tool body under the process-wide execution lock.

        Every one of the nine tools funnels its whole body through here, so this
        is the single place that establishes the v0.3-B serialization boundary:
        at most one DevRelay MCP tool body may access the accepted v0.3-A
        bridge/ledger at a time within one MCP server process.  The lock is held
        for the whole body (validation, bridge operation, envelope shaping) and
        is released on every exit path, including ``DevRelayError`` and
        unexpected exceptions.

        Cancellation is honest rather than magic: cancelling a client's MCP
        request does not interrupt an already-running synchronous tool body, so
        the lock is released only when that body actually returns.  No retry, no
        automatic interrupt and no automatic resubmission happens on the way out.

        ``DevRelayError`` (including validation and bridge/provider errors) keeps
        its stable code; anything else is an internal DevRelay error: it is
        diagnosed (bounded, sanitized) on stderr and reported generically - it is
        never translated into a provider failure.
        """
        with self._execution_lock:
            try:
                return call()
            except DevRelayError as exc:
                return error_envelope(tool, _error_type(exc), exc)
            except Exception as exc:  # pragma: no cover - defensive boundary
                self._diag(f"{tool}: internal error {type(exc).__name__}")
                return error_envelope(
                    tool,
                    "internal_error",
                    "internal DevRelay error while handling this tool call; "
                    "see the MCP server diagnostics on stderr",
                )

    # ------------------------------------------------------------------
    # validation (reuses the accepted v0.3-A rules; no second grammar)
    # ------------------------------------------------------------------
    @staticmethod
    def _require_session_id(session_id: object) -> str:
        if session_id is None or not isinstance(session_id, str) or not valid_session_id(
            session_id.strip()
        ):
            raise McpArgumentError(
                "session_id must be an explicit opaque OpenCode identifier "
                "(unreserved characters [A-Za-z0-9._~-], 1-200 chars)"
            )
        return session_id.strip()

    @staticmethod
    def _require_prompt(prompt: object) -> str:
        if prompt is None or not isinstance(prompt, str):
            raise McpArgumentError("prompt must be a non-empty string")
        if not prompt.strip():
            raise McpArgumentError("prompt must not be empty or whitespace-only")
        if len(prompt) > MCP_PROMPT_MAX_CHARS:
            raise McpArgumentError(
                f"prompt exceeds the documented MCP input bound of "
                f"{MCP_PROMPT_MAX_CHARS} characters"
            )
        return prompt

    @staticmethod
    def _require_model(model: object) -> str:
        if model is None or model == "":
            return ""
        if not isinstance(model, str):
            raise McpArgumentError("model must be a string '<providerID>/<modelID>'")
        # The accepted v0.3-A grammar is the only authority: reuse it verbatim so
        # the MCP layer can never parse a model differently from the bridge.
        try:
            OpenCodeBridge._model_identity(model)  # noqa: SLF001 - single grammar
        except DevRelayError as exc:
            # Reuse the accepted message, but do not stack two stable codes.
            detail = str(exc)
            prefix = f"{getattr(exc, 'code', '')}: "
            if prefix.strip(": ") and detail.startswith(prefix):
                detail = detail[len(prefix):]
            raise McpArgumentError(detail) from exc
        return model

    @staticmethod
    def _require_agent(agent: object) -> str:
        if agent is None or agent == "":
            return ""
        if not isinstance(agent, str):
            raise McpArgumentError("agent must be a string")
        if len(agent) > _AGENT_MAX_CHARS:
            raise McpArgumentError(
                f"agent exceeds {_AGENT_MAX_CHARS} characters"
            )
        return agent

    @staticmethod
    def _require_cursor(cursor: object) -> str | None:
        if cursor is None or cursor == "":
            return None
        if not isinstance(cursor, str):
            raise McpArgumentError("cursor must be a string message id")
        if len(cursor) > _CURSOR_MAX_CHARS:
            raise McpArgumentError(
                f"cursor exceeds {_CURSOR_MAX_CHARS} characters"
            )
        return cursor

    @staticmethod
    def _require_bool(value: object, name: str, *, default: bool = False) -> bool:
        if value is None:
            return default
        if not isinstance(value, bool):
            raise McpArgumentError(f"{name} must be a boolean")
        return value

    def _require_limit(self, limit: object) -> int:
        if limit is None:
            return MCP_DEFAULT_CALL_LIMIT
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise McpArgumentError("limit must be an integer")
        if limit < 1 or limit > MCP_MAX_CALL_LIMIT:
            raise McpArgumentError(
                f"limit must be between 1 and {MCP_MAX_CALL_LIMIT}"
            )
        return limit

    def _require_timeout(self, timeout_seconds: object) -> float | None:
        """Finite, positive and inside the configured/documented bounds."""
        if timeout_seconds is None:
            return None
        if isinstance(timeout_seconds, bool) or not isinstance(
            timeout_seconds, (int, float)
        ):
            raise McpArgumentError("timeout_seconds must be a finite number")
        value = float(timeout_seconds)
        if not math.isfinite(value) or value <= 0:
            raise McpArgumentError("timeout_seconds must be finite and positive")
        configured = float(self.opencode_config.idle_timeout_seconds)
        ceiling = min(configured, MCP_MAX_WAIT_SECONDS)
        if value > ceiling:
            raise McpArgumentError(
                f"timeout_seconds must not exceed {ceiling:g}s "
                "(the configured idle_timeout_seconds / documented MCP bound; "
                "an unlimited wait is not available)"
            )
        return value

    # ------------------------------------------------------------------
    # v0.3-D bounded orchestration helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _require_run_id(run_id: object) -> str:
        if not valid_run_id(run_id):
            raise McpArgumentError(
                "run_id must be an orchestration run id generated by "
                "devrelay_start_run ('DR-<32 hex characters>'); run ids are never "
                "supplied by the caller and never form a path"
            )
        return str(run_id)

    @staticmethod
    def _require_max_cycles(value: object) -> int:
        if value is None:
            return DEFAULT_MAX_CYCLES
        if isinstance(value, bool) or not isinstance(value, int):
            raise McpArgumentError("max_cycles must be an integer")
        if value < 1 or value > HARD_MAX_CYCLES:
            raise McpArgumentError(
                f"max_cycles must be between 1 and {HARD_MAX_CYCLES} "
                "(the v0.3-D hard bound; a caller cannot raise it)"
            )
        return int(value)

    @staticmethod
    def _require_decision(decision: object) -> str:
        allowed = tuple(item.value for item in Decision)
        if not isinstance(decision, str) or decision not in allowed:
            raise McpArgumentError(
                "decision must be exactly one of "
                f"{', '.join(allowed)} (DevRelay never derives a decision from "
                "reviewer text)"
            )
        return decision

    def _orchestration_failure(
        self, tool: str, exc: OrchestrationError, run_id: object
    ) -> McpEnvelope:
        """A local orchestration failure, with the run state when it is readable."""
        data: dict[str, Any] = {"run_id": run_id if isinstance(run_id, str) else None}
        if isinstance(run_id, str):
            try:
                data.update(self.orchestration.get_run(run_id).summary())
            except DevRelayError:
                # unknown or corrupt run: the run_id echo is all the context there is
                pass
        return error_envelope(
            tool,
            getattr(exc, "code", "orchestration_error"),
            exc,
            data,
        )

    @staticmethod
    def _orchestration_outcome(tool: str, outcome: object) -> McpEnvelope:
        """Shape one orchestration action: state is visible either way."""
        summary = outcome.summary  # type: ignore[attr-defined]
        if getattr(outcome, "ok", False):
            return ok_envelope(tool, summary)
        return error_envelope(
            tool,
            getattr(outcome, "error_type", "") or "orchestration_turn_blocked",
            getattr(outcome, "error_message", "")
            or "the orchestration action did not reach a confirmed completion",
            summary,
        )

    def devrelay_start_run(
        self,
        implementer_session_id: object = None,
        reviewer_session_id: object = None,
        max_cycles: object = None,
    ) -> McpEnvelope:
        """Create bounded orchestration state.  No model call, ever."""

        def call() -> McpEnvelope:
            impl_sid = self._require_session_id(implementer_session_id)
            rev_sid = self._require_session_id(reviewer_session_id)
            cycles = self._require_max_cycles(max_cycles)
            run = self.orchestration.start_run(
                implementer_session_id=impl_sid,
                reviewer_session_id=rev_sid,
                max_cycles=cycles,
            )
            return ok_envelope("devrelay_start_run", run.summary())

        return self._execute("devrelay_start_run", call)

    def devrelay_get_run(self, run_id: object = None) -> McpEnvelope:
        """Read durable run state locally (read-only, no OpenCode request)."""

        def call() -> McpEnvelope:
            rid = self._require_run_id(run_id)
            try:
                return ok_envelope(
                    "devrelay_get_run", self.orchestration.get_run(rid).summary()
                )
            except OrchestrationError as exc:
                return self._orchestration_failure("devrelay_get_run", exc, rid)

        return self._execute("devrelay_get_run", call)

    def devrelay_run_implementer(
        self, run_id: object = None, prompt: object = None
    ) -> McpEnvelope:
        """Run exactly one implementer turn (legal only in READY_IMPLEMENTER)."""

        def call() -> McpEnvelope:
            rid = self._require_run_id(run_id)
            try:
                text = self._require_prompt(prompt)
            except McpArgumentError as exc:
                return self._orchestration_failure("devrelay_run_implementer", exc, rid)
            try:
                outcome = self.orchestration.run_implementer(rid, text)
            except OrchestrationError as exc:
                return self._orchestration_failure("devrelay_run_implementer", exc, rid)
            return self._orchestration_outcome("devrelay_run_implementer", outcome)

        return self._execute("devrelay_run_implementer", call)

    def devrelay_run_reviewer(self, run_id: object = None, prompt: object = None) -> McpEnvelope:
        """Run exactly one reviewer turn (legal only in READY_REVIEWER)."""

        def call() -> McpEnvelope:
            rid = self._require_run_id(run_id)
            try:
                text = self._require_prompt(prompt)
            except McpArgumentError as exc:
                return self._orchestration_failure("devrelay_run_reviewer", exc, rid)
            try:
                outcome = self.orchestration.run_reviewer(rid, text)
            except OrchestrationError as exc:
                return self._orchestration_failure("devrelay_run_reviewer", exc, rid)
            return self._orchestration_outcome("devrelay_run_reviewer", outcome)

        return self._execute("devrelay_run_reviewer", call)

    def devrelay_decide_run(self, run_id: object = None, decision: object = None) -> McpEnvelope:
        """Record an explicit external decision.  No model call, ever."""

        def call() -> McpEnvelope:
            rid = self._require_run_id(run_id)
            try:
                value = self._require_decision(decision)
            except McpArgumentError as exc:
                return self._orchestration_failure("devrelay_decide_run", exc, rid)
            try:
                outcome = self.orchestration.decide_run(rid, value)
            except OrchestrationError as exc:
                return self._orchestration_failure("devrelay_decide_run", exc, rid)
            return self._orchestration_outcome("devrelay_decide_run", outcome)

        return self._execute("devrelay_decide_run", call)

    # ------------------------------------------------------------------
    # read-only tools
    # ------------------------------------------------------------------
    def devrelay_status(self) -> McpEnvelope:
        def call() -> McpEnvelope:
            config = self.opencode_config
            data: dict[str, Any] = {
                "schema_version": 1,
                "package_version": self.package_version,
                "workspace": str(self.workspace_root),
                "opencode": {
                    "configured": bool(config.configured),
                    "endpoint_authority": _endpoint_authority(config.base_url),
                    "token_source": "DEVRELAY_OPENCODE_TOKEN (environment only)",
                    "allow_unknown_workspace": bool(config.allow_unknown_workspace),
                    "timeout_seconds": float(config.timeout_seconds),
                    "idle_timeout_seconds": float(config.idle_timeout_seconds),
                    "max_messages": int(config.max_messages),
                },
                "bridge_operations": list(BRIDGE_OPERATIONS),
                # v0.3-C: role routing state (identifiers only, never secrets).
                "roles": self.roles.summary(),
                # v0.3-D: bounded-orchestration capability (never raw runs).
                "orchestration": {
                    "enabled": True,
                    "hard_max_cycles": HARD_MAX_CYCLES,
                    "default_max_cycles": DEFAULT_MAX_CYCLES,
                    "automatic_role_sequencing": False,
                    "automatic_decisions": False,
                    "durable_state": True,
                    "state_location": "orchestration/runs",
                    "recovery": "out of scope (v0.3-E)",
                },
                "ledger": {
                    "directory": "opencode/calls",
                    "present": (self.devrelay_dir / "opencode").is_dir(),
                },
                "mcp": {
                    "server": "devrelay",
                    "server_version": self.mcp_server_version,
                    "transport": "stdio",
                    "tools": list(TOOL_NAMES),
                    # v0.3-B: ALL tool execution is serialized in this process,
                    # not only the side-effecting tools (the accepted v0.3-A
                    # filesystem ledger is a single-writer store).
                    "execution_serialized": True,
                    "serialization": "one process-wide execution lock over all tools",
                    "side_effects_serialized": True,
                },
                "acceptance_authority": False,
            }
            return ok_envelope("devrelay_status", data)

        return self._execute("devrelay_status", call)

    def opencode_health(self) -> McpEnvelope:
        def call() -> McpEnvelope:
            result = self.bridge().health()
            return self._bridge_envelope(
                "opencode_health",
                result,
                failure_message="OpenCode health probe failed",
                error_type_fallback="provider_unavailable",
            )

        return self._execute("opencode_health", call)

    def opencode_list_sessions(
        self, include_other_workspaces: bool | None = None
    ) -> McpEnvelope:
        def call() -> McpEnvelope:
            include = self._require_bool(
                include_other_workspaces, "include_other_workspaces"
            )
            result = self.bridge().list_sessions(include_other_workspaces=include)
            return self._bridge_envelope(
                "opencode_list_sessions",
                result,
                failure_message="session listing failed",
                error_type_fallback="provider_unavailable",
            )

        return self._execute("opencode_list_sessions", call)

    def opencode_get_session(self, session_id: str | None = None) -> McpEnvelope:
        def call() -> McpEnvelope:
            sid = self._require_session_id(session_id)
            result = self.bridge().get_session(sid)
            # Envelope truthfulness: a provider failure (HTTP error, malformed
            # body, unreachable endpoint) must never be reported as success.
            return self._bridge_envelope(
                "opencode_get_session",
                result,
                failure_message="session read failed",
                error_type_fallback="provider_unavailable",
            )

        return self._execute("opencode_get_session", call)

    def opencode_read_messages(
        self, session_id: str | None = None, cursor: str | None = None
    ) -> McpEnvelope:
        def call() -> McpEnvelope:
            sid = self._require_session_id(session_id)
            position = self._require_cursor(cursor)
            result = self.bridge().read_messages(sid, position)
            return self._bridge_envelope(
                "opencode_read_messages",
                result,
                failure_message="message read failed",
                error_type_fallback="provider_unavailable",
            )

        return self._execute("opencode_read_messages", call)

    def opencode_calls(self, limit: int | None = None) -> McpEnvelope:
        def call() -> McpEnvelope:
            bound = self._require_limit(limit)
            sequence = sequence_state(self.devrelay_dir)
            records = read_records_strict(self.devrelay_dir, limit=bound)
            data = {
                "limit": bound,
                "count": len(records),
                "sequence": sequence,
                "records": records,
            }
            return ok_envelope("opencode_calls", data)

        return self._execute("opencode_calls", call)

    # ------------------------------------------------------------------
    # side-effecting tools (serialized with every other tool by _execute)
    # ------------------------------------------------------------------
    def opencode_send_prompt(
        self,
        session_id: str | None = None,
        prompt: str | None = None,
        agent: str | None = None,
        model: str | None = None,
    ) -> McpEnvelope:
        def call() -> McpEnvelope:
            sid = self._require_session_id(session_id)
            text = self._require_prompt(prompt)
            agent_value = self._require_agent(agent)
            model_value = self._require_model(model)
            result = self.bridge().send_prompt(
                sid, text, agent=agent_value, model=model_value
            )
            return self._send_prompt_envelope(result)

        return self._execute("opencode_send_prompt", call)

    def opencode_wait_idle(
        self, session_id: str | None = None, timeout_seconds: float | None = None
    ) -> McpEnvelope:
        def call() -> McpEnvelope:
            sid = self._require_session_id(session_id)
            timeout = self._require_timeout(timeout_seconds)
            result = self.bridge().wait_idle(sid, timeout)
            return self._bridge_envelope(
                "opencode_wait_idle",
                result,
                failure_message="session did not become idle/terminal inside the bound",
                error_type_fallback="not_idle",
            )

        return self._execute("opencode_wait_idle", call)

    def opencode_interrupt(self, session_id: str | None = None) -> McpEnvelope:
        def call() -> McpEnvelope:
            sid = self._require_session_id(session_id)
            result = self.bridge().interrupt(sid)
            return self._bridge_envelope(
                "opencode_interrupt",
                result,
                expect=lambda r: r.state is OpenCodeOperationState.INTERRUPTED,
                failure_message="the abort request was not accepted",
                error_type_fallback="interrupt_not_accepted",
                extra={
                    "interrupt_semantics": (
                        "an accepted abort request is not a verified terminal state"
                    )
                },
            )

        return self._execute("opencode_interrupt", call)

    # ------------------------------------------------------------------
    # v0.3-C role-aware tools (semantic role -> workspace-configured route)
    # ------------------------------------------------------------------
    def _role_failure(
        self, tool: str, exc: RoleRoutingError, requested: object
    ) -> McpEnvelope:
        """A local routing failure, with the requested role as evidence.

        Routing problems are never reported as provider failures, and this
        happens before any request that could submit a model turn.
        """
        requested_text = (
            bounded(requested, 64) if isinstance(requested, str) else ""
        )
        return error_envelope(
            tool,
            getattr(exc, "code", "role_routing_error"),
            exc,
            {
                "role": requested_text or None,
                "supported_roles": list(SUPPORTED_ROLES),
                "route_source": ROLE_ROUTE_SOURCE,
                "role_routing_configured": self.roles.summary()["configured"],
            },
        )

    def devrelay_list_roles(self) -> McpEnvelope:
        """Read-only view of the configured roles and their sanitized routes."""

        def call() -> McpEnvelope:
            summary = self.roles.summary()
            return ok_envelope(
                "devrelay_list_roles",
                {
                    "supported_roles": summary["supported_roles"],
                    "roles": summary["roles"],
                    "role_routing_configured": summary["configured"],
                    "route_source": summary["route_source"],
                    "read_only": True,
                    "acceptance_authority": False,
                },
            )

        return self._execute("devrelay_list_roles", call)

    def devrelay_get_role(self, role: object = None) -> McpEnvelope:
        """Resolve exactly one role to its configured route (read-only)."""

        def call() -> McpEnvelope:
            try:
                route = self.roles.resolve(role)
            except RoleRoutingError as exc:
                return self._role_failure("devrelay_get_role", exc, role)
            data = route.public()
            data.update(
                {
                    "configured": True,
                    "supported_roles": list(SUPPORTED_ROLES),
                    "read_only": True,
                    "acceptance_authority": False,
                }
            )
            return ok_envelope("devrelay_get_role", data)

        return self._execute("devrelay_get_role", call)

    def devrelay_send_role_prompt(
        self,
        role: object = None,
        session_id: object = None,
        prompt: object = None,
    ) -> McpEnvelope:
        """Send exactly one model turn as a semantic role.

        The route is resolved first (a routing failure is local and issues no
        request at all), then the session id and prompt are validated with the
        accepted v0.3-A rules, then the accepted
        :meth:`OpenCodeBridge.send_prompt` runs with the resolved model/agent.
        This tool accepts no ``model``/``agent`` argument by design.
        """

        def call() -> McpEnvelope:
            try:
                route = self.roles.resolve(role)
            except RoleRoutingError as exc:
                return self._role_failure("devrelay_send_role_prompt", exc, role)
            sid = self._require_session_id(session_id)
            text = self._require_prompt(prompt)
            try:
                outcome = self.roles.send_role_prompt(
                    self.bridge(), role=route.role, session_id=sid, prompt=text
                )
            except DevRelayError as exc:
                # An accepted v0.3-A failure keeps its exact code and message;
                # the role path additionally states which route was attempted, so
                # the caller can still audit the routing decision.  This is not a
                # provider reclassification and not a retry.
                return error_envelope(
                    "devrelay_send_role_prompt",
                    _error_type(exc),
                    exc,
                    route.route_evidence(),
                )
            return self._send_prompt_envelope(
                outcome.result,
                route=outcome.route,
                tool="devrelay_send_role_prompt",
            )

        return self._execute("devrelay_send_role_prompt", call)

    # ------------------------------------------------------------------
    # send_prompt envelope: preserve every nuance of the bridge result
    # ------------------------------------------------------------------
    @classmethod
    def _send_prompt_envelope(
        cls, result: Any, *, route: Any = None, tool: str = "opencode_send_prompt"
    ) -> McpEnvelope:
        """send_prompt envelope: success only for a confirmed completion.

        The same single rule as every other bridge-backed tool, plus the
        correlation nuance: a pending reply or an uncertain submission is **not**
        success, and ``retry_safe`` (derived from documented evidence only)
        travels with the evidence so a caller can distinguish "definitely not
        submitted" from "may already be running".

        The raw path (``opencode_send_prompt``) is unchanged: ``route`` is
        ``None`` there and no routing key appears in its ``data``.  The v0.3-C
        role path passes the resolved route, so the audit trail states exactly
        which semantic role was requested and which model/agent the workspace
        configured for it - it never claims which model "should" be used.
        """
        extra: dict[str, Any] = {
            "retry_safe": _retry_safe(result),
            "resubmit_policy": (
                "never resubmit automatically when submission_uncertain or "
                "reply_pending is set"
            ),
        }
        if route is not None:
            extra.update(route.route_evidence())
            extra["role_routing"] = (
                "semantic role resolved to the workspace-configured route; the "
                "caller cannot override the model or the agent"
            )
        return cls._bridge_envelope(
            tool,
            result,
            expect=lambda r: (
                r.ok and not r.reply_pending and not r.submission_uncertain
            ),
            error_type_fallback="submission_not_confirmed",
            failure_message=(
                "the prompt was accepted but no reply was confirmed"
                if result.reply_pending
                else "the prompt submission did not complete"
            ),
            extra=extra,
        )


def _retry_safe(result: Any) -> bool:
    """True only when DevRelay can prove nothing was submitted.

    Derived from documented bridge evidence, never from a guess:

    * no submission POST was issued at all (the probe/boundary failed first); or
    * the POST failed without any HTTP response *and* without submission
      uncertainty (the v0.3-A "definitely not submitted" class: connect/pool
      timeout, connect error, local refusal).

    An accepted submission (2xx, unusable body or not), an uncertain submission
    and a pending reply are never ``retry_safe``.
    """
    if not result.submission_attempted:
        return True
    return (
        result.submission_status is None
        and result.http_status is None
        and not result.submission_uncertain
        and not result.reply_pending
    )


def _error_type(exc: DevRelayError) -> str:
    code = getattr(exc, "code", "") or ""
    if code:
        return str(code)
    return type(exc).__name__


def _endpoint_authority(base_url: str) -> str:
    """``scheme://host[:port]`` only - never credentials, path or query."""
    if not base_url:
        return ""
    parts = urlsplit(base_url)
    if not parts.scheme or not parts.hostname:
        return ""
    authority = f"{parts.scheme}://{parts.hostname}"
    if parts.port:
        authority += f":{parts.port}"
    return authority


#: Exact tool inventory (order is the advertised order).
#: The nine v0.3-B tools are unchanged; v0.3-C appends exactly three.
TOOL_NAMES: tuple[str, ...] = (
    "devrelay_status",
    "opencode_health",
    "opencode_list_sessions",
    "opencode_get_session",
    "opencode_read_messages",
    "opencode_calls",
    "opencode_send_prompt",
    "opencode_wait_idle",
    "opencode_interrupt",
    "devrelay_list_roles",
    "devrelay_get_role",
    "devrelay_send_role_prompt",
    # v0.3-D appends exactly five bounded-orchestration tools.
    "devrelay_start_run",
    "devrelay_get_run",
    "devrelay_run_implementer",
    "devrelay_run_reviewer",
    "devrelay_decide_run",
)

READ_ONLY_TOOLS: tuple[str, ...] = (
    "devrelay_status",
    "devrelay_get_run",
    "devrelay_list_roles",
    "devrelay_get_role",
    "opencode_health",
    "opencode_list_sessions",
    "opencode_get_session",
    "opencode_read_messages",
    "opencode_calls",
    "opencode_wait_idle",
)

SIDE_EFFECTING_TOOLS: tuple[str, ...] = (
    "opencode_send_prompt",
    "opencode_interrupt",
    "devrelay_send_role_prompt",
    "devrelay_start_run",
    "devrelay_run_implementer",
    "devrelay_run_reviewer",
    "devrelay_decide_run",
)


__all__ = [
    "BRIDGE_OPERATIONS",
    "McpArgumentError",
    "McpToolSurface",
    "READ_ONLY_TOOLS",
    "SIDE_EFFECTING_TOOLS",
    "TOOL_NAMES",
]
