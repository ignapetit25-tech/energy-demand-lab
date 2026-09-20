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
    print("Release verification passed: source, 8 tests, outputs, and frozen results.")


if __name__ == "__main__":
    main()
