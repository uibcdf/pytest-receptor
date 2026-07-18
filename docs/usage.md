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

**This is what you get without asking.** These two are the same thing:

```bash
pytest                    # the default
pytest --receptor=human   # the same, stated explicitly
```

Installing `pytest-receptor` therefore changes nothing about how anyone else's
runs behave. In a shared environment you can install it for yourself, or for an
agent, without affecting colleagues who never pass `--receptor`. A regression
test asserts the byte-for-byte equivalence.

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
* Warnings grouped by category and message, with counts and origin, so a green
  run with a new deprecation does not look like a clean one.
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

## Interaction with pytest's own output flags

**You do not need to add anything.** `--receptor=llm` already configures the
standard reporter, and it goes further than the usual hand-tuned flags:

| What the receptor sets | CLI equivalent | Why |
| :--- | :--- | :--- |
| `verbose = -2` | `-qq` | Removes the progress bar *and* the trailing `N passed in Xs` line, which would otherwise duplicate the receptor's own verdict. Plain `-q` leaves that line in place. |
| `no_header = True` | `--no-header` | Removes the banner, `rootdir`, and plugin list. |
| `no_summary = True` | `--no-summary` | Removes the `short test summary info` section. |

So `pytest --receptor=llm` and `pytest --receptor=llm -q --no-header` produce
byte-identical output. The extra flags are redundant.

### Do not restrict `--tb`

`--tb` is deliberately left alone, and you should leave it alone too.

```{warning}
`--tb=line` and `--tb=no` **degrade** the receptor's output. They save a
handful of tokens and cost you the call chain.
```

| Command | Tokens | Call chain |
| :--- | ---: | :--- |
| `--receptor=llm` | 74 | present |
| `--receptor=llm --tb=short` | 74 | present |
| `--receptor=llm --tb=line` | 53 | **lost** |
| `--receptor=llm --tb=no` | 53 | **lost** |

The reason is that `--tb` does not control how a traceback is *printed*. It
controls how `longrepr` is *built*. Under `--tb=no` pytest never generates the
frame information in the first place, so there is nothing for the receptor to
summarize, and this line disappears:

```text
frames: tests/test_merge.py:6 -> molsysmt/merge.py:41 -> molsysmt/topology.py:117
```

Twenty-one tokens saved in exchange for no longer knowing where to look.

If your `addopts` in `pyproject.toml` or `pytest.ini` sets a restrictive `--tb`,
remove it when using the receptor.

---

## Distributed runs (`pytest-xdist`)

Supported, and tested in CI both ways.

```bash
pytest --receptor=llm -n 12
```

A distributed run produces **byte-identical output to a serial one**. Counts,
grouping, root-cause detection, and exit status do not change with `-n`.

This is not automatic. Workers finish in arbitrary order, so reports arrive
scrambled; occurrences and groups are given a total order before rendering.
Without that, the same failure would render differently on every run, and a
consumer could not tell "this is the same failure as before" from "this is
something new".

```{note}
Not yet reported: **worker identity**. A group tells you it has 38 occurrences
and names them, but not which worker ran each one. If a failure only reproduces
on a particular worker, the receptor will not currently help you see that.
```

`xdist` writes a `bringing up nodes...` line straight to the terminal, which the
receptor does not intercept. It costs a few tokens and is left alone rather than
swallowing output belonging to another plugin.

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
* **Tracebacks keep the decisive frame.** Every local frame survives; external
  frames are pruned to the boundary and the terminal frame, marked `(ext)`, with
  `...` where frames were elided. Dropping external frames entirely would hide
  the answer whenever a failure originates inside a dependency.
* **Projects can declare their own normalizers.** Scientific failures carry
  array shapes, dtypes, and device names that split one root cause into dozens
  of groups. We cannot guess which are non-semantic, so declare them:

  ```ini
  [pytest]
  receptor_normalizers =
      shape \(\d+, \d+\) -> shape (N, M)
      device='cuda:\d+' -> device='cuda:N'
  ```

  Each rule is `regex -> replacement`, applied before grouping only. The raw
  message is still what you read. A rule that fails to compile is skipped rather
  than costing you the run.
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
* Values that look like credentials are redacted before anything is rendered or
  written:

  ```text
  ValueError: connect failed: api_key=[REDACTED] rejected
  ```

  This happens early enough that a secret reaches neither the terminal, nor the
  on-disk report, nor a fingerprint.

  ```{warning}
  This is a conservative net, not a security boundary. It matches keyword-anchored
  shapes -- `api_key=`, `token:`, `Bearer ...` -- with a minimum length. It cannot
  catch a secret that does not look like one. Do not rely on it to make a log
  safe to publish.
  ```

* The on-disk report is created owner-only (`0600`) and will not follow a
  symlink.

If rendering raises for any reason, the receptor emits `RECEPTOR_ERROR` followed
by the underlying exception and the raw pytest evidence, and preserves pytest's
original exit status. Enabling the plugin cannot lose a run.
