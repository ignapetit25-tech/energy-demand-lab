# Energy Demand Evidence Lab results

## Result

The predefined hypothesis was **supported**. Adding heating and cooling degree features changed holdout MAE by **8.1%** relative to the calendar-and-trend model.

This is a point-estimate result, not decisive evidence. The uncertainty interval crosses zero. In addition, the temperature model's MAE is **46.1% higher** than the seasonal-naive benchmark.

## Holdout metrics

| Model | MAE GWh | RMSE GWh | MAPE |
| --- | ---: | ---: | ---: |
| Seasonal naive | 631.3 | 853.1 | 5.24% |
| Calendar and linear trend | 1003.8 | 1153.0 | 8.95% |
| Calendar trend and temperature | 922.6 | 1065.0 | 8.25% |

The year-block bootstrap 95% interval for monthly absolute-error improvement was **-17.5 to 184.1 GWh**. Because it includes zero, the data do not establish a stable improvement across holdout years. The interval respects year blocks, but the small number of holdout years still limits precision.

## Interpretation boundary

This benchmark uses observed monthly temperature, so it is not a real operational forecast. It estimates incremental explanatory and predictive value conditional on known temperature. The aggregate series does not justify causal claims, local grid recommendations, or individual policy decisions.
