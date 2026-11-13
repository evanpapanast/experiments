# Automated monthly close (concept)

**[Open the close report →](https://evanpapanast.github.io/experiments/monthly-close/dashboard/)**

A month-end close, the way an FP&A team does it, run by a scripted pipeline instead of by hand:
**new data → quality checks → actual vs budget → calculation checks → forecast → commentary → human approval.**

This is a one-off demonstration run on the April 2026 close of the [Iowa spirits market](../liquor-market/) experiment.
It reuses that experiment's monthly table and its December 2025 budget.

## Why governance comes first

Financial figures can tell a false story if one calculation is wrong. So in this pipeline:

1. **Nothing is typed by hand.** Every number on the report comes from one generated file, `dashboard/data.js`.
2. **Every figure must add up before it is shown.** The script reconciles to the source and to the earlier published figures, and checks that every split adds back to its total. If any FAIL check fails, the script stops and writes no report data.
3. **Every step leaves a trail.** The SQL that ran is in `sql/`, its results are saved unchanged in `data/`, and each input file is fingerprinted (SHA-256).
4. **A person approves.** Changes reach the live page only through a reviewed pull request.

During the build, check K6 caught a hand-written draft sentence that said price and mix won back "about a third" of the volume loss. The script calculates **41%**.

## The seven steps

| # | Step | What happens | Evidence |
|---|---|---|---|
| 1 | New data? | Find the newest month in the public source. If it is already closed, stop and log it. | `sql/01`, `data/source_months.csv` |
| 2 | Quality gate | 8 checks on the month's order lines: missing fields, duplicates, unmapped categories, margin, row count, returns, pricing. | `sql/02`, `data/source_checks.csv` |
| 3 | Actual vs budget | 11 product families, split into volume, mix and price. | `sql/03`, `sql/04` |
| 4 | Calculation checks | 9 checks that every figure adds up and matches published figures. | `governance/checks.md` |
| 5 | Forecast | How accurate was last month's forecast? Re-forecast the rest of the year with BigQuery `AI.FORECAST`. | `sql/05` |
| 6 | Commentary | Summary and actions produced by the written rules below. | `dashboard/data.js` |
| 7 | Human approval | Pull request; the owner reviews and merges. | Git history |

All of steps 3–6 run in one script, `scripts/close.py` (Python standard library only).

## Back end: what to look at

| File | What it shows |
|---|---|
| [`governance/checks.md`](governance/checks.md) | Every check, its rule, the result and PASS / WARN / FAIL |
| [`governance/run_log.md`](governance/run_log.md) | Every query that ran, GB billed, rows returned, and input fingerprints |
| [`data/close_by_family.csv`](data/close_by_family.csv) | The calculated close by product family |

## Definitions

- **Volume effect** = (actual litres − budget litres) × budget price per litre
- **Price effect** = (actual price per litre − budget price per litre) × actual litres
- **Mix effect** (total only) = sum of family volume effects − total volume effect at the average budget price. It shows sales moving between cheaper and dearer families.
- **Trend landing** = year-to-date actual + rest-of-year budget × (year-to-date actual ÷ year-to-date budget)
- **Model landing** = year-to-date actual + `AI.FORECAST` for the remaining months (80% range shown)

## Commentary rules

The summary is not free text. Each sentence appears only when its rule is met:

| Sentence | Rule |
|---|---|
| "Volume explains the miss" | Volume effect is negative and larger than price + mix together |
| "The year-to-date gap is stable / widening / narrowing" | Change in year-to-date % vs budget compared with one month earlier (±0.5 points = stable) |
| "Likely timing, not a trend" | A family is ≥10% below budget this month but on or above budget year to date |
| "Is growing" | Sales and litres both up vs the same month last year |
| "Beat budget on price only" | Above budget, but the volume effect is negative |
| "The forecast model was accurate / missed" | Actual inside / outside last month's forecast range |

## Rerun

```bash
cd monthly-close/scripts
python close.py        # exit code 1 and no report data if any FAIL check fails
```

The same script runs on every push in GitHub Actions; the job also fails if `dashboard/data.js` was edited by hand.

## Cost, data and privacy

- **Cost:** 4.82 GB billed, inside BigQuery's free 1 TB a month. All queries were read-only.
- **Source:** Iowa Department of Revenue, *Iowa Liquor Sales*, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), read from Google BigQuery public datasets. Changes: grouped into 11 product families and aggregated by month. Budget, forecasts and analysis are my own.
- **No names:** no store, supplier or product names are kept or published.
- **Limit:** the public data ends at April 2026, so this run replays the April close. A scheduled monthly run would start at step 1 and stop when no new month is available.

This is an analysis of public data, not business advice.

---
Part of [experiments](../README.md) by [Evangelos Papanastasis](https://evanpapanast.github.io/portfolio/).
