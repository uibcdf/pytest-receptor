# pytest-receptor

[![Tests](https://github.com/uibcdf/pytest-receptor/actions/workflows/tests.yml/badge.svg)](https://github.com/uibcdf/pytest-receptor/actions/workflows/tests.yml)
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

FAIL exit=1 | 38 errors, 90 passed | 12.40s | 1 root cause

[1] TypeError | 38 tests | setup
    conftest.py:31
    TypeError: 'NoneType' object is not subscriptable
    tests:
      tests/test_merge.py::test_merge[0]
      tests/test_merge.py::test_merge[1]
      tests/test_merge.py::test_merge[2]
      +35 more
    rerun: pytest tests/test_merge.py -q
```

That is 106 tokens. Plain `pytest` spends 3,308 on the same run.

---

## Install

```bash
pip install pytest-receptor
```

Requires Python 3.11-3.13 and pytest 8 or later. Every combination of
Python 3.11/3.12/3.13 with pytest 8 and 9 is exercised in CI, so the support
claim is evidence rather than intent.

## Use

```bash
pytest                    # unchanged pytest -- installing this changes nothing
pytest --receptor=llm     # compact output for a coding agent
pytest --receptor=ci      # compact output for a CI log
pytest --receptor=human   # the default, stated explicitly
pytest --receptor=llm --receptor-full   # expand every failure group
pytest --receptor=llm --receptor-stats  # what did this actually save?
```

**Installing the plugin does not change anything until you ask it to.** The
default is `human`, and `human` is a true passthrough: the plugin registers
nothing at all, so `pytest` on its own produces output byte-identical to not
having it installed. There is a test asserting exactly that.

This matters in a shared environment. You can install it for yourself, or for
your agent, without altering what anyone else sees.

You do not need to combine these with pytest's own quieting flags —
`--receptor=llm` already sets the equivalent of `-qq --no-header --no-summary`,
so adding them changes nothing. One caveat: do **not** pass `--tb=line` or
`--tb=no`. Those control how pytest *builds* the traceback, not how it prints it,
so they save a handful of tokens and silently cost the receptor the call chain.
See the [usage guide](https://uibcdf.github.io/pytest-receptor/usage.html).

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

Failures are grouped by exception type, phase, crash location, and cause chain.
Forty tests broken by one fixture become one group that keeps all forty test
IDs, and a parametrized test failing on twenty inputs is one bug with twenty
messages rather than twenty bugs. Failures crashing in unrelated places stay
separate, and so do two failures wrapping different underlying errors.

`raise X from Y` reports both, because the wrapper is usually the less
informative half:

```text
ValueError: could not build topology
caused by: KeyError: 'atoms'
```

### It gives you everything on stdout

Every root cause is rendered in full. Grouping has already collapsed the volume,
so withholding on top of it saves almost nothing and costs double if you then
have to read the file back: measured at five distinct causes, holding back saved
forty tokens and cost two hundred. Only a pathological spread — more than ten
distinct causes — is summarized, and only when the on-disk report exists to hold
what was left out.

Occurrence lists are the exception, and for the opposite reason: a group of
thirty-eight failing tests names three and counts the rest, because the rerun
command already selects all of them.

### It says why tests were skipped

A suite built on optional dependencies skips in the hundreds, and `412 skipped`
does not say which capability is missing:

```text
skipped: 412 in 3 groups
  x380 | openmm not installed
  x30 | requires a GPU
  x2 | (no reason declared)
```

The last group is deliberate: a skip nobody documented is worth knowing about.
Warnings and xfails are grouped the same way. Each section is bounded by the
variety of reasons rather than the number of tests.

### It degrades safely

If the receptor itself raises, you get `RECEPTOR_ERROR`, the underlying
exception, the raw pytest evidence, and pytest's original exit status. The worst
case of enabling this plugin is standard pytest plus one line of noise.

Test output is treated as untrusted input: ANSI escapes and control characters
are stripped, values that look like credentials are redacted before anything is
rendered or written, and no text produced by a test can forge a verdict line.
The redaction is a conservative net for obvious shapes — `api_key=`, `Bearer ...`
— not a security boundary.

### It shows the run is alive

pytest streams a progress character per test; suppressing those leaves a long
suite completely silent. Progress now goes to **stderr** — never stdout, so the
report stays as parseable as before — once per ten percent of the suite:

```text
receptor: 10% 933/9332 52s
receptor: 20% 1866/9332 108s
```

Reporting by decile rather than by clock bounds this at nine lines whether the
run takes five minutes or three hours, and the elapsed time exposes pace: a
decile that suddenly takes four times longer is visible before the run ends.

It is a liveness signal, not a hang detector: the line is emitted when a test
finishes, so a stuck test produces no further output. What survives is how far
the run got, which is what you want when something kills it.

### It works under `pytest-xdist`

A distributed run produces **byte-identical output to a serial one**. Workers
finish in arbitrary order, so occurrences and groups are given a total order
before rendering; otherwise the same failure would render differently on every
run. Counts, grouping, and exit status are unaffected by `-n`.

Worker identity is not reported, and that is a decision rather than a gap. The
signal it would provide — a group of failures landing entirely on one worker —
is confounded by the distribution mode: under `--dist loadfile` or `loadscope`,
failures from one file land on one worker by construction. The bare identifier
without execution order also does not help reproduce anything, which is what
`-n0` is for.

---

## How it works

Worth knowing before you trust it with your suite.

**It does not replace pytest's reporter.** Earlier versions unregistered
pytest's `TerminalReporter` and substituted a subclass of it. This one leaves it
in place — so any plugin that looks it up still finds it — and quietens it
through its documented options: `verbose = -2` and `no_header`, an emptied
`reportchars`, and a wrapper around `pytest_report_teststatus` that drops the
progress characters while preserving pytest's own categorization.

`no_summary` is deliberately *not* used, although it looks like the obvious
switch. It gates the whole `pytest_terminal_summary` hook, which is where
third-party plugins write, and setting it swallowed pytest-cov's report
entirely.

**It collects from public hooks.** `pytest_runtest_logreport` for phase results,
`pytest_collectreport` for collection failures, `pytest_warning_recorded` for
warnings, and `pytest_sessionfinish` to render. Rendering happens in
`sessionfinish` rather than `terminal_summary` because pytest does not call the
latter for internal errors, and an internal error is exactly when you most need
to be told the truth.

**Grouping is call-site aware.** The key is exception type, phase, crash
location, and cause chain. The message is deliberately excluded: keying on it
fragmented a parametrized test into one group per input, which defeats grouping
exactly where suites are most repetitive. Differing messages are kept as
variants inside the group and shown. Crash location rather than test line is
what makes this right — a bug in `merge.py:117` groups every caller.

**Tracebacks keep the decisive frame.** Every local frame is kept, because that
is the code you can change. External frames are pruned to the boundary you
entered the dependency at and the frame that actually broke, with elisions
marked:

```text
frames: tests/test_merge.py:12 -> molsysmt/merge.py:41 -> numpy/core/shape.py:88 (ext) -> ... -> numpy/core/_methods.py:52 (ext)
```

Dropping external frames entirely is cheaper, and wrong: when a failure
originates inside NumPy or a serializer, the external frame *is* the answer.

**Nothing is thrown away, and nothing is deferred.** Grouping is a presentation
decision; every occurrence keeps its node ID, phase, and location. The complete
report is written to `.pytest_cache/d/receptor/last-run.txt` while the run is
still going, owner-only and refusing symlinks. Detail is only ever held back
when that file exists to hold it, so a consumer can never be left with
information reachable solely by running the suite again.

**`--tb` is deliberately left alone.** It controls how pytest *builds*
`longrepr`, not how it prints it. Forcing `--tb=no` would look like a sensible
way to suppress tracebacks and would silently destroy every frame this plugin
exists to summarize.

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
| Cascade (38 failures, one cause) | 3308 | **106** | **-96.8%** |
| Green suite (128 tests) | 126 | **16** | -87.2% |
| Green with warnings | 189 | **46** | -75.9% |
| Green with many distinct warnings | 1946 | **669** | -65.6% |
| Single assertion failure | 354 | **167** | -53.1% |
| Five distinct causes | 411 | **212** | -48.2% |
| Collection error | 295 | **218** | -26.3% |
| Mixed states (skip, xfail, xpass) | 131 | **78** | -39.5% |

Every scenario is cheaper, most of them by half or better. In a TDD loop that
runs the suite twenty times, the cascade row alone is sixty thousand tokens.

And the saving grows with the suite. Measured on eight thousand tests under
twelve xdist workers, against `pytest -q -n 12` — a pytest that has *already*
been quietened:

| Scenario | `-q -n 12` | `--receptor=llm -n 12` | Saving |
| :--- | ---: | ---: | ---: |
| Whole suite green | 812 | **24** | 97.0% |
| One fixture breaks 200 tests | 25,474 | **114** | 99.6% |
| Six unrelated bugs | 1,497 | **285** | 81.0% |

`-q` prints one progress character per test, so a *successful* eight-thousand
test run costs 812 tokens of dots before anything has gone wrong.

### And if you already tuned pytest

If you are the kind of person who already runs `pytest -q --no-header
--tb=short`, the picture is narrower and you deserve to see that too:

| Scenario | tuned pytest | `--receptor=llm` | Change |
| :--- | ---: | ---: | ---: |
| Cascade (38 failures, one cause) | 2863 | **106** | -96.3% |
| Green with many distinct warnings | 1846 | **669** | -63.8% |
| Green with warnings | 91 | **46** | -49.5% |
| Five distinct causes | 316 | **212** | -32.9% |
| Green suite (128 tests) | 23 | **16** | -30.4% |
| Single assertion failure | 197 | **167** | -15.2% |
| Collection error | 196 | **218** | +11.2% |
| Mixed states (skip, xfail, xpass) | 31 | **78** | +151.6% |

Both positive rows are scenarios of a handful of tests, where any fixed overhead
looks enormous as a percentage: +151.6% is forty-seven tokens. They buy the
reason behind every skip and xfail and the name of the test that passed
unexpectedly, where `pytest -q` says `1 skipped, 1 xfailed, 1 xpassed` and
leaves you to re-run with `-rs` to find out which. Those sections are bounded by
the variety of reasons, not the number of tests, so four hundred skips across
three reasons still cost three lines.

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
