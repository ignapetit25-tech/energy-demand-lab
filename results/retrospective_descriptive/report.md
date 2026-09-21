# Advanced retrospective diagnostic results

**Status: RETROSPECTIVE-DESCRIPTIVE; NOT CONFIRMATORY.**

## Dead band versus active temperature features

The expanding temperature model has shoulder-month mean error of **1222.3 GWh** inside the 18-22 C dead band and **902.5 GWh** when a heating or cooling feature is active. Corresponding MAE values are **1222.3** and **902.5 GWh**.

The dead-band MAE is **35.4% higher**. Feature inactivity therefore contributes to the shoulder failure, but the large positive error outside the band shows that it is not a complete explanation. This split does not identify a causal temperature effect.

## Temperature is not creating the underlying bias

Across all shoulder months, calendar and trend has mean error of **1050.9 GWh** and the temperature model has mean error of **1029.4 GWh**. Their MAPE values are **10.72%** and **9.97%**. The comparison shows whether temperature creates the positive bias or merely changes an already biased level forecast.

Temperature reduces the calendar-and-trend mean error by only **21.5 GWh**. The bias is therefore already present in the level-and-calendar specification. Because percentage errors remain close to 10%, growth in the scale of demand cannot explain the failure by itself.

## Parameter instability

The expanding model's estimated trend falls from **333.4** to **219.2 GWh per year**. The recent-60-month estimate falls from **325.8** to **64.1 GWh per year** and ranges as low as **-107.1**. Heating, cooling, and shoulder-month coefficients also move materially. This establishes parameter instability but cannot distinguish gradual change, discrete breaks, omitted variables, or aggregation effects.

## Sector composition

Residential demand represented **41.8%** of total demand in 2015 and **46.7%** in 2025. Commerce and industry changed from **38.6%** to **36.3%**, while large users changed from **19.6%** to **17.1%**.

These movements can support a composition hypothesis but cannot establish why the shares changed.

The 2015-to-2025 sector indices show residential demand rising to **119.8**, commerce and industry remaining near **100.2**, and large users at **92.5**. The aggregate slowdown is therefore not a uniform slowdown across consumers. The residential share did not fall; it rose, weakening that specific version of the composition hypothesis.

## Files

- `coefficient_paths.csv`: expanding and recent-60-month parameter trajectories.
- `shoulder_decomposition.csv`: intercept, trend, month, heating, and cooling contribution for every shoulder forecast.
- `sector_diagnostics.csv`: monthly sector levels, shares, 2015-based indices, and annual growth.
- `metrics.json`: frozen summaries and interpretation boundaries.
