# Coverage reporting

The producer reuses the existing Python 3.13 / pytest 9 serial suite in `tests.yml`. It runs the
ordinary suite under `python -m coverage run --branch --source=pytest_receptor`, then
exports `coverage.xml`. Coverage starts before pytest loads plugins. The measured
scope is the checkout's `pytest_receptor` package in the parent test process; child
processes, clean-environment fixtures and distributed workers are not combined.
It does not claim coverage across every supported platform or interpreter.

The XML is retained for 14 days as `coverage-xml`. A separate publisher downloads
that exact run's artifact, grants OIDC only to the publisher job and uploads only
for push or manual dispatch on `main`. Pull requests produce evidence without
publishing it. Codecov action v7.1.1 is pinned to its verified commit. Missing XML
and upload failures fail the publisher; they are not reported as accepted coverage.

The README percentage represents the latest accepted default-branch report, which
can lag lightweight or `[skip ci]` commits. There is no percentage floor. Service
acceptance is checked separately using MolSysSuite's public coverage audit; a
successful upload step alone does not establish a completed report. An outage or
missing service configuration stays an explicit pending issue with owner and
review date under the shared repository badge policy.

For local reproduction, install the existing test extra and `coverage==7.16.0`,
then run the workflow's coverage command and `python -m coverage xml`. This is
developer-tool evidence; it does not execute any consumer's scientific suite.
