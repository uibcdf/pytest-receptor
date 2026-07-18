# Warning Group Truncation Is Not Diagnostically Sufficient

**Reported:** 2026-07-18  
**Pilot:** MolSysMT shadow evaluation  
**Category:** Diagnostic sufficiency

## Summary

On MolSysMT's complete green suite, pytest-receptor reports the correct total
warning count and number of groups but renders only three of sixty groups:

```text
PASS exit=0 | 9332 passed, 2 skipped | 519.94s | 216 warnings

warnings: 216 in 60 groups
  UnknownAtomNameWarning x50 | argdigest/core/decorator.py:376 | ...
  GpuNotAvailableWarning x18 | argdigest/core/decorator.py:376 | ...
  UnitStrippedWarning x10 | molsysmt/basic/compare.py:255 | ...
  +57 more groups
```

The verdict and aggregate counts agree with pytest. The problem is that an
agent cannot determine whether any of the hidden groups is new, actionable, or
scientifically important without opening the on-disk report or rerunning with
different output. Under the MolSysMT pilot's stated sufficiency rule, that
additional read is a design failure.

## Environment and command

- Python 3.13.12
- pytest 9.0.2
- pytest-receptor 0.6.0, editable installation
- command:
  `python -m pytest --receptor=llm --receptor-stats -n 12`
- MolSysMT addopts:
  `--doctest-modules -q --import-mode=importlib`

## Why the hidden groups matter

MolSysMT uses warnings for several materially different categories:

- GPU fallback and environmental capability;
- unit stripping and scientific data handling;
- malformed or unknown chemical identifiers;
- optional third-party format behavior;
- memory-pressure and scalability signals;
- deprecations that affect the Python 3.11-3.13 support window.

A total of 216 warnings is not itself actionable. The group identities are the
information needed to decide whether the run is acceptable. Showing only the
three most frequent groups biases the report toward known repetitive warnings
and can hide a single novel warning, which is often the most valuable one.

This run already demonstrates that frequency is not a sufficient priority
rule: 57 lower-frequency groups disappear from stdout.

## Expected behavior

The compact report should remain sufficient to identify every distinct warning
group without requiring another file read. Possible designs include:

1. render one compact line for every group, since grouping has already bounded
   repetition;
2. always render novel or singleton groups and summarize only groups matching
   an explicit accepted baseline;
3. allow a repository policy to classify accepted warning fingerprints, then
   render accepted totals compactly and every unrecognized group in full;
4. if a hard safety bound is necessary, expose a clearly copyable command or
   mode that expands warnings, while acknowledging that the first-run output
   remains insufficient under the current pilot contract.

The second or third option is likely the best long-term fit for a mature
scientific suite: frequency and novelty are different signals.

## Measured context

The full green run compressed from an estimated 10,372 tokens for configured
pytest to 386 tokens for the receptor, saving 9,986 tokens (96.3%). This is a
large and useful gain. Rendering 57 additional one-line warning fingerprints
would consume part of that saving but would still be far smaller than ordinary
pytest output and would make the result operationally trustworthy.

The stats used the labelled four-characters-per-token approximation because
`tiktoken` is not installed in the MolSysMT environment.

## Suggested regression coverage

Create warning sets where:

- one new singleton is mixed with many high-frequency accepted warnings;
- warning groups exceed the display threshold;
- the same warning arises from different local call sites;
- warnings differ only by array shapes, paths, or device identifiers;
- an accepted-warning baseline is absent, present, or stale.

Assert that the report never hides an unrecognized warning group behind a
frequency summary when stdout is intended to be diagnostically sufficient.

---

## Resolution

**Fixed 2026-07-18.** All warning groups are now listed. The report is right
that ranking by frequency is backwards: a group appearing once is the one most
likely to be new, so truncating by count hides exactly what is worth seeing.

The cost is real and was measured rather than assumed. On a synthetic run of
9,321 tests emitting 321 warnings in 60 groups, the output grows from 90 tokens
to 1,110 -- against 8,150 for `pytest -q`, so still an 86.4% reduction, and now
sufficient without a second read.

This is the same mistake made earlier with root causes, in a place it had not
been noticed: withholding on top of grouping saves little, and the saving is
worthless if acting on the report then requires opening a file. The section is
bounded by how many *kinds* of warning a suite emits, not by how many tests it
has.
