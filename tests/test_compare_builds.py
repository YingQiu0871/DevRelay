"""Reproducibility comparison helper tests (helper only, not a proof)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from compare_builds import compare  # noqa: E402


def _write(root: Path, name: str, content: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(content, encoding="utf-8")


def test_identical_artifact_directories_match(tmp_path: Path):
    first = tmp_path / "a"
    second = tmp_path / "b"
    for root in (first, second):
        _write(root, "devrelay-0.4.0-py3-none-any.whl", "wheel")
        _write(root, "DevRelay-Portable-Windows-x64.zip", "zip")
    assert compare(first, second) == []


def test_missing_and_changed_artifacts_are_reported(tmp_path: Path):
    first = tmp_path / "a"
    second = tmp_path / "b"
    _write(first, "one.whl", "one")
    _write(second, "one.whl", "two")
    _write(second, "two.whl", "two")
    problems = compare(first, second)
    assert "digest differs: one.whl" in problems
    assert "missing from first: two.whl" in problems
