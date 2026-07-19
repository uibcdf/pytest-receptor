# Usage

How to run the receptor and read what it gives you.

For a table of every option and output field, see [Reference](reference.md).
For what it does to pytest underneath, see [How it works](how-it-works.md).
For what it deliberately does not do, see [Limitations](limitations.md).

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

* One line on success, with the exit status and counts.
* Every distinct warning group listed, with counts and origin, so a green run
  with a new deprecation does not look like a clean one. Ranking by frequency
  and truncating would hide precisely the group that appears once, which is the
  one most likely to be new.
* Skips and xfails grouped by reason. A suite with optional dependencies skips
  heavily, and `412 skipped` does not say which capability is missing:

  ```text
  skipped: 38 in 2 groups
    x30 | openmm not installed
    x8 | requires a GPU
  ```

  Warning messages are shortened to about a hundred characters on stdout, since
  the line exists to let you recognise the warning rather than reproduce it; the
  full text is in the report on disk. Every group is listed regardless.

  A skip with no declared reason is reported as its own group,
  `x5 | (no reason declared)`, because that is a finding in its own right: tests
  are switched off and nobody recorded why.
* Failures grouped by root cause, keeping every affected test ID.
* No source echo. The agent already has your files; the assertion diff, which it
  cannot reconstruct, is kept.
* A literal rerun command per group.
* Every root cause in full. Only a pathological spread is summarized.

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
| Root causes expanded | all, unless more than ten | all |
| On-disk report referenced | yes | no |

---

## Interaction with pytest's own output flags

**You do not need to add anything.** `--receptor=llm` already configures the
standard reporter, and it goes further than the usual hand-tuned flags:

| What the receptor sets | CLI equivalent | Why |
| :--- | :--- | :--- |
| `verbose = -2` | `-qq` | Removes the progress bar *and* the trailing `N passed in Xs` line, which would otherwise duplicate the receptor's own verdict. Plain `-q` leaves that line in place. |
| `no_header = True` | `--no-header` | Removes the banner, `rootdir`, and plugin list. |
| `reportchars = ""` | *(no flag)* | Removes the `short test summary info` section. `--no-summary` would also have done it, and would also have silenced every other plugin — see [How it works](how-it-works.md). |
| `color = "no"` | `--color=no` | Colour is decoration for a terminal. Forced colour makes pytest emit ANSI into a pipe, which on an 8,000-test run is 73 kB of escape codes. |

So `pytest --receptor=llm` and `pytest --receptor=llm -q --no-header` produce
byte-identical output. The extra flags are redundant, and `--color=yes` is
overridden.

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

## Knowing the run is alive

pytest streams a progress character per test. The receptor suppresses those, and
on a long suite that leaves the terminal completely silent — a 520-second run
showed nothing at all until it finished. A consumer cannot tell a working suite
from a stalled one, and if the process is killed on a timeout it learns nothing
whatsoever, where plain pytest would at least have left a trail of dots.

Progress goes to **stderr**, once per ten percent of the suite. Under xdist it
comes from the controller only, so the milestones are global rather than one
stream per worker:

```text
receptor: 10% 933/9332 52s
receptor: 20% 1866/9332 108s
receptor: 30% 2800/9332 163s
```

Three properties worth knowing:

* **It never touches stdout.** The report stays exactly as parseable as before.
  Discard stderr and you get the old behaviour.
* **Short runs stay silent.** Nothing is emitted in the first twenty seconds,
  so an ordinary run is unaffected.
* **It is not a hang detector.** The line is emitted when a test finishes, so a
  genuinely stuck test produces no further output. What it gives you is the
  point the run reached — which is exactly what you want if something killed it.

```{note}
The predecessor of this feature claimed to be a periodic heartbeat and was not:
it could only fire between tests, so a single slow test produced nothing. It was
removed rather than fixed. This replacement makes the weaker claim it can
actually keep.
```

**The cost does not grow with the run.** Reporting by decile rather than by
clock bounds the output at nine lines whether the suite takes five minutes or
three hours -- roughly 110 tokens, against a report of 386 and a configured
pytest of 10,372 on the same run.

The elapsed time on each line is there for a second reason: it exposes pace. If
the first 70% took twenty seconds and each decile after that takes twelve, the
slowdown is visible before the run has even finished.

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

## What is on stdout, and what is not

**Everything you need is on stdout.** All root causes are rendered in full, with
their message, frames, and rerun command. You should never have to open a file
to act on a failure, and you must never have to run the suite again.

That was not the original design. `llm` used to show the first three causes and
point at a file for the rest, on the theory that an agent fixes one thing at a
time. Measurement killed it: at five distinct causes, holding back saves forty
tokens and costs two hundred more the moment the consumer reads the file, since
the file repeats what was already shown. Grouping had already solved the volume
problem, and withholding on top of it was solving a problem that no longer
existed.

What remains held back:

* **Occurrence lists.** A group of thirty-eight failing tests names three and
  counts the rest. The rerun command already selects all of them, so the
  remaining node IDs are recoverable without being read.
* **A pathological spread of causes.** Above ten *distinct* root causes,
  expanding all of them stops being cheaper than naming the file.

In both cases the complete report exists on disk before the summary is printed:

```text
full report: .pytest_cache/d/receptor/last-run.txt
```

It is written **during** the run and contains every group, every occurrence, and
every captured section.

```{note}
The `d/` component comes from pytest's own cache layout, not from us — we ask
`config.cache.mkdir("receptor")` and pytest decides where that lives. It is the
same on pytest 8 and 9, but the path the receptor prints is always the resolved
one, so prefer copying that over reconstructing it.
```

Detail is only ever withheld when that file is actually reachable. With
`-p no:cacheprovider` no report is written, so nothing is withheld at all rather
than being made unrecoverable.

If you know in advance that you want everything on stdout:

```bash
pytest --receptor=llm --receptor-full
```

`--receptor-full` is not the same as `--receptor=human`. Human output is complete
but redundant: source echo, headers, colour, and a duplicated summary section.
`--receptor-full` is complete in agent format and still grouped by root cause.

---

## Where to go next

- Every option, outcome label and output field, in tables — [Reference](reference.md)
- Why grouping keys on the crash location, and what `no_summary` broke —
  [How it works](how-it-works.md)
- Worker identity, warning baselines, and the bounds of credential redaction —
  [Limitations](limitations.md)
- What the compression actually measures — [Benchmarks](benchmarks.md)
