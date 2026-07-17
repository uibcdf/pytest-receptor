# Audit Action Register

**Recorded:** 2026-07-17

**Source documents:**

- `critical_audit_2026-07-17.md`
- `evidence_preserving_architecture_proposal.md`

## Purpose

This register converts the critical audit into an ordered, testable work queue.
It does not declare every proposed architectural feature accepted. Phase 0
items are correctness and release floors; later phases require explicit design
decisions before implementation.

## Severity definitions

| Severity | Meaning |
| --- | --- |
| Critical | Can report an unsuccessful or incomplete pytest run as successful. |
| High | Can destroy decisive diagnostic evidence, break parseability, expose sensitive data, or prevent installation in a supported environment. |
| Medium | Reduces traceability, compatibility, scalability, or operational reliability. |
| Low | Documentation, polish, or optimization debt without immediate correctness impact. |

## Confirmed findings

| ID | Severity | Finding | Current evidence | Required outcome | Phase |
| --- | --- | --- | --- | --- | --- |
| PR-CRIT-001 | Critical | No-tests session rendered as `OK` | pytest exit 5 produced `OK: 0 passed` | Render `NO_TESTS`, retain exit 5, never emit success | 0 |
| PR-CRIT-002 | Critical | Interrupted session rendered as `OK` | `KeyboardInterrupt`, exit 2, produced `OK: 0 passed` | Render `INTERRUPTED`, retain exit 2 and partial-session state | 0 |
| PR-FID-001 | High | Deduplication drops later occurrence context | Equal messages with different logs retained only the first log | Preserve every occurrence location, phase, worker, captures, and traceback reference | 0/1 |
| PR-FID-002 | High | XML-like output is malformed by unescaped values | `<` and `&` in messages/captures broke structure | Use a real serializer and parse golden outputs | 0 |
| PR-FID-003 | High | Warnings disappear from green runs | Runtime warning absent from LLM result | Report warning count and grouped category/message/origin | 0 |
| PR-FID-004 | High | Fingerprint is calculated after truncation | Code order is compress, normalize, group | Fingerprint complete normalized evidence before presentation budgets | 0 |
| PR-FID-005 | Medium | Skip/xfail/xpass reasons and identities disappear | Mixed-state probe returned counts only | List xpass; group skip/xfail by reason; retain node IDs | 2 |
| PR-FID-006 | Medium | External traceback origins are removed | Local-only filtering is destructive | Preserve local boundary, decisive external origin, cause chain, and full artifact | 1 |
| PR-FID-007 | Medium | Displayed traceback function is not a function name | Probe rendered `in ValueError` | Capture a real function identifier or label the field accurately | 0 |
| PR-OPS-001 | High | Python range rejects 3.13 patch releases | `<=3.13` rejects 3.13.1 and 3.13.11 | Change to `>=3.11,<3.14`; test representative versions | 0 |
| PR-OPS-002 | Medium | Heartbeat is not periodic | A single six-second test emitted no heartbeat | Implement and test a watchdog or remove/rename the claim | 0/3 |
| PR-OPS-003 | High | Suppressed human output is retained in memory unconditionally | `captured_lines` receives every terminal write | Capture only when requested; stream or bound storage; benchmark memory | 0 |
| PR-OPS-004 | Medium | Reporter depends on private pytest internals | Replaces `_pytest.terminal.TerminalReporter` | Isolate compatibility adapter and test pytest 8/9 | 3 |
| PR-OPS-005 | Medium | Output-channel authority is undefined | Other plugins and early errors can bypass replacement reporter | Define stdout/stderr/artifact contract and degradation behavior | 1 |
| PR-OPS-006 | Medium | Wall clock drives elapsed timing | `time.time()` used for durations and heartbeat | Use `time.monotonic()` for elapsed time | 0 |
| PR-OPS-007 | Medium | Human dump may omit direct plugin/process output | Only dummy terminal-writer traffic is captured | Narrow documentation claim or prove complete capture | 0 |
| PR-SEC-001 | High | Test text can inject control markup or agent instructions | Raw captured text is inserted into LLM output | Enforce trust boundary, structural encoding, and untrusted-data labeling | 0/2 |
| PR-SEC-002 | High | Artifacts may persist secrets without policy | Captured logs and tracebacks are written as plain files | Add permissions, redaction, retention, size, path, and no-upload contracts | 1/2 |
| PR-UX-001 | Medium | Adaptive hints can prescribe the wrong dependency mutation | Import name is converted directly into install command | Prefer diagnosis and rerun guidance; make repair hints policy-backed | 0 |
| PR-DOC-001 | Medium | Documentation overstates XML, heartbeat, dump, and warning behavior | Runtime probes contradict published claims | Align every public claim with executable evidence | 0 |
| PR-REL-001 | Medium | No compatibility CI exists | Repository has no CI workflows | Test Python 3.11-3.13, pytest 8/9, serial and xdist | 3 |

## Current-to-target behavior matrix

| Scenario | Current rendering | Target rendering |
| --- | --- | --- |
| Clean green suite | One-line `OK` | Keep one-line `OK` with exit, collected/executed counts, duration, warnings=0 |
| Green with warnings | `OK`, warning evidence absent | Success with visible warning occurrence/group counts and evidence reference |
| No tests | `OK: 0 passed` | `NO_TESTS exit=5 complete=true` or policy-defined failure label |
| Keyboard interrupt | `OK: 0 passed` | `INTERRUPTED exit=2 complete=false`, executed/not-executed counts |
| Collection error | Failure group with text-parsed evidence | `COLLECTION_ERROR`, structured location/cause and incomplete-session state |
| Homogeneous fixture cascade | Compact group, first occurrence context only | Reversible group with representative evidence and all occurrence deltas |
| Equal messages at different call sites | One group, later context lost | Separate groups or one group retaining every differing call site |
| Huge diff | Fixed middle truncation | Semantic budget plus sizes, hash, omissions, and artifact reference |
| XML metacharacters | Malformed output | Parseable serialization for arbitrary supported text |
| Single long-running test in CI | No periodic heartbeat | Tested watchdog or accurately documented absence of periodic output |
| xdist failure | Compact result without worker traceability | Worker, sequence, attempt, and complete occurrence evidence |
| Fail-fast/maxfail | Failure without explicit suite completeness | Failure plus collected, executed, not-executed, and stop reason |
| Missing import | Generic install command | Environment diagnosis, exact rerun, optional policy-backed hint |

## Phase 0: correctness and truth floor

Phase 0 should be implemented before advertising the plugin as a reliable LLM
or CI diagnostic receptor.

### Accepted scope

1. Derive session outcome from `pytest.ExitCode`.
2. Add no-tests and interruption regressions.
3. Produce structurally valid output.
4. Preserve warning and xpass visibility.
5. Preserve occurrence-level context during current grouping.
6. Fingerprint before truncation.
7. Stop unconditional human-output retention.
8. Use monotonic elapsed time.
9. Correct the Python version bound.
10. Make dependency hints conservative.
11. Correct public documentation claims.

### Phase 0 acceptance tests

- Exit codes 0 through 5 produce distinct correct top-level outcomes.
- No nonzero exit status contains an `OK` or CI-success label.
- XML, if retained, parses with messages, paths, and parameter IDs containing
  `<`, `>`, `&`, quotes, Unicode, and control-character edge cases.
- Two equal exception messages with different locations or captures retain both
  contexts.
- Two long messages differing only in the would-be truncated middle do not
  collide unless the complete normalized fingerprint intentionally matches.
- Green runs with warnings state warning counts and fingerprints.
- Xpasses identify the affected node and reason.
- LLM/CI mode without stats or dump does not accumulate suppressed human output.
- Python 3.11.x, 3.12.x, and 3.13.x satisfy package metadata; 3.14 does not.
- Documentation examples are generated from or checked against golden outputs.

## Architecture decision gates

Do not begin the full event-model migration until these decisions are recorded.

| Decision | Options | Recommended initial choice |
| --- | --- | --- |
| Canonical artifact | JSON, JSONL, SQLite | Versioned JSONL with optional external blobs |
| Terminal syntax | Compact text, XML, JSON | Compact deterministic text; JSONL remains canonical |
| Artifact default | Always, red only, opt-in | Automatic temporary artifact on unsuccessful runs; explicit path opt-in otherwise |
| Warning policy | Hide, count, grouped, full | Grouped by default; configurable known-warning baseline |
| Xpass policy | Count only, list, fail | Always list; respect pytest strictness for exit behavior |
| Heartbeat | Watchdog, lifecycle only, none | Remove current claim first; implement watchdog only with lifecycle tests |
| Redaction | None, built-in patterns, plugin protocol | Built-in conservative patterns plus project protocol and audit metadata |
| Group fingerprint | Message only, callsite-aware, configurable | Versioned callsite- and cause-aware fingerprint over complete evidence |
| API stability | CLI only, artifact reader, event API | Stable artifact reader first; renderer/event extension protocols later |
| Private pytest use | Direct throughout, isolated adapter | One small version-tested compatibility adapter |

## Explicit non-goals for the first reliable release

- Replacing pytest's execution engine.
- Reimplementing every pytest terminal feature.
- Automatically fixing failures or installing dependencies.
- Guaranteeing evidence after `SIGKILL`, host loss, or unrecoverable storage
  failure.
- Uploading diagnostics or telemetry without explicit user action.
- Making every third-party plugin structurally compatible in the first release.
- Treating token savings as sufficient proof of diagnostic quality.
- Freezing a broad public event API before real consumer evidence exists.

## Degradation contracts

The receptor must fail transparently:

- If artifact creation fails, preserve pytest's exit status and emit one clear
  receptor diagnostic through the safest available channel.
- If the selected renderer fails, fall back to a minimal outcome containing
  pytest exit status and the renderer exception; never emit success by default.
- If an unknown report or event is received, serialize it as an opaque event
  with provenance rather than dropping it silently.
- If output is truncated, state sizes, hashes, and the complete-event reference.
- If the artifact ends without a final session record, readers classify it as
  incomplete.
- If redaction fails, default to withholding the affected persisted field rather
  than writing a suspected secret unchanged under a false safety claim.

## Evidence required for later phases

### Phase 1: collector and artifact

- Schema review with examples for session, phase, exception, warning, capture,
  and opaque plugin events.
- Serial and xdist event-order experiments.
- Prototype proving count parity with pytest without replacing semantic totals
  with raw `TerminalReporter.stats` lengths.
- Streaming JSONL prototype with incomplete-tail detection.
- Peak-memory comparison against the current implementation.

### Phase 2: grouping, budgets, security, and API

- Collision corpus for normalization and fingerprints.
- Secret and prompt-injection threat-model fixtures.
- Semantic truncation prototypes for assertion diffs and captured logs.
- Artifact reader API exercised by at least one real agent or CI consumer.
- Warning/skip baseline experiment on a changing repository.

### Phase 3: ecosystem support

- Python and pytest compatibility CI.
- xdist worker crash and restart cases.
- rerun and subtest integrations.
- reporter-coexistence tests with coverage, JUnit, and live logging.
- explicit support table generated from passing integration evidence.

## Completion definition

The audit program is complete only when:

- every confirmed finding is fixed, explicitly accepted as a documented
  limitation, or rejected with evidence;
- every Critical and High item has an executable regression;
- public claims match tested behavior;
- the current and target behavior matrix has no unexplained divergence;
- supported version claims are exercised in CI;
- the LLM output is demonstrably sufficient to identify the root cause and
  exact rerun target for the curated failure corpus;
- complete evidence remains locally addressable whenever presentation is
  compressed during normal lifecycle operation.
