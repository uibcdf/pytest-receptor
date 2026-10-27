---
summary: Collection errors are counted as executed failed tests.
issue: uibcdf/pytest-receptor#46
status: open
opened: 2026-10-26
closed:
severity: medium
verification: reproduced
area: [reporting, collection]
guard:
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
