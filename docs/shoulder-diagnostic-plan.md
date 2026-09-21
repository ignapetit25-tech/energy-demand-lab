# Shoulder-month diagnostic plan

Plan fixed before generating the shoulder-month diagnostic outputs.

## Question

Why does the expanding-window temperature regression perform much worse than seasonal naive during Southern Hemisphere shoulder months (March-May and September-November)?

This is an exploratory diagnostic prompted by the rolling-origin result. It does not alter the original holdout hypothesis or the rolling usefulness gate.

## Candidate explanations

1. **Inactive temperature features.** Temperatures between 18 C and 22 C set both degree features to zero, so the temperature model reduces to calendar and linear trend precisely when weather is mild.
2. **Stale linear trend.** An expanding linear trend fitted since 2001 may extrapolate historical growth after the demand process has slowed or changed, producing persistent overprediction.
3. **Concentrated disruptions.** A small number of unusual years or months may account for most of the shoulder-season gap.
4. **Model architecture.** Forecasting the demand level with a long linear trend may be less robust than anchoring the prediction on demand from the same month one year earlier and estimating only the annual change.

## Fixed diagnostics

Using the 128 rolling forecasts from January 2016 through August 2026:

- report temperature-feature activation by season and calendar month;
- report MAE and signed error by season and calendar month;
- split results into 2016-2019, 2020-2022, and 2023-August 2026;
- list the ten largest shoulder-month losses relative to seasonal naive;
- measure how much of the total shoulder-month excess absolute error is contained in those ten months;
- compare two exploratory alternatives with the existing expanding temperature model:
  - the same regression fitted on only the most recent 60 months;
  - an annual-change model anchored on the same month one year earlier, with changes in heating and cooling degree features as predictors.

The 60-month window and annual-change formulation are diagnostic probes, not tuned production candidates. No thresholds, balance temperatures, or time buckets will be changed after outputs are generated.

## Interpretation rules

- Large positive signed errors in both fitted level models support the stale-trend explanation.
- A high dead-band rate supports feature inactivity but is insufficient on its own; it must coincide with weak performance.
- Error concentration in a few months weakens a general seasonal explanation and points to disruptions or omitted variables.
- Improvement from the annual-change model supports recent-level anchoring as a better architecture; it does not establish that the model is deployable.
- All models still use observed current-month temperature and therefore remain oracle diagnostics rather than real forecasts.
