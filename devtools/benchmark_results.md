# pytest-receptor Tokenizer Benchmark Results

This report benchmarks the token savings achieved by `pytest-receptor`'s LLM reporter compared to pytest's standard human-readable reporter across multiple popular tokenizer families.

| Suite Name | Tokenizer | Human Tokens | LLM Tokens | Savings % |
|---|---|---|---|---|
| Green Suite (10 passed) | cl100k_base (GPT-4/3.5) | 96 | 32 | 66.67% |
|  | o200k_base (GPT-4o) | 98 | 32 | 67.35% |
|  | p50k_base (Codex) | 109 | 33 | 69.72% |
|  | r50k_base (GPT-3/2) | 124 | 33 | 73.39% |
| | | | | |
| Red Suite (1 failed) | cl100k_base (GPT-4/3.5) | 188 | 131 | 30.32% |
|  | o200k_base (GPT-4o) | 192 | 132 | 31.25% |
|  | p50k_base (Codex) | 220 | 156 | 29.09% |
|  | r50k_base (GPT-3/2) | 268 | 156 | 41.79% |
| | | | | |
| Warnings Suite | cl100k_base (GPT-4/3.5) | 222 | 127 | 42.79% |
|  | o200k_base (GPT-4o) | 225 | 128 | 43.11% |
|  | p50k_base (Codex) | 268 | 149 | 44.40% |
|  | r50k_base (GPT-3/2) | 296 | 149 | 49.66% |
| | | | | |
| Mixed States Suite | cl100k_base (GPT-4/3.5) | 109 | 97 | 11.01% |
|  | o200k_base (GPT-4o) | 116 | 96 | 17.24% |
|  | p50k_base (Codex) | 125 | 117 | 6.40% |
|  | r50k_base (GPT-3/2) | 146 | 117 | 19.86% |
| | | | | |
| Multiple Failures Suite | cl100k_base (GPT-4/3.5) | 283 | 220 | 22.26% |
|  | o200k_base (GPT-4o) | 283 | 222 | 21.55% |
|  | p50k_base (Codex) | 356 | 268 | 24.72% |
|  | r50k_base (GPT-3/2) | 424 | 268 | 36.79% |
| | | | | |
| Cascade Failures (20 error) | cl100k_base (GPT-4/3.5) | 1881 | 339 | 81.98% |
|  | o200k_base (GPT-4o) | 1907 | 359 | 81.17% |
|  | p50k_base (Codex) | 2338 | 400 | 82.89% |
|  | r50k_base (GPT-3/2) | 2743 | 400 | 85.42% |
| | | | | |
