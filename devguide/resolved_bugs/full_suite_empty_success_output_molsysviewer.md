# Full MolSysViewer suite exits successfully without an LLM summary

**Observed:** 2026-07-29

## Environment

- `pytest 9.0.2`
- `pytest-receptor 0.6.0`
- MolSysViewer `7a14fbfc` plus an uncommitted `set_color` change

## Reproduction

From the MolSysViewer repository:

```bash
python -m pytest --receptor=llm tests/
```

The process ran for about 26 seconds and exited with status 0, but stdout and
stderr were both empty. No compact verdict or test count was emitted.

The same reporter did emit normal summaries for specific files in the same
environment:

```text
PASS exit=0 | 10 passed | 8.96s
PASS exit=0 | 2 passed | 6.29s
```

Those came from `tests/test_color_layers.py` and
`tests/test_public_api_docs.py`, respectively.

## Impact

The exit status still indicates success, but the agent cannot report how many
tests ran or whether tests were skipped. Re-running ordinary pytest would
violate MolSysViewer's one-full-suite-run discipline. This makes the compact
output insufficient even on a green run.

## Expected

At minimum, the full run should end with the same truth-preserving verdict and
counts that specific-file runs produce.

## Re-observation — 2026-08-02

The missing final summary no longer reproduces with the current local
pytest-receptor checkout. This command now finishes correctly:

```bash
python -m pytest --receptor=llm -n 12 tests/
```

Observed final verdict:

```text
PASS exit=0 | 1165 passed, 3 skipped | 65.18s | 63 warnings
```

There is still an xdist progress defect before that verdict. The 20% and 40%
milestones report the same completed count and elapsed time:

```text
receptor: 20% 647/1168 20s
receptor: 40% 647/1168 20s
receptor: 60% 701/1168 22s
receptor: 80% 935/1168 29s
receptor: 100% 1168/1168 61s
```

The denominator and final outcome agree (`1168 = 1165 + 3`), so this is not an
outcome disagreement. It is a misleading progress snapshot under `-n 12`: 40%
cannot truthfully correspond to 647 completed items. Serial reproduction has
not been attempted because the defect is specifically in xdist progress.

---

## Resolution

Two distinct issues; both closed.

**The empty final summary (original report, 2026-07-29) was fixed by
PR-PILOT-013** and no longer reproduces, as the 2026-08-02 re-observation
confirms — the full suite now ends with `PASS exit=0 | 1165 passed, 3 skipped`.
That report captured the deselection-denominator bug (a completed selection read
as incomplete); once the denominator moved to `session.items` in
`pytest_collection_finish`, the full run renders its verdict normally. See
[`deselected_tests_reported_incomplete.md`](deselected_tests_reported_incomplete.md).

**The progress snapshot (PR-PILOT-014) is fixed 2026-08-02.** The two identical
lines `20% 647/1168` and `40% 647/1168` came from the back-fill introduced for
PR-PILOT-009: after the warm-up, `_emit_progress` emitted *every* 20% milestone
already crossed, in order, each labelled with the round threshold but carrying
the *current* count. Under serial that is one slightly-early line; under `-n 12`
the warm-up hides more than half the run (647/1168 ≈ 55%), so two milestones are
back-filled at once — both stamped with the same 647 and the same 20s, and both
labelled with a percent that contradicts their own fraction (647 is 55%, not 20%
or 40%).

The percent is now the real one, derived from the count printed beside it, so the
two can never disagree. The milestone step still governs *when* a line is emitted
(bounding the output to five lines), but the number shown is
`finished * 100 // collected`, which at a live crossing already sits on the round
milestone without being forced there. Milestones crossed during the warm-up
silence are skipped rather than re-announced: the first post-warm-up call
realigns `_next_threshold` to the next uncrossed milestone and stays quiet, so
every line thereafter reports a crossing actually watched. The reported run would
now read `60% 701/1168`, `80% 935/1168`, `100% 1168/1168` — no duplicate
snapshot, no percent that disagrees with its fraction.

This supersedes the PR-PILOT-009 mechanism while keeping its intent: no milestone
is skipped in a way the reader would notice as a jump, the output stays bounded by
percentage not by clock, and 100% is still announced a moment before the verdict.

Regression: `test_progress_percent_always_matches_its_own_fraction` runs past a
long warm-up (so several milestones pass unseen) and asserts every line's percent
equals `finished * 100 // collected`, that no two lines share a snapshot, that
percents strictly increase, and that the last is 100.
