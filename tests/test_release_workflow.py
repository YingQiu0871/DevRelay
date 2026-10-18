"""Static validation of the PyPI Trusted Publishing workflows.

The release workflow finishes a hand-made draft Release: it validates the
dispatch tag, builds the distributions from that tag's own source, attaches the
wheel, the sdist and SHA256SUMS to the draft, uploads the distributions to PyPI
and only then flips the draft to a published Release.

These tests read the real workflow files and fail if that contract erodes: if
the draft gate turns back into a "must already be published" gate, if a checksum
file is written into dist/ where ``twine check`` would trip over it, if a rerun
rebuilds a version PyPI already has, or if the Release can become visible before
its assets exist.  They also keep the test CI running the suite on both
supported operating systems.
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
TAG_PATTERN = r"^v[0-9]+\.[0-9]+\.[0-9]+$"
SKIP_WHEN_PUBLISHED = "steps.pypi.outputs.exists != 'true'"


def _load() -> tuple[dict, dict]:
    data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    # PyYAML (YAML 1.1) parses the bare key ``on`` as boolean True.
    triggers = data.get("on", data.get(True))
    return data, triggers


def _publish_job() -> dict:
    data, _ = _load()
    return data["jobs"]["publish"]


def _steps() -> list[dict]:
    return _publish_job()["steps"]


def _text() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def _step_index(needle: str) -> int:
    """Index of the single step whose ``run:`` text contains *needle*."""
    for index, step in enumerate(_steps()):
        if needle in (step.get("run") or ""):
            return index
    raise AssertionError(f"no publish step whose run text contains {needle!r}")


def _step_run(needle: str) -> str:
    return _steps()[_step_index(needle)]["run"]


def _uses_index(fragment: str) -> int:
    """Index of the single step whose ``uses:`` contains *fragment*."""
    for index, step in enumerate(_steps()):
        if fragment in str(step.get("uses", "")):
            return index
    raise AssertionError(f"no publish step using {fragment!r}")


def _extract_pycode(run_text: str) -> str:
    """Return the Python source of the ``PYCODE='...'`` block of a step."""
    lines = run_text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "PYCODE='")
    base = len(lines[start]) - len(lines[start].lstrip())
    body: list[str] = []
    for line in lines[start + 1 :]:
        if line.strip() == "'":
            break
        body.append(line[base:])
    return "\n".join(body)


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
    assert "pull_request_target" not in _text()


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


def test_job_permissions_are_limited_to_what_the_upload_and_oidc_need():
    # `contents: write` is required to attach the built distributions to the
    # Release and to publish it; `id-token: write` is required for OIDC.
    # Nothing else may be granted, at any scope.
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
    for step in _steps():
        run_text = step.get("run") or ""
        assert not re.search(r"\$\{\{\s*inputs\.", run_text), (
            f"step {step.get('name')!r} interpolates an input into shell text"
        )


def test_checkout_uses_the_requested_tag():
    checkout = _steps()[_uses_index("actions/checkout")]
    assert checkout["with"]["ref"] == "${{ inputs.tag }}"
    assert checkout["with"]["fetch-depth"] == 0


def test_tag_shape_is_validated_first_so_it_needs_no_checkout():
    run = _step_run(TAG_PATTERN)
    assert _step_index(TAG_PATTERN) == 0
    assert _step_index(TAG_PATTERN) < _uses_index("actions/checkout")
    assert "exit 1" in run
    step = _steps()[0]
    assert step["env"]["TAG"] == "${{ inputs.tag }}"


def test_tag_must_match_the_version_in_pyproject():
    text = _text()
    assert "tomllib" in text
    assert '"pyproject.toml"' in text
    assert '"project"' in text and '"version"' in text
    assert 'tag == f"v{version}"' in text

    step = _steps()[_step_index('tag == f"v{version}"')]
    assert step["id"] == "version"
    assert step["env"]["TAG"] == "${{ inputs.tag }}"
    assert 'echo "version=$version"' in step["run"]
    assert "$GITHUB_OUTPUT" in step["run"]


def test_tag_must_be_reachable_from_origin_main():
    text = _text()
    assert "git fetch --no-tags origin main" in text
    assert "git merge-base --is-ancestor" in text


def test_requires_a_draft_release_not_a_published_one():
    run = _step_run("--json isDraft,isPrerelease")
    assert ".isDraft" in run
    assert 'if [ "$state" != "draft" ]' in run
    # The gate must demand the *draft* state; accepting an already published
    # Release is exactly the regression this test exists for.
    assert '"not-a-draft"' in run
    assert '"ok"' not in run
    assert 'else "ok" end' not in _text()
    # ...and the failure has to say how to get there.
    assert "gh release create" in run
    assert "--draft" in run
    assert "draft" in run.lower()
    assert "Release" in run
    assert "exit 1" in run


def test_pypi_existence_probe_is_fail_closed():
    probe = _steps()[_step_index("curl -sS --retry 3")]
    run = probe["run"]
    assert probe["id"] == "pypi"
    assert probe["env"]["VERSION"] == "${{ steps.version.outputs.version }}"
    assert 'https://pypi.org/pypi/devrelay/${VERSION}/json' in run
    assert "%{http_code}" in run
    assert "200)" in run and "404)" in run
    assert "exists=true" in run and "exists=false" in run
    assert 'echo "exists=$exists" >> "$GITHUB_OUTPUT"' in run
    # Any other answer (network failure, 5xx, a proxy error page) must stop the
    # run rather than be read as "not published yet".
    assert run.count("exit 1") >= 1


def test_build_and_publish_steps_are_skipped_when_the_version_is_on_pypi():
    steps = _steps()
    guarded = [
        _step_index("python -m build --outdir dist"),
        _step_index("mkdir -p release-assets"),
        _step_index("python -m twine check"),
        _step_index("gh release upload"),
        _uses_index(PUBLISH_ACTION),
    ]
    assert len(set(guarded)) == len(guarded)
    for index in guarded:
        assert steps[index]["if"] == SKIP_WHEN_PUBLISHED, steps[index].get("name")
    # The probe and the final Release flip are unconditional: the first one has
    # to answer the question, the second one has to finish a rerun.
    assert "if" not in steps[_step_index("%{http_code}")]
    assert "if" not in steps[-1]


def test_checksums_are_written_outside_dist():
    text = _text()
    step = _steps()[_step_index("mkdir -p release-assets")]
    run = step["run"]
    assert "release-assets/SHA256SUMS" in text
    assert "mkdir -p release-assets" in run
    assert 'assets = pathlib.Path("release-assets")' in run
    assert '"SHA256SUMS"' in run and ".write_text(" in run
    write_line = next(line for line in run.splitlines() if ".write_text(" in line)
    assert "assets" in write_line and "dist" not in write_line
    # A checksum file inside dist/ is what makes `twine check dist/*` fail.
    assert not re.search(r'dist\s*/\s*"SHA256SUMS"', text)


def test_twine_check_names_only_distributions():
    run = _step_run("python -m twine check")
    assert "python -m twine check dist/*.whl dist/*.tar.gz" in run
    assert not re.search(r"twine check\s+dist/\*(?!\.)", run)


def test_assets_are_attached_to_the_draft_before_the_pypi_upload():
    steps = _steps()
    upload_index = _step_index("gh release upload")
    publish_index = _uses_index(PUBLISH_ACTION)
    assert upload_index < publish_index
    run = steps[upload_index]["run"]
    assert "dist/*.whl" in run and "dist/*.tar.gz" in run
    assert "release-assets/SHA256SUMS" in run
    assert "--clobber" in run
    assert steps[publish_index]["with"]["packages-dir"] == "dist/"
    # `--clobber` belongs to the asset upload only.
    assert sum("--clobber" in (step.get("run") or "") for step in steps) == 1


def test_builds_from_source_instead_of_downloading_artifacts():
    text = _text()
    assert "python -m build --outdir dist" in text
    assert "gh release download" not in text


def test_build_and_twine_are_pinned_to_exact_versions():
    installs = [
        line
        for line in _step_run("python -m build --outdir dist").splitlines()
        if "pip install" in line
    ]
    assert len(installs) == 1
    assert installs[0].count("==") == 2
    assert re.search(r'"build==\d+(?:\.\d+)+"', installs[0])
    assert re.search(r'"twine==\d+(?:\.\d+)+"', installs[0])


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
    code_steps = [step for step in _steps() if "PYCODE='" in (step.get("run") or "")]
    assert len(code_steps) == 2
    for step in code_steps:
        compile(_extract_pycode(step["run"]), step["name"], "exec")
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


def test_the_final_step_publishes_the_release_only_after_checking_its_assets():
    steps = _steps()
    final = steps[-1]
    run = final["run"]
    assert "if" not in final
    assert "--json assets" in run
    assert ".assets[].name" in run
    assert "devrelay-${VERSION}-py3-none-any.whl" in run
    assert "devrelay-${VERSION}.tar.gz" in run
    assert "SHA256SUMS" in run
    assert "exit 1" in run
    assert run.index("--json assets") < run.index("gh release edit")
    assert "--draft=false" in run
    assert "--clobber" not in run
    assert sum("gh release edit" in (step.get("run") or "") for step in steps) == 1


def test_the_guarded_stage_order_is_fixed():
    order = [
        _step_index(TAG_PATTERN),
        _uses_index("actions/checkout"),
        _uses_index("actions/setup-python"),
        _step_index("tomllib"),
        _step_index("git merge-base --is-ancestor"),
        _step_index("--json isDraft,isPrerelease"),
        _step_index("%{http_code}"),
        _step_index("python -m build --outdir dist"),
        _step_index("mkdir -p release-assets"),
        _step_index("python -m twine check"),
        _step_index("gh release upload"),
        _uses_index(PUBLISH_ACTION),
        _step_index("gh release edit"),
    ]
    assert len(set(order)) == len(order)
    assert order == sorted(order)


def test_test_workflow_runs_the_suite_on_both_platforms():
    data = yaml.safe_load(TEST_WORKFLOW_PATH.read_text(encoding="utf-8"))
    triggers = data.get("on", data.get(True))
    assert set(triggers) == {"push", "pull_request"}
    assert triggers["push"]["branches"] == ["main", "v0.3-*", "release/*"]
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
