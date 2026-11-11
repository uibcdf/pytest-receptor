---
summary: Collection errors are counted as executed failed tests.
issue: uibcdf/pytest-receptor#46
status: resolved
opened: 2026-10-26
closed: 2026-11-11
severity: medium
verification: reproduced
area: [reporting, collection]
guard: tests/test_collection_counts.py
normative:
blocked_by: []
supersedes: []
---

# Collection errors are counted as executed failed tests.

## What
A collection SyntaxError is counted as `1 failed` and `1 of 0 executed` by the compact LLM summary. Native pytest reports one collection error and executes no tests. The compact header correctly says COLLECTION_ERROR and preserves exit 2, so this is count/phase fidelity, not a false-green result.

## How
Create a temporary `test_bad_syntax.py` containing:
```python
def test_incomplete(:
    pass
```
Run the same selection with `python -m pytest --noconftest -c /dev/null --rootdir=<temporary-directory> --receptor=human <test-path> -x`, then change only the profile to `--receptor=llm`.

Observed native: `1 error`, `Interrupted: 1 error during collection`, exit 2.
Observed compact: `COLLECTION_ERROR exit=2 | 1 failed | incomplete: 1 of 0 executed`, and `[1] Failure | 1 test | collect`.

## Why
The impossible executed/collected count can mislead agent CI reasoning. Found during uibcdf/molsysmt#421 / uibcdf/molsysviewer#264 receiving; a standalone malformed scratch file reproduces independently of those libraries.

## Acceptance criteria
Use public pytest event evidence to separate collection errors from failed/executed test items, preserve authoritative exit status and the collect phase, and avoid impossible counts. Add integration guards for SyntaxError/ImportError during collection, including `-x`/maxfail and partial collection, across applicable pytest versions. Human/native output remains the authority.

Linux, Python 3.14.7, pytest 9.1.1, pytest-receptor 1.2.1+22.g00a31c4 in the existing development environment. No source fix, new release or compatibility-matrix claim.

## What is measured and what is assumed

The reported behavior was executed in the existing Python 3.14 environment.
No clean-install or full compatibility-range conclusion is inferred.

## Alternatives and refuted paths

The reproduction excludes the molecular viewer. Native authority and the direct
provider remain separate from the compact or consumer presentation. The caller
will not rewrite inputs or reinterpret successful/failed exits to hide the gap.

## Scope and exclusions

This report records the defect and requested provider-owned guard. It does not
change runtime code, dependencies, release tags or publication state.

## Xdist receiving observation — 2026-10-29

During the standalone source review in uibcdf/molsysviewer#270, native JUnit
records 3,288 passed cases, eight failed cases, 21 skipped and four collection
errors (the same helper import problem reported by four xdist workers).
The compact LLM header instead reports nine failed cases: it groups the one
unique collection failure with eight call failures. This is not a false pass;
the authoritative exit remains 1. It is additional mixed collection/execution
and worker-deduplication evidence for this existing issue, not a new defect.

The consumer corrected its unsafe helper import, recovered the affected
checks separately and kept the original failed campaign. The consumer receipt
is referenced by owning issue uibcdf/molsysviewer#270. No receptor source,
dependency, tag or reporting status was changed in this receiving note.

## Provider correction — 2026-11-11

Keep failed collectors in a separate normalized set. They contribute to errors
but never runtime outcomes/executed counts. Repeated worker reports remain
in the stream and count once per collector; render diagnostic occurrences as
collectors rather than tests. Preserve pytest exit codes. Successful collect-only
keeps execution incomplete and explicitly reports collected/zero executed.
Sixteen focused regression cases cover SyntaxError, ImportError, partial
collection, -x/maxfail, continuation, collect-only and mixed xdist execution.
This source fix does not rewrite historical consumer evidence; actual installed
1.2.3 receiving is tracked separately in uibcdf/pytest-receptor#52.

## Resolution evidence — 2026-11-11

Implementation: d1d2349 (the immutable owner commit contains runtime changes,
regressions, route review and preserved consumer observations). Local focused
checks, exact pytest 8.0.0 API-floor checks and the completed Python 3.14.7
pytest 9.1.1 source suite are retained by the 1.2.3 campaign. Public installation
and hosted compatibility are separately qualified in uibcdf/pytest-receptor#52;
these source results do not claim registry delivery or downstream adoption.
