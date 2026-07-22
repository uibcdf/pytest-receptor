# Using pytest-receptor — a note for collaborators

**What you are being asked to do:** run this project's tests through
`pytest-receptor` in your normal development cycles, and report anything that
looks wrong or could be better.

**Read this first, it is short.** This note is meant to be copied into (or linked
from) a consumer repository's `devguide/` so anyone joining the project knows how
to use the receptor and, more importantly, how to feed back what they find.

---

## It is in a testing phase — that is the point

`pytest-receptor` is pre-1.0 and under active testing on real suites. That does
**not** mean "don't use it": use it in your day-to-day. It means two things:

- **Normal `pytest` stays the authority** for whether your tests actually passed.
  The receptor agrees with it on verdict, counts, and exit code across everything
  measured so far — but if they ever disagree, pytest is right and that
  disagreement is the single most important thing to report.
- **The output format may still change** before 1.0. It changes *because* people
  tell us what is missing or awkward. Your feedback is what shapes it.

## What it does

When a coding agent runs your tests, it reads pytest's output — and that output
was designed for a human at a terminal: a banner, the plugin list, a progress
bar, and the full source of every failing test. The agent pays tokens for all of
it, on every iteration.

The receptor renders the same run compactly and honestly: one broken fixture
appears **once**, with every affected test still named and a command to re-run
them; a green run is a single line. It never shortens the truth — a failed,
empty, or interrupted run can never read as a pass.

It changes **nothing** about whether your tests pass. Installing it is safe: with
no flag, pytest behaves exactly as if it were not installed.

## How to run it

```bash
pytest                    # unchanged pytest — installing changes nothing
pytest --receptor=llm     # compact output, for a coding agent
pytest --receptor=llm -n 12   # your normal parallel run, same output
```

A few things worth knowing:

- **You need no extra flags.** `--receptor=llm` already quietens pytest further
  than `-q`.
- **Do not pass `--tb=line` or `--tb=no`.** They delete the `frames:` line that
  says where the failure is, to save about twenty tokens. If this project's
  `addopts` carries a restrictive `--tb`, drop it for these runs.
- **The rerun line is configurable.** Each failure ends with a `rerun:` command
  meant to work pasted verbatim. If this project runs pytest as anything other
  than bare `pytest` (`python -m pytest`, `uv run pytest`, a wrapper), it should
  be set once in the config so the command matches:

  ```ini
  [pytest]
  receptor_rerun_command = python -m pytest
  ```

- **See what it saves you:** `pytest --receptor=llm --receptor-stats` appends the
  token cost against your own pytest configuration.

## Reading the output

```text
FAIL exit=1 | 38 errors, 90 passed | 12.40s | 1 root cause

[1] TypeError | 38 tests | setup
    conftest.py:31
    TypeError: 'NoneType' object is not subscriptable
    tests:
      tests/test_merge.py::test_merge[0]
      +37 more
    rerun: python -m pytest tests/test_merge.py -q
```

- The first line is the verdict — exit status and counts. It is always first, so
  reading line one tells you the answer.
- Failures are grouped by root cause; every affected test is still listed.
- No source echo — you have the files. The assertion diff, which you cannot
  reconstruct, is kept.
- Progress on long runs goes to **stderr** (never stdout), one line per 20%.

## The two things worth reporting

Feedback is the reason the pilot exists, and it goes **into the `pytest-receptor`
repository**, not into an issue tracker that gets lost. Write a short Markdown
file in one of two inboxes:

| What you have | Where (in the `pytest-receptor` repo) |
| :--- | :--- |
| The plugin did something **wrong** — bad output, a crash, a disagreement with pytest | `devguide/pending_bugs/` |
| The plugin should do something **different** — a rough edge, a feature you need | `devguide/pending_proposals/` |

If unsure, file it as a bug. Each directory has a short README with the (light)
conventions; rough notes are fine, and an unpolished observation you actually
write beats a polished one you don't.

Two reports are worth a file even when they feel small:

- **A run where the compact report was not enough to act on** — where you had to
  open the on-disk report, read a source file, or run pytest again to understand
  a failure. There is no "it was in the file" defence: if something you needed
  was not in front of you, that is our design failure, not yours. **This is the
  single most valuable signal we can get.**
- **Grouping that got it wrong** — two different bugs merged into one group, or
  one cause split across many. Scientific stacks (array shapes, dtypes, device
  names) are where we expect this to break first.

And one that jumps the queue: **any disagreement with pytest** about a run's
outcome or counts. File it as a bug and say so directly.

The repository is `github.com/uibcdf/pytest-receptor`. If you have it cloned
alongside this project, the inboxes are `../pytest-receptor/devguide/pending_bugs/`
and `.../pending_proposals/`.

## More detail, if you want it

- `README.md` in the `pytest-receptor` repo — what the plugin does and how.
- `devguide/molsysmt_pilot.md` — the fuller brief the pilot works from, including
  what the plugin does *not* do yet.
