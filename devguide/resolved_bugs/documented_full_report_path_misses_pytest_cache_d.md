---
summary: Make documented full-report paths locate the written artifact.
issue: uibcdf/pytest-receptor#19
status: resolved
opened: 2026-10-03
closed: 2026-10-03
severity: low
verification: inspected
area: [reporting, compatibility]
guard: tests/test_consumer_guide.py::test_documented_full_report_path_matches_written_report
normative:
blocked_by: []
supersedes: []
historical_register: PR-PILOT-006
historical_resolved: 2026-07-18
---

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


## Identity and closure review — 2026-10-03

Owning identity: `uibcdf/pytest-receptor#19`. Reconciliation: `uibcdf/pytest-receptor#10`.
Historical register: `PR-PILOT-006`; recorded historical outcome: 2026-07-18.

The metadata dates refer to the issue-backed review, except for the
already existing Python 3.14 issue, whose original issue dates are retained.
The pre-protocol text, including commands and historical claims, is
preserved byte for byte above this dated addition. This review inspects
the current implementation and relevant assertions; it does not rerun
the historical consumer suite or certify an old release again.

The guard extracts the path from four maintained documents, runs a real pytest session and reads the resulting PASS report at each declared path. Reintroducing the missing cache d/ component in maintained guidance makes that read fail. Historical examples above retain their original spelling.

Durable guard: `tests/test_consumer_guide.py::test_documented_full_report_path_matches_written_report`. Its relevance is explained above.
