# Proposal: built-in normalizers for warning variants

**Recorded:** 2026-07-18

**Status:** blocked on evidence. Requested from the MolSysMT pilot.

## Observation

While measuring the cost of warning reporting, twenty warnings differing only by
a trailing `(case 0)`, `(case 1)`, ... produced twenty separate groups. The
grouping key for warnings is `(category, normalized message)`, and the built-in
normalizers only cover hex addresses and timestamps, so any variable content in a
warning message splits one warning into as many groups as it has variants.

This is the same failure mode that call-site grouping fixed for *failures*, still
present for warnings. Failures group by crash location, which is stable across
parameter values; warnings group by message, which is not.

## Why it might matter for a real suite

The MolSysMT pilot reported 216 warnings in 60 groups. If some of those groups
are variants of one warning — an atom name, a file path, a device identifier, an
array shape embedded in the text — then the real number of distinct warnings is
smaller, the section is more expensive than it needs to be, and, worse, a reader
scanning sixty lines has a harder time spotting the one that is actually new.

We cannot tell from here. A group per variant and a group per genuinely distinct
warning look identical in our output.

## What was requested

The `warnings:` section from the pilot's on-disk report
(`.pytest_cache/receptor/last-run.txt`, which carries untruncated messages,
unlike stdout), so the sixty groups can be inspected for variants.

## Options, once the evidence exists

1. **Nothing.** If the sixty groups are sixty genuinely different warnings, the
   current behaviour is correct and this proposal closes.
2. **Additional built-in normalizers**, chosen from what actually appears:
   quoted identifiers, absolute paths, `cuda:N` style device names, array
   shapes. Each one risks false equivalence and needs to earn its place.
3. **Warning-specific call-site grouping.** Warnings carry an origin
   (`filename:lineno`), already collected. Keying on `(category, origin)` rather
   than on the message would merge variants raised from one place, mirroring what
   failure grouping does — but would also merge genuinely different warnings
   emitted from a shared helper, which in a decorator-based stack could be most
   of them. The pilot's data would show which risk is real: their sample already
   shows two different categories sharing `argdigest/core/decorator.py:376`.

Option 3 is the most principled and the most dangerous. Do not implement any of
them before seeing the data.

## Related

- `PR-FID-009` — project-declared normalizers, already shipped. A project can fix
  this for itself today; the question is whether a default should exist.
- `resolved_bugs/warning_group_truncation_is_not_diagnostically_sufficient.md` —
  the report that established every group must be listed.
