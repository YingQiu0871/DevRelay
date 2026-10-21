"""Role-aware execution (v0.3-C): the semantic-role prompt path.

``RoleRouter.send_role_prompt`` resolves one role to its exact configured route
and delegates to the **accepted v0.3-A** ``OpenCodeBridge.send_prompt``.  There
is no second HTTP path, no orchestration, no retry, no fallback and no automatic
role switch: a role-aware send is exactly one model turn through the accepted
bridge, with the model/agent taken only from workspace configuration.

The public operation deliberately accepts **no** ``model`` or ``agent``
argument - that is a P1 invariant of v0.3-C (otherwise ``role=reviewer`` with
``model=<implementer model>`` would make routing meaningless).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from devrelay.roles.models import RoleRoute, RolesConfig
from devrelay.roles.resolver import list_roles, resolve_role, roles_summary

__all__ = ["RolePromptOutcome", "RoleRouter"]


@dataclass(frozen=True)
class RolePromptOutcome:
    """One role-routed submission: the resolved route plus the accepted result."""

    route: RoleRoute
    result: Any

    @property
    def ok(self) -> bool:
        return bool(getattr(self.result, "ok", False))


class RoleRouter:
    """Resolve semantic roles and run role-aware sends for one workspace."""

    def __init__(self, roles: RolesConfig | None = None) -> None:
        self._roles = roles

    @property
    def roles(self) -> RolesConfig | None:
        return self._roles

    def resolve(self, role: object) -> RoleRoute:
        """Resolve exactly one role; routing failures are local and typed."""
        return resolve_role(self._roles, role)

    def list_roles(self) -> list[dict[str, Any]]:
        """Sanitized read-only view of every supported role."""
        return list_roles(self._roles)

    def summary(self) -> dict[str, Any]:
        """Compact routing summary (used by ``devrelay_status``)."""
        return roles_summary(self._roles)

    def send_role_prompt(
        self, bridge: Any, *, role: object, session_id: str, prompt: str
    ) -> RolePromptOutcome:
        """Send one model turn as *role*, using only the configured route.

        Order matters and is part of the contract: the role is validated and
        resolved **before** anything below it runs, so an unknown, unconfigured
        or malformed route can never reach the network.  Session ownership,
        exactly-one-submission semantics, reply correlation and ledger evidence
        are the accepted v0.3-A ones (this method adds no HTTP path at all).
        """
        route = self.resolve(role)
        result = bridge.send_prompt(
            session_id, prompt, agent=route.agent, model=route.model
        )
        return RolePromptOutcome(route=route, result=result)
