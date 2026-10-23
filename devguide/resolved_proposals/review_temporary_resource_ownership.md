---
summary: Complete the component-owned temporary-resource lifecycle review.
issue: uibcdf/pytest-receptor#42
status: resolved
opened: 2026-10-10
closed: 2026-10-23
verification: inspected
area: [resources, tooling, governance]
guard:
normative: devguide/temporary_resources.md
blocked_by: []
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

## Owner disposition — 2026-10-23

The maintained operational review and implementation are published in
`44e459655a25d4367fc2d69f59b2ad74c081fb4c`. Discovered defects #43/#44 are
resolved with actual guards and archived evidence; existing #40/#41 remain
resolved. No remaining implementation exception is being used to claim their
success. Normal retained caller/workspace/consumer resources keep their explicit
owners and next affected-change/release or 2026-11-23 review trigger.

All 24 new controls pass after repair; the final unchanged guards on a managed
baseline copy fail 22 cases and pass two controls. The local complete source
suite passes 254 tests and skips ten optional integrations. Those local skips
are not represented as executed coverage.

[Hosted Tests 40017079423](https://github.com/uibcdf/pytest-receptor/actions/runs/40017079423)
passes all twelve jobs. Independent native source/attempt/job/step verification
confirms all eight Linux Python 3.11–3.14 × pytest 8/9 cells and sixteen executed
serial/distributed suite steps. Lint, wheel packaging, benchmark harnesses and
coverage publication pass. Reporting `40017079305`, policy `40017080274`, Conda
publication governance `40017079700` and Sphinx/Pages `40017079317` pass too.
This is source/tool validation, not a new public or installed package admission,
nor physical hosted-runner teardown proof.

After their subprocesses completed and durable evidence was recorded, all eight
explicitly task-created pytest fixture roots were checked for task custody,
removed and confirmed absent without cleanup failure. The probe and two managed
baseline source copies also cleaned themselves after child exit. The maintained
record lists actual removed paths separately from the nineteen historical
absences; no earlier deletion, recovered capacity or foreign ownership is
invented. Primary/shared/consumer resources remain preserved.

Report this bounded completed owner disposition to `uibcdf/molsyssuite#104`;
the shared rollout and `uibcdf/moli#61` retain their independent scope. No new
central duplicate issue, package publication or sibling implementation change
is needed.
