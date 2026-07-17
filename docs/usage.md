# Usage Guide

`pytest-receptor` integrates seamlessly with your standard pytest workflows via the `--receptor` command-line option.

---

## Receptor Profiles (`--receptor`)

### 1. `human` (Default Profile)
This profile preserves pytest's native behavior: colorful progress bars, interactive status indicators, and full traceback code contexts. It is ideal for local human development.
```bash
pytest --receptor=human
```

### 2. `llm` (AI-Optimized Profile)
Optimized for AI coding agents and large language model prompts.
```bash
pytest --receptor=llm
```
**Key features of the `llm` profile:**
* **Silence on success:** Outputs a single clean line: `OK: N passed in X.XXs`.
* **Minified XML payload:** Failure tracebacks and logs are enclosed in semantic tags (e.g., `<failure_group>`, `<message>`, `<captured_stdout>`) with no indentations or decorative line breaks to optimize token counts.
* **Failure deduplication:** Groups identical failures (sharing exception type and message) and lists the associated test names under a single block.
* **Smart fingerprinting:** Strips Hex memory addresses and variable timestamps from messages before grouping, preventing deduplication failure on dynamic data.
* **Local traceback pruning:** Truncates external packages from traceback frames, leaving only your project's files.
* **Adaptive hints:** Detects the dependency manager of the project and suggests the exact install command (e.g., `poetry add` or `uv pip install`) for `ModuleNotFoundError`.

### 3. `ci` (Continuous Integration Profile)
Formated specifically for clean logs in CI/CD pipeline runs:
```bash
pytest --receptor=ci
```
**Key features of the `ci` profile:**
* **Silence on success:** Prints nothing during the run, showing only a final summary line if all tests pass.
* **CI heartbeat progress:** Emits flat progress logs (e.g., `CI Progress: 20% (after 5.0s)`) in 10% increments only if the run exceeds 5 seconds, preventing CI platform timeout flags.
* **Failures-only log:** If a test fails, it prints only the traceback in a flat, clean format without ANSI colors.

---

## Advanced Options

### Token Usage Statistics (`--receptor-stats`)
Calculates the tokens consumed by the default human output compared to the optimized LLM output:
```bash
pytest --receptor=llm --receptor-stats
```
This appends an XML comment at the end:
`<!-- [Receptor Stats] Human: 279 tokens | LLM: 202 tokens | Saved: 27.60% -->`

### Log Auditing Volcado (`--receptor-dump-dir=path`)
Saves a record of the human log and the LLM log for the same test run with unique filenames:
```bash
pytest --receptor=llm --receptor-dump-dir=./test_logs
```
This generates files named `pytest_human_YYYYMMDD_HHMMSS_PID.log` and `pytest_llm_YYYYMMDD_HHMMSS_PID.log`.
