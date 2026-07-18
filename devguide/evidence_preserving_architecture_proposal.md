# Evidence-Preserving Receptor Architecture

**Status:** post-0.6 reference. Proposed after the 2026-07-17 critical audit;
partially superseded on 2026-07-18 by `scope_0.6.md`.

**Operational work queue:** `audit_action_register_2026-07-17.md`

> **Read this first.** The goal of this document is intact: the receptor should
> eventually collect evidence once and render it for several consumers without
> changing the meaning of the run. What changed is sequencing and scope.
>
> `scope_0.6.md` is the authority for the next release. The following parts of
> this document no longer apply as written, and the reasons are recorded in
> `superseded_proposals.md`:
>
> - **The recommended implementation order.** Phase 0 here is roughly the 0.6
>   correctness floor, but 0.6 also deletes features this document assumed would
>   be repaired: XML output, installation hints, the heartbeat, and the separate
>   CI reporter.
> - **Building a bespoke `events@1` JSONL schema first.** `pytest-reportlog`
>   already streams per-report JSONL, including under xdist. It must be evaluated
>   before any bespoke schema is designed.
> - **"Lossless".** Narrowed to evidence-preserving during normal pytest
>   lifecycle operation.
> - **The XML presentation option.** Rejected; 0.6 uses compact plain text.
>
> Everything else — the event model, reversible grouping, semantic budgets,
> redaction, the artifact reader, and the compatibility strategy — remains the
> reference for work after 0.6.

## Objective

Turn `pytest-receptor` from a compact replacement terminal reporter into a
reliable diagnostic layer that collects pytest evidence once and renders it for
humans, LLM agents, CI systems, and machine consumers without silently changing
the meaning of the run.

The central invariant is:

> Rendering may omit repeated presentation, but it must not make an unsuccessful
> or incomplete run look successful, and every omitted diagnostic must remain
> addressable in a lossless artifact.

Here, "lossless" is bounded to events observed during normal pytest lifecycle
operation. `SIGKILL`, process crashes, host loss, and storage failure can prevent
complete capture. The implementation must stream best-effort evidence and mark
artifacts as incomplete rather than promise impossible durability.

## Proposed architecture

```text
pytest lifecycle hooks
        |
        v
lossless normalized event collector
        |
        +--> compact LLM renderer
        +--> flat CI renderer
        +--> human/default integration
        +--> versioned JSONL artifact
        +--> future agent-tool protocol
```

Collection, normalization, grouping, budgeting, and rendering should be
separate modules with independently tested contracts.

## Layer 1: normalized diagnostic events

Define a versioned internal schema, for example
`pytest-receptor.events@1`. It should represent events rather than terminal
strings.

### Session record

Capture:

- schema version and receptor version;
- run identifier;
- pytest exit status and normalized outcome;
- Python and pytest versions;
- relevant plugin names and versions;
- command arguments;
- root directory and configuration source;
- start/end monotonic duration;
- execution mode and xdist worker count;
- collected, executed, deselected, passed, failed, errored, skipped, xfailed,
  xpassed, rerun, and warning counts.
- explicit completeness, stop reason, and not-executed count;
- fail-fast, max-failure, selection, and sharding context where applicable.

The normalized session outcome must be derived from `pytest.ExitCode`, not from
the absence of failure reports.

### Test and phase events

Each setup, call, and teardown occurrence should retain:

- stable event identifier;
- node ID;
- phase;
- outcome;
- timestamp or monotonic sequence number;
- duration;
- worker identifier;
- rerun attempt where available;
- fixture context where available;
- exception reference;
- captured stdout, stderr, and log references;
- skip, xfail, or xpass reason.

Setup and teardown failures must not be collapsed into ordinary call failures.
The schema must separate the collected item, logical final outcome, individual
attempt, phase report, and subtest identity. Renderer totals must be derived
from the normalized model rather than copied from ambiguous reporter buckets.

### Exception evidence

Capture structured data where pytest exposes it:

- fully qualified exception type;
- message;
- assertion explanation/diff;
- cause and context chain;
- exception groups and nested members;
- crash location;
- traceback frames with path, line, and function where available;
- local/external classification as metadata, not destructive filtering;
- source snippet when pytest provides it;
- content hashes for large sections.

Do not infer the exception type by parsing formatted text when a structured
representation is available. Where pytest only supplies serialized report
data, make the limitation explicit in the event.

### Warning events

Capture:

- warning category;
- message;
- path and line;
- node ID or session scope;
- phase if attributable;
- occurrence count;
- normalized fingerprint.

Warnings must remain visible on successful runs, although repeated occurrences
may be grouped.

### Captured sections

Keep stdout, stderr, logs, and plugin-defined sections per occurrence. Unknown
section types should be preserved with their original names rather than
dropped.

## Layer 2: lossless artifact

Write a versioned JSONL artifact when requested, and consider enabling a
temporary artifact automatically on unsuccessful runs. JSONL is suitable
because events can be streamed and inspected without loading one large object.

Required properties:

- valid serialization for arbitrary Unicode and metacharacters;
- atomic finalization or a recognizable incomplete marker;
- stable event and fingerprint identifiers;
- bounded individual records with external blobs for very large captures;
- explicit schema version;
- deterministic ordering in non-distributed runs;
- sequence metadata for distributed runs;
- optional redaction hooks for secrets and credentials;
- configurable retention location;
- no implicit upload or network operation.
- restrictive default permissions and safe handling of symlinks;
- explicit retention and cleanup policy;
- bounded files and external blobs with graceful storage-failure records;
- integrity metadata for finalized artifacts;
- a clear distinction between complete and interrupted event streams.

The terminal report should reference this artifact by path and event ID when it
truncates or suppresses evidence.

### Streaming and memory bounds

Do not retain a complete suppressed human report by default. Human-output
capture should be enabled only for stats or audit dumps and should stream to a
bounded sink. The event collector should also avoid retaining duplicate large
captured sections when they are already persisted as blobs.

Define and test peak-memory behavior for:

- very large green suites;
- thousands of homogeneous setup failures;
- heterogeneous failures with large captured logs;
- xdist runs with simultaneous worker reports.

Performance reporting must include runtime and peak resident memory, not only
terminal token count.

## Layer 3: diagnostic grouping

Grouping must be reversible. A failure group should contain common evidence and
a list of complete occurrence summaries.

### Proposed fingerprint inputs

Use a reviewed combination of:

- normalized fully qualified exception type;
- phase;
- normalized message or assertion signature;
- origin frame or local/external boundary;
- relevant cause-chain signature.

Do not group solely by exception type and message. Equal messages from unrelated
call sites can have different causes.

Fingerprints must be calculated from complete normalized evidence before any
renderer truncation. Truncated presentation must never alter group identity.

### Normalization policy

Memory addresses and timestamps are reasonable first normalizers, but every
normalizer can create false equivalence. Therefore:

- normalization rules should be versioned;
- the raw value must remain in the artifact;
- the fingerprint should record the normalizer version;
- project-specific normalizers should be configurable;
- paths, ports, UUIDs, random seeds, and parameter IDs should not be erased by
  default without evidence that they are non-semantic.

### Occurrence preservation

Every grouped occurrence retains at least:

- node ID;
- phase;
- worker and attempt;
- location;
- captured-section fingerprints;
- traceback fingerprint;
- concise delta from the representative occurrence;
- link to its complete event.

## Layer 4: LLM renderer

The LLM renderer should be concise, deterministic, and explicitly lossy only at
the presentation layer.

### Green run

A genuinely clean run may remain one line:

```text
OK exit=0 collected=8241 passed=8239 skipped=2 duration=214.3s warnings=0
```

If warnings or unexpected outcomes exist, they must be visible:

```text
OK exit=0 passed=8238 skipped=2 xfailed=1 xpassed=1 duration=214.3s warnings=12/2groups
```

The renderer should list xpasses and warning groups by default because they are
actionable even when pytest exits successfully.

### Unsuccessful run

Lead with the outcome, not markup:

```text
FAILED exit=1 collected=8241 passed=8239 failed=2 groups=1 duration=214.3s
```

Then include, per group:

- stable fingerprint;
- exception and phase;
- representative location;
- concise root-cause message;
- minimal useful traceback;
- assertion diff or failure-specific evidence;
- occurrence list and meaningful deltas;
- exact rerun node IDs;
- reference to complete events.

Collection errors, interruption, internal error, no-tests, and usage errors need
distinct top-level labels.

### Budgeting

Replace the fixed 1500-character truncation with configurable budgets:

- overall output token or byte budget;
- per failure-group budget;
- traceback-frame budget;
- assertion-diff budget;
- captured-output budget;
- warning-group budget.

When a budget is exceeded, report original size, retained size, hash, and
artifact reference. Preserve structured boundaries rather than cutting an
arbitrary middle substring.

### Output syntax

Three reasonable options exist:

1. concise deterministic text for direct agent consumption;
2. properly escaped XML with a schema;
3. compact JSON for consumers that require parsing.

The canonical artifact should remain JSONL regardless of terminal syntax. If
XML remains the LLM presentation, all content and attributes must be escaped
and golden reports must be parsed during tests.

### Trust boundary

Treat exception text, captured streams, parameter IDs, paths, and plugin
sections as untrusted evidence. Escaping protects syntax but does not make the
content a trusted instruction for an agent.

The renderer should:

- place untrusted content only in explicit data fields;
- prevent test text from creating receptor control records;
- strip or encode unsafe terminal control characters;
- distinguish receptor-generated hints from test-generated text;
- attach confidence and provenance to every hint;
- support configurable secret redaction before persistence and display;
- never execute or implicitly authorize a suggested command.

## Layer 5: CI renderer

The CI receptor should share the collector and outcome model. It should not
reconstruct its own independent counts.

Requirements:

- never report success for a nonzero pytest exit status;
- include collection and interruption failures;
- provide CI annotation-friendly file and line data;
- preserve warnings according to configured policy;
- print exact final counts and duration;
- optionally publish the lossless artifact;
- avoid ANSI control sequences by default.
- define stdout/stderr ownership and tolerate unrelated plugin output;
- degrade clearly on broken pipes or unavailable artifact storage;
- expose session completeness and stop reason.

### Heartbeat decision

Choose explicitly between:

- a real periodic watchdog with deterministic startup and shutdown;
- lifecycle-boundary progress only, documented accurately;
- no heartbeat, delegating that concern to the CI runner.

A watchdog must be tested with a single long test, a hanging fixture, xdist,
interruption, and session shutdown. It must use `time.monotonic()`.

## Conservative hints and rerun guidance

Exact rerun commands are generally safer and more useful than speculative repair
commands. Prefer output such as:

```text
rerun: pytest path/test_module.py::test_case -q
```

For missing imports, report the fact and environment context. Do not assume the
distribution name or mutate dependency metadata. Optional project adapters may
provide dependency-manager-aware guidance when they can map import names to
declared distributions and dependency groups reliably.

Hints should have confidence and provenance fields. Low-confidence hints should
be phrased as checks, not commands.

## Public configuration proposal

Potential options, to be finalized only after the event model exists:

- `--receptor=human|llm|ci|jsonl`;
- `--receptor-artifact=PATH`;
- `--receptor-budget=SIZE`;
- `--receptor-warning-policy=summary|full|ignore-known`;
- `--receptor-max-groups=N`;
- `--receptor-max-occurrences=N`;
- `--receptor-heartbeat=SECONDS|off`;
- `--receptor-redact=PROFILE`;
- `--receptor-baseline=PATH` for warning/skip drift;
- `--receptor-stats` for output-cost diagnostics.

Do not freeze this CLI before the schema and main workflows are tested.

## Programmatic API

Provide a small supported API for consumers that should not parse terminal
text. Candidate concepts are:

- `SessionRecord`;
- `EventReader` for JSONL streams;
- `FailureGroup` and occurrence views;
- renderer protocol;
- redaction and normalization protocols;
- artifact validation and completeness checks.

The API should accept newer schema records conservatively and reject unsupported
incompatible versions with an actionable error. Private pytest compatibility
adapters must not leak into this public model.

## Packaging and release metadata

Express the Python support range as `>=3.11,<3.14`; `<=3.13` excludes Python
3.13 patch releases after 3.13.0. Add packaging tests that evaluate representative
patch versions.

Before a stable release, centralize the package version and complete standard
metadata such as license expression/file, maintainers or authors, project URLs,
classifiers, and pytest-plugin discoverability metadata as appropriate. These
are secondary to diagnostic correctness but important for trustworthy adoption.

## Compatibility strategy

Support should be evidence-based rather than expressed as an unbounded
`pytest>=8` claim.

Create CI coverage for:

- Python 3.11, 3.12, and 3.13 initially;
- the oldest supported pytest 8 release;
- the newest pytest 8 release;
- pytest 9;
- serial execution;
- xdist execution.

Add focused optional jobs for reruns and subtests. Pin upper pytest bounds only
if compatibility cannot otherwise be assured; preferably test upcoming pytest
releases before declaring incompatibility.

Minimize direct dependence on `_pytest` internals. Where a private API is
unavoidable, isolate it behind a small compatibility adapter and test that
adapter per pytest version.

## Validation strategy

### Correctness gates

Every pytest exit code must map to the correct receptor outcome. Golden
terminal reports must agree with the lossless artifact counts.

Test complete and incomplete sessions separately. A fail-fast run may be a
correct failure report while still being incomplete coverage of the collected
suite.

### Information-retention gates

Construct paired failures with equal messages but different:

- files and lines;
- call stacks;
- captured logs;
- phases;
- workers;
- causes.

After grouping, every difference must remain recoverable.

### Serialization gates

Exercise:

- XML metacharacters;
- quotes in node IDs and parameter values;
- arbitrary Unicode;
- null bytes or unsupported control characters;
- very large diffs;
- truncated output;
- incomplete sessions.

Parse every advertised XML/JSON output in the test itself.

### Security and resilience gates

Exercise:

- prompt-injection-shaped captured text;
- ANSI escape and terminal-control input;
- credential-shaped values and configured redaction;
- restrictive artifact permissions;
- symlinked and unwritable destinations;
- disk-full or bounded-writer failure;
- broken stdout/stderr pipes;
- incomplete JSONL tails after abnormal termination;
- unrelated plugin writes around machine-oriented output.

The expected behavior is safe, explicit degradation without changing the pytest
exit result or fabricating a successful receptor outcome.

### Diagnostic-efficiency gates

Token savings alone are insufficient. Measure:

- tokens emitted;
- number of additional pytest invocations needed to identify the cause;
- number of file/tool reads needed;
- whether the exact failing phase and rerun target are available;
- whether warning and skip drift is visible;
- root-cause identification accuracy on heterogeneous cascades.

Use a corpus of real failures from small and large scientific Python projects,
with sensitive data removed.

## Recommended implementation order

### Phase 0: correctness floor

1. Classify from `pytest.ExitCode`.
2. Fix no-tests and interruption reporting.
3. Escape XML or stop calling the output XML.
4. Preserve warnings and xpasses in summaries.
5. Correct or remove the heartbeat claim.
6. Add regression tests for each confirmed defect.
7. Fix the Python requirement to `>=3.11,<3.14`.
8. Stop unconditional in-memory capture of suppressed human output.
9. Fingerprint complete messages before renderer truncation.

This phase is small and should precede new features.

### Phase 1: lossless event model

1. Define `events@1` with session, test phase, exception, warning, and captured
   section records.
2. Implement the collector separately from rendering.
3. Write a JSONL artifact.
4. Make existing LLM and CI renderers consume the normalized model.
5. Prove count and outcome parity against pytest.
6. Model completeness, stop reason, logical tests, attempts, phases, and
   subtests independently.
7. Define stdout/stderr and artifact authority.

### Phase 2: reversible grouping and budgets

1. Introduce versioned fingerprints.
2. Retain occurrence-level deltas.
3. Add semantic budgets and artifact references.
4. Add warning, skip, xfail, and xpass grouping.
5. Add deterministic rerun instructions.
6. Add trust-boundary enforcement, control-character handling, and redaction.
7. Add a supported artifact-reader API.

### Phase 3: ecosystem robustness

1. Add pytest 8/9 and Python compatibility CI.
2. Validate xdist worker failures and crashes.
3. Validate reruns and subtests.
4. Isolate private pytest adapters.
5. Decide and implement the heartbeat model.

### Phase 4: evidence-based optimization

1. Establish a real failure corpus.
2. Benchmark multiple tokenizer families without coupling correctness to one.
3. Measure diagnostic sufficiency and follow-up tool calls.
4. Tune default budgets from evidence.
5. Publish reproducible benchmark metadata and commands.

## Acceptance criteria for a reliable 1.0

- No nonzero pytest exit status is rendered as `OK` or `CI` success.
- Every advertised machine syntax is parseable.
- Full evidence for every failure and warning is available in a versioned local
  artifact during normal lifecycle operation, or the artifact explicitly marks
  itself incomplete.
- Grouping never deletes occurrence-level location, phase, worker, capture, or
  cause information.
- Green runs expose warnings and unexpected passes according to explicit policy.
- Truncation always reports what was omitted and where the complete evidence
  lives.
- Serial and xdist results have count and outcome parity with pytest.
- Supported Python and pytest versions are exercised in CI.
- Documentation claims are backed by executable tests.
- Benchmarks measure both output size and diagnostic sufficiency.
- Fingerprints are derived before presentation truncation.
- Large suites have bounded, measured reporter memory overhead.
- Untrusted test output cannot alter receptor control structure.
- Artifact permissions, redaction, and failure behavior are tested.
- Session summaries state whether the collected suite completed.
- Python 3.11, 3.12, and all intended 3.13 patch releases satisfy package
  metadata.

## Expected result

This design keeps the project's strongest product idea while removing the main
risk. A coding agent receives a very small clean-green result, a compact but
sufficient red result, and a stable path to complete evidence when the first
summary is not enough. CI receives accurate status and durable artifacts. Human
users retain pytest's familiar output.

The result is not merely fewer tokens. It is a trustworthy bridge between
pytest's execution model and automated software-maintenance systems.
