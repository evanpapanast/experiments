-- Dataset and tables for the EU AI-adoption experiment (location: US multi-region, same as Google's public datasets)
CREATE SCHEMA IF NOT EXISTS `project-57338774-2b06-4ac1-ba9.ai_adoption`
  OPTIONS (location = 'US', description = 'Eurostat AI use in enterprises (isoc_eb_ai, isoc_eb_ain2)');

CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.ai_adoption.fact_ai_by_size` (
  geo STRING, year INT64, size_class STRING, indicator STRING, unit STRING, value FLOAT64, flag STRING);

CREATE OR REPLACE TABLE `project-57338774-2b06-4ac1-ba9.ai_adoption.fact_ai_by_sector` (
  geo STRING, year INT64, nace STRING, indicator STRING, value FLOAT64, flag STRING);
