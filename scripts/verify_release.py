#!/usr/bin/env python3
"""Run the project's reproducibility and release checks."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HASH = "13e2b0d693b3a04e5efe74afcf3bf328bd68a6b7f93f78fde2f1a021dec68106"
EXPECTED_SECTOR_HASH = "31d390ba985e387f964c213c854979ac39e1d382ee40d7b8b45fbfb7aa90f04b"


def run(command: list[str], suppress_stdout: bool = False) -> None:
    subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL if suppress_stdout else None,
    )


def main() -> None:
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    with tempfile.TemporaryDirectory() as temporary:
        run([sys.executable, "src/analyze.py", "--output", temporary], suppress_stdout=True)
        metrics = json.loads((Path(temporary) / "metrics.json").read_text(encoding="utf-8"))
        if metrics["data"]["source_sha256"] != EXPECTED_HASH:
            raise SystemExit("Source hash changed")
        if metrics["data"]["observations"] != 308 or metrics["data"]["holdout_observations"] != 56:
            raise SystemExit("Unexpected data coverage")
        if metrics["hypothesis"]["mae_improvement_percent"] != 8.097:
            raise SystemExit("Unexpected hypothesis result")
        if metrics["hypothesis"]["uncertainty_interval_excludes_zero"]:
            raise SystemExit("Unexpected uncertainty interpretation")
        run([sys.executable, "src/rolling_backtest.py", "--output", temporary], suppress_stdout=True)
        rolling = json.loads((Path(temporary) / "rolling_metrics.json").read_text(encoding="utf-8"))
        if rolling["design"]["forecasts"] != 128:
            raise SystemExit("Unexpected rolling-origin coverage")
        if rolling["usefulness_gate"]["passed"]:
            raise SystemExit("Unexpected rolling-origin usefulness result")
        if rolling["comparisons"]["temperature_mae_change_vs_seasonal_naive_percent"] != 33.386:
            raise SystemExit("Unexpected rolling-origin benchmark result")
        run([sys.executable, "src/shoulder_diagnostic.py", "--output", temporary], suppress_stdout=True)
        diagnostic = json.loads(
            (Path(temporary) / "shoulder_diagnostic_metrics.json").read_text(encoding="utf-8")
        )
        if diagnostic["interpretation_inputs"]["shoulder_expanding_mean_error_gwh"] != 1029.417:
            raise SystemExit("Unexpected shoulder-season bias")
        if diagnostic["interpretation_inputs"]["shoulder_recent_60m_mae_gwh"] != 362.154:
            raise SystemExit("Unexpected recent-window diagnostic result")
        run(
            [sys.executable, "src/retrospective_diagnostics.py", "--output", temporary],
            suppress_stdout=True,
        )
        advanced = json.loads((Path(temporary) / "metrics.json").read_text(encoding="utf-8"))
        if advanced["shoulder_overall"]["calendar_trend"]["mean_error_gwh"] != 1050.92:
            raise SystemExit("Unexpected shoulder calendar-trend bias")
        if (
            advanced["shoulder_by_feature_state"]["dead_band"]["models"][
                "expanding_temperature"
            ]["mae_gwh"]
            != 1222.297
        ):
            raise SystemExit("Unexpected dead-band diagnostic result")
        sector_path = ROOT / "data" / "raw" / "electricity_demand_sectors_monthly.csv"
        import hashlib

        if hashlib.sha256(sector_path.read_bytes()).hexdigest() != EXPECTED_SECTOR_HASH:
            raise SystemExit("Sector source hash changed")
        run([sys.executable, "src/nested_validation.py", "--output", temporary], suppress_stdout=True)
        nested = json.loads((Path(temporary) / "metrics.json").read_text(encoding="utf-8"))
        if nested["overall"]["adaptive_annual_change_honest"]["mae_gwh"] != 622.376:
            raise SystemExit("Unexpected nested honest-information result")
        if nested["window_selection_frequency"]["honest"]["120"] != 108:
            raise SystemExit("Unexpected nested window-selection trajectory")
        if nested["design"]["latest_demand_lag_months"] != 2:
            raise SystemExit("Nested validation did not preserve the availability lag")
        forecast_manifest = json.loads(
            (ROOT / "prospective" / "vintages" / "2026-10" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        if forecast_manifest["source_sha256"] != EXPECTED_HASH:
            raise SystemExit("Prospective input vintage hash changed")
        forecast_code = ROOT / forecast_manifest["forecast_code"]
        if hashlib.sha256(forecast_code.read_bytes()).hexdigest() != forecast_manifest[
            "forecast_code_sha256"
        ]:
            raise SystemExit("Prospective forecast code changed after issuance")
        with (ROOT / "prospective" / "forecasts.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            forecasts = list(__import__("csv").DictReader(handle))
        if len(forecasts) != 1 or forecasts[0]["target_period"] != "2026-10-01":
            raise SystemExit("Unexpected prospective forecast ledger")
        if forecasts[0]["primary_adaptive_annual_change_gwh"] != "10578.252":
            raise SystemExit("Prospective October forecast changed")
    print("Release verification passed: source, test suite, outputs, and frozen results.")


if __name__ == "__main__":
    main()
