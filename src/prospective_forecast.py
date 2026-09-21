#!/usr/bin/env python3
"""Issue an immutable prospective monthly electricity-demand forecast."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import date
from pathlib import Path

try:
    from .analyze import DEFAULT_INPUT, Observation, load_observations, validate_monthly_sequence
    from .nested_validation import (
        CANDIDATE_WINDOWS,
        expanding_drift_forecast,
        forecast_change,
        prediction_cache,
        select_window,
        shift_month,
    )
except ImportError:  # Direct execution
    from analyze import DEFAULT_INPUT, Observation, load_observations, validate_monthly_sequence
    from nested_validation import (
        CANDIDATE_WINDOWS,
        expanding_drift_forecast,
        forecast_change,
        prediction_cache,
        select_window,
        shift_month,
    )


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROSPECTIVE = ROOT / "prospective"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def future_observation(target: date, rows: list[Observation]) -> Observation:
    start = rows[0].period
    time_index = (target.year - start.year) * 12 + target.month - start.month
    return Observation(
        period=target,
        demand_gwh=0.0,
        temperature_c=0.0,
        peak_power_mw=0.0,
        time_index=time_index,
    )


def build_forecast(
    rows: list[Observation], target: date, issue_timestamp: str
) -> dict[str, object]:
    latest_allowed = shift_month(target, -2)
    if rows[-1].period != latest_allowed:
        raise ValueError(
            f"Target {target} requires a frozen input ending {latest_allowed}; "
            f"input ends {rows[-1].period}"
        )
    by_period = {row.period: row for row in rows}
    future = future_observation(target, rows)
    cache = prediction_cache(rows, by_period)
    selected, scores = select_window(future, by_period, cache, oracle=False)
    anchor = by_period[shift_month(target, -12)].demand_gwh
    challenger = forecast_change(future, rows, by_period, selected, False)
    fixed_60 = forecast_change(future, rows, by_period, 60, False)
    drift = expanding_drift_forecast(future, rows, by_period)
    return {
        "target_period": target.isoformat(),
        "issue_timestamp": issue_timestamp,
        "latest_allowed_demand_period": latest_allowed.isoformat(),
        "seasonal_naive_gwh": round(anchor, 3),
        "primary_adaptive_annual_change_gwh": round(challenger, 3),
        "selected_window_months": selected,
        "fixed_60m_annual_change_gwh": round(fixed_60, 3),
        "seasonal_naive_expanding_drift_gwh": round(drift, 3),
        **{
            f"inner_mae_w{window}_gwh": round(scores[window], 3)
            for window in CANDIDATE_WINDOWS
        },
    }


def write_forecast(
    input_path: Path,
    prospective_dir: Path,
    target: date,
    issue_timestamp: str,
) -> dict[str, object]:
    rows = load_observations(input_path)
    validate_monthly_sequence(rows)
    forecast = build_forecast(rows, target, issue_timestamp)
    target_label = target.strftime("%Y-%m")
    vintage_dir = prospective_dir / "vintages" / target_label
    vintage_dir.mkdir(parents=True, exist_ok=True)
    vintage_file = vintage_dir / input_path.name
    if vintage_file.exists() and sha256(vintage_file) != sha256(input_path):
        raise ValueError("Refusing to overwrite an existing input vintage with different data")
    if not vintage_file.exists():
        shutil.copyfile(input_path, vintage_file)

    code_path = Path(__file__).resolve()
    manifest = {
        "target_period": target.isoformat(),
        "issue_timestamp": issue_timestamp,
        "source_file": str(input_path.relative_to(ROOT)),
        "source_sha256": sha256(input_path),
        "latest_source_period": rows[-1].period.isoformat(),
        "vintage_file": str(vintage_file.relative_to(ROOT)),
        "forecast_code": str(code_path.relative_to(ROOT)),
        "forecast_code_sha256": sha256(code_path),
        "weather_deviation_input": 0.0,
        "weather_interpretation": "No current-month weather input; climatology implies zero deviation.",
    }
    manifest_path = vintage_dir / "manifest.json"
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing != manifest:
            raise ValueError("Refusing to rewrite an existing prospective manifest")
    else:
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    forecasts_path = prospective_dir / "forecasts.csv"
    if forecasts_path.exists():
        with forecasts_path.open(newline="", encoding="utf-8") as handle:
            existing_rows = list(csv.DictReader(handle))
        if any(row["target_period"] == target.isoformat() for row in existing_rows):
            raise ValueError(f"Forecast for {target} already exists and is immutable")
        fieldnames = list(existing_rows[0].keys())
        if fieldnames != list(forecast.keys()):
            raise ValueError("Forecast schema changed; preregister a migration before appending")
        mode = "a"
    else:
        fieldnames = list(forecast.keys())
        mode = "w"
    with forecasts_path.open(mode, newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if mode == "w":
            writer.writeheader()
        writer.writerow(forecast)

    note_path = vintage_dir / "forecast.md"
    note_path.write_text(
        f"""# Prospective forecast for {target_label}

Issued: `{issue_timestamp}`

| Model | Forecast GWh |
| --- | ---: |
| Seasonal naive benchmark | {forecast['seasonal_naive_gwh']:.3f} |
| Primary adaptive annual change | {forecast['primary_adaptive_annual_change_gwh']:.3f} |
| Fixed 60-month annual change | {forecast['fixed_60m_annual_change_gwh']:.3f} |
| Seasonal naive plus expanding drift | {forecast['seasonal_naive_expanding_drift_gwh']:.3f} |

The primary rule selected a **{forecast['selected_window_months']}-month** window using only inner outcomes available through {forecast['latest_allowed_demand_period']}. No target-month weather information was used. This forecast is immutable and will be evaluated after the official outcome is released.
""",
        encoding="utf-8",
    )
    return forecast


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--prospective-dir", type=Path, default=DEFAULT_PROSPECTIVE)
    parser.add_argument("--target", type=date.fromisoformat, required=True)
    parser.add_argument("--issue-timestamp", required=True)
    args = parser.parse_args()
    forecast = write_forecast(
        args.input, args.prospective_dir, args.target, args.issue_timestamp
    )
    print(json.dumps(forecast, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
