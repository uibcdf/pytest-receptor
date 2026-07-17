# Installation

This page guides you through installing and configuring `pytest-receptor` for your project.

---

## Prerequisites

`pytest-receptor` requires:
* **Python:** Version `>= 3.11` (with full support up to Python `3.13`).
* **Pytest:** Version `>= 8.0.0`.

---

## Installing Stable Releases (PyPI)

To install the latest stable version of the plugin from the Python Package Index (PyPI):

```bash
pip install pytest-receptor
```

Alternatively, add the package to your development dependencies using your preferred package manager:

* **Poetry:**
  ```bash
  poetry add --group dev pytest-receptor
  ```
* **Pipenv:**
  ```bash
  pipenv install --dev pytest-receptor
  ```
* **PDM:**
  ```bash
  pdm add -d pytest-receptor
  ```
* **UV:**
  ```bash
  uv pip install pytest-receptor
  ```

---

## Installing from Source (Development)

If you wish to clone the repository to contribute or test local changes:

1. Clone the repository from GitHub:
   ```bash
   git clone https://github.com/uibcdf/pytest-receptor.git
   cd pytest-receptor
   ```

2. Install in editable mode along with the development dependencies (`dev`):
   ```bash
   pip install -e .[dev]
   ```
