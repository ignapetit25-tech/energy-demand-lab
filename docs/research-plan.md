# Research plan

## Question

Does observed monthly average temperature improve out-of-sample estimates of Argentina's total electricity demand after accounting for linear time trend and calendar month?

## Predefined hypothesis

Adding heating and cooling degree features will reduce mean absolute error by at least 5% versus a model containing only linear trend and month indicators on the January 2022 to August 2026 holdout.

The threshold and holdout were chosen before inspecting model results. Failure to reach 5% is a valid negative result and will not trigger retrospective changes to balance temperatures or the split.

## Data

The official Datos Argentina monthly series contains total electricity demand, average temperature, and maximum power. The frozen file has 308 consecutive months from January 2001 through August 2026. The source URL, API query, identifiers, license, row count, and SHA-256 hash are recorded in `data/source_manifest.json`.

Official references:

- [Monthly electricity demand resource](https://datos.gob.ar/dataset/sspm-demanda-electricidad/archivo/sspm_367.3)
- [Argentina time-series API catalog](https://datos.gob.ar/dataset/jgm-base-series-tiempo-administracion-publica-nacional/archivo/jgm_3.13)

## Evaluation design

Training period: January 2001 through December 2021.

Holdout period: January 2022 through August 2026.

Models:

1. Seasonal naive: use demand from the same month one year earlier.
2. Calendar and trend: intercept, linear time trend, and month indicators.
3. Calendar, trend, and temperature: the same features plus heating degrees below 18 C and cooling degrees above 22 C.

Primary metric: mean absolute error in GWh.

Secondary metrics: root mean squared error, mean absolute percentage error, and mean error.

Uncertainty check: resample complete holdout years with replacement and calculate a 95% interval for the difference in absolute error between calendar-only and temperature models. This is a robustness aid, not a substitute for additional time periods.

## Interpretation rules

- The hypothesis passes only if temperature reduces holdout MAE by at least 5%.
- A lower error does not establish that temperature causes demand changes.
- Observed temperature is available to the benchmark, so the result is not a true ex-ante forecast.
- Aggregate national data cannot identify local network constraints or recommend infrastructure investment.
- The partial 2026 calendar year must remain visible in the report.

## Decision after results

If temperature adds material value, the next experiment should replace observed temperature with a separately sourced weather forecast and use rolling-origin evaluation. If it does not, investigate nonlinear trend, structural breaks, and sector composition before adding model complexity.
