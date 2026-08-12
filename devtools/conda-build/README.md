# Releasing pytest-receptor to the `uibcdf` conda channel

This is the exact, verified process used for `0.6.0`. For the coordinated 1.0.0
publication order and evidence checklist, start with
`../../devguide/roadmap_to_1.0_publication.md`; this remains the conda-specific
runbook.

## The one rule: the version is the git tag

There is no version written by hand anywhere. `versioningit` derives it from the
git tag at build time, and `conda-build` reads the same tag through
`GIT_DESCRIBE_TAG` (see `meta.yaml`). So the release starts by tagging, and
everything downstream follows from that.

Version bumps follow Semantic Versioning. The next planned release is `1.0.0`;
after a public immutable release, corrections use a new patch version such as
`1.0.1`.

## Prerequisites

The build/upload tools:

```bash
conda install -c conda-forge conda-build anaconda-client
# or: conda env create -f devtools/conda-envs/build_env.yaml -n pytest-receptor-build
```

This machine is already authenticated against `anaconda.org` as the `uibcdf`
account, so `anaconda upload` works without a login step. On a machine that is
**not** authenticated, run `anaconda login` first (it needs a real terminal —
from Claude Code, type `! anaconda login`).

> Note: the `anaconda` CLI here is the unified client (v0.7.x), not the classic
> `anaconda-client`. `anaconda upload` behaves as below; `anaconda whoami` may
> prompt for a destination and fail without a TTY — that is cosmetic and does not
> affect uploading.

## Step 1 — tag the release commit and push the tag

`main` must be committed and clean; the commit you tag is the release.

```bash
git tag -a 0.6.0 -m "pytest-receptor 0.6.0"
git push origin 0.6.0
```

Confirm the tree resolves to a clean version (no `+distance`/`.dirty` suffix):

```bash
python -m versioningit .        # -> 0.6.0
git describe --tags --long      # -> 0.6.0-0-g<sha>
```

## Step 2 — build (no auto-upload)

```bash
conda config --set anaconda_upload no
conda build devtools/conda-build
```

The output is one **noarch** package — architecture-independent, so a single
build serves linux, osx and win, and the `python >=3.11,<3.14` run constraint
makes it valid on Python 3.11, 3.12 and 3.13. There is no build matrix. The
artifact path:

```bash
conda build devtools/conda-build --output
# .../conda-bld/noarch/pytest-receptor-0.6.0-py_0.conda
```

The recipe's own test phase (`pytest --help`, importing `pytest_receptor`) runs
during the build; a green build means the package imports and the plugin loads.

## Step 3 — upload to the `uibcdf` channel

```bash
PKG=$(conda build devtools/conda-build --output)
anaconda upload --user uibcdf "$PKG" --label main   # labels: main, dev, tests
```

A successful upload prints `Upload complete` and the channel URL
`https://anaconda.org/uibcdf/pytest-receptor`.

## Step 4 — verify it is live

```bash
conda search -c uibcdf --override-channels pytest-receptor
# pytest-receptor   0.6.0   py_0   uibcdf
```

## Step 5 — clean up

```bash
conda build purge
```

## Installing (what users run)

```bash
conda install -c uibcdf pytest-receptor
```

## Additional info

https://docs.anaconda.com/anacondaorg/user-guide/packages/
