import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.analyze import (
    DEFAULT_INPUT,
    HOLDOUT_START,
    Observation,
    degree_features,
    load_observations,
    run_analysis,
    sha256,
    solve_linear_system,
    validate_monthly_sequence,
)


class AnalysisTests(unittest.TestCase):
    def test_source_hash_is_frozen(self):
        self.assertEqual(sha256(DEFAULT_INPUT), "13e2b0d693b3a04e5efe74afcf3bf328bd68a6b7f93f78fde2f1a021dec68106")

    def test_monthly_source_is_complete_and_split_is_predefined(self):
        rows = load_observations(DEFAULT_INPUT)
        validate_monthly_sequence(rows)
        self.assertEqual(len(rows), 308)
        self.assertEqual(rows[0].period, date(2001, 1, 1))
        self.assertEqual(rows[-1].period, date(2026, 8, 1))
        self.assertEqual(sum(row.period >= HOLDOUT_START for row in rows), 56)

    def test_degree_features_have_dead_band(self):
        self.assertEqual(degree_features(12), (6.0, 0.0))
        self.assertEqual(degree_features(20), (0.0, 0.0))
        self.assertEqual(degree_features(27), (0.0, 5.0))

    def test_linear_solver(self):
        solution = solve_linear_system([[2.0, 1.0], [1.0, 3.0]], [5.0, 6.0])
        self.assertAlmostEqual(solution[0], 1.8)
        self.assertAlmostEqual(solution[1], 1.4)

    def test_analysis_is_reproducible(self):
        with tempfile.TemporaryDirectory() as temporary:
            metrics = run_analysis(DEFAULT_INPUT, Path(temporary))
            saved = json.loads((Path(temporary) / "metrics.json").read_text())
            self.assertEqual(metrics, saved)
            self.assertEqual(saved["data"]["holdout_observations"], 56)
            self.assertTrue(saved["hypothesis"]["passed"])
            self.assertFalse(saved["hypothesis"]["uncertainty_interval_excludes_zero"])
            self.assertAlmostEqual(saved["hypothesis"]["mae_improvement_percent"], 8.097)
            self.assertAlmostEqual(
                saved["benchmark_context"]["temperature_model_mae_increase_vs_seasonal_naive_percent"],
                46.138,
            )
            self.assertTrue((Path(temporary) / "predictions.csv").exists())
            self.assertTrue((Path(temporary) / "holdout_predictions.svg").exists())


if __name__ == "__main__":
    unittest.main()
