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

## Accepted next step

Add a non-claiming Python 3.14 lane for both supported pytest majors. It remains
`continue-on-error` and uses the explicit metadata override until hosted evidence is green
and the central phased Python policy admits this component. Then update all support
surfaces together and require clean wheel and Conda installation without an override.

Python 3.11 remains supported. The routine development interpreter remains Python 3.13
until the central policy decides otherwise.
