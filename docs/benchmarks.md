# Benchmarks

Reproduce everything here:

```bash
python devtools/benchmarks/run_benchmarks.py            # the tables below
python devtools/benchmarks/run_benchmarks.py --scale    # 8,000 tests, 12 workers
python devtools/benchmarks/run_performance.py --tests 1000 --repeat 5  # wall time and peak RSS
```

The token harness exclusively claims `${tempdir}/receptor-bench` so pytest's
displayed `rootdir` stays stable across measurements. If that path is occupied,
it refuses to run and preserves its contents. Wait for the active owner to finish;
remove leftovers only after checking their ownership and useful lifetime. It
removes its own scenario files after success or failure, and reports cleanup
errors. The performance harness uses a unique managed directory with the same
cleanup/error contract. These operations do not clean other callers' resources.
See [uibcdf/pytest-receptor#40](https://github.com/uibcdf/pytest-receptor/issues/40).

Reference measurements were repeated on 2026-10-03 using an installed 1.2.1
candidate wheel in a fresh Linux environment: CPython 3.13.14, pytest 9.1.1,
pytest-xdist 3.8.0 and tiktoken 0.14.0. The wheel was built locally from
`b8071ce13196b5b24d20b034676636c0a8fd8f4a`; it is measurement evidence,
not proof of registry publication. Saved [token](https://github.com/uibcdf/pytest-receptor/blob/main/devtools/benchmarks/last-run.json),
[scale](https://github.com/uibcdf/pytest-receptor/blob/main/devtools/benchmarks/last-scale.json) and
[runtime](https://github.com/uibcdf/pytest-receptor/blob/main/devtools/benchmarks/last-performance.json) results record versions,
source and harness hashes, and the installed dependency closure.

Subprocesses run with colour disabled. Token measurements retain normal plugin
autoload in that clean environment; banner size can change with installed
plugins. These conditions differ from the previous 0.6.0 token measurements,
so the tables do not establish performance changes between releases.

## Runtime and memory

The performance harness disables third-party plugin autoload, explicitly loads
Receptor, redirects output to `DEVNULL`, and measures each pytest child with
`wait4`. This separates renderer work from terminal I/O and attributes peak RSS
to the run being measured. Modes rotate order and the reported value is the
median after an unreported warm-up.

Local reference measurement on Linux, CPython 3.13.14, 1,000 tests, median of
five runs:

| Scenario | Mode | Wall time | Peak RSS | Time vs quiet | RSS vs quiet |
| :--- | :--- | ---: | ---: | ---: | ---: |
| green | pytest quiet | 0.987s | 39.2 MiB | baseline | baseline |
| green | receptor | 1.096s | 39.9 MiB | +11.0% | +0.8 MiB |
| green | receptor + JSONL | 1.264s | 40.1 MiB | +28.1% | +0.9 MiB |
| setup cascade | pytest quiet | 2.243s | 41.2 MiB | baseline | baseline |
| setup cascade | receptor | 2.634s | 43.1 MiB | +17.5% | +1.8 MiB |
| setup cascade | receptor + JSONL | 2.738s | 43.9 MiB | +22.1% | +2.7 MiB |

These are reference observations, not portable promises: CPU, filesystem,
pytest and Python affect time and RSS. The meaningful result is that the
measurement is reproducible and reports absolute values as well as percentages.

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
| Whole suite green | 887 | 812 | **17** | 97.9% |
| One fixture breaks 200 tests | 22,952 | 22,874 | **107** | 99.5% |
| Six unrelated bugs | 1,494 | 1,419 | **278** | 80.4% |

`-q` does not save you: it still prints one progress character per test, so a
*successful* 8,000-test run costs 812 tokens of dots.

## Small scenarios

| Scenario | `pytest` | tuned pytest | `--tb=line` | `--receptor=llm` | Change |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Cascade (38 failures, one cause) | 3283 | 2863 | 1989 | **105** | -96.3% |
| Green with many distinct warnings | 1675 | 1598 | 1598 | **664** | -58.4% |
| Green with warnings | 164 | 87 | 87 | **45** | -48.3% |
| Five distinct causes | 388 | 316 | 213 | **211** | -33.2% |
| Green suite (128 tests) | 101 | 23 | 23 | **15** | -34.8% |
| Single assertion failure | 332 | 197 | 222 | **165** | -16.2% |
| Collection error | 269 | 192 | 192 | **217** | +13.0% |
| Mixed states (skip, xfail, xpass) | 107 | 31 | 31 | **77** | +148.4% |

`Change` compares against tuned pytest, the strict baseline.

## Across tokenizer families

Against plain `pytest`, so a claim is not an artifact of one vendor's
vocabulary:

| Scenario | `cl100k_base` | `o200k_base` | `p50k_base` | `r50k_base` |
| :--- | ---: | ---: | ---: | ---: |
| Cascade (38 failures, one cause) | -96.8% | -96.9% | -96.9% | -96.7% |
| Green suite (128 tests) | -85.1% | -85.4% | -88.2% | -88.3% |
| Green with warnings | -72.6% | -72.7% | -77.0% | -79.1% |
| Green with many distinct warnings | -60.4% | -60.5% | -64.0% | -65.5% |
| Single assertion failure | -50.3% | -50.7% | -52.1% | -58.6% |
| Five distinct causes | -45.6% | -44.1% | -48.6% | -55.1% |
| Collection error | -19.3% | -19.6% | -18.3% | -9.4% |

The cascade sits between -96.7% and -96.9% across all four. Other rows vary with
tokenizer vocabulary; the collection-error row is less favourable under
`r50k_base`.

## Reading the tables

**The two positive rows are real, and small.** +148% on a four-test mixed-state
run is 46 tokens; +13.0% on a collection error is 25 tokens. At that size any fixed
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
