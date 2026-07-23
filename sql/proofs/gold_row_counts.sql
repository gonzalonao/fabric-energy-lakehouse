-- C7 proof 1 — row counts of every Gold object, queried through the SQL analytics
-- endpoint (T-SQL over the Delta files in OneLake; read-only surface).
-- Expected (as of the 2026-07 build): dim_date 1826, dim_indicator 3, dim_technology 16
-- (16 distinct non-composite series across 2023-2026 - a single month shows fewer),
-- fact_demand_daily 1295, fact_generation_daily 19412, fact_price_hourly 102763,
-- mlv_monthly_avg_price ~86 (43 months x 2 series), mlv_monthly_renewables_share 43.
SELECT 'gold.dim_date' AS object_name, COUNT(*) AS row_count FROM gold.dim_date
UNION ALL
SELECT 'gold.dim_indicator', COUNT(*) FROM gold.dim_indicator
UNION ALL
SELECT 'gold.dim_technology', COUNT(*) FROM gold.dim_technology
UNION ALL
SELECT 'gold.fact_demand_daily', COUNT(*) FROM gold.fact_demand_daily
UNION ALL
SELECT 'gold.fact_generation_daily', COUNT(*) FROM gold.fact_generation_daily
UNION ALL
SELECT 'gold.fact_price_hourly', COUNT(*) FROM gold.fact_price_hourly
UNION ALL
SELECT 'gold.mlv_monthly_avg_price', COUNT(*) FROM gold.mlv_monthly_avg_price
UNION ALL
SELECT 'gold.mlv_monthly_renewables_share', COUNT(*) FROM gold.mlv_monthly_renewables_share
ORDER BY object_name;
