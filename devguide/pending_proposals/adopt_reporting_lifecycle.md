---
summary: Adopt the MolSysSuite issue-backed reporting lifecycle locally.
issue: uibcdf/pytest-receptor#8
status: active
opened: 2026-09-28
closed:
verification: inspected
area: [governance, reporting]
guard:
normative:
blocked_by: []
supersedes: []
---

# Adopt the reporting lifecycle

## What

Give current issue-backed reports a generated index, offline validator,
template, contributor guidance and independent governance job under
`uibcdf/molsyssuite#60`.

## How

Preserve existing issue-backed reports `#4`, `#5` and `#6`, add an identity
to the active CI-annotations proposal (`#9`), and retain the pre-protocol
resolved documents in their current paths with a bounded legacy manifest.
The legacy identity review is a separate local issue `#10`. Make the offline
validator reject new issue-less reports and stale indexes.

## Why

Recent reports follow the common protocol, but the queues and resolved-record
tables are manual. The 2026-07/08 field records use PR-PILOT and PR-UX
identifiers; treating these as GitHub identities would be false, while
deleting them would erase the pilot evidence.

## What is measured and what is assumed

On 2026-09-28, inspection found three modern issue-backed archived reports,
seventeen pre-protocol resolved documents without common front matter, one
active proposal without an issue, and no local index command or offline
reporting validator. One of the seventeen cites GitHub issue `#3` in prose.

## Scope and exclusions

This change governs report records. It does not alter pytest behavior,
scientific tests or the separate Python CI-lane rollout. Historical identity
backfill is owned by `#10` and remains open after this machinery is adopted.

## Acceptance criteria

The active reports and modern archive have valid issue identities and
generated indexes. The legacy records remain byte-preserved and visible in
the generated archive index. The validator rejects new issue-less reports,
false closure and missing guard selectors; its standalone hosted job passes.
Close this implementation issue with an archived record and durable guard.
