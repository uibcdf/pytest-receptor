# Critical Technical Audit of pytest-receptor

**Recorded:** 2026-07-17

**Scope:** read-only review of the repository documentation, package code,
tests, packaging metadata, and representative runtime behavior

**Tested with:** Python 3.13 and pytest 9.0.2

**Operational follow-up:** `audit_action_register_2026-07-17.md`

**Status:** historical record, still accurate as an assessment. It is not updated
as findings are fixed — the register tracks that. Where this document recommends
repairing a feature that 0.6 instead deletes (XML, installation hints, the
heartbeat), `scope_0.6.md` and `superseded_proposals.md` record the decision.

## Executive assessment

`pytest-receptor` addresses a real and increasingly important problem. Pytest's
terminal output is designed primarily for humans, while coding agents need a
compact, deterministic, high-signal representation. The receptor concept is a
good abstraction: the same test execution may need different presentations for
a person, an LLM, a CI log, or a machine consumer.

The current implementation should nevertheless be treated as a promising
proof of concept rather than a diagnostic authority. It is very effective for
green suites and simple repeated failures, but it can currently discard
information needed to diagnose warnings, heterogeneous cascades, interrupted
runs, external-library failures, and distributed execution. In two reproduced
cases it reports `OK` even though pytest exits unsuccessfully.

The optimization objective should be refined from "minimize output tokens" to:

> Minimize tokens while preserving the evidence needed to classify,
> reproduce, and resolve the test outcome.

This is not a reason to abandon the project. It is a reason to evolve it from a
compact terminal formatter into an evidence-preserving diagnostic protocol
with receptor-specific renderers.

## Indicative ratings

These scores are engineering judgments intended to identify priorities, not
formal quality measurements.

| Area | Current rating |
| --- | ---: |
| Usefulness of the core idea | 9.0/10 |
| Novelty and timing | 8.5/10 |
| Efficiency for green suites | 9.0/10 |
| Efficiency for homogeneous cascades | 8.0/10 |
| Diagnostic fidelity | 4.5/10 |
| Traceability | 4.0/10 |
| Internal architecture | 5.5/10 |
| Robustness across pytest and plugins | 4.5/10 |
| Scenario coverage | 5.0/10 |
| Documentation accuracy | 5.5/10 |
| Overall current maturity | 6.2/10 |
| Plausible maturity after the proposed redesign | 9.0/10 |

## Review method

The audit read all Markdown documentation, `pyproject.toml`, the package source,
the test suite, the development environment definition, and the recent Git
history. Ruff passes on `src/` and `tests/`.

Runtime probes loaded the plugin explicitly and exercised:

- a normal assertion diff;
- duplicate setup failures;
- equal exception messages with different captured logs;
- warnings, skips, xfail, and xpass;
- a collection-time import failure;
- an empty test directory;
- `KeyboardInterrupt`;
- `pytest-xdist` with two workers;
- a single six-second test under the CI receptor;
- messages and captured output containing XML metacharacters.

The repository's token benchmark module could not be collected in the active
environment because `tiktoken` was not installed. This is consistent with
`tiktoken` being a development extra and does not by itself prove a packaging
defect. It does mean that contributors must use the documented development
environment or that the benchmark tests must skip explicitly when the optional
benchmark dependency is absent.

## Confirmed correctness defects

### Unsuccessful sessions can be rendered as successful

The LLM report treats the absence of entries in the reporter's `failed` and
`error` buckets as success. It does not use the session `exitstatus` to classify
the run.

An empty test directory exited with pytest status 5 and produced:

```text
OK: 0 passed in 0.02s
```

A test raising `KeyboardInterrupt` exited with status 2 and produced:

```text
OK: 0 passed in 0.21s
```

This is the highest-severity defect. An agent or CI wrapper may accept an
incomplete run as evidence that the tested contract passed.

The session outcome must be based on pytest's exit status and explicitly
distinguish at least:

- passed;
- test failures;
- interrupted;
- internal error;
- usage error;
- no tests collected;
- collection errors.

The exit code should be present in every machine- or LLM-oriented summary.

### The advertised XML is not well formed

Exception messages, captured streams, paths, node IDs, and other values are
inserted directly into XML-like tags. They are not escaped.

The reproduced message:

```text
RuntimeError: shared <failure> & value
```

and captured output:

```text
fixture stdout <tag> & payload
```

produce malformed XML. Quotes in attribute values can break the structure in
the same way. The output is therefore useful visual markup, but it is not a
safe parseable protocol as currently documented.

All values must be serialized through a real XML encoder, or the canonical
machine artifact should use JSON/JSONL with a schema. If an XML renderer
remains, it should be tested by parsing every golden output.

### Deduplication discards per-occurrence evidence

Grouping by exception type and normalized message is valuable for fixture
cascades. The current group stores the location, traceback, captured sections,
and message from the first occurrence only. Later occurrences contribute just
their node ID and phase.

Two tests with `ValueError("same message")` but different captured log messages
were grouped. Only the first log survived. If equal messages arise through
different call sites, only the first call site's location and traceback survive
as well.

Deduplication must compress common evidence without destroying occurrence-level
differences. Each occurrence needs its own node ID, phase, worker, location,
captured sections, and traceback delta or reference.

### The CI heartbeat is not periodic

The heartbeat check runs only when `pytest_runtest_logreport` receives a
completed phase. It cannot emit while a test or fixture is still running.

A single six-second test produced no heartbeat. The first output arrived only
after the test completed. A stalled test could therefore remain silent for an
arbitrary period, contrary to the README and Usage Guide claims.

Either implement a safely managed periodic watchdog, emit accurately described
progress events at lifecycle boundaries, or remove the heartbeat claim until
the implementation exists.

### The declared Python range excludes Python 3.13 patch releases

`pyproject.toml` currently declares:

```toml
requires-python = ">=3.11,<=3.13"
```

Under PEP 440, `3.13.1` is greater than `3.13`. The declaration therefore
allows 3.13.0 but rejects 3.13.1 and every later 3.13 patch release. The tested
membership is:

```text
3.11.9  allowed
3.12.10 allowed
3.13.0  allowed
3.13.1  rejected
3.13.11 rejected
```

If the intended support policy is Python 3.11 through 3.13, the bound should be
expressed as `>=3.11,<3.14`. This is a release and installation defect rather
than a reporter defect, but it can prevent the package from being installed in
an explicitly supported environment.

## Confirmed information loss

### Warnings disappear from successful runs

A successful test emitting a `RuntimeWarning` produced no warning information
in LLM mode. The final line reported only outcome counts.

Warnings are not necessarily noise. They often reveal deprecated APIs, missing
argument digesters, numerical fallback, resource problems, optional dependency
misconfiguration, or contracts that will fail in a future release. A green
suite with new warnings is materially different from a clean green suite.

The LLM receptor should fingerprint warnings by category, normalized message,
and origin. A compact green result could report:

```text
OK: 1200 passed, 3 skipped in 42.1s; WARNINGS: 12 occurrences in 2 groups
```

It should then include the warning groups or a durable reference to them.

### Skip, xfail, and xpass traceability is insufficient

The current summary preserves counts but drops node IDs and reasons. This makes
it impossible to distinguish a stable expected skip set from a newly skipped
capability. A non-strict unexpected pass is especially important because it may
mean a known bug was fixed and its xfail marker should be removed.

At minimum:

- xpasses should be listed with node ID and reason;
- skips and xfails should be grouped by reason;
- changes from an optional baseline should be highlighted;
- strict xpass failures must remain ordinary failures.

### Traceback pruning is too aggressive and partly mislabeled

Filtering external frames can reduce noise, but an external frame can be the
scientifically or technically decisive location. Failures in NumPy, Pandas,
OpenMM, HDF5, a serializer, or another pytest plugin may require the boundary
and terminal external frames.

The displayed `in ...` text is currently derived from `reprfileloc.message`,
which represents the failure message rather than a reliable function name. A
probe consequently produced `in ValueError`, not the function name.

A compact traceback should preserve:

- the local frame that initiated the operation;
- the local-to-external boundary;
- the origin or terminal external frame;
- the final local frame, when different;
- exception cause and context chains;
- the assertion expression and structured diff.

The full traceback should remain available in the lossless artifact.

### Fixed character truncation is not a safe information budget

The implementation limits messages to 1500 characters and keeps the first 1000
and last 400 characters. Character count is not token count, and the omitted
middle may contain the only differing record in a large scientific array,
mapping, or schema diff.

Truncation should be semantic and auditable. It should record:

- original length;
- retained length;
- a content hash;
- omitted sections;
- the applicable budget;
- the path or identifier of the complete artifact.

Budgets should be configurable. A failure summary, traceback, assertion diff,
captured streams, and warning section may need separate limits.

### Fingerprints are computed after destructive truncation

The current order is:

```text
complete message -> truncate -> normalize -> fingerprint
```

Two long failures that differ only in the discarded middle can consequently
produce the same fingerprint. The renderer then groups them and retains only
the first occurrence's evidence, compounding two independent information-loss
mechanisms.

Fingerprinting must operate on the complete normalized evidence. Presentation
budgets and truncation belong after grouping and must never influence semantic
identity.

## Architecture and integration risks

### Replacing pytest's private TerminalReporter is brittle

The plugin unregisters pytest's terminal reporter and registers a subclass of
`_pytest.terminal.TerminalReporter`. This is a private implementation surface.
It can work, but compatibility must be proven across supported pytest versions
and common reporting plugins.

Risk areas include:

- pytest 8 versus pytest 9 internals;
- xdist collection and worker lifecycle;
- rerun plugins;
- subtests;
- plugins that retrieve the standard terminal reporter by identity or name;
- plugins that write directly to the terminal writer;
- future changes to reporter statistics categories;
- worker crashes and serialized reports.

The basic two-worker probe produced compact output, but it did not retain worker
identity, event order, or per-worker context.

### The implementation formats reporter text instead of owning evidence

The original design notes propose reading structured exception information.
The implementation instead relies substantially on `longrepr`, formatted crash
messages, and `TerminalReporter.stats`. Exception type extraction parses text
heuristically.

This makes the renderer dependent on pytest's current textual representation
and limits what can be reconstructed later. Collection failures, runtime
failures, warnings, setup and teardown, and distributed reports do not all have
the same representation.

The project needs a normalized event model populated through the relevant
pytest hooks before receptor-specific rendering.

### Adaptive installation hints can recommend incorrect mutations

`ModuleNotFoundError` does not imply that the correct action is to install a
distribution with the same name:

- import names and distribution names can differ;
- the dependency may be deliberately optional;
- pytest may be running in the wrong environment;
- the project's dependency policy may prohibit direct installation;
- test dependencies generally belong in a development group;
- environment managers have different declarative commands.

Hints should be conservative and diagnostic by default. Project-specific
dependency advice should come from a configurable resolver or policy plugin,
not from a generic message heuristic.

### Wall-clock time is used for elapsed durations

Session and heartbeat timing use `time.time()`. Elapsed time should use
`time.monotonic()` so clock adjustments cannot produce invalid durations or
heartbeat behavior.

### The human dump is not guaranteed to be a complete human run

The dump is the output captured through the replacement reporter's dummy
terminal writer. Output written directly by other plugins or processes may not
be represented. It should be documented as captured `TerminalReporter` output,
or a separate integration test should prove the stronger claim.

### Quiet output is accumulated in memory unconditionally

`DummyTerminalWriter` appends every suppressed write to `captured_lines`. This
happens even when neither `--receptor-stats` nor `--receptor-dump-dir` is active.
The LLM and CI receptors can therefore suppress a large terminal report while
still retaining that complete report in memory, in addition to pytest's report
objects and captured test sections.

This is a scalability defect for large suites and failure cascades. Human-output
capture should be disabled unless requested. When requested, it should stream
to a bounded or on-disk sink instead of requiring one unbounded in-memory list.
CPU time and peak memory must be measured alongside token savings.

### Report counts are not the same as logical test outcomes

The implementation derives summaries from `TerminalReporter.stats`. Those
categories contain reports and may represent setup, call, teardown, reruns, or
plugin-specific outcomes. One logical test may pass its call phase and fail its
teardown, or may produce several attempts and subtest results.

The diagnostic model must distinguish:

- collected test items;
- logical tests;
- execution attempts;
- setup, call, and teardown phases;
- subtests;
- reruns;
- final consolidated outcomes.

Without that separation, a numerically plausible summary can still misstate
what actually passed.

### Output-channel integrity is undefined

The plugin controls the registered terminal reporter but cannot assume every
plugin writes through it. Direct stdout/stderr writes, live logging, usage
errors raised before `pytest_configure`, coverage plugins, and worker output can
contaminate an advertised machine-readable stream.

The contract needs to state which channel is authoritative, what may appear on
stdout and stderr, and whether parseable output is guaranteed only in a
dedicated artifact. Broken pipes and renderer failures also need explicit
degradation behavior.

## Security and trust-boundary risks

### Test output is untrusted input to an LLM

An LLM-oriented reporter processes exception messages, logs, paths, parameter
IDs, and captured streams originating from tests and dependencies. That content
can contain XML injection, terminal control sequences, misleading commands, or
prompt-injection text such as instructions to ignore prior constraints.

Escaping XML is necessary for valid syntax but does not neutralize prompt
injection. The renderer must clearly delimit test-produced evidence as
untrusted data and must never reinterpret captured text as receptor directives
or trusted repair instructions.

### Diagnostic artifacts can expose secrets

Captured output and tracebacks can include tokens, credentials, environment
variables, private paths, database URLs, molecular or clinical data, and other
sensitive values. Dumps and future JSONL artifacts therefore require:

- restrictive file permissions;
- configurable redaction before rendering or persistence;
- explicit retention and cleanup policy;
- size limits and safe failure behavior;
- no implicit upload;
- documented handling of symlinks and user-selected paths;
- separation between public CI artifacts and restricted local evidence.

Hints that resemble shell commands deserve special care. Even a correctly
escaped missing-module name should not become an automatically trusted command.

## Session completeness and abnormal termination

Exit status and outcome are not enough to describe whether the intended suite
completed. `--maxfail`, `-x`, interruption, collection failure, worker loss,
timeouts, sharding errors, and exhausted reruns can leave most collected tests
unexecuted.

The session record should expose:

```text
complete=false
stop_reason=maxfail
collected=8241
executed=137
not_executed=8104
```

The architecture proposal uses the term "lossless", but no pytest plugin can
guarantee complete evidence after `SIGKILL`, a segmentation fault, host loss,
filesystem exhaustion, or process termination before finalization. The durable
claim should be narrower: evidence-preserving during normal pytest lifecycle
operation, with best-effort streaming and explicit detection of incomplete
artifacts after abnormal termination.

## Programmatic-consumer gap

The receptor is currently a CLI reporting feature. Agents, IDEs, CI systems,
and orchestration tools will gain more from a stable programmatic interface to
session records, events, groups, and artifacts than from reparsing stdout.

A public Python API or documented artifact-reading library should eventually
accompany the event schema. This also provides a cleaner extension point for
project-specific redaction, fingerprinting, dependency hints, and renderers.

## Testing and release gaps

The current tests cover the proof-of-concept strengths: green and red output,
captured streams, simple deduplication, hints, stats, dump files, slow tests,
normalization, and token reductions. They do not protect the most important
session and fidelity boundaries.

Required additional scenarios include:

- every pytest exit status;
- no tests collected;
- `KeyboardInterrupt`;
- pytest internal errors;
- multiple collection errors;
- setup, call, and teardown failures;
- exceptions raised during fixture finalization;
- warnings on green and red runs;
- skip, xfail, xpass, and strict xpass reasons;
- valid serialization with XML metacharacters and arbitrary Unicode;
- identical messages with different locations and captured sections;
- chained exceptions and exception groups;
- truncated diffs with lossless-artifact references;
- `pytest-xdist` worker identity, worker crash, and restart;
- `pytest-rerunfailures` attempts;
- `pytest-subtests` identities;
- one long-running test and a genuinely periodic heartbeat;
- reporter coexistence with common plugins;
- fail-fast and max-failure incomplete sessions;
- report-level counts versus logical test outcomes;
- prompt-injection strings, ANSI escapes, and control characters;
- secret-redaction and artifact-permission behavior;
- broken pipes, unwritable artifacts, and disk exhaustion;
- direct stdout/stderr writes from other plugins;
- fingerprint collisions caused by differences in truncated content;
- bounded-memory behavior on large green and red suites;
- supported Python patch releases accepted by package metadata;
- pytest 8 and pytest 9 across every supported Python version.

There is no repository CI workflow. A general pytest plugin needs a compatibility
matrix because its primary dependency is also its extension host.

Token benchmarks should become reproducible artifacts with recorded Python,
pytest, plugin, tokenizer, command, and fixture versions. They should measure
not only compression but diagnostic sufficiency: whether a consumer can identify
the root cause and exact rerun target without another full-output invocation.

## Documentation issues

The documentation explains the vision clearly, but several claims exceed the
current implementation:

- the CI heartbeat is described as periodic although it is report-triggered;
- output is described as XML although values are not escaped;
- local traceback pruning is presented as sufficient without documenting lost
  external origins;
- warning removal is presented only as token savings;
- dumps are described as parallel human and LLM reports without noting the
  capture boundary;
- benchmarks lack a committed reproduction protocol and environment record.

There are also smaller editorial issues such as mixed-language terms
(`Sanitización`, `Volcado`), `Dumping` where `deduplication` is intended,
`Formated`, and a local `file://` license link in the README. These do not affect
execution but reduce release polish.

## What should be retained

The following ideas are strong and should remain:

- receptor-oriented consumer profiles;
- complete silence during genuinely successful execution;
- one-line clean-green summaries;
- grouping homogeneous fixture cascades;
- deterministic, compact failure representation;
- human, LLM, CI, and future machine profiles;
- captured output sections when they contribute to a failure;
- slow-test reporting;
- normalization of non-semantic dynamic values;
- optional audit artifacts;
- explicit measurement of output cost.

The issue is not that these ideas are wrong. They need a lossless evidence layer
underneath them.

## Final verdict

`pytest-receptor` is useful today for clean suites and simple failures, and its
concept is worth developing. It is not yet safe as the only diagnostic output
for automated maintenance because it can report interrupted or empty runs as
successful and can silently discard warnings and per-occurrence evidence.

The recommended next step is not a larger set of formatting heuristics. It is a
small, explicit diagnostic event schema and a lossless collector. Once that
foundation exists, the current LLM renderer can become both more compact and
more trustworthy.
