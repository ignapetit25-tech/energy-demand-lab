# Shoulder-month diagnostic results

## Main finding

The failure is driven primarily by **level and trend misspecification**, not simply by inactive temperature features. During shoulder months, the expanding temperature model overpredicts demand by **1029.4 GWh on average** and has MAE of **1029.4 GWh**, versus **573.5 GWh** for seasonal naive.

Temperature sits inside the 18-22 C dead band in **39.7%** of shoulder forecasts. That contributes to the problem because the weather terms cannot correct the level model in those observations, but it is not a complete explanation: the long-run linear trend is already extrapolating too high.

## Diagnostic alternatives

| Model | Shoulder MAE GWh | Shoulder mean error GWh |
| --- | ---: | ---: |
| Seasonal naive | 573.5 | -48.8 |
| Expanding trend and temperature | 1029.4 | 1029.4 |
| Recent 60-month trend and temperature | 362.2 | 120.3 |
| Annual-change temperature model | 471.8 | 179.0 |

The recent-window probe tests whether old history is distorting the trend. The annual-change probe anchors each forecast on the same month one year earlier and estimates only the change associated with weather differences. These are exploratory results, not a new confirmed winner.

## Error concentration

The ten largest shoulder-month losses account for **34.4%** of the expanding model's gross positive excess absolute error relative to seasonal naive. This means unusual months matter, but the weakness is not safely reducible to a single outlier.

## Interpretation boundary

This diagnostic preserves the original results. It does not justify causal conclusions or production use, and every temperature model still receives observed current-month temperature.
