from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from typing import Any

import pytest

from energy_lakehouse.parsers import (
    PARSERS,
    ParseError,
    is_composite_series,
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


COMPOSITE_TITLE = "Generación total"


def _reflag_composite(payload: dict[str, Any], flag: Any) -> dict[str, Any]:
    """Copy the payload, setting the composite series' flag (``...`` deletes it)."""
    clone = deepcopy(payload)
    for series in clone["included"]:
        attributes = series["attributes"]
        if attributes.get("title") == COMPOSITE_TITLE:
            if flag is ...:
                attributes.pop("composite", None)
            else:
                attributes["composite"] = flag
    return clone


@pytest.mark.parametrize(
    "flag",
    [True, "true", "TRUE", "yes", 1, 1.0, ..., False, "false", 0, None],
    ids=[
        "true",
        "str_true",
        "str_upper",
        "str_yes",
        "int_1",
        "float_1",
        "absent",
        "false",
        "str_false",
        "int_0",
        "null",
    ],
)
def test_parse_generation_excludes_composite_whatever_the_flag_says(
    generacion_good: dict[str, Any], flag: Any
) -> None:
    """The aggregate is excluded regardless of the ``composite`` flag's value.

    The falsy half of this list is the one that matters. Both previous versions of this
    guard consulted the flag *first* and let its answer stand: ``is True`` rejected
    everything but a boolean, and the repair after it treated the title as a fallback
    reached only when the flag was absent. When REE set ``composite: False`` on every
    series, a dead signal answered on behalf of two live ones.
    """
    batch = parse_generation(_reflag_composite(generacion_good, flag))
    assert COMPOSITE_TITLE not in {r.technology for r in batch.rows}
    assert len({r.technology for r in batch.rows}) == 15


def test_parse_generation_handles_the_live_2026_07_payload_shape(
    generacion_good: dict[str, Any],
) -> None:
    """The payload as REE actually serves it since 2026-07: two signals changed at once.

    ``composite`` is ``False`` on *every* series (so it distinguishes nothing) and the
    aggregate's type was renamed ``Generación total`` -> ``total``. Only the title
    survived both changes, which is precisely why no single signal is trusted alone.
    """
    clone = deepcopy(generacion_good)
    for series in clone["included"]:
        attributes = series["attributes"]
        attributes["composite"] = False
        if attributes["title"] == COMPOSITE_TITLE:
            attributes["type"] = "total"
    batch = parse_generation(clone)
    assert COMPOSITE_TITLE not in {r.technology for r in batch.rows}
    assert len({r.technology for r in batch.rows}) == 15
    assert not batch.quarantined


@pytest.mark.parametrize("flag", [False, "false", "no", 0, 0.0], ids=lambda f: repr(f))
def test_parse_generation_keeps_real_technologies(
    generacion_good: dict[str, Any], flag: Any
) -> None:
    """A falsy composite flag must not drop a genuine technology.

    The mirror of the regression above: broadening the exclusion is only safe if it
    stays false for every series the payload types as a real technology.
    """
    clone = deepcopy(generacion_good)
    for series in clone["included"]:
        if series["attributes"].get("title") != COMPOSITE_TITLE:
            series["attributes"]["composite"] = flag
    batch = parse_generation(clone)
    assert len({r.technology for r in batch.rows}) == 15
    assert "Nuclear" in {r.technology for r in batch.rows}


def test_parse_generation_quarantines_an_unrecognised_series(
    generacion_good: dict[str, Any],
) -> None:
    """An unknown series type is quarantined, never silently dropped.

    A dropped series changes every total with nothing left to explain it; a quarantined
    one leaves a row naming the type we failed to recognise. Given REE has renamed a
    type once already, the next rename should surface in a table rather than in a
    number.
    """
    clone = deepcopy(generacion_good)
    for series in clone["included"]:
        if series["attributes"]["title"] == "Nuclear":
            series["attributes"]["type"] = "Almacenamiento"
    batch = parse_generation(clone)
    assert "Nuclear" not in {r.technology for r in batch.rows}
    assert len(batch.quarantined) == 1
    assert "Almacenamiento" in batch.quarantined[0].reason


def test_no_composite_signal_can_veto_another() -> None:
    """Each signal alone is sufficient; a false flag never overrules title or type."""
    assert is_composite_series({"composite": False, "title": "Generación total"})
    assert is_composite_series({"composite": False, "type": "total", "title": "x"})
    assert is_composite_series({"composite": True, "title": "x", "type": "Renovable"})
    # Accent- and case-insensitive, because the API is consistent about neither.
    assert is_composite_series({"title": "GENERACION TOTAL"})
    assert is_composite_series({"title": " Generación Total "})
    # And a genuine technology is never caught by any of them.
    assert not is_composite_series(
        {"composite": False, "title": "Solar fotovoltaica", "type": "Renovable"}
    )


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
