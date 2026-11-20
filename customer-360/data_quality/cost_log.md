# BigQuery cost log: Customer 360

Free tier: 1 TiB of queries and 10 GiB of storage per month. Every query below ran under a 1 GB per-query cap.
"Billed" is what counts against the free tier (BigQuery bills at least 10 MB per table referenced).

## Before the dbt rebuild

| When | Item | Value |
|---|---|---|
| 2026-11-20 | Queries billed in the project so far this month (all experiments) | 75.75 GiB of 1,024 GiB (7.4%) |
| 2026-11-20 | Storage, all experiment datasets | about 41 MiB of 10 GiB |

## dbt rebuild, 2026-11-20

| Step | Bytes billed |
|---|---|
| Dry runs of the heavy models (stg_order_items 93 MB, stg_sessions 164 MB, stg_customers 5 MB processed) | 0 (dry runs are free) |
| First build: all 13 models | 405 MB |
| 42 tests in one query | 147 MB |
| Parity check against the hand-written version | 189 MB |
| Tie-break investigation | 147 MB |
| Rebuild after the tie-break fix (12 models; stg_customers unchanged) | 394 MB |
| 43 tests in one query | 147 MB |
| Parity check and extract | 178 MB |
| **Total for the rebuild** | **about 1.6 GB (0.16% of the monthly free 1 TiB)** |

A normal rebuild from now on is one build plus one test query: about 0.55 GB.
