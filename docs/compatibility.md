# Compatibility and migration to 1.0

Version 1.0 freezes the reliability and evidence contracts without freezing
every character of presentation forever.

## Supported runtime

The 1.x series supports exactly Python 3.11, 3.12, and 3.13, with pytest 8 or
9. The wheel metadata enforces `Python >=3.11,<3.14`; CI exercises all six
Python/pytest combinations both serially and with xdist.

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
