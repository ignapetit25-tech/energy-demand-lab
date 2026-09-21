import json
import tempfile
import unittest
from pathlib import Path

from src.analyze import DEFAULT_INPUT, load_observations
from src.shoulder_diagnostic import diagnostic_predictions, run_diagnostic


class ShoulderDiagnosticTests(unittest.TestCase):
    def test_diagnostic_preserves_rolling_coverage(self):
        records = diagnostic_predictions(load_observations(DEFAULT_INPUT))
        self.assertEqual(len(records), 128)
        self.assertEqual(records[0]["period"], "2016-01-01")
        self.assertEqual(records[0]["training_observations"], 180)
        self.assertEqual(records[-1]["period"], "2026-08-01")
        self.assertEqual(records[-1]["training_observations"], 307)

    def test_shoulder_diagnostic_is_reproducible(self):
        with tempfile.TemporaryDirectory() as temporary:
            metrics = run_diagnostic(DEFAULT_INPUT, Path(temporary))
            saved = json.loads(
                (Path(temporary) / "shoulder_diagnostic_metrics.json").read_text()
            )
            self.assertEqual(metrics, saved)
            self.assertAlmostEqual(
                saved["interpretation_inputs"]["shoulder_dead_band_percent"], 39.683
            )
            self.assertAlmostEqual(
                saved["interpretation_inputs"]["shoulder_expanding_mean_error_gwh"],
                1029.417,
            )
            self.assertAlmostEqual(
                saved["interpretation_inputs"]["shoulder_recent_60m_mae_gwh"],
                362.154,
            )
            self.assertTrue(
                (Path(temporary) / "shoulder_diagnostic_predictions.csv").exists()
            )
            self.assertTrue((Path(temporary) / "shoulder_diagnostic_report.md").exists())


if __name__ == "__main__":
    unittest.main()
