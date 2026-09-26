# Changelog

## 2026-09-26 — Sector review dashboard and production contrast

- Added a separate, linked dashboard for 14 activities across 44 complete comparable months; Aluar remains separate and incomplete September is excluded.
- Preserved the original alert rule and added 27 exploratory sensitivity combinations plus four one-factor priority checks. Six August baseline priorities range from four to eight under the 27 combinations; frequency is not a confidence probability or a validation result.
- Archived and hashed the July INDEC IPI report. Compared July with July for textiles, metal products and cement, retaining category/population limitations and missing August production.
- Added reproducible JSON and a methods report, seven regression tests and browser checks covering periods, controls, downloads, keyboard, responsive layouts and print.
- Preserved Excel, national CSV and frozen forecasts. Data requests remain unsent; no automatic notifications or refresh were enabled.

## 2026-09-26 — Daily-source activity history and expanded workbook

- Archived CAMMESA's daily GUMA workbook and reconstructed 56 complete months plus a separately labeled partial month for 14 activities; no fixed establishment panel or contemporaneous historical vintages are assumed.
- Calculated Aluar monthly net-grid energy, including August 2025/2026, without imputing monthly production, gross consumption or self-generation. Reviewed quarterly disclosures and documented missing data/access limitations.
- Preserved conflicting August totals across PDF editions and the daily XLSX; did not silently reconcile or relabel them as growth.
- Extended the existing XLSX with Concentración, Aluar and Actividades. Added formulas, source references, missing-data guards and source-hash freshness checks while preserving the original three sheets.
- Added website filters, source-rich JSON, updated August TXT context, regression tests and browser coverage. Original national CSV and frozen forecasts remain unchanged.

## 2026-09-24 — Growth concentration and Aluar supply evidence

- Added interactive monthly/YTD national contributions and twelve monthly branch decompositions, separating shares of net growth from shares of consumption.
- Archived two Aluar annual reports: production, total electricity and supply mix remain separate. Preserved a 385 MWh source discrepancy; annual evidence is not attributed to August's monthly change.
- Added fourteen GUMA activities, complete August and partial September windows, and a separately matched 1–16 September comparison. Flagged membership changes, provisional status and the lack of individual-establishment or AI consumption identification.
- Added source-rich JSON, August TXT/Markdown evidence, validators and browser checks while retaining existing national CSV/XLSX and frozen forecasts.

## 2026-09-24 — Historical sector explorer and richer Argentine infrastructure

- Added 12 CAMMESA source editions (September 2025–August 2026), their published annual comparisons, and 164 same-calendar-month historical records across four branches.
- Flagged the documented coverage change from 98% to 90%, twelve unfilled early-period gaps, rounded levels and conflicting source headings. Comparisons across years use one source vintage; no homogeneous monthly series is claimed.
- Added 19 months of provisional INDEC capacity utilization for twelve activities and the general index, with independent month selection and percentage-point comparisons.
- Expanded Argentina from two to five documented facilities/projects: Stargate, Clementina, Cirion BUE1, EdgeConneX BUE01 and ARSAT. Added individually sourced technical quantities without converting capacity to measured energy.
- Added an interactive history page, downloadable source-rich JSON, expanded August TXT report, archived PDFs with hashes, offline extraction and five new regression tests.
- Preserved the existing visual system, native controls, national CSV/XLSX and frozen forecast. Verified desktop/mobile layouts and all 48 history selector combinations.

## 2026-09-24 — Argentine branches and documentary infrastructure register

- Added a visually checked CAMMESA August 2026 branch table, preserving its MW units, population, published growth rates and archived source PDF hash.
- Added July 2026 INDEC capacity utilization as separately dated context, not an August observation or electricity measurement.
- Added a filterable four-case infrastructure register, initially showing its two Argentine cases. Announced capacity, operating-status evidence, measured consumption, permits and legal events remain distinct.
- Added downloadable JSON, selected-month TXT context, source validation and five regression tests; verified mobile layout, keyboard filtering and downloads.
- Kept national-series CSV, Excel, research models and the frozen October forecast unchanged.

## 2026-09-24 — AI evidence and richer monthly exports

- Added a sourced AI/electricity evidence register separating international historical estimates, projections and an Argentine investment announcement.
- Added the AI research section to the web report and selected-month plain-text download; historical views explicitly label the current research vintage.
- Expanded Spanish CSV exports to include total, matched YTD, comparison dates, source URL/hash and unknown AI consumption as blank, never zero. Format: UTF-8 BOM, semicolon separator, decimal comma.
- Added the Excel sheet `IA y energía`, linked to the reporting-month control, with numerical evidence, sources and a formula-based global data-center contribution calculation. This is not an AI-only or Argentine attribution.
- Added evidence freshness validation and tests across all 248 month exports. Retained forecast code, source data and the frozen prospective forecast unchanged.

## 2026-09-24 — Excel download and prospective evaluator

- Added a formula-based XLSX with an editable reporting month, matched year-to-date comparisons, chart and original sector data.
- Added the Excel download to the website while retaining selected-month CSV and Markdown exports.
- Added source and workbook hash validation before deployment to prevent stale downloads.
- Connected prospective outcomes and errors to the dashboard; pending observations remain null.
- Added source-snapshot archival, idempotent outcome recording and revision detection without rewriting issued forecasts.
- Documented outstanding publication, weather, calendar and uncertainty work in `docs/estado-y-actualizacion.md`.

## 2026-09-24 — GitHub Pages website

- Added an explicit public site build with portable relative links and internal-link verification.
- Added GitHub Pages deployment after reproducibility checks pass on main.
- Added page metadata, site icon, publication instructions and a public-artifact hash manifest.
- Excluded local browser runtimes, screenshots and research source code from the web artifact.

## 2026-09-24 — Monthly sector diagnosis

- Added a monthly report integrated into the local dashboard, using the archived official sector dataset.
- Added year-on-year sector changes, additive percentage-point contributions, shares, and matched year-to-date comparisons.
- Added 248 selectable descriptive historical reports, Markdown/CSV exports, and print styles.
- Saved the August 2026 written report and numerical output with source provenance.
- Verified reconciliation, missing-month behavior, zero bases, cancelling sector changes, and browser interactions.
- Kept frozen forecast artifacts intact; no prospective performance claims or causal attribution are made by this module.

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
