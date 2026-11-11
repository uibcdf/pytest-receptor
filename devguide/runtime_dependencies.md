# Runtime dependency floors

Owner review: uibcdf/pytest-receptor#49, under uibcdf/molsyssuite#137.
Reviewed source baseline acd8897f593fd11ec676c2b960fe53b9e699f5e6 plus the
1.2.3 changes tracked in uibcdf/pytest-receptor#52.

## Required runtime

The sole external runtime is **pytest>=8.0.0**. It supplies Config/UsageError,
ExitCode, public collection/runtest/session hooks and hook wrappers, reporting
objects and terminal-writer access. Python standard-library modules supply
all other shipped behavior. Version 8.0.0 is the reviewed and executed API
baseline; this is not a claim that every individual API was introduced in 8.
The human passthrough and compact collectors share this requirement.

The same inclusive floor appears in pyproject.toml, the noarch recipe's run
requirements and the maintained historical Python 3.13 runtime environment.
No runtime upper bound or exclusion exists. Python >=3.11,<3.15 is separately
governed. All 13 maintained recipe/environment/workflow acquisition routes pass
the pinned dependency preflight. No sibling source provider is required.

## Optionality and contributor tools

There is no optional runtime backend, engine, or runtime-feature extra. The
extension producer API uses only pytest and the standard library; callers may
emit evidence without introducing an optional diagnostic-library dependency.
Pytest discovers installed third-party plugins; receptor does not select or
install them itself.

The test, lint, docs, benchmark, release and dev extras are contributor tools.
Their pytest-xdist/subtests/rerunfailures/cov, Sphinx/MyST/theme, tiktoken, Ruff,
build/packaging/Twine bounds apply to those activities, not shipped runtime
features. Retain these existing tooling ranges and exact CI/provider/build pins.
The Conda build environment is bootstrap-only; recipe host/run closures remain
separate. No automatic cap removal or invented runtime minimum is justified.

## Executed evidence and limits

Python 3.14.7 from the qualified molsyssuite@uibcdf_3.14 environment created a
task-owned venv with the exact public pytest 8.0.0 floor. Nineteen focused
model/collection cases pass, including partial collection, SyntaxError,
ImportError, maxfail and collect-only; the two xdist cases are deselected because
that independent floor scope intentionally has no optional plugins. This is
exact-floor API evidence, not all-interpreter or full artifact qualification.
The ordinary source/installed matrices and clean released dependency closures
are retained separately in the 1.2.3 release evidence.

Reassess on a new consumed pytest API, changed runtime feature, metadata/recipe/
environment or acquisition route. Unknown future pytest versions are not
certified by permissive metadata; concrete incompatibility needs owning
evidence, a justified bound and a reassessment/removal condition.
