---
summary: Review MolSysSuite Python ecosystem policy in pytest-receptor.
issue: uibcdf/pytest-receptor#6
status: resolved
opened: 2026-09-25
closed: 2026-09-27
verification: measured
area: [ci, governance]
guard:
normative: devguide/python_ecosystem_policy_adoption.md
blocked_by: []
supersedes: []
---

# Review MolSysSuite Python ecosystem policy in pytest-receptor

**Reported:** 2026-09-25, during the MolSysSuite member rollout in
`uibcdf/molsyssuite#6`.
**Status:** Resolved. Hosted CI and the policy-v1.5.2 caller passed; the local
applicability decisions are durable in `devguide/python_ecosystem_policy_adoption.md`.

## What

Review MolSysSuite's developer-tool and support-library member policies
independently for this Python package. The original eight-cell test matrix used
`--receptor=llm` in hosted logs; both top-level commands now use
`--receptor=ci`. The repository tests the plugin from its own source checkout,
so installing a published receptor in those jobs would test the wrong code.

## How

Keep `--receptor=ci` in both top-level test commands in
`.github/workflows/tests.yml`, with the same tests, Python and pytest matrix,
xdist invocation, and exit status. Use `--receptor=llm` for local agent tests.
Keep the self-test checkout as the code under test and independently install
the built wheel in a clean environment in the packaging job. Move the
MolSysSuite policy caller to the current policy release and verify its hosted run.

Review all four support boundaries against the actual plugin API and its
existing tests. Record why a boundary does or does not call for a support
library before changing runtime dependencies.

## Why

Hosted logs are consumed after their runner disappears. The `ci` profile
retains full failure detail for that setting. A passing matrix under `llm`
does not establish the suite CI-profile requirement. Conversely, adding
the published plugin as a test dependency could cause the tests to exercise
that release instead of the code under review.

## What is measured and what is assumed

At source `905f7ab014d6cda202a0247f54dd8686b426d122`, inspection of
`.github/workflows/tests.yml` found eight Python/pytest combinations and both
top-level test commands using `--receptor=llm`. Hosted run `36024482632`
passed 11/11 jobs, including all eight test cells, as inspected by GH Run
Receptor. Local `python -m pytest tests/ --receptor=llm -q` passed 172 tests
with nine skips; the skips concern unavailable optional test plugins. The
ordinary MolSysSuite repository checker passed. The implementation commit
`e51fc6f` then passed hosted Tests run `36134742751`: all eight Python
3.11–3.14 by pytest 8/9 cells passed both serial and xdist suites. The
packaging job built a wheel and installed it in a clean environment. GH Run
Receptor reported `PASS conclusion=success | profile=ci |
roles=lint:1,test:8,other:2 | jobs=11/11`. The later source commit
`7a8bcb3` passed Tests run `36271013311`.

The source checkout intentionally supplies the receptor in its own self-tests.
An exact published test dependency would replace the implementation under
review. This is a provider-specific non-applicability decision for the
published-version pin, limited to self-test jobs. The packaging job separately
installs the just-built wheel and checks pytest plugin discovery. Reassess this
decision if self-tests stop exercising the checkout or the artifact job stops
testing an isolated wheel.

Support-library applicability at the public boundary:

- **ArgDigest:** pytest owns CLI option parsing. The cross-option
  `--receptor-events` rule and 65536-byte floor raise `pytest.UsageError`;
  the artifact writer enforces the same floor for direct callers.
  `tests/test_artifact.py::test_events_size_limit_has_a_safe_minimum` and
  `tests/test_artifact.py::test_events_option_requires_collecting_profile`
  cover those paths. There is no separately decorated argument API for
  ArgDigest to digest; schema/content validation belongs to the artifact
  reader. Adding it here would duplicate pytest's option contract.
- **DepDigest:** optional pytest plugins are installed by the caller's
  environment and discovered by pytest. Receptor's hook integrations inspect
  already-registered plugins; it does not select, import, or explain an
  optional backend for its own runtime. No DepDigest loading boundary exists.
- **SMonitor:** this plugin is itself the pytest-facing diagnostic renderer.
  Expected option failures use `pytest.UsageError`; recoverable artifact
  failures are reported through its bounded stderr warning and tested by
  `tests/test_artifact.py::test_unavailable_destination_warns_without_changing_pytest_result`.
  Routing them through another diagnostic sink would change the plugin's
  output contract without adding a consumer need.
- **PyUnitWizard:** no physical quantities are parsed, converted, stored, or
  exchanged by the plugin. Byte counts and durations are reporting metadata.

These are non-applicability decisions for the product's current boundaries,
not claims that the libraries are installed. Reassess when a new public
argument API, optional runtime backend, or external diagnostic sink is added.

## Alternatives and refuted paths

Reusing the passing matrix as proof of the new hosted profile was rejected:
the workflow explicitly selected `llm`. Installing only the published plugin
in the provider's self-test jobs was rejected as an unreviewed change to the
code under test.

## Scope and exclusions

This report covers this provider's policy adoption. It does not change the
plugin's user-facing profile semantics, release artifacts, or the suite-wide
member rule. Historic devguide records are outside this review.

## Acceptance criteria

- Hosted test cells run the same selectors under `--receptor=ci` and preserve
  native failures; local agent tests use `--receptor=llm`.
- The exact hosted revision passes the Python 3.11–3.14 by pytest 8/9 matrix,
  with no loss of the distributed suite.
- The provider-specific self-test pin decision and clean wheel-installation
  check remain documented.
- Each support-library boundary has a tested integration, a reasoned
  non-applicability decision, or a bounded exception.
- The MolSysSuite 1.5.2 caller passes its exact-commit hosted gate.

## Local implementation issues

`uibcdf/pytest-receptor#6` owns the local review. MolSysSuite records its
separate member states under `uibcdf/molsyssuite#6`.

## Dependencies and risks

MolSysSuite owns member policy after `uibcdf/molsyssuite#53`. The source
checkout must remain the code under test; an independent installed-wheel job
provides artifact evidence.

## Provenance

Inspected on 2026-09-25 in a clean temporary checkout, on Linux with local
Python 3.13.15 and pytest 9.1.1. Hosted run `36024482632` supplies the prior
matrix. Reassessed on 2026-09-27 against pytest-receptor `a8a8a5a` and the
MolSysSuite `policy-v1.5.2` contract.

## Resolution

The hosted `ci` profile passed the eight-cell matrix at `e51fc6f` and
again at `7a8bcb3`. The latest local self-test suite passed 193 tests with
`--receptor=llm`. Commit `a8a8a5a` pins the current MolSysSuite
`policy-v1.5.2` caller; its [hosted policy run
`36310571746`](https://github.com/uibcdf/pytest-receptor/actions/runs/36310571746)
passed and GH Run Receptor reported `PASS` for the one-job gate. The local
MolSysSuite repository checker also passes on this review checkout.

The provider's source checkout is the self-test subject, and the packaging
job independently tests a clean installed wheel. No support library has an
applicable boundary in the current plugin API; the decision and explicit
reassessment triggers are in the normative local page named above. These
facts complete the separate developer-tool and support-library reviews for
`uibcdf/pytest-receptor#6`.
