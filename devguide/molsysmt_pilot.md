# Brief for the MolSysMT Team

**Recorded:** 2026-07-18

**For:** MolSysMT developers evaluating `pytest-receptor` on a real suite

**Read alongside:** the project [README](../README.md) for what the plugin does
and how, and [`scope_0.6.md`](scope_0.6.md) for why this release is deliberately
small.

---

## What we are asking

Run your suite through the receptor **in shadow mode** for a while: normal
pytest stays the authority for whether your tests pass, and the receptor output
is something you read alongside it and form an opinion about.

We are not asking you to trust it yet. We are asking whether its output is
*sufficient* — whether an agent, or you, can act on it without going back for
more.

That question cannot be answered from our synthetic test cases. MolSysMT is the
only suite we have access to with eight thousand tests, doctests, optional
dependencies, GPU fallbacks, twelve xdist workers, and a history of real
collection and conversion failures.

---

## What it is

A pytest reporter for coding agents. When an agent runs your tests, it reads
pytest's output, and that output was designed for a human at a terminal: banner,
`rootdir`, plugin list, progress bar, and the full source of every failing test.
The agent pays for all of it on every iteration.

The receptor renders the same run differently:

```text
FAIL exit=1 | 38 errors, 90 passed | 12.40s | 1 root cause

[1] TypeError | 38 tests | setup
    conftest.py:31
    TypeError: 'NoneType' object is not subscriptable
    frames: tests/test_merge.py:12 -> molsysmt/form/Topology/merge.py:117
    tests:
      tests/test_merge.py::test_merge[0]
      tests/test_merge.py::test_merge[1]
      tests/test_merge.py::test_merge[2]
      +35 more
    rerun: pytest tests/test_merge.py -q
```

The `frames:` line appears when a failure crosses more than one frame. It keeps
every frame in *your* code and prunes runs of library frames down to the point
you entered them and the point it broke, marked `(ext)`. When the bug is inside
NumPy or OpenMM, that external frame is the answer, so it is not discarded.

The important part is not that it is shorter. It is that one broken fixture
appears **once**, with every affected test still named, and with the command to
re-run them.

**Everything you need is on stdout.** Every root cause is rendered in full. You
should never have to open a file to act on a failure, and you must never have to
run the suite a second time to get information the first run already had.

### At your scale, with your command

You run `python -m pytest -q -n 12`. That matters: `-q` is already a tuned
pytest, so the figures published in our benchmarks — measured on suites of at
most 128 tests — understate what you would see.

Measured on eight thousand tests, twelve workers, `cl100k_base`:

| Scenario | `-q -n 12` | `--receptor=llm -n 12` | Saving |
| :--- | ---: | ---: | ---: |
| Whole suite green | 812 | **24** | 97.0% |
| One fixture breaks 200 tests | 25,474 | **114** | 99.6% |
| Six unrelated bugs | 1,497 | **285** | 81.0% |

Two things worth noticing.

**`-q` does not protect you.** It still prints one progress character per test,
which at eight thousand tests is 812 tokens of dots on a *successful* run. Every
run, including the ones where nothing is wrong.

**The cascade number is not a typo.** When one fixture breaks two hundred tests,
`-q` prints two hundred tracebacks: 25,481 tokens, most of them the same text
repeated. The receptor prints the cause once, names every affected test, and
gives you the command to re-run them: 114.

---

## What phase it is in

**Version 0.6.0. Pre-1.0, deliberately.**

The output format is this plugin's only public API, and this pilot exists partly
to find out whether that format is right. Freezing it at 1.0 before hearing from
you would be premature. Expect the format to change; tell us if it should.

What will **not** change, and what you can rely on from day one:

| Guarantee | Meaning |
| :--- | :--- |
| Never fabricates success | The verdict comes from `pytest.ExitCode`. An empty, interrupted, or fail-fast run cannot render as a pass. |
| Never loses a run | If the receptor itself raises, you get `RECEPTOR_ERROR`, the raw pytest evidence, and pytest's original exit status. |
| Never loses evidence | Grouping is presentation. Every occurrence keeps its node ID, and the complete report is on disk. |
| Never changes your results | `--receptor=human` registers nothing at all. The plugin cannot affect whether your tests pass. |

An earlier version reported `OK: 0 passed` for runs that pytest exited with
status 2 or 5 — an empty run and an interrupted run both looked like success.
That is fixed and has regressions. We mention it because it is the reason this
release exists, and because it is the class of bug you should be watching for.

---

## Installing it

You have the repository and a conda environment. From inside that environment:

```bash
pip install -e /path/to/pytest-receptor
```

**Dependencies: none beyond pytest.** The plugin requires `pytest>=8.0.0` and
nothing else. It does not import numpy, it does not touch your scientific stack,
and it adds nothing to your runtime dependencies.

One optional extra: `tiktoken`, used only by `--receptor-stats` to count tokens.
Without it that flag still works and falls back to a labelled approximation.

Supported and tested in CI: Python 3.11, 3.12, 3.13 against pytest 8 and 9,
serial and distributed.

To remove it, uninstall it. There is nothing to clean up beyond
`.pytest_cache/receptor/`.

---

## Invoking it

```bash
pytest                         # unchanged pytest -- installing changes nothing
pytest --receptor=llm          # compact output, for an agent
pytest --receptor=ci           # compact output, nothing held back
pytest --receptor=llm -n 12    # your normal parallel run
```

**Installing it into your shared environment is safe.** The default is `human`,
and `human` registers nothing at all, so anyone who does not pass `--receptor`
gets output byte-identical to not having the plugin installed. Nobody else on
the team is affected by your evaluation, and a regression test asserts it.

A few more things worth knowing before you start.

**You do not need to add quieting flags.** `--receptor=llm` already quietens
pytest further than `-q` does. Adding `-q` changes nothing.

**Do not pass `--tb=line` or `--tb=no`.** They control how pytest *builds* the
traceback, not how it prints it, so they save about twenty tokens and silently
delete the `frames:` line that tells you where to look. If MolSysMT's `addopts`
carries a restrictive `--tb`, drop it for these runs.

**xdist is supported.** A run with `-n 12` produces byte-identical output to a
serial run. Worker identity is not reported; see the table at the end for why we
decided against it rather than simply not having got to it.

**Coverage works alongside it.** `--cov` reports print normally. This needed
fixing: the first cut of the silencing swallowed pytest-cov's table completely,
because the option that suppresses pytest's own summary also gates the hook
third-party plugins write into. There is a regression test for it now.

**A long run now says it is alive.** Your 520-second green run printed nothing
at all until it finished, which makes a working suite indistinguishable from a
hung one — and yields nothing whatsoever if a timeout kills it, where `pytest -q`
would at least have left its dots. After the first minute, one line a minute goes
to stderr, never to stdout, once per ten percent of the suite:

```text
receptor: 10% 933/9332 52s
receptor: 20% 1866/9332 108s
```

Reporting by decile rather than by clock keeps this at nine lines however long
the suite runs, and the elapsed time shows pace — a decile that suddenly takes
four times longer than the last is worth knowing about while the run is still
going. It is a liveness signal, not a hang detector: it fires when a test
finishes, so a stuck test produces no further lines — but the last one printed
tells you where it got to.

**Skips are grouped by reason.** Your suite skips heavily for optional
dependencies, and `412 skipped` does not say which capability is missing:

```text
skipped: 412 in 3 groups
  x380 | openmm not installed
  x30 | requires a GPU
  x2 | (no reason declared)
```

The last group is deliberate. A skip with no recorded reason means tests are
switched off and nobody wrote down why — worth someone documenting or deleting,
and nothing else in a run points it out.

**Subtests and reruns work.** With `pytest-rerunfailures`, a test retried three
times is reported as one test that took three attempts, not as three tests.

### Seeing what it costs you

```bash
pytest --receptor=llm --receptor-stats
```

```text
receptor stats: 109 tokens vs 3360 for pytest as you configured it | 3251 fewer (-96.8%)
```

The baseline is *your* configuration, untouched — whatever `addopts` you already
have. pytest genuinely renders it into a temporary file during the same run, so
this is measured, not estimated. There is no second test run and nothing extra
is held in memory.

This is the number we would most like from you, on your real suite, in both a
green run and a bad one.

---

## What we need from you

In rough order of value.

### 1. Any case where the receptor and pytest disagree

This is the only category that is an emergency. If the receptor says `PASS` and
pytest's exit status says otherwise, or the counts differ, stop and tell us
immediately. Everything else can wait.

### 2. Diagnostic-sufficiency incidents

The important one, and the one we most want.

**Any case where the output was not enough to work from.** Not just where you
had to re-run pytest — where you had to open the report file, or go and read a
source file, or squint at something ambiguous. The rule we hold ourselves to is
that the information given to a consumer must be what it needs to work, compact
but complete. There is no "it was in the file" defence: if something you needed
was not in front of you, that is a design failure on our side, not user error.

This standard is why root-cause detail is no longer withheld at all. An earlier
version showed three causes and pointed at a file for the rest; measurement
showed that saved forty tokens and cost two hundred the moment anyone read the
file back. Tell us wherever the same mistake survives somewhere we have not
noticed.

### 3. Anything another plugin stopped doing

We suppress a lot of pytest's output, and doing that once swallowed pytest-cov's
report by accident. If a plugin you rely on goes quiet under `--receptor=llm`,
that is a bug on our side. `--cov` and `-n` are covered by tests; the rest of
your stack is not.

### 4. Grouping that got it wrong

Two shapes, both useful:

- **False grouping:** two genuinely different bugs collapsed into one group.
- **Missed grouping:** one root cause split across many groups, so a cascade
  still floods the output.

Scientific stacks are exactly where we expect this to break, because failures
carry array shapes, dtypes, file paths, and device names that our normalization
does not know about.

You can fix it yourself while you wait, and doing so is itself the evidence we
need:

```ini
[pytest]
receptor_normalizers =
    shape \(\d+, \d+\) -> shape (N, M)
```

Each rule is `regex -> replacement`, applied before grouping. **Please tell us
which rules you had to write.** That list is what decides which normalizers
become built-in defaults, and we have no way to guess it from here.

### 5. Real token numbers

`--receptor-stats` on your real suite, green and red. Our published figures come
from synthetic scenarios of at most 128 tests. Yours would be the first evidence
from a suite where it matters.

### 6. Anything that crashed

`RECEPTOR_ERROR` in your output means we have a bug. The run is safe — that is
what the fallback is for — but we want the traceback.

---

## What you can expect from us

- **Bugs in the first four categories above get priority over new features.**
- **The reliability floor is not negotiable.** If we ever have to choose between
  a prettier report and telling you the truth about a run, we tell you the truth.
- **No surprise behaviour changes in 0.6.x.** Format changes will land in 0.7
  with a note about what moved.
- **No dependency on MolSysSuite, ever.** `pytest-receptor` is a neutral plugin
  and must not import SMonitor, MolSysMT, or anything from the scientific stack.
  If integration becomes worth doing, it will be through a generic extension
  protocol that a dummy producer can exercise. See
  [`smonitor_and_molsyssuite_integration.md`](smonitor_and_molsyssuite_integration.md),
  which is exploratory and not an accepted contract.

### What it does not do yet

Stated plainly so you are not surprised:

| Not yet | Notes |
| :--- | :--- |
| Worker identity under xdist | You get the tests, not which worker ran them. We looked at adding it and decided against: with `--dist loadfile` or `loadscope` a group of failures lands on one worker by construction, so "all on gw3" would be an artifact rather than a finding, and the bare ID without execution order does not help you reproduce anything. If you suspect worker-local state, `-n0` is the check. |
| Thorough secret redaction | Obvious shapes are redacted (`api_key=`, `token:`, `Bearer ...`) before anything is rendered or written, and the report is owner-only. It is a conservative net, not a boundary: it cannot catch a secret that does not look like one. |
| A machine-readable artifact | The full report is plain text, not JSON. A structured artifact is post-0.6. |
| Warning baselines | Warnings are grouped, but there is no accepted-baseline comparison, so you cannot yet ask "what is *new* since last week". |

---

## Where to write things down

**Write it into this repository**, as a Markdown file in one of two inboxes:

| What you have | Where |
| :--- | :--- |
| The plugin did something wrong — bad output, a crash, a disagreement with pytest | [`devguide/pending_bugs/`](pending_bugs/README.md) |
| The plugin should do something different — design input, a feature you need | [`devguide/pending_proposals/`](pending_proposals/README.md) |

If unsure, file it as a bug. Deciding it was really a design gap is easy;
noticing a lost bug report is not.

These directories are the inbox for cross-project input. A GitHub issue, a Slack
message, or a comment in a meeting will get lost; a file in the devguide gets
read when the next release is planned, and gets an identifier in
[`audit_action_register_2026-07-17.md`](audit_action_register_2026-07-17.md),
which is the single complete work queue for this project.

Each directory has a short README with the conventions. Rough notes are fine. We would rather have an unpolished
observation than a polished one you did not have time to write.

Two things that are always worth a file, even if they feel small:

- a run where you needed more than the receptor gave you;
- a case where the grouping was wrong.

---

## Why this suite

MolSysMT is the proving ground because it has the properties our tests cannot
fake: thousands of tests, doctests, reference tests, optional dependencies, GPU
requests with CPU fallbacks, twelve-worker xdist, large molecular fixtures, and
a real history of collection and conversion failures.

If the receptor is going to be wrong somewhere, it will be wrong there first.
That is the point of asking you.
