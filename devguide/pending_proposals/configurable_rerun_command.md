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
