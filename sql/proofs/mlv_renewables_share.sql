-- C7 proof 3 — the materialized lake view serves from the endpoint like any table.
-- Expected: 12 rows (latest months first), renewables_share_pct strictly between 0 and
-- 100, renewable_mwh <= total_mwh on every row; the 2024-03 row must equal the derived
-- split from gold_star_join.sql (proof 2) - the MLV and the star agree.
SELECT TOP 12
    year,
    month,
    renewable_mwh,
    total_mwh,
    renewables_share_pct
FROM gold.mlv_monthly_renewables_share
ORDER BY year DESC, month DESC;
