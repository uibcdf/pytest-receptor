---
summary: Publish and independently verify pytest-receptor 1.2.1.
issue: uibcdf/pytest-receptor#32
status: blocked
opened: 2026-10-03
closed:
verification: reproduced
area: [release, distribution, compatibility]
guard: tests/test_noarch_conda_publication.py
normative:
blocked_by: [uibcdf/molsyssuite#88]
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
manual full matrix adds the two macOS arm64 Python 3.14 / pytest 8 and 9
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

The build caller adopts MolSysSuite commit
`2fb344525ca0eea817dc24a518f4a6bf26e311cf`, selecting the qualified active
Conda executable and exact-upload environment corrections. Other release units remain pinned to
`5a90853d4ac147f7b831cfc37f9f5defd87c190a`. At preparation time the common installed
workflow could not declare the integration dependencies needed here; the capability
was tracked in `uibcdf/molsyssuite#77` and has since been published at
`baac208f3f592e00eaf99fa78a879878f98dc141`. Receiving adoption remains separate
from qualification of the already staged file. The local manual wrapper retains the common
job/title descriptor and calls its `installed_noarch.py` operations for matrix
preparation, digest download, installed resource/provenance verification and
test execution. Only the component's dependency environment differs. Replace
 this wrapper with the qualified shared caller after the installed-gate defect
in `uibcdf/molsyssuite#88` is corrected and adopted;
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

### 2026-10-03 shared correction adoption

The handoff in `uibcdf/pytest-receptor#32` identifies the published shared
correction at `2a2a459cc3795bb92766fffa0fe28f4d80f01ad4`, selecting build
action `8da628d9b393e184c3bf3722708b19dcfbf7ef0a`. Review confirms that the
shared publisher changes only its build reference; the separately qualified
upload/promote references and all source, recipe/resource and installed gates
are retained. Provider runs `37115921728` and `37115921702` and shared
governance run `37125099269` establish provider qualification, not component
artifact delivery. `uibcdf/molsyssuite#78` stays open for our adoption and
actual staging evidence; its closure is not a prerequisite to using the fix.

The adopted policy 1.5.4 source lane now uses Python 3.14 for the representative
macOS arm64 source cells. The committed release plan requires those actual
job names. Its installed matrix still requires all Python 3.11–3.14 cells on
Linux and macOS arm64 for one exact file. Fresh final-candidate receipts remain
required before tagging or public delivery.

One exact clean source commit supplies tag, PyPI archives and the Conda file.
Native gates and every installed cell execute and pass; receipts identify the
candidate, recipe/resources, dependency closure and artifact digest. Public
PyPI metadata/files and Conda main-label/index records match the tested bytes.
Clean public-channel installs discover the pytest plugin and run a real test.
The release notification is filed in MolSysSuite after those facts exist.

### 2026-10-03 actual build and separate upload failure

Adoption PR `uibcdf/pytest-receptor#37` is merged at candidate
`52a61a2b8adcf377b717d00b9da8dbf91a2d391e`. Tests `37126704791` passes
the eight required Linux cells and all sixteen serial/distributed steps;
full matrix `37126758321` passes ten cells and twenty required test steps,
including macOS arm64 Python 3.14 / pytest 8 and 9. Documentation
`37126704742`, reporting `37126704736`, policy `37126705065` and publication
governance `37126705033` also pass at that candidate. The source is preserved
at `release/1.2.1-candidate`; the later main commit synchronizes the GH Run
Receptor guide and does not change the measured runtime modules.

Actual staging `37127152850` successfully builds one noarch file, runs the
recipe tests and checks its version and resource inventory. The inspected
filename is `pytest-receptor-1.2.1-py_0.tar.bz2`, SHA-256
`12367aa706ab5aad512794a6bffddd9f21eddd6fc51f1b4989ab969efb39ea7c`.
The separate exact-file uploader then fails; its retained receipt says only
`unverified`. Receipt artifact `noarch-publication-37127152850-1` (ID
`11275019229`) retains preflight, artifact, producer and upload evidence.
Independent post-failure anonymous all-label Conda release and PyPI queries
for 1.2.1 both return 404. No installed matrix, public tag or delivered package
is claimed, and upload has not been blindly repeated.

Ackredit independently reproduces the separate upload failure in run
`37127293886`. `uibcdf/action-build-and-upload-conda-packages#48` owns the
provider correction; the simultaneous report #49 retains our original
evidence and is consolidated into #48. Provider build bugs #46/#47 are
resolved. MolSysSuite #78 and MOLI #38 now contain the shared upload handoff.

The maintainer-requested comparison with MolSysMT uses successful historical
run `36113593257` at `e28ceb9ea0de0cc86bc370e5aff1e96c4cc71c69` on
2026-09-25. Its named micromamba build environment includes anaconda-client;
combined action v2.1.0 (`482d4decb71634d9fa4f81551c69ba958dff3f86`) uploads
with `bash -l {0}`. Our separate uploader at
`932fbef84440efbc97eb2275360fd3a767fdb47c` explicitly uses plain `bash`,
observed natively as `--noprofile --norc`. This is a source/route difference
supporting the missing active-client hypothesis, not proof of the specific
exception hidden by the receipt. Reverting to the older uploader would not
preserve the current exact-file controls and is not an accepted correction.

### 2026-10-03 resumed delivery after qualified upload adoption

The maintained publisher is now adopted in component commit
`718e96c782a24fc45a009317325645988fa5c8a4`, selecting shared source
`2fb344525ca0eea817dc24a518f4a6bf26e311cf` and upload provider
`1aa2011f902a1a9d533564572245bb29f6862e86`. The provider's hosted actual
composite qualification `37129463375` and central governance `37130795870`
pass. The identified shell/client defect in provider #48 is corrected;
these simulated provider checks do not establish actual registry delivery.

The maintainer explicitly requests completion of 1.2.1 under
`uibcdf/pytest-receptor#32`, with fresh exact-source gates, actual staging,
the same file's complete installed matrix and independent PyPI/Conda public
verification. General action v2.3.0 adoption remains separate deferred work in
`uibcdf/molsyssuite#87` and `uibcdf/moli#42`; withdrawal is outside this release.
The final source will be preserved at a new candidate reference, leaving
the earlier failed candidate and its evidence unchanged. Shared failures must
be reported with their native execution and receipts to the owning issue;
no unverified upload is repeated without a fresh public-state inspection.

### 2026-10-03 staging verified; installed qualification blocked

Frozen candidate `6c4686c55ee5e004160ba4c36a499ff7e5c8a64b` is retained at
`release/1.2.1-publication`. Source Tests `37133656874` and full matrix
`37133868138` pass with every required serial/distributed step verified
natively. Sphinx builds at that candidate in `37133870196`; its branch
deployment is rejected by the main-only Pages environment. Separate main
run `37136023643` at guide-only successor
`21524e3f44701ab194ff8a15eddd35494f1b1450` passes build and deployment.

Staging `37136074225` succeeds at the frozen candidate under the qualified
publisher. Its upload receipt is `uibcdf.conda-upload@1`, `state=verified`.
Independent anonymous Anaconda metadata, archive SHA-256 and resource/version
inspection verify `noarch/pytest-receptor-1.2.1-py_0.tar.bz2` with digest
`77bf3694bc903f606d4323b88e3bb3aea9628618036b53073f5a5dbd5dbc73cb`.

Installed run `37136496168`, attempt 1 at the same candidate, fails in all
eight Linux/macOS arm64 × Python 3.11–3.14 cells at `Install exact artifact`.
The exact archive download and digest verification pass, but Conda reports
that the staged package is excluded by strict repository priority. Installed
verification and scientific tests do not pass; a complete installed matrix
is not claimed. GH Run Receptor development `1.2.0+3.g6fe2cc5` in the required
Python 3.14 environment groups the eight failures; bounded native logs retain
the actual solver cause.

The shared installed-workflow defect and qualification path for these already
registered immutable bytes are handed off in `uibcdf/molsyssuite#88`, with
receiving evidence in `uibcdf/pytest-receptor#32` and coordination in
`uibcdf/molsyssuite#78`. The separate test-dependency capability #77 is now
resolved upstream; its publication does not establish receiving adoption.
No rebuild, overwrite, promotion, public tag or PyPI publication is performed.
Release completion waits for a qualified correction of the installed gate;
the already successful build/upload correction remains adopted.
