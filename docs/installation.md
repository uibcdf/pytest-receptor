# Installation

## Requirements

| | |
| :--- | :--- |
| Python | 3.11, 3.12, or 3.13 |
| pytest | 8.0 or later |
| Anything else | Nothing. The plugin has no dependency beyond pytest. |

Every combination of those Python and pytest versions is exercised in CI,
serially and under `pytest-xdist`, so the support claim is evidence rather than
intent.

## From conda (uibcdf channel)

The published package lives on the UIBCDF Anaconda channel:

```bash
conda install -c uibcdf pytest-receptor
```

## From PyPI (planned)

Version 1.0 is planned as the first PyPI release. Its package metadata already
declares pytest's `pytest11` entry point and `Framework :: Pytest` classifier,
so installation will make pytest discover it automatically:

```bash
pip install pytest-receptor
```

The official pytest plugin list is generated from PyPI project names beginning
with `pytest-` or `pytest_`; it is informational rather than an endorsement.
The package is not on PyPI yet — until 1.0, use conda (above) or install from
source.

## From source

```bash
git clone https://github.com/uibcdf/pytest-receptor.git
cd pytest-receptor
pip install -e .[dev]
```

## Optional extra

`tiktoken` is used by `--receptor-stats` to count tokens exactly. Without it the
flag still works and falls back to a labelled four-characters-per-token
approximation.

```bash
pip install tiktoken
```

## Installing it changes nothing

The default profile is `human`, and `human` registers no plugin at all — plain
`pytest` produces output byte-identical to not having the receptor installed.

This matters in a shared environment: you can install it for yourself, or for an
agent, without altering what anyone else sees. A regression test asserts the
byte-for-byte equivalence.

## Removing it

```bash
conda remove pytest-receptor   # or: pip uninstall pytest-receptor, if installed from source
```

Nothing is left behind except `.pytest_cache/d/receptor/`, which you can delete.
