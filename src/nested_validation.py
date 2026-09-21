#!/usr/bin/env python3
"""Run retrospective nested selection of annual-change training windows."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter
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
except ImportError:  # Direct execution
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
DEFAULT_OUTPUT = ROOT / "results" / "nested_exploratory"
CANDIDATE_WINDOWS = (36, 60, 84, 120)
INNER_MONTHS = 24


def shift_month(period: date, months: int) -> date:
    absolute = period.year * 12 + period.month - 1 + months
    return date(absolute // 12, absolute % 12 + 1, 1)


def change_features(
    row: Observation, previous_year: Observation, include_oracle_temperature: bool
) -> list[float]:
    features = [1.0]
    features.extend(1.0 if row.period.month == month else 0.0 for month in range(2, 13))
    if include_oracle_temperature:
        heating, cooling = degree_features(row.temperature_c)
        lag_heating, lag_cooling = degree_features(previous_year.temperature_c)
        features.extend((heating - lag_heating, cooling - lag_cooling))
    return features


def fit_change_model(
    rows: list[Observation],
    by_period: dict[date, Observation],
    cutoff: date,
    window: int,
    include_oracle_temperature: bool,
) -> list[float]:
    eligible: list[tuple[list[float], float]] = []
    for row in rows:
        if row.period > cutoff:
            break
        lag = by_period.get(shift_month(row.period, -12))
        if lag is None:
            continue
        eligible.append(
            (
                change_features(row, lag, include_oracle_temperature),
                row.demand_gwh - lag.demand_gwh,
            )
        )
    examples = eligible[-window:]
    if len(examples) != window:
        raise ValueError(f"Need {window} change observations by {cutoff}, found {len(examples)}")
    width = len(examples[0][0])
    xtx = [[0.0 for _ in range(width)] for _ in range(width)]
    xty = [0.0 for _ in range(width)]
    for features, target in examples:
        for left in range(width):
            xty[left] += features[left] * target
            for right in range(width):
                xtx[left][right] += features[left] * features[right]
    return solve_linear_system(xtx, xty)


def forecast_change(
    target: Observation,
    rows: list[Observation],
    by_period: dict[date, Observation],
    window: int,
    include_oracle_temperature: bool,
) -> float:
    cutoff = shift_month(target.period, -2)
    lag = by_period[shift_month(target.period, -12)]
    coefficients = fit_change_model(
        rows, by_period, cutoff, window, include_oracle_temperature
    )
    predicted_change = sum(
        value * coefficient
        for value, coefficient in zip(
            change_features(target, lag, include_oracle_temperature), coefficients
        )
    )
    return lag.demand_gwh + predicted_change


def prediction_cache(
    rows: list[Observation], by_period: dict[date, Observation]
) -> dict[tuple[date, int, bool], float]:
    first = shift_month(ROLLING_START, -(INNER_MONTHS + 1))
    last = rows[-1].period
    cache: dict[tuple[date, int, bool], float] = {}
    for target in (row for row in rows if first <= row.period <= last):
        for window in CANDIDATE_WINDOWS:
            for oracle in (False, True):
                cache[(target.period, window, oracle)] = forecast_change(
                    target, rows, by_period, window, oracle
                )
    return cache


def select_window(
    target: Observation,
    by_period: dict[date, Observation],
    cache: dict[tuple[date, int, bool], float],
    oracle: bool,
) -> tuple[int, dict[int, float]]:
    inner_periods = [
        shift_month(target.period, offset)
        for offset in range(-(INNER_MONTHS + 1), -1)
    ]
    scores: dict[int, float] = {}
    for window in CANDIDATE_WINDOWS:
        scores[window] = mean(
            abs(cache[(period, window, oracle)] - by_period[period].demand_gwh)
            for period in inner_periods
        )
    selected = min(CANDIDATE_WINDOWS, key=lambda window: (scores[window], -window))
    return selected, scores


def expanding_drift_forecast(
    target: Observation, rows: list[Observation], by_period: dict[date, Observation]
) -> float:
    cutoff = shift_month(target.period, -2)
    changes = []
    for row in rows:
        if row.period > cutoff:
            break
        lag = by_period.get(shift_month(row.period, -12))
        if lag is not None:
            changes.append(row.demand_gwh - lag.demand_gwh)
    anchor = by_period[shift_month(target.period, -12)].demand_gwh
    return anchor + mean(changes)


def expanding_oracle_forecast(target: Observation, rows: list[Observation]) -> float:
    cutoff = shift_month(target.period, -2)
    train = [row for row in rows if row.period <= cutoff]
    return predict(target, fit_ols(train, include_temperature=True), True)


MODEL_COLUMNS = {
    "seasonal_naive": "seasonal_naive_gwh",
    "seasonal_naive_expanding_drift": "seasonal_naive_drift_gwh",
    "expanding_level_temperature_oracle": "expanding_oracle_gwh",
    "fixed_60m_annual_change_honest": "fixed_60m_honest_gwh",
    "adaptive_annual_change_honest": "adaptive_honest_gwh",
    "adaptive_annual_change_temperature_oracle": "adaptive_oracle_gwh",
}


def metrics_for(records: list[dict[str, object]]) -> dict[str, dict[str, float]]:
    actual = [float(record["actual_gwh"]) for record in records]
    return {
        name: model_metrics(actual, [float(record[column]) for record in records])
        for name, column in MODEL_COLUMNS.items()
    }


def year_block_interval(
    records: list[dict[str, object]], iterations: int = 5_000
) -> tuple[float, float]:
    by_year: dict[int, list[float]] = {}
    for record in records:
        improvement = abs(
            float(record["seasonal_naive_gwh"]) - float(record["actual_gwh"])
        ) - abs(float(record["adaptive_honest_gwh"]) - float(record["actual_gwh"]))
        by_year.setdefault(int(str(record["period"])[:4]), []).append(improvement)
    years = sorted(by_year)
    generator = random.Random(42)
    estimates: list[float] = []
    for _ in range(iterations):
        selected = [generator.choice(years) for _ in years]
        estimates.append(mean(value for year in selected for value in by_year[year]))
    estimates.sort()
    return (
        round(estimates[int(iterations * 0.025)], 3),
        round(estimates[int(iterations * 0.975)], 3),
    )


def nested_predictions(rows: list[Observation]) -> list[dict[str, object]]:
    by_period = {row.period: row for row in rows}
    cache = prediction_cache(rows, by_period)
    output: list[dict[str, object]] = []
    for target in (row for row in rows if row.period >= ROLLING_START):
        honest_window, honest_scores = select_window(target, by_period, cache, False)
        oracle_window, oracle_scores = select_window(target, by_period, cache, True)
        anchor = by_period[shift_month(target.period, -12)].demand_gwh
        record: dict[str, object] = {
            "period": target.period.isoformat(),
            "season": season(target.period),
            "latest_allowed_demand_period": shift_month(target.period, -2).isoformat(),
            "actual_gwh": round(target.demand_gwh, 3),
            "seasonal_naive_gwh": round(anchor, 3),
            "seasonal_naive_drift_gwh": round(
                expanding_drift_forecast(target, rows, by_period), 3
            ),
            "expanding_oracle_gwh": round(expanding_oracle_forecast(target, rows), 3),
            "fixed_60m_honest_gwh": round(cache[(target.period, 60, False)], 3),
            "adaptive_honest_window": honest_window,
            "adaptive_honest_gwh": round(
                cache[(target.period, honest_window, False)], 3
            ),
            "adaptive_oracle_window": oracle_window,
            "adaptive_oracle_gwh": round(
                cache[(target.period, oracle_window, True)], 3
            ),
        }
        for window in CANDIDATE_WINDOWS:
            record[f"honest_inner_mae_w{window}_gwh"] = round(honest_scores[window], 3)
            record[f"oracle_inner_mae_w{window}_gwh"] = round(oracle_scores[window], 3)
        output.append(record)
    return output


def run_nested(input_path: Path, output_dir: Path) -> dict[str, object]:
    rows = load_observations(input_path)
    validate_monthly_sequence(rows)
    records = nested_predictions(rows)
    shoulder = [record for record in records if record["season"] == "shoulder"]
    overall = metrics_for(records)
    shoulder_metrics = metrics_for(shoulder)
    honest_windows = Counter(int(record["adaptive_honest_window"]) for record in records)
    oracle_windows = Counter(int(record["adaptive_oracle_window"]) for record in records)
    interval = year_block_interval(records)
    metrics: dict[str, object] = {
        "status": "RETROSPECTIVE-EXPLORATORY; NOT CONFIRMATORY",
        "design": {
            "first_outer_forecast": records[0]["period"],
            "last_outer_forecast": records[-1]["period"],
            "outer_forecasts": len(records),
            "inner_months": INNER_MONTHS,
            "candidate_windows": list(CANDIDATE_WINDOWS),
            "latest_demand_lag_months": 2,
            "tie_break": "larger window",
        },
        "overall": overall,
        "shoulder": shoulder_metrics,
        "window_selection_frequency": {
            "honest": {str(window): honest_windows[window] for window in CANDIDATE_WINDOWS},
            "temperature_oracle": {
                str(window): oracle_windows[window] for window in CANDIDATE_WINDOWS
            },
        },
        "seasonal_naive_minus_adaptive_honest_mae_year_block_95_interval_gwh": list(
            interval
        ),
        "boundaries": [
            "All outer outcomes were previously examined; nested selection is not confirmation.",
            "The primary adaptive model uses no current-month weather information.",
            "The temperature variant uses realized target-month temperature and is an oracle upper bound.",
            "Historical national-holiday adjustment is deferred until authoritative dated calendars are frozen.",
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "predictions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    honest = overall["adaptive_annual_change_honest"]
    oracle = overall["adaptive_annual_change_temperature_oracle"]
    naive = overall["seasonal_naive"]
    honest_shoulder = shoulder_metrics["adaptive_annual_change_honest"]
    naive_shoulder = shoulder_metrics["seasonal_naive"]
    report = f"""# Nested window-selection results

**Status: RETROSPECTIVE-EXPLORATORY; NOT CONFIRMATORY.**

## Primary honest-information result

The adaptive annual-change model achieved overall MAE of **{honest['mae_gwh']:.1f} GWh**, compared with **{naive['mae_gwh']:.1f} GWh** for seasonal naive. Shoulder MAE was **{honest_shoulder['mae_gwh']:.1f} GWh**, compared with **{naive_shoulder['mae_gwh']:.1f} GWh**.

The year-block interval for seasonal-naive absolute error minus adaptive-model absolute error is **{interval[0]:.1f} to {interval[1]:.1f} GWh**. This interval is descriptive because the outer period was already examined.

## Perfect-foresight comparison

The adaptive temperature-oracle variant achieved overall MAE of **{oracle['mae_gwh']:.1f} GWh**. Its difference from the honest model measures the advantage of knowing realized target-month temperature, not deployable weather skill.

## Window selections

The honest rule selected 36 months **{honest_windows[36]}** times, 60 months **{honest_windows[60]}** times, 84 months **{honest_windows[84]}** times, and 120 months **{honest_windows[120]}** times. Frequent switching is retained as evidence about instability rather than hidden through a single retrospective window.

## Availability boundary

Every outer forecast uses demand only through `t-2`. Every inner pseudo-forecast applies the same rule. Calendar-holiday features remain excluded until their historical vintages are independently frozen.
"""
    (output_dir / "report.md").write_text(report, encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run_nested(args.input, args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
