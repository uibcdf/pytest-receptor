# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-08-12

### Added

- A normalized evidence model shared by terminal rendering and machine output.
- The opt-in `pytest-receptor.events@1` JSONL artifact and supported reader.
- Exact text-contract tests and differential pytest/JUnit parity tests.
- Tested coexistence with xdist, coverage, reruns, subtests, and JUnit.
- Auditable artifact size limits and reproducible wall-time/peak-RSS benchmarks.
- Stable root-cause fingerprints and recoverable, auditable terminal truncation.

### Fixed

- Mixed valid and nonexistent paths under xdist now retain an actionable invalid
  selection diagnostic while preserving pytest's exit status.

### Changed

- CI, documentation, packaging metadata, and release gates now exercise the
  declared Python and pytest support matrix.
- Rerun attempts and subtests retain distinct normalized identities without
  inflating logical-test counts.

## [0.7.0] - 2026-08-02

### Changed

- Consolidated the post-0.6 development guide and proposal triage.

## [0.6.0] - 2026-07-28

### Changed

- Rebuilt compact reporting around pytest's public hooks and truth-preserving
  exit semantics.
- Added owner-only full reports, credential-pattern redaction, deterministic
  failure grouping, warning visibility, progress, and real-suite regressions.

## [0.5.0] - 2026-07-17

### Added

- Experimental integration and event-reader work, subsequently redesigned by
  the 0.6 correctness audit.

## [0.4.0] - 2026-07-17

### Added

- Experimental CI watchdog behavior, subsequently removed in 0.6.

## [0.3.0] - 2026-07-17

### Added

- Initial event-model and semantic-budget experiments.

## [0.2.0] - 2026-07-17

### Added

- Initial correctness and outcome handling.

## [0.1.2] - 2026-07-17

### Added

- Conda build recipe.

## [0.1.1] - 2026-07-17

### Changed

- English documentation and explicit Python support metadata.

## [0.1.0] - 2026-07-17

### Added

- Human, LLM, and CI output profiles.

[Unreleased]: https://github.com/uibcdf/pytest-receptor/compare/1.0.0...HEAD
[1.0.0]: https://github.com/uibcdf/pytest-receptor/compare/0.7.0...1.0.0
[0.7.0]: https://github.com/uibcdf/pytest-receptor/compare/0.6.0...0.7.0
[0.6.0]: https://github.com/uibcdf/pytest-receptor/compare/0.5.0...0.6.0
[0.5.0]: https://github.com/uibcdf/pytest-receptor/compare/0.4.0...0.5.0
[0.4.0]: https://github.com/uibcdf/pytest-receptor/compare/0.3.0...0.4.0
[0.3.0]: https://github.com/uibcdf/pytest-receptor/compare/0.2.0...0.3.0
[0.2.0]: https://github.com/uibcdf/pytest-receptor/compare/0.1.2...0.2.0
[0.1.2]: https://github.com/uibcdf/pytest-receptor/compare/0.1.1...0.1.2
[0.1.1]: https://github.com/uibcdf/pytest-receptor/compare/0.1.0...0.1.1
[0.1.0]: https://github.com/uibcdf/pytest-receptor/releases/tag/0.1.0
