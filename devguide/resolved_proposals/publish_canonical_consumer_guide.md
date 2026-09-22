---
summary: Publish a canonical Pytest Receptor guide for MolSysSuite consumers.
issue: uibcdf/pytest-receptor#5
status: resolved
opened: 2026-09-22
closed: 2026-09-22
verification: measured
area: [documentation, governance, integration]
guard: tests/test_consumer_guide.py
normative: standards/PYTEST_RECEPTOR_GUIDE.md
blocked_by: []
supersedes: []
---

# Publish a canonical Pytest Receptor consumer guide

**Reported:** 2026-09-22 from the central rollout request in
`uibcdf/molsyssuite#37`.
**Status:** Resolved on 2026-09-22. The canonical source, owner-side guard and hosted
provider verification are complete. Central rollout continues in `uibcdf/molsyssuite#37`.

## What

Own `standards/PYTEST_RECEPTOR_GUIDE.md` as the single synchronized contract for
repositories that use Pytest Receptor. Consumer root copies will be byte-identical and
read-only; content changes return to this repository.

## How

Distill the stable public behavior from installation, usage, artifact, limitation and
reference documentation. Cover profile selection, exit-code authority, structured
evidence, xdist and terminal limitations, native-pytest fallback, provider feedback and
the synchronization boundary. Protect the owner marker and required operational sections
with a focused test, and make the canonical source visible from `AGENTS.md`.

## Why

Usage instructions are currently split between provider documentation and consumer-local
notes. Some of those notes still describe pre-1.0 behavior or bypass the suite issue
protocol. A canonical guide lets consumers see the current contract without forking it.

## Evidence and consumer boundary

A 2026-09-22 inventory found durable use in SMonitor, ArgDigest, DepDigest, PyUnitWizard,
MolSysMT, MolSysViewer, GH Run Receptor, DockingMT and Ackredit. Evidence included direct
development dependencies, `--receptor` workflow commands, and maintained developer
instructions. Repositories with no durable use are excluded from the proposed central
consumer set.

The guide reflects current provider documentation: Python 3.11–3.14 and pytest 8–9 are
supported; `human` is a true passthrough; `llm` assumes a readable checkout; `ci` retains
all root causes inline; the receptor preserves pytest's exit status; JSONL artifacts are
opt-in and separate test outcome from artifact completeness.

After implementation, the focused owner contract passed 2 tests. The complete provider
suite, rendered through Pytest Receptor itself, passed 172 tests with 9 dependency-based
skips in 72.08 seconds. Ruff check and format checks passed all 80 inspected files.

## Acceptance criteria

- The canonical source has an unambiguous synchronized-copy marker and owner URL.
- Required behavior, profile selection, exit authority, artifacts, native fallback,
  feedback and synchronization are actionable from the guide alone.
- Provider tests fail if the marker or required contract sections disappear.
- `AGENTS.md` identifies this repository as the content owner.
- Provider CI passes before `uibcdf/molsyssuite#37` registers consumers.

## Scope and exclusions

This proposal does not change renderer behavior, output format, dependency versions or
artifact schema. Central registry and consumer-copy rollout belong to
`uibcdf/molsyssuite#37`.

## Provenance

`docs/installation.md`, `docs/usage.md`, `docs/artifacts.md`, `docs/limitations.md`,
`docs/reference.md`, provider source/tests, and a live search of registered MolSysSuite
consumer repositories on 2026-09-22.

## Resolution evidence

Commit `5765e6c` published the canonical marked source, its focused contract guard, the
owner route in `AGENTS.md`, and this record. The local provider suite passed 172 tests with
9 dependency-based skips; Ruff check and format checks passed 80 files.

Hosted test run `35719841057` passed all 11 jobs across lint, serial/distributed test roles
and supporting checks. Hosted MolSysSuite policy run `35719841348` passed its single job.
GH Run Receptor independently summarized both as complete successes. The provider issue
also carries the nine measured `component:<consumer>` relationships; central registry and
copy adoption remain independently owned by `uibcdf/molsyssuite#37`.

## Correction — 2026-09-22 — synchronized marker interoperability

The original closure said the source had a valid synchronized-copy marker. Its first
provider-specific wording passed the new owner test but did not satisfy MolSysSuite's
existing general synchronizer, which deliberately requires one literal marker across all
guide owners. The first central dry run rejected all nine relationships before writing.

The source and guard now use `SYNCHRONIZED MOLSYSSUITE GUIDE — DO NOT EDIT COMPONENT
COPIES.` while retaining the Pytest Receptor canonical URL on the next line. Provider
issue #5 was reopened until the corrected source passed owner and central preflight. This
correction appends to the archived record; it does not erase the original evidence.
