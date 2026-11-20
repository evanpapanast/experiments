# Data governance: Customer 360

How the data is sourced, protected, checked and changed.

## 1. Source and terms

| Item | Value |
|---|---|
| Dataset | TheLook eCommerce: customers, products, orders, order lines, inventory and website events of a fictional online fashion shop |
| Publisher | Google (Looker team), via the Google BigQuery public datasets |
| Nature | **Fully synthetic.** Programmatically generated; it describes no real people or companies |
| Read from | `bigquery-public-data.thelook_ecommerce` |
| Terms | Offered to practitioners for product discovery, testing and evaluation. No separate open-data licence is published for it. |
| How we use it | Only derived group totals are published, the source is credited, and the report states that the data is synthetic |
| Snapshot | The source adds new rows every day; the analysis is frozen at 19 Nov 2026 (window 20 Nov 2024 to 19 Nov 2026) |

## 2. Privacy and data minimisation (applied as if the data were real)

The source holds fields that would be personal data for a real shop: first and last name, e-mail, street address, postal code,
city, state, latitude/longitude, exact age, and for web visits the IP address, browser and page addresses.

| Rule | How it is enforced |
|---|---|
| **Minimisation:** copy only what the question needs | `sql/01` copies customer ID, age band, gender, region, first channel, sign-up month. BigQuery check: no forbidden column exists anywhere in the dataset |
| **No children's data** (GDPR Art. 8) | Customers under 18 are excluded. BigQuery check: customer count equals the source count of adults |
| **No re-identification through small places** | Country is replaced by four regions |
| **Group totals only** | Row-level IDs stay in BigQuery (`customer_metrics`), never in files or the report. Gate check: no ID columns published |
| **Minimum group size 50** | Smaller cells are set to empty (2 cells). BigQuery and gate checks fail on any group under 50 |
| **No invented data** | Marketing spend is not in the source, so no return-on-spend or acquisition-cost figures are shown. Gate check fails if such metrics appear |
| **No tracking** | The report loads no external scripts. Gate check fails otherwise |

## 3. Lineage

```
bigquery-public-data.thelook_ecommerce.{users, events, orders, order_items, inventory_items, products}
  → dbt: customer_360_dbt.stg_customers      (89,819 adult customers, 6 allowed columns)
  → dbt: customer_360_dbt.stg_sessions       (226,241 visits in window, no IP / browser / place / page)
  → dbt: customer_360_dbt.stg_order_items    (97,855 order lines with product cost and purchase channel)
  → dbt: customer_360_dbt.int_customer_metrics (internal: one row per customer ID → group and preferred channel)
  → dbt: customer_360_dbt.rpt_*              (group-level tables, small cells suppressed)
  → dbt test                                 (43 tests)
  → sql/extract_for_report.sql → data/bigquery_extract.json (SHA-256 in data/manifest.json)
  → scripts/01_build_report_data.py → data/*.csv, dashboard/data.js
  → scripts/02_data_quality.py → data_quality/dq_report.md (GitHub Actions on every change)
```

## 4. Method choices to know

- **Purchase channel:** the channel of the customer's purchase visit closest in time to the order, within 24 hours. All orders matched.
- **Preferred channel:** the channel of most of a customer's visits in the window; ties go to the most recent visit, then channel name, so every run gives the same answer.
- **Net revenue** excludes cancelled and returned items; items still processing or shipped count as sold.
- **Currency:** the source does not state one; amounts are shown in $.
- **Partial months:** Nov 2024 (from the 20th) and Nov 2026 (to the 19th).

## 5. Cost control

BigQuery's free tier is 1 TiB of queries and 10 GiB of storage per month. Every dbt query is capped at 1 GB billed
(`maximum_bytes_billed`), heavy models are dry-run first, public tables are read once per build, tests run as one query,
and CI never queries BigQuery. Every run is recorded in `data_quality/cost_log.md`.

## 6. Change log

| Date | Change |
|---|---|
| 2026-11-20 | First version in hand-written SQL, 15 checks. |
| 2026-11-20 | Rebuilt as a dbt project with 43 tests. Fixed an arbitrary tie-break in "preferred channel" (6,388 of 49,130 visiting customers had a tie); 7 of 9 report tables unchanged; in the 2 preferred-channel tables, channel totals moved by at most 80 buyers and small cells by a few customers (e.g. Champions preferring YouTube 104 → 112). Old dataset `customer_360` kept for comparison. |

## 7. Change control

Every change goes through a branch and a pull request reviewed by the owner. The data-quality workflow must pass before merging.
