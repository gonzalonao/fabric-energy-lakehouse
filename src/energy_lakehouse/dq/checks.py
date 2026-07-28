"""Pure data-quality checks: plain numeric inputs in, typed verdicts out.

Keeping these Spark-free is deliberate. The expensive part — counting nulls, finding the
max date, counting out-of-range rows — is a Spark aggregation done once in
:mod:`energy_lakehouse.dq.gate`; each function here only turns those scalars into a
:class:`~energy_lakehouse.models.DQResult`. That makes every threshold decision
unit-testable on the laptop, with no cluster and no fixtures.
"""

from __future__ import annotations

from datetime import date

from ..models import DQResult, DQStatus

# Thresholds live here as named constants; the gate maps tables and columns onto them.
DEFAULT_NULL_MAX_PCT = 0.0
DEFAULT_ROWCOUNT_MAX_PCT = 50.0
_PERCENT = 100.0


def _verdict(passed: bool) -> DQStatus:
    return DQStatus.PASS if passed else DQStatus.FAIL


def null_pct(
    *,
    table: str,
    column: str,
    null_count: int,
    total_count: int,
    max_pct: float = DEFAULT_NULL_MAX_PCT,
) -> DQResult:
    """Flag a column whose null fraction exceeds ``max_pct``.

    Args:
        table: Table under test.
        column: Column under test.
        null_count: Number of null values observed in the column.
        total_count: Total number of rows.
        max_pct: Maximum tolerated null percentage (default 0 for key columns).

    Returns:
        A PASS/FAIL result carrying the observed null percentage.
    """
    pct = (_PERCENT * null_count / total_count) if total_count else 0.0
    return DQResult(
        check="null_pct",
        table=table,
        column=column,
        status=_verdict(pct <= max_pct),
        observed=pct,
        threshold=max_pct,
        details=f"{null_count}/{total_count} null ({pct:.2f}%)",
    )


def value_range(
    *,
    table: str,
    column: str,
    out_of_range_count: int,
    low: float,
    high: float,
) -> DQResult:
    """Flag rows whose value falls outside ``[low, high]``.

    The caller counts offending rows in Spark; any nonzero count fails the check.

    Args:
        table: Table under test.
        column: Column under test.
        out_of_range_count: Number of rows observed outside the bounds.
        low: Inclusive lower bound.
        high: Inclusive upper bound.

    Returns:
        A PASS/FAIL result; the threshold is zero tolerated violations.
    """
    return DQResult(
        check="value_range",
        table=table,
        column=column,
        status=_verdict(out_of_range_count == 0),
        observed=float(out_of_range_count),
        threshold=0.0,
        details=f"{out_of_range_count} rows outside [{low}, {high}]",
    )


def ratio_band(
    *,
    table: str,
    column: str,
    out_of_band_days: int,
    extreme: float | None,
    low: float,
    high: float,
) -> DQResult:
    """Flag days whose derived ratio falls outside a plausible band.

    Every other check here judges one column of one table against a bound, which makes
    them blind to a defect that leaves each individual value plausible while breaking
    the relationship between them. The composite-series bug was exactly that: each
    technology's daily figure was sane, and the total was double what it should be.

    Args:
        table: Table under test (the numerator's table, for reporting).
        column: A label for the ratio being tested, e.g. ``generation/demand``.
        out_of_band_days: Number of days observed outside the band.
        extreme: The ratio furthest outside the band, or ``None`` if all days passed.
        low: Inclusive lower bound of the plausible band.
        high: Inclusive upper bound.

    Returns:
        A PASS/FAIL result; the threshold is zero tolerated days.
    """
    shown = "n/a" if extreme is None else f"{extreme:.2f}"
    return DQResult(
        check="ratio_band",
        table=table,
        column=column,
        status=_verdict(out_of_band_days == 0),
        observed=float(extreme) if extreme is not None else 0.0,
        threshold=high,
        details=(
            f"{out_of_band_days} day(s) with {column} outside "
            f"[{low}, {high}]; furthest {shown}"
        ),
    )


def freshness(*, table: str, max_date: date | None, min_expected: date) -> DQResult:
    """Flag a table whose most recent date is behind ``min_expected``.

    Args:
        table: Table under test.
        max_date: The latest date present, or ``None`` if the table is empty.
        min_expected: The oldest acceptable maximum date (e.g. yesterday).

    Returns:
        A PASS/FAIL result; the observed value is the number of days behind (0 when
        current or fresher, a large sentinel when the table is empty).
    """
    if max_date is None:
        return DQResult(
            check="freshness",
            table=table,
            column="date",
            status=DQStatus.FAIL,
            observed=float("inf"),
            threshold=0.0,
            details=f"table empty; expected max date >= {min_expected.isoformat()}",
        )
    days_behind = (min_expected - max_date).days
    return DQResult(
        check="freshness",
        table=table,
        column="date",
        status=_verdict(max_date >= min_expected),
        observed=float(max(days_behind, 0)),
        threshold=0.0,
        details=(
            f"max date {max_date.isoformat()}, expected >= {min_expected.isoformat()}"
        ),
    )


def row_count_delta(
    *,
    table: str,
    current: int,
    previous: int,
    max_pct: float = DEFAULT_ROWCOUNT_MAX_PCT,
) -> DQResult:
    """Flag a load whose row count swings more than ``max_pct`` from the previous load.

    The first load has no baseline (``previous == 0``) and always passes.

    Args:
        table: Table under test.
        current: Row count after this load.
        previous: Row count after the previous load.
        max_pct: Maximum tolerated absolute percentage change.

    Returns:
        A PASS/FAIL result carrying the observed percentage change.
    """
    if previous == 0:
        return DQResult(
            check="row_count_delta",
            table=table,
            column=None,
            status=DQStatus.PASS,
            observed=0.0,
            threshold=max_pct,
            details=f"no baseline (first load), current={current}",
        )
    pct = _PERCENT * abs(current - previous) / previous
    return DQResult(
        check="row_count_delta",
        table=table,
        column=None,
        status=_verdict(pct <= max_pct),
        observed=pct,
        threshold=max_pct,
        details=f"{previous} -> {current} ({pct:.2f}% change)",
    )
