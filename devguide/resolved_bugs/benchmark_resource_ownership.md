---
summary: Protect benchmark ownership and expose cleanup failures.
issue: uibcdf/pytest-receptor#40
status: resolved
opened: 2026-10-07
closed: 2026-10-07
severity: medium
verification: reproduced
area: [tooling, benchmarks]
guard: tests/test_benchmark_resources.py
normative:
blocked_by: []
supersedes: []
---

# Benchmark resource ownership

## What

The token benchmark removes `${tempdir}/receptor-bench` before claiming it. Two
callers can therefore erase one another's active scenario files. Both the token
and performance benchmarks suppress cleanup failures with `ignore_errors=True`.
The performance benchmark already creates a unique directory, avoiding the first
defect but retaining the second.

## How

The original source is c3ddf99f4d74dd2b120489bfb8a3d18949a6aaac. A bounded probe
under uibcdf/molsyssuite#104 executed the actual token `measure` with synthetic
callbacks in a managed private parent. A pre-existing active-run sentinel was
deleted. No real shared benchmark directory was touched.

Twelve focused regressions exercise both tools. Before repair, six fail: occupied
directory preservation, concurrent ownership refusal and four combinations of
cleanup failure with successful/failing children. Six controls already pass,
including ordinary success/failure cleanup, occupied-file preservation and a
stable real-pytest rootdir. After repair all twelve pass on Python 3.14.7.

## Why

Tools must protect other callers' resources and surface cleanup failures under
the accepted policy in uibcdf/molsyssuite#104. Retaining one stable displayed
rootdir is part of the existing token measurement contract; a random directory
suffix must not perturb historical token comparisons.

## What is measured and what is assumed

The focused tests use actual filesystem ownership, two concurrent threads and
controlled child/removal failures. Four tiny real pytest subprocesses confirm
that the displayed rootdir is identical across repetitions. Other callbacks and
timing/RSS samples are synthetic. This proves the harness lifecycle, not new
published token/runtime figures or an installed/public package qualification.
The qualified workspace keeps its existing editable import origins and seven
known MolSysSuite #82 dependency conflicts.

## Alternatives and refuted paths

Replacing the token path with an unnormalized random name would change the
measured banner. Automatic removal of an occupied path, global age/prefix
cleanup and suppression of removal errors violate ownership/error visibility.
An exclusive atomic directory claim is enough; no new lock service, shared
cleanup framework or suite policy is needed.

## Scope and exclusions

Only the two local benchmark harnesses, their resource regressions, documentation
and this report. Plugin API/rendering, measurements, canonical guides, Python
support, releases and consumer pins stay unchanged. The benchmark devtools are
outside the installed `pytest_receptor*` package; registered plugin consumers
need no source adoption. Existing automatic test CI may check the harness, but
this change creates no release, publication or new CI gate.

## Acceptance criteria

- Refuse an occupied token path without removing its contents.
- Preserve the first owner's scenario during a concurrent second invocation.
- Keep actual pytest rootdir stable across measurements.
- Remove owned resources after success and child failure.
- Surface removal failures, retaining the original child error as context.
- Use tests/test_benchmark_resources.py as the durable regression guard and
  archive this record/index with the repair after verification.

## Resolution — 2026-10-07

The token harness claims its stable path using atomic `mkdir`, refuses an occupied
path with an actionable diagnostic, and removes only its own directory in
`finally`, without suppression. The performance harness uses a managed
TemporaryDirectory; setup/teardown remain outside its timed child operation.
The twelve regressions and affected Ruff lint/import/format checks pass locally.
Published repair: e100d65e8f49fdb7a93edb8fe541ff296c16c6e0. Exact-source hosted
[Tests 37686778761](https://github.com/uibcdf/pytest-receptor/actions/runs/37686778761)
passes Python 3.11–3.14 with pytest 8 and 9, ordinary and distributed suites,
actual token/performance benchmarks, lint, packaging/clean-wheel checks and the
dependent coverage upload. This is existing test CI, not a public release.
Exact source/event/workflow/jobs/required executed steps were verified, together
with reporting (37686778742), policy (37686779765) and publication-control
(37686779737) gates. The documentation run 37686778650 also reports success.

The guard module is relevant: six new cases failed against the original source,
then all twelve pass after repair. Reintroducing pre-claim deletion breaks owned
sentinel/concurrency tests; suppressing removal failures breaks the controlled
success/failure cleanup checks. Real pytest headers protect the existing stable
rootdir constraint. No active primary clone or caller environment was changed.

Remaining full local-tool/retrospective reviews belong to MolSysSuite #104 and
are not closed by this focused repair. Archive/index closeout is a separate
metadata checkpoint; no code or measurement changes are added here.
