---
summary: Verify recurring full CI, skipped-push recovery and protected contributor routes.
issue: uibcdf/pytest-receptor#11
status: resolved
opened: 2026-09-29
closed: 2026-10-03
severity: medium
verification: measured
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
Linux and representative macOS lanes passed their initial manual dispatch;
actual cron execution and published platform claims remain unreviewed.
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

At `608b230`, [Tests](https://github.com/uibcdf/pytest-receptor/actions/runs/36644241696)
passed all eleven jobs, including both suite steps in all eight Linux
compatibility cells. [Reporting governance](https://github.com/uibcdf/pytest-receptor/actions/runs/36644241672)
and [MolSysSuite policy](https://github.com/uibcdf/pytest-receptor/actions/runs/36644242403)
also passed. The [initial probe](https://github.com/uibcdf/pytest-receptor/actions/runs/36644268513)
recognized `a4ea33a` as an executed full Tests watermark, found zero debt,
and omitted heavy jobs.

The protected `main` now requires all eleven stable Tests checks with strict
status. Required PR reviews are configured with zero mandatory approvals:
external integration requires a PR and full checks, while administrators
`dprada` and `LMMV` retain their direct-push bypass. The documentation push
`a7f3b0e` deliberately included `[skip ci]`; GitHub accepted it with explicit
PR and required-check bypass notices. The [debt probe](https://github.com/uibcdf/pytest-receptor/actions/runs/36644755285)
found exactly one skipped commit since the executed full Tests at `608b230`
and omitted all heavy jobs. The [manual full matrix](https://github.com/uibcdf/pytest-receptor/actions/runs/36644802980)
passed all ten compatibility cells at `a7f3b0e`, executing serial and
distributed suites and the architecture/pytest-major assertions in each.
The [recovery probe](https://github.com/uibcdf/pytest-receptor/actions/runs/36678939997)
then recognized `a7f3b0e` as the watermark, found zero debt, and omitted heavy
jobs. Keep this issue open until the actual daily trigger, hosted PR
enforcement and platform claims are reviewed.

### 2026-10-03 — scheduled recovery and platform review

The [2026-10-02 scheduled run](https://github.com/uibcdf/pytest-receptor/actions/runs/37015450064)
completed successfully on `3b0e07c3afff7b283efa7254bc251a3b8670005c`.
Its decision job found one skipped commit after the executed full Tests
watermark `b75be9c46b1e5bd42994b3fad619fd8481b09896` and selected the full
matrix. Native job metadata confirms that all eight Linux cells and both
macOS cells executed their serial and distributed suite steps successfully;
none of those steps was skipped. The macOS / pytest 8 job printed
`3.13.15 arm64 8.4.2` during the architecture/interpreter assertion.
Additional real scheduled runs on
[2026-09-30](https://github.com/uibcdf/pytest-receptor/actions/runs/36722924337)
and [2026-10-01](https://github.com/uibcdf/pytest-receptor/actions/runs/36876146300)
also completed successfully. Scheduled delivery was delayed relative to the
cron time; no exact-time guarantee is claimed.

A fresh branch-protection API response retains strict, up-to-date status
checks for lint, benchmarks, packaging and all eight Python/pytest pairs,
with zero mandatory review approvals and administrator enforcement disabled.
The collaborator API identifies `dprada` and `LMMV` as administrators. This
confirms the intended direct-push exception without changing the protection.
The final hosted PR-route review is still pending.

`docs/compatibility.md` now distinguishes the full Linux version matrix,
representative macOS arm64 source installations, and qualification of a
particular released wheel or Conda artifact. The Conda runbook no longer
treats noarch packaging as proof of all-platform installation. Current CI
does not provide Windows runtime evidence; Intel macOS is outside the suite
support boundary. No existing release gains a platform claim from this review.

`tests/test_ci_backlog.py` protects the recovery mechanism: every Linux pair
must execute both suites, a skipped commit stays due through ordinary commits,
probes/PRs/other branches cannot clear debt, and uncertain acquisition runs
the full matrix. Its four tests passed locally during this review.

### 2026-10-03 — hosted PR gate review and closure

[PR #13](https://github.com/uibcdf/pytest-receptor/pull/13) exercises the
ordinary pull-request route for this closing change. On head
`919ee0db62fa47222e544addd0d8629cebf5e4de`, GitHub reported
`isDraft=false`, `mergeable=MERGEABLE`, `mergeStateStatus=BLOCKED` and
`statusCheckRollup.state=PENDING`. All eleven required Tests contexts were
present and pending or executing; reporting governance had already passed.
The blocked state therefore was neither a draft nor a merge conflict.
The protection snapshot requires those exact contexts from GitHub Actions
(app ID 15368) with strict up-to-date status checks.

This is an observed hosted merge gate under the available administrator
account, together with inspection of the protection and collaborator APIs.
It does not impersonate a non-administrator or claim an attempted external
merge. Administrator bypass remains available, and is not used to integrate
this change while checks are pending. Final PR checks and merge evidence
are retained in the owning issue and PR.

The daily route has now executed real skipped-debt recovery, the manual
matrix has executed all compatibility cells, and the ordinary PR exposes
the expected required-check gate. Weekly scheduling is source-inspected;
the first Tuesday after introduction has not yet occurred at this review.
Manual and daily executions verify the same full-matrix job graph without
claiming an already executed weekly trigger. Platform wording now states
only the tested Linux matrix and representative macOS arm64 source lanes.
The issue's remaining review gates are complete; the indexed report is
archived with its recovery guard and the dated observations above.
