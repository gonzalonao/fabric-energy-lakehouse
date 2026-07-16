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

# Overridden by the calling pipeline's Notebook activity at runtime. Empty
# defaults fail validation rather than silently backfilling an unintended range.
p_from = ""
p_to = ""


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

"""Emit the (indicator x month) work list for ``pl_backfill_ree``.

Returns a JSON array via ``notebookutils.notebook.exit`` so the caller can drive a
ForEach over it. Windows are clipped to at most one calendar month because the REE
API rejects longer ranges on hourly series.

Ordering is indicator-major: every month of one indicator, then the next. If the
backfill dies midway that leaves whole indicators complete rather than all three
half-loaded, which is easier to reason about when resuming.
"""

import json
import logging
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterator

import notebookutils  # type: ignore[import-not-found]  # Fabric runtime builtin

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("nb_gen_backfill_chunks")

DATE_FORMAT = "%Y-%m-%d"
DAY_START_SUFFIX = "T00:00"
DAY_END_SUFFIX = "T23:59"


@dataclass(frozen=True)
class Indicator:
    """One REE series and how to request it.

    Attributes:
        path: URL path segment under ``/es/datos/``.
        name: Our name for the series; drives the Bronze path.
        time_trunc: API granularity, ``day`` or ``hour``.
    """

    path: str
    name: str
    time_trunc: str


# The single source of truth for what the backfill covers. `pl_ingest_daily`
# repeats these three in its own array parameter — keep them in step.
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

    The first and last windows are clipped to ``start`` and ``end``, so a range
    that begins mid-month does not request days outside it.

    Args:
        start: First date to cover, inclusive.
        end: Last date to cover, inclusive.

    Yields:
        ``(window_start, window_end)`` pairs, each within a single month.

    Raises:
        ValueError: If ``start`` is after ``end``.
    """
    if start > end:
        raise ValueError(f"p_from ({start}) must not be after p_to ({end})")
    cursor = start
    while cursor <= end:
        month_end = last_day_of_month(cursor)
        yield cursor, min(month_end, end)
        cursor = month_end + timedelta(days=1)


def build_chunks(
    indicators: tuple[Indicator, ...], start: date, end: date
) -> list[dict[str, str]]:
    """Build the full work list for the backfill.

    Args:
        indicators: Series to cover.
        start: First date to cover, inclusive.
        end: Last date to cover, inclusive.

    Returns:
        One dict per (indicator, month), shaped for ``pl_ingest_ree``'s parameters.
    """
    return [
        {
            "indicator_path": indicator.path,
            "indicator_name": indicator.name,
            "time_trunc": indicator.time_trunc,
            "start": f"{window_start.strftime(DATE_FORMAT)}{DAY_START_SUFFIX}",
            "end": f"{window_end.strftime(DATE_FORMAT)}{DAY_END_SUFFIX}",
        }
        for indicator in indicators
        for window_start, window_end in month_windows(start, end)
    ]


chunks = build_chunks(
    INDICATORS,
    parse_date(p_from, "p_from"),  # noqa: F821
    parse_date(p_to, "p_to"),  # noqa: F821
)
logger.info(
    "generated %d chunks across %d indicators", len(chunks), len(INDICATORS)
)
notebookutils.notebook.exit(json.dumps(chunks))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
