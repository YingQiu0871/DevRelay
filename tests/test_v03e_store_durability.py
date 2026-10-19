"""v0.3-E: the orchestration store fsyncs a run document before it publishes it.

Each test drives the real ``OrchestrationStore.save`` and interrupts a real
filesystem primitive (``os.fsync`` / ``os.replace``) instead of hand-writing a
"broken" document, so the failure cases exercise the production write path:

* the temp file is fsynced *before* the replace;
* a failure before the replace leaves the previous document byte-identical and
  no temp file behind;
* a failure to fsync the parent directory is reported *after* the replace, with
  the new document already on disk (durability unconfirmed, retry idempotent);
* the stable code is ``orchestration_persistence_error``.
"""

from __future__ import annotations

import errno
import os

import pytest

from devrelay.errors import OrchestrationError, OrchestrationPersistenceError
from devrelay.orchestration import OrchestrationStore

GOOD_ID = "DR-" + "0123456789abcdef" * 2
#: A second, different-but-valid ``updated_at`` so a re-save really changes bytes.
LATER = "2026-01-01T00:00:00+00:00"


def make_store(tmp_path) -> OrchestrationStore:
    (tmp_path / ".devrelay").mkdir(parents=True, exist_ok=True)
    return OrchestrationStore(tmp_path / ".devrelay")


def make_run(tmp_path, run_id: str = GOOD_ID):
    from v03d_helpers import honest_run

    return honest_run(run_id=run_id, workspace=str(tmp_path.resolve()))


def runs_dir(tmp_path):
    return tmp_path / ".devrelay" / "orchestration" / "runs"


def document_bytes(tmp_path, run_id: str = GOOD_ID) -> bytes:
    return (runs_dir(tmp_path) / f"{run_id}.json").read_bytes()


def temp_files(tmp_path) -> list[str]:
    return sorted(p.name for p in runs_dir(tmp_path).iterdir() if p.name.endswith(".tmp"))


def test_save_fsyncs_the_temp_file_before_replace(tmp_path, monkeypatch):
    store = make_store(tmp_path)
    run = make_run(tmp_path)
    order: list[str] = []
    real_fsync = os.fsync
    real_replace = os.replace

    def recording_fsync(fd: int) -> None:
        order.append("fsync")
        real_fsync(fd)

    def recording_replace(src, dst) -> None:
        order.append("replace")
        real_replace(src, dst)

    monkeypatch.setattr(os, "fsync", recording_fsync)
    monkeypatch.setattr(os, "replace", recording_replace)
    store.save(run)

    assert order[:2] == ["fsync", "replace"], "the bytes must be fsynced before they are published"
    loaded = store.load(GOOD_ID)
    assert loaded.run_id == GOOD_ID
    assert loaded.updated_at == run.updated_at
    assert temp_files(tmp_path) == []


def test_temp_fsync_failure_keeps_the_old_document(tmp_path, monkeypatch):
    store = make_store(tmp_path)
    run = make_run(tmp_path)
    store.save(run)
    before = document_bytes(tmp_path)

    def failing_fsync(fd: int) -> None:
        raise OSError(errno.EIO, "simulated fsync failure")

    monkeypatch.setattr(os, "fsync", failing_fsync)
    with pytest.raises(OrchestrationPersistenceError) as excinfo:
        store.save(run.model_copy(update={"updated_at": LATER}))

    message = str(excinfo.value)
    assert message.startswith("orchestration_persistence_error: ")
    assert "the previous document was left in place" in message
    assert document_bytes(tmp_path) == before, "a failed fsync must not publish anything"
    assert temp_files(tmp_path) == [], "the temp file is cleaned up on every failure path"


def test_replace_failure_keeps_the_old_document(tmp_path, monkeypatch):
    store = make_store(tmp_path)
    run = make_run(tmp_path)
    store.save(run)
    before = document_bytes(tmp_path)

    def failing_replace(src, dst) -> None:
        raise OSError(errno.EACCES, "simulated replace failure")

    monkeypatch.setattr(os, "replace", failing_replace)
    with pytest.raises(OrchestrationPersistenceError) as excinfo:
        store.save(run.model_copy(update={"updated_at": LATER}))

    message = str(excinfo.value)
    assert message.startswith("orchestration_persistence_error: ")
    assert "the previous document was left in place" in message
    assert "was replaced" not in message
    assert document_bytes(tmp_path) == before
    assert temp_files(tmp_path) == []


@pytest.mark.skipif(os.name == "nt", reason="Windows cannot fsync a directory")
def test_directory_fsync_failure_reports_after_replace(tmp_path, monkeypatch):
    store = make_store(tmp_path)
    run = make_run(tmp_path)
    store.save(run)
    before = document_bytes(tmp_path)
    real_fsync = os.fsync
    calls: list[int] = []

    def failing_directory_fsync(fd: int) -> None:
        calls.append(fd)
        if len(calls) == 1:
            real_fsync(fd)  # the document's own temp file
            return
        raise OSError(errno.EIO, "simulated directory fsync failure")

    monkeypatch.setattr(os, "fsync", failing_directory_fsync)
    with pytest.raises(OrchestrationPersistenceError) as excinfo:
        store.save(run.model_copy(update={"updated_at": LATER}))

    message = str(excinfo.value)
    assert "was replaced" in message
    assert "durability" in message
    assert len(calls) == 2, "exactly one file fsync and one directory fsync"
    assert document_bytes(tmp_path) != before, "the replace happened before the failure"
    assert store.load(GOOD_ID).updated_at == LATER
    assert temp_files(tmp_path) == []


def test_persistence_error_has_a_stable_code():
    exc = OrchestrationPersistenceError("disk full")
    assert exc.code == "orchestration_persistence_error"
    assert str(exc).startswith("orchestration_persistence_error: ")
    assert isinstance(exc, OrchestrationError)


def test_a_successful_save_leaves_no_temp_residue(tmp_path):
    store = make_store(tmp_path)
    store.save(make_run(tmp_path))
    assert temp_files(tmp_path) == []
    assert sorted(p.name for p in runs_dir(tmp_path).iterdir()) == [f"{GOOD_ID}.json"]
