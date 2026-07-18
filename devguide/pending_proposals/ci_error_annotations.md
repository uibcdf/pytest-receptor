# Proposal: CI error annotations

**Recorded:** 2026-07-18

**Origin:** salvaged design from the `event-model-v0.5` branch. Deliberately not
implemented in 0.6.

**Status:** untriaged. Waiting on evidence that anyone wants it.

## What it is

GitHub Actions reads specially formatted lines from a job's output and turns
them into inline annotations on the pull request diff:

```text
::error file=molsysmt/form/Topology/merge.py,line=117::tests/test_merge.py::test_merge phase=setup - TypeError: 'NoneType' object is not subscriptable
```

The failure then appears against the offending line in the PR, rather than only
inside a log nobody opens.

The `ci` profile already computes everything this needs — file, line, node ID,
phase, exception type, message — so emitting it is a formatting change, not new
collection work.

## Why it is not in 0.6

Three reasons, none of them fatal.

**It is vendor syntax.** `::error file=...` means something to GitHub Actions
and is noise everywhere else. Emitting it unconditionally, which is what the
branch did, adds a line per failure to every GitLab, Jenkins, and Buildkite log
that will never render it.

**We have no evidence anyone wants it.** 0.6 was scoped to what could be
justified. This is a plausible feature rather than a demonstrated need, and the
project already carries a warning about building on plausibility: the heartbeat,
the XML syntax, and the installation hints were all built on it and all removed.

**It costs tokens in the profile that can least afford them.** The `ci` profile
already expands every group because a CI runner is destroyed at job end. Adding
a duplicate line per failure on top of that is the opposite direction.

## What would settle it

One CI-using project saying they would turn it on. The MolSysMT pilot is the
obvious source.

## Sketch, if adopted

Gate on the runner rather than on a flag, so it costs nothing where it does not
render:

```python
if os.environ.get("GITHUB_ACTIONS") == "true":
    for group in groups:
        for occurrence in group.occurrences:
            path, _, line = occurrence.location.rpartition(":")
            emit(f"::error file={path},line={line}::{occurrence.nodeid} - {summary}")
```

Two details worth getting right if it happens:

- Annotate the **crash location**, not the test file. Pointing at
  `test_merge.py` is useless when the bug is in `merge.py:117`.
- Emit one annotation per occurrence, not per group. GitHub deduplicates
  identical annotations itself, and per-occurrence is what makes them land on
  the right lines.

Support for other CI systems (GitLab, Buildkite) should wait for the same kind
of evidence, separately.
