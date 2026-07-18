# Salvage review: the `event-model-v0.5` branch

**Recorded:** 2026-07-18

**Source:** branch `event-model-v0.5`, sixteen commits that were on `origin/main`
until 0.6 replaced them. Nothing was deleted; the branch is pushed and permanent.

**Status:** triaged 2026-07-18, over three passes. Five things were adopted; see
the register revision log. This file is the record of what the branch contained
and why the rest was left.

**A note on method.** The first two passes were done by reading commit messages
and grepping, and both concluded prematurely that the branch was exhausted. Both
were wrong: the second pass found redaction, which the first had reported as
absent, and the third found warning grouping and configurable normalizers. Only
the third pass actually read the files. If another branch ever needs salvaging,
read it.

## When this branch may be deleted

Not yet, and not on a date. Three conditions, all of which must hold:

1. **The `pytest-reportlog` gate is resolved.** The architecture decision gate
   requires evaluating it before any bespoke event schema is designed. Until
   that decision is recorded, `collector.py`, `events.py`, and `reader.py` are
   the only worked example of the schema shape this project has produced, and
   they are cited as reference material below.
2. **`PR-ARCH-002` is decided.** The extension protocol must be designed against
   a neutral dummy producer. Until then `hooks.py` and the SMonitor bridge are
   the only concrete proposal of what that protocol might look like, even though
   they cannot be adopted as they stand.
3. **`ci_error_annotations.md` is accepted or rejected.** Its implementation
   sketch was reconstructed from this branch; if it is accepted, the branch is
   where the original lives.

When all three hold, the branch has no remaining referent and can go.

Until then it costs one ref on the remote and nothing else. The asymmetry is
stark: keeping it costs nothing, and deleting it destroys the only copy of
roughly 2,400 lines. Three of the five things eventually salvaged from it were
found *after* it had been declared exhausted, which is the strongest argument
against trusting a judgement that it is finished.

Whoever deletes it should first check that no document still describes it as
preserved. This file does, twice.

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
- ~~**Configurable project-specific normalizers.**~~ **Adopted** on the third
  pass, and the reasoning that deferred it was backwards. Waiting for evidence
  about which values need normalizing, while withholding the mechanism that
  would produce that evidence, cannot terminate. Shipping `receptor_normalizers`
  turns the pilot into the experiment: what MolSysMT has to declare is the
  list that decides the built-in defaults.
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

## Also adopted, on later passes

- **Credential redaction** (second pass). Two keyword-anchored patterns. The
  first pass reported this as absent, which was simply wrong.
- **Warning grouping** (third pass). By category and normalized message, with
  count and origin — closing `PR-FID-003`, which 0.6 had left at a bare count.
  Ours reads `pytest_warning_recorded`, which hands over the real
  `WarningMessage`, so unlike the branch it does not parse category and origin
  back out of a formatted string.
- **Project normalizers** (third pass), as above.

## Confirmed as having nothing to take

On a proper read rather than a grep:

- **Exception extraction.** Theirs is *worse* than ours: it scans for `E   `
  line prefixes and misses a bare `assert 0`, which ours handles. No cause
  chains, despite the audit asking for them — so that part of `PR-FID-006`
  remains genuinely unbuilt on both sides.
- **Normalization.** The same two built-in patterns we already had.
- **The subtests and reruns test.** Asserts against `MagicMock` objects and
  their own collector API, so it never exercises `pytest-subtests` or
  `pytest-rerunfailures`. Not evidence of coexistence; those remain untested.

## What was done

The first three were taken in 0.6.

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
