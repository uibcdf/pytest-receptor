# Setup Errors Are Counted as Failed Tests

**Reported:** 2026-07-18  
**Priority:** Urgent outcome/count disagreement with pytest  
**Pilot:** MolSysMT shadow evaluation

## Summary

Pytest reports a parametrized fixture cascade as `20 errors`, while
pytest-receptor 0.6.0 renders `20 failed`. Both retain exit code 1, and the
receptor correctly identifies the occurrences as setup-phase failures, but its
headline changes pytest's result category.

This reproduces both serially and with twelve xdist workers. It is an urgent
pilot finding because the documented reliability contract requires result
counts to agree with pytest.

## Environment

- Python 3.13.12
- pytest 9.0.2
- pytest-receptor 0.6.0, editable installation
- MolSysMT `pytest.ini` addopts:
  `--doctest-modules -q --import-mode=importlib`

## Reproducer

The temporary test contains one fixture that raises while constructing a
MolSysMT object and twenty parametrized consumers:

```python
import pytest
import molsysmt as msm


@pytest.fixture
def broken_system():
    return msm.MolSys(n_atoms=2)


@pytest.mark.parametrize("case_index", range(20))
def test_requires_system(broken_system, case_index):
    assert case_index >= 0
```

Distributed authoritative command:

```text
python -m pytest -q -n 12 /tmp/molsysmt_receptor_pilot/test_fixture_cascade.py
```

Pytest exits with status 1 and ends with:

```text
20 errors in 2.44s
```

Distributed receptor command:

```text
python -m pytest --receptor=llm --receptor-stats -n 12 /tmp/molsysmt_receptor_pilot/test_fixture_cascade.py
```

Pytest-receptor also exits with status 1 but renders:

```text
FAIL exit=1 | 20 failed | 2.38s | 1 root cause

[1] AttributeError | 20 tests | setup
    molsysmt/molsysmt/__init__.py:131
    AttributeError: module 'molsysmt' has no attribute 'MolSys'
    frames: test_fixture_cascade.py:9 -> molsysmt/__init__.py:131
    tests:
      test_fixture_cascade.py::test_requires_resolved_chemistry[0]
      test_fixture_cascade.py::test_requires_resolved_chemistry[1]
      test_fixture_cascade.py::test_requires_resolved_chemistry[2]
      +17 more
    rerun: pytest test_fixture_cascade.py -q
```

The same mismatch reproduces with `-n 0`: pytest reports `20 errors in 0.56s`,
while the receptor reports `FAIL exit=1 | 20 failed | 0.56s`.

## Expected behavior

The headline should preserve pytest's category, for example:

```text
FAIL exit=1 | 20 errors | 2.38s | 1 root cause
```

If a run contains call-phase failures and setup/teardown errors together, the
headline should expose both counts rather than folding every unsuccessful test
into `failed`.

## Impact

- An agent receives the correct nonzero verdict but an incorrect test-state
  summary.
- The inconsistency is visible inside the same report: the headline says
  `failed`, while the group says `setup`.
- Setup cascades are a primary use case advertised by the plugin, so this can
  affect the highest-value compression scenario.
- Downstream comparisons or future machine-readable consumers could treat a
  failure as an assertion/code failure rather than fixture or infrastructure
  failure.

## What worked

The grouping itself was correct and diagnostically sufficient: one root cause,
the decisive local and MolSysMT frames, representative node IDs, the complete
occurrence count, and a usable rerun command. The distributed run compressed
from approximately 7,550 tokens to 131 (98.3%) without changing exit code.

## Requested regression coverage

Cover serial and xdist runs containing:

- setup errors only;
- teardown errors only;
- call failures only;
- mixed setup errors and call failures;
- mixed errors, failures, skips, and xfails.

Assert parity with pytest's category counts as well as the exit code and total
number of affected node IDs.
