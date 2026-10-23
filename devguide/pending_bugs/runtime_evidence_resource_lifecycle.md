---
summary: Retain runtime stream ownership and expose cleanup failures.
issue: uibcdf/pytest-receptor#43
status: active
opened: 2026-10-23
closed:
severity: medium
verification: reproduced
area: [resources, output, lifecycle]
guard: tests/test_runtime_resources.py
normative:
blocked_by: []
supersedes: []
---

# Runtime evidence stream lifecycle

## What

The #42 review reproduces lost stats-baseline ownership after terminal-writer
setup failure, suppressed baseline/artifact close/removal errors, and artifact
constructor/finalization paths without explicit handle cleanup. Discard close
failure can also replace the original pytest result; cache invalidation errors
are silently swallowed. Caller-requested artifacts must remain available for
failure analysis even when their streams cannot be finalized normally.

## How

Owned private files and controlled setup/read/write/close/removal faults exercise
the actual component operations. Native pytest subprocess results are compared
with compact runs, including a session-hook failure. Direct descriptor/file
checks verify release of raw fdopen and partial-construction resources.

The correction cleans failed stats setup/read, diagnoses baseline/cache/discard
cleanup faults nonfatally, exposes artifact closure as ArtifactError, and closes
partial constructor/finalization resources. The pytest adapter catches lifecycle
errors and retains caller output. If cache invalidation fails, the documented
warning explains that old cached text is not current-run evidence.

## Why

Optional reporting must not leak scratch or silently lose ownership, nor turn a
passing pytest run into a failing process solely because teardown failed.
Deleting caller evidence to conceal an incomplete artifact is not a repair.

## What is measured and what is assumed

Controlled probes on baseline `bfb34e3` reproduce file retention with lost
ownership and empty cleanup diagnostics. The first finalized eighteen-case
regression version fails sixteen cases and passes two controls on an isolated
copy of that baseline; its actual imported source is verified. Later controls
add cached-report invalidation, stats-close diagnostics and preservation of the
original interrupt when cleanup also fails. Injected faults are
not claims of actual OS close/removal failures.

Existing artifact integrity, reporter stream and native/compact output guards
remain relevant. Local validation uses Python 3.14.7 in
`molsyssuite@uibcdf_3.14`; other compatibility and hosted checks are recorded at
the implementation commit before closure. The final 24 new controls (#43/#44)
pass, and the full local source suite passes 254 tests with ten optional
integration skips (pytest-subtests/pytest-rerunfailures unavailable locally).
The final unchanged guard files also run against a managed original-source copy:
all 24 cases execute, with 22 failures and two passing controls. That copy's
provider import and docs Makefile are bound to baseline `bfb34e3`; the managed
source/fixtures are removed after the child exits.

## Alternatives and refuted paths

Suppressing teardown errors hides retained resources. Raising cleanup exceptions
through pytest unconfigure changes the run's authority. Removing partial JSONL
destroys caller evidence. The repair instead distinguishes disposable baseline
files from persistent explicit destinations and surfaces nonfatal diagnostics.

## Scope and exclusions

Only runtime evidence file/stream ownership and cleanup diagnostics. No schema,
public reader contract, test counts, fingerprint, scientific selection or package
version changes. Actual unremovable resources cannot be certified removed; their
diagnostics retain the resource identity for owner follow-up.

## Acceptance criteria

The guard exercises actual files/descriptors and pytest subprocesses for success
and failure, preserves caller bytes and pytest exit status, and detects silent
cleanup faults. Existing artifact/output/terminal checks and relevant CI pass;
the result is archived and synchronized with #43.
