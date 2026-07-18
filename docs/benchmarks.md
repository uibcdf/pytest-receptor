# Benchmarks

## What is being compared

Token counts are only meaningful against a fair baseline. An earlier version of
this page compared the receptor against pytest's **default** output, which
includes a header, a platform banner, a progress bar, and the source code of
every failing test. Nobody driving pytest from an agent leaves those switched on,
so that comparison inflated every figure and told the reader nothing.

The figures below are measured against **`pytest -q --no-header --tb=short`**: a
pytest that has already been told to be quiet, and which still shows the
assertion diff. `pytest -q --tb=line` is included as a third column because it is
the other common choice, even though it discards the diff and so is not really
comparable in usefulness.

Reproduce everything on your own machine:

```bash
python devtools/benchmarks/run_benchmarks.py
```

---

## Results

| Scenario | pytest (default) | quiet pytest | `--tb=line` | `--receptor=llm` | Saving |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Cascade (38 failures, one cause) | 3279 | 2863 | 1989 | **101** | 96.5% |
| Green with warnings | 167 | 93 | 93 | **20** | 78.5% |
| Five distinct causes | 385 | 316 | 243 | **181** | 42.7% |
| Green suite (128 tests) | 97 | 23 | 23 | **16** | 30.4% |
| Single assertion failure | 331 | 197 | 230 | **162** | 17.8% |
| Collection error | 273 | 198 | 198 | **215** | -8.6% |
| Mixed states (skip, xfail, xpass) | 103 | 31 | 31 | **44** | -41.9% |

Environment for the run above:

- python 3.13.14, pytest 9.1.1, pytest-receptor 0.1.0
- tokenizer: `tiktoken` `cl100k_base`
- platform: Linux 6.17, glibc 2.39
- baseline: `pytest -q --no-header --tb=short`

---

## Reading the table

**Percentages mislead at the bottom of the table.** Read the negative rows in
absolute terms: -41.9% on a mixed-state run is *thirteen tokens*, and -8.6% on a
collection error is seventeen. Those are rounding errors in any real context
window.

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
receptor stats: 100 tokens vs 3205 for `pytest -q --no-header --tb=auto` | saved 3105 (+96.9%) | cl100k_base
```

The baseline is measured, not estimated. During the same run pytest genuinely
renders its quiet output into a temporary file, which is then tokenized and
discarded. Your terminal output is unchanged, and nothing extra is accumulated in
memory.

The reported baseline uses whichever traceback style you have configured, which
is why the label names it. Comparing under `--tb=short` reproduces the numbers in
the table above exactly.

Both figures are given as a net token count and a percentage, because on small
runs only the net count means anything.

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
