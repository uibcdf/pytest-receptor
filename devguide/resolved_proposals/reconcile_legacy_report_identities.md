---
summary: Reconcile pre-protocol resolved-report identities without losing field evidence.
issue: uibcdf/pytest-receptor#10
status: resolved
opened: 2026-09-28
closed: 2026-10-03
verification: inspected
area: [governance, reporting, history]
guard: tests/test_reporting_protocol.py
normative:
blocked_by: []
supersedes: []
---

# Reconcile legacy report identities

## What

Retire the bounded exception in `devguide/legacy_report_manifest.toml` by
reconciling seventeen pre-protocol resolved documents with the current
issue-backed archive contract.

## How

Review each original PR-PILOT, PR-UX or PR-REL register identity against
GitHub ownership and its resolution evidence. One document already cites
`uibcdf/pytest-receptor#3`; the other sixteen have no known GitHub issue.
Do not fabricate a retrospective issue merely to satisfy a validator. If a
document represents an independently closable theme, create or identify its
real owning issue and append a dated metadata correction while preserving
the original claim. If it is only supporting evidence for a broader decision,
seek a suite-level classification and remove it from the report exception.
Regenerate the index whenever an entry leaves the manifest.

## Why

The old project register preserved useful pilot evidence before the common
GitHub issue protocol existed. Leaving those records silently exempt would
allow an issue-less archive to grow; deleting or relabeling them would lose
their provenance.

## What is measured and what is assumed

At filing, fourteen legacy bug documents and three legacy proposal documents
were registered in the manifest. They remain in `resolved_bugs/` and
`resolved_proposals/` at their original paths. The exception is owned by this
issue and must be reviewed by 2026-12-31; the offline guard fails after that
date until the review date or entries are resolved.

## Acceptance criteria

Every manifest entry is reconciled with a valid issue-backed report or an
explicit suite-approved non-report classification. The manifest is empty,
and no historical claim or reproducer was removed. The generated archive
index and offline guard pass, and the issue closes with the final decision.

## Resolution — 2026-10-03

All seventeen original documents now have owning GitHub identities, while
their complete original bodies remain byte-identical beneath the added
front matter and before the dated review. A SHA-256 comparison against the
pre-reconciliation snapshot verified every original body. Register references
and original resolution dates remain explicit historical fields.

Python 3.14 delivery reuses `uibcdf/pytest-receptor#3`; its real opening and
closing dates (2026-09-20 and 2026-09-21) are retained. The other sixteen
documents received retrospective issues after scope and guard review. Their
issue-backed opening/closure dates describe this review, not invented July
or August GitHub activity. Existing issues #4 and #5 have different scopes
and were not repurposed to absorb unrelated historical defects.

The MolSysViewer record contained two distinct themes. Its original empty
stdout observation is reviewed in `uibcdf/pytest-receptor#26`. The later
successful observation does not establish the asserted deselection-based
cause, so that investigation is withdrawn with the original claim retained
and a dated correction appended. The reproducible percentage/count mismatch
has its own resolved issue, `uibcdf/pytest-receptor#30`, and companion report
`resolved_bugs/progress_snapshot_percent_matches_completed_count.md`.
That repair supersedes the obsolete warm-up backfill in
`uibcdf/pytest-receptor#21`; the old record is indexed as superseded rather
than advertising the backfill as current behavior. No record was removed
from a queue by reclassifying it as non-report evidence.

The remaining retrospective issues #14–#20, #22–#25 and #27–#29 retain
their relevant current pytest selectors and explain how each assertion
protects the reported mechanism. A new guard for #19 reads the report at
the path declared by four maintained documents after an actual pytest run,
so a missing cache `d/` component cannot silently return. The README's stale
claim that the text report is published during execution is corrected to
session-finish publication under #20; the existing stale-report regression
checks absence during the next session.

The manifest is empty and explicitly retired. `tests/test_reporting_protocol.py`
validates every current report and generated index, proves that a retired
empty manifest has no deadline failure, rejects attempts to repopulate it,
and still rejects an overdue live exception. This is the durable guard for
retiring the exception without disabling normal identity enforcement.
Archived tests and historical installed-release evidence remain separately
classified; this reconciliation does not claim a new consumer suite run or
revalidation of an old published package.

Local verification on 2026-10-03 passed all 206 tests, including the
documentation-path and lifecycle guards, plus Ruff checks, strict Sphinx
build and the generated-index check.
