---
summary: Review runtime dependency API floors and classify every maintained route.
issue: uibcdf/pytest-receptor#49
status: active
opened: 2026-11-11
closed:
verification: inspected
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
