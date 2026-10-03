"""Exercise the issue-backed reporting guard without scientific dependencies."""

from __future__ import annotations

import importlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "devtools"))
devguide_reports = importlib.import_module("devguide_reports")


class TestReportingProtocol(unittest.TestCase):
    def test_existing_reports_have_valid_metadata_and_generated_indexes(self):
        reports, errors = devguide_reports.validate_all()
        self.assertEqual(errors, [])
        self.assertTrue(
            {
                "uibcdf/pytest-receptor#3",
                "uibcdf/pytest-receptor#4",
                "uibcdf/pytest-receptor#5",
                "uibcdf/pytest-receptor#6",
                "uibcdf/pytest-receptor#8",
                "uibcdf/pytest-receptor#9",
                "uibcdf/pytest-receptor#10",
                "uibcdf/pytest-receptor#12",
                "uibcdf/pytest-receptor#11",
            }
            <= {report.fields["issue"] for report in reports},
        )
        legacy, legacy_errors = devguide_reports.load_legacy_reports()
        self.assertEqual(legacy_errors, [])
        self.assertEqual(legacy, [])
        result = subprocess.run(
            [sys.executable, "devtools/devguide_index.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_issue_and_false_closure_are_rejected(self):
        reports, _ = devguide_reports.validate_all()
        pending = next(
            report
            for report in reports
            if report.fields["issue"] == "uibcdf/pytest-receptor#9"
        )
        fields = dict(pending.fields)
        fields["issue"] = ""
        fields["status"] = "resolved"
        fields["closed"] = ""
        fields["guard"] = ""
        fields["normative"] = ""
        invalid = devguide_reports.Report(
            pending.path, fields, pending.kind, pending.archived
        )
        errors = devguide_reports.validate_report(invalid)
        self.assertTrue(any("issue must be" in error for error in errors))
        self.assertTrue(any("closed reports belong" in error for error in errors))
        self.assertTrue(any("requires an ISO closed date" in error for error in errors))
        self.assertTrue(any("requires guard or normative" in error for error in errors))

    def test_guard_selectors_are_addressable(self):
        self.assertEqual(
            devguide_reports.validate_guard(
                "tests/test_plugin.py::test_late_terminal_discard_stream_is_closed"
            ),
            [],
        )
        self.assertTrue(
            devguide_reports.validate_guard("tests/test_plugin.py::test_missing")
        )
        self.assertTrue(devguide_reports.validate_guard("python arbitrary_command.py"))

    def test_retired_exception_has_no_expiry_debt_and_cannot_be_reopened(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "legacy.toml"
            manifest.write_text(
                'owner = "uibcdf/pytest-receptor#10"\n'
                'review_due = "2000-01-01"\n'
                'retired = "2026-10-03"\n'
                "legacy-reports = []\n",
                encoding="utf-8",
            )
            with patch.object(devguide_reports, "LEGACY_MANIFEST", manifest):
                self.assertEqual(devguide_reports.load_legacy_reports(), ([], []))
                manifest.write_text(
                    manifest.read_text().replace("legacy-reports = []\n", "")
                    + "[[legacy-reports]]\n"
                    + 'path = "devguide/resolved_bugs/setup_errors_counted_as_failed.md"\n'
                    + 'register = "PR-PILOT-001"\n'
                    + 'resolved = "2026-07-18"\n',
                    encoding="utf-8",
                )
                _legacy, errors = devguide_reports.load_legacy_reports()
                self.assertTrue(
                    any("cannot accept entries" in error for error in errors)
                )

    def test_live_legacy_exception_still_expires(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "devguide/resolved_bugs"
            archive.mkdir(parents=True)
            (archive / "test_history.md").write_text("# Original report\n")
            manifest = root / "legacy.toml"
            manifest.write_text(
                'owner = "uibcdf/pytest-receptor#10"\n'
                'review_due = "2000-01-01"\n'
                "[[legacy-reports]]\n"
                'path = "devguide/resolved_bugs/test_history.md"\n'
                'register = "PR-PILOT-001"\n'
                'resolved = "2026-07-18"\n',
                encoding="utf-8",
            )
            with (
                patch.object(devguide_reports, "ROOT", root),
                patch.object(devguide_reports, "LEGACY_MANIFEST", manifest),
            ):
                _legacy, errors = devguide_reports.load_legacy_reports()
                self.assertIn("legacy report exception review is overdue", errors)


if __name__ == "__main__":
    unittest.main()
