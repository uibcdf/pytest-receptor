# Benchmarks

Reproduce everything here:

```bash
python devtools/benchmarks/run_benchmarks.py            # the tables below
python devtools/benchmarks/run_benchmarks.py --scale    # 8,000 tests, 12 workers
```

Subprocesses run with colour disabled, so figures do not change with your shell.

## Two baselines

| Baseline | Why it is here |
| :--- | :--- |
| `pytest` | What an agent actually runs. Banner, progress bar, source of every failing test. |
| `pytest -q --no-header --tb=short` | A pytest already tuned by someone who thought about it. The comparison a published claim should survive. |

`pytest -q --tb=line` appears as a third column: the other common choice, though
it discards the assertion diff and is not really comparable in usefulness.

## At scale

8,000 tests, twelve xdist workers, `cl100k_base`:

| Scenario | `pytest -n 12` | `pytest -q -n 12` | `--receptor=llm -n 12` | Saving |
| :--- | ---: | ---: | ---: | ---: |
| Whole suite green | 904 | 812 | **17** | 97.9% |
| One fixture breaks 200 tests | 25,769 | 25,681 | **107** | 99.6% |
| Six unrelated bugs | 1,595 | 1,503 | **278** | 81.5% |

`-q` does not save you: it still prints one progress character per test, so a
*successful* 8,000-test run costs 812 tokens of dots.

## Small scenarios

| Scenario | `pytest` | tuned pytest | `--tb=line` | `--receptor=llm` | Change |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Cascade (38 failures, one cause) | 3300 | 2863 | 1989 | **105** | -96.3% |
| Green with many distinct warnings | 1692 | 1598 | 1598 | **664** | -58.4% |
| Green with warnings | 181 | 87 | 87 | **45** | -48.3% |
| Five distinct causes | 405 | 316 | 213 | **211** | -33.2% |
| Green suite (128 tests) | 118 | 23 | 23 | **15** | -34.8% |
| Single assertion failure | 349 | 197 | 222 | **165** | -16.2% |
| Collection error | 286 | 192 | 192 | **213** | +10.9% |
| Mixed states (skip, xfail, xpass) | 124 | 31 | 31 | **77** | +148.4% |

`Change` compares against tuned pytest, the strict baseline.

## Across tokenizer families

Against plain `pytest`, so a claim is not an artifact of one vendor's
vocabulary:

| Scenario | `cl100k_base` | `o200k_base` | `p50k_base` | `r50k_base` |
| :--- | ---: | ---: | ---: | ---: |
| Cascade (38 failures, one cause) | -96.8% | -96.9% | -96.9% | -96.7% |
| Green suite (128 tests) | -87.3% | -87.5% | -89.8% | -89.8% |
| Green with warnings | -75.1% | -75.3% | -78.9% | -80.6% |
| Green with many distinct warnings | -60.8% | -60.9% | -64.2% | -65.7% |
| Single assertion failure | -52.7% | -53.1% | -54.2% | -59.9% |
| Five distinct causes | -47.9% | -46.4% | -50.3% | -56.3% |
| Collection error | -25.5% | -25.9% | -23.2% | -14.5% |

The cascade sits between -96.7% and -96.9% across all four. Older encodings are
consistently more favourable, spending more tokens on the punctuation-heavy
decoration the receptor removes.

## Reading the tables

**The two positive rows are real, and small.** +148% on a four-test mixed-state
run is 46 tokens; +10.9% on a collection error is 21. At that size any fixed
overhead looks enormous as a percentage.

**They buy something.** The reason behind every skip and xfail, and the name of
the test that passed unexpectedly. `pytest -q` says `1 skipped, 1 xfailed,
1 xpassed` and leaves you to re-run with `-rs` to learn which — the expensive
outcome. Those sections are bounded by the *variety* of reasons, not the number
of tests: four hundred skips across three reasons still cost three lines.

**The saving is concentrated, not uniform.** 34.8% on a green run is eight
tokens. 96.3% on the cascade is 2,758. Same plugin, three orders of magnitude
apart, and the difference is how your failures cluster.

**Against plain `pytest` every row is negative.** Including the two that cost
more against a tuned one.

## What these numbers do not measure

Output size is the easy metric. The one that matters is whether the consumer can
identify the root cause and the exact rerun target from the first response,
without another pytest invocation or a series of file reads.

That needs a corpus of real failures rather than synthetic scenarios. The first
data point exists — a MolSysMT development cycle diagnosed and fixed from the
compact report alone — but one cycle is not a measurement.

```{note}
These scenarios have been wrong twice, both times by exercising the wrong axis.
`Green with warnings` emitted the *same* warning forty times, so it could not
detect that only three of sixty groups were being reported on a real suite. Its
replacement then varied warnings by number, and numeric normalization collapsed
them back into one group. A scenario that tests volume does not test variety.
```
