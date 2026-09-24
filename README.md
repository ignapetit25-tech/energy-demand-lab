# Energy Demand Evidence Lab

[Website](https://ignapetit25-tech.github.io/energy-demand-lab/) · [Monthly sector report](https://ignapetit25-tech.github.io/energy-demand-lab/monthly-report.html)

A reproducible time-series investigation of whether monthly temperature adds predictive information for Argentina's electricity demand beyond trend and calendar seasonality.

## Monthly reporting tool

The static website is published by `.github/workflows/pages.yml` after the release checks pass on `main`. Build locally with `python3 scripts/build_site.py`. [Publishing instructions](docs/publicar-web.md).

The report also offers an [Excel workbook](dashboard/downloads/energy-demand.xlsx) with an editable reporting month, formula-based sector comparisons, chart and original data. The prospective register is connected to an outcome evaluator that retains archived source snapshots and does not overwrite issued forecasts. [Current status, remaining work and update procedure](docs/estado-y-actualizacion.md).

Open [the dashboard](dashboard/index.html) or [the monthly sector report](dashboard/monthly-report.html) locally in a browser. The report describes year-on-year demand changes, sector contributions and like-for-like year-to-date totals. It supports month selection, Markdown and CSV downloads, and browser printing. Its first report covers August 2026 from the September 20 source snapshot; [the reusable written report](reports/monthly/2026-08.md) includes evidence and limitations. It is descriptive, not climate-adjusted or causal.

Rebuild with `python3 scripts/build_dashboard.py`. No forecast is retrained or changed. See [dashboard instructions](dashboard/README.md) for validation and scope.

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

## Shoulder-month diagnostic

A diagnostic protocol was committed before investigating the rolling model's shoulder-season failure. The expanding temperature regression overpredicted every evaluated shoulder month by an average of 1,029.4 GWh. Temperature features were inactive inside the 18-22 C dead band in 39.7% of shoulder observations, but the more important failure was the long linear trend: fitting the same model on only the most recent 60 months reduced shoulder MAE from 1,029.4 to 362.2 GWh.

The recent-window result is a promising exploratory lead, not an independently confirmed winner. An annual-change temperature model also improved on seasonal naive, supporting a future architecture that anchors on recent demand rather than extrapolating the full 2001-present trend.

An advanced prespecified retrospective diagnostic then separated the main mechanisms. The dead band matters: expanding-temperature MAE is 1,222.3 GWh inside 18-22 C and 902.5 GWh when a weather feature is active. It is not the primary source of bias, however, because calendar and trend already overpredicts shoulder demand by 1,050.9 GWh on average. Sector data add context: from 2015 to 2025 the residential share rose from 41.8% to 46.7%, while commerce and industry remained near its 2015 level and large-user demand remained below it. These findings establish instability and composition change, not their economic causes.

## Nested window-selection extension

A nested retrospective protocol then tested whether annual-change training-window length could be selected using only demand outcomes available with a two-month reporting lag. The primary honest-information rule selected 120 months in 108 of 128 forecasts and achieved MAE of 622.4 GWh, worse than seasonal naive at 566.6 GWh. Its shoulder MAE was also worse, 645.8 versus 573.5 GWh, and the descriptive year-block interval favored seasonal naive.

The parallel perfect-foresight temperature variant reached 393.9 GWh overall, showing that target-month weather contains substantial potential information. It does not establish deployable skill because realized monthly temperature is unavailable at forecast time. The nested result therefore rejects adaptive recency alone as a rescue and sharpens the next question: whether archived or prospectively captured weather forecasts can recover enough of the oracle gap.

## Prospective forecast

The first eligible untouched target is October 2026. Its protocol was committed before calculation, and the forecast was issued on September 20 from an immutable August data vintage. Seasonal naive forecasts 10,591.336 GWh; the primary adaptive annual-change rule selected a 120-month window and forecasts 10,578.252 GWh. No target-month weather information was used. One outcome will be descriptive only, and the forecast will not be rewritten after release.

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
python3 src/rolling_backtest.py
python3 src/shoulder_diagnostic.py
python3 src/retrospective_diagnostics.py
python3 src/nested_validation.py
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
- `results/shoulder_diagnostic_metrics.json`, `results/shoulder_diagnostic_predictions.csv`, and `results/shoulder_diagnostic_report.md` with the prespecified failure analysis.
- `results/retrospective_descriptive/` with dead-band, coefficient-path, forecast-decomposition, and sector-composition diagnostics. Every artifact in this folder is explicitly non-confirmatory.
- `results/nested_exploratory/` with lag-correct nested window selections, honest-information forecasts, and a separately labeled temperature-oracle upper bound.
- `prospective/preregistration.md`, `prospective/forecasts.csv`, and `prospective/vintages/2026-10/` with the frozen October protocol, forecast, source data, code hash, and input hash.

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

The external next-stage methodology review is evaluated in [`docs/external-review-audit.md`](docs/external-review-audit.md). The audit accepts its core caution while correcting the first prospective target, sector-data coverage, climate-normal period, and demand-availability lag before implementation.
