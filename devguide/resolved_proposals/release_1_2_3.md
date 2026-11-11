---
summary: Prepare and qualify public 1.2.3 after owner issue resolution.
issue: uibcdf/pytest-receptor#52
status: resolved
opened: 2026-11-11
closed: 2026-11-11
verification: measured
area: [reporting, governance]
guard: 
normative: devtools/conda-build/README.md
blocked_by: []
supersedes: []
---

# Prepare and qualify public 1.2.3 after owner issue resolution.

## What and how

Address uibcdf/pytest-receptor#46, #49, #50 and #51, and record the #9
no-demand deferral without inventing a feature request. Preserve received work.
Prepare one immutable source, current benchmarks and exact native source gates.
Build one file to staging, qualify the required installed matrix, promote those
same bytes and verify official Conda and PyPI independently with clean installs.

## Ownership and evidence

Maintainer dprada; advance impact/publication notice uibcdf/molsyssuite#188.
Current public release remains 1.2.2 until independently verified delivery.
Do not conflate source checks, installed artifacts, actual registry receiving or
scientific/Windows/DOI compatibility. Retain complete release evidence before
cleanup and record resources owned by this task.

## Verified completion — 2026-11-11

Published GitHub Release/tag **1.2.3**, frozen source
`84adb5bf64d0f6c5fcbbc824d6ec90772770896c`.
The earlier statement that 1.2.2 remained current records the proposal's opening
state; this dated completion supersedes it.

- [PyPI 1.2.3](https://pypi.org/project/pytest-receptor/1.2.3/): public wheel and
  sdist match retained hosted build bytes, validated metadata/resources/source.
- [Official Conda](https://anaconda.org/uibcdf/pytest-receptor): the exact staged
  noarch archive was promoted, not rebuilt. Registry/main/solver-index and public
  download digests verified independently.
- [Installed qualification 43105052378](https://github.com/uibcdf/pytest-receptor/actions/runs/43105052378):
  all eight Linux/macOS arm64 × Python 3.11–3.14 cells pass 281 tests, zero skips,
  complete dependency closures and final provenance checks. Candidate and
  qualification are the same frozen source.
- [Promotion 43106409040](https://github.com/uibcdf/pytest-receptor/actions/runs/43106409040)
  and [PyPI 43106408459](https://github.com/uibcdf/pytest-receptor/actions/runs/43106408459)
  completed successfully. The protected PyPI approval used the existing release
  authorization; no environment protection was changed.
- Fresh independent public pip (Python 3.14.7) and Conda (3.14.10) installations
  discover the plugin and pass a green execution and the #46 collection-error
  negative smoke, including complete/integrity-valid structured artifacts.
- [Zenodo version DOI 10.5281/zenodo.24146737](https://doi.org/10.5281/zenodo.24146737)
  and exact source ZIP independently verified. Coverage is source only.

Full filenames, digests, executed source/tag steps, actual public origins,
dependency closures, archival inventory and recovery limits are retained in
[`../release_evidence/1.2.3.json`](../release_evidence/1.2.3.json),
[`../release_evidence/1.2.3-installed-closures.json`](../release_evidence/1.2.3-installed-closures.json)
and the pre-existing source review. The first installed run's scientific success
does not erase its failed retention; the fresh complete matrix is authoritative.
The repeated matrix cost is owned by uibcdf/molsyssuite#92.

Issues #46, #49, #50 and #51 are resolved; #9 remains explicitly deferred.
Future bounded Zenodo automation is separately owned by #53, with successful
manual archival verification preserved here. Ecosystem release/receiving notice:
uibcdf/molsyssuite#188. Shared guides and foreign consumer checkouts were not
edited. Later audit commits do not move the immutable public tag.
