# pytest-receptor Technical Work Queue & Verification Checklist

This document tracks all the engineering requirements, correctness findings, architectural updates, and ecosystem integrations identified during the **July 2026 Critical Technical Audits** (`devguide`). 

As of the **v0.5.0 release**, all tasks have been successfully implemented, verified through automated integration testing, and merged.

---

## 1. Phase 0: Correctness & Truth Floor

- [x] **PR-CRIT-001: Correct outcome classification for empty test suites (NO_TESTS)**
  - *Requirement:* Pytest exit code 5 must render as `NO_TESTS` with exit status 5, rather than reporting `OK: 0 passed`.
  - *Verification:* Tested in `test_receptor_exit_codes` verifying `NO_TESTS exit=5`.
- [x] **PR-CRIT-002: Correct outcome classification for interrupted suites (INTERRUPTED)**
  - *Requirement:* Interrupted executions (e.g. KeyboardInterrupt, exit code 2) must render as `INTERRUPTED` and mark the session as incomplete.
  - *Verification:* Verified in exit status tests.
- [x] **PR-FID-002: Well-formed visual XML reporter output**
  - *Requirement:* All strings (exception messages, logs, node IDs) containing XML metacharacters (`<`, `>`, `&`, quotes) must be escaped to ensure valid, parseable structures.
  - *Verification:* Handled in `_xml_escape` and tested across multiple test cases.
- [x] **PR-FID-003: Warnings preservation on green runs**
  - *Requirement:* Keep warnings visible in successful runs by displaying warning count, category, message, and origin to avoid silencing depreciation warnings.
  - *Verification:* Tested in `test_receptor_warnings_and_xpassed_in_green_runs`.
- [x] **PR-FID-004: Fingerprint calculated before destructive truncation**
  - *Requirement:* Avoid fingerprint collisions by grouping/fingerprinting complete normalized error messages first, applying truncation only at the presentation layer.
  - *Verification:* Verified in grouping tests.
- [x] **PR-FID-007: Accurate traceback function/location labeling**
  - *Requirement:* Avoid misleading function labels (like `in ValueError`). Format location and exception type cleanly using explicit delimiters (`->`).
  - *Verification:* Verified in traceback outputs.
- [x] **PR-OPS-001: Correct Python version range metadata**
  - *Requirement:* Fix PEP 440 constraints in `pyproject.toml` to `>=3.11,<3.14` to allow Python 3.13 patch releases (e.g. 3.13.1).
  - *Verification:* Checked setup.
- [x] **PR-OPS-003: Bounded memory on suppressed human output**
  - *Requirement:* Disable standard human output accumulation in memory unless `--receptor-stats` or `--receptor-dump-dir` is explicitly requested.
  - *Verification:* Handled in `DummyTerminalWriter`.
- [x] **PR-OPS-006: Monotonic clock for elapsed durations**
  - *Requirement:* Replaced all instances of `time.time()` with `time.monotonic()` for test timing, CI heartbeat progress, and watchdog timing.
  - *Verification:* Verified duration outputs.
- [x] **PR-OPS-007: Clarified human dump capture boundary in documentation**
  - *Requirement:* Update user guides to clarify that the human dump captures only standard TerminalReporter output, not other arbitrary plugin/process bypasses.
  - *Verification:* Documented in Usage Guide and README.
- [x] **PR-UX-001: Conservative environment-neutral installation hints**
  - *Requirement:* Avoid recommending dependency installation commands that assume pip or specific environment structures. Rely on local diagnostic info and precise rerun command guidelines.
  - *Verification:* Handled in `_get_correction_hint`.
- [x] **PR-DOC-001: Align documentation with tested behavior**
  - *Requirement:* Ensure all documentation claims (XML parseability, watchdog periodicity, dump behaviors) align 100% with real code and unit-tested expectations.
  - *Verification:* Reviewed and updated README and sphinx docs with 0 warnings.

---

## 2. Phase 1: Lossless Event Model & Streaming Persistence

- [x] **Lossless Event Schema (`events@1`)**
  - *Requirement:* Implement independent dataclasses for `SessionStartEvent`, `SessionFinishEvent`, `TestPhaseEvent`, `WarningEvent`, `ExtensionEvent`, and `ExceptionInfo`.
  - *Verification:* Implemented in `src/pytest_receptor/events.py`.
- [x] **Streaming JSONL Artifact Writer**
  - *Requirement:* Stream events incrementally to a local `.jsonl` file (`--receptor-artifact`) to prevent memory leaks and protect evidence in case of abrupt termination.
  - *Verification:* Handled in `EventCollector`.
- [x] **EventReader API**
  - *Requirement:* Design and export a public Python class to programmatically read, query, and filter JSONL evidence.
  - *Verification:* Implemented in `src/pytest_receptor/reader.py` and tested.
- [x] **PR-OPS-005: Definition of authoritative output-channel boundaries**
  - *Requirement:* Formulate a robust contract where the local JSONL is the authoritative machine channel, stdout/stderr is the presentation channel (tolerating external noise), and safe degradation is guaranteed if artifact storage is unwritable.
  - *Verification:* Implemented safe fallback on file open/write errors in `EventCollector`.

---

## 3. Phase 2: Reversible Grouping, Semantic Budgets, and Security Hardening

- [x] **PR-FID-001: Preserve per-occurrence context in deduplication groups**
  - *Requirement:* Group homogeneous cascades by exception type/normalized message, but preserve node ID, phase, and unique captured stdout/stderr/logs for every individual test under `<test>` tag.
  - *Verification:* Verified in `test_receptor_llm_grouped_failures_preserve_distinct_logs`.
- [x] **PR-FID-005: Skip, xfail, and xpass traceability**
  - *Requirement:* Group skips and xfails by reason, list unexpected passes (xpasses) with their node IDs, and preserve these details in successful summaries.
  - *Verification:* Verified in `test_receptor_warnings_and_xpassed_in_green_runs`.
- [x] **PR-FID-006: Intelligent Traceback Pruning**
  - *Requirement:* Retain initiating local frame, local-to-external library boundary, and the terminal crash frame, while omitting unsemantic frames.
  - *Verification:* Verified in traceback formatting.
- [x] **PR-SEC-001: Redaction of Credentials and Secrets**
  - *Requirement:* Scan and redact passwords, credentials, api keys, and tokens from exceptions and logs before rendering or writing.
  - *Verification:* Verified in security tests.
- [x] **PR-SEC-002: Restrictive Artifact Permissions**
  - *Requirement:* Create local JSONL files with restrictive owner-only read/write permissions (`0o600`).
  - *Verification:* Verified in unit tests checking stat modes.
- [x] **PR-SEC-002: Symlink Attack Prevention**
  - *Requirement:* Detect and safely unlink (`os.unlink`) any pre-existing symlinks in the target path before writing the artifact.
  - *Verification:* Verified in symlink test cases.
- [x] **Configurable Project-Specific Normalizers**
  - *Requirement:* Support custom regex rules from `pytest.ini`/`pyproject.toml` (option `receptor_normalizers`) to normalize messages during grouping.
  - *Verification:* Tested in `test_receptor_custom_normalizers`.

---

## 4. Phase 3 & 4: Ecosystem Integration, CI Robustness & Token Benchmarks

- [x] **PR-OPS-002: CI Monotonic Watchdog Thread**
  - *Requirement:* Implement a background daemon thread in `CiTerminalReporter` that checks the active test every 10 seconds and warns on console if it hangs or exceeds 30 seconds.
  - *Verification:* Verified in watchdog cleanup.
- [x] **CI Error Annotations**
  - *Requirement:* Provide CI annotation-friendly file and line logs (e.g. `::error file=...::`) for all failing tests in CI mode.
  - *Verification:* Tested in `test_receptor_ci_reporter_features`.
- [x] **CI Session completeness**
  - *Requirement:* Display `complete=true/false` and the `stop_reason` (e.g. maxfail) at the end of the CI summary line.
  - *Verification:* Tested in CI summary assertions.
- [x] **Public Extension Hook Spec (`pytest_receptor_extension_event`)**
  - *Requirement:* Provide an extension hook so third-party ecosystem tools (e.g. `SMonitor`) can record namespaced diagnostic events into the stream.
  - *Verification:* Implemented in `src/pytest_receptor/hooks.py` and verified in integration tests.
- [x] **Active Correlation API (`get_current_correlation`)**
  - *Requirement:* Expose in-process correlation data (run_id, nodeid, phase, worker, attempt) for external consumers.
  - *Verification:* Verified in integration tests.
- [x] **Artifact Integrity Verification**
  - *Requirement:* Include `event_count` and `integrity_hash` (accumulated SHA256 of the JSONL contents) in the finalized `SessionFinishEvent`.
  - *Verification:* Tested in `test_receptor_extension_and_reader`.
- [x] **Tokenizer Benchmark Suite**
  - *Requirement:* Build a tokenizer benchmark script evaluating outputs across multiple tokenizer families (`cl100k_base`, `o200k_base`, `p50k_base`, `r50k_base`) and document the results.
  - *Verification:* Implemented in `devtools/benchmark_tokenizers.py` and published in `docs/benchmarks.md`.
- [x] **PR-OPS-004: Direct dependencies on pytest internals isolated**
  - *Requirement:* Bounded and isolated standard terminal reporter extensions behind simple hook-based configuration wrappers.
  - *Verification:* Implemented in `plugin.py`.
- [x] **PR-REL-001: Compatibility testing CI workflow**
  - *Requirement:* Establish automated test coverage matrix testing Python 3.11-3.13, pytest 8/9, serial, and xdist workers.
  - *Verification:* Configured and verified test run matrix.
