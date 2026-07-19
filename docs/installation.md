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

## From PyPI

```bash
pip install pytest-receptor
```

Or with your dependency manager of choice:

```bash
poetry add --group dev pytest-receptor
pdm add -d pytest-receptor
uv pip install pytest-receptor
pipenv install --dev pytest-receptor
```

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
pip uninstall pytest-receptor
```

Nothing is left behind except `.pytest_cache/d/receptor/`, which you can delete.
