"""Static validation of the PyPI Trusted Publishing workflows.

These tests fail if the release workflow ever stops being manual-only, gains
write permissions it does not need, drops the environment used for OIDC
matching, publishes anything other than distributions built from the released
source, or loses a pre-publication guard.  They also keep the test CI running
the suite on both supported operating systems.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
WORKFLOW_PATH = WORKFLOWS / "release.yml"
TEST_WORKFLOW_PATH = WORKFLOWS / "test.yml"
PUBLISH_ACTION = "pypa/gh-action-pypi-publish@release/v1"


def _load() -> tuple[dict, dict]:
    data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    # PyYAML (YAML 1.1) parses the bare key ``on`` as boolean True.
    triggers = data.get("on", data.get(True))
    return data, triggers


def _publish_job() -> dict:
    data, _ = _load()
    return data["jobs"]["publish"]


def _text() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def _run_text(step_name: str) -> str:
    for step in _publish_job()["steps"]:
        if step.get("name") == step_name:
            return step.get("run", "")
    raise AssertionError(f"no publish step named {step_name!r}")


def test_workflow_filename_is_release_yml():
    # PyPI matches the trusted publisher by this exact file name.
    assert WORKFLOW_PATH.is_file()
    assert WORKFLOW_PATH.name == "release.yml"


def test_only_manual_dispatch_can_trigger_the_workflow():
    _, triggers = _load()
    assert set(triggers) == {"workflow_dispatch"}
    inputs = triggers["workflow_dispatch"]["inputs"]
    assert inputs["tag"]["default"] == "v0.3.0"
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


def test_workflow_level_permissions_stay_read_only():
    data, _ = _load()
    assert data["permissions"] == {"contents": "read"}


def test_job_permissions_are_limited_to_the_upload_step_needs():
    # `contents: write` is required to attach the built distributions to the
    # release; `id-token: write` is required for OIDC.  Nothing else may be
    # granted, at any scope.
    job_permissions = _publish_job()["permissions"]
    assert job_permissions == {"contents": "write", "id-token": "write"}
    data, _ = _load()
    for job in data["jobs"].values():
        for scope, level in (job.get("permissions") or {}).items():
            if scope == "id-token":
                continue
            if scope == "contents":
                assert level in {"read", "write"}
                continue
            assert level == "read", f"unexpected write permission: {scope}: {level}"


def test_inputs_never_reach_the_shell_as_interpolated_text():
    # `${{ inputs.* }}` in `run:` text would let a crafted dispatch input run
    # arbitrary shell; inputs travel through `env:` instead.
    for step in _publish_job()["steps"]:
        run_text = step.get("run") or ""
        assert not re.search(r"\$\{\{\s*inputs\.", run_text), (
            f"step {step.get('name')!r} interpolates an input into shell text"
        )


def test_checkout_uses_the_requested_tag():
    checkout = [
        step
        for step in _publish_job()["steps"]
        if str(step.get("uses", "")).startswith("actions/checkout")
    ]
    assert len(checkout) == 1
    assert checkout[0]["with"]["ref"] == "${{ inputs.tag }}"
    assert checkout[0]["with"]["fetch-depth"] == 0


def test_tag_shape_is_validated_before_anything_else():
    text = _text()
    assert r"^v[0-9]+\.[0-9]+\.[0-9]+$" in text
    steps = _publish_job()["steps"]
    names = [step.get("name", "") for step in steps]
    validation_index = next(
        i for i, name in enumerate(names) if "tag shape" in name.lower()
    )
    publish_index = next(
        i for i, step in enumerate(steps) if PUBLISH_ACTION in str(step.get("uses", ""))
    )
    assert validation_index < publish_index


def test_tag_must_match_the_version_in_pyproject():
    text = _text()
    assert "tomllib" in text
    assert '"pyproject.toml"' in text
    assert '"project"' in text and '"version"' in text
    assert "tag == f\"v{version}\"" in text


def test_tag_must_be_reachable_from_origin_main():
    text = _text()
    assert "git fetch --no-tags origin main" in text
    assert "git merge-base --is-ancestor" in text


def test_verifies_the_github_release_is_published():
    text = _text()
    assert "gh release view" in text
    assert "isDraft,isPrerelease" in text


def test_builds_from_source_instead_of_downloading_artifacts():
    text = _text()
    assert "python -m build --outdir dist" in text
    assert "gh release download" not in text


def test_keeps_no_bootstrap_pins_or_hardcoded_v0_1_assets():
    text = _text()
    assert "v0.1.0" not in text
    assert "bootstrap" not in text
    assert "8c9b3261455758a60eb95fa51c77100530e759eb688fc2ecd11447791e03a7c5" not in text
    assert "aea142a7975d2d9f651b94db252547be23d91742a862df0aef9848d9409da005" not in text


def test_requires_exactly_one_wheel_one_sdist_and_the_packaged_profile():
    text = _text()
    assert "devrelay/profiles/default.yaml" in text
    assert "zipfile" in text and "tarfile" in text
    assert "SHA256SUMS" in text


def test_embedded_python_blocks_are_syntactically_valid():
    # The workflow ships Python inside shell variables; a syntax error there
    # would only surface in a real publication run.
    code_blocks = [
        step
        for step in _publish_job()["steps"]
        if "PYCODE='" in (step.get("run") or "")
    ]
    assert len(code_blocks) == 2
    for step in code_blocks:
        lines = (step["run"]).splitlines()
        start = next(i for i, line in enumerate(lines) if line.strip() == "PYCODE='")
        base = len(lines[start]) - len(lines[start].lstrip())
        body: list[str] = []
        for line in lines[start + 1 :]:
            if line.strip() == "'":
                break
            body.append(line[base:])
        code = "\n".join(body)
        compile(code, step["name"], "exec")
        assert 'python -c "$PYCODE"' in step["run"]


def test_publishes_with_the_official_action_and_no_credentials():
    text = _text()
    assert PUBLISH_ACTION in text
    assert "packages-dir: dist/" in text
    assert "attestations: true" in text
    for forbidden in (
        "twine upload",
        "${{ secrets.",
        "PYPI_API_TOKEN",
        "password:",
        "username:",
    ):
        assert forbidden not in text, f"workflow must not contain {forbidden!r}"


def test_twine_check_runs_before_the_upload_step():
    steps = _publish_job()["steps"]
    names = [step.get("name", "") for step in steps]
    check_index = next(i for i, name in enumerate(names) if "twine check" in name.lower())
    publish_index = next(
        i for i, step in enumerate(steps) if PUBLISH_ACTION in str(step.get("uses", ""))
    )
    assert check_index < publish_index
    assert steps[publish_index]["with"]["packages-dir"] == "dist/"


def test_distributions_and_checksums_are_attached_to_the_release():
    text = _text()
    assert 'gh release upload "$TAG" dist/*' in text


def test_test_workflow_runs_the_suite_on_both_platforms():
    data = yaml.safe_load(TEST_WORKFLOW_PATH.read_text(encoding="utf-8"))
    triggers = data.get("on", data.get(True))
    assert set(triggers) == {"push", "pull_request"}
    assert triggers["push"]["branches"] == ["main", "v0.3-*"]
    assert data["permissions"] == {"contents": "read"}

    job = data["jobs"]["pytest"]
    assert job["timeout-minutes"] == 30
    assert job["strategy"]["fail-fast"] is False
    assert job["strategy"]["matrix"]["os"] == ["ubuntu-latest", "windows-latest"]
    assert job["strategy"]["matrix"]["python-version"] == [
        "3.11",
        "3.12",
        "3.13",
        "3.14",
    ]
    checkout = [
        step
        for step in job["steps"]
        if str(step.get("uses", "")).startswith("actions/checkout")
    ]
    assert checkout
    setup = [
        step
        for step in job["steps"]
        if str(step.get("uses", "")).startswith("actions/setup-python")
    ]
    assert setup and setup[0]["with"]["cache"] == "pip"
    commands = [step.get("run", "") for step in job["steps"]]
    assert any('pip install -e ".[dev]"' in command for command in commands)
    assert any("python -m pytest -q" in command for command in commands)
