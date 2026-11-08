-- =====================================================================
-- Reporting views ("marts") that feed the dashboard.
-- Written in portable SQL: runs on BigQuery, and locally on SQLite via
-- scripts/02_build_marts.py (which strips the project/dataset prefix).
-- Scope: enterprises with 10+ employees (size_class = 'GE10') unless stated.
-- =====================================================================

-- 1. Headline adoption by country and year, with EU rank and change ----
CREATE OR REPLACE VIEW `project-57338774-2b06-4ac1-ba9.ai_adoption.mart_country_adoption` AS
WITH base AS (
  SELECT f.geo,
         g.label AS country,
         CASE WHEN f.geo IN ('EU27_2020', 'EA', 'NO', 'BA', 'ME', 'MK', 'AL', 'RS', 'TR')
              THEN 0 ELSE 1 END AS is_eu_member,
         f.year,
         f.value AS pct_enterprises_using_ai,
         f.flag
  FROM `project-57338774-2b06-4ac1-ba9.ai_adoption.fact_ai_by_size` f
  JOIN `project-57338774-2b06-4ac1-ba9.ai_adoption.dim_geo` g ON g.geo = f.geo
  WHERE f.indicator = 'E_AI_TANY' AND f.unit = 'PC_ENT' AND f.size_class = 'GE10'
)
SELECT b.*,
       CASE WHEN is_eu_member = 1
            THEN RANK() OVER (PARTITION BY year, is_eu_member ORDER BY pct_enterprises_using_ai DESC)
       END AS eu_rank,
       ROUND(pct_enterprises_using_ai
             - LAG(pct_enterprises_using_ai) OVER (PARTITION BY geo ORDER BY year), 2) AS change_pp_vs_previous
FROM base b;

-- 2. Size gap: small (10-49) vs medium (50-249) vs large (250+) firms --
CREATE OR REPLACE VIEW `project-57338774-2b06-4ac1-ba9.ai_adoption.mart_size_gap` AS
SELECT f.geo,
       f.year,
       MAX(CASE WHEN f.size_class = '10-49'  THEN f.value END) AS pct_small,
       MAX(CASE WHEN f.size_class = '50-249' THEN f.value END) AS pct_medium,
       MAX(CASE WHEN f.size_class = 'GE250'  THEN f.value END) AS pct_large,
       ROUND(MAX(CASE WHEN f.size_class = 'GE250' THEN f.value END)
           - MAX(CASE WHEN f.size_class = '10-49' THEN f.value END), 2) AS gap_large_vs_small_pp
FROM `project-57338774-2b06-4ac1-ba9.ai_adoption.fact_ai_by_size` f
WHERE f.indicator = 'E_AI_TANY' AND f.unit = 'PC_ENT'
GROUP BY f.geo, f.year;

-- 3. Technologies, purposes, barriers and sourcing in one long table --
--    unit tells the denominator:
--      PC_ENT          % of all enterprises            (technologies)
--      PC_ENT_AI_TANY  % of enterprises that use AI    (purposes, sourcing)
--      PC_ENT_AI_EC    % of enterprises that considered AI but do not use it (barriers)
CREATE OR REPLACE VIEW `project-57338774-2b06-4ac1-ba9.ai_adoption.mart_ai_profile` AS
SELECT f.geo,
       f.year,
       i.indicator_group,
       f.indicator,
       i.short_label,
       f.unit,
       f.value,
       f.flag
FROM `project-57338774-2b06-4ac1-ba9.ai_adoption.fact_ai_by_size` f
JOIN `project-57338774-2b06-4ac1-ba9.ai_adoption.dim_indicator` i ON i.indicator = f.indicator
WHERE f.size_class = 'GE10'
  AND (   (i.indicator_group = 'technology'                AND f.unit = 'PC_ENT')
       OR (i.indicator_group IN ('purpose', 'sourcing')    AND f.unit = 'PC_ENT_AI_TANY')
       OR (i.indicator_group = 'barrier'                   AND f.unit = 'PC_ENT_AI_EC'));

-- 4. Adoption by economic sector (curated, non-overlapping list) -------
CREATE OR REPLACE VIEW `project-57338774-2b06-4ac1-ba9.ai_adoption.mart_sector_adoption` AS
SELECT f.geo,
       f.year,
       f.nace,
       CASE f.nace
         WHEN 'J62_J63' THEN 'IT services & programming'
         WHEN 'J58-J60' THEN 'Publishing & media'
         WHEN 'J61'     THEN 'Telecommunications'
         WHEN 'M72'     THEN 'Scientific R&D'
         WHEN 'M73-M75' THEN 'Advertising & market research'
         WHEN 'M69-M71' THEN 'Legal, accounting & consulting'
         WHEN 'C21'     THEN 'Pharmaceuticals'
         WHEN 'C26'     THEN 'Computers & electronics'
         WHEN 'D'       THEN 'Energy supply'
         WHEN 'L'       THEN 'Real estate'
         WHEN 'C29_C30' THEN 'Motor vehicles & transport equipment'
         WHEN 'G46'     THEN 'Wholesale trade'
         WHEN 'N'       THEN 'Administrative & support services'
         WHEN 'G47'     THEN 'Retail trade'
         WHEN 'E'       THEN 'Water & waste management'
         WHEN 'C10-C12' THEN 'Food & beverages manufacturing'
         WHEN 'I'       THEN 'Accommodation & food services'
         WHEN 'H'       THEN 'Transport & storage'
         WHEN 'F'       THEN 'Construction'
       END AS sector,
       f.indicator,
       f.value,
       f.flag
FROM `project-57338774-2b06-4ac1-ba9.ai_adoption.fact_ai_by_sector` f
WHERE f.nace IN ('J62_J63', 'J58-J60', 'J61', 'M72', 'M73-M75', 'M69-M71', 'C21', 'C26', 'D', 'L',
                 'C29_C30', 'G46', 'N', 'G47', 'E', 'C10-C12', 'I', 'H', 'F');
