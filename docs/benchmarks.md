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
| Cascade (38 failures, one cause) | 3304 | 2863 | 1989 | **106** | -96.3% |
| Green with warnings | 193 | 93 | 93 | **47** | -49.5% |
| Five distinct causes | 411 | 316 | 243 | **181** | -42.7% |
| Green suite (128 tests) | 125 | 23 | 23 | **16** | -30.4% |
| Single assertion failure | 354 | 197 | 227 | **167** | -15.2% |
| Collection error | 293 | 195 | 195 | **217** | +11.3% |
| Mixed states (skip, xfail, xpass) | 131 | 31 | 31 | **44** | +41.9% |

The `Change` column compares against tuned pytest, the strict baseline.

### Across tokenizer families

A saving measured with one vocabulary can be an artifact of that vocabulary.
Byte-pair encodings differ enough that the same text varies by thirty percent
between them, so the comparison against plain `pytest` is repeated across four:

| Scenario | `cl100k_base` | `o200k_base` | `p50k_base` | `r50k_base` |
| :--- | ---: | ---: | ---: | ---: |
| Cascade (38 failures, one cause) | -96.8% | -96.9% | -96.9% | -96.7% |
| Green suite (128 tests) | -87.2% | -87.4% | -89.6% | -89.7% |
| Green with warnings | -75.6% | -75.8% | -79.5% | -80.2% |
| Mixed states (skip, xfail, xpass) | -66.4% | -66.9% | -66.7% | -75.5% |
| Five distinct causes | -56.0% | -54.8% | -58.5% | -64.5% |
| Single assertion failure | -52.8% | -53.1% | -54.2% | -58.9% |
| Collection error | -25.9% | -26.2% | -23.7% | -15.2% |

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

**Percentages mislead at the bottom of the table.** Read the positive rows in
absolute terms: +41.9% on a mixed-state run is *thirteen tokens*, and +11.3% on
a collection error is twenty-two. Those are rounding errors in any real context
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
seven tokens. The 96.3% on the cascade is 2,757. Same plugin, three orders of
magnitude apart in value, and the difference is entirely down to how your
failures cluster.

The `Green with warnings` row moved from -78.5% to -49.5% when warning grouping
landed: naming the groups costs tokens that counting them did not. That is the
trade being made deliberately, and it is left visible rather than reverted.

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
