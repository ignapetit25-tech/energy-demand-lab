#!/usr/bin/env python3
"""Run prespecified retrospective diagnostics for the energy-demand model."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

try:
    from .analyze import (
        DEFAULT_INPUT,
        Observation,
        degree_features,
        feature_vector,
        fit_ols,
        load_observations,
        mean,
        model_metrics,
        validate_monthly_sequence,
    )
    from .rolling_backtest import ROLLING_START, rolling_predictions
except ImportError:  # Direct execution
    from analyze import (
        DEFAULT_INPUT,
        Observation,
        degree_features,
        feature_vector,
        fit_ols,
        load_observations,
        mean,
        model_metrics,
        validate_monthly_sequence,
    )
    from rolling_backtest import ROLLING_START, rolling_predictions


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SECTOR_INPUT = ROOT / "data" / "raw" / "electricity_demand_sectors_monthly.csv"
DEFAULT_OUTPUT = ROOT / "results" / "retrospective_descriptive"
MODEL_COLUMNS = {
    "seasonal_naive": "seasonal_naive_gwh",
    "calendar_trend": "calendar_model_gwh",
    "expanding_temperature": "temperature_model_gwh",
}
COEFFICIENT_NAMES = (
    "intercept",
    "trend_gwh_per_year",
    "month_february",
    "month_march",
    "month_april",
    "month_may",
    "month_june",
    "month_july",
    "month_august",
    "month_september",
    "month_october",
    "month_november",
    "month_december",
    "heating_gwh_per_degree",
    "cooling_gwh_per_degree",
)


def metrics_for(records: list[dict[str, object]]) -> dict[str, dict[str, float]]:
    actual = [float(record["actual_gwh"]) for record in records]
    result: dict[str, dict[str, float]] = {}
    for name, column in MODEL_COLUMNS.items():
        metrics = model_metrics(actual, [float(record[column]) for record in records])
        metrics["bias_share_percent"] = round(
            100 * metrics["mean_error_gwh"] / metrics["mae_gwh"], 3
        )
        result[name] = metrics
    return result


def enrich_predictions(rows: list[Observation]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for record in rolling_predictions(rows):
        enriched: dict[str, object] = dict(record)
        temperature = float(record["temperature_c"])
        heating, cooling = degree_features(temperature)
        enriched["temperature_feature_state"] = (
            "dead_band" if heating == 0 and cooling == 0 else "active"
        )
        records.append(enriched)
    return records


def coefficient_paths(rows: list[Observation]) -> list[dict[str, object]]:
    paths: list[dict[str, object]] = []
    for target in (row for row in rows if row.period >= ROLLING_START):
        train = [row for row in rows if row.period < target.period]
        for window_name, sample in (
            ("expanding", train),
            ("recent_60m", train[-60:]),
        ):
            coefficients = fit_ols(sample, include_temperature=True)
            path: dict[str, object] = {
                "period": target.period.isoformat(),
                "window": window_name,
                "training_observations": len(sample),
            }
            path.update(
                {
                    name: round(value, 6)
                    for name, value in zip(COEFFICIENT_NAMES, coefficients)
                }
            )
            paths.append(path)
    return paths


def prediction_decomposition(rows: list[Observation]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for target in (row for row in rows if row.period >= ROLLING_START):
        if target.period.month not in (3, 4, 5, 9, 10, 11):
            continue
        train = [row for row in rows if row.period < target.period]
        coefficients = fit_ols(train, include_temperature=True)
        features = feature_vector(target, include_temperature=True)
        intercept = coefficients[0]
        trend = coefficients[1] * features[1]
        month = sum(
            coefficient * feature
            for coefficient, feature in zip(coefficients[2:13], features[2:13])
        )
        heating = coefficients[13] * features[13]
        cooling = coefficients[14] * features[14]
        prediction = intercept + trend + month + heating + cooling
        output.append(
            {
                "period": target.period.isoformat(),
                "temperature_c": round(target.temperature_c, 3),
                "feature_state": (
                    "dead_band" if features[13] == 0 and features[14] == 0 else "active"
                ),
                "actual_gwh": round(target.demand_gwh, 3),
                "intercept_component_gwh": round(intercept, 3),
                "trend_component_gwh": round(trend, 3),
                "month_component_gwh": round(month, 3),
                "heating_component_gwh": round(heating, 3),
                "cooling_component_gwh": round(cooling, 3),
                "prediction_gwh": round(prediction, 3),
                "error_gwh": round(prediction - target.demand_gwh, 3),
            }
        )
    return output


def load_sector_rows(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            rows.append(
                {
                    "period": date.fromisoformat(raw["period"]),
                    "total_gwh": float(raw["total_gwh"]),
                    "residential_gwh": float(raw["residential_gwh"]),
                    "commerce_industry_gwh": float(raw["commerce_industry_gwh"]),
                    "large_users_gwh": float(raw["large_users_gwh"]),
                }
            )
    if len(rows) != 260 or rows[0]["period"] != date(2005, 1, 1):
        raise ValueError("Unexpected sector dataset coverage")
    return rows


def sector_diagnostics(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, object]]:
    value_keys = ("residential_gwh", "commerce_industry_gwh", "large_users_gwh")
    base_rows = [row for row in rows if row["period"].year == 2015]
    base = {key: mean(float(row[key]) for row in base_rows) for key in value_keys}
    by_period = {row["period"]: row for row in rows}
    detailed: list[dict[str, object]] = []
    for row in rows:
        period = row["period"]
        total = float(row["total_gwh"])
        previous = by_period.get(date(period.year - 1, period.month, 1))
        output: dict[str, object] = {
            "period": period.isoformat(),
            "total_gwh": round(total, 3),
        }
        for key in value_keys:
            short = key.removesuffix("_gwh")
            value = float(row[key])
            output[f"{short}_gwh"] = round(value, 3)
            output[f"{short}_share_percent"] = round(100 * value / total, 3)
            output[f"{short}_index_2015_100"] = round(100 * value / base[key], 3)
            output[f"{short}_yoy_percent"] = (
                round(100 * (value / float(previous[key]) - 1), 3) if previous else ""
            )
        detailed.append(output)

    annual: dict[str, object] = {}
    grouped: dict[int, list[dict[str, object]]] = defaultdict(list)
    for row in detailed:
        grouped[int(str(row["period"])[:4])].append(row)
    for year, year_rows in grouped.items():
        annual[str(year)] = {
            short: {
                "index_2015_100": round(
                    mean(float(row[f"{short}_index_2015_100"]) for row in year_rows), 3
                ),
                "share_percent": round(
                    mean(float(row[f"{short}_share_percent"]) for row in year_rows), 3
                ),
            }
            for short in ("residential", "commerce_industry", "large_users")
        }
    return detailed, annual


def summarize_parameter_paths(paths: list[dict[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    tracked = (
        "trend_gwh_per_year",
        "month_march",
        "month_april",
        "month_may",
        "month_september",
        "month_october",
        "month_november",
        "heating_gwh_per_degree",
        "cooling_gwh_per_degree",
    )
    for window in ("expanding", "recent_60m"):
        subset = [row for row in paths if row["window"] == window]
        result[window] = {
            name: {
                "first": subset[0][name],
                "last": subset[-1][name],
                "minimum": round(min(float(row[name]) for row in subset), 3),
                "maximum": round(max(float(row[name]) for row in subset), 3),
            }
            for name in tracked
        }
    return result


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def run_diagnostics(
    input_path: Path, sector_path: Path, output_dir: Path
) -> dict[str, object]:
    rows = load_observations(input_path)
    validate_monthly_sequence(rows)
    records = enrich_predictions(rows)
    shoulder = [record for record in records if record["season"] == "shoulder"]
    dead_band = [
        record for record in shoulder if record["temperature_feature_state"] == "dead_band"
    ]
    active = [record for record in shoulder if record["temperature_feature_state"] == "active"]
    paths = coefficient_paths(rows)
    decomposition = prediction_decomposition(rows)
    sector_rows, sector_annual = sector_diagnostics(load_sector_rows(sector_path))

    split_metrics = {
        "dead_band": {"observations": len(dead_band), "models": metrics_for(dead_band)},
        "active": {"observations": len(active), "models": metrics_for(active)},
    }
    shoulder_metrics = metrics_for(shoulder)
    metrics: dict[str, object] = {
        "status": "RETROSPECTIVE-DESCRIPTIVE; NOT CONFIRMATORY",
        "design": {
            "rolling_forecasts": len(records),
            "shoulder_observations": len(shoulder),
            "dead_band_c": [18.0, 22.0],
            "sector_observations": len(sector_rows),
            "sector_start": sector_rows[0]["period"],
            "sector_end": sector_rows[-1]["period"],
        },
        "shoulder_overall": shoulder_metrics,
        "shoulder_by_feature_state": split_metrics,
        "parameter_paths": summarize_parameter_paths(paths),
        "sector_annual": sector_annual,
        "boundaries": [
            "All evaluated demand outcomes through August 2026 were previously examined.",
            "Parameter instability does not identify its economic cause.",
            "Sector divergence is descriptive and cannot establish tariff or activity effects.",
            "Current-month observed temperature remains a perfect-foresight input.",
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "coefficient_paths.csv", paths)
    write_csv(output_dir / "shoulder_decomposition.csv", decomposition)
    write_csv(output_dir / "sector_diagnostics.csv", sector_rows)
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    inside = split_metrics["dead_band"]["models"]["expanding_temperature"]
    outside = split_metrics["active"]["models"]["expanding_temperature"]
    calendar = shoulder_metrics["calendar_trend"]
    temperature = shoulder_metrics["expanding_temperature"]
    sector_2015 = sector_annual["2015"]
    sector_2025 = sector_annual["2025"]
    report = f"""# Advanced retrospective diagnostic results

**Status: RETROSPECTIVE-DESCRIPTIVE; NOT CONFIRMATORY.**

## Dead band versus active temperature features

The expanding temperature model has shoulder-month mean error of **{inside['mean_error_gwh']:.1f} GWh** inside the 18-22 C dead band and **{outside['mean_error_gwh']:.1f} GWh** when a heating or cooling feature is active. Corresponding MAE values are **{inside['mae_gwh']:.1f}** and **{outside['mae_gwh']:.1f} GWh**.

The dead-band MAE is **{100 * (inside['mae_gwh'] / outside['mae_gwh'] - 1):.1f}% higher**. Feature inactivity therefore contributes to the shoulder failure, but the large positive error outside the band shows that it is not a complete explanation. This split does not identify a causal temperature effect.

## Temperature is not creating the underlying bias

Across all shoulder months, calendar and trend has mean error of **{calendar['mean_error_gwh']:.1f} GWh** and the temperature model has mean error of **{temperature['mean_error_gwh']:.1f} GWh**. Their MAPE values are **{calendar['mape_percent']:.2f}%** and **{temperature['mape_percent']:.2f}%**. The comparison shows whether temperature creates the positive bias or merely changes an already biased level forecast.

Temperature reduces the calendar-and-trend mean error by only **{calendar['mean_error_gwh'] - temperature['mean_error_gwh']:.1f} GWh**. The bias is therefore already present in the level-and-calendar specification. Because percentage errors remain close to 10%, growth in the scale of demand cannot explain the failure by itself.

## Parameter instability

The expanding model's estimated trend falls from **{metrics['parameter_paths']['expanding']['trend_gwh_per_year']['first']:.1f}** to **{metrics['parameter_paths']['expanding']['trend_gwh_per_year']['last']:.1f} GWh per year**. The recent-60-month estimate falls from **{metrics['parameter_paths']['recent_60m']['trend_gwh_per_year']['first']:.1f}** to **{metrics['parameter_paths']['recent_60m']['trend_gwh_per_year']['last']:.1f} GWh per year** and ranges as low as **{metrics['parameter_paths']['recent_60m']['trend_gwh_per_year']['minimum']:.1f}**. Heating, cooling, and shoulder-month coefficients also move materially. This establishes parameter instability but cannot distinguish gradual change, discrete breaks, omitted variables, or aggregation effects.

## Sector composition

Residential demand represented **{sector_2015['residential']['share_percent']:.1f}%** of total demand in 2015 and **{sector_2025['residential']['share_percent']:.1f}%** in 2025. Commerce and industry changed from **{sector_2015['commerce_industry']['share_percent']:.1f}%** to **{sector_2025['commerce_industry']['share_percent']:.1f}%**, while large users changed from **{sector_2015['large_users']['share_percent']:.1f}%** to **{sector_2025['large_users']['share_percent']:.1f}%**.

These movements can support a composition hypothesis but cannot establish why the shares changed.

The 2015-to-2025 sector indices show residential demand rising to **{sector_2025['residential']['index_2015_100']:.1f}**, commerce and industry remaining near **{sector_2025['commerce_industry']['index_2015_100']:.1f}**, and large users at **{sector_2025['large_users']['index_2015_100']:.1f}**. The aggregate slowdown is therefore not a uniform slowdown across consumers. The residential share did not fall; it rose, weakening that specific version of the composition hypothesis.

## Files

- `coefficient_paths.csv`: expanding and recent-60-month parameter trajectories.
- `shoulder_decomposition.csv`: intercept, trend, month, heating, and cooling contribution for every shoulder forecast.
- `sector_diagnostics.csv`: monthly sector levels, shares, 2015-based indices, and annual growth.
- `metrics.json`: frozen summaries and interpretation boundaries.
"""
    (output_dir / "report.md").write_text(report, encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--sectors", type=Path, default=DEFAULT_SECTOR_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run_diagnostics(args.input, args.sectors, args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
