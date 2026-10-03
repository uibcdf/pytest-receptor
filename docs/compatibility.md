# Compatibility and migration to 1.0

Version 1.0 freezes the reliability and evidence contracts without freezing
every character of presentation forever.

## Supported runtime

The 1.x series supports exactly Python 3.11, 3.12, 3.13, and 3.14, with pytest 8
or 9. The wheel metadata enforces `Python >=3.11,<3.15`; Linux CI exercises
all eight Python/pytest combinations both serially and with xdist.

The recurring full matrix also exercises macOS arm64 with Python 3.13 and
both pytest majors, serially and with xdist. Intel macOS is outside the
supported platform boundary. These jobs install the checkout in editable
mode; they do not qualify every Python version on macOS or a particular
published wheel or Conda artifact. Windows runtime behavior is not covered
by the current hosted matrix. Package portability and installed-release
qualification remain separate from source-test evidence.

## CI and contributor routes

`tests.yml` runs on pushes to `main`, pull requests and manual dispatch.
External contributions use a pull request and the eleven required Tests
checks: lint, benchmarks, packaging and all eight Linux compatibility cells.
The branch requires up-to-date checks; administrators `dprada` and `LMMV`
retain their direct-push route without introducing mandatory review approvals.

`full-tests.yml` runs the Linux matrix and macOS representatives weekly on
Tuesday at 09:11 UTC, and supports manual full runs. A daily trigger at 01:07
in `America/Mexico_City` runs the matrix only when skipped direct pushes
remain after the latest executed green full Linux matrix. A later successful
full Tests push can clear that debt. Diagnostic probes, skipped suite steps,
failed runs, PRs and other branches cannot clear it; uncertain history runs
the matrix. Scheduled delivery can be delayed, so the cron expression is not
an exact execution-time guarantee.

The offline recovery guard is `tests/test_ci_backlog.py`. Hosted evidence and
the contributor-route review are recorded in `uibcdf/pytest-receptor#11`.

## Stable 1.x contracts

Within 1.x:

- installing the plugin remains a true passthrough until `--receptor=llm` or
  `--receptor=ci` is selected;
- pytest's numeric exit status remains authoritative and is never changed;
- leading verdict labels and documented result meanings remain compatible;
- existing command-line options and configuration keys are not removed or
  reinterpreted incompatibly;
- `pytest-receptor.events@1` remains readable by the supported
  `read_artifact()` API;
- artifact consumers may receive additive fields or event types and must ignore
  unknown fields while preserving unknown records;
- an incompatible artifact change requires `events@2`; an incompatible public
  behavior change requires a new major package version.

Exact golden reports protect against accidental formatting drift. A minor 1.x
release may make an additive presentation improvement, such as exposing new
pytest evidence, provided the meanings above and token-economy goal are kept.
Consumers should key on verdicts and documented fields, not offsets or ANSI
layout.

## Migrating from 0.7

No invocation change is required:

```bash
pytest --receptor=llm
pytest --receptor=ci
```

The important additions are opt-in or corrective:

- `--receptor-events=PATH` writes the versioned JSONL evidence stream;
- `--receptor-events-max-bytes=BYTES` sets its audited hard ceiling;
- `pytest_receptor.read_artifact()` is the supported machine-consumer API;
- reruns and subtests now retain attempt/subtest identity without inflating the
  logical test count;
- compact truncation is auditable, while the full disk report retains complete
  messages and captured sections;
- normalized root-cause groups carry stable SHA-256 fingerprints in the final
  artifact record.

The `human` default remains unchanged pytest. Existing
`receptor_normalizers` and `receptor_rerun_command` settings continue to work.
