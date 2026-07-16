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

# Overridden by the calling pipeline's Notebook activity at runtime. The defaults
# are deliberately empty and invalid: an unparameterized run must fail loudly
# rather than write a wrong watermark, because a wrong watermark is silent.
p_indicator = ""
p_new_end = ""


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""Upsert one indicator's ingest watermark into ``bronze.ctl_watermark``.

The watermark records how far Bronze has been loaded per indicator. It is written
**only after a successful copy** — see the phase-B guide. Writing it earlier would
let a failed run advance the watermark, permanently skipping its window with no
error raised.

The table is written through Spark rather than the SQL analytics endpoint, which
is read-only over Lakehouse tables.
"""

import logging
from datetime import datetime, timezone

from delta.tables import DeltaTable
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import StringType, StructField, StructType, TimestampType

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("nb_update_watermark")

SCHEMA_NAME = "bronze"
TABLE_NAME = f"{SCHEMA_NAME}.ctl_watermark"

# Matches the window format the REE API takes and the pipelines pass around.
WATERMARK_FORMAT = "%Y-%m-%dT%H:%M"

WATERMARK_SCHEMA = StructType(
    [
        StructField("indicator", StringType(), nullable=False),
        StructField("last_end", StringType(), nullable=False),
        StructField("updated_at", TimestampType(), nullable=False),
    ]
)


def validate_parameters(indicator: str, new_end: str) -> None:
    """Reject malformed input before it reaches the table.

    Args:
        indicator: Indicator name, e.g. ``demanda_evolucion``.
        new_end: Window end to record, formatted as ``WATERMARK_FORMAT``.

    Raises:
        ValueError: If the indicator is blank or ``new_end`` is not parseable.
    """
    if not indicator.strip():
        raise ValueError("p_indicator must be a non-empty string")
    try:
        datetime.strptime(new_end, WATERMARK_FORMAT)
    except ValueError as exc:
        raise ValueError(
            f"p_new_end must match {WATERMARK_FORMAT!r}; got {new_end!r}"
        ) from exc


def ensure_watermark_table(session: SparkSession) -> None:
    """Create the bronze schema and watermark table if they do not exist yet.

    Idempotent: safe to call on every run, which is why the first real run is
    also what bootstraps the table.

    Args:
        session: Active Spark session.
    """
    session.sql(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}")
    session.sql(
        f"CREATE TABLE IF NOT EXISTS {TABLE_NAME} ("
        "  indicator STRING NOT NULL,"
        "  last_end STRING NOT NULL,"
        "  updated_at TIMESTAMP NOT NULL"
        ") USING DELTA"
    )


def build_watermark_row(session: SparkSession, indicator: str, new_end: str) -> DataFrame:
    """Build the single-row source DataFrame for the merge.

    Args:
        session: Active Spark session.
        indicator: Indicator name.
        new_end: Window end to record.

    Returns:
        A one-row DataFrame matching ``WATERMARK_SCHEMA``.
    """
    return session.createDataFrame(
        [(indicator, new_end, datetime.now(timezone.utc))], schema=WATERMARK_SCHEMA
    )


def upsert_watermark(session: SparkSession, indicator: str, new_end: str) -> None:
    """Insert or update this indicator's watermark row.

    Uses a Delta MERGE keyed on ``indicator`` so each indicator keeps exactly one
    row regardless of how many times this runs.

    Args:
        session: Active Spark session.
        indicator: Indicator name.
        new_end: Window end to record.
    """
    source = build_watermark_row(session, indicator, new_end)
    target = DeltaTable.forName(session, TABLE_NAME)
    (
        target.alias("t")
        .merge(source.alias("s"), "t.indicator = s.indicator")
        .whenMatchedUpdate(
            set={"last_end": "s.last_end", "updated_at": "s.updated_at"}
        )
        .whenNotMatchedInsertAll()
        .execute()
    )


# ``spark`` is injected into the notebook session by the Fabric runtime.
validate_parameters(p_indicator, p_new_end)  # noqa: F821
ensure_watermark_table(spark)  # noqa: F821
upsert_watermark(spark, p_indicator, p_new_end)  # noqa: F821
logger.info(
    "watermark updated: indicator=%s last_end=%s", p_indicator, p_new_end  # noqa: F821
)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
