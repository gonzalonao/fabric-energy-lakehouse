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

# Overridden by the calling pipeline's Notebook activity at runtime.
#
# p_mode = "backfill" -> every indicator runs from p_from to p_to.
# p_mode = "daily"    -> every indicator runs from its OWN last_end in
#                        bronze.ctl_watermark to yesterday; p_from/p_to are ignored.
#
# The defaults are empty and fail validation on purpose: an unparameterized run must
# error rather than silently pick a mode and ingest an unintended range.
p_mode = ""
p_from = ""
p_to = ""


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""Emit the (indicator x month) work list for the ingest pipelines.

Serves both `pl_backfill_ree` (``p_mode="backfill"``) and `pl_ingest_daily`
(``p_mode="daily"``). Generating a work list is one responsibility; the mode only
decides where each indicator's start date comes from.

Windows are clipped to at most one calendar month because the REE API rejects longer
ranges on hourly series. This matters in daily mode too, not just for backfills: if the
schedule is paused or runs fail for over a month, ``watermark -> yesterday`` would exceed
a month. Since a failed run never advances the watermark, an unchunked daily pipeline
could never catch up without manual intervention.

Ordering is indicator-major: every month of one indicator, then the next. If a run dies
midway that leaves whole indicators complete rather than all of them half-loaded.

Returns a JSON array via ``notebookutils.notebook.exit`` for the caller's ForEach. An
empty array is a valid, expected result in daily mode when everything is already current.
"""

import json
import logging
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterator

import notebookutils  # type: ignore[import-not-found]  # Fabric runtime builtin
from pyspark.sql import SparkSession

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("nb_gen_chunks")

WATERMARK_TABLE = "bronze.ctl_watermark"
DATE_FORMAT = "%Y-%m-%d"
WATERMARK_FORMAT = "%Y-%m-%dT%H:%M"
DAY_START_SUFFIX = "T00:00"
DAY_END_SUFFIX = "T23:59"

MODE_BACKFILL = "backfill"
MODE_DAILY = "daily"
VALID_MODES = (MODE_BACKFILL, MODE_DAILY)


@dataclass(frozen=True)
class Indicator:
    """One REE series and how to request it.

    Attributes:
        path: URL path segment under ``/es/datos/``.
        name: Our name for the series; drives the Bronze path and the watermark key.
        time_trunc: API granularity, ``day`` or ``hour``.
    """

    path: str
    name: str
    time_trunc: str


# The single source of truth for which series this project ingests. Both pipelines read
# it from here — do not duplicate this list into a pipeline parameter.
INDICATORS: tuple[Indicator, ...] = (
    Indicator("demanda/evolucion", "demanda_evolucion", "day"),
    Indicator("generacion/estructura-generacion", "generacion_estructura", "day"),
    Indicator("mercados/precios-mercados-tiempo-real", "precios_mercados", "hour"),
)


def parse_date(value: str, field: str) -> date:
    """Parse a ``YYYY-MM-DD`` string.

    Args:
        value: The raw parameter value.
        field: Parameter name, used in the error message.

    Returns:
        The parsed date.

    Raises:
        ValueError: If the value is blank or not a valid ``YYYY-MM-DD`` date.
    """
    if not value.strip():
        raise ValueError(f"{field} must be a non-empty YYYY-MM-DD date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be YYYY-MM-DD; got {value!r}") from exc


def parse_watermark(value: str) -> date:
    """Extract the date part of a stored watermark.

    Args:
        value: A watermark such as ``2026-07-15T23:59``.

    Returns:
        The date the watermark refers to.

    Raises:
        ValueError: If the watermark does not match ``WATERMARK_FORMAT``.
    """
    try:
        return datetime.strptime(value, WATERMARK_FORMAT).date()
    except ValueError as exc:
        raise ValueError(
            f"{WATERMARK_TABLE} holds a malformed last_end {value!r}; "
            f"expected {WATERMARK_FORMAT!r}"
        ) from exc


def validate_mode(mode: str) -> str:
    """Check the mode parameter.

    Args:
        mode: The requested mode.

    Returns:
        The validated mode.

    Raises:
        ValueError: If the mode is not one of ``VALID_MODES``.
    """
    if mode not in VALID_MODES:
        raise ValueError(f"p_mode must be one of {VALID_MODES}; got {mode!r}")
    return mode


def last_day_of_month(day: date) -> date:
    """Return the last calendar day of the month containing ``day``.

    Args:
        day: Any date within the month.

    Returns:
        The month's final date.
    """
    return day.replace(day=monthrange(day.year, day.month)[1])


def month_windows(start: date, end: date) -> Iterator[tuple[date, date]]:
    """Split an inclusive date range into per-calendar-month windows.

    The first and last windows are clipped to ``start`` and ``end``.

    Args:
        start: First date to cover, inclusive.
        end: Last date to cover, inclusive.

    Yields:
        ``(window_start, window_end)`` pairs, each within a single month.

    Raises:
        ValueError: If ``start`` is after ``end``.
    """
    if start > end:
        raise ValueError(f"start ({start}) must not be after end ({end})")
    cursor = start
    while cursor <= end:
        month_end = last_day_of_month(cursor)
        yield cursor, min(month_end, end)
        cursor = month_end + timedelta(days=1)


def chunks_for(indicator: Indicator, start: date, end: date) -> list[dict[str, str]]:
    """Build one indicator's month-sized work items.

    Args:
        indicator: The series to cover.
        start: First date to cover, inclusive.
        end: Last date to cover, inclusive.

    Returns:
        One dict per month, shaped for ``pl_ingest_ree``'s five parameters.
    """
    return [
        {
            "indicator_path": indicator.path,
            "indicator_name": indicator.name,
            "time_trunc": indicator.time_trunc,
            "start": f"{window_start.strftime(DATE_FORMAT)}{DAY_START_SUFFIX}",
            "end": f"{window_end.strftime(DATE_FORMAT)}{DAY_END_SUFFIX}",
        }
        for window_start, window_end in month_windows(start, end)
    ]


def read_watermarks(session: SparkSession) -> dict[str, str]:
    """Read every indicator's watermark from the control table.

    Args:
        session: Active Spark session.

    Returns:
        Mapping of indicator name to its stored ``last_end``. Indicators absent from
        the table are simply absent here.
    """
    rows = session.sql(f"SELECT indicator, last_end FROM {WATERMARK_TABLE}").collect()
    return {row["indicator"]: row["last_end"] for row in rows}


def backfill_chunks(
    indicators: tuple[Indicator, ...], start: date, end: date
) -> list[dict[str, str]]:
    """Build the work list for a backfill: every indicator over the same range.

    Args:
        indicators: Series to cover.
        start: First date to cover, inclusive.
        end: Last date to cover, inclusive.

    Returns:
        The full work list, indicator-major.
    """
    return [chunk for indicator in indicators for chunk in chunks_for(indicator, start, end)]


def daily_chunks(
    indicators: tuple[Indicator, ...], watermarks: dict[str, str], end: date
) -> list[dict[str, str]]:
    """Build the work list for a daily run: each indicator from its own watermark.

    Per-indicator watermarks mean a series that failed yesterday resumes from its own
    position while the others carry on from theirs.

    An indicator already current (watermark at or after ``end``) contributes **no
    chunks** — the correct outcome for a same-day re-run, and why the caller must
    tolerate an empty array.

    The fetch start is snapped back to the first day of its month. Bronze stores one
    file per (indicator, month) and the Copy activity overwrites that file whole, so a
    mid-month window such as ``watermark+1 -> yesterday`` would replace a complete month
    file with a fragment. Re-fetching month-to-date keeps the file complete at a cost of
    at most ~31 redundant days per indicator. Currency is checked *before* the snap so
    an up-to-date indicator stays a true no-op instead of re-fetching its month forever.

    Args:
        indicators: Series to cover.
        watermarks: Mapping of indicator name to stored ``last_end``.
        end: Last date to cover, inclusive (normally yesterday).

    Returns:
        The work list, indicator-major, possibly empty.

    Raises:
        KeyError: If an indicator has no watermark row. Bootstrapping the table is a
            deliberate step; inventing a start date here could silently ingest years of
            data or skip a gap.
    """
    chunks: list[dict[str, str]] = []
    for indicator in indicators:
        if indicator.name not in watermarks:
            raise KeyError(
                f"no watermark row for {indicator.name!r} in {WATERMARK_TABLE}; "
                "run nb_update_watermark once to bootstrap it"
            )
        start = parse_watermark(watermarks[indicator.name]) + timedelta(days=1)
        if start > end:
            logger.info(
                "%s already current (watermark %s) - no chunks",
                indicator.name,
                watermarks[indicator.name],
            )
            continue
        # Month-boundary snap — see docstring: partial windows would clobber month files.
        chunks.extend(chunks_for(indicator, start.replace(day=1), end))
    return chunks


def yesterday(session: SparkSession) -> date:
    """Return yesterday's date in UTC.

    Today's data is incomplete, so ingest windows stop at yesterday.

    Args:
        session: Active Spark session (unused; kept for call-site symmetry).

    Returns:
        Yesterday's UTC date.
    """
    del session
    return datetime.utcnow().date() - timedelta(days=1)


# ``spark`` is injected into the notebook session by the Fabric runtime.
mode = validate_mode(p_mode)  # noqa: F821
if mode == MODE_BACKFILL:
    chunks = backfill_chunks(
        INDICATORS,
        parse_date(p_from, "p_from"),  # noqa: F821
        parse_date(p_to, "p_to"),  # noqa: F821
    )
else:
    chunks = daily_chunks(INDICATORS, read_watermarks(spark), yesterday(spark))  # noqa: F821

logger.info("mode=%s produced %d chunks", mode, len(chunks))
notebookutils.notebook.exit(json.dumps(chunks))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
