# Nested window-selection plan

Status: fixed before generating nested-validation results.

Every output from this plan is **retrospective-exploratory**, because all outcomes through August 2026 were previously examined. The purpose is to test whether a window-selection rule is operationally coherent, not to create new confirmation.

## Question

Can an annual-change model select its training-window length using only demand outcomes that would have been available before each forecast?

## Availability convention

- A forecast for month `t` is conceptually issued at the end of `t-1`.
- Monthly demand for `t-1` is not yet assumed available.
- The latest permitted demand outcome is therefore `t-2`.
- The same two-month convention applies inside every simulated inner forecast.
- `y[t-12]` is available and supplies the level anchor.

## Outer evaluation

- January 2016-August 2026.
- Overall and shoulder-month MAE, MAPE, RMSE, and mean error.
- Shoulder months remain March-May and September-November.
- No outer outcome may affect window selection for that month.

## Inner window selection

- Candidate windows: 36, 60, 84, and 120 available monthly change observations.
- Inner targets: the 24 months from `t-25` through `t-2`.
- Each inner target `s` is fitted using demand outcomes no later than `s-2`.
- Score: inner mean absolute error.
- Tie-break: select the larger window.

## Models

1. Seasonal naive: `y[t-12]`.
2. Seasonal naive plus expanding historical mean annual change.
3. Original expanding calendar/trend/temperature regression, refitted only through `t-2`; current-month realized temperature remains explicitly oracle information.
4. Fixed 60-month annual-change model.
5. Adaptive annual-change model selected by the nested rule.

The annual-change model predicts `y[t] - y[t-12]` using an intercept and calendar-month indicators. This deliberately excludes a historical holiday adjustment until an authoritative dated calendar is frozen.

Two adaptive variants will be reported:

- **honest information:** intercept and month indicators only;
- **perfect-foresight upper bound:** the same features plus current-versus-prior-year heating and cooling degree differences.

The honest-information variant is primary. The oracle result may illustrate potential weather value but cannot be presented as deployable.

## Interpretation rules

- Nested selection does not make the examined 2016-2026 outcomes confirmatory.
- A strong honest-information result supports the operational value of adaptive recency, not a specific structural-break story.
- A large gap between oracle and honest variants measures perfect-foresight advantage, not achievable weather skill.
- Frequent changes in the selected window are evidence of instability and must remain visible.
- No candidate window, inner length, start date, model feature, or tie-break will change after results are generated.
