# Nested window-selection results

**Status: RETROSPECTIVE-EXPLORATORY; NOT CONFIRMATORY.**

## Primary honest-information result

The adaptive annual-change model achieved overall MAE of **622.4 GWh**, compared with **566.6 GWh** for seasonal naive. Shoulder MAE was **645.8 GWh**, compared with **573.5 GWh**.

The year-block interval for seasonal-naive absolute error minus adaptive-model absolute error is **-99.1 to -13.8 GWh**. This interval is descriptive because the outer period was already examined.

## Perfect-foresight comparison

The adaptive temperature-oracle variant achieved overall MAE of **393.9 GWh**. Its difference from the honest model measures the advantage of knowing realized target-month temperature, not deployable weather skill.

## Window selections

The honest rule selected 36 months **9** times, 60 months **0** times, 84 months **11** times, and 120 months **108** times. Frequent switching is retained as evidence about instability rather than hidden through a single retrospective window.

## Availability boundary

Every outer forecast uses demand only through `t-2`. Every inner pseudo-forecast applies the same rule. Calendar-holiday features remain excluded until their historical vintages are independently frozen.
