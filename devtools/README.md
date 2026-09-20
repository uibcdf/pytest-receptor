# Devtools

This folder provides the conda environment definitions and the conda-build
recipe used to publish `pytest-receptor` to the `uibcdf` channel.

## Create the build environment

```bash
conda env create -f devtools/conda-envs/build_env.yaml -n pytest-receptor-build
conda activate pytest-receptor-build
```

## Build and publish the conda package

The normal path is the `Build and upload conda packages` GitHub workflow. A
manual dispatch takes an exact candidate commit and semantic version, builds one
`noarch` artifact, and uploads only to the `staging` label. A GitHub Release
from an exact tag is the separate path that uploads to `main`. See the full
runbook in [`conda-build/README.md`](conda-build/README.md).

Local builds are diagnostic only. They require an exact local tag because both
`versioningit` and `conda-build` derive the version from Git:

```bash
conda build devtools/conda-build
```

## Platform and Python coverage

The recipe is `noarch: python`: because the plugin is pure Python with no compiled
extensions, a single `conda build` produces one architecture-independent package
that installs on **linux, osx and win**, and the `python >=3.11,<3.15` run
constraint makes that same package valid on **Python 3.11 through 3.14**. There
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
