# `pytest-receptor` Documentation

Welcome to the official documentation for `pytest-receptor`, the pytest plugin designed for the AI era and agentic-driven development workflows.

---

## What is `pytest-receptor`?

`pytest-receptor` introduces the concept of a **Receptor (Consumer Profile)** to pytest. It decouples the core test runner from its visual reporting backend. This allows formatting test execution logs and failure tracebacks differently depending on *who* is consuming the outputs (a human developer, an autonomous AI agent, or a CI/CD build machine).

```{toctree}
---
maxdepth: 2
caption: "Contents:"
---
installation
usage
benchmarks
```

---

## Features at a Glance

* **`--receptor=human` (Default):** Classic, colorful, and interactive output for human developers.
* **`--receptor=llm`:** Densely packed, minified XML designed for AI prompt contexts, featuring de-duplication, smart fingerprinting, local traceback pruning, and repair suggestions.
* **`--receptor=ci`:** Flat, silent-on-success output with time-based heartbeat progress lines to prevent CI/CD VM timeouts.
* **Performance Reporting:** Automatic tracking and reporting of the top 3 slowest tests taking more than 0.5s.
