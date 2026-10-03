---
summary: Make progress snapshots agree with completed-test counts.
issue: uibcdf/pytest-receptor#30
status: resolved
opened: 2026-10-03
closed: 2026-10-03
severity: low
verification: inspected
area: [reporting, compatibility]
guard: tests/test_plugin.py::test_progress_percent_always_matches_its_own_fraction
normative:
blocked_by: []
supersedes: [uibcdf/pytest-receptor#21]
historical_register: PR-PILOT-014
historical_resolved: 2026-08-02
---

# Progress snapshot percentages match completed counts

## What

The MolSysViewer re-observation on 2026-08-02 displayed both
`20% 647/1168` and `40% 647/1168`. Neither percent describes
the printed completed fraction (55%), and both reuse one snapshot.

## How and why

PR-PILOT-014 replaced warm-up backfill with live crossings and
percentages computed from the displayed completed count. Milestones
crossed during the silent warm-up are omitted; twenty-percent
thresholds bound the stream while 100% marks completion.

The unchanged original observation and both historical narratives
remain in [the MolSysViewer report](full_suite_empty_success_output_molsysviewer.md).
The earlier missing final summary has a separate review identity;
this report owns only the demonstrated progress snapshot defect.

## Acceptance criteria

Every printed percentage matches its completed fraction, snapshots
are unique and increasing, and the final milestone is 100%.


## Identity and closure review — 2026-10-03

Owning identity: `uibcdf/pytest-receptor#30`. Reconciliation: `uibcdf/pytest-receptor#10`.
Historical register: `PR-PILOT-014`; recorded historical outcome: 2026-08-02.

The metadata dates refer to this issue-backed review. This companion report
separates the progress defect from the unchanged pre-protocol observation
in the MolSysViewer report linked above. This review inspects the current
implementation and relevant assertions; it does not rerun the historical
consumer suite or certify an old release again.

The long-warm-up regression requires every displayed percent to equal finished*100//collected, strictly increasing unique snapshots and a final 100%. This directly rejects the observed 20% and 40% labels both attached to 647/1168, and preserves the intentional omission of milestones crossed during warm-up.

Durable guard: `tests/test_plugin.py::test_progress_percent_always_matches_its_own_fraction`. Its relevance is explained above.
