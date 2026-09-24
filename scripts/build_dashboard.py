"""Build an offline dashboard data bundle from the project's frozen artifacts."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rows(path):
    with (ROOT / path).open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def main():
    from build_monthly_reports import build
    sources = ['data/raw/electricity_demand_monthly.csv',
               'results/nested_exploratory/predictions.csv',
               'results/nested_exploratory/metrics.json', 'prospective/forecasts.csv',
               'data/source_manifest.json']
    demand = rows(sources[0])
    predictions = rows(sources[1])
    forecasts = rows(sources[3])
    assert len({r['period'] for r in predictions}) == len(predictions)
    assert all(float(r['demanda_total']) > 0 for r in demand)
    data = dict(demand=demand, predictions=predictions, forecasts=forecasts,
                metrics=json.loads((ROOT / sources[2]).read_text()),
                source=json.loads((ROOT / sources[4]).read_text()),
                hashes={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources})
    destination = ROOT / 'dashboard' / 'data.js'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text('window.ENERGY_DATA = ' + json.dumps(data, ensure_ascii=False) + ';\n')
    print(f'Dashboard: {len(demand)} observations, {len(predictions)} backtest months, {len(forecasts)} frozen forecasts')
    build()


if __name__ == '__main__':
    main()
