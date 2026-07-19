# pytest-receptor

A pytest reporter for coding agents.

When pytest is driven by an agent rather than read by a person, its output is
consumed by something that pays for every token and cannot scroll back.
`pytest-receptor` renders the same run for that consumer: it states what
happened, groups repeated failures by root cause, and gives the exact command to
re-run them.

```{note}
**Pre-1.0.** The output format is this plugin's public API and may still change.
The reliability floor will not: an unsuccessful or incomplete run is never
reported as a success, and a failure inside the receptor never costs you the run.
```

```{toctree}
---
maxdepth: 1
hidden:
---
installation
usage
reference
how-it-works
limitations
benchmarks
```

## Where to go

| If you want to… | Read |
| :--- | :--- |
| Install it | [Installation](installation.md) |
| Run it and read its output | [Usage](usage.md) |
| Look up an option, an outcome label, or an output field | [Reference](reference.md) |
| Understand what it does to pytest, and why | [How it works](how-it-works.md) |
| Know what it does **not** do | [Limitations](limitations.md) |
| See measured token costs, and how they were measured | [Benchmarks](benchmarks.md) |

## In thirty seconds

```console
$ pytest --receptor=llm

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

One broken fixture, thirty-eight failing tests, one root cause. Plain `pytest`
spends 3,308 tokens on that run; this is 106.

Installing the plugin changes nothing until you ask it to: the default profile
registers nothing at all, so plain `pytest` behaves exactly as it does without
it installed.
