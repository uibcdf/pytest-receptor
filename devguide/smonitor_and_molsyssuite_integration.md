# SMonitor and MolSysSuite Integration Boundary

**Status:** exploratory integration proposal; input to a later cross-repository
proposal digestion, not an accepted contract

**Recorded:** 2026-07-17

**Companion SMonitor proposal:**
`smonitor/devguide/pending_proposals/pytest_diagnostics_bridge_and_molsyssuite_policy.md`

## Purpose

Define what pytest-receptor must provide so SMonitor and a possible future
`pytest-molsyssuite` policy package can contribute structured evidence without
coupling the neutral receptor to the UIBCDF scientific stack.

## Distinct communication layers

This proposal does not redefine SMonitor's general communication with agents.
SMonitor already communicates runtime exceptions and diagnostics through
catalog-backed events, normalized payloads, the `agent` profile, structured
evidence, causal metadata, and support bundles. That contract applies whether
or not pytest is running.

The layers are distinct:

1. **Runtime exception and diagnostic communication:** SMonitor records what a
   library emitted or raised and why.
2. **Test execution evidence:** pytest and pytest-receptor record which test,
   phase, worker, and attempt produced an outcome.
3. **Correlation bridge:** an optional SMonitor pytest integration relates the
   first two layers without replacing either.
4. **Ecosystem policy:** a possible pytest-molsyssuite package decides which
   diagnostics and validation outcomes are acceptable in shared QA/CI profiles.

The future design digestion must preserve SMonitor's usefulness for ordinary
runtime raises outside pytest and must not assume all agent communication is a
test-reporting concern.

## Architectural boundary

pytest-receptor owns:

- pytest session and exit-status truth;
- collection and completeness state;
- test, phase, attempt, subtest, and worker evidence;
- failure and warning occurrence records;
- reversible grouping;
- presentation budgets and renderers;
- canonical pytest event artifact and artifact reader.

SMonitor owns:

- diagnostic codes and signals;
- structured context, evidence, causal metadata, and confidence;
- diagnostic fingerprints, profiles, routing, and redaction policy;
- library integration for ArgDigest, DepDigest, MolSysMT, and other producers;
- standalone support bundles outside pytest.

pytest-molsyssuite may eventually own:

- shared profile selection;
- ecosystem diagnostic and warning policy;
- accepted baseline management;
- common fixtures and markers;
- environment/version manifest;
- CI artifact naming and retention policy;
- orchestration of repository-owned validators.

pytest-receptor must not import or depend on SMonitor or MolSysSuite. Integration
uses a generic public extension protocol.

## Extension-event protocol

The receptor event schema should allow a plugin to attach a namespaced event or
relationship without controlling the reporter.

Conceptual record:

```json
{
  "schema": "pytest-receptor.extension-event@1",
  "namespace": "org.uibcdf.smonitor",
  "kind": "diagnostic",
  "event_id": "...",
  "relationships": {
    "pytest_run_id": "...",
    "test_event_id": "...",
    "nodeid": "tests/path.py::test_name",
    "phase": "call",
    "worker": "gw3",
    "attempt": 1
  },
  "payload_schema": "smonitor.event@...",
  "payload": {}
}
```

The exact schema requires review. The contract should guarantee:

- namespace isolation;
- stable event identifiers;
- explicit payload schema/version;
- association with zero or one test occurrence plus session-level events;
- worker and sequence provenance;
- safe serialization of unknown payloads;
- payload size and blob-reference policy;
- redaction status and trust classification;
- preservation when the renderer does not understand the namespace.

## Registration and transport

Candidate integration mechanisms:

- a public hook specification registered through pytest's plugin manager;
- a receptor service object exposed through a documented pytest stash key;
- a narrow Python protocol for emitting extension events;
- post-run artifact linking when live integration is unavailable.

Selection criteria:

- works in serial and xdist;
- does not rely on importing private receptor modules;
- does not let one plugin mutate another plugin's records;
- has defined behavior before collector initialization and after finalization;
- degrades to a standalone namespaced artifact without data loss;
- is testable with a dummy third-party producer unrelated to SMonitor.

The generic protocol must be designed using a neutral fixture/plugin first so
pytest-receptor does not accidentally encode SMonitor-specific assumptions.

## Correlation model

The receptor should expose current execution correlation without requiring a
producer to infer it from terminal output:

- pytest run ID;
- current node ID;
- current phase;
- worker ID;
- attempt/rerun number;
- logical test and phase event IDs;
- monotonic sequence where available.

In-process correlation may use `contextvars`, but xdist records require explicit
worker provenance. Background threads, processes, and asynchronous tasks need a
documented propagation boundary.

Extension events emitted outside an active test remain valid session-level
events. The receptor must not assign them to the most recent test by guesswork.

## Cross-source deduplication

pytest-receptor may observe one incident through several channels:

- pytest warning;
- SMonitor extension event;
- captured log/stderr;
- test exception;
- linked SMonitor bundle.

Do not delete these records by message equality. Represent relationships such
as:

- `representation_of`;
- `caused_by`;
- `emitted_during`;
- `duplicate_of` with producer evidence;
- `derived_from`.

The renderer can present one causal incident while the artifact retains every
source record. Cross-source grouping should require stable identifiers or
high-confidence policy, not heuristic text similarity alone.

## Rendering extension diagnostics

The LLM renderer should provide a generic compact extension section. For a
known SMonitor adapter it may use stable fields such as code, severity,
confidence, evidence, and next step. Unknown namespaces remain visible and
addressable.

Example:

```text
diagnostics=3 occurrences/1 group
SMONITOR ARGDIGEST-WARN-MISSING-DIGESTER x3
  argument=value_range callable=molsysviewer.color_by
  tests=2 phase=call workers=gw1,gw3
  confidence=high
  evidence=.pytest-receptor/...jsonl#ext-group-2
```

Extension-provided hints are untrusted policy data until their provenance and
confidence are established. pytest-receptor must never execute them.

## Artifact composition

The receptor JSONL artifact is authoritative for pytest outcome and execution
completeness. SMonitor may:

- embed normalized extension events;
- reference a redacted standalone SMonitor bundle by path/hash/schema;
- provide summary fields for rendering;
- retain richer standalone profiling data outside the receptor artifact.

Artifact composition must avoid:

- conflicting exit outcomes;
- silent duplication of large event buffers;
- circular artifact references;
- unredacted payloads entering public CI artifacts;
- loss of extension events when a producer finalizes after pytest reporting.

Define finalization ordering and allow an explicit incomplete-extension marker.

## Possible pytest-molsyssuite consumer

### Function

`pytest-molsyssuite` would be a thin policy/composition plugin used by the
MolSysSuite repositories. It would configure and evaluate existing tools rather
than own evidence collection or rendering.

### Candidate characteristics

- select `dev`, `qa`, `ci`, or `agent` profiles;
- configure pytest-receptor and the SMonitor bridge through public APIs;
- compare warning/diagnostic fingerprints with accepted baselines;
- enforce MolSysSuite rules for unknown codes, unresolved catalog templates,
  missing ArgDigest digesters, invalid validated-payload use, and diagnostic
  emission failures;
- assemble a privacy-aware ecosystem version/commit manifest;
- expose shared diagnostic expectation fixtures and capability markers;
- invoke repository-declared validators without copying their implementation;
- standardize local/CI artifact paths, schemas, redaction, and retention;
- report new, recurrent, and disappeared diagnostic incidents;
- preserve exact pytest exit and complete/incomplete status.

### Non-characteristics

It is not:

- another TerminalReporter;
- another JSONL event implementation;
- a replacement for SMonitor bundles;
- a runtime dependency of MolSysSuite scientific libraries;
- a reason to import optional scientific packages during pytest startup;
- an automatic dependency installer or failure fixer;
- a mechanism for forced lockstep releases.

### Dependency direction

```text
pytest-receptor                 neutral base
       ^
       |
SMonitor optional bridge        diagnostic producer/adapter
       ^
       |
pytest-molsyssuite              policy and composition
```

pytest-receptor must never depend upward. The MolSysSuite policy package should
be installed only in development/test environments.

### Extraction gate

Do not create `pytest-molsyssuite` until:

- the receptor extension protocol is stable;
- the SMonitor bridge works in serial and xdist;
- MolSysMT and MolSysViewer have completed shadow/dogfooding runs;
- a third repository demonstrates the same shared policy needs;
- startup and runtime overhead are measured;
- ownership, compatibility, and release policy are assigned.

Before that point, maintain experimental policy close to each repository and
use the SMonitor proposal as the cross-project source of intent.

## pytest-receptor requirements created by this integration

- Public neutral extension-event protocol.
- Current-test correlation service with explicit lifecycle boundaries.
- Namespaced unknown-event preservation.
- Extension schema/version metadata.
- Cross-worker transport and ordering evidence.
- Relationship model rather than destructive cross-source deduplication.
- Redaction/trust metadata propagation.
- Artifact reference and incomplete-extension support.
- Generic extension rendering with strict token budgets.
- Dummy-producer contract tests independent of SMonitor.

## Validation scenarios

1. A SMonitor diagnostic emitted during setup is associated only with setup.
2. Equal diagnostic codes from two workers retain both occurrence contexts.
3. A Python warning and SMonitor representation of the same event render as one
   incident while both records remain recoverable.
4. Independent equal messages are not deduplicated without a relationship.
5. An ArgDigest missing-digester diagnostic retains callable and argument data.
6. A session-level diagnostic is not assigned to the last executed test.
7. An unknown extension namespace survives round trip and truncation.
8. Redacted fields cannot reappear through captured logs or linked artifacts.
9. Bridge failure preserves pytest outcome and marks extension evidence
   incomplete.
10. xdist worker loss leaves received extension events recoverable and the
    session explicitly incomplete.

## Recommended sequencing

1. Complete the receptor correctness floor.
2. Design the neutral extension protocol with a dummy producer.
3. Review it jointly with SMonitor's event and bundle contracts.
4. Implement the optional SMonitor bridge inside SMonitor.
5. Dogfood the integration on MolSysMT and MolSysViewer.
6. Stabilize shared diagnostic policies across a third repository.
7. Decide whether `pytest-molsyssuite` merits extraction.

## Future proposal digestion

This proposal should be digested jointly with:

- SMonitor exception/raise and agent-profile contracts;
- SMonitor structured-extra preservation debt;
- SMonitor's existing Project A for pytest/CI;
- pytest-receptor's evidence and trust proposals;
- real cross-library diagnostics from ArgDigest, MolSysViewer, and MolSysMT;
- any later pytest-molsyssuite policy prototype.

The digestion should decide the canonical event relationships, extension
mechanism, artifact ownership, correlation identifiers, and whether a separate
package is justified. Until then, all schemas and package names here are
illustrative.

## Provisional conclusion

A neutral extension boundary appears to be the cleanest direction, but this is
not yet an accepted pytest-receptor contract. The future
`pytest-molsyssuite` package remains a potentially useful policy and composition
layer only after the lower-level contracts have been digested and demonstrated
in real repositories.
