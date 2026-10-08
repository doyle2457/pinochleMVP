import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from discrepancy_reports import DiscrepancyReport, DiscrepancyReportStore


class DiscrepancyReportStoreTests(unittest.TestCase):
    def test_create_update_list_load_and_delete_report(self):
        with TemporaryDirectory() as directory:
            store = DiscrepancyReportStore(Path(directory))
            report = DiscrepancyReport.fresh()
            report.title = "Wrong player led the second trick"
            report.priority = "High"
            report.what_happened = "Player 2 was prompted to lead."
            report.expected_behavior = "Player 1 won and should lead."
            report.reproduction_steps = "1. Complete the first trick.\n2. Observe the hints."

            saved = store.save(report)
            self.assertEqual("DR-0001", saved.report_id)
            self.assertTrue((Path(directory) / "DR-0001.json").is_file())
            markdown_path = Path(directory) / "DR-0001.md"
            self.assertTrue(markdown_path.is_file())
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertIn("# DR-0001: Wrong player led the second trick", markdown)
            self.assertIn("**Priority:** High", markdown)
            self.assertIn("## Steps to reproduce", markdown)

            saved.status = "Analyzing"
            saved.disposition_category = "Fix Planned"
            saved.disposition = "Add a regression test for the next leader."
            store.save(saved)
            self.assertEqual(1, len(store.list()))
            loaded = store.load("DR-0001")
            self.assertEqual("Analyzing", loaded.status)
            self.assertEqual("Fix Planned", loaded.disposition_category)
            self.assertEqual(saved.disposition, loaded.disposition)
            self.assertIn(
                "**Disposition category:** Fix Planned",
                markdown_path.read_text(encoding="utf-8"),
            )

            store.delete("DR-0001")
            self.assertEqual([], store.list())
            self.assertFalse(markdown_path.exists())

    def test_report_ids_are_stable_and_incrementing(self):
        with TemporaryDirectory() as directory:
            store = DiscrepancyReportStore(Path(directory))
            first = DiscrepancyReport.fresh()
            first.title = "First"
            second = DiscrepancyReport.fresh()
            second.title = "Second"
            store.save(first)
            store.save(second)
            first.title = "Renamed first report"
            store.save(first)
            self.assertEqual("DR-0001", first.report_id)
            self.assertEqual("DR-0002", second.report_id)
            self.assertEqual(2, len(store.list()))

    def test_invalid_or_corrupt_reports_are_not_listed(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)
            path.mkdir(exist_ok=True)
            (path / "DR-0001.json").write_text("{broken", encoding="utf-8")
            (path / "DR-0002.json").write_text(
                json.dumps({"format_version": 999, "report": {}}),
                encoding="utf-8",
            )
            self.assertEqual([], DiscrepancyReportStore(path).list())

    def test_title_is_required(self):
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "title"):
                DiscrepancyReportStore(directory).save(DiscrepancyReport.fresh())

    def test_existing_report_without_disposition_category_remains_compatible(self):
        report = DiscrepancyReport.fresh()
        report.report_id = "DR-0001"
        report.title = "Legacy report"
        values = report.__dict__.copy()
        values.pop("disposition_category")
        restored = DiscrepancyReport.from_dict(values)
        self.assertEqual("", restored.disposition_category)

    def test_missing_fields_retain_model_defaults(self):
        restored = DiscrepancyReport.from_dict(
            {
                "report_id": "DR-0001",
                "title": "Legacy report",
                "reported_date": "2026-07-27",
            }
        )
        self.assertEqual("Medium", restored.priority)
        self.assertEqual("Reported", restored.status)

    def test_invalid_date_type_has_a_user_facing_validation_error(self):
        report = DiscrepancyReport.fresh()
        report.title = "Invalid date"
        report.reported_date = None
        with self.assertRaisesRegex(ValueError, "valid report date"):
            report.validate()

    def test_failed_save_does_not_assign_an_id(self):
        report = DiscrepancyReport.fresh()
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "title"):
                DiscrepancyReportStore(directory).save(report)
        self.assertEqual("", report.report_id)
        self.assertEqual("", report.created_at)

    def test_id_allocation_does_not_overwrite_orphaned_markdown(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "DR-0001.md").write_text("Existing report\n", encoding="utf-8")
            report = DiscrepancyReport.fresh()
            report.title = "New report"
            DiscrepancyReportStore(path).save(report)
            self.assertEqual("DR-0002", report.report_id)
            self.assertEqual(
                "Existing report\n",
                (path / "DR-0001.md").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
