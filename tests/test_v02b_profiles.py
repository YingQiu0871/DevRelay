"""v0.2-B stage 4: project profile resolution, limits and precedence."""

from __future__ import annotations

import pytest

from devrelay.artifacts.store import sha256_file
from devrelay.errors import (
    ProfileCountExceededError,
    ProfileDuplicateError,
    ProfileKeyForbiddenError,
    ProfileNameInvalidError,
    ProfileNotFoundError,
    ProfileTooLargeError,
)
from devrelay.profiles import (
    MAX_PROFILE_BYTES,
    compose_policy,
    discover_profiles,
    load_profile,
    profile_path,
    resolve_policy_config,
    validate_profiles,
    validate_selector,
)
from devrelay.config import load_workspace_file

from helpers import (
    ScriptedAutoReviewer,
    build_engine,
    default_config,
    make_packet,
    make_review,
)

STATE = "DR-0001"


def _profile(root, name: str, body: str) -> None:
    directory = root / ".devrelay" / "profiles"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{name}.yaml").write_text(body, encoding="utf-8")


def _config(root, body: str) -> None:
    path = root / ".devrelay" / "config.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _workspace(tmp_path):
    root, store, engine = build_engine(tmp_path)
    return root, store, engine


# ---------------------------------------------------------------------------
# precedence + provenance
# ---------------------------------------------------------------------------
def test_precedence_defaults_profiles_overrides(tmp_path):
    root, _store, _engine = _workspace(tmp_path)
    _profile(root, "base", "budget:\n  max_reviewer_calls: 3\n")
    _profile(
        root,
        "python",
        "budget:\n  max_reviewer_calls: 2\n  max_implementer_calls: 6\n"
        "tests:\n  targeted: ['pytest -q tests/test_x.py']\n",
    )
    _config(
        root,
        "profiles: [base, python]\nbudget:\n  max_total_provider_calls: 7\n",
    )
    policy = resolve_policy_config(root)
    document = policy.document

    assert document.budget.max_reviewer_calls == 2  # later profile wins
    assert document.budget.max_implementer_calls == 6
    assert document.budget.max_total_provider_calls == 7  # workspace override wins
    assert document.pipeline.max_fix_iterations == 3  # packaged default
    assert document.tests.targeted == ["pytest -q tests/test_x.py"]

    assert policy.provenance.selector_raw == ["base", "python"]
    assert [ref.name for ref in policy.provenance.profiles] == ["base", "python"]
    assert all(len(ref.sha256) == 64 for ref in policy.provenance.profiles)
    assert policy.provenance.workspace_config_sha256 == sha256_file(
        root / ".devrelay" / "config.yaml"
    )


def test_lists_replace_wholesale(tmp_path):
    root, _store, _engine = _workspace(tmp_path)
    _profile(root, "a", "review:\n  blocking_severities: [P0]\n")
    _profile(root, "b", "review:\n  blocking_severities: [P1, P2]\n")
    _config(root, "profiles: [a, b]\n")
    policy = resolve_policy_config(root)
    assert [s.value for s in policy.document.review.blocking_severities] == ["P1", "P2"]


def test_no_profiles_keeps_packaged_defaults(tmp_path):
    root, _store, _engine = _workspace(tmp_path)
    _config(root, "# nothing selected\n")
    policy = resolve_policy_config(root)
    assert policy.document.budget.max_reviewer_calls == 4
    assert policy.provenance.selector_raw == []


# ---------------------------------------------------------------------------
# schema rules: policy only, one name grammar, hard limits
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "body",
    [
        "git:\n  allow_push: false\n",
        "codex:\n  executable: codex\n",
        "review:\n  provider: openai_compatible\n",
        "profiles: [base]\n",
        "endpoint: https://example.test\n",
        "api_key: sk-not-a-real-key\n",
        "extends: base\n",
    ],
)
def test_profiles_may_only_set_policy(tmp_path, body):
    root, _store, _engine = _workspace(tmp_path)
    _profile(root, "bad", body)
    _config(root, "profiles: [bad]\n")
    with pytest.raises(ProfileKeyForbiddenError):
        resolve_policy_config(root)
    with pytest.raises(ProfileKeyForbiddenError):
        load_profile(root, "bad")


def test_profile_name_grammar_is_single_sourced(tmp_path):
    root, _store, _engine = _workspace(tmp_path)
    for name in ("Base", "base.yaml", "../evil", "a" * 65, "-lead", ""):
        with pytest.raises(ProfileNameInvalidError):
            profile_path(root, name)
    assert profile_path(root, "base-2_x").name == "base-2_x.yaml"


def test_selector_limits_and_duplicates(tmp_path):
    root, _store, _engine = _workspace(tmp_path)
    with pytest.raises(ProfileCountExceededError):
        validate_selector([f"p{i}" for i in range(9)])
    with pytest.raises(ProfileDuplicateError):
        validate_selector(["base", "base"])
    with pytest.raises(ProfileNameInvalidError):
        validate_selector(["Base"])
    validate_selector([f"p{i}" for i in range(8)])


def test_missing_profile_and_oversized_file_fail_closed(tmp_path):
    root, _store, _engine = _workspace(tmp_path)
    _config(root, "profiles: [ghost]\n")
    with pytest.raises(ProfileNotFoundError):
        resolve_policy_config(root)

    _profile(root, "huge", "pipeline:\n  max_fix_iterations: 3\n")
    path = profile_path(root, "huge")
    path.write_bytes(b"# " + b"x" * (MAX_PROFILE_BYTES + 1))
    _config(root, "profiles: [huge]\n")
    with pytest.raises(ProfileTooLargeError):
        resolve_policy_config(root)


def test_raw_inspection_survives_a_broken_selector(tmp_path):
    root, _store, _engine = _workspace(tmp_path)
    _profile(root, "valid", "budget:\n  max_reviewer_calls: 2\n")
    _profile(root, "Base", "budget:\n  max_reviewer_calls: 2\n")  # invalid filename
    _config(root, "profiles: [missing, valid]\n")

    names, invalid = discover_profiles(root)
    assert names == ["valid"]
    assert invalid == ["Base.yaml"]
    assert load_profile(root, "valid")[0].budget.max_reviewer_calls == 2

    report = validate_profiles(root)
    assert not report.ok
    # Every problem is reported, not just the first missing reference.
    assert any("Base.yaml" in error for error in report.errors)
    assert any("missing" in error for error in report.errors)
    assert any(entry.name == "valid" and entry.ok for entry in report.entries)


def test_compose_ignores_selector_and_wiring_in_workspace_config(tmp_path):
    root, _store, _engine = _workspace(tmp_path)
    _profile(root, "base", "budget:\n  max_reviewer_calls: 2\n")
    _config(
        root,
        "profiles: [base]\nreview:\n  provider: manual\ncodex:\n  executable: codex\n",
    )
    workspace = load_workspace_file(root / ".devrelay" / "config.yaml")
    document, refs = compose_policy(root, workspace)
    assert document.budget.max_reviewer_calls == 2
    assert [ref.name for ref in refs] == ["base"]
    assert "profiles" not in document.model_dump()


# ---------------------------------------------------------------------------
# frozen tasks: profile provenance is recorded, execution reads no profile
# ---------------------------------------------------------------------------
def test_frozen_task_records_profile_provenance_and_ignores_later_edits(tmp_path):
    root, _store, _engine = _workspace(tmp_path)
    _profile(root, "base", "budget:\n  max_reviewer_calls: 2\n")
    _config(root, "profiles: [base]\n")
    policy = resolve_policy_config(root)

    _root, store, engine = build_engine(
        tmp_path,
        fallback_policy_config=policy,
        reviewer=ScriptedAutoReviewer([make_review("PASS")]),
    )
    engine.create_task("t")
    task = store.read_task(STATE)

    from devrelay.snapshot import snapshot_path

    snapshot_text = snapshot_path(store, STATE).read_text(encoding="utf-8")
    assert "profiles" not in snapshot_text
    assert task.policy_provenance is not None
    assert task.policy_provenance.selector_raw == ["base"]
    assert [ref.name for ref in task.policy_provenance.profiles] == ["base"]
    assert task.policy_provenance.workspace_config_sha256 != ""
    assert engine._task_config(task).budget.max_reviewer_calls == 2

    # The live chain is now irrelevant to this task: the profile is edited and
    # then deleted, and the live policy override becomes malformed.
    _profile(root, "base", "budget:\n  max_reviewer_calls: 9\n")
    (root / ".devrelay" / "profiles" / "base.yaml").unlink()
    _config(root, 'budget:\n  max_total_provider_calls: "THIS IS NOT AN INTEGER"\n')

    engine.import_plan(STATE, make_packet(task_id=STATE))
    engine.continue_task(STATE)
    after = store.read_task(STATE)
    assert after.state.value in ("REVIEWING", "FINAL_GATE_REQUIRED")
    assert engine._task_config(after).budget.max_reviewer_calls == 2
    assert after.policy_provenance.selector_raw == ["base"]


def test_new_task_fails_closed_on_a_broken_live_policy(tmp_path):
    root, _store, _engine = _workspace(tmp_path)
    _config(root, 'budget:\n  max_total_provider_calls: "THIS IS NOT AN INTEGER"\n')
    with pytest.raises(Exception) as excinfo:
        resolve_policy_config(root)
    assert "invalid" in str(excinfo.value).lower()
