#!/usr/bin/env python3
"""Fetch and validate the official monthly electricity-demand sector series."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import urllib.request
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "raw" / "electricity_demand_sectors_monthly.csv"
DEFAULT_MANIFEST = ROOT / "data" / "sector_source_manifest.json"
SERIES = {
    "total_gwh": "367.3_DEMANDA_TOTAL__13",
    "residential_gwh": "367.3_DEMANDA_REIAL__19",
    "commerce_industry_gwh": "367.3_COMERCIO_ERIA__20",
    "large_users_gwh": "367.3_GRANDES_USIOS__16",
}
API_URL = (
    "https://apis.datos.gob.ar/series/api/series/?ids="
    + ",".join(SERIES.values())
    + "&format=json&limit=5000"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch_rows() -> list[list[object]]:
    request = urllib.request.Request(API_URL, headers={"User-Agent": "energy-demand-evidence-lab/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    complete = [row for row in payload["data"] if all(value is not None for value in row[1:])]
    if not complete:
        raise ValueError("The API returned no complete sector rows")
    return complete


def validate(rows: list[list[object]]) -> None:
    periods = [date.fromisoformat(str(row[0])) for row in rows]
    if periods[0] != date(2005, 1, 1) or periods[-1] != date(2026, 8, 1):
        raise ValueError(f"Unexpected sector coverage: {periods[0]} to {periods[-1]}")
    if len(rows) != 260:
        raise ValueError(f"Expected 260 complete sector rows, found {len(rows)}")
    for previous, current in zip(periods, periods[1:]):
        expected = date(
            previous.year + (previous.month == 12),
            1 if previous.month == 12 else previous.month + 1,
            1,
        )
        if current != expected:
            raise ValueError(f"Missing month between {previous} and {current}")
    for row in rows:
        total = float(row[1])
        components = sum(float(value) for value in row[2:])
        if abs(total - components) > 0.01:
            raise ValueError(f"Sector components do not sum to total in {row[0]}")


def write_outputs(rows: list[list[object]], output: Path, manifest: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("period", *SERIES.keys()))
        for row in rows:
            writer.writerow((row[0], *(f"{float(value):.6f}" for value in row[1:])))
    metadata = {
        "downloaded_at": date.today().isoformat(),
        "api_query": API_URL,
        "source": "Datos Argentina / CAMMESA",
        "series": SERIES,
        "coverage": {"start": rows[0][0], "end": rows[-1][0], "observations": len(rows)},
        "validation": {
            "consecutive_months": True,
            "components_sum_to_total_tolerance_gwh": 0.01,
        },
        "local_file": str(output.relative_to(ROOT)),
        "sha256": sha256(output),
    }
    manifest.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    rows = fetch_rows()
    validate(rows)
    write_outputs(rows, args.output, args.manifest)
    print(f"Wrote {len(rows)} validated monthly sector observations to {args.output}")


if __name__ == "__main__":
    main()
