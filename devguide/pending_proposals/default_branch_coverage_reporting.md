---
summary: Publish owned default-branch coverage from the existing tool suite.
issue: uibcdf/pytest-receptor#12
status: partial
opened: 2026-10-01
closed:
verification: measured
area: [governance, ci, coverage]
guard:
normative: devguide/coverage_reporting.md
blocked_by: []
supersedes: []
---

# Default-branch coverage reporting

## What

Implement the applicable developer-tool producer identified by
uibcdf/molsyssuite#69. The maintainer approved this implementation on 2026-10-01.

## How

Reuse the existing suite in Python 3.13 / pytest 9 serial suite in `tests.yml`, export package branch coverage,
retain its XML and publish from a separate trusted-main OIDC job. The maintained
contract is `devguide/coverage_reporting.md`.

## Why

Tests already exercise this tool, but the initial public audit found no accepted
complete default-branch report supporting a live README percentage.

## What is measured and what is assumed

Local coverage execution passed the existing suite on Python 3.13.15 with
coverage 7.16.0. Ruff and reporting/index guards pass. Hosted execution and
independent Codecov acceptance remain pending; no badge is claimed yet.

## Alternatives and refuted paths

A new duplicate full-suite job is unnecessary. Injecting coverage into child
processes could alter clean-environment fixture behavior and is not part of this
producer's declared scope. A numeric cached SVG alone cannot prove acceptance.

## Scope and exclusions

Only this tool's existing tests and package are measured. Scientific consumers,
release publication and new minimum percentages are excluded.

## Acceptance criteria

Existing CI tests still execute; XML is generated; a main-source upload succeeds;
Codecov exposes a complete report for that source; the README gains a truthful
live percentage with scope and cadence. Keep this report partial until measured.

## Provenance

2026-10-01, host nauta, Python 3.13; coverage 7.16.0. Hosted identifiers and service
acceptance will be recorded after execution.

## Hosted publisher correction (2026-10-01)

The first hosted publisher failed before sending a report because v5.5.1 fetched
an unavailable OpenPGP key. Tests and XML generation succeeded. The producer now
uses the official v7.1.1 commit, whose wrapper fetches the current `codecovsecops`
key. Signature checking remains enabled. Acceptance is still independently
required; the initial failure is not counted as an upload.
