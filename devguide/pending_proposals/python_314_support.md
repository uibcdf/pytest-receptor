# Verified Python 3.14 support

**Source:** UIBCDF development team, 2026-09-20.
**Tracking:** `PR-REL-008`, `uibcdf/pytest-receptor#3`, and
`uibcdf/molsyssuite#29`.

## Observation

The package metadata, Conda recipe, compatibility matrix, release verifier, and public
documentation currently stop at Python 3.13. This prevents pytest-receptor from serving as
the standard compact test reporter while MolSysSuite evaluates its libraries on Python
3.14.

The code itself passed an initial clean-environment feasibility measurement on Linux:

```text
CPython 3.14.7
pytest 9.1.1
pytest-xdist 3.8.0
pytest tests/ -n 12 --receptor=llm
PASS exit=0 | 172 passed | 9.37s
```

Installation used `--ignore-requires-python` because the current published contract is
still `>=3.11,<3.14`. That override is evidence scaffolding, not an installation
recommendation or support claim.

## Implementation

The first non-claiming lane passed in hosted run `35509547575`: all 11 jobs were green,
including Python 3.14 with both pytest 8 and pytest 9. MolSysSuite policy release
`policy-v1.2.0` then authorized this component to adopt the target range.

The implementation aligns package metadata, classifiers, the eight-cell compatibility
matrix, the release verifier, Conda recipe, public documentation, and changelog. Final
admission still requires the hosted required lane and clean wheel/Conda installation
without an override.

## Implementation evidence

On 2026-09-20, after aligning the contract:

- the complete Python 3.13 suite passed: 173 tests with 12 workers;
- a normal source installation on CPython 3.14.7, without
  `--ignore-requires-python`, passed the same 173 tests with 12 workers;
- Ruff lint and format checks passed;
- Python 3.14.7 built one wheel and one source distribution successfully;
- a separate Python 3.14 virtual environment installed the wheel and imported
  `pytest_receptor` from its own `site-packages`, not the checkout;
- installed metadata reported `Requires-Python: <3.15,>=3.11`; and
- the installed plugin exposed `pytest --receptor=llm --help` successfully.

The built development artifact carried a dirty, distance-derived version because this
evidence intentionally preceded the commit. It proves packaging shape and interpreter
metadata, not release identity. Hosted required CI subsequently passed all 11 jobs in run
`35512512809`, including both Python 3.14 cells.

An initial local Conda build then exposed a release-process gap: setting
`GIT_DESCRIBE_TAG=1.1.0` externally did not override the Git-derived value, so the recipe
correctly built and tested `1.0.0` rather than the intended candidate. The solver then
rejected the requested `1.1.0`. This is useful negative evidence: the package itself
loaded on Python 3.14, but the attempted command did not prove candidate identity.

The resolution begins with the shared MolSysSuite noarch publication pattern already used
by SMonitor and DepDigest. A manual workflow pins a full candidate SHA, creates an
ephemeral runner-local semantic-version tag, verifies `python -m versioningit`, builds one
artifact, uploads only to `staging`, and retains `events@1` producer evidence for
gh-run-receptor. The recipe also compares installed distribution and module versions with
Conda's `PKG_VERSION` during its own tests. Public delivery is a separate exact-file label
promotion, never a rebuild or overwrite.

A successful hosted staging build plus an independent clean Python 3.14 installation of
that exact staged artifact remain the final admission evidence.

Python 3.11 remains supported. The routine development interpreter remains Python 3.13
until the central policy decides otherwise.

## Promotion state

**Implementation verified 2026-09-20 (PR-REL-008, `uibcdf/pytest-receptor#3`),
public delivery pending.** Commit
`f2ff0e3` added the exact-commit, staging-first noarch Conda workflow and its local
contract tests. Ruff passed and the complete local suite passed 178 tests with 12 workers.

Hosted Conda run `35528151054` derived candidate version `1.1.0`, built and tested one
noarch package, uploaded it only to `uibcdf/label/staging`, and retained producer
evidence. gh-run-receptor independently interpreted the run as `PASS` with one of one
jobs and one available artifact. A separate channel query found
`pytest-receptor-1.1.0-py_0`; a clean CPython 3.14.7 environment installed it from
staging, imported distribution and module version `1.1.0` from `site-packages`, reported
`Requires-Python: <3.15,>=3.11`, and loaded `pytest --receptor=llm --help`.

This establishes a promotable candidate but not delivered Python 3.14 support. MolSysSuite
now reserves `admitted` for a public immutable release independently installed from every
claimed package channel. The component therefore remains `authorized` until release
`1.1.0` is published on GitHub and PyPI, the release workflow uploads the same source to
the public `uibcdf` Conda label, and clean Python 3.14 environments verify both package
indexes. No public tag, GitHub Release, PyPI artifact, or Conda `main` artifact was created
by the staging exercise.

Release candidate commit `14e996430fa2b3810ae68f8b7fed16298dc7733b` then passed the
complete 11-job hosted matrix in run `35532366589`. Exact tag `1.1.0` built one wheel and
one sdist; both passed strict metadata checks, and a clean CPython 3.14.7 environment
installed the wheel with `Requires-Python: <3.15,>=3.11`. The GitHub Release and PyPI
publication completed successfully in run `35532680937`.

The simultaneous Conda run `35532680623` revealed that rebuilding the staged `py_0`
coordinate for `main` is not promotion: Anaconda.org returned HTTP 409 because the file
identity already existed under `staging`. The failed run and its retained producer
evidence were preserved. Because `py_0` came from the earlier staging commit, it was not
silently relabeled. The exact release tag was instead built additively as `py_1` in run
`35533044229`. Independent channel metadata reports SHA-256
`4b56e6fc7c24e3f01d771c989bd7ed4bac9cf40c05e22f831a0ffff8defcd7dc`, and a clean Conda
environment installed that exact staged package on CPython 3.14.7 and loaded the plugin.

Provider issue `uibcdf/action-build-and-upload-conda-packages#43` produced release
`v2.2.0`: a reusable exact-file promotion subaction that verifies source identity and
digest, adds the target label without rebuilding, overwriting, or removing staging, and
then verifies the target postcondition. Pytest Receptor now separates staging build from
public promotion and retains an independently checked promotion receipt. Public Conda
promotion and clean installation from `uibcdf/main` are the remaining admission gates.

**Guard:** `tests/test_packaging.py::test_supported_python_versions_are_accepted`
protects the declared interpreter range; `tests/test_noarch_conda_publication.py`
protects the exact-candidate and staging-only publication contract. The hosted
`.github/workflows/tests.yml` matrix supplies the runtime gate for Python 3.14 with both
supported pytest majors.
