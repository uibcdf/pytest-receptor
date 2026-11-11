---
summary: Automate bounded public Zenodo verification and overdue recovery.
issue: uibcdf/pytest-receptor#53
status: open
opened: 2026-11-11
closed:
verification: inspected
area: [governance]
guard:
normative: MOLSYSSUITE_GUIDE.md
blocked_by: []
supersedes: []
---

# Automate bounded public Zenodo verification and overdue recovery

## What

Adopt the qualified common read-only archival verifier before the next applicable
public release. The current 1.2.3 source archive is independently verified in
record 24146737, version DOI 10.5281/zenodo.24146737. This proposal concerns future
automation, not a missing current archive or package-publication blocker.

## How

Reuse an immutable qualified shared workflow with contents:read only, verified
concept DOI `10.5281/zenodo.22863479`, and a fixed adoption cutoff including
1.2.3. Cover release:published, manual exact-tag checks and bounded scheduled
discovery at nominal six-hour intervals. Add owner controls and declare the
administrative dependency route; retain actual hosted receiving separately.

## Why

The component is primary/stabilizing with required archival. Its checkout has no
maintained scheduled/manual caller. A release hook does not establish public
archival; the 1.2.3 manual exact-tag probe and downloaded source inventory do.

## What is measured and what is assumed

The current public record/file checksum and selected frozen source files were
verified; see `../release_evidence/1.2.3.json`. Automatic future receiving has not
been implemented or measured. Wheels and Conda archives are not claimed archived.

## Alternatives and refuted paths

Do not infer archival from a hook/account toggle, invent a DOI, replay a hook,
create a duplicate deposit, retag or rebuild 1.2.3. A documented equivalent is
allowed by the common policy if it supplies the same bounded evidence/recovery.

## Scope and exclusions

Owner: pytest-receptor maintainers. This is read-only archival automation with no
scientific dependency installation or credential/deposit/hook mutation. It does
not imply historical backfill or consumer scientific qualification.

## Acceptance criteria

Preserve original publication clocks, complete discovery/pagination, exact
source-file inventory and separate verified/pending/absent/invalid/service-
unavailable states. Track the 72-hour owner intervention window and documented
maintainer investigation route. Validate trigger/input/read-only controls and
actual hosted evidence under the shared Zenodo policy before the next release.
