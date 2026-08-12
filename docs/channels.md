# Output channels and authority

`pytest-receptor` uses three channels deliberately. They are complementary;
none is a hidden fallback for a different channel.

## Process exit status

Pytest's process exit status is the authority for automation. The receptor
never changes it, including when it refines the human-readable label or when
its own renderer fails.

Examples of label refinement are `COLLECTION_ERROR exit=2` versus
`INTERRUPTED exit=2`, and `USAGE_ERROR exit=5 | invalid selection` when xdist
uses its no-tests status for explicit targets that do not exist. The number is
still pytest's original status.

## Standard output

Stdout carries the final receptor report. The first line of the
**receptor-owned block** is the verdict, exit status, and counts. The block is
plain text, deterministic for the same evidence, stripped of ANSI/control
characters, and sanitized before rendering.

The whole stdout stream is not exclusively owned by the receptor. A compatible
third-party plugin may publish its own terminal summary, and a process writing
directly to file descriptor 1 can bypass pytest's terminal writer. The receptor
silences pytest's presentation without unregistering that reporter or silencing
other plugins.

Test-produced stdout is evidence, not control input. When relevant to a failure
it appears inside an explicitly labelled `captured stdout` section.

## Standard error

Stderr carries bounded liveness progress after the twenty-second warm-up. It
never carries the receptor's final verdict. Pytest, native code, or another
plugin may also write exceptional diagnostics there.

Discarding stderr leaves the receptor report parseable, but intentionally loses
the live progress signal and may lose diagnostics owned by pytest or another
plugin.

## On-disk full report

When pytest's cache provider is available, the full plain-text report is
published at session finish under the path printed by the receptor, normally
`.pytest_cache/d/receptor/last-run.txt`.

- A previous report is removed at session start, so absence means “not yet”.
- Publication happens once, after the complete report has been rendered.
- The file is owner-only and a symlink is never followed.
- The same sanitization and redaction used for stdout is applied before writing.
- If the report cannot be written, compact output holds nothing back that would
  otherwise be recoverable only from that file.
- `-p no:cacheprovider` disables the report explicitly.

This file is the complete presentation artifact. It is separate from the
opt-in, versioned JSONL evidence stream produced by `--receptor-events`; see
[Versioned evidence artifacts](artifacts.md).

## Versioned JSONL artifact

When explicitly requested, JSONL is streamed to the supplied path as normalized
events arrive. A final `session_finish` record and its integrity metadata make a
completed stream distinguishable from partial evidence left by an interrupted
process. The supported Python reader validates that distinction. This artifact
is the machine-oriented receptor evidence channel; pytest's process status
remains the authority for the process that produced it.

## Independent machine evidence

JUnit XML remains independent pytest-owned evidence when requested with
`--junitxml`. Compact reporting and the receptor artifact must not suppress or
mutate it. Keeping both is useful for parity audits and third-party tooling.

In short:

| Need | Authority |
| :--- | :--- |
| Did the process succeed? | pytest process exit status |
| What should an agent read first? | receptor block on stdout |
| Is a long run still advancing? | receptor progress on stderr |
| What compact detail was omitted? | on-disk full report |
| What normalized receptor evidence should a tool read? | versioned JSONL artifact |
| What independent machine evidence can CI compare? | pytest JUnit XML |
