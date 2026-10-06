---
summary: Complete maintained dependency-route controls for distribution adoption.
issue: uibcdf/pytest-receptor#38
status: partial
opened: 2026-10-06
closed:
verification: measured
area: [packaging, integration, governance]
guard: tests/test_dependency_routes.py
normative:
blocked_by: []
supersedes: []
---

# Distribution adoption and runtime-route review

## What

Complete the member-owned review under uibcdf/molsyssuite#45. Preserve the
independently qualified public 1.2.1 Conda/PyPI artifacts and the accepted
self-test exception in uibcdf/pytest-receptor#6. Protect future dependency,
environment and workflow changes with maintained runnable checks.

## How

Reuse MolSysSuite's accepted `dependency_routes` operation at
`43b9f94bf5ab0ec3f54a4b2ca5b23b791d6af0bc`, integrated through
uibcdf/molsyssuite#105. The provider owns recipe/constraint/source parsing and
negative guards; this member owns route classification, exact-provider selection,
failure forwarding, CI ordering and its publication job requirements.

The committed inventory covers all 13 discovered inputs: one noarch recipe,
two Conda environments and ten workflows. Whole-workflow hashes require a
review before changes are accepted; never refresh them automatically in CI.
They detect drift rather than interpret arbitrary shell or prove execution.

| Route | Classification |
| --- | --- |
| Conda recipe | Required runtime `pytest>=8.0.0`, Python `>=3.11,<3.15`; existing shared resource/version checks retained. |
| Historical `pytest-receptor@uibcdf_3.13.yml` | Supported Python 3.13 compatibility profile, exact required pytest floor, `uibcdf` then `conda-forge`; create with strict channel priority. Routine development uses the qualified central `molsyssuite@uibcdf_3.14` environment. |
| `build_env.yaml` | Build bootstrap only, with separate recipe host/run closure; no runtime installation. |
| `tests.yml`, `full-tests.yml` | Pip-resolved pytest 8/9 and optional test tools; the reviewed source plugin is exercised serially and with xdist. The component under self-test is not a required sibling-source provider. |
| `docs.yml` | Pip-resolved runtime/docs extras; supported lower-bound Python 3.11 documentation lane. |
| `release.yml` | Exact tagged source, dependency audit and executed native source gates before build; wheel/sdist metadata/resources, clean installation/discovery, then Trusted Publishing. Gate receipt retained separately from distributions. |
| Conda staging, installed, promotion workflows | Existing pinned one-file/exact-file routes, original source binding, all claimed installed cells and same-byte promotion. |
| Reporting, suite policy, Conda publication policy | Administrative checks, with no required sibling-source runtime replacement. |

The public runtime has no required sibling source provider. Pytest itself is
resolved from Conda/PyPI; optional test/docs/build/benchmark tools do not become
runtime requirements. Generic below-floor source/provenance negative guards
remain provider-owned, rather than inventing an inapplicable sibling fixture.

## Why

The previous artifact checks protected public payload/version and recipe parity,
but no maintained control covered every environment and future workflow route.
The pinned audit runs in the existing required lint job before tests, benchmarks
and package builds. Keeping its existing check identity means a failed audit
cannot disappear behind skipped matrix jobs in PR protection.
The committed Conda source-gate contract also requires its executed audit step
before staging. PyPI now reuses the shared `acquire_gates` operation to verify
the already-declared ordinary/full source matrices for the exact tagged checkout
before building. It does not couple PyPI's public version to a Conda upload or
perform a second publication operation.

## What is measured and what is assumed

Local Python 3.14.7 in `molsyssuite@uibcdf_3.14`: all 13 route checks and
45 selected dependency/publication/reporting/packaging tests pass. Required
Ruff 0.16.5 is available in an isolated validation environment, preserving the
shared environment's tools. Hosted qualification of the changed source is
pending. The release event itself is not triggered by this review.

Central prior immutable evidence remains
[the 1.2.1 receipt](https://github.com/uibcdf/molsyssuite/blob/c625ca968be63b3f208a0ac429a65a6a373e0623/devguide/rollouts/pytest_receptor_distribution_45_20261006.json):
original `6c4686c55ee5e004160ba4c36a499ff7e5c8a64b`, producer 37136074225,
installed 37148738757 (eight Linux/macOS arm64 Python 3.11–3.14 cells), Conda
SHA-256 `77bf3694bc903f606d4323b88e3bb3aea9628618036b53073f5a5dbd5dbc73cb`,
public registry/index and independent PyPI wheel/sdist/resource verification.
Clean installation remains owner-measured evidence from completed #32/#34.
This source review does not recertify any new archive or public version.

Current shared-workspace dependency conflicts are retained under
uibcdf/molsyssuite#82. Imports of Pytest Receptor and GH Run Receptor are from
the session's original eligible local clones. These administrative tests change
no runtime code and do not qualify a joint scientific environment.

## Alternatives and refuted paths

- A previous delivery receipt cannot guard a later weakened environment.
- Copying a constraint engine locally would duplicate provider-owned behavior.
- Pinning another published receptor in the self-tests would replace the code
  under review and violate the accepted applicability decision.
- A successful release job without executed exact-source gates is insufficient.
  The added PyPI adapter reuses existing native gate acquisition and fails closed.
- Rebuilding, uploading or promoting the existing 1.2.1 files is unnecessary.

## Scope and exclusions

Distribution controls and their member review only. No runtime API, metadata
dependency, original artifact, scientific suite, public release, self-test
selection or Windows support change. Future credential availability is unknown;
access is confirmed only for previously observed authorized deliveries.

## Acceptance criteria

- Run the pinned shared operation on every classified route and exact candidate.
- Keep identity/tamper/failure, pre-build ordering and exact-tag/native-gate
  rejection guards addressable in `tests/test_dependency_routes.py`.
- Inspect applicable hosted CI at the changed default-branch source.
- Retain old artifacts/evidence, archive this record and hand separate adoption,
  recipe/CI readiness and bounded access results to MolSysSuite #45.
