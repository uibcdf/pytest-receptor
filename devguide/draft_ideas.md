# Development Guide: `pytest-receptor`

## 1. The Why (The Vision)

The software development ecosystem is undergoing a paradigm shift. It is increasingly common for `pytest` to be executed not by a human in their terminal, but by **AI Agents and LLM-native CLIs** (such as Claude Code, Codex CLI, Aider, or autonomous TDD loops).

### The Current Problem

`pytest` was designed at its core for human eyes. Its standard output (`stdout`) includes progress bars, visual decorations (`====`), ANSI colors, and redundant source code blocks in *tracebacks*.

* For a human, this is visual ergonomics.
* For a Language Model (LLM), this is **semantic noise and a massive waste of context tokens**, increasing the cost and latency of the development loop.

On the other hand, current "tricks" like `--tb=line -q` shorten the text but **blind the agent**, as they remove critical structural details (such as complex diffs of dictionaries or objects that failed in an `assert`), causing the AI to hallucinate corrections in loops.

---

## 2. The What (The Goal)

The goal of `pytest-receptor` is to introduce the concept of a **Receptor (Consumer Profile)** to the Python testing ecosystem. We want to decouple the internal execution logic of tests from the cosmetic way they are reported, optimizing the output based on *who* will digest the information.

The plugin exposes a new CLI flag:

```bash
pytest --receptor=[human|llm|ci]
```

* **`--receptor=human` (Default):** Preserves pytest's classic, visual, and user-friendly behavior.
* **`--receptor=llm`:** An output designed purely for Transformer architectures. It aims for maximum **semantic information density** at the lowest possible token cost.
* **`--receptor=ci`:** A clean and flat output optimized for traditional log engines (Jenkins, GitHub Actions) without interactive animations.

---

## 3. The How (Initial Implementation Ideas)

To build the `--receptor=llm` variant in a solid and efficient way, we base it on the following technical pillars:

### A. Efficient Output Heuristics

* **Silence on Success (Green Suite):** If all tests pass, no files or environments are listed. The plugin responds with a single atomic string: `OK: 42 passed in 1.4s`. Zero tokens wasted on successful regressions.
* **Mutilating Redundant Code:** In case of failure, we **do not** print the surrounding source code lines of the exception. The AI agent already has the source files indexed in its workspace context; printing the code back into `stdout` is pure redundancy.

### B. Semantic Density via Minified XML/Markdown

Instead of formatting tables or dashes (`----`), we wrap failures in lightweight structural tags (e.g., `<test_failures>`, `<failure_group>`). Modern language models have been heavily trained on web data (HTML/XML); their attention mechanisms identify and process the boundaries of these tags with drastically less context noise than arbitrary plain text.

### C. Injection Strategy via Hooks

We will not clean the text using string post-processing (which wastes CPU cycles). Instead, we intercept the `pytest` lifecycle using its native hooks:

1. Use `pytest_addoption` to register the flag.
2. Intercept `TerminalReporter` in `pytest_configure`.
3. Override or short-circuit `pytest_runtest_logreport` when `--receptor=llm` is active, extracting the raw attributes of `ExceptionInfo` (`err.type`, `err.value`, and the exact frame location) to serialize them directly into our token-optimized format.
