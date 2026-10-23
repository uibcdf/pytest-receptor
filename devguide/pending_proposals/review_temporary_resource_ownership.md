---
summary: Complete the component-owned temporary-resource lifecycle review.
issue: uibcdf/pytest-receptor#42
status: active
opened: 2026-10-10
closed:
verification: inspected
area: [resources, tooling, governance]
guard:
normative: devguide/temporary_resources.md
blocked_by: [uibcdf/pytest-receptor#43, uibcdf/pytest-receptor#44]
supersedes: []
---

# Component resource ownership and lifecycle

## What

Complete the owner review requested by `uibcdf/molsyssuite#104`, extending the
bounded 2026-10-08 receiving review without presenting guide delivery or earlier
focused repairs #40/#41 as complete operational compliance.

## How

The maintained operation table in `devguide/temporary_resources.md` records the
owner, useful lifetime, caller-resource protection and cleanup/failure handling
of current component scripts, tests, runtime streams, docs/build routes and
hosted qualification/publication callers. It separates inspected provider
custody from executed component controls and keeps future affected-route review
with dprada/LMMV, by 2026-11-23 or the next affected change/release.

Controlled probes reproduced two new implementation themes: runtime evidence
stream ownership/error visibility (#43) and unintended make-clean deletion
operands (#44). Their corrections and guards remain independently owned.
The developer runbook also incorrectly implied release-triggered Conda `main`
upload and Windows runtime admission. It now describes exact-file promotion,
separate PyPI publication and the actual Linux/macOS arm64 installed boundary.
Those are documentation corrections, not new package/platform qualification.

## Why

Contributors must distinguish disposable scratch from caller evidence, shared
environments, active human output and immutable public artifacts. A general
cleaner or blanket age/prefix deletion would not establish that distinction.

## What is measured and what is assumed

Nineteen explicit earlier task paths are absent on 2026-10-23; their earlier
removal is not attributed. The primary checkout/shared prefix, pre-existing
workspace caches/builds/editable metadata and an absent consumer worktree's Git
registration are preserved. They have their existing caller/consumer ownership,
not this task's deletion authority. The dated maintained record lists exact
paths and review triggers. This is separate from the central 55-path observation.

New regression controls use only owned private files and synthetic failures.
Source inspection, actual fixture cleanup, outcome preservation, hosted source
CI and public/installed artifact qualification remain separate evidence.
No public publisher, new solver/installed-artifact qualification, scientific
suite, GUI or browser is run merely to close this review. Ordinary source CI
retains its existing dependency installation and package-build jobs.

## Alternatives and refuted paths

- Guide synchronization alone cannot establish tool lifecycle behavior.
- Historical absence does not prove who removed a path or reclaimable capacity.
- Automatically pruning another consumer's worktree or deleting existing
  workspace artifacts would exceed the established ownership of this task.
- No new shared cleanup framework is needed: local operations use stdlib/pytest
  ownership, while existing shared provider routes retain their owners and pins.

## Scope and exclusions

Owner-local operational disposition and the two discovered component defects.
The broader shared rollout stays `uibcdf/molsyssuite#104`, with platform
coordination in `uibcdf/moli#61`. No sibling repository implementation, shared
policy, immutable artifact, source tag or environment is changed.

## Acceptance criteria

- A maintained operation table and resource disposition name owners/lifetimes.
- #43/#44 have verified corrections or explicit owned implementation exceptions.
- Actual task cleanup is reviewed separately from retained caller resources and
  unknown historical deletion.
- Run local component/report checks, archive the review and send its exact-source
  evidence back to `uibcdf/molsyssuite#104`.
