# Reference

Everything you might need to look up, in tables.

## Command-line options

| Option | Default | Effect |
| :--- | :--- | :--- |
| `--receptor=human` | ✔ default | Unchanged pytest. The plugin registers nothing; output is byte-identical to not having it installed. |
| `--receptor=llm` | | Compact output for a coding agent that can open the on-disk report; holds back only a pathological spread of root causes (>10). See [Choosing between `llm` and `ci`](usage.md#choosing-between-llm-and-ci). |
| `--receptor=ci` | | The same renderer with build-log defaults: nothing held back, no on-disk report referenced, because a CI log gets one shot and the runner is gone afterwards. See [Choosing between `llm` and `ci`](usage.md#choosing-between-llm-and-ci). |
| `--receptor-full` | off | Expand everything: every occurrence, every message in full. |
| `--receptor-stats` | off | Append what this run cost against pytest as *you* configured it. Measured in the same run, not estimated. |
| `--receptor-events=PATH` | off | Stream normalized `pytest-receptor.events@1` JSONL and finalize it with integrity metadata. Requires `llm` or `ci`. See [Versioned evidence artifacts](artifacts.md). |
| `--receptor-events-max-bytes=BYTES` | 52428800 | Set the artifact's hard total-size ceiling. Minimum 65536. Omitted events are counted and declared in the finalized stream. |

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

Exactly one of these opens every run. The numeric status is always pytest's;
the label refines statuses that pytest uses for more than one state when the
receptor has concrete evidence, rather than inferring success or failure from
the absence of reports.

| Line | Exit | Meaning |
| :--- | :---: | :--- |
| `PASS exit=0` | 0 | The suite ran and passed. |
| `FAIL exit=1` | 1 | Tests failed. |
| `INTERRUPTED exit=2` | 2 | The run was interrupted; counts state how much ran. |
| `COLLECTION_ERROR exit=2` | 2 | Collection failed before the suite could run. |
| `ERROR exit=3` | 3 | An internal pytest error. |
| `USAGE_ERROR exit=4` | 4 | pytest was invoked incorrectly. |
| `USAGE_ERROR exit=5 \| invalid selection` | 5 | Under xdist, pytest returned its no-tests status for an invocation containing nonexistent filesystem targets; every missing target follows. |
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
| `invalid selection:` | An xdist invocation returned exit 5 while containing explicit filesystem targets that do not exist. Every missing target is listed. |
| `full report: <path>` | Detail was held back, and only then. |

## Progress on stderr

```text
receptor: 20% 106/530 20s
receptor: 40% 212/530 22s
receptor: 100% 530/530 67s
```

One line as the run crosses each twenty-percent threshold, after a silent
twenty-second warm-up, ending at 100% — at most five lines however long the run
takes. Thresholds already passed during the warm-up are skipped; later lines are
emitted at live crossings with a percentage calculated from the count beside
it. Never on stdout. Under xdist, emitted by the controller only.

## Exit status

The receptor never changes pytest's exit status — not on success, not on
failure, and not when the receptor itself raises.
