"""v0.3-E evidence, recovery record and legal-action models (pure, offline)."""

from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError

from devrelay.orchestration import recovery
from devrelay.orchestration.models import (
    EVIDENCE_DIGEST_DOMAIN,
    RECOVERY_REASONS,
    RunState,
    RecoveryEvidence,
    RecoveryRecord,
    legal_next_actions,
)
from v03d_helpers import honest_run, with_in_flight


def evidence_for(**overrides):
    """A digest-consistent evidence set for one interrupted implementer turn."""
    run = with_in_flight(honest_run(RunState.READY_IMPLEMENTER, max_cycles=2), "implementer")
    attempt = run.in_flight_turn
    evidence = recovery.build_evidence(
        run,
        attempt,
        entry_state=RunState.READY_IMPLEMENTER,
        ledger_scan=None,
        remote=recovery.RemoteMatch(recovery.REMOTE_GAP),
    )
    payload = evidence.model_dump(mode="json")
    payload.update(overrides)
    return payload


def recomputed(**overrides):
    """Change a field *and* its digest, i.e. a different but self-consistent set."""
    evidence = RecoveryEvidence.model_construct(**evidence_for())
    payload = {
        **evidence.model_dump(mode="json"),
        **overrides,
    }
    draft = RecoveryEvidence.model_construct(**payload)
    return {**payload, "evidence_sha256": draft.compute_digest()}


# ---------------------------------------------------------------------------
# the canonical evidence field set
# ---------------------------------------------------------------------------
def test_evidence_values_are_the_frozen_27_field_canonical_set() -> None:
    evidence = RecoveryEvidence.model_validate(evidence_for())
    values = evidence.values()
    assert len(values) == 27
    assert values[0] == EVIDENCE_DIGEST_DOMAIN == "devrelay-evidence-v1"
    # one JSON scalar per field, joined by "\n", no trailing newline
    joined = "\n".join(values)
    assert not joined.endswith("\n")
    assert joined.count("\n") == 26
    assert evidence.run_id == values[1]
    # absent strings are "", absent numbers/ids are "null" - never omitted
    assert evidence.ledger_call_id == ""
    assert "null" in values  # ledger_http_status is absent
    assert values[-1] == "null"  # remote_matched_digest is absent


def test_evidence_digest_is_sha256_of_the_canonical_join() -> None:
    evidence = RecoveryEvidence.model_validate(evidence_for())
    expected = hashlib.sha256("\n".join(evidence.values()).encode("utf-8")).hexdigest()
    assert evidence.evidence_sha256 == expected
    assert len(evidence.evidence_sha256) == 64


def test_evidence_digest_is_order_and_content_sensitive() -> None:
    base = RecoveryEvidence.model_validate(evidence_for())
    other = RecoveryEvidence.model_validate(recomputed(remote_message_id="msg_1"))
    assert base.evidence_sha256 != other.evidence_sha256
    # changing a value without recomputing the digest is corruption, not a new set
    with pytest.raises(ValidationError, match="does not match its own canonical field"):
        RecoveryEvidence.model_validate(evidence_for(attempt_prompt_chars=12))


def test_coverage_is_not_part_of_the_digest() -> None:
    plain = RecoveryEvidence.model_validate(evidence_for(coverage="evidence_gap"))
    proven = RecoveryEvidence.model_validate(evidence_for(coverage="proven_interval"))
    assert plain.evidence_sha256 == proven.evidence_sha256


def test_evidence_carries_no_prompt_reply_or_credential_fields() -> None:
    keys = set(RecoveryEvidence.model_fields)
    for forbidden in (
        "prompt",
        "prompt_text",
        "reply",
        "response",
        "reasoning",
        "token",
        "credential",
        "authorization",
    ):
        assert forbidden not in keys


# ---------------------------------------------------------------------------
# recovery record shape
# ---------------------------------------------------------------------------
def _record_payload(**overrides):
    run = with_in_flight(honest_run(RunState.READY_IMPLEMENTER, max_cycles=2), "implementer")
    attempt = run.in_flight_turn
    evidence, frozen = recovery.build_record(
        run,
        attempt,
        entry_state=RunState.READY_IMPLEMENTER,
        reason="turn_interrupted",
        ledger_scan=None,
        remote=None,
    )
    payload = {
        "attempt": frozen.model_dump(mode="json"),
        "recovery_reason": "turn_interrupted",
        "resolution": "",
        "resolved_at": "",
        "evidence": evidence.model_dump(mode="json"),
    }
    payload.update(overrides)
    return payload


def test_an_unresolved_record_is_the_legal_recovery_required_shape() -> None:
    record = RecoveryRecord.model_validate(_record_payload())
    assert record.recovery_reason in RECOVERY_REASONS
    assert record.resolution == ""
    assert record.resolved_at == ""
    assert record.attempt.outcome == "blocked"
    assert record.attempt.blocked_reason == "turn_interrupted"
    assert record.attempt.completed_at


def test_unknown_recovery_reasons_are_rejected() -> None:
    with pytest.raises(ValidationError, match="recovery_reason"):
        RecoveryRecord.model_validate(_record_payload(recovery_reason="provider_timeout"))


def test_a_resolution_and_its_timestamp_are_all_or_nothing() -> None:
    payload = _record_payload(resolution="mark_unrecoverable", resolved_at="")
    with pytest.raises(ValidationError, match="either both"):
        RecoveryRecord.model_validate(payload)
    payload = _record_payload(resolution="", resolved_at="2026-10-17T10:00:00+00:00")
    with pytest.raises(ValidationError, match="either both"):
        RecoveryRecord.model_validate(payload)


def test_an_adopted_attempt_must_be_completed_and_a_failed_one_blocked() -> None:
    with pytest.raises(ValidationError, match="outcome"):
        RecoveryRecord.model_validate(
            _record_payload(
                resolution="mark_unrecoverable",
                resolved_at="2026-10-17T10:00:00+00:00",
                attempt={
                    **_record_payload()["attempt"],
                    "outcome": "completed",
                    "blocked_reason": "",
                },
            )
        )


def test_the_materialized_attempt_must_be_finished() -> None:
    payload = _record_payload()
    payload["attempt"] = {**payload["attempt"], "completed_at": ""}
    with pytest.raises(ValidationError, match="must be finished"):
        RecoveryRecord.model_validate(payload)


# ---------------------------------------------------------------------------
# legal actions
# ---------------------------------------------------------------------------
def test_recovery_required_advertises_reconcile_and_the_one_resolution() -> None:
    assert legal_next_actions(RunState.RECOVERY_REQUIRED) == [
        "devrelay_reconcile_run",
        "devrelay_resolve_recovery(mark_unrecoverable)",
    ]


def test_only_recovery_is_legal_while_a_v2_turn_is_in_flight() -> None:
    run = with_in_flight(honest_run(RunState.READY_IMPLEMENTER, max_cycles=2), "implementer")
    assert run.summary()["legal_next_actions"] == ["devrelay_resolve_recovery"]
    assert run.in_flight_turn is not None
    assert run.summary()["acceptance_authority"] is False


def test_the_summary_exposes_the_recovery_identifiers_only() -> None:
    run = honest_run(RunState.READY_IMPLEMENTER, max_cycles=2)
    summary = run.summary()
    assert "recovery" in summary
    assert summary["recovery"] is None
    assert summary["recovery_reason"] == ""
    assert "attempt" not in summary
