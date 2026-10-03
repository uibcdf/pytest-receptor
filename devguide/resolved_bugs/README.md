# Resolved Bugs

Closed field reports, kept with their resolution or dated disposition attached.

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

Every report below has an owning GitHub issue. The seventeen pre-protocol
records were reconciled under `uibcdf/pytest-receptor#10`, preserving their
original bodies and appending dated reviews. Resolved, withdrawn and
superseded outcomes remain separately indexed; no historical claim is
silently rewritten.

<!-- generated: devguide_index -->

### Resolved (15)

- [`deselected_tests_reported_incomplete.md`](deselected_tests_reported_incomplete.md) — [#25](https://github.com/uibcdf/pytest-receptor/issues/25) — Distinguish deselection from incomplete execution. *(resolved, inspected)*
- [`discard_stream_remains_unclosed_after_pytest.md`](discard_stream_remains_unclosed_after_pytest.md) — [#4](https://github.com/uibcdf/pytest-receptor/issues/4) — Close the late-terminal discard stream without leaking ResourceWarning *(resolved, reproduced)*
- [`documented_full_report_path_misses_pytest_cache_d.md`](documented_full_report_path_misses_pytest_cache_d.md) — [#19](https://github.com/uibcdf/pytest-receptor/issues/19) — Make documented full-report paths locate the written artifact. *(resolved, inspected)*
- [`external_single_test_rerun_loses_path_with_fixed_rootdir.md`](external_single_test_rerun_loses_path_with_fixed_rootdir.md) — [#24](https://github.com/uibcdf/pytest-receptor/issues/24) — Recover pathless external node IDs under a fixed rootdir. *(resolved, inspected)*
- [`external_test_paths_produce_invalid_rerun_and_location.md`](external_test_paths_produce_invalid_rerun_and_location.md) — [#15](https://github.com/uibcdf/pytest-receptor/issues/15) — Resolve external test paths from the invocation directory. *(resolved, inspected)*
- [`molsysmt_incomplete_stats_closes_terminal_stream.md`](molsysmt_incomplete_stats_closes_terminal_stream.md) — [#23](https://github.com/uibcdf/pytest-receptor/issues/23) — Preserve controlled-exit status with receptor statistics. *(resolved, inspected)*
- [`molsysmt_xdist_incomplete_run_reported_pass.md`](molsysmt_xdist_incomplete_run_reported_pass.md) — [#20](https://github.com/uibcdf/pytest-receptor/issues/20) — Prevent incomplete or stale sessions from appearing complete. *(resolved, inspected)*
- [`native_extension_stdout_leaks_after_final_report.md`](native_extension_stdout_leaks_after_final_report.md) — [#22](https://github.com/uibcdf/pytest-receptor/issues/22) — Flush native C stdout while pytest capture is active. *(resolved, inspected)*
- [`progress_snapshot_percent_matches_completed_count.md`](progress_snapshot_percent_matches_completed_count.md) — [#30](https://github.com/uibcdf/pytest-receptor/issues/30) — Make progress snapshots agree with completed-test counts. *(resolved, inspected)*
- [`recurring_full_ci_and_contributor_routes.md`](recurring_full_ci_and_contributor_routes.md) — [#11](https://github.com/uibcdf/pytest-receptor/issues/11) — Verify recurring full CI, skipped-push recovery and protected contributor routes. *(resolved, measured)*
- [`setup_errors_counted_as_failed.md`](setup_errors_counted_as_failed.md) — [#14](https://github.com/uibcdf/pytest-receptor/issues/14) — Preserve setup and teardown error categories. *(resolved, inspected)*
- [`warning_group_truncation_is_not_diagnostically_sufficient.md`](warning_group_truncation_is_not_diagnostically_sufficient.md) — [#16](https://github.com/uibcdf/pytest-receptor/issues/16) — List every distinct warning group. *(resolved, inspected)*
- [`xdist_mixed_valid_and_missing_paths_hide_the_usage_error.md`](xdist_mixed_valid_and_missing_paths_hide_the_usage_error.md) — [#27](https://github.com/uibcdf/pytest-receptor/issues/27) — Diagnose mixed valid and missing xdist selections. *(resolved, inspected)*
- [`xdist_progress_is_not_bounded_by_deciles.md`](xdist_progress_is_not_bounded_by_deciles.md) — [#17](https://github.com/uibcdf/pytest-receptor/issues/17) — Keep xdist progress bounded and controller-owned. *(resolved, inspected)*
- [`xdist_startup_noise_leaks_into_compact_stdout.md`](xdist_startup_noise_leaks_into_compact_stdout.md) — [#18](https://github.com/uibcdf/pytest-receptor/issues/18) — Suppress xdist startup chatter without losing crash reporting. *(resolved, inspected)*

### Withdrawn (1)

- [`full_suite_empty_success_output_molsysviewer.md`](full_suite_empty_success_output_molsysviewer.md) — [#26](https://github.com/uibcdf/pytest-receptor/issues/26) — Review the historical missing MolSysViewer final summary. *(withdrawn, inspected)*

### Superseded (1)

- [`molsysmt_xdist_progress_skips_initial_deciles.md`](molsysmt_xdist_progress_skips_initial_deciles.md) — [#21](https://github.com/uibcdf/pytest-receptor/issues/21) — Retire misleading warm-up progress backfill. *(superseded, inspected)*

<!-- /generated -->
