# Repository agent guide

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

## MolSysSuite coordination

pytest-receptor is governed by MolSysSuite policy 1.0. Policies, compatibility contracts
and proposals shared by multiple components are owned by `uibcdf/molsyssuite` and reported
on its issue board. Defects, implementation decisions and evidence specific to this plugin
remain in `uibcdf/pytest-receptor`.

Use stable `uibcdf/<repo>#<number>` references between repositories. Do not use sibling
developer-guide paths as cross-repository identities.

Before filing or closing a bug or proposal report, follow
`devguide/reporting_protocol.md`: open the local GitHub issue first, use
`devguide/templates/report.md`, and run the documented offline index and
reporting tests. Pre-protocol register references remain historical evidence;
they do not replace the owning GitHub issue identity.

## Modular reusable tools

Before adding a feature, inspect existing tools and identify the owning module or
component. Implement or extend independently useful operations as documented reusable
tools in that owner, with their own contracts and tests; have consumers call them.
Keep task-specific decisions local and report missing sibling capabilities to the
provider with linked consumer evidence. Follow
[MOLSYSSUITE_GUIDE.md#modular-reusable-tools](MOLSYSSUITE_GUIDE.md#modular-reusable-tools)
for applicability, compatibility, performance and tracked exceptions.

## Durable working instructions

Keep technical findings in owning issues, fixes, tests and maintained guidance.
Place only accepted lasting contributor actions in root or appropriately scoped
instructions, following
[the common policy](MOLSYSSUITE_GUIDE.md#durable-working-instructions).
For work under `devguide/`, also read [devguide/AGENTS.md](devguide/AGENTS.md)
and its local reporting protocol. Shared instruction proposals belong in
`uibcdf/molsyssuite`; cross-MOLI contracts belong in `uibcdf/moli`.
