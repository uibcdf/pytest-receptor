# Repository agent guide

## External Tooling Guides (Required for Development)

These guides are required reading for anyone developing this package. They describe how
external tools must be used here.

- `GH_RUN_RECEPTOR_GUIDE.md` — Required guide for compact, truth-preserving inspection of
  GitHub Actions runs and the native-command fallback.

## MolSysSuite coordination

pytest-receptor is governed by MolSysSuite policy 1.0. Policies, compatibility contracts
and proposals shared by multiple components are owned by `uibcdf/molsyssuite` and reported
on its issue board. Defects, implementation decisions and evidence specific to this plugin
remain in `uibcdf/pytest-receptor`.

Use stable `uibcdf/<repo>#<number>` references between repositories. Do not use sibling
developer-guide paths as cross-repository identities.
