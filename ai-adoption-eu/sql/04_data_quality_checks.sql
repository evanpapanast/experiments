-- =====================================================================
-- Data quality checks
-- ---------------------------------------------------------------------
-- dq_catalog   : the rule book (id, quality dimension, severity, rule)
-- dq_failures  : one row per record that breaks a rule (with a readable detail)
-- dq_results   : PASS / WARN / FAIL per rule
-- dq_log       : append-only audit trail of every run
--
-- Severity: FAIL = the data must not be published until fixed.
--           WARN = publish, but review (known source issue or unusual movement).
-- Portable SQL: runs on BigQuery and locally on SQLite (scripts/03_data_quality.py).
-- Tolerance 0.05 pp absorbs Eurostat's 2-decimal rounding.
-- =====================================================================

CREATE OR REPLACE VIEW `project-57338774-2b06-4ac1-ba9.ai_adoption.dq_catalog` AS
          SELECT 'C01' AS check_id, 'Completeness' AS dimension, 'FAIL' AS severity, 'Headline AI-use value exists for the EU and all 27 member states in every survey year' AS rule_text
UNION ALL SELECT 'C02', 'Completeness', 'FAIL', 'No missing keys or values in fact tables'
UNION ALL SELECT 'U01', 'Uniqueness',   'FAIL', 'One row per geo, year, size class, indicator and unit (fact_ai_by_size)'
UNION ALL SELECT 'U02', 'Uniqueness',   'FAIL', 'One row per geo, year, sector and indicator (fact_ai_by_sector)'
UNION ALL SELECT 'V01', 'Validity',     'FAIL', 'Every value is a percentage between 0 and 100'
UNION ALL SELECT 'V02', 'Validity',     'FAIL', 'Years are survey waves 2021, 2023, 2024 or 2025'
UNION ALL SELECT 'V03', 'Validity',     'FAIL', 'Eurostat flags are from the documented list (b, u, d, bu, e, p)'
UNION ALL SELECT 'V04', 'Validity',     'FAIL', 'Each indicator uses its correct denominator (unit)'
UNION ALL SELECT 'R01', 'Referential integrity', 'FAIL', 'Every indicator, country, sector and size class exists in its dimension table'
UNION ALL SELECT 'B01', 'Consistency',  'FAIL', 'Total (10+ employees) lies between the small, medium and large values'
UNION ALL SELECT 'B02', 'Consistency',  'FAIL', 'Share using any AI >= share using each single AI technology (by size)'
UNION ALL SELECT 'B03', 'Consistency',  'FAIL', 'Share using any AI <= sum of single technologies, where all are published'
UNION ALL SELECT 'B04', 'Consistency',  'FAIL', 'The two source datasets agree on the headline value (cross-dataset)'
UNION ALL SELECT 'B05', 'Consistency',  'WARN', 'Share using any AI >= share using each single AI technology (by sector)'
UNION ALL SELECT 'B06', 'Consistency',  'FAIL', 'EU average lies within the range of its member states'
UNION ALL SELECT 'A01', 'Plausibility', 'WARN', 'Year-on-year change in headline AI use larger than 12 pp (review)'
UNION ALL SELECT 'X01', 'Accuracy',     'FAIL', 'Loaded row counts and value totals match the extract control totals'
UNION ALL SELECT 'X02', 'Accuracy',     'FAIL', 'EU 2025 headline matches the 20.0% published by Eurostat'
UNION ALL SELECT 'F01', 'Timeliness',   'WARN', 'Source data is not older than the next scheduled Eurostat release';

CREATE OR REPLACE VIEW `project-57338774-2b06-4ac1-ba9.ai_adoption.dq_failures` AS
WITH
  s AS (SELECT * FROM `project-57338774-2b06-4ac1-ba9.ai_adoption.fact_ai_by_size`),
  n AS (SELECT * FROM `project-57338774-2b06-4ac1-ba9.ai_adoption.fact_ai_by_sector`),
  headline AS (SELECT geo, year, value FROM s WHERE indicator = 'E_AI_TANY' AND unit = 'PC_ENT' AND size_class = 'GE10'),
  members AS (
              SELECT 'BE' AS geo UNION ALL SELECT 'BG' UNION ALL SELECT 'CZ' UNION ALL SELECT 'DK' UNION ALL SELECT 'DE'
    UNION ALL SELECT 'EE' UNION ALL SELECT 'IE' UNION ALL SELECT 'EL' UNION ALL SELECT 'ES' UNION ALL SELECT 'FR'
    UNION ALL SELECT 'HR' UNION ALL SELECT 'IT' UNION ALL SELECT 'CY' UNION ALL SELECT 'LV' UNION ALL SELECT 'LT'
    UNION ALL SELECT 'LU' UNION ALL SELECT 'HU' UNION ALL SELECT 'MT' UNION ALL SELECT 'NL' UNION ALL SELECT 'AT'
    UNION ALL SELECT 'PL' UNION ALL SELECT 'PT' UNION ALL SELECT 'RO' UNION ALL SELECT 'SI' UNION ALL SELECT 'SK'
    UNION ALL SELECT 'FI' UNION ALL SELECT 'SE'),
  waves AS (SELECT 2021 AS year UNION ALL SELECT 2023 UNION ALL SELECT 2024 UNION ALL SELECT 2025),
  -- size classes side by side
  by_size AS (
    SELECT geo, year, indicator,
           MAX(CASE WHEN size_class = 'GE10'   THEN value END) AS total,
           MAX(CASE WHEN size_class = '10-49'  THEN value END) AS small,
           MAX(CASE WHEN size_class = '50-249' THEN value END) AS medium,
           MAX(CASE WHEN size_class = 'GE250'  THEN value END) AS large
    FROM s WHERE unit = 'PC_ENT' GROUP BY geo, year, indicator),
  -- any-AI next to the eight single technologies
  tech_s AS (
    SELECT geo, year, size_class,
           MAX(CASE WHEN indicator = 'E_AI_TANY' THEN value END) AS any_ai,
           MAX(CASE WHEN indicator <> 'E_AI_TANY' THEN value END) AS max_tech,
           SUM(CASE WHEN indicator <> 'E_AI_TANY' THEN value END) AS sum_tech,
           COUNT(CASE WHEN indicator <> 'E_AI_TANY' THEN value END) AS n_tech
    FROM s
    WHERE unit = 'PC_ENT' AND indicator IN ('E_AI_TANY', 'E_AI_TTM', 'E_AI_TSR', 'E_AI_TNLG', 'E_AI_TIR',
                                            'E_AI_TML', 'E_AI_TPA', 'E_AI_TAR', 'E_AI_TPVSG')
    GROUP BY geo, year, size_class),
  techs_per_wave AS (SELECT year, MAX(n_tech) AS n_expected FROM tech_s GROUP BY year),
  tech_n AS (
    SELECT geo, year, nace,
           MAX(CASE WHEN indicator = 'E_AI_TANY' THEN value END) AS any_ai,
           MAX(CASE WHEN indicator <> 'E_AI_TANY' THEN value END) AS max_tech
    FROM n GROUP BY geo, year, nace),
  yoy AS (
    SELECT h.geo, h.year, h.value,
           h.value - LAG(h.value) OVER (PARTITION BY h.geo ORDER BY h.year) AS chg
    FROM headline h),
  loaded AS (
              SELECT 'fact_ai_by_size' AS table_name, COUNT(*) AS n_rows, SUM(value) AS value_sum FROM s
    UNION ALL SELECT 'fact_ai_by_sector', COUNT(*), SUM(value) FROM n)

-- C01 completeness of the headline series
SELECT 'C01' AS check_id, g.geo || ' ' || CAST(w.year AS STRING) || ': headline value missing' AS detail
FROM (SELECT geo FROM members UNION ALL SELECT 'EU27_2020') g
CROSS JOIN waves w
LEFT JOIN headline h ON h.geo = g.geo AND h.year = w.year
WHERE h.value IS NULL

-- C02 nulls in keys or values
UNION ALL
SELECT 'C02', 'fact_ai_by_size: null in ' || geo FROM s
WHERE geo IS NULL OR year IS NULL OR size_class IS NULL OR indicator IS NULL OR unit IS NULL OR value IS NULL
UNION ALL
SELECT 'C02', 'fact_ai_by_sector: null in ' || geo FROM n
WHERE geo IS NULL OR year IS NULL OR nace IS NULL OR indicator IS NULL OR value IS NULL

-- U01 / U02 duplicate keys
UNION ALL
SELECT 'U01', geo || ' ' || CAST(year AS STRING) || ' ' || size_class || ' ' || indicator || ' ' || unit || ': ' || CAST(COUNT(*) AS STRING) || ' rows'
FROM s GROUP BY geo, year, size_class, indicator, unit HAVING COUNT(*) > 1
UNION ALL
SELECT 'U02', geo || ' ' || CAST(year AS STRING) || ' ' || nace || ' ' || indicator || ': ' || CAST(COUNT(*) AS STRING) || ' rows'
FROM n GROUP BY geo, year, nace, indicator HAVING COUNT(*) > 1

-- V01 range
UNION ALL
SELECT 'V01', 'size ' || geo || ' ' || CAST(year AS STRING) || ' ' || indicator || ' = ' || CAST(value AS STRING) FROM s WHERE value < 0 OR value > 100
UNION ALL
SELECT 'V01', 'sector ' || geo || ' ' || CAST(year AS STRING) || ' ' || indicator || ' = ' || CAST(value AS STRING) FROM n WHERE value < 0 OR value > 100

-- V02 survey waves
UNION ALL
SELECT 'V02', 'unexpected year ' || CAST(year AS STRING) FROM (SELECT year FROM s UNION ALL SELECT year FROM n) y
WHERE year NOT IN (2021, 2023, 2024, 2025)

-- V03 flags
UNION ALL
SELECT 'V03', 'unexpected flag ' || flag FROM (SELECT flag FROM s UNION ALL SELECT flag FROM n) f
WHERE flag IS NOT NULL AND flag NOT IN ('b', 'u', 'd', 'bu', 'e', 'p')

-- V04 denominator per indicator group
UNION ALL
SELECT 'V04', s.indicator || ' reported with unit ' || s.unit
FROM s JOIN `project-57338774-2b06-4ac1-ba9.ai_adoption.dim_indicator` i ON i.indicator = s.indicator
WHERE NOT (   s.unit = 'PC_ENT'
           OR (s.unit = 'PC_ENT_AI_TANY' AND i.indicator_group IN ('purpose', 'sourcing'))
           OR (s.unit = 'PC_ENT_AI_EC'   AND i.indicator_group = 'barrier'))

-- R01 referential integrity
UNION ALL
SELECT 'R01', 'unknown indicator ' || indicator FROM (SELECT indicator FROM s UNION ALL SELECT indicator FROM n) x
WHERE indicator NOT IN (SELECT indicator FROM `project-57338774-2b06-4ac1-ba9.ai_adoption.dim_indicator`)
UNION ALL
SELECT 'R01', 'unknown country ' || geo FROM (SELECT geo FROM s UNION ALL SELECT geo FROM n) x
WHERE geo NOT IN (SELECT geo FROM `project-57338774-2b06-4ac1-ba9.ai_adoption.dim_geo`)
UNION ALL
SELECT 'R01', 'unknown sector ' || nace FROM n
WHERE nace NOT IN (SELECT nace FROM `project-57338774-2b06-4ac1-ba9.ai_adoption.dim_sector`)
UNION ALL
SELECT 'R01', 'unknown size class ' || size_class FROM s
WHERE size_class NOT IN (SELECT size_class FROM `project-57338774-2b06-4ac1-ba9.ai_adoption.dim_size_class`)

-- B01 total between size classes
UNION ALL
SELECT 'B01', geo || ' ' || CAST(year AS STRING) || ' ' || indicator || ': total ' || CAST(total AS STRING) || ' outside size range'
FROM by_size
WHERE total IS NOT NULL AND small IS NOT NULL AND medium IS NOT NULL AND large IS NOT NULL
  AND (   total < (CASE WHEN small <= medium AND small <= large THEN small WHEN medium <= large THEN medium ELSE large END) - 0.05
       OR total > (CASE WHEN small >= medium AND small >= large THEN small WHEN medium >= large THEN medium ELSE large END) + 0.05)

-- B02 any >= each (by size)
UNION ALL
SELECT 'B02', geo || ' ' || CAST(year AS STRING) || ' ' || size_class || ': any AI ' || CAST(any_ai AS STRING) || ' < single technology ' || CAST(max_tech AS STRING)
FROM tech_s WHERE any_ai < max_tech - 0.05

-- B03 any <= sum of technologies (only where every technology is published)
UNION ALL
SELECT 'B03', t.geo || ' ' || CAST(t.year AS STRING) || ' ' || t.size_class || ': any AI ' || CAST(t.any_ai AS STRING) || ' > sum ' || CAST(t.sum_tech AS STRING)
FROM tech_s t JOIN techs_per_wave w ON w.year = t.year
WHERE t.n_tech = w.n_expected AND t.any_ai > t.sum_tech + 0.05

-- B04 cross-dataset agreement on the headline
UNION ALL
SELECT 'B04', h.geo || ' ' || CAST(h.year AS STRING) || ': size file ' || CAST(h.value AS STRING) || ' vs sector file ' || CAST(n.value AS STRING)
FROM headline h
JOIN n ON n.geo = h.geo AND n.year = h.year AND n.nace = 'C10-S951_X_K' AND n.indicator = 'E_AI_TANY'
WHERE ABS(h.value - n.value) > 0.01

-- B05 any >= each (by sector) - WARN: known Eurostat issue
UNION ALL
SELECT 'B05', geo || ' ' || CAST(year AS STRING) || ' sector ' || nace || ': any AI ' || CAST(any_ai AS STRING) || ' < single technology ' || CAST(max_tech AS STRING)
FROM tech_n WHERE any_ai < max_tech - 0.05

-- B06 EU average inside member-state range
UNION ALL
SELECT 'B06', 'EU ' || CAST(e.year AS STRING) || ' = ' || CAST(e.value AS STRING) || ' outside member range'
FROM headline e
JOIN (SELECT h.year, MIN(h.value) AS lo, MAX(h.value) AS hi FROM headline h JOIN members m ON m.geo = h.geo GROUP BY h.year) r
  ON r.year = e.year
WHERE e.geo = 'EU27_2020' AND (e.value < r.lo OR e.value > r.hi)

-- A01 unusually large year-on-year moves (review, not an error)
UNION ALL
SELECT 'A01', geo || ' ' || CAST(year AS STRING) || ': ' || CAST(ROUND(chg, 1) AS STRING) || ' pp vs previous wave'
FROM yoy WHERE ABS(chg) > 12

-- X01 control totals from the extract
UNION ALL
SELECT 'X01', c.table_name || ': loaded ' || CAST(COALESCE(l.n_rows, 0) AS STRING) || ' rows / '
       || CAST(ROUND(COALESCE(l.value_sum, 0), 2) AS STRING) || ', expected ' || CAST(c.expected_rows AS STRING)
       || ' / ' || CAST(c.expected_value_sum AS STRING)
FROM `project-57338774-2b06-4ac1-ba9.ai_adoption.load_control_totals` c
LEFT JOIN loaded l ON l.table_name = c.table_name
WHERE l.n_rows IS NULL OR l.n_rows <> c.expected_rows OR ABS(l.value_sum - c.expected_value_sum) > 0.01

-- X02 published headline
UNION ALL
SELECT 'X02', 'EU 2025 = ' || CAST(value AS STRING) || ', Eurostat published 20.0'
FROM headline WHERE geo = 'EU27_2020' AND year = 2025 AND ABS(value - 20.0) > 0.0501
UNION ALL
SELECT 'X02', 'EU 2025 headline missing' FROM (SELECT 1 AS one) d
WHERE NOT EXISTS (SELECT 1 FROM headline WHERE geo = 'EU27_2020' AND year = 2025)

-- F01 freshness
UNION ALL
SELECT 'F01', table_name || ': next Eurostat release was due ' || CAST(next_expected_update AS STRING) || ', refresh the extract'
FROM `project-57338774-2b06-4ac1-ba9.ai_adoption.load_control_totals`
WHERE CURRENT_DATE > next_expected_update;

CREATE OR REPLACE VIEW `project-57338774-2b06-4ac1-ba9.ai_adoption.dq_results` AS
SELECT c.check_id,
       c.dimension,
       c.severity,
       c.rule_text,
       COUNT(f.check_id) AS failed_rows,
       CASE WHEN COUNT(f.check_id) = 0 THEN 'PASS' ELSE c.severity END AS status
FROM `project-57338774-2b06-4ac1-ba9.ai_adoption.dq_catalog` c
LEFT JOIN `project-57338774-2b06-4ac1-ba9.ai_adoption.dq_failures` f ON f.check_id = c.check_id
GROUP BY c.check_id, c.dimension, c.severity, c.rule_text;

-- Audit trail: every run appends its results with a timestamp
CREATE TABLE IF NOT EXISTS `project-57338774-2b06-4ac1-ba9.ai_adoption.dq_log` (
  run_at TIMESTAMP, run_by STRING, check_id STRING, status STRING, failed_rows INT64);

INSERT INTO `project-57338774-2b06-4ac1-ba9.ai_adoption.dq_log` (run_at, run_by, check_id, status, failed_rows)
SELECT CURRENT_TIMESTAMP, 'bigquery', check_id, status, failed_rows
FROM `project-57338774-2b06-4ac1-ba9.ai_adoption.dq_results`;
