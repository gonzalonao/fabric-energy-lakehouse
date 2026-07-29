"""The write-then-raise data-quality gate.

``run_gate`` runs every check for a stage, writes **all** results to ``ops.dq_results``,
and only then raises if any failed. Writing before raising is the whole point: a failed
run leaves a complete, queryable record of what passed and failed, so the failure is
diagnosable from a table rather than reconstructed from a stack trace.

This is the only Spark-touching module in the package. It computes the scalar inputs
(counts, max dates) with Spark aggregations, hands them to the pure functions in
:mod:`energy_lakehouse.dq.checks`, and serializes the verdicts. The threshold logic
itself lives in those pure functions and is unit-tested without a cluster.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from ..models import DQResult, DQStatus
from . import checks

if TYPE_CHECKING:
    from pyspark.sql import SparkSession  # type: ignore[import-not-found]

OPS_TABLE = "ops.dq_results"
OPS_SCHEMA = "ops"

STAGE_SILVER = "silver"
VALID_STAGES = (STAGE_SILVER,)

# Value-range bounds (see the C2 check config). Demand must be strictly positive; the
# spot/PVPC price sits in a wide but bounded band in €/MWh.
PRICE_MIN = -500.0
PRICE_MAX = 4000.0
# Generation: a renewable technology can never be physically negative, so any negative
# renewable value is an error. A thermal (non-renewable) technology can dip slightly
# negative on near-idle days (station self-consumption net of output) — real REE data,
# observed only for coal at min ~-120 MWh over 3.5 years. We allow that small tolerance
# for non-renewables and only treat a gross negative as corruption.
GENERATION_MIN = -1000.0
FRESHNESS_MAX_LAG_DAYS = 1

# Daily generation over daily demand. Peninsular Spain generates a little more than it
# consumes (net exports plus losses); observed 1.10-1.17 across the loaded history. The
# band is deliberately wide — it exists to catch structural breakage, not to police
# weather. A doubling (2.29, when the `Generación total` composite was parsed as a
# technology) is far outside it; so is a collapse from a partially-loaded day.
GEN_DEMAND_MIN = 0.8
GEN_DEMAND_MAX = 1.6
GEN_DEMAND_LABEL = "generation/demand"

_ROW_COUNT_CHECK = "row_count"


class RangeCheck:
    """A value-range check: the bounds for the message and the SQL for the bad rows."""

    def __init__(self, column: str, low: float, high: float, bad_row_sql: str) -> None:
        """Store the column, its inclusive bounds, and the bad-row predicate."""
        self.column = column
        self.low = low
        self.high = high
        self.bad_row_sql = bad_row_sql


# Per-table check configuration for the silver stage.
_SILVER_TABLES = (
    "silver.demand_daily",
    "silver.generation_daily",
    "silver.price_hourly",
)

_SILVER_RANGE = {
    "silver.demand_daily": RangeCheck("value", 0.0, float("inf"), "value <= 0"),
    "silver.generation_daily": RangeCheck(
        "value",
        GENERATION_MIN,
        float("inf"),
        # Renewables strict; thermal tolerant of a small self-consumption negative.
        f"(is_renewable AND value < 0) OR value < {GENERATION_MIN}",
    ),
    "silver.price_hourly": RangeCheck(
        "value", PRICE_MIN, PRICE_MAX, f"value < {PRICE_MIN} OR value > {PRICE_MAX}"
    ),
}

_SILVER_KEY_COLUMNS = {
    "silver.demand_daily": ("date", "value"),
    "silver.generation_daily": ("date", "technology", "value"),
    "silver.price_hourly": ("datetime_utc", "series", "value"),
}

_SILVER_DATE_EXPR = {
    "silver.demand_daily": "date",
    "silver.generation_daily": "date",
    "silver.price_hourly": "to_date(datetime_utc)",
}


class DQGateError(RuntimeError):
    """Raised when one or more checks fail, after all results have been persisted."""

    def __init__(self, failures: list[DQResult]) -> None:
        """Build a readable summary listing every failed check."""
        self.failures = failures
        summary = "; ".join(
            f"{r.table}.{r.column or '*'} {r.check}: {r.details}" for r in failures
        )
        super().__init__(f"DQ gate failed ({len(failures)} check(s)): {summary}")


def validate_stage(stage: str) -> str:
    """Return ``stage`` if it is a known stage, else raise ``ValueError``."""
    if stage not in VALID_STAGES:
        raise ValueError(f"stage must be one of {VALID_STAGES}; got {stage!r}")
    return stage


def failures(results: list[DQResult]) -> list[DQResult]:
    """Return only the failing results — the pure decision the gate raises on."""
    return [r for r in results if r.status is DQStatus.FAIL]


def _yesterday_utc() -> date:
    """Return yesterday's UTC date, the freshness floor."""
    return datetime.now(UTC).date() - timedelta(days=FRESHNESS_MAX_LAG_DAYS)


def _scalar(spark: SparkSession, query: str, column: str) -> Any:
    """Run a one-row aggregation and return a single cell (dynamically typed)."""
    return spark.sql(query).collect()[0][column]


def _count_where(spark: SparkSession, table: str, predicate: str) -> int:
    """Count rows in ``table`` matching ``predicate``."""
    query = f"SELECT count(*) AS c FROM {table} WHERE {predicate}"
    return int(_scalar(spark, query, "c"))


def _row_count(spark: SparkSession, table: str) -> int:
    """Count all rows in ``table``."""
    return int(_scalar(spark, f"SELECT count(*) AS c FROM {table}", "c"))


def _max_date(spark: SparkSession, table: str, date_expr: str) -> date | None:
    """Return the latest date in ``table`` under ``date_expr``, or ``None`` if empty."""
    value = _scalar(spark, f"SELECT max({date_expr}) AS m FROM {table}", "m")
    return value if isinstance(value, date) else None


def _previous_row_count(spark: SparkSession, table: str) -> int:
    """Return the last recorded row count for ``table`` from ``ops.dq_results``.

    The baseline is stored as an informational ``row_count`` result each run, so the
    delta check has a prior value without a separate state table. Zero if none exists.
    """
    if not spark.catalog.tableExists(OPS_TABLE):
        return 0
    rows = spark.sql(
        f"SELECT observed FROM {OPS_TABLE} "
        f"WHERE `table` = '{table}' AND check = '{_ROW_COUNT_CHECK}' "
        "ORDER BY run_ts DESC LIMIT 1"
    ).collect()
    return int(rows[0]["observed"]) if rows else 0


def _row_count_info(table: str, count: int) -> DQResult:
    """An informational (always-PASS) result recording a table's current row count."""
    return DQResult(
        check=_ROW_COUNT_CHECK,
        table=table,
        status=DQStatus.PASS,
        observed=float(count),
        threshold=0.0,
        details=f"row count = {count}",
    )


def _gen_demand_ratio(spark: SparkSession) -> tuple[int, float | None]:
    """Return (days outside the band, the ratio furthest outside it).

    Compares the two indicators only on dates present in *both*, so a day loaded for one
    and not yet the other is out of scope rather than a false alarm.
    """
    daily = (
        "SELECT g.date AS date, sum(g.value) / d.value AS ratio "
        "FROM silver.generation_daily g "
        "JOIN silver.demand_daily d ON d.date = g.date "
        "WHERE d.value > 0 "
        "GROUP BY g.date, d.value"
    )
    row = spark.sql(
        "SELECT "
        f"  sum(CASE WHEN ratio < {GEN_DEMAND_MIN} OR ratio > {GEN_DEMAND_MAX} "
        "       THEN 1 ELSE 0 END) AS bad, "
        f"  max(CASE WHEN ratio > {GEN_DEMAND_MAX} THEN ratio END) AS hi, "
        f"  min(CASE WHEN ratio < {GEN_DEMAND_MIN} THEN ratio END) AS lo "
        f"FROM ({daily})"
    ).collect()[0]
    bad = int(row["bad"] or 0)
    extreme = row["hi"] if row["hi"] is not None else row["lo"]
    return bad, float(extreme) if extreme is not None else None


def collect_silver_results(spark: SparkSession) -> list[DQResult]:
    """Run every silver-stage check and return the verdicts (no writing, no raising)."""
    results: list[DQResult] = []
    floor = _yesterday_utc()
    for table in _SILVER_TABLES:
        current = _row_count(spark, table)
        previous = _previous_row_count(spark, table)
        results.append(_row_count_info(table, current))
        results.append(
            checks.row_count_delta(table=table, current=current, previous=previous)
        )
        for column in _SILVER_KEY_COLUMNS[table]:
            results.append(
                checks.null_pct(
                    table=table,
                    column=column,
                    null_count=_count_where(spark, table, f"{column} IS NULL"),
                    total_count=current,
                )
            )
        rng = _SILVER_RANGE[table]
        results.append(
            checks.value_range(
                table=table,
                column=rng.column,
                out_of_range_count=_count_where(spark, table, rng.bad_row_sql),
                low=rng.low,
                high=rng.high,
            )
        )
        results.append(
            checks.freshness(
                table=table,
                max_date=_max_date(spark, table, _SILVER_DATE_EXPR[table]),
                min_expected=floor,
            )
        )
    # Cross-indicator: the only check here that compares two tables. Everything above
    # judges a table in isolation, which is why a doubled generation total passed 20/20.
    out_of_band, extreme = _gen_demand_ratio(spark)
    results.append(
        checks.ratio_band(
            table="silver.generation_daily",
            column=GEN_DEMAND_LABEL,
            out_of_band_days=out_of_band,
            extreme=extreme,
            low=GEN_DEMAND_MIN,
            high=GEN_DEMAND_MAX,
        )
    )
    return results


def _write_results(spark: SparkSession, stage: str, results: list[DQResult]) -> None:
    """Append every result to ``ops.dq_results``, stamped with run time and stage."""
    from pyspark.sql import types as t  # Fabric-runtime-only import

    schema = t.StructType(
        [
            t.StructField("run_ts", t.TimestampType(), False),
            t.StructField("stage", t.StringType(), False),
            t.StructField("check", t.StringType(), False),
            t.StructField("table", t.StringType(), False),
            t.StructField("column", t.StringType(), True),
            t.StructField("status", t.StringType(), False),
            t.StructField("observed", t.DoubleType(), False),
            t.StructField("threshold", t.DoubleType(), False),
            t.StructField("details", t.StringType(), False),
        ]
    )
    run_ts = datetime.now(UTC)
    rows = [
        (
            run_ts,
            stage,
            r.check,
            r.table,
            r.column,
            str(r.status),
            r.observed,
            r.threshold,
            r.details,
        )
        for r in results
    ]
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {OPS_SCHEMA}")
    frame = spark.createDataFrame(rows, schema)
    frame.write.format("delta").mode("append").saveAsTable(OPS_TABLE)


def run_gate(stage: str, spark: SparkSession) -> None:
    """Run all checks for ``stage``, persist every result, then raise on any failure.

    Args:
        stage: The stage to gate (currently only ``silver``).
        spark: The active Spark session.

    Raises:
        ValueError: If ``stage`` is unknown.
        DQGateError: If any check failed. Raised only after all results are written, so
            the failure is fully diagnosable from ``ops.dq_results``.
    """
    validate_stage(stage)
    results = collect_silver_results(spark)
    _write_results(spark, stage, results)
    failed = failures(results)
    if failed:
        raise DQGateError(failed)
