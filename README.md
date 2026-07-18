# pytest-receptor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![Pytest Version](https://img.shields.io/badge/pytest-%3E%3D8.0.0-green)](https://docs.pytest.org/)

A pytest reporter for coding agents.

When pytest is driven by an agent such as Claude Code, Codex, or an autonomous
TDD loop, its output is read by something that pays for every token and cannot
scroll back. `pytest-receptor` renders the same run for that consumer: it says
what happened, groups repeated failures by root cause, and tells the agent
exactly what to re-run.

> **Status: pre-1.0.** The output format is this plugin's public API and it may
> still change. What will not change is the reliability floor: the receptor
> never reports an unsuccessful or incomplete run as a success, and a failure
> inside the receptor itself never costs you the run.

---

## The problem

Your agent was told to run the tests, so it runs `pytest`, and pytest answers
the way it has always answered: for a human sitting at a terminal. Banner,
`rootdir`, plugin list, progress bar, and the full source of every failing test.
The agent pays for all of it, on every iteration.

Tuning the flags does not fix it. `pytest -q --tb=line` is compact but strips
the assertion diff, so the agent guesses and loops. And nothing pytest offers
handles the case that hurts most: one broken fixture fails forty tests, and the
agent reads the same traceback forty times.

## What it does

```console
$ pytest --receptor=llm

FAIL exit=1 | 38 failed, 90 passed | 2.41s | 1 root cause

[1] TypeError | 38 tests | setup
    conftest.py:4
    TypeError: 'NoneType' object is not subscriptable
    tests:
      tests/test_merge.py::test_merge[0]
      tests/test_merge.py::test_merge[1]
      tests/test_merge.py::test_merge[2]
      +35 more
    rerun: pytest tests/test_merge.py -q
```

That is 101 tokens. Plain `pytest` spends 3,279 on the same run.

---

## Install

```bash
pip install pytest-receptor
```

Requires Python 3.11-3.13 and pytest 8 or later.

## Use

```bash
pytest --receptor=llm     # compact output for a coding agent
pytest --receptor=ci      # compact output for a CI log
pytest --receptor=human   # unchanged pytest (the default)
pytest --receptor=llm --receptor-full   # expand every failure group
pytest --receptor=llm --receptor-stats  # what did this actually save?
```

`human` is a true passthrough: the plugin registers nothing and the output is
byte-identical to pytest without it installed.

---

## Behavior

### It always tells you what actually happened

The verdict comes from pytest's exit status, never from the absence of failure
reports:

```text
PASS exit=0 | 126 passed, 2 skipped | 4.21s | 3 warnings
FAIL exit=1 | 2 failed, 87 passed | 12.40s | 2 root causes
NO_TESTS exit=5
INTERRUPTED exit=2 | incomplete: 12 of 128 executed
COLLECTION_ERROR exit=2
```

A run stopped by `-x`, `--maxfail`, or an interrupt is marked incomplete even
when nothing failed, so a partial run cannot be mistaken for a clean one.

### It groups by root cause, not by test

Failures are grouped by exception, phase, message, and call site. Forty tests
broken by one fixture become one group that keeps all forty test IDs. Equal
messages raised from unrelated places stay separate, because they are different
bugs.

### It holds back what you do not need yet

An agent fixes one cause at a time, so `llm` expands the first three root causes
in full and gives the rest one line each. Nothing is lost: the complete report is
written to `.pytest_cache/receptor/last-run.txt` during the run, so recovering it
is a file read rather than another full test run.

The `ci` profile expands everything instead, because a CI runner is destroyed
when the job ends and that file will not be there when someone reads the log.

### It degrades safely

If the receptor itself raises, you get `RECEPTOR_ERROR`, the underlying
exception, the raw pytest evidence, and pytest's original exit status. The worst
case of enabling this plugin is standard pytest plus one line of noise.

Test output is treated as untrusted input: ANSI escapes and control characters
are stripped, and no text produced by a test can forge a verdict line.

---

## What your agent is doing right now

Your agent runs `pytest`. Plain, because that is the obvious command and nobody
told it otherwise. So every test run spends tokens on a platform banner, a
`rootdir` line, a plugin list, a progress bar, and the source code of every
failing test — none of which the agent needs, all of which you pay for, on every
iteration of every loop.

Measured with `tiktoken` (`cl100k_base`):

| Scenario | `pytest` | `--receptor=llm` | Change |
| :--- | ---: | ---: | ---: |
| Cascade (38 failures, one cause) | 3279 | **101** | **-96.9%** |
| Green with warnings | 167 | **20** | -88.0% |
| Green suite (128 tests) | 97 | **16** | -83.5% |
| Mixed states (skip, xfail, xpass) | 103 | **44** | -57.3% |
| Five distinct causes | 385 | **181** | -53.0% |
| Single assertion failure | 331 | **162** | -51.1% |
| Collection error | 273 | **215** | -21.2% |

Every scenario is cheaper, most of them by half or better. In a TDD loop that
runs the suite twenty times, the cascade row alone is sixty thousand tokens.

### And if you already tuned pytest

If you are the kind of person who already runs `pytest -q --no-header
--tb=short`, the picture is narrower and you deserve to see that too:

| Scenario | tuned pytest | `--receptor=llm` | Change |
| :--- | ---: | ---: | ---: |
| Cascade (38 failures, one cause) | 2863 | **101** | -96.5% |
| Green with warnings | 93 | **20** | -78.5% |
| Five distinct causes | 316 | **181** | -42.7% |
| Green suite (128 tests) | 23 | **16** | -30.4% |
| Single assertion failure | 197 | **162** | -17.8% |
| Collection error | 198 | **215** | +8.6% |
| Mixed states (skip, xfail, xpass) | 31 | **44** | +41.9% |

The two positive rows are real, and they are thirteen and seventeen tokens. They
buy the difference between `1 xpassed` and knowing *which* test passed
unexpectedly and why — which is the thing you would otherwise have re-run pytest
to discover.

The cascade row does not move: grouping forty failures into one root cause is
something no combination of pytest flags does.

### Measure it on your own suite

```bash
pytest --receptor=llm --receptor-stats
```

```text
receptor stats: 38 tokens vs 148 for pytest as you configured it | 110 fewer (-74.3%) | cl100k_base
```

The baseline here is *your* pytest configuration, not the strict one used in the
table above, because the question this answers is personal: against how you
actually run pytest, what does this save you? It is measured rather than
estimated — pytest genuinely renders into a temporary file during the same run,
which is then tokenized and deleted. No second invocation, no extra memory, and
your own output is unaffected.

Reproduce the table above with `python devtools/benchmarks/run_benchmarks.py`.

---

## Documentation

Full documentation: [uibcdf.github.io/pytest-receptor](https://uibcdf.github.io/pytest-receptor/)

Design notes, the audit that shaped the current scope, and the open work queue
live in [`devguide/`](devguide/README.md).

## License

MIT. See [LICENSE](LICENSE).
