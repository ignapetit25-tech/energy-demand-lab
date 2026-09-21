# Changelog

## 2026-09-20 — Prospective boundary frozen

- Declared all outcomes through August 2026 previously examined.
- Rejected September 2026 as a prospective target because its August 31 issuance cutoff had passed.
- Preregistered October 2026 as the first prospective target before calculating its forecast.
- Froze a two-month demand-availability lag and prohibited current-month realized temperature and maximum power.
- Issued the October forecast from the August 2026 input vintage.
- Primary adaptive annual-change forecast: 10,578.252 GWh.
- Seasonal-naive benchmark: 10,591.336 GWh.
- Selected adaptive window: 120 months.
- Recorded source and code hashes and retained the input vintage under `prospective/vintages/2026-10/`.

No October outcome was available or inspected when these artifacts were created.

## 2026-09-20 — Retrospective extensions

- Added prespecified shoulder-season diagnostics.
- Added official sector series and verified component-to-total consistency.
- Added advanced retrospective diagnostics for dead-band activity, parameter paths, forecast decomposition, and sector composition.
- Added lag-correct nested window selection with honest-information and perfect-foresight variants.
- Labeled every post-holdout diagnostic and nested result as non-confirmatory.
