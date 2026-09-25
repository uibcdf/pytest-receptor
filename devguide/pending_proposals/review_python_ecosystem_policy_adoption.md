---
summary: Review inherited Python ecosystem policy in pytest-receptor.
issue: uibcdf/pytest-receptor#6
status: partial
opened: 2026-09-25
closed:
verification: measured
area: [ci, governance]
guard:
normative:
blocked_by: []
supersedes: []
---

# Review inherited Python ecosystem policy in pytest-receptor

**Reported:** 2026-09-25, during the MolSysSuite member rollout in
`uibcdf/molsyssuite#6`.
**Status:** Developer-tool and support-library applicability remain partial.

## What

Review the two inherited MOLI policies independently for this Python package.
The existing hosted eight-cell test matrix passed, but its two top-level pytest
commands selected `--receptor=llm`, while MOLI specifies `--receptor=ci` for
hosted pytest logs. The repository tests the plugin from its own source checkout,
which makes the general instruction to pin a published receptor release
inapplicable to those same self-tests without a provider-specific decision.

## How

Select `--receptor=ci` in both top-level test commands in
`.github/workflows/tests.yml`. Keep the same tests, Python and pytest matrix,
xdist invocation, and exit status. Use `--receptor=llm` for local agent tests.
Confirm the hosted result and its native pytest outcome with GH Run Receptor.
Document a bounded provider decision about testing the checkout version versus
pinning a published version; do not count the source checkout as an exact
published pin.

Review the four support boundaries against the actual plugin API. PyUnitWizard
has no physical-quantity boundary here. DepDigest requires assessment of
passive integration with optional pytest plugins: the plugin defines optional
hooks but does not directly load their packages. ArgDigest may apply to the
public `--receptor-events-max-bytes` constraint and artifact arguments.
SMonitor may apply to recoverable artifact or reporting failures, but the
renderer itself is the product's diagnostic path. Decide these from behavior
and dependency direction before adding any library.

## Why

Hosted logs are consumed after their runner disappears. The `ci` profile
retains full failure detail for that setting. A passing matrix under `llm`
does not establish the inherited CI-profile requirement. Conversely, adding
the published plugin as a test dependency could cause the tests to exercise
that release instead of the code under review.

## What is measured and what is assumed

At source `905f7ab014d6cda202a0247f54dd8686b426d122`, inspection of
`.github/workflows/tests.yml` found eight Python/pytest combinations and both
top-level test commands using `--receptor=llm`. Hosted run `36024482632`
passed 11/11 jobs, including all eight test cells, as inspected by GH Run
Receptor. Local `python -m pytest tests/ --receptor=llm -q` passed 172 tests
with nine skips; the skips concern unavailable optional test plugins. The
ordinary MolSysSuite repository checker passed. The new `ci` profile still
needs hosted confirmation at the implementation commit.

The support-library points above are applicability hypotheses, not adoption
claims. No library is added solely to satisfy the inventory.

## Alternatives and refuted paths

Reusing the passing matrix as proof of the new hosted profile was rejected:
the workflow explicitly selected `llm`. Installing only the published plugin
in the provider's self-test jobs was rejected as an unreviewed change to the
code under test.

## Scope and exclusions

This report covers this provider's policy adoption. It does not change the
plugin's user-facing profile semantics, release artifacts, or the suite-wide
MOLI rule. Historic devguide records are outside this review.

## Acceptance criteria

- Hosted test cells run the same selectors under `--receptor=ci` and preserve
  native failures; local agent tests use `--receptor=llm`.
- The exact hosted revision passes the Python 3.11–3.14 by pytest 8/9 matrix,
  with no loss of the distributed suite.
- A provider-specific, tracked decision resolves the published self-test pin
  question and identifies how release artifacts are checked independently.
- Each applicable support-library boundary has implementation and test
  evidence, a reasoned non-applicability decision, or a bounded exception.

## Local implementation issues

`uibcdf/pytest-receptor#6` owns the local review. MolSysSuite records its
separate member states under `uibcdf/molsyssuite#6`.

## Dependencies and risks

The self-test pin decision may need clarification from the policy owner in
`uibcdf/moli#6`; the running source must remain the code under test.

## Provenance

Inspected on 2026-09-25 in a clean temporary checkout, on Linux with local
Python 3.13.15 and pytest 9.1.1. Hosted run `36024482632` supplies the exact prior matrix
revision; a later run must verify the changed workflow.
