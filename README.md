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

`pytest -q --tb=line` is compact but strips the assertion diff, so the agent
guesses. Default pytest keeps the diff but spends thousands of tokens on
headers, progress bars, and source code the agent already has indexed. Neither
handles the common case where one broken fixture fails forty tests and the agent
reads the same traceback forty times.

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

That is 101 tokens where a fairly configured pytest spends 2,863.

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

## Token cost, measured honestly

Measured with `tiktoken` (`cl100k_base`) against **`pytest -q --no-header
--tb=short`** — a pytest that has already been told to be quiet. Comparing
against pytest's chatty default would roughly double every figure below and
would not tell you anything useful.

| Scenario | quiet pytest | `--receptor=llm` | Saving |
| :--- | ---: | ---: | ---: |
| Cascade (38 failures, one cause) | 2863 | **101** | 96.5% |
| Green with warnings | 93 | **20** | 78.5% |
| Five distinct causes | 316 | **181** | 42.7% |
| Green suite (128 tests) | 23 | **16** | 30.4% |
| Single assertion failure | 197 | **162** | 17.8% |
| Collection error | 198 | **215** | -8.6% |
| Mixed states (skip, xfail, xpass) | 31 | **44** | -41.9% |

**The last two rows are not typos**, but read them in absolute terms: -41.9%
there is *twelve tokens*. On small, simple runs the receptor costs about the
same as quiet pytest, occasionally a handful more, because it spends those
tokens on things pytest omits — naming the tests that passed unexpectedly,
stating the exit status, giving you a rerun command.

So the question is not really whether to turn it on. Turning it on is close to
free in the worst measured case and saves 96% in the best one. The question is
how much it will help *your* suite, which depends entirely on how your failures
cluster.

### Measure it on your own suite

```bash
pytest --receptor=llm --receptor-stats
```

```text
receptor stats: 100 tokens vs 3205 for `pytest -q --no-header --tb=auto` | saved 3105 (+96.9%) | cl100k_base
```

That baseline is not an estimate. pytest genuinely renders its quiet output
during the same run, into a temporary file, and the bytes are counted. Nothing
extra is held in memory and your own output is unaffected.

Reproduce the table above with `python devtools/benchmarks/run_benchmarks.py`.

---

## Documentation

Full documentation: [uibcdf.github.io/pytest-receptor](https://uibcdf.github.io/pytest-receptor/)

Design notes, the audit that shaped the current scope, and the open work queue
live in [`devguide/`](devguide/README.md).

## License

MIT. See [LICENSE](LICENSE).
