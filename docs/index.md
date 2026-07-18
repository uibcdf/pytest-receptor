# `pytest-receptor`

A pytest reporter for coding agents.

When pytest is driven by an agent such as Claude Code, Codex, or an autonomous
TDD loop, its output is read by something that pays for every token and cannot
scroll back. `pytest-receptor` renders the same run for that consumer: it says
what happened, groups repeated failures by root cause, and tells the agent
exactly what to re-run.

```{note}
**Pre-1.0.** The output format is this plugin's public API and it may still
change. The reliability floor will not: the receptor never reports an
unsuccessful or incomplete run as a success, and a failure inside the receptor
itself never costs you the run.
```

```{toctree}
---
maxdepth: 2
caption: "Contents:"
---
installation
usage
benchmarks
```

---

## In one command

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
spends 3,304 tokens on that run. This is 106.

The gap widens with the suite. On eight thousand tests under twelve workers, one
fixture breaking two hundred tests costs `pytest -q -n 12` **25,474 tokens** and
the receptor **114**.

---

## Profiles

* **`--receptor=human`** (default) — unchanged pytest. The plugin registers
  nothing, so output is byte-identical to not having it installed. Running
  plain `pytest` gets you this: installing the plugin changes nothing until you
  ask it to, which makes it safe to add to a shared environment.
* **`--receptor=llm`** — compact output for a coding agent. Root-cause grouping,
  the assertion diff without the source echo, and a rerun command per group.
  Everything you need is on stdout: no file to open, and never a second run.
* **`--receptor=ci`** — the same renderer with build-log defaults. Expands every
  group, because a CI runner is destroyed when the job ends.

## What it guarantees

* The verdict comes from pytest's exit status. An empty, interrupted, or
  fail-fast run can never render as a success.
* Grouping never discards which tests were affected.
* Nothing is ever recoverable only by running the suite again. The complete
  report is written to `.pytest_cache/d/receptor/last-run.txt` during the run, and
  detail is withheld only when that file exists to hold it.
* If the receptor raises, you get `RECEPTOR_ERROR`, the raw evidence, and
  pytest's original exit status.

## How much it helps

Agents run `pytest` plain, because that is the obvious command. Against that,
every scenario measured is cheaper — from 21% on a collection error to 97% on a
failure cascade. In a TDD loop that runs the suite twenty times, the cascade case
alone is sixty thousand tokens you were not getting anything for.

Against a pytest you have already tuned with `-q --no-header --tb=short` the
margin narrows, and on two small scenarios the receptor costs about a dozen
tokens more. Both tables are published rather than only the flattering one.

You can measure that directly rather than guessing:

```bash
pytest --receptor=llm --receptor-stats
```

pytest renders its quiet baseline into a temporary file during the same run and
the result is reported as a net token count and a percentage. The
[benchmarks](benchmarks.md) page publishes the full table, including the two
scenarios where the receptor costs slightly more and why.
