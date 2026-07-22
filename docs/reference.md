# Reference

Everything you might need to look up, in tables.

## Command-line options

| Option | Default | Effect |
| :--- | :--- | :--- |
| `--receptor=human` | ✔ default | Unchanged pytest. The plugin registers nothing; output is byte-identical to not having it installed. |
| `--receptor=llm` | | Compact output for a coding agent. |
| `--receptor=ci` | | The same renderer with build-log defaults: nothing held back, no on-disk report referenced. |
| `--receptor-full` | off | Expand everything: every occurrence, every message in full. |
| `--receptor-stats` | off | Append what this run cost against pytest as *you* configured it. Measured in the same run, not estimated. |

## What the compact profiles set on pytest

Applied on your behalf; you do not need to pass any of them.

| Setting | Equivalent | Why |
| :--- | :--- | :--- |
| `verbose = -2` | `-qq` | Suppresses the progress bar and the trailing counts line. |
| `no_header = True` | `--no-header` | Suppresses the banner, `rootdir`, and plugin list. |
| `reportchars = ""` | *(no flag)* | Suppresses `short test summary info` without silencing other plugins. |
| `color = "no"` | `--color=no` | Overrides `FORCE_COLOR`, `PY_COLORS`, and an explicit `--color=yes`. Not applied while `--receptor-stats` measures a baseline, where the point is to record what pytest would really have emitted. |

`--tb` is deliberately **not** set, and restricting it yourself degrades the
output — see *Do not restrict `--tb`* in [Usage](usage.md).

## Configuration file

| Setting | Type | Purpose |
| :--- | :--- | :--- |
| `receptor_normalizers` | line list | `regex -> replacement` rules applied before grouping, so project-specific dynamic values do not split one root cause into many. |
| `receptor_rerun_command` | string | The runner each `rerun:` line starts with. Default `pytest`. Set it to match how you invoke pytest, or empty to omit the line. |

```ini
[pytest]
receptor_normalizers =
    device='cuda:\d+' -> device='cuda:N'
    tmp/[a-f0-9]{8}/ -> tmp/HASH/
receptor_rerun_command = uv run pytest
```

Rules apply to grouping only — the message you read is the raw one. A rule that
fails to compile is skipped rather than costing you the run.

`receptor_rerun_command` replaces only the leading `pytest`; the receptor still
appends the selection and `-q`, so a configured runner reruns exactly the group
it is printed under. The promise that the line works pasted verbatim holds only
when this matches your invocation — a project driven by `uv run pytest`, `hatch
test`, `tox`, or a wrapper must set it.

## Session outcomes

Exactly one of these opens every run, derived from `pytest.ExitCode` rather than
from the absence of failure reports.

| Line | Exit | Meaning |
| :--- | :---: | :--- |
| `PASS exit=0` | 0 | The suite ran and passed. |
| `FAIL exit=1` | 1 | Tests failed. |
| `INTERRUPTED exit=2` | 2 | The run was interrupted; counts state how much ran. |
| `COLLECTION_ERROR exit=2` | 2 | Collection failed before the suite could run. |
| `ERROR exit=3` | 3 | An internal pytest error. |
| `USAGE_ERROR exit=4` | 4 | pytest was invoked incorrectly. |
| `NO_TESTS exit=5` | 5 | Nothing was collected. |
| `RECEPTOR_ERROR` | *preserved* | The receptor itself failed. pytest's status and the raw evidence follow. |

A run stopped early by `-x` or `--maxfail` is additionally marked `incomplete`
with executed and collected counts, **even when nothing has failed yet**.

## Result categories

These follow pytest exactly, including the fact that they count *phases* rather
than tests: a test that passes and then fails its teardown is both `passed` and
an `error`.

| Word | Means |
| :--- | :--- |
| `failed` | The call phase failed. |
| `errors` | Setup or teardown failed. |
| `passed` | The call phase passed. |
| `skipped` / `xfailed` / `xpassed` | As pytest reports them. |

## Anatomy of a failure group

```text
[1] TypeError | 38 tests | setup          ← index, exception, blast radius, phase
    conftest.py:31                        ← crash location, relative to your cwd
    TypeError: 'NoneType' object is not subscriptable
    caused by: KeyError: 'atoms'          ← only when `raise X from Y`
    frames: tests/a.py:12 -> lib/b.py:41 (ext)   ← only when more than one frame
    2 other messages:                     ← variants at this same call site
      ...
    captured stdout (tests/a.py::test_x): ← only when a test printed something
      ...
    tests:                                ← only when more than one occurrence
      tests/a.py::test_x[0]
      +35 more
    rerun: pytest tests/a.py -q           ← always; selects the whole group
```

## Other sections

Each appears only when it has something to say.

| Section | Appears when |
| :--- | :--- |
| `warnings: N in M groups` | Any warning was raised. Every distinct group is listed. |
| `skipped: N in M groups` | Any test was skipped. Grouped by reason; `(no reason declared)` is its own group. |
| `xfailed: N in M groups` | Any expected failure occurred. |
| `unexpected passes:` | An `xfail` test passed. Named individually, with its reason. |
| `full report: <path>` | Detail was held back, and only then. |

## Progress on stderr

```text
receptor: 20% 190/530 20s
receptor: 40% 212/530 22s
receptor: 100% 530/530 67s
```

One line as the run crosses each twenty-percent threshold, after a silent
twenty-second warm-up, ending at 100% — at most five lines however long the run
takes. Thresholds already passed when the warm-up ends are emitted together, in
order, so every percentage is a round milestone; the count beside the first can
already be a little past it, since reporting only began at the warm-up. Never on
stdout. Under xdist, emitted by the controller only.

## Exit status

The receptor never changes pytest's exit status — not on success, not on
failure, and not when the receptor itself raises.
