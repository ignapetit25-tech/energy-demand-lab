import json
import tempfile
import unittest
from pathlib import Path

from src.analyze import DEFAULT_INPUT, load_observations
from src.nested_validation import nested_predictions, run_nested


class NestedValidationTests(unittest.TestCase):
    def test_nested_forecasts_enforce_two_month_demand_lag(self):
        records = nested_predictions(load_observations(DEFAULT_INPUT))
        self.assertEqual(len(records), 128)
        self.assertEqual(records[0]["period"], "2016-01-01")
        self.assertEqual(records[0]["latest_allowed_demand_period"], "2015-11-01")
        self.assertEqual(records[-1]["period"], "2026-08-01")
        self.assertEqual(records[-1]["latest_allowed_demand_period"], "2026-06-01")

    def test_nested_results_are_reproducible(self):
        with tempfile.TemporaryDirectory() as temporary:
            metrics = run_nested(DEFAULT_INPUT, Path(temporary))
            saved = json.loads((Path(temporary) / "metrics.json").read_text())
            self.assertEqual(metrics, saved)
            self.assertAlmostEqual(
                saved["overall"]["adaptive_annual_change_honest"]["mae_gwh"],
                622.376,
            )
            self.assertAlmostEqual(
                saved["overall"]["adaptive_annual_change_temperature_oracle"]["mae_gwh"],
                393.868,
            )
            self.assertEqual(saved["window_selection_frequency"]["honest"]["120"], 108)
            self.assertEqual(
                saved[
                    "seasonal_naive_minus_adaptive_honest_mae_year_block_95_interval_gwh"
                ],
                [-99.057, -13.791],
            )
            self.assertTrue((Path(temporary) / "predictions.csv").exists())
            self.assertTrue((Path(temporary) / "report.md").exists())


if __name__ == "__main__":
    unittest.main()
