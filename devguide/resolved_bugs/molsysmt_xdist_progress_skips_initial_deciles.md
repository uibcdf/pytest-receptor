# MolSysMT xdist progress skips the initial deciles

**Observed:** 2026-07-21  
**Consumer:** MolSysMT  
**Command profile:** `--receptor=llm --receptor-stats -n 12`

## Summary

A completed, green 530-test MolSysMT run produced a correct final verdict and a
large token saving, but its progress stream began at 35% and never emitted the
10%, 20%, or 30% milestones. This does not match the documented and previously
reported contract of exactly nine controller-only lines from 10% through 90%.

## Evidence

The complete stderr progress stream captured from the live session was:

```text
receptor: 35% 190/530 20s
receptor: 40% 212/530 21s
receptor: 50% 265/530 25s
receptor: 60% 318/530 29s
receptor: 70% 371/530 32s
receptor: 80% 424/530 35s
receptor: 90% 477/530 37s
```

The final stdout verdict was correct:

```text
PASS exit=0 | 530 passed | 67.15s

receptor stats: 8 tokens vs 178 for pytest as you configured it | 170 fewer (-95.5%) | approx (4 chars/token)
```

The corresponding authoritative pytest run also completed with 530 tests and
exit code 0.

## Why it matters

The missing early milestones remove the liveness signal during the first half
of short-to-medium xdist runs. The first emitted percentage is also not a
decile, which makes the stream harder to interpret mechanically.

One likely shape is that the controller receives a batch of completions after
several thresholds have already been crossed and emits only the current
percentage. If so, every newly crossed threshold should be emitted in order, or
the contract should explicitly change from exact deciles to sparse progress.

## Expected behavior

- exactly one controller-side line at each threshold from 10% through 90%;
- strictly increasing percentages;
- every line includes completed/total and elapsed time;
- no worker-originated duplicates.

---

## Resolution

**Fixed 2026-07-21.** The behavior changed, not only the documentation. The old
code emitted a single catch-up line at the current percentage when the warm-up
ended — the confusing `35%`. It now emits every threshold already crossed, in
order, so the reader sees round milestones instead. Two related changes came with
it, on the maintainer's call: the step is twenty percent rather than ten (five
lines at most instead of nine — the same signal for fewer tokens), and 100% is
now announced, the run reaching its end on stderr a moment before the verdict
lands on stdout.

So the pilot's leading `35%` is now `20%`, and a green 530-test run reads:

```text
receptor: 20% 190/530 20s
receptor: 40% 212/530 22s
receptor: 60% 318/530 29s
receptor: 80% 424/530 35s
receptor: 100% 530/530 67s
```

The stream stays strictly increasing, controller-only, and every line carries
completed/total and elapsed time — the properties this report asked to preserve.
`usage.md` and `reference.md` describe the new contract. This takes the report's
second suggested option, emitting the crossed thresholds rather than skipping
them, with round twenty-percent milestones.
