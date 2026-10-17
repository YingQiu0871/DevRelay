"""v0.3-E invariants: a persisted recovery shape may only be read one way.

These tests mutate a *valid* v2 document at the JSON boundary - exactly what a
torn write, a downgrade or a hand edit would do - and require the strict reader
to refuse instead of guessing.
"""

from __future__ import annotations

from typing import Any

import pytest

from devrelay.orchestration import recovery
from devrelay.orchestration.models import (
    LEGACY_SCHEMA_VERSION,
    ORCHESTRATION_SCHEMA_VERSION,
    OrchestrationRun,
    RecoveryEvidence,
    RunState,
    TransitionRecord,
)
from v03d_helpers import honest_run, with_in_flight

REASON = "turn_interrupted"


def _evidence_and_attempt() -> tuple[Any, Any]:
    run = with_in_flight(honest_run(RunState.READY_IMPLEMENTER, max_cycles=2), "implementer")
    attempt = run.in_flight_turn
    assert attempt is not None
    evidence, frozen = recovery.build_record(
        run,
        attempt,
        entry_state=RunState.READY_IMPLEMENTER,
        reason=REASON,
        ledger_scan=None,
        remote=None,
    )
    return evidence, frozen


def live_intent_payload() -> dict[str, Any]:
    run = with_in_flight(honest_run(RunState.READY_IMPLEMENTER, max_cycles=2), "implementer")
    return run.model_dump(mode="json")


def recovery_required_payload() -> dict[str, Any]:
    evidence, frozen = _evidence_and_attempt()
    run = with_in_flight(honest_run(RunState.READY_IMPLEMENTER, max_cycles=2), "implementer")
    payload = run.model_dump(mode="json")
    payload.update(
        {
            "state": "RECOVERY_REQUIRED",
            "in_flight_turn": None,
            "recovery_reason": REASON,
            "recovery": {
                "attempt": frozen.model_dump(mode="json"),
                "recovery_reason": REASON,
                "resolution": "",
                "resolved_at": "",
                "evidence": evidence.model_dump(mode="json"),
            },
            "last_transition": TransitionRecord(
                action="recover",
                source="external_planner",
                previous_state="READY_IMPLEMENTER",
                next_state="RECOVERY_REQUIRED",
                cycle=1,
                role="implementer",
            ).model_dump(mode="json"),
        }
    )
    return payload


def accepted(payload: dict[str, Any]) -> None:
    OrchestrationRun.model_validate(payload)


def test_the_two_valid_v2_shapes_are_accepted() -> None:
    accepted(live_intent_payload())
    accepted(recovery_required_payload())


def test_an_unknown_schema_version_is_refused() -> None:
    payload = live_intent_payload()
    payload["schema_version"] = ORCHESTRATION_SCHEMA_VERSION + 1
    with pytest.raises(Exception, match="is not one of the supported versions"):
        OrchestrationRun.model_validate(payload)


def test_a_v1_document_may_never_carry_the_v2_recovery_surface() -> None:
    payload = recovery_required_payload()
    payload["schema_version"] = LEGACY_SCHEMA_VERSION
    with pytest.raises(Exception, match="frozen v0.3-D"):
        OrchestrationRun.model_validate(payload)
    payload = live_intent_payload()
    payload["schema_version"] = LEGACY_SCHEMA_VERSION
    payload["recovery_reason"] = REASON
    with pytest.raises(Exception, match="frozen v0.3-D"):
        OrchestrationRun.model_validate(payload)


def test_a_v1_document_can_never_enter_recovery_required() -> None:
    payload = recovery_required_payload()
    payload["schema_version"] = LEGACY_SCHEMA_VERSION
    payload["recovery"] = None
    payload["recovery_reason"] = ""
    with pytest.raises(Exception, match="RECOVERY_REQUIRED"):
        OrchestrationRun.model_validate(payload)


def test_a_v1_document_has_no_recover_edge() -> None:
    payload = live_intent_payload()
    payload["schema_version"] = LEGACY_SCHEMA_VERSION
    payload["in_flight_turn"] = None
    # a frozen v0.3-D run never reserved a recovery attempt
    payload["model_turns_used"] = 0
    payload["turn_attempts"] = 0
    payload["last_transition"] = TransitionRecord(
        action="recover",
        source="external_planner",
        previous_state="READY_IMPLEMENTER",
        next_state="READY_IMPLEMENTER",
        cycle=1,
        role="implementer",
    ).model_dump(mode="json")
    with pytest.raises(Exception, match="does not exist for schema_version 1"):
        OrchestrationRun.model_validate(payload)


def test_recovery_required_requires_exactly_one_attempt() -> None:
    payload = recovery_required_payload()
    payload["recovery"] = None
    payload["model_turns_used"] = 0
    payload["turn_attempts"] = 0
    with pytest.raises(Exception, match="requires exactly one materialized recovery"):
        OrchestrationRun.model_validate(payload)


def test_recovery_required_keeps_no_live_intent() -> None:
    payload = recovery_required_payload()
    payload["in_flight_turn"] = _evidence_and_attempt()[1].model_dump(mode="json")
    # two reserved slots, both accounted for: the live intent and the frozen
    # attempt; accounting is satisfied so the shape rule is what has to speak
    payload["model_turns_used"] = 2
    payload["turn_attempts"] = 2
    with pytest.raises(Exception, match="cannot carry a live in-flight intent"):
        OrchestrationRun.model_validate(payload)


def test_recovery_required_keeps_no_blocked_reason() -> None:
    payload = recovery_required_payload()
    payload["blocked_reason"] = REASON
    with pytest.raises(Exception, match="must not carry blocked_reason"):
        OrchestrationRun.model_validate(payload)


def test_only_recovery_required_may_hold_an_unresolved_attempt() -> None:
    payload = recovery_required_payload()
    payload["state"] = "BLOCKED"
    payload["blocked_reason"] = REASON
    # the frozen attempt is also booked in history, so the slot accounting is
    # satisfied and only the *unresolved record* is left to complain
    payload["implementer_turns"] = [payload["recovery"]["attempt"]]
    payload["last_transition"] = TransitionRecord(
        action="recover",
        source="external_planner",
        previous_state="RECOVERY_REQUIRED",
        next_state="BLOCKED",
        cycle=1,
        role="implementer",
    ).model_dump(mode="json")
    with pytest.raises(Exception, match="unresolved recovery record"):
        OrchestrationRun.model_validate(payload)


def test_a_failed_closed_recovery_must_state_its_reason() -> None:
    payload = recovery_required_payload()
    payload["state"] = "BLOCKED"
    payload["recovery"]["resolution"] = "mark_unrecoverable"
    payload["recovery"]["resolved_at"] = "2026-10-17T10:00:00+00:00"
    payload["blocked_reason"] = REASON
    payload["implementer_turns"] = [
        payload["recovery"]["attempt"]
    ]  # the frozen attempt was materialized into history
    payload["last_transition"] = TransitionRecord(
        action="recover",
        source="external_planner",
        previous_state="RECOVERY_REQUIRED",
        next_state="BLOCKED",
        cycle=1,
        role="implementer",
    ).model_dump(mode="json")
    accepted(payload)  # positive control: the settled shape is legal
    payload["blocked_reason"] = "turn_failed"
    with pytest.raises(Exception, match="blocked_reason == recovery_reason"):
        OrchestrationRun.model_validate(payload)


def test_the_recovery_attempt_also_pays_for_its_reserved_slot() -> None:
    payload = recovery_required_payload()
    payload["model_turns_used"] = 0
    payload["turn_attempts"] = 0
    with pytest.raises(Exception, match="do not account for"):
        OrchestrationRun.model_validate(payload)


def test_recovery_evidence_must_belong_to_the_run() -> None:
    payload = recovery_required_payload()
    evidence = payload["recovery"]["evidence"]
    evidence = rehashed(evidence, run_id="DR-" + "b" * 32)
    payload["recovery"]["evidence"] = evidence
    with pytest.raises(Exception, match="belongs to run"):
        OrchestrationRun.model_validate(payload)


def test_recovery_evidence_must_describe_the_frozen_attempt() -> None:
    payload = recovery_required_payload()
    payload["recovery"]["attempt"]["prompt_chars"] = 12
    with pytest.raises(Exception, match="disagrees with the frozen attempt"):
        OrchestrationRun.model_validate(payload)


def test_the_evidence_digest_is_verified_on_read() -> None:
    payload = recovery_required_payload()
    payload["recovery"]["evidence"]["attempt_prompt_chars"] = 12
    with pytest.raises(Exception, match="canonical field set"):
        OrchestrationRun.model_validate(payload)


def test_a_recovery_record_cannot_hide_a_live_outcome() -> None:
    payload = recovery_required_payload()
    payload["recovery"]["attempt"]["outcome"] = "in_flight"
    with pytest.raises(Exception, match="is not 'blocked'"):
        OrchestrationRun.model_validate(payload)


def test_the_frozen_attempt_must_carry_the_recorded_reason() -> None:
    payload = recovery_required_payload()
    payload["recovery"]["attempt"]["blocked_reason"] = "cycle_limit"
    with pytest.raises(Exception, match="not the recorded recovery reason"):
        OrchestrationRun.model_validate(payload)


def test_the_evidence_coverage_must_be_a_legal_class() -> None:
    # `coverage` is deliberately outside the 27-field digest (it is the reader's
    # verdict about the interval, not a fact about the attempt), so only the shape
    # invariant can refuse a hand-edited value.
    payload = recovery_required_payload()
    payload["recovery"]["evidence"]["coverage"] = "PWNED"
    with pytest.raises(Exception, match="coverage"):
        OrchestrationRun.model_validate(payload)


def rehashed(evidence: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    """Change an evidence field *and* its digest, so only cross-checks can fail."""
    payload = {**evidence, **overrides}
    draft = RecoveryEvidence.model_construct(**payload)
    return {**payload, "evidence_sha256": draft.compute_digest()}




