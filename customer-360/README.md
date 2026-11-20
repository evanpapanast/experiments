# Customer 360: which customers and channels drive profitable revenue

**[Open the interactive report →](https://evanpapanast.github.io/experiments/customer-360/dashboard/)**

A management report for an online fashion shop, built the way a commercial analytics team would:
**business question → free, legal data → GDPR-minimised model → checked insights.** Modelled in **dbt** on Google BigQuery.

> **Synthetic data.** TheLook is a fictional shop created by Google's Looker team. The figures show the method and the
> decisions, not a real market.

## The business question

> Which customer groups and channels create the most profitable revenue, and how should next year's marketing budget be split
> across channels to grow it?

Five report pages, last 24 months (20 Nov 2024 to 19 Nov 2026), customers shown only as groups:

1. **Overview:** revenue, margin, buyers, repeat rate, losses to cancellations and returns.
2. **Customer groups:** Champions, Loyal, New, At risk, One-time buyers, Lapsed, Never bought, plus region, age band and gender.
3. **Channels:** which channel each group prefers, where revenue comes from, visit-to-order rates, how customers first found the shop.
4. **Revenue vs cost:** from ordered value to gross margin, by channel and product category. Real costs only.
5. **Actions:** five actions sized with each group's own average order value (what-if slider).

## What we found

| | |
|---|---|
| **Two channels carry the business** | Email and Google Ads bring 75% of net revenue. Email alone is 45%, and 48% of buyers visit mostly through email. |
| **Channels differ in size, not quality** | All five channels earn 51.9% to 52.2% gross margin, convert 43.0% to 43.6% of visits to orders and bring the same repeat rate. |
| **Second orders are the growth pool** | Only 25% of buyers ordered more than once. 24,827 one-time buyers hold 43% of revenue. |
| **Cancellations cost more than returns** | 15% of ordered value was cancelled and 12% of shipped value returned: $1.47m that never became revenue. |
| **Half the base is dormant** | 46,408 of 89,819 registered adult customers did not buy in 24 months; most did not visit either. |

Marketing spend per channel is **not in the data**, so the report shows no marketing return or acquisition cost. That would be the
first thing to add with real data.

## How it works

```
bigquery-public-data.thelook_ecommerce (synthetic)
   └─► dbt staging        GDPR-minimised: allowed columns only, adults only, 24-month window
   └─► dbt intermediate   one internal row per customer ID → customer group and preferred channel (never published)
   └─► dbt marts          9 group-level report tables; cells under 50 customers suppressed
   └─► dbt tests          43 quality, privacy and reproducibility tests inside BigQuery (1 GB per-query cost cap)
   └─► extract ──► scripts/01  report data and plain-language insights ──► dashboard/
                   scripts/02  26 checks on the published files (GitHub Actions, with dbt parse and compile)
```

| Step | File |
|---|---|
| dbt project: models, macros, tests, cost cap | [`dbt/`](dbt/README.md) |
| Run plan for the BigQuery connector | `scripts/03_dbt_connector_plan.py` |
| Extract for the report | `sql/extract_for_report.sql` → `data/bigquery_extract.json` |
| BigQuery cost of every run | `data_quality/cost_log.md` |
| Report data, insights and actions | `scripts/01_build_report_data.py` → `data/*.csv`, `dashboard/data.js` |
| Quality gate on published files | `scripts/02_data_quality.py` → `data_quality/dq_report.md` |

Rerun the published part: `cd scripts && python 01_build_report_data.py && python 02_data_quality.py` (standard library only).

## Quality, privacy and governance

- **Reconciled:** 97,855 order lines and $4,378,159 of net revenue match the source exactly; segment, channel, category and
  monthly views agree with each other.
- **Checked twice:** 43 dbt tests in BigQuery and 26 checks on the published files; the second set runs on every change.
- **Reproducible:** the dbt rebuild found and fixed an arbitrary tie-break in "preferred channel"; 7 of 9 report tables are identical to the first version; in the other two, channel totals moved by at most 80 buyers (Email-preferred buyers 20,836 → 20,756).
- **Inside the free tier:** a full build and test run bills about 0.55 GB of the 1 TiB free each month; every query is capped at 1 GB.
- **GDPR by design:** only customer ID, age band, gender, region, first channel and sign-up month were copied; no names, e-mail,
  address, postal code, city, GPS, exact age, IP address or browser. Under-18s excluded. Only group totals of 50+ customers are published.
- See [DATA_GOVERNANCE.md](DATA_GOVERNANCE.md) and [DATA_DICTIONARY.md](DATA_DICTIONARY.md).

## Data source

TheLook eCommerce, `bigquery-public-data.thelook_ecommerce`, a fully synthetic dataset created by Google's Looker team and
offered in the Google BigQuery public datasets for product discovery, testing and evaluation. Only derived group totals are
published here. Independent analysis, not endorsed by Google.
