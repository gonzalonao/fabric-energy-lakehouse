-- One-off repair for the `Generación total` composite that was parsed as a technology.
--
-- WHERE THIS RUNS: a Spark notebook (`spark.sql`), NOT the SQL analytics endpoint.
-- The endpoint is a read-only projection over the Delta files; it can read these rows
-- but cannot delete them. Every write to a Lakehouse Delta table goes through a writer
-- engine. (A Fabric Warehouse would accept this DELETE over T-SQL; a Lakehouse does not.)
--
-- WHY A DELETE IS NEEDED AT ALL: `nb_bronze_to_silver` MERGEs on the natural key
-- (date, technology). Re-running it with the fixed parser stops *producing* composite
-- rows, but a MERGE never removes a row the new batch simply doesn't mention — the
-- existing ones would survive untouched. Gold needs no equivalent step: it is a full
-- atomic rebuild, so it self-heals as soon as silver is clean.
--
-- ORDER: (1) run this, (2) re-run `nb_gold_build`, (3) reframe `sm_energy`.
-- Run in dev and prod alike; both loaded the composite from the daily path.

-- 1. Confirm the damage before touching anything (expect ~26 rows/month affected,
--    only for months whose Bronze file was written by the daily month-to-date path).
SELECT technology, count(*) AS rows, min(date) AS first_date, max(date) AS last_date
FROM silver.generation_daily
WHERE technology = 'Generación total'
GROUP BY technology;

-- 2. Remove them.
DELETE FROM silver.generation_daily WHERE technology = 'Generación total';

-- 3. Verify: generation should track demand at ~1.1x on every loaded day, not ~2.3x.
--    This is the invariant the DQ gate now enforces as `ratio_band` (GEN_DEMAND band
--    [0.8, 1.6]) — the first check in the project that compares two indicators rather
--    than judging one table in isolation.
SELECT g.date, round(sum(g.value) / d.value, 2) AS gen_over_demand
FROM silver.generation_daily g
JOIN silver.demand_daily d ON d.date = g.date
WHERE g.date >= date_sub(current_date(), 40)
GROUP BY g.date, d.value
ORDER BY g.date;
