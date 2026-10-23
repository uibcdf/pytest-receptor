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
`noarch` artifact, and uploads only to the `staging` label. Conda publication
to `main` promotes that same tested archive through the separate promotion
workflow. A GitHub Release triggers the PyPI publisher. See the full
runbook in [`conda-build/README.md`](conda-build/README.md).

Local builds are diagnostic only. They require an exact local tag because both
`versioningit` and `conda-build` derive the version from Git:

```bash
conda build devtools/conda-build
```

## Platform and Python coverage

The recipe is `noarch: python`: because the plugin is pure Python with no compiled
extensions, a single `conda build` produces one architecture-independent
artifact. Installed qualification covers **Linux and macOS arm64** on
**Python 3.11 through 3.14**. The metadata constraint is `python >=3.11,<3.15`;
the noarch format alone does not establish Windows runtime support. There is
no per-platform build matrix; the installed test matrix remains required.

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

## Resource ownership and closeout

The operation-by-operation [resource review](../devguide/temporary_resources.md)
records scratch ownership, retained outputs, cleanup/error behavior, hosted
runner boundaries and explicit historical-path observations under
`uibcdf/pytest-receptor#42`. Use it when reviewing task resources or changing a
tool. Build outputs, evidence files, shared environments and other callers'
work are not interchangeable with disposable scratch.

## Reporting records

The issue-backed reporting validator is `devguide_reports.py`; regenerate or
check the developer-guide indexes with `python devtools/devguide_index.py` or
`python devtools/devguide_index.py --check` from the repository root. See
`devguide/reporting_protocol.md` for filing, closure and the retired legacy
archive exception. The empty manifest rejects new entries and has no expiry debt.
