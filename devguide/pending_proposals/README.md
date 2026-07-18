# Pending Proposals

The inbox for input that has not been triaged yet.

Anything that should influence `pytest-receptor` but is not yet an accepted
decision belongs here as a Markdown file: field reports from a real suite,
feature requests, integration needs from another project.

**Defects go to [`../pending_bugs/`](../pending_bugs/README.md) instead.** The
split is intent, not severity: a bug is the plugin doing something wrong, a
proposal is the plugin doing something you would rather it did differently. If
unsure, file it as a bug.

## Why a directory and not an issue tracker

Every task in this project has an identifier in
[`audit_action_register_2026-07-17.md`](../audit_action_register_2026-07-17.md),
which is the single complete work queue. A proposal that exists only in a
conversation is untracked work, and untracked work is how the original audit
found sixteen proposals that had been written down somewhere and then quietly
forgotten.

Files here get read when a release is planned. Each one is then either given an
identifier in the register, accepted as a documented limitation, or rejected with
a reason and moved to
[`../superseded_proposals.md`](../superseded_proposals.md). Nothing is deleted.

## Conventions

Deliberately light. Do not let formatting stop you writing something down.

- One file per topic. Name it for the topic, not the date:
  `grouping_misses_numpy_shape_mismatch.md`, not `notes_july.md`.
- Start with who wrote it, when, and which project it came from.
- Say what you observed before what you think should change. The observation
  survives even if the conclusion turns out to be wrong.
- Include the concrete evidence: the command, the output, the version.
  `pytest --receptor=llm --receptor-stats` output is ideal.
- Rough is fine. An unpolished observation beats a polished one nobody had time
  to write.

## Especially wanted

If you are running the receptor on a real suite, these are worth a file even
when they feel too small to bother with:

- **A run where the report was not enough** and you had to run pytest again.
  Record what was missing. This is the most valuable signal we can get.
- **Grouping that got it wrong**, in either direction: unrelated failures merged,
  or one cause split across many groups.
- **Any disagreement with pytest** about outcome or counts. That one is a bug
  and jumps the queue — file it in `../pending_bugs/` and say so directly.

## Current pilots

- MolSysMT — see [`../molsysmt_pilot.md`](../molsysmt_pilot.md).
