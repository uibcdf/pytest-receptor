# Python ecosystem policy decisions for pytest-receptor

This repository applies the [MolSysSuite member policy at
`policy-v1.5.2`](https://github.com/uibcdf/molsyssuite/blob/policy-v1.5.2/devguide/python_ecosystem_policy.md).
This page records only decisions specific to pytest-receptor. The owning review
is [uibcdf/pytest-receptor#6](https://github.com/uibcdf/pytest-receptor/issues/6).

## Developer tools

Hosted self-tests run the checkout's own plugin with `--receptor=ci`, in both
serial and xdist modes across the supported Python and pytest matrix. Local
agent tests use `--receptor=llm`. Pinning a published pytest-receptor release
inside these self-test jobs would replace the code under review, so the
published-version pin is inapplicable to those jobs. The packaging job builds
the candidate wheel, installs it into a clean environment, and checks pytest
plugin discovery independently. Reassess this decision if either job stops
exercising its stated source.

Use a published GH Run Receptor release for first inspection of hosted runs,
with native GitHub conclusions as authority, under the suite policy.

## Support libraries

| Library | Local decision | Evidence or reassessment trigger |
| --- | --- | --- |
| ArgDigest | No separate argument-digestion boundary. Pytest owns CLI option parsing and `pytest.UsageError`; the artifact writer checks its own size floor. | `tests/test_artifact.py::test_events_size_limit_has_a_safe_minimum` and `tests/test_artifact.py::test_events_option_requires_collecting_profile`. Reassess for a new public argument API. |
| DepDigest | No optional runtime backend is selected or loaded by receptor. Pytest discovers plugins installed by the caller. | Reassess if receptor begins loading an optional provider itself. |
| SMonitor | Receptor is the pytest-facing diagnostic renderer. Expected usage errors and recoverable artifact warnings use its own tested output contract. | `tests/test_artifact.py::test_unavailable_destination_warns_without_changing_pytest_result`. Reassess for an external diagnostic sink. |
| PyUnitWizard | No physical-quantity boundary; byte counts and timings are reporting metadata. | Reassess if a quantity enters the public API or artifact schema. |

These applicability decisions do not imply that the four libraries are runtime
dependencies. New boundaries must be reviewed under the current MolSysSuite
policy and recorded in this repository's issue board.
