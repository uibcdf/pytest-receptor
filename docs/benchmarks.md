# Benchmarks and Token Savings

To quantitatively measure the efficiency of the `llm` profile, the plugin features a benchmark suite comparing token counts across multiple popular tokenizer families.

---

## Token Comparison Results (Multi-Tokenizer)

The following table details the measured token usage and savings across different common testing scenarios using different encoding families:

| Suite Name | Tokenizer | Human Tokens | LLM Tokens | Savings % |
|---|---|---|---|---|
| Green Suite (10 passed) | cl100k_base (GPT-4/3.5) | 94 | 32 | 65.96% |
|  | o200k_base (GPT-4o) | 98 | 32 | 67.35% |
|  | p50k_base (Codex) | 107 | 33 | 69.16% |
|  | r50k_base (GPT-3/2) | 122 | 33 | 72.95% |
| | | | | |
| Red Suite (1 failed) | cl100k_base (GPT-4/3.5) | 192 | 131 | 31.77% |
|  | o200k_base (GPT-4o) | 196 | 132 | 32.65% |
|  | p50k_base (Codex) | 228 | 156 | 31.58% |
|  | r50k_base (GPT-3/2) | 276 | 156 | 43.48% |
| | | | | |
| Warnings Suite | cl100k_base (GPT-4/3.5) | 226 | 127 | 43.81% |
|  | o200k_base (GPT-4o) | 229 | 128 | 44.10% |
|  | p50k_base (Codex) | 268 | 149 | 44.40% |
|  | r50k_base (GPT-3/2) | 296 | 149 | 49.66% |
| | | | | |
| Mixed States Suite | cl100k_base (GPT-4/3.5) | 109 | 97 | 11.01% |
|  | o200k_base (GPT-4o) | 112 | 96 | 14.29% |
|  | p50k_base (Codex) | 121 | 117 | 3.31% |
|  | r50k_base (GPT-3/2) | 142 | 117 | 17.61% |
| | | | | |
| Multiple Failures Suite | cl100k_base (GPT-4/3.5) | 295 | 220 | 25.42% |
|  | o200k_base (GPT-4o) | 295 | 222 | 24.75% |
|  | p50k_base (Codex) | 374 | 268 | 28.34% |
|  | r50k_base (GPT-3/2) | 442 | 268 | 39.37% |
| | | | | |
| Cascade Failures (20 error) | cl100k_base (GPT-4/3.5) | 1923 | 339 | 82.37% |
|  | o200k_base (GPT-4o) | 1907 | 359 | 81.17% |
|  | p50k_base (Codex) | 2422 | 400 | 83.48% |
|  | r50k_base (GPT-3/2) | 2827 | 400 | 85.85% |
| | | | | |

---

## Quantitative Analysis

* **High Savings on Cascade Failures (Savings > 80%):** Grouping identical failures and showing short test names prevents repeating duplicate tracebacks many times. This saves thousands of tokens on large suites and keeps the LLM's context window clean.
* **Significant Savings on Green Runs (Savings > 65%):** Successful development runs (where tests pass) omit verbose terminal lists, resulting in up to 72% savings depending on the tokenizer encoding.
* **Assertion and Warnings (Savings > 25-45%):** Pruning verbose terminal headers and de-duplicating warnings by category achieves clean, readable output for LLM consumption while preserving exact source files and line locations.

To regenerate these benchmarks locally, run the script:
```bash
python devtools/benchmark_tokenizers.py
```
