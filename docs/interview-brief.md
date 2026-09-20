# Interview brief

## Thirty-second summary

I tested whether observed temperature improves estimates of Argentina's monthly electricity demand after accounting for trend and seasonality. I fixed the first holdout and success threshold before inspecting results. Temperature improved that regression's MAE by 8.1%, but a simple seasonal-naive benchmark remained stronger. I then committed a second rolling-origin protocol before execution. Across 128 forecasts, the temperature model was 33.4% worse than seasonal naive and passed none of the three usefulness conditions. I kept both results because model selection should follow evidence, not novelty.

## What I owned

- Converted a broad energy question into a falsifiable hypothesis.
- Selected official public data and froze the exact query and file hash.
- Defined the train/holdout split, success threshold, and interpretation rules before results.
- Implemented three comparable baselines without third-party packages.
- Added tests for source integrity, chronological coverage, feature behavior, numerical solving, and reproducibility.
- Interpreted the favorable point estimate together with its contradictory benchmark and uncertainty.
- Used a separate commit to prove that the rolling-origin success gate preceded its result.
- Diagnosed performance by year and season without changing the frozen model.

## The result I would defend

Observed temperature adds information relative to a weak calendar-and-trend regression, but the specification is not competitive with seasonal naive. The rolling-origin test confirms this across a longer window: temperature-model MAE is 33.4% higher overall, it wins only 2 of 10 complete years, and the year-block interval favors seasonal naive. Its relative gains in warm and cold months are overwhelmed by large shoulder-month errors.

## What could fail

- The linear trend cannot represent structural breaks in electricity demand.
- Observed temperature leaks information unavailable in a real forward forecast.
- Five full holdout years plus eight months of 2026 provide limited uncertainty evidence.
- National aggregation hides regional weather and demand patterns.
- Fixed heating and cooling balance temperatures may not reflect Argentina's heterogeneous climate and building stock.

## Next experiment

Use rolling-origin evaluation with only information available at each forecast date. Compare seasonal naive, recent-growth seasonal models, and a temperature model using archived weather forecasts. Report accuracy by season and year, not only one aggregate score.

## Personal ownership questions

1. Why is the seasonal-naive baseline so important here?
2. Why did you freeze the 5% threshold before running the model?
3. What does it mean that the interval crosses zero?
4. Why is observed temperature inappropriate for a production forecast?
5. Which decision would this analysis support today, and which would it not support?
