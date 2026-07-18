# Salvage review: the `event-model-v0.5` branch

**Recorded:** 2026-07-18

**Source:** branch `event-model-v0.5`, sixteen commits that were on `origin/main`
until 0.6 replaced them. Nothing was deleted; the branch is pushed and permanent.

**Status:** triaged 2026-07-18. All three recommendations below were adopted;
see the register revision log. This file is kept as the record of what the
branch contained and why the rest was left.

## Context

Two implementations of this project were developed in parallel from the same
audit. That branch worked top-down through the architecture proposal and reached
a claimed v0.5.0 covering Phases 0-4: a lossless event model, a JSONL artifact,
an artifact reader, an SMonitor bridge, a CI watchdog, and semantic budgets.
0.6 worked bottom-up from the correctness floor and deliberately deferred all of
it.

The two are architecturally incompatible — subclassed `TerminalReporter` versus
public hooks, XML versus plain text — so this is a salvage review, not a merge.
`plugin.py` differs by roughly a thousand lines and there is no useful common
ancestor for that file.

Some of the reasoning behind those decisions is recorded in
[`../superseded_proposals.md`](../superseded_proposals.md); the branch is
evidence that the alternatives were built rather than only imagined.

## Worth taking

### 1. Intelligent traceback pruning — **adopted** (PR-FID-006)

This is the strongest thing on the branch and it closes `PR-FID-006`, which 0.6
deferred. The algorithm selects, from the raw frame list:

- the initiating local frame;
- the final local frame;
- the terminal (crash) frame, always;
- every local-to-external boundary;

and renders the gaps as `[... external/internal frames omitted ...]`, labelling
each retained frame `(local)` or `(external)`.

That is exactly what the audit asked for and what 0.6 does not do. 0.6 drops
external frames entirely, which is the destructive behaviour the audit
criticized: when a failure originates inside NumPy, OpenMM, or a serializer, the
decisive frame is external and 0.6 currently hides it.

Adapting it is not a copy-paste. It assumes the branch's frame dictionaries and
its `at path:line (local) -> snippet` format; 0.6 renders a single compact
`frames: a -> b -> c` line. The selection logic is the valuable part.

### 2. Multi-tokenizer benchmarking — **adopted**, the idea and not the file

`devtools/benchmark_tokenizers.py` measures four tokenizer families —
`cl100k_base`, `o200k_base`, `p50k_base`, `r50k_base` — which is what Phase 4 of
the architecture proposal asks for, so that a savings claim is not an artifact of
one vendor's tokenizer. Worth folding into
`devtools/benchmarks/run_benchmarks.py` as an extra axis.

**Do not take its numbers.** `devtools/benchmark_results.md` compares against
pytest's default output and labels the column "Human Tokens", which is the
dishonest baseline `PR-REL-002` exists to correct. Its green-suite figure of
66.67% is measured against a banner and a progress bar.

Its scenarios are also small — ten passing tests, one failing test — and so miss
the cascade case where the receptor actually earns its keep.

### 3. Artifact hardening — **adopted** for the report we already write

Restrictive permissions (`0o600`) and symlink handling on artifact creation.
0.6 writes a plain-text report with default permissions, which is a real gap the
moment captured output contains credentials or private paths. The branch has a
worked implementation to start from when `PR-SEC-002` is scheduled.

## Reference only, not for adoption

- **`collector.py`, `events.py`, `reader.py`** (732 lines). A complete event
  model, JSONL writer, and reader. This is post-0.6 work, and the decision
  gate for it says `pytest-reportlog` must be evaluated first — it already
  streams per-report JSONL and may make a bespoke schema unnecessary. Valuable
  as a worked example of the schema shape when that gate is resolved.
- **SMonitor bridge and extension hooks.** Blocked by `PR-ARCH-002`: the
  extension protocol must be designed against a neutral dummy producer before
  any SMonitor-specific code exists, or the protocol will encode SMonitor's
  assumptions. The branch implemented the bridge before the protocol.
- **Configurable project-specific normalizers.** Wanted eventually
  (`PR-FID-009` territory); no reason to take it before there is evidence from a
  real suite about which values need normalizing.
- **CI error annotations and completeness reporting.** Plausible, but 0.6
  deliberately deferred CI-specific syntax "until someone runs it in anger". The
  MolSysMT pilot is what should decide this.

## Recommend rejecting

- **The monotonic CI watchdog thread.** 0.6 removed the heartbeat rather than
  implementing it: CI runners own their own timeouts, and a background thread
  that must be correct under xdist, hanging fixtures, interruption, and shutdown
  is cost without a matching problem. See `superseded_proposals.md` entry 3.
- **`devguide/todo_list.md`.** A parallel work queue organized by architecture
  phase, overlapping the action register. Two registries is how items get lost.
  Its identifiers match ours, and a scan found nothing it tracks that the
  register does not, so there is nothing to merge — but it should not be
  reintroduced alongside the register.

## What was done

All three were taken, in 0.6.

Item 1 was adapted rather than copied. The branch kept only the first and last
local frames; this keeps *every* local frame, because those are the code a
reader can actually change, and elides only runs of external frames. External
paths are shortened to their last three components so the library is
recognizable without spending tokens on an absolute path.

Item 2 confirmed the headline is robust: across `cl100k_base`, `o200k_base`,
`p50k_base`, and `r50k_base` the cascade saving stays between -96.8% and -97.0%.

Item 3 covers permissions only. Redaction is still absent, so `PR-SEC-002`
remains open.

The reference-only and rejected sections below stand.
