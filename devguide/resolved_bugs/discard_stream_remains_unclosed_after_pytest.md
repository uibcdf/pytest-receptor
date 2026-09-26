---
summary: Close the late-terminal discard stream without leaking ResourceWarning
issue: uibcdf/pytest-receptor#4
status: resolved
opened: 2026-09-21
closed: 2026-09-26
severity: low
verification: reproduced
area: [output, lifecycle, xdist]
guard: tests/test_plugin.py::test_late_terminal_discard_stream_is_closed
normative:
blocked_by: []
supersedes: []
---

# The late-terminal discard stream remains unclosed

**Reported:** 2026-09-21 while testing the SMonitor Python 3.14 transition.
**Consumer:** SMonitor (`uibcdf/smonitor#17`).
**Versions:** Python 3.14.7, pytest 9.1.1, pytest-xdist 3.8.0, pytest-receptor 1.1.0.

## What

The successful compact verdict can be accompanied by several `ResourceWarning` lines for
an unclosed `/dev/null` text stream. They are not part of pytest's normal report. A
SMonitor full-suite run with twelve workers printed seven such lines before the compact
`PASS exit=0 | 465 passed, 2 skipped` verdict; the same tests with xdist but without
pytest-receptor printed none. A pre-candidate full-suite run also printed the warnings.

This is output contamination and a file-descriptor lifecycle defect, not an outcome or
exit-code disagreement.

## How

The receptor's `pytest_unconfigure` calls `_silence_late_terminal()`, which opens
`os.devnull`, stores it in `self._sink`, and assigns a writer backed by it to pytest's
terminal reporter. There is no later `self._sink.close()` or transfer to a context that
owns the stream. The open handle is intentional until pytest's later terminal hooks run;
its failure to close afterwards is not. The earlier resolved bug
`molsysmt_incomplete_stats_closes_terminal_stream.md` explains why closing it immediately
in the same hook would reintroduce a wrong exit code on controlled incomplete runs.

Reproduction from the SMonitor checkout with the temporary CPython 3.14.7 test
environment, with plugin autoload disabled in both runs:

```text
python -m pytest -q -n 12 -p xdist.plugin -p pytest_receptor.plugin --receptor=llm -p no:cacheprovider
ResourceWarning: unclosed file <... name='/dev/null' ...>  # repeated seven times
PASS exit=0 | 465 passed, 2 skipped | 2.09s

python -m pytest -q -n 12 -p xdist.plugin -p no:cacheprovider
465 passed, 2 skipped  # no /dev/null ResourceWarning
```

The command needs the usual SMonitor cross-library test dependencies, NumPy and Pint.
The exact SMonitor candidate changes were local when measured, so the code-level
`_silence_late_terminal()` inspection is the durable reproduction seam.

## Why

The extra warnings appear outside the bounded report and waste tokens in the agent-facing
mode. They can make a successful run look suspicious even though the authoritative exit
code and counts are correct.

## What was refuted

- The `not resolved` skip reason is not caused by pytest-receptor: native pytest with
  `-rs` reports the same reason for the two SMonitor skips.
- The warnings are not intrinsic to pytest-xdist: the same full suite and worker count
  without pytest-receptor emits no such warning.
- Closing the stream in the current early `pytest_unconfigure` hook without preserving
  later writes would recreate the resolved PR-PILOT-011 regression.

## Acceptance criteria

- A subprocess regression detects no `/dev/null` `ResourceWarning` after normal serial
  and xdist runs, with and without `--receptor-stats`.
- Controlled incomplete `pytest.exit(returncode=0)` still returns zero, produces an
  `INCOMPLETE` verdict, and never prints a late pytest Exit banner or closed-writer error.
- The stream has an explicit lifecycle after the last pytest writer use; no test merely
  suppresses `ResourceWarning` while leaving the resource open.

## Resolution

Fixed 2026-09-26 (PR-PILOT-016). `pytest_unconfigure` is now a first-entered
hook wrapper. It redirects pytest's terminal writer before the other
unconfigure implementations run, preserving the controlled-exit behavior of
PR-PILOT-011, and closes the discard stream after all of them finish. The
cleanup also runs if another implementation raises.

The subprocess guard checks serial and two-worker xdist runs, each with and
without `--receptor-stats`. An atexit check showed `self._sink.closed` was
false in all four modes before the fix and true after it. It also checks the
verdict, exit status and absence of trailing `ResourceWarning` text. The
existing controlled-incomplete regression still checks the zero exit code,
`INCOMPLETE` verdict, and absence of a late Exit banner or closed-writer error.

### Correction, 2026-09-26

The first hosted matrix run exposed unrelated `ResourceWarning` lines for
unclosed xdist sockets on Python 3.11. The guard now matches only an unclosed
`/dev/null` file, the resource owned by this issue. It still checks explicitly
at process exit that every receptor discard stream was closed.
