# Instructions

The version is taken from the git tag (`GIT_DESCRIBE_TAG`), so the tag must exist
before building. Tag the release commit first, e.g. `git tag 0.6.0`.

## Conda packages required

```bash
conda install anaconda-client conda-build
```

## Building and pushing to https://anaconda.org/uibcdf

```bash
conda config --set anaconda_upload no
conda build .
PACKAGE_OUTPUT=`conda build . --output`
anaconda login
anaconda upload --user uibcdf $PACKAGE_OUTPUT --label main  # label: main, dev, tests
conda build purge
anaconda logout
```

## Install

```bash
conda install -c uibcdf pytest-receptor
```

## Additional Info

https://docs.anaconda.com/anaconda-cloud/user-guide/tasks/work-with-packages
