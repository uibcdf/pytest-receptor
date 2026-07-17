# pytest-receptor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![Pytest Version](https://img.shields.io/badge/pytest-%3E%3D8.0.0-green)](https://docs.pytest.org/)

`pytest-receptor` is a pytest plugin designed for the AI era. It introduces the concept of a **Receptor (Consumer Profile)** to decouple the test execution engine from how results are visually reported. This optimizes information density and dramatically reduces context token consumption for AI Agents (such as Claude Code, Aider, Codex) and Continuous Integration (CI/CD) environments.

---

## 🚀 Key Features

* **`--receptor=llm` (AI-Optimized Mode):**
  * **Silence on success:** If all tests pass, it outputs a single summary line: `OK: 42 passed in 1.23s`.
  * **Deduplication (Dumping):** Automatically groups multiple failures sharing the same exception type and error message under a single `<failure_group>` tag.
  * **Smart Fingerprinting (Sanitización):** Strips hexadecimal memory addresses (`0x...`) and dynamic timestamps from errors before grouping, ensuring identical failures consolidate perfectly.
  * **Simplified Tracebacks:** Omits redundant source code from tracebacks (which the AI already has in its indexed file context) and filters out external dependency frames in `site-packages`, keeping only local frames.
  * **Adaptive Hints:** Detects if your project uses Poetry, UV, PDM, or Pipenv, and suggests the exact command to install missing dependencies (e.g., `<hint>poetry add requests</hint>`).
  * **Diff Compression:** Automatically truncates massive assertion diffs to a maximum of 1500 characters to prevent context window saturation.

* **`--receptor=ci` (Silent-on-Success for CI/CD):**
  * **Absolute silence on green:** Does not generate interactive CLI progress or characters. If the suite passes, it only prints `CI: N passed in Xs`.
  * **Failures-only on red:** Prints only clean, flat tracebacks and diffs of the failed tests (without redundant ANSI colors).
  * **CI Heartbeat (Anti-Timeout):** In slow-running suites taking more than 5 seconds, it emits a flat progress heartbeat every 5 seconds to keep the CI/CD job active (e.g., `CI Progress: 45% (after 5.2s)`).

* **Performance Reporting (Slow Tests):**
  * At the end of execution, it reports the top 3 slowest tests exceeding a threshold of **0.5s** in both `llm` and `ci` modes.

* **Audit and Stats Tools:**
  * **`--receptor-stats`:** Appends a comment comparing the tokens consumed by the classic terminal report vs. the optimized LLM output.
  * **`--receptor-dump-dir=path`:** Saves parallel copies of both reports to disk (`pytest_human_*.log` and `pytest_llm_*.log`) signed with timestamp and PID.

---

## 📊 Token Savings Benchmarks (tiktoken: cl100k_base)

| Scenario / Casuistry | Human Output (Tokens) | LLM Output (Tokens) | Average Savings (%) |
| :--- | :---: | :---: | :---: |
| **Warnings** (Silenced deprecation warnings) | 198 | 12 | **93.94%** |
| **Green Suite** (All tests passed) | 99 | 12 | **87.88%** |
| **Cascade Failures** (Fixture failure across 20 tests) | 1864 | 303 | **83.74%** |
| **Mixed States** (Skipped, xfail, xpass) | 118 | 26 | **77.97%** |
| **Red Suite** (Single assertion failure) | 312 | 163 | **47.76%** |
| **Multiple Failures** (Setup + Call) | 269 | 185 | **31.23%** |
| **Collection Error** (Import error during discovery) | 279 | 202 | **27.60%** |

---

## 🛠️ Installation

Install `pytest-receptor` using `pip` or your favorite dependency manager:

```bash
pip install pytest-receptor
```

To install from source for local development:

```bash
git clone https://github.com/uibcdf/pytest-receptor.git
cd pytest-receptor
pip install -e .[dev]
```

---

## 📖 Usage

Activate the plugin using the `--receptor` option in your pytest command:

### 1. Default Human-Friendly Output
```bash
pytest --receptor=human
```

### 2. Token-Optimized XML Output for LLM Agents
```bash
pytest --receptor=llm
```

### 3. Flat and Clean Output for Continuous Integration
```bash
pytest --receptor=ci
```

### 4. Show Token Statistics
```bash
pytest --receptor=llm --receptor-stats
```

### 5. Dump Auditor Logs to a Folder
```bash
pytest --receptor=llm --receptor-dump-dir=./test_logs
```

---

## 🛡️ License

This project is licensed under the MIT License. See the [LICENSE](file:///home/diego/repos@uibcdf/pytest-receptor/LICENSE) file for details.