from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "devtools" / "conda-build" / "meta.yaml"
WORKFLOW = ROOT / ".github" / "workflows" / "build_and_upload_conda_packages.yaml"
RECEPTOR_CONFIG = ROOT / ".github" / "gh-run-receptor.yaml"


def test_recipe_declares_one_supported_noarch_python_artifact():
    recipe = RECIPE.read_text(encoding="utf-8")

    assert "noarch: python" in recipe
    assert recipe.count("python >=3.11,<3.15") == 2
    assert "PYTEST_RECEPTOR_CONDA_BUILD_NUMBER" in recipe


def test_recipe_checks_installed_and_imported_versions():
    recipe = RECIPE.read_text(encoding="utf-8")

    assert "md.version('pytest-receptor') == expected" in recipe
    assert "pytest_receptor.__version__ == expected" in recipe


def test_manual_candidates_are_exact_and_staging_only():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "candidate_sha:" in workflow
    assert (
        "ref: ${{ inputs.candidate_sha || github.event.release.tag_name }}" in workflow
    )
    assert 'test "$(git rev-parse HEAD)" = "$CANDIDATE_SHA"' in workflow
    assert "Build, test, and upload the staging candidate" in workflow
    assert "label: staging" in workflow


def test_noarch_workflow_has_one_job_and_retains_producer_evidence():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "matrix:" not in workflow
    assert "@v2.1.0" in workflow
    assert "--python" not in workflow
    assert "platform_linux-64: false" in workflow
    assert "platform_win-64: false" in workflow
    assert "always() && steps.conda_staging.outputs.evidence_path != ''" in workflow
    assert "always() && steps.conda_release.outputs.evidence_path != ''" in workflow


def test_gh_run_receptor_treats_the_workflow_as_noarch_conda():
    config = RECEPTOR_CONFIG.read_text(encoding="utf-8")

    assert "path: .github/workflows/build_and_upload_conda_packages.yaml" in config
    assert "profile: conda" in config
    assert "package_kind: noarch" in config
