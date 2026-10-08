---
summary: Reap direct performance benchmark children after wait failure or interruption.
issue: uibcdf/pytest-receptor#41
status: resolved
opened: 2026-10-08
closed: 2026-10-08
severity: low
verification: reproduced
area: [development, tooling]
guard: tests/test_performance_child_resources.py
normative:
blocked_by: []
supersedes: []
---

# Reap interrupted performance benchmark children

## What

The developer RSS benchmark launches a direct child with `Popen`, then waits
with `os.wait4`. A failed/interrupted wait previously unwound without stopping
and reaping that child, allowing scratch disposal while it remained active.

## How

At source `98f34db82a50260d1eed0517f2d824d0ef064e91`, the actual `_run` is
executed with a private real Python `-S` child instead of the pytest workload.
Injected `RuntimeError` and `KeyboardInterrupt` at `wait4` both leave the child
running. The reproducer and failing-before tests explicitly kill/reap it in
teardown. Two regression cases fail before repair; two success/nonzero controls
already pass. All four pass after exceptional kill/reap followed by re-raise.
The success path retains `wait4`, elapsed time, peak-RSS conversion and status.

## Why

The direct process belongs to this measurement. Exceptional cleanup must finish
before enclosing scratch cleanup and must retain the original interruption.
This is lifecycle implementation under uibcdf/molsyssuite#104, separate from
uibcdf/pytest-receptor#40's earlier scratch ownership repair.

## What is measured and what is assumed

On Linux Python 3.14.7, the four guards use real private direct children and real
kernel reaping. They assert process status, no remaining waitable child, original
exception and preserved caller evidence. Selected resource/reporting tests pass
21 cases, including existing scratch guards; affected Ruff passes. Injection
exercises exceptional control flow, not a measurement of actual OS wait failure.
Hosted administrative gates and local regression execution are distinct; hosted
policy/reporting/publication checks alone do not execute these guards.

## Alternatives and refuted paths

The existing scratch `TemporaryDirectory` cannot stop a live process. Waiting
indefinitely in a `Popen` context after interruption would delay exit until the
workload ended. Kill and reap the direct child on the exceptional path instead.

## Scope and exclusions

No plugin API, output, serialized contract, dependency, measurement formula,
retry/deadline, release, provider guide or consumer pin change. No full benchmark
or package publication is needed for these guards. Process descendants and
non-POSIX platforms remain outside this POSIX RSS helper's bounded proof.
Full-suite debt retains dprada/LMMV and existing weekly/manual recovery; local
resource and administrative checks do not qualify release/platform artifacts.

## Acceptance criteria

The durable guard fails on both original exceptional waits and passes after the
repair. Success/nonzero controls retain measured status and RSS fields. Original
caller evidence remains intact, direct children are reaped, and cleanup errors
are not suppressed. The archived report and generated indexes remain current.

## Delivery route

The authorized internal push conditionally skips automatic CI to avoid running
the full benchmark and package build for this resource-only tranche. Exact-head
policy, reporting and publication-control workflows are dispatched manually.
Those gates do not execute the new guards; their local execution is recorded
above. Full routine/compatibility/benchmark/build evidence remains distinct and
owned by dprada/LMMV through the existing weekly/manual recovery route.
