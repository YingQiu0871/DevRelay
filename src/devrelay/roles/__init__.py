"""v0.3-C semantic role routing: semantic role -> exact configured route.

Dependency direction (enforced by tests):

    MCP adapter  ->  role router  ->  accepted OpenCode bridge

The role router never imports :mod:`devrelay.mcp`, and the accepted v0.3-A
OpenCode bridge never imports this package.  v0.3-C routes; it does not
orchestrate, sequence, approve or reject anything.
"""

from __future__ import annotations

from devrelay.roles.models import (
    ROLE_AGENT_MAX_CHARS,
    ROLE_ROUTE_SOURCE,
    SUPPORTED_ROLES,
    RoleRoute,
    RoleRouteConfig,
    RolesConfig,
    agent_value,
    model_identity,
    normalize_role,
)
from devrelay.roles.resolver import describe_role, list_roles, resolve_role, roles_summary
from devrelay.roles.service import RolePromptOutcome, RoleRouter

__all__ = [
    "ROLE_AGENT_MAX_CHARS",
    "ROLE_ROUTE_SOURCE",
    "SUPPORTED_ROLES",
    "RolePromptOutcome",
    "RoleRoute",
    "RoleRouteConfig",
    "RoleRouter",
    "RolesConfig",
    "agent_value",
    "describe_role",
    "list_roles",
    "model_identity",
    "normalize_role",
    "resolve_role",
    "roles_summary",
]
