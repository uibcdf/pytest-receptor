"""Contract for the canonical guide synchronized into consumer repositories."""

from pathlib import Path

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
