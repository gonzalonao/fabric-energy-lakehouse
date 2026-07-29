"""Turn raw REE JSON:API payloads into typed rows, quarantining bad records.

Each indicator has its own parser because the three series differ in shape and grain:

* demand: one series, one value per day, keyed on the civil date.
* generation: the technology series (the ``Generación total`` composite excluded, any
  unrecognised series quarantined), keyed on ``(date, technology)``, with the renewable
  flag taken from the payload.
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

# Identifying the `Generación total` aggregate, which must never be parsed as a
# technology. Three independent signals, OR'd, because REE has changed two of them
# under us: as of 2026-07-28 the payload reports `composite: False` on *every* series
# (the flag carries no information at all any more) and renamed the aggregate's type
# from `Generación total` to `total`. Only the title survived both changes.
#
# OR'd, specifically. The previous version chained them — flag first, title as a
# fallback — so a flag that had gone dead could veto a title that was still correct.
# No signal here is allowed to answer "not composite" on another's behalf.
_COMPOSITE_TITLES = frozenset({"generacion total"})
_COMPOSITE_TYPES = frozenset({"total", "generacion total"})
_TRUTHY_STRINGS = frozenset({"true", "t", "yes", "y", "1"})

# The whitelist that makes the above a belt-and-braces rather than the only defence: a
# real technology is typed Renovable or No-Renovable. Anything else is not a technology,
# whether or not we recognise it as a known aggregate.
_TECHNOLOGY_TYPES = frozenset({"renovable", "no-renovable"})

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


def _text(attributes: Mapping[str, Any], key: str) -> str | None:
    """Return a normalized string attribute, or ``None`` if it isn't one."""
    value = attributes.get(key)
    return _normalize(value) if isinstance(value, str) else None


def _flag_is_true(flag: object) -> bool:
    """Interpret a JSON flag as a boolean across the encodings REE has used."""
    if isinstance(flag, bool):
        return flag
    if isinstance(flag, str):
        return _normalize(flag) in _TRUTHY_STRINGS
    if isinstance(flag, int | float):
        return bool(flag)
    return False


def is_composite_series(attributes: Mapping[str, Any]) -> bool:
    """Return whether a generation series is a known aggregate, not a technology.

    Any one of three signals is enough, and none may veto the others — the ordering
    that let this through twice is the reason for that emphasis:

    * ``composite`` truthy in any encoding (boolean, ``"true"``, ``1``);
    * the title being ``Generación total``;
    * the type being ``total`` (or the older ``Generación total``).

    History, because the shape of the mistake matters more than the fix. The original
    guard was ``attributes.get("composite") is True``, an identity comparison against
    Python's ``True`` singleton. The first repair broadened the encodings but kept the
    title as a *fallback* — reached only when the flag was absent. Then REE flipped
    ``composite`` to ``False`` on every series and renamed the aggregate's type, so a
    dead signal returned ``False`` and the live signal was never consulted. The
    aggregate parsed as an extra technology, doubling every daily total and halving the
    renewables share on any file that had been re-fetched.

    Args:
        attributes: The ``attributes`` object of one series in ``included``.

    Returns:
        ``True`` if the series is a known aggregate.
    """
    return (
        _flag_is_true(attributes.get("composite"))
        or _text(attributes, "title") in _COMPOSITE_TITLES
        or _text(attributes, "type") in _COMPOSITE_TYPES
    )


def is_technology_series(attributes: Mapping[str, Any]) -> bool:
    """Return whether a series is typed as a real technology.

    A whitelist, deliberately: the payload types every genuine technology ``Renovable``
    or ``No-Renovable``, so anything else is not one — whether or not
    :func:`is_composite_series` recognises it. Unrecognised series are quarantined
    rather than dropped, so the next upstream rename is visible in a table instead of
    silently changing a total.

    Args:
        attributes: The ``attributes`` object of one series in ``included``.

    Returns:
        ``True`` if the series' type is a known technology classification.
    """
    return _text(attributes, "type") in _TECHNOLOGY_TYPES


def parse_generation(payload: Mapping[str, Any]) -> ParsedBatch[GenerationRow]:
    """Parse the generation payload into one row per (day, technology).

    Each series is triaged three ways rather than two:

    * a known aggregate (:func:`is_composite_series`) is skipped silently — expected,
      not newsworthy. Including it would double every daily total;
    * a series typed as a real technology (:func:`is_technology_series`) is parsed;
    * anything else is **quarantined**, not dropped. That third branch is the point: a
      silently discarded series changes a total with nothing to show for it, whereas a
      quarantined one leaves a row naming the type we didn't recognise. REE has already
      renamed the aggregate's type once mid-project.

    The renewable flag comes from each series' own classification.

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
        if not is_technology_series(attributes) or not isinstance(technology, str):
            reason = (
                f"unrecognised generation series: title={technology!r} "
                f"type={attributes.get('type')!r} — neither a known aggregate nor a "
                "typed technology"
            )
            quarantined.append(_quarantine(attributes, GENERATION, reason))
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
