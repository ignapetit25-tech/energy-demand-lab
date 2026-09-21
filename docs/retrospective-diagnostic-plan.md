# Retrospective diagnostic protocol

Status: fixed before generating the advanced diagnostic outputs.

All results produced under this protocol are **retrospective and descriptive**. They use a period that has already been examined and cannot confirm a new forecasting claim.

## Questions

1. Is the shoulder-month bias materially larger when the 18-22 C temperature features are inactive?
2. Does the calendar-and-trend model show the same positive bias as the temperature model?
3. Which fitted parameters change between expanding-history and recent-history estimation?
4. Did the residential, commerce-and-industry, or large-user components change their growth or share of total demand?
5. Does the failure remain visible in percentage errors as well as GWh?

## Frozen inputs

- Existing frozen total-demand dataset: January 2001-August 2026.
- Official sector series from Datos Argentina: January 2005-August 2026.
- Sector series must have no gaps and residential plus commerce-and-industry plus large users must equal total demand within 0.01 GWh for every covered month.
- Rolling evaluation window: January 2016-August 2026.
- Shoulder months: March-May and September-November.
- Temperature dead band: 18-22 C, unchanged from the original model.
- Recent comparison window: 60 months, unchanged from the earlier diagnostic plan.

## Outputs fixed in advance

1. Shoulder metrics inside and outside the dead band for seasonal naive, calendar-and-trend, and expanding temperature models.
2. Shoulder mean error, MAE, MAPE, and bias share (`mean error / MAE`) for all three models.
3. Monthly expanding and 60-month coefficient paths for trend, heating, cooling, and shoulder-month indicators.
4. A row-level decomposition of every expanding temperature prediction into intercept, trend, month, heating, and cooling components.
5. Sector indices with 2015 annual average equal to 100, sector shares, and year-on-year growth.
6. A concise report stating which explanations are supported, weakened, or still unresolved.

## Interpretation rules

- If expanding calendar-and-trend has similar shoulder bias to the temperature model, temperature is failing to correct an underlying level specification rather than creating the bias.
- If bias is much larger inside the dead band, feature inactivity contributes. Similar bias inside and outside weakens that explanation.
- Large changes in recent versus expanding trend, month, or temperature coefficients demonstrate instability but do not identify its cause.
- Diverging sector indices or shares support a composition explanation but do not establish macroeconomic or tariff causality.
- Similar failure in percentage and GWh terms rules out demand scale as the sole explanation.
- No breakpoint, balance temperature, window, or subset will be selected after results are generated.
