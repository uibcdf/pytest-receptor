# MolSysMT Xdist Progress Reverification

## Environment

- pytest-receptor commit: `2f4b248`
- command: `python -m pytest --receptor=llm -n 12`
- authoritative comparison: the immediately preceding normal MolSysMT pytest
  run

## Result

The controller-only progress correction satisfies all six acceptance criteria
on the real MolSysMT suite. Stderr contained exactly these nine milestones:

```text
receptor: 10% 934/9338 32s
receptor: 20% 1868/9338 43s
receptor: 30% 2802/9338 62s
receptor: 40% 3736/9338 81s
receptor: 50% 4669/9338 88s
receptor: 60% 5603/9338 118s
receptor: 70% 6537/9338 161s
receptor: 80% 7471/9338 204s
receptor: 90% 8405/9338 248s
```

There were no denominator-free lines, duplicates, regressions, worker-local
counts, or post-90% progress lines. Percentages were strictly increasing.

The denominator is now also semantically correct: 9,338 collected items equals
the final 9,336 passed plus 2 skipped. The earlier faulty run advertised 9,378
while ultimately reporting only 9,338 outcomes.

The final receptor verdict was:

```text
PASS exit=0 | 9336 passed, 2 skipped | 582.77s | 215 warnings
```

It agrees with pytest's successful result. All 60 warning groups were rendered.
The one-warning difference from a previous run came from a third-party warning
whose emission varies with execution order; it is not a receptor counting
disagreement within the same run.

## Trust consequence

The xdist progress defect can be considered resolved for the MolSysMT pilot.
The receptor should remain in shadow mode as already agreed, with subsequent
evaluation focused on naturally occurring development failures rather than
more synthetic cases.

One separate low-severity observation was found during this verification:
xdist's two `bringing up nodes...` lines leak into compact stdout. It is reported
independently in `pending_bugs/xdist_startup_noise_leaks_into_compact_stdout.md`.
