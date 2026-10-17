"""MCP server construction for the DevRelay tool surface (v0.3-B).

Responsibilities:

* resolve the **one** bound workspace once and fail closed when its DevRelay
  configuration is invalid (before any tool is served);
* build the :class:`~devrelay.mcp.tools.McpToolSurface` bound to that workspace;
* register the exact tool inventory with MCP-safe names, typed input schemas,
  honest annotations (read-only vs side-effecting; no false idempotency) and
  planner-oriented descriptions;
* normalize every failure DevRelay can see into the envelope instead of a
  traceback (a failed envelope also sets the protocol ``isError`` flag while
  keeping the structured envelope), while keeping diagnostics on stderr.  Verified SDK fact (mcp 2.2.0):
  ``MCPServer`` converts tool failures into an ``isError`` result *before* the
  middleware tier runs, so DevRelay normalizes inside the tool bodies.  That is
  why every tool parameter is optional at the schema level and validated by
  DevRelay itself: malformed arguments therefore still produce the envelope.
  A value the SDK's own JSON-schema check rejects (for example a JSON object
  where a string is required) surfaces as the SDK's bounded error text - no
  traceback, no secrets - which is documented in the v0.3-B specification;
* run the local **stdio** transport (no HTTP listener, no LAN exposure).

The MCP SDK is the official ``mcp`` Python SDK; see
``docs/v0.3/V03B_SPEC.md`` for the pinned version and the inspected API facts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from devrelay.config import ConfigError, load_wiring_config
from devrelay.errors import DevRelayError
from devrelay.mcp.models import (
    MCP_SCHEMA_VERSION,
    MCP_SERVER_NAME,
    MCP_SERVER_TITLE,
    McpEnvelope,
    bounded,
    error_envelope,
)
from devrelay.mcp.tools import McpToolSurface

#: DevRelay MCP server version advertised to clients (independent of the
#: unreleased package version).  ``0.3.0-d`` advertises the v0.3-D surface: the
#: nine v0.3-B tools and the three v0.3-C role tools unchanged, plus exactly five
#: bounded-orchestration tools (17 in total).
MCP_SERVER_VERSION = "0.3.0-e"

#: Marker key the dispatcher uses to carry a prepared envelope through the
#: SDK's result conversion.
_ENVELOPE_KEY = "__devrelay_envelope__"


class McpStartupError(DevRelayError):
    """The MCP server could not be bound to a usable workspace."""

    code = "mcp_startup_error"


def _diag(message: str) -> None:
    """Bounded operational diagnostic on **stderr** (stdout is MCP-only)."""
    print(f"[devrelay-mcp] {bounded(message, 500)}", file=sys.stderr, flush=True)


def _envelope_result(envelope: McpEnvelope) -> Any:
    """Shape one prepared envelope as the MCP tool result.

    Verified SDK fact (mcp 2.2.0): a pydantic return value becomes both
    ``structuredContent`` and a JSON text fallback.  For a *failed* envelope the
    adapter additionally returns an explicit ``CallToolResult`` with
    ``isError = true`` so a client that only checks the protocol flag still sees
    a failure - while ``structuredContent`` keeps the whole DevRelay envelope
    (``ok``, ``data.submission_uncertain``, ``data.reply_pending``, ...), so
    nothing is collapsed into plain text or into a bare "failed".
    """
    if envelope.ok:
        return envelope
    from mcp.types import CallToolResult, TextContent

    payload = envelope.model_dump(mode="json")
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(payload, indent=2))],
        structuredContent=payload,
        isError=True,
    )


def resolve_workspace(workspace: str | Path) -> tuple[Path, Any, Path]:
    """Resolve and validate the single bound workspace (fail closed).

    Returns ``(workspace_root, wiring, devrelay_dir)``.  Raises
    :class:`McpStartupError` when the path is not an initialized DevRelay
    workspace or its wiring cannot be loaded - the process must refuse to serve
    tools rather than guess a workspace.
    """
    if workspace is None or str(workspace).strip() == "":
        raise McpStartupError("--workspace <absolute path> is required")
    root = Path(workspace)
    try:
        root = root.resolve(strict=True)
    except OSError as exc:
        raise McpStartupError(
            f"workspace {workspace!r} cannot be resolved ({type(exc).__name__})"
        ) from exc
    if not root.is_dir():
        raise McpStartupError(f"workspace {root} is not a directory")
    devrelay_dir = root / ".devrelay"
    if not devrelay_dir.is_dir():
        raise McpStartupError(
            f"workspace {root} is not an initialized DevRelay workspace "
            "(no .devrelay directory; run 'devrelay init' there first)"
        )
    try:
        wiring = load_wiring_config(root)
    except ConfigError as exc:
        raise McpStartupError(f"invalid DevRelay configuration in {root}: {exc}") from exc
    return root, wiring, devrelay_dir


def build_surface(
    workspace: str | Path,
    *,
    bridge_factory: Callable[[], Any] | None = None,
    diagnostics: Callable[[str], None] | None = None,
) -> McpToolSurface:
    """Build the tool surface for one bound workspace."""
    from devrelay import __version__

    root, wiring, devrelay_dir = resolve_workspace(workspace)
    return McpToolSurface(
        workspace_root=root,
        wiring=wiring,
        devrelay_dir=devrelay_dir,
        bridge_factory=bridge_factory,
        package_version=__version__,
        mcp_server_version=MCP_SERVER_VERSION,
        diagnostics=diagnostics or _diag,
    )


# ---------------------------------------------------------------------------
# tool descriptions: part of the safety surface (the consumer is an LLM planner)
# ---------------------------------------------------------------------------
_START_RUN_DESCRIPTION = (
    "Create bounded orchestration state for ONE run over the already configured "
    "semantic roles. It performs NO model call, accepts no task prompt and "
    "requires two existing, different OpenCode sessions (implementer and "
    "reviewer) that already belong to this workspace - DevRelay never creates, "
    "infers or reuses a session. It records max_cycles (1..3, default 2) and "
    "returns the durable run state; nothing runs until you explicitly call "
    "devrelay_run_implementer / devrelay_run_reviewer / devrelay_decide_run."
)

_GET_RUN_DESCRIPTION = (
    "Read-only view of one orchestration run from durable local state (no "
    "OpenCode request, no mutation): state, cycle, completed_cycles, max_cycles, "
    "model-turn slots used/budget, terminal flag, blocked reason, the role-route "
    "snapshot captured at creation, per-turn sanitized evidence and the decision "
    "history. A persisted document that cannot have produced its own state, "
    "counters or history is refused as orchestration_state_corrupt instead of "
    "being reported as a run. Never returns raw prompts, provider replies or "
    "credentials."
)

_RUN_IMPLEMENTER_DESCRIPTION = (
    "Run exactly ONE implementer role turn for an orchestration run, legal only "
    "in READY_IMPLEMENTER. A duplicate attempt that is simply illegal for the "
    "current state fails locally without submitting another model turn; if a "
    "previously interrupted phase is still persisted as in-flight, this tool "
    "REFUSES without mutating (orchestration_recovery_required): the interrupted "
    "turn is never replayed - call devrelay_reconcile_run and then "
    "devrelay_resolve_recovery(mark_unrecoverable). The prompt is supplied by "
    "you; the model and agent come from the workspace role configuration and "
    "cannot be overridden. On a confirmed completion the run moves to "
    "READY_REVIEWER. On uncertainty, a pending reply or any failure the run is "
    "BLOCKED: it is never retried, the reviewer is never invoked automatically, "
    "and no further model-turn slot is consumed."
)

_RUN_REVIEWER_DESCRIPTION = (
    "Run exactly ONE reviewer role turn for an orchestration run, legal only in "
    "READY_REVIEWER. The reviewer uses its own session and the configured "
    "reviewer route; you supply the prompt. DevRelay never interprets the "
    "reviewer's text (APPROVE / REQUEST_CHANGES / any prose): a confirmed "
    "completion always stops at AWAITING_DECISION and only your explicit "
    "devrelay_decide_run may advance the run. Uncertainty or failure blocks the "
    "run without retry. An interrupted in-flight reviewer turn is refused, not "
    "replayed: reconcile it and resolve it via devrelay_reconcile_run / "
    "devrelay_resolve_recovery(mark_unrecoverable)."
)

_DECIDE_RUN_DESCRIPTION = (
    "Record an EXPLICIT external decision for a run that is AWAITING_DECISION - "
    "there is no model call. Decisions are exactly: complete (you close the run), "
    "request_changes (allow one more bounded implementer/reviewer cycle if cycle "
    "budget remains, otherwise LIMIT_REACHED - it never starts the cycle for you) "
    "and stop (administrative terminal stop). The decision source is recorded as "
    "external_planner; reviewer message text is never a decision input. A run "
    "holding an interrupted turn or sitting in RECOVERY_REQUIRED refuses this "
    "tool without mutating."
)

_RECONCILE_RUN_DESCRIPTION = (
    "Read-only recovery evidence for ONE run: whether it holds a live interrupted "
    "turn, its frozen recovery record, and the join between that attempt, the "
    "strict OpenCode call ledger and the bounded session-history window. Ledger "
    "gaps, torn records, multiple digest matches and unreadable history are "
    "reported as evidence_gap/evidence_conflict - absence of a record is never "
    "proof of non-submission, and nothing here is inferred from silence. Adoption "
    "is reported as unavailable in this build. This tool writes nothing, submits "
    "no model request and never resumes a run."
)

_RESOLVE_RECOVERY_DESCRIPTION = (
    "Apply exactly ONE fail-closed recovery resolution to a run that holds an "
    "interrupted turn (or is already in RECOVERY_REQUIRED): materialize that "
    "interrupted attempt as exactly one blocked turn and end the run BLOCKED "
    "(mark_unrecoverable). Nothing is resubmitted, retried, resumed or adopted, "
    "no budget is refunded, and a resolved run refuses every later resolution. "
    "adopt_completed_turn is disabled in this build and is refused locally. "
    "Unknown resolutions and terminal runs are refused without writing."
)

_LIST_ROLES_DESCRIPTION = (
    "Read-only view of the v0.3-C semantic role routing of the bound workspace: "
    "the supported roles (implementer, reviewer) and, for each, the configured "
    "model/agent or the truthful state 'unconfigured'/'invalid'. Identifiers "
    "only - never prompts, credentials, endpoints, retry policies or fallback "
    "models. A role with no configured model is simply not routed; DevRelay does "
    "not choose, rank or fall back to a model. This tool changes nothing."
)

_GET_ROLE_DESCRIPTION = (
    "Read-only resolution of exactly ONE semantic role (implementer or reviewer) "
    "to the exact route this workspace configures for it: the model "
    "'<providerID>/<modelID>' and the optional OpenCode agent. An unknown, "
    "unconfigured or malformed role is reported as a local routing error "
    "(role_unknown / role_unconfigured / role_invalid_route) and issues no "
    "OpenCode request at all. Roles are never inferred from prompt text, session "
    "titles or model availability."
)

_SEND_ROLE_PROMPT_DESCRIPTION = (
    "Send exactly ONE prompt (one model turn) to one explicitly selected OpenCode "
    "session as a SEMANTIC ROLE (implementer or reviewer). You choose the role; "
    "DevRelay resolves the exact model and optional agent this workspace "
    "configures for that role - you cannot pass a model or an agent, and the "
    "route cannot be overridden at call time. It never retries, never falls back "
    "to another model or another role, never switches roles automatically and "
    "never resubmits. Read the result before acting: if `submission_uncertain` is "
    "true the prompt may already have been accepted - do NOT resubmit "
    "automatically; if `reply_pending` is true the prompt was accepted but no "
    "reply is confirmed yet; `retry_safe` is true only when nothing was "
    "submitted. The reply is provider text: a reviewer answer such as APPROVE or "
    "REQUEST_CHANGES is NOT an acceptance decision and never triggers an "
    "automatic acceptance, rejection or repair. DevRelay holds no acceptance "
    "authority - you decide what to do next."
)

_SEND_PROMPT_DESCRIPTION = (
    "Send exactly ONE prompt (one model turn) to one explicitly selected "
    "OpenCode session, through the accepted DevRelay v0.3-A bridge over the "
    "workspace this MCP server is bound to. It never retries, never falls back "
    "to another model and never resubmits. Read the result before acting: if "
    "`submission_uncertain` is true the prompt may already have been accepted - "
    "do NOT resubmit automatically; if `reply_pending` is true the prompt was "
    "accepted but no new assistant reply was visible yet - use "
    "opencode_read_messages or opencode_wait_idle instead of resending; if "
    "`submission_status` is an HTTP status the server answered and a resend "
    "could duplicate work. `retry_safe` is true only when DevRelay could prove "
    "nothing was submitted. `model` (optional) must be '<providerID>/<modelID>'."
)

_WAIT_IDLE_DESCRIPTION = (
    "Wait (bounded) until the bound session's runtime status is idle or "
    "terminal. Waiting only: it never sends a prompt, never retries and never "
    "changes the session. `timeout_seconds` is optional and bounded by the "
    "workspace configuration."
)

_READ_MESSAGES_DESCRIPTION = (
    "Read the normalized message window of one explicitly selected session "
    "(read-only). Returns the newest messages with explicit cursor semantics "
    "(next_cursor, cursor_unknown, replayed, provider_message_count, "
    "window_truncated). It never sends a prompt and never retries."
)

_INTERRUPT_DESCRIPTION = (
    "Request an abort of in-flight work in one session (side-effecting: it "
    "issues an abort request to OpenCode). An accepted abort request is NOT "
    "proof that the remote work has stopped - `interrupt_verified` is always "
    "false in v0.3-A semantics. It never sends a prompt and never retries."
)

_CALLS_DESCRIPTION = (
    "Read-only view of DevRelay's durable OpenCode call ledger for the bound "
    "workspace (one record per issued request: state, timing, HTTP status, "
    "error type and non-secret metadata). Ledger corruption is reported as an "
    "explicit error instead of an empty list."
)

_HEALTH_DESCRIPTION = (
    "Probe the configured OpenCode endpoint through the accepted bridge "
    "(read-only): health, version and advertised capabilities."
)

_SESSIONS_DESCRIPTION = (
    "List OpenCode sessions with their workspace-ownership verdict (read-only). "
    "By default only sessions belonging to the bound workspace are returned."
)

_GET_SESSION_DESCRIPTION = (
    "Read one explicitly selected OpenCode session with its ownership verdict "
    "(read-only). Unknown sessions and foreign workspaces still fail closed "
    "exactly as in v0.3-A."
)

_STATUS_DESCRIPTION = (
    "Sanitized DevRelay/MCP status for the bound workspace (read-only): schema "
    "and package versions, bound workspace, OpenCode endpoint authority, whether "
    "OpenCode is configured, the bridge operations this surface exposes, the "
    "exact MCP tool inventory, the v0.3-C role-routing state (which semantic "
    "roles are configured, identifiers only) and the fact that DevRelay holds "
    "no acceptance authority. Never returns tokens, credentials or raw "
    "configuration."
)


def create_server(
    surface: McpToolSurface,
    *,
    diagnostics: Callable[[str], None] | None = None,
) -> Any:
    """Build the MCP ``MCPServer`` with the exact DevRelay tool inventory.

    The import is local so importing :mod:`devrelay.mcp` (or any DevRelay module)
    never requires the optional MCP SDK.
    """
    from mcp.server.mcpserver import MCPServer
    from mcp.server.context import ServerMiddleware  # noqa: F401 - protocol check
    from mcp.types import ToolAnnotations

    diag = diagnostics or _diag

    server: Any = MCPServer(
        name=MCP_SERVER_NAME,
        title=MCP_SERVER_TITLE,
        description=(
            "DevRelay MCP tool surface (v0.3-B): invoke the accepted v0.3-A "
            "OpenCode session bridge of one bound workspace."
        ),
        instructions=(
            "Tools operate on exactly ONE DevRelay workspace, fixed when this "
            "server started. DevRelay is an adapter, not an orchestrator: it "
            "does not choose or rank models (a semantic role resolves to the "
            "model and agent this workspace configured for it), does not approve "
            "code and does not sequence your work. opencode_send_prompt is the "
            "raw path (you supply model/agent); devrelay_send_role_prompt is the "
            "role path (you supply only implementer or reviewer and cannot "
            "override the route). Both send exactly one model turn and never "
            "retry - inspect submission_uncertain / reply_pending / retry_safe "
            "before deciding anything, and never resubmit automatically. "
            "devrelay_start_run / devrelay_run_implementer / devrelay_run_reviewer "
            "/ devrelay_decide_run add bounded orchestration state: each phase is "
            "one explicit call, a successful reviewer turn always stops at "
            "AWAITING_DECISION, reviewer text is never interpreted, uncertainty "
            "blocks the run instead of retrying, and only your explicit decision "
            "(complete / request_changes / stop) advances it - all within a hard "
            "cycle bound. v0.3-E adds fail-closed recovery: an interrupted turn is "
            "never replayed, devrelay_reconcile_run reports bounded evidence "
            "read-only, and devrelay_resolve_recovery(mark_unrecoverable) records "
            "exactly one blocked turn and ends the run BLOCKED. Adoption is "
            "disabled in this build."
        ),
        version=MCP_SERVER_VERSION,
    )

    read_only = ToolAnnotations(read_only_hint=True, open_world_hint=True)
    local_read_only = ToolAnnotations(read_only_hint=True, open_world_hint=False)
    side_effecting = ToolAnnotations(
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    )
    aborting = ToolAnnotations(
        read_only_hint=False,
        destructive_hint=True,
        idempotent_hint=False,
        open_world_hint=True,
    )

    @server.tool(
        name="devrelay_status",
        title="DevRelay MCP status",
        description=_STATUS_DESCRIPTION,
        annotations=local_read_only,
    )
    def devrelay_status() -> McpEnvelope:
        return _envelope_result(surface.devrelay_status())

    @server.tool(
        name="opencode_health",
        title="OpenCode health",
        description=_HEALTH_DESCRIPTION,
        annotations=read_only,
    )
    def opencode_health() -> McpEnvelope:
        return _envelope_result(surface.opencode_health())

    @server.tool(
        name="opencode_list_sessions",
        title="List OpenCode sessions",
        description=_SESSIONS_DESCRIPTION,
        annotations=read_only,
    )
    def opencode_list_sessions(
        include_other_workspaces: bool | None = None,
    ) -> McpEnvelope:
        return _envelope_result(
            surface.opencode_list_sessions(include_other_workspaces)
        )

    @server.tool(
        name="opencode_get_session",
        title="Read one OpenCode session",
        description=_GET_SESSION_DESCRIPTION,
        annotations=read_only,
    )
    def opencode_get_session(session_id: str | None = None) -> McpEnvelope:
        return _envelope_result(surface.opencode_get_session(session_id))

    @server.tool(
        name="opencode_read_messages",
        title="Read OpenCode messages",
        description=_READ_MESSAGES_DESCRIPTION,
        annotations=read_only,
    )
    def opencode_read_messages(
        session_id: str | None = None, cursor: str | None = None
    ) -> McpEnvelope:
        return _envelope_result(surface.opencode_read_messages(session_id, cursor))

    @server.tool(
        name="opencode_calls",
        title="Read the OpenCode call ledger",
        description=_CALLS_DESCRIPTION,
        annotations=local_read_only,
    )
    def opencode_calls(limit: int | None = None) -> McpEnvelope:
        return _envelope_result(surface.opencode_calls(limit))

    @server.tool(
        name="opencode_send_prompt",
        title="Send one prompt to an OpenCode session",
        description=_SEND_PROMPT_DESCRIPTION,
        annotations=side_effecting,
    )
    def opencode_send_prompt(
        session_id: str | None = None,
        prompt: str | None = None,
        agent: str | None = None,
        model: str | None = None,
    ) -> McpEnvelope:
        return _envelope_result(
            surface.opencode_send_prompt(session_id, prompt, agent, model)
        )

    @server.tool(
        name="opencode_wait_idle",
        title="Wait for an OpenCode session to go idle",
        description=_WAIT_IDLE_DESCRIPTION,
        annotations=read_only,
    )
    def opencode_wait_idle(
        session_id: str | None = None, timeout_seconds: float | None = None
    ) -> McpEnvelope:
        return _envelope_result(surface.opencode_wait_idle(session_id, timeout_seconds))

    @server.tool(
        name="opencode_interrupt",
        title="Request an abort of a session",
        description=_INTERRUPT_DESCRIPTION,
        annotations=aborting,
    )
    def opencode_interrupt(session_id: str | None = None) -> McpEnvelope:
        return _envelope_result(surface.opencode_interrupt(session_id))

    # ---- v0.3-C role-aware tools (same surface, same execution boundary) ----
    @server.tool(
        name="devrelay_list_roles",
        title="List configured DevRelay roles",
        description=_LIST_ROLES_DESCRIPTION,
        annotations=local_read_only,
    )
    def devrelay_list_roles() -> McpEnvelope:
        return _envelope_result(surface.devrelay_list_roles())

    @server.tool(
        name="devrelay_get_role",
        title="Resolve one DevRelay role",
        description=_GET_ROLE_DESCRIPTION,
        annotations=local_read_only,
    )
    def devrelay_get_role(role: str | None = None) -> McpEnvelope:
        return _envelope_result(surface.devrelay_get_role(role))

    @server.tool(
        name="devrelay_send_role_prompt",
        title="Send one prompt as a configured role",
        description=_SEND_ROLE_PROMPT_DESCRIPTION,
        annotations=side_effecting,
    )
    def devrelay_send_role_prompt(
        role: str | None = None,
        session_id: str | None = None,
        prompt: str | None = None,
    ) -> McpEnvelope:
        return _envelope_result(
            surface.devrelay_send_role_prompt(role, session_id, prompt)
        )

    # ---- v0.3-D bounded orchestration tools (same surface, same boundary) ----
    @server.tool(
        name="devrelay_start_run",
        title="Start a bounded orchestration run",
        description=_START_RUN_DESCRIPTION,
        annotations=side_effecting,
    )
    def devrelay_start_run(
        implementer_session_id: str | None = None,
        reviewer_session_id: str | None = None,
        max_cycles: int | None = None,
    ) -> McpEnvelope:
        return _envelope_result(
            surface.devrelay_start_run(
                implementer_session_id, reviewer_session_id, max_cycles
            )
        )

    @server.tool(
        name="devrelay_get_run",
        title="Read an orchestration run",
        description=_GET_RUN_DESCRIPTION,
        annotations=local_read_only,
    )
    def devrelay_get_run(run_id: str | None = None) -> McpEnvelope:
        return _envelope_result(surface.devrelay_get_run(run_id))

    @server.tool(
        name="devrelay_run_implementer",
        title="Run the implementer phase",
        description=_RUN_IMPLEMENTER_DESCRIPTION,
        annotations=side_effecting,
    )
    def devrelay_run_implementer(
        run_id: str | None = None, prompt: str | None = None
    ) -> McpEnvelope:
        return _envelope_result(surface.devrelay_run_implementer(run_id, prompt))

    @server.tool(
        name="devrelay_run_reviewer",
        title="Run the reviewer phase",
        description=_RUN_REVIEWER_DESCRIPTION,
        annotations=side_effecting,
    )
    def devrelay_run_reviewer(
        run_id: str | None = None, prompt: str | None = None
    ) -> McpEnvelope:
        return _envelope_result(surface.devrelay_run_reviewer(run_id, prompt))

    @server.tool(
        name="devrelay_decide_run",
        title="Record an external decision",
        description=_DECIDE_RUN_DESCRIPTION,
        annotations=side_effecting,
    )
    def devrelay_decide_run(
        run_id: str | None = None, decision: str | None = None
    ) -> McpEnvelope:
        return _envelope_result(surface.devrelay_decide_run(run_id, decision))

    @server.tool(
        name="devrelay_reconcile_run",
        title="Read recovery evidence for a run",
        description=_RECONCILE_RUN_DESCRIPTION,
        annotations=local_read_only,
    )
    def devrelay_reconcile_run(run_id: str | None = None) -> McpEnvelope:
        return _envelope_result(surface.devrelay_reconcile_run(run_id))

    @server.tool(
        name="devrelay_resolve_recovery",
        title="Resolve an interrupted run fail-closed",
        description=_RESOLVE_RECOVERY_DESCRIPTION,
        annotations=side_effecting,
    )
    def devrelay_resolve_recovery(
        run_id: str | None = None, resolution: str | None = None
    ) -> McpEnvelope:
        return _envelope_result(surface.devrelay_resolve_recovery(run_id, resolution))

    return server


def serve(workspace: str | Path, *, bridge_factory: Callable[[], Any] | None = None) -> None:
    """Run the DevRelay MCP server over stdio until the client disconnects."""
    surface = build_surface(workspace, bridge_factory=bridge_factory)
    server = create_server(surface)
    _diag(
        f"serving MCP over stdio for workspace {surface.workspace_root} "
        f"(schema v{MCP_SCHEMA_VERSION}, server {MCP_SERVER_VERSION})"
    )
    server.run(transport="stdio")


__all__ = [
    "MCP_SERVER_VERSION",
    "McpStartupError",
    "build_surface",
    "create_server",
    "resolve_workspace",
    "serve",
]
