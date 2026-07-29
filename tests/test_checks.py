from __future__ import annotations

from datetime import date

from energy_lakehouse.dq import checks
from energy_lakehouse.models import DQStatus


def test_null_pct_passes_when_no_nulls() -> None:
    r = checks.null_pct(table="t", column="c", null_count=0, total_count=100)
    assert r.status is DQStatus.PASS
    assert r.observed == 0.0


def test_null_pct_fails_on_any_null_in_key_column() -> None:
    r = checks.null_pct(table="t", column="c", null_count=1, total_count=100)
    assert r.status is DQStatus.FAIL
    assert r.observed == 1.0


def test_null_pct_empty_table_is_zero_percent() -> None:
    r = checks.null_pct(table="t", column="c", null_count=0, total_count=0)
    assert r.status is DQStatus.PASS


def test_value_range_fails_when_rows_out_of_range() -> None:
    r = checks.value_range(
        table="silver.demand_daily",
        column="value",
        out_of_range_count=3,
        low=0.0,
        high=float("inf"),
    )
    assert r.status is DQStatus.FAIL
    assert r.observed == 3.0


def test_value_range_passes_when_clean() -> None:
    r = checks.value_range(
        table="t", column="value", out_of_range_count=0, low=-500.0, high=4000.0
    )
    assert r.status is DQStatus.PASS


def test_freshness_passes_when_current() -> None:
    r = checks.freshness(
        table="t", max_date=date(2026, 7, 17), min_expected=date(2026, 7, 17)
    )
    assert r.status is DQStatus.PASS
    assert r.observed == 0.0


def test_freshness_fails_when_stale() -> None:
    r = checks.freshness(
        table="t", max_date=date(2026, 7, 10), min_expected=date(2026, 7, 17)
    )
    assert r.status is DQStatus.FAIL
    assert r.observed == 7.0


def test_freshness_fails_on_empty_table() -> None:
    r = checks.freshness(table="t", max_date=None, min_expected=date(2026, 7, 17))
    assert r.status is DQStatus.FAIL
    assert r.observed == float("inf")


def test_row_count_delta_first_load_passes_without_baseline() -> None:
    r = checks.row_count_delta(table="t", current=100, previous=0)
    assert r.status is DQStatus.PASS
    assert "no baseline" in r.details


def test_row_count_delta_passes_within_tolerance() -> None:
    r = checks.row_count_delta(table="t", current=110, previous=100)
    assert r.status is DQStatus.PASS
    assert r.observed == 10.0


def test_row_count_delta_fails_on_large_swing() -> None:
    r = checks.row_count_delta(table="t", current=40, previous=100)
    assert r.status is DQStatus.FAIL
    assert r.observed == 60.0


def test_ratio_band_passes_when_every_day_is_in_band() -> None:
    r = checks.ratio_band(
        table="silver.generation_daily",
        column="generation/demand",
        out_of_band_days=0,
        extreme=None,
        low=0.8,
        high=1.6,
    )
    assert r.status is DQStatus.PASS
    assert "0 day(s)" in r.details


def test_ratio_band_fails_on_the_doubled_total() -> None:
    """The composite-series defect, expressed as the check that would have caught it.

    Generation ran at 2.29x demand for 26 days while every individual value stayed
    plausible, so no single-column check could see it.
    """
    r = checks.ratio_band(
        table="silver.generation_daily",
        column="generation/demand",
        out_of_band_days=26,
        extreme=2.29,
        low=0.8,
        high=1.6,
    )
    assert r.status is DQStatus.FAIL
    assert r.observed == 2.29
    assert "furthest 2.29" in r.details


def test_ratio_band_fails_on_an_undershoot_too() -> None:
    """A collapse is as much a break as a doubling — the band is two-sided."""
    r = checks.ratio_band(
        table="silver.generation_daily",
        column="generation/demand",
        out_of_band_days=1,
        extreme=0.41,
        low=0.8,
        high=1.6,
    )
    assert r.status is DQStatus.FAIL
    assert r.observed == 0.41
