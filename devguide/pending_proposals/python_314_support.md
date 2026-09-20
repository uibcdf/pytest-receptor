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

The resolution is the shared MolSysSuite noarch publication pattern already used by
SMonitor and DepDigest. A manual workflow pins a full candidate SHA, creates an ephemeral
runner-local semantic-version tag, verifies `python -m versioningit`, builds one artifact,
uploads only to `staging`, and retains `events@1` producer evidence for gh-run-receptor.
Only a later GitHub Release event may upload to `main`. The recipe also compares installed
distribution and module versions with Conda's `PKG_VERSION` during its own tests.

A successful hosted staging build plus an independent clean Python 3.14 installation of
that exact staged artifact remain the final admission evidence.

Python 3.11 remains supported. The routine development interpreter remains Python 3.13
until the central policy decides otherwise.
