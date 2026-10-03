---
summary: Publish and independently verify pytest-receptor 1.2.1.
issue: uibcdf/pytest-receptor#32
status: active
opened: 2026-10-03
closed:
verification: reproduced
area: [release, distribution, compatibility]
guard: tests/test_noarch_conda_publication.py
normative:
blocked_by: []
supersedes: []
---

# Publish pytest-receptor 1.2.1

## What

Release the compatible corrections and delivery improvements since 1.2.0
through GitHub, PyPI and the official `uibcdf` Conda channel, then notify
MolSysSuite by issue with independently verified evidence.

## How

The committed `devtools/conda-build/release_plan.toml` chooses staging with
build zero. The final candidate SHA and receipts are recorded in
`uibcdf/pytest-receptor#32` after this commit exists. Native source gates must
pass at that SHA, including every declared serial/distributed step. The
manual full matrix adds the two macOS arm64 Python 3.13 / pytest 8 and 9
source cells to the eight Linux cells. Lint, package, benchmarks, documentation,
reporting and policy results remain separate exact-candidate evidence.

The pinned shared publisher builds once, runs recipe tests and inspects
metadata, generated version and all runtime modules before staging upload.
The installed gate uses the same digest on Linux and macOS arm64 with each
Python minor 3.11–3.14, outside the source tree, with the complete `tests`
selection and all maintained test-extra dependencies. The shared promoter
independently verifies that run, adds the main label to the tested file and
checks both registry and solver index. GitHub Release triggers the existing
protected OIDC PyPI route, whose wheel and sdist receive independent metadata,
digest and clean-install checks.

## Why

The release delivers the terminal discard-stream cleanup, canonical consumer
guide, report-path/timing corrections, recurring CI and skip recovery,
coverage evidence and retirement of the historical archive exception.
Version 1.2.1 preserves the public API and schema contracts.

## Shared-tool boundary

The release units are pinned to MolSysSuite commit
`5a90853d4ac147f7b831cfc37f9f5defd87c190a`. The common installed workflow
cannot declare the integration dependencies needed here; this capability is
tracked in `uibcdf/molsyssuite#77`. The local manual wrapper retains the common
job/title descriptor and calls its `installed_noarch.py` operations for matrix
preparation, digest download, installed resource/provenance verification and
test execution. Only the component's dependency environment differs. Replace
this wrapper with the shared caller when #77 supports the required environment;
dprada reviews the interim route by 2026-12-31 under this release issue.

## What is measured and what is assumed

### 2026-10-03 candidate and provider evidence

Candidate `b8071ce13196b5b24d20b034676636c0a8fd8f4a` passed native source
Tests run `37111538632`, full matrix `37111565942` and documentation
`37111568582`. Staging run `37111808160` then failed before archive production
or upload: the action's `conda build` resolved the base-backed shell function,
although the named publisher environment contained conda-build 26.9.0.
Provider correction and qualification belong to
`uibcdf/action-build-and-upload-conda-packages#46`; shared adoption is tracked
in `uibcdf/molsyssuite#78` and `uibcdf/moli#38`. The original consumer diagnosis
remains `uibcdf/molsyssuite#80`. A planned temporary orchestration was examined
under `uibcdf/pytest-receptor#34` but has not been adopted; the shared caller is
retained while its provider correction is qualified. No public tag or artifact
is claimed from these runs. Any changed candidate needs fresh exact-source
gates.

Fresh benchmarks use a locally built 1.2.1 wheel from that candidate, with
runtime module and harness digests retained in the benchmark JSON receipts.
They cover eight small scenarios, 8,000 tests with twelve workers and 1,000-test
runtime/RSS medians over five runs. The README and documentation now state the
clean environment and versions; this wheel is measurement evidence rather
than a registry receipt. Publication-workflow and documentation changes do
not alter those measured runtime modules.

Before candidate CI, the shared administrative validators accept the plan,
recipe, resource inventory and workflow controls. That does not certify
publication or installed compatibility. Every original runtime dependency is
publicly resolvable (`pytest>=8`); the recipe preserves the project Python
bounds (`>=3.11,<3.15`). Ordinary environments use `uibcdf` then `conda-forge`;
staging selects only the exact plugin file, with third-party dependencies from
public channels. No bundled native code, data, schema or console launcher is
present; `_version.py` is the sole generated version-bearing runtime resource.
Windows runtime support is not claimed by this release. No Zenodo DOI or
archival claim is made.

## Acceptance criteria

One exact clean source commit supplies tag, PyPI archives and the Conda file.
Native gates and every installed cell execute and pass; receipts identify the
candidate, recipe/resources, dependency closure and artifact digest. Public
PyPI metadata/files and Conda main-label/index records match the tested bytes.
Clean public-channel installs discover the pytest plugin and run a real test.
The release notification is filed in MolSysSuite after those facts exist.
