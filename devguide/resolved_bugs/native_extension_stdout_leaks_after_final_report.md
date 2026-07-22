# Native-Extension Stdout Leaks After the Final Report

## Status

Confirmed during a real MolSysMT development cycle on 2026-07-21.

## Evidence

The command was:

```text
python -m pytest --receptor=llm tests/conversion_truth \
  devtools/tests/test_validate_form_adapters.py tests/basic/convert
```

Receptor correctly reported:

```text
PASS exit=0 | 117 passed | 126.45s | 2 warnings
```

After the warning and slowest sections, stdout still contained one stray `s`
line and many repetitions of native DCD plugin messages such as:

```text
dcdplugin) detected standard 32-bit DCD file of native endianness
dcdplugin) CHARMM format DCD file (also NAMD 2.1 and later)
```

The same DCD output was observed after a smaller successful conversion-truth
run. It appears to be emitted by a native extension rather than by Python's
warnings or logging machinery.

## Impact

- Compact stdout is not bounded by receptor's own report policy.
- The authoritative final summary is no longer the final visible output.
- A native library can dominate an otherwise compact report.
- An agent must distinguish post-summary dependency noise from evidence that
  pytest or receptor continued running incorrectly.

The pytest result itself remained correct. This is an output sufficiency and
ordering defect, not a result disagreement.

## Acceptance criteria

- Establish whether the text is written through Python streams or directly to
  process file descriptors.
- Keep native dependency chatter out of compact stdout when technically safe,
  or document a deliberate limitation and preserve it in the disk artifact.
- Ensure the receptor summary remains the final machine-oriented stdout block.
- Add a regression using a subprocess or native-like file-descriptor writer;
  Python-only `print()` coverage is not sufficient for this failure mode.
- Preserve raw evidence if suppression or capture fails.

---

## Resolution

**Fixed 2026-07-21.** The text is written to the process's stdout **file
descriptor** through C stdio, not Python's streams: the reproduction is a
`libc.printf` from a passing test. Under pytest's default fd capture, fd 1 is
redirected to a file, which makes libc's stdout *fully* buffered; nothing flushes
it until the C runtime does so at process exit, by which point pytest has
restored the terminal and the receptor's report is already printed. Hence the
trailing banners, and the lone `s` — a buffer boundary.

The fix flushes libc's buffers (`fflush(NULL)`) at every test teardown, while
that test's capture is still in place, so the native output lands in the capture
and is dropped on a pass (or kept as captured stdout on a failure) rather than
leaking. The receptor summary is once more the only machine-oriented block on
stdout, serial and under xdist, where the flush runs in each worker. The disk
artifact was already bounded and is unaffected.

Regression: a passing test issues real `libc.printf` writes in a subprocess run;
the report must be `PASS` and no `dcdplugin` text may reach stdout. Python-level
`print()` would not exercise this path, as the acceptance criteria noted.

The flush is best-effort: on a platform with no C library handle it is a no-op,
and output from a library that cached the terminal fd *before* capture began, or
that writes after the last teardown, stays outside any Python reporter's reach —
that residue is the documented limitation, with the bounded artifact as fallback.
