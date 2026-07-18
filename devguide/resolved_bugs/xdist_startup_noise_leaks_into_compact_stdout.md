# Xdist Startup Noise Leaks into Compact Stdout

## Status

Confirmed on 2026-07-18 with `pytest-receptor` main at `2f4b248`.

## Reproduction

From the MolSysMT repository:

```bash
python -m pytest --receptor=llm -n 4 \
  tests/_private/test_conversion_fidelity_audit.py
```

Observed stdout:

```text
bringing up nodes...
bringing up nodes...


PASS exit=0 | 4 passed | 8.47s
```

The same two lines appeared before the compact report in the full `-n 12`
MolSysMT run. This is independent of the resolved progress defect: progress is
now emitted correctly on stderr by the controller only, while these lines are
xdist startup output on stdout.

## Impact

- The compact stdout stream is not exclusively the receptor report.
- Agents consuming the first line as the verdict must skip unrelated pytest
  infrastructure text.
- The token cost is tiny, but the tone suggests that pytest's ordinary terminal
  reporter has not been completely replaced.
- Result integrity and diagnostic evidence are unaffected.

## Acceptance criteria

- `--receptor=llm -n N` and `--receptor=ci -n N` suppress xdist's
  `bringing up nodes...` lines.
- Human mode remains byte-identical to ordinary pytest and keeps the lines.
- Compact stdout begins with the receptor verdict or an intentional third-party
  report whose preservation is part of the documented contract.
- Add an xdist subprocess regression that inspects stdout, not only stderr
  progress.

---

## Resolution

**Fixed 2026-07-18.** The third acceptance criterion drew the distinction that
decided the fix: `bringing up nodes...` is infrastructure chatter -- the
distributed equivalent of the progress characters already suppressed -- while
pytest-cov's table is a *report*. Suppressing the first is consistent;
suppressing the second was a bug we shipped once already.

So the fix is deliberately narrow. `TerminalDistReporter.ensure_show_status` is
neutered on the instance, and nothing else. Unregistering the plugin would have
been simpler and wrong: the same object carries `pytest_testnodedown`, which
prints `[gw3] node down: <error>`. A worker dying is a completeness signal, and
losing it silently is exactly the failure mode this project exists to prevent.

The receptor also no longer prints a blank line before its verdict, so compact
stdout now begins with `PASS`/`FAIL` on a serial run. Under xdist a single blank
line remains, emitted by xdist itself outside the terminal writer; chasing it
would mean reaching further into another plugin than this warrants.

Regressions: stdout is asserted for both `llm` and `ci` profiles under `-n 2`,
checking the chatter is gone and the first line is the verdict, plus a test that
the crash-reporting hook survives the silencing.
