# `--receptor-stats` changes a controlled incomplete exit from code 0 to code 1

**Observed:** 2026-07-21  
**Consumer:** MolSysMT  
**pytest-receptor:** `5146688` (`0.6.0`)  
**Severity:** high — receptor changes the process exit code and emits an internal traceback

## Summary

The corrected incomplete-run verdict works without statistics: a controlled
`pytest.exit(returncode=0)` after one of four collected tests produces
`INCOMPLETE exit=0`, leaves three tests explicitly unexecuted, and the pytest
process returns 0. The previous disk artifact is also absent during the first
test, confirming that the session-start clearing fix works.

Adding `--receptor-stats` prints the same correct receptor verdict, but pytest
then crashes during `pytest_unconfigure` because its terminal writer targets an
already closed temporary file. The outer process consequently returns 1. This
is a result-integrity divergence: enabling a reporting/measurement option changes
pytest's exit status.

## Minimal reproducer

`conftest.py`:

```python
import pytest


def pytest_runtest_setup(item):
    if item.name == "test_stop_with_zero_exit":
        pytest.exit("controlled incomplete pilot run", returncode=0)
```

`test_incomplete.py`:

```python
def test_current_run_has_no_published_artifact(request):
    artifact = request.config.cache.mkdir("receptor") / "last-run.txt"
    assert not artifact.exists()


def test_stop_with_zero_exit():
    pass


def test_must_not_run_1():
    raise AssertionError("this test must remain unexecuted")


def test_must_not_run_2():
    raise AssertionError("this test must remain unexecuted")
```

First seed a prior report with a separate passing test, then run:

```bash
pytest --receptor=llm --receptor-stats test_incomplete.py
```

## Observed result

The compact report is semantically correct:

```text
INCOMPLETE exit=0 | 1 passed | incomplete: 1 of 4 executed | 0.18s

receptor stats: 25 tokens vs 119 for pytest as you configured it | 94 fewer (-79.0%) | cl100k_base
```

It is followed by an internal traceback ending at:

```text
File "_pytest/terminal.py", line 1003, in pytest_unconfigure
    self._report_keyboardinterrupt()
...
File "_pytest/_io/terminalwriter.py", line 168, in write_raw
    self._file.write(msg)
File "tempfile.py", line 500, in func_wrapper
    return func(*args, **kwargs)
ValueError: I/O operation on closed file.
```

The shell-observed process exit code is 1. Authoritative pytest without receptor
returns 0 with one passed test and the controlled exit notice. Receptor without
`--receptor-stats` also returns 0 and renders `INCOMPLETE exit=0`.

The on-disk report after the run contains the correct `INCOMPLETE` line. The
first test's artifact-absence assertion passes after a prior report was seeded,
so stale-artifact clearing is independently verified.

## Likely boundary

This appears specific to the stats baseline's temporary terminal stream. The
stream is closed before pytest's late `_report_keyboardinterrupt()` call in
`pytest_unconfigure`, which still holds a terminal writer referring to that
stream. The report itself has already been rendered by then.

A lower-severity companion symptom exists without `--receptor-stats`: pytest's
`!!!!!!!! _pytest.outcomes.Exit: ... !!!!!!!!` line is emitted after the compact
receptor verdict, so the receptor report is not the final stdout block for this
controlled-incomplete path. It does not change the exit code.

## Acceptance criteria

- The reproducer returns the same process exit code with normal pytest,
  `--receptor=llm`, and `--receptor=llm --receptor-stats`.
- The compact verdict is `INCOMPLETE exit=0`, never `PASS`.
- No receptor or pytest internal traceback is emitted.
- The stats temporary stream remains valid through all late pytest terminal
  hooks, or the original terminal writer is restored before it is closed.
- The compact report remains the final machine-oriented stdout block, including
  controlled `pytest.exit` and maxfail/incomplete paths.
- Add serial regressions with and without `--receptor-stats`; exercise the same
  boundary under xdist if pytest can produce an equivalent controlled exit.

---

## Resolution

**Fixed 2026-07-21 (PR-PILOT-011).** The cause is exactly the boundary this
report identified. `--receptor-stats` points the standard reporter's `_tw` at a
temp file to measure pytest's baseline, and reads-then-closes that file in the
receptor's `pytest_unconfigure`. pytest's *own* `pytest_unconfigure` runs later
and, on a controlled `pytest.exit`, calls `_report_keyboardinterrupt()`, which
writes the Exit banner to `_tw` — the now-closed temp file. The `ValueError`
propagates out of the hook, and pytest returns 1.

The receptor now redirects the reporter's `_tw` to a discard stream
(`os.devnull`) in its `pytest_unconfigure`, after reading the baseline and before
pytest's late hooks run. The write is valid (no crash, exit code unchanged) and
goes nowhere, so the Exit banner no longer trails the compact report. That also
resolves the companion symptom noted *without* `--receptor-stats`: the
`!!!! Exit !!!!` line no longer follows the verdict, so the receptor block is the
final machine-oriented stdout in both modes.

Regression (subprocess, with and without `--receptor-stats`): a controlled
`pytest.exit(returncode=0)` must return exit 0, render `INCOMPLETE exit=0`, emit
no `!!!!` banner, and produce no `I/O operation on closed file` traceback.
Verified against this report's exact reproducer.
