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

Modern issue-backed records and pre-protocol register evidence are listed
below. The legacy identity exception is owned by `uibcdf/pytest-receptor#10`.

<!-- generated: devguide_index -->

### Resolved (1)

- [`discard_stream_remains_unclosed_after_pytest.md`](discard_stream_remains_unclosed_after_pytest.md) — [#4](https://github.com/uibcdf/pytest-receptor/issues/4) — Close the late-terminal discard stream without leaking ResourceWarning *(resolved, reproduced)*

### Legacy register evidence (14)

- [`deselected_tests_reported_incomplete.md`](deselected_tests_reported_incomplete.md) — PR-PILOT-013 — resolved 2026-07-28; legacy identity review
- [`documented_full_report_path_misses_pytest_cache_d.md`](documented_full_report_path_misses_pytest_cache_d.md) — PR-PILOT-006 — resolved 2026-07-18; legacy identity review
- [`external_single_test_rerun_loses_path_with_fixed_rootdir.md`](external_single_test_rerun_loses_path_with_fixed_rootdir.md) — PR-PILOT-012 — resolved 2026-07-22; legacy identity review
- [`external_test_paths_produce_invalid_rerun_and_location.md`](external_test_paths_produce_invalid_rerun_and_location.md) — PR-PILOT-002 — resolved 2026-07-18; legacy identity review
- [`full_suite_empty_success_output_molsysviewer.md`](full_suite_empty_success_output_molsysviewer.md) — PR-PILOT-013, PR-PILOT-014 — resolved 2026-08-02; legacy identity review
- [`molsysmt_incomplete_stats_closes_terminal_stream.md`](molsysmt_incomplete_stats_closes_terminal_stream.md) — PR-PILOT-011 — resolved 2026-07-21; legacy identity review
- [`molsysmt_xdist_incomplete_run_reported_pass.md`](molsysmt_xdist_incomplete_run_reported_pass.md) — PR-PILOT-008 — resolved 2026-07-21; legacy identity review
- [`molsysmt_xdist_progress_skips_initial_deciles.md`](molsysmt_xdist_progress_skips_initial_deciles.md) — PR-PILOT-009 — resolved 2026-07-21; legacy identity review
- [`native_extension_stdout_leaks_after_final_report.md`](native_extension_stdout_leaks_after_final_report.md) — PR-PILOT-010 — resolved 2026-07-21; legacy identity review
- [`setup_errors_counted_as_failed.md`](setup_errors_counted_as_failed.md) — PR-PILOT-001 — resolved 2026-07-18; legacy identity review
- [`warning_group_truncation_is_not_diagnostically_sufficient.md`](warning_group_truncation_is_not_diagnostically_sufficient.md) — PR-PILOT-003 — resolved 2026-07-18; legacy identity review
- [`xdist_mixed_valid_and_missing_paths_hide_the_usage_error.md`](xdist_mixed_valid_and_missing_paths_hide_the_usage_error.md) — PR-PILOT-015 — resolved 2026-08-12; legacy identity review
- [`xdist_progress_is_not_bounded_by_deciles.md`](xdist_progress_is_not_bounded_by_deciles.md) — PR-PILOT-004 — resolved 2026-07-18; legacy identity review
- [`xdist_startup_noise_leaks_into_compact_stdout.md`](xdist_startup_noise_leaks_into_compact_stdout.md) — PR-PILOT-005 — resolved 2026-07-18; legacy identity review

<!-- /generated -->
