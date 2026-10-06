import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "devtools" / "conda-build" / "meta.yaml"
WORKFLOW = ROOT / ".github" / "workflows" / "build_and_upload_conda_packages.yaml"
PROMOTION_WORKFLOW = ROOT / ".github" / "workflows" / "promote_conda_package.yaml"
RECEPTOR_CONFIG = ROOT / ".github" / "gh-run-receptor.yaml"
PLAN = ROOT / "devtools" / "conda-build" / "release_plan.toml"
INVENTORY = ROOT / "devtools" / "conda-build" / "resources.toml"
INSTALLED_WORKFLOW = ROOT / ".github" / "workflows" / "test_installed_conda.yaml"


def test_recipe_declares_one_supported_noarch_python_artifact():
    recipe = RECIPE.read_text(encoding="utf-8")

    assert "noarch: python" in recipe
    assert recipe.count("python >=3.11,<3.15") == 2
    assert "MOLSYSSUITE_CONDA_BUILD_NUMBER" in recipe


def test_recipe_checks_installed_and_imported_versions():
    recipe = RECIPE.read_text(encoding="utf-8")

    assert "md.version('pytest-receptor') == expected" in recipe
    assert "pytest_receptor.__version__ == expected" in recipe


def test_manual_candidates_are_exact_and_staging_only():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    plan = tomllib.loads(PLAN.read_text())

    assert "candidate_sha:" in workflow
    assert "candidate_sha: ${{ inputs.candidate_sha }}" in workflow
    assert "version: ${{ inputs.version }}" in workflow
    assert re.search(r"publish-noarch-conda.yaml@[0-9a-f]{40}\b", workflow)
    assert "ANACONDA_TOKEN: ${{ secrets.ANACONDA_UIBCDF_TOKEN }}" in workflow
    assert "release:" not in workflow
    assert plan["route"] == "staged"
    assert plan["requires_installed_gate"] is True


def test_installed_gate_declares_the_complete_reviewed_matrix_and_test_selection():
    plan = tomllib.loads(PLAN.read_text())
    inventory = tomllib.loads(INVENTORY.read_text())
    workflow = INSTALLED_WORKFLOW.read_text()
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())

    gate = inventory["installed_gate"]
    assert gate["platforms"] == plan["test_platforms"]
    assert gate["python_versions"] == plan["python_versions"]
    assert inventory["installed_tests"]["paths"] == ["tests"]
    assert "ref: ${{ inputs.candidate_sha }}" in workflow
    assert '--candidate-sha "$CANDIDATE_SHA"' in workflow
    assert '--qualification-sha "$QUALIFICATION_SHA"' in workflow
    assert (
        "installed-source-binding-${{ github.run_id }}-${{ github.run_attempt }}"
        in workflow
    )
    assert "PYTHONSAFEPATH: '1'" in workflow
    assert "PYTHONPATH: ${{ github.workspace }}/component/devtools" in workflow
    assert "PYTHONPATH: ${{ github.workspace }}/component\n" not in workflow
    for requirement in project["project"]["optional-dependencies"]["test"]:
        assert requirement in workflow


def test_publication_promotes_one_exact_staged_digest_without_rebuilding():
    workflow = PROMOTION_WORKFLOW.read_text(encoding="utf-8")

    assert "candidate_sha:" in workflow
    assert "sha256:" in workflow
    assert "installed_run_id: ${{ inputs.installed_run_id }}" in workflow
    assert "qualification_sha: ${{ inputs.qualification_sha }}" in workflow
    assert re.search(r"promote-noarch-conda.yaml@[0-9a-f]{40}\b", workflow)
    assert "--force" not in workflow
    assert "python -m build" not in workflow
    assert "conda build" not in workflow


def test_gh_run_receptor_treats_the_workflow_as_noarch_conda():
    config = RECEPTOR_CONFIG.read_text(encoding="utf-8")

    assert "path: .github/workflows/build_and_upload_conda_packages.yaml" in config
    assert "path: .github/workflows/promote_conda_package.yaml" in config
    assert "profile: conda" in config
    assert "package_kind: noarch" in config
    assert "profile: release" in config
