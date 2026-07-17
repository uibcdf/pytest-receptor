# Trust and Adoption Criteria

**Recorded:** 2026-07-17

**Related documents:**

- `critical_audit_2026-07-17.md`
- `evidence_preserving_architecture_proposal.md`
- `audit_action_register_2026-07-17.md`

## Executive position

If the corrections and architecture described by the audit are implemented and
validated, `pytest-receptor` should be useful enough to become the primary
pytest interface for coding agents.

The project addresses a recurring operational problem:

- green suites can emit thousands of low-value tokens;
- one root cause can be repeated across many failed tests;
- aggressively shortened pytest output can hide the decisive assertion diff or
  traceback boundary;
- important warnings can be buried in otherwise successful output;
- xdist can make timing, worker ownership, and causal reconstruction difficult;
- agents often rerun pytest several times merely to recover information pytest
  already observed.

A trustworthy receptor can provide a concise first answer and a stable route to
the complete evidence:

```text
FAILED exit=1 complete=true
8241 collected, 8239 passed, 2 failed
1 root-cause group, 12 warnings in 2 groups

Root cause:
tests/native/test_topology.py::test_merge
IndexError at molsysmt/form/molsysmt_Topology/merge.py:117

Affected:
- test_merge_simple
- test_merge_viewer

Rerun:
pytest tests/native/test_topology.py::test_merge -q

Full evidence:
.pytest-receptor/run-...jsonl#failure-group-01
```

The value is not only token reduction. It is reducing the number of additional
commands and evidence-recovery steps required to reach the cause and repair.

## Adoption levels

### Level 0: current proof of concept

Recommended use:

- optional compact view for simple green suites;
- exploratory comparison with normal pytest output;
- token-output experiments.

Not recommended as:

- the only diagnostic output for red suites;
- CI authority;
- evidence that an interrupted or empty run succeeded.

Indicative trust: **50-55%**.

### Level 1: correctness floor implemented

Entry requirements:

- session classification uses `pytest.ExitCode`;
- no-tests and interruption cannot render as success;
- advertised machine syntax is structurally valid;
- warnings and xpasses remain visible;
- deduplication preserves occurrence-level evidence;
- fingerprints precede presentation truncation;
- suppressed human output is not accumulated unconditionally;
- Python support metadata accepts all intended patch releases;
- public documentation matches tested behavior.

Recommended use:

- routine local development;
- compact agent-facing output;
- CI trial mode beside JUnit or standard pytest evidence.

Normal pytest or a complete artifact should remain available as the authority.

Indicative trust: **75-80%**.

### Level 2: evidence-preserving architecture implemented

Entry requirements:

- normalized session and event model;
- versioned JSONL artifact;
- explicit complete/incomplete session state;
- reversible grouping;
- semantic output budgets with artifact references;
- warning, skip, xfail, xpass, rerun, phase, and worker traceability;
- tested redaction and untrusted-content boundaries;
- supported artifact reader;
- safe degradation if collection, persistence, or rendering fails.

Recommended use:

- default receptor for coding agents;
- primary terminal interface in development;
- CI presentation layer, with the artifact retained as machine evidence;
- integration with IDEs and orchestration tools through the artifact API.

Indicative trust: **88-92%** before extended real-world validation.

### Level 3: validated operational authority

Entry requirements:

- differential parity against pytest and JUnit across the supported matrix;
- sustained use on large real repositories;
- adversarial security and failure-injection suite;
- compatibility evidence for pytest, Python, xdist, coverage, reruns, subtests,
  and live logging;
- bounded and measured memory/runtime overhead;
- stable schema and compatibility policy;
- no unexplained semantic divergence during the dogfooding period.

Recommended use:

- primary pytest interface for agents;
- trusted CI summary and annotation source;
- standard diagnostic integration for supported consumers.

The complete event artifact remains the authority whenever presentation is
compressed.

Indicative trust: **92-96%**. Absolute 100% trust is not a realistic engineering
claim for a plugin operating inside another extensible execution framework.

## Non-negotiable trust invariants

### Never fabricate success

This is the absolute adoption condition:

> If pytest did not complete successfully, or if the receptor cannot determine
> the outcome safely, the receptor must not emit an `OK` or CI-success result.

An internal receptor failure should degrade to something explicit:

```text
RECEPTOR_ERROR exit=1 pytest_outcome=failed evidence_incomplete=true
```

Preserving an uncomfortable truth is more important than always producing a
well-formed compact report.

### Compression must be reversible during normal operation

Every omitted or truncated diagnostic should state:

- what was omitted;
- original and retained size;
- content hash;
- reason and applicable budget;
- artifact and event reference;
- whether the artifact finalized successfully.

Trust does not require displaying everything. It requires proving that
presentation compression did not silently destroy the evidence.

### Test-produced text is untrusted evidence

Exception messages, logs, paths, parameter IDs, and captured streams must never
be interpreted as receptor instructions or trusted repair commands. Structural
escaping, explicit data boundaries, control-character handling, redaction, and
hint provenance are adoption requirements rather than optional hardening.

### Unknown states fail visibly

Unknown report types, plugin outcomes, schema versions, renderer failures, and
artifact errors must become explicit opaque or degraded states. They must not
be dropped, guessed, or mapped to success.

## Evidence required for trust

### Semantic parity with pytest

For every run, receptor evidence must agree with pytest on:

- exit status;
- collected, executed, deselected, and not-executed counts;
- passed, failed, and errored logical tests;
- setup, call, and teardown failures;
- warnings, skips, xfails, and xpasses;
- collection errors and interruption;
- rerun attempts and final result;
- complete versus partial execution.

Use differential testing: execute the same generated or curated suite with the
receptor, standard terminal reporter, and JUnit, then compare their semantic
models automatically. Formatting differences are expected; unexplained outcome
differences are failures.

### Adversarial validation

The validation corpus must include:

- prompt-injection-shaped captured text;
- XML/JSON metacharacters and arbitrary Unicode;
- ANSI escapes and terminal control characters;
- very large exception messages and logs;
- simulated credentials and redaction patterns;
- `SIGINT`, timeouts, and abnormal process termination;
- xdist worker loss and restart;
- unwritable destinations and storage exhaustion;
- renderer exceptions and broken pipes;
- direct output from another plugin;
- equal messages with distinct call sites, causes, phases, workers, and logs;
- almost-equal long messages whose difference lies inside a presentation-truncated
  region.

The expected result is explicit, conservative degradation without changing the
pytest outcome.

### Compatibility evidence

The initial supported matrix should include:

- Python 3.11, 3.12, and 3.13;
- oldest supported pytest 8;
- newest pytest 8;
- pytest 9;
- serial execution;
- xdist;
- coverage and JUnit;
- reruns and subtests;
- live logging;
- `-x`, `--maxfail`, selection, and sharding.

Support claims should be generated from passing evidence or maintained in one
explicit registry. An open-ended `pytest>=8` dependency is not sufficient proof
of compatibility with future pytest internals.

### Operational and release evidence

Trust also requires:

- versioned event and artifact schemas;
- migration and unsupported-version policy;
- deterministic golden outputs;
- restrictive artifact permissions;
- documented retention and cleanup;
- measured runtime and peak-memory overhead;
- CI for every supported platform/version class;
- changelog and deprecation policy for public receptor behavior;
- a conservative fallback path to standard pytest diagnostics.

## MolSysMT dogfooding program

MolSysMT is a strong proving ground because it contains:

- more than eight thousand tests;
- doctests;
- scientific reference tests;
- optional dependencies;
- warnings that can reveal incomplete contracts;
- GPU requests and CPU fallbacks;
- xdist execution with twelve workers;
- slow tests and large molecular fixtures;
- external scientific libraries;
- historical collection, conversion, and integration failures.

### Stage A: shadow comparison

Run standard pytest/JUnit as the authority and generate receptor output from the
same execution or an equivalent paired execution.

Record:

- outcome and count parity;
- missing warning or failure evidence;
- grouping collisions;
- artifact completeness;
- token count;
- runtime and memory overhead;
- additional commands needed by the agent.

Do not allow receptor output to decide release success during this stage.

### Stage B: agent-facing default

After sustained semantic parity, use the receptor as the default output shown to
the coding agent while retaining JUnit or the receptor JSONL artifact as the
authority.

Any need to rerun with standard output because evidence was missing becomes a
diagnostic-sufficiency incident and a regression candidate.

### Stage C: CI presentation authority

Promote the receptor to CI summary and annotation authority only after:

- no unexplained parity divergence across the observation window;
- correct incomplete-session behavior;
- tested artifact failure handling;
- stable warning policy;
- compatible xdist behavior;
- security review of public CI artifacts.

The raw pytest exit status and complete event artifact must remain available.

## Success metrics

Token savings remain useful but are not the primary trust metric.

Measure:

- root cause identified from the first receptor response;
- exact failed phase available;
- exact rerun node ID available;
- warnings and unexpected passes visible;
- fixture cascades distinguished from independent causes;
- number of additional pytest executions required;
- number of file and artifact reads required;
- time from failed run to validated repair;
- false grouping and missed grouping rate;
- semantic parity incident rate;
- incomplete artifacts detected correctly;
- renderer runtime and peak-memory overhead;
- redaction false-negative and false-positive rates.

An effective receptor should reduce output tokens and reduce the number of
follow-up actions. Saving tokens while causing an additional full pytest run is
often a net loss.

## Promotion gates

### Gate 1: safe experimental use

- All Critical audit findings closed.
- Nonzero exits cannot render as success.
- Parseability and warning visibility regressions pass.

### Gate 2: routine development use

- All High audit findings closed or explicitly accepted with a safe fallback.
- Artifact and occurrence traceability implemented.
- Memory overhead bounded.
- Python/pytest compatibility CI active.

### Gate 3: agent-facing default

- MolSysMT shadow comparison shows sustained semantic parity.
- Diagnostic-sufficiency incidents are below an agreed threshold.
- Security and redaction suite passes.
- Artifact reader API is stable enough for the active consumer.

### Gate 4: CI authority

- Failure, interruption, collection, maxfail, and worker-crash behavior proven.
- Public artifact policy reviewed.
- Renderer and storage degradation paths proven.
- Release owner explicitly accepts the supported integration matrix.

## Final adoption decision

If the proposal is implemented with semantic parity, durable evidence, safe
degradation, security boundaries, compatibility testing, and prolonged
dogfooding on MolSysMT, `pytest-receptor` should be trusted and preferred over
conventional pytest terminal output for agent-driven work.

The governing principle is:

> The receptor may compress presentation, but it must never compress the truth.
