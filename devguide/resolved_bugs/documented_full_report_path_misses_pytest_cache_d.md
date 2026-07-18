# Documented Full-Report Path Misses Pytest Cache `d` Directory

## Status

Confirmed in the MolSysMT pilot on 2026-07-18 with pytest-receptor `11b3785`.

## Evidence

The user-facing documentation and pilot request name:

```text
.pytest_cache/receptor/last-run.txt
```

The file produced through pytest's `config.cache.mkdir("receptor")` is actually:

```text
.pytest_cache/d/receptor/last-run.txt
```

After a complete run, the documented path did not exist while the latter file
contained the expected owner-only full report. This follows pytest's cache API
layout rather than a MolSysMT configuration override.

## Impact

- A user following the documentation concludes that the report was not saved.
- Diagnostic detail may be regenerated unnecessarily by rerunning an expensive
  suite.
- Requests for evidence can point collaborators at the wrong file.

## Acceptance criteria

- Documentation uses the actual path returned by pytest's cache API, or avoids
  hard-coding an internal layout and prints the resolved report path after a run.
- The path is tested against every supported pytest major version.
- If the physical path is intentionally treated as private, provide a stable
  receptor command that prints or reads the latest complete report.

---

## Resolution

**Fixed 2026-07-18.** Documentation only; the receptor always printed the
resolved path, so what it emitted was correct and what we wrote about it was
not. Four documents said `.pytest_cache/receptor/last-run.txt`.

Verified on both supported majors -- pytest 8.4.2 and 9.1.1 both produce
`.pytest_cache/d/receptor/last-run.txt` -- and corrected everywhere, with a note
that the `d/` component belongs to pytest's cache layout rather than to us: we
call `config.cache.mkdir("receptor")` and pytest decides where that lives. The
usage guide now says to prefer the path the receptor prints over reconstructing
it by hand.
