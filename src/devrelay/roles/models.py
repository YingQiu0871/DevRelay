"""The normalized v0.3-C role vocabulary, route value and configuration schema.

A *role* is semantic (``implementer`` / ``reviewer``); the exact provider/model
route behind it belongs to workspace configuration, never to code.  Nothing in
this module mentions a vendor: DevRelay ships no DeepSeek/GLM/OpenAI default and
hard-codes no provider or model identifier.

The role path contains identifiers only.  A route never carries a prompt, a
credential, an endpoint, a retry policy, a fallback model or an acceptance rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from devrelay.errors import DevRelayError, RoleInvalidRouteError, RoleUnknownError

#: The exact v0.3-C role vocabulary.  Deliberately narrow: no generic
#: arbitrary-role plugin system yet, so no premature role taxonomy exists.
SUPPORTED_ROLES: tuple[str, ...] = ("implementer", "reviewer")

#: The only route provenance v0.3-C knows (there is no default and no fallback).
ROLE_ROUTE_SOURCE = "workspace_config"

#: Accepted agent bound (the same rule the v0.3-A/v0.3-B path applies).
ROLE_AGENT_MAX_CHARS = 64


def normalize_role(value: object) -> str:
    """Return the exact supported role name, or raise ``role_unknown``.

    Matching is exact (after trimming surrounding whitespace only): no case
    folding, no prefix/alias match, no similarity match, and never an inference
    from prompt text, session title or model availability.
    """
    if not isinstance(value, str):
        raise RoleUnknownError(
            "a role is required and must be one of "
            f"{', '.join(SUPPORTED_ROLES)} (got {type(value).__name__}); "
            "v0.3-C never infers a role"
        )
    candidate = value.strip()
    if not candidate:
        raise RoleUnknownError(
            f"a role is required and must be one of {', '.join(SUPPORTED_ROLES)}: "
            "an omitted or blank role is never inferred"
        )
    if candidate not in SUPPORTED_ROLES:
        raise RoleUnknownError(
            f"unknown role {candidate!r}: v0.3-C supports exactly "
            f"{', '.join(SUPPORTED_ROLES)}"
        )
    return candidate


def model_identity(model: object, *, role: str) -> dict[str, str]:
    """The exact OpenCode wire model object for a configured role model.

    The ``<providerID>/<modelID>`` grammar is the **accepted v0.3-A grammar**:
    this function delegates to the bridge's own mapper, so the role path can
    never parse a model differently from the bridge (no second grammar).
    """
    if not isinstance(model, str) or not model.strip():
        raise RoleInvalidRouteError(
            f"role {role!r} must configure an explicit '<providerID>/<modelID>' "
            "model: v0.3-C has no default model and never falls back"
        )
    from devrelay.opencode.bridge import OpenCodeBridge  # local: no import cycle

    try:
        return OpenCodeBridge._model_identity(model)  # noqa: SLF001 - single grammar
    except DevRelayError as exc:
        detail = str(exc)
        prefix = f"{getattr(exc, 'code', '')}: "
        if prefix.strip(": ") and detail.startswith(prefix):
            detail = detail[len(prefix):]
        raise RoleInvalidRouteError(f"role {role!r}: {detail}") from exc


def agent_value(agent: object, *, role: str) -> str:
    """The configured optional agent, or ``""`` when the route omits it.

    ``""`` means *omitted*: the accepted v0.3-A omission behavior applies and the
    bridge leaves the ``agent`` member out of the request entirely (never an
    empty-string agent merely because the configuration field exists).
    """
    if agent is None or agent == "":
        return ""
    if not isinstance(agent, str):
        raise RoleInvalidRouteError(f"role {role!r}: agent must be a string")
    if not agent.strip():
        raise RoleInvalidRouteError(
            f"role {role!r}: agent must not be blank; omit the field instead"
        )
    if len(agent) > ROLE_AGENT_MAX_CHARS:
        raise RoleInvalidRouteError(
            f"role {role!r}: agent exceeds {ROLE_AGENT_MAX_CHARS} characters"
        )
    return agent


class RoleRouteConfig(BaseModel):
    """One configured role route (workspace wiring; identifiers only)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model: str = ""
    agent: str = ""

    @field_validator("model", "agent", mode="before")
    @classmethod
    def _must_be_text(cls, value: Any, info: Any) -> Any:
        if value is None:
            return ""
        if not isinstance(value, str):
            raise ValueError(f"{info.field_name} must be a string")
        return value


class RolesConfig(BaseModel):
    """The ``roles:`` workspace wiring section (v0.3-C).

    Only the two v0.3-C roles exist as fields, so a typo such as ``implmenter:``
    fails configuration instead of silently disabling routing.  An absent or
    empty section is valid: existing v0.3-B workspaces keep working unchanged
    and only role-aware tools report the missing route (``role_unconfigured``).

    ``model``/``agent`` *grammar* is validated when a role is resolved, not when
    the file is loaded: a role typo must never make the accepted raw v0.3-B tools
    (or ``devrelay mcp serve``) unusable.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    implementer: RoleRouteConfig = Field(default_factory=RoleRouteConfig)
    reviewer: RoleRouteConfig = Field(default_factory=RoleRouteConfig)


@dataclass(frozen=True)
class RoleRoute:
    """A resolved, immutable route: which model/agent a semantic role selects."""

    role: str
    model: str
    agent: str = ""
    source: str = ROLE_ROUTE_SOURCE

    def public(self) -> dict[str, Any]:
        """The read-only configuration view (``devrelay_get_role``/``list_roles``)."""
        return {
            "role": self.role,
            "model": self.model,
            "agent": self.agent or None,
            "route_source": self.source,
        }

    def route_evidence(self) -> dict[str, Any]:
        """Audit evidence for a role-aware send (no secret is possible here)."""
        return {
            "role": self.role,
            "resolved_model": self.model,
            "resolved_model_identity": model_identity(self.model, role=self.role),
            "resolved_agent": self.agent or None,
            "route_source": self.source,
        }


__all__ = [
    "ROLE_AGENT_MAX_CHARS",
    "ROLE_ROUTE_SOURCE",
    "SUPPORTED_ROLES",
    "RoleRoute",
    "RoleRouteConfig",
    "RolesConfig",
    "agent_value",
    "model_identity",
    "normalize_role",
]
