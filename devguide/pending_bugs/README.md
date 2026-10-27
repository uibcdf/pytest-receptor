# Pending Bugs

Reported defects that have not been triaged yet.

There are no pending bug reports. The runtime stream lifecycle and documentation
cleanup defects discovered during `uibcdf/pytest-receptor#42` (#43/#44) are
archived in `resolved_bugs/`, alongside earlier repairs including #4 and #39.

See the [local reporting protocol](../reporting_protocol.md).

<!-- generated: devguide_index -->

### Open (1)

- [`collection_errors_counted_as_executed_failures.md`](collection_errors_counted_as_executed_failures.md) — [#46](https://github.com/uibcdf/pytest-receptor/issues/46) — Collection errors are counted as executed failed tests. *(open, reproduced)*

<!-- /generated -->

The distinction from [`../pending_proposals/`](../pending_proposals/README.md)
is intent, not severity:

| Directory | For |
| :--- | :--- |
| `pending_bugs/` | The plugin did something wrong. Wrong output, a crash, a disagreement with pytest. |
| `pending_proposals/` | The plugin should do something different. Design input, feature requests, integration needs. |

If you are unsure, file it as a bug. Deciding it was really a design gap is easy;
noticing a lost bug report is not.

## Priority

One category jumps the queue: **any disagreement with pytest about the outcome
of a run**. If the receptor reports a pass and pytest's exit status says
otherwise, or the counts do not match, that is the failure mode the whole
project is built to prevent. File it and say so directly.

Everything else is triaged at release planning.

## What to include

- The command you ran, in full, including any `addopts` in effect.
- The receptor output, and what pytest said instead.
- Versions: `pytest --version` and `pytest_receptor.__version__`.
- Whether it reproduces serially, under `-n`, or both.

A `RECEPTOR_ERROR` line in your output always means a bug here. The run itself
is safe — that is what the fallback exists for — but we want the traceback.

## Lifecycle

Once fixed, a report moves to [`../resolved_bugs/`](../resolved_bugs/README.md)
with its resolution appended, so this directory stays an inbox and the evidence
behind a register entry stays reachable.

Triaged bugs get an identifier in
[`../audit_action_register_2026-07-17.md`](../audit_action_register_2026-07-17.md),
which is the single complete work queue. Nothing is closed by deletion: a bug is
fixed, accepted as a documented limitation, or rejected with a reason.
