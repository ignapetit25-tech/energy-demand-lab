# Prospective electricity-demand forecast protocol

Protocol frozen on 2026-09-20 before calculating the first prospective forecast.

## Confirmatory boundary

All demand outcomes through August 2026 have been examined. September 2026 is not eligible because its required August 31 issuance cutoff has passed. The first eligible target is **October 2026**.

The October forecast will be issued from the frozen August 2026 demand vintage on September 20, 2026, before the target month begins and before its demand outcome exists. It will never be rewritten after publication.

## Forecast timing and available information

- Target: total monthly electricity demand in Argentina, GWh.
- Forecast for month `t` is issued before `t` begins.
- Latest permitted monthly demand observation: `t-2`.
- Same-month-last-year demand `y[t-12]` is available as the level anchor.
- Current-month realized temperature, maximum power, sector demand, EMAE, and any later-released information are prohibited.
- No weather adjustment is active in the first challenger. Climate-normal weather implies zero forecast deviation and therefore contributes zero by construction.

## Frozen models

### Benchmark

Seasonal naive:

`forecast[t] = demand[t-12]`

### Primary challenger

Adaptive annual-change model:

`demand[t] - demand[t-12] = intercept + calendar-month indicators + error`

- Candidate training windows: 36, 60, 84, and 120 monthly annual-change observations.
- Window selection uses the 24 inner targets from `t-25` through `t-2`.
- Every inner target `s` is fitted using outcomes no later than `s-2`.
- Selection metric: inner MAE.
- Tie-break: larger window.
- After selection, refit through `t-2` and forecast `t` from the `t-12` anchor.

The challenger has no contemporaneous weather feature and no holiday adjustment. Those features may be introduced only in a separately preregistered future challenger; the October forecast will not be retroactively changed.

### Secondary recorded comparisons

- Seasonal naive plus expanding historical mean annual change.
- Fixed 60-month annual-change model with the same month indicators.

These secondary values cannot replace the primary challenger after outcomes are known.

## Frozen evaluation

For every future month, archive:

- target period;
- forecast issue timestamp;
- input-file hash and latest input period;
- code hash;
- benchmark, challenger, and secondary forecasts;
- selected window and all inner-window MAE scores;
- outcome publication date and source hash when available;
- absolute error, percentage error, and signed error.

Metrics after outcomes arrive:

- overall MAE, MAPE, RMSE, and mean error;
- shoulder-month MAE and mean error, with shoulder fixed as March-May and September-November;
- paired monthly error differences against seasonal naive.

## Decision rules

- One, six, and twelve months are descriptive checkpoints only.
- At twelve complete months, the challenger is considered promising only if its overall MAE is at least 5% below seasonal naive, its shoulder MAE is not worse, and its absolute mean bias is lower.
- Missing any condition is a negative result.
- No year-block confidence interval will be reported with only twelve months.
- Formal year-block uncertainty requires at least 36 complete prospective months; 48-60 are preferred.
- Every forecast and outcome will be reported regardless of performance.

## Missing-data and revision rules

- If a new demand release is late, the forecast still uses the previously available vintage.
- Input vintages are immutable and stored separately by issue month.
- Later source revisions do not alter the original forecast. They may be recorded in a separate revised-outcome column.
- If a future weather forecast source is unavailable, its deviation remains zero. Realized weather is never substituted.

## Prohibited reinterpretations

- A favorable October error does not confirm the model.
- A favorable twelve-month point estimate does not establish statistical precision.
- The adaptive rule does not identify structural breaks or causal drivers.
- The prospective exercise tests a forecast procedure, not the causal effect of temperature, tariffs, activity, or sector composition.
