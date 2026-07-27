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

"""Full rebuild of the Gold star schema: three dimensions, three facts.

Runs only downstream of a green DQ gate, so it can assume Silver is trustworthy and
stay purely declarative: every table is derived start-to-finish from Silver (or from
constants), overwritten atomically each run. No MERGE, no watermark — rebuilding a few
hundred thousand rows is cheaper than reasoning about incremental correctness in Gold.

Facts join dimensions on natural keys (date / technology / indicator): at this scale
surrogate keys buy no performance and would cost a lookup step, and Direct Lake models
(Phase E) relate on columns either way.
"""

import logging

from energy_lakehouse.indicators import INDICATORS

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("nb_gold_build")

GOLD_SCHEMA = "gold"

# Units confirmed by C4 profiling (docs/data-dictionary.md). The wheel's Indicator.unit
# is still None in 0.2.0 — a metadata-only bump isn't worth an env re-publish cycle;
# fold into the next batched wheel release.
UNITS = {
    "demanda_evolucion": "MWh",
    "generacion_estructura": "MWh",
    "precios_mercados": "EUR/MWh",
}
GRAINS = {
    "demanda_evolucion": "1 row per civil day (Europe/Madrid)",
    "generacion_estructura": "1 row per civil day x technology",
    "precios_mercados": "1 row per UTC instant x series (60-min; spot 15-min from 2025-01-01)",
}


def overwrite(table, df):
    """Full-rebuild write: overwrite data and schema (gold's schema follows the code)."""
    (
        df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(table)
    )
    logger.info("%s rebuilt: %d rows", table, spark.table(table).count())


spark.sql(f"CREATE SCHEMA IF NOT EXISTS {GOLD_SCHEMA}")

# dim_date bounds come from the loaded data, not from a hardcoded window. The calendar
# itself is still *generated* — every day between the bounds exists regardless of gaps in
# the facts — but a fixed end date (previously 2027-12-31) leaked empty future years into
# every consumer: an unselectable 2027 in the report's year slicer, and rolling-window
# measures averaging over days that hold no data. Rebuilding the bounds costs nothing here
# because gold is a full atomic rebuild on every run.
#
# MAX across all three indicators, deliberately. A fact row whose date has no dim_date row
# is orphaned — a broken relationship and blank rows in the report — so the dimension must
# reach the *furthest* fact. Note this is the opposite aggregation to the `Data Through`
# measure, which takes the EARLIEST of the same three dates: freshness must not hide one
# lagging indicator behind two current ones, whereas the calendar must not fall short of
# any of them. Same three numbers, two different jobs.
#
# The price bound reuses fact_price_hourly's civil-Madrid expression; to_date() on the raw
# UTC instant would misdate the last hours of a Madrid day and could truncate the calendar
# a day early, orphaning exactly the newest rows.
span = spark.sql(
    """
    SELECT min(d) AS start_date, max(d) AS end_date
    FROM (
        SELECT date AS d FROM silver.demand_daily
        UNION ALL
        SELECT date AS d FROM silver.generation_daily
        UNION ALL
        SELECT to_date(from_utc_timestamp(datetime_utc, 'Europe/Madrid')) AS d
        FROM silver.price_hourly
    )
    """
).first()

if span["start_date"] is None or span["end_date"] is None:
    raise ValueError(
        "Cannot build dim_date: no rows found in silver.demand_daily, "
        "silver.generation_daily or silver.price_hourly."
    )

DATE_START = span["start_date"].isoformat()
DATE_END = span["end_date"].isoformat()
logger.info("dim_date span derived from silver: %s -> %s", DATE_START, DATE_END)

# weekday(): 0 = Monday ... 6 = Sunday, so is_weekend = weekday >= 5.
dim_date = spark.sql(
    f"""
    SELECT
        d                     AS date,
        year(d)               AS year,
        month(d)              AS month,
        date_format(d, 'MMMM') AS month_name,
        quarter(d)            AS quarter,
        weekday(d)            AS day_of_week,
        weekday(d) >= 5       AS is_weekend
    FROM (
        SELECT explode(sequence(DATE'{DATE_START}', DATE'{DATE_END}', INTERVAL 1 DAY)) AS d
    )
    """
)
overwrite("gold.dim_date", dim_date)

# dim_technology — distinct technologies with the API's own renewable classification
# (carried through Silver from the payload, never inferred from names).
# renewable_label is the display form of is_renewable: a boolean legend reads "True"/
# "False", which is meaningless to a report consumer. Derived here rather than in DAX
# because Direct Lake supports no calculated columns.
dim_technology = spark.sql(
    """
    SELECT DISTINCT
        technology,
        is_renewable,
        CASE WHEN is_renewable THEN 'Renewable' ELSE 'Non-renewable' END
            AS renewable_label
    FROM silver.generation_daily
    """
)
overwrite("gold.dim_technology", dim_technology)

# dim_indicator — from the wheel's canonical INDICATORS (the C2 duplication collapse):
# one row per ingested series with its source path, grain and confirmed unit.
dim_indicator = spark.createDataFrame(
    [
        (ind.name, ind.path, ind.silver_table, GRAINS[ind.name], UNITS[ind.name])
        for ind in INDICATORS
    ],
    "indicator STRING, source_path STRING, silver_table STRING, grain STRING, unit STRING",
)
overwrite("gold.dim_indicator", dim_indicator)

# Facts — 1:1 projections of Silver with unit-suffixed measure names. is_renewable
# deliberately stays in dim_technology (star schema: attributes live on the dimension).
fact_demand = spark.sql(
    "SELECT date, value AS demand_mwh FROM silver.demand_daily"
)
overwrite("gold.fact_demand_daily", fact_demand)

fact_generation = spark.sql(
    "SELECT date, technology, value AS generation_mwh FROM silver.generation_daily"
)
overwrite("gold.fact_generation_daily", fact_generation)

# The price fact adds a civil-Madrid date so daily joins line up with the daily facts'
# grain — to_date(datetime_utc) alone would shift late-evening rows to the wrong day.
fact_price = spark.sql(
    """
    SELECT
        datetime_utc,
        to_date(from_utc_timestamp(datetime_utc, 'Europe/Madrid')) AS date,
        series,
        period_minutes,
        value AS price_eur_mwh
    FROM silver.price_hourly
    """
)
overwrite("gold.fact_price_hourly", fact_price)

logger.info("gold star schema rebuilt: 3 dims + 3 facts")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
