---
summary: Review runtime dependency API floors and classify every maintained route.
issue: uibcdf/pytest-receptor#49
status: resolved
opened: 2026-11-11
closed: 2026-11-11
verification: measured
area: [reporting, governance]
guard: tests/test_dependency_routes.py
normative: devguide/runtime_dependencies.md
blocked_by: []
supersedes: []
---

# Review runtime dependency API floors and classify every maintained route.

## What and how

Review the sole runtime requirement, pytest>=8.0.0, in package metadata,
Conda host/run declarations, the legacy runtime environment and source/test/
release acquisition paths. Optional runtime engines/features do not exist.
Test, docs, lint, benchmark and release extras are contributor tools; their
bounds do not become shipped runtime requirements. Python retains its separate
>=3.11,<3.15 contract. Preserve exact workflow/build/provider pins.

## Evidence and disposition

The required inclusive floor already agrees in metadata, recipe and the legacy
runtime environment. No runtime upper bound or exclusion exists. Public hook,
Config/UsageError/ExitCode and report APIs consumed by the plugin are reviewed
against the qualified pytest 8 baseline. API presence and focused exact-floor
execution are separate from full public artifact qualification. The shared
preflight passes all 13 maintained routes. See the maintained dependency review
for executed floor scope and the release receipt for wider compatibility.

Report explicit Review completed in this issue and link the confirmation to
uibcdf/molsyssuite#137 after recording the implementation commit/checks.

## Resolution evidence — 2026-11-11

Implementation: d1d2349 (the immutable owner commit contains runtime changes,
regressions, route review and preserved consumer observations). Local focused
checks, exact pytest 8.0.0 API-floor checks and the completed Python 3.14.7
pytest 9.1.1 source suite are retained by the 1.2.3 campaign. Public installation
and hosted compatibility are separately qualified in uibcdf/pytest-receptor#52;
these source results do not claim registry delivery or downstream adoption.

Exact pytest 8.0.0 API-floor execution: **19 passed**, with only the two
optional xdist execution cases deselected. Full pytest 9.1.1 source selection:
**281 passed** serial and distributed, no skips. All 13 maintained dependency
routes pass. No required/optional runtime bound correction was needed.
