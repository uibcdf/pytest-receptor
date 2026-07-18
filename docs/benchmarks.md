# Benchmarks

## What is being compared

Two baselines matter, for different reasons, so both are published.

**`pytest`, plain.** This is what actually happens. An agent told to run the
tests runs `pytest`, and reads a platform banner, a `rootdir` line, a plugin
list, a progress bar, and the full source of every failing test. This is the
comparison that describes real token spend.

**`pytest -q --no-header --tb=short`.** A pytest already tuned by someone who
thought about it, still showing the assertion diff. This is the comparison a
published claim should have to survive, because picking the chatty default as an
opponent would inflate every figure. `pytest -q --tb=line` appears as a third
column as the other common choice, though it discards the diff and so is not
really comparable in usefulness.

An earlier version of this page quoted only savings against the default and
described them as though they held generally. They did not.

Reproduce everything on your own machine:

```bash
python devtools/benchmarks/run_benchmarks.py
```

---

## Results

Headline comparison, `cl100k_base`:

| Scenario | `pytest` | tuned pytest | `--tb=line` | `--receptor=llm` | Change |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Cascade (38 failures, one cause) | 3308 | 2863 | 1989 | **106** | -96.3% |
| Green with many distinct warnings | 1946 | 1846 | 1846 | **669** | -63.8% |
| Green with warnings | 189 | 91 | 91 | **46** | -49.5% |
| Five distinct causes | 411 | 316 | 243 | **212** | -32.9% |
| Green suite (128 tests) | 126 | 23 | 23 | **16** | -30.4% |
| Single assertion failure | 354 | 197 | 227 | **167** | -15.2% |
| Collection error | 295 | 196 | 196 | **218** | +11.2% |
| Mixed states (skip, xfail, xpass) | 131 | 31 | 31 | **78** | +151.6% |

The `Change` column compares against tuned pytest, the strict baseline.

The `Green with many distinct warnings` row is there because of a defect the
benchmarks failed to catch. Until a real pilot ran, the only warning scenario
here emitted the *same* warning forty times — one group — so it could not detect
that only three groups of sixty were being reported on a real suite. A scenario
that exercises variety rather than volume now sits beside it.

### At the scale that matters

The scenarios above are small — at most 128 tests — and they understate the
saving badly, because the fixed cost of pytest's decoration is amortized while
the repeated cost is not. Measured on eight thousand tests under twelve xdist
workers, against a pytest that has *already* been quietened:

| Scenario | `pytest -n 12` | `pytest -q -n 12` | `--receptor=llm -n 12` | Saving |
| :--- | ---: | ---: | ---: | ---: |
| Whole suite green | 910 | 812 | **24** | 97.0% |
| One fixture breaks 200 tests | 25,579 | 25,474 | **114** | 99.6% |
| Six unrelated bugs | 1,595 | 1,497 | **285** | 81.0% |

Reproduce with `python devtools/benchmarks/run_benchmarks.py --scale`.

Two things are worth reading twice.

**`-q` does not help much.** It removes the header and the summary, but it still
prints one progress character per test. At eight thousand tests that is 812
tokens of dots on a run where *nothing went wrong*, paid on every iteration of
every loop.

**The cascade figure is not a typo.** One broken fixture failing two hundred
tests makes `-q` print two hundred tracebacks, most of them the same text: 25,474
tokens. The receptor prints the cause once, names the affected tests, and gives
the command to re-run them, in 114.

That 99.6% is also the number most at risk from a careless change. It depends on
one cause rendering once regardless of how many tests it broke, and a refactor
once merged "expand every cause" with "list every occurrence" and pushed it back
to 2,079 without failing a single test. There is now a budget test guarding it.

### Across tokenizer families

A saving measured with one vocabulary can be an artifact of that vocabulary.
Byte-pair encodings differ enough that the same text varies by thirty percent
between them, so the comparison against plain `pytest` is repeated across four:

| Scenario | `cl100k_base` | `o200k_base` | `p50k_base` | `r50k_base` |
| :--- | ---: | ---: | ---: | ---: |
| Cascade (38 failures, one cause) | -96.8% | -96.9% | -96.9% | -96.7% |
| Green suite (128 tests) | -87.2% | -87.4% | -89.6% | -89.7% |
| Green with warnings | -75.9% | -76.0% | -79.6% | -81.1% |
| Green with many distinct warnings | -65.6% | -65.6% | -68.5% | -69.7% |
| Single assertion failure | -53.1% | -53.5% | -54.2% | -58.9% |
| Five distinct causes | -48.2% | -46.6% | -50.7% | -56.5% |
| Collection error | -26.3% | -26.5% | -23.7% | -15.2% |

The headline holds. The cascade sits between -96.7% and -96.9% across all four,
so it is a property of the output rather than of GPT-4's tokenizer. The older
encodings (`p50k_base`, `r50k_base`) are consistently *more* favourable, because
they spend more tokens on the punctuation-heavy decoration the receptor removes.

Note that every row is negative here. Against plain `pytest` — which is what an
agent actually runs — the receptor is cheaper in every scenario measured,
including the two that cost more against a tuned pytest.

Environment for the run above:

- python 3.13.14, pytest 9.1.1, pytest-receptor 0.6.0
- tokenizer: `tiktoken`, four encodings
- platform: Linux 6.17, glibc 2.39
- strict baseline: `pytest -q --no-header --tb=short`

---

## Reading the table

**The receptor is smaller than `--receptor=human` in every scenario above.**
That is worth stating plainly, because the negative rows invite the opposite
conclusion. They are negative against *quiet* pytest, not against the default
output you would otherwise be reading. On the mixed-state run: 148 tokens for
default pytest, 26 for quiet pytest, 39 for the receptor.

**Percentages mislead at the bottom of the table.** The mixed-state scenario is
four tests, a size at which any fixed overhead looks enormous as a percentage:
+151.6% is forty-seven tokens, and +11.1% on a collection error is twenty-two.

Those forty-seven buy the reason behind every skip and every xfail, and the name
of the test that passed unexpectedly. `pytest -q` reports `1 skipped, 1 xfailed,
1 xpassed` and leaves you to re-run with `-rs` to learn which — the expensive
thing. Both sections are bounded by the *variety* of reasons rather than the
number of tests, so four hundred skips across three reasons still cost three
lines.

Those thirteen tokens are also the whole difference between

```text
1 passed, 1 skipped, 1 xpassed
```

and the same line plus

```text
unexpected passes:
  test_mix.py::test_xp - known bug
```

`1 xpassed` tells you something passed unexpectedly. It does not tell you which
test or why, and you cannot act on it without both.

They are also not accidental. The receptor spends those tokens naming the tests
that passed unexpectedly and why; pytest reports `1 xpassed` and moves on. An
unexpected pass usually means a known bug was fixed and its `xfail` marker should
be removed — actionable information for thirteen tokens.

**The saving is concentrated, not uniform.** The 30% on a 128-test green run is
seven tokens. The 96.3% on the cascade is 2,757. Same plugin, three orders of
magnitude apart in value, and the difference is entirely down to how your
failures cluster.

The `Green with warnings` row moved from -78.5% to -50.0% when warning grouping
landed, and it is worth reading carefully rather than as a regression. The
receptor is still half the size of a tuned pytest and a quarter the size of a
plain one; it simply stopped being a *twentieth*. What the extra tokens buy is
that `12 warnings` becomes twelve warnings you can act on.

The scenario also flatters the cost. It is forty tests emitting warnings from a
single group, so the warning section is proportionally enormous. The section is
bounded by the number of *distinct* warnings, not by the size of the suite: a
suite of eight thousand tests with three distinct warnings pays three lines,
and only the first three groups are shown unless `--receptor-full` is passed.

So the practical conclusion is not "use it when your suite is red". Enabling it
costs nothing measurable in the worst case here and saves almost everything in
the best, which makes it worth leaving on. What varies is *how much* it helps,
and that is a property of your suite rather than of the plugin.

---

## Measuring your own suite

Rather than extrapolating from these synthetic scenarios:

```bash
pytest --receptor=llm --receptor-stats
```

```text
receptor stats: 38 tokens vs 148 for pytest as you configured it | 110 fewer (-74.3%) | cl100k_base
```

**That number will not match this page, and should not.** The table above uses a
deliberately strict baseline, because a published claim has no business choosing
a weak opponent. The flag uses *your* configuration untouched, because it answers
a personal question: against how you actually run pytest, what does this save
you? If you already run `pytest -q`, expect a much smaller figure than the table
suggests. If you run plain `pytest`, expect a larger one.

The baseline is measured, not estimated. During the same run pytest genuinely
renders into a temporary file, which is then tokenized and discarded. Your
terminal output is unchanged and nothing extra is accumulated in memory.

Both figures carry the same sign, and both are reported, because on small runs
only the net count means anything.

---

## What these numbers do not measure

Output size is the easy metric, not the important one. The measure that actually
matters is whether the agent can identify the root cause and the exact rerun
target from the first response, without another pytest invocation or a series of
file reads.

Measuring that requires a corpus of real failures rather than synthetic
scenarios, and it is planned work rather than something this page can currently
report. Until then, treat the table as evidence about cost and the grouping
behaviour described in the [usage guide](usage.md) as the argument about
usefulness.
