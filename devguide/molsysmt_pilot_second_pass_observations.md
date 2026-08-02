# MolSysMT Pilot Second-Pass Observations

## Context

MolSysMT resumed the 0.6.0 shadow pilot after the phase-counting, path, warning,
and liveness fixes landed on `main`. Normal pytest remained the authority. The
receptor was evaluated with a synthetic mixed-phase failure and the real
9,378-item MolSysMT suite.

## Result integrity

The phase model now agrees with pytest. A synthetic run containing one call
failure, one setup cascade, one teardown failure, and ordinary passes produced
the same summary in both reporters:

```text
1 failed, 2 passed, 6 errors
```

The teardown test correctly contributed one pass and one error. The five setup
errors were grouped once as `5 tests | setup`; the report no longer contradicts
its own phase label.

The real green run reported:

```text
PASS exit=0 | 9336 passed, 2 skipped | 529.65s | 216 warnings
```

This agrees with the authoritative pytest run. No success disagreement was
observed.

## Diagnostic sufficiency

The synthetic fixture cascade was sufficient without opening another report or
source file. It named affected tests, showed the phase and exception, and its
literal `rerun:` command worked from the invocation directory.

Tests located far outside the invocation directory were printed as absolute
paths. This avoided the former duplicated `molsysmt/molsysmt` path and was fully
actionable. It is intentional in `_display_path()` when a relative path would
begin with at least three parent traversals. Pilot wording should therefore say
"resolvable from the invocation directory" rather than promising that every
path is relative.

## Warning completeness and cost

All 216 warnings appeared as exactly 60 groups, with no `+N more groups` suffix.
The low-frequency tail included the new or unusual candidates that frequency
truncation previously hid. This is diagnostically sufficient from the terminal
output alone.

With `tiktoken` absent, the labelled four-characters-per-token estimate was:

```text
2444 tokens vs 10370 for pytest | 7926 fewer (-76.4%) | approx
```

The saving is smaller than the earlier green-suite benchmark because complete
warning evidence is now intentionally rendered. That is the correct trade-off:
76% less output that is sufficient is more valuable than 97% less output that
forces a second read. Exact token measurement is optional and does not justify
adding `tiktoken` to MolSysMT's scientific environment solely for the pilot.

## Experience and tone

The final report is calm, compact, and considerably easier to audit than the
ordinary pytest warning summary. Phase words (`setup`, `call`, `teardown`) are
especially effective because they remove interpretive ambiguity without adding
much text. The explicit `approx` label on token statistics is honest and clear.

The progress stream was uncomfortable before its cause was understood: lines
such as `receptor: 1990 43s` looked truncated, while repeated `10%` milestones
made the run appear to move backwards. This is reported separately as
`xdist_progress_is_not_bounded_by_deciles.md`. Apart from that defect, the new
liveness concept is useful: even imperfect output made it clear that the
529-second run was active, and the final slow-test list explained the long tail.

## Current trust assessment

The receptor passed the result-integrity, mixed-phase, rerun, and complete
warning checks in this pass. It is now useful enough to continue using in shadow
mode. It should not yet replace pytest as the sole authority because the xdist
progress contract still fails and the project remains deliberately pre-1.0.
Once controller-only progress has an xdist regression, the next trust-building
step should be several ordinary MolSysMT development cycles containing real,
not synthetic, failures.
