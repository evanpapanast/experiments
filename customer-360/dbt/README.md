# Customer 360 as a dbt project

The Customer 360 model, rebuilt in [dbt](https://www.getdbt.com/) on Google BigQuery: 13 models, 43 tests, one exposure
(the report). It produces the same group-level tables as the first, hand-written SQL version, with one bug fixed (see below).

## Structure

```
dbt/
├── dbt_project.yml        window dates, minimum group size, minimum age as vars; labels on every table
├── profiles.yml           BigQuery connection with a 1 GB per-query cost cap (no secrets)
├── macros/helpers.sql     revenue rules (net, shipped), channel names, small-cell suppression, window filter
├── models/
│   ├── staging/           stg_customers, stg_sessions, stg_order_items   (GDPR-minimised, adults only, 24 months)
│   ├── intermediate/      int_customer_metrics                            (one row per customer ID; never published)
│   └── marts/             9 rpt_* tables + exposure to the dashboard      (groups of 50+ only)
└── tests/                 8 singular tests + 2 custom generic tests (min_group_size, between)
```

```
source: bigquery-public-data.thelook_ecommerce
  stg_customers ──┬─► stg_sessions ──────┬─► int_customer_metrics ─► rpt_segments, rpt_segment_channel,
                  │                      │                           rpt_channel_acquisition, rpt_region_channel, rpt_demographics
                  └─► stg_order_items ───┴─► rpt_channel_purchase, rpt_monthly, rpt_category
                                  stg_sessions ─► rpt_funnel
```

## Tests (43, all passing)

| Kind | What it protects |
|---|---|
| Privacy | no personal-data column anywhere in the dataset; adults only; every published group has 50+ customers |
| Accuracy | order lines and net revenue reconcile exactly to the public source; group and channel views agree |
| Completeness | every customer sits in exactly one group; no missing keys |
| Reproducibility | the preferred channel is recomputed independently and must match |
| Integrity, uniqueness, validity | every order links to a customer and a purchase visit; no duplicates; allowed values only; dates inside the window |

## Cost control (free tier)

BigQuery gives **1 TiB of queries and 10 GiB of storage free per month**. This project is built to stay far inside both:

- **Hard cap:** `maximum_bytes_billed: 1000000000` in `profiles.yml` — any single query that would bill more than 1 GB fails instead of running.
- **Scan the public data once:** staging models are tables, so the large public tables are read once per build; everything downstream reads our small tables.
- **Tests in one query:** all 43 tests run as one combined query (BigQuery bills at least 10 MB per table per query, so 43 separate queries would cost more).
- **Dry runs first:** heavy models are dry-run before running to see the bytes they would bill.
- **Labels:** every table and job carries `project=customer-360`, so cost can be traced.
- **CI is free:** GitHub Actions only parses and compiles the project; it never touches BigQuery.

Measured on 2026-11-20 (see `../data_quality/cost_log.md`): a full build bills about **0.4 GB** and the tests **0.15 GB**,
about 0.05% of the monthly free queries. The dataset stores well under 50 MB of the 10 GiB free storage.

## How to run

With your own Google login (`gcloud auth application-default login`):

```bash
pip install dbt-core dbt-bigquery
cd customer-360/dbt
DBT_PROFILES_DIR=. dbt build          # builds all models and runs all tests, with the cost cap
DBT_PROFILES_DIR=. dbt docs generate  # optional: lineage and column docs
```

### How it was run here (no local Google login)

The build was run by Claude through the BigQuery connector, which has no local credentials. So:

1. `dbt compile --target offline` renders every model and test to SQL with a throw-away key that cannot reach BigQuery.
2. `../scripts/03_dbt_connector_plan.py` wraps each model in the same `CREATE OR REPLACE TABLE … AS` that dbt would run,
   in dependency order, and combines all tests into one query.
3. The connector runs those statements; the results are recorded in `../data_quality/cost_log.md`.

## What changed compared with the hand-written SQL

7 of the 9 report tables are **identical** to the first version (checked row by row with `EXCEPT DISTINCT`).
The two "preferred channel" tables changed slightly: the first version broke ties arbitrarily — 6,388 of 49,130 visiting
customers used two channels equally often on the same day — so a rerun could give different numbers. dbt now uses a strict
order (most visits, then most recent visit, then channel name), and a test checks it. Largest effect: buyers who prefer
email went from 20,836 to 20,756; every headline percentage in the report is unchanged.
