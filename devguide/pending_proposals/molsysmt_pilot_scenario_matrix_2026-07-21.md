# MolSysMT pilot scenario matrix and provisional usage policy

**Observed:** 2026-07-21  
**Consumer:** MolSysMT  
**Status:** shadow-mode evidence, not an adoption decision

## Outcome

The receptor is useful in the scenarios where agent-oriented compression
matters: broad distributed green runs, fixture cascades, multiple independent
failures, and warning families. It is counterproductive for very small green
suites because the fixed `slowest` block is larger than pytest's quiet output.

In every completed scenario below, receptor and authoritative pytest agreed on
pass/fail status and counts. Failure output was sufficient to act without
opening the disk artifact or source files. Distinct numeric assertions remained
distinct, while one six-test fixture cascade was grouped once.

Token counts are receptor's four-characters-per-token approximation because
`tiktoken` is not installed in the MolSysMT environment.

## Scenario evidence

| Scenario | Authority | Receptor | Token comparison | Assessment |
|---|---:|---:|---:|---|
| Focused PDB green, serial | 20 passed | 20 passed | 106 vs 25, +324% | Correct but too expensive |
| Focused PDB green, `-n 4` | 20 passed | 20 passed | 100 vs 35, +186% | Correct but too expensive |
| Controlled two failures plus six setup errors | 2 failed, 6 errors | 2 failed, 6 errors; 3 causes | 241 vs 1047, -77% | Compact and diagnostically sufficient |
| Numeric warning variants plus distinct atom names | 4 passed, 5 warnings | 4 passed, 5 warnings in 3 groups | 97 vs 404, -76% | Correct safe normalization; names preserved |
| Real `string:pdb_text` suite, serial | 366 passed | 366 passed | 105 vs 128, -18% | Modest but real benefit |
| Real PDB/native regression surface, `-n 12` | 530 passed | 530 passed | 8 vs 178, -95.5% | Very high value |

The distributed 530-test run emitted a correct final verdict and no unnecessary
`slowest` block, explaining much of the large saving. Its progress stream did,
however, skip the first three deciles; that defect is recorded separately in
`pending_bugs/molsysmt_xdist_progress_skips_initial_deciles.md`.

## Diagnostic sufficiency

For the controlled failing run, the receptor output was enough to identify and
rerun all causes:

- the six setup errors were grouped under the fixture's `RuntimeError` once;
- both assertion failures retained their distinct observed values (`3.5` and
  `4.5`) and separate node IDs;
- the failed/error phase counts matched pytest;
- every group carried a directly usable rerun command.

For warnings, three numeric size variants were safely grouped and explicitly
labelled `(3 variants)`. The scientifically meaningful atom names `Ar` and `CA`
remained separate groups. No local `receptor_normalizers` rule was needed.

## Provisional MolSysMT usage policy

Continue shadow mode and choose the reporter by expected output shape:

1. Use normal `pytest -q` as authority for focused green loops below roughly
   50 tests; receptor's fixed summary overhead is larger there.
2. Run receptor in parallel shadow evaluation for broad suites, xdist runs,
   warning-heavy surfaces, fixture failures, or multi-cause failures.
3. Keep comparing verdict, phase counts, and exit code until the pilot closes.
4. Treat any `PASS` in an artifact containing `incomplete:` as provisional and
   invalid for automation; the related artifact-state bug is recorded in
   `pending_bugs/molsysmt_xdist_incomplete_run_reported_pass.md`.
5. Do not add local normalizers until real MolSysMT output demonstrates a safe
   rule that built-in normalization does not cover.

## Product implication

A small-suite threshold or compact-green mode without `slowest` would make the
receptor attractive for systematic use rather than only broad runs. The plugin
already demonstrates enough value to continue the pilot: its best real result
reduced agent-visible stdout by 95.5%, and its failure grouping saved 77% while
retaining all information needed for action.

## Update 2026-07-21

The "counterproductive for very small green suites" finding was driven by the
fixed `slowest:` block, which this matrix names as the culprit ("larger than
pytest's quiet output"). That block was removed the same day (commit `29bc9a4`),
so a small green run is now a single verdict line plus the optional stats line.
The two small-suite rows above (`+324%`, `+186%`) were measured before that
change and should be re-measured before the shadow-mode small-suite policy
(items 1–2) is treated as settled; the threshold this proposal asks for may no
longer be needed.

Both referenced defects are resolved: the `PASS`-with-`incomplete:` artifact and
the stale mid-run snapshot are fixed in the verdict logic and by clearing the
artifact at session start, and the progress-decile contract is corrected in the
docs. See [`../resolved_bugs/`](../resolved_bugs/README.md). This does not close
the pilot, which stays in shadow mode.
