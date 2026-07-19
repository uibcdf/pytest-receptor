# Usage

```bash
pytest                    # unchanged pytest; installing changes nothing
pytest --receptor=llm     # compact, for a coding agent
pytest --receptor=ci      # compact, nothing held back
```

Full option list in [Reference](reference.md). What it does to pytest
underneath, in [How it works](how-it-works.md). What it does not do, in
[Limitations](limitations.md).

## Profiles

| | `human` (default) | `llm` | `ci` |
| :--- | :--- | :--- | :--- |
| Output | unchanged pytest | compact | compact |
| Plugin registered | none at all | yes | yes |
| Root causes expanded | — | all, unless >10 | all |
| On-disk report referenced | — | yes | no |
| Progress on stderr | — | yes | yes |

`human` registers nothing, so plain `pytest` is byte-identical to not having the
receptor installed. Safe to add to a shared environment.

`ci` differs from `llm` for one reason: a CI runner is destroyed at job end, so
the on-disk report is unreachable by the time anyone reads the log. Nothing may
be held back.

## What a failing run looks like

```text
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

- One line on success, with exit status and counts.
- Failures grouped by root cause, keeping every affected test ID.
- No source echo — you have the files. The assertion diff, which you cannot
  reconstruct, is kept.
- A rerun command that works pasted verbatim from where you invoked pytest.
- Every warning group and every skip reason listed, not counted.

Field-by-field breakdown in [Reference](reference.md).

## Flags

**You need none.** `--receptor=llm` already quietens pytest further than `-q`
does; adding `-q --no-header` produces byte-identical output.

```{warning}
Do **not** pass `--tb=line` or `--tb=no`. They control how pytest *builds* the
traceback, not how it prints it, so they save about twenty tokens and delete the
`frames:` line telling you where to look. Drop a restrictive `--tb` from
`addopts` for these runs.
```

## Progress

One line per ten percent, on **stderr**, after the first twenty seconds:

```text
receptor: 10% 933/9332 52s
receptor: 20% 1866/9332 108s
```

| Property | |
| :--- | :--- |
| Never on stdout | discard stderr and the report is unchanged |
| Bounded | nine lines whether the run takes five minutes or three hours |
| Shows pace | a decile suddenly taking four times longer is visible |
| Not a hang detector | it fires when a test finishes; a stuck test emits nothing |

## Distributed runs

```bash
pytest --receptor=llm -n 12
```

Byte-identical output to a serial run. Counts, grouping and exit status do not
change with `-n`, and progress comes from the controller only.

## Measuring your own suite

```bash
pytest --receptor=llm --receptor-stats
```

```text
receptor stats: 38 tokens vs 148 for pytest as you configured it | 110 fewer (-74.3%)
```

The baseline is **your** configuration, untouched, measured in the same run
rather than estimated. Expect it to differ from the published
[benchmarks](benchmarks.md), which use a deliberately strict baseline.

Exact counts need `tiktoken`; without it the figure falls back to a labelled
approximation.

## Recovering what was held back

Everything you need is on stdout. Detail is withheld only above ten distinct
root causes, and only when the report exists to hold it:

```text
full report: .pytest_cache/d/receptor/last-run.txt
```

Written **during** the run, so recovering it is a file read, never a second test
run. With `-p no:cacheprovider` nothing is withheld at all, since there would be
nowhere to recover it from.

`--receptor-full` expands everything on stdout. It is not the same as
`--receptor=human`: still grouped by root cause, still no source echo.
