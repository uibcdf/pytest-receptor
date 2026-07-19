"""Measure receptor output cost against a fairly configured pytest.

The baseline matters more than the numbers. Comparing against pytest's *default*
output inflates every figure, because nobody driving pytest from an agent leaves
the header, the progress bar, and the source echo switched on. The honest
comparison is against a pytest that has already been told to be quiet, so this
script reports three baselines and lets the reader judge.

Run:  python devtools/benchmarks/run_benchmarks.py
      python devtools/benchmarks/run_benchmarks.py --scale

The scale scenarios model a real suite -- eight thousand tests under twelve
xdist workers -- because the small ones understate the saving badly. They take
a couple of minutes, so they are opt-in.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASELINES = {
    "pytest (default)": [],
    "pytest -q --no-header --tb=short": ["-q", "--no-header", "--tb=short"],
    "pytest -q --tb=line": ["-q", "--tb=line"],
}
RECEPTOR = ["--receptor=llm"]

# The baseline the published figures quote. Fair, and still readable by a human.
HONEST = "pytest -q --no-header --tb=short"

_WORDS = [
    f"{a}{b}" for a in "abcdefgh" for b in ("lpha", "eta", "amma", "elta", "psilon")
][:40]

SCENARIOS = {
    "Green suite (128 tests)": {
        "test_suite.py": (
            "import pytest\n"
            "@pytest.mark.parametrize('i', range(128))\n"
            "def test_ok(i): assert True\n"
        )
    },
    # The pilot found 216 warnings in 60 distinct groups on a real suite. A
    # scenario with a single repeated warning cannot detect a defect in how
    # many *kinds* are reported, and ours could not.
    "Green with many distinct warnings": {
        "test_suite.py": (
            "import warnings, pytest\n"
            "class W(UserWarning): pass\n"
            # Non-numeric variation on purpose. Numeric normalization -- added
            # after this scenario was written -- collapsed `condition 1` and
            # `condition 2` into one group, silently turning a forty-group
            # scenario back into the one-group scenario it was created to
            # replace, and taking this row from -64% to -97%.
            + "".join(
                f"def test_w{k}():\n"
                f"    warnings.warn('condition {_WORDS[k]} detected', W)\n"
                for k in range(40)
            )
        )
    },
    "Green with warnings": {
        "test_suite.py": (
            "import warnings, pytest\n"
            "@pytest.mark.parametrize('i', range(40))\n"
            "def test_ok(i):\n"
            "    warnings.warn('deprecated api', DeprecationWarning)\n"
            "    assert True\n"
        )
    },
    "Cascade (38 failures, one cause)": {
        "conftest.py": (
            "import pytest\n"
            "@pytest.fixture\n"
            "def topology():\n"
            "    raise TypeError(\"'NoneType' object is not subscriptable\")\n"
        ),
        "test_suite.py": (
            "import pytest\n"
            "@pytest.mark.parametrize('i', range(38))\n"
            "def test_merge(topology, i): assert True\n"
            "@pytest.mark.parametrize('i', range(90))\n"
            "def test_fine(i): assert True\n"
        ),
    },
    "Single assertion failure": {
        "test_suite.py": (
            "def test_diff():\n"
            "    expected = {'a': 1, 'b': [1, 2, 3], 'c': 'x'}\n"
            "    actual = {'a': 1, 'b': [1, 2, 4], 'c': 'y'}\n"
            "    assert actual == expected\n"
        )
    },
    "Five distinct causes": {
        "test_suite.py": (
            "def test_a(): raise ValueError('cause a')\n"
            "def test_b(): raise TypeError('cause b')\n"
            "def test_c(): raise KeyError('cause c')\n"
            "def test_d(): raise IndexError('cause d')\n"
            "def test_e(): raise RuntimeError('cause e')\n"
        )
    },
    "Collection error": {
        "test_suite.py": "import module_that_does_not_exist\ndef test_a(): pass\n"
    },
    "Mixed states (skip, xfail, xpass)": {
        "test_suite.py": (
            "import pytest\n"
            "@pytest.mark.skip(reason='not ready')\n"
            "def test_s(): pass\n"
            "@pytest.mark.xfail(reason='known bug')\n"
            "def test_x(): assert 0\n"
            "@pytest.mark.xfail(reason='fixed?')\n"
            "def test_xp(): assert 1\n"
            "def test_ok(): assert 1\n"
        )
    },
}


# Several families, so a savings claim is not an artifact of one vendor's
# tokenizer. Byte-pair vocabularies differ enough that the same text can vary by
# 30% between them.
TOKENIZERS = ["cl100k_base", "o200k_base", "p50k_base", "r50k_base"]


def _count_tokens(text):
    """Token counts per family, plus the headline family used in the table."""
    try:
        import tiktoken
    except ImportError:
        # Rough but stable, and it keeps the harness usable without the extra.
        approx = len(text) // 4
        return {"approx (4 chars/token)": approx}, "approx (4 chars/token)"
    counts = {}
    for name in TOKENIZERS:
        try:
            counts[name] = len(tiktoken.get_encoding(name).encode(text))
        except Exception:
            continue
    return counts, TOKENIZERS[0]


SCALE_TESTS = 8000
SCALE_BASELINE = "pytest -q -n 12"
SCALE_BASELINES = {
    "pytest -n 12": ["-n", "12"],
    SCALE_BASELINE: ["-q", "-n", "12"],
}
SCALE_RECEPTOR = ["--receptor=llm", "-n", "12"]

_CONFTEST = (
    "import pytest\n@pytest.fixture\ndef topology():\n"
    "    raise TypeError(\"'NoneType' object is not subscriptable\")\n"
)


def _scale_suite(passing, cascade=0, distinct=0):
    body = [
        "import pytest",
        f"@pytest.mark.parametrize('i', range({passing}))",
        "def test_ok(i): assert True",
    ]
    if cascade:
        body += [
            f"@pytest.mark.parametrize('i', range({cascade}))",
            "def test_merge(topology, i): assert True",
        ]
    body += [
        f"def test_distinct{i}(): raise ValueError('unrelated cause {i}')"
        for i in range(distinct)
    ]
    return {"conftest.py": _CONFTEST, "test_suite.py": "\n".join(body) + "\n"}


SCALE_SCENARIOS = {
    "Whole suite green": _scale_suite(SCALE_TESTS),
    "One fixture breaks 200 tests": _scale_suite(SCALE_TESTS - 200, cascade=200),
    "Six unrelated bugs": _scale_suite(SCALE_TESTS - 6, distinct=6),
}


# A measurement that changes with the caller's shell is not a measurement.
# `FORCE_COLOR` in the environment makes pytest emit ANSI even into a pipe, and
# with one escape pair per progress character an 8,000-test green run went from
# 9 kB to 82 kB -- inflating every baseline sevenfold and, incidentally, making
# the receptor look far better than it is. Colour is disabled explicitly so the
# numbers reproduce on anyone's machine.
_NEUTRAL_ENV = {"NO_COLOR": "1"}
_DROPPED_ENV = ("FORCE_COLOR", "PY_COLORS", "COLORTERM")


def _run(directory, args):
    env = {k: v for k, v in os.environ.items() if k not in _DROPPED_ENV}
    env.update(_NEUTRAL_ENV)
    process = subprocess.run(
        [sys.executable, "-m", "pytest", *args, "-p", "no:cacheprovider"],
        capture_output=True,
        text=True,
        cwd=directory,
        env=env,
    )
    return process.stdout


def measure(scenarios=None, baselines=None, receptor=None):
    scenarios = SCENARIOS if scenarios is None else scenarios
    baselines = BASELINES if baselines is None else baselines
    receptor = RECEPTOR if receptor is None else receptor
    results = {}
    encoding_name = None
    for scenario, files in scenarios.items():
        directory = Path(tempfile.mkdtemp(prefix="receptor-bench-"))
        try:
            for name, content in files.items():
                (directory / name).write_text(content, encoding="utf-8")
            row = {}
            for label, args in baselines.items():
                counts, encoding_name = _count_tokens(_run(directory, args))
                row[label] = counts
            counts, encoding_name = _count_tokens(_run(directory, receptor))
            row["--receptor=llm"] = counts
            results[scenario] = row
        finally:
            shutil.rmtree(directory, ignore_errors=True)
    return results, encoding_name


def _scale_report():
    results, encoding = measure(SCALE_SCENARIOS, SCALE_BASELINES, SCALE_RECEPTOR)
    print(f"Scale: {SCALE_TESTS} tests, twelve workers, `{encoding}`:")
    print()
    print(
        "| Scenario | "
        + " | ".join(SCALE_BASELINES)
        + " | `--receptor=llm -n 12` | Saving |"
    )
    print(
        "| :--- | " + " | ".join("---:" for _ in SCALE_BASELINES) + " | ---: | ---: |"
    )
    for scenario, row in results.items():
        mine = row["--receptor=llm"][encoding]
        base = row[SCALE_BASELINE][encoding]
        saving = (1 - mine / base) * 100 if base else 0.0
        cells = " | ".join(f"{row[label][encoding]:,}" for label in SCALE_BASELINES)
        print(f"| {scenario} | {cells} | **{mine:,}** | {saving:.1f}% |")
    print()


def main():
    import pytest

    import pytest_receptor

    if "--scale" in sys.argv:
        _scale_report()
        return

    results, encoding_name = measure()
    metadata = {
        "python": platform.python_version(),
        "pytest": pytest.__version__,
        "pytest_receptor": pytest_receptor.__version__,
        "tokenizer": encoding_name,
        "platform": platform.platform(),
        "baseline": HONEST,
    }

    head = encoding_name
    print("<!-- generated by devtools/benchmarks/run_benchmarks.py -->")
    print()
    print(f"Headline table, `{head}`:")
    print()
    print("| Scenario | " + " | ".join(BASELINES) + " | `--receptor=llm` | Change |")
    print("| :--- | " + " | ".join("---:" for _ in BASELINES) + " | ---: | ---: |")
    for scenario, row in results.items():
        receptor = row["--receptor=llm"][head]
        honest = row[HONEST][head]
        change = (receptor / honest - 1) * 100 if honest else 0.0
        cells = " | ".join(str(row[label][head]) for label in BASELINES)
        print(f"| {scenario} | {cells} | **{receptor}** | {change:+.1f}% |")
    print()

    families = sorted({name for row in results.values() for name in row[HONEST]})
    if len(families) > 1:
        print("Across tokenizer families, against `pytest` plain:")
        print()
        print("| Scenario | " + " | ".join(families) + " |")
        print("| :--- | " + " | ".join("---:" for _ in families) + " |")
        for scenario, row in results.items():
            cells = []
            for name in families:
                plain = row["pytest (default)"].get(name)
                mine = row["--receptor=llm"].get(name)
                cells.append(
                    f"{(mine / plain - 1) * 100:+.1f}%" if plain and mine else "-"
                )
            print(f"| {scenario} | " + " | ".join(cells) + " |")
        print()
    print("Environment:")
    print()
    for key, value in metadata.items():
        print(f"- {key}: {value}")

    Path(__file__).with_name("last-run.json").write_text(
        json.dumps({"metadata": metadata, "results": results}, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
