"""v0.2-C unit/acceptance coverage: baseline root, migration, staging, reparse."""

from __future__ import annotations

import json
import os
import stat as stat_module
from pathlib import Path

import pytest

from devrelay.artifacts.store import ArtifactStore
from devrelay.baseline.service import BaselineService
from devrelay.errors import BaselineCorruptError, DevRelayError
from devrelay.models import MAX_SUPPORTED_STATE_SCHEMA, STATE_SCHEMA_VERSION, TaskRun
from devrelay.pipeline.control_plane import (
    ControlPlaneError,
    build_manifest,
    build_staging_dir,
    cleanup_staging,
    diff_manifests,
    is_reparse_or_link,
)
from devrelay.providers.codex_runtime import write_json_new
from devrelay.workspace.runner import CommandRunner

from helpers import default_config, make_git_repo

STATE = "DR-0001"


# ---------------------------------------------------------------------------
# C45: baseline integrity root — a tampered blob fails closed before use
# ---------------------------------------------------------------------------
def test_baseline_blob_tamper_is_detected_before_use(tmp_path):
    repo = make_git_repo(tmp_path / "repo", initial_files={"a.txt": "a\n"})
    (repo / "scratch.txt").write_text("original\n", encoding="utf-8")
    store = ArtifactStore(repo)
    store.ensure_initialized()
    service = BaselineService(repo, CommandRunner(), store, default_config())
    service.capture(STATE)

    blob = next((store.task_dir(STATE) / "baseline" / "files").glob("*.blob"))
    blob.write_text("TAMPERED\n", encoding="utf-8")  # same length, new content
    with pytest.raises(BaselineCorruptError):
        service.validate_baseline(STATE)


def test_baseline_root_files_are_content_hashed(tmp_path):
    devrelay = tmp_path / ".devrelay"
    (devrelay / "tasks" / STATE / "baseline").mkdir(parents=True)
    patch = devrelay / "tasks" / STATE / "baseline" / "tracked.patch"
    patch.write_text("original patch\n", encoding="utf-8")
    staging = devrelay / "tmp" / "runtime" / "A1"
    staging.mkdir(parents=True)

    def identity() -> str:
        return build_manifest(
            devrelay, staging_dir=staging, allowed_files=("last-message.raw.json",)
        ).protected_sha256()

    before = identity()
    patch.write_text("tampered patch\n", encoding="utf-8")
    assert identity() != before


# ---------------------------------------------------------------------------
# C18: schema 5 states keep loading and migrate through the existing machinery
# ---------------------------------------------------------------------------
def test_schema5_state_loads_and_migrates(tmp_path):
    store = ArtifactStore(tmp_path / "ws")
    store.ensure_initialized()
    store.task_dir(STATE).mkdir(parents=True, exist_ok=True)
    legacy = {
        "task_id": STATE,
        "title": "v0.2-B task",
        "state_schema_version": 5,
        "state": "PLAN_READY",
        "plan_ready": True,
        "packet": {"task_id": STATE, "title": "t", "objective": "o"},
        "current_findings": [],
        "open_p3": [],
        "review_history": [],
        "test_evidence": [],
        "implementation_report_paths": [],
        "audit": [],
        "policy_violations": [],
        "attempts": [],
        "provider_calls": [],
        "review_attempts": [],
        "finding_seen_counts": {},
        "applied_reviews": [],
        "policy_refreshes": [],
    }
    store.state_path(STATE).write_text(json.dumps(legacy), encoding="utf-8")
    before = store.state_path(STATE).read_bytes()

    task = store.read_task(STATE)                 # read-only: no migration
    assert task.state_schema_version == 5
    assert store.state_path(STATE).read_bytes() == before

    store.write_task(task)                        # first mutating write migrates
    assert json.loads(store.state_path(STATE).read_text(encoding="utf-8"))[
        "state_schema_version"
    ] == STATE_SCHEMA_VERSION
    assert (store.task_dir(STATE) / "state.v5.json.bak").read_bytes() == before
    assert MAX_SUPPORTED_STATE_SCHEMA == STATE_SCHEMA_VERSION


# ---------------------------------------------------------------------------
# C36 / C37: staging lifecycle and durable-artifact immutability
# ---------------------------------------------------------------------------
def test_stale_staging_cleanup_and_refusal(tmp_path):
    devrelay = tmp_path / ".devrelay"
    staging = devrelay / "tmp" / "runtime" / "A1"
    staging.mkdir(parents=True)
    (staging / "last-message.raw.json").write_text("stale", encoding="utf-8")
    assert cleanup_staging(staging, allowed_files=("last-message.raw.json",)) == [
        "last-message.raw.json"
    ]
    assert list(staging.iterdir()) == []

    # unexpected content is never silently deleted
    (staging / "evil.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ControlPlaneError):
        cleanup_staging(staging, allowed_files=("last-message.raw.json",))
    # and a dirty staging directory is refused before a new attempt starts
    (staging / "evil.txt").unlink()
    (staging / "last-message.raw.json").write_text("stale", encoding="utf-8")
    with pytest.raises(ControlPlaneError):
        build_staging_dir(staging)


def test_durable_runtime_artifact_collision_fails_closed(tmp_path):
    target = tmp_path / "result.json"
    target.write_text("{}", encoding="utf-8")
    with pytest.raises(DevRelayError):
        write_json_new(target, {"schema_version": 1})


# ---------------------------------------------------------------------------
# C48: reparse/junction detection (mocked attributes + real probe where possible)
# ---------------------------------------------------------------------------
def test_reparse_detection_uses_platform_attributes(tmp_path, monkeypatch):
    target = tmp_path / "state.json"
    target.write_text("{}", encoding="utf-8")
    assert is_reparse_or_link(target) is False

    real_lstat = os.lstat
    real_stat_result = real_lstat(str(target))

    class FakeStat:
        def __init__(self, base):
            self._base = base
            self.st_file_attributes = 0x400  # FILE_ATTRIBUTE_REPARSE_POINT
            for field in ("st_mode", "st_dev", "st_ino", "st_size"):
                setattr(self, field, getattr(base, field))

        def __getattr__(self, item):  # pragma: no cover - defensive
            return getattr(self._base, item)

    monkeypatch.setattr(os, "lstat", lambda path: FakeStat(real_stat_result))
    assert is_reparse_or_link(target) is True
    monkeypatch.setattr(os, "lstat", real_lstat)

    # real junction probe (mklink /J needs no elevation); skipped if the platform
    # cannot create one - reported as SKIPPED, never as PASS
    junction = tmp_path / "junction"
    created = False
    if os.name == "nt":
        import subprocess

        proc = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(junction), str(tmp_path)],
            capture_output=True,
            text=True,
        )
        created = proc.returncode == 0 and junction.exists()
    if not created:
        pytest.skip("SKIPPED BY PLATFORM PRIVILEGE: cannot create a junction/symlink")
    assert is_reparse_or_link(junction) is True


# ---------------------------------------------------------------------------
# C43: staging-directory metadata must not false-positive; other entries must
# ---------------------------------------------------------------------------
def test_staging_metadata_exempt_but_unexpected_entries_detected(tmp_path):
    devrelay = tmp_path / ".devrelay"
    (devrelay / "tasks").mkdir(parents=True)
    (devrelay / "state.json").write_text("{}", encoding="utf-8")
    staging = devrelay / "tmp" / "runtime" / "A1"
    staging.mkdir(parents=True)
    allowed = ("last-message.raw.json",)

    pre = build_manifest(devrelay, staging_dir=staging, allowed_files=allowed)
    (staging / "last-message.raw.json").write_text('{"ok": true}', encoding="utf-8")
    post = build_manifest(devrelay, staging_dir=staging, allowed_files=allowed)
    assert diff_manifests(pre, post) == []          # allowed write: no violation

    (staging / "evil.txt").write_text("x", encoding="utf-8")
    post2 = build_manifest(devrelay, staging_dir=staging, allowed_files=allowed)
    diffs = diff_manifests(pre, post2)
    assert [d.rel_path for d in diffs] == ["tmp/runtime/A1/evil.txt"]

    (staging / "evil.txt").unlink()
    (staging / "nested").mkdir()
    post3 = build_manifest(devrelay, staging_dir=staging, allowed_files=allowed)
    assert any(d.rel_path.endswith("nested") for d in diff_manifests(pre, post3))
