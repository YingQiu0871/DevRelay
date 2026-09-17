"""Shared offline harness for the v0.3-D bounded-orchestration suites.

Deterministic and offline: the real MCP SDK dispatch, the real v0.3-D
orchestration service, the real v0.3-C role router and the real accepted v0.3-A
bridge wired to the accepted OpenCode stub (``httpx.MockTransport``).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from devrelay.mcp.server import build_surface, create_server
from devrelay.opencode.accounting import FilesystemOpenCodeLedger
from devrelay.orchestration import OrchestrationStore

from opencode_stub import StubOpenCodeServer
from test_v03b_mcp_tools import envelope_of, make_workspace

#: Two distinct role sessions (v0.3-D forbids sharing one session).
IMPLEMENTER_SESSION = "ses_impl"
REVIEWER_SESSION = "ses_rev"

DISTINCT_ROLES: dict[str, Any] = {
    "implementer": {"model": "provider-a/model-a"},
    "reviewer": {"model": "provider-b/model-b"},
}
AGENT_ROLES: dict[str, Any] = {
    "implementer": {"model": "provider-a/model-a", "agent": "build"},
    "reviewer": {"model": "provider-b/model-b", "agent": "review"},
}

RUN_ID = "DR-" + "a" * 32


def fixed_run_ids(*ids: str):
    """A deterministic run-id factory for tests."""
    remaining = list(ids) or [RUN_ID]

    def factory() -> str:
        return remaining.pop(0) if len(remaining) > 1 else remaining[0]

    return factory


def make_run(**overrides: Any):
    """A valid run document for policy/model tests."""
    from devrelay.orchestration import OrchestrationRun, RoleRouteSnapshot

    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "workspace": "C:/ws",
        "implementer_session_id": IMPLEMENTER_SESSION,
        "reviewer_session_id": REVIEWER_SESSION,
        "max_cycles": 2,
        "model_turn_budget": 4,
        "route_snapshot": {
            "implementer": RoleRouteSnapshot(role="implementer", model="provider-a/model-a"),
            "reviewer": RoleRouteSnapshot(role="reviewer", model="provider-b/model-b"),
        },
    }
    payload.update(overrides)
    return OrchestrationRun(**payload)


def write_roles(ws: Path, roles: dict[str, Any] | None) -> None:
    path = ws / ".devrelay" / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if roles is None:
        data.pop("roles", None)
    else:
        data["roles"] = roles
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def two_session_stub(ws: Path, **kwargs: Any) -> StubOpenCodeServer:
    stub = StubOpenCodeServer(workspace=str(ws), **kwargs)
    base = dict(stub.sessions[0])
    stub.sessions = [
        dict(base, id=IMPLEMENTER_SESSION, directory=str(ws)),
        dict(base, id=REVIEWER_SESSION, directory=str(ws)),
    ]
    stub.workspace = str(ws)
    for session in stub.sessions:
        session["directory"] = str(ws)
    return stub


@dataclass(frozen=True)
class Harness:
    surface: Any
    server: Any
    stub: StubOpenCodeServer
    ws: Path
    ledger: Any

    @property
    def service(self) -> Any:
        return self.surface.orchestration

    @property
    def posts(self) -> list[str]:
        return [path for method, path in self.stub.requests if method == "POST"]

    @property
    def requests(self) -> list[tuple[str, str]]:
        return list(self.stub.requests)


def build(
    tmp_path: Path,
    *,
    roles: dict[str, Any] | None = DISTINCT_ROLES,
    stub: StubOpenCodeServer | None = None,
    run_id_factory: Any = None,
    bridge_factory: Any = None,
) -> Harness:
    ws = make_workspace(tmp_path)
    write_roles(ws, roles)
    stub = stub or two_session_stub(ws)
    ledger = FilesystemOpenCodeLedger(ws / ".devrelay")
    if bridge_factory is None:

        def bridge_factory() -> Any:  # noqa: F811 - injected factory
            return stub.bridge(workspace_root=str(ws), ledger=ledger)

    surface = build_surface(ws, bridge_factory=bridge_factory)
    if run_id_factory is not None:
        surface.orchestration.store = OrchestrationStore(
            ws / ".devrelay", run_id_factory=run_id_factory
        )
    return Harness(
        surface=surface,
        server=create_server(surface),
        stub=stub,
        ws=ws,
        ledger=ledger,
    )


def call(server: Any, tool: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    return envelope_of(asyncio.run(server.call_tool(tool, arguments or {})))


def call_result(server: Any, tool: str, arguments: dict[str, Any] | None = None) -> Any:
    return asyncio.run(server.call_tool(tool, arguments or {}))


def start(
    server: Any,
    *,
    max_cycles: int = 1,
    implementer_session: str = IMPLEMENTER_SESSION,
    reviewer_session: str = REVIEWER_SESSION,
) -> dict[str, Any]:
    return call(
        server,
        "devrelay_start_run",
        {
            "implementer_session_id": implementer_session,
            "reviewer_session_id": reviewer_session,
            "max_cycles": max_cycles,
        },
    )


def run_id_of(server: Any, **kwargs: Any) -> str:
    envelope = start(server, **kwargs)
    assert envelope["ok"] is True, envelope
    return envelope["data"]["run_id"]


def phase(server: Any, tool: str, run_id: str, prompt: str = "phase prompt") -> dict[str, Any]:
    return call(server, tool, {"run_id": run_id, "prompt": prompt})


def decide(server: Any, run_id: str, decision: str) -> dict[str, Any]:
    return call(server, "devrelay_decide_run", {"run_id": run_id, "decision": decision})


def get_run(server: Any, run_id: str) -> dict[str, Any]:
    return call(server, "devrelay_get_run", {"run_id": run_id})


def state_path(ws: Path, run_id: str) -> Path:
    return ws / ".devrelay" / "orchestration" / "runs" / f"{run_id}.json"


def raw_payload(ws: Path, run_id: str) -> dict[str, Any]:
    import json

    return json.loads(state_path(ws, run_id).read_text(encoding="utf-8"))
