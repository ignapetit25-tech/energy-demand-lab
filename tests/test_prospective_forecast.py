import unittest
from datetime import date

from src.analyze import DEFAULT_INPUT, load_observations
from src.prospective_forecast import build_forecast


class ProspectiveForecastTests(unittest.TestCase):
    def test_october_forecast_is_reproducible_from_frozen_input(self):
        forecast = build_forecast(
            load_observations(DEFAULT_INPUT),
            date(2026, 10, 1),
            "2026-09-20T23:44:41-03:00",
        )
        self.assertEqual(forecast["latest_allowed_demand_period"], "2026-08-01")
        self.assertEqual(forecast["selected_window_months"], 120)
        self.assertAlmostEqual(forecast["seasonal_naive_gwh"], 10591.336)
        self.assertAlmostEqual(
            forecast["primary_adaptive_annual_change_gwh"], 10578.252
        )
        self.assertAlmostEqual(forecast["inner_mae_w120_gwh"], 592.267)


if __name__ == "__main__":
    unittest.main()
