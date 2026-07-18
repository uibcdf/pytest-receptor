"""Regression for PR-OPS-001: the declared Python range must accept every
intended patch release. ``>=3.11,<=3.13`` silently rejected 3.13.1 and later
because, under PEP 440, ``3.13.1 > 3.13``.
"""

import tomllib
from pathlib import Path

import pytest
from packaging.specifiers import SpecifierSet

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"
CONDA_RECIPE = REPO_ROOT / "devtools" / "conda-build" / "meta.yaml"

SUPPORTED = ["3.11.0", "3.11.9", "3.12.0", "3.12.10", "3.13.0", "3.13.1", "3.13.14"]
UNSUPPORTED = ["3.9.18", "3.10.14", "3.14.0"]


def _requires_python():
    with open(PYPROJECT, "rb") as f:
        return SpecifierSet(tomllib.load(f)["project"]["requires-python"])


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


def test_conda_recipe_version_matches_package():
    # PR-REL-004: the version lives in __init__.py, but the recipe needs a
    # literal. This is the only guard against the two drifting apart, as they
    # already did once (0.1.0 vs 0.1.1).
    import pytest_receptor

    assert f'{{% set version = "{pytest_receptor.__version__}" %}}' in (
        CONDA_RECIPE.read_text()
    )
