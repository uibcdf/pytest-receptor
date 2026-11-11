---
summary: Adopt the reviewed shared Conda v2.3.0 publisher and promotion callers.
issue: uibcdf/pytest-receptor#50
status: resolved
opened: 2026-11-11
closed: 2026-11-11
verification: measured
area: [reporting, governance]
guard: tests/test_noarch_conda_publication.py
normative: devtools/conda-build/README.md
blocked_by: []
supersedes: []
---

# Adopt the reviewed shared Conda v2.3.0 publisher and promotion callers.

## What and how

Adopt MolSysSuite 95f693be10c9205ab9b912cb53453710a207bf45 in the
publish and promotion callers. Compared with their previous respective pins,
the shared workflow changes are only the three build/exact-upload bindings and
one promotion binding to provider 87c70b1443d5f22d738ee3ddf812bdbe0152f6c2.
Existing inputs, explicit ANACONDA_TOKEN mapping, .tar.bz2 host-only noarch
build, pre-upload inspection, source gates, installed gate before promotion,
original candidate/digest and independent public verification remain.

## Evidence and limits

28 shared publication-contract tests pass from an independent exact provider
checkout; 21 member dependency/publication/guide tests and all 13 dependency
routes pass locally. Reviewed only the two changed workflow hashes in the
inventory. Installed workflow/helper/operator/dependency-preflight pins stay at
their separately qualified revisions. This is source adoption, not a real new
publication, registry receiving or scientific/installed claim. The next release
qualifies the actual bytes separately under uibcdf/pytest-receptor#52.

Explicit Review completed with the exact implementation commit goes to #50 and
uibcdf/molsyssuite#87. Withdrawal and existing artifact replacement remain out
of scope.

## Resolution evidence — 2026-11-11

Implementation: d1d2349 (the immutable owner commit contains runtime changes,
regressions, route review and preserved consumer observations). Local focused
checks, exact pytest 8.0.0 API-floor checks and the completed Python 3.14.7
pytest 9.1.1 source suite are retained by the 1.2.3 campaign. Public installation
and hosted compatibility are separately qualified in uibcdf/pytest-receptor#52;
these source results do not claim registry delivery or downstream adoption.

The member's source suite passes **281/281** serial and **281/281** with two
xdist workers on Python 3.14.7 / pytest 9.1.1, with the optional test providers
installed in a task-owned validation prefix and no skips. These executions
exercise the owner guard while shared registry transport remains fixture-only.
