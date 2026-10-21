"""v0.3-C role resolver + role-aware service (library level, offline).

These tests pin the routing contract itself: exact resolution, the local error
taxonomy, the absence of any caller model/agent override, and the dependency
direction (roles never import MCP; the accepted bridge never imports roles).
"""

from __future__ import annotations

import dataclasses
import inspect
from pathlib import Path

import pytest

from devrelay.errors import (
    RoleInvalidRouteError,
    RoleRoutingError,
    RoleUnconfiguredError,
    RoleUnknownError,
)
from devrelay.roles.models import (
    ROLE_ROUTE_SOURCE,
    SUPPORTED_ROLES,
    RoleRoute,
    agent_value,
    model_identity,
    normalize_role,
)
from devrelay.roles.resolver import describe_role, list_roles, resolve_role, roles_summary
from devrelay.roles.service import RolePromptOutcome, RoleRouter

from v03c_helpers import AGENT_ROLES, DISTINCT_ROLES, roles_config

REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# vocabulary and resolution
# ---------------------------------------------------------------------------
def test_supported_roles_are_exactly_implementer_and_reviewer():
    assert SUPPORTED_ROLES == ("implementer", "reviewer")


def test_resolution_returns_the_exact_configured_routes():
    router = RoleRouter(roles_config(DISTINCT_ROLES))
    implementer = router.resolve("implementer")
    reviewer = router.resolve("reviewer")
    assert implementer == RoleRoute(
        role="implementer", model="provider-a/model-a", agent="", source=ROLE_ROUTE_SOURCE
    )
    assert reviewer == RoleRoute(
        role="reviewer", model="provider-b/model-b", agent="", source=ROLE_ROUTE_SOURCE
    )
    assert implementer.model != reviewer.model, "the fixtures must stay distinct"


def test_resolution_normalizes_the_configured_model_spelling():
    router = RoleRouter(roles_config({"reviewer": {"model": " provider-b / model-b "}}))
    assert router.resolve("reviewer").model == "provider-b/model-b"


def test_multi_slash_model_keeps_the_provider_boundary():
    router = RoleRouter(roles_config({"reviewer": {"model": "openrouter/anthropic/claude"}}))
    evidence = router.resolve("reviewer").route_evidence()
    assert evidence["resolved_model_identity"] == {
        "providerID": "openrouter",
        "modelID": "anthropic/claude",
    }


@pytest.mark.parametrize(
    "value", ["implementer", "reviewer", " implementer ", "reviewer\t"]
)
def test_exact_role_names_are_accepted(value):
    assert normalize_role(value) == value.strip()


@pytest.mark.parametrize(
    "value",
    [
        "Implementer",
        "IMPLEMENTER",
        "impl",
        "implement",
        "planner",
        "arbiter",
        "reviewer2",
        "",
        "   ",
        None,
        7,
        ["reviewer"],
        {"role": "reviewer"},
    ],
)
def test_unknown_roles_fail_locally(value):
    with pytest.raises(RoleUnknownError) as excinfo:
        normalize_role(value)
    assert excinfo.value.code == "role_unknown"
    assert str(excinfo.value).startswith("role_unknown: ")


def test_no_fuzzy_or_inferred_role_selection():
    """Role text is never matched by similarity, case, prefix or prompt content."""
    router = RoleRouter(roles_config(DISTINCT_ROLES))
    for value in ("Reviewer", "REVIEWER", "review", "review er", "reviewers", "r"):
        with pytest.raises(RoleUnknownError):
            router.resolve(value)
    # Nothing in the resolver *code* reads a prompt, a session, a title or a
    # model-availability/ranking signal (docstrings are excluded: they describe
    # exactly these non-behaviours).
    import ast

    tree = ast.parse(
        (REPO_ROOT / "src" / "devrelay" / "roles" / "resolver.py").read_text(
            encoding="utf-8"
        )
    )
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if (
            isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef))
            and body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            body[0].value.value = ""
    code = ast.unparse(tree).lower()
    for forbidden in ("prompt", "session", "title", "available", "rank", "score"):
        assert forbidden not in code, forbidden


def test_unconfigured_role_is_typed_and_local():
    router = RoleRouter(roles_config({"implementer": {"model": "provider-a/model-a"}}))
    with pytest.raises(RoleUnconfiguredError) as excinfo:
        router.resolve("reviewer")
    assert excinfo.value.code == "role_unconfigured"
    assert "roles.reviewer.model" in str(excinfo.value)


def test_blank_model_is_unconfigured():
    router = RoleRouter(roles_config({"reviewer": {"model": "   "}}))
    with pytest.raises(RoleUnconfiguredError):
        router.resolve("reviewer")


@pytest.mark.parametrize("model", ["not-a-route", "provider-only/", "/model-only"])
def test_malformed_configured_model_is_an_invalid_route(model):
    router = RoleRouter(roles_config({"reviewer": {"model": model}}))
    with pytest.raises(RoleInvalidRouteError) as excinfo:
        router.resolve("reviewer")
    assert excinfo.value.code == "role_invalid_route"
    assert not str(excinfo.value).startswith("opencode_config_invalid")


@pytest.mark.parametrize("model", ["provider//", "a b/c", "p/m?x=1"])
def test_role_config_inherits_the_accepted_grammar_verbatim(model):
    """v0.3-C adds no second grammar: it accepts exactly what the bridge accepts.

    The accepted v0.3-A rule is "a non-empty provider and a non-empty modelID,
    split at the first slash"; anything stricter here would let the role path and
    the raw path disagree about the same string.
    """
    route = RoleRouter(roles_config({"reviewer": {"model": model}})).resolve("reviewer")
    assert route.route_evidence()["resolved_model_identity"] == model_identity(
        model, role="reviewer"
    )


def test_no_configuration_at_all_is_unconfigured_not_unknown():
    with pytest.raises(RoleUnconfiguredError):
        RoleRouter(None).resolve("implementer")
    with pytest.raises(RoleUnknownError):
        RoleRouter(None).resolve("planner")


def test_routing_errors_share_one_base_class():
    for error in (RoleUnknownError, RoleUnconfiguredError, RoleInvalidRouteError):
        assert issubclass(error, RoleRoutingError)
        assert issubclass(error, Exception)


# ---------------------------------------------------------------------------
# route value object and read-only views
# ---------------------------------------------------------------------------
def test_role_route_is_frozen_and_carries_no_secret_or_policy():
    route = RoleRouter(roles_config(AGENT_ROLES)).resolve("reviewer")
    with pytest.raises(dataclasses.FrozenInstanceError):
        route.model = "other/model"  # type: ignore[misc]
    assert {field.name for field in dataclasses.fields(RoleRoute)} == {
        "role",
        "model",
        "agent",
        "source",
    }


def test_public_and_evidence_views_are_sanitized():
    route = RoleRouter(roles_config(AGENT_ROLES)).resolve("implementer")
    assert route.public() == {
        "role": "implementer",
        "model": "provider-a/model-a",
        "agent": "build",
        "route_source": ROLE_ROUTE_SOURCE,
    }
    evidence = route.route_evidence()
    assert evidence == {
        "role": "implementer",
        "resolved_model": "provider-a/model-a",
        "resolved_model_identity": {"providerID": "provider-a", "modelID": "model-a"},
        "resolved_agent": "build",
        "route_source": ROLE_ROUTE_SOURCE,
    }
    assert "prompt" not in evidence and "token" not in evidence


def test_omitted_agent_is_none_never_empty_string():
    route = RoleRouter(roles_config(DISTINCT_ROLES)).resolve("reviewer")
    assert route.agent == ""
    assert route.public()["agent"] is None
    assert route.route_evidence()["resolved_agent"] is None


@pytest.mark.parametrize("value", [None, "", "build", "review", "x" * 64])
def test_agent_values_follow_the_accepted_rule(value):
    assert agent_value(value, role="reviewer") == (value or "")


@pytest.mark.parametrize("value", ["   ", "x" * 65])
def test_malformed_agent_values_fail_locally(value):
    with pytest.raises(RoleInvalidRouteError):
        agent_value(value, role="reviewer")


def test_list_roles_reports_every_supported_role_with_state():
    entries = list_roles(
        roles_config({"implementer": {"model": "provider-a/model-a"}, "reviewer": {"model": "nope"}})
    )
    assert [entry["role"] for entry in entries] == list(SUPPORTED_ROLES)
    assert entries[0]["state"] == "configured" and entries[0]["configured"] is True
    assert entries[1]["state"] == "invalid" and entries[1]["error"] == "role_invalid_route"


def test_roles_summary_is_compact_and_truthful():
    summary = roles_summary(None)
    assert summary["supported_roles"] == ["implementer", "reviewer"]
    assert summary["configured"] is False
    assert summary["route_source"] == ROLE_ROUTE_SOURCE
    assert all(entry["model"] is None for entry in summary["roles"])
    assert roles_summary(roles_config(DISTINCT_ROLES))["configured"] is True


def test_describe_role_of_an_unsupported_role_still_fails():
    with pytest.raises(RoleUnknownError):
        describe_role(None, "planner")


# ---------------------------------------------------------------------------
# the P1 invariant: no caller model/agent override, ever
# ---------------------------------------------------------------------------
def test_role_aware_send_accepts_no_model_or_agent_argument():
    parameters = inspect.signature(RoleRouter.send_role_prompt).parameters
    assert "model" not in parameters
    assert "agent" not in parameters
    assert list(parameters) == ["self", "bridge", "role", "session_id", "prompt"]


def test_model_identity_reuses_the_accepted_bridge_grammar():
    assert model_identity("provider-a/model-a", role="implementer") == {
        "providerID": "provider-a",
        "modelID": "model-a",
    }
    with pytest.raises(RoleInvalidRouteError):
        model_identity("provider-a", role="implementer")


# ---------------------------------------------------------------------------
# delegation: exactly one accepted bridge call, with only the resolved route
# ---------------------------------------------------------------------------
class _RecordingBridge:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def send_prompt(self, session_id: str, prompt: str, *, agent: str = "", model: str = ""):
        self.calls.append(
            {"session_id": session_id, "prompt": prompt, "agent": agent, "model": model}
        )
        return type("R", (), {"ok": True, "state": "COMPLETED"})()


def test_send_role_prompt_delegates_once_with_the_resolved_route():
    bridge = _RecordingBridge()
    router = RoleRouter(roles_config(AGENT_ROLES))
    outcome = router.send_role_prompt(
        bridge, role="reviewer", session_id="ses_1", prompt="please review"
    )
    assert isinstance(outcome, RolePromptOutcome) and outcome.ok is True
    assert outcome.route.role == "reviewer"
    assert bridge.calls == [
        {
            "session_id": "ses_1",
            "prompt": "please review",
            "agent": "review",
            "model": "provider-b/model-b",
        }
    ]


def test_send_role_prompt_resolves_before_touching_the_bridge():
    bridge = _RecordingBridge()
    router = RoleRouter(roles_config(DISTINCT_ROLES))
    with pytest.raises(RoleUnknownError):
        router.send_role_prompt(bridge, role="planner", session_id="ses_1", prompt="hi")
    with pytest.raises(RoleUnconfiguredError):
        RoleRouter(None).send_role_prompt(
            bridge, role="implementer", session_id="ses_1", prompt="hi"
        )
    assert bridge.calls == [], "no bridge call may happen without an exact route"


def test_send_role_prompt_does_not_retry_or_fall_back():
    bridge = _RecordingBridge()
    router = RoleRouter(roles_config(AGENT_ROLES))
    router.send_role_prompt(bridge, role="implementer", session_id="s", prompt="p")
    router.send_role_prompt(bridge, role="implementer", session_id="s", prompt="p")
    assert [call["model"] for call in bridge.calls] == [
        "provider-a/model-a",
        "provider-a/model-a",
    ]
    assert len(bridge.calls) == 2, "one call per invocation: no retry, no fallback"


# ---------------------------------------------------------------------------
# dependency direction
# ---------------------------------------------------------------------------
def _imported_modules(path: Path) -> set[str]:
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
            modules.update(f"{node.module}.{alias.name}" for alias in node.names)
    return modules


def test_roles_package_never_imports_mcp():
    for path in sorted((REPO_ROOT / "src" / "devrelay" / "roles").glob("*.py")):
        imported = _imported_modules(path)
        assert not [name for name in imported if name.startswith("devrelay.mcp")], path
        assert not [name for name in imported if name.startswith("devrelay.cli")], path


def test_accepted_opencode_package_never_imports_roles():
    for path in sorted((REPO_ROOT / "src" / "devrelay" / "opencode").glob("*.py")):
        imported = _imported_modules(path)
        assert not [name for name in imported if name.startswith("devrelay.roles")], path


def test_roles_package_contains_no_http_or_shell_code():
    for path in sorted((REPO_ROOT / "src" / "devrelay" / "roles").glob("*.py")):
        source = path.read_text(encoding="utf-8")
        for forbidden in ("httpx", "subprocess", "os.system", "requests", "socket"):
            assert forbidden not in source, (path, forbidden)
