"""Turn raw REE JSON:API payloads into typed rows, quarantining bad records.

Each indicator has its own parser because the three series differ in shape and grain:

* demand: one series, one value per day, keyed on the civil date.
* generation: sixteen technology series (the ``Generación total`` composite excluded),
  keyed on ``(date, technology)``, with the renewable flag taken from the payload.
* prices: two series at possibly different grains, keyed on ``(datetime_utc, series)``,
  with the per-observation grain derived from timestamp spacing.

Structural failures (missing field, non-numeric value, unparseable datetime) quarantine
the individual record. Semantic problems (a negative demand, a wild price) still parse
into a row on purpose: judging them is the DQ gate's job.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime
from itertools import pairwise
from typing import Any

from .models import (
    DemandRow,
    GenerationRow,
    ParsedBatch,
    PriceRow,
    QuarantineRecord,
)

DEMAND = "demanda_evolucion"
GENERATION = "generacion_estructura"
PRICES = "precios_mercados"

# The API tags each generation series with its own renewable classification.
RENEWABLE_TYPE = "Renovable"

# Composite (aggregate) generation series, which must never be parsed as technologies.
# The primary signal is the payload's own ``composite`` attribute; the title set is a
# backstop for payloads that omit or restyle that flag. Compared case-folded and
# accent-stripped, because the API is not consistent about either.
_COMPOSITE_TITLES = frozenset({"generacion total"})
_TRUTHY_STRINGS = frozenset({"true", "t", "yes", "y", "1"})
_ACCENTS = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")

# Fields we read out of each raw value entry.
VALUE_KEY = "value"
DATETIME_KEY = "datetime"

_SECONDS_PER_MINUTE = 60


class ParseError(ValueError):
    """Raised when a payload is too malformed to parse at all (not record-level).

    A missing or non-list ``included`` array means the file itself is unusable, which
    should fail the run — distinct from a single bad record, which is quarantined.
    """


def _included(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Return the payload's ``included`` series list, or raise ``ParseError``."""
    included = payload.get("included")
    if not isinstance(included, list):
        raise ParseError("payload has no 'included' series array")
    return included


def _as_float(value: object) -> float:
    """Coerce a JSON value to float, rejecting nulls, strings, and booleans.

    Raises:
        TypeError: If the value is not a real number (``bool`` is rejected explicitly
            because it is an ``int`` subclass but never a valid reading).
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"non-numeric {VALUE_KEY} {value!r}")
    return float(value)


def _parse_dt(raw: object) -> datetime:
    """Parse an offset-aware REE timestamp such as ``2024-01-01T00:00:00.000+01:00``."""
    if not isinstance(raw, str):
        raise TypeError(f"non-string {DATETIME_KEY} {raw!r}")
    return datetime.fromisoformat(raw)


def _quarantine(entry: object, indicator: str, reason: str) -> QuarantineRecord:
    """Serialize a rejected record for the quarantine table."""
    raw = json.dumps(entry, ensure_ascii=False, default=str)
    return QuarantineRecord(raw=raw, indicator=indicator, reason=reason)


def _to_utc_naive(dt: datetime) -> datetime:
    """Normalize an aware datetime to tz-naive UTC (the canonical instant)."""
    return dt.astimezone(UTC).replace(tzinfo=None)


def _modal_period_minutes(instants: list[datetime]) -> int:
    """Derive a series' grain from the most common gap between its timestamps.

    The modal gap (rather than the mean) is robust to the one long or short gap a DST
    transition day introduces. Returns ``0`` when the grain cannot be derived from fewer
    than two points.
    """
    if len(instants) < 2:
        return 0
    ordered = sorted(instants)
    deltas = [
        int((later - earlier).total_seconds() // _SECONDS_PER_MINUTE)
        for earlier, later in pairwise(ordered)
        if later > earlier
    ]
    if not deltas:
        return 0
    return Counter(deltas).most_common(1)[0][0]


def _values(series: Mapping[str, Any]) -> Iterable[Any]:
    """Yield the raw value entries of one series."""
    attributes = series.get("attributes", {})
    values = attributes.get("values", [])
    if not isinstance(values, list):
        return []
    return values


def parse_demand(payload: Mapping[str, Any]) -> ParsedBatch[DemandRow]:
    """Parse the demand payload into one row per day.

    Args:
        payload: The raw REE JSON:API response for ``demanda/evolucion``.

    Returns:
        A batch of :class:`DemandRow` plus any quarantined records.

    Raises:
        ParseError: If the payload has no ``included`` array.
    """
    rows: list[DemandRow] = []
    quarantined: list[QuarantineRecord] = []
    for series in _included(payload):
        for entry in _values(series):
            try:
                day = _parse_dt(entry[DATETIME_KEY]).date()
                value = _as_float(entry[VALUE_KEY])
            except (KeyError, TypeError, ValueError) as exc:
                quarantined.append(_quarantine(entry, DEMAND, str(exc)))
                continue
            rows.append(DemandRow(date=day, value=value))
    return ParsedBatch(rows=rows, quarantined=quarantined)


def _normalize(text: str) -> str:
    """Case-fold and strip accents, so title matching survives API restyling."""
    return text.translate(_ACCENTS).strip().casefold()


def is_composite_series(attributes: Mapping[str, Any]) -> bool:
    """Return whether a generation series is an aggregate rather than a technology.

    Two independent signals, because relying on one of them cost a production defect.
    The original test was ``attributes.get("composite") is True`` — an *identity* check
    against Python's ``True`` singleton, so it passed only for a JSON boolean and let
    ``"true"``, ``1`` and a missing flag straight through (``1 is True`` is ``False``).
    The composite then parsed as a sixteenth technology, doubling every daily total and
    halving the renewables share for any month whose Bronze file had been re-fetched.

    Args:
        attributes: The ``attributes`` object of one series in the payload's
            ``included`` array.

    Returns:
        ``True`` if the series is the ``Generación total`` aggregate, by either its
        ``composite`` flag (in any plausible encoding) or its title.
    """
    flag = attributes.get("composite")
    if isinstance(flag, bool):
        return flag
    if isinstance(flag, str):
        return _normalize(flag) in _TRUTHY_STRINGS
    if isinstance(flag, int | float):
        return bool(flag)
    title = attributes.get("title")
    return isinstance(title, str) and _normalize(title) in _COMPOSITE_TITLES


def parse_generation(payload: Mapping[str, Any]) -> ParsedBatch[GenerationRow]:
    """Parse the generation payload into one row per (day, technology).

    The ``Generación total`` series is a composite aggregate and is skipped: it is the
    sum of the technologies, not a technology, and including it doubles every daily
    total. Detection is delegated to :func:`is_composite_series`, which accepts the flag
    in any encoding and falls back to the title. The renewable flag comes from each
    series' own classification.

    Args:
        payload: The raw REE JSON:API response for ``generacion/estructura-generacion``.

    Returns:
        A batch of :class:`GenerationRow` plus any quarantined records.

    Raises:
        ParseError: If the payload has no ``included`` array.
    """
    rows: list[GenerationRow] = []
    quarantined: list[QuarantineRecord] = []
    for series in _included(payload):
        attributes = series.get("attributes", {})
        if is_composite_series(attributes):
            continue
        technology = attributes.get("title")
        if not isinstance(technology, str):
            continue
        is_renewable = attributes.get("type") == RENEWABLE_TYPE
        for entry in _values(series):
            try:
                day = _parse_dt(entry[DATETIME_KEY]).date()
                value = _as_float(entry[VALUE_KEY])
            except (KeyError, TypeError, ValueError) as exc:
                reason = f"{technology}: {exc}"
                quarantined.append(_quarantine(entry, GENERATION, reason))
                continue
            rows.append(
                GenerationRow(
                    date=day,
                    technology=technology,
                    is_renewable=is_renewable,
                    value=value,
                )
            )
    return ParsedBatch(rows=rows, quarantined=quarantined)


def parse_prices(payload: Mapping[str, Any]) -> ParsedBatch[PriceRow]:
    """Parse the prices payload into one row per (instant, series).

    Each series' grain is derived independently from its own timestamp spacing, because
    the spot and PVPC series can differ within a single file (spot went 15-minute in
    2025 while PVPC stayed hourly). Timestamps are normalized to UTC so the natural key
    stays unique across DST transitions.

    Args:
        payload: The raw REE JSON:API response for the real-time prices series.

    Returns:
        A batch of :class:`PriceRow` plus any quarantined records.

    Raises:
        ParseError: If the payload has no ``included`` array.
    """
    rows: list[PriceRow] = []
    quarantined: list[QuarantineRecord] = []
    for series in _included(payload):
        title = series.get("attributes", {}).get("title")
        if not isinstance(title, str):
            continue
        parsed: list[tuple[datetime, float]] = []
        for entry in _values(series):
            try:
                instant = _to_utc_naive(_parse_dt(entry[DATETIME_KEY]))
                value = _as_float(entry[VALUE_KEY])
            except (KeyError, TypeError, ValueError) as exc:
                quarantined.append(_quarantine(entry, PRICES, f"{title}: {exc}"))
                continue
            parsed.append((instant, value))
        period = _modal_period_minutes([instant for instant, _ in parsed])
        rows.extend(
            PriceRow(
                datetime_utc=instant,
                series=title,
                value=value,
                period_minutes=period,
            )
            for instant, value in parsed
        )
    return ParsedBatch(rows=rows, quarantined=quarantined)


# Dispatch by indicator name (the Bronze path / watermark key) for the Silver notebook.
PARSERS: dict[str, Callable[[Mapping[str, Any]], ParsedBatch[Any]]] = {
    DEMAND: parse_demand,
    GENERATION: parse_generation,
    PRICES: parse_prices,
}
