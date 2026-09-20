# Publishing pytest-receptor to Conda

pytest-receptor follows the shared MolSysSuite publication shape for pure-Python
packages: one exact candidate, one `noarch: python` artifact, staging before release,
structured producer evidence, and a separate promotion decision.

## Version identity

The Git tag is the only version source. `versioningit` derives the installed Python
version and `conda-build` reads the same tag through `GIT_DESCRIBE_TAG`. The workflow
checks that the requested commit is exact and that the derived version equals the
requested semantic version before it builds anything.

For a manual staging run, the workflow creates the requested tag only inside its runner
checkout when that tag does not yet exist. It does not push a tag or create a GitHub
Release. If the tag already exists, it must resolve to the requested commit.

## Stage an exact candidate

From a clean, pushed candidate commit:

```bash
git rev-parse HEAD
gh workflow run build_and_upload_conda_packages.yaml \
  -f candidate_sha=FULL_40_CHARACTER_SHA \
  -f version=1.1.0 \
  -f build_number=0
```

The manual path always uploads to `uibcdf/label/staging`. `build_number` starts at zero
and changes only when a defective artifact for the same version must be superseded.

Inspect the run first with gh-run-receptor and fall back to native GitHub inspection if
the report is incomplete:

```bash
gh run-receptor inspect RUN_ID --repo uibcdf/pytest-receptor --receptor=llm
gh run view RUN_ID --repo uibcdf/pytest-receptor --json status,conclusion,jobs
```

Then verify registry presence independently and install the exact artifact in a clean
environment. The producer evidence proves what the action observed; it does not prove
Anaconda.org state.

```bash
conda search -c uibcdf/label/staging --override-channels pytest-receptor=1.1.0
conda create -n pytest-receptor-candidate \
  -c uibcdf/label/staging -c conda-forge \
  python=3.14 pytest-receptor=1.1.0
conda run -n pytest-receptor-candidate pytest --receptor=llm --help
```

## Publish a released package

The `release` event uses the same workflow and recipe, but uploads to `main`. It accepts
only a three-part semantic-version tag and checks that the checkout resolves exactly to
that tag. Publish the GitHub Release only after the repository's complete release gates
pass; do not use a public release to test a candidate.

## Why there is no platform matrix

The package is pure Python. One `noarch: python` artifact installs on Linux, macOS, and
Windows. Its `python >=3.11,<3.15` runtime constraint makes that same artifact usable on
Python 3.11 through 3.14. Creating per-platform duplicates would cost time without adding
coverage. Cross-platform behavior belongs in the test matrix, while Conda publication
proves the single reusable artifact.

## Local diagnostic build

For recipe development, check out or create an exact local tag and disable automatic
upload:

```bash
conda config --set anaconda_upload no
conda build devtools/conda-build
```

The recipe imports the package, compares distribution and module versions against
`PKG_VERSION`, and asks pytest to load its help. Local builds are evidence about the
recipe, not permission to publish.
