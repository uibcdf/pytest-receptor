# Resolved Bugs

Field reports that have been fixed, kept with their resolution attached.

Moved here from [`../pending_bugs/`](../pending_bugs/README.md) so the inbox
stays an inbox. Nothing is closed by deletion.

## Why these are kept

- They are the **evidence** for their register entries. `PR-PILOT-001` through
  `PR-PILOT-003` cite this directory as their source; deleting the reports would
  leave findings in the work queue with nothing behind them.
- They contain **reproducers**, which outlive the bug. If one of these
  regresses, this is where the case that caught it lives.
- They record **what the pilot experienced**, which is the evidence the whole
  dogfooding programme exists to produce. A fixed bug is not an uninteresting
  bug: three of these came from a single afternoon of real use, which is itself
  the argument for running pilots.

## Contents

| Report | Register | Fixed |
| :--- | :--- | :--- |
| `setup_errors_counted_as_failed.md` | PR-PILOT-001 | 2026-07-18 |
| `external_test_paths_produce_invalid_rerun_and_location.md` | PR-PILOT-002 | 2026-07-18 |
| `warning_group_truncation_is_not_diagnostically_sufficient.md` | PR-PILOT-003 | 2026-07-18 |
| `xdist_progress_is_not_bounded_by_deciles.md` | PR-PILOT-004 | 2026-07-18 |
| `xdist_startup_noise_leaks_into_compact_stdout.md` | PR-PILOT-005 | 2026-07-18 |
| `documented_full_report_path_misses_pytest_cache_d.md` | PR-PILOT-006 | 2026-07-18 |
