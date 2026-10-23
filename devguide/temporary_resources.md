# Component resource ownership review

Owner: pytest-receptor maintainers (`dprada` / `LMMV`). Review date: 2026-10-23.
Owning review: `uibcdf/pytest-receptor#42`; shared policy:
`uibcdf/molsyssuite#104`, delivered through `MOLSYSSUITE_GUIDE.md`.
This is the component's operational disposition, not a local copy of suite policy.
Revisit affected rows when their tools, workflow/provider pins or resource routes
change, at the next release closeout, or by 2026-11-23, whichever occurs first.

## Operations, useful lifetimes and custody

| Operation and implementation | Resource owner / useful lifetime | Success, failure and error handling |
| --- | --- | --- |
| Token benchmark, `devtools/benchmarks/run_benchmarks.py` | The invocation exclusively claims `${tempdir}/receptor-bench` for one scenario. Caller measurement output remains separate. | Refuses occupied paths, including another active run; `finally` removes only its claimed directory and exposes removal failures. #40 guards concurrent and caller custody. |
| RSS/time benchmark, `devtools/benchmarks/run_performance.py` | Managed unique scratch lasts through measurement; the direct child belongs to that sample. Explicit `--json` output belongs to the caller. | `TemporaryDirectory` cleans success/failure. #41 kills/reaps its direct child before scratch teardown on wait failure/interruption. No descendant-process or Windows RSS claim. |
| Runtime stats, `pytest_receptor/plugin.py` | The plugin owns its named baseline and discard stream until the final native reporter use. It borrows the native writer and real stdout. | #43 closes/removes baselines after failed setup, read and normal use; warns on cleanup faults without changing pytest's exit. Discard stream close faults are likewise nonfatal and visible. Borrowed stdout/writers are not closed. |
| Runtime evidence, `pytest_receptor/artifact.py`, `plugin.py` | The plugin owns the open stream. Explicit JSONL destinations and cached final reports are caller evidence after writing, including useful partial JSONL. | #43 closes constructor/finalization failures, exposes close errors and catches them at the pytest adapter. It preserves requested output bytes and reports cleanup failure. A failed startup cache invalidation warns that the old cached report can remain. |
| Tests, `tests/` | `tmp_path`, pytester and stdlib `TemporaryDirectory` own disposable fixtures. Pytest's retained numbered roots remain framework/caller-owned for failure diagnosis. | Managed fixtures and synchronous subprocess helpers delimit test work. Optional `--basetemp` is an explicit disposable directory selected by that test invocation; never point it at a borrowed directory. No global pytest-root deletion. Resource regressions exercise faults inside private fixtures. |
| Archive checks, `devtools/check_release.py` | The caller owns wheel/sdist inputs; the checker borrows bounded archive/member streams. | Context managers close archive/member readers; no package extraction or input deletion. `tests/test_packaging.py` protects artifact/resource checks, not physical package-manager teardown. |
| Dependency/source preflight, `check_dependency_routes.py`, `check_release_gates.py` | The caller owns the exact provider checkout and optional source-gate receipt. | Checked synchronous children finish before returning; file readers/writers have bounded uses. Explicit receipts remain caller outputs. Provider checkout creation/removal stays with its creating task, not the adapter. No independent solver, cache or environment is created by these adapters. |
| Reporting/recovery, `devguide_index.py`, `devguide_reports.py`, `ci_backlog.py` | Maintained reports/indexes and `GITHUB_OUTPUT` are caller/workflow outputs. | Source/file/network contexts and synchronous Git commands are scoped. No disposable checkout or environment is owned here. Rewritten indexes and recovery output are intentionally retained; these tools do not delete neighboring working files. |
| Local documentation, `docs/Makefile`, `docs/conf.py` | The caller selects and owns the build directory while preview/review needs it. | Explicit `make clean` removes selected generated contents; #44 quotes its operand and ends options, preserving unrelated neighboring work even for spaces/leading dashes. Removal failures propagate through make. A build alone does not authorize a blanket cleanup of user directories. |
| Local builds/editable development | The creating task owns disposable `build/`, `dist/` and isolated diagnostic environments until verification ends. Shared development environments and editable metadata/version files have workspace lifetimes. | Review before disposing of generated work. Do not remove the active shared prefix, editable metadata, human build outputs or a registered worktree as a side effect of a checker. Local diagnostic Conda builds are not public publication. |
| Hosted test/full-test and documentation workflows | Job-local checkouts, `/tmp/clean`, docs output, wheels, coverage data and caches belong to the selected GitHub-hosted job. Uploaded evidence has its declared artifact/service retention. | Successful and failed jobs retain only uploaded outputs according to each workflow's upload condition and retention. Components do not clean other jobs/hosts or infer physical teardown from a green suite. Runner custody is separate from artifact verification. |
| PyPI, build/upload/promote and installed Conda callers | The job owns build/install prefixes and temporary downloads. Published coordinates are immutable registry outputs. Exact source, archive/digest, matrix, promotion and dependency-closure receipts retain their release evidence lifetime. | Upload conditions preserve the declared evidence. Promotion reuses the same file, without rebuilding/deleting staging. Shared publisher/installed helpers remain provider-owned at the caller's exact pins; changing those pins requires a new affected-route review. This review performs no upload, promotion, solver run or installed-platform qualification. |

The reviewed operation inventory covers the component's current developer
scripts, tests, runtime evidence handling, documentation and checked-in workflows.
It does not claim that all possible third-party tools or platforms have been
executed. No new universal resource-test matrix or global cleanup tool is added.

For the selected hosted labels, GitHub documents a fresh job image/VM and
job-scoped temporary storage. Its temp cleanup depends on deletion permission;
those are provider contracts, not an independently observed teardown of our jobs.
See [runner images](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
and [runner temp context](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts#runner-context).
Moving a route to a persistent/self-hosted runner would require a new explicit
environment/workspace cleanup disposition before relying on these rows.

## Executed controls and limits

- Existing benchmark scratch/custody and interrupted direct-child guards stay
  owned by #40/#41. Their focused suite is rerun during this review.
- `tests/test_runtime_resources.py` owns #43's controlled setup/read/write/close
  and cleanup cases, caller evidence preservation and actual pytest subprocess
  outcome comparisons. Real private files/handles are used; injected faults are
  not a claim that an actual filesystem deletion/close failure occurred.
- `tests/test_docs_resources.py` owns #44: the actual make target runs inside
  private fixtures. Before correction it deletes the controlled neighboring
  sentinel for a spaced name and rejects a leading dash; after correction it
  preserves caller bytes and removes only selected generated contents.
- `tests/test_artifact.py`, existing terminal/late-exit tests and reporting
  checks retain their own contracts. Full source CI is separate from installed
  package, scientific, native GUI/browser and other-platform qualification.

The review discovers and corrects #43/#44; it does not reopen resolved #40/#41.
No unresolved implementation exception is being used to claim those repairs
complete. Actual local/hosted checks and closeout are recorded in their owning
reports and issues; source inspection alone is not executed cleanup evidence.

## Explicit historical-path observation — 2026-10-23

The following nineteen task paths were checked individually with `lstat` and
were absent. No deletion or attribution of their earlier removal is claimed:

```text
/tmp/pytest-receptor-121-evidence
/tmp/pytest-receptor-121-public-installs
/tmp/pytest-receptor-121-installed-source
/tmp/pytest-receptor-121-release-dist
/tmp/pytest-receptor-121-verify.py
/tmp/pytest-receptor-121-native-installed.py
/tmp/pytest-receptor-121-installed-closure.py
/tmp/pytest-receptor-121-public-installs.py
/tmp/pytest-receptor-121-record-release.py
/tmp/pytest-receptor-121-final-candidate.json
/tmp/pytest-receptor-121-suite-announcement.md
/tmp/pytest-receptor-121-release-notes.md
/tmp/pytest-receptor-121-create-release.json
/tmp/pytest-receptor-121-update-release.json
/tmp/pytest-receptor-121-close-32.md
/tmp/pytest-receptor-121-accepted-pin-comment.md
/tmp/pytest-receptor-issue39-before
/tmp/pytest-receptor-issue39-after
/tmp/pytest-receptor-issue39-suite
```

This is distinct from the central 2026-10-10 observation of 55 historical paths;
neither is a complete `/tmp` inventory or a measurement of reclaimed space.

## Retained resources and closeout

The primary checkout, `molsyssuite@uibcdf_3.14`, editable metadata and generated
`_version.py` remain necessary for development. Existing `.pytest_cache/`,
`.ruff_cache/`, `docs/_build/` and `build/` were observed and preserved: this task
did not establish exclusive ownership or absence of active/human changes in
those pre-existing resources. `dist/` was absent. Their creating callers own
review/removal when their current use ends; this is ordinary workspace
retention, not an automatic deletion queue.

Git also reports a stale registration for
`/tmp/opencastp-guide-sources/pytest-receptor`; its directory is absent. The
consumer's registration is preserved, not pruned or attributed to this task.
The next consumer source handoff or the dated review above must reconcile that
metadata with its owner. No private consumer contents were inspected.

This review's managed probes/source copies clean themselves after child
completion. Explicitly owned pytest fixture roots and issue-comment drafts are
removed after their useful evidence is committed and synchronized. The owning
closeout records distinguish those actual removals from historical absence.
Retain failure evidence while useful, keep caller outputs outside disposable
scratch, and leave cleanup failures visible with their owner if removal fails.

### Executed closeout — 2026-10-23

Implementation `44e4596` passes the new 24 controls, the full local source suite
(254 passed / ten optional-integration skips) and hosted Tests `40017079423`:
all twelve jobs, including eight Linux Python 3.11–3.14 × pytest 8/9 cells with
both suite steps independently verified as executed successes. The component
reporting, policy, publication-control and Sphinx/Pages runs also pass. Exact
run identities and scope are retained in the archived #42/#43/#44 records.

Following completed subprocesses, the eight task-created fixture roots below
were checked individually as owned, non-symlink directories, removed and
confirmed absent. No cleanup failure occurred:

```text
/tmp/pytest-receptor-issue42-before
/tmp/pytest-receptor-issue42-after
/tmp/pytest-receptor-issue42-runtime
/tmp/pytest-receptor-issue42-focused
/tmp/pytest-receptor-issue42-docs-before
/tmp/pytest-receptor-issue42-final-focused
/tmp/pytest-receptor-issue42-final-runtime
/tmp/pytest-receptor-issue42-suite
```

The probe and two managed baseline source/fixture copies were automatically
removed after their child operations; issue comment drafts last only through
their final upload. This execution does not establish the historical absence
attribution, reclaimed physical space, complete `/tmp` inventory or physical
hosted-runner teardown. No primary, shared environment, pre-existing workspace
output or foreign consumer worktree registration was a deletion operand.
