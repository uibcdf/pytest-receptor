# Devtools

This folder provides the conda environment definitions and the conda-build
recipe used to publish `pytest-receptor` to the `uibcdf` channel.

## Create the build environment

```bash
conda env create -f devtools/conda-envs/build_env.yaml -n pytest-receptor-build
conda activate pytest-receptor-build
```

## Build and publish the conda package

The recipe takes the version from the git tag, so tag the release commit first.
Full upload flow in [`conda-build/README.md`](conda-build/README.md):

```bash
git tag 0.6.0
conda build devtools/conda-build
```

## Platform and Python coverage

The recipe is `noarch: python`: because the plugin is pure Python with no compiled
extensions, a single `conda build` produces one architecture-independent package
that installs on **linux, osx and win**, and the `python >=3.11,<3.14` run
constraint makes that same package valid on **Python 3.11, 3.12 and 3.13**. There
is no build matrix and nothing per-platform to publish.

## Versioning

The version has a single source of truth: the git tag. `versioningit` derives it
at build time and writes `pytest_receptor/_version.py` (gitignored); the conda
recipe reads the same tag through `GIT_DESCRIBE_TAG`. Nothing is edited by hand —
this matches the rest of the UIBCDF suite (`argdigest`, `pyunitwizard`).

## Benchmarks

Token/output benchmarks and the separate wall-time/peak-RSS benchmark live in
`benchmarks/`:

```bash
python devtools/benchmarks/run_benchmarks.py
python devtools/benchmarks/run_performance.py
```

The performance harness uses a unique temporary directory, disables unrelated
third-party plugins, and removes it after the run, so concurrent invocations do
not interfere.
