-- C7 proof 2 — the star works: fact x dim_date x dim_technology reproducing one known
-- month (March 2024) split by the renewable flag.
-- Expected: exactly 2 rows (is_renewable 0/1), positive MWh totals on a 10^6 scale,
-- day_count 31 for both, and the derived share matching gold.mlv_monthly_renewables_share
-- for year=2024, month=3 (cross-checked by proof 3).
SELECT
    d.year,
    d.month,
    t.is_renewable,
    COUNT(DISTINCT d.date)          AS day_count,
    ROUND(SUM(f.generation_mwh), 3) AS generation_mwh
FROM gold.fact_generation_daily AS f
JOIN gold.dim_date AS d
    ON f.date = d.date
JOIN gold.dim_technology AS t
    ON f.technology = t.technology
WHERE d.year = 2024 AND d.month = 3
GROUP BY d.year, d.month, t.is_renewable
ORDER BY t.is_renewable;
