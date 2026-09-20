# Rolling-origin backtest results

## Result

The predefined usefulness gate **did not pass**. Across 128 monthly forecasts, the temperature model's MAE was **33.4% higher** than seasonal naive and **10.1% lower** than calendar and trend.

The temperature model beat seasonal naive in **2 of 10** complete calendar years. The year-block 95% interval for seasonal-naive MAE minus temperature-model MAE was **-370.7 to -41.1 GWh**.

The aggregate result hides a seasonal split. Relative to seasonal naive, the temperature model's MAE changed by **-14.0% in warm months**, **-10.6% in cold months**, and **79.5% in shoulder months**. Negative values indicate lower error. The large shoulder-month deterioration is the clearest next diagnostic target.

## Overall metrics

| Model | MAE GWh | RMSE GWh | MAPE | Mean error GWh |
| --- | ---: | ---: | ---: | ---: |
| Seasonal naive | 566.6 | 736.1 | 4.98% | -83.1 |
| Calendar and trend | 840.8 | 995.4 | 7.83% | 719.1 |
| Calendar, trend, and temperature | 755.8 | 897.5 | 7.07% | 728.1 |

## Interpretation

The rolling-origin design is more demanding than one fixed split because every month is evaluated using only earlier demand observations. The temperature model still receives observed current-month temperature, so even a favorable result would not establish deployable forecast performance. The original 2022 holdout result remains unchanged and should be read separately.
