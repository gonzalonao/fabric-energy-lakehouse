# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "6cabfc1b-836e-43ad-9379-94fa8bdb6c16",
# META       "default_lakehouse_name": "lh_energy",
# META       "default_lakehouse_workspace_id": "476b58fd-19e3-4c0d-bde7-c3f16d2a6fcf",
# META       "known_lakehouses": [
# META         {
# META           "id": "6cabfc1b-836e-43ad-9379-94fa8bdb6c16"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

"""Declare the Gold materialized lake views (MLVs).

An MLV is defined once and refreshed by the lakehouse engine on its managed schedule —
declarative, unlike nb_gold_build's imperative rebuild. IF NOT EXISTS makes this
notebook an idempotent no-op after first creation; changing a definition requires
DROP MATERIALIZED LAKE VIEW first (recorded in the README's honest-MLV paragraph).

Requires the schema-enabled lakehouse chosen irreversibly at A3.
"""

import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("nb_gold_mlv")

# Monthly renewables share — the headline aggregate. is_renewable comes from
# dim_technology, i.e. from the API's own classification.
spark.sql(
    """
    CREATE MATERIALIZED LAKE VIEW IF NOT EXISTS gold.mlv_monthly_renewables_share
    AS
    SELECT
        year(f.date)  AS year,
        month(f.date) AS month,
        round(sum(CASE WHEN t.is_renewable THEN f.generation_mwh ELSE 0 END), 3)
            AS renewable_mwh,
        round(sum(f.generation_mwh), 3) AS total_mwh,
        round(
            100 * sum(CASE WHEN t.is_renewable THEN f.generation_mwh ELSE 0 END)
                / sum(f.generation_mwh),
            2
        ) AS renewables_share_pct
    FROM gold.fact_generation_daily f
    JOIN gold.dim_technology t USING (technology)
    GROUP BY year(f.date), month(f.date)
    """
)
logger.info("gold.mlv_monthly_renewables_share declared")

# Monthly average price per series. A plain AVG is grain-safe here: within any
# (series, month) the grain is homogeneous — PVPC is hourly throughout and spot
# switched to 15-min exactly at 2025-01-01, so no month mixes row weights.
spark.sql(
    """
    CREATE MATERIALIZED LAKE VIEW IF NOT EXISTS gold.mlv_monthly_avg_price
    AS
    SELECT
        year(date)  AS year,
        month(date) AS month,
        series,
        round(avg(price_eur_mwh), 2) AS avg_price_eur_mwh,
        count(*)    AS n_observations
    FROM gold.fact_price_hourly
    GROUP BY year(date), month(date), series
    """
)
logger.info("gold.mlv_monthly_avg_price declared")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
