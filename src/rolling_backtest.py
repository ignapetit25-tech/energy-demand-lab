#!/usr/bin/env python3
"""Run an expanding-window monthly backtest for electricity demand models."""

from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date
from pathlib import Path

try:
    from .analyze import (
        DEFAULT_INPUT,
        Observation,
        fit_ols,
        load_observations,
        mean,
        model_metrics,
        predict,
        validate_monthly_sequence,
    )
except ImportError:  # Direct execution: python3 src/rolling_backtest.py
    from analyze import (
        DEFAULT_INPUT,
        Observation,
        fit_ols,
        load_observations,
        mean,
        model_metrics,
        predict,
        validate_monthly_sequence,
    )


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "results"
ROLLING_START = date(2016, 1, 1)
COMPLETE_YEARS = tuple(range(2016, 2026))


def season(period: date) -> str:
    if period.month in (12, 1, 2):
        return "warm"
    if period.month in (6, 7, 8):
        return "cold"
    return "shoulder"


def error_metrics(records: list[dict[str, float | int | str]], prediction_key: str) -> dict[str, float]:
    actual = [float(record["actual_gwh"]) for record in records]
    predicted = [float(record[prediction_key]) for record in records]
    return model_metrics(actual, predicted)


def year_block_interval(
    records: list[dict[str, float | int | str]], iterations: int = 5_000
) -> tuple[float, float]:
    by_year: dict[int, list[float]] = {}
    for record in records:
        improvement = float(record["seasonal_naive_abs_error_gwh"]) - float(
            record["temperature_model_abs_error_gwh"]
        )
        by_year.setdefault(int(str(record["period"])[:4]), []).append(improvement)
    years = sorted(by_year)
    generator = random.Random(42)
    estimates: list[float] = []
    for _ in range(iterations):
        selected_years = [generator.choice(years) for _ in years]
        estimates.append(mean(value for year in selected_years for value in by_year[year]))
    estimates.sort()
    return (
        round(estimates[int(iterations * 0.025)], 3),
        round(estimates[int(iterations * 0.975)], 3),
    )


def rolling_predictions(rows: list[Observation]) -> list[dict[str, float | int | str]]:
    by_period = {row.period: row for row in rows}
    records: list[dict[str, float | int | str]] = []
    for target in (row for row in rows if row.period >= ROLLING_START):
        train = [row for row in rows if row.period < target.period]
        previous_year = date(target.period.year - 1, target.period.month, 1)
        naive = by_period[previous_year].demand_gwh
        calendar = predict(target, fit_ols(train, include_temperature=False), include_temperature=False)
        temperature = predict(target, fit_ols(train, include_temperature=True), include_temperature=True)
        records.append(
            {
                "period": target.period.isoformat(),
                "season": season(target.period),
                "training_observations": len(train),
                "temperature_c": round(target.temperature_c, 3),
                "actual_gwh": round(target.demand_gwh, 3),
                "seasonal_naive_gwh": round(naive, 3),
                "calendar_model_gwh": round(calendar, 3),
                "temperature_model_gwh": round(temperature, 3),
                "seasonal_naive_abs_error_gwh": round(abs(naive - target.demand_gwh), 3),
                "calendar_model_abs_error_gwh": round(abs(calendar - target.demand_gwh), 3),
                "temperature_model_abs_error_gwh": round(abs(temperature - target.demand_gwh), 3),
            }
        )
    return records


def write_year_chart(yearly: dict[str, dict[str, dict[str, float]]], path: Path) -> None:
    width, height = 1_200, 600
    left, right, top, bottom = 82, 32, 54, 78
    plot_width, plot_height = width - left - right, height - top - bottom
    years = list(yearly)
    model_keys = (
        ("seasonal_naive", "#c56c28", "Seasonal naive"),
        ("calendar_trend", "#627178", "Calendar and trend"),
        ("calendar_trend_temperature", "#0a8275", "Calendar, trend, and temperature"),
    )
    maximum = max(yearly[year][key]["mae_gwh"] for year in years for key, _, _ in model_keys)
    axis_max = max(500.0, ((maximum // 500) + 1) * 500)

    def y(value: float) -> float:
        return top + (axis_max - value) * plot_height / axis_max

    grid: list[str] = []
    for step in range(6):
        value = axis_max * step / 5
        y_position = y(value)
        grid.append(
            f'<line x1="{left}" y1="{y_position:.1f}" x2="{width-right}" y2="{y_position:.1f}" stroke="#d8ddd9"/>'
        )
        grid.append(
            f'<text x="{left-12}" y="{y_position+5:.1f}" text-anchor="end" font-size="13" fill="#526064">{value:,.0f}</text>'
        )

    group_width = plot_width / len(years)
    bar_width = min(22.0, group_width / 4)
    bars: list[str] = []
    labels: list[str] = []
    for index, year in enumerate(years):
        center = left + group_width * (index + 0.5)
        for offset, (key, color, _) in enumerate(model_keys, start=-1):
            value = yearly[year][key]["mae_gwh"]
            x_position = center + offset * bar_width - bar_width / 2
            y_position = y(value)
            bars.append(
                f'<rect x="{x_position:.1f}" y="{y_position:.1f}" width="{bar_width-2:.1f}" height="{top+plot_height-y_position:.1f}" fill="{color}"/>'
            )
        suffix = "*" if year == "2026" else ""
        labels.append(
            f'<text x="{center:.1f}" y="{height-43}" text-anchor="middle" font-size="13" fill="#526064">{year}{suffix}</text>'
        )

    legend: list[str] = []
    legend_x = 580
    for index, (_, color, label) in enumerate(model_keys):
        x_position = legend_x + index * 195
        legend.append(
            f'<rect x="{x_position}" y="20" width="16" height="12" fill="{color}"/><text x="{x_position+23}" y="31" font-size="12" fill="#243438">{label}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Rolling-origin mean absolute error by year</title>
<desc id="desc">Annual mean absolute error in gigawatt-hours for three electricity demand models from 2016 through August 2026.</desc>
<rect width="100%" height="100%" fill="#fffdf8"/>
<text x="{left}" y="31" font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="#16272b">Rolling-origin MAE by year</text>
<g font-family="Arial, sans-serif">{''.join(grid)}{''.join(bars)}{''.join(labels)}{''.join(legend)}</g>
<text x="{left}" y="{height-12}" font-family="Arial, sans-serif" font-size="13" fill="#526064">GWh · expanding monthly origin · *2026 through August</text>
</svg>'''
    path.write_text(svg, encoding="utf-8")


def run_backtest(input_path: Path, output_dir: Path) -> dict[str, object]:
    rows = load_observations(input_path)
    validate_monthly_sequence(rows)
    records = rolling_predictions(rows)
    if len(records) != 128:
        raise ValueError(f"Expected 128 rolling forecasts, found {len(records)}")

    model_columns = {
        "seasonal_naive": "seasonal_naive_gwh",
        "calendar_trend": "calendar_model_gwh",
        "calendar_trend_temperature": "temperature_model_gwh",
    }
    overall = {name: error_metrics(records, column) for name, column in model_columns.items()}
    yearly: dict[str, dict[str, dict[str, float]]] = {}
    for year in range(2016, 2027):
        subset = [record for record in records if str(record["period"]).startswith(str(year))]
        yearly[str(year)] = {
            name: error_metrics(subset, column) for name, column in model_columns.items()
        }
    by_season: dict[str, dict[str, dict[str, float]]] = {}
    for label in ("warm", "cold", "shoulder"):
        subset = [record for record in records if record["season"] == label]
        by_season[label] = {
            name: error_metrics(subset, column) for name, column in model_columns.items()
        }

    complete_year_temperature_wins = sum(
        yearly[str(year)]["calendar_trend_temperature"]["mae_gwh"]
        < yearly[str(year)]["seasonal_naive"]["mae_gwh"]
        for year in COMPLETE_YEARS
    )
    interval = year_block_interval(records)
    temperature_better_overall = (
        overall["calendar_trend_temperature"]["mae_gwh"]
        < overall["seasonal_naive"]["mae_gwh"]
    )
    majority_years = complete_year_temperature_wins >= 6
    interval_above_zero = interval[0] > 0
    usefulness_passed = temperature_better_overall and majority_years and interval_above_zero
    improvement_vs_calendar = 100 * (
        overall["calendar_trend"]["mae_gwh"]
        - overall["calendar_trend_temperature"]["mae_gwh"]
    ) / overall["calendar_trend"]["mae_gwh"]
    change_vs_naive = 100 * (
        overall["calendar_trend_temperature"]["mae_gwh"]
        - overall["seasonal_naive"]["mae_gwh"]
    ) / overall["seasonal_naive"]["mae_gwh"]
    change_vs_naive_by_season = {
        label: round(
            100
            * (
                by_season[label]["calendar_trend_temperature"]["mae_gwh"]
                - by_season[label]["seasonal_naive"]["mae_gwh"]
            )
            / by_season[label]["seasonal_naive"]["mae_gwh"],
            3,
        )
        for label in ("warm", "cold", "shoulder")
    }

    metrics: dict[str, object] = {
        "design": {
            "first_forecast": records[0]["period"],
            "last_forecast": records[-1]["period"],
            "forecasts": len(records),
            "origin": "expanding window refitted monthly",
            "observed_temperature_oracle": True,
        },
        "overall": overall,
        "by_year": yearly,
        "by_season": by_season,
        "comparisons": {
            "temperature_mae_improvement_vs_calendar_percent": round(improvement_vs_calendar, 3),
            "temperature_mae_change_vs_seasonal_naive_percent": round(change_vs_naive, 3),
            "temperature_mae_change_vs_seasonal_naive_by_season_percent": change_vs_naive_by_season,
            "calendar_month_win_rate_vs_seasonal_naive_percent": round(
                100
                * mean(
                    float(record["calendar_model_abs_error_gwh"])
                    < float(record["seasonal_naive_abs_error_gwh"])
                    for record in records
                ),
                3,
            ),
            "temperature_month_win_rate_vs_seasonal_naive_percent": round(
                100
                * mean(
                    float(record["temperature_model_abs_error_gwh"])
                    < float(record["seasonal_naive_abs_error_gwh"])
                    for record in records
                ),
                3,
            ),
            "seasonal_naive_minus_temperature_mae_year_block_95_interval_gwh": list(interval),
        },
        "usefulness_gate": {
            "temperature_better_overall_than_seasonal_naive": temperature_better_overall,
            "complete_years_won": complete_year_temperature_wins,
            "complete_years_required": 6,
            "majority_of_complete_years_won": majority_years,
            "uncertainty_interval_entirely_above_zero": interval_above_zero,
            "passed": usefulness_passed,
        },
        "boundaries": [
            "This exploratory extension was planned after the original fixed-holdout result.",
            "Observed current-month temperature makes the temperature model an oracle benchmark, not an ex-ante forecast.",
            "The 2026 annual result contains January through August only and is excluded from the complete-year gate.",
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "rolling_predictions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    (output_dir / "rolling_metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_year_chart(yearly, output_dir / "rolling_mae_by_year.svg")

    gate_text = "passed" if usefulness_passed else "did not pass"
    report = f"""# Rolling-origin backtest results

## Result

The predefined usefulness gate **{gate_text}**. Across 128 monthly forecasts, the temperature model's MAE was **{change_vs_naive:.1f}% higher** than seasonal naive and **{improvement_vs_calendar:.1f}% lower** than calendar and trend.

The temperature model beat seasonal naive in **{complete_year_temperature_wins} of 10** complete calendar years. The year-block 95% interval for seasonal-naive MAE minus temperature-model MAE was **{interval[0]:.1f} to {interval[1]:.1f} GWh**.

The aggregate result hides a seasonal split. Relative to seasonal naive, the temperature model's MAE changed by **{change_vs_naive_by_season['warm']:.1f}% in warm months**, **{change_vs_naive_by_season['cold']:.1f}% in cold months**, and **{change_vs_naive_by_season['shoulder']:.1f}% in shoulder months**. Negative values indicate lower error. The large shoulder-month deterioration is the clearest next diagnostic target.

## Overall metrics

| Model | MAE GWh | RMSE GWh | MAPE | Mean error GWh |
| --- | ---: | ---: | ---: | ---: |
| Seasonal naive | {overall['seasonal_naive']['mae_gwh']:.1f} | {overall['seasonal_naive']['rmse_gwh']:.1f} | {overall['seasonal_naive']['mape_percent']:.2f}% | {overall['seasonal_naive']['mean_error_gwh']:.1f} |
| Calendar and trend | {overall['calendar_trend']['mae_gwh']:.1f} | {overall['calendar_trend']['rmse_gwh']:.1f} | {overall['calendar_trend']['mape_percent']:.2f}% | {overall['calendar_trend']['mean_error_gwh']:.1f} |
| Calendar, trend, and temperature | {overall['calendar_trend_temperature']['mae_gwh']:.1f} | {overall['calendar_trend_temperature']['rmse_gwh']:.1f} | {overall['calendar_trend_temperature']['mape_percent']:.2f}% | {overall['calendar_trend_temperature']['mean_error_gwh']:.1f} |

## Interpretation

The rolling-origin design is more demanding than one fixed split because every month is evaluated using only earlier demand observations. The temperature model still receives observed current-month temperature, so even a favorable result would not establish deployable forecast performance. The original 2022 holdout result remains unchanged and should be read separately.
"""
    (output_dir / "rolling_report.md").write_text(report, encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    metrics = run_backtest(args.input, args.output)
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
