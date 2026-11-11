---
summary: Document same-session exhaustive skipped-node recovery after detail truncation.
issue: uibcdf/pytest-receptor#51
status: active
opened: 2026-11-11
closed:
verification: inspected
area: [reporting, governance]
guard: tests/test_artifact.py::test_same_session_junit_recovers_late_skips_after_detail_truncation
normative: docs/artifacts.md
blocked_by: []
supersedes: []
---

# Document same-session exhaustive skipped-node recovery after detail truncation.

## What and how

Document the existing supported read_artifact boundary and same-session
pytest JUnit fallback. Finalized/integrity-valid transport and final counters
do not establish exhaustive phase detail. Require explicit untruncated final
policy before deriving exhaustive node sets. Live evidence_limit marks loss;
a missing final record cannot certify completeness. Unknown metadata, missing/
partial original JUnit, ambiguous testcase-to-node identity or counter mismatch
requires explicit incomplete recovery, never an apparently exhaustive list.

## Evidence and limits

A real pytest session with 120 passes and three late skips reaches the 64-KiB
cap. All three skip phase details are absent, final skipped remains three,
transport/integrity remain valid, the size ceiling holds, and same-session
JUnit retains all three expected testcase identities. Documentation and the
canonical consumer guide explain exact-selector correspondence limits.
No new query/API, mandatory unbounded retention or schema-major change is
needed. Consumer origin: uibcdf/molsysmt#612; central handoff is
uibcdf/molsyssuite#188.
