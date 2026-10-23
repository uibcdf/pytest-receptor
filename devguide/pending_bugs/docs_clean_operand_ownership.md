---
summary: Keep documentation cleanup within the selected build directory.
issue: uibcdf/pytest-receptor#44
status: active
opened: 2026-10-23
closed:
severity: medium
verification: reproduced
area: [resources, documentation, tooling]
guard: tests/test_docs_resources.py
normative:
blocked_by: []
supersedes: []
---

# Documentation clean operand ownership

## What

`docs/Makefile` expands `rm -rf $(BUILDDIR)/*` without quoting the build directory
or ending rm options. A spaced build name becomes multiple deletion operands;
a leading dash is interpreted as an option. This was found in the #42 review.

## How

The actual make target runs inside a private pytest fixture containing an owned
`scratch output` build and unrelated `scratch/caller.txt` sentinel. Before
correction, the sentinel is deleted while the intended build survives. The
leading-dash control exits nonzero. Both regressions fail on the original source.
The correction quotes the directory and supplies `--` before the glob.

## Why

An explicit build cleanup must preserve neighboring caller work, even when the
caller selects an ordinary spaced directory. This reproduction changes only
synthetic fixture files; no real human file loss is claimed.

## What is measured and what is assumed

Two real make invocations reproduce the defects on 2026-10-23 under Python
3.14.7. The regression asserts the actual subprocess exit, caller bytes and
selected output removal. It does not merely match the command text. Hosts
without make skip this optional tool-specific guard.

## Alternatives and refuted paths

Deleting all build-looking directories or forcing a fixed global scratch path
would exceed the caller's selection. A separate cleaner is unnecessary.

## Scope and exclusions

The existing explicit clean interface and generated-content selection remain.
No blanket cleanup, neighboring output deletion, package build or Sphinx runtime
change is introduced. Actual cleanup command errors still propagate through make.

## Acceptance criteria

Both spaced and leading-dash builds clean successfully, preserving neighboring
caller bytes. Run the guard and relevant reporting/CI checks, archive the record
and synchronize #44.
