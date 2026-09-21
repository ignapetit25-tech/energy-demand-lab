# Prompt for Meta AI

I am developing a reproducible research portfolio project called **Energy Demand Evidence Lab**. Please act as a critical research collaborator and help me improve the project without overstating the evidence.

The project investigates whether monthly average temperature adds out-of-sample predictive information for Argentina's total electricity demand. The frozen official dataset contains 308 consecutive monthly observations from January 2001 through August 2026: total electricity demand in GWh, average temperature in degrees Celsius, and maximum power in MW.

The original evaluation used data through December 2021 for training and January 2022 through August 2026 as a fixed holdout. It compared:

1. seasonal naive: demand from the same month one year earlier;
2. calendar and linear trend: a linear time trend plus month indicators;
3. calendar, trend, and temperature: the same regression plus heating degrees below 18 C and cooling degrees above 22 C.

The temperature model reduced holdout MAE by 8.1% relative to calendar and trend, passing a predefined 5% point-estimate threshold. However, its year-block uncertainty interval crossed zero, and its MAE was 46.1% higher than seasonal naive.

A separately planned expanding-window backtest then generated 128 monthly forecasts from January 2016 through August 2026, refitting each model using only earlier demand observations. Seasonal naive achieved MAE of 566.6 GWh, calendar and trend 840.8 GWh, and calendar, trend, and temperature 755.8 GWh. The temperature model was therefore 33.4% worse than seasonal naive overall. It performed better than seasonal naive in warm and cold months but 79.5% worse during Southern Hemisphere shoulder months: March-May and September-November.

I then predefined a shoulder-month diagnostic before generating additional results. The diagnostic found:

- the expanding temperature model overpredicted every evaluated shoulder month, with mean error and MAE both equal to 1,029.4 GWh;
- seasonal naive shoulder-month MAE was 573.5 GWh;
- temperature was inside the model's 18-22 C dead band in 39.7% of shoulder observations, especially April, October, and November;
- the ten largest shoulder-month losses represented 34.4% of gross positive excess absolute error, so the failure was not caused by one isolated outlier;
- fitting the same temperature regression on only the most recent 60 months reduced shoulder MAE to 362.2 GWh and overall MAE to 334.0 GWh;
- an exploratory annual-change model anchored on the same month one year earlier achieved shoulder MAE of 471.8 GWh and overall MAE of 431.4 GWh.

My current interpretation is that inactive temperature features contribute to the shoulder-month problem, but the main failure is level and trend misspecification: a linear trend fitted on all history since 2001 extrapolates past growth too aggressively after the demand process changes. The strong recent-window result supports that explanation, but it was discovered on the evaluation period and is not yet independently confirmed.

Please do the following:

1. Critique this interpretation and identify plausible alternative explanations.
2. Evaluate whether the diagnostic design adequately distinguishes dead-band failure, structural change, unusual years, and trend misspecification.
3. Propose one focused next experiment with a new untouched evaluation period or a defensible nested time-series validation design.
4. Recommend variables that would have been genuinely available at forecast time, such as weather forecasts, economic activity, tariffs, holidays, or regional demand, and explain which add the most value.
5. Explain how to test structural breaks without using future information or tuning the model retrospectively.
6. Suggest a simple, interpretable forecasting architecture that combines a recent demand anchor with forecast weather.
7. Clearly separate confirmed findings, exploratory findings, hypotheses, and causal claims that the data cannot support.

Do not optimize for a positive result. Prefer a falsifiable design, strong baselines, temporal validation, uncertainty estimates, and honest reporting of negative evidence. Write your response for an economics-oriented researcher who uses AI to implement code and wants to demonstrate sound judgment rather than algorithmic complexity.
