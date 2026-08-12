# Roadmap to the 1.0.0 publication

**Paused:** 2026-08-12

**Release candidate commit:** `4535431`

**Latest published/tagged source release:** `0.7.0`

**Target:** publish the same immutable `1.0.0` source in GitHub, PyPI, and the
`uibcdf` Anaconda.org channel, then verify its automatic discovery by pytest and
eventual inclusion in pytest's community plugin report.

This is the resume point. Do not redo the completed architecture work and do
not publish from an uncommitted tree. Check each box only with the evidence
named beside it.

## Current state at the pause

- [x] The 1.0 release candidate is committed locally as `4535431`.
- [x] The working tree was clean immediately after that commit.
- [x] Serial and xdist suites passed locally.
- [x] Ruff, strict Sphinx, wheel/sdist build, and strict Twine checks passed.
- [x] Package metadata supports exactly Python 3.11, 3.12, and 3.13.
- [x] `pytest11` autoload metadata and `Framework :: Pytest` are declared.
- [x] The GitHub OIDC publication workflow and immutable-release checker exist.
- [x] Changelog and 1.x compatibility contract are prepared for `1.0.0`.
- [ ] Commit `4535431` is pushed to `origin/main`.
- [ ] The complete GitHub Actions matrix is green on that commit.
- [ ] PyPI and GitHub one-time Trusted Publisher setup is complete.
- [ ] `1.0.0` is tagged, released, and published.

## Release invariants

These are stop conditions, not suggestions:

1. One Git commit supplies the GitHub Release, PyPI distributions, and conda
   package. Do not rebuild from a later commit under the same version.
2. The release tree is clean and `python -m versioningit .` returns exactly
   `1.0.0`, with no distance, local, or dirty suffix.
3. Tag `1.0.0` is created only after the candidate commit is on `origin/main`
   and its full CI matrix is green.
4. PyPI publication uses `.github/workflows/release.yml` and OIDC. Do not add a
   long-lived PyPI token.
5. Conda auto-upload stays disabled during the build; inspect the exact package
   before uploading it explicitly to `uibcdf/main`.
6. PyPI distributions and Anaconda.org packages are immutable release outputs.
   A defect gets `1.0.1`; never replace a public `1.0.0` file.

## Phase 1 — publish and validate the candidate commit

- [ ] Confirm the resume state:

  ```bash
  git status --short
  git log -1 --oneline --decorate
  git diff 0.7.0..HEAD --check
  ```

  Expected: clean status and `4535431` at `HEAD`. If documentation-only pause
  commits exist after it, inspect them and treat the final reviewed commit as
  the candidate; do not silently tag an unknown tree.

- [ ] Push `main` without force:

  ```bash
  git push origin main
  ```

- [ ] Wait for every required GitHub Actions job on the candidate SHA:

  - lint;
  - Python 3.11 / pytest 8 and 9, serial and xdist;
  - Python 3.12 / pytest 8 and 9, serial and xdist;
  - Python 3.13 / pytest 8 and 9, serial and xdist;
  - token and performance benchmark harnesses;
  - packaging and clean-wheel pytest discovery;
  - strict documentation build.

- [ ] If CI changes code, create a new commit, push it, and restart this phase.
  Never tag the old candidate after a CI fix.

**Exit evidence:** final candidate SHA recorded here and every required check
green on that SHA.

## Phase 2 — one-time PyPI and GitHub configuration

Complete this before creating the GitHub Release, because publishing that
release triggers the workflow immediately.

- [ ] In GitHub repository settings, create environment `pypi`.
- [ ] Restrict deployment branches/tags appropriately and require manual
  approval from trusted maintainers.
- [ ] In the PyPI account, register this pending Trusted Publisher exactly:

  | Field | Value |
  | :--- | :--- |
  | PyPI project name | `pytest-receptor` |
  | GitHub owner | `uibcdf` |
  | Repository | `pytest-receptor` |
  | Workflow filename | `release.yml` |
  | Environment | `pypi` |

- [ ] Recheck that the PyPI name is still available immediately before
  release. Availability observed on 2026-08-12 was provisional; only the first
  successful upload reserves the name.
- [ ] Confirm no obsolete `PYPI_API_TOKEN` secret is required by the workflow.

A pending publisher can create a new PyPI project on its first successful OIDC
publication and then becomes a normal publisher automatically. There is no need
to perform an insecure manual first upload.

**Exit evidence:** protected GitHub `pypi` environment exists and the pending
publisher values match the table character-for-character.

## Phase 3 — clean release rehearsal and tag

- [ ] From the final candidate commit, rerun the local release gates:

  ```bash
  ruff check pytest_receptor tests devtools docs/conf.py
  ruff format --check pytest_receptor tests devtools docs/conf.py
  pytest -q
  pytest -q -n 2
  sphinx-build -W --keep-going -b html docs docs/_build/html
  python devtools/benchmarks/run_benchmarks.py
  python devtools/benchmarks/run_performance.py
  python -m build
  python -m twine check --strict dist/*
  ```

- [ ] Create the annotated tag on that exact commit:

  ```bash
  git tag -a 1.0.0 -m "pytest-receptor 1.0.0"
  ```

- [ ] Verify the version and release distributions from the tagged tree:

  ```bash
  python -m versioningit .
  git describe --tags --long
  python -m build
  python -m twine check --strict dist/*
  python devtools/check_release.py --tag 1.0.0
  ```

  Expected: `1.0.0`, `1.0.0-0-g<sha>`, exactly one wheel and one sdist,
  version `1.0.0`, and `Requires-Python: >=3.11,<3.14`.

- [ ] Push the tag without force:

  ```bash
  git push origin 1.0.0
  ```

**Exit evidence:** remote annotated tag `1.0.0` resolves to the green candidate
SHA and the release checker accepts distributions built from it.

## Phase 4 — publish 1.0.0 to PyPI

- [ ] Create a GitHub Release for tag `1.0.0`, using the `1.0.0` changelog
  section as release notes.
- [ ] Observe the `Publish release to PyPI` workflow. The build job must:

  - check out the immutable release tag;
  - build one wheel and one sdist;
  - pass strict Twine and tag/metadata validation;
  - install the wheel in a clean environment;
  - prove pytest autoloads `pytest_receptor.plugin`.

- [ ] Review the build job and approve the protected `pypi` environment.
- [ ] Confirm the OIDC publishing job succeeds and creates
  `https://pypi.org/project/pytest-receptor/1.0.0/`.
- [ ] Confirm PyPI shows the expected metadata, files, Python constraint,
  `Framework :: Pytest` classifier, project links, and provenance.

- [ ] Verify from a clean Python 3.11, 3.12, or 3.13 environment:

  ```bash
  python -m venv /tmp/pytest-receptor-pypi
  /tmp/pytest-receptor-pypi/bin/pip install pytest-receptor==1.0.0
  cd /tmp
  /tmp/pytest-receptor-pypi/bin/pytest --trace-config --help 2>&1 \
    | grep 'pytest_receptor.plugin'
  /tmp/pytest-receptor-pypi/bin/pytest --receptor=llm --help >/dev/null
  ```

**Exit evidence:** clean installation comes from PyPI, reports version 1.0.0,
and pytest discovers the plugin through the installed `pytest11` entry point.

## Phase 5 — publish the same 1.0.0 to `uibcdf` conda

Follow `devtools/conda-build/README.md`, with `1.0.0` replacing its historical
0.6 example.

- [ ] Ensure conda build tools are installed and the uploader is authenticated
  for the `uibcdf` Anaconda.org account.
- [ ] Keep automatic upload disabled and build from the checked-out `1.0.0`
  tag:

  ```bash
  git switch --detach 1.0.0
  conda config --set anaconda_upload no
  conda build devtools/conda-build
  ```

- [ ] Confirm the recipe tests pass and inspect the one `noarch` output:

  ```bash
  conda build devtools/conda-build --output
  ```

  Expected version: `1.0.0`; build: `py_0`; runtime constraint:
  `python >=3.11,<3.14`; dependency: `pytest >=8.0.0`.

- [ ] Upload that exact file explicitly:

  ```bash
  CONDA_PACKAGE=$(conda build devtools/conda-build --output)
  anaconda upload --user uibcdf "$CONDA_PACKAGE" --label main
  ```

- [ ] Verify channel metadata and a clean install:

  ```bash
  conda search -c uibcdf --override-channels pytest-receptor=1.0.0
  conda create -n pytest-receptor-verify \
    -c uibcdf -c conda-forge pytest-receptor=1.0.0 python=3.13
  conda run -n pytest-receptor-verify \
    pytest --trace-config --help 2>&1 | grep 'pytest_receptor.plugin'
  ```

- [ ] Return to `main` and clean conda build intermediates:

  ```bash
  git switch main
  conda build purge
  ```

**Exit evidence:** Anaconda.org `uibcdf/main` exposes the `noarch` 1.0.0
package and a clean solver/install loads it as a pytest plugin.

## Phase 6 — verify automatic community listing

The official pytest plugin report is an automated, informational compilation
of public PyPI projects whose names begin with `pytest-` or `pytest_`, excluding
projects classified as inactive. `pytest-receptor` satisfies the name rule.
There is no manual listing request and no requirement to move the repository to
the `pytest-dev` organization.

- [ ] After PyPI publication, wait for the external pytest index refresh.
  Do not treat immediate absence as a release failure; its schedule is not under
  this repository's control.
- [ ] Search the official report for `pytest-receptor`:
  <https://docs.pytest.org/en/stable/reference/plugin_list.html>.
- [ ] Verify the row links to the correct PyPI project and shows plausible
  summary, release date, status, and requirements.
- [ ] If the project remains absent after a reasonable refresh window, inspect
  the plugin-list update script and PyPI metadata/inactivity classification
  before opening an upstream issue. Do not request manual inclusion first.

**Exit evidence:** `pytest-receptor` appears in pytest's generated plugin report
and its row resolves to the public PyPI release.

## Phase 7 — close and communicate the release

- [ ] Update installation documentation from “planned” to published for both
  `pip install pytest-receptor` and `conda install -c uibcdf pytest-receptor`.
- [ ] Record PyPI, Anaconda.org, GitHub Release, CI run, and pytest plugin-list
  links in this document.
- [ ] Mark the 1.0 readiness dashboard published and open a fresh post-1.0
  section for adoption monitoring; do not continue using this release checklist
  as the general backlog.
- [ ] Publish a brief user announcement emphasizing automatic pytest discovery,
  Python 3.11–3.13 support, and unchanged plain-pytest behavior.

## Publication record

Fill this only after the facts exist:

| Evidence | URL or value |
| :--- | :--- |
| Final release commit | pending |
| GitHub CI run | pending |
| GitHub Release 1.0.0 | pending |
| PyPI 1.0.0 | pending |
| PyPI provenance | pending |
| Anaconda.org `uibcdf` 1.0.0 | pending |
| pytest community plugin report | pending |

## Verified upstream mechanisms

Checked again on 2026-08-12:

- pytest's plugin report is automatically compiled from eligible PyPI project
  names and is informational, not an endorsement;
- PyPI pending Trusted Publishers can create a project on first OIDC use;
- PyPA recommends short-lived OIDC Trusted Publishing for GitHub Actions and a
  manually protected `pypi` environment;
- conda-build produces the output path and supports explicit later upload to
  Anaconda.org when automatic upload is disabled.

Primary references:

- <https://docs.pytest.org/en/stable/reference/plugin_list.html>
- <https://docs.pytest.org/en/stable/how-to/writing_plugins.html#making-your-plugin-installable-by-others>
- <https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/>
- <https://docs.pypi.org/trusted-publishers/using-a-publisher/>
- <https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/>
- <https://docs.conda.io/projects/conda-build/en/stable/user-guide/tutorials/building-conda-packages.html>
