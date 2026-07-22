# External single-test rerun loses its file path when rootdir is fixed

**Observed:** 2026-07-22  
**Consumer:** MolSysMT  
**pytest-receptor:** `ad610e6` (`0.6.0`)  
**Severity:** medium — a rendered rerun command is not executable

## Summary

The new `receptor_rerun_command` setting works for ordinary tests inside the
project. A separate path edge remains when pytest is given both a fixed project
configuration/rootdir and a single test outside that rootdir. Pytest 9 reports
that item's node ID as only `::test_name`, with no file component. Receptor
passes that incomplete node ID through `_selector`, producing a rerun command
whose selection begins with `::` and cannot be executed.

This was found while re-running MolSysMT's controlled-incomplete pilot fixture
from `/tmp` under the actual MolSysMT `pytest.ini`.

## Reproducer

MolSysMT configures:

```ini
[pytest]
receptor_rerun_command = python -m pytest
```

With a failing external test at
`/tmp/molsysmt_receptor_regression/test_failure_cascade.py`, run from the
MolSysMT repository:

```bash
python -m pytest -c pytest.ini --receptor=llm \
  /tmp/molsysmt_receptor_regression/test_failure_cascade.py::test_distinct_numeric_failure_35
```

Receptor renders the correct absolute failure location but this rerun line:

```text
rerun: python -m pytest ::test_distinct_numeric_failure_35 -q
```

Copying it verbatim returns exit 4:

```text
ERROR: directory argument cannot contain :: selection parts: ::test_distinct_numeric_failure_35
```

Pytest exposes the underlying edge directly:

```bash
python -m pytest -c pytest.ini --collect-only -o addopts='' -q \
  /tmp/molsysmt_receptor_regression/test_failure_cascade.py::test_distinct_numeric_failure_35
```

prints:

```text
::test_distinct_numeric_failure_35
```

The receptor nevertheless knows the file from the report location, which it
renders as:

```text
/tmp/molsysmt_receptor_regression/test_failure_cascade.py:15
```

## Scope

- An ordinary failing test inside MolSysMT correctly renders, for example:

  ```text
  rerun: python -m pytest tests/_private/test_receptor_rerun_probe.py::test_configured_rerun_command_probe -q
  ```

- The configured runner prefix is therefore working.
- The defect is the missing file component in an external single occurrence
  when pytest's node ID is pathless under a forced rootdir.
- Multi-occurrence groups may follow a different branch (`files = ...`) and
  should be tested independently.

## Acceptance criteria

- A single failing test outside rootdir, invoked with `-c <project pytest.ini>`,
  receives a rerun command containing its resolvable absolute path and test
  selector.
- Copying the rendered command from the original invocation directory selects
  exactly that test (its expected assertion failure is exit 1, not usage exit
  4).
- The behavior works with the default runner and with a multi-token configured
  runner such as `python -m pytest` or `uv run pytest`.
- Add subprocess regressions for single and grouped external occurrences under
  an explicitly fixed project rootdir.

---

## Resolution

**Fixed 2026-07-22 (PR-PILOT-012).** The receptor already knew the file — it
renders it as the failure location — but `_selector` built the rerun selection
from the node ID alone, so a pathless `::test_name` produced a pathless `::`
selection. The rerun and the listed test IDs now recover the file from the
occurrence's location (`<file>:<lineno>`) whenever the node ID has no path, both
for a single occurrence (`<file>::<test>`) and for a grouped one (the bare
`<file>` branch). An ordinary in-rootdir test is unchanged, since its node ID
already carries the path.

Verified against the reproducer: `-c <ini>` with a single failing test outside
rootdir now yields `rerun: python -m pytest outside/test_ext.py::test_x -q`,
executable from the invocation directory. Subprocess regressions cover the single
and grouped external cases under a forced rootdir.
