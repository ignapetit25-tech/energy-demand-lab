import json
import tempfile
import unittest
from pathlib import Path

from src.analyze import DEFAULT_INPUT
from src.retrospective_diagnostics import (
    DEFAULT_SECTOR_INPUT,
    load_sector_rows,
    run_diagnostics,
)


class RetrospectiveDiagnosticTests(unittest.TestCase):
    def test_sector_data_is_complete_and_adds_to_total(self):
        rows = load_sector_rows(DEFAULT_SECTOR_INPUT)
        self.assertEqual(len(rows), 260)
        self.assertEqual(rows[0]["period"].isoformat(), "2005-01-01")
        self.assertEqual(rows[-1]["period"].isoformat(), "2026-08-01")
        for row in rows:
            component_sum = (
                row["residential_gwh"]
                + row["commerce_industry_gwh"]
                + row["large_users_gwh"]
            )
            self.assertAlmostEqual(row["total_gwh"], component_sum, places=3)

    def test_advanced_diagnostics_are_reproducible(self):
        with tempfile.TemporaryDirectory() as temporary:
            metrics = run_diagnostics(
                DEFAULT_INPUT, DEFAULT_SECTOR_INPUT, Path(temporary)
            )
            saved = json.loads((Path(temporary) / "metrics.json").read_text())
            self.assertEqual(metrics, saved)
            self.assertEqual(saved["design"]["shoulder_observations"], 63)
            self.assertEqual(
                saved["shoulder_by_feature_state"]["dead_band"]["observations"], 25
            )
            self.assertAlmostEqual(
                saved["shoulder_by_feature_state"]["dead_band"]["models"][
                    "expanding_temperature"
                ]["mae_gwh"],
                1222.297,
            )
            self.assertAlmostEqual(
                saved["shoulder_overall"]["calendar_trend"]["mean_error_gwh"],
                1050.92,
            )
            self.assertAlmostEqual(
                saved["sector_annual"]["2025"]["residential"]["share_percent"],
                46.66,
            )
            self.assertTrue((Path(temporary) / "coefficient_paths.csv").exists())
            self.assertTrue((Path(temporary) / "shoulder_decomposition.csv").exists())
            self.assertTrue((Path(temporary) / "sector_diagnostics.csv").exists())


if __name__ == "__main__":
    unittest.main()
