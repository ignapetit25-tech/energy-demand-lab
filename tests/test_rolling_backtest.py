import json
import tempfile
import unittest
from pathlib import Path

from src.analyze import DEFAULT_INPUT, load_observations
from src.rolling_backtest import rolling_predictions, run_backtest, season


class RollingBacktestTests(unittest.TestCase):
    def test_southern_hemisphere_seasons(self):
        rows = load_observations(DEFAULT_INPUT)
        self.assertEqual(season(rows[0].period), "warm")
        self.assertEqual(season(rows[5].period), "cold")
        self.assertEqual(season(rows[3].period), "shoulder")

    def test_rolling_origins_use_only_earlier_demand_observations(self):
        records = rolling_predictions(load_observations(DEFAULT_INPUT))
        self.assertEqual(len(records), 128)
        self.assertEqual(records[0]["period"], "2016-01-01")
        self.assertEqual(records[0]["training_observations"], 180)
        self.assertEqual(records[-1]["period"], "2026-08-01")
        self.assertEqual(records[-1]["training_observations"], 307)

    def test_backtest_outputs_are_reproducible(self):
        with tempfile.TemporaryDirectory() as temporary:
            metrics = run_backtest(DEFAULT_INPUT, Path(temporary))
            saved = json.loads((Path(temporary) / "rolling_metrics.json").read_text())
            self.assertEqual(metrics, saved)
            self.assertEqual(saved["design"]["forecasts"], 128)
            self.assertFalse(saved["usefulness_gate"]["passed"])
            self.assertEqual(saved["usefulness_gate"]["complete_years_won"], 2)
            self.assertAlmostEqual(
                saved["comparisons"]["temperature_mae_change_vs_seasonal_naive_percent"],
                33.386,
            )
            self.assertAlmostEqual(
                saved["comparisons"]["temperature_mae_improvement_vs_calendar_percent"],
                10.111,
            )
            self.assertEqual(
                saved["comparisons"]["seasonal_naive_minus_temperature_mae_year_block_95_interval_gwh"],
                [-370.725, -41.13],
            )
            self.assertTrue((Path(temporary) / "rolling_predictions.csv").exists())
            self.assertTrue((Path(temporary) / "rolling_mae_by_year.svg").exists())
            self.assertTrue((Path(temporary) / "rolling_report.md").exists())


if __name__ == "__main__":
    unittest.main()
