# Xdist Progress Is Not Bounded by Deciles

## Status

Confirmed in the MolSysMT shadow pilot on 2026-07-18 with the current `main`
branch at `2df8cf5`.

## Reproduction

From the MolSysMT repository:

```bash
python -m pytest --receptor=llm --receptor-stats -n 12
```

The 9,378-item run completed successfully, but stderr mixed controller deciles
with clock-based lines and repeated deciles:

```text
receptor: 1 23s
receptor: 1990 43s
receptor: 2843 63s
receptor: 3474 83s
receptor: 10% 938/9378 88s
receptor: 5112 103s
receptor: 5747 123s
receptor: 6053 143s
receptor: 6373 163s
receptor: 10% 938/9378 165s
...
receptor: 20% 1876/9378 268s
...
receptor: 10% 938/9378 312s
```

The run emitted substantially more than nine progress lines. Some lines lacked
both percentage and denominator, and the 10% milestone appeared repeatedly
after later apparent counts had already been printed.

## Likely cause

`ReceptorPlugin._emit_progress()` falls back to a clock-based marker whenever
`self._collected` is zero. Under xdist, plugin instances without the controller's
collection total appear to write that fallback to the same stderr stream as the
controller. Other instances also appear able to emit their own decile state.
The current progress regressions use serial `pytester.runpytest_subprocess()`
scenarios and therefore cannot detect multi-process emission.

This cause is an inference from the observed output and the current source; it
should be confirmed by recording process or worker identity in a development
build.

## Impact

- The advertised upper bound of nine lines is false for the principal MolSysMT
  command.
- Lines without a denominator are ambiguous and look like corrupted output.
- Repeated lower milestones make pace interpretation unreliable.
- The final verdict remains correct; this is not a result-integrity failure.

## Acceptance criteria

- With `-n 12`, only the controller emits progress.
- A completed long run emits at most the nine 10%-through-90% milestones.
- Every emitted line uses `receptor: N% finished/collected elapsed`.
- Percentages are strictly increasing and never repeated.
- The contract holds both with and without `--receptor-stats`.
- Add an xdist subprocess regression that asserts stderr line count, format,
  monotonicity, and uniqueness rather than only testing serial execution.

---

## Resolution

**Fixed 2026-07-18.** The inference in this report was correct, and the cause was
worse than "instances without the controller's total": *every* process was
emitting. Under xdist the plugin is instantiated in each worker as well as the
controller. A worker collects the whole suite, so its denominator is right, but
it only ever finishes its own share -- so all twelve announced 10% at their own
pace, interleaved with the controller, whose `pytest_collection_modifyitems`
never fires under xdist and which therefore had no denominator at all and fell
back to a bare count.

Two changes. Workers no longer emit: only the controller has the global view.
And the controller now learns the total from `pytest_xdist_node_collection_finished`,
declared with `optionalhook=True` so the plugin still loads where xdist is
absent.

Verified on `-n 4` over 60 tests: exactly nine lines, 10% through 90%, strictly
increasing, every one carrying the full denominator.

The regression is the one this report specified: an xdist subprocess run
asserting line count, format, monotonicity, uniqueness, and the absence of 100%,
parametrized over `--receptor-stats` since the report asked for both. The point
about our serial-only coverage was the important half of the report -- the tests
could not have caught this, and now can.
