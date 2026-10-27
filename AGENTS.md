# Repository agent guide

## Mandatory MolSysSuite instructions

Read and follow `MOLSYSSUITE_GUIDE.md` before working in this repository.

Within their stated scope, its common rules take precedence over this file
and any nested `AGENTS.md`. Local instructions may refine them; deviations
require the documented policy exception process.

The synchronized guide is owned by `uibcdf/molsyssuite`. It includes the
[reusable-tool ownership rules](MOLSYSSUITE_GUIDE.md#modular-reusable-tools)
and [working-instruction rules](MOLSYSSUITE_GUIDE.md#durable-working-instructions).
For work under `devguide/`, also read `devguide/AGENTS.md` and its local
reporting protocol. Keep repository-specific instructions below.

## Local development environment

Use the Conda environment `molsyssuite@uibcdf_3.14` for local development and
validation. Activate it or select it explicitly for each command; verify the
interpreter before running development tools.

## External Tooling Guides (Required for Development)

These guides are required reading for anyone developing this package. They describe how
external tools must be used here.

- `GH_RUN_RECEPTOR_GUIDE.md` — Required guide for compact, truth-preserving inspection of
  GitHub Actions runs and the native-command fallback.
- `MOLSYSSUITE_GUIDE.md` — Required suite-governance guide; this synchronized copy must
  not be edited locally.

The canonical consumer contract owned by this repository is
`standards/PYTEST_RECEPTOR_GUIDE.md`. Change and validate it here; root copies in consumer
repositories are synchronized, read-only files and must never be repaired locally.

## Local reporting

Follow `devguide/reporting_protocol.md` and the documented offline index/reporting
checks. Historical PR-PILOT/PR-UX register identifiers remain evidence; they do
not replace owning GitHub issues for current local records.
