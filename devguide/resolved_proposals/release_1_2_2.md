---
summary: Publish and independently verify pytest-receptor 1.2.2.
issue: uibcdf/pytest-receptor#45
status: resolved
opened: 2026-10-24
closed: 2026-10-24
verification: reproduced
area: [release, distribution, compatibility]
guard: tests/test_noarch_conda_publication.py
normative:
blocked_by: []
supersedes: []
---

# Publish pytest-receptor 1.2.2

## What

Deliver the compatible changes since 1.2.1 through a canonical GitHub Release,
PyPI and the official `uibcdf` Conda channel. The maintainer requests publication
on 2026-10-24 after #39/#42/#43/#44 close. Earlier benchmark repairs #40/#41 and
exact-source/dependency checks #38 are also part of this release. Optional CI
annotations #9 remain outside its scope.

## How

The committed release plan selects 1.2.2, build zero and the existing staging
route. Freeze a final candidate after documenting measured benchmark input
identity. Required ordinary and full source jobs/steps must pass at that exact
commit; earlier development success is historical evidence, not its release
authorization. Inspect package metadata/runtime resources, documentation,
reporting and policy separately.

Build one exact noarch Conda archive, run recipe tests and inspect resources
before staging. Independently verify the registered file/digest. Qualify that
same file outside source imports across Linux/macOS arm64 and Python 3.11–3.14
using the complete `tests` selection. Preserve actual source, qualification
commit, native run/attempt, filename/digest and before/after provenance checks.
Publish the exact immutable `1.2.2` tag and GitHub Release with title `1.2.2`;
complete protected PyPI Trusted Publishing, and promote the staged Conda file
without rebuilding or overwriting it. Check both public registries and solver
index, downloaded PyPI files/provenance, and actual fresh public pip/Conda
installations before claiming completion.

## Why

This patch repairs external-helper rerun selection and reporting/resource
lifecycle faults while preserving pytest authority, logical counts, profiles
and `events@1` compatibility. Public dependencies and Python support do not
change. Runtime evidence adds optional `test_path`; old artifacts/readers remain
supported within the existing additive contract.

## Shared tools and retained receiving route

Build/upload remains on shared publisher `2fb344525ca0eea817dc24a518f4a6bf26e311cf`;
installed qualification retains reviewed provider
`3350615eee8c95903aca916e42789ecbdcc1f8ef`; promotion uses accepted
`c3e2b9b3dabf3d1c65349c389a23048957bea21a`. Required dependency/source preflight
uses `43b9f94bf5ab0ec3f54a4b2ca5b23b791d6af0bc`. These are unchanged reviewed
routes, not a broad provider/action rollout.

The previously qualified local installed equivalent retains the complete
integration dependencies, source exclusion, exact-file binding and final origin
recheck. Its inherited safe-path mode exposes only reviewed `component/devtools`
to legacy administrative subprocesses, never the component package root. The
thin shared-caller migration remains separately owned in
`uibcdf/molsyssuite#92`; this interim route is reviewed for this exact candidate
and must be revisited by dprada by 2026-12-31 or a route/provider change. Every
installed cell still has to execute successfully; this disposition waives none.
General action v2.3.0 rollout and package withdrawal remain deferred in
`uibcdf/molsyssuite#87` / `uibcdf/moli#42`.

## What is measured and what is assumed

Initial public PyPI/all-label Conda queries and native GitHub tag/release queries
return 404 for 1.2.2. Repeat relevant checks before immutable publication. This
does not authorize overwriting a later registered coordinate.

Benchmarks use an installed locally built 1.2.2 wheel in a clean Python 3.14.7
environment, rather than the editable shared development namespace. The private
measurement clone's ephemeral tag is not pushed. Its runtime/harness hashes,
versions, resolved closure and wheel digest distinguish measurement evidence
from a published artifact. Compare runtime source bytes against the final
candidate before reusing those measurements.

All three measurements are complete: eight token scenarios, three 8,000-test /
twelve-worker scenarios, and 1,000-test runtime/RSS medians over five repeats.
The final RSS measurement runs in a fresh performance-only process so previously
loaded tokenizers do not contaminate the parent/child high-water measurement.
All runtime source and harness hashes match the prepared source; wheel/sdist
metadata and runtime payload checks pass for version 1.2.2. This is still local
measurement evidence, not public delivery. Shared dependency-route preflight,
recipe inspection, fifteen targeted publication/dependency guards, Ruff and
offline reporting/index checks pass before freezing the candidate.

Every gate, source, artifact and public outcome is recorded in #45 and durable
receipts as it becomes known. Planned upload/verification is not success.
The release-specific central notice is `uibcdf/molsyssuite#133`, updated for
staging, source release and each actual public package event.

## Alternatives and refuted paths

- Rebuilding a staged coordinate or moving an existing public tag would discard
  exact-file evidence and violate immutability.
- Green overall CI without required executed tests cannot authorize publication.
- No feature demand for #9 or broad shared-action migration is needed to deliver
  these already verified compatible corrections.

## Scope and exclusions

No dependency-floor change, new Windows/Intel-macOS support, source prerelease,
automatic consumer update or unverified DOI claim. The known receiving context
is `uibcdf/opencastp#13` through #39; central/consumer maintainers own any later
pin/adoption work. New public package availability alone does not certify it.

## Acceptance criteria

- Exact-candidate native gates, metadata/resource checks and complete installed
  matrix pass without skipped required steps or source import substitution.
- Git tag, GitHub Release title/tag and published package versions are 1.2.2.
- Preserve Conda file SHA-256 from staging through public promotion; independently
  verify public labels/repodata and actual fresh installation.
- Independently verify public PyPI wheel/sdist, provenance and clean install.
- Archive/update durable evidence and #45, update central notice #133 and review
  task-owned resources for removal after their required use ends.

## Resolution — 2026-10-24

The annotated tag and GitHub Release `1.2.2` target
`531bafde5d48ddd8974e29ac91ae53ecae0fd787`; release title/tag are both exactly
`1.2.2`. Ordinary Tests `40121309054` and full compatibility `40121311832` pass
at that source. Pinned native preflight verifies all required ordinary/full
jobs/steps, including representative macOS arm64 Python 3.14 / pytest 8 and 9.
Native reporting `40121309163`, policy `40121309333`, publication governance
`40121309530` and Sphinx build/deployment `40121309105` pass. Tag policy
`40123323764` and publication governance `40123323767` pass separately.

Staging `40121753074` builds/uploads one exact archive and retains verified
`uibcdf.conda-upload@1` evidence. Independent anonymous registry/download/resource
checks confirm `noarch/pytest-receptor-1.2.2-py_0.tar.bz2`, build zero, SHA-256
`c0b075286f45e8fce5ab5852947611bfba82b7d509115fc5dadf1a9572b9dd74`.
Installed run `40122053512`, attempt 1, passes all eight Linux/macOS arm64 ×
Python 3.11–3.14 cells, with **264 tests passed in each**. Producer and
qualification source are the same release commit. Independent native checks
verify the matrix and all 32 required execution/provenance steps. Source/file/run
binding and complete dependency closures are retained. Native CLI log rendering
labels steps `UNKNOWN STEP`; actual required-step execution is verified through
native job metadata, and the unique bound job verdict supplies each test count.
No missing step name is invented from that CLI rendering.

Promotion `40123419141` verifies the existing installed matrix, promotes those
same bytes to `main` and retains verified `uibcdf.conda-promotion@1` evidence.
Staging remains. Independent public metadata, downloaded archive and solver
repodata agree on the same filename/digest; no rebuild/overwrite occurred.

PyPI `40123418672` passes exact-tag source/dependency checks, strict metadata and
runtime payload validation, clean plugin discovery and Trusted Publishing. The
protected `pypi` environment is approved only after those build gates pass.
Anonymous public downloads and metadata verify wheel and sdist; both archives
exactly match the native publisher's retained files and their public attested
subjects. Publisher identity is this repository, `release.yml`, environment
`pypi`. This receipt does not claim a separate local Sigstore signature audit.

Fresh ordinary public installations pass: pip on Python 3.14.7 and Conda on
Python 3.14.9, both Linux. Each imports the non-editable plugin from its own
prefix, discovers pytest11, passes a real smoke test and executes the corrected
external-helper rerun, reproducing the two original controlled failures with
complete, integrity-valid JSONL. These checks are separate from the complete
eight-cell exact-file installed Conda matrix.

Public PyPI file hashes, native gate/run/job/step receipts, publisher/source/tag
identities, benchmark provenance, upload/promotion/public verification and fresh
install results are retained in `devguide/release_evidence/1.2.2.json`. Complete
normalized installed dependency closures are retained separately in
`devguide/release_evidence/1.2.2-installed-closures.json`. The static guard protects
route/matrix/file controls; actual native and public receipts prove delivery.

The version-specific notice `uibcdf/molsyssuite#133` records actual source,
staging and public package events and the consumer follow-up disposition.
Known receiving context remains `uibcdf/opencastp#13` through #39; no automatic
consumer update is claimed. #9 remains an independent optional proposal.

## Resource closeout

All task-created build/measurement/public verification processes finish before
disposal. The public Conda verification prefix is removed with its manager after
its successful results are recorded. The unique owned task root contains clean
independent provider/source clones, venvs, cache, generated tests/downloads and
temporary scripts/receipts; these are retired after durable evidence and final
handoff payloads are preserved. Clones are not primary-repository registered
worktrees; clean tracked status is checked before disposal. Cleanup success or
failure is recorded in the durable release receipt before issue closure.

The primary checkout, shared `molsyssuite@uibcdf_3.14` environment and foreign
consumer worktree registration remain protected. Small final API/comment drafts
last through their final upload and are then removed. No broader `/tmp` cleanup
or historical-deletion/space-reclaimed claim is made. No new platform or DOI
claim is introduced by this release.

Closeout confirms the owned `/tmp/pytest-receptor-122-6jn92rq6` task root is
absent after the verification prefix was removed with Conda and all owned
processes completed. The three independent clones were clean before removal;
no cleanup failure occurred. Durable receipts retain the explicit outcome.
