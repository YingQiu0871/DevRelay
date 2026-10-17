"""Production-generated honest-state corpus for the v0.3-D reachability proof.

Every document here is produced by the **real** service: the real MCP tool
surface, the real orchestration service, the real v0.3-C role router and the
accepted v0.3-A bridge wired to the deterministic OpenCode stub.  Nothing in this
module hand-writes a "valid" run document: crash boundaries come from a real
``SystemExit`` at submission, failures come from the stub's transport knobs, and
route invalidation comes from rewriting the workspace configuration.

The corpus is the anti-over-strictness proof: the validator must accept every
member, must keep accepting it across a save/destroy/recreate/load/re-save cycle,
and must reject every semantically corrupted variant of it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from v03d_helpers import (
    Harness,
    build,
    decide,
    dying_stub,
    failing_post_stub,
    fixed_run_ids,
    freeze_v03d,
    phase,
    raw_payload,
    restart_surface,
    run_id_of,
    start,
    state_path,
    two_session_stub,
    write_roles,
)

#: The 19 corpus members required for the reachability proof, in order.
CORPUS_STATES: tuple[str, ...] = (
    "ready_implementer_c1",
    "ready_reviewer_c1",
    "reviewer_in_flight_c1",
    "awaiting_decision_c1",
    "ready_implementer_c2",
    "ready_reviewer_c2",
    "reviewer_in_flight_c2",
    "awaiting_decision_c2",
    "ready_implementer_c3",
    "completed",
    "stopped",
    "limit_reached",
    "blocked_implementer_failure",
    "blocked_reviewer_failure",
    "blocked_route_change",
    "blocked_interrupted_implementer",
    "blocked_interrupted_reviewer",
    "implementer_in_flight",
    "reviewer_in_flight_after_restart",
)


def _harness(root: Path, *, stub: Any = None, roles: dict[str, Any] | None = None) -> Harness:
    return build(
        root,
        stub=stub,
        roles=roles if roles is not None else _default_roles(),
        run_id_factory=fixed_run_ids(_run_id()),
    )


def _default_roles() -> dict[str, Any]:
    from v03d_helpers import DISTINCT_ROLES

    return DISTINCT_ROLES


def _run_id() -> str:
    from v03d_helpers import RUN_ID

    return RUN_ID


def _started(root: Path, *, max_cycles: int = 2, **kwargs: Any) -> tuple[Harness, str]:
    harness = _harness(root, **kwargs)
    run_id = run_id_of(harness.server, max_cycles=max_cycles)
    freeze_v03d(harness.ws, run_id)
    return harness, run_id


def _implementer(harness: Harness, run_id: str, prompt: str = "implementer turn") -> dict[str, Any]:
    envelope = phase(harness.server, "devrelay_run_implementer", run_id, prompt)
    assert envelope["ok"] is True, envelope
    return envelope


def _reviewer(harness: Harness, run_id: str, prompt: str = "reviewer turn") -> dict[str, Any]:
    envelope = phase(harness.server, "devrelay_run_reviewer", run_id, prompt)
    assert envelope["ok"] is True, envelope
    return envelope


def _request_changes(harness: Harness, run_id: str) -> dict[str, Any]:
    envelope = decide(harness.server, run_id, "request_changes")
    assert envelope["ok"] is True, envelope
    return envelope


def _crash_at(root: Path, *, on_post: int, max_cycles: int = 2) -> tuple[Harness, str]:
    """Start a run, drive it, and die at the *on_post*-th submission."""
    stub = dying_stub(root / "ws", on_post=on_post)
    harness = build(root, stub=stub, run_id_factory=fixed_run_ids(_run_id()))
    run_id = run_id_of(harness.server, max_cycles=max_cycles)
    freeze_v03d(harness.ws, run_id)
    prompts = ["implementer turn", "reviewer turn", "implementer turn 2", "reviewer turn 2"]
    for index in range(on_post - 1):
        tool = (
            "devrelay_run_implementer" if index % 2 == 0 else "devrelay_run_reviewer"
        )
        envelope = phase(harness.server, tool, run_id, prompts[index])
        assert envelope["ok"] is True, envelope
        if index % 2 == 1:
            _request_changes(harness, run_id)
    try:
        phase(
            harness.server,
            "devrelay_run_implementer" if (on_post - 1) % 2 == 0 else "devrelay_run_reviewer",
            run_id,
            prompts[on_post - 1],
        )
    except SystemExit:
        pass
    else:  # pragma: no cover - the crash double must actually die
        raise AssertionError("the crash double did not die at submission")
    return harness, run_id


def _blocked_by_failure(root: Path, *, on_post: int, max_cycles: int = 2) -> tuple[Harness, str]:
    stub = failing_post_stub(root / "ws", on_post=on_post)
    harness = build(root, stub=stub, run_id_factory=fixed_run_ids(_run_id()))
    run_id = run_id_of(harness.server, max_cycles=max_cycles)
    freeze_v03d(harness.ws, run_id)
    if on_post == 1:
        envelope = phase(harness.server, "devrelay_run_implementer", run_id, "implementer turn")
    else:
        _implementer(harness, run_id)
        envelope = phase(harness.server, "devrelay_run_reviewer", run_id, "reviewer turn")
    assert envelope["ok"] is False and envelope["data"]["state"] == "BLOCKED", envelope
    return harness, run_id


def _blocked_by_route_change(root: Path) -> tuple[Harness, str]:
    harness, run_id = _started(root, max_cycles=2)
    _implementer(harness, run_id)
    # the workspace loses the reviewer role entirely
    write_roles(harness.ws, {"implementer": {"model": "provider-a/model-a"}})
    restarted = restart_surface(harness)
    envelope = phase(restarted.server, "devrelay_run_reviewer", run_id, "reviewer turn")
    assert envelope["ok"] is False, envelope
    assert envelope["data"]["state"] == "BLOCKED", envelope
    assert envelope["data"]["blocked_reason"] == "route_changed", envelope
    return restarted, run_id


def _materialized(harness: Harness, run_id: str, tool: str) -> tuple[Harness, str]:
    restarted = restart_surface(harness)
    envelope = phase(restarted.server, tool, run_id, "post-crash attempt")
    assert envelope["ok"] is False, envelope
    assert envelope["data"]["state"] == "BLOCKED", envelope
    assert envelope["data"]["blocked_reason"] == "turn_interrupted", envelope
    return restarted, run_id


def build_state(name: str, root: Path) -> tuple[Harness, str]:
    """Produce corpus member *name* with the real service under *root*."""
    if name == "ready_implementer_c1":
        return _started(root, max_cycles=2)
    if name == "ready_reviewer_c1":
        harness, run_id = _started(root, max_cycles=2)
        _implementer(harness, run_id)
        return harness, run_id
    if name == "reviewer_in_flight_c1":
        return _crash_at(root, on_post=2, max_cycles=2)
    if name == "awaiting_decision_c1":
        harness, run_id = _started(root, max_cycles=2)
        _implementer(harness, run_id)
        _reviewer(harness, run_id)
        return harness, run_id
    if name == "ready_implementer_c2":
        harness, run_id = _started(root, max_cycles=2)
        _implementer(harness, run_id)
        _reviewer(harness, run_id)
        _request_changes(harness, run_id)
        return harness, run_id
    if name == "ready_reviewer_c2":
        harness, run_id = _started(root, max_cycles=2)
        _implementer(harness, run_id)
        _reviewer(harness, run_id)
        _request_changes(harness, run_id)
        _implementer(harness, run_id)
        return harness, run_id
    if name == "reviewer_in_flight_c2":
        return _crash_at(root, on_post=4, max_cycles=2)
    if name == "awaiting_decision_c2":
        harness, run_id = _started(root, max_cycles=2)
        _implementer(harness, run_id)
        _reviewer(harness, run_id)
        _request_changes(harness, run_id)
        _implementer(harness, run_id)
        _reviewer(harness, run_id)
        return harness, run_id
    if name == "ready_implementer_c3":
        harness, run_id = _started(root, max_cycles=3)
        for _ in range(2):
            _implementer(harness, run_id)
            _reviewer(harness, run_id)
            _request_changes(harness, run_id)
        return harness, run_id
    if name == "completed":
        harness, run_id = _started(root, max_cycles=2)
        _implementer(harness, run_id)
        _reviewer(harness, run_id)
        assert decide(harness.server, run_id, "complete")["ok"] is True
        return harness, run_id
    if name == "stopped":
        harness, run_id = _started(root, max_cycles=2)
        _implementer(harness, run_id)
        _reviewer(harness, run_id)
        assert decide(harness.server, run_id, "stop")["ok"] is True
        return harness, run_id
    if name == "limit_reached":
        harness, run_id = _started(root, max_cycles=1)
        _implementer(harness, run_id)
        _reviewer(harness, run_id)
        envelope = _request_changes(harness, run_id)
        assert envelope["data"]["state"] == "LIMIT_REACHED", envelope
        return harness, run_id
    if name == "blocked_implementer_failure":
        return _blocked_by_failure(root, on_post=1)
    if name == "blocked_reviewer_failure":
        return _blocked_by_failure(root, on_post=2)
    if name == "blocked_route_change":
        return _blocked_by_route_change(root)
    if name == "blocked_interrupted_implementer":
        harness, run_id = _crash_at(root, on_post=1)
        return _materialized(harness, run_id, "devrelay_run_implementer")
    if name == "blocked_interrupted_reviewer":
        harness, run_id = _crash_at(root, on_post=2)
        return _materialized(harness, run_id, "devrelay_run_reviewer")
    if name == "implementer_in_flight":
        return _crash_at(root, on_post=1)
    if name == "reviewer_in_flight_after_restart":
        harness, run_id = _crash_at(root, on_post=2)
        restarted = restart_surface(harness)
        from v03d_helpers import get_run

        read = get_run(restarted.server, run_id)
        assert read["data"]["in_flight"] is True, read
        return restarted, run_id
    raise AssertionError(f"unknown corpus state {name!r}")


def corpus(root: Path, *, names: tuple[str, ...] = CORPUS_STATES) -> dict[str, dict[str, Any]]:
    """Build every requested member, each in its own sub-directory of *root*."""
    members: dict[str, dict[str, Any]] = {}
    for name in names:
        directory = root / name
        directory.mkdir(parents=True, exist_ok=True)
        harness, run_id = build_state(name, directory)
        members[name] = {
            "harness": harness,
            "run_id": run_id,
            "ws": harness.ws,
            "path": state_path(harness.ws, run_id),
            "payload": raw_payload(harness.ws, run_id),
        }
    return members


#: Registry for callers that want to build a single member.
BUILDERS: dict[str, Callable[[str, Path], tuple[Harness, str]]] = {
    name: build_state for name in CORPUS_STATES
}

__all__ = ["BUILDERS", "CORPUS_STATES", "build_state", "corpus"]
