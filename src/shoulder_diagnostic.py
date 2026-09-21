#!/usr/bin/env python3
"""Diagnose shoulder-month errors in the rolling electricity-demand benchmark."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

try:
    from .analyze import (
        DEFAULT_INPUT,
        Observation,
        degree_features,
        fit_ols,
        load_observations,
        mean,
        model_metrics,
        predict,
        solve_linear_system,
        validate_monthly_sequence,
    )
    from .rolling_backtest import ROLLING_START, season
except ImportError:  # Direct execution: python3 src/shoulder_diagnostic.py
    from analyze import (
        DEFAULT_INPUT,
        Observation,
        degree_features,
        fit_ols,
        load_observations,
        mean,
        model_metrics,
        predict,
        solve_linear_system,
        validate_monthly_sequence,
    )
    from rolling_backtest import ROLLING_START, season


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "results"
RECENT_WINDOW_MONTHS = 60


def annual_change_features(row: Observation, previous_year: Observation) -> list[float]:
    heating, cooling = degree_features(row.temperature_c)
    previous_heating, previous_cooling = degree_features(previous_year.temperature_c)
    features = [1.0]
    features.extend(1.0 if row.period.month == month else 0.0 for month in range(2, 13))
    features.extend((heating - previous_heating, cooling - previous_cooling))
    return features


def fit_annual_change(
    rows: list[Observation], by_period: dict[date, Observation]
) -> list[float]:
    examples: list[tuple[list[float], float]] = []
    for row in rows:
        lag_period = date(row.period.year - 1, row.period.month, 1)
        if lag_period not in by_period:
            continue
        previous_year = by_period[lag_period]
        examples.append(
            (annual_change_features(row, previous_year), row.demand_gwh - previous_year.demand_gwh)
        )
    width = len(examples[0][0])
    xtx = [[0.0 for _ in range(width)] for _ in range(width)]
    xty = [0.0 for _ in range(width)]
    for features, target in examples:
        for left in range(width):
            xty[left] += features[left] * target
            for right in range(width):
                xtx[left][right] += features[left] * features[right]
    return solve_linear_system(xtx, xty)


def predict_annual_change(
    row: Observation, previous_year: Observation, coefficients: list[float]
) -> float:
    change = sum(
        value * coefficient
        for value, coefficient in zip(annual_change_features(row, previous_year), coefficients)
    )
    return previous_year.demand_gwh + change


def diagnostic_predictions(rows: list[Observation]) -> list[dict[str, float | int | str]]:
    by_period = {row.period: row for row in rows}
    records: list[dict[str, float | int | str]] = []
    for target in (row for row in rows if row.period >= ROLLING_START):
        train = [row for row in rows if row.period < target.period]
        previous_year = by_period[date(target.period.year - 1, target.period.month, 1)]
        expanding = predict(target, fit_ols(train, include_temperature=True), True)
        recent = predict(
            target,
            fit_ols(train[-RECENT_WINDOW_MONTHS:], include_temperature=True),
            True,
        )
        change_coefficients = fit_annual_change(train, by_period)
        annual_change = predict_annual_change(target, previous_year, change_coefficients)
        heating, cooling = degree_features(target.temperature_c)
        predictions = {
            "seasonal_naive": previous_year.demand_gwh,
            "expanding_temperature": expanding,
            "recent_60m_temperature": recent,
            "annual_change_temperature": annual_change,
        }
        record: dict[str, float | int | str] = {
            "period": target.period.isoformat(),
            "season": season(target.period),
            "month": target.period.month,
            "period_bucket": (
                "2016-2019"
                if target.period.year <= 2019
                else "2020-2022"
                if target.period.year <= 2022
                else "2023-2026"
            ),
            "training_observations": len(train),
            "temperature_c": round(target.temperature_c, 3),
            "temperature_feature_state": (
                "heating" if heating > 0 else "cooling" if cooling > 0 else "dead_band"
            ),
            "actual_gwh": round(target.demand_gwh, 3),
        }
        for name, prediction in predictions.items():
            error = prediction - target.demand_gwh
            record[f"{name}_gwh"] = round(prediction, 3)
            record[f"{name}_error_gwh"] = round(error, 3)
            record[f"{name}_abs_error_gwh"] = round(abs(error), 3)
        record["expanding_excess_abs_error_vs_naive_gwh"] = round(
            float(record["expanding_temperature_abs_error_gwh"])
            - float(record["seasonal_naive_abs_error_gwh"]),
            3,
        )
        records.append(record)
    return records


MODEL_COLUMNS = {
    "seasonal_naive": "seasonal_naive_gwh",
    "expanding_temperature": "expanding_temperature_gwh",
    "recent_60m_temperature": "recent_60m_temperature_gwh",
    "annual_change_temperature": "annual_change_temperature_gwh",
}


def metrics_for(records: list[dict[str, float | int | str]]) -> dict[str, dict[str, float]]:
    actual = [float(record["actual_gwh"]) for record in records]
    return {
        name: model_metrics(actual, [float(record[column]) for record in records])
        for name, column in MODEL_COLUMNS.items()
    }


def activation_summary(records: list[dict[str, float | int | str]]) -> dict[str, object]:
    def summarize(subset: list[dict[str, float | int | str]]) -> dict[str, float | int]:
        total = len(subset)
        return {
            "observations": total,
            "dead_band_percent": round(
                100 * mean(record["temperature_feature_state"] == "dead_band" for record in subset),
                3,
            ),
            "heating_active_percent": round(
                100 * mean(record["temperature_feature_state"] == "heating" for record in subset),
                3,
            ),
            "cooling_active_percent": round(
                100 * mean(record["temperature_feature_state"] == "cooling" for record in subset),
                3,
            ),
        }

    return {
        "by_season": {
            label: summarize([record for record in records if record["season"] == label])
            for label in ("warm", "cold", "shoulder")
        },
        "by_month": {
            str(month): summarize([record for record in records if record["month"] == month])
            for month in range(1, 13)
        },
    }


def run_diagnostic(input_path: Path, output_dir: Path) -> dict[str, object]:
    rows = load_observations(input_path)
    validate_monthly_sequence(rows)
    records = diagnostic_predictions(rows)
    shoulder = [record for record in records if record["season"] == "shoulder"]
    top_losses = sorted(
        shoulder,
        key=lambda record: float(record["expanding_excess_abs_error_vs_naive_gwh"]),
        reverse=True,
    )[:10]
    positive_excess = sum(
        max(0.0, float(record["expanding_excess_abs_error_vs_naive_gwh"]))
        for record in shoulder
    )
    top_positive_excess = sum(
        max(0.0, float(record["expanding_excess_abs_error_vs_naive_gwh"]))
        for record in top_losses
    )
    by_season = {
        label: metrics_for([record for record in records if record["season"] == label])
        for label in ("warm", "cold", "shoulder")
    }
    by_month = {
        str(month): metrics_for([record for record in records if record["month"] == month])
        for month in range(1, 13)
    }
    by_period = {
        bucket: metrics_for([record for record in records if record["period_bucket"] == bucket])
        for bucket in ("2016-2019", "2020-2022", "2023-2026")
    }
    shoulder_models = by_season["shoulder"]
    metrics: dict[str, object] = {
        "design": {
            "forecasts": len(records),
            "first_forecast": records[0]["period"],
            "last_forecast": records[-1]["period"],
            "shoulder_months": [3, 4, 5, 9, 10, 11],
            "recent_window_months": RECENT_WINDOW_MONTHS,
            "observed_temperature_oracle": True,
        },
        "feature_activation": activation_summary(records),
        "overall": metrics_for(records),
        "by_season": by_season,
        "by_month": by_month,
        "by_period": by_period,
        "shoulder_error_concentration": {
            "gross_positive_excess_abs_error_gwh": round(positive_excess, 3),
            "top_10_share_of_gross_positive_excess_percent": round(
                100 * top_positive_excess / positive_excess, 3
            ),
            "top_10_losses": [
                {
                    "period": record["period"],
                    "actual_gwh": record["actual_gwh"],
                    "temperature_c": record["temperature_c"],
                    "feature_state": record["temperature_feature_state"],
                    "seasonal_naive_abs_error_gwh": record["seasonal_naive_abs_error_gwh"],
                    "expanding_temperature_abs_error_gwh": record[
                        "expanding_temperature_abs_error_gwh"
                    ],
                    "excess_abs_error_gwh": record[
                        "expanding_excess_abs_error_vs_naive_gwh"
                    ],
                }
                for record in top_losses
            ],
        },
        "interpretation_inputs": {
            "shoulder_dead_band_percent": activation_summary(records)["by_season"]["shoulder"][
                "dead_band_percent"
            ],
            "shoulder_expanding_mean_error_gwh": shoulder_models["expanding_temperature"][
                "mean_error_gwh"
            ],
            "shoulder_recent_60m_mae_gwh": shoulder_models["recent_60m_temperature"]["mae_gwh"],
            "shoulder_annual_change_mae_gwh": shoulder_models["annual_change_temperature"][
                "mae_gwh"
            ],
            "shoulder_seasonal_naive_mae_gwh": shoulder_models["seasonal_naive"]["mae_gwh"],
        },
        "boundaries": [
            "This is a prespecified exploratory diagnostic after the rolling-origin result.",
            "The alternative models are diagnostic probes and were not subjected to a new confirmation set.",
            "Observed current-month temperature makes all temperature models oracle benchmarks.",
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "shoulder_diagnostic_predictions.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    (output_dir / "shoulder_diagnostic_metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    activation = metrics["interpretation_inputs"]["shoulder_dead_band_percent"]
    expanding = shoulder_models["expanding_temperature"]
    recent = shoulder_models["recent_60m_temperature"]
    change = shoulder_models["annual_change_temperature"]
    naive = shoulder_models["seasonal_naive"]
    report = f"""# Shoulder-month diagnostic results

## Main finding

The failure is driven primarily by **level and trend misspecification**, not simply by inactive temperature features. During shoulder months, the expanding temperature model overpredicts demand by **{expanding['mean_error_gwh']:.1f} GWh on average** and has MAE of **{expanding['mae_gwh']:.1f} GWh**, versus **{naive['mae_gwh']:.1f} GWh** for seasonal naive.

Temperature sits inside the 18-22 C dead band in **{activation:.1f}%** of shoulder forecasts. That contributes to the problem because the weather terms cannot correct the level model in those observations, but it is not a complete explanation: the long-run linear trend is already extrapolating too high.

## Diagnostic alternatives

| Model | Shoulder MAE GWh | Shoulder mean error GWh |
| --- | ---: | ---: |
| Seasonal naive | {naive['mae_gwh']:.1f} | {naive['mean_error_gwh']:.1f} |
| Expanding trend and temperature | {expanding['mae_gwh']:.1f} | {expanding['mean_error_gwh']:.1f} |
| Recent 60-month trend and temperature | {recent['mae_gwh']:.1f} | {recent['mean_error_gwh']:.1f} |
| Annual-change temperature model | {change['mae_gwh']:.1f} | {change['mean_error_gwh']:.1f} |

The recent-window probe tests whether old history is distorting the trend. The annual-change probe anchors each forecast on the same month one year earlier and estimates only the change associated with weather differences. These are exploratory results, not a new confirmed winner.

## Error concentration

The ten largest shoulder-month losses account for **{metrics['shoulder_error_concentration']['top_10_share_of_gross_positive_excess_percent']:.1f}%** of the expanding model's gross positive excess absolute error relative to seasonal naive. This means unusual months matter, but the weakness is not safely reducible to a single outlier.

## Interpretation boundary

This diagnostic preserves the original results. It does not justify causal conclusions or production use, and every temperature model still receives observed current-month temperature.
"""
    (output_dir / "shoulder_diagnostic_report.md").write_text(report, encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    metrics = run_diagnostic(args.input, args.output)
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
