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

# PARAMETERS CELL ********************

# Overridden by the caller's Notebook activity at runtime. Empty fails validation on
# purpose: an unparameterized run must error rather than transform an unintended series.
p_indicator = ""


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""Parse one indicator's Bronze JSON files into its typed Silver Delta table.

Thin orchestration: the parse logic and the structural/semantic DQ boundary live in the
``energy_lakehouse`` wheel (published on ``env_energy``). This notebook only does the
Spark-side plumbing:

1. Glob the Bronze month files for ``p_indicator`` and strip Fabric's JsonSink BOM.
2. Run the matching typed parser; structural failures go to ``silver.quarantine``.
3. Upsert good rows through a natural-key Delta MERGE into the indicator's Silver table,
   so re-running the same slice is idempotent.
4. OPTIMIZE to keep the file count down.
"""

import json
import logging
from dataclasses import astuple
from datetime import datetime, timezone

from delta.tables import DeltaTable
from pyspark.sql import types as T

from energy_lakehouse.indicators import INDICATORS_BY_NAME
from energy_lakehouse.parsers import PARSERS

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("nb_bronze_to_silver")

SILVER_SCHEMA = "silver"
QUARANTINE_TABLE = "silver.quarantine"
# Fabric's JsonSink prepends a UTF-8 BOM to every Bronze file (Phase B finding); it must
# be stripped before json.loads, which rejects a leading BOM.
BOM = "﻿"

# Explicit output schemas so the field types (date vs timestamp) are never inferred and
# an empty batch still produces a well-typed table. Field order matches the dataclasses.
SILVER_TABLE_SCHEMAS = {
    "silver.demand_daily": T.StructType(
        [
            T.StructField("date", T.DateType(), False),
            T.StructField("value", T.DoubleType(), False),
        ]
    ),
    "silver.generation_daily": T.StructType(
        [
            T.StructField("date", T.DateType(), False),
            T.StructField("technology", T.StringType(), False),
            T.StructField("is_renewable", T.BooleanType(), False),
            T.StructField("value", T.DoubleType(), False),
        ]
    ),
    "silver.price_hourly": T.StructType(
        [
            T.StructField("datetime_utc", T.TimestampType(), False),
            T.StructField("series", T.StringType(), False),
            T.StructField("value", T.DoubleType(), False),
            T.StructField("period_minutes", T.IntegerType(), False),
        ]
    ),
}

QUARANTINE_TABLE_SCHEMA = T.StructType(
    [
        T.StructField("raw", T.StringType(), False),
        T.StructField("indicator", T.StringType(), False),
        T.StructField("reason", T.StringType(), False),
        T.StructField("loaded_at", T.TimestampType(), False),
    ]
)


def validate_indicator(name):
    """Return the indicator name if known, else raise ValueError."""
    if name not in PARSERS:
        raise ValueError(f"p_indicator must be one of {sorted(PARSERS)}; got {name!r}")
    return name


def read_raw_payloads(indicator):
    """Read and JSON-decode every Bronze month file for an indicator.

    Uses wholetext so each month file stays one record, and strips the JsonSink BOM.
    The payloads are small (a few KB each, tens per indicator), so collecting them to
    the driver to hand to the pure Python parser is safe.
    """
    glob = f"Files/raw/{indicator}/*/*/*.json"
    # wholetext must be text()'s keyword: .option("wholetext", True) is silently
    # clobbered by text()'s own wholetext=False default. Latent while every JsonSink
    # file was single-line; C5's first multi-line file split into per-line rows.
    frame = spark.read.text(glob, wholetext=True)
    return [json.loads(row["value"].lstrip(BOM)) for row in frame.collect()]


def parse_all(indicator):
    """Parse every Bronze file, returning (good rows, quarantined records)."""
    parser = PARSERS[indicator]
    rows = []
    quarantine = []
    for payload in read_raw_payloads(indicator):
        batch = parser(payload)
        rows.extend(batch.rows)
        quarantine.extend(batch.quarantined)
    logger.info("%s: %d rows, %d quarantined", indicator, len(rows), len(quarantine))
    return rows, quarantine


def upsert(table, rows, schema, natural_key):
    """MERGE rows into a Silver Delta table on its natural key (idempotent re-runs)."""
    data = [astuple(r) for r in rows]
    df = spark.createDataFrame(data, schema).dropDuplicates(list(natural_key))
    if not spark.catalog.tableExists(table):
        df.write.format("delta").saveAsTable(table)
        return
    condition = " AND ".join(f"t.{key} = s.{key}" for key in natural_key)
    (
        DeltaTable.forName(spark, table)
        .alias("t")
        .merge(df.alias("s"), condition)
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )


def write_quarantine(records):
    """Append quarantined records (never drop them silently)."""
    if not records:
        return
    loaded_at = datetime.now(timezone.utc)
    data = [(r.raw, r.indicator, r.reason, loaded_at) for r in records]
    frame = spark.createDataFrame(data, QUARANTINE_TABLE_SCHEMA)
    frame.write.format("delta").mode("append").saveAsTable(QUARANTINE_TABLE)


indicator = validate_indicator(p_indicator)
meta = INDICATORS_BY_NAME[indicator]
rows, quarantine = parse_all(indicator)

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SILVER_SCHEMA}")
write_quarantine(quarantine)
if rows:
    upsert(meta.silver_table, rows, SILVER_TABLE_SCHEMAS[meta.silver_table], meta.natural_key)
    spark.sql(f"OPTIMIZE {meta.silver_table}")
logger.info("%s -> %s complete", indicator, meta.silver_table)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
