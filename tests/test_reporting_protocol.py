"""Exercise the issue-backed reporting guard without scientific dependencies."""

from __future__ import annotations

import importlib
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "devtools"))
devguide_reports = importlib.import_module("devguide_reports")


class TestReportingProtocol(unittest.TestCase):
    def test_existing_reports_have_valid_metadata_and_generated_indexes(self):
        reports, errors = devguide_reports.validate_all()
        self.assertEqual(errors, [])
        self.assertEqual(
            {report.fields["issue"] for report in reports},
            {
                "uibcdf/elastnetmt#19",
                "uibcdf/elastnetmt#21",
                "uibcdf/elastnetmt#23",
                "uibcdf/elastnetmt#18",
                "uibcdf/elastnetmt#14",
                "uibcdf/elastnetmt#16",
                "uibcdf/elastnetmt#17",
            },
        )
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
            if report.fields["issue"] == "uibcdf/elastnetmt#14"
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
                "tests/test_reporting_protocol.py::TestReportingProtocol::test_guard_selectors_are_addressable"
            ),
            [],
        )
        self.assertTrue(
            devguide_reports.validate_guard("tests/test_import.py::test_missing")
        )
        self.assertTrue(devguide_reports.validate_guard("python arbitrary_command.py"))


if __name__ == "__main__":
    unittest.main()
