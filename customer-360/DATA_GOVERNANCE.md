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
  → customer_360.stg_customers     (89,819 adult customers, 6 allowed columns)
  → customer_360.stg_sessions      (226,241 visits in window, no IP / browser / place / page)
  → customer_360.stg_order_items   (97,855 order lines with product cost and purchase channel)
  → customer_360.customer_metrics  (internal: one row per customer ID → group and preferred channel)
  → customer_360.rpt_*             (group-level tables, small cells suppressed)
  → customer_360.qa_checks         (15 checks)
  → sql/05_extract.sql → data/bigquery_extract.json (SHA-256 in data/manifest.json)
  → scripts/01_build_report_data.py → data/*.csv, dashboard/data.js
  → scripts/02_data_quality.py → data_quality/dq_report.md (GitHub Actions on every change)
```

## 4. Method choices to know

- **Purchase channel:** the channel of the customer's purchase visit closest in time to the order, within 24 hours. All orders matched.
- **Preferred channel:** the channel of most of a customer's visits in the window (ties: most recent).
- **Net revenue** excludes cancelled and returned items; items still processing or shipped count as sold.
- **Currency:** the source does not state one; amounts are shown in $.
- **Partial months:** Nov 2024 (from the 20th) and Nov 2026 (to the 19th).

## 5. Change control

Every change goes through a branch and a pull request reviewed by the owner. The data-quality workflow must pass before merging.
