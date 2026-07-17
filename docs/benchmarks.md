# Benchmarks and Token Savings

To quantitatively measure the efficiency of the `llm` profile, the plugin features a benchmark suite comparing token counts using OpenAI's `cl100k_base` tokenizer (used by GPT-4 and compatible models).

---

## Token Comparison Results

The following table details the measured token usage across different common testing scenarios:

| Scenario / Casuistry | Human Output (Tokens) | LLM Output (Tokens) | Average Savings (%) |
| :--- | :---: | :---: | :---: |
| **Warnings** (Silenced deprecation warnings) | 198 | 12 | **93.94%** |
| **Green Suite** (Standard successful run) | 99 | 12 | **87.88%** |
| **Cascade Failures** (Common fixture failure in 20 tests) | 1864 | 303 | **83.74%** |
| **Mixed States** (Skipped, xfail, xpass) | 118 | 26 | **77.97%** |
| **Red Suite** (Single assertion failure) | 312 | 163 | **47.76%** |
| **Multiple Failures** (Fixture + test failure) | 269 | 185 | **31.23%** |
| **Collection Error** (Discovery/Import error) | 279 | 202 | **27.60%** |

---

## Quantitative Analysis

* **Success (Savings > 85%):** During standard development (where tests pass most of the time), removing CLI environment headers and test lists cuts almost 90% of token weight, allowing faster response loops from your LLM agent.
* **Cascade Failures (Savings > 80%):** Grouping failures and using short test names prevents repeating identical tracebacks dozens of times, saving thousands of tokens and preventing agent context blindness.
* **Assertion Failures (Savings > 45%):** Omitting the test's source code (since the agent already has your project files in its workspace context) yields a 47% reduction, reporting only the essential assertion diffs.
