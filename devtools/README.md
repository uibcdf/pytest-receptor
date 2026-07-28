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

## Versioning

The version has a single source of truth: the git tag. `versioningit` derives it
at build time and writes `pytest_receptor/_version.py` (gitignored); the conda
recipe reads the same tag through `GIT_DESCRIBE_TAG`. Nothing is edited by hand —
this matches the rest of the UIBCDF suite (`argdigest`, `pyunitwizard`).
