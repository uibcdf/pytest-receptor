# Deselected Tests Are Reported as an Incomplete Run

## Summary

Pytest-receptor reports a completed, successful pytest selection as
`INCOMPLETE exit=0` when a collection hook deselects tests through
`pytest_deselected`.

Normal pytest remains authoritative and reports the selected tests at 100% with
exit code 0. The receptor appears to retain the pre-deselection collection
count as its expected execution total.

## Environment

- pytest-receptor: editable `main` used by the MolSysMT pilot on 2026-07-28
- pytest: 9.0.2
- Python: 3.13.12
- execution: serial

## Reproduction on MolSysMT

MolSysMT's `tests/conftest.py` deselects the 40 tests marked
`peptide_parity` unless the user explicitly requests that marker:

```python
if 'peptide_parity' not in mark_expr:
    deselected = [
        item for item in items
        if item.get_closest_marker('peptide_parity')
    ]
    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = [
            item for item in items
            if not item.get_closest_marker('peptide_parity')
        ]
```

Run:

```bash
python -m pytest --receptor=llm \
  --molsysmt-kernel=rust \
  tests/build/build_peptide/test_build_peptide_molsysmt_MolSys.py
```

Observed receptor result:

```text
INCOMPLETE exit=0 | 39 passed | incomplete: 39 of 79 executed | 19.52s
```

Authority check:

```bash
python -m pytest -q \
  --molsysmt-kernel=rust \
  tests/build/build_peptide/test_build_peptide_molsysmt_MolSys.py
```

Observed normal-pytest result:

```text
....................................... [100%]
```

Exit code: 0.

The complete build-peptide selection reproduced the same issue:

```text
INCOMPLETE exit=0 | 135 passed | incomplete: 135 of 175 executed
```

The difference is again exactly 40 intentionally deselected tests.

## Expected Behavior

Intentional deselection is a completed pytest run over the effective
selection. The verdict should be `PASS exit=0`, with deselected tests reported
separately if receptor chooses to expose them. They must not count as tests
left unexecuted.

True incomplete runs such as `pytest.exit(returncode=0)`, `-x`, or
`--maxfail` must continue to render `INCOMPLETE`.

## Likely Cause

The progress/completeness denominator appears to be captured before
`pytest_collection_modifyitems` and is not reduced when
`pytest_deselected(items=...)` is emitted. This is an inference from the exact
79 collected versus 39 executed plus 40 deselected count.

## Acceptance Criteria

1. The reproduction above reports `PASS exit=0 | 39 passed`.
2. Optional counts distinguish `40 deselected` from incomplete tests.
3. A controlled early exit still reports `INCOMPLETE`.
4. The behavior is correct in serial and under xdist.
5. Progress percentages use the post-deselection total.

---

## Resolution

**Fixed 2026-07-28.** The diagnosis in the report was exact: the denominator was
read in `pytest_collection_modifyitems`, whose ordering against a project's own
deselection hook is undefined, and in the MolSysMT case ran *before* the conftest
trimmed the list — capturing 79 instead of 39. `pytest_deselected` was not
observed at all, so the 40 deselected tests were silently folded into the
"unexecuted" gap, and a completed selection read as `INCOMPLETE`.

The denominator is now taken from `session.items` in `pytest_collection_finish`,
which fires once after *all* collection modification — including deselection —
so it is the effective run set regardless of hook order. Under xdist the
controller collects nothing itself; its denominator still comes from
`pytest_xdist_node_collection_finished`, whose ids are already post-deselection,
and the new hook guards on a non-empty item list so it never zeroes that out on
the controller (acceptance criterion 4). Progress percentages read the same
`self._collected`, so they now use the post-deselection total (criterion 5).

Deselection is also counted for its own sake: a new `pytest_deselected` handler
accumulates the count and the summary reports it alongside the other outcomes —
`PASS exit=0 | 39 passed, 40 deselected` (criterion 2). Because deselected tests
no longer inflate the denominator, `executed < collected` is false for an
intentional selection and the verdict stays `PASS` (criterion 1). Genuine early
exits are unaffected: `INTERRUPTED`, `--maxfail`, `-x`, and
`pytest.exit(returncode=0)` still leave `executed < collected` over the effective
set and still render `INCOMPLETE` (criterion 3), as their regressions confirm.

Regression: a conftest that deselects a marked subset through `pytest_deselected`
now asserts the summary starts `PASS exit=0`, reports `2 passed, 2 deselected`,
and contains no `incomplete`.

