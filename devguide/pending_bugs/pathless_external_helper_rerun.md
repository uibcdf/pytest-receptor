---
summary: Keep pathless external tests separate from foreign crash locations.
issue: uibcdf/pytest-receptor#39
status: active
opened: 2026-10-06
closed:
severity: medium
verification: reproduced
area: [reporting, rerun, compatibility]
guard: tests/test_plugin.py::test_external_helper_failure_rerun_selects_original_tests
normative:
blocked_by: []
supersedes: []
---

# Pathless external helper failures select the wrong rerun file

## What

OpenC ASTP reported this provider defect while working on
`uibcdf/opencastp#13`. With an explicit pytest config fixing rootdir, an
external test can have a pathless node ID such as `::test_external_failure[0]`.
If the failure originates in an imported helper, the receptor incorrectly
uses that crash file as the test's rerun file. This is a distinct remaining
case of the external-path behavior reviewed in `uibcdf/pytest-receptor#24`.

## How

Use an empty `[tool.pytest.ini_options]` project config and an external
parametrized test importing a helper that raises `AttributeError`. Run pytest
with `-c` pointing to that config and `pythonpath` including the external
directory. Compare native pytest with compact output and execute the actual
rendered command using the same interpreter, fixed config and test environment.

The correction retains the test file from pytest's `report.location` in the
normalized phase and occurrence models. A pathless node ID uses that file for
selectors; exception location, cause grouping and fingerprints retain the crash
site. Existing node IDs with paths continue to take precedence. Reports without
a test path retain the legacy fallback.

The additive optional `test_path` phase field is documented in
`docs/artifacts.md`; old `events@1` artifacts can omit it. No schema major,
consumer migration or public package version changes in this correction.

## Why

The original run's failure verdict and counts are correct, but the advertised
rerun can return usage error 4 or no-tests exit 5 instead of reproducing the
original failure. Consumers lose an actionable selection despite complete,
integrity-valid evidence. Crash diagnostics must not be replaced with the test
location to repair a selection.

## What is measured and what is assumed

On 2026-10-23, baseline `7041366` plus the new regression fails all four
combinations: single/grouped occurrences in serial and with two xdist workers.
Native and compact original selections return exit 1 in every case. The
rendered serial single-test command instead returns exit 4; grouped and xdist
commands return exit 5. All point to `outside/helper.py`.

With the correction, all four regression combinations pass. Their actual
rendered reruns select `outside/test_external.py`, return exit 1 and report the
original one or two failures. Grouped occurrence selectors identify the original
tests. JSONL remains complete and integrity-valid, with test and crash paths
retained separately. The two earlier external-path regressions also pass.

Local validation uses Python 3.14.7 / pytest 9.1.1 in
`molsyssuite@uibcdf_3.14`. The full local suite passes 230 tests and skips 10
optional-integration cases because pytest-subtests and pytest-rerunfailures are
absent. Ruff lint and format checks pass. Hosted CI remains to be checked at the
implementation commit; local results do not establish other Python versions or
the skipped integrations.

## Alternatives and refuted paths

- Reusing the exception location is the reproduced defect; a helper's failure
  line does not identify the collected test file.
- Replacing the crash location with the test path would damage root-cause
  diagnostics and grouping. The model retains both instead.
- The existing #24 tests raise inside the external test file and therefore
  cannot detect a foreign-helper target. Their original resolution stays valid.

## Scope and exclusions

This component-owned correction addresses rerun and occurrence selectors.
Pytest outcomes, counts, exception evidence, grouping, configuration and runner
selection retain their existing contracts. No consumer checkout is modified,
and no package, release, benchmark table or shared policy is published.

The owned baseline and corrected pytest subprocess directories under `/tmp`
are retained during validation, then reviewed at closeout. The durable evidence
is this report, the owning issue and the executable regression; those generated
directories are not a new public artifact.

## Acceptance criteria

- Individual and grouped commands select the original external tests even when
  a foreign helper raises, under both serial pytest and xdist.
- Execute the rendered command with its configured runner and fixed config;
  assert exit 1 and the original failure count, rather than just matching text.
- Keep the foreign crash location visible and preserve JSONL integrity and
  truthful native/compact outcome parity.
- Preserve the previous external-path guards and run relevant model, artifact,
  output-contract and integration checks.
- Archive this record with final verification and synchronize
  `uibcdf/pytest-receptor#39`.
