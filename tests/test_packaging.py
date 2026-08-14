"""Regression for PR-OPS-001: the declared Python range must accept every
intended patch release. ``>=3.11,<=3.13`` silently rejected 3.13.1 and later
because, under PEP 440, ``3.13.1 > 3.13``.
"""

import tomllib
from email.message import EmailMessage
from importlib import util
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from packaging.specifiers import SpecifierSet

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"
CONDA_RECIPE = REPO_ROOT / "devtools" / "conda-build" / "meta.yaml"
RELEASE_CHECK = REPO_ROOT / "devtools" / "check_release.py"

SUPPORTED = ["3.11.0", "3.11.9", "3.12.0", "3.12.10", "3.13.0", "3.13.1", "3.13.14"]
UNSUPPORTED = ["3.9.18", "3.10.14", "3.14.0"]


def _requires_python():
    with open(PYPROJECT, "rb") as f:
        return SpecifierSet(tomllib.load(f)["project"]["requires-python"])


def _project_metadata():
    with open(PYPROJECT, "rb") as f:
        return tomllib.load(f)["project"]


def _release_module():
    spec = util.spec_from_file_location("check_release", RELEASE_CHECK)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("version", SUPPORTED)
def test_supported_python_versions_are_accepted(version):
    assert _requires_python().contains(version)


@pytest.mark.parametrize("version", UNSUPPORTED)
def test_unsupported_python_versions_are_rejected(version):
    assert not _requires_python().contains(version)


def test_conda_recipe_matches_pyproject_bound():
    # The recipe carries the same range in conda syntax; drift here reintroduces
    # PR-OPS-001 for conda users only.
    assert "python >=3.11,<3.14" in CONDA_RECIPE.read_text()


def test_conda_recipe_version_is_git_derived():
    # PR-REL-004 used to guard against a hand-copied literal drifting from
    # __init__.py. There is no literal any more: the version has one source, the
    # git tag. versioningit derives the package version and the recipe reads the
    # same tag through GIT_DESCRIBE_TAG, so drift is structurally impossible. This
    # asserts the recipe stays git-derived and no literal creeps back in.
    recipe = CONDA_RECIPE.read_text()
    assert "GIT_DESCRIBE_TAG" in recipe
    assert "set version" not in recipe


def test_pypi_metadata_identifies_an_autoloaded_pytest_plugin():
    project = _project_metadata()

    assert project["name"] == "pytest-receptor"
    assert "Framework :: Pytest" in project["classifiers"]
    assert project["entry-points"]["pytest11"] == {"receptor": "pytest_receptor.plugin"}
    assert project["urls"]["Issues"].endswith("/pytest-receptor/issues")
    assert project["urls"]["Changelog"].endswith("/CHANGELOG.md")
    assert project["license"] == "MIT"


def _release_files(tmp_path, requires_python=">=3.11,<3.14"):
    wheel = tmp_path / "pytest_receptor-1.0.0-py3-none-any.whl"
    metadata = EmailMessage()
    metadata["Metadata-Version"] = "2.4"
    metadata["Name"] = "pytest-receptor"
    metadata["Version"] = "1.0.0"
    metadata["Requires-Python"] = requires_python
    with ZipFile(wheel, "w", ZIP_DEFLATED) as archive:
        archive.writestr("pytest_receptor-1.0.0.dist-info/METADATA", bytes(metadata))
    (tmp_path / "pytest_receptor-1.0.0.tar.gz").touch()


def test_release_checker_accepts_exact_tag_and_python_support(tmp_path):
    _release_files(tmp_path)

    assert _release_module().validate_release(tmp_path, "1.0.0") == "1.0.0"
    assert _release_module().validate_release(tmp_path, "v1.0.0") == "1.0.0"


def test_release_checker_accepts_reordered_python_specifier(tmp_path):
    # packaging serializes an equivalent SpecifierSet in its own order; 26.2
    # emits `<3.14,>=3.11` from a `>=3.11,<3.14` declaration. The constraint is
    # identical, so the checker must accept it. An exact-text match did not, and
    # failed the real 1.0.0 release build.
    _release_files(tmp_path, requires_python="<3.14,>=3.11")

    assert _release_module().validate_release(tmp_path, "1.0.0") == "1.0.0"


@pytest.mark.parametrize("tag", ["1.0.1", "1.0.0+dirty", ""])
def test_release_checker_rejects_wrong_or_non_public_tag(tmp_path, tag):
    _release_files(tmp_path)

    with pytest.raises(ValueError):
        _release_module().validate_release(tmp_path, tag)


def test_release_checker_rejects_python_314_support_drift(tmp_path):
    _release_files(tmp_path, requires_python=">=3.11")

    with pytest.raises(ValueError, match="exactly Python 3.11-3.13"):
        _release_module().validate_release(tmp_path, "1.0.0")
