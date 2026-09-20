# Energy Demand Evidence Lab

A reproducible time-series investigation of whether monthly temperature adds predictive information for Argentina's electricity demand beyond trend and calendar seasonality.

## Why this project exists

Energy demand is influenced by weather, long-term growth, seasonality, technology, prices, and behavior. A simple correlation between temperature and demand can be misleading because both change across seasons and time. This project starts with a falsifiable question and a future holdout rather than a dashboard or an in-sample fit.

## Predefined hypothesis

Heating and cooling degree features must reduce holdout mean absolute error by at least 5% relative to a calendar-and-linear-trend model. The January 2022 holdout boundary and the 5% threshold were fixed before model results were inspected.

## Result

The temperature features reduced holdout MAE by 8.1% against the calendar-and-trend regression, so the predefined point-estimate threshold passed. The year-block uncertainty interval ranges from -17.5 to 184.1 GWh and crosses zero, so the evidence is not stable across holdout years. The temperature model also has 46.1% higher MAE than the much simpler seasonal-naive benchmark.

The useful conclusion is therefore narrow: observed temperature adds some information to this particular regression specification, but this is not yet a competitive forecasting model. This motivated the rolling-origin extension below. A deployable follow-up still needs structural-break handling and weather values that would actually have been available at forecast time.

## Rolling-origin extension

A second protocol was committed before running an expanding-window backtest from January 2016 through August 2026. The model was refitted before each of 128 monthly predictions using only earlier demand observations.

The predefined usefulness gate failed:

- temperature-model MAE was 33.4% higher than seasonal naive;
- it beat seasonal naive in only 2 of 10 complete years;
- the year-block interval for seasonal-naive error minus temperature-model error was -370.7 to -41.1 GWh;
- temperature helped relative to seasonal naive in warm and cold months but deteriorated sharply in shoulder months.

This extension is explicitly exploratory relative to the original fixed holdout. It does not revise that earlier result. It shows why a favorable comparison against one weak baseline is insufficient.

## Data source

The project uses 308 consecutive monthly observations from the official Datos Argentina time-series API, January 2001 through August 2026:

- total electricity demand, GWh;
- average temperature, degrees Celsius;
- maximum power, MW.

The exact query, series identifiers, license, download date, row count, and file hash are frozen in [`data/source_manifest.json`](data/source_manifest.json). The analysis does not contain personal data.

## Run it

Python 3.10+ and no third-party packages are required.

```bash
python3 src/analyze.py
python3 -m unittest discover -s tests -v
python3 scripts/verify_release.py
```

The GitHub Actions workflow runs the same release verifier on every push and pull request, and can also be started manually. Until the repository is published, this is validated CI configuration rather than evidence of a hosted run.

The analysis writes:

- `results/metrics.json` with data scope, holdout metrics, hypothesis result, and boundaries;
- `results/predictions.csv` with every holdout prediction and error;
- `results/report.md` with the concise conclusion;
- `results/holdout_predictions.svg` with actual and predicted demand.
- `results/rolling_metrics.json` and `results/rolling_report.md` with the expanding-window extension;
- `results/rolling_predictions.csv` and `results/rolling_mae_by_year.svg` with its auditable forecasts and annual errors.

## Method

The training set ends in December 2021. The holdout begins in January 2022 and is never used to fit coefficients.

Three models are compared:

1. same month one year earlier;
2. linear trend plus month indicators;
3. the same calendar model plus heating degrees below 18 C and cooling degrees above 22 C.

The code uses ordinary least squares implemented with the Python standard library. A year-block bootstrap estimates the uncertainty of the absolute-error difference without pretending the monthly observations are independent.

## Boundaries

- Observed temperature is used, so this is not a production forecast.
- Aggregate national data does not support causal claims or local grid decisions.
- Calendar and linear trend are intentionally simple baselines, not a claim of best possible forecasting.
- The final year contains January through August 2026 only.
- A negative result remains part of the portfolio and determines the next experiment.

See [`docs/research-plan.md`](docs/research-plan.md) for the complete preregistered logic.
