# Readiness for pytest-receptor 1.0

**Recorded:** 2026-08-12

**Status:** live dashboard derived from the accepted trust and architecture
documents. It does not replace their scope or lower their acceptance criteria.

**Pause/resume:** architecture and local release preparation are consolidated
in commit `4535431`. The ordered operational path through CI, tag, PyPI,
`uibcdf` conda, and pytest's automated plugin report is now
`roadmap_to_1.0_publication.md`.

Version 1.0 means the Level 2 evidence-preserving architecture, not merely a
stable rendering of the current plain-text report. This dashboard separates
work that is already executable from evidence that requires sustained use.

## Current position

| Gate | Status | Evidence or remaining work |
| :--- | :--- | :--- |
| Reliability floor | Complete | Exit truth, incomplete runs, degradation, redaction, permissions, serial/xdist behavior and field regressions are executable tests. |
| Public text contract | Frozen for 1.x | Exact golden reports cover green, failure, and mixed-state output; `docs/compatibility.md` defines which meanings are stable and permits only compatible additive presentation improvements. |
| Differential parity | Curated harness complete | Green, call/setup/teardown/collection failure, skip, xfail, xpass, empty, maxfail, interruption, rerun, and subtest runs compare receptor with plain pytest/JUnit in serial and xdist where applicable. Generated mixed-state expansion remains. |
| Channel authority | Complete for current architecture | `docs/channels.md` defines exit status, stdout, stderr, the full text report, JUnit coexistence, and failure boundaries. |
| Normalized event model | Complete for known pytest reports | The renderer and JSONL writer consume normalized phase, exception, captured-section, warning, logical-outcome, subtest identity, attempt, and final-session evidence. Runtime exception identity comes from structured `CallInfo.excinfo` and survives xdist serialization; collection failures retain an explicit `formatted` fallback. |
| Versioned canonical artifact | Frozen as `events@1` | Opt-in JSONL streams serial/xdist evidence, ends in a final session record, covers earlier records with SHA-256 integrity metadata, and enforces an auditable 50 MiB default ceiling. Missing/truncated tails are recognizably incomplete; incompatible evolution requires `events@2`. |
| Supported artifact reader | Frozen for 1.x | `pytest_receptor.read_artifact` negotiates the schema major, validates finalized streams, distinguishes incomplete tails, and preserves unknown event types. Clean-wheel consumer validation is part of the release workflow. |
| Reversible grouping and semantic budgets | Substantially complete | Every occurrence remains addressable; normalized cause groups have stable SHA-256 fingerprints. Compact truncation states original/retained characters and a content hash, while the complete disk report and optional structured event remain recoverable. Configurable per-section budgets remain. |
| Security and retention policy | Complete with documented boundary | Owner-only creation, symlink refusal, conservative redaction, and an auditable hard size policy are implemented. Retention is explicitly deployment-owned; arbitrary sensitive test data cannot be guaranteed absent. |
| Performance bounds | Locally measurable | The reproducible child-process harness measures wall time and peak RSS for green and homogeneous-failure suites, with and without JSONL. At 2,000 tests the largest local increment was 5.0 MiB RSS and 24.9% wall time. Repeat at MolSysMT scale before the clean release. |
| Dogfooding evidence | Accepted for 1.0 | MolSysMT exposed and drove fixes for real scientific-suite failures; this repository's structurally different suite and differential corpus exercise the same plugin serially and under xdist. Adoption monitoring continues after publication. |
| PyPI publication | Locally ready | Name, `Framework :: Pytest`, `pytest11`, project URLs, changelog, tag/distribution verifier, clean-wheel discovery, and OIDC release workflow are present. A maintainer must register the pending PyPI publisher and protected `pypi` GitHub environment before the first release. |

## Proposed release sequence

### 0.8 — evidence model

1. ~~Implement the smallest normalized session/report model that reproduces the
   current renderer without changing its output.~~ Implemented locally with
   golden serial/xdist regressions; the model remains internal until its
   artifact representation is validated.
2. ~~Stream a versioned JSONL artifact with a mandatory final session record.~~
   Implemented opt-in with restrictive permissions, symlink refusal, redaction,
   and integrity metadata.
3. ~~Add a reader that rejects unsupported major schema versions and preserves
   unknown events.~~ Implemented; external consumer validation remains.
4. Make terminal counts a projection of the same model consumed by the reader.

### 0.9 — reversibility and validation

1. ~~Add stable group hashes and semantic truncation metadata with recoverable
   complete evidence.~~ Configurable per-section budgets remain optional.
2. ~~Expand differential parity to teardown failures, reruns, subtests,
   interruption, maxfail, and collection failures.~~ Add generated mixed states.
3. ~~Add a reproducible memory/runtime harness and establish local scale
   evidence.~~ Continue MolSysMT measurement after release.
4. ~~Complete the artifact security, size, integrity, and failure suite.~~
5. ~~Exercise a scientific suite and a structurally different local suite.~~

### 1.0 — freeze

1. Resolve every unexplained parity divergence.
2. Freeze the text and artifact schemas with an explicit compatibility policy.
3. Publish migration notes from 0.x and the supported reader API.
4. Re-run the full Python/pytest/plugin matrix, packaging check, docs build,
   benchmarks, and real-suite acceptance corpus from a clean release commit.
5. Follow `pypi_release.md`; publish through the protected Trusted Publisher,
   then verify automatic loading and the generated pytest plugin-list entry.

## Local release gate

The checks available from this repository are:

```bash
ruff check pytest_receptor tests devtools docs/conf.py
ruff format --check pytest_receptor tests devtools docs/conf.py
pytest -q
pytest -q -n 2
sphinx-build -W --keep-going -b html docs docs/_build/html
python -m build
```

CI repeats tests across Python 3.11–3.13 and pytest 8–9 with coverage, JUnit,
reruns, subtests, and xdist installed. Real-suite observation and the clean-tag
release rehearsal cannot be replaced by a local unit test.
