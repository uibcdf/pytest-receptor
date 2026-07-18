# Usage Guide

`pytest-receptor` adds one option to your normal pytest workflow.

```bash
pytest --receptor=[human|llm|ci]
```

---

## Profiles

### `human` (default)

Unchanged pytest. The plugin registers nothing at all, so the output is
byte-identical to running pytest without it installed. Nothing is intercepted,
suppressed, or buffered.

```bash
pytest --receptor=human
```

### `llm`

Compact output for a coding agent.

```bash
pytest --receptor=llm
```

```text
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

* One line on success, with the exit status and counts.
* Failures grouped by root cause, keeping every affected test ID.
* No source echo. The agent already has your files; the assertion diff, which it
  cannot reconstruct, is kept.
* A literal rerun command per group.
* The first three root causes in full, the rest one line each.

### `ci`

The same renderer with defaults suited to a build log.

```bash
pytest --receptor=ci
```

The difference from `llm` is not cosmetic. A CI runner is destroyed when the job
ends, so the on-disk full report is unreachable by the time anyone reads the log.
The CI profile therefore expands **every** group rather than holding any back.

| | `llm` | `ci` |
| :--- | :--- | :--- |
| ANSI colour | off | off |
| Progress output | none | none |
| Root causes expanded | first three | all |
| On-disk report referenced | yes | no |

---

## Session outcomes

The verdict is derived from pytest's exit status, never from the absence of
failure reports. Every run produces exactly one of:

| Output | Meaning |
| :--- | :--- |
| `PASS exit=0` | The suite ran and passed. |
| `FAIL exit=1` | Tests failed. |
| `INTERRUPTED exit=2` | The run was interrupted; the counts state how much ran. |
| `COLLECTION_ERROR exit=2` | Collection failed before the suite could run. |
| `ERROR exit=3` | An internal pytest error. |
| `USAGE_ERROR exit=4` | pytest was invoked incorrectly. |
| `NO_TESTS exit=5` | Nothing was collected. |
| `RECEPTOR_ERROR` | The receptor itself failed; pytest's status and evidence follow. |

A run stopped early by `-x` or `--maxfail` is marked `incomplete` with the
executed and collected counts, even when nothing has failed yet.

---

## Recovering what was held back

When `llm` holds back later root causes it names the file that has everything:

```text
full report: .pytest_cache/receptor/last-run.txt
```

That file is written **during** the run and contains every group, every
occurrence, and every captured section. Reading it costs one file read. This
matters because the alternative — re-running pytest with a different flag — costs
a whole test execution, which is usually far more expensive than any formatting
saving.

If you know in advance that you want everything on stdout:

```bash
pytest --receptor=llm --receptor-full
```

`--receptor-full` is not the same as `--receptor=human`. Human output is complete
but redundant: source echo, headers, colour, and a duplicated summary section.
`--receptor-full` is complete in agent format and still grouped by root cause.

When the cache provider is disabled (`-p no:cacheprovider`) no file is written
and the output names the flag instead.

---

## Measuring what it costs you (`--receptor-stats`)

```bash
pytest --receptor=llm --receptor-stats
```

```text
receptor stats: 38 tokens vs 148 for pytest as you configured it | 110 fewer (-74.3%) | cl100k_base
```

**The baseline is your own pytest configuration**, whatever it happens to be.
Nothing is overridden. If you normally run plain `pytest`, that is what you are
compared against; if you already run `pytest -q`, the comparison is against that
and the saving will look much smaller:

```text
receptor stats: 38 tokens vs 26 for pytest as you configured it | 12 more (+46.2%)
```

This is deliberate. The [benchmarks](benchmarks.md) page compares against a
deliberately strict `pytest -q --no-header --tb=short`, because a published claim
should not pick a weak opponent. But this flag answers a different, personal
question — *against how I actually run pytest, what does this save me?* — and only
your real settings can answer it. Expect the two numbers to differ.

The baseline is **measured, not estimated**. During the same run the standard
reporter renders into a temporary file instead of the terminal; that file is
tokenized and deleted. There is no second pytest invocation, no extra memory, and
your own output is byte-for-byte unchanged.

Both a net token count and a percentage are reported, with the same sign, because
on small runs only the net count is meaningful — "+46%" can be twelve tokens.

Token counts use `tiktoken` when it is installed. Without it, the figure falls
back to a labelled four-characters-per-token approximation.

This option is a diagnostic, not something to leave on: the statistics line
itself costs tokens.

---

## Grouping

Failures are grouped by exception type, phase, normalized message, and call
site.

* **Cascades collapse.** Forty tests broken by one fixture become one group that
  still lists all forty test IDs.
* **Unrelated failures stay apart.** Two `ValueError('boom')` raised from
  different places are two bugs, so they are two groups.
* **Dynamic values do not split a group.** Memory addresses and timestamps are
  normalized before grouping, so `0x7f8b...` differences do not fragment one
  cause into many.
* **Long messages are fingerprinted whole.** Grouping happens before any
  truncation, so two long diffs differing only in the middle cannot be merged by
  accident. When a message is shortened, the output states how much was omitted
  and where the complete text is.

---

## Safety

Test output is untrusted input. Exception messages, captured streams, parameter
IDs, and paths come from your tests and their dependencies.

* ANSI escapes and control characters are stripped.
* No text produced by a test can forge a verdict line or otherwise alter the
  structure of the report.
* The receptor never suggests a command that mutates your environment. Guidance
  is limited to the exact rerun selector for a failure.

If rendering raises for any reason, the receptor emits `RECEPTOR_ERROR` followed
by the underlying exception and the raw pytest evidence, and preserves pytest's
original exit status. Enabling the plugin cannot lose a run.
