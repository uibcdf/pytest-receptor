# MolSysMT Real Development Cycle: PDB Connectivity

## Context

MolSysMT used pytest-receptor in shadow mode during a real PDB fidelity change,
not a synthetic receptor scenario. The new regression exercised canonical PDB
serial numbering, atom and model subsets, occupancy, B factors, and `CONECT`
round trips.

## Failure report

The focused run reported one root cause:

```text
FAIL exit=1 | 1 failed, 1 passed | 5.01s | 1 root cause

[1] AssertionError | 1 test | call
    tests/conversion_truth/test_pdb_fidelity.py:66
    assert [] == [[0, 1]]

    rerun: pytest tests/conversion_truth/test_pdb_fidelity.py::test_native_pdb_roundtrip_uses_canonical_serials_and_preserves_scalar_fields -q
```

## Was the output sufficient?

Yes. The receptor output alone identified that the expected PDB bond vanished
on round trip and pointed to the exact assertion. We did not consult ordinary
pytest output or receptor's full disk artifact. Inspection could begin directly
at the PDB parser boundary.

The cause was that MolSysMT's topology parser stopped scanning at the first
`ENDMDL`, so it never reached global `CONECT` records written after the model
block. The fix keeps ignoring coordinate records after the first model while
continuing to scan global topology records. The exact receptor rerun then
passed.

## Follow-up runs

Two broader receptor runs also completed successfully:

- 435 PDB and conversion-contract tests passed in 141.76 seconds;
- 373 string-PDB, handler, and fidelity tests passed in 123.51 seconds.

Progress output remained bounded, monotonic, and useful throughout both runs.
This cycle is positive evidence that the compact report can be sufficient for
ordinary diagnosis and repair, while pytest remains the result authority.
