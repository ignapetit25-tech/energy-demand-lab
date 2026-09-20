# Rolling-origin backtest plan

Plan fixed before running the rolling-origin extension.

## Question

Does the temperature-enhanced regression remain competitive when every evaluated month is predicted by a model fitted only on earlier observations?

## Evaluation window

- First forecast: January 2016.
- Last forecast: August 2026.
- Origin: expanding window, refitted once for every forecast month.
- Minimum training history: January 2001 through December 2015.
- Total expected forecasts: 128 consecutive months.

## Fixed models

1. Seasonal naive: demand from the same month one year earlier.
2. Calendar and trend: intercept, linear time trend, and month indicators.
3. Calendar, trend, and temperature: the same regression plus heating degrees below 18 C and cooling degrees above 22 C.

The current month's observed temperature is supplied to model 3. This makes it an explanatory oracle benchmark, not a deployable ex-ante forecast.

## Primary usefulness gate

The temperature model will be considered competitive only if all three conditions hold:

1. Its overall mean absolute error is lower than seasonal naive.
2. Its annual mean absolute error is lower in at least 6 of the 10 complete calendar years from 2016 through 2025.
3. A year-block bootstrap 95% interval for seasonal-naive absolute error minus temperature-model absolute error is entirely above zero.

Failure on any condition rejects the usefulness claim for this specification.

## Secondary checks

- Overall MAE, RMSE, MAPE, and mean error for all three models.
- Temperature-model improvement relative to calendar and trend.
- Metrics by calendar year.
- Metrics for warm months (December through February), cold months (June through August), and shoulder months.
- Share of individual months in which each fitted model beats seasonal naive.

## Interpretation rules

- This extension does not alter or replace the original fixed 2022 holdout result.
- No balance temperature, start date, model feature, or usefulness condition will be changed after results are generated.
- A favorable result cannot support causal claims.
- The partial 2026 year appears in monthly and overall results but does not count toward the complete-year majority condition.
- Observed temperature prevents a production-forecast interpretation.
