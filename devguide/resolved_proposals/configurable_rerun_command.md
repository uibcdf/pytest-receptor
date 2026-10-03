---
summary: Configure the runner prefix in rerun commands.
issue: uibcdf/pytest-receptor#29
status: resolved
opened: 2026-10-03
closed: 2026-10-03
verification: inspected
area: [reporting, compatibility]
guard: tests/test_plugin.py::test_rerun_command_is_configurable
normative:
blocked_by: []
supersedes: []
historical_register: PR-UX-004
historical_resolved: 2026-07-21
---

# Proposal: configurable rerun command

**Recorded:** 2026-07-19

**Origin:** `pytest-markdown-report`, found during the prior-art survey
([`../prior_art_2026-07-19.md`](../prior_art_2026-07-19.md)). It ships
`--markdown-rerun-cmd`; we ship nothing equivalent. Their idea is better than
ours. The implementation is ours to write.

**Status:** untriaged, but this is debt rather than a feature request.

## The problem

Every failure group ends with a rerun line:

```text
rerun: pytest tests/test_merge.py -q
```

The contract we state, repeatedly and publicly, is that this works **pasted
verbatim** from where pytest was invoked. That is what
`invocation_params.dir` resolution exists to guarantee, and we corrected a real
defect to keep it true.

For any project not invoked as bare `pytest`, the promise is false. `just test`,
`uv run pytest`, `hatch test`, `tox -e py311`, `make test`, a wrapper script that
sets environment — in all of these the emitted command either fails or silently
runs under a different configuration than the suite it is reporting on. The
second is worse than the first.

This is not a discovered bug; nobody has reported it. It is a promise that
happens to hold for the way we run our own suite.

## Shape

A configuration value rather than a flag, since the invocation style is a
property of the project, not of the run:

```ini
[pytest]
receptor_rerun_command = uv run pytest
```

Default `pytest`, preserving current behaviour. The value replaces the leading
token; selection arguments and `-q` are still appended by us, so grouping logic
is untouched.

Open questions to settle before implementing:

- Whether an empty value should suppress the rerun line entirely, as
  `--markdown-rerun-cmd=""` does for them.
- Whether it belongs in the same `--receptor-*` flag namespace as well, for a
  one-off run that differs from the project default.
- Whether to attempt detection (`uv.lock` present, `justfile` present) or refuse
  to guess. Current instinct is to refuse: a wrong rerun command is worse than a
  generic one, because it looks authoritative.

## Why it is not in 0.6

0.6 is the reliability floor and is closed. This changes emitted output, so it
needs its own regression coverage: the command must be correct for the default,
correct for a configured runner, and must never emit a command that would run a
*different* selection than the group it belongs to.

---

## Resolution

**Implemented 2026-07-21 (PR-UX-004).** A `receptor_rerun_command` ini value,
default `pytest`, replaces only the leading runner; the receptor still appends
the selection and `-q`, so a configured runner reruns exactly the reported group.
An empty value omits the rerun line — the opt-out the prior art (`pytest-markdown-
report`'s `--markdown-rerun-cmd=""`) offers.

The open questions were settled as the proposal leaned: empty suppresses the
line; it is an ini value only, not a per-run flag, because the invocation style
is a property of the project rather than of the run; and no auto-detection —
guessing `uv`/`just` from a lockfile was rejected, since a wrong rerun command
that looks authoritative is worse than a generic one.

Regressions cover all three requirements: the default still says `pytest`, a
configured `uv run pytest` still selects the same node, and an empty value emits
no line. Documented in `docs/reference.md`.


## Identity and closure review — 2026-10-03

Owning identity: `uibcdf/pytest-receptor#29`. Reconciliation: `uibcdf/pytest-receptor#10`.
Historical register: `PR-UX-004`; recorded historical outcome: 2026-07-21.

The metadata dates refer to the issue-backed review, except for the
already existing Python 3.14 issue, whose original issue dates are retained.
The pre-protocol text, including commands and historical claims, is
preserved byte for byte above this dated addition. This review inspects
the current implementation and relevant assertions; it does not rerun
the historical consumer suite or certify an old release again.

The guard asserts a configured uv run pytest prefix with the unchanged test selector and -q. test_each_group_carries_a_rerun_command covers the default, and test_empty_rerun_command_omits_the_line covers explicit opt-out. No runner auto-detection was accepted.

Durable guard: `tests/test_plugin.py::test_rerun_command_is_configurable`. Its relevance is explained above.
