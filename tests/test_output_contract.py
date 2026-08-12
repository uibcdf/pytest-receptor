"""Golden tests for the pre-1.0 plain-text API."""

from __future__ import annotations

import re
from textwrap import dedent

import pytest

CASES = {
    "green": (
        "def test_a(): assert 1\ndef test_b(): assert 1\n",
        """
        PASS exit=0 | 2 passed | <duration>
        """,
    ),
    "single_failure": (
        "def test_ok(): assert 1\ndef test_bad(): assert 1 == 2\n",
        """
        FAIL exit=1 | 1 failed, 1 passed | <duration> | 1 root cause

        [1] AssertionError | 1 test | call
            test_contract.py:2
            assert 1 == 2
            rerun: pytest test_contract.py::test_bad -q
        """,
    ),
    "mixed_states": (
        "import pytest\n"
        "@pytest.mark.skip(reason='missing GPU')\n"
        "def test_skip(): pass\n"
        "@pytest.mark.xfail(reason='known defect')\n"
        "def test_xfail(): assert 0\n"
        "@pytest.mark.xfail(reason='fixed')\n"
        "def test_xpass(): assert 1\n"
        "def test_ok(): assert 1\n",
        """
        PASS exit=0 | 1 passed, 1 skipped, 1 xfailed, 1 xpassed | <duration>

        skipped: 1 in 1 group
          x1 | missing GPU

        xfailed: 1 in 1 group
          x1 | known defect

        unexpected passes:
          test_contract.py::test_xpass - fixed
        """,
    ),
}


def _stable_contract(text):
    return re.sub(r"\d+\.\d+s", "<duration>", text.lstrip()).rstrip() + "\n"


@pytest.mark.parametrize("case", CASES)
def test_compact_output_matches_golden_contract(pytester, case):
    """The output format is a public API; intentional changes update this."""
    source, expected = CASES[case]
    pytester.makepyfile(test_contract=source)
    result = pytester.runpytest("--receptor=llm", "-p", "no:cacheprovider")
    assert _stable_contract(result.stdout.str()) == dedent(expected).lstrip()
