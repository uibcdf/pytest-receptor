# Audit Action Register

**Recorded:** 2026-07-17

**Revised:** 2026-07-18 — completed against every devguide document, split phases
decomposed, xpass contradiction resolved, and reorganized around the accepted
0.6 scope.

**Source documents:**

| Key | Document |
| --- | --- |
| SCOPE | `scope_0.6.md` — authority for what ships in 0.6 |
| AUD | `critical_audit_2026-07-17.md` |
| ARCH | `evidence_preserving_architecture_proposal.md` |
| TRUST | `trust_and_adoption_criteria.md` |
| SMON | `smonitor_and_molsyssuite_integration.md` |
| OLD | `superseded_proposals.md` — rejected and replaced proposals, preserved |
| ISSUE | `original_issue_in_pytest.md` |

## Purpose

This register is the single complete work queue for the project. Every action
proposed in any devguide document appears here with an identifier, a release, a
phase, and a status. If a proposal exists in another document but not in this
table, that is a defect in this register.

`scope_0.6.md` decides **what** ships in 0.6 and why. This register tracks
**every** item, including the ones deliberately deferred. Where the two differ on
a required outcome, SCOPE wins and this register is corrected.

## Severity definitions

| Severity | Meaning |
| --- | --- |
| Critical | Can report an unsuccessful or incomplete pytest run as successful. |
| High | Can destroy decisive diagnostic evidence, break parseability, expose sensitive data, or prevent installation in a supported environment. |
| Medium | Reduces traceability, compatibility, scalability, or operational reliability. |
| Low | Documentation, polish, or optimization debt without immediate correctness impact. |

## Identifier prefixes

| Prefix | Domain |
| --- | --- |
| PR-CRIT | Session outcome truth |
| PR-FID | Diagnostic fidelity and information retention |
| PR-ARCH | Internal architecture and extension boundaries |
| PR-API | Programmatic consumer surface |
| PR-OPS | Runtime operation, resources, and compatibility |
| PR-SEC | Security and trust boundaries |
| PR-UX | Agent-facing output behavior and guidance |
| PR-DOC | Documentation accuracy |
| PR-REL | Packaging, benchmarking, and release evidence |

## Work queue

`Release` is `0.6` or `post`. `Phase` orders post-0.6 work using the phase model
in ARCH. Status values are `open`, `in progress`, `done`, or `accepted
limitation`.

| ID | Sev | Finding | Required outcome | Release | Phase | Status |
| --- | --- | --- | --- | --- | --- | --- |
| PR-CRIT-001 | Critical | No-tests session rendered as `OK` | Render `NO_TESTS`, retain exit 5, never emit success | 0.6 | 0 | **done 2026-07-18** |
| PR-CRIT-002 | Critical | Interrupted session rendered as `OK` | Render `INTERRUPTED`, retain exit 2 and partial-session state | 0.6 | 0 | **done 2026-07-18** |
| PR-CRIT-003 | Critical | Session completeness is not modeled | Qualify incomplete runs even when nothing failed; state stop reason and executed/collected | 0.6 | 0 | **done 2026-07-18** |
| PR-FID-001 | High | Deduplication drops later occurrence context | 0.6: every occurrence retains node ID, phase, and location. Post: full deltas and per-occurrence references | 0.6 | 0 | **done 2026-07-18** |
| PR-FID-002 | High | XML-like output is malformed by unescaped values | Resolved by deleting XML output in favour of compact plain text | 0.6 | 0 | **done 2026-07-18** |
| PR-FID-003 | High | Warnings disappear from green runs | 0.6: warning count on the summary line. Post: grouped category/message/origin | 0.6 | 0 | **done 2026-07-18** |
| PR-FID-004 | High | Fingerprint is calculated after truncation | Fingerprint complete normalized evidence before presentation budgets | 0.6 | 0 | **done 2026-07-18** |
| PR-FID-005 | Medium | Xpass identities and reasons disappear | List every xpass with node ID and reason; respect pytest strictness for exit behavior | 0.6 | 0 | **done 2026-07-18** |
| PR-FID-007 | Medium | Displayed traceback function is not a function name | Capture a real function identifier or label the field accurately | 0.6 | 0 | **done 2026-07-18** |
| PR-FID-008 | High | Reporter bucket counts are treated as logical test outcomes | 0.6: aggregate by node ID and report the failing phase. Post: full logical/attempt/subtest model | 0.6 | 0 | **done 2026-07-18** |
| PR-FID-011 | High | Omitted detail is only recoverable by re-running pytest | Write the complete agent-format report to `.pytest_cache/receptor/last-run.txt` and reference it | 0.6 | 0 | **done 2026-07-18** |
| PR-FID-006 | Medium | External traceback origins are removed | Preserve local boundary, decisive external origin, cause chain, and full artifact | post | 1 | open |
| PR-FID-009 | High | Fixed character truncation is not an auditable information budget | Configurable semantic budgets reporting original size, retained size, hash, omissions, and reference | post | 2 | open |
| PR-FID-010 | Medium | Skip and xfail reasons are not grouped or trackable | Group skip/xfail by reason; support an optional baseline to expose drift | post | 2 | open |
| PR-UX-001 | Medium | Adaptive hints can prescribe the wrong dependency mutation | Delete installation hints; replace with the exact rerun command | 0.6 | 0 | **done 2026-07-18** |
| PR-UX-002 | High | Every failure is rendered in full regardless of root-cause count | Progressive disclosure: full detail for the first three root causes, one line for the rest | 0.6 | 0 | **done 2026-07-18** |
| PR-UX-003 | Medium | Output provides no rerun target | Emit a literal rerun command per failure group that actually selects it | 0.6 | 0 | **done 2026-07-18** |
| PR-ARCH-003 | High | Renderer replaces the private `TerminalReporter` | Rebuild on public hooks with the standard reporter silenced through public options | 0.6 | 0 | **done 2026-07-18** |
| PR-ARCH-001 | High | Renderer formats reporter text instead of owning structured evidence | Normalized event model populated from pytest hooks; stop inferring exception type from formatted text | post | 1 | open |
| PR-ARCH-002 | Medium | No neutral extension-event protocol for third-party producers | Namespaced extension events, correlation service, unknown-namespace preservation, dummy-producer tests | post | 2 | open (gated) |
| PR-API-001 | Medium | No programmatic consumer interface | Supported artifact reader and session/event API | post | 2 | open |
| PR-OPS-001 | High | Python range rejects 3.13 patch releases | Change to `>=3.11,<3.14`; test representative versions | 0.6 | 0 | **done 2026-07-18** |
| PR-OPS-002 | Medium | Heartbeat is not periodic | Delete the heartbeat feature and its claims; revisit only with lifecycle evidence | 0.6 | 0 | **done 2026-07-18** |
| PR-OPS-003 | High | Suppressed human output is retained in memory unconditionally | Resolved by the public-hook architecture: no terminal-writer capture exists | 0.6 | 0 | **done 2026-07-18** |
| PR-OPS-006 | Medium | Wall clock drives elapsed timing | Use `time.monotonic()` for elapsed time | 0.6 | 0 | **done 2026-07-18** |
| PR-OPS-007 | Medium | Human dump may omit direct plugin/process output | Resolved by the architecture change; document the dump boundary that remains | 0.6 | 0 | **done 2026-07-18** |
| PR-OPS-008 | High | Receptor internal failure has no explicit degraded outcome | `RECEPTOR_ERROR` plus standard pytest output, preserving pytest's exit status | 0.6 | 0 | **done 2026-07-18** |
| PR-OPS-009 | Medium | `--receptor=human` is not a true passthrough | Register nothing in human mode; output must be byte-identical to pytest without the plugin | 0.6 | 0 | **done 2026-07-18** |
| PR-OPS-010 | Medium | `CiTerminalReporter` duplicates the LLM renderer | Delete the duplicated class; keep `--receptor=ci` as a profile of the single renderer with CI-appropriate defaults | 0.6 | 0 | **done 2026-07-18** |
| PR-OPS-004 | Medium | Reporter depends on private pytest internals | Residual private usage isolated in one version-tested adapter | post | 3 | open |
| PR-OPS-005 | Medium | Output-channel authority is undefined | Define stdout/stderr/artifact contract and degradation behavior | post | 1 | open |
| PR-SEC-001 | High | Test text can inject control markup or agent instructions | 0.6: strip ANSI and control characters, structural safety, untrusted-data delimitation. Post: hint provenance and confidence | 0.6 | 0 | **done 2026-07-18** |
| PR-SEC-002 | High | Artifacts may persist secrets without policy | Permissions, redaction, retention, size, path, and no-upload contracts | post | 1 | open |
| PR-DOC-001 | Medium | Documentation overstates XML, heartbeat, dump, and warning behavior | Align every public claim with executable evidence | 0.6 | 0 | open |
| PR-DOC-002 | Low | Editorial debt in public documents | Fix mixed-language terms, `Dumping` where deduplication is meant, `Formated`, and the `file://` license link | 0.6 | 0 | open |
| PR-DOC-003 | Medium | `draft_ideas.md` presented an unimplemented design as current | Preserve it as history with supersession notes rather than deleting it | 0.6 | 0 | **done 2026-07-18** |
| PR-DOC-004 | Medium | The term "lossless" overstates achievable durability | Narrow the claim to evidence-preserving during normal pytest lifecycle operation | 0.6 | 0 | open |
| PR-REL-001 | Medium | No compatibility CI exists | 0.6: Python 3.11 and 3.13 against pytest 8 and 9. Post: full matrix with xdist | 0.6 | 0 | open |
| PR-REL-002 | Medium | Benchmarks use a dishonest baseline and measure only compression | Baseline `pytest -q --no-header --tb=short`; record environment; measure diagnostic sufficiency | 0.6 | 0 | open |
| PR-REL-003 | Low | Benchmark module fails collection without the optional tokenizer | Skip explicitly when `tiktoken` is absent | 0.6 | 0 | open |
| PR-REL-004 | Low | Package metadata is incomplete and the version is duplicated | Version centralized in `__init__.py` via `[tool.hatch.version]`, with a recipe-drift regression. Remaining: license expression, authors, URLs, classifiers | post | 3 | in progress |
| PR-REL-005 | Medium | No differential parity harness against pytest and JUnit | Compare semantic models automatically across the supported matrix | post | 3 | open |
| PR-REL-006 | Medium | No dogfooding program is scheduled | Execute the MolSysMT shadow, agent-facing, and CI stages | post | 4 | open |

**0.6 blockers: 31. Post-0.6: 12.** Most 0.6 items are corrections or deletions;
only PR-UX-002, PR-UX-003, and PR-FID-011 add behavior.

## Evidence and provenance

| ID | Confirmed evidence | Source |
| --- | --- | --- |
| PR-CRIT-001 | pytest exit 5 produced `OK: 0 passed` | AUD |
| PR-CRIT-002 | `KeyboardInterrupt`, exit 2, produced `OK: 0 passed` | AUD |
| PR-CRIT-003 | `-x`, `--maxfail`, timeouts, and worker loss can leave most collected tests unexecuted with no completeness signal | AUD, ARCH, TRUST |
| PR-FID-001 | Equal messages with different logs retained only the first log | AUD |
| PR-FID-002 | `<` and `&` in messages/captures broke structure | AUD |
| PR-FID-003 | Runtime warning absent from LLM result | AUD |
| PR-FID-004 | Code order is compress, normalize, group | AUD |
| PR-FID-005 | Mixed-state probe returned counts only | AUD |
| PR-FID-006 | Local-only filtering is destructive | AUD |
| PR-FID-007 | Probe rendered `in ValueError` | AUD |
| PR-FID-008 | Summaries derive from `TerminalReporter.stats`, which counts reports, not logical tests | AUD, ARCH |
| PR-FID-009 | Fixed 1500-character cut keeps the first 1000 and last 400 characters with no omission record | AUD, ARCH |
| PR-FID-010 | Skip and xfail reasons and node IDs are dropped from summaries | AUD |
| PR-FID-011 | Any escape hatch requiring `--receptor-full` costs a full suite re-execution, the dominant term in the cost model | SCOPE |
| PR-UX-001 | Import name is converted directly into an install command | AUD, ARCH |
| PR-UX-002 | A 38-failure cascade renders every occurrence although an agent fixes one cause at a time | SCOPE |
| PR-UX-003 | The agent must construct its own rerun selector from node IDs | SCOPE, ARCH |
| PR-ARCH-001 | Exception type is inferred by parsing `longrepr` text line prefixes | AUD, ARCH, OLD |
| PR-ARCH-002 | SMonitor and a future policy package need correlated namespaced events | SMON |
| PR-ARCH-003 | `pytest_configure` unregisters `terminalreporter` and registers a `_pytest.terminal.TerminalReporter` subclass | AUD, SCOPE |
| PR-API-001 | The receptor is CLI-only; consumers would have to reparse stdout | AUD, ARCH |
| PR-OPS-001 | `<=3.13` rejected 3.13.1 through 3.13.14, including the active development environment; fixed in `pyproject.toml` and the conda recipe, with the regression in `tests/test_packaging.py` | AUD, ARCH |
| PR-OPS-002 | A single six-second test emitted no heartbeat | AUD |
| PR-OPS-003 | `captured_lines` receives every terminal write | AUD, ARCH |
| PR-OPS-004 | Replaces `_pytest.terminal.TerminalReporter` | AUD |
| PR-OPS-005 | Other plugins and early errors can bypass the replacement reporter | AUD |
| PR-OPS-006 | `time.time()` used for durations and heartbeat | AUD |
| PR-OPS-007 | Only dummy terminal-writer traffic is captured | AUD |
| PR-OPS-008 | No defined behavior when the renderer or artifact writer raises | ARCH, TRUST, SCOPE |
| PR-OPS-009 | Human mode still loads the plugin; byte-identity with plain pytest is untested | SCOPE |
| PR-OPS-010 | `CiTerminalReporter` duplicates slow-test, summary, and counter logic from `LlmTerminalReporter` | SCOPE |
| PR-SEC-001 | Raw captured text is inserted into LLM output | AUD, ARCH, TRUST |
| PR-SEC-002 | Captured logs and tracebacks are written as plain files | AUD, ARCH, TRUST |
| PR-DOC-001 | Runtime probes contradict published claims | AUD |
| PR-DOC-002 | `Sanitización`, `Volcado`, `Dumping`, `Formated`, and a `file://` license link appear in public documents | AUD |
| PR-DOC-003 | `draft_ideas.md` described extracting raw `ExceptionInfo` attributes, which was never implemented; moved verbatim into `superseded_proposals.md` | AUD, OLD |
| PR-DOC-004 | No plugin can guarantee complete evidence after `SIGKILL` or host loss | AUD, ARCH |
| PR-REL-001 | Repository has no test CI workflow, only documentation deployment | AUD, ARCH, TRUST |
| PR-REL-002 | The published table compares against default pytest; against `-q --no-header` the green case is roughly 12 tokens versus 9, not an 87.88% saving | AUD, SCOPE |
| PR-REL-003 | `tests/test_token_savings.py` could not be collected without `tiktoken` | AUD |
| PR-REL-004 | `pyproject.toml` and `devtools/conda-build/meta.yaml` declared 0.1.0 and 0.1.1; now single-sourced and guarded by `tests/test_packaging.py` | ARCH |
| PR-REL-005 | Semantic parity with pytest and JUnit is asserted but never measured | TRUST |
| PR-REL-006 | MolSysMT is identified as the proving ground but no stage is scheduled | TRUST |

## Split-release decomposition

Findings delivered partly in 0.6 and completed later. None may be closed until
its post-0.6 entry is satisfied or explicitly accepted as a limitation.

| ID | 0.6 deliverable | Post-0.6 deliverable |
| --- | --- | --- |
| PR-CRIT-003 | Never render an incomplete run as a clean pass; state stop reason and executed/collected | Full collected/executed/deselected/not-executed model from the event collector |
| PR-FID-001 | Node ID, phase, and location per occurrence within the current grouping | Reversible groups with occurrence deltas and per-occurrence artifact references |
| PR-FID-003 | Warning count on the summary line | Grouping by category, message, and origin, with baseline drift |
| PR-FID-008 | Aggregate by node ID and report the failing phase | Separate logical tests, attempts, phases, subtests, and reruns |
| PR-OPS-002 | Delete the feature and every claim about it | Reconsider a monotonic watchdog only with lifecycle tests |
| PR-OPS-010 | Delete the duplicated class; `ci` becomes a profile that expands all groups and omits the on-disk reference | Consider CI-specific annotation syntax for file and line if real use justifies it |
| PR-SEC-001 | Strip ANSI and control characters; delimit untrusted data | Hint provenance and confidence; extension payload trust classification |
| PR-REL-001 | Python 3.11 and 3.13 against pytest 8 and 9 | Full matrix with xdist, coverage, JUnit, reruns, subtests |

## Resolved contradictions and decisions

| Item | Resolution |
| --- | --- |
| PR-FID-005 was Phase 2 while Phase 0 required xpass identity | Split. PR-FID-005 covers xpass only and is a 0.6 blocker. Skip and xfail grouping became PR-FID-010, post-0.6. |
| Phases written as `0/1`, `0/2`, `0/3`, `1/2` were not actionable | Replaced by the split-release decomposition table. |
| `draft_ideas.md` read as a current specification but predated the audit | Moved verbatim into `superseded_proposals.md` with per-section supersession notes. Sections 1 and 2 remain accurate motivation; section 3 is dead. |
| ARCH uses "lossless" while AUD rejects that guarantee | PR-DOC-004 narrows it to evidence-preserving during normal lifecycle operation. |
| XML was to be fixed by escaping | XML is deleted instead. Its premise, that XML boundaries cost a transformer less attention noise, is unevidenced, and XML costs more tokens than plain text for the same content. Resolves PR-FID-002 by construction. |
| Installation hints were to be made conservative | Deleted. Import names are not distribution names, and a conservative hint is close to useless. Replaced by the exact rerun command (PR-UX-003). |
| `--receptor=ci` was to be deleted | Reversed 2026-07-18. The duplicated `CiTerminalReporter` is deleted, but the mode survives as a renderer profile. In CI the runner is destroyed at job end, so the on-disk full report is unreachable and progressive disclosure cannot be the default there. That is a substantive difference in consumer, not cosmetics. |
| The heartbeat was to become a watchdog | Deleted. CI runners own their own timeouts; a threaded watchdog tested against xdist and interruption is cost without a matching problem. |
| `--receptor-full` versus `--receptor=human` | Kept as distinct. Human is complete but redundant (source echo, headers, ANSI, duplicated summary); `--receptor-full` is complete in agent format and still deduplicated. |
| How to recover omitted detail | Not by re-running pytest. The complete report is written to `.pytest_cache/receptor/last-run.txt` during the run, so recovery is a file read (PR-FID-011). |
| Evidence artifact format for 0.6 | Plain text, not JSONL. The versioned schema is post-0.6 and should first be checked against `pytest-reportlog`, which already streams per-report JSONL and may make a bespoke schema unnecessary. |
| Dogfooding was scheduled in Phase 4 | Stage A shadow comparison should begin immediately after 0.6, since it is the only way to learn whether compact output is sufficient. |

## Current-to-target behavior matrix

| Scenario | Current rendering | Target rendering |
| --- | --- | --- |
| Clean green suite | One-line `OK` | `PASS exit=0` with counts and duration |
| Green with warnings | `OK`, warning evidence absent | `PASS` with warning count; grouped detail post-0.6 |
| Green but incomplete | `OK` with no completeness signal | Qualified by completeness and stop reason |
| No tests | `OK: 0 passed` | `NO_TESTS exit=5` |
| Keyboard interrupt | `OK: 0 passed` | `INTERRUPTED exit=2`, executed/collected counts |
| Collection error | Failure group with text-parsed evidence | Distinct collection outcome with structured location and incomplete-session state |
| Homogeneous fixture cascade | Every occurrence rendered, first context only | One group, full detail, all occurrence node IDs retained |
| Many distinct causes | All rendered in full | First three in full, remainder one line each, full report on disk |
| Equal messages at different call sites | One group, later context lost | Separate groups or one group retaining every call site |
| Huge diff | Fixed middle truncation | 0.6: truncate after fingerprinting, with the full text on disk. Post: semantic budgets |
| XML metacharacters | Malformed output | No XML; ANSI and control characters stripped |
| Long-running test in CI | No periodic heartbeat | Feature removed and claims withdrawn |
| Missing import | Generic install command | Environment diagnosis and the exact rerun command |
| Renderer or artifact failure | Undefined | `RECEPTOR_ERROR` plus standard pytest output, exit status preserved |
| `--receptor=human` | Plugin registered, reporter untouched | Plugin registers nothing; byte-identical to plain pytest |
| xdist failure | Compact result without worker traceability | Post-0.6: worker, sequence, attempt, and occurrence evidence |
| Third-party diagnostic event | Not represented | Post-0.6: namespaced extension record preserved |

## Release 0.6: correctness and truth floor

Acceptance criteria and the work sequence live in SCOPE. This section records
only the mapping from scope items to identifiers.

| SCOPE item | Identifiers |
| --- | --- |
| Delete XML, hints, heartbeat, duplicated CI reporter | PR-FID-002, PR-UX-001, PR-OPS-002, PR-OPS-010 |
| Rebuild on public hooks | PR-ARCH-003, PR-OPS-003, PR-OPS-007, PR-OPS-009 |
| Outcome classification and completeness | PR-CRIT-001, PR-CRIT-002, PR-CRIT-003, PR-FID-008 |
| Visibility of warnings and xpasses | PR-FID-003, PR-FID-005 |
| Grouping, progressive disclosure, on-disk report | PR-UX-002, PR-UX-003, PR-FID-001, PR-FID-004, PR-FID-011 |
| Safety of untrusted text | PR-SEC-001 |
| Reliability floor | PR-OPS-008 |
| Correctness details | PR-OPS-006, PR-FID-007, PR-OPS-001 |
| Honest benchmark | PR-REL-002, PR-REL-003 |
| Documentation | PR-DOC-001, PR-DOC-002, PR-DOC-003, PR-DOC-004 |
| Compatibility CI | PR-REL-001 |

## Architecture decision gates

Post-0.6 work must not begin until these are recorded.

| Decision | Options | Recommended initial choice |
| --- | --- | --- |
| Canonical artifact | Reuse `pytest-reportlog`, bespoke JSONL, SQLite | Evaluate `pytest-reportlog` first; build bespoke only if it proves insufficient |
| Terminal syntax | Compact text, XML, JSON | Compact deterministic text — decided for 0.6 |
| Artifact default | Always, red only, opt-in | Plain-text report always in 0.6; structured artifact opt-in later |
| Warning policy | Hide, count, grouped, full | Count in 0.6; grouped with configurable baseline later |
| Xpass policy | Count only, list, fail | Always list; respect pytest strictness — decided for 0.6 |
| Heartbeat | Watchdog, lifecycle only, none | None — decided for 0.6 |
| Redaction | None, built-in patterns, plugin protocol | Built-in conservative patterns plus project protocol and audit metadata |
| Group fingerprint | Message only, callsite-aware, configurable | Versioned callsite- and cause-aware fingerprint over complete evidence |
| API stability | CLI only, artifact reader, event API | CLI only in 0.6; stable artifact reader first afterwards |
| Private pytest use | Direct throughout, isolated adapter | Public hooks in 0.6; one tested adapter for any residual need |
| Completeness model | Exit status only, explicit session record | Explicit record with stop reason and not-executed count |
| Extension mechanism | Hook spec, stash service object, artifact linking | Decide with a dummy producer before any SMonitor work (PR-ARCH-002) |
| Delta mode storage | pytest cache, bespoke state, none | pytest cache, targeted at 1.1 |

## Explicit non-goals

- Replacing pytest's execution engine.
- Reimplementing every pytest terminal feature.
- Automatically fixing failures or installing dependencies.
- Guaranteeing evidence after `SIGKILL`, host loss, or unrecoverable storage
  failure.
- Uploading diagnostics or telemetry without explicit user action.
- Making every third-party plugin structurally compatible in 0.6.
- Treating token savings as sufficient proof of diagnostic quality.
- Freezing a public event API before real consumer evidence exists.
- Depending on SMonitor or MolSysSuite in any direction.
- Creating `pytest-molsyssuite` before its extraction gate is satisfied.
- Upstreaming `--receptor` into pytest core as a 0.6 objective.

## Degradation contracts

The receptor must fail transparently (PR-OPS-008):

- If the renderer fails, emit `RECEPTOR_ERROR`, then pytest's standard output,
  preserving pytest's exit status. Never emit success by default.
- If the on-disk report cannot be written, preserve the exit status and note the
  failure in one line.
- If an unknown report or event is received, represent it explicitly rather than
  dropping it silently.
- If output is truncated, state where the complete text lives.
- Post-0.6: if the artifact ends without a final session record, readers classify
  it as incomplete; if redaction fails, withhold the affected field.

## Required regression corpus

| Release | Scenarios |
| --- | --- |
| 0.6 | every pytest exit status; no tests collected; `KeyboardInterrupt`; internal errors; multiple collection errors; setup/call/teardown failures; fixture finalization errors; warnings on green and red runs; skip, xfail, xpass, strict xpass; arbitrary Unicode, ANSI escapes, and control characters; identical messages with different locations and captures; fingerprint collisions from truncated content; prompt-injection-shaped captured text; renderer exception producing `RECEPTOR_ERROR`; human mode byte-identity; on-disk report completeness; supported Python patch releases; pytest 8 and 9 |
| post | chained exceptions and exception groups; report counts versus logical outcomes; direct stdout/stderr writes from other plugins; broken pipes and unwritable artifacts; bounded memory on large suites; truncated diffs with artifact references; secret redaction and permissions; disk exhaustion; extension-event round trip; xdist worker identity, crash, and restart; reruns and subtests; reporter coexistence with coverage, JUnit, and live logging |

## Evidence required for post-0.6 phases

### Phase 1: collector and artifact

- Evaluation of `pytest-reportlog` before defining any bespoke schema.
- Schema review with examples for session, phase, exception, warning, capture,
  and opaque plugin events.
- Serial and xdist event-order experiments.
- Prototype proving count parity with pytest without copying reporter buckets.
- Streaming prototype with incomplete-tail detection.
- Peak-memory comparison against 0.6.

### Phase 2: grouping, budgets, security, and API

- Collision corpus for normalization and fingerprints.
- Secret and prompt-injection threat-model fixtures.
- Semantic truncation prototypes for assertion diffs and captured logs.
- Artifact reader API exercised by at least one real agent or CI consumer.
- Warning and skip baseline experiment on a changing repository.
- Neutral extension protocol validated with a dummy producer unrelated to
  SMonitor, covering the ten validation scenarios in SMON.

### Phase 3: ecosystem support

- Full Python and pytest compatibility CI.
- xdist worker crash and restart cases.
- Rerun and subtest integrations.
- Reporter-coexistence tests with coverage, JUnit, and live logging.
- Differential parity harness against the standard reporter and JUnit.
- Support table generated from passing integration evidence.

### Phase 4: evidence-based optimization and adoption

- A real failure corpus with sensitive data removed.
- Multiple tokenizer families, without coupling correctness to one.
- Diagnostic sufficiency measurement: additional pytest invocations, additional
  file reads, availability of the failing phase and rerun target.
- Budgets tuned from evidence.
- Reproducible benchmark metadata and commands.
- MolSysMT dogfooding stages, beginning immediately after 0.6.

## Adoption gates

Trust levels are defined in TRUST. Their dependency on this register:

| Gate | Requires |
| --- | --- |
| Gate 1: safe experimental use | All Critical findings closed; no nonzero exit renders as success |
| Gate 2: routine development use | 0.6 shipped: every 0.6 blocker closed or accepted, with compatibility CI active |
| Gate 3: agent-facing default | Phase 2 complete; sustained MolSysMT shadow parity; security suite passing |
| Gate 4: CI authority | Phase 3 complete; failure, interruption, collection, maxfail, and worker-crash behavior proven |

## Completion definition

The audit program is complete only when:

- every finding is fixed, explicitly accepted as a documented limitation, or
  rejected with evidence;
- every Critical and High item has an executable regression;
- public claims match tested behavior;
- the behavior matrix has no unexplained divergence;
- supported version claims are exercised in CI;
- the output is demonstrably sufficient to identify the root cause and exact
  rerun target for the curated failure corpus;
- omitted evidence is recoverable without re-executing the suite;
- semantic parity with pytest and JUnit is measured, not assumed;
- no proposal in any devguide document lacks an identifier here.

## Revision log

**2026-07-18e** — Implemented the 0.6 renderer.

Rewrote the plugin on public hooks. Closed 23 further findings; the remaining
0.6 work is documentation (PR-DOC-001/002/004), the benchmark rebaseline
(PR-REL-002/003), and compatibility CI (PR-REL-001).

Measured on a 38-failure cascade over 128 tests, against the honest baseline
`pytest -q --no-header --tb=short`: 2863 tokens to 101, a 96.5% reduction.
Against `pytest -q --tb=line`, which loses the diff entirely, 1989 to 101.

**2026-07-18d** — Reversed the decision to delete `--receptor=ci` (PR-OPS-010).

The duplicated `CiTerminalReporter` class is still deleted, but the mode survives
as a profile of the single renderer. CI runners are destroyed at job end, so the
on-disk full report is unreachable there and progressive disclosure cannot be the
CI default. That makes `ci` a genuinely different consumer rather than a
cosmetic variant, and keeping it avoids withdrawing a documented feature.

**2026-07-18c** — Renamed the target release from 1.0 to 0.6 and reorganized the
devguide.

The output format is this plugin's only public API, and the plan explicitly uses
dogfooding to discover whether that format is sufficient. Freezing it at 1.0
before that evidence exists would force a 2.0 for any correction. 0.6 maps to
Level 1 in TRUST; 1.0 now means the format-frozen release at Level 2.

Added: `devguide/README.md` as an index, `superseded_proposals.md` accumulating
rejected proposals with their reasons and the original development guide
verbatim. Status headers added to ARCH, AUD, TRUST, and ISSUE.

Closed: PR-DOC-003. In progress: PR-REL-004 (version centralized).

**2026-07-18b** — Reorganized around the accepted 0.6 scope (`scope_0.6.md`).

Added: PR-FID-011, PR-UX-002, PR-UX-003, PR-ARCH-003, PR-OPS-009, PR-OPS-010.
Added the `Release` column, the split-release decomposition, and the scope-item
mapping.

Changed by decision: PR-FID-002, PR-UX-001, and PR-OPS-002 are now resolved by
deletion rather than repair. PR-OPS-003 and PR-OPS-007 are resolved
by the architecture change. PR-REL-002 now requires a corrected baseline. The
canonical-artifact gate must evaluate `pytest-reportlog` first.

**2026-07-18a** — Completeness pass against all six devguide documents.

Added: PR-CRIT-003, PR-FID-008, PR-FID-009, PR-FID-010, PR-ARCH-001,
PR-ARCH-002, PR-API-001, PR-OPS-008, PR-DOC-002, PR-DOC-003, PR-DOC-004,
PR-REL-002, PR-REL-003, PR-REL-004, PR-REL-005, PR-REL-006.

Changed: PR-FID-005 narrowed to xpass; split phases decomposed; status column,
provenance table, identifier prefixes, regression corpus, Phase 4, and adoption
gates added.

Closed: PR-OPS-001.
