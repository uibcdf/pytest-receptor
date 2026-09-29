---
summary: Recurring full CI and protected contributor routes are missing.
issue: uibcdf/pytest-receptor#11
status: partial
opened: 2026-09-29
closed:
severity: medium
verification: inspected
area: [ci, governance]
guard: tests/test_ci_backlog.py
normative:
blocked_by: []
supersedes: []
---

# Recurring full CI and protected contributor routes

## What

At `a4ea33a`, Tests runs the complete suite serially and under xdist on
Linux across Python 3.11–3.14 and pytest 8/9, plus lint, benchmarks and wheel
checks. The [hosted Tests run](https://github.com/uibcdf/pytest-receptor/actions/runs/36390398882)
passed. No workflow schedules the full matrix, and `main` has no effective
branch rules. Native CI-skip markers have no daily recovery route.

## How

Keep Tests intact and require its stable checks on external PRs.
Administrators `dprada` and `LMMV`, the only current collaborators, retain
direct pushes. Add `full-tests.yml` with the same eight Linux compatibility
cells and two macOS arm64 Python 3.13 cells, one for each pytest major.
Run it weekly on Tuesday at 09:11 UTC and conditionally daily at 01:07 in
`America/Mexico_City`. The daily route examines skipped commits since the
last executed green full Linux matrix, recognizing both full Tests pushes
and scheduled/manual full matrices. Every required Python/pytest pair must
have passed both serial and distributed steps; probes, skipped steps,
failed runs, PRs and other branches never clear debt. Uncertain history runs
the full matrix. A manual probe checks the detector without heavy jobs.

## Why

This plugin provides test reporting across the ecosystem. Recurring coverage
finds dependency changes even without a new push. Protected PRs and recovery
of skipped internal pushes implement `uibcdf/molsyssuite#39` while retaining
the plugin's pytest-major compatibility contract.

## What is measured and what is assumed

The current hosted Tests matrix passed at the inspected commit. The new
scheduled lanes and macOS test environment need initial manual dispatch.
GitHub lists `macos-15` as arm64 in its
[runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners);
the workflow also asserts the actual architecture. The
[schedule documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
supports IANA time zones and warns of delayed or dropped runs.

## Alternatives and refuted paths

A daily trigger alone does not prove execution. A green diagnostic workflow
with skipped tests is not a valid matrix watermark. The API branch filter
returned old run lists in other members, so branch filtering is local.
Requiring an extra nightly matrix after a later successful full Tests push
would duplicate already executed coverage; that push can clear the debt.

## Scope and exclusions

This issue owns CI routing, required checks and skip recovery. Platform
publication claims and exact release-candidate evidence need their own
review; the new macOS lane alone cannot certify existing releases.

## Acceptance criteria

- Existing full compatibility checks gate PRs; administrators retain direct pushes.
- Weekly and manual full runs execute every Linux pair and the macOS representatives.
- Skipped direct pushes remain due until an executed green full matrix passes.
- Hosted zero-debt, skipped-debt and recovery evidence is recorded.
- Actual daily execution, hosted PR enforcement and platform claims are reviewed.

## Resolution

Implementation and hosted evidence are being collected. Keep this issue open
until remaining observations and platform claims are recorded centrally.
