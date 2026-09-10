"""Static validation of the PyPI Trusted Publishing workflow.

These tests fail if the release workflow ever stops being manual-only, gains
write permissions it does not need, drops the environment used for OIDC
matching, or stops publishing the exact verified release artifacts.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "release.yml"
PUBLISH_ACTION = "pypa/gh-action-pypi-publish@release/v1"
WHEEL_SHA256 = "8c9b3261455758a60eb95fa51c77100530e759eb688fc2ecd11447791e03a7c5"
SDIST_SHA256 = "aea142a7975d2d9f651b94db252547be23d91742a862df0aef9848d9409da005"


def _load() -> tuple[dict, dict]:
    data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    # PyYAML (YAML 1.1) parses the bare key ``on`` as boolean True.
    triggers = data.get("on", data.get(True))
    return data, triggers


def _publish_job() -> dict:
    _, data = None, _load()[0]
    return data["jobs"]["publish"]


def test_workflow_filename_is_release_yml():
    # PyPI matches the trusted publisher by this exact file name.
    assert WORKFLOW_PATH.is_file()
    assert WORKFLOW_PATH.name == "release.yml"


def test_only_manual_dispatch_can_trigger_the_workflow():
    _, triggers = _load()
    assert set(triggers) == {"workflow_dispatch"}
    inputs = triggers["workflow_dispatch"]["inputs"]
    assert inputs["tag"]["default"] == "v0.1.0"
    assert inputs["tag"]["required"] is True
    assert inputs["confirm"]["required"] is True
    assert inputs["confirm"]["default"] == ""


def test_job_is_gated_on_confirm_publish():
    job = _publish_job()
    assert "inputs.confirm == 'PUBLISH'" in job["if"]


def test_publish_job_uses_the_pypi_environment():
    job = _publish_job()
    environment = job["environment"]
    name = environment["name"] if isinstance(environment, dict) else environment
    assert name == "pypi"


def test_permissions_are_minimal():
    data, _ = _load()
    assert data["permissions"] == {"contents": "read"}
    job_permissions = _publish_job()["permissions"]
    assert job_permissions == {"contents": "read", "id-token": "write"}
    for job in data["jobs"].values():
        for scope, level in (job.get("permissions") or {}).items():
            if scope == "id-token":
                continue
            assert level == "read", f"unexpected write permission: {scope}: {level}"


def test_publishes_with_the_official_action_and_no_credentials():
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert PUBLISH_ACTION in text
    assert "packages-dir: dist/" in text
    assert "attestations: false" in text
    for forbidden in (
        "twine upload",
        "${{ secrets.",
        "PYPI_API_TOKEN",
        "password:",
        "username:",
    ):
        assert forbidden not in text, f"workflow must not contain {forbidden!r}"


def test_downloads_release_artifacts_instead_of_rebuilding():
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "gh release download" in text
    assert "python -m build" not in text
    assert "python3 -m build" not in text


def test_integrity_pins_match_the_published_release_assets():
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert WHEEL_SHA256 in text
    assert SDIST_SHA256 in text
    assert "bootstrap integrity pin" in text


def test_twine_check_runs_before_the_upload_step():
    job = _publish_job()
    steps = job["steps"]
    names = [step.get("name", "") for step in steps]
    check_index = next(i for i, name in enumerate(names) if "twine check" in name.lower())
    publish_index = next(
        i for i, step in enumerate(steps) if PUBLISH_ACTION in str(step.get("uses", ""))
    )
    assert check_index < publish_index
    assert steps[publish_index]["with"]["packages-dir"] == "dist/"


def test_bootstrap_guard_rejects_other_tags():
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert 'TAG" != "v0.1.0"' in text
    assert "bootstrap safety guard" in text
