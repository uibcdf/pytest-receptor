# In-progress MolSysMT xdist artifact is temporarily reported as PASS

**Observed:** 2026-07-21  
**Consumer:** MolSysMT  
**Profile:** `--receptor=llm --receptor-stats -n 12`

## Severity

High for artifact consumers, but not a demonstrated false final verdict. The
terminal never rendered `PASS`; the misleading status was observed in the disk
artifact while the unified execution session was still active.

## Reproduction

From the MolSysMT repository, the authoritative pytest run over the selected PDB
and native regression surface yielded control after displaying 54% progress.
The execution wrapper returned a live session, but the consumer initially
mistook that intermediate yield for process completion. The same selection was
then run with:

```bash
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

The first captured terminal chunk contained only these progress records and no
verdict:

```text
receptor: 34% 179/526 20s
receptor: 40% 211/526 22s
receptor: 50% 263/526 25s
```

While the pytest process was still running, the resolved report path
`.pytest_cache/d/receptor/last-run.txt` already contained:

```text
PASS exit=0 | 39 passed | incomplete: 39 of 526 executed | 36.38s

slowest:
  tests/conversion_truth/test_native_bond_seam_adapters.py::test_endpoint_adapters_fail_closed_without_chemical_state[string:pdb_text-True] (6.03s)
  tests/form/string_pdb_text/test_to_molsysmt_native.py::test_string_pdb_text_to_molsysmt_topology_preserves_counts (1.87s)
  tests/form/string_pdb_text/test_get_topological_attributes.py::test_flat_list[get_chain_index_from_chain-1] (1.02s)
```

The completed-count discrepancy is itself inconsistent: progress had reached
263/526, whereas the provisional artifact said only 39/526 executed.

## Correction to the initial interpretation

Subsequent inspection showed that the pytest process had not terminated. The
execution API yields a session after 30 seconds and requires explicit polling;
the original report incorrectly described that yield as a completed run. A
separate real receptor run over 366 MolSysMT tests was polled to completion and
correctly reported `PASS exit=0 | 366 passed`, with exactly nine monotonic
progress lines and an 18% token saving.

Therefore, there is no evidence here that receptor's final stdout verdict was
false. The remaining defect is that the documented complete report path can
contain a success-labelled, internally inconsistent provisional snapshot while
the run is active. A consumer that reads the advertised artifact path before
process completion can still be misled.

## Expected behavior

- A provisional artifact must not use the `PASS` verdict. Prefer atomic publish
  at session finish, or label an intermediate artifact `RUNNING`/`INCOMPLETE`.
- The report should explain why the run ended if pytest/xdist exposes that
  evidence, or state explicitly that the termination cause is unavailable.
- The completed count in progress and the final artifact must share one
  controller-side source of truth.
- Documentation should state whether `last-run.txt` is valid only after process
  completion. If it is intentionally updated during execution, readers need a
  machine-checkable running state.

## Consumer action

The receptor pilot continues in shadow mode across serial, xdist, green, failed,
fixture-cascade, and warning scenarios. Normal pytest remains the authority.

---

## Resolution

**Fixed 2026-07-21.** Two independent fixes, one for each half of the report.

*The verdict.* `_summary_line` computed the verdict from the exit status and then
only *appended* the `incomplete:` note, so a zero exit with collected tests left
unexecuted printed `PASS ... | incomplete: N of M executed` — the contradiction
this report caught, and one a consumer keying on the leading token would miss.
The qualifier is now computed before the verdict token, and when it is present a
`PASS` is downgraded to `INCOMPLETE`. Reproduced with a `pytest.exit(returncode=0)`
mid-suite — the smallest way to reach a zero exit with tests unrun; the
regression asserts the output starts `INCOMPLETE exit=0` and contains no `PASS`.

*The stale artifact.* The disk report is written once, at session finish — never
progressively — so the snapshot read mid-run was a *previous* run's file, and the
39-vs-263 count gap was the distance between two different runs, not a live
inconsistency. A new run now clears any prior `last-run.txt` at session start, so
the documented path is absent until this run finishes and a mid-run read is an
unambiguous "not yet". Regression: a first run publishes the artifact; a second
run's own test asserts it is gone while that second run is still executing.

The docs claimed the report was "written during the run"; that was never true and
is corrected. `slowest:` no longer appears in the artifact either — it was
removed the same day for unrelated reasons.
