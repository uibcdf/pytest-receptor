# PyPI and pytest plugin discovery

**Verified:** 2026-08-12 against the current pytest and PyPA documentation.

The cross-channel release order and resume checklist are authoritative in
`roadmap_to_1.0_publication.md`; this document remains the detailed PyPI
runbook.

## What happens automatically

Pytest loads installed third-party plugins from the `pytest11` entry-point
group. This project declares:

```toml
[project.entry-points.pytest11]
receptor = "pytest_receptor.plugin"
```

The official pytest plugin page is an automated, informational compilation of
PyPI projects whose names begin with `pytest-` or `pytest_`; it is not a curated
endorsement. Publishing `pytest-receptor` to PyPI therefore supplies the naming
condition for inclusion, while `Framework :: Pytest` makes its purpose explicit
in package metadata. Index refresh is external and may not be immediate.

Transferring the repository to the `pytest-dev` GitHub organization is a
different, optional process for established plugins. It is not required for
automatic loading, PyPI publication, or appearance in the generated list.

## One-time setup requiring a maintainer

The release workflow uses PyPI Trusted Publishing. Before the first release, a
UIBCDF maintainer with a PyPI account must register a pending publisher at
<https://pypi.org/manage/account/publishing/> with exactly:

| Field | Value |
| :--- | :--- |
| PyPI project name | `pytest-receptor` |
| GitHub owner | `uibcdf` |
| Repository | `pytest-receptor` |
| Workflow | `release.yml` |
| Environment | `pypi` |

The exact PyPI JSON endpoint returned 404 on 2026-08-12, so the name appeared
available then; only successful first publication reserves it.

Create the `pypi` environment in GitHub and require a trusted maintainer's
manual approval. No long-lived PyPI token belongs in repository secrets.

## Release procedure

1. Complete the 1.0 gates and update `CHANGELOG.md` from `Unreleased` to the
   release version and date.
2. Commit from a green, clean tree and tag that exact commit `1.0.0`.
3. Push the commit and tag, wait for the complete CI matrix, and create a GitHub
   Release for `1.0.0`.
4. Approve the protected `pypi` environment after reviewing the build job.
5. The workflow checks README rendering, tag/version agreement, wheel and sdist
   metadata, installs the wheel in a clean environment, confirms pytest's
   automatic discovery, and publishes through short-lived OIDC credentials.
6. Verify `pip install pytest-receptor`, `pytest --trace-config`, the PyPI
   project metadata, provenance attestation, and eventual appearance in pytest's
   generated plugin list.

The release-only local rehearsal is:

```bash
pip install -e ".[release]"
python -m build
python -m twine check --strict dist/*
python devtools/check_release.py --tag 1.0.0
```

The last command is expected to fail on an untagged or dirty development tree;
that is the guard against uploading a distribution whose embedded version does
not equal the immutable release tag.

PyPI distributions are immutable. A broken release is followed by a new patch
version; never delete and reuse a version number.

## Optional future pytest-dev submission

Once the plugin has happy users outside its maintainers, pytest invites a
discussion about transferring it to `pytest-dev`. Their current prerequisites
include PyPI metadata, tox, README/platform documentation, matching license
metadata, issue tracker, changelog, and preferably three release-capable people.
That organizational transfer should be evaluated after 1.0 adoption, not used
as a publication gate.

## Official references

- [pytest: writing installable plugins](https://docs.pytest.org/en/stable/how-to/writing_plugins.html#making-your-plugin-installable-by-others)
- [pytest: generated plugin list](https://docs.pytest.org/en/stable/reference/plugin_list.html)
- [pytest: submitting established plugins to pytest-dev](https://docs.pytest.org/en/stable/contributing.html#submitting-plugins-to-pytest-dev)
- [PyPI: Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [PyPA: publishing distributions with GitHub Actions](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
