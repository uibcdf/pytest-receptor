# Xdist mixed valid and missing paths hide the usage error

Observed from a real MolSysMT development cycle on 2026-08-11.

## Environment

- pytest 9.1.1
- pytest-receptor 0.6.0 from the editable sibling checkout
- pytest-xdist enabled
- Python 3.13

## Reproduction

The first path exists and contains two tests. The second path does not exist.

```bash
python -m pytest --receptor=llm -n 2 \
  tests/form/test_converter_imports_resolve.py tests/basic/extract
```

The complete stdout report, and the complete disk report in
`.pytest_cache/d/receptor/last-run.txt`, are both:

```text
NO_TESTS exit=5 | 1.69s
```

Plain pytest agrees on exit code 5 under xdist, but is also silent apart from xdist startup:

```bash
python -m pytest -q -n 2 \
  tests/form/test_converter_imports_resolve.py tests/basic/extract
```

```text
bringing up nodes...
bringing up nodes...
```

The serial receptor run diagnoses the actual invocation error correctly:

```bash
python -m pytest --receptor=llm tests/basic/extract
```

```text
USAGE_ERROR exit=4 | 0.02s

ERROR: file or directory not found: tests/basic/extract
```

The original field command used `-n 12`, several valid test paths, and the same invalid
path. It produced `NO_TESTS exit=5`; the smaller `-n 2` reproducer above preserves the
defect.

## Why this is a receptor defect

There is no receptor/pytest verdict disagreement, but the compact output was not sufficient
to act on. A valid test file was present, so `NO_TESTS` suggested a collection or marker
problem rather than naming the malformed path. Diagnosing it required inspecting the test
tree and rerunning a corrected command. The disk artifact contains no additional evidence.

Plain pytest being equally unhelpful under xdist does not satisfy the receptor's stated
criterion: the machine-oriented report should contain what an agent needs to correct the
run. The serial behavior proves the useful cause exists at the invocation boundary.

## Expected behavior

When xdist receives a mixture of valid and nonexistent selection paths, the final report
should name every nonexistent path and distinguish an invalid invocation from a genuinely
empty effective selection. If pytest exposes no collection diagnostic in this mode, the
receptor may need to validate explicit filesystem selection arguments or retain controller
collection evidence before xdist converts the outcome to exit 5.

The pytest exit code must remain authoritative; this report does not request changing it.

---

## Resolution

**Fixed 2026-08-12 as PR-PILOT-015.** The controller retains the parsed
filesystem collection targets in `config.args`, even though it delegates
collection to xdist workers. The receptor now validates those already-parsed
targets against `invocation_params.dir`. It does not parse the raw command line,
so option values cannot be mistaken for paths, and it leaves `--pyargs` module
resolution to pytest.

When pytest/xdist returns exit 5 and one or more explicit filesystem targets do
not exist, the report now reads:

```text
USAGE_ERROR exit=5 | invalid selection | 0.47s

invalid selection:
  file or directory not found: missing_one
  file or directory not found: missing_two/test_file.py
```

The numeric exit status remains pytest's original 5. A genuinely empty existing
target still renders `NO_TESTS exit=5`, so the refinement does not reclassify an
empty suite without concrete invalid-selection evidence. The same diagnostic is
written to the full report.

Regressions cover a mixed valid/two-missing-path xdist invocation, preservation
of exit 5, both missing paths on stdout and disk, and a genuinely empty existing
file remaining `NO_TESTS`.
