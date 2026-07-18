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

| Scenario | pytest (default) | quiet pytest | `--tb=line` | `--receptor=llm` | Change |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Cascade (38 failures, one cause) | 3279 | 2863 | 1989 | **101** | -96.5% |
| Green with warnings | 167 | 93 | 93 | **20** | -78.5% |
| Five distinct causes | 385 | 316 | 243 | **181** | -42.7% |
| Green suite (128 tests) | 97 | 23 | 23 | **16** | -30.4% |
| Single assertion failure | 331 | 197 | 230 | **162** | -17.8% |
| Collection error | 273 | 198 | 198 | **215** | +8.6% |
| Mixed states (skip, xfail, xpass) | 103 | 31 | 31 | **44** | +41.9% |

Environment for the run above:

- python 3.13.14, pytest 9.1.1, pytest-receptor 0.6.0
- tokenizer: `tiktoken` `cl100k_base`
- platform: Linux 6.17, glibc 2.39
- baseline: `pytest -q --no-header --tb=short`

---

## Reading the table

**The receptor is smaller than `--receptor=human` in every scenario above.**
That is worth stating plainly, because the negative rows invite the opposite
conclusion. They are negative against *quiet* pytest, not against the default
output you would otherwise be reading. On the mixed-state run: 148 tokens for
default pytest, 26 for quiet pytest, 39 for the receptor.

**Percentages mislead at the bottom of the table.** Read the negative rows in
absolute terms: +46.2% on a mixed-state run is *thirteen tokens*, and +8.6% on a
collection error is seventeen. Those are rounding errors in any real context
window.

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
seven tokens. The 96.5% on the cascade is 2,762. Same plugin, four orders of
magnitude apart in value, and the difference is entirely down to how your
failures cluster.

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
