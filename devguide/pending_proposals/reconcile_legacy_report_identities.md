---
summary: Reconcile pre-protocol resolved-report identities without losing field evidence.
issue: uibcdf/pytest-receptor#10
status: active
opened: 2026-09-28
closed:
verification: inspected
area: [governance, reporting, history]
guard:
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

Fourteen legacy bug documents and three legacy proposal documents are
registered in the manifest. They remain in `resolved_bugs/` and
`resolved_proposals/` at their original paths. The exception is owned by this
issue and must be reviewed by 2026-12-31; the offline guard fails after that
date until the review date or entries are resolved.

## Acceptance criteria

Every manifest entry is reconciled with a valid issue-backed report or an
explicit suite-approved non-report classification. The manifest is empty,
and no historical claim or reproducer was removed. The generated archive
index and offline guard pass, and the issue closes with the final decision.
