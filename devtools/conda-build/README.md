# Publishing pytest-receptor to Conda

pytest-receptor follows the shared MolSysSuite publication shape for pure-Python
packages: one exact candidate, one `noarch: python` artifact, staging before release,
structured producer evidence, and a separate promotion decision.

## Version identity

The Git tag is the only version source. `versioningit` derives the installed Python
version and `conda-build` reads the same tag through `GIT_DESCRIBE_TAG`. The workflow
checks that the requested commit is exact and that the derived version equals the
requested semantic version before it builds anything.

The reviewed version/build live in `release_plan.toml`; `resources.toml`
declares all Python modules, the generated `_version.py` and the installed
gate. The shared publisher freezes that version only in its ephemeral build
checkout. Source and PyPI versions continue to derive from the immutable tag.

For a manual staging run, the workflow creates the requested tag only inside its runner
checkout when that tag does not yet exist. It does not push a tag or create a GitHub
Release. If the tag already exists, it must resolve to the requested commit.

## Stage an exact candidate

From a clean, pushed candidate commit:

```bash
git rev-parse HEAD
gh workflow run build_and_upload_conda_packages.yaml \
  -f candidate_sha=FULL_40_CHARACTER_SHA \
  -f version=1.2.1
```

The manual path always uploads to `uibcdf/label/staging`. `build_number` starts at zero
and changes only when a defective artifact for the same version must be superseded.
Both values must be committed in the reviewed plan before building.

Inspect the run first with gh-run-receptor and fall back to native GitHub inspection if
the report is incomplete:

```bash
gh run-receptor inspect RUN_ID --repo uibcdf/pytest-receptor --receptor=llm
gh run view RUN_ID --repo uibcdf/pytest-receptor --json status,conclusion,jobs
```

Then verify registry presence and digest independently. Dispatch the installed
gate at a ref resolving to the candidate, using the exact filename and digest:

```bash
gh workflow run test_installed_conda.yaml --ref CANDIDATE_REF \
  -f candidate_sha=FULL_40_CHARACTER_SHA \
  -f filename=pytest-receptor-1.2.1-py_0.tar.bz2 \
  -f sha256=FULL_64_CHARACTER_STAGING_DIGEST
```

## Promote a released package

Public publication does not rebuild or re-upload a staged coordinate. After the GitHub
Release exists and all of its gates pass, dispatch `promote_conda_package.yaml` with the
full release commit, version, existing installed run ID, and SHA-256 returned
by the independent staging query:

```bash
gh workflow run promote_conda_package.yaml \
  -f candidate_sha=FULL_40_CHARACTER_RELEASE_SHA \
  -f version=1.2.1 \
  -f sha256=FULL_64_CHARACTER_STAGING_DIGEST \
  -f installed_run_id=EXACT_COMPLETED_INSTALLED_RUN_ID
```

The pinned shared workflow binds the candidate to the committed plan and native
CI, verifies every declared installed job/step for that exact digest, promotes
the same file and independently checks both public registry and solver index.
It retains all receipts and preserves staging. Never use `--force`: labels
share one underlying file identity, so rebuilding the coordinate either
conflicts or risks replacing verified bytes.

All shared units are pinned to full MolSysSuite commits. The local installed
wrapper calls the provider's validation tools and adds the integration-test
dependencies absent from its common workflow, tracked in
`uibcdf/molsyssuite#77`. The descriptor requires all Linux/macOS arm64 and
Python 3.11–3.14 cells in the current plan. Actual run results and the release
decision belong to `uibcdf/pytest-receptor#32`.

## Why there is no platform matrix

The package is pure Python. One `noarch: python` artifact carries a
platform-independent payload, with a `python >=3.11,<3.15` runtime constraint.
Creating per-platform duplicates would cost time without adding coverage.
That package format alone does not prove installed runtime compatibility.
The source-test matrix covers all supported Python/pytest pairs on Linux
and representative Python 3.13 / pytest 8 and 9 runs on macOS arm64; Intel
macOS is outside the supported boundary. Windows runtime behavior is not
covered by the current hosted matrix. A release's actual installed-package
checks remain separate evidence; see [`docs/compatibility.md`](../../docs/compatibility.md).

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
