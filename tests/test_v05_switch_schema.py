"""v3 run schema / session-switch evidence validation."""

from __future__ import annotations

import pytest

from devrelay.errors import OrchestrationStateCorruptError
from devrelay.orchestration.models import (
    ORCHESTRATION_SCHEMA_VERSION,
    OrchestrationRun,
    SessionSwitchRecord,
)
from v03d_helpers import honest_run

SOURCE = "ses_source"
TARGET = "ses_target"


def _payload(tmp_path):
    run = honest_run(workspace=str(tmp_path), run_id="DR-" + "b" * 32)
    payload = run.model_dump(mode="json")
    payload["implementer_session_id"] = TARGET
    payload["session_switch_history"] = [
        {
            "switch_id": "SW-" + "c" * 32,
            "role": "implementer",
            "source_session_id": SOURCE,
            "target_session_id": TARGET,
            "switched_at": "2026-10-25T00:00:00+00:00",
            "source_revision": "2026-10-25T00:00:00+00:00",
            "target_lease_acquired_at": "2026-10-25T00:00:00+00:00",
        }
    ]
    return payload


def test_new_runs_are_v3_with_empty_switch_history(tmp_path):
    run = honest_run(workspace=str(tmp_path))
    assert run.schema_version == ORCHESTRATION_SCHEMA_VERSION == 3
    assert run.session_switch_history == []
    assert run.summary()["session_switch_history"] == []


def test_valid_switch_evidence_round_trips(tmp_path):
    payload = _payload(tmp_path)
    loaded = OrchestrationRun.model_validate(payload)
    assert len(loaded.session_switch_history) == 1
    assert loaded.session_switch_history[0].role == "implementer"
    assert loaded.implementer_session_id == TARGET
    assert loaded.summary()["session_switch_history"][0]["switch_id"] == "SW-" + "c" * 32


def test_v2_document_cannot_carry_switch_history(tmp_path):
    payload = _payload(tmp_path)
    payload["schema_version"] = 2
    with pytest.raises(OrchestrationStateCorruptError):
        OrchestrationRun.model_validate(payload)


def test_switch_history_must_continue_from_previous_target(tmp_path):
    payload = _payload(tmp_path)
    payload["session_switch_history"].append(
        {
            "switch_id": "SW-" + "d" * 32,
            "role": "implementer",
            "source_session_id": "ses_wrong",
            "target_session_id": "ses_third",
            "switched_at": "2026-10-25T00:01:00+00:00",
            "source_revision": "2026-10-25T00:01:00+00:00",
            "target_lease_acquired_at": "2026-10-25T00:01:00+00:00",
        }
    )
    with pytest.raises(OrchestrationStateCorruptError):
        OrchestrationRun.model_validate(payload)


def test_switch_record_rejects_invalid_id_and_blank_sessions():
    with pytest.raises(ValueError):
        SessionSwitchRecord(
            switch_id="SW-nope",
            role="implementer",
            source_session_id=SOURCE,
            target_session_id=TARGET,
            switched_at="x",
            source_revision="x",
            target_lease_acquired_at="x",
        )
