# Pytest Receptor reporting protocol

This repository implements `uibcdf/molsyssuite`'s
`devguide/reporting_protocol.md`. The suite protocol defines issue identity,
statuses, closure evidence and exceptions; the local audit action register
continues to track release work and historical pilot identifiers.

Open `uibcdf/pytest-receptor#<number>` before adding a queued report. Copy
`devguide/templates/report.md`, remove `severity` for a proposal, and keep
analysis and evidence in the document. The GitHub issue holds public state
and settled facts. The internal PR-PILOT/PR-UX register does not replace the
owning GitHub issue for new reports.

- `devguide/pending_bugs/` holds open defects;
- `devguide/pending_proposals/` holds open proposals;
- `devguide/resolved_bugs/` and `devguide/resolved_proposals/` permanently
  retain closed records.

Set a closed status and date, cite a relevant durable `guard` or `normative`
document, move the report to the appropriate resolved directory and regenerate
the indexes. Close the issue with the result, evidence and archive path.
Preserve archived claims; append a dated correction if one proves false.

The default `guard` is a pytest selector under `tests/` or `devtools/tests/`.
The offline validator verifies that the selected function, class method or
module exists; a reviewer still checks relevance to the reported mechanism.

The seventeen pre-protocol documents remain at their original paths with
their original bodies preserved and dated issue-identity reviews appended.
`uibcdf/pytest-receptor#10` retired their exception on 2026-10-03. The empty
`devguide/legacy_report_manifest.toml` records that retirement and cannot
accept entries again; its former deadline creates no debt once it is empty.
Register references such as PR-PILOT and PR-UX remain historical evidence,
not substitutes for GitHub identities. Reuse an existing owning issue when
its scope matches; create a retrospective issue only after reviewing a real
independently closable theme and its evidence. If a historical diagnosis
cannot be established or was superseded, retain the original claim and
append the dated disposition rather than inventing a successful fix.

Run these offline checks after changing a report:

```bash
python devtools/devguide_index.py
python devtools/devguide_index.py --check
python -m unittest discover -s tests -p test_reporting_protocol.py
```

The standalone reporting-governance workflow runs the index check and
reporting tests independently of the plugin compatibility matrix.
