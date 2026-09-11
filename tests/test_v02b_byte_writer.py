"""v0.2-B stage 1: byte-true textual artifact writes (Windows-safe).

Regression: ``Path.write_text`` translates LF to CRLF on Windows while
``hashlib.sha256(text.encode())`` hashes LF, so a recorded digest could never
match the bytes on disk.  Every textual artifact now goes through
``encode_lf`` and every digest is computed from those exact bytes.
"""

from __future__ import annotations

import hashlib
import json

from devrelay.artifacts.store import (
    ArtifactStore,
    encode_lf,
    sha256_file,
    sha256_hex,
)
from devrelay.models import TaskRun


def test_encode_lf_normalizes_crlf_and_bare_cr() -> None:
    assert encode_lf("a\r\nb\r\n") == b"a\nb\n"
    assert encode_lf("a\nb\n") == b"a\nb\n"
    assert encode_lf("a\rb") == b"a\nb"


def test_digest_is_of_bytes_not_of_text() -> None:
    crlf_text = "budget:\r\n  max_reviewer_calls: 2\r\n"
    # The old defect: hashing the in-memory text disagreed with the file bytes.
    assert sha256_hex(encode_lf(crlf_text)) != hashlib.sha256(
        crlf_text.encode("utf-8")
    ).hexdigest()
    # LF text is stable: both agree.
    lf_text = "budget:\n  max_reviewer_calls: 2\n"
    assert sha256_hex(encode_lf(lf_text)) == hashlib.sha256(
        lf_text.encode("utf-8")
    ).hexdigest()


def test_store_write_text_writes_lf_bytes(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "ws")
    store.ensure_initialized()
    target = store.devrelay_dir / "tasks" / "DR-0001" / "config.snapshot.yaml"
    store.write_text(target, "pipeline:\n  max_fix_iterations: 3\n")
    raw = target.read_bytes()
    assert b"\r" not in raw
    assert raw == encode_lf("pipeline:\n  max_fix_iterations: 3\n")
    # Re-reading through the text API normalizes nothing away.
    assert store.read_text(target) == "pipeline:\n  max_fix_iterations: 3\n"


def test_write_text_with_digest_matches_disk_bytes(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "ws")
    store.ensure_initialized()
    # CRLF input is normalized, and the returned digest is the on-disk digest.
    text = "budget:\r\n  max_reviewer_calls: 2\r\n"
    path, digest = store.write_text_with_digest(tmp_path / "policy.yaml", text)
    assert digest == sha256_file(path)
    assert path.read_bytes() == b"budget:\n  max_reviewer_calls: 2\n"


def test_task_state_and_json_writes_are_lf(tmp_path) -> None:
    store = ArtifactStore(tmp_path / "ws")
    store.ensure_initialized()
    task = TaskRun(task_id="DR-0001", title="t")
    store.write_task(task)
    raw = store.state_path("DR-0001").read_bytes()
    assert b"\r" not in raw
    assert json.loads(raw.decode("utf-8"))["task_id"] == "DR-0001"

    jpath = store.write_json(store.devrelay_dir / "extra.json", {"a": 1})
    assert b"\r" not in jpath.read_bytes()
