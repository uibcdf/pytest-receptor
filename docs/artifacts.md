# Versioned evidence artifacts

The structured artifact is an opt-in JSONL stream produced from the same
normalized evidence as the text renderer:

```bash
pytest --receptor=llm --receptor-events=.pytest-receptor/events.jsonl
```

The destination directory must already exist. The option requires the `llm` or
`ci` profile because `human` is a true passthrough and installs no collector.
No upload, network access, or automatic retention is performed.

The stream is bounded to 50 MiB by default. Set a different explicit ceiling
(minimum 64 KiB) when required:

```bash
pytest --receptor=ci --receptor-events=events.jsonl \
  --receptor-events-max-bytes=104857600
```

When the next event would consume the space reserved for finalization, the
writer emits `evidence_limit`, stops storing further event bodies, and still
writes `session_finish`. Its `artifact_policy` records the byte ceiling,
whether truncation occurred, and the exact number of dropped records. Thus a
bounded artifact remains integrity-valid but never silently claims full
evidence retention.

## Completion and integrity

Every line is a UTF-8 JSON object with `schema` set to
`pytest-receptor.events@1` and a `type` discriminator. A normal stream contains:

1. one `session_start` record;
2. `phase` and `warning` records as pytest emits them;
3. one final `session_finish` record.

The final record carries pytest's exit status, normalized outcome, explicit
counts and completeness, plus a SHA-256 digest and count covering every earlier
record exactly as written. Each `root_cause` event gives a normalized cause a
stable `sha256:` fingerprint and lists its logical occurrences without growing
the finalization record.
A failed test run can still have a finalized artifact. Conversely, a file
without `session_finish` is an incomplete event stream even if its last
recorded test passed.

Evidence is streamed, so an interrupted process normally leaves useful partial
records. `SIGKILL`, host loss, storage failure, and buffered filesystem loss can
still prevent capture; the artifact does not claim otherwise.

## Reader API

```python
from pytest_receptor import read_artifact

artifact = read_artifact(".pytest-receptor/events.jsonl")
if not artifact.complete:
    print(f"partial stream: {artifact.issue}")
else:
    print(artifact.final.data["outcome"])
```

`artifact.complete` means that the stream has a validated final record. The
test run's execution completeness is the separate
`artifact.final.data["complete"]` field.

The reader:

- validates the SHA-256 digest of finalized streams;
- rejects unsupported schema major versions;
- preserves unknown record types as `ArtifactRecord(known=False)` so a newer
  producer's data is not silently discarded;
- classifies a missing or truncated final record as incomplete;
- raises `ArtifactFormatError` for malformed interior records and
  `ArtifactIntegrityError` for altered finalized evidence.

Minor evolution within `events@1` may add fields and record types. Consumers
must ignore unknown fields and retain unknown records when rewriting an
artifact. An incompatible change requires a new schema major.

## Extension producer API

The receptor owns namespaced extension records in the same JSONL stream as
pytest evidence. A producer can opt in without importing another diagnostic
library:

```python
from pytest_receptor.extensions import current_context, emit

def test_timed_operation(pytestconfig):
    context = current_context()  # active node, phase, worker, and attempt
    reference = emit(
        pytestconfig,
        "org.example.timer@1",
        {"operation": "example", "elapsed_ms": 3.2},
    )
```

`emit` returns an opaque producer reference when accepted, or `None` when the
receptor is inactive or the event is rejected. It never changes the pytest
outcome. A namespace must include a major version. The optional
`relationships` argument accepts a list or tuple of producer references; it
does not deduplicate events or reinterpret pytest outcomes. `current_context`
returns an immutable phase snapshot inside setup, call, or teardown and `None`
outside those phases. Background threads and subprocesses need explicit
context propagation; the service never assigns the last test's node ID to a
session event.
If a producer catches its own recording failure, it can call
`mark_incomplete(config)` so the final artifact declares the evidence gap
without changing pytest's result.

The service is active only with `--receptor=llm` or `--receptor=ci` **and**
`--receptor-events=PATH`. The human profile installs no collector. Events are
bounded to 16 KiB each, 128 per phase or session, and 10,000 per process.
Payloads must be JSON-compatible objects with string keys, at most six nested
levels, 128 entries per container, and strings no longer than 2,048
characters. Invalid or excess events are counted as dropped, with
`session_finish.extensions.incomplete=true`; they do not fail the test.

The receptor strips control characters and applies its conservative secret
pattern redaction **before** worker transport and artifact persistence. Each
`extension` record declares `trust=producer_untrusted` and
`redaction=pattern`. Producers must exclude sensitive values that do not match
those patterns. The record carries `nodeid`, `phase`, `worker_id`, `attempt`,
`producer_ref`, `relationships`, and an `emitted_during` reference to the
receptor's phase record where applicable. Xdist workers transport phase events
through the corresponding pytest report; worker session events arrive through
worker shutdown metadata. The controller assigns final event IDs and writes
the sole canonical artifact. If a worker is lost, extension evidence is marked
incomplete while already received records remain in the artifact.

Terminal message and captured-section budgets do not mutate the normalized
events. A compact omission marker states original and retained character counts
plus a SHA-256 prefix; `.pytest_cache/d/receptor/last-run.txt` retains the full
text projection, and JSONL retains the structured source event when enabled.

## Security boundary

The file is created owner-only (`0600`) and symlinks are refused. Text fields
pass through the receptor's control-character stripping and conservative
credential-pattern redaction before persistence. This catches common
`token=...`, password, secret, credential, Basic-auth, and bearer-token shapes;
it is not a guarantee that arbitrary sensitive test data cannot appear.

Choose the destination and retention period accordingly. The producer applies
the configured hard size limit but deliberately does not delete artifacts;
retention remains the responsibility of the local or CI system that owns the
destination. Configurable project-specific redaction rules and external blobs
may be added compatibly in a future 1.x release.
