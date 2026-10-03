"""Contract for the canonical guide synchronized into consumer repositories."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "standards/PYTEST_RECEPTOR_GUIDE.md"


def test_consumer_guide_has_owner_marker_and_operational_contract():
    text = GUIDE.read_text(encoding="utf-8")

    assert text.startswith(
        "<!--\nSYNCHRONIZED MOLSYSSUITE GUIDE — DO NOT EDIT COMPONENT COPIES.\n"
    )
    for expected in (
        "Canonical source: https://github.com/uibcdf/pytest-receptor/",
        "Report changes in: https://github.com/uibcdf/pytest-receptor/issues",
        "## Required consumer behavior",
        "## Choosing a profile",
        "`--receptor=llm`",
        "`--receptor=ci`",
        "`--receptor=human`",
        "## Exit status and authority",
        "never changes pytest's exit status",
        "## Evidence artifacts",
        "`--receptor-events=PATH`",
        "## When to use native pytest",
        "## Reporting missing or limiting behavior",
        "## Synchronization contract",
    ):
        assert expected in text


def test_owner_agent_guide_names_the_canonical_source():
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "standards/PYTEST_RECEPTOR_GUIDE.md" in agents


@pytest.mark.parametrize(
    "document",
    [
        "README.md",
        "docs/usage.md",
        "docs/channels.md",
        "standards/PYTEST_RECEPTOR_GUIDE.md",
    ],
)
def test_documented_full_report_path_matches_written_report(pytester, document):
    """PR-PILOT-006: following maintained guidance must locate real evidence."""
    text = (ROOT / document).read_text(encoding="utf-8")
    paths = re.findall(r"\.pytest_cache/[^\s`]+/last-run\.txt", text)
    assert paths, f"{document} must identify the full report destination"
    pytester.makepyfile("def test_ok(): assert True\n")
    result = pytester.runpytest("--receptor=llm")
    assert result.ret == pytest.ExitCode.OK
    for path in paths:
        report = pytester.path / path
        assert report.read_text(encoding="utf-8").startswith("PASS exit=0 | 1 passed")
