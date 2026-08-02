# MolSysMT pilot remeasurement against pytest-receptor `5146688`

**Observed:** 2026-07-21  
**Consumer:** MolSysMT  
**Status:** shadow-mode evidence; normal pytest remains authoritative

## Outcome

Three requested corrections are verified on real MolSysMT surfaces:

- removing the fixed `slowest:` block eliminates the small-green-suite penalty;
- native `dcdplugin)` C-stdio output no longer trails the compact verdict;
- xdist progress uses bounded round 20% steps and finishes at 100%.

The previously successful fixture-cascade and warning-normalization behavior
also remains correct. One new high-severity divergence was found on the
controlled-incomplete path with `--receptor-stats`: the compact verdict is
correct, but pytest later writes through the already closed stats temporary
stream and the process changes from exit 0 to exit 1. That defect is reported
separately in
`pending_bugs/molsysmt_incomplete_stats_closes_terminal_stream.md`.

Token counts below are exact `cl100k_base` measurements. `tiktoken` is now
available in the pilot environment.

## Results

| Scenario | Authoritative pytest | Receptor | Tokens | Assessment |
| --- | --- | --- | ---: | --- |
| Focused PDB green, serial | 22 passed, exit 0 | 22 passed, exit 0 | 15 vs 16, -6.2% | Correct; former small-suite penalty removed |
| Focused PDB green, `-n 4` | 22 passed, exit 0 | 22 passed, exit 0 | 15 vs 24, -37.5% | Correct and beneficial |
| Native conversion/DCD surface | 79 passed, exit 0 | 79 passed, exit 0 | 15 vs 22, -31.8% | Correct; no native banner trails `PASS` |
| Broad PDB/native surface, `-n 12` | 528 passed, exit 0 | 528 passed, exit 0 | 15 vs 78, -80.8% | Correct; progress exactly 20/40/60/80/100% |
| Controlled incomplete, no stats | 1 of 4 passed, controlled exit 0 | `INCOMPLETE exit=0`, 1 of 4, process exit 0 | not measured | Correct verdict and stale-artifact clearing |
| Controlled incomplete, stats | 1 of 4 passed, controlled exit 0 | `INCOMPLETE exit=0`, then internal traceback, process exit 1 | 25 vs 119 before traceback | **New result-integrity defect** |
| Two failures plus fixture cascade | 2 failed, 6 errors, exit 1 | same counts and exit; 3 causes | 300 vs 855, -64.9% | Correct; numeric assertions remain separate |
| Numeric warning variants | 4 passed, 5 warnings | 4 passed, 5 warnings in 3 groups | 156 vs 479, -67.4% | Correct; numeric sizes merge, names do not |

The former 530-test selection now collects 528 tests after intervening MolSysMT
changes. This is suite evolution, not a reporter discrepancy: both invocations
collected and completed the same 528 outcomes.

## Exact real-suite commands

Small PDB suite:

```bash
pytest tests/conversion_truth/test_pdb_fidelity.py
pytest --receptor=llm --receptor-stats tests/conversion_truth/test_pdb_fidelity.py
pytest -n 4 tests/conversion_truth/test_pdb_fidelity.py
pytest --receptor=llm --receptor-stats -n 4 tests/conversion_truth/test_pdb_fidelity.py
```

Native conversion/DCD surface:

```bash
pytest tests/conversion_truth
pytest --receptor=llm --receptor-stats tests/conversion_truth
```

Broad distributed surface:

```bash
pytest -n 12 \
  tests/conversion_truth \
  tests/form/file_pdb \
  tests/form/molsysmt_PDBFileHandler \
  tests/form/string_pdb_text \
  tests/basic/convert/one_to_one/test_convert_from_string_pdb_text.py \
  tests/basic/convert/one_to_one/test_convert_from_file_pdb.py \
  tests/basic/get/test_get_file_pdb.py \
  tests/native/test_molsys.py \
  tests/native/test_structures_extended.py \
  tests/build/make_bioassembly/test_make_bioassembly.py

pytest --receptor=llm --receptor-stats -n 12 \
  tests/conversion_truth \
  tests/form/file_pdb \
  tests/form/molsysmt_PDBFileHandler \
  tests/form/string_pdb_text \
  tests/basic/convert/one_to_one/test_convert_from_string_pdb_text.py \
  tests/basic/convert/one_to_one/test_convert_from_file_pdb.py \
  tests/basic/get/test_get_file_pdb.py \
  tests/native/test_molsys.py \
  tests/native/test_structures_extended.py \
  tests/build/make_bioassembly/test_make_bioassembly.py
```

## Progress and native-output observations

The 528-test xdist stream was exactly:

```text
receptor: 20% 106/528 28s
receptor: 40% 212/528 42s
receptor: 60% 317/528 56s
receptor: 80% 423/528 68s
receptor: 100% 528/528 99s
```

It is controller-only, strictly increasing, round, bounded to five lines, uses a
stable denominator, and announces completion. The 79-test serial run emitted
catch-up thresholds 20% and 40% at the same completed count; this matches the
documented behavior of emitting every already-crossed threshold in order.

Normal pytest's 79-test DCD run ended with many `dcdplugin)` banners after its
summary. Receptor ended with its compact summary and stats; no `dcdplugin)` text
appeared before or after it. The bounded native flush/capture fix is therefore
verified on the original consumer surface.

## Incomplete-run verification

A prior report was deliberately seeded in the temporary test root. The first
test of the next receptor session asserted that
`.pytest_cache/d/receptor/last-run.txt` did not exist, and passed. The new
session therefore clears the stale artifact before test execution as intended.

Without stats, the controlled `pytest.exit(returncode=0)` produced:

```text
INCOMPLETE exit=0 | 1 passed | incomplete: 1 of 4 executed | 0.18s
```

and the process returned 0. A normal pytest run also returned 0 after one test.
With `--receptor-stats`, the same correct compact line was followed by a
`ValueError: I/O operation on closed file` from pytest's late terminal handling,
and the process returned 1. See the dedicated pending bug for the full
reproducer and acceptance criteria.

## Updated pilot assessment

There is no longer evidence for a small-suite threshold: the two previously
counterproductive green rows now save output, including the 22-test serial case.
For ordinary completed runs, the receptor is useful across small, broad,
distributed, warning-heavy, native-output, and multi-cause failure scenarios.

The pilot must remain in shadow mode. The new stats/incomplete divergence is
precisely the class of issue for which pytest must remain authoritative: a
reporting option must never change the process exit status. After that defect is
fixed, this exact controlled-incomplete scenario should be re-run before raising
the trust level.

## Update 2026-07-21

The stats/incomplete divergence is fixed (PR-PILOT-011): the receptor redirects
pytest's terminal writer to a discard stream in `pytest_unconfigure`, so the late
Exit write neither crashes nor trails the report, and the exit code is unchanged
with and without `--receptor-stats`. A subprocess regression covers both modes.
The controlled-incomplete scenario above is the one to re-run to confirm on the
real surface.

The small-suite threshold question is settled by this re-measurement: the two
formerly counterproductive green rows now save output (including the 22-test
serial case at -6.2%), so the provisional policy of preferring plain pytest below
~50 tests in `molsysmt_pilot_scenario_matrix_2026-07-21.md` (items 1–2) is
withdrawn. No threshold is needed. The pilot stays in shadow mode until the
consumer decides otherwise.
