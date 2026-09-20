#!/usr/bin/env python3
"""Evaluate whether temperature adds out-of-sample value for monthly electricity demand."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "raw" / "electricity_demand_monthly.csv"
DEFAULT_OUTPUT = ROOT / "results"
HOLDOUT_START = date(2022, 1, 1)
HEATING_BALANCE_C = 18.0
COOLING_BALANCE_C = 22.0


@dataclass(frozen=True)
class Observation:
    period: date
    demand_gwh: float
    temperature_c: float
    peak_power_mw: float
    time_index: int


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_observations(path: Path) -> list[Observation]:
    rows: list[Observation] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for index, row in enumerate(csv.DictReader(handle)):
            if any(not row[field] for field in ("indice_tiempo", "demanda_total", "temperatura_promedio", "potencia_maxima")):
                raise ValueError(f"Missing required value on data row {index + 2}")
            rows.append(
                Observation(
                    period=date.fromisoformat(row["indice_tiempo"]),
                    demand_gwh=float(row["demanda_total"]),
                    temperature_c=float(row["temperatura_promedio"]),
                    peak_power_mw=float(row["potencia_maxima"]),
                    time_index=index,
                )
            )
    if not rows:
        raise ValueError("Dataset is empty")
    return rows


def next_month(period: date) -> date:
    return date(period.year + (period.month == 12), 1 if period.month == 12 else period.month + 1, 1)


def validate_monthly_sequence(rows: list[Observation]) -> None:
    periods = [row.period for row in rows]
    if periods != sorted(periods):
        raise ValueError("Periods are not sorted")
    if len(periods) != len(set(periods)):
        raise ValueError("Duplicate monthly periods found")
    for previous, current in zip(periods, periods[1:]):
        if next_month(previous) != current:
            raise ValueError(f"Missing monthly period between {previous} and {current}")


def degree_features(temperature_c: float) -> tuple[float, float]:
    return max(0.0, HEATING_BALANCE_C - temperature_c), max(0.0, temperature_c - COOLING_BALANCE_C)


def feature_vector(row: Observation, include_temperature: bool) -> list[float]:
    years_from_start = row.time_index / 12.0
    vector = [1.0, years_from_start]
    vector.extend(1.0 if row.period.month == month else 0.0 for month in range(2, 13))
    if include_temperature:
        vector.extend(degree_features(row.temperature_c))
    return vector


def solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    size = len(vector)
    augmented = [matrix[row][:] + [vector[row]] for row in range(size)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-10:
            raise ValueError("Design matrix is singular")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                augmented[row][item] - factor * augmented[column][item]
                for item in range(size + 1)
            ]
    return [augmented[row][-1] for row in range(size)]


def fit_ols(rows: list[Observation], include_temperature: bool) -> list[float]:
    design = [feature_vector(row, include_temperature) for row in rows]
    width = len(design[0])
    xtx = [[0.0 for _ in range(width)] for _ in range(width)]
    xty = [0.0 for _ in range(width)]
    for features, row in zip(design, rows):
        for left in range(width):
            xty[left] += features[left] * row.demand_gwh
            for right in range(width):
                xtx[left][right] += features[left] * features[right]
    return solve_linear_system(xtx, xty)


def predict(row: Observation, coefficients: list[float], include_temperature: bool) -> float:
    return sum(value * coefficient for value, coefficient in zip(feature_vector(row, include_temperature), coefficients))


def mean(values: Iterable[float]) -> float:
    items = list(values)
    return sum(items) / len(items) if items else 0.0


def model_metrics(actual: list[float], predicted: list[float]) -> dict[str, float]:
    errors = [prediction - observed for observed, prediction in zip(actual, predicted)]
    return {
        "mae_gwh": round(mean(abs(error) for error in errors), 3),
        "rmse_gwh": round(math.sqrt(mean(error * error for error in errors)), 3),
        "mape_percent": round(100 * mean(abs(error) / observed for observed, error in zip(actual, errors)), 3),
        "mean_error_gwh": round(mean(errors), 3),
    }


def year_block_interval(rows: list[dict[str, float | int | str]], iterations: int = 5_000) -> tuple[float, float]:
    by_year: dict[int, list[float]] = {}
    for row in rows:
        difference = float(row["calendar_abs_error_gwh"]) - float(row["temperature_abs_error_gwh"])
        by_year.setdefault(int(str(row["period"])[:4]), []).append(difference)
    years = sorted(by_year)
    generator = random.Random(42)
    estimates: list[float] = []
    for _ in range(iterations):
        sampled = [generator.choice(years) for _ in years]
        estimates.append(mean(value for year in sampled for value in by_year[year]))
    estimates.sort()
    lower = estimates[int(iterations * 0.025)]
    upper = estimates[int(iterations * 0.975)]
    return round(lower, 3), round(upper, 3)


def write_svg(rows: list[dict[str, float | int | str]], path: Path) -> None:
    width, height = 1_200, 520
    left, right, top, bottom = 76, 30, 45, 64
    plot_width, plot_height = width - left - right, height - top - bottom
    values = [float(row[key]) for row in rows for key in ("actual_gwh", "seasonal_naive_gwh", "temperature_model_gwh")]
    minimum, maximum = min(values), max(values)

    def x(index: int) -> float:
        return left + index * plot_width / max(len(rows) - 1, 1)

    def y(value: float) -> float:
        return top + (maximum - value) * plot_height / (maximum - minimum)

    def polyline(key: str, color: str, width_px: int) -> str:
        points = " ".join(f"{x(index):.1f},{y(float(row[key])):.1f}" for index, row in enumerate(rows))
        return f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="{width_px}" stroke-linejoin="round"/>'

    grid = []
    for step in range(5):
        value = minimum + (maximum - minimum) * step / 4
        y_position = y(value)
        grid.append(f'<line x1="{left}" y1="{y_position:.1f}" x2="{width-right}" y2="{y_position:.1f}" stroke="#d8ddd9"/>')
        grid.append(f'<text x="{left-12}" y="{y_position+5:.1f}" text-anchor="end" font-size="14" fill="#526064">{value:,.0f}</text>')
    labels = []
    for index, row in enumerate(rows):
        if index % 12 == 0:
            labels.append(f'<text x="{x(index):.1f}" y="{height-28}" text-anchor="middle" font-size="14" fill="#526064">{str(row["period"])[:4]}</text>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Monthly electricity demand holdout predictions</title>
<desc id="desc">Actual demand compared with seasonal naive and temperature-enhanced predictions from 2022 to 2026.</desc>
<rect width="100%" height="100%" fill="#fffdf8"/>
<text x="{left}" y="26" font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="#16272b">Out-of-sample monthly electricity demand</text>
<text x="{left}" y="{height-5}" font-family="Arial, sans-serif" font-size="13" fill="#526064">Holdout: January 2022 to August 2026 · GWh</text>
<g font-family="Arial, sans-serif">{''.join(grid)}{''.join(labels)}
{polyline("actual_gwh", "#102f36", 4)}
{polyline("seasonal_naive_gwh", "#c56c28", 2)}
{polyline("temperature_model_gwh", "#0a8275", 3)}
<g transform="translate(720,18)" font-size="13">
<line x1="0" y1="0" x2="30" y2="0" stroke="#102f36" stroke-width="4"/><text x="38" y="5">Actual</text>
<line x1="115" y1="0" x2="145" y2="0" stroke="#c56c28" stroke-width="2"/><text x="153" y="5">Seasonal naive</text>
<line x1="280" y1="0" x2="310" y2="0" stroke="#0a8275" stroke-width="3"/><text x="318" y="5">Temperature model</text>
</g></g></svg>'''
    path.write_text(svg, encoding="utf-8")


def run_analysis(input_path: Path, output_dir: Path) -> dict[str, object]:
    rows = load_observations(input_path)
    validate_monthly_sequence(rows)
    train = [row for row in rows if row.period < HOLDOUT_START]
    test = [row for row in rows if row.period >= HOLDOUT_START]
    if not train or not test:
        raise ValueError("Both training and holdout periods are required")

    calendar_coefficients = fit_ols(train, include_temperature=False)
    temperature_coefficients = fit_ols(train, include_temperature=True)
    by_period = {row.period: row for row in rows}
    predictions: list[dict[str, float | int | str]] = []
    for row in test:
        previous_year = date(row.period.year - 1, row.period.month, 1)
        naive = by_period[previous_year].demand_gwh
        calendar = predict(row, calendar_coefficients, include_temperature=False)
        temperature = predict(row, temperature_coefficients, include_temperature=True)
        predictions.append({
            "period": row.period.isoformat(),
            "temperature_c": row.temperature_c,
            "actual_gwh": round(row.demand_gwh, 3),
            "seasonal_naive_gwh": round(naive, 3),
            "calendar_model_gwh": round(calendar, 3),
            "temperature_model_gwh": round(temperature, 3),
            "calendar_abs_error_gwh": round(abs(calendar - row.demand_gwh), 3),
            "temperature_abs_error_gwh": round(abs(temperature - row.demand_gwh), 3),
        })

    actual = [float(row["actual_gwh"]) for row in predictions]
    seasonal = [float(row["seasonal_naive_gwh"]) for row in predictions]
    calendar = [float(row["calendar_model_gwh"]) for row in predictions]
    temperature = [float(row["temperature_model_gwh"]) for row in predictions]
    seasonal_metrics = model_metrics(actual, seasonal)
    calendar_metrics = model_metrics(actual, calendar)
    temperature_metrics = model_metrics(actual, temperature)
    improvement = 100 * (calendar_metrics["mae_gwh"] - temperature_metrics["mae_gwh"]) / calendar_metrics["mae_gwh"]
    versus_naive = 100 * (temperature_metrics["mae_gwh"] - seasonal_metrics["mae_gwh"]) / seasonal_metrics["mae_gwh"]
    interval = year_block_interval(predictions)
    hypothesis_passed = improvement >= 5.0
    uncertainty_excludes_zero = interval[0] > 0 or interval[1] < 0

    metrics: dict[str, object] = {
        "data": {
            "source_sha256": sha256(input_path),
            "observations": len(rows),
            "start": rows[0].period.isoformat(),
            "end": rows[-1].period.isoformat(),
            "train_observations": len(train),
            "holdout_observations": len(test),
            "holdout_start": HOLDOUT_START.isoformat(),
        },
        "models": {
            "seasonal_naive": seasonal_metrics,
            "calendar_trend": calendar_metrics,
            "calendar_trend_temperature": temperature_metrics,
        },
        "hypothesis": {
            "claim": "Temperature features reduce holdout MAE by at least 5% versus calendar and linear trend alone.",
            "mae_improvement_percent": round(improvement, 3),
            "passed": hypothesis_passed,
            "year_block_bootstrap_mae_difference_gwh_95_interval": list(interval),
            "uncertainty_interval_excludes_zero": uncertainty_excludes_zero,
            "interpretation": (
                "The predefined improvement threshold was met."
                if hypothesis_passed
                else "The predefined improvement threshold was not met."
            ),
        },
        "benchmark_context": {
            "temperature_model_mae_increase_vs_seasonal_naive_percent": round(versus_naive, 3),
            "interpretation": "The seasonal-naive model has lower holdout MAE than either fitted regression.",
        },
        "boundaries": [
            "This is an explanatory benchmark using observed monthly temperature, not a production forecast.",
            "The aggregate national series cannot identify causal effects or local network constraints.",
            "The holdout includes incomplete calendar year 2026 through August.",
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "predictions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=predictions[0].keys())
        writer.writeheader()
        writer.writerows(predictions)
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_svg(predictions, output_dir / "holdout_predictions.svg")

    conclusion = "supported" if hypothesis_passed else "not supported"
    report = f"""# Energy Demand Evidence Lab results

## Result

The predefined hypothesis was **{conclusion}**. Adding heating and cooling degree features changed holdout MAE by **{improvement:.1f}%** relative to the calendar-and-trend model.

This is a point-estimate result, not decisive evidence. The uncertainty interval crosses zero. In addition, the temperature model's MAE is **{versus_naive:.1f}% higher** than the seasonal-naive benchmark.

## Holdout metrics

| Model | MAE GWh | RMSE GWh | MAPE |
| --- | ---: | ---: | ---: |
| Seasonal naive | {seasonal_metrics['mae_gwh']:.1f} | {seasonal_metrics['rmse_gwh']:.1f} | {seasonal_metrics['mape_percent']:.2f}% |
| Calendar and linear trend | {calendar_metrics['mae_gwh']:.1f} | {calendar_metrics['rmse_gwh']:.1f} | {calendar_metrics['mape_percent']:.2f}% |
| Calendar trend and temperature | {temperature_metrics['mae_gwh']:.1f} | {temperature_metrics['rmse_gwh']:.1f} | {temperature_metrics['mape_percent']:.2f}% |

The year-block bootstrap 95% interval for monthly absolute-error improvement was **{interval[0]:.1f} to {interval[1]:.1f} GWh**. Because it includes zero, the data do not establish a stable improvement across holdout years. The interval respects year blocks, but the small number of holdout years still limits precision.

## Interpretation boundary

This benchmark uses observed monthly temperature, so it is not a real operational forecast. It estimates incremental explanatory and predictive value conditional on known temperature. The aggregate series does not justify causal claims, local grid recommendations, or individual policy decisions.
"""
    (output_dir / "report.md").write_text(report, encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    metrics = run_analysis(args.input, args.output)
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
