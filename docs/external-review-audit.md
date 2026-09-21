# Orchestrator audit of the external methodology review

Audit date: 2026-09-20.

The external review is accepted as a strong methodological critique, subject to the corrections below. This document records the orchestrator's decision rather than treating another model's answer as authority.

## Accepted recommendations

- All observations through August 2026 have been examined. No analysis using that period can become fresh confirmation.
- The current evidence establishes systematic forecast bias but does not identify trend, level, seasonality, temperature coefficients, calendar, demand composition, or macroeconomic conditions as the dominant mechanism.
- Realized current-month temperature is a perfect-foresight input and must remain labeled as an explanatory upper bound rather than a deployable forecast input.
- The 60-month and annual-change results remain exploratory.
- Nested rolling evaluation can test whether a model-selection rule could have operated using past information, but it remains retrospective.
- A prospective protocol must archive input vintages and forecasts before outcomes become available.
- Twelve prospective observations are descriptive and are insufficient for a meaningful year-block uncertainty interval.

## Corrections required before implementation

### 1. First prospective target

September 2026 cannot be the first prospective target. The proposed forecast cutoff was August 31, 2026, and the audit is occurring on September 20. An unpublished outcome does not make a forecast prospective if its issuance deadline has already passed.

The earliest eligible target is **October 2026**, provided the protocol, code, input snapshot, and forecast are frozen no later than September 30, 2026.

### 2. Sector-series coverage

The official API confirms that monthly residential, commerce-and-industry, and large-user demand begin in January 2005, not January 2001. There are 260 complete monthly observations through August 2026, no gaps after the first observation, and the three components sum to total demand within floating-point precision for every covered month.

Verified series:

- total: `367.3_DEMANDA_TOTAL__13`;
- residential: `367.3_DEMANDA_REIAL__19`;
- commerce and industry: `367.3_COMERCIO_ERIA__20`;
- large users: `367.3_GRANDES_USIOS__16`.

Official API query:

`https://apis.datos.gob.ar/series/api/series/?ids=367.3_DEMANDA_TOTAL__13,367.3_DEMANDA_REIAL__19,367.3_COMERCIO_ERIA__20,367.3_GRANDES_USIOS__16&format=json&limit=5000`

These series are approved for retrospective composition diagnostics. Contemporaneous sector demand is not approved as a predictor of contemporaneous total demand.

### 3. Climate-normal reference period

The located official SMN resource publishes station-level monthly climate normals for **1981-2010**, not 1991-2020:

`https://www.datos.gob.ar/dataset/smn-estadisticas-climaticas-normales/archivo/smn_8.1`

No 1991-2020 normal may be referenced until an authoritative publication is located and archived. Station normals also cannot be converted into a national electricity-demand weather index without a weighting rule fixed independently of forecast outcomes.

### 4. Demand-availability lag in nested validation

The review states that a forecast for month `t`, issued at the end of `t-1`, may use demand through `t-2`. Its pseudocode nevertheless scores inner origins through `t-1`. That is inconsistent.

The corrected inner validation set must end at `t-2`. For a 24-month inner evaluation, use the 24 targets from `t-25` through `t-2`. Each inner forecast for month `s` must itself use demand outcomes no later than `s-2`.

This lag convention must be used consistently in window selection, refitting, baselines, and feature construction.

### 5. Climatology is not a weather forecast deviation

If the deployed weather forecast is set equal to the monthly normal, then forecast-minus-normal equals zero by construction. The weather adjustment contributes nothing to the prospective forecast. This is an honest fallback, but it tests an anchored calendar model rather than deployable weather value.

The first challenger should therefore be described as **annual-change plus calendar**, with climatology as a zero-deviation fallback. A weather contribution may be activated only after a dated, reproducible forecast source and a fixed conversion rule are archived.

### 6. Status of the 60-month probe

The 60-month window was written into `docs/shoulder-diagnostic-plan.md` and committed before its diagnostic result was generated. It was not selected after seeing its exact MAE. It was, however, proposed after the original rolling failure was known, so it remains exploratory and cannot be called confirmed.

### 7. Timing of the suspected instability

The current evidence does not isolate a post-2020 or post-2021 break. Positive expanding-model bias is already visible in 2016-2019. Any hypothesis must refer broadly to parameter instability or historical-regime mismatch until recursive estimates or a prespecified break diagnostic show otherwise.

## Approved next-stage sequence

1. Add the verified 2005-2026 sector series as a separately hashed diagnostic input.
2. Run the prespecified retrospective diagnostics: dead-band split, no-temperature comparison, recursive parameters, residual views, sector composition, forecast decomposition, and percentage errors.
3. Implement the corrected nested selection rule with the two-month demand-availability convention. Label every output retrospective-exploratory.
4. Keep the prospective challenger parsimonious: same-month-last-year anchor, recent drift, working-day difference, and Easter placement. Weather deviation defaults to zero until a reproducible forecast vintage exists.
5. Freeze the code, October 2026 input vintage, forecast, benchmarks, and failure rules by September 30, 2026.
6. Publish the October forecast before the target month begins and never rewrite it after the outcome appears.

## Scientific claim retained

The expanding temperature model, even with realized current-month temperature, does not reliably beat seasonal naive out of sample. Its shoulder-month failure is systematic. Short-window and annual-change specifications generate promising retrospective hypotheses, but the dominant failure mechanism is not identified and no deployable improvement is yet confirmed.
