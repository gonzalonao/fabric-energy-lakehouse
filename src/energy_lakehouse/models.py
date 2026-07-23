"""Typed rows, quarantine records, and DQ verdicts exchanged across the package.

These are plain, frozen dataclasses with no Spark dependency so they can be constructed
and asserted on in unit tests. The Silver notebook turns lists of these into Spark
DataFrames; the DQ gate serializes :class:`DQResult` into ``ops.dq_results``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Generic, TypeVar

RowT = TypeVar("RowT")


@dataclass(frozen=True, slots=True)
class DemandRow:
    """A single day of peninsular electricity demand.

    Attributes:
        date: The local (Europe/Madrid) calendar day. Kept as the civil date, not
            UTC-shifted: a daily bucket UTC-converted would land on the wrong day.
        value: The demand reading for that day (unit confirmed at C4, expected MWh).
    """

    date: date
    value: float


@dataclass(frozen=True, slots=True)
class GenerationRow:
    """One technology's generation for one day.

    Attributes:
        date: The local (Europe/Madrid) calendar day.
        technology: The generation technology (e.g. ``Eólica``). The ``Generación
            total`` aggregate series is excluded upstream and never appears here.
        is_renewable: Taken from the API's own renewable classification, not a
            hardcoded mapping.
        value: Generation for the technology on that day (expected MWh).
    """

    date: date
    technology: str
    is_renewable: bool
    value: float


@dataclass(frozen=True, slots=True)
class PriceRow:
    """One price observation for one series at one instant.

    Attributes:
        datetime_utc: The instant, normalized to UTC and tz-naive. UTC normalization
            keeps the key unique across DST, where a local timestamp repeats.
        series: The price series (``PVPC`` or ``Precio mercado spot``).
        value: The price (expected €/MWh).
        period_minutes: The observation's grain in minutes, derived per series from the
            spacing of its timestamps. Series differ within one file: since 2025-01-01
            the spot price is 15-minute while PVPC stays hourly, so this is data, not a
            constant. ``0`` signals an underivable grain (fewer than two points).
    """

    datetime_utc: datetime
    series: str
    value: float
    period_minutes: int


@dataclass(frozen=True, slots=True)
class QuarantineRecord:
    """A raw record that could not be turned into a typed row.

    Attributes:
        raw: The offending record, serialized back to JSON for later inspection.
        indicator: The indicator name the record came from.
        reason: Why parsing failed (missing field, non-numeric value, bad datetime).
    """

    raw: str
    indicator: str
    reason: str


@dataclass(frozen=True, slots=True)
class ParsedBatch(Generic[RowT]):
    """The outcome of parsing one Bronze file: good rows and quarantined records.

    Attributes:
        rows: Successfully typed rows.
        quarantined: Records that failed structural parsing and must be quarantined
            rather than dropped.
    """

    rows: list[RowT] = field(default_factory=list)
    quarantined: list[QuarantineRecord] = field(default_factory=list)


class DQStatus(StrEnum):
    """The verdict of a single data-quality check."""

    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class DQResult:
    """The typed result of one data-quality check, one row of ``ops.dq_results``.

    Attributes:
        check: The check name (e.g. ``value_range``).
        table: The table the check ran against.
        status: PASS or FAIL.
        observed: The numeric quantity the check measured (e.g. out-of-range row count,
            null percentage, days behind).
        threshold: The numeric bound the observation was compared against.
        details: A human-readable one-line explanation for the ops table.
        column: The column checked, when the check is column-scoped; ``None`` otherwise.
    """

    check: str
    table: str
    status: DQStatus
    observed: float
    threshold: float
    details: str
    column: str | None = None
