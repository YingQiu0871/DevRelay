"""Shared offline helpers for the v0.3-C role-routing suites.

Everything here is deterministic and offline: the real MCP SDK dispatch over the
real v0.3-A bridge wired to the accepted OpenCode stub (``httpx.MockTransport``).
No network, no model, no OpenCode process.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from devrelay.mcp.server import build_surface, create_server
from devrelay.opencode.accounting import FilesystemOpenCodeLedger
from devrelay.roles.models import RolesConfig

from opencode_stub import StubOpenCodeServer
from test_v03b_mcp_tools import envelope_of, make_workspace

#: Intentionally distinct fixtures: the two roles share neither provider nor
#: model, so any cross-routing is visible on the wire.
DISTINCT_ROLES: dict[str, Any] = {
    "implementer": {"model": "provider-a/model-a"},
    "reviewer": {"model": "provider-b/model-b"},
}
AGENT_ROLES: dict[str, Any] = {
    "implementer": {"model": "provider-a/model-a", "agent": "build"},
    "reviewer": {"model": "provider-b/model-b", "agent": "review"},
}
IMPLEMENTER_WIRE = {"providerID": "provider-a", "modelID": "model-a"}
REVIEWER_WIRE = {"providerID": "provider-b", "modelID": "model-b"}

ROLE_PROMPT = "Reply with exactly DEVRELAY_V03C_OK."


@dataclass(frozen=True)
class RolesHarness:
    surface: Any
    server: Any
    stub: StubOpenCodeServer
    ws: Path
    ledger: Any = None


def write_roles(ws: Path, roles: dict[str, Any] | None) -> Path:
    """Write (``dict``) or remove (``None``) the ``roles:`` wiring section."""
    path = ws / ".devrelay" / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if roles is None:
        data.pop("roles", None)
    else:
        data["roles"] = roles
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def roles_config(roles: dict[str, Any]) -> RolesConfig:
    return RolesConfig.model_validate(roles)


def build_roles_server(
    tmp_path: Path,
    roles: dict[str, Any] | None = DISTINCT_ROLES,
    *,
    opencode: dict[str, Any] | None = None,
    stub: StubOpenCodeServer | None = None,
    bind_stub: bool = True,
    bridge_factory: Any = None,
    ledger: Any = None,
) -> RolesHarness:
    """A real surface/server with a real bridge over the accepted stub.

    ``roles=None`` removes the ``roles:`` section entirely (a plain v0.3-B
    workspace); ``roles={}`` writes an empty section.
    """
    ws = make_workspace(tmp_path, **(opencode or {}))
    write_roles(ws, roles)
    stub = stub or StubOpenCodeServer(workspace=str(ws))
    if bind_stub:
        stub.workspace = str(ws)
        for session in stub.sessions:
            session["directory"] = str(ws)
    if bridge_factory is None:
        ledger = ledger or FilesystemOpenCodeLedger(ws / ".devrelay")

        def bridge_factory() -> Any:  # noqa: F811 - injected factory
            return stub.bridge(workspace_root=str(ws), ledger=ledger)

    surface = build_surface(ws, bridge_factory=bridge_factory)
    return RolesHarness(
        surface=surface,
        server=create_server(surface),
        stub=stub,
        ws=ws,
        ledger=ledger,
    )


def call(server: Any, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    return envelope_of(asyncio.run(server.call_tool(name, arguments or {})))


def call_result(server: Any, name: str, arguments: dict[str, Any] | None = None) -> Any:
    return asyncio.run(server.call_tool(name, arguments or {}))


def send_role(
    server: Any,
    role: Any,
    *,
    session_id: Any = "ses_match",
    prompt: Any = ROLE_PROMPT,
) -> dict[str, Any]:
    arguments: dict[str, Any] = {"session_id": session_id, "prompt": prompt}
    if role is not Ellipsis:
        arguments["role"] = role
    return call(server, "devrelay_send_role_prompt", arguments)


def wire_bodies(stub: StubOpenCodeServer) -> list[dict[str, Any]]:
    """Raw ``POST /session/{id}/message`` bodies the accepted stub received."""
    return list(stub.prompts)


def last_wire_body(stub: StubOpenCodeServer) -> dict[str, Any]:
    assert stub.prompts, "no submission reached the provider"
    return stub.prompts[-1]


def posts(stub: StubOpenCodeServer) -> list[str]:
    return [path for method, path in stub.requests if method == "POST"]


def prompt_texts(stub: StubOpenCodeServer) -> list[str]:
    texts = []
    for body in stub.prompts:
        parts = body.get("parts") or []
        texts.append("".join(str(p.get("text", "")) for p in parts))
    return texts


def ledger_records(ws: Path, limit: int = 200) -> list[dict[str, Any]]:
    from devrelay.mcp.ledger import read_records_strict

    return read_records_strict(ws / ".devrelay", limit=limit)


def json_text(envelope: dict[str, Any]) -> str:
    return json.dumps(envelope, ensure_ascii=False)
