from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pytest

from energy_lakehouse.parsers import (
    PARSERS,
    ParseError,
    parse_demand,
    parse_generation,
    parse_prices,
)


def test_parse_demand_good_yields_one_row_per_day(demanda_good: dict[str, Any]) -> None:
    batch = parse_demand(demanda_good)
    assert not batch.quarantined
    assert [r.date for r in batch.rows] == [
        date(2024, 1, 1),
        date(2024, 1, 2),
        date(2024, 1, 3),
    ]
    # Civil date is preserved, not UTC-shifted off the +01:00 midnight bucket.
    assert batch.rows[0].date == date(2024, 1, 1)
    assert batch.rows[0].value == pytest.approx(555244.867)


def test_parse_demand_quarantines_bad_records_but_keeps_negatives(
    demanda_malformed: dict[str, Any],
) -> None:
    batch = parse_demand(demanda_malformed)
    # Null value and missing datetime are structural failures -> quarantined.
    assert len(batch.quarantined) == 2
    assert all(q.indicator == "demanda_evolucion" for q in batch.quarantined)
    # The negative value is a *semantic* problem: it parses cleanly and is left for the
    # DQ gate to judge, never silently dropped by the parser.
    assert len(batch.rows) == 1
    assert batch.rows[0].value == -999.0
    assert batch.rows[0].date == date(2024, 1, 3)


def test_parse_generation_excludes_composite_total(
    generacion_good: dict[str, Any],
) -> None:
    batch = parse_generation(generacion_good)
    technologies = {r.technology for r in batch.rows}
    # The 'Generación total' aggregate (composite=True) must never become a tech row.
    assert "Generación total" not in technologies
    # 15 real technologies over 2 days = 30 rows.
    assert len(technologies) == 15
    assert len(batch.rows) == 30
    assert not batch.quarantined


def test_parse_generation_reads_renewable_flag_from_payload(
    generacion_good: dict[str, Any],
) -> None:
    batch = parse_generation(generacion_good)
    by_tech = {r.technology: r for r in batch.rows}
    assert by_tech["Hidráulica"].is_renewable is True
    assert by_tech["Nuclear"].is_renewable is False


def test_parse_prices_2024_is_hourly_for_both_series(
    precios_2024_good: dict[str, Any],
) -> None:
    batch = parse_prices(precios_2024_good)
    periods = {r.series: r.period_minutes for r in batch.rows}
    assert periods == {"PVPC": 60, "Precio mercado spot": 60}


def test_parse_prices_2025_grain_differs_per_series(
    precios_2025_good: dict[str, Any],
) -> None:
    batch = parse_prices(precios_2025_good)
    periods = {r.series: r.period_minutes for r in batch.rows}
    # The grain split: spot went 15-minute in 2025 while PVPC stayed hourly.
    assert periods["PVPC"] == 60
    assert periods["Precio mercado spot"] == 15
    spot = [r for r in batch.rows if r.series == "Precio mercado spot"]
    assert len(spot) == 96


def test_parse_prices_normalizes_to_utc(precios_2024_good: dict[str, Any]) -> None:
    batch = parse_prices(precios_2024_good)
    first = min(batch.rows, key=lambda r: r.datetime_utc)
    # 2024-06-01T00:00:00+02:00 (summer offset) -> 2024-05-31T22:00 UTC, tz-naive.
    assert first.datetime_utc == datetime(2024, 5, 31, 22, 0)
    assert first.datetime_utc.tzinfo is None


def test_missing_included_raises_parse_error() -> None:
    with pytest.raises(ParseError):
        parse_demand({"data": {"type": "x"}})


def test_parsers_registry_maps_every_indicator() -> None:
    assert set(PARSERS) == {
        "demanda_evolucion",
        "generacion_estructura",
        "precios_mercados",
    }
