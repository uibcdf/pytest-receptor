# Decision: `pytest-reportlog` and the canonical artifact gate

**Recorded:** 2026-07-22
**Status:** decided. Resolves the "Canonical artifact" architecture decision gate
and unblocks `PR-ARCH-001` (the normalized event model). Does **not** schedule
its implementation — that still waits on real consumer demand.

**Method:** measured, not recalled. `pytest-reportlog==1.0.0` was installed and
run against probe suites (serial and `-n 2`) and its JSONL inspected directly.
Every claim below about what it emits is from that output.

---

## The question the gate asks

Before designing any bespoke JSONL schema for the receptor's evidence artifact,
evaluate `pytest-reportlog`, "which already streams per-report JSONL and may make
a bespoke schema unnecessary" (register, current-to-target matrix). Reuse it if
it suffices; build bespoke only if it does not.

## What `pytest-reportlog` actually is

An official pytest plugin. `--report-log=FILE` appends one JSON object per line,
one per report event, as the run proceeds. Each line is a **serialization of the
pytest report object** the plugin's hooks receive — the same objects the receptor
already consumes live through its own hooks.

### What it emits (observed)

Record types seen: `SessionStart`, `SessionFinish`, `CollectReport`,
`TestReport`, `WarningMessage`.

A `TestReport` (call phase) carries:

```
$report_type, nodeid, location, when, outcome, duration, start, stop,
keywords, user_properties, sections, longrepr
```

and under `-n 2` it additionally carries `worker_id`, `node`, `item_index`, and
`testrun_uid` — so **worker provenance, a run identifier, and a per-item index
are present under xdist** (this corrected an earlier assumption that they were
not).

`longrepr` for a failure is a dict: `reprcrash {path, lineno, message}`,
`reprtraceback {reprentries}`, `chain` (the cause/context chain), and `sections`.

`WarningMessage` carries `category` (as a name string), `filename`, `lineno`,
`message`, `when` — so warnings are captured, with a structured category.

`SessionFinish` carries `exitstatus`.

### What it does **not** provide

1. **A structured exception type.** `reprcrash.message` is the formatted text,
   e.g. `"AssertionError: assert {'a': 1} == {'a': 2}\n  ..."`. There is no
   exception-type field; a consumer still parses the type out of the message —
   the exact thing `PR-ARCH-001` exists to stop doing. reportlog inherits this
   because it serializes pytest's repr, and pytest does not expose the type
   separately there. **The receptor already has this same `reprcrash` live**, so
   reportlog gives it no exception data it does not already hold.
2. **Redaction, restrictive permissions, symlink safety.** reportlog writes
   `sections` and `longrepr` verbatim with default file permissions. It applies
   no redaction and makes no ownership guarantee. This is in direct conflict with
   `PR-SEC-002` (owner-only report, symlink refusal, credential redaction before
   anything is written).
3. **A derived, normalized session outcome.** `exitstatus` is present, but the
   completeness story — stop reason, not-executed count, deselected count — is
   not aggregated. It is recomputable by counting the stream, which is exactly
   the ambiguous-bucket counting the receptor deliberately replaced.
4. **Grouping, fingerprints, stable diagnostic event identifiers.** Not its job.
5. **Bounded records and external blobs / content hashes.** Large captures and
   longreprs are inline and unbounded.
6. **An environment manifest and a stable, self-describing schema version.** The
   record shape is implicitly pytest's, so it is **coupled to the pytest
   version**, not to a schema the receptor controls and can promise consumers.
7. **Any extension-event mechanism.** No way for a third-party producer
   (SMonitor and, across the eight MolSysSuite repos, others) to attach a
   namespaced payload correlated to a test occurrence.

## Evaluation

| Requirement (architecture proposal, Layer 1–2) | reportlog |
| :--- | :--- |
| Per-report stream, streamable JSONL | ✅ yes |
| Session start/finish, exit status | ✅ yes |
| Per-phase reports (setup/call/teardown), durations, sections | ✅ yes |
| Warnings with category | ✅ yes |
| xdist worker id, run id, item index | ✅ yes |
| Traceback entries with path/line; cause chain | ✅ (as repr) |
| Incomplete detectable (missing `SessionFinish`) | ✅ yes |
| **Structured exception type (not parsed from text)** | ❌ no |
| **Redaction / owner-only / symlink safety** | ❌ no |
| Normalized completeness (stop reason, not-executed) | ❌ derive |
| Reversible grouping, fingerprints, event ids | ❌ no |
| Bounded records + external blobs + hashes | ❌ no |
| Receptor-owned, version-stable schema + env manifest | ❌ no |
| Namespaced extension events | ❌ no |

## Decision

**Build the bespoke normalized event model (`pytest-receptor.events@N`). Do not
adopt `pytest-reportlog` as the receptor's canonical artifact.**

The reason is not that reportlog is weak — it is a good tool and, on raw report
capture and xdist provenance, better than assumed. The reason is that reportlog
serializes *pytest's report stream*, and the receptor's artifact must be a
*diagnostic evidence model*: a semantic layer above the reports. Everything that
distinguishes the two is in reportlog's "does not provide" column, and two of
those are decisive, not cosmetic:

- **Redaction is non-negotiable and reportlog has none.** `PR-SEC-002` forbids
  writing captured output without redaction, owner-only permissions, and symlink
  safety. A public/default artifact that re-emits raw `sections` and longreprs
  cannot be the receptor's, whatever else it does well.
- **The typed-evidence goal is the whole point of `PR-ARCH-001`,** and reportlog
  leaves the exception type in formatted text exactly as the live reports do. It
  offers the receptor no data it does not already have live — only a format.

Coupling the receptor's promised schema to pytest's internal report shape (which
is what reusing reportlog means) also surrenders the versioned, stable contract a
consumer API needs.

## What to take from it anyway

Deciding against reuse is not deciding against learning from it:

- **Adopt its proven conventions** for the bespoke artifact: one JSON object per
  line, a `$report_type`-style tag on every record, append-as-you-go streaming,
  and "no final session record ⇒ interrupted" as the incomplete marker. These
  are the Layer-2 requirements, already validated in a maintained plugin.
- **Do not reimplement raw report capture.** A consumer who wants the unfiltered
  pytest report stream can enable `--report-log` themselves; the receptor should
  not reproduce it. The receptor's artifact stays a curated, redacted, typed,
  grouped semantic layer — orthogonal to reportlog, not a competitor.
- Its xdist fields (`worker_id`, `testrun_uid`, `item_index`) are a concrete
  reference for the provenance the bespoke model must carry.

## Where it lives — inside the receptor, not a second plugin

Deciding against reportlog does **not** mean building "our own reportlog" as a
separate package or plugin. The bespoke artifact is a layer **inside
`pytest-receptor`**, not a standalone tool.

The receptor already collects this evidence live — it must, to render the
compact text report at all (the `Occurrence`/`Group` records built in
`pytest_sessionfinish` from pytest's reports). The structured artifact is the
*same evidence serialized instead of rendered*, not a second collection.
`PR-ARCH-001` formalizes that shared collection into one normalized event model:

```
pytest hooks
     │
     ▼
  collector ──► normalized event model  (PR-ARCH-001)
                    │        │        │
                    ▼        ▼        ▼
              text render  JSONL      future consumer
              (today)      artifact   API
                           (opt-in)
```

So the JSONL artifact is an **opt-in output of the receptor itself** (behind a
flag), produced from the model that already feeds the text report — redacted,
typed, and grouped, which is the layer reportlog does not provide. reportlog
stays a *separate* plugin anyone can enable for raw pytest reports; the receptor
does not reproduce it.

Downstream, that artifact is also the anchor where SMonitor and a possible
`pytest-molsyssuite` would attach namespaced **extension events** (via
`PR-ARCH-002`) and from which they would read — but that is later and gated, and
still lives around the receptor's artifact, not in a separate reportlog-like
tool.

## Sequencing — decided is not scheduled

The gate is now resolved, which unblocks `PR-ARCH-001`. It does **not** mean the
event model should be built now:

- No consumer has yet asked for a machine-readable artifact. The MolSysMT pilot
  brief lists it under "not yet"; the plain-text report has been sufficient for
  every real cycle so far.
- The model's eventual consumers are SMonitor (diagnostic correlation) and a
  possible `pytest-molsyssuite` across the eight current MolSysSuite repos —
  `molsysmt`, `molsysviewer`, `topomt`, `elastnetmt`, `smonitor`,
  `pyunitwizard`, `argdigest`, `depdigest`. Those consumers need the namespaced
  **extension events** reportlog cannot carry, which reinforces this decision —
  and they are governed by `PR-ARCH-002` and the `pytest-molsyssuite` extraction
  gate, both of which are earlier in the queue and still open.

**Recommended trigger to start `PR-ARCH-001`:** the first real request from one of
those repos for structured output — a consumer that would read the artifact, not
a plausibility argument. Until then the decision is recorded and the work stays
deferred.

## Housekeeping

`pytest-reportlog==1.0.0` was installed into the working environment for this
evaluation. It is inert unless `--report-log` is passed and is not a project
dependency; remove it with `pip uninstall pytest-reportlog` if an unused plugin
in the environment is unwanted.
