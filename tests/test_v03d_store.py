"""v0.3-D durable orchestration store (offline)."""

from __future__ import annotations

import json

import pytest

from devrelay.errors import OrchestrationRunNotFoundError, OrchestrationStateCorruptError
from devrelay.orchestration import OrchestrationRun, OrchestrationStore, generate_run_id
from devrelay.orchestration.store import RUN_ID_PATTERN, valid_run_id
from devrelay.orchestration.models import RoleRouteSnapshot

GOOD_ID = "DR-" + "0123456789abcdef" * 2


def make_run(run_id: str = GOOD_ID) -> OrchestrationRun:
    return OrchestrationRun(
        run_id=run_id,
        workspace="C:/ws",
        implementer_session_id="ses_impl",
        reviewer_session_id="ses_rev",
        max_cycles=2,
        model_turn_budget=4,
        route_snapshot={
            "implementer": RoleRouteSnapshot(role="implementer", model="provider-a/model-a"),
            "reviewer": RoleRouteSnapshot(role="reviewer", model="provider-b/model-b"),
        },
    )


def store_for(tmp_path, factory=None) -> OrchestrationStore:
    (tmp_path / ".devrelay").mkdir(parents=True, exist_ok=True)
    return OrchestrationStore(tmp_path / ".devrelay", **({"run_id_factory": factory} if factory else {}))


# ---------------------------------------------------------------------------
# identity and containment
# ---------------------------------------------------------------------------
def test_generated_ids_are_collision_resistant_and_pattern_valid():
    ids = {generate_run_id() for _ in range(500)}
    assert len(ids) == 500
    assert all(valid_run_id(run_id) for run_id in ids)
    import re

    assert all(re.match(RUN_ID_PATTERN, run_id) for run_id in ids)


@pytest.mark.parametrize(
    "candidate",
    [
        "../../etc/passwd",
        "..",
        "DR-../../x",
        "/abs/path",
        "C:/windows/system32/x",
        "DR-0123456789abcdef0123456789abcdef/../x",
        "DR-0123456789abcdef0123456789abcde",  # too short
        "DR-0123456789ABCDEF0123456789ABCDEF",  # uppercase is not generated
        "DR-" + "0" * 200,  # very long
        "",
        None,
        7,
    ],
)
def test_caller_supplied_ids_can_never_be_paths(tmp_path, candidate):
    store = store_for(tmp_path)
    assert valid_run_id(candidate) is False
    with pytest.raises(OrchestrationRunNotFoundError):
        store.path_for(candidate)
    with pytest.raises(OrchestrationRunNotFoundError):
        store.load(candidate)
    assert store.exists(candidate) is False
    # nothing was created outside the runs directory
    assert not (tmp_path / ".devrelay" / "orchestration").exists() or list(
        (tmp_path / ".devrelay" / "orchestration").rglob("*.json")
    ) == []


def test_contained_path_stays_under_the_runs_directory(tmp_path):
    store = store_for(tmp_path)
    path = store.path_for(GOOD_ID)
    assert path.parent == tmp_path / ".devrelay" / "orchestration" / "runs"
    assert path.name == f"{GOOD_ID}.json"


def test_bad_run_id_factory_is_rejected(tmp_path):
    store = store_for(tmp_path, factory=lambda: "../../escape")
    with pytest.raises(OrchestrationStateCorruptError):
        store.new_run_id()


# ---------------------------------------------------------------------------
# round trip, atomicity, corruption
# ---------------------------------------------------------------------------
def test_round_trip_preserves_the_run_document(tmp_path):
    store = store_for(tmp_path)
    run = make_run()
    store.create(run)
    loaded = store.load(GOOD_ID)
    assert loaded.model_dump(mode="json") == run.model_dump(mode="json")
    assert loaded.state.value == "READY_IMPLEMENTER"
    assert loaded.model_turn_budget == 4


def test_writes_are_atomic_and_leave_no_temp_files(tmp_path):
    store = store_for(tmp_path)
    store.create(make_run())
    for index in range(5):
        run = store.load(GOOD_ID)
        run.turn_attempts = index + 1
        store.save(run)
    files = sorted(path.name for path in store.root.iterdir())
    assert files == [f"{GOOD_ID}.json"]
    assert json.loads((store.root / f"{GOOD_ID}.json").read_text(encoding="utf-8"))["turn_attempts"] == 5


def test_missing_run_is_reported_as_not_found(tmp_path):
    store = store_for(tmp_path)
    with pytest.raises(OrchestrationRunNotFoundError):
        store.load(GOOD_ID)


def test_corrupt_json_is_reported_and_never_reset(tmp_path):
    store = store_for(tmp_path)
    store.create(make_run())
    path = store.path_for(GOOD_ID)
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(OrchestrationStateCorruptError):
        store.load(GOOD_ID)
    assert path.read_text(encoding="utf-8") == "{not json", "a corrupt run is never rewritten"


def test_malformed_document_is_reported_as_corrupt(tmp_path):
    store = store_for(tmp_path)
    store.create(make_run())
    path = store.path_for(GOOD_ID)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["state"] = "SOMETHING_FUZZY"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(OrchestrationStateCorruptError):
        store.load(GOOD_ID)


def test_unknown_fields_are_rejected_as_corrupt(tmp_path):
    store = store_for(tmp_path)
    store.create(make_run())
    path = store.path_for(GOOD_ID)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["reviewer_approved"] = True
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(OrchestrationStateCorruptError):
        store.load(GOOD_ID)


def test_document_with_a_different_run_id_is_corrupt(tmp_path):
    store = store_for(tmp_path)
    store.create(make_run())
    path = store.path_for(GOOD_ID)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["run_id"] = "DR-" + "f" * 32
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(OrchestrationStateCorruptError):
        store.load(GOOD_ID)


def test_touch_updates_the_timestamp(tmp_path):
    store = store_for(tmp_path)
    run = store.create(make_run())
    before = run.updated_at
    store.touch(run)
    assert store.load(GOOD_ID).updated_at >= before
