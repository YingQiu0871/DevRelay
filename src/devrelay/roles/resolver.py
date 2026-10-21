"""Deterministic role resolution (v0.3-C).

``resolve_role`` turns one semantic role into exactly the route the workspace
configures, or fails locally with a typed routing error.  There is no default
role, no fallback route, no candidate list, no ranking and no availability
probe: resolution is a pure function of configuration.
"""

from __future__ import annotations

from typing import Any

from devrelay.errors import RoleUnconfiguredError
from devrelay.roles.models import (
    ROLE_ROUTE_SOURCE,
    SUPPORTED_ROLES,
    RoleRoute,
    RolesConfig,
    agent_value,
    model_identity,
    normalize_role,
)


def _route_config(roles: RolesConfig | None, role: str) -> Any:
    if roles is None:
        return None
    return getattr(roles, role, None)


def resolve_role(roles: RolesConfig | None, role: object) -> RoleRoute:
    """Resolve one semantic role to its exact configured route.

    Raises :class:`~devrelay.errors.RoleUnknownError` for an unsupported/omitted
    role, :class:`~devrelay.errors.RoleUnconfiguredError` when the role has no
    configured model, and :class:`~devrelay.errors.RoleInvalidRouteError` when the
    configured model/agent cannot be mapped exactly.  Every failure happens
    locally, before any request that could submit a model turn.
    """
    name = normalize_role(role)
    config = _route_config(roles, name)
    model = getattr(config, "model", "") if config is not None else ""
    if not isinstance(model, str) or not model.strip():
        raise RoleUnconfiguredError(
            f"role {name!r} has no configured route in this workspace "
            f"(set roles.{name}.model to '<providerID>/<modelID>'); v0.3-C has no "
            "default role and never guesses one"
        )
    identity = model_identity(model, role=name)
    agent = agent_value(getattr(config, "agent", ""), role=name)
    # Keep the configured spelling, but only after proving it maps exactly.
    return RoleRoute(
        role=name,
        model=f"{identity['providerID']}/{identity['modelID']}",
        agent=agent,
        source=ROLE_ROUTE_SOURCE,
    )


def describe_role(roles: RolesConfig | None, role: object) -> dict[str, Any]:
    """Sanitized state of one role (never raises for a *supported* role)."""
    name = normalize_role(role)
    entry: dict[str, Any] = {
        "role": name,
        "configured": False,
        "state": "unconfigured",
        "model": None,
        "agent": None,
        "route_source": ROLE_ROUTE_SOURCE,
        "error": None,
    }
    try:
        route = resolve_role(roles, name)
    except Exception as exc:  # noqa: BLE001 - routing state, not control flow
        code = getattr(exc, "code", "")
        entry["error"] = code or type(exc).__name__
        if code == "role_invalid_route":
            model = getattr(_route_config(roles, name), "model", "")
            entry["state"] = "invalid"
            entry["model"] = model if isinstance(model, str) and model else None
        return entry
    entry.update(
        {
            "configured": True,
            "state": "configured",
            "model": route.model,
            "agent": route.agent or None,
        }
    )
    return entry


def list_roles(roles: RolesConfig | None) -> list[dict[str, Any]]:
    """The sanitized read-only view of every supported role."""
    return [describe_role(roles, role) for role in SUPPORTED_ROLES]


def roles_summary(roles: RolesConfig | None) -> dict[str, Any]:
    """The compact routing summary embedded in ``devrelay_status``."""
    entries = list_roles(roles)
    return {
        "supported_roles": list(SUPPORTED_ROLES),
        "route_source": ROLE_ROUTE_SOURCE,
        "configured": any(entry["configured"] for entry in entries),
        "roles": entries,
    }


__all__ = ["describe_role", "list_roles", "resolve_role", "roles_summary"]
