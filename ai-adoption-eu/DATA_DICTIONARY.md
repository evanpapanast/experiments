# Data dictionary: AI adoption in EU enterprises

BigQuery dataset `ai_adoption` (project `project-57338774-2b06-4ac1-ba9`, location US).
The same tables exist as CSV files in [`data/`](data/). Star schema: two fact tables, four dimension tables.

## Fact tables

### `fact_ai_by_size`: AI indicators by enterprise size class
Source: Eurostat `isoc_eb_ai`. Grain: one row per **geo × year × size_class × indicator × unit**. 26,963 rows.

| Column | Type | Description | Allowed values / rule |
|---|---|---|---|
| `geo` | STRING | Country or aggregate code | Must exist in `dim_geo` (R01) |
| `year` | INT64 | Survey reference year | 2021, 2023, 2024, 2025 (V02). No AI module in 2022 |
| `size_class` | STRING | Enterprise size by persons employed | Must exist in `dim_size_class`. Main ones: `GE10` (10+), `10-49`, `50-249`, `GE250` |
| `indicator` | STRING | What is measured | Must exist in `dim_indicator` |
| `unit` | STRING | Denominator of the percentage | `PC_ENT` = % of all enterprises · `PC_ENT_AI_TANY` = % of enterprises using AI · `PC_ENT_AI_EC` = % of enterprises that considered AI but do not use it (V04) |
| `value` | FLOAT64 | The percentage | 0–100 (V01); never null (C02) |
| `flag` | STRING | Eurostat observation flag | null, or `b` break in series, `u` low reliability, `d` definition differs, `e` estimated, `p` provisional (V03). Currently only `b` (347 rows) |

### `fact_ai_by_sector`: AI indicators by economic activity
Source: Eurostat `isoc_eb_ain2`, enterprises with 10+ employees only. Grain: one row per **geo × year × nace × indicator**. 47,700 rows. Unit is always `PC_ENT`.

| Column | Type | Description | Allowed values / rule |
|---|---|---|---|
| `geo`, `year`, `indicator`, `value`, `flag` | | as above | as above (`flag` = `b` in 786 rows) |
| `nace` | STRING | Economic activity (NACE Rev. 2) | Must exist in `dim_sector`. Aggregates and sub-sectors overlap, so never sum across sectors |

## Dimension tables

| Table | Key | Columns | Rows | Notes |
|---|---|---|---|---|
| `dim_indicator` | `indicator` | `label` (Eurostat wording), `short_label` (used in charts), `indicator_group` | 31 | Groups: `headline`, `technology`, `purpose`, `barrier`, `sourcing` |
| `dim_geo` | `geo` | `label` | 36 | EU27, euro area, 27 member states, Norway and 6 candidate countries |
| `dim_sector` | `nace` | `label` | 50 | Eurostat NACE Rev. 2 labels |
| `dim_size_class` | `size_class` | `label` | 8 | |

## Control and audit tables

| Object | Type | Purpose |
|---|---|---|
| `load_control_totals` | table | Expected rows, value totals, source dates and SHA-256 per fact table, generated at extract time |
| `dq_catalog` | view | The rule book: check id, quality dimension, severity, rule text |
| `dq_failures` | view | One row per record that breaks a rule, with a readable description |
| `dq_results` | view | PASS / WARN / FAIL per rule |
| `dq_log` | table | Append-only history of every data quality run (`run_at`, `run_by`, `check_id`, `status`, `failed_rows`) |

## Reporting views (used by the report)

| View | Grain | Key measures |
|---|---|---|
| `mart_country_adoption` | geo × year | `pct_enterprises_using_ai`, `eu_rank` (members only), `change_pp_vs_previous` |
| `mart_size_gap` | geo × year | `pct_small`, `pct_medium`, `pct_large`, `gap_large_vs_small_pp` |
| `mart_ai_profile` | geo × year × indicator | Technologies (% of all), uses and sourcing (% of AI users), barriers (% of those who considered AI) |
| `mart_sector_adoption` | geo × year × sector | 19 curated, non-overlapping sectors with readable names |

## Business definitions

- **Enterprise uses AI** (`E_AI_TANY`): uses at least one of 8 AI technologies: text mining, speech recognition, generating text/speech/code, image recognition, machine learning for data analysis, workflow automation or decision support, autonomous machines, generating images/video/audio (the last one asked only from 2025, so earlier years cover 7 technologies).
- **pp (percentage points):** the arithmetic difference between two percentages (30% − 20% = 10 pp).
- **Size gap:** % of large enterprises using AI minus % of small enterprises.
- **Population:** enterprises with 10+ employees in NACE sections C to N excluding K (financial), plus group 95.1. Agriculture, mining and finance are not covered by the survey.
