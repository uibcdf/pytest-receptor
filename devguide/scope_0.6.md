# Scope for pytest-receptor 0.6

**Recorded:** 2026-07-18

**Status:** accepted scope. Supersedes the phase plan in
`evidence_preserving_architecture_proposal.md` for everything that ships in 0.6.
That proposal remains the reference for post-0.6 work.

**Operational queue:** `audit_action_register_2026-07-17.md`

## Goal

> A reliable, efficient pytest reporter for coding agents.

Version 0.6 does one thing: when pytest is executed by an agent such as Claude
Code or Codex, it produces the smallest output that still lets the agent fix the
failure without running pytest again. Everything else in the devguide is
post-0.6.

## The objective function

Token count alone is the wrong target. The cost to optimize is:

```text
cost = tokens(this output) + P(another run needed) x cost(that run)
```

The second term dominates. A 200-token report that leaves the agent guessing and
forces a second full suite execution is far more expensive than a 600-token
report that enables the fix immediately. This single equation decides every
trade-off below, and it is why `--tb=line -q` is a bad solution despite being
extremely compact.

Two consequences:

1. Compression is only a win if the compressed output remains sufficient.
2. Any escape hatch that requires re-running pytest is close to worthless.

## In scope

- One renderer with two output profiles, `--receptor=llm` and `--receptor=ci`.
- `--receptor=human` as a true passthrough: the plugin registers nothing and
  pytest behaves exactly as it does without the plugin installed.
- Compact deterministic plain-text output.
- Session outcome derived from `pytest.ExitCode`.
- Root-cause grouping with progressive disclosure.
- A plain-text full report on disk so omitted detail never costs a re-run.
- Safe degradation to standard pytest output if the renderer fails.
- An honest benchmark against a competently configured pytest.

## Out of scope for 0.6

Removed from the codebase:

- XML output syntax.
- Adaptive dependency-installation hints.
- The CI heartbeat.
- `CiTerminalReporter` as a separate reporter implementation. The `ci` mode
  survives as a profile of the single renderer; see "Output profiles".

Deferred, not started:

- Versioned JSONL artifact and event schema.
- Public artifact-reader API.
- Secret redaction protocol.
- Extension-event protocol for third-party diagnostic producers.
- Semantic truncation budgets.
- Warning, skip, and xfail baselines and drift detection.

## Design rules

1. **The first line is self-sufficient.** Verdict, exit code, and counts within
   roughly the first fifteen tokens, so the decisive fact survives any context
   truncation.
2. **Plain text, not XML.** Fewer tokens for the same content, and it removes the
   escaping defect by construction rather than fixing it.
3. **Never echo source code.** The agent already has the files. Keep the `E`
   assertion line and the diff, which are the only things that cannot be
   reconstructed by reading the file.
4. **A literal rerun command per group.** The agent's next action is almost
   always to re-run a subset; it should not have to construct the command.
5. **Deterministic output.** The same failure produces the same bytes, so a
   consumer can recognize an unchanged failure without re-reading it.

## Output profiles

One renderer, two profiles. A profile is a set of defaults, not a second
implementation. The separate `CiTerminalReporter` class is deleted; its 116 lines
duplicated the outcome counters, slow-test reporting, and summary construction of
the agent renderer.

The profiles differ for one substantive reason, not for cosmetics: **in CI there
is no second chance at the output.** The runner is destroyed when the job ends,
so `.pytest_cache/receptor/last-run.txt` does not exist by the time anyone reads
the log. Progressive disclosure depends on that file being reachable, so it must
not be the CI default.

| Behavior | `llm` | `ci` |
| --- | --- | --- |
| ANSI colour | off | off |
| Silent on success | yes | yes |
| Progressive disclosure | first three root causes | **all groups expanded** |
| On-disk report reference | shown | **not shown; the file will not survive** |
| Interactive progress output | none | none |

Everything else — outcome classification, grouping, fingerprinting, rerun
commands, the reliability floor — is shared. A defect fixed in one profile is
fixed in both.

`--receptor=ci` remains advertised in the README, so 0.6 does not remove a
documented feature. Whether CI deserves further divergence, such as GitHub
annotation syntax for file and line, is deferred until someone runs it in anger.

## Session outcomes

Every run renders exactly one top-level line, derived from `pytest.ExitCode`,
never from the absence of failure reports.

```text
PASS exit=0 · 128 tests · 4.2s
PASS exit=0 · 126 passed, 2 skipped · 4.2s · 3 warnings
FAIL exit=1 · 41 failed, 87 passed · 12.4s · 3 root causes
NO_TESTS exit=5
INTERRUPTED exit=2 · 12 of 128 executed
ERROR exit=3 · internal
USAGE_ERROR exit=4
RECEPTOR_ERROR · pytest exit=1 · <exception> · standard output follows
```

An incomplete run is qualified even when nothing failed, so a suite stopped by
`-x`, `--maxfail`, a timeout, or worker loss can never read as a clean pass.

Warnings and xpasses are reported as counts on the summary line. Their full
grouping and baseline handling is post-0.6; their visibility is not.

## Progressive disclosure

This is the main token saving in 0.6, and it is larger than any formatting
change.

When forty tests fail, an agent fixes one. Rendering all forty in full is the
real waste — but the unit that matters is the *occurrence*, not the cause.

The original rule here was "full detail for the first three root causes, one
line for the rest". It was wrong and was reversed on 2026-07-18. Grouping has
already collapsed the volume: a thousand failures become a handful of causes.
Withholding on top of that saves almost nothing and costs double when the
consumer reads the file back, because the file repeats what was already shown.
Measured at five distinct causes: 40 tokens saved, 200 lost on a single read.

The rule is now: **every root cause in full; occurrence lists truncated; the
complete report on disk but not load-bearing.** A pathological spread, more than
ten distinct causes, is the one case still summarized.

```text
FAIL exit=1 · 41 failed, 87 passed · 12.4s · 3 root causes

[1] TypeError · 38 tests · setup
    conftest.py:31 in build_topology
    E  TypeError: 'NoneType' object is not subscriptable
    tests/test_merge.py:12 -> conftest.py:31
    rerun: pytest tests/test_merge.py -q

[2] AssertionError · 2 tests · call
    tests/test_units.py:88
    E  assert 3.0 == 3.5
       + where 3.0 = convert(...)
    rerun: pytest tests/test_units.py::test_scale -q

[3] ImportError · 1 test · collection — tests/test_gpu.py
    full: .pytest_cache/receptor/last-run.txt
```

Thirty-eight identical failures collapse into eight lines without losing that
there were thirty-eight or which ones they were. Nothing is destroyed: the
complete report is on disk.

## Recovering omitted detail

Compression must be reversible, but reversing it must not cost a suite
execution.

During the run the complete report, in the same agent format, is written to
`.pytest_cache/receptor/last-run.txt` using `config.cache.mkdir("receptor")`,
which is public pytest API. The compact output references that path.

Recovering omitted evidence is therefore a file read, not a pytest invocation.

| Need | Action |
| --- | --- |
| Default working output | `--receptor=llm` |
| Detail omitted from the summary | read `.pytest_cache/receptor/last-run.txt` |
| Everything expanded on stdout, known in advance | `--receptor=llm --receptor-full` |
| Human inspection or plugin debugging | `--receptor=human` |

`--receptor-full` exists for consumers that know up front they want everything.
It is deliberately **not** advertised in the compact output; the file path is.
When the cache provider is disabled (`-p no:cacheprovider`) no file is written,
and the output falls back to naming the flag.

`--receptor-full` is not equivalent to `--receptor=human`. Human output is
complete but redundant: source echo, headers, progress, ANSI, and a duplicated
summary section. `--receptor-full` is complete in agent format, still grouped and
deduplicated, and materially cheaper.

## Architecture

0.6 does **not** replace `TerminalReporter`. The standard reporter is silenced
through its public options (`verbose`, `tbstyle`, `no_header`, `no_summary`) and
the receptor writes its own output from public hooks:

- `pytest_runtest_logreport` — collect phase reports
- `pytest_collectreport` — collect collection failures
- `pytest_warning_recorded` — count warnings
- `pytest_terminal_summary` — render
- `pytest_sessionfinish` — outcome and completeness

This removes the unbounded in-memory capture, the dump capture-boundary
ambiguity, most of the output-channel ambiguity, and nearly all dependence on
private pytest internals — as a consequence of the design rather than as
separate fixes.

Elapsed time uses `time.monotonic()`.

Fingerprints are computed over complete normalized evidence before any
presentation truncation, so two failures differing only inside an omitted region
never collide.

## Reliability floor

The adoption condition is not renderer correctness. It is that installing the
plugin can never lose a run.

The entire render is wrapped so that any receptor exception produces:

```text
RECEPTOR_ERROR · pytest exit=1 · KeyError: 'longrepr' · standard output follows
```

followed by pytest's standard output, with pytest's exit status preserved
unchanged. The worst case of enabling the plugin is standard pytest plus one
line of noise. That is what makes it safe to put in `addopts`.

The receptor never renders success when it cannot determine the outcome.

## Measuring efficiency honestly

The published benchmark must change in two ways.

**Correct the baseline.** Current figures compare against pytest's *default*
output. The honest comparison is against a competently configured pytest,
`pytest -q --no-header --tb=short`. Measured on a green two-test suite, stock
quiet pytest emits roughly twelve tokens and the receptor roughly nine: the
advertised 87.88% green-suite saving does not survive a fair baseline.

**Measure sufficiency, not only size.** For each scenario in the failure corpus,
record whether the root cause and the exact rerun target are recoverable from the
first response. A 60% saving that causes one extra suite execution is a net loss.

The honest 0.6 headline is not the green case, which stock pytest already solves.
It is the cascade case: a 38-failure cascade dropping from roughly 1,900 tokens
to roughly 300 with no loss of which tests failed or why.

## Acceptance criteria

0.6 ships when all of the following hold.

**Truth**

- Exit codes 0 through 5 each render a distinct correct outcome.
- No nonzero exit status renders as `PASS`.
- An interrupted, fail-fast, or max-failure run states that it is incomplete.
- A renderer exception yields `RECEPTOR_ERROR`, preserves pytest's exit code, and
  emits standard output.
- Warning and xpass counts appear on successful runs; xpasses are identified.

**Fidelity**

- Two failures with equal messages but different locations or captured output
  retain both contexts.
- Two long messages differing only inside the omitted region do not collide.
- Every grouped occurrence retains its node ID and phase.
- Every failure group carries a rerun command that actually selects it.
- The full report on disk contains every group and occurrence.

**Safety**

- Arbitrary Unicode, ANSI escapes, and control characters in messages, node IDs,
  and captured output cannot corrupt the output structure.
- Test-produced text is never rendered as a receptor instruction or command.

**Efficiency**

- The benchmark baseline is a configured pytest, with environment and command
  recorded.
- The cascade scenario is measured for both size and sufficiency.

**Compatibility**

- CI covers Python 3.11 and 3.13 against pytest 8 and pytest 9.
- `--receptor=human` produces byte-identical output to pytest without the plugin
  installed.

## Work sequence

1. **Delete.** XML, hints, heartbeat, and the duplicated `CiTerminalReporter`
   class. Largest risk reduction per line
   removed; 0.6 is smaller than the current code.
2. **Rebuild on public hooks**, with the `RECEPTOR_ERROR` fallback in place from
   the first commit.
3. **Outcome classification** from `ExitCode`, with completeness, and regressions
   for exit codes 0 through 5.
4. **Grouping with progressive disclosure** and the on-disk full report.
5. **Fix the benchmark baseline** and publish the honest figure.
6. **Minimal compatibility CI**, then release.

## Deliberately deferred to 1.1

**Delta mode.** In a TDD loop, "3 of 4 previous failures fixed, 1 remains, 0 new"
is extremely cheap and is exactly what an agent needs from iteration two onward.
pytest already provides `.pytest_cache` and `--lf`, so the implementation is
inexpensive. It is held back only to avoid delaying 0.6.

After cascade deduplication, this is the strongest remaining idea in the project.
